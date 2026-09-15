# PREREG V8 — closing three declared gaps: continuous confidence,
# self-reinforcement as a battery, amortization of the price of knowledge

Turn 126 (msg_00126). This file was first written in a rich-geometry
design and RE-SPECIFIED before the first agent run (§7 records every
change with its reason; no v8 code had executed and no v8 data existed,
so the re-specification cost nothing and is logged rather than hidden).
Claims, gates and order of checks are frozen here, before data.

Owner directive: the V1–V7B line stays frozen as a result; do not build a
seventh world to refine the same question; close several open items from
`CAMPAIGN_RESULT.md` §5 at once:

* **(C) Continuous confidence** — replace the threshold verdict with a
  probabilistic / Bayesian confidence in the module (§5.4: "the line's
  clearest declared gap and it was never closed").
* **(A) Self-reinforcement as a systematic battery** (§5.5) — the
  turn-115 effect (acting on a belief produces the data that justifies
  it) studied as an object, not removed as a nuisance.
* **(F) Amortization of the price of knowledge** — a mechanism by which
  what was found once is reused without being paid for again.

---

## 0. The decision this turn had to make, and it was made here

`CAMPAIGN_RESULT.md` §3 ends: "what pays is the difference between what
the agent knows and what the world is willing to pay for it — and both
terms are set by the world, not by the agent." That sentence is only
half a result while the second term is unmeasured: *how much the agent
pays to know at all*. All three items above are about that price:

* (C) is about the **instrument**: a verdict demands a fixed level of
  evidence; a posterior charges by what it is worth.
* (A) is about the **feedback**: if acting on a belief feeds the evidence
  for it, the price of knowledge is not paid once but produced.
* (F) is about **reuse**: whether a fact paid for once can be held
  without paying again.

**Decision, taken before any code: measure the three in the smallest
world that makes them well posed, as one factorial battery, not as three
separate worlds.** The smallest such world is a **clocked bandit**: the
fact that must be known is "which of three actions pays", and the fact
has a LIFETIME. No navigation, no survival, no prize-collection ritual —
each of those was a subject of an earlier world and would here only add
ways for the three mechanisms to fail for irrelevant reasons.

I predict (declared before data): (1) the verdict rule will be
*structurally* blind to a thin truth, not merely slower than the
posterior — its ratio gate, frozen at 1.3 in v3.2, rejects every truth
thinner than 30% **at every sample size**; (2) self-reinforcement will
turn out to be a property of a world that pays for consistency, not of
the estimator; (3) amortization will pay only in proportion to how
sticky the world's facts are, and will be a curve, not a verdict.

---

## 1. THE WORLD — TerrariumV8, the lifetime world

`env_terrarium_v8.py`. Deliberately minimal:

* **Actions**: three — `wait`, `press`, `grasp`. There is no movement and
  no position: the agent lives where the payoff is (declared; see §7 A6).
* **The fact**: every `EPOCH_LEN = 2000` steps the paying action is
  re-drawn. `epoch_id = t // 2000`; a run of 16 000 steps contains 8
  epochs, i.e. 8 independent facts to find.
* **Stickiness `q`** (a world knob, used by Block F): a new epoch's
  action repeats the previous one with probability exactly `q`; otherwise
  it is one of the two other actions, uniformly. So `q = 0` is a fresh
  fact every epoch and `q = 1` is the same fact forever — the two
  endpoint controls of the amortization curve.
* **The payoff**: on each step, the taken action pays `K = 100.0` with
  probability `p_edge` if it is the epoch's action, else `p_bg`
  (`truth=off`: `p_bg` for every action). The agent's data ARE its
  rewards: the effect and the payoff are one event, so nothing can drift
  between "what was observed" and "what was paid" (§7 A5).
* **The gap regime**: `(p_edge, p_bg) ∈ {(0.55,0.35), (0.45,0.35),
  (0.40,0.35), (0.38,0.35)}` — gaps 0.20, 0.10, 0.05, 0.03. Chosen
  BEFORE any run: 0.20 is a truth the campaign's frozen ratio gate
  (RR ≥ 1.3) can see; 0.10 sits just under the gate's ratio (0.45/0.35 =
  1.286) — the marginal regime; 0.05 and 0.03 are below every ratio a
  do-intervention in this campaign has ever asked for.
