"""Automated discovery and annotation from OpenAlex.

This module exists because the hand-coded layer has a structural defect that care
cannot fix: it is a list of things one person remembered. Here the *candidate
set*, the *importance measure* and the *prerequisite edges* all come from a
source with its own inclusion criteria:

* **candidate set** -- the 26 top-level fields in OpenAlex's own taxonomy, so
  fields are enumerated rather than chosen;
* **importance** -- ``cited_by_count``, computed from the citation record rather
  than judged;
* **edges** -- ``referenced_works``, i.e. actual citations. A prerequisite claim
  becomes an observable event instead of an assertion.

That last point is the significant upgrade. In the hand-coded layer, "the
transistor requires band theory" was my claim. Here, "paper A cites paper B" is a
recorded fact with a coverage caveat, and the caveat is measurable: OpenAlex's
reference lists are complete for modern works and patchy for old ones, so the
graph is dense after ~1980 and sparse before. Coverage is reported with every
result rather than assumed.

Everything is cached under ``data/openalex/`` so the pipeline is reproducible
offline once fetched, and every call fails soft.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

BASE = "https://api.openalex.org"
MAILTO = "panagist32@gmail.com"
DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "data" / "openalex"
USER_AGENT = f"world-impact/0.1 (research; {MAILTO})"
WORK_SELECT = (
    "id,doi,title,publication_year,cited_by_count,referenced_works,primary_topic,authorships,type"
)


POLITE_DELAY = 0.12
"""Seconds between requests. OpenAlex's polite pool tolerates roughly ten per
second; a corpus-wide citer fetch followed immediately by a probe exceeded it and
returned HTTP 429, which crashed the probe. Both the delay and the retry below
exist because that happened."""


def _get(
    path: str,
    params: dict[str, Any],
    timeout: float = 60.0,
    retries: int = 5,
) -> dict[str, Any]:
    """GET with polite pacing and exponential backoff on rate limiting."""
    merged = {**params, "mailto": MAILTO}
    last: Exception | None = None
    for attempt in range(retries):
        try:
            response = requests.get(
                f"{BASE}{path}",
                params=merged,
                timeout=timeout,
                headers={"User-Agent": USER_AGENT},
            )
        except requests.RequestException as error:
            last = error
            time.sleep(POLITE_DELAY * (2**attempt))
            continue
        if response.status_code == 429:
            last = requests.HTTPError("429 Too Many Requests")
            time.sleep(1.5 * (2**attempt))
            continue
        response.raise_for_status()
        time.sleep(POLITE_DELAY)
        payload = response.json()
        return payload if isinstance(payload, dict) else {"results": payload}
    raise last if last is not None else requests.HTTPError("request failed")


def short_id(value: str | None) -> str:
    """``https://openalex.org/W123`` -> ``W123``."""
    return (value or "").rsplit("/", 1)[-1]


def fetch_fields(cache: Path = DEFAULT_CACHE, refresh: bool = False) -> list[dict[str, Any]]:
    """The 26 top-level fields, enumerated rather than chosen."""
    path = cache / "fields.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))
    payload = _get("/fields", {"per-page": 50})
    rows = [
        {
            "id": row["id"],
            "short": short_id(row["id"]),
            "name": row["display_name"],
            "works_count": row.get("works_count", 0),
            "cited_by_count": row.get("cited_by_count", 0),
        }
        for row in payload.get("results", [])
    ]
    cache.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return rows


def top_works(
    field_id: str,
    per_page: int = 30,
    year_from: int = 1900,
    year_to: int = 2024,
    timeout: float = 90.0,
) -> list[dict[str, Any]]:
    """The most-cited works in a field over a window. Selection is by citation."""
    payload = _get(
        "/works",
        {
            "filter": (f"primary_topic.field.id:{field_id},publication_year:{year_from}-{year_to}"),
            "sort": "cited_by_count:desc",
            "per-page": per_page,
            "select": WORK_SELECT,
        },
        timeout=timeout,
    )
    return [_slim(row) for row in payload.get("results", [])]


def _slim(row: dict[str, Any]) -> dict[str, Any]:
    topic = row.get("primary_topic") or {}
    field = topic.get("field") or {}
    subfield = topic.get("subfield") or {}
    authorships = row.get("authorships") or []
    return {
        "id": short_id(row.get("id")),
        "doi": row.get("doi"),
        "title": row.get("title") or "",
        "year": row.get("publication_year"),
        "cited_by_count": row.get("cited_by_count") or 0,
        "type": row.get("type"),
        "field_id": field.get("id"),
        "field": field.get("display_name"),
        "subfield": subfield.get("display_name"),
        "first_author": (authorships[0].get("author") or {}).get("display_name")
        if authorships
        else None,
        "referenced_works": [short_id(x) for x in (row.get("referenced_works") or [])],
    }


