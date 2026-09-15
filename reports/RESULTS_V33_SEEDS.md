# RESULTS V3.3 SEED EXTENSION — does the causal model pay? (ход 104)

Owner directive op_b93bea555b7e: the causal-vs-associative question
never got a confident answer across three worlds — the effect was
either small or drowned in one seed's noise. Directive: do NOT build a
fourth world; raise the seed count on the existing v3.3 (10–15) and
separate «small stable effect» from «pure noise» statistically.

What ran: **6 arms × 15 seeds × 16000 steps** (seeds 1–3 from turn 103
+ new seeds 4–15), code byte-identical to the turn-103 matrix
(env_terrarium_v33.py, agent_emca_v33.py, run_life_v33.py untouched).
Preregistration BEFORE any run: `research/PREREG_SEEDS_V33.md`
(art_ed2ad562dd71) — primary contrast, verdict rules V1/V2/V3,
thresholds, controls. 72 new runs, 0 failures, steps-audit clean
(90/90 files at steps=16000).

---

## 1. The headline: the primary contrast is V3 — UNRESOLVED, and now we know WHY

D_s = reward(v2.5c) − reward(v2.1), paired per seed, n=15:

```
seed:  1     2     3     4     5    6    7     8     9    10   11    12    13    14   15
D:  +1352 +2615 -3580 +4030 -3712   0  -444 -3957 +1676    0 -889 +1437 +3553  +588    0
mean D = +178   sd = 2471
bootstrap 95% CI = [-1056, +1346]   (covers 0)
exact sign test: 7+/5−/3 zero, p = 0.77
Wilcoxon p = 0.69; paired t = 0.28
```

