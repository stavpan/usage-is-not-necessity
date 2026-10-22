"""Is the coarse row a legitimate unit of analysis?

The coarse layer says "electromagnetism mattered". True, and uninformative.
Worse, it may be *wrong as a unit*: if a coarse row's children have divergent
outcome profiles, then aggregating over them produces a row that describes none
of them.

Three diagnostics, all computed from the two matrices:

``coherence``
    Does the parent's coded effect vector agree with the per-outcome maximum over
    its children? A parent should carry at least the largest single contribution
    its children make, so disagreement means the two resolutions contradict each
    other and one is miscoded.

``dispersion``
    Mean pairwise cosine distance among a parent's children. High dispersion
    means the coarse row is a bag, not a thing, and every coarse-level statement
    about it is an average over disagreement.

``resolution comparison``
    Does the coarse ranking survive disaggregation? Reported as top-k overlap and
    a rank correlation, so "the coarse level is sufficient" becomes testable
    rather than assumed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from world_impact.data import Dataset


def parent_indices(fine: Dataset, coarse: Dataset) -> np.ndarray:
    """For each fine row, the index of its coarse parent in ``coarse``."""
    lookup = {name: position for position, name in enumerate(coarse.ids)}
    out = np.full(fine.n_developments, -1, dtype=int)
    for i, development in enumerate(fine.developments):
        if development.parent is None:
            continue
        out[i] = lookup[development.parent]
    return out


def children_of(parents: np.ndarray, parent_index: int) -> np.ndarray:
    """Indices of the fine rows belonging to one coarse parent."""
    return np.flatnonzero(parents == parent_index)


@dataclass
class GranularityResult:
    """The three diagnostics, plus the counts needed to read them."""

    coherence: list[dict[str, Any]]
    dispersion: list[dict[str, Any]]
    ranking: dict[str, Any]
    n_coarse_with_children: int
    n_fine_without_parent: int

    def worst_dispersion(self, k: int = 8) -> list[dict[str, Any]]:
        return sorted(self.dispersion, key=lambda row: -row["dispersion"])[:k]

    def worst_coherence(self, k: int = 8) -> list[dict[str, Any]]:
        return sorted(self.coherence, key=lambda row: -row["max_abs_gap"])[:k]


def coherence(
    fine: Dataset, coarse: Dataset, parents: np.ndarray, tolerance: int = 0
) -> list[dict[str, Any]]:
    """Parent effect vector vs the per-outcome maximum over its children."""
    fine_matrix = fine.matrix()
    coarse_matrix = coarse.matrix()
    rows: list[dict[str, Any]] = []
    for parent_index in range(coarse.n_developments):
        children = children_of(parents, parent_index)
        if children.size == 0:
            continue
        aggregate = fine_matrix[children].max(axis=0)
        declared = coarse_matrix[parent_index]
        gaps = aggregate - declared
        mismatches: list[dict[str, Any]] = [
            {
                "outcome": fine.outcome_ids[j],
                "parent": float(declared[j]),
                "children_max": float(aggregate[j]),
                "gap": float(gaps[j]),
            }
            for j in range(fine.n_outcomes)
            if abs(gaps[j]) > tolerance
        ]
        rows.append(
            {
                "parent": coarse.names[parent_index],
                "parent_id": coarse.ids[parent_index],
                "n_children": int(children.size),
                "n_mismatched_outcomes": len(mismatches),
                "max_abs_gap": float(np.abs(gaps).max()),
                "mismatches": sorted(mismatches, key=lambda row: -abs(float(row["gap"])))[:6],
            }
        )
    return rows


def dispersion(fine: Dataset, coarse: Dataset, parents: np.ndarray) -> list[dict[str, Any]]:
    """Mean pairwise cosine distance among each parent's children."""
    matrix = fine.matrix()
    norms = np.linalg.norm(matrix, axis=1)
    safe = np.where(norms == 0, 1.0, norms)
    similarity = (matrix @ matrix.T) / np.outer(safe, safe)
    rows: list[dict[str, Any]] = []
    for parent_index in range(coarse.n_developments):
        children = children_of(parents, parent_index)
        if children.size < 2:
            continue
        block = similarity[np.ix_(children, children)]
        upper = block[np.triu_indices(children.size, k=1)]
        rows.append(
            {
                "parent": coarse.names[parent_index],
                "parent_id": coarse.ids[parent_index],
                "n_children": int(children.size),
                "mean_cosine": float(upper.mean()),
                "dispersion": float(1.0 - upper.mean()),
                "min_cosine": float(upper.min()),
            }
        )
    return rows


def resolution_comparison(
    fine: Dataset, coarse: Dataset, parents: np.ndarray, top_k: int = 10
) -> dict[str, Any]:
    """Does the coarse ranking survive disaggregation?

    Computed from the plain impact totals, not from SMAA: the point is to compare
    resolutions, and running the full uncertainty machinery twice would double
    the pipeline cost for a diagnostic. The caveat travels in the output.
    """
    fine_totals = fine.matrix().sum(axis=1)
    coarse_totals = coarse.matrix().sum(axis=1)

    coarse_top = set(np.argsort(-coarse_totals)[:top_k].tolist())
    fine_top = set(np.argsort(-fine_totals)[:top_k].tolist())
    fine_top_parents = {int(parents[i]) for i in fine_top if parents[i] >= 0}
    overlap = len(coarse_top & fine_top_parents) / max(len(coarse_top), 1)

    best_child = np.full(coarse.n_developments, -1, dtype=int)
    for parent_index in range(coarse.n_developments):
        children = children_of(parents, parent_index)
        if children.size:
            best_child[parent_index] = int(children[int(np.argmax(fine_totals[children]))])

    valid = best_child >= 0
    order_coarse = np.argsort(np.argsort(-coarse_totals))
    order_fine = np.argsort(np.argsort(-fine_totals[best_child[valid]]))
    correlation = (
        float(np.corrcoef(order_coarse[valid], order_fine)[0, 1]) if valid.sum() > 2 else 0.0
    )

    return {
        "top_k": top_k,
        "coarse_top_k": [coarse.names[i] for i in sorted(coarse_top)],
        "fine_top_k": [fine.names[i] for i in sorted(fine_top)],
        "top_k_overlap": float(overlap),
        "rank_correlation_coarse_vs_best_child": correlation,
        "caveat": (
            "from impact totals only, not from SMAA; a diagnostic on resolution "
            "rather than a ranking result"
        ),
    }


def analyse_granularity(fine: Dataset, coarse: Dataset, top_k: int = 10) -> GranularityResult:
    """All three diagnostics."""
    parents = parent_indices(fine, coarse)
    return GranularityResult(
        coherence=coherence(fine, coarse, parents),
        dispersion=dispersion(fine, coarse, parents),
        ranking=resolution_comparison(fine, coarse, parents, top_k=top_k),
        n_coarse_with_children=int(
            sum(1 for p in range(coarse.n_developments) if children_of(parents, p).size)
        ),
        n_fine_without_parent=int((parents < 0).sum()),
    )
