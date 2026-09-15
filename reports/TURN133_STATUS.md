# TURN 133 STATUS — V9: the union mechanism transplanted into the EMCA agent

Owner directive **msg_00133**. Question: does the improved (context-specificity +
exploration, no broken cost-aware arbiter), partly formally proved causal
mechanism finally give a MEASURABLE ADVANTAGE in a full agent world?

**Answer: no — it loses significantly, and the reason is structural.**

## What was built

| file | role |
|---|---|
| `research/PREREG_V9.md` | preregistration, written before the first run |
| `union_layer_v9.py` | the union causal layer as a mixin (ctx contrast + exploration, no price) |
| `agent_emca_v9.py` | the arms; v7 arms re-exported byte-identical |
| `run_life_v9.py` | runner (v7 world construction, verbatim) |
| `driver_v9.py` | 180-cell matrix, resumable, PYTHONHASHSEED=0 |
| `analyze_v9.py` | verdicts (prereg V9 §3) |
| `verify_v9_independent.py` | independent pass, disk only, different code |
| `factcheck_v9_report.py` | every report number recomputed from frozen JSON |

## Headline numbers (all from frozen JSON, all independently recomputed)

* **H1** reward(union) − reward(v7) = **−104.7**, CI [−184.1, −55.0],
  perm p = **0.0020**, **0/10** seeds → **SIGNIFICANT LOSS**
* **H2** fruits: −0.80, CI [−1.60, +0.40] → NO ADVANTAGE
* **H4** true-edge CAUSAL **10/10**; decoy CAUSAL rows **0** of 87 verdicts → PASS
* **H5b** union vs noctx: **exact 0.0000 tie** (context split changes nothing here)
* **H3i/H3ii** FAIL as preregistered; the discriminating post-hoc readings are
  10/10 (contrast-source nomination, truth=on) vs **0/10** (truth=off)

## Why it loses (measured)

1. No price → no stop rule: mean probe trials **3595** on BOTH `rich=low` and
   `rich=high` (v7: 1080 / 880), first CAUSAL at t = 3872…9694 (v7: 3402…4996).
2. The exploration source floods the ranking: at the first probe the list holds
   **162 exploration rows / 13 contrast rows**; the true contrast edge sits at
   **rank 15–19 of 16–20** (median 18); exploration score 1.0 vs the true edge's
   measured contrast 0.2577.
3. `v9_noexp` (exploration off) is **identical to v7 on every non-log field,
   10/10** — so the union's entire difference from the old mechanism is the
   exploration term, and that term is what makes it lose.
4. The oracle does not rescue it: injected edge still buried, 3220 probe trials,
   217.9 reward.

## Controls

* transplant control: frozen v7 arm through the new runner == frozen v7 cell,
  behaviour 10/10 and log rows 10/10 modulo the new SOURCE label
* `v9_fixed` (designer list) nominates the true pair in **4/10** — exactly the 4
  seeds where the edge is `wait` — yet scores the highest reward of any probing
  arm (391.6): a cheap wrong fixed hypothesis beats an expensive correct
  self-generated one
* negative control: +5000 corruption of one cell flips the H1 reading
* determinism: seed 7 byte-identical across fresh processes (`616cc2d0…`)
* frozen files untouched: `env_terrarium_v7 1bfcba7a…`, `agent_emca_v7
  64a719d1…`, `candidate_gen fa9721ae…`, `arbitration 2d3d825b…`;
  `results/matrix_v7/` 110 cells unchanged

## Defects found in my own work this turn (reported, not hidden)

1. `analyze_v9.verdict_advantage` first tested only "CI excludes 0", labelling a
   significant LOSS as ADVANTAGE. Directional gate restored.
2. `union_layer_v9._plan` logged the score in position 2, so a reader filtering
   on the source label filtered nothing (two nomination readings came out
   identical). Fixed (label now position 4); matrix re-run; **0 decision-field
   diffs / 180 cells** against the pre-fix matrix, preserved at
   `results/matrix_v9_prelogfix/`.
3. `verify_v9_independent` checks B2/C2 first compared whole records (failing on
   key presence) and my first label-stripper did not recurse. Both fixed; the
   verifier now passes 13/13 with the negative control live.

## Verification record

* `experiment_run` id **exp_380c20ebe00d** — the independent verifier,
  exit 0, stdout sha `7f71a8ae…`, 13 checks / 0 failures.
* Analysis: `results/analysis_v9.txt`; factcheck: `results/factcheck_v9.txt`.

## Honest limits

n = 10 seeds; `v9_oracle` is an analysis device; the stop rule (`v9_stop`)
halves the loss (−59.7) but does not beat v7 either, so the fix does not rescue
the mechanism; the v7 world's own oracle verification was done in turn 124 and is
not repeated (the transplant control replaces it).
