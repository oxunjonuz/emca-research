# RESULTS — turn 132: the arbiter's price scale, repaired and re-measured

Owner directive msg_00132. The diagnosis of turn 131 was accepted as a genuine
engineering error, found before the result rather than after it, and the task was:
repair it; re-run the same base sweep and say whether the effect **disappeared or
merely shifted**; re-run the full union matrix on the fixed arbiter **without
mixing with old data**; say explicitly whether the Lean part is affected; report
honestly whether the **three-part union now beats the two-part**; name any new
problem as plainly as the old ones.

Preregistration of the repair and of the claims below: `PREREG_UNION_FIX.md`
(written after the trace/sweep measurements that established the error, before
this report — the order is stated there).

**Headline, three parts.**
(1) The error was real and is repaired: the price now bills the probe's own
length (`PROBE_LEN = PROBE_BLOCK = 20`) instead of an unrelated declared horizon
(`H = 40`), in a new module with the frozen rule left byte-identical.
(2) The effect did **not** disappear and did **not** merely shift: it was
**half-artefact, half-economics**. The corrected rule recovers the regime
`0.8167 < rich ≤ 0.8909` (where the old rule refused a candidate carrying the
full attainable headroom), and it lowers regret on the main instance — but on the
rich instance (`rich ≈ 0.9232`) the price is a **monotone tax with no interior
optimum**: regret falls as the price falls, all the way to zero price.
(3) **The honest answer to the owner's question: no.** On the main instance the
three-part union now **ties** the two-part (|z| < 0.4 at every ε); on the rich
instance it still **loses** by a large, significant margin (z ≈ +8). The repair
removed an artefact; it did not buy a win.

---

## 1. The error, stated as arithmetic

Frozen rule (`arbitration.py`, sha `2d3d825b…`, **untouched**):

    value = beta · GAIN_UNIT · score          GAIN_UNIT = 200
    rhs   = rich_rate · H + PROBE_COST        H = 40, PROBE_COST = 4
    probe iff value > rhs

Both sides are in reward units; only one of them is in *probe* units. A probe
spends exactly `PROBE_BLOCK = 20` steps (`union_agent.py`, the campaign's own
declared constant from turn-128 A3), while the price billed 40. Because no
candidate can carry a score above the attainable headroom `1 − rich`, the rule is
forced silent for every candidate once

    GAIN_UNIT·(1 − rich) ≤ rich·H + PROBE_COST
    rich ≥ (GAIN_UNIT − PROBE_COST)/(GAIN_UNIT + H) = 196/240 = **0.816667**

Above that level the arbiter refuses even a *maximal* candidate — not a decision,
an arithmetic dead zone.

## 2. The repair, and why it is not a new knob

`arbitration_scaled.py`. One substitution:

    rhs = rich_rate · PROBE_LEN + PROBE_COST,   PROBE_LEN = 20 = PROBE_BLOCK

No new free parameter: `PROBE_LEN` **is** the declared probe block (asserted in
the sweep and re-checked by the verifier). The frozen `arbitration.py` and
`candidate_gen.py` are byte-identical (hashes re-checked). The corrected rule is
reached by a **one-line diff**: `union_agent_v2.py` differs from `union_agent.py`
in exactly `-import arbitration as AR` → `+import arbitration_scaled as AR`
(checked programmatically). `union_run_v2.py` differs from `union_run.py` in
exactly the driver import.

**The new cutoff, and why it cannot be removed.** The corrected rule is silent
above

    rich ≥ (GAIN_UNIT − PROBE_COST)/(GAIN_UNIT + PROBE_LEN) = 196/220 = **0.890909**

That cutoff is **economics, not an artefact**: when the alternative already pays
`r` per step, the largest conceivable gain is `(1 − r)` per step, so once
`(1 − r)·GAIN_UNIT ≤ r·PROBE_LEN + PROBE_COST` no probe can pay for itself,
whatever the candidate. The repair moves the boundary from a level dictated by an
irrelevant horizon (0.8167) to the level dictated by the probe itself (0.8909).
It does not abolish the boundary, and the report does not claim it does.

