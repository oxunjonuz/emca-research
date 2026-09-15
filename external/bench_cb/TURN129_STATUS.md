# TURN 129 STATUS — the UNION mechanism (context-specificity + exploration + cost-aware arbitration)

Directive: msg_00129. Status: **complete, one continuous run, independently verified.**

## What was asked

Turn 128 found the mechanism was a **verification**, not an **exploration**,
procedure and named the two missing pieces (exploration term; cost-aware
trade-off), both published. The owner said: build them **into C2** not as a copy
but as material, keeping what the campaign proved (context-specificity across six
worlds); re-run on the same hard instance (0.300); test **super-additivity** —
does the union do more than the parts?; attempt a Lean 4 proof of a regret bound
for the case where the true cause is **context-specific, not pooled**, and must
still be discovered; and if the union gives nothing over the sum, say so.

## What was done

1. **Surveyed prior art before choosing** (arXiv API, sources registered). Found
   the closest neighbour: **Additive Causal Bandits with Unknown Graph** (ICML
   2023, arXiv:2306.07858) — unknown graph but **requires additivity**. Confirmed
   `"causal bandit" AND "context-specific"` → **0 results**, so no such instance
   is published. Prior art is reported **first** in the report.
2. **Froze PREREG_UNION.md before the first run** (instance, mechanism, arms
   `union / union_noctx / union_noexp / union_nocost / union_pooledexp / pure /
   beta0 / budget_pub / uniform_policy`, hypotheses H1–H6, thresholds).
3. **Built** `union_instance.py` (context-specific causal bandit, on the authors'
   unmodified model interface), `union_agent.py` (context contrast +
   context-conditional exploration + frozen arbiter, one switch per ablation),
   `budget_agent.py` (declared cost-aware adaptation), `union_run.py`,
   `union_matrix.py`.
4. **Wrote + compiled + mutation-checked** `lean/UNION_BOUND.lean` — 3 obligations
   proved in core Lean 4.19 (no Mathlib), 3/3 mutations caught, no `sorry`/`axiom`.
5. **Ran the grid**: 93 cells × 1000 sims (mask ε∈{0.15,0.25,0.35} × 9 arms;
   maskr rich ε∈{0.25,0.35} × 9; pub m∈{2,8,16,25,40,49} × 8). 369 s.
6. **Independent verification** (different code, disk only, negative control):
   first pass 5 disagreements — **2 real, both fixed** (a wrong analytic
   expectation in the instance, caught by Monte-Carlo; a naive expectation in the
   verifier itself). Second pass **111 checks, 0 disagreements**, control fired.
7. **Factcheck of the report**: 46 statements → **ALL PASS**; it caught 3
   over-strong claims of mine, all corrected in the report rather than softened.

## The result — three honest answers

* **H1 SURVIVES**: on the published instance the union goes from the mechanism's
  worst-case **0.3000** to **0.0264–0.0276** (m≥16), beating Algorithm 1 at every
  **m≥8** (0.0276 vs 0.1056 at m=16; 0.0264 vs 0.2574 at m=49). It does **not**
  beat Algorithm 1 at **m=2** (0.0069 vs 0.0000) — reported first.
* **H2/H3 — the composition is real and super-additive.** On the context-specific
  instance: union **0.0051** vs union_noctx **0.1794**, union_noexp **0.1776**,
  pure **0.1804** (ε=0.35) — a **35.6×** gap. Removing **either** piece collapses
  the union. Directly measured: without exploration the true arm gets **0 pulls**
  (its natural rate is 0); with it but without the context split the arm is
  pulled but the effect is pooled to the flat marginal. Both pieces necessary,
  for different reasons.
* **H4 — the cost-aware arbiter FAILS.** `union == union_nocost` to four decimals
  on the main instance, and in the **rich** regime (`maskr`) the union is *worse*
  than nocost (0.0313 vs 0.0210). The third published piece does not earn its
  place; the recommended composition is **two-part**, not three-part.
* **H5 — proved for the combinatorial core, conjecture for the theorem.**
  `lean/UNION_BOUND.lean` proves (S) pooling **annihilates** a context-reversing
  effect (pooled gap exactly 0, per-context gaps ±2d), (P) a pooled rule
  nominates nothing, (B) discovery cost ≤ (exploration pulls)·Δ, independent of
  the pooled marginal. The **stochastic** regret bound is NOT proved — no Mathlib;
  the missing step (concentration) is named in the file and the report.
* **H6 SURVIVES**: the three-way union is not published as one mechanism, but the
  closest work (ICML 2023) assumes **additivity**, which a context-specific cause
  **violates**. The honest unoccupied point is: *non-additive, context-specific
  discovery from a reward stream, with exploration that keeps its
  context-specificity* — a composition claim, not a first-in-field claim.

## Honest limits

* The context instance is **mine, not published** (0 arXiv hits) — supplementary.
* `budget_pub` is a **declared adaptation**, not the authors' code.
* The exploration term is the **principle** of Algorithm 2, not its code.
* No Mathlib → finite-combinatorial Lean result, **not** a stochastic theorem.
* 1000 sims/cell (paper used 10 000). `MIN_PER_CTX` sensitivity {5,10,20} reported;
  verdicts do not move with it.
* Verified first pass caught a real defect in my own instance's analytic values.

## Artefacts

* `bench_cb/PREREG_UNION.md`, `bench_cb/RESULTS_UNION.md`
* `bench_cb/union_agent.py`, `union_instance.py`, `union_run.py`,
  `union_matrix.py`, `budget_agent.py`
* `bench_cb/results_union/` (93 cells + SUMMARY.json), `results_union_meta.json`
* `bench_cb/verify_union_independent.py` + `verify_union_out.txt` (ALL AGREE)
* `bench_cb/factcheck_union_report.py` (46/46)
* `bench_cb/lean/UNION_BOUND.lean` (+ out.txt, mut1..3.lean)
* sources: `src_a7f5b2eef8a0`, `src_7d19b569ae60`, `src_aaf0a4fed135`
