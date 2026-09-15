# RESULTS_STOPPING.md — turn 134

**A stopping rule of a different type, built and measured.**

Owner directive **msg_00134**: *"the next, genuinely interesting step is not to
tune the current price, but to design a fundamentally different type of stopping
rule, not based on directly comparing quantities incommensurable by nature
(probability vs reward)."*

Preregistration (written before the first matrix cell):
`PREREG_STOPPING.md`. Unit suite: `test_stopping_rules.py` (green, red-capable).
Independent verification: `results/verify_stopping.txt`. Factcheck:
`results/factcheck_stopping.txt`.

---

## 0. Headline

1. **The rule was replaced, and the replacement is a different TYPE.** The frozen
   arrow `probe iff β·GAIN_UNIT·score > rich·PROBE_LEN + cost` is gone from the
   new arms. In its place: **T2**, which compares the expected **reward totals of
   two complete strategies** over the same horizon (`voi`), and **T3**, which
   compares **probability with probability** (`conf`).
2. **The *replacement type* is the winner, and the specific T2 rule I wrote is
   not.** On the **published instance** (where the frozen rule probes at all
   prices) `voi` is **significantly better** — up to **−0.0123 regret
   [−0.0156, −0.0090]** at m=16 — while on the **context-specific instance** it
   loses (**+0.0013 [+0.0007, +0.0021]** at mask ε=0.35) and, in rich worlds,
   refuses to probe at all (0 probes above base ~0.85).
3. **T3 — the probability-only rule — is best where the frozen rule is worst.**
   On the richness family it is **significantly better than frozen at base
   0.60/0.70/0.75/0.80** (up to **−0.0265 [−0.0282, −0.0248]** at base 0.70)
   precisely in the band where the new T2 was **worse**, and it is exactly `nocost`
   where T2 refuses. It is the no-stop extreme, and on this family the no-stop
   extreme *wins*.
4. **T3 as I first designed it had no stopping term at all.** The preregistration
   declared this before the matrix (§5): "openness" is a different question from
   "worth the steps". Measured: `conf` tracks `nocost` to within one probe across
   the whole richness family. I did **not** bolt a price onto it — that is the
   turn-104 trap — it is reported as the measured limit of the type.

---

## 1. What the old rule actually compared (a correction to the campaign's framing)

The owner's phrase is "probability vs reward". Reading the code, that is not
literally what the union engine did: both engines key `candidate_gen` on the
observed **reward** `"y"`, so `score`, `rate_a`, `rich_rate` are all reward
rates. The incommensurability is real but one level down:

```
probe iff  β · GAIN_UNIT · score  >  rich_rate · PROBE_LEN + PROBE_COST
           └ value-per-gap × gap ┘   └ duration × rate ┘
```

**GAIN_UNIT** is a declared *value per unit gap*; **PROBE_LEN** a declared
*duration*. The verdict is fixed by two declared constants of different kinds,
neither checkable against the world. Corrected in `PREREG_STOPPING.md §1` and
stated here rather than quietly.

## 2. The replacement types

| arm | rule | what is compared with what |
|---|---|---|
| `frozen_rule` | the campaign's own rule (delegated to `arbitration_scaled`) | value×gap vs duration×rate |
| **`voi`** (T2) | `probe iff info > risk` | **reward total vs reward total**, same horizon |
| **`voi_rate`** (T2b) | horizon-free form | reward **per step** vs per step |
| **`conf`** (T3) | `probe iff q_lo < P(rate_cand > rate_alt) < q_hi` | **probability vs probability** |
| `union_nocost` | probe everything nominated | the no-price extreme (control) |
| `beta0` / `pure` / `union_noexp` | controls | — |

where, with `mu_c` the agent's own Beta(1,1) posterior mean on the candidate's
rate, `r` the observed best alternative rate, `L = T − t` the agent's **observed**
remaining steps and `n = PROBE_BLOCK = 20` (asserted equal to the campaign's own
constant):

```
info = (L−n)·( E_k[max(post, r)] − max(mu_c, r) )     risk = n·( max(mu_c, r) − mu_c )
```

`E_k` is the exact Beta-Binomial predictive of `n` further pulls — **closed
form, no sampling, no RNG**, so the stopping rule cannot leak a random stream
into the agent. There is **no GAIN_UNIT, no β, no PROBE_COST** in T2/T2b/T3
(audited by introspection in unit test W6).

## 3. The result that answers the owner's question

### 3.1 On the published instance the new type **wins** (nsim = 2000)

| m | `voi` regret | `frozen_rule` regret | diff [95% CI] | `voi` probes | frozen probes |
|---|---|---|---|---|---|
| 2 | 0.005100 | 0.005250 | −0.00015 [−0.00045, 0.00000] | 6.45 | 8.73 |
| 8 | 0.010800 | 0.012750 | **−0.00195 [−0.00330, −0.00060]** | 7.80 | 8.89 |
| 16 | 0.013200 | 0.025500 | **−0.01230 [−0.01560, −0.00900]** | 8.30 | 9.99 |
| 49 | 0.012300 | 0.024450 | **−0.01215 [−0.01530, −0.00900]** | 8.89 | 9.99 |

