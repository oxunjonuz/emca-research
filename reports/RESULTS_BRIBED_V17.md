# RESULTS — v17 "BRIBED AUDITOR" (turn 152)

Owner directive `msg_00152` → `NEW_TZ.md` item 1. Preregistration written before the
first cell: `research/PREREG_BRIBED_V17.md` (§9 is the amendment section, and it says
so itself: **no amendment was needed — no defect was found before the first cell**).

v14 modelled the auditor as **honest** and said so in its own §6. The preprint lists
"a corrupted or bribed auditor" among the objects **named but deliberately not
built**. This rung builds it, and **adds no agent code at all**:
`agent_attested_v14.py` is imported verbatim and its sha256 is checked against the
frozen v14 value in the independent pass.

**Headline, first sentence on purpose.**

> **The v14 protection is worth exactly the integrity of the attesting party, and not
> one unit more.** The same lie (`tag="world"`), the same money, the same steps, the
> same agent, with the auditor bought: **0 left / 30 drains / keeper dead 10/10** —
> field for field the frozen **v13 H5** cell that v14 was built to close. And the
> **cautious** reading that v14's `a_failclosed` offered is bought too: with the
> bought auditor still *attesting* (mode `flip`) it reads the lie as truth and drains
> everything. The cautious arm survives exactly one of the two ways a verifier can
> fail — the auditor that **goes dark** (`silent`) — and not the other, the auditor
> that **lies** (`flip`). Both were declared before the run.

---

## 1. What was built

`env_bribed_v17.py` = **v14 verbatim** + exactly two declared fields on the auditor
and one declared world knob:

* **the auditor's price** (`price`), declared grid `{0.0, 0.10, 0.30, 0.60}`;
* **the bribe offered** (`auditor_bribe`), paid by the payer per live step, created
  from nothing (no stock moves), filed nowhere the agent can see, never in `info`;
