# 0008. Personal data is removed, every removal is logged, and another model audits

- Status: accepted
- Date: 2026-11-22 (archive), 2026-11-23 (repository)

## Context

The agents of the host-run studies could read the author's machine ([0006](0006-pinned-container-for-study-3.md)),
and the transcripts recorded what they saw. The agent client also wrote account metadata into its output stream.
Anything published on Zenodo should be treated as permanent, since copies already downloaded stay out of the author's control even if a record is later removed or restricted, so anything personal that goes out stays out. Keeping the raw
data untouched protects its integrity but exposes the author; editing it silently protects the author but breaks
the evidence.

## Decision

Before anything was published, even as a draft:

1. **Secrets.** `gitleaks` over the directory and over every decompressed archive inside it, and a broad pattern
   search for tokens and private keys. Every hit was read in context. No credential was found; the 10,206 private
   signing keys of the trial ledgers were removed and the public keys kept, so the signatures can still be checked.
2. **Privacy.** A search by category: listings of the home directory and its settings folders, text read from
   personal files, process lists, names of other projects, contact data, file owners, local times and time zone,
   account metadata of the agent client.
3. **Removal, not exposure.** Each affected tool output was replaced by a marked notice, and each removed metadata
   field is listed per file. The archive ships `REDACTIONS.tsv` (trial, file, line, tool call, rule) and
   `FIELDS-REMOVED.tsv`.
4. **An independent audit.** A model from another vendor was asked, with an open brief and without our list of
   patterns, to find anything personal or sensitive. The findings of each audit pass were fixed or declared before the
   next pass: five passes for the archive, four for this repository.
5. **Re-verification.** After every pass: the signed ledgers are byte-identical, the final messages and the scores
   are unchanged, and the study 2 and study 3 analyses reproduce from the redacted archive.

## Alternatives considered

- **Publish the raw data as it is.** Rejected: it exposed the author's machine and account.
- **Publish scores only.** Leaves every transcript claim uncheckable.
- **Rely on the author's own search.** The author knows what to look for and also what they expect not to find;
  the audit exists to catch the second kind of miss.

## Consequences

- What remains is declared in the archive's README: the author's public handle, the machine's architecture and
  toolchain strings, the time zone that local times imply, estimated list-price costs per run, and excerpts of
  open-source files that agents printed.
- The integrity of the raw data rests on the redaction log plus the unchanged ledgers, scores and analyses, not on
  byte identity with what the machine wrote.

## References

- Raw archive README, `REDACTIONS.tsv` and `FIELDS-REMOVED.tsv` in
  [10.5281/zenodo.24450523](https://doi.org/10.5281/zenodo.24450523)
- [`REPRODUCIBILITY.md`](../../REPRODUCIBILITY.md), "Known limits of this package"
