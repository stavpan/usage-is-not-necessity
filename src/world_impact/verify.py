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

    # ``best_score`` starts below any possible ratio: at 0.0 the first item can
    # fail the strict ``>`` test (empty titles score 0.0), leaving ``best`` None
    # and tripping the old assertion. Found by running the command, not by
    # reading it -- which is the argument for running things.
    best, best_score = items[0], -1.0
    for item in items:
        titles = item.get("title") or [""]
        score = difflib.SequenceMatcher(None, source.title.lower(), titles[0].lower()).ratio()
        if score > best_score:
            best, best_score = item, score

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
        row = lookup(source)
        row["tier"] = classify(row)
        results.append(row)
        if index < len(entries):
            time.sleep(pause)

    counts: dict[str, int] = {}
    for row in results:
        counts[row["tier"]] = counts.get(row["tier"], 0) + 1
    return {
        "entries": results,
        "n_entries": len(results),
        "counts_by_tier": counts,
        "summary": (
            f"{counts.get('verified', 0)} verified, "
            f"{counts.get('plausible', 0)} plausible, "
            f"{counts.get('weak', 0)} weak, "
            f"{counts.get('unmatched', 0)} unmatched, out of {len(results)}. "
            "A DOI hit is NOT verification: Crossref returns its best guess for any "
            "query, so the tier is gated on title similarity and year agreement. An "
            "earlier version of this module reported 'matched a DOI' without gating "
            "and claimed 4/4 for entries whose similarity scores were 0.2-1.0 and "
            "only one of which agreed on year."
        ),
    }


def classify(row: dict[str, object]) -> str:
    """Grade a Crossref hit. Never call a weak hit a match.

    The tiers exist because the failure mode of a bibliography checker is
    over-confidence, not under-confidence: it always returns *something*, so a
    naive count of "matched" rises toward 100% regardless of correctness.
    """
    if row.get("error") or not row.get("matched_doi"):
        return "unmatched"
    raw = row.get("similarity")
    similarity = float(raw) if isinstance(raw, (int, float)) else 0.0
    year_agrees = row.get("year_agrees") is True
    if similarity >= 0.90 and year_agrees:
        return "verified"
    if similarity >= 0.75 and year_agrees:
        return "verified"
    if similarity >= 0.70 or (similarity >= 0.55 and year_agrees):
        return "plausible"
    if similarity >= 0.40:
        return "weak"
    return "unmatched"
