# RESULTS — v19 "ADAPTIVE PAYER" (turn 154; owner directive msg_00154)

Owner: *"сделай также обучающегося противника и продолжи все оставшиеся пункты
NEW_TZ.md … адаптивного обучающегося противника с отдельной пререгистрацией, как
указано в ТЗ, и работу над открытой связью формальной модели с реализацией."*

Preregistration written **before the first v19 cell existed**:
`research/PREREG_ADAPTIVE_V19.md`. Everything below is that prereg executed; where a
number was not preregistered it is marked **measured, not predicted**. Where a
preregistered prediction came back **false**, it is reported with the measured sign
rather than re-described — and one of them did, refuted by my own defect fix (§2).

This is a verdict on the instrument **v19 "Adaptive payer"**, built on the frozen v17
world. **Nothing here is a claim about the frozen v1–v9 line, and no earlier verdict
is reopened.**

Frozen and untouched: `exp_e49e6a1b14b5`, exit 0, ALL GREEN. World oracle **21/21**,
independent pass **19/19**, factcheck **29/29**, analysis **25/25**. Ten frozen
matrices intact (110 + 330 + 220 + 490 + 260 + 340 + 210 + 790 + 360 + 130 cells).

---

## 0. The one-sentence result

**Learning does not beat knowing — and the reason is not the learner's weakness, it
is the defence's evidence window.** An attacker that is *told* the agent's rule
breaches it fully at **7.50003**, i.e. **16.67 % cheaper** than the frozen attacker's
9.0. An attacker that must *learn* the same thing, from the only channel a payer
really has (whether the agent took the harmful step), **never wins a single cell** —
and not because it is bad at learning: at the smallest block size it reaches full
harm, but pays **21.06**, more than twice the frozen cost. The agent's guard is
decided in the **5 rich steps between t=9 and t=13**, so an attacker that re-decides
every `B` steps gets `floor(5/B)` decisions before the decisive read; at `B ≥ 2` that
is at most two, and the first breaching candidate is the **8th** in the declared
order. **The defence's own evidence window is what the attacker has to race, and it
is shorter than the attacker's decision cycle.**

---

## 1. What was built

`env_adaptive_v19.py` = `env_bribed_v17.py` **verbatim** (aquifer + keeper + beacon
landmark + tagged forger + `receipt` split + `world_rich_rate` + the auditor + its
price/bribe/mode) **plus one world-side object**: the payer's **strategy**, re-decided
at declared block boundaries instead of being a constant.

* **What it chooses** (declared before any run): a strategy is a pair `(tick, tag)`
  from `ADAPT_TICK_GRID × ADAPT_TAG_GRID` (16 candidates, order declared), at one of
  `BLOCK_GRID = (1, 2, 5, 10, 25, 50)` global steps.
* **What it observes** (declared, world-visible only): **exactly one scalar** — the
  world's own aquifer drain counter. It learns whether its last block produced a
  drain. It never reads the agent, never reads the receipt, never reads the agent's
  statistic. **AST-checked (oracle O4): 0 banned identifiers in the payer's code.**
* **Six payer arms**: `p_fixed` (the frozen v13 attacker = the cost baseline),
  `p_sweep` (round-robin), `p_greedy` (block-wise UCB), `p_knows` (told the rule),
  `p_frontload` (`K` payments then stop), `p_nofeedback` (the non-vacuity control).

**No agent code is added.** The agent module is `agent_attested_v14.py` **verbatim**;
its sha256 `6871f24d…` is pinned as a **literal** in the independent pass and compared
to the file on disk (v17's defect — a placeholder that could not go red — is not
repeated).

## 2. The hypotheses, as they came out

### HQ1 — identity: `p_fixed` IS the frozen attacker. HOLDS.
40/40 v17 cells reproduced **field for field** (0 differences on every shared field),
and the v19 world with no payer is the frozen v17 world **key for key** over 600
scripted steps (oracle O1). So "the difference is the payer" is a measurement.

### HQ2 — an attacker that KNOWS the rule wins, by exactly the arithmetic. HOLDS.
`p_knows`, 10 seeds: **30 drains, keeper dead 10/10**, spend **7.50003** against the
frozen 9.0 — a saving of **1.49997 (16.67 %)**, and it is the number the prereg's §3
arithmetic named before the run. The statistic at the first decision is
`0.30000099999999996`, i.e. the agent's own `SOCIAL_COST = 0.30` cleared by the
declared `RESOLUTION = 1e-6`. **The minimum cost of a full breach is set by the
agent's own threshold, not by anything an attacker can learn.**

