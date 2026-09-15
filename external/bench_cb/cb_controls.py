"""cb_controls.py -- turn 128: controls that bound what the ported mechanism can
possibly earn.

  greedy_half : after the observational half, spend every remaining pull on the
                best empirical arm and nothing else. This is the floor the
                mechanism must beat to have any value: it is what an agent that
                CANNOT generate a hypothesis does with the same data.
  rnd_probe   : observational half, then uniform-random arm for every remaining
                pull. Bounds what blind exploration earns here.
  know_probe  : observational half, then every remaining pull on the arm the
                generator would pick IF the optimal arm's table were non-empty
                (i.e. the mechanism handed the one thing it cannot get).
                Bounds what a perfect hypothesis-generation step would earn.
  obs_only    : the observational half alone, then a random arm (the published
                "Observational" idea in their own code).

These are controls, not arms of the campaign; they are labelled so everywhere.
"""
import sys, os
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)

import models as M                          # noqa: F401  (harness import path)
from cb_agent import CBAgent, arm_labels, arm_index, EFFECT


class CBFixed(CBAgent):
    """Reuses the campaign agent's observational half, then a fixed policy."""

    def __init__(self, policy, seed=0):
        CBAgent.__init__(self, kind="pure", seed=seed)
        self.policy = policy

    def run(self, T, model):
        K, N = model.K, model.N
        obs_arm = K - 1
        acts = arm_labels(K)
        half = T // 2
        for _ in range(half):
            self._observe(model, obs_arm)
        # the best arm the observational half can see (never the optimal one
        # in the m>0 published instance: it has zero trials there)
        best_obs = self._best_empirical(acts)
        t = half
        while t < T:
            if self.policy == "greedy_half":
                lab = best_obs
            elif self.policy == "rnd_probe":
                lab = acts[(t * 2654435761) % len(acts)]
            elif self.policy == "obs_only":
                lab = best_obs if t % 2 == 0 else acts[(t * 40503) % len(acts)]
            elif self.policy == "know_probe":
                lab = "a%d" % N          # do(X_1=1): the truly optimal arm
            else:
                raise ValueError(self.policy)
            self._pull(model, lab)
            t += 1
        chosen = self._best_empirical(acts)
        self.chosen = chosen
        ci = arm_index(chosen)
        self.regret = max(model.expected_rewards) - model.expected_rewards[ci]
        self.optimal_arm = int(max(range(K), key=lambda a: model.expected_rewards[a]))
        self.chosen_is_optimal = int(ci == self.optimal_arm)
        self.found_optimal = int(self.optimal_arm in [arm_index(l) for l in self.tried])
        self.opt_trials = self.tab["a%d" % self.optimal_arm][EFFECT][1]
        return self.regret
