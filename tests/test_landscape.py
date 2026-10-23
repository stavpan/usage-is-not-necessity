"""The landscape tool's analysis, on a synthetic graph so it needs no network.

The point of these tests is the *ranking* behaviour, not the fetch: reach must count
descendants rather than ancestors, and the gap list must be defined by absolute
thresholds rather than by a rank difference or a ratio.
"""

from __future__ import annotations

from world_impact import landscape


def chain() -> dict:
    """A -> B -> C -> D, plus two works that cite nothing.

    `reach` counts *descendants*, so A has reach 0 (nothing depends on it) and D has
    reach 3. Getting that backwards is not hypothetical: it happened, and it inverted
    a result in the paper.
    """
    ids = ("A", "B", "C", "D", "X", "Y")
    nodes = {
        "A": {"title": "A", "year": 2020, "cited_by_count": 10, "counts_by_year": {}},
        "B": {"title": "B", "year": 2019, "cited_by_count": 20, "counts_by_year": {}},
        "C": {"title": "C", "year": 2018, "cited_by_count": 30, "counts_by_year": {}},
        "D": {"title": "D", "year": 2017, "cited_by_count": 40, "counts_by_year": {}},
        "X": {"title": "X", "year": 2021, "cited_by_count": 5, "counts_by_year": {}},
        "Y": {"title": "Y", "year": 2021, "cited_by_count": 5, "counts_by_year": {}},
    }
    edges = [("A", "B"), ("B", "C"), ("C", "D")]
    return {"nodes": nodes, "ids": ids, "edges": edges}


def test_reach_counts_descendants_not_ancestors() -> None:
    analysis = landscape.analyse(chain())
    reach = analysis["reach"]
    assert reach["A"] == 0, "nothing depends on the newest link"
    assert reach["D"] == 3, "everything downstream depends on the oldest link"
    assert reach["B"] == 1 and reach["C"] == 2


def test_in_degree_is_the_use_column() -> None:
    analysis = landscape.analyse(chain())
    assert analysis["in_degree"]["D"] == 1
    assert analysis["in_degree"]["A"] == 0
    assert analysis["by_use"][0] == "D", "most-cited-within-focus comes first"


def test_the_gap_uses_absolute_thresholds_not_rank_differences() -> None:
    """A node with reach 1 must not appear, however it ranks.

    A rank difference put a reach-1 node at the top of the list with a score of "+63"
    purely because it sat high on one ordering. A ratio such as reach/in_degree is worse
    still: its denominator rewards the sparse nodes the list exists to find.
    """
    analysis = landscape.analyse(chain())
    for row in analysis["disagreement"]:
        assert row["reach"] >= 1
        assert row["in_degree"] <= 2
        assert "gap" not in row, "the rank-difference score was removed on purpose"


def test_the_audit_reports_a_criterion_that_cannot_discriminate() -> None:
    """Every node citing exactly one other gives in-degree two distinct values."""
    analysis = landscape.analyse(chain())
    assert analysis["distinct_values"]["in_degree"] < 10
    assert "in_degree" in analysis["dropped_criteria"]
