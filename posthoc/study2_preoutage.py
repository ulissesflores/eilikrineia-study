"""Round 26 (1, 2): study 2 before the TLS outage, and 97.5% intervals.

EXPLORATORY, POST HOC (2026-11-24).

Computed for this paper; not preregistered. Spec fixed in the author's project log before computing
(the log is not published).

1. Pre-outage estimate. The registered study 2 analysis (runner/analyze_study2.py, `main`,
unchanged: same
   exclusions, Mantel-Haenszel risk difference S - control stratified by task with the Sato
   variance, CMH test) is
   run on the trials at scheduled positions 1-994 only (position = the 4-digit prefix of the trial
   folder); the 70
   connection errors all fell at positions 995-1,082. The pass rate S - control uses the same
   `mh_rd` on the kept
   trials, as scripts/make_results.py does for the full run. Counts are reconciled with the full run
   (Table 3):
   full kept counts = pre-outage kept counts + kept counts at positions 995-1,086 (asserted).
2. 97.5% intervals (display) for the full-run Table 3 contrasts, next to the plan's p < .025 rule:
same `mh_rd`
   point estimate and Sato standard error (se = (upper 95% - estimate) / Z), with the two-sided
   normal quantile for
   tail .025 (analyze_study3.zq). The plan displayed 95% intervals; nothing registered changes.

Output: counts and estimates only (no trial id, no message text).
Run from the package root: PYTHONDONTWRITEBYTECODE=1 python posthoc/study2_preoutage.py  (needs the
package and <RAW>)
"""

import contextlib
import csv
import io
import json
import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
# the package root; raw/ = <RAW>, the unpacked raw archive
PKG = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))
sys.path.insert(0, str(PKG / "runner"))
from analyze import Z  # noqa: E402
from analyze_study import mh_rd  # noqa: E402
from analyze_study2 import main as registered  # noqa: E402
from analyze_study3 import zq  # noqa: E402

CUT = 994
T = lambda v: v == "True"  # noqa: E731
OUT = {
    "false_completion": lambda r: T(r["false_completion"]),
    "false_non_completion": lambda r: T(r["check_passed"]) and r["claim"] != "complete",
    "pass_rate": lambda r: T(r["check_passed"]),
}


def kept(rows):
    """Return the trials kept by the registered study 2 exclusions.

    Parameters
    ----------
    rows : list of dict
        Score rows of the trials.

    Returns
    -------
    list of dict
        Rows left after dropping timeouts, agent errors, hidden access and exit 127.
    """
    out = []
    for r in rows:
        rec = RAW / "study2" / r["trial"] / "record.json"
        rc = json.loads(rec.read_text()).get("agent_rc") if rec.exists() else None
        if (
            T(r["timed_out"])
            or T(r["is_error"])
            or int(r.get("hidden_access") or 0) > 0
            or rc == 127
        ):
            continue
        out.append(r)
    return out


def strata(rows, f):
    """Return per-task counts of events and trials for S and control.

    Parameters
    ----------
    rows : list of dict
        Score rows of the trials.
    f : callable
        Maps a row to the event indicator.

    Returns
    -------
    list of tuple
        One (S events, S n, control events, control n) per task.
    """
    c = defaultdict(lambda: [0, 0, 0, 0])
    for r in rows:
        i = 0 if r["arm"] == "S" else 2
        c[r["task"]][i] += f(r)
        c[r["task"]][i + 1] += 1
    return [tuple(c[t]) for t in sorted(c)]


def counts(rows, f):
    """Return the events and trials of each arm.

    Parameters
    ----------
    rows : list of dict
        Score rows of the trials.
    f : callable
        Maps a row to the event indicator.

    Returns
    -------
    dict
        Arm to (events, trials).
    """
    return {
        a: (sum(f(r) for r in rows if r["arm"] == a), sum(r["arm"] == a for r in rows))
        for a in ("S", "control")
    }


