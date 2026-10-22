"""Null models.

The first draft used a +-15% lognormal perturbation and concluded its ranking
was robust. That test could not detect the two failures that mattered: it
perturbs magnitudes rather than *structure*, and it leaves the row and column
margins of the matrix intact. Everything here exists to fix that.

``row_shuffle``      permute nonzero cells within each row. Preserves row
                     margins and the magnitude multiset; destroys column
                     structure. Tests "is there any coupling between outcomes?"
``swap_null``        bounded checkerboard swaps, preserving row AND column sums
                     exactly. Tests "is the co-occurrence pattern structured
                     *given* the margins?" -- the null the first draft needed.
``parallel_analysis`` Horn (1965). Tests "how many dimensions are real?" and
                     replaces the arbitrary choice of how many axes to keep.
``noise_floor``      Marchenko-Pastur upper edge. Any eigenvalue below it is
                     indistinguishable from noise.
"""

from __future__ import annotations

import numpy as np

from world_impact.schema import MAGNITUDE_MAX


def row_shuffle(matrix: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Permute the nonzero cells within each row independently."""
    out = np.zeros_like(matrix)
    for i in range(matrix.shape[0]):
        nonzeros = np.flatnonzero(matrix[i] > 0)
        if nonzeros.size == 0:
            continue
        target = rng.choice(matrix.shape[1], size=nonzeros.size, replace=False)
        out[i, target] = matrix[i, nonzeros]
    return out


def swap_null(
    matrix: np.ndarray,
    rng: np.random.Generator,
    n_swaps: int | None = None,
    max_value: int = MAGNITUDE_MAX,
    attempts_per_swap: int = 200,
) -> tuple[np.ndarray, int]:
    """Bounded checkerboard swaps preserving row and column sums exactly.

    A swap takes rows i,k and columns j,l with ``a[i,j] > 0`` and ``a[k,l] > 0``
    and moves one unit from each to ``a[i,l]`` and ``a[k,j]``. Swaps that would
    push a cell above ``max_value`` are rejected so the null stays inside the
    coding range; the realized swap count is returned so callers can report how
    much mixing occurred (an over-constrained null is not a null).

    Returns
    -------
    (null_matrix, n_realized_swaps)
    """
    out = matrix.astype(float).copy()
    rows, cols = out.shape
    target = n_swaps if n_swaps is not None else 20 * int((out > 0).sum())
    realized = 0
    for _ in range(target):
        for _ in range(attempts_per_swap):
            i, k = rng.integers(0, rows, size=2)
            j, other = rng.integers(0, cols, size=2)
            if i == k or j == other:
                continue
            if out[i, j] <= 0 or out[k, other] <= 0:
                continue
            if out[i, other] >= max_value or out[k, j] >= max_value:
                continue
            out[i, j] -= 1
            out[k, other] -= 1
            out[i, other] += 1
            out[k, j] += 1
            realized += 1
            break
    return out, realized


def spectrum(matrix: np.ndarray, standardize: bool = True) -> np.ndarray:
    """Descending eigenvalues of the (optionally standardized) covariance.

    ``standardize=True`` analyses the correlation matrix, so every outcome
    domain has equal footing regardless of how many developments touch it.
    ``standardize=False`` gives raw covariance, sensitive to column margins;
    reported as a sensitivity, never as the headline.
    """
    matrix = np.asarray(matrix, dtype=float)
    centred = matrix - matrix.mean(axis=0, keepdims=True)
    if standardize:
        scale = centred.std(axis=0, ddof=1)
        scale[scale == 0] = 1.0
        centred = centred / scale
    covariance = centred.T @ centred / max(matrix.shape[0] - 1, 1)
    return np.sort(np.linalg.eigvalsh(covariance))[::-1]


def parallel_analysis(
    matrix: np.ndarray,
    rng: np.random.Generator,
    n_iter: int = 500,
    percentile: float = 95.0,
    standardize: bool = True,
) -> dict[str, np.ndarray | float | int]:
    """Horn's parallel analysis against random data of the same shape.

    A component is retained while its eigenvalue exceeds the ``percentile``-th
    percentile of the null eigenvalues. ``percentile=50`` is Horn's original
    rule; 95 is the Glorfeld (1995) revision and the current default
    recommendation (Zwick & Velicer 1986).

    Reported as a bound, not a verdict: this is the component version on a
    sparse ordinal matrix, so it is cross-checked against the
    Marchenko-Pastur floor and against the out-of-sample prediction-error
    criterion of Haslbeck & van Bork (2024).
    """
    matrix = np.asarray(matrix, dtype=float)
    n, p = matrix.shape
    observed = spectrum(matrix, standardize=standardize)

    null = np.empty((n_iter, p))
    generator = np.random.default_rng(rng.integers(1 << 31))
    for it in range(n_iter):
        null[it] = spectrum(generator.normal(size=(n, p)), standardize=standardize)

    threshold = np.percentile(null, percentile, axis=0)
    exceeds = observed > threshold
    n_retained = int(np.sum(np.cumprod(exceeds)))
    return {
        "observed": observed,
        "threshold": threshold,
        "null_mean": null.mean(axis=0),
        "n_retained": n_retained,
        "percentile": float(percentile),
    }


def marchenko_pastur_edge(n: int, p: int, variance: float = 1.0) -> float:
    """Largest eigenvalue of pure noise: ``sigma^2 (1 + sqrt(p/n))^2``."""
    return variance * (1.0 + np.sqrt(p / n)) ** 2


def noise_floor(matrix: np.ndarray) -> float:
    """Marchenko-Pastur threshold for this matrix's shape and scale."""
    matrix = np.asarray(matrix, dtype=float)
    n, p = matrix.shape
    centred = matrix - matrix.mean(axis=0, keepdims=True)
    return marchenko_pastur_edge(n, p, float(centred.var(ddof=1)))
