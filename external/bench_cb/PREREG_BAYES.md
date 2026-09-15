# PREREG_BAYES.md — turn 135

**Written BEFORE the matrix runs.** §5 declares pilot observations I have ALREADY
looked at, so no reader has to guess which predictions are post hoc. Everything
else is written before the first matrix cell.

Owner directive **msg_00135**: option **(C)** — *"spend one more cycle building a
more complex rule that computes the whole future ahead."*

---

## §1 What is being built, and what it replaces

Turn 134 replaced the frozen threshold rule with **T2** (`voi`), a ONE-STEP
lookahead: probe `n` steps, then commit. T4 (this turn) solves the actual optimal
stopping problem — after a probe the agent may probe AGAIN:

```
V(a,b,0) = 0
V(a,b,m) = max( m*n*max(mu, r) ,  n*mu + sum_k P(k;n,a,b) * V(a+k, b+n-k, m-1) )
```

`P(k;n,a,b)` is the exact Beta-Binomial predictive (closed form, no RNG). The rule
accepts a candidate iff the optimal policy PROBES at that state. Module:
`bayes_stopping.py`.

**This is named a NEW INSTRUMENT, not the campaign's mechanism.** The campaign's
mechanism is the frozen threshold rule; T4 is my construction, and any verdict it
earns is a verdict about T4.

## §2 The theorem, stated correctly (and a correction I owe)

Since `V >= commit` at every state, `probe_value_T4 >= probe_value_T2` at every
state, so **accept(T4) contains accept(T2)**.

**Correction, made before the matrix ran.** I first wrote this as a plain set
inclusion. My own unit suite W2 **failed** on 7/240 grid states. The cause is not
dominance: in those states the probe is exactly worthless, so both rules sit on
the indifference point — T2's margin is `+2.2e-15` (float noise) and T4's is
exactly `0.0`, and they break the tie differently. A wide scan
(`diag_t4_inclusion.py`, 2240 states) finds **0** violations with a T2 margin
above `1e-12`, **111** ties (worst `8.4e-14`), and **138** states where T4
strictly accepts and T2 does not. The corrected claim, now in both the module
docstring and the test:

> accept(T4) contains accept(T2) **up to indifference ties**, and is **strictly
> larger** wherever the probe has positive expected value.

The suite tests the corrected claim with the tolerance declared in the test
(`TIE_TOL = 1e-12`); the negative control W9 (V := commit) still reddens it.

## §3 Declared quantities and approximations

