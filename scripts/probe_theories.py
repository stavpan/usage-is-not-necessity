#!/usr/bin/env python3
"""Test the suspicion: is theory systematically under-ranked, or is Shannon lucky?

The consensus top 25 contained exactly one theory paper, and it happened to be the
one this project was originally about. That is the shape of a result that is too
good to be true, so it gets tested directly.

The test: take a hand-picked list of canonical *theoretical* results across
physics, biology, mathematics, economics and computing -- chosen by me, so this is
a probe and not data -- look each up in OpenAlex, and compare its citation count
against its citer prestige. If theory is cited less but by heavier works, then a
count-based ranking measures usage rather than importance and the tool-heavy
consensus is an artifact of the metric. If theory is lower on both, the consensus
is simply what the literature is.
"""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path

from world_impact import convergence as cv
from world_impact import fields, openalex

ROOT = Path(__file__).resolve().parents[1]

# (search title, approximate year, what it is)
THEORIES = [
    ("On the Electrodynamics of Moving Bodies", 1905, "special relativity"),
    ("The Foundation of the General Theory of Relativity", 1916, "general relativity"),
    (
        "A Relation between Distance and Radial Velocity among Extra-Galactic Nebulae",
        1929,
        "Hubble law",
    ),
    ("On the Origin of Species by Means of Natural Selection", 1859, "evolution"),
    ("On the Equilibrium of Heterogeneous Substances", 1878, "chemical thermodynamics"),
    ("A Mathematical Theory of Communication", 1948, "information theory"),
    (
        "On Computable Numbers, with an Application to the Entscheidungsproblem",
        1936,
        "computability",
    ),
    ("The Chemical Basis of Morphogenesis", 1952, "morphogenesis"),
    ("Molecular Structure of Nucleic Acids", 1953, "DNA"),
    ("The Genetical Evolution of Social Behaviour", 1964, "kin selection"),
    ("The Structure of Scientific Revolutions", 1962, "philosophy of science"),
    ("The General Theory of Employment, Interest and Money", 1936, "macroeconomics"),
    ("The Market for Lemons", 1970, "information asymmetry"),
    ("The Problem of Social Cost", 1960, "property rights"),
    ("The Nature of the Firm", 1937, "transaction costs"),
    ("Equilibrium Points in N-Person Games", 1950, "Nash equilibrium"),
    ("An Essay on the Principle of Population", 1798, "population dynamics"),
    ("The Tragedy of the Commons", 1968, "common-pool resources"),
    ("History of Ocean Basins", 1962, "sea-floor spreading"),
    ("Uber formal unentscheidbare Satze", 1931, "incompleteness"),
    ("Endogenous Technological Change", 1990, "growth theory"),
    ("A Theory of Human Motivation", 1943, "motivation"),
    ("The PageRank Citation Ranking", 1998, "network centrality"),
    ("An Inquiry into the Nature and Causes of the Wealth of Nations", 1776, "political economy"),
]


def search(title: str, year: int) -> dict | None:
    """Best OpenAlex match for a title, preferring the stated year window."""
    payload = openalex._get(
        "/works",
        {
            "search": title,
            "filter": f"publication_year:{max(year - 3, 1500)}-{year + 6}",
            "per-page": 5,
            "select": "id,title,publication_year,cited_by_count,primary_topic,type",
        },
    )
    results = payload.get("results") or []
    if not results:
        return None
    scored = [
        (
            difflib.SequenceMatcher(
                None, title.lower(), (row.get("title") or "").lower()
            ).ratio(),
            row,
        )
        for row in results
    ]
    score, best = max(scored, key=lambda pair: pair[0])
    if score < 0.55:
        return None
    return openalex._slim(best)


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "theory-probe.json")
    args = parser.parse_args()

    corpus = openalex.build_corpus()
    upstream = fields.upstreamness(openalex.field_flow(corpus))
    citers_path = ROOT / "data" / "openalex" / "citers.json"
    citers = json.loads(citers_path.read_text(encoding="utf-8")) if citers_path.exists() else {}

    matched: list[dict] = []
    for title, year, label in THEORIES:
        record = search(title, year)
        if record is None:
            print(f"  MISS  {label:<26} {title[:50]}")
            continue
        record["label"] = label
        matched.append(record)
        print(
            "  ok    {:<26} {:>9,} cit  {}  {}".format(
                label, record["cited_by_count"], record["year"], (record["title"] or "")[:40]
            )
        )

    extra = openalex.fetch_citers(
        [record["id"] for record in matched],
        cache=ROOT / "data" / "openalex",
    )
    merged = {**citers, **extra}
    rows = cv.criteria_table(corpus, upstream, merged)
    by_id = {str(row["id"]): row for row in rows}

    print(
        "\ncorpus medians: citations {:,.0f}  rate {:,.1f}  unique citers {:,.0f}  "
        "citer prestige {:,.0f}".format(
            _median([r["citations"] for r in rows]),
            _median([r["rate"] for r in rows]),
            _median([r["unique_citers"] for r in rows]),
            _median([r["citer_prestige"] for r in rows]),
        )
    )
    print("\nCANONICAL THEORIES against the corpus distribution")
    print(
        "  {:<26} {:>11} {:>9} {:>11} {:>9}".format(
            "theory", "citations", "rate", "prestige", "prestige pct"
        )
    )
    for record in matched:
        row = by_id.get(str(record["id"]))
        if row is None:
            continue
        percentile = sum(
            1 for other in rows if other["citer_prestige"] <= row["citer_prestige"]
        ) / len(rows)
        print(
            "  {:<26} {:>11,} {:>9,.1f} {:>11,.0f} {:>8.0%}".format(
                record["label"][:26],
                row["citations"],
                row["rate"],
                row["citer_prestige"],
                percentile,
            )
        )

    gap = cv.method_theory_gap(rows, fields.classify_work)
    print("\nMETHOD vs THEORY GAP over the corpus")
    for name, stats in gap["profile"].items():
        print(
            "  {:<14} n={:>4.0f}  median cit {:>9,.0f}  rate {:>8,.1f}  "
            "unique citers {:>7,.0f}  prestige {:>9,.0f}".format(
                name,
                stats["n"],
                stats["citations"],
                stats["rate"],
                stats["unique_citers"],
                stats["citer_prestige"],
            )
        )
    print("  VERDICT:", gap["verdict"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "theories": matched,
                "corpus_rows": {str(r["id"]): by_id.get(str(r["id"])) for r in matched},
                "method_theory_gap": gap,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
