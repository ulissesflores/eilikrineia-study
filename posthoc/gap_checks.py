"""Round 27 (3): three cheap deterministic checks that close "not tested / not examined" sentences.

EXPLORATORY, POST HOC (2026-11-24). Computed for this paper; not preregistered. Spec fixed here
before the first run.

(a) Pilot, claim entries per kept trial, P against S. Data: the `recorded` column of
runs/pilot-scores.csv; kept
    trials = all minus the four the frozen runs/pilot-analysis.txt excludes (line 1, parsed). Gate:
    the frozen means
    3.49 (P) and 4.10 (S). Test: the same van Elteren task-stratified Wilcoxon rank-sum test as
    round 26
    (posthoc/claim_counts.py `van_elteren`, imported), strata = the 20 pilot tasks.
(b) Study 2, timing of the connection errors. Data: runs/study2-scores.csv (`is_error`, `seconds`,
arm) and each
    scored trial's record.json `started`; window = schedule positions 995 to 1,082 (Section 7).
    Gate: 88 scored
    trials, errors 43/49 control and 27/39 S. A trial is exposed if it had not finished (started +
    seconds) by the
    earliest end of any errored trial; counts by arm for exposed and unexposed trials; Fisher's
    exact test
    (two-sided, by enumeration) on the exposed. Revised after review: a first version split at the
    earliest start among errored trials that ran under 200 seconds, a threshold chosen after a
    start-time listing
    of the window had been printed; that version is superseded and not cited.
(c) Added after (a) and (b) had run (same day, before any paper edit): study 1's divergent rebuilds.
Data:
    runs/study-rescore.csv fidelity flags (diff_match, check_match, fail_set_match;
    runner/rescore_replay.py), over
    the kept trials of the registered study 1 analysis. Gate: 141 kept trials fail at least one flag
    (81 P, 60 S).
    Counts by task, and by which flag fails. No cause per trial is inferred.

Output: counts and statistics only.
Run from the package root: PYTHONDONTWRITEBYTECODE=1 python posthoc/gap_checks.py  (needs the
package and <RAW>)
"""

import ast
import csv
import json
import math
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
# the package root; raw/ = <RAW>, the unpacked raw archive
PKG = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from claim_counts import selftest, van_elteren  # noqa: E402

T = lambda v: v == "True"  # noqa: E731


def pilot():
    """Check the pilot's recorded entries, P against S."""
    first = (PKG / "runs" / "pilot-analysis.txt").read_text().splitlines()[0]
    excluded = set(ast.literal_eval(first.split(": ", 1)[1]))
    assert len(excluded) == 4
    rows = [
        r
        for r in csv.DictReader(open(PKG / "runs" / "pilot-scores.csv"))
        if r["trial"] not in excluded
    ]
    x = {a: [int(r["recorded"]) for r in rows if r["arm"] == a] for a in "PS"}
    m = {a: sum(v) / len(v) for a, v in x.items()}
    assert (round(m["P"], 2), round(m["S"], 2)) == (3.49, 4.10), m
    strata = []
    for task in sorted({r["task"] for r in rows}):
        g = {
            a: [int(r["recorded"]) for r in rows if r["arm"] == a and r["task"] == task]
            for a in "PS"
        }
        if g["P"] and g["S"]:
            strata.append((g["P"], g["S"]))
    z, p = van_elteren(strata)
    print(
        f"(a) Pilot: kept P {len(x['P'])}, S {len(x['S'])}; means {m['P']:.2f} / {m['S']:.2f} "
        f"[frozen 3.49 / 4.10: True]"
    )
    print(
        f"    van Elteren over {len(strata)} task strata, P vs S: z = {z:.2f}, two-sided p = "
        f"{p:.2g} "
        f"(normal approximation; about three trials per arm and task)"
    )


