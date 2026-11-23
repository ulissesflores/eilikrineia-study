# Contributing

This package is the record of four experiments that have already run. It is not developed further in the usual
sense, but it can be corrected, checked and extended.

## Reporting an error

Open an issue with the file and line, what it says, what it should say and how you know (a command and its
output is best). Errors in a number are checked against the frozen outputs under `runs/` first.

Corrections follow the rules the documents already follow:

- A sealed file (anything listed in [`output/hash-chain.md`](../output/hash-chain.md)) is not edited in place.
  A correction to a plan or a result goes in a new dated file at the root named `DEVIATION*.md` or `POSTHOC*.md`
  (both patterns are in the seal). Then run `python make_provenance.py` to write the new seal and
  `python run_all.py` to check it.
- Reader material (README files, `REPRODUCIBILITY.md`, `docs/`) can be fixed directly. A change that touches a
  number must keep the English README and the four translations identical in their digit strings, or the translation test fails; the sentence around the number needs a read, which the test cannot do.

## Replicating

A replication that runs new trials is a new study, not a fix to this one. If you run one, cite this package and
the raw data record, and say what you changed (model, client version, tasks, environment). An issue linking to it
is welcome.

## Pull requests

- Run `python run_all.py` before opening one; it must end with `provenance verified`.
- Lint covers the code written for the package: `ruff format --check . && ruff check . && interrogate -c pyproject.toml .`
- Code under `runner/`, `td/`, `template*/`, `overclaim/`, `rescore/` and `patches/` is kept as it was fixed
  and is not reformatted (see [ADR 0003](../docs/adr/0003-sealed-files-shipped-byte-for-byte.md)).
- Contributions are accepted under the licence of the part they touch (see [`NOTICE`](../NOTICE)).

Privacy or credential problems go through [`SECURITY.md`](SECURITY.md), not a public issue.
