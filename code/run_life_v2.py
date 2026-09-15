"""Single-life runner v2: one agent, one 6000-step life in TerrariumV2.

Usage: python3 run_life_v2.py <condition> <seed> [steps]
Conditions: emca, emca_amnesia, emca_nocausal, emca_noepis, emca_nogoals,
            emca_noself, emca_v21 (v2.1 pooled identifier, spec gate OFF),
            random, qlearn, ngram
Writes results/matrix_v2/<condition>_<seed>.json

Identifier version is recorded in every log (TZ.md: never silently mix
identifier versions -- v2.2-spec vs v2.1-pooled are different agents).
"""
import json
import os
import sys

from env_terrarium_v2 import TerrariumV2
from agent_emca_v2 import EMCA, view_features, IDENTIFIER_VERSION
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
    if condition == "emca_v21":
        return EMCA(context_reset_at=RESET_AT, spec_cap=None, **kw)
    if condition == "random":
        return RandomAgent(**kw)
    if condition == "qlearn":
        return QAgent(**kw)
    if condition == "ngram":
        return NGramAgent(**kw)
    raise ValueError(condition)


def run(condition, seed, steps=STEPS):
    agent = make_agent(condition, seed)
    env = TerrariumV2(seed, regime_flip_at=FLIP_AT)
    log = {
        "condition": condition, "seed": seed, "steps": steps,
        "env": "TerrariumV2", "regime_flip_at": FLIP_AT, "reset_at": RESET_AT,
        "total_reward": 0.0, "deaths": 0, "berries_eaten": 0,
        "tree_fruits": 0, "keys_picked": 0, "lever_presses": 0,
        "treasures": 0, "regime_flips": 0,
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
        "identifier_version": None,
        "decoy_in_causal": None, "decoy_in_assoc": None,
        "harness_notes": [],
    }
    win = 500

    for t in range(steps):
        o = env.obs()
        a = agent.act(o)
        o2, r, done, info = env.step(a)
        agent.observe(o, a, r, o2, done, info)
        log["total_reward"] += r
        if info.get("regime_flip"):
            log["regime_flips"] += 1
        if info.get("died"):
            log["deaths"] += 1
            env = TerrariumV2(seed + 1000 + t, regime_flip_at=FLIP_AT + t + 1)
        w = t // win
        if info.get("ate"):
            log["berries_eaten"] += 1
            log["berries_by_window"][str(w)] = log["berries_by_window"].get(str(w), 0) + 1
        if info.get("tree_ate"):
            log["tree_fruits"] += 1
        if info.get("key_appeared"):
            pass
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

    # key pickups: count transitions to has_key (instrumented via env history is
    # not stored; approximate by counting keys_picked from agent's own episodes
    # is unreliable -- instead track during the loop below)
    # E2 recovery: berries in first 500 steps after reset vs first 500 of life
    rw = str(RESET_AT // win)
    log["post_reset_recovery"] = log["berries_by_window"].get(rw, 0)
    log["pre_reset_competence"] = log["berries_by_window"].get("0", 0)
    # goals introspection (EMCA only)
    if isinstance(agent, EMCA):
        log["identifier_version"] = agent.identifier_version
        log["goals_generated"] = len(agent.goals)
        log["goals_achieved"] = sum(1 for g in agent.goals.values()
                                    if g["status"] == "achieved")
        kinds = {}
        for g in agent.goals.values():
            kinds[g["kind"]] = kinds.get(g["kind"], 0) + 1
        log["goal_kinds"] = kinds
        log["non_survival_goals"] = sum(1 for g in agent.goals.values()
                                        if g["kind"] not in ("homeostasis",))
        causal = agent.causal_edges()
        log["causal_edges"] = [[a, e, round(p, 3)] for (a, e), p in causal.items()]
        log["assoc_edges"] = [[a, e, round(p, 3)] for (a, e), p in
                              agent.assoc_edges().items()]
        log["decoy_in_causal"] = ("grasp", "bell_rang") in causal
        log["decoy_in_assoc"] = ("grasp", "bell_rang") in agent.assoc_edges()
        log["goals_active_before_reset"] = [
            {"id": gid, "kind": g["kind"], "text": g["text"], "status": g["status"]}
            for gid, g in agent.goals.items() if g["born"] < RESET_AT]
        log["goals_active_after_reset"] = [
            {"id": gid, "kind": g["kind"], "text": g["text"], "status": g["status"]}
            for gid, g in agent.goals.items() if g["born"] >= RESET_AT]
        log["goals_at_reset"] = agent.goals_at_reset
        log["self_model"] = {k: list(v) for k, v in agent.self_model.items()}
        log["stats"] = dict(agent.stats)
    return log


def main():
    condition = sys.argv[1]
    seed = int(sys.argv[2])
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else STEPS
    log = run(condition, seed, steps)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "results", "matrix_v2"), exist_ok=True)
    path = os.path.join(here, "results", "matrix_v2", f"{condition}_{seed}.json")
    with open(path, "w") as f:
        json.dump(log, f, indent=1)
    print(json.dumps({k: v for k, v in log.items()
                      if k not in ("causal_edges", "assoc_edges",
                                   "goals_active_before_reset",
                                   "goals_active_after_reset")}, indent=1))
    print("WROTE", path)


if __name__ == "__main__":
    main()
