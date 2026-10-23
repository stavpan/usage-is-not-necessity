# Usage is not necessity

**Citation counts measure how much a work is *used*. Importance is how much *depends* on it. Those are two opposed quantities, and the citation record cannot tell them apart.**

This repo builds both instruments, measures the gap, reports what does and does not survive scrutiny — and ships a **landscape tool** that uses the result to map any field you narrow down to.

```bash
python scripts/landscape.py --doi 10.1002/j.1538-7305.1948.tb01338.x   # a seed paper
python scripts/landscape.py --topic "cognitive dissonance"            # a topic
```

## The answer

| ranked by **use** (citations) | ranked by **necessity** (transitive reach) |
|---|---|
| limma — moderated fold-change estimation | **The infinitesimal calculus** (58 of 150 downstream) |
| lme4 — mixed-effects models | Electromagnetic induction |
| ResNet | The Carnot cycle |
| DSM — the diagnostic manual | The mechanical equivalent of heat |
| Bradford protein assay | Entropy and the second law |
| Adam optimiser | The calculus of variations |
| GLOBOCAN cancer statistics | Maxwell's equations |
| 2^−ΔΔCt gene expression | The Lorentz force |
| ImageNet | The H-theorem |
| VGG | Planck's quantum hypothesis |
| U-Net | The Bohr model |
| Deep learning for tutoring | The Schrödinger equation |

**Zero overlap.** Not one entry appears in both lists. One column is software, assays, datasets and reporting standards; the other is physics, mathematics and biology. Both are correct answers to different questions.

## Why the gap exists

1. **Citation count is in-degree; importance is transitive in-degree.** A tool cited by 1,000 terminal measurements has reach 1,000. An idea cited by 100 works that each support 100 more has reach 10,100. Rank by in-degree and the tool wins, always.
2. **A citation edge is untyped.** A paper that *uses* BLAST and a paper that *builds on* Shannon produce identical edges. Necessity is a property of the edge's type, and the type is not recorded.
3. **The obvious repair fails.** We tried the PageRank-style fix — rank by how heavy a work's *citers* are. It correlates 0.65 with raw citations, and its top eight are AlexNet, VGG, ResNet, Kohn–Sham, ImageNet, Faster R-CNN, LeNet and SAMtools. Prestige among citers is prestige, and prestige is citations.

## The one thing worth stealing

**Count each criterion's distinct values before letting it rank anything.**

One criterion here took **three** values across 520 works, so its top ranks were tie-breaks. Its rank 1 was the finding that this project had vindicated its own origin — Shannon 1948, the paper it started from. Dropping it moved Shannon out of the top 30 entirely. The check is one line:

```python
if len({row[c] for row in rows}) < 10:
    drop_and_name(c)   # it cannot discriminate; its ranks are the sort function
```

## The strongest result

On the same 150 coded rows, five measures of importance form **two blocks that oppose each other** — what a development *did*, and what *rests on* it. Every between-block correlation is negative:

| | consequence | breadth | peak | necessity |
|---|---|---|---|---|
| **consequence** | 1.00 | 0.74 | 0.71 | **−0.30** |
| **breadth** | 0.74 | 1.00 | 0.16 | **−0.32** |
| **peak** | 0.71 | 0.16 | 1.00 | **−0.15** |
| **necessity** | −0.30 | −0.32 | −0.15 | 1.00 |

The developments that changed the world most are, weakly but consistently, the ones the fewest later developments depend on. A composite "impact score" averaging these is cancelling what it set out to measure.

## What is not new here

The distinction this repo is built on is decades old, and it would be dishonest to
present it as a discovery. That citation counts measure *use* rather than importance is
the settled position of the field's critical literature — Bornmann & Daniel's review
(1,297 citations), Seglen, the MacRoberts, Aksnes et al. And the mechanism the paper
reports in §5.5, that a result stops being cited once it becomes bedrock, is
**obliteration by incorporation**: Merton described it, Garfield named it in 1975, and
McCain measured it in 2014 with a better method than ours.

**What is missing from that literature is the arithmetic.** Everyone agrees the two
quantities differ; nobody has computed both over a citation graph and reported how far
apart the orderings are, because no standard tool computes the second one at all. The
contribution is a measurement, not a concept. Section 1.1 lists what was searched for
prior art and what was not found — and notes that a bibliographic search is weak
evidence of absence.

## The landscape tool

Connected Papers, ResearchRabbit, Litmaps, Inciteful and OpenAlex's own graph views all
show a field's most-cited papers and call that its structure. Every one of them ranks by
**use** — the column the literature has criticised for fifty years — and none computes
the other one. So they answer confidently, and one column short.

Point this at a seed paper or a topic and it computes both columns over the local
citation graph, then leads with the **gap**: the works a field structurally depends on
and does not cite directly. For Shannon 1948 that is Nyquist's 1924 telegraph-speed
paper, Hartley's transmission limits, and 1930s random-number tables — each cited
**once** inside the neighbourhood, by Shannon, with a reach of 51 because everything
downstream of Shannon transitively depends on them. They are information theory's
invisible foundations, and no existing tool surfaces them.

Three things from the research transfer directly:

- **Necessity, not popularity.** Reach counts how many works transitively depend on a
  node, with no free parameter — the property the paper argues for, because the
  alternative carries a parameter that changes the top-ten *set*.
- **The audit.** Before presenting either column the tool counts distinct values and
  reports what it would drop. A ranking whose criterion cannot discriminate is the sort
  function wearing a number's clothes.
- **Trajectory.** Momentum separates durable infrastructure from standards in the act of
  being replaced. A landscape that cannot tell those apart will recommend a dying tool.

Honest about its own limits, because the research is: reach over a *citation* graph is
reach over **untyped** edges, so it is an upper bound on necessity rather than necessity.
Locally, use and necessity also correlate *positively* (about +0.86) rather than
opposing as they do globally — a local graph is transitive by construction — so the
tool's value is the gap list, not a disagreement between whole rankings. And the gap
list is age-confounded: the oldest shared ancestors are the easiest to find.

![The same question, two instruments](docs/figures/necessity-contrast.svg)

## What is honest about this

- **The bibliometric layer is real, measured data** — fetched from OpenAlex and committed, so every number reproduces offline.
- **The dependency layer is coded by one person and its reliability is unmeasured.** Every edge is traceable to a source and the graph passes chronology and acyclicity audits, but that is internal consistency, not verification. `scripts/reliability.py` exports a blinded sample for a second coder and reports κ when one exists; until then it says so.
- **Two findings were retracted for reversing under a plausible alternative measurement.** Both concerned classifying works as method or theory: the title classifier and the abstract classifier agree on only 23% of cases, so neither direction is established.

## Reproduce

```bash
pixi install
pixi run gate        # lint, mypy, 36 tests
pixi run all         # edges, bibliography, figures, contrast — no network needed
pixi run docs-build  # the paper
```

Fetches are cached to `data/`, so each runs once: `pixi run fetch-openalex`, `fetch-abstracts`, `fetch-literature`.

## Layout

```
docs/paper.md          the paper
src/world_impact/
  openalex.py          fetch the corpus, the citers, the abstracts
  convergence.py       the instrument: criteria, consensus, the degeneracy and
                       redundancy diagnostics
  linkage.py           transitive reach — the dependency instrument
  fields.py            field flow; net citation exporters
  figures.py           deterministic SVG
data/
  openalex/            the committed corpus, citers, abstracts
  results.yml          150 coded results with effects on 18 outcome domains
  edge-sources.yml     a warrant for each of the 143 prerequisite edges
scripts/               fetch, build, audit
```

Data CC-BY-4.0, code MIT.
