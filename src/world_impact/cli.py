"""Command line interface."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import typer
from rich.console import Console
from rich.table import Table

from world_impact import figures, nulls, report, stages
from world_impact.data import DEFAULT_DATA_DIR, load_dataset
from world_impact.pipeline import SEED, run_analysis

app = typer.Typer(add_completion=False, no_args_is_help=True, help=__doc__)
console = Console()

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
FIGURES = ROOT / "figures"


@app.command()
def version() -> None:
    """Print the package version."""
    from world_impact import __version__

    console.print(f"world-impact {__version__}")


@app.command()
def validate(data_dir: Path = typer.Option(DEFAULT_DATA_DIR, "--data")) -> None:
    """Validate the coding matrix and its provenance. Fails the build on error."""
    dataset = load_dataset(data_dir)
    console.print(
        f"[green]valid[/green]: {dataset.n_developments} developments, "
        f"{dataset.n_outcomes} outcome domains, "
        f"{int((dataset.matrix() > 0).sum())} coded cells"
    )
    table = Table(title="provenance")
    table.add_column("development")
    table.add_column("sources", justify="right")
    table.add_column("outcomes", justify="right")
    for development in dataset.developments:
        table.add_row(
            development.name[:48],
            str(len(development.sources)),
            str(len(development.effects)),
        )
    console.print(table)


@app.command()
def analyse(
    quick: bool = typer.Option(False, "--quick", help="small draws, for tests"),
    seed: int = typer.Option(SEED, "--seed"),
    out: Path = typer.Option(REPORTS / "results.json", "--out"),
    no_reference: bool = typer.Option(False, "--no-reference"),
) -> None:
    """Run the full analysis and write reports/results.json."""
    settings = (
        {
            "smaa_draws": 2000,
            "null_iterations": 40,
            "pa_iterations": 100,
            "tensor_null_iterations": 10,
            "screen_trajectories": 5,
            "screen_targets": 1,
        }
        if quick
        else {}
    )
    results = run_analysis(seed=seed, reference_panel=not no_reference, **settings)
    report.write_json(results, out)
    _print_headline(results)
    console.print(f"wrote [bold]{out}[/bold]")


@app.command()
def figures_cmd(
    seed: int = typer.Option(SEED, "--seed"),
    out_dir: Path = typer.Option(FIGURES, "--out"),
) -> None:
    """Regenerate every figure as SVG."""
    rng = np.random.default_rng(seed)
    dataset = load_dataset()
    measurement = stages.measurement_stage(dataset, rng, seed=seed, value_draws=8)
    structure_block = stages.structure_stage(dataset, rng, pa_iterations=300)
    ranking_block = stages.ranking_stage(
        dataset, measurement["value_matrices"], rng, smaa_draws=2000
    )
    axes = structure_block["axes_object"]
    fit = measurement["fit_object"]
    threshold = np.asarray(nulls.parallel_analysis(dataset.matrix(), rng, n_iter=300)["threshold"])
    acceptance = np.asarray(ranking_block["smaa"]["acceptance"])

    written = [
        figures.scree(
            np.asarray(structure_block["eigenvalues"]),
            threshold,
            float(structure_block["noise_floor"]),
            out_dir / "scree.svg",
        ),
        figures.loadings_heatmap(
            axes.rotated,
            dataset.outcome_labels,
            int(structure_block["n_retained_pa95"]),
            out_dir / "loadings.svg",
        ),
        figures.rank_acceptability(
            np.asarray(ranking_block["smaa"]["rank_acceptability"]),
            dataset.names,
            [int(i) for i in np.argsort(-acceptance)],
            out_dir / "rank-acceptability.svg",
        ),
        figures.impact_breadth(
            np.asarray(ranking_block["totals"]),
            np.asarray(ranking_block["breadth"]),
            dataset.names,
            np.asarray(ranking_block["frontier"], dtype=bool),
            out_dir / "impact-breadth.svg",
        ),
        figures.pervasiveness_bar(
            np.asarray(axes.pervasiveness_weighted),
            dataset.outcome_labels,
            out_dir / "pervasiveness.svg",
            "Pervasiveness across retained components",
        ),
        figures.test_information(fit, out_dir / "test-information.svg"),
    ]
    for path in written:
        console.print(f"wrote {path}")


@app.command()
def report_cmd(
    results: Path = typer.Option(REPORTS / "results.json", "--results"),
    out: Path = typer.Option(REPORTS / "report.md", "--out"),
) -> None:
    """Render the markdown report from a results.json."""
    payload = json.loads(Path(results).read_text(encoding="utf-8"))
    report.write_markdown(payload, out)
    console.print(f"wrote [bold]{out}[/bold]")


@app.command()
def verify_sources(
    out: Path = typer.Option(REPORTS / "source-verification.json", "--out"),
    limit: int = typer.Option(0, "--limit", help="0 = all"),
) -> None:
    """Check every bibliography entry against Crossref (requires network)."""
    from world_impact.verify import verify_entries

    dataset = load_dataset()
    entries = list(dataset.sources.values())
    if limit:
        entries = entries[:limit]
    results = verify_entries(entries)
    report.write_json(results, out)
    matched = sum(1 for row in results["entries"] if row.get("matched_doi"))
    console.print(f"[bold]{matched}/{len(results['entries'])}[/bold] entries matched to a DOI")
    console.print(f"wrote {out}")


def _print_headline(results: dict) -> None:
    structure_block = results["structure"]
    nulls_block = results["nulls"]
    measurement = results["measurement"]
    tensor_block = results["tensor"]
    console.print(
        f"effective rank [bold]{structure_block['effective_rank']:.2f}[/bold] "
        f"| parallel analysis retains {structure_block['n_retained_pa95']} "
        f"(95th pct) / {structure_block['n_retained_pa50']} (median) "
        f"| MP floor {structure_block['noise_floor']:.2f} "
        f"| above floor {structure_block['n_above_noise_floor']}"
    )
    console.print(
        f"coupling p: row-shuffle {nulls_block['row_shuffle']['p_value']:.4f}, "
        f"margin-preserving swap {nulls_block['swap_null']['p_value']:.4f} "
        f"({nulls_block['swap_null']['realized_swaps']} swaps realized)"
    )
    console.print(
        f"rubric Spearman {results['ranking']['rubric_spearman']:.3f} "
        f"| theta SD median {measurement['theta_sd_median']:.3f} "
        f"| info at top decile / peak {measurement['saturation_ratio']:.2f}"
    )
    console.print(
        f"tensor interaction share {tensor_block['interaction_share']:.3f} "
        f"vs era-shuffled null {tensor_block['interaction_null_mean']:.3f} "
        f"(p {tensor_block['interaction_p_value']:.3f})"
    )


if __name__ == "__main__":
    app()
