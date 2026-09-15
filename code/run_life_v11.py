"""run_life_v11.py -- single-life runner for the WIREHEADING line (turn 140).

Mirrors run_life_v10.py (frozen, untouched): same persistence rule (a death
respawns a FRESH world and keeps the SAME agent), same accumulator folding on
death, same log fields, PYTHONHASHSEED=0.

ADDED: `beacon_rate` and the beacon metrics, and `appraised_rate` (the agent's
own last-appraised alternative rate) so the declared term is auditable from the
frozen JSON rather than from the report.

`world="v10"` builds the FROZEN TerrariumV10 -- that is the path used for the
prereg's identity anchors (n_unarmed == v10 s0_nobrake, n_none == v10
s4_internalized), and no beacon code runs on it at all.

Usage: python3 run_life_v11.py <arm> <seed> [steps] [truth] [rich] [decoy] [world] [beacon_rate]
Writes results/matrix_wirehead_v11/<arm>_<seed>_<truth>_<rich>_<decoy>_<world>_b<rate>.json
"""
import json
import os
import sys

from env_terrarium_v7 import TerrariumV7, pick_edge_action, NONMOVE
from env_safety_v10 import TerrariumV10, Aquifer, COMMONS_START
from env_wirehead_v11 import TerrariumV11, BEACON, in_beacon_field
from agent_wirehead_v11 import make_agent

STEPS = 16000


def fmt_rate(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def run(arm, seed, steps=STEPS, truth=True, rich="low", decoy=True, world="v11",
        beacon_rate=0.0):
    edge_action = pick_edge_action(seed)
    agent = make_agent(arm, seed)
    aq = Aquifer(coupling=0)

    def new_world(seed_):
        if world == "v7":
            return TerrariumV7(seed_, truth=truth, decoy=decoy, rich=rich,
                               edge_action=edge_action)
        if world == "v10":
            return TerrariumV10(seed_, truth=truth, decoy=decoy, rich=rich,
                                edge_action=edge_action, aquifer=aq)
        return TerrariumV11(seed_, truth=truth, decoy=decoy, rich=rich,
                            edge_action=edge_action, aquifer=aq,
                            beacon_rate=beacon_rate)

    env = new_world(seed)
    log = {
        "arm": arm, "seed": seed, "steps": steps, "truth": truth,
        "rich": rich, "decoy": decoy, "world": world,
        "beacon_rate": float(beacon_rate), "beacon": list(BEACON),
        "edge_action": edge_action, "decoy_action": env.decoy_action,
        "total_reward": 0.0, "deaths": 0, "fruits_eaten": 0,
        "fruit_blooms": 0, "hums": 0, "glows": 0, "aura_steps": 0,
        "rich_steps": 0, "probe_trials": 0, "probe_blocks": 0,
        "candidates_seen": [], "n_candidates_total": 0,
        "verdicts": {}, "rich_rate_obs": 0.0, "harness_notes": [],
        "beacon_steps": 0, "beacon_receipt": 0.0, "appraised_rate": 0.0,
    }
    acc = {"hums": 0, "glows": 0, "aura_steps": 0, "fruit_blooms": 0,
           "fruits_eaten": 0, "rich_steps": 0, "beacon_steps": 0,
           "beacon_receipt": 0.0}
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
            acc["hums"] += env.hums
            acc["glows"] += env.glows
            acc["aura_steps"] += env.aura_steps
            acc["fruit_blooms"] += env.fruit_blooms
            acc["fruits_eaten"] += env.fruits_eaten
            acc["beacon_steps"] += getattr(env, "beacon_steps", 0)
            acc["beacon_receipt"] += getattr(env, "beacon_receipt", 0.0)
            env = new_world(seed + 1000 + t)
    acc["hums"] += env.hums
    acc["glows"] += env.glows
    acc["aura_steps"] += env.aura_steps
    acc["fruit_blooms"] += env.fruit_blooms
    acc["fruits_eaten"] += env.fruits_eaten
    acc["beacon_steps"] += getattr(env, "beacon_steps", 0)
    acc["beacon_receipt"] += getattr(env, "beacon_receipt", 0.0)
    log["hums"] = acc["hums"]
    log["glows"] = acc["glows"]
    log["aura_steps"] = acc["aura_steps"]
    log["fruit_blooms"] = acc["fruit_blooms"]
    log["fruits_eaten"] = acc["fruits_eaten"]
    log["rich_steps"] = acc["rich_steps"]
    log["probe_trials"] = getattr(agent, "probe_trials", 0)
    log["probe_blocks"] = getattr(agent, "probe_blocks_done", 0)
    log["verdicts"] = {f"{a}->{e}": v
                       for (a, e), v in getattr(agent, "verdicts", {}).items()}
    log["rich_rate_obs"] = round(getattr(agent, "rich_rate_obs", 0.0), 4)
    log["appraised_rate"] = round(getattr(agent, "appraised_rate", 0.0), 6)
    log["first_probe"] = getattr(agent, "first_probe", None)
    log["first_causal_t"] = getattr(agent, "first_causal_t", None)
    log["deaths_agent"] = getattr(agent, "deaths", 0)
    log["guard_blocks"] = getattr(agent, "guard_blocks", 0)
    log["beacon_steps"] = acc["beacon_steps"]
    log["beacon_receipt"] = round(acc["beacon_receipt"], 4)
    log["commons_left"] = aq.commons
    log["commons_drains"] = aq.drains
    log["keeper_dead"] = aq.keeper_dead
    log["keeper_death_t"] = aq.keeper_death_t
    log["keeper_min_energy"] = round(aq.keeper_min_energy, 3)
    log["vetoed_rich_steps"] = getattr(env, "vetoed_rich_steps", 0)
    return log


def path_for(arm, seed, truth, rich, decoy, world, beacon_rate, outdir):
    ttag = "on" if truth else "off"
    dtag = "on" if decoy else "off"
    return os.path.join(
        outdir,
        f"{arm}_{seed}_{ttag}_{rich}_{dtag}_{world}_b{fmt_rate(beacon_rate)}.json")


def main():
    arm = sys.argv[1]
    seed = int(sys.argv[2])
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else STEPS
    truth = (sys.argv[4] != "off") if len(sys.argv) > 4 else True
    rich = sys.argv[5] if len(sys.argv) > 5 else "low"
    decoy = (sys.argv[6] != "off") if len(sys.argv) > 6 else True
    world = sys.argv[7] if len(sys.argv) > 7 else "v11"
    beacon_rate = float(sys.argv[8]) if len(sys.argv) > 8 else 0.0
    log = run(arm, seed, steps, truth, rich, decoy, world, beacon_rate)
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(here, "results", "matrix_wirehead_v11")
    os.makedirs(d, exist_ok=True)
    with open(path_for(arm, seed, truth, rich, decoy, world, beacon_rate, d),
              "w") as f:
        f.write(json.dumps(log, indent=1, sort_keys=True))
    print(json.dumps({k: v for k, v in log.items()
                      if k != "candidates_seen"}, indent=1))
    print("WROTE", path_for(arm, seed, truth, rich, decoy, world, beacon_rate, d))


if __name__ == "__main__":
    main()
