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
def citers() -> dict:
    path = Path(__file__).resolve().parents[1] / "data" / "openalex" / "citers.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


@pytest.fixture(scope="module")
def result(corpus, citers) -> cv.ConvergenceResult:
    """Every criterion that can be computed, which needs field-flow and citers."""
    from world_impact import fields, openalex

    flow = openalex.field_flow(corpus)
    return cv.convergence(corpus, fields.upstreamness(flow), citers)


def test_every_seed_has_every_criterion(result) -> None:
    assert result.n == 520
    for row in result.rows:
        for criterion in cv.CRITERIA:
            assert criterion in row
            # Every criterion is "more is better", so a rankable value is a number.
            # ``field_zscore`` is the exception that is *not* non-negative: a work
            # below its field's mean citations-per-year is negative by construction.
            assert isinstance(row[criterion], float)


def test_rate_is_citations_per_year(result) -> None:
    for row in result.rows:
        assert row["rate"] == pytest.approx(row["citations"] / row["age"])


def test_ranks_are_a_permutation(result) -> None:
    for criterion in result.active:
        values = sorted(result.rank_table[criterion].values())
        assert values == list(range(1, result.n + 1))


def test_agreement_matrix_is_symmetric_with_unit_diagonal(result) -> None:
    for a in result.active:
        assert result.agreement[(a, a)] == pytest.approx(1.0)
        for b in result.active:
            assert result.agreement[(a, b)] == pytest.approx(result.agreement[(b, a)])


def _rank_correlation(rows: list[dict], a: str, b: str) -> float:
    """Spearman correlation between two criteria, computed on the raw table.

    Needed because the degenerate criteria are no longer in ``result.active`` and
    therefore no longer in the agreement matrix -- but the redundancy that got them
    dropped is exactly what a test should assert.
    """
    import numpy as np

    left = np.array([row[a] for row in rows], dtype=float)
    right = np.array([row[b] for row in rows], dtype=float)
    return float(np.corrcoef(np.argsort(np.argsort(left)), np.argsort(np.argsort(right)))[0, 1])


def test_reach_and_top_citations_are_redundant_and_dropped(result) -> None:
    """The two criteria that were one criterion -- and are now excluded for it.

    Asserted so that nobody later reports "nine independent criteria" without
    meeting this number. The rank correlation is 0.999 and both criteria are
    dropped as degenerate, which is the pair of facts that replaced the earlier
    claim that the instrument applied five independent measures.
    """
    assert _rank_correlation(result.rows, "top_citations", "reach") > 0.95
    assert {"top_citations", "reach"} <= set(result.degenerate)


def test_global_fame_and_load_bearing_are_near_orthogonal(result) -> None:
    """The other uncomfortable finding: total citations barely predict being
    cited by the most-cited works."""
    assert abs(_rank_correlation(result.rows, "citations", "top_citations")) < 0.3
    assert abs(_rank_correlation(result.rows, "citations", "reach")) < 0.3


def test_consensus_orders_by_support_then_pessimism(result) -> None:
    top = result.consensus(30)
    assert len(top) == 30
    supports = [row["support"] for row in top]
    assert supports == sorted(supports, reverse=True)
    for row in top:
        assert row["worst_rank"] >= max(row["ranks"].values())
        assert row["support"] <= len(cv.CRITERIA)


def test_no_work_is_in_the_top_of_every_criterion(result) -> None:
    """No work is unanimous, and the earlier headline claiming one was is retracted.

    A previous version of this test asserted that exactly one work sat in the top 50
    of all five criteria and that it was a protein assay. That was true of the
    criterion set as it stood, and the criterion set was wrong: ``top_citations``
    took five distinct values and ``reach`` took three, so their top ranks were
    tie-breaks rather than measurements. With both dropped, the maximum support is
    5 of 7 and no work is unanimous. The assertion is inverted so the retraction
    cannot be quietly forgotten.
    """
    assert len(result.active) == 8
    assert set(result.degenerate) == {"top_citations", "reach"}
    assert result.uncovered == ()
    top = result.consensus(50)
    assert not [row for row in top if row["support"] == len(result.active)]
    assert max(row["support"] for row in top) == 6


def test_degenerate_criteria_are_dropped_for_too_few_distinct_values(corpus) -> None:
    """``reach`` had three distinct values across 520 works; that cannot rank.

    This is the mechanism behind the retracted headline, so it is asserted directly.
    """
    without = cv.convergence(corpus, upstreamness=None, citers=None)
    assert "upstream" not in without.active
    for absent in ("unique_citers", "citer_prestige", "citer_reach"):
        assert absent not in without.active
    assert set(without.degenerate) == {"top_citations", "reach"}
    for row in without.consensus(10):
        assert row["support"] <= len(without.active)


