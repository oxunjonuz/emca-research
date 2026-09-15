# RESULTS V3.3 — SCARCITY, DYNAMIC COSTS, THE CHAIN FROM CURIOSITY

Owner directive (op_6181258f9eae), three tasks: (1) dynamic prices
for empty grasps and experiments under a hard energy deficit — the
stability test; (2) connect curiosity to the multi-step chain
(lever→key→door→treasure) WITHOUT a hard goal planner; (3) the
unified preprint table for v3.1+v3.2+v3.3. Full cycle in one turn:
env → independent verify (15/15) → toy BEFORE the matrix → matrix
11×3×16000 (33 runs, 0 failures) → independent disk-only analysis.

---

## 1. The world: TerrariumV33 (env_terrarium_v33.py)

TerrariumV32 kept whole (separated geometry, altar gray edge,
linger trap, chain gates). Three deltas, each priced:

* **Dynamic grasp cost.** The empty grasp costs 0.6 in calm, **1.8 in
  a storm** (3×). The competent grasp (tree at dist≤1) still pays
  +18 energy / +8 reward, capped at **60 fruits per storm** — then
  the tree is bare (`tree_bare` signal).
* **The altar demands an offering.** Every `wait` at the altar burns
  1.0 energy. The gray-zone true edge (wait→patch_berry, P=0.28 vs
  base 0.15) is unchanged — the experiment now costs energy per
  trial, not just time.
* **Hard deficit.** Berries 2 (warm) / 1 (cold, was 3/2); storm fury
  −3.0 (was −2.4); tree fruit 18 (was 25).

verify_env_v33.py: **15/15 PASS** — the do-oracle P(ring|do(a)) is
equal for all actions (spread 0.014), the altar RR is 1.88, brute
force finds 0 treasures in 5×6000, and a scripted competent forager
survives the deficit (1–2 deaths/16k): the world is harsh but not
unsurvivable.

## 2. Toy BEFORE the matrix — 6 PASS, 2 honest FAIL-as-prediction

W1 deficit survivable (v2.5c deaths 21–23 at 8k) · W3 identifier
stable (decoy 3/3 in v2.1, 0/3 in v2.5c, true edges 3/3) · W4 prober
survives the offering and reaches CAUSAL 3/3 · W6 chain arm functions
(levers 4229–5679, keys 93–179, treasures 9/5/10 at 8000 steps!) ·
W7 pure novelty dies (48–49 vs 19–29) · W8 determinism.

