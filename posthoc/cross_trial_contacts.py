# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Carlos Ulisses Flores (Codex Hash Ltda.)
"""Print the first transcript line of each 'contact' trial, with context.

The contact trials are the trial-id-* rows of cross-trial-reads.tsv. The context lets the
description of contact trials be checked. The raw archive is read only.

Inputs
------
- posthoc/cross-trial-reads.tsv.
- The raw archive <RAW> (environment variable EILIKRINEIA_RAW, default raw/), the unpacked archive,
  read only.

Outputs
-------
- The first transcript line of each contact trial, with context, on standard output; the committed
  posthoc/cross_trial_contacts.txt must be reproduced byte for byte.

Usage
-----
    PYTHONDONTWRITEBYTECODE=1 python posthoc/cross_trial_contacts.py

Status
------
Post hoc, exploratory, not preregistered. The numbers it backs are listed in
posthoc/paper_numbers.json.

Author
------
Carlos Ulisses Flores, ORCID https://orcid.org/0000-0002-6034-7765

Repository
----------
https://github.com/ulissesflores/eilikrineia-study
"""

import csv
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # never write .pyc into the sealed runner/ folder
HERE = Path(__file__).resolve().parent
PKG = HERE.parent  # the package root: run from there, the paths below are relative to it
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))  # <RAW>: the raw trial archive, unpacked
TSV = HERE / "cross-trial-reads.tsv"
# the host's per-user temp prefix (macOS /private/var/folders/<xx>/<hash>/T/ or
# /var/folders/...) is machine-specific: replace it by <TMPDIR> before the excerpt is cut, so the
# trial id after it stays and the prefix never is printed
TMP_PREFIX = re.compile(r"(?:/private)?/var/folders/[^/\\\s\"]+/[^/\\\s\"]+/T/")
rows = [r for r in csv.DictReader(open(TSV), delimiter="\t") if r["kind"].startswith("trial-id-")]
seen = {}
for r in sorted(rows, key=lambda r: (r["trial"], int(r["line"]))):
    seen.setdefault(r["trial"], r)
print(f"contact trials: {len(seen)}")
for t, r in seen.items():
    line = (RAW / t / "agent.stdout").read_text(errors="replace").splitlines()[int(r["line"]) - 1]
    line = TMP_PREFIX.sub("<TMPDIR>/", line)
    i = line.find(TMP_PREFIX.sub("<TMPDIR>/", r["foreign_trial_id_or_path"]))
    print(
        f"{t} | line {r['line']} | {r['kind']} | ...{line[max(0, i - 110) : i + 50]}...".replace(
            "\\n", " "
        )
    )
