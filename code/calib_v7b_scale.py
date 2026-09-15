"""calib_v7b_scale.py -- LARGE-SCALE scripted calibration (PREREG_V7B §1 H5).

Question: the V7 scripted calibration ran 0/400 and 0/160 windows and
therefore only bounded the FP rate at ~1% and ~2.3%. The exact null rate
of the frozen rule at n=200/arm is ~0.49%/test, so those checks had
expected hits of 1.95 and 0.78 -- they were UNDERPOWERED, and 0 hits was
the likely outcome even under a perfectly calibrated rule.

This script runs the SAME scripted protocol (5/5 alternation, the same
affordability gate, pinned on the station, respawn, scored inside warm,
exact Fisher, p<0.05 AND RR>=1.3) at N windows large enough to measure
the rate rather than bound it, and reports a Wilson CI.

Plus an ARM-PERMUTATION control: the same streams, but the window's
target/control labels shuffled -- if the result depends on the labels
rather than the stream, the measurement is invalid.

Usage: python3 calib_v7b_scale.py [N] [n_per_arm] > results/calib_v7b_scale.txt
"""
import math
import os
import random
import sys

from env_terrarium_v7 import TerrariumV7, STATION, NONMOVE, pick_decoy_action

BLOCK = 5


def fisher_greater(a_yes, a_no, c_yes, c_no):
    n = a_yes + a_no + c_yes + c_no
    if n == 0:
        return 1.0
    r1, c1 = a_yes + a_no, a_yes + c_yes
    hi = min(r1, c1)
    p = 0.0
    den = math.comb(n, c1)
    for x in range(a_yes, hi + 1):
        p += math.comb(r1, x) * math.comb(n - r1, c1 - x) / den
    return min(1.0, max(0.0, p))


def window(seed, n_scored, swap=False):
    """Scripted protocol under the null (truth=off). Returns (ty,tn,cy,cn).
    `swap` flips which arm is scored as target -- the permutation control."""
    da = pick_decoy_action(seed)
    ctrl = next(a for a in sorted(NONMOVE) if a != da)
    env = TerrariumV7(seed, truth=False, decoy=True, rich="low")
    env.pos = STATION
    ty = tn = cy = cn = 0
    t = 0
    while (ty + tn + cy + cn) < n_scored and t < 200000:
        on_target = (t // BLOCK) % 2 == 0
        if swap:
            on_target = not on_target
        a = da if on_target else ctrl
        other = ctrl if on_target else da
        aff = env.afford()
        if not (a in aff and other in aff):
            _, _, done, info = env.step(a)
        else:
            _, _, done, info = env.step(a)
            if env.phase == "warm":
                y = 1 if info.get("glow") else 0
                if on_target:
                    ty += y
                    tn += 1 - y
                else:
                    cy += y
                    cn += 1 - y
        if done:
            env = TerrariumV7(seed + 9000 + t, truth=False, decoy=True,
                              rich="low")
            env.pos = STATION
        t += 1
    return ty, tn, cy, cn


def rule(ty, tn, cy, cn):
    if (ty + tn) == 0 or (cy + cn) == 0:
        return False
    p = fisher_greater(ty, tn, cy, cn)
    ra = ty / (ty + tn)
    rc = cy / (cy + cn)
    rr = ra / rc if rc > 0 else float("inf")
    return p < 0.05 and rr >= 1.3


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 2500
    n_arm = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    print("=== LARGE-SCALE SCRIPTED CALIBRATION (PREREG_V7B H5) ===")
    print(f"  protocol: 5/5 alternation, affordability gate, pinned on the "
          f"station, respawn, scored inside warm, exact Fisher, "
          f"p<0.05 AND RR>=1.3")
    print(f"  N = {N} windows at n = {n_arm}/arm (null regime, truth=off)")
    passes = 0
    for s in range(N):
        ty, tn, cy, cn = window(s, 2 * n_arm)
        if rule(ty, tn, cy, cn):
            passes += 1
    rate = passes / N
    lo, hi = wilson(passes, N)
    print(f"  CALIBRATED: {passes}/{N} = {100*rate:.3f}%  "
          f"Wilson 95% CI [{100*lo:.3f}%, {100*hi:.3f}%]")
    print(f"  expected under the exact null rate 0.488%: "
          f"{N*0.00488:.2f} passes")
    # permutation control
    swapped = 0
    M = max(400, N // 4)
    for s in range(M):
        ty, tn, cy, cn = window(s, 2 * n_arm, swap=True)
        if rule(ty, tn, cy, cn):
            swapped += 1
    lo2, hi2 = wilson(swapped, M)
    print(f"  ARM-PERMUTATION CONTROL: {swapped}/{M} = "
          f"{100*swapped/M:.3f}%  Wilson 95% CI "
          f"[{100*lo2:.3f}%, {100*hi2:.3f}%]")
    print(f"  (both arms should agree if the measurement is driven by the "
          f"stream, not the label assignment)")
    # power statement about the OLD checks
    print("\n  POWER OF THE OLD CHECKS (the honest corollary):")
    for n_old, label in ((400, "calib_v7_fprate 0/400"),
                         (160, "diag_w4 replicas 0/160")):
        e = n_old * rate
        print(f"    {label}: E[hits] = {e:.2f} at the measured rate -> "
              f"P(0 hits) = {math.exp(-e):.2f}")


if __name__ == "__main__":
    main()
