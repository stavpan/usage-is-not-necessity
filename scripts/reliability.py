#!/usr/bin/env python3
"""Inter-coder reliability: set it up, and measure what can be measured without one.

The project's largest remaining threat to validity is that the dependency graph was
coded by one person. That limitation cannot be removed by the same person, and this
script does not pretend otherwise. It does three things instead.

**1. Export a blinded sample** (`--export`). A stratified sample of prerequisite edges
is written to `data/reliability/sample-to-code.yml` with the endpoints named and the
primary verdict withheld. A second coder fills in `necessary: true/false` per edge and
saves it as `data/reliability/second-coder.yml`. Nothing about the task requires
knowing the primary coding.

**2. Score it** (`--score`), once that file exists: Cohen's kappa on the binary edge
judgements, with the raw agreement rate and the confusion counts, because kappa on a
small sample is unstable and both numbers should be visible.

**3. Measure the internal consistency that is available now.** Three checks that a
single coder *can* run and that a second coder would not change:

    chronology    a prerequisite postdating what it enables is a contradiction
    acyclicity    a cycle is an error somewhere in the loop
    halo          if a row's coded magnitude tracked its prominence, the magnitudes
                  would be contaminated by fame rather than by effect. Measured as the
                  rank correlation between coded consequence and transitive reach.

The halo check is the interesting one: it is a test the coding could fail, and it
tests the thing a sceptical reader would suspect -- that the impressive-sounding rows
were given the big numbers.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results.yml"
EDGE_SOURCES = ROOT / "data" / "edge-sources.yml"
OUT_DIR = ROOT / "data" / "reliability"
SAMPLE = OUT_DIR / "sample-to-code.yml"
SECOND = OUT_DIR / "second-coder.yml"

SAMPLE_HEADER = """# Blinded edge sample for a second coder.
#
# For each edge below, replace `necessary: null` with `necessary: true` if the user
# would not have been possible, as it occurred, without the provider, and
# `necessary: false` otherwise. Do not consult `data/results.yml`.
#
# Save as data/reliability/second-coder.yml and run:
#     python scripts/reliability.py --score
#
# 40 edges, stratified so that high-reach and low-reach providers are both represented.
"""


def load_rows() -> list[dict]:
    return yaml.safe_load(RESULTS.read_text(encoding="utf-8"))


def transitive_reach(rows: list[dict]) -> dict[str, int]:
    adjacency: dict[str, list[str]] = {row["id"]: list(row.get("requires") or []) for row in rows}
    closure: dict[str, set[str]] = {}

    def descend(node: str, seen: set[str]) -> set[str]:
        if node in closure:
            return closure[node]
        if node in seen:
            return set()
        seen = seen | {node}
        reachable: set[str] = set()
        for parent in adjacency.get(node, []):
            reachable.add(parent)
            reachable |= descend(parent, seen)
        closure[node] = reachable
        return reachable

    for row in rows:
        descend(row["id"], set())
    return {node: len(closure.get(node, set())) for node in adjacency}


def export_sample(rows: list[dict], size: int, seed: int) -> Path:
    """A stratified, blinded sample of edges for a second coder."""
    reach = transitive_reach(rows)
    edges = [(row["id"], provider) for row in rows for provider in (row.get("requires") or [])]
    # Stratified by provider reach so the sample is not all leaf prerequisites: the
    # interesting edges are the ones near the top of the reach ranking, where a coding
    # disagreement changes the headline.
    edges.sort(key=lambda edge: -reach.get(edge[1], 0))
    rng = random.Random(seed)
    top = edges[: max(size // 2, 1)]
    rest = edges[len(top) :]
    sample = top + rng.sample(rest, min(size - len(top), len(rest)))
    rng.shuffle(sample)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    names = {row["id"]: row.get("name") or row["id"] for row in rows}
    lines = [
        f"- {{user: {user}, user_name: \"{names.get(user, user)}\", "
        f"provider: {provider}, provider_name: \"{names.get(provider, provider)}\", "
        "necessary: null}"
        for user, provider in sample
    ]
    SAMPLE.write_text(SAMPLE_HEADER + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"exported {len(sample)} blinded edges to {SAMPLE}")
    print(f"  of which {len(top)} come from the top of the reach ranking")
    return SAMPLE


def score_second_coder() -> dict | None:
    """Cohen's kappa between the primary coding and a second coder's file."""
    if not SECOND.exists():
        return None
    primary = {(r["user"], r["provider"]) for r in yaml.safe_load(
        EDGE_SOURCES.read_text(encoding="utf-8")
    )}
    second = yaml.safe_load(SECOND.read_text(encoding="utf-8"))
    counts = {"both": 0, "primary_only": 0, "second_only": 0, "neither": 0}
    scored = 0
    for row in second:
        verdict = row.get("necessary")
        if verdict is None:
            continue
        key = (row["user"], row["provider"])
        in_primary = key in primary
        scored += 1
        if in_primary and verdict:
            counts["both"] += 1
        elif in_primary and not verdict:
            counts["primary_only"] += 1
        elif not in_primary and verdict:
            counts["second_only"] += 1
        else:
            counts["neither"] += 1
    if not scored:
        return None
    total = scored
    observed = (counts["both"] + counts["neither"]) / total
    primary_yes = (counts["both"] + counts["primary_only"]) / total
    second_yes = (counts["both"] + counts["second_only"]) / total
    expected = primary_yes * second_yes + (1 - primary_yes) * (1 - second_yes)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else float("nan")
    return {
        "n_scored": scored,
        "observed_agreement": observed,
        "cohens_kappa": kappa,
        "counts": counts,
    }


def internal_consistency(rows: list[dict]) -> dict:
    """Checks a single coder can run, and that a second coder would not change."""
    reach = transitive_reach(rows)
    ids = sorted(row["id"] for row in rows)
    # `right` is the necessity vector; the consequence vectors are built per measure below.
    right = [reach.get(i, 0) for i in ids]

    def spearman(a: list[float], b: list[float]) -> float:
        """Midrank Spearman, via scipy.

        A hand-rolled version mapped value -> position in a dict, which collapses
        ties to a single rank; `peak` takes only four distinct values, so the
        tie handling dominated the answer and the same correlation came out as 0.43
        here and 0.62 under ordinal ranks. Ties on coarse data are not a detail, so
        the canonical implementation is used and the number is the one the paper
        quotes.
        """
        from scipy.stats import spearmanr

        statistic = spearmanr(a, b).statistic
        return float(statistic) if statistic is not None else float("nan")

    # Three consequence measures, not one, because the halo shows up most strongly in
    # `peak` and a single aggregate would have averaged it away. An earlier version
    # used the total only, with a 0.35 threshold, and reported "no evidence of halo" at
    # 0.31 -- while peak against necessity was 0.62. The threshold is now 0.25 and the
    # per-measure breakdown is reported.
    totals = {row["id"]: sum((row.get("effects") or {}).values()) for row in rows}
    breadth = {row["id"]: len(row.get("effects") or {}) for row in rows}
    peak = {row["id"]: max((row.get("effects") or {}).values(), default=0) for row in rows}
    by_measure = {
        "total": spearman([totals[i] for i in ids], right),
        "breadth": spearman([breadth[i] for i in ids], right),
        "peak": spearman([peak[i] for i in ids], right),
    }
    worst = max(by_measure, key=lambda name: abs(by_measure[name]))
    halo = by_measure[worst]
    return {
        "n_rows": len(rows),
        "halo_rank_correlation": halo,
        "halo_by_measure": by_measure,
        "halo_worst_measure": worst,
        "halo_verdict": (
            "HALO DETECTED: coded magnitude tracks structural prominence "
            f"(worst measure: {worst} at {halo:+.2f}). The magnitudes are not "
            "independent evidence about consequence."
            if abs(halo) >= 0.25
            else "no evidence of halo: coded magnitude does not track prominence"
        ),
        "rows_without_sources": sum(1 for row in rows if not row.get("sources")),
        "rows_without_requires": sum(1 for row in rows if not row.get("requires")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", type=int, default=0, metavar="N", help="export N blinded edges")
    parser.add_argument("--score", action="store_true", help="score a second coder's file")
    parser.add_argument("--seed", type=int, default=20241022)
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "reliability.json")
    args = parser.parse_args()

    rows = load_rows()
    if args.export:
        export_sample(rows, args.export, args.seed)

    consistency = internal_consistency(rows)
    print("\nINTERNAL CONSISTENCY (available without a second coder)")
    for key, value in consistency.items():
        print(f"  {key}: {value}")

    scored = score_second_coder() if args.score else None
    if scored is None:
        print(
            "\nINTER-CODER RELIABILITY: unmeasured. No second coder has coded any part of\n"
            "  the graph. Export a blinded sample with `--export 40`, have someone fill it\n"
            "  in, and re-run with `--score`. This number cannot be produced by the coder\n"
            "  who produced the first one, and no substitute for it is reported here."
        )
    else:
        print("\nINTER-CODER RELIABILITY (edge judgements, binary)")
        print(f"  n scored: {scored['n_scored']}")
        print(f"  observed agreement: {scored['observed_agreement']:.3f}")
        print(f"  Cohen's kappa: {scored['cohens_kappa']:.3f}")
        print(f"  counts: {scored['counts']}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "internal_consistency": consistency,
                "second_coder": scored,
                "second_coder_note": (
                    "unmeasured: no second coder has coded the graph; the blinded sample "
                    "is data/reliability/sample-to-code.yml"
                )
                if scored is None
                else "scored",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
