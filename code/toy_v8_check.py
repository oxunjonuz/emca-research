"""toy_v8_check.py -- synthetic units for V8, BEFORE any agent claim
(PREREG_V8 §5.2). Every check prints PASS/FAIL; exit 1 on any FAIL.

W1  the sign of z is right whenever the gap is real, and is <= 0 when it
    is 0 (2 000 synthetic 2x2 tables per regime; the null leg's tolerance
    is 0.03 -- amendment A12: my first tolerance, 0.01 at 400 epochs, was
    tighter than the check's own sampling error).
W2  THE MECHANISM OF THE FROZEN RULE BELOW ITS RATIO GATE (amendment A10,
    after the toy pass refuted the first form of this claim): for a truth
    whose RATIO is below 1.3 the frozen rule's firing rate is a
    NON-MONOTONE function of n -- maximum strictly interior, value at the
    largest n strictly below the maximum -- while it is monotone
    increasing above the gate.
W3  the evidence-demand ratio on a gap ABOVE the gate: n at which the
    frozen rule fires >50%, divided by n at which mean gamma crosses 0.5,
    lands in [8, 18] (analytic 8.5; amendment A11).
W4  the persistence arithmetic reproduces 1.25*p_edge - p_bg (and the
    correct per-gap factors 1.69 / 2.13).
W5  determinism of the agent's counts and beliefs across processes.
W6  tau=0 and the rot arm never act on a belief.
W7  NEGATIVE CONTROLS -- the checks CAN go red: W1's positive leg fails
    on a flat world, and W2's blindness leg fails on a gap above the
    gate. A check that cannot go red checks nothing.
"""
import json
import math
import os
import random
import subprocess
import sys

from agent_emca_v8 import (two_prop_z, gamma_of, fisher_exact_2x2,
                           AgentV8, RR_ACCEPT)
from env_terrarium_v8 import GAP_PEDGE, P_BG, MOMENTUM_BONUS

HERE = os.path.dirname(os.path.abspath(__file__))
fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    if not cond:
        fails.append(name)


def sim_tables(p_edge, p_bg, n, reps, seed=0, single=False):
    """`reps` synthetic epochs at n trials/action, 3 actions; action 0 is
    the cause. Returns (sign_correct, mean_gamma_true, mean_gamma_false,
    frozen_fires). `single=True` grades the true action against a SINGLE
    control (the frozen rule's contrast form) instead of the pooled
    others -- used only by the negative control."""
    rng = random.Random(seed)
    correct = 0
    g_true = 0.0
    g_false = 0.0
    frozen = 0
    for _ in range(reps):
        h = []
        for a in range(3):
            p = p_edge if a == 0 else p_bg
            h.append(sum(1 for _ in range(n) if rng.random() < p))
        # graded: argmax z over pooled-others
        best, bz, bg = None, None, None
        for a in range(3):
            oh = sum(h) - h[a]
            on = 2 * n
            z = two_prop_z(h[a], n, oh, on)
            if bz is None or z > bz:
                best, bz, bg = a, z, gamma_of(z)
        correct += 1 if best == 0 else 0
        if single:
            zt = two_prop_z(h[0], n, h[1], n)
            g_true += gamma_of(zt)
            for a in (1, 2):
                g_false += gamma_of(two_prop_z(h[a], n, h[0], n))
        else:
            g_true += gamma_of(two_prop_z(h[0], n, sum(h) - h[0], 2 * n))
            for a in (1, 2):
                g_false += gamma_of(two_prop_z(h[a], n, sum(h) - h[a], 2 * n))
        # frozen rule: target = highest-rate action, control = first other
        cand = max(range(3), key=lambda a: h[a] / n)
        others = [b for b in range(3) if b != cand]
        c = others[0]
        rr = (h[cand] / n) / (h[c] / n) if h[c] else float("inf")
        p = fisher_exact_2x2(h[cand], h[c], n - h[cand], n - h[c])
        if p < 0.05 and rr >= RR_ACCEPT:
            frozen += 1
    return correct / reps, g_true / reps, g_false / (2 * reps), frozen / reps


def first_n_frozen(p_edge, p_bg, reps=300, seed=0):
    """Smallest n (per action) at which the frozen rule fires in >50% of
    synthetic epochs."""
    for n in (10, 20, 30, 40, 50, 60, 80, 100, 140, 200, 320, 480, 640,
              960, 1280, 1600, 2000):
        _, _, _, f = sim_tables(p_edge, p_bg, n, reps, seed)
        if f > 0.5:
            return n
    return None


