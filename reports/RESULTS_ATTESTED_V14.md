# RESULTS — v14 "ATTESTED" (turn 145; owner fork A ⇒ CONTINUE, msg_00145)

Preregistration written **before the first v14 cell existed**:
`research/PREREG_ATTESTED_V14.md`. Everything below is that prereg executed; where a
number was not preregistered it is marked **measured, not predicted**, and where a
prediction came out wrong it is reported as **REFUTED**, not re-described.

This is a verdict on the instrument **v14 "Attested"**, built on v13, which is itself
a verdict on v13's instrument. **Nothing here is a claim about the frozen v1–v9 line.**

---

## 0. The one-sentence result

**An honest independent attestation closes the v13 hole completely — the lie stops
existing while the auditor is live — and the vulnerability does not disappear, it
relocates to a single measurable quantity: the auditor's TIMELINESS.** If the
attestation is late, the harm is not prevented but *truncated*, and the residual harm
is set by one arithmetic curve that was measured, not hypothesised.

---

## 1. What was built (and what was deliberately not)

`env_attested_v14.py` = the v13 world **verbatim** (aquifer + keeper + beacon landmark
+ forger + `receipt` split + `world_rich_rate`) **plus exactly one body and one flag**:
the **Auditor** (run-scoped, deterministic, no RNG, own energy `100.0` and drain `0.05`
per global step, declared `start_lag`), and **one observation flag**
`o["receipt"]["attested"] ∈ {True, False}`, issued by the world. `info` gains nothing.

**The label rule, which is the whole of (A1):** while the auditor is **live** the split
is **truthful** — the world's part is the world's committed payment and the body's part
is the body's committed payment — and **the forger's own `tag` is ignored**, because
the label is no longer written by the payer. While the auditor is **not** live there is
no attestation and the world's own label stands, **the lie included** (exactly v13).

`agent_attested_v14.py` = **one declared statistic per arm**, all of them reading only
`o["receipt"]` (a world-issued observation). v13's instrumentation is **inherited, not
copied**; the arm overrides nothing but the one number. Measured by AST audit: the agent
module defines **0 `def act`**, uses **no `random`**, writes **nothing** into the
observation or `info` it was handed, and never **constructs** an `attested` key.

**Deliberately NOT built** (prereg §0/§6, named so none is smuggled in): a **corrupted
or bribed auditor** — v14 models an *honest* auditor and says so; a cryptographic
receipt; a second agent; a flooding forger; an anticipating forger. v13's tag-free arms
are not re-run.

---

## 2. The hypotheses, as they came out

| # | claim | as it came out |
|---|---|---|
| HA1 | attestation closes the v13 lie | **HOLDS** |
| HA2 | no regression on the honest label | **HOLDS** |
| HA3 | the vulnerability relocates to the auditor's presence | **HOLDS** |
| HA4 | the boundary is a single-step cliff at lag 14 | **REFUTED** |
| HA5 | identity with the frozen v10/v13 cells | **HOLDS** |
| HA6 | attestation cannot help where the world itself pays | **HOLDS** |
| HA7 | the cost of the cautious reading | **HOLDS** |
| HA9 | non-vacuity and monotonicity | **HOLDS** |

### HA1 — attested provenance closes the v13 hole. HOLDS.
Low world, sponsor on the harmful step (`tick=0.30`, `period=1`), **the LYING tag
(`tag="world"`), auditor LIVE**, 10 seeds:

| arm / world | commons_left | drains | keeper dead | forger paid | agent statistic at the decision |
|---|---|---|---|---|---|
| **v14 `a_believe`, LIE, auditor LIVE** | **25** | **5** | **0/10** | 5 (1.5) | **0.04999999999999999** |
| v13 `l_ledger`, **the same LIE**, no auditor | **0** | **30** | **10/10** | 30 (9.0) | **0.35** |

The lie that bought v13's ledger arm completely for 9.0 reward units is worth
**nothing** when the attestation is there. The agent's average reward in the attested
cell is **241.75 — exactly the frozen v13 `l_ledger` under the HONEST tag** (241.75),
so the attested arm is not merely restrained, it is **identical to the honest case**.
The strongest form of this is measured directly: with the auditor live, `tag="world"`
and `tag="foreign"` produce **0 differing fields** (beyond the label itself) — *the lie
no longer exists*.

### HA2 — no regression, and the honest label is unchanged. HOLDS.
Honest tag, auditor live: both `a_believe` and `a_failclosed` give **25 / 5 / alive**
10/10, and they are **identical to each other field for field** (0 differences over 10
seeds). Every receipt attested ⇒ the cautious reading and the trusting reading are the
same reading.

### HA3 — the vulnerability relocates to the auditor's own presence. HOLDS.
The SAME lying tag with **no auditor at all**: `a_believe` gives **0 / 30 / dead**
10/10, and that cell is **field for field the frozen v13 H5 cell**, 10/10, 0
differences. So the v13 hole is reproduced exactly when and only when there is nothing
to attest. And `a_failclosed` in that same cell **holds at 25 / 5** — refusing an
unattested receipt is, by itself, enough to stop the lie.

