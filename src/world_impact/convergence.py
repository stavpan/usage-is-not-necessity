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

MIN_COVERAGE = 0.95
"""A criterion must have its input present for this share of rows to be allowed to rank.

The citer cache covers 520 of the 1,300 seeds in the extended corpus. Letting the
citer criteria rank anyway would score 780 works at zero for a reason that has
nothing to do with the works -- the criterion would be measuring *cache coverage* and
would present that as a property of the papers. That is the same failure as the
degenerate ``reach`` criterion, one level up: a criterion must not rank on missing
data. Criteria below the coverage floor are dropped and named, exactly as degenerate
ones are.
"""

MIN_DISTINCT_VALUES = 10
"""A criterion must take at least this many distinct values to be allowed to rank.

Below it, the ranks of the top works are decided by tie-breaking rather than by
measurement. ``reach`` took three distinct values and put Shannon 1948 at rank 1.
"""

RECENT_WINDOW = 5
"""Years at the end of the corpus window over which ``momentum`` is measured."""

CRITERIA = (
    "citations",
    "rate",
    "field_zscore",
    "momentum",
    "top_citations",
    "reach",
    "upstream",
    "unique_citers",
    "citer_prestige",
    "citer_reach",
)
CRITERION_LABEL = {
    "citations": "total citations",
    "rate": "citations per year",
    "field_zscore": "rate z-score within field",
    "momentum": "recent rate / lifetime rate",
    "top_citations": "cited by other top works",
    "reach": "distinct citing fields",
    "upstream": "upstreamness of its field",
    "unique_citers": "unique citing works",
    "citer_prestige": "median citations of its citers",
    "citer_reach": "distinct fields among its citers",
}

CRITERION_INPUT = {
    "momentum": "counts_by_year",
    "unique_citers": "citers",
    "citer_prestige": "citers",
    "citer_reach": "citers",
}
"""Which input each criterion needs, so missing input is detectable as missingness
rather than as a zero. Criteria absent from this map need nothing beyond the seed
record and are always available."""
"""The ``citer_*`` criteria exist to break the usage bias.

``citations`` and ``unique_citers`` count how many use a work. ``citer_prestige``
asks how *important* the users are: the median citation count of the work's 25
most-cited citers. A work cited by few but very heavy works is foundational; a
work cited by everyone but by ordinary papers is a service. If a count-based
ranking is structurally biased toward instruments -- which is the suspicion -- then
theory should rank low on the counting criteria and higher on the prestige one.

``field_zscore`` removes the field-size effect that raw counts carry: it is the
work's citations-per-year standardised within its own field, so a small field's best
work is not punished for its field being small.

``momentum`` is the one criterion derived from the citation *trajectory* rather than
the citation total, and it exists to separate an instrument from a foundation with a
measurement instead of a judgement. A tool that gets superseded loses citations once
the successor appears; a foundation does not. Momentum is the mean annual citations
over the last ``RECENT_WINDOW`` years divided by the work's lifetime mean annual
citations, so it is dimensionless and roughly age-independent: a work accruing
citations at its historical average scores 1.0, and a work that has been displaced
scores below 1.0. It is not a clean measure of supersession -- global citation volume
grows, so the corpus median is above 1, and a decaying work in a fast-growing field
can still score above 1 -- which is why it is used comparatively, to contrast groups,
rather than as an absolute threshold.
"""


def trajectory_momentum(counts_by_year: dict[Any, Any], reference_year: int) -> float:
    """Recent annual rate divided by lifetime annual rate.

    Zero when a work has no trajectory data, so the column is constant for a corpus
    fetched without ``counts_by_year`` and the ``active`` mechanism drops it rather
    than letting a tie-break pretend it ranked something.
    """
    if not counts_by_year:
        return 0.0
    series = {int(year): float(count) for year, count in counts_by_year.items()}
    first = min(series)
    lifetime_years = max(reference_year - first + 1, 1)
    lifetime_mean = sum(series.values()) / lifetime_years
    if lifetime_mean <= 0:
        return 0.0
    window = range(reference_year - RECENT_WINDOW + 1, reference_year + 1)
    recent = [series.get(year, 0.0) for year in window]
    return float(sum(recent) / RECENT_WINDOW / lifetime_mean)


