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
5. **Mediation changes which developments look upstream.** The knowledge layer
   occupies the top of the downstream-share ranking and the middle of the
   transitive-reach ranking. Reported as mixed, because that is what it is.
