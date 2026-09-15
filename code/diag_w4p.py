"""diag_w4p.py -- choose the pre-matrix amendment A7 on MEASURED trade-offs.

The seed-8 decoy FP is a tail of a calibrated test (5 independent probes:
disjoint RNG draws, calibrated scripted replica, decorrelation removes it,
phase keying identical, both truth regimes). It dilutes with more evidence.

A7 candidate settings, all at the FIXED thresholds (p<0.05, RR>=1.3) and the
FIXED 16000-step life budget:
  (1) PROBE_MAX_BLOCKS 80  (as frozen)
  (2) PROBE_MAX_BLOCKS 160
  (3) PROBE_MAX_BLOCKS 240

For each: FP (truth on / off), true-edge detection, and BOTH candidate
metrics for C1-iii -- the prereg's own phrase is "probe_attempts":
   * probe_trials        (what analyze_v7.py coded)
   * n_cleared           (the arbiter's own decision: how many candidates
                          clear value_k > rich_rate*H + cost -- the
                          COMPUTED quantity C1 is about)
plus C1-i (beta0 probes) and C1-ii (perm follows ranking).
"""
import collections

import agent_emca_v7 as A
from env_terrarium_v7 import TerrariumV7, pick_edge_action
from agent_emca_v7 import AgentV7Full, AgentV7Beta0, AgentV7Perm

STEPS = 16000
SEEDS = list(range(20))


def run(cls, seed, truth=True, rich="low"):
    ea = pick_edge_action(seed)
    ag = cls(seed)
    env = TerrariumV7(seed, truth=truth, decoy=True, rich=rich,
                      edge_action=ea)
    rew = 0.0
    for t in range(STEPS):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        rew += r
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = TerrariumV7(seed + 1000 + t, truth=truth, decoy=True,
                              rich=rich, edge_action=ea)
    return ag, rew


def cleared_count(ag):
    """The arbiter's decision, reconstructed from what it actually did:
    distinct candidates it started a probe on (probe_order_log entries),
    deduplicated by (action, effect), capped by what _plan returned."""
    return len({(a, e) for (a, e, _rk) in ag.probe_order_log})


for blocks in (80, 160, 240):
    A.PROBE_MAX_BLOCKS = blocks
    fp_on, fp_off = [], []
    tp = 0
    miss = []
    trials_lo, trials_hi = [], []
    cleared_lo, cleared_hi = [], []
    rew_lo, rew_hi = [], []
    b0 = 0
    perm_ok = perm_n = 0
    for seed in SEEDS:
        ag, rew = run(AgentV7Full, seed)
        ea = pick_edge_action(seed)
        rew_lo.append(rew)
        trials_lo.append(ag.probe_trials)
        cleared_lo.append(cleared_count(ag))
        for (a, e), v in ag.verdicts.items():
            if e == "glow" and v["verdict"] == "CAUSAL":
                fp_on.append((seed, a, v["p"], v["rr"]))
        v = ag.verdicts.get((ea, "hum"))
        if v and v["verdict"] == "CAUSAL":
            tp += 1
        else:
            miss.append(seed)

        ag2, rew2 = run(AgentV7Full, seed, rich="high")
        rew_hi.append(rew2)
        trials_hi.append(ag2.probe_trials)
        cleared_hi.append(cleared_count(ag2))

        ago, _ = run(AgentV7Full, seed, truth=False)
        for (a, e), v in ago.verdicts.items():
            if e == "glow" and v["verdict"] == "CAUSAL":
                fp_off.append((seed, a, v["p"], v["rr"]))

        b0 += run(AgentV7Beta0, seed)[0].probe_trials
        agp, _ = run(AgentV7Perm, seed)
        if agp.first_probe and agp.ranked_at_first_probe:
            perm_n += 1
            rk = sorted(agp.ranked_at_first_probe,
                        key=lambda c: (-c[2], -c[3], c[0], c[1]))
            if agp.first_probe[:2] == (rk[0][0], rk[0][1]):
                perm_ok += 1

    print(f"\n########## PROBE_MAX_BLOCKS={blocks} ##########")
    print(f"  FP truth=on : {len(fp_on)} {fp_on}")
    print(f"  FP truth=off: {len(fp_off)} {fp_off}")
    print(f"  true edge TP: {tp}/20  misses={miss}")
    print(f"  C1-i  beta0 probe_trials={b0} (must be 0)")
    print(f"  C1-ii perm follows ranking: {perm_ok}/{perm_n}")
    print(f"  C1-iii metric A probe_trials: low mean "
          f"{sum(trials_lo)/20:.0f} high mean {sum(trials_hi)/20:.0f} "
          f"-> high<low? {sum(trials_hi) < sum(trials_lo)}")
    print(f"  C1-iii metric B n_cleared  : low mean "
          f"{sum(cleared_lo)/20:.2f} high mean {sum(cleared_hi)/20:.2f} "
          f"-> high<low? {sum(cleared_hi) < sum(cleared_lo)} "
          f"| low>0? {sum(cleared_lo) > 0} high>0? {sum(cleared_hi) > 0}")
    print(f"  reward: low mean {sum(rew_lo)/20:.1f} high mean "
          f"{sum(rew_hi)/20:.1f}")
