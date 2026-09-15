# RESULTS V3.1 — THE ACTIONABLE DECOY: KNOWLEDGE BECOMES BEHAVIOUR

Owner directive (msg_00100 / op_39d83261dc8e): «Следующий шаг — создать
мир, где этот признак становится аттрактором или несёт издержки, чтобы
агенты с разными идентификаторами начали различаться поведенчески.
Разблокировать полную цепочку (Treasures > 0)… Проверить Направление 3
(Learning-Progress / Любопытство).»

All three parts are done in one turn. This file reports the measurements;
TURN100_STATUS.md holds the turn's ledger.

---

## 1. The world: TerrariumV31 (env_terrarium_v31.py)

TerrariumV3 kept whole (weather linger trap, chain lever→door + key in
cold + treasure, rare calm trees, survival, regime flip, all four
brute-force gates unchanged: order gate, 12-step key window, spawn
dist>5, 300-step door window). Three deltas, each tied to a measured
defect of the turn-99 matrix:

* **The decoy moved from `eat` to `grasp` (the actionable form).** The
  storm tree's fruit hangs high: gathered with `grasp` from a cell
  ADJACENT to the tree (dist≤1), +25 energy / reward 8. `grasp` is a
  chosen action, not a universal one — so the false edge (grasp,
  bell_rang) is exactly the kind of edge a planner can act on. The linger
  structure is unchanged (storm tree within 2 of the bell, ring 0.40 vs
  0.01, interventional oracle: P(ring|do(a)) equal for every action —
  verify_env_v31.py 21/21 PASS).
* **The ring is collectable and the bell zone is an attractor WITH a
  cost.** A ring drops a chime within 2 of the bell; walking onto it
  collects +0.5. Storms are FURIOUS: −2.4 energy/step (vs −0.1 calm
  warm). Lingering by the bell in a storm is survivable but expensive —
  the storm tree is the only food that pays for the fury. Attractor
  (chimes) and cost (fury) in one geometry, as the directive asked.
* **The chain is completable again.** The turn-99 trace showed treasures
  0/21 had TWO causes beyond the 12-step window: (a) the key goal was
  UNSATISFIABLE — v3 never emitted info["key"], so the goal expired 3×
  and was demoted forever (self_model['key']=[0,3] in every seed);
  (b) no navigation channel to the treasure — the agent wandered off
  with the key and the window died. v3.1: info["key"] on pickup, a
  'treasure' scent while key-in-hand + door open, and wanting-refresh
  (achieved goal kinds re-issue after a 1500-step cooldown). The gate
  parameters are UNTOUCHED — the 12-step window stays; brute-force
  re-check: 0 treasures for random in 5×6000.

Agent layer (agent_emca_v31.py): identifiers imported UNTOUCHED (v2.1
pooled / v2.2 spec / v2.5c stratified-RR / assoc-only). New: the RING
goal (satisfied only by COLLECTING a chime — the first draft satisfied
it on any bell_rang anywhere, which made it vacuous: satisfied in 5
steps by chance, measured), grasp competence (tree in 3×3 view → grasp),
storm competence (during a storm the tree scent overrides goal pursuit —
the trace showed treasure-goals monopolising storms while the agent
wandered 9–10 cells from the only food: 16/29 deaths mid-storm), and
AgentCurious — the direction-3 arm whose trajectory generator is
novelty/learning-progress, not goals.

## 2. Toy check (TZ.md rule) — W1–W8 ALL PASS, pre-registered

8000 steps, 3 seeds, 5 arms (toy_v31_check.py). The toy pass caught
three defects before the matrix: the vacuous ring goal (above), the
stand-ON-the-tree grasp interface (agent starved beside a visible tree —
22 deaths/4000; fixed to dist≤1 in the ENV, re-verified), and the
storm-competence gap. Final: W1 deaths≤25 [20,26,19] · W2 treasures≥1
[2,1,0] — **the chain completes; the turn-99 0/21 defect is closed
without touching the gates** · W3 decoy bites v2.1 3/3 + assoc 3/3 ·
W4 v2.5c rejects 3/3 · W5 true edges 3/3 · W6 behavioural divergence
3/3 · W7 curious arm rejects 3/3 with decoy data present (assoc rate
0.127–0.165) · W8 determinism PASS.

## 3. Matrix (8 conditions × 3 seeds × 16000 steps, 24 runs, 0 failures)

| condition | reward | deaths | fruits | chimes | grasp@bell | levers | keys | treasures | decoy in causal | decoy in assoc |
|---|---|---|---|---|---|---|---|---|---|---|
| emca_v21 (believes) | 12879.8 | 40.0 | 1558 | 132 | 2453 | 12.0 | 119 | 0.7 | **3/3** | 3/3 |
| emca_v22 (believes) | 12879.8 | 40.0 | 1558 | 132 | 2453 | 12.0 | 119 | 0.7 | **3/3** | 3/3 |
| emca_v25c (rejects) | 12158.3 | 41.3 | 1467 | 119 | 2255 | 9.7 | 132 | 1.0 | **0/3** | 3/3 |
| emca_nocausal (assoc) | 10486.7 | 45.0 | 1258 | 126 | 1913 | 11.0 | 113 | 1.0 | 3/3* | 3/3 |
| curious (v2.5c + novelty) | 467.5 | 85.7 | 6 | 78 | 98 | 6.3 | 63 | 0.0 | **0/3** | 3/3 |
| random | −0.7 | 87.0 | 36 | 46 | 552 | 57.7 | 40 | 0.0 | – | 0/3 |
| qlearn | 571.3 | 87.3 | 99 | 43 | 771 | 1.3 | 10 | 0.0 | – | – |
| ngram | 2050.5 | 79.0 | 283 | 36 | 1661 | 2.3 | 4 | 0.0 | – | – |

