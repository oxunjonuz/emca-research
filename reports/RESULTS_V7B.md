# RESULTS V7B — closure of C3's open item: is family-wise control the answer, and what is the true FP rate

Turn 125 (msg_00125). Owner directive: V7 accepted; C1/C2/C3 give a
coherent picture; this may be the point to freeze the line as a result
rather than build a seventh world; if continuing, option (A)
(family-wise error control instead of a fixed block budget) looks like
the most exact answer to the cause of C3 FAIL. Frozen preregistration:
`research/PREREG_V7B.md` (written before the first new run; amendments
A1 and A2 declared in §3b/§3c before the bulk of the data existed; not
one threshold, verdict rule, block budget, world or line of code
changed).

**Short answer.** (A) cannot be the answer: it is a **layer error**, and
the arithmetic is decisive. The block budget (80) is **already a
family-wise control at the exact level the agent lives at**; the cap
guarantees a finite family, so within-life error is already bounded by α
with no correction needed, and any further correction *loses* power
instead of gaining honesty. Meanwhile the gate "FP = 0" is not failing
because the verifier is loose — it is failing because **"zero false
positives" is not a property a calibrated decision rule can have**. The
only convention under which the observed false positive is rejected is
the study-level family, i.e. a property of the *experiment*, not of the
*agent*.

---

## 0. What is measured and on what

| measurement | source | n |
|---|---|---|
| frozen matrix V7 | `results/matrix_v7/*.json` | 110 runs, 149 verdict rows |
| held-out battery V7B | `results/matrix_v7b/*.json` | 1000 runs (seeds 10..509, both regimes), 1471 verdict rows |
| scripted calibration | `results/calib_v7b_scale.txt` | 5000 windows (null regime) |
| exact null rate | enumeration over [0,200]×[0,199] | exact |
| independent pass | `verify_v7b_independent.py` | different code, disk only |

Code hashes confirmed **before and after** all runs, identical to the
configuration that produced the V7 matrix: `env_terrarium_v7
1bfcba7a…`, `agent_emca_v7 64a719d1…`, `candidate_gen fa9721ae…`,
`arbitration 2d3d825b…`, `run_life_v7 78af6b34…`, `driver_v7 18c945cb…`,
`analyze_v7 b02b4882…`. The frozen matrix's combined sha256 is unchanged
(`1f5a66e32c2cda4e…`), 110 files.

---

## 1. H1 — option (A) is a layer error, and this is arithmetic

The observed FP has exact p = **0.000551** (recomputed independently from
the recorded 2×2: 114/86 vs 80/119). A family-wise control of level α
rejects it only if the family is at least:

| α | family needed |
|---|---|
| 0.05 | m ≥ **91** |
| 0.01 | m ≥ **19** |
| 0.001 | m ≥ 2 |

The agent's **real per-life family** — the number of verdicts it actually
issues in one life — is **mean 1.35, max 4** (measured on the frozen
matrix: 64 lives with 1 candidate, 6 with 2, 37 with 3, 3 with 4).
Against the observed event, **no agent-level family-wise control of any
convention can reject it.** Only the study-level family (149 rows,
threshold 0.000336) does — and that is a statement about the experiment,
not about the agent's epistemic rule.

**And the budget is already a family-wise control.** The block budget
(`PROBE_MAX_BLOCKS = 80`, ~800 scheduled trials per candidate) fixes the
family in advance *within a life*: because the number of tests an agent
runs per lifetime is capped, a per-candidate α controls the within-life
error at exactly α. Correcting an already-specified family by α/m is
textbook power loss, not honesty. So (A) is not a stricter answer to
C3's cause; it is a category mistake about which level owns the error.

## 2. H1, second leg — even applied literally, (A) changes nothing

Applied as an agent-side Bonferroni over that life's candidates
(α_adj = 0.05/m_life), every FP event survives:

| seed | m_life | α_adj | p | still CAUSAL |
|---|---|---|---|---|
| 29 | 3 | 0.0167 | 0.00526 | yes |
| 31 | 3 | 0.0167 | 0.01188 | yes |
| 319 | 3 | 0.0167 | 0.00170 | yes |
| 432 | 2 | 0.0250 | 0.00038 | yes |
| 493 | 3 | 0.0167 | 0.00286 | yes |

Across **both corpora the α-adjusted rule flips zero verdicts** — 6/99
false positives and 50/50 true-edge detections in the frozen matrix,
6/1030 and 439/441 held out, all unchanged. The binding constraint in
every one of these verdicts is **RR ≥ 1.3, not α**. Tightening α on
p-values that sit 20–130× below the boundary is inert by construction.
(A) would be a change that costs nothing and fixes nothing.

## 3. H2 — and V7's denominator was inflated

V7 reported E[FP] = 149 × 0.0051 = 0.76 with "149 tests". But the 149
**rows** are not 149 tests: the single event appears in **6 rows** because
the same seed-8 world is replayed by three arms in two truth regimes,
sharing a stream. Counted at the level the event lives at — distinct
worlds — the frozen matrix holds **23 worlds** and **one** event.
Correcting the record: on the frozen matrix, E[FP] is **0.73 by rows** and
**0.11 by worlds**; the honest event rate is **1/23**, not 1/149. This is
a record correction, **not** a verdict revision: C3 stays FAIL by the
letter of the frozen gate.

## 4. H3 — the exact null rate, and why the old "0 FP" evidence was weak

Exact enumeration over all 200×199 = 39 800 outcome pairs at p = 0.5
(the effect is a world event independent of the action):

* P(p < 0.05, one-sided greater) = **4.430%**
* P(p < 0.05 **and** RR ≥ 1.3) = **0.488%** ← the frozen rule's per-test
  false-positive rate. The campaign's Monte-Carlo said 0.51%; the
  independent simulation gives 0.443% (177/40 000). All three agree.
