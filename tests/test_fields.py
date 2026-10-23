"""The automated layer: corpus invariants, upstreamness, classification.

Runs offline against the committed corpus, so the analysis is testable without
network access. The corpus itself is the artefact that makes the layer
reproducible; regenerating it needs `pixi run fetch-openalex`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from world_impact import fields, openalex

CORPUS = Path(__file__).resolve().parents[1] / "data" / "openalex" / "corpus.json"

pytestmark = pytest.mark.skipif(
    not CORPUS.exists(), reason="automated corpus not fetched (run pixi run fetch-openalex)"
)


@pytest.fixture(scope="module")
def corpus() -> dict:
    return json.loads(CORPUS.read_text(encoding="utf-8"))


def test_corpus_is_non_trivial(corpus) -> None:
    assert corpus["n_seeds"] > 100
    assert corpus["n_fields"] == 26
    for work in corpus["seeds"]:
        assert work["id"].startswith("W")
        assert work["field"]
        assert work["cited_by_count"] > 0


def test_reference_coverage_is_high_enough_to_use(corpus) -> None:
    flow = openalex.field_flow(corpus)
    # 0.769 rather than the ~0.97 of the shallower corpus, and the trade is deliberate:
    # capturing up to 100 references per seed tripled the reference set (5,870 to
    # 15,671) while metadata resolution was capped at 12,000 requests, so the unresolved
    # residue is the lowest-in-degree third. Coverage is lower and the graph is much
    # deeper. A threshold of 0.7 asserts that the flow matrix is usable without
    # pretending the trade did not happen.
    assert flow["reference_coverage"] > 0.7, "a low-coverage flow matrix is not usable"


def test_flow_matrix_is_square_and_matches_labels(corpus) -> None:
    flow = openalex.field_flow(corpus)
    n = len(flow["fields"])
    assert len(flow["matrix"]) == n
    assert all(len(row) == n for row in flow["matrix"])
    assert flow["n_references_resolved"] == sum(sum(row) for row in flow["matrix"])


def test_upstreamness_conserves_flow(corpus) -> None:
    flow = openalex.field_flow(corpus)
    upstream = fields.upstreamness(flow)
    total_in = sum(stats["incoming"] for stats in upstream.values())
    total_out = sum(stats["outgoing"] for stats in upstream.values())
    assert total_in == pytest.approx(total_out)
    for stats in upstream.values():
        if stats["outgoing"]:
            assert stats["ratio"] == pytest.approx(stats["incoming"] / stats["outgoing"])


def test_classify_work_known_cases() -> None:
    assert (
        fields.classify_work("A Rapid and Sensitive Method for the Quantitation of Microgram")
        == "method"
    )
    assert fields.classify_work("Generalized Gradient Approximation Made Simple") == "method"
    assert (
        fields.classify_work("R: A Language and Environment for Statistical Computing") == "method"
    )
    assert (
        fields.classify_work("On the Origin of Species by Means of Natural Selection") == "theory"
    )
    assert fields.classify_work("Zzyzx") == "unclassified"


def test_method_share_is_a_distribution(corpus) -> None:
    shares = fields.method_share(corpus)
    assert shares
    for stats in shares.values():
        assert stats["method"] + stats["theory"] + stats["unclassified"] == stats["n"]
        assert 0.0 <= stats["method_share"] <= 1.0


def test_cross_field_hubs_are_ranked_and_classified(corpus) -> None:
    hubs = fields.cross_field_hubs(corpus, top=15)
    assert hubs
    counts = [row["n_citing_fields"] for row in hubs]
    assert counts == sorted(counts, reverse=True)
    for row in hubs:
        assert row["classification"] in {"method", "theory", "unclassified"}
        assert row["n_citing_fields"] == len(row["citing_fields"])


def test_outlier_flag_catches_the_known_data_error(corpus) -> None:
    """The 2020 'Radiation Resistant Camera System' record has ~800k citations in
    a field whose median seed has ~30k. It is a mis-merged OpenAlex record, and
    the flag exists so a data error cannot sit silently at the top of a ranking.
    """
    flagged = fields.suspect_outliers(corpus)
    assert flagged
    assert any("Radiation Resistant Camera" in (row["title"] or "") for row in flagged)
    assert all(row["multiple_of_median"] > 8.0 for row in flagged)


def test_size_normalisation_reorders_or_explains(corpus) -> None:
    """Normalising by works_count must change something, or it is decoration."""
    flow = openalex.field_flow(corpus)
    raw = fields.upstreamness(flow)
    sizes = {row["name"]: row["works_count"] for row in openalex.fetch_fields()}
    normalised = fields.size_normalised_upstreamness(flow, sizes)
    assert normalised
    raw_top = max(raw, key=lambda name: raw[name]["ratio"])
    norm_top = max(normalised, key=lambda name: normalised[name]["incoming_per_10k_works"])
    assert raw_top != norm_top or len(normalised) < len(raw)
