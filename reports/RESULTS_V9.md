# RESULTS V9 — the union mechanism transplanted into the EMCA agent, on the original Terrarium world

Turn 133, owner directive **msg_00133**. Preregistration written before the first
run of any v9 arm: `research/PREREG_V9.md`. Frozen world: `env_terrarium_v7.py`
(untouched, byte-identical). Frozen comparator: `agent_emca_v7.py` (untouched).

**Headline, and it is the first sentence on purpose.** The improved mechanism
does **not** buy an advantage in the full agent world. Transplanted into the EMCA
agent and run on the original Terrarium (goals, planning, memory), the two-part
union **loses significantly** to the mechanism it replaced:

    H1  reward(union) − reward(v7)  =  −104.7   CI [−184.1, −55.0]   perm p = 0.0020   0/10 seeds

and the reason is measured, not guessed: **the union has no stop rule, and its
exploration source floods the ranked list so completely that the true edge is
buried under decoys.** The price the union removed was, in this world, the brake
that made the agent stop probing and start collecting. Removing it removed the
exploitation.

---

## 1. What was transplanted, exactly

The v7 agent's causal layer — `_candidates()` (generator + designer list +
permutation + injection) and `_plan()` (the priced arbiter `arbitration.plan`) —
was replaced by `union_layer_v9.UnionCausalLayer`:

* **source 1, context contrast:** `candidate_gen.generate` (imported
  byte-identical, sha `fa9721ae…`) over the agent's per-context tables;
* **source 2, exploration under thin evidence** (the turn-129 term, unchanged):
  every item the agent has not resolved in some context it has seen, scored by
  its optimistic gain in the worst-covered context;
* **ranking:** `(-score, trials, action)`;
* **decision:** the top unverified candidate is probed. **No price, no beta, no
  arbiter** — the turn-132 recommended two-part composition.

Everything else is inherited verbatim from `AgentV7Base`: the filing path and
context attribution, the aura probe protocol (alternated blocks, exact Fisher
p<0.05 and RR≥1.3, `PROBE_MAX_BLOCKS=80`), survival, the exploration schedule
(`EXPLORE_END=3000`), navigation, the goal/planning layer and the exploitation
branch. The world is not touched.

**The one structural fact the proposal had to meet, declared in the prereg before
the first run.** In v7 the exploitation branch fires when the arbiter's accepted
list is **empty**. Removing the price removes the only thing that ever emptied
that list. The unconditional arm therefore has no stop rule, and since one
candidate costs up to 800 scheduled steps while the world offers ~28
(action, effect) pairs, it can spend the whole life probing. The prereg predicted
exactly this (prediction 1) and predicted the arm would therefore lose. It did.

**Internal transplant control (prereg §2), and it passed.** The frozen v7 arm run
through the NEW runner `run_life_v9.py` reproduces the frozen v7 cell on **every
field except the three v9-only log fields — 10/10 seeds, 0 value diffs**
(`verify_v9_independent.py` check B). The runner did not leak into the shared
machinery.

## 2. The matrix

180 cells: BASE 9 arms × 10 seeds, CONFLICT 6 arms × 10 seeds (`rich=high`),
OFF 3 arms × 10 seeds (`truth=off`); 16000 steps, `PYTHONHASHSEED=0`,
`edge_action` randomised by seed. All 180 complete, 0 driver failures.
Determinism: seed 7 re-run in two fresh processes gives a byte-identical JSON
(sha `616cc2d0…`, the post-log-fix matrix).

## 3. The verdicts (prereg V9 §3, thresholds unchanged)

