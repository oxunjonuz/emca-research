"""diag_w4.py -- diagnose the W4 false positive (a CAUSAL verdict on the decoy).

Seed 8 (edge=grasp, decoy_action=wait) yields CAUSAL wait->glow with
target 114/200 = 0.570 vs ctrl 80/199 = 0.402 in the warm stratum.
In warm, glow is a world event at p=0.50 for EVERY action, so the two arms
must be exchangeable. This script logs every SCORED step to find why not.
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
print(f"env.decoy_action={env.decoy_action} phase_span={env.phase_span}")

rows = []
for t in range(STEPS):
    o = env.obs()
    a = ag.act(o)
    pre = (env.phase, env.pos, env._in_aura(), a in env.afford(), env.fruit,
           env.pool)
    st = ag.probe_state
    cand = (st["cand"].action, st["cand"].effect) if st else None
    o2, r, done, info = env.step(a)
    mark = getattr(ag, "_probe_mark", None)
    rows.append((t, cand, mark, a, pre, bool(info.get("glow")),
                 bool(info.get("hum")), env.pos, env._in_aura()))
    ag.observe(o, a, r, o2, done, info)
    if info.get("died"):
        env = TerrariumV7(SEED + 1000 + t, truth=True, decoy=True, rich="low",
                          edge_action=ea)

# ---- 1. scored steps by arm x mark-phase ------------------------------
c = collections.Counter()
for (t, cand, mark, a, pre, glow, hum, post, post_aura) in rows:
    if mark is None:
        continue
    arm, act, ph = mark
    c[(cand, arm, act, ph, glow)] += 1
print("\n--- scored steps (cand, arm, act, mark_phase, glow) ---")
for k in sorted(c, key=str):
    print("  ", k, c[k])

# ---- 2. glow rate per arm inside the warm stratum --------------------
agg = collections.Counter()
for (t, cand, mark, a, pre, glow, hum, post, post_aura) in rows:
    if mark is None:
        continue
    arm, act, ph = mark
    agg[(arm, ph, glow)] += 1
print("\n--- per (arm, phase): glow yes/no ---")
for arm in ("target", "ctrl"):
    for ph in ("warm", "cold"):
        y = agg[(arm, ph, True)]
        n = y + agg[(arm, ph, False)]
        if n:
            print(f"   {arm:6s} {ph:4s}  glow {y}/{n} = {y/n:.4f}")

# ---- 3. position/pre-state of scored target vs ctrl steps ------------
print("\n--- scored steps: PRE phase, PRE in_aura, POST in_aura ---")
pa = collections.Counter()
for (t, cand, mark, a, pre, glow, hum, post, post_aura) in rows:
    if mark is None:
        continue
    arm, act, ph = mark
    pa[(arm, pre[0], pre[2], post_aura)] += 1
for k in sorted(pa, key=str):
    print("  ", k, pa[k])

# ---- 4. are target and ctrl steps in DIFFERENT t-windows? ------------
print("\n--- scored step t-ranges per arm/phase ---")
tr = collections.defaultdict(list)
for (t, cand, mark, a, pre, glow, hum, post, post_aura) in rows:
    if mark is None:
        continue
    arm, act, ph = mark
    tr[(arm, ph)].append(t)
for k in sorted(tr, key=str):
    v = tr[k]
    print(f"   {k}: n={len(v)} t in [{min(v)},{max(v)}]")

# ---- 5. verdict payload --------------------------------------------
print("\n--- verdicts ---")
print(json.dumps({f"{a}->{e}": v for (a, e), v in ag.verdicts.items()},
                 indent=2, default=str))
print("\n--- probe_log for the decoy candidate ---")
for k, v in ag.probe_log.items():
    print("  ", k, {ph: dict(d) for ph, d in v.items()} if v else v)
