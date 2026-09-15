"""calib_v7_fprate.py -- is the FROZEN C3 gate (FP == 0) a bar that a
CALIBRATED test can be expected to meet?

The matrix produced 1 distinct false-positive event (seed 8, wait->glow),
appearing 6 times because the same seed drives every arm and both truth
regimes. C3 as frozen (PREREG_V7 §2) demands FP == 0 across all modes and
seeds, so C3 is reported FAIL. This script measures whether that bar is
attainable at all, by measuring the NOMINAL false-positive rate of the very
same verdict rule under the null.

Method (scripted, no agent, so nothing about the arbiter or the generator
can enter): drive the identical protocol (5/5 alternation, same affordability
gate, pinned on the station, respawn on death) in a regime where the effect
carries no causal information (truth=off). Collect windows of the SAME
matched size the verdicts actually used, apply the identical rule
(p<0.05 and RR>=1.3), and count passes. Then:

    expected FP count = per-test rate x number of tests the matrix issued

Also re-checks determinism (rerun one matrix cell in a fresh process).
"""
import glob
import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile

from env_terrarium_v7 import (TerrariumV7, STATION, NONMOVE,
                              pick_decoy_action)

HERE = os.path.dirname(os.path.abspath(__file__))
MATRIX = os.path.join(HERE, "results", "matrix_v7")
BLOCK = 5


def fisher_greater(a_yes, a_no, c_yes, c_no):
    n = a_yes + a_no + c_yes + c_no
    if n == 0:
        return 1.0
    r1, c1 = a_yes + a_no, a_yes + c_yes
    hi = min(r1, c1)
    p = 0.0
    denom = math.comb(n, c1)
    for x in range(a_yes, hi + 1):
        p += math.comb(r1, x) * math.comb(n - r1, c1 - x) / denom
    return min(1.0, p)


def window(seed, n_scored):
    """Scripted protocol, null regime; returns (ty, tn, cy, cn)."""
    da = pick_decoy_action(seed)
    ctrl = next(a for a in sorted(NONMOVE) if a != da)
    env = TerrariumV7(seed, truth=False, decoy=True, rich="low")
    env.pos = STATION
    ty = tn = cy = cn = 0
    t = 0
    while (ty + tn + cy + cn) < n_scored and t < 200000:
        on_target = (t // BLOCK) % 2 == 0
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


print("=== 1. DETERMINISM: one cell, byte hash across a fresh process ===")
cell = os.path.join(MATRIX, "v7_full_7_on_low_on.json")
h_before = hashlib.sha256(open(cell, "rb").read()).hexdigest()
# rerun into a SCRATCH copy of the tree so the frozen matrix is never
# touched (the runner writes next to itself)
scratch = tempfile.mkdtemp(prefix="v7det_", dir=HERE)
for f in ("run_life_v7.py", "env_terrarium_v7.py", "agent_emca_v7.py",
          "candidate_gen.py", "arbitration.py", "baselines.py",
          "agent_emca.py", "env_terrarium.py"):
    shutil.copy(os.path.join(HERE, f), os.path.join(scratch, f))
r = subprocess.run([sys.executable, "run_life_v7.py", "v7_full", "7",
                    "16000", "on", "low", "on"],
                   cwd=scratch, capture_output=True, text=True,
                   env={**os.environ, "PYTHONHASHSEED": "0"})
scratch_cell = os.path.join(scratch, "results", "matrix_v7",
                            "v7_full_7_on_low_on.json")
h_after = hashlib.sha256(open(scratch_cell, "rb").read()).hexdigest()
print(f"   frozen cell sha256 : {h_before}")
print(f"   fresh  cell sha256 : {h_after}")
print(f"   byte-identical     : {h_before == h_after}")
h_now = hashlib.sha256(open(cell, "rb").read()).hexdigest()
print(f"   frozen cell untouched by this script: {h_now == h_before}")
shutil.rmtree(scratch, ignore_errors=True)

print("\n=== 2. how many tests did the matrix actually issue? ===")
tests = 0
for p in sorted(glob.glob(os.path.join(MATRIX, "*.json"))):
    d = json.load(open(p))
    tests += len(d.get("verdicts", {}))
print(f"   verdicts issued across the matrix: {tests}")

print("\n=== 3. NOMINAL per-test false-positive rate (matched n) ===")
# matched n: the verdicts that were actually issued used ~equal arms; take
# the modal n and also 200 (the seed-8 event's n) for the headline number.
for n_per_arm in (100, 200, 400):
    N = 400
    passed = 0
    for s in range(N):
        ty, tn, cy, cn = window(s, 2 * n_per_arm)
        if rule(ty, tn, cy, cn):
            passed += 1
    rate = passed / N
    print(f"   n={n_per_arm}/arm: scripted pass rate {passed}/{N} = "
          f"{100*rate:.2f}%")

# analytic cross-check at n=200/arm under exchangeability
rng = random.Random(11)
NMC = 40000
mc = 0
for _ in range(NMC):
    ty = sum(1 for _ in range(200) if rng.random() < 0.5)
    cy = sum(1 for _ in range(200) if rng.random() < 0.5)
    if rule(ty, 200 - ty, cy, 200 - cy):
        mc += 1
print(f"   analytic Monte-Carlo at n=200/arm: {mc}/{NMC} = "
      f"{100*mc/NMC:.2f}%")

print("\n=== 4. expected FP count vs observed ===")
for rate, label in ((mc / NMC, "Monte-Carlo n=200"),
                    (0.0043, "frozen nominal 0.43%")):
    print(f"   {label}: E[FP] = {tests} x {rate:.4f} = {tests*rate:.2f}")
    lam = tests * rate
    print(f"      P(at least one FP) = {1 - math.exp(-lam):.2f} ; "
          f"observed distinct FP events = 1")
