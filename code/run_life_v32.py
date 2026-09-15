"""Single-life runner for TerrariumV32 (separated geometry + altar).

Usage: python3 run_life_v32.py <condition> <seed> [steps]
Conditions:
  emca_v21      - pooled identifier + v3.2 goals -- BELIEVES the decoy
  emca_v22      - spec-gated identifier + v3.2 goals -- BELIEVES the decoy
  emca_v25c     - stratified RR identifier + v3.2 goals -- REJECTS the decoy
  emca_nocausal - assoc-only + v3.2 goals -- BELIEVES (correlation)
  prober        - v2.5c + do-interventions (gray-zone active experiments)
  curious_pure  - v2.5c + REACHABLE pure novelty (turn-100 correction)
  curious_surv  - v2.5c + novelty + survival arbiter + storm competence
  random / qlearn / ngram - baselines
Writes results/matrix_v32/<condition>_<seed>.json
"""
import json
import os
import sys

from env_terrarium_v32 import TerrariumV32
from agent_emca_v2 import EMCA
from agent_emca_v32 import (
    AgentV32, AgentV32Pooled, AgentV32Spec, AgentV32Assoc,
    AgentV32Prober, AgentCuriousPure, AgentCuriousSurvivor,
)
from baselines import RandomAgent, QAgent, NGramAgent

STEPS = 16000
RESET_AT = 4500
FLIP_AT = 3000
DECOY = ("grasp", "bell_rang")
ALTAR_EDGE = ("wait", "patch_berry")
TRUE_EDGES = [("press", "lever"), ("eat", "ate"), ("grasp", "tree_gather")]


def make_agent(condition, seed):
    kw = dict(seed=seed)
    if condition == "emca_v21":
        return AgentV32Pooled(**kw)
    if condition == "emca_v22":
        return AgentV32Spec(**kw)
    if condition == "emca_v25c":
        return AgentV32(**kw)
    if condition == "emca_nocausal":
        return AgentV32Assoc(**kw)
    if condition == "prober":
        return AgentV32Prober(**kw)
    if condition == "curious_pure":
        return AgentCuriousPure(**kw)
    if condition == "curious_surv":
        return AgentCuriousSurvivor(**kw)
    if condition == "random":
        return RandomAgent(**kw)
    if condition == "qlearn":
        return QAgent(**kw)
    if condition == "ngram":
        return NGramAgent(**kw)
    raise ValueError(condition)


def run(condition, seed, steps=STEPS):
    agent = make_agent(condition, seed)
    env = TerrariumV32(seed, regime_flip_at=FLIP_AT)
    log = {
        "condition": condition, "seed": seed, "steps": steps,
        "env": "TerrariumV32", "regime_flip_at": FLIP_AT, "reset_at": None,
        "total_reward": 0.0, "deaths": 0, "berries_eaten": 0,
        "tree_fruits": 0, "keys_picked": 0, "lever_presses": 0,
        "treasures": 0, "storm_duty": 0.0, "chimes_collected": 0,
        "grasp_attempts": 0, "grasp_at_bell": 0, "grasp_costs_paid": 0.0,
        "patch_sprouts_seen": 0, "patch_ate": 0, "altar_visits": 0,
        "waits_at_altar": 0, "far_zone_steps": 0,
        "novelty_transitions": None,
        "goals_generated": 0, "goals_achieved": 0,
        "goals_by_kind": {},
        "causal_edges": [], "assoc_edges": [], "assoc_edges_p002": [],
        "identifier_version": None,
        "decoy_in_causal": None, "decoy_in_assoc": None,
        "altar_edge_in_causal": None,
        "true_in_causal": {},
        "probe_verdicts": None, "probe_trials": None,
        "harness_notes": [],
    }
    prev_pos = None
    for t in range(steps):
        o = env.obs()
        a = agent.act(o)
        o2, r, done, info = env.step(a)
        agent.observe(o, a, r, o2, done, info)
        log["total_reward"] += r
        if a == "grasp":
            log["grasp_attempts"] += 1
            if abs(env.pos[0] - 1) + abs(env.pos[1] - 3) <= 2:
                log["grasp_at_bell"] += 1
        if info.get("died"):
            log["deaths"] += 1
            env = TerrariumV32(seed + 1000 + t, regime_flip_at=FLIP_AT + t + 1)
        if info.get("ate"):
            log["berries_eaten"] += 1
        if info.get("patch_ate"):
            log["patch_ate"] += 1
        if info.get("patch_berry"):
            log["patch_sprouts_seen"] += 1
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
        if a == "wait" and tuple(env.pos) == (7, 2):
            log["waits_at_altar"] += 1
        if env.pos[0] >= 5:
            log["far_zone_steps"] += 1
        if a is None:
            log["harness_notes"].append(f"t={t}: agent returned None")
    log["storm_duty"] = round(env.storm_steps / max(1, env.t), 3)
    log["grasp_costs_paid"] = round(env.grasp_costs_paid * 0.6, 1)

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
        log["altar_edge_in_causal"] = ALTAR_EDGE in causal
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
    if hasattr(agent, "verdicts"):
        log["probe_verdicts"] = {f"{a}->{e}": v for (a, e), v
                                 in agent.verdicts.items()}
        log["probe_trials"] = {f"{a}->{e}": dict(v) for (a, e), v
                               in agent.probe_log.items()}
    if hasattr(agent, "trans_counts"):
        log["novelty_transitions"] = sum(
            sum(c.values()) for c in agent.trans_counts.values())
    return log


def main():
    condition = sys.argv[1]
    seed = int(sys.argv[2])
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else STEPS
    log = run(condition, seed, steps)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "results", "matrix_v32"), exist_ok=True)
    path = os.path.join(here, "results", "matrix_v32",
                        f"{condition}_{seed}.json")
    with open(path, "w") as f:
        json.dump(log, f, indent=1)
    print(json.dumps(log, indent=1))
    print("WROTE", path)


if __name__ == "__main__":
    main()
