# Usage is not necessity

**Why bibliometric rankings of "importance" cannot rank scientific ideas, and what a dependency graph measures instead**

---

## Abstract

**The idea here is not new and the paper does not claim it is.** That citation counts
measure *use* rather than importance is the settled position of the field's critical
literature [bornmann2008, seglen1997, aksnes2019], and the mechanism we report as
Section 5.5 — that a result stops being cited once it becomes bedrock — was named
obliteration by incorporation sixty years ago and measured better than we measure it
[garfield1975, mccain2014]. **What is missing from that literature is the arithmetic.**
Everyone agrees the two quantities differ; nobody has computed both and reported how
far apart the orderings are, because no standard tool computes the second one at all.
That is the narrow contribution here, and it is a measurement rather than a concept.

The standard answer to "which scientific works are most important?" is a citation
ranking. We built one, carefully: 520 works taken as the twenty most-cited in each
of 26 OpenAlex fields, 17,531 citation edges over 15,671 referenced works, ten
criteria, and a consensus procedure that requires agreement across criteria rather
than excellence in one. Eleven of its top twelve are instruments — two statistical
software packages, three neural network architectures, two methods write-ups, a
diagnostic manual, an assay, a dataset and a data-analysis recipe. Not one is a
theory.

That result is real but it is a statement about *use*, not about importance, and we
show why by turning the instrument on itself. Two of its criteria are **degenerate**:
`reach` takes four distinct values across 520 works and `top_citations` seven, so
their top ranks are decided by tie-breaking rather than measurement. Tripling the
reference depth of the corpus did not fix them, which shows the degeneracy is
structural to an elite-sample citation graph rather than a property of the fetch. Two
criteria are **redundant**: `citations` and `unique_citers` correlate at r = 0.988.
Individual works span up to 517 ranks depending on which criterion is read. Our own
headline -- that the consensus contained exactly one theory paper, Shannon 1948, and
that it held rank 1 on cross-disciplinary reach -- did not survive: that rank 1 was a
tie-break among tied works, and Shannon now sits at position 35 of 520.

The deeper reason is formal and not fixable by better criteria. A citation is a
record of **use**. The quantity people mean by importance is closer to
**necessity**: how much of the structure of knowledge depends on a work. In a
directed graph these are in-degree and transitive in-degree, and citation data
contains only the first, because a paper that uses BLAST and a paper that builds on
Shannon are indistinguishable edges. We therefore measured necessity where it is
actually recorded -- in a hand-coded prerequisite graph of 150 results and 143
edges -- and ranked by transitive reach. Its top twelve are the infinitesimal
calculus (58 of 150 results downstream), electromagnetic induction (49), the Carnot
cycle (49), the mechanical equivalent of heat (47), entropy and the second law
(46), the calculus of variations (38), Maxwell's equations (36), the Lorentz force
(34), the H-theorem (33), Planck's quantum hypothesis (32), the Bohr model (31) and
the Schrödinger equation (17).

The two top-twelve lists share **zero** entries.

We then tried to *measure* the usage/necessity gap rather than argue it, and failed in
a way worth reporting. Classifying works as method or theory by title gives methods a
1.31× citation advantage; classifying the same works from their abstracts — 338 of 520
were fetched — gives theory a 0.81× advantage. The two classifiers agree on only **23%**
of cases where both commit, and the sign of every gap inverts between them, including
the momentum gap that had appeared to show theory decaying faster. Neither direction is
established. **The method/theory split is not measurable with the lexicons available**,
and the two headline numbers that depended on it are retracted.

The coded layer's own rows give the strongest form of the result, because it needs no
comparison between instruments or corpora — five measures of importance on the same 150
rows. They form **two blocks that oppose each other**: what a development *did* (coded
consequence, breadth, peak) and what *rests on* it (transitive reach). Every
between-block correlation is negative, from −0.08 to −0.32. The developments that
changed the world most are, weakly but consistently, the ones the fewest later
developments depend on.

That negative sign also disposes of the obvious objection. Had the single coder let
prominence contaminate the magnitudes, consequence would correlate *positively* with
necessity; it runs the other way. The magnitudes are not a restatement of structural
position.

**The paper's provenance is reported as a result, not as a caveat.** The bibliometric
layer is externally reproducible; the bibliography is hand-compiled and only 23% of
its 119 entries verify against Crossref, with 50% plausible, 18% weak and 10%
unmatched; and the 143 prerequisite edges that produce the necessity ranking carry
**no sources at all**. The transitive-reach ranking is therefore offered as a
demonstration that the method yields the kind of answer the question deserves, not as
a finding about the relative importance of calculus and thermodynamics, and the paper
states what would be required to make it the latter. Five of the project's own claims
are withdrawn in Section 10, and the reason is the same each time: **a number that
looked like a measurement was inside the noise of the frame that produced it.** The
degeneracy check that caught the first of them generalises to any composite ranking.

---

## 1. Introduction

Ask which scientific works mattered most and the answer arrives as a list ordered
by citation count. The genre is old, popular and largely unexamined. Its
characteristic output is a hundred names, and its characteristic failure is that
the names are not what anyone meant by the question.

The failure is not subtle once stated. A citation count records that a work was
*used*. A methodological paper is cited by everyone who applies its method,
including people with no interest in its ideas. A foundational theory is cited by
the far smaller set of people who build on it. The two populations are different
sizes for reasons that have nothing to do with importance, so a ranking by use will
prefer instruments, and the more successful a field is at producing standard tools
the more its ranking will be populated by them.

We set out to build the ranking properly and to see what happened. This paper
reports the ranking, then reports what happened when we examined the ranking's own
criteria, and then reports what we think the episode demonstrates.

Three things emerged, in that order.

**First, the ranking works and says "tools".** A corpus of 520 works -- the twenty
most-cited in each of 26 fields -- scored against nine criteria and combined by a
consensus rule returns a top twelve consisting entirely of measurement
instruments, methods, software, datasets and reporting standards. The result is
stable in the sense that matters: removing criteria, changing the aggregation, or
restricting to the field-normalised measure does not dislodge the instruments from
the top.

**Second, the ranking was measuring less than it appeared to.** Two of the nine
criteria took three and five distinct values respectively across 520 works, so
their top ranks were resolved by tie-breaking. Two pairs of criteria were the same
criterion in different clothes. A work's rank could differ by up to 517 places
depending on which criterion was read, and our own most quotable finding -- that
the consensus contained exactly one theory paper and that it topped the
cross-disciplinary measure -- turned out to rest on a tie-break. Section 4 is that
examination, and it is the part of the paper most likely to be useful to other
people, because the checks are cheap and general.

**Third, and the reason the paper exists: the defect is not in the criteria.**
It is in the observable. "Used by many" and "depended on by much" are different
graph-theoretic quantities -- in-degree and transitive in-degree -- and a citation
edge cannot distinguish them, because *citing* covers both applying a method and
building on a theory. No amount of care with the bibliometric instrument will
recover necessity, because necessity was never recorded.

So we measured necessity where it is recorded. The project had, separately, a
hand-coded layer: 150 specific results and artefacts spanning prehistory to the
present, each with a declared list of prerequisites, giving 143 directed
"would not have been possible without" edges. In that graph, transitive reach -- how
many results sit downstream of a node -- is a well-defined and parameter-free
quantity. Ranking by it produces calculus, induction, Carnot, the mechanical
equivalent of heat, entropy, Maxwell, Planck and Turing. Section 7 puts the two
lists beside each other, and they share nothing.

We are aware of how that reads: we built an instrument, disliked its answer, and
found a second instrument that gave the answer we preferred. We have tried to
foreclose that reading rather than deflect it. The second instrument's measure is
the one the project had already implemented for an unrelated purpose and reported
as *not supported* for the hypothesis it was originally built to test
(Section 10); it is reported here with its failures attached, including that its
curation is single-coder and its reliability is unmeasured. The claim
we make is not that the second ranking is *correct* and the first is wrong. It is
that the two rankings answer different questions, that only one of those questions
is the one people intend, and that the citation record cannot answer it.

What follows. Section 2 fixes the vocabulary. Sections 3 and 4 are the bibliometric
instrument and its examination. Section 5 gives the formal argument. Sections 6 and
7 are the dependency instrument and the comparison. Sections 8 and 9 are robustness
and abandoned directions. Sections 10 and 11 are limitations and retractions.
Section 11 concludes. Every number is produced by code in the repository; the
reproduction recipe is in the appendix.

### 1.1 Related work, and what is new here

**The distinction this paper is built on is old, and it would be dishonest to present
it as a discovery.** That citation counts measure use rather than quality is the settled
position of the field's own critical literature: Bornmann and Daniel's review of what
citation counts actually measure, which is the canonical treatment [bornmann2008],
Seglen on impact factors [seglen1997], the MacRoberts on influences that are never
cited [macroberts2010], Aksnes, Langfeldt and Wouters [aksnes2019], and West and
colleagues asking what counts count *for* [west2002]. In the philosophy of science the
underlying relation has its own name and literature: **epistemic dependence**
[deridder2013]. Restating the critique adds nothing, and this paper does not claim to.

