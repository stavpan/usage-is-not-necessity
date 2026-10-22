"""External, enumerable sources, so the dataset is not a memory dump.

The threat this module addresses is not sloppiness, it is *structural*: a
hand-written list of "important results" is a list of things one person happened
to remember, so it is biased toward the famous, the Western, the 20th-century and
the well-documented, and no amount of care fixes that. The only repair is to draw
the candidate set from a source with its own inclusion criteria, then measure how
far the hand-written list departs from it.

Two sources, chosen because they are enumerable, citable and free:

``Wikidata``
    A SPARQL query over items with *time of discovery or invention* (P575),
    ranked by ``wikibase:sitelinks`` (how many Wikipedias cover the item). An
    objective candidate pool with dates and a coverage-based notability measure,
    produced by a query rather than by judgement. Its bias is different from
    mine and documented: Wikidata favours what already has a Wikipedia article.

``OpenAlex``
    The scholarly record with citation counts, used to test whether a coded
    result exists and how much a paper has been cited. OpenAlex indexes articles
    well and monographs poorly -- the inverse of Crossref's weakness, which is
    why both are used.

Everything is cached under ``data/external/`` and every call fails soft: an API
error is recorded as an error, never as a silent zero.
"""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

import requests

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php"
OPENALEX = "https://api.openalex.org/works"
USER_AGENT = "world-impact/0.1 (research; panagist32@gmail.com)"
DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "data" / "external"

CANDIDATE_QUERY = """
SELECT ?item ?itemLabel ?date ?links WHERE {
  ?item wdt:P575 ?date ;
        wikibase:sitelinks ?links .
  FILTER(YEAR(?date) >= %d && YEAR(?date) <= %d)
  FILTER(?links >= %d)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?links)
LIMIT %d
"""


def _get(url: str, params: dict[str, Any], timeout: float = 60.0) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {"data": payload}


def wikidata_candidate_pool(
    year_min: int = 1600,
    year_max: int = 2024,
    min_sitelinks: int = 18,
    limit: int = 500,
) -> dict[str, Any]:
    """Objective candidate pool: inventions and discoveries, by Wikipedia coverage.

    The query is deliberately crude. It selects on a property meaning "this has a
    date of discovery or invention" and ranks by how many language editions cover
    it. It therefore contains sport and food as well as physics -- which is a
    feature, because the point is to see what a criterion-driven list contains
    that a curated one does not.
    """
    query = CANDIDATE_QUERY % (year_min, year_max, min_sitelinks, limit)
    try:
        payload = _get(WIKIDATA_SPARQL, {"query": query, "format": "json"}, timeout=120.0)
    except requests.RequestException as error:
        return {"error": f"{type(error).__name__}: {error}", "candidates": []}
    rows = payload.get("results", {}).get("bindings", [])
    candidates = [
        {
            "qid": row["item"]["value"].rsplit("/", 1)[-1],
            "label": row.get("itemLabel", {}).get("value", ""),
            "date": row["date"]["value"][:10],
            "sitelinks": int(row["links"]["value"]),
        }
        for row in rows
    ]
    return {
        "year_min": year_min,
        "year_max": year_max,
        "min_sitelinks": min_sitelinks,
        "n_candidates": len(candidates),
        "candidates": candidates,
    }


def wikidata_label_lookup(label: str, timeout: float = 30.0) -> dict[str, Any]:
    """Find a Wikidata item by label. Returns the best hit or a miss record."""
    try:
        payload = _get(
            WIKIDATA_SEARCH,
            {
                "action": "wbsearchentities",
                "search": label,
                "language": "en",
                "format": "json",
                "limit": 5,
            },
            timeout=timeout,
        )
    except requests.RequestException as error:
        return {"found": False, "error": f"{type(error).__name__}: {error}"}
    hits = payload.get("search") or []
    if not hits:
        return {"found": False, "error": "no entity"}
    scored = [
        (
            difflib.SequenceMatcher(None, label.lower(), (hit.get("label") or "").lower()).ratio(),
            hit,
        )
        for hit in hits
    ]
    score, best = max(scored, key=lambda pair: pair[0])
    return {
        "found": score >= 0.60,
        "qid": best.get("id"),
        "matched_label": best.get("label"),
        "similarity": round(score, 3),
    }


