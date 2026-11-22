"""Z4 step 2 (study 3 plan, E17): validate each writer's acceptance tests on the reference solution, then run the
valid tests on every rebuilt study 2 workspace. Exploratory, NOT preregistered (2026-11-08).

1. Validity: for each writer set (runs/z4-writers/<task>/<writer>-r<k>/test_acceptance.py), the tests run on the task's
   starting repo with the reference solution laid over it. Tests that fail there are dropped, never fixed by hand, and
   the kept set is the "validated" set ("spec-derived, reference-filtered").
2. Catch: each study 2 trial is rebuilt from its transcript (runner/rescore_replay.py, same fidelity checks), and every
   validated set of its task runs on the rebuilt workspace. A set "flags" the trial when any kept test fails, errors
   or times out. The task's original visible tests (restored from the pinned repo, never the agent's copy) are the
   baseline (Z2).
Reported per writer: validity, flag rate on trials whose hidden check failed (catch) and passed (disagreement), on
faithful rebuilds only. The writer is NOT chosen by catch rate (owner's decision 2026-11-08): this is the predicted
ceiling.

Model-written test code runs under `sandbox-exec` (no network, writes only inside the temporary directory).

Usage: python3 z4_score_tests.py WRITERS_DIR RUNS_DIR SCORES_CSV OUT_PREFIX [--jobs N] [--limit N]
"""

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from rescore_replay import TASKS, profile, rebuild

PY = "/opt/homebrew/bin/python3.11"
TIMEOUT = 180
UNIT = r'''
import json, sys, unittest
sys.path.insert(0, ".")
res = {}
class R(unittest.TextTestResult):
    def addSuccess(self, t): res[t.id()] = "ok"
    def addFailure(self, t, e): res[t.id()] = "fail"
    def addError(self, t, e): res[t.id()] = "error"
    def addSkip(self, t, r): res[t.id()] = "skip"
    def addExpectedFailure(self, t, e): res[t.id()] = "ok"
    def addUnexpectedSuccess(self, t): res[t.id()] = "fail"
try:
    suite = unittest.defaultTestLoader.loadTestsFromName("acceptance.test_acceptance")
except Exception as e:
    print(json.dumps({"__import__": repr(e)[:300]})); sys.exit(0)
unittest.TextTestRunner(resultclass=R, stream=open("/dev/null", "w")).run(suite)
print(json.dumps(res))
'''


def run_tests(ws, test_file, tmp, kind="acceptance"):
    """{test_id: status} for the writer file placed in ws; {'__timeout__': ...} on timeout."""
    if kind == "acceptance":
        (ws / "acceptance").mkdir(exist_ok=True)
        (ws / "acceptance" / "__init__.py").write_text("")
        shutil.copy(test_file, ws / "acceptance" / "test_acceptance.py")
        (ws / "_z4unit.py").write_text(UNIT)
        cmd = [PY, "_z4unit.py"]
    else:  # the task's original visible tests
        shutil.rmtree(ws / "tests", ignore_errors=True)
        shutil.copytree(test_file, ws / "tests")
        cmd = [PY, "-m", "unittest", "discover", "-s", "tests", "-t", "."]
    prof = Path(tmp) / "z4.sb"
    prof.write_text(profile(str(tmp)))
    try:
        p = subprocess.run(["sandbox-exec", "-f", str(prof), *cmd], cwd=ws, capture_output=True, text=True,
                           timeout=TIMEOUT, stdin=subprocess.DEVNULL)  # fmt: skip
    except subprocess.TimeoutExpired:
        return {"__timeout__": "timeout"}
    if kind != "acceptance":
        return {"visible": "ok" if p.returncode == 0 else "fail"}
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"__crash__": (p.stderr or "")[-300:]}


def writer_sets(wdir):
    return sorted(p for p in Path(wdir).glob("*/*-r*/test_acceptance.py"))


