# RESULTS — turn 128: the ACTIVE half (C1 + C2) against causal bandits

Owner directive msg_00128. Benchmark, instance and thresholds chosen and frozen
**before** the first run (`PREREG_CB.md`, written before any measurement).
H1–H6 below are exactly the frozen hypotheses, with their measured verdicts.

**Headline: an independent, non-neural area for the active half exists, and it
has published algorithms and published regret bounds — so this angle is not
"unanswerable". And in that area the campaign's mechanism, imported unchanged,
scores the worst possible regret at every difficulty, because it has no way to
reach an arm it has never observed. The failure is upstream of both of its own
claims: the generator never fires (C2) and the arbiter is therefore never
exercised (C1). When a hypothesis is handed to the arbiter directly, C1 works
perfectly — so the failure is not the decision rule, it is that the mechanism
has no exploration term at all.**

---

## 0. The answer to the owner's question, in one paragraph

Causal bandits are the independent, non-neural area the directive asked for:
the field is public (2016→2026), its instances are tabular Bernoulli problems
with no learned encoder anywhere, and it publishes both algorithms and matching
**upper and lower** regret bounds, so a mechanism can be scored against a known
optimum and not only against a rival. I took the canonical instance from the
paper that founded the field (Lattimore, Lattimore & Reid, arXiv:1606.03203),
ran **the authors' own published code** as the comparator, and ported the
campaign's two frozen modules (`candidate_gen.py`, `arbitration.py`, imported
byte-unchanged) onto it. The result is negative and clean: **the mechanism
attains the worst-case regret 0.300 at every `m` tested, while the published
Algorithm 1 attains 0.000–0.257 and even plain UCB attains 0.000–0.236.** The
mechanism does not merely fail to beat published methods; it does not act.

## 1. H1 — an independent non-neural area exists: **SURVIVES**

| candidate | independent of me? | published algorithms | published bounds | neural gate |
|---|---|---|---|---|
| **Causal bandits** (Lattimore, Lattimore & Reid 2016, arXiv:1606.03203) | yes (ANU/Alberta, 2016) | **yes**, and the first author's own implementation is public | **yes** — Theorem 1 upper, Theorem 2 **lower** | **none** |
| Structural causal bandits / POMIS (Lee & Bareinboim, NeurIPS 2018) | yes | yes (own repo, MIT) | yes | none |
| Budgeted causal bandits (Nair, Patil & Sinha, arXiv:2012.07058) | yes | yes | yes | none |
| Causal trees/forests, CN-UCB (Lu, Meisami & Tewari, arXiv:2106.02988) | yes | yes | yes | none |
| CausalWorld / CausalMBRL | yes | yes | — | **neural/vision** (turn 127, unchanged) |

So the answer is **not** "this angle is unanswerable". The active half *can* be
tested outside my worlds, and it is. (The published bound the paper states,
quoted from the fetched PDF: Algorithm 1 attains `O(sqrt(m(q)/T))` while
standard bandit algorithms suffer `Ω(sqrt(N/T))`.)

## 2. The instance and the comparators

The **parallel bandit** of §3 of arXiv:1606.03203, built by the authors' own
`models.Parallel.create(N=50, m, eps=0.3)`: `N=50` binary causes, `K=2N+1=101`
arms, reward depends on `X_1` alone, and `P(X_1=1)=0` for the first `m`
variables — so **the best arm `do(X_1=1)` has literally zero natural
occurrences**, which is the paper's own difficulty parameter `m(q)`.

Comparators are the **authors' published code**, ported Py2→Py3 mechanically
(every edit listed in `ext/PORTS_diff_*.txt`; the unmodified original bytes are
kept in `ext/latt_src/`): `ParallelCausal` (their Algorithm 1), `GeneralCausal`
(Algorithm 2), `SuccessiveRejects`, `AlphaUCB(2)`.

**The port is faithful — checked against a published figure, not against my
hopes.** Their Figure 2a shape reproduces (1000 sims/cell, my run):

| m | alg1_pub | alg2_pub | sr_pub | ucb_pub |
|---|---|---|---|---|
| 2 | 0.0000 | 0.0162 | 0.1638 | 0.2361 |
| 8 | 0.0189 | 0.1005 | 0.1638 | 0.2361 |
| 16 | 0.1056 | 0.1686 | 0.1638 | 0.2361 |
| 25 | 0.1755 | 0.2106 | 0.1638 | 0.2361 |
| 40 | 0.2394 | 0.2400 | 0.1638 | 0.2361 |
| 49 | 0.2574 | 0.2496 | 0.1638 | 0.2361 |

Algorithm 1's regret rises with `m`, Successive Rejects is **exactly flat**
(it ignores the causal structure, so it cannot depend on `m`), and Algorithm 1
crosses below SR between `m=16` and `m=25` — the paper's own stated weakness,
reproduced. If this shape had not reproduced, no comparison below would be
valid.

