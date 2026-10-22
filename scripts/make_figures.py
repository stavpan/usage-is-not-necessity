#!/usr/bin/env python3
"""Generate every figure for the automated (OpenAlex) layer.

Deterministic: same corpus in, same SVG out. Written as a script rather than by
hand so the figures cannot drift from the numbers they illustrate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from world_impact import fields, figures, openalex

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

    report = {
        "summary": summary,
        "size_normalised_upstreamness": normalised,
        "suspect_outliers": fields.suspect_outliers(corpus),
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
