# RESULTS — external benchmark: does the principle survive outside my own worlds?

Turn 127. Owner directive msg_00127. Benchmark chosen **before** measuring, from
a survey of what exists independently of this campaign
(`bench_ext/PREREG_BENCH.md`, frozen before the first run).

**Headline: the mechanism does not transfer in the form the campaign measured
it, and it does transfer in an adjacent form — but the transferred form lands
at the level of a long-established published constraint-based algorithm, not
above it.** Three preregistered hypotheses FAIL, one survives, and the
failures are the substance of the answer.

## 0. What was found first: the agentic half has no non-neural benchmark

The campaign's question was about a causal module **inside an agent**. The
external landscape for that is gated by a neural component, and this is not a
matter of taste — it is in the manifests:

| benchmark | gate | evidence |
|---|---|---|
| **CausalWorld** (arXiv:2010.04296, MILA/MPI 2020) | vision + policy learning; tasks are block-construction with a simulated robot | source `src_2e2fe669f2ec` |
| **CausalMBRL / Causal-Curiosity** (Sontakke et al., ICML'21) | env requires `python=3.7.7` + `tensorflow=1.14.0=gpu`; **every** published arm is a learned encoder — `model_name = AE, VAE, Modular, GNN` | sources `src_3438679a32ca`, `src_fb0bcfcaba94`, `src_ae0f06b05339` |

Both are legitimate benchmarks, both are published, both are independent of
me — and both require replacing the thing being tested with a neural encoder
before anything can be measured. That is exactly the case the owner named as
a valid answer. **H4 is not falsified: I found no non-neural external
benchmark for the agentic half.**

What remains measurable externally is the **epistemic half** — whether
within-context contrast sees relations a pooled marginal structurally cannot
— and for that an offline dataset with real experimental context columns
exists: **Sachs et al., *Science* 2005**.

## 1. The benchmark, and why it is a fair container

Sachs 2005 is the standard real-world causal-discovery benchmark: 11
phosphoproteins, a **validated golden-standard DAG published in 2005**, and
what makes it usable here — real intervention indicators. The external file
`ds/sachs.experimental.mixed.txt` (sha256 `c1c4b12b…`, 7466 rows) carries
**nine indicator columns** naming which stimulus/inhibitor was applied to
that cell (`cd3_cd28`, `icam2`, `aktinhib`, `g0076`, `psitect`, `u0126`,
`ly`, `pma`, `b2camp`). Mean 1.67 indicators per row. So the data has a
genuine **context variable** that someone else designed, fifteen years
before this campaign, for their own reasons.

Ground truth used: the published 20-edge graph
(`ds/sachs.ground.truth.graph.txt`, sha256 `2406ec0f…`), and the 17-edge
validated network that the published bnlearn analysis is scored against.

## 2. The results, against the frozen preregistration

Procedure frozen in `PREREG_BENCH.md` §4 before any run: Spearman/Fisher-z;
pooled decision at α=0.05; stratum decision as Bonferroni over strata with
n≥50; permutation null (200 replicates, seed 20260912) that destroys all
joint structure while preserving every marginal exactly.

| hyp | claim | verdict | measured |
|---|---|---|---|
| **H1** | pooled marginal sees only a minority of true edges | **FAIL** | pooled recall **0.95** (19/20); falsified at the 0.75 bar |
| **H2** | context-exclusive true edges exist here | **FAIL** | **0** such pairs; only 1 pair is pooled-invisible at all |
| **H3** | context-exclusive pairs are enriched for truth | **FAIL** | enrichment undefined (0 pairs); 200/200 nulls ≥ observed |
| **H4** | agentic half has no non-neural external benchmark | **SURVIVES** | see §0 |

`bench_transfer.py` → `results_bench.json`; exact numbers reproduce
independently (`verify_bench_independent.py`, "ALL AGREE").

**Why H1/H2 failed is the finding.** In my worlds I built masked edges —
relations true inside a context whose pooled marginal is structurally below
threshold. Sachs 2005 has almost none: 54 of 55 pairs are marginally
associated, and the single pooled-invisible pair (`mek–erk`) is a *true*
edge. The benchmark's difficulty is not masking. **It is the opposite: a
pooled marginal here is not blind, it is indiscriminate.** That is a
different failure mode, and it is the one the campaign never faced.

## 3. So I tested the mirror-image form — and it transfers

Reading the principle as *"context is information, the pool is not enough"*
rather than *"context unmasks what the pool hides"*, the same machinery gives
three arms. All on the external data, external ground truth, external
context columns (`bench_transfer2.py` → `results_bench2.json`):

| arm | selection rule | tp | fp | fn | precision | recall |
|---|---|---|---|---|---|---|
| **A** pooled marginal | p_pooled < 0.05 | 19 | **35** | 1 | **0.352** | 0.950 |
| **B** all strata agree | A ∧ every stratum significant, same sign, α/K | 3 | 0 | 17 | **1.000** | 0.150 |
| **C** unpolluted context confirms | A ∧ general stratum significant, same sign | 8 | **1** | 12 | **0.889** | 0.400 |

Before any interpretation — the **honest scale of this**:

* precision 0.352 → 0.889 is Fisher **p = 0.0013** (vs gt17; p = 0.0036 vs gt20);
* but the naive pooled arm is a *weaker* stand-in than any published method,
  so beating it is **not** evidence against published methods;
* under the permutation null the arms are **not comparable by precision**: the
  null destroys the pooled marginal association outright, so arm A selects a
  median of only **3** pairs (max 8) against 54 observed, i.e. an ~18× smaller
  denominator. Reporting "null precision 0.383 vs observed 0.352" would
  compare a 3-pair decision to a 54-pair decision and is **withdrawn** here as
  uninformative. What the null does establish, and all it establishes:
  arm B fires on **0 of 200** null replicates (never on pure noise), and arm C
  fires on a mean of 0.32 pairs. Neither the exchangeability of A nor the
  calibration of the α=0.05 pooled threshold is tested by this null — that
  would need a null that preserves the marginal association, which a
  column-wise permutation cannot do.

Ranked by pooled p: at k=3 precision is 0.333 pooled vs **1.000** for
context-stability ranking (hypergeometric P=0.043 for a random 3-subset being
all-true). The substance: **34 of arm A's 35 false positives are dropped by
requiring the unpolluted context to confirm** (their mean heterogeneity
p = 0.49, i.e. no evidence of a stable relation at all; true edges' mean
spread 0.395 vs false 0.117).

## 4. The head-to-head with published methods — and the honest verdict

I ran **external, widely-published implementations** (pgmpy: PC, PC-chi²,
HillClimbSearch) plus the two **published bnlearn numbers** for Sachs, on the
same file, same ground truth, skeleton comparison (`run_published_methods.py`,
`results_headtohead.json`, `results_published_methods.json`):

| method / arm | tp | fp | fn | precision | recall |
|---|---|---|---|---|---|
| **PUBLISHED bnlearn inter.iamb** (test='cor') | 8 | 0 | 9 | **1.000** | 0.471 |
| **MINE arm C** (pooled + context confirm) | 8 | 1 | 9 | 0.889 | 0.471 |
| **MINE arm B** (all strata agree) | 3 | 0 | 14 | 1.000 | 0.176 |
| **MINE arm A** (naive pooled marginal) | 16 | 38 | 1 | 0.296 | 0.941 |
| **pgmpy PC** (pearsonr, continuous) | 6 | 3 | 11 | 0.667 | 0.353 |
| **pgmpy PC** (chi², q3 discrete) | 13 | 11 | 4 | 0.542 | 0.765 |
| **pgmpy HillClimb** (bic-g, continuous) | 15 | 20 | 2 | 0.429 | 0.882 |
| **PUBLISHED bnlearn mbde** (intervention-aware) | 17 | 8 | 0 | 0.680 | **1.000** |

**Verdict, stated plainly: at matched recall my ported arm C does not beat the
published baseline — it ties it.** Both recover the same 8 of 17 arcs and both
miss 9. arm C pays one false positive where inter.iamb pays none; arm B buys
precision 1.000 by giving up 82% of recall. The published intervention-aware
method (mbde, recall 1.000) is far ahead of everything I produced, and it got
there using the same intervention columns my arms read.

So: **the principle transfers** — context genuinely separates edges the pooled
marginal cannot rank (p = 0.0013) — **and it does not transfer into an
advantage.** Applied offline to a dataset built by others, the ported
mechanism buys precision at a heavy recall cost, and lands level with a
constraint-based algorithm published decades earlier. Nothing here supports
the claim that the campaign's mechanism is superior to established causal
discovery. It supports a weaker, honest claim: a specific *failure mode* of
pooled analysis (34/35 false positives are context-unstable) is real and
detectable outside my worlds.

## 5. Everything I was forced to adapt — labelled, not hidden

1. **Only the epistemic half is testable.** C1 (choosing what to intervene
   on) and C2 (generating its own candidate) cannot be exercised on frozen
   data — the interventions were assigned by Sachs' experimenters in 2005.
   H5 declared this before running. **The transfer is partial by construction.**
2. **The agent is not an agent here.** My arms are statistical decisions on a
   table, not an agent acting in an environment. What transferred is the
   *contrast rule*, not the agent.
3. **The permutation null is an anti-conservative control for the pooled
   arm.** A column-wise permutation destroys the marginal association too, so
   it cannot test whether arm A's own α=0.05 rule is calibrated — it only
   tests whether the *context* arms fire on structureless data. This was
   missed in the first draft of this report and corrected in §3.
4. **Discretisation was mine, not theirs.** bnlearn used Hartemink
   information-preserving discretisation; I used quantile-3 for the pgmpy
   discrete arms. Declared in-code and in the frozen preregistration.
5. **My own attempt to reproduce the published 8/0/9 failed.** My
   constraint-based skeleton search on the observational file gave tp 16 /
   fp 26 at α=0.05, and stayed far off at α down to 1e-6
   (`reproduce_published.py`). Reported as a failure, not smoothed over. The
   likeliest reading: the published figure is the *DAG* inter.iamb returns,
   whose skeleton is not directly comparable to a liberally-tuned MB search;
   I could not close that gap, so I do not claim reproduction.
6. **Direction is lost.** My arms score skeleton only; the campaign's
   identifier produced directed edges. The port gives up a capacity, which is
   why the published mbde (which does orient) is far ahead.
7. **pgmpy's PC and HillClimbSearch are `PYTHONHASHSEED`-dependent.** Three
   unseeded reruns gave HillClimb tp ∈ {14,15,16}, fp ∈ {20,21}, and
   PC-pearsonr fp ∈ {1,2,3}; under `PYTHONHASHSEED=0` three runs are
   bit-identical (`7e72e7f4…` × 3). The frozen comparison uses the fixed
   hash seed. This is the **same defect class** I found in my own competence
   at turn 115 — now observed in a third-party published library.

## 5a. Prior art found during the search — the campaign's central insight is published

The survey turned up something that belongs in this report ahead of any
comparison. **Günther, Popescu, Rabel, Ninad, Gerhardus, Runge, "Causal
discovery with endogenous context variables", NeurIPS 37 (2024)**,
arXiv:2412.04981 — submitted 6 Dec 2024, i.e. **before** this campaign
(v1–v8 ran 2026-09). Registered source `src_3a8d4bcdbff5`, quote:

> We show that naive approaches such as learning different regime graphs on
> masked data, or pooling all data, can lead to uninformative results.

That is the campaign's central result — `CAMPAIGN_RESULT.md` §2.1, the
headline claim that pooling destroys context-exclusive structure — stated as
a known result in the causal-discovery literature, with a soundness proof for
an adaptive constraint-based algorithm and numerical comparisons against
baselines. It is not a coincidence of phrasing: the same paper names both
failure modes the campaign measured (per-regime graphs on masked data, and
pooling).

I am reporting this because it changes what the campaign's claim can be. The
stratified-contrast mechanism is a **re-derivation of a published idea**, not
a new one, and the campaign's six worlds cannot establish novelty that
already existed in print. The words I have used for it in earlier turns
("the line's central, self-contained result") were true about the line and
too strong about the world.

## 6. Independent verification (different code, disk only)

`verify_bench_independent.py` re-derives every arm with **scipy** instead of
the hand-rolled Fisher-z, parses the ground truth from the published file
again, and compares against the frozen outputs.

First pass: **26 disagreements.** Cause: my verifier indexed `X[a]` (a *row*,
11 values) where it needed `X[:,a]` (a *column*, 7466 values). Diagnosed
directly — scipy on the correct column gives rho 0.78507, p 0.0, matching the
measurement code's hand-rolled value to every digit; on the wrong axis it gave
rho 0.288, p 0.391. Fixed, re-run: **"ALL AGREE"**, zero disagreements. The
bug was in the check, not in the measurement — which is exactly why the check
has to be a different implementation.

Determinism: my two measurement scripts are bit-reproducible
(`results_bench2.json` sha256 `a5e1f949…` twice).

## 7. What this does to the campaign's claim

The campaign's line rested on one central, self-contained result: the
stratified identifier rejects the decoy 0/51 where the pooled identifier
accepts it 48/51, invariant to the decoy's price. Outside my worlds, on
someone else's benchmark:

* **it is not new** — §5a: the same insight, both failure modes named, is
  published (NeurIPS 2024) and predates the campaign;
* the **diagnosis survives** — pooled analysis produces false positives that
  context-stability removes (34 of 35 here), and that removal is significant
  (p = 0.0013);
* the **advantage does not** — at matched recall the ported mechanism ties
  inter.iamb and is beaten badly by the published intervention-aware method;
* and the **agentic half cannot be tested externally at all** without
  replacing it with a neural encoder.

So the honest summary of the transfer: the mechanism is a real and portable
*diagnostic* that already existed in the literature, and it is not a portable
*advantage*. The v1–v8 campaign measured the mechanism's internal behaviour
under controlled conditions; this measurement says that when the same
contrast rule is put on a benchmark it did not design, it recovers what a
standard constraint-based method already recovers, and no more.

## 8. Artefacts

* Preregistration (frozen before the first run): `bench_ext/PREREG_BENCH.md`
* Data (external, hashed): `bench_ext/ds/` — sources `src_16bafb0019c0`,
  `src_94f323687b6f`, `src_b54eb6d0fec2`
* Measurement: `bench_transfer.py`, `bench_transfer2.py`
* Published-method runs: `run_published_methods.py`,
  `reproduce_published.py`
* Comparison: `compare_published.py`, `headtohead.py`
* Independent check: `verify_bench_independent.py`
* Source registrations: `src_2e2fe669f2ec` (CausalWorld),
  `src_3438679a32ca`/`src_fb0bcfcaba94`/`src_ae0f06b05339` (CausalMBRL),
  `src_e8ed2b143798` (bnlearn Sachs HOWTO, published numbers),
  `src_3a8d4bcdbff5` (context-variable causal discovery, the literature this
  principle belongs to)
