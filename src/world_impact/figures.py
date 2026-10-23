"""Figures. Deterministic SVG, no interactive backend, no styling libraries.

Every figure is a pure function of the analysis output, so a figure cannot
disagree with the numbers it illustrates. Font sizes are held at or above the
10 pt floor used by the vault's SVG linter, so these drop into a written report
without a second pass.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update(
    {
        "figure.dpi": 110,
        "savefig.dpi": 110,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.fonttype": "none",
    }
)
FLOOR = 10.0


def _save(fig: plt.Figure, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)
    return path


def scree(
    eigenvalues: np.ndarray,
    threshold: np.ndarray,
    noise_floor: float,
    path: Path,
    title: str = "Outcome-space spectrum against two nulls",
) -> Path:
    """Scree plot with the parallel-analysis threshold and the MP floor."""
    index = np.arange(1, eigenvalues.size + 1)
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    ax.plot(index, eigenvalues, marker="o", label="observed")
    ax.plot(index, threshold, marker="s", linestyle="--", label="parallel analysis (95th pct)")
    ax.axhline(noise_floor, color="crimson", linestyle=":", label="Marchenko-Pastur floor")
    ax.set_xlabel("component")
    ax.set_ylabel("eigenvalue")
    ax.set_title(title)
    ax.set_xticks(index)
    ax.legend(loc="upper right")
    return _save(fig, path)


def loadings_heatmap(
    rotated: np.ndarray, labels: tuple[str, ...], n_components: int, path: Path
) -> Path:
    """Rotated loadings, outcomes x retained components."""
    block = rotated[:, :n_components]
    fig, ax = plt.subplots(figsize=(1.1 * n_components + 3.0, 0.34 * len(labels) + 1.6))
    limit = float(np.abs(block).max()) or 1.0
    image = ax.imshow(block, cmap="RdBu_r", vmin=-limit, vmax=limit, aspect="auto")
    ax.set_xticks(range(n_components))
    ax.set_xticklabels([f"PC{i + 1}" for i in range(n_components)])
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    for row in range(block.shape[0]):
        for column in range(block.shape[1]):
            value = block[row, column]
            if abs(value) >= 0.15:
                ax.text(
                    column,
                    row,
                    f"{value:+.2f}",
                    ha="center",
                    va="center",
                    fontsize=FLOOR - 1,
                    color="white" if abs(value) > 0.6 * limit else "black",
                )
    fig.colorbar(image, ax=ax, shrink=0.7, label="loading")
    ax.set_title("Rotated loadings (varimax)")
    return _save(fig, path)


def rank_acceptability(
    rank_acceptability: np.ndarray,
    names: tuple[str, ...],
    order: list[int],
    path: Path,
    top: int = 20,
) -> Path:
    """Heatmap of P(development at rank) for the top developments."""
    selected = order[:top]
    block = rank_acceptability[selected, :top]
    fig, ax = plt.subplots(figsize=(7.5, 0.34 * len(selected) + 1.8))
    image = ax.imshow(block, cmap="viridis", aspect="auto", vmin=0.0)
    ax.set_xticks(range(top))
    ax.set_xticklabels([str(i + 1) for i in range(top)])
    ax.set_yticks(range(len(selected)))
    ax.set_yticklabels([names[i][:44] for i in selected])
    ax.set_xlabel("rank")
    ax.set_title("SMAA rank acceptability index")
    fig.colorbar(image, ax=ax, shrink=0.7, label="probability")
    return _save(fig, path)


def impact_breadth(
    totals: np.ndarray,
    breadth: np.ndarray,
    names: tuple[str, ...],
    frontier: np.ndarray,
    path: Path,
    annotate: int = 12,
) -> Path:
    """Impact against breadth, with the Pareto frontier marked."""
    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    ax.scatter(breadth[~frontier], totals[~frontier], s=28, color="#8aa0b4", label="dominated")
    ax.scatter(breadth[frontier], totals[frontier], s=52, color="#c0392b", label="Pareto frontier")
    for index in np.argsort(-totals)[:annotate]:
        ax.annotate(
            names[index][:30],
            (breadth[index], totals[index]),
            textcoords="offset points",
            xytext=(4, 3),
            fontsize=FLOOR - 1,
        )
    ax.set_xlabel("outcome domains touched (breadth)")
    ax.set_ylabel("sum of magnitudes (impact)")
    ax.set_title("Two scalarisations; only the frontier survives both")
    ax.legend(loc="lower right")
    return _save(fig, path)


def pervasiveness_bar(values: np.ndarray, labels: tuple[str, ...], path: Path, title: str) -> Path:
    """Horizontal bar chart of per-outcome pervasiveness."""
    order = np.argsort(values)
    fig, ax = plt.subplots(figsize=(7.5, 0.32 * len(labels) + 1.6))
    ax.barh(range(len(labels)), values[order], color="#2c6e8f")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels([labels[i] for i in order])
    ax.set_title(title)
    return _save(fig, path)


def field_flow_heatmap(
    flow: dict[str, Any], path: Path, title: str = "Field-to-field citation flow"
) -> Path:
    """Rows cite columns. Diagonal dominates, which is itself the finding."""
    names = [name[:26] for name in flow["fields"]]
    matrix = np.asarray(flow["matrix"], dtype=float)
    if matrix.size == 0:
        raise ValueError("empty flow matrix")
    normalised = matrix / np.maximum(matrix.sum(axis=1, keepdims=True), 1.0)
    fig, ax = plt.subplots(figsize=(0.34 * len(names) + 3.0, 0.34 * len(names) + 2.6))
    image = ax.imshow(normalised, cmap="magma", vmin=0.0)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=90, fontsize=FLOOR - 2)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=FLOOR - 2)
    ax.set_xlabel("cited field")
    ax.set_ylabel("citing field")
    ax.set_title(title)
    fig.colorbar(image, ax=ax, shrink=0.6, label="share of the citing field's references")
    return _save(fig, path)


def field_supply(
    upstream: dict[str, dict[str, float]],
    path: Path,
    title: str = "Net citation exporters and importers",
    limit: int = 12,
) -> Path:
    """Horizontal bars of the incoming/outgoing citation ratio, both extremes."""
    rows = sorted(
        (
            (name, stats["ratio"], stats["incoming"], stats["outgoing"])
            for name, stats in upstream.items()
        ),
        key=lambda row: -row[1],
    )
    selected = rows[:limit] + rows[-limit:]
    fig, ax = plt.subplots(figsize=(8.0, 0.32 * len(selected) + 1.8))
    values = [row[1] for row in selected]
    colours = ["#1f6f8b" if value >= 1.0 else "#b0413e" for value in values]
    ax.barh(range(len(selected)), values, color=colours)
    ax.axvline(1.0, color="black", linestyle=":", linewidth=1.0)
    ax.set_yticks(range(len(selected)))
    ax.set_yticklabels([row[0][:40] for row in selected], fontsize=FLOOR - 1)
    ax.invert_yaxis()
    ax.set_xlabel("incoming / outgoing citation flow  (>1 = net supplier)")
    ax.set_title(title)
    return _save(fig, path)


def corpus_timeline(
    seeds: list[dict[str, Any]],
    path: Path,
    classify: Any,
    title: str = "Top-cited works by year: the corpus as a timeline",
) -> Path:
    """One point per work, x = year, y = citations (log), coloured by class.

    This is the automated equivalent of a hand-built timeline: the lanes are the
    three title classes, so the reader can see at a glance when methodological
    infrastructure came to dominate the most-cited literature.
    """
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    palette = {"method": "#1f6f8b", "theory": "#b0413e", "unclassified": "#8aa0b4"}
    for label, colour in palette.items():
        subset = [
            work
            for work in seeds
            if classify(work.get("title") or "") == label and work.get("year")
        ]
        if not subset:
            continue
        ax.scatter(
            [work["year"] for work in subset],
            [max(work.get("cited_by_count") or 1, 1) for work in subset],
            s=16,
            alpha=0.65,
            color=colour,
            label=f"{label} ({len(subset)})",
        )
    ax.set_yscale("log")
    ax.set_xlabel("publication year")
    ax.set_ylabel("citations (log scale)")
    ax.set_title(title)
    ax.legend(loc="upper left", title="title classification")
    return _save(fig, path)


def timeline_lanes(
    items: list[dict[str, Any]],
    path: Path,
    lane_key: str = "field",
    title: str = "Multi-field timeline",
    max_lanes: int = 12,
    max_items_per_lane: int = 6,
) -> Path:
    """The Information-Revolution visual grammar, generated from data.

    Lanes are categories; each lane gets a horizontal rule with its most
    important items placed at their date and labelled. Produced by a function
    rather than drawn, so the same figure can be regenerated for any subset of
    the corpus -- which is the point of automating it.
    """
    lanes: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        if not item.get("year"):
            continue
        lanes.setdefault(str(item.get(lane_key) or "unknown"), []).append(item)
    ranked = sorted(lanes.items(), key=lambda pair: -len(pair[1]))[:max_lanes]
    fig, ax = plt.subplots(figsize=(11.0, 0.62 * len(ranked) + 2.0))
    for row, (_lane, members) in enumerate(ranked):
        members = sorted(members, key=lambda work: -(work.get("cited_by_count") or 0))
        members = sorted(members[:max_items_per_lane], key=lambda work: work["year"] or 0)
        years = [work["year"] for work in members]
        if not years:
            continue
        ax.hlines(row, min(years), max(years), color="#c8d3dd", linewidth=2.0, zorder=1)
        ax.scatter(years, [row] * len(years), s=42, color="#1f6f8b", zorder=2)
        for index, work in enumerate(members):
            offset = 0.22 if index % 2 == 0 else -0.34
            ax.annotate(
                (work.get("title") or "")[:34],
                (work["year"], row),
                textcoords="offset points",
                xytext=(0, 14 if offset > 0 else -16),
                fontsize=FLOOR - 2,
                ha="center",
                color="#33414d",
            )
    ax.set_yticks(range(len(ranked)))
    ax.set_yticklabels([lane[:34] for lane, _ in ranked], fontsize=FLOOR - 1)
    ax.invert_yaxis()
    ax.set_xlabel("year")
    ax.set_title(title)
    ax.grid(axis="x", linestyle=":", alpha=0.35)
    return _save(fig, path)


def consensus_atlas(
    rows: list[dict[str, Any]],
    consensus: list[dict[str, Any]],
    path: Path,
    label_top: int = 12,
    title: str = "The atlas: 520 most-cited works, by year and citation intensity",
) -> Path:
    """Year against citations-per-year, with the consensus items named.

    The x axis is time, the y axis is how intensively the work is still used, so
    the vertical axis is the age-corrected importance measure. Grey is everything;
    the named points are the works every criterion agrees on.
    """
    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    ax.scatter(
        [row["year"] for row in rows],
        [max(row["rate"], 1.0) for row in rows],
        s=13,
        color="#c3ced8",
        alpha=0.8,
        label=f"all seeds (n={len(rows)})",
    )
    top = consensus[:label_top]
    ax.scatter(
        [row["year"] for row in top],
        [max(row["rate"], 1.0) for row in top],
        s=70,
        color="#b0413e",
        zorder=3,
        label=f"consensus top {label_top}",
    )
    for index, row in enumerate(top):
        ax.annotate(
            (row["title"] or "")[:38],
            (row["year"], max(row["rate"], 1.0)),
            textcoords="offset points",
            xytext=(6, 6 if index % 2 == 0 else -12),
            fontsize=FLOOR - 1,
            color="#3a2a2a",
        )
    ax.set_yscale("log")
    ax.set_xlabel("publication year")
    ax.set_ylabel("citations per year since publication (log scale)")
    ax.set_title(title)
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle=":", alpha=0.3)
    return _save(fig, path)


def criterion_agreement(
    agreement: dict[tuple[str, str], float],
    labels: dict[str, str],
    path: Path,
    title: str = "Do the criteria agree? Spearman correlation between rank orders",
) -> Path:
    """Annotated heatmap of the rank-correlation matrix between criteria.

    ``keys`` is intersected with the agreement matrix rather than taken from
    ``labels`` directly: dropped criteria (degenerate or uncovered) have no entry in
    the matrix, and the earlier version raised ``KeyError: ('citations',
    'top_citations')`` when the criterion set changed. A figure should show the
    criteria that actually ranked, and should not be able to crash on a criterion
    that did not.
    """
    keys = [key for key in labels if (key, key) in agreement]
    matrix = np.array([[agreement[(a, b)] for b in keys] for a in keys])
    fig, ax = plt.subplots(figsize=(1.7 * len(keys) + 2.6, 1.5 * len(keys) + 2.0))
    image = ax.imshow(matrix, cmap="RdBu_r", vmin=-1.0, vmax=1.0)
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels([labels[k] for k in keys], rotation=30, ha="right", fontsize=FLOOR - 1)
    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels([labels[k] for k in keys], fontsize=FLOOR - 1)
    for i in range(len(keys)):
        for j in range(len(keys)):
            ax.text(
                j,
                i,
                f"{matrix[i, j]:.2f}",
                ha="center",
                va="center",
                fontsize=FLOOR,
                color="white" if abs(matrix[i, j]) > 0.6 else "black",
            )
    fig.colorbar(image, ax=ax, shrink=0.7, label="rank correlation")
    ax.set_title(title)
    return _save(fig, path)


def decade_intensity(
    trend: list[dict[str, Any]],
    path: Path,
    title: str = "Citation intensity by publication decade",
) -> Path:
    """Median citations per year for the seeds of each decade."""
    decades = [row["decade"] for row in trend]
    medians = [row["median_rate"] for row in trend]
    maxima = [row["max_rate"] for row in trend]
    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    ax.plot(decades, medians, marker="o", label="median citations/year")
    ax.plot(decades, maxima, marker="s", linestyle="--", label="maximum citations/year")
    ax.set_yscale("log")
    ax.set_xlabel("publication decade")
    ax.set_ylabel("citations per year (log scale)")
    ax.set_title(title)
    ax.legend(loc="upper left")
    ax.grid(linestyle=":", alpha=0.3)
    return _save(fig, path)


def necessity_contrast(
    by_use: list[tuple[str, float]],
    by_necessity: list[tuple[str, float]],
    path: Path,
    title: str = "Two instruments, two answers",
) -> Path:
    """The same question answered by in-degree and by transitive in-degree.

    Left panel ranks by how many works *use* something (citation count); right
    panel ranks by how many works *depend* on it (transitive reach in the
    dependency graph). The point of the figure is that the two lists do not
    overlap at all: no work appears in both, and no label can be moved from one
    panel to the other without changing which question is being asked.
    """
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6))
    for ax, rows, colour, caption, unit in (
        (axes[0], by_use, "#b45309", "by use", "citations"),
        (axes[1], by_necessity, "#1d4ed8", "by necessity", "dependants"),
    ):
        labels = [_shorten(name, 40) for name, _ in rows][::-1]
        values = [value for _, value in rows][::-1]
        positions = np.arange(len(rows))
        ax.barh(positions, values, color=colour, alpha=0.85)
        ax.set_yticks(positions)
        ax.set_yticklabels(labels)
        ax.set_xlabel(unit)
        ax.set_title(caption)
        # A log-free x-axis with the value printed at the bar end: the two panels
        # differ by three orders of magnitude, so a shared scale would flatten one.
        span = max(values) if values else 1.0
        for position, value in zip(positions, values, strict=True):
            ax.text(
                value + span * 0.02,
                position,
                f"{value:,.0f}",
                va="center",
                fontsize=9,
            )
        ax.set_xlim(0, span * 1.22)
    fig.suptitle(title, fontsize=12)
    return _save(fig, path)


def _shorten(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "\u2026"


def test_information(fit: Any, path: Path) -> Path:
    """The instrument's resolving power, and where it collapses."""
    grid = np.linspace(-3.0, 3.0, 121)
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    ax.plot(grid, fit.test_information(grid))
    ax.axvline(
        fit.top_theta(0.9), color="crimson", linestyle=":", label="top decile of developments"
    )
    ax.set_xlabel(r"latent impact $\theta$")
    ax.set_ylabel("test information")
    ax.set_title("Graded-response test information: the ceiling is visible")
    ax.legend(loc="upper right")
    return _save(fig, path)