## 3. H2 — is the ported mechanism competitive? **FAIL, in the strongest form**

1000 simulations per cell, seeds 1..1000, `np.random.seed(seed)` before every
run (applied to all arms equally):

| m | **pure** (the mechanism) | beta0 | perm | unc (declared adaptation) | boot5 (declared adaptation) | **alg1_pub** |
|---|---|---|---|---|---|---|
| 2 | **0.3000** | 0.3000 | 0.3000 | 0.0000 | 0.1029 | **0.0000** |
| 8 | **0.3000** | 0.3000 | 0.3000 | 0.0066 | 0.1035 | **0.0189** |
| 16 | **0.3000** | 0.3000 | 0.3000 | 0.0537 | 0.1035 | **0.1056** |
| 25 | **0.3000** | 0.3000 | 0.3000 | 0.0936 | 0.1035 | **0.1755** |
| 40 | **0.3000** | 0.3000 | 0.3000 | 0.1587 | 0.1035 | **0.2394** |
| 49 | **0.3000** | 0.3000 | 0.3000 | 0.1728 | 0.1035 | **0.2574** |

`0.3000` is not a bad score: it is the **maximum possible** regret on this
instance (`max_a E[Y|a] − min_a E[Y|a] = 0.800 − 0.500`). The mechanism selects
a 0.5-reward arm in **100 % of runs at every m** (`frac_optimal = 0.000`,
`opt_trials = 0.0` in all 6000 runs). It is not "slightly worse than published";
it never acts on the optimum at all.

## 4. Why — the mechanism dies upstream of its own arbiter

The generator's own frozen bar is `MIN_N = 40` trials per candidate. In this
instance the optimal arm is **never observed**, so it can never be nominated.
Measured over the whole grid:

| m | generator calls | empty calls | fraction empty | mean probes | trials on the optimal arm |
|---|---|---|---|---|---|
| 2 | 199 661 | 199 512 | 0.9993 | 0.019 | 0.0 |
| 8 | 199 661 | 199 512 | 0.9993 | 0.019 | 0.0 |
| 16 | 199 700 | 199 554 | 0.9993 | 0.017 | 0.0 |
| 25 | 199 778 | 199 651 | 0.9994 | 0.013 | 0.0 |
| 40 | 199 873 | 199 822 | 0.9997 | 0.008 | 0.0 |
| 49 | 199 965 | 199 942 | 0.9999 | 0.002 | 0.0 |

The generator is silent in **99.9 %** of calls; the arbiter is asked to decide
on an empty list; the agent falls back to the best arm it has already seen,
which is one of the 0.5-reward arms. **C2 (generation) is the failure, and it
takes C1 down with it — C1 was never exercised.**

## 5. Isolating C1 from C2 — the arbiter itself works

