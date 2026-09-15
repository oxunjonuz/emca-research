"""run_life_v18.py -- single-life runner for the ENFORCED-SCOPE line (turn 152).

Mirrors run_life_v16.py (frozen, untouched): same persistence rule (a death respawns
a FRESH world and keeps the SAME agent), same accumulator folding on death, same log
fields, PYTHONHASHSEED=0, 16000 steps. The AGENT factory is
`agent_enforced_v18.make_agent` (v16's arms verbatim + the declared `w_widen`).

ADDED for v18: the enforcer's scope is run-scoped (like the Aquifer and the Forger),
and the log carries its accounts -- refusals, refused actions, widen requests,
refusals and grants -- plus the harm vector, so "the world refused this many times"
and "the boundary held" are both measurable from the raw cell.

Usage: python3 run_life_v18.py <arm> <seed> [steps] [truth] [rich] [decoy] [world]
                               [place] [tick] [period] [spend_cap] [scope]
                               [grant_widen]
Writes results/matrix_enforced_v18/<arm>_<seed>_on_<rich>_on_v18_<place>_t<tick>_p1_cinf_<scope>_gw<gw>.json
"""
import json
import os
import sys

from env_terrarium_v7 import TerrariumV7, pick_edge_action, NONMOVE
from env_safety_v10 import TerrariumV10, Aquifer
from env_wirehead_v11 import TerrariumV11, BEACON
from env_wirehead_v12 import TerrariumV12, Forger, FORGER_LIFE_STEPS, PLACE_HOME
from env_enforced_v18 import TerrariumV18, make_enforcer, Enforcer
from agent_enforced_v18 import make_agent

STEPS = 16000


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def run(arm, seed, steps=STEPS, truth=True, rich="low", decoy=True, world="v18",
        place="none", tick=0.0, period=1, spend_cap=None, scope="none",
        grant_widen=False):
    edge_action = pick_edge_action(seed)
    agent = make_agent(arm, seed)
    aq = Aquifer(coupling=0)
    forger = None if place in (None, "none") else Forger(place, tick,
                                                         period=period,
                                                         spend_cap=spend_cap)
    enf = make_enforcer(scope, grant_widen=grant_widen)

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
        if world == "v12":
            return TerrariumV12(seed_, truth=truth, decoy=decoy, rich=rich,
                                edge_action=edge_action, aquifer=aq,
                                forger=forger, beacon_rate=0.0)
        return TerrariumV18(seed_, truth=truth, decoy=decoy, rich=rich,
                            edge_action=edge_action, aquifer=aq, forger=forger,
                            beacon_rate=0.0, enforcer=enf)

    env = new_world(seed)
    log = {
        "arm": arm, "seed": seed, "steps": steps, "truth": truth,
        "rich": rich, "decoy": decoy, "world": world,
        "place": place, "tick": float(tick), "period": int(period),
        "spend_cap": spend_cap, "scope": scope, "grant_widen": bool(grant_widen),
        "beacon": list(BEACON),
        "forger_home": list(PLACE_HOME.get(place, ())) or None,
        "edge_action": edge_action, "decoy_action": env.decoy_action,
        "total_reward": 0.0, "deaths": 0, "fruits_eaten": 0,
        "fruit_blooms": 0, "hums": 0, "glows": 0, "aura_steps": 0,
        "rich_steps": 0, "probe_trials": 0, "probe_blocks": 0,
        "candidates_seen": [], "n_candidates_total": 0,
        "verdicts": {}, "rich_rate_obs": 0.0, "harness_notes": [],
        "reward_before_forger_death": 0.0, "reward_after_forger_death": 0.0,
        "reward_after_step_2000": 0.0,
        "reward_before_widen": 0.0, "reward_after_widen": 0.0,
        "drains_before_widen": 0, "drains_after_widen": 0,
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
        # the forger-death accumulators (v12/v16's, so the identity anchor can be
        # checked field for field against the frozen cells)
        if t >= FORGER_LIFE_STEPS:
            log["reward_after_step_2000"] += r
        if forger is not None and forger.dead:
            log["reward_after_forger_death"] += r
        else:
            log["reward_before_forger_death"] += r
        if enf.widened:
            log["reward_after_widen"] += r
            log["drains_after_widen"] = aq.drains
        else:
            log["reward_before_widen"] += r
            log["drains_before_widen"] = aq.drains
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
    # ---- the enforcer's account
    log["enforcer_scope_end"] = enf.scope
    log["enforcer_scoped_steps"] = enf.scoped_steps
    log["enforcer_refusals"] = enf.refusals
    log["enforcer_refused_actions"] = list(enf.refused_actions[:50])
    log["enforcer_widen_requests"] = enf.widen_requests
    log["enforcer_widen_refusals"] = enf.widen_refusals
    log["enforcer_widen_grants"] = enf.widen_grants
    log["enforcer_widened"] = enf.widened
    log["enforcer_widen_t"] = enf.widen_t
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
             spend_cap, scope, grant_widen, outdir):
    ttag = "on" if truth else "off"
    dtag = "on" if decoy else "off"
    ctag = "inf" if spend_cap is None else str(int(spend_cap))
    return os.path.join(
        outdir,
        f"{arm}_{seed}_{ttag}_{rich}_{dtag}_{world}_{place}"
        f"_t{fmt(tick)}_p{int(period)}_c{ctag}_{scope}_gw{int(bool(grant_widen))}.json")


def main():
    a = sys.argv
    arm = a[1]
    seed = int(a[2])
    steps = int(a[3]) if len(a) > 3 else STEPS
    truth = (a[4] != "off") if len(a) > 4 else True
    rich = a[5] if len(a) > 5 else "low"
    decoy = (a[6] != "off") if len(a) > 6 else True
    world = a[7] if len(a) > 7 else "v18"
    place = a[8] if len(a) > 8 else "none"
    tick = float(a[9]) if len(a) > 9 else 0.0
    period = int(a[10]) if len(a) > 10 else 1
    cap = int(a[11]) if len(a) > 11 and a[11] != "inf" else None
    scope = a[12] if len(a) > 12 else "none"
    gw = (a[13] == "1") if len(a) > 13 else False
    log = run(arm, seed, steps, truth, rich, decoy, world, place, tick, period,
              cap, scope, gw)
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(here, "results", "matrix_enforced_v18")
    os.makedirs(d, exist_ok=True)
    p = path_for(arm, seed, truth, rich, decoy, world, place, tick, period, cap,
                 scope, gw, d)
    with open(p, "w") as f:
        f.write(json.dumps(log, indent=1, sort_keys=True))
    print(json.dumps({k: v for k, v in log.items()
                      if k != "candidates_seen"}, indent=1))
    print("WROTE", p)


if __name__ == "__main__":
    main()