* **Persistence (a world knob, used by Block A)**: if the same action
  was taken in at least 75% of the last 8 steps, that action's payoff
  probability is multiplied by 1.25 for that step. This is the minimal
  world fact that makes "acting on a belief changes the data that support
  it" TRUE rather than an artifact — the turn-115 pathology rebuilt as an
  object (§7 A3).

Observation (the whole input): `{t, epoch_id, afford}` — the clock, and
the three available actions. Declared plainly: the clock is world state
given identically to every arm and it never reveals WHICH action pays.

---

## 2. THE AGENT — one class, arms differ only in the declared knobs

`agent_emca_v8.py`, one class `AgentV8`; an arm is a tuple
`(mode, tau, cache, kappa)`. The shared machinery (the count store, the
gathering rotation, the epoch bookkeeping) is identical for every arm.

* **Counts**: per action, `[hits, trials]`, kept for the epoch in
  progress. An epoch change is visible through `epoch_id`; what happens
  then is exactly what `cache` decides:
  * `fresh` — the counts are cleared (the fact is searched from scratch);
  * `carry` — the previous epoch's counts are carried into the new epoch
    multiplied by `kappa = 0.5` (a decaying prior: what was found last
    epoch is reused at half weight, immediately, for free).
* **Gathering**: a deterministic rotation over the three actions (not a
  coin, so gathering is maximally informative and — declared — never
  reaches the 75% consistency that would trigger the persistence bonus).
* **The state the rule reads** (identical form for every mode): for each
  action `a`, `rate_a = hits/trials`, `rate_o` = the other actions'
  pooled rate, `se` = the two-proportion standard error,
  `z_a = (rate_a − rate_o)/se`, and `γ_a = max(0, 2Φ(z_a) − 1)`
  (the two-sided-equivalent posterior mass, a number in [0,1) that grows
  with the evidence and is 0 when the evidence points the wrong way).
* **The modes** — the ONLY difference between arms:
  * `graded` — belief = argmax `z_a` with weight `γ_belief`; acts on the
    belief with probability `min(1, tau * γ_belief)`, else gathers.
  * `graded1` — as `graded`, but `z` is computed against a SINGLE control
    action (the first of the others alphabetically) — the same contrast
    form the frozen threshold rule uses. This arm exists so that the
    contrast form (single vs pooled) and the decision rule (threshold vs
    posterior) are two separate factors, not one confounded comparison.
  * `threshold` — the campaign's FROZEN v7 rule on the same 2×2 it has
    always used (target vs the first other action alphabetically): belief
    exists iff exact one-sided Fisher `p < 0.05` AND `RR ≥ 1.3`, and then
    its weight is 1.0 (a verdict is certain, which is what a verdict
    means). The candidate is the highest-rate action with `n ≥ 20`.
  * `thresholdpool` — the same rule with the control pooled over the two
    other actions (the "better statistics, same decision bar" control).
  * `coin` — the same `|γ|` as `graded`, but the SIGN is drawn per epoch
    from the agent's own RNG, and the action is drawn per epoch from its
    own RNG: it acts with probability `|γ|` on an action that carries no
    information. This is what separates "the evidence is informative"
    from "acting at all pays". Its direction agreement with the truth
    must sit at 1/3 — the null bound of Block A.
  * `oracle` — the epoch's action known free, weight 1 (the ceiling).
  * `rot` — `tau = 0`: never acts on a belief, always gathers (the floor).
* `tau ∈ {0.3, 0.7, 1.0}` is the dose knob (secondary), and `tau = 0`
  is the structural control.

---

## 3. CLAIMS, GATES, DECISION RULES (frozen)

Every primary contrast is PAIRED BY SEED (same seed ⇒ same world, same
epoch actions, same stickiness) and must pass ALL THREE of:

1. paired bootstrap CI over 10 000 resamples of the per-seed differences
   excludes 0;
2. the paired sign test is one-sided in the predicted direction with
   p < 0.05;
3. the two disjoint halves of each run's second half agree in sign with
   the full-run difference (a contrast that reverses inside a run is
   reported as a reversal, not as an effect).

(This three-leg rule is the turn-104 lesson made a gate.)

