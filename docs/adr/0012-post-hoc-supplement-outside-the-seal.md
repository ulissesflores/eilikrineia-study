# 0012. Post hoc analyses ship as a supplement outside the seal

- Status: accepted
- Date: 2026-11-23

## Context

After the paper's reviews, reviewers asked for analyses that no preregistration contains: a sensitivity check
with the trials that read another trial's temporary files removed, task heterogeneity, minimum detectable effects,
the effect of the Python 3.8 sentence on the labeller, assorted counts, and the chronology of when each plan was
recorded. The scripts import the package's own analysers unchanged and read the package's frozen files, and some of
them need the raw archive and a clone of the public ledger. Their outputs are quoted in the paper, so a reader
should be able to check them. Putting them in the sealed set would change the `chain_hash` of version 1.0.0 and
suggest that they were part of the plan; leaving them out leaves numbers in the paper with no code behind them.

## Decision

- The scripts, their outputs, the scan list they read and the flagged cross-trial list live in `posthoc/`, a folder
  outside the `chain_hash`, like `docs/`. `posthoc/SHA256SUMS` lists their checksums, and `posthoc/README.md` states
  that they are post hoc and exploratory, what each one needs, and how to run it from the package root.
- The scripts were changed from the author's working copies to read paths relative to the package root, the
  raw archive (`EILIKRINEIA_RAW`, default `raw/`) and a clone of the public ledger (`EILIKRINEIA_CHAIN`), and in
  four further respects that change no number: the contact excerpts are redacted before cutting, three scripts
  (`cross_trial_sensitivity.py`, `round12_checks.py`, `rebuild_vs_flagged.py`) print dictionaries with sorted keys, two scripts use Python 3.11 syntax, and the pilot inputs of `mde.py` are checked
  against the frozen pilot output. Two scripts gained asserts on frozen values. The outputs were rerun and compared
  with the author's first run; `posthoc/README.md` lists the five that differ in form.
- The flagged list carries the trial, study, arm, task, strict and broad membership and the evidence category, and
  no transcript text. Personal data was looked for before copying (the author's home folder, user name, mail addresses and the
  names of other projects) in the lists and outputs. The contact excerpts first carried the author's host-specific
  temporary-folder prefix (`/private/var/folders/.../T/`); the generator now replaces it by `<TMPDIR>/` before cutting
  each excerpt, the output was regenerated, and a search for that prefix, the home folder and the user name finds none.
- The sealed files are not touched: version 1.1.0 has the same `chain_hash` as version 1.0.0.
- The supplement counts the cross-trial reads and reruns the estimates of studies 1 and 2 under three exclusion sets
  (see [0006](0006-pinned-container-for-study-3.md)); it does not settle whether the reads changed any outcome.
- The timestamp wording follows the evidence: study 3 has verified external timestamps from before its first trial;
  the inspection found none for the pilot and studies 1 and 2, whose plans carry only the signed entry times of the
  author's ledger (internal timestamps).

## Alternatives considered

- **Seal the supplement and reissue the `chain_hash`.** Makes the post hoc analyses look like part of the plan and
  breaks the continuity of the seal that the ledger and the paper cite.
- **Publish it as a separate record.** A reader of the package would not find the code that produced numbers the
  package's documents cite, and the supplement would need its own versioning and DOI.
- **Leave the scripts out and keep only the outputs.** Outputs without code cannot be checked.

## Consequences

- Readers can rerun every post hoc number; the cost is a folder that is not covered by the seal and that depends,
  for some scripts, on inputs that are not in the repository (the raw archive, the ledger clone).
- `prereg_chronology.py` reads a live repository, so its output can change if the ledger is rewritten; its output
  file records one run.
- `posthoc/` is excluded from lint and docstring coverage in `pyproject.toml`, as the sealed code is, because the
  scripts are shipped as they ran.
- A later post hoc script is added here with its output and a new line in `SHA256SUMS`, never in the sealed set.

## References

- [`posthoc/README.md`](../../posthoc/README.md)
- [0003](0003-sealed-files-shipped-byte-for-byte.md) for what stays outside the seal
- [0001](0001-one-chain-hash-seal.md) for what the seal covers
