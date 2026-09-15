#!/usr/bin/env python3
"""verify_matrix_determinism_v2.py -- turn 132.

Re-run a sample of cells from results_union_v2/ in a FRESH process and compare
against the frozen per-seed rows, field by field. A different process, reading
only the frozen JSON for the expectation: if the recorded numbers were not
reproducible, this fails.

Also re-derives each cell's mean/sem from its OWN `rows` array (the matrix must
agree with the raw rows it shipped), and re-checks that every non-arbiter arm is
bit-identical to the turn-129 matrix -- the internal control that says the repair
touched ONLY the arms that consult the price.
"""
import sys, os, json, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))      # the campaign root, for the
sys.path.insert(0, os.path.join(HERE, "ext", "latt_py3"))   # frozen modules
OUT = os.path.join(HERE, "results_union_v2")
OLD = os.path.join(HERE, "results_union")

CASES = [("union", "maskr", "0.35"), ("union", "maskr", "0.25"),
         ("union", "mask", "0.35"), ("union", "mask", "0.15"),
         ("union_nocost", "maskr", "0.35"), ("union", "pub", "16"),
         ("union", "pub", "2"), ("union_noctx", "pub", "49"),
         ("beta0", "maskr", "0.35"), ("union_pooledexp", "mask", "0.35")]

fails = 0


def check(name, ok, detail=""):
    global fails
    print(("  PASS  " if ok else "  FAIL  ") + name + ("   " + detail if detail else ""))
    if not ok:
        fails += 1


