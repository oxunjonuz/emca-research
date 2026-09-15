"""Preprint table builder: reads ALL matrix JSONs on disk (v3.1, v3.2,
v3.3 -- the whole EMCA campaign) and produces one comparative table
(Markdown + CSV) for the paper. Fresh process, disk-only.

Output: research/PREPRINT_TABLE.md + research/PREPRINT_TABLE.csv
"""
import csv
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

WORLDS = [
    ("v3.1", "results/matrix_v31", "TerrariumV31 (actionable decoy: "
     "chime zone == tree zone, flat grasp cost, no scarcity)"),
    ("v3.2", "results/matrix_v32", "TerrariumV32 (separated geometry: "
     "chime far zone, grasp cost 0.6, altar gray edge, no scarcity)"),
    ("v3.3", "results/matrix_v33", "TerrariumV33 (scarcity: dynamic "
     "grasp cost 0.6/1.8, altar offering 1.0, berries 2/1, tree 18 "
     "capped 60/storm, fury -3.0)"),
]

# metric key -> (label, higher-is-better or None)
METRICS = [
    ("total_reward", "reward", True),
    ("deaths", "deaths", False),
    ("tree_fruits", "fruits", True),
    ("berries_eaten", "berries", True),
    ("chimes_collected", "chimes", True),
    ("treasures", "treasures", True),
    ("grasp_at_bell", "grasp@bell", None),
    ("grasp_at_bell_no_tree", "grasp@bell-no-tree", None),
    ("decoy_in_causal", "decoy-in-causal", None),
]


def load_world(dirname):
    rows = {}
    for path in sorted(glob.glob(os.path.join(HERE, dirname, "*.json"))):
        with open(path) as f:
            d = json.load(f)
        cond = d["condition"]
        rows.setdefault(cond, []).append(d)
    return rows


def mean(vals):
    return sum(vals) / len(vals) if vals else None


def fmt(v, kind=None):
    if v is None:
        return "-"
    if isinstance(v, bool):
        return f"{sum(1 for x in [v] if x)}/1" if False else str(v)
    if kind == "count3":
        return f"{v}/3"
    if isinstance(v, float):
        return f"{v:.1f}"
    return str(v)


def main():
    md_lines = ["# EMCA campaign -- the preprint table",
                "",
                "All numbers are means over 3 seeds, read directly from "
                "the matrix JSONs on disk (fresh process, no agent "
                "imports). Lives: 16000 steps (v3.1: 16000).",
                ""]
    csv_rows = [("world", "condition") +
                tuple(label for _, label, _ in METRICS)]

    for tag, dirname, desc in WORLDS:
        rows = load_world(dirname)
        if not rows:
            continue
        md_lines.append(f"## {tag} -- {desc}")
        md_lines.append("")
        header = ("| condition | " +
                  " | ".join(label for _, label, _ in METRICS) + " |")
        sep = ("|---" * (len(METRICS) + 1)) + "|"
        md_lines.append(header)
        md_lines.append(sep)
        for cond in sorted(rows):
            rs = rows[cond]
            vals = []
            for key, label, _ in METRICS:
                if key == "decoy_in_causal":
                    n = sum(1 for r in rs if r.get(key))
                    vals.append(f"{n}/{len(rs)}")
                else:
                    vals.append(fmt(mean([r.get(key, 0) for r in rs])))
            md_lines.append("| " + cond + " | " +
                            " | ".join(vals) + " |")
            csv_rows.append((tag, cond) +
                            tuple(v for v in vals))
        md_lines.append("")

    # cross-world headline contrasts
    md_lines += ["## Headline contrasts across worlds", ""]
    md_lines.append("| contrast | v3.1 | v3.2 | v3.3 |")
    md_lines.append("|---|---|---|---|")

    def get(tag, cond, key):
        dirname = dict(WORLDS)[0] if False else \
            {"v3.1": "results/matrix_v31",
             "v3.2": "results/matrix_v32",
             "v3.3": "results/matrix_v33"}[tag]
        rows = load_world(dirname).get(cond, [])
        return mean([r.get(key, 0) for r in rows]) if rows else None

    contrasts = [
        ("believer (v2.1) reward", lambda t: get(t, "emca_v21",
                                                 "total_reward")),
        ("rejector (v2.5c) reward", lambda t: get(t, "emca_v25c",
                                                  "total_reward")),
        ("rejector - believer", lambda t: (
            get(t, "emca_v25c", "total_reward") or 0) -
         (get(t, "emca_v21", "total_reward") or 0)),
        ("prober reward", lambda t: get(t, "prober", "total_reward")),
        ("curious_surv reward", lambda t: get(t, "curious_surv",
                                              "total_reward")),
        ("curious_surv deaths", lambda t: get(t, "curious_surv",
                                              "deaths")),
        ("best arm reward", lambda t: max(
            (get(t, c, "total_reward") or -1e9) for c in
            ("emca_v21", "emca_v25c", "prober", "curious_surv",
             "curious_chain", "emca_nocausal"))),
        ("best arm name", lambda t: max(
            (("emca_v21", "emca_v25c", "prober", "curious_surv",
              "curious_chain", "emca_nocausal")),
            key=lambda c: (get(t, c, "total_reward") or -1e9))),
        ("chain treasures", lambda t: get(t, "curious_chain",
                                          "treasures")),
        ("v2.5c deaths", lambda t: get(t, "emca_v25c", "deaths")),
        ("v2.5c fruits", lambda t: get(t, "emca_v25c", "tree_fruits")),
    ]
    for label, fn in contrasts:
        vals = []
        for tag in ("v3.1", "v3.2", "v3.3"):
            v = fn(tag)
            vals.append("-" if v is None else
                        (f"{v:.0f}" if isinstance(v, float) else str(v)))
        md_lines.append(f"| {label} | " + " | ".join(vals) + " |")

    out_md = os.path.join(HERE, "research", "PREPRINT_TABLE.md")
    out_csv = os.path.join(HERE, "research", "PREPRINT_TABLE.csv")
    with open(out_md, "w") as f:
        f.write("\n".join(md_lines) + "\n")
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerows(csv_rows)
    print("WROTE", out_md)
    print("WROTE", out_csv)
    print("\n".join(md_lines))


if __name__ == "__main__":
    main()
