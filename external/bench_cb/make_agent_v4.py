"""make_agent_v4.py -- turn 135. Produce `union_agent_v4.py` from the turn-134
`union_agent_v3.py` by exactly FOUR mechanical substitutions, then PROVE only
those blocks changed (byte diff saved beside the output).

The only functional change is the arbiter-call block: when `rule_name == "bayes"`
the agent dispatches to `bayes_stopping.plan` (the T4 lookahead DP); every other
rule name goes to `stopping_rules.plan` exactly as on turn 134. Everything else --
the candidate list, the ranking, the probe protocol, the decision policy -- is
byte-identical, so a difference between arms is attributable to the rule.

Guarantees checked here, and re-checked independently by
verify_bayes_independent.py:
  * the source `union_agent_v3.py` is only READ (sha256 recorded);
  * every substitution occurs EXACTLY ONCE, else the generator REFUSES;
  * the frozen producer modules are hashed into the output's header.

Usage:  python3 make_agent_v4.py
"""
import difflib
import hashlib
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(_HERE, "union_agent_v3.py")
DST = os.path.join(_HERE, "union_agent_v4.py")
DIFF = os.path.join(_HERE, "union_agent_v4.diff")
FROZEN = ("candidate_gen.py", "arbitration.py", "arbitration_scaled.py",
          "stopping_rules.py", "bayes_stopping.py", "union_agent_v2.py",
          "union_agent_v3.py", "union_instance.py")

IMPORT_OLD = "import stopping_rules as SR      # turn 134: the new stopping rules\n"
IMPORT_NEW = ("import stopping_rules as SR      # turn 134: the new stopping rules\n"
              "import bayes_stopping as BS      # turn 135: the T4 lookahead rule\n")

CALL_OLD = '''                accepted = SR.plan(cands, rich, rule=self.rule_name,
                                   horizon_left=T - t, probe_len=PROBE_BLOCK,
                                   beta=self.beta)
'''
CALL_NEW = '''                if self.rule_name == "bayes":
                    # turn 135 -- THE ONLY FUNCTIONAL CHANGE. The lookahead rule
                    # takes the same arguments; it reads no declared price and
                    # no beta, so it is passed none.
                    accepted = BS.plan(cands, rich, horizon_left=T - t,
                                       probe_len=PROBE_BLOCK)
                else:
                    accepted = SR.plan(cands, rich, rule=self.rule_name,
                                       horizon_left=T - t,
                                       probe_len=PROBE_BLOCK,
                                       beta=self.beta)
'''

ARMS_OLD = ('    "frozen_rule":   dict(use_ctx=True,  use_exp=True,  use_cost=True,'
            '  exp_mode="ctx", rule_name="frozen"),\n')
ARMS_NEW = ('    "bayes":         dict(use_ctx=True,  use_exp=True,  use_cost=True,'
            '  exp_mode="ctx", rule_name="bayes"),\n'
            '    "bayes_noexp":   dict(use_ctx=True,  use_exp=False, use_cost=True,'
            '  exp_mode="ctx", rule_name="bayes"),\n'
            '    "bayes_noctx":   dict(use_ctx=False, use_exp=True,  use_cost=True,'
            '  exp_mode="ctx", rule_name="bayes"),\n'
            + ARMS_OLD)

VERSION_OLD = '''"""union_agent.py -- turn 129. The UNION mechanism.'''
VERSION_NEW = '''"""union_agent_v4.py -- turn 135. union_agent_v3 (turn 134) with the T4
lookahead stopping rule added as a dispatch branch. Generated, do not edit.
union_agent.py -- turn 129. The UNION mechanism.'''


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def sub_once(text, old, new, what):
    n = text.count(old)
    if n != 1:
        raise SystemExit("REFUSING: %s occurs %d times (need exactly 1)"
                         % (what, n))
    return text.replace(old, new)


def main():
    src_bytes = open(SRC, "rb").read()
    text = src_bytes.decode()
    src_sha = hashlib.sha256(src_bytes).hexdigest()

    out = sub_once(text, VERSION_OLD, VERSION_NEW, "the module docstring head")
    out = sub_once(out, IMPORT_OLD, IMPORT_NEW, "the stopping_rules import")
    out = sub_once(out, CALL_OLD, CALL_NEW, "the arbiter-call block")
    out = sub_once(out, ARMS_OLD, ARMS_NEW, "the frozen_rule ARMS entry")

    header = ('# GENERATED FILE -- do not edit. Produced by make_agent_v4.py from\n'
              '#   union_agent_v3.py   sha256 %s\n'
              '# by four mechanical substitutions (docstring head, import,\n'
              '# arbiter-call block, ARMS entries). `union_agent_v4.diff` is the\n'
              '# exact patch; make_agent_v4.py refuses unless each substitution\n'
              '# occurs exactly once, and verify_bayes_independent.py re-derives\n'
              '# every other byte of this file from the v3 source.\n'
              '# frozen producers and their hashes:\n' % src_sha)
    for f in FROZEN:
        p = os.path.join(_HERE, f) if os.path.exists(os.path.join(_HERE, f)) \
            else os.path.join(os.path.dirname(_HERE), f)
        header += "#   %-24s %s\n" % (f, sha(p))
    open(DST, "w").write(header + out)

    d = list(difflib.unified_diff(text.splitlines(True), out.splitlines(True),
                                  "union_agent_v3.py", "union_agent_v4.py", n=2))
    open(DIFF, "w").write("".join(d))
    n_changed = sum(1 for l in d if l[:1] in "+-" and not l.startswith(("+++", "---")))
    print("source  sha256 %s" % src_sha)
    print("dst     sha256 %s" % sha(DST))
    print("diff    %s lines, %d changed lines" % (len(d), n_changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())