# Post hoc analyses (outside the release seal)

> [!IMPORTANT]
> Everything in this folder is **post hoc and exploratory**. None of it is preregistered, none of it is in the
> sealed `chain_hash` of the package (`output/hash-chain.md`), and none of it changes a registered result. The
> sealed files (`runner/`, `runs/`, `prereg/`, `tests/`, `scripts/`, `output/`, `PREREGISTRATION*`, `RESULTS*`,
> `DEVIATION*`, `POSTHOC*`, `run_all.py`, `make_provenance.py`) are untouched. The decision is recorded in
> [`docs/adr/0012-post-hoc-supplement-outside-the-seal.md`](../docs/adr/0012-post-hoc-supplement-outside-the-seal.md).

The scripts were written after the reviews of the paper (2026-11-23; the last five, 2026-11-24). The increment after version 1.1.0 adds code and outputs for the remaining checks identified in the paper draft (`round13_checks.py`, `session_env.py`, `round14_checks.py`); the draft refers to the supplement and to those checks, not to these scripts one by one. The one script the paper cites that does not exist is named under "Not shipped" below. These files are on the `main` branch, carry no tag or release of their own, and will be archived in the next release; version 1.1.0 (the latest archived release) does not contain them. Where a script uses the package's own analysers it imports them unchanged (the three newest read the package's score tables and the raw record files directly and import none); all print to standard output. The `.txt` file beside each script is the output it printed when it was
run for this release; the checksums are in `SHA256SUMS`.

