#!/usr/bin/env python3
"""Classify seeds from abstracts, and test whether the paper's findings survive it.

Every method/theory result in the paper rests on a **title** classifier, which the
paper itself flags as a lower bound: a work called *On the electrodynamics of moving
bodies* contains no theory keyword, so the 33 theory works found in 520 are a floor and
the group is biased toward titles that advertise their genre.

Abstracts fix most of that. This script classifies each seed twice -- by title with the
existing classifier, and by abstract with a marker lexicon -- and reports the confusion
between them. Then it re-runs the two findings that depend on the split:

  Section 5.4  methods cited 1.31x more often and 1.75x faster than theory, but
               theory's citers are heavier
  Section 5.5  theory's citation rate decays FASTER than methods', age-matched, which
               refuted the project's own durability hypothesis

If those hold under abstract-based labels as well, the finding is about the literature
rather than about which classifier was used. If they do not, the paper has to say so.

The lexicon is transparent and crude by design. A learned classifier would score better
and would put an unverifiable component into the middle of a paper about verification.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from world_impact import fields

ROOT = Path(__file__).resolve().parents[1]

METHOD_MARKERS = (
    "we present a method", "we propose a method", "we describe a method", "we introduce a method",
    "we present an algorithm", "we propose an algorithm", "we present a tool", "we introduce a tool",
    "software", "toolkit", "open-source", "implementation", "we implemented", "benchmark",
    "protocol", "assay", "we provide a", "available at", "we develop a method",
    "we present a framework for", "package", "pipeline", "we present a new algorithm",
)
FOUNDATION_MARKERS = (
    "we prove", "theorem", "we show that", "theory of", "a theory", "we derive",
    "foundational", "law of", "principle of", "we establish", "we argue that",
    "conjecture", "we formalise", "we formalize", "equations of", "we define",
    "necessary and sufficient", "the nature of", "we investigate the origin",
    "philosophical", "conceptual framework", "we propose a theory",
)


def classify_abstract(text: str) -> str:
    """`method`, `theory`, `both` or `unclear` from an abstract."""
    lowered = text.lower()
    method = sum(1 for marker in METHOD_MARKERS if marker in lowered)
    theory = sum(1 for marker in FOUNDATION_MARKERS if marker in lowered)
    if method and theory:
        return "both"
    if method:
        return "method"
    if theory:
        return "theory"
    return "unclear"


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "abstract-classification.json")
    args = parser.parse_args()

    corpus = json.loads((ROOT / "data" / "openalex" / "corpus.json").read_text(encoding="utf-8"))
    abstracts = json.loads((ROOT / "data" / "openalex" / "abstracts.json").read_text(encoding="utf-8"))
    citers = json.loads((ROOT / "data" / "openalex" / "citers.json").read_text(encoding="utf-8"))

    from world_impact import convergence as cv

    rows = cv.criteria_table(corpus, None, citers)
    by_id = {str(row["id"]): row for row in rows}

    title_labels: dict[str, str] = {}
    abstract_labels: dict[str, str] = {}
    for work in corpus["seeds"]:
        work_id = work["id"]
        title_labels[work_id] = fields.classify_work(work.get("title") or "")
        text = abstracts.get(work_id)
        abstract_labels[work_id] = classify_abstract(text) if text else "no abstract"

    covered = [w["id"] for w in corpus["seeds"] if abstract_labels[w["id"]] != "no abstract"]
    print(f"seeds with an abstract: {len(covered)} of {len(corpus['seeds'])}")
    print("\nTITLE CLASSIFIER (all seeds)")
    print("  " + str({k: sum(1 for v in title_labels.values() if v == k) for k in
                      ("method", "theory", "unclassified")}))
    print("ABSTRACT CLASSIFIER (covered seeds)")
    print("  " + str({k: sum(1 for v in abstract_labels.values() if v == k) for k in
                      ("method", "theory", "both", "unclear", "no abstract")}))

    # How often do they agree, and in which direction does the title classifier err?
    both = [i for i in covered if title_labels[i] in {"method", "theory"}]
    agree = sum(1 for i in both if title_labels[i] == abstract_labels[i])
    print(f"\nAGREEMENT where both classifiers commit: {agree}/{len(both)} "
          f"({agree / max(len(both), 1):.1%})")
    title_theory_abstract_method = sum(
        1 for i in covered if title_labels[i] == "theory" and abstract_labels[i] == "method"
    )
    title_method_abstract_theory = sum(
        1 for i in covered if title_labels[i] == "method" and abstract_labels[i] == "theory"
    )
    print(f"  title says theory, abstract says method: {title_theory_abstract_method}")
    print(f"  title says method, abstract says theory: {title_method_abstract_theory}")

    # Does the Section 5.4/5.5 gap survive the better classifier?
    print("\nTHE GAP UNDER EACH CLASSIFIER")
    for name, labels, keep in (
        ("title", title_labels, {"method", "theory"}),
        ("abstract", abstract_labels, {"method", "theory"}),
    ):
        groups: dict[str, list[dict]] = {"method": [], "theory": []}
        for work_id, label in labels.items():
            if label in keep and work_id in by_id:
                groups[label].append(by_id[work_id])
        if not groups["method"] or not groups["theory"]:
            print(f"  {name}: not enough in one group")
            continue
        m, t = groups["method"], groups["theory"]
        print(
            f"  {name:<9} method n={len(m):<4} theory n={len(t):<4} "
            f"cit ratio {median([r['citations'] for r in m]) / max(median([r['citations'] for r in t]), 1):.2f}  "
            f"momentum method {median([r['momentum'] for r in m]):.2f} vs "
            f"theory {median([r['momentum'] for r in t]):.2f}"
        )
        band_m = [r["momentum"] for r in m if 20 <= r["age"] <= 34]
        band_t = [r["momentum"] for r in t if 20 <= r["age"] <= 34]
        if band_m and band_t:
            print(
                f"  {'':<9} age 20-34: momentum method {median(band_m):.2f} "
                f"vs theory {median(band_t):.2f}  -> "
                + ("theory decays faster (refutation holds)" if median(band_t) < median(band_m)
                   else "theory decays SLOWER (refutation does NOT hold)")
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "n_seeds": len(corpus["seeds"]),
                "n_with_abstract": len(covered),
                "title_counts": {k: sum(1 for v in title_labels.values() if v == k)
                                 for k in ("method", "theory", "unclassified")},
                "abstract_counts": {k: sum(1 for v in abstract_labels.values() if v == k)
                                    for k in ("method", "theory", "both", "unclear", "no abstract")},
                "agreement": agree / max(len(both), 1),
                "title_theory_abstract_method": title_theory_abstract_method,
                "title_method_abstract_theory": title_method_abstract_theory,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