def first_n_gamma(p_edge, p_bg, reps=600, seed=0, thresh=0.5, single=False):
    """Smallest n at which mean gamma on the TRUE action exceeds `thresh`.
    `single=True` uses the SINGLE-control contrast (the deliberately
    mis-specified instrument) for the negative control."""
    for n in (2, 3, 4, 5, 6, 8, 10, 14, 20, 30, 40, 60, 80, 120, 160, 240):
        _, gt, _, _ = sim_tables(p_edge, p_bg, n, reps, seed, single=single)
        if gt > thresh:
            return n
    return None


def firing_curve(p_edge, p_bg, ns, reps=400, seed=0):
    """Firing rate of the frozen rule at each n in `ns`."""
    return [(n, sim_tables(p_edge, p_bg, n, reps, seed)[3]) for n in ns]


def main():
    print("=== V8 TOY / SYNTHETIC UNITS ===")

    # ---- W1: the sign ----
    acc, gt, gf, frozen = sim_tables(0.55, 0.35, 400, 2000, seed=1)
    check("W1 sign correct at gap 0.20", acc > 0.99,
          f"(argmax-z correct {acc:.3f}; gamma true {gt:.3f} > false {gf:.3f})")
    acc0, gt0, gf0, _ = sim_tables(0.35, 0.35, 400, 2000, seed=2)
    check("W1 no signal at gap 0", acc0 < 0.45,
          f"(flat world: argmax-z correct {acc0:.3f} ~ 1/3)")
    check("W1 gamma does not separate truth under the null",
          abs(gt0 - gf0) < 0.03,
          f"(true {gt0:.4f} vs false {gf0:.4f}; tol 0.03, A12)")

    # ---- W2: the frozen rule's shape below its ratio gate ----
    NS = (20, 40, 60, 100, 200, 500, 1000, 2000)
    lo = firing_curve(0.45, 0.35, NS, reps=600, seed=3)   # ratio 1.286 < 1.3
    xs = [n for n, _ in lo]
    fs = [f for _, f in lo]
    imax = fs.index(max(fs))
    nonmono = 0 < imax < len(fs) - 1 and fs[-1] < max(fs) - 0.02
    print("  W2 curve gap 0.10 (below the gate): "
          + "  ".join(f"{n}:{f:.2f}" for n, f in lo))
    check("W2 frozen rule below the gate is NON-MONOTONE in n",
          nonmono, f"(max {max(fs):.3f} at n={xs[imax]}, at n=2000 {fs[-1]:.3f})")
    check("W2 gamma monotone increasing at gap 0.10",
          all(sim_tables(0.45, 0.35, a, 600, 4)[1]
              <= sim_tables(0.45, 0.35, b, 600, 4)[1] + 0.02
              for a, b in ((20, 60), (60, 200), (200, 1000))),
          f"(mean gamma: n=20 {sim_tables(0.45,0.35,20,600,4)[1]:.3f}, "
          f"n=200 {sim_tables(0.45,0.35,200,600,4)[1]:.3f}, "
          f"n=1000 {sim_tables(0.45,0.35,1000,600,4)[1]:.3f})")
    hi = firing_curve(0.55, 0.35, NS, reps=400, seed=5)
    fh = [f for _, f in hi]
    check("W2 frozen rule above the gate is monotone increasing",
          all(fh[i] <= fh[i + 1] + 0.03 for i in range(len(fh) - 1))
          and fh[-1] > 0.9,
          f"(n=2000 {fh[-1]:.2f})")
    for pe, lbl in ((0.40, "0.05"), (0.38, "0.03")):
        f2 = sim_tables(pe, 0.35, 2000, 600, seed=6)[3]
        check(f"W2 frozen rule silent at gap {lbl}, n=2000", f2 < 0.01,
              f"(fired {f2:.4f})")

    # ---- W3: evidence-demand ratio above the gate ----
    n_f = first_n_frozen(0.55, 0.35, reps=400, seed=7)
    n_g = first_n_gamma(0.55, 0.35, reps=400, seed=7)
    ratio = (n_f / n_g) if (n_f and n_g) else None
    check("W3 evidence-demand ratio in [8,18]",
          ratio is not None and 8.0 <= ratio <= 18.0,
          f"(n_frozen {n_f} / n_gamma {n_g} = {ratio})")

    # ---- W4: persistence arithmetic ----
    for gap, pe in (("0.20", 0.55), ("0.10", 0.45)):
        inflated = pe * (1 + MOMENTUM_BONUS)
        obs_gap = inflated - P_BG
        true_gap = pe - P_BG
        print(f"  W4 gap {gap}: inflated contrast {obs_gap:.4f} "
              f"(true {true_gap:.4f}, factor {obs_gap/true_gap:.2f})")
        check(f"W4 arithmetic gap {gap}", abs(obs_gap - (pe * 1.25 - P_BG)) < 1e-9)
    check("W4 factors match the prereg (1.69 / 2.13)",
          abs((0.55 * 1.25 - 0.35) / 0.20 - 1.6875) < 1e-9 and
          abs((0.45 * 1.25 - 0.35) / 0.10 - 2.125) < 1e-9)

    # ---- W5: determinism across processes ----
    code = ("import sys;sys.path.insert(0,'%s');"
            "from run_life_v8 import run;"
            "L=run('graded',9,'0.10',0.0,False,True,6000);"
            "print(L['total_reward'],L['steps_belief'],L['steps_gathering'],"
            "L['per_epoch_pays'])" % HERE)
    outs = []
    for _ in range(2):
        r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True, env={**os.environ, "PYTHONHASHSEED": "0"})
        outs.append(r.stdout.strip())
    check("W5 determinism across processes", outs[0] == outs[1] and outs[0],
          f"({outs[0][:70]})")

    # ---- W6: tau=0 and rot never act on a belief ----
    from run_life_v8 import run
    for arm in ("rot",):
        L = run(arm, 2, "0.20", 0.0, False, True, 8000)
        check(f"W6 {arm} never acts on a belief", L["steps_belief"] == 0,
              f"(steps_belief {L['steps_belief']})")
    L = run("graded_t00", 2, "0.20", 0.0, False, True, 8000) \
        if "graded_t00" in __import__("run_life_v8").ARMS else None
    # graded with tau=0 is the rot arm's construction; check via the agent
    ag = AgentV8(2, mode="graded", tau=0.0)
    acts = []
    for t in range(4000):
        o = {"t": t, "epoch_id": 0, "afford": ["wait", "press", "grasp"]}
        acts.append(ag.act(o))
        ag.observe(o, acts[-1], 100.0 if acts[-1] == "wait" else 0.0,
                   o, False, {"epoch": 0})
    check("W6 tau=0 never acts on a belief", ag.steps_belief == 0,
          f"(steps_belief {ag.steps_belief}, gathered {ag.steps_gathering})")

    # ---- W7: negative controls - the checks CAN go red ----
    # W1's positive leg on a flat world must FAIL
    acc_flat = sim_tables(0.35, 0.35, 400, 400, seed=7)[0]
    check("W7 negative control: W1 positive leg fails on a flat world",
          acc_flat < 0.45, f"(flat acc {acc_flat:.3f})")
    # W2's non-monotonicity leg must FAIL on a gap above the gate
    f_hi = [f for _, f in hi]
    check("W7 negative control: W2 non-monotonicity leg fails above the gate",
          all(f_hi[i] <= f_hi[i + 1] + 0.03 for i in range(len(f_hi) - 1))
          and not (0 < f_hi.index(max(f_hi)) < len(f_hi) - 1
                   and f_hi[-1] < max(f_hi) - 0.02),
          f"(above the gate the curve is monotone: {[round(x,2) for x in f_hi]})")
    # W3's band must FAIL when deliberately applied to a gap BELOW the
    # gate: there the frozen rule never reaches a 50% firing rate at any
    # n tested, so its evidence demand has no finite value and the ratio
    # is undefined -- the live measurement of the claim, and the red that
    # proves the band is doing work rather than always printing PASS.
    n_f_lo = first_n_frozen(0.40, 0.35, reps=400, seed=7)
    check("W7 negative control: W3 band has no finite value below the gate",
          n_f_lo is None,
          f"(gap 0.05: frozen rule never fires >50% at any n tested; "
          f"n_frozen={n_f_lo} -> the [8,18] band cannot be satisfied)")

    print()
    if fails:
        print("TOY V8: FAIL", fails)
        raise SystemExit(1)
    print("TOY V8: ALL PASS")


if __name__ == "__main__":
    main()