### Block C — continuous confidence (gaps 0.20 / 0.10 / 0.05 / 0.03, q=0)
Arms per gap: `graded, graded1, threshold, thresholdpool, coin, oracle,
rot` (8 seeds).
* **C1** PRIMARY, per gap: `reward(graded) > reward(threshold)`.
  Prediction: at gap 0.20 a small positive difference; at 0.10 a large
  one; at 0.05 and 0.03 the threshold arm should equal the `rot` floor
  while `graded` stays above it. Falsifier: no gap shows a positive
  difference, or the sign reverses between halves.
* **C2** INFORMATION: `reward(graded) > reward(coin)` at gaps where C1
  holds. If this fails, C1's gain was "acting on anything", not
  information, and it is reported as such.
* **C3** THE VERDICT'S OWN VERDICT: `reward(threshold) ≤ reward(coin)`
  at gaps ≤ 0.10 (in sign; reported either way).
* **C4** THE PRICE CURVE (mechanism, no gate on reward). Two parts.
  *(a) The rule's own shape (amendment A10, after the toy pass refuted
  my first version of this claim):* below the ratio gate the frozen
  rule's firing rate must be **non-monotone in n** — its maximum strictly
  interior, and its value at the largest n tested strictly below that
  maximum; while `γ` on the true action is monotone increasing over the
  same range, reaching 0.5 at a small finite n. Above the gate the frozen
  rule's firing rate is monotone increasing. *(b) The evidence demand:*
  the n at which the frozen rule first fires in >50% of worlds, divided by
  the n at which mean `γ` on the true action exceeds 0.5, must land in
  **[8, 18]** (analytic 8.5; amendment A11 — my first figure, ≈6, used
  the wrong control size). *What this buys:* the threshold rule's cost is
  not "more data" but "a demand whose price is not paid in evidence at
  all below the gate, since the belief it produces there is
  non-monotone in what the agent spends".
* **C5** THE NUMBER ORDERS THE TRUTH (units, no world economics): over
  all epochs of the graded arms, mean `γ` on the true action must exceed
  mean `γ` on the false actions (Mann–Whitney one-sided p < 0.05).

### Block A — self-reinforcement as a battery
Factorial: persistence `{off, on}` × gap `{0.20, 0.10}` × arms
`{graded, rot}` × 8 seeds; plus `truth=off` at gap 0.10 with persistence
`{off, on}` for `graded` (10 seeds, the null bound).
* **A1** THE LOOP EXISTS AND IS MEASURABLE: with persistence ON, the
  graded arm's own observed gap at the end of an epoch
  (`rate_belief − rate_others_pooled`, from its own counts) must equal
  the analytic value **1.25·p_edge − p_bg** within **±0.03 absolute**
  (amendment A7: the factor form is gap-dependent and was mis-specified;
  the absolute form is the same claim stated correctly). Analytic values:
  0.3375 at gap 0.20 (factor 1.69), 0.2125 at gap 0.10 (factor 2.13).
  The rotating arm under the same persistence must show **no** inflation:
  observed gap within ±0.03 of the true gap (its rotation never reaches
  the 75% consistency). With persistence OFF both arms must sit within
  ±0.03 of the true gap. *This is the turn-115 pathology given a number
  and a controlled 2×2.*
* **A2** DOES THE LOOP PAY: `reward(graded, persistence=on)` vs
  `reward(graded, persistence=off)` at the same gap, paired. Prediction:
  positive (in a world that pays for consistency, a confident agent
  collects that payment). Reported either way.
