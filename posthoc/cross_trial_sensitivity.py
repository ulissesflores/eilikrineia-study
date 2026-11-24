"""Post hoc: cross-trial-read sensitivity of the registered estimates of studies 1 and 2.

EXPLORATORY, POST HOC (2026-11-23). Not preregistered. Flagging happens after randomisation, so excluding flagged
trials is a sensitivity check, not an unbiased estimate of the effect in an uncontaminated run.

Inputs (read only):
- the scan list posthoc/cross-trial-reads.tsv (the author's scan of the original raw folders, one row per flagged
  read; columns: trial, file, line, kind, foreign path or trial id, up to five other trial folders and a "+N" count,
  study, other studies). This script does not rebuild it: the rule that found the `trial-id-*` rows is not shipped;
- the raw trial folders <RAW>/{pilot,study,study2} (default: raw/, the unpacked archive 10.5281/zenodo.24450523;
  record.json start times; agent.stdout to recover the full list of other writers of each shared temp path, which
  the list truncates after five names);
- the published package, i.e. the package root (score files and the analysers, imported
  and run unchanged: analyze_study.main, analyze_rescore.main, analyze_study2.main, analyze_study.mh_rd).

Classification of flagged trials (printed below with counts):
- contact: the transcript itself shows another trial's folder name (a `trial-id-*` row of the TSV). On inspection
  these are another trial's script read, overwritten or run from a shared temp folder (its `sys.path` names the other
  trial), not bare directory listings.
- plausible read: a `shared-tmp-read` row in which at least one OTHER trial that wrote the same temp path had started
  before the reading trial ended (record.json `started` + `seconds`).
- implausible only: every flagged read of the trial names only writers that started after the reader had ended, so the
  file read cannot have been another trial's.
Strict set = contact or plausible read. Broad set = every trial of the TSV (as first disclosed). A third set adds
to the broad set every trial NAMED as the other party of a `trial-id-*` row (its own temp file was touched).

Usage (from the package root): python posthoc/cross_trial_sensitivity.py            -> the analysis (stdout)
                               python posthoc/cross_trial_sensitivity.py --write-list posthoc/cross-trial-flagged.tsv
                               -> only the per-trial list of flagged trials, with the strict/broad classification.

Gate: with no trial excluded, every analyser output must equal the frozen package output for the lines used.
"""

import ast
import collections
import contextlib
import csv
import io
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path

sys.dont_write_bytecode = True  # never write .pyc into the sealed runner/ folder
HERE = Path(__file__).resolve().parent
PKG = HERE.parent  # the package root
RUNS = PKG / "runs"
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))  # <RAW>
TSV = HERE / "cross-trial-reads.tsv"
sys.path.insert(0, str(PKG / "runner"))
import analyze_rescore  # noqa: E402
import analyze_study  # noqa: E402
import analyze_study2  # noqa: E402
from analyze_study import mh_rd  # noqa: E402

# --- the author's scan rule for shared temp paths (xscan), to recover the full writer sets ---------------------------
ID_RE = re.compile(rb"trial-[A-Za-z0-9_]{8}")
TMP_RE = re.compile(r"(?<![\w.-])(/private/tmp|/tmp)/[^\s\"'\;|&)<>`$*?]+")
WRITE_CMD = re.compile(r"open\([^)]*['\"][wa]b?\+?['\"]|write_text|write_bytes|\.write\(|tee\b|touch\b|mkdir\b")
INPUT_KEYS = ("command", "file_path", "path", "pattern")


def own_id(path):
    with open(path, "rb") as f:
        for n, raw in enumerate(f):
            if b'"subtype":"init"' in raw:
                m = ID_RE.search(raw)
                return m.group(0).decode() if m else ""
            if n > 40:
                break
    return ""