`n` = steps in one probe (asserted equal to the campaign's own `PROBE_BLOCK`),
`m = floor((T-t)/n)` whole blocks remaining (`T-t` observed), prior `Beta(1,1)`
(a COUNT), `r` observed. **NO GAIN_UNIT, no β, no PROBE_COST** (unit test W6,
AST-level).

* **A1 ~~block quantisation~~ WITHDRAWN.** The first version quantised the
  horizon to whole probe blocks (`m = floor((T-t)/n)`) and treated the `< n`
  remainder as commit-only. **The instrumented diagnostic falsified this as an
  approximation, before the re-shot matrix:** at the state actually visited on
  `mask` (`rate_a=None, trials=99, r=0.711, L=135`) T2 accepted (margin
  `+4.8e-2`) while the quantised T4 refused (margin `-3.4e-1`), because the rule
  valued that state as if only 120 steps were left. **The discarded 15 steps were
  worth more than the entire lookahead gain** — so A1 was not a small error term,
  it was a different rule. The DP now carries `L` exactly in steps: no block
  quantisation, no tail approximation. The first-pass matrix produced by the
  quantised version is preserved as evidence in
  `results_bayes_QUANTISED_superseded/` and is NOT reported as the result; the
  matrix below is re-shot from zero on the corrected rule, same instances, same
  seeds. Declared costs that remain: A2, A3, A4, A5.
* **A2 the alternative is a point** (inherited from turn 134, L4).
* **A3 one candidate at a time** — same scope as T2, so the comparison is
  like-for-like.
* **A4 the DP's objective is the candidate's own reward, not episode regret.**
  The gap between the two is what the matrix measures.
* **A5 memo cap** — clearing costs time, never correctness.

## §4 Gates, fixed before the run

Instances: `mask` eps ∈ {0.15, 0.25, 0.35}; `maskr` (base 0.8) eps ∈ {0.25, 0.35};
richness family `mask@base` for base ∈ {0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90,
0.95} at eps = 0.35; `pub` m ∈ {2, 8, 16, 49}. T = 400.

* **G0 transplant control.** Arm `bayes` must be the ONLY new arm; arms
  `frozen_rule` and `voi` run through the **v4** driver must reproduce the turn-134
  **v3** producer cell-for-cell. *(Already checked on 2 pilot cells: IDENTICAL.)*
  If it fails, NO other verdict is reported.
* **G1 the new rule must act.** `bayes` records ≥1 probe on ≥80% of `mask` cells.
* **G2 derived silence.** `bayes`' mean probes must be non-increasing in the
  world's richness `base` (Spearman ρ ≤ 0 allowed slack 0). If probes are FLAT in
  richness, T4 has not replaced the price, it has renamed it.
* **G3 regret.** `bayes` vs `voi` and vs `frozen_rule` on `mask`, `maskr`, `pub`:
  two-sided, bootstrap 95% CI + sign test. **NO direction is preregistered as
  expected** — the gate is that the difference is MEASURED with its CI.
* **G4 the theorem's empirical shadow, measured honestly.** The theorem is about
  the accept set at a FIXED state, not about trajectory totals: probing more
  consumes blocks, so the trajectories diverge and probe counts are NOT
  predicted to be ordered. Preregistered prediction **P1**: `bayes`' probe count
  on `mask` is NOT required to exceed `voi`'s; what IS required is that on the
  richness family, wherever `voi` still probes, `bayes` probes at least as often.
  This is declared because §5 shows it is already partly the case.
* **G5 controls that must behave.** `beta0` probes 0; `pure` probes 0;
  `union_nocost` probes ≥ both new rules everywhere.
* **G6 cost.** `bayes`' wall-clock per cell is reported; if the DP makes the
  2000-sim cells infeasible, the cell is run at the largest feasible nsim and the
  reduction is DECLARED, not hidden.

**Honest register for method.** `test_bayes_rules.py` is a RED-CAPABLE suite (W9
negative control must fail an assertion); it was run and its output goes in the
report verbatim. It already caught one real error (§2).

## §5 Pilot observations ALREADY SEEN (declared, so they are not predictions)

10 seeds, T = 400, mean regret / mean probes:

| arm | mask eps 0.35 | maskr eps 0.35 | pub m=16 |
|---|---|---|---|
| `bayes` | 0.00653 / 4.40 | 0.03100 / 0.20 | 0.03000 / 8.60 |
| `voi` | 0.00653 / 4.70 | 0.03100 / 0.00 | 0.03000 / 8.60 |
| `frozen_rule` | 0.00653 / 5.30 | 0.02525 / 1.40 | 0.00000 / 10.00 |
| `conf` | 0.00225 / 3.90 | 0.02662 / 4.00 | 0.00000 / 10.00 |
| `union_nocost` | 0.00653 / 5.70 | 0.02662 / 4.00 | — |

Two consequences, declared before the matrix:

* **`bayes` probes FEWER blocks than `voi` on mask (4.40 vs 4.70), not more.**
  This does not contradict the theorem (which is about the accept set at a fixed
  state): probing earlier consumes blocks, the trajectories diverge, and the
  totals are not ordered. It is exactly why G4/P1 is phrased as it is. If the
  matrix shows `bayes` probing LESS than `voi` while the theorem holds per state,
  that is the honest headline, not a failure to hide.
* `bayes` and `voi` are **tied on regret** in all three pilot cells, and both are
  **worse than `frozen_rule` on pub m=16 at 10 seeds** — which contradicts the
  turn-134 2000-seed result and is almost certainly a small-sample artifact of the
  pilot. The matrix runs `pub` at 2000 seeds; if the pilot's sign survives, it is
  reported as a contradiction of turn 134, not explained away.

## §6 What would make me abandon the line

If G2 fails (probes flat in richness), T4 is not a different type of stopping rule
but a more expensive formula for the same bar, and the honest report says so. If
G0 fails, nothing is reported at all.

## §7 Out of scope / not attempted

* No new world; the frozen instances are used as they are.
* No change to `candidate_gen.py`, `arbitration.py`, `arbitration_scaled.py`,
  `stopping_rules.py`, `union_agent_v2.py`, `union_agent_v3.py`.
* The DP does not model the other candidates competing for the same blocks (A3);
  a multi-candidate DP is NOT attempted.