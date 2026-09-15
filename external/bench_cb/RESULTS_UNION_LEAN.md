/work/Shopify/audit-work/agent_arch/bench_cb/RESULTS_UNION_LEAN.md
# The stochastic Union bound: closed, with the premises tested

Turn 131. Continues the turn-129/130 Lean line. Owner directive: msg_00131
("продолжай"), standing intentions from turn 130.

Files: `bench_cb/lean/union_stoch_v2.lean` (the proofs, no `sorry`),
`bench_cb/lean/mutate_union_lean.py` (the premise campaign, frozen),
`bench_cb/lean/nonvacuity_v6.lean` (the bound is inhabited),
`bench_cb/lean/m10_followup.lean` (the survivor, examined).

---

## 1. The one thing turn 130 left open, and its cause

Turn 130 reported one wall: elaboration of the **T6 statement** timed out at
`whnf` (8M heartbeats). Root cause found and stated precisely: the empirical mean
was defined **pointwise**,

    sampleMean X n := fun ω => (n:ℝ)⁻¹ * ∑ i ∈ Finset.range n, X i ω

so that when the elaborator type-checked the `≤` between the `setOf` predicate
and the bound, it had to **unfold a `Finset.range` sum inside the predicate**.
Reformulating the same mean as a scalar multiple of the **sum function**,

    sMean X n := (n:ℝ)⁻¹ • ∑ i ∈ Finset.range n, X i

makes the term opaque to `whnf`. The statement then elaborates in ~8 s and the
proof closes. The two forms agree pointwise (`Union.sMean_apply`), so this is a
change in *what the elaborator unfolds*, not in *what is proved*.

Consequence for the T6 proof: the accounting step that failed in turn 130
(`Var[sMean] = (n)⁻¹² · Var[ΣX]`) is now a one-line consequence of
`variance_smul` — `Union.variance_mean_le`.

## 2. What is now proved, and the one thing that is NOT

`union_stoch_v2.lean`, compiled in one fresh `lake env lean` run, exit 0:

| id | statement |
|----|-----------|
| T7 | `pooled_gap_zero` — pooling a context-reversal annihilates the effect |
| T1 | `integral_le_of_split` — expectation split at a measurable bad event |
| T2 | `bad_le_sum` — finite union bound in real-measure form |
| T3 | `expected_regret_le` — 𝔼[R] ≤ bΔ + M·Σpᵢ |
| T4 | `hoeffding_mean_le` — sub-Gaussian Hoeffding for a sample mean |
| T5 | `chebyshev_abs` — Chebyshev with explicit variance bound |
| T5b | `variance_sum_le` — n independent [0,1] pulls have variance ≤ n/4 |
| T6 | `chebyshev_sample_mean` — **CLOSED** (was the wall) |
| T9 | `union_regret_bound` — the full bound, **`hp` DISCHARGED** |

**T9 is the substantive change from turn 130.** There, the per-context bad-event
probability was an *assumption* (`hp`). Now it is *proved*: T9 takes an explicit
family of `r` independent `[0,1]` pulls per context, applies T6 once per context,
and gets

    𝔼[R] ≤ bΔ + M · k/(4 r ε²)

with no probability hypothesis left. The bound mentions the exploration budget,
the number of pulls and the loss scale — and no pooled marginal.

**What is still NOT proved, named rather than hidden:** Mathlib has Hoeffding's
*inequality* for sub-Gaussian variables but not Hoeffding's *lemma* (bounded ⇒
sub-Gaussian). T4 is therefore stated for variables that carry
`HasSubgaussianMGF`; the unconditional route is Chebyshev + Popoviciu, and that
is the route T9 uses. Both routes are in the file; neither assumes the missing
bridge. This is unchanged from turn 130 and is a genuine limit of the library,
not of the argument.

**A dead hypothesis removed.** T1 in turn 130 carried `0 ≤ bΔ` and `0 ≤ M` which
its proof never used. They are dropped — nonnegativity is used one level up in
T3. A dead hypothesis is exactly what a premise campaign would report as a
survivor, so it is removed rather than kept as decoration.

## 3. Kernel audit, not a grep

`#print axioms` on all 15 declarations plus the two non-vacuity lemmas: every one
depends only on `propext`, `Classical.choice`, `Quot.sound`. **No `sorryAx`**
anywhere. A `grep` for `sorry` is a text check; this asks the kernel.

## 4. The premise campaign — and a survivor I must report

`mutate_union_lean.py` introduces 10 faults, one at a time, and records for each
the exit code, the first error verbatim, and a **classification of the red**:

- `semantic_conclusion` — the statement is now false/different and the proof
  cannot reach it (the constant IS load-bearing);
