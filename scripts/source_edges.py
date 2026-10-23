#!/usr/bin/env python3
"""Give every prerequisite edge a bibliographic warrant, and audit the graph.

The paper's weakest data was `edges.yml`: 143 assertions of the form "X would not
have been possible without Y", none of them carrying a source, which made the entire
transitive-reach ranking unauditable. This script fixes the traceability half of that
and measures the consistency half.

**What it does to the edges.** Each edge inherits the union of its two endpoints'
declared sources, so every edge becomes traceable to at least one citable work. That
is a mechanical derivation -- no new judgement is introduced -- and it is *not*
verification of the dependency claim: a source that documents Maxwell's equations
does not assert that the calculus was necessary for them. The distinction is kept in
the output and in the paper.

**What it audits.** Two checks that can find coding errors offline:

  chronology    every edge should have provider onset <= user onset, since a
                prerequisite that postdates what it enables is a contradiction. The
                graph deliberately contains one exception (the steam engine before
                thermodynamics) and the check surfaces it rather than hiding it.
  acyclicity    a prerequisite graph with a cycle means a coding error somewhere in
                the loop; the cycle is printed so it can be inspected.

Run with --write to modify `data/edges.yml`; without it, the audit is read-only.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EDGES = ROOT / "data" / "edges.yml"
RESULTS = ROOT / "data" / "results.yml"
DEVELOPMENTS = ROOT / "data" / "developments.yml"

EDGE_LINE = re.compile(r"^-\s*\{user:\s*([a-z0-9_]+),\s*provider:\s*([a-z0-9_]+)\s*\}\s*$")


def load_rows() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for path in (RESULTS, DEVELOPMENTS):
        for row in yaml.safe_load(path.read_text(encoding="utf-8")):
            rows[row["id"]] = row
    return rows


def parse_edges() -> list[tuple[int, str, str, str]]:
    """(line number, user, provider, raw line) for every edge, comments preserved."""
    found: list[tuple[int, str, str, str]] = []
    for number, line in enumerate(EDGES.read_text(encoding="utf-8").splitlines(), start=1):
        match = EDGE_LINE.match(line.strip())
        if match:
            found.append((number, match.group(1), match.group(2), line))
    return found


def audit(edges: list[tuple[int, str, str, str]], rows: dict[str, dict]) -> dict:
    chronology: list[dict] = []
    for _, user, provider, _ in edges:
        user_row, provider_row = rows.get(user), rows.get(provider)
        if not user_row or not provider_row:
            chronology.append({"user": user, "provider": provider, "issue": "unknown endpoint"})
            continue
        if provider_row["onset"] > user_row["onset"]:
            chronology.append(
                {
                    "user": user,
                    "provider": provider,
                    "issue": "provider postdates user",
                    "user_onset": user_row["onset"],
                    "provider_onset": provider_row["onset"],
                    "gap_years": provider_row["onset"] - user_row["onset"],
                }
            )

    adjacency: dict[str, list[str]] = defaultdict(list)
    for _, user, provider, _ in edges:
        adjacency[user].append(provider)
    cycles: list[list[str]] = []
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for neighbour in adjacency.get(node, []):
            if state.get(neighbour, 0) == 1:
                cycles.append([*stack[stack.index(neighbour) :], neighbour])
            elif state.get(neighbour, 0) == 0:
                visit(neighbour)
        stack.pop()
        state[node] = 2

    for node in list(adjacency):
        if state.get(node, 0) == 0:
            visit(node)
    return {"chronology": chronology, "cycles": cycles}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="rewrite edges.yml with sources")
    args = parser.parse_args()

    rows = load_rows()
    edges = parse_edges()
    print(f"edges: {len(edges)}   rows: {len(rows)}")

    unknown = [
        (user, provider)
        for _, user, provider, _ in edges
        if user not in rows or provider not in rows
    ]
    if unknown:
        print(f"  WARNING {len(unknown)} edges have an endpoint with no row")
        for user, provider in unknown[:10]:
            print(f"    {user} -> {provider}")

    sourced = 0
    lines = EDGES.read_text(encoding="utf-8").splitlines()
    for number, user, provider, raw in edges:
        union = sorted(
            set(rows.get(user, {}).get("sources") or [])
            | set(rows.get(provider, {}).get("sources") or [])
        )
        if union:
            sourced += 1
        if args.write:
            indent = raw[: len(raw) - len(raw.lstrip())]
            body = raw.strip()[1:-1].strip()
            lines[number - 1] = f"{indent}{{{body}, sources: [{', '.join(union)}]}}"

    print(f"  edges with a non-empty warrant: {sourced} of {len(edges)}")
    if args.write:
        EDGES.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("  rewrote data/edges.yml")

    report = audit(edges, rows)
    print(f"\nCHRONOLOGY: {len(report['chronology'])} edge(s) where the provider postdates the user")
    for row in report["chronology"][:12]:
        if "gap_years" in row:
            print(
                f"  {row['user']} <- {row['provider']}   user {row['user_onset']}, "
                f"provider {row['provider_onset']} (provider is {row['gap_years']} years later)"
            )
        else:
            print(f"  {row['user']} <- {row['provider']}: {row['issue']}")
    print(f"\nACYCLICITY: {len(report['cycles'])} cycle(s)")
    for cycle in report["cycles"][:5]:
        print("  " + " -> ".join(cycle))


if __name__ == "__main__":
    main()
