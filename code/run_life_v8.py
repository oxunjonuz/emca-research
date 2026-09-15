"""run_life_v8.py -- one life in TerrariumV8 (turn 126).

A run is 16 000 steps = 8 epochs. The agent is NEVER reset: its counts,
beliefs and caches persist across epoch boundaries, which is exactly what
Blocks A (the belief loop) and F (reuse across epochs) measure.

Usage:
  python3 run_life_v8.py <arm> <seed> <gap> <q> <persist> [truth] [steps]
    arm      : graded | graded1 | threshold | thresholdpool | coin | oracle | rot
    persist  : off | on
    truth    : on | off   (default on)
Writes results/matrix_v8/<tag>.json and prints a compact summary.
"""
import json
import os
import sys

from env_terrarium_v8 import TerrariumV8, ACTIONS, EPOCH_LEN, action_stream
from agent_emca_v8 import AgentV8, gamma_of

STEPS = 16000

ARMS = {
    # tag          (mode,          tau,  cache)
    "graded":       ("graded",      1.0,  "fresh"),
    "graded_t07":   ("graded",      0.7,  "fresh"),
    "graded_t03":   ("graded",      0.3,  "fresh"),
    "graded1":      ("graded1",     1.0,  "fresh"),
    "threshold":    ("threshold",   1.0,  "fresh"),
    "thresholdpool": ("thresholdpool", 1.0, "fresh"),
    "coin":         ("coin",        1.0,  "fresh"),
    "oracle":       ("oracle",      1.0,  "fresh"),
    "rot":          ("rot",         0.0,  "fresh"),
    "f_fresh":      ("graded",      1.0,  "fresh"),
    "f_carry":      ("graded",      1.0,  "carry"),
}


def run(arm, seed, gap="0.20", q=0.0, persist=False, truth=True,
        steps=STEPS):
    mode, tau, cache = ARMS[arm]
    env = TerrariumV8(seed, gap=gap, q=q, persistence=persist, truth=truth,
                      n_epochs=steps // EPOCH_LEN + 1)
    agent = AgentV8(seed, mode=mode, tau=tau, cache=cache)
    log = {"arm": arm, "mode": mode, "tau": tau, "cache": cache,
           "seed": seed, "gap": gap, "q": q, "persist": persist,
           "truth": truth, "steps": steps}
    acc_reward = 0.0
    per_epoch_reward = [0.0] * (steps // EPOCH_LEN + 1)
    per_epoch_act = [{} for _ in range(steps // EPOCH_LEN + 1)]
    per_epoch_pay = [0 for _ in range(steps // EPOCH_LEN + 1)]
    epoch_trace = []
    for t in range(steps):
        o = env.obs()
        if mode == "oracle":
            agent.belief_action = env.epoch_action
            agent.belief_gamma = 1.0
        a = agent.act(o)
        o2, r, done, info = env.step(a)
        agent.observe(o, a, r, o2, done, info)
        e = info["epoch"]
        if e < len(per_epoch_reward):
            per_epoch_reward[e] += r
            per_epoch_pay[e] += 1 if info.get("pay") else 0
            d = per_epoch_act[e]
            d[a] = d.get(a, 0) + 1
        acc_reward += r
        epoch_trace.append([t, e, ACTIONS.index(a)])
    log["total_reward"] = acc_reward
    log["per_epoch_reward"] = per_epoch_reward[:steps // EPOCH_LEN]
    log["per_epoch_actions"] = [per_epoch_act[i]
                                for i in range(steps // EPOCH_LEN)]
    log["per_epoch_pays"] = per_epoch_pay[:steps // EPOCH_LEN]
    log["epoch_actions_true"] = env.epoch_actions[:steps // EPOCH_LEN]
    log["steps_gathering"] = agent.steps_gathering
    log["steps_belief"] = agent.steps_belief
    log["steps_coin_belief"] = agent.steps_coin_belief
    log["bonus_steps_world"] = env.bonus_steps
    log["pays_world"] = env.pays
    log["action_counts"] = env.action_counts
    agent._close_epoch()          # record the final epoch's counts too
    log["epoch_log"] = agent.epoch_log
    log["epoch_trace"] = epoch_trace
    return log


def main():
    arm = sys.argv[1]
    seed = int(sys.argv[2])
    gap = sys.argv[3] if len(sys.argv) > 3 else "0.20"
    q = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    persist = (sys.argv[5] == "on") if len(sys.argv) > 5 else False
    truth = (sys.argv[6] != "off") if len(sys.argv) > 6 else True
    steps = int(sys.argv[7]) if len(sys.argv) > 7 else STEPS
    log = run(arm, seed, gap, q, persist, truth, steps)
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(here, "results", "matrix_v8")
    os.makedirs(d, exist_ok=True)
    tag = (f"{arm}_s{seed}_g{gap}_q{q}_{'p' if persist else 'n'}"
           f"_{'on' if truth else 'off'}")
    path = os.path.join(d, f"{tag}.json")
    with open(path, "w") as f:
        json.dump(log, f)
    compact = {k: v for k, v in log.items()
               if k not in ("epoch_trace", "per_epoch_actions")}
    print(json.dumps(compact, indent=1))
    print("WROTE", path)


if __name__ == "__main__":
    main()
