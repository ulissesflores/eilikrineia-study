"""Post hoc: minimum detectable effect (MDE) at 80% power for each null result of the paper.

EXPLORATORY, POST HOC (2026-11-23). Not preregistered.

MDE = (z_{1 - a/2} + z_{.80}) * SE, the usual normal approximation, with SE the standard error of
the estimate as
analysed: the package's Mantel-Haenszel estimator (runner/analyze_study.mh_rd, Sato variance) on the
kept trials,
so SE = (upper 95% bound - estimate) / 1.959964. The stratified SE is smaller than an unstratified
one where tasks
differ in rate (TD - S pass rate: 6.8 points with the unstratified binomial SE against 6.3 here). It
is the true difference that a two-sided test at level a would
detect with probability .80 if the variance were the observed one; it describes the design, not the
data's support for
any value. a = .05 for studies 1-2 and the pilot, a = .05/6 for study 3 (its Bonferroni level).

The estimates of studies 1-3 are recomputed from the package score files and checked against the
frozen value printed
in the paper; the study 1 recount uses the strata of its frozen output. The pilot is a separate
approximation: the
pilot has no Mantel-Haenszel line here, only the pooled Newcombe interval of
runs/pilot-analysis.txt, so its SE is the
interval half-width / 1.959964 (not a Mantel-Haenszel SE). The pilot's estimate and interval,
hard-coded below, are
checked against the "P-S M1" and "S-H M1" lines of that file; its comparison-arm rates (7/58, 9/59)
are not checked.
"""

import csv
import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # never write .pyc into the sealed runner/ folder
# the package root; raw/ = <RAW>, the unpacked raw archive
PKG = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))
sys.path.insert(0, str(PKG / "runner"))
from analyze import Z  # noqa: E402
from analyze_study import mh_rd  # noqa: E402
from analyze_study3 import zq  # noqa: E402

T = lambda v: v == "True"  # noqa: E731
Z80 = 0.8416212335729143


def strata(rows, a, b, f):
    """Return per-task counts of events and trials for two arms.

    Parameters
    ----------
    rows : list of dict
        Score rows of the trials.
    a : str
        First arm.
    b : str
        Second arm.
    f : callable
        Maps a row to the event indicator.

    Returns
    -------
    list of tuple
        One (a events, a n, b events, b n) per task.
    """
    out = []
    for task in sorted({r["task"] for r in rows}):
        x = [r for r in rows if r["task"] == task]
        out.append(
            (
                sum(f(r) for r in x if r["arm"] == a),
                sum(r["arm"] == a for r in x),
                sum(f(r) for r in x if r["arm"] == b),
                sum(r["arm"] == b for r in x),
            )
        )
    return out


def line(name, s, alpha, frozen, base):
    """Print one estimate with its standard error and minimum detectable effect.

    Parameters
    ----------
    name : str
        Label of the contrast.
    s : list of tuple
        Per-task counts.
    alpha : float
        Two-sided level.
    frozen : float
        Frozen point estimate in points.
    base : float
        Comparison-arm rate in percent.
    """
    rd, lo, hi, _, p = mh_rd(s)
    se = (hi - rd) / Z
    assert abs(rd * 100 - frozen) < 0.051, (name, rd * 100, frozen)
    mde = (zq(alpha) + Z80) * se * 100
    print(
        f"{name}: estimate {rd * 100:+.1f} (95% {lo * 100:+.1f} to {hi * 100:+.1f}); SE "
        f"{se * 100:.2f}; "
        f"alpha {alpha:.4f}; MDE {mde:.1f} points; comparison-arm rate {base:.1f}% -> MDE/rate "
        f"{mde / base:.2f}"
    )


