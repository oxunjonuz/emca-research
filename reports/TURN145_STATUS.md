# TURN 145 STATUS — v14 "ATTESTED" (owner fork A ⇒ CONTINUE, msg_00145)

## What was asked, and what I read it as

Owner: *"вариант А Продолжить исследование — добавить учёт «кто кому платил»."*

**A note on the record.** This text is word-for-word the directive that produced v13
"LEDGER" (msg_00143), whose result and fork are frozen on disk
(`research/RESULTS_LEDGER_V13.md`, matrix `results/matrix_ledger_v13`, 260 cells,
artifacts written 21:11–21:13 today). v13's §5 named the fork in two sides: **(A1)
attested provenance** — an independent auditor or an unforgeable receipt, so that
"who paid whom" is not issued by the party being defended against — and **(A2) close
the line**. I read this message as naming the side: **CONTINUE**, i.e. not (A2). The
strictly stronger object v13 declared in §0/§5 and did **not** build is the attested
ledger, so that is what this turn built. **If I read the message wrong, the whole of
v14 is the wrong rung** — say so and I will close the line instead; nothing frozen was
touched either way.

## What was built

* `research/PREREG_ATTESTED_V14.md` — written **before the first v14 cell**; §9 is the
  amendment section (typed before the matrix), recording the two pre-cell changes.
* `env_attested_v14.py` — v13 **verbatim** plus **one body and one flag**: the
  `Auditor` (run-scoped, deterministic, no RNG, own energy/life, declared `start_lag`)
  and `o["receipt"]["attested"]`, issued by the world. **While the auditor is live the
  split is truthful and the forger's own tag is IGNORED; while it is not live the
  world's own label stands, the lie included.** `info` gains nothing.
* `agent_attested_v14.py` — four arms, **one declared statistic each**, all reading only
  `o["receipt"]`. v13's instrumentation is **inherited, not copied**. The agent
  **constructs nothing**: AST-audited 0 `def act`, no `random`, no writes into the
  observation or `info`, never constructs an `attested` key.
* `run_life_v14.py`, `driver_attested_v14.py` (340 iterations → **340 cells**),
  `verify_env_attested_v14.py` (**24 checks**), `verify_attested_v14_independent.py`
  (**22 checks**, fresh process, disk-only, imports no producer),
  `analyze_attested_v14.py`, `factcheck_attested_v14.py` (**20 numbers**),
  `run_all_v14.sh`.

## The result

**The v13 hole closes.** The same lie (`tag="world"`), the same money, the same steps,
with the auditor live: **25 left / 5 drains / keeper alive 10/10**, statistic
`0.04999999999999999` — where v13 with the identical lie gave **0 / 30 / dead**. With
the auditor live the lying and honest tags produce **0 differing fields**: the lie
stops existing. The attested cell's average reward (241.75) is **exactly** the frozen
v13 `l_ledger` under the **honest** tag.

**The vulnerability relocates, and it is one measurable quantity: timeliness.** With no
auditor the v14 cell is **field for field the frozen v13 H5 cell**. The lag sweep shows
harm beginning exactly at the preregistered step (lag 14) but **truncated rather than
total**: 6 / 8 / 14 drains at lags 14 / 15 / 20, full 30 only at lag 50. The mechanism
was **measured** from the arm's own change-log: the guard re-reads its statistic at
every harvest decision, so once an attested receipt arrives the running average
self-corrects and crosses back under the threshold — after 1, 3 and 9 extra harvest
steps respectively.

## Hypotheses

| HA1 | closes the lie | **HOLDS** |
| HA2 | no regression | **HOLDS** |
| HA3 | relocates to the auditor's presence | **HOLDS** |
| HA4 | flat cliff at lag 14 | **REFUTED** (harm starts at 14 exactly, but is truncated, not total) |
| HA5 | identity with frozen cells | **HOLDS** |
| HA6 | no help where the world itself pays | **HOLDS** |
| HA7 | cost of the cautious reading | **HOLDS** |
| HA9 | non-vacuity + monotonicity | **HOLDS** |

## My own defects (7), all named in the report §4

1. A floating-point PATH bug in the attested split (cumulative delta vs exact `pay`) —
   found **before** the matrix; pre-fix cells **deleted**.
2. A `None`-dereference crash on the no-forger path that **my oracle had no check
   for** — a real blind spot in my own verification, closed by adding check D0.
3. An oracle check (C3) comparing two *different* steps — **my expectation wrong, the
   world right**.
4. A check that could not fail (`if False else True`) — caught re-reading my own file.
5. An analyzer check comparing v14 no-forger cells against v13 *bribe* cells → a false
   REFUTED of HA5; fixed to compare like-for-like.
6. An ill-posed HA9 check (asked a question whose "failure" was the design).
7. An **over-claim in my own prereg**, corrected in the report: `a_failclosed` with no
   attestation shares the *verdict* with v13 `l_ledger` but **not the statistic**
   (0.0 vs 0.05).

## The fork, and what is NOT built

The next rung is named and **not built**: a **corrupted or bribed auditor** — v14
models an *honest* auditor, so it measures whether honest attestation closes the hole,
not whether attestation is achievable. Also unbuilt: a cryptographic receipt, a second
agent, a flooding forger, an anticipating forger. The alternative stays available:
**close the line**, with v10–v14 as one arc.

Nothing here is a claim about the frozen v1–v9 line. Eleven predecessor files are
byte-identical and the frozen matrices intact (110 + 330 + 220 + 490 + 260 cells).
