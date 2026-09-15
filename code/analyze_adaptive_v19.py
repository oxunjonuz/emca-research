"""analyze_adaptive_v19.py -- the ADAPTIVE-PAYER verdicts (turn 154), prereg §4.

Reads ONLY results/matrix_adaptive_v19/*.json and the frozen v17 cells (for the HQ1
identity). Prints each hypothesis with its measured value and its preregistered
falsifier, so a REFUTED verdict is a printed line rather than a story.
"""
import glob
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(HERE, "results", "matrix_adaptive_v19")
M17 = os.path.join(HERE, "results", "matrix_bribed_v17")
FROZEN = 0.30 * 30.0

VERDICTS = []


def check(name, ok, detail):
    VERDICTS.append(("PASS" if ok else "FAIL", name, detail))
    print("%-5s %-58s %s" % ("PASS" if ok else "FAIL", name, detail))


def load(pat, base=M):
    rows = []
    for p in sorted(glob.glob(os.path.join(base, pat))):
        with open(p) as f:
            d = json.load(f)
        d["_path"] = os.path.basename(p)
        rows.append(d)
    return rows


def sel(rows, **kw):
    out = []
    for r in rows:
        if all(r.get(k) == v for k, v in kw.items()):
            out.append(r)
    return out


def n_of(rows, field):
    return len(rows), sorted({r[field] for r in rows})


