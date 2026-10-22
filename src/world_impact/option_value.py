"""Option value: what a development makes *reachable*, not what it does.

The impact matrix measures outcomes a development produced. It is blind to a
different quantity: the futures a development made possible. Maxwell's equations
fed nobody; they made radio, radar, power distribution and the electrical
industry *reachable*. Neither the matrix nor forward linkage can see that,
because linkage asks how much of an existing effect flows downstream -- not how
much of the space of possible things did not exist before.

The formalisation is deliberately crude, and stated rather than hidden:

    capability space    the set of results *available* given prerequisites
    availability        a result is available iff every prerequisite is
                        available (conjunctive reading of ``requires``)
    criticality(i)      share of weighted capability space lost if i is removed
    substitutability(i) share of i's dependants that already depend on another
                        result of the same kind (same coarse parent)
    option_value(i)     criticality(i) x (1 - substitutability(i))

Two properties follow from the conjunctive reading and bound the result in
*both* directions: option value is an **upper** bound (a real substitute outside
the coded prerequisite set would reduce it), and substitutability is a **lower**
bound (we only count alternatives already present in a dependant's list).

Related literature this builds on rather than invents: most-vital-vertex analysis
(Ball & Golden 1989); the product-space reading of capability accumulation
(Hidalgo et al. 2007; Hidalgo 2021); and real-options theory for the underlying
idea that value can sit in the option rather than the flow (Dixit & Pindyck 1994;
Arrow & Fisher 1974).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np


def requires_matrix(ids: tuple[str, ...], edges: Iterable[tuple[str, str]]) -> np.ndarray:
    """(n, n) boolean matrix with ``M[user, provider] = True`` per prerequisite."""
    index = {name: position for position, name in enumerate(ids)}
    matrix = np.zeros((len(ids), len(ids)), dtype=bool)
    for user, provider in edges:
        if user not in index:
            raise KeyError(f"unknown development in edge: {user}")
        if provider not in index:
            raise KeyError(f"unknown development in edge: {provider}")
        matrix[index[user], index[provider]] = True
    return matrix


def available(
    requires: np.ndarray,
    removed: np.ndarray | None = None,
    max_iterations: int | None = None,
) -> np.ndarray:
    """Fixed point of conjunctive availability.

    A result with no prerequisites is available; a result with prerequisites is
    available only when *all* of them are. Iterated to a fixed point, which
    terminates in at most ``n`` passes on an acyclic graph and is guarded
    otherwise so a cycle cannot hang the pipeline.
    """
    requires = np.asarray(requires, dtype=bool)
    n = requires.shape[0]
    blocked = np.zeros(n, dtype=bool) if removed is None else np.asarray(removed, dtype=bool)
    available_now = np.zeros(n, dtype=bool)
    limit = n + 2 if max_iterations is None else max_iterations
    for _ in range(limit):
        unmet = (requires & ~available_now).sum(axis=1)
        updated = (~blocked) & (unmet == 0)
        if np.array_equal(updated, available_now):
            break
        available_now = updated
    return available_now


@dataclass
class OptionValueResult:
    """Per-development option value, with both bounds stated in the docstring."""

    criticality: np.ndarray
    substitutability: np.ndarray
    option_value: np.ndarray
    reach_lost: np.ndarray
    n_dependants: np.ndarray
    total_capability: float
    n_available: int

    def ranked(self, names: tuple[str, ...]) -> list[dict[str, Any]]:
        order = np.argsort(-self.option_value)
        return [
            {
                "name": names[i],
                "index": int(i),
                "option_value": float(self.option_value[i]),
                "criticality": float(self.criticality[i]),
                "substitutability": float(self.substitutability[i]),
                "reach_lost": int(self.reach_lost[i]),
                "n_dependants": int(self.n_dependants[i]),
            }
            for i in order
        ]


def option_value(
    requires: np.ndarray,
    weights: np.ndarray,
    parents: np.ndarray | None = None,
) -> OptionValueResult:
    """Option value for every node.

    Parameters
    ----------
    requires
        (n, n) boolean prerequisite matrix.
    weights
        (n,) capability weights. Direct impact gives "how much capability is
        lost"; ones give "how many results are lost". The caller reports both;
        neither is privileged here.
    parents
        (n,) integer class label per node, used to decide whether a dependant
        already has an alternative of the same kind. ``None`` disables the
        discount, which is equivalent to asserting that no substitutes exist.
    """
    requires = np.asarray(requires, dtype=bool)
    weights = np.asarray(weights, dtype=float)
    n = requires.shape[0]

    baseline = available(requires)
    total = float(weights[baseline].sum())

    criticality = np.zeros(n)
    reach_lost = np.zeros(n, dtype=int)
    for i in range(n):
        removed = np.zeros(n, dtype=bool)
        removed[i] = True
        lost = baseline & ~available(requires, removed=removed)
        reach_lost[i] = int(lost.sum())
        criticality[i] = float(weights[lost].sum() / total) if total > 0 else 0.0

    n_dependants = requires.sum(axis=0).astype(int)
    substitutability = np.ones(n)
    if parents is not None:
        parents = np.asarray(parents)
        for i in range(n):
            dependants = np.flatnonzero(requires[:, i])
            if dependants.size == 0:
                substitutability[i] = 1.0
                continue
            alternatives = 0
            for j in dependants:
                others = np.setdiff1d(np.flatnonzero(requires[j]), [i])
                if others.size and np.isin(parents[others], parents[i]).any():
                    alternatives += 1
            substitutability[i] = alternatives / dependants.size

    return OptionValueResult(
        criticality=criticality,
        substitutability=substitutability,
        option_value=criticality * (1.0 - substitutability),
        reach_lost=reach_lost,
        n_dependants=n_dependants,
        total_capability=total,
        n_available=int(baseline.sum()),
    )


def criticality_null(
    requires: np.ndarray,
    weights: np.ndarray,
    rng: np.random.Generator,
    n_iter: int = 200,
) -> dict[str, float]:
    """Null distribution for criticality under a degree-preserving rewiring.

    This null is necessary and easy to forget. Criticality is mechanically large
    for a *root*: a node with no prerequisites that many others depend on will
    look critical in any graph of that shape. Rewiring each user's prerequisite
    set to a random set of the same size keeps every node's out-degree exactly,
    so the comparison asks the only question worth asking: **is this node's
    criticality higher than a node with the same number of prerequisites would
    get by accident?**

    The rewiring can create cycles, which the fixed-point guard in
    :func:`available` terminates safely.
    """
    requires = np.asarray(requires, dtype=bool)
    weights = np.asarray(weights, dtype=float)
    n = requires.shape[0]
    out_degree = requires.sum(axis=1)
    baseline = available(requires)
    total = float(weights[baseline].sum())

    maxima = np.empty(n_iter)
    means = np.empty(n_iter)
    for iteration in range(n_iter):
        rewired = np.zeros_like(requires)
        for j in range(n):
            k = int(out_degree[j])
            if k == 0:
                continue
            candidates = np.setdiff1d(np.arange(n), [j])
            chosen = rng.choice(candidates, size=min(k, candidates.size), replace=False)
            rewired[j, chosen] = True
        rewired_baseline = available(rewired)
        rewired_total = float(weights[rewired_baseline].sum())
        values = np.zeros(n)
        for i in range(n):
            removed = np.zeros(n, dtype=bool)
            removed[i] = True
            lost = rewired_baseline & ~available(rewired, removed=removed)
            values[i] = float(weights[lost].sum() / rewired_total) if rewired_total else 0.0
        maxima[iteration] = float(np.max(values))
        means[iteration] = float(np.mean(values))
    _ = total

    observed = option_value(requires, weights)
    result: dict[str, Any] = {
        "observed_max": float(observed.criticality.max()),
        "observed_mean": float(observed.criticality.mean()),
        "null_max_mean": float(maxima.mean()),
        "null_max_p95": float(np.percentile(maxima, 95)),
        "null_mean_mean": float(means.mean()),
        "p_value": float((maxima >= observed.criticality.max()).mean()),
        "n_iterations": int(n_iter),
        "interpretation": (
            "p is the share of degree-preserving rewirings whose most critical node "
            "is at least as critical as the observed most critical node. A large p "
            "means the top of the ranking is a property of the graph's shape, not of "
            "which node sits there."
        ),
    }
    return result


def future_space_expansion(requires: np.ndarray) -> np.ndarray:
    """Share of the available capability space that is lost without each node.

    A companion to :func:`option_value` that needs no weights at all, so it
    cannot be accused of smuggling in an importance judgement: it is just the
    fraction of results that stop being reachable.
    """
    requires = np.asarray(requires, dtype=bool)
    n = requires.shape[0]
    baseline = available(requires)
    total = int(baseline.sum())
    expansion = np.zeros(n)
    for i in range(n):
        removed = np.zeros(n, dtype=bool)
        removed[i] = True
        lost = baseline & ~available(requires, removed=removed)
        expansion[i] = float(lost.sum() / total) if total else 0.0
    return expansion
