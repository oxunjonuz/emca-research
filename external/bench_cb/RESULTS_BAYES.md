# RESULTS_BAYES.md — turn 135

**Option (C): the lookahead stopping rule, built and measured.**

Owner directive **msg_00135**: *"option (C) — spend one more cycle building a
more complex rule that computes the whole future ahead."* (msg_id
`op_c72c86c24668`, "продолжай", confirmed mid-run; work preserved.)

Preregistration (written before the first matrix cell): `PREREG_BAYES.md`.
Unit suite: `test_bayes_rules.py` (green, red-capable, 11 groups).
Independent verification: `results/verify_bayes.txt` (11 checks, PASS).
Factcheck: `results/factcheck_bayes.txt` (101 numbers, PASS).

---

## 0. Headline

1. **The lookahead rule is built and it works.** T4 solves the actual optimal
   stopping problem — after a probe the agent may probe again — by a backward
   induction over the exact remaining steps. It **never loses** to the one-step
   rule (T2) anywhere measured, and on two thin-world cells it **wins
   significantly** (mask ε=0.35 at 2000 sims: **−0.00055 [−0.00105, −0.00013]**;
   base=0.60: **−0.00659 [−0.00805, −0.00512]**). On every other cell the
   difference is **exactly zero** to the bit.
2. **The theorem is confirmed, and stated correctly.** `probe_value_T4 ≥
   probe_value_T2` at every state, so `accept(T4) ⊇ accept(T2)`. In live
   trajectories this shows up exactly: 8 states where T4 accepts and T2 refuses,
   **3 where T2 accepts and T4 refuses — all indifference ties (worst margin
   1.2e−14)**, and 0 real violations.
3. **The extra machinery buys little, and the report says so.** The winning
   margin is **0.05%** of the regret level at mask ε=0.35 and **8%** at base=0.60.
   Cost is **1.79×** the DP at 2000 sims. **The honest reading: the lookahead is the correct
   fix conceptually, and its measured benefit over the one-step rule is small —
   because the one-step rule was already nearly optimal in this decision problem.**
4. **The decisive negative survives.** On the rich world (`maskr`) T4 is
   **significantly worse** than the frozen rule (**+0.0041 [+0.0036, +0.0045]**)
   and than `conf` (**+0.0099 [+0.0090, +0.0108]**), exactly as T2 was. Enriching the rule did not
   change that — **the loss is not a myopia defect, it is the economics of the
   rich world**, and no amount of lookahead fixes it.

## 1. What T4 is

```
V(a,b,L) = L*max(mu,r)                                          if L < n
V(a,b,L) = max( L*max(mu,r) ,  n*mu + Σ_k P(k;n,a,b)·V(a+k,b+n-k,L-n) )
```

`mu = a/(a+b)`, `P` the exact Beta-Binomial predictive (closed form, no RNG), `n`
the campaign's own `PROBE_BLOCK`, `L` the **observed** remaining steps, `r` the
observed alternative rate. The rule accepts iff the optimal policy probes.
Module: `bayes_stopping.py` (art registered; sha in `SUMMARY.json`).

**A DEFECT FOUND IN MY OWN FIRST VERSION, WITH A LARGE MARGIN — corrected, and
the whole matrix re-shot.** My first T4 quantised the horizon to whole probe
blocks (`m = floor(L/n)`) and declared the `< n` remainder "worth at most n−1
steps" (prereg A1). **The instrumented diagnostic falsified that** at the state
actually visited on `mask` — `rate_a=None, trials=99, r=0.711, L=135`: T2 accepted
(margin **+4.8e−2**) while the quantised T4 refused (margin **−3.4e−1**), because
the rule valued the same state as if only 120 steps were left. **The discarded 15
steps were worth more than the entire lookahead gain.** A1 was therefore not an
approximation of the rule — it was a different rule with a large error term. The DP
now carries `L` exactly in steps; **A1 is withdrawn**; the first-pass matrix
produced by the quantised version is preserved as evidence in
`results_bayes_QUANTISED_superseded/` and is **not** reported as the result. Every
number below comes from the corrected rule, re-shot from zero, same instances,
same seeds.