def openalex_lookup(title: str, year: int | None = None, timeout: float = 30.0) -> dict[str, Any]:
    """Find a work in OpenAlex and report its citation count."""
    params: dict[str, Any] = {
        "search": title,
        "per-page": 3,
        "mailto": "panagist32@gmail.com",
    }
    # The year filter must be skipped for pre-modern onsets: OpenAlex rejects
    # negative years with HTTP 400, which turned every ancient row into a spurious
    # "not found" in the first run.
    if year and year > 1000:
        params["filter"] = f"publication_year:{year - 1}-{year + 2}"
    try:
        payload = _get(OPENALEX, params, timeout=timeout)
    except requests.RequestException as error:
        return {"found": False, "error": f"{type(error).__name__}: {error}"}
    results = payload.get("results") or []
    if not results:
        return {"found": False, "error": "no work"}
    scored = [
        (
            difflib.SequenceMatcher(None, title.lower(), (work.get("title") or "").lower()).ratio(),
            work,
        )
        for work in results
    ]
    score, best = max(scored, key=lambda pair: pair[0])
    return {
        "found": score >= 0.80,
        "openalex_id": best.get("id"),
        "doi": best.get("doi"),
        "matched_title": best.get("title"),
        "publication_year": best.get("publication_year"),
        "cited_by_count": best.get("cited_by_count"),
        "similarity": round(score, 3),
    }


def load_exclusions(
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """Read the exclusion register (categories plus stated reasons)."""
    import yaml

    target = path or (DEFAULT_CACHE.parent / "exclusions.yml")
    if not target.exists():
        return []
    payload = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    return list(payload.get("categories") or [])


def classify_candidate(label: str, categories: list[dict[str, Any]]) -> str:
    """Assign a pool candidate to a declared exclusion category, or 'unexplained'.

    Substring matching on the lowercased label, deliberately generous: a loose
    rule can only shrink the unexplained residual, never inflate it, so the
    residual is a conservative estimate of genuine selection bias.
    """
    lowered = (label or "").lower()
    for category in categories:
        for pattern in category.get("patterns") or []:
            if str(pattern) in lowered:
                return str(category["id"])
    return "unexplained"


def match_pool_to_dataset(
    pool: list[dict[str, Any]],
    names: list[str],
    threshold: float = 0.72,
    categories: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Three-way split of the objective pool: covered, explained, unexplained.

    The raw overlap between a curated list and a criterion-driven pool is a
    misleading statistic on its own. The pool's unit is "notable entity with a
    discovery or invention date" -- substances, places, sports, pathogens -- while
    the coded unit is "intervention with a causal path to an outcome domain".
    Measured naively, the overlap was 5/400 = 1.3%, which reads as catastrophic
    bias and is mostly a unit mismatch.

    So omissions are split. Candidates in a declared exclusion category are
    *explained*: the register states why that kind of thing is out of scope.
    Whatever remains is the **unexplained residual**, and that residual -- not the
    raw 99% -- is the selection-bias measure worth quoting.
    """
    categories = categories if categories is not None else load_exclusions()
    lowered = [name.lower() for name in names]
    covered: list[dict[str, Any]] = []
    explained: list[dict[str, Any]] = []
    unexplained: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for candidate in pool:
        label = (candidate.get("label") or "").lower()
        if not label:
            continue
        best = max(
            (difflib.SequenceMatcher(None, label, name).ratio() for name in lowered),
            default=0.0,
        )
        row = dict(candidate)
        row["best_name_similarity"] = round(best, 3)
        if best >= threshold:
            covered.append(row)
            continue
        category = classify_candidate(label, categories)
        row["exclusion_category"] = category
        counts[category] = counts.get(category, 0) + 1
        (explained if category != "unexplained" else unexplained).append(row)
    unexplained.sort(key=lambda row: -row["sitelinks"])
    explained.sort(key=lambda row: -row["sitelinks"])
    total = len(covered) + len(explained) + len(unexplained)
    return {
        "threshold": threshold,
        "n_pool": total,
        "n_covered": len(covered),
        "n_explained": len(explained),
        "n_unexplained": len(unexplained),
        "raw_coverage": round(len(covered) / total, 3) if total else 0.0,
        "scope_adjusted_coverage": round(len(covered) / (len(covered) + len(unexplained)), 3)
        if (len(covered) + len(unexplained))
        else 0.0,
        "exclusion_counts": counts,
        "top_unexplained": unexplained[:40],
        "top_explained": explained[:15],
        "reading": (
            "raw_coverage counts every pool item; scope_adjusted_coverage counts only "
            "the items that fall inside the declared scope. The gap between them is the "
            "unit mismatch, and n_unexplained is the residual selection bias."
        ),
    }
