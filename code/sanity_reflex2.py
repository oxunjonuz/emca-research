#!/usr/bin/env python3
"""Run 4: is the run-3 reflexive-gate rejection of the linger decoy REAL or
small-sample noise? Long-run measurement with adequate eps samples.

Run 3 (sanity_reflex.py) measured: reflex gate rejects (eat,bell_rang) 3/3
seeds -- but with n_eps = 13/18/12 only, and the mechanism was NOT the
predicted one (predicted eps-rate LOW ~0.10 vs deliberate ~0.30; measured
eps HIGH 0.54/0.56 vs 0.375/0.378, seed 3 reversed 0.25 vs 0.397). Pooled
across seeds the gap is 0.082 < slack 0.10 (z ~ 1.06, p ~ 0.29): the 3/3
rejection is consistent with noise. The boundary stated in run 3's header
may be binding: eps randomises the ACTION, not the DESTINATION -- both
eps-eats and deliberate eats happen mostly at the storm tree, so the
invariance test has no contrast and no power against a LOCATION-coupled
confounder.

This run measures the eps/deliberate contrast with ~4x more data
(60000 steps x 3 seeds vs 16000) and audits WHERE the eats happen.

PRE-REGISTERED CRITERIA (before the first run of this file):
  G1 harness: pooled n_eps(eat) >= 100 (enough eps data to trust rates)
  G2 MAIN:    pooled |r_eps - r_del| for (eat,bell_rang) < 0.10 AND per-seed
              gap < 0.10 in >=2/3 seeds  ->  the run-3 rejection does NOT
              replicate: the reflex gate (action-level eps) has NO POWER
              against the linger confounder; direction 4 as instrumented
              is dead. (If G2 FAILs -- gap >= 0.10 persists with big n --
              the gate is real and run 3 was not luck.)
  G3 control: (eat,ate) gap < 0.10 (a true edge is invariant to the reason
              for acting -- the gate's LOGIC is sound where contrast exists)
  G4 audit:   location mix of eps-eats vs deliberate eats (at-tree vs
              at-berry fractions) -- explains G2 mechanistically.
  Decision: G2 PASS -> direction 4 requires DESTINATION-level randomisation
  (goal-override exploration, "4b"), not action-level eps; design 4b as the
  next toy check. G2 FAIL -> proceed to v3 with the reflex gate as-is.
"""
import sys
from collections import defaultdict

from sanity_reflex import AgentV23
from sanity_linger import LingerEnv


def run(seed, steps=60000):
    env = LingerEnv(seed)
    ag = AgentV23(seed)
    # per-mode, per-effect counters for action "eat"
    cnt = {
        "eps": defaultdict(lambda: [0, 0]),    # effect -> [yes, n]
        "del": defaultdict(lambda: [0, 0]),
    }
    loc = {"eps": [0, 0], "del": [0, 0]}       # [at_tree, at_berry]
    ring_at_tree = {"eps": [0, 0], "del": [0, 0]}   # [rings, n] at tree
    for i in range(steps):
        o = env.obs()
        a = ag.act(o)
        o2, r, done, info = env.step(a)
        ag.observe(o, a, r, o2, done, info)
        if a == "eat":
            mode = "eps" if ag._last_eps else "del"
            cnt[mode]["n"][1] += 1
            for e in ("bell_rang", "ate", "tree_ate"):
                cnt[mode][e][1] += 1          # denominator: EVERY eat trial
                if info.get(e):
                    cnt[mode][e][0] += 1
            if info.get("tree_ate"):
                loc[mode][0] += 1
                ring_at_tree[mode][1] += 1
                ring_at_tree[mode][0] += 1 if info.get("bell_rang") else 0
            elif info.get("ate"):
                loc[mode][1] += 1
        if done:
            env = LingerEnv(seed + 1000 + i)
    return cnt, loc, ring_at_tree


def rate(c, e):
    y, n = c[e]
    return (y / n) if n else None


