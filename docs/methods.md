# Methods

## The object

A matrix `M` with developments as rows and outcome domains as columns.
`M[i, j]` is the magnitude of development `i`'s effect on domain `j`, on an
ordinal 0–3 rubric:

| value | meaning |
|---|---|
| 0 | absent (not written down) |
| 1 | substantial but bounded in space, time or domain |
| 2 | large global or hemispheric shift |
| 3 | transformed the domain at global scale |

The rubric is **outcome-neutral**: catastrophe scores like cure. A
valence-weighted rubric would require a value theory, which would reintroduce the
arbitrariness the project exists to remove.

Two decisions in the object itself matter more than they look:

**Absolute magnitudes, not shares.** The first draft normalised each row to sum
to 1. That forces the axes to be *substitutes* rather than complements, and it
makes any error uniform across axes within one observable *unidentifiable* — the
factor cancels in the normalisation, so the answer is bit-identical. Absolute
magnitudes fix both.

**A closed, machine-checkable protocol.** The pydantic schema *is* the coding
protocol: a typo'd field name, a magnitude outside range, an undeclared citation
key, or an era contradicting the onset ordering fails the build. Rules that are
not enforceable tend to stop applying quietly.

## Stages

### 1. Measurement (`measurement.py`, `grm.py`)

The rubric is ordinal, so its integers are not a ratio scale. A graded response
model (Samejima 1969) treats domains as items and developments as respondents on
a latent "general magnitude of impact" trait:

```
P*(x >= k | theta) = logistic(a_j (theta - b_jk))
P(x = k | theta)   = P*(x >= k) - P*(x >= k+1)
```

Fit by marginal maximum likelihood with Gauss-Hermite quadrature; parameters
reparameterised so discrimination is positive and thresholds strictly ordered by
construction, removing the need for constrained optimisation and the
label-switching it invites.

Two outputs matter downstream: per-development EAP scores **with posterior SDs**,
so measurement uncertainty propagates rather than being assumed away; and the
**test-information function**, which is the honest statement of the ceiling.
Information falls at the top of the scale because there are no higher categories
left to distinguish. That number is why the report makes no acceleration claim.

### 2. Structure (`axes.py`, `structure.py`, `nulls.py`)

