"""Measured reference series: validation against the real world.

Everything in ``data/developments.yml`` is a *derived* judgement about
magnitudes. That is the largest threat to validity in the project, and the only
honest response is to compare the coded structure against something measured.

This module pulls long-run series for the outcome domains from Our World in
Data's public grapher endpoint (CC-BY) and asks two questions:

1. **Do the outcome domains co-move the way the coding says they do?** The
   measured cross-domain correlation structure can be compared with the coded
   co-impact grammar (RV coefficient / Procrustes on the first components).
   Agreement is evidence; disagreement is a finding.
2. **Are the domains separable at all?** If two outcome domains correlate at
   r > 0.95 across 60 years of measured data, then coding them as separate
   columns is a distinction without a difference.

The module degrades honestly: series that fail to resolve are recorded as
missing and the comparison runs on what remains, with the coverage reported
alongside. No imputation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

GRAPHER = "https://ourworldindata.org/grapher/{slug}.csv?v=1&csvType=full"
DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "data" / "raw" / "owid"


@dataclass
class ReferencePanel:
    """Wide (year x outcome) panel of world-aggregate series."""

    frame: pd.DataFrame
    resolved: dict[str, str]
    missing: dict[str, list[str]] = field(default_factory=dict)

    @property
    def outcomes(self) -> list[str]:
        return list(self.frame.columns)

    def correlation(self) -> pd.DataFrame:
        """Pairwise correlation over the overlapping years, listwise deleted."""
        return self.frame.corr(min_periods=10)


def fetch_series(
    slug: str,
    cache_dir: Path | str = DEFAULT_CACHE,
    entity: str = "World",
    timeout: float = 30.0,
) -> pd.DataFrame | None:
    """Download one grapher CSV (cached) and return a year-indexed frame."""
    import requests

    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{slug}.csv"
    if not path.exists():
        try:
            response = requests.get(GRAPHER.format(slug=slug), timeout=timeout)
        except requests.RequestException:
            return None
        if response.status_code != 200 or not response.content:
            return None
        path.write_bytes(response.content)
    try:
        frame = pd.read_csv(path)
    except (pd.errors.ParserError, UnicodeDecodeError):
        return None
    if "Entity" not in frame.columns or "Year" not in frame.columns:
        return None
    value_columns = [
        c
        for c in frame.columns
        if c not in {"Entity", "Code", "Year"} and "annotation" not in c.lower()
    ]
    if not value_columns:
        return None
    subset = frame[frame["Entity"] == entity]
    if subset.empty:
        subset = frame.groupby("Year")[value_columns].mean().reset_index()
    series = subset.set_index("Year")[value_columns[0]].astype(float)
    series = series[~series.index.duplicated(keep="last")].sort_index()
    return series.rename(slug).to_frame()


def build_panel(
    registry: list[tuple[str, list[str]]],
    cache_dir: Path | str = DEFAULT_CACHE,
    year_min: int = 1950,
    year_max: int = 2022,
) -> ReferencePanel:
    """Resolve candidate slugs for each outcome and assemble the panel.

    ``registry`` is a list of ``(outcome_id, [candidate slugs])``. The first
    candidate that resolves wins; all failures are recorded.
    """
    frames: dict[str, pd.Series] = {}
    resolved: dict[str, str] = {}
    missing: dict[str, list[str]] = {}
    for outcome_id, candidates in registry:
        for slug in candidates:
            series = fetch_series(slug, cache_dir=cache_dir)
            if series is None or series.empty:
                continue
            column = series.iloc[:, 0]
            window = column[(column.index >= year_min) & (column.index <= year_max)]
            if window.dropna().size < 10:
                continue
            frames[outcome_id] = window
            resolved[outcome_id] = slug
            break
        else:
            missing[outcome_id] = list(candidates)
    frame = pd.DataFrame(frames).sort_index()
    return ReferencePanel(frame=frame, resolved=resolved, missing=missing)


def rv_coefficient(a: np.ndarray, b: np.ndarray) -> float:
    """RV coefficient: multivariate generalisation of squared correlation.

    Used to compare the *coded* co-impact grammar with the *measured*
    cross-domain correlation structure. 1.0 means identical up to rotation and
    scale; 0 means orthogonal.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    numerator = float(np.trace(a @ b.T @ b @ a.T))
    denominator = float(np.sqrt(np.trace(a @ a.T) ** 2 * np.trace(b @ b.T) ** 2))
    return numerator / denominator if denominator > 0 else 0.0


def compare_structures(coded: np.ndarray, measured: np.ndarray) -> dict[str, float]:
    """Compare coded and measured co-impact grammars on shared domains.

    Both matrices are standardised to correlation-like form first, because the
    coded matrix is ordinal and the measured panel is in physical units.
    """
    coded = np.asarray(coded, dtype=float)
    measured = np.asarray(measured, dtype=float)
    if coded.shape[1] != measured.shape[1]:
        raise ValueError("coded and measured must cover the same outcome domains")
    coded_gram = _normalise(coded.T @ coded)
    measured_gram = _normalise(measured.T @ measured)
    return {
        "rv": rv_coefficient(coded_gram, measured_gram),
        "frobenius_distance": float(np.linalg.norm(coded_gram - measured_gram)),
    }


def _normalise(gram: np.ndarray) -> np.ndarray:
    scale = np.sqrt(np.clip(np.diag(gram), 1e-12, None))
    return gram / np.outer(scale, scale)
