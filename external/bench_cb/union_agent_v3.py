# GENERATED FILE -- do not edit. Produced by make_agent_v3.py from
#   union_agent_v2.py   sha256 76bfe972bde4963cb7bc47bce3b0bbb11f712117b2c232f7c655f515eb43b8ec
# by four mechanical substitutions (import, __init__ signature,
# arbiter-call block, ARMS opening). `union_agent_v3.diff` is the
# exact patch; make_agent_v3.py refuses unless each substitution
# occurs exactly once, and verify_stopping_independent.py re-derives
# every other byte of this file from the frozen source.
# frozen producers and their hashes:
#   candidate_gen.py         fa9721ae816c3c42ecf73ca28ba3f188b78f51b345a381e092515f262c46ef49
#   arbitration.py           2d3d825bcfc83cc8533866510960572c42140db2f2f03c6a9945807b71e0914c
#   arbitration_scaled.py    fbdd446fa1841ca30a1e5332e717ab673c365a6c226f16575e87db0cf18f7fec
#   union_agent_v2.py        76bfe972bde4963cb7bc47bce3b0bbb11f712117b2c232f7c655f515eb43b8ec
#   union_instance.py        09a0e27e292bfbd60cc4e8ddef7da7ef029c2f0ca91cd8232b90319a5d22c0ff
"""union_agent.py -- turn 129. The UNION mechanism.

Owner's instruction (msg_00129): take the published exploration term and the
published cost-aware trade-off NOT as a solution to copy but as MATERIAL; build
the exploration term INTO C2 so that it does not lose what already works
(context-specificity); re-run on the same hard instance.

So the union is ONE candidate list with TWO sources feeding the FROZEN arbiter:

  source 1 -- CONTEXT CONTRAST (the campaign's own C2 machinery, restored):
      candidate_gen.generate over the agent's per-context tables. Nominates an
      arm whose rate stands out WITHIN a context -- the only way to see an
      effect that pooling averages away. score = measured context gap.

  source 2 -- EXPLORATION (the PRINCIPLE of Algorithm 2 of arXiv:1606.03203,
      not its code): every arm the agent has NOT yet resolved (insufficient
      evidence in some observed context) is ALSO a candidate, scored by
      OPTIMISM UNDER THIN EVIDENCE: with no data an arm may pay at most 1, so
      its optimistic gap is `1 - rich`. This is the ONLY thing that can reach an
      arm the pooled scan never observed -- turn 128's exact failure, where the
      generator's MIN_N=40 bar made the optimum unreachable forever.

  the FROZEN arbiter (arbitration.plan, imported UNCHANGED) prices BOTH sources
      with the same rule: probe iff beta*GAIN_UNIT*score > rich_rate*H +
      PROBE_COST. Cheap alternatives clear more candidates, expensive ones
      fewer, beta=0 clears none.

  the decision estimate is CONTEXT-BALANCED: an arm is scored by the equal-weight
      average of its per-context rates, not by its pooled sample. This is the
      only piece that refuses a decoy whose apparent edge is a context-merging
      artifact of where its trials landed.

ABLATIONS (identical code, ONE switch each, so a difference is attributable):
  use_ctx  : context contrast in discovery AND the balanced estimate
             (False -> pooled only: turn-128 behaviour)
  use_exp  : source 2, the exploration term
             (False -> greedy fallback when nothing is nominated)
  use_cost : the priced arbiter
             (False -> probe the top candidate unconditionally)

The agent reads only (x, y, z) from model.sample(); model.expected_rewards is
the harness's scoring truth and is never touched.
"""
import sys, os
from collections import defaultdict
from math import log, sqrt

_HERE = os.path.dirname(os.path.abspath(__file__))
_CAMPAIGN = os.path.dirname(_HERE)
if _CAMPAIGN not in sys.path:
    sys.path.insert(0, _CAMPAIGN)

import candidate_gen as CG
import arbitration_scaled as AR
import stopping_rules as SR      # turn 134: the new stopping rules

PROBE_BLOCK = 20        # the campaign's own declared constant (turn-128 A3)
MIN_PER_CTX = 10        # RESOLVED iff >= this many pulls in EVERY context seen;
                        # declared agent constant, sensitivity {5,10,20} reported
                        # (prereg amendment A1 -- the verdicts H1-H6 do not move
                        # with it; it only affects the union's own noise floor)
MIN_N_EST = 40          # the generator's own frozen bar, used for rich_rate
EFFECT = "y"


def arm_labels(K):
    return ["a%d" % i for i in range(K - 1)]   # the do() arm is never an action


