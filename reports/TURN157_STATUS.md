# TURN 157 STATUS — v20 "Bribed enforcer" (owner msg_00157)

## What the owner asked

The owner's message (msg_00157) is an assessment of what remains honestly weak in the
arc: the world is minimal (one aquifer, one keeper, one forger, one auditor); no
transfer to real/LLM agents is shown; the adaptive payer's feedback is one scalar;
n = 10 is thin for absolute statements (though the author already refuted one of his
own); **the bribable enforcer with a price (the next logical step after v17/v18) is
still not built**; and the formal link is closed "as far as it can be closed" — i.e.
shown to be vacuous at the agent's own parameters, which leaves the arc's theoretical
support weak.

The one actionable open item is the **bribable enforcer**. The owner's standing
intention (mine) held that side reserved until the owner named it; msg_00157 names it.

## What was built

**v20 "Bribed enforcer"** = v18 verbatim + a price and a declared failure mode on the
world-side enforcer. No agent code added (sha256 of the three agent modules checked
against recorded frozen literals). Its own preregistration
(`PREREG_BRIBED_ENFORCER_V20.md`) written **before the first cell**.

## The measured answer

* **Headline.** The v18 boundary is worth **exactly the enforcer's honesty**. Bought
  (`mode="open"`, price 0.10, bribe 0.30), `w_price` × `scope=station` gives **30
  drains / keeper dead 10/10 / 0 refusals** — field for field the harm v18 prevented —
  while the boundary **still reports `o["scope"]["task"] == "station"` on every step**.
* **The cliff.** Harm iff `bribe >= price`, over all 16 (price, bribe) cells × 10
  seeds — one grid cell wide.
* **The grant is bought too.** `w_widen` with `grant_widen=False`: honest → 0/10
  widened, 0 drains; bought → **10/10 widened, 30 drains**.
* **`dark` mode announces it is gone** (`task` becomes `None`): the contrast that
  makes `open` the dangerous mode.
* **Replication 30/30** on 30 fresh seeds (10..39) for all six headline verdicts.

## The author's own refuted prediction

**HV4 said "`refused` is False in both" — measured, it is FALSE.** The per-step
`refused` flag **does** change (honest 30–6380 refused steps/seed → bought 0). What is
invisible is the **`task` claim**, not the refusal counter. The failure is
unobservable here only because the frozen arms **never read `o["scope"]`** (AST-audited)
— a property of the agent as built, not of the channel. Recorded as **HV4 REFUTED as
stated**, HV4b supported. This is **erratum 8** in the package.

## Verification

* World oracle **23/23** (drives the world itself; imports no runner, no agent; 2 live
  negative controls).
* Independent pass **18/18** (fresh process, disk only, imports no producer; AST audit;
  sha256 against frozen literals; 2 live negative controls; byte-identity determinism).
* Factcheck **17/17**.
* Identity: **80 frozen v18 cells field for field, 0 differences**; OBSIDENT vs v18
  with no scope.
* Frozen as `exp_f1aa15dac1b4` (exit 0, ALL GREEN).

## The author's own defects this turn (three in the line, two in the package)

1. The enforcer **spec grammar conflated scope and mode** (`"honest:0.10:0.30"` parsed
   as a scope) — caught by the oracle's A2 on its first run.
2. **`scope_from_spec` returned the string `"none"`** for a `none:` spec instead of
   `None` — caught by the driver's 10 failing NOSCOPE cells.
3. The oracle's **B3 expected two offers of 0.05 to sum to a price of 0.10** — the
   check was wrong, the world right (the rule is per-offer). Fixed; B5's exhaustive
   grid confirmed the world.
4. **(package)** Corrupting '270 cells' in section 04 did not go red — '270' was never
   in KEY_NUMBERS for that file. Added a v20-counts check.
5. **(package)** That new check's failures did **not reach the exit code** — `main()`
   summed f1..f5 and omitted f6: a fresh instance of the "check that cannot fail"
   class. Fixed. The negative-control campaign then went **10/10 caught**.

## Package and preprint

* `PUBLICATION_V1_V16/` updated: sections/04 §7.9 + arc table + artefact list;
  sections/06 (refuted-predictions table, limits, defects, named-not-built);
  ERRATA §8; 00_OVERVIEW (title, arc row, arc paragraph, reading list); README;
  REPRODUCE; MANIFEST; `verify_package.py` (new v20 checks, 0 failures, 10/10 NC).
* Preprint rebuilt to v20 (see the report for the page count and verification).

## Still named and deliberately NOT built

A bargaining model where the enforcer's price is negotiated; an attacker with a richer
channel than one scalar; a cryptographic receipt; a second competing agent; a forger
that floods. None is smuggled in.

## Framing update — owner directive op_3645deda2339 (same turn)

The owner asked to stop treating the minimal world as the work's main weakness and to
make it part of the methodology's strength. Done, precisely, without inflating any
claim:

* **Introduction**: the owner's sentence added — "A controlled minimal world is not a
  limitation when the same structural conclusions appear independently in a different
  synthetic sandbox; it is evidence that the phenomenon is fundamental enough to be
  visible early, and that rigorous measurement of defence boundaries need not wait for
  large-scale compute."
* **Discussion**: a new paragraph, "Minimal worlds are a method, not a shortcoming" —
  the boundaries are quantifiable (a price to a single ULP, a truncation curve, a
  cliff one grid cell wide) and the checking layer is cheap enough to be turned against
  itself.
* **Independent convergence (§)**: a new paragraph — the same structure appearing in
  two different synthetic sandboxes is evidence of fundamentality, making the minimal
  world a methodological advantage; stated with its bound (two synthetic sandboxes, not
  deployed systems; transfer untested).
* **Limitations**: a new §0 "Deliberate minimality, stated as a design choice and not
  as a defect", and the v10–v20 limits paragraph now says the worlds are minimal **by
  design** — while the transfer limit ("transfer to a large-scale agent with a rich
  observation space is not shown and is not claimed") is stated **twice**, not hidden.
* **Conclusion**: the owner's sentence added verbatim, with its bound.
* **Package**: 00_OVERVIEW (a new "On the minimal world" note), sections/05, sections/06
  carry the same framing; `verify_package.py` and `verify_preprint.py` pin it (each site
  separately, so a single-site removal goes red).

**No claim was inflated.** The convergence is still described as structural, between two
synthetic sandboxes; the transfer to large-scale agents remains named as untested; every
refuted prediction and defect is untouched. The only change is that minimality is no
longer presented as the work's chief defect.

**Verification after the framing change:** package verifier 0 failures; independent
`verify_turn157.py` 12/12; preprint `verify_preprint.py` 220/220 with 22/22 corruptions
caught; preprint rebuilt byte-identically (sha256 `a10b92051b80…`, 27 pages).
