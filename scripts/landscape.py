#!/usr/bin/env python3
"""Map a field you have narrowed down to: a seed paper, or a topic.

    python scripts/landscape.py --doi 10.1136/bmj.314.7079.497
    python scripts/landscape.py --topic "consciousness" --hops 2
    python scripts/landscape.py --openalex W2147108231

The brief's first section is the thing no other tool produces: the works this field
structurally depends on and does not cite directly. Then the two rankings side by side,
the audit of whether either can discriminate, and what is rising or being displaced.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from world_impact import landscape, openalex

ROOT = Path(__file__).resolve().parents[1]


def resolve(args: argparse.Namespace) -> tuple[list[str], str]:
    """Seeds and a human label, from whichever way the focus was given."""
    if args.openalex:
        work = openalex.work_by_id(args.openalex)
        label = f"{work['title']} ({work['year']})" if work else args.openalex
        return [args.openalex], label
    if args.doi:
        work = openalex.work_by_doi(args.doi)
        if work is None:
            raise SystemExit(f"could not resolve DOI {args.doi}")
        return [work["id"]], f"{work['title']} ({work['year']})"
    if args.topic:
        topic = openalex.resolve_topic(args.topic)
        if topic is None:
            raise SystemExit(f"no OpenAlex topic matched {args.topic!r}")
        print(
            f"topic: {topic['name']}  ({topic['field']}, {topic['works_count']:,} works)"
        )
        seeds = openalex.top_works_in_topic(topic["id"], limit=args.seeds)
        if not seeds:
            raise SystemExit(f"no works in topic {topic['name']!r}")
        return [work["id"] for work in seeds], f"{topic['name']} ({topic['field']})"
    raise SystemExit("give one of --doi, --openalex or --topic")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doi")
    parser.add_argument("--openalex")
    parser.add_argument("--topic")
    parser.add_argument("--seeds", type=int, default=10, help="seed works when --topic is used")
    parser.add_argument("--hops", type=int, default=2)
    parser.add_argument("--per-node", type=int, default=40)
    parser.add_argument("--max-nodes", type=int, default=250)
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "landscape.json")
    parser.add_argument("--brief", type=Path, default=ROOT / "reports" / "landscape.md")
    args = parser.parse_args()

    seeds, label = resolve(args)
    print(f"focus: {label}   seeds: {len(seeds)}   hops: {args.hops}")
    graph = landscape.expand(
        seeds, hops=args.hops, per_node=args.per_node, max_nodes=args.max_nodes, verbose=True
    )
    print(f"graph: {len(graph['ids'])} nodes, {len(graph['edges'])} internal edges")
    if not graph["ids"]:
        raise SystemExit("empty graph -- nothing to analyse")

    analysis = landscape.analyse(graph)
    nodes = graph["nodes"]

    print(f"\nrank correlation between use and necessity: {analysis['rank_correlation']:+.3f}")
    print(f"distinct values: {analysis['distinct_values']}")
    if analysis["dropped_criteria"]:
        print(
            "  DROPPED as unable to discriminate: "
            + ", ".join(analysis["dropped_criteria"])
            + " -- their ranks are tie-breaks"
        )

    print("\nTHE GAP: structurally load-bearing, rarely cited within the focus")
    for row in analysis["disagreement"][:10]:
        print(
            f"  {row['year']}  reach {row['reach']:>3}  cited within focus "
            f"{row['in_degree']:>2}x  {row['title'][:56]}"
        )

    write_brief(args, analysis, nodes, label)
    write_json(args, analysis, nodes, seeds, label)


def write_brief(
    args: argparse.Namespace, analysis: dict, nodes: dict, label: str
) -> None:
    """The markdown brief. The gap comes first because it is the reason to run this."""
    lines = [
        f"# {label}",
        "",
        f"*{analysis['n_nodes']} works, {analysis['n_edges']} internal citation edges, "
        f"{args.hops} hops from the seed.*",
        "",
        "## The gap: what this field rests on and does not cite directly",
        "",
        "| year | reach | cited within the focus | work |",
        "|---|---|---|---|",
    ]
    for row in analysis["disagreement"][:20]:
        lines.append(
            f"| {row['year']} | {row['reach']} | {row['in_degree']} | {row['title']} |"
        )
    lines += ["", "## Most used, and most needed", ""]
    lines += ["| ranked by use | ranked by necessity |", "|---|---|"]
    for left, right in zip(analysis["by_use"][:15], analysis["by_necessity"][:15], strict=False):
        lines.append(f"| {nodes[left]['title'][:52]} | {nodes[right]['title'][:52]} |")
    lines += [
        "",
        "## Can either ranking discriminate?",
        "",
        f"- distinct values: in-degree {analysis['distinct_values']['in_degree']}, "
        f"reach {analysis['distinct_values']['reach']}",
        f"- rank correlation between the two columns: {analysis['rank_correlation']:+.3f}",
    ]
    if analysis["dropped_criteria"]:
        lines.append(
            f"- **dropped**: {', '.join(analysis['dropped_criteria'])} — too few distinct "
            "values to order a list, so their ranks are the sort function"
        )
    lines += ["", "## Rising and being displaced", ""]
    lines += ["| rising | momentum | being displaced | momentum |", "|---|---|---|---|"]
    for left, right in zip(analysis["rising"][:8], analysis["decaying"][:8], strict=False):
        lines.append(
            f"| {nodes[left]['title'][:44]} | {analysis['momentum'][left]:.2f} | "
            f"{nodes[right]['title'][:44]} | {analysis['momentum'][right]:.2f} |"
        )
    lines += [
        "",
        "---",
        "",
        "Reach is transitive dependence over *untyped* citation edges, so it is an upper",
        "bound on necessity rather than necessity itself. Type the edges with",
        "`scripts/fetch_contexts.py` and the distinction becomes available.",
    ]
    args.brief.parent.mkdir(parents=True, exist_ok=True)
    args.brief.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {args.brief}")


def write_json(
    args: argparse.Namespace, analysis: dict, nodes: dict, seeds: list[str], label: str
) -> None:
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "label": label,
                "seeds": seeds,
                "hops": args.hops,
                "n_nodes": analysis["n_nodes"],
                "n_edges": analysis["n_edges"],
                "rank_correlation": analysis["rank_correlation"],
                "distinct_values": analysis["distinct_values"],
                "dropped_criteria": analysis["dropped_criteria"],
                "structurally_load_bearing_and_rarely_cited": analysis["disagreement"][:50],
                "by_use": [nodes[w]["title"] for w in analysis["by_use"][:25]],
                "by_necessity": [nodes[w]["title"] for w in analysis["by_necessity"][:25]],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
