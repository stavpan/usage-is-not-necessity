#!/usr/bin/env python3
"""Generate every figure for the automated (OpenAlex) layer.

Deterministic: same corpus in, same SVG out. Written as a script rather than by
hand so the figures cannot drift from the numbers they illustrate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from world_impact import convergence, fields, figures, openalex

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "figures")
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    corpus = openalex.build_corpus()
    flow = openalex.field_flow(corpus)
    upstream = fields.upstreamness(flow)
    summary = fields.summarise(corpus)

    sizes = {row["name"]: row["works_count"] for row in openalex.fetch_fields()}
    normalised = fields.size_normalised_upstreamness(flow, sizes)

    written = [
        figures.field_flow_heatmap(
            flow, out / "field-flow.svg", "Where each field's references come from"
        ),
        figures.field_supply(
            upstream, out / "field-supply.svg", "Net citation exporters and importers"
        ),
        figures.corpus_timeline(
            corpus["seeds"],
            out / "corpus-timeline.svg",
            fields.classify_work,
            "The 520 most-cited works, 1900-2024, by title class",
        ),
        figures.timeline_lanes(
            corpus["seeds"],
            out / "corpus-lanes.svg",
            lane_key="field",
            title="Multi-field timeline of the most-cited works",
        ),
    ]
    for path in written:
        print(f"wrote {path}  ({path.stat().st_size} bytes)")

    # ---- convergence: the answer to "what are the most important things" ----
    citers_path = ROOT / "data" / "openalex" / "citers.json"
    citers = json.loads(citers_path.read_text(encoding="utf-8")) if citers_path.exists() else {}
    print(f"citers cached for {len(citers)} works")
    result = convergence.convergence(corpus, upstream, citers)
    consensus = result.consensus(30)
    trend = convergence.decade_trend(result.rows)
    written += [
        figures.consensus_atlas(result.rows, consensus, out / "consensus-atlas.svg", label_top=12),
        figures.criterion_agreement(
            result.agreement, convergence.CRITERION_LABEL, out / "criterion-agreement.svg"
        ),
        figures.decade_intensity(trend, out / "decade-intensity.svg"),
    ]
    for path in written[4:]:
        print(f"wrote {path}  ({path.stat().st_size} bytes)")

    # ---- how many criteria are actually independent? ----
    redundant = convergence.redundant_pairs(result.agreement)
    effective = convergence.effective_criteria(result.agreement)
    print(f"\nactive criteria {len(result.active)}, effective {effective}")
    for pair in redundant:
        print(f"  REDUNDANT  {pair['a']} = {pair['b']}  (r={pair['r']})")

    # ---- was the single theory paper a coincidence? ----
    gap = convergence.method_theory_gap(result.rows, fields.classify_work)
    for name, stats in gap["profile"].items():
        print(
            "  {:<13} n={:>3.0f} cit={:>10,.0f} rate={:>8,.1f} prestige={:>9,.0f}".format(
                name, stats["n"], stats["citations"], stats["rate"], stats["citer_prestige"]
            )
        )
    print("  VERDICT:", gap["verdict"])

    # Per-work rank under every criterion, so criterion-dependence is visible
    # rather than asserted. Shannon 1948 is the case that prompted this.
    criterion_spread = []
    for row in consensus:
        ranks = {key: result.rank_table[key][str(row["id"])] for key in result.active}
        criterion_spread.append(
            {
                "title": row["title"],
                "year": row["year"],
                "support": result.support(str(row["id"])),
                "ranks": ranks,
                "best": min(ranks.values()),
                "worst": max(ranks.values()),
                "spread": max(ranks.values()) - min(ranks.values()),
            }
        )
    widest = max(criterion_spread, key=lambda row: row["spread"]) if criterion_spread else None
    if widest:
        print(
            "\n  widest criterion spread in the consensus top 30: "
            f"{widest['spread']} ranks  {(widest['title'] or '')[:48]}"
        )

    report = {
        "summary": summary,
        "size_normalised_upstreamness": normalised,
        "suspect_outliers": fields.suspect_outliers(corpus),
        "convergence": {
            "n": result.n,
            "criteria": list(convergence.CRITERIA),
            "active_criteria": list(result.active),
            "effective_criteria": effective,
            "redundant_pairs": redundant,
            "agreement": {f"{a}|{b}": value for (a, b), value in result.agreement.items()},
            "consensus_top_30": consensus,
            "criterion_spread": criterion_spread,
            "method_theory_gap": gap,
            "movers": result.movers(15),
            "decade_trend": trend,
            "pareto_size": len(result.pareto()),
            "support_histogram": {
                str(support): sum(
                    1 for row in result.rows if result.support(str(row["id"])) == support
                )
                for support in range(len(convergence.CRITERIA) + 1)
            },
        },
    }
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "fields.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    print("wrote reports/fields.json")
    print("outliers flagged:", len(report["suspect_outliers"]))
    for row in report["suspect_outliers"][:5]:
        print(
            "  {}x median  {}  {}  {}".format(
                row["multiple_of_median"],
                row["year"],
                (row["title"] or "")[:52],
                row["field"][:22],
            )
        )


if __name__ == "__main__":
    main()
