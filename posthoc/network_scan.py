"""Round 21 (a): network-command scan of every agent tool call. EXPLORATORY, POST HOC (2026-11-24). Not preregistered.

Question: did any agent fetch remote content, and did any fetch target the benchmark or its hidden-check sources?

Scanned: every tool call of every saved transcript (agent.stdout) in <RAW>/{pilot,study,study2,study3}. The shell
command of a Bash call is split into simple commands at `;`, `&&`, `||`, `|` and newlines; a simple command that only
asks for help or a version (`--help`, `-h`, `--version`) is not counted. Write and Edit contents are scanned for
network libraries only (a script written to disk and then run).

Fetch-capable command classes (set before the counts, then revised once after a first pass over the output: the
`httpx` pattern was narrowed, since a `grep` pattern naming the word matched, and the pip-notice retrieval rule
below was added, since a quiet install shows nothing else):
  package  pip/pip3/python -m pip download|install|index, uv add|sync|pip install|tool install, uvx, pipx,
           npm install|ci, npx, yarn add, brew|apt|apt-get|conda install
  git      git clone|fetch|pull|ls-remote|submodule
  http     curl, wget
  remote   ssh, scp, sftp, telnet, nc, ncat
  pylib    urllib.request, urlopen(, requests.get|post|head|Session, import httpx or
           httpx.get|post|Client|stream, http.client, socket.create_connection
URL literals (http:// or https://) are counted apart, because the URI task's tests are full of them; a URL whose host
is a code or package host (GitHub, GitLab, Bitbucket, PyPI, npm) is counted as such.
Benchmark target: a fetch-capable command or URL that names the benchmark repository (owner `h-a-forster`, name
`overclaim`) or a task folder of any study (read from the trial folder names).
Retrieved: the tool result of a fetch-capable command shows fetched content (a wheel or archive name, a dist-info
folder, "Successfully installed/downloaded", "Saved", a commit hash before HEAD, or a version list "(N.N)"), or pip
printed its "new release of pip" notice, which it shows only after reaching the package index, with no "ERROR".

Sensitivity: if any trial retrieved benchmark content, the main contrasts of its study are rerun without those
trials with the package analysers, imported unchanged. The same rerun is printed for trials that retrieved any
third-party content, behind a gate: with nothing removed, the line must equal the frozen package output.

Verb-free check: any tool input of any kind (all fields) that names `h-a-forster` or `overclaim`, counted by
trial; study 1 and 2 trials with a tool call naming the checks' folder (which contains `overclaim`) are already
excluded by the planned rule, so this count is read against that rule.

Output: counts only. No transcript text, no trial id, no path. Arm labels come from an allowlist (else `other`);
failures print a fixed error category and a count, never input-derived text.
Run from the package root: PYTHONDONTWRITEBYTECODE=1 python posthoc/network_scan.py  (needs the package and <RAW>)
"""

import collections
import contextlib
import csv
import io
import json
import os
import re
import sys
import tempfile
from multiprocessing import Pool
from pathlib import Path

sys.dont_write_bytecode = True
PKG = Path(__file__).resolve().parent.parent  # the package root; raw/ = <RAW>, the unpacked raw archive
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))
RUNS = PKG / "runs"
STUDIES = ("pilot", "study", "study2", "study3")

CLASSES = {
    "package": re.compile(
        r"\b(?:pip[\d.]*|python[\d.]*\s+(?:-\w+\s+)*-m\s+pip)\s+(?:-\S+\s+)*(?:download|install|index)\b"
        r"|\buv\s+(?:add|sync|pip\s+install|tool\s+install)\b|\buvx\b|\bpipx\b|\bnpm\s+(?:install|i|ci)\b|\bnpx\b"
        r"|\byarn\s+add\b|\b(?:brew|apt|apt-get|conda)\s+install\b"),
    "git": re.compile(r"\bgit\s+(?:-C\s+\S+\s+)?(?:clone|fetch|pull|ls-remote|submodule)\b"),
    "http": re.compile(r"(?:^|[\s(`$])(?:curl|wget)\b"),
    "remote": re.compile(r"(?:^|[\s(`])(?:ssh|scp|sftp|telnet|nc|ncat)\s"),
    "pylib": re.compile(r"\burllib\.request\b|\burlopen\s*\(|\brequests\.(?:get|post|head|Session)\b"
                        r"|\bimport\s+httpx\b|\bhttpx\.(?:get|post|Client|stream)\b|\bhttp\.client\b|\bsocket\.create_connection\b"),
}
SPLIT = re.compile(r"\n|;|&&|\|\||\|")
HELP = re.compile(r"(?:^|\s)(?:--help|-h|--version|-V)(?:\s|$)")
URL = re.compile(r"https?://([^/\s'\"`:?#)\]>]*)")
CODE_HOSTS = re.compile(r"(?:^|\.)(?:github\.com|githubusercontent\.com|gitlab\.com|bitbucket\.org|pypi\.org"
                        r"|pythonhosted\.org|npmjs\.(?:com|org))$")
