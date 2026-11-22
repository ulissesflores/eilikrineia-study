"""Run a batch of trials (tasks x arms x repetitions), shuffled by a seed taken from a ledger entry hash.

Usage: python3 run_batch.py SEED_HEX OUT_DIR --tasks T1,T2 --arms P,S --reps N [--jobs 3] [--timeout 1200] [run_trial options]
                            [--start-util U --max-spend 0.40 --max-weekly 0.90]

Used for the E8 screening and the E10 main study; the pilot keeps its own pinned run_pilot.py.
Resumable: a trial whose record.json exists is skipped, never rerun.
Quota guard: before each trial, the weekly utilization seen by the latest finished trial is read from its transcript;
no new trial starts once it reaches --max-weekly, or once it has grown by --max-spend since --start-util.
"""

import argparse
import json
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

RUNNER = Path(__file__).resolve().parent / "run_trial.py"


def latest_utilization(out, now=None):
    """Seven-day utilization seen by the latest finished trial; 0 once that window has reset (review A, item 1)."""
    now = now if now is not None else datetime.now(timezone.utc).timestamp()
    done = sorted((d for d in out.iterdir() if (d / "record.json").exists()), key=lambda d: (d / "record.json").stat().st_mtime)
    for d in reversed(done):
        for line in reversed((d / "agent.stdout").read_text().splitlines()):
            if '"rate_limit_event"' in line:
                w = (json.loads(line)["rate_limit_info"].get("unifiedWindows") or {}).get("seven_day") or {}
                if w.get("utilization") is not None:
                    return 0.0 if (w.get("resetsAt") or now + 1) <= now else w["utilization"]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("seed")
    ap.add_argument("out")
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--arms", required=True)
    ap.add_argument("--reps", type=int, required=True)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=1200)
    ap.add_argument("--start-util", type=float)
    ap.add_argument("--max-spend", type=float, default=0.40)
    ap.add_argument("--max-weekly", type=float, default=0.90)
    a, extra = ap.parse_known_args()  # anything else (--effort, --image, ...) goes to every run_trial.py call
    tasks, arms = a.tasks.split(","), a.arms.split(",")
    plan = [(t, arm, r) for t in tasks for arm in arms for r in range(1, a.reps + 1)]
    random.Random(int(a.seed[:8], 16)).shuffle(plan)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    width = len(str(len(plan)))
    (out / "schedule.txt").write_text("\n".join(f"{i + 1:0{width}d} {t} {arm} r{r}" for i, (t, arm, r) in enumerate(plan)) + "\n")
    log = out / "progress.log"

    def one(item):
        i, (t, arm, r) = item
        d = out / f"{i + 1:0{width}d}-{arm}-{t}-r{r}"
        if (d / "record.json").exists():
            return
        if (d / "agent.stdout").exists():  # the agent finished but the harness crashed after it: never rerun (item 7)
            with log.open("a") as f:
                f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} HARNESS-CRASH kept, not rerun: {d.name}\n")
            return
        u = latest_utilization(out)
        if u is not None and (u >= a.max_weekly or (a.start_util is not None and u - a.start_util >= a.max_spend)):
            with log.open("a") as f:
                f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} QUOTA-STOP before {d.name}: weekly {u}\n")
            return
        p = subprocess.run([sys.executable, "-I", str(RUNNER), t, arm, str(d), "--timeout", str(a.timeout), *extra],
                           capture_output=True, text=True)  # fmt: skip
        line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {d.name} rc={p.returncode} {p.stdout.strip()[-300:]} {p.stderr.strip()[-200:]}"
        with log.open("a") as f:
            f.write(line + "\n")

    with ThreadPoolExecutor(a.jobs) as ex:
        list(ex.map(one, enumerate(plan)))
    print("done", sum(1 for d in out.iterdir() if (d / "record.json").exists()), "of", len(plan))


if __name__ == "__main__":
    main()
