# TURN 101 STATUS — v3.2: SEPARATED GEOMETRY + DO-INTERVENTIONS + CURIOUS SURVIVOR

Directive: op_51a5f449bf5e (msg_00101), three tasks, one turn, full
house-rule cycle. Result: all three tasks closed by measurement; one
criterion (T2b) an honest FAIL with the mechanism explained; one
turn-100 claim corrected (dead code in the curious arm).

## Ledger

* env_terrarium_v32.py — the world (chime far zone, grasp cost 0.6,
  altar gray-zone true edge). verify_env_v32.py 22/22 PASS.
* agent_emca_v32.py — V32Mixin (place check, dist1 grasp, storm proxy
  via chime scent, stale-fallthrough, ring→chime pursuit), AgentV32*
  identifier arms (lineage untouched), AgentV32Prober (gray detection,
  alternated blocks, Fisher exact, verdict gating), AgentCuriousPure /
  AgentCuriousSurvivor (REACHABLE novelty — the turn-100 correction).
* probe_unit_check.py 7/7 PASS; diag_prober_trace.py — the probe debug
  trail (4 harness defects fixed: probe at wrong cell, patch-blocked
  trials, drift onto the patch, no return to the altar).
* toy_v32_check.py W1–W9 ALL PASS (after catching 3 agent defects:
  blind grasp shortcut, dist-2 grasp loop, invisible storm signal).
* Matrix: 10 arms × 3 seeds × 16000 = 30 runs, 0 failures, 0
  truncations (steps-field audit). Determinism: bit-identical fresh
  re-runs (v2.1, v2.5c, prober).
* analyze_v32.py — fresh process, disk-only. T1 PASS (sign inversion,
  2/3 seeds), T2a/c/d PASS, T2b honest FAIL (power-limited: 1/3 CAUSAL,
  2/3 UNRESOLVED, no false REJECT), T3 PASS (0.7 deaths, +82% reward),
  T4/T5 PASS.
* research/RESULTS_V32.md — the full report.

## Headlines

1. **Sign inversion confirmed** (task 1): the false belief stopped
   paying (+1274/−2888/+1040 per seed to the rejector; was +1226/+996
   to the believer in turn 100). Magnitude modest (~1%): the trap
   geometry still feeds bell-zone presence.
2. **Do-interventions work and are priced** (task 2): the gray-zone
   true edge (wait→patch_berry, RR≈1.9) is invisible to every passive
   arm (0/3) and resolved only by the probe's alternated trials
   (CAUSAL in seed 3, p<0.001; UNRESOLVED — not falsely rejected — in
   seeds 1–2 at ~55% per-life power). Cost: ~33% reward.
3. **The curious survivor dominates** (task 3): 0.7 deaths (pure
   curiosity: 93), reward 39436 (+82% over the best goal arm),
   exploration rate 100% of pure. Roaming + competence beats goals in
   a rare-event world.
4. **Turn-100 correction**: the v31 AgentCurious had unreachable dead
   code — its novelty generator never ran; the turn-100
   generator-independence claim was unsupported. Re-established here
   on a policy that runs (traced: 16000/16000 steps).

## Open threads (priority order)

1. **Prober power** — the honest limit: at RR≈1.9, n≈180/arm, per-life
   power ~55%. Options: (a) longer lives / fewer competing goals;
   (b) sequential testing (stop early on strong draws — seeds 3's
   p<0.001 needed half the trials); (c) accept UNRESOLVED as the
   honest default and accumulate verdicts ACROSS lives (persistent
   episodic memory of experiments — the EMCA episode store already
   survives resets).
2. **The second resource coincidence** — the far zone holds the cold
   berries AND the chimes; the rejector's chime-chasing parks it in
   the post-flip berry zone. A world with the chime zone barren of
   everything would sharpen the inversion (predicted: the gap grows
   from ~1% to ~8%, mirroring v3.1 in reverse).
3. **curious_surv has no chain** — 0 treasures: novelty does not plan.
   The obvious synthesis: curiosity as the EXPLORATION policy inside
   the goal planner (goal sets the destination, novelty picks the
   route). One mixin, one matrix.
4. **The prober's passive coupling** — the probe's trials feed the
   passive stratified counters (seed 1: the passive layer found the
   altar edge on probe data). Unplanned, sound, and it suggests the
   cleanest next question: is the passive layer's failure on the altar
   edge a data problem (no aligned trials) rather than a mechanism
   problem? A passive arm FORCED to wait at the altar (scripted) would
   separate those.

## Provenance

* RESULTS_V32.md (this turn's report), TURN101_STATUS.md (this file).
* results/matrix_v32/*.json — 30 runs; matrix_v32_analysis.txt — the
  independent analysis output; matrix_v32_driver.log — driver log.
* All identifier lineages untouched (v2.1/v2.2/v2.5c imported as-is).
* No network use. No hanging processes. Repositories untouched.
