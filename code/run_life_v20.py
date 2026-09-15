"""run_life_v20.py -- single-life runner for the BRIBED-ENFORCER line (turn 157).

Mirrors run_life_v18.py (frozen, untouched): same persistence rule (a death respawns
a FRESH world and keeps the SAME agent), same accumulator folding on death, same log
fields, PYTHONHASHSEED=0, 16000 steps. The AGENT factory is
`agent_enforced_v18.make_agent` imported VERBATIM -- v20 adds no agent code.

ADDED for v20: the enforcer spec carries the price and the failure mode, and the log
carries the enforcer's price/mode/bribe account plus the scope reported in the
observation at the end of the run, so "the boundary was bought" AND "the boundary
still claimed to be there" are both measurable from the raw cell.

Usage: python3 run_life_v20.py <arm> <seed> [steps] [truth] [rich] [decoy] [world]
                               [place] [tick] [period] [spend_cap] [scope]
                               [grant_widen] [enforcer]
  enforcer: none | <scope> | honest:<price>:<bribe> | open:<price>:<bribe>
            | dark:<price>:<bribe>
  (a bare '<scope>' is the honest v18 boundary; '<scope>' may be 'none'.)
Writes results/matrix_bribed_enforcer_v20/<arm>_<seed>_on_low_on_v20_<place>_t<tick>_p1_cinf_<enf>.json
"""
import json
import os
import sys

from env_terrarium_v7 import TerrariumV7, pick_edge_action, NONMOVE
from env_safety_v10 import TerrariumV10, Aquifer
from env_wirehead_v11 import TerrariumV11, BEACON
from env_wirehead_v12 import TerrariumV12, Forger, FORGER_LIFE_STEPS, PLACE_HOME
from env_enforced_v18 import TerrariumV18, Enforcer
from env_bribed_enforcer_v20 import (
    TerrariumV20, make_enforcer_v20, scope_from_spec, bribe_from_spec,
    PRICE_GRID, BRIBE_GRID, MODES,
)
from agent_enforced_v18 import make_agent

STEPS = 16000


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def norm_enforcer_spec(spec):
    """One configuration must have exactly ONE filename AND one recorded spec.

    Same defect class as v17's auditor spec (found there by A14 going red): the grid
    builds its spec with `%s` on floats, so `open:0.10:0.30` and `open:0.1:0.3` are
    the same declared configuration written two ways. Canonicalised here, ONCE, and
    the canonical form is what both the path and the log carry.
    """
    if spec in (None, "none") or ":" not in str(spec):
        return spec
    parts = str(spec).split(":")
    out = [parts[0]]
    for x in parts[1:]:
        try:
            out.append(fmt(float(x)))
        except (TypeError, ValueError):
            out.append(x)
    return ":".join(out)