* The observed event's p = 0.00055 corresponds to a class probability of
  **0.0386%**.

**The honest corollary about the old evidence:** the scripted
calibrations that reported 0/400 and 0/160 were **underpowered at this
rate** — expected hits 1.95 and 0.78, so P(0 hits) = 0.14 and 0.46 even
under a perfectly calibrated rule. "0/400" never demonstrated that the
rule cannot produce a false positive; it bounded the rate at ~1% at best.
That is exactly the over-read the V7 report flagged as "a bar a
calibrated test cannot meet" — now measured rather than argued.

## 5. H4 — held-out seeds: the verdict the count trigger gave was wrong

1000 runs on **seeds 10..509** (never used by the campaign; every one
full-length, all four code hashes unchanged): **1030 null (glow) tests,
6 false-positive events, rate 0.583%** — against the calibrated 0.488%
(one-sided Fisher p = **0.409**, i.e. indistinguishable).

Five events in the truth=on regime (seeds 29, 31, 319, 432, 493) and one
in truth=off (493); the on/off split is **not** significant (Fisher
p = 0.750) — as it must be, since the event's anatomy (a warm-phase world
event, action-independent) carries no information about the injected edge.

**The count trigger fired and it was the wrong instrument.** PREREG_V7B
§1 H4 fixed a count rule ("FP ≥ 2 → real defect"), calibrated for ~100
tests. At 109 tests, 2 events carry P(≥2 | calibrated) = 0.087 — above
any sensible threshold. Amendment A2 (declared before the extension ran)
replaced the count trigger with a rate test and said so in advance. The
rate test:

| | events / tests | rate | 95% CI |
|---|---|---|---|
| agent side, held out | 6 / 1030 | 0.583% | [0.267%, 1.265%] |
| scripted protocol | 19 / 5000 | 0.380% | [0.243%, 0.593%] |
| exact null | — | 0.488% | — |

One-sided Fisher (agent above scripted) **p = 0.2457** → **no
inflation**. The agent-driven verifier is neither looser nor tighter than
the same rule driven by scripted actions.

**Clustered at the right level (a seed, not a row):** the frozen matrix
contributes 1 seeded event across 10 seeds; the held-out battery 5 events
across 441 seeds. Combined: **6 seeded events, expected 5.45 under the
null rate — P(≥6) = 0.46.** The false positives are neither absent nor
excessive: they are what a calibrated rule at this n produces.

## 6. H5 — large-scale scripted calibration with power

5000 windows at n = 200/arm: **19/5000 = 0.380%, Wilson CI [0.243%,
0.593%]**; the exact null rate 0.488% sits inside the interval. Arm
permutation control (target/control labels shuffled): 4/1250 = 0.320%,
CI [0.125%, 0.820%] — the measurement is driven by the stream, not the
label assignment. This is the first calibration in the campaign with the
power to speak about the *rate* rather than bound it.

## 7. Independent verification (different code, disk only)

`verify_v7b_independent.py` → `results/verify_v7b_independent.txt`,
importing neither the analysis nor the agents:

* recomputed p of the frozen event 0.000551 vs recorded 0.00055 — PASS;
* all six held-out events reproduce under the frozen rule — PASS;
* exact null rate by **simulation** (0.443%) vs the primary pass's
  **enumeration** (0.488%) — PASS (different computational path);
* Bonferroni family thresholds — PASS;
* frozen matrix integrity: 110 files, combined sha256 unchanged — PASS.

**Determinism:** seeds 29 and 493 rerun in a fresh process give
**byte-identical** JSON (sha256 prefixes 924a21fd, 5bf1b7e8, 3b3ffbe1,
4eed0449). The frozen matrix was never touched by any V7B script.

---

## 8. Verdicts

| claim | result |
|---|---|
| H1: (A) can be the answer to C3's cause | **REFUTED** — layer error; agent-side family too small (needs m ≥ 91, has ≤ 4) and the budget is already the within-life control |
| H1b: (A) applied literally would have helped | **REFUTED** — flips zero verdicts in both corpora; RR, not α, binds |
| H2: V7's E[FP] denominator | **CORRECTED** — 0.76 by rows / 0.11 by worlds; event rate 1/23, not 1/149 (V7's C3 verdict untouched) |
| H3: exact null rate | **PASS** — 0.488% exact, 0.443% simulated, 0.51% Monte-Carlo; old 0/400 shown underpowered |
| H4: inflation on held-out seeds | **NO INFLATION** — 0.583% vs 0.488%, p = 0.409; count trigger (fired at 2) shown underpowered and replaced in advance by a rate test |
| H5: scripted calibration | **PASS** — 0.380% [0.243%, 0.593%], permutation control agrees |

**C3 remains FAIL by the letter of the frozen gate.** Nothing was
retracted or reinterpreted: the gate was not met in V7, that is the
published result, and this turn establishes only *why* — the gate
demands a property (zero false positives) that no calibrated rule has,
at any sample size. "FP = 0" is **unattainable in expectation**, not
merely strict.

## 9. What this means for the line

The open item that V7B was written to close is closed, and it closes
against the proposed fix. Three things are now measured rather than
argued:

1. The verifier is **calibrated**: its false-positive rate matches the
   exact null rate of its own rule, on held-out seeds and under
   independent verification.
2. Its **gate is mis-specified at the unit level**: the criterion should
   be a rate with a pre-declared bound, not FP = 0.
3. The proposed remedy (A) **cannot change anything**, and the reason is
   structural: the budget is already the family-wise control, and α is
   not the binding term in any observed verdict.

That is a result about the line's own instrumentation, not another world
— and it is the natural place to stop.
