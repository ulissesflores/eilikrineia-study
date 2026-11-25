# 0013. A second post hoc increment, run on the public archive only; two checks stay out

- Status: accepted (replaces the last clause of [0012](0012-post-hoc-supplement-outside-the-seal.md), "the
  supplement is frozen with that increment")
- Date: 2026-11-24

## Context

[0012](0012-post-hoc-supplement-outside-the-seal.md) closed the post hoc supplement after its first increment and said
that a later analysis would be a separate decision. The paper's draft then listed, in its Table 11, ten more checks as
"next version" and two as not reproducible from the package. A number in the paper whose script is not public
cannot be checked by a reader, so either the ten checks get public scripts or their numbers leave the paper. Their
first versions ran on the author's working folders, which hold files that are not published (unredacted trial
folders, private keys, the reading aid's suggestion files).

## Decision

- The supplement is reopened once, for those ten checks: `not_verified.py`, `study2_preoutage.py`,
  `td_secondary.py`, `claim_counts.py`, `gap_checks.py`, `ledger_content.py`, `sdt_bootstrap.py`, `ledger_share.py`,
  `power_543.py` and `b1_split.py`, each with its committed output, in `posthoc/` and outside the seal, under the
  rules of 0012.
- Every one of them reads only the package and the public, redacted raw archive
  ([10.5281/zenodo.24450523](https://doi.org/10.5281/zenodo.24450523); `EILIKRINEIA_RAW`, default `raw/`). They
  were changed from the author's copies only in how they find the package, in where they import their two sibling
  scripts from, and in their docstrings. Their outputs on the public archive, with Python 3.11 and 3.12, are
  byte-identical to the author's first run.
- Two checks are not shipped, and `posthoc/README.md` ("Excluded") says why: `audit_assist.py` reads the reading
  aid's suggestion files and their creation times on the author's machine, and `keys_count.py` counts the private
  key files of the unredacted trial folders. Neither input is published, and the published archive cannot rebuild
  either count. The paper marks both as not reproducible from the package.
- The supplement is frozen again with this increment. A reviewer's request for a further analysis becomes either a
  limit stated in the paper or a new version of the package that goes through the same steps (public script, public
  inputs, committed output, entry in `posthoc/paper_numbers.json`, see
  [0014](0014-paper-numbers-manifest-and-test.md)).

## Alternatives considered

- **Ship the scripts as they ran, reading the working folders.** A reader could not run them, and their paths and
  inputs would expose files the redaction removed.
- **Rebuild the two excluded counts from what is published.** The published archive keeps only public keys and has
  no creation times of the aid's files, so the rebuilt numbers would be different numbers presented as the same.
- **Drop the ten numbers from the paper.** Loses checks the reviews asked for, when public inputs suffice for them.

## Consequences

- Every post hoc number in the paper, except the two excluded checks and the figures listed under `unscripted`, has
  a public script that a reader can rerun on public data.
- Six of the ten need the raw archive (0.5 GB compressed, about 2.5 GB unpacked); continuous integration reruns only
  the four that need the package alone (see [0015](0015-ci-and-colab-from-a-pinned-version.md)).

## References

- [`posthoc/README.md`](../../posthoc/README.md), "What is here" and "Excluded"
- [0012](0012-post-hoc-supplement-outside-the-seal.md)
