"""Diagnostic: run the prober once, dump the probe trial trace + verdict.
Goal: verify the patch-clearing loop now works (trials AT the altar with
an EMPTY patch). Criterion: >= 30 target-waits at (7,2) with empty patch,
verdict computed on real sprout data. This is a one-shot diagnostic, not
a matrix run."""
from collections import Counter

from run_life_v32 import make_agent
from env_terrarium_v32 import TerrariumV32

ag = make_agent('prober', 1)
env = TerrariumV32(1)
c = Counter()
seq = []
for t in range(8000):
    o = env.obs()
    a = ag.act(o)
    if ag.probe_state is not None and ag.probe_state['phase'] == 'trial':
        c[(tuple(env.pos), a, env.patch_berry)] += 1
        if len(seq) < 30:
            seq.append((t, tuple(env.pos), a, env.patch_berry))
    o2, r, done, info = env.step(a)
    ag.observe(o, a, r, o2, done, info)
    if done:
        env = TerrariumV32(1001 + t)

print("trial (pos, action, patch_loaded) counts:")
for k, v in c.most_common(10):
    print("  ", k, v)
print("first 30 trial steps:")
for s in seq:
    print("  ", s)
print("verdicts:", ag.verdicts)
tw = sum(v for k, v in c.items() if k[0] == (7, 2) and k[1] == 'wait' and not k[2])
cw = sum(v for k, v in c.items() if k[0] == (7, 2) and k[1] == 'grasp' and not k[2])
print(f"target-waits at altar, empty patch: {tw}")
print(f"ctrl-grasps at altar, empty patch: {cw}")