| # | claim | result | verdict |
|---|---|---|---|
| **H1** | `reward(union) > reward(v7)` | −104.7, CI [−184.1, −55.0], perm p = 0.0020, 0/10 seeds | **SIGNIFICANT LOSS** |
| **H2** | `fruits(union) > fruits(v7)` | −0.80, CI [−1.60, +0.40], 1/10 | **NO ADVANTAGE** |
| H1b | `reward(stop) > reward(v7)` | −59.7, CI [−154.1, +5.0], 2/10 | NO ADVANTAGE |
| H5a | `union ≥ noexp` | −104.7, CI [−184.1, −55.0], 0/10 | **SIGNIFICANT LOSS** |
| H5b | `union ≥ noctx` | 0.0000, CI [0,0] | exact tie |
| H3i | true pair nominated ≥8/10 (on) and ≤2/10 (off) | **10/10 on, 6/10 off** | **FAIL** |
| H3ii | first probe = argmax of own ranked list ≥8/10 | 6/10 | **FAIL** |
| **H4** | true-edge CAUSAL ≥8/10 | **10/10**, decoy CAUSAL rows **0** of 87 verdicts | **PASS** |
| H6 | hardcode control | see §5 | **PASS** |

Independent recomputation (different code, disk only, different bootstrap RNG,
plus an exhaustive sign-flip permutation): **identical** — H1 mean −104.715,
CI [−184.145, −55.000], perm p = 0.0020.

## 4. Why it loses — the mechanism, measured

**(a) The union cannot see the price, and does not need to — but it also cannot
stop.** Mean probe trials are **3595** on `rich=low` and **3595** on `rich=high`:
identical, because there is no price term. The v7 arm spent **1080** (low) and
**880** (high). The union spends 3.3× the v7 probe budget and, in the conflict
world, 4.1× — and reaches its first CAUSAL verdict only at t = 3872…9694 (v7:
3402…4993). It arrives at the exploitation branch late, having paid for the
privilege.