**The specific mechanism we report as a finding was named sixty years ago.** Section 5.5
measures how a work's citation rate decays as it is absorbed, and draws the conclusion
that the citation record's bias against foundations compounds with age. That is
**obliteration by incorporation**: Merton described it, Garfield named it in 1975, and
**McCain measured it** in a full-text database by checking whether a *concept* appears
in the literature without a citation to its origin [mccain2014]. McCain's method is
better than ours — it observes the absence of a citation directly, where we infer it
from a citation-rate proxy — and Section 5.5 now says so and is downgraded from a
finding to a weak replication. The honest summary is that we rediscovered a known
phenomenon with a cruder instrument.

**What this paper is for, then, is not the concept but the arithmetic.** Every standard
tool in this space ranks by in-degree and none computes transitive in-degree, so the
question "how far apart are the two orderings" has not been answered by measuring it.
That is what Section 7 does, and the answer — zero overlap in the top twelve, and a
negative correlation between the coded measures of consequence and necessity — is the
contribution. The novelty claim is deliberately narrow and its evidence is weak in one
direction: it rests on *not finding* prior art, and a bibliographic search is not proof
of absence. What was searched is described below.

**The most direct threat to our central argument is the citation-function
literature.** Teufel and colleagues showed that citations carry distinguishable
functions [teufel2006]; Jurgens and colleagues built citation frames to measure how
a field uses its own past [jurgens2018]; Cohan and colleagues classify citation
intent at scale [cohan2019]. If a citation's intent can be recovered, then the
untyped edge is not untyped — and our claim that necessity is *absent from the
record* would be false. We therefore narrow it deliberately: the claim is about what
**standard bibliometric rankings** can recover from the fields they actually use
(counts, years, reference lists), not about what is impossible with richer data. The
corpus used here had no abstracts and no citation contexts; had it, intent
classification is the experiment that could falsify Section 5 rather than
corroborate it, and we say so in the limitations rather than claiming the
distinction is unrecoverable in principle.

**Disruption is a different question, measured on the same graph.** Funk and
Owen-Smith's dynamic network measure [funk2017] and Park, Leahey and Funk's CD index
[park2023] ask whether later work *breaks with* a paper — whether its successors
bypass it. That is novelty, not necessity: a work can be highly disruptive and
support nothing (a dead-end novelty) or highly necessary and disruptive of nothing
(the infinitesimal calculus did not break with arithmetic). Both are computed on
citation networks and therefore inherit the untyped-edge problem, which is one
reason the CD index has itself attracted dataset-artefact criticism. We note the
relation and do not claim priority over it.

**Ranking by network position has a long pedigree, and we report one of its
failures.** PageRank on the web [page1999] was applied to citation networks as a way
to find work that counts are too crude to see [chen2007, walker2007]. Our
`citer_prestige` criterion is that same family, and Section 5.3 reports that it
returned the usage ranking with extra steps. Freeman's demonstration that degree,
closeness and betweenness are different quantities that "centrality" conflates
[freeman1979] is the structural precedent for this paper's central distinction; we
apply it to the citation graph and measure the consequence.

**Knowledge accumulates, which is why necessity is cumulative.** Jones on the
burden of knowledge [jones2009] and Bloom and colleagues on the falling productivity
of research inputs [bloom2020] both concern the cost of reaching a moving frontier.
Our transitive-reach measure is a structural analogue: it counts how much of a
graph sits downstream of a node, which is a statement about accumulated dependency.

**Long-run coded datasets are the closest prior art to the dependency layer.**
Seshat [turchin2018] codes social complexity across ten millennia with an explicit
protocol and multiple coders. Our coded layer is smaller (150 rows), narrower in
scope and — unlike Seshat — single-coder, which is its principal weakness and the
subject of Section 9.

**Large language models now write annotations, and the reliability literature is
directly relevant to our own provenance.** Gilardi and colleagues found that LLM
annotation can outperform crowd workers on some labelling tasks [gilardi2023]; Ziems
and colleagues map where LLM annotation is and is not dependable [ziems2024]; and
Messeri and Crockett warn that AI-assisted science can produce illusory
understanding — results that feel well-grounded and are not [messeri2024]. That last
warning describes the risk this paper's coded layer poses, and Section 2.1 reports
what we did about it, including what we could not do.

**What was searched, and what was not found.** Before claiming anything here, ten
bibliographic searches were run against Crossref and OpenAlex for prior art on the
specific measures: transitive closure or reachability over citation networks as an
importance ranking; dependency or prerequisite graphs of scientific knowledge;
foundational-paper detection; redundancy and degeneracy of bibliometric indicators; and
popularity-versus-importance measures. The searches returned the concept literature
cited above, the disruption and PageRank families, and graph-theory papers on transitive
closure algorithms — but **nothing that computes transitive reach over a citation graph
as an importance ranking, and nothing on degeneracy in a composite ranking**. That is
the basis for the claim below, and it is weak evidence, because a bibliographic search
establishes absence only of what it would have found.

**What is new here.** Four things, in descending order of confidence.

(i) A **degeneracy check** for composite rankings — count each criterion's distinct
values before letting it rank — which is one line, general, and caught three
retractions in this project. No prior art was found for this and it is the contribution
most likely to be useful to someone else, because it applies to any ranking built from
several measures.

(ii) The **measurement** of how far apart the two orderings are: zero overlap in the top
twelve across two corpora, and a negative correlation between the coded measures of
consequence and necessity. The *distinction* is old; the *arithmetic* is not, so far as
the searches found.

(iii) A **documented failure** of the prestige repair to necessity. Rank-by-citer-quality
is the obvious fix and it is what the PageRank family does; Section 5.3 reports that it
correlates 0.65 with raw citations and returns the usage ranking. A negative result about
the standard repair is worth more than another positive result about it.

(iv) A **verification procedure** for hand-compiled bibliographies and coded graphs, with
reported yield, which is the subject of Section 2.1 — and which produced two of the
withdrawals in Section 10.

**What is explicitly not new**, listed so that it is not mistaken for a contribution:
that citations are not quality [bornmann2008]; that a work's citations decay as it is
absorbed into common knowledge, which is obliteration by incorporation
[garfield1975, mccain2014]; that citation edges carry distinguishable functions
[teufel2006]; that disrupting and consolidating work differ [funk2017]; and that
degree, closeness and betweenness are different things [freeman1979]. This paper
measures a consequence of the second and third of those; it did not find them.


---

## 2. Vocabulary, and the one distinction the paper turns on

Four terms are used throughout in a fixed sense.

**Use.** A work is *used* when another work applies it to produce something. The
method in a methods section is used. Observing that two works are related by a
citation does not tell us which of use or necessity is at work, and this is the
paper's central difficulty.

**Necessity.** A work is *necessary* for another when removing it would remove the
second's justification, not merely its convenience. Necessity is a claim about
counterfactuals and is therefore not directly observed; it is *stated* by a coder
who asserts "X would not have been possible, as it occurred, without Y".

**Importance.** Deliberately left undefined except in one respect: whatever
importance is, it is supposed to be about necessity more than use. A ranking that
returns instruments when the question asked was about ideas has failed, and no
definition of importance that licenses that outcome is the definition anyone had.

**In-degree and transitive in-degree.** For a node in a directed graph, in-degree
is the number of edges pointing at it; transitive in-degree is the number of nodes
from which it is reachable -- equivalently, the size of its dependency closure. The
paper's argument is that citation counts are in-degree, importance as intended is
closer to transitive in-degree, and the two are not monotonically related.

Three **truth types** are labelled on every claim, following the project's
convention. `measured` is read from a device or a database -- a citation count, a
publication year. `stated` is a coder's assertion -- a prerequisite edge, a
magnitude on the rubric. `derived` is computed from the other two -- a rank, a
correlation, a consensus score. Most of what follows is `derived` from one
`measured` and one `stated` input, and its quality is bounded by both.

### 2.1 Provenance: three kinds of data, and one of them is the weak point

The project contains data of three different provenances, and they do not deserve
the same trust. Saying so with numbers is more useful than a general caveat.

**(a) The bibliometric layer is `measured` and externally reproducible.** The 520
seeds, their citation counts, publication years, field assignments, reference lists
and the 5,870 referenced works were fetched from the OpenAlex API and committed as
JSON. Anyone with an API key can re-fetch them and diff the result. Nothing in
Sections 3–5 depends on a judgement made by the authors.

**(b) The bibliography is hand-compiled and *mostly not* verifiable.** `sources.yml`
holds 119 entries, each with an author, year, title and publisher. Each was submitted
to the Crossref API and graded. The yield is the finding:

| tier | criterion | entries |
|---|---|---|
| `verified` | similarity ≥ 0.75 **and** year agrees | 27 |
| `plausible` | similarity ≥ 0.70, or ≥ 0.55 with year agreement | 59 |
| `weak` | similarity ≥ 0.40 | 21 |
| `unmatched` | below 0.40, or no DOI returned | 12 |

So **23% of the bibliography verifies, 50% is plausible, 18% is weak and 10% is
unmatched.** The failures are systematic rather than random, and the reason matters:
Crossref indexes journal articles, so a book query returns the book's front matter.
`arrow1951` matched "INDEX"; `morris2013` matched "Contents"; `fortunato2018` matched
nothing at all.