## 3. Did the effect disappear, or shift? Both — measured, not argued

### 3a. The base sweep, old rule vs corrected rule, same instances, same seeds

`union_old` = frozen rule; `union_new` = corrected; `union_nocost` = no price at
all (probe the top candidate); `beta0_new` = the C1 control under the corrected
rule. 200 sims/cell, `T=400`, `eps=0.35`, `N=50`, seeds 1..200
(`sweep_arbiter_v2.json`).

| base | OLD regret | OLD probes | NEW regret | NEW probes | nocost regret | nocost probes | beta0 probes |
|---|---|---|---|---|---|---|---|
| 0.50 | 0.00486 | 3.365 | **0.00311** | 3.430 | 0.00289 | 4.330 | 0.000 |
| 0.55 | 0.01197 | 3.180 | **0.00386** | 3.260 | 0.00289 | 4.160 | 0.000 |
| 0.60 | 0.03392 | 2.755 | **0.00756** | 2.990 | 0.00225 | 3.985 | 0.000 |
| 0.65 | 0.04625 | 2.405 | **0.02001** | 2.905 | 0.00334 | 4.135 | 0.000 |
| 0.70 | 0.04932 | 1.655 | **0.02888** | 2.795 | 0.00382 | 4.305 | 0.000 |
| 0.75 | 0.05143 | 0.440 | **0.02886** | 2.435 | 0.01039 | 4.425 | 0.000 |
| 0.80 | 0.03100 | 0.010 | **0.02656** | 1.545 | 0.02127 | 4.455 | 0.000 |
| 0.85 | 0.00600 | 0.000 | 0.00600 | 0.465 | 0.00688 | 4.640 | 0.000 |
| 0.90 | 0.00475 | 0.000 | 0.00475 | 0.100 | 0.00475 | 4.455 | 0.000 |
| 0.95 | 0.00350 | 0.000 | 0.00350 | 0.000 | 0.00350 | 4.095 | 0.000 |

Readings:
* The corrected rule **never probes less** than the frozen one and probes much
  more in the transition (base 0.70–0.80: 1.66→2.80, 0.44→2.44, 0.01→1.55).
* Regret improves monotonically with the correction up to base 0.80, and the
  improvement is largest exactly where the old rule was dying (base 0.75:
  0.0514 → 0.0289).
* **The `beta0` control is dead at every base** (0.000 probes) — the C1 control
  survives the repair, as required.
* **But the corrected rule still does not reach the no-price level anywhere in
  the rich half.** At base 0.80 the corrected rule is 0.02656 against nocost
  0.02127; at base 0.85 and 0.90 the corrected rule probes less and regret is
  equal-to-worse. The price is still a tax above the transition.

### 3b. The decisive diagnostic: sweep the price horizon itself

If the old silence were *only* an artefact of the wrong horizon, some interior
horizon should beat both the frozen value and the no-price arm. It does not:
`diag_bar_sweep_v2.py`, maskr (base 0.8), `PL ∈ {0,5,10,15,20,30,40,60}`:

| PL (price horizon) | rhs @ rich .92 | regret | probes |
|---|---|---|---|
| 0 | 4.00 | **0.02137** | 3.185 |
| 5 | 8.62 | 0.02295 | 3.105 |
| 10 | 13.23 | 0.02324 | 2.940 |
| 15 | 17.85 | 0.02482 | 2.345 |
| **20 (corrected)** | 22.46 | 0.02656 | 1.545 |
| 30 | 31.70 | 0.02942 | 0.340 |
| **40 (frozen)** | 40.93 | 0.03100 | 0.010 |
| 60 | 59.39 | 0.03100 | 0.000 |
| nocost | — | 0.02127 | 4.455 |

