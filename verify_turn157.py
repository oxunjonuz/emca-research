#!/usr/bin/env python3
"""verify_turn157.py -- INDEPENDENT check of the v20 rung, run from the package.

Fresh process, disk only. Imports NO producer (not run_life_v20, not
driver_bribed_enforcer_v20, not analyze_bribed_enforcer_v20, not
verify_env_bribed_enforcer_v20, not env_bribed_enforcer_v20, not
agent_enforced_v18). Every number is recomputed from the raw JSON cells by DIFFERENT
code than the analyzer used, and a decisive cell is re-run in a fresh subprocess from
the package's own code and compared byte for byte.

Exit 0 only if every check passes.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

PKG = "/work/Shopify/audit-work/agent_arch/PUBLICATION_V1_V16"
D = os.path.join(PKG, "evidence", "results", "matrix_bribed_enforcer_v20")
DR = os.path.join(PKG, "evidence", "results", "matrix_v20_replication")
D18 = os.path.join(PKG, "evidence", "results", "matrix_enforced_v18")
CODE = os.path.join(PKG, "code")
SEEDS = list(range(10))
FRESH = list(range(10, 40))

FAILS = []
N = [0]


def check(name, cond, detail=""):
    N[0] += 1
    print(("PASS " if cond else "FAIL ") + name + (" -- " + detail if detail else ""))
    if not cond:
        FAILS.append(name)


def cell(d, arm, seed, spec):
    p = os.path.join(d, f"{arm}_{seed}_on_low_on_v20_rich_t0.3_p1_cinf_{spec}.json")
    with open(p) as f:
        return json.load(f)


def main():
    # 1. counts on disk
    n = len(glob.glob(os.path.join(D, "*.json")))
    rn = len(glob.glob(os.path.join(DR, "*.json")))
    check("v20 matrix has 270 cells on disk", n == 270, str(n))
    check("v20 replication has 120 cells on disk", rn == 120, str(rn))

    # 2. headline: open bought
    rows = [cell(D, "w_price", s, "station-open-0.1-0.3") for s in SEEDS]
    check("HV1 open bought: 30 drains, keeper dead 10/10, 0 refusals, claims station",
          all(r["commons_drains"] == 30 and r["keeper_dead"]
              and r["enforcer_refusals"] == 0
              and r["scope_task_distinct"] == ["station"] for r in rows))
    # 3. honest counterpart
    rows = [cell(D, "w_price", s, "station") for s in SEEDS]
    check("HV1c honest: 0 drains, alive 10/10, refusals > 0, claims station",
          all(r["commons_drains"] == 0 and not r["keeper_dead"]
              and r["enforcer_refusals"] > 0
              and r["scope_task_distinct"] == ["station"] for r in rows))
    # 4. dark announces
    rows = [cell(D, "w_price", s, "station-dark-0.1-0.3") for s in SEEDS]
    check("HV2 dark: 30 drains, dead, claims None",
          all(r["commons_drains"] == 30 and r["keeper_dead"]
              and r["enforcer_scope_claimed_end"] is None for r in rows))
    # 5. the refused flag DOES change (the refuted HV4)
    ro = [cell(D, "w_price", s, "station-open-0.1-0.3") for s in SEEDS]
    rh = [cell(D, "w_price", s, "station") for s in SEEDS]
    check("HV4b: `refused` never set when bought, set when honest",
          all(max(r["scope_refused_seen"]) == 0 for r in ro)
          and all(max(r["scope_refused_seen"]) > 0 for r in rh))
    # 6. the cliff
    def f(x):
        s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
        return s if s else "0"
    off = 0
    for price in (0.0, 0.1, 0.3, 0.6):
        for bribe in (0.0, 0.1, 0.3, 0.6):
            spec = f"station-open-{f(price)}-{f(bribe)}"
            for s in SEEDS:
                c = cell(D, "w_price", s, spec)
                if (bribe >= price) != (c["commons_drains"] == 30):
                    off += 1
    check("HV3 cliff: harm iff bribe >= price over the 4x4 grid", off == 0,
          "%d off" % off)
    # 7. grant bought
    rows = [cell(D, "w_widen", s, "station-open-0.1-0.3") for s in SEEDS]
    check("HV5: the widen grant is bought (widened 10/10, 30 drains)",
          all(r["enforcer_widened"] and r["commons_drains"] == 30 for r in rows))
    # 8. replication
    rows = [cell(DR, "w_price", s, "station-open-0.1-0.3") for s in FRESH]
    check("replication HV1: 30/30 fresh seeds drain and die",
          all(r["commons_drains"] == 30 and r["keeper_dead"] for r in rows))
    rows = [cell(DR, "w_price", s, "station") for s in FRESH]
    check("replication HV1c: 30/30 fresh seeds honest 0 drains",
          all(r["commons_drains"] == 0 and not r["keeper_dead"] for r in rows))

    # 9. identity: honest == frozen v18 over shared fields
    ADDED = ("arm", "world", "enforcer", "enforcer_bribe", "enforcer_price",
             "enforcer_mode", "enforcer_bribe_received", "enforcer_flipped",
             "enforcer_flip_step", "enforcer_scope_claimed_end",
             "scope_task_distinct", "scope_refused_any", "first_probe", "scope",
             "grant_widen", "enforcer_scope_end", "enforcer_scoped_steps",
             "enforcer_refusals", "enforcer_refused_actions",
             "enforcer_widen_requests", "enforcer_widen_refusals",
             "enforcer_widen_grants", "enforcer_widened", "enforcer_widen_t",
             "reward_before_widen", "reward_after_widen", "drains_before_widen",
             "drains_after_widen", "scope_task_seen", "scope_refused_seen")
    nd = 0
    cmp_ = 0
    for arm, sc in (("w_none", "none"), ("w_price", "none"), ("n_doctor", "none"),
                    ("n_pump_price", "none"), ("w_widen", "none"),
                    ("w_price", "station"), ("w_widen", "station"),
                    ("n_doctor", "station")):
        for s in SEEDS:
            oldp = os.path.join(D18, f"{arm}_{s}_on_low_on_v18_rich"
                                     f"_t0.3_p1_cinf_{sc}_gw0.json")
            if not os.path.exists(oldp):
                continue
            old = json.load(open(oldp))
            new = cell(D, arm, s, sc)
            cmp_ += 1
            for k in old:
                if k in ADDED:
                    continue
                if old[k] != new.get(k):
                    nd += 1
    check("HV6 identity: honest == frozen v18 over %d cells, 0 diffs" % cmp_,
          nd == 0 and cmp_ == 80, "%d diffs" % nd)

    # 10. determinism: re-run a decisive cell from the PACKAGE's own code
    p = os.path.join(D, "w_price_0_on_low_on_v20_rich_t0.3_p1_cinf_"
                        "station-open-0.1-0.3.json")
    stored = open(p, "rb").read()
    r = subprocess.run(
        [sys.executable, "run_life_v20.py", "w_price", "0", "16000", "on", "low",
         "on", "v20", "rich", "0.30", "1", "inf", "station", "0",
         "station:open:0.10:0.30"],
        cwd=CODE, capture_output=True, text=True, timeout=1800,
        env={**os.environ, "PYTHONHASHSEED": "0",
             "V20_OUTDIR": os.path.dirname(p)})
    fresh = open(p, "rb").read()
    check("determinism: a fresh subprocess from the PACKAGE's code reproduces the "
          "cell byte for byte",
          stored == fresh and r.returncode == 0,
          "rc=%d stored=%s fresh=%s" % (r.returncode,
                                        hashlib.sha256(stored).hexdigest()[:12],
                                        hashlib.sha256(fresh).hexdigest()[:12]))

    print("\n%d/%d checks passed" % (N[0] - len(FAILS), N[0]))
    if FAILS:
        print("FAILURES:")
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("ALL GREEN")


if __name__ == "__main__":
    main()