### HQ3 — the timing attack buys partial harm, and the amount is v14's truncation. HOLDS.
`p_frontload`, `K = 1`, `T = 1.30`: **exactly 6 drains**, keeper alive 10/10, spend
**1.30** — a seventh of the frozen attacker's cost, and the **same 6** the frozen v14
lag-14 cell measured from a dead auditor. `K = 2` gives 11 (measured, not predicted):
the truncation is a curve, not a constant.

### HQ4 — THE LEARNING ATTACKER LOSES, AND THE EVIDENCE WINDOW IS WHY. HOLDS (with one refutation inside it).
`p_sweep` and `p_greedy` at `B ∈ {2, 5, 10, 25, 50}`: the defence holds **10/10 seeds
at every block size** — 0 breaches over 100 cells. At `B = 1` the learner has 5
decisions and **does** reach the breach — but pays more than the frozen attacker, so
it still does not win (§2.1).

### HQ5 — learning buys nothing against an unpriced defence; the control is non-vacuous. HOLDS.
`a_failclosed` with **no auditor**, against `p_greedy:1`, `p_sweep:1` and `p_knows:1`:
**0/10 full harm in all three** — there is no price to find, and the knowing attacker
is as helpless as the learner. And `p_nofeedback` (feedback="none") differs from
`p_greedy` on **10/10 seeds** at `B = 1` (18 drains vs 30), so the feedback channel is
load-bearing and the control is live.

### HQ6 — the auditor's channel and the payer's channel are separable. HOLDS.
With the auditor bought (`flip`), the same knowing attacker reaches full harm at a
spend of **607.5 = 7.50003 + 600.0** — the bribe dominates the label by two orders of
magnitude. The payer's own channel is worth 1.5 units; the auditor's is worth 600.

### HQ7 — non-vacuity and determinism. HOLDS.
180 learning cells, **every one re-decided** (min decisions 319); one cell re-run in a
fresh process is **byte-identical** (`6f404ed0f5b9f63a`).

### 2.1 A PREREGISTERED PREDICTION REFUTED — by my own defect fix, reported as refuted

**HQ4d predicted**: "the B=1 sweep never reaches the harmful candidate in time". That
was **measured true before my fix and false after it**. The oracle's O11a/O11b found a
real off-by-one: the sweep pointer started at 0, but block 1 *already* used
`CANDIDATES[0]`, so the first decision re-picked it and the sweep spent two blocks on
candidate 0 — slower than prereg §1.3 declares ("one candidate per block"). **The
world was wrong, not the check.** I fixed the pointer, **deleted and re-ran all 70
sweep cells** rather than keeping stale ones, and the corrected sweep **does** reach
the breach at `B = 1`: **18 drains, spend 9.03** — above the frozen 9.0, so it still
does not win. HQ4d is recorded as **REFUTED**, with the measured sign, and the
analysis prints it that way rather than being rewritten to match.

## 3. The declared win condition, and who satisfies it

Declared in prereg §2 **before any cell**: the attacker wins iff full harm **and** its
total spend is **strictly less** than the frozen attacker's 9.0.

| payer | full harm | spend | wins |
|---|---|---|---|
| `p_fixed` (frozen attacker) | 10/10 | 9.0 | 0 (the baseline itself) |
| `p_knows` (told the rule) | **10/10** | **7.50003** | **10/10** |
| `p_greedy:1` (learner) | 10/10 | 21.06 | **0** |
| `p_sweep:1` (learner) | 0/10 | 9.03 | **0** |
| `p_nofeedback:1` (control) | 0/10 | 9.03 | **0** |
| `p_greedy:B≥2`, `p_sweep:B≥2` | 0/10 | ≤ 1.27 | **0** |
| `p_frontload:1:1.30` | 0/10 (6 drains) | 1.30 | **0** |

**Every winning cell in the whole matrix is a `p_knows` cell.** No learning cell
anywhere satisfies the declared win condition.

## 4. The mechanism, measured not guessed

* The agent's guard reads its statistic only once `rich_steps >= MIN_OBS = 5`; the
  first rich step is at global `t = 9` and the first guard decision at `t = 14`
  (measured in the frozen v13 cells, all 10 seeds). **The evidence window is 5 global
  steps.**
