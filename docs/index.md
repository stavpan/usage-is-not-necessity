# Usage is not necessity

**Citation counts measure how much a work is *used*. Importance is how much *depends*
on it. Those are two opposed quantities, and the citation record cannot tell them
apart.**

**[Read the paper →](paper.md)**

---

## In one screen

Two instruments, one question, **zero overlap** between their answers.

**Ranked by use** — the twenty most-cited works in each of 26 fields, scored on eight
criteria, combined by consensus — the top twelve are limma, lme4, ResNet, the DSM, the
Bradford assay, the Adam optimiser, GLOBOCAN, 2^−ΔΔCt, ImageNet, VGG, U-Net and a
deep-learning tutoring paper. Software, assays, datasets and reporting standards.

**Ranked by necessity** — 150 coded results, ranked by how much of the dependency graph
sits downstream — the top twelve are the infinitesimal calculus (58 of 150), induction,
the Carnot cycle, the mechanical equivalent of heat, entropy, the calculus of
variations, Maxwell, Lorentz, the H-theorem, Planck, the Bohr model and the Schrödinger
equation.

Not one entry appears in both lists.

## Why

Citation count is **in-degree**; importance is **transitive in-degree**. A tool cited by
1,000 terminal measurements has reach 1,000; an idea cited by 100 works that each support
100 more has reach 10,100. Rank by in-degree and the tool wins, always.

And a citation edge is **untyped**: a paper that *uses* BLAST and a paper that *builds
on* Shannon produce identical edges. Necessity is a property of the edge's type, and the
type is not recorded. The obvious repair — ranking by how heavy a work's citers are —
fails: it correlates 0.65 with raw citations and its top eight are all machine learning.

## The one check worth stealing

Count each criterion's distinct values before letting it rank anything. A criterion with
three values across 520 works cannot discriminate, and its ranks are the sort function
wearing a number's clothes. That check caught the finding that this project had
vindicated its own origin.

## Read the paper

Everything else — the corpus, the criteria, the two-block result, and an honest account
of what did not survive — is in **[the paper](paper.md)**.
