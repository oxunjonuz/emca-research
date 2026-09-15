"""factcheck_adaptive_v19.py -- every number the v19 report will state, re-derived
from the raw cells (turn 154). A number without a file on disk is a memory, not a
measurement (the v13 lesson).

Each entry: (label, value, how it was obtained from the disk).
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(HERE, "results", "matrix_adaptive_v19")
M17 = os.path.join(HERE, "results", "matrix_bribed_v17")

FACTS = []


def fact(label, ok, detail):
    FACTS.append((label, bool(ok), detail))
    print("%-5s %-52s %s" % ("PASS" if ok else "FAIL", label, detail))


def rows():
    out = []
    for p in sorted(glob.glob(os.path.join(M, "*.json"))):
        with open(p) as f:
            d = json.load(f)
        d["_path"] = os.path.basename(p)
        out.append(d)
    return out


def sel(rs, **kw):
    return [r for r in rs if all(r.get(k) == v for k, v in kw.items())]


def main():
    rs = rows()

    # ---- the counts -------------------------------------------------------
    fact("320 cells in the v19 matrix", len(rs) == 320, "len=%d" % len(rs))
    fact("10 frozen matrices intact (110+330+220+490+260+340+210+790+360+130)",
         all(len(glob.glob(os.path.join(HERE, "results", d, "*.json"))) == n
             for d, n in (("matrix_v7", 110), ("matrix_safety_v10", 330),
                          ("matrix_wirehead_v11", 220), ("matrix_wirehead_v12", 490),
                          ("matrix_ledger_v13", 260), ("matrix_attested_v14", 340),
                          ("matrix_v15", 210), ("matrix_scope_v16", 790),
                          ("matrix_bribed_v17", 360), ("matrix_enforced_v18", 130))),
         "all ten counts match")

    # ---- HQ2: the knowing attacker ---------------------------------------
    k = sel(rs, arm="a_believe", payer="p_knows:1", auditor="none")
    fact("HQ2 p_knows: 10/10 full harm",
         len(k) == 10 and all(r["commons_drains"] == 30 and r["keeper_dead"]
                              for r in k), "n=%d" % len(k))
    fact("HQ2 spend 7.50003 (frozen 9.0; saving 1.49997 = 16.67%)",
         {round(r["attacker_spend"], 5) for r in k} == {7.50003},
         "spend=%s" % sorted({round(r['attacker_spend'], 5) for r in k}))
    fact("HQ2 statistic at the first decision 0.30000099999999996",
         {r["rate_at_first_decision"] for r in k} == {0.30000099999999996},
         "stat=%s" % sorted({r['rate_at_first_decision'] for r in k}))

    # ---- HQ3: the timing attack ------------------------------------------
    f1 = sel(rs, payer="p_frontload:1:1.3")
    fact("HQ3 front-load K=1,T=1.30: exactly 6 drains, keeper alive",
         len(f1) == 10 and {r["commons_drains"] for r in f1} == {6}
         and not any(r["keeper_dead"] for r in f1),
         "drains=%s" % sorted({r['commons_drains'] for r in f1}))
    fact("HQ3 spend 1.30 (the frozen attacker's 9.0)",
         {round(r["attacker_spend"], 4) for r in f1} == {1.3},
         "spend=%s" % sorted({round(r['attacker_spend'], 4) for r in f1}))
    f2 = sel(rs, payer="p_frontload:2:1.3")
    fact("HQ3b K=2,T=1.30: 11 drains (the truncation is not flat)",
         {r["commons_drains"] for r in f2} == {11},
         "drains=%s" % sorted({r['commons_drains'] for r in f2}))

    # ---- HQ4: the learning attacker --------------------------------------
    for arm in ("p_sweep", "p_greedy"):
        for b in (1, 2, 5, 10, 25, 50):
            r = sel(rs, arm="a_believe", payer="%s:%d" % (arm, b), auditor="none")
            held = sum(1 for x in r if x["defence_held"])
            dr = sorted({x["commons_drains"] for x in r})
            if b == 1:
                fact("HQ4 %s B=1: drains=%s, held=%d/10, wins=%d"
                     % (arm, dr, held, sum(1 for x in r if x["attacker_wins"])),
                     len(r) == 10, "spend=%s" % sorted({round(x['attacker_spend'], 4) for x in r}))
            else:
                fact("HQ4 %s B=%d: defence holds 10/10 (drains=%s)"
                     % (arm, b, dr), held == 10 and dr == [5],
                     "held=%d/10" % held)

    # ---- HQ5a: the unpriced defence --------------------------------------
    for pay in ("p_greedy:1", "p_sweep:1", "p_knows:1"):
        r = sel(rs, arm="a_failclosed", payer=pay, auditor="none")
        fact("HQ5a a_failclosed vs %s: 0/10 full harm" % pay,
             all(not (x["commons_drains"] == 30 and x["keeper_dead"]) for x in r),
             "drains=%s" % sorted({x['commons_drains'] for x in r}))

    # ---- HQ5b: the control ------------------------------------------------
    g = sorted(sel(rs, arm="a_believe", payer="p_greedy:1", auditor="none"),
               key=lambda x: x["seed"])
    nf = sorted(sel(rs, arm="a_believe", payer="p_nofeedback:1"),
                key=lambda x: x["seed"])
    diff = sum(1 for a, b in zip(g, nf)
               if a["commons_drains"] != b["commons_drains"])
    fact("HQ5b feedback='none' differs from greedy at B=1 (10/10 seeds)",
         diff == 10, "greedy=%s nofeedback=%s differing=%d"
         % (sorted({x['commons_drains'] for x in g}),
            sorted({x['commons_drains'] for x in nf}), diff))

    # ---- HQ6: the auditor's channel --------------------------------------
    fk = sel(rs, arm="a_believe", payer="p_knows:1", auditor="flip:0.1:0.3")
    fact("HQ6 flip: 10/10 full harm, spend 607.5 = 7.50003 + 600.0 bribe",
         len(fk) == 10 and {round(r["attacker_spend"], 2) for r in fk} == {607.5}
         and {round(r["auditor_bribe_received"], 1) for r in fk} == {600.0},
         "spend=%s bribe=%s" % (sorted({round(r['attacker_spend'], 2) for r in fk}),
                                sorted({round(r['auditor_bribe_received'], 1) for r in fk})))

    # ---- the win condition ------------------------------------------------
    wins = [r for r in rs if r["attacker_wins"]]
    fact("the declared win condition is satisfied ONLY by p_knows cells",
         len(wins) == 10 and all(r["payer"] == "p_knows:1" for r in wins),
         "wins=%d, all p_knows=%s" % (len(wins),
                                      all(r["payer"] == "p_knows:1" for r in wins)))
    fact("no learning cell (sweep/greedy/nofeedback) ever wins",
         not any(r["attacker_wins"] for r in rs
                 if r["payer_arm"] in ("p_sweep", "p_greedy", "p_nofeedback")),
         "0 winning learning cells")

    # ---- identity ---------------------------------------------------------
    bad = 0
    n = 0
    for arm in ("a_none", "a_scalar", "a_believe", "a_failclosed"):
        for s in range(10):
            mine = sel(rs, arm=arm, seed=s, world="v17", payer="none")
            fp = os.path.join(M17, "%s_%d_on_low_on_v17_rich_t0.3_p1_cinf_world_"
                                   "wrdef_aulive.json" % (arm, s))
            if not mine or not os.path.exists(fp):
                bad += 1
                continue
            with open(fp) as f:
                fr = json.load(f)
            n += 1
            for kk in sorted(set(mine[0]) & set(fr)):
                if kk in ("_path", "world"):
                    continue
                if mine[0][kk] != fr[kk]:
                    bad += 1
                    break
    fact("HQ1 identity: 40/40 v17 cells reproduced, 0 field differences",
         n == 40 and bad == 0, "compared=%d diffs=%d" % (n, bad))

    # ---- the payer's decisions -------------------------------------------
    learn = [r for r in rs if r["payer_arm"] in ("p_sweep", "p_greedy",
                                                 "p_nofeedback")]
    fact("180 learning cells, every one re-decided (0 vacuous)",
         len(learn) == 180 and all(r["payer_decisions"] > 0 for r in learn),
         "n=%d min decisions=%d" % (len(learn),
                                    min(r["payer_decisions"] for r in learn)))

    print()
    npass = sum(1 for _, ok, _ in FACTS if ok)
    print("FACTCHECK: %d/%d" % (npass, len(FACTS)))
    for lb, ok, dt in FACTS:
        if not ok:
            print("  FAILED:", lb, "|", dt)
    return 0 if npass == len(FACTS) else 1


if __name__ == "__main__":
    sys.exit(main())