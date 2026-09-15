"""cb_c1_isolate.py -- turn 128: isolate C1 (the arbiter) from C2 (the generator).

The main grid cannot say WHICH half failed, because in the published instance the
generator is silent (no candidate is ever produced) and therefore the arbiter is
never exercised: "the mechanism is bad here" and "the arbiter never ran" look
identical from the outside. That would be an over-claim.

This script separates them by giving the arbiter exactly one thing -- a correct
hypothesis (the truly optimal arm, injected into the candidate list with the
generator's own score scale), i.e. the same oracle-injection control V7 used
(`INJECT_EDGE`). Then only C1 is measured:

  inject_none    -- the frozen mechanism (no injection)
  inject_true    -- the same mechanism with the true edge prepended to the list
  inject_forced  -- the same, with the arbiter's bar removed (beta effectively
                    infinite): does the DECISION RULE, not the bar, follow the
                    injected hypothesis?

If inject_true still probes ~never while inject_forced probes, then C1's failure
is entirely in its threshold, and the threshold is the thing that has no
exploration term. If inject_true probes the true arm, C1 works and C2 is the
only failure. Measured, not asserted.
"""
import sys, os
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

import candidate_gen as CG
import arbitration as AR
from cb_agent import CBAgent, arm_labels, arm_index, EFFECT, PROBE_BLOCK


class C1Iso(CBAgent):
    def __init__(self, mode, seed=0, target=None):
        CBAgent.__init__(self, kind="pure", seed=seed)
        self.mode = mode
        self.target = target          # label of the injected hypothesis

    def run(self, T, model):
        K, N = model.K, model.N
        acts = arm_labels(K)
        half = T // 2
        for _ in range(half):
            self._observe(model, K - 1)
        t = half
        while t < T:
            cands = CG.generate_flat(self._flat_table(), acts, min_n=self.min_n)
            self.n_gen_calls += 1
            if self.mode in ("inject_true", "inject_forced"):
                # the generator's own Candidate scale: a full-margin contrast
                cands = [CG.Candidate(self.target, EFFECT, "injected",
                                      1.0, 0.0, 999, 0.5)] + \
                        [c for c in cands if c.action != self.target]
            self.n_cands_total += len(cands)
            if not cands:
                self.n_empty_gen += 1
            if self.mode == "inject_forced":
                beta = 1e6
            else:
                beta = 1.0
            plan = AR.plan(cands, self._rich_rate(acts), beta=beta)
            if plan.probe_order:
                lab = plan.probe_order[0].action
                self.probes.append(lab)
                n = min(PROBE_BLOCK, T - t)
                for _ in range(n):
                    self._pull(model, lab)
                t += n
            else:
                self._pull(model, self._best_empirical(acts))
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
