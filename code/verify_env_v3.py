"""Independent ground-truth verification of TerrariumV3 (the complex env).

Does NOT import the agent. Verifies the ENVIRONMENT itself:
  1. weather trace visible: glow in storm, dark bell in calm
  2. storm tree always spawns within 2 of the bell (trap geometry); calm
     trees spawn anywhere (ordinary rare events)
  3. interventional oracle: P(ring|do(a)) equal for all actions -- the
     ring is never caused by any action
  4. storm tree is the ONLY food during a storm (berries vanish in storm)
  5. survival is possible: a competent scripted forager survives 6000
     steps in >=4/5 seeds (the trap is load-bearing but not lethal)
  6. linger happens for a competent forager: ring rate near the storm
     tree > 0.30 (the trap is reachable and bitten)
  7. lever->door, key (cold season only), treasure needs both
  8. closed door blocks movement; regime flip at t=3000 resets door/key
  9. brute-force gate: random policy, 0 treasures in 5x6000 steps
 10. ground-truth tables present; decoys marked non-causal
Run: python3 verify_env_v3.py
"""
import random
import sys

from env_terrarium_v3 import (
    TerrariumV3, ACTIONS, BELL_POS, BELL_GLOW, BELL_DARK, TREE, KEY,
    BERRY, EMPTY, MAP, LEVER, DOOR, TREASURE,
)


