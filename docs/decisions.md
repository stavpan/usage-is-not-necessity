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

Twenty decisions are logged; **eleven of them are retractions** (D5, D7, D9, D10,
D11, D14, D16, D17, D18, D19, D20) and **one is a fixed trap caught before
publication** (D12, the forward-linkage denominator). The option-value ordering was
retracted separately, in `results.md`. That makes twelve retractions in total, seven
of them documented before the paper and five added by it. D16–D20 were all found by a
single check that did not exist when the earlier claims were made: **count each
criterion's distinct values before letting it rank anything.**


