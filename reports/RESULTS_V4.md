# RESULTS V4 — THE EPISTEMIC-VALUE WORLD: the false belief costs a life's worth

Owner directive op_097e99fae22e (thread A of the turn-104 fork) +
op_6d6b5f5a1105 (the sharpening: causal module useful when chains
are needed, false beliefs walk away from food, raw curiosity is
costly). Full cycle in one turn: env → independent verify (10/10) →
toy BEFORE the matrix (8/8) → prereg → matrix 9×10×16000 (90 runs,
0 failures) → disk-only analysis.

---

## 1. The world: TerrariumV4 (env_terrarium_v4.py)

TerrariumV33 kept whole (scarcity, the lever→key→door chain, the
altar gray edge, the bell linger trap). Three deltas:

* **THE SECOND-ORDER DECOY — (grasp, torch_lit).** A brazier at
  (3,6), the upper-right pocket, away from every food source. In a
  storm the brazier pulses a flame (lit 60 / dark 40 steps, by the
  wind — the agent cannot influence it). The flame is a world-event:
  `info['torch_lit']` every lit step. The linger mechanism (the
  storm tree is the only food in a storm; grasping it is competent)
  correlates grasp with the flame: **P(lit|grasp)=0.66 vs 0.03,
  RR=20** in the raw world — the strongest decoy of the campaign,
  and the oracle P(lit|do(a)) is equal for all actions (spread 0.000).
* **THE TREASURY — food behind a competence chain.** The treasury
  tile '$' at (2,1) pays +10 energy / +1 reward, but eating needs a
  BANKED torch — collected by STANDING on the brazier cell while the
  flame is lit (not by grasping), inside the scorch pocket (2.2
  energy/step beside a lit brazier, on top of the storm fury 3.0).
  The warm berry zone is gated by two new walls; the berry zone
  follows the gates. Brute force: 0 treasury meals in 5×3000 random
  steps; the scripted competent chain eats 31 meals over 3 seeds
  (deaths 38–47, the v3.3 planner scale). The chain is scarce by
  design: a competent agent gets 4–7 meals per 16000-step life.
* **THE ARMOUR REMOVED — the honest finding of the disk-read.** The
  v3.2 planner has carried a hardcoded guard since turn 101: `if
  a == "grasp" and e == "bell_rang": continue` — the decoy edge's
  actionable content was silently disabled for EVERY arm in the
  v3.2/v3.3 matrices. A world that prices the false belief cannot run
  believers with that guard on. The v4 arms remove it (decoy edges
  fire like any other causal route); the identifiers themselves are
  untouched (v2.1 pooled / v2.2 spec / v2.5c stratified / assoc).

## 2. Toy BEFORE the matrix — 8/8 PASS (toy_v4_check.py, preregistered)

W1 the decoy baits the believer (v2.1 causal 3/3) · W2 the
stratified rejector rejects it 3/3 and keeps the true edges 3/3 ·
W3 the belief is BEHAVIOURALLY active: the believer's empty grasps in
the brazier pocket 330/1066/1475 per seed vs the rejector's
38/2/15; torch-goal steps 2403/2521/3590 vs 195/261/489 · W4 the
planner's own machinery reaches the treasury food (2 arm-seeds at
8000 steps) · W5 pure novelty dies hardest 3/3 · W6 random dies most
3/3 · W7 determinism · W8 no harness defects.

Two harness defects caught BEFORE the matrix: the runner read the
pocket counters from only the LAST env (respawn resets env state —
fixed by per-step accumulation); the warm berry zone after the gate
walls was 3 cells (starvation, caught by the scripted-chain verify
FAIL) — the zone now follows the gates (verify V3: 31 meals/3 seeds).

## 3. The matrix (9 arms × 10 seeds × 16000, 90 runs, 0 failures)

