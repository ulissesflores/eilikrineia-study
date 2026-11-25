"""Compute study 3 TD - S with per-arm counts, and TD without 11 trials.

Round 26 (5): study 3, TD - S with per-arm counts, and TD without the 11 trials that edited
acceptance/. EXPLORATORY, POST HOC (2026-11-24). Computed for this paper; not preregistered.

Rows, outcomes and exclusions are built exactly as the registered study 3 analysis builds them
(runner/analyze_study3.py
`main`: passed, false_completion, false_non_completion from runs/study3-scores.csv; timeouts, agent
errors, agents that
never started, hidden access, check-infrastructure errors excluded), and each contrast is the
package's own
analyze_study3.contrast (Mantel-Haenszel risk difference by task, Sato variance, CMH p) with the
registered decision
grid analyze_study3.cell at alpha = .05/6. Gate: the frozen TD - S lines of
runs/study3-analysis.txt.
Then the same contrasts with the TD trials whose writer tests were edited (`td_edited` > 0; 11 kept)
left out.

Output: counts and estimates only.
Run from the package root: PYTHONDONTWRITEBYTECODE=1 python posthoc/td_secondary.py  (needs the
package only)
"""

import csv
import sys
from pathlib import Path

sys.dont_write_bytecode = True
# the package root; raw/ = <RAW>, the unpacked raw archive
PKG = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PKG / "runner"))
from analyze_study3 import ALPHA, cell, contrast, zq  # noqa: E402

T = lambda v: v == "True"  # noqa: E731
MEAS = ("false_completion", "false_non_completion", "passed")


def rows():
    """Return the kept study 3 trials of arms S and TD.

    Returns
    -------
    list of dict
        One row per kept trial.
    """
    out = []
    for r in csv.DictReader(open(PKG / "runs" / "study3-scores.csv")):
        if r["arm"] not in ("S", "TD"):
            continue
        if (
            T(r["timed_out"])
            or T(r["is_error"])
            or not r["init_model"]
            or int(r.get("hidden_access_path") or 0) > 0
            or T(r["check_infra_error"])
        ):
            continue
        ok = T(r["check_passed"])
        r |= {
            "passed": ok,
            "false_completion": T(r["false_completion"]),
            "false_non_completion": ok and r["claim"] != "complete",
        }
        out.append(r)
    return out


def show(rs, title):
    """Print the TD - S contrasts of each measure.

    Parameters
    ----------
    rs : list of dict
        Kept trials.
    title : str
        Heading of the block.
    """
    print(f"\n== {title}")
    for m in MEAS:
        k = {
            a: (sum(r[m] for r in rs if r["arm"] == a), sum(r["arm"] == a for r in rs))
            for a in ("TD", "S")
        }
        rd, lo, hi, p, se, events = contrast(rs, "TD", m, lambda r: r["task"])
        a, b = rd - zq(ALPHA) * se, rd + zq(ALPHA) * se
        print(
            f"  {m}: TD {k['TD'][0]}/{k['TD'][1]} ({100 * k['TD'][0] / k['TD'][1]:.1f}%), S "
            f"{k['S'][0]}/{k['S'][1]} "
            f"({100 * k['S'][0] / k['S'][1]:.1f}%); TD-S {100 * rd:+.1f} (95% {100 * lo:+.1f} to "
            f"{100 * hi:+.1f}; "
            f"(1 - alpha) {100 * a:+.1f} to {100 * b:+.1f}), CMH p {p:.4f}, events {events} -> "
            f"{cell(rd, se, p, events)}"
        )
    return rs


def main():
    """Print the TD - S contrasts, all kept and without the trials that edited tests."""
    rs = rows()
    assert (sum(r["arm"] == "S" for r in rs), sum(r["arm"] == "TD" for r in rs)) == (740, 737)
    show(
        rs,
        "All kept (frozen: FC +3.0 (95% +0.2 to +5.8), FNC -11.8 (95% -16.4 to -7.2), pass +2.0 "
        "(95% -1.6 to +5.5))",
    )
    edited = [r for r in rs if r["arm"] == "TD" and int(r["td_edited"] or 0) > 0]
    print(
        f"\nTD kept trials that edited the writer tests: {len(edited)}; passed "
        f"{sum(r['passed'] for r in edited)}, "
        f"by task "
        f"{sorted((t, sum(r['task'] == t for r in edited)) for t in {r['task'] for r in edited})}"
    )
    assert len(edited) == 11
    show(
        [r for r in rs if r not in edited], "Without the 11 TD trials that edited the writer tests"
    )


if __name__ == "__main__":
    main()
