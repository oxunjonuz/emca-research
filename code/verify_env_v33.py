"""Independent verification of TerrariumV33 (scarcity + dynamic costs).
Checks the world's mechanics WITHOUT any agent -- fresh process, no
imports from the agent modules. Every check pins energy where needed
and uses do()-style forced interventions.

V1  dynamic grasp cost: empty grasp costs 0.6 calm / 1.8 storm
V2  competent grasp still pays +18 (was 25), capped 60/storm
V3  altar offering: wait@altar costs 1.0; other waits free
V4  altar gray edge rates UNCHANGED: 0.28 wait vs 0.15 base (RR~1.9)
V5  oracle: P(ring|do(a)) equal for all actions (bell not causal)
V6  fury deepened: storm ambient -3.0 (net -3.4 with metabolism)
V7  berry budget cut: 2 warm / 1 cold (was 3/2)
V8  chain gates unchanged: brute force 0 treasures in 5x6000
V9  a competent forager SURVIVES the deficit (the world is harsh but
    not unsurvivable -- the point is stability testing, not extinction)
V10 chime far zone unchanged (>=5, >=4 from bell)
V11 tree_bare signal fires at the 60-fruit cap
V12 determinism: same seed -> identical trajectory hash
"""
import random
import sys

sys.path.insert(0, ".")

from env_terrarium_v33 import (
    TerrariumV33, GRASP_COST_CALM, GRASP_COST_STORM, WAIT_ALTAR_COST,
    STORM_FURY_V33, TREE_ENERGY_V33, BERRY_TARGET_WARM, BERRY_TARGET_COLD,
    MAX_STORM_FRUITS, ALTAR_POS, PATCH_POS,
)
from env_terrarium_v3 import ACTIONS, BELL_POS, MAP, W, H, EMPTY, TREASURE

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + ("  " + detail if detail else ""))


def force_weather(env, weather, dwell=10000):
    env.weather = weather
    env.weather_dwell = dwell


def pin_energy(env, e):
    env.energy = e


# ---------- V1: dynamic grasp cost ----------
# energy math (pinned, traced): a calm warm step applies ambient
# AMB_WARM-METAB = -0.1; an empty grasp adds -GRASP_COST. Expected
# calm grasp delta: -0.7; storm: ambient -3.4 + grasp -1.8 = -5.2.
env = TerrariumV33(7)
force_weather(env, "calm")
env.season = "warm"
pin_energy(env, 50.0)
env.pos = [5, 5]          # empty cell, no tree
e0 = env.energy
env.step("grasp")
cost_calm = -(env.energy - e0) - 0.1          # subtract the ambient
env2 = TerrariumV33(7)
force_weather(env2, "storm")
pin_energy(env2, 50.0)
env2.pos = [5, 5]
e0 = env2.energy
env2.step("grasp")
cost_storm = -(env2.energy - e0) - 3.4        # subtract the ambient
check("V1 dynamic grasp cost 0.6 calm / 1.8 storm",
      abs(cost_calm - GRASP_COST_CALM) < 1e-6
      and abs(cost_storm - GRASP_COST_STORM) < 1e-6,
      f"calm={cost_calm:.3f} storm={cost_storm:.3f}")

# ---------- V2: competent grasp pays +18, capped 60 ----------
env = TerrariumV33(7)
force_weather(env, "storm")
env.tree = (5, 5)
env.tree_fuel = 10000        # keep the tree alive across the cap probe
env.pos = [4, 5]          # adjacent
pin_energy(env, 50.0)
e0 = env.energy
_, r, _, info = env.step("grasp")
gain = env.energy - e0 + 3.4                 # add back the ambient
check("V2 competent grasp pays +18 and rewards 8",
      abs(gain - TREE_ENERGY_V33) < 1e-6 and r == 8.0
      and info.get("tree_gather"),
      f"gain={gain:.1f} r={r}")
# cap: 60 fruits per storm, then bare
env3 = TerrariumV33(7)
force_weather(env3, "storm")
env3.tree = (5, 5)
env3.tree_fuel = 10000
env3.pos = [4, 5]
pin_energy(env3, 100.0)
bare_seen = False
for i in range(70):
    pin_energy(env3, 100.0)
    _, r, _, info = env3.step("grasp")
    if info.get("tree_bare"):
        bare_seen = True
        break
