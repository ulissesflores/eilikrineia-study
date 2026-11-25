# 0014. Every number the paper prints is mapped to its output and checked

- Status: accepted
- Date: 2026-11-24

## Context

[0004](0004-published-numbers-as-tests.md) locks the headline numbers of the results documents and the README as
test assertions. The paper prints many more: every estimate, interval, count and post hoc figure, several hundred in
all, some read from the frozen `runs/` outputs and some from the post hoc outputs. A reader who wants to check one
has to find the file and the line that prints it, and nothing fails if the paper and the outputs drift apart. The
tests of 0004 live in `tests/`, which is inside the seal; adding to them would change the `chain_hash` of version
1.0.0.

## Decision

- `posthoc/paper_numbers.json` holds one entry per number group the paper prints: the section or table, the quoted
  context, the value as printed, the script that produces it, the committed output file, a line anchor (with the
  number of lines it must match, so an ambiguous anchor fails) and the rule that turns the number in that line into
  the printed value (equal, rounded, percentage, one side of a fraction, and so on). A figure the paper computes from
  several outputs is a `derived` entry with its formula. Figures with no committed script are listed under
  `unscripted` with the reason, and are never counted as checked. The manifest also records the SHA-256 of every
  script and output it uses.
- `posthoc/verify_paper_numbers.py` checks those hashes and every value; with `--rerun` it also reruns each post hoc
  script and compares its output with the committed one byte for byte, skipping, with the reason, the scripts whose
  inputs (the raw archive, a ledger clone, external tools) are absent.
- `posthoc/test_paper_numbers.py` runs the same checks as tests, plus a test that the checker rejects a changed
  value. It sits in `posthoc/`, not `tests/`, so the seal is unchanged. A further test checks each quoted context
  against the paper's source text when `EILIKRINEIA_PAPER` points to it; it is skipped otherwise.
- The manifest names the paper version it describes (`paper_version`). A change to a printed number goes through the
  manifest and the tests in the same change.

## Alternatives considered

- **Add the checks to `tests/` and reissue the seal.** Breaks the continuity of the `chain_hash` that the ledger and
  the paper cite (see [0012](0012-post-hoc-supplement-outside-the-seal.md)).
- **Extract the numbers from the paper's PDF.** Layout and typography make the extraction fragile, and a missed
  number would pass silently; the manifest states each one explicitly.
- **Check only the headline numbers, as 0004 does.** Leaves most printed figures without a check.

## Consequences

- A reader can go from any number in the paper to the line that prints it, and rerun the script.
- A hash match shows that the files are the ones described, and a rerun shows that the script prints that output.
  Neither shows that the analysis is the right one; that remains the paper's argument.
- The manifest must be updated with every edit of a printed number, or the tests fail. That is the intended cost.

## References

- [`posthoc/README.md`](../../posthoc/README.md)
- [0004](0004-published-numbers-as-tests.md), [0012](0012-post-hoc-supplement-outside-the-seal.md),
  [0013](0013-second-post-hoc-increment-public-archive-only.md)
