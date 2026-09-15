"""Independent ground-truth verification of TerrariumV32 (separated
geometry + gray-zone altar). Does NOT import the agent.

 1. interventional oracle: P(ring|do(a)) equal for all actions -- the
    ring is never caused by any action (grasp included)
 2. chimes land ONLY in the far zone (r>=5, >=4 from the bell), never
    near the storm tree / bell
 3. empty grasps COST energy (0.6); grasping the storm tree pays +25
 4. the altar: wait@altar sprouts a patch berry at P~0.28; other cells
    / other actions sprout at the base rate ~0.15; measured RR in
    [1.5, 2.3] (the gray zone 1<=RR<2 by design)
 5. the patch berry is a normal berry: eat gives +10 energy, reward 1,
    info['ate'] + info['patch_ate']; it rots after 60 steps
 6. the altar is visible (tile 'A') and has a scent channel
 7. chain gates unchanged: order gate, 12-step window, door window 300
 8. brute force: random policy, 0 treasures in 5x6000
 9. survival: a competent grasp-forager survives (<=2 deaths) in >=4/5
    seeds; the fury + grasp cost do not make the world unsurvivable
10. ground truth table
"""
import random
import sys

from env_terrarium_v3 import ACTIONS, BELL_POS, MAP, EMPTY
from env_terrarium_v32 import (
    TerrariumV32, ALTAR_POS, PATCH_POS, GRASP_COST, CHIME_FAR_CELLS,
    PATCH_BERRY_P, BASE_BERRY_P,
)