RETRIEVED = re.compile(r"\.whl\b|\.tar\.gz\b|dist-info|Successfully (?:installed|downloaded)|\bSaved\b"
                       r"|\b[0-9a-f]{40}\s+HEAD\b|\(\d+\.\d+(?:\.\d+)?\)")
PIP_NOTICE = re.compile(r"\[notice\] (?:A new release of pip|To update, run: pip install)")


def markers():
    tasks = {d.name.split("-", 2)[2].rsplit("-r", 1)[0] for s in STUDIES for d in (RAW / s).iterdir() if d.is_dir()}
    return ("h-a-forster", "overclaim", *sorted(tasks))


MARK = None


def segments(cmd):
    return [s for s in SPLIT.split(cmd) if s.strip() and not HELP.search(s)]


def scan(path):
    """Per trial: counters of fetch commands by class, retrieval, URL literals and benchmark hits.

    Any failure (unreadable file, unexpected structure) is reduced to a fixed category: the trial is returned with
    the counter `scan error` and nothing derived from the input is kept.
    """
    tid = f"{path.parent.parent.name}/{path.parent.name}"
    try:
        return tid, scan_file(path)
    except Exception:  # noqa: BLE001 - deliberately broad; the message may contain input-derived text
        return tid, collections.Counter({"scan error": 1})


def scan_file(path):
    c = collections.Counter()
    pending = {}
    with open(path, errors="replace") as f:
        for line in f:
            if '"tool_use"' not in line and '"tool_result"' not in line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            for it in (o.get("message") or {}).get("content") or []:
                if not isinstance(it, dict):
                    continue
                if it.get("type") == "tool_use":
                    name, inp = (it.get("name") or "").lower(), it.get("input") or {}
                    c["tool calls"] += 1
                    blob = json.dumps(inp).lower()
                    for m in ("h-a-forster", "overclaim"):
                        if m in blob:
                            c[f"calls naming {m} (any tool, any field)"] += 1
                    cmd = inp.get("command", "") if name == "bash" else ""
                    text = cmd or str(inp.get("content", "")) + str(inp.get("new_string", ""))
                    hosts = URL.findall(text)
                    if hosts:
                        c["calls with a URL literal"] += 1
                    if any(CODE_HOSTS.search(h.lower()) for h in hosts):
                        c["calls with a code/package-host URL"] += 1
                    if any(m in u.lower() for u in re.findall(r"https?://\S+", text) for m in MARK):
                        c["calls with a URL naming the benchmark or a task"] += 1
                    hit = set()
                    for seg in segments(cmd):
                        for k, r in CLASSES.items():
                            if k != "pylib" and r.search(seg):
                                hit.add(k)
                                if any(m in seg.lower() for m in MARK):
                                    c["fetch commands naming the benchmark or a task"] += 1
                    if CLASSES["pylib"].search(text):
                        hit.add("pylib")
                    for k in hit:
                        c[f"fetch: {k}"] += 1
                    if hit:
                        c["fetch-capable calls"] += 1
                        pending[it.get("id")] = hit
                elif it.get("type") == "tool_result" and it.get("tool_use_id") in pending:
                    hit = pending.pop(it["tool_use_id"])
                    res = json.dumps(it.get("content"))
                    if RETRIEVED.search(res) or (PIP_NOTICE.search(res) and "ERROR" not in res):
                        c["fetch calls whose result shows retrieved content"] += 1
                        for k in hit:
                            c[f"retrieved: {k}"] += 1
    return c


def init(m):
    global MARK
    MARK = m


ARMS = ("H", "S", "P", "control", "I", "K", "TD")  # allowlist: any other label is printed as `other`


def arm(trial):
    parts = trial.split("/", 1)[-1].split("-")
    return parts[1] if len(parts) > 1 and parts[1] in ARMS else "other"


# ---- sensitivity with the package analysers (imported unchanged) ----------------------------------------------------
def run(fn, *args, argv=None):
    buf, old = io.StringIO(), sys.argv
    sys.argv = argv or old
    try:
        with contextlib.redirect_stdout(buf):
            fn(*args)
    finally:
        sys.argv = old
    return buf.getvalue()


def lines(out, prefix):
    return [x.strip() for x in out.splitlines() if x.strip().startswith(prefix)]