def arm_index(label):
    return int(label[1:])


class UnionAgent(object):
    def __init__(self, kind="union", seed=0, min_n=None, beta=None,
                 use_ctx=True, use_exp=True, use_cost=True, exp_mode="ctx",
                 rule_name="frozen"):
        self.kind = kind
        self.rule_name = rule_name
        self.seed = seed
        self.min_n = CG.MIN_N if min_n is None else min_n
        self.beta = 1.0 if beta is None else beta
        self.use_ctx = use_ctx
        self.use_exp = use_exp
        self.use_cost = use_cost
        self.exp_mode = exp_mode
        self.ctx_table = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: [0, 0])))
        self.tab = defaultdict(lambda: defaultdict(lambda: [0, 0]))   # pooled
        self.contexts_seen = []
        self.n_gen_calls = 0
        self.n_empty_gen = 0
        self.n_probes = 0
        self.n_explore_picks = 0
        self.tried = set()
        self.active_pulls = 0

    # ---- accounting -------------------------------------------------
    def _record(self, lab, y, ctx):
        self.tab[lab][EFFECT][1] += 1
        self.tab[lab][EFFECT][0] += int(y)
        c = self.ctx_table[ctx][lab][EFFECT]
        c[1] += 1
        c[0] += int(y)
        if ctx not in self.contexts_seen:
            self.contexts_seen.append(ctx)
        self.tried.add(lab)

    def _pull(self, model, lab):
        x, y, z = model.sample(arm_index(lab))
        self._record(lab, y, model.context_of(z))
        self.active_pulls += 1

    # ---- views ------------------------------------------------------
    def _flat_table(self):
        return {lab: {EFFECT: list(v[EFFECT])}
                for lab, v in self.tab.items() if v[EFFECT][1] > 0}

    def _ctx_table(self):
        out = {}
        for ctx, tbl in self.ctx_table.items():
            d = {}
            for lab, eff in tbl.items():
                if eff[EFFECT][1] > 0:
                    d[lab] = {EFFECT: list(eff[EFFECT])}
            if d:
                out[ctx] = d
        return out

    def _emp(self, lab):
        h, n = self.tab[lab][EFFECT]
        return (h / float(n)) if n else None

    def _resolved(self, lab):
        """True iff the arm has >= MIN_PER_CTX pulls in EVERY context the agent
        has seen. World-agnostic: contexts are opaque keys the agent produced."""
        if not self.contexts_seen:
            return False
        for ctx in self.contexts_seen:
            if self.ctx_table[ctx][lab][EFFECT][1] < MIN_PER_CTX:
                return False
        return True

    def _balanced_est(self, lab):
        """Equal weight per context; requires the arm to be resolved."""
        if not self._resolved(lab):
            return None
        vals = []
        for ctx in self.contexts_seen:
            h, n = self.ctx_table[ctx][lab][EFFECT]
            vals.append(h / float(n))
        return sum(vals) / len(vals)

    def _rich_rate(self, acts):
        """What the alternative pays, as the agent has SEEN it: best empirical
        pooled mean among arms with >= MIN_N_EST trials (its own reward stream)."""
        best = None
        for lab in acts:
            h, n = self.tab[lab][EFFECT]
            if n >= MIN_N_EST:
                m = h / float(n)
                if best is None or m > best:
                    best = m
        return 0.5 if best is None else best

    def _best_pooled(self, acts):
        best, bestlab = None, acts[0]
        for lab in acts:
            m = self._emp(lab)
            if m is None:
                continue
            if best is None or m > best:
                best, bestlab = m, lab
        return bestlab

    # ---- source 2: the exploration term, AS CANDIDATES -----------------
    def _explore_candidates(self, acts, rich):
        """POOLED-optimistic exploration (the ablation 'union_pooledexp'): every
        unresolved arm, scored by the pooled optimistic gap `1 - rich`. This is
        where an exploration term LOSES context-specificity -- a rich pooled
        alternative suppresses exploration even when a single context hides a
        large gain. Kept as an arm precisely to measure that loss."""
        out = []
        for lab in acts:
            if not self._resolved(lab):
                out.append(CG.Candidate(
                    action=lab, effect=EFFECT, context="thin",
                    rate_a=None, rate_o=round(rich, 4),
                    trials=self.tab[lab][EFFECT][1],
                    score=round(1.0 - rich, 4)))
        return out

    def _best_rate_in_ctx(self, ctx, acts):
        """Best rate any RESOLVED arm pays in this context (its own data)."""
        rows = self.ctx_table[ctx]
        best = None
        for lab in acts:
            h, n = rows[lab][EFFECT]
            if n >= MIN_PER_CTX:
                m = h / float(n)
                if best is None or m > best:
                    best = m
        return best

    def _explore_candidates_ctx(self, acts):
        """CONTEXT-CONDITIONAL exploration (the 'good' union): an unresolved arm
        is scored by the OPTIMISTIC gain in the WORST-covered context --
        `1 - best_rate_in_that_context` -- not by the pooled alternative. This is
        the exploration term built INTO C2 so that it does not lose
        context-specificity (the owner's msg_00129 instruction). A high pooled
        alternative no longer masks a context that is still unexplored."""
        out = []
        for lab in acts:
            unresolved = [c for c in self.contexts_seen if not self._resolved_in(lab, c)]
            if not unresolved:
                continue
            best_gain = None
            for c in unresolved:
                br = self._best_rate_in_ctx(c, acts)
                # no resolved arm in this context yet -> the arm may pay at most 1
                gain = 1.0 - (br if br is not None else 0.5)
                if best_gain is None or gain > best_gain:
                    best_gain = gain
            out.append(CG.Candidate(
                action=lab, effect=EFFECT, context="thin-ctx",
                rate_a=None, rate_o=None,
                trials=self.tab[lab][EFFECT][1],
                score=round(best_gain, 4)))
        return out

    def _resolved_in(self, lab, ctx):
        return self.ctx_table[ctx][lab][EFFECT][1] >= MIN_PER_CTX

    # ---- observational half ----------------------------------------
    def _observe_half(self, model, T_obs):
        N = model.N
        obs_arm = model.K - 1
        for _ in range(T_obs):
            x, y, z = model.sample(obs_arm)
            ctx = model.context_of(z)
            for i, xi in enumerate(x):
                if xi == 1:
                    self._record("a%d" % (N + i), y, ctx)
                else:
                    self._record("a%d" % i, y, ctx)

    # ---- the run ----------------------------------------------------
    def run(self, T, model):
        K = model.K
        acts = arm_labels(K)
        half = T // 2
        self._observe_half(model, half)

        t = half
        while t < T:
            if self.use_ctx:
                cands = CG.generate(self._ctx_table(), acts, min_n=self.min_n)
            else:
                cands = CG.generate_flat(self._flat_table(), acts, min_n=self.min_n)
            self.n_gen_calls += 1
            rich = self._rich_rate(acts)

            if self.use_exp:
                # fold the exploration term into the SAME list, then rank the
                # union by value of information; ties go to the LEAST-observed
                # arm (gather evidence where it is thinnest -- the infrequent-arm
                # signal Algorithm 1 uses, world-agnostic).
                if self.exp_mode == "ctx":
                    cands = list(cands) + self._explore_candidates_ctx(acts)
                else:
                    cands = list(cands) + self._explore_candidates(acts, rich)
            cands = sorted(cands, key=lambda c: (-c.score, c.trials, c.action))

            if not cands:
                self.n_empty_gen += 1
                self._pull(model, self._best_pooled(acts))
                t += 1
                continue

            if self.use_cost:
                # turn 134 -- THE ONLY CHANGE. The rule is still selected by
                # `use_cost`/`rule_name` and still returns the accept list in the
                # incoming ranked order; what changed is what the accept decision
                # is computed FROM. `horizon_left = T - t` is the number of steps
                # REMAINING in the episode, which the agent observes: a duration,
                # priced in the same reward units as every other term. No GAIN_UNIT
                # and no price constant appear in any rule this dispatches to.
                accepted = SR.plan(cands, rich, rule=self.rule_name,
                                   horizon_left=T - t, probe_len=PROBE_BLOCK,
                                   beta=self.beta)
            else:
                accepted = cands          # no price: take the top candidate

            if not accepted:
                self.n_empty_gen += 1
                self._pull(model, self._best_pooled(acts))
                t += 1
                continue

            lab = accepted[0].action
            if str(accepted[0].context).startswith("thin"):
                self.n_explore_picks += 1
            n = min(PROBE_BLOCK, T - t)
            for _ in range(n):
                self._pull(model, lab)
            t += n
            self.n_probes += 1

        # ---- the decision: a POLICY, one arm per context ------------
        self.policy = {}
        if self.use_ctx:
            for ctx in self.contexts_seen:
                rows = self.ctx_table[ctx]
                best, bestlab = None, None
                for lab in acts:
                    h, n = rows[lab][EFFECT]
                    if n >= MIN_PER_CTX:
                        m = h / float(n)
                        if best is None or m > best:
                            best, bestlab = m, lab
                if bestlab is not None:
                    self.policy[ctx] = bestlab
        else:
            chosen = self._best_pooled(acts)
            for ctx in self.contexts_seen:
                self.policy[ctx] = chosen
        self.chosen = self.policy.get(self.contexts_seen[0]) if self.contexts_seen else None
        self.regret = float(model.policy_regret(self.policy))
        if hasattr(model, "ctx_opt_arm"):
            self.chosen_is_optimal = int(all(
                self.policy.get(model.context_of(c)) == "a%d" % model.ctx_opt_arm[c]
                for c in model.ctx_opt_arm))
        else:
            self.chosen_is_optimal = int(self.policy.get("flat") ==
                                         "a%d" % model.optimal_arm)
        self.n_resolved = sum(1 for lab in acts if self._resolved(lab))
        return self.regret

    def diagnostics(self):
        return {"n_gen_calls": self.n_gen_calls, "n_empty_gen": self.n_empty_gen,
                "n_probes": self.n_probes, "n_explore_picks": self.n_explore_picks,
                "n_resolved": self.n_resolved, "chosen": self.chosen,
                "chosen_is_optimal": self.chosen_is_optimal,
                "active_pulls": self.active_pulls, "regret": round(self.regret, 6)}


