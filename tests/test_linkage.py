"""Mediation: the enabling graph, the Leontief inverse, and the metric trap.

The trap matters more than the arithmetic. ``forward_linkage`` divides by the
development's own direct impact, so a node with a tiny direct footprint scores
enormously -- which is what a knowledge row is by construction. A test asserts
that trap explicitly so nobody "fixes" the code back into it.
"""

from __future__ import annotations

import numpy as np
import pytest

from world_impact import linkage

IDS = ("a", "b", "c")


def test_adjacency_orientation() -> None:
    """rows are users, columns are providers."""
    matrix = linkage.adjacency(IDS, [("b", "a")])
    assert matrix[1, 0] == 1.0
    assert matrix[0, 1] == 0.0


def test_adjacency_rejects_unknown_and_self() -> None:
    with pytest.raises(KeyError):
        linkage.adjacency(IDS, [("b", "ghost")])
    with pytest.raises(ValueError, match="self-loop"):
        linkage.adjacency(IDS, [("a", "a")])


def test_no_edges_means_no_propagation() -> None:
    direct = np.array([1.0, 2.0, 3.0])
    result = linkage.linkage(direct, linkage.adjacency(IDS, []))
    assert np.allclose(result.total, direct)
    assert np.allclose(result.downstream_share, 0.0)
    assert result.n_edges == 0


def test_chain_propagates_upstream() -> None:
    """a -> b -> c means b and c depend on a, so a's total exceeds its direct."""
    requires = linkage.adjacency(IDS, [("b", "a"), ("c", "b")])
    result = linkage.linkage(np.array([1.0, 1.0, 1.0]), requires, attenuation=1.0)
    assert result.total[0] == pytest.approx(3.0)
    assert result.total[1] == pytest.approx(2.0)
    assert result.total[2] == pytest.approx(1.0)
    assert result.downstream_share[0] > result.downstream_share[1]


def test_zero_attenuation_recovers_direct_effects() -> None:
    requires = linkage.adjacency(IDS, [("b", "a"), ("c", "b")])
    direct = np.array([5.0, 1.0, 1.0])
    result = linkage.linkage(direct, requires, attenuation=0.0)
    assert np.allclose(result.total, direct)


def test_forward_linkage_denominator_trap_is_real() -> None:
    """The ratio (total - direct)/direct flatters a node with a small direct
    footprint, which is what a knowledge row is by construction. The bounded
    share compresses that discrepancy rather than reproducing it.

    A first version of this test asserted the shares were *equal*; that was
    wrong, because the share also depends on the dependant's own impact. The
    correct assertion is comparative.
    """
    requires = linkage.adjacency(("root", "user"), [("user", "root")])
    small = linkage.linkage(np.array([1.0, 9.0]), requires, attenuation=1.0)
    large = linkage.linkage(np.array([9.0, 1.0]), requires, attenuation=1.0)
    # the ratio separates them by a factor of ~36
    assert small.forward_linkage[0] / large.forward_linkage[0] > 10
    # the share separates them by a factor of 9 -- i.e. it compresses, and does
    # not reward the small denominator for being small
    assert small.downstream_share[0] > large.downstream_share[0]
    assert small.downstream_share[0] / large.downstream_share[0] < 10
    # both are bounded, which the ratio is not
    assert 0.0 <= large.downstream_share[0] < 1.0


def test_reachability_counts_descendants() -> None:
    requires = linkage.adjacency(IDS, [("b", "a"), ("c", "b")])
    reach = linkage.reachability(requires)
    assert reach[0] == 2  # b and c
    assert reach[1] == 1  # c
    assert reach[2] == 0


def test_reachability_ignores_cycles_safely() -> None:
    """A 2-cycle terminates instead of diverging. Note the id tuple must match
    the nodes present: an earlier version of this test passed the three-element
    IDS while defining a two-node graph, so the isolated third node scored 0 and
    the assertion was measuring the wrong thing."""
    ids = ("a", "b")
    requires = linkage.adjacency(ids, [("a", "b"), ("b", "a")])
    reach = linkage.reachability(requires)
    assert set(reach.tolist()) == {1}


def test_ranked_uses_the_bounded_measure_by_default() -> None:
    requires = linkage.adjacency(IDS, [("b", "a"), ("c", "b")])
    result = linkage.linkage(np.array([1.0, 1.0, 1.0]), requires)
    top = result.ranked(IDS)[0]
    assert "downstream_share" in top
    assert top["name"] == "a"
    by_reach = result.ranked(IDS, key="transitive_reach")[0]
    assert by_reach["transitive_reach"] >= top["transitive_reach"]
