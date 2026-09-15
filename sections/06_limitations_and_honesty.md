# Section 06 — Limitations and honesty: every refuted prediction, every defect

*The owner asked for "честно названные ограничения" in every section and "ничего не
приукрашивать". This section collects them in one place so none is buried in a
report footnote. Nothing here is new — every item is quoted from a frozen report,
and the report is named.*

---

## 0. Deliberate minimality, stated as a design choice and not as a defect

*Added turn 157, owner directive `op_3645deda2339`.*

The worlds are small on purpose. Each safety campaign adds **one** mechanism to the
world of its predecessor and nothing else (the one-extension rule), so every result is
a causal statement about the added mechanism rather than a comparison between unrelated
designs. This is what makes the boundary of each defence **quantifiable** — a measured
price (0.25 per unit of harm), a measured truncation curve, a measured cliff exactly one
grid cell wide — and what makes the campaign's own instrumentation errors cheap to
catch and report. **The minimal world is therefore a methodological choice that buys
high cleanliness at low compute cost, not the work's main weakness.** The phenomenon
reproduces independently in a different synthetic sandbox (Che & Wu 2026, `MoneyWorld`;
section 05), which is evidence that it is fundamental enough to be visible early.

**What remains an honest limit is the other side of the same coin, and it is stated
plainly, not hidden:** the worlds are minimal, so **transfer to a large-scale agent
with a rich observation space is not shown and is not claimed**. The claim is about the
*structure* of the phenomenon and the *boundaries* of specific defences, not about
scale. The convergence with an independent study is evidence about fundamentality, not
about transfer.

---

## 1. Refuted predictions (preregistered, then measured false)

A preregistration that is never wrong is a preregistration that was not written
before the run. These are the ones that came back false, reported with the measured
sign rather than re-described.

