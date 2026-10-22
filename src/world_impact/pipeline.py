"""The analysis pipeline: one entry point, fully seeded, JSON-serialisable.

Order is deliberate. Measurement first, because every later step propagates its
uncertainty. Structure second, because the number of axes is an output. Nulls
third, because a structure claim without a null is not a claim. Ranking fourth,
and only after the Pareto frontier -- which needs no weights at all. Sensitivity
and the tensor last, because they are diagnostics on the first four.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from world_impact import stages
from world_impact.data import DEFAULT_DATA_DIR, Dataset, load_dataset

SEED = 20261022


def run_analysis(
    data_dir: Path | str | None = None,
    seed: int = SEED,
    smaa_draws: int = 20000,
    value_draws: int = 24,
    null_iterations: int = 300,
    pa_iterations: int = 500,
    tensor_null_iterations: int = 60,
    screen_trajectories: int = 20,
    screen_targets: int = 3,
    reference_panel: bool = True,
    level: str = "results",
    with_granularity: bool = True,
    dataset: Dataset | None = None,
) -> dict[str, Any]:
    """Run every stage and return a JSON-serialisable result tree.

    ``level`` selects the resolution: ``"results"`` (the fine layer of specific
    artefacts and papers, the default) or ``"developments"`` (the coarse layer of
    disciplines). The pipeline is identical at both, which is what makes the
    granularity comparison a measurement rather than a rhetorical move.
    """
    rng = np.random.default_rng(seed)
    root = data_dir or DEFAULT_DATA_DIR
    ds = dataset if dataset is not None else load_dataset(root, level=level)
    matrix = ds.matrix()

    measurement = stages.measurement_stage(ds, rng, seed=seed, value_draws=value_draws)
    structure_block = stages.structure_stage(ds, rng, pa_iterations=pa_iterations)
    nulls_block = stages.nulls_stage(ds, rng, iterations=null_iterations)
    ranking_block = stages.ranking_stage(
        ds, measurement["value_matrices"], rng, smaa_draws=smaa_draws
    )
    sensitivity_block = stages.sensitivity_stage(
        ds, rng, trajectories=screen_trajectories, targets=screen_targets
    )
    tensor_block = stages.tensor_stage(ds, rng, null_iterations=tensor_null_iterations)
    linkage_block = stages.linkage_stage(ds)
    option_value_block = stages.option_value_stage(ds, rng)
    granularity_block: dict[str, Any] = {"available": False}
    if with_granularity:
        try:
            coarse = load_dataset(root, level="developments")
            granularity_block = stages.granularity_stage(ds, coarse)
            granularity_block["available"] = True
        except ValueError as error:
            granularity_block = {"available": False, "error": str(error)}
    reference_block = stages.reference_stage(ds) if reference_panel else {"available": False}

    return {
        "meta": {
            "seed": seed,
            "level": level,
            "n_developments": ds.n_developments,
            "n_outcomes": ds.n_outcomes,
            "n_cells": int((matrix > 0).sum()),
            "density": float((matrix > 0).mean()),
            "settings": {
                "smaa_draws": smaa_draws,
                "value_draws": value_draws,
                "null_iterations": null_iterations,
                "pa_iterations": pa_iterations,
                "tensor_null_iterations": tensor_null_iterations,
                "screen_trajectories": screen_trajectories,
                "screen_targets": screen_targets,
            },
        },
        "outcomes": [
            {"id": o.id, "label": o.label, "custodian": o.custodian, "unit": o.unit}
            for o in ds.outcomes
        ],
        "measurement": _strip(measurement),
        "structure": _strip(structure_block),
        "nulls": nulls_block,
        "ranking": ranking_block,
        "sensitivity": sensitivity_block,
        "tensor": tensor_block,
        "linkage": linkage_block,
        "option_value": option_value_block,
        "granularity": granularity_block,
        "reference": reference_block,
    }


NON_SERIALISABLE = {"fit_object", "axes_object", "value_matrices"}


def _strip(block: dict[str, Any]) -> dict[str, Any]:
    """Drop the non-serialisable objects that stages carry for plotting."""
    return {k: v for k, v in block.items() if k not in NON_SERIALISABLE}
