# world-impact

**An uncertainty-aware, multi-criteria basis for ranking world-historical developments.**

Most claims that "X was a turning point" are unfalsifiable prose. This repository makes
them falsifiable: it codes ~50 documented developments against 18 outcome domains, then
asks what structure that coding actually supports — and reports the answer as an
*interval plus a Pareto frontier*, never as a single league table, because the arithmetic
says a single league table does not exist.

## What this is not

It is **not** a list of "the most important inventions". It is a measurement instrument
plus an honest account of what that instrument can and cannot resolve. Two results in
this repository are *negative*, and they are reported as prominently as the positive ones:

1. A rubric with four levels cannot distinguish "transformed the world" from "transformed
   the world enormously". At the top of the scale the instrument is blind, so **no claim
   about acceleration is possible from this data**.
2. Ranking depends on (a) which outcomes you weight and (b) which norm you use to combine
   them. Both are normative choices, not empirical ones. We therefore report
   *rank-acceptability* distributions over the space of legitimate choices rather than a
   point ordering.

## Why it might be publishable

There is a substantial literature on measuring long-run social development
([Morris 2013](docs/literature.md#morris2013), [Seshat/Turchin et al. 2018](docs/literature.md#turchin2018)),
and a substantial literature on multi-criteria ranking under uncertainty
([SMAA, Lahdelma et al. 1998](docs/literature.md#lahdelma1998)). What is missing is the
join: **nobody has taken the expert-coded magnitude of a development's effect across
outcome domains and propagated measurement, weighting and norm uncertainty all the way
through to the ranking**, with null models and pre-registered robustness checks. That
join, plus the two negative results above, is the contribution.

## Design commitments

| Commitment | Implementation |
|---|---|
| No axis is assumed | Axes are **derived** as principal directions of the outcome co-impact grammar. The count is an output, selected by parallel analysis, not by taste. |
| Every cell is attributable | Each effect carries a source key into `data/sources.yml`; `world-impact validate` fails the build on a missing citation. |
| Uncertainty propagates | Ordinal codes become a latent scale via a graded-response model; rankings use SMAA (rank acceptability, central weights, confidence factors). |
| Nothing is ranked without a null | Permutation nulls preserve **both** row and column margins (curveball), so "structure" cannot be a margin artifact. |
| No single ranking | Pareto frontier over impact/breadth/peak; Sobol sensitivity over every coding decision. |
| Retractions are shipped | `docs/decisions.md` records three claims from earlier drafts that this code **disproved**, with the test that killed them. |
| Reproducible | `pixi install && pixi run all` from a clean checkout. Deterministic seeds, locked environment, CI enforcing it. |

## Quickstart

```bash
pixi install                 # locked environment
pixi run validate            # schema + citation completeness
pixi run analyse             # writes reports/*.json
pixi run figures             # writes figures/*.svg
pixi run all                 # gates + full pipeline
```

## Layout

```
data/            developments.yml, outcomes.yml, sources.yml, owid series registry
src/world_impact/
  schema.py      pydantic models; the coding protocol as executable validation
  data.py        loading + the incidence tensor
  measurement.py graded-response model: ordinal codes -> latent impact + SE
  structure.py   factor analysis with parallel analysis, Marchenko-Pastur, rotation
  nulls.py       curveball nulls preserving row and column margins
  ranking.py     Pareto, SMAA, rank acceptability, confidence factors
  sensitivity.py Sobol indices over coding decisions
  tensor.py      Tucker/HOSVD over development x outcome x era
  reference.py   OWID measured series: validation against the real world
  figures.py     deterministic SVG
  report.py      markdown + JSON
tests/           property-based and golden tests
docs/            literature review, methods, decision log (including retractions)
```

## Status

Alpha, pre-registration stage. The coding matrix is complete enough to run end-to-end;
inter-coder reliability has **not** yet been measured, which is the single largest threat
to validity (see `docs/methods.md#threats`). Do not cite this as an estimate of anything
until that is done.

## Licence

Code MIT. Coded data and derived outputs CC-BY-4.0. Third-party reference series retain
their own licences (OWID: CC-BY; see `data/raw/owid/README.md`).
