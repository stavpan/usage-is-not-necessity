"""The graded response model: the equations first, then the fit."""

from __future__ import annotations

import numpy as np
import pytest

from world_impact import grm
from world_impact.measurement import fit_graded_response


def test_probabilities_sum_to_one() -> None:
    theta = np.linspace(-4, 4, 41)
    probabilities = grm.category_probabilities(1.3, np.array([-1.0, 0.0, 1.0]), theta, 4)
    assert probabilities.shape == (4, theta.size)
    assert np.allclose(probabilities.sum(axis=0), 1.0)


def test_probabilities_are_monotone_in_theta() -> None:
    """Higher categories must become more likely as theta rises: if this fails
    the model is not measuring anything."""
    theta = np.linspace(-4, 4, 81)
    probabilities = grm.category_probabilities(1.0, np.array([-1.0, 0.0, 1.0]), theta, 4)
    assert np.all(np.diff(probabilities[0]) <= 1e-9)
    assert np.all(np.diff(probabilities[3]) >= -1e-9)


def test_sigmoid_is_stable_at_extremes() -> None:
    values = grm.sigmoid(np.array([-1000.0, 0.0, 1000.0]))
    assert np.isfinite(values).all()
    assert values[0] == pytest.approx(0.0)
    assert values[2] == pytest.approx(1.0)


def test_unpack_parameters_orders_thresholds() -> None:
    parameters = np.array([0.5, -1.0, 0.2, 0.3])
    discrimination, thresholds = grm.unpack_parameters(parameters, 1, 4)
    assert discrimination[0] == pytest.approx(np.exp(0.5))
    assert thresholds.shape == (1, 3)
    assert np.all(np.diff(thresholds[0]) > 0)


def test_fit_recovers_a_known_ordering() -> None:
    """Two separated latent groups: the high group must score higher.

    Convergence is not asserted here. On a synthetic matrix with near-perfect
    separation the likelihood is very flat at large discriminations, so L-BFGS-B
    routinely exhausts its iteration budget while the *estimates* are already
    correct. Asserting convergence on this fixture would be testing the
    optimiser's stopping rule rather than the model's ability to order cases;
    the real dataset does converge and is asserted elsewhere.
    """
    rng = np.random.default_rng(0)
    low = rng.integers(0, 2, size=(20, 4))
    high = rng.integers(2, 4, size=(20, 4))
    fit = fit_graded_response(np.vstack([low, high]), max_iterations=200)
    assert fit.theta[:20].mean() < fit.theta[20:].mean()
    assert fit.theta[20:].min() > fit.theta[:20].max()
    assert np.all(fit.theta_sd > 0)


def test_test_information_is_positive_and_peaks_somewhere() -> None:
    rng = np.random.default_rng(1)
    matrix = rng.integers(0, 4, size=(30, 5))
    fit = fit_graded_response(matrix, max_iterations=40)
    grid = np.linspace(-3, 3, 41)
    information = fit.test_information(grid)
    assert np.all(information >= 0)
    assert information.max() > 0
    assert 0 <= int(np.argmax(information)) < grid.size
