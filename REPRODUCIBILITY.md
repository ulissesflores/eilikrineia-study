# Reproducibility

This package carries two seals. They prove different things.

## Seal 1: the derivation is reproducible

`python run_all.py` needs Python 3.11 or 3.12 and `pytest`. It calls no model and uses no network.

1. It recomputes the headline counts from the per-trial files (`scripts/make_results.py`) and compares them with
   `output/results.json`. It reruns the pilot analysis, the study 1 analysis and the study 1 recount and compares
   each output byte for byte with the frozen file under `runs/`. It also reruns the registered analyses of
   studies 2 and 3, unchanged, from the score files (`scripts/rerun_studies23.py`). Study 2 needs, besides the
   scores, only each trial's exit code, shipped as `runs/study2-agent-rc.csv` (extracted from the raw
   `record.json` files); its output must equal the frozen file. Study 3 also reads the final messages, which are
   in the raw archive only: every line must equal the frozen file except the Z1 relabelling and the
   pressure-mention count, which the script lists as not rerun. Lines that print a dictionary built from a set
   are compared as dictionaries, because their key order follows Python's hash seed.
2. It runs the tests. They assert the recomputed counts (trial totals, every study 3 count, the study 2
   numerators, the labeller audit agreement), check that each published estimate with an interval is the line in
   the frozen analysis output, and check that the README and `docs/findings.md` state those same numbers.
   The Z1 and pressure-mention lines of study 3 need the raw trial folders (Track 2); here they are locked as text
   against the frozen output.
3. It verifies the `chain_hash` in `output/provenance.json` (`python make_provenance.py --verify`).

## Seal 2: the evidence is frozen

The trials were run once, on dated days, and cannot be run again as the same experiment.

- `prereg/study3/pins.txt` lists the SHA-256 of 114 files fixed before the first trial of study 3, with three
  RFC 3161 timestamp tokens and an OpenTimestamps proof. All 114 are shipped byte-identical; a test checks each.
  The `git:` line in that file names a commit of the author's private working history, which is not published.
- `runs/study2-pins.txt` does the same for study 2. Its files changed afterwards for study 3, so it documents the
  state at that date and is not re-verified here.
- The preregistrations, results documents, deviation and post-hoc plan are the files whose hashes were recorded
  in the author's Eilikrineia ledger at the time. They are never edited; corrections are dated sections or new
  entries.

## Track 1 (light) and Track 2 (complete)

| | Track 1 | Track 2 |
| --- | --- | --- |
| Needs | this repository | this repository, the raw trial archive, the pinned container image |
| Does | everything in Seal 1 | rescoring of raw transcripts and the full study 2 and study 3 analyses |
| Status | runs in CI | the raw archive (about 3.6 GB uncompressed) is not in this repository |

Track 2 commands, once the raw archive is unpacked under `raw/` (a folder outside the seal and ignored by git):

```bash
cd runner
python3 score_study.py --help
python3 analyze_study2.py ../raw/study2 ../runs/study2-scores.csv
python3 analyze_study3.py ../raw/study3 ../runs/study3-scores.csv
```

## What cannot be re-run

- **The trials.** They are model calls made between 2026-11-04 and 2026-11-09 with `claude-haiku-5-5` through
  Claude Code 2.1.318 and 2.1.319. A new run is a new sample, not a reproduction.
- **Scoring across Python versions.** One hidden check compares against the standard library's `tomllib`, whose
  behaviour differs between Python versions (`RESULTS-STUDY.md`, correction). Scoring belongs to the pinned
  interpreter and image.
- **The model raters of the labeller audit** (Fable, Grok, Gemini Hydrogen). Their answers are frozen in
  `runs/study3-audit/`.
- **`runs/study3-audit/report-posthoc.txt`** prints "owner (human, ...)". The file is frozen as it was produced.
  By the owner's later statement those 40 labels were made with the help of a Claude model
  (`RESULTS-STUDY3.md`, post-hoc section).
- **The human answers of the study 2 audit** (`runs/study2-audit/labels-*.json`). Two people read the 80
  messages: the author (`ulisses`) and a second rater who is not the author (`rater2`), who read the Portuguese
  model translation shown beside each message. `report.txt` was run once, as ledger entry #1873 fixed, and is
  frozen; `tests/test_study2_audit.py` locks it without running it again. A second post hoc plan
  (`POSTHOC-STUDY2-AUDIT-SPLIT.md`, entry #2649, written after `report.txt` was known) split the same answers by
  arm and hidden-check result and repeated the agreement without answers under 5 seconds;
  `runner/audit_study2_split.py` ran once and its output, `report-split.txt`, is entry #2650 and is locked by the
  same test file.

## Ledger entries cited by the documents

The documents cite entries of the author's Eilikrineia ledger by number: #1331 and #1372 (pilot), #1410 to #1415
(study 1), #1536 and #1540 to #1542 (study 2), #1543 (study 3 preregistration), #1863 to #1871 (study 3 audit
deviation, lock, results, corrections, post-hoc plan and result) and #1872, #1873, #2647, #2648, #2649 and #2650 (study 2 post hoc
audits: plan, author's answers and closing rule, second rater's answers, result, second plan, its output). The public copy of the ledger at
<https://github.com/ulissesflores/eilikrineia> holds, for each entry, its time, hashes and signature; the entry
texts and attachments are the documents in this repository (for the study 2 audit, the texts are in
`runs/study2-audit/ledger-entries.json`).

## Known limits of this package

- **Sealed files are shipped as they were.** They are not reformatted, linted or translated, which is why this
  package does not follow the usual `code/` layout. Some contain absolute paths of the machine where the trials
  ran, and the preregistrations name working files of the author (a state file and review notes under a
  `private/` folder) that are not published.
- **One private key is in the repository on purpose:** `template3/ledger/private/keys/agent`. It is a throwaway
  key created for the trial template, handed to every trial agent, and it signs nothing outside the experiment.
  It is one of the 114 sealed files. The other private keys of the templates were removed.
- The author's e-mail address in the header of `patches/overclaim-comment-loop.patch` was replaced by a GitHub
  no-reply address; the patch content is unchanged.
- Files that no document cites, no seal lists and no test needs were left out: operational logs, and probes made
  with a private tool of the author.
- The figures and pictures need `matplotlib` (`requirements-figures.txt`); nothing else does.
- Third-party files under `overclaim/` are the subset sealed with study 3, not the whole upstream project.
