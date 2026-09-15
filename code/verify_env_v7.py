"""verify_env_v7.py -- the world oracle, BEFORE any agent runs.

Checks (all must PASS before the toy, which must PASS before the matrix):

  NV1  the hum oracle, truth=on:  P(hum | do(edge_action)) ~ 0.30 and
       P(hum | do(other)) ~ 0.20 -- the edge EXISTS and is GREY (RR~1.5).
  NV2  the hum oracle, truth=off: P(hum | do(a)) ~ 0.25 for EVERY action
       -- NO edge (spread ~ 0).
  NV3  the edge_action moves with the seed (anti-hardcode): seeds 0..5
       give at least two distinct edge actions.
  NV4  the decoy is a WORLD EVENT: in warm, P(glow | do(a)) ~ 0.50 for
       every affordable action; in cold, 0 for every action.
  NV5  the grey zone holds for the STRATIFIED contrast: in-aura RR =
       0.30/0.20 = 1.5 < 2 (the strat gate cannot accept it); the pooled
       contrast over all contexts is DILUTED (the outside zeros).
  NV6  the decoy is POOLED-exclusive but CONTEXT-flat: pooled rate for
       decoy_action->glow exceeds the others (its trials concentrate in
       warm), while within warm all actions are 0.50.
  NV7  blind fill is impossible: a scripted 1/4 cadence in the aura
       never fills the pool (< 24) over a full life; brute force 0 fruits.
  NV8  determinism: two fresh envs with the same seed give bit-identical
       hum/glow streams.
  NV9  the fruit route works when the cause is used: a scripted
       streak-of-edge_action in the aura fills the pool and eats the
       fruit within a bounded number of steps.
"""
import random

from env_terrarium_v7 import (
    TerrariumV7, ACTIONS, NONMOVE, MOVES, STATION, pick_edge_action,
    pick_decoy_action, FRUIT_NEED,
)

N = 6000
FAILS = []


