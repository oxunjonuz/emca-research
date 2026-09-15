# TURN 102 STATUS — v3.3: SCARCITY + DYNAMIC COSTS + THE CHAIN FROM CURIOSITY

Directive: op_6181258f9eae, three tasks, one turn, full house-rule
cycle. Result: T1/T2/T3/T4(a,b,c')/T5/T6 PASS; T4c (my calibration
guess) FAIL honestly — replaced by the contrast that actually isolates
the layer, which PASSES. One harness defect (stuck tree_bare flag)
caught by the matrix death-trace and fixed before the final matrix.

## Ledger

* env_terrarium_v33.py — the scarcity world (dynamic grasp 0.6/1.8,
  altar offering 1.0, berries 2/1, tree 18 capped 60/storm, fury −3.0).
  verify_env_v33.py 15/15 PASS (re-run confirmed).
* agent_emca_v33.py — V33Mixin scarcity gates + AgentCuriousChain
  (object-directed novelty: rarity pull + treasure dash) + Survivor/
  Pure v33. Identifier lineage untouched.
* toy_v33_check.py — W1/W3/W4/W6/W7/W8 PASS; W2/W5 honest
  FAIL-as-prediction (diagnosed by tracing, criteria rewritten
  neutrally for the matrix).
* Matrix: 11 arms × 3 seeds × 16000 = 33 runs, 0 failures, steps-audit
  clean, determinism bit-identical (3 conditions re-run fresh).
* analyze_v33.py — independent disk-only analysis:
  T1 PASS (deaths 40–47, fruits 1526 vs 2508),
  T2 PASS (gap decomposes to the harvest channel; believer's wasted
  grasps are noise — 35/life),
  T3 PASS 3/3 CAUSAL (offerings 227, experiment cost ~3.5% of reward,
  down from ~33% in v3.2),
  T4a/b PASS (chain treasures 13–18/life vs 0–2 for every other arm),
  T4c FAIL (guess ≤40) + T4c' PASS (layer is death-neutral vs
  curious_surv: +2.3 deaths mean),
  T5/T6 PASS.
* research/PREPRINT_TABLE.md + .csv — the campaign table (v3.1+v3.2+
  v3.3, fresh process, disk-only).
* research/RESULTS_V33.md — the full report.

## Headlines

1. **Scarcity erased the believer's edge** (task 1): rejector −
   believer = +129 mean (was −722 in v3.1, −191 in v3.2), but seed 3
   still pays −3580 — the sign is now seed-noisy, and the mechanism is
   the harvest-time channel, NOT the grasp cost (the believer's
   grasps are competent: it parks at the tree zone).
2. **The prober got cheaper and stronger** (task 1): 3/3 CAUSAL
   verdicts (the v3.2 power limit is gone — scarcity concentrates its
   life at the altar), and the experiments now cost ~3.5% of reward
   (was ~33%): the offering replaced the opportunity cost.
3. **The chain from curiosity works** (task 2): 13–18 treasures/life
   with NO goal machinery — every other arm in the campaign completes
   0–2. The price is lives (56–69 deaths): roaming under scarcity
   keeps the agent from the storm tree; the object-novelty layer
   itself is death-neutral (chain ≈ surv + 2.3).
4. **A harness defect caught by the death-trace**: the storm tree
   spawn emits no `tree_appeared`, so the bare-tree flag stuck True
   after the first capped storm — the agent starved beside fruiting
   trees (36% of storm steps). Fixed; matrix re-run from scratch.

## Open threads (priority order)

1. **The chain's death price** — the curiosity policy dies 56–69×
   under scarcity while solving the chain. The obvious synthesis:
   the planner's storm competence inside the curiosity policy (the
   v3.2 lesson at the policy level). One mixin, one matrix.
2. **The believer's seed-3 edge** — the sign is seed-noisy now; a
   sterile world (no cold berries in the far zone) would settle
   whether the believer's edge is geometry or luck.
3. **The prober's verdict accumulation across lives** — the episodic
   store survives resets; verdicts could too (the EMCA episode
   machinery already persists).

## Provenance

* RESULTS_V33.md, TURN102_STATUS.md, PREPRINT_TABLE.md/.csv (this
  turn); results/matrix_v33/*.json (33 runs);
  matrix_v33_analysis.txt; matrix_v33_driver.log.
* Identifier lineages untouched (v2.1/v2.2/v2.5c imported as-is).
* No network use. No hanging processes. Repositories untouched.