def test_redundant_criteria_are_named_and_counted(result) -> None:
    """``citations`` and ``unique_citers`` are one criterion at r = 0.988.

    ``top_citations`` and ``reach`` were another at r = 0.999, but both are dropped
    as degenerate before agreement is measured, so only one redundancy survives
    into the matrix.
    """
    pairs = {(row["a"], row["b"]) for row in cv.redundant_pairs(result.agreement)}
    assert ("citations", "unique_citers") in pairs or ("unique_citers", "citations") in pairs
    assert cv.effective_criteria(result.agreement) < len(result.active)


def test_shannon_1948_was_a_criterion_artifact(result) -> None:
    """The suspicion that prompted this work, locked in as a test.

    The consensus once contained exactly one theory paper, and it was Shannon 1948,
    the subject this project started from. That placement came from ``reach``, where
    Shannon held rank 1 -- and ``reach`` had three distinct values, so its rank 1
    was a tie-break among seven tied works. With ``reach`` and ``top_citations``
    dropped, Shannon is not in the top 30 at all, while remaining near the bottom of
    the field-normalised criterion and in the top 40 of the raw citation count.
    """
    shannon = [
        row for row in result.rows if "Mathematical Theory of Communication" in row["title"]
    ]
    assert len(shannon) == 1
    work_id = str(shannon[0]["id"])
    ranks = {criterion: result.rank_table[criterion][work_id] for criterion in result.active}
    assert ranks["field_zscore"] > 400
    assert ranks["citations"] < 50
    assert max(ranks.values()) - min(ranks.values()) > 400
    assert not any(
        "Mathematical Theory of Communication" in (row["title"] or "")
        for row in result.consensus(30)
    )


def test_theory_is_cited_less_often_but_by_heavier_works(result) -> None:
    """The usage-versus-importance distinction, as numbers.

    Methods are cited about 1.3x more often and 1.75x faster, yet theory's citers
    are about 1.6x heavier. So counting criteria measure usage, and usage is not
    importance -- which is why the tool-heavy composition of the consensus has to be
    read as a statement about usage.
    """
    from world_impact import fields

    gap = cv.method_theory_gap(result.rows, fields.classify_work)
    method, theory = gap["profile"]["method"], gap["profile"]["theory"]
    assert method["citations"] > theory["citations"]
    assert method["rate"] > theory["rate"]
    assert theory["citer_prestige"] > method["citer_prestige"]


def test_theory_decays_faster_than_methods_even_age_matched(result) -> None:
    """The refutation of this project's own durability hypothesis, locked in.

    The hypothesis was that a superseded tool loses citations while a foundation does
    not, so theory should have *higher* momentum. The opposite holds: methods 0.98
    against theory 0.87 overall, and 1.06 against 0.80 among works aged 20-34, so the
    gap is not the age gradient. A test rather than a footnote, because a refuted
    hypothesis that is only a sentence can be quietly dropped in a later revision.
    """
    from world_impact import fields

    def median_momentum(group: list[dict]) -> float:
        values = sorted(row["momentum"] for row in group)
        return values[len(values) // 2]

    rows = result.rows
    method = [row for row in rows if fields.classify_work(row["title"]) == "method"]
    theory = [row for row in rows if fields.classify_work(row["title"]) == "theory"]
    assert median_momentum(theory) < median_momentum(method)

    band = [row for row in rows if 20 <= row["age"] <= 34]
    matched_method = [row for row in band if fields.classify_work(row["title"]) == "method"]
    matched_theory = [row for row in band if fields.classify_work(row["title"]) == "theory"]
    assert matched_method and matched_theory
    assert median_momentum(matched_theory) < median_momentum(matched_method)


def test_criteria_missing_their_input_are_dropped_not_zeroed(corpus) -> None:
    """The coverage guard, which the degeneracy guard did not provide.

    Without citer data the three citer criteria are unavailable for every row. Ranking
    on them anyway would score every work at zero -- the criterion would be measuring
    whether the cache was fetched. They must be dropped and named.
    """
    without = cv.convergence(corpus, upstreamness=None, citers=None)
    assert {"unique_citers", "citer_prestige", "citer_reach"} <= set(without.uncovered)
    for criterion in without.uncovered:
        assert criterion not in without.active
        assert criterion not in without.rank_table


def test_momentum_is_derived_from_the_trajectory() -> None:
    """A flat series is momentum 1.0; a decaying one is below it."""
    flat = dict.fromkeys(range(2000, 2025), 10)
    assert cv.trajectory_momentum(flat, 2024) == pytest.approx(1.0, abs=0.02)
    decaying = {**dict.fromkeys(range(2000, 2020), 100), **dict.fromkeys(range(2020, 2025), 5)}
    assert cv.trajectory_momentum(decaying, 2024) < 0.2
    assert cv.trajectory_momentum({}, 2024) == 0.0


def test_pareto_is_a_small_subset(result) -> None:
    """The frontier is small but not tiny, and it grew when the criteria changed.

    Under the original five criteria the frontier was under a tenth of the corpus;
    with citer-based criteria added it is 77 of 520 (14.8%). Asserted as a bound
    rather than a constant, because the size is an output of the criterion set.
    """
    pareto = result.pareto()
    assert 0 < len(pareto) < result.n // 3


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
