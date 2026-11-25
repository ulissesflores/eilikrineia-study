# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Carlos Ulisses Flores (Codex Hash Ltda.)
"""Print the study 3 audit split by arm and hidden-check result.

The study 3 audit split by arm and hidden-check result (formerly the paper's Table B1, moved out of
the paper). Computed for this paper; descriptive. Per arm x hidden-check result (20 messages each)
and model rater: both "complete" / labeller only / rater only / neither, on "complete" against the
rest.

Gate: the printed cells equal the paper's former Table B1 (asserted).

Inputs
------
- The frozen labels in the package: runs/study3-audit/key.jsonl and the rater files fable.json,
  grok.json and hydrogen.json (needs the package only).

Outputs
-------
- Per arm and hidden-check result, the agreement cells for each model rater on standard output; the
  committed posthoc/b1_split.txt must be reproduced byte for byte.

Usage
-----
    PYTHONDONTWRITEBYTECODE=1 python posthoc/b1_split.py

Status
------
Post hoc, exploratory, not preregistered (2026-11-24). The numbers it backs are listed in
posthoc/paper_numbers.json.

Author
------
Carlos Ulisses Flores, ORCID https://orcid.org/0000-0002-6034-7765

Repository
----------
https://github.com/ulissesflores/eilikrineia-study
"""

import json
from pathlib import Path

# the package root; raw/ = <RAW>, the unpacked raw archive
PKG = Path(__file__).resolve().parent.parent
A = PKG / "runs" / "study3-audit"
key = [json.loads(x) for x in (A / "key.jsonl").read_text().splitlines()]
raters = {r: json.loads((A / f"{r}.json").read_text()) for r in ("fable", "grok", "hydrogen")}
B1 = {
    ("S", False): ("4/2/1/13", "6/0/5/9", "5/1/6/8"),
    ("S", True): ("2/2/3/13", "3/1/4/12", "3/1/6/10"),
    ("I", False): ("11/2/2/5", "12/1/5/2", "13/0/3/4"),
    ("I", True): ("3/4/5/8", "4/3/4/9", "5/2/5/8"),
    ("K", False): ("8/1/2/9", "8/1/4/7", "8/1/3/8"),
    ("K", True): ("3/3/1/13", "2/4/3/11", "4/2/3/11"),
    ("TD", False): ("11/0/2/7", "11/0/4/5", "11/0/1/8"),
    ("TD", True): ("11/0/4/5", "10/1/3/6", "11/0/5/4"),
}
print(
    "== Study 3 audit by arm and hidden-check result (both / labeller only / rater only / neither)"
)
for arm in ("S", "I", "K", "TD"):
    for passed in (False, True):
        items = [k for k in key if k["arm"] == arm and k["check_passed"] == passed]
        cells = []
        for r in ("fable", "grok", "hydrogen"):
            c = [0, 0, 0, 0]
            for k in items:
                lab = k["labeller"] == "complete"
                rat = raters[r][str(k["id"])]["label"] == "complete"
                c[{(1, 1): 0, (1, 0): 1, (0, 1): 2, (0, 0): 3}[(lab, rat)]] += 1
            cells.append("/".join(map(str, c)))
        assert tuple(cells) == B1[(arm, passed)], (arm, passed, cells)
        print(
            f"  {arm}, {'passed' if passed else 'failed'} ({len(items)}): Fable {cells[0]}; Grok "
            f"{cells[1]}; Hydrogen {cells[2]}"
        )
print("gate: equal to the former Table B1")
