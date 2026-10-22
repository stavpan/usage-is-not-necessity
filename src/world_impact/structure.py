"""Rotation, rank statistics and out-of-sample rank selection.

Nothing here assumes how many axes exist or what they mean. Rotation does not
change the subspace spanned by the retained components; it changes which
*labels* are defensible, which is why the rotation is a declared parameter
rather than a hidden step.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def varimax(loadings: np.ndarray, max_iter: int = 200, tol: float = 1e-8) -> np.ndarray:
    """Orthogonal varimax rotation of a loading matrix."""
    p, k = loadings.shape
    if k < 2:
        return loadings.copy()
    rotation = np.eye(k)
    previous = 0.0
    for _ in range(max_iter):
        transformed = loadings @ rotation
        column_sums = (transformed**2).sum(axis=0)
        gradient = loadings.T @ (transformed**3 - transformed * column_sums / p)
        u, s, vh = np.linalg.svd(gradient)
        rotation = u @ vh
        objective = float(s.sum())
        if previous and abs(objective - previous) < tol * previous:
            break
        previous = objective
    return loadings @ rotation


def effective_rank(eigenvalues: np.ndarray) -> float:
    """Participation ratio of the spectrum: (sum l)^2 / sum l^2."""
    eigen = np.clip(np.asarray(eigenvalues, dtype=float), 0.0, None)
    return float(eigen.sum() ** 2 / np.sum(eigen**2))


def stable_rank(matrix: np.ndarray) -> float:
    """||A||_F^2 / ||A||_2^2. Bounded above by the numerical rank."""
    singular = np.linalg.svd(np.asarray(matrix, dtype=float), compute_uv=False)
    return float((singular**2).sum() / singular[0] ** 2)


def cumulative_energy(eigenvalues: np.ndarray) -> np.ndarray:
    eigen = np.clip(np.asarray(eigenvalues, dtype=float), 0.0, None)
    return np.cumsum(eigen) / eigen.sum()


def prediction_error_curve(
    matrix: np.ndarray,
    rng: np.random.Generator,
    max_rank: int = 10,
    holdout_fraction: float = 0.25,
    n_repeats: int = 20,
    inner_iterations: int = 60,
) -> dict[str, np.ndarray]:
    """Out-of-sample reconstruction error as a function of rank.

    Implements the spirit of Haslbeck & van Bork (2024): pick the number of
    dimensions that minimises error on entries the model never saw. Held-out
    entries are filled by soft-impute style iterative SVD, so the comparison is
    between rank-k models rather than between a model and a constant.
    """
    matrix = np.asarray(matrix, dtype=float)
    n, p = matrix.shape
    fallback = float(matrix.mean())
    errors = np.zeros((n_repeats, max_rank))
    for repeat in range(n_repeats):
        mask = rng.random((n, p)) < holdout_fraction
        if mask.sum() < 10:
            mask = np.zeros_like(mask, dtype=bool)
            mask[rng.integers(0, n), rng.integers(0, p)] = True
        observed = matrix.copy()
        observed[mask] = np.nan
        for rank in range(1, max_rank + 1):
            filled = np.where(np.isnan(observed), fallback, observed)
            for _ in range(inner_iterations):
                u, s, vh = np.linalg.svd(filled, full_matrices=False)
                approximation = (u[:, :rank] * s[:rank]) @ vh[:rank]
                candidate = np.where(mask, approximation, observed)
                if np.allclose(candidate, filled, atol=1e-10):
                    filled = candidate
                    break
                filled = candidate
            errors[repeat, rank - 1] = float(np.mean((filled[mask] - matrix[mask]) ** 2))
    return {
        "mean": errors.mean(axis=0),
        "sd": errors.std(axis=0),
        "ranks": np.arange(1, max_rank + 1),
    }


def deduplicate(
    matrix: np.ndarray,
    threshold: float = 0.85,
    metric: str = "cosine",
) -> dict[str, Any]:
    """Complete-linkage clustering of developments by outcome profile.

    Complete linkage is required, not a preference: single linkage chains, and
    in the first draft it merged "fiat money" with "antibiotics" through a
    sequence of pairwise links. Two developments belong to one intervention
    type only if *every* cross-pair is similar.
    """
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import pdist

    matrix = np.asarray(matrix, dtype=float)
    distances = pdist(matrix, metric=metric)
    tree = linkage(distances, method="complete")
    labels = fcluster(tree, t=1.0 - threshold, criterion="distance")
    groups: dict[int, list[int]] = {}
    for index, label in enumerate(labels):
        groups.setdefault(int(label), []).append(index)
    return {"labels": labels, "groups": groups, "tree": tree, "threshold": threshold}