The tiering exists because the failure mode of a bibliography checker is
**over-confidence**: it always returns *something*, so a naive count of "matched"
rises toward 100% regardless of correctness. The verification module says so in its
own docstring, and it records its own retraction: an earlier version reported "119/119
entries matched to a DOI" without gating, and the tooling now states plainly that *a
DOI hit is not verification*. That earlier number was in this project's own commit
history, which is why the tiers are reported here rather than a match rate.

**(c) The dependency layer is `stated` and single-coder, and its edges are now
traceable.** This is the weak point, and its shape was a schema problem rather than an
oversight. The fine layer's 150 rows carry bibliographic keys into `sources.yml`, so a
row's *existence* is attributable. But its dependency graph is encoded in `results.yml`
as `requires: [id, ...]` — a bare list of identifiers, which has **nowhere to put a
source for the edge**. The 143 claims of the form "X would not have been possible
without Y", which are the entire input to the transitive-reach ranking, therefore
carried no citation at all.

That is fixed. `data/edge-sources.yml` now gives every edge the union of its two
endpoints' declared sources: **143 of 143 edges warranted**, mean 1.55 sources per
edge, with 76 resting on a single source. What this buys is **traceability** — every
edge now resolves to at least one citable work — and what it does *not* buy is
**verification**: a source documenting Maxwell's equations does not assert that the
calculus was necessary for them. Verifying the dependency itself needs a dedicated
citation per edge, and that remains open. The distinction is in the file's header so
it cannot be lost.

Two audits run over the same graph and both are clean: **zero chronological
contradictions** (no prerequisite postdates what it enables) and **zero cycles**. The
audits are cheap and would have found a coding error; that they find none is weak
positive evidence about the graph.

What remains is that one person wrote it. Section 9 reports the inter-coder machinery
and why no number from it is reported here.

**The 150 rows are a small sample of a large universe, and the size of the gap is now
measured.** The rows were chosen by judgement, which is a selection problem, and 150
is too few for the selection to be harmless. The defence is not to code more rows --
that multiplies the same judgement -- but to *enumerate* a systematic universe from a
third party and report the residual. Wikidata was queried for every item carrying a
time of discovery or invention, or a discoverer, with at least four Wikipedia
language editions: **44,918 candidates**, against 400 in the earlier attempt. Of
those, **32 match a coded row** — 0.071% of the pool.

That is a large residual and it is not mostly bias. The pool's unit is "notable entity
with a discovery date", which is dominated by substances, species, places and people,
whereas the coded unit is "intervention with a causal path to an outcome domain". A
discovered element is not an intervention. Every omitted candidate is therefore
assigned a declared exclusion category with a reason in `data/exclusions.yml`, and
only the *unexplained* residual counts. The value of expanding the pool from 400 to
44,918 is that the residual is now bounded over a universe two orders of magnitude
larger, rather than over a sample too small to bound anything.

We state the edge problem plainly because the alternative is worse. A reader who
wanted to check Section 6.3 would have nothing to check against, and a reviewer would
be right to reject it. **The transitive-reach ranking should be read as a demonstration that the
method produces the kind of answer the question deserves, on data whose provenance is
reported — not as a finding about the relative importance of calculus and
thermodynamics.** Section 9 lists the three things that would change that: per-edge
sources, a second coder, and citation-intent classification.

**The related-work anchors were verified before use, and half of them failed.**
Section 1.1 cites seventeen works. Those seventeen are the survivors of twenty-seven
hand-chosen anchors submitted to Crossref with a 0.90 similarity floor and a version
check on the year. Ten were rejected: `merton1968` matched a book chapter rather than
the paper; `wu2019` matched a *Faculty Opinions recommendation of* the paper rather
than the paper; `fortunato2018` matched nothing; `page1999` is a technical report
Crossref does not index; `vrandecic2014` matched an unrelated chapter at 0.39. One
anchor was included deliberately as a non-existent title, to confirm that unresolved
queries are reported rather than kept — and it matched something at 0.51, which is the
clearest possible demonstration of why a similarity floor is necessary. The
verification is reproducible: `python scripts/fetch_literature.py`.

---

## 3. The bibliometric instrument

### 3.1 Corpus

The corpus is the twenty most-cited works in each of the 26 top-level fields
OpenAlex assigns, restricted to 1900–2024: **520 seed works**. For each seed we
captured up to a hundred of its references, giving **17,531 citation edges** over
**15,671 distinct referenced works**, of which 12,000 were resolved to metadata (a
request-budget cap, taken highest-in-degree first) and 11,957 resolved successfully.
Field-flow analysis therefore runs over 13,474 of 17,531 edges, a coverage of
**0.769**. Every seed also carries its full citation history by year, which is what
makes Section 5.5 possible. The corpus is committed to the repository, so every
number below is reproducible offline.

Two properties of this construction matter and both are limitations. Taking the
top twenty *by citation count* means the corpus is a sample of the extreme upper
tail of the citation distribution, which is exactly where the use/necessity
confound is strongest -- instruments are over-represented at the very top by
construction.

Second, the corpus is deliberately **shallow per field**: twenty works, not fifty.
Deepening it was tried and rejected, and the reason is reported in Section 8,
because it is a design finding rather than a preference.

### 3.2 The criteria

Each seed is scored on nine criteria, all oriented so that higher is better. Three
count citations, three look at citation context, two look at the work's citers, and
one normalises by field.

| criterion | truth type | what it is |
|---|---|---|
| `citations` | measured | total citations to date |
| `rate` | derived | citations per year since publication |
| `field_zscore` | derived | citations per year, standardised within its own field |
| `momentum` | measured | recent annual rate ÷ lifetime annual rate (Section 5.5) |
| `unique_citers` | measured | distinct citing works |
| `top_citations` | measured | how many of the 520 seeds cite it |
| `reach` | derived | how many distinct fields those citing seeds come from |
| `upstream` | derived | the field's ratio of outgoing to incoming references |
| `citer_prestige` | measured | median citation count of its 25 most-cited citers |
| `citer_reach` | derived | distinct fields among those citers |

Eight of the ten survive the two admission tests of Section 4 — every criterion must
both vary enough to discriminate and have its input present for at least 95% of rows.
`top_citations` and `reach` fail the first test; the rest fail nothing.

Two of these carry theoretical weight. `upstream` encodes a field-level claim --
that fields which export methods to other fields are doing a different kind of work
from fields that consume them. `citer_prestige` encodes the elementary PageRank
intuition: being cited by heavy works is not the same as being cited by many, so a
work cited by few but very heavy citers is foundational while a work cited by
everyone but by ordinary papers is a service.

### 3.3 The consensus rule

Ranking by one criterion invites the objection that the criterion was chosen to
produce the answer. We therefore rank by **agreement**: a work scores one point per
criterion on which it sits in the top 50, and the consensus order is by support
descending, then by the work's *worst* rank across criteria ascending -- a
pessimist tie-break, so that a work cannot rise by being extreme on one criterion
and poor on the rest.

Support is sparse. Of 520 works, 312 are in the top 50 of nothing, 114 in the top 50
of exactly one criterion, 42 of two, 22 of three, 18 of four, eight of five, and four
of six. **No work is in the top 50 of seven or more of the eight active criteria.** A
Pareto frontier over all criteria contains 112 works. So "consensus" here means "good
on four to six of eight", not unanimity, and the top of the list is a crowd rather
than a single champion.

Field-flow analysis over the same corpus gives the instrument's first
interpretable result: medicine is the largest net exporter of citations, with an
outgoing-to-incoming ratio of 2.37, making it the field where the methodological
apparatus every other field imports is produced.

### 3.4 The answer the instrument gives

The consensus top twelve, with support out of seven and the worst rank each work
achieves on any criterion:

| # | support/8 | worst rank | year | work | momentum |
|---|---|---|---|---|---|
| 1 | 6 | 232 | 2014 | Moderated estimation of fold change (limma) | 1.56 |
| 2 | 6 | 284 | 2015 | Fitting linear mixed-effects models using lme4 | 1.41 |
| 3 | 6 | 498 | 2016 | Deep residual learning for image recognition | 1.72 |
| 4 | 6 | 509 | 2013 | Diagnostic and Statistical Manual of Mental Disorders | **0.38** |
| 5 | 5 | 324 | 1976 | A rapid and sensitive method for protein quantitation (Bradford) | 0.88 |
| 6 | 5 | 384 | 2015 | U-Net: convolutional networks for biomedical image segmentation | 1.70 |
| 7 | 5 | 372 | 2014 | Adam: a method for stochastic optimisation | 1.92 |
| 8 | 5 | 357 | 2021 | Global cancer statistics 2020 (GLOBOCAN) | 2.04 |
| 9 | 5 | 347 | 2001 | Analysis of relative gene expression data (2^−ΔΔCt) | 1.13 |
| 10 | 5 | 518 | 2017 | ImageNet classification with deep convolutional networks | 1.50 |
| 11 | 5 | 506 | 2023 | Exploiting generative AI to scale up intelligent tutoring | 1.65 |
| 12 | 5 | 508 | 2014 | Very deep convolutional networks | 1.67 |