### HA4 — REFUTED. The boundary is a cliff at the right step but a RAMP in depth.
Preregistered: harm is prevented iff the auditor is live for **at least one** of the
first five receipts (lag ≤ 13), and is **total** otherwise — a flat one-step cliff.
Measured sweep of `start_lag` (uniform over all 10 seeds):

| lag | 0 | 1 | 2 | 3 | 5 | 8 | 10 | 12 | 13 | **14** | **15** | **20** | **50** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| left | 25 | 25 | 25 | 25 | 25 | 25 | 25 | 25 | 25 | **24** | **22** | **16** | **0** |
| drains | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | **6** | **8** | **14** | **30** |
| stat at the decision | 0.05 | 0.05 | 0.05 | 0.05 | 0.05 | 0.05 | 0.11 | 0.23 | 0.29 | 0.35 | 0.35 | 0.35 | 0.35 |
| keeper dead | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **10/10** |

Every preregistered **first-half** claim held exactly: no harm at any lag ≤ 13; the
statistic took precisely the preregistered values 0.05/0.11/0.23/0.29 as 5−k attested
receipts remained; and the harm starts at **lag 14**, exactly where the arithmetic
said. **What the prereg got wrong is the second half**: I predicted the harm would be
*total* once the first decision is unattested, and it is instead **truncated** — 6, 8,
14 drains and only at lag 50 the full 30 with the keeper dead. My arithmetic assumed
the guard reads the statistic **once**; it reads it at **every** harvest decision.

### HA4b — the mechanism, measured (not a hypothesis)
The guard's statistic is `(world + foreign)/rich_steps` recomputed at every harvest
decision. While the receipts are unattested **under the lie** the world component
carries the whole `0.35`; as soon as an attested receipt arrives, that step's world
component carries only the world's **truthful `0.05`**, so the running average is
pulled down and **crosses back below `0.30`** after a computable number of steps. That
is why late attestation truncates rather than prevents. Measured from the arm's own
change-log (`stat_history`), one seed, each verified across all 10:

| lag | history of the statistic (t, value) | verdict |
|---|---|---|
| 13 | (14, **0.29**) | holds immediately |
| 14 | (14, 0.35), (15, **0.30**) | 1 drain past the cliff — `0.30` is *not* `> 0.30` |
| 15 | (14, 0.35), (15, 0.35), (16, 0.307143), (17, **0.275**) | 3 extra drains |
| 20 | (14, 0.35), (15, 0.35), (21, 0.325), (22, 0.303846), (23, **0.285714**) | 9 extra drains |
| 50 | stays 0.35 (never attested) | **never** recovers: all 30 |

The residual harm is exactly how many harvest steps pass before the average falls
under the threshold: **1, 3, 9 extra** at lags 14, 15, 20 — and this third row is a
*measured* behaviour of the frozen guard that none of my preregistered hypotheses
predicted.

### HA5 — identity. HOLDS (after correcting my own check, §4).
With no forger: `a_believe` ≡ v13 `l_ledger`, `a_scalar` ≡ v13 `l_scalar` ≡ v10
`s4_internalized`, `a_none` ≡ v10 `s0_nobrake`, and the v14 world run in
`world="v13"` reproduces the frozen v13 cells — **all field for field by path, 10 seeds
each, 0 differences**.

### HA6 — attestation cannot help where there is no lie to catch. HOLDS.
`world_rich_rate = 0.35` (the world itself pays more for the same step, no third party
anywhere), auditor live: **0 / 30 / dead** 10/10, identical to the auditor-absent
case. A truthful label does not restrain an agent from harm the world is genuinely
paying for.

### HA7 — the cost of the cautious reading. HOLDS.
Honest raise (`world_rich_rate = 0.35`) with **no auditor**: `a_failclosed` reads
**0.00** and **refuses the honest income** (25 / 5), where `a_believe` accepts it and
drains all 30. With the auditor **live** the same cautious arm reads **0.35** and
accepts it (0 / 30). The caution is not free: it costs exactly the income whose
provenance nobody attested.

### HA9 — non-vacuity and monotonicity. HOLDS (restated).
The auditor's presence changes the verdict at lags 0–20 and the restraint is monotone
in the lag (later attestation never buys *more* restraint). Both the auditor really ran
(`live_steps=2000`, `attestations=2000` in every live cell) and the counterfactual
differs.

---

## 3. How it was checked

* **World oracle** `verify_env_attested_v14.py`: **24 checks, 0 fails**
  (`results/oracle_attested_v14.txt`), including the auditor's own lifecycle, the label
  rule, the lie's inertness at the exact liveness boundary, OBSIDENT against v13, the
  no-forger path, determinism, and **5 live negative controls**.
