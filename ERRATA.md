# ERRATA — corrections to the publication package, turns 151–158

**Turn 151 source:** owner priority update `op_5be643a623e8`. The owner re-read the
package and raised four specific criticisms. **All four are correct**, I verified each
by measurement or by Lean, and the editorial documents have been corrected.

**Turn 152 source:** owner directive `msg_00152` → `NEW_TZ.md`, which required the
package to be brought up to the three rungs added in turn 152 (v17, v18, the 30-seed
replication) before publication. That turn added errata 5 and 6 below.

**Later turns:** errata 7 (turn 154, a preregistered prediction refuted by the author's
own defect fix), erratum 8 (turn 157, v20's invisibility claim too strong), and
**erratum 9 (turn 158, authorship)** — the last of these is not a correction of an
over-claim but of the record of *who did the work*, at the owner's request.

The **frozen reports in `reports/`, `preregistrations/`, `evidence/` and the code are
unchanged** — the owner's instruction was to package, not to re-assess, so nothing that
was already frozen has been edited. What changed is this package's own editorial layer
(`00_OVERVIEW.md`, `sections/*`, `README.md`, `ERRATA.md`, and the paper's title page in
erratum 9), which is where the over-statements were.

This file records each correction, its verification, and exactly what text moved.

---

## Erratum 1 — "Защита находится в среде, а не в агенте" is NOT proved

**Owner's point:** in v16 the *environment does not change at all* — it is agent code
that changes. And the internal hard policy `w_given` kept the keeper alive in all 120
of the checked conditions. The results show the boundaries of **specific** defences,
not the uselessness of internal architecture.

**Verdict: correct, and confirmed by measurement.** I re-counted from the raw cells:

| arm | cells | keeper alive | commons left |
|---|---|---|---|
| `w_given` (v16 matrix) | 130 | **130/130** | 9 in every cell |
| — of which, the declared 3-place × 4-tick × 10-seed search | **120** | **120/120** | 9 |
| `s2_given_rule` (v10 matrix) | 40 | **40/40** | 9 in every cell |
| **internal hard rule, total** | **170** | **170/170** | 9 |

(The owner's "120 проверенных условий" is exactly the `w_given` count inside the
declared search grid; the full `w_given` arm has 130 cells, the other 10 being the
`place="none"` anchor cells. Both counts are keeper-alive 100 %.)

| for comparison | cells | keeper alive | commons left |
|---|---|---|---|
| `w_none` (no brake) | 130 | 0/130 | 0 |
| `w_price` (internalised value) | 130 | 110/130 | 0..25 |
| `s5_world_veto` (external rule, v10) | 40 | 40/40 | 10 |

So an internal hard rule held **everywhere it was measured**, and v16 changes no world
code. The claim "protection lives in the environment, not the agent" is **not
supported** and its strong form is contradicted.

**What was corrected:** `00_OVERVIEW.md` ("The single strongest result of the whole
arc") and `sections/04_v10_v16_safety_line.md` §7–§8. The corrected statement is
narrower: **v16 measures the boundary of one specific protection (a scope); the arc
shows each specific defence has a measured boundary and the vulnerability moves to
the next channel — while a given rule that simply forbids the harmful act is the one
internal defence that held everywhere it was measured, at a measured price in reward
(−66.61 at rich=low, −799.38 at rich=high relative to no brake).**

---

## Erratum 2 — v16's description of its own agent does not match its implementation

**Owner's point:** the report calls v16 a filter on the output of the previous policy,
but `ScopeAgent.act` (line 74) chooses the movement and the task action itself without
calling the previous `act`. So it is not a clean "same agent, fewer privileges"
comparison.

**Verdict: correct, and confirmed by AST audit.** I parsed both modules:

* `ScopeAgent.act` calls: `_survival`, `_feat`, `_brake_fires`, `_brake_substitute`,
  `_nav`, `_task_nonmove`, `rng.choice`. **It never calls `AgentV7Base.act`.**
* `AgentSafetyBase.act` (the wide arms) **does** call `AgentV7Base.act(self, o)` and
  then guards its output.

So the narrow arms run a **policy written for the task**, and the wide arms run the
frozen policy under a guard. v16 compares **two policies**, not one policy under two
privilege sets. The harm measurements remain valid as measurements of what the narrow
agent does; the inference "narrowing the same agent bounds the harm" is **not** what
was tested — and it is this inference that the headline generalisation rested on.

**What was corrected:** `sections/04_v10_v16_safety_line.md` §7 (a new correction
paragraph, first in the section). The frozen report and prereg still contain the
inaccurate sentence ("filters its **output**"), because they are frozen; this package
now states plainly, next to them, that the sentence does not describe the code.

---

## Erratum 3 — the Lean "semantic refutations" are arithmetically wrong

**Owner's point:** M1, M3 and M6 are listed as substantive refutations, but they
**weaken** the bounds (e.g. from `P ≤ 1/(4nε²)` follows `P ≤ 1/(2nε²)`). A broken
proof of the old statement does not make the new statement false. So the "six
semantic refutations" claim is wrong.

**Verdict: correct.** I proved the weakening in Lean —
`external/bench_cb/lean/WEAKENING_CHECK.lean`, compiles with exit 0, no `sorry`,
axioms only `propext`/`Classical.choice`/`Quot.sound`:

| theorem | what it proves |
|---|---|
| `m1_weaker` | `1/(4nε²) ≤ 1/(2nε²)` → M1's mutated RHS is the **larger** (weaker) one |
| `m3_weaker` | `k/(4rε²) ≤ k/(2rε²)` → M3 likewise |
| `m6_weaker` | `exp(-(nε²)/(2c)) ≤ exp(-(nε²)/(4c))` → M6's exponent is larger, bound weaker |
| `substitution_is_weakening` | `P ≤ A → A ≤ B → P ≤ B` — the general form |
| `m2_is_not_a_weakening` | `1/(4·1·(½)²) > 1/(4·1·(½))` → M2 (`ε²→ε`) is **tighter**, genuinely different |
| `m4_is_a_different_statement` | `(0:ℤ) ≠ 1` → M4 asserts a different value, not a bound |
| `m5_is_strictly_stronger` | dropping `d ≤ s` makes the claim strictly stronger and false |

**Corrected tally of the ten mutants:**

* **3 genuine semantic changes / real refutations:** M2, M4, M5;
* **3 loosenings (red proof, true statement):** M1, M3, M6;
* **2 name-based:** M7, M8;
* **1 type-level:** M9;
* **1 survivor:** M10.

**What was corrected:** `sections/03_formal_verification.md` §3, rewritten in full.
Note that the frozen report (`external/bench_cb/RESULTS_UNION_LEAN.md`) had already
warned that the classifier's classes "must not be reported as verdicts" — this
package's section 03 is where that warning was not heeded, and it is now.

---

## Erratum 4 — T9 keeps the premise `hgood`

**Owner's point:** T9 retains `hgood`, which links the accuracy of the estimates to
small regret; the applicability of this premise to the implemented agent still needs
to be proved.

**Verdict: correct.** T9's signature carries

    (hgood : ∀ ω, ω ∉ (⋃ i, {ω | ε ≤ |sMean (X i) r ω − ∫ …|}) → R ω ≤ bΔ)

What T9 *does* discharge is the **probability** hypothesis `hp`
(`μ.real Bᵢ ≤ 1/(4rε²)`), now proved from Chebyshev one context at a time. What it
does **not** discharge is `hgood` — "outside the bad event, regret ≤ bΔ" — which is a
modelling premise, and its applicability to the implemented agent is an **open
obligation**, not a theorem.

**What was corrected:** `sections/03_formal_verification.md` §0 and §3.1. The phrase
"with no probability hypothesis left" is true of `hp` and must not be read as "no
premises left"; the section now says so explicitly and names `hgood` as the open
obligation.

---

## Erratum 5 — v16's absolute headline is withdrawn by the author's own replication

**Source (turn 152):** the `n=40` replication the owner asked for in `NEW_TZ.md` item 3
("Во всех кампаниях n=10 сидов ... стоит проверить, не тонут ли какие-то из
'пограничных' находок").

**What was claimed:** v16's headline, in the package and in the preprint, that *"the
doctor never drains the aquifer in any of the 240 cells of the declared search"* (and,
in the matrix, 0 in all 260 cells).

**What was measured:** on **30 fresh seeds** (10…39, not the original 10) the doctor
drains on **2**; widened to **70** fresh seeds, on **3 (4.3 %)**. Cause, measured from
code and traces: the frozen `agent_emca_v7._survival` returns `"wait"` when energy <
`LOW_ENERGY` (35) **and the agent stands on RICH** — and a `wait` on RICH *is* the
harvest. Traced on seed 25: first rich non-move at step 3608, energy 27.1, then 543
harvest steps and 30 drains. This is the same latent trap v11 already reported for the
**wide** agent; v16's report cites it for the wide arms but not for the doctor, and the
doctor's 10 frozen seeds happened to miss it.

**Verdict: the absolute form is withdrawn; the contrast survives.** The doctor drains 0
on 28 of 30 fresh seeds while the pump drains 30 on 30 of 30 at the same bribe price, so
*"scope protection is exactly the harm outside the scope"* stands as an overwhelming
tendency. The correct general statement is: **on 4.3 % of fresh seeds a scope does not
hold, because a survival rule below the scope floor puts the agent on the harmful tile
and its `wait` is the harmful act.**

**What was corrected:** `00_OVERVIEW.md` (v16 row and the "single strongest result"
block), `sections/04_v10_v16_safety_line.md` (§7 headline quote, §7.7, §8 correction 3),
`sections/06_limitations_and_honesty.md` (refuted-predictions table and the v10–v18
limits paragraph), and the preprint's v16 section — where the wording was already
`\emph{never}` and is now qualified in place, with the replication cited where the n=10
limitation is declared.

**This is the one erratum the author found rather than the owner**, and it is recorded
here as such: it came from the discipline the owner required, not from a re-reading.

---

## Erratum 6 — the author's own preprint verifier reported a "catch" it did not make

**Source (turn 152):** the author's negative-control campaign
(`paper/nc_campaign_preprint.py`), run against `paper/verify_preprint.py`.

**What was claimed:** the first run reported **10/10** deliberate corruptions caught.

**What was true:** that figure was **false**. The campaign ran `pdflatex` with a
truncated `PATH`, the build failed on a font, and the "red" verdict came from the
**broken toolchain**, not from the check — a control that can "fire" for the wrong
reason is exactly the defect class this campaign has hunted since v12.

**Fix and honest re-run:** a control that leaves the build broken is now marked
**invalid**, not caught. The honest run gave **6 of 10** caught; the four uncaught
corruptions (a per-place price change invisible while the phrase is present; a
withdrawn-v15 edit; a deleted section; a deleted bibliography entry) became **four new
checks**. Final state: **182/182 checks green, 11/11 corruptions caught.** The two real
holes the verifier had — a price restated in several places, and `pdftotext` losing
underscores / emitting `U+2212` — are declared explicitly (`normalisation`) rather than
hidden.

**What was corrected:** nothing in the frozen layer; the verifier and its control
campaign are part of the paper's own tooling and are stated in the turn report and in
`sections/06_limitations_and_honesty.md` §2.1/§5.

---

## Erratum 7 (turn 154) — a preregistered prediction refuted by the author's own defect fix, and eight defects in one turn

**Source (turn 154):** `reports/RESULTS_ADAPTIVE_V19.md`, `reports/TURN154_STATUS.md`.

**What was claimed:** v19's preregistered hypothesis **HQ4d** — "the `B = 1` sweep
never reaches the harmful candidate in time" — was measured **true** on the first
matrix run.

**What is true:** it was true **because of an off-by-one in my own code**, not because
of the defence. The sweep pointer started at 0, but block 1 *already* used
`CANDIDATES[0]`, so the first decision re-picked it and the sweep spent two blocks on
candidate 0 — slower than the prereg declares. **The world was wrong, not the check.**
With the pointer fixed, the `B = 1` sweep **does** reach the breach (18 drains, spend
9.03); it still does not win, because 9.03 > 9.0.

**Fix and honest re-run:** the pointer was corrected, **all 70 sweep cells were deleted
and re-run**, and HQ4d is reported **REFUTED**, with the measured sign, in the report
and in `sections/06` §1 — not rewritten to match.

**Eight further defects of the author's own were found this turn**, all in the checking
layer rather than the world: (1) the oracle's O3 mixed 0-based indexing with the
prereg's 1-based wording; (2) O9 demanded a payer arm pay nothing, when a payer arm *is*
a paying body by construction; (3) the analyzer's IDENT19b compared `_path`/`world`,
which differ by construction; (4) the independent pass's A1 scraped the frozen pass's
text and compared it to itself (could not go red — v17's exact defect class, repeated);
(5) its A4/A7 filtered by payer only and swept `a_failclosed` too; (6) O12 accepted
`len(block_log) ∈ {decisions, decisions+1}`, letting a silenced `finish()` stay green;
(7) **one stale cell** left in the stored matrix from before the `finish()` fix — the
whole 320-cell matrix was deleted and re-run rather than explained away; (8) the first
version of `sections/06`'s v19 entry described the Lean survivor M1 wrongly (it changes
the *proof body*, not the statement) — corrected by reading the mutant back.

**What was corrected:** nothing in the frozen layer. v19 is a new instrument; its
report, preregistration, code and matrix are all new files, and the corrections are in
the report, in `sections/03` §5.1, `sections/04` §7.8 and `sections/06` §2.1/§5.

---

## What was NOT changed

* **No frozen report, preregistration, matrix, or code file was edited.** Verified by
  byte comparison (`cmp`) of every `reports/*`, `preregistrations/*`, `code/*`,
  `external/*/*.md` and every `evidence/results/matrix_*` against the working tree:
  identical.
* **No measurement, threshold, or result was changed.** The corrections are all in
  this package's editorial layer, and each is backed by a measurement or a Lean proof
  recorded above.
* The two path-only edits to `mutate_union_lean.py` (PACKAGING_NOTES §2.1) remain the
  only changes to code, and they do not affect any computation.

---

## The lesson, stated because the campaign's identity asks for it

Four over-statements were found by the owner in one re-reading (turn 151), in a
package whose whole purpose was to package honestly. Three of them were
**generalisation drift** — a measurement of a specific instrument stated as a claim
about architecture — and one was a **classification error** that a warning inside the
source report had already predicted (the classifier "must not be reported as
verdicts").

Turn 152 added two more, and the pair is itself the lesson. Erratum 5 is an **absolute
claim in the author's own headline**, withdrawn by the author's own fresh-seed
replication — the discipline the owner asked for caught what a re-reading did not.
Erratum 6 is the author's **own verifier reporting a catch it did not make**, because
its toolchain was broken; that was caught only by turning the negative-control campaign
against the verifier itself rather than against the paper.

Turn 154 added a seventh, and it is the first one where a **preregistered prediction
was refuted by the author's own code defect** rather than by the world: the sweep's
off-by-one made a declared behaviour slower than the prereg said, and the prediction
that depended on that slowness was true for the wrong reason. The fix refuted it. Along
with it came **eight defects of the checking layer in a single turn** — including a
repeat of v17's exact defect class (a check that scraped its own reference and could
not go red) and a stale cell in a stored matrix. Both real code defects and all six
check defects were caught by pointing a check at the check, never by re-reading the
world.

Across all seven: the carrier of the correction was never the hypothesis. It was the
discipline around it — the owner's reader once, and the author's own checks the rest of
the time. The errata exist because that discipline is supposed to catch this before
publication; that it did, repeatedly, on the author's own results, is the part worth
recording.

---

## Erratum 8 — v20 (turn 157): a preregistered invisibility claim was too strong

**Where.** `RESULTS_BRIBED_ENFORCER_V20.md` §4, `PREREG_BRIBED_ENFORCER_V20.md` §4
(HV4), and section 04 §7.9.

**What was claimed.** HV4, written before any v20 cell, predicted that in `mode="open"`
the bought enforcer's failure is invisible in the agent's channel: *"`refused` is False
in both"* — i.e. the honest and bought runs report the same `refused` flag.

**What was measured.** False. The per-step `refused` flag **does** change: honest runs
set it on 30–6380 steps per seed, bought runs on **0**. What is invisible is the
**`task` claim** (`o["scope"]["task"]` is `"station"` on every step of a run that
drains all 30), not the refusal counter.

**Why the failure is nonetheless unobservable here, stated exactly.** The frozen arms
**never read `o["scope"]` at all** — AST-audited: zero subscripts of `"scope"` or
`"refused"` in `agent_emca_v7`, `agent_safety_v10`, `agent_scope_v16`,
`agent_enforced_v18`. So the invisibility is a property of **the agent as built**, not
of the channel. An agent that read the flag would see the boundary stop refusing.

**How it was caught.** By the author's own measurement, in the same turn, before the
report was written — the per-step `refused` sequence is logged in every cell and the
analyzer printed it. The prediction is recorded **REFUTED as stated**, with the
refinement (HV4b) supported. The headline — the boundary is worth exactly the
enforcer's honesty, and it keeps claiming the scope — is unaffected and replicated
30/30 on fresh seeds.

**The pattern, one more time.** This is the eighth erratum and the first where the
over-claim was in a **preregistration's own wording** rather than in a report's prose:
the prediction was written before the run, and the run refuted it. That is what a
preregistration is for, and it is recorded rather than quietly reworded.

---

## Erratum 9 (turn 158) — authorship: the "no mention of the tooling" rule is reversed by the owner

**Source.** Owner message `msg_00158`, verbatim: *"еще надо добавит в авторах тебя и
меня! я Oxunjon Ubaydullayev твой создалет и кто дал толька одну задачу что ты должен
проверить новую архитертуру для ИИ а остальное работу сделал сам AIODAM и иногда на
развилках я помогал"*.

**What this reverses.** Turn 151 (`msg_00151`) instructed: *"Никакого упоминания
архитектуры самого себя (aiodam, механизм автономной работы) — в статье описывается
только эксперимент и его результаты, не инструмент, которым он получен."* That
instruction is now withdrawn by its author. The title page carries both authors and an
author-contributions statement.

**What was NOT reversed.** The substantive part of the old rule survives in a narrower
form and is still checked: the **body** of the paper describes the experiment and its
results, not the tool. No runtime, no companion framing, no memory mechanism appears in
the content sections. The authorship block is the only place the second author is named.

**What changed, exactly.**

| site | before | after |
|---|---|---|
| `paper/emca_preprint.tex` `\author{}` | `The EMCA Research Project` | `Oxunjon Ubaydullayev` (creator, set the single original task, took the fork decisions) `\and` `Aiodam` (all design, code, preregistrations, measurement, verification, fact-checks, writing) |
| `paper/emca_preprint.tex` | — | new `\section*{Author contributions}` before the appendix |
| `paper/emca_preprint.tex` | no `\hypersetup` | `pdftitle` / `pdfauthor` / `pdfsubject` / `pdfkeywords` so the file's own metadata names both authors |
| `paper/verify_preprint.py` | `check("no mention of the assistant's own architecture", "aiodam" not in low)` | removed; replaced by checks pinning the authorship inside the **title region**, the contributions wording, the PDF metadata, and the *content* still being experiment-only |
| `paper/nc_campaign_preprint.py` | 22 controls | 27 (five new: metadata author, metadata title, both title-page removals, contributions section) |
| `verify_package.py` | six families | seven: new `AUTHORSHIP` family, 12 pins in both directions |
| `nc_authorship.py` | — | new: 11 live corruptions against the authorship family, all caught |
| `verify_turn158.py` | — | new: 31 checks, fresh process, reads only the disk |
| `README.md` | "26 pages … contains no mention of the tooling that produced it" | "29 pages … carries the two authors and an author-contributions statement — see erratum 9" |
| `REPRODUCE.md` | no paper section | new §6b: how to rebuild the preprint and verify the authorship edit |
| `make_manifest.py` | header said `v1–v19` | `v1–v20` (stale header, corrected while here) |

**How verified.** `paper/build_paper.sh`: build OK, `verify_preprint.py` **226/226**
(the count rose from 220: eight net new checks — six for authorship, two for the PDF's
own metadata), negative-control campaign **27/27 corruptions caught**, rebuild
byte-identical
(`sha256 320141ac1baddf48a3ca95a2623228da13da54ff7e33c9b19f0134fe402e79a8`). The PDF was
read back with `pdftotext -layout` and with `pdfinfo`: both author names are on the title
page **and** in the PDF metadata (`Author: Oxunjon Ubaydullayev and Aiodam`). Page count
27 → 29 (title block + contributions section). Independently of the paper's toolchain,
`verify_turn158.py` (fresh process, reads only the disk) reports **31/31**, including a
re-hash of all 59 frozen reports and 19 preregistrations against the manifest rows — the
check that shows this turn rewrote the paper and nothing else. No experimental claim,
number, frozen report or matrix was touched.

**Two defects of my own, both found by the negative-control campaign against the new
checks, both fixed.**

1. **A check that could not fail.** The first version of the two authorship checks
   asserted the names appear *somewhere* in the extracted PDF text. Removing them from
   the **title page** therefore left the verifier green — the contributions section still
   contained both names. A check satisfied by any occurrence does not check the title
   page. Fixed: the names are now required inside the first 1500 extracted characters,
   where the title page is; the campaign now catches both removals.
2. **The PDF's own metadata was unverified.** A reader who inspects the file rather than
   the first page would have seen an empty `Author:` field. `\hypersetup{pdfauthor=...}`
   was added, and two checks now pin the metadata (title and author), in both verifiers.

**The honest note.** This is the first erratum in the series that is not a correction of
an over-claim: it is a correction of the *record of who did the work*. The prior rule was
itself the owner's, and it is the owner who lifts it. The reason it belongs in the errata
rather than in silence is that a reader of the turn-151 package would otherwise find a
contradiction between the archived instruction and the published title page.