| condition | reward | deaths | fruits | torch | treasury | pocket-grasps | torch-goal | decoy |
|---|---|---|---|---|---|---|---|---|
| v4_believer (v2.1) | 10995 | 72.5 | 1041 | 10.4 | 0.6 | **2193** | **5560** | 9/10 |
| v4_spec (v2.2) | 13430 | 53.8 | 1273 | 16.1 | 1.1 | 115 | 1282 | 0/10 |
| v4_assoc | 15248 | 52.6 | 1430 | 15.8 | 1.8 | 712 | 2500 | 0/10 |
| **v4_rejector (v2.5c)** | 14154 | 50.2 | 1349 | 18.4 | 1.2 | 64 | 990 | 0/10 |
| v4_curious | 9833 | 67.9 | 1192 | 24.5 | 2.0 | 148 | 1587 | 2/10 |
| v4_pure | −371 | 98.1 | 1 | 0.1 | 0 | 7 | 558 | 0/10 |
| random / qlearn / ngram | −318/−155/−132 | 98–101 | 11–34 | 0 | 0 | – | – | – |

Determinism: fresh subprocess re-runs of (believer, seed 1) and
(rejector, seed 1) — byte-identical JSON. Steps-audit 90/90 clean.

### PRIMARY CONTRAST — D = reward(rejector) − reward(believer), n=10

```
seed:  1     2     3     4    5     6     7     8     9      10
D:  +2076 +5530  -536 +115 +3576 +3068 +2689 +6576 -1704 +10198
mean = +3159   sd = 3391   bootstrap 95% CI = [+1128, +5356]
sign test 8+/2−, exact p = 0.109; Wilcoxon one-sided p = 0.011
```

**By the pre-registered verdict rules: V1 PAYS — barely, and honestly
on the edge.** The CI excludes zero entirely (its floor +1128 is
nearly 4× the 300 practical floor), the Wilcoxon one-sided p = 0.011,
but the pre-registered exact sign test gives p = 0.109 (8+/2−). The
verdict rule said V1 needs mean ≥ 300 AND sign p ≤ 0.05: **the sign
test misses the bar; the CI and Wilcoxon clear it.** Reported both,
no cherry-pick: the honest label is **V1 PAYS (CI-based), sign-test
borderline** — this is the first world of the campaign where the
identifier's choice matters at the +3000-reward scale (~20% of a
life's reward), with per-seed noise ±3400 (the known weather scale).

### THE MECHANISM — decomposition (not a reward black box)

