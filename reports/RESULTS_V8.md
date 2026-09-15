# RESULTS V8 — the three declared gaps, closed as far as this world allows

Turn 126 (msg_00126). Frozen preregistration: `research/PREREG_V8.md`,
written before the first line of v8 code, with amendments A1–A17 each
carrying its date and its reason. The V1–V7B line stays frozen
(`CAMPAIGN_RESULT.md`); nothing there is revisited.

**Short answer, three claims, three different shapes.**

* **Continuous confidence — the belief number is not decoration, but its
  measured advantage over the verdict is small at the top and large where
  the verdict is structurally weak.** C1 passed all three legs at every
  gap: `graded > threshold` by +7 288 (gap 0.20) and +7 550 (gap 0.03),
  CI excluding 0, 8/8 seeds, both halves. C2 (`graded > coin`) passed at
  every gap by an order of magnitude more (+203 350 … +7 738) — so the
  gain is **information**, not merely "acting on something". And C3
  (`threshold ≤ coin`) failed at 0.05 and 0.03: the frozen verdict rule
  is *still* better than a coin there (by +10 825 and +188). The strong
  claim I preregistered — "below the gate the verdict collapses to the
  floor" — is **refuted**; what survives is measured, not asserted.
* **Self-reinforcement — the loop is real, is the world's, and pays.**
  In a world that pays consistency, the graded arm's own end-of-epoch
  contrast inflates from 0.2130 to **0.3273** (analytic 1.25·p_edge −
  p_bg = 0.3375; the rotating control stays at 0.1967 in the same world).
  Because the inflation is the *only* way to collect the consistency
  payment, the graded arm earns **+403 588** over the rotating arm in the
  persistence world against **+203 925** in the persistence-free world:
  the loop is worth roughly **+200 000** on top, and the coin control
  earns nothing of it. That is the turn-115 pathology, given a number and
  a controlled 2×2 — and it turns out to be **a property of the world,
  not of the estimator**.
