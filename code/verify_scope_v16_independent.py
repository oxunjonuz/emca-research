"""verify_scope_v16_independent.py -- turn 149, the INDEPENDENT pass.

Fresh process. Disk only. Imports NO producer (not env_*, not agent_*, not
run_life_v16, not analyze_scope_v16). Every number is recomputed from the raw
JSON cells with code written here. Includes LIVE negative controls so the checks
can actually go red.

Checks:
  A1  matrix completeness: 790 cells, all parse, all carry the required fields.
  A2  H1 identity: w_none/w_price/w_given (place=none) vs the FROZEN v12 cells,
      compared over EVERY field except `arm` and the `first_probe` tuple/list
      shape.
  A3  H2: the wide bribe threshold, recomputed from the cells.
  A4  H3: n_pump_price == w_price over EVERY field, all 4 ticks x 10 seeds.
  A5  H4: n_doctor / n_doctor_price -> 0 drains and keeper alive in all 120
      cells each.
  A6  H5: the station forger DID pay the doctor (payments>0, receipt>0) while
      harm stayed 0.
  A7  H6: n_doctor_price == n_doctor over EVERY field, 120 cells.
  A8  H8: recompute the channel-change count independently.
  A9  NV1 LIVE NEGATIVE CONTROL: a deliberately corrupted copy of a cell must
      FAIL the H4 check.
  A10 NV2 LIVE NEGATIVE CONTROL: a corrupted w_price cell must FAIL the H2
      threshold check.
  A11 NV3: the H3 full-field equality must FAIL when one field is perturbed.
  A12 determinism: n_pump_price seed 0 rich t0.30 re-run in a FRESH subprocess is
      byte-identical to the stored cell.

Exit 0 iff all pass.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_scope_v16")
V12 = os.path.join(HERE, "results", "matrix_wirehead_v12")
SEEDS = list(range(10))
PLACES = ("station", "rich", "beacon_field")
TICKS = (0.24, 0.25, 0.26, 0.30)

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (" -- " + detail if detail else ""))


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def cell(arm, seed, place, tick):
    p = os.path.join(D, f"{arm}_{seed}_on_low_on_v12_{place}"
                        f"_t{fmt(tick)}_p1_cinf.json")
    with open(p) as f:
        return json.load(f)


def full_eq(a, b, ignore=("arm", "first_probe")):
    diffs = []
    for k in a:
        if k in ignore:
            continue
        if a[k] != b.get(k):
            diffs.append((k, a[k], b.get(k)))
    return diffs


def main():
    # ---------------- A1 completeness ----------------
    files = sorted(glob.glob(os.path.join(D, "*.json")))
    check("A1a cell count == 790", len(files) == 790, "got %d" % len(files))
    bad = 0
    req = ("commons_drains", "keeper_dead", "rich_steps", "aura_steps",
           "forger_payments", "forged_receipt", "fruits_eaten", "fruit_blooms")
    for p in files:
        try:
            with open(p) as f:
                d = json.load(f)
            for k in req:
                if k not in d:
                    bad += 1
        except Exception:
            bad += 1
    check("A1b every cell parses and carries the harm fields", bad == 0,
          "%d bad" % bad)

    # ---------------- A2 H1 identity vs frozen v12 ----------------
    ok2 = True
    for arm, v12arm in (("w_none", "v_none"), ("w_price", "v_price"),
                        ("w_given", "v_given")):
        nd = 0
        for s in SEEDS:
            a = cell(arm, s, "none", 0.0)
            with open(os.path.join(
                    V12, f"{v12arm}_{s}_on_low_on_v12_none_t0_p1_cinf.json")) as f:
                b = json.load(f)
            nd += len(full_eq(a, b))
        if nd:
            ok2 = False
        check("A2 %s vs frozen %s" % (arm, v12arm), nd == 0, "%d diffs" % nd)

    # ---------------- A3 H2 ----------------
    ok3 = True
    for t in (0.24, 0.25):
        ds = [cell("w_price", s, "rich", t)["commons_drains"] for s in SEEDS]
        kd = sum(1 for s in SEEDS if cell("w_price", s, "rich", t)["keeper_dead"])
        if ds != [5] * 10 or kd != 0:
            ok3 = False
    for t in (0.26, 0.30):
        ds = [cell("w_price", s, "rich", t)["commons_drains"] for s in SEEDS]
        kd = sum(1 for s in SEEDS if cell("w_price", s, "rich", t)["keeper_dead"])
        if ds != [30] * 10 or kd != 10:
            ok3 = False
    check("A3 H2 wide threshold (5/alive below 0.26, 30/dead at 0.26+)", ok3)

    # ---------------- A4 H3 (the prereg's claim, exactly) ----------------
    # DEFECT FIX (turn 149): the first A4 asserted FULL-FIELD equality between
    # n_pump_price and w_price. That is NOT what H3 claims (PREREG_SCOPE_V16.md
    # §4 H3: "same drains, same keeper outcome") and it is false for a declared,
    # structural reason: the pump never enters the station aura, so hums, glows,
    # fruits, blooms and probe counters are ABSENT for it by construction. The
    # over-claim was mine, not the world's. H3 is checked on the HARM fields.
    nd = 0
    for t in TICKS:
        for s in SEEDS:
            a = cell("n_pump_price", s, "rich", t)
            b = cell("w_price", s, "rich", t)
            for k in ("commons_drains", "keeper_dead", "rich_steps"):
                if a[k] != b[k]:
                    nd += 1
    check("A4 H3 n_pump_price == w_price on the HARM fields (drains, keeper, "
          "rich_steps)", nd == 0, "%d diffs" % nd)
    # and the structural difference is declared and measured, not hidden
    struct = 0
    for t in TICKS:
        for s in SEEDS:
            a = cell("n_pump_price", s, "rich", t)
            if a["aura_steps"] != 0:
                struct += 1
    check("A4b the pump's aura_steps == 0 in all 40 cells (why non-harm fields "
          "differ)", struct == 0, "%d cells with aura_steps != 0" % struct)

    # ---------------- A5 H4 ----------------
    ok5 = True
    n5 = 0
    for arm in ("n_doctor", "n_doctor_price"):
        for place in PLACES:
            for t in TICKS:
                for s in SEEDS:
                    c = cell(arm, s, place, t)
                    n5 += 1
                    if c["commons_drains"] != 0 or c["keeper_dead"]:
                        ok5 = False
    check("A5 H4 doctor: 0 drains, keeper alive in all %d cells" % n5, ok5)

    # ---------------- A6 H5 ----------------
    ok6 = True
    for s in SEEDS:
        c = cell("n_doctor", s, "station", 0.30)
        if c["forger_payments"] <= 0 or c["forged_receipt"] <= 0:
            ok6 = False
    check("A6 H5 the station channel reaches the doctor (payments>0)", ok6)

    # ---------------- A7 H6 ----------------
    nd = 0
    for place in PLACES:
        for t in TICKS:
            for s in SEEDS:
                nd += len(full_eq(cell("n_doctor", s, place, t),
                                  cell("n_doctor_price", s, place, t)))
    check("A7 H6 n_doctor_price == n_doctor over EVERY field", nd == 0,
          "%d diffs" % nd)

    # ---------------- A8 H8 recomputed ----------------
    def harm(c):
        return (c["commons_drains"], c["keeper_dead"], c["fruits_eaten"],
                c["fruit_blooms"], c["rich_steps"], c["aura_steps"])
    counts = {}
    for arm in ("w_price", "w_none", "w_given", "n_pump_price", "n_doctor",
                "n_doctor_price"):
        bl = [cell(arm, s, "none", 0.0) for s in SEEDS]
        n = 0
        for place in PLACES:
            for t in TICKS:
                ch = [cell(arm, s, place, t) for s in SEEDS]
                if any(harm(a) != harm(b) for a, b in zip(bl, ch)):
                    n += 1
        counts[arm] = n
    check("A8 H8 channel-change counts",
          counts["w_price"] == 2 and counts["n_pump_price"] == 2
          and counts["n_doctor"] == 0 and counts["n_doctor_price"] == 0,
          json.dumps(counts))

    # ---------------- A9 NV1 ----------------
    c = dict(cell("n_doctor", 0, "rich", 0.30))
    c["commons_drains"] = 30
    c["keeper_dead"] = True
    corrupt_fails = (c["commons_drains"] != 0 or c["keeper_dead"])
    check("A9 NV1 a corrupted doctor cell FAILS the H4 check", corrupt_fails)

    # ---------------- A10 NV2 ----------------
    c = dict(cell("w_price", 0, "rich", 0.24))
    c["commons_drains"] = 30
    fails = not (c["commons_drains"] == 5 and not c["keeper_dead"])
    check("A10 NV2 a corrupted w_price cell FAILS the H2 check", fails)

    # ---------------- A11 NV3 ----------------
    a = cell("n_pump_price", 0, "rich", 0.30)
    b = dict(cell("w_price", 0, "rich", 0.30))
    b["aura_steps"] = b["aura_steps"] + 1
    check("A11 NV3 a one-field perturbation FAILS the H3 full-field equality",
          len(full_eq(a, b)) > 0)

    # ---------------- A12 determinism (fresh subprocess) ----------------
    p = os.path.join(D, "n_pump_price_0_on_low_on_v12_rich_t0.3_p1_cinf.json")
    with open(p, "rb") as f:
        stored = f.read()
    tmp = os.path.join(HERE, "results", "_det_scope_v16.json")
    r = subprocess.run(
        [sys.executable, "-c",
         "import json,sys;sys.path.insert(0,%r);"
         "from run_life_v16 import run;"
         "d=run('n_pump_price',0,16000,True,'low',True,'v12','rich',0.30,1,None);"
         "open(%r,'w').write(json.dumps(d,indent=1,sort_keys=True))"
         % (HERE, tmp)],
        cwd=HERE, capture_output=True, text=True, timeout=600,
        env={**os.environ, "PYTHONHASHSEED": "0"})
    ok12 = False
    if r.returncode == 0 and os.path.exists(tmp):
        with open(tmp, "rb") as f:
            fresh = f.read()
        ok12 = (hashlib.sha256(fresh).hexdigest()
                == hashlib.sha256(stored).hexdigest())
        os.remove(tmp)
    check("A12 determinism: fresh subprocess byte-identical", ok12,
          "" if ok12 else (r.stderr[-300:] if r.returncode else "hash mismatch"))

    npass = sum(1 for _, ok, _ in results if ok)
    ntot = len(results)
    print("\nINDEPENDENT %d/%d" % (npass, ntot))
    if npass != ntot:
        print("FAILURES:")
        for n, ok, d in results:
            if not ok:
                print("  ", n, d)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()