*nocausal's "causal" column is its assoc view at the causal-grade
threshold. Determinism: fresh seed-1 re-runs reproduce edge sets AND
behavioural counters bit-for-bit for v2.1, v2.5c, curious (independent
subprocess audit).

### The directive's core question: do the arms now DIFFER behaviourally?

**YES — the turn-99 inertness is broken.** Per-seed reward v2.1 vs v2.5c:
13556 vs 12330 (seed 1), 11506 vs 10510 (seed 2), 13578 vs 13636 (seed
3). Fruits, chimes, grasp@bell, deaths, treasures all diverge. The
identifier choice is no longer epistemic decoration: what the agent
BELIEVES about grasp→bell_rang now changes what it DOES.

**But the sign is the honest headline: in this world the false belief
PAYS.** v2.1 beats v2.5c by +1226 (seed 1) and +996 (seed 2); seed 3 is
a wash (−58). Decomposition (exact, reward = fruits×8 + berries×1 +
chimes×0.5 + treasures×20 − deaths×5): the entire gap is FRUITS — v2.1
gathers 155/117 more fruits per life. Mechanism, measured by tracing
grasp events: the believing agent's ring goal routes it to grasp WHERE
THE TREE IS (its false edge grasp→bell_rang is exercised at the tree,
where grasping yields fruit); the rejecting agent's ring goal has no
causal route, so it navigates to the bell TILE and grasps the bare bell
— wasted grasps at the bell zone: v2.1 1195 vs v2.5c 1488 per life. The
decoy zone IS the foraging ground (the linger trap requires the tree at
the bell), so believing the decoy concentrates ring-pursuit where the
fruit is. **The false belief is accidentally adaptive — an honest
structural result, not softened: in a world where the spurious
correlation's attractor sits on top of a real resource, epistemic
correctness costs ~8% of reward.** The direction of the cost is a
property of the GEOMETRY (chime/tree coincidence), not of the
identifiers: a world where chimes land away from the tree would invert
it. That world is one parameter (CHIME_MAX_DIST placement) away and is
the natural v3.2.

### The chain: Treasures > 0 — closed

v2.1: [2,0,0] · v2.2: [2,0,0] · v2.5c: [2,1,0] · nocausal: [1,0,2] ·
curious/baselines: 0. Mean treasures per life: 0.7–1.0 for the planner
arms (turn 99: 0.0 everywhere). The fix was NOT the 12-step window (it
stays, and random still leaks 0/5×6000): it was the unsatisfiable key
goal (info["key"] now exists), the missing treasure scent, and
wanting-refresh. The owner's hypothesis «окно 12 слишком строгое» was
tested and REFUTED in its strong form: the window is completable — what
was too strict was the goal machinery around it.

### Direction 3 (curiosity generator): the rejection is structural

The curious arm (v2.5c identifier, novelty-driven policy) REJECTS the
decoy 3/3 with the decoy data present (assoc rate 0.117–0.131 over
271–325 grasp attempts; the assoc layer accepts it 3/3). v2.5c's
rejection survives the change of trajectory generator — it is not an
artifact of goal-driven lingering. **Honest negative, not softened:**
the curious agent is not a viable SURVIVOR in this world — 86 deaths
per 16k life, 6 fruits (vs 1467 for the goal-driven arms): novelty
seeking does not feed in a fury world. It answers the identifier
question (its data still discriminate the decoy) but not the survival
question; a curiosity arm that survives would need the storm-competence
fix, which would make it goal-driven again — the generator and the
competence are entangled in this design. Stated as a boundary.

### Baselines

random/qlearn/ngram die 79–87× per 16k (planner arms: 40–45) — the
competence gap survives the harsher world. ngram reaches 2050 reward on
berries+chimes but never the chain.

## 4. What this turn establishes

1. **The identifier question is now behavioural** (directive part 1):
   arms differ in reward, foraging, and wasted grasps — measured, per
   seed, deterministic.
2. **The chain completes** (part 2): treasures 0.7–1.0/life with all
   brute-force gates intact; the blocker was the goal machinery, not the
   12-step window.
3. **The rejection is generator-independent** (part 3): v2.5c rejects
   the decoy under goal-driven AND novelty-driven trajectories.
4. **The honest inversion:** in this geometry the false belief pays
   (+8% reward) because the decoy's attractor sits on the foraging
   ground. Knowing the truth and profiting from it are different
   questions — and the second depends on where the world puts its
   resources, not on the identifier.

## 5. Files and provenance

* env_terrarium_v31.py, verify_env_v31.py (21/21 PASS) — the world.
* agent_emca_v31.py — goal/planning layer + AgentCurious; identifiers
  imported untouched from turn 99.
* run_life_v31.py, driver_v31.py, toy_v31_check.py (W1–W8 PASS).
* results/matrix_v31/*.json — 24 runs, full logs.
* Analysis: fresh script reading only the JSONs; determinism audited by
  independent subprocess re-runs.
