"""Terrarium v15 -- the REWARD-FREE world for the SEAM architecture.

Owner directive (msg_00147 / msg_00148): do NOT build another RL-like
frame with the reward deleted. Build a combination of 2-3 non-LLM,
non-RL paradigms whose blind spots complement each other, and test the
core question -- can an agent act WITHOUT a preference over world
states, or does "truth" inevitably hide a goal?

This world has NO reward, NO energy, NO death, NO preferred state. The
agent observes one feature value per step (the feature is determined by
its action) plus the observable phase (context). Its ONLY drive is
epistemic. Nothing in the world is "good" or "bad".

DECLARED INHERITANCE (PREREG_V15.md names every line):
  * representation-space prediction -- from JEPA (I-JEPA,
    src_c71f7fa65f68): the agent predicts the REPRESENTATION of the next
    observation (the feature value), never reconstructs the world.
    JEPA has no agent, no action selection and no memory across
    episodes -- that is its blind spot.
  * epistemic action selection with NO prior preferences -- from active
    inference / the free-energy principle: the expected-free-energy
    epistemic term, with the prior-preference term REMOVED. Active
    inference keeps prior preferences (a goal) and needs an explicit
    generative model -- that is its blind spot.
  * contextual specificity -- from the campaign's own v3-v9 line: a
    contrast computed WITHIN a context is not the same as a pooled
    contrast (the campaign's central epistemic result, 0/51 vs 48/51).
    JEPA and active inference both lack an explicit context index.
  AT THE SEAM (new): a context-indexed, representation-space,
  epistemic-only agent -- no reward, no energy, no death, no prior
  preferences -- whose OWN drive is measured for fakeability on its own
  evidence channel. No one of the three sources has this.

THE WORLD:
  phase (context) switches every CTX_SPAN steps between "A" and "B".
  Each action REVEALS one feature; the agent observes {phase, feat, val}:
    a0 -> f0      the TRUE structure: P(val=1) = 0.9 in A, 0.1 in B.
                  Pooled over contexts it is 0.5 -- indistinguishable
                  from noise. Only a CONTEXT-INDEXED model can learn it.
    a1 -> f1      pure noise, P=0.5, action- and context-independent.
    a2 -> fnoise  pure noise, P=0.5 -- the NOISY-TV channel: maximal
                  outcome entropy forever, zero parameter information.
    a3 -> fconst  P(val=1)=0.0 always -- the PARKING channel: zero
                  prediction error, zero information.
  decoy=True replaces a3's channel with
    a3 -> fdecoy  NON-STATIONARY: P=0.9 for DECOY_RESET steps, then 0.1,
                  alternating. Learnable forever, relevant never -- the
                  channel that satisfies a Bayesian information drive
                  without ever touching the true structure.
"""
import random

CTX_SPAN = 400
DECOY_RESET = 50
ACTIONS = ("a0", "a1", "a2", "a3")
REVEAL = {"a0": "f0", "a1": "f1", "a2": "fnoise", "a3": "fpark"}
TRUE_RATE = {"A": 0.9, "B": 0.1}
NOISE_RATE = 0.5
CONST_RATE = 0.0
DECOY_RATES = (0.9, 0.1)


class WorldV15:
    def __init__(self, seed, decoy=False, ctx_span=CTX_SPAN,
                 decoy_reset=DECOY_RESET, tv=False):
        self.seed = int(seed)
        self.rng = random.Random(self.seed)
        self.t = 0
        self.decoy = bool(decoy)
        self.tv = bool(tv)
        self.ctx_span = int(ctx_span)
        self.decoy_reset = int(decoy_reset)

    @property
    def ctx(self):
        return "A" if (self.t // self.ctx_span) % 2 == 0 else "B"

    def feature(self, action):
        f = REVEAL[action]
        if f == "fpark":
            if self.tv:
                return "ftv"
            return "fdecoy" if self.decoy else "fconst"
        return f

    def rate(self, feat):
        if feat == "f0":
            return TRUE_RATE[self.ctx]
        if feat in ("f1", "fnoise"):
            return NOISE_RATE
        if feat == "fconst":
            return CONST_RATE
        if feat == "ftv":
            # the NOISY TV: the rate flips EVERY step, so the channel is
            # never predictable and its expected information gain never
            # decays. This is the fakeable channel for an epistemic drive.
            return 0.98 if (self.t % 2 == 0) else 0.02
        if feat == "fdecoy":
            return DECOY_RATES[(self.t // self.decoy_reset) % 2]
        raise KeyError(feat)

    def step(self, action):
        assert action in ACTIONS, action
        phase = self.ctx
        feat = self.feature(action)
        p = self.rate(feat)
        val = 1 if self.rng.random() < p else 0
        self.t += 1
        return {"phase": phase, "feat": feat, "val": val}