ARMS = {
    # turn 134 arms: the SAME agent, the SAME candidate list, ONLY the stopping
    # rule differs. Each new arm names the rule it dispatches to.
    "voi":           dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx", rule_name="voi"),
    "voi_exp":       dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx", rule_name="voi"),
    "voi_ctx":       dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx", rule_name="voi"),
    "voi_rate":      dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx", rule_name="voi_rate"),
    "voi_rate_noexp": dict(use_ctx=True, use_exp=False, use_cost=True,  exp_mode="ctx", rule_name="voi_rate"),
    "conf":          dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx", rule_name="conf"),
    "conf_noexp":    dict(use_ctx=True,  use_exp=False, use_cost=True,  exp_mode="ctx", rule_name="conf"),
    "frozen_rule":   dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx", rule_name="frozen"),
    "union":         dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx"),
    "union_pooledexp": dict(use_ctx=True, use_exp=True, use_cost=True, exp_mode="pooled"),
    "union_noctx":   dict(use_ctx=False, use_exp=True,  use_cost=True,  exp_mode="ctx"),
    "union_noexp":   dict(use_ctx=True,  use_exp=False, use_cost=True),
    "union_nocost":  dict(use_ctx=True,  use_exp=True,  use_cost=False, exp_mode="ctx"),
    "pure":          dict(use_ctx=False, use_exp=False, use_cost=True),
    "beta0":         dict(use_ctx=True,  use_exp=True,  use_cost=True, exp_mode="ctx", beta=0.0),
}


