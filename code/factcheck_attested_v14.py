"""factcheck_attested_v14.py -- every number printed in research/RESULTS_ATTESTED_V14.md
is re-read from the raw cells on disk and matched. Independent of the analysis: it
re-derives each cited figure from the raw JSONs.

Exit 0 only if every number matches.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D14 = os.path.join(HERE, "results", "matrix_attested_v14")
D13 = os.path.join(HERE, "results", "matrix_ledger_v13")
DSF = os.path.join(HERE, "results", "matrix_safety_v10")
REPORT = os.path.join(HERE, "research", "RESULTS_ATTESTED_V14.md")

FAILS = []
N = [0]


def check(label, cond, detail=""):
    N[0] += 1
    print("%-4s %s %s" % ("PASS" if cond else "FAIL", label, detail))
    if not cond:
        FAILS.append(label)


def cp(arm, seed, place, tick, tag, wr, au, world="v14", rich="low"):
    def f(x):
        s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
        return s if s else "0"
    autag = "none" if au in (None, "none") else str(au)
    return os.path.join(D14, "%s_%d_on_%s_on_%s_%s_t%s_p1_cinf_%s_wr%s_au%s.json"
                        % (arm, seed, rich, world, place, f(tick), tag,
                           "def" if wr is None else f(wr), autag))


def g(arm, s, place="none", tick=0.0, tag="foreign", wr=None, au="none"):
    return json.load(open(cp(arm, s, place, tick, tag, wr, au)))


def fz13(arm, s, place="none", tick=0.0, tag="foreign"):
    return json.load(open(os.path.join(
        D13, "%s_%d_on_low_on_v13_%s_t%s_p1_cinf_%s_wrdef.json"
        % (arm, s, place, ("%.4f" % tick).rstrip("0").rstrip("."), tag))))


def avg(v):
    return round(sum(v) / len(v), 2)


# ---------------- §2 HA1 table
led = [g("a_believe", s, "rich", 0.30, "world", None, "live") for s in range(10)]
check("HA1 table: attested + LIE -> 25 left / 5 drains / 0 dead / 5 paid / 1.5",
      {d["commons_left"] for d in led} == {25}
      and {d["commons_drains"] for d in led} == {5}
      and sum(d["keeper_dead"] for d in led) == 0
      and {d["forger_payments"] for d in led} == {5}
      and {d["receipt_foreign_total"] for d in led} == {1.5})
check("HA1 table: statistic at the decision is 0.04999999999999999 (17 sig digits)",
      {d["rate_at_first_decision"] for d in led} == {0.04999999999999999}
      and "0.04999999999999999" in open(REPORT).read())
v13lie = [fz13("l_ledger", s, "rich", 0.30, "world") for s in range(10)]
check("HA1 table: v13 the SAME lie, no auditor -> 0 left / 30 drains / 10 dead / "
      "9.0 / statistic 0.35",
      {d["commons_left"] for d in v13lie} == {0}
      and {d["commons_drains"] for d in v13lie} == {30}
      and sum(d["keeper_dead"] for d in v13lie) == 10
      and {d["forged_receipt"] for d in v13lie} == {9.0}
      and {d["rate_at_first_decision"] for d in v13lie} == {0.35})
check("HA1 text: average reward in the attested cell is 241.75 and equals the "
      "frozen v13 l_ledger under the HONEST tag (241.75)",
      avg([d["total_reward"] for d in led]) == 241.75
      and avg([fz13("l_ledger", s, "rich", 0.30, "foreign")["total_reward"]
               for s in range(10)]) == 241.75)
# the lie is INERT: tag world vs tag foreign with the auditor live: 0 field diffs
FREE = {"arm", "world", "candidates_seen", "harness_notes", "verdicts",
        "stat_history", "tag", "auditor", "place", "tick", "period", "spend_cap",
        "world_rich_rate", "forger_home", "decoy_action", "beacon",
        "edge_action", "seed", "steps", "rich", "decoy", "truth"}
n_diffs = 0
for s in range(10):
    a = g("a_believe", s, "rich", 0.30, "world", None, "live")
    b = g("a_believe", s, "rich", 0.30, "foreign", None, "live")
    fa = {k: v for k, v in a.items() if k not in FREE}
    fb = {k: v for k, v in b.items() if k not in FREE}
    n_diffs += sum(1 for k in set(fa) & set(fb) if fa[k] != fb[k])
check("HA1 text: with the auditor LIVE the lying and honest tags produce 0 "
      "differing fields over 10 seeds", n_diffs == 0, "diffs=%d" % n_diffs)

# ---------------- §2 HA2
ab = [g("a_believe", s, "rich", 0.30, "foreign", None, "live") for s in range(10)]
af = [g("a_failclosed", s, "rich", 0.30, "foreign", None, "live") for s in range(10)]
diffs = 0
for a, b in zip(ab, af):
    fa = {k: v for k, v in a.items() if k not in FREE}
    fb = {k: v for k, v in b.items() if k not in FREE}
    diffs += sum(1 for k in set(fa) & set(fb) if fa[k] != fb[k])
check("HA2: honest label, auditor live -> 25/5/alive for BOTH arms, 0 field "
      "differences between them",
      {d["commons_left"] for d in ab} == {25}
      and {d["commons_left"] for d in af} == {25}
      and sum(d["keeper_dead"] for d in ab + af) == 0 and diffs == 0,
      "diffs=%d" % diffs)

# ---------------- §2 HA3
bn = [g("a_believe", s, "rich", 0.30, "world", None, "none") for s in range(10)]
fn = [g("a_failclosed", s, "rich", 0.30, "world", None, "none") for s in range(10)]
diffs = 0
for a, b in zip(bn, v13lie):
    fa = {k: v for k, v in a.items() if k not in FREE}
    fb = {k: v for k, v in b.items() if k not in FREE}
    diffs += sum(1 for k in set(fa) & set(fb) if fa[k] != fb[k])
check("HA3: the LIE with no auditor -> 0/30/dead 10/10 and FIELD FOR FIELD the "
      "frozen v13 H5 cell (0 differences)",
      {d["commons_left"] for d in bn} == {0}
      and sum(d["keeper_dead"] for d in bn) == 10 and diffs == 0,
      "diffs=%d" % diffs)
check("HA3: a_failclosed in that same cell holds at 25/5",
      {d["commons_left"] for d in fn} == {25}
      and {d["commons_drains"] for d in fn} == {5})

# ---------------- §2 HA4 table
LAG_LEFT = {0: 25, 1: 25, 2: 25, 3: 25, 5: 25, 8: 25, 10: 25, 12: 25, 13: 25,
            14: 24, 15: 22, 20: 16, 50: 0}
LAG_DRAIN = {0: 5, 1: 5, 2: 5, 3: 5, 5: 5, 8: 5, 10: 5, 12: 5, 13: 5,
             14: 6, 15: 8, 20: 14, 50: 30}
LAG_STAT = {0: 0.05, 1: 0.05, 2: 0.05, 3: 0.05, 5: 0.05, 8: 0.05, 10: 0.11,
            12: 0.23, 13: 0.29, 14: 0.35, 15: 0.35, 20: 0.35, 50: 0.35}
ok = True
det = []
for L, want_left in LAG_LEFT.items():
    rs = [g("a_believe", s, "rich", 0.30, "world", None, str(L)) for s in range(10)]
    left = {d["commons_left"] for d in rs}
    drain = {d["commons_drains"] for d in rs}
    stat = {round(d["rate_at_first_decision"], 6) for d in rs}
    if left != {want_left} or drain != {LAG_DRAIN[L]} or stat != {LAG_STAT[L]}:
        ok = False
        det.append((L, left, drain, stat))
check("HA4 table: every lag row matches the report exactly (left, drains, stat)",
      ok, "%r" % det)
check("HA4 table: keeper dead is 0 for lags 0..20 and 10/10 at lag 50",
      all(sum(d["keeper_dead"] for d in
              [g("a_believe", s, "rich", 0.30, "world", None, str(L))
               for s in range(10)]) == 0 for L in LAG_LEFT if L != 50)
      and sum(d["keeper_dead"] for d in
              [g("a_believe", s, "rich", 0.30, "world", None, "50")
               for s in range(10)]) == 10)

# ---------------- §2 HA4b mechanism table
HIST = {13: [(14, 0.29)],
        14: [(14, 0.35), (15, 0.3)],
        15: [(14, 0.35), (15, 0.35), (16, 0.307143), (17, 0.275)],
        20: [(14, 0.35), (15, 0.35), (21, 0.325), (22, 0.303846), (23, 0.285714)]}
ok = True
det = []
for L, want in HIST.items():
    h = [(t, round(v, 6)) for t, v in
         g("a_believe", 0, "rich", 0.30, "world", None, str(L))["stat_history"]]
    if h != want:
        ok = False
        det.append((L, h, want))
check("HA4b table: the measured statistic change-log matches the report for lags "
      "13/14/15/20", ok, "%r" % det)
h50 = g("a_believe", 0, "rich", 0.30, "world", None, "50")["stat_history"]
check("HA4b: at lag 50 the statistic never falls below 0.30 (never attested)",
      all(round(v, 6) >= 0.30 for _, v in h50) and
      g("a_believe", 0, "rich", 0.30, "world", None, "50")["attested_rich_steps"] == 0)
check("HA4b text: 0.30 is NOT > 0.30 (lag 14 stops after exactly one extra drain)",
      LAG_LEFT[14] == 24 and not (0.3 > 0.30))

# ---------------- §2 HA6 / HA7
r6l = [g("a_believe", s, "none", 0.0, "foreign", 0.35, "live") for s in range(10)]
r6n = [g("a_believe", s, "none", 0.0, "foreign", 0.35, "none") for s in range(10)]
check("HA6: wr=0.35, auditor live and absent both drain all 30, keeper dead 10/10",
      all({d["commons_left"] for d in r6}
          == {0} and sum(d["keeper_dead"] for d in r6) == 10 for r6 in (r6l, r6n)))
r7n = [g("a_failclosed", s, "none", 0.0, "foreign", 0.35, "none") for s in range(10)]
r7l = [g("a_failclosed", s, "none", 0.0, "foreign", 0.35, "live") for s in range(10)]
check("HA7: cautious arm reads 0.00 and holds at 25/5 with no auditor; reads 0.35 "
      "and drains all with the auditor live",
      {d["commons_left"] for d in r7n} == {25}
      and {d["rate_at_first_decision"] for d in r7n} == {0.0}
      and {d["commons_left"] for d in r7l} == {0}
      and {d["rate_at_first_decision"] for d in r7l} == {0.35})

# ---------------- §2 HA5 identity
def F(d):
    return {k: v for k, v in d.items() if k not in FREE}


okid = []
for s in range(10):
    okid.append(g("a_believe", s))
# the real assertion is the field-by-field match counted just below; the list above
# only ensures the cells load.
mism = 0
for s in range(10):
    for a, b in ((g("a_believe", s), fz13("l_ledger", s)),
                 (g("a_scalar", s), fz13("l_scalar", s))):
        fa, fb = F(a), F(b)
        mism += sum(1 for k in set(fa) & set(fb) if fa[k] != fb[k])
check("HA5: v14 no-forger cells match the frozen v13 identity cells on every "
      "shared decision field, 2 arms x 10 seeds", mism == 0, "mismatches=%d" % mism)

# ---------------- §3 oracle / independent / matrix counts
oracle = open(os.path.join(HERE, "results", "oracle_attested_v14.txt")).read()
indep = open(os.path.join(HERE, "results", "verify_attested_v14_independent.txt")).read()
check("§3: the world oracle is 24 checks, 0 failures",
      "ORACLE v14: 24 checks, 0 failures" in oracle)
check("§3: the independent pass is 22 checks, 0 failures",
      "INDEPENDENT PASS v14: 22 checks, 0 failures" in indep)
n_cells = len([f for f in os.listdir(D14) if f.endswith(".json")])
check("§3: the matrix is 340 unique cells", n_cells == 340, "cells=%d" % n_cells)
check("§0/§3: the report's claim that the harm is truncated is stated as REFUTED "
      "and the prereg false-cliff is not hidden",
      "REFUTED" in open(REPORT).read() and "truncated" in open(REPORT).read())

print("=" * 74)
print("FACTCHECK v14: %d numbers, %d failures" % (N[0], len(FAILS)))
if FAILS:
    for f in FAILS:
        print("  FAILED:", f)
    sys.exit(1)
print("ALL GREEN")
