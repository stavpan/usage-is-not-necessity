"""The convergence analysis: criteria, ranks, agreement, consensus.

Runs offline against the committed corpus. The properties tested here are the
ones the answer depends on, so a change that breaks the argument breaks a test.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from world_impact import convergence as cv

CORPUS = Path(__file__).resolve().parents[1] / "data" / "openalex" / "corpus.json"

pytestmark = pytest.mark.skipif(
    not CORPUS.exists(), reason="automated corpus not fetched (run pixi run fetch-openalex)"
)


@pytest.fixture(scope="module")
def corpus() -> dict:
    return json.loads(CORPUS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def result(corpus) -> cv.ConvergenceResult:
    """All five criteria active, which needs the field-flow input."""
    from world_impact import fields, openalex

    flow = openalex.field_flow(corpus)
    return cv.convergence(corpus, fields.upstreamness(flow))


def test_every_seed_has_every_criterion(result) -> None:
    assert result.n == 520
    for row in result.rows:
        for criterion in cv.CRITERIA:
            assert criterion in row
            assert row[criterion] >= 0.0


def test_rate_is_citations_per_year(result) -> None:
    for row in result.rows:
        assert row["rate"] == pytest.approx(row["citations"] / row["age"])


def test_ranks_are_a_permutation(result) -> None:
    for criterion in cv.CRITERIA:
        values = sorted(result.rank_table[criterion].values())
        assert values == list(range(1, result.n + 1))


def test_agreement_matrix_is_symmetric_with_unit_diagonal(result) -> None:
    for a in cv.CRITERIA:
        assert result.agreement[(a, a)] == pytest.approx(1.0)
        for b in cv.CRITERIA:
            assert result.agreement[(a, b)] == pytest.approx(result.agreement[(b, a)])


def test_reach_and_top_citations_are_redundant(result) -> None:
    """The finding that two of the five criteria are one criterion.

    Asserted so that nobody later reports 'five independent criteria' without
    meeting this number.
    """
    assert result.agreement[("top_citations", "reach")] > 0.98


def test_global_fame_and_load_bearing_are_near_orthogonal(result) -> None:
    """The other uncomfortable finding: total citations barely predict being
    cited by the most-cited works."""
    assert abs(result.agreement[("citations", "top_citations")]) < 0.3


def test_consensus_orders_by_support_then_pessimism(result) -> None:
    top = result.consensus(30)
    assert len(top) == 30
    supports = [row["support"] for row in top]
    assert supports == sorted(supports, reverse=True)
    for row in top:
        assert row["worst_rank"] >= max(row["ranks"].values())
        assert row["support"] <= len(cv.CRITERIA)


def test_the_single_top_of_everything_work_is_an_assay(result) -> None:
    """The headline of the answer: with all five criteria active, exactly one work
    is in the top 50 of every one of them, and it is a protein assay."""
    assert len(result.active) == len(cv.CRITERIA)
    top = result.consensus(5)
    unanimous = [row for row in top if row["support"] == len(result.active)]
    assert len(unanimous) == 1
    assert "FOLIN" in unanimous[0]["title"].upper()


def test_constant_criteria_are_dropped_not_tie_broken(corpus) -> None:
    """Without field-flow data the ``upstream`` criterion is constant, and a
    constant column ranks by tie-break alone -- which would inflate every work's
    support. It must be dropped and named."""
    without = cv.convergence(corpus, upstreamness=None)
    assert "upstream" not in without.active
    assert len(without.active) == len(cv.CRITERIA) - 1
    for row in without.consensus(10):
        assert row["support"] <= len(without.active)


def test_pareto_is_a_small_subset(result) -> None:
    pareto = result.pareto()
    assert 0 < len(pareto) < result.n // 10


def test_movers_are_sorted_by_shift(result) -> None:
    movers = result.movers(20)
    shifts = [row["shift"] for row in movers]
    assert shifts == sorted(shifts, reverse=True)
    for row in movers:
        assert row["shift"] == row["raw_rank"] - row["rate_rank"]


def test_decade_trend_is_ordered_and_sparse_aware(result) -> None:
    trend = cv.decade_trend(result.rows)
    decades = [row["decade"] for row in trend]
    assert decades == sorted(decades)
    assert all(row["n"] >= 5 for row in trend)
    assert all(row["max_rate"] >= row["median_rate"] for row in trend)