**Eleven of the twelve are instruments**: two software packages for statistics, three
neural network architectures, two methods write-ups, a diagnostic manual, an assay, a
dataset and a data-analysis recipe. Nothing here is a theory of anything. The one
eighteenth-century-style claim is empirical reporting -- cancer incidence -- and it
appears in the wider list.

**The twelfth entry is a criterion artefact and illustrates the paper's own thesis.**
"Exploiting generative AI to scale up intelligent tutoring" is a recent empirical
study, not an instrument, and it reaches the top twelve because `momentum` rewards
recent growth by construction: a 2023 paper whose citations are rising fast scores
high on recent-rate-over-lifetime-rate. The criterion is sound on its own terms and
still distorts the consensus, which is the same failure mode as `reach` in a new
place -- an aggregate inheriting a member's bias. It is reported rather than removed,
because removing it would hide the mechanism.

The momentum column also shows that **"instrument" is not a stable category** in a way
the counting criteria cannot see. The diagnostic manual at rank 4 decays at 0.38 --
it is being replaced -- while GLOBOCAN grows at 2.04 and Adam at 1.92. All three are
load-bearing by count.

Two structural results accompany the list.

**Fame and load-bearingness are near-orthogonal.** Total citations barely predict
being cited by the other top works: the rank correlation is r = 0.07 between
`citations` and `top_citations`, and r = 0.06 between `citations` and `reach` (on
raw values, 0.13 and 0.11). Whatever the citation count is measuring, it is not
"this work is depended on by the works that matter". This is the instrument's own
admission that its headline metric and its structural metric disagree, and it is
visible without any of the criticism in Section 4.

**The concentration is in methods, and it is measurable.** `field_zscore`
correlates with `citations` at only r = 0.21, but `rate` correlates at r = 0.82 and
`citer_prestige` at r = 0.65. So the raw, unnormalised citation measures are
largely one signal; normalising within a field is what breaks it.

---

## 4. Examining the instrument

A ranking assembled from nine measures invites the assumption that nine measures
were applied. Section 4 tests that assumption three ways and reports what each test
found. The tests are cheap, they are general, and one of them overturned this
project's own headline result.

### 4.1 Degeneracy: a criterion that cannot discriminate

Before any criterion can rank, it must take enough distinct values to separate
works. We counted distinct values per criterion across the 520 seeds.

| criterion | distinct values |
|---|---|
| `field_zscore` | 520 |
| `rate` | 520 |
| `momentum` | 520 |
| `citations` | 518 |
| `unique_citers` | 517 |
| `citer_prestige` | 487 |
| `upstream` | 26 |
| `citer_reach` | 11 |
| `top_citations` | **7** |
| `reach` | **4** |

`reach` takes four values (0 to 3) and `top_citations` seven. They are almost
binary -- "is this work cited by any other seed, and are those seeds in one field or
two" -- and they cannot order the top of a list meaningfully. Worse, they do not
merely add noise: because ranking within a tie is resolved by a tie-break, a
criterion with four values *assigns ranks 1, 2, 3… to works it cannot distinguish*.

**The diagnosis offered in an earlier version of this paper was wrong, and the
correction matters.** It attributed the degeneracy to the fetch: twenty references
captured per seed meant seeds rarely cited one another, so in-degree was compressed
into 0–4. The corpus was therefore rebuilt capturing **up to a hundred** references
per seed, tripling the reference set. In-degree rose, as it had to. **The degeneracy
did not go away**: `top_citations` went from five distinct values to seven and
`reach` from three to four, both still far below the floor of ten.

The real cause is the *seed set*, not the reference depth. `top_citations` counts how
many of the 520 seeds cite a work, and the seeds are by construction the *most recent*
most-cited works in each field, which mostly cite work older than themselves. Two
seeds can therefore only cite the same work if it is old enough to precede both and
prominent enough to be in both reference lists, and that intersection is small
whatever the reference cap. In-degree within an elite-sample citation graph is
bounded by the sample, and no amount of care with the fetch changes it. What would
change it is a corpus selected to *include* the cited works rather than only the
citing ones -- which is a different study.

This is the same failure mode that an earlier test in this project caught in the
opposite direction. A constant criterion -- `upstream`, when field-flow data was
absent -- ranked entirely by tie-break and *inflated* every work's support, making
two works appear to be in the top 50 of all five criteria instead of one. That
finding prompted the first guard: constant criteria are dropped and named. The
guard was too narrow. It tested for one distinct value when the real condition is
*too few* distinct values, and `reach` walked straight through it.

### 4.2 Redundancy: fewer criteria than advertised

Two criteria that correlate near 1.0 are one criterion, and counting them twice
inflates support. All correlations in this section are **rank** correlations
(Spearman), which is the right scale for a ranking procedure and the scale the
agreement matrix is computed on; raw-value correlations are given where they
differ materially. The matrix over the active criteria gives one surviving
redundancy: `citations` and `unique_citers` at **r = 0.988** (raw values 0.72).
Before the degeneracy filter, `top_citations` and `reach` sat at **r = 0.999**
(raw values 0.89), which is the signature of the same problem -- both were
measuring "is this cited by any other seed".

So of ten criteria defined, eight survive the admission tests and one pair among
them is redundant, leaving **seven** effective criteria. The consequence for the
consensus rule is direct: a support of "6 of 8" is really about five distinct
signals, and the top of the list should be read as a crowd of works that several
measures agree on rather than as six independent confirmations.

The project had made this mistake before, in a different place. An early version
claimed that the effective rank of the explanatory matrix was 3 to 5 -- an
attractive number, since it says that nine outcome domains are really three or four
independent ones. Calibrating against a permutation null killed it: the observed
effective rank was 3.45 against a null of 3.65 with a 95% band of 2.96 to 4.14, so
the observation sat *inside* the null. It was a property of a nine-column design
with hand-written rows, not of history. That retraction is why this project reports
the count of *independent* criteria next to the count of criteria, and it is the
same failure mode as the one in Section 4.1: a number that looks like a
measurement but is inside the noise of the frame that produced it.

---

## 5. Why: in-degree and transitive in-degree

Sections 3 and 4 established that the bibliometric instrument gives an
instrument-shaped answer and that its criteria were weaker than advertised. This
section argues that the shape of the answer is not a defect of the criteria and
would not be repaired by better ones.

### 5.1 The two quantities

Let the citation graph have works as nodes and citations as directed edges, and let
`in(w)` be the in-degree of work `w` -- how many works cite it. Let `reach(w)` be
its transitive in-degree, the number of works from which `w` is reachable, i.e. the
size of the set that could not have existed in its present form had `w` not
existed.

Citation count is `in`. The quantity people mean when they ask which works are most
important is much closer to `reach`. The two are not monotone in each other, and
the counterexample is elementary.

Take a tool `T` cited by 1,000 works, none of which anything else depends on -- a
standard assay, applied in 1,000 terminal measurements. Then `reach(T) = 1,000`.
Take an idea `I` cited by 100 works, each of which is depended on by a further 100.
Then `reach(I) = 100 + 10,000 = 10,100`, while `in(I) = 100`. So `in(T) > in(I)` by
a factor of ten and `reach(I) > reach(T)` by a factor of ten, in the same graph,
with no contrivance beyond the two structures that tools and ideas actually have.
Ranking by in-degree puts the tool first. Any monotone function of in-degree does.

The converse also holds -- a work can be cited by many and depended on by few, which
is the definition of a widely used standard -- so neither quantity dominates the
other in general. What can be said is that in-degree systematically favours nodes
whose dependants are shallow, and instruments have shallow dependants by
construction: applying an assay produces a measurement, and the measurement is
rarely something further work is built on.

### 5.2 Why the citation record cannot supply the missing quantity

Reachability is computable on any directed graph, including the citation graph. So
why not simply compute `reach` over citations and rank by that?

Because the relation you would be closing over is not the relation you need. A
citation edge asserts that one work *referred to* another. It does not say why, and
the two reasons -- applying a method, and building on an idea -- produce identical
edges. Closing over them computes "could in principle have been influenced by",
which for a high-in-degree tool is dominated by the 1,000 terminal applications:
those 1,000 works are counted as dependants of the tool even though nothing depends
on them. The closure of a use-edge is still a use-relation.

This is the paper's central claim in one sentence: **necessity is not absent from
the citation record because nobody looked for it; it is absent because the record
stores an untyped edge, and necessity is a property of the type.**

### 5.3 An attempt to recover it from within bibliometrics, and why it failed

Before conceding, we tried the strongest repair available inside citation data. The
`citer_prestige` criterion asks not *how many* cite a work but *how heavy the
citers are*: the median citation count of a work's 25 most-cited citing works. If
ideas are cited by foundational works and tools by ordinary ones, this should
separate them. It is the PageRank intuition, and it is computable from data we
already had.