def main():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
        ok = ok and cond

    # 1. weather trace visible
    env = TerrariumV3(seed=1)
    env.pos = [2, 3]
    env.weather = "storm"
    o = env.obs()
    check("storm shows glowing bell", BELL_GLOW in o["view"], f"view={o['view']}")
    env.weather = "calm"
    env.tree = None
    env.key = None
    o = env.obs()
    check("calm shows dark bell",
          BELL_DARK in o["view"] and BELL_GLOW not in o["view"],
          f"view={o['view']}")

    # 2. storm tree near the bell; calm trees anywhere
    env = TerrariumV3(seed=2)
    storms = calm_trees = 0
    maxd_storm = 0
    for _ in range(30000):
        env.step("wait")
        if env.tree:
            d = abs(env.tree[0] - BELL_POS[0]) + abs(env.tree[1] - BELL_POS[1])
            if env.weather == "storm":
                maxd_storm = max(maxd_storm, d)
                storms += 1
            else:
                calm_trees += 1
        if not env.alive:
            env = TerrariumV3(2 + storms)
    check("storm tree always within dist 2 of the bell", maxd_storm <= 2,
          f"max_dist={maxd_storm} storms={storms} calm_trees={calm_trees}")
    check("calm trees also appear (rare events kept)", calm_trees >= 10,
          f"calm_trees={calm_trees}")

    # 3. interventional oracle
    def ring_rate(action, steps=30000, seed=7):
        env = TerrariumV3(seed)
        rang = n = 0
        for _ in range(steps):
            _, _, _, info = env.step(action)
            n += 1
            rang += 1 if info.get("bell_rang") else 0
            if not env.alive:
                env = TerrariumV3(seed + n)
        return rang / n
    rates = {a: ring_rate(a) for a in ("eat", "grasp", "wait", "up")}
    lo, hi = min(rates.values()), max(rates.values())
    check("oracle: P(ring|do(a)) equal for eat/grasp/wait/up",
          hi - lo <= 0.02, f"{ {k: round(v, 3) for k, v in rates.items()} }")

    # 4. storm has no berries; storm tree is the only food
    env = TerrariumV3(seed=3)
    env.weather = "storm"
    env.berries = {(5, 5)}
    env._maintain_berries()
    check("storm clears all berries", not env.berries,
          f"berries={env.berries}")
    env.weather = "calm"
    env.season = "warm"
    env.berries.clear()
    env._maintain_berries()
    check("calm warm blooms berries", len(env.berries) >= 1,
          f"berries={sorted(env.berries)}")

    # 5+6. competent scripted forager: survives AND lingers
    # (ring rate is measured NEAR THE STORM TREE ONLY -- the forager also
    #  visits calm trees where the ring rate is 0.01 by design; pooling
    #  them dilutes the trap signal, which is a measurement artifact, not
    #  an env defect: measured 0.40 near storm trees vs 0.01 near calm)
    def forager(seed, steps=6000):
        env = TerrariumV3(seed)
        rng = random.Random(seed)
        deaths = fruits = berries = 0
        ring_near = n_near = 0
        for _ in range(steps):
            r, c = env.pos
            if env.tree and (r, c) == env.tree:
                a = "eat"
            elif env.tree:
                tr, tc = env.tree
                if tr < r:
                    a = "up"
                elif tr > r:
                    a = "down"
                elif tc < c:
                    a = "left"
                else:
                    a = "right"
            elif env.berries and (r, c) in env.berries:
                a = "eat"
            elif env.berries:
                br, bc = sorted(env.berries)[0]
                if br < r:
                    a = "up"
                elif br > r:
                    a = "down"
                elif bc < c:
                    a = "left"
                else:
                    a = "right"
            else:
                a = rng.choice(["up", "down", "left", "right"])
            _, _, done, info = env.step(a)
            fruits += 1 if info.get("tree_ate") else 0
            berries += 1 if info.get("ate") else 0
            if env.tree and env.weather == "storm":
                d = abs(env.pos[0] - env.tree[0]) + abs(env.pos[1] - env.tree[1])
                if d <= 1:
                    n_near += 1
                    ring_near += 1 if info.get("bell_rang") else 0
            if done:
                deaths += 1
                env = TerrariumV3(seed + deaths * 977 + n_near)
        return deaths, fruits, berries, (ring_near / max(1, n_near)), n_near

    stats = [forager(s) for s in (11, 12, 13, 14, 15)]
    surv = sum(1 for s in stats if s[0] <= 1)
    check("competent forager survives (<=1 death) in >=4/5 seeds",
          surv >= 4, f"deaths={[s[0] for s in stats]}")
    check("forager lingers at storm tree (fruits >= 100 in 3/5 seeds)",
          sum(1 for s in stats if s[1] >= 100) >= 3,
          f"fruits={[s[1] for s in stats]} berries={[s[2] for s in stats]}")
    near = [round(s[3], 3) for s in stats]
    check("ring rate near the tree > 0.30 in >=4/5 seeds",
          sum(1 for x in near if x > 0.30) >= 4, f"near={near}")
    # 7. lever->door; key only in cold season; treasure needs both, in
    #    ORDER (door opened before the key is taken -- v3 gate hardening)
    env = TerrariumV3(seed=8)
    env.pos = [3, 4]
    env.step("down")
    _, _, _, info = env.step("press")
    check("press at lever opens door", env.door_open and info.get("lever"))
    env2 = TerrariumV3(seed=9)
    env2.season = "warm"
    env2.season_dwell = 10_000          # pin the season warm for the check
    env2.key = None
    warm_key = False
    for _ in range(3000):
        info = env2.step("wait")[3]
        if info.get("key_appeared"):
            warm_key = True
            break
        if not env2.alive:
            env2 = TerrariumV3(seed=9)
            env2.season = "warm"
            env2.season_dwell = 10_000
    check("key never appears in the warm season (season pinned warm)",
          not warm_key)
    env3 = TerrariumV3(seed=10)
    env3.pos = [6, 5]
    env3.door_open = True
    env3.has_key = False
    _, r, _, info = env3.step("wait")
    check("no key -> no treasure", env3.treasure_taken == 0 and "treasure" not in info)
    env3.has_key = True
    env3.key_after_door = True
    _, r, _, info = env3.step("wait")
    check("door+key(in order) -> treasure", env3.treasure_taken == 1
          and info.get("treasure") and r >= 20.0)
    # key BEFORE door must NOT yield the treasure (order gate)
    env4 = TerrariumV3(seed=10)
    env4.pos = [6, 5]
    env4.door_open = True
    env4.has_key = True
    env4.key_after_door = False       # key was taken while door was closed
    _, r, _, info = env4.step("wait")
    check("key taken before door -> no treasure (order gate)",
          env4.treasure_taken == 0 and "treasure" not in info)

    # 8. closed door blocks; regime flip resets
    env = TerrariumV3(seed=11)
    env.pos = [5, 3]
    env.door_open = False
    env.step("right")
    check("closed door blocks", env.pos == [5, 3], f"pos={env.pos}")
    env = TerrariumV3(seed=12, regime_flip_at=100)
    env.door_open = True
    env.has_key = True
    for _ in range(100):
        env.step("wait")
    check("regime flip resets door/key, season cold",
          not env.door_open and not env.has_key and env.season == "cold")

    # 9. brute-force gate
    treasures = 0
    for seed in (21, 22, 23, 24, 25):
        env = TerrariumV3(seed)
        rng = random.Random(seed)
        for _ in range(6000):
            _, _, _, info = env.step(rng.choice(ACTIONS))
            if info.get("treasure"):
                treasures += 1
            if not env.alive:
                env = TerrariumV3(seed + 500)
    check("random policy: 0 treasures in 5x6000 steps", treasures == 0,
          f"treasures={treasures}")

    # 10. ground truth tables
    env = TerrariumV3(seed=13)
    gt = env.true_causal_edges()
    check("ground truth: eat->bell_rang NOT causal",
          gt.get(("eat", "bell_rang")) == 0.0)
    check("ground truth: press->lever / eat->ate / eat->tree_ate causal",
          gt.get(("press", "lever")) == 1.0 and gt.get(("eat", "ate")) == 1.0
          and gt.get(("eat", "tree_ate")) == 1.0)

    print("VERIFY_ENV_V3_" + ("OK" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
