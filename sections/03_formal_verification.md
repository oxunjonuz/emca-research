# Section 03 — Formal verification (Lean 4): what is proved, what is conjecture

*The owner asked for "что доказано, что осталось conjecture, с честной границей".
This section is that boundary, quoted from the frozen Lean files and reports in
`../external/bench_cb/lean/` and `../external/bench_cb/RESULTS_*.md`.*

> **Corrected in turn 151 — see `../ERRATA.md` §3–§4.** Two errors in this section's
> first version: three mutants (M1, M3, M6) were mis-classified as semantic
> refutations when they are *loosenings*, and T9's retained premise `hgood` was not
> named. Both are now fixed below, and the weakening is proved in Lean
> (`external/bench_cb/lean/WEAKENING_CHECK.lean`, exit 0).

---

## 0. The boundary in one paragraph

Two Lean 4 developments exist. The first (`UNION_BOUND.lean`, core Lean 4.19.0)
proves the **finite combinatorial core** of the union's claim: that pooling
annihilates a context-reversed effect while the per-context gap survives, and that
the extra discovery cost is bounded by the number of exploration pulls times the
per-pull loss, **independent of the pooled marginal**. The second
(`union_stoch_v2.lean`) discharges the **concentration probability** `hp` from
Chebyshev, so the per-context bad-event bound `≤ 1/(4rε²)` is *proved* rather than
assumed.

**What is still NOT proved is more than the earlier draft of this section said**,
and the owner's re-reading (turn 151) is the reason this paragraph was rewritten:

* the **modelling identification** — that "context i's bad event is its own contrast
  being off by ε" — remains a modelling step, stated in the file's docstring, not a
  theorem. **Turn 154 closed this item as far as it can be closed, and the answer is
  a reason rather than a proof: see §5.1 below — the identification is a *conditional*,
  and at the agent's own parameters the bound it feeds is vacuous.**
* **T9 still carries the premise `hgood`** — "outside the bad event, regret ≤ bΔ" —
  which links estimator accuracy to regret. **Its applicability to the agent
  actually implemented is not proved**; it is assumed at the statement level. So
  "the concentration premise is discharged" must not be read as "no premises left".
  **Turn 154 proved it is an INDEPENDENT premise, by counterexample — not a corollary
  of the identification (§5.1).**
* the **mutation campaign's "semantic kills" were over-counted** (three of them are
  loosenings, not refutations). Corrected in §3 below, with a Lean proof of the
  weakening.

---

## 1. `UNION_BOUND.lean` — the combinatorial core

Core Lean **4.19.0**, compiles clean (`out.txt` empty, `grep` finds no
`sorry`/`admit`/`axiom`). **No Mathlib is installed in this image** — declared, and
it bounds what could be said. Three obligations, each genuine (a mutated statement
is **false**, verified — 3/3 mutations caught):

| id | statement | what it establishes |
|---|---|---|
| `separation` | for two balanced contexts on an arm whose effect reverses (`s+d` successes in one, `s−d` in the other, `d ≤ s`), the per-context gaps are `±2d` and the **pooled gap is exactly 0**, for *every* `s, d` | the precise reason a pooled scan **cannot** see the arm — the context split is necessary, not cosmetic |
| `pooled_probes_none` | a pooled rule with margin `M > 0` therefore nominates nothing among the reversed arms | the pooled rule is blind by theorem, not by tuning |
| `union_regret_le` | for a finite arm set, if each exploration pull loses at most `Δ`, total exploration regret ≤ `len · Δ`, **independent of the pooled marginal** | the finite skeleton of the regret bound: the extra discovery cost is bounded by the number of exploration pulls times the per-pull loss, and does not mention the pooled marginal |

**What is NOT proved here, stated exactly:** the *stochastic* regret bound — the
transition from "these pulls lose at most Δ" (a deterministic fact about a realised
run) to "expected regret ≤ O(exploration budget · Δ)" requires a concentration
argument that needs Mathlib's measure theory, which was not available when this
file was written. The missing step is named: *bound the probability that a per-pull
loss exceeds Δ, then integrate.*

---

## 2. `union_stoch_v2.lean` — the stochastic step, closed

Compiled in one fresh `lake env lean` run, exit 0. The file proves T1–T9. **T9 is
the substantive change from the earlier turn**: there, the per-context bad-event
probability was an *assumption* (`hp`); now it is *proved*.

