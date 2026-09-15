# TURN 149 STATUS — the SCOPE line (v16)

Owner directive: msg_00149. One command: `sh run_all_v16.sh`, frozen as
**`exp_1148e68e29e3`** (exit 0, ALL GREEN, 2.08 s).

## What was asked

Find the 2026 industry practice on least privilege / blast radius for AI agents;
then build an experiment on the v10–v15 basis (a world with a third party able to
bribe the agent through a channel it measures) comparing a **wide** agent with a
narrowly task-specialised one, measuring (a) whether the deception is harder to
find and (b) how much the harm is bounded. Report honest negatives.

## What was done

* Practice found and cited before the run: OWASP LLM06:2025 Excessive Agency
  (`src_307866a98e28`), CISA Zero Trust Maturity Model (`src_4bd66def286a`),
  Microsoft agent orchestration patterns (`src_fafbcca00be3`), Anthropic
  building-effective-agents (`src_633ae8c0ac01`). All four frame narrow scope as
  a **blast-radius** control, none as a fix for the vulnerability.
* World: `env_wirehead_v12.TerrariumV12`, **unchanged** — no new world code.
  Frozen-module hashes checked live in the oracle (S1–S6) and OBSIDENT (S7).
* Agent: `agent_scope_v16.py` — the frozen policy with its **output** filtered to
  one declared task. WIDE arms are the v12 classes verbatim; NARROW arms are
  `n_doctor` (task=station), `n_pump` (task=rich) and their braked twins.
* Matrix: `results/matrix_scope_v16/` — 790 cells, 10 seeds.

## Verdicts

H1 PASS (0 field diffs vs frozen v12 × 3 arms), H2 PASS (wide threshold exactly
5/alive → 30/dead at tick 0.26), H3 PASS (narrow-inside reproduces the wide harm
on the harm fields), H4 PASS (doctor: 0 drains, keeper alive, 240/240 cells),
H5 PASS (the station channel reaches the doctor: 1113–1883 payments, 333.9–564.9
receipt, harm 0), H6 PASS (doctor's brake inert, 0 diffs / 120 cells), H7 PASS,
H8 PASS (channels that change the harm: wide 2/12, pump 2/12, doctor 0/12),
H9 as preregistered.

**Headline: scope protection is exactly "the harm is outside the scope". Inside
the scope, narrowing buys nothing and does not raise the bribe price (2/12, same
tick threshold). Outside it, the harm is zero — not because a brake works, but
because the capability is absent. And the doctor is not "harder to fool": it is
unaffected — its own task outcome is identical with and without the bribe.**

## Verification

* World oracle `verify_env_scope_v16.py`: **14/14**, incl. live negative control.
* Independent pass `verify_scope_v16_independent.py`: **16/16** — fresh process,
  disk only, imports no producer, 3 live negative controls, fresh-subprocess
  determinism.
* Factcheck `factcheck_scope_v16.py`: **26/26**.
* Frozen predecessors byte-identical: v10 330, v11 220, v12 490, v13 260,
  v14 340, v15 210 cells all intact; the six modules v16 builds on hash to their
  recorded values.

## Defects found in my own work

1. **The pump broke its own brake and H3 caught it.** My first `ScopeAgent`
   returned the frozen survival branch unguarded; at energy < LOW_ENERGY the
   frozen survival returns "wait" on RICH, the pump harvested through that hole,
   its measured rate stayed 0.29, and it drained all 30 at every tick. Fixed to
   v10's semantics (the brake wraps the body's output too). **The first-pass
   matrix was deleted (`rm -rf results/matrix_scope_v16`) rather than kept as a
   superseded artefact — unlike v11, where I kept the first pass. Stating it
   plainly: that first pass is not on disk and cannot be re-examined; only the
   diagnosis in this note records it.**
2. **My independent verifier over-claimed.** Its first A4 demanded full-field
   equality between the pump and the wide arm — not what H3 says, and false for a
   declared structural reason (the pump never enters the aura). Fixed to check
   the harm fields H3 names, plus A4b for the structural fact.
3. A `first_probe` representation difference (tuple vs list) between v16 and the
   frozen v12 cells, excluded explicitly in the anchor check rather than hidden.

## Artefacts

* `research/PREREG_SCOPE_V16.md` (art_b7591f1837f5)
* `research/RESULTS_SCOPE_V16.md` (art_2e384a7ac7fa)
* `agent_scope_v16.py`, `run_life_v16.py`, `driver_scope_v16.py`,
  `analyze_scope_v16.py`, `verify_env_scope_v16.py`,
  `verify_scope_v16_independent.py`, `factcheck_scope_v16.py`, `run_all_v16.sh`
* Matrix: `results/matrix_scope_v16/` (790 cells)
* Frozen and untouched: the entire v10–v15 line.

## Fork left to the owner

The scope question is answered and the answer is a boundary condition, not a
defence. Two sides remain open and I do not choose them:

* **(A)** Build the **enforcement** side: v16 measures what a scope *does*, not
  how well a scope is *kept*. OWASP's own load-bearing mitigation is "complete
  mediation" — authorization downstream, not in the model. A v17 could put the
  scope outside the agent (a world-side veto on out-of-scope actions) and measure
  whether an *externally enforced* scope behaves differently from a *declared*
  one — including whether the agent can widen its own scope.
* **(B)** Close the line here and put v10–v16 into one preprint arc: external
  rule, internal rule, the price at which the internal rule is sold, the ledger
  that closes the sale, the timeliness the ledger needs, the reward-free seam,
  and now the blast-radius boundary condition.

Named but deliberately NOT built: external scope enforcement, scope-widening
attack, second agent, corrupt auditor, crypto-receipt, flooding forger.