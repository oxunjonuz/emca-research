"""verify_env_v15.py -- the world oracle.

Every claim below is checked against the WORLD's own arithmetic, not
against the agent. A live negative control (NV) is included: each check
must be able to FAIL if the world is perturbed.
"""
import random
import sys

from env_v15 import (WorldV15, ACTIONS, CTX_SPAN, TRUE_RATE, NOISE_RATE,
                     CONST_RATE, DECOY_RATES, DECOY_RESET)

FAILS = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    if not cond:
        FAILS.append(name)
    print(f"  [{tag}] {name} {detail}")


def rate_of(seed, action, ctx, n=40000, decoy=False, ctx_span=CTX_SPAN):
    w = WorldV15(seed, decoy=decoy, ctx_span=ctx_span)
    hits = 0
    tot = 0
    for _ in range(n * 8):
        if w.ctx != ctx:
            w.step(action)
            continue
        obs = w.step(action)
        hits += obs["val"]
        tot += 1
        if tot >= n:
            break
    return hits / tot


def main():
    print("=== v15 world oracle ===")
    # 1. feature identity per action
    w = WorldV15(0)
    check("O1 f0 channel of a0", w.feature("a0") == "f0")
    check("O2 f1 channel of a1", w.feature("a1") == "f1")
    check("O3 fnoise channel of a2", w.feature("a2") == "fnoise")
    check("O4 fconst channel of a3 (decoy off)", w.feature("a3") == "fconst")
    wd = WorldV15(0, decoy=True)
    check("O5 fdecoy channel of a3 (decoy on)", wd.feature("a3") == "fdecoy")

    # 2. context alternation
    w = WorldV15(0)
    ctxs = []
    for _ in range(CTX_SPAN * 3):
        ctxs.append(w.ctx)
        w.step("a1")
    check("O6 phase A on [0,span)", ctxs[0] == "A" and ctxs[CTX_SPAN - 1] == "A")
    check("O7 phase B on [span,2span)",
          ctxs[CTX_SPAN] == "B" and ctxs[2 * CTX_SPAN - 1] == "B")
    check("O8 phase A again on [2span,3span)", ctxs[2 * CTX_SPAN] == "A")

    # 3. measured rates match declared rates
    rA = rate_of(1, "a0", "A")
    rB = rate_of(1, "a0", "B")
    check("O9 P(val|a0,A) ~ 0.9", abs(rA - TRUE_RATE["A"]) < 0.01,
          f"measured {rA:.4f}")
    check("O10 P(val|a0,B) ~ 0.1", abs(rB - TRUE_RATE["B"]) < 0.01,
          f"measured {rB:.4f}")
    rn = rate_of(1, "a1", "A")
    check("O11 P(val|a1,A) ~ 0.5", abs(rn - NOISE_RATE) < 0.01,
          f"measured {rn:.4f}")
    rn2 = rate_of(1, "a2", "B")
    check("O12 P(val|a2,B) ~ 0.5", abs(rn2 - NOISE_RATE) < 0.01,
          f"measured {rn2:.4f}")
    rc = rate_of(1, "a3", "A")
    check("O13 P(val|a3,A) == 0.0 (parking)", rc == 0.0, f"measured {rc}")

    # 4. THE POOLED TRAP: pooled over contexts, a0 is indistinguishable
    #    from noise. This is the structural fact the whole seam rests on.
    pooled = (rA + rB) / 2.0
    check("O14 pooled P(val|a0) ~ 0.5 (pooled trap)",
          abs(pooled - NOISE_RATE) < 0.01, f"pooled {pooled:.4f}")
    # a pooled contrast between a0 and a1 is ~zero
    check("O15 pooled contrast a0 vs a1 ~ 0",
          abs(pooled - rn) < 0.02, f"|{pooled:.4f}-{rn:.4f}|")

    # 5. the decoy channel is non-stationary and learnable forever
    w = WorldV15(0, decoy=True)
    early = []
    for _ in range(DECOY_RESET):
        early.append(w.step("a3")["val"])
    late = []
    for _ in range(DECOY_RESET):
        late.append(w.step("a3")["val"])
    check("O16 decoy rate 0.9 then 0.1 (non-stationary)",
          sum(early) / len(early) > 0.5 and sum(late) / len(late) < 0.5,
          f"early {sum(early)}/{len(early)} late {sum(late)}/{len(late)}")

    # 6. determinism: same seed -> same stream
    def stream(seed):
        w = WorldV15(seed)
        return [w.step(a)["val"] for a in (ACTIONS * 50)]
    check("O17 determinism (same seed, same bytes)",
          stream(7) == stream(7))
    check("O18 different seeds differ", stream(7) != stream(8))

    # 7. NO reward/energy/death exists in the observation at all
    w = WorldV15(0)
    obs = w.step("a0")
    check("O19 observation has exactly {phase,feat,val}",
          set(obs.keys()) == {"phase", "feat", "val"})
    check("O20 no 'reward'/'energy'/'alive' key",
          not ({"reward", "energy", "alive", "died"} & set(obs.keys())))

    # 8. LIVE NEGATIVE CONTROL: perturb the world and the checks go red
    class Perturbed(WorldV15):
        def rate(self, feat):
            if feat == "f0":
                return 0.5
            return super().rate(feat)
    wp = Perturbed(1)
    hits = 0
    tot = 0
    for _ in range(40000):
        if wp.ctx != "A":
            wp.step("a0")
            continue
        hits += wp.step("a0")["val"]
        tot += 1
        if tot >= 4000:
            break
    rp = hits / tot
    check("NV1 perturbed world FAILS the true-rate check",
          abs(rp - TRUE_RATE["A"]) >= 0.01, f"measured {rp:.4f}")

    print(f"=== {len(FAILS)} failures ===")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())