def build_corpus(
    per_field: int = 25,
    year_from: int = 1900,
    year_to: int = 2024,
    max_refs_per_work: int = 20,
    cache: Path = DEFAULT_CACHE,
    refresh: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """Build the automated corpus: top works per field, plus their cited works.

    The corpus is deliberately two-tier. The *seed* set is the most-cited works
    per field (selection by citation count, not by judgement). The *reference*
    set is whatever those works cite, fetched only for its field label, which is
    what makes a field-to-field citation flow computable.
    """
    path = cache / "corpus.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))

    fields = fetch_fields(cache)
    seeds: list[dict[str, Any]] = []
    for field in fields:
        try:
            works = top_works(field["id"], per_page=per_field, year_from=year_from, year_to=year_to)
        except requests.RequestException as error:
            if verbose:
                print(f"  {field['name']}: {type(error).__name__}")
            continue
        for work in works:
            work["referenced_works"] = work["referenced_works"][:max_refs_per_work]
        seeds.extend(works)
        if verbose:
            print(f"  {field['name']:<44} {len(works)} works")

    seed_ids = {work["id"] for work in seeds}
    referenced = sorted({ref for work in seeds for ref in work["referenced_works"]} - seed_ids)
    if verbose:
        print(f"  fetching metadata for {len(referenced)} referenced works")
    ref_records = works_by_ids(referenced)

    corpus = {
        "generated_by": "world_impact.openalex.build_corpus",
        "year_from": year_from,
        "year_to": year_to,
        "per_field": per_field,
        "max_refs_per_work": max_refs_per_work,
        "n_fields": len(fields),
        "n_seeds": len(seeds),
        "n_referenced": len(referenced),
        "n_referenced_resolved": len(ref_records),
        "seeds": seeds,
        "references": ref_records,
    }
    cache.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(corpus, indent=2), encoding="utf-8")
    return corpus


def fetch_citers(
    seed_ids: list[str],
    per_seed: int = 25,
    cache: Path = DEFAULT_CACHE,
    refresh: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """Who cites each seed, and how important those citers are.

    This exists because citation *count* measures usage, and usage is not
    importance. Everybody who uses an assay cites the assay; only people building
    directly on a theory cite the theory. So a count-based ranking is structurally
    biased toward instruments. The repair is to look at *who* does the citing: a
    work cited by few but extremely-cited works is foundational; a work cited by
    everyone but by ordinary papers is a service.

    Two numbers per seed, both from one request:

    ``n_citers``      unique citing works (``meta.count``), which is a different
                      quantity from ``cited_by_count`` -- the latter counts
                      citation *instances*, so a single paper citing the same work
                      twelve times inflates it.
    ``top_citers``    the 25 most-cited citing works, fetched for their own
                      citation counts and fields. That is the input to the
                      ``citer_prestige`` criterion in :mod:`world_impact.convergence`.
    """
    path = cache / "citers.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))

    # Merge into any existing cache rather than overwriting it: this function is
    # called both for the whole corpus and for ad-hoc subsets (the theory probe),
    # and an overwrite would silently destroy 520 seeds' worth of fetches.
    out: dict[str, Any] = {}
    if path.exists():
        out = json.loads(path.read_text(encoding="utf-8"))
    out = {key: value for key, value in out.items() if key not in set(seed_ids)}
    for index, work_id in enumerate(seed_ids, start=1):
        try:
            payload = _get(
                "/works",
                {
                    "filter": f"cites:{work_id}",
                    "sort": "cited_by_count:desc",
                    "per-page": per_seed,
                    "select": "id,title,publication_year,cited_by_count,primary_topic",
                },
                timeout=60.0,
            )
        except requests.RequestException:
            continue
        out[work_id] = {
            "n_citers": int((payload.get("meta") or {}).get("count") or 0),
            "top_citers": [_slim(row) for row in payload.get("results", [])],
        }
        if verbose and index % 50 == 0:
            print(f"    {index}/{len(seed_ids)} seeds")

    cache.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def field_flow(corpus: dict[str, Any]) -> dict[str, Any]:
    """Field-to-field citation flow, from actual reference records.

    ``flow[i][j]`` counts references from works in field *i* to works in field *j*.
    Rows are citing fields, columns are cited fields, so a row-sum is how much a
    field draws on the literature and a column-sum is how much it supplies. The
    ratio is the upstreamness measure in :mod:`world_impact.fields`.

    Coverage is reported because it is the honest limit of this object: OpenAlex
    reference lists are near-complete for recent work and patchy for older work,
    so a low-coverage cell means "no records", not "no influence".
    """
    references = corpus.get("references", {})
    names: list[str] = []
    index: dict[str, int] = {}
    for work in corpus.get("seeds", []):
        label = work.get("field") or "unknown"
        if label not in index:
            index[label] = len(names)
            names.append(label)
    n = len(names)
    matrix = [[0] * n for _ in range(n)]
    resolved = 0
    attempted = 0
    for work in corpus.get("seeds", []):
        citing = index.get(work.get("field") or "unknown")
        if citing is None:
            continue
        for ref in work.get("referenced_works") or []:
            attempted += 1
            record = references.get(ref)
            if not record:
                continue
            label = record.get("field") or "unknown"
            if label not in index:
                index[label] = len(names)
                names.append(label)
                for row in matrix:
                    row.append(0)
                matrix.append([0] * len(names))
            matrix[citing][index[label]] += 1
            resolved += 1
    return {
        "fields": names,
        "matrix": matrix,
        "n_references_attempted": attempted,
        "n_references_resolved": resolved,
        "reference_coverage": round(resolved / attempted, 3) if attempted else 0.0,
    }


def works_by_ids(
    ids: list[str], batch: int = 50, timeout: float = 90.0
) -> dict[str, dict[str, Any]]:
    """Fetch field metadata for many works, batched. Returns ``{id: record}``.

    Batched because a field-flow matrix needs the *field* of every cited work,
    and one request per reference would be tens of thousands of calls.
    """
    out: dict[str, dict[str, Any]] = {}
    for start in range(0, len(ids), batch):
        chunk = ids[start : start + batch]
        try:
            payload = _get(
                "/works",
                {
                    "filter": "ids.openalex:" + "|".join(chunk),
                    "per-page": batch,
                    "select": "id,title,publication_year,cited_by_count,primary_topic",
                },
                timeout=timeout,
            )
        except requests.RequestException:
            continue
        for row in payload.get("results", []):
            record = _slim(row)
            out[record["id"]] = record
        time.sleep(0.05)
    return out
