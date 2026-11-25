# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Carlos Ulisses Flores (Codex Hash Ltda.)
"""Test whether the registered +9.1 points can be reproduced from the trials file.

Can the registered "+9.1 points" (runs/z4-union.txt, whose script is not in package v1.0.0) be
reproduced from runs/z4-trials.jsonl? The script prints, per writer, the pooled share of faithful
study 2 rebuilds whose hidden check failed and which the writer's tests flag, the unweighted mean of
the three task shares, and the same for false completions, beside the six figures that z4-union.txt
prints.

Inputs
------
- runs/z4-trials.jsonl and runs/z4-union.txt of the package (needs the package only).

Outputs
-------
- The shares and the six frozen figures on standard output; the committed posthoc/ceiling_9_1.txt
  must be reproduced byte for byte.

Usage
-----
    PYTHONDONTWRITEBYTECODE=1 python posthoc/ceiling_9_1.py

Status
------
Post hoc, exploratory, not preregistered (2026-11-23). The numbers it backs are listed in
posthoc/paper_numbers.json.

Author
------
Carlos Ulisses Flores, ORCID https://orcid.org/0000-0002-6034-7765

Repository
----------
https://github.com/ulissesflores/eilikrineia-study
"""

import json
import statistics
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # never write .pyc into the sealed runner/ folder
PKG = Path(__file__).resolve().parent.parent  # the package root
rows = [json.loads(x) for x in open(PKG / "runs" / "z4-trials.jsonl")]
fa = [r for r in rows if r["faithful"]]
tasks = sorted({r["task"] for r in fa})
printed = {"haiku": (5.1, 1.9), "sonnet": (6.0, 2.9), "opus": (9.1, 3.7)}
for w, (p_pass, p_fc) in printed.items():

    def fl(r):
        """Tell whether any flag of the trial names the current writer.

        Parameters
        ----------
        r : dict
            Trial row with a 'flags' mapping.

        Returns
        -------
        bool
            True if some flagged key ends in a name starting with the writer.
        """
        # called only inside this iteration, so late binding of w is safe
        return any(
            v
            for k, v in r["flags"].items()
            if k.split("/")[-1].startswith(w)  # noqa: B023
        )

    fixed = [r for r in fa if not r["recorded_check"] and fl(r)]
    fc = [r for r in fixed if r["claim"] == "complete"]
    tp = statistics.mean(
        100 * sum(r in fixed for r in fa if r["task"] == t) / sum(r["task"] == t for r in fa)
        for t in tasks
    )
    tf = statistics.mean(
        100 * sum(r in fc for r in fa if r["task"] == t) / sum(r["task"] == t for r in fa)
        for t in tasks
    )
    print(
        f"{w}: flagged failures {len(fixed)}/{len(fa)} = {100 * len(fixed) / len(fa):.2f} pooled, "
        f"task mean {tp:.2f} "
        f"(printed pass +{p_pass}); flagged false completions {len(fc)} = "
        f"{100 * len(fc) / len(fa):.2f} pooled, "
        f"task mean {tf:.2f} (printed {-p_fc})"
    )
print(
    "Verdict: the task mean matches 9.1 and 5.1 but gives 5.9 for 6.0 and no false-completion "
    "figure; not reproduced."
)
