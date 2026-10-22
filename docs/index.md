# world-impact

**Usage is not necessity: why bibliometric rankings of "importance" cannot rank
scientific ideas, and what a dependency graph measures instead.**

**[Read the paper →](paper.md)**

---

## The one-paragraph version

Two instruments were built to answer "which scientific works are most important?"
and they answer different questions.

The **bibliometric instrument** (520 works, the twenty most-cited in each of 26
fields, nine criteria, consensus across criteria) ranks a diagnostic manual, a
method write-up, a statistics package, a network architecture, a gene-expression
recipe, two cancer-statistics reports, two protein assays, a programming language,
an algorithm and a methodological distinction. Not one is a theory. That result is
robust to every repair we applied.

The **dependency instrument** (150 coded results, 143 prerequisite edges, ranked by
transitive reach) ranks the infinitesimal calculus -- 58 of 150 results sit
downstream of it -- then electromagnetic induction, the Carnot cycle, the mechanical
equivalent of heat, entropy, the calculus of variations, Maxwell's equations, the
Lorentz force, the H-theorem, Planck's quantum hypothesis, the Bohr model and the
Schrödinger equation. Not one is software.

**The two top-twelve lists share zero entries.**

## Why, in one sentence

A citation edge records that one work *used* another; it does not record *why*, and
use and necessity -- in-degree and transitive in-degree -- are non-monotone in each
other. No refinement of a bibliometric ranking can recover a distinction the data
does not carry.

## The three portable contributions

1. **A degeneracy check.** Count each criterion's distinct values before trusting a
   composite ranking. One criterion in this project had **three** values across 520
   works, so its top ranks were tie-breaks -- and its rank 1 was the finding that
   this project had vindicated its own origin. The check caught three retractions.
2. **The in-degree / transitive-in-degree distinction**, with an empirical
   demonstration that the two rankings are disjoint and, within a single coding,
   *negatively* correlated (ρ = −0.30).
3. **A coded dependency layer**, and an honest account of its limit: 150 rows and 143
   binary sourced assertions, coded by one person, reliability unmeasured.

## Read in this order

1. **[The paper](paper.md)** -- everything, with the numbers and the limitations.
2. **[Decision log](decisions.md)** -- ten retractions. Read this before trusting
   anything elsewhere.
3. **[Methods](methods.md)** -- what the instruments do and cannot do.
4. **[The answer](consensus.md)** -- the bibliometric ranking in full.
5. **[Literature review](literature.md)** -- what exists already and what is new.

## Quickstart

```bash
pixi install
pixi run gate                      # lint, mypy, tests
pixi run analyse                   # coded-layer analysis -> reports/results.json
pixi run figures-openalex          # bibliometric figures -> reports/fields.json
python scripts/make_contrast.py    # the central figure -> reports/contrast.json
pixi run docs-build                # mkdocs, strict
```

## Where the numbers live

`reports/results.json` and `reports/fields.json` (machine-readable),
`reports/contrast.json` (the two rankings side by side), `figures/*.svg`
(generated). The bibliometric corpus and its citer cache are committed, so every
number reproduces offline. CI runs the pipeline twice and diffs the output, because
a pipeline that is not bit-reproducible under a fixed seed is a sample, not a
result.

