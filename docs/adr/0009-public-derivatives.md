# 0009. Redacted public copies of ledger-recorded files, with both hashes tested

- Status: accepted
- Date: 2026-11-23

## Context

The audit of this repository ([0008](0008-redact-log-audit.md)) found personal details inside files whose hashes
the author's ledger had already recorded: wall-clock times of each rater's answers, a temporary-folder prefix, the
answer times and a remark on a rater's language inside ledger texts, the hour of a lock, and a commit id and date
in a patch header. Leaving them exposes the raters; editing them breaks the match with the recorded hashes.

## Decision

The published files are redacted copies ("public derivatives"):

- wall-clock times became seconds spent per answer, or seconds since the start of the same sitting;
- the temporary-folder prefix became `<TMPDIR>`; the lock keeps its date, not its hour; the patch header lost its
  date and commit id while its subject and diff stayed byte-identical;
- the ledger reading copy (`runs/study2-audit/ledger-entries.json`) dropped the raters' answer times and the
  language remark; entry numbers, times, attachment hashes and the `hash` field are as recorded.

For the four study 2 files (`items.jsonl`, `items.pt.json`, `labels-ulisses.json`, `labels-rater2.json`),
`tests/test_study2_audit.py` checks both the ledger's original hashes and the derivatives' own hashes; the other
shipped bytes are covered by the release manifest only. Every published number is unchanged. [`REPRODUCIBILITY.md`](../../REPRODUCIBILITY.md) lists each derivative and what
was replaced. The second rater agreed to the publication of their labels under the name `rater2`.

## Alternatives considered

- **Publish the originals.** Exposes the raters' activity times.
- **Re-record new ledger entries for the redacted files.** The ledger is append-only and public; a new entry
  would not change what the old one attests.

## Consequences

- For the redacted files, the hash recorded in the ledger no longer matches the published bytes. The originals
  are kept privately by the author; the test of the original hashes documents what was recorded.
- Two sealed files still say "flight pause" for a network pause; they are kept as sealed, and the deviation is
  stated.

## References

- [`REPRODUCIBILITY.md`](../../REPRODUCIBILITY.md), "Public derivatives"
- [`tests/test_study2_audit.py`](../../tests/test_study2_audit.py)
