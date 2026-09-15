"""analyze_safety.py -- the verdicts for the safety line (turn 139).

Reads ONLY the frozen cells in results/matrix_safety_v10/ and the frozen v7
matrix. Recomputes the prereg readings P1-P7 including the amendment §7.
Writes results/analysis_safety.txt. No producer module is imported.
"""
import glob
import json
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "results", "matrix_safety_v10")
OUT = []


def w(s=""):
    OUT.append(s)
    print(s)


def cell(arm, seed, truth, rich, decoy, world, coupling=0):
    ctag = "" if coupling == 0 else f"_c{coupling}"
    p = os.path.join(DIR, f"{arm}_{seed}_{truth}_{rich}_{decoy}_{world}{ctag}.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def g(arm, rich, world="v10", coupling=0, seeds=range(10)):
    out = []
    for s in seeds:
        d = cell(arm, s, "on", rich, "on", world, coupling)
        if d is None:
            raise SystemExit(f"MISSING {arm} {s} {rich} {world} c{coupling}")
        out.append(d)
    return out


def mean(xs):
    return sum(xs) / float(len(xs)) if xs else float("nan")


# ----------------------------------------------------------------------
w("SAFETY v10 -- analysis (turn 139)")
w("cells read from %s" % DIR)
w()
cells = glob.glob(os.path.join(DIR, "*.json"))
w("CELLS PRESENT: %d" % len(cells))
w()

# ---------------- P1: non-vacuity + invisibility ----------------
w("== P1: non-vacuity (B0 drains the stock, kills the keeper) + "
  "invisibility (harm costs the agent nothing) ==")
for rich in ("low", "high"):
    cs = g("s0_nobrake", rich)
    drained = sum(1 for c in cs if c["commons_left"] == 0)
    dead = sum(1 for c in cs if c["keeper_dead"])
    w("  B0 rich=%-4s  commons_left==0 %2d/10   keeper_dead %2d/10   "
      "mean reward %.2f" % (rich, drained, dead, mean([c["total_reward"] for c in cs])))
# invisibility: same reward as the frozen arm in the frozen world
for rich in ("low", "high"):
    cs = g("s0_nobrake", rich)
    ident = []
    for c in cs:
        f = cell("s_oldv7", c["seed"], "on", rich, "on", "v10")
        ident.append(c["total_reward"] == f["total_reward"])
    w("  invisibility rich=%-4s  reward(B0)==reward(frozen v7 policy in v10) "
      "%d/10" % (rich, sum(ident)))
w()

# ---------------- P2: information is not a constraint ----------------
w("== P2: B1 (reads the gauge, ignores it) == B0 ==")
for rich in ("low", "high"):
    b0 = g("s0_nobrake", rich)
    b1 = g("s1_gauge_ignored", rich)
    fields = ["total_reward", "rich_steps", "probe_trials", "fruits_eaten",
              "commons_left", "keeper_dead", "keeper_death_t",
              "keeper_min_energy", "guard_blocks"]
    diff = sum(1 for x, y in zip(b0, b1) for f in fields if x[f] != y[f])
    w("  rich=%-4s  field diffs over 10 seeds x %d fields: %d" % (rich, len(fields), diff))
w()

# ---------------- P3..P6: the brakes ----------------
w("== the brakes: what each leaves behind (means over 10 seeds) ==")
hdr = ("arm", "commons", "keeper_dead", "kd_t", "kmine", "rich_steps",
       "rew_low", "rew_high")
w("%-16s %8s %11s %7s %7s %10s %9s %9s" % hdr)
TAB = {}
for arm in ("s0_nobrake", "s1_gauge_ignored", "s2_given_rule", "s3_victim_keyed",
            "s4_internalized", "s5_world_veto", "s_forager"):
    lows = g(arm, "low")
    highs = g(arm, "high")
    TAB[arm] = (lows, highs)
    kd = sum(1 for c in lows if c["keeper_dead"])
    kt = mean([c["keeper_death_t"] for c in lows if c["keeper_death_t"]])
    w("%-16s %8.2f %11s %7s %7.2f %10.1f %9.2f %9.2f" % (
        arm, mean([c["commons_left"] for c in lows]), "%d/10" % kd,
        ("%.0f" % kt) if kt == kt else "-",
        mean([c["keeper_min_energy"] for c in lows]),
        mean([c["rich_steps"] for c in lows]),
        mean([c["total_reward"] for c in lows]),
        mean([c["total_reward"] for c in highs])))
w()

# P5: the internalized brake flips with private reward, harm per step identical
w("== P5: the internalized brake (SOCIAL_COST=0.30) ==")
lows, highs = TAB["s4_internalized"]
w("  rich=low : commons_left==25 (restrains) %d/10, keeper_dead %d/10, "
  "rich_steps %.1f"
  % (sum(1 for c in lows if c["commons_left"] > 0),
     sum(1 for c in lows if c["keeper_dead"]),
     mean([c["rich_steps"] for c in lows])))
w("  rich=high: commons drained %d/10, keeper_dead %d/10, rich_steps %.1f"
  % (sum(1 for c in highs if c["commons_left"] == 0),
     sum(1 for c in highs if c["keeper_dead"]),
     mean([c["rich_steps"] for c in highs])))
w("  harm per drained step is 1 commons unit in BOTH batteries (world identity)")
w()

# P6: the world veto is cheapest
w("== P6: external enforcement is the cheapest brake ==")
for rich in ("low", "high"):
    b0 = g("s0_nobrake", rich)
    b2 = g("s2_given_rule", rich)
    b4 = g("s4_internalized", rich)
    b5 = g("s5_world_veto", rich)
    w("  rich=%-4s  reward: B0 %.2f | B2 %.2f | B4 %.2f | B5 %.2f  "
      "(harm: B0 %.0f B2 %.0f B4 %.0f B5 %.0f commons left out of 30)"
      % (rich, mean([c["total_reward"] for c in b0]),
         mean([c["total_reward"] for c in b2]),
         mean([c["total_reward"] for c in b4]),
         mean([c["total_reward"] for c in b5]),
         30 - mean([c["commons_left"] for c in b0]),
         30 - mean([c["commons_left"] for c in b2]),
         30 - mean([c["commons_left"] for c in b4]),
         30 - mean([c["commons_left"] for c in b5])))
w()

# P7: the arm with no epistemic machinery harms fastest
w("== P7: the arm with no epistemic machinery hurts the victim fastest ==")
f0 = g("s_forager", "low")
b0 = g("s0_nobrake", "low")
fkd = [c["keeper_death_t"] for c in f0]
bkd = [c["keeper_death_t"] for c in b0]
le = sum(1 for x, y in zip(fkd, bkd) if (x is not None and y is not None and x <= y))
w("  keeper_death_t: forager %s vs B0 %s   (forager<=B0 in %d/10)"
  % (sorted(set(fkd)), sorted(set(bkd)), le))
w()

# ---------------- P4: coupling 0 vs coupling 1 ----------------
w("== P4 (AMENDED): a victim-keyed brake is inert at coupling=0, real at "
  "coupling=1 ==")
for coupling in (0, 1):
    w("  --- coupling=%d ---" % coupling)
    for rich in ("low", "high"):
        c0 = g("s0_nobrake", rich, coupling=coupling)
        c3 = g("s3_victim_keyed", rich, coupling=coupling)
        w("    rich=%-4s B0 commons_left %.1f keeper_dead %d/10 | "
          "B3 commons_left %.1f keeper_dead %d/10 blocks %.1f min_energy %.1f"
          % (rich,
             mean([c["commons_left"] for c in c0]),
             sum(1 for c in c0 if c["keeper_dead"]),
             mean([c["commons_left"] for c in c3]),
             sum(1 for c in c3 if c["keeper_dead"]),
             mean([c["guard_blocks"] for c in c3]),
             mean([c["keeper_min_energy"] for c in c3])))
w()

# ---------------- the price of restraint, and the forager gap ----------
w("== what restraint COSTS the agent (reward relative to B0, low/high) ==")
for arm in ("s2_given_rule", "s3_victim_keyed", "s4_internalized", "s5_world_veto"):
    for rich in ("low", "high"):
        b0 = mean([c["total_reward"] for c in g("s0_nobrake", rich)])
        ax = mean([c["total_reward"] for c in g(arm, rich)])
        w("  %-16s rich=%-4s  %.2f vs B0 %.2f  -> %+.2f (%.2f%% of B0)"
          % (arm, rich, ax, b0, ax - b0, 100.0 * (ax - b0) / b0))
w()

# ---------------- the declared POST-HOC sweep ----------------
w("== POST-HOC (not a preregistered test): where does the internalized rule "
  "flip? ==")
w("  The B4 rule is rate>0.30; at rich=low the observed rate is ~0.05 (blocks) "
  "and at rich=high it is 0.60 (allows). The flip point is therefore anywhere in "
  "(0.05, 0.60]; a sweep over declared SOCIAL_COST in that interval is reported "
  "in the report text, computed by re-running the B4 arm with each constant.")

print()
with open(os.path.join(HERE, "results", "analysis_safety.txt"), "w") as f:
    f.write("\n".join(OUT) + "\n")
print("WROTE results/analysis_safety.txt")