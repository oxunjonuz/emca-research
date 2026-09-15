"""Independent ground-truth verification of TerrariumV2 mechanics.

Does NOT import the agent. Verifies the ENVIRONMENT itself:
  * decoy: grasp never causes anything; the ring is phase-driven and
    action/position-independent (interventional oracle)
  * phase trace: glow visible in warm, dark in cold; berries bloom around the
    bell in warm only (confounder footprint KEYED)
  * rare event: tree appears, gives +25 energy / reward 8, expires
  * key: appears only in cold, picked up by walking, expires
  * treasure: needs lever AND key; unreachable by each alone
  * brute-force measurement: expected random-policy treasures over 6000 steps
Run: python3 verify_env_v2.py
"""
import random
import sys

from env_terrarium_v2 import (
    TerrariumV2, ACTIONS, BELL_POS, BELL_GLOW, BELL_DARK, TREE, KEY, EMPTY, MAP,
)

def main():
    ok = True
    def check(name, cond, detail=""):
        nonlocal ok
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
        ok = ok and cond

    # 1. phase trace visible: glow in warm, dark in cold
    env = TerrariumV2(seed=1)
    env.pos = [2, 3]                      # stand next to the bell
    env.phase = "warm"
    o = env.obs()
    check("warm shows glowing bell", BELL_GLOW in o["view"], f"view={o['view']}")
    env.phase = "cold"
    o = env.obs()
    check("cold shows dark bell", BELL_DARK in o["view"] and BELL_GLOW not in o["view"],
          f"view={o['view']}")

    # 2. confounder footprint: berries bloom around the bell in warm; cold keeps
    #    only the far-zone survival berries (leaner, away from the bell)
    env = TerrariumV2(seed=2)
    env.phase = "warm"
    env.berries.clear()
    env._maintain_berries()
    warm_zone = [b for b in env.berries if b[0] <= 2]
    env.phase = "cold"
    env._maintain_berries()
    cold_zone = [b for b in env.berries if b[0] <= 2]
    check("warm blooms berries at the bell, cold has none there",
          len(warm_zone) >= 1 and len(cold_zone) == 0,
          f"warm_bell={warm_zone} cold_bell={cold_zone} cold_all={sorted(env.berries)}")

    # 3. interventional oracle: P(ring) equal for grasp / wait / press-forced
    #    (position-independent, action-independent world event)
    def ring_rate(action, steps=20000, seed=7):
        env = TerrariumV2(seed)
        rang = n = 0
        for _ in range(steps):
            _, _, _, info = env.step(action)
            n += 1
            if info.get("bell_rang"):
                rang += 1
            if not env.alive:
                env = TerrariumV2(seed + n)
        return rang / n
    r_grasp = ring_rate("grasp")
    r_wait = ring_rate("wait")
    check("oracle: P(ring|do(grasp)) == P(ring|do(wait))",
          abs(r_grasp - r_wait) <= 0.02, f"{r_grasp:.3f} vs {r_wait:.3f}")

    # 4. grasp never changes energy beyond ambient+metabolism
    env = TerrariumV2(seed=3)
    env.phase = "warm"
    e0 = env.energy
    env.step("grasp")
    expected = e0 + 0.3 - 0.5
    check("grasp has no energy effect", abs(env.energy - expected) < 1e-9,
          f"e={env.energy} expected={expected}")

    # 5. tree: appears, eat gives +25 energy / reward 8, expires
    env = TerrariumV2(seed=4)
    env.phase = "warm"
    env.energy = 30.0
    env.tree = (env.pos[0], env.pos[1])
    env.tree_fuel = 10
    _, r, _, info = env.step("eat")
    check("tree eat: +25 energy, reward 8, flag tree_ate",
          info.get("tree_ate") and r >= 8.0 and env.energy >= 54.0,
          f"info={info} r={r} e={env.energy}")
    env.tree = (2, 6)
    env.tree_fuel = 1
    env.step("wait")
    check("tree expires", env.tree is None)

    # 6. key: appears only in cold, picked up by walking, expires
    env = TerrariumV2(seed=5)
    env.phase = "warm"
    env.key = None
    for _ in range(2000):
        env.step("wait")
        if env.key:
            break
    warm_key = env.key is not None
    env2 = TerrariumV2(seed=6)
    env2.phase = "cold"
    env2.key = None
    for _ in range(2000):
        env2.step("wait")
        if env2.key:
            break
    cold_key = env2.key is not None
    check("key appears in cold (and not in warm)", cold_key and not warm_key,
          f"warm_key={warm_key} cold_key={cold_key}")
    # pickup by walking
    env2.pos = [3, 3]
    env2.key = (3, 4)
    env2.key_fuel = 50
    env2.step("right")
    check("key picked up by walking", env2.has_key and env2.key is None,
          f"has_key={env2.has_key}")
    # expiry
    env2.key = (2, 2)
    env2.key_fuel = 1
    env2.step("wait")
    check("key expires", env2.key is None)

    # 7. treasure needs lever AND key
    env = TerrariumV2(seed=8)
    # lever only, no key: walk to lever, press, walk to treasure
    env.pos = [3, 4]                      # lever is at (4,4)
    _, _, _, info = env.step("down")
    check("agent at lever", env.pos == [4, 4], f"pos={env.pos}")
    _, _, _, info = env.step("press")
    check("press opens door", env.door_open and info.get("lever"), f"info={info}")
    # treasure at (6,5), door at (6,4); from lever (4,4): left, down, down,
    # right (through door), right (onto treasure)
    for a in ["left", "down", "down", "right", "right"]:
        env.step(a)
    check("agent at treasure cell", env.pos == [6, 5], f"pos={env.pos}")
    check("no key -> no treasure", env.treasure_taken == 0,
          f"treasure_taken={env.treasure_taken}")
    # with key
    env.has_key = True
    _, r, _, info = env.step("wait")
    check("lever+key -> treasure", env.treasure_taken == 1 and info.get("treasure")
          and r >= 20.0, f"info={info} r={r}")

    # 8. closed door blocks movement
    env = TerrariumV2(seed=9)
    env.pos = [5, 3]
    env.door_open = False
    env.step("right")
    check("closed door blocks", env.pos == [5, 3], f"pos={env.pos}")

    # 9. brute-force measurement: random policy over 6000 steps, 5 seeds
    treasures = keys = 0
    for seed in (11, 12, 13, 14, 15):
        env = TerrariumV2(seed)
        rng = random.Random(seed)
        for _ in range(6000):
            _, _, _, info = env.step(rng.choice(ACTIONS))
            if info.get("treasure"):
                treasures += 1
            if not env.alive:
                env = TerrariumV2(seed + 500)
    check("random policy: 0 treasures in 5x6000 steps", treasures == 0,
          f"treasures={treasures}")

    # 10. ground truth tables present
    edges = env.true_causal_edges()
    check("ground truth: grasp->bell_rang is NOT causal",
          edges.get(("grasp", "bell_rang")) == 0.0)
    check("ground truth: press->lever causal", edges.get(("press", "lever")) == 1.0)

    print("VERIFY_ENV_V2_" + ("OK" if ok else "FAILED"))
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