check("V2b the tree goes BARE at the 60-fruit cap",
      bare_seen and env3.storm_fruits_this_storm == MAX_STORM_FRUITS,
      f"bare at storm_fruits={env3.storm_fruits_this_storm}")

# ---------- V3: altar offering ----------
env = TerrariumV33(7)
force_weather(env, "calm")
env.season = "warm"
env.pos = list(ALTAR_POS)
pin_energy(env, 50.0)
e0 = env.energy
env.step("wait")
cost_altar = -(env.energy - e0) - 0.1
check("V3 wait@altar costs the 1.0 offering",
      abs(cost_altar - WAIT_ALTAR_COST) < 1e-6,
      f"cost={cost_altar:.2f}")
env.pos = [3, 3]
pin_energy(env, 50.0)
e0 = env.energy
env.step("wait")
cost_elsewhere = -(env.energy - e0) - 0.1
check("V3b wait elsewhere is free",
      abs(cost_elsewhere) < 1e-6, f"cost={cost_elsewhere:.2f}")

# ---------- V4: altar gray edge rates unchanged ----------
N = 3000
env = TerrariumV33(11)
force_weather(env, "calm")
env.patch_berry = False
hits_wait = 0
for i in range(N):
    env.patch_berry = False
    env.pos = list(ALTAR_POS)
    pin_energy(env, 100.0)
    _, _, _, info = env.step("wait")
    if info.get("patch_berry"):
        hits_wait += 1
rate_wait = hits_wait / N
env = TerrariumV33(11)
force_weather(env, "calm")
hits_base = 0
for i in range(N):
    env.patch_berry = False
    env.pos = [3, 3]
    pin_energy(env, 100.0)
    _, _, _, info = env.step("wait")
    if info.get("patch_berry"):
        hits_base += 1
rate_base = hits_base / N
rr = rate_wait / max(rate_base, 1e-9)
check("V4 altar rates 0.28 vs 0.15, RR in the gray zone",
      0.20 <= rate_wait <= 0.36 and 0.09 <= rate_base <= 0.21
      and 1.4 <= rr <= 2.6,
      f"wait={rate_wait:.3f} base={rate_base:.3f} RR={rr:.2f}")

# ---------- V5: oracle P(ring|do(a)) equal for all actions ----------
# forced interventions: teleport the agent, force the weather cycle,
# pin energy so mortality cannot alias into the ring rate (the v3.2
# verifier lesson: unpinned oracles confuse cost-mortality with
# causality)
rates = {}
for action in ACTIONS:
    rng_hits = 0
    n = 0
    env = TerrariumV33(23)
    for i in range(4000):
        env.t += 0
        # advance weather by its own dynamics: step with 'wait' but
        # from a FIXED cell, then count rings only on action steps
        pin_energy(env, 100.0)
        env.pos = [3, 3]
        env.patch_berry = False
        _, _, _, info = env.step(action)
        n += 1
        if info.get("bell_rang"):
            rng_hits += 1
    rates[action] = rng_hits / n
mx = max(rates.values()); mn = min(rates.values())
check("V5 oracle: P(ring|do(a)) equal for all actions",
      mx - mn < 0.02, f"min={mn:.3f} max={mx:.3f} spread={mx-mn:.3f}")

# ---------- V6: fury deepened ----------
env = TerrariumV33(7)
force_weather(env, "storm")
pin_energy(env, 50.0)
env.pos = [3, 3]
e0 = env.energy
env.step("wait")
drain = e0 - env.energy
check("V6 storm ambient -3.0 (net -3.4 with metab)",
      abs(drain - 3.4) < 1e-6, f"drain={drain:.2f}")

# ---------- V7: berry budget ----------
env = TerrariumV33(7)
force_weather(env, "calm")
env.season = "warm"
env.berries = set()
for i in range(5):
    env._maintain_berries()
check("V7 warm berries capped at 2", len(env.berries) <= BERRY_TARGET_WARM,
      f"{len(env.berries)}")
env.season = "cold"
env.berries = set()
for i in range(5):
    env._maintain_berries()
check("V7b cold berries capped at 1", len(env.berries) <= BERRY_TARGET_COLD,
      f"{len(env.berries)}")

