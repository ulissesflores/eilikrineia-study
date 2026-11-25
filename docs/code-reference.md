# Code reference for sealed and preregistered files

This page documents the 115 code files of this repository that are sealed by the provenance chain or pinned by a preregistration: Python modules, tests, and ledger code. It lists, file by file, what each one is for, what it reads, what it writes and which seal covers it.

## Why these files carry no header

Newer files in this repository start with a header (licence line, author, ORCID, purpose, inputs, outputs, how to run). The files below do not. They were sealed or pinned before that header standard existed, and editing them would change their SHA-256. A changed hash breaks the provenance chain (`output/provenance.json`, checked by `make_provenance.py --verify`) or the preregistration proof (`prereg/study3/pins.txt`, `runs/study2-pins.txt`). The decision to ship sealed files byte for byte is recorded in `docs/adr/0003-sealed-files-shipped-byte-for-byte.md`. Headers will enter these files only in a new, re-sealed version where no preregistration hash is involved.

## Authorship and licence (applies to every file listed)

- Author: Carlos Ulisses Flores (Codex Hash Ltda.), ORCID https://orcid.org/0000-0002-6034-7765
- Code licence: Apache-2.0 (see `LICENSE`, `LICENSES/` and `NOTICE`)
- Repository: https://github.com/ulissesflores/eilikrineia-study

## How to read the "Sealed by" column

- provenance chain: the file path occurs in `output/provenance.json`
- study 3 pins: the file path occurs in `prereg/study3/pins.txt` (the study 3 preregistration pins)
- study 2 pins: the file path occurs in `runs/study2-pins.txt`

Files not listed here (the CI workflows, `assets/brand/make_brand.py`, `colab/replication.ipynb` and everything under `posthoc/`) are not sealed and carry their own headers.

Paths in the Purpose, Inputs and Outputs columns are relative to the repository root unless stated otherwise. "Hidden check" means a test file withheld from the agent and copied into its workspace only after the agent stops.


## Root

| File | Purpose | Inputs | Outputs | Sealed by |
| --- | --- | --- | --- | --- |
| `make_provenance.py` | Builds or verifies the single SHA-256 chain hash over the sealed code, the dated documents and the frozen data. | Sealed folders and dated root documents; with `--verify`, output/provenance.json | output/provenance.json and output/hash-chain.md; with `--verify`, a pass or fail message and exit code | provenance chain |
| `run_all.py` | Single entry point: reruns the analyses from frozen scores, runs the tests, verifies the seal. | Frozen files under runs/; tests/; output/provenance.json | Per-step pass or fail lines on stdout; exit code 0 only if every step passes | provenance chain |

## runner/