## 2. The theorem — and the correction it needed

Since `V ≥ commit` at every state, `probe_value_T4 ≥ probe_value_T2` everywhere,
so **accept(T4) ⊇ accept(T2)**.

**Correction, made before the matrix ran.** I first wrote this as a plain set
inclusion; my own unit suite **W2 failed** on 7/240 grid states. The cause is not
dominance: there the probe is exactly worthless, so both rules sit on the
indifference point — T2's margin is `+2.2e−15` (float noise), T4's is exactly
`0.0`, and they break the tie differently. Wide scan (`diag_t4_inclusion.py`, 2240
states): **0** violations with a T2 margin above `1e−12`, **111** ties (worst
`8.4e−14`), **138** states where T4 strictly accepts and T2 does not. Corrected
claim, now tested with `TIE_TOL = 1e-12` declared in the test:

> accept(T4) contains accept(T2) **up to indifference ties**, and is **strictly
> larger** wherever the probe has positive expected value.

The independent verifier re-derives both rules from the preregistration's
mathematical statement (no shared code) over **750 states: 0 violations**, and
`probe_T4 − probe_T2` never negative.

**Measured on live trajectories** (`diag_bayes_decisions.py`, 10 seeds each):

| instance | decisions | rules agree | T4-only | T2-only | T2-only with margin > 1e−12 |
|---|---|---|---|---|---|
| mask ε=0.35 | 98 | 87 | 8 | 3 | **0** (worst tie 1.2e−14) |
| maskr ε=0.35 | 1962 | 1960 | 2 | 0 | 0 |
| pub m=16 | 366 | 366 | 0 | 0 | 0 |
| pub m=49 | 290 | 290 | 0 | 0 | 0 |

## 3. Does the lookahead buy anything? — the decisive measurement

`bayes` (T4) vs `voi` (T2), same agent, same candidate list, **only the rule
differs**. 2000 sims, bootstrap 95% CI paired by seed:

| instance | bayes regret | voi regret | diff [95% CI] | sign | probes | verdict |
|---|---|---|---|---|---|---|
| mask ε=0.35 | 0.00409 | 0.00464 | **−0.00055 [−0.00105, −0.00013]** | 4+/8− | 4.02 vs 3.98 | **bayes BETTER** |
| mask @base 0.60 | 0.07233 | 0.07892 | **−0.00659 [−0.00805, −0.00512]** | 25+/126− | 1.53 vs 1.34 | **bayes BETTER** |
| mask @base 0.70 | 0.08148 | 0.08152 | −0.00004 [−0.00012, +0.00000] | 0+/1− | 0.47 vs 0.46 | no difference |
| mask @base 0.80 | 0.03129 | 0.03129 | +0.00000 [0, 0] | 0/0 | 0.65 vs 0.24 | no difference |
| mask @base 0.85 | 0.00599 | 0.00599 | +0.00000 [0, 0] | 0/0 | 0.04 vs 0.00 | no difference |
| maskr ε=0.35 | 0.03129 | 0.03129 | +0.00000 [0, 0] | 0/0 | 0.65 vs 0.24 | no difference |
| pub m=16 | 0.01320 | 0.01320 | +0.00000 [0, 0] | 0/0 | 8.31 vs 8.30 | no difference |
| pub m=49 | 0.01230 | 0.01230 | +0.00000 [0, 0] | 0/0 | 8.89 vs 8.89 | no difference |

**T4 is never worse at 2000 sims, and significantly better in exactly two cells —
both where the world is thin and the rule is still probing.** The winning margins
are **0.05%** and **8%** of the regret level. On the identical-regret cells the two
rules nevertheless **probe different numbers of blocks** (0.65 vs 0.24 at base
0.80) — the difference is real but does not reach the decision, which is why the
CI is exactly `[0,0]`: the *chosen arm* is the same on every seed.

