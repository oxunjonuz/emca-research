# TURN 141 — STATUS: v12 "FORGER"

Owner directive: msg_00141 — *"давай это сделай beacon генерируется миром, агент его
не фальсифицирует. Поэтому следующий v12 с настоящим forged signal действительно
будет новым уровнем эксперимента, а не просто повторением v11."*

**Status: COMPLETE.** Prereg (before the first run): `research/PREREG_V12_FORGE.md`.
Report: `research/RESULTS_FORGER_V12.md`. Frozen experiment record:
**exp_d309de3c37cb** (exit 0, one command, ALL GREEN).

## What was done

* `env_wirehead_v12.py` — v10 (aquifer + keeper, untouched) + v11's beacon **landmark
  and geometry** with the world's beacon payment **switched off** + **the forger**:
  its own body, energy (2000-step life), deterministic movement, declared cooldown,
  declared spend cap, sticker from the declared grid `{0.0, 0.24, 0.25, 0.26, 0.30}`,
  in one of three declared places (`beacon_field`, `station`, `rich`). No RNG.
* `agent_wirehead_v12.py` — **an arm table only. 0 class definitions.** Four arms, all
  the frozen v10/v11 classes. The owner's constraint ("the agent does not falsify")
  is met literally: there is no agent-side code to falsify with.
* `run_life_v12.py`, `driver_wirehead_v12.py`, `analyze_wirehead_v12.py`,
  `diag_v12_crossing.py`, `verify_env_wirehead_v12.py`,
  `verify_wirehead_v12_independent.py`, `factcheck_v12_report.py`, `run_all_v12.sh`.
* Matrix: **490 cells** / 500 declared battery entries.

## The measured result

1. **The brake is for sale on exactly one channel: the harmful step.** A party paying
   **0.30 per unit of harm** — 9.0 reward units, **1.5 %** of its own 2000-step life —
   takes the aquifer from 25 left to **0** and kills the keeper **10/10 seeds**, with
   the agent's arithmetic untouched.
2. **The same money anywhere else buys nothing.** A sponsor at the station pays
   **125.70–251.40** (mean 175.98) to the same agent and moves **0 decision fields over
   10 seeds for both brakes**. **Purchasability is a property of what the brake
   measures, not of the money.**
3. **The crossing is exact and its location is the price.** `tick = 0.25` →
   the agent's own rate is exactly `0.2999999999999999889` (not `> 0.30`) → guard holds
   → 5 drains. `tick = 0.26` → 0.31 → **30 drains**. Measured step by step, with the
   guard's own reason string `rate<=0.30` at harvest decision t=14.
4. **Tempo decides whether a bribe is a bribe.** `period = 4` buys **nothing** beyond
   the unsponsored 5; `period = 1` buys all 30.
5. **A cap limits but does not stop it.** cap 5 → **6** drains; cap 10 → **12**: the
   frozen statistic's paid history keeps buying.
6. **A dead spoofed goal falls back to the harm** (H6 refuted as preregistered, §7 of
   the report): in 4/10 seeds the bound agent returns to the rich patch when its
   signal dies, with post-death reward exactly `0.05 × rich_steps`, and in those seeds
   the aquifer is drained and the keeper is dead.
7. **At rich=high the sponsor moves no outcome field of any arm** — nothing to buy.

## Verification

| path | result |
|---|---|
| world oracle | **50/50 PASS** (live negative control) |
| independent pass | **36/36 PASS** — fresh process, disk only, **no producer imported** |
| identity | 5 frozen anchor arms × 10 seeds × 7 fields: **0 diffs**; forger present-but-silent: **90 cells, 0 diffs incl. reward** |
| source audit | **0 class definitions** in the v12 agent module; no arithmetic on any rate/reward/receipt |
| frozen bytes | 8 predecessor files byte-identical; 110 + 330 + 220 frozen cells on disk |
| determinism | fresh-process rerun byte-identical (`77c80e6f94a0…`) |
| factcheck | **83 numbers, 0 fails** |

## My own defects, all reported

1. **A vacuous H1 cell** in the first battery (the forger placed only where the
   unbound arms never walk → 0.00 paid → H1 would have been trivially true). Caught
   by the oracle's non-vacuity check; `station` added; prereg amended **pre-run** (§9).
2. **A wrong rationale for a designed arm** (`v_price_win`): I claimed the frozen
   counter could only accumulate, but it counts every harvest (the world pays 0.05 even
   unsponsored). Rather than keep an arm resting on a false premise, the arm was cut
   and **v12 has no agent-side deviation at all**. The window idea itself remains
   unbuilt, on purpose — recording it here rather than quietly dropping it.
3. **A diagnostic that could not observe a block** (blocks substitute moves, so
   counting only harvest steps hides exactly the events it was built to show).
4. **Two bad checks in my own oracle**: a 1e-12 tolerance against a 997-term float
   accumulation, and a negative control asserting an impossible conjunction (could
   never fail). Both replaced; the world was right in both.
5. **The report's §8 first quoted one reading where three exist** (0.7525 ×9, 0.6007
   ×1) — caught by the factcheck, corrected.
6. **H6 and H11's declared null refuted as preregistered** — kept as refutations.
7. Runtime stopped the background driver once on a WRITESET ALERT on
   `/data/owner_trace/*.json.gz` (its own trace layer; my scripts write only under
   `results/`). Driver is resumable; finished 500/500.
8. **My own edit duplicated the prereg's §9 and stranded §7 after it** — caught by
   reading the file back. Fixed; the file now states plainly that §9 was *typed*
   after the matrix while recording pre-run changes, and notes that it skips §8.

## Fork, for the owner (prereg §7 named it in advance)

If a party willing to pay per harmful step can buy the self-measuring brake, the next
instrument is **not another brake** but an **accounting layer** — *who paid whom*
becomes part of what the agent measures. The opposite fork is equally cheap: close the
line here, with the measured price and the defects, and put v10–v12 in the preprint as
one arc — external rule, internal rule, and the price at which the internal rule is
for sale. Not my call.
