"""Reporting: JSON for machines, markdown for humans, caveats in both.

The markdown report is generated, not written, so it cannot drift from the
numbers. It also carries the limitations section automatically, because the
limitations *are* a result: this instrument has a demonstrable ceiling, and the
report says so every time it is rendered.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def write_json(payload: dict, path: Path | str) -> Path:
    """Write results as pretty JSON, converting numpy scalars."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), indent=2), encoding="utf-8")
    return path


def _jsonable(value):
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def write_markdown(payload: dict, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(payload), encoding="utf-8")
    return path


def render(payload: dict) -> str:
    """Render the whole report. Long by nature; sections are appended in order."""
    lines: list[str] = []
    lines.extend(_header(payload))
    lines.extend(_section_axes(payload))
    lines.extend(_section_nulls(payload))
    lines.extend(_section_measurement(payload))
    lines.extend(_section_ranking(payload))
    lines.extend(_section_tensor(payload))
    lines.extend(_section_reference(payload))
    lines.extend(_section_sensitivity(payload))
    if "linkage" in payload:
        lines.extend(_section_linkage(payload["linkage"]))
    lines.extend(_section_limitations())
    return "\n".join(lines)


def _header(payload: dict) -> list[str]:
    meta = payload["meta"]
    return [
        "# world-impact: generated report\n",
        f"Coded matrix: **{meta['n_developments']} developments x "
        f"{meta['n_outcomes']} outcome domains**, {meta['n_cells']} nonzero cells "
        f"(density {meta['density']:.3f}). Seed `{meta['seed']}`. Every number below "
        "is reproduced by `pixi run all`.\n",
    ]


def _section_axes(payload: dict) -> list[str]:
    block = payload["structure"]
    lines = ["## 1. How many axes are there? (an output, not a setting)\n"]
    lines.append(
        "| criterion | value |\n|---|---|\n"
        f"| effective rank (participation ratio) | {block['effective_rank']:.2f} |\n"
        f"| parallel analysis, 95th pct (Glorfeld) | {block['n_retained_pa95']} |\n"
        f"| parallel analysis, median rule (Horn) | {block['n_retained_pa50']} |\n"
        f"| eigenvalues above the Marchenko-Pastur floor | {block['n_above_noise_floor']} |\n"
        "| best rank by out-of-sample prediction error | "
        f"{block['best_rank_by_prediction_error']} |\n"
        f"| stable rank | {block['stable_rank']:.2f} |\n"
    )
    lines.append(
        "**These criteria disagree, and the disagreement is the result.** The honest "
        "statement is a *range*: roughly "
        f"{block['n_above_noise_floor']}-{block['n_retained_pa50']} interpretable "
        "dimensions. 'History has exactly k dimensions' is a choice of criterion "
        "dressed as a finding.\n"
    )
    lines.append("### Derived components\n")
    for component in block["components"]:
        lines.append(
            f"**Component {component['index'] + 1}** ({component['share'] * 100:.1f}% of variance)"
        )
        for entry in component["top"]:
            lines.append(f"  - `{entry['loading']:+.2f}` {entry['outcome']}")
        lines.append("")
    lines.append(
        "Labels are read off the loadings **after a declared varimax rotation**. "
        "Rotation does not change the subspace; it changes which labels are "
        "defensible, which is why it is a stated parameter.\n"
    )
    return lines


def _section_nulls(payload: dict) -> list[str]:
    block = payload["nulls"]
    return [
        "## 2. Is the coupling real?\n",
        "| null | null mean | 95th pct | p |\n|---|---|---|---|\n"
        f"| row shuffle (row margins only) | {block['row_shuffle']['mean']:.3f} | "
        f"{block['row_shuffle']['p95']:.3f} | {block['row_shuffle']['p_value']:.4f} |\n"
        f"| margin-preserving swap | {block['swap_null']['mean']:.3f} | "
        f"{block['swap_null']['p95']:.3f} | {block['swap_null']['p_value']:.4f} |\n",
        f"Observed coupling statistic {block['observed_coupling']:.3f}; the swap null "
        f"realizes {block['swap_null']['realized_swaps']} swaps while holding both "
        "margins fixed, so a non-significant result would mean the apparent structure "
        "is a margin artifact.\n",
    ]


def _section_measurement(payload: dict) -> list[str]:
    block = payload["measurement"]
    return [
        "## 3. Measurement: the instrument's ceiling\n",
        f"- graded response model converged: `{block['converged']}`, "
        f"{block['n_parameters']} parameters\n"
        f"- posterior SD of latent impact: median {block['theta_sd_median']:.3f}\n"
        f"- test information at the top decile of developments: "
        f"**{block['saturation_ratio'] * 100:.1f}% of its peak**\n",
        "With four categories per item the instrument loses resolving power at the top "
        "of the scale. This is why the report makes no claim about acceleration: the "
        "rubric cannot distinguish 'transformed' from 'transformed enormously'.\n",
    ]


