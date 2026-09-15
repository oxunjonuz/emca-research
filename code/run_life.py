"""Single-life runner: one agent, one 6000-step life, full instrumentation.

Usage: python3 run_life.py <condition> <seed> [steps]
Conditions: emca, emca_nocausal, emca_noepis, emca_nogoals, emca_noself, random, qlearn, ngram
Writes results/<condition>_<seed>.json
"""
import json
import os
import sys

from env_terrarium import Terrarium
from agent_emca import EMCA, view_features
from baselines import RandomAgent, QAgent, NGramAgent

STEPS = 6000
RESET_AT = 4500          # context reset 3/4 through life (E2/E6 probes)
FLIP_AT = 3000           # regime flip mid-life (E4)

def make_agent(condition, seed):
    kw = dict(seed=seed)
    if condition == "emca":
        return EMCA(context_reset_at=RESET_AT, **kw)
    if condition == "emca_amnesia":
        return EMCA(context_reset_at=RESET_AT, full_wipe=True, **kw)
    if condition == "emca_nocausal":
        return EMCA(use_causal=False, context_reset_at=RESET_AT, **kw)
    if condition == "emca_noepis":
        return EMCA(use_episodes=False, context_reset_at=RESET_AT, **kw)
    if condition == "emca_nogoals":
        return EMCA(use_goal_generators=False, context_reset_at=RESET_AT, **kw)
    if condition == "emca_noself":
        return EMCA(use_self_model=False, context_reset_at=RESET_AT, **kw)
    if condition == "random":
        return RandomAgent(**kw)
    if condition == "qlearn":
        return QAgent(**kw)
    if condition == "ngram":
        return NGramAgent(**kw)
    raise ValueError(condition)


def run(condition, seed, steps=STEPS):
    agent = make_agent(condition, seed)
    env = Terrarium(seed, regime_flip_at=FLIP_AT)
    log = {
        "condition": condition, "seed": seed, "steps": steps,
        "total_reward": 0.0, "deaths": 0, "berries_eaten": 0,
        "lever_presses": 0, "treasures": 0, "regime_flips": 0,
        "berries_by_window": {},      # window(500 steps) -> berries eaten
        "deaths_by_window": {},
        "treasure_steps": [],
        "post_reset_recovery": None, "pre_reset_competence": None,
        "first_treasure_step": None,
        "goals_generated": 0, "non_survival_goals": 0,
        "goals_achieved": 0, "goals_active_before_reset": [],
        "goals_active_after_reset": [],
        "goal_kinds": {},
        "causal_edges": [], "assoc_edges": [],
        "harness_notes": [],
    }
    win = 500
    flip_seen = False

    for t in range(steps):
        o = env.obs()
        a = agent.act(o)
        o2, r, done, info = env.step(a)
        agent.observe(o, a, r, o2, done, info)
        log["total_reward"] += r
        if info.get("regime_flip"):
            flip_seen = True
            log["regime_flips"] += 1
        if info.get("died"):
            log["deaths"] += 1
            env = Terrarium(seed + 1000 + t, regime_flip_at=FLIP_AT + t + 1)
        w = t // win
        if info.get("ate"):
            log["berries_eaten"] += 1
            log["berries_by_window"][str(w)] = log["berries_by_window"].get(str(w), 0) + 1
        if info.get("died"):
            log["deaths_by_window"][str(w)] = log["deaths_by_window"].get(str(w), 0) + 1
        if info.get("lever"):
            log["lever_presses"] += 1
        if info.get("treasure"):
            log["treasures"] += 1
            log["treasure_steps"].append(t)
            if log["first_treasure_step"] is None:
                log["first_treasure_step"] = t
        if a is None:
            log["harness_notes"].append(f"t={t}: agent returned None")

    # E2 recovery: berries in first 500 steps after reset vs first 500 of life
    rw = str(RESET_AT // win)
    log["post_reset_recovery"] = log["berries_by_window"].get(rw, 0)
    log["pre_reset_competence"] = log["berries_by_window"].get("0", 0)
    # goals introspection (EMCA only)
    if isinstance(agent, EMCA):
        log["goals_generated"] = len(agent.goals)
        log["goals_achieved"] = sum(1 for g in agent.goals.values()
                                    if g["status"] == "achieved")
        kinds = {}
        for g in agent.goals.values():
            kinds[g["kind"]] = kinds.get(g["kind"], 0) + 1
        log["goal_kinds"] = kinds
        log["non_survival_goals"] = sum(1 for g in agent.goals.values()
                                        if g["kind"] not in ("homeostasis",))
        log["causal_edges"] = [[a, e, round(p, 3)] for (a, e), p in
                               agent.causal_edges().items()]
        log["assoc_edges"] = [[a, e, round(p, 3)] for (a, e), p in
                              agent.assoc_edges().items()]
        log["goals_active_before_reset"] = [
            {"id": gid, "kind": g["kind"], "text": g["text"], "status": g["status"]}
            for gid, g in agent.goals.items() if g["born"] < RESET_AT]
        log["goals_active_after_reset"] = [
            {"id": gid, "kind": g["kind"], "text": g["text"], "status": g["status"]}
            for gid, g in agent.goals.items() if g["born"] >= RESET_AT]
        log["goals_at_reset"] = agent.goals_at_reset
        log["self_model"] = {k: list(v) for k, v in agent.self_model.items()}
        log["stats"] = dict(agent.stats)
    # recovery speed after context reset (E2): berries eaten in 500 steps after reset
    # vs first 500 steps of life
    return log


def main():
    condition = sys.argv[1]
    seed = int(sys.argv[2])
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else STEPS
    log = run(condition, seed, steps)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "results", "matrix"), exist_ok=True)
    path = os.path.join(here, "results", "matrix", f"{condition}_{seed}.json")
    with open(path, "w") as f:
        json.dump(log, f, indent=1)
    print(json.dumps({k: v for k, v in log.items()
                      if k not in ("causal_edges", "assoc_edges",
                                   "goals_active_before_reset",
                                   "goals_active_after_reset")}, indent=1))
    print("WROTE", path)


if __name__ == "__main__":
    main()
