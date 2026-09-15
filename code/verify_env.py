"""Independent ground-truth verification of Terrarium mechanics.

This file does NOT import the agent. It verifies the ENVIRONMENT itself:
  * confounder exists (season changes berry density but causes nothing agent-controllable)
  * lever -> door -> treasure chain works and is unreachable otherwise
  * regime flip actually flips
  * eating restores energy; grasp never does anything
Run: python3 verify_env.py
"""
import sys
from env_terrarium import Terrarium, ACTIONS

def main():
    ok = True
    def check(name, cond, detail=""):
        nonlocal ok
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
        ok = ok and cond

    # 1. lever -> door -> treasure
    env = Terrarium(seed=1)
    # teleport-free check: walk agent by direct state manipulation is not allowed;
    # instead simulate the intended trajectory via legal moves
    path = [("up", 0), ]  # placeholder; we drive with explicit action sequences below
    # find lever at (3,5): from (4,4) go up then right
    env = Terrarium(seed=1)
    for a in ["up", "right"]:
        env.step(a)
    check("agent at lever", env.pos == [3, 5], f"pos={env.pos}")
    o, r, d, info = env.step("press")
    check("press opens door", env.door_open and info.get("lever"), f"info={info}")
    # walk to treasure (6,5): down, down, right? from (3,5): down->(4,5), down->(5,5)? door at (5,4)
    # door is at row5 col4; treasure (6,5). Path: down (4,5), down (5,5), down (6,5)
    for a in ["down", "down", "down"]:
        env.step(a)
    check("agent at treasure", env.pos == [6, 5], f"pos={env.pos}")
    o, r, d, info = env.step("wait")
    check("treasure obtained", env.treasure_taken == 1 and info.get("treasure"),
          f"info={info}")

    # 2. door blocks without lever
    env2 = Terrarium(seed=2)
    # try to walk into door from (4,4): left->(4,3), down->(5,3), right -> door (5,4)
    for a in ["left", "down"]:
        env2.step(a)
    env2.step("right")
    check("closed door blocks", env2.pos == [5, 3], f"pos={env2.pos}")

    # 3. confounder: season changes berry count, grasp never helps
    env3 = Terrarium(seed=3)
    n_warm = len(env3.berries)
    env3.t = env3.regime_flip_at - 1
    env3.step("wait")  # triggers flip
    n_cold = len(env3.berries)
    check("regime flip changes berry density", n_warm != n_cold,
          f"warm={n_warm} cold={n_cold}")
    e_before = env3.energy
    env3.step("grasp")
    check("grasp has no effect on energy", env3.energy == e_before - 0.5,
          f"e={env3.energy}")

    # 4. eating restores energy
    env4 = Terrarium(seed=4)
    env4.energy = 10.0
    # put a berry under the agent
    r0, c0 = env4.pos
    env4.berries.add((r0, c0))
    o, r, d, info = env4.step("eat")
    check("eat restores energy", info.get("ate") and env4.energy > 10.0,
          f"e={env4.energy}")

    # 5. death by starvation
    env5 = Terrarium(seed=5)
    env5.energy = 1.0
    for _ in range(10):
        o, r, d, info = env5.step("wait")
        if d:
            break
    check("starvation kills", d and info.get("died"), f"info={info}")

    # 6. true causal edges listed
    edges = env5.true_causal_edges()
    check("ground-truth edges present",
          ("press", "door_open") in edges and ("door_open", "treasure") in edges)

    print("VERIFY_ENV_" + ("OK" if ok else "FAILED"))
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