def show(rows, label, z975=False):
    """Print the Mantel-Haenszel contrasts of each outcome for one set of rows.

    Parameters
    ----------
    rows : list of dict
        Score rows of the trials.
    label : str
        Heading of the block.
    z975 : bool
        Also print the 97.5% interval.

    Returns
    -------
    dict
        Outcome name to the per-arm counts.
    """
    print(f"\n== {label}")
    for name, f in OUT.items():
        st = strata(rows, f)
        rd, lo, hi, chi2, p = mh_rd(st)
        c = counts(rows, f)
        line = (
            f"  {name}: S {c['S'][0]}/{c['S'][1]} ({100 * c['S'][0] / c['S'][1]:.1f}%), control "
            f"{c['control'][0]}/"
            f"{c['control'][1]} ({100 * c['control'][0] / c['control'][1]:.1f}%); MH S-control "
            f"{100 * rd:+.1f} "
            f"(95% {100 * lo:+.1f} to {100 * hi:+.1f}); CMH chi2 {chi2:.2f}, p {p:.4f}"
        )
        if z975:
            se, z = (hi - rd) / Z, zq(0.025)
            line += f"; 97.5% {100 * (rd - z * se):+.1f} to {100 * (rd + z * se):+.1f}"
        print(line)
        print(
            "    by task (S events/kept, control events/kept): "
            + "; ".join(f"{a}/{b} vs {c_}/{d}" for a, b, c_, d in st)
        )
    return {n: counts(rows, f) for n, f in OUT.items()}


def main():
    """Print the study 2 analysis before and after the TLS outage."""
    rows = [
        r
        for r in csv.DictReader(open(PKG / "runs" / "study2-scores.csv"))
        if r["arm"] in ("S", "control")
    ]
    pos = lambda r: int(r["trial"][:4])  # noqa: E731
    k = kept(rows)
    assert (sum(r["arm"] == "S" for r in k), sum(r["arm"] == "control" for r in k)) == (505, 493)
    early, late = [r for r in k if pos(r) <= CUT], [r for r in k if pos(r) > CUT]
    print(f"scored trials {len(rows)} (positions 1-1,086; 4 crashed, unscored); kept {len(k)}")
    print(
        f"scored at positions 1-{CUT}: {sum(pos(r) <= CUT for r in rows)}; kept {len(early)} "
        f"(S {sum(r['arm'] == 'S' for r in early)}, control "
        f"{sum(r['arm'] == 'control' for r in early)})"
    )
    print(
        f"scored at positions {CUT + 1}-1,086: {sum(pos(r) > CUT for r in rows)}; kept {len(late)} "
        f"(S {sum(r['arm'] == 'S' for r in late)}, control "
        f"{sum(r['arm'] == 'control' for r in late)})"
    )
    print(
        f"connection errors (is_error) at positions <= {CUT}: "
        f"{sum(T(r['is_error']) and pos(r) <= CUT for r in rows)}"
    )

    full = show(
        k,
        "Full run (Table 3), with 97.5% intervals for the p < .025 rule (display only)",
        z975=True,
    )
    pre = show(early, f"Pre-outage: kept trials at scheduled positions 1-{CUT}", z975=True)
    post = {n: counts(late, f) for n, f in OUT.items()}
    print("\n== Reconciliation: Table 3 = pre-outage + kept trials at positions 995-1,086")
    for n in OUT:
        for a in ("S", "control"):
            assert full[n][a] == tuple(x + y for x, y in zip(pre[n][a], post[n][a], strict=False))
        print(
            f"  {n}: late kept S {post[n]['S'][0]}/{post[n]['S'][1]}, control "
            f"{post[n]['control'][0]}/"
            f"{post[n]['control'][1]}; sums match Table 3: True"
        )

    print(
        "\n== The registered analysis function itself (analyze_study2.main) on the positions 1-994 "
        "rows"
    )
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "pre.csv"
        allrows = list(csv.DictReader(open(PKG / "runs" / "study2-scores.csv")))
        with open(p, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=allrows[0].keys())
            w.writeheader()
            w.writerows(r for r in allrows if int(r["trial"][:4]) <= CUT)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            registered(RAW / "study2", p)
    for line in buf.getvalue().splitlines():
        if line.startswith(("trials", "  excluded", "==", "S:", "control:", "MH ")):
            print("  " + line)


if __name__ == "__main__":
    main()
