"""cb_grey.py -- turn 128 SUPPLEMENTARY probe (MY instance, NOT published).

Why this exists. On the published instance the mechanism never reaches its own
arbiter: the generator's bar is MIN_N=40 trials, and the optimal arm has ZERO
natural occurrences, so no candidate is ever generated (measured: silent in
98.5-99.7% of runs). Reporting "C1 is refuted in causal bandits" from that would
be an over-claim -- C1 was not exercised at all. This instance makes C1+C2
exercisable, which is the only honest way to ask whether they help.

Structure (tariff):
  Y depends on TWO causes, with eps1 > eps2 > 0:
     X_1 : P(X_1=1) = q1 -- the STRONG cause; at q1=0 it never occurs
                            naturally, so its intervention arm has no data
     X_2 : P(X_2=1) = 0.5 -- the WEAK cause, always observable
  P(Y=1|X_1,X_2) = 0.5 + eps1*X_1 + eps2*X_2  (clipped to [0,1])
  Actions: do(X_i=0), do(X_i=1) for i=1,2, plus do()  -> K = 5.

So there IS a real, table-visible edge (X_2 -> Y) for the generator to find,
and the generator's own contrast rule should nominate do(X_2=1). Whether the
agent then acts on it, and whether that buys regret, is exactly claim C1+C2 in
a bandit -- measured, not asserted.

This instance is MINE, not from the paper; every number from it is labelled
"supplementary" in the report and is never compared to a published figure.
"""
import sys, os
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))

import models as M


class TwoParentParallel(object):
    """Minimal two-parent parallel instance, same sampling convention as the
    authors' models.Parallel: sample(x) returns (x, y) with x the parent values
    actually set (the intervention sets one coordinate, the rest are drawn)."""

    def __init__(self, q1=0.0, eps1=0.3, eps2=0.15):
        self.N = 2
        self.K = 2 * self.N + 1           # do(X1=0),do(X2=0),do(X1=1),do(X2=1),do()
        self.q = np.array([q1, 0.5], dtype=float)
        self.eps1, self.eps2 = eps1, eps2
        # action index convention: i in 0..N-1 = do(X_i=0); N+i = do(X_i=1)
        exp = np.zeros(self.K)
        for i in range(self.N):
            for val in (0, 1):
                xs = []
                for _ in range(2):
                    xs.append([val, val])
                # integrate over the other coordinate
                tot = 0.0
                for other in (0, 1):
                    p = (self.q[1] if other else 1 - self.q[1]) if i == 0 \
                        else (self.q[0] if other else 1 - self.q[0])
                    x = [0, 0]
                    x[i] = val
                    x[1 - i] = other
                    tot += p * self._py(x)
                exp[i if val == 0 else self.N + i] = tot
        exp[self.K - 1] = 0.5 + self.eps1 * self.q[0] + self.eps2 * self.q[1]
        self.expected_rewards = exp
        self.expected_Y = exp
        self.optimal = exp.max()
        self.m = 1

    def _py(self, x):
        return min(1.0, max(0.0, 0.5 + self.eps1 * x[0] + self.eps2 * x[1]))

    def sample(self, a):
        x = (np.random.random(2) < self.q).astype(int)
        if a != self.K - 1:
            i, j = a % self.N, a // self.N
            x[i] = j
        y = 1 if np.random.random() < self._py(x) else 0
        return x, y


def make_grey(q1=0.0, eps1=0.3, eps2=0.15):
    return TwoParentParallel(q1, eps1, eps2)


if __name__ == "__main__":
    m = make_grey()
    print("K", m.K, "expected rewards", np.round(m.expected_rewards, 4),
          "optimal", round(m.optimal, 4))
