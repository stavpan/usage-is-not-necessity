#!/usr/bin/env python3
"""Expand the systematic candidate universe from 400 to tens of thousands.

The coded layer of 150 rows was selected by judgement, and 150 rows is far too few
for the selection to be harmless. The defence used here is not to code more rows --
that would multiply the judgement problem -- but to *enumerate* a large, systematic
universe of candidates from a third party, so the size of the unexplained residual
can be measured rather than asserted.

The universe is drawn from Wikidata: items carrying a time of discovery or invention
or a discoverer/inventor, with a documented Wikipedia footprint. Wikidata is
community-curated and uneven, but it is not written by this project, and every
candidate it returns is citable and auditable.

The previous pool took only items with at least 18 sitelinks, which yielded 400
candidates -- too small to bound anything. This lowers the floor and raises the cap
so the pool is three orders of magnitude larger, and reports the overlap in tiers.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
SPARQL = "https://query.wikidata.org/sparql"
UA = "world-impact/0.1 (candidate pool; mailto:panagist32@gmail.com)"

# Two deliberately cheap queries rather than one clever one. The first attempt walked
# `wdt:P31/wdt:P279*` over a class hierarchy and Wikidata returned HTTP 504: the
# traversal is unbounded and the query service will not run it at this scale. A single
# triple pattern plus a sitelinks filter is cheap, and it is the depth of the property
# that defines the universe, not the depth of the class tree.
QUERIES = {
    "discovery_or_invention_date": """
      SELECT ?item ?itemLabel ?sitelinks ?date WHERE {
        ?item wdt:P575 ?date .
        ?item wikibase:sitelinks ?sitelinks .
        FILTER(?sitelinks >= %d)
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
      } LIMIT %d
    """,
    "discoverer_or_inventor": """
      SELECT ?item ?itemLabel ?sitelinks ?date WHERE {
        ?item wdt:P61 ?person .
        ?person wdt:P569 ?date .
        ?item wikibase:sitelinks ?sitelinks .
        FILTER(?sitelinks >= %d)
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
      } LIMIT %d
    """,
}


def run_query(query: str, attempts: int = 3) -> list[dict[str, Any]]:
    """Fetch a SPARQL result as CSV.

    CSV rather than JSON because Wikidata labels contain raw control characters and
    unescaped quotes that make its JSON output invalid: two runs returned 6.6 MB and
    15 MB of results and then failed to parse both, at `strict=False` as well. The
    data was fine and the serialisation was not, so the serialisation is what changed.
    """
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            response = requests.get(
                SPARQL,
                params={"query": query},
                headers={"User-Agent": UA, "Accept": "text/csv"},
                timeout=180.0,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            last = error
            time.sleep(5.0 * (attempt + 1))
            continue
        rows = list(csv.reader(io.StringIO(response.text)))
        if not rows:
            return []
        header = rows[0]
        index = {name: position for position, name in enumerate(header)}
        out: list[dict[str, Any]] = []
        for row in rows[1:]:
            if len(row) != len(header):
                continue
            item = row[index["item"]]
            try:
                sitelinks = int(row[index["sitelinks"]])
            except (ValueError, IndexError):
                continue
            out.append(
                {
                    "qid": item.rsplit("/", 1)[-1],
                    "label": row[index["itemLabel"]] if "itemLabel" in index else None,
                    "sitelinks": sitelinks,
                    "date": (row[index["date"]] if "date" in index else "")[:10],
                }
            )
        return out
    raise last if last is not None else RuntimeError("query failed")


def fetch(min_sitelinks: int, limit: int) -> list[dict[str, Any]]:
    """Union of both property patterns, de-duplicated by QID."""
    merged: dict[str, dict[str, Any]] = {}
    for name, template in QUERIES.items():
        try:
            rows = run_query(template % (min_sitelinks, limit))
        except Exception as error:  # reported, not swallowed
            print(f"  {name}: {type(error).__name__} ({error})")
            continue
        for row in rows:
            row["kind"] = name
            merged.setdefault(row["qid"], row)
        print(f"  {name}: {len(rows)} rows, {len(merged)} unique so far")
    return list(merged.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-sitelinks", type=int, default=4)
    parser.add_argument("--limit", type=int, default=60000)
    parser.add_argument(
        "--out", type=Path, default=ROOT / "data" / "external" / "wikidata_pool_large.json"
    )
    args = parser.parse_args()

    candidates = fetch(args.min_sitelinks, args.limit)
    time.sleep(0.5)
    unique = {row["qid"]: row for row in candidates if row["label"]}
    print(f"candidates: {len(candidates)} rows, {len(unique)} unique labelled items")

    # The coded layer's own rows, name-normalised, for the overlap that is meaningful.
    import yaml

    coded = yaml.safe_load((ROOT / "data" / "results.yml").read_text(encoding="utf-8"))
    coded_dev = yaml.safe_load((ROOT / "data" / "developments.yml").read_text(encoding="utf-8"))

    def normalise(text: str) -> set[str]:
        keep = "".join(c if c.isalnum() or c == " " else " " for c in str(text).lower())
        return set(keep.split())

    coded_tokens = [normalise(row.get("name") or "") for row in coded + coded_dev]
    matched: list[dict[str, Any]] = []
    for row in unique.values():
        tokens = normalise(row["label"] or "")
        for index, candidate in enumerate(coded_tokens):
            union = tokens | candidate
            if union and len(tokens & candidate) / len(union) >= 0.5:
                matched.append({"qid": row["qid"], "pool_label": row["label"], "coded_index": index})
                break

    report = {
        "min_sitelinks": args.min_sitelinks,
        "limit": args.limit,
        "n_candidates": len(unique),
        "n_coded_rows": len(coded) + len(coded_dev),
        "n_matched_to_coded": len(matched),
        "overlap_rate": len(matched) / max(len(unique), 1),
        "matched": matched[:200],
        "largest": sorted(
            ({"qid": row["qid"], "label": row["label"], "sitelinks": row["sitelinks"]}
             for row in unique.values()),
            key=lambda row: -row["sitelinks"],
        )[:40],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"matched {len(matched)} of {len(unique)} candidates to a coded row "
          f"({report['overlap_rate']:.3%} of the pool)")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