**W2 FAIL as a prediction:** I predicted the dynamic grasp cost would
tip the believer below the rejector. It did not at 8000 steps — the
believer's grasps are mostly COMPETENT (at the tree: 20 fruits/tree
vs the rejector's 12.4 — the key goal pulls the rejector away from
harvests). **W5 FAIL partially:** curious_surv kept the reward edge
in 2/3 seeds but its deaths rose to 29 in seed 1. Both failures were
diagnosed by tracing, not patched away: the matrix criteria were
rewritten neutrally (measure, don't wish).

## 3. The matrix (11 arms × 3 seeds × 16000, 33 runs, 0 failures)

| condition | reward | deaths | fruits | treasures | decoy | altar |
|---|---|---|---|---|---|---|
| emca_v21 (believes) | 15387 | 47.0 | 1475 | 0 | 3/3 | 0/3 |
| emca_v22 (believes) | 15387 | 47.0 | 1475 | 0 | 3/3 | 0/3 |
| emca_v25c (rejects) | 15516 | 43.0 | 1526 | 0 | 0/3 | 0/3 |
| emca_nocausal | 15820 | 45.0 | 1521 | 0 | 3/3 | 0/3 |
| prober | 14979 | 39.0 | 1424 | 0.7 | 0/3 | 3/3 |
| curious_pure | −390 | 98.7 | 0.3 | 0 | 0/3 | 0/3 |
| curious_surv | 12058 | 59.0 | 1192 | 0 | 0/3 | 0/3 |
| **curious_chain** | 11329 | 61.3 | 1281 | **16.0** | 0/3 | 0/3 |
| random / qlearn / ngram | −209 / 292 / 535 | 96–98 | 16–92 | 0 | – | – |

Determinism: fresh subprocess re-runs bit-identical (v2.1, v2.5c,
curious_chain). Steps-audit clean.

### T1 — scarcity bites (task 1): PASS
v2.5c deaths 40–47 (v3.2: 22); fruits 1526 (v3.2: 2508). The deficit
is real and survivable: every planner arm lives; every baseline dies
96–98 times.

### T2 — the price of the false belief (task 1): the sign is now seed-noisy, the mechanism is measured
Per-seed (rejector − believer): **+1352, +2615, −3580**. The mean
gap is +129 — under scarcity the believer's edge has vanished on
average, but seed 3 still pays it. The decomposition criterion PASSES:
the gap is attributable to the fruit-harvest channel (fruit gap × 8 ≈
reward gap), NOT to the grasp costs (the believer's wasted grasps:
35/life, ~40 energy — noise). **The honest reading: the dynamic grasp
cost did NOT become the price of the false belief, because the
believer's grasps are competent — the false edge parks it at the tree
zone where grasping feeds it. The belief's price under scarcity is
carried by the harvest-time channel, and it shrank to seed noise.**

### T3 — the prober under the offering (task 1): PASS 3/3 CAUSAL
The prober reaches CAUSAL on the altar edge in **3/3 seeds** (the
v3.2 power limit is gone: the scarcity gates concentrate its life at
the altar, giving the probe more effective trials — target 30–36/180
vs ctrl 12–19/180, all p<0.05). It pays for the data: 227 offerings
burned, 168 empty grasps, reward 14979 vs 15516 — **experimentation
now costs ~3.5% of reward, down from ~33%** (the offering replaced
the opportunity cost: the probe no longer walks away from foraging).
Deaths 33–44 — the offering did not kill it.

### T4 — the chain from curiosity (task 2): PASS with the honest boundary
**curious_chain completes 13–18 treasures per life — every other arm
in the whole campaign completes 0–2.** The object-directed novelty
(rarity pull per interaction + the treasure-scent dash when key+door
align) solves the multi-step quest with NO goal machinery: no goals,
no deadlines, no planner. The mechanism is measurable: 8951–10737
lever presses and 218–287 key pickups per life (roaming produces the
encounters); the dash converts the aligned windows.
The honest boundary: **the chain costs lives** — 56–69 deaths vs
43–47 for the planner arms. The object-novelty layer itself is
death-neutral (chain ≈ curious_surv + 2.3 deaths; T4c' PASS) — the
deaths are the price of the curiosity POLICY under scarcity (roaming
keeps the agent away from the storm tree; all 185 curious-arm deaths
are storm+tree-present). My pre-registered T4c guess (≤40 deaths)
FAILED; the replacement criterion (the layer is death-neutral vs the
same policy without it) PASSES. Reported both, no smoothing.

### T5/T6 — controls: PASS
Decoy in v2.1 3/3, never in v2.5c; true edges 3/3; baselines die
96–98 vs 39–61 for every planner/curious arm.

## 4. A harness defect caught by the matrix death-trace (before the final matrix)

The first matrix run showed v2.5c deaths 45–49 with ALL deaths
storm+tree-present. The trace showed the agent circling a fruiting
tree at dist 1–2 WITHOUT grasping, dying at energy 0. Root cause:
**the storm tree spawn does not emit `tree_appeared`** (only calm
rare trees do), so after the first storm hit its 60-fruit cap, the
agent's `tree_bare` flag stayed True forever — it refused to grasp
any later storm tree and starved beside food (36% of storm steps
lived with a stuck flag). Fixed (the flag resets when a tree is
visible again), the matrix re-run from scratch: v2.5c deaths 43,
fruits 1526. The first run's JSONs were deleted, not averaged in.

## 5. The preprint table (task 3)

`research/PREPRINT_TABLE.md` + `.csv` — all three worlds, all arms,
means over 3 seeds, read from disk by a fresh process. The headline
cross-world contrasts:

| contrast | v3.1 | v3.2 | v3.3 |
|---|---|---|---|
| rejector − believer (reward) | −722 | −191 | **+129** |
| best arm | emca_v21 (believer) | curious_surv (+82%) | emca_nocausal |
| curious_surv deaths | – | 1 | 59 |
| chain treasures | – | – | 16 |
| v2.5c fruits | 1467 | 2508 | 1526 |

The campaign's arc in one line each: **v3.1** — the false belief PAYS
(+722) because the world put the decoy's attractor on food; **v3.2**
— separating the geometry inverts the sign (−191) and curiosity with
a survival arbiter dominates everything; **v3.3** — scarcity erases
the believer's edge to seed noise, the prober's experiments become
cheap (3.5% of reward) and 3/3 decisive, and object-directed novelty
solves the chain that no goal arm solves — at the measurable price of
lives.

## 6. Files and provenance

* env_terrarium_v33.py, verify_env_v33.py (15/15 PASS, re-run
  confirmed).
* agent_emca_v33.py — V33Mixin (scarcity gates: chime≥60, altar≥40,
  bare-tree with the spawn-signal fix), AgentV33* identifier arms
  (lineage untouched), AgentV33Prober, AgentCuriousChain /
  SurvivorV33 / PureV33.
* run_life_v33.py, driver_v33.py (pre-registered T1–T6),
  toy_v33_check.py (W1–W8), analyze_v33.py (independent, disk-only).
* results/matrix_v33/*.json — 33 runs;
  results/matrix_v33_analysis.txt — the analysis output.
* research/PREPRINT_TABLE.md / .csv — the campaign table.
