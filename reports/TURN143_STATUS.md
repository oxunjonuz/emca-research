# TURN 143/144 STATUS — v13 "LEDGER"

Owner directive (msg_00143, restated in msg_00144): **fork (A) — continue the
research, add accounting: "who paid whom".** Turn 143 was interrupted by three
consecutive provider 502s, not by anything in the work. Owner then raised the retry
count from 3 to 10. This turn resumed from the saved state and finished the line.

## State at resume
* `PREREG_LEDGER_V13.md` (written before the first cell), `env_ledger_v13.py`,
  `agent_ledger_v13.py`, `run_life_v13.py`, `driver_ledger_v13.py`,
  `verify_env_ledger_v13.py` all existed.
* The matrix was already **complete** on disk: driver log `DONE 280 / 280`;
  260 unique cell files (the battery list has 10 duplicate filenames by
  construction — the tick-0.30 BRIBE13 cell and the tick-0.30 CROSSING13 cell are
  the same cell).
* World oracle already on disk: **58 checks, 0 fails**.
* Missing: analysis, independent pass, factcheck, report, freeze. All done this turn.

## What was produced this turn
| file | role |
|---|---|
| `analyze_ledger_v13.py` → `results/analyze_ledger_v13.json` | H1–H10 from raw cells |
| `verify_ledger_v13_independent.py` → `results/verify_ledger_v13_independent.txt` | independent pass, 45 checks, 0 fails |
| `factcheck_ledger_v13.py` → `results/factcheck_ledger_v13.txt` | 26 numbers re-read from disk, 0 fails |
| `diag_ledger_lag_v13.py` → `results/diag_ledger_lag_v13.txt` | independent re-measure of the drain-lag claim |
| `run_all_v13.sh` | the whole line in one resumable command |
| `research/RESULTS_LEDGER_V13.md` | the report |
| `research/PREREG_LEDGER_V13.md` §9 | amendment: pre-run world changes + the post-run check correction |

## Verdicts (all ten preregistered hypotheses hold)
* **H1** the ledger arm holds 25 left / 5 drains / keeper alive 10/10, while the
  same sponsor buys the scalar arm completely (0 / 30 / dead 10/10, 9.0 reward units).
* **H1b** the ledger arm under the bribe reproduces the frozen v10 `s4_internalized`
  cell on every decision field, 10/10, 0 differences (reward is excluded by the
  prereg — the money is still paid, just not counted: 241.75 vs 240.25).
* **H2** with the world itself paying 0.35 (no third party) the ledger drains
  everything, identical to the scalar arm — accounting, not blanket refusal.
* **H3** the scalar statistic is the *same double* (0.35) in the bribed and honest
  worlds; the ledger's differs (0.05 vs 0.35). The tag carries the whole difference.
* **H4** both tag-free arms drain everything; the first non-draining rich receipt
  arrives at step **39**, the first guard decision at step **14**, in 10/10 seeds —
  the calibration signal is produced only by the harm.
* **H5** under a **lying tag** the ledger arm is bought completely (0 / dead 10/10),
  with the same money on the same steps. The agent sees `foreign == 0` while the
  forger paid 30 times.
* **H6** at `rich=high` the ledger drains everything; the forger moves no field.
* **H7** a sponsor at the station pays 125.70–251.40 and moves no decision field.
* **H8** identity across three worlds, 0 field differences; a tick-0.0 forger moves
  nothing.
* **H9** the ledger is flat at 25 for every tick; the scalar crossing .25→.26 is
  re-measured in the same battery.

## Fork for the owner (prereg §7, third ending reached)
H1 holds **and** H5 holds together: **the accounting layer is worth exactly the
trustworthiness of its provenance channel.** (A1) attested provenance (auditor /
unforgeable receipt) — strictly stronger, **not built**; (A2) close the line here.

## Integrity
* One command, `run_all_v13.sh`, exit 0, **ALL GREEN**; frozen as `exp_` (see
  summary).
* Eleven predecessor files byte-identical; four frozen matrices intact
  (110 + 330 + 220 + 490 cells).
* Determinism: fresh-process rerun byte-identical (sha `7fcb169bd7c8…` on
  `l_ledger_3_…`).
* The source-comment edit to `agent_ledger_v13.py` this turn is **comment-only**:
  the same cell re-runs byte-identical after it.

## Own defects this turn
1. The independent pass's partition check was asserted over all 260 cells and 40
   out-of-scope cells refuted it; scope now declared (200 in, 60 skipped).
2. A negative control (NC5) contained `or True` — a check that cannot fail;
   replaced with a measured control, and NC6 added.
3. `analyze_ledger_v13.py` confused the world-richness axis with `place` — caught
   by a `KeyError`.
4. A turn-143 source comment claimed "6 of 36 … exactly the wrong six";
   re-measured: the two rules disagree on **exactly one** step. Corrected in source
   and in the report, with evidence on disk.
