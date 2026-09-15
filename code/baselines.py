"""Baselines: random, tabular Q-learning (eps-greedy), n-gram action predictor.

All baselines get the SAME observation stream and reward signal as EMCA.
They are deliberately strong for this small world (tabular = full capacity).
"""
import random
from collections import defaultdict

from env_terrarium import ACTIONS
from agent_emca import view_features


class RandomAgent:
    def __init__(self, seed=0, **kw):
        self.rng = random.Random(seed)
        self.t = 0

    def act(self, o):
        return self.rng.choice(ACTIONS)

    def observe(self, o, a, r, o2, done, info):
        self.t += 1


class QAgent:
    """Tabular Q-learning over symbolic feature state x action."""

    def __init__(self, seed=0, alpha=0.2, gamma=0.95, eps=0.15, **kw):
        self.rng = random.Random(seed)
        self.alpha, self.gamma, self.eps = alpha, gamma, eps
        self.Q = defaultdict(lambda: defaultdict(float))
        self.last = None
        self.t = 0

    def _s(self, o):
        f = view_features(o)
        return (f["berry_near"] > 0, f["door_near"] > 0, f["lever_near"] > 0,
                f["treasure_near"] > 0, f["energy_low"], f["energy_mid"])

    def act(self, o):
        s = self._s(o)
        if self.rng.random() < self.eps:
            return self.rng.choice(ACTIONS)
        q = self.Q[s]
        best = max(ACTIONS, key=lambda a: q[a])
        return best

    def observe(self, o, a, r, o2, done, info):
        s, s2 = self._s(o), self._s(o2)
        q = self.Q[s]
        next_best = max((self.Q[s2][a2] for a2 in ACTIONS), default=0.0)
        target = r + (0.0 if done else self.gamma * next_best)
        q[a] += self.alpha * (target - q[a])
        self.t += 1


class NGramAgent:
    """Context-limited predictor: picks action that historically followed this
    feature context with highest reward (1-step lookahead, no planning chain)."""

    def __init__(self, seed=0, **kw):
        self.rng = random.Random(seed)
        self.stats = defaultdict(lambda: defaultdict(lambda: [0.0, 0]))  # ctx->a->[r,n]
        self.t = 0

    def _s(self, o):
        f = view_features(o)
        return (f["berry_near"] > 0, f["door_near"] > 0, f["lever_near"] > 0,
                f["energy_mid"], f["energy_low"])

    def act(self, o):
        s = self._s(o)
        if self.rng.random() < 0.15:
            return self.rng.choice(ACTIONS)
        cands = []
        for a, (rs, n) in self.stats[s].items():
            if n >= 2:
                cands.append((rs / n, a))
        if not cands:
            return self.rng.choice(ACTIONS)
        cands.sort(reverse=True)
        return cands[0][1]

    def observe(self, o, a, r, o2, done, info):
        s = self._s(o)
        self.stats[s][a][0] += r
        self.stats[s][a][1] += 1
        self.t += 1
