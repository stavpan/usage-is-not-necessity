"""Schema and cross-file validation.

These tests are the coding protocol under test: if a rule matters it has to be
enforceable, and every rule here is one the first draft got wrong.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from world_impact.data import check, check_edges, load_dataset
from world_impact.schema import Development, Era, Outcome, Source


@pytest.fixture(scope="module")
def dataset():
    return load_dataset()


def test_dataset_loads(dataset) -> None:
    assert dataset.n_developments > 40
    assert dataset.n_outcomes == 18
    assert dataset.edges, "the enabling graph should not be empty"
    assert dataset.knowledge_mask().sum() >= 5


def test_matrix_shape_and_sparsity(dataset) -> None:
    matrix = dataset.matrix()
    assert matrix.shape == (dataset.n_developments, dataset.n_outcomes)
    assert matrix.max() <= 3
    assert 0.15 < (matrix > 0).mean() < 0.45


def test_every_effect_has_a_declared_source(dataset) -> None:
    for development in dataset.developments:
        assert development.sources
        for key in development.sources:
            assert key in dataset.sources


def test_magnitude_out_of_range_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Development(
            id="x",
            name="x",
            onset=2000,
            era=Era.contemporary,
            extern=["information"],
            sources=["s"],
            effects={"health": 7},
        )


def test_extra_fields_are_rejected() -> None:
    """The schema is closed: a typo'd field name must fail loudly rather than be
    silently dropped, which is how a coding rule quietly stops applying."""
    with pytest.raises(ValidationError):
        Development(
            id="x",
            name="x",
            onset=2000,
            era=Era.contemporary,
            extern=["information"],
            sources=["s"],
            effects={"health": 1},
            effect={"health": 2},  # typo
        )


def test_unknown_outcome_is_caught(dataset) -> None:
    broken = dataset.developments[0].model_copy(update={"effects": {"not_an_outcome": 2}})
    problems = check(dataset.outcomes, (broken,), dataset.sources)
    assert any("unknown outcome" in problem for problem in problems)


def test_undeclared_source_is_caught(dataset) -> None:
    broken = dataset.developments[0].model_copy(update={"sources": ["ghost2020"]})
    problems = check(dataset.outcomes, (broken,), dataset.sources)
    assert any("undeclared source" in problem for problem in problems)


def test_duplicate_edge_is_caught(dataset) -> None:
    edge = dataset.edges[0]
    problems = check_edges(dataset.developments, (edge, edge))
    assert any("duplicate edge" in problem for problem in problems)


def test_unknown_edge_endpoint_is_caught(dataset) -> None:
    problems = check_edges(dataset.developments, (("ghost", dataset.ids[0]),))
    assert any("unknown development" in problem for problem in problems)


def test_enabling_graph_is_acyclic_as_coded(dataset) -> None:
    """Not a law of nature -- the linear model of innovation is false -- but the
    graph as currently coded should be acyclic, so any cycle is a bug."""
    problems = check_edges(dataset.developments, dataset.edges)
    assert not any("cycle" in problem for problem in problems)


def test_source_needs_a_container() -> None:
    with pytest.raises(ValidationError):
        Source(key="k", author="a", year=2000, title="t", kind="book")


def test_outcome_requires_custodian() -> None:
    with pytest.raises(ValidationError):
        Outcome(id="x", label="x", custodian="", unit="u")
