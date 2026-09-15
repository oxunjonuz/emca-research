"""diag_w4m.py -- can the raised evidence budget live inside 16000 steps?

Measured: the seed-8 decoy FP (target 114/200 vs ctrl 80/199, p=0.00055 in
the WARM stratum only) is a TAIL of a calibrated test, not a leak:
  * the two arms consume DISJOINT world-RNG draws (no shared coin);
  * a scripted replica of the identical protocol is calibrated
    (mean gap +0.0003, sd 0.0472 vs binomial 0.0500, 0/160 windows past
    the bar);
  * decorrelating the glow coin removes it;
  * phase keying (pre-move vs world) is identical for that candidate.

The active stratum is ONE phase, so each test runs at ~200/arm when the
life presents only one phase to the candidate -- half the evidence the
scheduled 80 blocks would give if both phases counted. Raising the probe's
EVIDENCE BUDGET (PROBE_MAX_BLOCKS, a shared constant; NO verdict threshold
touched) diluted it: 80 -> 1 FP, 160 -> 0 FP, 320 -> 0 FP, with true-edge
detection unchanged (9/10).

This checks the raised budget is AFFORDABLE at the prereg's 16000 steps and
does not wreck the C1 economics: probe completion, probe_attempts,
true-edge detection, FP, reward, deaths -- all arms, both rich regimes.
"""
import collections

import agent_emca_v7 as A
from env_terrarium_v7 import TerrariumV7, pick_edge_action
from agent_emca_v7 import (AgentV7Full, AgentV7Beta0, AgentV7Perm,
                           AgentV7Forager)

STEPS = 16000
SEEDS = range(10)


def run(cls, seed, truth=True, rich="low", decoy=True):
    ea = pick_edge_action(seed)
    ag = cls(seed)
    env = TerrariumV7(seed, truth=truth, decoy=decoy, rich=rich,
                      edge_action=ea)
    rew = 0.0
    deaths = 0
    for t in range(STEPS):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        rew += r
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            deaths += 1
            env = TerrariumV7(seed + 1000 + t, truth=truth, decoy=decoy,
                              rich=rich, edge_action=ea)
    return ag, rew, deaths


for blocks in (80, 160, 320):
    A.PROBE_MAX_BLOCKS = blocks
    print(f"\n########## PROBE_MAX_BLOCKS={blocks}  steps={STEPS} ##########")
    # full arm: FP on glow, TP on true edge, reward, deaths, blocks done
    fp = tp = 0
    rew_all = []
    deaths_all = []
    blocks_done = collections.Counter()
    for seed in SEEDS:
        ag, rew, deaths = run(AgentV7Full, seed)
        ea = pick_edge_action(seed)
        rew_all.append(rew)
        deaths_all.append(deaths)
        for (a, e), v in ag.verdicts.items():
            if e == "glow" and v["verdict"] == "CAUSAL":
                fp += 1
            if e == "hum" and (a, e) == (ea, "hum") and v["verdict"] == "CAUSAL":
                tp += 1
        for k, v in ag.verdicts.items():
            blocks_done[v.get("blocks", 0)] += 1
        blocks_done[("probe_trials", ag.probe_trials)] += 0
    print(f"  FP(glow)={fp}  TP(true edge)={tp}/10  "
          f"reward mean={sum(rew_all)/len(rew_all):.1f} "
          f"deaths mean={sum(deaths_all)/len(deaths_all):.1f}")
    print(f"  verdict block counts: {dict(blocks_done)}")
    # C1 legs
    b0_probes = 0
    perm_follow = 0
    perm_n = 0
    for seed in SEEDS:
        agb, _, _ = run(AgentV7Beta0, seed)
        b0_probes += agb.probe_trials
        agp, _, _ = run(AgentV7Perm, seed)
        if agp.first_probe and agp.ranked_at_first_probe:
            perm_n += 1
            ranked = sorted(agp.ranked_at_first_probe,
                            key=lambda c: (-c[2], -c[3], c[0], c[1]))
            if agp.first_probe[:2] == (ranked[0][0], ranked[0][1]):
                perm_follow += 1
    print(f"  beta0 probe_trials={b0_probes} ; perm follows ranking "
          f"{perm_follow}/{perm_n}")
    # C1 conflict (rich=high) vs no conflict (rich=low): probe_attempts
    for rich in ("low", "high"):
        pa = []
        for seed in SEEDS:
            ag, _, _ = run(AgentV7Full, seed, rich=rich)
            pa.append(len(ag.probe_order_log))
        print(f"  rich={rich:4s}: probe_attempts per seed {pa} "
              f"mean={sum(pa)/len(pa):.2f}")
