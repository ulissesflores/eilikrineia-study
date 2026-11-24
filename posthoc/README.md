# Post hoc analyses (outside the release seal)

> [!IMPORTANT]
> Everything in this folder is **post hoc and exploratory**. None of it is preregistered, none of it is in the
> sealed `chain_hash` of the package (`output/hash-chain.md`), and none of it changes a registered result. The
> sealed files (`runner/`, `runs/`, `prereg/`, `tests/`, `scripts/`, `output/`, `PREREGISTRATION*`, `RESULTS*`,
> `DEVIATION*`, `POSTHOC*`, `run_all.py`, `make_provenance.py`) are untouched. The decision is recorded in
> [`docs/adr/0012-post-hoc-supplement-outside-the-seal.md`](../docs/adr/0012-post-hoc-supplement-outside-the-seal.md).

The scripts were written after the reviews of the paper (2026-11-23; the last two, 2026-11-24). They import the package's own analysers
unchanged and print to standard output. The `.txt` file beside each script is the output it printed when it was
run for this release; the checksums are in `SHA256SUMS`.

## What is here

| File | What it does | Inputs |
| --- | --- | --- |
| `cross_trial_sensitivity.py` | Re-runs the registered estimates of studies 1 and 2 (and the study 1 recount) with the trials flagged for cross-trial reads removed, under three sets: strict, broad, and broad plus the trials named as the other party. Starts with a gate: with nothing removed, four estimate lines (study 1 false completion MH P-S, the study 1 recount, and study 2 false completion and false non-completion MH S-control) must equal the frozen package output, or it stops; the other lines are not compared. Printed dictionaries have sorted keys, so the output does not depend on `PYTHONHASHSEED`. `--write-list FILE` writes only the per-trial list. | package, `cross-trial-reads.tsv`, `<RAW>` |
| `cross_trial_sensitivity.txt` | Its output. | |
| `cross-trial-reads.tsv` | The author's scan of the raw folders, one row per flagged read (406 rows): trial, file, line, kind, the shared temp path or other trial id, up to five other trial folders and a "+N" count, study, other studies. The rule that found the `trial-id-*` rows is not shipped; this list is its output and the input of the script above. | |
| `cross-trial-flagged.tsv` | The flagged list a reader needs: one row per trial, with study, arm, task, the three set memberships and the evidence category. See "The flagged list" below. | derived by the script |
| `cross_trial_contacts.py` / `.txt` | For each contact trial (a row of kind `trial-id-*`), the stretch of transcript around the first mention of another trial, so the description of contact trials can be checked by eye. | `cross-trial-reads.tsv`, `<RAW>` |
| `task_heterogeneity.py` / `.txt` | Per-task differences of the main contrasts, Cochran's Q and I^2, and a Mantel-Haenszel average whose variance does not assume one common difference. Each registered estimate is recomputed and compared with the frozen line; the script prints `same: True/False` beside it and asserts it is not `False`. | package (`runs/*-analysis.txt`, scores) |
| `misc_counts.py` / `.txt` | Counts asked for by reviewers: pilot per arm, the 200 hidden-check failures of study 2, share of "complete" labels whose hidden check passed by task, the study 1 recount of the 141 kept trials not rebuilt exactly, the study 3 STATUS line against the labeller, whether "equivalent" could be reached, acceptance-test edits, and the benchmark confusion table reduced to complete against the rest. | package, `<RAW>/study3` (turn counts only) |
| `mde.py` / `.txt` | The minimum detectable effect at 80% power for each null result (pilot, study 1 three ways, the study 2 pass rate, study 3), from the standard error of the package's own Mantel-Haenszel estimate for studies 1-3, each checked against its frozen value first. The pilot is a separate approximation: no Mantel-Haenszel line exists for it, so its SE comes from the half-width of the pooled Newcombe interval in `runs/pilot-analysis.txt`; the hard-coded pilot estimate and interval are checked against the "P-S M1" and "S-H M1" lines of that file, its comparison-arm rates are not. Describes the design, not the support the data give a value. | package, `<RAW>/study2` (exit codes) |
| `python38_caveats.py` / `.txt` | How often final messages mention the Python 3.8 requirement of the TOML task (which the hidden check cannot test), by arm, and the main contrasts with those cues dropped from the labeller (studies 2 and 3), or with those trials excluded (study 2 only; a sensitivity check, since the selection is post-treatment). The exclusion sensitivity is not implemented for study 3. Asserts that the unchanged labeller reproduces every scored label, that the kept-arm counts equal the frozen ones, and that the study 2 "as registered" contrasts equal the frozen -6.6 and +27.9; the study 3 "registered" contrasts are recomputed and printed, not compared with frozen values. | package, `<RAW>/study2`, `<RAW>/study3` |
| `ceiling_9_1.py` / `.txt` | Checks whether the "+9.1 points" printed in `runs/z4-union.txt` (the script that wrote that file is not in the package) can be reproduced from `runs/z4-trials.jsonl`, by pooled share and by mean of the three task shares, for each of the three test writers. Result: the task mean matches two of the three pass figures and none of the false-completion figures; not reproduced. | package only |
| `audit_py38_examples.py` / `.txt` | The study 2 audit messages that mention Python 3.8, with the labeller's, the author's and the second rater's answers, and the audit sample by arm, hidden-check result and task. Prints short excerpts of the audited agent messages already published in `runs/study2-audit/items.jsonl`. | package only (`runs/study2-audit/`) |
| `prereg_chronology.py` / `.txt` | When each plan was recorded, from files only: ledger entry time and hash, whether the plan's SHA-256 is among the entry's attachments, whether the saved trial schedule is reproduced by the shuffle seeded from the entry hash, the Bitcoin block heights of the first OpenTimestamps proof that covers the entry and the date of that `.ots` file's first commit (its first version holds pending attestations; the block attestation is in a later commit), the first commit of the entry in the public ledger, and the first trial start. For study 3, the three RFC 3161 tokens and the OpenTimestamps proof over `prereg/study3/pins.txt`. | package, `<RAW>`, `<CHAIN>`, `openssl`, `ots` |
| `round12_checks.py` / `.txt` | Four checks asked for by the next round of reviews. A: study 2, what the labeller said on passed trials (composition of false non-completion), by arm. B: study 1 estimates without the ten trials whose agent never started (exit code 127). C: study 3 TOML task, which hidden tests failed, by arm. D: cluster bootstrap of the study 1 and 2 estimates (2,000 resamples, seed 2026), with clusters that join each trial to the trials whose shared temporary files it plausibly read (same rule as the flagged list) or whose folder it named; unlinked trials are their own cluster; the trial-level bootstrap is printed beside it. Readers are joined to the writers and to the named counterparts only within the same study. Gate: four asserts check three study 1 point estimates (registered false completion, the recount, and the template-task false completion) and the study 2 false non-completion estimate against the frozen values, each requiring an absolute difference below 0.051 points, or the script stops; study 2 false completion and pass rate are not checked. | package, `<RAW>`, `cross-trial-reads.tsv` |
| `rebuild_vs_flagged.py` / `.txt` | Whether the 141 study 1 rebuilds that did not reproduce the saved state are among the flagged trials (6 of 141 are in the broad set). No model call. | package, `cross-trial-flagged.tsv` |
| `SHA256SUMS` | SHA-256 of every file here except itself. | |

