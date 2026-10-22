"""Typed schema for the coding protocol.

The schema *is* the protocol: if a rule matters it is a validator here, not a
paragraph in a methods section. Loading the data is therefore also a
methodological check.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAGNITUDE_MIN = 1
MAGNITUDE_MAX = 3


class Era(StrEnum):
    """Long-run periodisation. Ordering is authoritative; the validator only
    checks that era and onset do not contradict each other."""

    deep_prehistory = "deep_prehistory"
    antiquity = "antiquity"
    medieval = "medieval"
    early_modern = "early_modern"
    industrial = "industrial"
    contemporary = "contemporary"


ERA_ORDER: tuple[Era, ...] = (
    Era.deep_prehistory,
    Era.antiquity,
    Era.medieval,
    Era.early_modern,
    Era.industrial,
    Era.contemporary,
)
ERA_LABEL: dict[Era, str] = {
    Era.deep_prehistory: "deep prehistory",
    Era.antiquity: "antiquity",
    Era.medieval: "medieval",
    Era.early_modern: "early modern",
    Era.industrial: "industrial",
    Era.contemporary: "contemporary",
}
# Tolerance for the era/onset consistency check, in years. Periodisation is a
# convention, so we require non-contradiction rather than agreement.
ERA_TOLERANCE_YEARS = 150


class SeshatGroup(StrEnum):
    """External taxonomy, from the Seshat Global History Databank's published
    variable groups (Turchin et al. 2015). Used only for the inter-framework
    reliability check, never to build the axes."""

    population = "population"
    agriculture = "agriculture"
    warfare = "warfare"
    governance = "governance"
    religion = "religion"
    economy = "economy"
    social_complexity = "social_complexity"
    infrastructure = "infrastructure"
    information = "information"


class Outcome(BaseModel):
    """A column of the impact matrix."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    custodian: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    owid_candidates: list[str] = Field(default_factory=list)


class Source(BaseModel):
    """A bibliography entry."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1)
    author: str = Field(min_length=1)
    year: int
    title: str = Field(min_length=1)
    kind: str = Field(pattern=r"^(book|article|dataset|report)$")
    venue: str | None = None
    publisher: str | None = None
    volume: str | None = None
    doi: str | None = None
    note: str | None = None
    verified: bool = False

    @model_validator(mode="after")
    def _has_container(self) -> Source:
        if not (self.venue or self.publisher):
            raise ValueError(f"{self.key}: needs either venue or publisher")
        return self


class Development(BaseModel):
    """A row of the impact matrix: one datable intervention."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    onset: int
    era: Era
    extern: list[SeshatGroup] = Field(min_length=1)
    sources: list[str] = Field(min_length=1)
    effects: dict[str, int] = Field(min_length=1)
    knowledge_layer: bool = False
    """True for developments whose primary product is *understanding* rather than
    a deployable capability (mathematics, mechanics, thermodynamics,
    electromagnetism, quantum theory, statistics).

    This flag is used for exactly one purpose: to read the seed hypothesis off the
    analysis instead of asserting it. It never enters the axes, the weights or the
    impact scores, so marking a development here cannot inflate its rank. See
    :mod:`world_impact.linkage`.
    """

    @model_validator(mode="after")
    def _check(self) -> Development:
        for outcome_id, magnitude in self.effects.items():
            if not MAGNITUDE_MIN <= magnitude <= MAGNITUDE_MAX:
                raise ValueError(
                    f"{self.id}/{outcome_id}: magnitude {magnitude} outside "
                    f"[{MAGNITUDE_MIN}, {MAGNITUDE_MAX}]"
                )
        if len(set(self.sources)) != len(self.sources):
            raise ValueError(f"{self.id}: duplicate source keys")
        if len(set(self.extern)) != len(self.extern):
            raise ValueError(f"{self.id}: duplicate external groups")
        return self

    @property
    def total(self) -> int:
        """Sum of magnitudes. The 'impact' scalarisation, nothing more."""
        return sum(self.effects.values())

    @property
    def breadth(self) -> int:
        """Number of outcome domains touched. The rubric-free scalarisation."""
        return len(self.effects)

    @property
    def peak(self) -> int:
        return max(self.effects.values())
