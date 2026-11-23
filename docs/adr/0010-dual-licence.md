# 0010. Code under Apache-2.0, documents and data under CC BY 4.0

- Status: accepted
- Date: 2026-11-14

## Context

The package mixes code (the trial runner, analyses, tests, figures as code), documents and data (plans, results,
per-trial scores, frozen outputs, pictures) and third-party files (the sealed subset of the overclaim benchmark).
One licence does not fit all three: a software licence is awkward for prose and data, and a content licence
lacks the patent terms expected for code.

## Decision

- Source code: **Apache-2.0** ([`LICENSE`](../../LICENSE), [`LICENSES/Apache-2.0.txt`](../../LICENSES/Apache-2.0.txt)).
  `.zenodo.json` declares it as the licence of the deposit; its notes describe the split.
- Documents, data and pictures: **CC BY 4.0** ([`LICENSES/CC-BY-4.0.txt`](../../LICENSES/CC-BY-4.0.txt)).
- Third-party files under `overclaim/`, `rescore/` and `patches/`: **MIT**, as upstream
  ([`overclaim/LICENSE`](../../overclaim/LICENSE)).
- [`NOTICE`](../../NOTICE) maps each folder to its licence, including the split inside the ledger templates
  (the ledger tool is code, its entries, keys and texts are data).

## Alternatives considered

- **MIT for everything.** Simple, but applies a software licence to plans and data.
- **CC BY 4.0 for everything.** Creative Commons advises against it for software.

## Consequences

- `CITATION.cff`, `codemeta.json` and `.zenodo.json` declare Apache-2.0, the licence of the deposit, and the
  notes of `.zenodo.json` state the split.

## References

- [`NOTICE`](../../NOTICE)
