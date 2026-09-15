"""union_instance.py -- turn 129. MASK-CB: a CONTEXT-SPECIFIC causal bandit.

WHY THIS INSTANCE (PREREG_UNION.md §1-2): the published parallel instance has a
single parent whose pooled effect is exactly what pooling sees, so
context-specificity has nothing to do there. The six campaign worlds proved, and
turns 127/128 could not exercise, the opposite regime: an effect that lives in
ONE context. This instance is that regime, built on the published model
interface (ext/latt_py3/models.py) with the authors' own action layout.

REWARD (declared; NEVER given to any agent):

  z ~ Bernoulli(0.5)                              -- context, revealed per pull
  x ~ Bernoulli(q), q[0]=0, q[1..]=0.5             -- A=x[0] true cause, others
                                                     natural 0.5 fillers
  P(X_2=1 | z=0)=seg, P(X_2=1 | z=1)=1-seg         -- the DECOY's observational
                                                     trials concentrate in ctx0
  P(Y=1 | x, z) = 0.5
        + eps        if x[0]=1 and z=0            -- true cause pays HERE
        - eps        if x[0]=1 and z=1            -- ... and reverses HERE
        + decoy      if x[1]=1 and z=0            -- decoy pays mildly in ctx0
        - decoy*0.6  if x[1]=1 and z=1            -- ... and mildly-negative
  (clipped to [0,1])

Consequences, with eps=0.35, decoy=0.25, seg=0.95:
  pooled:  E[Y|do(A=1)] = 0.5  ==  E[Y|do(A=0)]               -> POOLING IS BLIND
  ctx0:    do(A=1) = 0.85  (best)   do(A=0) = 0.15
  ctx1:    do(A=0) = 0.85  (best)   do(A=1) = 0.15
  decoy:   pooled 0.5, but its OBSERVATIONAL pooled mean is biased high (~0.70)
           because ~95% of its occurrences land in ctx0 where it pays 0.75;
           its empirical context-balanced mean (0.5) is far below the true arm's
           context-optimal 0.85.

OBJECTIVE (declared, and the honest formalisation of the owner's words "the true
cause has a context-specific, not pooled, effect, and must still be discovered"):

  the agent outputs a POLICY: one arm per context it has seen. Regret is the
  context-conditional gap,

      R = mean_z ( max_a E[Y | do(a), z]  -  E[Y | do(chosen_z), z] ).

  A context-optimal policy scores 0; any pooled policy that must pick ONE arm for
  both contexts scores >= eps (=0.35), because the true cause helps in exactly
  one context and hurts in the other. The pooled view of the true cause is flat,
  so no amount of pooled sampling reveals the policy.

This is the campaign's own context-exclusive edge, transplanted to a causal
bandit, and the exact object the union's context split exists to find.
"""
import numpy as np
from numpy.random import binomial