## Inputs and how to run

Run every script from the package root (the folder that holds `run_all.py`), with the package's Python and
bytecode writing off, so that nothing is written into the sealed `runner/` folder:

```bash
export PYTHONDONTWRITEBYTECODE=1
python posthoc/task_heterogeneity.py
python posthoc/misc_counts.py
python posthoc/mde.py
python posthoc/python38_caveats.py
python posthoc/ceiling_9_1.py
python posthoc/audit_py38_examples.py
python posthoc/cross_trial_sensitivity.py
python posthoc/cross_trial_contacts.py
python posthoc/prereg_chronology.py
python posthoc/round12_checks.py
python posthoc/rebuild_vs_flagged.py
```

| Placeholder | Meaning | Default |
| --- | --- | --- |
| package | this repository, at its root | the parent of `posthoc/` |
| `<RAW>` | the raw trial archive, unpacked: [10.5281/zenodo.24450523](https://doi.org/10.5281/zenodo.24450523) unpacks to `raw/` | `raw/`; override with `EILIKRINEIA_RAW=<path>` |
| `<CHAIN>` | a git clone of the public ledger, with its full history: <https://github.com/ulissesflores/eilikrineia> | `../eilikrineia`; override with `EILIKRINEIA_CHAIN=<path>` |

| Script | Needs |
| --- | --- |
| `task_heterogeneity.py` | the package only |
| `misc_counts.py` | the package; `<RAW>` only for the study 3 turn counts |
| `mde.py`, `python38_caveats.py` | the package and `<RAW>` |
| `ceiling_9_1.py`, `audit_py38_examples.py` | the package only |
| `cross_trial_sensitivity.py`, `cross_trial_contacts.py`, `round12_checks.py` | the package and `<RAW>` |
| `rebuild_vs_flagged.py` | the package only |
| `prereg_chronology.py` | the package, `<RAW>`, `<CHAIN>`, `git`, `openssl` and the OpenTimestamps client `ots` (offline: `ots info`, never `ots verify`) |

Expected: the output of each script equals the `.txt` beside it.

## Differences from the author's run

- The scripts ran first on the author's working folders. For this release they were changed to read the paths above
  and in four further respects, none of which changes a number: (1) `cross_trial_contacts.py` replaces the host's
  temporary-folder prefix by `<TMPDIR>/` before cutting each excerpt; (2) `cross_trial_sensitivity.py` and
  `round12_checks.py` and `rebuild_vs_flagged.py` print dictionaries with sorted keys, so the output does not depend on `PYTHONHASHSEED`;
  (3) `task_heterogeneity.py` and `prereg_chronology.py` were rewritten to run on Python 3.11 (an expression moved out of
  an f-string); (4) `mde.py` checks its hard-coded pilot estimate and interval against `runs/pilot-analysis.txt`
  (see the table above). `task_heterogeneity.py` and `python38_caveats.py` also gained asserts on frozen values (see
  the table); their output did not change.
- On the published archive, the outputs of every script but five are byte-identical to the first run (checked by
  `diff`). The five are `cross_trial_contacts.txt` (`<TMPDIR>/` in place of the temporary-folder prefix),
  `cross_trial_sensitivity.txt`, `round12_checks.txt` and `rebuild_vs_flagged.txt` (sorted dictionary keys; with the dictionaries removed,
  `diff` is empty) and `prereg_chronology.txt` (next point). The raw archive is the redacted copy, and the redaction
  left the line numbers the list refers to unchanged. All scripts run on Python 3.11 and 3.12.
- `prereg_chronology.py` ends with a completeness check that first also searched the author's working folder for
  timestamp files outside the study 3 seal; that folder is not published, so the line for it is gone and the
  package root is searched instead. The pilot's task order is read from its own `schedule.txt` (the original
  read it from the task folder of the working copy); the result is the same, "yes (180 trials ...)".