| campaign | prediction | what was measured | report |
|---|---|---|---|
| v10 | **P6** — the world-veto arm's reward ≥ the given-rule arm's (a world rule costs the agent nothing) | **refuted**: the veto *withholds* the payment, so it charges the agent the forfeited reward (241.00 vs 241.05 low; 252.00 vs 252.60 high, every seed) | `RESULTS_SAFETY.md` §3 |
| v10 | **P7** — the forager's keeper dies sooner than B0's | **refuted as stated**: both die at t = 2039, because both exhaust the 30-unit stock in the first ~40 steps; the real difference is total harvest (13368 vs 1353), not death time | `RESULTS_SAFETY.md` §3 |
| v11 | **W6** — the harm curve is non-monotone (relaxes once the inflation clears the accept bar) | **refuted**: the harm is `[5,5,6,30,30,30,30]` — it steps up once and **never comes back down**, because all 30 units are gone by t = 39, before the arbiter exists | `RESULTS_WIREHEAD.md` §4 |
| v12 | **H11 null** — "the credit balance cannot show up in harm" | **refuted as written**: it shows up in harm at exactly the declared rate (cap 5 → 6 drains, cap 10 → 12) | `RESULTS_FORGER_V12.md` §6 |
| v12 | **H6** — `total_reward == tick × payments`, and zero reward after the signal dies | **refuted in 4/10 seeds**: the bound agent falls back to the rich patch, post-death reward exactly `0.05 × rich_steps`, and in those seeds the aquifer is drained and the keeper dead | `RESULTS_FORGER_V12.md` §7 |
| v13 | — (all ten hypotheses held) | — | `RESULTS_LEDGER_V13.md` §2 |
| v14 | **HA4** — the attestation boundary is a flat one-step cliff at lag 14 | **refuted**: the harm is **truncated**, not prevented (6/8/14/30 drains at lag 14/15/20/50), because the guard reads the statistic at *every* decision, not once | `RESULTS_ATTESTED_V14.md` §2 |
| v18 | **HE6** — with no forger the widening arm still asks to widen | **REFUTED**: on the no-forger path `w_widen` still issues 30–6380 widening requests (it asks unconditionally), but the harm stays 0 and nothing is widened — the request is a property of the arm, not of the bribe | `RESULTS_ENFORCED_V18.md` §5 |
| v19 | **HQ4d** — the `B = 1` sweep never reaches the harmful candidate in time | **REFUTED by the author's own defect fix**: the first version was true because an off-by-one made the sweep spend two blocks on candidate 0; with the declared one-candidate-per-block sweep it **does** reach the breach (18 drains, spend 9.03) — but still does not win, because 9.03 > 9.0 | `RESULTS_ADAPTIVE_V19.md` §2.1 |
| v20 | **HV4** — in `mode="open"` the failure is invisible: "`refused` is False in both" | **REFUTED as stated**: the per-step `refused` flag **does** change (honest 30–6380 refused steps per seed → bought 0). What is invisible is the **`task` claim**, not the refusal counter; the failure is unobservable *in this experiment* only because the frozen arms never read `o["scope"]` (AST-audited) — a property of the agent as built, not of the channel | `RESULTS_BRIBED_ENFORCER_V20.md` §4 |
| v16 (headline) | the doctor **never** drains the aquifer (260 cells) | **refuted by the author's own replication (turn 152)**: on 30 fresh seeds it drains on **2**, on 70 on **3 (4.3 %)** — the frozen survival layer parks a starving agent on the harmful tile; the *contrast* survives, the *absolute* form does not | `RESULTS_N40_REPLICATION.md` §2 |
| v8 | **C3** — the verdict rule collapses to the coin floor below the gate | **refuted**: it stays above the coin at 0.05 (+10 825) and is indistinguishable at 0.03 (+188) | `RESULTS_V8.md` §1 |
| v8 | **F1** — reuse pays and grows with q | **half-right**: monotone in q but **negative** until q = 1.0; two rows FAIL by the gate | `RESULTS_V8.md` §3 |
| v3.3 | **W2** — the dynamic grasp cost tips the believer below the rejector | **refuted**: the believer's grasps are mostly *competent* (at the tree), so the belief's price is carried by the harvest-time channel | `RESULTS_V33.md` §2 |
| v3.3 | **T4c** — the chain arm stays under 40 deaths | **refuted**: 56–69 deaths; the object-novelty layer itself is death-neutral, the deaths are the price of the curiosity policy under scarcity | `RESULTS_V33.md` §3 |
| v9 | **H3i/H3ii** — the union nominates the true pair and probes its top candidate ≥8/10 | **FAIL** (10/10 on / 6/10 off; 6/10) — reported as post-hoc readings, not verdict flips | `RESULTS_V9.md` §3 |
| v7 | **C3** — verification rejects the decoy with FP = 0 | **FAIL by the letter** (FP = 1), then **explained**: the gate demands a property a calibrated rule does not have at any sample size (null rate 0.488 %) | `RESULTS_V7B.md`, `CAMPAIGN_RESULT.md` §2.3 |
| v2 | **E2** — memory gives ≥2× recovery after a context reset | **FAIL by the letter**: 1.35×; the threshold was set without calibrating the environment's difficulty — an error of the preregistration, recorded | `RESULTS.md` |
| v2 | **E3** — baselines complete the chain 0 times | **PASS with a caveat**: random gets 4.7 — brute force opens the door; the treasure is not a strict planning test against brute force | `RESULTS.md` |
| v2 | **E4** — adaptation to the regime flip | **FAIL by the letter, PASS by spirit**: EMCA degrades 1.5× vs Q-learning's 2.5×, but the "no worse than before" bar was not met | `RESULTS.md` |

---

## 2. Defects found in the author's own work (reported, not hidden)

These are the failures of the *instrumentation* — the checks, the analyzers, the
verifiers — as distinct from refuted hypotheses. The campaign's own pattern: the
carrier of the result was repeatedly not the hypothesis but the discipline around
it, and several times the thing it caught was the author's own code or prose.

### 2.1 Checks that could not fail (vacuous controls)

* **v13 NC5** contained `or True` — a check that cannot go red. Found re-reading the
  file against the discipline just applied to v12's arms; replaced with a measured
  control, and NC6 added.
* **v14 D2** was first written `check(..., fg_pay_check() if False else True, "")` —
  a vacuous pass; found before running, replaced with a measured non-vacuity check.
* **v12 NC2** asserted an impossible conjunction, so it could never fail; replaced.
* **v15 NV1** (first negative control) corrupted only 1000 of 16000 steps, moving
  a0_share to 0.234 — not enough to fail the indifference check, so the control could
  not go red. Fixed to corrupt the whole trace (now 0.000, correctly red).
* **v8's toy suite**: one negative control did not go red (the single-control ratio
  landed inside the band) and was replaced by one that does — "a check that cannot
  fail checks nothing".
* **v9 `verdict_advantage`** tested only "the CI excludes zero", which labels a
  significant **loss** as ADVANTAGE; the prereg gate is directional, and the code now
  is too.