# ---------- V8: brute force 0 treasures ----------
treasures = 0
for seed in range(5):
    env = TerrariumV33(100 + seed)
    rng = random.Random(seed)
    for t in range(6000):
        if not env.alive:
            env = TerrariumV33(100 + seed + 1000 + t,
                               regime_flip_at=3000 + t + 1)
        a = rng.choice(ACTIONS)
        _, r, _, info = env.step(a)
        if info.get("treasure"):
            treasures += 1
check("V8 brute force: 0 treasures in 5x6000", treasures == 0,
      f"treasures={treasures}")

# ---------- V9: a competent forager survives ----------
# scripted policy: storm -> go to the tree and grasp; calm -> eat
# berries in the warm zone / cold zone; the deficit must be survivable
def competent_life(seed, steps=16000):
    env = TerrariumV33(seed)
    tot = 0.0
    deaths = 0
    for t in range(steps):
        if not env.alive:
            deaths += 1
            env = TerrariumV33(seed + 1000 + t, regime_flip_at=3000 + t + 1)
        r, c = env.pos
        o = env.obs()
        view = o["view"]
        # tree adjacent -> grasp
        if env.tree and abs(r - env.tree[0]) + abs(c - env.tree[1]) <= 1 \
                and env.storm_fruits_this_storm < MAX_STORM_FRUITS:
            a = "grasp"
        elif "eat" in o["afford"]:
            a = "eat"
        elif env.tree:
            # walk to the tree (greedy manhattan)
            dr = (env.tree[0] > r) - (env.tree[0] < r)
            dc = (env.tree[1] > c) - (env.tree[1] < c)
            a = "down" if dr > 0 else ("up" if dr < 0 else
                                       ("right" if dc > 0 else "left"))
        else:
            # walk to the nearest berry by scent-free greedy scan
            berries = sorted(env.berries) if env.berries else []
            if berries:
                br, bc = min(berries,
                             key=lambda b: abs(b[0]-r) + abs(b[1]-c))
                dr = (br > r) - (br < r)
                dc = (bc > c) - (bc < c)
                a = "down" if dr > 0 else ("up" if dr < 0 else
                                           ("right" if dc > 0 else "left"))
            else:
                a = "wait"
        _, rr, _, info = env.step(a)
        tot += rr
    return tot, deaths


deaths_list = []
for seed in (1, 2, 3):
    tot, d = competent_life(seed)
    deaths_list.append(d)
check("V9 competent forager survives the deficit (deaths <= 15/16k)",
      max(deaths_list) <= 15, f"deaths={deaths_list}")

# ---------- V10: chime far zone ----------
env = TerrariumV33(31)
far_ok = 0
far_n = 0
for i in range(2000):
    pin_energy(env, 100.0)
    force_weather(env, "storm")
    env.chime = None
    env.step("wait")
    if env.chime:
        far_n += 1
        r, c = env.chime
        if r >= 5 and abs(r - BELL_POS[0]) + abs(c - BELL_POS[1]) >= 4:
            far_ok += 1
check("V10 chimes land only in the far zone", far_n > 0 and far_ok == far_n,
      f"{far_ok}/{far_n}")

# ---------- V11: tree_bare fires ----------
env = TerrariumV33(7)
force_weather(env, "storm")
env.tree = (5, 5)
env.tree_fuel = 10000        # default fuel (60) expires before the cap
env.pos = [4, 5]
saw_bare = False
for i in range(70):
    pin_energy(env, 100.0)
    _, _, _, info = env.step("grasp")
    if info.get("tree_bare"):
        saw_bare = True
        break
check("V11 tree_bare info signal fires", saw_bare)

# ---------- V12: determinism ----------
h1, h2 = None, None
for run in (1, 2):
    env = TerrariumV33(99)
    rng = random.Random(5)
    acc = []
    for t in range(3000):
        if not env.alive:
            env = TerrariumV33(99 + 1000 + t, regime_flip_at=3000 + t + 1)
        a = rng.choice(ACTIONS)
        _, r, _, info = env.step(a)
        acc.append((round(r, 3), env.pos[0], env.pos[1],
                    tuple(sorted(k for k in info if info[k] is True))))
    h = hash(tuple(acc))
    if run == 1:
        h1 = h
    else:
        h2 = h
check("V12 determinism: identical trajectory hash", h1 == h2)

print()
print(f"VERIFY_V33: {len(PASS)} PASS, {len(FAIL)} FAIL")
if FAIL:
    print("FAILED:", FAIL)
    sys.exit(1)