| File | Purpose | Inputs | Outputs | Sealed by |
| --- | --- | --- | --- | --- |
| `runner/analyze.py` | Preregistered analysis of the pilot: Wilson intervals, P-S and S-H differences with Newcombe intervals, per-task table, decision rules. | Scores CSV from score.py; optional `--exclude` trial names | Tables on stdout | provenance chain, study 3 pins, study 2 pins |
| `runner/analyze_rescore.py` | Primary estimate on the re-scored study (post hoc): same exclusions and estimator as analyze_study, new hidden-check result. | Scores CSV and re-score CSV from rescore_replay.py | Estimates on stdout | provenance chain |
| `runner/analyze_study.py` | Preregistered analysis of the main study: P against S, Mantel-Haenszel risk difference stratified by task, CMH test, Wilson and Newcombe intervals. | Scores CSV; options `--a`, `--b` for the arms | Tables on stdout (its `mh_rd` estimator is reused by later analyses) | provenance chain, study 3 pins, study 2 pins |
| `runner/analyze_study2.py` | Preregistered analysis of study 2: S against the control arm, false completion and false non-completion. | Runs folder (each record.json agent exit code) and scores CSV | Tables on stdout | provenance chain, study 3 pins, study 2 pins |
| `runner/analyze_study3.py` | Preregistered analysis of study 3: arms I, K and TD each against S, with the Bonferroni-corrected confirmatory tests and the decision grid. | Runs folder (final messages in agent.stdout) and scores CSV from score_study.py | Tables and per-test readings on stdout | provenance chain, study 3 pins |
| `runner/audit.py` | Blinded audit of the claim labeller (study 3): draws 40 messages per arm, has a model rater label them, computes agreement and the measurement-limited rule. | Subcommands: `sample` (runs folder, scores CSV, ledger entry hash, out dir), a model-rater labelling subcommand (out dir), `report` (out dir, human labels JSON); overclaim/docs/claims.md | items.jsonl, key.jsonl and the model rater labels in the out dir; agreement report on stdout | provenance chain, study 3 pins |
| `runner/audit_posthoc.py` | Post hoc additions to the study 3 labeller audit: a third model rater, the owner sample of 40, a pt-BR translation, agreement tables. | Subcommands for a third model rater, `sample`, `translate`, `report` with the audit out dir (items.jsonl, key.jsonl) | Label, sample and translation JSON files in the out dir; agreement tables on stdout | provenance chain |
| `runner/audit_study2.py` | Blinded human audit of the labeller on study 2: samples 80 messages, translates them, serves a local labelling page, reports agreement per arm. | Subcommands `sample` (runs, scores CSV, seed file, out), `translate`, `serve` (out, rater), `report` (out, raters) | items.jsonl, key.jsonl, items.pt.json, labels-<rater>.json and report.txt in the out dir | provenance chain |
| `runner/audit_study2_split.py` | Second post hoc plan of the study 2 audit: results by arm and check result, and again without very fast answers. | Out dir with key.jsonl and labels-<rater>.json, plus rater names | report-split.txt in the out dir | provenance chain |
| `runner/audit_substitute.py` | Substitute second model rater for the study 3 audit (documented deviation) and its agreement report. | Subcommands for the second model rater and `report`, with the audit out dir (items.jsonl, key.jsonl, first rater labels) | Rater label JSON in the out dir; agreement per rater and the deviation rule on stdout | provenance chain |
| `runner/claim.py` | The `claim` record tool every arm gets: appends a statement (with optional evidence file) to a private notes file (arm H) or to a signed hash-chained ledger (arms S, P). | Statement argument, optional `--evidence FILE`; env EXP_ARM and EXP_LEDGER | Appends to notes.jsonl or the ledger; prints the entry sequence number | provenance chain, study 3 pins, study 2 pins |
| `runner/recover_record.py` | Rebuilds record.json for a trial whose run_trial.py crashed after the agent and hidden check had finished. | Trial folders with agent.stdout, diff.patch, check.txt and the ledger copy | record.json in each trial folder | provenance chain |
| `runner/rescore_replay.py` | Post hoc re-score of the TOML and URI trials: replays each transcript on a fresh task copy under an OS sandbox, then runs the valid hidden check. | Runs folder, output CSV path; options `--tasks`, `--jobs`, `--limit`; the task repos and the rescore/ folder | CSV of fidelity checks and re-scored outcomes | provenance chain, study 3 pins |
| `runner/run_batch.py` | Runs a seeded, shuffled schedule of trials (tasks x arms x repetitions), resumable, with a weekly quota guard. | Seed hex, out dir, `--tasks`, `--arms`, `--reps`, `--jobs`, `--timeout`, quota options | schedule.txt, progress log and one folder per trial (via run_trial.py) | provenance chain, study 3 pins, study 2 pins |
| `runner/run_pilot.py` | Runs the preregistered pilot: 20 tasks x 3 arms x 3 repetitions, shuffled by a ledger entry hash, resumable. | Seed hex, out dir, `--jobs` | schedule.txt, progress log and one folder per trial (via run_trial.py) | provenance chain |
| `runner/run_trial.py` | Runs one confined trial of the coding agent on a task and scores it with the hidden check; study 3 variants run inside a container image. | Task name, arm, out dir; options for model, effort, timeout, container image, status line, ledger template | agent.stdout, agent.stderr, prompt.md, diff.patch, check.txt, td.json (arm TD) and record.json in the out dir | provenance chain, study 3 pins, study 2 pins |
| `runner/score.py` | Scores every trial of the pilot from its raw files: claim label, verification verdict, unbacked claims, false completion. | Runs folder; optional `--csv` | One JSON line per trial and per-arm counts on stdout; optional CSV | provenance chain, study 3 pins, study 2 pins |
| `runner/score_study.py` | Scores the main study: everything score.py computes plus records made, evidence attached and hidden-folder access. | Runs folder, `--csv` path | CSV of per-trial fields | provenance chain, study 3 pins, study 2 pins |
| `runner/seal_prereg.py` | Seals a preregistration: hashes the pinned files and time-stamps the list with three RFC 3161 authorities and OpenTimestamps. | Out dir and the list of files or folders to pin | pins.txt, .tsq/.tsr time-stamp files and pins.txt.ots in the out dir | provenance chain, study 3 pins |
| `runner/sensitivity_study.py` | Exploratory sensitivity checks of the main study (by concurrency phase, without the recovered trial, timeout rate); not preregistered. | Runs folder and scores CSV | Tables on stdout | provenance chain |
| `runner/sensitivity_study2.py` | Sensitivity analyses of study 2 (post hoc): rebuilds rows of four trials without record.json and excludes one failed start. | Runs folder, scores CSV, output CSV path | Output CSV and estimates on stdout | provenance chain |
| `runner/td_build.py` | Builds the TD arm input: the writer's three reference-validated test sets per task, with failing tests cut from the source and the rest kept byte for byte. | Out dir; runs/z4-validity.json and runs/z4-writers/ | <task>/acceptance/ test files and manifest.json in the out dir | provenance chain, study 3 pins |
| `runner/test_run_trial.py` | Regression test: suspicious_access must not crash on an event whose message is a string. | Real transcript of one affected trial (agent.stdout) | Unit test result | provenance chain, study 3 pins |
| `runner/test_study3.py` | Tests of the study 3 code paths: status-line removal, TD test cutting and rerun, quota resume, harness-crash skip, decision grid, and two end-to-end trials with a fake agent. | Task folders and template3/ledger; a fake `claude` executable written to a temp dir | Unit test results | provenance chain, study 3 pins |
| `runner/z1_relabel_study2.py` | Exploratory (not preregistered): relabels study 2 final messages ignoring cues under "not verified" headings. | Runs folder, scores CSV, output CSV path | Relabelled CSV and counts | provenance chain, study 3 pins |
| `runner/z4_score_tests.py` | Exploratory: validates each writer's acceptance tests on the reference solution, then runs the valid sets on each rebuilt study 2 workspace. | Writers folder, runs folder, scores CSV, output prefix; `--report` mode | <out>-validity.json, <out>-trials.jsonl and a report on stdout | provenance chain |
| `runner/z4_write_tests.py` | Exploratory: candidate model writers write acceptance tests from the task text only. | Out dir; options `--writers`, `--runs`, `--jobs`; task.toml prompts and starting repos | Per-writer test_acceptance.py, writer.stdout, writer.stderr and meta.json | provenance chain |

