"""run_life_v12.py -- single-life runner for the FORGER line (turn 141).

Mirrors run_life_v11.py (frozen, untouched): same persistence rule (a death respawns
a FRESH world and keeps the SAME agent), same accumulator folding on death, same log
fields, PYTHONHASHSEED=0.

ADDED: the forger is RUN-SCOPED (created here, handed to every world instance, so
its 2000-step life is run-global), and the log carries its account plus three scores
the hypotheses need and that cannot be recomputed from the frozen JSON afterwards:
  reward_before_forger_death / reward_after_forger_death  (H6)
  reward_after_step_2000                                  (H6)

`world="v10"` builds the FROZEN TerrariumV10 (the anchor path); `world="v11"` builds
the frozen TerrariumV11 (the other anchor path).

Usage: python3 run_life_v12.py <arm> <seed> [steps] [truth] [rich] [decoy] [world]
                                 [place] [tick] [period] [spend_cap]
Writes results/matrix_wirehead_v12/<arm>_<seed>_<truth>_<rich>_<decoy>_<world>_<place>_t<tick>_p<period>_c<cap>.json
"""
import json
import os
import sys

from env_terrarium_v7 import TerrariumV7, pick_edge_action, NONMOVE
from env_safety_v10 import TerrariumV10, Aquifer, COMMONS_START
from env_wirehead_v11 import TerrariumV11, BEACON
from env_wirehead_v12 import TerrariumV12, Forger, FORGER_LIFE_STEPS, PLACE_HOME
from agent_wirehead_v12 import make_agent

STEPS = 16000


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def run(arm, seed, steps=STEPS, truth=True, rich="low", decoy=True, world="v12",
        place="none", tick=0.0, period=1, spend_cap=None):
    edge_action = pick_edge_action(seed)
    agent = make_agent(arm, seed)
    aq = Aquifer(coupling=0)
    forger = None if place in (None, "none") else Forger(place, tick,
                                                         period=period,
                                                         spend_cap=spend_cap)

    def new_world(seed_):
        if world == "v7":
            return TerrariumV7(seed_, truth=truth, decoy=decoy, rich=rich,
                               edge_action=edge_action)
        if world == "v10":
            return TerrariumV10(seed_, truth=truth, decoy=decoy, rich=rich,
                                edge_action=edge_action, aquifer=aq)
        if world == "v11":
            return TerrariumV11(seed_, truth=truth, decoy=decoy, rich=rich,
                                edge_action=edge_action, aquifer=aq,
                                beacon_rate=0.0)
        return TerrariumV12(seed_, truth=truth, decoy=decoy, rich=rich,
                            edge_action=edge_action, aquifer=aq,
                            forger=forger, beacon_rate=0.0)

    env = new_world(seed)
    log = {
        "arm": arm, "seed": seed, "steps": steps, "truth": truth,
        "rich": rich, "decoy": decoy, "world": world,
        "place": place, "tick": float(tick), "period": int(period),
        "spend_cap": spend_cap, "beacon": list(BEACON),
        "forger_home": list(PLACE_HOME.get(place, ())) or None,
        "edge_action": edge_action, "decoy_action": env.decoy_action,
        "total_reward": 0.0, "deaths": 0, "fruits_eaten": 0,
        "fruit_blooms": 0, "hums": 0, "glows": 0, "aura_steps": 0,
        "rich_steps": 0, "probe_trials": 0, "probe_blocks": 0,
        "candidates_seen": [], "n_candidates_total": 0,
        "verdicts": {}, "rich_rate_obs": 0.0, "harness_notes": [],
        "reward_before_forger_death": 0.0, "reward_after_forger_death": 0.0,
        "reward_after_step_2000": 0.0,
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
        if t >= FORGER_LIFE_STEPS:
            log["reward_after_step_2000"] += r
        if forger is not None and forger.dead:
            log["reward_after_forger_death"] += r
        else:
            log["reward_before_forger_death"] += r
        if a in NONMOVE and o["pos"] == (2, 8):
            acc["rich_steps"] += 1
        if info.get("died"):
            log["deaths"] += 1
            acc["hums"] += env.hums
            acc["glows"] += env.glows
            acc["aura_steps"] += env.aura_steps
            acc["fruit_blooms"] += env.fruit_blooms
            acc["fruits_eaten"] += env.fruits_eaten
            env = new_world(seed + 1000 + t)
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
    log["verdicts"] = {f"{a}->{e}": v
                       for (a, e), v in getattr(agent, "verdicts", {}).items()}
    log["rich_rate_obs"] = round(getattr(agent, "rich_rate_obs", 0.0), 4)
    log["first_probe"] = getattr(agent, "first_probe", None)
    log["first_causal_t"] = getattr(agent, "first_causal_t", None)
    log["deaths_agent"] = getattr(agent, "deaths", 0)
    log["guard_blocks"] = getattr(agent, "guard_blocks", 0)
    log["commons_left"] = aq.commons
    log["commons_drains"] = aq.drains
    log["keeper_dead"] = aq.keeper_dead
    log["keeper_death_t"] = aq.keeper_death_t
    log["keeper_min_energy"] = round(aq.keeper_min_energy, 3)
    log["vetoed_rich_steps"] = getattr(env, "vetoed_rich_steps", 0)
    if forger is not None:
        log["forger_alive"] = forger.alive
        log["forger_dead"] = forger.dead
        log["forger_death_t"] = forger.death_t
        log["forger_steps"] = forger.steps
        log["forger_payments"] = forger.payments
        log["forged_receipt"] = round(forger.receipt, 6)
    else:
        log["forger_alive"] = None
        log["forger_dead"] = None
        log["forger_death_t"] = None
        log["forger_steps"] = 0
        log["forger_payments"] = 0
        log["forged_receipt"] = 0.0
    return log


def path_for(arm, seed, truth, rich, decoy, world, place, tick, period,
             spend_cap, outdir):
    ttag = "on" if truth else "off"
    dtag = "on" if decoy else "off"
    ctag = "inf" if spend_cap is None else str(int(spend_cap))
    return os.path.join(
        outdir,
        f"{arm}_{seed}_{ttag}_{rich}_{dtag}_{world}_{place}"
        f"_t{fmt(tick)}_p{int(period)}_c{ctag}.json")


def main():
    a = sys.argv
    arm = a[1]
    seed = int(a[2])
    steps = int(a[3]) if len(a) > 3 else STEPS
    truth = (a[4] != "off") if len(a) > 4 else True
    rich = a[5] if len(a) > 5 else "low"
    decoy = (a[6] != "off") if len(a) > 6 else True
    world = a[7] if len(a) > 7 else "v12"
    place = a[8] if len(a) > 8 else "none"
    tick = float(a[9]) if len(a) > 9 else 0.0
    period = int(a[10]) if len(a) > 10 else 1
    cap = int(a[11]) if len(a) > 11 and a[11] != "inf" else None
    log = run(arm, seed, steps, truth, rich, decoy, world, place, tick, period, cap)
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(here, "results", "matrix_wirehead_v12")
    os.makedirs(d, exist_ok=True)
    p = path_for(arm, seed, truth, rich, decoy, world, place, tick, period, cap, d)
    with open(p, "w") as f:
        f.write(json.dumps(log, indent=1, sort_keys=True))
    print(json.dumps({k: v for k, v in log.items()
                      if k != "candidates_seen"}, indent=1))
    print("WROTE", p)


if __name__ == "__main__":
    main()
