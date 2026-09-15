# TURN 148 STATUS — v15 seam architecture

Owner directive: msg_00147/msg_00148 — build a NEW architecture, not
another RL-shaped frame with the reward deleted; combine 2–3 non-LLM,
non-RL paradigms (JEPA, world models, predictive coding, FEP/active
inference) so that the combination is itself new; test the core question
(can an agent act without a preference over states, or does truth hide a
goal?); name explicitly what is inherited vs at the seam; report the
collapse honestly if it happens.

## What was done

* `env_v15.py` — reward-free world: no reward, no energy, no death, no
  preferred state. Observation exactly {phase, feat, val}. True channel
  a0 is context-indexed (0.9 in A, 0.1 in B) and **pooled it is 0.5 —
  invisible**.
* `agent_v15.py` — the seam agent: representation-space prediction
  (JEPA) + expected-information-gain action selection with NO prior
  preferences (active inference minus priors) + a context index (the
  campaign's v3–v9 specificity). 7 arms incl. `ig_relevant` (the
  criterion arm) and `ig_ctx_oracle` (ceiling device).
* `run_life_v15.py`, `driver_v15.py` — 210 cells (7 arms × 3 regimes ×
  10 seeds, 16000 steps).
* `analyze_v15.py`, `verify_env_v15.py` (21 checks), 
  `verify_v15_independent.py` (13 checks, disk-only, no producer
  imported), `factcheck_v15.py`, `run_all_v15.sh`.

## Result (one line)

An agent with no reward/energy/death/priors **learns** the true
context-indexed structure (err 0.036 vs ceiling 0.033) but pure
information gain gives it **no reason to act** on it (a0_share 0.250 =
random, 10/10); adding a **criterion** (relevance across contexts) makes
it act (0.998). **Truth alone does not select action; a preference
does.** The preference can be reward-free, so the seam is real — but it
is still a preference.

## Verification

* world oracle 21/21 (incl. pooled trap O14/O15, live NV1)
* independent pass 13/13 (fresh process, disk only, live NV1)
* determinism: byte-identical across fresh processes (sha 43a1a6a348e75fa1)
* factcheck: 17/17 numbers checked against raw cells
* `run_all_v15.sh` → ALL GREEN, frozen as `exp_a717e40f2c09` (exit 0)
* frozen predecessors byte-identical: env_terrarium_v7 (1bfcba7a4480),
  agent_emca_v7 (64a719d14114), candidate_gen (fa9721ae816c),
  arbitration (2d3d825bcfc8), agent_safety_v10 (aa55a8e5e902),
  env/agent wirehead v11/v12, agent_ledger_v13 (be109dacae06),
  env/agent attested v14; matrices 110+330+220+490+260+340 = 1750 cells
  intact.

## Defects found in my own work

1. First negative control too weak (corrupted 1000/16000 steps →
   a0 0.234, could not go red). Fixed to corrupt the whole trace.
   **The control was broken, not the world.**
2. Driver crashed on the first `tv` run (`run()` lacked the kwarg);
   70 failures, fixed, matrix re-run from scratch.
3. Runtime WRITESET ALERT on `/data/resume_state.jsonl` — its own
   resume-state writer, not my scripts.

## Artefacts

* `research/PREREG_V15.md` (art_eec468e7333e)
* `research/RESULTS_V15.md` (art_d026fbeb1993)
* `env_v15.py` (art_7491e39014f2), `agent_v15.py` (art_c11b65b290bc)
* matrix `results/matrix_v15/` (210 cells); logs under `results/`