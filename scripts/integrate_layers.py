#!/usr/bin/env python3
"""Are "use", "necessity" and "consequence" one thing or three?

The project accumulated four separate quantifications of importance and never put
them in one table. This does, on the 150 coded rows, where all of them are
computable at once:

  consequence       direct impact: the sum of a row's coded effects on 18 outcome
                    domains -- what it did to the world
  breadth           how many of the 18 domains it touches at all
  peak              its largest single effect
  necessity         transitive reach in the prerequisite graph
  downstream_share  the fraction of its total propagated effect that is mediated

Plus the structure results (effective rank, retained dimensions), the coupling
nulls, and the retracted option-value and inconclusive tensor results, so the whole
apparatus appears in one place rather than only in the sections that retired it.

The output is a rank-correlation matrix and a verdict. If the measures correlate
near 1.0 they are one quantity with four names and the paper should say so; if they
do not, "importance" is several quantities and any single ranking is a choice.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from world_impact.pipeline import SEED, run_analysis

ROOT = Path(__file__).resolve().parents[1]
QUICK = {
    "smaa_draws": 2000,
    "null_iterations": 40,
    "pa_iterations": 100,
    "tensor_null_iterations": 10,
    "screen_trajectories": 5,
    "screen_targets": 1,
}

MEASURES = ("consequence", "breadth", "peak", "necessity", "downstream_share")


def build(analysis: dict) -> dict[str, np.ndarray]:
    """One array per measure, aligned by the linkage ranking's own row order."""
    linkage = analysis["linkage"]
    ranked = sorted(linkage["ranked_by_reach"], key=lambda row: row["index"])
    ranking = analysis["ranking"]
    totals = dict(zip(ranking["names"], ranking["totals"], strict=True))
    breadth = dict(zip(ranking["names"], ranking["breadth"], strict=True))
    peak = dict(zip(ranking["names"], ranking["peak"], strict=True))

    out: dict[str, list[float]] = {name: [] for name in MEASURES}
    for row in ranked:
        name = row["name"]
        out["consequence"].append(float(totals.get(name, row["direct"])))
        out["breadth"].append(float(breadth.get(name, 0)))
        out["peak"].append(float(peak.get(name, 0)))
        out["necessity"].append(float(row["transitive_reach"]))
        out["downstream_share"].append(float(row["downstream_share"]))
    return {name: np.array(values, dtype=float) for name, values in out.items()}


def spearman(left: np.ndarray, right: np.ndarray) -> float:
    a = np.argsort(np.argsort(left)).astype(float)
    b = np.argsort(np.argsort(right)).astype(float)
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "integration.json")
    args = parser.parse_args()

    analysis = run_analysis(seed=SEED, reference_panel=False, **QUICK)
    measures = build(analysis)

    print(f"n rows: {len(next(iter(measures.values())))}")
    print("\nRANK-CORRELATION MATRIX (Spearman)")
    width = max(len(name) for name in MEASURES) + 2
    print(" " * width + "".join(f"{name[:9]:>11}" for name in MEASURES))
    matrix: dict[str, dict[str, float]] = {}
    for a in MEASURES:
        matrix[a] = {}
        cells = []
        for b in MEASURES:
            value = spearman(measures[a], measures[b])
            matrix[a][b] = value
            cells.append(f"{value:>11.2f}")
        print(f"{a:<{width}}" + "".join(cells))

    off = [
        abs(matrix[a][b])
        for i, a in enumerate(MEASURES)
        for b in MEASURES[i + 1 :]
        if not np.isnan(matrix[a][b])
    ]
    mean_off, max_off = float(np.mean(off)), float(np.max(off))
    print(f"\nmean |r| off the diagonal: {mean_off:.3f}   max {max_off:.3f}")

    structure = analysis["structure"]
    verdict = (
        f"{len(MEASURES)} measures of importance, mean |rank correlation| "
        f"{mean_off:.2f}, maximum {max_off:.2f}. "
        + (
            "They are distinguishable quantities: no ranking of these rows is *the* "
            "ranking of importance, it is a ranking of whichever quantity was chosen."
            if mean_off < 0.5
            else "The measures are largely one quantity and should be reported as one."
        )
    )
    print("VERDICT:", verdict)
    print(
        "\nstructure: effective rank {:.2f}, retained {} (95th pct) / {} (median), "
        "{} above the MP floor".format(
            structure["effective_rank"],
            structure["n_retained_pa95"],
            structure["n_retained_pa50"],
            structure["n_above_noise_floor"],
        )
    )
    nulls = analysis["nulls"]
    print(
        "nulls: coupling {:.3f} vs row-shuffle p={:.4f}, margin-preserving swap p={:.4f}".format(
            nulls["observed_coupling"],
            nulls["row_shuffle"]["p_value"],
            nulls["swap_null"]["p_value"],
        )
    )
    print(
        "tensor: interaction share {:.3f} vs era-shuffled null {:.3f}, p={:.3f} "
        "(inconclusive, abandoned)".format(
            analysis["tensor"]["interaction_share"],
            analysis["tensor"]["interaction_null_mean"],
            analysis["tensor"]["interaction_p_value"],
        )
    )
    option = analysis["option_value"]["null"]
    print(
        "option value: p={:.3f} against a degree-preserving rewiring null "
        "(retracted; the concept survives, the ranking does not)".format(option["p_value"])
    )
    print("linkage verdict:", analysis["linkage"]["verdict"][:170])

    ranking = analysis["ranking"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "n": len(next(iter(measures.values()))),
                "measures": list(MEASURES),
                "rank_correlation": matrix,
                "mean_abs_off_diagonal": mean_off,
                "max_abs_off_diagonal": max_off,
                "verdict": verdict,
                "effective_rank": structure["effective_rank"],
                "n_above_noise_floor": structure["n_above_noise_floor"],
                "coupling": nulls["observed_coupling"],
                "coupling_p_rowshuffle": nulls["row_shuffle"]["p_value"],
                "coupling_p_swap": nulls["swap_null"]["p_value"],
                "tensor_p": analysis["tensor"]["interaction_p_value"],
                "option_value_p": option["p_value"],
                "top_by_consequence": [
                    (name, float(value))
                    for name, value in sorted(
                        zip(ranking["names"], measures["consequence"], strict=True),
                        key=lambda pair: -pair[1],
                    )[:12]
                ],
                "top_by_necessity": [
                    (row["name"], int(row["transitive_reach"]))
                    for row in analysis["linkage"]["ranked_by_reach"][:12]
                ],
                "top_by_breadth": [
                    (name, float(value))
                    for name, value in sorted(
                        zip(ranking["names"], measures["breadth"], strict=True),
                        key=lambda pair: -pair[1],
                    )[:12]
                ],
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
