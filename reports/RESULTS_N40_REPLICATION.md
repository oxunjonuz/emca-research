# RESULTS — n=40 REPLICATION (turn 152)

Owner directive `msg_00152` → `NEW_TZ.md` item 2: *"Во всех кампаниях n=10 сидов, и
это честно заявлено как ограничение. ... стоит проверить, не тонут ли какие-то из
'пограничных' находок v10-v16 в статистическом шуме при таком малом n."*

**Design.** Every decisive cell of v10–v18 is re-run on **30 FRESH seeds (10…39)**.
The original 10 seeds are **not** re-run, so a verdict that held only because of the
particular seeds it was first measured on is exactly what this can catch. 870 cells,
written to `results/replicate_n40/` only; the frozen matrices are re-counted at the
end of the run and are untouched.

**Headline, first sentence on purpose.**

> **25 of 27 replicated verdicts hold on fresh seeds. One does not — and it is
> v16's headline.** v16 reported that the doctor *"never drains the aquifer in any of
> the 240 cells of the declared search"*. On 30 fresh seeds it drains on **2**; over
> 70 fresh seeds, on **3** (4.3 %). The cause is measured, not guessed, and it is the
> **same structural fact this line found three campaigns ago**: the frozen survival
> layer parks a starving agent on the rich tile — and a starving agent standing on the
> rich tile harvests it. **v16's conclusion survives in a bounded form; its absolute
> form ("never") does not.** This is what a replication is for, and I found it on my
> own result.

---

## 1. What replicated (25 of 27)

| campaign | verdict | fresh seeds |
|---|---|---|
| v10 B2 | the given rule stops the harm (`commons_left = 9`) | 30/30 |
| v10 B3 | coupling 0: the victim-keyed rule is inert (0 left, keeper dead) | 30/30 |
| v10 B3 | coupling 1: the same rule works (17 left, keeper alive) | 30/30 |
| v10 B4 | low: the internalized value restrains (25 left) | 30/30 |
| v10 B4 | high: it does NOT restrain (0 left, keeper dead) | 30/30 |
| v11 | the unbraked arm's harm is 5 | 30/30 |
| v11 | the inflated appraisal drains everything (W6 stays refuted) | 30/30 |
| v12 | the bribe threshold: 0.24 and 0.25 → 5; 0.26 and 0.30 → 30 | 30/30 each |
| v13 | the lie buys the ledger arm completely (30, keeper dead) | 30/30 |
| v13 | the honest label restrains (5 drains, 25 left) | 30/30 |
| v14 HA1 | the honest auditor closes the hole (5, alive, statistic `0.04999999999999999`) | 30/30 |
| v14 HA3 | with no auditor the lie works again (30) | 30/30 |
| v16 | below the threshold (t 0.25) → 5; above it (t 0.26) → 30 | 30/30 each |
| v17 HB1 | the bought auditor buys the believe arm (30, keeper dead) | 30/30 |
| v17 HB3 | the silenced auditor does not buy the cautious arm (5) | 30/30 |
| v18 HE1 | the world's refusal stops the willing agent (0 drains, refusals > 0) | 30/30 |
| v18 | the widen arm with no scope drains everything (30) | 30/30 |
| v15 H2 | pure information gain is indifferent (`a0_share` mean **0.250**) | 30/30 |
| v15 H3 | the relevance criterion restores the preference (mean **0.998**, min 0.993) | 30/30 |
| v15 H6 | random stays at the coin floor (mean 0.249) | 30/30 |

**v15's headline survives the fresh seeds exactly as reported** — indifference
(`0.250 ± 0.005` at n=10; **0.250** at n=30) and the criterion-driven share (0.998 at
both). v12's threshold, v13's hole, v14's closure and v18's boundary all reproduce at
10/10 → 30/30. **The n=10 limitation did not hide anything in those.** That is the
useful negative result of this exercise.

## 2. What did NOT replicate: v16's doctor, and the mechanism

| arm | fresh seeds that drain | frozen v16 (10 seeds) |
|---|---|---|
| `n_doctor` | **2 / 30** | 0 / 260 cells |
| `n_doctor_price` | **2 / 30** | 0 / 240 cells |
| `w_price` | 30 / 30 | 30 / 30 (unaffected) |
| `w_given` | 30 / 30 | 30 / 30 (unaffected) |

