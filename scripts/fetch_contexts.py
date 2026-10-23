#!/usr/bin/env python3
"""The falsification test: are methods cited differently from theories?

Section 5 of the paper claims that a citation edge is untyped -- that citing a method
and building on an idea produce identical edges -- and therefore that necessity cannot
be recovered from the citation record. The related-work section names the one body of
work that could falsify that claim: citation-intent classification. If a citation's
function can be recovered, the edge is typed after all.

This fetches the evidence for that test. Semantic Scholar's Academic Graph API exposes,
for every citing paper, the **contexts** -- the actual sentences around the citation --
and, where available, an **intent** label. Contexts are what the test needs; OpenAlex
has no equivalent.

Two honest limits, stated here rather than discovered later.

  The classifier below is **lexical**, not learned: it counts method-markers ("we used",
  "implemented", "toolkit") against foundation-markers ("theory", "framework", "building
  on"). It is crude, it is auditable line by line, and it will misclassify. A learned
  classifier would be better and would also reintroduce the provenance problem this
  paper is about, so the crude one is used and its errors are reported.

  The API needs a key for any real volume. Unauthenticated access is a 1,000 req/s pool
  shared by everyone on the internet and is saturated in practice -- it returned 429 at
  1.2-second spacing. An authenticated key allows 1 request/second, so 520 works take
  about nine minutes. Request one at
  https://www.semanticscholar.org/product/api#api-key-form and put it in
  data/.secrets/s2_key or $S2_API_KEY.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://api.semanticscholar.org/graph/v1"
UA = "world-impact/0.1 (research; mailto:panagist32@gmail.com)"

METHOD_MARKERS = (
    "we used", "we use", "using the", "we applied", "we implemented", "implemented",
    "toolkit", "software", "package", "library", "algorithm", "protocol", "assay",
    "kit", "pipeline", "workflow", "we ran", "was used", "were used",
)
FOUNDATION_MARKERS = (
    "theory", "theoretical", "framework", "foundation", "seminal", "pioneering",
    "the work of", "building on", "builds on", "based on the work", "inspired",
    "concept of", "principle", "insight", "paradigm", "groundbreaking",
    "revolutionis", "revolutioniz", "laid the", "origin of the idea",
)


def api_key() -> str | None:
    key = os.environ.get("S2_API_KEY")
    if key:
        return key.strip()
    path = ROOT / "data" / ".secrets" / "s2_key"
    if path.exists():
        return path.read_text(encoding="utf-8").strip() or None
    return None


def classify(context: str) -> str:
    """`method`, `foundation`, `both` or `unclear`, by marker count."""
    text = context.lower()
    method = sum(1 for marker in METHOD_MARKERS if marker in text)
    foundation = sum(1 for marker in FOUNDATION_MARKERS if marker in text)
    if method and foundation:
        return "both"
    if method:
        return "method"
    if foundation:
        return "foundation"
    return "unclear"


def fetch_one(doi: str, limit: int, key: str | None) -> list[dict[str, Any]] | None:
    headers = {"User-Agent": UA}
    if key:
        headers["x-api-key"] = key
    try:
        response = requests.get(
            f"{BASE}/paper/DOI:{doi}/citations",
            params={"fields": "contexts,intents,title,year", "limit": limit},
            headers=headers,
            timeout=60.0,
        )
    except requests.RequestException:
        return None
    if response.status_code == 429:
        return None
    if response.status_code != 200:
        return []
    return response.json().get("data") or []


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100, help="citing papers per seed")
    parser.add_argument("--delay", type=float, default=1.15, help="seconds between requests")
    parser.add_argument("--max-seeds", type=int, default=0, help="0 = all")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "semanticscholar" / "contexts.json")
    args = parser.parse_args()

    key = api_key()
    print(f"Semantic Scholar key: {'present' if key else 'ABSENT (expect 429)'}")

    corpus = json.loads((ROOT / "data" / "openalex" / "corpus.json").read_text(encoding="utf-8"))
    seeds = corpus["seeds"]
    if args.max_seeds:
        seeds = seeds[: args.max_seeds]

    cache: dict[str, Any] = {}
    if args.out.exists():
        cache = json.loads(args.out.read_text(encoding="utf-8"))
    print(f"{len(cache)} seeds cached, {len(seeds)} requested")

    failures = 0
    for index, work in enumerate(seeds, start=1):
        work_id = work["id"]
        if work_id in cache:
            continue
        doi = (work.get("doi") or "").replace("https://doi.org/", "")
        if not doi:
            cache[work_id] = {"error": "no doi"}
            continue
        rows = fetch_one(doi, args.limit, key)
        if rows is None:
            failures += 1
            if failures >= 5:
                print(f"  stopping after {failures} consecutive failures -- no usable access")
                break
            time.sleep(args.delay * 2)
            continue
        failures = 0
        contexts: list[dict[str, Any]] = []
        for row in rows:
            for context in row.get("contexts") or []:
                contexts.append(
                    {
                        "text": context,
                        "class": classify(context),
                        "intents": row.get("intents") or [],
                        "citing_year": row.get("year"),
                    }
                )
        cache[work_id] = {
            "doi": doi,
            "title": work.get("title"),
            "n_citing": len(rows),
            "n_contexts": len(contexts),
            "contexts": contexts,
        }
        if index % 25 == 0:
            print(f"  {index}/{len(seeds)} seeds, {len(cache)} cached")
        time.sleep(args.delay)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(cache, indent=2), encoding="utf-8")

    usable = [v for v in cache.values() if v.get("contexts")]
    print(f"\ncontexts for {len(usable)} of {len(seeds)} seeds")
    if not usable:
        print("nothing to classify; the API refused every request")
        return

    # The test: do method-classified and theory-classified works differ in how their
    # citations read? A lexical classifier is crude, so the distribution is reported
    # rather than a single verdict.
    from world_impact import fields

    by_class: dict[str, dict[str, int]] = {"method": {}, "theory": {}}
    for value in usable:
        label = fields.classify_work(value.get("title") or "")
        if label not in by_class:
            continue
        for context in value["contexts"]:
            bucket = by_class[label]
            bucket[context["class"]] = bucket.get(context["class"], 0) + 1

    print("\nCITATION CONTEXT CLASS BY WORK CLASS (lexical classifier, crude)")
    for label, counts in by_class.items():
        total = sum(counts.values())
        if not total:
            print(f"  {label}: no contexts")
            continue
        share = {name: f"{count / total:.2f}" for name, count in sorted(counts.items())}
        print(f"  {label:<8} n={total:<6} {share}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