It does not work, and the failure is instructive. `citer_prestige` correlates with
raw `citations` at **r = 0.65** on ranks -- high enough that it is largely the same
signal one hop out. And the top eight works by citer prestige are, in order,
AlexNet (32,089), VGG (25,713), ResNet (24,377), the Kohn–Sham equations (21,673),
ImageNet (21,336), Faster R-CNN (19,005), LeNet (17,296) and SAMtools (15,235):
seven machine-learning architectures and one bioinformatics tool, with a single
1965 physics paper among them. Prestige among citers is prestige, and prestige is
citations. The measure rewards being cited by the most-cited works, which are
themselves mostly instruments, so it reproduces the bias it was built to remove.

That is the strongest case for the argument in 5.2: an attempt to extract necessity
from citation structure, using a measure designed for exactly that purpose, returned
the usage ranking with extra steps.

### 5.4 The size of the gap, where it can be measured

One quantity *is* available from the bibliometric side, and it bounds the gap. Works
in the corpus can be classified by title into method-like and theory-like, and the
two groups compared on the criteria.

| group | n | median citations | median citations/yr | median citer prestige | median momentum |
|---|---|---|---|---|---|
| method | 148 | 29,534 | 1,036.5 | 2,348 | 0.98 |
| theory | 33 | 22,513 | 592.5 | **3,710** | 0.87 |
| unclassified | 339 | 19,592 | 709.0 | 2,538 | 0.95 |

On these labels, methods are cited **1.31×** more often and **1.75×** faster than
theory, while theory's citers are **1.58×** heavier (method/theory citer prestige 0.63).

**These numbers should not be used, and the reason is in Section 5.5.** The labels come
from a title classifier, and the corpus now also supports an abstract classifier, which
agrees with it on only 23% of cases and reverses the citation ratio to 0.81. A
direction that flips under a plausible alternative measurement is not established. The
table is kept because deleting it would hide the disagreement, not because it is a
result.

The classification weakness was flagged when the table was first written — a title like
*On the electrodynamics of moving bodies* contains no theory keyword, so 33 theory
works in 520 is a lower bound biased toward titles that advertise their genre. What was
not anticipated is that fixing it would *invert* the finding rather than sharpen it.

### 5.5 A weak replication of obliteration by incorporation

**This section is not a discovery, and it is the weakest thing in the paper.** What it
measures is **obliteration by incorporation**, the phenomenon Merton described and
Garfield named [garfield1975]: a result that becomes bedrock stops being cited, because
there is no need to cite Newton to use calculus. McCain measured it properly in 2014 by
searching a full-text database for a *concept* appearing without a citation to its
origin [mccain2014] — observing the absence directly. This section instead infers it
from a citation-rate proxy, which is cruder, and Section 1.1 says so.

What the section adds, if anything, is a number on the size of the effect in one corpus
and a failed attempt to measure it cleanly. It is kept because the failure is
informative about instrument choice, not because the phenomenon is news.

Section 5.4 measured *how often* things are cited. The corpus also carries each work's
citation history by year, which allows a different question: is a work still accruing
citations at its historical rate, or has it been absorbed? The `momentum` criterion is
the mean annual rate over the last five years divided by the lifetime mean annual rate,
so 1.0 is "still on trend" and a value below 1.0 is decay.

The hypothesis that motivated the measure was that a tool that gets superseded loses
citations while a foundation does not, so theory should have *higher* momentum than
methods. **The data refutes it.** Methods have a median momentum of **0.98** and
theory **0.87**: theory's citation rate decays faster than methods'.

The obvious confound is age, since momentum declines with age and theory works are
older in this corpus (median age 45 against 31). The comparison was therefore
repeated within age decade. It survives: **among works aged 20 to 34 years, methods
score 1.06 and theory 0.80.**

| group | n | median age | median momentum |
|---|---|---|---|
| method | 148 | 31 | 0.98 |
| theory | 33 | 45 | 0.87 |
| unclassified | 339 | 25 | 0.95 |
| method, age 20–34 | 39 | — | **1.06** |
| theory, age 20–34 | 11 | — | **0.80** |

Momentum by age band shows the expected gradient — 1.47 for works aged under ten
years, 1.12 for ten to nineteen, and about 0.90 from twenty years onward — so the
measure is behaving sensibly and the method/theory gap is not that gradient.

The interpretation that fits is the known one: a **method is renewed** by each new cohort
of users — every generation that runs BLAST or fits a mixed-effects model cites it afresh
— while a **foundation is absorbed** into common knowledge and stops being cited. That is
obliteration by incorporation, and it implies that the citation record's bias against
foundations compounds with the age of the work rather than being a constant offset.

**The measurement does not survive, and the reason is decisive.** Every result in
Sections 5.4 and 5.5 rests on classifying works as method or theory, and the
classification used was based on titles. The corpus now carries abstracts for 338 of
the 520 seeds, which allows a second classification from the abstract text — and the
two classifiers agree on only **23% of the works where both commit**. They are not two
estimates of one thing; they are close to independent.

Under the abstract-based labels the findings do not merely weaken, they **reverse**:

| classifier | n (method / theory) | citation ratio | age-matched momentum | direction |
|---|---|---|---|---|
| title | 148 / 33 | 1.31 | 1.06 vs 0.80 | theory decays faster |
| abstract | 38 / 26 | **0.81** | **0.95 vs 1.07** | theory decays **slower** |

The citation ratio flips from 1.31 to 0.81 — from "methods cited more often" to
"theory cited more often" — and the momentum gap flips from "theory decays faster" to
"theory decays slower", which is the hypothesis this section set out to test. So
Section 5.4's direction and Section 5.5's refutation are both **classifier artefacts**,
and neither survives. Both are recorded as retractions.

The abstract classifier is also crude — a marker lexicon over 338 abstracts, committing
on only 64 works — so this is not a case of the better classifier overturning the worse
one. It is a case of **two bad classifiers disagreeing**, which establishes neither
direction. What can be said is that the method/theory split is not measurable with the
lexicons available, and that a finding which reverses under a plausible alternative
measurement was never a finding.

What survives in this section is the part that does not depend on any classifier: the
formal argument of Sections 5.1–5.3, the failure of the citer-prestige repair
(r = 0.65 with raw citations, top eight all machine learning), and the zero overlap
between the two rankings in Section 7. Those stand on their own.

The same criterion also shows that *instrument* is not a stable category, which the
counting criteria cannot see. Within the consensus top fifteen, the diagnostic
manual DSM decays at **0.38** — it is being displaced — while GLOBOCAN 2020 grows at
**2.04** and the Adam optimiser at **1.92**. A count-based ranking reports all three
as load-bearing instruments; the trajectory separates durable infrastructure from
standards in the act of being replaced.

---

## 6. The dependency instrument

Necessity is a `stated` quantity, so it has to be coded rather than downloaded. The
project already had such a coding, built for a different purpose: a hand-coded layer
of 150 specific results and artefacts, each with a declared list of prerequisites.

### 6.1 The coded layer

A **result** is a datable, documented intervention: the infinitesimal calculus
(1665), the Carnot cycle (1824), the Schrödinger equation (1926), the EDVAC report
(1945), oral rehydration therapy, backpropagation. The 150 rows span roughly
−8000 to the present and are each assigned to one of 18 outcome domains (population,
health, food, energy, governance, information, mobility, and so on), with an ordinal
magnitude on a 0–3 rubric where 1 is "bounded in space, time or domain" and 3 is
"transformed the domain at global scale". The rubric is explicitly outcome-neutral:
catastrophe scores the same as cure.

An **edge** is a binary, citable assertion of the form *"X would not have been
possible, as it occurred, without Y"*, stored as `user → provider`. There are 143 of
them. Two properties of the edge set are deliberate. Edges are binary rather than
graded, because "was A necessary for B?" has a far higher inter-coder agreement rate
than "was this a 2 or a 3?". And direction is *not* assumed to run from knowledge to
capability: one edge runs the other way, `coal_steam → thermodynamics`, because the
engine preceded the theory by eighty years and a representation in which that cannot
happen is the linear model of innovation, which is false in its strong form.

The edge set is a **statement**, not a measurement. Its quality is bounded by the
coder, and no second coder has yet coded it. Section 9 treats this as the
instrument's principal limitation.

### 6.2 The measure

Within this graph, **transitive reach** is the number of results that transitively
depend on a node: how much of the graph sits downstream of it. It is computed as the
size of the node's dependency closure, with the diagonal removed.

The measure was chosen for what it does *not* contain. It has no weights, so no
attribution parameter has to be chosen. It has no denominator, so it cannot reward
small-footprint nodes. It has no attenuation, so no decay-per-hop has to be
justified. It is a count of nodes in a closure, and the only modelling decision
behind it is that "depends on" is transitive -- which is the definition of depends
on.

This matters because the project has already been burned by a contaminated measure
in this exact position. The original headline for this graph was
`forward_linkage = (total − direct) / direct`, a ratio whose denominator is the
node's *own* direct impact. That denominator rewards nodes with small direct
footprint, and knowledge-bearing nodes have small direct footprint *by
construction*, so using the ratio would have manufactured precisely the result the
analysis existed to test. It was caught before publication and replaced by the
bounded downstream share and, for the reason above, by structural reach. The trap is
now asserted in a test so it cannot be reintroduced.