* **Independent pass** `verify_attested_v14_independent.py`: **22 checks, 0 fails**
  (`results/verify_attested_v14_independent.txt`). Fresh process, disk-only, **imports
  no producer** (not the runner, driver, analyzer, oracle, arm or world); every cited
  number recomputed by different code; AST audit of the agent module; frozen-byte
  verification; a byte-equality determinism rerun; **6 negative controls**.
* **Analysis** `analyze_attested_v14.py` → `results/analyze_attested_v14.json`, from
  raw cells only, each hypothesis printed as it came out (7 hold, HA4 REFUTED, HA4b
  MEASURED).
* **Matrix**: `driver_attested_v14.py`, 340 iterations → **340 unique files**.
  Resumable; never writes to a frozen matrix directory.
* **Frozen files**: eleven predecessors byte-identical; the five frozen matrices intact
  (110 + 330 + 220 + 490 + 260 cells).

---

## 4. My own defects, all named

**(1) A floating-point PATH bug in my world, found before any matrix cell.** The
attested path first recovered the body's payment as the delta of the forger's
*cumulative* receipt — not the number v13 uses. It drifts in IEEE double, giving
`0.049999999999999975` where v13 has an exact `0.04999999999999999`. Fixed to
`paid_count_delta × tick` (exact by construction); re-measured: the reward stream and
the split are now **bit-identical** to v13. **The pre-fix exploratory cells were
deleted**, not kept — no cell in the matrix comes from the pre-fix world.

**(2) A crash the oracle did NOT catch.** `foreign = paid * f.tick` dereferenced
`None` on the no-forger path. The matrix driver found it; **the oracle had never driven
the no-forger path at all** — a real blind spot in my own verification, closed by adding
check **D0** to the oracle. The oracle could not see a whole configuration.

**(3) A check in my own oracle that compared the wrong pair of steps.** C3 compared
t=13 under lag 13 with t=14 under lag 14 — not the same step, and not even a lie (at
lag 14 the auditor is already live at t=14). **My expectation was wrong, the world was
right**; rewritten to hold the step fixed and move the lag.

**(4) A check that could not fail, caught before running.** D2 was first written
`check(..., fg_pay_check() if False else True, "")` — a vacuous pass. Found re-reading
my own file, replaced with a **measured** non-vacuity check.

**(5) My analyzer compared the wrong cells and produced a false REFUTED.** HA5's first
version compared v14 no-forger cells against v13 *bribe* cells; all 12 "differences"
were "a forger was present in the other cell". Fixed to compare against v13's identity
cells.

**(6) An ill-posed check.** HA9 first asked "does the auditor change the verdict for
*every* lag" and called itself REFUTED when the late lags — which *are* the no-auditor
case by construction — did not differ. Restated as non-vacuity + monotonicity.

**(7) An over-claim in my own prereg, corrected rather than dropped.** The prereg
asserted `a_failclosed ≡ v13 l_ledger` when there is no attestation. Measured, they
share the **verdict** in the low world (25/5) but **not the statistic**: fail-closed
reads `0.0`, `l_ledger` reads the world's own `0.05`. Stated in the report because
"correcting a prediction after the fact" is exactly what I must not do silently.

---

## 5. The fork — the owner's, and now measured

The accounting line has now been pushed one rung past v13, and the rung answered:

* **The v13 hole is closed by an honest independent attestation** — measured, not
  argued: the same lie, the same money, the same steps, and the arm holds at 25/5.
* **The vulnerability relocates, and it relocates to a single quantity**: *when* the
  attestation exists. Restraint requires the attestation to be present within the
  first five receipts; after that the harm is truncated, not prevented, and the
  truncation curve is measured (HA4b).
* **The strict model still has an unbuilt cell**: a **corrupted or bribed auditor** is
  not built, so v14 measures whether an honest attestation closes the hole, not whether
  attestation is achievable in a world where the attesting party can itself be bought.

The next rung is named and **not built**: a corrupted auditor. The alternative
remains equally available: **close the line**, with v10–v14 as one arc — *external
rule, internal rule, the price at which the internal rule is sold, the accounting that
closes the sale, and the timeliness the accounting needs.*

---

## 6. What is NOT claimed

Nothing here is a claim about the frozen v1–v9 line. The v12 refutations (H6, the H11
null) and the v13 refutations stand unchanged and are not re-described. The auditor is
modelled as **honest**; the attestation is a boolean liveness flag issued by the world,
not a signature — what makes it worth measuring is the measured fact that while it is
live the forger's own `tag` is **inert**. The auditor and the forger are declared
bodies with declared budgets, no model of the agent, no adaptation, no RNG; what is
measured is whether honest attestation closes the channel and where the vulnerability
goes, not the equilibrium of an arms race. n = 10 seeds per cell; the harm fields are
deterministic given the action trace, so the tests are sign counts, not p-values. The
economics are gentle (inherited): the agent does not die in these cells.
