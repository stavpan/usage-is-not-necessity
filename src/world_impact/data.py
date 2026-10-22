"""Loading, cross-validation and array construction.

All array construction happens in exactly one place so that the ordering of
rows and columns is never re-derived ad hoc (the bug that silently corrupted
the first draft's clustering).
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from world_impact.schema import (
    ERA_LABEL,
    ERA_ORDER,
    ERA_TOLERANCE_YEARS,
    Development,
    Outcome,
    SeshatGroup,
    Source,
)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _read_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@dataclass(frozen=True)
class Dataset:
    """A validated coding matrix and everything needed to interpret it."""

    outcomes: tuple[Outcome, ...]
    developments: tuple[Development, ...]
    sources: dict[str, Source]
    edges: tuple[tuple[str, str], ...] = ()
    """``(user, provider)`` pairs: the user depended on the provider. Loaded from
    ``data/edges.yml``. Used only by :mod:`world_impact.linkage`."""

    def knowledge_mask(self) -> np.ndarray:
        """Boolean mask of developments flagged as knowledge-layer."""
        return np.array([d.knowledge_layer for d in self.developments], dtype=bool)

    @property
    def n_developments(self) -> int:
        return len(self.developments)

    @property
    def n_outcomes(self) -> int:
        return len(self.outcomes)

    @property
    def outcome_ids(self) -> tuple[str, ...]:
        return tuple(o.id for o in self.outcomes)

    @property
    def outcome_labels(self) -> tuple[str, ...]:
        return tuple(o.label for o in self.outcomes)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(d.name for d in self.developments)

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(d.id for d in self.developments)

    def matrix(self, dtype: type = float) -> np.ndarray:
        """(n_developments, n_outcomes) magnitude matrix, zeros where absent."""
        index = {o: j for j, o in enumerate(self.outcome_ids)}
        out: np.ndarray = np.zeros((self.n_developments, self.n_outcomes), dtype=dtype)
        for i, dev in enumerate(self.developments):
            for outcome_id, magnitude in dev.effects.items():
                out[i, index[outcome_id]] = magnitude
        return out

    def binary(self) -> np.ndarray:
        """Presence only: the scalarisation that ignores the rubric entirely."""
        return (self.matrix() > 0).astype(float)

    def era_index(self) -> np.ndarray:
        order = {e: i for i, e in enumerate(ERA_ORDER)}
        return np.array([order[d.era] for d in self.developments], dtype=int)

    def era_labels(self) -> tuple[str, ...]:
        return tuple(ERA_LABEL[e] for e in ERA_ORDER)

    def external_labels(self) -> tuple[str, ...]:
        """Primary Seshat group per development (first listed)."""
        return tuple(d.extern[0].value for d in self.developments)

    def tensor(self) -> np.ndarray:
        """(n_developments, n_outcomes, n_eras) incidence tensor.

        This is the object the matrix is a collapse of. The matrix loses every
        era-specific interaction; see :mod:`world_impact.tensor`.
        """
        matrix = self.matrix()
        eras = self.era_index()
        out = np.zeros((self.n_developments, self.n_outcomes, len(ERA_ORDER)))
        for i in range(self.n_developments):
            out[i, :, eras[i]] = matrix[i, :]
        return out

    def by_id(self, development_id: str) -> Development:
        for dev in self.developments:
            if dev.id == development_id:
                return dev
        raise KeyError(development_id)


LEVELS: dict[str, str] = {
    "developments": "developments.yml",
    "results": "results.yml",
}
"""The two resolutions the same instrument runs at.