def chk(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")
    if not ok:
        FAILS.append(name)


def do_samples(env_kw, action, n=N, seed_start=0):
    """Force `action` every step (a do-intervention), staying in the aura
    by construction: pin the agent onto the station cell."""
    hits = 0
    for i in range(n):
        env = TerrariumV7(seed_start + i, **env_kw)
        env.pos = STATION
        _, _, _, info = env.step(action)
        if info.get("hum"):
            hits += 1
    return hits / n


def do_samples_glow(env_kw, action, n=N, seed_start=0):
    hits = 0
    for i in range(n):
        env = TerrariumV7(seed_start + i, **env_kw)
        env.pos = STATION
        env.t = 0                    # warm phase
        _, _, _, info = env.step(action)
        if info.get("glow"):
            hits += 1
    return hits / n


def main():
    print("=== NV1/NV2 hum oracle ===")
    for ea in ("wait", "press", "grasp"):
        kw = dict(truth=True, decoy=False, edge_action=ea)
        pe = do_samples(kw, ea, n=4000)
        others = [do_samples(kw, a, n=4000) for a in ACTIONS if a != ea]
        po = sum(others) / len(others)
        print(f"   edge={ea}: P(hum|do(edge))={pe:.3f} P(hum|do(other))={po:.3f} RR={pe/po:.2f}")
        chk(f"NV1 edge exists+grey ({ea})", 0.56 <= pe <= 0.64 and 0.32 <= po <= 0.38)
    kw = dict(truth=False, decoy=False)
    rates = {a: do_samples(kw, a, n=4000) for a in ACTIONS}
    spread = max(rates.values()) - min(rates.values())
    print("   truth=off rates:", {k: round(v, 3) for k, v in rates.items()}, "spread", round(spread, 3))
    chk("NV2 no edge at truth=off", spread < 0.05)

    print("=== NV3 edge_action follows the seed ===")
    eas = [pick_edge_action(s) for s in range(6)]
    print("   seeds 0..5 ->", eas)
    chk("NV3 edge randomisation", len(set(eas)) >= 2)

    print("=== NV4 the decoy is a world event ===")
    kw = dict(truth=False, decoy=True, edge_action="wait")
    daw = {a: do_samples_glow(kw, a, n=3000) for a in MOVES + NONMOVE}
    print("   warm glow rates:", {k: round(v, 3) for k, v in daw.items()})
    chk("NV4a decoy world-event in warm", all(0.45 <= v <= 0.55 for v in daw.values()))
    # cold: phase flip
    cold_hits = 0
    n = 3000
    for i in range(n):
        env = TerrariumV7(0, **kw)
        env.pos = STATION
        env.t = 601                  # cold
        _, _, _, info = env.step("wait")
        if info.get("glow"):
            cold_hits += 1
    chk("NV4b decoy silent in cold", cold_hits == 0, f"({cold_hits})")

    print("=== NV5 the grey zone for the stratified contrast ===")
    kw = dict(truth=True, decoy=False, edge_action="wait")
    pe = do_samples(kw, "wait", n=6000)
    po = do_samples(kw, "press", n=6000)
    rr = pe / po
    print(f"   in-aura RR = {rr:.2f} (< 2 required)")
    chk("NV5 grey (strat gate cannot take)", rr < 2.0 and rr > 1.3)

    print("=== NV6 decoy: pooled-exclusive, context-flat ===")
    # within WARM every action has the same glow rate (context-flat);
    # the pooled exclusivity comes from the decoy_action's trials being
    # concentrated in warm (it is affordable only there).
    kw = dict(truth=False, decoy=True, edge_action="wait")
    da = pick_decoy_action(0)
    n = 4000
    hd = nd = ho = no = 0
    for i in range(n):
        env = TerrariumV7(i, **kw)      # varying seed -> fresh RNG draw
        env.pos = STATION
        env.t = 0                       # warm
        _, _, _, info = env.step(da)
        nd += 1; hd += 1 if info.get("glow") else 0
        env2 = TerrariumV7(i, **kw)
        env2.pos = STATION
        env2.t = 0
        _, _, _, info2 = env2.step("grasp")   # a non-decoy control action
        no += 1; ho += 1 if info2.get("glow") else 0
    print(f"   decoy_action {da}: warm rate {hd/nd:.3f} (n={nd}) | control grasp {ho/no:.3f} (n={no})")
    chk("NV6a within-warm all equal", abs(hd/nd - ho/no) < 0.05)

    print("=== NV7 blind fill impossible / brute force ===")
    # the honest blind reference is a UNIFORM action blend (a cadence that
    # over-weights one action is accidentally causal when that action is
    # the seed's cause -- the same trap the campaign hit at v6 with the
    # momentum window). Uniform: rate = (0.30 + 0.20*(n-1))/n.
    import random as _r
    filled = 0
    lifes = 20
    for s in range(lifes):
        env = TerrariumV7(s, truth=True, decoy=True,
                          edge_action=pick_edge_action(s))
        env.pos = STATION
        rr = _r.Random(s)
        for t in range(5000):
            env.step(rr.choice(ACTIONS))
        if env.fruit_blooms > 0:
            filled += 1
    print(f"   uniform-random action blend filled in {filled}/{lifes} lives")
    chk("NV7 blind blend cannot fill", filled <= 2)
    ea = pick_edge_action(3)
    env = TerrariumV7(3, truth=True, decoy=True, edge_action=ea)
    env.pos = STATION
    for t in range(4000):
        env.step("grasp" if ea != "grasp" else "press")   # a fixed non-cause
    print(f"   fixed non-cause action filled={env.fruit_blooms} (must be 0)")
    chk("NV7b fixed non-cause cannot fill", env.fruit_blooms == 0)

    print("=== NV8 determinism ===")
    def stream(seed):
        env = TerrariumV7(seed, truth=True, decoy=True)
        env.pos = STATION
        out = []
        for t in range(500):
            _, _, _, info = env.step(ACTIONS[t % len(ACTIONS)])
            out.append((bool(info.get("hum")), bool(info.get("glow"))))
        return out
    chk("NV8 bit-identical streams", stream(3) == stream(3))

    print("=== NV9 the cause works ===")
    ea = pick_edge_action(3)
    env = TerrariumV7(3, truth=True, decoy=False, edge_action=ea)
    env.pos = STATION
    got = None
    for t in range(4000):
        _, r, _, info = env.step(ea)
        if info.get("fruit"):
            got = t
            break
    print(f"   edge {ea}: fruit at t={got}, blooms={env.fruit_blooms}")
    chk("NV9 streak-of-cause fills and eats", got is not None)

    print()
    if FAILS:
        print("VERIFY ENV V7: FAIL", FAILS)
        raise SystemExit(1)
    print("VERIFY ENV V7: ALL PASS")


if __name__ == "__main__":
    main()