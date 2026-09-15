"""diag_w4e.py -- decisive isolation of the seed-8 decoy false positive.

The real agent's scored arms for (wait,glow) at seed 8 came out
target(wait) 114/200 vs ctrl(grasp) 80/200 in warm, p=0.00055. The world
oracle says glow is action-independent in warm. This script removes the
agent entirely: it drives the EXACT probe protocol (5/5 alternation, the
same affordability gate, position pinned to the station, respawn on
death) and counts warm glow per arm.

  ARMED   target=decoy_action, ctrl=first nonmove != target
  NEUTRAL both arms step the SAME action (pure world exchangeability)

If ARMED reproduces ~114/80 and NEUTRAL shows ~50/50, the leak is in the
protocol's arm asymmetry (different actions -> different RNG draw counts
through the env's short-circuit), not in the world's glow law.
"""
import collections

from env_terrarium_v7 import (
    TerrariumV7, STATION, NONMOVE, pick_edge_action, pick_decoy_action,
)

STEPS = 16000
BLOCK = 5


def scripted(seed, mode):
    ea = pick_edge_action(seed)
    da = pick_decoy_action(seed)
    ctrl = next(a for a in sorted(NONMOVE) if a != da)
    res = collections.Counter()
    env = TerrariumV7(seed, truth=False, decoy=True, rich="low",
                      edge_action=ea)
    env.pos = STATION
    for t in range(STEPS):
        ph = env.phase
        on_target = (t // BLOCK) % 2 == 0
        if mode == "armed":
            a = da if on_target else ctrl
            other = ctrl if on_target else da
        else:                      # neutral: same action both arms
            a = da
            other = da
        aff = env.afford()
        if not (a in aff and other in aff):
            _, _, done, info = env.step(a)
        else:
            _, _, done, info = env.step(a)
            if ph == "warm":
                arm = "target" if on_target else "ctrl"
                res[(arm, "y" if info.get("glow") else "n")] += 1
        if done:
            env = TerrariumV7(seed + 1000 + t, truth=False, decoy=True,
                              rich="low", edge_action=ea)
            env.pos = STATION
    return res, (ea, da, ctrl)


print(f"{'seed':>4} {'edge':>6} {'decoy':>6} {'ctrl':>6} | "
      f"{'ARMED target':>16} {'ARMED ctrl':>16} | "
      f"{'NEUTRAL target':>16} {'NEUTRAL ctrl':>16}")

tot_fp = 0
for seed in range(12):
    ra, info = scripted(seed, "armed")
    rb, _ = scripted(seed, "neutral")

    def fmt(r, arm):
        y = r[(arm, "y")]
        n = y + r[(arm, "n")]
        return f"{y}/{n}={y/n:.3f}" if n else "n/a"

    ea, da, ctrl = info
    print(f"{seed:>4} {ea:>6} {da:>6} {ctrl:>6} | "
          f"{fmt(ra,'target'):>16} {fmt(ra,'ctrl'):>16} | "
          f"{fmt(rb,'target'):>16} {fmt(rb,'ctrl'):>16}")
