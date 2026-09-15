"""diag_bayes_decisions.py -- turn 135. THE decisive diagnostic.

The matrix shows a strange thing: `bayes` (T4) and `voi` (T2) have BIT-IDENTICAL
regret on every pub cell and on maskr (CI exactly [0,0]), while their PROBE
COUNTS differ. And G4 (bayes probes >= voi wherever voi probes) FAILED at two
richness levels.

This script asks the honest question: at the states the agent ACTUALLY VISITS,
how often do the two rules disagree, and does a disagreement ever change the
decision the agent would make? It instruments the agent's own decision loop.

Output: for each instance, the number of candidate decisions, the number where
T2 accepts and T4 refuses, the number where T4 accepts and T2 refuses, and the
number of episodes in which the FINAL chosen arm differs.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "ext", "latt_py3"))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

import numpy as np

import candidate_gen as CG
import stopping_rules as SR
import bayes_stopping as BS
import union_run_v2
import union_agent_v4

OBS = {"n_decisions": 0, "t2_only": 0, "t4_only": 0, "both": 0, "neither": 0,
       "states": [], "t2_only_detail": []}


def instrumented_run(arm, inst, param, seed, T=400):
    """Run the v4 agent but intercept the arbiter call to record both rules'
    decisions at every state actually visited."""
    import types
    np.random.seed(seed)
    if inst == "mask":
        model = union_run_v2.MaskedParallel(N=50, m=1, eps=float(param))
    elif inst == "maskr":
        model = union_run_v2.MaskedParallel(N=50, m=1, eps=float(param), base=0.8)
    elif inst == "pub":
        import models as M
        from union_instance import PublishedParallel
        model = PublishedParallel(M.Parallel.create(50, int(param), 0.3))
    else:
        raise ValueError(inst)

    ag = union_agent_v4.make_agent(arm, seed)
    real_plan = BS.plan

    def spy(cands, r_best, horizon_left=None, probe_len=20, **kw):
        t4 = real_plan(cands, r_best, horizon_left=horizon_left,
                       probe_len=probe_len)
        t2 = SR.plan(cands, r_best, rule="voi", horizon_left=horizon_left,
                     probe_len=probe_len)
        a4 = {c.action for c in t4}
        a2 = {c.action for c in t2}
        if a4 == a2:
            OBS["both" if a4 else "neither"] += 1
        elif a2 - a4:
            OBS["t2_only"] += 1
            # record EVERY state where T2 accepts and T4 refuses, with the margins
            for c in cands:
                if c.action in (a2 - a4):
                    t2m = SR.voi_terms(c.rate_a, c.trials, r_best, int(probe_len),
                                       float(horizon_left))
                    mu, commit, probe, V, LL = BS.terms_bayes(
                        c.rate_a, c.trials, r_best, int(probe_len),
                        float(horizon_left))
                    OBS["t2_only_detail"].append(
                        (c.rate_a, c.trials, float(r_best),
                         float(horizon_left), t2m.info - t2m.risk, probe - commit))
        else:
            OBS["t4_only"] += 1
        OBS["n_decisions"] += 1
        if cands:
            first = cands[0]
            # record the TRUE horizon the decision was made at, so the printed
            # margins are the actual ones (a fixed L would be a different state)
            OBS["states"].append((first.rate_a, first.trials, float(r_best),
                                  bool(a2), bool(a4), float(horizon_left)))
        return t4

    BS.plan = spy
    try:
        r = ag.run(T, model)
    finally:
        BS.plan = real_plan
    return r, ag


for inst, params in (("mask", (0.35,)), ("maskr", (0.35,)),
                     ("pub", (16, 49))):
    for p in params:
        for key in OBS:
            OBS[key] = [] if key in ("states", "t2_only_detail") else 0
        chosen_diff = 0
        regs = []
        for seed in range(1, 11):
            r, ag = instrumented_run("bayes", inst, p, seed)
            regs.append(r)
        print("%-6s p=%-4s decisions=%-5d  rules agree=%-5d  T2-only=%-4d "
              "T4-only=%-4d  (obj. differ on %d/%d seeds)"
              % (inst, p, OBS["n_decisions"], OBS["both"] + OBS["neither"],
                 OBS["t2_only"], OBS["t4_only"], chosen_diff, 10))
        # the states where they disagree, with the numbers
        dis = [s for s in OBS["states"] if s[3] != s[4]]
        if dis:
            print("     first disagreements (rate_a, trials, r_best, T2, T4, L):")
            for s in dis[:4]:
                L = s[5]
                mu, commit, probe, V, m = BS.terms_bayes(s[0], s[1], s[2], 20, L)
                t2 = SR.voi_terms(s[0], s[1], s[2], 20, L)
                print("       rate=%-5s tr=%-4s r=%.3f L=%-5.0f T2=%-5s T4=%-5s"
                      "   T2 margin=%+.3e  T4 margin=%+.3e  L=%d"
                      % (s[0], s[1], s[2], L, s[3], s[4], t2.info - t2.risk,
                         probe - commit, m))
        # ANY state where T2 accepted and T4 refused: the theorem says these must
        # all be indifference ties. Report the worst margin if not.
        det = OBS["t2_only_detail"]
        if det:
            big = [d for d in det if abs(d[4]) > 1e-12]
            print("     T2-accepts/T4-refuses on %d candidate-states; "
                  "with T2 margin > 1e-12: %d" % (len(det), len(big)))
            if big:
                print("       REAL VIOLATIONS (rate_a, trials, r, L, T2m, T4m):")
                for d in big[:6]:
                    print("         %s" % (d,))
            else:
                print("       worst T2 margin among them: %.3e (all ties)"
                      % max(abs(d[4]) for d in det))
        print()