* **v17's independent pass** first asserted the agent module's sha256 as
  `h == "<placeholder>" or True` — a check that could not go red, found by noticing
  the placeholder in its own printed output; replaced with the **real frozen hash as a
  literal**, and a second module's hash added.
* **the preprint verifier's own negative-control campaign** (turn 152) reported 10/10
  corruptions caught and it was **false**: `pdflatex` ran with a truncated `PATH`, the
  build died on a font, and the "red" came from the broken toolchain. A control that
  leaves the build broken is now marked **invalid**, not caught; the honest run gave
  6/10 and the four survivors became four new checks.
* **the authorship checks** (turn 158) asserted that the two author names appear
  *somewhere* in the extracted PDF text. Removing them from the **title page** therefore
  left the verifier **green** — the contributions section still contained both names. A
  check satisfied by any occurrence does not check the page it names. Fixed by requiring
  the names inside the first 1500 extracted characters; the campaign now catches both
  removals. Found by running the corruptions against the new checks, not by reading them.
* **the PDF's own metadata** was unverified until turn 158: `Author:` was empty, so a
  reader inspecting the file rather than the first page would have seen no authorship at
  all. `\hypersetup{pdfauthor=...}` added, and the metadata is now pinned in two
  independent verifiers.

### 2.2 Verifiers and analyzers that over-claimed or compared the wrong thing

* **v13's independent pass asserted the receipt split partition over all 260 cells,
  and 40 cells refuted it** — all out of scope (the frozen v10/v12 anchor worlds
  carry no `receipt` key). **The check was wrong, not the world.** Fixed by declaring
  scope explicitly (200 in, 60 skipped).
* **v14's analyzer compared the wrong cells and produced a false REFUTED** (HA5
  compared v14 no-forger cells against v13 *bribe* cells).
* **v16's independent verifier over-claimed**: its first A4 demanded full-field
  equality between the pump and the wide arm — not what H3 says, and false for a
  declared structural reason. Fixed to check the harm fields H3 names.
* **v14's oracle check C3 compared the wrong pair of steps** (t=13 under lag 13 with
  t=14 under lag 14). **The author's expectation was wrong, the world was right.**
* **v11's oracle**: two checks that could never pass (O5's wrong expectation about the
  scent convention; Z1's asymmetric dict comparison) — both fixed *in the oracle*; the
  world was right in both.
* **v12's T5 and NC2**: a 1e-12 tolerance against a 997-term float accumulation
  (residual 6e-12) went red on a correct ledger; and the first negative control
  asserted an impossible conjunction.
* **v3.3's analyzer** conflated the world-richness axis with `place` — caught by a
  `KeyError` (a coding defect that would have silently produced a wrong table).
* **v9's logging defect**: `candidates_seen` logged the score in position 2, so a
  reader filtering on the source label filtered nothing. The decision path was never
  affected; the matrix was re-run from scratch and every decision-relevant field was
  bit-identical (0 diffs / 180 cells), with the pre-fix matrix preserved as evidence.
* **v8's independent pass caught a real world defect**: the environment's `obs()`
  built the observation before advancing the clock, so `epoch_id` named the previous
  step's epoch. **The entire 404-run matrix was re-run from scratch on the fixed
  code.**
* **v13's first world** returned a freshly recomputed observation, silently shifting
  it by one step; fixed to return v11's own dict with `receipt` added.
* **v14's world** had a floating-point PATH bug (recovering the body's payment as the
  delta of a cumulative receipt, drifting in IEEE double). Fixed to
  `paid_count_delta × tick`; **the pre-fix exploratory cells were deleted**, not kept.

### 2.3 A number written in prose and never re-derived

* **v13's `agent_ledger_v13.py` comment** claimed the lagged rule "classified 6 of 36
  rich steps as non-draining, exactly the wrong six". The diagnostic behind that
  figure was **not on disk**, so it was re-measured from scratch: the naive rule
  *calls* 6 of 36, but **disagrees with the correct rule on exactly ONE step** — the
  one that drained the last unit. "The wrong six" was itself wrong. The comment is
  corrected and the evidence file saved. **The lesson, in the author's own words:
  any number written about the work must have a file on disk, otherwise it is a
  memory, not a measurement.**

### 2.4 A first-pass matrix deleted rather than kept

* **v16's first pump broke its own brake** (returned the frozen survival branch
  unguarded; the pump harvested through the hole and drained all 30 at every tick).
  H3 caught it. Fixed; the matrix was re-run from scratch — and **the first pass was
  deleted (`rm -rf`), not kept as a superseded artefact**, unlike v11 where the first
  pass was preserved. **Stated plainly in the turn note: that first pass is not on
  disk and cannot be re-examined.**

