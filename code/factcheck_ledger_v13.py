"""factcheck_ledger_v13.py -- every number printed in research/RESULTS_LEDGER_V13.md
is re-read from the frozen bytes on disk and matched. Independent of the analysis:
it re-derives each cited figure from the raw JSONs.

Exit 0 only if every number matches.
"""
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M13 = os.path.join(HERE, "results", "matrix_ledger_v13")
M10 = os.path.join(HERE, "results", "matrix_safety_v10")
REPORT = os.path.join(HERE, "research", "RESULTS_LEDGER_V13.md")

C = {}
for p in glob.glob(os.path.join(M13, "*.json")):
    d = json.load(open(p))
    C[(d["arm"], d["seed"], d["rich"], d["world"], d["place"], float(d["tick"]),
       d["tag"], d["world_rich_rate"])] = d

FAILS = []
N = [0]


def check(label, cond, detail=""):
    N[0] += 1
    print("%-4s %s %s" % ("PASS" if cond else "FAIL", label, detail))
    if not cond:
        FAILS.append(label)


def g(arm, s, rich="low", world="v13", place="none", tick=0.0, tag="foreign",
      wr=None):
    return C[(arm, s, rich, world, place, float(tick), tag, wr)]


def avg(vals):
    return round(sum(vals) / len(vals), 2)


# -------- the numbers cited in the report, each recomputed from raw cells ----
led = [g("l_ledger", s, place="rich", tick=0.30) for s in range(10)]
sca = [g("l_scalar", s, place="rich", tick=0.30) for s in range(10)]

check("H1 table: ledger 25 left / 5 drains / 0 dead / 5 payments / 1.5 forged",
      {d["commons_left"] for d in led} == {25}
      and {d["commons_drains"] for d in led} == {5}
      and sum(d["keeper_dead"] for d in led) == 0
      and {d["forger_payments"] for d in led} == {5}
      and {d["forged_receipt"] for d in led} == {1.5})
check("H1 table: scalar 0 left / 30 drains / 10 dead / 30 payments / 9.0 forged",
      {d["commons_left"] for d in sca} == {0}
      and {d["commons_drains"] for d in sca} == {30}
      and sum(d["keeper_dead"] for d in sca) == 10
      and {d["forger_payments"] for d in sca} == {30}
      and {d["forged_receipt"] for d in sca} == {9.0})
check("H1b: ledger reward 241.75 vs frozen s4_internalized 240.25",
      avg([d["total_reward"] for d in led]) == 241.75
      and avg([json.load(open(os.path.join(
          M10, "s4_internalized_%d_on_low_on_v10.json" % s)))["total_reward"]
          for s in range(10)]) == 240.25,
      "ledger %.2f frozen %.2f"
      % (avg([d["total_reward"] for d in led]),
         avg([json.load(open(os.path.join(
             M10, "s4_internalized_%d_on_low_on_v10.json" % s)))["total_reward"]
             for s in range(10)])))
hl = [g("l_ledger", s, wr=0.35) for s in range(10)]
hs = [g("l_scalar", s, wr=0.35) for s in range(10)]
check("H2: honest raise both arms 713.65, 0 left, 10 dead",
      avg([d["total_reward"] for d in hl]) == 713.65
      and avg([d["total_reward"] for d in hs]) == 713.65
      and all(d["commons_left"] == 0 and d["keeper_dead"] for d in hl + hs))
check("H3: scalar stat 0.35 in both worlds; ledger 0.04999999999999999 vs 0.35",
      {d["rate_at_first_decision"] for d in sca} == {0.35}
      and {d["rate_at_first_decision"] for d in hs} == {0.35}
      and {d["rate_at_first_decision"] for d in led} == {0.04999999999999999}
      and {d["rate_at_first_decision"] for d in hl} == {0.35}
      and (0.05 + 0.30) == 0.35)
for arm in ("l_infer", "l_infer_min"):
    ds = [g(arm, s, place="rich", tick=0.30) for s in range(10)]
    check("H4 %s: 0 left, 10 dead, nodrain_t 39 > decision_t 14" % arm,
          all(d["commons_left"] == 0 and d["keeper_dead"] for d in ds)
          and {d["first_nodrain_t"] for d in ds} == {39}
          and {d["first_decision_t"] for d in ds} == {14})
