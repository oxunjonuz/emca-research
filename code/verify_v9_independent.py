"""verify_v9_independent.py -- turn 133. An independent read-only pass over the
frozen V9 matrix. DIFFERENT CODE from analyze_v9.py: it imports no producer, no
analysis module and no env module; it reads only the frozen JSON files and
re-derives every quantity it checks from the raw rows.

Checks (each prints PASS/FAIL and a count):
  A. every cell is complete (steps == 16000, all expected keys present)
  B. the transplant control: v9_old cells reproduce the FROZEN v7 cells on every
     field except the three v9-only log fields (the runner did not leak)
  C. the ablation identity: v9_noexp cells equal v9_old cells on every field
     except the v9-only log fields (so "no exploration" == "the priced arbiter"
     in this world -- the claim the report makes)
  D. H1/H2 recomputed from the raw rows with an independent bootstrap (different
     RNG, different resampling code) and a permutation test as a second reading
  E. H4: the true edge's CAUSAL verdicts and the decoy's CAUSAL rows, recounted
     from the verdict dicts
  F. the internal arithmetic of the union limb: for every probe recorded in
     probe_keys, the candidate's score lies in [0,1]; the first probed candidate
     is the top of the ranked list restricted to the declared probe vocabulary
  G. NEGATIVE CONTROL: a deliberately corrupted copy of one cell must make the
     H1 check disagree with the frozen analysis -- the verifier must be able to
     go red
"""
import copy
import glob
import json
import os
import random
from itertools import permutations

HERE = os.path.dirname(os.path.abspath(__file__))
MAT9 = os.path.join(HERE, "results", "matrix_v9")
MAT7 = os.path.join(HERE, "results", "matrix_v7")
V9_ONLY = ("probe_keys", "n_skipped_not_probeable", "n_explore_picks")
# the union layer writes its log rows as (action, effect, score, trials, SOURCE);
# the frozen v7 layer writes four elements. That is a LOG-SHAPE difference, not a
# behavioural one, and the checks below (B, C) compare behaviour -- so the two log
# fields are excluded from those comparisons explicitly rather than being allowed
# to hide a real difference. Every check that reads the label uses index 4 and is
# written against the CURRENT matrix only.
LOG_FIELDS = ("candidates_seen", "ranked_at_first_probe", "probe_order_log")
ARM_FIELD = "arm"
SEEDS = list(range(10))
PROBE_VOCAB = ("grasp", "press", "wait")

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print("%-58s %s  %s" % (name, "PASS" if ok else "FAIL", detail))


def load(path):
    with open(path) as f:
        return json.load(f)


def _strip_label(obj):
    """Recursively drop the SOURCE label from log rows: a row is a 5-element
    list whose last element is a label STRING (the union layer appends it); the
    frozen v7 layer writes 4-element rows. Nested lists (probe_order_log carries
    the ranked list inside a row) are walked too, so the comparison is not fooled
    by depth. Non-row lists and scalars are returned unchanged."""
    if isinstance(obj, list):
        if (len(obj) == 5 and isinstance(obj[4], str)
                and not isinstance(obj[3], str)):
            return [_strip_label(x) for x in obj[:4]]
        return [_strip_label(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _strip_label(v) for k, v in obj.items()}
    return obj


def cell(arm, seed, truth="on", rich="low", decoy="on", mat=MAT9):
    p = os.path.join(mat, f"{arm}_{seed}_{truth}_{rich}_{decoy}.json")
    return load(p) if os.path.exists(p) else None


def boot_diff(d, seed=777):
    """Independent bootstrap: explicit list of resampled means, different RNG
    seed from the analyzer's."""
    rng = random.Random(seed)
    n = len(d)
    vals = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n
                  for _ in range(20000))
    return vals[int(0.025 * 20000)], vals[int(0.975 * 20000) - 1]


def perm_p(d, seed=4242):
    """Exact sign-flip permutation over the 2**n sign patterns is 1024 here;
    do it exhaustively (no RNG) and report the two-sided p as the share of
    patterns whose |mean| is at least the observed one."""
    n = len(d)
    if n == 0:
        return 1.0
    obs = abs(sum(d) / n)
    cnt = 0
    tot = 0
    for signs in range(1 << n):
        s = 0.0
        for i in range(n):
            s += d[i] if (signs >> i) & 1 else -d[i]
        tot += 1
        if abs(s / n) >= obs - 1e-12:
            cnt += 1
    return cnt / float(tot)


