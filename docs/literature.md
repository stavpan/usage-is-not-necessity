# Literature review and positioning

The point of this document is to establish that nothing here was invented in a
vacuum, and to identify precisely what is new. Every section ends with what we
take from it.

## 1. Measuring long-run development

**Morris (2010, 2013)** is the closest existing work and the most direct rival.
His *social development index* averages four components — energy capture per
person, social organisation (max settlement size), **information technology**
(writing and communication systems), and war-making capacity — scored from
14,000 BC to 2000 AD. Two things follow. First, an information component is
*standard* in this literature, not a private obsession: the axis we are accused
of privileging is one of four in the leading quantitative index. Second, Morris
averages. Averaging assumes the four components are substitutable, which is the
same zero-sum move our first draft made and had to abandon. **Take from it:** the
outcome domains and the deep time horizon; **depart from it:** the assumption
that development is a scalar.

**Seshat Global History Databank** (Turchin et al. 2015) codes ~1,500 polities
over 10,000 years against a published variable taxonomy organised into
complexity characteristics. It is the source of our *external* groups, used only
for the inter-framework reliability check. Crucially, **Turchin et al. (2018,
PNAS)** found that 51 Seshat complexity variables collapse onto a single
dominant dimension. That is a strong prior *against* a high effective rank, and
it is the benchmark our null models must beat: beating randomness is not enough
if the literature already reports near-unidimensionality. Our result of 3–4
dimensions on a different object (outcomes, not polity traits) is consistent with
theirs once sampling differences are allowed for.

**Clio-Infra, Maddison (Bolt & van Zanden 2020), Barro-Lee, V-Dem, HYDE 3.2,
UCDP, Global Carbon Project, GBD, WID.**
The custodians of the 18 outcome domains. These are what make the domain set
non-circular: they were chosen from what the measurement system *already* treats
as the state of the world, not to fit an axis.

**Our World in Data** supplies the measured cross-domain panel used in §6 of the
report. It is a validation instrument, not a source of magnitudes.

## 2. Technology diffusion, and what "magnitude" should mean

**Comin & Hobijn (2010)** built CHAT: measured adoption dates and lags for ~20
technologies across ~160 countries. **Rogers (2003)** and **Grübler (1990)**
supply the adoption-curve and infrastructure-substitution formalisms. Together
they show that *magnitude* and *diffusion lag* are separable properties, and that
the second is measurable at scale for the technology subset. This repository
codes only the first. That is a stated omission, not an oversight: substituting
measured adoption lags for coded magnitudes is the single most promising route to
turning part of this instrument from `derived` into `measured`.

**Fortunato et al. (2018)** on the science of science is the corrective to any
naive impact metric: citation counts, attention and importance are different
quantities and conflating them is the standard failure mode.

## 3. Counterfactual and outcome-neutral impact

"Impact" is a counterfactual quantity. **Ferguson (1997)** and **Tetlock &
Belkin (1996)** on counterfactual reasoning in history; **Ord (2020)** as an
attempt to formalise an outcome-neutral magnitude scale; **Parfit (1984)** for
why the scale cannot be confined to present people. The rubric is deliberately
outcome-neutral — catastrophe scores like cure — because a valence-weighted scale
requires a value theory that would reintroduce exactly the arbitrariness the
project exists to avoid.

## 4. Ordinal measurement

The 0–3 rubric is an ordinal instrument. Treating it as a ratio scale is the
error that produced a flat, misleading "impact per development" column in the
first draft. The graded response model (**Samejima 1969**) is the standard
treatment: outcomes as items, developments as respondents, a latent trait with a
posterior SD, and a test-information function that states the instrument's
resolving power. The information function is what turns "the rubric saturates" from
an assertion into a number.

**Horn (1965)** parallel analysis, the **Glorfeld (1995)** 95th-percentile
revision, **Zwick & Velicer (1986)** on why the Kaiser rule overestimates, and
**Haslbeck & van Bork (2024)** on out-of-sample prediction error. We report all
four rather than choosing: when they disagree, the disagreement *is* the finding,
because "how many dimensions does history have" is not a question with a single
criterion-free answer.

## 5. Ranking under uncertainty: why there is no league table