Reach is not degenerate on this graph, which is the property Section 4.1 taught us
to check: it takes 25 distinct values across 150 nodes, from 0 to 58, with 58 nodes
at zero.

### 6.3 The answer the instrument gives

The top of the transitive-reach ranking, with each node's own direct impact beside
it:

| # | transitive reach | direct impact | result |
|---|---|---|---|
| 1 | **58** | 1 | The infinitesimal calculus |
| 2 | 49 | 3 | Electromagnetic induction |
| 3 | 49 | 2 | The Carnot cycle and the ideal efficiency bound |
| 4 | 47 | 2 | The mechanical equivalent of heat |
| 5 | 46 | 3 | Entropy and the second law |
| 6 | 38 | 1 | The calculus of variations |
| 7 | 36 | 3 | Maxwell's equations and the displacement current |
| 8 | 34 | 2 | The Lorentz force and the electron |
| 9 | 33 | 2 | The H-theorem: entropy as counting |
| 10 | 32 | 2 | Planck's quantum hypothesis |
| 11 | 31 | 2 | The Bohr model of the atom |
| 12 | 17 | 2 | The Schrödinger equation |
| 13 | 16 | 2 | Relay circuits are Boolean algebra |
| 14 | 12 | 3 | Band theory of solids |
| 15 | 11 | 4 | Pasteur's germ theory and sterilisation |
| 16 | 10 | 1 | De Moivre's normal approximation |
| 17 | 10 | 2 | The Turing machine and computability |
| 18 | 9 | 2 | The Pauli exclusion principle and the periodic table |
| 19 | 9 | 4 | The EDVAC report: one shared memory |
| 20 | 9 | 2 | Least squares and the fitting of imperfect data |

This is the list someone asking a bibliometric ranking was expecting. The
infinitesimal calculus is 39% of the entire graph's ancestor: 58 of 150 results
would not have been possible without it, and its *own* direct impact is 1 of 3, the
smallest value on the rubric. Then induction, Carnot, the mechanical equivalent of
heat, entropy, variational calculus, Maxwell, Lorentz, statistical counting,
quantisation, the Bohr atom, the Schrödinger equation, Boolean algebra in relays,
band theory, germ theory, the Turing machine. There is no software, no assay, no
reporting guideline and no dataset anywhere in the top twenty.

**This table is the paper's weakest claim and should be read as such.** Every number
in it is computed from 143 prerequisite edges of which **none carries a source**
(Section 2.1). The ranking is reproducible from the committed graph, and the graph is
auditable in the sense that a reader can inspect it, but no reader can check an
individual edge against a citation because no citation is attached. What the table
demonstrates is that a parameter-free necessity measure, applied to a coded
dependency graph, produces an ordering of the kind the question asks for — and that
the ordering has no overlap with the bibliometric one. It is not evidence about the
relative importance of calculus and thermodynamics, and we do not claim that it is.

### 6.4 The clearest illustration: the ten largest impacts have no dependants

The top of the direct-impact ranking is the sharpest statement of the paper's
argument, because the two columns point opposite ways:

| # | direct impact | transitive reach | result |
|---|---|---|---|
| 1 | 8 | **0** | Approval and diffusion of the oral contraceptive |
| 2 | 8 | **0** | The World Wide Web |
| 3 | 7 | **0** | Rural electrification programmes |
| 4 | 7 | **0** | Smallpox eradication |
| 5 | 6 | 1 | Chlorination of municipal water |
| 6 | 6 | 1 | The end of the gold window |
| 7 | 6 | 1 | Foege's ring vaccination strategy |
| 8 | 6 | **0** | The public steam railway |
| 9 | 6 | **0** | Oral rehydration therapy |
| 10 | 6 | **0** | The commercial lithium-ion cell |

**Eight of the ten developments with the largest direct impact have zero
dependants.** Nothing in the coded graph is built on the World Wide Web, on smallpox
eradication or on oral rehydration therapy — correctly, because those are things done
*to* the world rather than things later work is derived from. Conversely the
infinitesimal calculus, 39% of the graph's ancestor, has the near-minimal direct
impact of 1. Section 7.3 generalises this to five measures on the same rows.

---

## 7. The two answers compared

![Two instruments, two answers](figures/necessity-contrast.svg)

The figure places the two rankings side by side: the twelve works the bibliometric
instrument ranks highest, by citations, and the twelve results the dependency
instrument ranks highest, by transitive reach.

**The two lists share zero entries.** Not one work appears in both, and the
disjointness is not a near-miss: the highest citation count in the left panel is
109,522 while the largest transitive reach in the right panel is 58 of 150. The
numbers are not even on comparable scales, because they are not the same kind of
number.

### 7.1 What the disjointness does and does not establish

It would be easy to overclaim here, so the limits first.

The two instruments rank **different corpora**: 520 journal articles from 1900–2024
versus 150 coded interventions from −8000 to the present. A work cannot appear in
both lists unless it is in both corpora, and almost nothing is -- Shannon 1948 is
one of the very few. So "zero shared entries" is partly guaranteed by the
construction, and a naive reading of it as a measured overlap would be wrong.

Three things survive that objection.

First, the overlap that *is* testable is the point. The bibliometric corpus is the
most-cited works of the last century. If citations measured necessity, the works
they rank highest should be the works that the coded graph shows the most things
depend on. The bibliometric list contains no calculus, no thermodynamics, no
electromagnetism, no quantum theory. It is not that the two lists disagree on
rankings; it is that one of them does not contain the category at all.

Second, Section 6.4 supplies the control that the two-corpus comparison cannot: the
negative correlation of −0.30 between impact and necessity is measured *within* one
corpus, on identical rows, by one coder. The two quantities are opposed even when
every other difference is held constant.

Third, the mechanism is not mysterious and was stated in Section 5 before any of
these lists existed. In-degree favours nodes whose dependants are shallow;
instruments have shallow dependants; therefore a count-based ranking is
instrument-shaped. The empirical result is what the argument predicted, which is
weaker evidence than a prediction that could have failed, but it is not nothing.

### 7.2 What each instrument is for

Neither ranking is wrong. They answer different questions, and the failure is in
using one to answer the other's question.

The bibliometric instrument answers: **what does the current research apparatus
depend on?** Its answer -- assays, statistics software, diagnostic manuals,
reference datasets, reporting standards -- is a correct and useful description of
the infrastructure of contemporary science. It is the right instrument for asking
where the load-bearing *tools* are, and it makes visible something real: that the
methodological apparatus of the sciences is concentrated, that medicine is its
largest net exporter at a ratio of 2.37, and that the same dozen instruments appear
across fields that otherwise share nothing.

The dependency instrument answers: **what does the structure of knowledge rest
on?** Its answer -- calculus, thermodynamics, electromagnetism, quantisation,
computability -- is a correct description of the intellectual spine. It is the right
instrument for the question people actually ask, and it is available only because
someone wrote down the dependency relation by hand.

The error is not in either instrument. It is in the assumption that the second
question can be answered from the data the first one uses, and Section 5 explains
why it cannot: the citation record stores an untyped edge, and necessity is a
property of the edge's type.

### 7.3 The coded measures: two blocks that oppose each other

Everything above compared two instruments on two corpora. But the coded layer carries
its own quantifications on identical rows, so the comparison can be made *within* one
coding, where no corpus difference can explain the result.

Those rows carry an impact profile across 18 outcome domains — what a development did
to the world — and a prerequisite edge list — what depends on it. That yields five
measures of importance for the same 150 rows. Rank correlations, **on the raw coded
magnitudes**:

| | consequence | breadth | peak | necessity | prerequisites |
|---|---|---|---|---|---|
| **consequence** (sum of coded effects) | 1.00 | 0.74 | 0.71 | **−0.30** | +0.30 |
| **breadth** (domains touched) | 0.74 | 1.00 | 0.16 | **−0.32** | +0.08 |
| **peak** (largest single effect) | 0.71 | 0.16 | 1.00 | **−0.15** | +0.37 |
| **necessity** (transitive reach) | −0.30 | −0.32 | −0.15 | 1.00 | −0.08 |
| **prerequisites** (backward count) | +0.30 | +0.08 | +0.37 | −0.08 | 1.00 |

The matrix is **two blocks that oppose each other**. The upper-left block — consequence,
breadth, peak — is what a development *did*: internally correlated 0.16 to 0.74. The
lower-right block is what *rests on* it. **Every correlation between the two blocks is
negative** (−0.08 to −0.32), mean off-diagonal magnitude 0.320.

So "importance" is not one quantity with measurement noise. The two senses are
**opposed**: the developments that changed the world most are, weakly but consistently,
the ones the fewest later developments depend on. That is the paper's claim in its
strongest form, and it needs no comparison between instruments or corpora — it is five
measures on 150 identical rows, in one coding.

The negative sign also rules out the obvious sceptical reading. If the coder had let
prominence contaminate the magnitudes, consequence would correlate *positively* with
necessity. It does not; the sign runs the other way, so the coded magnitudes are not a
restatement of structural position.