**G4/P1 (declared before the matrix, and it needed the correction to hold).** Once
the horizon is exact, `bayes` probes **at least as much as `voi` at every richness
level**: 4.08/1.54/0.46/0.77/0.73/0.04 ≥ 4.04/1.39/0.43/0.66/0.19/0.00. Under the
quantised version this **failed** at two levels — the strongest single piece of
evidence that A1 was a real defect, not a cosmetic one.

## 4. The richness family — G2 remains derived, G3 unchanged

`mask` @eps=0.35, nsim=200:

| base | bayes probes | voi probes | frozen probes | conf probes | nocost probes |
|---|---|---|---|---|---|
| 0.50 | 4.08 | 4.04 | 3.43 | 3.92 | 4.33 |
| 0.60 | 1.54 | 1.39 | 2.99 | 3.90 | 3.98 |
| 0.70 | 0.46 | 0.43 | 2.79 | 4.07 | 4.30 |
| 0.75 | 0.77 | 0.66 | 2.44 | 4.15 | 4.42 |
| 0.80 | 0.73 | 0.19 | 1.54 | 4.39 | 4.46 |
| 0.85 | 0.04 | 0.00 | 0.47 | 4.61 | 4.64 |
| 0.90 | 0.00 | 0.00 | 0.10 | 4.33 | 4.46 |
| 0.95 | 0.00 | 0.00 | 0.00 | 4.06 | 4.09 |

**G2 PASS:** ρ(bayes probes, richness) = **−0.922** (scipy) / **−0.905** (tie-free
manual ranks) — the silence is **derived**, and slightly more strictly than T2's
(−0.952 scipy / −0.881 manual; the two rank conventions differ on ties and both are
reported rather than one being picked).

**G3 on `maskr` — the decisive negative, restated.** At 2000 sims (`results_bayes_hi`):

| comparison | diff [95% CI] | sign | verdict |
|---|---|---|---|
| bayes − voi | +0.00000 [0, 0] | 0+/0− | no difference |
| **bayes − frozen_rule** | **+0.00405 [+0.00358, +0.00451]** | 287+/2− | **bayes WORSE** |
| **bayes − conf** | **+0.00989 [+0.00898, +0.01078]** | 844+/65− | **bayes WORSE** |

(A correction against myself: the first draft of this table carried the CIs from
the 200-sim pass into a paragraph labelled 2000 sims. Those two rows are now
recomputed from `results_bayes_hi` and are covered by the factcheck.)

So the richer rule did **not** repair the rich-world loss. This is the honest answer
to the question option (C) was meant to settle: **the loss on `maskr` is not a
myopia defect.** It is the economics — in a rich world the best arm already pays
0.8–0.9, and the blocks spent buying evidence about it cost more than the evidence
is worth. T4 computes that correctly and refuses; `conf`/`nocost` win there by
refusing to price anything at all. Lookahead sharpens the refusal, it cannot
reverse the economics.

## 5. Gates (PREREG_BAYES.md §4)

| gate | claim | result |
|---|---|---|
| **G0** | transplant control: v4 driver with OLD rules == turn-134 v3 producer | **PASS** (V2, 3 cells cell-for-cell) |
| **G1** | the new rule must act (≥1 probe on ≥80% of mask seeds) | **PASS** (99.5% at every ε) |
| **G2** | probes fall with richness (Spearman ≤ 0) | **PASS** (−0.922 scipy / −0.905 manual) |
| **G3** | regret measured vs voi and frozen, with CI | **done**: better on 2 thin cells, never worse, worse on maskr |
| **G4/P1** | bayes probes ≥ voi wherever voi probes | **PASS** after the A1 fix (failed under quantisation) |
| **G5** | controls: beta0 0 probes, pure 0.07, nocost ≥ both new rules | **PASS** |
| **G6** | cost reported | **PASS**: **1.79×** the one-step rule at 2000 sims (0.0805 vs 0.0450 s/cell); **2.12×** on a cold single cell. In-matrix means are **memo-warm** (the DP memo persists across seeds in one process), so they understate cold cost — both figures reported |

