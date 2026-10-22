"""Structure: rotation invariance, rank statistics, deduplication."""

from __future__ import annotations

import numpy as np
import pytest

from world_impact import structure


def test_varimax_preserves_the_subspace() -> None:
    """Rotation must not change the column space: that is the whole reason a
    rotation is a labelling choice rather than a modelling choice."""
    loadings = np.random.default_rng(0).normal(size=(12, 4))
    rotated = structure.varimax(loadings)
    assert np.allclose(rotated @ rotated.T, loadings @ loadings.T, atol=1e-8)


def test_varimax_leaves_one_component_alone() -> None:
    loadings = np.random.default_rng(1).normal(size=(8, 1))
    assert np.allclose(structure.varimax(loadings), loadings)


def test_varimax_increases_the_simplicity_criterion() -> None:
    loadings = np.random.default_rng(2).normal(size=(20, 3))
    before = np.sum(np.var(loadings**2, axis=0))
    after = np.sum(np.var(structure.varimax(loadings) ** 2, axis=0))
    assert after >= before - 1e-8


def test_effective_rank_of_a_flat_spectrum_is_p() -> None:
    assert structure.effective_rank(np.ones(7)) == pytest.approx(7.0)


def test_effective_rank_of_a_rank_one_spectrum_is_one() -> None:
    eigenvalues = np.array([10.0, 0.0, 0.0, 0.0])
    assert structure.effective_rank(eigenvalues) == pytest.approx(1.0)


def test_stable_rank_is_bounded_by_the_numerical_rank() -> None:
    matrix = np.random.default_rng(3).normal(size=(10, 4))
    assert structure.stable_rank(matrix) <= 4 + 1e-9


def test_cumulative_energy_ends_at_one() -> None:
    assert structure.cumulative_energy(np.array([3.0, 1.0, 0.5]))[-1] == pytest.approx(1.0)


def test_prediction_error_favours_the_planted_rank() -> None:
    """A rank-2 matrix must be reconstructed better at rank 2 than at rank 1."""
    rng = np.random.default_rng(4)
    factors = rng.normal(size=(40, 2)) @ rng.normal(size=(2, 9))
    curve = structure.prediction_error_curve(
        factors, rng, max_rank=4, n_repeats=6, holdout_fraction=0.2
    )
    assert curve["mean"][1] < curve["mean"][0]
    assert curve["mean"][1] <= curve["mean"][3]


def test_deduplicate_merges_identical_profiles() -> None:
    matrix = np.array([[3.0, 0.0, 0.0], [3.0, 0.0, 0.0], [0.0, 3.0, 0.0]])
    result = structure.deduplicate(matrix, threshold=0.85)
    groups = result["groups"]
    assert len(groups) == 2
    assert max(len(v) for v in groups.values()) == 2


def test_deduplicate_does_not_chain() -> None:
    """Three points at 45 degrees apart: a and c are far, so complete linkage
    must keep all three separate even though a~b and b~c are close."""
    matrix = np.array([[1.0, 0.0], [1.0, 0.8], [0.0, 1.0]])
    result = structure.deduplicate(matrix, threshold=0.9)
    assert len(result["groups"]) == 3
