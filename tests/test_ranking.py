"""Ranking: dominance, weights, SMAA invariants."""

from __future__ import annotations

import numpy as np
import pytest

from world_impact import ranking


def test_pareto_frontier_keeps_only_undominated() -> None:
    frontier = ranking.pareto_frontier(
        {"a": np.array([3.0, 1.0, 2.0]), "b": np.array([3.0, 2.0, 1.0])}
    )
    assert frontier.tolist() == [True, False, False]


def test_pareto_frontier_is_invariant_to_duplicates() -> None:
    """A tie is not a domination: two identical developments are both kept."""
    frontier = ranking.pareto_frontier({"a": np.array([1.0, 1.0]), "b": np.array([1.0, 1.0])})
    assert frontier.all()


def test_roc_weights_sum_to_one_and_decrease() -> None:
    weights = ranking.roc_weights(5)
    assert weights.sum() == pytest.approx(1.0)
    assert np.all(np.diff(weights) < 0)


def test_smaa_rank_acceptability_is_a_distribution() -> None:
    matrix = np.array([[3.0, 1.0], [1.0, 3.0], [2.0, 2.0]])
    result = ranking.smaa(matrix, np.random.default_rng(0), n_draws=400, local_draws=20)
    assert np.allclose(result.rank_acceptability.sum(axis=1), 1.0)
    assert np.allclose(result.acceptance, result.rank_acceptability[:, 0])
    assert (result.mean_rank >= 1).all()
    assert (result.mean_rank <= 3).all()


def test_smaa_is_invariant_to_a_common_shift() -> None:
    """Adding a constant to every score must not change the ordering, so the
    rank acceptability of an identical matrix plus a constant is unchanged."""
    matrix = np.array([[3.0, 1.0], [1.0, 3.0], [2.0, 2.0]])
    base = ranking.smaa(matrix, np.random.default_rng(1), n_draws=200, local_draws=10)
    shifted = ranking.smaa(matrix + 100.0, np.random.default_rng(1), n_draws=200, local_draws=10)
    assert np.allclose(base.rank_acceptability, shifted.rank_acceptability)


def test_smaa_accepts_a_list_of_value_draws() -> None:
    matrix = np.array([[3.0, 1.0], [1.0, 3.0]])
    draws = [matrix, matrix * 0.9, matrix * 1.1]
    result = ranking.smaa(draws, np.random.default_rng(2), n_draws=300, local_draws=10)
    assert result.n_draws == 300


def test_best_rank_interval_contains_the_acceptance() -> None:
    matrix = np.array([[3.0, 1.0], [1.0, 3.0], [2.0, 2.0]])
    result = ranking.smaa(matrix, np.random.default_rng(3), n_draws=600, local_draws=10)
    for index in range(3):
        low, high = result.best_rank_interval(index, mass=0.8)
        assert 1 <= low <= high <= 3


def test_pairwise_dominance_is_antisymmetric() -> None:
    matrix = np.array([[3.0, 1.0], [1.0, 3.0]])
    dominance = ranking.pairwise_dominance(matrix, np.random.default_rng(4), n_draws=300)
    assert dominance[0, 1] + dominance[1, 0] == pytest.approx(1.0)
    assert np.allclose(np.diag(dominance), 0.0)
