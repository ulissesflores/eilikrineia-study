# 0004. Headline numbers are test assertions, in every language

- Status: accepted
- Date: 2026-11-14

## Context

The numbers of a study travel: from the analysis output to the results document, the README, the one-page
summary, four translations and the paper. Each copy is a chance for a number to drift from the data, and a
reviewer who finds one wrong number has reason to doubt the rest.

## Decision

`tests/test_published_numbers.py` and `tests/test_study2_audit.py` lock the headline numbers and selected strings:

- counts are recomputed from the per-trial CSV files and asserted;
- selected estimates with an interval must be the line printed in the frozen analysis output, and the
  exploratory intervals are asserted against `output/results.json`;
- the results documents, the README and `docs/findings.md` must contain selected strings among them;
- each translated README must carry exactly the multiset of digit strings of the English one, separators ignored
  (a changed or missing number is caught; two numbers swapped between claims are not, so a change to a number
  also needs a read of the sentence around it);
- the 114 files pinned before study 3 must hash to the pinned values, and a scan for the private-key marker in
  files under 10 KB must find only the one throwaway trial key (it does not look for other kinds of credential).

The tests are part of the `chain_hash` ([0001](0001-one-chain-hash-seal.md)), so they cannot be loosened
without resealing.

## Alternatives considered

- **Generate the README from a template.** Moves the drift into the template and makes the prose harder to read
  and translate.
- **Check only the results documents.** The README is what most readers see.

## Consequences

- A sentence in any language that changes a digit string fails CI until every page agrees.
- Adding a number to the README means adding it, identically, to the four translations.

## References

- [`tests/test_published_numbers.py`](../../tests/test_published_numbers.py),
  [`tests/test_study2_audit.py`](../../tests/test_study2_audit.py)
