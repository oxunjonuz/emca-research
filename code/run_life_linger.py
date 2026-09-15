"""Single-life runner for TerrariumLinger (the simple trap-only env).

Usage: python3 run_life_linger.py <condition> <seed> [steps]
Conditions:
  emca_v21    - EMCA v2.1 (pooled contrast, spec gate OFF) -- the OLD way
  emca_v22    - EMCA v2.2 (pooled + specificity gate) -- the v2-matrix way
  emca_v25c   - EMCA v2.5c (stratified contrast + RR>=2 + door_gone data
                fix) -- the NEW way of thinking (turn 97, run 7)
  emca_nocausal - assoc-only control (what correlation alone asserts)
  random / qlearn / ngram - baselines
Writes results/matrix_linger/<condition>_<seed>.json

The agent files are reused WITHOUT modification (agent_emca_v2.EMCA for
v2.1/v2.2, sanity_stratified3.AgentV25c for v2.5c). Identifier version is
recorded in every log (TZ.md rule: never silently mix identifier versions).
"""
import json
import os
import sys

from env_linger import TerrariumLinger
from agent_emca_v2 import EMCA, view_features
from baselines import RandomAgent, QAgent, NGramAgent
from sanity_stratified3 import AgentV25c

STEPS = 16000
DECOY = ("eat", "bell_rang")
TRUE_EDGES = [("eat", "ate"), ("eat", "tree_ate")]


def make_agent(condition, seed):
    kw = dict(seed=seed)
    if condition == "emca_v21":
        return EMCA(spec_cap=None, **kw)
    if condition == "emca_v22":
        return EMCA(spec_cap=0.10, **kw)
    if condition == "emca_v25c":
        return AgentV25c(**kw)
    if condition == "emca_nocausal":
        return EMCA(use_causal=False, **kw)
    if condition == "random":
        return RandomAgent(**kw)
    if condition == "qlearn":
        return QAgent(**kw)
    if condition == "ngram":
        return NGramAgent(**kw)
    raise ValueError(condition)


def run(condition, seed, steps=STEPS):
    agent = make_agent(condition, seed)
    env = TerrariumLinger(seed)
    log = {
        "condition": condition, "seed": seed, "steps": steps,
        "env": "TerrariumLinger",
        "total_reward": 0.0, "deaths": 0, "berries_eaten": 0,
        "tree_fruits": 0, "storm_duty": 0.0,
        "ring_near_tree": None, "ring_far": None,
        "causal_edges": [], "assoc_edges": [],
        "identifier_version": None,
        "decoy_in_causal": None, "decoy_in_assoc": None,
        "true_in_causal": {},
        "harness_notes": [],
    }
    near_r = near_n = far_r = far_n = 0
    for t in range(steps):
        o = env.obs()
        a = agent.act(o)
        o2, r, done, info = env.step(a)
        agent.observe(o, a, r, o2, done, info)
        log["total_reward"] += r
        if info.get("died"):
            log["deaths"] += 1
            env = TerrariumLinger(seed + 1000 + t)
        if info.get("ate"):
            log["berries_eaten"] += 1
        if info.get("tree_ate"):
            log["tree_fruits"] += 1
        if env.tree:
            d = abs(env.pos[0] - env.tree[0]) + abs(env.pos[1] - env.tree[1])
            if d <= 1:
                near_n += 1
                near_r += 1 if info.get("bell_rang") else 0
            else:
                far_n += 1
                far_r += 1 if info.get("bell_rang") else 0
        if a is None:
            log["harness_notes"].append(f"t={t}: agent returned None")
    log["storm_duty"] = round(env.storm_steps / max(1, env.t), 3)
    log["ring_near_tree"] = round(near_r / max(1, near_n), 3)
    log["ring_far"] = round(far_r / max(1, far_n), 3)

    if isinstance(agent, EMCA):
        log["identifier_version"] = agent.identifier_version
        causal = agent.causal_edges()
        log["causal_edges"] = [[a, e, round(p, 3)] for (a, e), p in causal.items()]
        log["assoc_edges"] = [[a, e, round(p, 3)] for (a, e), p in
                              agent.assoc_edges().items()]
        # analysis view at the sanity-calibrated threshold: the decoy rate is
        # ~0.26, invisible at the agent-behaviour default min_p=0.5. The
        # "correlation fooled" criterion needs the co-occurrence rate at the
        # same threshold the sanity runs used (min_p=0.02) -- measurement fix,
        # documented; the agent's OWN planning still uses the default arm.
        log["assoc_edges_p002"] = [[a, e, round(p, 3)] for (a, e), p in
                                   agent.assoc_edges(min_n=3, min_p=0.02).items()]
        log["decoy_in_causal"] = DECOY in causal
        log["decoy_in_assoc"] = DECOY in agent.assoc_edges(min_n=3, min_p=0.02)
        log["true_in_causal"] = {f"{a}->{e}": (a, e) in causal
                                 for a, e in TRUE_EDGES}
    return log


def main():
    condition = sys.argv[1]
    seed = int(sys.argv[2])
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else STEPS
    log = run(condition, seed, steps)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "results", "matrix_linger"), exist_ok=True)
    path = os.path.join(here, "results", "matrix_linger",
                        f"{condition}_{seed}.json")
    with open(path, "w") as f:
        json.dump(log, f, indent=1)
    print(json.dumps(log, indent=1))
    print("WROTE", path)


if __name__ == "__main__":
    main()
