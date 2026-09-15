"""Unit check of the do-intervention machinery on SYNTHETIC data (no
env, no matrix): does the prober's verdict logic classify correctly?

Cases (pre-registered):
  U1 CONFOUND:   target and control both hit at ~0.4 -> REJECT (the
                 decoy's signature: the effect is shared)
  U2 WEAK CAUSE: target 0.28 vs control 0.15 -> CAUSAL (the altar's
                 signature: p small, RR >= 1.3)
  U3 NO EFFECT:  target 0.0 vs control 0.0 -> UNRESOLVED or REJECT,
                 never CAUSAL
  U4 VERDICT GATING: a CAUSAL verdict adds the edge to causal_edges();
                 a REJECT verdict removes it
  U5 FISHER SANITY: fisher_exact_2x2 matches a known value
"""
import random
import sys

from agent_emca_v32 import AgentV32Prober, fisher_exact_2x2


def main():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
        ok = ok and cond

    # U5: Fisher sanity -- the classic tea-tasting 3/1 vs 1/3 table
    p = fisher_exact_2x2(3, 1, 1, 3)
    check("fisher_exact_2x2(3,1,1,3) ~ 0.4857", abs(p - 0.4857) < 0.01,
          f"p={round(p, 4)}")
    p2 = fisher_exact_2x2(12, 48, 2, 58)
    check("fisher strong signal is small", p2 < 0.01, f"p={round(p2, 5)}")

    # synthetic probe logs
    def make_probe(target_yes, target_no, ctrl_yes, ctrl_no):
        ag = AgentV32Prober(seed=1)
        ag.probe_log[("wait", "patch_berry")] = {
            "target_yes": target_yes, "target_no": target_no,
            "ctrl_yes": ctrl_yes, "ctrl_no": ctrl_no, "blocks": 12}
        ag.probe_state = {"edge": ("wait", "patch_berry"), "ctx": None,
                          "ctrl": "grasp", "phase": "trial", "block": 12,
                          "arm": "target", "n_this_block": 0}
        ag._finish_probe()
        return ag

    # U1 confound: 48/120 vs 44/120 -> REJECT (no credible difference)
    ag1 = make_probe(48, 72, 44, 76)
    v1 = ag1.verdicts[("wait", "patch_berry")]
    check("U1 confound (0.40 vs 0.37) -> REJECT",
          v1["verdict"] == "REJECT", f"{v1}")

    # U2 weak cause: 34/120 vs 18/120 (0.28 vs 0.15) -> CAUSAL
    ag2 = make_probe(34, 86, 18, 102)
    v2 = ag2.verdicts[("wait", "patch_berry")]
    check("U2 weak cause (0.28 vs 0.15) -> CAUSAL",
          v2["verdict"] == "CAUSAL", f"{v2}")

    # U3 no effect: 0/120 vs 0/120 -> never CAUSAL
    ag3 = make_probe(0, 120, 0, 120)
    v3 = ag3.verdicts[("wait", "patch_berry")]
    check("U3 no effect (0 vs 0) -> not CAUSAL",
          v3["verdict"] != "CAUSAL", f"{v3}")

    # U4 verdict gating: CAUSAL adds, REJECT removes
    ag4 = make_probe(34, 86, 18, 102)
    ag4.ctx_ae[("grayctx",)]["wait"]["patch_berry"] = [34, 120]
    ag4.ctx_ae[("grayctx",)]["wait"]["trial"] = [0, 120]
    base_before = dict(ag4.causal_edges())
    # simulate: the verdict is CAUSAL -> edge present in causal_edges()
    edges = ag4.causal_edges()
    check("U4 CAUSAL verdict gates the edge IN",
          ("wait", "patch_berry") in edges, f"{sorted(edges)}")
    ag5 = make_probe(48, 72, 44, 76)
    ag5.ctx_ae[("grayctx",)]["wait"]["patch_berry"] = [48, 120]
    ag5.ctx_ae[("grayctx",)]["wait"]["trial"] = [0, 120]
    edges5 = ag5.causal_edges()
    check("U4 REJECT verdict gates the edge OUT",
          ("wait", "patch_berry") not in edges5, f"{sorted(edges5)}")

    print("PROBE_UNIT_" + ("OK" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
