"""Single-life runner for TerrariumV3 (the complex env: v2 world + trap).

Usage: python3 run_life_v3.py <condition> <seed> [steps]
Conditions:
  emca_v21      - pooled contrast (spec OFF) -- the OLD way
  emca_v22      - pooled + specificity gate -- the v2-matrix way
  emca_v25c     - stratified + RR>=2 + door_gone data fix -- the NEW way
  emca_amnesia  - v2.5c + full wipe at reset (E2 control)
  emca_nocausal - assoc-only control
  emca_noepis / emca_nogoals / emca_noself - v2.5c ablations
  random / qlearn / ngram - baselines
Writes results/matrix_v3/<condition>_<seed>.json

Identifier version is recorded in every log (TZ.md rule). The agent files
are reused WITHOUT modification.
"""
import json
import os
import sys

from env_terrarium_v3 import TerrariumV3
from agent_emca_v2 import EMCA, view_features
from baselines import RandomAgent, QAgent, NGramAgent
from sanity_stratified3 import AgentV25c

STEPS = 16000
RESET_AT = 4500
FLIP_AT = 3000
DECOY = ("eat", "bell_rang")
TRUE_EDGES = [("press", "lever"), ("eat", "ate"), ("eat", "tree_ate")]


def make_agent(condition, seed):
    kw = dict(seed=seed)
    if condition == "emca_v21":
        return EMCA(spec_cap=None, **kw)
    if condition == "emca_v22":
        return EMCA(spec_cap=0.10, **kw)
    if condition == "emca_v25c":
        return AgentV25c(**kw)
    if condition == "emca_amnesia":
        ag = AgentV25c(**kw)
        ag.context_reset_at = RESET_AT
        ag.full_wipe = True
        return ag
    if condition == "emca_noepis":
        return AgentV25c(use_episodes=False, **kw)
    if condition == "emca_nogoals":
        return AgentV25c(use_goal_generators=False, **kw)
    if condition == "emca_noself":
        return AgentV25c(use_self_model=False, **kw)
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
    env = TerrariumV3(seed, regime_flip_at=FLIP_AT)
    log = {
        "condition": condition, "seed": seed, "steps": steps,
        "env": "TerrariumV3", "regime_flip_at": FLIP_AT, "reset_at": None,
        "total_reward": 0.0, "deaths": 0, "berries_eaten": 0,
        "tree_fruits": 0, "keys_picked": 0, "lever_presses": 0,
        "treasures": 0, "storm_duty": 0.0,
        "ring_near_storm_tree": None,
        "berries_by_window": {}, "deaths_by_window": {},
        "goals_generated": 0, "goals_achieved": 0,
        "goals_at_reset": [], "goals_active_after_reset": [],
        "causal_edges": [], "assoc_edges": [], "assoc_edges_p002": [],
        "identifier_version": None,
        "decoy_in_causal": None, "decoy_in_assoc": None,
        "true_in_causal": {},
        "harness_notes": [],
    }
    near_r = near_n = 0
    win = 500
    for t in range(steps):
        o = env.obs()
        a = agent.act(o)
        o2, r, done, info = env.step(a)
        agent.observe(o, a, r, o2, done, info)
        log["total_reward"] += r
        if info.get("died"):
            log["deaths"] += 1
            w = str(t // win)
            log["deaths_by_window"][w] = log["deaths_by_window"].get(w, 0) + 1
            env = TerrariumV3(seed + 1000 + t, regime_flip_at=FLIP_AT + t + 1)
        if info.get("ate"):
            log["berries_eaten"] += 1
            w = str(t // win)
            log["berries_by_window"][w] = log["berries_by_window"].get(w, 0) + 1
        if info.get("tree_ate"):
            log["tree_fruits"] += 1
        if info.get("lever"):
            log["lever_presses"] += 1
        if info.get("treasure"):
            log["treasures"] += 1
        if env.has_key and log["keys_picked"] == 0:
            log["keys_picked"] = 1
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
        log["goals_at_reset"] = agent.goals_at_reset
        log["goals_active_after_reset"] = [
            {"id": gid, "kind": g["kind"], "status": g["status"]}
            for gid, g in agent.goals.items() if g["born"] >= RESET_AT]
        log["self_model"] = {k: list(v) for k, v in agent.self_model.items()}
    return log


def main():
    condition = sys.argv[1]
    seed = int(sys.argv[2])
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else STEPS
    log = run(condition, seed, steps)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "results", "matrix_v3"), exist_ok=True)
    path = os.path.join(here, "results", "matrix_v3",
                        f"{condition}_{seed}.json")
    with open(path, "w") as f:
        json.dump(log, f, indent=1)
    print(json.dumps(log, indent=1))
    print("WROTE", path)


if __name__ == "__main__":
    main()
