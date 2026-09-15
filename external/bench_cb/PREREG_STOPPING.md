# PREREG_STOPPING.md — turn 134

**Written BEFORE the matrix runs.** Everything in §5 ("pilot observations already
seen") is declared as data I have ALREADY looked at, so no reader has to guess
which predictions are post hoc. Everything else is written before the first
matrix cell.

Owner directive **msg_00134**: *"the next, genuinely interesting step is not to
tune the current price, but to design a fundamentally different type of stopping
rule, not based on directly comparing quantities incommensurable by nature
(probability vs reward)."*

---

## §1 What is being replaced, stated in units

Frozen rule (`arbitration.py` sha `2d3d825b…`, corrected sibling
`arbitration_scaled.py`):

    probe iff  beta * GAIN_UNIT * score  >  rich_rate * PROBE_LEN + PROBE_COST
               └──── value per gap ────┘     └──── rate × duration ────┘

One side multiplies a **gap** by a **declared value-per-gap**; the other
multiplies a **rate** by a **declared duration**. Three declared numbers, none
derivable from the world; turn 132 measured that the maskr verdict flips between
`GAIN_UNIT` 200 and 400 with no world change.

This preregistration **corrects one campaign framing**: in the union engine the
fields fed to the rule are ALREADY reward rates (the agent keys `candidate_gen`
on the observed reward `"y"`), so the defect was never "probability vs reward" —
it was "value-weighted gap vs time-weighted rate". Reported, not hidden.

## §2 The three replacement types

| type | rule | what is compared with what |
|---|---|---|
| **T2** `voi` | probe iff `info > risk`, where `info = (L-n)·(E_k[max(post,r)] - cur)`, `risk = n·(cur - mu_c)`, `cur = max(mu_c, r)` | reward total vs reward total, same horizon L |
| **T2b** `voi_rate` | probe iff `(E_k[max(post,r)] - cur) > (cur - mu_c)` | reward per step vs reward per step, no horizon |
| **T3** `conf` | probe iff `q_lo < P(rate_cand > r) < q_hi` | probability vs probability; no reward magnitude anywhere |
| **T1** `frozen` | the old rule | control |

`mu_c` and its update are the agent's own Beta(1,1) posterior on the candidate's
rate; `E_k` integrates the exact Beta-Binomial predictive of `n` further pulls in
closed form (no sampling, no RNG). `L = T − t` is the agent's OBSERVED remaining
steps. `n = PROBE_BLOCK = 20`, asserted equal to the campaign's own constant.

## §3 Declared quantities, and the difference that matters

`probe_len` (STEPS), `horizon` (STEPS), prior `Beta(1,1)` (a COUNT), `q_lo/q_hi`
(confidence). **No `GAIN_UNIT`, no `beta`, no `PROBE_COST` in T2/T3.**

**A4 (the honest limit, declared now).** T2 still moves with `horizon`. It must:
how long the answer will be used is a fact about the episode, and any
decision-maker's answer changes with it. That is a different kind of dependence
from moving with a value-per-gap constant, which no fact about the world pins.
`diag_sensitivity_v3.py` measures both side by side and the report shows both
numbers rather than arguing about the difference.

## §4 Gates, fixed before the run

Instances (`build_model` imported unchanged from `union_run_v2`): `mask` eps
∈ {0.15, 0.25, 0.35}; `maskr` (base 0.8) eps ∈ {0.25, 0.35}; plus a **richness
family** `mask@base` for base ∈ {0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95} at
eps = 0.35, T = 400, 1000 seeds per cell.

* **G0 transplant control.** Arm `frozen_rule` must reproduce arm `union`
  byte-for-byte on every cell (all fields but `arm`/`seconds`/`rule_name`).
  If it fails, NO other verdict is reported. *(Already verified on 4 pilot
  cells: 0 mismatches.)*
* **G1 the new rule must act.** `voi` must record ≥1 probe on ≥80% of `mask`
  cells, else the rule is a `never` in disguise and the comparison is vacuous.
* **G2 the new rule must stop somewhere — and the stopping point must be
  DERIVED, not declared.** `voi`'s mean probes must be non-increasing in the
  world's richness `base` over the richness family (weak monotonicity, Spearman
  ρ ≤ 0 allowed slack 0). If probes are FLAT in richness, T2 has not replaced
  the price, it has renamed it.
* **G3 regret.** `voi` vs `frozen_rule` on `mask` and on `maskr`: two-sided,
  reported with bootstrap 95% CI and a sign test over seeds. NO direction is
  preregistered as "expected"; the gate is that the difference is MEASURED, with
  the CI. (Turn 132 established the frozen rule's maskr behaviour as its
  economic indifference point, so `voi` refusing there is a candidate outcome,
  not a failure.)
* **G4 the probability-only rule.** `conf`'s probe count is reported against
  `nocost` (the no-price extreme). Preregistered prediction **P1**: `conf` will
  behave like `nocost`, not like a stopping rule, because "the comparison is
  undecided" is not the same question as "deciding it is worth the steps". I
  expect `conf`'s probes to track `nocost`'s and to be NON-monotone in richness.
* **G5 controls that must behave.** `beta0` must probe on 0 probes (the frozen
  C1 control); `pure`/`never`-equivalent arms must probe 0; `nocost` must probe
  ≥ `voi` everywhere.
* **G6 structural test on the rule alone** (unit level, already in
  `test_stopping_rules.py`): the accept set of T2/T2b is non-increasing in the
  alternative's rate, and the frozen rule's is NOT (the turn-131 finding). This
  is the falsifiable structural difference between the types.

**Honest register for method.** The rule modules were written and unit-tested;
`test_stopping_rules.py` is a RED-CAPABLE suite (its negative control W9 must
fail an assertion). Full unit suite and its output go in the report verbatim.

## §5 Pilot observations ALREADY SEEN (declared, so they are not predictions)

10 seeds, regret mean / mean probes:

| arm | mask eps 0.35 | maskr eps 0.35 |
|---|---|---|
| `frozen_rule` | 0.00652 / 5.30 | 0.02525 / 1.40 |
| `voi` | 0.00652 / 4.70 | 0.03100 / **0.00** |
| `voi_rate` | 0.16403 / 0.40 | 0.03100 / 0.00 |
| `conf` | 0.00225 / 3.90 | 0.02662 / 4.00 |
| `union_nocost` | 0.00652 / 5.70 | 0.02662 / 4.00 |

Two consequences, declared before the matrix:

* **T3 as I first designed it has no stopping term at all** — `conf` probes
  wherever the comparison is open, which is `nocost`-like (maskr: 4.00 vs 4.00).
  I am NOT going to "fix" it by adding a price: that is the turn-104 trap. It is
  reported as the measured limit of the probability-only type.
* `voi_rate` (horizon-free) under-probes badly on mask (0.40 probes,
  regret 0.164) — the per-step form ignores that a probe is a fixed block of
  steps. Declared as a candidate negative result.

## §6 What would make me abandon the line

If G2 fails (probes flat in richness), then the one-currency rule is not a
different type of stopping rule, only a different formula for the same declared
bar, and the honest report says so. If G0 fails, nothing is reported at all.

## §7 Out of scope / not attempted

* No new world. The frozen instances are used as they are.
* No change to `candidate_gen.py`, `arbitration.py`, `arbitration_scaled.py`,
  `union_agent_v2.py`, `union_instance.py` (hashes re-verified in the report).
* The Bayes-optimal dynamic program over beliefs is NOT implemented (declared
  limit L1: one-step lookahead). `nocost` is kept to bound the size of that gap.
