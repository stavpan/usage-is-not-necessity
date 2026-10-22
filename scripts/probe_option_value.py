#!/usr/bin/env python3
"""Probe the option-value and granularity stages without running the pipeline.

Both stages are cheap (no graded-response fit), so they can be inspected in
isolation while iterating on the coding.
"""

from __future__ import annotations

from world_impact import stages
from world_impact.data import load_dataset


def main() -> None:
    fine = load_dataset(level="results")
    coarse = load_dataset(level="developments")
    print(f"fine: {fine.n_developments} rows, {len(fine.edges)} prerequisite edges")
    print(f"coarse: {coarse.n_developments} rows, {len(coarse.edges)} edges")

    option = stages.option_value_stage(fine)
    print(
        f"\nOPTION VALUE  nodes={option['n_nodes']} edges={option['n_edges']} "
        f"available={option['n_available']} total_capability={option['total_capability']:.0f}"
    )
    print("-- top 20 by option value (weighted, with substitutability discount) --")
    for row in option["ranked"][:20]:
        print(
            "  {:<52} ov={:.4f} crit={:.4f} subs={:.2f} lost={:3d} deps={:2d}".format(
                row["name"][:52],
                row["option_value"],
                row["criticality"],
                row["substitutability"],
                row["reach_lost"],
                row["n_dependants"],
            )
        )
    print("-- biggest movers: high option value, low direct impact --")
    for row in option["biggest_movers"][:12]:
        print(
            "  {:<52} impact_rank={:3d} ov_rank={:3d} shift={:3d}".format(
                row["name"][:52],
                row["impact_rank"],
                row["option_value_rank"],
                row["shift"],
            )
        )
    print("-- top 10 by direct impact, for contrast --")
    for row in option["by_impact"][:10]:
        print("  {:<52} impact={:.0f}".format(row["name"][:52], row["impact"]))

    granularity = stages.granularity_stage(fine, coarse)
    print("\nGRANULARITY")
    print("  verdict:", granularity["verdict"])
    print("  coarse rows with children:", granularity["n_coarse_with_children"])
    print("  fine rows without a parent:", granularity["n_fine_without_parent"])
    print("  ranking:", granularity["ranking"]["top_k_overlap"], "overlap")
    print("-- most dispersed coarse rows (bad units of analysis) --")
    for row in granularity["worst_dispersion"]:
        print(
            "  {:<44} children={:2d} dispersion={:.3f} min_cos={:.2f}".format(
                row["parent"][:44], row["n_children"], row["dispersion"], row["min_cosine"]
            )
        )
    print("-- worst coherence (declared effects vs children's max) --")
    for row in granularity["worst_coherence"]:
        print(
            "  {:<44} children={:2d} max_gap={:.0f} mismatched={}".format(
                row["parent"][:44],
                row["n_children"],
                row["max_abs_gap"],
                row["n_mismatched_outcomes"],
            )
        )


if __name__ == "__main__":
    main()
