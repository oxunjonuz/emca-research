# THE CAMPAIGN RESULT — the EMCA line, frozen as a result (turn 125)

Authority: owner directive msg_00125 — C1/C2/C3 give a coherent picture
(nominates a hypothesis, chooses truth when an alternative is allowed,
almost never errs in verification) together with the restored epistemic
verdict over all six earlier worlds; this may be the point to freeze the
line as a result rather than pull toward a seventh fork for one more
world. This document is that freeze. It is written after the line's last
open item was closed (`RESULTS_V7B.md`), and it adds no new runs.

Every number below is traceable to a frozen artefact on disk; the
per-world reports and the ledger are named at each point. Nothing here
is new measurement.

---

## 1. The question the line was actually about

Not "does causal structure pay in reward" — that was measured three
times and is a property of the **world** (see §4). The question the
campaign ended up answering, after the frame was restored in turn 116
(`EPISTEMIC_VERDICT.md`), is:

> Does an agent that carries an explicit causal module find the truth
> reliably and honestly — telling cause from coincidence, truth from
> decoy — as a value in its own right, and does it keep that commitment
> when knowing conflicts with short-term reward?

## 2. Axis B — epistemic reliability (the line's main result)

### 2.1 Discrimination: invariant to the price of the decoy

A single stratified identifier (v2.5c) **rejected the designer decoy in
0 of 51 runs across all six earlier worlds** — in a world where the decoy
was free, in a world where believing it *paid* (+722), and in a world
where believing it *killed* (−3159 reward, +22 deaths). The pooled
identifier accepted the decoy **48/51**: its one contrast cannot separate
"exclusive inside a context" from "exclusive in the pooled table".

That invariance to the decoy's price is the line's central, self-contained
result. Source: `EPISTEMIC_VERDICT.md` §4.1, `results/epistemic_ledger.txt`.

### 2.2 Active uncovering of grey truths

The prober line (v3.2/v3.3/v6/v7) issues do-intervention verdicts with
alternating blocks and an exact Fisher rule. Across v3.2/v3.3/v6 it
produced **21 CAUSAL verdicts, all on true edges, with zero false
positives in 28 verdicts.** Verdict calibration is good: measured RR of
accepted edges sits +1% from the oracle in v6, +16% in v3.3 (winner's
curse), +48% at n=1 in v3.2.

### 2.3 The three claims separated (V7) — three different outcomes

V7 was built precisely to stop measuring a mixture
(`research/PREREG_V7.md`, `RESULTS_V7.md`):

| claim | what it asks | verdict |
|---|---|---|
| **C2 — generation** | is the candidate list a function of the agent's own tables, or a constant? | **PASS** — nominates the true pair 9/10 when the edge exists, 0/10 when it does not, follows the seed-randomised action across all three choices, and the generator source audited at **0 world tokens**. The designer-list control hits only 4/10 — exactly the seeds where the truth happened to equal the hardcoded action. |
| **C1 — choice** | is "verify or exploit" computed from the agent's state plus the reward structure? | **PASS** — all three legs: probes in conflict 9/10 vs 0 for β=0; first probe follows the permuted ranking 18/18; probes at the expensive alternative (880) < cheap (1080) and not zero. |
| **C3 — verification** | does a do-intervention on self-generated candidates reject the decoy? | **FAIL by the letter** (FP = 1 where the gate demanded 0; FN = 1, within tolerance) |

**And then C3's failure was explained rather than patched** (turn 125,
`RESULTS_V7B.md`): the exact null rate of the frozen rule is **0.488%**
per test; on **1030 held-out null tests** (seeds 10..509, same code) the
observed rate is **0.583%** (p = 0.409 — no inflation); clustered by
world, 6 events against 5.45 expected (P(≥6) = 0.46). The gate "FP = 0"
demands a property a calibrated rule does not have at any sample size:
**unattainable in expectation, not merely strict.**

Also corrected in the record: V7's E[FP] denominator ("149 tests") was
inflated by arm-coupled rows — the same seed-8 world replayed six times.
At the right unit the frozen matrix holds 23 worlds and one event
(E[FP] 0.11, not 0.76).

