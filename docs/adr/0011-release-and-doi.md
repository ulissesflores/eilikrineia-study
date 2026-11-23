# 0011. A release candidate mints the DOI; the concept DOI is the citation anchor

- Status: accepted
- Date: 2026-11-23

## Context

Zenodo creates a deposit, and a DOI, when a GitHub release is published, not when a commit is pushed or a tag is
created. A published deposit is treated as permanent. If the first citable version were released before its DOI
existed, its files could not carry that DOI, and a second version would be needed only to add it.

## Decision

1. The repository went public with no release, version `1.0.0` in the metadata and CI green.
2. The GitHub-Zenodo integration was switched on for this repository.
3. `v1.0.0-rc1` was published as a pre-release. Zenodo deposited it: version DOI
   [10.5281/zenodo.24471762](https://doi.org/10.5281/zenodo.24471762), concept DOI
   [10.5281/zenodo.24471761](https://doi.org/10.5281/zenodo.24471761).
4. The concept DOI was written into the README badge and BibTeX, `CITATION.cff` (`doi`, `identifiers`,
   `preferred-citation`), `codemeta.json` (`identifier`) and the citation section of each README. In the
   machine-readable citation metadata, the rc1 version DOI appears only in `CITATION.cff` `identifiers`.
5. `v1.0.0` is then released from that commit, and Zenodo gives it its own version DOI under the same concept.

## Alternatives considered

- **Reserve a DOI by hand on Zenodo.** Gives a DOI that is not linked to the GitHub release that holds the code.
- **Cite the version DOI.** Pins readers to one version; the concept DOI always resolves to the latest.

## Consequences

- The rc1 stays on GitHub and on Zenodo as the record of how the DOI was obtained.
- Zenodo first labelled the rc1 deposit version "1.0.0", because it reads the version from `.zenodo.json`; the
  label was changed to "1.0.0-rc1" by a metadata edit before the final release (the DOI is unchanged). Between
  rc1 and the final release the files differ by the DOIs, the added architecture, decision records and the
  security and contributing policies, the re-recorded demo GIFs, the reworded labeller limit and the disclosures
  added to [`REPRODUCIBILITY.md`](../../REPRODUCIBILITY.md).

## References

- [`CITATION.cff`](../../CITATION.cff), [`codemeta.json`](../../codemeta.json), [`.zenodo.json`](../../.zenodo.json)
