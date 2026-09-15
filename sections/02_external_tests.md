# Section 02 — External tests: the honest re-assessment of scientific novelty

*The owner asked for a "честная переоценка научной новизны, с точными ссылками на
найденную предшествующую литературу". This section is that, and nothing else. Every
number is quoted from the frozen reports in `../reports/` and `../external/`.*

---

## 0. The finding, stated first

**The campaign's central insight is already published, and the mechanism does not
transfer into an advantage.** Three external tests were run, each preregistered
before its first measurement:

1. **Sachs 2005** (real-world causal-discovery benchmark) — the epistemic half
   transfers as a **diagnostic**, not as an **advantage**.
2. **Causal bandits** (Lattimore, Lattimore & Reid 2016) — the active half, put on
   the canonical instance of the field that exists to test it, **does not act at
   all**: worst-case regret at every difficulty.
3. **The union mechanism** (context-specificity + exploration + cost-aware
   arbitration) — the two-part union is real, mutually necessary and
   super-additive on an instance built to require it; the third published piece,
   the cost-aware arbiter, does not earn its place.

---

## 1. Prior art found — the campaign's central insight predates the campaign

**Günther, Popescu, Rabel, Ninad, Gerhardus, Runge, "Causal discovery with
endogenous context variables", NeurIPS 37 (2024), arXiv:2412.04981** — submitted
6 Dec 2024, i.e. **before** this campaign (v1–v8 ran 2026-09). Registered source
`src_3a8d4bcdbff5`. Quoted fragment:

> "We show that naive approaches such as learning different regime graphs on
> masked data, or pooling all data, can lead to uninformative results."

That is the campaign's central result — `../reports/CAMPAIGN_RESULT.md` §2.1, the
headline claim that pooling destroys context-exclusive structure — stated as a
known result in the causal-discovery literature, with a soundness proof for an
adaptive constraint-based algorithm and numerical comparisons against baselines.
The same paper names **both** failure modes the campaign measured (per-regime
graphs on masked data, and pooling).

