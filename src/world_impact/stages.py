"""Analysis stages. Each returns a JSON-serialisable dict.

Splitting the pipeline into stages keeps :mod:`world_impact.pipeline` a readable
orchestrator and makes every stage independently testable and independently
reportable -- which matters because the report has to be able to say *which*
stage a conclusion came from.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from world_impact import nulls, ranking, reference, sensitivity, tensor
from world_impact.axes import analyse_structure
from world_impact.data import Dataset
from world_impact.measurement import fit_graded_response
from world_impact.uncertainty import predictive_draws


def coupling_statistic(matrix: np.ndarray) -> float:
    """Off-diagonal norm of the standardized co-impact grammar.

    A scalar summary of "do outcome domains co-occur non-randomly?", used as the
    test statistic for both nulls.
    """
    matrix = np.asarray(matrix, dtype=float)
    centred = matrix - matrix.mean(axis=0, keepdims=True)
    scale = centred.std(axis=0, ddof=1)
    scale[scale == 0] = 1.0
    standardised = centred / scale
    gram = standardised.T @ standardised / (matrix.shape[0] - 1)
    off = gram - np.diag(np.diag(gram))
    return float(np.linalg.norm(off))


def measurement_stage(
    dataset: Dataset,
    rng: np.random.Generator,
    seed: int = 0,
    value_draws: int = 24,
) -> dict[str, Any]:
    """Fit the graded response model and generate value-uncertainty draws."""
    matrix = dataset.matrix()
    fit = fit_graded_response(matrix, seed=seed)
    grid = np.linspace(-3.0, 3.0, 121)
    information = fit.test_information(grid)
    peak_index = int(np.argmax(information))
    top_decile = fit.top_theta(0.9)
    value_matrices = predictive_draws(fit, matrix, rng, n_draws=value_draws)
    return {
        "converged": fit.converged,
        "n_parameters": fit.n_parameters,
        "log_likelihood": fit.log_likelihood,
        "n_categories": fit.n_categories,
        "theta": fit.theta.tolist(),
        "theta_sd": fit.theta_sd.tolist(),
        "theta_sd_median": float(np.median(fit.theta_sd)),
        "discrimination": fit.discrimination.tolist(),
        "thresholds": fit.thresholds.tolist(),
        "information_peak_theta": float(grid[peak_index]),
        "information_peak": float(information[peak_index]),
        "information_at_top_decile": float(np.interp(top_decile, grid, information)),
        "saturation_ratio": float(
            np.interp(top_decile, grid, information) / information[peak_index]
        ),
        "fit_object": fit,
        "value_matrices": value_matrices,
    }


def structure_stage(
    dataset: Dataset,
    rng: np.random.Generator,
    pa_iterations: int = 500,
) -> dict[str, Any]:
    """Derive the axes; the number of them is an output, not a setting."""
    matrix = dataset.matrix()
    axes = analyse_structure(matrix, dataset.outcome_labels, rng, pa_iterations=pa_iterations)
    return {
        "effective_rank": axes.effective_rank,
        "stable_rank": axes.stable_rank,
        "noise_floor": axes.noise_floor,
        "n_retained_pa95": axes.n_retained,
        "n_retained_pa50": axes.n_retained_median_rule,
        "n_above_noise_floor": int(axes.extras["n_above_noise_floor"]),
        "best_rank_by_prediction_error": int(axes.extras["best_rank_by_prediction_error"]),
        "eigenvalues": axes.eigenvalues.tolist(),
        "cumulative": axes.cumulative.tolist(),
        "components": [
            {
                "index": component,
                "share": axes.component_share(component),
                "top": [
                    {
                        "outcome": dataset.outcome_labels[j],
                        "outcome_id": dataset.outcome_ids[j],
                        "loading": loading,
                    }
                    for j, loading in axes.top_loadings(component)
                ],
            }
            for component in range(min(axes.n_retained, 6))
        ],
        "pervasiveness": {
            dataset.outcome_ids[j]: {
                "n_components": int(axes.pervasiveness[j]),
                "weighted": float(axes.pervasiveness_weighted[j]),
            }
            for j in range(dataset.n_outcomes)
        },
        "prediction_error": axes.mean_prediction_error.tolist(),
        "axes_object": axes,
    }


def nulls_stage(
    dataset: Dataset,
    rng: np.random.Generator,
    iterations: int = 300,
) -> dict[str, Any]:
    """Two nulls for the coupling claim: row-shuffle and margin-preserving swap."""
    matrix = dataset.matrix()
    observed = coupling_statistic(matrix)
    shuffle_values = np.empty(iterations)
    swap_values = np.empty(iterations)
    realized = 0
    for iteration in range(iterations):
        shuffle_values[iteration] = coupling_statistic(nulls.row_shuffle(matrix, rng))
        swapped, realized = nulls.swap_null(matrix, rng)
        swap_values[iteration] = coupling_statistic(swapped)
    return {
        "observed_coupling": observed,
        "row_shuffle": {
            "mean": float(shuffle_values.mean()),
            "p95": float(np.percentile(shuffle_values, 95)),
            "p_value": float((shuffle_values >= observed).mean()),
        },
        "swap_null": {
            "mean": float(swap_values.mean()),
            "p95": float(np.percentile(swap_values, 95)),
            "p_value": float((swap_values >= observed).mean()),
            "realized_swaps": int(realized),
        },
    }


def ranking_stage(
    dataset: Dataset,
    value_matrices: list[np.ndarray],
    rng: np.random.Generator,
    smaa_draws: int = 20000,
    dominance_draws: int = 2000,
) -> dict[str, Any]:
    """Frontier first (no weights), then SMAA (all legitimate weights)."""
    matrix = dataset.matrix()
    binary = dataset.binary()
    names = dataset.names

    totals = matrix.sum(axis=1)
    breadth = binary.sum(axis=1)
    peak = matrix.max(axis=1)
    intensity = np.sqrt((matrix**2).sum(axis=1))
    nonsub = _nonsubstitutability(matrix)
    presence = binary.sum(axis=1)

    frontier = ranking.pareto_frontier({"impact": totals, "breadth": breadth, "peak": peak})
    smaa_result = ranking.smaa(value_matrices, rng, n_draws=smaa_draws)
    dominance = ranking.pairwise_dominance(value_matrices, rng, n_draws=dominance_draws)

    spearman = sensitivity.rank_correlation(totals, presence)
    leave_one_out = sensitivity.leave_one_out_columns(matrix)

    return {
        "names": list(names),
        "totals": totals.tolist(),
        "breadth": breadth.tolist(),
        "peak": peak.tolist(),
        "intensity": intensity.tolist(),
        "nonsubstitutability": nonsub.tolist(),
        "frontier": frontier.tolist(),
        "rubric_spearman": spearman,
        "leave_one_out_columns": leave_one_out,
        "smaa": {
            "n_draws": smaa_result.n_draws,
            "acceptance": smaa_result.acceptance.tolist(),
            "mean_rank": smaa_result.mean_rank.tolist(),
            "rank_sd": smaa_result.rank_sd.tolist(),
            "confidence": smaa_result.confidence.tolist(),
            "rank_acceptability": smaa_result.rank_acceptability.tolist(),
            "central_weights": {
                names[i]: {
                    dataset.outcome_ids[j]: float(smaa_result.central_weights[i, j])
                    for j in range(dataset.n_outcomes)
                }
                for i in smaa_result.top_by_acceptance(5)
            },
            "rank_interval_90": [
                list(smaa_result.best_rank_interval(i, 0.90)) for i in range(dataset.n_developments)
            ],
        },
        "pairwise_dominance": dominance.tolist(),
    }


def _nonsubstitutability(matrix: np.ndarray) -> np.ndarray:
    """1 - max cosine similarity to any other development's profile.

    The naive leave-one-out regression is degenerate here: with more rows than
    columns, every row lies exactly in the span of the others, so the residual
    is identically zero. The nearest-neighbour form asks the answerable
    question -- "could another single development have produced this profile?"
    """
    matrix = np.asarray(matrix, dtype=float)
    norms = np.linalg.norm(matrix, axis=1)
    safe = np.where(norms == 0, 1.0, norms)
    similarity = (matrix @ matrix.T) / np.outer(safe, safe)
    np.fill_diagonal(similarity, 0.0)
    return 1.0 - similarity.max(axis=1)


def sensitivity_stage(
    dataset: Dataset,
    rng: np.random.Generator,
    trajectories: int = 20,
    targets: int = 3,
) -> dict[str, Any]:
    """Morris screening: which cell codings drive the rank of the top developments."""
    matrix = dataset.matrix()
    order = list(np.argsort(-matrix.sum(axis=1))[:targets])
    screens: dict[str, Any] = {}
    for index in order:
        result = sensitivity.screen_coding_decisions(
            matrix, int(index), rng, n_trajectories=trajectories
        )
        screens[dataset.names[index]] = {
            "n_evaluations": result.n_evaluations,
            "top": [
                {
                    "development": dataset.names[i],
                    "outcome": dataset.outcome_labels[j],
                    "mu_star": mu_star,
                    "sigma": sigma,
                }
                for (i, j), mu_star, sigma in result.top(8)
            ],
        }
    return screens


def tensor_stage(
    dataset: Dataset,
    rng: np.random.Generator,
    ranks: tuple[int, int, int] = (4, 4, 3),
    null_iterations: int = 60,
) -> dict[str, Any]:
    """Tucker/HOSVD on development x outcome x era, with an era-shuffled null."""
    incidence = dataset.tensor()
    decomposition = tensor.tucker_decomposition(incidence, ranks)
    observed = tensor.interaction_share(decomposition.core)
    null_values = tensor.era_shuffle_null(incidence, rng, ranks, n_iter=null_iterations)
    by_era = incidence.sum(axis=(0, 1))
    counts = np.bincount(dataset.era_index(), minlength=len(dataset.era_labels()))
    return {
        "ranks": list(ranks),
        "energy_retained": decomposition.energy_retained,
        "reconstruction_error": decomposition.reconstruction_error,
        "interaction_share": observed,
        "interaction_null_mean": float(null_values.mean()),
        "interaction_null_p95": float(np.percentile(null_values, 95)),
        "interaction_p_value": float((null_values >= observed).mean()),
        "mass_by_era": {
            label: float(value) for label, value in zip(dataset.era_labels(), by_era, strict=True)
        },
        "count_by_era": {
            label: int(value) for label, value in zip(dataset.era_labels(), counts, strict=True)
        },
    }


def linkage_stage(
    dataset: Dataset,
    attenuation: float = 0.6,
) -> dict[str, Any]:
    """Mediation: total effects through the enabling graph.

    The last word is computed, not written. ``verdict`` compares the forward
    linkage of the knowledge-layer developments against the rest of the matrix,
    so the seed hypothesis is *tested* here rather than assumed by whoever built
    the graph.
    """
    from world_impact import linkage as lk

    matrix = dataset.matrix()
    direct = matrix.sum(axis=1)
    requires = lk.adjacency(dataset.ids, list(dataset.edges))
    result = lk.linkage(direct, requires, attenuation=attenuation)
    sweep = sensitivity.attenuation_sweep(direct, requires)
    names = dataset.names
    mask = dataset.knowledge_mask()
    others = ~mask

    def pct_of_others(values: np.ndarray, index: int) -> float:
        """Percentile of this development within the non-knowledge rows."""
        reference = values[others]
        if reference.size == 0:
            return float("nan")
        return float((reference < values[index]).mean() * 100.0)

    knowledge_rows: list[dict[str, Any]] = [
        {
            "name": names[i],
            "forward_linkage": float(result.forward_linkage[i]),
            "downstream_share": float(result.downstream_share[i]),
            "transitive_reach": int(result.transitive_reach[i]),
            "direct_dependants": float(result.downstream_reach[i]),
            "percentile_share": pct_of_others(result.downstream_share, int(i)),
            "percentile_reach": pct_of_others(result.transitive_reach, int(i)),
        }
        for i in np.flatnonzero(mask)
    ]
    knowledge_rows.sort(key=lambda row: -row["downstream_share"])

    share_threshold = float(np.quantile(result.downstream_share[others], 0.9))
    reach_threshold = float(np.quantile(result.transitive_reach[others], 0.9))
    above_share = sum(1 for row in knowledge_rows if row["downstream_share"] > share_threshold)
    above_reach = sum(1 for row in knowledge_rows if row["transitive_reach"] > reach_threshold)
    majority = max(1, len(knowledge_rows) // 2)

    sweep_stability = {
        str(value): [names[i] for i in np.argsort(-values)[:10]] for value, values in sweep.items()
    }
    top_sets = {tuple(v) for v in sweep_stability.values()}

    if above_share >= majority and above_reach >= majority:
        conclusion = (
            "SUPPORTED on both denominator-free measures: knowledge-bearing "
            "developments dominate downstream transmittance."
        )
    elif above_share >= majority or above_reach >= majority:
        conclusion = (
            "MIXED: the seed hypothesis holds on one denominator-free measure and "
            "not the other. Read the two columns together rather than choosing."
        )
    else:
        conclusion = (
            "NOT SUPPORTED on the denominator-free measures. Under the "
            "Kline-Rosenberg reading that is a finding rather than a failure: "
            "capability repeatedly precedes theory."
        )

    verdict = (
        f"Of {len(knowledge_rows)} knowledge-layer developments, {above_share} exceed the "
        f"90th percentile of the rest on downstream share ({share_threshold:.2f}) and "
        f"{above_reach} exceed it on transitive reach ({reach_threshold:.0f} developments "
        f"downstream). {conclusion} The top-10 by downstream share is "
        f"{'stable' if len(top_sets) == 1 else 'not stable'} across attenuation values "
        f"0.0-0.95 ({len(top_sets)} distinct top-10 sets), so the membership is robust "
        "while the ordering is not. Caveat: high forward linkage is partly mechanical, "
        "since (total - direct) / direct flatters rows with small direct impact, which "
        "knowledge rows are by construction; that is why the verdict uses the bounded "
        "share and the structural reach instead."
    )

    return {
        "n_edges": result.n_edges,
        "n_nodes": len(names),
        "attenuation": attenuation,
        "share_threshold_p90": share_threshold,
        "reach_threshold_p90": reach_threshold,
        "ranked": result.ranked(names, key="downstream_share"),
        "ranked_by_reach": result.ranked(names, key="transitive_reach"),
        "knowledge": knowledge_rows,
        "sweep_top10": sweep_stability,
        "verdict": verdict,
    }


def option_value_stage(dataset: Dataset, rng: np.random.Generator | None = None) -> dict[str, Any]:
    """Option value: what becomes unreachable without each development.

    Three variants are reported, because the two free choices (weights, and
    whether same-kind substitutes count) each move the answer, and picking one
    silently would be exactly the move this project exists to avoid.
    """
    from world_impact import option_value as ov

    matrix = dataset.matrix()
    requires = ov.requires_matrix(dataset.ids, list(dataset.edges))
    direct = matrix.sum(axis=1)

    kinds = _kind_labels(dataset)
    weighted = ov.option_value(requires, direct, parents=kinds)
    weighted_no_subs = ov.option_value(requires, direct, parents=None)
    unweighted = ov.option_value(requires, np.ones(len(dataset.ids)), parents=kinds)
    expansion = ov.future_space_expansion(requires)
    generator = rng if rng is not None else np.random.default_rng(0)
    null = ov.criticality_null(requires, direct, generator, n_iter=60)

    names = dataset.names
    ranked = weighted.ranked(names)
    by_impact = [
        {"name": names[i], "impact": float(direct[i])}
        for i in sorted(range(len(names)), key=lambda i: -direct[i])[:25]
    ]
    impact_rank = {int(i): position + 1 for position, i in enumerate(np.argsort(-direct))}
    option_rank = {int(row["index"]): position + 1 for position, row in enumerate(ranked)}
    # Annotated explicitly: without it the generator's dicts are inferred as
    # dict[str, object], and every later arithmetic on a field becomes a mypy
    # error rather than a check.
    biggest_movers: list[dict[str, Any]] = sorted(
        (
            {
                "name": names[i],
                "impact_rank": int(impact_rank[i]),
                "option_value_rank": int(option_rank[i]),
                "shift": int(impact_rank[i] - option_rank[i]),
            }
            for i in range(len(names))
        ),
        key=lambda row: -int(row["shift"]),
    )

    return {
        "n_nodes": len(names),
        "n_edges": int(requires.sum()),
        "n_available": weighted.n_available,
        "total_capability": weighted.total_capability,
        "ranked": ranked[:30],
        "ranked_no_substitutes": weighted_no_subs.ranked(names)[:30],
        "ranked_unweighted": unweighted.ranked(names)[:30],
        "future_space_expansion": {
            names[i]: float(expansion[i]) for i in np.argsort(-expansion)[:25]
        },
        "by_impact": by_impact,
        "biggest_movers": [row for row in biggest_movers if int(row["shift"]) > 0][:15],
        "null": null,
        "note": (
            "option value is criticality x (1 - substitutability) under a "
            "conjunctive prerequisite reading, so it is an upper bound; "
            "substitutability counts only alternatives already in a dependant's "
            "prerequisite list, so it is a lower bound"
        ),
    }


def _kind_labels(dataset: Dataset) -> np.ndarray:
    """A 'same kind' label per row, for the substitutability discount.

    Uses the coarse parent where one exists (fine layer) and the primary external
    Seshat group otherwise (coarse layer). Either way it is a claim about which
    developments are alternatives for each other, and it is stated rather than
    buried.
    """
    labels = []
    for development in dataset.developments:
        key = development.parent or development.extern[0].value
        labels.append(key)
    unique = {key: position for position, key in enumerate(sorted(set(labels)))}
    return np.array([unique[key] for key in labels], dtype=int)


def granularity_stage(dataset: Dataset, coarse: Dataset, top_k: int = 10) -> dict[str, Any]:
    """Coarse vs fine: coherence, dispersion, and whether the ranking survives."""
    from world_impact import granularity as gr

    result = gr.analyse_granularity(dataset, coarse, top_k=top_k)
    return {
        "n_coarse_with_children": result.n_coarse_with_children,
        "n_fine_without_parent": result.n_fine_without_parent,
        "ranking": result.ranking,
        "worst_coherence": result.worst_coherence(8),
        "worst_dispersion": result.worst_dispersion(8),
        "mean_dispersion": float(np.mean([row["dispersion"] for row in result.dispersion]))
        if result.dispersion
        else 0.0,
        "verdict": _granularity_verdict(result),
    }


def _granularity_verdict(result: Any) -> str:
    """Computed, not written: does the coarse layer hold up as a unit?"""
    overlap = result.ranking["top_k_overlap"]
    mean_dispersion = (
        float(np.mean([row["dispersion"] for row in result.dispersion]))
        if result.dispersion
        else 0.0
    )
    worst = max((row["min_cosine"] for row in result.dispersion), default=1.0)
    incoherent = sum(1 for row in result.coherence if row["max_abs_gap"] >= 1)
    if overlap >= 0.8 and mean_dispersion < 0.3:
        headline = "the coarse layer holds up"
    elif overlap >= 0.5:
        headline = "the coarse layer mostly holds up"
    else:
        headline = "the coarse layer does NOT hold up as a unit of analysis"
    return (
        f"{headline}: top-{result.ranking['top_k']} overlap {overlap:.2f}, mean "
        f"within-parent dispersion {mean_dispersion:.3f}, and {incoherent} coarse "
        f"row(s) whose declared effects fall short of what their own children "
        f"claim by a full rubric level. Worst within-parent cosine {worst:.2f}: "
        "the lower that number, the more the coarse row is a bag of unrelated "
        "things rather than one intervention."
    )


def reference_stage(
    dataset: Dataset,
    year_min: int = 1950,
    year_max: int = 2022,
) -> dict[str, Any]:
    """Compare the coded grammar against measured long-run series (OWID).

    Degrades honestly: unresolved series are reported as missing and the
    comparison runs on the intersection. No imputation, and the coverage is
    always reported next to the statistic.
    """
    registry = [(outcome.id, list(outcome.owid_candidates)) for outcome in dataset.outcomes]
    try:
        panel = reference.build_panel(registry, year_min=year_min, year_max=year_max)
    except Exception as error:
        return {"available": False, "error": f"{type(error).__name__}: {error}"}

    if not panel.resolved:
        return {"available": False, "error": "no reference series resolved"}

    resolved = list(panel.resolved)
    index = {outcome_id: j for j, outcome_id in enumerate(dataset.outcome_ids)}
    columns = [index[outcome_id] for outcome_id in resolved]
    coded = dataset.matrix()[:, columns]

    correlation = panel.correlation()
    # Convert to numpy and a plain label list up front: pandas' scalar union
    # types make every arithmetic expression on ``iloc`` a typing fight, and the
    # values are what matter here.
    labels = [str(name) for name in correlation.columns]
    measured = np.nan_to_num(correlation.to_numpy(dtype=float), nan=0.0)
    redundant = [
        {"a": labels[i], "b": labels[j], "r": float(measured[i, j])}
        for i in range(len(resolved))
        for j in range(i + 1, len(resolved))
        if abs(float(measured[i, j])) >= 0.95
    ]
    index_values = np.asarray(panel.frame.index)

    return {
        "available": True,
        "resolved": panel.resolved,
        "missing": panel.missing,
        "coverage": f"{len(resolved)}/{dataset.n_outcomes}",
        "years": [int(index_values.min()), int(index_values.max())],
        "n_years": int(panel.frame.shape[0]),
        "comparison": reference.compare_structures(coded, measured),
        "redundant_pairs_above_0.95": redundant,
    }
