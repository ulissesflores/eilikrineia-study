"""Run the preregistered pilot: 20 tasks x 3 arms x 3 repetitions, shuffled by the preregistration entry's hash.

Usage: python3 run_pilot.py SEED_HEX OUT_DIR [--jobs 3]

Resumable: a trial whose record.json exists is skipped, never rerun.
"""

import argparse
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

TASKS = sorted(p.name for p in Path("/Users/ulissesflores/Developer/eilikrineia-experiment/overclaim/tasks/solvable").iterdir()
               if (p / "task.toml").exists()) + ["billing-month-end", "oncall-rota"]  # fmt: skip
ARMS, REPS = ("H", "S", "P"), 3
RUNNER = Path(__file__).resolve().parent / "run_trial.py"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("seed")
    ap.add_argument("out")
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args()
    assert len(TASKS) == 20, TASKS
    plan = [(t, arm, r) for t in TASKS for arm in ARMS for r in range(1, REPS + 1)]
    random.Random(int(a.seed[:8], 16)).shuffle(plan)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "schedule.txt").write_text("\n".join(f"{i + 1:03d} {t} {arm} r{r}" for i, (t, arm, r) in enumerate(plan)) + "\n")
    log = out / "progress.log"

    def one(item):
        i, (t, arm, r) = item
        d = out / f"{i + 1:03d}-{arm}-{t}-r{r}"
        if (d / "record.json").exists():
            return
        p = subprocess.run([sys.executable, "-I", str(RUNNER), t, arm, str(d)], capture_output=True, text=True)
        line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {d.name} rc={p.returncode} {p.stdout.strip()[-300:]} {p.stderr.strip()[-200:]}"
        with log.open("a") as f:
            f.write(line + "\n")

    with ThreadPoolExecutor(a.jobs) as ex:
        list(ex.map(one, enumerate(plan)))
    print("done", sum(1 for d in out.iterdir() if (d / "record.json").exists()), "of", len(plan))


if __name__ == "__main__":
    main()
