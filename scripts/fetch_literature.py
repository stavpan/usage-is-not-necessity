#!/usr/bin/env python3
"""Build a *verified* bibliography for the paper's related-work section.

No citation enters the paper unless Crossref returned it. Titles are submitted as
queries, not as facts: whatever Crossref does not resolve to a record at or above
the similarity floor is reported as unresolved and left out. A search engine
returns *something* for any string, which is why the floor exists and why rejected
matches are printed rather than silently kept.
"""

from __future__ import annotations

import argparse
import difflib
import json
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
CROSSREF = "https://api.crossref.org/works"
USER_AGENT = "world-impact/0.1 (literature verification; mailto:panagist32@gmail.com)"

# (key, query title, approximate year, why it is cited)
ANCHORS: list[tuple[str, str, int, str]] = [
    ("aksnes2019", "Citations, Citation Indicators, and Research Quality: An Overview of Basic Concepts and Theories", 2019, "the standard review of what citation counts do and do not measure"),
    ("macroberts2010", "Problems of citation analysis: A study of uncited and seldom-cited influences", 2010, "citation analysis misses influences that are not cited"),
    ("seglen1997", "Why the impact factor of journals should not be used for evaluating research", 1997, "the foundational critique of journal-level citation measures"),
    ("merton1968", "The Matthew Effect in Science", 1968, "cumulative advantage in scientific recognition"),
    ("vanraan2004", "Sleeping beauties in science", 2004, "delayed recognition: citation trajectories are not monotone in importance"),
    ("teufel2006", "Automatic classification of citation function", 2006, "citations carry different functions, and the function is not in the edge"),
    ("cohan2019", "Structural Scaffolds for Citation Intent Classification in Scientific Publications", 2019, "citation intent classification at scale"),
    ("jurgens2018", "Measuring the Evolution of a Scientific Field through Citation Frames", 2018, "citation framing as a measure of how a work is used"),
    ("park2023", "Papers and patents are becoming less disruptive over time", 2023, "the CD index: a citation-network measure of whether work breaks with the past"),
    ("funk2017", "A Dynamic Network Measure of Technological Change", 2017, "the original disruption measure"),
    ("wu2019", "Large teams develop and small teams disrupt science and technology", 2019, "team size, disruption and the use of prior knowledge"),
    ("wang2013", "Quantifying Long-Term Scientific Impact", 2013, "citation dynamics and the limits of early prediction"),
    ("chen2007", "Finding scientific gems with Google's PageRank", 2007, "PageRank on citation networks: the direct ancestor of our citer-prestige measure"),
    ("walker2007", "Ranking scientific publications using a model of network traffic", 2007, "traffic-based ranking as an alternative to raw counts"),
    ("freeman1979", "Centrality in social networks conceptual clarification", 1979, "degree versus closeness versus betweenness: centrality is not one thing"),
    ("page1999", "The PageRank Citation Ranking: Bringing Order to the Web", 1999, "the ranking the citer-prestige criterion imitates"),
    ("fortunato2018", "Science of science", 2018, "the field this paper sits in"),
    ("jones2009", "The Burden of Knowledge and the Death of the Renaissance Man", 2009, "knowledge accumulates and the cost of reaching the frontier rises"),
    ("bloom2020", "Are Ideas Getting Harder to Find?", 2020, "the productivity of research is falling despite more inputs"),
    ("godin2006", "The Linear Model of Innovation: The Historical Construction of an Analytical Framework", 2006, "the linear model is a construction, not a finding"),
    ("mowery1979", "The Influence of Science on Technological Advance", 1979, "the direction of the science-technology relation is an empirical question"),
    ("gilardi2023", "ChatGPT outperforms crowd workers for text-annotation tasks", 2023, "LLM annotation reliability, the provenance question this paper raises about itself"),
    ("ziems2024", "Can Large Language Models Transform Computational Social Science?", 2024, "where LLM annotation is and is not reliable"),
    ("messeri2024", "Artificial intelligence and illusions of understanding in scientific research", 2024, "the risk of AI-assisted science producing illusory understanding"),
    ("vrandecic2014", "Wikidata: a free collaborative knowledgebase", 2014, "the third-party graph we attempted to source the dependency layer from"),
    ("turchin2018", "Quantitative historical analysis uncovers a single dimension of complexity that structures global variation in human social organization", 2018, "the long-run coded dataset our coarse layer was compared against"),
    ("unresolved_probe", "The Scientometrics of Citation Networks in Twenty-First Century Research", 2023, "a deliberately non-existent title, to show unresolved queries are reported not kept"),
]


