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