def fisher(a, b, c, d):
    """Return the two-sided Fisher exact p for a 2x2 table.

    Parameters
    ----------
    a : int
        Count in cell (1, 1).
    b : int
        Count in cell (1, 2).
    c : int
        Count in cell (2, 1).
    d : int
        Count in cell (2, 2).

    Returns
    -------
    float
        Sum of the probabilities of tables no more likely than the observed one.
    """
    r1, c1, n = a + b, a + c, a + b + c + d
    pr = lambda x: math.comb(c1, x) * math.comb(n - c1, r1 - x) / math.comb(n, r1)  # noqa: E731
    obs = pr(a)
    return sum(
        pr(x) for x in range(max(0, r1 - (n - c1)), min(r1, c1) + 1) if pr(x) <= obs * (1 + 1e-9)
    )


def outage():
    """Check the study 2 connection errors at positions 995 to 1082, by arm."""
    rows = [
        r
        for r in csv.DictReader(open(PKG / "runs" / "study2-scores.csv"))
        if r["arm"] in ("S", "control") and 995 <= int(r["trial"][:4]) <= 1082
    ]
    for r in rows:
        r["started"] = json.loads((RAW / "study2" / r["trial"] / "record.json").read_text())[
            "started"
        ]
    err = {
        a: (sum(T(r["is_error"]) for r in rows if r["arm"] == a), sum(r["arm"] == a for r in rows))
        for a in ("control", "S")
    }
    assert len(rows) == 88 and err == {"control": (43, 49), "S": (27, 39)}, err
    from datetime import datetime, timedelta

    for r in rows:
        r["end"] = datetime.fromisoformat(r["started"]) + timedelta(seconds=float(r["seconds"]))
    t_e = min(r["end"] for r in rows if T(r["is_error"]))
    print(
        f"\n(b) Study 2 window, positions 995-1082: 88 scored [gate 43/49 control, 27/39 S: True]; "
        f"earliest end of an errored trial {t_e.isoformat()}"
    )
    cells = {}
    for lab, sel in (
        ("finished before it", lambda r: r["end"] < t_e),
        ("exposed", lambda r: r["end"] >= t_e),
    ):
        for a in ("control", "S"):
            rs = [r for r in rows if r["arm"] == a and sel(r)]
            cells[(lab, a)] = (sum(T(r["is_error"]) for r in rs), len(rs))
        print(
            f"    {lab}: "
            + ", ".join(
                f"{a} errors {cells[(lab, a)][0]}/{cells[(lab, a)][1]}" for a in ("control", "S")
            )
        )
    (ec, nc), (es, ns) = cells[("exposed", "control")], cells[("exposed", "S")]
    print(f"    exposed, Fisher exact two-sided p = {fisher(ec, nc - ec, es, ns - es):.3f}")


def rebuilds():
    """Count kept study 1 trials whose rescored rebuild did not match."""
    kept = [
        r
        for r in csv.DictReader(open(PKG / "runs" / "study-scores.csv"))
        if r["arm"] in ("P", "S")
        and not (T(r["timed_out"]) or T(r["is_error"]) or int(r.get("hidden_access") or 0) > 0)
    ]
    re_ = {r["trial"]: r for r in csv.DictReader(open(PKG / "runs" / "study-rescore.csv"))}
    bad = [
        re_[r["trial"]]
        for r in kept
        if not all(T(re_[r["trial"]][f]) for f in ("diff_match", "check_match", "fail_set_match"))
    ]
    arms = {a: sum(x["arm"] == a for x in bad) for a in "PS"}
    assert len(kept) == 1992 and len(bad) == 141 and arms == {"P": 81, "S": 60}, (
        len(kept),
        len(bad),
        arms,
    )
    print(f"\n(c) Study 1 divergent rebuilds among 1992 kept: {len(bad)} [gate 81 P / 60 S: True]")
    for task in sorted({x["task"] for x in bad}):
        xs = [x for x in bad if x["task"] == task]
        print(
            f"    {task}: {len(xs)} (P {sum(x['arm'] == 'P' for x in xs)}, S "
            f"{sum(x['arm'] == 'S' for x in xs)})"
        )
    for f in ("diff_match", "check_match", "fail_set_match"):
        print(f"    {f} fails: {sum(not T(x[f]) for x in bad)}")
    print(
        f"    original check pass/fail reproduced (check_match): "
        f"{sum(T(x['check_match']) for x in bad)} of {len(bad)}"
    )


if __name__ == "__main__":
    selftest()
    pilot()
    outage()
    rebuilds()