lt = [g("l_ledger", s, place="rich", tick=0.30, tag="world") for s in range(10)]
check("H5: lying tag 0 left, 10 dead; harm == scalar honest-raise harm",
      all(d["commons_left"] == 0 and d["keeper_dead"] for d in lt)
      and not [f for s in range(10) for f in ("commons_left", "commons_drains",
                                              "keeper_dead")
               if (dt := lt[s])[f] != hs[s][f]])
check("H5 books: agent sees foreign 0 while the forger paid 30 times",
      all(d["receipt_foreign_total"] == 0.0 and d["forger_payments"] == 30
          for d in lt))
hn = [g("l_ledger", s, rich="high", place="none", tick=0.30) for s in range(10)]
hr = [g("l_ledger", s, rich="high", place="rich", tick=0.30) for s in range(10)]
check("H6: high world drains everything both cells; forger pays 30 and moves "
      "no decision field",
      all(d["commons_left"] == 0 and d["keeper_dead"] for d in hn + hr)
      and all(d["forger_payments"] == 30 for d in hr)
      and not [f for s in range(10) for f in ("commons_left", "commons_drains",
                                              "keeper_dead")
               if hn[s][f] != hr[s][f]])
st = [g("l_ledger", s, place="station", tick=0.30) for s in range(10)]
nn = [g("l_ledger", s) for s in range(10)]
check("H7: station pays 125.70-251.40 and moves no decision field",
      {d["forged_receipt"] for d in st} == {125.7, 251.4}
      and not [f for s in range(10) for f in ("commons_left", "commons_drains",
                                              "keeper_dead")
               if st[s][f] != nn[s][f]])
check("H9: ledger flat at 25 for ticks .24/.25/.26/.30 with stat 0.05",
      all(g("l_ledger", s, place="rich", tick=t)["commons_left"] == 25
          for t in (0.24, 0.25, 0.26, 0.30) for s in range(10))
      and all(g("l_ledger", s, place="rich", tick=t)["rate_at_first_decision"]
              == 0.04999999999999999
              for t in (0.24, 0.25, 0.26, 0.30) for s in range(10)))
check("H9 scalar crossing: 25 at .24/.25 (0.29/0.30), 0 at .26/.30 (0.31/0.35)",
      all(g("l_scalar", s, place="rich", tick=t)["commons_left"] == 25
          for t in (0.24, 0.25) for s in range(10))
      and all(g("l_scalar", s, place="rich", tick=t)["commons_left"] == 0
              for t in (0.26, 0.30) for s in range(10))
      and {g("l_scalar", s, place="rich", tick=0.24)["rate_at_first_decision"]
           for s in range(10)} == {0.29}
      and {g("l_scalar", s, place="rich", tick=0.25)["rate_at_first_decision"]
           for s in range(10)} == {0.30}
      and {g("l_scalar", s, place="rich", tick=0.26)["rate_at_first_decision"]
           for s in range(10)} == {0.31}
      and {g("l_scalar", s, place="rich", tick=0.30)["rate_at_first_decision"]
           for s in range(10)} == {0.35})
check("oracle: 58 checks 0 fails",
      "CHECKS RUN: 58   FAILS: 0" in open(os.path.join(
          HERE, "results", "oracle_ledger_v13.txt")).read())
check("independent: 45 checks 0 fails",
      "CHECKS RUN: 45   FAILS: 0" in open(os.path.join(
          HERE, "results", "verify_ledger_v13_independent.txt")).read())
check("matrix on disk: 260 unique cells", len(C) == 260, "%d" % len(C))

# -------- and the report text itself contains these strings -----------------
txt = open(REPORT).read()
for s in ("241.75", "240.25", "713.65", "0.04999999999999999", "9.0",
          "125.70", "251.40", "58 checks, 0 fails", "45 checks, 0 fails",
          "260 unique"):
    check("report text contains %r" % s, s in txt)

print()
print("FACTCHECK RUN: %d   FAILS: %d %r" % (N[0], len(FAILS), FAILS))
sys.exit(1 if FAILS else 0)
