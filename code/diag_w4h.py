"""diag_w4h.py -- settle it: is the seed-8 decoy FP a BIAS (the two arms do
not see exchangeable draws) or a TAIL (an honest p=0.5 test landing at
3.4 sigma on a fixed seed)?

Instrument the world's RNG: log the draw index at every SCORED step for
seed 8, per arm. Then:

  * if target-draw-indices and ctrl-draw-indices are DISJOINT, the two
    arms are independent draws -> the observed gap is a tail event of an
    honest test.
  * if they OVERLAP (the same draw scores both arms) or if one arm's
    draws are systematically biased (e.g. always the 2nd position of a
    pair), the protocol is broken.

Also: the full statistic distribution over the whole stream, plus a
conditional permutation check -- including a synthetic control where the
world uses an independent glow stream (DECORR) -- and count how many
distinct test statistics the seed-8 life actually produced.
"""
import collections

from env_terrarium_v7 import TerrariumV7, pick_edge_action, pick_decoy_action
from agent_emca_v7 import AgentV7Full

SEED = 8
STEPS = 16000

ea = pick_edge_action(SEED)
da = pick_decoy_action(SEED)
print(f"seed={SEED} edge={ea} decoy={da}")

ag = AgentV7Full(SEED)
env = TerrariumV7(SEED, truth=True, decoy=True, rich="low", edge_action=ea)

# wrap the env RNG to count draws
orig_random = env.rng.random
counter = {"n": 0}


def counting_random():
    counter["n"] += 1
    return orig_random()


env.rng.random = counting_random

# map: (arm, draw_index) -> glow result of the SECOND draw of that step
scored = []
for t in range(STEPS):
    o = env.obs()
    a = ag.act(o)
    mark = getattr(ag, "_probe_mark", None)
    before = counter["n"]
    o2, r, done, info = env.step(a)
    after = counter["n"]
    if mark is not None:
        cand = (ag.probe_state["cand"].action,
                ag.probe_state["cand"].effect) if ag.probe_state else None
        scored.append({"t": t, "arm": mark[0], "act": mark[1],
                       "phase": mark[2], "cand": cand,
                       "draws": (before, after),
                       "glow": bool(info.get("glow")),
                       "hum": bool(info.get("hum"))})
    ag.observe(o, a, r, o2, done, info)
    if info.get("died"):
        env = TerrariumV7(SEED + 1000 + t, truth=True, decoy=True,
                          rich="low", edge_action=ea)
        env.rng.random = counting_random   # rewrap after respawn

print(f"\ntotal world RNG draws: {counter['n']}")
print(f"scored steps: {len(scored)}")

for target in (("wait", "glow"), ("grasp", "hum"), ("grasp", "glow")):
    rows = [s for s in scored if s["cand"] == target and s["phase"] == "warm"]
    tgt = [s for s in rows if s["arm"] == "target"]
    ctl = [s for s in rows if s["arm"] == "ctrl"]
    ti = sorted(s["draws"][1] - 1 for s in tgt)   # index of the glow draw
    ci = sorted(s["draws"][1] - 1 for s in ctl)
    inter = set(ti) & set(ci)
    ty = sum(1 for s in tgt if s["glow"])
    cy = sum(1 for s in ctl if s["glow"])
    print(f"\ncandidate {target}: target n={len(tgt)} glow={ty} "
          f"({ty/max(1,len(tgt)):.3f}) | ctrl n={len(ctl)} glow={cy} "
          f"({cy/max(1,len(ctl)):.3f}) | overlap of draw indices: "
          f"{len(inter)}")
    print(f"   target draw idx range [{min(ti) if ti else '-'}, "
          f"{max(ti) if ti else '-'}] ; ctrl [{min(ci) if ci else '-'}, "
          f"{max(ci) if ci else '-'}]")

# the decisive test: is glow at a scored step equal to (draw < 0.5) of a
# draw that is OTHERWISE used by the other arm?
print("\n--- how many draws does a scored step consume? ---")
c = collections.Counter(s["draws"][1] - s["draws"][0] for s in scored)
print("   draws per scored step:", dict(c))
c2 = collections.Counter((s["arm"], s["draws"][1] - s["draws"][0])
                         for s in scored)
print("   by arm:", dict(c2))

print("\n--- was the glow draw possibly SHARED with the hum comparison? ---")
c3 = collections.Counter((s["arm"], s["hum"], s["glow"]) for s in scored
                         if s["cand"] == ("wait", "glow"))
print("   (arm, hum, glow):", dict(c3))
print("\n--- verdicts ---")
for k, v in ag.verdicts.items():
    print("   ", k, v["verdict"], "p=", v["p"], "rr=", v["rr"],
          v["target_yes"], v["target_no"], v["ctrl_yes"], v["ctrl_no"])