The gap is carried by MEASURED channels, correlation 0.965:
* **The fruit channel (+24664 of +31588, 78%)**: the believer's
  torch goal burns 5560 steps/life (the rejector's 990) in empty
  grasps at the brazier — 2193 pocket-grasps/life vs the rejector's
  64 — instead of storm-tree harvesting (fruits 1041 vs 1349).
* **The death channel (+1115)**: the believer dies 72.5/life vs the
  rejector's 50.2 (each death −5 reward and a respawn); the believer
  stands in the scorch pocket believing grasp banks torches.
* The treasury channel is small (the believer banks 10.4 torches but
  eats 0.6 meals: it grabs instead of standing).

This is the campaign's first second-order decoy: the believer does
not merely lose reward — **its false edge corrupts the PLAN** (which
goal monopolises the life) and **where the body stands** (the
pocket), exactly the directive's «уходит от еды в опасную зону».

### SECONDARY CONTRASTS

* **D2 (rejector − assoc) = −1093, CI [−3399, +1018], p = 0.75** —
  the assoc arm is NOT hurt: its torch plan has no causal route (the
  assoc layer's decoy does not enter `causal_edges()`), it falls to
  the same world-knowledge standing route. The arm that believed in
  the decoy was only the one whose CAUSAL layer accepted it. The
  assoc arm's pocket-grasps (712/life) come from its assoc-driven
  retry behaviour, not an edge — and it still wins 15248 (best
  planner reward: light model, few goals).
* **D3 (rejector − spec) = +725, p = 1.00** — the spec gate rejected
  the torch decoy in 10/10 (its v3.3 15/15 acceptance did not
  transfer: the RR=20 decoy is NOT in the spec gate's gray zone) —
  the spec arm is a second honest planner here, and the contrast is
  pure weather noise.
* **D4 (curious − rejector) = −4321, CI [−6535, −2187], p = 0.021** —
  curiosity is BITTER in this world: object-directed novelty banks
  the most torches (24.5/life) and eats the most treasury meals
  (2.0/life, best of all arms) but pays 68 deaths (the rejector's
  50) and −30% reward. The directive's part 3 measured: **raw
  curiosity survives the world only through its competence layers,
  and still pays a death tax for the pocket's novelty.**

### CONTROLS

* **T1 identifier stability**: decoy in believer causal 9/10 (one
  seed under the noise floor), rejector 0/10, assoc 0/10, true edges
  in rejector 10/10. The arms measured what they claim.
* **T4 pure novelty dies hardest 10/10** (98 deaths, reward −371 —
  the pocket's novelty plus the scarcity kills it outright).
* **T5 baselines**: random/qlearn/ngram 98–101 deaths, all worse
  than every planner arm.
* Treasury meals per arm (T3): the chain is scarce but reachable:
  curious 7/10 seeds, spec/assoc 6/10, rejector 4/10, believer 5/10,
  pure 0/10.

## 4. What this turn changes

1. **The identifier's choice is behavioural for the first time**: the
   v3.1–v3.3 result «знание истины не меняет ни одного действия» is
   superseded in this world — the false edge, when it is ALLOWED to
   act (armour off) and the world makes its actionable content
   costly, monopolises the believer's life and kills it 45% more
   often. The epistemic win became a survival win.
2. **The guard discovered in the disk-read** — the turn-101 hardcoded
   decoy skip — is now an explicit part of the record: every
   v3.2/v3.3 «believer» was armoured; the v4 matrix is the first
   where believers actually believed. The v3.1 «belief pays» and
   v3.3 «belief is noise» results both stand, but their believers
   never fired the decoy edge; the v4 believer is the campaign's
   first honest test of acting on a false causal edge.
3. **Curiosity's verdict is world-relative, now measured both ways**:
   in v3.2/v3.3 (pocketless worlds) curiosity with a survival
   arbiter dominated; here the SAME policy pays −30% and +18 deaths
   because the world put its novelty source in a scorch pocket. The
   filter «what actually influences survival» — the causal model —
   is what the curious arm lacks, exactly the owner's directive.

## 5. Open threads (the fork, per TZ.md)

* **(A) Power**: 10 seeds resolved the CI but the exact sign test is
  borderline (p=0.109); 5–10 more seeds on the same code would settle
  it cheaply (~5 min/run × 20) — the v3.3 lesson (power before new
  worlds) applies to THIS contrast now.
* **(B) The assoc paradox**: the arm with the LIGHTEST model wins
  reward (15248) even here — because its causal block is empty and
  its goal menu never monopolises. The v4 world prices the false
  EDGE but still does not price the causal MODEL's benefit: the
  rejector's edge did not gain it anything the assoc arm lacks. A
  world where the TRUE edge (wait→patch_berry, treasury chain) must
  be CAUSALLY known to be exploited is the remaining step.
* **(C) Close the line**: the preprint table gains the v4 column:
  epistemic win → behavioural win (armour off, second-order decoy),
  with the sign-test caveat reported.

## 6. Files and provenance

* `research/PREREG_V4.md` — written before the first matrix run.
* `results/matrix_v4/*.json` — 90 runs, steps-audit 90/90.
* `analyze_v4.py` — disk-only, frozen output
  `results/matrix_v4_analysis.txt`.
* Determinism: `/tmp/det_v4` re-runs byte-identical (restored).
