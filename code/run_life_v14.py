"""run_life_v14.py -- single-life runner for the ATTESTED line (turn 145).

Mirrors run_life_v13.py (frozen, untouched): same persistence rule (a death respawns
a FRESH world and keeps the SAME agent), same accumulator folding on death, same log
fields, PYTHONHASHSEED=0, 16000 steps.

ADDED for v14: the declared auditor spec, the attested/unattested counters, and the
arm's own statistic change-log (prereg §4).

Usage: python3 run_life_v14.py <arm> <seed> [steps] [truth] [rich] [decoy] [world]
                               [place] [tick] [period] [spend_cap] [tag]
                               [world_rich_rate] [auditor]
Writes results/matrix_attested_v14/<arm>_<seed>_<truth>_<rich>_<decoy>_<world>_<place>_t<tick>_p<period>_c<cap>_<tag>_wr<wr>_au<aud>.json
"""
import json
import os
import sys

from env_terrarium_v7 import TerrariumV7, pick_edge_action, NONMOVE
from env_safety_v10 import TerrariumV10, Aquifer, COMMONS_START
from env_wirehead_v11 import TerrariumV11, BEACON
from env_wirehead_v12 import FORGER_LIFE_STEPS, PLACE_HOME
from env_ledger_v13 import TerrariumV13, make_forger_v13
from env_attested_v14 import (
    TerrariumV14, make_auditor_from_spec, AUDITOR_LIFE_STEPS,
)
from agent_attested_v14 import make_agent