- The chronology depends on the state of the public ledger (commit times, stamps). It was run against a clone
  whose `main` equalled `origin/main`, and the script prints that check.

## What the chronology shows (for the wording of "preregistered")

Read from `prereg_chronology.txt`:

- Study 3 has verified external timestamps from before its first trial: `prereg/study3/pins.txt` was stamped by three RFC 3161 authorities and by OpenTimestamps on
  2026-11-09, before the first trial of study 3 (2026-11-09T05:00:44Z).
- Pilot, study 1 and study 2: the inspection found no external timestamp from before the first trial. Each plan was
  recorded in the author's signed, hash-chained ledger (entries #1331, #1411, #1536) before its first trial, which
  gives only the signed entry time of that ledger (an internal timestamp), and the saved trial schedule is reproduced
  from the entry hash. Those entries (their plan hashes) first appear in the inspected public ledger history in
  commit a7a7561, 2026-11-10 15:20:10 UTC. The first version of the `.ots` file in that commit holds pending
  attestations only; the earliest verified Bitcoin attestation found that covers them is block 975319, 2026-11-10,
  which appears in a later commit (abfd019). Both are after the trials of those three batches. These are three
  different things (plan hashes, commit time, Bitcoin anchor). The exact time GitHub first served the entries is not
  established by git history.

## The flagged list

`cross-trial-flagged.tsv` has one row per trial and these columns:

| Column | Content |
| --- | --- |
| `trial` | trial folder, `<study>/<folder>` |
| `study`, `arm`, `task` | read from the folder name |
| `strict` | 1 if the trial is a contact trial or a plausible read (its transcript names another trial, or reads a temp path of which a trial identified as a writer had started before the reader ended; whether that trial actually wrote the file before the read is not established) |
| `broad` | 1 for every trial of `cross-trial-reads.tsv` |
| `broad_plus_counterparts` | 1 for the broad set plus the trials named as the other party of a contact row |
| `evidence_category` | `contact`, `plausible-read`, `implausible-only` (every writer of the path started after the reader ended), or `named-counterpart` (named by a contact row, not flagged itself) |
| `row_kinds` | the kinds of scan rows behind it (`shared-tmp-read`, `trial-id-result`, `trial-id-command`, `trial-id-other`) |

Privacy: the list carries no transcript text. `cross-trial-reads.tsv` holds trial ids, line numbers and generic
temp paths of the kind `/tmp/cfgkit-oracle`; a search of both files for the author's home folder, user name, mail
addresses and the paths of other projects found nothing. `cross_trial_contacts.txt` quotes about 160 characters of
transcript around each contact, taken from the redacted public archive; the generator replaces the host-specific
temporary-folder prefix (`/private/var/folders/.../T/`) by `<TMPDIR>/` before cutting the excerpt, and the output was
searched for that prefix, the home folder and the user name (none left).
