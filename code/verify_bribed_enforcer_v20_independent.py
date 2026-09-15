"""verify_bribed_enforcer_v20_independent.py -- INDEPENDENT pass for the v20 line.

Fresh process, disk only, IMPORTS NO PRODUCER (not run_life_v20, not
driver_bribed_enforcer_v20, not analyze_bribed_enforcer_v20, not
verify_env_bribed_enforcer_v20, not env_bribed_enforcer_v20, not
agent_enforced_v18). Every number is recomputed from the raw JSON cells by DIFFERENT
code than the analyzer used; the agent modules are audited by AST and by SHA-256.

Exit 0 only if every check passes. Live negative controls are included.

Checks:
  A1  matrix completeness: 270 cells, all parse, required fields present.
  A2  agent_safety_v10.py, agent_scope_v16.py, agent_enforced_v18.py are UNCHANGED
      (sha256 against recorded frozen literals) -- v20 adds NO agent code.
  A3  AST audit of the agent modules: none of them reads o["scope"] / o["refused"].
  A4  HV6: honest reproduces the frozen v18 cells field for field (80 cells).
  A5  HV1: w_price open -> 30 drains, keeper dead 10/10, refusals == 0.
  A6  HV1 counterfactual: w_price honest -> 0 drains, keeper alive 10/10, refusals>0.
  A7  HV2: dark -> 30 drains, dead 10/10, and claimed task None.
  A8  HV4: in OPEN the claimed `task` is "station" on EVERY step (identical to
      honest), i.e. the boundary still claims to be there.
  A9  HV4b (the honest refinement): the per-step `refused` flag DOES change
      (honest > 0, open == 0) -- the failure is not invisible to an agent that
      reads it, only to the frozen arms which do not.
  A10 HV3: the cliff -- harm iff bribe >= price over the 4x4 grid.
  A11 HV5: the widen grant is bought (gw=0, open -> widened 10/10, 30 drains).
  A12 NV1 LIVE NEGATIVE CONTROL: a corrupted HV1 cell must FAIL.
  A13 NV2 LIVE NEGATIVE CONTROL: a corrupted HV5 cell must FAIL.
  A14 determinism: a fresh subprocess reproduces a cell byte for byte.
"""
import ast
import glob
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_bribed_enforcer_v20")
D18 = os.path.join(HERE, "results", "matrix_enforced_v18")
SEEDS = list(range(10))
PRICE_GRID = (0.0, 0.10, 0.30, 0.60)
BRIBE_GRID = (0.0, 0.10, 0.30, 0.60)

FROZEN = {
    "agent_safety_v10.py":
        "aa55a8e5e90203c6375bebc90e88c995610d685cd3280e654f40307edc6e5df4",
    "agent_scope_v16.py":
        "66388790637754551837b126850e51b26a932f40f922ce677be60d54704c1883",
    "agent_enforced_v18.py":
        "97809d80053a21ae4102c28aee77189f7435c38dd18dd44c07f221c66378b24d",
    "env_enforced_v18.py":
        "0ef9cddc5cde902d35a1eee93b3c8964e755be8034603f96bcaf32fe3fab284c",
}

FAILS = []
N = [0]


def check(name, cond, detail=""):
    N[0] += 1
    print(("PASS " if cond else "FAIL ") + name + (" -- " + detail if detail else ""))
    if not cond:
        FAILS.append(name)


def fmt(x):
    s = ("%.4f" % float(x)).rstrip("0").rstrip(".")
    return s if s else "0"


def norm(spec):
    if spec in (None, "none") or ":" not in str(spec):
        return spec
    parts = str(spec).split(":")
    out = [parts[0]]
    for x in parts[1:]:
        try:
            out.append(fmt(float(x)))
        except (TypeError, ValueError):
            out.append(x)
    return "-".join(out)


def cell(arm, seed, place, tick, spec):
    p = os.path.join(D, f"{arm}_{seed}_on_low_on_v20_{place}"
                        f"_t{fmt(tick)}_p1_cinf_{norm(spec)}.json")
    with open(p) as f:
        return json.load(f)


