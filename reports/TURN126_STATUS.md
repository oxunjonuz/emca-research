# TURN 126 STATUS — V8: three declared gaps closed in one world

Owner message: msg_00126 (the V1–V7B line stays frozen; do not build a
seventh world for the same question; close several items from
`CAMPAIGN_RESULT.md` §5 at once — continuous confidence,
self-reinforcement as a battery, amortization of the price of knowledge;
decide the order, whether a toy pass is needed, where the real fork is;
stop only at a real fork or a result that changes the hypothesis).

## Decision taken

One new world, three batteries, because the three items are not
independent of each other and are all priced by the same quantity: what
the agent pays to know. Deliberate design choice, declared before any
code: **the world is the smallest one in which the three claims are well
posed** — a clocked three-action bandit, not a room. The room, the
navigation, the survival economy and the do-intervention protocol were
each the subject of an earlier world; here they would have added ways for
the three mechanisms to fail for irrelevant reasons. Declared as
amendment A1 with its reason, and the lineage break (`candidate_gen`,
`arbitration_v8.py`, the decoy) is stated in prereg §6 rather than left
implicit.

## What was done this turn

1. Read the frozen state from disk: `CAMPAIGN_RESULT.md` §5 (the six
   declared limits), `EPISTEMIC_VERDICT.md`, the frozen v7 code
   (`candidate_gen`, `arbitration`, `env_terrarium_v7`, `agent_emca_v7`,
   runners, verifiers) and the V7/V7B reports. Nothing answered from
   recall; verified matrix integrity first (110 files, combined sha256
   `1f5a66e3…`, unchanged).
2. Wrote `research/PREREG_V8.md` **before the first line of v8 code**:
   world, arms, gates {0.20, 0.10, 0.05, 0.03} straddling the campaign's
   own frozen `RR ≥ 1.3` ratio, the three-leg gate, the batteries, the
   order of checks, and the deletions.
3. New code: `env_terrarium_v8.py`, `agent_emca_v8.py`, `run_life_v8.py`,
   `driver_v8.py`, `verify_env_v8.py`, `toy_v8_check.py`, `analyze_v8.py`,
   `verify_v8_independent.py`, `factcheck_v8_report.py`.
4. Ran the world oracle (E1–E6 ALL PASS), the toy/synthetic units
   (W1–W7 ALL PASS incl. three live negative controls), then the matrix
   (**404 runs × 16 000 steps**), the primary analysis, the independent
   pass, and a fact-check of the report's own numbers.
5. **Found and fixed a real defect** (A16) and **re-ran the whole matrix**
   on the fixed code.

## Results (all frozen on disk)

| claim | result |
|---|---|
| **C1** belief number beats the verdict | **PASS at all four gaps** — +7 288 / +28 150 / +15 488 / +7 550, all three legs |
| **C2** the gain is information, not activity | **PASS** — +203 350 / +86 275 / +26 312 / +7 738 over the coin |
| **C3** the verdict collapses to the coin below the gate | **FAIL — my prediction refuted**; threshold stays +10 825 above the coin at 0.05 (sign test 6/8 fails) and is indistinguishable at 0.03 (+188) |
| **C4 / C4b** the verdict's price | **PASS** — 8.3/40.9/70.5/79.6 % of life gathering vs 4.5/10.4/24.9/26.8 %; evidence-demand multiple 21.7× / 12.7× / 3.4× / 5.6×, non-convergent at 0.03 |
| **C5** the number orders the truth | **PASS** at all gaps (p ≤ 1e-16) |
| **A1** the loop's size = 1.25·p_edge − p_bg | **PASS** — graded inflates 0.2130 → **0.3273** (analytic 0.3375); rot, same world, stays 0.1967 |
| **A2** the loop pays | **PASS** — graded−rot is +403 588 with consistency vs +203 925 without; the difference (+199 663) equals graded(pon)−graded(poff) **exactly** |
| **A3** the loop is the world's, not the estimator's | **PASS** — the control reads the true gap in the same world |
| **A4** the belief identifies the truth | **PASS** — graded 64/64 and 64/64; coin 0.328 / 0.359 (its 1/3 band) |
| **A-null** truth=off is at chance | **PASS** |
| **F1** reuse pays, growing with q | **PARTIAL / two rows FAIL** — monotone in q but **negative** at q = 0, 0.25, 0.5 (−48 163 / −36 688 / −25 762), crossing zero between 0.75 and 1.0 |
| **F2** reuse is free at high q | **PASS at q = 1.0** (44.9 % of fresh's gathering), missed at 0.75 (89.6 %) |
| **F3** at q = 1 reuse reaches the oracle | **PASS** — 99.2 % |

**The turn's headline, in one line:** knowledge is worth what the world
pays for it, and this turn priced three things the campaign had never
priced — the evidence rule's own demand, the feedback of acting on a
belief, and the lifetime of the fact. The belief number beats the verdict
everywhere but by a *bounded* margin in reward and a *large* one in
effort; the self-reinforcement loop is real, is the world's, and is worth
about a second agent's worth of advantage; amortization pays only when
the world's facts outlive their use, and is a tax when they do not.

## Verification of this turn's own work

* **World oracle** (`results/verify_env_v8.txt`): E1 ground truth
  recomputable from (seed, q); E2 stickiness matches q for all five
  values; E3 the four gaps measured to ±0.005 and truth=off flat
  (spread 0.0032); E4 the persistence multiplier reproduces 1.25·p_edge
  and the rotation earns no bonus; E5 determinism across fresh
  processes; E6 the noise floor stated (sd 5 154, 2·SEM ≈ 3 645).
  **ALL PASS.**
* **Toy / synthetic units** (`results/toy_v8_out.txt`): W1 sign correct
  (1.000) and no signal at gap 0; W2 the frozen rule's firing curve below
  its ratio gate is **non-monotone** (peak 0.463 at n = 200, 0.408 at
  n = 2000) while γ is monotone; W3 the evidence-demand ratio 8.33 inside
  the declared [8, 18]; W4 the persistence arithmetic; W5 determinism;
  W6 τ=0 and rot never act on a belief; W7 three **live** negative
  controls that do go red. **ALL PASS.**
* **Independent pass** (`results/verify_v8_independent.py`, different
  code, disk only, no import of the analysis and no trust in the agent's
  log): ground truth recomputed from the seed in all 404 files — 0
  mismatches; accounting identities PASS; fresh arms' counts == the raw
  trace — 0 mismatches; **carry arm's counts == `int(0.5·previous) + raw`
  — 960/960 rows**, a stronger check than the equality it replaced;
  per-epoch agent hits == the world's own pay counts — 0 mismatches; the
  persistence contrast reproduces the analytic inflation ±0.03; every
  contrast sign and direction agreement reproduced; determinism
  byte-identical in three fresh processes (faba82f5…, b8fab957…,
  ccd12bf2…). **ALL PASS, zero discrepancies.**
* **Fact-check of the report's own numbers** (`factcheck_v8_report.py`,
  55 assertions re-derived from the frozen matrix, importing neither the
  analysis nor the report): **ALL PASS**, after it caught two wrong A2
  numbers I had typed from the superseded first pass. The report now
  carries the measured values.