### 2.4 What the campaign's own instrumentation got wrong — twice

The line's most durable confounders turned out to live in its own plan,
not in its worlds:

* a hardcoded **armour in the planner** (turns ≤101–104) silently skipped
  the false edge, so every "believer" arm before v4 never acted on its
  belief — "belief is costly" only became measurable once it was removed;
* a **hash-order non-determinism** in a competence's tie-breaking made
  whole v5 numbers depend on `PYTHONHASHSEED` (found turn 115, fixed for
  all arms equally);
* an **anti-illusion device** (turn 115) coupled epistemology back into
  statistics — acting on a belief produced the data that justified it;
  removed before the matrix.

## 3. Axis A — economics (secondary, measured, deliberately not a verdict)

The conversion of knowledge into reward is assigned by the world, and
this was measured end to end:

| world | contrast | effect |
|---|---|---|
| v3.3 | strat − pooled (primary) | +178, CI covers 0 — **weather** (corr 0.962) |
| v4 | honest − fooled (price of the false edge) | **+3159**, CI excludes 0 (sign test 0.109, reported) |
| v5 | selectivity | −1008, CI covers 0 (corr with weather 0.999) |
| v6 | truth, gross | **+3755**, CI excludes 0, p = 0.004 — largest effect of the line |
| v6 | discovery, net | +455, CI covers 0, p = 0.754 |
| v6 | cost of finding out | 88% of the gross value |

The clean formulation the line earned: **what pays is the difference
between what the agent knows and what the world is willing to pay for
it — and both terms are set by the world, not by the agent.**

## 4. The line's outcome, in one paragraph

The causal module does the epistemic job it was built for. It
distinguishes truth from decoy invariantly to the decoy's price (0/51
against 48/51); it uncovers hidden grey truths by intervention with a
calibrated rule; and when its three capacities were at last separated,
two of them passed outright (it **generates** its own hypotheses — with
zero world tokens in the generator — and it **chooses** to verify from
its own state and the reward structure) while the third **fails only by
the letter of a gate that is statistically unattainable**. Its reward
conversion, measured five times, is a property of the world every time.
Two of the line's longest-lived confounders were found in the line's own
instrumentation, and one of them — a hardcoded armour — had silently
protected the hypothesis it was supposed to test for three matrices.

## 5. Known limits, stated plainly (none of them hidden)

1. **n = 10 seeds** for the v4–v7 matrix contrasts; the v7 separation
   evidence is deterministic and bit-reproducible, but seed-level
   contrasts are not powered beyond sign tests.
2. **v5 numbers** were produced under a random hash seed (caveat from
   turn 115); valid as a sample, not as a bit-reproducible record.
3. **C3's FN = 1** in v7 (9/10 true-edge acceptance) is honest, not
   adjusted for.
4. **Continuous confidence is still missing** — the module issues a
   threshold verdict, not a posterior. This is the line's clearest
   declared gap and it was never closed.
5. **Self-reinforcement was tested once**, where the line met it, not as
   a battery.
6. The v7 **oracle** arm is an analytic device (the edge injected free),
   never entered into any fairness verdict.

## 6. Artefacts of the freeze

* Per-world reports: `research/RESULTS_V4.md`, `RESULTS_V5.md`,
  `RESULTS_V6.md`, `RESULTS_V7.md`, `RESULTS_V7B.md`.
* Frame: `research/EPISTEMIC_VERDICT.md`; ledger (recomputed from raw
  JSON in a fresh process): `results/epistemic_ledger.txt`.
* Frozen preregistrations, one per world: `research/PREREG_V4.md` …
  `PREREG_V7B.md` (every amendment logged with its date and its reason).
* Matrices: `results/matrix_v4|v5|v6|v7|v7b/` (110 + 1000 runs for v7/v7b).
* Comparative economics table for v3.1–v3.3: `research/PREPRINT_TABLE.md`
  (its builder reads the `condition`-keyed v3.x matrices; the v4–v7
  numbers live in §3 here and were not retro-fitted into that frozen
  artefact).
