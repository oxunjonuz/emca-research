"""Where does the seed-2 rejector wander during its 3 lotus goals?"""
from collections import Counter
from env_terrarium_v5 import TerrariumV5
from agent_emca_v5 import AgentV5, view_features5

for seed in (2, 3):
    ag = AgentV5(seed=seed)
    env = TerrariumV5(seed, regime_flip_at=3000)
    pos_c = Counter()
    for t in range(8000):
        o = env.obs()
        f = view_features5(o)
        goal = ag.goals.get(ag.active_goal) if ag.active_goal else None
        if goal is not None and goal.get("target") == "lotus_bloom":
            pos_c[tuple(env.pos)] += 1
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = TerrariumV5(seed + 1000 + t, regime_flip_at=3000 + t + 1)
    top = pos_c.most_common(8)
    print(f"seed {seed}: distinct positions={len(pos_c)} total={sum(pos_c.values())}")
    print("  top:", top)
    # where is the spring?
    e0 = TerrariumV5(seed, regime_flip_at=3000)
    print("  spring pos:", e0.spring_pos, "agent spawn:", e0.pos)
