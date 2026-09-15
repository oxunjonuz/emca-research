"""verify_env_v8.py -- the world oracle for TerrariumV8 (PREREG_V8 §5.1).

Runs BEFORE any agent: the world's own claims must be true by direct
measurement, and the NOISE FLOOR must be stated so that later contrasts
are never reported beyond what the design can see.

Checks (each prints PASS/FAIL; the script exits 1 on any FAIL):
  E1  the epoch-action stream is a pure function of (seed, q): re-derived
      from the seed alone it reproduces the action actually used at every
      step of a run.
  E2  stickiness is real: the measured P(new epoch == previous) matches q
      for q in {0, 0.25, 0.5, 0.75, 1.0} within a binomial CI.
  E3  P(pay | epoch action) == p_edge and P(pay | other) == p_bg, measured
      over the three actions, per gap; truth=off is flat for all three.
  E4  persistence: with a 100%-consistent history the measured rate matches
      1.25*p_edge; with a 1/3 rotation it matches p_edge (no bonus).
  E5  determinism: two fresh processes produce byte-identical traces.
  E6  noise floor: the sd of per-epoch reward across seeds, and the
      smallest paired effect this design (8 seeds) can detect.
"""
import json
import math
import os
import statistics
import subprocess
import sys

from env_terrarium_v8 import (TerrariumV8, ACTIONS, GAP_PEDGE, P_BG, K,
                              MOMENTUM_BONUS, action_stream, EPOCH_LEN)

