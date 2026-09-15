# PREREG — external-benchmark transfer test (turn 127)

Frozen BEFORE the first measurement run. Owner directive msg_00127.

## 0. What the owner asked

The whole v1–v8 campaign ran on worlds I designed, populated, and checked
myself. That is right for falsifying a hypothesis under control, but it does
not show the mechanism works outside a world built so that it works. Task:

1. find an **existing, independently recognised** benchmark/dataset for
   causal discovery / causal induction in agentic or RL environments,
   made by someone else, before this campaign, **with published results of
   other methods** for comparison;
2. do not bend the benchmark to the mechanism — find one that existed
   independently of me;
3. test whether the **principle** (specificity / exclusivity inside a
   context vs a picture washed out over the pool) transfers to that
   benchmark's data structure — it may not, and that is itself a result;
4. compare against **published** results of existing methods, not a
   baseline I wrote; where no direct comparison exists, build it as
   honestly as possible and document every place I had to adapt;
5. if no suitable benchmark exists, or all require a neural component
   outside the original principle (not a Transformer/LLM core), say so
   plainly — that is also a valid and important result.

## 1. Survey — made before choosing (recorded as sources)

| candidate | what it is | independent of me? | published baselines? | non-neural tractable? | verdict |
|---|---|---|---|---|---|
| **CausalWorld** (Ahmed, Trauble et al., arXiv:2010.04296, 2020) | robotic-manipulation benchmark for causal structure + transfer | yes (MILA/MPI) | yes (baselines in-paper, curricula) | **NO** — PPO/vision policies, sim environment | **REJECT: neural/vision gate** |
| **CausalMBRL / Causal-Curiosity** (Sontakke et al. ICML'21; arXiv:2107.00848) | RL environments + evaluation criteria for causal induction in MBRL | yes (MILA) | yes (AE, VAE, Modular, GNN arms; published tables) | **NO** — env is `python=3.7.7` + `tensorflow=1.14.0=gpu` + 128-dim neural encoders (its own `environment_py37.yml`) | **REJECT: neural/vision gate** |
| **bnlearn / Sachs 2005 network** (Sachs et al., *Science* 2005) | protein-signalling network, 11 nodes, 9+1 experimental conditions, validated golden-standard DAG | yes (Sachs et al. 2005; bnlearn HOWTO by Scutari) | **YES — published, numeric, on the same data** | **YES** — tabular, no learned component required | **SELECT** |

Selection rule applied: the benchmark had to exist before the campaign, be
recognised by others, and be measurable without a component that replaces the
principle being tested. Two of the three candidates fail the third test, and
that failure is reported as a result in its own right (section 6).

## 2. The mechanism, stated as it will be tested

Campaign result (`research/CAMPAIGN_RESULT.md` section 2.1): a single pooled
contrast cannot separate "exclusive inside a context" from "exclusive in the
pooled table", so a pooled identifier accepted the designer decoy 48/51 while
a stratified identifier rejected it 0/51.

That is a claim with two halves:

* **epistemic half** — a within-context contrast of association recovers
  relations a pooled marginal structurally cannot see;
* **agentic half** — the agent *chooses* what to intervene on (C1) and
  *generates* its own candidate (C2).

Only the epistemic half can be tested on a frozen offline dataset, because
the interventions in Sachs were performed by the experimenters years ago.
This asymmetry is a finding, not a workaround (section 5, H4).

## 3. Data and ground truth (external, hashed on acquisition)

* observations: `ds/sachs.experimental.mixed.txt`
  sha256 `c1c4b12bdbb2c5411f7410fa65792a3191500e4b5276df2f7d1bf35a41a42c71`,
  700171 bytes, source `src_16bafb0019c0`
  (cmu-phil/example-causal-datasets, `real/sachs/data/`), 7466 rows:
  cols 0-10 = 11 log-transformed proteins, cols 11-19 = 9 intervention
  indicators.
* ground truth: `ds/sachs.ground.truth.graph.txt`
  sha256 `2406ec0f9cd34bcbcd33fb74282386232330a630dba68c0f2d01a0d985a652b9`,
  391 bytes, source `src_94f323687b6f`, 20 directed edges.
* pooled-only variant for the "no context" arm: `ds/sachs.2005.continuous.txt`
  sha256 `a488589b0f021b2a261ff2c696a908c6823051b0d98693e0fa0e78bb12097063`
  (source `src_b54eb6d0fec2`), the observational file with **no** indicator
  columns.

Context definition (frozen): a row's **stratum** is the set of specific
indicators active beyond the general stimulus `cd3_cd28`. Rows where only
`cd3_cd28` is active form the general/baseline stratum; each other indicator
defines one specific stratum. No indicator is invented by me.

## 4. Frozen procedure (no threshold moves after this point)

Association measure: Spearman rank correlation, Fisher-z transform,
two-sided normal p (n-3).

Pair set: all 55 unordered protein pairs; true-edge set = the 20 golden
edges (skeleton, direction ignored for E1-E3).

* **pooled** decision: p_pooled < 0.05 over all 7466 rows.
* **stratum** decision for pair (i,j): p_strat < 0.05/K in at least one of
  the K strata, K = number of strata with n >= 50 for that pair
  (Bonferroni within pair over strata).
* **pooled-visible** = pooled decision true.
* **context-exclusive** = pooled decision **false** AND stratum decision
  **true**. This is the operational analogue of the campaign's masked-
  exclusive edge: structurally invisible in the pool, present in a context.

Null model (the control, and it shares no assumption with the Fisher-z
decisions): each protein column is independently randomly permuted
(seeded, deterministic), destroying all joint structure while preserving
every marginal exactly; the whole pipeline is recomputed per replicate.

Frozen seeds: null replicates 200, base seed 20260912.
Primary statistic: **enrichment** = P(true edge | context-exclusive) /
base rate P(true edge) = (20/55).

## 5. Hypotheses, frozen with their falsifiers

* **H1 (visibility).** The pooled marginal can see only a minority of the 20
  golden edges. *Falsified if* pooled recall >= 0.75.
* **H2 (masking exists in this data).** Some true edges are context-exclusive
  by the section 4 definition. *Falsified if* that class is empty.
* **H3 (transfer).** Context-exclusive pairs are enriched for true edges
  relative to the base rate, beyond the permutation null. *Falsified if* the
  point enrichment <= 1 or the null >= the observed value.
* **H4 (the agentic half has no non-neural external benchmark).** *Falsified
  if* a non-neural external benchmark with published baselines is found
  during this turn.
* **H5 (adaptation cost, declared).** The offline dataset cannot exercise
  C1 (choice) or C2 (generation). Declared, not tested — reported as the
  boundary of the transfer.

## 6. What will be reported regardless of outcome

Every number with its null; the published comparison extracted from the
external source (inter.iamb pooled skeleton tp 8 / fp 0 / fn 9; intervention-
aware model averaging tp 17 / fp 8 / fn 0, both as published, quoted and
registered); the neural-gate rejections for CausalWorld and CausalMBRL with
their own manifest evidence; and every adaptation I was forced to make,
labelled as adaptation rather than measurement.
