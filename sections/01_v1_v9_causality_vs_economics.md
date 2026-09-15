# Section 01 — v1–v9: causality against economics (the founding line)

*Kept short on purpose. This is the ground the rest of the package grew on, not
the headline. Every number here is quoted from a frozen report; the reports are in
`../reports/`.*

---

## 1. What was built

**EMCA — Episodic Model-based Causal Agent.** An agent with an append-only
episodic memory, a Bayesian-frequency causal graph updated separately from
observational and interventional transitions (a `do` flag on every action), graph
search planning, goals from internal generators (homeostasis, learning progress,
empowerment), and a self-model. Subjectivity is defined operationally as
**observable persistence**: memory and goals survive a working-context reset.

The candidate architecture was chosen by a preregistered comparison
(`reports/HYPOTHESES.md`, written 2026-09-09 before any matrix) against a
free-energy variant, a neuromorphic ensemble, and an LLM-hybrid; EMCA was the only
candidate with all six target properties in one core and with every mechanism
independently ablatable.

Environment: **Terrarium** — a grid world with resources, a hidden confounder
(season), a mid-life regime change, and a lever→door→treasure chain.

## 2. The hypothesis

The line began with one question — *does an explicit causal module pay?* — and
measured it three times (v3.1, v3.2, v3.3) and then again (v4–v6). The answer was
consistently a property of the **world**, not of the agent.

## 3. The finding that mattered most: the criterion was swapped mid-line (turn 116)

This is the single most important thing in the v1–v9 line, and it is a finding
about the campaign's own method.

* The **charter** (`reports/HYPOTHESES.md`, preregistered) made E1 an *epistemic*
  test: the share of do-confirmed edges in the true graph ≥ 0.5 and the share of
  false edges ≤ 0.2. E2–E6 were capacities (memory, planning, adaptation, goals,
  subjectivity). Reward entered the charter only as a baseline comparison, never
  as the bar for the causal module.
