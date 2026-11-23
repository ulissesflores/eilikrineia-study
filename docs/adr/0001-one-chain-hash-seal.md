# 0001. One SHA-256 chain hash seals code, documents, data and tests

- Status: accepted
- Date: 2026-11-14

## Context

A reader of a replication package needs to know that the code, the dated documents and the frozen data in front
of them are the ones the published numbers came from, and needs to check it without trusting the author or a
hosting service. Per-file checksums answer "is this file intact" but not "is this the whole set": a file can be
added without any checksum failing.

## Decision

`make_provenance.py` hashes every file under the sealed folders (`runner/`, `runs/`, `prereg/`, `td/`,
`template/`, `template3/`, `container/`, `patches/`, `rescore/`, `overclaim/`, `tests/`, `scripts/`) and the root
files `PREREGISTRATION*.md`, `RESULTS*.md`, `DEVIATION*.md`, `POSTHOC*.md`, `run_all.py`, `make_provenance.py` and
`output/results.json`, skipping cache folders and `.DS_Store`. It sorts them by path and folds the lines
`<sha256>  <path>` into one SHA-256, the `chain_hash`. It writes `output/provenance.json` (every file and its hash)
and `output/hash-chain.md` (the same, for reading). `python make_provenance.py --verify` recomputes the hashes and
compares them with `output/provenance.json` (not with `output/hash-chain.md`); on a difference it exits with an
error and names up to 20 files, whether changed, missing or added. It uses the standard library only. A manifest
and the files it lists could be replaced together, so the check shows that this copy matches the manifest; that
the manifest is the published one rests on the release and the Zenodo deposit.

## Alternatives considered

- **Per-file checksums only (`SHA256SUMS`).** Detects a changed or missing file; an added file goes unnoticed unless
  the list is also compared with the folder, which is what the seal does.
- **A Merkle tree with per-folder roots.** Allows proving one file without the others, which no reader of this
  package needs; more code to review for the same guarantee.
- **Signing the seal with the author's key.** Adds a key-management dependency. The `chain_hash` is instead
  anchored by the commit, the GitHub release and the Zenodo deposit.

## Consequences

- One string identifies the sealed state; the README, the CI and the deposit can all cite it.
- Anything that varies by machine (figures, lockfile, caches) stays outside the seal, so it verifies on any
  machine. The "Informational (NOT hashed)" section of `output/hash-chain.md`,
  written by the sealed generator, names `output/` as a whole; `output/results.json` is nonetheless hashed and
  appears in the file list of the same report.
- Any change to a sealed file, even a comment, changes the `chain_hash` and is resealed with
  `python make_provenance.py`; `python run_all.py` checks the seal and leaves the seal files untouched. CI verifies the
  committed seal before the full rerun.

## References

- [`make_provenance.py`](../../make_provenance.py), [`output/hash-chain.md`](../../output/hash-chain.md)
- [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)
