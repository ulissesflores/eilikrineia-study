"""Single entry point: rerun the analyses from the frozen scores, run the tests, verify the seal.

Usage
-----
    python run_all.py

The steps are (1) rerun every analysis that needs only the frozen score files and compare
it byte for byte with the frozen output, including the registered analyses of studies 2 and 3
(``scripts/rerun_studies23.py``: all of study 2; study 3 except its Z1 and pressure-mention
sections, which read the final messages in the raw archive), (2) run the tests that lock the
published numbers, (3) verify the provenance seal. Nothing here calls a model or needs the raw
trial archive.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RERUNS = [
    (
        [
            "analyze.py",
            "../runs/pilot-scores.csv",
            "--exclude",
            "061-S-bughunt-ratelimit-r1",
            "164-H-data-interval-sets-r2",
        ],
        "pilot-analysis.txt",
    ),
    (["analyze_study.py", "../runs/study-scores.csv"], "study-analysis.txt"),
    (
        ["analyze_rescore.py", "../runs/study-scores.csv", "../runs/study-rescore.csv"],
        "study-rescore-analysis.txt",
    ),
]


def rerun():
    """Rerun the score-only analyses and compare them with the frozen outputs.

    Returns
    -------
    bool
        True when every rerun equals its frozen output.
    """
    ok = True
    check = subprocess.run([sys.executable, "scripts/make_results.py", "--check"], cwd=ROOT)
    print(
        f"  {'identical' if check.returncode == 0 else 'DIFFERENT'}: "
        "scripts/make_results.py -> output/results.json"
    )
    ok &= check.returncode == 0
    for cmd, frozen in RERUNS:
        out = subprocess.run(
            [sys.executable, *cmd], cwd=ROOT / "runner", capture_output=True, text=True
        )
        same = out.returncode == 0 and out.stdout == (ROOT / "runs" / frozen).read_text()
        print(f"  {'identical' if same else 'DIFFERENT'}: runner/{cmd[0]} -> runs/{frozen}")
        ok &= same
    ok &= subprocess.run([sys.executable, "scripts/rerun_studies23.py"], cwd=ROOT).returncode == 0
    return ok


def main():
    """Run the three steps and exit non-zero on the first failure.

    Returns
    -------
    int
        Process exit code.
    """
    print("[1/3] rerun analyses from the frozen scores")
    if not rerun():
        return 1
    print("[2/3] tests that lock the published numbers")
    if subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ROOT).returncode:
        return 1
    print("[3/3] provenance seal")
    return subprocess.run([sys.executable, "make_provenance.py", "--verify"], cwd=ROOT).returncode


if __name__ == "__main__":
    sys.exit(main())