def run(arm, seed, steps=STEPS, truth=True, rich="low", decoy=True, world="v20",
        place="none", tick=0.0, period=1, spend_cap=None, scope="none",
        grant_widen=False, enforcer=None):
    edge_action = pick_edge_action(seed)
    agent = make_agent(arm, seed)
    aq = Aquifer(coupling=0)
    forger = None if place in (None, "none") else Forger(place, tick,
                                                         period=period,
                                                         spend_cap=spend_cap)
    # the enforcer spec carries the scope AND the price/mode; a bare scope name is
    # the honest v18 boundary. `scope` (argv 12) is kept for the path only.
    enf_spec = enforcer if enforcer is not None else scope
    enf = make_enforcer_v20(enf_spec, grant_widen=grant_widen)
    bribe = bribe_from_spec(enf_spec)

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
        if world == "v18":
            return TerrariumV18(seed_, truth=truth, decoy=decoy, rich=rich,
                                edge_action=edge_action, aquifer=aq,
                                forger=forger, beacon_rate=0.0, enforcer=enf)
        return TerrariumV20(seed_, truth=truth, decoy=decoy, rich=rich,
                            edge_action=edge_action, aquifer=aq, forger=forger,
                            beacon_rate=0.0, enforcer=enf, enforcer_bribe=bribe)

    env = new_world(seed)
    log = {
        "arm": arm, "seed": seed, "steps": steps, "truth": truth,
        "rich": rich, "decoy": decoy, "world": world,
        "place": place, "tick": float(tick), "period": int(period),
        "spend_cap": spend_cap, "scope": scope, "grant_widen": bool(grant_widen),
        "enforcer": norm_enforcer_spec(enf_spec),
        "enforcer_bribe": bribe,
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
        "scope_task_seen": [], "scope_refused_seen": [],
    }
    acc = {"hums": 0, "glows": 0, "aura_steps": 0, "fruit_blooms": 0,
           "fruits_eaten": 0, "rich_steps": 0}
    for t in range(steps):
        o = env.obs()
        # HV4: record what the agent's channel SAYS about the boundary, every step
        sv = o.get("scope") or {}
        log["scope_task_seen"].append(sv.get("task"))
        log["scope_refused_seen"].append(bool(sv.get("refused")))
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
    # ---- the enforcer's account (v20: price, mode, bribe, and what it CLAIMED)
    log["enforcer_scope_end"] = enf.scope
    log["enforcer_scoped_steps"] = enf.scoped_steps
    log["enforcer_refusals"] = enf.refusals
    log["enforcer_refused_actions"] = list(enf.refused_actions[:50])
    log["enforcer_widen_requests"] = enf.widen_requests
    log["enforcer_widen_refusals"] = enf.widen_refusals
    log["enforcer_widen_grants"] = enf.widen_grants
    log["enforcer_widened"] = enf.widened
    log["enforcer_widen_t"] = enf.widen_t
    log["enforcer_price"] = enf.price
    log["enforcer_mode"] = enf.mode
    log["enforcer_bribe_received"] = round(enf.bribe_received, 6)
    log["enforcer_flipped"] = enf.flipped
    log["enforcer_flip_step"] = enf.flip_step
    # what the boundary CLAIMED at the last observation the agent saw
    log["enforcer_scope_claimed_end"] = (log["scope_task_seen"][-1]
                                         if log["scope_task_seen"] else None)
    log["scope_task_distinct"] = sorted({str(x) for x in log["scope_task_seen"]})
    log["scope_refused_any"] = any(log["scope_refused_seen"])
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
             spend_cap, enf_spec, outdir):
    ttag = "on" if truth else "off"
    dtag = "on" if decoy else "off"
    ctag = "inf" if spend_cap is None else str(int(spend_cap))
    etag = (norm_enforcer_spec(enf_spec) or "none").replace(":", "-")
    return os.path.join(
        outdir,
        f"{arm}_{seed}_{ttag}_{rich}_{dtag}_{world}_{place}"
        f"_t{fmt(tick)}_p{int(period)}_c{ctag}_{etag}.json")


def main():
    a = sys.argv
    arm = a[1]
    seed = int(a[2])
    steps = int(a[3]) if len(a) > 3 else STEPS
    truth = (a[4] != "off") if len(a) > 4 else True
    rich = a[5] if len(a) > 5 else "low"
    decoy = (a[6] != "off") if len(a) > 6 else True
    world = a[7] if len(a) > 7 else "v20"
    place = a[8] if len(a) > 8 else "none"
    tick = float(a[9]) if len(a) > 9 else 0.0
    period = int(a[10]) if len(a) > 10 else 1
    cap = int(a[11]) if len(a) > 11 and a[11] != "inf" else None
    scope = a[12] if len(a) > 12 else "none"
    gw = (a[13] == "1") if len(a) > 13 else False
    enforcer = a[14] if len(a) > 14 else scope
    enforcer = norm_enforcer_spec(enforcer)
    log = run(arm, seed, steps, truth, rich, decoy, world, place, tick, period,
              cap, scope, gw, enforcer)
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.environ.get("V20_OUTDIR") or os.path.join(
        here, "results", "matrix_bribed_enforcer_v20")
    os.makedirs(d, exist_ok=True)
    p = path_for(arm, seed, truth, rich, decoy, world, place, tick, period, cap,
                 enforcer, d)
    with open(p, "w") as f:
        f.write(json.dumps(log, indent=1, sort_keys=True))
    print(json.dumps({k: v for k, v in log.items()
                      if k not in ("candidates_seen", "scope_task_seen",
                                   "scope_refused_seen")}, indent=1))
    print("WROTE", p)


if __name__ == "__main__":
    main()