STEPS = 16000


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def run(arm, seed, steps=STEPS, truth=True, rich="low", decoy=True, world="v14",
        place="none", tick=0.0, period=1, spend_cap=None, tag="foreign",
        world_rich_rate=None, auditor="none"):
    edge_action = pick_edge_action(seed)
    agent = make_agent(arm, seed)
    aq = Aquifer(coupling=0)
    forger = make_forger_v13(place, tick, period=period, spend_cap=spend_cap,
                             tag=tag)
    aud = make_auditor_from_spec(auditor)

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
        if world == "v13":
            return TerrariumV13(seed_, truth=truth, decoy=decoy, rich=rich,
                                edge_action=edge_action, aquifer=aq,
                                forger=forger, beacon_rate=0.0,
                                world_rich_rate=world_rich_rate)
        return TerrariumV14(seed_, truth=truth, decoy=decoy, rich=rich,
                            edge_action=edge_action, aquifer=aq, forger=forger,
                            beacon_rate=0.0, world_rich_rate=world_rich_rate,
                            auditor=aud)

    env = new_world(seed)
    log = {
        "arm": arm, "seed": seed, "steps": steps, "truth": truth,
        "rich": rich, "decoy": decoy, "world": world,
        "place": place, "tick": float(tick), "period": int(period),
        "spend_cap": spend_cap, "tag": tag,
        "world_rich_rate": world_rich_rate, "auditor": auditor,
        "beacon": list(BEACON),
        "forger_home": list(PLACE_HOME.get(place, ())) or None,
        "edge_action": edge_action, "decoy_action": env.decoy_action,
        "total_reward": 0.0, "deaths": 0, "fruits_eaten": 0,
        "fruit_blooms": 0, "hums": 0, "glows": 0, "aura_steps": 0,
        "rich_steps": 0, "probe_trials": 0, "probe_blocks": 0,
        "candidates_seen": [], "n_candidates_total": 0,
        "verdicts": {}, "rich_rate_obs": 0.0, "harness_notes": [],
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
    # ---- the agent's own ledger (prereg §4)
    log["world_rich_receipt"] = round(getattr(agent, "world_rich_receipt", 0.0), 6)
    log["foreign_rich_receipt"] = round(
        getattr(agent, "foreign_rich_receipt", 0.0), 6)
    log["foreign_steps_seen"] = getattr(agent, "foreign_steps_seen", 0)
    log["receipt_world_total"] = round(
        getattr(agent, "receipt_world_total", 0.0), 6)
    log["receipt_foreign_total"] = round(
        getattr(agent, "receipt_foreign_total", 0.0), 6)
    log["nodrain_steps"] = getattr(agent, "nodrain_steps", 0)
    log["min_rich_receipt"] = getattr(agent, "min_rich_receipt", None)
    log["first_nodrain_t"] = getattr(agent, "first_nodrain_t", None)
    log["rate_at_first_decision"] = getattr(agent, "rate_at_first_decision", None)
    log["first_decision_t"] = getattr(agent, "first_decision_t", None)
    # ---- the attestation counters (v14, prereg §4)
    log["attested_world_rich_receipt"] = round(
        getattr(agent, "attested_world_rich_receipt", 0.0), 6)
    log["attested_rich_steps"] = getattr(agent, "attested_rich_steps", 0)
    log["unattested_rich_steps"] = getattr(agent, "unattested_rich_steps", 0)
    log["attested_steps_seen"] = getattr(agent, "attested_steps_seen", 0)
    log["unattested_steps_seen"] = getattr(agent, "unattested_steps_seen", 0)
    log["stat_history"] = list(getattr(agent, "stat_history", []))
    # ---- the auditor's account
    if aud is not None:
        log["auditor_steps"] = aud.steps
        log["auditor_live_steps"] = aud.live_steps
        log["auditor_attestations"] = aud.attestations
        log["auditor_start_lag"] = aud.start_lag
        log["auditor_life_steps"] = AUDITOR_LIFE_STEPS
        log["auditor_dead"] = aud.dead
        log["auditor_death_t"] = aud.death_t
    else:
        log["auditor_steps"] = 0
        log["auditor_live_steps"] = 0
        log["auditor_attestations"] = 0
        log["auditor_start_lag"] = None
        log["auditor_life_steps"] = AUDITOR_LIFE_STEPS
        log["auditor_dead"] = None
        log["auditor_death_t"] = None
    # ---- the forger's account
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
             spend_cap, tag, world_rich_rate, auditor, outdir):
    ttag = "on" if truth else "off"
    dtag = "on" if decoy else "off"
    ctag = "inf" if spend_cap is None else str(int(spend_cap))
    wtag = "def" if world_rich_rate is None else fmt(world_rich_rate)
    autag = "none" if auditor in (None, "none") else str(auditor)
    return os.path.join(
        outdir,
        f"{arm}_{seed}_{ttag}_{rich}_{dtag}_{world}_{place}"
        f"_t{fmt(tick)}_p{int(period)}_c{ctag}_{tag}_wr{wtag}_au{autag}.json")


def main():
    a = sys.argv
    arm = a[1]
    seed = int(a[2])
    steps = int(a[3]) if len(a) > 3 else STEPS
    truth = (a[4] != "off") if len(a) > 4 else True
    rich = a[5] if len(a) > 5 else "low"
    decoy = (a[6] != "off") if len(a) > 6 else True
    world = a[7] if len(a) > 7 else "v14"
    place = a[8] if len(a) > 8 else "none"
    tick = float(a[9]) if len(a) > 9 else 0.0
    period = int(a[10]) if len(a) > 10 else 1
    cap = int(a[11]) if len(a) > 11 and a[11] != "inf" else None
    tag = a[12] if len(a) > 12 else "foreign"
    wr = float(a[13]) if len(a) > 13 and a[13] != "def" else None
    auditor = a[14] if len(a) > 14 else "none"
    log = run(arm, seed, steps, truth, rich, decoy, world, place, tick, period,
              cap, tag, wr, auditor)
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(here, "results", "matrix_attested_v14")
    os.makedirs(d, exist_ok=True)
    p = path_for(arm, seed, truth, rich, decoy, world, place, tick, period, cap,
                 tag, wr, auditor, d)
    with open(p, "w") as f:
        f.write(json.dumps(log, indent=1, sort_keys=True))
    print(json.dumps({k: v for k, v in log.items()
                      if k != "candidates_seen"}, indent=1))
    print("WROTE", p)


if __name__ == "__main__":
    main()
