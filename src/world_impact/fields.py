"""Field-level and cross-field analysis of the automated corpus.

Three questions, all answerable from the OpenAlex corpus without judgement from me:

``upstreamness``
    Which fields *supply* the literature that other fields' top work rests on?
    From actual reference records: the ratio of incoming to outgoing citation
    flow in the field-to-field matrix.

``method share``
    Of each field's most-cited works, what fraction is methodological
    infrastructure -- an assay, a protocol, a statistical procedure, a software
    package, a computational scheme -- rather than a theoretical claim? The
    classifier is keyword-based and therefore crude. The rules are declared and
    the unclassified residual is reported rather than folded into either class:
    being able to read the rule matters more than accuracy for a claim this
    central.

``cross-disciplinary hubs``
    Which individual works are cited by the most top-cited papers *across the
    most different fields*? A work cited by twenty top papers inside one field is
    that field's infrastructure; a work cited by twenty top papers across eight
    fields is infrastructure for the enterprise.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

METHOD_PATTERNS = (
    "method",
    "protocol",
    "assay",
    "reagent",
    "measurement",
    "quantitation",
    "quantification",
    "determination of",
    "analysis of",
    "statistic",
    "regression",
    "estimation",
    "inference",
    "algorithm",
    "software",
    "package",
    "language and environment",
    "toolkit",
    "framework for",
    "guideline",
    "checklist",
    "statement:",
    "criteria",
    "index",
    "scale",
    "questionnaire",
    "approximation made simple",
    "scheme",
    "implementation",
    "simulation",
    "solver",
    "toolbox",
    "database",
    "atlas",
    "benchmark",
    "dataset",
    "cloning",
    "sequencing",
    "polymerase",
    "electrophoresis",
    "chromatography",
    "spectrometry",
    "spectroscopy",
    "microscopy",
    "staining",
    "buffer",
    "calibration",
    "standardization",
    "validation",
    "reliability",
    "fit indexes",
    "structural equation",
    "meta-analysis",
    "systematic review",
)
THEORY_PATTERNS = (
    "theory",
    "theorem",
    "model of",
    "hypothesis",
    "law of",
    "principle",
    "mechanism",
    "origin of",
    "nature of",
    "structure of",
    "evolution of",
    "relativity",
    "field equations",
    "mechanism of action",
    "pathogenesis",
    "epidemiology of",
    "causes of",
)


@dataclass
class FieldProfile:
    name: str
    incoming: int
    outgoing: int
    ratio: float
    n_seeds: int
    method_share: float
    median_citations: float


def upstreamness(flow: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Per-field incoming/outgoing citation flow and their ratio.

    A ratio above 1 means the field is a net supplier: other fields' top work
    cites it more than it cites them.
    """
    names = flow["fields"]
    matrix = flow["matrix"]
    n = len(names)
    out: dict[str, dict[str, float]] = {}
    for j, name in enumerate(names):
        incoming = sum(matrix[i][j] for i in range(n))
        outgoing = sum(matrix[j])
        out[name] = {
            "incoming": float(incoming),
            "outgoing": float(outgoing),
            "ratio": float(incoming / outgoing) if outgoing else float("inf"),
            "net": float(incoming - outgoing),
        }
    return out


def size_normalised_upstreamness(
    flow: dict[str, Any], field_sizes: dict[str, int]
) -> dict[str, dict[str, float]]:
    """Upstreamness per *work published*, not per field.

    Necessary and easy to forget: raw citation flow makes a large field look like
    a large supplier mechanically, because it has more work to be cited.
    Normalising by each field's total works_count answers the different and more
    interesting question: how much does one paper's worth of this field get drawn
    on by the rest?
    """
    raw = upstreamness(flow)
    out: dict[str, dict[str, float]] = {}
    for name, stats in raw.items():
        size = field_sizes.get(name)
        if not size:
            continue
        out[name] = {
            "works_count": float(size),
            "incoming_per_10k_works": float(stats["incoming"]) / (size / 10_000),
            "outgoing_per_10k_works": float(stats["outgoing"]) / (size / 10_000),
            "ratio": float(stats["ratio"]),
            "net": float(stats["net"]),
        }
    return out


