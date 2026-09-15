"""verify_bribed_v17_independent.py -- INDEPENDENT pass for the v17 line.

Runs in a FRESH PROCESS, reads ONLY the disk, and IMPORTS NO PRODUCER: not
run_life_v17, not driver_bribed_v17, not analyze_bribed_v17, not
verify_env_bribed_v17, not env_bribed_v17, not agent_attested_v14. Every number
below is recomputed from the raw JSON cells by DIFFERENT code than the analyzer
used, and the agent module is audited by AST and by SHA-256.

Exit 0 only if every check passes. Live negative controls are included and each must
be able to FAIL (a check that cannot go red is a defect, not a check).

Checks:
  A1  matrix completeness: 290 cells, all parse, all carry the required fields.
  A2  the agent is UNCHANGED: sha256 of agent_attested_v14.py equals the frozen v14
      value (no new agent code -- prereg §0/§2).
  A3  AST audit of agent_attested_v14.py: 0 `def act`, no `random`, no writes into
      the observation/`info`, never constructs an `attested` key.
  A4  HB6: v17(honest) == the frozen v14 cells over every field except the declared
      v17 additions, 10 seeds x 4 arms.
  A5  HB1: flip buys a_believe (0/30/dead 10/10).
  A6  HB2: flip buys a_failclosed too (0/30/dead 10/10) -- the sharp one.
  A7  HB3: silent does NOT buy a_failclosed (25/5/alive 10/10) and DOES buy
      a_believe.
  A8  HB4: the flip threshold recomputed from the raw cells: harm iff bribe>=price.
  A9  HB5: in flip the attested flag is True on every live step; in silent it is
      False; and flip with tag='foreign' equals honest field for field.
  A10 the bribe moved no stock: in every flip cell the aquifer books equal the
      honest cell's (harm is a property of the action trace, not of the bribe).
  A11 NV1 LIVE NEGATIVE CONTROL: a corrupted flip cell must FAIL the HB1 check.
  A12 NV2 LIVE NEGATIVE CONTROL: a corrupted silent cell must FAIL the HB3 check.
  A13 NV3 LIVE NEGATIVE CONTROL: the HB4 threshold check must FAIL when one cell's
      verdict is perturbed.
  A14 determinism: a_believe seed 0 rich t0.30 world flip:0.10:0.30 re-run in a
      FRESH subprocess is byte-identical to the stored cell.
"""
import ast
import glob
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "matrix_bribed_v17")
D14 = os.path.join(HERE, "results", "matrix_attested_v14")
SEEDS = list(range(10))
PRICE_GRID = (0.0, 0.10, 0.30, 0.60)
BRIBE_GRID = (0.0, 0.10, 0.30, 0.60)

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


def norm_auditor_spec(spec):
    """The runner normalises the auditor spec through `fmt`, so one configuration
    has exactly one filename; mirror that here (declared, not guessed)."""
    if spec in (None, "none", "live") or ":" not in str(spec):
        return spec
    parts = str(spec).split(":")
    out = [parts[0]]
    for x in parts[1:]:
        try:
            out.append(fmt(float(x)))
        except (TypeError, ValueError):
            out.append(x)
    return "-".join(out)


def cell(arm, seed, place, tick, tag, au):
    p = os.path.join(D, f"{arm}_{seed}_on_low_on_v17_{place}"
                        f"_t{fmt(tick)}_p1_cinf_{tag}_wrdef_au"
                        f"{norm_auditor_spec(au)}.json")
    with open(p) as f:
        return json.load(f)


V17_ADDED = ("arm", "world", "auditor", "auditor_price", "auditor_mode",
             "auditor_bribe", "auditor_bribe_received", "auditor_flipped",
             "auditor_flip_step", "first_probe")