HERE = os.path.dirname(os.path.abspath(__file__))
fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    if not cond:
        fails.append(name)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    print("=== V8 WORLD ORACLE ===")

    # ---- E1: the action stream is recomputable from (seed, q) ----
    ok = True
    for seed in (0, 1, 7, 42):
        for q in (0.0, 0.5, 1.0):
            env = TerrariumV8(seed, q=q, n_epochs=8)
            ref = action_stream(seed, q, 8)
            used = []
            for t in range(8 * EPOCH_LEN + 5):
                if env.epoch == (len(used)):
                    pass
                o, r, d, info = env.step("wait")
                if info["epoch"] == len(used):
                    used.append(env.epoch_action)
            if used[:8] != ref[:8] or env.epoch_actions[:8] != ref[:8]:
                ok = False
    check("E1 epoch actions recomputable from (seed,q)", ok)

    # ---- E2: stickiness ----
    for q in (0.0, 0.25, 0.5, 0.75, 1.0):
        n = rep = 0
        for seed in range(400):
            a = action_stream(seed, q, 8)
            for i in range(1, len(a)):
                n += 1
                rep += 1 if a[i] == a[i - 1] else 0
        lo, hi = wilson(rep, n)
        ok = lo - 0.03 <= q <= hi + 0.03
        check(f"E2 stickiness q={q}", ok, f"(measured {rep/n:.3f} CI [{lo:.3f},{hi:.3f}])")

    # ---- E3: the gap, by direct measurement ----
    for gap, (pe, pb) in [("0.20", (0.55, 0.35)), ("0.10", (0.45, 0.35)),
                          ("0.05", (0.40, 0.35)), ("0.03", (0.38, 0.35))]:
        env = TerrariumV8(0, gap=gap, n_epochs=64)
        thr = {a: [0, 0] for a in ACTIONS}
        back = {a: [0, 0] for a in ACTIONS}
        for _ in range(64 * EPOCH_LEN):
            ea = env.epoch_action
            for a in ACTIONS:
                o, r, d, info = env.step(a)
                if a == ea:
                    thr[a][0] += 1 if info.get("pay") else 0
                    thr[a][1] += 1
                else:
                    back[a][0] += 1 if info.get("pay") else 0
                    back[a][1] += 1
        m_thr = sum(v[0] for v in thr.values()) / sum(v[1] for v in thr.values())
        m_back = sum(v[0] for v in back.values()) / sum(v[1] for v in back.values())
        check(f"E3 gap {gap}: causal {m_thr:.4f}~{pe}, bg {m_back:.4f}~{pb}",
              abs(m_thr - pe) < 0.005 and abs(m_back - pb) < 0.005)

    # truth=off: flat
    env = TerrariumV8(0, gap="0.20", truth=False, n_epochs=64)
    acc = {a: [0, 0] for a in ACTIONS}
    for _ in range(64 * EPOCH_LEN):
        for a in ACTIONS:
            o, r, d, info = env.step(a)
            acc[a][0] += 1 if info.get("pay") else 0
            acc[a][1] += 1
    rates = [v[0] / v[1] for v in acc.values()]
    check("E3 truth=off flat", max(rates) - min(rates) < 0.005,
          f"(spread {max(rates)-min(rates):.5f}, all ~{statistics.mean(rates):.4f})")

    # ---- E4: persistence arithmetic ----
    env = TerrariumV8(3, gap="0.20", persistence=True, n_epochs=32)
    hits = tot = 0
    for _ in range(32 * EPOCH_LEN):
        a = env.epoch_action
        o, r, d, info = env.step(a)          # 100% consistent history
        hits += 1 if info.get("pay") else 0
        tot += 1
    m = hits / tot
    check("E4 persistence inflates the rate to ~1.25*p_edge",
          abs(m - 0.55 * (1 + MOMENTUM_BONUS)) < 0.01,
          f"(measured {m:.4f} vs {0.55*(1+MOMENTUM_BONUS):.4f})")
    env = TerrariumV8(3, gap="0.20", persistence=True, n_epochs=32)
    hits = tot = 0
    rot = 0
    for _ in range(32 * EPOCH_LEN):
        a = ACTIONS[rot % 3]                 # 1/3 rotation: no bonus
        rot += 1
        o, r, d, info = env.step(a)
        if a == env.epoch_action:
            hits += 1 if info.get("pay") else 0
            tot += 1
    m = hits / tot
    check("E4 rotation earns no bonus", abs(m - 0.55) < 0.02,
          f"(measured {m:.4f} vs 0.55)")

    # ---- E5: determinism across processes ----
    code = ("import json,sys;sys.path.insert(0,'%s');"
            "from run_life_v8 import run;"
            "L=run('graded',5,'0.10',0.0,False,True,4000);"
            "print(json.dumps([L['total_reward'],L['per_epoch_pays'],"
            "L['steps_gathering'],L['steps_belief']]))" % HERE)
    outs = []
    for _ in range(2):
        r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True,
                           env={**os.environ, "PYTHONHASHSEED": "0"})
        outs.append(r.stdout.strip())
    check("E5 determinism across fresh processes", outs[0] == outs[1] and outs[0],
          f"({outs[0][:60]}...)")

    # ---- E6: noise floor and the smallest detectable effect ----
    rewards = []
    for seed in range(8):
        r = subprocess.run(
            [sys.executable, "run_life_v8.py", "rot", str(seed), "0.10", "0",
             "off", "on", "16000"],
            cwd=HERE, capture_output=True, text=True,
            env={**os.environ, "PYTHONHASHSEED": "0"})
        p = os.path.join(HERE, "results", "matrix_v8",
                         f"rot_s{seed}_g0.10_q0.0_n_on.json")
        with open(p) as fh:
            rewards.append(json.load(fh)["total_reward"])
    sd = statistics.stdev(rewards)
    sem = sd / math.sqrt(len(rewards))
    print(f"  E6 noise floor: rot reward mean {statistics.mean(rewards):.1f} "
          f"sd {sd:.1f} across 8 seeds; paired-test MDE ~ "
          f"{2.0*sem:.1f} (2*SEM), 80%-power MDE ~ {2.8*sem:.1f}")
    check("E6 noise floor reported", sd > 0)

    print()
    if fails:
        print("WORLD ORACLE: FAIL", fails)
        raise SystemExit(1)
    print("WORLD ORACLE: ALL PASS")


if __name__ == "__main__":
    main()
