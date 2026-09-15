"""Independent verification of TerrariumV5's mechanics: the do-oracle
(wait is a REAL cause; every other action is equal; the flow is
place-bound), the leak/cadence arithmetic (blind patience never fills),
the exploit (pure waiting blooms the lotus), brute force, determinism.
No agent code is imported -- the world is driven directly."""
import random
from collections import defaultdict

from env_terrarium_v5 import (
    TerrariumV5, SPRING_POS, FLOW_BACKGROUND, FLOW_WAIT,
    LOTUS_NEED, DECAY_TICKS,
)
from env_terrarium_v3 import ACTIONS, MAP, W, H

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + " " + name
          + ("  " + detail if detail else ""))


def pin_in_aura(env, cell=None):
    """Pin the agent inside the spring aura, energy high, calm warm."""
    if cell is None:
        for cand in ((7, 6), (7, 8), (6, 7), (6, 6), (6, 8), (7, 7)):
            if MAP[cand[0]][cand[1]] == ".":
                env.pos = list(cand)
                return
    else:
        env.pos = list(cell)
    env.weather = "calm"
    env.weather_dwell = 10 ** 9
    env.season = "warm"
    env.season_dwell = 10 ** 9
    env.energy = 90.0
    env.torch_lit = False


# ---------------------------------------------------------------------------
# NV1. The do-oracle: P(spring_flow | do(a)) -- wait is a REAL cause,
#      every other action is EQUAL at the background rate, and the flow
#      is PLACE-BOUND (outside the aura nothing flows).
def oracle_spring():
    counts = {a: [0, 0] for a in ACTIONS}
    for seed in range(3):
        for a in ACTIONS:
            for rep in range(400):
                env = TerrariumV5(seed * 977 + rep)   # FRESH rng each trial
                pin_in_aura(env)
                o, r, done, info = env.step(a)
                counts[a][1] += 1
                if info.get("spring_flow") is True:
                    counts[a][0] += 1
    ps = {a: c[0] / c[1] for a, c in counts.items()}
    others = [p for a, p in ps.items() if a != "wait"]
    spread = max(others) - min(others)
    check("NV1a do-oracle: wait raises the flow (the TRUE cause)",
          ps["wait"] > 0.40, f"P(flow|wait)={ps['wait']:.3f}")
    check("NV1b do-oracle: every other action EQUAL at the background",
          spread <= 0.06 and abs(sum(others) / len(others)
                                 - FLOW_BACKGROUND) <= 0.05,
          f"spread={spread:.3f} mean_others={sum(others)/len(others):.3f} "
          f"(design {FLOW_BACKGROUND})")
    # place-bound: outside the aura no action flows
    env = TerrariumV5(5)
    env.pos = [3, 3]
    env.weather = "calm"
    env.weather_dwell = 10 ** 9
    env.season = "warm"
    env.season_dwell = 10 ** 9
    env.energy = 90.0
    flowed = 0
    for rep in range(200):
        o, r, done, info = env.step("wait")
        if info.get("spring_flow"):
            flowed += 1
    check("NV1c the flow is place-bound (0 outside the aura)",
          flowed == 0, f"flows at (3,3)={flowed}/200")
    # weather-free: the spring ignores the weather
    env = TerrariumV5(5)
    pin_in_aura(env)
    env.weather = "storm"
    env.weather_dwell = 10 ** 9
    env.tree = (1, 4)      # keep the storm tree away from the aura
    env.tree_fuel = 10 ** 9
    env.energy = 95.0
    storm_flows = 0
    for rep in range(200):
        env.energy = 95.0
        o, r, done, info = env.step("wait")
        if info.get("spring_flow"):
            storm_flows += 1
    check("NV1d the spring is weather-free (storm rate ~ wait rate)",
          storm_flows / 200 > 0.40,
          f"P(flow|wait,storm)={storm_flows/200:.3f}")


# ---------------------------------------------------------------------------
# NV2. The leak arithmetic: the background NEVER fills the pool.
def leak_background():
    fills = 0
    for seed in range(5):
        env = TerrariumV5(seed)
        pin_in_aura(env)
        for rep in range(3000):
            env.energy = 90.0
            o, r, done, info = env.step("grasp")   # any non-wait action
            if info.get("lotus_bloom"):
                fills += 1
    check("NV2 the background never blooms the lotus (0 in 5x3000)",
          fills == 0, f"blooms={fills}")


