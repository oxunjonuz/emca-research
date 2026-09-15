"""Diagnose why the in-aura cadence starves in seeds 2/3: trace the
lotus-plan branch decisions step by step for v5_rejector."""
from collections import Counter
from env_terrarium_v5 import TerrariumV5
from agent_emca_v5 import AgentV5, view_features5

for seed in (1, 2):
    ag = AgentV5(seed=seed)
    env = TerrariumV5(seed, regime_flip_at=3000)
    br = Counter()
    energy_in_aura = []
    for t in range(8000):
        o = env.obs()
        f = view_features5(o)
        goal = ag.goals.get(ag.active_goal) if ag.active_goal else None
        if goal is not None and goal.get("target") == "lotus_bloom" \
                and f.get("spring_near", 0) > 0:
            energy_in_aura.append(o["energy"])
            scent = o.get("scent") or {}
            if f["bell_glow_near"] > 0 or scent.get("bell"):
                br["storm_branch"] += 1
            elif f["energy_low"]:
                br["energy_low"] += 1
            elif o["energy"] >= 40:
                br["cadence"] += 1
            else:
                br["too_poor(<40)"] += 1
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if info.get("died"):
            env = TerrariumV5(seed + 1000 + t, regime_flip_at=3000 + t + 1)
    import statistics as st
    print(f"seed {seed}: lotus-in-aura steps={len(energy_in_aura)} "
          f"branches={dict(br)}")
    if energy_in_aura:
        print(f"  energy in aura: mean={st.mean(energy_in_aura):.1f} "
              f"median={st.median(energy_in_aura)} "
              f"min={min(energy_in_aura)} max={max(energy_in_aura)} "
              f"frac>=40={sum(1 for e in energy_in_aura if e>=40)/len(energy_in_aura):.2f}")