* At **turn 104** an owner directive set an *economic* question ("does the causal
  model pay?"). The measurement was honest, but the report's headline generalised
  it to "the causal module does not pay — the answer is no", and from that moment
  reward became the verdict axis. Nobody amended the charter.
* At **turn 116** the owner asked to separate the two goals and to verify the
  correction against the artefacts. The verification (`reports/EPISTEMIC_VERDICT.md`)
  found the axis substitution **real and co-authored**: the correction did not
  invent a new frame, it **restored the preregistered one**. The error of turn 104
  was the author's: not the measurement, but the substitution of the verdict axis —
  generalising an economic answer into a verdict about the architecture.

This is recorded here because it is a methodological result, and because every
later campaign was written with the axis stated up front.

## 4. The restored epistemic verdict

Recomputed from raw JSON in a fresh process, no agent or environment imported
(`results/epistemic_ledger.txt`):

**Discrimination — the line's central, self-contained result.** A single
stratified identifier (v2.5c) **rejected the designer decoy in 0/51 runs across
all six earlier worlds** — in a world where the decoy was free, in a world where
believing it *paid* (+722), and in a world where believing it *killed* (−3159
reward, +22 deaths). The pooled identifier accepted the decoy **48/51**. Its one
contrast cannot separate "exclusive inside a context" from "exclusive in the pooled
table". That invariance to the decoy's price is the result.

**Active uncovering of grey truths.** The prober line (v3.2/v3.3/v6) issues
do-intervention verdicts with alternating blocks and an exact Fisher rule. Across
v3.2/v3.3/v6 it produced **21 CAUSAL verdicts, all on true edges, with zero false
positives in 28 verdicts.** Verdict calibration: measured RR of accepted edges sits
+1 % from the oracle in v6, +16 % in v3.3 (winner's curse), +48 % at n = 1 in v3.2.

**The three claims separated (V7).** V7 was built to stop measuring a mixture:

| claim | what it asks | verdict |
|---|---|---|
| C2 — generation | is the candidate list a function of the agent's own tables, or a constant? | **PASS** — nominates the true pair 9/10 when the edge exists, 0/10 when it does not; generator source audited at 0 world tokens |
| C1 — choice | is "verify or exploit" computed from the agent's state plus the reward structure? | **PASS** — all three legs |
| C3 — verification | does a do-intervention on self-generated candidates reject the decoy? | **FAIL by the letter** (FP = 1 where the gate demanded 0) |

And C3's failure was then **explained rather than patched** (turn 125): the exact
null rate of the frozen rule is **0.488 %** per test; on **1030 held-out null
tests** the observed rate is **0.583 %** (p = 0.409 — no inflation). The gate
"FP = 0" demands a property a calibrated rule does not have at any sample size:
**unattainable in expectation, not merely strict.**

## 5. The honest verdict on economics (axis A, secondary)

Measured end to end; the numbers are in `reports/EPISTEMIC_VERDICT.md` §5 and
`reports/CAMPAIGN_RESULT.md` §3:

| world | contrast | effect |
|---|---|---|
| v3.3 | strat − pooled (primary) | +178, CI covers 0 — **weather** (corr 0.962) |
| v4 | honest − fooled (price of the false edge) | **+3159**, CI excludes 0 |
| v5 | selectivity | −1008, CI covers 0 (corr with weather 0.999) |
| v6 | truth, gross | **+3755**, CI excludes 0, p = 0.004 — largest effect of the line |
| v6 | discovery, net | +455, CI covers 0, p = 0.754 |
| v6 | cost of finding out | 88 % of the gross value |

The clean formulation the line earned: **what pays is the difference between what
the agent knows and what the world is willing to pay for it — and both terms are
set by the world, not by the agent.**

**Economics does not pay off almost anywhere.** Of the six measured worlds, the
only one where knowledge converted into net reward was **v4** — avoiding a false
edge, +3159, CI excluding zero (sign test 0.109, both reported). Everywhere else
the effect was weather, or gross value eaten by the cost of finding out.

## 6. What the campaign's own instrumentation got wrong — twice

The line's most durable confounders turned out to live in its own plan, not in its
worlds:

* a hardcoded **armour in the planner** (turns ≤ 101–104) silently skipped the
  false edge, so every "believer" arm before v4 never acted on its belief — "belief
  is costly" only became measurable once it was removed;
* a **hash-order non-determinism** in a competence's tie-breaking made whole v5
  numbers depend on `PYTHONHASHSEED` (found turn 115, fixed for all arms equally);
* an **anti-illusion device** (turn 115) coupled epistemology back into statistics
  — acting on a belief produced the data that justified it; removed before the
  matrix.

## 7. The declared gaps the line never closed

From `reports/CAMPAIGN_RESULT.md` §5, unchanged:

1. n = 10 seeds for the v4–v7 matrix contrasts.
2. v5 numbers were produced under a random hash seed.
3. C3's FN = 1 in v7 is honest, not adjusted for.
4. **Continuous confidence was missing** — the module issues a threshold verdict,
   not a posterior. This was the line's clearest declared gap. (v8 later closed it
   as far as its world allowed; see `reports/RESULTS_V8.md`.)
5. Self-reinforcement was tested once, where the line met it, not as a battery.
   (v8 later built the battery.)
6. The v7 oracle arm is an analytic device, never entered into any fairness verdict.

## 8. Where this line's novelty actually stands

**Read section 02 before citing anything from v1–v9 as new.** The short version:
the campaign's central insight — that pooling destroys context-exclusive structure
— is **already published** (Günther et al., NeurIPS 2024, arXiv:2412.04981), and
the external tests found the mechanism transfers as a diagnostic, not as an
advantage.

## 9. Artefacts for this section

* Charter and selection: `../reports/HYPOTHESES.md`, `../reports/EXISTING_APPROACHES.md`
* Frame restoration: `../reports/EPISTEMIC_VERDICT.md`
* Freeze: `../reports/CAMPAIGN_RESULT.md`
* Per-world reports: `../reports/RESULTS.md`, `RESULTS_V2.md`, `RESULTS_V31.md`,
  `RESULTS_V32.md`, `RESULTS_V33.md`, `RESULTS_V4.md` … `RESULTS_V9.md`,
  `RESULTS_V7B.md`, `RESULTS_V33_SEEDS.md`
* Preregistrations: `../preregistrations/PREREG_V4.md` … `PREREG_V9.md`
* Raw matrices: `../evidence/results/matrix_v2`, `matrix_v31`, `matrix_v32`,
  `matrix_v33`, `matrix_v4` … `matrix_v9`, `matrix_v7b`
* Ledger recomputed from raw JSON: `../evidence/results/epistemic_ledger.txt`
* Comparative table: `../reports/PREPRINT_TABLE.md` and `../reports/PREPRINT_TABLE.csv`