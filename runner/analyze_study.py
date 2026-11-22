"""Preregistered analysis of the main study (PREREGISTRATION-STUDY.md): P against S, compared within each task.

Usage: python3 analyze_study.py SCORES_CSV [--a P --b S]

For each outcome: per-arm counts with Wilson intervals; the Mantel-Haenszel risk difference a - b stratified by task,
with the Sato (1989) variance and a 95% interval; the Cochran-Mantel-Haenszel test; the pooled Newcombe interval as a
sensitivity check; and a per-task table. Exclusions follow the preregistration: timeouts, agent errors, and trials
whose tool inputs name the overclaim folder.
"""

import argparse
import csv
import math
from collections import defaultdict

from analyze import Z, newcombe, wilson

OUTCOMES = (("false_completion", "primary: says complete, hidden check fails"),
            ("unbacked", "pilot M1, kept for comparison"),
            ("record_false_complete", "exploratory: a record says complete, hidden check fails"))  # fmt: skip


def mh_rd(strata):
    """strata: list of (a1, n1, a0, n0). Returns (rd, lo, hi, cmh_chi2, cmh_p)."""
    num = den = sp = sq = 0.0
    cmh_num = cmh_var = 0.0
    for a1, n1, a0, n0 in strata:
        n = n1 + n0
        if n1 == 0 or n0 == 0:
            continue
        num += (a1 * n0 - a0 * n1) / n
        den += n1 * n0 / n
        sp += (n1 * n1 * a0 - n0 * n0 * a1 + n1 * n0 * (n0 - n1) / 2) / (n * n)
        sq += (a1 * (n0 - a0) + a0 * (n1 - a1)) / (2 * n)
        m = a1 + a0
        cmh_num += a1 - n1 * m / n
        if n > 1:
            cmh_var += n1 * n0 * m * (n - m) / (n * n * (n - 1))
    rd = num / den
    se = math.sqrt(max(rd * sp + sq, 0)) / den
    chi2 = max(abs(cmh_num) - 0.5, 0) ** 2 / cmh_var if cmh_var else float("nan")  # no correction past 0 (review A, 13)
    p = math.erfc(math.sqrt(chi2 / 2)) if cmh_var else float("nan")
    return rd, rd - Z * se, rd + Z * se, chi2, p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--a", default="P")
    ap.add_argument("--b", default="S")
    x = ap.parse_args()
    t = lambda v: v == "True"  # noqa: E731
    rows = [r for r in csv.DictReader(open(x.csv)) if r["arm"] in (x.a, x.b)]
    bad = sorted(r["trial"] for r in rows if t(r["timed_out"]) or t(r["is_error"]) or int(r.get("hidden_access") or 0) > 0)
    kept = [r for r in rows if r["trial"] not in bad]
    print(f"trials {len(rows)}, excluded {len(bad)}")
    for arm in (x.a, x.b):
        ex = [r for r in rows if r["arm"] == arm and r["trial"] in bad]
        print(f"  excluded in {arm}: {len(ex)} (timeouts {sum(t(r['timed_out']) for r in ex)})")
    tasks = sorted({r["task"] for r in kept})
    for col, desc in OUTCOMES:
        print(f"\n== {col} ({desc})")
        tot = {}
        for arm in (x.a, x.b):
            rs = [r for r in kept if r["arm"] == arm]
            k, n = sum(t(r[col]) for r in rs), len(rs)
            tot[arm] = (k, n)
            lo, hi = wilson(k, n)
            print(f"{arm}: {k}/{n} = {k / n:.1%} (95% {lo:.1%}-{hi:.1%})")
        strata = []
        for task in tasks:
            c = defaultdict(lambda: [0, 0])
            for r in kept:
                if r["task"] == task:
                    c[r["arm"]][0] += t(r[col])
                    c[r["arm"]][1] += 1
            strata.append((*c[x.a], *c[x.b]))
        rd, lo, hi, chi2, p = mh_rd(strata)
        print(f"MH {x.a}-{x.b} by task: {rd * 100:+.1f} points (95% {lo * 100:+.1f} to {hi * 100:+.1f}); CMH chi2 {chi2:.2f}, p {p:.3f}")
        nlo, nhi = newcombe(tot[x.a][0], tot[x.a][1], tot[x.b][0], tot[x.b][1])
        print(f"pooled Newcombe {x.a}-{x.b}: {(tot[x.a][0] / tot[x.a][1] - tot[x.b][0] / tot[x.b][1]) * 100:+.1f} points (95% {nlo * 100:+.1f} to {nhi * 100:+.1f})")
        print("per task: " + "; ".join(f"{task} {s[0]}/{s[1]} vs {s[2]}/{s[3]}" for task, s in zip(tasks, strata)))
    print("\n== records with evidence attached (secondary)")
    for arm in (x.a, x.b):
        rs = [r for r in kept if r["arm"] == arm]
        n_rec, n_ev = sum(int(r["records"]) for r in rs), sum(int(r["records_with_evidence"]) for r in rs)
        print(f"{arm}: {n_ev}/{n_rec} records = {n_ev / max(n_rec, 1):.1%}; trials with no record {sum(r['records'] == '0' for r in rs)}/{len(rs)}")


if __name__ == "__main__":
    main()
