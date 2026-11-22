"""Arm TD input (study 3, E19): the Opus writer's three reference-validated test sets per task, as the files mounted in
the developer's workspace under acceptance/. Tests that failed on the reference solution in Z4 (runs/z4-validity.json)
are cut from the source text, never edited; everything else is kept byte for byte. The result is checked twice: every
kept test passes on the reference solution, and the starting repo fails some (the developer starts red).

Usage: python3 td_build.py OUT_DIR   (writes OUT_DIR/<task>/acceptance/ and OUT_DIR/manifest.json)
"""

import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from rescore_replay import TASKS

ROOT = Path(__file__).resolve().parent.parent
PY = "/opt/homebrew/bin/python3.11"
CMD = [PY, "-m", "unittest", "discover", "-s", "acceptance", "-t", "."]


def cut(src, kept):
    """Source with every test method not in kept removed (decorators included); a class left with no test is removed."""
    lines = src.splitlines(keepends=True)
    drop, add, tree = [], [], ast.parse(src)
    classes = [c for c in tree.body if isinstance(c, ast.ClassDef)]
    subs = {c.name: [s for s in classes if any(isinstance(b, ast.Name) and b.id == c.name for b in s.bases)]
            for c in classes}  # fmt: skip
    ok = lambda c, m: f"acceptance.test_acceptance.{c}.{m}" in kept  # noqa: E731
    for n in classes:
        tests = [m for m in n.body if isinstance(m, ast.FunctionDef) and m.name.startswith("test")]
        if subs[n.name]:  # a base class: its tests run in each subclass, so keep a test any subclass kept, and
            gone = [m for m in tests if not any(ok(s.name, m.name) for s in subs[n.name])]
            for s in subs[n.name]:  # switch it off (name = None, which unittest skips) in the subclasses that dropped it
                add += [(s.end_lineno, f"    {m.name} = None  # failed on the reference solution\n")
                        for m in tests if m not in gone and not ok(s.name, m.name)]  # fmt: skip
        else:
            gone = [m for m in tests if not ok(n.name, m.name)]
            if tests and len(gone) == len(tests):
                gone = [n]
        drop += [((m.decorator_list[0].lineno if m.decorator_list else m.lineno) - 1, m.end_lineno) for m in gone]
    edits = [(a, b, "") for a, b in drop] + [(at, at, text) for at, text in add]
    for a, b, text in sorted(edits, key=lambda e: (e[0], e[1]), reverse=True):
        lines[a:b] = [text] if text else []
    out = "".join(lines)
    compile(out, "test", "exec")
    return out


def run(task, accept, solution):
    with tempfile.TemporaryDirectory(prefix="td-") as tmp:
        ws = Path(tmp) / "work"
        shutil.copytree(TASKS / task / "repo", ws)
        if solution:
            shutil.copytree(TASKS / task / "solution", ws, dirs_exist_ok=True)
        shutil.copytree(accept, ws / "acceptance")
        p = subprocess.run(CMD, cwd=ws, capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)
    return p.returncode, p.stderr.strip().splitlines()[-3:]


def main(out):
    out = Path(out)
    vals = {v["set"]: v for v in json.load(open(ROOT / "runs" / "z4-validity.json"))}
    manifest = {}
    for task in sorted({s.split("/")[0] for s in vals}):
        acc = out / task / "acceptance"
        shutil.rmtree(acc, ignore_errors=True)
        acc.mkdir(parents=True)
        (acc / "__init__.py").write_text("")
        for k in (1, 2, 3):
            v = vals[f"{task}/opus-r{k}"]
            src = (ROOT / "runs" / "z4-writers" / task / f"opus-r{k}" / "test_acceptance.py").read_text()
            (acc / f"test_r{k}.py").write_text(cut(src, set(v["kept"])))
        files = sorted(acc.iterdir())
        ref, bare = run(task, acc, True), run(task, acc, False)
        manifest[task] = {"files": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files},
                          "kept": sum(len(vals[f"{task}/opus-r{k}"]["kept"]) for k in (1, 2, 3)),
                          "reference_rc": ref[0], "reference_tail": ref[1], "repo_rc": bare[0], "repo_tail": bare[1]}  # fmt: skip
        print(task, manifest[task]["kept"], "reference rc", ref[0], ref[1][-1:], "| repo rc", bare[0], bare[1][-1:])
        ran = int(ref[1][0].split()[1])  # "Ran N tests in ..."
        assert ref[0] == 0 and bare[0] != 0 and ran == manifest[task]["kept"], (task, ran)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
