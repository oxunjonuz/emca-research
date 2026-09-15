# TURN 125 STATUS — V7B: the C3 open item closed, and the line frozen

Owner message: msg_00125 (V7 accepted; C1/C2/C3 coherent; this may be the
point to freeze the line as a result; if continuing, option (A)
family-wise control looks like the most exact answer to C3's cause;
decide yourself, stop only at a real fork).

## Decision taken

I did **not** build a seventh world. The owner's hint (A) was tested for
whether it is a real answer — and it is not. The line is frozen as a
result (`research/CAMPAIGN_RESULT.md`).

## What was done this turn

1. Read the frozen V7 state from disk (report, prereg, all five code
   files, driver, runner, runner hashes) — nothing answered from recall.
2. Wrote `research/PREREG_V7B.md` **before any new run**: claims H1–H5,
   thresholds, decision rules, and two amendments (A1: extend held-out
   seeds 10→59 after 1 s/run was measured and only seed 10 had run;
   A2: replace the underpowered count trigger with a rate test and
   extend to seeds 10..509 — **both declared before the bulk existing**).
3. New code (nothing frozen edited):
   * `run_life_v7b.py` — imports `run_life_v7.run` (byte-identical
     logic), writes to `results/matrix_v7b/`;
   * `driver_v7b.py` — seeds 10..509 × {truth on, truth off}, 1000 runs;
   * `analyze_v7b.py` — primary pass, H1–H5;
   * `calib_v7b_scale.py` — 5000-window scripted calibration + arm
     permutation control;
   * `diag_v7b_parity.py` — mechanism check (draw parity, arm splits);
   * `verify_v7b_independent.py` — second pass, different code, disk only.
4. Ran everything; verified by an independent path.

## Results (all frozen on disk)

| claim | result |
|---|---|
| **H1** (A) can answer C3's cause | **REFUTED** — layer error. Observed FP p = 0.000551; rejecting it needs family m ≥ 91 at α=0.05. The agent's real per-life family is mean 1.35 / max 4. The block budget is **already** the within-life family-wise control. |
| **H1b** (A) applied literally | **REFUTED** — α_adj = 0.05/m_life flips **zero** verdicts in both corpora (6/99 & 6/1030 FP unchanged, 50/50 & 439/441 true-edge unchanged). RR≥1.3, not α, binds. |
| **H2** V7's E[FP] denominator | **CORRECTED** — the 149 rows are 23 worlds; the seed-8 event is 6 coupled rows of 1 event. E[FP] 0.73 by rows, **0.11 by worlds**. C3's verdict untouched. |
| **H3** exact null rate of the frozen rule | **PASS** — 0.488% enumeration, 0.443% independent simulation, 0.51% campaign Monte-Carlo. Old 0/400 and 0/160 shown **underpowered** (E[hits] 1.95 / 0.78). |
| **H4** inflation on held-out seeds | **NO INFLATION** — 6/1030 = 0.583% vs calibrated 0.488%, Fisher p = **0.409**; vs scripted protocol p = **0.2457**. The count trigger fired at 2 and was the wrong instrument (P(≥2)=0.087 at 109 tests); replaced by a rate test in advance (A2). |
| **H5** scripted calibration with power | **PASS** — 19/5000 = 0.380%, CI [0.243%, 0.593%]; permutation control 4/1250. |

**Clustered at the right unit (a seed):** 6 seeded events in 451 seeds,
**5.45 expected** under the null rate, P(≥6) = 0.46 — exactly what a
calibrated rule produces. The frozen matrix's "149 tests" framing had
inflated both numerator (6 rows for 1 event) and denominator.

**Mechanism checked and set aside:** glow is drawn from the world RNG
only in warm, so every scored step in a warm block registers glow=1;
I measured the draw-index parity per arm (diag_v7b_parity) — parity is
mixed within arms (e.g. seed 29: 45.4%/54.6% target), so the FP is not a
constant-parity interleaving artifact, and the effect is not
regime-specific (on vs off Fisher p = 0.750).

## Verification of this turn's own work

* Frozen code hashes **unchanged before and after** all 1000 runs:
  env 1bfcba7a, agent 64a719d1, gen fa9721ae, arb 2d3d825b,
  run 78af6b34, driver 18c945cb, analyze b02b4882.
* Frozen matrix `results/matrix_v7/` **untouched**: 110 files, combined
  sha256 `1f5a66e32c2cda4e19d30403a819feb581a3ae37ebf4238b75fefe77d3a179b0`.
* Held-out battery: 1000/1000 runs full length (16000 steps), 50 seeds ×
  2 regimes, no failures.
* Determinism: seeds 29 and 493 rerun in a fresh process → byte-identical
  JSON (924a21fd, 5bf1b7e8, 3b3ffbe1, 4eed0449).
* Independent pass (`verify_v7b_independent.py`): recomputed p 0.000551,
  all 6 events reproduce, exact null rate by a different computational
  path, Bonferroni thresholds, matrix integrity — **no discrepancies**.
* `analyze_v7b.py` and the primary ad-hoc passes agree with the
  independent pass on every reported number.

## Honest corrections to my own record

* V7 §2's "149 tests" (and E[FP] = 0.76) counted coupled rows; the
  honest unit is the world: 23 worlds, one event. C3 stays FAIL by the
  letter; only the accounting is corrected.
* The §1 H4 decision rule I wrote myself ("FP ≥ 2 → real defect") was
  **underpowered** for the n it governed, and it fired on a 0.087
  event. A2 replaced it *before* the extension ran, and the replacement
  is the measurement that decides — not the count.

## Deliverables

* `research/RESULTS_V7B.md` — the turn's report.
* `research/CAMPAIGN_RESULT.md` — the line frozen as a result (axis B
  main findings, axis A economics table, limits stated plainly,
  artefact index).
* `results/analysis_v7b.txt`, `results/verify_v7b_independent.txt`,
  `results/calib_v7b_scale.txt` — frozen outputs.
* `results/matrix_v7b/` — 1000 held-out runs (new data, ~4.2 MB JSON).
* `research/PREREG_V7B.md` — preregistration + A1/A2.

## Fork for the owner

The line is at a natural stopping point and I recommend **closing it**.
If continued, the one item that is a real gap rather than a refinement
is the line's own declared missing instrument: **continuous confidence
(a posterior, not a threshold verdict)** — `EPISTEMIC_VERDICT.md` §6 and
§9 flag it as the never-closed gap, and it is the only remaining item
that changes the *picture* rather than the *precision*.
