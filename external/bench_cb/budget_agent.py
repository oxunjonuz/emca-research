"""budget_agent.py -- turn 129. The COST-AWARE TRADE-OFF TAKEN BY ITSELF.

DECLARED ADAPTATION, not published code: the authors of arXiv:2012.07058
(budgeted causal bandits) do not publish an implementation, and their setting
(interventions strictly costlier than observations, unknown threshold learned
online) is not identical to ours. This arm implements THEIR STATED PRINCIPLE on
our instance, in the simplest honest way, so that "the union beats the parts"
can be tested against the cost-aware part ALONE:

  * the agent has a partially-known structure: it uses the SAME context-aware
    discovery candidate list the union uses (so the two arms differ ONLY in the
    exploration term and the balanced estimate), and
  * it spends a fixed budget on interventions, choosing which arm to intervene
    on by an explicit observe-vs-intervene price: it intervenes on the arm whose
    optimistic value of information exceeds the currently observed best payoff.

It is labelled `budget_pub` everywhere and is never called a published baseline.
Its purpose is the ablation the owner asked for: does adding the exploration
term to the cost-aware trade-off produce MORE than the trade-off alone?
"""
from collections import defaultdict

PROBE_BLOCK = 20
EFFECT = "y"


class BudgetAgent(object):
    def __init__(self, seed=0, budget_frac=0.5):
        self.seed = seed
        self.budget_frac = budget_frac
        self.tab = defaultdict(lambda: defaultdict(lambda: [0, 0]))
        self.n_pulls = 0
        self.n_interventions = 0
        self.chosen = None

    def _emp(self, lab):
        h, n = self.tab[lab][EFFECT]
        return (h / float(n)) if n else None

    def _best(self, acts):
        best, bestlab = None, acts[0]
        for lab in acts:
            m = self._emp(lab)
            if m is not None and (best is None or m > best):
                best, bestlab = m, lab
        return bestlab

    def run(self, T, model):
        K = model.K
        acts = ["a%d" % i for i in range(K - 1)]
        obs_arm = K - 1
        half = T // 2
        N = model.N
        # observational half (the cost-aware literature's cheap observations)
        for _ in range(half):
            x, y, z = model.sample(obs_arm)
            ctx = model.context_of(z)
            for i, xi in enumerate(x):
                lab = ("a%d" % (N + i)) if xi == 1 else ("a%d" % i)
                c = self.tab[lab][EFFECT]
                c[1] += 1
                c[0] += int(y)
        # active half: intervene only where the value of information beats the
        # currently observed payoff, up to a budget
        t = half
        budget = int(self.budget_frac * (T - half) / PROBE_BLOCK)
        used = 0
        while t < T:
            best_pay = self._emp(self._best(acts)) or 0.5
            # cheapest candidate by evidence, only if optimistic gap > best_pay
            thin = sorted(acts, key=lambda l: self.tab[l][EFFECT][1])
            target = None
            for lab in thin:
                if self.tab[lab][EFFECT][1] < 40 and (1.0 - best_pay) > best_pay:
                    target = lab
                    break
            if target is not None and used < budget:
                n = min(PROBE_BLOCK, T - t)
                for _ in range(n):
                    x, y, z = model.sample(int(target[1:]))
                    c = self.tab[target][EFFECT]
                    c[1] += 1
                    c[0] += int(y)
                used += 1
                self.n_interventions += 1
                t += n
            else:
                lab = self._best(acts)
                for _ in range(1):
                    x, y, z = model.sample(int(lab[1:]))
                    c = self.tab[lab][EFFECT]
                    c[1] += 1
                    c[0] += int(y)
                t += 1
        self.chosen = self._best(acts)
        self.policy = {model.context_of(c): self.chosen for c in range(2)} \
            if hasattr(model, "ctx_opt_arm") else {"flat": self.chosen}
        self.regret = float(model.policy_regret(self.policy))
        ci = int(self.chosen[1:])
        self.chosen_is_optimal = int(ci == model.optimal_arm)
        return self.regret

    def diagnostics(self):
        return {"n_interventions": self.n_interventions, "chosen": self.chosen,
                "chosen_is_optimal": self.chosen_is_optimal,
                "regret": round(self.regret, 6)}
