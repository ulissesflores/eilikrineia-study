# 0007. The raw trial archive is a separate data record with its own DOI

- Status: accepted
- Date: 2026-11-22

## Context

The raw trial folders (transcripts, tool outputs, hidden-check outputs, signed ledgers) are about 3.6 GB
uncompressed and 144,609 files. Track 2 needs them; Track 1 does not. Git hosting is a poor fit for that size:
Git LFS has a monthly bandwidth quota charged to the owner, and, depending on settings, clones and downloads could
carry data most readers never open.

## Decision

The raw archive is published as its own Zenodo record,
[10.5281/zenodo.24450523](https://doi.org/10.5281/zenodo.24450523): one deterministic `tar.gz` (fixed file times,
owner and modes, so the same tree gives the same bytes), a `SHA256SUMS` file, a `filelist.txt` and a README that
lists every change made before publication. The package links to it from `CITATION.cff` (`references`),
`codemeta.json` (`relatedLink`) and `.zenodo.json` (`isSupplementedBy`). The archive unpacks under `raw/`, a
folder outside the seal and ignored by git.

## Alternatives considered

- **Git LFS in this repository.** Quota and cost fall on the owner; depending on how LFS files are archived, the
  archive could enter the Zenodo snapshot of each release.
- **Attach the archive to the GitHub release.** Ties the data's identifier to the package version; the data does
  not change when the package does.
- **Not publishing the raw data.** Leaves Track 2 and every claim about transcripts uncheckable.

## Consequences

- The package and the data have separate DOIs and separate versions; a corrected package does not republish
  half a gigabyte.
- The archive carries its own checksum file and is outside the `chain_hash` of the package.

## References

- [`REPRODUCIBILITY.md`](../../REPRODUCIBILITY.md), "Track 1 (light) and Track 2 (complete)"
- [0008](0008-redact-log-audit.md) for what was removed before publication
