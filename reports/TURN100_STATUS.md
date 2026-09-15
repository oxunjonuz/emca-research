# TURN 100 STATUS — THE ACTIONABLE DECOY

Owner directive (msg_00100 / op_39d83261dc8e, acknowledged): (1) a world
where the decoy becomes an attractor or carries a cost so identifier
arms diverge BEHAVIOURALLY; (2) unlock the chain (Treasures > 0) — the
12-step window suspected too strict; (3) direction 3: test the
stratified identifier on a curiosity-driven trajectory generator.

Full measurements: research/RESULTS_V31.md.

## What was done (one turn, full cycle)

1. **Diagnosed treasures 0/21 by tracing a live 16k life** (not by
   guessing): the key goal was UNSATISFIABLE (v3 never emitted
   info["key"] → goal expired 3× → demoted forever: self_model
   ['key']=[0,3] every seed) and there was NO navigation channel to the
   treasure (scent covered tree/key only; the agent wandered off with
   the key and the 12-step window died). The window itself was NOT the
   primary blocker.
2. **Built TerrariumV31**: decoy moved to `grasp` (actionable — a
   chosen action, not a universal one), ring drops a collectable chime
   at the bell (attractor), storms furious at −2.4/step (cost),
   info["key"] + treasure scent + wanting-refresh (chain completable).
   All four brute-force gates UNCHANGED; random re-measured 0 treasures
   in 5×6000. verify_env_v31.py: 21/21 PASS.
3. **Toy check (TZ.md rule) caught four defects before the matrix**:
   the vacuous ring goal (satisfied by any ring anywhere in 5 steps —
   fixed to chime collection); the stand-ON-the-tree grasp interface
   (agent starved beside a visible tree, 22 deaths/4000 — fixed to
   dist≤1 in the env, re-verified); the storm-competence gap
   (treasure-goals monopolised storms, agent 9–10 cells from the only
   food, 16/29 deaths mid-storm — fixed: tree scent overrides goal
   pursuit in storms); a KeyError on the chime feature. W1–W8 ALL PASS.
4. **Matrix 8×3×16000, 24 runs, 0 failures.** Determinism audited by
   independent subprocess re-runs (edge sets + behavioural counters
   bit-for-bit).

## Verdicts

* **Directive (1) — behavioural divergence: YES.** Arms differ in
  reward/fruits/chimes/grasp@bell/deaths per seed. The turn-99
  inertness ("the false edge never feeds a goal") is closed.
* **Honest inversion, not softened:** in THIS geometry the false belief
  PAYS (+1226/+996 reward in seeds 1–2, wash in seed 3): the decoy's
  attractor sits on the foraging ground, so the believing arm's
  ring-pursuit concentrates where the fruit is (wasted bell-grasps:
  1195 vs 1488 per life). Epistemic correctness costs ~8% of reward
  here. The sign is a property of the chime/tree geometry, not of the
  identifiers — v3.2 (chimes away from the tree) would invert it.
* **Directive (2) — chain unlocked: YES.** Treasures 0.7–1.0/life for
  planner arms (was 0.0 everywhere). The 12-step window stands; the
  owner's "окно слишком строгое" hypothesis is refuted in its strong
  form — what was too strict was the goal machinery (unsatisfiable key
  goal, no treasure scent, no wanting-refresh).
* **Directive (3) — curiosity generator: rejection is structural.**
  The curious arm (v2.5c identifier, novelty policy) rejects the decoy
  3/3 with decoy data present (assoc accepts 3/3). Honest boundary: it
  does not SURVIVE this world (86 deaths/16k, 6 fruits) — novelty does
  not feed in a fury world; a surviving curiosity arm would need the
  storm-competence fix, which re-entangles it with goals.

## Open threads (priority order)

1. **v3.2 — inverted geometry:** chimes land AWAY from the tree (one
   parameter: chime placement). Prediction (pre-registerable): the
   false belief then COSTS (ring-pursuit pulls the believer off the
   foraging ground), and v2.5c wins. This turns the honest inversion
   into a measured contrast — the same identifiers, opposite sign.
2. **Curiosity that survives:** decouple the generator from competence
   (e.g. curiosity budget + storm override) — tests whether direction 3
   can be run without entangling the generator with survival.
3. **press→lever at 16k** (turn-99 boundary): still below min_p=0.02 for
   all arms at 16k in v3.1 too; the noise-floor question is unchanged.

## Artifacts

* research/RESULTS_V31.md — full report (this turn's measurements).
* results/matrix_v31/*.json — 24 runs.
* env_terrarium_v31.py / verify_env_v31.py / agent_emca_v31.py /
  run_life_v31.py / driver_v31.py / toy_v31_check.py — the v3.1 stack.
* Turn-99 files untouched.
