"""Recompute the headline counts from the frozen per-trial files and write ``output/results.json``.

Only counts that need nothing but the shipped files are recomputed here. Estimates with intervals
come from the frozen analysis outputs and are locked by the tests as text. Two exploratory
estimates that the paper adds are computed with the sealed estimator in ``runner/analyze_study``.

Usage
-----
    python scripts/make_results.py            # write output/results.json
    python scripts/make_results.py --check    # exit 1 if the committed file differs
"""

import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runner"))

from analyze_study import Z, mh_rd  # noqa: E402  (the sealed Mantel-Haenszel estimator)

ALPHA = 0.05 / 6  # study 3
RUNS, AUDIT, OUT = ROOT / "runs", ROOT / "runs" / "study3-audit", ROOT / "output" / "results.json"
RATERS = ("fable", "grok", "hydrogen")


def rows(name):
    """Read one per-trial score file.

    Parameters
    ----------
    name : str
        File name under ``runs/`` without the ``.csv`` extension.

    Returns
    -------
    list of dict
        One dictionary per trial.
    """
    with (RUNS / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


def arm_counts(trials, status=False):
    """Count the outcomes of one arm.

    Parameters
    ----------
    trials : list of dict
        Trials of one arm, exclusions already applied.
    status : bool
        Also count failed trials that answered ``STATUS: COMPLETE`` (study 3 only).

    Returns
    -------
    dict
        Counts of kept trials, passed, said complete, false completion and false non-completion.
    """
    ok = [r["check_passed"] == "True" for r in trials]
    said = [r["claim"] == "complete" for r in trials]
    out = {
        "kept": len(trials),
        "passed": sum(ok),
        "said_complete": sum(said),
        "false_completion": sum(s and not p for p, s in zip(ok, said, strict=True)),
        "false_non_completion": sum(p and not s for p, s in zip(ok, said, strict=True)),
    }
    if status:
        out["failed"] = out["kept"] - out["passed"]
        out["status_complete_on_failure"] = sum(
            not p and r["status"] == "COMPLETE" for p, r in zip(ok, trials, strict=True)
        )
    return out


def quantile(tail):
    """Two-sided normal quantile, by bisection on ``erfc`` (standard library only).

    Parameters
    ----------
    tail : float
        Total probability in the two tails.

    Returns
    -------
    float
        The quantile z with P(|N(0, 1)| > z) equal to ``tail``.
    """
    lo, hi = 0.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if math.erfc(mid / math.sqrt(2)) > tail else (lo, mid)
    return lo


def interval(strata, tail=0.05):
    """Mantel-Haenszel risk difference with an interval, in percentage points.

    Parameters
    ----------
    strata : list of tuple
        One ``(events_1, n_1, events_0, n_0)`` per task.
    tail : float
        Total probability outside the interval.

    Returns
    -------
    list of float
        Difference, lower bound and upper bound, rounded to one decimal.
    """
    rd, lo, _, _, _ = mh_rd(strata)
    half = quantile(tail) * (rd - lo) / Z
    return [round(100 * v, 1) for v in (rd, rd - half, rd + half)]


def compute():
    """Recompute every count this package derives from the shipped files.

    Returns
    -------
    dict
        Trial totals, study 3 counts per arm, study 2 numerators (overall and per task) and the
        labeller audit agreement.
    """
    files = {
        "pilot": "pilot-scores",
        "study1": "study-scores",
        "study2": "study2-scores",
        "study3": "study3-scores",
    }
    trials = {k: len(rows(v)) for k, v in files.items()}
    kept3 = [
        r for r in rows("study3-scores") if r["timed_out"] != "True" and r["is_error"] != "True"
    ]
    study3 = {
        arm: arm_counts([r for r in kept3 if r["arm"] == arm], status=True)
        for arm in ("S", "I", "K", "TD")
    }
    # Study 2's exclusions need the raw trial folders, so only the numerators are recomputed:
    # a trial that timed out or errored neither passes nor is labelled complete.
    kept2 = [
        r for r in rows("study2-scores") if r["timed_out"] != "True" and r["is_error"] != "True"
    ]
    study2 = {}
    for arm in ("S", "control"):
        c = arm_counts([r for r in kept2 if r["arm"] == arm])
        study2[arm] = {k: c[k] for k in ("passed", "false_completion", "false_non_completion")}
    # Per task: how often the agent said "complete" after passing and after failing.
    by_task = {}
    for arm in ("S", "control"):
        by_task[arm] = {}
        for task in sorted({r["task"] for r in kept2}):
            c = arm_counts([r for r in kept2 if r["arm"] == arm and r["task"] == task])
            by_task[arm][task] = {
                "passed": c["passed"],
                "complete_after_passing": c["passed"] - c["false_non_completion"],
                "complete_after_failing": c["false_completion"],
            }
    tasks = sorted({r["task"] for r in kept3})

    def cell(arm, task):
        """Count false completions and kept trials of one arm and task in study 3."""
        c = arm_counts([r for r in kept3 if r["arm"] == arm and r["task"] == task])
        return c["false_completion"], c["kept"]

    # Exploratory: the equivalence interval of K - S that the frozen output does not print, and
    # the study 2 pass-rate difference (kept trials per task are the frozen denominators).
    kept_by_task = {"S": (171, 163, 171), "control": (156, 166, 171)}
    exploratory = {
        "study3_k_minus_s_false_completion_tost": interval(
            [cell("K", t) + cell("S", t) for t in tasks], tail=2 * ALPHA
        ),
        "study2_pass_rate_s_minus_control": interval(
            [
                (by_task["S"][t]["passed"], kept_by_task["S"][i])
                + (by_task["control"][t]["passed"], kept_by_task["control"][i])
                for i, t in enumerate(sorted(by_task["S"]))
            ]
        ),
    }
    key = {r["id"]: r for r in map(json.loads, (AUDIT / "key.jsonl").open())}
    audit = {}
    for rater in RATERS:
        lab = {
            int(k): v["label"] for k, v in json.loads((AUDIT / f"{rater}.json").read_text()).items()
        }
        audit[rater] = {}
        for arm in ("all", "S", "I", "K", "TD"):
            ids = [i for i, k in key.items() if arm in ("all", k["arm"])]
            agree = sum((key[i]["labeller"] == "complete") == (lab[i] == "complete") for i in ids)
            audit[rater][arm] = {"agree": agree, "n": len(ids)}
    owner = json.loads((AUDIT / "owner40-raw.json").read_text())
    return {
        "trials": {**trials, "total": sum(trials.values())},
        "study3": study3,
        "study3_status_complete_on_failure": {
            "complete": sum(v["status_complete_on_failure"] for v in study3.values()),
            "failed": sum(v["failed"] for v in study3.values()),
        },
        "study2_numerators": study2,
        "study2_by_task": by_task,
        "exploratory": exploratory,
        "labeller_audit": audit,
        "owner_labels": {
            "first_attempt": len(json.loads((AUDIT / "owner-partial.json").read_text())),
            "posthoc": len(owner),
            "posthoc_agree_with_labeller": sum(
                (v["label"] == "complete") == (key[int(i)]["labeller"] == "complete")
                for i, v in owner.items()
            ),
        },
        # Bytecode written by the rerun itself and Finder metadata are not sealed files.
        "sealed_third_party_files": sum(
            1
            for p in (ROOT / "overclaim").rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.name != ".DS_Store"
        )
        - 1,
    }


if __name__ == "__main__":
    text = json.dumps(compute(), indent=1) + "\n"
    if "--check" in sys.argv:
        sys.exit(
            0 if OUT.read_text() == text else "output/results.json differs from the recomputation"
        )
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")
