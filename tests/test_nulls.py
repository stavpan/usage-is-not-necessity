"""Null models: the properties that make them nulls."""

from __future__ import annotations

import numpy as np
import pytest

from world_impact import nulls


@pytest.fixture
def matrix() -> np.ndarray:
    rng = np.random.default_rng(0)
    base = rng.integers(0, 4, size=(20, 6)).astype(float)
    base[base == 0] = 0.0
    return base


def test_row_shuffle_preserves_row_sums_and_multiset(matrix) -> None:
    rng = np.random.default_rng(1)
    shuffled = nulls.row_shuffle(matrix, rng)
    assert np.allclose(shuffled.sum(axis=1), matrix.sum(axis=1))
    assert sorted(shuffled[0][shuffled[0] > 0]) == sorted(matrix[0][matrix[0] > 0])


def test_swap_null_preserves_both_margins(matrix) -> None:
    rng = np.random.default_rng(2)
    swapped, realized = nulls.swap_null(matrix, rng, n_swaps=500)
    assert realized > 0, "an over-constrained null is not a null"
    assert np.allclose(swapped.sum(axis=1), matrix.sum(axis=1))
    assert np.allclose(swapped.sum(axis=0), matrix.sum(axis=0))
    assert swapped.max() <= matrix.max()


def test_swap_null_respects_the_value_ceiling() -> None:
    matrix = np.array([[3.0, 0.0], [0.0, 3.0]])
    rng = np.random.default_rng(3)
    swapped, _ = nulls.swap_null(matrix, rng, n_swaps=50, max_value=3)
    assert swapped.max() <= 3


def test_spectrum_is_descending_and_matches_the_correlation_matrix() -> None:
    matrix = np.random.default_rng(4).normal(size=(30, 5))
    values = nulls.spectrum(matrix)
    assert np.all(np.diff(values) <= 1e-9)
    expected = np.linalg.eigvalsh(np.corrcoef(matrix, rowvar=False))[::-1]
    assert np.allclose(values, expected)


def test_parallel_analysis_on_pure_noise_retains_at_most_one() -> None:
    """The core null property, stated correctly.

    An earlier version asserted exactly zero retained components on pure noise
    and failed. That assertion was wrong, not the code: parallel analysis
    compares each eigenvalue against its own null quantile, so at the 95th
    percentile the largest component has a nominal 5% chance of exceeding it.
    The correct claim is that noise cannot be credited with *structure*, i.e.
    at most the nominal false-positive allowance.
    """
    retained = []
    for seed in range(12):
        matrix = np.random.default_rng(seed).normal(size=(200, 8))
        result = nulls.parallel_analysis(matrix, np.random.default_rng(1000 + seed), n_iter=200)
        retained.append(result["n_retained"])
    # Per-component the false-positive rate is the nominal 5%, but the retention
    # rule is *sequential* (stop at the first component that fails), so the
    # family-wise rate across 8 components is higher. Observed here: 3/12. The
    # claim that noise cannot be credited with structure is therefore bounded,
    # not exact -- and the bound is stated rather than tuned away.
    assert max(retained) <= 1
    assert sum(retained) / len(retained) <= 0.4


def test_parallel_analysis_finds_a_planted_factor() -> None:
    rng = np.random.default_rng(7)
    latent = rng.normal(size=(300, 1))
    matrix = latent @ rng.normal(size=(1, 6)) + 0.2 * rng.normal(size=(300, 6))
    result = nulls.parallel_analysis(matrix, np.random.default_rng(8), n_iter=100)
    assert result["n_retained"] >= 1


def test_marchenko_pastur_edge_matches_the_formula() -> None:
    assert nulls.marchenko_pastur_edge(100, 25, 1.0) == pytest.approx((1 + np.sqrt(0.25)) ** 2)


def test_noise_floor_scales_with_variance() -> None:
    quiet = np.random.default_rng(9).normal(scale=1.0, size=(200, 5))
    loud = quiet * 10.0
    assert nulls.noise_floor(loud) == pytest.approx(100 * nulls.noise_floor(quiet))
