# TURN 128 STATUS — causal bandits: the active half (C1 + C2) on an independent area

Directive: msg_00128. Status: **complete, one continuous run, verified.**

## What was asked

Turn 127 tested the epistemic half on frozen data and reported a negative. The
owner asked for a **different angle**: find an independent, non-neural area where
the **active** half (C1 choice + C2 generation together) has published
benchmarks, algorithms, or regret bounds; compare the mechanism honestly; and if
no such area exists, say so plainly.

## What was done

1. **Surveyed the area before choosing** (`PREREG_CB.md` §1, sources registered):
   causal bandits (arXiv:1606.03203, the founding paper), structural causal
   bandits/POMIS, budgeted causal bandits (arXiv:2012.07058), CN-UCB causal
   trees/forests (arXiv:2106.02988), plus the two neural-gated benchmarks already
   rejected in turn 127. **Verdict: the area exists, is non-neural, and publishes
   both upper and lower regret bounds. H1 SURVIVES.**
2. **Froze the instance, thresholds and hypotheses before the first run**
   (`PREREG_CB.md`; the file is timestamped and its sha256 is recorded in
   `results_cb_meta.json`).
3. **Took the authors' own published code** as the comparator: fetched
   `finnhacks42/causal_bandits` (tarball sha `17e4584d…`), kept the unmodified
   bytes in `ext/latt_src/`, ported Py2→Py3 mechanically (every edit in
   `ext/PORTS_diff_*.txt`), and **verified the port against a published figure**
   — their Figure 2a shape reproduces (Algorithm 1 rises with `m`, Successive
   Rejects is exactly flat, Algorithm 1 crosses below SR between m=16 and m=25).
4. **Ported the campaign's active half unchanged**: `candidate_gen.py` and
   `arbitration.py` imported byte-identical (hashes in `results_cb_meta.json`).
5. **Ran the grid**: 72 cells × 1000 simulations, `m ∈ {2,8,16,25,40,49}`,
   T=400, N=50, eps=0.3, seeds 1..1000.
6. **Ran three follow-up measurements** to avoid over-claiming: a
   natural-occurrence family (q1 swept, 56 cells), a C1-isolation control
   (inject a true hypothesis), and the bounding controls (greedy / random /
   oracle) plus a beta sweep and a horizon sweep.
7. **Independent verification** (different code, disk only, negative control
   that must fail): first pass 6 disagreements — 2 real (one was a wrong claim
   of mine, one a bug in the verifier) — fixed; second pass **190 checks, 0
   disagreements**.
8. **Factcheck of the report**: 158 numbers re-derived from the frozen JSON,
   0 failures.

## The result

* **H1 SURVIVES** — an independent non-neural area for the active half exists.
* **H2 FAILS, maximally** — the mechanism scores the **worst possible regret
  0.300 at every m**; the published Algorithm 1 scores 0.000–0.257 and plain UCB
  0.000–0.236. It selects a 0.5-reward arm in 100 % of 6000 runs.
* **Cause** — the generator is silent in **99.9 %** of calls (the optimal arm
  has zero natural occurrences, and the generator's bar needs 40 trials), so the
  arbiter is never exercised. **C2 fails and takes C1 down with it.**
* **C1 isolated is sound** — handed a true hypothesis, the frozen arbiter probes
  it and finds the optimum in **100 %** of runs, identical to the bar-removed
  control. The decision rule is not the problem.
* **The mechanism has no operating region of its own** — across the
  natural-occurrence family it reaches zero regret only where a plain greedy
  estimator already does, and it never beats plain UCB anywhere.
* **Prior art (H6 SURVIVES, and it matters most)** — both missing pieces are
  published: exploration (Algorithm 2 of the same 2016 paper; CN-UCB 2021) and
  the cost-aware observation/intervention trade-off (arXiv:2012.07058). The
  arbiter's idea is a re-derivation of a published trade-off.

## Honest limits

* The supplementary two-parent instance is **mine, not published**; every number
  from it is labelled supplementary and never compared to a published figure.
* 1000 sims/cell, not the paper's 10 000 — declared.
* The `sqrt(m(q)/T)` diagnostic is a shape diagnostic only; no violation of the
  published bound is claimed (the Θ-constants are unpublished).
* `unc` and `boot1/boot5` are **declared adaptations**, never called the
  mechanism.
* The port's observational half (A1') is an addition the campaign agent did not
  have (it foraged); it is the same split the published Algorithm 1 uses.

## Artefacts

* `bench_cb/PREREG_CB.md` (art_5ddf6ff5631d), `bench_cb/RESULTS_CB.md`
  (art_215487540307)
* `bench_cb/results_cb/` (72 cells), `results_cb_family/` (56), `results_cb_iso/` (5)
* `bench_cb/verify_cb_independent.py` + `verify_cb_out.txt` (ALL AGREE)
* `bench_cb/factcheck_cb_report.py` (158/158 OK)
* `bench_cb/results_cb_meta.json` (all module and external-code hashes)
* sources: `src_6a2ee36a7d5d`, `src_0f710f512030`, `src_88cb0221447d`,
  `src_e6e9978c4ec3`