def _section_ranking(payload: dict) -> list[str]:
    block = payload["ranking"]
    names = block["names"]
    totals = np.asarray(block["totals"])
    breadth = np.asarray(block["breadth"])
    peak = np.asarray(block["peak"])
    frontier = np.asarray(block["frontier"], dtype=bool)
    acceptance = np.asarray(block["smaa"]["acceptance"])
    mean_rank = np.asarray(block["smaa"]["mean_rank"])
    confidence = np.asarray(block["smaa"]["confidence"])
    intervals = block["smaa"]["rank_interval_90"]
    nonsub = np.asarray(block["nonsubstitutability"])

    lines = ["## 4. Ranking\n", "### Pareto frontier (needs no weights at all)\n"]
    for index in np.flatnonzero(frontier):
        lines.append(
            f"- **{names[index]}** -- impact {totals[index]:.0f}, breadth "
            f"{breadth[index]:.0f}, peak {peak[index]:.0f}"
        )
    lines.append("")
    lines.append(
        f"Rubric robustness: Spearman between magnitude-weighted and presence-only "
        f"impact is **{block['rubric_spearman']:.3f}**, so the 0-3 assignment is not "
        "deciding the order. Column robustness: deleting any single outcome domain "
        f"moves the top-10 by Jaccard "
        f"{block['leave_one_out_columns']['min']:.2f}-"
        f"{block['leave_one_out_columns']['max']:.2f} "
        f"(median {block['leave_one_out_columns']['median']:.2f}).\n"
    )
    lines.append("### SMAA: rank acceptability over all legitimate weightings\n")
    lines.append(
        "| development | P(rank 1) | mean rank | 90% rank interval | confidence |\n"
        "|---|---|---|---|---|\n"
    )
    for index in np.argsort(-acceptance)[:15]:
        lines.append(
            f"| {names[index][:44]} | {acceptance[index]:.3f} | {mean_rank[index]:.2f} "
            f"| {intervals[index][0]}-{intervals[index][1]} | {confidence[index]:.2f} |\n"
        )
    lines.append(
        "\nRank acceptability is the probability of a rank across the simplex of "
        "outcome weights and across value draws from the measurement model. "
        "Confidence is the probability of ranking first under a local Dirichlet "
        "centred on that development's own central weight vector.\n"
    )
    lines.append("### Redundancy: how many timelines are there really?\n")
    for index in np.argsort(nonsub)[:6]:
        lines.append(f"- {names[index][:44]} (non-substitutability {nonsub[index]:.2f})")
    lines.append(
        "\nLow non-substitutability means another single development already has "
        "essentially this profile, so a separate timeline would duplicate it.\n"
    )
    return lines


def _section_tensor(payload: dict) -> list[str]:
    block = payload["tensor"]
    lines = [
        "## 5. Era structure (tensor)\n",
        f"Tucker ranks {block['ranks']}, energy retained "
        f"{block['energy_retained'] * 100:.1f}%. Interaction share (core energy off the "
        f"a=b=c diagonal) **{block['interaction_share']:.3f}** against an era-shuffled "
        f"null of {block['interaction_null_mean']:.3f} "
        f"(p = {block['interaction_p_value']:.3f}).\n",
        "| era | impact mass | developments coded | impact per development |\n|---|---|---|---|\n",
    ]
    for label, mass in block["mass_by_era"].items():
        count = block["count_by_era"][label]
        per = mass / count if count else 0.0
        lines.append(f"| {label} | {mass:.0f} | {count} | {per:.2f} |\n")
    lines.append(
        "\nThe 'developments coded' column is the honest baseline: eras with more "
        "entries win on mass for free. The rubric also saturates, so none of this "
        "supports an acceleration claim in either direction.\n"
    )
    return lines


def _section_reference(payload: dict) -> list[str]:
    block = payload.get("reference", {})
    lines = ["## 6. Validation against measured series\n"]
    if not block.get("available"):
        lines.append(
            f"Reference panel unavailable: {block.get('error', 'not requested')}. "
            "Run with network access to enable it.\n"
        )
        return lines
    comparison = block["comparison"]
    lines.append(
        f"Resolved {block['coverage']} outcome domains against Our World in Data "
        f"series over {block['years'][0]}-{block['years'][1]} "
        f"({block['n_years']} years).\n\n"
        f"- RV coefficient between the coded co-impact grammar and the measured "
        f"cross-domain correlation structure: **{comparison['rv']:.3f}**\n"
        f"- Frobenius distance between the two normalized grammars: "
        f"{comparison['frobenius_distance']:.3f}\n"
    )
    redundant = block["redundant_pairs_above_0.95"]
    if redundant:
        lines.append(
            f"- {len(redundant)} measured domain pair(s) correlate above 0.95, i.e. "
            "may not be separable columns:\n"
        )
        for pair in redundant[:8]:
            lines.append(f"  - {pair['a']} vs {pair['b']}: r = {pair['r']:.3f}\n")
    else:
        lines.append(
            "- no measured domain pair correlates above 0.95: the columns are "
            "separable in the data, not only in the coding.\n"
        )
    if block.get("missing"):
        lines.append(
            f"\nUnresolved domains (no series found; not imputed): {', '.join(block['missing'])}\n"
        )
    return lines


