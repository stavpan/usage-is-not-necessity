"""Probability machinery for the graded response model (Samejima 1969).

Separated from :mod:`world_impact.measurement` so the equations can be unit
tested against their defining properties -- monotonicity in theta, probabilities
summing to one, thresholds ordered -- without fitting anything.
"""

from __future__ import annotations

import numpy as np


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Numerically stable logistic.

    The naive ``1 / (1 + exp(-x))`` overflows in exp for large negative x, which
    the optimiser will reach routinely when it explores extreme discriminations.
    Branching on the sign keeps exp's argument non-positive in both branches.
    """
    values = np.asarray(x, dtype=float)
    out = np.empty_like(values)
    positive = values >= 0
    out[positive] = 1.0 / (1.0 + np.exp(-values[positive]))
    exp_values = np.exp(values[~positive])
    out[~positive] = exp_values / (1.0 + exp_values)
    return out


def category_probabilities(
    discrimination: float,
    thresholds: np.ndarray,
    theta: np.ndarray,
    n_categories: int,
) -> np.ndarray:
    """(n_categories, n_theta) probabilities for categories 0..K-1.

    ``P*(x >= k) = sigmoid(a (theta - b_k))`` and ``P(x = k)`` is the successive
    difference, with ``P(x = 0) = 1 - P*(x >= 1)``.
    """
    cumulative = np.ones((n_categories, theta.size))
    for k, threshold in enumerate(thresholds, start=1):
        cumulative[k:] *= sigmoid(discrimination * (theta - threshold))
    probabilities = np.empty_like(cumulative)
    probabilities[:-1] = cumulative[:-1] - cumulative[1:]
    probabilities[-1] = cumulative[-1]
    return np.clip(probabilities, 1e-12, 1.0)


def category_derivative(
    discrimination: float,
    thresholds: np.ndarray,
    theta: np.ndarray,
    n_categories: int,
) -> np.ndarray:
    """d/dtheta of each category probability (for Fisher information)."""
    cumulative = np.ones((n_categories, theta.size))
    derivative = np.zeros((n_categories, theta.size))
    for k, threshold in enumerate(thresholds, start=1):
        sig = sigmoid(discrimination * (theta - threshold))
        cumulative[k:] = cumulative[k:] * sig
        derivative[k:] = derivative[k:] * sig + cumulative[k:] * discrimination * (1.0 - sig)
    result = np.empty_like(cumulative)
    result[:-1] = derivative[:-1] - derivative[1:]
    result[-1] = derivative[-1]
    return result


def unpack_parameters(
    parameters: np.ndarray, n_items: int, n_categories: int
) -> tuple[np.ndarray, np.ndarray]:
    """Unconstrained vector -> (discrimination > 0, strictly ordered thresholds).

    Parameterised as ``a = exp(p0)`` and ``b_k = b_1 + cumsum(exp(dp))`` so the
    optimiser can never produce a negative discrimination or crossing
    thresholds, which removes the need for constrained optimisation and the
    label-switching it invites.
    """
    block = n_categories
    reshaped = parameters.reshape(n_items, block)
    discrimination = np.exp(reshaped[:, 0])
    first = reshaped[:, 1]
    increments = np.exp(reshaped[:, 2:])
    thresholds = np.column_stack([first, first[:, None] + np.cumsum(increments, axis=1)])
    return discrimination, thresholds