def xscan(path):
    own = own_id(path)
    reads, writes = [], set()
    with open(path, "rb") as f:
        for ln, raw in enumerate(f, 1):
            if not (b'"type":"assistant"' in raw[:40] and own and b"/tmp/" in raw):
                continue
            try:
                o = json.loads(raw)
            except Exception:
                continue
            for it in o.get("message", {}).get("content") or []:
                if not (isinstance(it, dict) and it.get("type") == "tool_use"):
                    continue
                inp = it.get("input") or {}
                name = it.get("name")
                for k in INPUT_KEYS:
                    sv = inp.get(k)
                    if not isinstance(sv, str) or "/tmp/" not in sv:
                        continue
                    for m in TMP_RE.finditer(sv):
                        tok = m.group(0).rstrip(".,:")
                        if tok.startswith(("/private/tmp/claude-", "/tmp/claude-")):
                            continue
                        tok = tok.replace("/private/tmp/", "/tmp/", 1)
                        pre = sv[max(0, m.start() - 12):m.start()]
                        is_w = name in ("Write", "Edit", "NotebookEdit") or re.search(r">>?\s*$|tee\s+(-a\s+)?$", pre) \
                            or (k == "command" and WRITE_CMD.search(sv))
                        if is_w:
                            writes.add(tok)
                        else:
                            reads.append((ln, tok))
    return path, reads, sorted(writes)
# ------------------------------------------------------------------------------------------------------------------


def ts(s):
    return datetime.fromisoformat(s).timestamp()


def times():
    out = {}
    for study in ("pilot", "study", "study2"):
        for d in (RAW / study).iterdir():
            rec = d / "record.json"
            if rec.exists():
                r = json.loads(rec.read_text())
                if r.get("started"):
                    out[f"{study}/{d.name}"] = (ts(r["started"]), ts(r["started"]) + float(r.get("seconds") or 0))
    return out


def scan():
    paths = [str(p) for s in ("pilot", "study", "study2") for p in (RAW / s).glob("*/agent.stdout")]
    with Pool(8) as pool:
        res = pool.map(xscan, paths, chunksize=16)
    writers = collections.defaultdict(set)
    reads = {}
    for path, rd, wr in res:
        trial = os.path.relpath(os.path.dirname(path), RAW)
        reads[trial] = (rd, set(wr))
        for w in wr:
            writers[w].add(trial)
    return reads, writers


def run(fn, *args, argv=None):
    buf = io.StringIO()
    old = sys.argv
    if argv is not None:
        sys.argv = argv
    try:
        with contextlib.redirect_stdout(buf):
            fn(*args)
    finally:
        sys.argv = old
    return buf.getvalue()


def write_csv(src, drop, tmp, name):
    rows = list(csv.DictReader(open(src)))
    out = Path(tmp) / name
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(r for r in rows if r["trial"] not in drop)
    return str(out), rows


def mh_line(text, header, prefix):
    sec = text.split(header, 1)[1]
    return next(x for x in sec.splitlines() if x.strip().startswith(prefix)).strip()


