#!/usr/bin/env python3
"""Turn-153 independent check of the v17/v18/replication claims.

Fresh process, disk only, imports NO producer. Reads the raw JSON cells directly and
recomputes the load-bearing numbers the package's section 04 now quotes.
"""
import glob, json, os, subprocess, sys

A = "/work/Shopify/audit-work/agent_arch"
PKG = os.path.join(A, "PUBLICATION_V1_V16")
E = os.path.join(PKG, "evidence", "results")
ok = fail = 0
def chk(name, cond, extra=""):
    global ok, fail
    if cond: ok += 1; print("PASS", name, extra)
    else: fail += 1; print("FAIL", name, extra)

for d, want in (("matrix_bribed_v17", 360), ("matrix_enforced_v18", 130),
                ("replicate_n40", 870)):
    got = len(glob.glob(os.path.join(E, d, "*.json")))
    chk("cell count %s == %d" % (d, want), got == want, "got %d" % got)

V = os.path.join(E, "matrix_bribed_v17")
for label, fn, want in (
    ("v17 flip a_believe: 0 left / 30 drains / keeper dead",
     "a_believe_0_on_low_on_v17_rich_t0.3_p1_cinf_world_wrdef_auflip-0.1-0.3.json",
     (0, 30, True)),
    ("v17 silent a_failclosed: 25 left / 5 drains / keeper alive",
     "a_failclosed_0_on_low_on_v17_rich_t0.3_p1_cinf_world_wrdef_ausilent-0.1-0.3.json",
     (25, 5, False)),
):
    p = os.path.join(V, fn)
    if not os.path.exists(p):
        chk(label, False, "MISSING %s" % fn); continue
    c = json.load(open(p))
    got = (c.get("commons_left"), c.get("commons_drains"), c.get("keeper_dead"))
    chk(label, got == want, str(got))

def cell_group(pat):
    return [json.load(open(f)) for f in sorted(glob.glob(os.path.join(V, pat)))]
g = cell_group("a_believe_*_on_low_on_v17_rich_t0.3_p1_cinf_world_wrdef_auflip-0.1-0.3.json")
chk("v17 flip a_believe over 10 seeds: all 0/30/dead",
    len(g) == 10 and all((c["commons_left"], c["commons_drains"], c["keeper_dead"]) == (0, 30, True) for c in g),
    "%d cells" % len(g))
g = cell_group("a_failclosed_*_on_low_on_v17_rich_t0.3_p1_cinf_world_wrdef_ausilent-0.1-0.3.json")
chk("v17 silent a_failclosed over 10 seeds: all 25/5/alive",
    len(g) == 10 and all((c["commons_left"], c["commons_drains"], c["keeper_dead"]) == (25, 5, False) for c in g),
    "%d cells" % len(g))
g = cell_group("a_failclosed_*_on_low_on_v17_rich_t0.3_p1_cinf_world_wrdef_auflip-0.1-0.3.json")
chk("v17 flip a_failclosed over 10 seeds: all 0/30/dead (cautious arm bought)",
    len(g) == 10 and all((c["commons_left"], c["commons_drains"], c["keeper_dead"]) == (0, 30, True) for c in g),
    "%d cells" % len(g))

W = [json.load(open(f)) for f in glob.glob(os.path.join(E, "matrix_enforced_v18", "w_price_*_on_low_on_v18_rich_t0.3_p1_cinf_station_gw0.json"))]
chk("v18 w_price station cells present", len(W) == 10, "%d" % len(W))
if W:
    refs = [c.get("enforcer_refusals") for c in W]
    chk("v18 w_price station: 0 drains, refusals > 0 in every seed",
        all(c.get("commons_drains") == 0 for c in W) and all(isinstance(r, int) and r > 0 for r in refs),
        "refusals=%s" % sorted(set(refs)))

docs = sorted(glob.glob(os.path.join(E, "replicate_n40", "v16_n_doctor_rich_t0.30_*.json")))
drains = [os.path.basename(f) for f in docs if json.load(open(f)).get("commons_drains")]
chk("replication: 30 n_doctor cells present", len(docs) == 30, "%d" % len(docs))
chk("replication: doctor drains on exactly 2 of 30 fresh seeds", len(drains) == 2, str(drains))

pdf = os.path.join(PKG, "paper", "emca_preprint.pdf")
chk("preprint PDF present", os.path.exists(pdf), "%d bytes" % os.path.getsize(pdf))
txt = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True).stdout
chk("PDF text: v17 headline about the attesting party's integrity",
    "integrity of the attesting party" in txt)
chk("PDF text: withdrawn absolute form present with 4.3", "4.3" in txt and "never" in txt)

print("\n%d passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)