def _section_sensitivity(payload: dict) -> list[str]:
    lines = [
        "## 7. Which coding decisions drive the answer?\n",
        "Morris elementary-effects screening (SALib) on the rank of each top "
        "development, over all nonzero cell codings:\n",
    ]
    for development, screen in payload["sensitivity"].items():
        lines.append(f"**{development}** ({screen['n_evaluations']} evaluations)")
        for row in screen["top"][:6]:
            lines.append(
                f"  - {row['development'][:34]} / {row['outcome']}: "
                f"mu* {row['mu_star']:.2f}, sigma {row['sigma']:.2f}"
            )
        lines.append("")
    lines.append(
        "High mu* identifies the coding decisions a second coder should revisit "
        "first. High sigma indicates interaction, i.e. the effect depends on other "
        "cells being as coded.\n"
    )
    return lines


def _section_linkage(block: dict) -> list[str]:
    lines = ["## 9. Mediation: total effects through the enabling graph\n"]
    lines.append(
        f"Edges: **{block['n_edges']}** enabling relations over {block['n_nodes']} "
        "developments. Direct effects are the coded matrix; total effects resolve "
        "mediation through the Leontief inverse (I - B)^-1 (Leontief 1936; Hirschman "
        "1958). Forward linkage is the total effect a development transmits to others "
        "per unit of its own impact -- the formal version of 'this is a seed'.\n"
    )
    lines.append(
        "| development | direct | total own | downstream reach | forward linkage |\n"
        "|---|---|---|---|---|\n"
    )
    for row in block["ranked"][:20]:
        lines.append(
            f"| {row['name'][:40]} | {row['direct']:.0f} | {row['total_own']:.1f} | "
            f"{row['downstream']:.1f} | {row['forward_linkage']:.2f} |\n"
        )
    lines.append(
        f"\nMedian forward linkage {block['median_forward_linkage']:.3f}. Knowledge-"
        "bearing developments are listed separately so the seed hypothesis can be "
        "read off the analysis rather than asserted by it.\n"
    )
    lines.append(
        "| knowledge development | forward linkage | downstream reach | rank |\n|---|---|---|---|\n"
    )
    for row in block["knowledge"]:
        lines.append(
            f"| {row['name'][:40]} | {row['forward_linkage']:.2f} | "
            f"{row['downstream']:.1f} | {row['rank']} / {block['n_nodes']} |\n"
        )
    lines.append(f"\n{block['verdict']}\n")
    return lines


def _section_limitations() -> list[str]:
    lines = ["## 8. Limitations\n"]
    lines.extend(f"- {item}" for item in LIMITATIONS)
    lines.append("")
    return lines


LIMITATIONS = [
    "**Single coder.** Inter-coder reliability has not been measured. It is the "
    "largest threat to validity. The graph layer helps: 'was A necessary for B?' is "
    "a binary question with far higher agreement rates than 'was this a 2 or a 3?'.",
    "**Sample, not census.** The developments are a judgement sample. Era-level "
    "statistics inherit its composition; only 'impact per development' is comparable "
    "across eras.",
    "**Rubric saturation.** Four categories cannot separate the top of the scale, so "
    "no acceleration claim is supported.",
    "**Omission uncertainty is unmodelled.** The Morris screen holds zero cells at "
    "zero, so it says nothing about developments or effects left out entirely.",
    "**Attribution, not causation.** The graph layer narrows this gap by requiring an "
    "explicit citable enabling claim per edge, but a DAG is a hypothesis, not an "
    "identification strategy. The complete fix -- instrumented response from "
    "historical shocks -- is not built here.",
    "**Additive model.** A purely multiplicative enabler is invisible to a linear "
    "decomposition, since SVD(cA) = c SVD(A). Mediation through the graph is the "
    "partial repair; growth accounting is the complete one.",
    "**Tensor power.** The era-shuffled null on the interaction share is the binding "
    "constraint on the tensor result; treat it as inconclusive until the coding is "
    "denser or the era mode is coarser.",
    "**Bibliography provenance.** Entries not marked verified in `data/sources.yml` "
    "were compiled from domain knowledge; run `world-impact verify-sources` first.",
]