def estimates(drop1, drop2, label):
    """Run the package analysers with the given study 1 and study 2 trials removed; return printable lines."""
    lines = [f"\n######## {label}"]
    with tempfile.TemporaryDirectory() as tmp:
        s1, _ = write_csv(RUNS / "study-scores.csv", drop1, tmp, "s1.csv")
        out1 = run(analyze_study.main, argv=["analyze_study.py", s1])
        lines.append("  study 1 registered (P-S false completion, 3 tasks): " +
                     mh_line(out1, "== false_completion", "MH P-S"))
        lines.append("    arms: " + " | ".join(x for x in mh_line(out1, "== false_completion", "per task").split("; ")))
        lines.append("    " + out1.splitlines()[0])
        rows1 = [r for r in csv.DictReader(open(s1))]
        t = lambda v: v == "True"  # noqa: E731
        kept1 = [r for r in rows1 if not (t(r["timed_out"]) or t(r["is_error"]) or int(r.get("hidden_access") or 0) > 0)]
        tpl = [r for r in kept1 if r["task"] == "text-template-engine"]
        a1 = sum(t(r["false_completion"]) for r in tpl if r["arm"] == "P")
        n1 = sum(r["arm"] == "P" for r in tpl)
        a0 = sum(t(r["false_completion"]) for r in tpl if r["arm"] == "S")
        n0 = sum(r["arm"] == "S" for r in tpl)
        rd, lo, hi, _, p = mh_rd([(a1, n1, a0, n0)])
        lines.append(f"  study 1 valid task only (text-template-engine, registered measure): P {a1}/{n1} S {a0}/{n0}; "
                     f"P-S {rd * 100:+.1f} (95% {lo * 100:+.1f} to {hi * 100:+.1f}), p {p:.2f}")
        outr = run(analyze_rescore.main, s1, str(RUNS / "study-rescore.csv"))
        lines.append("  study 1 recount (valid checks): " + mh_line(outr, "== primary estimate", "all trials:"))
        s2, rows2 = write_csv(RUNS / "study2-scores.csv", drop2, tmp, "s2.csv")
        stub = Path(tmp) / "raw2"
        stub.mkdir()
        rc = {r["trial"]: r["agent_rc"] for r in csv.DictReader(open(RUNS / "study2-agent-rc.csv"))}
        for trial, code in rc.items():
            (stub / trial).mkdir()
            (stub / trial / "record.json").write_text(json.dumps({"agent_rc": None if code == "" else int(code)}))
        saved = analyze_study2.OUTCOMES
        analyze_study2.OUTCOMES = saved + (("check_passed", "exploratory: pass rate"),)
        try:
            out2 = run(analyze_study2.main, str(stub), s2)
        finally:
            analyze_study2.OUTCOMES = saved
        head = "    " + out2.splitlines()[0] + "; " + "; ".join(x.strip() for x in out2.splitlines()[1:3])
        # runner/analyze_study2.py prints a dict built from a set, so its key order follows PYTHONHASHSEED: sort the keys
        head = re.sub(r"\{[^{}]*\}", lambda m: str(dict(sorted(ast.literal_eval(m.group()).items()))), head)
        lines.append(head)
        for col in ("false_completion", "false_non_completion", "check_passed"):
            sec = out2.split(f"== {col} ", 1)[1].splitlines()
            arms = [x for x in sec[1:3]]
            lines.append(f"  study 2 {col}: " + mh_line(out2, f"== {col} ", "MH S-control") + "  [" + "; ".join(arms) + "]")
    return lines, out1, outr, out2


def write_list(out, rows, contact, plausible, flagged, counterparts):
    """Write the per-trial list of flagged trials: study, arm, task, the three sets and the evidence category."""
    kinds = collections.defaultdict(set)
    for r in rows:
        kinds[r["trial"]].add(r["kind"])
    named = {t for t in counterparts if re.match(r"(pilot|study2?)/", t)} - flagged
    with open(out, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["trial", "study", "arm", "task", "strict", "broad", "broad_plus_counterparts", "evidence_category",
                    "row_kinds"])
        for t in sorted(flagged | named):
            study, name = t.split("/")
            _, arm, task = name.split("-", 2)
            cat = ("contact" if t in contact else "plausible-read" if t in plausible
                   else "implausible-only" if t in flagged else "named-counterpart")
            w.writerow([t, study, arm, task.rsplit("-r", 1)[0], int(t in contact | plausible), int(t in flagged), 1,
                        cat, ";".join(sorted(kinds.get(t, ())))])


