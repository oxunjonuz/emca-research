"""diag_w4s.py -- does A7 (PROBE_MAX_BLOCKS 80 -> 120) leave BOTH candidate
readings of C1-iii with the same sign?

The prereg's C1-iii wording is "probe_attempts при rich=high строго меньше,
чем при rich=low... но не ноль". The code stores two different quantities:

  probe_trials        -- scheduled probe STEPS accumulated
  n_cleared           -- distinct candidates the ARBITER actually started
                         probing (the computed decision itself)

If both give high < low at the chosen budget, no definitional choice is
needed. If they disagree, the choice must be declared BEFORE the matrix.
Also reports the exact per-seed table analyze_v7.py will print, for seeds
0..9 (the matrix set), so the calibration is on the same seeds.
"""
import agent_emca_v7 as A
from env_terrarium_v7 import TerrariumV7, pick_edge_action
from agent_emca_v7 import AgentV7Full

STEPS = 16000
NSEED = 60


def run(seed, rich, truth=True):
    ea = pick_edge_action(seed)
    ag = AgentV7Full(seed)
    env = TerrariumV7(seed, truth=truth, decoy=True, rich=rich,
                      edge_action=ea)
    for t in range(STEPS):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = TerrariumV7(seed + 1000 + t, truth=truth, decoy=True,
                              rich=rich, edge_action=ea)
    return ag


for blocks in (120, 160):
    A.PROBE_MAX_BLOCKS = blocks
    print(f"\n########## PROBE_MAX_BLOCKS={blocks} ##########")
    tl, th, cl, ch = [], [], [], []
    for seed in range(NSEED):
        a1 = run(seed, "low")
        a2 = run(seed, "high")
        tl.append(a1.probe_trials)
        th.append(a2.probe_trials)
        cl.append(len({(a, e) for (a, e, _r) in a1.probe_order_log}))
        ch.append(len({(a, e) for (a, e, _r) in a2.probe_order_log}))
    print(f"  probe_trials : low mean {sum(tl)/NSEED:8.1f} "
          f"high mean {sum(th)/NSEED:8.1f}  high<low? {sum(th) < sum(tl)}")
    print(f"  n_cleared    : low mean {sum(cl)/NSEED:8.2f} "
          f"high mean {sum(ch)/NSEED:8.2f}  high<low? {sum(ch) < sum(cl)}"
          f"  high>0? {sum(ch) > 0}  low>0? {sum(cl) > 0}")
    # how many seeds individually show the strict inequality?
    print(f"  per-seed strict: probe_trials "
          f"{sum(1 for x, y in zip(th, tl) if x < y)}/{NSEED} ; "
          f"n_cleared {sum(1 for x, y in zip(ch, cl) if x < y)}/{NSEED}")

print("\n=== per-seed table for the matrix seeds 0..9 (blocks=120) ===")
A.PROBE_MAX_BLOCKS = 120
for seed in range(10):
    a1 = run(seed, "low")
    a2 = run(seed, "high")
    c1 = len({(a, e) for (a, e, _r) in a1.probe_order_log})
    c2 = len({(a, e) for (a, e, _r) in a2.probe_order_log})
    v = a1.verdicts.get((pick_edge_action(seed), "hum"))
    print(f"  seed {seed}: trials lo={a1.probe_trials:5d} hi={a2.probe_trials:5d}"
          f" | cleared lo={c1} hi={c2} | true-edge "
          f"{v['verdict'] if v else 'NONE'}")
