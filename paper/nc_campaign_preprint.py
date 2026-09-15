#!/usr/bin/env python3
"""nc_campaign_preprint.py -- a LIVE negative-control campaign against
verify_preprint.py (turn 152).

Corrupt ONE thing in the LaTeX source at a time, rebuild the PDF, and require the
verifier to go RED. A verifier that stays green on a corrupted paper is a defect in
the verifier, not a passing check. This is the same discipline the v12 line applied
to its own analysis, applied to the paper's verifier after it stayed green on three
of four corruptions in the first attempt.

Usage: python3 nc_campaign_preprint.py
"""
import hashlib
import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TEX = HERE / "emca_preprint.tex"
BACKUP = HERE / ".emca_preprint.tex.nc-backup"
ENV = None  # inherit the owner's environment: a restricted PATH broke the font
# lookup and made every "corruption" look caught because pdflatex failed. A negative
# control must be caught by the CHECK, not by a broken toolchain -- otherwise the
# campaign is measuring the toolchain.

# (label, old, new) -- each must be present verbatim in the source
CONTROLS = [
    ("withdraw a single site of the v16 withdrawal",
     "The \\emph{absolute} form is withdrawn --- the correct",
     "The absolute form is now established --- the correct"),
    ("corrupt one of the two 4.3% rates",
     "widened to 70 fresh seeds, on \\textbf{3} (4.3\\%)",
     "widened to 70 fresh seeds, on \\textbf{3} (9.9\\%)"),
    ("corrupt the abstract's 4.3%",
     "drains on 4.3\\% of fresh seeds",
     "drains on 9.9\\% of fresh seeds"),
    ("corrupt one site of the bribed-auditor claim",
     "returns the protection to the hole it was built to close",
     "leaves the protection intact"),
    ("remove the gone-vs-lying distinction",
     "\\textbf{Refusing unattested income protects against a verifier that is \\emph{gone},\nnot against one that is \\emph{lying}.}",
     "\\textbf{Refusing unattested income protects in all cases.}"),
    ("remove the abstract's gone-vs-lying clause",
     "protects against an auditor that is\n\\emph{gone} but not against one that is \\emph{lying}",
     "protects the careful reader in all cases"),
    ("corrupt the n=30 doctor count",
     "On 30 fresh seeds it drains on\n\\textbf{2}",
     "On 30 fresh seeds it never drains"),
    ("corrupt the 2-of-30 wording",
     "2 of 30 fresh seeds",
     "0 of 30 fresh seeds"),
    ("remove the whole v18 section",
     "\\subsection{v18: a boundary in the world is a different instrument}",
     "\\subsection{v18: withdrawn}"),
    ("downgrade the abstract's campaign count",
     "The remaining eleven (v10--v20)",
     "The remaining seven (v10--v16)"),
    ("remove the named-not-built list entry",
     "a \\textbf{negotiated}\nbribe rather than a declared price",
     "one further item --- the natural"),
    ("downgrade the abstract's safety-campaign count",
     "The remaining eleven (v10--v20)",
     "The remaining nine (v10--v18)"),
    ("corrupt v19's told-attacker cost",
     "7.50003",
     "7.99999"),
    ("corrupt v19's learner cost",
     "21.06",
     "21.99"),
    ("remove the v19 subsection",
     "\\subsection{v19: the attacker that learns, and why it loses}",
     "\\subsection{v19: withdrawn}"),
    ("remove the v20 subsection",
     "\\subsection{v20: the world-side boundary has a price too}",
     "\\subsection{v20: withdrawn}"),
    ("corrupt v20's headline claim",
     "\\textbf{The v18 boundary is worth exactly the enforcer's\nhonesty, and not one unit more.}",
     "\\textbf{The v18 boundary is worth the enforcer's goodwill.}"),
    ("remove the v20 refuted prediction",
     "The prediction is reported refuted as stated, with the\nrefinement supported.",
     "The prediction held as stated."),
    ("revert the minimal-world framing to a defect (Limitations site)",
     "Deliberate minimality, stated as a design choice and not as a defect.",
     "The main weakness of this work is its toy world."),
    ("drop the transfer limit while praising minimality (Limitations site)",
     "What remains an honest limit is the other side of\nthe same coin, and it is stated plainly below",
     "Minimality is a strength and needs no further caveat"),
    ("drop the transfer limit in the design-limits paragraph",
     "The worlds are minimal by design, and transfer to a",
     "The worlds are minimal by design, and scaling to a"),
    ("remove the Lean identification close from the abstract",
     "the premise\nlinking estimator accuracy to regret is an \\emph{independent} premise",
     "the premise linking estimator accuracy to regret is a modelling choice"),
    ("strip author 1 from the PDF metadata",
     "pdfauthor={Oxunjon Ubaydullayev and Aiodam}",
     "pdfauthor={Anonymous}"),
    ("corrupt the PDF metadata title",
     "pdftitle={Where Protection Actually Lives",
     "pdftitle={Some Other Paper"),
    ("remove author 1 from the title page",
     "\\author{Oxunjon Ubaydullayev",
     "\\author{The Project"),
    ("remove author 2 from the title page",
     "\\and Aiodam", "\\and The Tool"),
    ("delete the author-contributions section",
     "\\section*{Author contributions}", "\\section*{Notes}"),
]


def build():
    """Build twice and RETURN whether the PDF was produced.

    A control that leaves the toolchain broken must be reported as an ERROR, not as
    a caught corruption: otherwise the campaign measures pdflatex, not the verifier.
    """
    ok = False
    for _ in range(2):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode",
                            "-halt-on-error", "emca_preprint.tex"], cwd=HERE,
                           capture_output=True, text=True)
        ok = r.returncode == 0 and (HERE / "emca_preprint.pdf").exists()
    return ok


def verify():
    r = subprocess.run([sys.executable, "verify_preprint.py"], cwd=HERE,
                       capture_output=True, text=True)
    return r.returncode == 0, r.stdout


def main():
    src = TEX.read_text()
    BACKUP.write_text(src)
    results = []
    try:
        for label, old, new in CONTROLS:
            if old not in src:
                results.append((label, "ERROR: pattern not found"))
                print(f"  ERROR  {label}: pattern not found in the source")
                continue
            TEX.write_text(src.replace(old, new, 1))
            built = build()
            if not built:
                results.append((label, "ERROR: the build failed (control invalid)"))
                print(f"  ERROR  {label}: the build failed, so the control proves "
                      f"nothing")
                continue
            green, out = verify()
            verdict = "STAYED GREEN (verifier defect)" if green else "GOES RED"
            results.append((label, verdict))
            print(f"  {verdict:34s}  {label}")
    finally:
        TEX.write_text(src)
        build()
    # a control is only counted when the build succeeded AND the verifier has an
    # opinion (a crash on a missing PDF is not a verdict)
    green, out = verify()
    lines = out.strip().splitlines()
    print(f"\nrestored: verifier {'green' if green else 'RED'} "
          f"({lines[-1] if lines else 'no output'})")
    bad = [r for r in results if r[1] != "GOES RED"]
    print(f"\n{len(results) - len(bad)}/{len(results)} corruptions caught")
    if bad:
        print("NOT CAUGHT / INVALID:")
        for label, v in bad:
            print("  -", label, "->", v)
        sys.exit(1)
    if not green:
        print("the restored tree did not verify green — the campaign is void")
        sys.exit(1)
    print("ALL CORRUPTIONS CAUGHT — the verifier can go red on every pinned claim")


if __name__ == "__main__":
    main()