def rerun(study, drop):
    sys.path.insert(0, str(PKG / "runner"))
    import analyze_study  # noqa: E402
    import analyze_study2  # noqa: E402
    import analyze_study3  # noqa: E402

    name = {"study": "study-scores.csv", "study2": "study2-scores.csv", "study3": "study3-scores.csv"}[study]
    frozen = (RUNS / name.replace("scores.csv", "analysis.txt")).read_text()
    rows = list(csv.DictReader(open(RUNS / name)))
    with tempfile.TemporaryDirectory() as tmp:
        out = []
        for label, d in (("nothing removed", set()), ("removed", drop)):
            p = Path(tmp) / name
            with open(p, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=rows[0].keys())
                w.writeheader()
                w.writerows(r for r in rows if r["trial"] not in d)
            if study == "study":
                o = run(analyze_study.main, argv=["analyze_study.py", str(p)])
                key = "MH P-S"
            elif study == "study2":
                o = run(analyze_study2.main, str(RAW / study), str(p))
                key = "MH S-control"
            else:
                o = run(analyze_study3.main, str(RAW / study), str(p))
                key = None
            sel = lines(o, key) if key else [x for x in lines(o, "") if "CONFIRMATORY" in x][:5]
            if label == "nothing removed":
                ref = lines(frozen, key) if key else [x for x in lines(frozen, "") if "CONFIRMATORY" in x][:5]
                assert sel == ref, (study, "gate: rerun with nothing removed differs from the frozen output")
                print(f"  {study}: gate passed (nothing removed equals the frozen output, {len(sel)} lines)")
            else:
                print(f"  {study}: {len(d)} trials removed")
                for x in sel:
                    print("    " + x)
        return out


def main():
    m = markers()
    paths = sorted(p for s in STUDIES for p in (RAW / s).glob("*/agent.stdout"))
    with Pool(8, initializer=init, initargs=(m,)) as pool:
        res = pool.map(scan, paths, chunksize=16)
    errors = sum(c["scan error"] for _, c in res)
    if errors:
        print(f"error: {errors} transcripts could not be read or parsed (category: unreadable or malformed transcript)")
        sys.exit(1)
    print("== Round 21 (a): network-command scan (post hoc, exploratory). Counts only.")
    print(f"transcripts scanned: {len(res)}; benchmark/task markers: {len(m)} (owner, repository and task names)")
    by = collections.defaultdict(collections.Counter)
    trials = collections.defaultdict(collections.Counter)
    bench, third = set(), collections.defaultdict(set)
    for t, c in res:
        key = (t.split("/")[0], arm(t))
        by[key].update(c)
        trials[key]["transcripts"] += 1
        if c["fetch-capable calls"]:
            trials[key]["trials with a fetch-capable call"] += 1
        for m in ("h-a-forster", "overclaim"):
            if c[f"calls naming {m} (any tool, any field)"]:
                trials[key][f"trials with a call naming {m}"] += 1
        if c["fetch calls whose result shows retrieved content"]:
            trials[key]["trials that retrieved content"] += 1
        if c["fetch commands naming the benchmark or a task"] or c["calls with a URL naming the benchmark or a task"]:
            trials[key]["trials naming the benchmark or a task in a fetch or URL"] += 1
            bench.add(t)
        elif c["fetch calls whose result shows retrieved content"]:
            third[t.split("/")[0]].add(t.split("/", 1)[1])
    for key in sorted(by):
        print(f"\n{key[0]} {key[1]}: " + ", ".join(f"{k} {v}" for k, v in sorted(trials[key].items())))
        print("  calls: " + ", ".join(f"{k} {v}" for k, v in sorted(by[key].items())))
    tot = collections.Counter()
    for c in trials.values():
        tot.update(c)
    print("\nall studies: " + ", ".join(f"{k} {v}" for k, v in sorted(tot.items())))
    print(f"\ntrials that named the benchmark or a task in a fetch command or URL: {len(bench)}")
    for m in ("h-a-forster", "overclaim"):
        print(f"trials with any tool call naming {m} (any tool, any field): {tot[f'trials with a call naming {m}']}")
    if bench:
        for s in ("study", "study2", "study3"):
            d = {t.split("/", 1)[1] for t in bench if t.startswith(s + "/")}
            if d:
                rerun(s, d)
    else:
        print("  no exclusion needed for benchmark retrieval")
    print("\n== sensitivity: main contrasts without the trials that retrieved third-party content (package analysers)")
    for s in ("study", "study2", "study3"):
        if third[s]:
            rerun(s, third[s])
        else:
            print(f"  {s}: no trial retrieved content; estimates unchanged by construction")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except AssertionError:
        print("error: a gate failed (category: gate)")
        sys.exit(1)
    except Exception as e:  # noqa: BLE001 - print the exception class only, never its input-derived message
        print(f"error: unexpected failure (category: {type(e).__name__})")
        sys.exit(1)