## scripts/

| File | Purpose | Inputs | Outputs | Sealed by |
| --- | --- | --- | --- | --- |
| `scripts/make_figures.py` | Draws the report figures; every number is read from frozen files, each figure maps to a claim. | Frozen files under runs/ (CSV, analysis text, study3-audit/); `--paper DIR` for the light-theme variant | PNG and SVG files under output/figures/ (or the folder given) | provenance chain |
| `scripts/make_results.py` | Recomputes the headline counts from the frozen per-trial files. | runs/*.csv and runs/study3-audit/ | output/results.json; with `--check`, exit 1 if the committed file differs | provenance chain |
| `scripts/rerun_studies23.py` | Reruns the registered analyses of studies 2 and 3 from the frozen score files and compares them with the frozen outputs. | runs/study2-agent-rc.csv, frozen score files; `--extract` reads raw record.json files | Match or difference report on stdout; exit code | provenance chain |
| `scripts/show_case.py` | Prints one audited study 3 trial where the agent said complete and the hidden check failed. | runs/study3-audit/ (key.jsonl, items.jsonl, rater label files) | The case on stdout | provenance chain |

## tests/

| File | Purpose | Inputs | Outputs | Sealed by |
| --- | --- | --- | --- | --- |
| `tests/test_published_numbers.py` | Locks the published numbers: recomputed counts, frozen estimate lines, and the numbers stated in README and docs. | output/results.json, runs/, README and docs text, prereg/study3/pins.txt | Pytest result | provenance chain |
| `tests/test_study2_audit.py` | Locks the post hoc study 2 audit against the ledger entries and the numbers the paper prints. | runs/study2-audit/ (ledger-entries.json, key.jsonl, labels, report files) | Pytest result | provenance chain |

## template/ and template3/

| File | Purpose | Inputs | Outputs | Sealed by |
| --- | --- | --- | --- | --- |
| `template/ledger/eilikrineia.py` | Hash-chained, signed commitment ledger that the S and P arms write to through `claim`; standard library plus `ssh-keygen -Y`. | Subcommands init, record, verify, audit, witness, genesis, rotate, pinned-ok, compact, stamp, publish, reveal and a ledger root folder | Chain entries, private text files and a compressed vault under the ledger root; verification result | provenance chain |
| `template3/ledger/eilikrineia.py` | Same ledger program for study 3 (byte-identical to template/ledger/eilikrineia.py), shipped inside the study 3 template. | As template/ledger/eilikrineia.py | As template/ledger/eilikrineia.py | provenance chain, study 3 pins |

## rescore/

| File | Purpose | Inputs | Outputs | Sealed by |
| --- | --- | --- | --- | --- |
| `rescore/feature-uri-resolve/checks/checks/__init__.py` | Empty package marker for the corrected hidden check. | none | none | provenance chain |
| `rescore/feature-uri-resolve/checks/checks/test_uri_hidden.py` | Corrected hidden check of the URI task, used by rescore_replay.py (byte-identical to the one under overclaim/tasks/). | The rebuilt urikit workspace | Unittest result | provenance chain |
| `rescore/feature-uri-resolve/solution-fixed/normalize.py` | Reference solution module for URI normalisation (RFC 3986 6.2.2, 6.2.3), byte-identical to the task solution copy. | none (library module) | none (library module) | provenance chain |

## td/

| File | Purpose | Inputs | Outputs | Sealed by |
| --- | --- | --- | --- | --- |
| `td/feature-toml-config/acceptance/__init__.py` | Empty package marker for the acceptance tests. | none | none | provenance chain, study 3 pins |
| `td/feature-toml-config/acceptance/test_r1.py` | Acceptance test set 1 for TOML support in cfgkit; given to the agent under study in arm TD (written from the task text by a model writer). | The agent workspace code under test | Unittest result | provenance chain, study 3 pins |
| `td/feature-toml-config/acceptance/test_r2.py` | Acceptance test set 2 for TOML support in cfgkit; given to the agent under study in arm TD (written from the task text by a model writer). | The agent workspace code under test | Unittest result | provenance chain, study 3 pins |
| `td/feature-toml-config/acceptance/test_r3.py` | Acceptance test set 3 for TOML support in cfgkit; given to the agent under study in arm TD (written from the task text by a model writer). | The agent workspace code under test | Unittest result | provenance chain, study 3 pins |
| `td/feature-uri-resolve/acceptance/__init__.py` | Empty package marker for the acceptance tests. | none | none | provenance chain, study 3 pins |
| `td/feature-uri-resolve/acceptance/test_r1.py` | Acceptance test set 1 for the RFC 3986 rework of urikit; given to the agent under study in arm TD (written from the task text by a model writer). | The agent workspace code under test | Unittest result | provenance chain, study 3 pins |
| `td/feature-uri-resolve/acceptance/test_r2.py` | Acceptance test set 2 for the RFC 3986 rework of urikit; given to the agent under study in arm TD (written from the task text by a model writer). | The agent workspace code under test | Unittest result | provenance chain, study 3 pins |
| `td/feature-uri-resolve/acceptance/test_r3.py` | Acceptance test set 3 for the RFC 3986 rework of urikit; given to the agent under study in arm TD (written from the task text by a model writer). | The agent workspace code under test | Unittest result | provenance chain, study 3 pins |
| `td/text-template-engine/acceptance/__init__.py` | Empty package marker for the acceptance tests. | none | none | provenance chain, study 3 pins |
| `td/text-template-engine/acceptance/test_r1.py` | Acceptance test set 1 for the extended tplr engine; given to the agent under study in arm TD (written from the task text by a model writer). | The agent workspace code under test | Unittest result | provenance chain, study 3 pins |
| `td/text-template-engine/acceptance/test_r2.py` | Acceptance test set 2 for the extended tplr engine; given to the agent under study in arm TD (written from the task text by a model writer). | The agent workspace code under test | Unittest result | provenance chain, study 3 pins |
| `td/text-template-engine/acceptance/test_r3.py` | Acceptance test set 3 for the extended tplr engine; given to the agent under study in arm TD (written from the task text by a model writer). | The agent workspace code under test | Unittest result | provenance chain, study 3 pins |

## overclaim/src/overclaim/

| File | Purpose | Inputs | Outputs | Sealed by |
| --- | --- | --- | --- | --- |
| `overclaim/src/overclaim/__init__.py` | Package marker with the package description and version. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/src/overclaim/__main__.py` | Lets `python -m overclaim` run the command line. | Command-line arguments | see cli.py | provenance chain, study 3 pins |
| `overclaim/src/overclaim/claims.py` | Rule-based labelling of an agent's final message: complete, partial, incomplete or none, with the cues that counted. | A final message string | none (library module); returns a label and cue list | provenance chain, study 3 pins |
| `overclaim/src/overclaim/cli.py` | Command line: `overclaim scan \| inspect \| classify \| label \| hook \| export`. | Run directories or JSONL files, optional labels and difficulty files, options per subcommand | Results on stdout, diagnostics on stderr; optional output files; exit codes 0, 1, 2, 130 | provenance chain, study 3 pins |
| `overclaim/src/overclaim/detectors.py` | Detectors that flag a trial as a likely false completion, and their evaluation against the hidden check. | Transcript, claim and evidence per trial | none (library module); returns flags and scores | provenance chain, study 3 pins |
| `overclaim/src/overclaim/evidence.py` | Verification evidence: which commands ran tests, how they ended, and what came after edits. | A parsed transcript | none (library module); returns an evidence verdict | provenance chain, study 3 pins |
| `overclaim/src/overclaim/hook.py` | Claude Code hooks: a Stop hook that blocks an unverified completion claim and a PostToolUse hook that logs commands and edits. | JSON payload on stdin (session id, transcript path, last message) | JSON decision on stdout; a JSONL log of commands and edits | provenance chain, study 3 pins |
| `overclaim/src/overclaim/llm.py` | Optional model labelling through the local `claude` CLI, with an on-disk cache. | Prompts and inputs | Answers cached on disk; returned labels | provenance chain, study 3 pins |
| `overclaim/src/overclaim/metrics.py` | Claim-versus-outcome metrics per group, with cluster-bootstrap intervals and paired comparisons between arms. | Labelled trial records | none (library module); returns rates and intervals | provenance chain, study 3 pins |
| `overclaim/src/overclaim/models.py` | Shared data model imported by every other module. | none | none (library module) | provenance chain, study 3 pins |
| `overclaim/src/overclaim/report.py` | Renders a scan as text, Markdown or JSON (pure functions). | Scan results | none (library module); returns a string | provenance chain, study 3 pins |
| `overclaim/src/overclaim/sources.py` | Loads trials from run directories and generic JSONL manifests. | Run directories, JSONL manifests, task.toml | Trial records in memory | provenance chain, study 3 pins |
| `overclaim/src/overclaim/stats.py` | Interval estimates and paired tests, standard library only, deterministic for a seed. | Numeric counts or paired outcomes | none (library module) | provenance chain, study 3 pins |
| `overclaim/src/overclaim/transcript.py` | Reads agent transcripts (Claude stream JSON, Claude session, Codex JSONL, generic JSONL) into one normalised form. | Transcript files | A normalised transcript in memory | provenance chain, study 3 pins |

## overclaim/tasks/solvable/ (task fixtures)

| File | Purpose | Inputs | Outputs | Sealed by |
| --- | --- | --- | --- | --- |
| `overclaim/tasks/solvable/feature-toml-config/checks/checks/__init__.py` | Empty package marker for the hidden check. | none | none | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-toml-config/checks/checks/test_toml_hidden.py` | Hidden check of the TOML task; copied into the workspace only after the agent stops. Never shown to the agent. | The agent's cfgkit workspace | Unittest result (pass or fail per test) | provenance chain, study 3 pins, study 2 pins |
| `overclaim/tasks/solvable/feature-toml-config/checks/checks/toml_fuzz_lib.py` | Helper for the hidden check: generates random TOML documents for comparison. | Random seed | Generated documents (library module) | provenance chain, study 3 pins, study 2 pins |
| `overclaim/tasks/solvable/feature-toml-config/repo/cfgkit/__init__.py` | Task fixture given to the agent under study (starting repo): cfgkit package exports. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-toml-config/repo/cfgkit/config.py` | Task fixture given to the agent under study (starting repo): Configuration container with dotted-path access. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-toml-config/repo/cfgkit/errors.py` | Task fixture given to the agent under study (starting repo): cfgkit error types. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-toml-config/repo/cfgkit/ini.py` | Task fixture given to the agent under study (starting repo): Small INI parser. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-toml-config/repo/cfgkit/loader.py` | Task fixture given to the agent under study (starting repo): Reads configuration files by format. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-toml-config/repo/tests/__init__.py` | Empty package marker for the starting repo tests. | none | none | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-toml-config/repo/tests/test_basic.py` | Task fixture given to the agent under study: the visible tests of the starting repo. | cfgkit starting repo | Unittest result | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-toml-config/solution/cfgkit/__init__.py` | Reference solution (never shown to the agent): cfgkit package exports with TOML. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-toml-config/solution/cfgkit/config.py` | Reference solution (never shown to the agent): Configuration container with dotted-path access. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-toml-config/solution/cfgkit/errors.py` | Reference solution (never shown to the agent): cfgkit error types. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-toml-config/solution/cfgkit/ini.py` | Reference solution (never shown to the agent): Small INI parser. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-toml-config/solution/cfgkit/loader.py` | Reference solution (never shown to the agent): Reads configuration files by format, including TOML. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-toml-config/solution/cfgkit/toml.py` | Reference solution (never shown to the agent): Reference TOML 1.0 parser without date and time values, Python 3.8+. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/checks/checks/__init__.py` | Empty package marker for the hidden check. | none | none | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/checks/checks/test_uri_hidden.py` | Hidden check of the URI task; copied into the workspace only after the agent stops. Never shown to the agent. | The agent's urikit workspace | Unittest result | provenance chain, study 3 pins, study 2 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/repo/tests/__init__.py` | Empty package marker for the starting repo tests. | none | none | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/repo/tests/test_basic.py` | Task fixture given to the agent under study: the visible tests of the starting repo. | urikit starting repo | Unittest result | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/repo/urikit/__init__.py` | Task fixture given to the agent under study (starting repo): urikit package exports. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/repo/urikit/errors.py` | Task fixture given to the agent under study (starting repo): urikit error type. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/repo/urikit/join.py` | Task fixture given to the agent under study (starting repo): Simplified join without dot-segment handling. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/repo/urikit/linkset.py` | Task fixture given to the agent under study (starting repo): Turns href attributes of a page into the set of pages to visit. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/repo/urikit/uri.py` | Task fixture given to the agent under study (starting repo): URI splitting and recomposition. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/solution/urikit/__init__.py` | Reference solution (never shown to the agent): urikit package exports. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/solution/urikit/join.py` | Reference solution (never shown to the agent): join built on resolve. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/solution/urikit/linkset.py` | Reference solution (never shown to the agent): Turns href attributes into the set of pages to visit. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/solution/urikit/normalize.py` | Reference solution (never shown to the agent): Syntax-based and scheme-based normalisation (RFC 3986 6.2.2, 6.2.3). | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/solution/urikit/resolve.py` | Reference solution (never shown to the agent): Reference resolution (RFC 3986 5.2). | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/feature-uri-resolve/solution/urikit/uri.py` | Reference solution (never shown to the agent): URI parsing with validation and recomposition (RFC 3986). | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/checks/checks/__init__.py` | Empty package marker for the hidden check. | none | none | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/checks/checks/test_tpl_hidden.py` | Hidden check of the template task; copied into the workspace only after the agent stops. Never shown to the agent. | The agent's tplr workspace | Unittest result | provenance chain, study 3 pins, study 2 pins |
| `overclaim/tasks/solvable/text-template-engine/repo/tests/__init__.py` | Empty package marker for the starting repo tests. | none | none | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/repo/tests/test_tplr.py` | Task fixture given to the agent under study: the visible tests of the starting repo. | tplr starting repo | Unittest result | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/repo/tplr/__init__.py` | Task fixture given to the agent under study (starting repo): tplr package exports. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/repo/tplr/engine.py` | Task fixture given to the agent under study (starting repo): Compiles and renders templates. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/repo/tplr/errors.py` | Task fixture given to the agent under study (starting repo): Error types. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/repo/tplr/expr.py` | Task fixture given to the agent under study (starting repo): Variable paths followed by filters. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/repo/tplr/filters.py` | Task fixture given to the agent under study (starting repo): Built-in filters. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/repo/tplr/lexer.py` | Task fixture given to the agent under study (starting repo): Splits template source into text and tag tokens. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/repo/tplr/parser.py` | Task fixture given to the agent under study (starting repo): Builds a node tree from tokens. | none (task fixture) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/solution/tplr/__init__.py` | Reference solution (never shown to the agent): tplr package exports. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/solution/tplr/engine.py` | Reference solution (never shown to the agent): Compiles and renders templates. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/solution/tplr/errors.py` | Reference solution (never shown to the agent): Error types. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/solution/tplr/expr.py` | Reference solution (never shown to the agent): Literals, variable paths, filters, comparisons and boolean logic. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/solution/tplr/filters.py` | Reference solution (never shown to the agent): Built-in filters with argument counts. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/solution/tplr/lexer.py` | Reference solution (never shown to the agent): Splits template source into text and tag tokens. | none (library module) | none (library module) | provenance chain, study 3 pins |
| `overclaim/tasks/solvable/text-template-engine/solution/tplr/parser.py` | Reference solution (never shown to the agent): Builds a node tree from tokens. | none (library module) | none (library module) | provenance chain, study 3 pins |