| id | statement |
|---|---|
| **T7** | `pooled_gap_zero` — pooling a context-reversal annihilates the effect |
| **T1** | `integral_le_of_split` — expectation split at a measurable bad event |
| **T2** | `bad_le_sum` — finite union bound in real-measure form |
| **T3** | `expected_regret_le` — 𝔼[R] ≤ bΔ + M·Σpᵢ |
| **T4** | `hoeffding_mean_le` — sub-Gaussian Hoeffding for a sample mean |
| **T5** | `chebyshev_abs` — Chebyshev with explicit variance bound |
| **T5b** | `variance_sum_le` — n independent [0,1] pulls have variance ≤ n/4 |
| **T6** | `chebyshev_sample_mean` — **CLOSED** (was the elaboration wall) |
| **T9** | `union_regret_bound` — the full bound, **`hp` DISCHARGED** |

T9 takes an explicit family of `r` independent `[0,1]` pulls per context, applies
T6 once per context, and gets

    𝔼[R] ≤ bΔ + M · k/(4 r ε²)

**with no probability hypothesis left.** The bound mentions the exploration budget,
the number of pulls and the loss scale — and no pooled marginal.

**Kernel audit, not a grep.** `#print axioms` on all 15 declarations plus the two
non-vacuity lemmas: every one depends only on `propext`, `Classical.choice`,
`Quot.sound`. **No `sorryAx` anywhere.** A `grep` for `sorry` is a text check; this
asks the kernel.

**Non-vacuity — the bound constrains something.** A theorem with unsatisfiable
hypotheses is true and empty. `nonvacuity_v6.lean` APPLIES T9 on `Ω = Unit`,
`μ = dirac ()`, `k = 1`, `r = 1`, `X ≡ 1/2`, `R ≡ 0`: all five hypotheses
discharged, conclusion reduces to `0 ≤ 0`. To do that it needed a lemma Mathlib does
not have — *every* family is independent on a one-point space — proved by hand
(`UnionNV.iIndepFun_unit`). So T9 is inhabited, and this is checked, not asserted.

---

## 3. The premise campaign — with the owner's correction (turn 151), which is right

