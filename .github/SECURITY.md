# Security and privacy

This repository is a replication package: it runs no service and holds no credentials
apart from one declared experimental signing key (below). Two kinds of report still matter.

## What to report

- **A credential or private key** anywhere in this repository or in the raw trial archive
  ([10.5281/zenodo.24450523](https://doi.org/10.5281/zenodo.24450523)). One private key is shipped on purpose:
  `template3/ledger/private/keys/agent`, a throwaway key that signs nothing
  outside the experiment. In study 3 the agents of the arms with the record tool and a signed ledger (S, K and TD)
  had it; the I arm had no tool (see [`REPRODUCIBILITY.md`](../REPRODUCIBILITY.md)).
- **Personal data** of the author or of anyone else that the redaction missed: names, contact details, account
  data, file listings of a personal machine, activity times. What was removed and what was knowingly left is listed
  in the raw archive's README, `REDACTIONS.tsv` and `FIELDS-REMOVED.tsv`, and in
  [`REPRODUCIBILITY.md`](../REPRODUCIBILITY.md), "Known limits".

## How to report

Do not open a public issue. Use GitHub's private vulnerability report form:
<https://github.com/ulissesflores/eilikrineia-study/security/advisories/new>.
Please name the file, the line or trial, and what it exposes.

## What happens next

The aim is to acknowledge a report within seven days. A confirmed exposure is removed in a new version of the package or
of the data record, the removal is logged as in [ADR 0008](../docs/adr/0008-redact-log-audit.md), and an exposed
credential under the author's control is revoked; the issuer is told of any other. Older versions that still serve the file are
restricted or removed where Zenodo allows it. Treat what was published as permanent: copies already downloaded stay out of the author's control, even if a record is later removed or
restricted.