def main():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
        ok = ok and cond

    # 1. interventional oracle (all actions) -- SURVIVAL-PINNED: the
    #    grasp cost kills a do(grasp) agent faster, and every death
    #    respawns into calm weather (a mortality asymmetry, not a bell
    #    asymmetry). Pinning energy isolates the bell itself.
    def ring_rate(action, steps=30000, seed=7):
        env = TerrariumV32(seed)
        rang = n = 0
        for _ in range(steps):
            env.energy = 60.0          # pin: no deaths, no respawn bias
            _, _, _, info = env.step(action)
            n += 1
            rang += 1 if info.get("bell_rang") else 0
        return rang / n
    rates = {a: ring_rate(a) for a in ("eat", "grasp", "wait", "up")}
    lo, hi = min(rates.values()), max(rates.values())
    check("oracle: P(ring|do(a)) equal for eat/grasp/wait/up",
          hi - lo <= 0.02, f"{ {k: round(v, 3) for k, v in rates.items()} }")

    # 2. chimes land only in the far zone
    env = TerrariumV32(seed=4)
    drops = far = near_tree = dist2 = 0
    for _ in range(40000):
        _, _, _, info = env.step("wait")
        if env.chime is not None and info.get("bell_rang"):
            drops += 1
            r, c = env.chime
            if r >= 5 and abs(r - BELL_POS[0]) + abs(c - BELL_POS[1]) >= 4:
                far += 1
            if env.tree:
                dt = abs(r - env.tree[0]) + abs(c - env.tree[1])
                if dt <= 1:
                    near_tree += 1
                if dt == 2:
                    dist2 += 1
        if not env.alive:
            env = TerrariumV32(4 + drops)
    check("rings drop chimes only in the FAR zone (r>=5, dist>=4)",
          drops >= 100 and far == drops,
          f"drops={drops} far={far} near_tree={near_tree}")
    check("chimes never land within 1 of the storm tree (the forage cell)",
          near_tree == 0,
          f"within1={near_tree} dist2={dist2} (dist-2 cells are the cold "
          f"berry rows -- the far zone itself; the tree is gathered from "
          f"dist<=1)")

    # 3. grasp cost vs tree payoff
    env = TerrariumV32(seed=1)
    env.weather = "storm"
    env.weather_dwell = 100
    env.pos = [4, 4]
    env.energy = 50.0
    env.step("grasp")
    d_empty = 50.0 - env.energy
    check("empty grasp costs energy (fury + 0.6)", 2.4 <= d_empty <= 3.4,
          f"drain={round(d_empty, 2)}")
    env2 = TerrariumV32(seed=1)
    env2.weather = "storm"
    env2.weather_dwell = 100
    env2.tree = (2, 4)
    env2.tree_fuel = 50
    env2.pos = [1, 4]
    env2.energy = 50.0
    e0 = env2.energy
    _, r_g, _, info_g = env2.step("grasp")
    check("grasp ADJACENT to the storm tree pays (+25, reward 8, no cost)",
          r_g >= 8.0 and info_g.get("tree_gather") is True
          and env2.energy >= e0 + 20,
          f"r={r_g} energy {e0}->{round(env2.energy, 1)}")

    # 4. the altar rates (SURVIVAL-PINNED scripted alternation: the
    #    harness pins energy so death/respawn never biases the weather
    #    mix; the patch is kept empty by direct reset after counting)
    def altar_rate(at_altar, steps=6000, seed=11):
        env = TerrariumV32(seed)
        sprouts = n = 0
        cell = ALTAR_POS if at_altar else (6, 6)
        env.pos = list(cell)
        for _ in range(steps):
            env.energy = 60.0          # pin: no deaths, no respawn bias
            env.pos = list(cell)       # pin: stay on the trial cell
            _, _, _, info = env.step("wait")
            n += 1
            sprouts += 1 if info.get("patch_berry") else 0
            if env.patch_berry:
                env.patch_berry = False
                env.patch_fuel = 0
        return sprouts / n
    p_altar = altar_rate(True)
    p_base = altar_rate(False)
    rr = p_altar / p_base if p_base > 0 else float("inf")
    check("wait@altar sprouts at ~0.28", 0.22 <= p_altar <= 0.34,
          f"p_altar={round(p_altar, 3)}")
    check("base sprout rate ~0.15 at a neutral cell",
          0.11 <= p_base <= 0.19, f"p_base={round(p_base, 3)}")
    check("measured RR in the gray zone [1.5, 2.3]", 1.5 <= rr <= 2.3,
          f"RR={round(rr, 2)}")

    # 5. the patch berry is a normal berry
    env = TerrariumV32(seed=2)
    env.patch_berry = True
    env.patch_fuel = 60
    env.pos = [7, 3]
    env.energy = 50.0
    e0 = env.energy
    _, r_e, _, info_e = env.step("eat")
    check("eat on the patch berry: +10 energy, reward 1, info['patch_ate']",
          r_e >= 1.0 and info_e.get("ate") and info_e.get("patch_ate")
          and env.energy >= e0 + 9 and not env.patch_berry)
    env = TerrariumV32(seed=3)
    env.patch_berry = True
    env.patch_fuel = 2
    env.pos = [5, 5]
    for _ in range(3):
        env.step("wait")
    check("patch berry rots after its fuel", not env.patch_berry)

    # 6. altar visible + scent
    env = TerrariumV32(seed=7)
    env.pos = [6, 2]
    o = env.obs()
    check("altar tile 'A' visible from (6,2)", "A" in o["view"],
          f"view={o['view']}")
    s = env._scent(3, 3)
    check("scent carries 'altar'", "altar" in s)

    # 7. chain gates unchanged
    env = TerrariumV32(seed=8)
    env.pos = [6, 5]
    env.door_open = True
    env.has_key = True
    env.key_after_door = False
    env.step("wait")
    check("key taken before door -> no treasure (order gate)",
          env.treasure_taken == 0)
    env3 = TerrariumV32(seed=8)
    env3.pos = [6, 5]
    env3.door_open = True
    env3.has_key = True
    env3.key_after_door = True
    _, r, _, info3 = env3.step("wait")
    check("door+key(in order) -> treasure",
          env3.treasure_taken == 1 and info3.get("treasure") and r >= 20.0)
    env4 = TerrariumV32(seed=9)
    env4.has_key = True
    env4.key_taken_at = 1
    env4.t = 20
    env4.door_open = True
    env4.key_after_door = True
    env4.step("wait")
    check("key crumbles after the 12-step window", not env4.has_key)

    # 8. brute-force gate
    treasures = 0
    for seed in (21, 22, 23, 24, 25):
        env = TerrariumV32(seed)
        rng = random.Random(seed)
        for _ in range(6000):
            _, _, _, info = env.step(rng.choice(ACTIONS))
            if info.get("treasure"):
                treasures += 1
            if not env.alive:
                env = TerrariumV32(seed + 500)
    check("random policy: 0 treasures in 5x6000 steps", treasures == 0,
          f"treasures={treasures}")

    # 9. survival with fury + grasp cost
    def forager(seed, steps=6000):
        env = TerrariumV32(seed)
        rng = random.Random(seed)
        deaths = fruits = berries = chimes = 0
        for _ in range(steps):
            r, c = env.pos
            if env.tree:
                tr, tc = env.tree
                d = abs(r - tr) + abs(c - tc)
                if d == 1:
                    a = "grasp"
                elif d == 0:
                    a = rng.choice(["up", "down", "left", "right"])
                elif tr < r:
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
            fruits += 1 if info.get("tree_gather") else 0
            berries += 1 if info.get("ate") else 0
            chimes += 1 if info.get("chime") else 0
            if done:
                deaths += 1
                env = TerrariumV32(seed + deaths * 977)
        return deaths, fruits, berries, chimes
    stats = [forager(s) for s in (11, 12, 13, 14, 15)]
    check("competent grasp-forager survives (<=2 deaths) in >=4/5 seeds",
          sum(1 for s in stats if s[0] <= 2) >= 4,
          f"deaths={[s[0] for s in stats]}")
    check("forager gathers storm fruits (>=100 in 3/5 seeds)",
          sum(1 for s in stats if s[1] >= 100) >= 3,
          f"fruits={[s[1] for s in stats]}")

    # 10. ground truth
    env = TerrariumV32(seed=13)
    gt = env.true_causal_edges()
    check("ground truth: grasp->bell_rang NOT causal",
          gt.get(("grasp", "bell_rang")) == 0.0)
    check("ground truth: wait->patch_berry TRUE weak cause",
          gt.get(("wait", "patch_berry")) == 1.0)
    check("ground truth: grasp->tree_gather / press->lever / eat->ate causal",
          gt.get(("grasp", "tree_gather")) == 1.0
          and gt.get(("press", "lever")) == 1.0
          and gt.get(("eat", "ate")) == 1.0)

    print("VERIFY_ENV_V32_" + ("OK" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
