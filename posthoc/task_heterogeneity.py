"""Post hoc: task heterogeneity of the main contrasts. EXPLORATORY, POST HOC (2026-11-23), not preregistered.

Per-task counts are read from the frozen package outputs (runs/*-analysis.txt, which print them) or recomputed as
scripts/make_results.py does (study 2 pass rate). For each contrast:
- the registered estimate, recomputed with the package's analyze_study.mh_rd (gate: equals the frozen line);
- per-task differences with the package's analyze.newcombe 95% interval;
- Cochran's Q (inverse-variance, Wald variance per task; df = 2) and I^2, as a homogeneity check (written here);
- the same Mantel-Haenszel-weighted average with a variance that does NOT assume a common difference across tasks,
  Var = sum w_k^2 v_k / (sum w_k)^2, w_k = n1k n0k / nk, v_k = p1k(1-p1k)/n1k + p0k(1-p0k)/n0k (written here;
  checked against mh_rd on a single task, where both must equal the variance of a difference of two proportions);
- for study 3, the registered (1 - alpha) interval and, for K - S false completion, the (1 - 2 alpha) interval, with
  the Sato variance (package) and with the heterogeneity-robust variance.
"""

import csv
import math
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # never write .pyc into the sealed runner/ folder
PKG = Path(__file__).resolve().parent.parent  # the package root
sys.path.insert(0, str(PKG / "runner"))
from analyze import Z, newcombe  # noqa: E402
from analyze_study import mh_rd  # noqa: E402
from analyze_study3 import ALPHA, zq  # noqa: E402

RUNS = PKG / "runs"
TASKS = ("feature-toml-config", "feature-uri-resolve", "text-template-engine")