def suspect_outliers(corpus: dict[str, Any], factor: float = 8.0) -> list[dict[str, Any]]:
    """Flag seed works whose citation count is implausible for their field.

    Found the hard way: the single most-cited item in the first corpus was a 2020
    paper on a radiation-resistant camera with 801,217 citations, which is a
    mis-merged OpenAlex record rather than a famous paper. Reporting a ranking
    that a data error sits on top of would be worse than reporting nothing, so
    outliers are surfaced rather than silently used.
    """
    per_field: dict[str, list[int]] = {}
    for work in corpus.get("seeds", []):
        per_field.setdefault(work.get("field") or "unknown", []).append(
            work.get("cited_by_count") or 0
        )
    medians = {
        name: sorted(values)[len(values) // 2] if values else 0
        for name, values in per_field.items()
    }
    flagged = []
    for work in corpus.get("seeds", []):
        field = work.get("field") or "unknown"
        median = medians.get(field, 0)
        if median and (work.get("cited_by_count") or 0) > factor * median:
            flagged.append(
                {
                    "id": work.get("id"),
                    "title": work.get("title"),
                    "year": work.get("year"),
                    "field": field,
                    "cited_by_count": work.get("cited_by_count"),
                    "field_median": median,
                    "multiple_of_median": round((work.get("cited_by_count") or 0) / median, 1),
                }
            )
    flagged.sort(key=lambda row: -row["multiple_of_median"])
    return flagged


def classify_work(title: str) -> str:
    """``"method"``, ``"theory"`` or ``"unclassified"``, from the title alone."""
    lowered = (title or "").lower()
    method_hits = sum(1 for pattern in METHOD_PATTERNS if pattern in lowered)
    theory_hits = sum(1 for pattern in THEORY_PATTERNS if pattern in lowered)
    if method_hits > theory_hits:
        return "method"
    if theory_hits > method_hits:
        return "theory"
    if method_hits:
        return "method"
    return "unclassified"


def method_share(corpus: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Per field, the share of top-cited works classified as method."""
    per_field: dict[str, list[dict[str, Any]]] = {}
    for work in corpus.get("seeds", []):
        per_field.setdefault(work.get("field") or "unknown", []).append(work)
    out: dict[str, dict[str, Any]] = {}
    for name, works in per_field.items():
        labels = [classify_work(work.get("title") or "") for work in works]
        citations = sorted((work.get("cited_by_count") or 0) for work in works)
        n = len(labels) or 1
        out[name] = {
            "n": len(labels),
            "method": labels.count("method"),
            "theory": labels.count("theory"),
            "unclassified": labels.count("unclassified"),
            "method_share": round(labels.count("method") / n, 3),
            "median_citations": float(citations[len(citations) // 2]) if citations else 0.0,
        }
    return out


def cross_field_hubs(corpus: dict[str, Any], top: int = 40) -> list[dict[str, Any]]:
    """Works cited by the most top-cited papers across the most fields.

    The load-bearing measure for the automated layer: a work cited by twenty top
    papers inside one field is that field's infrastructure; a work cited by
    twenty top papers across eight fields is infrastructure for the enterprise.
    The second column is the interesting one.
    """
    references = corpus.get("references", {})
    counts: dict[str, dict[str, Any]] = {}
    for work in corpus.get("seeds", []):
        citing_field = work.get("field") or "unknown"
        for ref in work.get("referenced_works") or []:
            record = references.get(ref)
            if not record:
                continue
            entry = counts.setdefault(
                ref,
                {
                    "id": ref,
                    "title": record.get("title") or "",
                    "year": record.get("year"),
                    "field": record.get("field"),
                    "cited_by_count": record.get("cited_by_count") or 0,
                    "cited_by_n_seeds": 0,
                    "citing_fields": set(),
                },
            )
            entry["cited_by_n_seeds"] += 1
            entry["citing_fields"].add(citing_field)
    rows = []
    for entry in counts.values():
        fields = sorted(entry.pop("citing_fields"))
        entry["n_citing_fields"] = len(fields)
        entry["citing_fields"] = fields
        entry["classification"] = classify_work(entry["title"])
        rows.append(entry)
    rows.sort(key=lambda row: (-row["n_citing_fields"], -row["cited_by_n_seeds"]))
    return rows[:top]


def summarise(corpus: dict[str, Any]) -> dict[str, Any]:
    """The headline numbers of the automated layer, computed not asserted."""
    from world_impact import openalex

    flow = openalex.field_flow(corpus)
    up = upstreamness(flow)
    shares = method_share(corpus)
    hubs = cross_field_hubs(corpus, top=25)
    seeds = corpus.get("seeds", [])
    labels = [classify_work(work.get("title") or "") for work in seeds]
    n = len(labels) or 1
    ranked = sorted(up.items(), key=lambda pair: -pair[1]["ratio"])
    return {
        "n_seeds": len(seeds),
        "n_fields": len({work.get("field") for work in seeds}),
        "reference_coverage": flow.get("reference_coverage", 0.0),
        "overall_method_share": round(labels.count("method") / n, 3),
        "overall_theory_share": round(labels.count("theory") / n, 3),
        "overall_unclassified_share": round(labels.count("unclassified") / n, 3),
        "top_suppliers": [{"field": name, **stats} for name, stats in ranked[:8]],
        "top_consumers": [{"field": name, **stats} for name, stats in ranked[::-1][:8]],
        "most_method_heavy": sorted(
            ({"field": name, **stats} for name, stats in shares.items() if stats["n"] >= 10),
            key=lambda row: -row["method_share"],
        )[:8],
        "hubs": hubs,
    }
