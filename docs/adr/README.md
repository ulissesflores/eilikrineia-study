# Architecture decision records

Each record states one decision about how this package was built: the context, the decision, the alternatives that
were weighed and what follows from it. The format follows
[MADR](https://adr.github.io/madr/) in a short form. Dates are those of the decision, in 2026.

Scientific decisions (hypotheses, arms, sample sizes, decision rules, exclusions) are not repeated here: they are
the preregistrations at the root of the repository, which are dated and sealed. These records cover the
engineering of the package around them.

| No. | Decision | Date | Status |
| --- | --- | --- | --- |
| [0001](0001-one-chain-hash-seal.md) | One SHA-256 chain hash seals code, documents, data and tests | 11-14 | accepted |
| [0002](0002-two-seals.md) | Two seals: a reproducible derivation and frozen evidence | 11-14 | accepted |
| [0003](0003-sealed-files-shipped-byte-for-byte.md) | Sealed files are shipped byte for byte; packaging stays outside the seal | 11-14 | accepted |
| [0004](0004-published-numbers-as-tests.md) | Headline numbers are test assertions, in every language | 11-14 | accepted |
| [0005](0005-rerun-registered-analyses.md) | The registered analyses of studies 2 and 3 are rerun from the frozen scores | 11-22 | accepted |
| [0006](0006-pinned-container-for-study-3.md) | Study 3 ran in a container image pinned by digest | 11-08 | accepted |
| [0007](0007-raw-archive-as-separate-record.md) | The raw trial archive is a separate data record with its own DOI | 11-22 | accepted |
| [0008](0008-redact-log-audit.md) | Personal data is removed, every removal is logged, and another model audits | 11-22 | accepted |
| [0009](0009-public-derivatives.md) | Redacted public copies of ledger-recorded files, with both hashes tested | 11-23 | accepted |
| [0010](0010-dual-licence.md) | Code under Apache-2.0, documents and data under CC BY 4.0 | 11-14 | accepted |
| [0011](0011-release-and-doi.md) | A release candidate mints the DOI; the concept DOI is the citation anchor | 11-23 | accepted |
| [0012](0012-post-hoc-supplement-outside-the-seal.md) | Post hoc analyses ship as a supplement outside the seal | 11-23 | accepted; last clause superseded by 0013 |
| [0013](0013-second-post-hoc-increment-public-archive-only.md) | A second post hoc increment, run on the public archive only; two checks stay out | 11-24 | accepted |
| [0014](0014-paper-numbers-manifest-and-test.md) | Every number the paper prints is mapped to its output and checked | 11-24 | accepted |
| [0015](0015-ci-and-colab-from-a-pinned-version.md) | Continuous integration and a Colab notebook rerun the package from a pinned version | 11-24 | accepted |

A new decision gets the next number. A record is never rewritten: a later decision that replaces it says so, and
the earlier record's status becomes "superseded by NNNN".