def robust(strata):
    num = den = var = 0.0
    for a1, n1, a0, n0 in strata:
        n = n1 + n0
        w = n1 * n0 / n
        p1, p0 = a1 / n1, a0 / n0
        num += w * (p1 - p0)
        den += w
        var += w * w * (p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    return num / den, math.sqrt(var) / den


def cochran(strata):
    ds, ws = [], []
    for a1, n1, a0, n0 in strata:
        p1, p0 = a1 / n1, a0 / n0
        v = p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0
        if v == 0:
            return None
        ds.append(p1 - p0)
        ws.append(1 / v)
    m = sum(w * d for w, d in zip(ws, ds)) / sum(ws)
    q = sum(w * (d - m) ** 2 for w, d in zip(ws, ds))
    df = len(ds) - 1
    p = math.exp(-q / 2) if df == 2 else float("nan")  # chi-square survival function with 2 degrees of freedom
    i2 = max(0.0, (q - df) / q) if q > 0 else 0.0
    return q, p, i2


def show(name, strata, frozen=None, study3=False, tost=False):
    rd, lo, hi, _, p = mh_rd(strata)
    se = (hi - rd) / Z
    line = f"{rd * 100:+.1f} (95% {lo * 100:+.1f} to {hi * 100:+.1f})"
    same = None if frozen is None else frozen.replace(" points", "").startswith(line)  # outside the f-string: Python 3.11
    gate = "" if frozen is None else f"  [frozen: {frozen}; same: {same}]"
    print(f"\n== {name}\n  Mantel-Haenszel (package mh_rd, Sato variance): {line}, p {p:.3f}{gate}")
    assert same is not False, f"{name}: recomputed estimate differs from the frozen line"
    for t, (a1, n1, a0, n0) in zip(TASKS, strata):
        nlo, nhi = newcombe(a1, n1, a0, n0)
        print(f"    {t}: {a1}/{n1} vs {a0}/{n0}: {(a1 / n1 - a0 / n0) * 100:+.1f} (Newcombe 95% {nlo * 100:+.1f} to {nhi * 100:+.1f})")
    c = cochran(strata)
    print("  Cochran Q: " + ("not computable (a task has zero variance in both arms)" if c is None else
                             f"{c[0]:.2f}, df 2, p {c[1]:.3f}, I^2 {c[2] * 100:.0f}%"))
    r, rse = robust(strata)
    print(f"  same weights, variance without a common difference: {r * 100:+.1f} (95% {(r - Z * rse) * 100:+.1f} to "
          f"{(r + Z * rse) * 100:+.1f}); SE robust {rse * 100:.2f} vs Sato {se * 100:.2f} points")
    if study3:
        za = zq(ALPHA)
        print(f"  (1 - alpha) interval, alpha {ALPHA:.4f}: Sato {(rd - za * se) * 100:+.1f} to {(rd + za * se) * 100:+.1f}; "
              f"robust {(r - za * rse) * 100:+.1f} to {(r + za * rse) * 100:+.1f}")
    if tost:
        z2 = zq(2 * ALPHA)
        print(f"  (1 - 2 alpha) interval: Sato {(rd - z2 * se) * 100:+.1f} to {(rd + z2 * se) * 100:+.1f}; "
              f"robust {(r - z2 * rse) * 100:+.1f} to {(r + z2 * rse) * 100:+.1f}  (margin +-5)")


def per_task_lines(text, header, arm):
    sec = text.split(header, 1)[1]
    out = []
    for t in TASKS:
        m = re.search(rf"{t}: {arm} (\d+)/(\d+), S (\d+)/(\d+)", sec)
        out.append(tuple(int(x) for x in m.groups()))
    return out


def main():
    # self-check of the robust variance: one task, both formulas = variance of a difference of two proportions
    one = [(30, 171, 52, 171)]
    rd, lo, hi, _, _ = mh_rd(one)
    r, rse = robust(one)
    print(f"single-stratum check: mh_rd SE {(hi - rd) / Z:.6f}, robust SE {rse:.6f}, "
          f"two-proportion SE {math.sqrt(30 / 171 * (1 - 30 / 171) / 171 + 52 / 171 * (1 - 52 / 171) / 171):.6f}")

    s1 = (RUNS / "study-analysis.txt").read_text()
    pt = re.search(r"== false_completion.*?per task: (.*?)\n", s1, re.S).group(1)
    strata = [tuple(int(x) for x in re.search(rf"{t} (\d+)/(\d+) vs (\d+)/(\d+)", pt).groups()) for t in TASKS]
    show("Study 1 registered, P - S false completion (two checks defective)", strata,
         re.search(r"== false_completion.*?MH P-S by task: (.*?);", s1, re.S).group(1))
    rr = (RUNS / "study-rescore-analysis.txt").read_text().split("== primary estimate", 1)[1]
    strata = [tuple(int(x) for x in re.search(rf"  {t}: P (\d+)/(\d+) S (\d+)/(\d+)", rr).groups()) for t in TASKS]
    show("Study 1 recount with corrected checks, P - S false completion", strata,
         re.search(r"all trials:\s+.*?MH P-S (.*?),", rr).group(1))

    s2 = (RUNS / "study2-analysis.txt").read_text()
    for col in ("false_completion", "false_non_completion"):
        sec = s2.split(f"== {col} ", 1)[1]
        strata = [tuple(int(x) for x in re.search(rf"{t}: S (\d+)/(\d+), control (\d+)/(\d+)", sec).groups()) for t in TASKS]
        show(f"Study 2, S - control {col}", strata, re.search(r"MH S-control by task: (.*?);", sec).group(1))
    rows = [r for r in csv.DictReader(open(RUNS / "study2-scores.csv")) if r["timed_out"] != "True" and r["is_error"] != "True"]
    kept_by_task = {"S": (171, 163, 171), "control": (156, 166, 171)}  # frozen denominators, as scripts/make_results.py
    strata = []
    for i, t in enumerate(TASKS):
        ps = sum(r["check_passed"] == "True" for r in rows if r["arm"] == "S" and r["task"] == t)
        pc = sum(r["check_passed"] == "True" for r in rows if r["arm"] == "control" and r["task"] == t)
        strata.append((ps, kept_by_task["S"][i], pc, kept_by_task["control"][i]))
    show("Study 2, S - control pass rate (exploratory)", strata, "-1.2 (95% -6.0 to +3.5)")

    s3 = (RUNS / "study3-analysis.txt").read_text().split("######## SENSITIVITY", 1)[0]
    for arm, col, tost in (("I", "false_completion", False), ("I", "false_non_completion", False),
                           ("K", "false_completion", True), ("K", "false_non_completion", False), ("TD", "passed", False)):
        sec = s3.split(f"\n== {col}\n", 1)[1]
        strata = per_task_lines(sec, f"  {arm}-S ", arm)
        fro = re.search(rf"  {arm}-S \w+: (.*?), CMH", sec).group(1).replace(" points", "")
        show(f"Study 3, {arm} - S {col}", strata, fro, study3=True, tost=tost)


if __name__ == "__main__":
    main()
