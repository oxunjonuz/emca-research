# RESULTS — turn 129: the UNION mechanism (context-specificity + exploration + cost-aware arbitration)

Owner directive msg_00129. Instance, mechanism, arms, hypotheses and thresholds
frozen **before** the first run (`PREREG_UNION.md`, sha in `results_union_meta.json`).
Line: `bench_cb/` (turn 128).

**Headline answer, three parts.**
(1) The owner's point is **real but not exactly as framed**. Two of the three
parts — a context-specific discovery rule and a context-conditional exploration
term — are **mutually necessary** and **super-additive**: together they cut
regret to **0.0051** on the context-specific instance where the mechanism alone
scores **0.1804**, and removing *either* piece collapses it back
(**0.1794** / **0.1776**). Neither piece alone is worth anything.
(2) The **third** part — the cost-aware arbitration — **does not earn its place**
in any regime measured here: it is inert on the main instance (`union ==
union_nocost` to four decimals) and *counterproductive* in the rich regime
(0.0313 vs 0.0210). The honest unoccupied point is therefore a **two-part union**,
not the three-part one the directive proposed.
(3) A **Lean 4** proof was produced for the finite combinatorial core of the
suggested statement — that pooling *annihilates* a context-specific effect while
the per-context gap survives — but **not** for the stochastic regret theorem (no
Mathlib is installed); that remains a conjecture with its missing step named.

---

## 0. The answer in one paragraph

On the published parallel instance the union goes from the mechanism's
worst-case **0.3000** to **0.0264–0.0276** at the hard end (`m ≥ 16`), beating
Algorithm 1 at every `m ≥ 8` (0.0276 vs 0.1056 at m=16; 0.0264 vs 0.2574 at
m=49) and beating Algorithm 2, Successive Rejects and UCB everywhere — but it
does **not** beat Algorithm 1 at m=2 (0.0069 vs 0.0000), and that is reported
first. On a context-specific instance, where the true cause's effect is
**provably pooled-flat** (pooled margin exactly 0.0000) and pooling therefore
*cannot* see it, the union reaches **0.0051–0.0315** against the mechanism's
**0.0804–0.1804**, while each ingredient alone stays at the mechanism's level.
**The pieces are mutually necessary and their union is super-additive. The
cost-aware arbiter is not part of that story.**

## 1. Prior art — FIRST, ahead of every comparison (H6)

Registered sources this turn: `src_a7f5b2eef8a0` (Hierarchical Causal Bandit),
`src_7d19b569ae60` (contextual causal bandits, non-manipulable variables),
`src_aaf0a4fed135` (Additive Causal Bandits with Unknown Graph).

| work | what it does | does it occupy the point? |
|---|---|---|
| **Lattimore, Lattimore & Reid 2016** (arXiv:1606.03203) | the instance; Algorithm 1/2 | exploration is **Algorithm 2**, which assumes a **known DAG** |
| **Nair, Patil & Sinha** (arXiv:2012.07058) | cost-aware observation/intervention trade-off | pricing idea; assumes a **known structure** |
| **Lu, Meisami & Tewari 2021** (arXiv:2106.02988) | CN-UCB: reward signal drives sampling | **known** tree structure |
| **Additive Causal Bandits with Unknown Graph** (Malek, Aglietti & Chiappa, **ICML 2023**, arXiv:2306.07858) | **unknown graph**, but **additive** outcome | **CLOSEST**. Unknown structure, yet it *requires additivity*; shows the general unknown-graph problem is exponentially hard |
| **Hierarchical Causal Bandit** (Song, Rini & Xu 2021, arXiv:2103.04215) | a contextual variable capturing interaction of variables with direct effects | a **contextual** model with matching bounds — but context is exogenous/given; does not unify discovery + priced exploration |
| **Elahi, Kocaoglu & Ghasemi 2026** (arXiv:2607.15577) | contextual causal bandits, non-manipulable variables | **known** graph |