``developments`` is coarse: whole disciplines and interventions
("electromagnetism", "coal and the steam engine"). ``results`` is fine: the
specific artefact or paper that did the work ("Maxwell's displacement current",
"Watt's separate condenser"). Same schema, same pipeline, same nulls -- which is
what makes the comparison between them meaningful rather than rhetorical.
"""


def load_dataset(
    data_dir: Path | str = DEFAULT_DATA_DIR,
    level: str = "developments",
) -> Dataset:
    """Load and validate the coding matrix at one resolution.

    Parameters
    ----------
    level
        ``"developments"`` (coarse) or ``"results"`` (fine).

    Raises
    ------
    ValueError
        If any cross-file rule is violated: unknown outcome id, undeclared
        source key, duplicate id, an era/onset contradiction, an unknown
        prerequisite, or an unknown coarse parent.
    """
    if level not in LEVELS:
        raise ValueError(f"unknown level {level!r}; expected one of {sorted(LEVELS)}")
    root = Path(data_dir)
    outcomes = tuple(Outcome(**row) for row in _read_yaml(root / "outcomes.yml"))
    developments = tuple(Development(**row) for row in _read_yaml(root / LEVELS[level]))
    sources = {row["key"]: Source(**row) for row in _read_yaml(root / "sources.yml")}

    # Edges. The coarse layer keeps its graph in a separate file because the
    # edges there are a research artefact in their own right; the fine layer
    # carries prerequisites inline, so that each result's dependency claim sits
    # next to the result. Mixing the two would let a fine row silently inherit a
    # coarse edge, which is exactly the coupling the granularity analysis needs
    # to be able to measure.
    inline = tuple((d.id, provider) for d in developments for provider in d.requires)
    if level == "developments":
        edges_path = root / "edges.yml"
        declared = (
            tuple((row["user"], row["provider"]) for row in (_read_yaml(edges_path) or []))
            if edges_path.exists()
            else ()
        )
        edges = declared + inline
    else:
        edges = inline

    coarse_ids = None
    if level == "results":
        coarse_path = root / LEVELS["developments"]
        coarse_ids = {row["id"] for row in _read_yaml(coarse_path)}

    problems = check(outcomes, developments, sources, coarse_ids=coarse_ids)
    problems.extend(check_edges(developments, edges))
    if problems:
        raise ValueError("coding matrix failed validation:\n  - " + "\n  - ".join(problems))
    return Dataset(outcomes=outcomes, developments=developments, sources=sources, edges=edges)


def check_edges(
    developments: tuple[Development, ...], edges: tuple[tuple[str, str], ...]
) -> list[str]:
    """Violations in the enabling graph.

    Duplicate edges are rejected rather than silently collapsed, self-loops are
    impossible in a DAG, and a cycle is reported with the cycle itself so it can
    be inspected -- cycles are not forbidden (science and craft genuinely feed
    each other) but they must be *deliberate*, and a leaky inverse is a real
    hazard. See :mod:`world_impact.linkage`.
    """
    problems: list[str] = []
    ids = {d.id for d in developments}
    seen: set[tuple[str, str]] = set()
    for user, provider in edges:
        if user not in ids:
            problems.append(f"edge references unknown development: {user}")
        if provider not in ids:
            problems.append(f"edge references unknown development: {provider}")
        if user == provider:
            problems.append(f"self-loop in enabling graph: {user}")
        if (user, provider) in seen:
            problems.append(f"duplicate edge: {user} -> {provider}")
        seen.add((user, provider))

    order = {d.id: i for i, d in enumerate(developments)}
    graph: dict[str, list[str]] = {d.id: [] for d in developments}
    for user, provider in edges:
        if user in graph and provider in graph:
            graph[user].append(provider)

    state: dict[str, int] = {d.id: 0 for d in developments}
    cycle: list[str] = []

    def visit(node: str, path: list[str]) -> bool:
        if state[node] == 1:
            cycle.extend([*path[path.index(node) :], node])
            return True
        if state[node] == 2:
            return False
        state[node] = 1
        for neighbour in graph[node]:
            if visit(neighbour, [*path, node]):
                return True
        state[node] = 2
        return False

    for node in sorted(graph, key=lambda n: order[n]):
        if state[node] == 0 and visit(node, []):
            break
    if cycle:
        problems.append(
            "enabling graph contains a cycle (allowed only if deliberate; the "
            "propagation matrix may be ill-conditioned): " + " -> ".join(cycle)
        )
    return problems


def check(
    outcomes: tuple[Outcome, ...],
    developments: tuple[Development, ...],
    sources: dict[str, Source],
    coarse_ids: set[str] | None = None,
) -> list[str]:
    """Return a list of cross-file violations (empty means valid).

    ``coarse_ids`` is supplied when validating the fine layer, so that every fine
    row can be checked against the coarse row it claims to refine. Without it, a
    typo in ``parent`` would silently drop a result out of the granularity
    analysis rather than failing the build.
    """
    problems: list[str] = []

    for name, seq in (("outcome", outcomes), ("development", developments)):
        seen: set[str] = set()
        for item in seq:
            if item.id in seen:
                problems.append(f"duplicate {name} id: {item.id}")
            seen.add(item.id)

    outcome_ids = {o.id for o in outcomes}
    ids = {d.id for d in developments}
    for dev in developments:
        unknown = sorted(set(dev.effects) - outcome_ids)
        if unknown:
            problems.append(f"{dev.id}: unknown outcome ids {unknown}")
        missing = sorted(set(dev.sources) - set(sources))
        if missing:
            problems.append(f"{dev.id}: undeclared source keys {missing}")

        # Same-resolution prerequisites. Cross-resolution coupling goes through
        # ``parent``, never through ``requires``, so a fine row cannot quietly
        # inherit a coarse dependency.
        unknown_requires = sorted(set(dev.requires) - ids)
        if unknown_requires:
            problems.append(f"{dev.id}: unknown prerequisites {unknown_requires}")
        if dev.id in dev.requires:
            problems.append(f"{dev.id}: requires itself")
        if len(set(dev.requires)) != len(dev.requires):
            problems.append(f"{dev.id}: duplicate prerequisites")

        if dev.parent is not None:
            if coarse_ids is None:
                problems.append(f"{dev.id}: parent set but no coarse level supplied for checking")
            elif dev.parent not in coarse_ids:
                problems.append(f"{dev.id}: unknown coarse parent {dev.parent}")

    # Era/onset consistency: era medians must not decrease along era order.
    # Periodisation is a convention, so we forbid contradiction rather than
    # requiring agreement.
    order = {e: i for i, e in enumerate(ERA_ORDER)}
    grouped: dict[int, list[int]] = {}
    for dev in developments:
        grouped.setdefault(order[dev.era], []).append(dev.onset)
    medians = {k: float(np.median(v)) for k, v in grouped.items()}
    present = sorted(medians)
    for a, b in itertools.pairwise(present):
        if medians[b] - medians[a] < -ERA_TOLERANCE_YEARS:
            problems.append(
                f"era order contradicted by onset: {ERA_ORDER[a]} median "
                f"{medians[a]:.0f} vs {ERA_ORDER[b]} median {medians[b]:.0f}"
            )

    declared = set(SeshatGroup)
    for dev in developments:
        if not set(dev.extern) <= declared:
            problems.append(f"{dev.id}: unknown external group")

    return problems


def outcome_presence(dataset: Dataset) -> np.ndarray:
    """Number of developments touching each outcome domain."""
    return (dataset.matrix() > 0).sum(axis=0)