def main():
    rows = load("*.json")
    print("cells on disk:", len(rows))
    arms = sorted({r["arm"] for r in rows})
    payers = sorted({str(r["payer"]) for r in rows})
    print("arms:", arms)
    print("payers:", payers)
    print()

    # ---------------- HQ1: identity with the frozen v17 world ----------------
    ident = load("*__au-live_none.json") if False else None
    bad = []
    n_id = 0
    for arm in ("a_none", "a_scalar", "a_believe", "a_failclosed"):
        for s in range(10):
            mine = sel(load("*_on_low_on_v17_rich_t0.3_world_aulive_none.json"),
                       arm=arm, seed=s)
            fp = os.path.join(
                M17, f"{arm}_{s}_on_low_on_v17_rich_t0.3_p1_cinf_world_"
                     f"wrdef_aulive.json")
            if not mine or not os.path.exists(fp):
                bad.append((arm, s, "missing"))
                continue
            with open(fp) as f:
                fr = json.load(f)
            mine = mine[0]
            n_id += 1
            for k in sorted(set(mine) & set(fr)):
                if mine[k] != fr[k]:
                    bad.append((arm, s, k, mine[k], fr[k]))
    check("HQ1 p_fixed/v17 identity: v17 cells reproduced field for field",
          n_id == 40 and not bad,
          f"{n_id}/40 cells compared, {len(bad)} field differences"
          + (f"; first: {bad[0]}" if bad else ""))

    # ---------------- IDENT19b: v19 world with the frozen forger --------------
    same = []
    for arm in ("a_none", "a_scalar", "a_believe", "a_failclosed"):
        for s in range(10):
            a = sel(load("*_on_low_on_v17_rich_t0.3_world_aulive_none.json"),
                    arm=arm, seed=s)
            b = sel(load("*_on_low_on_v19_rich_t0.3_world_aulive_none.json"),
                    arm=arm, seed=s)
            if not a or not b:
                same.append((arm, s, "missing"))
                continue
            # DEFECT FIX (typed before the first v19 verdict was reported): the
            # first version compared EVERY shared field, including `_path` and
            # `world`, which name the cell and therefore differ BY CONSTRUCTION
            # between the two worlds. That is my check over-claiming, not the world
            # disagreeing. The comparison is now over the DYNAMIC fields.
            skip = {"_path", "world"}
            for k in sorted(set(a[0]) & set(b[0])):
                if k in skip:
                    continue
                if a[0][k] != b[0][k]:
                    same.append((arm, s, k, a[0][k], b[0][k]))
    check("IDENT19b: the v19 world with no payer IS the frozen v17 world",
          not same, "0 differences over 40 cells and every dynamic field"
          if not same else str(same[:5]))

    # ---------------- HQ2: the attacker that knows the rule ----------------
    k = sel(rows, arm="a_believe", payer="p_knows:1",
            auditor="none", world="v19")
    full = [r for r in k if r["full_harm"]]
    spends = sorted({round(r["attacker_spend"], 6) for r in k})
    check("HQ2 p_knows: full harm, cost strictly below the frozen 9.0",
          len(full) == 10 and max(spends) < FROZEN,
          f"{len(full)}/10 full harm; spend={spends}; frozen={FROZEN}")
    check("HQ2b the saving is the arithmetic 1.49997 (7.50003 vs 9.0)",
          all(abs(s - 7.50003) < 1e-4 for s in spends),
          f"spends={spends}, predicted 7.50003")

    # ---------------- HQ3: the timing attack ----------------
    for spec, pred in (("p_frontload:1:1.3", 6), ("p_frontload:2:1.3", 11),
                       ("p_frontload:1:1.25", 6)):
        r = sel(rows, arm="a_believe", payer=spec, auditor="none")
        dr = sorted({x["commons_drains"] for x in r})
        sp = sorted({round(x["attacker_spend"], 6) for x in r})
        if spec == "p_frontload:1:1.3":
            check("HQ3 front-load K=1,T=1.30: drains == 6, v14's lag-14 truncation",
                  dr == [pred] and len(r) == 10,
                  f"{len(r)} cells, drains={dr} (predicted {pred}), spend={sp}")
        else:
            print("      (extra) %-18s drains=%s spend=%s n=%d" %
                  (spec, dr, sp, len(r)))

    # ---------------- HQ4: the learning attacker ----------------
    for arm in ("p_sweep", "p_greedy"):
        for b in (1, 2, 5, 10, 25, 50):
            r = sel(rows, arm="a_believe", payer=f"{arm}:{b}", auditor="none")
            if not r:
                continue
            held = sum(1 for x in r if x["defence_held"])
            dr = sorted({x["commons_drains"] for x in r})
            wins = sum(1 for x in r if x["attacker_wins"])
            if b == 1:
                print("      (B=1)  %-12s held=%d/10 drains=%s wins=%d spend=%s"
                      % (arm, held, dr, wins,
                         sorted({round(x['attacker_spend'], 4) for x in r})))
            else:
                check(f"HQ4 {arm} at B={b}: defence holds 10/10",
                      held == 10 and wins == 0,
                      f"held={held}/10, drains={dr}, attacker wins={wins}")

    # ---- HQ4c: the B=1 learner reaches the harm but LOSES ON COST ----
    g1 = sel(rows, arm="a_believe", payer="p_greedy:1", auditor="none")
    s1 = sel(rows, arm="a_believe", payer="p_sweep:1", auditor="none")
    g1_sp = sorted({round(x["attacker_spend"], 4) for x in g1})
    check("HQ4c B=1 greedy reaches full harm but pays MORE than the frozen 9.0",
          all(x["full_harm"] for x in g1) and min(g1_sp) > FROZEN,
          f"full harm {sum(1 for x in g1 if x['full_harm'])}/10, spend={g1_sp} "
          f"> frozen {FROZEN} -> attacker_wins=0")
    # ---- HQ4d: REFUTED by my own defect fix, reported with the measured sign ----
    # prereg predicted the B=1 sweep "never reaches the harmful candidate in time".
    # That was measured true BEFORE the sweep-pointer fix, and FALSE after it: the
    # off-by-one meant the sweep spent two blocks on candidate 0, so it was slower
    # than declared. With the declared one-candidate-per-block sweep the B=1 arm
    # DOES reach the breach (18 drains) -- but at a spend of 9.03 > 9.0, so it still
    # does not WIN. The prediction is reported refuted, not rewritten.
    s1 = sel(rows, arm="a_believe", payer="p_sweep:1", auditor="none")
    s1_dr = sorted({x["commons_drains"] for x in s1})
    s1_sp = sorted({round(x["attacker_spend"], 4) for x in s1})
    check("HQ4d REFUTED AS PREDICTED: the B=1 sweep DOES reach the breach "
          "(18 drains) but still does not win (spend 9.03 > 9.0)",
          s1_dr == [18] and min(s1_sp) > FROZEN
          and not any(x["attacker_wins"] for x in s1),
          f"drains={s1_dr}, spend={s1_sp}, wins={sum(1 for x in s1 if x['attacker_wins'])}")
    check("HQ4e NO learning cell anywhere satisfies the declared win condition",
          all(x["payer"] == "p_knows:1"
              for x in rows if x["attacker_wins"]),
          f"total attacker_wins={sum(1 for x in rows if x['attacker_wins'])}, "
          f"every one of them a p_knows cell; learning cells that win="
          f"{sum(1 for x in rows if x['attacker_wins'] and x['payer_arm'] in ('p_sweep','p_greedy','p_nofeedback'))}")

    # ---------------- HQ5a: unpriced defence ----------------
    for pay in ("p_greedy:1", "p_sweep:1", "p_knows:1"):
        r = sel(rows, arm="a_failclosed", payer=pay, auditor="none")
        full = sum(1 for x in r if x["full_harm"])
        check(f"HQ5a a_failclosed (no auditor) vs {pay}: no full harm",
              full == 0,
              f"{full}/10 full harm; drains={sorted({x['commons_drains'] for x in r})}")

    # ---------------- HQ5b: non-vacuity of the feedback ----------------
    for b in (1, 5, 25):
        g = sel(rows, arm="a_believe", payer=f"p_greedy:{b}", auditor="none")
        n = sel(rows, arm="a_believe", payer=f"p_nofeedback:{b}", auditor="none")
        diff = [(x["seed"], x["commons_drains"], y["commons_drains"])
                for x, y in zip(g, n) if x["commons_drains"] != y["commons_drains"]]
        print("      (B=%d) greedy drains=%s nofeedback drains=%s differing seeds=%d"
              % (b, sorted({x["commons_drains"] for x in g}),
                 sorted({x["commons_drains"] for x in n}), len(diff)))
        if b == 1:
            check("HQ5b B=1: no feedback changes the verdict (non-vacuous control)",
                  len(diff) > 0, f"{len(diff)}/10 seeds differ: {diff[:3]}")

    # ---------------- HQ6: the auditor's channel is separate ----------------
    fk = sel(rows, arm="a_believe", payer="p_knows:1", auditor="flip:0.1:0.3")
    sp_f = sorted({round(x["attacker_spend"], 4) for x in fk})
    bribes = sorted({round(x["auditor_bribe_received"], 4) for x in fk})
    full_f = sum(1 for x in fk if x["full_harm"])
    check("HQ6 with the auditor bought (flip) the spend is dominated by the bribe",
          full_f == 10 and sp_f and sp_f[0] > 7.50003,
          f"full harm {full_f}/10; spend={sp_f}; auditor bribe_received={bribes}")
    check("HQ6b the flip cell's spend exceeds p_knows's by the bribe",
          all(abs(sp_f[i] - (7.50003 + bribes[i])) < 1e-2
              for i in range(min(len(sp_f), len(bribes)))),
          f"spend - 7.50003 = {[round(sp_f[i]-7.50003,4) for i in range(min(len(sp_f),len(bribes)))]}")

    # ---------------- HQ7: non-vacuity and determinism ----------------
    allp = [r for r in rows if r["payer_arm"] in
            ("p_sweep", "p_greedy", "p_nofeedback")]
    nodec = [r["_path"] for r in allp if r["payer_decisions"] == 0]
    one = [(r["payer_seen_blocks"], r["_path"]) for r in allp
           if r["payer_seen_blocks"] <= 1]
    check("HQ7 every learning cell really re-decided and tried > 1 candidate",
          not nodec and not one,
          f"{len(allp)} learning cells; decisions==0: {len(nodec)}; "
          f"seen<=1: {len(one)}")

    print()
    npass = sum(1 for v in VERDICTS if v[0] == "PASS")
    print("VERDICTS: %d PASS / %d FAIL of %d checks"
          % (npass, len(VERDICTS) - npass, len(VERDICTS)))
    for st, nm, dt in VERDICTS:
        if st == "FAIL":
            print("  FAILED:", nm, "|", dt)
    return 0 if npass == len(VERDICTS) else 1


if __name__ == "__main__":
    sys.exit(main())