### 2.5 Over-claims in the author's own preregistrations, corrected rather than dropped

* **v14's prereg** asserted `a_failclosed ≡ v13 l_ledger` when there is no
  attestation. Measured, they share the **verdict** in the low world (25/5) but **not
  the statistic** (fail-closed reads 0.0, `l_ledger` reads 0.05). Stated in the
  report because correcting a prediction after the fact is exactly what must not be
  done silently.
* **v12's report's own first §-block** presented the *lifetime* statistic as if it
  were the value *at the crossing* — different numbers; the analysis now says so.
* **v12's author's own edit duplicated the prereg's §9** and left §7 stranded after
  it — found by reading the file back rather than trusting the edit.
* **v8's report** typed A2's two numbers from a superseded pass; the factcheck caught
  both (+199 663 and +152 775, not +199 950 and +148 850).
* **v8's Block F** had a defect where the analysis compared the same arm to itself
  because the persistence knob was not threaded into its lookup; the SUPERSEDED
  first-pass analysis is kept on disk.
* **v14's prereg** over-claimed in a second place (HA4's flat cliff) — refuted, above.

### 2.6 A survivor in a mutation campaign, printed as a kill

* **Lean M10** (T5b constant n/4 → n/2, looser) was printed as a kill; it is a
  **survivor** — the weaker bound is provable (`m10_followup.lean` does it), and the
  red is an artefact of the mutant's own `calc` block being pinned to `n/4`. The
  honest tally is **6 semantic + 1 type-level + 2 syntactic + 1 survivor = 10**, not
  the engine's 7 semantic. The classifier is a string rule and **must not be reported
  as a verdict**.
* **Lean T1** carried `0 ≤ bΔ` and `0 ≤ M` which its proof never used — a dead
  hypothesis, exactly what a premise campaign would report as a survivor, so it was
  **removed** rather than kept as decoration.

### 2.7 The axis substitution (the largest methodological defect of the whole campaign)

* **Turn 104** generalised an economic measurement into a verdict about the
  architecture, substituting the verdict axis the charter had preregistered. Found and
  corrected at turn 116 (`EPISTEMIC_VERDICT.md`), and the correction **restored the
  preregistered frame** rather than inventing a new one. Recorded in section 01 §3.

---

## 3. Declared limits, by campaign (unchanged from the reports)

**v1–v9:** n = 10 seeds for the v4–v7 contrasts; v5 numbers under a random hash seed;
C3's FN = 1 honest; continuous confidence missing (later closed as far as v8's world
allowed); self-reinforcement tested once (later built as a battery in v8); the v7
oracle arm is an analytic device, never in a fairness verdict.