def normalise(text: str) -> str:
    """Lower-case alphanumeric words only.

    Needed because Crossref titles carry typographic punctuation that a hand-typed
    query does not: `Google's` against `Google’s` scored 0.882 and was rejected by a
    0.90 floor even though the DOI was the correct paper.
    """
    keep = "".join(c if c.isalnum() or c == " " else " " for c in text.lower())
    return " ".join(keep.split())


def best_match(title: str, rows: int = 4) -> dict[str, Any]:
    """Best Crossref match for a title query, with its similarity ratio."""
    response = requests.get(
        CROSSREF,
        params={
            "query.bibliographic": title,
            "rows": rows,
            "select": "DOI,title,author,issued,container-title,volume,page,type",
        },
        timeout=30.0,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    items = response.json().get("message", {}).get("items", [])
    scored: list[tuple[float, dict[str, Any]]] = []
    for item in items:
        candidate = (item.get("title") or [""])[0]
        ratio = difflib.SequenceMatcher(None, normalise(title), normalise(candidate)).ratio()
        scored.append((ratio, item))
    if not scored:
        return {"similarity": 0.0}
    ratio, item = max(scored, key=lambda pair: pair[0])
    issued = (item.get("issued") or {}).get("date-parts") or [[None]]
    authors = item.get("author") or []
    return {
        "similarity": round(ratio, 3),
        "doi": item.get("DOI"),
        "title": (item.get("title") or [""])[0],
        "year": issued[0][0],
        "container": (item.get("container-title") or [""])[0],
        "volume": item.get("volume"),
        "page": item.get("page"),
        "type": item.get("type"),
        "authors": [
            f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") for a in authors[:6]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--floor", type=float, default=0.90, help="minimum title similarity")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "literature" / "verified.json")
    args = parser.parse_args()

    verified: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for key, title, year, why in ANCHORS:
        try:
            record = best_match(title)
        except requests.RequestException as error:
            record = {"similarity": 0.0, "error": type(error).__name__}
        record.update({"key": key, "query": title, "why": why})
        issued = record.get("year")
        # High title similarity is required. The year check is a *version* check,
        # widened to four years and skipped for preprints: `Are Ideas Getting Harder
        # to Find?` resolves to the 2017 NBER working paper whose journal version is
        # 2020, and rejecting that would discard a correct citation for a reason that
        # has nothing to do with the citation being real.
        preprint = record.get("type") in {"posted-content", "report", "other"}
        keep = record.get("similarity", 0.0) >= args.floor and bool(record.get("doi"))
        if keep and issued is not None and not preprint:
            keep = abs(int(issued) - year) <= 4
        (verified if keep else rejected).append(record)
        print(
            f"  {'OK  ' if keep else 'DROP'} {key:<16} sim={record.get('similarity', 0.0):.3f} "
            f"{(record.get('doi') or '-'):<36} {(record.get('title') or title)[:40]}"
        )
        time.sleep(0.3)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"floor": args.floor, "verified": verified, "rejected": rejected}, indent=2),
        encoding="utf-8",
    )
    print(f"\nverified {len(verified)} of {len(ANCHORS)}; {len(rejected)} rejected")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
