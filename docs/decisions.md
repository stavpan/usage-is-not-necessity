# Decision log, including retractions

Every entry is a claim that was made, and what happened to it. Retractions are
kept rather than deleted: a project whose whole argument is "measurement choices
dominate conclusions" cannot hide its own.

| # | Claim or choice | Status | What settled it |
|---|---|---|---|
| D1 | Nine axes, invented in prose before any computation | **fixed** | Axes are now derived as principal modes; the count is an output |
| D2 | Exactly nine axes | **fixed** | Nine was fitted to a prompt, which is the worst possible provenance for a parameter. Count now comes from parallel analysis |
| D3 | Observables written to give each axis support | **fixed** | Domains taken from the reporting structure of the major long-run measurement programmes |
| D4 | Rows normalised to sum to 1 | **fixed** | The simplex forces axes to be substitutes and makes any uniform error invisible. Absolute magnitudes now |
| D5 | "Uniqueness" measured as 1 − R² | **retracted as ill-posed** | Under the simplex, Σⱼ A[:,j] = 1⃗, so with an intercept R² = 1 exactly for every axis. Only an angle is identifiable |
| D6 | ±15% lognormal perturbation as the robustness test | **replaced** | It perturbs magnitudes, not structure, and leaves both margins intact. Now: Morris screening (SALib) + row-shuffle + margin-preserving swap |
| D7 | "Effective rank of the explanatory matrix is 3–5" | **RETRACTED** | Calibrated against a permutation null: real 3.45 vs null 3.65 (95% band 2.96–4.14). Inside the band. It was a property of a 9-column design with hand-written rows, not of history |
| D8 | Single-linkage deduplication of developments | **fixed (bug)** | It chained: "fiat money" merged with "antibiotics" through a sequence of pairwise links. Complete linkage now, and a test asserts it |
| D9 | Row-uniform errors are treated as uncertainty | **retracted as unidentifiable** | A factor applied to every entry of a row cancels in normalisation, so the answer is bit-identical. Any error uniform across axes within one observable is invisible to this design |
| D10 | Leave-one-out regression for non-substitutability | **retracted as degenerate** | With more rows than columns every row lies exactly in the span of the others, so the residual is identically zero for every development — the mirror of D5. Replaced by nearest-neighbour cosine |
| D11 | Tensor "diagonal share" reported against a uniform baseline | **RETRACTED** | 13.7% vs 2.8% looked like a 4.9× concentration, but against an era-shuffled null (12.8%, 95% 10.0–14.8) it is not above chance. The uniform baseline was not a null |
| D12 | `forward_linkage = (total − direct) / direct` as the headline | **fixed before publication** | The denominator is the development's own direct impact, so the ratio rewards small-footprint nodes — which knowledge rows are *by construction*. Using it would have manufactured the result the analysis existed to test. Headline is now the bounded downstream share plus structural reach, with the trap asserted in a test |
| D13 | Index arrays used after `rows.sort()` | **fixed (bug)** | Positions no longer matched the matrix rows, producing nonsense merges. The original index is carried explicitly |
| D14 | A linear decomposition can rank a pervasive enabler | **retracted as impossible** | Verified: σ(1.5·A) = 1.5·σ(A) with identical directions. A factor that multiplies everything leaves no trace. Growth accounting, not factor analysis, is the instrument for that claim |
| D15 | Quantum mechanics and other bodies of knowledge were absent | **fixed** | They are not deployable interventions, so they could never be matrix rows. Added as rows *plus* an enabling graph, so their effect is mediated rather than direct |
| D16 | `reach` and `top_citations` are legitimate criteria | **RETRACTED — degenerate** | Across 520 works `reach` takes **3** distinct values and `top_citations` **5**, so their top ranks are tie-breaks. Seven works tie at the maximum `reach` and occupy ranks 1–7 in sort order. Cause: 20 references captured per seed, so seeds rarely cite each other. Both are now dropped and named; a criterion must take ≥ 10 distinct values to rank |
| D17 | Exactly one work is in the top 50 of every criterion (the Folin assay), and Shannon 1948 is the consensus's only theory paper and holds rank 1 on cross-disciplinary reach | **RETRACTED — tie-break artefact** | Shannon's rank 1 on `reach` was the first of seven tied works. Under the corrected criterion set no work is unanimous (maximum support 5 of 7), and Shannon falls out of the top 30 to position 35. On discriminating criteria Shannon is 471st of 520 on field-normalised rate. This was the finding that made the project look as though it had vindicated its own origin |
| D18 | The knowledge layer occupies the top of the downstream-share ranking | **retracted as untestable on the fine layer** | Zero of the 150 fine rows carry the `knowledge_layer` flag — it exists only on the 55-row coarse layer, which D19 shows is not a legitimate unit. So the fine-layer verdict "NOT SUPPORTED" is vacuous: there was nothing to test. Reported as vacuous rather than as evidence either way |
| D19 | The 55-row coarse layer and the 150-row fine layer are two resolutions of one thing | **retracted — coarse is not a unit** | Top-10 overlap between resolutions is 0.30, mean within-parent dispersion 0.233, and 40 coarse rows declare effects below what their own children claim by a full rubric level. A coarse row is a bag of related things, not one intervention |
| D20 | `citer_prestige` recovers foundational importance from citation structure | **retracted — it is citations one hop out** | Rank correlation with raw citations is 0.65, and the top eight by citer prestige are AlexNet, VGG, ResNet, Kohn–Sham, ImageNet, Faster R-CNN, LeNet and SAMtools — seven machine-learning architectures. The PageRank intuition returns the usage ranking with extra steps, which is the strongest single piece of evidence that necessity cannot be recovered from an untyped edge |
| D21 | "119/119 bibliography entries matched to a DOI" | **RETRACTED — a DOI hit is not verification** | Crossref returns its best guess for any query, so an ungated match rate rises toward 100% regardless of correctness. The checker now grades hits into `verified` / `plausible` / `weak` / `unmatched` on title similarity **and** year agreement. True yield: 27 verified, 59 plausible, 21 weak, 12 unmatched out of 119 |
| D22 | The 143 prerequisite edges are auditable claims | **retracted — zero carry a source** | `edges.yml` has no `sources` field, so the transitive-reach ranking's entire input is unsourced assertion. The 150 rows do carry bibliographic keys, so a row's existence is attributable; the edges are not. This is the project's weakest data and the paper says so at the point of the claim rather than only in the limitations |
| D23 | The degeneracy of `reach` and `top_citations` is caused by capturing only 20 references per seed | **RETRACTED — wrong diagnosis** | Rebuilt the corpus at 100 references per seed: 3× the reference depth, 17,531 edges, in-degree maximum up from 4 to 12. Distinct values moved from 5 to 7 and 3 to 4 — both criteria still dropped. The cause is the *seed set*: a top-20-per-field sample cites older work, so mutual in-degree is bounded by the sample size, not the reference cap. The rebuild is evidence for the corrected claim rather than a repair |
| D24 | Tools get superseded and lose citations while foundations persist, so theory should have higher momentum than methods | **RETRACTED — the opposite holds** | Methods 0.98 against theory 0.87, and the gap survives age matching (1.06 against 0.80 among works aged 20–34 years). The refutation is the better finding: methods are *renewed* by each cohort of users, foundations are *absorbed* and stop being cited, so the citation record's bias against necessity compounds with age |
| D25 | "Importance is two *opposed* quantities": on the same 150 rows, every between-family correlation is negative (−0.07 to −0.41) | **RETRACTED — manufactured by the transform** | The matrix was computed on the pipeline's **mediated totals**, which propagate effects through the prerequisite graph and thereby subtract downstream effect from upstream nodes by construction. On the **raw coded magnitudes** the same five measures give all-positive correlations: consequence vs necessity +0.42, peak vs necessity +0.62. The sign was a property of the mediation, not of the coding. **Guard: report a correlation on the raw coding as well as on any transformed version, because a transform can flip a sign.** The check that caught it was computing the same correlation twice |
| D26 | The 143 fine-layer prerequisite edges are unauditable because a `requires: [id]` list has no slot for a per-edge source | **fixed** | `data/edge-sources.yml` now gives every edge the union of its two endpoints' declared sources: 143/143 warranted, mean 1.55 sources, 76 resting on a single source. This is *traceability*, not verification — a source documenting a result does not assert that its prerequisite was necessary for it — and the distinction is in the file header and the paper. Two audits run on the same graph: chronology (0 violations) and acyclicity (0 cycles) |
| D27 | Methods are cited 1.31× more often and 1.75× faster than theory | **RETRACTED — classifier artefact** | Fetched abstracts for 338 of 520 seeds (the key made it possible) and classified from abstract text. The title and abstract classifiers agree on only **23%** of cases where both commit, and under the abstract labels the citation ratio **inverts to 0.81** — theory cited more often. A direction that flips under a plausible alternative measurement is not established. The table stays in the paper because deleting it would hide the disagreement |
| D28 | Theory's citation rate decays faster than methods', age-matched, so the citation record's bias against necessity compounds with age | **RETRACTED — classifier artefact** | Under abstract-based labels the age-matched momentum gap also inverts: 0.95 method against **1.07** theory, i.e. theory decays *slower*, which is the hypothesis D24 had "refuted". Neither direction is established, because neither classifier is good enough: the abstract lexicon commits on 64 works and the title lexicon is near-uncorrelated with it. The honest statement is that the method/theory split is not measurable with the lexicons available |