def main():
    rows = list(csv.DictReader(open(TSV), delimiter="\t"))
    flagged = sorted({r["trial"] for r in rows})
    by_study = collections.Counter(t.split("/")[0] for t in flagged)
    arm = lambda t: t.split("/")[1].split("-")[1]  # noqa: E731
    by_arm = collections.Counter((t.split("/")[0], arm(t)) for t in flagged)
    print(f"TSV rows {len(rows)}; flagged trials {len(flagged)}; by study {dict(sorted(by_study.items()))}; by study and arm {dict(sorted(by_arm.items()))}")
    kinds = collections.defaultdict(set)
    for r in rows:
        kinds[r["kind"]].add(r["trial"])
    print("trials per row kind: " + ", ".join(f"{k} {len(v)}" for k, v in sorted(kinds.items())))

    tm = times()
    reads, writers = scan()
    # reproduction check of the shared-tmp-read rows
    mine = set()
    for trial, (rd, wr) in reads.items():
        for ln, tok in rd:
            if tok in wr:
                continue
            if writers.get(tok, set()) - {trial}:
                mine.add((trial, ln, tok))
    theirs = {(r["trial"], int(r["line"]), r["foreign_trial_id_or_path"]) for r in rows if r["kind"] == "shared-tmp-read"}
    print(f"reproduced shared-tmp-read rows: {len(mine)}; TSV {len(theirs)}; in both {len(mine & theirs)}; "
          f"only TSV {len(theirs - mine)}; only reproduced {len(mine - theirs)}")

    contact = {r["trial"] for r in rows if r["kind"].startswith("trial-id-")}
    counterparts = set()
    for r in rows:
        if r["kind"].startswith("trial-id-"):
            counterparts |= set(x for x in r["foreign_trial_folder(s)"].split(";") if x)
    plausible, implausible_rows, plausible_rows = set(), 0, 0
    for r in rows:
        if r["kind"] != "shared-tmp-read":
            continue
        t, tok = r["trial"], r["foreign_trial_id_or_path"]
        end = tm.get(t, (None, float("inf")))[1]
        others = writers.get(tok, set()) - {t}
        early = [w for w in others if tm.get(w, (float("-inf"),))[0] < end]
        if early:
            plausible.add(t)
            plausible_rows += 1
        else:
            implausible_rows += 1
    strict = contact | plausible
    implausible_only = set(flagged) - strict
    print(f"shared-tmp-read rows with an earlier other writer {plausible_rows}, with only later writers {implausible_rows}")
    print(f"contact trials {len(contact)}; plausible-read trials {len(plausible)}; strict (union) {len(strict)}; "
          f"implausible only {len(implausible_only)}; named counterparts not themselves flagged "
          f"{len(counterparts - set(flagged))}")
    for name, s in (("strict", strict), ("broad", set(flagged)), ("broad+counterparts", set(flagged) | counterparts)):
        c = collections.Counter((t.split("/")[0], arm(t)) for t in s)
        print(f"  {name}: {len(s)} trials; by study and arm {dict(sorted(c.items()))}")
        task = collections.Counter((t.split("/")[0], arm(t), t.split("/")[1].split("-", 2)[2].rsplit("-r", 1)[0])
                                   for t in s if not t.startswith("pilot"))
        print(f"    by study, arm and task: {dict(sorted(task.items()))}")

    def ids(s, study):
        return {t.split("/", 1)[1] for t in s if t.startswith(study + "/")}

    if len(sys.argv) > 2 and sys.argv[1] == "--write-list":
        write_list(Path(sys.argv[2]), rows, contact, plausible, set(flagged), counterparts)
        return
    base, o1, orr, o2 = estimates(set(), set(), "NO EXCLUSION (gate: must equal the frozen package outputs)")
    for line in base:
        print(line)
    frozen1 = (RUNS / "study-analysis.txt").read_text()
    frozen2 = (RUNS / "study2-analysis.txt").read_text()
    frozenr = (RUNS / "study-rescore-analysis.txt").read_text()
    gate = [mh_line(o1, "== false_completion", "MH P-S") == mh_line(frozen1, "== false_completion", "MH P-S"),
            mh_line(orr, "== primary estimate", "all trials:") == mh_line(frozenr, "== primary estimate", "all trials:"),
            mh_line(o2, "== false_completion ", "MH S-control") == mh_line(frozen2, "== false_completion ", "MH S-control"),
            mh_line(o2, "== false_non_completion ", "MH S-control") ==
            mh_line(frozen2, "== false_non_completion ", "MH S-control")]
    print(f"GATE frozen lines reproduced: {gate} -> {'OK' if all(gate) else 'FAILED'}")
    if not all(gate):
        sys.exit(1)
    for name, s in (("STRICT", strict), ("BROAD", set(flagged)), ("BROAD + NAMED COUNTERPARTS", set(flagged) | counterparts)):
        d1, d2 = ids(s, "study"), ids(s, "study2")
        lines, *_ = estimates(d1, d2, f"EXCLUDING {name}: {len(d1)} study 1 and {len(d2)} study 2 trials removed "
                                      "(before the registered exclusions)")
        for line in lines:
            print(line)


if __name__ == "__main__":
    main()