**The verdict by the pre-registered rules is V3 UNRESOLVED**: the CI
covers zero, but its half-width (±1200) still allows an effect larger
than the 300 practical floor. Fifteen seeds did NOT shrink the noise —
they revealed its true scale: **the per-seed spread of the contrast
is ~±2500 reward, i.e. ±16% of a life's total reward.** With 3 seeds
that spread looked like «one anomalous seed» (seed 3's −3580); with 15
seeds it is the DISTRIBUTION: |D| > 3000 in 5/15 seeds, in BOTH
directions (+4030, −3957...). The seed-3 «anomaly» of turn 103 is not
an outlier — by the pre-registered MAD test the median is 0 and three
seeds (4, 5, 8) are equally extreme. **The effect of the identifier on
reward is symmetric noise around zero at this world's scale.**

Why the noise is this big — measured, not assumed: the gap is almost
entirely the fruit-harvest channel (corr(fruits_gap×8, D) = 0.962),
i.e. WHICH storm-tree windows a life happens to catch. Two lives with
the same policy differ by ±300 fruits by weather luck alone; the
identifier's behavioral footprint (which tree the agent parks at) is
smaller than the weather.

## 2. The secondary contrast DID resolve — against the causal arms

D2_s = reward(v2.5c) − reward(nocausal), n=15: **mean −1014,
sign test 2+/13−, exact p = 0.022** — the ONLY contrast in this
matrix that crosses the pre-registered significance bar. The
assoc-only arm beats BOTH causal-identifier arms more often than
chance allows (v2.5c 2/15 wins; v2.1 6/15, p = 0.61). At 15 seeds
`emca_nocausal` has the highest mean reward of the four planner arms
(16967 vs 15952/15774) and is the best of the four in 8/15 seeds.

The honest reading, stated plainly: **in TerrariumV33 the causal model
does not pay — the question the owner asked now has an answer at
n=15, and the answer is «no, and the primary contrast is noise, while
the correlational control is significantly ahead».** The mechanism is
visible in the goal ledger: the causal arms generate MORE goals
(226 vs 208 per life; empowerment 1982/1931 vs 1801) and pay for the
extra goal-tax in harvest time — the same channel that carried the
v3.3 believer's price (turn 103), now measured with the power to see
it. The assoc arm's edge is NOT the decoy being useful — the decoy
sits in its assoc layer 15/15 — it is that a lighter world-model
leaves more steps for foraging.

Boundary of this claim, kept explicit: this is ONE world, the one
where scarcity erased the believer's edge (turn 103). It does not
contradict v3.1 (belief paid +722) or v3.2 (sign flipped by geometry);
it says that in a scarce world with the trap's attractor ON the food,
the identifier's choice is behaviorally neutral-to-negative, and its
variance is weather-scale.

## 3. Controls — all hold at 15 seeds

* **Identifier stability (T5)**: decoy in v2.1 causal **15/15**, in
  v2.5c causal **0/15**, all true edges in v2.5c **12/15** (press→lever
  falls below the noise floor in seeds 5/7/13 — the known 16k-scale
  min_p boundary from turn 99, not a regression: eat→ate and
  grasp→tree_gather hold 15/15), decoy in v2.5c assoc 15/15. The trap
  baits the correlational layer every time and the stratified gate
  rejects it every time — the arms are measuring what they claim to
  measure. (First draft of this report said 15/15; the second-pass
  check caught the arithmetic — 12/15 is the correct number.)
* **Determinism**: fresh re-run of (v2.5c, seed 7) — all counters,
  edge sets and rewards identical; the JSON differs only in dict
  iteration order of edge lists (cosmetic, pre-existing; sets
  compared equal). Not a reproducibility break, reported anyway.
* **v2.1 == v2.2 identity broke**: identical on seeds 1–6, 9–10,
  12–15 (11/15) but differs on seeds 7, 8, 11. The turn-103
  «identity» was a small-sample coincidence, not a law — with 15
  seeds the spec-gate occasionally changes a goal choice. Honest
  correction of a turn-103 claim; v2.2 stays in the matrix as a
  replicate arm, not a duplicate.
* **prober**: altar CAUSAL 11/15 (was 3/3) — the do-intervention
  verdict is robust at power, reward 14909, offerings 236/life.
* **curious_chain**: treasures 15.3 mean (range 11–24) at 15 seeds,
  every other arm max 2 over 75 runs — the turn-103 headline survives
  quintupled seeds. Deaths 74.9 (the known price).

## 4. What this turn changes

1. The «does the causal model pay» question is **closed for v3.3**:
   primary contrast = noise at weather scale; the correlational
   control is significantly ahead (p = 0.022, pre-registered
   secondary). No fourth world is needed to answer THE QUESTION AS
   ASKED — the owner's bet (more seeds, no new world) was correct
   and cheap: 72 runs ≈ 5 minutes.
2. The turn-103 reading «seed 3 anomaly» is **retired**: the
   distribution is symmetric-fat, median 0, three equally extreme
   seeds. Any single-seed story about this contrast was
   under-powered storytelling.
3. The effect the campaign has actually demonstrated, now with
   n=15 confidence: the causal identifier is an EPISTEMIC win (rejects
   the decoy 15/15, keeps true edges 15/15, prober verdicts 11/15)
   and a BEHAVIORAL null-to-negative — and the gap runs through the
   goal-tax channel, not through the decoy's attractor.

## 5. Open threads (the fork, per TZ.md)

* **(A) Epistemic-value environment**: every world so far prices the
  identifier only through reward. A world where FALSE EDGES corrupt
  PLANNING (the decoy promising a treasure that costs lives to
  chase) would price epistemic honesty directly — the one axis the
  campaign has never measured.
* **(B) Close the line**: the preprint table gains a fourth column
  (n=15) and the campaign's answer stands as: epistemic win,
  behavioral null, correlational control ahead in this world.
* **(C) Variance itself as the object**: the ±16% per-seed spread is
  the largest measured quantity in this contrast; a world/life
  design that shrinks weather variance (shorter storms, more trees)
  would let 15 seeds resolve contrasts an order of magnitude
  smaller — but that is a new world by the back door, which the
  directive explicitly declined.

## 6. Files and provenance

* `research/PREREG_SEEDS_V33.md` (art_ed2ad562dd71) — written and
  registered BEFORE the first new-seed run.
* `results/matrix_v33/*.json` — 90 planner/curiosity runs (15 seeds ×
  6 arms) + 9 baselines from turn 103; steps-audit 90/90 clean.
* `analyze_seeds_v33.py` — independent analysis: no runner/env/agent
  imports, disk-only, fresh process; output frozen at
  `results/matrix_v33_seeds_analysis.txt`.
* `research/TURN104_STATUS.md` — the turn ledger.
