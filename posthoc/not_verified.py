# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Carlos Ulisses Flores (Codex Hash Ltda.)
"""Count 'Not verified'-type sections in final messages, study 2 and study 3 by arm.

Computed for this paper. The specification was fixed before computing; it is not published.

Matcher: the one behind study 2's "100 S messages against 11 in the control" (Section 5.4), imported
unchanged: runner/z1_relabel_study2.py `relabel(text)`, whose second value says whether the message
has a caveat section whose heading starts with not verified / not tested / not checked / not run /
untested / unverified (the labeller's own section parser, overclaim.claims._units). Study 2 messages
are record.json `final_message`, as z1 reads them (gate: the frozen 100 / 11 over all scored trials,
runs/study2-z1.txt). Study 3 messages are read and stripped of their STATUS line exactly as the
registered study 3 analysis does before the same relabel (analyze_study3.final_message, then
run_trial.split_status). Kept trials follow the registered exclusions of each study (gates: frozen
kept counts).

Study 2 ran on the author's host (with the host's start-up hooks); study 3 ran in isolated
containers without them.

Inputs
------
- The raw archive <RAW> (environment variable EILIKRINEIA_RAW, default raw/): record.json and
  agent.stdout of the study 2 and study 3 trials.
- The package: runs/study2-z1.txt, the score files, runner/z1_relabel_study2.py,
  runner/analyze_study3.py and runner/run_trial.py (imported unchanged).

Outputs
-------
- Counts only, on standard output; the committed posthoc/not_verified.txt must be reproduced byte
  for byte.

Usage
-----
    PYTHONDONTWRITEBYTECODE=1 python posthoc/not_verified.py

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

import csv
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
# the package root; raw/ = <RAW>, the unpacked raw archive
PKG = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))
sys.path.insert(0, str(PKG / "runner"))
sys.path.insert(0, str(PKG / "overclaim" / "src"))
from analyze_study3 import final_message  # noqa: E402
from run_trial import split_status  # noqa: E402
from z1_relabel_study2 import relabel  # noqa: E402

T = lambda v: v == "True"  # noqa: E731


def has_section(text):
    """Tell whether a final message has a 'Not verified' type section.

    Parameters
    ----------
    text : str or None
        Final message.

    Returns
    -------
    bool
        True if the relabelling finds such a section.
    """
    return relabel(text)[1]


def study2():
    """Print the section counts for study 2 by arm."""
    rows = [
        r
        for r in csv.DictReader(open(PKG / "runs" / "study2-scores.csv"))
        if r["arm"] in ("S", "control")
    ]
    allc, keptc = {"S": [0, 0], "control": [0, 0]}, {"S": [0, 0], "control": [0, 0]}
    for r in rows:
        rec = RAW / "study2" / r["trial"] / "record.json"
        d = json.loads(rec.read_text()) if rec.exists() else {}
        h = has_section(d.get("final_message"))
        allc[r["arm"]][0] += h
        allc[r["arm"]][1] += 1
        if not (
            T(r["timed_out"])
            or T(r["is_error"])
            or int(r.get("hidden_access") or 0) > 0
            or d.get("agent_rc") == 127
        ):
            keptc[r["arm"]][0] += h
            keptc[r["arm"]][1] += 1
    assert (allc["S"][0], allc["control"][0]) == (100, 11)
    assert (keptc["S"][1], keptc["control"][1]) == (505, 493)
    print("== Study 2 (author's host)")
    print(
        "  all scored: "
        + ", ".join(f"{a} {k}/{n}" for a, (k, n) in allc.items())
        + "  [frozen 100 / 11: True]"
    )
    print(
        "  kept:       "
        + ", ".join(f"{a} {k}/{n} ({100 * k / n:.1f}%)" for a, (k, n) in keptc.items())
    )


def study3():
    """Print the section counts for study 3 by arm."""
    rows = [
        r
        for r in csv.DictReader(open(PKG / "runs" / "study3-scores.csv"))
        if r["arm"] in ("S", "I", "K", "TD")
    ]
    arms = ("S", "I", "K", "TD")
    allc, keptc = {a: [0, 0] for a in arms}, {a: [0, 0] for a in arms}
    for r in rows:
        h = has_section(split_status(final_message(RAW / "study3" / r["trial"]))[0])
        allc[r["arm"]][0] += h
        allc[r["arm"]][1] += 1
        excluded = (
            T(r["timed_out"])
            or T(r["is_error"])
            or not r["init_model"]
            or int(r.get("hidden_access_path") or 0) > 0
            or T(r["check_infra_error"])
        )
        if not excluded:
            keptc[r["arm"]][0] += h
            keptc[r["arm"]][1] += 1
    assert tuple(keptc[a][1] for a in arms) == (740, 740, 741, 737)
    print("\n== Study 3 (isolated containers, no host hooks)")
    print("  all scored: " + ", ".join(f"{a} {k}/{n}" for a, (k, n) in allc.items()))
    print(
        "  kept:       "
        + ", ".join(f"{a} {k}/{n} ({100 * k / n:.1f}%)" for a, (k, n) in keptc.items())
    )


if __name__ == "__main__":
    study2()
    study3()
