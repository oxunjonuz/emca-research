"""Single-life runner for TerrariumV31 (the actionable-decoy env).

Usage: python3 run_life_v31.py <condition> <seed> [steps]
Conditions:
  emca_v21      - pooled contrast (spec OFF) + v3.1 goals -- believes decoy
  emca_v22      - pooled + specificity gate + v3.1 goals -- believes decoy
  emca_v25c     - stratified RR + v3.1 goals -- rejects decoy
  emca_nocausal - assoc-only + v3.1 goals -- believes decoy (correlation)
  curious       - v2.5c identifier + novelty generator (direction 3)
  random / qlearn / ngram - baselines
Writes results/matrix_v31/<condition>_<seed>.json
"""
import json
import os
import sys

from env_terrarium_v31 import TerrariumV31
from agent_emca_v2 import EMCA
from agent_emca_v31 import (
    AgentV31, AgentV31Pooled, AgentV31Spec, AgentV31Assoc, AgentCurious,
)
from baselines import RandomAgent, QAgent, NGramAgent

STEPS = 16000
RESET_AT = 4500
FLIP_AT = 3000
DECOY = ("grasp", "bell_rang")
TRUE_EDGES = [("press", "lever"), ("eat", "ate"), ("grasp", "tree_gather")]


def make_agent(condition, seed):
    kw = dict(seed=seed)
    if condition == "emca_v21":
        return AgentV31Pooled(**kw)
    if condition == "emca_v22":
        return AgentV31Spec(**kw)
    if condition == "emca_v25c":
        return AgentV31(**kw)
    if condition == "emca_nocausal":
        return AgentV31Assoc(**kw)
    if condition == "curious":
        return AgentCurious(**kw)
    if condition == "random":
        return RandomAgent(**kw)
    if condition == "qlearn":
        return QAgent(**kw)
    if condition == "ngram":
        return NGramAgent(**kw)
    raise ValueError(condition)


def run(condition, seed, steps=STEPS):
    agent = make_agent(condition, seed)
    env = TerrariumV31(seed, regime_flip_at=FLIP_AT)
    log = {
        "condition": condition, "seed": seed, "steps": steps,
        "env": "TerrariumV31", "regime_flip_at": FLIP_AT, "reset_at": None,
        "total_reward": 0.0, "deaths": 0, "berries_eaten": 0,
        "tree_fruits": 0, "keys_picked": 0, "lever_presses": 0,
        "treasures": 0, "storm_duty": 0.0, "chimes_collected": 0,
        "grasp_attempts": 0, "grasp_at_bell": 0,
        "ring_near_storm_tree": None,
        "goals_generated": 0, "goals_achieved": 0,
        "goals_by_kind": {},
        "causal_edges": [], "assoc_edges": [], "assoc_edges_p002": [],
        "identifier_version": None,
        "decoy_in_causal": None, "decoy_in_assoc": None,
        "true_in_causal": {},
        "harness_notes": [],
    }
    near_r = near_n = 0
    win = 500
    bell_zone = lambda p: abs(p[0] - 1) + abs(p[1] - 3) <= 2
    for t in range(steps):
        o = env.obs()
        a = agent.act(o)
        o2, r, done, info = env.step(a)
        agent.observe(o, a, r, o2, done, info)
        log["total_reward"] += r
        if a == "grasp":
            log["grasp_attempts"] += 1
            if bell_zone(env.pos):
                log["grasp_at_bell"] += 1
        if info.get("died"):
            log["deaths"] += 1
            env = TerrariumV31(seed + 1000 + t, regime_flip_at=FLIP_AT + t + 1)
        if info.get("ate"):
            log["berries_eaten"] += 1
        if info.get("tree_gather"):
            log["tree_fruits"] += 1
        if info.get("chime"):
            log["chimes_collected"] += 1
        if info.get("lever"):
            log["lever_presses"] += 1
        if info.get("treasure"):
            log["treasures"] += 1
        if info.get("key"):
            log["keys_picked"] += 1
        if env.tree and env.weather == "storm":
            d = abs(env.pos[0] - env.tree[0]) + abs(env.pos[1] - env.tree[1])
            if d <= 1:
                near_n += 1
                near_r += 1 if info.get("bell_rang") else 0
        if a is None:
            log["harness_notes"].append(f"t={t}: agent returned None")
    log["storm_duty"] = round(env.storm_steps / max(1, env.t), 3)
    log["ring_near_storm_tree"] = round(near_r / max(1, near_n), 3)

    if isinstance(agent, EMCA):
        log["identifier_version"] = agent.identifier_version
        causal = agent.causal_edges()
        log["causal_edges"] = [[a, e, round(p, 3)] for (a, e), p in causal.items()]
        log["assoc_edges"] = [[a, e, round(p, 3)] for (a, e), p in
                              agent.assoc_edges().items()]
        log["assoc_edges_p002"] = [[a, e, round(p, 3)] for (a, e), p in
                                   agent.assoc_edges(min_n=3, min_p=0.02).items()]
        log["decoy_in_causal"] = DECOY in causal
        log["decoy_in_assoc"] = DECOY in agent.assoc_edges(min_n=3, min_p=0.02)
        log["true_in_causal"] = {f"{a}->{e}": (a, e) in causal
                                 for a, e in TRUE_EDGES}
        log["goals_generated"] = len(agent.goals)
        log["goals_achieved"] = sum(1 for g in agent.goals.values()
                                    if g["status"] == "achieved")
        gk = {}
        for g in agent.goals.values():
            gk[g["kind"]] = gk.get(g["kind"], 0) + 1
        log["goals_by_kind"] = gk
        log["self_model"] = {k: list(v) for k, v in agent.self_model.items()}
    return log


def main():
    condition = sys.argv[1]
    seed = int(sys.argv[2])
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else STEPS
    log = run(condition, seed, steps)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "results", "matrix_v31"), exist_ok=True)
    path = os.path.join(here, "results", "matrix_v31",
                        f"{condition}_{seed}.json")
    with open(path, "w") as f:
        json.dump(log, f, indent=1)
    print(json.dumps(log, indent=1))
    print("WROTE", path)


if __name__ == "__main__":
    main()
