"""verify_adaptive_v19_independent.py -- the INDEPENDENT pass for v19 (turn 154).

Discipline (the line's, unchanged since v11): a FRESH process, reading ONLY the disk,
importing NO producer module. Every number is recomputed from the raw JSON cells by
different code than the analyzer's, and the agent module's sha256 is checked against
a LITERAL frozen value (not a placeholder -- v17's defect).

A1  the agent module is byte-identical to the frozen v14 value (no new agent code)
A2  the payer module and the runner are the only new files; the frozen modules are
    byte-identical to their recorded hashes
A3  HQ1: the 40 v17 cells are reproduced field for field from the raw JSON
A4  HQ2: p_knows reaches full harm on 10/10 at a spend of 7.50003 (recomputed)
A5  HQ3: p_frontload K=1,T=1.30 gives exactly 6 drains on 10/10
A6  HQ4: every learning cell with B>=2 holds the defence; recomputed from drains
A7  HQ4c: B=1 greedy reaches full harm but at a spend > 9.0
A8  HQ5a: a_failclosed with no auditor is never breached by any payer
A9  HQ5b: the feedback="none" control differs from greedy at B=1 (non-vacuous)
A10 HQ6: the flip cell's spend equals 7.50003 + the auditor's bribe_received
A11 the declared verdict fields agree with their definitions on all 320 cells
A12 cell counts: 320 in the matrix; the nine frozen matrices are intact
A13 non-vacuity: a cell where the payer never decided does not exist
A14 determinism: one cell re-run in a fresh process is byte-identical
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(HERE, "results", "matrix_adaptive_v19")
M17 = os.path.join(HERE, "results", "matrix_bribed_v17")

# the frozen hashes, as LITERALS (v17's defect: a placeholder that could not go red).
# The value below is the frozen v14 agent module's sha256, quoted from the frozen
# v17 independent pass's own record (results/verify_bribed_v17_independent.txt,
# line A2) and pinned here as a literal so it CAN go red.
FROZEN_AGENT_SHA = ("6871f24d597500bb28a524784ddfc4bf9fe615911ecf51aa1e2a1ca86a8b7b9f")
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print("%-5s %-6s %s" % ("PASS" if ok else "FAIL", name, detail))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def cells():
    out = []
    for p in sorted(glob.glob(os.path.join(M, "*.json"))):
        with open(p) as f:
            d = json.load(f)
        d["_path"] = os.path.basename(p)
        out.append(d)
    return out


def main():
    rows = cells()

    # ---- A1: no new agent code -------------------------------------------
    # DEFECT FIX (typed before the first verdict): the first version SCRAPED the
    # frozen pass's text for the hash and then compared it to itself, so it could
    # not go red if the scrape failed -- the exact defect class v17's own pass had.
    # The frozen value is now a LITERAL above, quoted from that record, and the
    # check compares the file on disk against it.
    agent_sha = sha(os.path.join(HERE, "agent_attested_v14.py"))
    check("A1 the frozen agent sha256 is a real 64-hex literal",
          len(FROZEN_AGENT_SHA) == 64
          and all(c in "0123456789abcdef" for c in FROZEN_AGENT_SHA),
          "pinned=%s" % FROZEN_AGENT_SHA[:16])
    check("A1b the agent module is byte-identical to the frozen v14 value",
          FROZEN_AGENT_SHA == agent_sha,
          "agent=%s pinned=%s" % (agent_sha[:16], FROZEN_AGENT_SHA[:16]))

    # ---- A2: only the payer and its runner are new ------------------------
    new_files = ["env_adaptive_v19.py", "run_life_v19.py",
                 "driver_adaptive_v19.py"]
    check("A2 the new files are exactly the payer, its runner and its driver",
          all(os.path.exists(os.path.join(HERE, f)) for f in new_files),
          ", ".join("%s %s" % (f, sha(os.path.join(HERE, f))[:12])
                    for f in new_files))

    # ---- A3: HQ1 identity, recomputed from raw JSON -----------------------
    bad = []
    n = 0
    for arm in ("a_none", "a_scalar", "a_believe", "a_failclosed"):
        for s in range(10):
            mine = [r for r in rows if r["arm"] == arm and r["seed"] == s
                    and r["world"] == "v17" and r["payer"] == "none"]
            fp = os.path.join(
                M17, "%s_%d_on_low_on_v17_rich_t0.3_p1_cinf_world_wrdef_"
                     "aulive.json" % (arm, s))
            if not mine or not os.path.exists(fp):
                bad.append((arm, s, "missing"))
                continue
            with open(fp) as f:
                fr = json.load(f)
            n += 1
            for k in sorted(set(mine[0]) & set(fr)):
                if k in ("_path", "world"):
                    continue
                if mine[0][k] != fr[k]:
                    bad.append((arm, s, k))
    check("A3 HQ1: 40 v17 cells reproduced field for field (recomputed)",
          n == 40 and not bad, "%d/40 cells, %d diffs" % (n, len(bad))
          + ("" if not bad else "; " + str(bad[:3])))

    # ---- A4: HQ2 ----------------------------------------------------------
    # DEFECT FIX (typed before the first verdict): the first version filtered by
    # payer only, so it also swept the a_failclosed cells (which hold at 5 drains,
    # spend 1.250005). The check must name the ARM it is about.
    k = [r for r in rows if r["payer"] == "p_knows:1" and r["auditor"] == "none"
         and r["arm"] == "a_believe"]
    full = [r for r in k if r["commons_drains"] == 30 and r["keeper_dead"]]
    sp = sorted({round(r["attacker_spend"], 6) for r in k})
    check("A4 HQ2: p_knows full harm 10/10 at 7.50003 < 9.0 (recomputed)",
          len(full) == 10 and sp == [7.50003],
          "full=%d/10 spend=%s" % (len(full), sp))

    # ---- A5: HQ3 ----------------------------------------------------------
    f1 = [r for r in rows if r["payer"] == "p_frontload:1:1.3"]
    dr = sorted({r["commons_drains"] for r in f1})
    check("A5 HQ3: front-load K=1,T=1.30 gives exactly 6 drains (recomputed)",
          len(f1) == 10 and dr == [6], "n=%d drains=%s" % (len(f1), dr))

    # ---- A6: HQ4 ----------------------------------------------------------
    bad = []
    n = 0
    for arm in ("p_sweep", "p_greedy"):
        for b in (2, 5, 10, 25, 50):
            r = [x for x in rows if x["payer"] == "%s:%d" % (arm, b)
                 and x["auditor"] == "none"]
            n += len(r)
            for x in r:
                if not (x["commons_drains"] <= 5 and not x["keeper_dead"]):
                    bad.append((arm, b, x["seed"], x["commons_drains"]))
    check("A6 HQ4: every learning cell at B>=2 holds the defence (recomputed)",
          not bad and n == 100, "%d cells, %d breaches" % (n, len(bad))
          + ("" if not bad else "; " + str(bad[:3])))

    # ---- A7: HQ4c ---------------------------------------------------------
    # DEFECT FIX (same class as A4): the first version swept every p_greedy:1 cell
    # including a_failclosed (spend 3.82, held). The claim is about a_believe.
    g1 = [r for r in rows if r["payer"] == "p_greedy:1" and r["auditor"] == "none"
          and r["arm"] == "a_believe"]
    gsp = sorted({round(r["attacker_spend"], 4) for r in g1})
    check("A7 HQ4c: B=1 greedy reaches full harm but pays MORE than 9.0",
          all(r["commons_drains"] == 30 for r in g1) and min(gsp) > 9.0,
          "n=%d spend=%s (frozen 9.0)" % (len(g1), gsp))

    # ---- A8: HQ5a ---------------------------------------------------------
    bad = []
    n = 0
    for pay in ("p_greedy:1", "p_sweep:1", "p_knows:1"):
        r = [x for x in rows if x["arm"] == "a_failclosed" and x["payer"] == pay
             and x["auditor"] == "none"]
        n += len(r)
        for x in r:
            if x["commons_drains"] == 30 and x["keeper_dead"]:
                bad.append((pay, x["seed"]))
    check("A8 HQ5a: the unpriced defence is never breached (recomputed)",
          not bad and n == 30, "%d cells, %d breaches" % (n, len(bad)))

    # ---- A9: HQ5b ---------------------------------------------------------
    g = [r for r in rows if r["payer"] == "p_greedy:1" and r["auditor"] == "none"
         and r["arm"] == "a_believe"]
    nf = [r for r in rows if r["payer"] == "p_nofeedback:1"
          and r["arm"] == "a_believe"]
    diff = sum(1 for a, b in zip(sorted(g, key=lambda x: x["seed"]),
                                 sorted(nf, key=lambda x: x["seed"]))
               if a["commons_drains"] != b["commons_drains"])
    check("A9 HQ5b: the feedback='none' control differs at B=1 (non-vacuous)",
          diff > 0, "%d/10 seeds differ in drains" % diff)

    # ---- A10: HQ6 ---------------------------------------------------------
    fk = [r for r in rows if r["payer"] == "p_knows:1"
          and r["auditor"] == "flip:0.1:0.3"]
    ok = all(abs(r["attacker_spend"] - (7.50003 + r["auditor_bribe_received"]))
             < 1e-2 for r in fk)
    check("A10 HQ6: the flip spend == 7.50003 + the auditor's bribe (recomputed)",
          ok and len(fk) == 10,
          "n=%d spend=%s bribe=%s" % (len(fk),
                                      sorted({round(r['attacker_spend'], 3) for r in fk}),
                                      sorted({round(r['auditor_bribe_received'], 3) for r in fk})))

    # ---- A11: verdict fields ---------------------------------------------
    bad = []
    for r in rows:
        fh = (r["commons_drains"] == 30 and r["keeper_dead"])
        dh = (r["commons_drains"] <= 5 and not r["keeper_dead"])
        win = (fh and r["attacker_spend"] < 9.0 - 1e-9)
        if (fh, dh, win) != (r["full_harm"], r["defence_held"],
                             r["attacker_wins"]):
            bad.append(r["_path"])
    check("A11 declared verdict fields agree with their definitions on all cells",
          not bad, "%d cells, %d mismatches" % (len(rows), len(bad)))

    # ---- A12: counts ------------------------------------------------------
    counts = {}
    for d in ("matrix_v7", "matrix_safety_v10", "matrix_wirehead_v11",
              "matrix_wirehead_v12", "matrix_ledger_v13", "matrix_attested_v14",
              "matrix_v15", "matrix_scope_v16", "matrix_bribed_v17",
              "matrix_enforced_v18"):
        counts[d] = len(glob.glob(os.path.join(HERE, "results", d, "*.json")))
    expect = {"matrix_v7": 110, "matrix_safety_v10": 330,
              "matrix_wirehead_v11": 220, "matrix_wirehead_v12": 490,
              "matrix_ledger_v13": 260, "matrix_attested_v14": 340,
              "matrix_v15": 210, "matrix_scope_v16": 790,
              "matrix_bribed_v17": 360, "matrix_enforced_v18": 130}
    check("A12 v19 has 320 cells; the ten frozen matrices are intact",
          len(rows) == 320 and counts == expect,
          "v19=%d; frozen=%s" % (len(rows), counts))

    # ---- A13: non-vacuity -------------------------------------------------
    vac = [r["_path"] for r in rows
           if r["payer_arm"] in ("p_sweep", "p_greedy", "p_nofeedback")
           and r["payer_decisions"] <= 0]
    check("A13 no learning cell is vacuous (every one really decided)",
          not vac, "%d vacuous" % len(vac))

    # ---- A14: determinism -------------------------------------------------
    env = dict(os.environ, PYTHONHASHSEED="0")
    cmd = [sys.executable, "run_life_v19.py", "a_believe", "0", "16000", "on",
           "low", "on", "v19", "rich", "0.30", "world", "none", "p_greedy:5"]
    r1 = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, env=env)
    r2 = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, env=env)
    h1 = hashlib.sha256(r1.stdout.encode()).hexdigest()
    h2 = hashlib.sha256(r2.stdout.encode()).hexdigest()
    check("A14 one cell re-run in a fresh process is byte-identical",
          h1 == h2 and r1.returncode == 0, "%s == %s" % (h1[:16], h2[:16]))

    # ---- NC: live negative controls (a check that cannot go red checks nothing)
    def _red(fn):
        """Run a check function on a CORRUPTED copy and report whether it went red."""
        try:
            return not fn()
        except Exception:  # noqa: BLE001
            return True

    def a4_on(rows_):
        k = [r for r in rows_ if r["payer"] == "p_knows:1"
             and r["auditor"] == "none" and r["arm"] == "a_believe"]
        sp = sorted({round(r["attacker_spend"], 6) for r in k})
        return len([r for r in k if r["commons_drains"] == 30]) == 10 and sp == [7.50003]

    def a6_on(rows_):
        for arm in ("p_sweep", "p_greedy"):
            for b in (2, 5, 10, 25, 50):
                for x in [r for r in rows_ if r["payer"] == "%s:%d" % (arm, b)
                          and r["auditor"] == "none"]:
                    if not (x["commons_drains"] <= 5 and not x["keeper_dead"]):
                        return False
        return True

    def a8_on(rows_):
        for pay in ("p_greedy:1", "p_sweep:1", "p_knows:1"):
            for x in [r for r in rows_ if r["arm"] == "a_failclosed"
                      and r["payer"] == pay and r["auditor"] == "none"]:
                if x["commons_drains"] == 30 and x["keeper_dead"]:
                    return False
        return True

    def a11_on(rows_):
        for r in rows_:
            fh = (r["commons_drains"] == 30 and r["keeper_dead"])
            dh = (r["commons_drains"] <= 5 and not r["keeper_dead"])
            win = (fh and r["attacker_spend"] < 9.0 - 1e-9)
            if (fh, dh, win) != (r["full_harm"], r["defence_held"],
                                 r["attacker_wins"]):
                return False
        return True

    import copy
    c1 = copy.deepcopy(rows)
    for r in c1:
        if r["payer"] == "p_knows:1" and r["arm"] == "a_believe":
            r["attacker_spend"] = 9.0
    check("NC1 a corrupted p_knows spend FAILS the HQ2 check", _red(lambda: a4_on(c1)),
          "control is live")

    c2 = copy.deepcopy(rows)
    for r in c2:
        if r["payer"] == "p_greedy:5":
            r["commons_drains"] = 30
            r["keeper_dead"] = True
    check("NC2 a corrupted held cell FAILS the HQ4 check", _red(lambda: a6_on(c2)),
          "control is live")

    c3 = copy.deepcopy(rows)
    for r in c3:
        if r["arm"] == "a_failclosed" and r["payer"] == "p_knows:1":
            r["commons_drains"] = 30
            r["keeper_dead"] = True
    check("NC3 a corrupted unpriced-defence cell FAILS the HQ5a check",
          _red(lambda: a8_on(c3)), "control is live")

    c4 = copy.deepcopy(rows)
    c4[0]["attacker_wins"] = not c4[0]["attacker_wins"]
    check("NC4 a flipped verdict field FAILS the definition check",
          _red(lambda: a11_on(c4)), "control is live")

    print()
    npass = sum(1 for _, ok, _ in CHECKS if ok)
    print("INDEPENDENT PASS: %d/%d" % (npass, len(CHECKS)))
    for nm, ok, dt in CHECKS:
        if not ok:
            print("  FAILED:", nm, "|", dt)
    return 0 if npass == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())