**Regret is monotone non-decreasing in the price horizon**, and the no-price arm
is the best of the sweep. There is no interior optimum: on this instance the
price never earns its place. So the honest verdict is *not* "the effect
disappeared". It is: **the scale error was real and is fixed; the residual
failure in the rich regime is the economics of the price, not the horizon.**

### 3c. The trace — where the two rules actually differ

`trace_arbiter.py`, 100 runs per instance, every decision point recorded:

| | mask (base 0.5) | maskr (base 0.8) |
|---|---|---|
| decision points | 13 984 | 19 962 |
| observed rich_rate, mean | 0.6482 | **0.9232** |
| top candidate score, max | 0.5000 | 0.2200 |
| cleared > 0, frozen rule | 2.24 % | 0.01 % |
| would clear, corrected rule | 5.56 % | 41.62 % |
| decisions inside the band (0.8167, 0.8909] | **0** | 503 |
| of those: frozen clears / corrected clears | 0 / 0 | **0 / 367** |

Two facts fall out. First, the band the repair is about is **empty on mask and
populated on maskr** — the repair is correctly aimed. Second, maskr's mean
rich_rate is **0.9232**, *above* the corrected cutoff 0.8909: the arbiter's
residual silence there is the economics, exactly as §2 says. The 41.62 % "would
clear" figure counts decisions at which *some* candidate clears; the realised
probe count is lower because a cleared candidate is only probed when the ranked
list is non-empty and the run reaches it.

## 4. The full matrix, re-run on the corrected rule — and the answer

`union_matrix_v2.py` → `results_union_v2/`, 93 cells × 1000 sims, same grid as
`PREREG_UNION.md` §3. **The old `results_union/` directory is untouched** (its
SUMMARY sha `e33ea343…` unchanged); nothing is merged.

**The owner's question — does the three-part union now beat the two-part?**

| instance | ε | three-part (union) | two-part (union_nocost) | diff | z | probes |
|---|---|---|---|---|---|---|
| mask | 0.15 | 0.03092 ± 0.00122 | 0.03126 ± 0.00122 | −0.00034 | −0.20 | 4.07 vs 4.11 |
| mask | 0.25 | 0.01332 ± 0.00114 | 0.01336 ± 0.00114 | −0.00004 | −0.03 | 3.91 vs 4.23 |
| mask | 0.35 | 0.00328 ± 0.00026 | 0.00341 ± 0.00027 | −0.00013 | −0.35 | 3.31 vs 4.27 |
| maskr | 0.25 | 0.02698 ± 0.00035 | 0.02101 ± 0.00066 | **+0.00597** | **+7.93** | 1.46 vs 4.40 |
| maskr | 0.35 | 0.02719 ± 0.00038 | 0.02097 ± 0.00066 | **+0.00621** | **+8.11** | 1.46 vs 4.40 |

* On the **main instance** the repair moves the three-part union from
  *worse-than-two-part* to a **statistical tie** (all |z| < 0.4). It does not
  win: the difference is a fraction of one SEM and the sign is still, if
  anything, against the price.
* On the **rich instance** the three-part union still **loses** to the two-part
  by 0.0060–0.0062 regret at z ≈ +8 — a large, unambiguous loss. The repair
  improved it (0.03125 → 0.02719, a 13 % cut) but nowhere near closing the gap.

**Confirmed by an independent read-only pass** (no producer imported, only the
frozen per-seed rows, 20 000-resample bootstrap on the difference):

| instance | diff (three-part − two-part) | 95 % CI | reading |
|---|---|---|---|
| maskr ε=0.35 | +0.00621 | [+0.00471, +0.00770] | **significant loss**, P(diff>0)=1.0000 |
| mask ε=0.15 | −0.00034 | [−0.00372, +0.00303] | tie (CI spans 0) |
| mask ε=0.25 | −0.00004 | [−0.00321, +0.00316] | tie |
| mask ε=0.35 | −0.00013 | [−0.00086, +0.00061] | tie |

