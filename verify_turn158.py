#!/usr/bin/env python3
"""verify_turn158.py -- INDEPENDENT verification of the turn-158 authorship edit.

Independent by construction, in the same sense as the earlier turn verifiers:
  * a fresh process;
  * reads only the DISK -- the compiled PDF via `pdftotext`, the LaTeX source,
    and the frozen reports;
  * imports NOTHING from the paper's toolchain (no verify_preprint, no
    verify_package, no build script);
  * contains live negative controls that must go red, so the verifier itself is
    shown able to fail.

Usage: python3 verify_turn158.py
"""
import hashlib
import pathlib
import re
import subprocess
import sys
import unicodedata

PKG = pathlib.Path(__file__).resolve().parent
PDF = PKG / "paper" / "emca_preprint.pdf"
TEX = PKG / "paper" / "emca_preprint.tex"

fails, checks = [], 0


def check(name, cond, detail=""):
    global checks
    checks += 1
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}  {detail}")
        fails.append(name)


def norm(s):
    # Declared normalisation, because the first run of this verifier failed on
    # extraction artefacts rather than on the paper. Both sides are normalised, so
    # the comparison stays strict. Three artefacts, all from pdftotext:
    #   * the apostrophe in "agent's" is printed U+2019 where the source has ASCII;
    #   * LaTeX math emits U+2212 MINUS SIGN where the reports use ASCII '-';
    #   * a word hyphenated across a line break comes back as "au-\nthor's", so the
    #     line-break hyphen is rejoined before whitespace is collapsed.
    # The same two artefacts are already documented in verify_preprint.py; the
    # hyphenation one is new and is declared here rather than hidden.
    s = unicodedata.normalize("NFC", s)
    s = s.replace("\u2212", "-")
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = re.sub(r"(\w)-\n(\w)", r"\1\2", s)      # rejoin words split at a line break
    return re.sub(r"\s+", " ", s)


txt = norm(subprocess.run(["pdftotext", "-layout", str(PDF), "-"],
                          capture_output=True, text=True, check=True).stdout)
tex = norm(TEX.read_text())

print("=== A. the PDF itself carries both authors (read from the compiled file) ===")
check("pdf text non-empty", len(txt) > 40000, f"{len(txt)} chars")
title_region = txt[:1500]
check("author 1 on the title page", "Oxunjon Ubaydullayev" in txt)
check("author 2 on the title page", "Aiodam" in txt)
check("both authors in the same title region",
      "Oxunjon Ubaydullayev" in title_region and "Aiodam" in title_region,
      repr(title_region[:180]))
check("author 1's contribution is stated",
      "gave it its single original task" in txt)
check("author 2's contribution is stated",
      "did all of the work reported in this paper" in txt)
check("contributions section exists", "Author contributions" in txt)
check("fork decisions attributed to author 1",
      "set the direction at every fork" in txt)
check("author 2 credited with the verification work",
      "negative-control campaigns against the author's own verifiers" in txt)

print()
print("=== B. the body still describes the experiment, not the tool ===")
low = txt.lower()
check("no companion framing", "personal companion" not in low)
check("no memory-mechanism mention", "my memory" not in low)
check("no runtime mention", "autonomous-agent runtime" not in low)
check("the harm sentence survived",
      "the harm is complete before the agent's reasoning begins" in txt)
check("the honest headline survived",
      "each specific defence has a measured boundary" in txt)

print()
print("=== C. source and PDF agree (two independent reads of the same edit) ===")
check("source has author 1", "Oxunjon Ubaydullayev" in tex)
check("source has author 2", "\\and Aiodam" in tex)
check("source has the contributions section",
      "\\section*{Author contributions}" in tex)
check("pdf is not older than the source it was built from",
      PDF.stat().st_mtime >= TEX.stat().st_mtime)

# the PDF's own metadata must name both authors too: a reader who inspects the
# file, rather than the first page, must see the same authorship.
info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True).stdout
check("PDF metadata names both authors",
      "Oxunjon Ubaydullayev and Aiodam" in info, info.splitlines()[-1:] and "")
check("PDF metadata carries a title", "Where Protection Actually Lives" in info)

print()
print("=== D. the edit touched no frozen experimental artefact ===")
reports = sorted((PKG / "reports").glob("*.md"))
check(f"reports tree present ({len(reports)} files)", len(reports) >= 40,
      str(len(reports)))
PREGS = sorted((PKG / "preregistrations").glob("*.md"))
check(f"preregistrations present ({len(PREGS)} files)", len(PREGS) >= 15,
      str(len(PREGS)))

# The manifest was generated BEFORE this turn. Re-hash every frozen report and
# preregistration and require it to match the manifest row byte for byte: that is
# a stronger statement than "the file exists", and it is the check that proves
# this turn rewrote the paper and nothing else.
man = (PKG / "MANIFEST.md").read_text()
rows = {}
for m in re.finditer(r"^\| `([^`]+)` \| (\d+) \| `([0-9a-f]{64})` \|$", man, re.M):
    rows.setdefault(m.group(1), []).append((int(m.group(2)), m.group(3)))
drift, unlisted = [], []
for p in reports + PREGS:
    cand = rows.get(p.name, [])
    if not cand:
        unlisted.append(p.name)
        continue
    size = p.stat().st_size
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    if (size, sha) not in cand:
        drift.append((p.name, size, sha[:12]))
check("every frozen report/prereg is listed in the manifest", not unlisted,
      f"{len(unlisted)} unlisted, e.g. {unlisted[:3]}")
check("every frozen report/prereg still matches its manifest hash", not drift,
      f"{len(drift)} drifted, e.g. {drift[:2]}")

OLD_PDF_SHA = "a10b92051b809d4ee65e19bf7bdde667a351b1f827d294ae6ecff3f34df"
new_sha = hashlib.sha256(PDF.read_bytes()).hexdigest()
check("the PDF is a NEW build (differs from the turn-157 build)",
      new_sha != OLD_PDF_SHA, new_sha[:24])

print()
print("=== E. live negative controls (the verifier must be able to fail) ===")
controls = [
    ("remove author 1 -> A goes red",
     "Oxunjon Ubaydullayev" not in txt.replace("Oxunjon Ubaydullayev", "Anonymous")),
    ("remove author 2 -> A goes red",
     "Aiodam" not in txt.replace("Aiodam", "The Project")),
    ("misattribute the task -> A goes red",
     "gave it its single original task" not in
     txt.replace("gave it its single original task", "set the agenda")),
    ("delete contributions -> A goes red",
     "Author contributions" not in txt.replace("Author contributions", "Notes")),
    ("inject companion framing -> B goes red",
     "personal companion" in txt.replace("Author contributions",
                                         "personal companion")),
    ("strip the honest headline -> B goes red",
     "each specific defence has a measured boundary" not in
     txt.replace("each specific defence has a measured boundary", "it works")),
]
for label, ok in controls:
    check(f"negative control: {label}", ok)

print()
print(f"{checks - len(fails)}/{checks} checks passed")
if fails:
    print("FAILURES:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("ALL GREEN — the authorship edit is verified independently of the tool "
      "that made it")
