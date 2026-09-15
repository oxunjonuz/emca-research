"""run_life_v9.py -- single-life runner for the V9 transplant (turn 133).

The runner is a copy of run_life_v7.py with ONE change: the arm table comes from
agent_emca_v9 and the log carries two extra fields the union's verdicts read
(`probe_keys`, `n_skipped_not_probeable`). The world construction, the death
handling, the respawn seed arithmetic and the affordability gate are BYTE-FOR-
BYTE the v7 logic, so that the v7 arm carried through this runner must reproduce
the frozen v7 cell exactly (prereg V9 §2, the internal transplant control).

Usage: python3 run_life_v9.py <arm> <seed> [steps] [truth] [rich] [decoy]
Writes results/matrix_v9/<arm>_<seed>_<truth>_<rich>_<decoy>.json
"""
import json
import os
import sys

from env_terrarium_v7 import TerrariumV7, pick_edge_action
from agent_emca_v9 import ARMS, NONMOVE

STEPS = 16000


def make_agent(arm, seed, edge_action):
    cls = ARMS[arm]
    if arm in ("v9_oracle", "v9_oldoracle"):
        return cls(seed, edge=(edge_action, "hum"))
    return cls(seed)


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
           "fruits_eaten": 0}
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
            acc["rich_steps"] = acc.get("rich_steps", 0) + 1
        if info.get("died"):
            log["deaths"] += 1
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
    # --- the two v9-only log fields -------------------------------------
    log["probe_keys"] = getattr(agent, "probe_keys", [])
    log["n_skipped_not_probeable"] = getattr(agent,
                                             "n_skipped_not_probeable", 0)
    log["n_explore_picks"] = getattr(agent, "n_explore_picks", 0)
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
    d = os.path.join(here, "results", "matrix_v9")
    os.makedirs(d, exist_ok=True)
    tag = (f"{arm}_{seed}_{'on' if truth else 'off'}_{rich}_"
           f"{'on' if decoy else 'off'}")
    path = os.path.join(d, f"{tag}.json")
    with open(path, "w") as f:
        f.write(json.dumps(log, indent=1))
    print(json.dumps({k: v for k, v in log.items()
                      if k != "candidates_seen"}, indent=1))
    print("WROTE", path)


if __name__ == "__main__":
    main()
