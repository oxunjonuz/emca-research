"""cb_agent.py -- turn 128: the campaign's ACTIVE half (C1 + C2) ported to the
published parallel causal bandit of Lattimore, Lattimore & Reid, arXiv:1606.03203.

IMPORTED UNCHANGED from the campaign's frozen files (hashes in
results_cb_meta.json; no edit of any kind):
  candidate_gen.generate_flat   -- claim C2, the world-agnostic generator
  candidate_gen.permute         -- the frozen C1 control
  arbitration.plan              -- claim C1, the frozen verify-or-exploit rule

NEW HERE (declared in PREREG_CB.md as adaptations A1'..A5):
  A1' observational half: T/2 pulls of do(), crediting each observed X_i to the
      arm that would have SET it. Sound in a parallel graph and exactly what the
      authors' own ParallelCausal does (`xij = hstack((1-x, x, 1))`).
  A2  the same T/2 observational split the published Algorithm 1 uses.
  A3  probe block = PROBE_BLOCK (20) pulls of the nominated arm.
  A4  re-generation every block, not every step.
  A5  `boot*` arms only: PILOT forced pulls of every never-tried arm at the
      start of the active half. Declared adaptation; measures whether the
      mechanism needs a bootstrap, not whether it is superior.

The agent reads only (x, y) from model.sample(a). It never touches
model.expected_rewards -- that array is the harness's scoring truth.

ACTION LAYOUT (the authors' own, models.py): 0..N-1 = do(X_i=0), N..2N-1 =
do(X_i=1), 2N = do(). Labels are the opaque strings "a<i>"; the observe arm is
never offered to the generator (it is not an intervention).

ARMS
  pure      the campaign mechanism exactly as frozen
  beta0     beta=0 -- the frozen control: may never probe
  perm      candidate scores permuted with the frozen seed (computed vs scheduled)
  unc       DECLARED ADAPTATION: pure + UCB1 fallback when the arbiter declines
  ucb       published-style UCB1 alone (Auer et al. 2002): the exploration floor
  boot1/boot5  DECLARED ADAPTATION A5: pure + PILOT forced pulls of untried arms
  pure_minn{N} SENSITIVITY only: mechanism with the generator's MIN_N lowered
"""
import sys, os
from collections import defaultdict
from math import log, sqrt

_HERE = os.path.dirname(os.path.abspath(__file__))
_CAMPAIGN = os.path.dirname(_HERE)
if _CAMPAIGN not in sys.path:
    sys.path.insert(0, _CAMPAIGN)

import candidate_gen as CG
import arbitration as AR

PROBE_BLOCK = 20
PILOT = {"boot1": 1, "boot5": 5}
EFFECT = "y1"


def arm_labels(K):
    return ["a%d" % i for i in range(K - 1)]


def arm_index(label):
    return int(label[1:])