**External tests:** only the epistemic half is testable on frozen Sachs data (the
interventions were assigned in 2005); the arms are statistical decisions, not an
agent; the permutation null is an anti-conservative control for the pooled arm and
cannot test its own α = 0.05 calibration; discretisation was the author's, not
bnlearn's; the author's own attempt to reproduce the published 8/0/9 **failed** and is
reported as a failure; direction (edge orientation) is lost in the port; pgmpy's PC
and HillClimbSearch are `PYTHONHASHSEED`-dependent (the same defect class found in the
campaign's own competence at turn 115, now observed in a third-party library).

**Causal-bandit test:** 1000 sims/cell, not the paper's 10 000; the observational half
is a declared adaptation (A1'); the supplementary two-parent instance is the author's,
not published; the `sqrt(m(q)/T)` diagnostic is a shape diagnostic only (the
Θ-constants are unpublished, so no violation of the published bound is claimed).

**Union test:** the context-specific instance is the author's, not published; the
cost-aware baseline is a declared adaptation (arXiv:2012.07058 publishes no
implementation); the exploration term is the *principle* of Algorithm 2, not its code;
no Mathlib for the Lean part; 1000 sims/cell.

**v10–v20:** the keeper is a world process, not an agent (this measures *harm done*,
not conflict between two goal-seeking systems); the economy is gentle (the frozen
agent does not die in most cells, so the price of restraint is a fraction of a small
absolute reward); **the worlds are minimal by design (see §0), and transfer to a
large-scale agent with a rich observation space is not shown and is not claimed**;
n = 10 seeds per cell in the frozen matrices, and the harm fields are
deterministic given the action trace, so their tests are sign counts, not p-values —
**and the n = 10 limit was tested, not merely declared (turn 152): a replication on 30
fresh seeds confirmed 25 of 26 headline verdicts and refuted one absolute claim (v16's
"the doctor never drains", 4.3 % of fresh seeds) — see
`../reports/RESULTS_N40_REPLICATION.md`; and again for v20 (turn 157): all six v20
verdicts hold 30/30 on fresh seeds — see
`../reports/RESULTS_BRIBED_ENFORCER_V20.md` §7**; the beacon/appraisal arms are an
instrument, not a model; the auditor is modelled as **honest** in v14 and **bribable**
in v17, but the bribe is a declared price, not a negotiated bargain; the scope filter is
a *declared* filter in the agent's own code (v16) or a declared world-side mediation
(v18), so the "complete mediation" question is answered for a declared substitute, not
for a production enforcement point; the bribe space is the declared grid (3 places × 4
ticks), so "0/12" is a statement about that grid, not about every conceivable channel;
**v19's attacker observes exactly one scalar (the world's own drain counter) and its
strategy space is a declared 16-candidate grid plus one declared resolution, so "the
learner never wins" is a statement about *that* channel and *that* decision budget,
not about learning in general — an attacker that can probe, hold out or model the
defence is not built; and v20's enforcer price is a declared scalar, so "the boundary
is bought at its price" is a statement about *that* channel, not about every way a
world-side party could be corrupted.**

**v15:** n = 10 seeds; `ig_ctx_oracle` is an analysis device, never in a fairness
verdict; the world is deliberately minimal (4 channels, binary outcomes) — the seam
claim is about the *structure* of the drive, not about scale; `REL_MARGIN=0.20` is a
declared constant (result not sensitive across 0.1–0.4); **this is not a claim of a
fundamentally new intelligence** — it is a measured intersection of three known ideas,
and the report names exactly which part comes from which source.

---

## 4. Named but deliberately NOT built (so none is smuggled in later)

Across the safety line, these were named at the time and left unbuilt, each because
building it would have been a strictly stronger object than the one being measured,
and the owner had not chosen that side of the fork:

* a forger that poisons the **epistemic** channel (the aura's `hum`/`glow` — a spoofer
  inside the inference path itself);
* a forger that **floods** (many payments per step);
* a **second competing agent**;
* a **cryptographic receipt** (unforgeability, as distinct from honesty);
* a **bought enforcer** — the natural junction of v17 and v18, since v18 locates the
  boundary in the world and v17 shows what happens when a world-side party has a price;

**Built in turn 157, and therefore removed from it:** the **bought enforcer** (now
v20, `RESULTS_BRIBED_ENFORCER_V20.md`) — the last item on this list that was a rung of
the safety line. It has its own preregistration (`PREREG_BRIBED_ENFORCER_V20.md`),
written before the first cell, and its own oracle, independent pass, factcheck and
30-fresh-seed replication. It adds **no agent code** (the agent modules' sha256 are
checked against recorded frozen literals).
* a **bargaining model** where the auditor's price is negotiated rather than declared;
* an attacker with a **richer channel than one scalar** — v19's payer sees only the
  world's drain counter, so "the learner cannot find the hole" is a statement about
  *that* channel and *that* decision budget, not about learning in general.

**Built since the first edition of this list (turn 152), and therefore removed from
it:** the **corrupted or bribed auditor** (now v17, `RESULTS_BRIBED_V17.md`) and
**external scope enforcement plus a scope-widening attack** (now v18,
`RESULTS_ENFORCED_V18.md`). Both were named here because the owner had not chosen that
side of the fork; the turn-152 directive chose it, and both are now measured. Neither
was smuggled in: each has its own preregistration, oracle, independent pass and
factcheck.

**Built in turn 154, and therefore removed from it:** the **adaptive / learning
forger** (now v19, `RESULTS_ADAPTIVE_V19.md`) — the last item on this list that was a
rung of the safety line rather than a different line. It has its own preregistration
(`PREREG_ADAPTIVE_V19.md`), written before the first cell, declaring in advance what
counts as the attacker winning.

And in the external line: the **Bayes-optimal multi-candidate** stopping rule (the DP
prices one candidate at a time) was named as a new instrument and **not built**,
because the two small wins did not suggest the multi-candidate term is where the
remaining regret lives.

---

## 5. What the honesty discipline actually caught

Worth stating as a result in its own right, because it recurs: **the carrier of the
result was repeatedly not the hypothesis but the discipline around it.**

* v11: a **non-vacuity check** caught a cell where the hypothesis would have been
  vacuously true (money elsewhere moves nothing — but the forger never went there).
* v12: **reading the frozen code back** caught the author's own false premise about
  an arm.
* v13: the author's **own prose** — a number written in a comment and never
  re-derived — turned out to be wrong, caught only by re-measuring it.
* v14: the author's **own oracle was blind to a whole configuration** (the no-forger
  path) that the matrix driver then crashed on.