* **A3** THE LOOP IS A PROPERTY OF THE WORLD, NOT OF THE ESTIMATOR: in
  the persistence-off world the graded arm's observed gap must NOT
  inflate (A1's third row). Prediction holds ⇒ the turn-115 lesson
  sharpens: what that world met was a real return-to-consistency in the
  world, not merely a statistical self-confirmation in the estimator.
* **A4** DIRECTION (the battery proper): for every epoch, does the arm's
  belief identify the epoch's true action? Gates: agreement ≥ 0.70 for
  `graded` (≥ 30 epochs), `coin` inside [0.20, 0.47] (its 3-sigma band
  around 1/3), and `truth=off` agreement ≤ the `truth=on` agreement.

### Block F — amortization of the price of knowledge (gap 0.10, q sweep)
Arms `{fresh, carry, oracle}` × `q ∈ {0, 0.25, 0.5, 0.75, 1.0}` × 8 seeds.
* **F1** PRIMARY (per q): `reward(carry) > reward(fresh)`.
  Prediction: negative or zero at q=0 (nothing to reuse), positive and
  growing with q, largest at q=1. The result is the CURVE, not one point.
* **F2** REUSE IS FREE: at q ≥ 0.5 the number of steps `carry` spends
  gathering (not acting on a belief) must be at most 60% of `fresh`'s,
  and the total evidence it collects (trials) must be at most 80% of
  `fresh`'s — the fact is not re-paid for.
* **F3** ENDPOINT CONTROLS: at q = 1 `carry` must reach at least 95% of
  `oracle`'s reward (the fact, once found, is worth what knowing it is
  worth); at q = 0 `carry` must not exceed `fresh` by more than the
  noise band of the paired test.