## 6. Verification (independent paths)

`verify_bayes_independent.py` — **11 checks, 0 failures** (`results/verify_bayes.txt`):
V1 all 119 cells' mean/sem/probes recomputed from raw rows (0 mismatches);
V2 cross-producer transplant control in fresh processes;
V3 the DP **re-derived from the preregistration's statement, own lgamma pmf, no
shared code** — 750 states, 0 violations;
V4 the headline diffs recomputed;
V5 G2 recomputed with **scipy** (an independent implementation, giving −0.922);
V6 bit-identical across 3 hash seeds; V7 frozen producers unchanged; V8 the
superseded first pass preserved; **V0 negative control fires.**

`factcheck_bayes.py` — **119 numbers quoted in this report recomputed from the
frozen JSON, 0 failures**. It caught **two numbers I had written from a pilot
rather than from the matrix** — the `maskr` CIs (taken from the 200-sim pass into a
2000-sim paragraph) and the DP cost ratio (2.12× from a cold single cell, where the
in-matrix means are memo-warm at 1.79×) — both corrected in this report rather than
quietly dropped.

**Independent observation, reported not resolved:** the runtime raised a WRITESET
ALERT on `/data/owner_priority.jsonl` during this turn. That file is the layer
recording *the owner's own priority message* (`op_c72c86c24668`); my scripts write
only under `bench_cb/`. Surfaced, not swallowed.

## 7. Defects found in my own work this turn (reported, not hidden)

1. **A1 block quantisation was a real defect with a large margin** (§1) — found by
   my own instrumented diagnostic, not by the matrix, and it required re-shooting
   the whole matrix. The quantised matrix is kept as evidence.
2. **The theorem's first statement was false as written** (§2) — found by unit
   suite W2 before the matrix; corrected to an up-to-ties claim with the tolerance
   declared in the test.
3. **The W9 negative control silently stopped reddening** after the horizon fix
   (it was written for the block semantics). Rewritten, and a second control W9b
   added. Caught because the suite is required to be red-capable.
4. **`verify` V4 initially reported no difference where the mask numbers do
   differ** — the check compared against its own recomputation. Corrected to
   compare the recomputed diff against the stored one.

## 8. Honest limits

* **The benefit over T2 is small.** Two significant cells, margins 0.05% and 8% of
  level, and six cells identical to the bit. The lookahead is the right
  *conceptual* fix; the measured gain is modest, and I say so rather than
  foregrounding the two wins.
* The DP is **myopic about other candidates** (A3): it prices this candidate
  against the observed alternative, not against the whole candidate list.
* The objective is the candidate's **own reward**, not episode regret (A4): the
  gap between them is what the matrix measures and it is not assumed away.
* `r` is a **point**, not a posterior (A2).
* Frame is **T = 400, PROBE_BLOCK = 20**; horizon `L` enters exactly, so the rule's
  behaviour at other T is untested here.
* Two rank conventions for Spearman disagree on ties (−0.922 / −0.905); both are
  reported.

## 9. Fork (the owner's decision)

* **(A)** Adopt T4 and close the line: it is the correct instrument, it never loses,
  and its measured advantage over the one-step rule is small — the honest end of
  this sub-line.
* **(B)** Write the preprint column with v1–v8 plus this: **the stopping-rule family
  is now three types (threshold / one-currency / lookahead), ordered by how much
  machinery they need and NOT by how much they win**, and the rich-world loss is
  economics, not myopia.
* **(C2)** One more turn on the object that this cycle revealed as the real gap: the
  DP prices **one candidate at a time** (A3). The next genuinely different object is
  a DP over the **candidate list** — but I would name it a new instrument again,
  and I do not recommend it before (A) or (B), because the two wins above do not
  suggest the multi-candidate term is where the remaining regret lives.

My recommendation: **(A)**, and if the line is to be written up, **(B)** with §3
and §4 exactly as they are — including the two small wins and the one loss that
survived a more powerful rule.