* **Code freeze**: all 404 matrix files are newer than the newest code
  edit (checked by mtime), so the matrix was produced on one frozen
  code revision. Hashes: `env_terrarium_v8 c9e807082353`,
  `agent_emca_v8 d42ff252f4c6`, `run_life_v8 11de36970c0c`,
  `driver_v8 64a47fa9a31c`, `analyze_v8 99477d5046d0`,
  `verify_v8_independent 387d42b653d2`.
* **The frozen V1–V7B material was never written to.** The V7 matrix's
  combined sha256 was re-verified before the work; no v8 script reads or
  writes `matrix_v4…v7b/`.

## Honest corrections to my own record (all in the prereg's amendment log)

* **A10–A12, A17** — three of my preregistered predictions were **wrong**
  and are corrected in writing, not edited away: the frozen rule below
  its ratio gate is **non-monotone in n** rather than silent; the
  evidence-demand ratio is ≈8.5, not 6.0; and A1's control row demanded
  an effect the control cannot have.

* **A16** — a **real defect**, found by the independent pass and not by
  the analysis: the environment's `obs()` built the observation before
  advancing the clock, so every epoch-boundary trial was filed one row
  late (4 470 individual mismatches on the first pass). My first
  attribution named the agent; that was wrong, and the amendment says so.
  Fixed, regression-checked (`C1`/`D1`), and **the entire matrix was
  re-run** — same seeds, same thresholds, nothing else changed. Per-run
  sums were unaffected; the per-epoch battery was not.
* **A negative control that did not go red** — the first W7 control
  (the single-control ratio) landed inside the band it was supposed to
  violate; it was replaced by one that does. A check that cannot fail
  checks nothing.
* **First-pass analysis superseded, not edited**: kept on disk as
  `results/analysis_v8_FIRSTPASS_superseded.txt`.

## Deliverables

* `research/RESULTS_V8.md` — the turn's report.
* `research/PREREG_V8.md` — frozen preregistration with amendments
  A1–A17, each dated with its reason.
* `results/matrix_v8/` — 404 runs × 16 000 steps (new data).
* `results/analysis_v8.txt`, `results/verify_v8_independent.txt`,
  `results/verify_env_v8.txt`, `results/toy_v8_out.txt`,
  `results/factcheck_v8.txt` — frozen outputs.
* `results/analysis_v8_FIRSTPASS_superseded.txt` — the pre-fix analysis.

## Fork / recommendation

The three declared gaps of `CAMPAIGN_RESULT.md` §5 are closed, each with
a measured shape rather than a pass/fail. The one place a further
measurement would change the *picture* rather than the precision is
**C1's economics**: the belief number's reward advantage is small (1.3 %–
4.3 %) precisely because the harvest's marginal value is low in this
world. I do **not** recommend building that world: the line was frozen
once for the reason that further worlds stopped buying new things, and
the three results above are the answer to this directive. If the owner
wants the round closed, the preprint column for v8 is the natural
deliverable.
