"""diag_w4c.py -- is the seed-8 decoy false positive a WORLD property or a
PROTOCOL (RNG-stream) artifact?

Isolation: no learning, no arbiter. Pin the agent on the station cell and
drive a SCRIPTED 5/5 cadence (target=decoy_action=wait vs ctrl=grasp),
exactly the probe protocol the agent runs. Then compare:

  A. cadence run outdoors-of-phase-skip (the agent's real protocol):
     in cold, wait is UNaffordable -> the env consumes 0 RNG draws for the
     target arm but 1 for the ctrl arm (grasp is always affordable).
  B. cadence with BOTH arms stepping the SAME action (pure world check):
     if glow really is action-independent, A and B differ only through the
     RNG stream offset that the arm asymmetry creates.

If B shows ~0.50/0.50 and A shows a big gap, the leak is my protocol, not
the world. Also sweeps all 10 seeds for both.
"""
import collections

from env_terrarium_v7 import (
    TerrariumV7, STATION, pick_edge_action, pick_decoy_action, NONMOVE,
)

STEPS = 20000
BLOCK = 5


def scripted(seed, mode):
    """mode 'armed'   : target block -> decoy_action (wait), ctrl -> grasp
       mode 'neutral' : both blocks -> the same action (world purity)"""
    ea = pick_edge_action(seed)
    da = pick_decoy_action(seed)
    env = TerrariumV7(seed, truth=True, decoy=True, rich="low",
                      edge_action=ea)
    ctrl = next(a for a in sorted(NONMOVE) if a != da)
    env.pos = STATION
    res = collections.Counter()
    for t in range(STEPS):
        ph = env.phase
        on_target = (t // BLOCK) % 2 == 0
        if mode == "armed":
            a = da if on_target else ctrl
            arm = "target" if on_target else "ctrl"
        else:
            a = da
            arm = "target" if on_target else "ctrl"
        # the agent-side affordability gate (identical to _probe_act):
        # score only if BOTH the scheduled action and its pair are
        # affordable RIGHT NOW
        other = ctrl if on_target else da
        aff = env.afford()
        scored = (a in aff) and (other in aff)
        if not scored:
            env.step(a)          # the benign non-move the agent performs
            continue
        _, _, _, info = env.step(a)
        if ph == "warm":
            res[(arm, "glow_y" if info.get("glow") else "glow_n")] += 1
        # else: cold, unscored (same rule the verdict uses)
    return res, (ea, da, ctrl)


print(f"{'seed':>4} {'edge':>6} {'decoy':>6} {'ctrl':>6} | "
      f"{'ARMED  target':>14} {'ctrl':>14} | {'NEUTRAL target':>14} {'ctrl':>14}")
for seed in range(10):
    ra, info = scripted(seed, "armed")
    rb, _ = scripted(seed, "neutral")
    def fmt(r, arm):
        y = r[(arm, "glow_y")]
        n = y + r[(arm, "glow_n")]
        return f"{y}/{n}={y/n:.3f}" if n else "n/a"
    ea, da, ctrl = info
    print(f"{seed:>4} {ea:>6} {da:>6} {ctrl:>6} | "
          f"{fmt(ra,'target'):>14} {fmt(ra,'ctrl'):>14} | "
          f"{fmt(rb,'target'):>14} {fmt(rb,'ctrl'):>14}")
