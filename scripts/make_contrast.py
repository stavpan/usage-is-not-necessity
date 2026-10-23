#!/usr/bin/env python3
"""The paper's central figure, and the number that carries its claim.

Left panel: the twelve works the bibliometric instrument ranks highest, by citations.
Right panel: the twelve results the dependency instrument ranks highest, by transitive
reach. The script prints the overlap between the two lists, because "the two rankings
are disjoint" is the claim and it should be a computed number, not an impression.

Self-contained: transitive reach is computed here from `data/results.yml`, so the
figure does not depend on an analysis pipeline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from world_impact import convergence as cv
from world_impact import fields, figures, linkage, openalex

ROOT = Path(__file__).resolve().parents[1]


def reach_of(rows: list[dict]) -> dict[str, int]:
    """Number of results that transitively depend on each result.

    Delegates to `linkage.reach_from_rows` so there is one implementation. A local
    recursive version here returned 24 where the correct answer is 58.
    """
    return linkage.reach_from_rows(rows)


def normalise(text: str) -> str:
    """Lower-case word set, so overlap is not decided by punctuation."""
    keep = "".join(c if c.isalnum() or c == " " else " " for c in str(text).lower())
    return " ".join(sorted(keep.split()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--out", type=Path, default=ROOT / "figures" / "necessity-contrast.svg")
    parser.add_argument("--json", type=Path, default=ROOT / "reports" / "contrast.json")
    args = parser.parse_args()

    corpus = openalex.build_corpus()
    upstream = fields.upstreamness(openalex.field_flow(corpus))
    citers = json.loads((ROOT / "data" / "openalex" / "citers.json").read_text(encoding="utf-8"))
    result = cv.convergence(corpus, upstream, citers)
    by_use = [(row["title"] or "", float(row["citations"])) for row in result.consensus(args.top)]

    rows = yaml.safe_load((ROOT / "data" / "results.yml").read_text(encoding="utf-8"))
    reach = reach_of(rows)
    names = {row["id"]: row.get("name") or row["id"] for row in rows}
    by_necessity = [
        (names[node], float(value))
        for node, value in sorted(reach.items(), key=lambda pair: -pair[1])[: args.top]
    ]

    path = figures.necessity_contrast(
        by_use, by_necessity, args.out, title="The same question, two instruments"
    )
    print(f"wrote {path}  ({path.stat().st_size} bytes)")

    left = {normalise(title) for title, _ in by_use}
    right = {normalise(name) for name, _ in by_necessity}
    shared = left & right
    print(f"\ntop-{args.top} by use vs top-{args.top} by necessity: {len(shared)} shared entries")
    print(f"  highest citation count in the by-use list: {by_use[0][1]:,.0f}")
    print(f"  largest transitive reach: {by_necessity[0][1]:,.0f} of {len(rows)}")

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps(
            {
                "top": args.top,
                "by_use": [{"title": t, "citations": v} for t, v in by_use],
                "by_necessity": [{"name": n, "transitive_reach": v} for n, v in by_necessity],
                "shared_entries": sorted(shared),
                "n_shared": len(shared),
                "n_nodes": len(rows),
                "n_edges": sum(len(row.get("requires") or []) for row in rows),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
