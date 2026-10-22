#!/usr/bin/env python3
"""The paper's central figure, and the number that carries its claim.

Left panel: the twelve works the bibliometric instrument ranks highest, by
citations. Right panel: the twelve results the dependency instrument ranks
highest, by transitive reach. The figure is generated rather than drawn, and the
script prints the overlap between the two lists, because "the two rankings are
disjoint" is the claim and it should be a computed number, not an impression.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from world_impact import convergence as cv
from world_impact import fields, figures, openalex
from world_impact.pipeline import SEED, run_analysis

ROOT = Path(__file__).resolve().parents[1]
QUICK = {
    "smaa_draws": 2000,
    "null_iterations": 40,
    "pa_iterations": 100,
    "tensor_null_iterations": 10,
    "screen_trajectories": 5,
    "screen_targets": 1,
}


def normalise(text: str) -> str:
    """Lower-case word set, so overlap is not decided by punctuation."""
    keep = "".join(
        character if character.isalnum() or character == " " else " "
        for character in text.lower()
    )
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
    consensus = result.consensus(args.top)
    by_use = [(row["title"] or "", float(row["citations"])) for row in consensus]

    analysis = run_analysis(seed=SEED, reference_panel=False, **QUICK)
    linkage = analysis["linkage"]
    ranked = linkage["ranked_by_reach"][: args.top]
    by_necessity = [(row["name"], float(row["transitive_reach"])) for row in ranked]

    path = figures.necessity_contrast(
        by_use,
        by_necessity,
        args.out,
        title="The same question, two instruments: use and necessity",
    )
    print(f"wrote {path}  ({path.stat().st_size} bytes)")

    left = {normalise(title) for title, _ in by_use}
    right = {normalise(name) for name, _ in by_necessity}
    shared = left & right
    print(f"\ntop-{args.top} by use vs top-{args.top} by necessity: {len(shared)} shared entries")
    print(f"  highest citation count in the by-use list: {by_use[0][1]:,.0f}")
    print(f"  largest transitive reach: {by_necessity[0][1]:,.0f} of {linkage['n_nodes']}")

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps(
            {
                "top": args.top,
                "by_use": [{"title": title, "citations": value} for title, value in by_use],
                "by_necessity": [
                    {"name": name, "transitive_reach": value} for name, value in by_necessity
                ],
                "shared_entries": sorted(shared),
                "n_shared": len(shared),
                "n_nodes": linkage["n_nodes"],
                "n_edges": linkage["n_edges"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