def main():
    print("=== A. each cell agrees with the raw rows it shipped ===")
    for fn in sorted(os.listdir(OUT)):
        if not fn.endswith(".json") or fn == "SUMMARY.json":
            continue
        d = json.load(open(os.path.join(OUT, fn)))
        rows = d["rows"]
        regs = [r["regret"] for r in rows]
        m = float(np.mean(regs))
        se = float(np.std(regs, ddof=1) / np.sqrt(len(regs)))
        ok = (abs(m - d["mean_regret"]) < 1e-12 and abs(se - d["sem_regret"]) < 1e-12
              and len(rows) == d["nsim"])
        if not ok:
            check(fn, False, f"{m} vs {d['mean_regret']}")
    print(f"  checked {len([f for f in os.listdir(OUT) if f.endswith('.json') and f!='SUMMARY.json'])} cells, "
          f"{fails} failures")

    print("\n=== B. non-arbiter arms are BIT-IDENTICAL to the turn-129 matrix ===")
    same, diff = 0, []
    for fn in sorted(os.listdir(OUT)):
        if not fn.endswith(".json") or fn == "SUMMARY.json":
            continue
        d = json.load(open(os.path.join(OUT, fn)))
        if d["arm"] in ("union", "union_noctx", "union_pooledexp"):
            continue
        op = os.path.join(OLD, fn)
        if not os.path.exists(op):
            continue
        o = json.load(open(op))
        if ([r["regret"] for r in o["rows"]] == [r["regret"] for r in d["rows"]]):
            same += 1
        else:
            diff.append(fn)
    check("arms that never consult the price reproduce exactly", not diff,
          f"{same} identical" + (f", differing: {diff[:4]}" if diff else ""))

    print("\n=== C. fresh-process reproduction of sampled cells ===")
    py = ("import sys,os,json;sys.path[:0]=['.','ext/latt_py3','..'];\n"
          "from union_run_v2 import run_cell\n"
          "import numpy as np\n"
          "arm,inst,param,n = {ARGS!r}\n"
          "rows=[run_cell(arm,inst,param,s,400) for s in range(1,n+1)]\n"
          "print('{FMT}'%np.mean([x['regret'] for x in rows]))\n"
          "print('{FMT}'%np.mean([x['n_probes'] for x in rows]))\n")
    for arm, inst, param in CASES:
        fn = "%s_p%s_%s.json" % (inst, param.replace(".", "p"), arm)
        d = json.load(open(os.path.join(OUT, fn)))
        src = py.format(ARGS=(arm, inst, param, d["nsim"]), FMT="%.12f")
        p = subprocess.run(["python3", "-c", src], capture_output=True, text=True,
                           cwd=HERE)
        got = p.stdout.split()
        exp = ["%.12f" % d["mean_regret"], "%.12f" % d["mean_probes"]]
        ok = len(got) >= 2 and got[0] == exp[0] and got[1] == exp[1]
        check(f"{arm} {inst} p={param}", ok,
              f"frozen {exp} fresh {got[:2]}" if not ok else "")

    print("\n=== D. the corrected arbiter's own arithmetic ===")
    import arbitration_scaled as AS
    import arbitration as AR
    import candidate_gen as CG
    check("PROBE_LEN == union_agent_v2.PROBE_BLOCK",
          AS.PROBE_LEN == __import__("union_agent_v2").PROBE_BLOCK)
    check("cutoff_old = 196/240", abs(AS.cutoff_old() - 196.0 / 240.0) < 1e-12,
          "%.6f" % AS.cutoff_old())
    check("cutoff_new = 196/220", abs(AS.cutoff_new() - 196.0 / 220.0) < 1e-12,
          "%.6f" % AS.cutoff_new())
    check("cutoff_new > cutoff_old", AS.cutoff_new() > AS.cutoff_old())
    c_lo = CG.Candidate("a", "y", "c", None, None, 100, 0.5)
    check("beta=0 clears nothing under the new rule",
          AS.plan([c_lo], 0.5, beta=0.0).probe_order == [])
    # The band the repair is ABOUT: a candidate carrying the FULL attainable
    # headroom (score = 1 - rich). Below cutoff_old both rules clear; inside the
    # band (0.8167, 0.8909] only the corrected rule does; above cutoff_new
    # neither does -- and that last part is economics, not an artefact.
    for rich in (0.80, 0.85, 0.88, 0.92):
        c = CG.Candidate("a", "y", "c", None, None, 100, 1.0 - rich)
        old_ok = bool(AR.plan([c], rich).probe_order)
        new_ok = bool(AS.plan([c], rich).probe_order)
        print(f"    rich={rich:.2f}  max-gap candidate: old={old_ok} new={new_ok}")
        if rich < AS.cutoff_old():
            check(f"rich={rich}: both rules clear a full-headroom candidate",
                  old_ok and new_ok)
        elif rich <= AS.cutoff_new():
            check(f"rich={rich}: only the corrected rule clears (the repair's band)",
                  new_ok and not old_ok)
        else:
            check(f"rich={rich}: neither clears -- economics, not a horizon artefact",
                  not old_ok and not new_ok)
    check("frozen arbitration.py untouched",
          __import__("hashlib").sha256(
              open(os.path.join(os.path.dirname(HERE), "arbitration.py"), "rb").read()
          ).hexdigest() == "2d3d825bcfc83cc8533866510960572c42140db2f2f03c6a9945807b71e0914c")
    check("frozen candidate_gen.py untouched",
          __import__("hashlib").sha256(
              open(os.path.join(os.path.dirname(HERE), "candidate_gen.py"), "rb").read()
          ).hexdigest() == "fa9721ae816c3c42ecf73ca28ba3f188b78f51b345a381e092515f262c46ef49")
    check("union_agent_v2 differs from union_agent in EXACTLY one line",
          _one_line_diff(os.path.join(HERE, "union_agent.py"),
                         os.path.join(HERE, "union_agent_v2.py")))

    print("\n%s (%d failures)" % ("ALL CHECKS PASS" if fails == 0 else "FAILURES PRESENT", fails))
    json.dump({"fails": fails}, open(os.path.join(HERE, "verify_matrix_determinism_v2.json"), "w"), indent=1)


def _one_line_diff(a, b):
    import difflib
    al = open(a).read().splitlines()
    bl = open(b).read().splitlines()
    d = [l for l in difflib.unified_diff(al, bl, n=0) if l.startswith(("+", "-"))
         and not l.startswith(("+++", "---"))]
    return len(d) == 2 and d[0].startswith("-import arbitration as AR") \
        and d[1].startswith("+import arbitration_scaled as AR")


if __name__ == "__main__":
    main()