## The five claims that survived, and their status

1. **The outcome domains co-occur non-randomly.** Row-shuffle and
   margin-preserving swap both reject at p < 0.001 with thousands of realized
   swaps. `measured` in the sense that the nulls are computed; `derived` in that
   the cells are coded.
2. **The effective rank is small but criterion-dependent.** 3 to 4 dimensions,
   with the four criteria disagreeing. Reported as a range on purpose.
3. **The rubric saturates.** Test information at the top decile of developments
   is a stated fraction of its peak. This is why no acceleration claim appears
   anywhere in the repository.
4. **There is no league table.** Pareto frontier (weight-free) plus SMAA
   (distribution over orderings). Forced by Arrow and Sen, not by preference.
5. **Mediation changes which developments look upstream** — *restated, and partly
   withdrawn.* The original claim was that the knowledge layer occupies the top of
   the downstream-share ranking and the middle of the transitive-reach ranking. It
   cannot be tested on the fine layer, because no fine row carries the knowledge
   flag (D18), and the coarse layer on which it can be tested is not a legitimate
   unit (D19). What survives is the structural result, and it is the paper's
   central one: **transitive reach and direct impact are negatively correlated
   (Spearman ρ = −0.30)** across the same 150 rows, and the ten developments with
   the largest direct impact have a transitive reach of 0 or 1 — eight of them zero.
   Necessity and impact are not two estimates of one quantity.

## Status of the retractions, counted

Twenty-six decisions are logged; **fourteen of them are retractions** (D5, D7, D9,
D10, D11, D14, D16, D17, D18, D19, D20, D23, D24, D25) and **two are fixed traps
caught before publication** (D12, the forward-linkage denominator; D26, the missing
per-edge source slot). The option-value ordering was retracted separately, in
`results.md`. That makes fifteen retractions in total, seven of them documented before
the paper and eight added by it.

Four distinct failure modes produced them, and each now has a named guard:

| mode | instance | guard |
|---|---|---|
| a criterion that cannot discriminate | D16, D17 — `reach` had 3 distinct values and put Shannon at rank 1 | count distinct values before letting a criterion rank |
| a criterion ranking on missing data | the citer criteria over a corpus where the cache covered 40% of rows | require ≥95% input coverage, or drop and name |
| a transform that flips a sign | D25 — mediation turned +0.42 into −0.20 | report every correlation on the raw coding as well as the transformed version |
| a hypothesis treated as a finding | D23 (wrong diagnosis, never tested against a rebuild), D24 (durability, refuted) | rebuild the data and re-run before publishing a mechanism |


