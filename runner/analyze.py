"""Preregistered analysis of the pilot (PREREGISTRATION.md): rates with Wilson intervals, P-S and S-H differences
with Newcombe intervals, per-task table, decision rules. Input: the CSV written by score.py; exclusions by name.

Usage: python3 analyze.py SCORES_CSV [--exclude TRIAL ...]
"""

import argparse
import csv
import math
from collections import defaultdict

Z = 1.959964


def wilson(k, n):
    if n == 0:
        return (float("nan"),) * 2
    p, d = k / n, 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return c - h, c + h


def newcombe(k1, n1, k2, n2):
    """95% interval for p1 - p2 (Newcombe hybrid score, method 10)."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--exclude", nargs="*", default=[])
    a = ap.parse_args()
    rows = [r for r in csv.DictReader(open(a.csv))]
    bad = {r["trial"] for r in rows if r["timed_out"] == "True" or r["is_error"] == "True"} | set(a.exclude)
    kept = [r for r in rows if r["trial"] not in bad]
    t = lambda v: v == "True"  # noqa: E731
    by = defaultdict(list)
    for r in kept:
        by[r["arm"]].append(r)
    print(f"trials {len(rows)}, excluded {len(bad)}: {sorted(bad)}")
    m = {}
    for arm in ("H", "S", "P"):
        rs = by[arm]
        n = len(rs)
        m1, m2 = sum(t(r["unbacked"]) for r in rs), sum(t(r["false_completion"]) for r in rs)
        m[arm] = (n, m1, m2)
        lo1, hi1 = wilson(m1, n)
        lo2, hi2 = wilson(m2, n)
        print(f"{arm}: n={n} M1={m1} ({m1 / n:.1%}, 95% {lo1:.1%}-{hi1:.1%}) M2={m2} ({m2 / n:.1%}, {lo2:.1%}-{hi2:.1%}) "
              f"check_pass={sum(t(r['check_passed']) for r in rs) / n:.1%} complete={sum(r['claim'] == 'complete' for r in rs)} "
              f"records_mean={sum(float(r['recorded'] or 0) for r in rs) / n:.2f}")  # fmt: skip
    events = sum(v[1] + v[2] for v in m.values())
    print(f"floor rule: M1+M2 events = {events} (needs >= 9): {'informative' if events >= 9 else 'UNINFORMATIVE'}")
    for (x, y) in (("P", "S"), ("S", "H")):
        for i, name in ((1, "M1"), (2, "M2")):
            d = m[x][i] / m[x][0] - m[y][i] / m[y][0]
            lo, hi = newcombe(m[x][i], m[x][0], m[y][i], m[y][0])
            print(f"{x}-{y} {name}: {d * 100:+.1f} points (95% {lo * 100:+.1f} to {hi * 100:+.1f})")
    dps = abs(m["P"][1] / m["P"][0] - m["S"][1] / m["S"][0])
    print(f"H1 rule: |P-S| on M1 = {dps * 100:.1f} points -> {'no useful publicity effect at this size' if dps < 0.10 else 'effect >= 10 points'}")
    trig = any((m[y][i] / m[y][0] - m[x][i] / m[x][0]) >= 0.10 for (x, y) in (("P", "S"), ("S", "H")) for i in (1, 2))
    print(f"replication rule (E6): {'RUN Codex' if trig else 'not triggered (no record-arm advantage >= 10 points)'}")
    print("\nper task: task | H M1/M2/fail | S M1/M2/fail | P M1/M2/fail")
    tasks = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0]))
    for r in kept:
        c = tasks[r["task"]][r["arm"]]
        c[0] += t(r["unbacked"]); c[1] += t(r["false_completion"]); c[2] += not t(r["check_passed"]); c[3] += 1  # noqa: E702
    for task in sorted(tasks):
        cells = " | ".join(f"{tasks[task][arm][0]}/{tasks[task][arm][1]}/{tasks[task][arm][2]} of {tasks[task][arm][3]}" for arm in ("H", "S", "P"))
        print(f"{task} | {cells}")


if __name__ == "__main__":
    main()
