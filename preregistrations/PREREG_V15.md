# PREREG V15 — the SEAM architecture (reward-free, non-RL, non-LLM)

Written BEFORE the first cell of the v15 matrix. Owner directive:
msg_00147 / msg_00148 (verbatim in §0). The task is NOT another
RL-shaped frame with the reward deleted; it is a combination of 2–3
existing non-LLM, non-RL paradigms whose blind spots complement each
other, tested against the core question: **can an agent act without a
preference over world states, or does "truth" inevitably hide a goal?**

## §0 The owner's constraint, verbatim

> v15 одобряю с уточнением. Не строй ещё одну RL-подобную рамку с
> убранной наградой — это будет не новая архитектура, а старая с одной
> вычеркнутой деталью. Задача: изучи существующие альтернативные
> (не-LLM, не-RL) парадигмы — JEPA и то, что рядом с ней (world models,
> predictive coding, free energy principle, active inference …), и любые
> другие, которые сам найдёшь. Не бери ни одну из них целиком. Найди то,
> чего нет ни в одной по отдельности, и собери из двух-трёх такое
> сочетание, которое само по себе является новым … Не заявляй, что
> построил что-то принципиально новое, пока не проверишь и не назовёшь
> явно, какая часть архитектуры унаследована от какой существующей идеи,
> а какая — действительно на стыке.

## §1 What is inherited, line by line (the honesty requirement)

| component | inherited from | what that source CANNOT do (its blind spot) |
|---|---|---|
| predict the **representation** of the next observation, never reconstruct it | JEPA / I-JEPA (src_c71f7fa65f68) | no agent, no action selection, no memory across episodes, no context index |
| choose actions by **expected information gain**, with the prior-preference term REMOVED | active inference / free-energy principle (src_973284d453d0, src_…2212.01354) | keeps prior preferences (a goal) and needs an explicit generative model; scales poorly |
| compute the contrast **within a context**, not pooled | the campaign's own v3–v9 line (0/51 vs 48/51, `EPISTEMIC_VERDICT.md` §4.1) | was built for a reward-bearing world; never tested without a goal |
| **AT THE SEAM (new)** | — | a context-indexed, representation-space, epistemic-only agent with **no reward, no energy, no death and no prior preferences**, whose OWN drive is measured for fakeability on its own evidence channel |

**The seam claim, stated so it can fail:** no one of the three sources
has (a) no goal AND (b) a context index AND (c) a fakeability test of
its own drive. v15 is exactly that intersection. If the intersection
turns out to behave like one of its parents, that is the honest result
and it will be reported as such.

## §2 The world (reward-free by construction)

`env_v15.py`. There is NO reward, NO energy, NO death, NO preferred
state. Observation is exactly `{phase, feat, val}`. Each action reveals
one binary feature:

| action | feature | rate |
|---|---|---|
| a0 | f0 | **0.9 in phase A, 0.1 in phase B** — the TRUE context-indexed structure |
| a1 | f1 | 0.5 always — pure noise |
| a2 | fnoise | 0.5 always — pure noise (second noise channel) |
| a3 | fconst / fdecoy / ftv | regime-dependent (below) |

Phase alternates A/B every `CTX_SPAN=400` steps. **The pooled trap is
the structural fact the seam rests on:** pooled over contexts,
P(val|a0)=0.5 — identical to noise. Only a context-indexed model can
learn it. Oracle-verified (O14/O15).

Three regimes:
* **base** — a3 is `fconst`, rate 0.0 (the PARKING channel: zero error,
  zero information).
* **decoy** — a3 is `fdecoy`, a NON-STATIONARY channel (0.9 for
  `DECOY_RESET` steps, then 0.1, alternating): learnable forever,
  relevant never.
* **tv** — a3 is `ftv`, the NOISY TV: the rate flips EVERY step, so the
  channel is never predictable and its expected information gain never
  decays. This is the fakeable channel for an epistemic drive.

## §3 The agent (`agent_v15.py`) and its declared criterion

A Dirichlet/Beta–Bernoulli model per `(context, action)`, discounted by
`discount`. Action score = expected information gain (nats) of one more
draw about that channel's rate. Arms:

* `rand` — uniform.
* `naive_info` — score = outcome entropy H(p̂) (the "predictive coding"
  style drive: seek high-entropy outcomes). **Predicted to be captured
  by the noisy TV.**
* `confirm` — score = −min(p̂,1−p̂) (seek confirmation). Control.
* `ig_pooled` — IG, but with NO context index (pooled). **Predicted to
  fail to learn the true structure.**
* `ig_ctx` — IG with the context index (the seam agent).
* `ig_relevant` — IG **plus a relevance criterion**: a channel scores 0
  unless its learned rate differs across contexts by > 0.20. This arm
  exists to measure what restoring a preference costs.
* `ig_ctx_oracle` — model pre-seeded with the true rates; the metric's
  ceiling. Analysis device only, never in a fairness verdict.

**The one non-epistemic parameter, declared as such:** `ig_eps=0.01`, the
threshold below which `ig_ctx` declares "nothing left to learn" and acts
at random. That threshold is a criterion — the prereg names it rather
than hiding it.

## §4 Preregistered hypotheses and gates

* **H1 (learning).** `ig_ctx` learns the true structure: mean
  `model_err = |p̂_A(a0)−0.9| + |p̂_B(a0)−0.1|` < 0.08 over 10 seeds.
* **H2 (the seam).** With pure IG and no preference, the agent's action
  distribution is **indistinguishable from random** (a0_share within
  0.02 of 0.25 in 10/10 seeds) — i.e. after learning, IG gives it no
  reason to prefer the true channel. **This is the core prediction.**
* **H3 (the criterion).** `ig_relevant` a0_share > 0.95 in 10/10 seeds —
  restoring a relevance criterion restores the preference.
* **H4 (pooled trap).** `ig_pooled` model_err > 0.5 (it cannot learn a
  structure that is invisible pooled).
* **H5 (the fakeable drive).** `naive_info` a3_share > 0.20 in the `tv`
  regime and < 0.05 in `base` — the high-entropy drive is captured by
  the never-resolving channel, and only by it.
* **H6 (control).** `rand` a0_share within 0.02 of 0.25.
* **H7 (the honest collapse, if it happens).** If H2 holds and H3 holds,
  then the agent acts only when a criterion is present — and the
  criterion is a preference over states. That is the seam's answer.

## §5 Verification plan (before any run)

* `verify_env_v15.py` — world oracle, 21 checks incl. the pooled trap and
  a live negative control.
* `verify_v15_independent.py` — fresh process, disk only, imports neither
  env/agent/runner; recomputes every metric from the trace; live NV.
* `factcheck_v15.py` — every number in `RESULTS_V15.md` checked against
  the cells.
* Determinism: a cell re-run in a fresh process must be byte-identical.

## §6 What is deliberately NOT built

No second agent, no forger, no reward channel, no auditor. The owner's
constraint is a new architecture, not another patch on v10–v14. The
v10–v14 line is frozen and untouched.