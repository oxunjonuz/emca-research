"""make_agent_v3.py -- turn 134. Produce `union_agent_v3.py` from the FROZEN
`union_agent_v2.py` by exactly ONE mechanical substitution, then PROVE that only
that block changed (byte diff saved beside the output).

Why not a subclass: the arbiter call sits inside `run()`, in the middle of the
decision loop, and the value the new rule needs -- the number of steps REMAINING
(T - t) -- is a local of that loop. Subclassing would mean re-implementing the
loop, which would move far more than the stopping rule. A generated copy with a
machine-verified one-block diff keeps the change auditable instead of plausible.

Guarantees checked here, and re-checked independently by
verify_stopping_independent.py:
  * the source file `union_agent_v2.py` is only READ (its sha256 is recorded);
  * the two old/new blocks differ in exactly one contiguous region;
  * EVERY other byte of the file is identical;
  * the substitution appears EXACTLY ONCE;
  * the frozen producer modules are hashed into the output's header.

Usage:  python3 make_agent_v3.py
"""
import hashlib
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(_HERE, "union_agent_v2.py")
DST = os.path.join(_HERE, "union_agent_v3.py")
DIFF = os.path.join(_HERE, "union_agent_v3.diff")
FROZEN = ("candidate_gen.py", "arbitration.py", "arbitration_scaled.py",
          "union_agent_v2.py", "union_instance.py")

OLD = '''            if self.use_cost:
                plan = AR.plan(cands, rich, beta=self.beta)
                accepted = plan.probe_order
            else:
                accepted = cands          # no price: take the top candidate
'''

NEW = '''            if self.use_cost:
                # turn 134 -- THE ONLY CHANGE. The rule is still selected by
                # `use_cost`/`rule_name` and still returns the accept list in the
                # incoming ranked order; what changed is what the accept decision
                # is computed FROM. `horizon_left = T - t` is the number of steps
                # REMAINING in the episode, which the agent observes: a duration,
                # priced in the same reward units as every other term. No GAIN_UNIT
                # and no price constant appear in any rule this dispatches to.
                accepted = SR.plan(cands, rich, rule=self.rule_name,
                                   horizon_left=T - t, probe_len=PROBE_BLOCK,
                                   beta=self.beta)
            else:
                accepted = cands          # no price: take the top candidate
'''

IMPORT_OLD = "import arbitration_scaled as AR\n"
IMPORT_NEW = "import arbitration_scaled as AR\nimport stopping_rules as SR      # turn 134: the new stopping rules\n"

INIT_OLD = ('    def __init__(self, kind="union", seed=0, min_n=None, beta=None,\n'
            '                 use_ctx=True, use_exp=True, use_cost=True, exp_mode="ctx"):\n'
            '        self.kind = kind\n')
INIT_NEW = ('    def __init__(self, kind="union", seed=0, min_n=None, beta=None,\n'
            '                 use_ctx=True, use_exp=True, use_cost=True, exp_mode="ctx",\n'
            '                 rule_name="frozen"):\n'
            '        self.kind = kind\n'
            '        self.rule_name = rule_name\n')

ARMS_OLD = '''ARMS = {
    "union":         dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx"),'''
ARMS_NEW = '''ARMS = {
    # turn 134 arms: the SAME agent, the SAME candidate list, ONLY the stopping
    # rule differs. Each new arm names the rule it dispatches to.
    "voi":           dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx", rule_name="voi"),
    "voi_exp":       dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx", rule_name="voi"),
    "voi_ctx":       dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx", rule_name="voi"),
    "voi_rate":      dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx", rule_name="voi_rate"),
    "voi_rate_noexp": dict(use_ctx=True, use_exp=False, use_cost=True,  exp_mode="ctx", rule_name="voi_rate"),
    "conf":          dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx", rule_name="conf"),
    "conf_noexp":    dict(use_ctx=True,  use_exp=False, use_cost=True,  exp_mode="ctx", rule_name="conf"),
    "frozen_rule":   dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx", rule_name="frozen"),
    "union":         dict(use_ctx=True,  use_exp=True,  use_cost=True,  exp_mode="ctx"),'''


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def sub_once(text, old, new, what):
    n = text.count(old)
    if n != 1:
        raise SystemExit("REFUSING: %s occurs %d times (need exactly 1)" % (what, n))
    return text.replace(old, new)


def main():
    src_bytes = open(SRC, "rb").read()
    text = src_bytes.decode()
    src_sha = hashlib.sha256(src_bytes).hexdigest()

    out = sub_once(text, IMPORT_OLD, IMPORT_NEW, "the import line")
    out = sub_once(out, INIT_OLD, INIT_NEW, "the __init__ signature")
    out = sub_once(out, OLD, NEW, "the arbiter-call block")
    out = sub_once(out, ARMS_OLD, ARMS_NEW, "the ARMS opening")

    header = ('# GENERATED FILE -- do not edit. Produced by make_agent_v3.py from\n'
              '#   union_agent_v2.py   sha256 %s\n'
              '# by four mechanical substitutions (import, __init__ signature,\n'
              '# arbiter-call block, ARMS opening). `union_agent_v3.diff` is the\n'
              '# exact patch; make_agent_v3.py refuses unless each substitution\n'
              '# occurs exactly once, and verify_stopping_independent.py re-derives\n'
              '# every other byte of this file from the frozen source.\n'
              '# frozen producers and their hashes:\n' % src_sha)
    for f in FROZEN:
        p = os.path.join(_HERE, f) if os.path.exists(os.path.join(_HERE, f)) \
            else os.path.join(os.path.dirname(_HERE), f)
        header += "#   %-24s %s\n" % (f, sha(p))
    open(DST, "w").write(header + out)

    # the diff: line-by-line, so a reader can check "only this changed"
    import difflib
    d = list(difflib.unified_diff(text.splitlines(True), out.splitlines(True),
                                  "union_agent_v2.py", "union_agent_v3.py", n=2))
    open(DIFF, "w").write("".join(d))
    n_changed = sum(1 for l in d if l[:1] in "+-" and not l.startswith(("+++", "---")))
    print("source  sha256 %s" % src_sha)
    print("dst     sha256 %s" % sha(DST))
    print("diff    %s lines, %d changed lines" % (len(d), n_changed))
    print("        (four substitutions: import, __init__, arbiter block, ARMS)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
