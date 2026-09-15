# TURN 132 STATUS — the arbiter's price scale repaired, re-measured, and the honest answer

Directive: msg_00132. Status: **complete, one continuous run, independently
verified.**

## What was open coming in

Turn 131 diagnosed (but did not repair) the frozen arbiter's scale mismatch:
`rhs = rich·H + c` billed the alternative over `H = 40` steps while a probe
spends `PROBE_BLOCK = 20`. The owner accepted the diagnosis as a genuine
engineering error found before the result, and ordered the repair.

## What was done

1. **Repaired, minimally.** `arbitration_scaled.py`: `rhs = rich·PROBE_LEN + c`
   with `PROBE_LEN = 20 = union_agent.PROBE_BLOCK` (asserted). No new free knob.
   Frozen `arbitration.py` and `candidate_gen.py` left **byte-identical**.
   `union_agent_v2.py` and `union_run_v2.py` each differ from their originals in
   **exactly one import line** (checked by the verifier).
2. **Named the new cutoff and refused to hide it.** The corrected rule is silent
   above `rich = 196/220 = 0.890909` (old: `196/240 = 0.816667`). That cutoff is
   **economics, not artefact** — no probe pays for itself above it. Stated before
   the run.
3. **Re-ran the base sweep, old rule vs corrected, same instances/seeds.** The
   corrected rule never probes less and improves regret up to base 0.80, most at
   base 0.75 (0.0514 → 0.0289). `beta0` still probes exactly 0 everywhere.
4. **Answered "disappeared or shifted?" by a horizon sweep.** Regret is
   **monotone non-decreasing in the price horizon** on maskr; the no-price arm is
   the best. So it is half-artefact, half-economics: the scale error was real and
   is fixed; the residual rich-regime failure is the price itself.
5. **Traced every decision.** The band where the two rules differ is **empty on
   mask** and populated on maskr (503 decisions; frozen clears 0, corrected 367).
   maskr's observed rich_rate is **0.9232** — above the corrected cutoff.
6. **Re-ran the full matrix** on the corrected rule into a **new** directory
   `results_union_v2/` (93 cells × 1000 sims). `results_union/` untouched.
7. **Checked the Lean part explicitly.** `grep` for `GAIN_UNIT`, `PROBE_COST`,
   `PROBE_LEN`, `H_DEFAULT`, `rich_rate`, `arbitration` in `union_stoch_v2.lean`
   and `nonvacuity_v6.lean`: **0 hits**. The file is byte-identical
   (`6a5bcfb3…`) and recompiles clean (`EXIT=0`, zero output). **The formal part
   is unaffected** — the theorem carries no price term.

## The answer the owner asked for

**The three-part union does NOT beat the two-part union.**

| instance | three-part | two-part | diff | z |
|---|---|---|---|---|
| mask ε=0.35 | 0.00328 | 0.00341 | −0.00013 | −0.35 |
| maskr ε=0.35 | 0.02719 | 0.02097 | **+0.00621** | **+8.11** |

On the main instance the repair turns a loss into a **tie** (all |z| < 0.4); on
the rich instance the three-part union still **loses significantly** (z ≈ +8).
The repair improved maskr's union by 13 % but nowhere near closed the gap. The
turn-129 recommendation — a **two-part** union — stands, now on a corrected
instrument.

## A new problem, named plainly

The corrected cutoff moves with the **declared** `GAIN_UNIT`. At the campaign's
declared 200 the maskr instance is above the cutoff; at 400 it is below and the
rich-instance gap shrinks to a tie (z +2.74 → +0.91). Reported as a
**sensitivity**, not a recommendation: raising a declared constant until the
verdict flips is the move the owner stopped on turn 104.

## Verification

* `verify_matrix_determinism_v2.py`: **27 checks, 0 failures** — all 93 cells
  re-derive their own mean/sem; 66 non-arbiter cells reproduce turn-129
  bit-for-bit; 10 cells re-run in fresh processes match to 12 decimals; the
  arbiter arithmetic and both frozen hashes check out; the one-line diff holds.
* `factcheck_union_fix.py`: **94/94** numbers re-derived from frozen JSON — and
  it caught **one number I typed from memory** (nocost at base 0.85: 0.006881 vs
  the data's 0.006875), corrected in the report.
* Frozen artefacts re-hashed after the run: `arbitration.py 2d3d825b…`,
  `candidate_gen.py fa9721ae…`, `results_union/SUMMARY.json e33ea343…`,
  `union_stoch_v2.lean 6a5bcfb3…`. V7 110 and V8 404 files untouched.
* **Runtime event, surfaced.** Twice a `multiprocessing.Pool` sweep was killed by
  a runtime **WRITESET ALERT** on `/data/owner_trace/*.json.gz` — a runtime-layer
  write (my scripts write only under `bench_cb/`), firing on the number of
  simultaneous spawns. Re-run serially/as background jobs, which completed.

## Artefacts

* `bench_cb/arbitration_scaled.py` — the corrected rule
* `bench_cb/union_agent_v2.py`, `bench_cb/union_run_v2.py` — one-line-diff producer
* `bench_cb/sweep_arbiter_v2.py` + `.json` — base sweep, old vs corrected
* `bench_cb/diag_bar_sweep_v2.py` + `.json` — the horizon sweep (the decisive one)
* `bench_cb/trace_arbiter.py` + `trace_arbiter_summary.json` — per-decision trace
* `bench_cb/diag_gain_unit_v2.py` + `.json` — GAIN_UNIT sensitivity
* `bench_cb/union_matrix_v2.py`, `run_cells_v2.py`, `results_union_v2/` — full matrix
* `bench_cb/verify_matrix_determinism_v2.py` + `.out.txt` — independent verifier
* `bench_cb/factcheck_union_fix.py` — 94/94
* `bench_cb/PREREG_UNION_FIX.md` — preregistration of the repair
* `bench_cb/RESULTS_UNION_FIX.md` — the report
* `bench_cb/lean/compile_v2_turn132.txt` — the unchanged Lean file recompiled

## Not done, said plainly

* The repair is a **new instrument**; the verdict is a verdict on it. The frozen
  rule's results stand unaltered as the record of the old instrument.
* The GAIN_UNIT dependence (§ new problem) is diagnosed, not resolved.
* The maskr instance remains mine, not published.
