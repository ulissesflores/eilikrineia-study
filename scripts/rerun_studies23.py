"""Rerun the registered analyses of studies 2 and 3 from the frozen score files, unchanged.

``runner/analyze_study2.py`` and ``runner/analyze_study3.py`` read a folder of raw trials besides
the score file. This script stands in for that folder with what the package ships, runs the sealed
code as it is, and compares the output with the frozen ``runs/study{2,3}-analysis.txt``.

- Study 2 reads only each trial's ``agent_rc`` (an exit code of 127 means the agent never started).
  ``runs/study2-agent-rc.csv`` holds it for all 1,082 scored trials, extracted from the raw
  ``record.json`` files with ``--extract``. The rerun must equal the frozen output line for line.
- Study 3 also reads each trial's final message, for the Z1 relabelling and the exploratory count
  of messages that mention the pressure frame. Messages are in the raw archive only, so the script
  feeds an empty message to every trial: every line must equal the frozen output except the lines of
  those text-dependent sections (``TEXT_SECTIONS``), which need the archive and are reported, not
  hidden.

Both analysers print a ``dict`` built from a ``set``, whose key order depends on the interpreter's
hash seed; such lines are compared as dictionaries.

Usage
-----
    python scripts/rerun_studies23.py                       # exit 1 on any difference
    python scripts/rerun_studies23.py --extract RAW_STUDY2  # rewrite runs/study2-agent-rc.csv
"""

import ast
import csv
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
RC = RUNS / "study2-agent-rc.csv"
TEXT_SECTIONS = (
    "== z1_false_completion",
    "== z1_false_non_completion",
    "== exploratory manipulation check",
)
DICT = re.compile(r"\{[^{}]*\}")

STUDY3 = """
import sys
sys.path.insert(0, {runner!r})
import analyze_study3
analyze_study3.final_message = lambda trial: ""  # messages are in the raw archive only
analyze_study3.main({runs!r}, {scores!r})
"""


def extract(raw):
    """Write ``trial,agent_rc`` for every trial folder of the raw study 2 archive."""
    rows = sorted(
        (d.name, json.loads((d / "record.json").read_text()).get("agent_rc"))
        for d in Path(raw).iterdir()
        if (d / "record.json").exists()
    )
    with RC.open("w", newline="") as f:
        csv.writer(f).writerows([("trial", "agent_rc"), *rows])
    print(f"wrote {RC.relative_to(ROOT)}: {len(rows)} trials")


def same_line(a, b):
    """Compare two output lines, reading any ``{...}`` literal as a dictionary."""
    if a == b:
        return True
    da, db = DICT.findall(a), DICT.findall(b)
    if not da or len(da) != len(db) or DICT.sub("{}", a) != DICT.sub("{}", b):
        return False
    return all(ast.literal_eval(x) == ast.literal_eval(y) for x, y in zip(da, db, strict=True))


def compare(out, frozen, skip=()):
    """Return (differing lines outside ``skip`` sections, lines inside them that differ)."""
    new, old = out.splitlines(), frozen.splitlines()
    if len(new) != len(old):
        return [f"line count {len(new)} != {len(old)}"], 0
    bad, skipped, section = [], 0, ""
    for i, (a, b) in enumerate(zip(new, old, strict=True), 1):
        if b.startswith(("==", "########")):
            section = b
        if same_line(a, b):
            continue
        if skip and section.startswith(skip):
            skipped += 1
        else:
            bad.append(f"line {i}: {a!r} != {b!r}")
    return bad, skipped


def run(args):
    """Run a Python command from ``runner/`` and return its standard output."""
    out = subprocess.run(
        [sys.executable, *args], cwd=ROOT / "runner", capture_output=True, text=True
    )
    if out.returncode:
        sys.exit(f"failed: {args[0]}\n{out.stderr}")
    return out.stdout


def main():
    """Rerun both analyses and print one verdict line each; exit 1 on a difference."""
    rc = {r["trial"]: r["agent_rc"] for r in csv.DictReader(RC.open())}
    scored = {r["trial"] for r in csv.DictReader((RUNS / "study2-scores.csv").open())}
    if set(rc) != scored:
        sys.exit("study2-agent-rc.csv does not cover exactly the scored trials of study 2")
    ok = True
    with tempfile.TemporaryDirectory() as raw:
        for trial, code in rc.items():
            (Path(raw) / trial).mkdir()
            agent_rc = None if code == "" else int(code)
            (Path(raw) / trial / "record.json").write_text(json.dumps({"agent_rc": agent_rc}))
        out = run(["analyze_study2.py", raw, str(RUNS / "study2-scores.csv")])
    bad, _ = compare(out, (RUNS / "study2-analysis.txt").read_text())
    verdict = "identical" if not bad else "DIFFERENT"
    print(f"  {verdict}: runner/analyze_study2.py -> runs/study2-analysis.txt")
    ok &= not bad
    with tempfile.TemporaryDirectory() as raw:
        code = STUDY3.format(
            runner=str(ROOT / "runner"), runs=raw, scores=str(RUNS / "study3-scores.csv")
        )
        out = run(["-c", code])
    bad3, skipped = compare(out, (RUNS / "study3-analysis.txt").read_text(), TEXT_SECTIONS)
    print(
        f"  {'identical' if not bad3 else 'DIFFERENT'}: "
        "runner/analyze_study3.py -> runs/study3-analysis.txt"
        f" ({skipped} lines of the Z1 and pressure-mention sections need the raw archive)"
    )
    ok &= not bad3
    for line in bad + bad3:
        print("   ", line)
    return 0 if ok else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["--extract"]:
        extract(sys.argv[2])
    else:
        sys.exit(main())
