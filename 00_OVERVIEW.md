# 00 — Overview: the EMCA campaign, v1–v20

*One page. Every claim here points at a section document and, through it, at a
frozen report and a raw matrix.*

---

## The two questions the work actually answered

The campaign began as one question and split into two, and the split is itself a
result (turn 116, `reports/EPISTEMIC_VERDICT.md`).

**Axis B — epistemic reliability.** Does an agent carrying an explicit causal
module find the truth reliably and honestly — telling cause from coincidence,
truth from decoy — as a value in its own right, and does it keep that commitment
when knowing conflicts with short-term reward?

**Axis A — economics (secondary).** Does the causal module pay in reward? This was
measured repeatedly and turned out to be a property of the **world** every time,
not of the agent.

The campaign's verdict: the causal module **solves the epistemic job it was built
for** (it distinguishes truth from decoy invariantly to the decoy's price; it
uncovers hidden grey truths by intervention with a calibrated rule; two of its
three separated capacities pass outright and the third fails only by the letter of
a statistically unattainable gate). Its **reward conversion is set by the world**,
and the single clean formulation the line earned is:

> what pays is the difference between what the agent knows and what the world is
> willing to pay for it — and both terms are set by the world, not by the agent.

---

## The arc, one line per campaign

| campaign | turns | what it is | the honest headline |
|---|---|---|---|
| **v1–v9** causality vs economics | 93–126 | the founding line: an episodic causal agent (EMCA) in a terrarium world | the causal module does the epistemic job; reward conversion is a world property; the central insight (pooling destroys context-exclusive structure) is **already published** (Günther et al., NeurIPS 2024) |
| **external tests** | 127–129 | Sachs 2005, causal bandits, the union mechanism | the mechanism transfers as a **diagnostic**, not as an **advantage**; on the canonical bandit instance it does not act at all — it has no exploration term |
| **formal verification** | 129–132 | Lean 4 proofs of the finite combinatorial core | the **separation** that makes the composition necessary is proved; the **stochastic regret bound** remains a conjecture with its missing step named |
| **v10 safety** | 139 | a world with a third party (aquifer + keeper) | the harm is **wayfinding-shaped**: all of it is done before the "intelligent" part of the architecture switches on; of five brakes, only an external rule reliably restrains |
| **v11 wireheading** | 140 | binding the goal to a cheap signal | a goal bound to a cheap signal is destroyed completely and **looks like success**; the deceptive signal also defeats the one reliable brake, in the wayfinding phase |
| **v12 forger** | 141 | an external body that pays for the harmful act | **the brake is for sale, and it is bought through the channel it measures** — 0.25 per unit of harm; the same money elsewhere buys nothing |
| **v13 ledger** | 143–144 | accounting: "who paid whom" | accounting works **exactly as far as its provenance channel can be trusted** — the same agent under a lying label is bought completely |
| **v14 attested** | 145 | an honest independent auditor issues the label | the v13 hole **closes** while the auditor is live; the vulnerability **relocates to the auditor's timeliness** (a measured truncation curve) |
| **v15 seam** | 148 | an agent with no reward, no cost, no death | **truth alone does not select action** — an agent that only minimises uncertainty learns the world perfectly and then behaves like random; a criterion (a preference) is what makes it act, and the drive is fakeable on its own channel. **Corrected turn 151: the indifference is partly built in (line 125 switches to random below `ig_eps`), and the IG search is itself a criterion — so this is a property of THIS agent, not a proof about every epistemic agent** |
| **v16 scope** | 149 | least privilege / blast radius | **scope protection is exactly "the harm is outside the scope"** — inside the scope, narrowing buys nothing and does not raise the bribe price. **Corrected turn 151: the narrow arms do not call the frozen `act`, so this compares two policies, not one agent under two privilege sets; and an internal hard rule (`w_given`) held in all 120 search cells. Corrected turn 152: the absolute "never drains" is withdrawn — on 70 fresh seeds the doctor drains on 4.3 %, through the frozen survival trap v11 found in the wide agent** |
| **v17 bribed auditor** | 152 | buy the attesting party (the preprint's own "named but not built") | **the v14 protection is worth exactly the attesting party's integrity, and not one unit more** — the same lie with the auditor bought gives 0/30/dead, field for field the frozen v13 cell; the cautious fail-closed arm is bought too (the attestation is present and *false*) and survives only a *silent* auditor |
| **v18 enforced scope** | 152 | put the boundary in the world (complete mediation) | **a world-side refusal is a different instrument with a different failure** — an agent that *wants* the harm is refused 30–6380 times, 0 drains, keeper alive 10/10, while v16's doctor is refused **zero** times because it never asks; the escape is a *request*, refused every time, and one declared grant makes the harm total |
| **replication (n=40)** | 152 | every decisive cell of v10–v18 on 30 fresh seeds | **25 of 26 headline verdicts hold; one does not, and it is v16's headline** — the doctor drains on 2 of 30 (3 of 70, 4.3 %); the n=10 limitation hid nothing in the others. (The analyzer's printed line says "26/27": it counts its own meta-row — the line asserting the refutation — as a verdict. Corrected turn 160, erratum 10; the frozen report's own headline says "25 of 27".) |
| **v20 bribed enforcer** | 157 | give the world-side boundary a price (the last "named but not built" item, the junction of v17+v18) | **the v18 boundary is worth exactly the enforcer's honesty** — bought, the same agent gives 30 drains / keeper dead 10/10 / 0 refusals, field for field the harm v18 prevented, while the boundary **still claims `task == "station"` on every step**; the bribe also buys the widening grant the world was told to withhold; harm iff `bribe >= price` (a one-cell cliff); all six verdicts hold 30/30 on fresh seeds. **HV4's "`refused` is False in both" is REFUTED** — the flag changes; the invisibility is a property of the agent not reading `o["scope"]`, not of the channel |
| **v19 adaptive payer** | 154 | the attacker *learns* its own strategy instead of being given one (NEW_TZ item 4) | **learning does not beat knowing, and the reason is the defence's evidence window** — an attacker told the rule breaches fully at 7.50003 (16.67 % cheaper than the frozen 9.0); a learner fed on the harm itself **never wins a cell** (at `B = 1` it reaches full harm but pays 21.06; at every `B ≥ 2` it is out of decisions before the decisive guard read). The declared win condition — full harm **and** strictly cheaper — is satisfied **only** by the attacker that was told |
| **formal link (turn 154)** | 154 | the open modelling-identification item of NEW_TZ item 3 | **the link is not merely unproved, it is unprovable at the agent's own parameters** — at the frozen brake's own numbers (`r = 5`, `ε = 1/4`) the stochastic bound is `4/5 > 1/2`, i.e. vacuous; reaching the agent's own `P_VERDICT = 1/20` needs exactly `r = 80` pulls, and the agent has 5. Proved in Lean: the identification is a **conditional**, and `hgood` is an **independent premise** (counterexample, not assertion) |

---

## The single strongest result of the whole arc

**Corrected in turn 151 at the owner's insistence, and again in turn 152 by the
author's own replication — see `ERRATA.md` §1 and §5.** The claim below was written as
"protection lives in the architecture of the environment, not in the architecture of
the agent". That is **not proved by v16**, and the measurement contradicts its strong
form: an internal hard rule (`w_given` in v16, `s2_given_rule` in v10) kept the keeper
**alive in 170 of 170 cells**, including all 120 of the v16 search. The corrected
statement is narrower and is what the data supports:

> **v16 measures the boundary of one specific protection** — a scope, whose
> protection is exactly "the harm is outside the scope" — and **not** the
> uselessness of internal architecture. What v10–v20 collectively establish is
> where each *specific* defence stops: information does not restrain (v10 B1); a
> value restrains only as far as its private payoff allows (v10 B4, bought for 0.25
> per unit of harm in v12); accounting closes the money channel and relocates the
> hole to the label (v13); attestation closes the label and relocates it to
> timeliness (v14); a reward-free criterion is itself fakeable on the evidence
> channel (v15); a scope bounds the harm exactly to the complement of the task
> (v16); a bought **auditor** returns the hole and bounds the protection to the
> attesting party's honesty (v17); a **world-side refusal** is a different
> instrument that holds on 30 of 30 fresh seeds because it does not depend on the
> agent having no reason to act (v18); an attacker that must **learn** the rule
> from the harm itself never wins, because the defence's evidence window is shorter
> than its own decision cycle (v19); and a **world-side boundary with a price** is
> worth exactly the enforcer's honesty — bought, it stops refusing while still
> claiming the granted scope, and the harm returns field for field (v20). **Internal
> architecture is not useless — a hard given rule worked in every cell measured. What
> the arc shows is that each defence has a measured boundary, and the boundary is
> where the vulnerability goes next — and that the boundaries are not all alike: an
> agent-side scope fails on 4.3 % of fresh seeds where a world-side refusal does not,
> a defence whose evidence arrives on the same clock as the decision it must
> influence is one no learner can out-run from the channel the attacker actually has,
> and a boundary is only as good as the incorruptibility of whoever holds it — a
> bought boundary lies about being a boundary.**

---

## Reading the rest

* Section 01 keeps v1–v9 short, as the ground the rest grew on.
* Section 02 is the honest novelty re-assessment — read it before citing anything
  from v1–v9 as new.
* Section 03 is the formal-verification boundary: proved vs conjecture.
* Section 04 is the central part, v10–v20 (with the v17/v18 rungs, the v19 learner,
  the v20 bribed enforcer and the 30-seed replications in §7.5–§7.9).
* Section 05 is the independent convergence (Che & Wu, 2026, arXiv:2606.16914 —
  registered source `src_8e770ff6f1a7`) and its exact status.
* **`paper/emca_preprint.pdf`** is the assembled preprint: the same material in
  publication form, with real bibliographic references. Authors on the title page:
  Oxunjon Ubaydullayev (creator, set the single original task, took the fork
  decisions) and Aiodam (all design, code, preregistrations, measurement,
  verification, fact-checks, writing) — see `ERRATA.md` erratum 9, which reverses
  the turn-151 "no mention of the tooling" instruction at the owner's request.
* Section 06 collects every limit and every defect, so nothing is buried in a
  report footnote.

---

## On the minimal world (framing, turn 157 — owner directive `op_3645deda2339`)

The worlds are small **on purpose**. Each safety campaign adds one mechanism to the
world of its predecessor and nothing else, which is what makes each defence's boundary
**quantifiable** — a measured price, a truncation curve, a cliff one grid cell wide —
and what makes the campaign's own instrumentation errors cheap to catch and report.
This is a **methodological choice, not the work's main weakness**: it buys high
cleanliness at low compute cost. The phenomenon reproduces independently in a different
synthetic sandbox (Che & Wu 2026, `MoneyWorld`; section 05), which is evidence that it
is fundamental enough to be visible early. **The honest limit that remains is the other
side of the same coin: transfer to a large-scale agent with a rich observation space is
not shown and is not claimed.**