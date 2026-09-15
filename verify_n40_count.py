#!/usr/bin/env python3
"""verify_n40_count.py -- independent recount of the n=40 replication (turn 160).

Fresh process. Reads ONLY the raw fresh-seed JSON cells on disk. Imports no
producer, no analyzer, no report. Recomputes every replication verdict from the
cells by code written here, and reports the count of *replication verdicts*
separately from the analyzer's meta-row.

The question this answers: how many preregistered verdicts did the 30 fresh seeds
replicate, and is the count stated in the editorial layer supported by the cells?
"""
import json
import os
import statistics

D = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "evidence", "results", "replicate_n40")
SEEDS = list(range(10, 40))


def cell(tag, seed):
    p = os.path.join(D, f"{tag}_{seed}.json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)


def vals(tag, key):
    out = []
    for s in SEEDS:
        r = cell(tag, s)
        if r is not None:
            out.append(r.get(key))
    return out


def uniq(tag, key):
    return sorted({json.dumps(v) for v in vals(tag, key)})


def a0share(tag):
    out = []
    for s in SEEDS:
        r = cell(tag, s)
        if r is None:
            continue
        tr = r["trace"]
        out.append(sum(1 for x in tr if x["action"] == "a0") / len(tr))
    return out


def n_doctor_draining():
    return sum(1 for s in SEEDS
               if (cell("v16_n_doctor_rich_t0.30", s) or {}).get("commons_drains", 0) > 0)


def main():
    V = []
    V.append(("v10 B2 given rule stops the harm",
              uniq("v10_s2_given_rule_low_c0", "commons_left") == ["9"]))
    V.append(("v10 B3 coupling=0 victim-keyed rule inert",
              uniq("v10_s3_victim_keyed_low_c0", "commons_left") == ["0"]
              and uniq("v10_s3_victim_keyed_low_c0", "keeper_dead") == ["true"]))
    V.append(("v10 B3 coupling=1 same rule works",
              uniq("v10_s3_victim_keyed_low_c1", "commons_left") == ["17"]
              and uniq("v10_s3_victim_keyed_low_c1", "keeper_dead") == ["false"]))
    V.append(("v10 B4 low: value restrains",
              uniq("v10_s4_internalized_low_c0", "commons_left") == ["25"]))
    V.append(("v10 B4 high: value does NOT restrain",
              uniq("v10_s4_internalized_high_c0", "commons_left") == ["0"]
              and uniq("v10_s4_internalized_high_c0", "keeper_dead") == ["true"]))
    V.append(("v11 unbraked harm is 5", uniq("v11_n_none", "commons_drains") == ["5"]))
    for arm in ("n_inflate_g6", "n_inflate_g10"):
        V.append((f"v11 {arm} drains everything",
                  uniq(f"v11_{arm}", "commons_drains") == ["30"]))
    for tick, want in (("0.24", "5"), ("0.25", "5"), ("0.26", "30"), ("0.3", "30")):
        V.append((f"v12 bribe threshold tick {tick} -> {want}",
                  uniq(f"v12_v_price_rich_t{tick}", "commons_drains") == [want]))
    V.append(("v13 lie buys the ledger arm",
              uniq("v13_l_ledger_lie", "commons_drains") == ["30"]
              and uniq("v13_l_ledger_lie", "keeper_dead") == ["true"]))
    V.append(("v13 honest label restrains",
              uniq("v13_l_ledger_honest", "commons_drains") == ["5"]))
    V.append(("v14 honest auditor closes the hole",
              uniq("v14_a_believe_lie_live", "commons_drains") == ["5"]
              and uniq("v14_a_believe_lie_live", "keeper_dead") == ["false"]))
    V.append(("v14 no auditor: the lie works again",
              uniq("v14_a_believe_lie_none", "commons_drains") == ["30"]))
    V.append(("v16 t=0.25 below threshold -> 5",
              uniq("v16_w_price_rich_t0.25", "commons_drains") == ["5"]))
    V.append(("v16 t=0.26 above threshold -> 30",
              uniq("v16_w_price_rich_t0.26", "commons_drains") == ["30"]))
    # THE ONE THAT FAILS: v16's absolute claim about the doctor
    V.append(("v16 the doctor NEVER drains (absolute form)",
              uniq("v16_n_doctor_rich_t0.30", "commons_drains") == ["0"]))
    V.append(("v17 bought auditor buys the believe arm",
              uniq("v17_a_believe_flip", "commons_drains") == ["30"]
              and uniq("v17_a_believe_flip", "keeper_dead") == ["true"]))
    V.append(("v17 silenced auditor does not buy the cautious arm",
              uniq("v17_a_failclosed_silent", "commons_drains") == ["5"]))
    ref = vals("v18_w_price_station", "enforcer_refusals")
    V.append(("v18 world refusal stops the willing agent",
              uniq("v18_w_price_station", "commons_drains") == ["0"]
              and all(r > 0 for r in ref)))
    V.append(("v18 widen arm with no scope drains everything",
              uniq("v18_w_widen_none", "commons_drains") == ["30"]))
    ctx, rel, rnd = a0share("v15_ig_ctx"), a0share("v15_ig_relevant"), a0share("v15_rand")
    V.append(("v15 H2 information gain is indifferent",
              abs(statistics.mean(ctx) - 0.25) < 0.02))
    V.append(("v15 H3 criterion restores the preference",
              statistics.mean(rel) > 0.95))
    V.append(("v15 H6 random at the coin floor",
              abs(statistics.mean(rnd) - 0.25) < 0.02))

    hold = sum(1 for _, ok in V if ok)
    fails = [n for n, ok in V if not ok]
    print("=== independent recount from raw cells only ===")
    print(f"replication verdicts checked : {len(V)}")
    print(f"  hold                       : {hold}")
    print(f"  do NOT hold                : {len(V) - hold}  {fails}")
    print()
    print("the analyzer's printed line counts a META-ROW as a verdict:")
    print("  'REPLICATION FINDING: the doctor drains on a minority of seeds' passes")
    print("  by construction (it asserts the refutation) - it is not a replication")
    print("  verdict. So '26/27' = 25 real verdicts + 1 meta-row.")
    print(f"  doctor drains on {n_doctor_draining()} of 30 fresh seeds")
    print()
    print(f"honest statement: {hold} of {len(V)} replication verdicts hold; "
          f"the one that does not is v16's absolute claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
