"""Single-life runner for TerrariumV5 (the true-edge-value world).
Usage: python3 run_life_v5.py <condition> <seed> [steps]
Conditions:
  v5_believer - pooled v2.1
  v5_spec     - spec-gated v2.2
  v5_assoc    - assoc-only, threshold 0.5 (structurally blind)
  v5_assoc02  - assoc-only, threshold 0.02 (permissive control)
  v5_rejector - stratified v2.5c
  random / qlearn / ngram - baselines
Writes results/matrix_v5/<condition>_<seed>.json

Harness notes (the v4 lessons, kept):
  * the env's pocket counters (scorch, grasps_near_torch, near_trap,
    spring flows/fills/waits/aura) are PER-ENV lifetime counters -- a
    respawn resets them, so the runner accumulates them EVERY step;
  * the agent's identifier snapshot is taken at the END of the life
    (the edge sets the arm acted on all along; the per-step edge
    history is not needed for the preregistered verdicts).
"""
import json
import os
import sys

from env_terrarium_v5 import TerrariumV5
from agent_emca_v2 import EMCA
from agent_emca_v5 import (
    AgentV5Pooled, AgentV5Spec, AgentV5Assoc, AgentV5Assoc02, AgentV5,
)
from baselines import RandomAgent, QAgent, NGramAgent

STEPS = 16000
FLIP_AT = 3000
DECOY_TORCH = ("grasp", "torch_lit")
DECOY_BELL = ("grasp", "bell_rang")
TRUE_EDGES = [("press", "lever"), ("eat", "ate"), ("grasp", "tree_gather"),
              ("eat", "treasury_ate")]
SPRING_EDGE = ("wait", "spring_flow")


def make_agent(condition, seed):
    kw = dict(seed=seed)
    if condition == "v5_believer":
        return AgentV5Pooled(**kw)
    if condition == "v5_spec":
        return AgentV5Spec(**kw)
    if condition == "v5_assoc":
        return AgentV5Assoc(**kw)
    if condition == "v5_assoc02":
        return AgentV5Assoc02(**kw)
    if condition == "v5_rejector":
        return AgentV5(**kw)
    if condition == "random":
        return RandomAgent(**kw)
    if condition == "qlearn":
        return QAgent(**kw)
    if condition == "ngram":
        return NGramAgent(**kw)
    raise ValueError(condition)


def _blank_log(condition, seed, steps):
    return {
        "condition": condition, "seed": seed, "steps": steps,
        "env": "TerrariumV5", "regime_flip_at": FLIP_AT,
        "total_reward": 0.0, "deaths": 0, "berries_eaten": 0,
        "tree_fruits": 0, "keys_picked": 0, "lever_presses": 0,
        "treasures": 0, "chimes_collected": 0,
        "grasp_attempts": 0, "grasp_costs_paid": 0.0,
        "torches_collected": 0, "treasury_eaten": 0,
        "scorch_paid": 0.0, "scorch_steps": 0,
        "grasps_near_torch": 0, "near_trap_steps": 0,
        "torch_goal_steps": 0, "lotus_goal_steps": 0,
        "lotus_eaten": 0, "spring_flows": 0, "pool_fills": 0,
        "waits_in_aura": 0, "aura_steps": 0,
        "goals_generated": 0, "goals_achieved": 0, "goals_by_kind": {},
        "causal_edges": [], "assoc_edges": [], "assoc_edges_p002": [],
        "identifier_version": None,
        "decoy_torch_in_causal": None, "decoy_torch_in_assoc": None,
        "decoy_bell_in_causal": None,
        "spring_in_causal": None, "spring_in_assoc": None,
        "spring_in_assoc002": None,
        "true_in_causal": {},
        "harness_notes": [],
    }


def run(condition, seed, steps=STEPS):
    agent = make_agent(condition, seed)
    env = TerrariumV5(seed, regime_flip_at=FLIP_AT)
    log = _blank_log(condition, seed, steps)
    g_acc = 0.0
    gnt_acc = 0
    nts_acc = 0
    gc_acc = 0.0
    flows = fills = waits = aura = 0
    for t in range(steps):
        o = env.obs()
        a = agent.act(o)
        ag = getattr(agent, "active_goal", None)
        if ag is not None and agent.goals.get(ag, {}).get("target") \
                == "torch_bank":
            log["torch_goal_steps"] += 1
        if ag is not None and agent.goals.get(ag, {}).get("target") \
                == "lotus_bloom":
            log["lotus_goal_steps"] += 1
        o2, r, done, info = env.step(a)
        agent.observe(o, a, r, o2, done, info)
        log["total_reward"] += r
        # per-step accumulation (respawn resets the env's counters)
        gnt_acc += env.grasps_near_torch
        nts_acc += env.near_trap_steps
        env.grasps_near_torch = 0
        env.near_trap_steps = 0
        flows += env.spring_flows
        fills += env.pool_fills
        waits += env.waits_in_aura
        aura += env.aura_steps
        env.spring_flows = 0
        env.pool_fills = 0
        env.waits_in_aura = 0
        env.aura_steps = 0
        if info.get("died"):
            g_acc += env.scorch_paid
            gc_acc += env.grasp_costs_paid
            log["deaths"] += 1
            env = TerrariumV5(seed + 1000 + t, regime_flip_at=FLIP_AT + t + 1)
        if info.get("ate"):
            log["berries_eaten"] += 1
        if info.get("tree_gather") or info.get("tree_ate"):
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
        if info.get("lotus"):
            log["lotus_eaten"] += 1
        if a == "grasp":
            log["grasp_attempts"] += 1
        if a is None:
            log["harness_notes"].append(f"t={t}: agent returned None")
    log["scorch_paid"] = round(g_acc + env.scorch_paid, 1)
    log["grasp_costs_paid"] = round(gc_acc + env.grasp_costs_paid, 1)
    log["grasps_near_torch"] = gnt_acc
    log["near_trap_steps"] = nts_acc
    log["spring_flows"] = flows
    log["pool_fills"] = fills
    log["waits_in_aura"] = waits
    log["aura_steps"] = aura
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
        log["decoy_torch_in_assoc"] = DECOY_TORCH in agent.assoc_edges(
            min_n=3, min_p=0.02)
        log["decoy_bell_in_causal"] = DECOY_BELL in causal
        log["spring_in_causal"] = SPRING_EDGE in causal
        log["spring_in_assoc"] = SPRING_EDGE in agent.assoc_edges()
        log["spring_in_assoc002"] = SPRING_EDGE in agent.assoc_edges(
            min_n=3, min_p=0.02)
        log["true_in_causal"] = {f"{a}->{e}": (a, e) in causal
                                 for a, e in TRUE_EDGES}
        log["goals_generated"] = len(agent.goals)
        log["goals_achieved"] = sum(1 for g in agent.goals.values()
                                    if g["status"] == "achieved")
        gk = {}
        for g in agent.goals.values():
            gk[g["kind"]] = gk.get(g["kind"], 0) + 1
        log["goals_by_kind"] = gk
    return log


def main():
    condition = sys.argv[1]
    seed = int(sys.argv[2])
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else STEPS
    log = run(condition, seed, steps)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "results", "matrix_v5"), exist_ok=True)
    path = os.path.join(here, "results", "matrix_v5",
                        f"{condition}_{seed}.json")
    with open(path, "w") as f:
        json.dump(log, f, indent=1)
    print(json.dumps(log, indent=1))
    print("WROTE", path)


if __name__ == "__main__":
    main()
