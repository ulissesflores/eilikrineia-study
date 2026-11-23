# 0003. Sealed files are shipped byte for byte; packaging stays outside the seal

- Status: accepted
- Date: 2026-11-14

## Context

The preregistrations, results documents, trial code and audit code were hashed into the author's Eilikrineia
ledger when each was fixed; the 114 files pinned before study 3 (`prereg/study3/pins.txt`) were also timestamped
before its data existed. Reformatting, linting or translating them would make the
published bytes differ from the hashes recorded at the time, and a reader could no longer check that the plan
came first. The usual layout of the house (`code/`, linted to one standard, documents in several languages)
conflicts with that.

## Decision

- The evidence files (preregistrations, results documents, trial and audit code, frozen outputs) ship as they
  were recorded in the ledger or in the study 3 pins; a file changed between studies, such as
  `runner/run_trial.py`, ships in its last recorded version. They are not reformatted, linted, translated or
  moved, which is why the trial code lives in `runner/` and not in `code/`. The package's own code (`tests/`,
  `scripts/`, `run_all.py`, `make_provenance.py`) is sealed only by the release `chain_hash` and changed between
  release candidates, for example to handle the redactions.
- Lint and documentation coverage apply to the code written for the package (`run_all.py`,
  `make_provenance.py`, `scripts/`, `tests/`, `assets/brand/make_brand.py`); `pyproject.toml` excludes the folders
  sealed before the studies ran (`runner/`, `td/`, `template*/`, `overclaim/`, `rescore/`, `patches/`).
- The reader-facing material (README files in five languages, `REPRODUCIBILITY.md`, `docs/`, metadata, CI) is
  outside the `chain_hash`, so it can be corrected without touching the seal.
- Files that no document cites, no seal lists and no test needs are left out.

## Alternatives considered

- **Clean copies beside the originals.** Two versions of the same plan invite the question of which one ran.
- **Lint everything and reseal.** Breaks the link to the hashes recorded before the trials.

## Consequences

- Some sealed files contain absolute paths of the machine where the trials ran and name working files of the
  author that are not published; [`REPRODUCIBILITY.md`](../../REPRODUCIBILITY.md) says so.
- The only edits made to evidence files after sealing are the redactions of [0009](0009-public-derivatives.md), each listed in
  `REPRODUCIBILITY.md` ("Public derivatives"), with the ledger entry or lock that holds the original hash where
  one was recorded.

## References

- [`pyproject.toml`](../../pyproject.toml), [`REPRODUCIBILITY.md`](../../REPRODUCIBILITY.md), "Known limits"
