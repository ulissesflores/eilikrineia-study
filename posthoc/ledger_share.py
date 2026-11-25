"""Compute success entries per trial and study 2 false completion.

Round 28 (3): success entries per trial by hidden-check result, and study 2 false completion read
from message or record. EXPLORATORY, POST HOC, computed for this paper (2026-11-24); not
preregistered. Spec fixed before the first run.

Reuses posthoc/ledger_content.py unchanged (kept trials, entry reading as
runner/score_study.recorded, the benchmark
labeller overclaim.claims.classify per entry; gates there: kept counts, entries per trial and
record_false_complete).
Studies 2 and 3, signed arms (study 2 S; study 3 S, K, TD), kept trials, the scored hidden check.
 1. Per trial: number of entries labelled complete ("success entries") and their share of the
 trial's entries.
    Printed by result (failed / passed): mean count, mean per-trial share, and the median per-trial
    share; the
    difference of mean per-trial shares (failed - passed) with a percentile bootstrap interval
    (2,000 resamples of
    trials within each result, seed 2028).
 2. Study 2 only: false completion if read from the message or the record: failed kept trials of S
 whose message
    is labelled complete or that hold >= 1 success entry, over 505. The control has no record, so
    its figure stays
    the message-only 81/493; the two are not a like-for-like contrast.
Output: counts only.
Run from the package root: PYTHONDONTWRITEBYTECODE=1 python posthoc/ledger_share.py  (needs the
package and <RAW>)
"""

import random
import statistics
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ledger_content as L  # noqa: E402


def main():
    """Print success entries per trial and study 2 false completion by source."""
    rng = random.Random(2028)
    print(
        "== Round 28 (3): success entries per trial by hidden-check result (post hoc, exploratory)"
    )
    res = {False: [], True: []}
    s2 = {"fail": 0, "either": 0, "msg": 0, "n": 0}
    for study, arms in (("study2", ("S",)), ("study3", ("S", "K", "TD"))):
        rows = L.kept_rows(study)
        for arm in arms:
            for r in (x for x in rows if x["arm"] == arm):
                ents = [L.classify(t) for t, _ in L.recorded(L.RAW / study / r["trial"])]
                assert len(ents) == int(r["records"])
                k = sum(c.label.value == "complete" for c in ents)
                passed = L.T(r["check_passed"])
                res[passed].append((k, k / len(ents) if ents else 0.0))
                if study == "study2":
                    s2["n"] += 1
                    if not passed:
                        s2["fail"] += 1
                        s2["msg"] += r["claim"] == "complete"
                        s2["either"] += r["claim"] == "complete" or k > 0
    assert (len(res[False]), len(res[True])) == (485, 2238), (len(res[False]), len(res[True]))
    print("gate: 485 failed and 2,238 passed kept trials (round 27)")
    for p in (False, True):
        ks = [x[0] for x in res[p]]
        sh = [x[1] for x in res[p]]
        print(
            f"  check {'passed' if p else 'failed'}: trials {len(ks)}; success entries per trial "
            f"mean "
            f"{statistics.mean(ks):.2f}; per-trial share mean {100 * statistics.mean(sh):.1f}%, "
            f"median "
            f"{100 * statistics.median(sh):.1f}%"
        )
    f, q = [x[1] for x in res[False]], [x[1] for x in res[True]]
    d = statistics.mean(f) - statistics.mean(q)
    bs = sorted(
        statistics.mean(rng.choices(f, k=len(f))) - statistics.mean(rng.choices(q, k=len(q)))
        for _ in range(2000)
    )
    print(
        f"  per-trial share, failed - passed: {100 * d:+.1f} points (95% percentile "
        f"{100 * bs[49]:+.1f} to "
        f"{100 * bs[1949]:+.1f})"
    )
    assert s2["n"] == 505
    print(
        f"\nStudy 2 S, failed kept trials {s2['fail']}: message labelled complete {s2['msg']}; "
        f"message or >= 1 success "
        f"entry {s2['either']} = {s2['either']}/{s2['n']} ({100 * s2['either'] / s2['n']:.1f}%) of "
        f"kept S trials "
        f"(message only {s2['msg']}/{s2['n']} = {100 * s2['msg'] / s2['n']:.1f}%; control, message "
        f"only, 81/493 = 16.4%)"
    )


if __name__ == "__main__":
    main()
