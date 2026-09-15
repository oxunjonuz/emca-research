"""run_life_v7.py -- single-life runner for TerrariumV7.

PERSISTENCE (the point of the claims): when the world kills the agent,
the RUNNER respawns a FRESH world and keeps the SAME agent object --
its tables, candidates and verdicts survive. This is what lets C3's
verdicts accumulate data across deaths and C1's decision be observed
over a whole life.

Usage: python3 run_life_v7.py <arm> <seed> [steps] [truth] [rich] [decoy]
  arms: v7_full v7_beta0 v7_perm v7_nogen v7_oracle v7_forager v7_random
Writes results/matrix_v7/<arm>_<seed>_<truth>_<rich>_<decoy>.json
"""
import json
import os
import sys

from env_terrarium_v7 import TerrariumV7, pick_edge_action
from agent_emca_v7 import (
    AgentV7Full, AgentV7Beta0, AgentV7Perm, AgentV7NoGen, AgentV7Oracle,
    AgentV7Forager, AgentV7Random, NONMOVE,
)

STEPS = 16000


def make_agent(arm, seed, edge_action):
    if arm == "v7_full":
        return AgentV7Full(seed)
    if arm == "v7_beta0":
        return AgentV7Beta0(seed)
    if arm == "v7_perm":
        return AgentV7Perm(seed)
    if arm == "v7_nogen":
        return AgentV7NoGen(seed)
    if arm == "v7_oracle":
        return AgentV7Oracle(seed, edge=(edge_action, "hum"))
    if arm == "v7_forager":
        return AgentV7Forager(seed)
    if arm == "v7_random":
        return AgentV7Random(seed)
    raise ValueError(arm)


def run(arm, seed, steps=STEPS, truth=True, rich="low", decoy=True):
    edge_action = pick_edge_action(seed)
    agent = make_agent(arm, seed, edge_action)
    env = TerrariumV7(seed, truth=truth, decoy=decoy, rich=rich,
                      edge_action=edge_action)
    log = {
        "arm": arm, "seed": seed, "steps": steps, "truth": truth,
        "rich": rich, "decoy": decoy, "edge_action": edge_action,
        "decoy_action": env.decoy_action,
        "total_reward": 0.0, "deaths": 0, "fruits_eaten": 0,
        "fruit_blooms": 0, "hums": 0, "glows": 0, "aura_steps": 0,
        "rich_steps": 0, "probe_trials": 0, "probe_blocks": 0,
        "candidates_seen": [], "n_candidates_total": 0,
        "verdicts": {}, "rich_rate_obs": 0.0,
        "harness_notes": [],
    }
    acc = {"hums": 0, "glows": 0, "aura_steps": 0, "fruit_blooms": 0,
           "fruits_eaten": 0, "rich_steps": 0}
    for t in range(steps):
        o = env.obs()
        a = agent.act(o)
        if a not in o["afford"]:
            log["harness_notes"].append(f"t={t}: unaffordable {a}")
            a = "wait" if "wait" in o["afford"] else o["afford"][0]
        o2, r, done, info = env.step(a)
        agent.observe(o, a, r, o2, done, info)
        log["total_reward"] += r
        if a in NONMOVE and o["pos"] == (2, 8):
            acc["rich_steps"] += 1
        if info.get("died"):
            log["deaths"] += 1
            # fold the dying world's counters into the accumulator BEFORE
            # respawning (turn-120 fix: the earlier version read only the
            # last env's counters, so blooms/aura_steps were wrong on any
            # multi-death run)
            acc["hums"] += env.hums
            acc["glows"] += env.glows
            acc["aura_steps"] += env.aura_steps
            acc["fruit_blooms"] += env.fruit_blooms
            acc["fruits_eaten"] += env.fruits_eaten
            env = TerrariumV7(seed + 1000 + t, truth=truth, decoy=decoy,
                              rich=rich, edge_action=edge_action)
    acc["hums"] += env.hums
    acc["glows"] += env.glows
    acc["aura_steps"] += env.aura_steps
    acc["fruit_blooms"] += env.fruit_blooms
    acc["fruits_eaten"] += env.fruits_eaten
    log["hums"] = acc["hums"]
    log["glows"] = acc["glows"]
    log["aura_steps"] = acc["aura_steps"]
    log["fruit_blooms"] = acc["fruit_blooms"]
    log["fruits_eaten"] = acc["fruits_eaten"]
    log["rich_steps"] = acc["rich_steps"]
    log["probe_trials"] = getattr(agent, "probe_trials", 0)
    log["probe_blocks"] = getattr(agent, "probe_blocks_done", 0)
    log["candidates_seen"] = getattr(agent, "candidates_seen", [])
    log["n_candidates_total"] = getattr(agent, "n_candidates_total", 0)
    log["verdicts"] = {f"{a}->{e}": v
                       for (a, e), v in getattr(agent, "verdicts", {}).items()}
    log["rich_rate_obs"] = round(getattr(agent, "rich_rate_obs", 0.0), 4)
    log["first_probe"] = getattr(agent, "first_probe", None)
    log["ranked_at_first_probe"] = getattr(agent, "ranked_at_first_probe", None)
    log["probe_order_log"] = getattr(agent, "probe_order_log", [])
    log["first_causal_t"] = getattr(agent, "first_causal_t", None)
    log["deaths_agent"] = getattr(agent, "deaths", 0)
    return log


def main():
    arm = sys.argv[1]
    seed = int(sys.argv[2])
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else STEPS
    truth = (sys.argv[4] != "off") if len(sys.argv) > 4 else True
    rich = sys.argv[5] if len(sys.argv) > 5 else "low"
    decoy = (sys.argv[6] != "off") if len(sys.argv) > 6 else True
    log = run(arm, seed, steps, truth, rich, decoy)
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(here, "results", "matrix_v7")
    os.makedirs(d, exist_ok=True)
    tag = f"{arm}_{seed}_{'on' if truth else 'off'}_{rich}_{'on' if decoy else 'off'}"
    path = os.path.join(d, f"{tag}.json")
    with open(path, "w") as f:
        f.write(json.dumps(log, indent=1))
    print(json.dumps({k: v for k, v in log.items()
                      if k != "candidates_seen"}, indent=1))
    print("WROTE", path)


if __name__ == "__main__":
    main()