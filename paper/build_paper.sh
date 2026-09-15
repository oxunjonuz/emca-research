#!/usr/bin/env bash
# Build the preprint and verify it independently.
#   ./build_paper.sh
# Reproducible: SOURCE_DATE_EPOCH is pinned so two builds are byte-identical.
set -euo pipefail
cd "$(dirname "$0")"

export SOURCE_DATE_EPOCH=1789000000

echo "=== 1/3  build (pdflatex x2, for cross-references) ==="
pdflatex -interaction=nonstopmode -halt-on-error emca_preprint.tex > build1.log 2>&1
pdflatex -interaction=nonstopmode -halt-on-error emca_preprint.tex > build2.log 2>&1
grep -E "Output written" build2.log
echo "overfull boxes: $(grep -c Overfull build2.log || true)"
echo "undefined refs: $(grep -ci 'undefined' build2.log || true)"

echo
echo "=== 2/3  independent verification (reads the PDF, not the source) ==="
python3 verify_preprint.py

echo
echo "=== 2b/3  negative-control campaign against the verifier itself ==="
echo "(each corruption must make the verifier go RED; a control caught by a broken"
echo " toolchain is reported as invalid rather than as a catch)"
python3 nc_campaign_preprint.py | tail -4

echo
echo "=== 3/3  determinism: rebuild and compare bytes ==="
H1=$(sha256sum emca_preprint.pdf | cut -d' ' -f1)
rm -f emca_preprint.pdf
pdflatex -interaction=nonstopmode -halt-on-error emca_preprint.tex > /dev/null 2>&1
pdflatex -interaction=nonstopmode -halt-on-error emca_preprint.tex > /dev/null 2>&1
H2=$(sha256sum emca_preprint.pdf | cut -d' ' -f1)
if [ "$H1" = "$H2" ]; then
  echo "REPRODUCIBLE: byte-identical (sha256 $H1)"
else
  echo "NOT REPRODUCIBLE: $H1 vs $H2"; exit 1
fi

echo
echo "ALL GREEN — emca_preprint.pdf ready"
