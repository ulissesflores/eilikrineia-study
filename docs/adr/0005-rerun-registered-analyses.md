# 0005. The registered analyses of studies 2 and 3 are rerun from the frozen scores

- Status: accepted
- Date: 2026-11-22

## Context

The registered analysers of studies 2 and 3 (`runner/analyze_study2.py`, `runner/analyze_study3.py`) read the raw
trial folders, which are not in this repository ([0007](0007-raw-archive-as-separate-record.md)). Without them,
Track 1 could only check that the frozen outputs had not changed, not that the code produces them.

## Decision

`scripts/rerun_studies23.py` runs both analysers unchanged, from the score files:

- Study 2 needs, besides the scores, only each trial's exit code. It is shipped as
  `runs/study2-agent-rc.csv`, extracted from the raw `record.json` files, and the rerun must equal the frozen
  output.
- Study 3 also reads the final messages, which are in the raw archive only. Every line is compared with the
  frozen output; differences are allowed only inside the Z1 relabelling and pressure-mention sections, which the
  script names as not rerun (36 lines there differ in Track 1). Those lines are locked as text and are
  reproduced in Track 2.
- Lines that print a dictionary built from a set are compared as dictionaries, because their key order follows
  Python's hash seed.

## Alternatives considered

- **Port the analysers to read CSV.** Would change sealed code; the rerun would no longer be of the code that ran.
- **Ship the final messages in the repository.** Brings transcript text, and its privacy review, into a package
  meant to be light.

## Consequences

- Track 1 reruns the registered analysis scripts of the pilot and the three studies. Study 3 runs on empty trial
  folders: its crash check finds nothing and prints an empty table, which equals the frozen output (zero
  crashes) without recomputing it from the trials, and the 36 lines that differ in the final-message sections are
  allowed to differ;
  the labeller audits are not rerun.
- With the raw archive unpacked under `raw/`, the same analysers reproduce the full outputs (Track 2); this was
  checked on the published archive after redaction.

## References

- [`scripts/rerun_studies23.py`](../../scripts/rerun_studies23.py), [`run_all.py`](../../run_all.py)
