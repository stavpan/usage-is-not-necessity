"""Mediation: turning a matrix of direct effects into total effects.

A body of knowledge never appears as a row of the impact matrix, because
knowledge is not a deployable intervention. Quantum mechanics has no line: its
effects arrive *through* other developments -- solid-state physics into the
transistor, nuclear physics into weapons and power, spectroscopy into chemistry,
atomic clocks into satellite navigation, lasers into fibre optics into the
internet. Attributing outcomes only to whatever touched them is therefore a
one-hop projection of a multi-hop process, and it systematically zeroes mediated
causes.

The repair is standard and old: input-output economics. If ``B[j, i]`` is the
extent to which development *j* is required by *i*, direct effects propagate to
total effects through the Leontief inverse (Leontief 1936); the linkage reading
is Hirschman (1958). Then "this development is a seed" stops being a taste and
becomes a number: **forward linkage**, the total effect transmitted downstream per
unit of own impact.

Two warnings from the innovation-studies literature are encoded rather than
decorative. The *linear model of innovation* (science into technology into growth)
is false in its strong form (Kline & Rosenberg 1986): the steam engine preceded
thermodynamics. So the graph admits edges in both directions and the interesting
output is *where* it runs each way. And a DAG is a hypothesis, not an
identification strategy: edges are binary and citable, which makes them far more
auditable than magnitudes, but audit is not identification.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class LinkageResult:
    direct: np.ndarray
    total: np.ndarray
    propagation: np.ndarray
    forward_linkage: np.ndarray
    downstream_share: np.ndarray
    transitive_reach: np.ndarray
    backward_linkage: np.ndarray
    downstream_reach: np.ndarray
    n_edges: int

    def ranked(self, names: tuple[str, ...], key: str = "downstream_share"):
        """Rank by ``key``.

        Default is ``downstream_share``, not ``forward_linkage``. The ratio
        ``(total - direct) / direct`` has ``direct`` in the denominator, so it
        rewards developments with small direct impact -- which is precisely what
        a knowledge-layer row is by construction. Using it as the headline would
        have manufactured the result the analysis was meant to test. The share
        version, ``(total - direct) / total``, is bounded in [0, 1) and has no
        such bias.
        """
        values = np.asarray(getattr(self, key), dtype=float)
        order = np.argsort(-values)
        return [
            {
                "name": names[i],
                "index": int(i),
                "direct": float(self.direct[i]),
                "total": float(self.total[i]),
                "total_own": float(self.propagation[i, i] * self.direct[i]),
                "downstream": float(self.downstream_reach[i]),
                "transitive_reach": int(self.transitive_reach[i]),
                "forward_linkage": float(self.forward_linkage[i]),
                "downstream_share": float(self.downstream_share[i]),
            }
            for i in order
        ]


def adjacency(ids: tuple[str, ...], edges: list[tuple[str, str]]) -> np.ndarray:
    """(n, n) matrix with ``A[user, provider] = 1`` for each enabling edge.

    Orientation: rows are users, columns are providers. Column sums are therefore
    the number of dependants of a development -- its downstream reach.
    """
    index = {name: position for position, name in enumerate(ids)}
    matrix = np.zeros((len(ids), len(ids)))
    for user, provider in edges:
        for endpoint in (user, provider):
            if endpoint not in index:
                raise KeyError(f"enabling edge references unknown development: {endpoint}")
        if user == provider:
            raise ValueError(f"self-loop on {provider}")
        matrix[index[user], index[provider]] = 1.0
    return matrix


def linkage(
    direct_impact: np.ndarray,
    requires: np.ndarray,
    attenuation: float = 0.6,
) -> LinkageResult:
    """Total effects and linkage indices.

    Parameters
    ----------
    direct_impact
        (n,) direct impact per development, e.g. the sum of its coded magnitudes.
    requires
        (n, n) adjacency from :func:`adjacency`: ``requires[j, i] = 1`` means j
        depends on i.
    attenuation
        How much of a downstream development's impact is credited to an upstream
        one it enabled, per hop. This is a **normative parameter** and the weakest
        point of the construction: 1.0 says perfect substitutability, 0.0 says no
        credit at all. It is exposed rather than fixed, and every linkage result is
        reported across a range of values by
        :func:`world_impact.sensitivity.attenuation_sweep`.

    Returns
    -------
    LinkageResult

    Notes
    -----
    ``propagation = (I - attenuation * B)^-1`` where ``B`` is the adjacency
    column-normalised so a development that needs three providers splits its
    dependence between them. Normalising keeps the spectral radius below one, so
    the inverse always exists, acyclic or not.
    """
    requires = np.asarray(requires, dtype=float)
    direct = np.asarray(direct_impact, dtype=float)
    users, _ = requires.shape
    if users != requires.shape[1]:
        raise ValueError("requires must be square")

    column_sums = requires.sum(axis=0)
    weights = np.divide(
        requires,
        np.where(column_sums == 0, 1.0, column_sums),
        out=np.zeros_like(requires),
        where=column_sums != 0,
    )
    propagation = np.linalg.inv(np.eye(users) - attenuation * weights.T)
    total = propagation @ direct
    downstream = np.clip(total - direct, 0.0, None)
    forward_linkage = np.divide(
        downstream,
        np.where(direct == 0, 1.0, direct),
        out=np.zeros_like(direct),
        where=direct != 0,
    )
    downstream_share = np.divide(
        downstream,
        np.where(total <= 0, 1.0, total),
        out=np.zeros_like(direct),
        where=total > 0,
    )
    return LinkageResult(
        direct=direct,
        total=total,
        propagation=propagation,
        forward_linkage=forward_linkage,
        downstream_share=downstream_share,
        transitive_reach=reachability(requires),
        backward_linkage=requires.sum(axis=1),
        downstream_reach=requires.sum(axis=0),
        n_edges=int((requires > 0).sum()),
    )


def reachability(requires: np.ndarray) -> np.ndarray:
    """Number of developments that transitively depend on each development.

    A purely structural measure with no weights, no attenuation and no
    denominator: just how much of the graph sits downstream. The closing
    argument is that its ranking should be read *alongside* the flow-based
    measures, because the flow measures inherit the propagation model while this
    one does not.
    """
    adjacency = (requires > 0).astype(float)
    closure = adjacency.copy()
    frontier = adjacency.copy()
    for _ in range(adjacency.shape[0]):
        frontier = (adjacency @ frontier > 0).astype(float)
        if not frontier.any():
            break
        closure = ((closure + frontier) > 0).astype(float)
    # A development that depends on nothing downstream of itself is its own
    # dependant in the closure; subtract the diagonal.
    np.fill_diagonal(closure, 0.0)
    return closure.sum(axis=0).astype(int)
