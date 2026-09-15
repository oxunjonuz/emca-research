"""diag_w4b.py -- WHERE does the seed-8 decoy false positive come from?

Seed 8: edge=grasp, decoy=wait. Verdict (wait, glow) -> CAUSAL with
target warm 114/200 = 0.570 vs ctrl warm 80/199 = 0.402 (Fisher p=0.00055).
In warm, glow is documented as a world event at p=0.50 for EVERY action,
so the two arms must be exchangeable. This logs every step and asks:

  0. how many steps were actually SCORED for (wait,glow), by arm/phase
  1. is the WORLD glow rate action-independent in warm? (all in-aura warm
     steps, split by the action actually taken)
  2. scored steps: was the agent actually in the aura at the time?
  3. block-level (5-step) rates: overdispersion or independent trials
  4. how often was the probe RESTARTED (blocks counter reset)
  5. verdict payload + probe_log
"""
import collections
import json

from env_terrarium_v7 import TerrariumV7, pick_edge_action, pick_decoy_action
from agent_emca_v7 import AgentV7Full

SEED = 8
STEPS = 16000

ea = pick_edge_action(SEED)
da = pick_decoy_action(SEED)
print(f"seed={SEED} edge_action={ea} decoy_action={da}")

ag = AgentV7Full(SEED)
env = TerrariumV7(SEED, truth=True, decoy=True, rich="low", edge_action=ea)

rows = []
prev_state = None
restarts = []
for t in range(STEPS):
    o = env.obs()
    pre = (t, env.t, env.phase, env._in_aura(), env.pos, round(env.energy, 2))
    st_before = ag.probe_state
    cand_before = (st_before["cand"].action, st_before["cand"].effect) \
        if st_before else None
    blocks_before = st_before["blocks"] if st_before else None
    a = ag.act(o)
    st_after = ag.probe_state
    if st_before is not None and st_after is not None \
            and cand_before == (st_after["cand"].action,
                                st_after["cand"].effect) \
            and blocks_before is not None and st_after["blocks"] == 0 \
            and blocks_before > 0:
        restarts.append((t, pre[2]))
    mark = getattr(ag, "_probe_mark", None)
    o2, r, done, info = env.step(a)
    rows.append((pre, a, bool(info.get("glow")), bool(info.get("hum")),
                 mark, cand_before, bool(info.get("died"))))
    ag.observe(o, a, r, o2, done, info)
    if info.get("died"):
        env = TerrariumV7(SEED + 1000 + t, truth=True, decoy=True,
                          rich="low", edge_action=ea)

print(f"probe restarts (blocks reset >0 -> 0): {len(restarts)} "
      f"first5={restarts[:5]}")

sc = [r for r in rows if r[4] is not None and r[5] == ("wait", "glow")]
print(f"\nscored steps for (wait,glow): {len(sc)}")
c = collections.Counter()
for (pre, a, glow, hum, mark, cand, died) in sc:
    arm, act, ph = mark
    c[(arm, ph, glow)] += 1
for k in sorted(c, key=str):
    print("   (arm, phase, glow):", k, c[k])

print("\n--- ALL in-aura warm steps, by action taken (unscored included) ---")
w = collections.Counter()
for (pre, a, glow, hum, mark, cand, died) in rows:
    if pre[2] == "warm" and pre[3]:
        w[(a, "glow_yes" if glow else "glow_no")] += 1
for a in ("wait", "press", "grasp", "up", "down", "left", "right"):
    y = w[(a, "glow_yes")]
    n = y + w[(a, "glow_no")]
    if n:
        print(f"   {a:6s} glow {y}/{n} = {y/n:.4f}")

print("\n--- scored (wait,glow) steps: PRE in_aura? ---")
c2 = collections.Counter()
for (pre, a, glow, hum, mark, cand, died) in sc:
    arm, act, ph = mark
    c2[(arm, ph, pre[3])] += 1
for k in sorted(c2, key=str):
    print("   (arm, phase, in_aura):", k, c2[k])

print("\n--- scored (wait,glow) steps: was the EXECUTED action == scheduled? ---")
c3 = collections.Counter()
for (pre, a, glow, hum, mark, cand, died) in sc:
    arm, act, ph = mark
    c3[(arm, act, a, act == a)] += 1
for k in sorted(c3, key=str):
    print("   ", k, c3[k])

print("\n--- block-level (5-step) glow rates per arm (warm only) ---")
blocks = collections.defaultdict(lambda: [0, 0])
for (pre, a, glow, hum, mark, cand, died) in sc:
    arm, act, ph = mark
    if ph != "warm":
        continue
    blocks[(arm, pre[0] // 5)][0 if glow else 1] += 1
per_arm = collections.defaultdict(list)
for (arm, b), (y, n) in blocks.items():
    if n:
        per_arm[arm].append(y / n)
for arm in sorted(per_arm):
    v = per_arm[arm]
    m = sum(v) / len(v)
    var = sum((x - m) ** 2 for x in v) / max(1, len(v) - 1)
    print(f"   {arm:6s} buckets={len(v)} mean_rate={m:.4f} var={var:.4f} "
          f"(binomial var for p=.5,n=5 = .050)")

print("\n--- verdicts ---")
print(json.dumps({f"{a}->{e}": v for (a, e), v in ag.verdicts.items()},
                 indent=2, default=str))
print("\n--- probe_log ---")
for k in ag.probe_log:
    print("   ", k, {ph: dict(d) for ph, d in ag.probe_log[k].items()})