# ---------------------------------------------------------------------------
# NV3. Blind patience (the shared cadence: 1 wait in 3, else a random
#      non-wait action) never fills -- the pool is a p>0.5 threshold.
def leak_cadence():
    fills = 0
    peaks = []
    for seed in range(5):
        env = TerrariumV5(seed)
        pin_in_aura(env)
        peak = 0
        i = 0
        for rep in range(6000):
            env.energy = 90.0
            a = "wait" if i % 3 == 0 else "grasp"
            i += 1
            o, r, done, info = env.step(a)
            peak = max(peak, env.pool)
            if info.get("lotus_bloom"):
                fills += 1
        peaks.append(peak)
    check("NV3 the 1/3-wait cadence never blooms (p=0.30 < leak)",
          fills == 0, f"blooms={fills} peak pools={peaks} "
          f"(need {LOTUS_NEED})")


# ---------------------------------------------------------------------------
# NV4. The exploit: PURE waiting blooms the lotus (12 flows, ~40 waits).
def exploit_wait():
    blooms = 0
    waits_needed = []
    for seed in range(5):
        env = TerrariumV5(seed)
        pin_in_aura(env)
        waits = 0
        for rep in range(2000):
            env.energy = 90.0
            o, r, done, info = env.step("wait")
            waits += 1
            if info.get("lotus_bloom"):
                blooms += 1
                waits_needed.append(waits)
                break
    check("NV4 pure waiting blooms the lotus (5/5 seeds)",
          blooms == 5, f"blooms={blooms}/5 waits={waits_needed}")


# ---------------------------------------------------------------------------
# NV5. Brute force: random lives never bloom (and rarely even reach
#      the aura productively).
def brute_force():
    blooms = 0
    for seed in range(1, 6):
        env = TerrariumV5(seed)
        rng = random.Random(seed)
        for t in range(6000):
            a = rng.choice(ACTIONS)
            o, r, done, info = env.step(a)
            if info.get("lotus_bloom"):
                blooms += 1
            if info.get("died"):
                env = TerrariumV5(seed * 100 + t)
    check("NV5 brute force never blooms the lotus (0 in 5x6000)",
          blooms == 0, f"blooms={blooms}")


# ---------------------------------------------------------------------------
# NV6. The lotus is food: +30 energy, +8 reward, eatable, expires.
def lotus_food():
    env = TerrariumV5(9)
    pin_in_aura(env, (7, 7))       # ON the spring cell
    env.energy = 50.0
    # force a lotus
    env.lotus = True
    env.lotus_fuel = 80
    e0 = env.energy
    o, r, done, info = env.step("eat")
    # the ambient applies on top of the +30 (calm warm: +0.3 - 0.4 = -0.1)
    from env_terrarium_v3 import AMB_WARM, METAB
    amb = AMB_WARM - METAB
    check("NV6 the lotus pays +30 energy / +8 reward",
          info.get("lotus") is True
          and abs((env.energy - e0) - (30.0 + amb)) < 1e-6
          and abs(r - 8.0) < 1e-6,
          f"energy_delta={env.energy-e0:.1f} (30 + ambient {amb:+.1f}) "
          f"reward={r:.1f}")
    # expiry
    env2 = TerrariumV5(9)
    pin_in_aura(env2, (7, 6))
    env2.lotus = True
    env2.lotus_fuel = 3
    for i in range(4):
        o, r, done, info = env2.step("wait")
    check("NV6b the lotus expires (80 steps)",
          env2.lotus is False, f"lotus={env2.lotus}")


# ---------------------------------------------------------------------------
# NV7. Determinism: same seed, same scripted action stream -> identical
#      info/reward stream.
def determinism():
    outs = []
    for rep in range(2):
        env = TerrariumV5(42)
        rng = random.Random(7)
        h = []
        for t in range(2000):
            a = rng.choice(ACTIONS)
            o, r, done, info = env.step(a)
            h.append((round(r, 6),
                      tuple(sorted(k for k in info if info[k] is True))))
            if done:
                env = TerrariumV5(42 * 3 + t)
        outs.append(h)
    check("NV7 determinism (2 fresh envs, identical streams)",
          outs[0] == outs[1])


