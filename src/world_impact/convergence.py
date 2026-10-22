"""What are the most important things? Whatever several independent criteria agree on.

Any single importance measure is a choice, and a choice is what this project has
been trying to avoid. But different measures fail in different ways, so agreement
between measures that share no machinery is evidence in a way that no single
ranking can be. Importance is therefore defined here as **robustness across
criteria**:

* a work's *worst rank* across all criteria is its pessimist rank. A work every
  criterion places high is important in a sense no single criterion can
  manufacture.
* the *number of criteria* that place a work in the top 50 is its support.
  Support 5 of 5 is a different object from support 1 of 5 at rank 1.

The criteria, computed from the corpus rather than judged:

===============  ==========================================================
``citations``    total citations -- the standard measure, and an age artifact
``rate``         citations per year since publication -- the age correction
``top_citations``how many of the other most-cited works cite it
``reach``        how many distinct fields cite it
``upstream``     the upstreamness of its own field
===============  ==========================================================

``rate`` exists because the raw ranking is confounded by age: a protocol published
in 1970 has had fifty years to accumulate citations. Reporting both, and the rank
correlation between them, makes that confound visible instead of arguable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

CRITERIA = ("citations", "rate", "top_citations", "reach", "upstream")
CRITERION_LABEL = {
    "citations": "total citations",
    "rate": "citations per year",
    "top_citations": "cited by other top works",
    "reach": "distinct citing fields",
    "upstream": "upstreamness of its field",
}


def criteria_table(
    corpus: dict[str, Any],
    upstreamness: dict[str, dict[str, float]] | None = None,
    reference_year: int = 2024,
) -> list[dict[str, Any]]:
    """One row per seed work, with every criterion as a raw value."""
    upstreamness = upstreamness or {}
    referenced_by: dict[str, int] = {}
    citing_fields: dict[str, set[str]] = {}
    for work in corpus.get("seeds", []):
        field = work.get("field") or "unknown"
        for ref in work.get("referenced_works") or []:
            referenced_by[ref] = referenced_by.get(ref, 0) + 1
            citing_fields.setdefault(ref, set()).add(field)

    rows: list[dict[str, Any]] = []
    for work in corpus.get("seeds", []):
        year = work.get("year") or reference_year
        age = max(reference_year - year + 1, 1)
        citations = float(work.get("cited_by_count") or 0)
        field = work.get("field") or "unknown"
        rows.append(
            {
                "id": work.get("id"),
                "title": work.get("title") or "",
                "year": year,
                "field": field,
                "citations": citations,
                "age": age,
                "rate": citations / age,
                "top_citations": float(referenced_by.get(work.get("id"), 0)),
                "reach": float(len(citing_fields.get(work.get("id"), set()))),
                "upstream": float(upstreamness.get(field, {}).get("ratio", 1.0)),
            }
        )
    return rows


def ranks(rows: list[dict[str, Any]], criterion: str) -> dict[str, int]:
    """1-based ranks, ties broken deterministically by id."""
    order = sorted(rows, key=lambda row: (-row[criterion], str(row["id"])))
    return {str(row["id"]): position + 1 for position, row in enumerate(order)}


@dataclass
class ConvergenceResult:
    rows: list[dict[str, Any]]
    rank_table: dict[str, dict[str, int]]
    agreement: dict[tuple[str, str], float]
    n: int
    active: tuple[str, ...] = CRITERIA
    """Criteria that actually vary across the corpus.

    A criterion with one distinct value ranks by tie-break alone, which silently
    *inflates* every work's support -- found by a test that passed no field-flow
    data, so ``upstream`` was constant and two works appeared to be in the top 50
    of all five criteria instead of one. Constant criteria are dropped and named
    rather than left in to flatter the result.
    """

    def support(self, work_id: str, cutoff: int = 50) -> int:
        return sum(1 for criterion in self.active if self.rank_table[criterion][work_id] <= cutoff)

    def consensus(self, top: int = 30, cutoff: int = 50) -> list[dict[str, Any]]:
        """Works ranked by how many criteria agree, then by pessimist rank."""
        scored = []
        for row in self.rows:
            work_id = str(row["id"])
            support = self.support(work_id, cutoff)
            worst = max(self.rank_table[c][work_id] for c in self.active)
            mean = float(np.mean([self.rank_table[c][work_id] for c in self.active]))
            scored.append(
                {
                    **{k: row[k] for k in ("id", "title", "year", "field", "citations")},
                    "rate": round(row["rate"], 1),
                    "support": support,
                    "worst_rank": worst,
                    "mean_rank": round(mean, 1),
                    "ranks": {c: self.rank_table[c][work_id] for c in self.active},
                }
            )
        scored.sort(key=lambda row: (-row["support"], row["mean_rank"], row["worst_rank"]))
        return scored[:top]

    def movers(self, top: int = 15) -> list[dict[str, Any]]:
        """Biggest disagreement between raw citations and age-corrected rate.

        Positive shift means the work looks far better once age is corrected: it
        is being used intensively now, and its raw rank understates it.
        """
        out = []
        for row in self.rows:
            work_id = str(row["id"])
            raw = self.rank_table["citations"][work_id]
            corrected = self.rank_table["rate"][work_id]
            out.append(
                {
                    "title": row["title"],
                    "year": row["year"],
                    "field": row["field"],
                    "citations": row["citations"],
                    "rate": round(row["rate"], 1),
                    "raw_rank": raw,
                    "rate_rank": corrected,
                    "shift": raw - corrected,
                }
            )
        out.sort(key=lambda row: -row["shift"])
        return out[:top]

    def pareto(self) -> list[str]:
        """Works not dominated on any criterion. Needs no aggregation at all."""
        stack = np.array([[row[c] for c in CRITERIA] for row in self.rows], dtype=float)
        keep = []
        for i in range(stack.shape[0]):
            dominated = (stack >= stack[i]).all(axis=1) & (stack > stack[i]).any(axis=1)
            if not dominated.any():
                keep.append(str(self.rows[i]["id"]))
        return keep


def convergence(
    corpus: dict[str, Any],
    upstreamness: dict[str, dict[str, float]] | None = None,
    reference_year: int = 2024,
) -> ConvergenceResult:
    """Build the criteria table, the ranks, and the criterion-agreement matrix."""
    rows = criteria_table(corpus, upstreamness, reference_year)
    # Drop criteria that do not vary: a constant column ranks by tie-break alone
    # and would inflate every work's support.
    active = tuple(
        criterion for criterion in CRITERIA if len({round(row[criterion], 9) for row in rows}) > 1
    )
    rank_table = {criterion: ranks(rows, criterion) for criterion in active}
    agreement: dict[tuple[str, str], float] = {}
    for a in active:
        for b in active:
            left = np.array([rank_table[a][str(row["id"])] for row in rows], dtype=float)
            right = np.array([rank_table[b][str(row["id"])] for row in rows], dtype=float)
            agreement[(a, b)] = float(np.corrcoef(left, right)[0, 1])
    return ConvergenceResult(
        rows=rows,
        rank_table=rank_table,
        agreement=agreement,
        n=len(rows),
        active=active,
    )


def decade_trend(rows: list[dict[str, Any]], reference_year: int = 2024) -> list[dict[str, Any]]:
    """Median citations per year by publication decade.

    A crude measure of how intensively scientific attention is now applied to
    recent work, and the reason the age correction changes the ranking so much.
    """
    buckets: dict[int, list[float]] = {}
    for row in rows:
        decade = (row["year"] // 10) * 10
        buckets.setdefault(decade, []).append(row["rate"])
    out = []
    for decade, values in sorted(buckets.items()):
        if len(values) < 5:
            continue
        ordered = sorted(values)
        out.append(
            {
                "decade": decade,
                "n": len(values),
                "median_rate": ordered[len(ordered) // 2],
                "max_rate": ordered[-1],
            }
        )
    return out
