# TURN 98/99 STATUS — LINGER TRAP: SIMPLE → COMPLEX, ONE TURN

Owner directive (msg_00098 / op_94de348cf9ed; continuation op_a14554b64112
«продолжай»): simple env with only the linger trap → check the new way of
thinking; then immediately embed the trap into the large complex env →
check everything together. This is A→B from turn 97's fork, done in one
turn (spread across two provider-degraded sessions; the work is one
continuous line).

Full measurements: research/RESULTS_LINGER_V3.md.

## What was done

1. **Simple env (TerrariumLinger)** built, verified (interventional
   oracle: bell ignores actions), toy-checked, matrix 7×3×16000 complete.
   Answer: v2.5c rejects the decoy 0/3, v2.1 3/3 fooled, v2.2 2/3, true
   edges kept 3/3 everywhere. **The new way helps.**
2. **Complex env (TerrariumV3)** built: v2 chain + rare events + survival
   + regime flip + the linger trap. Brute-force leaks driven to 0/80
   (order gate, 12-step in-hand window, spawn distance >5, door window).
   Verified 20/20 PASS. Toy check caught TWO real defects before the
   matrix (trap not delivered — planner-blind tree; 6000-step dilution),
   both fixed with measurements, criteria re-registered. Matrix
   7×3×16000 complete. Answer: **identical to the simple env** — v2.5c
   0/3, v2.1 3/3, v2.2 2/3, assoc 3/3, true edges kept.
3. One competence fix in the agent (opportunistic tree eating), measured
   before adoption, applied to all arms equally. Identifiers untouched.

## Verdicts

* **E-decoy (both envs): PASS for v2.5c.** The stratified RR identifier
  is the only one that rejects the linger decoy in both worlds, every
  seed, keeping the true foraging edges. The identifier question the
  owner asked is answered with matrices, not toys.
* **Honest negative:** identifier choice is behaviourally inert in both
  envs — the false edge never feeds a goal, so all arms act identically.
  Knowing the truth and acting on it are different questions; the
  second needs a world where the false edge is actionable (not built).
* **Honest negative:** treasures = 0 in every arm (the hardened gates
  closed the planner's path too); press→lever falls below the min_p
  noise floor at 16k for ALL arms (recorded as a boundary, C7 amended
  openly).
* **Baselines:** qlearn/ngram/random die 110–118×/16k in the stormy
  world; EMCA arms 6. The competence gap from the v2 matrix is preserved.

## Harness defects caught this turn (before they cost the matrix)

1. Two truncated matrix JSONs (provider died mid-run at 3000 steps) —
   detected by steps-field audit, deleted, re-run at full scale.
2. First v3 draft's trap was planner-invisible (fruits 50–62) — caught
   by toy check C3/C4, root-caused in the agent's goal machinery.
3. 6000-step lives dilute the trap below every identifier's threshold —
   caught while diagnosing C5; recalibrated to 16000 with measurement.
4. My analysis table first showed true_kept 1/3 — an aggregation bug in
   my own script (press->lever mixed into the foraging predicate);
   re-read per-seed from disk before reporting.

## Open threads (priority order)

1. **Actionable-false-edge env (v3.1 candidate):** give the false edge a
   cost the planner can take — e.g. bell_rang as an attractor goal — so
   believing the decoy changes behaviour. This is the only remaining way
   the identifier question can touch the acting question.
2. **Learning-progress confounder (turn 97 direction 3):** the same
   linger mechanism with a different trajectory generator (curiosity
   instead of hunger) — tests whether v2.5c's rejection is
   mechanism-specific or structural.
3. **Planner vs the hardened chain:** treasures 0/21 runs; either a
   smarter key→door sequencing or a relaxed window (measured, not
   guessed) would make the chain completable again.
4. press→lever below min_p at 16k: if rare-cause retention matters,
   the noise floor needs a data-driven definition (e.g. n-weighted),
   not a constant.

## Artifacts

* research/RESULTS_LINGER_V3.md — this turn's full report (both matrices).
* results/matrix_linger/*.json — 21 runs, simple env.
* results/matrix_v3/*.json — 21 runs, complex env.
* env_linger.py / env_terrarium_v3.py + verify + toy + driver stacks.
* agent_emca_v2.py — opportunistic tree-eating fix (documented inline).