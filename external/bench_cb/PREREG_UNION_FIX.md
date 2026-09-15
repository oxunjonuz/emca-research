# PREREG — turn 132: repairing the arbiter's price scale (union line)

Written AFTER the trace measurement (`trace_arbiter.py`, `trace_arbiter_summary.json`)
and the horizon sweep (`sweep_arbiter_v2.py`, `diag_bar_sweep_v2.py`) had been run,
and BEFORE the full matrix was assembled into a report. The record is honest about
that order: the *repair* is a hypothesis about an engineering error, so the
measurement that established the error comes first; what is frozen HERE, before
the report, is the interpretation and the exact claims I will make.

Owner directive msg_00132: the diagnosis is accepted as a genuine engineering
error found before, not after, the result; repair it; then re-run the same base
sweep and say whether the effect disappeared or merely shifted; re-run the full
matrix on the fixed arbiter without mixing with old data; say explicitly whether
the Lean part is affected; report honestly whether the three-part union now beats
the two-part; and name any new problem as plainly as the old ones.

## 1. What the error was, in one line

`arbitration.rhs = rich_rate * H + PROBE_COST` billed the alternative's payoff
over `H = 40` declared evaluation steps, while a probe actually spends exactly
`PROBE_BLOCK = 20` steps (`union_agent.py`). The value side (`GAIN_UNIT = 200`)
is a valuation horizon; the price side was a *different* horizon. Both sides
carried the same units and neither carried a time base, so the mismatch was
invisible until the world's reward level moved.

## 2. What "repair" means here, and what it must NOT be

The repair is **not** free to be anything that improves the number. It must be

  (a) a single substitution, with no new free parameter: `PROBE_LEN =
      PROBE_BLOCK = 20`, the campaign's own declared probe length;
  (b) applied in a NEW module, `arbitration_scaled.py`, with the frozen
      `arbitration.py` left byte-identical (`sha256 2d3d825b…`), so no frozen
      artefact's producer is silently altered;
  (c) reachable by a one-line diff: `union_agent_v2.py` differs from
      `union_agent.py` in exactly the import line (checked by the verifier);
  (d) accompanied by the statement, in advance, that the cutoff it produces is
      NOT removable, because it is the economics:

        no probe can pay for itself once  (1 - r)·GAIN_UNIT ≤ r·PROBE_LEN + c
        r ≤ (GAIN_UNIT - c)/(GAIN_UNIT + PROBE_LEN) = 196/220 = 0.890909

      against the old 196/240 = 0.816667.

## 3. Frozen claims and their falsifiers (written before the report)

* **F1 — the error was real.** The old rule refuses a candidate carrying the
  FULL attainable headroom once `rich > 0.816667`; the corrected rule clears it
  up to `0.890909`.
  *Falsified if* the old rule clears a `1 - rich` candidate anywhere in
  (196/240, 196/220], or the corrected rule fails to.
* **F2 — the repair is not a shift of the same defect.** If the old silence was
  an artefact of a mis-chosen horizon, then the regime between the two cutoffs is
  the place where the two rules differ, and the maskr instance (rich ≈ 0.92) is
  *above both* — so the repair alone should NOT restore maskr to the two-part
  level. The horizon sweep (`diag_bar_sweep_v2.py`) tests this directly:
  *falsified if* there is an interior price horizon that beats both the frozen
  value and the no-price arm on maskr.
* **F3 — the honest question the owner asked: does the three-part union now beat
  the two-part?** Registered prediction, written BEFORE the fixed matrix was
  pooled: **NO on the rich instance, YES-or-tie on the main instance.**
  *Falsified if* `union` (corrected) beats `union_nocost` by more than 2 combined
  SEM on maskr, or loses to it by more than 2 combined SEM on mask.
* **F4 — the repair touches only the arms that consult the price.** Every arm
  whose action does not depend on `AR.plan` must reproduce the turn-129 matrix
  bit-for-bit.
  *Falsified by* any differing per-seed regret on such an arm.
* **F5 — the C1 control survives.** `beta0` must still probe exactly zero times
  under the corrected rule, at every base.
* **F6 — the formal part is unaffected.** The Lean development contains no term
  naming `GAIN_UNIT`, `H`, `PROBE_COST` or the price; its bound is stated with
  `bΔ` (an abstract per-pull loss budget) and a concentration argument.
  *Falsified if* any of those identifiers appears in `union_stoch_v2.lean`, or if
  the compile status changes.

## 4. What will be reported regardless

Every base from .50 to .95 for old rule, new rule, no-price and the `beta0`
control, with SEM; the full 93-cell matrix on the corrected rule in
`results_union_v2/`, never merged with `results_union/`; the horizon sweep; the
independent verification and its result; the explicit statement about the Lean
part; and, if a new problem is found on the way, its name.
