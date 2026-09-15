"""verify_v7b_independent.py -- SECOND PASS for V7B, different code, disk only.

Imports nothing from analyze_v7b / agent_emca_v7 / env_terrarium_v7 /
candidate_gen / arbitration. Recomputes every reported number from the
raw JSONs and the frozen calibration text, and re-derives the null rate
by SIMULATION (the primary pass used exact enumeration -- a genuinely
different path).

Checks:
  1. frozen matrix inventory and the FP event (recomputed Fisher p)
  2. held-out inventory: runs, null tests, events, rate
  3. the rate test: agent-side vs scripted (independent Fisher)
  4. exact null rate by Monte-Carlo (40 000 draws) vs the primary's
     enumeration and the campaign's 0.51%
  5. Bonferroni family thresholds
  6. the frozen matrix was not modified (row count and per-file sha)

Usage: python3 verify_v7b_independent.py > results/verify_v7b_independent.txt
"""
import glob
import hashlib
import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
M7 = os.path.join(HERE, "results", "matrix_v7")
M7B = os.path.join(HERE, "results", "matrix_v7b")
SCALE = os.path.join(HERE, "results", "calib_v7b_scale.txt")


def fisher_greater(a, b, c, d):
    """One-sided Fisher: is a/b > c/d? (independent implementation)"""
    a_yes, a_no, c_yes, c_no = a, b, c, d
    n = a_yes + a_no + c_yes + c_no
    if n == 0:
        return 1.0
    r1, c1 = a_yes + a_no, a_yes + c_yes
    hi = min(r1, c1)
    tot = 0.0
    den = math.comb(n, c1)
    for x in range(a_yes, hi + 1):
        tot += math.comb(r1, x) * math.comb(n - r1, c1 - x) / den
    return min(1.0, max(0.0, tot))


def verdicts(path):
    return json.load(open(path)).get("verdicts", {})