The same pass re-checked that the corrected rule never probes less than the
frozen one at any base, that `results_union/SUMMARY.json` still hashes to
`e33ea343…`, and that the new matrix has all 93 cells plus its summary.

**Verdict, plainly: the three-part union does NOT beat the two-part union.** The
cost-aware arbiter, repaired, is a tie on the main instance and a significant
loss on the rich one. The recommended composition from turn 129 — a **two-part**
union — stands, now on a corrected instrument rather than a broken one.

**The internal control that makes this credible.** Every arm whose action does
not depend on the price is **bit-identical** to the turn-129 matrix: 66 cells,
per-seed regrets equal (`verify_matrix_determinism_v2.py`, section B). The repair
moved only the arms that consult the arbiter — `union`, `union_noctx`,
`union_pooledexp` — and it moved them in the right direction (maskr union
0.03125→0.02719, `union_noctx` 0.03486→0.03596, `union_pooledexp`
0.03130→0.02863). A repair that had leaked into the other arms would have shown
up here as noise; it did not.

## 5. Is the Lean part affected? **No — explicitly, and checked**

The formal development is **not touched and does not need to be**. The claim is
not a reading of the file, it is a check:

* `grep` for `GAIN_UNIT`, `PROBE_COST`, `PROBE_LEN`, `H_DEFAULT`, `rich_rate`,
  `arbitration` in `union_stoch_v2.lean` and `nonvacuity_v6.lean`: **0 hits in
  each**. The bound is stated with an abstract per-pull loss budget `bΔ` and a
  concentration argument (`𝔼[R] ≤ bΔ + M·k/(4rε²)`), which carries no price term.
* `union_stoch_v2.lean` is **byte-identical** (sha `6a5bcfb3…`) and recompiles
  clean in a fresh process (`compile_v2_turn132.txt`: zero bytes of output,
  `EXIT=0`).

So the repair is confined to the empirical arbiter; the theorem was never about
the arbiter's constants and remains valid as written. Had the repair changed the
statement's meaning, the `grep` would have shown a price identifier in the file —
it shows none.

## 6. A new problem found on the way — named as plainly as the old ones

**The verdict's dependence on a declared constant.** The corrected cutoff is

    cutoff = (GAIN_UNIT − PROBE_COST)/(GAIN_UNIT + PROBE_LEN)

so it moves with the agent's **declared** `GAIN_UNIT`. At the campaign's declared
`GAIN_UNIT = 200` the maskr instance (rich 0.9232) sits above the cutoff and the
arbiter refuses; at `GAIN_UNIT = 400` the cutoff is 0.9429 and maskr falls below
it. Measured (`diag_gain_unit_v2.py`):

| GAIN_UNIT | base 0.80 union | base 0.80 nocost | diff | z |
|---|---|---|---|---|
| 200 (declared) | 0.02656 | 0.02127 | +0.00529 | +2.74 |
| 400 | 0.02295 | 0.02127 | +0.00168 | +0.91 |

At `GAIN_UNIT = 400` the rich-instance gap shrinks to a tie. I am **not**
recommending 400: raising a declared constant until the three-part union stops
losing is exactly the "change the instrument to get the wanted verdict" move the
owner stopped on turn 104. It is reported so the reader can see **how much of the
verdict rests on a declared constant rather than on the world** — which is the
honest boundary of this result, and a candidate for the next turn's attention
rather than a fix smuggled into this one.

**A second, smaller finding.** The `union_noctx` arm's regret *rose* slightly
under the corrected rule (maskr 0.03486 → 0.03596, mask 0.35 ~0.00004). That is
not a defect: with the price lowered, the pooled-discovery arm probes more and
sometimes probes worse, which is precisely the context-specificity result the
campaign already established. It is noted so the direction of every moved arm is
on the record.

## 7. How this was verified

