# world-impact

**Usage is not necessity.** An instrument for ranking scientific works, and the
demonstration that bibliometric importance rankings measure *use* while people mean
*necessity* — because a citation edge records that one work referred to another and
never says why.

**[Read the paper](docs/paper.md)** · **[Decision log, with twelve retractions](docs/decisions.md)**

---

## The result in three lines

- A careful nine-criterion citation instrument over 520 works (the twenty most-cited
  in each of 26 fields) returns a top twelve that is entirely instruments: a
  diagnostic manual, a statistics package, a network architecture, two assays, a
  programming language, an algorithm. **Not one is a theory.** The result is robust
  to every repair we applied to the instrument.
- A parameter-free dependency instrument over 150 coded results, ranked by
  transitive reach, returns the infinitesimal calculus (58 of 150 results sit
  downstream of it), electromagnetic induction, Carnot, entropy, Maxwell, Planck,
  the Turing machine. **Not one is software.**
- **The two top-twelve lists share zero entries**, and within a single coding direct
  impact and transitive reach are *negatively* correlated (Spearman ρ = −0.30).

## Why

Citation count is in-degree: how many works *use* a thing. Importance is closer to
transitive in-degree: how much of the structure of knowledge *depends* on it. These
are non-monotone in each other, and the citation record stores an **untyped edge** —
a paper using BLAST and a paper building on Shannon look identical in the graph. The
one attempt to recover necessity from citation structure (a PageRank-flavoured citer
prestige measure) returned the same machine-learning papers as the count it was
meant to correct.

## What is portable

**A degeneracy check.** Count each criterion's distinct values before trusting a
composite ranking. One criterion here had *three* values across 520 works, so its
top ranks were tie-breaks — and its rank 1 was the finding that made the project
look as though it had vindicated its own origin. The check caught three retractions.

## Design commitments

| Commitment | Implementation |
|---|---|
| Nothing ranks without a null | Permutation nulls preserve **both** row and column margins (curveball), so "structure" cannot be a margin artefact |
| No criterion ranks without discriminating | A criterion must take ≥ 10 distinct values or it is dropped and named (`convergence.MIN_DISTINCT_VALUES`) |
| Redundancy is reported, not tolerated | Criteria correlating above 0.95 are collapsed and the effective count reported |
| No denominator that flatters the thesis | The forward-linkage ratio was rejected before publication because its denominator rewarded exactly the nodes the analysis was meant to test; the trap is asserted in a test |
| Retractions are shipped | Twelve, in `docs/decisions.md`, each with the test that killed it |
| Reproducible | `pixi install && pixi run all` from a clean checkout. Deterministic seeds, locked environment, CI enforcing bit-identical output |

## Reproduce

```bash
pixi install
pixi run gate                      # lint, mypy, 81 tests
pixi run analyse                   # coded-layer analysis -> reports/results.json
pixi run figures-openalex          # bibliometric figures -> reports/fields.json
python scripts/make_contrast.py    # the central figure -> reports/contrast.json
pixi run docs-build                # mkdocs, strict
```

The bibliometric corpus and its citer cache are committed, so every number in the
paper reproduces offline. CI runs the pipeline twice and diffs the output, because a
pipeline that is not bit-reproducible under a fixed seed is a sample, not a result.

## Layout

```
data/           coded layer (results, developments, outcomes, edges, exclusions)
                + committed OpenAlex corpus and citer cache
src/world_impact/
  convergence.py    the bibliometric instrument: criteria, ranks, consensus,
                    and the degeneracy / redundancy diagnostics
  linkage.py        the dependency instrument: reachability, transitive reach
  granularity.py    the coarse-vs-fine comparison that retired the coarse layer
  fields.py         field flow and net citation export
  option_value.py   implemented, null result, retracted
  figures.py        deterministic SVG, including the two-instrument contrast
docs/paper.md   the paper
docs/decisions.md   twenty decisions, twelve retractions
tests/          81 tests; a change that breaks the argument breaks a test
```

## Provenance, stated as a result

Three kinds of data, three levels of trust:

- **The bibliometric layer is `measured` and externally reproducible.** Fetched from
  the OpenAlex API and committed, so anyone can re-fetch and diff.
- **The bibliography is 23% verified.** Of 119 hand-compiled entries, Crossref
  confirms 27, finds 59 plausible, 21 weak and 12 unmatched — because Crossref
  indexes articles, not books. `world-impact verify-sources` is reproducible, and its
  output is committed at `data/literature/bibliography-verification.json`.
- **The 143 prerequisite edges carry no sources at all.** So the transitive-reach
  ranking is a demonstration that the method yields the right kind of answer, **not** a
  finding about the relative importance of calculus and thermodynamics. Attaching a
  citation to each edge and recomputing over the sourced subgraph is the single most
  valuable thing anyone could do to this repository.

## Status

Alpha, and the above is why. The bibliometric layer is complete and reproducible. The
dependency layer is single-coder, unsourced and unmeasured for reliability — see
`docs/paper.md` §2.1 and §10. Do not cite the transitive-reach ranking as an estimate
of anything until the edges are sourced.

## Licence

Code MIT. Coded data and derived outputs CC-BY-4.0.

