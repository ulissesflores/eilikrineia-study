"""Exploratory sensitivity checks for the main study. NOT preregistered: written after the run, before RESULTS.

Usage: python3 sensitivity_study.py RUNS_DIR SCORES_CSV

Why: the study did not run under one condition. Concurrency went 3 -> 6 -> 10 trials at a time, and the run was paused
for a flight while Ulisses's connection dropped (contract §5, ledger #1412, #1413). Trial 1013 crashed in run_trial.py
and its record was rebuilt by recover_record.py (#1414). These checks repeat the preregistered primary estimate
(analyze_study.mh_rd, same exclusions) inside each phase and without the recovered trial, and report the timeout rate
per arm, which the preregistration names as a threat above 5 points.
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from analyze_study import mh_rd

# Relaunch times from runs/study.out (UTC). A trial belongs to the phase in which it started.
PHASES = (("3 jobs", "2026-11-06T01:52:10"), ("6 jobs", "2026-11-06T11:56:33"),
          ("10 jobs, before the flight pause", "2026-11-06T22:09:36"), ("10 jobs, after the pause", "9999"))  # fmt: skip
t = lambda v: v == "True"  # noqa: E731


def estimate(rows, col="false_completion"):
    tasks = sorted({r["task"] for r in rows})
    strata = []
    for task in tasks:
        c = defaultdict(lambda: [0, 0])
        for r in rows:
            if r["task"] == task:
                c[r["arm"]][0] += t(r[col])
                c[r["arm"]][1] += 1
        strata.append((*c["P"], *c["S"]))
    rd, lo, hi, _, p = mh_rd(strata)
    k = {a: sum(t(r[col]) for r in rows if r["arm"] == a) for a in "PS"}
    n = {a: sum(r["arm"] == a for r in rows) for a in "PS"}
    return f"P {k['P']}/{n['P']} S {k['S']}/{n['S']}; MH P-S {rd * 100:+.1f} (95% {lo * 100:+.1f} to {hi * 100:+.1f}), p {p:.2f}"


def main(runs, scores):
    rows = list(csv.DictReader(open(scores)))
    started = {}
    for f in Path(runs).glob("*/record.json"):
        rec = json.loads(f.read_text())
        started[f.parent.name] = (rec["started"][:19], "recovered" in rec)
    bad = {
        r["trial"]
        for r in rows
        if t(r["timed_out"]) or t(r["is_error"]) or int(r.get("hidden_access") or 0) > 0
    }
    kept = [r for r in rows if r["trial"] not in bad]

    print("== excluded trials")
    for r in rows:
        if r["trial"] in bad:
            why = (
                "timeout"
                if t(r["timed_out"])
                else "agent error"
                if t(r["is_error"])
                else "hidden access"
            )
            print(f"  {r['trial']}: {why}")
    for a in "PS":
        n = sum(r["arm"] == a for r in rows)
        print(
            f"  timeout rate {a}: {sum(t(r['timed_out']) for r in rows if r['arm'] == a)}/{n}"
        )

    print("\n== primary estimate by concurrency phase (trial start time)")
    for i, (name, end) in enumerate(PHASES):
        begin = PHASES[i - 1][1] if i else ""
        part = [r for r in kept if begin <= started[r["trial"]][0] < end]
        print(f"  {name}: {len(part)} trials; {estimate(part)}")

    recovered = sorted(k for k, (_, rec) in started.items() if rec)
    print(f"\n== without the recovered trial(s) {recovered}")
    print("  " + estimate([r for r in kept if r["trial"] not in recovered]))

    # agent_rc 127: the claude command was missing for a moment (Claude Code was being reinstalled), so the agent
    # never ran. The pinned analysis counts them (is_error is empty); here they are dropped.
    recs = {
        f.parent.name: json.loads(f.read_text())
        for f in Path(runs).glob("*/record.json")
    }
    nostart = sorted(k for k, rec in recs.items() if rec.get("agent_rc") == 127)
    print(
        f"\n== without the {len(nostart)} trials whose agent never started (agent_rc 127): {nostart}"
    )
    print("  " + estimate([r for r in kept if r["trial"] not in nostart]))

    print("\n== by Claude Code version")
    for v in sorted(
        {rec.get("cli_version") for rec in recs.values() if rec.get("cli_version")}
    ):
        print(
            f"  {v}: {estimate([r for r in kept if recs[r['trial']].get('cli_version') == v])}"
        )

    access = [
        r
        for r in rows
        if r["trial"] in bad and not t(r["timed_out"]) and not t(r["is_error"])
    ]
    print(
        f"\n== with the hidden-access exclusion(s) put back {[r['trial'] for r in access]}"
    )
    print("  " + estimate(kept + access))

    print("\n== claim records per trial (descriptive)")
    for a in "PS":
        rs = [r for r in kept if r["arm"] == a]
        print(
            f"  {a}: {sum(int(r['records']) for r in rs) / len(rs):.2f} records per trial"
        )
        for task in sorted({r["task"] for r in kept}):
            rt = [r for r in rs if r["task"] == task]
            print(f"    {task}: {sum(int(r['records']) for r in rt) / len(rt):.2f}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
