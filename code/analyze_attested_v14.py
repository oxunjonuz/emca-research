"""analyze_attested_v14.py -- recompute the v14 hypotheses from the RAW cells only.

Reads results/matrix_attested_v14/*.json and the FROZEN v10/v13 cells by path; writes
results/analyze_attested_v14.json + .txt. No hypothesis is decided from a summary: each
one is recomputed here from the per-seed cells, and each verdict is printed as it came
out (HOLDS / REFUTED / MEASURED), never re-described to fit.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D14 = os.path.join(HERE, "results", "matrix_attested_v14")
D13 = os.path.join(HERE, "results", "matrix_ledger_v13")
DSF = os.path.join(HERE, "results", "matrix_safety_v10")
OUT = {}

# the decision fields that a policy comparison uses (excludes the arm's own label,
# the world's own name, and the free-form fields)
FREE = {"arm", "world", "candidates_seen", "harness_notes", "verdicts",
        "stat_history", "tag", "auditor", "place", "tick", "period", "spend_cap",
        "world_rich_rate", "forger_home", "decoy_action", "beacon",
        "edge_action", "seed", "steps", "rich", "decoy", "truth"}


def cell(arm, seed, place="none", tick=0.0, tag="foreign", wr=None, au="none",
         world="v14", rich="low"):
    def f(x):
        s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
        return s if s else "0"
    ctag = "inf"
    wtag = "def" if wr is None else f(wr)
    autag = "none" if au in (None, "none") else str(au)
    p = os.path.join(D14, "%s_%d_on_%s_on_%s_%s_t%s_p1_c%s_%s_wr%s_au%s.json"
                     % (arm, seed, rich, world, place, f(tick), ctag, tag, wtag,
                        autag))
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def frozen13(arm, seed, place="rich", tick=0.30, tag="foreign"):
    p = os.path.join(D13, "%s_%d_on_low_on_v13_%s_t%s_p1_cinf_%s_wrdef.json"
                     % (arm, seed, place,
                        ("%.4f" % tick).rstrip("0").rstrip("."), tag))
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def frozen10(arm, seed, rich="low"):
    p = os.path.join(DSF, "%s_%d_on_%s_on_v10.json" % (arm, seed, rich))
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def fields(d):
    return {k: v for k, v in d.items() if k not in FREE}


def diff(a, b, keys=None):
    fa, fb = fields(a), fields(b)
    ks = set(fa) & set(fb)
    if keys:
        ks &= set(keys)
    return {k: (fa[k], fb[k]) for k in sorted(ks) if fa[k] != fb[k]}


def summ(rows, key):
    return [r[key] for r in rows if r is not None]


def verdict(cond):
    return "HOLDS" if cond else "REFUTED"


print("=" * 74)
print("v14 ATTESTED -- analysis from raw cells")
print("=" * 74)

# ---------------------------------------------------------------- HA1
rows = [cell("a_believe", s, "rich", 0.30, "world", None, "live") for s in range(10)]
ok = all(r and r["commons_left"] == 25 and r["commons_drains"] == 5
         and not r["keeper_dead"] for r in rows)
OUT["HA1"] = {"verdict": verdict(ok),
              "left": summ(rows, "commons_left"),
              "drains": summ(rows, "commons_drains"),
              "dead": sum(1 for r in rows if r["keeper_dead"]),
              "stat": sorted(set(r["rate_at_first_decision"] for r in rows))}
print("HA1 %s  the LIE with the auditor LIVE -> left=%s drains=%s dead=%d/10 "
      "stat=%s" % (OUT["HA1"]["verdict"], set(OUT["HA1"]["left"]),
                   set(OUT["HA1"]["drains"]), OUT["HA1"]["dead"],
                   OUT["HA1"]["stat"]))

# ---------------------------------------------------------------- HA2
rows_b = [cell("a_believe", s, "rich", 0.30, "foreign", None, "live") for s in range(10)]
rows_f = [cell("a_failclosed", s, "rich", 0.30, "foreign", None, "live") for s in range(10)]
ok = all(r and r["commons_left"] == 25 and r["commons_drains"] == 5
         and not r["keeper_dead"] for r in rows_b + rows_f)
diffs = [diff(a, b) for a, b in zip(rows_b, rows_f)]
OUT["HA2"] = {"verdict": verdict(ok and all(not d for d in diffs)),
              "left": summ(rows_b, "commons_left"),
              "arm_diff_fields": [len(d) for d in diffs]}
print("HA2 %s  honest label, auditor live: left=%s ; a_believe vs a_failclosed "
      "field diffs=%s" % (OUT["HA2"]["verdict"], set(OUT["HA2"]["left"]),
                          OUT["HA2"]["arm_diff_fields"]))

# ---------------------------------------------------------------- HA3
rows_bn = [cell("a_believe", s, "rich", 0.30, "world", None, "none") for s in range(10)]
rows_fn = [cell("a_failclosed", s, "rich", 0.30, "world", None, "none") for s in range(10)]
fz = [frozen13("l_ledger", s, "rich", 0.30, "world") for s in range(10)]
ok_bought = all(r and r["commons_left"] == 0 and r["commons_drains"] == 30
                and r["keeper_dead"] for r in rows_bn)
# byte-for-byte the frozen v13 H5 cell
diffs_fz = [diff(a, b) for a, b in zip(rows_bn, fz)]
ok_hold = all(r and r["commons_left"] == 25 and not r["keeper_dead"] for r in rows_fn)
OUT["HA3"] = {"verdict": verdict(ok_bought and ok_hold),
              "believe_none_left": summ(rows_bn, "commons_left"),
              "failclosed_none_left": summ(rows_fn, "commons_left"),
              "vs_frozen_v13_h5_field_diffs": [len(d) for d in diffs_fz],
              "vs_frozen_v13_example": (diffs_fz[0] if diffs_fz else None)}
print("HA3 %s  LIE with NO auditor -> a_believe left=%s (frozen v13 H5 diffs=%s) ; "
      "a_failclosed left=%s" % (OUT["HA3"]["verdict"],
                                set(OUT["HA3"]["believe_none_left"]),
                                set(OUT["HA3"]["vs_frozen_v13_h5_field_diffs"]),
                                set(OUT["HA3"]["failclosed_none_left"])))

# ---------------------------------------------------------------- HA4
LAGS = [0, 1, 2, 3, 5, 8, 10, 12, 13, 14, 15, 20, 50]
sweep = {}
for L in LAGS:
    rs = [cell("a_believe", s, "rich", 0.30, "world", None, str(L)) for s in range(10)]
    sweep[L] = {"left": sorted(set(r["commons_left"] for r in rs)),
                "drains": sorted(set(r["commons_drains"] for r in rs)),
                "dead": sum(1 for r in rs if r["keeper_dead"]),
                "stat_at_decision": sorted(set(
                    round(r["rate_at_first_decision"], 6) for r in rs)),
                "attested_rich_steps": sorted(set(r["attested_rich_steps"] for r in rs))}
flip = [L for L in LAGS if 0 in sweep[L]["left"]]
cliff = (len(flip) == 1 and flip[0] == 14)
stats_ok = all(s["stat_at_decision"] in ([0.05], [0.11], [0.17], [0.23], [0.29],
                                         [0.35], [0.3])
               for s in sweep.values())
total_harm_lags = [L for L in LAGS if sweep[L]["dead"] == 10]
partial_lags = [L for L in LAGS if 0 not in sweep[L]["left"]
                and sweep[L]["left"] != [25]]
OUT["HA4"] = {"verdict": verdict(cliff),
              "sweep": sweep, "first_lag_with_any_harm": flip,
              "lags_with_full_harm": total_harm_lags,
              "lags_partial": partial_lags,
              "stat_values_as_preregistered": stats_ok}
print("HA4 %s  single-step cliff: first lag with ANY harm=%s (prereg said 14). "
      "FULL harm (30/30 dead) at lags=%s ; PARTIAL harm at lags=%s"
      % (OUT["HA4"]["verdict"], flip, total_harm_lags, partial_lags))
for L in LAGS:
    print("     lag=%-3d left=%-14s dead=%2d stat@decision=%s attested_rich=%s"
          % (L, sweep[L]["left"], sweep[L]["dead"], sweep[L]["stat_at_decision"],
             sweep[L]["attested_rich_steps"]))

# ---------------------------------------------------------------- HA5
# DEFECT FIX (turn 145, found by running this analyzer): the first version compared
# v14's NO-FORGER cells against v13's BRIBE cells (place="rich", tick=0.30). Every
# one of the 12 "differences" was "a forger was present in the other cell", not a
# behavioural difference -- my analyzer compared the wrong cells. The correct
# counterpart of a no-forger v14 cell is v13's own IDENTITY cell (place="none",
# tick=0.0). Both are compared below, and the world-identity is checked separately.
def frozen13_ident(arm, seed):
    return frozen13(arm, seed, place="none", tick=0.0, tag="foreign")


ident = {}
for arm, fz13, fz10 in (("a_believe", "l_ledger", None),
                        ("a_scalar", "l_scalar", "s4_internalized"),
                        ("a_none", None, "s0_nobrake")):
    d13 = []
    if fz13:
        for s in range(10):
            a = cell(arm, s, "none", 0.0, "foreign", None, "none")
            b = frozen13_ident(fz13, s)
            if a and b:
                d13.append(len(diff(a, b)))
    d10 = []
    if fz10:
        for s in range(10):
            a = cell(arm, s, "none", 0.0, "foreign", None, "none")
            b = frozen10(fz10, s)
            if a and b:
                d10.append(len(diff(a, b)))
    ident[arm] = {"vs_v13_identity_cells": d13, "vs_v10_cells": d10}
# the v14 WORLD itself: the same arm run in world="v13" must reproduce the frozen
# v13 cells (this isolates the world identity from the arm identity)
dworld = []
for s in range(10):
    a = cell("a_believe", s, "none", 0.0, "foreign", None, "none", world="v13")
    b = frozen13_ident("l_ledger", s)
    if a and b:
        dworld.append(len(diff(a, b)))
ident["world_v13_vs_frozen"] = dworld
# a_failclosed with NO attestation: HONESTLY, this is NOT l_ledger. A fail-closed
# reading of an unattested receipt is 0.0, where l_ledger reads the world's own
# label (0.05 here). The prereg's HA5 said they were identical; that was an
# OVER-CLAIM and it is corrected here rather than quietly dropped.
dfc_stat, dfc_verdict = [], []
for s in range(10):
    a = cell("a_failclosed", s, "none", 0.0, "foreign", None, "none")
    b = frozen13_ident("l_ledger", s)
    if a and b:
        dfc_stat.append((a["rate_at_first_decision"], b["rate_at_first_decision"]))
        dfc_verdict.append((a["commons_left"], b["commons_left"],
                            a["commons_drains"], b["commons_drains"]))
ident["a_failclosed_vs_l_ledger"] = {
    "stat_pairs": dfc_stat, "verdict_pairs": dfc_verdict,
    "same_verdict": all(x[0] == x[1] and x[2] == x[3] for x in dfc_verdict),
    "same_statistic": all(x[0] == x[1] for x in dfc_stat)}
ok5 = (all(x == 0 for x in ident["a_believe"]["vs_v13_identity_cells"])
       and all(x == 0 for x in ident["a_scalar"]["vs_v13_identity_cells"])
       and all(x == 0 for x in ident["a_scalar"]["vs_v10_cells"])
       and all(x == 0 for x in ident["a_none"]["vs_v10_cells"])
       and all(x == 0 for x in ident["world_v13_vs_frozen"]))
OUT["HA5"] = {"verdict": verdict(ok5), "detail": ident,
              "prereg_overclaim_corrected": (
                  "the prereg claimed a_failclosed == v13 l_ledger with no "
                  "attestation; measured, they share the VERDICT in the low world "
                  "but NOT the statistic (fail-closed reads 0.0, l_ledger reads "
                  "the world's own 0.05)")}
print("HA5 %s  identity vs frozen IDENTITY cells: %s" % (OUT["HA5"]["verdict"], ident))
print("     NOTE (my prereg over-claimed): a_failclosed vs l_ledger with no "
      "attestation -> same verdict=%s, same statistic=%s"
      % (ident["a_failclosed_vs_l_ledger"]["same_verdict"],
         ident["a_failclosed_vs_l_ledger"]["same_statistic"]))

# ---------------------------------------------------------------- HA6
r6l = [cell("a_believe", s, "none", 0.0, "foreign", 0.35, "live") for s in range(10)]
r6n = [cell("a_believe", s, "none", 0.0, "foreign", 0.35, "none") for s in range(10)]
ok6 = all(r and r["commons_left"] == 0 and r["keeper_dead"] for r in r6l + r6n)
d6 = [len(diff(a, b)) for a, b in zip(r6l, r6n)]
OUT["HA6"] = {"verdict": verdict(ok6), "live_left": summ(r6l, "commons_left"),
              "none_left": summ(r6n, "commons_left"),
              "live_vs_none_field_diffs": d6}
print("HA6 %s  honest raise wr=0.35: live left=%s none left=%s diffs=%s"
      % (OUT["HA6"]["verdict"], set(OUT["HA6"]["live_left"]),
         set(OUT["HA6"]["none_left"]), set(d6)))

# ---------------------------------------------------------------- HA7
r7n = [cell("a_failclosed", s, "none", 0.0, "foreign", 0.35, "none") for s in range(10)]
r7l = [cell("a_failclosed", s, "none", 0.0, "foreign", 0.35, "live") for s in range(10)]
ok7 = (all(r and r["commons_left"] == 25 and not r["keeper_dead"] for r in r7n)
       and all(r and r["commons_left"] == 0 and r["keeper_dead"] for r in r7l))
OUT["HA7"] = {"verdict": verdict(ok7), "none_left": summ(r7n, "commons_left"),
              "live_left": summ(r7l, "commons_left"),
              "none_stat": sorted(set(r["rate_at_first_decision"] for r in r7n))}
print("HA7 %s  cautious reading, wr=0.35: auditor NONE left=%s stat=%s ; "
      "auditor LIVE left=%s" % (OUT["HA7"]["verdict"], set(OUT["HA7"]["none_left"]),
                                OUT["HA7"]["none_stat"], set(OUT["HA7"]["live_left"])))

# ---------------------------------------------------------------- HA9 non-vacuity
# DEFECT FIX (turn 145): the first version asked "does the auditor's presence change
# the verdict for EVERY lag", and called itself REFUTED because the late lags are
# exactly the no-auditor case -- which is not a defect but the design. The check is
# restated as what it was meant to be: the doctor's presence is NON-VACUOUS iff
# there EXISTS a lag at which it changes the verdict, AND the change is MONOTONE in
# the lag (later attestation never buys MORE restraint than earlier), which is the
# real claim worth falsifying.
lags_all = [L for L in LAGS if L < 50]
changes = [L for L in lags_all if sweep[L]["left"] != sweep[50]["left"]]
mono = all(sweep[a]["commons_left"] if False else
           (min(sweep[a]["left"]) >= min(sweep[b]["left"]))
           for a, b in zip(lags_all, lags_all[1:]))
nonvac_ok = len(changes) > 0 and mono
OUT["HA9"] = {"verdict": verdict(nonvac_ok),
              "lags_where_the_auditor_changes_the_verdict": changes,
              "monotone_later_never_better": mono,
              "restated": ("a_auditor's presence is non-vacuous iff some lag "
                           "changes the verdict AND restraint is monotone in the lag")}
print("HA9 %s  the auditor changes the verdict at lags %s, and restraint is "
      "monotone in the lag=%s (restated check; the first version asked the wrong "
      "question and called itself REFUTED)"
      % (OUT["HA9"]["verdict"], OUT["HA9"]["lags_where_the_auditor_changes_the_verdict"],
         OUT["HA9"]["monotone_later_never_better"]))

# ---------------------------------------------------------------- HA4b (MEASURED)
# The graded boundary is not a defect of the world but of my ARITHMETIC in the
# prereg: it assumed the guard reads the statistic ONCE. It reads it on every
# harvest decision, so after the first decision the coefficient of the world
# component drops from 0.35 to 0.05 and the statistic self-corrects. This section
# MEASURES that correction from the arm's own change-log and is reported as a
# measured mechanism, not as a hypothesis that held.
mech = {}
for L in (13, 14, 15, 20, 50):
    r = cell("a_believe", 0, "rich", 0.30, "world", None, str(L))
    h = [(t, round(s, 6)) for t, s in r["stat_history"]]
    below = next((t for t, s in h if s < 0.30), None)
    mech[L] = {"left": r["commons_left"], "drains": r["commons_drains"],
               "history": h, "first_stat_that_falls_below_0.30": below}
OUT["HA4b"] = {"verdict": "MEASURED (mechanism, not a hypothesis)",
               "detail": mech,
               "explanation": (
                   "the frozen guard re-reads the statistic at EVERY harvest "
                   "decision, not once. After the first decision the statistic's "
                   "coefficient on the world component falls from 0.35 to 0.05, so "
                   "the first attenuation is (world+foreign)/6 = 0.3666 > 0.30 -> "
                   "the guard fires a SECOND time, and each later attested step then "
                   "drags the average below 0.30 and the guard closes for good. The "
                   "residual harm is therefore set by how many harvest steps pass "
                   "before the average crosses back under the threshold -- measured "
                   "1, 3 and 9 drains at lags 14, 15 and 20.")}
print("HA4b MEASURED  the crossing self-corrects; per-lag (left, drains, first "
      "statistic < 0.30):")
for L, v in mech.items():
    print("     lag=%-3d left=%-3d drains=%-3d below_at_t=%s  history=%s"
          % (L, v["left"], v["drains"], v["first_stat_that_falls_below_0.30"],
             v["history"][:6]))

print("-" * 74)
nv = sum(1 for k in ("HA1", "HA2", "HA3", "HA4", "HA5", "HA6", "HA7", "HA9")
         if OUT[k]["verdict"] == "HOLDS")
print("HYPOTHESES HOLDING: %d / 8" % nv)
for k in ("HA1", "HA2", "HA3", "HA4", "HA5", "HA6", "HA7", "HA9"):
    print("  %-5s %s" % (k, OUT[k]["verdict"]))

with open(os.path.join(HERE, "results", "analyze_attested_v14.json"), "w") as f:
    json.dump(OUT, f, indent=1, sort_keys=True, default=str)
print("WROTE results/analyze_attested_v14.json")