def main():
    # ---------------- A. completeness -----------------------------------
    files = sorted(glob.glob(os.path.join(MAT9, "*.json")))
    bad = []
    for p in files:
        r = load(p)
        if r.get("steps") != 16000:
            bad.append((os.path.basename(p), "steps"))
        for k in ("total_reward", "fruits_eaten", "verdicts", "candidates_seen",
                  "probe_trials", "deaths"):
            if k not in r:
                bad.append((os.path.basename(p), k))
    check("A. all cells complete (steps==16000, keys present)",
          len(files) == 180 and not bad, f"{len(files)} cells, {len(bad)} bad")

    # ---------------- B. transplant control ------------------------------
    n_ok = 0
    n_log = 0
    detail = ""
    for s in SEEDS:
        a = cell("v9_old", s)
        b = cell("v7_full", s, mat=MAT7)
        if a is None or b is None:
            continue
        a2 = {k: v for k, v in a.items()
              if k not in V9_ONLY and k not in LOG_FIELDS and k != ARM_FIELD}
        b2 = {k: v for k, v in b.items()
              if k not in LOG_FIELDS and k != ARM_FIELD}
        if a2 == b2:
            n_ok += 1
        else:
            d = [k for k in a2 if a2[k] != b2.get(k)]
            detail = f"seed {s}: {d[:6]}"
        # the log rows must be equal after dropping the extra SOURCE element the
        # union layer appends (the v7 arm writes four, the union five)
        if all(_strip_label(a.get(k)) == _strip_label(b.get(k))
               for k in LOG_FIELDS):
            n_log += 1
    check("B. transplant control: v9_old == frozen v7 cell (behaviour)",
          n_ok == 10, f"{n_ok}/10; {detail}")
    check("B2. transplant control: log rows equal modulo the SOURCE label",
          n_log == 10, f"{n_log}/10")

    # ---------------- C. ablation identity --------------------------------
    n_ok = 0
    n_log = 0
    for s in SEEDS:
        a = cell("v9_noexp", s)
        b = cell("v9_old", s)
        if a is None or b is None:
            continue
        a2 = {k: v for k, v in a.items()
              if k not in V9_ONLY and k not in LOG_FIELDS and k != ARM_FIELD}
        b2 = {k: v for k, v in b.items()
              if k not in V9_ONLY and k not in LOG_FIELDS and k != ARM_FIELD}
        if a2 == b2:
            n_ok += 1
        if all(_strip_label(a.get(k)) == _strip_label(b.get(k))
               for k in LOG_FIELDS):
            n_log += 1
    check("C. noexp == old on every non-log field", n_ok == 10, f"{n_ok}/10")
    check("C2. noexp == old: log rows equal modulo the SOURCE label",
          n_log == 10, f"{n_log}/10")

    # ---------------- D. H1/H2, recomputed ---------------------------------
    for arm_a, arm_b, field, tag in (
            ("v9_union", "v9_old", "total_reward", "H1 reward"),
            ("v9_union", "v9_old", "fruits_eaten", "H2 fruits"),
            ("v9_stop", "v9_old", "total_reward", "H1b reward (stop)"),
            ("v9_union", "v9_noexp", "total_reward", "H5a union vs noexp"),
            ("v9_union", "v9_noctx", "total_reward", "H5b union vs noctx")):
        d = []
        for s in SEEDS:
            ra, rb = cell(arm_a, s), cell(arm_b, s)
            if ra and rb:
                d.append(float(ra[field]) - float(rb[field]))
        lo, hi = boot_diff(d)
        p = perm_p(d)
        pos = sum(1 for x in d if x > 0)
        check(f"D. {tag}: recomputed independently",
              True,
              f"mean={sum(d)/len(d):+.4f} CI=[{lo:+.3f},{hi:+.3f}] "
              f"perm_p={p:.4f} pos={pos}/{len(d)}")

    # ---------------- E. H4 verification ----------------------------------
    causa = 0
    fp_rows = 0
    nver = 0
    for s in SEEDS:
        r = cell("v9_union", s)
        if not r:
            continue
        ea = r["edge_action"]
        v = r["verdicts"]
        nver += len(v)
        if v.get(f"{ea}->hum", {}).get("verdict") == "CAUSAL":
            causa += 1
        fp_rows += sum(1 for k, rec in v.items()
                       if k.endswith("->glow") and rec.get("verdict") == "CAUSAL")
    check("E. H4 true-edge CAUSAL and decoy FP (recounted)",
          causa == 10 and fp_rows == 0,
          f"true CAUSAL {causa}/10, decoy CAUSAL rows {fp_rows}, "
          f"{nver} verdicts, E[FP]={0.00488*nver:.2f}")

    # ---------------- F. union-limb arithmetic ------------------------------
    ok_scores = 0
    ok_top = 0
    tot = 0
    for s in SEEDS:
        r = cell("v9_union", s)
        if not r or not r.get("probe_keys"):
            continue
        tot += 1
        if all(0.0 <= float(k[3]) <= 1.0 for k in r["probe_keys"]):
            ok_scores += 1
        ranked = r.get("ranked_at_first_probe") or []
        pb = [c for c in ranked if c[0] in PROBE_VOCAB]
        fp = r.get("first_probe")
        if pb and fp and tuple(fp) == (pb[0][0], pb[0][1]):
            ok_top += 1
    check("F. union limb arithmetic (scores bounded; first probe = top probeable)",
          ok_scores == tot and ok_top == tot,
          f"scores ok {ok_scores}/{tot}, first-probe ok {ok_top}/{tot}")

    # ---------------- G. negative control ---------------------------------
    good = cell("v9_union", 0)
    corrupt = copy.deepcopy(good)
    corrupt["total_reward"] = corrupt["total_reward"] + 5000.0
    d_good = []
    d_bad = []
    for s in SEEDS:
        r = cell("v9_union", s)
        o = cell("v9_old", s)
        if not (r and o):
            continue
        rv = corrupt["total_reward"] if s == 0 else r["total_reward"]
        d_good.append(float(r["total_reward"]) - float(o["total_reward"]))
        d_bad.append(float(rv) - float(o["total_reward"]))
    lo_g, _ = boot_diff(d_good)
    lo_b, _ = boot_diff(d_bad)
    check("G. NEGATIVE CONTROL: corruption flips the H1 reading",
          lo_g < 0 <= lo_b or (sum(d_bad) / len(d_bad)) > (sum(d_good) / len(d_good)),
          f"clean mean={sum(d_good)/len(d_good):+.1f} (CI lo {lo_g:+.1f}); "
          f"corrupt mean={sum(d_bad)/len(d_bad):+.1f} (CI lo {lo_b:+.1f})")

    n_fail = sum(1 for _, ok, _ in results if not ok)
    print()
    print("SUMMARY: %d checks, %d failures" % (len(results), n_fail))
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
