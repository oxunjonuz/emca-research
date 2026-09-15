# PREREG V7B — closure of C3's open item: can family-wise control ever be the answer, and what is the FP rate on held-out seeds

Turn 125 (msg_00125). Owner directive: "V7 accepted; C1/C2/C3 now give a
coherent picture; this may be the point to freeze the line as a result
rather than pull toward a seventh fork for one more world; if you
continue — option (A) (family-wise error control instead of a fixed
block budget) looks like the most exact answer specifically to the cause
of C3 FAIL; decide yourself, stop only at a real fork."

This file is frozen BEFORE the first new run. No threshold of
`PREREG_V7.md` §2, no verdict rule (p<0.05, RR>=1.3), no block count
(80), no world, and no agent/generator/arbiter code is changed. The v7
code is NOT edited: its byte hashes are pinned below and rechecked after
the runs.

**Declared deviation from "one more world":** V7B is NOT a new world. It
is (i) arithmetic on frozen data and (ii) held-out seeds of the same
world on the same code. The owner warned against a seventh fork for mere
refinement — here the question is whether the proposed (A) is a real
answer or cosmetics, and only then is the freeze decision taken.

---

## 0. Already known (frozen fact, not re-measured)

* V7 matrix: 110 runs x 16000 steps, 149 verdict rows.
* Exactly **one** distinct false-positive event: seed 8, pair
  `wait->glow`, target warm 114/200 vs ctrl 80/199, Fisher
  **p = 0.00055**, RR = 1.418 (6 rows — the same seed in 6 runs).
* In the V7 report (§2) E[FP] was computed as 149 x 0.0051 = 0.76,
  P(>=1) = 0.53, and the gate "FP = 0" was honestly reported FAIL by the
  letter.
* Rejected fixes: raising the probe budget 80->120 (a reshuffle on
  held-out seeds 60..159), replacing the threshold with "FP <= 1".

## 1. Testable claims, thresholds, decision rules

### H1 — (A) cannot be the answer to C3's cause (arithmetic)

Operationally: let the observed FP have exact p = p_fp. A family-wise
error control of strictness alpha would reject this event only if the
family m >= alpha/p_fp. The agent's family is the number of tests the
agent actually issues per life (from the frozen matrix). The study's
family is all tests issued.

* **Decision rule:** measure p_fp and the m-thresholds for alpha in
  {0.05, 0.01, 0.001}; compare with (i) the agent's per-life family,
  (ii) the number of runs, (iii) the number of rows.
* **Refutation of H1:** if any real family convention rejects the event
  at alpha=0.05.
* **Data:** frozen JSON only; no new runs needed.

### H2 — the E[FP] denominator in V7 was inflated by coupled rows

Operationally: 149 rows are not independent (seed 8 yields 6 rows);
independent "worlds" number 10. Count the tests under all four
conventions and E[FP] in each.

* **Decision rule:** report the E[FP] range (lowest convention — tests
  within worlds; highest — all rows) and which convention V7 quoted.
* This is a **record correction**, not a verdict revision: C3 remains
  FAIL by the letter of the frozen gate.

### H3 — null frequency of the rule: exact enumeration + power of past calibrations

Operationally: exact enumeration over all (x,y) in [0,200]x[0,199] at
p=0.5 (the effect is a world event independent of the action) gives the
nominal frequency of the rule "p<0.05 AND RR>=1.3" and of any p<0.05.

* Plus: the expected number of hits in the scripted V7 checks (0/400 and
  0/160) at the measured rate — a measure of their power.
* **Refutation of H3:** exact rate deviating from the campaign's
  Monte-Carlo (0.51%) by more than 1.5x.

### H4 — HELD-OUT SEEDS: FP rate on fresh worlds (the main new run)

Design: seeds **10..29** (never in the campaign), v7 code unchanged,
`PYTHONHASHSEED=0`, two batteries:
  BA: `v7_full`, truth=on, rich=low, decoy=on (20 runs)
  BB: `v7_full`, truth=off, rich=low, decoy=on (20 runs)
Run via `run_life_v7b.py`, which IMPORTS `run_life_v7.run` (the same
agent/world logic) and writes to `results/matrix_v7b/` — the frozen
`results/matrix_v7/` is never touched.

Metric: the number of **distinct** FP events (CAUSAL on a `*->glow`
pair) and the number of null tests issued.

* **Pre-registered prediction:** at 0.488% per test and ~30-40 null tests
  across the two batteries, E[FP] = 0.15..0.20, so **0** events are
  expected; >=2 events is a p ~ 0.01 event.
* **Decision rule (frozen BEFORE the runs):**
  * FP = 0 -> C3's FAIL stays FAIL by the letter, but is
    re-characterized: "frequency calibrated, the letter is strict";
    the line closes as a result (fork C) if H1/H3 hold.
  * FP >= 2 -> inflation above the calibrated rate (a real verifier
    defect) -> the line continues, the fork changes.
  * FP = 1 -> indeterminate; both conventions and the CI are reported.