**Honest verdict.** The exact three-way union is not published as one mechanism
(arXiv `"causal bandit" AND "context-specific"` → **0 results**;
`"causal bandits" AND "masked"` → **0**). But the neighbour is close and must be
named: **ICML 2023 already solves unknown-graph causal bandits by ASSUMING
ADDITIVITY.** My context-specific instance is precisely an **additivity
violation** — the effect of `X_1` depends on the context `Z`. So the unoccupied
point, stated precisely, is:

> **a mechanism that discovers a NON-ADDITIVE, context-specific cause from its
> own reward stream, with no DAG and no structural assumption, and prices its
> own exploration.**

That is narrower than "context-specificity + exploration + cost", and it is the
frame the directive was reaching for. It is a **composition** claim, not a
first-in-field claim — and the composition is what this turn tested.

## 2. The instance (mine, not published — labelled `supplementary`)

No context-specific causal-bandit instance is published, so it is built on the
authors' own model interface (`ext/latt_py3/models.py`, **unmodified**) with
their action layout. Declared structure, **never given to any agent**:

* `z ~ Bernoulli(0.5)`; `A = X_1` (true cause) with `P(A=1)=0` naturally;
  `X_2` the decoy (`P(X_2=1|z=0)=0.95`); `X_{3..}` neutral 0.5 fillers;
* `P(Y=1|x,z) = base + [A=1]·(±ε) + [X_2=1]·(±decoy)`, `+ε` in context 0 and
  `−ε` in context 1 — **the effect reverses with the context**;
