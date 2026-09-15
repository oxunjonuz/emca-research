"""Single-life runner for TerrariumV4 (the epistemic-value world).
Usage: python3 run_life_v4.py <condition> <seed> [steps]
Conditions:
  v4_believer  - pooled v2.1 + v4 torch goals, ARMOUR OFF (decoy ACTIVE)
  v4_spec      - spec-gated v2.2 believer replicate
  v4_assoc     - assoc-only (no causal route; falls to world route)
  v4_rejector  - stratified v2.5c + world-knowledge torch route
  v4_curious   - object-directed novelty (bitter curiosity)
  v4_pure      - pure novelty (the ablation)
  curious_chain - v3.3 chain arm as a v4-world control (scorch naive)
  random / qlearn / ngram - baselines
Writes results/matrix_v4/<condition>_<seed>.json
"""
import json
import os
import sys

from env_terrarium_v4 import TerrariumV4, TRAP_CELL
from agent_emca_v2 import EMCA
from agent_emca_v4 import (
    AgentV4Pooled, AgentV4Spec, AgentV4Assoc, AgentV4,
)
from agent_emca_v4b import AgentV4Curious, AgentV4CuriousPure
from agent_emca_v33 import AgentCuriousChain
from baselines import RandomAgent, QAgent, NGramAgent

STEPS = 16000
FLIP_AT = 3000
DECOY_TORCH = ("grasp", "torch_lit")
DECOY_BELL = ("grasp", "bell_rang")
TRUE_EDGES = [("press", "lever"), ("eat", "ate"), ("grasp", "tree_gather"),
              ("eat", "treasury_ate")]


def make_agent(condition, seed):
    kw = dict(seed=seed)
    if condition == "v4_believer":
        return AgentV4Pooled(**kw)
    if condition == "v4_spec":
        return AgentV4Spec(**kw)
    if condition == "v4_assoc":
        return AgentV4Assoc(**kw)
    if condition == "v4_rejector":
        return AgentV4(**kw)
    if condition == "v4_curious":
        return AgentV4Curious(**kw)
    if condition == "v4_pure":
        return AgentV4CuriousPure(**kw)
    if condition == "curious_chain":
        return AgentCuriousChain(**kw)
    if condition == "random":
        return RandomAgent(**kw)
    if condition == "qlearn":
        return QAgent(**kw)
    if condition == "ngram":
        return NGramAgent(**kw)
    raise ValueError(condition)


def run(condition, seed, steps=STEPS):
    agent = make_agent(condition, seed)
    env = TerrariumV4(seed, regime_flip_at=FLIP_AT)
    log = {
        "condition": condition, "seed": seed, "steps": steps,
        "env": "TerrariumV4", "regime_flip_at": FLIP_AT,
        "total_reward": 0.0, "deaths": 0, "berries_eaten": 0,
        "tree_fruits": 0, "keys_picked": 0, "lever_presses": 0,
        "treasures": 0, "chimes_collected": 0,
        "grasp_attempts": 0, "grasp_costs_paid": 0.0,
        "torches_collected": 0, "treasury_eaten": 0,
        "scorch_paid": 0.0, "scorch_steps": 0,
        "grasps_near_torch": 0, "near_trap_steps": 0,
        "torch_goal_steps": 0,
        "goals_generated": 0, "goals_achieved": 0, "goals_by_kind": {},
        "causal_edges": [], "assoc_edges": [], "assoc_edges_p002": [],
        "identifier_version": None,
        "decoy_torch_in_causal": None, "decoy_torch_in_assoc": None,
        "decoy_bell_in_causal": None,
        "true_in_causal": {},
        "harness_notes": [],
    }
    g_acc = 0.0
    gnt_acc = 0
    nts_acc = 0
    torch_active_last = False
    for t in range(steps):
        o = env.obs()
        a = agent.act(o)
        if hasattr(agent, "active_goal") and agent.active_goal is not None \
                and agent.goals.get(agent.active_goal, {}).get("target") == "torch_bank":
            log["torch_goal_steps"] += 1
            torch_active_last = True
        else:
            torch_active_last = False
        o2, r, done, info = env.step(a)
        agent.observe(o, a, r, o2, done, info)
        log["total_reward"] += r
        # accumulate the per-env pocket counters EVERY step (they are
        # env lifetime counters; a respawn resets them)
        gnt_acc += env.grasps_near_torch
        nts_acc += env.near_trap_steps
        env.grasps_near_torch = 0
        env.near_trap_steps = 0
        if info.get("died"):
            g_acc += env.scorch_paid
            log["deaths"] += 1
            env = TerrariumV4(seed + 1000 + t, regime_flip_at=FLIP_AT + t + 1)
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
        if info.get("torch_collect"):
            log["torches_collected"] += 1
        if info.get("treasury_ate"):
            log["treasury_eaten"] += 1
        if a == "grasp":
            log["grasp_attempts"] += 1
        if a is None:
            log["harness_notes"].append(f"t={t}: agent returned None")
    log["scorch_paid"] = round(g_acc + env.scorch_paid, 1)
    log["grasps_near_torch"] = gnt_acc
    log["near_trap_steps"] = nts_acc
    if isinstance(agent, EMCA):
        log["identifier_version"] = agent.identifier_version
        causal = agent.causal_edges()
        log["causal_edges"] = [[a, e, round(p, 3)]
                               for (a, e), p in causal.items()]
        log["assoc_edges"] = [[a, e, round(p, 3)] for (a, e), p in
                              agent.assoc_edges().items()]
        log["assoc_edges_p002"] = [[a, e, round(p, 3)] for (a, e), p in
                                   agent.assoc_edges(min_n=3, min_p=0.02).items()]
        log["decoy_torch_in_causal"] = DECOY_TORCH in causal
        log["decoy_torch_in_assoc"] = DECOY_TORCH in agent.assoc_edges(min_n=3, min_p=0.02)
        log["decoy_bell_in_causal"] = DECOY_BELL in causal
        log["true_in_causal"] = {f"{a}->{e}": (a, e) in causal
                                 for a, e in TRUE_EDGES}
        log["goals_generated"] = len(agent.goals)
        log["goals_achieved"] = sum(1 for g in agent.goals.values()
                                    if g["status"] == "achieved")
        gk = {}
        for g in agent.goals.values():
            gk[g["kind"]] = gk.get(g["kind"], 0) + 1
        log["goals_by_kind"] = gk
    if hasattr(agent, "interaction_counts"):
        log["interaction_counts"] = dict(agent.interaction_counts)
        log["chain_events"] = dict(agent.chain_events) \
            if hasattr(agent, "chain_events") else {}
    return log


def main():
    condition = sys.argv[1]
    seed = int(sys.argv[2])
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else STEPS
    log = run(condition, seed, steps)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "results", "matrix_v4"), exist_ok=True)
    path = os.path.join(here, "results", "matrix_v4",
                        f"{condition}_{seed}.json")
    with open(path, "w") as f:
        json.dump(log, f, indent=1)
    print(json.dumps(log, indent=1))
    print("WROTE", path)


if __name__ == "__main__":
    main()
