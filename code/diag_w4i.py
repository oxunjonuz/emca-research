"""diag_w4i.py -- is W4's FP=0 gate achievable at all, and is the seed-8 FP
caused by MULTIPLICITY in my own verifier?

Facts already measured (files diag_w4b..h):
  * seed 8, candidate (wait,glow): target warm 114/200 vs ctrl 80/199,
    plain two-proportion Fisher p=0.00055, RR=1.418 -> CAUSAL.
  * the two arms' world-RNG draw indices are DISJOINT (no shared draws),
    a scored warm step consumes exactly 2 draws, and the scripted replica
    of the same protocol (no agent, 160 windows) is CALIBRATED: mean gap
    +0.0003, sd 0.0472 vs binomial 0.0500, 0/160 windows passed the bar.
  * the FP reproduces in the null regime (truth=off) at the same seed.

=> the per-test p-value is valid; the question is whether "FP == 0 across
   all seeds and candidates" is a gate a CALIBRATED test can pass, and
   whether the verifier's own selection (several candidates per life, and
   a max over phases) inflates the family-wise error rate.

Measurement: run the real agent in the NULL regime (truth=off) and in the
TRUTH regime (truth=on), and re-derive every verdict from the stored
probe_log under two bars, applied IDENTICALLY to all arms:

  A) per-test:      p < 0.05                      (current code)
  B) family-wise:   p < 0.05 / (n_cand * n_ph)     (Bonferroni)

and report, per regime: false positives on glow, true-edge detections,
and the family-wise FP rate over the seed set.
"""
import collections
import math

from env_terrarium_v7 import TerrariumV7, pick_edge_action
from agent_emca_v7 import AgentV7Full

STEPS = 16000
NSEED = 40


def fisher_greater(a_yes, a_no, c_yes, c_no):
    n = a_yes + a_no + c_yes + c_no
    if n == 0:
        return 1.0
    r1, c1 = a_yes + a_no, a_yes + c_yes
    hi = min(r1, c1)
    p = 0.0
    denom = math.comb(n, c1)
    for x in range(a_yes, hi + 1):
        p += math.comb(r1, x) * math.comb(n - r1, c1 - x) / denom
    return min(1.0, p)


RR_ACCEPT = 1.3


def verdicts_at_bar(probe_log, n_cand, alpha):
    """Re-derive every verdict from the stored phase-keyed log at a given
    family-wise alpha. Selection of the active stratum is IDENTICAL to the
    code (max by min(n_t,n_c), then by target hits)."""
    out = {}
    for key, log in probe_log.items():
        phases = sorted(set(log["target"]) | set(log["ctrl"]))
        strata = {}
        for ph in phases:
            ty, tn = log["target"][ph]
            cy, cn = log["ctrl"][ph]
            strata[ph] = (ty, tn, cy, cn)
        if not strata:
            out[key] = ("UNRESOLVED", 1.0, 0.0, 0, 0, 0, 0, None)
            continue
        active = max(strata, key=lambda ph: (
            min(strata[ph][0] + strata[ph][1], strata[ph][2] + strata[ph][3]),
            strata[ph][0] + strata[ph][2]))
        ty, tn, cy, cn = strata[active]
        if (ty + tn) == 0 or (cy + cn) == 0:
            out[key] = ("UNRESOLVED", 1.0, 0.0, ty, tn, cy, cn, active)
            continue
        p = fisher_greater(ty, tn, cy, cn)
        ra = ty / (ty + tn)
        rc = cy / (cy + cn)
        rr = (ra / rc) if rc > 0 else float("inf")
        bar = alpha / max(1, n_cand)
        if p < bar and rr >= RR_ACCEPT:
            v = "CAUSAL"
        elif p < bar and rr < RR_ACCEPT:
            v = "REJECT"
        elif p >= bar and rr < RR_ACCEPT:
            v = "REJECT"
        else:
            v = "UNRESOLVED"
        out[key] = (v, p, rr, ty, tn, cy, cn, active)
    return out


def run(seed, truth, alpha):
    ea = pick_edge_action(seed)
    ag = AgentV7Full(seed)
    env = TerrariumV7(seed, truth=truth, decoy=True, rich="low",
                      edge_action=ea)
    for t in range(STEPS):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = TerrariumV7(seed + 1000 + t, truth=truth, decoy=True,
                              rich="low", edge_action=ea)
    n_cand = len(ag.probe_log)
    return ea, verdicts_at_bar(ag.probe_log, n_cand, alpha), n_cand


for alpha, label in ((0.05, "A) per-test  p<0.05"),
                     (0.05, "B) family-wise p<0.05/k")):
    print(f"\n############ BAR {label} ############")
    for truth in (False, True):
        tag = "NULL truth=off" if not truth else "TRUTH truth=on"
        fp = 0
        fp_seeds = []
        tps = 0
        fns = []
        for seed in range(NSEED):
            ea, vd, n_cand = run(seed, truth, alpha)
            for (a, e), v in vd.items():
                if e == "glow" and v[0] == "CAUSAL":
                    fp += 1
                    fp_seeds.append((seed, a, round(v[1], 5), round(v[2], 3),
                                     n_cand))
            if truth:
                v = vd.get((ea, "hum"))
                if v and v[0] == "CAUSAL":
                    tps += 1
                else:
                    fns.append((seed, (v[0] if v else "NONE")))
        print(f"  {tag}: glow CAUSALs (FP) = {fp} over {NSEED} runs")
        if fp_seeds:
            for f in fp_seeds:
                print("      ", f)
        if truth:
            print(f"     true-edge detected: {tps}/{NSEED} ; misses: {fns}")