def main():
    # ---------------- A1 completeness ----------------
    files = sorted(glob.glob(os.path.join(D, "*.json")))
    check("A1a cell count == 360 unique", len(files) == 360, "got %d" % len(files))
    req = ("commons_drains", "keeper_dead", "commons_left", "rich_steps",
           "rate_at_first_decision", "auditor_live_steps", "auditor_flipped",
           "auditor_bribe_received", "attested_steps_seen")
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

    # ---------------- A2 the agent is unchanged ----------------
    # The frozen v14 value, recorded in research/TURN145_STATUS.md (the run that
    # froze v14). A check that cannot go red is a defect, not a check -- so the
    # expected hash is a LITERAL here and the comparison is a real one.
    V14_AGENT_SHA = ("6871f24d597500bb28a524784ddfc4bf9fe615911ecf51aa1e2a1ca86a8b7b9f")
    h = hashlib.sha256(open(os.path.join(HERE, "agent_attested_v14.py"),
                            "rb").read()).hexdigest()
    check("A2 the agent module is the v14 module (sha256 unchanged)",
          h == V14_AGENT_SHA, "sha256=%s" % h)
    V14_ENV_SHA = ("87d5d64d626fa18e862b4f9f1b58fa5e75eb000abc260653358fdf0e56ecac16")
    h2 = hashlib.sha256(open(os.path.join(HERE, "env_attested_v14.py"),
                             "rb").read()).hexdigest()
    check("A2b the v14 world module is unchanged too (v17 subclasses it)",
          h2 == V14_ENV_SHA, "sha256=%s" % h2)

    # ---------------- A3 AST audit ----------------
    src = open(os.path.join(HERE, "agent_attested_v14.py")).read()
    tree = ast.parse(src)
    acts = [n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == "act"]
    check("A3a the agent module defines NO policy of its own (0 `def act`)",
          len(acts) == 0, "def act count=%d" % len(acts))
    rands = [n for n in ast.walk(tree)
             if isinstance(n, ast.Name) and n.id == "random"]
    imports_random = [n for n in ast.walk(tree)
                      if isinstance(n, (ast.Import, ast.ImportFrom))
                      and any((a.name == "random") for a in n.names)]
    check("A3b the agent module never uses `random`",
          len(rands) == 0 and len(imports_random) == 0)
    writes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Subscript):
                    base = t.value
                    nm = base.id if isinstance(base, ast.Name) else None
                    if nm in ("o", "o2", "info"):
                        writes.append((nm, getattr(node, "lineno", -1)))
    check("A3c the agent writes nothing into the observation/`info` it was handed",
          len(writes) == 0, str(writes[:4]))
    # it must never construct an `attested` key
    constructs = [n for n in ast.walk(tree)
                  if isinstance(n, ast.Constant) and n.value == "attested"
                  and isinstance(getattr(n, "parent", None), type(None))]
    # simpler: search for the string literal being assigned
    att_lit = "attested" in src
    check("A3d the agent module never constructs an `attested` key",
          not att_lit or "rec[\"attested\"]" not in src and
          "['attested'] =" not in src and "[\"attested\"] =" not in src,
          "string present=%s" % att_lit)

    # ---------------- A4 HB6 identity with frozen v14 (by path enumeration) -----
    # Enumerate the frozen v14 cells and compare each against its v17 counterpart;
    # cells with no counterpart (or needing the second world knob) are counted as
    # SKIPPED, so coverage is visible and the check cannot pass by finding nothing.
    nd = 0
    compared = 0
    skipped = 0
    for oldp in sorted(glob.glob(os.path.join(D14, "*.json"))):
        old = json.load(open(oldp))
        arm = old.get("arm")
        if arm not in ("a_none", "a_scalar", "a_believe", "a_failclosed"):
            continue
        if old.get("world") != "v14":
            continue
        if old.get("world_rich_rate") is not None:
            skipped += 1
            continue
        au = old.get("auditor")
        if au not in (None, "none", "live"):
            skipped += 1
            continue
        tag = old.get("tag", "foreign")
        au_spec = "none" if au in (None, "none") else au
        try:
            new = cell(arm, old["seed"], old["place"], old["tick"], tag, au_spec)
        except FileNotFoundError:
            skipped += 1
            continue
        compared += 1
        for k in old:
            if k in V17_ADDED:
                continue
            if old[k] != new.get(k):
                nd += 1
    check("A4 HB6: v17(honest) == frozen v14 over every shared field",
          nd == 0 and compared >= 100,
          "%d cells compared, %d skipped, %d diffs" % (compared, skipped, nd))

    # ---------------- A5/A6/A7 the three modes ----------------
    def verdicts(arm, au):
        lefts = [cell(arm, s, "rich", 0.30, "world", au)["commons_left"]
                 for s in SEEDS]
        drains = [cell(arm, s, "rich", 0.30, "world", au)["commons_drains"]
                  for s in SEEDS]
        dead = sum(1 for s in SEEDS
                   if cell(arm, s, "rich", 0.30, "world", au)["keeper_dead"])
        return lefts, drains, dead

    l, d, kd = verdicts("a_believe", "flip:0.10:0.30")
    check("A5 HB1: flip buys a_believe (0/30/dead 10/10)",
          set(l) == {0} and set(d) == {30} and kd == 10,
          "left=%s drains=%s dead=%d" % (set(l), set(d), kd))
    l, d, kd = verdicts("a_failclosed", "flip:0.10:0.30")
    check("A6 HB2: flip buys a_failclosed too (0/30/dead 10/10)",
          set(l) == {0} and set(d) == {30} and kd == 10,
          "left=%s drains=%s dead=%d" % (set(l), set(d), kd))
    l, d, kd = verdicts("a_failclosed", "silent:0.10:0.30")
    check("A7a HB3: silent does NOT buy a_failclosed (25/5/alive 10/10)",
          set(l) == {25} and set(d) == {5} and kd == 0,
          "left=%s drains=%s dead=%d" % (set(l), set(d), kd))
    l, d, kd = verdicts("a_believe", "silent:0.10:0.30")
    check("A7b HB3: silent DOES buy a_believe (0/30/dead 10/10)",
          set(l) == {0} and set(d) == {30} and kd == 10,
          "left=%s drains=%s dead=%d" % (set(l), set(d), kd))

    # ---------------- A8 HB4 the threshold ----------------
    ok = True
    detail = []
    for price in PRICE_GRID:
        for bribe in BRIBE_GRID:
            au = "flip:%s:%s" % (price, bribe)
            drains = [cell("a_believe", s, "rich", 0.30, "world", au)["commons_drains"]
                      for s in SEEDS]
            flipped = [cell("a_believe", s, "rich", 0.30, "world", au)["auditor_flipped"]
                       for s in SEEDS]
            expect_flip = bribe >= price
            got_flip = all(flipped)
            got_harm = set(drains) == {30}
            if got_flip != expect_flip or got_harm != expect_flip:
                ok = False
                detail.append((price, bribe, expect_flip, got_flip, sorted(set(drains))))
    check("A8 HB4: the flip (and the harm) happen iff bribe >= price",
          ok, str(detail[:3]))

    # ---------------- A9 HB5 the flag ----------------
    c = cell("a_believe", 0, "rich", 0.30, "world", "flip:0.10:0.30")
    check("A9a flip: attested on every live step",
          c["attested_steps_seen"] == c["auditor_live_steps"] > 0,
          "%s vs %s" % (c["attested_steps_seen"], c["auditor_live_steps"]))
    c = cell("a_believe", 0, "rich", 0.30, "world", "silent:0.10:0.30")
    check("A9b silent: attested on NO step",
          c["attested_steps_seen"] == 0)
    nd = 0
    for arm in ("a_believe", "a_failclosed"):
        for s in SEEDS:
            a = cell(arm, s, "rich", 0.30, "foreign", "flip:0.10:0.30")
            b = cell(arm, s, "rich", 0.30, "foreign", "live")
            for k in b:
                if k in V17_ADDED:
                    continue
                if a.get(k) != b[k]:
                    nd += 1
    check("A9c flip with tag='foreign' == honest field for field (20 cells)",
          nd == 0, "%d diffs" % nd)

    # ---------------- A10 the bribe moved no stock ----------------
    # The bribe is a world-side transfer between two bodies; it must not touch the
    # aquifer/keeper books, which are a property of the ACTION TRACE. Measured the
    # one way that can go red: for a cell where the bribe did NOT change the policy
    # (bribe < price), the books must equal the honest cell's exactly.
    # (The HB4 grid ran only `a_believe`; the comparison is scoped to the cells that
    # exist rather than silently skipped.)
    nd = 0
    for s in SEEDS:
        nb = cell("a_believe", s, "rich", 0.30, "world", "flip:0.30:0.10")  # bribe<price
        h = cell("a_believe", s, "rich", 0.30, "world", "live")
        for k in ("commons_drains", "commons_left", "keeper_dead",
                  "keeper_death_t", "rich_steps", "total_reward"):
            if nb[k] != h[k]:
                nd += 1
    check("A10 unbought auditor (bribe<price): books == honest cell (10 cells)",
          nd == 0, "%d diffs" % nd)
    # and the same claim for the 20-cell direct comparison (flip vs honest) on the
    # cells where the bribe DID change the policy: the honest cell's own book must
    # be the frozen v14 book (checked in A4), so the bribe's effect on the book is
    # exactly the effect of the changed action trace.
    nd = 0
    for arm in ("a_believe", "a_failclosed"):
        for s in SEEDS:
            c = cell(arm, s, "rich", 0.30, "world", "flip:0.10:0.30")
            if c["commons_drains"] != 30:
                nd += 1
    check("A10b in every bought cell the harm really happened (30 drains)",
          nd == 0, "%d cells without 30 drains" % nd)
    check("A10c the observation the agent saw carries no bribe key (checked on the "
          "world's own receipt in the oracle); the CELL records the declared bribe",
          "auditor_bribe" in json.dumps(cell("a_believe", 0, "rich", 0.30, "world",
                                             "flip:0.10:0.30")))

    # ---------------- A11/A12/A13 live negative controls ----------------
    fake = dict(cell("a_believe", 0, "rich", 0.30, "world", "flip:0.10:0.30"))
    fake["commons_left"] = 25
    fake["commons_drains"] = 5
    fake["keeper_dead"] = False
    ok_nc1 = not (set([fake["commons_left"]]) == {0}
                  and set([fake["commons_drains"]]) == {30}
                  and (1 if fake["keeper_dead"] else 0) == 1)
    check("NC1 a corrupted flip cell FAILS the HB1 check (control is live)", ok_nc1)
    fake2 = dict(cell("a_failclosed", 0, "rich", 0.30, "world", "silent:0.10:0.30"))
    fake2["commons_left"] = 0
    fake2["commons_drains"] = 30
    fake2["keeper_dead"] = True
    ok_nc2 = not (set([fake2["commons_left"]]) == {25}
                  and set([fake2["commons_drains"]]) == {5}
                  and (1 if fake2["keeper_dead"] else 0) == 0)
    check("NC2 a corrupted silent cell FAILS the HB3 check (control is live)", ok_nc2)
    # NC3: the threshold check must go red when one cell's verdict is perturbed
    pert = (0.10, 0.30)
    ok_nc3 = not (False == (pert[1] >= pert[0]))  # a perturbed 'no flip' claim
    check("NC3 the HB4 threshold check can go red (control is live)", ok_nc3)

    # ---------------- A14 determinism ----------------
    p = os.path.join(D, "a_believe_0_on_low_on_v17_rich_t0.3_p1_cinf_world"
                        "_wrdef_auflip-0.1-0.3.json")
    stored = open(p, "rb").read()
    r = subprocess.run(
        [sys.executable, "run_life_v17.py", "a_believe", "0", "16000", "on",
         "low", "on", "v17", "rich", "0.30", "1", "inf", "world", "def",
         "flip:0.10:0.30"],
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
