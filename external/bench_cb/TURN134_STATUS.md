# TURN 134 — a stopping rule of a different type

Owner directive **msg_00134**: *"the next, genuinely interesting step is not to
tune the current price, but to design a fundamentally different type of stopping
rule, not based on directly comparing quantities incommensurable by nature
(probability vs reward)."*

**Done. The type was replaced and measured; the specific rule I wrote wins on the
published instance and loses on ours.**

## Deliverables

| file | role |
|---|---|
| `stopping_rules.py` | the three rule types (T2 `voi`, T2b `voi_rate`, T3 `conf`) + the frozen rule as a delegated control |
| `test_stopping_rules.py` | unit suite, 9 groups, red-capable (W8 negative control) — **ALL PASS** |
| `make_agent_v3.py` | generates `union_agent_v3.py` from frozen `union_agent_v2.py` by 4 mechanical substitutions; writes `union_agent_v3.diff` |
| `union_agent_v3.py` / `union_run_v3.py` | the agent and driver; only the stopping rule differs between arms |
| `union_matrix_v3.py` | the matrix (170 cells @200 sims, 85 cells @2000) |
| `PREREG_STOPPING.md` | preregistration, written before the first matrix cell |
| `analyze_stopping.py` | gates G0–G5 + headline tables |
| `verify_stopping_independent.py` | independent pass, disk only, different code — **13/13 PASS** |
| `factcheck_stopping.py` | every report number recomputed from frozen JSON — **ALL PASS** |
| `diag_sensitivity_v3.py` | which declared number moves which verdict |
| `RESULTS_STOPPING.md` | the report |

## The result in three lines

* On the **published instance** the one-currency rule **wins**: −0.0123 regret
  [−0.0156, −0.0090] at m=16, and it **stops earlier** (8.3 vs 10.0 probe blocks).
* On the **context-specific instance** the same rule **loses** on the maskr world
  (+0.0041) and, above base ~0.85, **refuses to probe at all** — a derived
  silence, Spearman ρ = −0.976 against the world's richness.
* Where T2 goes silent, **T3 (probability-only) wins**: it beats the frozen rule
  at base 0.60/0.70/0.75/0.80, up to **−0.0265 [−0.0282, −0.0248]** — i.e. in the
  middle of the richness range the correct amount of stopping is *none*.

## Structural difference (the owner's actual question)

For one fixed candidate, with the **world's** alternative rate varying 0.10…0.95,
the frozen rule answers "probe" at **all six** levels (its bar is on the score,
not the price); T2 answers "probe" at **exactly one** (0.85) — a two-sided band
around the point where learning would change the decision. T2/T3 contain **no
GAIN_UNIT, no β, no PROBE_COST** (audited by source introspection, unit test W6).

## Verification record

* unit suite 21 checks, 0 failures; independent verifier 13 checks, 0 failures;
  factcheck 60+ numbers, 0 failures — all re-run after the defect fix.
* transplant control: generated v3 agent with the OLD rule reproduces the **frozen
  v2 producer** cell-for-cell on 25 cells.
* frozen files untouched: `candidate_gen.py fa9721ae816c3c42…`,
  `arbitration.py 2d3d825bcfc83cc8…`, `union_agent_v2.py 76bfe972bde4963c…`.
* `union_agent_v3.py` sha `67e096eb7897ccb0…`; diff = 27 lines, four regions.
* no stray processes; both matrices on disk (170 + 85 cells).

## Defects found in my own work (reported, not hidden)

1. `_frozen` hardcoded `beta=1.0`, so the **`beta0` C1 control was silently equal
   to `frozen_rule`** (3.43 probes instead of 0). Caught by gate **G5**; fixed to
   pass β through; 17 `beta0` cells re-run; verification re-run.
2. My first negative control (**W8**) was ill-posed — it asserted that corrupting
   the predictive must break the rule's algebraic identity, but that identity is
   definitional. Replaced with one that must change the *decision* (1 → 0).
3. The verifier's first **V2** was a self-comparison and could not fail; rewritten
   against the frozen v2 producer.
4. **T3's first design had no stopping term at all** — declared in the
   preregistration §5 *before* the matrix, and **not** patched with a price
   (the turn-104 trap).

## Honest limits

Instance transfer is not free (wins on pub, loses on mask); T2 is myopic
(no dynamic program); `r` enters as a point, not a posterior; `voi_rate` is a
declared negative result (0.38 probes, 0.164 regret).

## Fork (owner's call)

**(A)** adopt by instance class; **(B)** close the line with this as the honest
end and write the preprint column; **(C)** one more turn for the Bayes-optimal
(lookahead) version, named as a new instrument.
