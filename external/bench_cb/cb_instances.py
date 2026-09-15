"""cb_instances.py -- turn 128: the second measurement axis.

The published Figure-2a instance sets q_i = 0 for the first m variables, so the
optimal arm do(X_1=1) has ZERO natural occurrences: no observational pull can
ever fill a trial for it. The first grid showed the mechanism scoring the
worst-case regret 0.300 everywhere there.

This module builds a one-parameter family that keeps the paper's reward
structure EXACTLY (`Parallel.set_epsilon`: eps_minus = eps*q1/(1-q1), so the
expected reward of the best arm is always 0.5+eps and of the second-best
0.5-eps_minus) and varies only `q1 = P(X_1=1)`, the natural occurrence rate of
the optimal arm's intervention.

  q1 = 0    -- the paper's own instance: the best arm is structurally invisible
  q1 > 0    -- the best arm occurs naturally with probability q1, so the
               observational half DOES fill trials for it

The question this answers: at which natural-occurrence rate, if any, does the
campaign's mechanism start to find the optimum -- and at that rate, what do
plain greedy and the published arms do? If the mechanism only works where a
greedy estimator already works, the mechanism has no operating region of its own.
"""
import sys, os
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)

import models as M


def make_instance(q1, N=50, eps=0.3):
    """The paper's parallel instance with P(X_1=1) = q1 instead of 0.
    Every other variable keeps q = 0.5 (the paper's part_balanced_q)."""
    q = np.full(N, 0.5, dtype=float)
    q[0] = q1
    return M.Parallel(q, eps)


if __name__ == "__main__":
    for q1 in [0.0, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5]:
        m = make_instance(q1)
        print("q1=%.2f  E[r] best arm a%d = %.3f | a0 = %.3f | others = %.3f | m(q) = %d"
              % (q1, m.N, m.expected_rewards[m.N], m.expected_rewards[0],
                 m.expected_rewards[1], m.m))
