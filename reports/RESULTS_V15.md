# RESULTS V15 — the SEAM architecture: an agent with no reward, no cost, no death

Turn 148, owner directive msg_00147/msg_00148 (verbatim in
`PREREG_V15.md` §0). Preregistration written before the first cell:
`research/PREREG_V15.md`. World: `env_v15.py`; agent: `agent_v15.py`;
runner: `run_life_v15.py`; driver: `driver_v15.py`; matrix:
`results/matrix_v15/` (210 cells).

**The headline, first sentence on purpose.** An agent with **no reward,
no energy, no death and no prior preferences** does learn the true
context-indexed structure of its world (model error 0.036 against a
ceiling of 0.033) — **but pure information gain gives it no reason to
act on what it learned.** Its action distribution is statistically
indistinguishable from random (a0_share 0.250 ± 0.005, 10/10 seeds,
versus 0.250 for `rand`). The moment a **criterion** is added — "prefer
the channel whose rate differs across contexts" — the same agent spends
99.8% of its steps on the true channel. **The criterion is a preference
over states. That is the seam's answer to the owner's question: truth
alone does not select action; a preference does.**

---

## 1. What was built, and what each part is inherited from

Per the owner's explicit requirement, every component is labelled:

| component | inherited from | blind spot of that source |
|---|---|---|
| predict the **representation** of the next observation, never reconstruct | JEPA / I-JEPA (`src_c71f7fa65f68`) | no agent, no action selection, no memory across episodes, no context index |
| select actions by **expected information gain**, prior-preference term REMOVED | active inference / free-energy principle (`src_973284d453d0`, `src_…2212.01354`) | keeps prior preferences (a goal); needs an explicit generative model; scales poorly |
| compute the contrast **within a context**, not pooled | the campaign's own v3–v9 line (`EPISTEMIC_VERDICT.md` §4.1: 0/51 vs 48/51) | built for a reward-bearing world; never tested without a goal |
| **AT THE SEAM (new)** | — | a context-indexed, representation-space, **epistemic-only** agent with no reward/energy/death/priors, whose own drive is measured for fakeability on its own channel |

**No single source has (a) no goal AND (b) a context index AND (c) a
fakeability test of its own drive.** v15 is that intersection. It is not
a re-description of JEPA (JEPA has no agent) or of active inference
(active inference has priors and a goal).

## 2. The world is reward-free by construction, and this is verified

Observation is exactly `{phase, feat, val}`. The independent pass
re-derives this from the raw bytes: **no `reward`, `energy`, `alive` or
`died` key exists in any of the 210 cells** (check A3), and the trace
schema is exactly `{t, phase, feat, val, action, pred_f0}` (check A4).
There is nothing in the world that is "good" or "bad".

The structural fact the seam rests on (oracle O14/O15): the true channel
`a0` has rate **0.9 in phase A and 0.1 in phase B**, so **pooled over
contexts it is 0.5 — identical to noise.** Only a context-indexed model
can see it.

## 3. The verdicts

| # | claim | measured | verdict |
|---|---|---|---|
| **H1** | `ig_ctx` learns the true structure (err < 0.08) | **0.0364** (ceiling `ig_ctx_oracle` 0.0327) | **PASS** |
| **H2** | pure IG leaves the agent **indifferent** (a0_share ≈ 0.25) | **0.250**, range [0.246,0.255], **10/10** | **PASS — the core result** |
| **H3** | a relevance criterion restores the preference (>0.95) | **0.998**, range [0.995,1.000], **10/10** | **PASS** |
| **H4** | pooled (no context index) cannot learn (err > 0.5) | **0.8000** | **PASS** |
| **H5** | the high-entropy drive is captured by the noisy TV | tv a3_share **0.300**, base **0.000** | **PASS** |
| **H6** | `rand` a0_share ≈ 0.25 | **0.250** | **PASS** |

All six preregistered hypotheses confirmed. **H2 is the one that
matters**, and it is the honest answer to the owner's question.

## 4. What the numbers mean, precisely

**(a) Learning without a goal works.** `ig_ctx` reaches model error
0.036, close to the oracle ceiling 0.033 — it learns the context-indexed
truth with no reward anywhere. Representation-space prediction plus a
context index is sufficient for **learning**.

**(b) Learning is not acting.** After learning, `ig_ctx`'s a0_share is
0.250 — **the same as `rand`** (0.250) and the same as `ig_pooled`
(0.250). The agent knows the true structure and does nothing different
because of it. Why, measured: once every channel is learned, every
channel's expected information gain decays to the same floor
(`ig_ctx` base: IG_A(a0)=0.00025, IG_A(a3)=0.00000) — the agent declares
itself unmotivated on **97.3%** of steps and acts at random. **Pure
information gain has no term that distinguishes a channel that matters
from one that does not.**

**(c) The criterion is what selects action.** `ig_relevant` adds one
term — "score 0 unless the channel's rate differs across contexts by
>0.20" — and a0_share jumps from 0.250 to **0.998**. The contrast is
paired and enormous: `ig_ctx − ig_relevant = −0.7475`, CI
[−0.7504,−0.7446], **0/10 seeds**. The term that made the agent act is
**not information** — it is a **preference over which states matter**.