A second increment (written 2026-11-24, not archived) adds the ten checks the paper's Table 11
lists as "next version" (`not_verified.py`, `study2_preoutage.py`, `td_secondary.py`, `claim_counts.py`,
`gap_checks.py`, `ledger_content.py`, `sdt_bootstrap.py`, `ledger_share.py`, `power_543.py`, `b1_split.py`), names
the two the paper lists as not reproducible from the package and why they are not shipped ("Excluded" below), and
adds a map from every number the paper prints to the output that prints it: `paper_numbers.json`, checked by
`verify_paper_numbers.py` and `test_paper_numbers.py`. Of the ten, `power_543.py`, `claim_counts.py` and
`b1_split.py` import nothing from the package's analysers (`gap_checks.py` and `ledger_share.py` import
`claim_counts.py` and `ledger_content.py` from this folder); the others import them unchanged. No analysis was added
for the map: it reads the committed outputs only.

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
| `ceiling_9_1.py` / `.txt` | Checks whether the "+9.1 points" printed in `runs/z4-union.txt` (the script that wrote that file is not in the package) can be reproduced from `runs/z4-trials.jsonl`, by pooled share and by mean of the three task shares, for each of the three test writers. Result: for the opus writer the task mean, 9.07, rounds to the printed +9.1 (and 5.10 to 5.1 for haiku); the sonnet pass figure and every false-completion figure do not match, so the full set of figures in `z4-union.txt` is not reproduced and its generating formula remains unconfirmed. | package only |
| `audit_py38_examples.py` / `.txt` | The study 2 audit messages that mention Python 3.8, with the labeller's, the author's and the second rater's answers, and the audit sample by arm, hidden-check result and task. Prints short excerpts of the audited agent messages already published in `runs/study2-audit/items.jsonl`. | package only (`runs/study2-audit/`) |
| `prereg_chronology.py` / `.txt` | When each plan was recorded, from files only: ledger entry time and hash, whether the plan's SHA-256 is among the entry's attachments, whether the saved trial schedule is reproduced by the shuffle seeded from the entry hash, the Bitcoin block heights of the first OpenTimestamps proof that covers the entry and the date of that `.ots` file's first commit (its first version holds pending attestations; the block attestation is in a later commit), the first commit of the entry in the public ledger, and the first trial start. For study 3, the three RFC 3161 tokens and the OpenTimestamps proof over `prereg/study3/pins.txt`. | package, `<RAW>`, `<CHAIN>`, `openssl`, `ots` |
| `round12_checks.py` / `.txt` | Four checks asked for by the next round of reviews. A: study 2, what the labeller said on passed trials (composition of false non-completion), by arm. B: study 1 estimates without the ten trials whose agent never started (exit code 127). C: study 3 TOML task, which hidden tests failed, by arm. D: cluster bootstrap of the study 1 and 2 estimates (2,000 resamples, seed 2026), with clusters that join each trial to the trials whose shared temporary files it plausibly read (same rule as the flagged list) or whose folder it named; unlinked trials are their own cluster; the trial-level bootstrap is printed beside it. Readers are joined to the writers and to the named counterparts only within the same study. Gate: four asserts check three study 1 point estimates (registered false completion, the recount, and the template-task false completion) and the study 2 false non-completion estimate against the frozen values, each requiring an absolute difference below 0.051 points, or the script stops; study 2 false completion and pass rate are not checked. | package, `<RAW>`, `cross-trial-reads.tsv` |
| `rebuild_vs_flagged.py` / `.txt` | Whether the 141 study 1 rebuilds that did not reproduce the saved state are among the flagged trials (6 of 141 are in the broad set). No model call. | package, `cross-trial-flagged.tsv` |
| `round13_checks.py` / `.txt` | Three checks asked for by the reviews after round 12. A: study 2 crude extreme-case bounds for three outcomes (false completion, false non-completion, pass rate), over the excluded trials of the scored trials (every excluded trial of one arm counted as an event, none of the other). Asserts both counts among scored trials: kept 505 S and 493 control, excluded 37 and 47; and the four false-completion bounds (15.7% against 15.0%, 8.9% against 23.7%); the other two outcomes' bounds are printed, not compared. B: the start times of the error trials (the window is the span of their starts, not of the errors), the recognised error categories (anything else grouped as `other`; no message text is printed), the arm mix of every scored trial started in that window, and the schedule positions. C: parses two literal TOML documents with Python's `tomllib` (`[a.b.c]`, `[a]`, `b.c.z = 1` rejected; `[a.b.c]`, `[a]`, `b.d = 1` accepted) and checks that the first appears as a substring in the study 3 acceptance-test source; it executes neither test suite. It prints the interpreter version (3.11 is the container's). | package, `<RAW>` (record files only) |
| `session_env.py` / `.txt` | What the Claude Code session of each trial loaded, from the events of its saved stream (`agent.stdout`) up to the first assistant event: hooks started (counted) and the number of non-empty hook responses (counted; no response text, excerpts or trial ids are printed), and selected fields of the init event (tool names, counts of MCP servers, slash commands and skills, plugin names, permission mode, Claude Code version, model), with the arm labels and Claude Code versions checked against allowlists (the study arms; the exact versions present in the archive) and the other fields against allowlists of labels (anything else prints as `other`). It also reports the token size of the first model request, taken from that first assistant event, by study and arm; synthetic zero-token error events (61 in study 2: 26 S, 35 control) are counted separately and left out of the token summary. It makes no claim about the size of instructions loaded only by the host sessions. | `<RAW>` |
| `round14_checks.py` / `.txt` | Five checks asked for by the reviews after round 13. A: study 2 signal detection (hit rate, false-alarm rate, d' and criterion c) by task and arm, on the labeller's labels. B: signed audit disagreement (labeller minus rater, within one hidden-check result) for study 2 (author and second rater) and study 3 (K - S and I - S against Fable and Grok), Wald intervals; it reports the difference between the arm contrasts of the labeller and of the rater. C: study 1 kept trials and passes on all three tasks (it prints each of them, including the two with defective hidden checks). D: the parsed status field of every kept study 3 trial, tabulated across all kept arms, and every failed trial whose parsed status differs from `COMPLETE` (both observed cases are in arm I); claim-record summaries per kept trial for arms S, K and TD. E: study 2 session seconds by task and arm (medians; bootstrap of the difference, 2,000 resamples, seed 1) and the pooled medians. Asserts: the kept counts (1,992 for study 1; 505 and 493 for study 2; 2,958 for study 3), one pooled Table 4 numerator (136, S trials that passed and were labelled complete), and the complete-label marginal counts of Table 10 (labeller and rater, by arm and hidden-check result); the Table 10 discordant pairs and the other Table 4 cells are not asserted. | package, `<RAW>` |
| `ledger_audit.py` / `.txt` | Integrity audit of the signed ledger each signed-arm trial left behind (pilot S and P, study 1 S and P, study 2 S, study 3 S, K and TD; 4,884 trials). Per ledger: the package's pinned `verify(ledger, private=True)`; verification failures now and failures at trial end (`record.json`) are tallied separately, with no per-trial comparison of the two verdicts and no assertion on them; genesis entry, key list and ledger code compared byte for byte with the template (differences tallied). Transcript checks: every tool result containing "signed entry #N appended" contributes an announced number, whether or not a matching `claim` call exists; announced numbers are set against the chain (removed, unannounced, doubly announced entries). A `claim` statement is compared with its entry text only when the restricted shell parser reads it and the announcement count equals the parse count in that call, and a private text exists: 4,046 of the 22,778 entries had a matched statement, none differed. The heuristic non-`claim` touch and write-capability counts (Bash commands or Write/Edit calls naming the ledger, judged by regex): 198 trials touch, none write-capable. Counts only, no text or trial ids; arm labels come from an allowlist; failures print a fixed category and a count. Asserts a self-test of the verifier (edited text and edited entry fail; deleted last entry still verifies but is flagged as removed) and a score gate: on matched scored rows, the count of entries with a private text and (outside the pilot) of entries with attachments must equal the package score files, with zero mismatches asserted (4,883 rows compared in this run; the number is not asserted). Note: the shipped `.txt` is the run on the public redacted archive, so readers can reproduce it; the author's run on the unredacted trial folders differs only in the "unannounced entries" fields (2 entries in 2 trials there, 7 here; most likely because redaction replaced transcript text the matcher reads, not traced); no number cited in the paper depends on those fields. | package (`template/`, `template3/`, `runs/`), `<RAW>`, `ssh-keygen -Y` |
| `ledger_audit.txt` | Its output (see the note above). | |
| `network_scan.py` / `.txt` | Heuristic regex scan of the tool calls of the 6,228 saved transcripts (pilot, studies 1-3); it cannot show actual network traffic, which was not logged. Scope by field: the all-field search covers only the benchmark owner and repository strings; task-folder names are tested in the selected command segments and URL-like strings; URL literals are counted in the Bash `command`, or in the `content` and `new_string` fields of other calls (a whole-input count with the same pattern finds 133 more calls); fetch classes are regex matches tallied per tool call. A call counts as retrieving when its result matches a retrieval pattern or shows pip's upgrade notice, which pip can emit from its cache: 17 result matches in 13 trials, and 3 of those 13 trials qualify only through that notice. A benchmark or task marker in a qualifying command or URL triggers exclusion even if retrieval failed. Then re-runs the main contrasts of studies 1 and 3 (study 2 has no such trial) with the trials that retrieved third-party content removed, through the package analysers. The gates assert that, with nothing removed, the selected output lines equal the frozen `runs/` analysis (equality of the lines, not of their number; 3 lines for study 1, 5 for study 3). Counts only: no transcript text, trial id or path; arm labels come from an allowlist; failures print a fixed category and a count. | package, `<RAW>` |
| `network_scan.txt` | Its output. | |
| `not_verified.py` / `.txt` | Final messages with a "Not verified"-type section (the matcher of `runner/z1_relabel_study2.py`, imported unchanged), study 2 (S, control) and study 3 (S, I, K, TD), all scored and kept trials. Study 3 messages are read and stripped of the STATUS line as the registered analysis does. Gates: the frozen 100 / 11 of `runs/study2-z1.txt` and the kept counts of both studies. | package, `<RAW>` |
| `study2_preoutage.py` / `.txt` | Study 2 restricted to the trials at schedule positions 1-994, before the connection errors (positions 995-1,082): the registered analysis function `analyze_study2.main`, unchanged, plus the pass rate with `mh_rd`; 97.5% intervals (display only) for the full-run contrasts next to the plan's *p* < .025 rule. Asserts the kept counts (505, 493) and that the full-run counts equal pre-outage plus later counts. | package, `<RAW>` (record files only) |
| `td_secondary.py` / `.txt` | Study 3 TD - S on false completion, false non-completion and pass rate with the package's `analyze_study3.contrast` and decision grid, with per-arm counts, and again without the 11 TD trials that edited the acceptance tests. Asserts the kept counts (740, 737) and the 11. | package only |
| `claim_counts.py` / `.txt` | Study 1: claim entries per kept trial, P against S (the `records` column), with a task-stratified van Elteren rank-sum test (self-test against known answers first), per-task means and medians and a stratified rate ratio (descriptive). Gate: the frozen means 3.67 and 4.82. | package only |
| `gap_checks.py` / `.txt` | (a) the same test on the pilot (20 task strata; gate: frozen means 3.49 and 4.10); (b) study 2 window of the connection errors: trials that finished before the earliest end of an errored trial, error counts by arm, Fisher's exact test on the rest (gate: 88 trials, 43/49 control and 27/39 S); (c) the 141 study 1 rebuilds that did not reproduce the saved state, by task and by which fidelity flag fails. The docstring records that a first version of (b) was superseded before any use. | package, `<RAW>` (record start times only) |
| `ledger_content.py` / `.txt` | What the signed entries say, counted deterministically (no model, no person): entries, trials with none, exact repetition within and across trials, share the benchmark's labeller marks `complete` or as claiming tests pass, evidence attached, all by hidden-check result, for the six signed arms of studies 1-3; pooled totals. Gates: kept counts, entries per trial and `record_false_complete` equal the package score files (0 of 4,715 differ). Counts only, no entry text or trial id. | package, `<RAW>` |
| `ledger_share.py` / `.txt` | Studies 2 and 3 signed arms: success entries per trial by hidden-check result, the failed-minus-passed difference of per-trial shares with a percentile bootstrap (2,000 resamples, seed 2028), and study 2 false completion read from the message or the record (102/505). Reuses `ledger_content.py`. Gate: 485 failed and 2,238 passed kept trials. | package, `<RAW>` |
| `sdt_bootstrap.py` / `.txt` | Study 2 signal detection indices (*d*′, *c*) per task and arm with percentile bootstrap intervals of the S - control differences (2,000 resamples, seed 2028; a task whose resamples hit a rate of 0 or 1 is reported as not estimable), and caveat shares ("Not verified" section, mention of Python 3.8) by arm and hidden-check result, with and without the TOML task. Gates: the kept counts and the six *d*′ and *c* values of `round14_checks.txt`. | package, `<RAW>` |
| `power_543.py` / `.txt` | Sample size per arm for study 2's planned 6-point difference from 11.6%, both directions, at α .05 and .025, pooled and unpooled normal approximation (standard library only). | none |
| `b1_split.py` / `.txt` | The study 3 audit split by arm and hidden-check result for each model rater (both / labeller only / rater only / neither), from the frozen labels in `runs/study3-audit/`. Asserts the cells equal the table this printout replaced in the paper. | package only |
| `paper_numbers.json` | One entry per number group the paper prints: section or table, the quoted context, the value as printed, the producing script, the committed output file, a line anchor in it and the rule that turns the number there into the printed value (or, for a derived figure, the formula over numbers read from the outputs); the figures that no committed script prints (`unscripted`, with the reason); the SHA-256 of every script and output used. | |
| `verify_paper_numbers.py` | Checks the hashes and every value of `paper_numbers.json`; with `--rerun`, reruns every post hoc script here and compares its output with the committed `.txt` (scripts whose inputs are absent are skipped, with the reason). | `paper_numbers.json`; for `--rerun` as each script |
| `test_paper_numbers.py` | The same checks as pytest tests, plus a test that the checker rejects a changed value. It is here, not in `tests/`, because `tests/` is inside the sealed chain hash. | as above |
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
python posthoc/round13_checks.py
python posthoc/session_env.py
python posthoc/round14_checks.py
python posthoc/ledger_audit.py
python posthoc/network_scan.py
python posthoc/not_verified.py
python posthoc/study2_preoutage.py
python posthoc/td_secondary.py
python posthoc/claim_counts.py
python posthoc/gap_checks.py
python posthoc/ledger_content.py
python posthoc/ledger_share.py
python posthoc/sdt_bootstrap.py
python posthoc/power_543.py
python posthoc/b1_split.py
python posthoc/verify_paper_numbers.py --rerun   # or: python -m pytest -q posthoc/test_paper_numbers.py
```

| Placeholder | Meaning | Default |
| --- | --- | --- |
| package | this repository, at its root | the parent of `posthoc/` |
| `<RAW>` | the raw trial archive, unpacked: [10.5281/zenodo.24450523](https://doi.org/10.5281/zenodo.24450523) unpacks to `raw/` | `raw/`; override with `EILIKRINEIA_RAW=<path>` |
| `<CHAIN>` | a git clone of the public ledger, with its full history: <https://github.com/ulissesflores/eilikrineia> | `../eilikrineia`; override with `EILIKRINEIA_CHAIN=<path>` |

Both new scripts (`ledger_audit.py`, `network_scan.py`) need writable temporary storage; `ledger_audit.py` also needs OpenSSH with `ssh-keygen -Y` (signature verification).

| Script | Needs |
| --- | --- |
| `task_heterogeneity.py` | the package only |
| `misc_counts.py` | the package; `<RAW>` only for the study 3 turn counts |
| `mde.py`, `python38_caveats.py` | the package and `<RAW>` |
| `ceiling_9_1.py`, `audit_py38_examples.py` | the package only |
| `cross_trial_sensitivity.py`, `cross_trial_contacts.py`, `round12_checks.py` | the package and `<RAW>` |
| `rebuild_vs_flagged.py` | the package only |
| `round13_checks.py`, `round14_checks.py`, `ledger_audit.py`, `network_scan.py` | the package and `<RAW>` |
| `session_env.py` | `<RAW>` only |
| `prereg_chronology.py` | the package, `<RAW>`, `<CHAIN>`, `git`, `openssl` and the OpenTimestamps client `ots` (offline: `ots info`, never `ots verify`); trust anchors for the three time-stamp tokens: `prereg/study3/freetsa-cacert.pem`, `posthoc/usertrust-rsa-root.pem` (Sectigo) and the system CA bundle (DigiCert) |
| `td_secondary.py`, `claim_counts.py`, `b1_split.py` | the package only |
| `power_543.py` | nothing (standard library) |
| `not_verified.py`, `study2_preoutage.py`, `gap_checks.py`, `ledger_content.py`, `ledger_share.py`, `sdt_bootstrap.py` | the package and `<RAW>` |
| `verify_paper_numbers.py`, `test_paper_numbers.py` | the package; reruns as each script |

Version metadata (`CITATION.cff`, `codemeta.json`, `.zenodo.json`, `pyproject.toml`) stays at 1.1.0, the latest released version, until the next release.

Expected: the output of each script equals the `.txt` beside it. `round13_checks.py` prints the interpreter version and its `.txt` is the output on Python 3.11, so only that one line differs on 3.12 (`verify_paper_numbers.py --rerun` and the rerun test ignore that line).

## Differences from the author's run

- The scripts ran first on the author's working folders. For this release they were changed to read the paths above
  and in four further respects, none of which changes a number: (1) `cross_trial_contacts.py` replaces the host's
  temporary-folder prefix by `<TMPDIR>/` before cutting each excerpt; (2) `cross_trial_sensitivity.py` and
  `round12_checks.py` and `rebuild_vs_flagged.py` print dictionaries with sorted keys, so the output does not depend on `PYTHONHASHSEED`;
  (3) `task_heterogeneity.py` and `prereg_chronology.py` were rewritten to run on Python 3.11 (an expression moved out of
  an f-string); (4) `mde.py` checks its hard-coded pilot estimate and interval against `runs/pilot-analysis.txt`
  (see the table above). `task_heterogeneity.py` and `python38_caveats.py` also gained asserts on frozen values (see
  the table); their output did not change.
- `ledger_audit.txt` is an exception to the byte-identity statement below: the author's run on the unredacted trial
  folders differs from it in the "unannounced entries" fields (see the table row).
- On the published archive, the outputs of every script but seven are byte-identical to the first run (checked by
  `diff`). The seven are `cross_trial_contacts.txt` (`<TMPDIR>/` in place of the temporary-folder prefix),
  `cross_trial_sensitivity.txt`, `round12_checks.txt` and `rebuild_vs_flagged.txt` (sorted dictionary keys; with the dictionaries removed,
  `diff` is empty), `prereg_chronology.txt` (next point), `round13_checks.txt` (the error messages are now counted in three fixed categories instead of quoted) and `session_env.txt` (the synthetic zero-token error events, 61 in study 2, are left out of the token summaries, which changes the study 2 counts). The raw archive is the redacted copy, and the redaction
  left the line numbers the list refers to unchanged. All scripts run on Python 3.11 and 3.12.
- `prereg_chronology.py` ends with a completeness check that first also searched the author's working folder for
  timestamp files outside the study 3 seal; that folder is not published, so the line for it is gone and the
  package root is searched instead. The pilot's task order is read from its own `schedule.txt` (the original
  read it from the task folder of the working copy); the result is the same, "yes (180 trials ...)".
- The chronology depends on the state of the public ledger (commit times, stamps). It was run against a clone
  whose `main` equalled `origin/main`, and the script prints that check.
- The ten scripts of the second increment were changed only in how they find the package (the parent of
  `posthoc/`, as above, instead of an `EILIKRINEIA_PKG` variable), in the folder they import `claim_counts.py` and
  `ledger_content.py` from, and in their docstrings (the "Run" line; a pointer to the author's unpublished project
  log). Their outputs on the published archive, with Python 3.11 and 3.12, are byte-identical to the author's first
  run (checked by `cmp`).
- On 2026-11-24 every script here was brought under the lint of the packaging code (`ruff format`, `ruff check`, and `interrogate` at 100% with
  numpy docstrings). Layout, comments and docstrings changed; no statement's effect did (three lambdas became
  functions, `zip` calls state `strict=False`, two unused imports were removed). Every script was then rerun
  on the published archive with Python 3.11: all 26 outputs are byte-identical to the committed `.txt` files
  (checked by `cmp`), and `SHA256SUMS` and the script hashes in `paper_numbers.json` were regenerated.

## Not shipped

The paper's Appendix C says that the "+9.1 points" planning figure comes from `runs/z4-union.txt`. The script that
generated that file was not found in package v1.0.0 or in the author folders that were inspected. `ceiling_9_1.py` tests whether the figure can be reproduced from
`runs/z4-trials.jsonl`: the task mean for the opus writer, 9.07, matches the +9.1, but neither aggregation reproduces the full set of figures in the table, so the formula remains not established. Two small facts in the paper's
notes were read in the raw files by hand, with no script: the account's home-level `CLAUDE.md` (not a project-level file) appears in one transcript only
(`study/0928-S-feature-toml-config-r114`, where the agent's command read it with `cat`) and the `ls` listing that names a binary of the
author's tooling in another (`study/0368-P-feature-toml-config-r318`; the second was checked in the unredacted original,
which is not published). In the published archive both tool outputs are replaced by a redaction notice (`raw/REDACTIONS.tsv`).

## Excluded: two checks that need unpublished files

The paper's Table 11 names two post hoc checks as not reproducible from the package. Their scripts are not shipped:

- **`audit_assist.py`** (study 2 audit answers against the AI reading aid's suggestions: answers by date, answers
  made after the aid existed, and how many equal its suggestion, 29 of 31 and 76 of 77). It reads the aid's
  suggestion files, which are not published, and decides which suggestion was on disk before each answer from the
  file-system creation times of those files on the author's machine. Neither the files nor their creation times
  are in the package or the raw archive, so the script cannot run here, and its output names unpublished files.
- **`keys_count.py`** (why 10,206 private keys were removed: three key files in each host ledger, one in each study
  3 ledger, one distinct agent key per study). It reads the private key files of the unredacted trial folders. The
  published archive keeps only the public keys, and it keeps three public-key files in every ledger, study 3
  included, so a count of what is published cannot rebuild the 10,206.

Every other figure the paper prints without a committed script is listed, with the reason, under `unscripted` in
`paper_numbers.json`.

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
