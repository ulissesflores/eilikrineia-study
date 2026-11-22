"""Z4 step 1 (study 3 plan, E17): candidate test writers write acceptance tests from the task text only.
Exploratory, NOT preregistered (2026-11-08).

Each writer gets a fresh temporary copy of the task's starting repository (never the solution, never the hidden check)
and the task text, and must write one file, `acceptance/test_acceptance.py` (unittest), with one TestCase class per
requirement it finds in the task. Claude writers run through `claude -p` with the trial runner's isolation flags;
Gemini runs through Antigravity (`agy`, Google subscription). GPT through `codex exec` is kept but unused: on
2026-11-08 the ChatGPT workspace was out of credits.

Usage: python3 z4_write_tests.py OUT_DIR [--writers haiku,sonnet,opus,gemini] [--runs 3] [--jobs 6]
Output: OUT_DIR/<task>/<writer>-r<k>/{test_acceptance.py, writer.stdout, writer.stderr, meta.json}
"""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "overclaim" / "tasks" / "solvable"
TASK_IDS = ("feature-toml-config", "feature-uri-resolve", "text-template-engine")
CLAUDE = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}
PROMPT = """You are the test writer. Another developer will implement the task below later; you write only its \
acceptance tests, before any implementation exists.

Write exactly one file, `acceptance/test_acceptance.py` (create the `acceptance` folder and an empty \
`acceptance/__init__.py`), using only the Python standard library `unittest`. Rules:
- One `unittest.TestCase` class per requirement you find in the task text, named `Req01_<short_name>`, \
`Req02_<short_name>`, ... in the order the task states them. Put the requirement, quoted or paraphrased from the \
task, in the class docstring.
- Every test checks behaviour that the task text states. Do not test anything the task leaves open.
- Use only the public names the task text or the existing code define. The code will be importable from the \
repository root.
- Do not implement the task and do not change any other file. You may read the repository and run the existing tests.
- The tests are expected to fail now, because nothing is implemented yet.

Task:
"""


def run_writer(task, writer, k, out_root):
    out = out_root / task / f"{writer}-r{k}"
    if (out / "meta.json").exists():
        return out
    out.mkdir(parents=True, exist_ok=True)
    text = tomllib.loads((TASKS / task / "task.toml").read_text())["prompt"].strip()
    with tempfile.TemporaryDirectory(prefix="writer-") as tmp:
        ws = Path(tmp) / "work"
        shutil.copytree(TASKS / task / "repo", ws)
        env = {k_: v for k_, v in os.environ.items() if not k_.startswith("ANTHROPIC_")}
        if writer in CLAUDE:
            cmd = ["claude", "-p", PROMPT + text, "--model", CLAUDE[writer], "--tools", "Bash,Read,Write,Glob,Grep",
                   "--disable-slash-commands", "--strict-mcp-config", "--setting-sources", "",
                   "--no-session-persistence", "--permission-mode", "bypassPermissions", "--output-format",
                   "stream-json", "--verbose", "--max-turns", "60"]  # fmt: skip
        elif writer == "gemini":  # Google subscription through Antigravity; -p must come before --model
            cmd = ["/Users/ulissesflores/.local/bin/agy", "-p", PROMPT + text, "--model", "gemini-4-argon-high",
                   "--dangerously-skip-permissions", "--add-dir", str(ws)]  # fmt: skip
        else:
            home = Path(tmp) / "codex-home"
            home.mkdir()
            src = Path.home() / ".codex" / "auth.json"
            if src.exists():
                shutil.copy(src, home / "auth.json")
            env["CODEX_HOME"] = str(home)
            cmd = ["/opt/homebrew/bin/codex", "exec", "--skip-git-repo-check", "--sandbox", "workspace-write",
                   "--json", PROMPT + text]  # fmt: skip
        t0 = time.time()
        p = subprocess.run(cmd, cwd=ws, env=env, capture_output=True, text=True, timeout=1800, stdin=subprocess.DEVNULL)
        (out / "writer.stdout").write_text(p.stdout)
        (out / "writer.stderr").write_text(p.stderr)
        f = ws / "acceptance" / "test_acceptance.py"
        if f.exists():
            shutil.copy(f, out / "test_acceptance.py")
    meta = {"task": task, "writer": writer, "run": k, "rc": p.returncode, "seconds": round(time.time() - t0, 1),
            "wrote_tests": (out / "test_acceptance.py").exists()}
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--writers", default="haiku,sonnet,opus,gemini")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()
    jobs = [(t, w, k) for k in range(1, a.runs + 1) for w in a.writers.split(",") for t in TASK_IDS]
    with ThreadPoolExecutor(a.jobs) as ex:
        for out in ex.map(lambda j: run_writer(*j, Path(a.out)), jobs):
            m = json.loads((out / "meta.json").read_text())
            print(m["task"], m["writer"], m["run"], "rc", m["rc"], "tests", m["wrote_tests"], m["seconds"], "s", flush=True)


if __name__ == "__main__":
    main()