def main():
    # pilot (frozen interval only; 20 tasks)
    """Print the minimum detectable effect of each null result."""
    frozen_pilot = (PKG / "runs" / "pilot-analysis.txt").read_text()
    for name, key, est, lo, hi, base in (
        ("Pilot P - S, unbacked claim", "P-S M1", 3.2, -9.7, 16.0, 7 / 58 * 100),
        ("Pilot S - H, unbacked claim", "S-H M1", -3.2, -16.0, 9.7, 9 / 59 * 100),
    ):  # fmt: skip
        want = f"{key}: {est:+.1f} points (95% {lo:+.1f} to {hi:+.1f})"
        # the hard-coded pilot interval equals the frozen pilot output
        assert want in frozen_pilot, want
        se = (hi - lo) / 2 / Z
        print(
            f"{name}: estimate {est:+.1f} (95% {lo:+.1f} to {hi:+.1f}); SE {se:.2f}; alpha .05; "
            f"MDE {(Z + Z80) * se:.1f} points; comparison-arm rate {base:.1f}%"
        )

    # study 1
    rows = [
        r for r in csv.DictReader(open(PKG / "runs" / "study-scores.csv")) if r["arm"] in ("P", "S")
    ]
    kept = [
        r
        for r in rows
        if not (T(r["timed_out"]) or T(r["is_error"]) or int(r.get("hidden_access") or 0) > 0)
    ]
    assert len(kept) == 1992
    fc = lambda r: T(r["false_completion"])  # noqa: E731
    line(
        "Study 1 P - S, registered (three tasks)",
        strata(kept, "P", "S", fc),
        0.05,
        1.2,
        255 / 997 * 100,
    )
    v = [r for r in kept if r["task"] == "text-template-engine"]
    line("Study 1 P - S, valid task only", strata(v, "P", "S", fc), 0.05, 0.3, 83 / 333 * 100)
    rec = (PKG / "runs" / "study-rescore-analysis.txt").read_text()
    s = [
        tuple(map(int, m[1:]))
        for m in re.findall(r"^  ([a-z-]+): P (\d+)/(\d+) S (\d+)/(\d+);", rec, re.M)
    ][:3]
    assert len(s) == 3, s
    line("Study 1 P - S, recount with corrected checks", s, 0.05, 0.6, 113 / 997 * 100)

    # study 2 pass rate (exploratory; same exclusions as analyze_study2)
    runs2 = RAW / "study2"
    rows = [
        r
        for r in csv.DictReader(open(PKG / "runs" / "study2-scores.csv"))
        if r["arm"] in ("S", "control")
    ]
    rc = {r["trial"]: json.loads((runs2 / r["trial"] / "record.json").read_text()).get("agent_rc")
          for r in rows if (runs2 / r["trial"] / "record.json").exists()}  # fmt: skip
    k2 = [
        r
        for r in rows
        if not (
            T(r["timed_out"])
            or T(r["is_error"])
            or int(r["hidden_access"] or 0) > 0
            or rc.get(r["trial"]) == 127
        )
    ]  # fmt: skip
    assert len(k2) == 998
    line(
        "Study 2 S - control, pass rate",
        strata(k2, "S", "control", lambda r: T(r["check_passed"])),
        0.05,
        -1.2,
        396 / 493 * 100,
    )

    comp = [r for r in k2 if r["claim"] == "complete"]
    line(
        "Study 2 S - control, hidden check passed among 'complete' labels (descriptive)",
        strata(comp, "S", "control", lambda r: T(r["check_passed"])),
        0.05,
        -3.8,
        277 / 358 * 100,
    )

    # study 3 (exclusions as analyze_study3)
    rows = list(csv.DictReader(open(PKG / "runs" / "study3-scores.csv")))
    k3 = [
        r
        for r in rows
        if not (
            T(r["timed_out"])
            or T(r["is_error"])
            or not r["init_model"]
            or int(r.get("hidden_access_path") or 0) > 0
            or T(r["check_infra_error"])
        )
    ]  # fmt: skip
    assert len(k3) == 2958
    a3 = 0.05 / 6
    fnc = lambda r: T(r["check_passed"]) and r["claim"] != "complete"  # noqa: E731
    ok = lambda r: T(r["check_passed"])  # noqa: E731
    line("Study 3 K - S, false completion", strata(k3, "K", "S", fc), a3, 1.2, 56 / 740 * 100)
    line(
        "Study 3 K - S, false non-completion", strata(k3, "K", "S", fnc), a3, -2.5, 416 / 740 * 100
    )
    line("Study 3 TD - S, pass rate", strata(k3, "TD", "S", ok), a3, 2.0, 608 / 740 * 100)
    line(
        "Study 3 I - S, false completion (no claim)",
        strata(k3, "I", "S", fc),
        a3,
        2.3,
        56 / 740 * 100,
    )
    line(
        "Study 3 I - S, false non-completion (no claim)",
        strata(k3, "I", "S", fnc),
        a3,
        -2.8,
        416 / 740 * 100,
    )


if __name__ == "__main__":
    main()
