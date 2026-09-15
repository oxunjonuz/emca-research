# PREREG — turn 128: causal bandits as the independent, non-neural area for the ACTIVE half

Frozen BEFORE the first measurement run. Owner directive msg_00128.

## 0. What the owner asked

Turn 127 tested the **epistemic half** of the campaign's claim on someone else's
data (Sachs 2005) and reported a negative: the diagnosis transfers, the novelty
and the advantage do not. The owner accepted that and moved the angle:

* find an independent, non-neural area in which the **active** half — C1 (choose
  what to test next / verify-or-exploit) and C2 (generate your own hypothesis)
  together — has published **benchmarks, algorithms, or at least theoretical
  efficiency bounds (regret bounds)** to compare against;
* the named candidate area: **causal bandits** — sequential active choice of
  interventions to find the cause with the fewest trials;
* if the mechanism there is at best level with existing methods, or re-derives
  something published, report that plainly; if no independent non-neural area
  for active experimental design exists at all, say that plainly too.

Turn 127's boundary (§5.1 there) was exactly this: on frozen data C1 and C2
*"cannot be exercised"*. This turn tests whether they can be exercised somewhere
that is not mine.

## 1. Survey (made before choosing; external sources registered)

| candidate | what it is | independent of me? | published algorithms? | published bounds? | neural gate? | verdict |
|---|---|---|---|---|---|---|
| **Causal bandits** (Lattimore, Lattimore & Reid, *Causal Bandits: Learning Good Interventions via Causal Inference*, arXiv:1606.03203, 2016) | sequential design: interventions are arms, reward is a node; simple-regret objective | yes (ANU/Alberta 2016) | **YES** — and the **first author's own published implementation** exists | **YES** — Theorem 1 upper and Theorem 2 **lower** bound | **NONE** — tabular, Bernoulli, no learned encoder | **SELECT** |
| Structural causal bandits / POMIS (Lee & Bareinboim, NeurIPS 2018; repo `sanghack81/SCMMAB-NIPS2018`) | interventions over an SCM, minimal intervention sets | yes | yes (own repo, MIT, tests) | yes, in-paper | none | second comparator, if it runs |
| CausalWorld / CausalMBRL | agentic causal induction | yes | yes | — | **neural/vision gate** (established turn 127) | reject: unchanged |
| offline causal discovery (Sachs 2005) | frozen table | yes | yes | — | none | **reject this turn**: no choice exists in frozen data (turn 127 §5.1) |

Selection rule: the area must let an agent **choose what to intervene on next**,
must be measurable without replacing the mechanism by a neural encoder, and must
carry published numbers. Causal bandits pass all three — this is the first area
in the whole campaign that tests the active half outside my own worlds.

## 2. The published instance (chosen before measuring)

The **parallel bandit** of §3 of arXiv:1606.03203, taken from the first author's
own published code (`finnhacks42/causal_bandits`, fetched this turn as
`ext/latt_code.tar.gz`, sha256 `17e4584d…`; unmodified bytes kept in
`ext/latt_src/`, a mechanical Python-2→3 port in `ext/latt_py3/`, every edit
listed in `ext/PORTS_diff_*.txt`).

* `N = 50` binary causes `X_1..X_N`, all observable; reward `Y ∈ {0,1}`.
* Actions: `do()` (observe) ∪ `{do(X_i=0), do(X_i=1)}` → `K = 2N+1 = 101` arms.
* Reward depends on `X_1` only (unknown to every algorithm):
  `P(Y=1|X_1=1) = 0.5+ε`, `P(Y=1|X_1=0) = 0.5−ε'`, `ε = 0.3`.
* `q_i = P(X_i=1)` = 0 for the first `m` variables, 0.5 otherwise —
  **the promising action `do(X_1=1)` has literally zero natural trials**, which
  is the published paper's own difficulty parameter `m(q)`.
* Published figures use `T = 400`, `10 000` simulations, `m` swept over `2..N`.

**Why this instance is the right container for C1+C2:** here an agent *must*
choose its own sequence of interventions, the best arm can be invisible in any
observational sample, and the paper publishes both an upper and a **lower** bound,
so a mechanism can be scored against a known optimum, not only against a rival.

## 3. Published comparators (their code, not mine)

Run **unmodified from the authors' port**: `ParallelCausal` (their Algorithm 1),
`GeneralCausal(truncate='None')` (Algorithm 2), `SuccessiveRejects`, `AlphaUCB(2)`.
Their published claim, quoted from the fetched PDF: Algorithm 1 attains
`O(sqrt(m(q)/T))` and standard bandit algorithms `Ω(sqrt(N/T))`; Theorem 2 gives
the matching lower bound.

## 4. The mechanism, ported (what exactly is being tested)

The campaign's active half is two modules, and **both are imported unchanged from
the campaign's own frozen files** (`candidate_gen.py`, `arbitration.py` at the
campaign root — the same modules V7 ran, hashes recorded in
`results_cb_meta.json`):

* **C2 — generation** (`candidate_gen.generate_flat`): from its **own** count
  tables only, nominate the (action → effect) pairs where that action's rate for
  that effect stands out against the other actions', with the frozen bars
  `MARGIN=0.08`, `MIN_N=40`, `Z_MIN=4.0`.