- `syntactic_reference` — the body names something that no longer exists: this
  reds a NAME, not a fact, and is recorded as **weak** evidence;
- `ill_typed` — the mutated header no longer type-checks as a function.

| id | mutation | result | class |
|----|----------|--------|-------|
| M1 | T6 conclusion 1/(4nε²) → 1/(2nε²) | red | semantic |
| M2 | T6 conclusion ε² → ε | red | semantic |
| M3 | T9 conclusion k/(4rε²) → k/(2rε²) | red | semantic |
| M4 | T7 pooled gap 0 → 1 | red | semantic |
| M5 | T7 drops `d ≤ s` | red | semantic |
| M6 | T4 exponent /2 → /4 | red | semantic |
| M7 | T6 drops `h_indep` from the signature | red | syntactic |
| M8 | T6 drops the [0,1] bound from the signature | red | syntactic |
| M9 | T9's internal `hp` 1/(4rε²) → 1/(8rε²) | red | ill_typed |
| M10 | T5b constant n/4 → n/2 (**looser**) | red | **SURVIVOR** (see below) |

**The campaign's own tally needed correcting, twice.** The engine classified 7
mutants as `semantic_conclusion` — but one of those 7 (M10) is the survivor below,
so the genuine semantic kills are **6** (M1–M6). M9 reds with a *type mismatch*
on the internal `hp` constant, which is real but of a different kind (the internal
witness is pinned by type, not by arithmetic). M7/M8 red because the proof *body*
still names the removed hypothesis — they show independence and boundedness are
*used in the proof term*, which is real but weaker than a semantic kill. Honest
tally: **6 semantic + 1 type-level + 2 syntactic + 1 survivor = 10.**