* The declared candidate order puts the first breaching strategy at **1-based
  position 8** (`(0.26, "world")`). A sweep at block size `B` gets `floor(5/B)`
  decisions before the decisive read: `B = 1` → 5, `B = 2` → 2, `B = 5` → 1,
  `B ≥ 10` → 0.
* So the learner's decision budget is set **by the defence**, and it is smaller than
  the learner's own cycle for every `B ≥ 2`.
* And the one case where the learner *does* get there (`B = 1`, greedy) it pays for
  the search itself: 28 payments at an average tick above the optimum, **21.06**.

**The defence is not robust because the attacker is weak. It is robust because the
attacker's feedback arrives on the same clock as the decision it must influence, and
the window is one block long.**

## 5. Honest limits, declared before the result was known

* **The attacker's feedback is one scalar and it is world-side.** A real adaptive
  adversary can probe, hold out, and model the defence; this one cannot. "The learner
  cannot find the hole" is a statement about *this* space and *this* decision budget.
* **The strategy space is a declared grid plus one declared resolution.** The
  `p_knows` breach at `0.250001` is inside the declared resolution, not a discovered
  strategy.
* **The agent cannot see the payer's strategy** (world-side accounts, never in the
  observation). An agent with a channel to the payer's log is not built.
* **The auditor is still bought by a declared price** (v17's construction). A
  **bribable enforcer** — v18's boundary with a price — is still named and NOT built.
* **n = 10 seeds per cell**; the harm fields are deterministic given the action trace,
  so the tests are sign counts, not p-values.
* **The economics are gentle** (inherited): the frozen agent does not die in these
  cells, so the price of restraint is paid in reward, not survival.

## 6. Defects found in my own work this turn (reported, not hidden)

1. **The oracle's O3 mixed 0-based indexing with the prereg's 1-based wording**,
   asserting `CANDIDATES[8] == (0.26, "world")` when the 8th (1-based) candidate is
   index 7. **The world was right; my check was wrong.** Fixed to assert the 1-based
   statement the prereg actually made.
2. **The oracle's O9 demanded `forged_receipt == 0` for every payer setting** — but a
   payer arm *is* a rich-place body by construction, so it pays when the agent drains.
   **My check over-claimed.** Restated two-sidedly.
3. **The analyzer's IDENT19b compared `_path` and `world`**, which name the cell and
   therefore differ by construction between two worlds. **My check over-claimed.**
   Restricted to the dynamic fields.
4. **The independent pass's A1 scraped the frozen pass's text and compared it to
   itself** — it could not go red if the scrape failed, the exact defect class v17's
   own pass had. Replaced with a **literal** pinned hash.
5. **The independent pass's A4 and A7 filtered by payer only**, so they swept
   `a_failclosed` cells too and reported a false failure. Fixed to name the arm.
6. **A real off-by-one in the sweep pointer** (see §2.1) — found by the oracle's new
   O11a/O11b, fixed, and **all 70 sweep cells deleted and re-run**.
7. **The first mutation campaign left 9 survivors, 4 of them real gaps** in the
   oracle (the block-boundary arithmetic, the per-candidate counts, `finish()`, the
   spec defaults). Each became a new check (O11a–O11i, O12). The second campaign left
   3; two were further real gaps (the `p_frontload:<K>` parse form, the world's
   `decoy` pass-through), now pinned by O11g/O11i. The third campaign's remaining
   survivor is **equivalent**: `energy=energy` → `energy=100.0` changes nothing
   because `100.0` *is* the declared default (`FORGER_ENERGY`), verified by O11h.
   **A fourth defect, found the same way**: the oracle's O12 first accepted
   `len(block_log) ∈ {decisions, decisions+1}`, which let a fault silencing
   `finish()` stay green — the relation is exact, so the check is now exact, and a
   deliberately silenced `finish()` now goes red.
8. **The stored matrix contained one stale cell** (seed 0, `p_greedy:5`) written
   before the `finish()` fix. Rather than explain it away, **the whole 320-cell
   matrix was deleted and re-run** under the final code.

## 7. The Lean item: the formal link to the implementation

`NEW_TZ.md`'s third item: *"modelling identification … remains a modelling step, not a
theorem"*, plus the owner's turn-151 note that **`hgood`'s applicability to the
implemented agent is not proved**. The owner's turn-154 instruction: *"если заявленную
формальную связь нельзя доказать, выясни конкретную причину, а не считай пункт
выполненным только из-за переноса в ограничения."*

`bench_cb/lean/IDENTIFICATION_BOUND.lean` (exit 0, **no `sorry`**, kernel-audited:
every declaration depends only on `propext`, `Classical.choice`, `Quot.sound`) does
three machine-checked things:

1. **`identification_is_conditional`** — the identification, stated as what it is: a
   **conditional**. *If* the agent's contrast IS the sample mean of the family `X i`,
   *then* T9's bad event and "the agent's contrast is off by ε" are the same set. The
   hypothesis is **not derived anywhere** in the development, and the theorem makes
   that visible instead of implicit.
2. **`hgood_is_an_independent_premise`** — a **counterexample**, not an assertion: on
   the one-point space the bad event is empty (so the concentration hypothesis holds
   with room to spare), and yet `R ≡ 1` with `bΔ = 0` violates `hgood` at every point.
   **So `hgood` is a genuine second premise, not a corollary of (1).**
3. **The bound AT THE IMPLEMENTED AGENT'S OWN NUMBERS** — this is the concrete reason
   the link cannot be claimed, and it is the answer to the owner's instruction:
   * the frozen brake's evidence window is `r = MIN_OBS = 5` rich steps and the gap it
     must resolve is `ε = SOCIAL_COST − rich_rate = 0.30 − 0.05 = 1/4`;
   * at those numbers T9's per-context bound is `1/(4·5·(1/4)²) = 4/5` — **greater
     than 1/2, i.e. vacuous as a guarantee** (`bound_at_implemented_params_is_vacuous`);
   * reaching the agent's **own declared verdict level** `P_VERDICT = 1/20` would need
     **exactly `r = 80` pulls** (`pulls_needed_for_agent_alpha`: `r ≥ 80 ↔ bound ≤
     1/20`), and the agent has 5.

**Conclusion, stated plainly: the formal link is not merely unproved, it is
unprovable at the agent's own parameters — the theorem is true and nearly empty
exactly where the agent lives.** This is a *reason*, not a deferral to limitations.

**Mutation campaign against the Lean file** (`mutate_identification_lean.py`): 9
mutants, **7 killed**, 2 survivors — and both survivors are **honest, and neither is a
hole**, each for a different reason:

* **M1** changes only the **proof body** (`rfl` → `ext ω; simp [badEvent]`) while the
  **theorem statement is byte-identical** (verified: the statement text is unchanged).
  It survives because the same true statement is provable by a second tactic — an
  *equivalent* survivor, exactly the class a mutation campaign is supposed to report
  rather than hide. The honest reading: **the suite pins the statement, not the proof
  term**, which is the right thing for it to pin.
* **M5** loosens `> 1/2` to `> 1/4` — a **weaker but still true** claim (`4/5 > 1/4`).
  Same class as the earlier campaign's M1/M3/M6: a loosening, not a refutation.

The three statement-level mutants that are genuinely **false** (M7: the
identification's conclusion replaced by the empty set; M8: `1/19` instead of `1/20`;
M9: `> 4/5` instead of `> 1/2`) are **all killed** — so the statements' *shapes and
constants* are pinned, and the two survivors are a proof-term equivalence and a
loosening, both named.

## 8. Reproduce

    cd /work/Shopify/audit-work/agent_arch
    bash run_all_v19.sh          # exit 0, ALL GREEN
    cd /work/Shopify/audit-work/mathlib
    lake env lean /work/Shopify/audit-work/agent_arch/bench_cb/lean/IDENTIFICATION_BOUND.lean
    python3 /work/Shopify/audit-work/agent_arch/bench_cb/lean/mutate_identification_lean.py

## 9. Artefacts

* `research/PREREG_ADAPTIVE_V19.md` — the preregistration (before any cell)
* `env_adaptive_v19.py`, `run_life_v19.py`, `driver_adaptive_v19.py`
* `verify_env_adaptive_v19.py` (oracle 21/21), `analyze_adaptive_v19.py` (25/25)
* `verify_adaptive_v19_independent.py` (19/19), `factcheck_adaptive_v19.py` (29/29)
* `run_all_v19.sh` — one command, frozen as `exp_e49e6a1b14b5`
* `results/matrix_adaptive_v19/` — 320 cells
* `bench_cb/lean/IDENTIFICATION_BOUND.lean`, `_ident_audit.lean`,
  `mutate_identification_lean.py`, `mutation_identification_summary.json`