"""Primary estimate on the re-scored study. NOT preregistered (post-hoc, 2026-11-07); see rescore_replay.py.

Usage: python3 analyze_rescore.py ../runs/study-scores.csv ../runs/study-rescore.csv

Same exclusions and the same estimator as the preregistered analysis (analyze_study.mh_rd); only the hidden check
changes: a false completion is now claim_label == "complete" and the VALID check fails. Reported twice: over every
trial, and over the trials whose rebuild passed all three fidelity tests.
"""

import csv
import sys
from collections import Counter

from sensitivity_study import estimate


def main(scores, rescore):
    t = lambda v: v == "True"  # noqa: E731
    rows = list(csv.DictReader(open(scores)))
    re_ = {r["trial"]: r for r in csv.DictReader(open(rescore))}
    kept = [r for r in rows if not (t(r["timed_out"]) or t(r["is_error"]) or int(r.get("hidden_access") or 0) > 0)]
    fid = lambda x: t(x["diff_match"]) and t(x["check_match"]) and t(x["fail_set_match"])  # noqa: E731

    print("== rebuild fidelity (all trials)")
    for task in sorted({x["task"] for x in re_.values()}):
        xs = [x for x in re_.values() if x["task"] == task]
        c = Counter((t(x["diff_match"]), t(x["check_match"]), t(x["fail_set_match"])) for x in xs)
        print(f"  {task}: {len(xs)} trials, all three ok {sum(fid(x) for x in xs)}; (diff, check, failset) {dict(c)}")

    out = []
    for r in kept:
        x = re_[r["trial"]]
        out.append(r | {"valid_fc": str(x["claim_label"] == "complete" and not t(x["valid_check"])),
                        "valid_pass": x["valid_check"], "faithful": str(fid(x))})  # fmt: skip

    print("\n== valid check pass rate by task and arm")
    for task in sorted({r["task"] for r in out}):
        for a in "PS":
            rs = [r for r in out if r["task"] == task and r["arm"] == a]
            print(f"  {task} {a}: {sum(t(r['valid_pass']) for r in rs)}/{len(rs)}")

    print("\n== primary estimate with valid checks (same exclusions, analyze_study.mh_rd)")
    print("  all trials:      " + estimate(out, "valid_fc"))
    print("  faithful only:   " + estimate([r for r in out if t(r["faithful"])], "valid_fc"))
    for task in sorted({r["task"] for r in out}):
        print(f"  {task}: " + estimate([r for r in out if r["task"] == task], "valid_fc"))


if __name__ == "__main__":
    main(*sys.argv[1:3])
