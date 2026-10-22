"""Check the bibliography against Crossref.

A bibliography compiled from memory is a liability in review. This queries
Crossref for each entry's title and reports the best match, its DOI and a
similarity score, so the unverified flags in ``data/sources.yml`` can be turned
into verified ones or into corrections.

Network-dependent by design: it is a maintenance command, never part of the
analysis pipeline, and the test suite marks it accordingly.
"""

from __future__ import annotations

import difflib
import time
from typing import Any

import requests

from world_impact.schema import Source

CROSSREF = "https://api.crossref.org/works"
USER_AGENT = "world-impact/0.1 (bibliography verification; mailto:panagist32@gmail.com)"


def lookup(source: Source, timeout: float = 20.0) -> dict[str, Any]:
    """Query Crossref for one entry. Returns the best match or an error record."""
    params: dict[str, str | int] = {
        "query.bibliographic": source.title,
        "rows": 3,
        "select": "DOI,title,author,issued,container-title,type",
    }
    try:
        response = requests.get(
            CROSSREF,
            params=params,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
        )
    except requests.RequestException as error:
        return {"key": source.key, "error": f"{type(error).__name__}: {error}"}
    if response.status_code != 200:
        return {"key": source.key, "error": f"HTTP {response.status_code}"}

    items = response.json().get("message", {}).get("items", [])
    if not items:
        return {"key": source.key, "error": "no candidates"}

    best, best_score = None, 0.0
    for item in items:
        titles = item.get("title") or [""]
        score = difflib.SequenceMatcher(None, source.title.lower(), titles[0].lower()).ratio()
        if score > best_score:
            best, best_score = item, score
    assert best is not None

    year = None
    issued = best.get("issued", {}).get("date-parts", [[None]])
    if issued and issued[0]:
        year = issued[0][0]
    return {
        "key": source.key,
        "declared_title": source.title,
        "declared_year": source.year,
        "matched_title": (best.get("title") or [""])[0],
        "matched_doi": best.get("DOI"),
        "matched_year": year,
        "similarity": round(best_score, 3),
        "year_agrees": year == source.year if year else None,
        "already_declared_doi": source.doi,
    }


def verify_entries(
    sources: list[Source], pause: float = 0.4, limit: int | None = None
) -> dict[str, Any]:
    """Verify a list of entries. ``pause`` keeps us inside Crossref's courtesy rate."""
    entries = sources[:limit] if limit else sources
    results = []
    for index, source in enumerate(entries, start=1):
        results.append(lookup(source))
        if index < len(entries):
            time.sleep(pause)
    matched = sum(1 for row in results if row.get("matched_doi"))
    agreeing = sum(1 for row in results if row.get("year_agrees") is True)
    return {
        "entries": results,
        "n_entries": len(results),
        "n_matched": matched,
        "n_year_agree": agreeing,
        "summary": (
            f"{matched}/{len(results)} entries matched a DOI; {agreeing} of those also "
            "agreed on year. Review every mismatch by hand: Crossref matching is a "
            "suggestion, not a verdict."
        ),
    }
