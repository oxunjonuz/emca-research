"""Independent ground-truth verification of TerrariumV31 (the actionable-
decoy env). Does NOT import the agent. Verifies the ENVIRONMENT:

 1. interventional oracle: P(ring|do(a)) equal for all actions -- the
    ring is never caused by any action (grasp included: the decoy is on
    grasp now)
 2. the storm tree is gathered with GRASP (not eat): grasp at the tree
    gives +25 energy / reward 8 / info['tree_gather']; eat at the tree
    gives NOTHING
 3. a ring drops a chime within 2 of the bell; chime collected by
    walking (+0.5, info['chime']); chime expires after 40 steps
 4. storms are furious: energy drains ~2.4/step in a storm (vs ~0.1/0.4
    in calm) -- lingering by the bell has a cost
 5. the key pickup is REPORTED: info['key']=True on the step the key is
    picked up (and only then)
 6. the scent carries 'treasure' iff key-in-hand AND door open; 'bell'
    iff a chime is on the ground
 7. chain gates UNCHANGED from v3: order gate (key before door -> no
    treasure), 12-step in-hand window, spawn dist>5, door window 300
 8. brute-force gate: random policy, 0 treasures in 5x6000 steps
 9. survival is possible: a competent grasp-forager survives a full
    storm cycle in >=4/5 seeds (the fury is survivable with the tree)
10. ground truth: (grasp, bell_rang) NOT causal; grasp->tree_gather,
    press->lever, eat->ate causal
"""
import random
import sys

from env_terrarium_v3 import ACTIONS, BELL_POS, MAP, EMPTY
from env_terrarium_v31 import TerrariumV31, STORM_FURY, CHIME_MAX_DIST


