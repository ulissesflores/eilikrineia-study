"""Second post hoc plan of the study 2 human audit (POSTHOC-STUDY2-AUDIT-SPLIT.md). Post hoc: results are known.

    python3 audit_study2_split.py OUT RATER [RATER...]   # writes OUT/report-split.txt

A: per arm and check result, who read "complete", and the labeller x rater 2 x 2 table. B: the first plan's
agreement table and A again, without answers given in under FAST seconds. Computed once; changes no reading.
`agreement` repeats the per-rater block of audit_study2.report, which stays untouched because the ledger holds
its hash (ponytail: duplication accepted to keep the recorded file byte-identical).
"""

import json
import sys
from pathlib import Path

from audit import kappa
from audit_posthoc import wilson
from audit_study2 import ARMS


def agreement(key, lab, rater):
    """Lines of the first plan's table for one rater: agreement overall and per arm, and the gap between arms."""
    secs = sorted(v["seconds"] for v in lab.values() if v.get("seconds") is not None)
    lines = [f"== rater {rater}: {len(lab)} of {len(key)} items; seconds per item: median "
             f"{secs[len(secs) // 2] if secs else 'n/a'}, shortest {secs[0] if secs else 'n/a'}"]  # fmt: skip
    acc = {}
    for arm in ("all",) + ARMS:
        ids = [i for i in lab if arm == "all" or key[i]["arm"] == arm]
        a = [key[i]["labeller"] == "complete" for i in ids]
        b = [lab[i]["complete"] for i in ids]
        agree = sum(x == y for x, y in zip(a, b, strict=True))
        lo, hi = wilson(agree, len(ids))
        acc[arm] = 100 * agree / len(ids) if ids else float("nan")
        lines.append(f"  {arm:8s} n {len(ids):3d}  agreement {agree}/{len(ids)} = {acc[arm]:.1f}% "
                     f"(95% {100 * lo:.1f} to {100 * hi:.1f})  kappa {kappa(a, b):.2f}  "
                     f"rater says complete {sum(b)}, labeller says complete {sum(a)}")  # fmt: skip
    gap = abs(acc["S"] - acc["control"])
    lines.append(f"  gap in agreement between arms: {gap:.1f} points -> "
                 f"{'MEASUREMENT-LIMITED (gap above 10 points)' if gap > 10 else 'within 10 points'}")
    return lines


FAST = 5.0  # seconds; second plan, computation B


def cells(key, lab, rater):
    """Second plan, computation A: per arm and check result, who read 'complete', and labeller x rater 2 x 2."""
    lines = [f"== rater {rater}: split by arm and check result ({len(lab)} answers)"]
    for arm in ARMS:
        for passed in (True, False):
            ids = [i for i in lab if key[i]["arm"] == arm and key[i]["check_passed"] is passed]
            a = [key[i]["labeller"] == "complete" for i in ids]
            b = [lab[i]["complete"] for i in ids]
            n = len(ids)
            lo_a, hi_a = wilson(sum(a), n)
            lo_b, hi_b = wilson(sum(b), n)
            both, lab_only, rater_only = (sum(x and y for x, y in zip(a, b, strict=True)),
                                          sum(x and not y for x, y in zip(a, b, strict=True)),
                                          sum(y and not x for x, y in zip(a, b, strict=True)))  # fmt: skip
            lines.append(f"  {arm:8s} check {'passed' if passed else 'failed'}  n {n:2d}  "
                         f"labeller complete {sum(a)} ({100 * lo_a:.1f} to {100 * hi_a:.1f})  "
                         f"rater complete {sum(b)} ({100 * lo_b:.1f} to {100 * hi_b:.1f})  "
                         f"2x2 [both {both}, labeller only {lab_only}, rater only {rater_only}, "
                         f"neither {n - both - lab_only - rater_only}]")  # fmt: skip
    return lines


def split(out, raters):
    """Second post hoc plan (POSTHOC-STUDY2-AUDIT-SPLIT.md): A, the split by check result; B, without answers
    under FAST seconds (first plan's table, then A again). Writes report-split.txt next to report.txt."""
    out = Path(out)
    key = {json.loads(x)["id"]: json.loads(x) for x in open(out / "key.jsonl")}
    lines = ["# A. split by check result, all answers"]
    labs = {r: {int(k): v for k, v in json.loads((out / f"labels-{r}.json").read_text()).items()} for r in raters}
    for rater, lab in labs.items():
        lines += cells(key, lab, rater)
    lines.append(f"# B. without answers under {FAST} seconds")
    for rater, lab in labs.items():
        fast = sorted(i for i, v in lab.items() if v.get("seconds") is not None and v["seconds"] < FAST)
        lines.append(f"== rater {rater}: removed {len(fast)} answer(s) {fast}")
        kept = {i: v for i, v in lab.items() if i not in fast}
        lines += agreement(key, kept, rater) + cells(key, kept, rater)
    text = "\n".join(lines)
    (out / "report-split.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    split(sys.argv[1], sys.argv[2:])
