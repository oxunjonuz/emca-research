# PREREG — turn 129: the UNION mechanism (context-specificity + exploration + cost-aware arbitration)

Frozen BEFORE the first measurement run of this turn. Owner directive msg_00129.
Line: `bench_cb/` (turn 128). Nothing below the constants in section 3 exists on
disk at freeze time.

## 0. What the owner asked (verbatim intent)

Take the two published pieces found in turn 128 — the exploration term
(Algorithm 2 of Lattimore, Lattimore & Reid, arXiv:1606.03203) and the
cost-aware observation/intervention trade-off (Nair, Patil & Sinha,
arXiv:2012.07058) — **not as a solution to copy, but as material**. Build them
INTO the campaign mechanism C2 so that the union does not lose what already
works (context-specificity, the one thing the campaign proved across six
worlds), and re-run on the same hard causal-bandit instance where the mechanism
now scores 0.300 (= worst possible).

If the union beats Algorithm 1 and the cost-aware methods *taken separately* —
that is a real unoccupied point. If the owner's suggested formal claim can be
stated and proved ("a regret bound for the case where the true cause has a
context-specific, not pooled, effect, and must still be *discovered*"), attempt
it in Lean 4. **If the union gives nothing over the sum of its parts, say so
plainly.**

## 1. The point of the union — why the pieces are not the same piece

The two published pieces cannot be executed by a mechanism unless it can also
do something neither of them does:

* Algorithm 2 (exploration) **assumes** it is handed the DAG (paper: "given a
  causal DAG"). Its exploration is an *arm-design* question once you know the
  structure.
* The cost-aware trade-off (arXiv:2012.07058) **assumes** a known causal
  structure — its whole purpose is choosing *which known-variable* to intervene
  on.
* The campaign mechanism **discovers** the (action→effect) association from its
  own reward stream, world-agnostically, with no DAG. It is the only piece that
  can run on an instance whose structure nobody supplied.

So the union is: **discover the effect set without a DAG → find, among the many
arms the pooled discovery cannot see, which one actually pays, when pooling is
the *reason* it is invisible → stop exploring when the evidence says stop,
priced against what you are already earning.**

The pooled instance of turn 128 has no such arms (a single parent's effect is
what pooling sees perfectly). The union must be tested where a context-specific
effect exists and pooling destroys it. That is the instance of section 2.

## 2. Instances (frozen)

### 2a. MASK-CB — a context-specific causal bandit built on a published instance
Built from the **authors' own published model** (`ext/latt_py3`, unmodified):
`ParallelConfounded`-style structure is not used; instead a specific, declared
family is constructed in `union_instance.py`, with the reward structure fixed to
the published `epsilon = 0.3` and the causal graph known to the harness but
**never given to any agent**:

* `Z ~ Bernoulli(pZ)` — a context variable that **sets the action's meaning**.
* `X_1` is set by intervention; reward depends on `X_1 **and on Z**`:
  `P(Y=1 | X_1=1, Z=0) = 0.5 + ε`, `P(Y=1 | X_1=1, Z=1) = 0.5 − ε'`,
  `P(Y=1 | X_1=0, ·) = 0.5 − ε'`. That is: **the true cause `do(X_1=1)` pays in
  one context and is neutral-or-worse in the other.** Pooled over Z, the
  marginal effect shrinks toward zero and a pooled estimator ranks it ~0.5,
  i.e. blind exactly the way the six campaign worlds established.
* `X_2..X_N` have `P(X_i=1) = 0.5` natural occurrence (the non-rare filler
  causes), so the pooled table is dominated by arms whose gaps are pure
  context-merging artifacts.
* Actions: `do()` ∪ `{do(X_i=v)}` → `K = 2N+1` (the authors' own layout).
* `N = 50`. At least `m_last` of the rare-cause structure kept so the optimal
  arm has rare natural occurrence (the published difficulty parameter), swept
  together with a **context-reversal sweep** `ε' ∈ {0, 0.15, 0.3}` (how badly
  the true arm pays in the wrong context).

The measured quantity is **simple regret against the context-appropriate
optimum**, exactly as the authors define it: the optimum is
`max_a E[Y | do(a)]` averaged over Z, so an agent that only knows the pooled
average with Z=0.5 cannot reach the optimum by luck; the true arm wins only in
one context, and the harness reports regret, not arm identity.

### 2b. The published instance (turn-128 container), unchanged
`models.Parallel.create(N=50, m, eps=0.3)` from the authors' port, `T=400`,
`m ∈ {2,8,16,25,40,49}`, to test that the union's exploration term does not lose
what the mechanism does not have — and that it beats the parts here too.

## 3. Frozen constants (never moved after any run)

* UNI: `MIN_N=40`, `MARGIN=0.08`, `Z_MIN=4.0` — **candidate_gen's own frozen bars, unchanged**.
* arbiter: `GAIN_UNIT=200`, `H=40`, `PROBE_COST=4` — **arbitration's own frozen constants, unchanged**.
* UNION exploration seeds: the union's exploration budget is **one declared arm
  parameter `E0`** (unknown-arm pulls at the start of the active half), `E0 ∈
  {0, 20, 50}` — `E0=0` reproduces the turn-128 mechanism exactly.
* `T=400`, `N=50`, `ε=0.3`, `1000` sims/cell, seeds 1..1000, `np.random.seed(seed)` before every run.
* Context instance: `pZ = 0.5`, `N=50`, `T=400`.

## 4. Mechanism (what exactly is built)

`union_agent.py`. The union = **three frozen parts + one new term + one new
switch**:

1. **(C2, unchanged)** `candidate_gen.generate_flat` over the agent's OWN
   tables, world-agnostic. Nothing edited.
2. **(NEW: context split — the campaign's claim, restored)** the agent also
   maintains a table keyed by the observed context value `z` it sees on its
   `do()` pulls, and runs the generator in **each context separately** as well
   as pooled. This is the exact machinery `candidate_gen.generate(ctx_table,…)`
   already has (the campaign's own context contrast), which the turn-128 port
   had to drop because the published instance had no context. It is restored,
   not invented.
3. **(NEW: exploration term, from Algorithm 2's *idea*, not its code)** when the
   discovery yields no candidate, the agent pulls its **least-observed** arm
   instead of falling back to greedy — the decision *which* arm is
   "least-observed" is computed from its own tables. Declared as an adaptation:
   Algorithm 2 samples `η`, it does not do round-robin least-observed; the union
   uses the *principle* (re-estimate arms with poor observational support) with
   a mechanism the agent can actually compute without the DAG.
4. **(C1, unchanged)** `arbitration.plan` decides verify-vs-exploit with its own
   frozen constants. **A discovered-but-unobserved arm can now enter the
   candidate list without 40 trials, because the context contrast is carried by
   the context the agent already observed** — this is the pivot that makes C1
   fire on the bandit at all.
5. **(NEW: discovered-arm bootstrap)** the union probes the *top-scoring*
   candidate for a declared block `PROBE_BLOCK=20` (the campaign's own declared
   constant), then re-discovers.

## 5. Arms (frozen)

| arm | what it is |
|---|---|
| `pure` | the campaign mechanism exactly as turn 128 froze it (reproduce 0.300) |
| `alg1_pub`, `alg2_pub`, `sr_pub`, `ucb_pub` | the authors' published code, unchanged (turn-128 port) |
| `budget_pub`-style | the cost-aware trade-off, taken **by itself**: a declared implementation of the arXiv:2012.07058 principle on THIS instance (intervene-vs-observe priced against the observed reward) — labelled adaptation, never the union |
| `union` | parts 1–5 above |
| `union_noexp` | the union **with the exploration term removed** (context split + arbiter only) — isolates what the exploration term adds |
| `union_noctx` | the union **with the context split removed** (exploration + arbiter, pooled only) — isolates what context-specificity adds |
| `union_nocost` | the union **with the cost-aware arbiter replaced by a fixed probe budget** — isolates what the trade-off adds |

The last three arms are the whole point: they let me say whether the union is
**more than the sum of its parts** or **exactly the sum**. If
`union == max(parts)` and the interaction term is zero, the honest report is
"nothing over the sum", and the owner said to say it.

## 6. Frozen hypotheses and falsifiers

* **H1 (the union acts on the reported hard instance).** *Falsified if*
  `union`'s mean regret on 2b does not beat `pure`'s 0.3000 by more than 3
  combined standard errors at **every** `m` tested.
* **H2 (the union beats each part separately — the unoccupied point).**
  *Falsified if* `union` is ≤ `max(union_noexp, union_noctx, union_nocost,
  alg1_pub, alg2_pub, budget_pub)` at every context-reversal level on 2a.
  **This is the owner's actual question.**
* **H3 (the context-specificity is load-bearing, not decoration).**
  *Falsified if* `union == union_noctx` on 2a (context split buys nothing) or if
  the pooled discovery nominates the context-exclusive arm nearly as often as
  the context split does.
* **H4 (the trade-off is load-bearing).** *Falsified if* `union == union_nocost`
  on 2a (a fixed probe budget does as well as the priced decision).
* **H5 (the formal claim is true).** Statement frozen in section 7; *falsified
  if* a Lean 4 proof is not produced. If no proof is produced, the statement is
  reported as **conjecture**, not theorem, and the informal argument is stated
  with its exact missing step.
* **H6 (prior art — reported FIRST, ahead of every comparison).** Any published
  work that already unifies context-specific discovery + exploration +
  cost-aware intervention choice in one bandit mechanism. *Falsified if* such a
  work is found and named. Partial matches found before this run are registered
  as sources and listed in the report ahead of the comparison.

## 7. The formal statement to attempt (frozen now, proved or not)

Informal: *consider a causal bandit whose true cause has a context-specific
effect, so that pooled estimation cannot separate it; suppose the agent runs
discovery (which nominates candidates from its own observation tables), an
exploration rule (which bounds the number of pulls on any arm before it is
considered observed), and a priced arbitration (which probes iff the value of a
gap exceeds what the alternative pays). Then the regret suffered on the
context-specific cause is bounded by the exploration floor, and the extra
discovery cost is bounded by the number of exploration pulls times the per-pull
loss, independent of the pooled marginal.*

The **Lean 4** fragment that can actually be closed in core Lean 4.19 (no
Mathlib is installed — declared) is a finite combinatorial lemma, not the
stochastic statement:

> `union_regret_le` — for a finite arm set, if exactly `e` arms are explored
> outside the "already-earning" set and each such pull costs at most `Δ`, and
> every non-explored arm is dominated by the earning arm, then total regret ≤
> `e·Δ`. Plus the **separation lemma**: if a cause's effect in context `z` has
> gap `g_z > 0` in a subset of contexts of total mass `π`, and equals `−g_z`
> elsewhere with the same mass, then the pooled gap is exactly `0` while the
> best context gap is `g_z` — i.e. the union's context split sees a signal the
> pooled scan provably cannot.

Both are finite arithmetic over `Nat`/rational expressions; the proof obligation
is genuine (the second is the whole argument that context-splitting is
necessary, not cosmetic).

## 8. What will be reported regardless of outcome

Every arm's regret with error bars per instance and per reversal level; the
fraction of runs in which discovery produced no candidate; the fraction in which
the union selected the true arm; the three ablation arms' numbers next to the
union's, **so "more than the sum" is a measured quantity, not a claim**; the
exact state of the Lean statement (proved / unproved + the missing step); and,
ahead of every comparison, the prior art.

## 9. Honest limits declared now

* No Mathlib → the Lean result is a finite-combinatorial lemma, NOT a
  stochastic-regret theorem, and will say so.
* The context instance is **mine, not published** (no "masked causal bandit"
  instance is published — the survey found 0 arXiv hits for
  `"causal bandits" AND "masked"`). Every number from it is labelled
  `supplementary`.
* The cost-aware arm `budget_pub` is a **declared adaptation** of the
  arXiv:2012.07058 principle to this instance, not their code (their code is not
  public); it is labelled everywhere and never called a published baseline.
* `T=400`, `1000` sims/cell (the paper used 10 000 for the figure) — declared.
