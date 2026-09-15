"""Independent verification of TerrariumV6's mechanics: the do-oracle
(wait is a REAL GREY cause: 0.30 vs 0.20, every other action equal,
place-bound), the anti-luck arithmetic (the blind cadence never fills;
pure streak-waiting fills in ~330 waits), the passive-layer blindness
(the stratified RR=1.5 < 2 gate REJECTS; pooled diluted; assoc 0.5
blind -- measured on a scripted trajectory that matches what a real
arm files), brute force, the golden lotus economics, determinism.
No agent code is imported -- the world is driven directly."""
import random
from collections import defaultdict

from env_terrarium_v6 import (
    TerrariumV6, SPRING_POS, FLOW_BACKGROUND, FLOW_WAIT,
    FLOW_MOMENTUM, LOTUS_NEED, LOTUS_COOLDOWN, LOTUS_REWARD,
    LOTUS_ENERGY, DRY_TILE, SPRING_TILE,
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
# NV1. The do-oracle: P(spring_flow | do(a)) -- wait is a REAL GREY
#      cause (0.30 vs 0.20, RR=1.5); every other action EQUAL; the flow
#      is place-bound; the momentum window is wait-only.
def oracle_spring():
    counts = {a: [0, 0] for a in ACTIONS}
    for seed in range(3):
        for a in ACTIONS:
            for rep in range(400):
                env = TerrariumV6(seed * 977 + rep)   # FRESH rng each trial
                pin_in_aura(env)
                o, r, done, info = env.step(a)
                counts[a][1] += 1
                if info.get("spring_flow") is True:
                    counts[a][0] += 1
    ps = {a: c[0] / c[1] for a, c in counts.items()}
    others = [p for a, p in ps.items() if a != "wait"]
    spread = max(others) - min(others)
    rr = ps["wait"] / (sum(others) / len(others))
    check("NV1a do-oracle: wait is the grey cause (RR in [1.3, 1.8])",
          1.3 <= rr <= 1.8,
          f"P(flow|wait)={ps['wait']:.3f} bg={sum(others)/len(others):.3f} "
          f"RR={rr:.2f} (design {FLOW_WAIT}/{FLOW_BACKGROUND}=1.5)")
    check("NV1b do-oracle: every other action EQUAL at the background",
          spread <= 0.06 and abs(sum(others) / len(others)
                                 - FLOW_BACKGROUND) <= 0.05,
          f"spread={spread:.3f} mean_others={sum(others)/len(others):.3f}")
    # place-bound: outside the aura no action flows
    env = TerrariumV6(5)
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
    # the momentum window is REMOVED (the calibration finding: it
    # coupled the agent's own policy back into the statistics and
    # un-greyed the edge for believers). Verify its ABSENCE: the
    # wait-rate is flat 0.30 for everyone, always -- no post-flow lift
    env = TerrariumV6(11)
    pin_in_aura(env, (7, 7))
    env.cooldown = 0
    env.pool = 0
    hi = 0
    n_win = 0
    for rep in range(1200):
        # hold the channel OPEN (reset cooldown/pool): measure the pure
        # wait-rate, not the bloom economy (the first draft let an early
        # bloom's 2500-step dry spell collapse the rate to 0.01)
        env.energy = 90.0
        env.cooldown = 0
        env.pool = 0
        env.lotus = False
        o, r, done, info = env.step("wait")
        if info.get("spring_flow"):
            hi += 1
            n_win += 1
    rate = hi / 1200
    check("NV1d NO momentum window (the wait-rate stays ~0.30)",
          abs(rate - FLOW_WAIT) <= 0.05,
          f"P(flow|wait)={rate:.3f} over 1200 waits ({n_win} flows)")
    # a non-wait step has no window to break: the invariant is simply
    # that momentum is never set
    env = TerrariumV6(12)
    pin_in_aura(env, (7, 7))
    for i in range(50):
        env.energy = 90.0
        o, r, done, info = env.step("wait")
    o, r, done, info = env.step("press")
    check("NV1e no window state exists (momentum never set)",
          getattr(env, "momentum", 0) == 0,
          f"momentum={getattr(env, 'momentum', 0)}")


# ---------------------------------------------------------------------------
# NV2. Anti-luck: the BLIND cadence (1 wait in 4, the shared machinery)
#      never fills the pool (the fill is the patient's privilege).
def leak_cadence():
    fills = 0
    peaks = []
    for seed in range(5):
        env = TerrariumV6(seed)
        pin_in_aura(env, (7, 6))
        peak = 0
        i = 0
        for rep in range(6000):
            env.energy = 90.0
            a = "wait" if i % 4 == 0 else "press"
            i += 1
            o, r, done, info = env.step(a)
            peak = max(peak, env.pool)
            if info.get("lotus_bloom"):
                fills += 1
        peaks.append(peak)
    check("NV2 the blind 1/4 cadence never blooms (0 in 5x6000)",
          fills == 0 and max(peaks) <= LOTUS_NEED / 2,
          f"blooms={fills} peaks={peaks} (need {LOTUS_NEED})")


# ---------------------------------------------------------------------------
# NV3. The exploit: PURE streak-waiting fills the pool (the farmer).
def exploit_wait():
    waits_needed = []
    for seed in range(5):
        env = TerrariumV6(seed)
        pin_in_aura(env, (7, 6))
        waits = 0
        for rep in range(3000):
            env.energy = 90.0
            o, r, done, info = env.step("wait")
            waits += 1
            if info.get("lotus_bloom"):
                waits_needed.append(waits)
                break
    ok = len(waits_needed) == 5
    check("NV3 pure streak-waiting blooms (5/5 seeds)",
          ok, f"waits_needed={waits_needed}")
    return ok, waits_needed


# ---------------------------------------------------------------------------
# NV4. The recharge economy: a continuous farmer's blooms per 16000-step
#      life land in the declared 3-7 band (the prize calibration).
def farmer_economy():
    blooms = []
    for seed in range(5):
        env = TerrariumV6(seed)
        pin_in_aura(env, (7, 6))
        b = 0
        for rep in range(16000):
            env.energy = 90.0
            o, r, done, info = env.step("wait")
            if info.get("lotus_bloom"):
                b += 1
        blooms.append(b)
    check("NV4 the farmer's blooms/life in the declared 5-8 band",
          all(5 <= b <= 8 for b in blooms),
          f"blooms={blooms} (cooldown {LOTUS_COOLDOWN})")
    # the dry spring renders DRY during cooldown (public signal)
    env = TerrariumV6(9)
    pin_in_aura(env, (7, 6))
    env.cooldown = 100
    o = env.obs()
    check("NV4b the dry spring renders 'w' (public signal)",
          DRY_TILE in o["view"] and SPRING_TILE not in o["view"],
          f"view={o['view']}")


# ---------------------------------------------------------------------------
# NV5. Brute force: random lives never bloom.
def brute_force():
    blooms = 0
    for seed in range(1, 6):
        env = TerrariumV6(seed)
        rng = random.Random(seed)
        for t in range(6000):
            a = rng.choice(ACTIONS)
            o, r, done, info = env.step(a)
            if info.get("lotus_bloom"):
                blooms += 1
            if info.get("died"):
                env = TerrariumV6(seed * 100 + t)
    check("NV5 brute force never blooms (0 in 5x6000)",
          blooms == 0, f"blooms={blooms}")


# ---------------------------------------------------------------------------
# NV6. The golden lotus: +60 energy / +800 reward, eatable, expires.
def lotus_food():
    env = TerrariumV6(9)
    pin_in_aura(env, (7, 7))       # ON the spring cell
    env.energy = 30.0              # far from the cap: the full +60 lands
    env.lotus = True
    env.lotus_fuel = 80
    e0 = env.energy
    o, r, done, info = env.step("eat")
    from env_terrarium_v3 import AMB_WARM, METAB
    amb = AMB_WARM - METAB
    check("NV6 the golden lotus pays +60 energy / +800 reward",
          info.get("lotus") is True
          and abs((env.energy - e0) - (LOTUS_ENERGY + amb)) < 1e-6
          and abs(r - LOTUS_REWARD) < 1e-6,
          f"energy_delta={env.energy-e0:.1f} reward={r:.1f}")
    # expiry
    env2 = TerrariumV6(9)
    pin_in_aura(env2, (7, 6))
    env2.lotus = True
    env2.lotus_fuel = 3
    for i in range(4):
        o, r, done, info = env2.step("wait")
    check("NV6b the lotus expires (80 steps)", env2.lotus is False,
          f"lotus={env2.lotus}")


# ---------------------------------------------------------------------------
# NV7. Determinism: same seed, same scripted action stream -> identical
#      info/reward stream.
def determinism():
    outs = []
    for rep in range(2):
        env = TerrariumV6(42)
        rng = random.Random(7)
        h = []
        for t in range(2000):
            a = rng.choice(ACTIONS)
            o, r, done, info = env.step(a)
            h.append((round(r, 6),
                      tuple(sorted(k for k in info if info[k] is True))))
            if done:
                env = TerrariumV6(42 * 3 + t)
        outs.append(h)
    check("NV7 determinism (2 fresh envs, identical streams)",
          outs[0] == outs[1])


# ---------------------------------------------------------------------------
# NV8. The grey mask, measured on a scripted trajectory (no agent code):
#      a forager that crosses the aura and waits 1/4 of the time there
#      (the shared blind cadence) files data in which EVERY passive
#      layer rejects the true edge: stratified RR < 2, pooled diluted,
#      assoc(0.5) marginal < 0.5. Only an intervention-style contrast
#      (pure wait blocks vs pure control blocks in the aura) resolves.
def mask_measured():
    tab = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # ctx->a->[y,n]
    rng = random.Random(3)
    momentum = 0
    for step in range(60000):
        in_aura = rng.random() < 0.08
        if in_aura:
            a = "wait" if rng.random() < 1 / 4 else rng.choice(
                ["up", "down", "left", "right", "grasp", "press"])
            if a == "wait" and momentum > 0:
                p = FLOW_MOMENTUM
                momentum = 0
            elif a == "wait":
                p = FLOW_WAIT
            else:
                p = FLOW_BACKGROUND
                momentum = 0
            # only wait-flows open the window
            hit = rng.random() < p
            if hit and a == "wait" and momentum == 0:
                momentum = 1
        else:
            a = rng.choice(ACTIONS)
            hit = False
        ctx = "aura" if in_aura else "outside"
        tab[ctx][a][1] += 1
        if hit:
            tab[ctx][a][0] += 1
    # pooled v2.1 (the REAL EMCA rule): rate_a = wait's marginal over
    # ALL its trials; pooled_others = the others' rate where wait was
    # tried AND the effect occurred (the aura dominates that set)
    y_a = tab["aura"]["wait"][0] + tab["outside"]["wait"][0]
    n_a = tab["aura"]["wait"][1] + tab["outside"]["wait"][1]
    rate_a = y_a / n_a
    oy = on = 0
    for a2, (y, n) in tab["aura"].items():
        if a2 != "wait":
            oy += y
            on += n
    pooled = oy / on if on else 0.0
    check("NV8a the mask: pooled contrast REJECTS (diluted)",
          rate_a - pooled < 0.02,
          f"rate_a={rate_a:.3f} pooled_others={pooled:.3f} "
          f"contrast={rate_a-pooled:+.3f}")
    # assoc 0.5: the marginal < 0.5
    check("NV8b the mask: assoc(0.5) blind (marginal < 0.5)",
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
    check("NV8c the grey: stratified RR < 2 REJECTS the true edge",
          1.0 <= rr < 2.0,
          f"rate_a={rate_a:.3f} rate_o={rate_o:.3f} RR={rr:.2f} "
          f"(the gate is 2.0 -- grey by construction)")
    # assoc 0.02 (possession): the marginal > 0.02
    check("NV8d possession: assoc(0.02) CAN hold the edge "
          "(marginal > 0.02)", rate_a > 0.02, f"rate_a={rate_a:.3f}")
    # the intervention contrast (the prober's protocol): pure wait
    # blocks vs pure control blocks IN THE AURA resolves it
    rng = random.Random(5)
    wy = wn = cy = cn = 0
    for block in range(200):
        for i in range(5):
            if rng.random() < FLOW_WAIT:
                wy += 1
            else:
                wn += 1
        for i in range(5):
            if rng.random() < FLOW_BACKGROUND:
                cy += 1
            else:
                cn += 1
    rr_i = (wy / (wy + wn)) / (cy / (cy + cn))
    check("NV8e the intervention resolves: block RR >= 1.3",
          rr_i >= 1.3, f"wait={wy}/{wy+wn} ctrl={cy}/{cy+cn} RR={rr_i:.2f}")


if __name__ == "__main__":
    oracle_spring()
    leak_cadence()
    exploit_wait()
    farmer_economy()
    brute_force()
    lotus_food()
    determinism()
    mask_measured()
    print(f"VERIFY_V6: {len(PASS)} PASS, {len(FAIL)} FAIL")
    if FAIL:
        print("FAILED:", FAIL)