def validate(test_file):
    task = test_file.parent.parent.name
    with tempfile.TemporaryDirectory(prefix="z4ref-") as tmp:
        tmp = str(Path(tmp).resolve())
        ws = Path(tmp) / "work"
        shutil.copytree(TASKS / task / "repo", ws)
        shutil.copytree(TASKS / task / "solution", ws, dirs_exist_ok=True)
        res = run_tests(ws, test_file, tmp)
    kept = sorted(k for k, v in res.items() if v == "ok" and not k.startswith("__"))
    return {"set": str(test_file.parent.relative_to(test_file.parent.parent.parent)), "task": task,
            "writer": test_file.parent.name.rsplit("-r", 1)[0], "tests": len([k for k in res if not k.startswith("__")]),
            "kept": kept, "problem": next((f"{k}: {v}" for k, v in res.items() if k.startswith("__")), "")}  # fmt: skip


def score_trial(args):
    trial, sets = args
    flags = {}

    def hook(scratch, snap, task, row):
        tmp = str(Path(scratch).parent)
        for s in sets[task]:
            ws = Path(scratch) / "ws"
            shutil.rmtree(ws, ignore_errors=True)
            shutil.copytree(snap, ws)
            res = run_tests(ws, s["file"], tmp)
            bad = [k for k in s["kept"] if res.get(k) != "ok"]
            flags[s["set"]] = bool(bad) or "__timeout__" in res or "__crash__" in res or "__import__" in res
        ws = Path(scratch) / "ws"
        shutil.rmtree(ws, ignore_errors=True)
        shutil.copytree(snap, ws)
        flags["visible-tests"] = run_tests(ws, TASKS / task / "repo" / "tests", tmp, kind="visible").get("visible") != "ok"

    row = rebuild(trial, extra=hook)
    row["faithful"] = row["diff_match"] and row["check_match"] and row["fail_set_match"]
    row["flags"] = flags
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("writers")
    ap.add_argument("runs")
    ap.add_argument("scores")
    ap.add_argument("out")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    vals = []
    for f in writer_sets(a.writers):
        v = validate(f)
        v["file"] = str(f)
        vals.append(v)
        print(f"valid {v['set']}: kept {len(v['kept'])}/{v['tests']} {v['problem']}", flush=True)
    Path(a.out + "-validity.json").write_text(json.dumps(vals, indent=1))
    sets = defaultdict(list)
    for v in vals:
        if v["kept"]:
            sets[v["task"]].append(v)
    t = lambda x: x == "True"  # noqa: E731
    rows = [r for r in csv.DictReader(open(a.scores)) if not (t(r["timed_out"]) or t(r["is_error"]))
            and (Path(a.runs) / r["trial"] / "record.json").exists()]  # fmt: skip
    rows = [r for r in rows if json.loads((Path(a.runs) / r["trial"] / "record.json").read_text()).get("agent_rc") not in (126, 127)]
    rows = sorted(rows, key=lambda r: r["trial"])[: a.limit or None]
    claim = {r["trial"]: r["claim"] for r in rows}
    with ProcessPoolExecutor(a.jobs) as ex, open(a.out + "-trials.jsonl", "w") as f:
        done = 0
        for row in ex.map(score_trial, [(Path(a.runs) / r["trial"], dict(sets)) for r in rows]):
            row["claim"] = claim[row["trial"]]
            f.write(json.dumps(row) + "\n")
            done += 1
            if done % 50 == 0:
                print("trials", done, flush=True)
    report(a.out)


def report(out):
    rows = [json.loads(x) for x in open(out + "-trials.jsonl")]
    vals = json.loads(Path(out + "-validity.json").read_text())
    fa = [r for r in rows if r["faithful"]]
    print(f"\ntrials {len(rows)}, faithful rebuilds {len(fa)}")
    print("\n== validity on the reference solution (tests kept / written)")
    for v in vals:
        print(f"{v['set']}: {len(v['kept'])}/{v['tests']} {v['problem']}")
    names = sorted({k for r in fa for k in r["flags"]})
    print("\n== flags on faithful rebuilds: hidden check failed (catch) | passed (disagreement) | false 'complete' caught")
    for n in names:
        sub = [r for r in fa if n in r["flags"]]
        fail = [r for r in sub if not r["recorded_check"]]
        ok = [r for r in sub if r["recorded_check"]]
        fc = [r for r in fail if r["claim"] == "complete"]
        c1, c2, c3 = (sum(r["flags"][n] for r in g) for g in (fail, ok, fc))
        print(f"{n}: catch {c1}/{len(fail)} | disagree {c2}/{len(ok)} | false complete caught {c3}/{len(fc)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        report(sys.argv[2])
    else:
        main()
