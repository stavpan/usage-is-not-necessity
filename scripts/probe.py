#!/usr/bin/env python3
"""Ad-hoc probe: run the pipeline with small draws and print a summary.

Not part of the package. Used during development to inspect stages without
writing a full report.
"""

from __future__ import annotations

import argparse
import json

from world_impact.pipeline import run_analysis


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--reference", action="store_true")
    args = parser.parse_args()

    results = run_analysis(
        seed=args.seed,
        smaa_draws=500,
        null_iterations=40,
        pa_iterations=200,
        tensor_null_iterations=10,
        screen_trajectories=4,
        screen_targets=1,
        reference_panel=args.reference,
    )

    structure_block = results["structure"]
    nulls_block = results["nulls"]
    measurement = results["measurement"]
    ranking_block = results["ranking"]
    tensor_block = results["tensor"]
    linkage_block = results["linkage"]

    print("META", json.dumps(results["meta"], sort_keys=True))
    print(
        "STRUCT effrank={:.2f} pa95={} pa50={} floor={:.2f} above={} bestPE={}".format(
            structure_block["effective_rank"],
            structure_block["n_retained_pa95"],
            structure_block["n_retained_pa50"],
            structure_block["noise_floor"],
            structure_block["n_above_noise_floor"],
            structure_block["best_rank_by_prediction_error"],
        )
    )
    print(
        "NULL p_rowshuffle={:.4f} p_swap={:.4f} swaps={}".format(
            nulls_block["row_shuffle"]["p_value"],
            nulls_block["swap_null"]["p_value"],
            nulls_block["swap_null"]["realized_swaps"],
        )
    )
    print(
        "MEAS converged={} theta_sd_med={:.3f} saturation={:.3f}".format(
            measurement["converged"],
            measurement["theta_sd_median"],
            measurement["saturation_ratio"],
        )
    )
    print(
        "RUBRIC spearman={:.3f} loo={}".format(
            ranking_block["rubric_spearman"],
            {k: round(v, 2) for k, v in ranking_block["leave_one_out_columns"].items()},
        )
    )
    print(
        "FRONTIER "
        + "; ".join(
            ranking_block["names"][i]
            for i in range(len(ranking_block["names"]))
            if ranking_block["frontier"][i]
        )
    )
    print(
        "TENSOR interaction={:.3f} null={:.3f} p={:.3f}".format(
            tensor_block["interaction_share"],
            tensor_block["interaction_null_mean"],
            tensor_block["interaction_p_value"],
        )
    )
    print(
        "LINKAGE edges={} p90_share={:.3f} p90_reach={:.0f}".format(
            linkage_block["n_edges"],
            linkage_block["share_threshold_p90"],
            linkage_block["reach_threshold_p90"],
        )
    )
    print("-- knowledge layer -------------------------------------------")
    for row in linkage_block["knowledge"]:
        print(
            "  {:<44} share={:.3f} pct={:5.1f} reach={:2d} pct={:5.1f} fl={:5.2f}".format(
                row["name"][:44],
                row["downstream_share"],
                row["percentile_share"],
                row["transitive_reach"],
                row["percentile_reach"],
                row["forward_linkage"],
            )
        )
    print("-- top 10 by downstream share (denominator-free) ------------")
    for row in linkage_block["ranked"][:10]:
        print(
            "  {:<44} share={:.3f} reach={:2d} direct={:.0f} fl={:5.2f}".format(
                row["name"][:44],
                row["downstream_share"],
                row["transitive_reach"],
                row["direct"],
                row["forward_linkage"],
            )
        )
    print("-- top 10 by transitive reach (structural) ------------------")
    for row in linkage_block["ranked_by_reach"][:10]:
        print(
            "  {:<44} reach={:2d} share={:.3f} direct={:.0f}".format(
                row["name"][:44],
                row["transitive_reach"],
                row["downstream_share"],
                row["direct"],
            )
        )
    print("VERDICT", linkage_block["verdict"])
    print(
        "SWEEP distinct top-10 sets:",
        len({tuple(v) for v in linkage_block["sweep_top10"].values()}),
    )
    print(
        "-- smaa top 10 ----------------------------------------------\n  "
        + "\n  ".join(
            "{:<44} P(1)={:.3f} meanrank={:.2f}".format(
                ranking_block["names"][i],
                ranking_block["smaa"]["acceptance"][i],
                ranking_block["smaa"]["mean_rank"][i],
            )
            for i in sorted(
                range(len(ranking_block["names"])),
                key=lambda k: -ranking_block["smaa"]["acceptance"][k],
            )[:10]
        )
    )
    if results.get("reference", {}).get("available"):
        print("REFERENCE", json.dumps(results["reference"]["comparison"], sort_keys=True))
        print("REFERENCE coverage", results["reference"]["coverage"])
    else:
        print("REFERENCE unavailable")


if __name__ == "__main__":
    main()