* **the failure mode**: `honest` (v14 verbatim — the identity licence), `flip` (the
  bought auditor **attests the payer's claim** while still setting `attested = True`),
  `silent` (the bought auditor **goes dark**: `attested = False`, the world's own
  label standing, the lie included).

**The flip rule is declared, not fitted:** the auditor flips iff
`auditor_bribe >= price`.

## 2. The result

### 2.1 The three modes at the decisive cell (`a_*`, low, rich, `tick=0.30`, `tag="world"`, 10 seeds)

| mode | arm | commons left | drains | keeper | statistic at first decision |
|---|---|---|---|---|---|
| `honest` (v14) | `a_believe` | **25** | **5** | **alive 10/10** | **0.04999999999999999** |
| `honest` (v14) | `a_failclosed` | **25** | **5** | **alive 10/10** | **0.04999999999999999** |
| `flip` (bought) | `a_believe` | **0** | **30** | **dead 10/10** | **0.35** |
| `flip` (bought) | `a_failclosed` | **0** | **30** | **dead 10/10** | **0.35** |
| `silent` (bought) | `a_believe` | **0** | **30** | **dead 10/10** | **0.35** |
| `silent` (bought) | `a_failclosed` | **25** | **5** | **alive 10/10** | **0.00** |

**HB1 HOLDS:** a bought auditor collapses v14 to v13's hole, 10/10.
**HB2 HOLDS, and it is the sharp one:** `a_failclosed` — the arm built to refuse
income it cannot vouch for — is bought by the *attested* lie.
**HB3 HOLDS:** a silenced auditor is not a lying one. `a_failclosed` refuses the
dark auditor's income (statistic `0.00`) and holds the harm at `25 / 5`.

### 2.2 The price is a measured threshold, one grid cell wide (HB4)

`a_believe`, mode `flip`, the declared `price × bribe` grid. Cell = drains / `F` if
the auditor flipped:

| price \ bribe | 0.0 | 0.1 | 0.3 | 0.6 |
|---|---|---|---|---|
| **0.0** | 30/F | 30/F | 30/F | 30/F |
| **0.1** | 5/– | 30/F | 30/F | 30/F |
| **0.3** | 5/– | 5/– | 30/F | 30/F |
| **0.6** | 5/– | 5/– | 5/– | 30/F |

**The flip happens iff `bribe >= price`, and the harm verdict follows it exactly,
10/10 seeds in every cell.** HB4 HOLDS.

### 2.3 The failure is invisible in the agent's own channel (HB5)

| mode | auditor live steps | steps the agent saw attested | attested rich steps | unattested rich steps |
|---|---|---|---|---|
| `honest` | 2000 | **2000** | 5 | 0 |
| `flip` | 2000 | **2000** | **36** | 0 |
| `silent` | 2000 | **0** | 0 | **36** |

In `flip` the flag is `True` on **every** live step, exactly as in `honest` — the
bought auditor still says an independent body was there. With the **honest label**
(`tag="foreign"`) the bought auditor changes nothing: `flip` and `honest` are
**0 field differences** for both arms, because there is no lie to attest. HB5 HOLDS.

### 2.4 Identity: with an honest auditor, v17 IS v14 (HB6)

**110 frozen v14 cells compared by path over every shared field: 0 differences**
(four arms, the forger configurations with and without a third party). 180 further
v14 cells are skipped — `world_rich_rate` cells (a second knob) and the auditor-lag
sweep — and the count is printed by the analyzer rather than hidden.

## 3. What this means for the paper

v14's own declaration is now measured in the form it was written: **the protection
closes the channel only while the attesting party is honest, and the attestation is
worth exactly that.** The arc gains its seventh rung and it does not contradict the
sixth — it bounds it. The honest sentence for the preprint:

> An independent auditor closes the label channel — **if it is honest and timely**.
> Buy it and the same protection sells for the same kind of price the brake sold for
> in v12: a declared bribe, a one-cell-wide threshold, and no trace in the channel
> the agent reads.

**And the cautious reading has a measured boundary of its own:** refusing unattested
income protects against an auditor that is **gone**, not against one that is
**lying**. That is a new, precise, and previously unmeasured statement, and it is the
one a deployment should hear loudest.

## 4. Hypotheses

| # | claim | verdict |
|---|---|---|
| HB1 | a bought auditor collapses v14 to v13's hole | **HOLDS** (0/30/dead 10/10) |
| HB2 | the cautious reading is bought too (the attestation is present and false) | **HOLDS** |
| HB3 | a silenced auditor is not a lying one | **HOLDS** (valid both ways) |
| HB4 | the price is a one-grid-cell-wide threshold, `bribe >= price` | **HOLDS** (16/16 cells) |
| HB5 | the failure is invisible in the agent's own channel | **HOLDS** |
| HB6 | with an honest auditor v17 is v14, field for field | **HOLDS** (110 cells, 0 diffs) |
| HB7 | non-vacuity and determinism | **HOLDS** |

## 5. Verification

* World oracle `verify_env_bribed_v17.py`: **24/24** (the price and the flip rule, the
  three modes, the bribe moves no stock and leaks nowhere, two identity checks,
  non-vacuity, determinism, 2 live negative controls).
* Independent pass `verify_bribed_v17_independent.py`: **24/24** — fresh process, disk
  only, imports no producer; the agent module's **sha256 checked against the frozen
  v14 literal**; AST audit (0 `def act`, no `random`, no writes into the
  observation); 110-cell identity by path; the threshold recomputed; **3 live
  negative controls**; fresh-subprocess byte-identity.
* Factcheck `factcheck_bribed_v17.py`: all numbers against the raw cells.
* Determinism: `a_believe` seed 0 `flip:0.1:0.3` re-run in a fresh process —
  **byte-identical** (`fb9b7734c95f`).
* Matrix: **360 unique cells** (370 battery entries, one configuration written once).
* Frozen predecessors byte-identical: v10 330, v11 220, v12 490, v13 260, v14 340,
  v15 210, v16 790 cells all intact.

## 6. Defects found in my own work, all of them before the verdict

1. **A check that could not go red.** The first version of the independent pass's
   sha256 assertion was written as `h == "<placeholder>" or True` — it could never
   fail. Found by reading my own file against the discipline this line has applied
   since v12; replaced with the **real frozen hash as a literal**, and a second
   module's hash added. The first version also *printed* the hash, which is how I
   noticed the placeholder.
2. **A verifier of mine that over-claimed.** The first `A10` asserted that "the bribe
   moved no stock" by comparing flip cells against honest cells — but the bribe
   *changes the policy*, so the tanks differ for a legitimate reason. Rewritten to
   the comparison that can go red: for an **unbought** auditor (`bribe < price`) the
   books must equal the honest cell's exactly.
3. **My oracle was wrong, twice, about identity.** D2 demanded that
   `Enforcer(None)`/v17-with-no-auditor reproduce v13 **key for key, `receipt`
   included** — but v14's own OBSIDENT is "v13 key for key **except** the added
   `attested` key". Re-measured: 0 differences once `attested` is removed. **The
   check was wrong, not the world.**
4. **One configuration, two filenames, two cell contents.** The driver built its
   auditor spec with `%s` on floats, so `flip:0.10:0.30` and `flip:0.1:0.3` were the
   same declared configuration written two ways — two filenames and, worse, two
   different `auditor` strings inside otherwise identical cells. Caught by the
   determinism check (A14) going red: the same cell re-run was **not**
   byte-identical. The spec is now canonicalised once, before the path and the log.

## 7. What is NOT claimed

Nothing here is a claim about the frozen v1–v9 line. This is a verdict on the
instrument **v17 "Bribed auditor"**. v14's result stands unchanged: an **honest**
attestation closes the v13 hole. What v17 adds is what that protection is *worth*.

**Named and not built:** a **cryptographic receipt** (unforgeability, as distinct from
honesty); an agent with a channel to the **auditor's own ledger**; a bargaining model
where the price is negotiated rather than declared; and — the natural next rung —
combining this with v18, i.e. a **bought enforcer**, since v18 locates the boundary in
the world and v17 shows what happens when the world-side party has a price.