* **Amortization — the answer is a curve, and its sign flips.** Reuse
  (carrying last epoch's counts at half weight) is **negative** at q =
  0, 0.25, 0.5 (up to −48 163) and **positive only at q = 1.0**
  (+11 838, 8/8 seeds, 99.2% of the oracle). Where facts die every epoch,
  reuse is a stale prior and costs reward; where the fact never changes,
  reuse is nearly free knowledge. The mechanism claim in the prereg —
  "paying once and reusing free" — is **true of the mechanism** (carry's
  gathering falls to **44.9%** of fresh's at q = 1.0) and **false of the
  reward** except in the limit.

---

## 0. What was measured and on what

| measurement | source | n |
|---|---|---|
| world oracle | `results/verify_env_v8.txt` | E1–E6, ALL PASS |
| synthetic units | `results/toy_v8_out.txt` | W1–W7 incl. 3 live negative controls, ALL PASS |
| matrix | `results/matrix_v8/*.json` | **404 runs × 16 000 steps** |
| primary analysis | `results/analysis_v8.txt` | `analyze_v8.py` |
| independent pass | `results/verify_v8_independent.txt` | `verify_v8_independent.py`, different code, disk only, ALL PASS |

Frozen code hashes before and after the matrix:
`env_terrarium_v8.py c9e807082353`, `agent_emca_v8.py d42ff252f4c6`,
`run_life_v8.py 11de36970c0c`, `driver_v8.py 64a47fa9a31c`,
`analyze_v8.py 99477d5046d0`, `verify_v8_independent.py 387d42b653d2`
(prefixes; full digests in the ledger). Noise floor, stated before the
analysis was read: the rotating arm's reward sd across 8 seeds is
**5 154** units, so a 2·SEM paired effect is ≈ **3 645** and an 80 %-power
paired effect ≈ **5 102**. Every primary contrast below is read against
that floor, and C1 at gap 0.03 (+7 550) is above it while C1 at 0.20
(+7 288) is only just above it — recorded plainly.

---

## 1. Block C — continuous confidence

Design: three-action clocked bandit; the paying action is re-drawn every
2 000 steps; the agent holds per-action counts and forms a belief either
by a thresholded exact-Fisher + RR rule (the campaign's frozen v7 rule)
or by a posterior `γ = max(0, 2Φ(z) − 1)`, then acts on the belief with
probability `min(1, τ·γ)`. The gate for every contrast is the frozen
three-leg rule (paired bootstrap CI excluding 0, one-sided paired sign
test p < 0.05 in the declared direction, and both within-run halves
agreeing with the declared direction).

| contrast | 0.20 | 0.10 | 0.05 | 0.03 |
|---|---|---|---|---|
| **C1** graded − threshold | **+7 288 PASS** | **+28 150 PASS** | **+15 488 PASS** | **+7 550 PASS** |
| **C2** graded − coin | **+203 350 PASS** | **+86 275 PASS** | **+26 312 PASS** | **+7 738 PASS** |
| **C3** threshold − coin | **+196 062 PASS** | **+58 125 PASS** | +10 825 **FAIL** (6/8) | +188 **FAIL** (5/8) |

**What each says.**
C1 is the headline the directive asked for: at **every** gap the belief
number beats the verdict, and at the *thinnest* gap the verdict is nearly
worthless (it leaves 12 739 steps of the 16 000 spent gathering, against
graded's 4 294). C2 is the honesty check on C1: if C1's gain were merely
"acting on anything", the coin arm — same |γ|, no information — would
match it. It does not, by 7 738 to 203 350, so **the sign of the evidence
carries the information**. C3 is where my preregistration was wrong and
the measurement answered: I predicted the threshold rule collapses to the
coin floor below the gate. It does not collapse: at 0.05 it is still
+10 825 above the coin, its CI just excludes 0 but the sign test fails
(6/8), and at 0.03 it is +188 with a CI covering 0 — indistinguishable
from the coin. So the honest form of the finding is: **the verdict rule
degrades towards the coin as the truth thins, and is indistinguishable
from it at 0.03; it does not collapse at 0.05.** No threshold was moved;
C3 was reported FAIL by the gate as written.

**C4 — the price, in effort.** The threshold rule pays with its life.
Gathering share of the total life: **8.3 % / 40.9 % / 70.5 % / 79.6 %**
across the four gaps, against graded's **4.5 % / 10.4 % / 24.9 % /
26.8 %** — a **1.8×–3.9×** effort multiple. The reward consequence is far
smaller (at 0.03 the threshold arm earns 579 225 against graded's 586 775,
**1.3 %** below) because the marginal value of the harvest falls with the
gap; both numbers are reported and neither is used to excuse the other.

**C4b — agent-level evidence demand.** Per epoch, the trials-per-action
at which each rule acquires a belief: graded crosses γ > 0.5 at
**87 / 118 / 206 / 333** trials for the four gaps; the threshold rule
fires at **1 877 / 1 494 / 703 / 1 850** trials, i.e. a **21.7× / 12.7× /
3.4× / 5.6×** evidence multiple — and at 0.03 that figure (1 850) is
*noise*: the rule's firing rate there is 3.1 %, so the number is the
mean over the few epochs where a lucky control rate let a thin truth
through. This is the quantitative form of the campaign's `RR ≥ 1.3` gate:
its cost is not "more data", it is an evidence demand that no longer
converges to a belief below the ratio the gate imposes.

**C5 — the number orders the truth.** Mean `γ` on the true action vs on
the false actions, over epoch ends: 0.9967/0.0000, 0.9868/0.0002,
0.8132/0.0383, 0.5664/0.1244 (Mann–Whitney p ≈ 1e-16 … 1e-41). **PASS**
at every gap: the confidence value is not a proxy for "something
happened" — it separates the truth from the noise it competes with.

**C6 — τ dose (secondary, no verdict).** At gap 0.10 the reward falls
monotonically with the tendency-to-act parameter and the effort rises:
τ=1 → **704 275** reward / 1 666 gathering steps; τ=0.7 → **677 750** /
5 837; τ=0.3 → **642 125** / 11 616; τ=0 → **613 512** / 16 000 (the
floor). Not gated; reported because the directive asked whether a single
number can carry the decision, and a monotone dose curve is the evidence
that it can — with the honest note that the two intermediate rows are
**not** separately gated and carry no verdict force.

---

## 2. Block A — self-reinforcement as a battery

Preregistered prediction (A1): under the persistence rule the acting
arm's own observed contrast becomes `1.25·p_edge − p_bg`, i.e. 0.3375 at
gap 0.20 and 0.2125 at 0.10, while the rotating control stays at the true
gap.

| arm | persist | gap 0.20 measured | gap 0.10 measured |
|---|---|---|---|
| graded | off | 0.2130 (true 0.2000) | 0.1224 (true 0.1000) |
| graded | **on** | **0.3273** (pred 0.3375) | **0.1868** (pred 0.2125) |
| rot | off | 0.1967 | 0.0994 |
| rot | **on** | **0.1967** | **0.0994** |

All forecasts inside ±0.03 except graded at 0.10 (+0.026 short — inside
tolerance, reported) — and the control shows the inflation is **not** the
estimator's own doing: the rotating arm, in the *same* persistence world,
reads exactly the true gap. **The loop is the world's, and the estimator
is honest in a world that does not pay for consistency.** This is the
sharpened form of the turn-115 lesson: what that world met was a real
return-to-consistency in the world, not a statistical artifact of the
agent.

**A2 — does it pay?** Two contrasts, both passing all three legs:

* reward(graded, persistence on) − reward(graded, persistence off)
  = **+199 663** (gap 0.20) and **+152 775** (gap 0.10). Note: the
  persistence world does not add reward — it converts the *same* action
  mix into a higher hitting rate, and the graded arm collects that as
  reward it would not otherwise earn. The value of acting on a belief
  rises with the consistency payment.
* reward(graded, persist on) − reward(rot, persist on)
  = **+403 588**; reward(graded, persist off) − reward(rot, persist off)
  = **+203 925**.

The second pair is the clean within-world comparison: in the world that
pays consistency, acting on a belief is worth about **twice** what it is
worth in the world that does not, and the extra **+199 663** is the
consistency payment itself. That this difference equals the first bullet
**exactly** (+403 588 − +203 925 = +199 663) is worth stating: it means
the mechanism is understood arithmetically, not merely detected. The coin
control earns none of it (A-null: agreement 0.300–0.425 under
`truth=off`).

**A2a — a correction to my own instrument, and a second to my own
reporting.** (i) The first analysis compared the same arm to itself
because the persistence knob was not threaded into its lookup; that
defect is fixed and the SUPERSEDED first-pass analysis is kept on disk as
`results/analysis_v8_FIRSTPASS_superseded.txt`. (ii) Then, in the first
draft of this report, I typed A2's two numbers from the superseded pass.
`factcheck_v8_report.py` — a separate script that re-derives every number
printed here from the frozen matrix — caught both, and the numbers above
are its measured values: **+199 663** and **+152 775**, not +199 950 and
+148 850. The fact-check exists because the report is prose written by me
and the matrix is not.

**A4 — direction battery.** The belief identifies the epoch's true
action **64/64 = 1.000** for graded, 48/48 for the threshold arm at
0.10, and **0.328 / 0.359** for the coin — inside its 1/3 ± 3σ band, as
the prereg required. Under `truth=off` agreement is 0.300–0.425, i.e. at
chance. All null bounds respected.

---

## 3. Block F — amortization of the price of knowledge

Design: the agent either starts each epoch blank (`fresh`) or carries the
previous epoch's counts at half weight (`carry`); stickiness `q` is the
world's probability of repeating the same paying action.

| q | carry − fresh (paired) | gate | carry's gathering / fresh's |
|---|---|---|---|
| 0.00 | **−48 163** (0/8) | PASS (declared negative) | 2.064 |
| 0.25 | **−36 688** (0/8) | PASS (two-sided) | 1.909 |
| 0.50 | **−25 762** (0/8) | FAIL (declared positive) | 1.199 |
| 0.75 | **−10 125** (2/8) | FAIL (declared positive) | 0.896 |
| 1.00 | **+11 838** (8/8) | PASS | **0.449** |

* **F1's sign flip is the result.** My prereg said "negative or zero at
  q = 0, positive and growing with q". The first half is right; the
  second is half-right: the difference is monotone in q, crosses zero
  between q = 0.75 and 1.0, and is **negative across most of the range**.
  Two of the five rows are therefore **FAIL** by the letter of the gate,
  and they are reported as FAIL.
* **F2 — the reuse is real and free at the limit:** carry spends
  **44.9 %** of fresh's gathering steps at q = 1.0 (gate ≤ 0.60), and
  89.6 % at 0.75 (gate missed). At q = 0 it spends **twice** fresh's,
  because it must *unlearn* the stale prior — that is the mechanism of
  the negative rows, measured rather than asserted.
* **F3 — endpoint control PASS:** at q = 1.0 carry reaches **99.2 %** of
  the oracle's reward (720 300 vs 714 413). A fact found once and held
  without re-paying is worth essentially what knowing it for free is
  worth. That is the amortization claim, true in the limit the claim
  requires — and only there.

**The honest synthesis of Block F, in `CAMPAIGN_RESULT.md` §3's terms:**
reuse does not create value; it **converts a stale fact into a free one
only when the world's facts outlive their use**. Where the world changes
faster than the agent acts, the same mechanism is a tax.

---

## 4. Two defects found, both by the instrument, both declared

1. **A real defect in the world, found by the independent pass
   (amendment A16).** The first v8 matrix was analysed and then
   cross-checked; the verifier caught 4 470 per-epoch mismatches between
   the agent's own log and the world's recorded counts. Root cause: the
   environment's `obs()` built the observation *before* advancing the
   clock, so `epoch_id` named the previous step's epoch and every
   epoch-boundary trial was filed one row late. My first attribution
   named the agent; that was wrong, and the amendment says so. Fixed in
   `env_terrarium_v8.py`, a regression check (`C1`/`D1`) now exists, and
   **the entire 404-run matrix was re-run from scratch on the fixed
   code** — same seeds, same thresholds, same batteries. Per-run sums
   (reward, every cross-arm contrast) were unaffected; the per-epoch
   battery was not. The report carries the re-run's numbers.
2. **A mis-specified check of my own, found by the toy pass (A10–A12,
   A17).** Three of my preregistered predictions were wrong and are
   corrected in writing rather than edited away: the frozen rule is
   **non-monotone in n** below its ratio gate rather than silent (A10);
   the evidence-demand ratio is ≈8.5, not 6.0 (A11); and A1's control row
   demanded an effect the control cannot have (A17). One negative control
   in the toy suite did not actually go red (the single-control ratio
   landed inside the band) and was replaced by one that does — a check
   that cannot fail checks nothing.

---

## 5. Independent verification

`verify_v8_independent.py` — a separate script, importing neither the
analysis nor the agent's log, rebuilding every quantity from the raw
traces and the world's ground truth recomputed from the seed alone:

* **A1** ground truth = f(seed, q) in all 404 files — PASS, 0 mismatches;
* **B1–B4** accounting identities (reward = K·pays, counts sum to steps,
  per-epoch pays sum to the total, trace length = steps) — PASS;
* **C1** fresh arms: agent counts == raw trace — PASS, 0 mismatches;
* **C2** carry arm: counts == `int(0.5·previous) + raw` — PASS, 960/960
  rows match the declared reuse arithmetic (a *stronger* check than the
  one it replaced: it verifies the mechanism rather than its absence);
* **D1** fresh arms: per-epoch agent hits == the world's recorded pay
  counts — PASS, 0 mismatches;
* **D2** the persistence contrast reproduces the analytic inflation
  within ±0.03 — PASS for all four rows;
* **E** the frozen rule's firing rates recomputed from raw data:
  0.750 / 0.484 / 0.047 / 0.031 — matching the analysis;
* **F, G, H** every contrast sign and every direction agreement
  reproduced independently;
* **I** determinism: three arms re-run in fresh processes,
  **byte-identical** JSON (faba82f5…, b8fab957…, ccd12bf2…).

**Verdict: ALL PASS, zero discrepancies with the primary analysis.**

---

## 6. Verdicts

| claim | result |
|---|---|
| **C1** graded beats threshold at every gap | **PASS** (+7 288 / +28 150 / +15 488 / +7 550), all three legs |
| **C2** the gain is information, not activity | **PASS** (+203 350 / +86 275 / +26 312 / +7 738) vs the coin |
| **C3** the verdict collapses to the floor below the gate | **FAIL, my prediction refuted** — threshold stays above the coin at 0.05 (+10 825) and is indistinguishable at 0.03 (+188) |
| **C4** threshold pays 1.8–3.9× the effort | **PASS** (8.3/40.9/70.5/79.6 % vs 4.5/10.4/24.9/26.8 %) |
| **C4b** evidence-demand multiple | **PASS** (21.7× / 12.7× / 3.4× / 5.6×; non-convergent at 0.03) |
| **C5** the number orders the truth | **PASS** at all four gaps (p ≤ 1e-16) |
| **A1** the loop's size is the predicted 1.25·p_edge − p_bg | **PASS** for the acting arm; control inflated by nothing |
| **A2** acting on a belief pays more in a world that pays consistency | **PASS** — +403 588 vs +203 925 against the control |
| **A3** the loop is the world's, not the estimator's | **PASS** — rot shows the true gap in the same world |
| **A4** the belief identifies the truth; the coin does not | **PASS** (1.000 / 1.000 vs 0.328 / 0.359) |
| **A-null** under truth=off agreement is at chance | **PASS** |
| **F1** reuse pays, growing with q | **PARTIAL** — monotone in q but negative until q = 1.0; **two rows FAIL by the gate** |
| **F2** reuse is free at high q | **PASS** at q = 1.0 (0.449); missed at 0.75 (0.896) |
| **F3** at q = 1 carry reaches the oracle | **PASS** (99.2 %) |

---

## 7. What this changes in the picture

`CAMPAIGN_RESULT.md` §3 ended the last line with: *"what pays is the
difference between what the agent knows and what the world is willing to
pay for it — and both terms are set by the world."* V8 adds a third term
to that sentence, and the three gaps each landed on it:

1. **How much the agent pays to know** — the verdict rule is not merely
   slower than the posterior; it spends 1.8–3.9× the effort, and its
   evidence demand stops converging to a belief below the ratio gate it
   imposes. Continuous confidence buys a *bounded* advantage in reward
   (1.3 %–4.3 %) and a *large* one in effort.
2. **How the agent's own acting feeds its evidence** — in a world that
   pays consistency the belief loop is worth about the size of a whole
   second agent's worth of advantage (+200 000 over the same lifetime),
   and it is the *world's* property: a control that never acts on a
   belief reads the un-inflated gap in the same world.
3. **Whether a fact paid for once can be held free** — yes, exactly in
   proportion to how long the world's facts live; below that, reuse is a
   tax, and the same mechanism switches sign.

The one-line form: **knowledge is worth what the world pays for it — and
that price is now measured in three places the campaign had never priced:
the evidence rule's own demand, the feedback of acting on belief, and the
lifetime of the fact.**

---

## 8. Limits, stated plainly

1. `n = 8` seeds per arm in Blocks C and F, 10 for the null. The three-leg
   gate is strict, but the seed count is what it is; C1 at gap 0.20
   (+7 288) is only just above the 8-seed noise floor (≈3 645 for 2·SEM).
2. The persistence rule is **one** implemented mechanism (75 % over 8
   steps, ×1.25). It is a real world fact and the analysis is exact for
   it, but "self-reinforcement" in general is not thereby characterised —
   other consistency rules would give other factors.
3. `kappa = 0.5` is a declared constant; F1's *sign* is the claim, its
   magnitude is a function of that declaration and is reported as such.
4. The bandit has three actions, one observable effect and one payoff;
   nothing here speaks to spaces where the fact is not observable at all.
5. The threshold arm's `MIN_N = 20` candidate bar is a frozen v7 constant
   carried over unchanged; it was not re-tuned for v8, and a different bar
   would move C3's marginal rows.
6. The v7 lineage break is declared in the prereg §6: `candidate_gen`,
   `arbitration_v8.py` and the do-intervention protocol are **not** used
   in v8, and nothing here claims their results.

---

## 9. Fork

The three declared gaps of `CAMPAIGN_RESULT.md` §5 are closed in one
world, and each closed with a measured shape rather than a verdict. The
natural next step, if the owner wants one, is not another world but the
**economics**: C1's reward advantage is a small percentage precisely
because the harvest's marginal value is low in this world; a world where
the harvest is the dominant source of reward would price the belief
number where the campaign can see it directly. I do not recommend it —
the three results above are the answer to the directive, and the line was
already frozen once for the reason that more worlds stopped buying
anything new.
