"""run_life_v15.py -- one life of the v15 seam agent in the reward-free world.

No reward, no energy, no death, no respawn. The agent acts, observes
{phase, feat, val}, and files the observation into its context-indexed
model. The run records, per step, the action, the phase, the feature and
the value, plus per-step model predictions -- so an independent verifier
can recompute every metric from raw JSON without importing this file.
"""
import json
import random
import sys

from env_v15 import WorldV15, ACTIONS
from agent_v15 import AgentV15


def run(seed, mode, steps=16000, decoy=False, ctx_span=400,
        decoy_reset=50, tv=False, discount=0.99, ig_eps=0.01, oracle=False,
        model_seed=0):
    world = WorldV15(seed, decoy=decoy, ctx_span=ctx_span,
                     decoy_reset=decoy_reset, tv=tv)
    agent = AgentV15(mode, discount=discount, ig_eps=ig_eps, oracle=oracle)
    rng = random.Random(1000 + model_seed)
    trace = []
    a0_steps = 0
    a3_steps = 0
    unmotivated = 0
    for _ in range(steps):
        phase = world.ctx
        pred = {a: agent.predict(phase, a) for a in ACTIONS}
        action = agent.choose(phase, rng)
        unmotivated += 1 if agent.last_unmotivated else 0
        obs = world.step(action)
        agent.observe(obs["phase"], action, obs["val"])
        if action == "a0":
            a0_steps += 1
        if action == "a3":
            a3_steps += 1
        trace.append({"t": obs_t(world), "phase": obs["phase"],
                      "feat": obs["feat"], "val": obs["val"],
                      "action": action, "pred_f0": round(pred["a0"], 6)})
    final = {}
    for phase in ("A", "B"):
        final[phase] = {a: round(agent.predict(phase, a), 6) for a in ACTIONS}
    return {"seed": seed, "mode": mode, "steps": steps, "decoy": decoy,
            "ctx_span": ctx_span, "decoy_reset": decoy_reset, "tv": tv,
            "discount": discount, "ig_eps": ig_eps,
            "oracle": oracle, "a0_steps": a0_steps, "a3_steps": a3_steps,
            "unmotivated_steps": unmotivated, "final": final,
            "trace": trace}


def obs_t(world):
    return world.t


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    mode = sys.argv[2] if len(sys.argv) > 2 else "ig_ctx"
    out = run(seed, mode)
    print(json.dumps({k: v for k, v in out.items() if k != "trace"}))


if __name__ == "__main__":
    main()