Reporting "C1 is refuted" from §4 would be an over-claim, because C1 never ran.
So I injected a correct hypothesis directly into the candidate list (the
campaign's own V7 `INJECT_EDGE` control), with the generator's own score scale:

| mode | m | regret | probes | trials on optimum | optimal selected |
|---|---|---|---|---|---|
| none (frozen) | any | 0.3000 | ~0.0 | 0.0 | 0.000 |
| **inject_true** (beta=1, frozen bar) | 2/8/25/49 | **0.0000** | **10.0** | **200.0** | **1.000** |
| inject_forced (bar removed) | 2/8/25/49 | 0.0000 | 10.0 | 200.0 | 1.000 |

**C1 is not the failure.** Handed one true hypothesis, the frozen arbiter
(beta = 1, unmodified bar) probes it in 100 % of runs and finds the optimum in
100 % of runs — identical to the bar-removed control. The decision rule is
sound. What the mechanism lacks is any way to *obtain* a hypothesis about an arm
it has never pulled.

## 6. What the mechanism lacks, measured three ways

**(a) The floor it must beat.** On the published instance, after the same
observational half:

| policy | m=2 | m=8 | m=25 | m=49 |
|---|---|---|---|---|
| `greedy_half` (best empirical arm, no generation) | 0.3000 | 0.3000 | 0.3000 | 0.3000 |
| `obs_only` | 0.3000 | 0.3000 | 0.3000 | 0.3000 |
| **`pure` (the mechanism)** | **0.3000** | **0.3000** | **0.3000** | **0.3000** |
| `rnd_probe` (uniform-random exploration) | 0.1070 | 0.1070 | 0.1080 | 0.1080 |
| `know_probe` (the optimal arm handed over) | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

The mechanism is **exactly indistinguishable from doing nothing but greedy**.
Every gram of value in this instance comes from exploration, and the mechanism
has none: its only exploration is "probe a candidate", and its candidate bar
requires 40 trials on the arm it would probe.

**(b) The natural-occurrence family.** Keeping the paper's reward structure
intact and varying only `q1 = P(X_1=1)`, the rate at which the optimal arm
occurs naturally:

| q1 | pure | beta0 | unc | ucb | alg1_pub | sr_pub |
|---|---|---|---|---|---|---|
| 0.00 | 0.3000 | 0.3000 | 0.0000 | 0.0000 | 0.0000 | 0.1638 |
| 0.02 | 0.0702 | 0.0702 | 0.0000 | 0.0000 | 0.0000 | 0.1641 |
| 0.05 | 0.0222 | 0.0222 | 0.0000 | 0.0000 | 0.0000 | 0.1636 |
| 0.10 | 0.0033 | 0.0033 | 0.0000 | 0.0000 | 0.0000 | 0.1642 |
| 0.20 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1626 |
| 0.35 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1608 |
| 0.50 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1593 |

The mechanism's regret goes to zero **only where a plain greedy estimator also
reaches zero** (q1 ≥ 0.2), and it is never better than plain UCB anywhere. It
has **no operating region of its own**: there is no cell in this family where
the campaign's mechanism beats the exploration baseline it is supposed to
improve on.

**(c) The supplementary two-parent instance (MINE, not published).** To give the
generator a real, table-visible edge, I built a two-parent instance where
`Y` depends on a strong cause (`X_1`, invisible at `q1=0`) and a weak cause
(`X_2`, always observable, `eps2=0.15`). There the generator *can* fire:

* the weak cause's measured gap is ~0.089 with `z ≈ 2.4` at 200 observational
  pulls — **below the campaign's own `Z_MIN = 4.0` scan bar**, so it needs
  ~500 pulls to clear it (analytic: `z = 4.87` at n=500);
* once it does fire, the arbiter **declines**: `value = 200 × 0.0888 = 17.76`
  against `rhs = rich_rate × 40 + 4 = 29.42`. The weak cause is worth less than
  the alternative the agent is already exploiting. That is not a bug — it is
  the arbiter working as designed;
* and even when it *does* probe (0.48 probes per run, always the weak cause
  `a3`, never the optimum `a2`), regret stays at 0.2270 — **identical to the
  beta = 0 control at every beta from 0 to 50**. The arbiter is measurably
  inert on this instance.

So: the mechanism has no exploration term, its generator's evidence bar is
tuned for a foraging world where every action accumulates trials for free, and
its arbiter is a *comparison*, not a *search*.

## 7. H3–H6

* **H3 (the arbiter is load-bearing): FAIL as stated.** `beta0 == pure` exactly
  at every `m` (0.3000 vs 0.3000) and `perm == pure` exactly — the two frozen
  controls are indistinguishable from the mechanism. They are *supposed* to be
  the controls that prove the arbiter matters; here they prove it does not, in
  this instance, because it never fires. On the supplementary instance,
  `beta0 == pure` at every beta up to 50 as well.
* **H4 (not a re-derivation of the published heuristic): vacuous.** The
  mechanism probes ~0.02 times per run, so there is no probe set to compare
  with Algorithm 1's infrequent-arm set. Reported as unmeasurable, not as a pass.
* **H5 (improves where the paper is weak): FAIL.** The paper's own weakness is
  that its algorithms ignore the reward signal; the mechanism *also* ignores it
  (its arbiter compares against an observed `rich_rate` but never uses the
  reward to decide *which arm to explore*), and it does not improve on
  Algorithm 1 at any `m` — it is worse at every `m`.
* **H6 (prior art): SURVIVES — and it is the finding that matters most.**
  The two things the mechanism is missing are both already published, and both
  are named in the surveyed literature:
  * **the exploration term**: `GeneralCausal` (Algorithm 2 of the same 2016
    paper) already samples the intervention distribution `η` and re-estimates
    the arms with poor observational support — exactly the missing piece, and
    the authors' own code does it;
  * **the cost/benefit comparison against the alternative**: Nair, Patil &
    Sinha (arXiv:2012.07058) study precisely "interventions are more expensive
    than observations" and derive an algorithm that "determines this unknown
    threshold online and successfully manages to trade-off interventions with
    observations" — which is what the arbiter's `rhs` is trying to be, done
    properly and published;
  * **using the reward signal in the sampling policy**: Lu, Meisami & Tewari
    (arXiv:2106.02988) build CN-UCB, which "exploits the reward signal and the
    tree structure to efficiently find the direct cause of the reward" — the
    exact weakness the 2016 paper itself flags for future work, closed by 2021.

  So the arbiter's idea (compare the value of finding out against what you are
  already earning) is a **re-derivation of a published cost-aware trade-off**,
  and the missing exploration is a **published algorithm in the very paper the
  instance came from**. This is the second time in two turns that the campaign's
  mechanism turns out to re-derive something already in print (turn 127:
  Günther et al., NeurIPS 2024).