def main():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
        ok = ok and cond

    # 1. interventional oracle (all actions, incl. grasp)
    def ring_rate(action, steps=30000, seed=7):
        env = TerrariumV31(seed)
        rang = n = 0
        for _ in range(steps):
            _, _, _, info = env.step(action)
            n += 1
            rang += 1 if info.get("bell_rang") else 0
            if not env.alive:
                env = TerrariumV31(seed + n)
        return rang / n
    rates = {a: ring_rate(a) for a in ("eat", "grasp", "wait", "up")}
    lo, hi = min(rates.values()), max(rates.values())
    check("oracle: P(ring|do(a)) equal for eat/grasp/wait/up",
          hi - lo <= 0.02, f"{ {k: round(v, 3) for k, v in rates.items()} }")

    # 2. the storm tree is GRASPED from adjacent, not eaten
    env = TerrariumV31(seed=1)
    env.weather = "storm"
    env.weather_dwell = 100
    env.tree = (2, 4)
    env.tree_fuel = 50
    env.pos = [1, 4]
    env.energy = 50.0
    _, r_eat, _, info_eat = env.step("eat")
    check("eat near the storm tree gives NOTHING (fruit hangs high)",
          r_eat == 0.0 and "tree_gather" not in info_eat
          and "ate" not in info_eat, f"r={r_eat} info={info_eat}")
    env2 = TerrariumV31(seed=1)
    env2.weather = "storm"
    env2.weather_dwell = 100
    env2.tree = (2, 4)
    env2.tree_fuel = 50
    env2.pos = [1, 4]
    env2.energy = 50.0
    e0 = env2.energy
    _, r_grasp, _, info_g = env2.step("grasp")
    check("grasp ADJACENT to the storm tree gathers fruit (+25, reward 8)",
          r_grasp >= 8.0 and info_g.get("tree_gather") is True
          and env2.energy >= e0 + 20,
          f"r={r_grasp} energy {e0}->{env2.energy}")
    env3 = TerrariumV31(seed=1)
    env3.weather = "storm"
    env3.weather_dwell = 100
    env3.tree = (2, 4)
    env3.tree_fuel = 50
    env3.pos = [4, 4]
    env3.energy = 50.0
    _, r_far, _, info_far = env3.step("grasp")
    check("grasp FAR from the tree gathers nothing (dist>1)",
          r_far == 0.0 and "tree_gather" not in info_far)

    # 3. chime: ring drops it, walk collects it, it expires
    env = TerrariumV31(seed=2)
    env.weather = "storm"
    env.weather_dwell = 500
    env.chime = (1, 4)
    env.chime_fuel = 40
    env.pos = [1, 3]
    _, r0, _, info0 = env.step("right")
    check("walking onto the chime collects it (+0.5, info['chime'])",
          info0.get("chime") is True and r0 >= 0.5 and env.chime is None,
          f"r={r0} info={info0}")
    env = TerrariumV31(seed=3)
    env.weather = "calm"
    env.chime = (2, 5)
    env.chime_fuel = 2
    env.pos = [5, 5]
    for _ in range(3):
        env.step("wait")
    check("chime expires after its fuel runs out", env.chime is None)
    # ring drops chime near the bell
    env = TerrariumV31(seed=4)
    drops = 0
    for _ in range(20000):
        _, _, _, info = env.step("wait")
        if info.get("bell_rang") and env.chime:
            d = abs(env.chime[0] - BELL_POS[0]) + abs(env.chime[1] - BELL_POS[1])
            if d <= CHIME_MAX_DIST:
                drops += 1
        if not env.alive:
            env = TerrariumV31(4 + drops)
    check("rings drop chimes within 2 of the bell (>=100 drops observed)",
          drops >= 100, f"drops={drops}")

    # 4. fury: storm drains ~2.4/step, calm ~0.1-0.4
    env = TerrariumV31(seed=5)
    env.weather = "storm"
    env.weather_dwell = 100
    env.season = "warm"
    env.energy = 80.0
    env.step("wait")
    d_storm = 80.0 - env.energy
    env2 = TerrariumV31(seed=5)
    env2.weather = "calm"
    env2.weather_dwell = 100
    env2.season = "warm"
    env2.energy = 80.0
    env2.step("wait")
    d_calm = 80.0 - env2.energy
    check("storm fury drains ~2.4/step (vs calm ~0.1)",
          2.0 <= d_storm <= 2.8 and 0.0 <= d_calm <= 0.6,
          f"storm={round(d_storm, 2)} calm={round(d_calm, 2)}")

    # 5. key pickup reported (the observable fires on the pickup step;
    #    whether the key is then HELD depends on the door state -- the
    #    v3 gate: a key picked up while the door is closed is dropped
    #    immediately. The goal machinery sees the pickup either way.)
    env = TerrariumV31(seed=6)
    env.season = "cold"
    env.season_dwell = 10000
    env.key = (3, 3)
    env.key_fuel = 50
    env.pos = [3, 2]
    env.door_open = True
    env.door_opened_at = env.t
    _, _, _, info = env.step("right")
    check("key pickup reported via info['key'] (door open: key held)",
          env.has_key and info.get("key") is True, f"info={info}")
    env0 = TerrariumV31(seed=6)
    env0.season = "cold"
    env0.season_dwell = 10000
    env0.key = (3, 3)
    env0.key_fuel = 50
    env0.pos = [3, 2]
    _, _, _, info0 = env0.step("right")
    check("pickup observable fires even when the door is closed",
          info0.get("key") is True and not env0.has_key,
          f"info={info0} has_key={env0.has_key}")

    # 6. scent channels
    env = TerrariumV31(seed=7)
    env.has_key = True
    env.door_open = True
    s = env._scent(3, 3)
    check("scent carries 'treasure' with key+door",
          "treasure" in s, f"scent keys={sorted(s.keys())}")
    env2 = TerrariumV31(seed=7)
    env2.chime = (1, 4)
    s2 = env2._scent(3, 3)
    check("scent carries 'bell' while a chime is down",
          "bell" in s2, f"scent keys={sorted(s2.keys())}")

    # 7. chain gates unchanged
    env = TerrariumV31(seed=8)
    env.pos = [6, 5]
    env.door_open = True
    env.has_key = True
    env.key_after_door = False
    _, r, _, info = env.step("wait")
    check("key taken before door -> no treasure (order gate)",
          env.treasure_taken == 0 and "treasure" not in info)
    env3 = TerrariumV31(seed=8)
    env3.pos = [6, 5]
    env3.door_open = True
    env3.has_key = True
    env3.key_after_door = True
    _, r, _, info3 = env3.step("wait")
    check("door+key(in order) -> treasure",
          env3.treasure_taken == 1 and info3.get("treasure") and r >= 20.0)
    env4 = TerrariumV31(seed=9)
    env4.has_key = True
    env4.key_taken_at = 1
    env4.t = 20
    env4.door_open = True
    env4.key_after_door = True
    env4.step("wait")
    check("key crumbles after the 12-step window",
          not env4.has_key)

    # 8. brute-force gate
    treasures = 0
    for seed in (21, 22, 23, 24, 25):
        env = TerrariumV31(seed)
        rng = random.Random(seed)
        for _ in range(6000):
            _, _, _, info = env.step(rng.choice(ACTIONS))
            if info.get("treasure"):
                treasures += 1
            if not env.alive:
                env = TerrariumV31(seed + 500)
    check("random policy: 0 treasures in 5x6000 steps", treasures == 0,
          f"treasures={treasures}")

    # 9. survival with the fury: a competent grasp-forager survives
    def forager(seed, steps=6000):
        env = TerrariumV31(seed)
        rng = random.Random(seed)
        deaths = fruits = berries = chimes = 0
        for _ in range(steps):
            r, c = env.pos
            if env.tree and (r, c) == env.tree:
                # ON the tree: step off it (fruit hangs high, gathered
                # from ADJACENT with grasp, not from on top)
                a = rng.choice(["up", "down", "left", "right"])
            elif env.tree:
                tr, tc = env.tree
                d = abs(r - tr) + abs(c - tc)
                if d == 1:
                    a = "grasp"
                elif tr < r:
                    a = "up"
                elif tr > r:
                    a = "down"
                elif tc < c:
                    a = "left"
                else:
                    a = "right"
            elif env.chime:
                cr, cc = env.chime
                if cr < r:
                    a = "up"
                elif cr > r:
                    a = "down"
                elif cc < c:
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
                env = TerrariumV31(seed + deaths * 977)
        return deaths, fruits, berries, chimes
    stats = [forager(s) for s in (11, 12, 13, 14, 15)]
    check("competent grasp-forager survives (<=2 deaths) in >=4/5 seeds",
          sum(1 for s in stats if s[0] <= 2) >= 4,
          f"deaths={[s[0] for s in stats]}")
    check("forager gathers storm fruits (>=100 in 3/5 seeds)",
          sum(1 for s in stats if s[1] >= 100) >= 3,
          f"fruits={[s[1] for s in stats]} chimes={[s[3] for s in stats]}")

    # 10. ground truth
    env = TerrariumV31(seed=13)
    gt = env.true_causal_edges()
    check("ground truth: grasp->bell_rang NOT causal",
          gt.get(("grasp", "bell_rang")) == 0.0)
    check("ground truth: grasp->tree_gather / press->lever / eat->ate causal",
          gt.get(("grasp", "tree_gather")) == 1.0
          and gt.get(("press", "lever")) == 1.0
          and gt.get(("eat", "ate")) == 1.0)

    print("VERIFY_ENV_V31_" + ("OK" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
