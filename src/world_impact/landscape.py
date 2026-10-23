"""A landscape tool for a *chosen* focus, built on what this project established.

Connected Papers, ResearchRabbit, Litmaps, Inciteful and OpenAlex's own graph views all
do the same thing: they show a field's most-cited papers and call that its structure.
Every one of them ranks by **use**. This project's central result is that use and
necessity are not merely different but *opposed* — on the same rows, consequence
correlates with structural necessity at −0.30, breadth at −0.32, peak at −0.15 — so a
tool that shows the most-cited papers is showing the wrong column, and confidently.

This module computes both columns for a narrowed focus and makes the **disagreement**
the headline: the works a field structurally depends on but does not cite directly.
Those are the invisible foundations, and no existing tool surfaces them because no
existing tool computes transitive reach at all.

Three things from the project transfer directly, and they are why this is worth
building rather than wrapping an API:

**Necessity, not popularity.** ``reach`` counts how many works in the neighbourhood
transitively depend on a node. It has no free parameter — no weights, no attenuation,
no denominator — which is the property the paper argues for, because the alternative
carries a parameter that changes the top-ten *set*.

**The audit.** A ranking is worthless if its criterion cannot discriminate. Before
presenting either column this module counts distinct values and reports what it would
drop. Every tool in this space should do this and none does.

**Trajectory.** ``momentum`` (recent citation rate over lifetime rate) separates durable
infrastructure from standards in the act of being replaced. A landscape that cannot tell
those apart will recommend a dying tool.

Honest limits, because the module is built by people who spent a project learning them:

- Reach over a *citation* graph is still reach over untyped edges, so it is an upper
  bound on necessity, not necessity. ``scripts/fetch_contexts.py`` exists to type the
  edges; until it has run, the distinction is unavailable.
- A local graph is small, so reach is coarse. That is the price of narrowing the focus,
  and it is why the audit is reported alongside rather than hidden.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from world_impact import linkage, openalex

DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "data" / "landscape"


def expand(
    seeds: list[str],
    hops: int = 2,
    per_node: int = 40,
    max_nodes: int = 300,
    verbose: bool = False,
) -> dict[str, Any]:
    """Breadth-first over citations *and* references, bounded.

    Both directions matter. Following only citations gives a focus's descendants;
    following only references gives its ancestors. A landscape needs both, because the
    interesting object is a work that many things depend on and few cite directly — and
    that is only visible when both directions are present in one graph.
    """
    nodes: dict[str, dict[str, Any]] = {}
    frontier = list(seeds)

    for hop in range(hops + 1):
        next_frontier: list[str] = []
        for work_id in frontier:
            if len(nodes) >= max_nodes:
                break
            if work_id in nodes:
                continue
            record = openalex.work_by_id(work_id)
            if record is None:
                continue
            nodes[work_id] = record
            if hop < hops:
                next_frontier.extend(record.get("referenced_works") or [])
                next_frontier.extend(openalex.citing_ids(work_id, limit=per_node))
        frontier = [work_id for work_id in next_frontier if work_id not in nodes]
        if verbose:
            print(f"  hop {hop}: {len(nodes)} nodes, {len(frontier)} queued")
        if not frontier:
            break

    ids = tuple(nodes)
    known = set(ids)
    # `ref != work_id` because OpenAlex records do sometimes list a work as its own
    # reference -- a version pair sharing an ID, or a dataset citing its own paper.
    # `linkage.adjacency` refuses self-loops rather than silently dropping them, which
    # is how this was found, and the filter belongs here where the edge is built.
    edges = [
        (work_id, ref)
        for work_id, record in nodes.items()
        for ref in (record.get("referenced_works") or [])
        if ref in known and ref != work_id
    ]
    return {"nodes": nodes, "ids": ids, "edges": edges}


def analyse(graph: dict[str, Any], reference_year: int = 2025) -> dict[str, Any]:
    """The two columns, the disagreement between them, and the audit of both."""
    from world_impact import convergence as cv

    ids = graph["ids"]
    edges = graph["edges"]
    nodes = graph["nodes"]

    in_degree = dict.fromkeys(ids, 0)
    for _, provider in edges:
        in_degree[provider] += 1

    reach = dict(
        zip(ids, linkage.reachability(linkage.adjacency(ids, edges)).tolist(), strict=True)
    )

    # Ties broken by citation count so the output is stable; the audit reports how many
    # ties there were rather than pretending the order is fully determined.
    by_use = sorted(ids, key=lambda w: (-in_degree[w], -nodes[w]["cited_by_count"]))
    by_necessity = sorted(ids, key=lambda w: (-reach[w], -in_degree[w]))
    use_rank = {work_id: position + 1 for position, work_id in enumerate(by_use)}
    necessity_rank = {work_id: position + 1 for position, work_id in enumerate(by_necessity)}

    # The headline: structurally load-bearing and rarely cited *within the focus*.
    #
    # Defined by absolute thresholds, not by a rank difference, and not by a ratio.
    # Both alternatives were tried and both failed. A rank difference (use rank minus
    # necessity rank) is meaningless in a list of 200: a node with reach 1 scored
    # "+63" purely because it happened to sit high on one ordering, and the output was
    # dominated by that noise. A ratio such as reach / in_degree is worse, because its
    # denominator rewards exactly the sparse nodes it is meant to find -- the same
    # denominator trap the paper documents. So: reach in the top quartile AND cited at
    # most twice, ordered by reach.
    positive = sorted(value for value in reach.values() if value > 0)
    threshold = positive[int(len(positive) * 0.75)] if positive else 0
    disagreement = sorted(
        (
            {
                "id": work_id,
                "title": nodes[work_id]["title"],
                "year": nodes[work_id]["year"],
                "citations": nodes[work_id]["cited_by_count"],
                "reach": reach[work_id],
                "in_degree": in_degree[work_id],
                "necessity_rank": necessity_rank[work_id],
                "use_rank": use_rank[work_id],
            }
            for work_id in ids
            if reach[work_id] >= threshold and in_degree[work_id] <= 2 and threshold > 0
        ),
        key=lambda row: (-row["reach"], row["in_degree"]),
    )

    distinct = {
        "in_degree": len({in_degree[w] for w in ids}),
        "reach": len({reach[w] for w in ids}),
    }
    dropped = [name for name, count in distinct.items() if count < cv.MIN_DISTINCT_VALUES]
    rank_correlation = float(
        np.corrcoef([use_rank[w] for w in ids], [necessity_rank[w] for w in ids])[0, 1]
    )

    momentum = {
        work_id: cv.trajectory_momentum(
            nodes[work_id].get("counts_by_year") or {}, reference_year
        )
        for work_id in ids
    }
    rising = sorted(ids, key=lambda w: -momentum[w])[:10]
    decaying = [w for w in sorted(ids, key=lambda w: momentum[w]) if momentum[w] > 0][:10]

    return {
        "n_nodes": len(ids),
        "n_edges": len(edges),
        "in_degree": in_degree,
        "reach": reach,
        "momentum": momentum,
        "by_use": by_use,
        "by_necessity": by_necessity,
        "disagreement": disagreement,
        "distinct_values": distinct,
        "dropped_criteria": dropped,
        "rank_correlation": rank_correlation,
        "rising": rising,
        "decaying": decaying,
    }