**(d) The drive itself is fakeable.** `naive_info` (score = outcome
entropy) is drawn to the noisy TV: a3_share **0.300** in the `tv` regime
versus **0.000** in `base`. The never-resolving channel captures the
drive completely. Note the sharp asymmetry: `naive_info`'s a0_share is
**0.000** — it never once touches the true channel, because the true
channel's outcomes are *less* entropic than noise. **An entropy-seeking
drive is not just indifferent to truth — it is actively repelled by it.**

**(e) The pooled trap is real.** `ig_pooled` (no context index) reaches
model error **0.8000** — it cannot learn a structure that is invisible
when contexts are merged. Context specificity is load-bearing, exactly
as the v3–v9 line found in a reward-bearing world.

**(f) The confirmation control sits in between.** `confirm` (seek
confirmation) parks on a0 at a0_share **0.500** — it prefers whichever
channel is most predictable, which is a preference, but not for the true
channel; it never learns (err 0.4135).

## 5. The honest answer to the owner's question

The owner asked: *can an agent act without a preference over world
states, or does "truth" inevitably hide a goal?*

**Measured answer, in this architecture: truth alone does not select
action.** An agent that only minimises its own uncertainty learns the
world perfectly and then does nothing in particular — its behaviour is
indistinguishable from random. To act, it needs a term that says *which*
uncertainty matters, and that term is a preference over states. The
preference can be made epistemic in *form* (a relevance criterion rather
than a reward), but it is a criterion all the same, and a criterion is a
goal.

This is the collapse the owner named as an acceptable outcome ("если
после честной попытки … всё равно упрёшься в тот же вывод … это тоже
честный, важный результат"). It happened. But it is **weaker and more
precise** than the general claim, and I state the difference:

* The collapse is **not** "any action requires a reward". It requires a
  **criterion** — and a criterion can be purely epistemic (no reward, no
  cost, no death). `ig_relevant` has no reward; it has a relevance
  preference. So the seam is real: an agent can be **reward-free** and
  still act.
* The collapse **is** "any action requires a preference over which
  states matter". Information gain alone is not such a preference; it is
  symmetric over channels. Something must break the symmetry, and
  whatever breaks it is a goal.
* And the drive that breaks it is **fakeable on its own channel**: the
  entropy drive is captured by the noisy TV (0.300). So the v11–v14
  lesson recurs one level up — the risk moves from the reward channel to
  the **evidence channel**, exactly as predicted in turn 146.

## 6. How it was verified

* **World oracle** `verify_env_v15.py`: **21/21**, including the pooled
  trap (O14/O15), the non-stationary decoy (O16), determinism (O17/O18),
  the exact observation schema (O19/O20), and a **live negative control**
  (NV1: a perturbed world fails the true-rate check).
* **Independent pass** `verify_v15_independent.py`: **13/13** — fresh
  process, **disk only**, imports neither `env_v15` nor `agent_v15` nor
  `run_life_v15`; recomputes every metric from the trace with its own
  code; includes a live negative control (NV1).
* **Determinism:** seed 3 re-run in a fresh process gives a
  byte-identical JSON (sha `43a1a6a348e75fa1`).
* **Factcheck** `factcheck_v15.py`: every number in this report checked
  against the raw cells.

## 7. Defects found in my own work during this turn

1. **My first negative control was too weak.** NV1 corrupted only 1000
   of 16000 steps, moving a0_share from 0.250 to 0.234 — **not** enough
   to fail the indifference check, so the control could not go red. I
   found it by running the verifier and reading the FAIL; fixed to
   corrupt the whole trace (now 0.000, correctly red). **The control was
   broken, not the world.**
2. **The driver crashed on the first `tv` run** — `run()` did not accept
   the `tv` kwarg. Found immediately (70 failures), fixed, matrix re-run
   from scratch.
3. **The runtime raised a WRITESET ALERT** on `/data/resume_state.jsonl`
   — its own resume-state writer, not my scripts (my scripts write only
   under `results/`). Surfaced, not swallowed.

## 8. Limits, declared

1. n = 10 seeds; the paired contrasts are bit-reproducible, but the sign
   tests are not powered beyond 10.
2. `ig_ctx_oracle` is an analysis device, never in a fairness verdict.
3. The world is deliberately minimal (4 channels, binary outcomes). The
   seam claim is about the *structure* of the drive, not about scale.
4. The relevance criterion `ig_relevant` uses `REL_MARGIN=0.20`, a
   declared constant; the result is not sensitive to it across
   0.1–0.4 (the true gap is 0.8, the noise gap is 0.0).
5. **This is not a claim of a fundamentally new intelligence.** It is a
   measured intersection of three known ideas, and §1 names exactly which
   part comes from which.

## 9. Artefacts

* Preregistration: `research/PREREG_V15.md`
* World: `env_v15.py`; agent: `agent_v15.py`; runner: `run_life_v15.py`;
  driver: `driver_v15.py`
* Matrix: `results/matrix_v15/` (210 cells)
* Analysis: `analyze_v15.py`, `results/analyze_v15.txt`
* World oracle: `verify_env_v15.py`, `results/oracle_v15.txt`
* Independent verifier: `verify_v15_independent.py`,
  `results/verify_v15_independent.txt`
* Factcheck: `factcheck_v15.py`, `results/factcheck_v15.txt`
* Frozen and untouched: the entire v10–v14 line.