## 8. Independent verification (different code, disk only)

`verify_cb_independent.py` imports none of the producers; it re-derives every
cell mean from the raw per-seed rows, re-derives the published shape, the
silence fraction, the control ordering and the arbiter arithmetic from the
frozen constants, and runs a **negative control that must fail**.

* First pass: **6 disagreements.** Two were real and are fixed in the report:
  (i) I had asserted `pure == ucb` on the family; that was **wrong** — plain UCB
  is strictly better wherever the optimum is rare, and the corrected claim
  ("the mechanism never beats plain UCB") is the one in §6(b); (ii) the
  determinism check compared the raw JSON including the wall-clock `seconds`
  field, so it reported a spurious disagreement on a genuinely deterministic
  run — the verifier was fixed to strip timing fields.
* Second pass: **190 checks, 0 disagreements**, negative control fired.
* Fresh-process determinism: `pure m=8 seed=1` and `alg1_pub m=8 seed=1` each
  bit-identical across separate processes (sha `64118da4a52b`, `a454f5e5fcae`).

## 9. Everything I was forced to adapt — labelled, not hidden

1. **A1' observational half.** The campaign agent lived in a foraging world
   where every action accumulated trials for free; a best-arm-identification
   bandit has no such phase. The port gets an explicit `T/2` observational half,
   crediting each observed `X_i` to the arm that would have set it — sound in a
   parallel graph and exactly what the authors' own `ParallelCausal` does
   (`xij = hstack((1-x, x, 1))`).
2. **A2** the same `T/2` split the published Algorithm 1 uses, so no arm is
   handicapped by the schedule.
3. **A3** probe block = 20 pulls (declared agent constant; the campaign's own
   `PROBE_MAX_BLOCKS=80` was also a declared agent constant).
4. **A4** re-generation every block, not every step.
5. **A5** the `boot1`/`boot5` arms only: forced pilot pulls of never-tried arms.
   Declared adaptation, labelled as such everywhere; they measure whether the
   mechanism needs a bootstrap, not whether it is superior.
6. **`unc`** is a declared adaptation (the mechanism plus a UCB1 fallback), not
   the campaign mechanism. It exists to measure what the mechanism lacks, and it
   is never called the mechanism in this report.
7. **The supplementary two-parent instance is mine, not published.** Every
   number from it is labelled supplementary and is never compared to a published
   figure.
8. **1000 simulations per cell**, not the paper's 10 000 — declared, not hidden.
9. **The `sqrt(m(q)/T)` diagnostic** is reported as a shape diagnostic only: the
   Θ-constants are unpublished, so no violation of the published bound is
   claimed anywhere in this report.
10. **The Py2→Py3 port** touched `xrange`, `map`, `range`, integer division and
    `scipy.misc.comb` (removed from modern scipy). Every edit is in
    `ext/PORTS_diff_*.txt`; the original bytes are preserved.

## 10. What this does to the campaign's claim

Turn 127 reported that the **epistemic** half transfers as a diagnostic but not
as an advantage. Turn 128 reports that the **active** half, put on the canonical
instance of the field that exists precisely to test it, **does not act at all**:
worst-case regret at every difficulty, because the mechanism has no exploration
term and its generator's evidence bar presumes a world where trials arrive for
free. Its decision rule, isolated, is sound — handed a hypothesis it acts on it
perfectly. Its two missing pieces — exploration, and a proper cost-aware
trade-off — are both published, one of them in the very paper the instance came
from.

The honest summary: the campaign's mechanism is a **verification** procedure,
not an **experimental-design** procedure. It is excellent at deciding whether a
hypothesis it already has is true (V7's C1, re-confirmed here at 100 %), and it
has no machinery for deciding what to look at when it has no hypothesis — which
is the entire problem causal bandits exist to formalise.

## 11. Artefacts

* Preregistration (frozen before the first run): `bench_cb/PREREG_CB.md`
* External code (unmodified): `bench_cb/ext/latt_src/`, tarball sha `17e4584d…`
* Port + every edit: `bench_cb/ext/latt_py3/`, `bench_cb/ext/PORTS_diff_*.txt`
* Frozen constants and module hashes: `bench_cb/results_cb_meta.json`
* Grid (72 cells × 1000 sims): `bench_cb/results_cb/`
* Family (56 cells): `bench_cb/results_cb_family/`
* Isolation, controls, beta sweep, horizon sweep: `bench_cb/results_cb_iso/`
* Independent check: `bench_cb/verify_cb_independent.py`, output `verify_cb_out.txt`
* Source registrations: `src_6a2ee36a7d5d` (1606.03203), `src_0f710f512030`
  (2510.16811), `src_88cb0221447d` (2012.07058), `src_e6e9978c4ec3` (2106.02988)
