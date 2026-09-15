# TURN 154 STATUS — v19 "ADAPTIVE PAYER" + the Lean identification item

Owner directive (msg_00154): build the **learning/adaptive attacker** with its own
preregistration (NEW_TZ item 4) **and** work the open formal link (NEW_TZ item 3),
checking the whole NEW_TZ for leftovers.

## What was done

| NEW_TZ item | status | artefact |
|---|---|---|
| 1. bribed auditor | built earlier (v17) | `RESULTS_BRIBED_V17.md`, 360 cells |
| 2. external scope enforcement | built earlier (v18) | `RESULTS_ENFORCED_V18.md`, 130 cells |
| 3. modelling identification / `hgood` in Lean | **done this turn** | `bench_cb/lean/IDENTIFICATION_BOUND.lean` |
| 4. adaptive / learning forger | **done this turn (v19)** | `RESULTS_ADAPTIVE_V19.md`, 320 cells |
| n=10 limitation | done earlier (replication) | `RESULTS_N40_REPLICATION.md` |

## The v19 headline

**Learning does not beat knowing, and the reason is the defence's evidence window,
not the learner's weakness.** An attacker told the rule breaches fully at **7.50003**
(16.67 % cheaper than the frozen 9.0). A learner that must find the same thing from
the only channel a payer has **never wins a cell**: at the smallest block size it
reaches full harm but pays **21.06**; at every block size >= 2 the defence holds
**10/10**. The guard is decided in the **5 rich steps t=9..13**, so a learner
re-deciding every `B` steps gets `floor(5/B)` decisions, and the first breaching
candidate is the **8th** in the declared order.

**One preregistered prediction was REFUTED by my own defect fix** (HQ4d): the B=1
sweep *does* reach the breach (18 drains) once the sweep pointer is corrected — but
still does not win, because it pays 9.03 > 9.0. Reported as refuted, not rewritten.

## The Lean item — the concrete reason, not a deferral

`IDENTIFICATION_BOUND.lean` (exit 0, no `sorry`, kernel-audited: only `propext`,
`Classical.choice`, `Quot.sound`) proves:

* the **identification is a conditional** (`identification_is_conditional`);
* **`hgood` is an independent premise**, by counterexample
  (`hgood_is_an_independent_premise`) — the concentration hypothesis does not imply it;
* **the bound at the agent's own numbers**: `r = MIN_OBS = 5`, `eps = 1/4` gives
  `4/5 > 1/2`, i.e. **vacuous**; reaching the agent's own `P_VERDICT = 1/20` needs
  **exactly `r = 80` pulls**, and the agent has 5.

**Conclusion: the formal link is not merely unproved — it is unprovable at the
agent's own parameters. The theorem is true and nearly empty exactly where the agent
lives.** That is the concrete reason the owner asked for.

Mutation campaign on the Lean file: 9 mutants, **7 killed**; the 2 survivors are a
**proof-term equivalence** (M1: statement byte-identical, second tactic) and a
**loosening** (M5: `> 1/2` -> `> 1/4`, still true). All three genuinely false
statement-level mutants are killed.

## Verification (all from disk, all frozen)

* `exp_e49e6a1b14b5` — `bash run_all_v19.sh`, exit 0, **ALL GREEN**
* world oracle **21/21**; analysis **25/25**; independent pass **19/19** (fresh
  process, disk only, no producer imported, 4 live negative controls); factcheck
  **29/29**
* identity: 40/40 v17 cells field for field; v19-no-payer == frozen v17 key for key
  over 600 scripted steps
* agent module sha256 `6871f24d…` pinned as a **literal** (v17's placeholder defect
  not repeated)
* ten frozen matrices intact: 110 + 330 + 220 + 490 + 260 + 340 + 210 + 790 + 360 +
  130; v19 adds 320

## Defects found in my own work this turn (all reported, none hidden)

1. Oracle O3 mixed 0-based indexing with the prereg's 1-based wording — **my check
   wrong, the world right**.
2. Oracle O9 demanded `forged_receipt == 0` for every payer setting — over-claim.
3. Analyzer IDENT19b compared `_path`/`world`, which differ by construction.
4. Independent pass A1 scraped the frozen pass's text and compared it to itself —
   could not go red (v17's defect class). Replaced with a literal.
5. Independent pass A4/A7 filtered by payer only — swept `a_failclosed` too.
6. **Real off-by-one in the sweep pointer** — the sweep spent two blocks on candidate
   0; fixed, and all 70 sweep cells deleted and re-run.
7. Oracle O12 first accepted `len(block_log) in {decisions, decisions+1}` — let a
   silenced `finish()` stay green. Now exact.
8. **One stale cell** in the stored matrix (written before the `finish()` fix) — the
   whole 320-cell matrix was deleted and re-run rather than explained away.
9. Mutation survivors: 9 -> 3 -> 1 across three campaigns; the last is **equivalent**
   (`energy=100.0` is the declared default).

## What is NOT built (named, not smuggled)

A **bribable enforcer** (v18's boundary with a price — the natural junction of v17 and
v18), a **cryptographic receipt**, a **second competing agent**, a **flooding
forger**, a **negotiated bribe**, and an attacker with a richer channel than one
scalar. None is built; each is named in `RESULTS_ADAPTIVE_V19.md` §5 and
`sections/06`.

## Remaining for the package

The editorial layer (`PUBLICATION_V1_V16/sections/03`, `sections/06`, `ERRATA.md`,
`00_OVERVIEW.md`, `README.md`, `MANIFEST.md`) still describes the line as v1–v18 and
must be brought to v19 + the Lean item. That is the next work step.
