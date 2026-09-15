"""Independent ground-truth verification of TerrariumLinger (the simple env).

Does NOT import the agent. Verifies the ENVIRONMENT itself:
  1. weather trace visible: glow in storm, dark bell in calm
  2. tree spawns within 2 of the bell in EVERY storm (the trap geometry)
  3. interventional oracle: P(ring) equal for eat / grasp / wait / moves --
     the ring is a world event, never caused by any action
  4. tree never vanishes on eat (linger is possible), reward 8, energy
     static (no survival pressure in the simple env -- identifier question)
  5. calm berries bloom in the far shelter only, never near the bell
  6. no death: energy is static 80, done is always False (the simple env
     must not kill the question by starvation)
  7. linger actually happens for a competent forager: ring rate near the
     tree > 0.30 and fruits >= 200 (the trap must be reachable)
  8. ground-truth tables present; decoy edges marked non-causal
Run: python3 verify_env_linger.py
"""
import random
import sys

from env_linger import (
    TerrariumLinger, ACTIONS, BELL_POS, BELL_GLOW, BELL_DARK, TREE,
    BERRY, EMPTY, MAP, SHELTER,
)


def main():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
        ok = ok and cond

    # 1. weather trace visible
    env = TerrariumLinger(seed=1)
    env.pos = [2, 3]
    env.phase = "storm"
    o = env.obs()
    check("storm shows glowing bell", BELL_GLOW in o["view"], f"view={o['view']}")
    env.phase = "calm"
    env.tree = None
    o = env.obs()
    check("calm shows dark bell",
          BELL_DARK in o["view"] and BELL_GLOW not in o["view"],
          f"view={o['view']}")

    # 2. tree spawns within 2 of the bell in every storm
    env = TerrariumLinger(seed=2)
    storms = 0
    maxd = 0
    for _ in range(20000):
        env.step("wait")
        if env.tree:
            d = abs(env.tree[0] - BELL_POS[0]) + abs(env.tree[1] - BELL_POS[1])
            maxd = max(maxd, d)
            storms += 1
    check("tree always spawns within dist 2 of the bell", maxd <= 2,
          f"max_dist={maxd} storms_seen={storms}")

    # 3. interventional oracle: P(ring|do(a)) equal for all actions
    def ring_rate(action, steps=30000, seed=7):
        env = TerrariumLinger(seed)
        rang = n = 0
        for _ in range(steps):
            _, _, _, info = env.step(action)
            n += 1
            rang += 1 if info.get("bell_rang") else 0
        return rang / n
    rates = {a: ring_rate(a) for a in ("eat", "grasp", "wait", "up")}
    lo, hi = min(rates.values()), max(rates.values())
    check("oracle: P(ring|do(a)) equal for eat/grasp/wait/up",
          hi - lo <= 0.02, f"{ {k: round(v, 3) for k, v in rates.items()} }")

    # 4. tree never vanishes on eat; reward 8; energy static
    env = TerrariumLinger(seed=3)
    env.phase = "storm"
    env.tree = (4, 4)
    env.tree_fuel = 50
    env.pos = [4, 4]
    _, r, done, info = env.step("eat")
    o = env.obs()
    check("tree eat: flag, reward 8, tree persists, energy static 80",
          info.get("tree_ate") and r >= 8.0 and env.tree == (4, 4)
          and o["energy"] == 80 and not done,
          f"info={info} r={r} energy={o['energy']} done={done}")

    # 5. calm berries bloom in the far shelter only
    env = TerrariumLinger(seed=4)
    env.phase = "calm"
    env.berries.clear()
    env._maintain_berries()
    near_bell = [b for b in env.berries
                 if abs(b[0] - BELL_POS[0]) + abs(b[1] - BELL_POS[1]) <= 3]
    check("calm berries only in the far shelter",
          len(env.berries) >= 1 and not near_bell,
          f"berries={sorted(env.berries)} near_bell={near_bell}")

    # 6. no death: energy static, done always False (random policy)
    env = TerrariumLinger(seed=5)
    rng = random.Random(5)
    deaths = 0
    for _ in range(6000):
        o, _, done, info = env.step(rng.choice(ACTIONS))
        if done or info.get("died") or o["energy"] != 80:
            deaths += 1
    check("no death under a random policy (energy static)", deaths == 0,
          f"violations={deaths}")

    # 7. competent scripted forager lingers at the tree (the trap bites)
    def forager(seed, steps=16000):
        env = TerrariumLinger(seed)
        rng = random.Random(seed)
        fruits = berries = 0
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
            _, _, _, info = env.step(a)
            fruits += 1 if info.get("tree_ate") else 0
            berries += 1 if info.get("ate") else 0
            if env.tree:
                d = abs(env.pos[0] - env.tree[0]) + abs(env.pos[1] - env.tree[1])
                if d <= 1:
                    n_near += 1
                    ring_near += 1 if info.get("bell_rang") else 0
        return fruits, berries, (ring_near / max(1, n_near)), n_near

    stats = [forager(s) for s in (11, 12, 13, 14, 15)]
    check("forager lingers at the tree (fruits >= 200 in 3/5 seeds)",
          sum(1 for s in stats if s[0] >= 200) >= 3,
          f"fruits={[s[0] for s in stats]} berries={[s[1] for s in stats]}")
    near_rates = [round(s[2], 3) for s in stats]
    check("ring rate near the tree > 0.30 in >=4/5 seeds (trap reachable)",
          sum(1 for x in near_rates if x > 0.30) >= 4,
          f"near_rates={near_rates} n_near={[s[3] for s in stats]}")

    # 8. ground truth tables
    env = TerrariumLinger(seed=6)
    gt = env.true_causal_edges()
    check("ground truth: eat->bell_rang NOT causal",
          gt.get(("eat", "bell_rang")) == 0.0)
    check("ground truth: eat->ate / eat->tree_ate causal",
          gt.get(("eat", "ate")) == 1.0 and gt.get(("eat", "tree_ate")) == 1.0)

    print("VERIFY_ENV_LINGER_" + ("OK" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
