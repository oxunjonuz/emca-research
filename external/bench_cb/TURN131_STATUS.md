# TURN 131 STATUS — the stochastic bound closed, its premises tested, and the rich regime explained

Directive: msg_00131 ("продолжай"), continuing the standing intentions from
turn 130. Status: **complete, one continuous run, independently verified.**

## What was open coming in

Turn 130 ended with three named obligations and one wall:
1. close T6 (`chesbyshev_sample_mean`) — its STATEMENT timed out at `whnf`;
2. glue T6 with T8 into one theorem without the hypothesis `hp`;
3. audit `sorry`/`axiom` and mutation-test the premises.

Plus the turn-129 open item: H4, why the cost-aware arbiter hurts.

## What was done

1. **Diagnosed and removed the wall.** The `whnf` timeout was caused by the
   *pointwise* definition of the empirical mean: it forced the elaborator to
   unfold a `Finset.range` sum inside the `setOf` predicate. Redefining the mean
   as a scalar multiple of the sum function (`(n)⁻¹ • ∑ X i`) makes it opaque to
   `whnf`. `Union.sMean_apply` proves the two forms agree pointwise, so nothing
   about the content changed.
2. **T6 closed**; the variance accounting that failed in turn 130 is now a
   one-line consequence of `variance_smul` (`Union.variance_mean_le`).
3. **T9 written: `hp` DISCHARGED.** The per-context bad-event probability is no
   longer an assumption — T9 takes an explicit `r`-pull `[0,1]` family per
   context, applies T6 once per context, and concludes
   `𝔼[R] ≤ bΔ + M·k/(4 r ε²)`. A dead hypothesis in T1 (`0 ≤ bΔ`, `0 ≤ M`) was
   found and removed.
4. **Kernel audit.** `#print axioms` on all 15 declarations + the non-vacuity
   lemmas: everything rests on `propext`, `Classical.choice`, `Quot.sound` only.
   No `sorryAx`.
5. **Premise campaign** (`mutate_union_lean.py`, frozen, `mutation_summary.json`):
   10 mutants, baseline green first. Hand-tallied from the raw error lines:
   **6 semantic kills** (M1–M6, constant/statement load-bearing), 1 type-level
   (M9), 2 that red only because the proof body names the removed hypothesis
   (M7/M8, recorded as weak), and **1 survivor** (M10) — see below. The engine's
   own class over-counted: it is a string rule over the first error line, and it
   cannot see that M10's red came from the mutant's own `calc`.
6. **Non-vacuity**: T9 APPLIED to a concrete instance, which required proving a
   lemma Mathlib lacks (every family is independent on a one-point space).
7. **Rich regime explained**: the turn-129 H4 number now has a mechanism, and my
   first hypothesis about it was refuted by its own control.

## Honest corrections I must report

* **A survivor.** M10 mutated T5b's constant from `n/4` to the *weaker* `n/2` and
  reddened — the campaign first printed it as a kill. It is not one:
  `m10_followup.lean` proves the `n/2` statement by transitivity and compiles.
  The red was an artefact of the mutant's own `calc` block being pinned to `n/4`.
  So the suite pins the statement's *shape*, not the tight constant. Counted as a
  survivor. Corrected tally: **6 semantic + 1 type-level + 2 syntactic + 1
  survivor**, not the "10/10 caught" the engine printed.
* **A refuted hypothesis.** I first attributed the rich-regime failure to clipping
  (`base=0.8` puts the true cause at `1.15 → 1.0`, compressing the contrast). The
  no-clip control at the same `base` kept probing 0.04 times/run — clipping is
  refuted. The real cause is a scale mismatch in the frozen rule: `rhs` is affine
  in `rich_rate` while the achievable gap is bounded by `1 − rich_rate`.
* **A harness event I did not cause but must surface.** During the baseline sweep
  the runtime emitted a WRITESET ALERT for `/data/resume_state.jsonl` (outside the
  workbench, in protected home). No script of mine writes there — my own scripts
  write only under `bench_cb/` — so this is a runtime-layer write, surfaced rather
  than swallowed.

## Verification (independent path, disk only, no producer imported for the checks)

`verify_union_lean_independent.py`: **8/8 PASS**, including a fresh compile of
`union_stoch_v2.lean` (exit 0, zero bytes of output), a recomputed kernel-axiom
list (15/15, no `sorryAx`, no unexpected axioms), a `#check` that every
declaration named in the report exists, and a disk-vs-summary agreement check on
all 10 mutants (fresh exit codes match the recorded ones).

## Artefacts

* `bench_cb/lean/union_stoch_v2.lean` — the proofs (T1–T9), no `sorry`
* `bench_cb/lean/nonvacuity_v6.lean` — T9 applied to a concrete instance
* `bench_cb/lean/m10_followup.lean` — the survivor, examined
* `bench_cb/lean/mutate_union_lean.py` + `mutation_summary.json` — the campaign
* `bench_cb/lean/verify_union_lean_independent.py` + `verify_union_lean_out.json`
* `bench_cb/diag_cost_decompose.py` + `diag_cost_decomposition.json` — the refuted hypothesis
* `bench_cb/diag_cost_baseline_sweep.py` + `diag_cost_baseline_sweep.json` — the cause
* `bench_cb/RESULTS_UNION_LEAN.md` — the report

## Not done, said plainly

* The modelling identification ("context i's bad event = its contrast is off by ε")
  remains a modelling step, not a theorem — stated in T9's docstring.
* Hoeffding's lemma is absent from Mathlib; T4 stays conditional by construction.
* The arbiter's scale mismatch is DIAGNOSED, not repaired. Repairing it would be
  the same class of move the owner stopped on turn 104 (changing the instrument to
  get the wanted verdict). Frozen matrix untouched: 404 V8 files and 94 union
  cells unchanged.