class CBAgent(object):
    def __init__(self, kind="pure", seed=0, min_n=None, beta=None):
        self.kind = kind
        self.seed = seed
        self.min_n = CG.MIN_N if min_n is None else min_n
        self.beta = 1.0 if beta is None else beta
        self.tab = defaultdict(lambda: defaultdict(lambda: [0, 0]))
        self.n_gen_calls = 0
        self.n_cands_total = 0
        self.n_empty_gen = 0
        self.probes = []
        self.tried = set()
        self.pilot_pulls = 0
        self.active_pulls = 0

    # ---- the agent's own accounting ---------------------------------
    def _record(self, label, y):
        cell = self.tab[label][EFFECT]
        cell[1] += 1
        cell[0] += int(y)
        self.tried.add(label)

    def _pull(self, model, label):
        _, y = model.sample(arm_index(label))
        self._record(label, y)
        self.active_pulls += 1

    def _flat_table(self):
        return {lab: {EFFECT: list(v[EFFECT])}
                for lab, v in self.tab.items() if v[EFFECT][1] > 0}

    def _emp(self, lab):
        h, n = self.tab[lab][EFFECT]
        return (h / float(n)) if n else None

    def _rich_rate(self, acts):
        """What the alternative pays as the agent has SEEN it: best empirical
        mean among arms with at least MIN_N trials. The agent's own reward
        stream; the world's parameters are never read."""
        best = None
        for lab in acts:
            h, n = self.tab[lab][EFFECT]
            if n >= self.min_n:
                m = h / float(n)
                if best is None or m > best:
                    best = m
        return 0.5 if best is None else best

    def _best_empirical(self, acts):
        best, bestlab = None, acts[0]
        for lab in acts:
            m = self._emp(lab)
            if m is None:
                continue
            if best is None or m > best:
                best, bestlab = m, lab
        return bestlab

    def _ucb_pick(self, acts, t):
        """UCB1 (Auer et al. 2002)."""
        for lab in acts:
            if self.tab[lab][EFFECT][1] == 0:
                return lab
        best, bestlab = None, acts[0]
        for lab in acts:
            h, n = self.tab[lab][EFFECT]
            b = h / float(n) + sqrt(2.0 * log(max(t, 2)) / n)
            if best is None or b > best:
                best, bestlab = b, lab
        return bestlab

    # ---- observational half -----------------------------------------
    def _observe(self, model, obs_arm):
        N = model.N
        x, y = model.sample(obs_arm)
        for i, xi in enumerate(x):
            if xi == 1:
                self._record("a%d" % (N + i), y)   # do(X_i=1)
            else:
                self._record("a%d" % i, y)         # do(X_i=0)

    # ---- the run ----------------------------------------------------
    def run(self, T, model):
        K = model.K
        obs_arm = K - 1
        acts = arm_labels(K)
        half = T // 2

        for _ in range(half):
            self._observe(model, obs_arm)

        t = half
        # A5: optional pilot (declared). Round-robin, then proceed normally.
        if self.kind in PILOT:
            n = PILOT[self.kind]
            for _ in range(n):
                for lab in acts:
                    if t >= T:
                        break
                    self._pull(model, lab)
                    self.pilot_pulls += 1
                    t += 1

        while t < T:
            if self.kind == "ucb":
                lab = self._ucb_pick(acts, t)
                self._pull(model, lab)
                t += 1
                continue
            table = self._flat_table()
            cands = CG.generate_flat(table, acts, min_n=self.min_n)
            self.n_gen_calls += 1
            if self.kind == "perm":
                cands = CG.permute(cands, self.seed)
            self.n_cands_total += len(cands)
            if not cands:
                self.n_empty_gen += 1
            plan = AR.plan(cands, self._rich_rate(acts), beta=self.beta)
            if plan.probe_order:
                lab = plan.probe_order[0].action
                self.probes.append(lab)
                n = min(PROBE_BLOCK, T - t)
                for _ in range(n):
                    self._pull(model, lab)
                t += n
            else:
                lab = self._ucb_pick(acts, t) if self.kind == "unc" \
                    else self._best_empirical(acts)
                self._pull(model, lab)
                t += 1

        chosen = self._best_empirical(acts)
        self.chosen = chosen
        ci = arm_index(chosen)
        self.regret = max(model.expected_rewards) - model.expected_rewards[ci]
        self.optimal_arm = int(max(range(K),
                                   key=lambda a: model.expected_rewards[a]))
        self.chosen_is_optimal = int(ci == self.optimal_arm)
        self.found_optimal = int(self.optimal_arm in
                                 [arm_index(l) for l in self.tried])
        self.opt_trials = self.tab["a%d" % self.optimal_arm][EFFECT][1]
        return self.regret

    def diagnostics(self):
        return {"n_empty_gen": self.n_empty_gen,
                "n_gen_calls": self.n_gen_calls,
                "n_cands_total": self.n_cands_total,
                "probes": list(self.probes),
                "n_probes": len(self.probes),
                "pilot_pulls": self.pilot_pulls,
                "active_pulls": self.active_pulls,
                "chosen": self.chosen,
                "chosen_is_optimal": self.chosen_is_optimal,
                "found_optimal": self.found_optimal,
                "opt_trials": self.opt_trials,
                "regret": round(self.regret, 6)}