The axes are the principal directions of the outcome co-impact grammar. **The
number of them is an output**, and four criteria are reported side by side:
parallel analysis at the 95th percentile (Glorfeld's revision of Horn 1965);
parallel analysis at the median (Horn's original rule); the Marchenko–Pastur
noise floor; and out-of-sample reconstruction error as a function of rank
(Haslbeck & van Bork 2024).

They disagree, and the disagreement is the result. "History has exactly *k*
dimensions" is a choice of criterion dressed as a finding, so a range is reported.

Loadings are labelled **after a declared varimax rotation**. Rotation does not
change the subspace; it changes which labels are defensible, which is why it is a
parameter rather than a hidden step.

### 3. Nulls (`nulls.py`)

Two, in increasing strictness:

- **row shuffle** — permutes nonzero cells within each row, preserving row
  margins and the magnitude multiset while destroying column structure;
- **margin-preserving swap** — bounded checkerboard swaps that preserve row *and*
  column sums exactly. This is the null the first draft needed and did not have.

A coupling statistic is computed on the standardized grammar and compared against
both. The swap null reports how many swaps it actually realized, because an
over-constrained null is not a null.

### 4. Ranking (`ranking.py`)

Order matters, and it is forced by the literature rather than by taste. Arrow
(1951) and Sen (1970) mean no aggregate ordering satisfies a short list of
reasonable axioms, so:

1. **Pareto frontier first** — the only ranking statement requiring no weights;
2. **SMAA second** (Lahdelma, Hokkanen & Salminen 1998) — rank acceptability
   indices over the simplex of outcome weights, crossed with value draws from the
   measurement model's predictive law;
3. **confidence factors** — the probability of ranking first under a local
   Dirichlet centred on a development's own central weight vector. The literature
   uses several definitions of "confidence factor", so this one is stated in the
   docstring rather than implied.

### 5. Sensitivity (`sensitivity.py`)

Morris elementary-effects screening over every nonzero cell, via SALib. This
replaces ±15% lognormal perturbation, which answered the wrong question: it
tested whether slight errors everywhere move the answer, when the real question
is which coding decisions the answer is *sensitive* to. Plus leave-one-column-out
stability, and the Spearman correlation between magnitude-weighted and
presence-only impact, which is how the rubric is shown not to be doing the work.

### 6. Tensor (`tensor.py`)

A development × outcome matrix is a collapse of a development × outcome × era
tensor, and the collapse forbids every era-specific interaction. Tucker/HOSVD via
TensorLy. The reported statistic is the share of core energy off the `a = b = c`
diagonal, compared against an **era-shuffled** null.

### 7. Mediation (`linkage.py`) — the fix for a structural blind spot

A body of knowledge is not a deployable intervention, so it can never be an
ordinary row of an outcome-impact matrix. Quantum mechanics has no line: its
effects arrive through solid-state physics, nuclear physics, spectroscopy, atomic
clocks and lasers. Attributing outcomes only to whatever touched them is a
one-hop projection of a multi-hop process, and it systematically zeroes mediated
causes.

The repair is input–output analysis. With `B[j, i]` meaning "`j` requires `i`",
direct effects propagate to total effects through the Leontief inverse
`(I - B)^-1` (Leontief 1936; the linkage reading is Hirschman 1958). Three
measures are reported, and the third exists because the first is biased:

| measure | definition | bias |
|---|---|---|
| forward linkage | `(total − direct) / direct` | **flatters small direct impact** |
| downstream share | `(total − direct) / total` | bounded, denominator-free |
| transitive reach | count of nodes reachable downstream | purely structural |

The first would have manufactured the result the analysis existed to test, since
knowledge rows have tiny direct impact *by construction*. It is still reported —
hiding it would be worse — but the verdict uses the other two, and a test asserts
the trap so nobody "fixes" the code back into it.

Directions are not assumed. One edge deliberately runs from capability to theory
(`coal_steam → thermodynamics`) because the linear model of innovation is false in
its strong form (Kline & Rosenberg 1986), and the interesting output is where the
causation runs each way.

### 8. Validation (`reference.py`)

The coded magnitudes are `derived` judgement, which is the largest threat to
validity. The honest response is comparison against measured series: outcome-domain
series are pulled from Our World in Data, and the coded co-impact grammar is
compared with the measured cross-domain correlation structure via the RV
coefficient. Domain pairs correlating above 0.95 in the measured data are
reported, because those are columns that may not be separable. The module
degrades honestly: unresolved series are reported as missing and never imputed.

## Threats to validity

Stated in `reports/report.md` every time it renders:

1. **Single coder.** Inter-coder reliability is not measured. The graph layer
   helps: "was A necessary for B?" is binary and citable, with far higher
   agreement rates than "was this a 2 or a 3?".
2. **Sample, not census.** A judgement sample. Era statistics inherit its
   composition; only impact *per development* is comparable across eras.
3. **Rubric saturation.** No acceleration claim is supported.
4. **Omission uncertainty unmodelled.** The Morris screen holds zero cells at
   zero, so it says nothing about what was left out entirely.
5. **Attribution, not causation.** An explicit edge per claim narrows the gap,
   but a DAG is a hypothesis, not an identification strategy.
6. **Additive model.** A purely multiplicative enabler is invisible to a linear
   decomposition. Mediation is the partial repair; growth accounting is the
   complete one.
7. **Tensor power.** The interaction share does not beat its null at this
   sparsity, so the tensor result is inconclusive.
8. **Bibliography provenance.** Entries not marked verified were compiled from
   domain knowledge; run `world-impact verify-sources` before citing.