def make_agent(kind, seed):
    spec = dict(ARMS[kind])
    beta = spec.pop("beta", None)
    return UnionAgent(kind=kind, seed=seed, beta=beta, **spec)


class _UniformPolicy(object):
    """Baseline: pool everything, pick the best POOLED empirical arm, apply it in
    every context. This is the context-blind floor -- it can never reach a
    context-conditional optimum on the masked instance."""

    def __init__(self, seed=0):
        self.seed = seed
        self.tab = defaultdict(lambda: defaultdict(lambda: [0, 0]))

    def run(self, T, model):
        K = model.K
        acts = arm_labels(K)
        N = model.N
        obs_arm = K - 1
        for _ in range(T // 2):
            x, y, z = model.sample(obs_arm)
            for i, xi in enumerate(x):
                lab = ("a%d" % (N + i)) if xi == 1 else ("a%d" % i)
                c = self.tab[lab][EFFECT]
                c[1] += 1
                c[0] += int(y)
        best, bestlab = None, acts[0]
        for lab in acts:
            h, n = self.tab[lab][EFFECT]
            if n:
                m = h / float(n)
                if best is None or m > best:
                    best, bestlab = m, lab
        self.policy = {model.context_of(c): bestlab for c in range(2)} \
            if hasattr(model, "ctx_opt_arm") else {"flat": bestlab}
        self.chosen = bestlab
        self.regret = float(model.policy_regret(self.policy))
        self.chosen_is_optimal = int(self.policy.get(model.context_of(0)) ==
                                     "a%d" % model.optimal_arm)
        return self.regret

    def diagnostics(self):
        return {"chosen": self.chosen, "chosen_is_optimal": self.chosen_is_optimal,
                "regret": round(self.regret, 6)}