**Arrow (1951)** and **Sen (1970)** establish that no aggregate ordering satisfies
a short list of reasonable axioms. This is not a technicality to be worked
around; it is the reason a single ranked list of historical developments cannot
be the deliverable. What can be delivered:

- the **Pareto frontier**, which requires no weights at all (the only
  normatively innocent ranking statement available);
- **SMAA** (Lahdelma, Hokkanen & Salminen 1998): rank acceptability indices,
  central weight vectors, confidence factors — a distribution over orderings
  instead of an ordering;
- **ROC weights** (Barron & Barrett 1996) as the elicited alternative to a
  uniform prior over weights, so the reader can see how much the answer moves
  between agnosticism and ranked priorities.

## 6. Sensitivity analysis, and the specific error we are correcting

**Morris (1991)** elementary effects and **Campolongo et al. (2007)**; **Sobol
(2001)** and **Saltelli et al. (2008)**; implemented via **SALib**.

The error worth naming: perturbing every cell by ±15% and declaring the ranking
robust. That test answers "does the answer move if I am slightly wrong about
everything?" when the real question is "which of 250 coding decisions is the
answer sensitive to, and how wrong would I have to be about it?". Magnitude
perturbation cannot detect structural error — a missing axis, a missing
development, a wrong unit of analysis. Morris screening can.

## 7. The multilinear object

**Tucker (1966)** and **De Lathauwer et al. (2000)** for the multilinear SVD;
**Kossaifi et al. (2019)** for TensorLy. A development × outcome matrix is a
collapse of a development × outcome × era tensor, and the collapse forbids every
era-specific interaction. The honest statistic is the share of core energy off
the diagonal, and it must be compared against an era-shuffled null rather than a
uniform-chance baseline — a subtlety the first draft got wrong.

## 8. Mediation, linkage, and the "knowledge is the seed" hypothesis

This is the part of the literature the instrument was originally missing, and it
was missing because a matrix of direct effects cannot represent a mediated cause.

**Leontief (1936)** input–output analysis and **Hirschman (1958)** forward/backward
linkage give the formal machinery: if `B[j,i]` is the extent to which `j` requires
`i`, direct effects propagate to total effects through `(I - B)^-1`. "This
development is a seed" then becomes a measurable quantity — the share of its
total effect that arrives downstream — rather than a preference.

**Kline & Rosenberg (1986)** is the necessary correction, and it cuts against the
hypothesis: the *linear model of innovation* (science → technology → growth) is
false in its strong form. The steam engine preceded thermodynamics by roughly
eighty years. So the graph must admit edges in both directions, and the
interesting output is *where* the causation runs each way. In this repository the
counterexample is coded as an explicit edge (`coal_steam → thermodynamics`) so
the analysis has to weigh it.

The result is accordingly **mixed rather than confirmatory**: the six
knowledge-layer developments all sit in the top decile on *downstream share* (how
much of their total effect arrives via others), but **none** sits in the top
decile on *transitive reach* (how much of the graph lies below them). Knowledge
is a low-footprint, high-transmittance node. Agriculture, irrigation, writing and
metallurgy are high-footprint, high-reach nodes. That is a structural
characterisation of the seed intuition, not a vindication of it.

## 9. What is actually new here

Each ingredient exists elsewhere. The join does not, as far as this review found:

1. ordinal expert coding of **world-historical developments against measured
   outcome domains**, with a closed, machine-checkable protocol;
2. **measurement uncertainty propagated into the ranking** (graded response →
   predictive draws → SMAA), rather than a point score;
3. **two nested nulls** for the structure claim — row-shuffle and
   margin-preserving swap — so "there is structure" cannot be a margin artifact;
4. **mediation through an explicit, citable enabling graph**, with forward
   linkage and reach reported separately because the two disagree;
5. **negative results shipped as results**: rubric saturation, the tensor's
   inconclusive interaction share, and the denominator trap in forward linkage.

## 10. Verification status

`data/sources.yml` carries a `verified` flag. Only entries marked `true` were
checked against a primary or authoritative source during construction (currently
Horn 1965, DOI 10.1007/BF02289447, from the Wikipedia citation trail). The rest
were compiled from domain knowledge and **must** be checked with
`world-impact verify-sources` before submission. A bibliography that has not been
machine-checked against Crossref is a liability in review, not an asset.
