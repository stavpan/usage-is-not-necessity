"""The derived axes, assembled into a reportable object."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from world_impact import nulls, structure


@dataclass
class StructureResult:
    """Everything the structural analysis produced, with units declared."""

    eigenvalues: np.ndarray
    cumulative: np.ndarray
    effective_rank: float
    stable_rank: float
    noise_floor: float
    n_retained: int
    n_retained_median_rule: int
    loadings: np.ndarray
    rotated: np.ndarray
    outcome_labels: tuple[str, ...]
    pervasiveness: np.ndarray
    pervasiveness_weighted: np.ndarray
    mean_prediction_error: np.ndarray
    prediction_error_sd: np.ndarray
    extras: dict[str, float] = field(default_factory=dict)

    def top_loadings(
        self, component: int, threshold: float = 0.15, limit: int = 8
    ) -> list[tuple[int, float]]:
        """(outcome index, loading) for one rotated component."""
        column = self.rotated[:, component]
        order = np.argsort(-np.abs(column))
        return [(int(j), float(column[j])) for j in order if abs(column[j]) >= threshold][:limit]

    def component_share(self, component: int) -> float:
        return float(self.eigenvalues[component] / self.eigenvalues.sum())


def analyse_structure(
    matrix: np.ndarray,
    outcome_labels: tuple[str, ...],
    rng: np.random.Generator,
    n_components: int = 8,
    pa_iterations: int = 500,
    loading_threshold: float = 0.15,
) -> StructureResult:
    """Full structural analysis of the outcome co-impact grammar.

    The number of axes is an *output*: parallel analysis at the 95th percentile
    (Glorfeld revision), cross-checked against the 50th percentile, the
    Marchenko-Pastur noise floor, and an out-of-sample prediction-error curve.
    Disagreement between these is reported rather than resolved by preference.
    """
    matrix = np.asarray(matrix, dtype=float)
    eigenvalues = nulls.spectrum(matrix, standardize=True)
    cumulative = structure.cumulative_energy(eigenvalues)

    pa95 = nulls.parallel_analysis(matrix, rng, n_iter=pa_iterations, percentile=95.0)
    pa50 = nulls.parallel_analysis(matrix, rng, n_iter=pa_iterations, percentile=50.0)
    floor = nulls.noise_floor(matrix)

    centred = matrix - matrix.mean(axis=0, keepdims=True)
    scale = centred.std(axis=0, ddof=1)
    scale[scale == 0] = 1.0
    standardised = centred / scale
    correlation = standardised.T @ standardised / (matrix.shape[0] - 1)
    values, vectors = np.linalg.eigh(correlation)
    order = np.argsort(values)[::-1][:n_components]
    unrotated = vectors[:, order] * np.sqrt(np.clip(values[order], 0, None))
    rotated = structure.varimax(unrotated)

    retained = max(1, int(pa95["n_retained"]))
    top = np.abs(rotated)[:, :retained]
    pervasiveness = (top >= loading_threshold).sum(axis=1)
    energy = np.clip(values[order][:retained], 0, None)
    weights = energy / energy.sum() if energy.sum() > 0 else np.full(retained, 1 / retained)
    pervasiveness_weighted = (top >= loading_threshold) @ weights

    prediction = structure.prediction_error_curve(matrix, rng)

    return StructureResult(
        eigenvalues=eigenvalues,
        cumulative=cumulative,
        effective_rank=structure.effective_rank(eigenvalues),
        stable_rank=structure.stable_rank(matrix),
        noise_floor=floor,
        n_retained=retained,
        n_retained_median_rule=max(1, int(pa50["n_retained"])),
        loadings=unrotated,
        rotated=rotated,
        outcome_labels=outcome_labels,
        pervasiveness=pervasiveness,
        pervasiveness_weighted=pervasiveness_weighted,
        mean_prediction_error=prediction["mean"],
        prediction_error_sd=prediction["sd"],
        extras={
            "cumulative_at_retained": float(cumulative[retained - 1]),
            "n_above_noise_floor": float(int((eigenvalues > floor).sum())),
            "best_rank_by_prediction_error": float(int(np.argmin(prediction["mean"])) + 1),
        },
    )