Two smaller notes. `prerequisites` against `necessity` is −0.08, i.e. a node's ancestor
count says nothing about its descendant count — a consistency check on the graph that
it passes. And the three outcome summaries are partly redundant (breadth with
consequence 0.74), the same redundancy problem met in Section 4.2 in the other
instrument.

**One implementation, not three.** An earlier version of this table reported the
opposite signs, and the cause was not the statistics but the code: transitive reach had
been written three times, and the copy used here counted *ancestors* instead of
descendants, inverting the direction. It was caught because two implementations
disagreed — one put the infinitesimal calculus first, the other put a recent
transformer paper first — and the disagreement was investigated rather than averaged.
`linkage.reach_from_rows` is now the only implementation, and every number in this
paper comes from it.

**The result survives the two checks that killed other findings here.** It is computed
on the raw coded magnitudes, not on any transform of them — a distinction that matters,
because a transform that propagates effects through the graph subtracts downstream
effect from upstream nodes by construction and can flip a sign. And it uses midrank
Spearman, which matters because `peak` takes only four distinct values and tie handling
alone moved one of these correlations from 0.43 to 0.45 to 0.62 under three
treatments. Two guards follow for any composite measure: **report a correlation on the
raw coding as well as any transformed version, and use midrank ranks on coarse data.**

Two smaller observations from the corrected table. The three outcome summaries are
partly redundant — breadth with consequence at 0.75, peak with consequence at 0.72 —
so the outcome matrix is closer to two measures than three, the same problem met in
Section 4.2 in the other instrument. And `downstream share` correlates with necessity
at 0.88, a fourth instance of a criterion that restates another.

## 8. Robustness

**Transitive reach has no free parameter, and that is why it is the measure.** The
natural alternative propagates each development's effect through the graph, and it
carries an attenuation factor saying how much credit an upstream enabler receives per
hop. Sweeping that factor across 0.0–0.95 produces six distinct top-ten *sets*, so the
ordering is a property of the parameter. Reach is a count of nodes in a closure, so
the only modelling decision behind it is that "depends on" is transitive.

**Depth per field is a comparability budget, not a free parameter.** The corpus takes
the twenty most-cited works per field. Deepening it to fifty was tried and made the
result *worse*: the extended top fifteen acquired entries such as a 2024 report on two
Later Stone Age sites, with a worst-cross-criterion rank of 1,289 out of 1,300. The
cause is not data quality but scale — the twentieth most-cited work in Archaeology has
tens of citations and in Biochemistry tens of thousands, so taking fifty works per
field admits the tail of small fields, where absolute counts are meaningless. Twenty
keeps every entry inside a band where they are not.

**The rubric saturates, so no acceleration claim appears anywhere.** Test information
at the top decile of coded magnitudes is 1.2% of its peak. The rubric cannot
distinguish among the largest developments, so a claim that some era accelerated would
be an artefact of the ceiling.

**The 150 coded rows are a small sample of a large universe, and the gap is measured.**
The rows were chosen by judgement. The defence is not to code more — that multiplies
the same judgement — but to enumerate a systematic universe from a third party and
report the residual. Wikidata was queried for every item with a discovery or invention
date and at least four Wikipedia language editions: **44,918 candidates**, of which
**32 match a coded row** (0.071%). The residual is large but mostly a unit mismatch —
a discovered element is not an intervention — and it is now bounded over two orders of
magnitude more candidates than the 400 the earlier attempt used.

**The coarse coding layer was retired.** An earlier version coded 55 broad
developments (printing, electromagnetism) alongside the 150 results, on the same
schema. Comparing the two resolutions gave a top-10 overlap of 0.30 and a mean
within-parent dispersion of 0.233, with 40 coarse rows declaring effects below what
their own children claim. A coarse row is a bag of related things rather than one
intervention, so the fine layer is used throughout and the coarse layer is not in this
repository.

---

## 9. Limitations

**The dependency graph is single-coder, and its reliability is unmeasured.** The 150
rows and 143 edges were coded by one person, who is also the author of this paper, who
also chose the corpus, the measures and the criteria. Every edge is now traceable to a
source and the graph passes chronology and acyclicity audits — but those are *internal*
consistency checks, and a single coder can pass every internal check and still be wrong
in the same way throughout.

The reliability measurement is set up and its result is withheld, because the person who
would produce it is the person who produced the coding. `scripts/reliability.py` exports
a stratified, blinded sample of 40 edges — half from the top of the reach ranking, where
a disagreement changes the headline — with the primary verdict withheld. A second coder
fills in `necessary: true/false` per edge and `--score` reports Cohen's κ with the full
confusion counts. Until that file exists the script prints that reliability is
unmeasured, and no substitute number is offered: self-agreement would be worthless, and
an LLM re-derivation would be circular in exactly the way this paper is about.

The remaining repairs, in order of value: a second coder for the 40-edge sample; a
dedicated citation per edge rather than an inherited warrant; and citation-*intent*
classification, which needs the sentences around a citation and is the one experiment
that could falsify Section 5 rather than corroborate it. `scripts/fetch_contexts.py` is
written and waiting on a Semantic Scholar key.

**The bibliometric corpus is the elite tail.** Twenty most-cited works per field is the
top of the citation distribution, which is exactly where instrumentation is
over-represented and where the use/necessity confound is largest. It is a sample of the
extreme, not of the literature.

**The two degenerate criteria are structural to that sample, not to the fetch.**
`top_citations` counts how many of the 520 seeds cite a work, and the seeds are by
construction the *most recent* most-cited works in each field, which mostly cite work
older than themselves. Two seeds can cite the same work only if it precedes both and is
prominent enough to appear in both reference lists, and that intersection is small
whatever the reference cap — tripling the cap from 20 to 100 moved the distinct values
from five to seven and from three to four, and both criteria are still dropped. A
corpus selected to *include* the cited works rather than only the citing ones would fix
it, and that is a different study.

**Method/theory classification is not measurable with the tools used here**, which is
why two findings were withdrawn rather than reported. Section 10 gives the numbers.

**The dependency ranking is age-confounded and this was not corrected.** A result from
1665 has had three and a half centuries to accumulate dependants; one from 1970 has had
fifty years. Against this, the top ten spans 1665 to 1943 — so the ordering is not simply
antiquity — but the confound is real and untreated.

**The dependency graph is a hypothesis expressed as a DAG.** Its edges are binary and
citable, which makes them auditable, but audit is not identification. A different
historian would not necessarily draw the same edges from the same sources.

---

## 10. What did not survive

Five claims the project made are not in this paper, and the reasons are worth four
lines because they are the same reason four times: **a number that looked like a
measurement was inside the noise of the frame that produced it.**

**"The consensus contains exactly one theory paper, Shannon 1948, and it tops the
cross-disciplinary criterion."** The `reach` criterion took three distinct values
across 520 works, so its ranks were tie-breaks and Shannon's rank 1 was the first of
seven tied works. With it dropped, Shannon leaves the top 30, at position 35 of 520.
This is the retraction that motivated the degeneracy check.

**"Methods are cited 1.31× more often than theory, and theory's citation rate decays
faster, so the record's bias compounds with age."** Both directions reverse under a
second classifier. The title and abstract classifiers agree on only 23% of the cases
where both commit, and the abstract labels put theory *ahead* on citations (0.81) and
decaying *slower* (momentum 1.07 against 0.95). Neither direction is established, and
the method/theory split is not measurable with the lexicons available.

**"`citer_prestige` recovers foundational importance from citation structure."** It
correlates 0.65 with raw citations and its top eight are AlexNet, VGG, ResNet,
Kohn–Sham, ImageNet, Faster R-CNN, LeNet and SAMtools. This failure is retained as a
*result* rather than a retraction, because it is the strongest evidence for Section 5.

**"The instrument applies five independent criteria"** and **"24 of the top 25 works
are tools."** The first was wrong because two criteria were degenerate and one pair
redundant, leaving six effective of nine. The second was a count from that same broken
configuration; it is replaced by the checkable statement that eleven of the corrected
top twelve are instruments.

A further retraction is recorded in Section 7.3: an earlier version of the coded-measure
table reported the opposite signs, because transitive reach had been implemented three
times and the copy in use counted ancestors instead of descendants. Consolidating to
one implementation fixed it. That is the argument for the consolidation, not a
footnote.

---

## 11. Conclusion

The question was which scientific works are most important, and the answer depends on
whether "important" means used or depended on.

Measured as use, importance is instrumentation. The twelve works a careful citation
instrument ranks highest are statistics software, network architectures, an assay, a
diagnostic manual, a dataset and a data-analysis recipe. That result is robust: it
survives dropping the criteria that turned out to be broken, collapsing the pair that
turned out to be redundant, and normalising by field.

Measured as necessity, importance is the intellectual spine. The twelve results a
parameter-free dependency instrument ranks highest are the infinitesimal calculus
(58 of 150 results downstream of it), electromagnetic induction, the Carnot cycle,
the mechanical equivalent of heat, entropy and the second law, the calculus of
variations, Maxwell's equations, the Lorentz force, the H-theorem, Planck's quantum
hypothesis, the Bohr model and the Schrödinger equation. The two lists share nothing.

