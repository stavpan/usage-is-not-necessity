#!/usr/bin/env python3
"""Fetch the automated corpus from OpenAlex and summarise it.

Run once with network access; everything afterwards is offline and reproducible
from data/openalex/corpus.json.
"""

from __future__ import annotations

import argparse

from world_impact import openalex


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-field", type=int, default=20)
    parser.add_argument("--year-from", type=int, default=1900)
    parser.add_argument("--year-to", type=int, default=2024)
    parser.add_argument(
        "--max-refs",
        type=int,
        default=100,
        help="references captured per seed; 20 was the cause of the two degenerate criteria",
    )
    parser.add_argument(
        "--min-ref-indegree",
        type=int,
        default=1,
        help="only resolve metadata for references cited by at least this many seeds",
    )
    parser.add_argument(
        "--max-refs-to-resolve",
        type=int,
        default=12000,
        help="cap on reference metadata fetches, taken highest-in-degree first",
    )
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    corpus = openalex.build_corpus(
        per_field=args.per_field,
        year_from=args.year_from,
        year_to=args.year_to,
        max_refs_per_work=args.max_refs,
        min_ref_indegree=args.min_ref_indegree,
        max_refs_to_resolve=args.max_refs_to_resolve,
        refresh=args.refresh,
        verbose=True,
    )
    print(
        f"\nCORPUS: {corpus['n_seeds']} seeds across {corpus['n_fields']} fields, "
        f"{corpus['n_referenced']} referenced works, "
        f"{corpus['n_referenced_resolved']} resolved"
    )

    # Citers are cached separately from the corpus and cost 520 requests, so they
    # are NOT refreshed with the corpus: rebuilding the corpus is cheap (26 seed
    # requests plus one batch per 50 references) and the citer cache is not. Passing
    # `refresh=args.refresh` here would have spent the whole daily budget re-fetching
    # data that had not changed.
    print("\nciters: reusing the cache unless it is missing...")
    citers = openalex.fetch_citers(
        [work["id"] for work in corpus["seeds"]], verbose=True, refresh=False
    )
    print(f"CITERS: resolved for {len(citers)} of {len(corpus['seeds'])} seeds")

    flow = openalex.field_flow(corpus)
    print(
        f"FLOW: {len(flow['fields'])} fields, "
        f"{flow['n_references_resolved']}/{flow['n_references_attempted']} references "
        f"resolved (coverage {flow['reference_coverage']:.3f})"
    )

    matrix = flow["matrix"]
    names = flow["fields"]
    incoming = [sum(matrix[i][j] for i in range(len(names))) for j in range(len(names))]
    outgoing = [sum(row) for row in matrix]
    totals = [(names[j], incoming[j], outgoing[j]) for j in range(len(names))]
    print("\n-- fields by how much they SUPPLY (cited by other top works) --")
    for name, inc, out in sorted(totals, key=lambda row: -row[1])[:14]:
        ratio = inc / out if out else float("inf")
        print(f"  {name[:44]:<46} cited={inc:5d} cites={out:5d} ratio={ratio:6.2f}")

    print("\n-- most-cited seeds overall --")
    for work in sorted(corpus["seeds"], key=lambda w: -w["cited_by_count"])[:20]:
        print(
            "  {:5d}  {}  {:<54} {}".format(
                work["cited_by_count"],
                work.get("year") or "?",
                (work.get("title") or "")[:54],
                (work.get("field") or "")[:26],
            )
        )


if __name__ == "__main__":
    main()