class MaskedParallel(object):
    def __init__(self, N=50, m=1, eps=0.35, decoy=0.15, decoy_rev=0.6,
                 pZ=0.5, seg=0.95, base=0.5):
        self.N = N
        self.K = 2 * N + 1                       # the authors' own layout
        self.m = m
        self.eps = float(eps)
        self.decoy = float(decoy)
        self.decoy_rev = float(decoy_rev)
        self.pZ = float(pZ)
        self.seg = float(seg)
        self.base = float(base)
        self.q = np.full(N, 0.5)
        self.q[0:m] = 0.0
        self.contexts = ["c0", "c1"]
        self._expected()

    # ---- expected values, per context and pooled --------------------
    def _er_ctx(self, c):
        """E[Y | do(a), z=c] for every action. An intervention sets ONLY its
        target variable; every other variable keeps its NATURAL distribution in
        context c. (The earlier version forced all non-targets to 0 -- a real
        bug caught by verify_union_independent.py's Monte-Carlo check, because
        do(A=0) leaves the decoy free and the decoy co-occurs.)"""
        p = self._pX_given_c(c)
        er = np.zeros(self.K)
        for a in range(self.K):
            forced = None if a == self.K - 1 else (a % self.N, a // self.N)
            tot = 0.0
            for x0 in (0, 1):
                for x1 in (0, 1):
                    if forced is not None and forced[0] == 0:
                        pr0 = 1.0 if x0 == forced[1] else 0.0
                    else:
                        pr0 = p[0] if x0 == 1 else (1.0 - p[0])
                    if forced is not None and forced[0] == 1:
                        pr1 = 1.0 if x1 == forced[1] else 0.0
                    else:
                        pr1 = p[1] if x1 == 1 else (1.0 - p[1])
                    pr = pr0 * pr1
                    if pr == 0.0:
                        continue
                    x = [0] * self.N
                    x[0], x[1] = x0, x1
                    tot += pr * self.pYgivenX(x, c)
            er[a] = tot
        return er

    def _expected(self):
        self.er_ctx = {c: self._er_ctx(c) for c in (0, 1)}
        pooled = (1 - self.pZ) * self.er_ctx[0] + self.pZ * self.er_ctx[1]
        self.expected_rewards = pooled                     # for pooled agents
        self.optimal = float(pooled.max())
        self.optimal_arm = int(np.argmax(pooled))
        # context-conditional optimum: the value a per-context policy can reach
        self.ctx_opt_arm = {c: int(np.argmax(self.er_ctx[c])) for c in (0, 1)}
        self.ctx_opt_val = {c: float(self.er_ctx[c].max()) for c in (0, 1)}
        self.opt_ctx_val = float(np.mean([self.ctx_opt_val[c] for c in (0, 1)]))

    # ---- sampling ---------------------------------------------------
    def _pX_given_c(self, c):
        p = np.array(self.q, dtype=float)
        p[1] = self.seg if c == 0 else (1.0 - self.seg)
        return p

    def pYgivenX(self, x, z):
        v = self.base
        if x[0] == 1:
            v += self.eps if z == 0 else -self.eps
        if x[1] == 1:
            v += self.decoy if z == 0 else -self.decoy * self.decoy_rev
        return min(max(v, 0.0), 1.0)

    def sample(self, action):
        """Returns (x, y, z). z is the context, revealed on every pull."""
        z = int(binomial(1, self.pZ))
        x = binomial(1, self._pX_given_c(z))
        if action != self.K - 1:                 # everything except do()
            i, j = action % self.N, action // self.N
            x[i] = j
        y = binomial(1, self.pYgivenX(x, z))
        return x, y, z

    def context_of(self, z):
        return "c%d" % z

    # ---- policy scoring (the objective) -----------------------------
    def policy_regret(self, policy):
        """policy: {context_key: arm_label}. Regret = mean over contexts seen of
        (best-in-context value - chosen arm's value in that context)."""
        vals = []
        for c in (0, 1):
            key = self.context_of(c)
            lab = policy.get(key)
            if lab is None:
                vals.append(self.ctx_opt_val[c])     # never decided: full loss
                continue
            a = int(lab[1:]) if isinstance(lab, str) else int(lab)
            vals.append(self.ctx_opt_val[c] - float(self.er_ctx[c][a]))
        return float(np.mean(vals))


class PublishedParallel(object):
    """Points the union agent at the AUTHORS' own published model. No context is
    present there, so the policy has one entry and the objective degenerates to
    the authors' own simple regret."""

    def __init__(self, model):
        self._m = model
        self.N = model.N
        self.K = model.K
        self.expected_rewards = np.array(model.expected_rewards, dtype=float)
        self.optimal = float(self.expected_rewards.max())
        self.optimal_arm = int(np.argmax(self.expected_rewards))
        self.m = getattr(model, "m", None)
        self.contexts = ["flat"]
        self.ctx_opt_val = {"flat": self.optimal}
        self.er_ctx = {}

    def sample(self, action):
        x, y = self._m.sample(action)
        return x, y, 0

    def context_of(self, z):
        return "flat"

    def policy_regret(self, policy):
        lab = policy.get("flat")
        if lab is None:
            return self.optimal
        a = int(lab[1:]) if isinstance(lab, str) else int(lab)
        return float(self.optimal) - float(self.expected_rewards[a])
