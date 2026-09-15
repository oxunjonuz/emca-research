#!/usr/bin/env python3
"""Live negative controls against the AUTHORSHIP family of verify_package.py
(turn 158). Corrupt one pinned element at a time in a COPY of the package and
require the verifier to go RED. A control that leaves the verifier green means
the check cannot fail.

Usage: python3 nc_authorship.py        (from the package root)

The copy is made with the heavy trees (`evidence/`, MANIFEST.md) excluded: the
authorship family reads only the paper source, README, 00_OVERVIEW and ERRATA,
so copying 694 MiB would measure nothing extra. That exclusion is declared here
rather than hidden."""
import pathlib, shutil, subprocess, sys, tempfile

PKG = pathlib.Path("/work/Shopify/audit-work/agent_arch/PUBLICATION_V1_V16")

CONTROLS = [
    ("remove author 1 from the title page", "paper/emca_preprint.tex",
     "\\author{Oxunjon Ubaydullayev", "\\author{Anonymous"),
    ("remove author 2 from the title page", "paper/emca_preprint.tex",
     "\\and Aiodam", "\\and The Project"),
    ("delete the contributions section", "paper/emca_preprint.tex",
     "\\section*{Author contributions}", "\\section*{Unused heading}"),
    ("misattribute the original task", "paper/emca_preprint.tex",
     "gave it its single\noriginal task", "set the research agenda"),
    ("misattribute the work to author 1", "paper/emca_preprint.tex",
     "did all of the work reported in this paper", "contributed to the work"),
    ("drop the fork-decision attribution", "paper/emca_preprint.tex",
     "set the direction at every fork", "was involved"),
    ("remove erratum 9", "ERRATA.md", "## Erratum 9 (turn 158)", "## Erratum 9b"),
    ("un-attribute the reversal", "ERRATA.md", "msg_00158", "an earlier note"),
    ("remove the authors from README", "README.md",
     "(Oxunjon Ubaydullayev, Aiodam)", "(the authors)"),
    ("remove the authors from the overview", "00_OVERVIEW.md",
     "Oxunjon Ubaydullayev", "the first author"),
    ("sneak a companion framing into the paper", "paper/emca_preprint.tex",
     "\\section*{Author contributions}",
     "\\section*{Author contributions}\n\\noindent This work was done by a personal companion."),
]

def main():
    results = []
    for label, rel, old, new in CONTROLS:
        with tempfile.TemporaryDirectory() as td:
            work = pathlib.Path(td) / "pkg"
            shutil.copytree(PKG, work, symlinks=True,
                            ignore=shutil.ignore_patterns("evidence", "MANIFEST.md"))
            f = work / rel
            src = f.read_text()
            if old not in src:
                results.append((label, "ERROR: pattern not found"))
                print(f"  ERROR  {label}: pattern not found")
                continue
            f.write_text(src.replace(old, new, 1))
            r = subprocess.run([sys.executable, "verify_package.py"], cwd=work,
                               capture_output=True, text=True)
            red = r.returncode != 0 and "AUTHORSHIP" in r.stdout
            results.append((label, "GOES RED" if red else
                            f"STAYED GREEN (rc={r.returncode})"))
            print(f"  {'GOES RED' if red else 'STAYED GREEN':14s}  {label}")
    bad = [x for x in results if x[1] != "GOES RED"]
    print(f"\n{len(results)-len(bad)}/{len(results)} corruptions caught")
    if bad:
        for label, v in bad:
            print("  -", label, "->", v)
        sys.exit(1)

if __name__ == "__main__":
    main()