**M10 is a survivor, and the campaign printed it as a kill.** The mutation asks
T5b to prove the *weaker* bound `≤ n/2`, which is provable — `m10_followup.lean`
does exactly that, by transitivity from the `n/4` result, and compiles. So the
red is an artefact of the mutant's own `calc` block being pinned to `n/4`, not a
mathematical failure. Reported as a survivor: **the suite does not pin the tight
constant**, it pins the statement's *shape*. This is the second time in this
campaign that a "caught" mutant had to be un-claimed after inspection (turn 127,
the verifier's own `X[a]` bug; turn 126, the `seconds` field).

A note on the classifier itself: it is a string rule over the first error line,
and it is the weakest part of this campaign. It read M9 as `other` (the error is a
*type mismatch* on the internal `hp` witness) and it read M10 as `semantic` when
the cause was the mutant's own `calc` pinning. The classes are useful for
triage and must not be reported as verdicts — which is why the table above is
hand-corrected rather than copied from `mutation_summary.json`.

## 5. Non-vacuity — the bound constrains something

A theorem with unsatisfiable hypotheses is true and empty. `nonvacuity_v6.lean`
APPLIES T9 on `Ω = Unit`, `μ = dirac ()`, `k = 1`, `r = 1`, `X ≡ 1/2`,
`R ≡ 0`: all five hypotheses discharged, conclusion reduces to `0 ≤ 0`. To do
that it needed a lemma Mathlib does not have — *every* family is independent on a
one-point space — proved here by hand (`UnionNV.iIndepFun_unit`). So T9 is
inhabited, and this is checked, not asserted.

## 6. What this does and does not do to the turn-129 claim

Turn 129 proved the **combinatorial core** (pooling annihilates; discovery cost
≤ pulls × Δ) and named the stochastic step as missing. Turn 131 closes the
stochastic step: the concentration premise is discharged, not assumed, on the
same route turn 129/130 pointed at. What it still does not do: it does not make
the *modelling identification* ("context i's bad event is its own contrast being
off by ε") a theorem — that stays a modelling step, stated in the file. And it
does not touch the H4 finding from turn 129 (the cost-aware arbiter fails on the
rich regime); that is a separate, still-open item.

## 8. The rich regime: why the cost-aware arbiter hurts — cause found, and a hypothesis refuted

Turn 129 reported H4 as a bare number: in the rich regime `union` is *worse* than
`union_nocost` (0.0313 vs 0.0210). Turn 131 found the mechanism.

**First hypothesis, refuted by its own control.** The rich instance (`maskr`) sets
`base = 0.8`, so the true cause's raw `pY` in context 0 is `0.8 + 0.35 = 1.15`,
**clipped to 1.0**, while the decoy sits at `0.95` — the observable in-context
contrast collapses from 0.20 to 0.05. That looked like the cause. It is not:
`diag_cost_decompose.py` runs the same instance with `base = 0.8` and **no clip**,
so the contrast is restored to 0.20 — and the arbiter *still* probes 0.04 times
per run, exactly as with the clip. Clipping is refuted as the cause.

**The actual cause, traced source by source.** Instrumenting the two candidate
sources separately (60 runs each):

| | top exploration score | observed `rich_rate` | value = 200·score | rhs = rich·40 + 4 |
|---|---|---|---|---|
| `mask` (base .5) | 0.5094 | 0.6435 | **101.9** | 29.7 → clears |
| `maskr` (base .8) | 0.1837 | 0.9228 | **36.7** | 40.9 → fails |

The arbiter compares `value = β·GAIN_UNIT·gap` against `rhs = rich_rate·H +
PROBE_COST`. **Both sides scale with the world's reward range, but not the same
way:** `rhs` is *affine* in `rich_rate`, while any achievable `gap` is bounded
above by `1 − rich_rate` — and in practice by the *empirical* contrast, which is
smaller still. So the bar `(rich·H + c)/GAIN_UNIT` rises linearly while the
headroom shrinks, and past a crossover the arbiter stops probing **entirely** —
not because the information became less valuable, but because the two terms are
on different scales.

**Measured, not asserted.** `diag_cost_baseline_sweep.py` sweeps `base` across the
transition on the same instance (200 sims/cell):

| base | union probes | union clear% | nocost probes | beta0 probes | union regret |
|---|---|---|---|---|---|
| 0.50 | 3.365 | 3.7% | 4.330 | 0.000 | 0.00486 |
| 0.55 | 3.180 | 3.6% | 4.160 | 0.000 | 0.01197 |
| 0.60 | 2.755 | 2.3% | 3.985 | 0.000 | 0.03392 |
| 0.65 | 2.405 | 1.8% | 4.135 | 0.000 | 0.04625 |
| 0.70 | 1.655 | 1.1% | 4.305 | 0.000 | 0.04932 |
| 0.75 | 0.440 | 0.3% | 4.425 | 0.000 | 0.05143 |
| 0.80 | **0.010** | **0.0%** | 4.455 | 0.000 | 0.03100 |

Three things hold: (i) `union`'s probe count falls **monotonically** to zero as
the alternative gets richer; (ii) `union_nocost`'s does **not** (it has no price
term) — so the loss is attributable to the price, not to the instance; (iii)
`beta0` probes exactly zero everywhere — the control is alive. The regret is
non-monotone (peaks at 0.75, drops at 0.80) because at 0.80 the union degenerates
to the greedy pooled policy, whose own regret is 0.0310 — i.e. it stops exploring
and returns to the no-probe floor.

**Honest statement of what this is.** It is a diagnosis of the frozen rule, not a
fix. Turn 129's H4 said the third published piece does not earn its place; this
says *why*: the rule's two terms are on different scales, and the scale mismatch
is invisible while the alternative is poor and fatal once it is rich. Whether to
repair the rule (rescale `rhs` by `GAIN_UNIT`, or make the price relative) is a
decision for the owner — repairing it now would be the same class of move the
owner stopped on turn 104: changing the instrument to get the verdict you want.
The frozen matrix is untouched.

## 9. Reproduce

    cd /work/Shopify/audit-work/mathlib
    lake env lean /work/Shopify/audit-work/agent_arch/bench_cb/lean/union_stoch_v2.lean
    # exit 0, no output, no sorry
    python3 /work/Shopify/audit-work/agent_arch/bench_cb/lean/mutate_union_lean.py
    # baseline green, 10 mutants, mutation_summary.json

## Honest limits

- The modelling identification is a step, not a theorem (stated in T9's docstring).
- Hoeffding's lemma is absent from Mathlib; T4 stays conditional by construction.
- Honest tally: 6 semantic kills (M1–M6) + 1 type-level (M9) + 2 syntactic (M7, M8)
  + 1 survivor (M10). The engine's own `semantic_conclusion` class over-counted by
  one, because M10 sits in it; the class is a string rule, and a string rule cannot
  see that the mutant's own `calc` is what reddened.
- M7/M8 are name-based reds; counted separately, not as logic.

## 10. Artifact ledger (sha256 in the provenance ledger)

| id | path | what |
|----|------|------|
| art_74274ad62eb4 | lean/union_stoch_v2.lean | the proofs T1–T9, no `sorry` |
| art_87930c8376b6 | lean/mutation_summary.json | the 10-mutant campaign record |
| art_42430d620ec4 | lean/verify_union_lean_out.json | independent pass, 8/8 |
| art_d382a051f999 | diag_cost_decomposition.json | the refuted clipping hypothesis |
| art_668d8c832bb3 | diag_cost_baseline_sweep.json | the cause, swept |