**The owner's point, and it is a real mathematical error in this section:** M1, M3
and M6 were reported as *semantic refutations* (`semantic_conclusion` — "the
statement is now false"). **They are not.** They replace a bound by a **looser**
one, which is still true; only the original *proof term* stops type-checking.
Formally: from `P ≤ 1/(4nε²)` one gets `P ≤ 1/(2nε²)`, because
`1/(2nε²) ≥ 1/(4nε²)`. A red proof is not a false statement.

I verified this directly, by proving the weakening arithmetic in Lean
(`external/bench_cb/lean/WEAKENING_CHECK.lean`, compiles clean, exit 0):

| theorem | statement proved | witnesses |
|---|---|---|
| `m1_weaker` | `1/(4nε²) ≤ 1/(2nε²)` | M1's mutated RHS is the **larger** one |
| `m3_weaker` | `k/(4rε²) ≤ k/(2rε²)` | M3 likewise |
| `m6_weaker` | `exp(-(nε²)/(2c)) ≤ exp(-(nε²)/(4c))` | M6's mutated exponent is the **larger** one → weaker bound |
| `substitution_is_weakening` | `P ≤ A → A ≤ B → P ≤ B` | the general form: a looser bound is not a refutation |
| `m2_is_not_a_weakening` | `1/(4·1·(½)²) > 1/(4·1·(½))` | M2 (`ε² → ε`) is **tighter** for ε<1 — genuinely different |
| `m4_is_a_different_statement` | `(0:ℤ) ≠ 1` | M4 changes an equality to a different one, not a bound |
| `m5_is_strictly_stronger` | the dropped hypothesis makes the claim strictly stronger, and it is then false | M5 is a real strengthening, not a loosening |

So the honest classification of the ten mutants is:

| class | mutants | what a red actually shows |
|---|---|---|
| **genuine semantic change / real refutation** | **M2, M4, M5** | the mutated claim is *not* implied by the original: M2 is tighter, M4 asserts a different value, M5 drops a hypothesis and becomes false |
| **loosening (red proof, true statement)** | **M1, M3, M6** | the statement is unchanged in truth value; **the original proof term is what broke** |
| name-based | M7, M8 | a removed hypothesis is still *named* by the proof body |
| type-level | M9 | the internal `hp` witness is pinned by type |
| **survivor** | **M10** | the suite pins the statement's *shape*, not its tight constant |

**So the earlier tally in this section ("6 semantic kills") was wrong**, and the
report's own text had already warned why: the classifier is a string rule over the
first error line and "must not be reported as verdicts". It said
`semantic_conclusion` for every `unsolved goals`/`omega`-failure — but `omega`
failing to close a goal is exactly what happens when the *proof* was written for a
tighter constant. **Corrected tally: 3 genuine semantic refutations (M2, M4, M5) +
3 loosenings (M1, M3, M6) + 2 name-based (M7, M8) + 1 type-level (M9) + 1 survivor
(M10).** The mutation campaign still says something real — the statements' *shapes*
are pinned and the proof terms are load-bearing — but it does not say "nine of ten
mutated theorems are false".

### 3.1 The other half of the owner's point: `hgood` is not discharged either

The owner notes that T9 retains `hgood`. **Correct.** T9's signature carries

    (hgood : ∀ ω, ω ∉ (⋃ i, {ω | ε ≤ |sMean (X i) r ω − ∫ …|}) → R ω ≤ bΔ)

i.e. "**outside** the bad event, the regret is at most `bΔ`". This is a modelling
premise relating the estimator's accuracy to the regret, and **whether it holds for
the agent actually implemented is not proved** — it is assumed at the statement
level. What T9 *does* discharge is the **probability** hypothesis `hp`
(`μ.real Bᵢ ≤ 1/(4rε²)`), which is now proved from Chebyshev. So the honest sentence
for section 0 should be: **the concentration probability is discharged; the
accuracy→regret premise `hgood` is not, and its applicability to the implemented
agent is an open modelling obligation.** The earlier phrasing ("with no probability
hypothesis left") is true of `hp` and should not be read as "no premises left".

---

## 4. A dead hypothesis removed

T1 in the earlier turn carried `0 ≤ bΔ` and `0 ≤ M` which its proof never used. They
are dropped — nonnegativity is used one level up in T3. **A dead hypothesis is
exactly what a premise campaign would report as a survivor**, so it is removed
rather than kept as decoration.

---

## 5. The boundary, stated plainly

**Proved:**

* pooling annihilates a context-reversed effect (`separation` / `pooled_gap_zero`);
* a pooled rule nominates nothing among reversed arms (`pooled_probes_none`);
* the discovery cost is bounded by pulls × per-pull loss, independent of the pooled
  marginal (`union_regret_le`);
* the full stochastic bound `𝔼[R] ≤ bΔ + M·k/(4rε²)` with the concentration premise
  **discharged** (`union_regret_bound`);
* the bound is inhabited (non-vacuity, checked);
* **(turn 154, §5.1)** the identification is a **conditional**, and `hgood` is an
  **independent premise** (counterexample).

**NOT proved (conjecture or assumption, named):**

* the **modelling identification** — that context i's bad event is its own contrast
  being off by ε — is a modelling step, stated in T9's docstring, not a theorem.
  **Turn 154 established the concrete reason it cannot be a theorem *for this agent*:
  see §5.1.**
* **`hgood`** — the accuracy→regret premise — is **not** discharged, and **cannot be
  derived from the concentration hypothesis** (§5.1, by counterexample);
* **Hoeffding's lemma** (bounded ⇒ sub-Gaussian) is absent from Mathlib; T4 stays
  conditional on `HasSubgaussianMGF` by construction. The unconditional route is
  Chebyshev + Popoviciu, and that is the route T9 uses;
* the tight constant of T5b is **not pinned** by the suite (M10 survivor);
* nothing here touches the **H4 finding** (the cost-aware arbiter fails on the rich
  regime) — that is a separate, still-open item, and its *cause* (the two terms of
  the frozen rule are on different scales) was diagnosed separately in
  `RESULTS_UNION_LEAN.md` §8, not proved.

---

## 5.1 The modelling identification, closed as far as it can be (turn 154)

*NEW_TZ item 3. File: `../external/bench_cb/lean/IDENTIFICATION_BOUND.lean`
(exit 0, no `sorry`, kernel-audited: every declaration depends only on `propext`,
`Classical.choice`, `Quot.sound`). The owner's instruction was explicit: if the
claimed formal link cannot be proved, **find the concrete reason, and do not count
the item done merely because it was moved into limitations.***

**1. The identification is a conditional, and the theorem says so.**
`identification_is_conditional`: *if* the agent's realised contrast IS the sample mean
of the family `X i`, *then* "the agent's contrast is off by ε" and T9's bad event are
the same set. The hypothesis is **not derived anywhere** in the development — the
theorem makes the modelling step visible instead of leaving it implicit.

**2. `hgood` is an independent premise, by counterexample, not by assertion.**
`hgood_is_an_independent_premise`: on the one-point space the bad event is empty (so
the concentration hypothesis holds with room to spare), and yet `R ≡ 1` with `bΔ = 0`
violates `hgood` at every point. **So the concentration hypothesis does not imply
`hgood`, and the identification does not either.**

**3. The concrete reason the link cannot be claimed — the bound at the agent's own
numbers.** The frozen brake's evidence window is `r = MIN_OBS = 5` rich steps and the
gap it must resolve is `ε = SOCIAL_COST − rich_rate = 0.30 − 0.05 = 1/4`. At those
numbers:

| claim | Lean name | value |
|---|---|---|
| T9's per-context bound at the agent's parameters | `bound_at_implemented_params` | `1/(4·5·(1/4)²) = 4/5` |
| ... and it is not a guarantee | `bound_at_implemented_params_is_vacuous` | `4/5 > 1/2` |
| pulls needed to reach the agent's OWN `P_VERDICT = 1/20` | `pulls_needed_for_agent_alpha` | `r ≥ 80 ↔ bound ≤ 1/20` |
| ... at exactly 80 pulls | `bound_at_eighty_pulls` | `1/(4·80·(1/4)²) = 1/20` |

**The agent has 5 pulls. The theorem is true and nearly empty exactly where the agent
lives.** That is the concrete reason, not a deferral.

**Mutation campaign against the Lean file** (`mutate_identification_lean.py`): 9
mutants, **7 killed**. The 2 survivors are honest and neither is a hole: **M1** changes
only the *proof body* while the theorem statement is byte-identical (an equivalent
survivor — the suite pins the statement, not the proof term), and **M5** loosens
`> 1/2` to `> 1/4` (weaker but true — a loosening, the same class as the earlier
campaign's M1/M3/M6). All three genuinely **false** statement-level mutants (M7: the
identification's conclusion replaced by the empty set; M8: `1/19` for `1/20`; M9:
`> 4/5` for `> 1/2`) are **killed**.

---

## 6. What this section does and does not do to the campaign's claim

It proves the **separation** that makes the composition necessary, and it closes the
stochastic step on one route. It does **not** make the campaign's mechanism superior
to published work (see section 02), and it does not repair the rich-world loss. The
Lean work is a proof about the *structure* of the composition, not a performance
claim.

---

## 7. Reproduce

    cd /work/Shopify/audit-work/mathlib
    lake env lean /work/Shopify/audit-work/agent_arch/bench_cb/lean/union_stoch_v2.lean
    # exit 0, no output, no sorry
    python3 /work/Shopify/audit-work/agent_arch/bench_cb/lean/mutate_union_lean.py
    # baseline green, 10 mutants, mutation_summary.json

---

## 8. Artefacts for this section

* `../external/bench_cb/lean/UNION_BOUND.lean` — the combinatorial core
* `../external/bench_cb/lean/union_stoch_v2.lean` — T1–T9, no `sorry`
* `../external/bench_cb/lean/mutate_union_lean.py`, `mutation_summary.json` — the
  premise campaign
* `../external/bench_cb/lean/nonvacuity_v6.lean`, `m10_followup.lean` — non-vacuity
  and the survivor examined
* `../external/bench_cb/lean/IDENTIFICATION_BOUND.lean` — the modelling-identification
  item closed as far as it can be (§5.1), plus `_ident_audit.lean` (kernel audit),
  `mutate_identification_lean.py` and `mutation_identification_summary.json`
* `../external/bench_cb/lean/verify_union_lean_independent.py`,
  `verify_union_lean_out.json` — independent pass (8/8)
* Reports: `../external/bench_cb/RESULTS_UNION.md` §7,
  `../external/bench_cb/RESULTS_UNION_LEAN.md`