# ---------------------------------------------------------------------------
# NV8. The mask, measured on a scripted trajectory (the identifier
#      bait check, no agent code): a forager that crosses the aura and
#      waits 1/3 of the time there (the shared cadence) files data in
#      which the pooled contrast REJECTS the true edge while the
#      stratified contrast (within-ctx) ACCEPTS it.
def mask_measured():
    # build a synthetic ctx_ae-like table from a scripted trajectory that
    # matches what a BLIND arm's machinery actually files: the goal
    # pursuit brings it to the aura and the shared cadence explores
    # actions there (1/3 waits), but its normal life (foraging, roaming,
    # other goals) keeps ~90% of its steps -- and ~90% of its waits --
    # OUTSIDE the aura. W (the in-aura share of waits) ~ 0.08: the
    # dilution a real blind arm files.
    tab = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # ctx->a->[y,n]
    rng = random.Random(3)
    for step in range(60000):
        in_aura = rng.random() < 0.08
        if in_aura:
            a = "wait" if rng.random() < 1 / 3 else rng.choice(
                ["up", "down", "left", "right", "grasp"])
            p = FLOW_WAIT if a == "wait" else FLOW_BACKGROUND
        else:
            a = rng.choice(ACTIONS)
            p = 0.0
        ctx = "aura" if in_aura else "outside"
        hit = rng.random() < p
        tab[ctx][a][1] += 1
        if hit:
            tab[ctx][a][0] += 1
    # pooled v2.1 (the REAL EMCA rule): rate_a = wait's marginal over
    # ALL its trials; pooled_others = the others' rate over the
    # contexts where WAIT was tried AND the effect occurred -- the
    # aura dominates that set (the outside never flows)
    y_a = tab["aura"]["wait"][0] + tab["outside"]["wait"][0]
    n_a = tab["aura"]["wait"][1] + tab["outside"]["wait"][1]
    rate_a = y_a / n_a
    oy = on = 0
    for a2, (y, n) in tab["aura"].items():
        if a2 != "wait":
            oy += y
            on += n
    pooled = oy / on if on else 0.0
    check("NV8a the mask: pooled contrast REJECTS the true edge",
          rate_a - pooled < 0.02,
          f"rate_a={rate_a:.3f} pooled_others={pooled:.3f} "
          f"contrast={rate_a-pooled:+.3f}")
    # spec gate: pooled_others > spec_cap 0.10
    check("NV8b the mask: spec gate REJECTS (pooled_others > 0.10)",
          pooled > 0.10, f"pooled_others={pooled:.3f}")
    # assoc 0.5: the marginal < 0.5
    check("NV8c the mask: assoc(0.5) blind (marginal < 0.5)",
          rate_a < 0.5, f"rate_a={rate_a:.3f}")
    # stratified v2.5c: exposure-weighted rate_o within wait's contexts
    y_w = n_w = 0.0
    for ctx in tab:
        if "wait" in tab[ctx]:
            n_a_ctx = tab[ctx]["wait"][1]
            n_o = sum(v[1] for a2, v in tab[ctx].items() if a2 != "wait")
            y_o = sum(v[0] for a2, v in tab[ctx].items() if a2 != "wait")
            if n_o > 0:
                y_w += n_a_ctx * (y_o / n_o)
                n_w += n_a_ctx
    rate_o = y_w / n_w if n_w > 0 else None
    rr = rate_a / rate_o if rate_o else float("inf")
    check("NV8d the reveal: stratified RR >= 2 ACCEPTS the true edge",
          rr >= 2.0, f"rate_a={rate_a:.3f} rate_o={rate_o:.3f} RR={rr:.2f}")


if __name__ == "__main__":
    oracle_spring()
    leak_background()
    leak_cadence()
    exploit_wait()
    brute_force()
    lotus_food()
    determinism()
    mask_measured()
    print(f"VERIFY_V5: {len(PASS)} PASS, {len(FAIL)} FAIL")
    if FAIL:
        print("FAILED:", FAIL)