def criteria_table(
    corpus: dict[str, Any],
    upstreamness: dict[str, dict[str, float]] | None = None,
    citers: dict[str, Any] | None = None,
    reference_year: int = 2024,
) -> list[dict[str, Any]]:
    """One row per seed work, with every criterion as a raw value.

    ``citers`` is the output of :func:`world_impact.openalex.fetch_citers`. When it
    is absent the four columns it supplies are constant zero, and the ``active``
    mechanism in :func:`convergence` drops them rather than letting a tie-break
    inflate support.
    """
    upstreamness = upstreamness or {}
    citers = citers or {}
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
        record = citers.get(str(work.get("id"))) or {}
        momentum = trajectory_momentum(work.get("counts_by_year") or {}, reference_year)
        top_citers = record.get("top_citers") or []
        citer_citations = sorted(
            float(citer.get("cited_by_count") or 0) for citer in top_citers
        )
        citer_fields = {
            citer.get("field") for citer in top_citers if citer.get("field")
        }
        rows.append(
            {
                "id": work.get("id"),
                "title": work.get("title") or "",
                "year": year,
                "field": field,
                "citations": citations,
                "age": age,
                "rate": citations / age,
                "momentum": momentum,
                "top_citations": float(referenced_by.get(work.get("id"), 0)),
                "reach": float(len(citing_fields.get(work.get("id"), set()))),
                "upstream": float(upstreamness.get(field, {}).get("ratio", 1.0)),
                "_inputs": {
                    "counts_by_year": bool(work.get("counts_by_year")),
                    "citers": bool(record),
                },
                "unique_citers": float(record.get("n_citers") or 0),
                "citer_prestige": (
                    citer_citations[len(citer_citations) // 2] if citer_citations else 0.0
                ),
                "citer_reach": float(len(citer_fields)),
            }
        )

    # Within-field standardisation of citations-per-year, so a small field's best
    # work is not punished for its field being small.
    #
    # This replaced a within-field *percentile rank*, which was a mistake: with
    # only 20 seeds per field the maximum percentile is always 1.0, so 26 works --
    # one per field -- tied at the top and the criterion could not discriminate
    # where it mattered. A z-score is continuous and has no such tie.
    by_field: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_field.setdefault(row["field"], []).append(row)
    for members in by_field.values():
        rates = [row["rate"] for row in members]
        mean = sum(rates) / len(rates)
        variance = sum((value - mean) ** 2 for value in rates) / max(len(rates) - 1, 1)
        spread = variance**0.5 or 1.0
        for row in members:
            row["field_zscore"] = (row["rate"] - mean) / spread
    return rows


def redundant_pairs(
    agreement: dict[tuple[str, str], float], threshold: float = 0.95
) -> list[dict[str, Any]]:
    """Criteria that are the same criterion in different clothes.

    Found three times in this project: ``top_citations`` and ``reach`` at r = 1.00,
    ``unique_citers`` and ``citations`` at r = 0.99, and (earlier) nine axes whose
    effective rank was 3. A criterion list is only as long as its *independent*
    members, so the redundancies are reported as a result rather than tolerated as
    a curiosity.
    """
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for (a, b), value in agreement.items():
        if a == b or (b, a) in seen or abs(value) < threshold:
            continue
        seen.add((a, b))
        out.append({"a": a, "b": b, "r": round(value, 3)})
    return sorted(out, key=lambda row: -abs(row["r"]))


def effective_criteria(
    agreement: dict[tuple[str, str], float], threshold: float = 0.95
) -> int:
    """How many criteria remain after collapsing redundant ones."""
    redundant = {frozenset((row["a"], row["b"])) for row in redundant_pairs(agreement, threshold)}
    keys = sorted({key for pair in agreement for key in pair})
    merged = list(keys)
    for pair in redundant:
        left, right = sorted(pair)
        if left in merged and right in merged:
            merged.remove(right)
    return len(merged)


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

    Criteria that vary but only over a handful of values are dropped too; see
    ``degenerate`` and ``MIN_DISTINCT_VALUES``.
    """

    uncovered: tuple[str, ...] = ()
    """Criteria dropped because their input is missing for too many rows.

    Distinct from ``degenerate``: a degenerate criterion has its input everywhere and
    varies too little, while an uncovered one varies fine on the rows that have it and
    would rank the rest as zero. The citer criteria in the 1,300-seed corpus are the
    second case, and letting them rank would have measured cache coverage.
    """

    degenerate: tuple[str, ...] = ()
    """Criteria dropped for having too few distinct values to discriminate.

    ``top_citations`` and ``reach`` were both near-degenerate: over the 520 seeds
    they take 5 and 3 distinct values respectively, because seeds selected as the
    most-cited work in each field rarely cite one another. Seven works tie at the
    maximum ``reach`` and therefore occupy ranks 1-7 in arbitrary tie-break order.
    The consequence was not academic: the single theory paper in the consensus,
    Shannon 1948, held *rank 1* on ``reach``, and that rank-1 was pure tie-break.
    A criterion that cannot discriminate must not be allowed to decide a headline.
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


def method_theory_gap(
    rows: list[dict[str, Any]], classify: Any
) -> dict[str, Any]:
    """How much more are method-classified works cited than theory-classified ones?

    This is the test of the suspicion. If citation counts measure *usage*, then
    methods should dominate on every counting criterion -- and if that is the
    whole story, theory should also be *lower* on citer prestige, because the
    works that use a method include everyone, important or not. If theory is
    instead cited by heavier works while being cited less often, then the two
    quantities are genuinely different and a count-based ranking is measuring the
    wrong thing.
    """
    groups: dict[str, list[dict[str, Any]]] = {"method": [], "theory": [], "unclassified": []}
    for row in rows:
        groups.setdefault(classify(row["title"]), []).append(row)

    def median(values: list[float]) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        return float(ordered[len(ordered) // 2])

    profile: dict[str, dict[str, float]] = {}
    for name, members in groups.items():
        if not members:
            continue
        profile[name] = {
            "n": float(len(members)),
            "citations": median([row["citations"] for row in members]),
            "rate": median([row["rate"] for row in members]),
            "momentum": median([row["momentum"] for row in members]),
            "unique_citers": median([row["unique_citers"] for row in members]),
            "citer_prestige": median([row["citer_prestige"] for row in members]),
            "citer_reach": median([row["citer_reach"] for row in members]),
        }

    verdict = "insufficient groups to compare"
    if "method" in profile and "theory" in profile:
        m, t = profile["method"], profile["theory"]
        counting = {
            key: (m[key] / t[key] if t[key] else float("inf"))
            for key in ("citations", "rate", "unique_citers")
        }
        # The prestige leg only means anything when citer data exists for the corpus.
        # In the extended corpus it does not, and a ratio of zero to zero would have
        # been reported as `inf` -- an infinite finding generated by missing data.
        have_prestige = bool(m["citer_prestige"]) and bool(t["citer_prestige"])
        prestige = m["citer_prestige"] / t["citer_prestige"] if have_prestige else float("nan")
        momentum_ratio = t["momentum"] / m["momentum"] if m["momentum"] else float("nan")
        # The verdict is the *contrast*, not an absolute threshold. An earlier
        # version required every counting ratio to exceed 1.5 and therefore
        # reported "no gap" for a sample whose whole point was a 1.31x counting
        # gap against a 0.63x prestige ratio -- i.e. theory cited less often by
        # heavier works, which is the informative case, missed by a threshold.
        counting_gap = min(counting.values()) > 1.05
        decay_gap = momentum_ratio > 1.05
        if counting_gap and decay_gap:
            verdict = (
                "BIAS CONFIRMED and DIAGNOSED: methods are cited more often "
                f"(x{counting['citations']:.2f} on citations, x{counting['rate']:.2f} on "
                f"rate) AND decay faster (theory/method momentum ratio "
                f"{momentum_ratio:.2f} -- theory retains its citation rate better). The "
                "counting criteria therefore reward instruments twice: for being used "
                "and for being used now."
            )
        elif counting_gap and have_prestige and prestige < 0.95:
            verdict = (
                "CONFIRMED and informative: methods are cited more often "
                f"(x{counting['citations']:.2f} on citations, x{counting['rate']:.2f} "
                f"on rate) while theory is cited by HEAVIER works (method/theory "
                f"prestige ratio {prestige:.2f}). Counting measures usage; usage and "
                "importance come apart -- modestly, not dramatically."
            )
        elif counting_gap:
            verdict = (
                "BIAS CONFIRMED, no rescue: methods dominate the counting criteria "
                f"(x{counting['citations']:.2f} on citations) with no compensating "
                "signal. A count-based consensus is a usage ranking."
            )
        else:
            verdict = (
                "no material method/theory gap in this sample "
                f"(citations ratio {counting['citations']:.2f})"
            )
    return {"profile": profile, "verdict": verdict}


def convergence(
    corpus: dict[str, Any],
    upstreamness: dict[str, dict[str, float]] | None = None,
    citers: dict[str, Any] | None = None,
    reference_year: int = 2024,
) -> ConvergenceResult:
    """Build the criteria table, the ranks, and the criterion-agreement matrix."""
    rows = criteria_table(corpus, upstreamness, citers, reference_year)
    # Drop criteria that do not vary: a constant column ranks by tie-break alone
    # and would inflate every work's support. Then drop criteria that vary but too
    # coarsely to discriminate -- see MIN_DISTINCT_VALUES.
    cardinality = {
        criterion: len({round(row[criterion], 9) for row in rows}) for criterion in CRITERIA
    }
    coverage = {
        criterion: (
            sum(1 for row in rows if row.get("_inputs", {}).get(CRITERION_INPUT[criterion]))
            / max(len(rows), 1)
            if criterion in CRITERION_INPUT
            else 1.0
        )
        for criterion in CRITERIA
    }
    active = tuple(
        criterion
        for criterion in CRITERIA
        if cardinality[criterion] >= MIN_DISTINCT_VALUES
        and coverage[criterion] >= MIN_COVERAGE
    )
    degenerate = tuple(
        criterion
        for criterion in CRITERIA
        if 1 < cardinality[criterion] < MIN_DISTINCT_VALUES
        and coverage[criterion] >= MIN_COVERAGE
    )
    uncovered = tuple(
        criterion for criterion in CRITERIA if coverage[criterion] < MIN_COVERAGE
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
        degenerate=degenerate,
        uncovered=uncovered,
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