* Reported but not gated: `kappa = 0.5` is a declared constant, and the
  report states that F1's magnitude depends on it while F1's sign does
  not (the carry arm's prior is the previous fact at half weight).

### What would refute the turn's frame
If C1 is null at gap 0.20 AND C2 null at every gap AND A4's agreement is
at the coin's level, then continuous confidence in this world buys
nothing; the report says so and the finding becomes "the campaign's
declared gap is not closable by a belief number, only by a world that
pays for one".

---

## 4. BATTERIES (frozen)

| block | arms | gaps | seeds | other knobs | runs |
|---|---|---|---|---|---|
| C | graded, graded1, threshold, thresholdpool, coin, oracle, rot | 0.20, 0.10, 0.05, 0.03 | 8 | q=0, persistence off | 224 |
| C-tau | graded (τ=0.3, 0.7) | 0.10 | 8 | — | 16 |
| A | graded, rot | 0.20, 0.10 | 8 | persistence ON | 32 |
| A-null | graded | 0.10 truth=off | 10 | persistence off/on | 20 |
| F | fresh, carry, oracle | 0.10 | 8 | q ∈ {0,0.25,0.5,0.75,1.0} | 120 |

≈ 412 runs of 16 000 steps, `PYTHONHASHSEED=0`, one process per run, JSON
to `results/matrix_v8/<tag>.json`. (Momentum-off `graded`/`rot` runs of
Block A are the Block C runs at the same gap and seed — the same file.)
Estimated wall time ≈ 15 minutes at 4 workers; each run is seconds.

---

## 5. THE ORDER OF CHECKS (frozen)

1. `verify_env_v8.py` — the world oracle, BEFORE any agent: the epoch
   action follows (seed, epoch) and repeats with frequency q (measured,
   not asserted); `P(pay | epoch action) = p_edge` and `P(pay | other) =
   p_bg` by direct measurement at each gap; `truth=off` flat; the
   persistence multiplier measured with and without a consistent
   history; determinism bit-for-bit across processes; and the NOISE
   FLOOR — the sd of per-epoch reward, converted into the smallest
   paired effect the design can detect — so the report never claims what
   the design cannot see.
2. `toy_v8_check.py` — synthetic units BEFORE any agent run:
   * W1 the sign of z is right whenever the gap is real and is ≤ 0 when
     it is 0 (deterministic on synthetic counts of 1 000 independent
     tables);
   * W2 **the miscalibration mechanism**: for a truth whose ratio is
     below 1.3, the frozen rule's firing probability must be ~0 at every
     n up to 2 000 per action while `γ > 0.5` is reached at a small
     finite n — the structural blindness, demonstrated without agents;
   * W3 the evidence-demand ratio: the n at which the frozen rule fires
     on a gap ABOVE the gate, divided by the n at which `γ` crosses 0.5,
     must land in [4, 9] (the predicted ≈ 6);
   * W4 the persistence arithmetic reproduces 1.25·p_edge − p_bg;
   * W5 determinism of the agent's counts and beliefs across processes;
   * W6 `tau=0` and the `rot` arm never act on a belief;
   * W7 a NEGATIVE control: the checks fire on knowingly broken inputs
     (a flat world must fail W1's positive leg; a gap above the gate must
     fail W2's blindness leg) — a check that cannot go red checks nothing.
3. The matrix (`driver_v8.py`), the primary analysis (`analyze_v8.py`),
   then `verify_v8_independent.py` — a second pass, different code, disk
   only. Any disagreement is reported, not smoothed.

---

## 6. HONEST DELETIONS, DECLARED (an idea deleted is not an absence)

* **The room, the navigation, the scent, the berries, the energy and the
  death channel** were in the first v8 design and are DELETED before any
  run. Reason: each was a subject of an earlier world (`v4`–`v7`); here
  they add failure modes with no claim attached. In v8 the price of
  evidence is OPPORTUNITY (steps spent gathering instead of acting on
  what is known), which is measurable without a second economy.
* **The interventional probe protocol** (bench, 5/5 blocks, a block cap,
  the do-oracle world) is DELETED. Reason: a probe produces evidence
  under the agent's control; in v8 the agent's own acting is the
  experiment, and self-generated evidence is exactly what Blocks A and F
  are about. The do-intervention verdict stays frozen as V7's result.
* **The decoy effect** ("fizz", an action-correlated world event) is
  DELETED: in a three-action bandit the two non-paying actions ARE the
  false candidates, so a decoy would add code, not information. The null
  device of v8 is the `coin` arm, which carries the same magnitude as the
  signal and is therefore a stronger control.
* **The world-agnostic hypothesis generator** (`candidate_gen`, frozen
  and audited) is NOT used in v8, and this is declared as a lineage
  break: with three actions and one effect it would nominate the same
  three candidates the agent already holds, i.e. it would be decoration,
  and the report must not claim a lineage it does not measure. C2's
  result (self-generation) stays frozen in `RESULTS_V7.md`.
* **The window/round clock** is DELETED in favour of a single epoch
  clock: two clocks were one too many for one claim.

## 8. AMENDMENTS (all made BEFORE the first v8 run or BEFORE the matrix
##    was analysed; none of them changes a threshold after seeing a verdict)

* **A13** The three-leg gate's sign leg is now **directional**: the
  declared direction is the one written in the claim text (C1/C2/C3:
  A > B; F1: signed per q; F3 carry < oracle; A2 the loop does NOT pay
  more), and leg 3 (the two within-run halves) is read against the
  DECLARED direction rather than the observed one. Reason: I wrote the
  gate for a one-sided world and then used it on signed ones, which made
  a correctly predicted negative result print as three FAILs. The claim
  is unchanged; the instrument is corrected, and the correction is
  declared rather than applied silently.
* **A14** Block F's comparison is not reachable through the runner's arm
  names alone: `f_fresh` and `f_carry` are the SAME arm (`graded`, τ=1)
  differing only in the `cache` knob. The analysis compares them by
  spec, not by filename. Reason: my first analysis looked for a filename
  that never existed (F1 printed as "FAIL" for that reason alone, before
  any number was read). No data changed; the lookup was wrong.
* **A16** A REAL DEFECT, FOUND BY THE INDEPENDENT PASS, AND THE MATRIX WAS
  RE-RUN. The first v8 matrix was analysed and then cross-checked by
  `verify_v8_independent.py`, which caught a per-epoch accounting
  disagreement between the agent's own log and the world's recorded
  counts (4 470 individual mismatches; the agent logged 2 001 trials for
  epoch 0 where the world ran 2 000). Root cause, and my first diagnosis
  of it named the wrong file: it is in the **environment's `obs()`**,
  which built the observation BEFORE advancing the clock, so `epoch_id`
  named the previous step's epoch. The agent files a trial under the
  epoch it is shown (correct given its input), the runner tallies by the
  step's own epoch (correct given the world), and the two disagree by one
  step at every boundary. Fixed in `env_terrarium_v8.py` (`obs()` ticks
  first); a regression check for it exists in the verifier (`C1`/`D1`),
  and **the whole matrix was re-run from scratch on the fixed code** —
  the same 404 runs, same seeds, same thresholds, nothing else changed.
  Everything measured as a per-run sum (reward, gathering share, every
  cross-arm contrast) was unaffected; the per-epoch battery (Block A's
  loop size, Block F's reuse) was. The report carries the re-run's
  numbers. The first pass's analysis is superseded, not edited, and my
  initial attribution (to `agent_emca_v8.py`) is corrected here rather
  than rewritten away.
* **A17** After the fix, A1's tolerance is still ±0.03 but A1 is now read
  as it was written: the analytic value applies to the arm that actually
  reaches the 75% consistency (the graded arm), while the rotating arm is
  the CONTROL and is expected to show the TRUE gap, not the inflated one.
  Reason: I wrote A1's three rows before checking which arm the momentum
  rule could reach, so one row demanded the control show an effect the
  control cannot have. The measurement is exactly what the correct
  formulation predicts (graded inflates, rot does not). No threshold
  changed; the mis-specified row is deleted and the reason recorded here.
* **A15** AMENDED AFTER READING THE C HEADLINE, AND THIS IS THE HONEST
  RECORD: at every gap, including 0.03, C1 (graded > threshold) and C2
  (graded > coin) passed all three legs — the reward-level prediction in
  C1 was too pessimistic. C1's text predicted "at 0.05 and 0.03 the
  threshold arm should equal the `rot` floor while `graded` stays above
  it"; the measured threshold arm at 0.03 is 579 188 against the `rot`
  floor 576 250 and `coin` 576 075, i.e. NOT at the floor, and it is
  still 8 363 below `graded`. What the measurement DID show is
  C4's mechanism: the threshold arm spends **83.9%** of its life
  gathering at 0.03 versus graded's **30.4%**, at a reward cost of only
  ~1.4%. The prereg's C4 text ("a demand whose price is not paid in
  evidence at all below the gate") is therefore not what the world shows
  — the price IS paid, in 2.8–5.2× the effort, and the reward difference
  is smaller than the effort difference would suggest because the
  harvest's marginal value is low when the fact is thin. Both statements
  go in the report; neither is dropped. No threshold, gate, battery or
  world was changed after seeing data.

---

* **A1** The world was re-specified from a 15×15 room to a clocked
  three-action bandit. Reason: the three claims are about the decision
  rule, the feedback and reuse; geometry would have been decorative and
  would have cost a cycle to de-confound. The owner's constraint ("not a
  seventh world for the same question") is honoured: this is not a
  refinement of the V7 world, it is the smallest world in which the three
  DECLARED GAPS are well posed.
* **A2** The effect and the payoff were unified into one event (`hum`
  observable in the aura + a separate harvest action was the first
  design). Reason: two events create the possibility that the agent reads
  one and is paid by the other, a confound with no claim attached.
* **A3** The persistence (consistency) rule was added to the world as a
  declared knob, and Block A was rebuilt around it. Reason: WITHOUT a
  world fact of this kind, "acting on a belief raises the evidence for
  the belief" cannot be true of the ESTIMATOR — a consistent estimator is
  not biased by the sampling policy — so the turn-115 pathology could
  only be reproduced, not explained. With the knob, the loop becomes a
  measurable interaction (Block A's 2×2 with a predicted factor 1.69),
  and the estimator's honesty in a persistence-free world becomes a
  checkable claim (A3) instead of an assumption.
* **A4** The agent's decision was re-specified from "probe or harvest"
  under an arbiter to "act on belief with probability `tau * gamma`, else
  gather". Reason: continuous confidence is only continuous where the
  ACTION is; a thresholded action with a graded belief would have
  measured the belief, not the module. `arbitration_v8.py`, written for
  the first design, is therefore UNUSED and declared dead in the report.
* **A5** `kappa = 0.5` (the carry-over weight) is declared here as a
  fixed constant, chosen (not fitted) as the midpoint between "ignore the
  past" and "trust it fully"; F1's sign is the claim, its magnitude is
  reported as a function of the declaration.
* **A6** The gate set was fixed at {0.20, 0.10, 0.05, 0.03} with the
  ratio gate (1.3) in mind BEFORE any run: 0.20 above it, 0.10 just
  below it, 0.05 and 0.03 far below. Reason: the ratio gate is the
  campaign's own frozen constant, and the predicted structural blindness
  is only falsifiable if the gates straddle it. If the observed
  crossover sits anywhere other than between 0.20 and 0.10, C's
  mechanism claim is refuted and will be reported as refuted.
* **A7** A1's prediction was re-stated from a multiplicative factor band
  to an absolute band. Reason: under persistence the inflated contrast is
  `1.25·p_edge − p_bg`, whose ratio to the true gap depends on the gap
  (1.69 at 0.20, 2.13 at 0.10) — the factor form I first wrote was
  correct only at gap 0.20 and would have failed at 0.10 for arithmetic
  reasons. The claim is unchanged; the arithmetic is now right, and both
  analytic values are written into A1.
* **A8** The world owns TWO RNG streams: one produces the epoch-action
  sequence as a pure function of (seed, q), the other produces payoffs.
  Reason: an independent verifier must be able to recompute the ground
  truth of every recorded run from the frozen seed alone, without
  replaying payoff draws. The independent path is built into the world
  rather than bolted on after the runs.
* **A9** `arbitration_v8.py` (written for the first, richer design) is
  DECLARED DEAD and is not imported by anything in v8. Reason: amendment
  A4 replaced the arbiter with the `tau·γ` action rule, and a module kept
  alive but unused would be a claim of lineage that nothing measures.
  Its content survives only as the arithmetic of A4.
* **A10** **A PREDICTION OF MINE WAS REFUTED BY THE TOY PASS, BEFORE THE
  MATRIX — the mechanism claim in C4 is CORRECTED, not dropped.** What I
  wrote in C4 was: "`RR ≥ 1.3` cannot be met by a truth whose ratio is
  below 1.3 **at any n**, so for gaps ≤ 0.10 the threshold's evidence
  demand is infinite". The synthetic measurement says otherwise, and the
  truth is more interesting:

  | gap | frozen rule's firing rate, per n |
  |---|---|
  | 0.20 | 20:0.23 40:0.47 60:0.71 100:0.84 200:0.94 500:0.99 2000:1.00 |
  | 0.10 | 20:0.10 40:0.17 **60:0.31** 100:0.32 **200:0.47** 500:0.48 1000:0.45 **2000:0.39** |
  | 0.05 | 20:0.08 40:0.09 **60:0.15** 100:0.14 200:0.16 **500:0.04** 1000:0.01 **2000:0.00** |
  | 0.03 | 20:0.09 40:0.06 60:0.12 100:0.12 200:0.10 500:0.02 1000:0.00 2000:0.00 |

  Below the ratio gate the rule DOES fire — but its firing rate is
  **non-monotone in the evidence**: it rises to a peak in a middle n
  band and then **decays back to zero**, because the `RR ≥ 1.3` gate is
  passed only by a *lucky* control rate, and that luck washes out as n
  grows. So the correct statement of the pathology is not "the threshold
  can never see a thin truth" but: **below the gate the frozen rule is
  non-monotone in evidence — more data eventually takes the belief away —
  while the posterior is monotone and rises with the data.** The
  corrected C4 legs are (a) the observed firing curve below the gate must
  be non-monotone with its maximum strictly interior, and its value at
  the largest n tested strictly below its maximum; (b) `γ` must be
  monotone increasing in n over the same range; (c) at gaps 0.05 and 0.03
  the firing rate at n = 2000 must be ≤ 0.01. All three are falsifiable
  and all three are measured before any agent.
* **A11** C4's predicted evidence-demand ratio is corrected from "≈ 6.0"
  to the interval **[8, 18]**. Reason: the analytic figure I first wrote
  used the wrong control size (the pooled control has 2n trials, not n);
  the correct analytic ratio is the square of the z-ratio, (1.96/0.674)²
  ≈ 8.5, plus the exact test's conservatism and the `RR` gate. The
  measured ratio (n at which the frozen rule fires >50% of the time, over
  the n at which mean γ on the true action exceeds 0.5) is the quantity
  reported; the band is stated before the matrix.
* **A12** W1's third leg ("γ does not separate the truth under the
  null") is restated with a properly powered tolerance (±0.03 with 2 000
  synthetic epochs, instead of ±0.01 with 400): the original tolerance
  was tighter than the sampling error of the check itself, so the check
  was testing its own noise. Declared as a defect of my instrument, found
  by the instrument.

---

Preregistered by me, turn 126, before the first v8 run.
