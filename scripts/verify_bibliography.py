#!/usr/bin/env python3
"""Grade the bibliography against Crossref, and never call a weak hit a match.

The failure mode of a bibliography checker is over-confidence: Crossref returns its
best guess for any query, so an ungated count of "matched" rises toward 100% however
wrong it is. An earlier version of this check reported "119/119 entries matched to a
DOI" for exactly that reason. Hits are therefore graded into four tiers, gated on
title similarity **and** year agreement, and the yield is reported as a distribution.

    verified    similarity >= 0.75 and the year agrees
    plausible   similarity >= 0.70, or >= 0.55 with year agreement
    weak        similarity >= 0.40
    unmatched   below that, or no DOI returned

The result is a paper claim: 27 verified, 59 plausible, 21 weak, 12 unmatched out of
119. Crossref indexes journal articles, so a book query tends to return the book's
front matter -- `arrow1951` matched "INDEX", `morris2013` matched "Contents".
"""

from __future__ import annotations

import argparse
import difflib
import json
import time
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
CROSSREF = "https://api.crossref.org/works"
UA = "world-impact/0.1 (bibliography verification; mailto:panagist32@gmail.com)"


def classify(similarity: float, year_agrees: bool, has_doi: bool) -> str:
    if not has_doi:
        return "unmatched"
    if similarity >= 0.90 and year_agrees:
        return "verified"
    if similarity >= 0.75 and year_agrees:
        return "verified"
    if similarity >= 0.70 or (similarity >= 0.55 and year_agrees):
        return "plausible"
    if similarity >= 0.40:
        return "weak"
    return "unmatched"


def lookup(entry: dict[str, Any]) -> dict[str, Any]:
    title = str(entry.get("title") or "")
    try:
        # `rows=3` and lowercased-raw similarity, matching the implementation whose
        # output the paper quotes. Changing either changes the tier distribution --
        # a first rewrite of this function used rows=4 and reported 47 verified
        # instead of 27 -- and a paper claim must not move because a checker was
        # refactored.
        response = requests.get(
            CROSSREF,
            params={
                "query.bibliographic": title,
                "rows": 3,
                "select": "DOI,title,author,issued,container-title,type",
            },
            timeout=30.0,
            headers={"User-Agent": UA},
        )
        response.raise_for_status()
    except requests.RequestException as error:
        return {"key": entry.get("key"), "error": type(error).__name__}

    items = response.json().get("message", {}).get("items", [])
    best, best_score = None, -1.0
    for item in items:
        candidate = (item.get("title") or [""])[0]
        score = difflib.SequenceMatcher(None, title.lower(), candidate.lower()).ratio()
        if score > best_score:
            best, best_score = item, score
    if best is None:
        return {"key": entry.get("key"), "error": "no match"}

    issued = (best.get("issued") or {}).get("date-parts") or [[None]]
    matched_year = issued[0][0]
    declared_year = entry.get("year")
    year_agrees = (
        matched_year is not None
        and declared_year is not None
        and abs(int(matched_year) - int(declared_year)) <= 2
    )
    return {
        "key": entry.get("key"),
        "declared_title": title,
        "matched_title": (best.get("title") or [""])[0],
        "matched_doi": best.get("DOI"),
        "similarity": round(best_score, 3),
        "year_agrees": year_agrees,
        "tier": classify(best_score, year_agrees, bool(best.get("DOI"))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=ROOT / "data" / "sources.yml")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "bibliography-verification.json")
    args = parser.parse_args()

    entries = yaml.safe_load(args.sources.read_text(encoding="utf-8"))
    print(f"bibliography: {len(entries)} entries")

    results = []
    for entry in entries:
        results.append(lookup(entry))
        time.sleep(0.25)

    counts: dict[str, int] = {}
    for row in results:
        counts[row.get("tier", "unmatched")] = counts.get(row.get("tier", "unmatched"), 0) + 1

    order = ("verified", "plausible", "weak", "unmatched")
    total = max(len(results), 1)
    for tier in order:
        print(f"  {tier:<10} {counts.get(tier, 0):>4}  ({counts.get(tier, 0) / total:.0%})")
    print(
        "\nA DOI hit is not verification: Crossref returns its best guess for any query. "
        "The tier is gated on title similarity and year agreement."
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "n_entries": len(results),
                "counts_by_tier": counts,
                "summary": (
                    f"{counts.get('verified', 0)} verified, {counts.get('plausible', 0)} plausible, "
                    f"{counts.get('weak', 0)} weak, {counts.get('unmatched', 0)} unmatched, "
                    f"out of {len(results)}"
                ),
                "entries": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
