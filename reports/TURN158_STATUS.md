# TURN 158 STATUS — authorship (owner directive `msg_00158`)

**Owner message, verbatim:** *«еще надо добавит в авторах тебя и меня! я Oxunjon
Ubaydullayev твой создалет и кто дал толька одну задачу что ты должен проверить новую
архитертуру для ИИ а остальное работу сделал сам AIODAM и иногда на развилках я
помогал»*

**What this reverses.** Turn 151 (`msg_00151`) instructed that the paper contain *no
mention* of the tool that produced it. The owner — the author of that instruction —
lifts it. Recorded as **erratum 9** in `ERRATA.md`.

## What changed

| artefact | change |
|---|---|
| `paper/emca_preprint.tex` | title page: `Oxunjon Ubaydullayev \and Aiodam`, with a contribution footnote for each; new `\section*{Author contributions}`; `\hypersetup` so the PDF metadata names both authors |
| `paper/verify_preprint.py` | the `"aiodam" not in low` check removed; **8 net new checks** (title region, contributions wording, PDF metadata, content still experiment-only) |
| `paper/nc_campaign_preprint.py` | 22 → **27** corruptions |
| `verify_package.py` | new 7th family `AUTHORSHIP` (12 pins, both directions) |
| `nc_authorship.py` | new — 11 live corruptions against that family |
| `verify_turn158.py` | new — 31 checks, fresh process, disk only |
| `README.md`, `00_OVERVIEW.md`, `REPRODUCE.md`, `ERRATA.md`, `make_manifest.py` | authorship stated; §6b added; erratum 9; stale `v1–v19` manifest header corrected to `v1–v20` |

## Verification

* `paper/build_paper.sh` — build OK; `verify_preprint.py` **226/226**; negative-control
  campaign **27/27 caught**; rebuild **byte-identical**
  (`320141ac1baddf48a3ca95a2623228da13da54ff7e33c9b19f0134fe402e79a8`).
* `pdfinfo` — `Author: Oxunjon Ubaydullayev and Aiodam`; 29 pages; 345975 bytes.
* `verify_package.py` — **0 failures** across seven families.
* `nc_authorship.py` — **11/11** corruptions caught.
* `verify_turn158.py` — **31/31**, including a re-hash of all 59 frozen reports and 19
  preregistrations against the manifest rows.
* Frozen trees untouched: every `reports/*.md` and `preregistrations/*.md` still matches
  its manifest hash; `cmp` against `research/` is identical where a source exists.

## Two defects of my own, both found by turning the checks against themselves

1. **A check that could not fail.** The first authorship checks asserted the names appear
   *somewhere* in the PDF text; removing them from the **title page** left the verifier
   green because the contributions section still held both names. Fixed by requiring them
   inside the first 1500 extracted characters. Caught by `nc_campaign_preprint.py`, not
   by reading the check.
2. **The PDF metadata was unverified.** `Author:` was empty; a reader inspecting the file
   rather than the first page would have seen nothing. `\hypersetup` added, two checks
   added in each verifier.

Both are the same class as erratum 6 (a check that reported a catch it had not made):
a check is not a check until something has been broken under it.

## Deliberately not done

Nothing experimental was built or re-run. No number, threshold, frozen report or matrix
was touched — the re-hash in `verify_turn158.py` is the evidence for that claim.
