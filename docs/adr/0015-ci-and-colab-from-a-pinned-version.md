# 0015. Continuous integration and a Colab notebook rerun the package from a pinned version

- Status: accepted
- Date: 2026-11-24

## Context

The seal, the tests and the paper-number checks only help a reader who runs them. A reviewer reading the paper
should be able to see a public record of them passing, and to run them without installing anything. The paper cites
one version of the repository, so whatever a reader runs has to be that version, not whatever the main branch holds
later. Part of the post hoc supplement needs the raw archive (0.5 GB compressed, about 2.5 GB unpacked), which is a
separate record on Zenodo.

## Decision

- `.github/workflows/ci.yml` runs on every push and pull request, on Python 3.11 and 3.12: verify the seal
  (`make_provenance.py --verify`), `run_all.py` (rerun the analyses from the frozen scores, the tests of
  [0004](0004-published-numbers-as-tests.md), the seal again), the post hoc checksums (`posthoc/SHA256SUMS`), the
  paper-number tests and the verifier with `--rerun` (see [0014](0014-paper-numbers-manifest-and-test.md)). The
  scripts that need the raw archive are skipped there, with the reason. A separate lint job checks the packaging
  code; the sealed code and `posthoc/` are excluded because they are shipped as they ran
  ([0003](0003-sealed-files-shipped-byte-for-byte.md)).
- `colab/replication.ipynb` clones the repository at a constant `REF` (the paper pins a tag or commit there),
  installs the one requirement, verifies the seal, runs `run_all.py`, the paper-number tests and the verifier, and
  shows each printed value beside the value in its output with a match column; the figures with no script are listed
  separately. An optional step downloads the raw archive from its Zenodo record, checks its SHA-256 against the
  record's `SHA256SUMS`, unpacks it, clones the public ledger and reruns every post hoc script. The notebook says at
  the top what it cannot reproduce (the model calls of the trials) and why.
- The committed notebook has no outputs. Environment variables (`EILIKRINEIA_NB_*`) let an automated test run point
  it at a local clone and a local copy of the archive; a reader leaves them unset.

## Alternatives considered

- **Run the raw-archive part in CI.** Every push would download 0.5 GB from Zenodo and depend on its availability;
  the part that needs only the repository already covers every frozen output and every hash. The raw part is in the
  notebook's optional step instead.
- **Binder or a container image.** Another service to maintain, slower to start, and the package needs only
  `pytest`.
- **Point the notebook at the main branch only.** A reader would check a version other than the one the paper cites.

## Consequences

- The CI log is a public record of the seal and the number checks on Linux, for each push.
- The notebook checks the version the paper cites as long as `REF` is updated when the paper pins one; with `"main"`
  it checks the latest version.
- `posthoc/prereg_chronology.py` reads the live public ledger, so its rerun in the notebook can differ if that
  history is ever rewritten; that is reported as a difference, not hidden.
- A manual workflow, `.github/workflows/raw-archive.yml` (`workflow_dispatch`, added 2026-11-24), downloads the raw
  archive from Zenodo (record 24450523), checks it against the archive's `SHA256SUMS`, clones the public ledger and
  reruns all 26 post hoc scripts, failing if any is skipped or prints a different output. Its run log is the public
  record of the heavy run; GitHub keeps Actions logs for a limited time (90 days by default).

## References

- [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), [`.github/workflows/raw-archive.yml`](../../.github/workflows/raw-archive.yml), [`colab/replication.ipynb`](../../colab/replication.ipynb)
- [0003](0003-sealed-files-shipped-byte-for-byte.md), [0004](0004-published-numbers-as-tests.md),
  [0014](0014-paper-numbers-manifest-and-test.md)
