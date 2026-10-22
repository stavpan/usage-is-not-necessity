"""Sources of uncertainty, kept separate from the estimators that consume them.

Three kinds, deliberately not conflated:

``value``        what the true magnitude of a cell might be, given the coding.
``weight``       what the outcome weights might legitimately be.
``structure``    what the matrix might have looked like with different coding
                 decisions (see :mod:`world_impact.sensitivity`).

Only the first two are distributional; the third is a screening problem,
because 237 coding decisions cannot be given a joint prior honestly.
"""

from __future__ import annotations

import numpy as np

from world_impact.grm import category_probabilities
from world_impact.measurement import GradedResponseFit


def predictive_draws(
    fit: GradedResponseFit,
    matrix: np.ndarray,
    rng: np.random.Generator,
    n_draws: int = 32,
) -> list[np.ndarray]:
    """Draw alternative matrices from the measurement model's predictive law.

    Each nonzero cell is resampled from ``P(x = k | theta_i, item_j)`` at that
    development's EAP theta: the model's own statement of how uncertain each
    coded magnitude is. These feed the value uncertainty in
    :func:`world_impact.ranking.smaa`.

    Zeros are held fixed. The instrument as built says nothing about cells coded
    absent, so resampling them would invent information; that is a stated
    limitation, not an oversight.
    """
    data = np.asarray(matrix, dtype=int)
    n_persons, n_items = data.shape
    draws: list[np.ndarray] = []
    for _ in range(n_draws):
        sample = np.zeros_like(data)
        for i in range(n_persons):
            for j in range(n_items):
                if data[i, j] == 0:
                    continue
                probabilities = category_probabilities(
                    fit.discrimination[j],
                    fit.thresholds[j],
                    np.array([fit.theta[i]]),
                    fit.n_categories,
                )[:, 0]
                sample[i, j] = rng.choice(fit.n_categories, p=probabilities)
        draws.append(sample.astype(float))
    return draws


def dirichlet_draws(
    rng: np.random.Generator, n_outcomes: int, n_draws: int, alpha: float = 1.0
) -> np.ndarray:
    """(n_draws, n_outcomes) weight vectors, uniform over the simplex by default."""
    return rng.dirichlet(np.full(n_outcomes, alpha), size=n_draws)


def disagreement(matrices: list[np.ndarray]) -> np.ndarray:
    """Per-cell SD across a set of candidate matrices."""
    stack = np.stack(matrices)
    return stack.std(axis=0)