def main():
    print("sanity_reflex2.py -- run 4: long-run eps/deliberate contrast "
          "for the linger decoy (is run-3's 3/3 real?)")
    print("=" * 72)
    per_seed = []
    pooled = {"eps": defaultdict(lambda: [0, 0]),
              "del": defaultdict(lambda: [0, 0])}
    loc_pooled = {"eps": [0, 0], "del": [0, 0]}
    ring_tree_pooled = {"eps": [0, 0], "del": [0, 0]}
    for seed in (1, 2, 3):
        cnt, loc, ring_tree = run(seed)
        for mode in ("eps", "del"):
            for e in ("bell_rang", "ate", "tree_ate", "n"):
                pooled[mode][e][0] += cnt[mode][e][0]
                pooled[mode][e][1] += cnt[mode][e][1]
            for k in range(2):
                loc_pooled[mode][k] += loc[mode][k]
                ring_tree_pooled[mode][k] += ring_tree[mode][k]
        rb, ra = rate(cnt["eps"], "bell_rang"), rate(cnt["del"], "bell_rang")
        gap = abs(rb - ra) if rb is not None and ra is not None else None
        per_seed.append(gap)
        print(f"seed {seed}: n_eps={cnt['eps']['n'][1]} "
              f"n_del={cnt['del']['n'][1]}")
        print(f"  eat->bell_rang: r_eps={rb} r_del={ra} gap={gap}")
        print(f"  eat->ate:       r_eps={rate(cnt['eps'], 'ate')} "
              f"r_del={rate(cnt['del'], 'ate')}")
        print(f"  eat->tree_ate:  r_eps={rate(cnt['eps'], 'tree_ate')} "
              f"r_del={rate(cnt['del'], 'tree_ate')}")
        print(f"  eat locations: eps at_tree/berry="
              f"{loc['eps'][0]}/{loc['eps'][1]}, del at_tree/berry="
              f"{loc['del'][0]}/{loc['del'][1]}")
        rt_e, rt_d = ring_tree["eps"], ring_tree["del"]
        print(f"  ring while eating AT TREE: eps="
              f"{rt_e[0]}/{rt_e[1]}={rt_e[0] / max(1, rt_e[1]):.3f}, "
              f"del={rt_d[0]}/{rt_d[1]}={rt_d[0] / max(1, rt_d[1]):.3f}")

    rb, ra = rate(pooled["eps"], "bell_rang"), rate(pooled["del"], "bell_rang")
    gap = abs(rb - ra)
    n_eps = pooled["eps"]["n"][1]
    n_del = pooled["del"]["n"][1]
    print("=" * 72)
    print(f"POOLED: n_eps={n_eps} n_del={n_del}")
    print(f"  eat->bell_rang: r_eps={rb:.4f} r_del={ra:.4f} gap={gap:.4f}")
    print(f"  eat->ate:       r_eps={rate(pooled['eps'], 'ate')} "
          f"r_del={rate(pooled['del'], 'ate')}")
    print(f"  eat locations pooled: eps at_tree/berry="
          f"{loc_pooled['eps'][0]}/{loc_pooled['eps'][1]} "
          f"({loc_pooled['eps'][0] / max(1, sum(loc_pooled['eps'])):.2f} at tree), "
          f"del at_tree/berry={loc_pooled['del'][0]}/{loc_pooled['del'][1]} "
          f"({loc_pooled['del'][0] / max(1, sum(loc_pooled['del'])):.2f} at tree)")
    rt_e, rt_d = ring_tree_pooled["eps"], ring_tree_pooled["del"]
    print(f"  ring while eating AT TREE pooled: eps={rt_e[0]}/{rt_e[1]}"
          f"={rt_e[0] / max(1, rt_e[1]):.3f}, del={rt_d[0]}/{rt_d[1]}"
          f"={rt_d[0] / max(1, rt_d[1]):.3f}")

    print("\n================ PRE-REGISTERED VERDICTS ================")
    g1 = n_eps >= 100
    gaps_ok = sum(1 for g in per_seed if g is not None and g < 0.10)
    g2 = (gap < 0.10) and (gaps_ok >= 2)
    g3 = abs((rate(pooled["eps"], "ate") or 0)
             - (rate(pooled["del"], "ate") or 0)) < 0.10
    print(f"G1 harness (pooled n_eps >= 100):        "
          f"{'PASS' if g1 else 'FAIL'} (n_eps={n_eps})")
    print(f"G2 MAIN gap < 0.10 pooled and >=2/3 seeds: "
          f"{'PASS' if g2 else 'FAIL'} (pooled gap={gap:.4f}, "
          f"per-seed gaps={[round(g, 3) if g is not None else None for g in per_seed]})")
    print(f"G3 control (eat->ate invariant):          "
          f"{'PASS' if g3 else 'FAIL'}")
    print(f"G4 audit: see location lines above")
    if g2:
        print("DECISION: run-3's 3/3 rejection does NOT replicate -- the "
              "reflex gate (action-level eps) has no power against the "
              "linger confounder. Direction 4 needs DESTINATION-level "
              "randomisation (goal-override exploration, 4b).")
    else:
        print("DECISION: the gap persists with adequate n -- the reflex gate "
              "is real; proceed to v3 with it.")
    sys.exit(0)


if __name__ == "__main__":
    main()
