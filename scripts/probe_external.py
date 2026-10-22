#!/usr/bin/env python3
"""Measure how far the hand-coded dataset departs from an objective pool.

Run with network access. Prints the selection-bias diagnostic: what an
enumerable, criterion-driven candidate list contains that a curated list of
"what mattered" did not think of.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from world_impact import external
from world_impact.data import load_dataset

CACHE = Path(__file__).resolve().parents[1] / "data" / "external"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--min-sitelinks", type=int, default=18)
    parser.add_argument("--openalex-sample", type=int, default=10)
    args = parser.parse_args()

    CACHE.mkdir(parents=True, exist_ok=True)
    fine = load_dataset(level="results")
    coarse = load_dataset(level="developments")

    pool = external.wikidata_candidate_pool(
        year_min=1600, year_max=2024, min_sitelinks=args.min_sitelinks, limit=args.limit
    )
    (CACHE / "wikidata_pool.json").write_text(json.dumps(pool, indent=2), encoding="utf-8")
    print("WIKIDATA POOL:", pool.get("n_candidates"), "candidates", pool.get("error", ""))

    candidates = pool.get("candidates", [])
    print("-- top 25 by Wikipedia coverage (the objective pool) --")
    for row in candidates[:25]:
        print(f"  {row['sitelinks']:4d}  {row['date'][:4]}  {row['label'][:62]}")

    matches = external.match_pool_to_dataset(candidates, list(fine.names) + list(coarse.names))
    (CACHE / "pool_coverage.json").write_text(json.dumps(matches, indent=2), encoding="utf-8")
    print("\nCOVERAGE OF THE OBJECTIVE POOL BY THE CODED LISTS")
    print(
        f"  pool {matches['n_pool']}: covered {matches['n_covered']}, "
        f"explained {matches['n_explained']}, unexplained {matches['n_unexplained']}"
    )
    print(
        f"  raw coverage {matches['raw_coverage']:.3f} | "
        f"scope-adjusted coverage {matches['scope_adjusted_coverage']:.3f}"
    )
    print(f"  exclusion counts: {matches['exclusion_counts']}")
    print("-- top 30 UNEXPLAINED by Wikipedia coverage (the residual bias) --")
    for row in matches["top_unexplained"][:30]:
        print(
            f"  {row['sitelinks']:4d}  {row['date'][:4]}  {row['label'][:58]} "
            f"(sim {row['best_name_similarity']:.2f})"
        )

    sample = [d for d in fine.developments if d.onset > 1900][: args.openalex_sample]
    print(f"\nOPENALEX existence check on {len(sample)} coded results")
    out = {}
    for development in sample:
        result = external.openalex_lookup(development.name, year=development.onset)
        out[development.id] = result
        print(
            "  {:<44} found={} cites={} sim={} {}".format(
                development.name[:44],
                result.get("found"),
                result.get("cited_by_count"),
                result.get("similarity"),
                result.get("error", ""),
            )
        )
    (CACHE / "openalex_sample.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
