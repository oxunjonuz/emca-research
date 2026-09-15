"""diag_w4f.py -- CALIBRATION of the probe's null distribution.

Question: is seed 8's decoy FP (a) a deterministic small-sample fluke of an
honest protocol, or (b) evidence of a bias/dependence in the protocol?

Measurement 1 (empirical null of the exact statistic the verifier uses):
  a scripted 5/5 alternation in the world, NO agent, pinned on the station,
  null regime (truth=off): glow is warm-only p=0.50 for EVERY action.
  Collect many independent 400-scored-step windows (200/arm) and compare
  the observed distribution of the one-sided Fisher p and of the rate gap
  with the binomial/Monte-Carlo expectation under exchangeability.

Measurement 2 (real agent, null regime): 40 seeds, count CAUSAL verdicts
  on glow => the protocol's empirical FP rate at the real bar (p<0.05 and
  RR>=1.3).

A calibrated protocol: mean gap 0, sd ~ 0.050 (n=200/arm), ~0.5% of windows
pass the bar. A flag is raised only if the empirical tail is heavier.
"""
import collections
import math
import random

from env_terrarium_v7 import (
    TerrariumV7, STATION, NONMOVE, pick_edge_action, pick_decoy_action,
)
from agent_emca_v7 import AgentV7Full

BLOCK = 5


def fisher_greater(a_yes, a_no, c_yes, c_no):
    n = a_yes + a_no + c_yes + c_no
    r1, c1 = a_yes + a_no, a_yes + c_yes
    hi = min(r1, c1)
    p = 0.0
    denom = math.comb(n, c1)
    for x in range(a_yes, hi + 1):
        p += math.comb(r1, x) * math.comb(n - r1, c1 - x) / denom
    return min(1.0, p)


def window_rows(seed, n_scored=400):
    """Return the list of (arm, glow) over the first n_scored SCORED warm
    steps of a scripted 5/5 protocol (target=decoy_action, ctrl=other)."""
    da = pick_decoy_action(seed)
    ctrl = next(a for a in sorted(NONMOVE) if a != da)
    env = TerrariumV7(seed, truth=False, decoy=True, rich="low")
    env.pos = STATION
    rows = []
    for t in range(40000):
        if len(rows) >= n_scored:
            break
        on_target = (t // BLOCK) % 2 == 0
        a = da if on_target else ctrl
        other = ctrl if on_target else da
        aff = env.afford()
        if not (a in aff and other in aff):
            _, _, done, info = env.step(a)
        else:
            _, _, done, info = env.step(a)
            if env.phase == "warm":
                rows.append((0 if on_target else 1, 1 if info.get("glow") else 0))
        if done:
            env = TerrariumV7(seed + 7000 + t, truth=False, decoy=True,
                              rich="low")
            env.pos = STATION
    return rows


print("=== M1: empirical null of the verifier statistic (scripted, no agent) ===")
NSEED = 160
gaps, ps, pass_bar = [], [], 0
for s in range(NSEED):
    rows = window_rows(s, 400)
    ty = sum(1 for a, g in rows if a == 0 and g)
    tn = sum(1 for a, g in rows if a == 0 and not g)
    cy = sum(1 for a, g in rows if a == 1 and g)
    cn = sum(1 for a, g in rows if a == 1 and not g)
    ra = ty / (ty + tn)
    rc = cy / (cy + cn)
    gaps.append(ra - rc)
    pp = fisher_greater(ty, tn, cy, cn)
    ps.append(pp)
    if pp < 0.05 and rc > 0 and ra / rc >= 1.3:
        pass_bar += 1

mean_gap = sum(gaps) / len(gaps)
sd_gap = (sum((g - mean_gap) ** 2 for g in gaps) / (len(gaps) - 1)) ** 0.5
print(f"   windows={len(gaps)} mean_gap={mean_gap:+.4f} sd_gap={sd_gap:.4f} "
      f"(binomial prediction for n=200/arm: 0.0500)")
print(f"   Fisher p: min={min(ps):.5f} median={sorted(ps)[len(ps)//2]:.3f}")
print(f"   windows passing the real bar (p<0.05 AND RR>=1.3): {pass_bar}/{len(ps)}"
      f" = {100*pass_bar/len(ps):.2f}%")
# Monte-Carlo expectation under exchangeability for the same n
rng = random.Random(0)
mc = 0
NMC = 20000
for _ in range(NMC):
    ty = sum(1 for _ in range(200) if rng.random() < 0.5)
    cy = sum(1 for _ in range(200) if rng.random() < 0.5)
    ra, rc = ty / 200, cy / 200
    if rc > 0 and ra / rc >= 1.3 and fisher_greater(ty, 200 - ty, cy, 200 - cy) < 0.05:
        mc += 1
print(f"   Monte-Carlo expectation (iid, 200/arm): {100*mc/NMC:.2f}%")

print(f"\n=== M2: real agent, null regime (truth=off), FP rate on glow ===")
N2 = 40
fp = 0
tests = 0
for seed in range(N2):
    ea = pick_edge_action(seed)
    ag = AgentV7Full(seed)
    env = TerrariumV7(seed, truth=False, decoy=True, rich="low",
                      edge_action=ea)
    for t in range(16000):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = TerrariumV7(seed + 1000 + t, truth=False, decoy=True,
                              rich="low", edge_action=ea)
    for (a, e), v in ag.verdicts.items():
        tests += 1
        if e == "glow" and v["verdict"] == "CAUSAL":
            fp += 1
            print(f"   seed {seed}: glow CAUSAL {a}->{e} p={v['p']} rr={v['rr']}")
print(f"   glow CAUSALs: {fp} (all verdicts issued: {tests})")
