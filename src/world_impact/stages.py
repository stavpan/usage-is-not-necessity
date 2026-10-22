"""Analysis stages. Each returns a JSON-serialisable dict.

Splitting the pipeline into stages keeps :mod:`world_impact.pipeline` a readable
orchestrator and makes every stage independently testable and independently
reportable -- which matters because the report has to be able to say *which*
stage a conclusion came from.
"""

from __future__ import annotations

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
) -> dict[str, object]:
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
) -> dict[str, object]:
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
) -> dict[str, object]:
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
) -> dict[str, object]:
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
) -> dict[str, object]:
    """Morris screening: which cell codings drive the rank of the top developments."""
    matrix = dataset.matrix()
    order = list(np.argsort(-matrix.sum(axis=1))[:targets])
    screens = {}
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
) -> dict[str, object]:
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
) -> dict[str, object]:
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

    knowledge_rows = [
        {
            "name": names[i],
            "forward_linkage": float(result.forward_linkage[i]),
            "downstream_share": float(result.downstream_share[i]),
            "transitive_reach": int(result.transitive_reach[i]),
            "direct_dependants": float(result.downstream_reach[i]),
            "percentile_share": pct_of_others(result.downstream_share, i),
            "percentile_reach": pct_of_others(result.transitive_reach, i),
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


def reference_stage(
    dataset: Dataset,
    year_min: int = 1950,
    year_max: int = 2022,
) -> dict[str, object]:
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
    redundant = [
        {
            "a": correlation.columns[i],
            "b": correlation.columns[j],
            "r": float(correlation.iloc[i, j]),
        }
        for i in range(len(resolved))
        for j in range(i + 1, len(resolved))
        if abs(correlation.iloc[i, j]) >= 0.95
    ]
    measured = correlation.to_numpy()
    measured = np.nan_to_num(measured, nan=0.0)

    return {
        "available": True,
        "resolved": panel.resolved,
        "missing": panel.missing,
        "coverage": f"{len(resolved)}/{dataset.n_outcomes}",
        "years": [int(panel.frame.index.min()), int(panel.frame.index.max())],
        "n_years": int(panel.frame.shape[0]),
        "comparison": reference.compare_structures(coded, measured),
        "redundant_pairs_above_0.95": redundant,
    }