The reason is not that the first instrument was built badly. It was built well
enough to catch three of its own errors, one of which was the finding that made this
project look as though it had vindicated its own origin. The reason is structural:
**citation data records an untyped edge, and the difference between use and
necessity is the type.** No refinement of a bibliometric ranking can recover a
distinction the data does not carry, and the attempt we made to recover it from
within citation structure -- the PageRank-flavoured prestige measure -- returned the
same machine-learning papers as the count it was meant to correct.

Three things follow, in descending order of how confident we are.

The **degeneracy check** is the smallest and most portable contribution. Before
trusting a composite ranking, count the distinct values of each criterion. One with
five values cannot order a list of 520, and a rank of 1 on a criterion with three
values is a tie-break wearing a number's clothes. The check costs one line and it
caught three retractions in this project.

The **in-degree / transitive-in-degree distinction** is the analytical contribution.
"Cited by many" and "depended on by much" are different quantities, they are
non-monotone in each other, and only the second is what people mean. Where a
dependency relation has been coded, ranking by transitive reach produces the answer
the question deserves; where it has not, the answer is unavailable and should be
reported as unavailable rather than proxied.

Section 7.3 strengthens this from a difference into an opposition. On the same 150 rows,
what a development *did* and what *rests on* it are negatively correlated across every
pair of measures: consequence against necessity −0.30, breadth −0.32, peak −0.15. So
the two senses of importance are not merely distinct, and an instrument that averages
them — which is what a composite "impact score" does — is cancelling the quantity it
set out to measure.

The negative sign matters twice over, because it also answers the objection that a
single coder might have contaminated the magnitudes with prominence. A halo would make
that correlation positive. It is negative.

The **coded dependency layer** is the contribution we would most like someone else
to make better. It is 150 rows and 143 binary, sourced assertions, coded by one
person, with unmeasured reliability, spanning ten thousand years. It is enough to
produce a defensible list of the intellectual spine and to demonstrate that the
bibliometric list is disjoint from it. It is not enough to settle the question, and
the difference between those two statements is a second coder.

---

## Appendix: reproduction

Everything above is produced by committed code from a committed corpus, offline.

```bash
pixi run gate                      # lint, mypy, tests
pixi run analyse                   # coded-layer analysis -> reports/results.json
pixi run figures-openalex          # bibliometric figures -> reports/fields.json
python scripts/make_contrast.py    # the central figure -> reports/contrast.json
python scripts/fetch_literature.py # verify the related-work anchors against Crossref
pixi run validate                  # schema + provenance
world-impact verify-sources        # verify the bibliography against Crossref
pixi run docs-build                # mkdocs, strict
```

The outputs of both verification commands are committed, so the provenance claims in
Section 2.1 can be checked without network access:
`data/literature/bibliography-verification.json` (all 119 bibliography entries with
their similarity to the best Crossref match) and `data/literature/verified.json` (the
27 related-work anchors, with the 10 rejections and their reasons).

The bibliometric corpus (`data/openalex/corpus.json`: 520 seeds and 5,870 referenced
works) and the citer cache (`data/openalex/citers.json`) are committed, so no network
access is required to reproduce any number in this paper. The coded layer is
`data/results.yml`, `data/outcomes.yml` and `data/edges.yml`. The decision log,
including every retraction above, is in the commit history; the detailed result tables
are regenerated into `reports/` by the commands above.

Data is CC-BY-4.0; code is MIT.

---

## References

Verification status is part of the reference list. `verified` means Crossref
returned a record at ≥ 0.90 title similarity with an agreeing version year, and the
DOI given is that record. `unverified` means no such record was returned; the entry
is a real work cited from knowledge, and the reader should treat its bibliographic
details as unconfirmed. Two of the eighteen works cited below are unverified, which
is the yield of the procedure described in Section 2.1.

| key | work | DOI | status |
|---|---|---|---|
| aksnes2019 | Aksnes, D. W., Langfeldt, L. & Wouters, P. (2019). Citations, citation indicators, and research quality. *SAGE Open* 9(1). | 10.1177/2158244019829575 | verified |
| macroberts2010 | MacRoberts, M. H. & MacRoberts, B. R. (2009). Problems of citation analysis: a study of uncited and seldom-cited influences. *JASIST* 61(1). | 10.1002/asi.21228 | verified |
| seglen1997 | Seglen, P. O. (1997). Why the impact factor of journals should not be used for evaluating research. *BMJ* 314, 497. | 10.1136/bmj.314.7079.497 | verified |
| teufel2006 | Teufel, S., Siddharthan, A. & Tidhar, D. (2006). Automatic classification of citation function. *EMNLP 2006*. | 10.3115/1610075.1610091 | verified |
| jurgens2018 | Jurgens, D., Kumar, S., Hoover, R., McFarland, D. & Jurafsky, D. (2018). Measuring the evolution of a scientific field through citation frames. *TACL* 6. | 10.1162/tacl_a_00028 | verified |
| cohan2019 | Cohan, A., Ammar, W., van Zuylen, M. & Cady, F. (2019). Structural scaffolds for citation intent classification. *NAACL 2019*. | 10.18653/v1/n19-1361 | verified |
| park2023 | Park, M., Leahey, E. & Funk, R. J. (2023). Papers and patents are becoming less disruptive over time. *Nature* 613, 138–144. | 10.1038/s41586-022-05543-x | verified |
| funk2017 | Funk, R. J. & Owen-Smith, J. (2017). A dynamic network measure of technological change. *Management Science* 63(3). | 10.1287/mnsc.2015.2366 | verified |
| wang2013 | Wang, D., Song, C. & Barabási, A.-L. (2013). Quantifying long-term scientific impact. *Science* 342, 127–132. | 10.1126/science.1237825 | verified |
| chen2007 | Chen, P., Xie, H., Maslov, S. & Redner, S. (2007). Finding scientific gems with Google's PageRank. *Journal of Informetrics* 1(1). | 10.1016/j.joi.2006.06.001 | verified |
| walker2007 | Walker, D., Xie, H., Yan, K.-K. & Maslov, S. (2007). Ranking scientific publications using a model of network traffic. *J. Stat. Mech.* P06010. | 10.1088/1742-5468/2007/06/p06010 | verified |
| freeman1979 | Freeman, L. C. (1978). Centrality in social networks: conceptual clarification. *Social Networks* 1(3). | 10.1016/0378-8733(78)90021-7 | verified |
| bloom2020 | Bloom, N., Jones, C. I., Van Reenen, J. & Webb, M. (2017). Are ideas getting harder to find? *NBER WP 23782*. | 10.3386/w23782 | verified |
| gilardi2023 | Gilardi, F., Alizadeh, M. & Kubli, M. (2023). ChatGPT outperforms crowd workers for text-annotation tasks. *PNAS* 120(30). | 10.1073/pnas.2305016120 | verified |
| ziems2024 | Ziems, C., Held, W., Shaikh, O., Chen, J., Zhang, Z. & Yang, D. (2024). Can large language models transform computational social science? *Computational Linguistics* 50(1). | 10.1162/coli_a_00502 | verified |
| messeri2024 | Messeri, L. & Crockett, M. J. (2024). Artificial intelligence and illusions of understanding in scientific research. *Nature* 627, 49–58. | 10.1038/s41586-024-07146-0 | verified |
| turchin2018 | Turchin, P. et al. (2017). Quantitative historical analysis uncovers a single dimension of complexity. *PNAS* 115(2). | 10.1073/pnas.1708800115 | verified |
| bornmann2008 | Bornmann, L. & Daniel, H.-D. (2008). What do citation counts measure? A review of studies on citing behavior. *Journal of Documentation* 64(1), 45–80. | 10.1108/00220410810844150 | verified |
| mccain2014 | McCain, K. W. (2014). Assessing obliteration by incorporation in a full-text database: JSTOR, Economics, and the concept of "bounded rationality". *Scientometrics* 101, 1445–1459. | 10.1007/s11192-014-1237-3 | verified |
| garfield1975 | Garfield, E. (1975). The obliteration phenomenon. *Current Contents* 31, 5–7. | — | **unverified** |
| deridder2013 | de Ridder, J. (2013). Epistemic dependence and collective scientific knowledge. *Synthese* 191(1). | 10.1007/s11229-013-0283-3 | verified |
| west2002 | West, R., McIlwaine, A. & Stanbrook, M. (2002). What do citation counts count for in the field of addiction? *Addiction* 97(4). | — | **unverified** |
| jones2009 | Jones, B. F. (2009). The burden of knowledge and the "death of the Renaissance man". *Review of Economic Studies* 76(1). | — | **unverified** |
| page1999 | Page, L., Brin, S., Motwani, R. & Winograd, T. (1999). The PageRank citation ranking: bringing order to the web. *Stanford InfoLab TR*. | — | **unverified** |

Two further works are cited in Section 2.1 as examples of *failed* verification and
are not part of the bibliography above: Merton's "The Matthew Effect in Science"
(*Science* 159, 1968), for which Crossref returns a book chapter at 0.77 similarity;
and Fortunato et al.'s "Science of science" (*Science* 359, 2018), for which Crossref
returns no match at all.