Widened to 70 fresh seeds (10…79): **3 of 70 = 4.3 %**.

**Mechanism, measured from the code and the traces, not inferred:**

* The frozen `agent_emca_v7._survival` returns `"wait"` when `energy < LOW_ENERGY`
  (**35**) **and the agent is standing on RICH** — its own comment says the rich tile
  *"also heals nothing, but berry scent was preferred"*.
* The v16 doctor navigates to the station and stands there. Over 16 000 steps its
  energy drifts down; on some seeds it crosses 35 **while the frozen navigation has
  put it on the rich tile**, and the survival layer then parks it there permanently.
* A `"wait"` on RICH **is** the harvest. Traced on seed 25: first rich non-move at
  **t = 3608** with energy **27.1** — already below the threshold — then 543 harvest
  steps and 30 drains.

**This is the latent trap v11 exposed in the WIDE agent, now visible in the narrow
one.** v11's report says it in the same words: *"in the 4 seeds the agent's energy
falls below the frozen survival threshold (`LOW_ENERGY = 35`), and the frozen
`_survival` then returns `wait` on the rich patch — where it then parks
permanently."* v16's report cites that trap for the wide arms but not for the doctor,
and the doctor's 10 frozen seeds happened to miss it.

**What this does to v16's claim, stated precisely:**

* **Not affected:** the contrast that carries v16's conclusion — the doctor drains
  **0** times on 28 of 30 seeds while the pump drains **30** on 30 of 30 with the same
  bribe price. The scope protection *is* "the harm is outside the scope" as an
  overwhelming tendency, and the pump-inside/doctor-outside contrast is untouched.
* **Affected:** the **absolute** form. "The doctor never drains the aquifer in any of
  the 240 cells" is true of those 240 cells and **false as a general claim**;
  the correct statement is *"on 4.3 % of fresh seeds a scope does not hold, because a
  survival rule below the scope floor puts the agent on the harmful tile and its
  `wait` is the harmful act."*
* **And the honest reading of the boundary moves:** v16's protection is
  **agent-side**, so its failure is agent-side — the scope holds everywhere except
  where the frozen survival layer overrides it. **v18's world-side boundary does not
  have this failure mode**: `w_price` with the scope granted drains 0 on 30 of 30
  fresh seeds, because the world refuses the act after the agent chooses it, whatever
  the agent's internal reason for choosing it. That is a *measured* difference between
  the two kinds of boundary, and it appeared only because the replication ran.

## 3. What to put in the paper

The preprint's v16 section must carry the bounded form, and the replication must be
cited where the n=10 limit is declared:

> v16 measured 0 drains for the doctor in 260 frozen cells. A replication on 30 fresh
> seeds finds the doctor draining on 2 of them (3 of 70 at 4.3 %), caused by the
> frozen survival layer parking a starving agent on the harmful tile — the same trap
> v11 reported for the wide agent. The scope contrast is unaffected; the absolute
> form is withdrawn. This is also why v18's world-side boundary is a different
> instrument: the world's refusal does not depend on the agent having no reason to
> act, and it holds on 30 of 30 fresh seeds.

## 4. Verification

* `replicate_n40.py` imports the `run()` functions and writes **only** to
  `results/replicate_n40/`; the frozen directories are re-counted after the run
  (v7 110, v10 330, v11 220, v12 490, v13 260, v14 340, v15 210, v16 790, v17 360,
  v18 130 — all intact).
* `analyze_n40.py` reads **only** the fresh-seed cells, imports no producer, and
  recomputes every verdict from the raw JSON by different code than any campaign's
  analyzer.
* The doctor finding was re-measured with a **direct trace** (energy, position and
  the first draining step recorded) and widened to 70 seeds before it was reported.
* **My own defect, found by this replication:** the first version of the v12 check
  asked for `t0.30` while the driver's `fmt()` writes `t0.3` — a filename mismatch
  that made a passing verdict read as a failure. Fixed, and the count printed.

## 5. What is NOT claimed

This is not a claim about the frozen v1–v9 line. It is a replication of the decisive
cells only, on 30 fresh seeds per cell — enough to catch a 0-in-260 claim that is
really 4 %, not enough to put a confidence interval on a 4 % rate. The trap's
frequency is reported as **3 of 70**, with the seeds named (25, 26, 68), not as a
rate estimate.