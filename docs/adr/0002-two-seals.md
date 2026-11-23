# 0002. Two seals: a reproducible derivation and frozen evidence

- Status: accepted
- Date: 2026-11-14

## Context

The trials were model calls made on dated days. Running them again gives a new sample, not a reproduction. What
can be reproduced is the path from the frozen per-trial scores to every published number. A package that blurs
the two either promises a reproduction it cannot deliver or hides the part that can be checked.

## Decision

The package states two seals and keeps them apart ([`REPRODUCIBILITY.md`](../../REPRODUCIBILITY.md)):

1. **The derivation is reproducible.** `python run_all.py` recomputes the counts, reruns the analyses of the pilot and of
   studies 1 to 3 from the frozen scores, runs the tests and verifies the `chain_hash`, with no model call and no network
   (Track 1, in CI).
2. **The evidence is frozen.** The preregistrations, the study 3 pins with RFC 3161 and OpenTimestamps proofs,
   the frozen analysis outputs and the answers of the model raters are shipped as they were fixed (the redacted
   derivatives of [0009](0009-public-derivatives.md) excepted), and a test checks the 114 files pinned before
   study 3 ran. Later documents and audits are attested by their own, later ledger entries, not by those pins.

Rescoring and reanalysing saved trials from the raw transcripts is Track 2: it needs the raw archive
([0007](0007-raw-archive-as-separate-record.md)). Rerunning the hidden checks is a separate task; for study 3
it also needs the pinned image ([0006](0006-pinned-container-for-study-3.md)); the image itself is
not shipped, only `container/Containerfile` and the recorded digest.

## Alternatives considered

- **A Docker "reproduce everything" target.** Would call the model again and produce a different sample under a
  name that suggests the same one.
- **Ship only the derivation.** Drops the evidence that the plans came before the data.

## Consequences

- Each claim of reproducibility in the README names which seal it rests on.
- "What cannot be re-run" is a section of its own: the trials, scoring across Python versions, the model raters.

## References

- [`REPRODUCIBILITY.md`](../../REPRODUCIBILITY.md), [`prereg/study3/pins.txt`](../../prereg/study3/pins.txt)
