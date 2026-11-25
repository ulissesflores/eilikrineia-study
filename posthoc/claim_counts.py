# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Carlos Ulisses Flores (Codex Hash Ltda.)
"""Count claim-record entries per trial, P against S, study 1.

Computed for this paper. The specification was fixed before computing; it is not published.

Data: the `records` column of runs/study-scores.csv (entries the claim tool appended in the trial),
over the kept trials of the registered study 1 analysis (analyze_study.py exclusions: timeouts,
agent errors, hidden access). Gate: the frozen descriptive means 3.67 (P) and 4.82 (S) of
runs/study-sensitivity.txt.

Test: van Elteren's stratified Wilcoxon rank-sum test (strata = the three tasks, weights 1 / (N_k +
1), mid-ranks for ties with the tie-corrected variance, normal approximation, two-sided), chosen
because entry counts are skewed and tied and the registered analysis stratifies by task. Also shown,
descriptive: per-task means and medians, and the Mantel-Haenszel-type rate ratio of entries P / S
stratified by task (sum_k E1k*n0k/N_k / sum_k E0k*n1k/N_k), without an interval (entries within a
trial are not independent events). Pilot: not tested (descriptive means are frozen).

Inputs
------
- runs/study-scores.csv and runs/study-sensitivity.txt of the package (needs the package only).

Outputs
-------
- Counts and statistics only, on standard output; the committed posthoc/claim_counts.txt must be
  reproduced byte for byte.

Usage
-----
    PYTHONDONTWRITEBYTECODE=1 python posthoc/claim_counts.py

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
import math
import statistics
import sys
from pathlib import Path

sys.dont_write_bytecode = True
# the package root; raw/ = <RAW>, the unpacked raw archive
PKG = Path(__file__).resolve().parent.parent
T = lambda v: v == "True"  # noqa: E731


def midranks(values):
    """Return the mid-ranks of a list of numbers.

    Parameters
    ----------
    values : list of float
        Numbers to rank.

    Returns
    -------
    list of float
        Rank of each value, ties sharing their mean rank.
    """
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks, i = [0.0] * len(values), 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def van_elteren(strata):
    """Return the van Elteren stratified rank-sum test (z, two-sided p).

    Parameters
    ----------
    strata : list of tuple
        One ``(x_group1, x_group0)`` pair of value lists per stratum (task).

    Returns
    -------
    tuple of float
        The z statistic and its two-sided normal p value.
    """
    t = e = v = 0.0
    for g1, g0 in strata:
        n1, n0 = len(g1), len(g0)
        n = n1 + n0
        r = midranks(list(g1) + list(g0))
        w = sum(r[:n1])
        ties = {}
        for x in list(g1) + list(g0):
            ties[x] = ties.get(x, 0) + 1
        tc = sum(c**3 - c for c in ties.values()) / (n * (n - 1))
        wt = 1 / (n + 1)
        t += wt * w
        e += wt * n1 * (n + 1) / 2
        v += wt * wt * n1 * n0 / 12 * ((n + 1) - tc)
    z = (t - e) / math.sqrt(v)
    return z, math.erfc(abs(z) / math.sqrt(2))


def selftest():
    """Check the van Elteren test against known answers."""
    import itertools

    z, _ = van_elteren([([1, 2, 3], [4, 5, 6])])
    assert abs(z - (6 - 10.5) / math.sqrt(5.25)) < 1e-9
    strata = [([0, 1, 1, 3], [1, 2, 2, 5]), ([2, 2, 4, 4], [0, 2, 3, 4])]
    t_obs, means, vars_ = 0.0, 0.0, 0.0
    for g1, g0 in strata:
        pool, n1 = list(g1) + list(g0), len(g1)
        r = midranks(pool)
        w = 1 / (len(pool) + 1)
        sums = [sum(r[i] for i in c) for c in itertools.combinations(range(len(pool)), n1)]
        mu = sum(sums) / len(sums)
        t_obs += w * sum(r[:n1])
        means += w * mu
        vars_ += w * w * sum((x - mu) ** 2 for x in sums) / len(sums)
    z_exact = (t_obs - means) / math.sqrt(vars_)
    z, _ = van_elteren(strata)
    assert abs(z - z_exact) < 1e-9, (z, z_exact)
    print(
        f"self-test: no-ties z {(6 - 10.5) / math.sqrt(5.25):.3f} reproduced; tied two-stratum z "
        f"{z:.4f} = exact "
        f"permutation moments {z_exact:.4f}"
    )


def main():
    """Print the claim-record entry counts per trial for study 1 and the pilot."""
    selftest()
    rows = [
        r for r in csv.DictReader(open(PKG / "runs" / "study-scores.csv")) if r["arm"] in ("P", "S")
    ]
    kept = [
        r
        for r in rows
        if not (T(r["timed_out"]) or T(r["is_error"]) or int(r.get("hidden_access") or 0) > 0)
    ]
    x = {a: [int(r["records"]) for r in kept if r["arm"] == a] for a in "PS"}
    m = {a: sum(v) / len(v) for a, v in x.items()}
    assert (len(kept), round(m["P"], 2), round(m["S"], 2)) == (1992, 3.67, 4.82)
    print(
        f"== Study 1, kept trials {len(kept)} (P {len(x['P'])}, S {len(x['S'])})  [frozen means "
        f"3.67 / 4.82: True]"
    )
    for a in "PS":
        print(
            f"  {a}: entries {sum(x[a])}, mean {m[a]:.2f}, median {statistics.median(x[a])}, "
            f"trials with none "
            f"{sum(v == 0 for v in x[a])}"
        )
    strata, num, den = [], 0.0, 0.0
    for task in sorted({r["task"] for r in kept}):
        g = {
            a: [int(r["records"]) for r in kept if r["arm"] == a and r["task"] == task]
            for a in "PS"
        }
        strata.append((g["P"], g["S"]))
        n = len(g["P"]) + len(g["S"])
        num += sum(g["P"]) * len(g["S"]) / n
        den += sum(g["S"]) * len(g["P"]) / n
        print(
            f"  {task}: P mean {sum(g['P']) / len(g['P']):.2f} (median "
            f"{statistics.median(g['P'])}, n {len(g['P'])}), "
            f"S mean {sum(g['S']) / len(g['S']):.2f} (median {statistics.median(g['S'])}, n "
            f"{len(g['S'])})"
        )
    z, p = van_elteren(strata)
    print(f"  van Elteren stratified rank test, P vs S: z = {z:.2f}, two-sided p = {p:.2g}")
    print(
        f"  task-stratified rate ratio of entries P / S: {num / den:.2f} (descriptive, no interval)"
    )

    print(
        "\nPilot: descriptive only; its means (3.49 / 4.10, kept trials) are the frozen "
        "runs/pilot-analysis.txt."
    )


if __name__ == "__main__":
    main()