The mechanism is visible in the probe counts: the one-currency rule **stops
earlier** (8.3 vs 10.0 blocks at m=16), and `chosen_is_optimal` rises
0.915 → 0.956. The frozen rule's bar is on the *score*, not on the price, so it
keeps probing at the cap; T2 prices the steps.

### 3.2 On the context-specific instance the same rule **loses** — and where T2 goes silent, T3 takes over

Richness family (`eps = 0.35`, world's best-arm rate = base):

| base | `voi` regret | frozen regret | `voi` probes | frozen probes | `conf` regret | `conf` probes |
|---|---|---|---|---|---|---|
| 0.50 | 0.004635 | 0.003299 | 3.98 | 3.31 | 0.003214 | 3.87 |
| 0.60 | 0.078917 | 0.006822 | 1.34 | 3.01 | **0.003026** | 3.89 |
| 0.70 | 0.081520 | 0.030479 | 0.46 | 2.76 | **0.004001** | 4.00 |
| 0.75 | 0.056363 | 0.030429 | 0.65 | 2.40 | **0.009572** | 4.15 |
| 0.80 | 0.031290 | 0.027238 | 0.24 | 1.46 | **0.021404** | 4.34 |
| 0.85 | 0.005994 | 0.005994 | 0.0045 | 0.47 | 0.006037 | 4.47 |
| 0.90 | 0.004750 | 0.004750 | 0.0040 | 0.08 | 0.004750 | 4.46 |
| 0.95 | 0.003638 | 0.003638 | 0.0020 | 0.00 | 0.003642 | 3.96 |

* **G2 PASS.** `voi` probes fall monotonically with the world's richness
  (Spearman ρ = **−0.976**): the silence is **derived**, not declared. T2 is a
  **two-sided band** — it probes only while the alternative is close enough that
  learning would change the decision (base 0.85: the alternative is already at
  the candidate's level). The frozen rule's answer, by contrast, **does not move
  with the price at all** for a fixed candidate (§3.3).
* **T2 loses to the frozen rule exactly where it is still probing** (base 0.60–0.80,
  up to **+0.0721 [+0.0694, +0.0749]** at base 0.60) and **ties where both are
  silent** (base 0.85–0.95, diff exactly 0).
* **`conf` (probability only) beats the frozen rule in that same band**:
  −0.0038 at 0.60, **−0.0265 [−0.0282, −0.0248]** at 0.70, −0.0209 at 0.75,
  −0.0058 at 0.80; ties elsewhere. The pattern is real, not noise: the CI
  excludes zero at four successive richness levels.

### 3.3 What actually moves each verdict (`diag_sensitivity_v3.py`)

Same candidate (rate 0.85, n = 200), alternative rate 0.30, each declared number
varied:

| declared number | range | answer of `frozen_rule` | answer of `voi` |
|---|---|---|---|
| GAIN_UNIT (value per gap) | 25 … 800 | **True at every value** | n/a |
| PROBE_LEN (duration) | 5 … 80 | **True at every value** | n/a |
| horizon (remaining steps) | 20 … 400 | n/a | False at every value here |
| probe_len | 5 / 20 / 40 | n/a | True / False / False |

and with the **world's own** alternative rate varying (0.10 … 0.95):
`frozen` answers **True at all six** levels; `voi` answers True at exactly one
(0.85). That is the structural difference the owner asked for, stated as a
number: the frozen rule's verdict does not respond to the world's price for a
fixed candidate — it responds to a declared conversion — while T2's respond to
the price in a band and are invariant to any such conversion.

**The honest limit (prereg A4).** T2 still moves with the horizon. It must: how
long the answer will be used is a fact about the episode, and a decision-maker's
answer really does change with it. That is a different dependence from moving
with a declared value-per-gap, which no fact about the world pins. Both
sensitivities are shown above rather than argued about.

## 4. Gates (PREREG_STOPPING.md §4), all measured

| gate | claim | result |
|---|---|---|
| **G0** | transplant control: `frozen_rule` cells identical to `union` | **PASS** (25 cells, cell-for-cell, `verify` V2) |
| **G1** | the new rule must act (≥1 probe on ≥80% of mask seeds) | **PASS** (99.7% at every ε) |
| **G2** | probes must fall with richness (Spearman ≤ 0) | **PASS** (ρ = −0.976) |
| **G3** | regret `voi` vs `frozen_rule` measured with CI | done: **better on `pub`, worse on `mask`/`maskr`** |
| **G4 / P1** | `conf` tracks `nocost`, not a stopping rule | **CONFIRMED** (within one probe at every richness) |
| **G5** | controls behave: `beta0` probes 0, `pure`/`noexp` ~0 | **PASS** (after a defect fix, §6) |

## 5. Verification (independent paths)

`verify_stopping_independent.py` — **13 checks, 0 failures**, run on
`results_stopping_hi` (nsim = 2000):

* **V1** every cell's mean and sem recomputed from its own raw rows (85 cells,
  0 mismatches);
* **V2** the generated v3 agent run with the OLD rule reproduces the **frozen v2
  producer** (`union_run_v2.run_cell`) cell-for-cell on 25 cells — a genuine
  cross-producer transplant control, not a self-comparison;
* **V3** the rule's arithmetic re-implemented **from its mathematical statement**
  (own posterior, own predictive, no shared code): `info ≥ 0`, `risk ≥ 0`, the
  identity holds to 3.4e−14, and the accept set over the alternative's rate is an
  **interval** (0.002 … 0.852);
* **V4** the published-instance win recomputed from raw rows (4/4 m-values) and
  the probe count there is genuinely lower;
* **V5** G2 recomputed (ρ = −0.976; probes ≤ 0.05 above base 0.85);
* **V0** negative control: a corrupted stored mean is detected by the same
  recomputation;
* **V6** a fresh `voi` cell is bit-identical across three processes / hash seeds;
* **V7** frozen producers unchanged: `candidate_gen.py fa9721ae816c3c42…`,
  `arbitration.py 2d3d825bcfc83cc8…`, `union_agent_v2.py 76bfe972bde4963c…`.

`factcheck_stopping.py` — **every number quoted above recomputed from the frozen
JSON, ALL PASS** (`results/factcheck_stopping.txt`).

The v3 agent itself is **generated**, not hand-edited: `make_agent_v3.py` applies
four mechanical substitutions to the frozen `union_agent_v2.py` and refuses
unless each occurs exactly once; the exact patch is `union_agent_v3.diff` (27
changed lines). The diff is the audit trail.

## 6. Defects found in my own work this turn (reported, not hidden)

1. **`beta0` control was silently equal to `frozen_rule`.** My `_frozen` wrapper
   hardcoded `beta=1.0`, ignoring the β the caller passed, so the C1 control
   probed 3.43 instead of 0. **G5 caught it**; fixed to pass β through; the 17
   `beta0` cells re-run; `verify` and `factcheck` re-run after.
2. **My first negative control (W8) was ill-posed.** It asserted that corrupting
   the predictive must break the rule's algebraic identity — but that identity is
   *definitional* and holds for any predictive. Replaced with a meaningful one:
   a degenerate predictive must **change the decision** (and it does: 1 → 0).
   The corrected control is in the suite and the error is written into its
   docstring.
3. **`verify` V2's first version was a self-comparison** (v3's `frozen_rule` vs
   v3's `union`, which share the new dispatch) and could not fail. Rewritten to
   compare against the **frozen v2 producer**.
4. **T3's first design had no stopping term.** Declared in the prereregistration
   §5 before the matrix rather than after; not "fixed" by adding a price.

## 7. What this changes about the campaign's claim

The campaign's mechanism was a **verification** procedure with a declared price.
This turn replaces the price with two rules that need no conversion:
one compares the two strategies in reward units (`voi`), one compares
probabilities with probabilities (`conf`).

The honest summary of the measurement:

* **a different TYPE of rule does exist and is measurable**, and the *type*
  (pricing the steps actually spent, rather than converting a gap into reward) is
  what wins on the published instance (**−0.0123** at m=16);
* **the specific T2 I wrote is not a strict improvement**: on the context-specific
  world it under-probes and loses, and in rich worlds it goes silent;
* **the no-stop extreme wins on that richness family** (`conf`/`nocost` beat
  frozen at base 0.60–0.80), which is a finding against the premise that a
  stopping rule must help at all — here, in the middle of the richness range,
  the correct amount of stopping is *none*.

## 8. Honest limits

* The **instance transfer is not free**: the same rule wins on the published
  instance and loses on the context-specific one. No single rule is best on both;
  the report shows both rather than averaging them.
* **n = 10 seeds** since turn 129 set the pattern; here **nsim = 2000** for the
  headline cells, so the CI widths are real (mask ε=0.35 diff CI width 0.0014).
* T2 is **myopic** (one-step lookahead); the Bayes-optimal dynamic program is not
  implemented (prereg L1). `nocost` bounds the gap from the other side.
* `voi_rate` (horizon-free) is a **negative result**: 0.38 probes, regret 0.164 —
  it ignores that a probe is a fixed block of steps. Declared as a candidate
  negative in the prereg §5 and borne out.
* The comparator rate `r` enters as a point, not a posterior (L4).

## 9. Fork (the owner's decision)

* **(A)** Adopt the one-currency rule **by instance class**: `voi` where the world
  is thin (it wins), `nocost`/`conf` where the world is rich (it wins there). This
  is defensible but is a *policy over rules*, not a single rule.
* **(B)** Close the line with this as the honest end: "a different type of rule
  exists, it wins on the published instance and loses on ours; the no-stop extreme
  wins in the middle of the richness range" — and write the preprint column with
  this in it.
* **(C)** One more turn to build the **Bayes-optimal** version (real lookahead),
  which is the only remaining object that could dominate both. I would name it as
  a new instrument, not as the campaign's mechanism.
