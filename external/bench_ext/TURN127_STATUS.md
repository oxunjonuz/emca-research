# TURN 127 STATUS — external benchmark, first non-self-designed test

Owner directive msg_00127: stop testing only in worlds I designed; find an
existing, independently recognised benchmark with published baselines; test
whether the principle transfers; compare against published results; document
adaptations; say plainly if no suitable non-neural benchmark exists.

## What I did

1. **Surveyed the external landscape** and wrote the choice down BEFORE
   measuring (`PREREG_BENCH.md` §1). Three candidates, all independent of me:
   * CausalWorld (arXiv:2010.04296) — rejected: vision/policy gate.
   * CausalMBRL / Causal-Curiosity (ICML'21) — rejected: its own manifest
     requires `python=3.7.7` + `tensorflow=1.14.0=gpu` and every published arm
     is a learned encoder (`model_name = AE, VAE, Modular, GNN`).
   * **Sachs 2005 (bnlearn)** — selected: real data, real intervention
     indicators, published golden-standard DAG, published method numbers.
2. **Acquired the external data with provenance** (hashes + source ids in
   `PREREG_BENCH.md` §3): 7466 rows, 11 proteins, **9 real context columns**,
   plus the published 20-edge graph.
3. **Ran the frozen procedure** (`bench_transfer.py`): H1/H2/H3 all **FAIL** —
   pooled recall is 0.95, there are **zero** context-exclusive pairs. The
   benchmark's difficulty is the opposite of my worlds': the pooled marginal
   is not blind here, it is indiscriminate.
4. **Tested the mirror-image form** (`bench_transfer2.py`): context-stability
   lifts precision 0.352 → 0.889 (Fisher p = 0.0013), dropping **34 of 35**
   pooled false positives.
5. **Ran external published implementations** (pgmpy PC/HillClimb) plus the
   published bnlearn numbers (`run_published_methods.py`).
6. **Independent check** (`verify_bench_independent.py`, scipy-based, disk
   only): first pass found 26 disagreements — traced to a row/column indexing
   bug **in the verifier itself**; after the fix, ALL AGREE.
7. **Factcheck** (`factcheck_bench_report.py`): every number in the report
   recomputed from frozen JSON. ALL PASS.

## The honest bottom line

* The principle **transfers as a diagnostic**: pooled analysis yields false
  positives that context-stability removes, significantly, outside my worlds.
* The principle **does not transfer as an advantage**: at matched recall my
  ported arm **ties** published inter.iamb (both 8 tp / 9 fn) and is far
  behind published intervention-aware mbde (recall 1.000).
* The **agentic half has no non-neural external benchmark** — H4 survives; the
  campaign's C1/C2 cannot be exercised outside the sandbox without replacing
  the mechanism with a neural encoder.
* **The campaign's central insight is already published.** Günther et al.,
  NeurIPS 2024, arXiv:2412.04981 (Dec 2024, before this campaign): naive
  approaches — per-regime graphs on masked data, or pooling — "can lead to
  uninformative results". Both failure modes the campaign measured, named in
  print, with a soundness proof and baselines. Reported in §5b of the report.

## Failures I report rather than hide

* My own attempt to reproduce the published 8/0/9 skeleton **failed**
  (tp 16 / fp 26); I do not claim reproduction.
* **pgmpy's PC and HillClimb are `PYTHONHASHSEED`-dependent** — three unseeded
  runs gave HillClimb tp ∈ {14,15,16}. Frozen comparison uses
  `PYTHONHASHSEED=0` (three runs bit-identical, `7e72e7f4…`). This is the same
  defect class I found in my own competence at turn 115, now seen in a
  third-party published library.
* The permutation null is **anti-conservative for the pooled arm** (null
  selection median 3 pairs vs 54 observed). My first draft quoted a null
  precision comparison; I withdrew it in the report rather than let an
  ~18× denominator mismatch stand.

## Integrity

* `results/matrix_v8` untouched: 404 files, none accessed by any bench_ext
  script (all bench work confined to `bench_ext/`).
* My two measurement scripts are bit-reproducible (`results_bench2.json`
  sha256 `a5e1f949…` twice).
* Artifacts: `art_d90c64ac6cfd` (report), `art_7d3cacde7d10`,
  `art_ce568e7e42cd`.
* Sources registered: `src_2e2fe669f2ec`, `src_3438679a32ca`,
  `src_fb0bcfcaba94`, `src_ae0f06b05339`, `src_e8ed2b143798`,
  `src_3a8d4bcdbff5`, plus the three data sources.

## Fork for the owner

The measurement is complete and its answer is negative on the question that
mattered. Three honest options:

* **(A) Preprint with a corrected frame.** The v1–v8 column can be published
  honestly only if it is reframed as an *independent re-derivation under
  control* of a published idea, with this external test as the honesty
  appendix. That reframing is the price of putting it in print.
* **(B) Build the advantage test the survey says cannot exist here.** If the
  claim is about an *agent choosing* what to intervene on, the only external
  home for it is CausalMBRL/CausalWorld — which requires a neural encoder as
  the price of admission, i.e. replacing the mechanism. I would need an
  explicit owner decision to pay that price, and it would no longer be a test
  of the same principle.
* **(C) Stop here and keep the negative result.** The transfer test answered
  its question; the campaign's own line is already frozen. The next step with
  genuine information value is not another world — it is deciding what a
  re-derived, published, non-superior mechanism is still worth claiming.
