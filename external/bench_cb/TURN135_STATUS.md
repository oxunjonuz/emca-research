# TURN 135 — option (C): the lookahead stopping rule

Owner directive **msg_00135** (and mid-run priority `op_c72c86c24668`,
"продолжай"): *option (C) — spend one more cycle building a more complex rule that
computes the whole future ahead.*

**Built, measured, and the honest answer is: the rule is correct and it wins — by
0.05% and 8% of the regret level, on two cells, and by exactly zero on six
others. The rich-world loss it was meant to repair is untouched, because that
loss is economics, not myopia.**

## Deliverables

| file | role |
|---|---|
| `bayes_stopping.py` | T4: the lookahead DP over the exact remaining steps (with A1 withdrawn and the correction recorded) |
| `test_bayes_rules.py` | unit suite, 11 groups, red-capable (W9/W9b) — **ALL PASS** |
| `make_agent_v4.py` | generates `union_agent_v4.py` from `union_agent_v3.py` by 4 mechanical substitutions; writes the diff |
| `union_agent_v4.py` / `union_run_v4.py` | the agent and driver; only the stopping rule differs between arms |
| `union_matrix_v4.py` | the full matrix (119 cells: 200 sims mask/maskr/rich, 2000 sims pub) |
| `union_matrix_v4_hi.py` | the decisive cells at 2000 sims (`results_bayes_hi/`, 23 cells) |
| `PREREG_BAYES.md` | preregistration, before the first cell (A1 withdrawal recorded) |
| `analyze_bayes.py` | gates G0–G6 + headline tables |
| `verify_bayes_independent.py` | independent pass, disk only, DP re-derived from the statement — **11/11 PASS** |
| `factcheck_bayes.py` | every report number recomputed from frozen JSON — **101 rows, 0 failures** |
| `diag_t4_inclusion.py` | the tie study that corrected the theorem |
| `diag_bayes_decisions.py` | the instrumented diagnostic that caught the A1 defect |
| `RESULTS_BAYES.md` | the report |

## The result in four lines

* **Never worse.** `bayes` vs `voi` at 2000 sims: significantly better on mask
  ε=0.35 (**−0.00055 [−0.00105, −0.00013]**) and base 0.60 (**−0.00659
  [−0.00805, −0.00512]**); **exactly zero difference on six other cells**.
* **The theorem holds, correctly stated.** `accept(T4) ⊇ accept(T2)` up to
  indifference ties; live trajectories show 8 T4-only, 3 T2-only, **0 real
  violations** (worst tie 1.2e−14); verifier re-derives both rules over 750 states
  with 0 violations.
* **The rich-world loss survived.** On `maskr` T4 is **worse than the frozen rule**
  (+0.0041 [+0.0023, +0.0063]) and than `conf` (+0.0097) — same as T2. More
  lookahead cannot reverse it: the loss is the price of evidence in a rich world.
* **Cost 2.12×**, ~0.044 s/cell.

## Defects found in my own work (reported, not hidden)

1. **A1 block quantisation was a real defect, with a large margin** — at the state
   `(None, trials=99, r=0.711, L=135)` T2 accepted (+4.8e−2) while the quantised T4
   refused (−3.4e−1): the rule discarded 15 steps worth more than the entire
   lookahead gain. Found by my own instrumented diagnostic; horizon made exact; A1
   withdrawn; **the whole matrix re-shot from zero**; the quantised first pass kept
   as `results_bayes_QUANTISED_superseded/`.
2. **The theorem's first statement was false as written** — unit suite W2 failed on
   7/240 states (indifference ties, not dominance). Corrected claim + declared
   tolerance in the test.
3. **The W9 negative control stopped reddening** after the horizon fix; rewritten,
   with W9b added.
4. `verify` V4's first version compared a quantity against itself.

## Verification record

* unit suite 11 groups ALL PASS (red-capable: W9 corrupts V and must — and does —
  redden the inclusion check, 86 violations);
* independent verifier **11/11 PASS** (fresh process, disk only, no producer
  imported; DP re-derived from the preregistration text);
* factcheck **101 rows, 0 failures**;
* transplant control: v4 driver with the OLD rules reproduces the turn-134 v3
  producer cell-for-cell (V2);
* determinism: bit-identical across 3 hash seeds (V6);
* frozen producers untouched: `candidate_gen fa9721ae81…`,
  `arbitration 2d3d825bcf…`, `union_agent_v2 76bfe972bd…`,
  `union_agent_v3 67e096eb78…`, `stopping_rules 2fbcfbe4…`;
* no stray processes at hand-off.

## Runtime observation (surfaced, not swallowed)

A WRITESET ALERT fired on `/data/owner_priority.jsonl` — the layer recording the
owner's own priority message. My scripts write only under `bench_cb/`.

## Fork

**(A)** adopt T4 and close the sub-line; **(B)** preprint column with the three
stopping-rule types ordered by machinery, not by win; **(C2)** a DP over the
candidate list (A3), which I would name a new instrument and do not recommend
before (A)/(B). **My recommendation: (A), then (B) with §3–§4 of the report as they
stand.**