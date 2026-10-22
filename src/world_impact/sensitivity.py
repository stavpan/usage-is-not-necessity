"""Which coding decisions actually drive the answer?

The first draft perturbed every cell by +-15% and reported that the ranking was
robust. That is the wrong instrument: it answers "does the answer move if I am
slightly wrong about everything?", when the real question is "which of my 237
coding decisions is the answer *sensitive* to, and how wrong would I have to be
about it?". Those are screening questions with a standard tool.

We use the Morris elementary-effects method (Morris 1991; Campolongo et al.
2007) via SALib. It is designed for models with many inputs and a cheap
evaluator, which is exactly this situation. It returns, per parameter, the mean
absolute elementary effect (mu_star: how much the answer moves) and the SD
(sigma: how much it depends on where you are in the space -- i.e. interaction).
Parameters with high mu_star are the ones that need a second coder.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from SALib.analyze import morris as morris_analyze
from SALib.sample import morris as morris_sample

from world_impact.schema import MAGNITUDE_MAX, MAGNITUDE_MIN


@dataclass
class ScreeningResult:
    """Morris screening of one output against the cell codings."""

    cell_names: list[tuple[int, int]]
    mu_star: np.ndarray
    sigma: np.ndarray
    mu: np.ndarray
    output_name: str
    n_trajectories: int
    n_evaluations: int

    def top(self, k: int = 10) -> list[tuple[tuple[int, int], float, float]]:
        order = np.argsort(-self.mu_star)[:k]
        return [(self.cell_names[i], float(self.mu_star[i]), float(self.sigma[i])) for i in order]


def _ranking_output(matrix: np.ndarray, weights: np.ndarray | None = None) -> np.ndarray:
    """Mean rank of every development under a fixed weighting."""
    n_dev = matrix.shape[0]
    if weights is None:
        weights = np.full(matrix.shape[1], 1.0 / matrix.shape[1])
    scores = matrix @ weights
    order = np.argsort(-scores, kind="stable")
    ranks = np.empty(n_dev, dtype=float)
    ranks[order] = np.arange(1, n_dev + 1)
    return ranks


def screen_coding_decisions(
    matrix: np.ndarray,
    target_index: int,
    rng: np.random.Generator,
    n_trajectories: int = 20,
    num_levels: int = 4,
    weights: np.ndarray | None = None,
) -> ScreeningResult:
    """Morris screen of "the rank of one development" against all cell codings.

    Parameters are the *nonzero* cells, relaxed to a continuous range
    ``[MAGNITUDE_MIN, MAGNITUDE_MAX]``. Cells coded zero are held at zero:
    turning a non-effect into an effect is a different (and much larger) claim
    than being off by a level, and mixing the two would make the screen
    uninterpretable. The consequence is that this screen says nothing about
    *omission* uncertainty, which is a stated limitation.
    """
    matrix = np.asarray(matrix, dtype=float)
    cells = [
        (i, j) for i in range(matrix.shape[0]) for j in range(matrix.shape[1]) if matrix[i, j] > 0
    ]
    if not cells:
        raise ValueError("matrix has no nonzero cells to screen")

    problem = {
        "num_vars": len(cells),
        "names": [f"d{i}_o{j}" for i, j in cells],
        "bounds": [[float(MAGNITUDE_MIN), float(MAGNITUDE_MAX)] for _ in cells],
    }
    sample = morris_sample.sample(
        problem,
        N=n_trajectories,
        num_levels=num_levels,
        seed=int(rng.integers(1 << 31)),
    )

    outputs = np.empty(sample.shape[0])
    for row, parameters in enumerate(sample):
        candidate = matrix.copy()
        for value, (i, j) in zip(parameters, cells, strict=True):
            candidate[i, j] = value
        outputs[row] = _ranking_output(candidate, weights)[target_index]

    analysis = morris_analyze.analyze(
        problem, sample, outputs, num_levels=num_levels, seed=int(rng.integers(1 << 31))
    )
    return ScreeningResult(
        cell_names=cells,
        mu_star=np.asarray(analysis["mu_star"], dtype=float),
        sigma=np.asarray(analysis["sigma"], dtype=float),
        mu=np.asarray(analysis["mu"], dtype=float),
        output_name=f"rank_of_development_{target_index}",
        n_trajectories=n_trajectories,
        n_evaluations=int(sample.shape[0]),
    )


def attenuation_sweep(
    direct_impact: np.ndarray,
    requires: np.ndarray,
    values: tuple[float, ...] = (0.0, 0.2, 0.4, 0.6, 0.8, 0.95),
) -> dict[float, np.ndarray]:
    """Forward linkage for each mediation-attenuation value.

    The attenuation in :func:`world_impact.linkage.linkage` is a normative
    parameter, and a single value for it would be exactly the kind of hidden
    weight this project exists to expose. Reported across the range so the reader
    can see that the *ordering* by forward linkage is stable while the magnitudes
    are not.
    """
    from world_impact.linkage import linkage as run

    return {
        value: run(direct_impact, requires, attenuation=value).forward_linkage for value in values
    }


def rank_correlation(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman correlation, used for the rubric-robustness check."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.size != b.size:
        raise ValueError("arrays must be the same length")
    order_a = np.argsort(np.argsort(a))
    order_b = np.argsort(np.argsort(b))
    return float(np.corrcoef(order_a, order_b)[0, 1])


def jaccard(a: set, b: set) -> float:
    """Set overlap, used for leave-one-column-out stability of the top-k set."""
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def leave_one_out_columns(matrix: np.ndarray, top_k: int = 10) -> dict[str, float]:
    """How much the impact top-k moves when each column is deleted in turn.

    This is the sensitivity of the ranking to the *choice of outcome domains*,
    which is the other half of the first draft's problem: it had invented
    columns and never tested them.
    """
    matrix = np.asarray(matrix, dtype=float)
    full = set(np.argsort(-matrix.sum(axis=1))[:top_k].tolist())
    overlaps = []
    for column in range(matrix.shape[1]):
        keep = [c for c in range(matrix.shape[1]) if c != column]
        subset = set(np.argsort(-matrix[:, keep].sum(axis=1))[:top_k].tolist())
        overlaps.append(jaccard(full, subset))
    overlaps_array = np.array(overlaps)
    return {
        "min": float(overlaps_array.min()),
        "median": float(np.median(overlaps_array)),
        "max": float(overlaps_array.max()),
        "mean": float(overlaps_array.mean()),
    }