**(b) The exploration source dominates the ranked list, and the true edge is
buried.** At the first probe the ranked list holds **162 exploration rows and 13
contrast rows**; the top of the list is an exploration row in **10/10** seeds,
never the true contrast edge. The exploration score is `1 − best_rate_in_ctx`,
which for a thin context is **1.0** — higher than any real measured contrast
(the true edge's own contrast score is **0.2577**). The measured consequence: the
true contrast edge sits at **rank 15–19 of a list 16–20 long** at the first probe
(median rank **18**; in seed 3 it is not in the list yet at all). So the union
probes decoys and berries while the true edge waits near the bottom of its own
list.

**(c) The ablation that removes exploration is the exact v7 behaviour.**
`v9_noexp` (contrast only, unconditional probe) is **identical to `v9_old` on
every non-log field, 10/10 seeds** (verifier check C). In this world, dropping
the exploration term from the union reproduces the priced arbiter's entire
trajectory — because the arbiter's price, at `rich=low`, admitted essentially the
same two candidates the contrast source nominates. **The union's advantage over
the old mechanism is therefore carried entirely by the exploration term, and that
term is what makes it lose.**

**(d) Context-specificity contributes nothing here.** `v9_noctx` (pooled
discovery + exploration) is **bit-identical to `v9_union`, 10/10 seeds** — H5b is
an exact tie. In the v7 world the context split changes no decision, because the
exploration source's score-1.0 candidates dominate the ranking before the
contrast source can matter.

**(e) The oracle does not rescue it.** The injected-edge device (`v9_oracle`)
still spends 3220 probe trials and scores 217.9 — no better than the union's
202.9 — because the injected candidate (score 0.10) is also buried under the
score-1.0 exploration rows. The ceiling is not reached by the mechanism even when
it is handed the answer.

## 5. Controls, all live

* **H6 hidden hardcode:** `v9_fixed` (designer list `wait→hum`, unconditional
  probe) nominates the true pair in **4/10** seeds — **exactly the 4 seeds where
  the seed-randomised edge happens to be `wait`**. It nonetheless scores the
  **highest reward of any probing arm (391.6)** on only 400 probe trials: in this
  world a cheap, wrong, fixed hypothesis beats an expensive, self-generated,
  correct one. That is the sharpest statement of the negative result.
* **H4 verification:** the true edge is accepted CAUSAL **10/10**, the decoy is
  never accepted (0 CAUSAL rows among 87 verdicts). Nominal null rate of the
  frozen rule is 0.488% per test (turns 124/125), so E[FP] = 0.42; observed 0.
  The gate "FP = 0" is reported as passed by the letter here, with the frequency
  beside it.
* **Forager floor:** 668.4 reward, 7 deaths, 0 fruits — the blind floor is far
  above every probing arm, and the union's exploration tax is why.
* **Negative control:** corrupting one cell's reward by +5000 flips the H1
  reading (clean mean −104.7 → corrupt +395.3), so the verifier can go red.

## 6. Honest corrections made during this turn

1. **A defect in my own analyzer, found by reading its first output.** The
   first `verdict_advantage` tested only "the CI excludes zero", which labels a
   significant **loss** as ADVANTAGE. The prereg gate is directional; the code
   now is too. The bug is reported, not silently fixed.
2. **A defect in my own logging, found by the factcheck.** `candidates_seen`
   logged `(action, effect, score, trials)` — the score in position 2 — so a
   reader filtering on the source label compared a float to `'thin-ctx'` and
   filtered nothing, which made two nomination readings identical. The decision
   path was never affected (it uses the namedtuple). Fixed: the label is now
   position 4. The matrix was **re-run from scratch**; every decision-relevant
   field is **bit-identical to the pre-fix matrix (0 diffs / 180 cells)**, and
   the pre-fix matrix is preserved as evidence at `results/matrix_v9_prelogfix/`.
3. **H3's two readings are reported as post-hoc, not as verdict flips.** The
   preregistered H3i/H3ii were inherited from v7, where the candidate list was not
   deliberately permissive; the union's exploration source nominates everything,
   so both tests answer "is the list permissive?" The discriminating readings —
   contrast-source nomination 10/10 on / **0/10 off**, and first probe = top
   *probeable* candidate 10/10 — are labelled `POSTHOC_` in the analysis and do
   not change any verdict above.

## 7. What this means for the campaign's claim

Turn 127: the epistemic half transfers as a diagnostic, not as an advantage.
Turn 128: the active half does not act at all on the causal-bandit instance.
Turn 132: the priced union is a tie on the main instance and a loss on the rich
one. **Turn 133: the improved, unpriced, partly formally proved mechanism, put
back into the full agent world it was built for, loses to the mechanism it
replaced — and the reason is structural, not statistical.** The union is a
better *hypothesis generator* (it nominates the true edge 10/10 where the
designer list manages 4/10) and a worse *agent*, because it has no rule for
stopping. In v7 the price was doing two jobs — pricing truth, and stopping the
search. Turn 132 showed the pricing job was a tax. Turn 133 shows the stopping
job was load-bearing: remove it and the agent never gets to spend what it knows.

## 8. Artefacts

* Preregistration: `research/PREREG_V9.md`
* Union layer: `union_layer_v9.py`; arms: `agent_emca_v9.py`;
  runner: `run_life_v9.py`; driver: `driver_v9.py`
* Matrix: `results/matrix_v9/` (180 cells); pre-fix matrix preserved:
  `results/matrix_v9_prelogfix/`
* Analysis: `analyze_v9.py`, `results/analysis_v9.txt`, `results/analysis_v9.json`
* Independent verifier: `verify_v9_independent.py`,
  `results/verify_v9_independent.txt` (11 checks, 0 failures)
* Factcheck: `factcheck_v9_report.py`, `results/factcheck_v9.txt`
* Frozen, untouched: `env_terrarium_v7.py`, `agent_emca_v7.py`,
  `candidate_gen.py` (`fa9721ae…`), `arbitration.py` (`2d3d825b…`),
  `results/matrix_v7/` (110 cells)

## 9. Limits, declared

1. n = 10 seeds; the seed-level contrasts are paired and bit-reproducible, but
   the sign tests are not powered beyond 10.
2. `v9_oracle` is an analysis device, never in a fairness verdict.
3. The stop rule (`v9_stop`) was added as part of the design, not as a rescue;
   it improves on the union (−59.7 vs −104.7) but does **not** beat v7 either —
   so the fix does not rescue the mechanism, it only halves the loss.
4. The world is the frozen v7 world; its oracle verification was done in turn 124
   and is not repeated here — the internal transplant control (§1) replaces it.