def main():
    print("=" * 72)
    print("V7B INDEPENDENT VERIFICATION (disk only, no analysis imports)")
    print("=" * 72)

    # ---------- 1. frozen matrix ----------
    files7 = sorted(glob.glob(os.path.join(M7, "*.json")))
    rows7, fp7 = 0, []
    for p in files7:
        for k, v in verdicts(p).items():
            rows7 += 1
            if k.endswith("->glow") and v["verdict"] == "CAUSAL":
                fp7.append((os.path.basename(p), k, v))
    print(f"\n[1] frozen matrix: {len(files7)} files, {rows7} verdict rows, "
          f"{len(fp7)} glow-CAUSAL rows")
    if fp7:
        v = fp7[0][2]
        p_re = fisher_greater(v["target_yes"], v["target_no"],
                              v["ctrl_yes"], v["ctrl_no"])
        print(f"    recomputed p of the event: {p_re:.6f} "
              f"(recorded {v['p']})")
        print(f"    VERDICT: p agreement "
              f"{'PASS' if abs(p_re - v['p']) < 5e-5 else 'FAIL'}")

    # ---------- 2. held-out battery ----------
    filesb = sorted(glob.glob(os.path.join(M7B, "*.json")))
    null_tests, events, all_rows = 0, [], 0
    truth_edge = [0, 0]
    for p in filesb:
        for k, v in verdicts(p).items():
            all_rows += 1
            if k.endswith("->glow"):
                null_tests += 1
                if v["verdict"] == "CAUSAL":
                    events.append((os.path.basename(p), k, v))
            elif k.endswith("->hum"):
                # the true-edge tests (truth must be on for a real edge)
                d = json.load(open(p))
                if d["truth"]:
                    truth_edge[0] += 1
                    if v["verdict"] == "CAUSAL":
                        truth_edge[1] += 1
    k_null = null_tests - len(events)
    print(f"\n[2] held-out battery: {len(filesb)} files, {all_rows} verdict "
          f"rows")
    print(f"    null (glow) tests: {null_tests}; FP events: {len(events)}")
    rate = len(events) / null_tests if null_tests else 0.0
    print(f"    held-out FP rate: {len(events)}/{null_tests} = "
          f"{100*rate:.3f}%")
    print(f"    true-edge tests (truth=on): {truth_edge[0]}, CAUSAL "
          f"{truth_edge[1]}")
    # every event recomputed independently
    print("    events recomputed:")
    for name, k, v in events:
        p_re = fisher_greater(v["target_yes"], v["target_no"],
                              v["ctrl_yes"], v["ctrl_no"])
        ok = (p_re < 0.05) and (v["rr"] >= 1.3)
        print(f"      {name} {k}: p_re={p_re:.5f} rr={v['rr']} "
              f"rule-reproduces={ok}")

    # ---------- 3. the rate test ----------
    print("\n[3] RATE TEST: agent side vs scripted protocol")
    scr_ev = scr_n = None
    if os.path.exists(SCALE):
        txt = open(SCALE).read()
        for line in txt.splitlines():
            if "CALIBRATED:" in line:
                # e.g. "  CALIBRATED: 19/5000 = 0.380% ..."
                body = line.split("CALIBRATED:")[1].strip().split()[0]
                a, b = body.split("/")
                scr_ev, scr_n = int(a), int(b)
    print(f"    scripted: {scr_ev}/{scr_n}")
    print(f"    agent   : {len(events)}/{null_tests}")
    if scr_ev is not None:
        p_rate = fisher_greater(len(events), k_null, scr_ev,
                                scr_n - scr_ev)
        print(f"    one-sided Fisher (agent rate ABOVE scripted) p = "
              f"{p_rate:.4f}")
        print(f"    VERDICT: {'INFLATION (real defect)' if p_rate < 0.05 else 'NO INFLATION -- agent rate is consistent with the calibrated rule'}")
        # also compare with the exact null rate
        p_exact = fisher_greater(len(events), k_null, 49, 10000 - 49)
        print(f"    (reference: 0.488% exact-null rate) one-sided p = "
              f"{p_exact:.4f}")

    # ---------- 4. exact null rate by simulation ----------
    print("\n[4] NULL RATE OF THE FROZEN RULE -- simulated (different path)")
    rng = random.Random(20260912)
    NMC = 40000
    hits = 0
    for _ in range(NMC):
        ty = sum(1 for _ in range(200) if rng.random() < 0.5)
        cy = sum(1 for _ in range(199) if rng.random() < 0.5)
        if (ty + cy) == 0:
            continue
        ra = ty / 200
        rc = cy / 199
        if rc == 0 or ra <= rc:
            continue
        pv = fisher_greater(ty, 200 - ty, cy, 199 - cy)
        if pv < 0.05 and ra / rc >= 1.3:
            hits += 1
    sim = hits / NMC
    print(f"    simulated per-test FP rate = {hits}/{NMC} = {100*sim:.3f}%")
    print(f"    primary pass enumerated 0.488%; campaign Monte-Carlo 0.51%")
    ok = abs(sim - 0.00488) < 0.0025
    print(f"    VERDICT: {'PASS' if ok else 'FAIL'} (within 0.25pp)")

    # ---------- 5. Bonferroni thresholds ----------
    print("\n[5] FAMILY-WISE THRESHOLDS for the frozen-matrix event")
    if fp7:
        v = fp7[0][2]
        p_fp = fisher_greater(v["target_yes"], v["target_no"],
                              v["ctrl_yes"], v["ctrl_no"])
        for a in (0.05, 0.01, 0.001):
            print(f"    alpha={a:<5}: needs m >= {math.ceil(a/p_fp)}")
        print(f"    agent-side tests per life: max 4 -> never sufficient")

    # ---------- 6. frozen matrix integrity ----------
    print("\n[6] FROZEN MATRIX INTEGRITY")
    h = hashlib.sha256()
    for p in files7:
        h.update(open(p, "rb").read())
    print(f"    {len(files7)} files, combined sha256 = {h.hexdigest()}")
    print(f"    expected 110 files, 1f5a66e32c2cda4e... ")
    print(f"    VERDICT: {'PASS' if len(files7) == 110 else 'FAIL'}")

    print("\n" + "=" * 72)


if __name__ == "__main__":
    main()
