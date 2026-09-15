"""Why does the rejector with the spring edge (2/3 seeds) still not
bloom the lotus? Trace the lotus-plan branch decisions."""
from collections import Counter
from env_terrarium_v5 import TerrariumV5
from agent_emca_v5 import AgentV5, view_features5

for seed in (2, 3):
    ag = AgentV5(seed=seed)
    env = TerrariumV5(seed, regime_flip_at=3000)
    br = Counter()
    for t in range(8000):
        o = env.obs()
        f = view_features5(o)
        goal = ag.goals.get(ag.active_goal) if ag.active_goal else None
        if goal is not None and goal.get("target") == "lotus_bloom" \
                and f.get("spring_near", 0) > 0:
            scent = o.get("scent") or {}
            if f["bell_glow_near"] > 0 or scent.get("bell"):
                br["storm_branch"] += 1
            elif f["energy_low"]:
                br["energy_low"] += 1
            elif o["energy"] >= ag.LOTUS_WAIT_ENERGY:
                br["edge_block"] += 1
            else:
                br["poor(<55)"] += 1
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = TerrariumV5(seed + 1000 + t, regime_flip_at=3000 + t + 1)
    print(f"seed {seed}: branches={dict(br)}")