**Consequence for the campaign's claim, in the report's own words:** the
stratified-contrast mechanism is a **re-derivation of a published idea**, not a new
one, and the campaign's six worlds cannot establish novelty that already existed in
print. The words used for it in earlier turns ("the line's central, self-contained
result") were true about the line and **too strong about the world**.

---

## 2. External test A — Sachs 2005 (the epistemic half)

**Benchmark:** Sachs et al., *Science* 2005 — 11 phosphoproteins, a validated
golden-standard DAG published in 2005, and real intervention indicator columns.
External file `external/bench_ext/ds/sachs.experimental.mixed.txt`
(sha256 `c1c4b12b…`, 7466 rows) carries **nine indicator columns** naming which
stimulus/inhibitor was applied to that cell. Mean 1.67 indicators per row — a
genuine **context variable** someone else designed, fifteen years before this
campaign.

**Procedure frozen before any run** (`external/bench_ext/PREREG_BENCH.md` §4):
Spearman/Fisher-z; pooled decision at α = 0.05; stratum decision as Bonferroni over
strata with n ≥ 50; permutation null (200 replicates, seed 20260912).

| hyp | claim | verdict | measured |
|---|---|---|---|
| H1 | pooled marginal sees only a minority of true edges | **FAIL** | pooled recall **0.95** (19/20) |
| H2 | context-exclusive true edges exist here | **FAIL** | **0** such pairs |
| H3 | context-exclusive pairs are enriched for truth | **FAIL** | enrichment undefined (0 pairs) |
| H4 | agentic half has no non-neural external benchmark | **SURVIVES** | CausalWorld and CausalMBRL both gate on a neural encoder |

**Why H1/H2 failed is the finding.** In the campaign's own worlds, masked edges
were built — relations true inside a context whose pooled marginal is structurally
below threshold. Sachs 2005 has almost none: 54 of 55 pairs are marginally
associated. The benchmark's difficulty is not masking; it is the opposite — **a
pooled marginal here is not blind, it is indiscriminate.** That is a different
failure mode, and it is the one the campaign never faced.

**The mirror-image form does transfer.** Reading the principle as "context is
information, the pool is not enough", three arms on the external data with external
ground truth:

| arm | selection rule | tp | fp | fn | precision | recall |
|---|---|---|---|---|---|---|
| A | pooled marginal | 19 | 35 | 1 | 0.352 | 0.950 |
| B | all strata agree | 3 | 0 | 17 | 1.000 | 0.150 |
| C | unpolluted context confirms | 8 | 1 | 12 | 0.889 | 0.400 |

Precision 0.352 → 0.889 is Fisher **p = 0.0013** (vs gt17). **34 of arm A's 35
false positives are dropped by requiring the unpolluted context to confirm.**

**Head-to-head with published methods** (external implementations: pgmpy PC,
PC-chi², HillClimbSearch; plus published bnlearn numbers for Sachs):

| method / arm | tp | fp | fn | precision | recall |
|---|---|---|---|---|---|
| **PUBLISHED bnlearn inter.iamb** (test='cor') | 8 | 0 | 9 | **1.000** | 0.471 |
| **MINE arm C** (pooled + context confirm) | 8 | 1 | 9 | 0.889 | 0.471 |
| **MINE arm B** (all strata agree) | 3 | 0 | 14 | 1.000 | 0.176 |
| **MINE arm A** (naive pooled) | 16 | 38 | 1 | 0.296 | 0.941 |
| **pgmpy PC** (pearsonr) | 6 | 3 | 11 | 0.667 | 0.353 |
| **pgmpy PC** (chi², q3) | 13 | 11 | 4 | 0.542 | 0.765 |
| **pgmpy HillClimb** (bic-g) | 15 | 20 | 2 | 0.429 | 0.882 |
| **PUBLISHED bnlearn mbde** (intervention-aware) | 17 | 8 | 0 | 0.680 | **1.000** |

**Verdict, in the report's words:** at matched recall the ported arm C **does not
beat the published baseline — it ties it.** Both recover the same 8 of 17 arcs and
both miss 9. The published intervention-aware method (mbde, recall 1.000) is far
ahead of everything produced, and it got there using the same intervention columns.
**The principle transfers; the advantage does not.**

---

## 3. External test B — causal bandits (the active half)

**Benchmark:** the parallel bandit of §3 of **Lattimore, Lattimore & Reid,
"Causal Bandits: Learning Good Interventions via Causal Inference", NeurIPS 2016,
arXiv:1606.03203**. Instance built by the authors' own published code
(`models.Parallel.create(N=50, m, eps=0.3)`): N = 50 binary causes, K = 2N+1 = 101
arms, reward depends on X₁ alone, and P(X₁=1) = 0 for the first m variables — so
**the best arm `do(X₁=1)` has literally zero natural occurrences**, the paper's own
difficulty parameter m(q). The authors' published code was ported Py2→Py3
mechanically (every edit in `external/bench_cb/ext/PORTS_diff_*.txt`; original
bytes kept in `ext/latt_src/`).

**The port is faithful — checked against a published figure, not against hopes.**
Algorithm 1's regret rises with m, Successive Rejects is exactly flat, and
Algorithm 1 crosses below SR between m = 16 and m = 25 — the paper's own stated
weakness, reproduced.

**Result: the campaign's mechanism imported unchanged scores the worst possible
regret at every difficulty.**

| m | **pure** (the mechanism) | beta0 | perm | **alg1_pub** |
|---|---|---|---|---|
| 2 | **0.3000** | 0.3000 | 0.3000 | **0.0000** |
| 8 | **0.3000** | 0.3000 | 0.3000 | **0.0189** |
| 16 | **0.3000** | 0.3000 | 0.3000 | **0.1056** |
| 25 | **0.3000** | 0.3000 | 0.3000 | **0.1755** |
| 40 | **0.3000** | 0.3000 | 0.3000 | **0.2394** |
| 49 | **0.3000** | 0.3000 | 0.3000 | **0.2574** |

`0.3000` is not a bad score: it is the **maximum possible** regret on this instance
(`max_a E[Y|a] − min_a E[Y|a] = 0.800 − 0.500`). The mechanism selects a 0.5-reward
arm in **100 % of runs at every m**. It is not "slightly worse than published"; it
**never acts on the optimum at all**.

**Why — the mechanism dies upstream of its own arbiter.** The generator's own
frozen bar is `MIN_N = 40` trials per candidate. In this instance the optimal arm
is **never observed**, so it can never be nominated. The generator is silent in
**99.9 %** of calls; the arbiter is asked to decide on an empty list. **C2
(generation) is the failure, and it takes C1 down with it — C1 was never
exercised.** Isolated from C2 (a correct hypothesis injected directly, the
campaign's own V7 `INJECT_EDGE` control): regret **0.0000**, probes 10.0, trials on
optimum 200.0, optimal selected 1.000. **The decision rule is sound.**

**What the mechanism lacks, measured three ways:** (a) it is exactly
indistinguishable from doing nothing but greedy (`greedy_half` = `pure` = 0.3000);
(b) its regret goes to zero only where a plain greedy estimator also reaches zero
(q₁ ≥ 0.2), and it is never better than plain UCB anywhere — **no operating region
of its own**; (c) on a supplementary two-parent instance the generator *can* fire
but the arbiter declines (the weak cause is worth less than the alternative already
being exploited — the arbiter working as designed).

**Prior art (H6 SURVIVES, and it matters most).** Both missing pieces are already
published:
* the **exploration term** — `GeneralCausal` (Algorithm 2 of the same 2016 paper)
  already samples the intervention distribution η and re-estimates poorly-supported
  arms;
* the **cost/benefit comparison** — **Nair, Patil & Sinha, arXiv:2012.07058** study
  precisely "interventions are more expensive than observations" and derive an
  algorithm that "determines this unknown threshold online and successfully manages
  to trade-off interventions with observations";
* **using the reward signal in the sampling policy** — **Lu, Meisami & Tewari,
  arXiv:2106.02988** build CN-UCB, which "exploits the reward signal and the tree
  structure to efficiently find the direct cause of the reward".

**Honest summary:** the campaign's mechanism is a **verification** procedure, not
an **experimental-design** procedure. It is excellent at deciding whether a
hypothesis it already has is true (V7's C1, re-confirmed here at 100 %), and it has
no machinery for deciding what to look at when it has no hypothesis — which is the
entire problem causal bandits exist to formalise.

---

## 4. External test C — the union mechanism

**Directive:** combine context-specificity + exploration + cost-aware arbitration
and test whether the composition occupies an unoccupied point.

**Prior art, stated ahead of every comparison:**

| work | what it does | does it occupy the point? |
|---|---|---|
| Lattimore, Lattimore & Reid 2016 (arXiv:1606.03203) | the instance; Algorithm 1/2 | exploration is Algorithm 2, which assumes a **known DAG** |
| Nair, Patil & Sinha (arXiv:2012.07058) | cost-aware observation/intervention trade-off | pricing idea; assumes a **known structure** |
| Lu, Meisami & Tewari 2021 (arXiv:2106.02988) | CN-UCB: reward signal drives sampling | **known** tree structure |
| **Malek, Aglietti & Chiappa, "Additive Causal Bandits with Unknown Graph", ICML 2023, arXiv:2306.07858** | **unknown graph**, but **additive** outcome | **CLOSEST** — unknown structure, yet it *requires additivity* |
| Song, Rini & Xu 2021 (arXiv:2103.04215) | hierarchical/contextual causal bandit | context is exogenous/given |
| Elahi, Kocaoglu & Ghasemi 2026 (arXiv:2607.15577) | contextual causal bandits, non-manipulable variables | **known** graph |

**The honest verdict.** The exact three-way union is not published as one mechanism
(arXiv `"causal bandit" AND "context-specific"` → **0 results**). But the neighbour
is close and must be named: **ICML 2023 already solves unknown-graph causal bandits
by ASSUMING ADDITIVITY.** The campaign's context-specific instance is precisely an
**additivity violation** — the effect of X₁ depends on the context Z. So the
unoccupied point, stated precisely, is:

> **a mechanism that discovers a NON-ADDITIVE, context-specific cause from its own
> reward stream, with no DAG and no structural assumption, and prices its own
> exploration.**

That is a **composition** claim, not a first-in-field claim.

**Result on the published instance** (simple regret, 1000 sims/cell):

| m | pure | **union** | union_noexp | **alg1_pub** | alg2_pub | sr_pub | ucb_pub |
|---|---|---|---|---|---|---|---|
| 2 | 0.3000 | 0.0069 | 0.3000 | **0.0000** | 0.0162 | 0.1638 | 0.2361 |
| 8 | 0.3000 | **0.0129** | 0.3000 | 0.0189 | 0.1005 | 0.1638 | 0.2361 |
| 16 | 0.3000 | **0.0276** | 0.3000 | 0.1056 | 0.1686 | 0.1638 | 0.2361 |
| 49 | 0.3000 | **0.0264** | 0.3000 | 0.2574 | 0.2496 | 0.1638 | 0.2361 |

The union acts where the mechanism scored the worst possible regret; at m ≥ 8 it
beats Algorithm 1. **The honest caveat, reported first: at m = 2 the union does NOT
beat Algorithm 1** (0.0069 vs 0.0000) — Algorithm 1 is exactly optimal there. This
claim was in the first draft as "union < alg1 at every m" and the **factcheck caught
it as false**.

**On the context-specific instance** (the campaign's own, labelled `supplementary`
— no such published instance exists), the two parts are **mutually necessary and
super-additive**: together they cut regret to **0.0051** where the mechanism alone
scores **0.1804**, and removing *either* piece collapses it back (**0.1794** /
**0.1776**).

**The third part does not earn its place.** The cost-aware arbitration is inert on
the main instance (`union == union_nocost` to four decimals) and
**counterproductive** in the rich regime (0.0313 vs 0.0210). The honest unoccupied
point is a **two-part union**, not the three-part one the directive proposed.

---

## 5. What the external tests do to the campaign's claim

* Turn 127: the **epistemic** half transfers as a diagnostic but not as an
  advantage.
* Turn 128: the **active** half, put on the canonical instance of the field that
  exists precisely to test it, **does not act at all**.
* Turn 129: the smallest composition that repairs that — context-specific discovery
  + context-conditional exploration — is real, mutually necessary and
  super-additive; the priced arbiter is not part of it.
* **The campaign's central insight is published prior art (NeurIPS 2024).**

Nothing in this section supports a claim that the campaign's mechanism is superior
to established causal discovery. It supports a weaker, honest claim: a specific
*failure mode* of pooled analysis (34/35 false positives are context-unstable) is
real and detectable outside the campaign's own worlds.

---

## 6. Artefacts for this section

* Sachs test: `../external/bench_ext/PREREG_BENCH.md`, `RESULTS_BENCH.md`,
  data in `../external/bench_ext/ds/`, measurement `bench_transfer.py`,
  `bench_transfer2.py`, `run_published_methods.py`, `reproduce_published.py`,
  `compare_published.py`, `headtohead.py`, independent check
  `verify_bench_independent.py`
* Causal-bandit test: `../external/bench_cb/PREREG_CB.md`, `RESULTS_CB.md`,
  ported published code `../external/bench_cb/ext/latt_src/` and `latt_py3/`,
  matrices `../external/bench_cb/results_cb/`, `results_cb_family/`,
  `results_cb_iso/`, independent check `verify_cb_independent.py`
* Union test: `../external/bench_cb/PREREG_UNION.md`, `RESULTS_UNION.md`,
  mechanism `union_agent.py`, instance `union_instance.py`, matrix
  `../external/bench_cb/results_union/`, independent check
  `verify_union_independent.py`, factcheck `factcheck_union_report.py`
* Registered sources: `src_3a8d4bcdbff5` (Günther et al., NeurIPS 2024),
  `src_6a2ee36a7d5d` (arXiv:1606.03203), `src_88cb0221447d` (arXiv:2012.07058),
  `src_e6e9978c4ec3` (arXiv:2106.02988), `src_aaf0a4fed135` (arXiv:2306.07858),
  `src_a7f5b2eef8a0` (arXiv:2103.04215), `src_7d19b569ae60` (arXiv:2607.15577),
  `src_e8ed2b143798` (bnlearn Sachs HOWTO, published numbers),
  `src_2e2fe669f2ec` (CausalWorld), `src_3438679a32ca`/`src_fb0bcfcaba94`/
  `src_ae0f06b05339` (CausalMBRL)