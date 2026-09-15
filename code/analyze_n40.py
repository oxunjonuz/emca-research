"""analyze_n40.py -- the n=40 replication verdict table (turn 152).

Reads ONLY results/replicate_n40/*.json (30 fresh seeds, 10..39) and reports each
headline verdict recomputed on the fresh seeds alone. Imports no producer. The point
of the exercise is a verdict that does NOT hold on fresh seeds, so each row prints
the actual distribution, not a boolean.

Usage: python3 analyze_n40.py
"""
import glob
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "results", "replicate_n40")
SEEDS = list(range(10, 40))


def load(tag, seed):
    p = os.path.join(D, f"{tag}_{seed}.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def rows(tag):
    return [load(tag, s) for s in SEEDS if load(tag, s) is not None]


def summarize(tag, keys):
    rs = rows(tag)
    out = {}
    for k in keys:
        vals = [r.get(k) for r in rs]
        uniq = sorted({json.dumps(v) for v in vals})
        out[k] = uniq if len(uniq) <= 4 else \
            "min=%.3f max=%.3f mean=%.3f" % (
                min(v for v in vals if isinstance(v, (int, float))),
                max(v for v in vals if isinstance(v, (int, float))),
                statistics.mean(v for v in vals if isinstance(v, (int, float))))
    return len(rs), out


def main():
    print("=== n=40 replication: 30 FRESH seeds (10..39), the original 10 not re-run ===\n")
    checks = []

    def ck(claim, cond, detail):
        checks.append((claim, bool(cond), detail))
        print(("PASS " if cond else "FAIL ") + f"{claim}  -- {detail}")

    # ---- v10 B2 / B3 / B4
    n, s = summarize("v10_s2_given_rule_low_c0", ("commons_left", "keeper_dead"))
    ck("v10 B2 the given rule stops the harm", s["commons_left"] == ["9"],
       f"n={n} commons_left={s['commons_left']} keeper_dead={s['keeper_dead']}")
    n, s = summarize("v10_s3_victim_keyed_low_c0", ("commons_left", "keeper_dead"))
    ck("v10 B3 coupling=0 the victim-keyed rule is INERT",
       s["commons_left"] == ["0"] and s["keeper_dead"] == ["true"],
       f"n={n} commons_left={s['commons_left']} keeper_dead={s['keeper_dead']}")
    n, s = summarize("v10_s3_victim_keyed_low_c1", ("commons_left", "keeper_dead"))
    ck("v10 B3 coupling=1 the same rule WORKS",
       s["commons_left"] == ["17"] and s["keeper_dead"] == ["false"],
       f"n={n} commons_left={s['commons_left']} keeper_dead={s['keeper_dead']}")
    n, s = summarize("v10_s4_internalized_low_c0", ("commons_left",))
    ck("v10 B4 low: the internalized value restrains", s["commons_left"] == ["25"],
       f"n={n} commons_left={s['commons_left']}")
    n, s = summarize("v10_s4_internalized_high_c0", ("commons_left", "keeper_dead"))
    ck("v10 B4 high: the same rule does NOT restrain",
       s["commons_left"] == ["0"] and s["keeper_dead"] == ["true"],
       f"n={n} commons_left={s['commons_left']}")

    # ---- v11 the harm curve
    n, s = summarize("v11_n_none", ("commons_drains",))
    ck("v11 the unbraked arm's harm is 5", s["commons_drains"] == ["5"],
       f"n={n} drains={s['commons_drains']}")
    for arm in ("n_inflate_g6", "n_inflate_g10"):
        n, s = summarize(f"v11_{arm}", ("commons_drains",))
        ck(f"v11 {arm}: the inflated appraisal drains everything (W6 stays refuted)",
           s["commons_drains"] == ["30"], f"n={n} drains={s['commons_drains']}")

    # ---- v12 the threshold (the driver's path uses fmt(), which drops the trailing
    # zero: the cell for tick 0.30 is written `t0.3`, so the tag must match)
    for tick, want in (("0.24", "5"), ("0.25", "5"), ("0.26", "30")):
        n, s = summarize(f"v12_v_price_rich_t{tick}", ("commons_drains",))
        ck(f"v12 the bribe threshold at tick {tick} -> {want} drains",
           s["commons_drains"] == [want], f"n={n} drains={s['commons_drains']}")
    n, s = summarize("v12_v_price_rich_t0.3", ("commons_drains",))
    ck("v12 the bribe threshold at tick 0.30 -> 30 drains",
       s["commons_drains"] == ["30"], f"n={n} drains={s['commons_drains']}")

    # ---- v13 the hole
    n, s = summarize("v13_l_ledger_lie", ("commons_drains", "keeper_dead"))
    ck("v13 H5 the lie buys the ledger arm completely",
       s["commons_drains"] == ["30"] and s["keeper_dead"] == ["true"],
       f"n={n} {s}")
    n, s = summarize("v13_l_ledger_honest", ("commons_drains", "commons_left"))
    ck("v13 the honest label restrains", s["commons_drains"] == ["5"],
       f"n={n} {s}")

    # ---- v14 HA1 / HA3
    n, s = summarize("v14_a_believe_lie_live", ("commons_drains", "keeper_dead",
                                                "rate_at_first_decision"))
    ck("v14 HA1 the honest auditor closes the hole (the lie fails)",
       s["commons_drains"] == ["5"] and s["keeper_dead"] == ["false"]
       and s["rate_at_first_decision"] == ["0.04999999999999999"],
       f"n={n} {s}")
    n, s = summarize("v14_a_believe_lie_none", ("commons_drains",))
    ck("v14 HA3 with no auditor the lie works again", s["commons_drains"] == ["30"],
       f"n={n} {s}")

    # ---- v16
    n, s = summarize("v16_w_price_rich_t0.25", ("commons_drains",))
    ck("v16 t=0.25 below the threshold -> 5 drains", s["commons_drains"] == ["5"],
       f"n={n} {s}")
    n, s = summarize("v16_w_price_rich_t0.26", ("commons_drains",))
    ck("v16 t=0.26 above the threshold -> 30 drains", s["commons_drains"] == ["30"],
       f"n={n} {s}")
    n, s = summarize("v16_n_doctor_rich_t0.30", ("commons_drains", "keeper_dead"))
    n_drain = sum(1 for r in rows("v16_n_doctor_rich_t0.30")
                  if r["commons_drains"] > 0)
    ck("v16 the doctor never drains (the harm is outside its scope)",
       s["commons_drains"] == ["0"], f"n={n} {s}")
    ck("REPLICATION FINDING: v16's doctor drains on a minority of FRESH seeds "
       "(the frozen matrix had no such cell)",
       n_drain > 0, "%d of %d fresh seeds drain (the frozen v16: 0 of 260 cells)"
       % (n_drain, n))

    # ---- v17
    n, s = summarize("v17_a_believe_flip", ("commons_drains", "keeper_dead"))
    ck("v17 HB1 the bought auditor buys the believe arm",
       s["commons_drains"] == ["30"] and s["keeper_dead"] == ["true"],
       f"n={n} {s}")
    n, s = summarize("v17_a_failclosed_silent", ("commons_drains",))
    ck("v17 HB3 the silenced auditor does not buy the cautious arm",
       s["commons_drains"] == ["5"], f"n={n} {s}")

    # ---- v18
    n, s = summarize("v18_w_price_station", ("commons_drains", "enforcer_refusals"))
    ck("v18 HE1 the world's refusal stops the willing agent",
       s["commons_drains"] == ["0"] and "0" not in s["enforcer_refusals"],
       f"n={n} {s}")
    n, s = summarize("v18_w_widen_none", ("commons_drains",))
    ck("v18 the widen arm with no scope drains everything",
       s["commons_drains"] == ["30"], f"n={n} {s}")

    # ---- v15 the paired contrast, recomputed on fresh seeds
    def a0share(tag):
        vals = []
        for s in SEEDS:
            r = load(tag, s)
            if r is None:
                continue
            tr = r["trace"]
            vals.append(sum(1 for x in tr if x["action"] == "a0") / len(tr))
        return vals
    ctx = a0share("v15_ig_ctx")
    rel = a0share("v15_ig_relevant")
    rnd = a0share("v15_rand")
    ck("v15 H2 pure information gain is indifferent on fresh seeds "
       f"(mean {statistics.mean(ctx):.3f})",
       abs(statistics.mean(ctx) - 0.25) < 0.02,
       "shares=%s" % ["%.3f" % x for x in ctx[:6]])
    ck("v15 H3 the relevance criterion restores the preference on fresh seeds "
       f"(mean {statistics.mean(rel):.3f})",
       statistics.mean(rel) > 0.95,
       "min=%.3f" % min(rel))
    ck("v15 H6 random stays at the coin floor (mean %.3f)" % statistics.mean(rnd),
       abs(statistics.mean(rnd) - 0.25) < 0.02, "")

    ok = sum(1 for _, c, _ in checks if c)
    print("\n%d/%d replicated verdicts hold on 30 fresh seeds" % (ok, len(checks)))
    out = {"verdicts": [{"claim": a, "holds": c, "detail": d} for a, c, d in checks],
           "seeds": SEEDS}
    with open(os.path.join(HERE, "results", "analyze_n40.json"), "w") as f:
        json.dump(out, f, indent=1)
    with open(os.path.join(HERE, "results", "analyze_n40.txt"), "w") as f:
        f.write("\n".join("%s %s -- %s" % ("PASS" if c else "FAIL", a, d)
                          for a, c, d in checks) + "\n")
    if ok != len(checks):
        sys.exit(1)
    print("ALL GREEN")


if __name__ == "__main__":
    main()