* **Honest caveat, declared in advance:** FP = 0 gives only weak
  evidence of calibration (at ~35 tests the upper 95% bound on the rate
  is ~8.5%). So H4 decides **inflation**, and H5 decides **frequency**;
  interpretation rests on both.

### H5 — large-scale scripted calibration (its own power)

Design: the same scripted protocol as `calib_v7_fprate.py` (5/5
alternation, affordability gate, pinned on the station, respawn, scored
within warm), but N = 2500 windows at a matched n.

* **Refutation of calibration:** measured rate outside the 95% CI of
  0.488% at E[hits] ~ 12 (power sufficient to speak about rate, unlike
  0/400).
* Arm-permutation control: the same procedure with the target/control
  assignment shuffled checks whether the result depends on the arm
  assignment rather than the stream itself.

## 2. Independent verification

`verify_v7b_independent.py` — different code, disk only, importing
neither the analysis nor the agents: recomputes p_fp, the exact rule
frequency (by simulation, not enumeration), the family conventions, the
held-out rate, and the scripted rate. Any deviation from the primary
pass above 1e-9 (exact quantities) or above 2 sigma (simulated) is
reported as a discrepancy.

## 3. What is NOT done

* Thresholds, verdict rule, block budget, world, and v7 code are not
  changed.
* No V7 verdict is revised (C2 PASS, C3 FAIL by the letter, C1 PASS stay
  as published).
* No new world is built (owner directive: a seventh fork for refinement
  is not needed).
* The frozen `results/matrix_v7/` is overwritten by nothing.

## 3b. AMENDMENT A1 (turn 125, declared before the bulk of the held-out runs)

Measured runtime of one held-out seed (both batteries) = **~1 s**. The
frozen plan (§1 H4) named seeds 10..29. Since the cost is negligible and
power is the binding constraint, the held-out battery is EXTENDED to
**seeds 10..59** (100 runs, two batteries), declared here after ONLY
seed 10 had been run (10-on: 3 verdicts, 0 glow-CAUSAL; 10-off: 0
verdicts), and before any other held-out seed was run.

* No threshold, no verdict rule, no block budget, no world, no code
  changes. The decision rule of §1 H4 stands verbatim.
* The extension is not outcome-dependent: no seed was selected or
  dropped on the basis of its result.
* The extended set is reported as one whole; seeds 10..29 are NOT
  reported separately as "the frozen subset" (that would be a
  garden of forking paths).

## 3c. AMENDMENT A2 (turn 125, declared BEFORE the extended agent-side run)

State when declared: only seeds **10..59** have been run (100 runs, 109
null tests) plus the frozen matrix. Observed so far: 2 held-out
glow-CAUSAL events (seeds 29, 31) against an expectation of 0.53, and 1
in the frozen matrix. The §1 H4 count trigger (>= 2) therefore FIRED.
That trigger was calibrated for 100 tests; at 109 tests, 2 events carry
P(>=2 | calibrated rate 0.488%) = **0.087** — the trigger is
underpowered, so following it literally would be a category error
(deciding a rate question with a count threshold). Two changes are
declared here, before any further data:

**(1) The count trigger is replaced by a rate test.** The measurable
quantity is the agent-side false-positive RATE, compared with the rate
of the SAME rule under the scripted protocol (which shares the world,
the rule and the block protocol, and differs only in being driven by
scripted actions instead of the agent's life). Decision:
  * one-sided Fisher exact on (agent events, agent null tests) vs
    (scripted events, scripted windows) with p < 0.05 and the agent rate
    ABOVE the scripted rate -> **inflation: a real verifier defect**;
  * otherwise -> the agent-side count is **consistent with a calibrated
    rule**, and C3's FAIL is re-characterised (not erased).
The frozen §1 H4 verdict (FAIL by the letter) is untouched by this.

**(2) The held-out battery is extended to seeds 10..509** (1000 runs,
two batteries) so that the rate test has the power to separate a 0.5%
rate from a 1.9% rate (expected events ~5.4 vs ~20). Runtime measured on
50 seeds: 25 s; 500 seeds ~ 4 min.

* No threshold in `PREREG_V7.md` §2, no verdict rule, no block budget,
  no world, and no agent/generator/arbiter code is changed.
* No seed was selected or dropped on the basis of its result; the set is
  reported whole (seeds 10..509). Seeds 10..59 are NOT reported
  separately as a preferred subset.
* If the extended run shows the agent rate is NOT above the scripted
  rate, that is the result and it will be reported as such — including
  the possibility that the two held-out events were tail luck.

## 4. Pinned hashes of the frozen code (checked before and after the runs)

Record sha256 first-16 hex for: `env_terrarium_v7.py`,
`agent_emca_v7.py`, `candidate_gen.py`, `arbitration.py`,
`run_life_v7.py`, `driver_v7.py`, `analyze_v7.py`. Expectation (from
PREREG_V7 §5 A7): `1bfcba7a`, `64a719d1`, `fa9721ae`, `2d3d825b`,
`78af6b34`, `18c945cb`, `b02b4882`. A mismatch is a report, not a silent
edit.