* **C1 — arbitration** (`arbitration.plan`): probe iff
  `beta·GAIN_UNIT·score > rich_rate·H + PROBE_COST`, with the frozen constants
  `GAIN_UNIT=200`, `H=40`, `PROBE_COST=4`, and `rich_rate` = the payoff the agent
  **observes** the best alternative to pay.

Both modules are **world-agnostic**; nothing is edited to suit the bandit.
Declared adaptations (each one is a place the port is weaker, not stronger):

* **A1** — a bandit has one effect (`Y=1`) and no exogenous context variable, so
  the generator's context machinery degenerates to its pooled branch
  (`generate_flat`). The campaign's context contrast has no bandit counterpart
  and is **not** exercised this turn.
* **A2** — the campaign's agent lived in a world it was *foraging* in, so every
  action accumulated trials for free. A best-arm-identification bandit has no
  foraging phase; the port gets one explicit observational half (`T/2` pulls of
  `do()`), the same budget split the published Algorithm 1 uses, so nobody is
  handicapped by the split.
* **A3** — probe block size is a declared agent constant `PROBE_BLOCK = 20` pulls
  (the campaign's own constant was `PROBE_MAX_BLOCKS=80`, also a declared agent
  constant; the block is re-declared here for a 400-step horizon).
* **A4** — the generator is re-run only every `PROBE_BLOCK` pulls, not per step
  (its own `MIN_N=40` bar makes per-step re-generation meaningless).

## 5. Arms

| arm | what it is |
|---|---|
| `mine_pure` | **the campaign mechanism**: `candidate_gen` + `arbitration`, imported unchanged |
| `mine_beta0` | same, `beta=0` — the frozen negative control: it may never probe |
| `mine_perm` | same, candidate scores permuted (frozen seed) — the "is the decision computed or scheduled" control |
| `mine_unc` | **declared adaptation, NOT the campaign mechanism**: `mine_pure` plus a standard published-style exploration rule (pull the arm with the widest one-sided CI when the generator is silent). It exists to measure *what the mechanism lacks*, and is labelled as an adaptation everywhere it appears. |
| `alg1_pub`, `alg2_pub`, `sr_pub`, `ucb_pub` | the authors' unmodified implementations |

## 6. Frozen hypotheses and falsifiers

* **H1 (an independent non-neural area for the active half exists).**
  *Falsified if* no published algorithm **and** no published bound is found for
  sequential causal experimental design without a neural component.
* **H2 (the ported mechanism is competitive on the published instance).**
  *Falsified if* `mine_pure`'s mean simple regret exceeds the best published
  arm's by more than 3 combined standard errors at **every** `m` tested.
* **H3 (the reward-aware arbiter is load-bearing).** *Falsified if*
  `mine_beta0` ≥ `mine_pure` (the arbiter buys nothing) or if `mine_perm` equals
  `mine_pure` (the decision is scheduled, not computed).
* **H4 (the mechanism does not merely re-derive the published heuristic).**
  *Falsified if* the set of arms `mine_pure` probes coincides with the published
  Algorithm 1's "infrequent arms" set in ≥90 % of runs.
* **H5 (the mechanism improves where the paper says its own algorithm is weak).**
  The paper's own stated weakness (§6, quoted): "our algorithms completely ignore
  the reward signal when developing their arm sampling policies", and it shows
  Algorithm 1 losing to Successive Rejects as `m` grows. *Falsified if* `mine_pure`
  shows no relative gain over `alg1_pub` at large `m`.
* **H6 (prior art).** A published causal-bandit algorithm that already uses the
  reward signal (or an explicit intervention/budget cost) for its sampling policy
  exists. *Falsified if* none is found in the surveyed literature.

## 7. Frozen procedure

* Instance construction via the authors' own `models.Parallel.create(N, m, eps)`.
* `N=50`, `ε=0.3`, `T=400`, `m ∈ {2,4,8,16,25,40,49}`, simulations per cell
  **1000** (declared; the paper used 10 000 — the difference is declared, not
  hidden), seeds `1..1000` per cell, `np.random.seed(seed)` before every run
  (the authors' code uses the global NumPy RNG; seeding it per run is the only
  reproducibility edit and it is applied to all arms equally).
* Statistic: **simple regret** `= max_a E[Y|a] − E[Y|â]`, exactly the authors'
  definition, computed by their own `expected_rewards` array.
* Faithfulness check (independent path, §8): re-run the published Figure 2a
  configuration with the published arms only and check the **published shape**
  reproduces — Algorithm 1's regret rises with `m`, Successive Rejects stays flat.
  If the shape does not reproduce, the port is wrong and no comparison is valid.
* Scale-free diagnostic: measured regret divided by the claimed lower-bound shape
  `sqrt(m(q)/T)`. The Θ-constants are unpublished, so this is a diagnostic,
  **not** a violation test — reported as such, never as "proved suboptimal".

## 8. What will be reported regardless of outcome

Every arm's regret per `m` with its error bars; the fraction of runs in which the
generator produced **no candidate at all** (the bootstrap question); the share of
runs that selected the truly best arm; the comparator arms' measured numbers next
to the published shape; every adaptation A1–A4 restated; and, in its own section
and ahead of any comparison, any **published work that already does what the port
does** (this is where turn 127's NeurIPS-2024 finding belonged).