* v15: the author's **own weak negative control** was caught by its own FAIL.
* v16: H3 caught the first pump breaking its own brake.
* v17: the author's **own check that could not go red** (`h == "<placeholder>" or True`)
  and a **canonicalisation defect** — the same declared auditor configuration was
  written under two filenames (`flip:0.10:0.30` vs `flip:0.1:0.3`), caught by the
  determinism check going red.
* v18: two defects caught by a **smoke test before any matrix cell**, one of which
  changed what the experiment measures.
* replication (turn 152): **the author's own absolute result** — v16's "never drains"
  — was refuted by the author's own fresh-seed replication, and separately a filename
  mismatch (`t0.30` vs `t0.3`) made a passing verdict read as a failure.
* preprint verifier (turn 152): the author's **own negative-control campaign** first
  reported 10/10 corruptions caught — and it was **false**: `pdflatex` was run with a
  truncated `PATH`, the build failed on a font, and the "red" came from the broken
  toolchain, not from the check. Fixed so a control that leaves the build broken is
  marked **invalid** rather than caught; the honest run then gave **6/10**, and the
  four uncaught corruptions became four new checks (182/182, 11/11 caught).
* v19 (turn 154): **eight of the author's own defects in one turn**, and the pattern
  held — every one was caught by a check pointed at the *check*, not at the world:
  the oracle's O3 mixed 0-based indexing with the prereg's 1-based wording (the world
  was right); O9 demanded `forged_receipt == 0` for a payer arm that *is* a paying body
  by construction; the analyzer's IDENT19b compared `_path`/`world`, which differ by
  construction; the independent pass's A1 scraped the frozen pass's text and compared
  it to itself (could not go red — v17's exact defect class, repeated); its A4/A7
  filtered by payer only and swept `a_failclosed` too; O12 first accepted
  `len(block_log) ∈ {decisions, decisions+1}`, letting a silenced `finish()` stay
  green. **Two real code defects** were found the same way: an **off-by-one in the
  sweep pointer** (all 70 sweep cells deleted and re-run), and **one stale cell** left
  in the stored matrix from before the `finish()` fix (the whole 320-cell matrix was
  deleted and re-run rather than explained away). The mutation campaign on the world
  went **9 → 3 → 1 survivors** across three passes; the last survivor is **equivalent**
  (`energy=100.0` is the declared default).
* v19's Lean item (turn 154): the mutation campaign on `IDENTIFICATION_BOUND.lean`
  left 2 survivors, and **the first version of this section described one of them
  wrongly** — it claimed M1 replaced the statement by a weaker one, when in fact M1
  changes only the *proof body* and the statement is byte-identical. Corrected by
  reading the mutant back rather than trusting the description.
* v20 (turn 157): **three of the author's own defects in one turn**, all caught by
  checks pointed at the checks: (1) the enforcer **spec grammar conflated scope and
  mode** (`"honest:0.10:0.30"` parsed as a scope name), caught by the world oracle's
  A2 on its first run; (2) **`scope_from_spec` returned the string `"none"`** for a
  `none:` spec instead of `None`, caught by the driver's 10 failing NOSCOPE cells;
  (3) the oracle's **B3 asserted that two offers of 0.05 sum to a price of 0.10** —
  **the check was wrong, the world was right** (the flip rule is per-offer, v17's
  semantics), fixed to B3/B3b and confirmed by B5's exhaustive grid check. And one
  **refuted prediction**: HV4's "`refused` is False in both" — the flag does change;
  the invisibility is narrower than the prereg claimed (see §1's table and
  `RESULTS_BRIBED_ENFORCER_V20.md` §4).

In each case the error was the author's, the world was right, and the fix was to the
check, not to the world.

---

## 6. Artefacts for this section

Every item above names its source report; the reports are in `../reports/` and
`../external/bench_cb/`, `../external/bench_ext/`. The turn-status notes
(`../reports/TURN*_STATUS.md`) carry the per-turn defect lists verbatim, including
the ones too small to reach a results report.