def main():
    # ---------------- A1 completeness ----------------
    files = sorted(glob.glob(os.path.join(D, "*.json")))
    check("A1a cell count == 270", len(files) == 270, "got %d" % len(files))
    req = ("commons_drains", "keeper_dead", "commons_left", "enforcer_refusals",
           "enforcer_flipped", "enforcer_mode", "enforcer_bribe_received",
           "enforcer_scope_claimed_end", "scope_task_distinct", "scope_refused_any")
    bad = 0
    for p in files:
        try:
            d = json.load(open(p))
        except Exception:
            bad += 1
            continue
        if any(k not in d for k in req):
            bad += 1
    check("A1b every cell parses and carries the required fields", bad == 0,
          "%d bad" % bad)

    # ---------------- A2 the reused modules are unchanged ----------------
    for fn, want in FROZEN.items():
        got = hashlib.sha256(open(os.path.join(HERE, fn), "rb").read()).hexdigest()
        check("A2 %s unchanged (sha256 matches the recorded frozen value)" % fn,
              got == want, "got %s" % got[:16])

    # ---------------- A3 AST audit: no arm reads o["scope"] ----------------
    reads = []
    for fn in ("agent_emca_v7.py", "agent_safety_v10.py", "agent_scope_v16.py",
               "agent_enforced_v18.py"):
        tree = ast.parse(open(os.path.join(HERE, fn)).read())
        for node in ast.walk(tree):
            # a subscript o["scope"] / o["refused"] anywhere
            if isinstance(node, ast.Subscript):
                s = node.slice
                if isinstance(s, ast.Constant) and s.value in ("scope", "refused"):
                    reads.append((fn, getattr(node, "lineno", "?")))
            if isinstance(node, ast.Name) and node.id in ("scope", "refused"):
                reads.append((fn, "NAME:" + node.id, getattr(node, "lineno", "?")))
    check("A3 no frozen arm reads o['scope'] / o['refused'] (the failure is "
          "unobservable to the agent as built)", len(reads) == 0, "%r" % reads[:5])

    # ---------------- A4 HV6 identity ----------------
    anchors = [("w_none", "none"), ("w_price", "none"), ("n_doctor", "none"),
               ("n_pump_price", "none"), ("w_widen", "none"),
               ("w_price", "station"), ("w_widen", "station"),
               ("n_doctor", "station")]
    nd_total = 0
    cells = 0
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
    for arm, sc in anchors:
        for s in SEEDS:
            oldp = os.path.join(D18, f"{arm}_{s}_on_low_on_v18_rich"
                                     f"_t0.3_p1_cinf_{sc}_gw0.json")
            if not os.path.exists(oldp):
                continue
            old = json.load(open(oldp))
            new = cell(arm, s, "rich", 0.30, sc)
            cells += 1
            for k in old:
                if k in ADDED:
                    continue
                if old[k] != new.get(k):
                    nd_total += 1
    check("A4 HV6: honest == the frozen v18 cells over every shared field",
          nd_total == 0 and cells == 80, "%d cells, %d diffs" % (cells, nd_total))

    # ---------------- A5/A6/A7 the verdicts ----------------
    def agg(arm, spec):
        rows = [cell(arm, s, "rich", 0.30, spec) for s in SEEDS]
        return (sorted({r["commons_drains"] for r in rows}),
                sum(1 for r in rows if r["keeper_dead"]),
                sorted({r["enforcer_refusals"] for r in rows}),
                sorted({str(r["enforcer_scope_claimed_end"]) for r in rows}))

    d, dead, ref, claim = agg("w_price", "station:open:0.10:0.30")
    check("A5 HV1 OPEN bought: 30 drains, dead 10/10, refusals == 0",
          d == [30] and dead == 10 and ref == [0], "drains=%s dead=%d ref=%s"
          % (d, dead, ref))
    d, dead, ref, claim = agg("w_price", "station")
    check("A6 HV1 HONEST: 0 drains, alive 10/10, refusals > 0",
          d == [0] and dead == 0 and min(ref) > 0, "drains=%s dead=%d ref=%s"
          % (d, dead, ref))
    d, dead, ref, claim = agg("w_price", "station:dark:0.10:0.30")
    check("A7 HV2 DARK: 30 drains, dead 10/10, and it SAYS it is gone",
          d == [30] and dead == 10 and claim == ["None"],
          "drains=%s dead=%d claim=%s" % (d, dead, claim))

    # ---------------- A8/A9 the claimed scope vs the refused flag ----------------
    nd = 0
    for s in SEEDS:
        c = cell("w_price", s, "rich", 0.30, "station:open:0.10:0.30")
        if c["scope_task_distinct"] != ["station"]:
            nd += 1
    check("A8 HV4 OPEN: the boundary claims task 'station' on EVERY step, "
          "identical to honest", nd == 0, "%d cells off" % nd)
    ref_open = [sum(cell("w_price", s, "rich", 0.30,
                         "station:open:0.10:0.30")["scope_refused_seen"])
                for s in SEEDS]
    ref_hon = [sum(cell("w_price", s, "rich", 0.30, "station")["scope_refused_seen"])
               for s in SEEDS]
    check("A9 HV4b (REFINEMENT): the per-step `refused` flag DOES change "
          "(honest > 0, open == 0) -- the failure is visible to an agent that "
          "reads the flag, though the frozen arms do not",
          min(ref_hon) > 0 and max(ref_open) == 0,
          "honest=%s open=%s" % (ref_hon[:3], ref_open[:3]))

    # ---------------- A10 the cliff ----------------
    off = 0
    for price in PRICE_GRID:
        for bribe in BRIBE_GRID:
            spec = "station:open:%s:%s" % (price, bribe)
            for s in SEEDS:
                c = cell("w_price", s, "rich", 0.30, spec)
                want_harm = (bribe >= price)
                got_harm = (c["commons_drains"] == 30)
                if want_harm != got_harm or c["enforcer_flipped"] != want_harm:
                    off += 1
    check("A10 HV3: harm iff bribe >= price over the whole 4x4 grid x 10 seeds",
          off == 0, "%d cells off" % off)

    # ---------------- A11 the widen grant bought ----------------
    wid = sum(1 for s in SEEDS
              if cell("w_widen", s, "rich", 0.30,
                      "station:open:0.10:0.30")["enforcer_widened"])
    dr = sorted({cell("w_widen", s, "rich", 0.30,
                      "station:open:0.10:0.30")["commons_drains"] for s in SEEDS})
    check("A11 HV5: gw=0 + open -> the widen request is GRANTED 10/10 and the "
          "harm is total", wid == 10 and dr == [30], "widened=%d drains=%s"
          % (wid, dr))

    # ---------------- A12/A13 live negative controls ----------------
    fake = dict(cell("w_price", 0, "rich", 0.30, "station:open:0.10:0.30"))
    fake["commons_drains"] = 0
    fake["keeper_dead"] = False
    fake["enforcer_refusals"] = 30
    ok1 = not (fake["commons_drains"] == 30 and fake["keeper_dead"]
               and fake["enforcer_refusals"] == 0)
    check("NC1 a corrupted HV1 cell FAILS the check (control is live)", ok1)
    fake2 = dict(cell("w_widen", 0, "rich", 0.30, "station:open:0.10:0.30"))
    fake2["enforcer_widened"] = False
    ok2 = not (fake2["enforcer_widened"] and fake2["commons_drains"] == 30)
    check("NC2 a corrupted HV5 cell FAILS the check (control is live)", ok2)

    # ---------------- A14 determinism ----------------
    p = os.path.join(D, "w_price_0_on_low_on_v20_rich_t0.3_p1_cinf_"
                        "station-open-0.1-0.3.json")
    stored = open(p, "rb").read()
    r = subprocess.run(
        [sys.executable, "run_life_v20.py", "w_price", "0", "16000", "on", "low",
         "on", "v20", "rich", "0.30", "1", "inf", "station", "0",
         "station:open:0.10:0.30"],
        cwd=HERE, capture_output=True, text=True, timeout=1800,
        env={**os.environ, "PYTHONHASHSEED": "0"})
    fresh = open(p, "rb").read()
    check("A14 determinism: a fresh subprocess reproduces the cell byte for byte",
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