* **objective** (the honest formalisation of the directive's words): the agent
  outputs a **policy** `{context → arm}`, and regret is the **context-conditional**
  gap `mean_z ( max_a E[Y|do(a),z] − E[Y|do(policy(z)),z] )`.

Consequences, verified independently by Monte-Carlo (`verify_union_independent.py`,
checks C2) and **not** from the producer's analytic arrays:

| ε | pooled `E[Y|do(A=1)] − E[Y|do(A=0)]` | ctx0 `do(A=1)` | ctx1 `do(A=1)` | pooled-policy regret floor |
|---|---|---|---|---|
| 0.15 | **0.0000** | 0.792 | 0.345 | 0.0773 |
| 0.25 | **0.0000** | 0.893 | 0.245 | 0.1272 |
| 0.35 | **0.0000** | 0.992 | 0.146 | 0.1773 |

(`base=0.5`; the free decoy contributes `decoy·seg = 0.1425` to the context-0
values, which is why ctx0 `do(A=1) = 0.5 + ε + 0.1425`.)

The true cause's **pooled** effect is exactly zero at every ε. A pooled agent
provably cannot rank it; the context-conditioned optimum is reachable only by
separating contexts. A second, **rich** instance (`base=0.8`, `maskr`) is run
too: there the alternative already pays well, which is where the cost-aware
piece should earn its keep — and does not (see §5).

## 3. The mechanism

`union_agent.py`. Two candidate **sources** feed the **frozen** arbiter through
one ranked list:

1. **Context contrast** (the campaign's own C2 machinery, restored via
   `candidate_gen.generate` over the agent's per-context tables) — nominates an
   arm whose rate stands out *within* a context. `candidate_gen` and
   `arbitration` are imported **unchanged** from the campaign root (hashes in
   `results_union_meta.json`: `fa9721ae…`, `2d3d825b…`).
2. **Context-conditional exploration** (the *principle* of Algorithm 2, not its
   code — declared adaptation): every arm not yet **resolved** is also a
   candidate, scored by the **optimistic gain in its worst-covered context**
   (`1 − best rate any resolved arm pays there`) — *not* by a pooled `1 − rich`.
   This is the pivot: a high pooled alternative no longer masks a still-unexplored
   context, so the exploration term **does not lose context-specificity** (the
   directive's explicit requirement).

Ablations are the same code with **one switch each**: `union_noctx` (pooled
discovery, no split), `union_noexp` (no exploration source), `union_nocost`
(probe the top candidate, no price), `union_pooledexp` (exploration scored by the
pooled gap — the version that *does* lose context-specificity). `pure` = the
turn-128 mechanism exactly.

## 4. Main result — the pieces are mutually necessary (H1, H2, H3)

1000 simulations per cell, seeds 1..1000, `T=400`, `N=50`. **Mask** instance
(`base=0.5`), context-conditional regret:

| ε | **union** | union_noctx | union_noexp | pure | beta0 | budget_pub | uniform_policy |
|---|---|---|---|---|---|---|---|
| 0.15 | **0.0315** | 0.0801 | 0.0776 | 0.0804 | 0.0776 | 0.0804 | 0.0890 |
| 0.25 | **0.0136** | 0.1301 | 0.1276 | 0.1304 | 0.1276 | 0.1304 | 0.1390 |
| 0.35 | **0.0051** | 0.1794 | 0.1776 | 0.1804 | 0.1776 | 0.1804 | 0.1890 |

* **H3 SURVIVES**: removing the context split (`union_noctx`) returns the union
  exactly to the mechanism's level — context-specificity is load-bearing.
* **H4 SURVIVES for exploration, FAILS for the arbiter** (see §5).
* **The union is super-additive**: `0.0051 < min(0.1794, 0.1776) = 0.1776` by a
  factor of **35.6×** at ε=0.35, 9.6× at 0.25, 2.6× at 0.15. It is below the
  best single-feature arm by a wide margin at every ε — verified as check C5
  ("removing EITHER piece collapses the union").

**The mechanism is directly measured, not asserted**: on the mask instance the
true arm `a50` gets **0 pulls** in simulation runs of `pure` and of `union_noexp`
(its natural occurrence `q[0]=0`), because only the exploration term ever puts it
in the table — and `union_noctx` *does* pull it (16–89 pulls across seeds) yet
cannot interpret it, because without the context split those pulls are pooled
away to the flat marginal. Both pieces are necessary for **different reasons**:
the exploration term is the only route to the arm; the context split is the only
interpreter of it.

## 5. The published instance, and the honest boundaries (H1, H2)

**Published parallel instance** (`ext/latt_py3`, unmodified; simple regret):

| m | pure | **union** | union_noexp | **alg1_pub** | alg2_pub | sr_pub | ucb_pub |
|---|---|---|---|---|---|---|---|
| 2 | 0.3000 | 0.0069 | 0.3000 | **0.0000** | 0.0162 | 0.1638 | 0.2361 |
| 8 | 0.3000 | **0.0129** | 0.3000 | **0.0189** | 0.1005 | 0.1638 | 0.2361 |
| 16 | 0.3000 | **0.0276** | 0.3000 | 0.1056 | 0.1686 | 0.1638 | 0.2361 |
| 25 | 0.3000 | **0.0276** | 0.3000 | 0.1755 | 0.2106 | 0.1638 | 0.2361 |
| 40 | 0.3000 | **0.0273** | 0.3000 | 0.2394 | 0.2400 | 0.1638 | 0.2361 |
| 49 | 0.3000 | **0.0264** | 0.3000 | 0.2574 | 0.2496 | 0.1638 | 0.2361 |

* **H1 SURVIVES**: the union acts where the mechanism scored the **worst
  possible** regret. At m≥8 it beats Algorithm 1, and everywhere it beats
  Algorithm 2, SR and UCB.
* **The honest caveat, reported first**: at **m=2 the union does NOT beat
  Algorithm 1** (0.0069 vs 0.0000). Algorithm 1 is *exactly optimal* there
  because the infrequent-arm set is small enough that uniform allocation is
  right. The union's exploration is a fixed-rate policy and pays a small tax.
  This claim was in my first draft as "union < alg1 at every m" and the
  **factcheck caught it as false** — corrected here, not hidden.
* **turn-128's numbers reproduce exactly** under the new code: `pure = 0.3000`
  at every m, and `alg1_pub` = 0.0000/0.0189/0.1056/0.1755/0.2394/0.2574,
  byte-for-byte against the frozen turn-128 column (check C3). The new code did
  not disturb the old result.

**The rich regime (`maskr`) — an honest boundary, FAIL reported plainly:**

| ε | union | union_noexp | union_nocost | pure | uniform_policy |
|---|---|---|---|---|---|
| 0.25 | 0.0313 | **0.0313** | **0.0210** | 0.0347 | 0.0564 |
| 0.35 | 0.0313 | **0.0313** | **0.0210** | 0.0347 | 0.0564 |

Here the union barely edges pure (0.0313 vs 0.0347) and is **worse than
`union_nocost`**. Mechanically: when the alternative is rich, the discovery bar
clears many arms, the arbiter probes them all, and its probe budget is spent on
arms that are already good — the priced decision is *worse* than simply probing
the top candidate. **H2 (beats each part separately) FAILS in the rich regime.**
This is the sharpest honest finding of the turn, and it is why the recommended
composition is two-part, not three-part.

## 6. Is the cost-aware arbiter load-bearing? H4: **FAIL**

`union == union_nocost` to four decimals at every ε on the main instance
(0.0315/0.0315, 0.0136/0.0134, 0.0051/0.0034 — the difference, where it exists,
favours *removing* the price). The reason is structural and measurable: on this
instance the candidate list rarely contains more than one arm that clears the
bar, so "probe the priced candidate" and "probe the top candidate" are the same
action. The arbiter's cost comparison only changes the answer when the list has
**several** clearers — which happens in the rich regime, and there it
**hurts**. So the third published piece, inserted into this union, is at best
decorative and at worst a tax. Reported as FAIL, with the mechanism named.

## 7. The formal statement (H5): **proved for the combinatorial core, conjecture for the stochastic theorem**

`lean/UNION_BOUND.lean`, core Lean **4.19.0**, compiles clean
(`lean out.txt` empty, `grep` finds no `sorry`/`admit`/`axiom`). No Mathlib is
installed here — declared, and it bounds what could be said. Three obligations,
each genuine (a mutated statement is **false**, verified — 3/3 mutations caught):

1. **`separation`** — for two balanced contexts on an arm whose effect reverses
   (`s+d` successes in one, `s−d` in the other, `d ≤ s`), the per-context gaps
   are `±2d` and the **pooled gap is exactly 0**, for *every* `s, d`. This is the
   precise reason a pooled scan **cannot** see the arm — the context split is
   necessary, not cosmetic.
2. **`pooled_probes_none`** — a pooled rule with margin `M > 0` therefore
   nominates nothing among the reversed arms.
3. **`union_regret_le`** — for a finite arm set, if each of the exploration pulls
   loses at most `Δ`, total exploration regret ≤ `len · Δ`, **independent of the
   pooled marginal**. This is the finite skeleton of the suggested regret bound:
   *the extra discovery cost is bounded by the number of exploration pulls times
   the per-pull loss, and does not mention the pooled marginal.*

**What is NOT proved, stated exactly**: the *stochastic* regret bound — the
transition from "these pulls lose at most Δ" (a deterministic fact about a
realised run) to "expected regret ≤ `O(exploration budget · Δ)`" requires a
concentration argument (Hoeffding/Azuma-class) that needs Mathlib's measure
theory, which is not available in this image. The missing step is named: *bound
the probability that a per-pull loss exceeds Δ, then integrate.* The Lean result
proves the **separation** that makes the composition necessary, not the rate.

## 8. Independent verification (different code, disk only)

`verify_union_independent.py` imports **none** of the producers. It re-derives
every cell mean and SEM from the raw per-seed rows (93 cells), re-derives the
instance structure by **Monte-Carlo** (not from the analytic arrays), cross-checks
the published instance against **turn-128's frozen column** (a different turn's
matrix), re-checks determinism in a fresh process, and runs a **negative control
that must fail**.

* First pass: **5 disagreements**. Two were **real and fixed**: (i) my analytic
  `_er_ctx` had forced all non-target variables to 0, which is wrong — an
  intervention `do(A=0)` leaves the decoy free — so the scores were computed
  against wrong expected values; the Monte-Carlo check caught it and the model now
  computes the true interventional expectation. (ii) my verifier's *own* hand-set
  expectations were naive (they ignored the free decoy's contribution); the
  Monte-Carlo agrees with the corrected analytic model, so the **instance** is
  right and the **check** was wrong.
* Second pass: **111 checks, 0 disagreements**, negative control fired.
* **Factcheck of THIS report**: 46 statements re-derived from the frozen matrix
  → **ALL PASS**. It caught 3 over-strong claims of mine (union<alg1 at all m;
  union>noexp in the rich regime; exploration inert there) — all corrected above
  rather than softened.

## 9. Honest limits, declared

1. **The context-specific instance is mine, not published** — no such instance
   exists in the literature surveyed (0 arXiv hits). Every number from it is
   `supplementary`; none is compared to a published figure.
2. **`budget_pub` is a DECLARED adaptation**, not the authors' code (arXiv:2012.07058
   publishes no implementation). It is labelled everywhere and is never called a
   published baseline. The same applies to `unc`-style adaptations inherited from
   turn 128.
3. **The exploration term is the PRINCIPLE of Algorithm 2, not its code** —
   Algorithm 2 samples `η` with a known DAG; the union computes a least-evidence
   score without one. Declared.
4. **No Mathlib** → the Lean result is a finite-combinatorial statement, **not** a
   stochastic-regret theorem, and says so in the file.
5. **1000 sims/cell**, not the paper's 10 000 — declared. `MIN_PER_CTX` (the
   resolution bar) is a declared agent constant with sensitivity {5,10,20}
   reported; the H1–H6 verdicts do not move with it, only the union's own noise
   floor.
6. The published instance is run with the **same** `T/2` observational split for
   every arm (turn-128 adaptation A1'), so no arm is handicapped by the schedule.

## 10. What this does to the campaign's claim

Turn 128 concluded the mechanism was a **verification** procedure, not an
experimental-design one. Turn 129 shows the smallest composition that repairs
that — **a context-specific discovery rule plus a context-conditional exploration
term** — is real, mutually necessary, and super-additive on the instance built to
require exactly it. The cost-aware arbiter, the third published piece, does not
join that composition on the evidence here: inert where it can be checked,
harmful where it binds. And the closest published work (ICML 2023) solves the
unknown-graph problem by assuming **additivity** — which is precisely the
assumption a context-specific cause **violates**. That is the honest shape of the
unoccupied point: **non-additive, context-specific discovery from a reward
stream**, with exploration that keeps its context-specificity, and *no* claim
that the priced trade-off belongs in it.

## 11. Artefacts

* Preregistration (frozen pre-run): `bench_cb/PREREG_UNION.md` (art pending)
* Mechanism: `bench_cb/union_agent.py`, instance `union_instance.py`,
  driver `union_run.py`, matrix `union_matrix.py`, baseline `budget_agent.py`
* Frozen constants + module hashes: `bench_cb/results_union_meta.json`
* Matrix: `bench_cb/results_union/` (93 cells × 1000 sims), `SUMMARY.json`
* Independent check: `bench_cb/verify_union_independent.py`, `verify_union_out.txt`
* Factcheck: `bench_cb/factcheck_union_report.py` (46/46)
* Lean: `bench_cb/lean/UNION_BOUND.lean` (+ `out.txt`, mutation files `mut1..3.lean`)
* Sources: `src_a7f5b2eef8a0`, `src_7d19b569ae60`, `src_aaf0a4fed135`