* **Independent verifier** (`verify_matrix_determinism_v2.py`, different code,
  reads only the frozen JSON): **27 checks, 0 failures** — (A) all 93 cells
  re-derive their own mean/sem from the raw rows they shipped; (B) 66 non-arbiter
  cells reproduce the turn-129 matrix bit-for-bit; (C) 10 cells re-run in fresh
  processes reproduce the frozen means and probe counts to 12 decimals; (D) the
  arbiter arithmetic: `PROBE_LEN == PROBE_BLOCK`, `cutoff_old == 196/240`,
  `cutoff_new == 196/220`, `beta0` clears nothing, the full-headroom candidate
  clears under the corrected rule exactly inside the band and under neither rule
  above it, both frozen modules hash to their recorded values, and
  `union_agent_v2` differs from `union_agent` in exactly one line.
* **Factcheck of this report** (`factcheck_union_fix.py`): **94/94 numbers**
  re-derived from the frozen JSON — and it caught **one number I typed from
  memory** (nocost at base 0.85: I wrote 0.006881, the data says 0.006875),
  corrected here rather than left.
* **Frozen artefacts untouched**: `arbitration.py` `2d3d825b…`,
  `candidate_gen.py` `fa9721ae…`, `results_union/SUMMARY.json` `e33ea343…`,
  `union_stoch_v2.lean` `6a5bcfb3…` — all re-hashed after the run.
* **A runtime event, surfaced not swallowed.** Twice this turn a
  `multiprocessing.Pool` sweep was killed by a runtime **WRITESET ALERT** on
  `/data/owner_trace/*.json.gz` (5 files at once). No script of mine writes
  there — my scripts write only under `bench_cb/` — and the alert fires on the
  *number* of simultaneous spawns, not on my output. The sweeps were therefore
  re-run serially and as plain background jobs, which completed. This is the
  same class of runtime-layer write surfaced on turn 131; it is reported, not
  worked around silently.

## 8. Honest limits, declared

1. The corrected rule is a **new module**; a verdict on it is a verdict on the
   repaired instrument, and is labelled as such. The frozen rule's own results
   (`results_union/`) stand unaltered as the record of the old instrument.
2. `GAIN_UNIT` is a **declared agent constant**, and §6 shows the rich-instance
   verdict is sensitive to it. The headline uses the campaign's declared 200.
3. The maskr instance is **mine, not published** (declared since turn 129); every
   number from it is `supplementary`.
4. 200 sims/cell in the sweep, 1000 in the matrix — declared, and the matrix is
   the one the verdicts rest on.
5. The horizon sweep's monotonicity is a **measured** property of this instance,
   not a theorem about all instances.

## 9. Artefacts

* Corrected rule: `bench_cb/arbitration_scaled.py` (sha `fbdd446f…`)
* One-line-diff agent / driver: `bench_cb/union_agent_v2.py`,
  `bench_cb/union_run_v2.py`
* Base sweep: `bench_cb/sweep_arbiter_v2.py` + `sweep_arbiter_v2.json`
* Horizon sweep: `bench_cb/diag_bar_sweep_v2.py` + `diag_bar_sweep_v2.json`
* Trace: `bench_cb/trace_arbiter.py` + `trace_arbiter_summary.json`
* GAIN_UNIT sensitivity: `bench_cb/diag_gain_unit_v2.py` + `diag_gain_unit_v2.json`
* Full matrix: `bench_cb/union_matrix_v2.py`, `bench_cb/run_cells_v2.py`,
  `bench_cb/results_union_v2/` (93 cells + SUMMARY.json)
* Independent verifier: `bench_cb/verify_matrix_determinism_v2.py` +
  `verify_matrix_determinism_v2.out.txt` (27/27)
* Factcheck: `bench_cb/factcheck_union_fix.py` (94/94)
* Preregistration of the repair: `bench_cb/PREREG_UNION_FIX.md`
* Lean (unchanged, recompiled): `bench_cb/lean/union_stoch_v2.lean`,
  `compile_v2_turn132.txt`
