"""Where exactly does the seed-2 lotus navigation lose the scent?
Trace _scent_step_smart calls and their outcomes during a lotus goal."""
from env_terrarium_v5 import TerrariumV5
from agent_emca_v5 import AgentV5, view_features5

ag = AgentV5(seed=2)
env = TerrariumV5(2, regime_flip_at=3000)
trace = []
for t in range(8000):
    o = env.obs()
    f = view_features5(o)
    goal = ag.goals.get(ag.active_goal) if ag.active_goal else None
    if goal is not None and goal.get("target") == "lotus_bloom":
        s = (o.get("scent") or {}).get("spring")
        trace.append((t, tuple(env.pos), s, ag._escape_left if hasattr(ag,'_escape_left') else None))
    a = ag.act(o)
    o2, r, done, info = env.step(a)
    ag.observe(o, a, r, o2, done, info)
    if info.get("died"):
        env = TerrariumV5(2 + 1000 + t, regime_flip_at=3000 + t + 1)
print("total lotus steps:", len(trace))
# print segments: first 5, and around each escape
for x in trace[:5]:
    print(x)
print("...")
# distribution of scent presence
n_scent = sum(1 for _,_,s,_ in trace if s)
print("steps with spring scent present:", n_scent)
# where scent absent
absent = [p for _,p,s,_ in trace if not s]
from collections import Counter
print("top absent-scent positions:", Counter(absent).most_common(6))
