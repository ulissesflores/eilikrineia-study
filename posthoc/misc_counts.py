"""Post hoc: counts asked for by reviewers, from the package files (and the raw study 3 records for turns).
EXPLORATORY / DESCRIPTIVE unless stated; none is preregistered. Statistics use the package's own functions.

Sections: pilot per arm; study 2 accounting of the 200 failures; the 9.1-point ceiling; precision of "complete"
against the hidden check by task (study 2) with a task-stratified difference; study 1 recount, the 141 kept trials not
rebuilt exactly; study 3 STATUS line by arm and against the labeller; equivalence reachability of the three tests the
preregistration called "not reachable"; acceptance-test edits by task with durations and turns; the benchmark's
held-out confusion table reduced to complete against the rest.
"""

import csv
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True  # never write .pyc into the sealed runner/ folder
PKG = Path(__file__).resolve().parent.parent  # the package root
RAW3 = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw")) / "study3"  # <RAW>/study3, only for turn counts
sys.path.insert(0, str(PKG / "runner"))
from analyze import Z, newcombe, wilson  # noqa: E402
from analyze_study import mh_rd  # noqa: E402
from analyze_study3 import ALPHA, zq  # noqa: E402
from sensitivity_study import estimate  # noqa: E402

RUNS = PKG / "runs"
TASKS = ("feature-toml-config", "feature-uri-resolve", "text-template-engine")
t = lambda v: v == "True"  # noqa: E731


def rows(name):
    return list(csv.DictReader(open(RUNS / name)))


def pilot():
    print("== Pilot, per arm (frozen runs/pilot-analysis.txt; exclusions from RESULTS.md and pilot-scores.csv)")
    txt = (RUNS / "pilot-analysis.txt").read_text()
    for arm in "HSP":
        m = re.search(rf"^{arm}: n=(\d+) M1=(\d+) .*? M2=(\d+) .*?check_pass=([\d.]+)%", txt, re.M)
        print(f"  {arm}: kept {m.group(1)}, unbacked claims {m.group(2)}, false completions {m.group(3)}, pass {m.group(4)}%")
    ex = re.search(r"excluded 4: \[(.*?)\]", txt).group(1).replace("'", "").split(", ")
    sc = {r["trial"]: r for r in rows("pilot-scores.csv")}
    for e in ex:
        print(f"  excluded {e}: arm {e.split('-')[1]}, timed_out {sc[e]['timed_out']}")


def study2_accounting():
    print("\n== Study 2: the 200 hidden-check failures of Table 4 and the Z4 rebuilds (runs/z4-trials.jsonl)")
    z = [json.loads(x) for x in open(RUNS / "z4-trials.jsonl")]
    fa = [r for r in z if r["faithful"]]
    nf = [r for r in z if not r["faithful"]]
    print(f"  rebuilt trials (kept, with a final state) {len(z)}; faithful {len(fa)}; failed among faithful "
          f"{sum(not r['recorded_check'] for r in fa)}; failed among all rebuilt {sum(not r['recorded_check'] for r in z)}")
    print(f"  not faithful {len(nf)}: {dict(Counter((r['arm'], 'passed' if r['recorded_check'] else 'failed') for r in nf))}")
    rc = {r["trial"]: r["agent_rc"] for r in csv.DictReader(open(RUNS / "study2-agent-rc.csv"))}
    sc = {r["trial"]: r for r in rows("study2-scores.csv")}
    e126 = [k for k, v in rc.items() if v == "126"]
    print(f"  exit 126 trials {e126}: arm {[sc[k]['arm'] for k in e126]}, check_passed {[sc[k]['check_passed'] for k in e126]}")
    opus = lambda r: any(v for k, v in r["flags"].items() if "/opus-" in k)  # noqa: E731
    f = [r for r in fa if not r["recorded_check"]]
    print(f"  Opus-written tests flag {sum(opus(r) for r in f)} of {len(f)} failures among faithful rebuilds "
          f"({sum(opus(r) for r in f) / len(fa) * 100:.1f} points of the {len(fa)} faithful trials, pooled)")
    print("  runs/z4-union.txt prints 'pass rate +9.1 points' for these tests; the script that wrote that file is not in"
          " the package, and no single formula tried here reproduces all six ceiling figures in that file.")


def ppv():
    print("\n== Study 2: share of 'complete' labels whose hidden check passed, by task (kept trials; descriptive)")
    r2 = [r for r in rows("study2-scores.csv") if not t(r["timed_out"]) and not t(r["is_error"])]
    # frozen per-task kept denominators exclude also never-started trials; those neither pass nor say complete,
    # so numerators among 'complete' labels are unaffected (as scripts/make_results.py notes)
    strata = []
    for task in TASKS:
        cells = []
        for arm in ("S", "control"):
            c = [r for r in r2 if r["arm"] == arm and r["task"] == task and r["claim"] == "complete"]
            k = sum(t(r["check_passed"]) for r in c)
            cells += [k, len(c)]
            lo, hi = wilson(k, len(c))
            print(f"  {task} {arm}: {k}/{len(c)} = {k / len(c) * 100:.1f}% (Wilson 95% {lo * 100:.1f} to {hi * 100:.1f})")
        nlo, nhi = newcombe(*cells)
        print(f"    S - control {(cells[0] / cells[1] - cells[2] / cells[3]) * 100:+.1f} (Newcombe 95% {nlo * 100:+.1f} to {nhi * 100:+.1f})")
        strata.append(tuple(cells))
    rd, lo, hi, _, p = mh_rd(strata)
    print(f"  task-stratified (package mh_rd) S - control: {rd * 100:+.1f} (95% {lo * 100:+.1f} to {hi * 100:+.1f}), p {p:.3f}")
    tot = [sum(s[i] for s in strata) for i in range(4)]
    nlo, nhi = newcombe(*tot)
    print(f"  pooled: S {tot[0]}/{tot[1]} control {tot[2]}/{tot[3]}: {(tot[0] / tot[1] - tot[2] / tot[3]) * 100:+.1f} "
          f"(Newcombe 95% {nlo * 100:+.1f} to {nhi * 100:+.1f})")


def recount_141():
    print("\n== Study 1 recount: kept trials whose rebuild did not reproduce the saved state (runs/study-rescore.csv)")
    sc = rows("study-scores.csv")
    re_ = {r["trial"]: r for r in rows("study-rescore.csv")}
    kept = [r for r in sc if not (t(r["timed_out"]) or t(r["is_error"]) or int(r.get("hidden_access") or 0) > 0)]
    fid = lambda x: t(x["diff_match"]) and t(x["check_match"]) and t(x["fail_set_match"])  # noqa: E731
    bad = [r for r in kept if not fid(re_[r["trial"]])]
    print(f"  kept {len(kept)}; not faithful {len(bad)}: by arm {dict(Counter(r['arm'] for r in bad))}; by arm and task "
          f"{dict(sorted(Counter((r['arm'], r['task']) for r in bad).items()))}")
    print(f"  kind: diff differs {sum(not t(re_[r['trial']]['diff_match']) for r in bad)}, "
          f"only the failing set differs {sum(t(re_[r['trial']]['diff_match']) and not t(re_[r['trial']]['fail_set_match']) for r in bad)}, "
          f"by arm {dict(Counter((r['arm'], 'diff' if not t(re_[r['trial']]['diff_match']) else 'failset') for r in bad))}")
    out = [r | {"valid_fc": str(re_[r["trial"]]["claim_label"] == "complete" and not t(re_[r["trial"]]["valid_check"]))} for r in kept]
    print("  as published: " + estimate(out, "valid_fc"))
    for name, p_val, s_val in (("worst case against P (every unfaithful P trial a false completion, no S one)", "True", "False"),
                               ("worst case against S (the reverse)", "False", "True")):
        mod = [r | {"valid_fc": (p_val if r["arm"] == "P" else s_val)} if not fid(re_[r["trial"]]) else r for r in out]
        print(f"  {name}: " + estimate(mod, "valid_fc"))
    print("  faithful only (as published): " + estimate([r for r in out if fid(re_[r["trial"]])], "valid_fc"))


def kept3():
    rs = [r for r in rows("study3-scores.csv") if r["arm"] in ("S", "I", "K", "TD")]
    out = []
    for r in rs:  # exclusions as runner/analyze_study3.py main()
        if t(r["timed_out"]) or t(r["is_error"]) or not r["init_model"] or int(r.get("hidden_access_path") or 0) > 0 \
                or t(r["check_infra_error"]):
            continue
        out.append(r)
    print(f"  study 3 kept per arm {dict(Counter(r['arm'] for r in out))} (frozen: S 740, I 740, K 741, TD 737)")
    return out


def status():
    print("\n== Study 3 STATUS line by arm (kept trials)")
    k3 = kept3()
    for arm in ("S", "I", "K", "TD"):
        a = [r for r in k3 if r["arm"] == arm]
        passed = [r for r in a if t(r["check_passed"])]
        failed = [r for r in a if not t(r["check_passed"])]
        print(f"  {arm}: failed {len(failed)}, STATUS COMPLETE among failed {sum(r['status'] == 'COMPLETE' for r in failed)}; "
              f"passed {len(passed)}, STATUS not COMPLETE among passed {sum(r['status'] != 'COMPLETE' for r in passed)} "
              f"({dict(Counter(r['status'] for r in passed if r['status'] != 'COMPLETE'))})")
        cross = Counter((r["status"] or "missing", r["claim"]) for r in a)
        print(f"     STATUS x labeller: {dict(sorted(cross.items()))}")


def reachability():
    print("\n== Study 3: could 'equivalent' be reached? (1 - 2 alpha) half-width at the observed variance (package mh_rd, zq)")
    s3 = (RUNS / "study3-analysis.txt").read_text().split("######## SENSITIVITY", 1)[0]
    for arm, col in (("I", "false_non_completion"), ("K", "false_non_completion"), ("TD", "passed"), ("K", "false_completion"),
                     ("I", "false_completion")):
        sec = s3.split(f"\n== {col}\n", 1)[1].split(f"  {arm}-S ", 1)[1]
        strata = [tuple(int(x) for x in re.search(rf"{task}: {arm} (\d+)/(\d+), S (\d+)/(\d+)", sec).groups()) for task in TASKS]
        rd, lo, hi, _, _ = mh_rd(strata)
        se = (hi - rd) / Z
        hw = zq(2 * ALPHA) * se
        print(f"  {arm} - S {col}: estimate {rd * 100:+.1f}, (1 - 2 alpha) half-width {hw * 100:.2f} points -> 'equivalent' needs "
              f"|estimate| < {max(0, 5 - hw * 100):.2f} points" + ("" if hw * 100 < 5 else " (impossible: half-width exceeds the margin)"))


def td_edits():
    print("\n== Study 3 TD: acceptance tests edited, by task; seconds and turns by task and arm (kept trials)")
    k3 = kept3()
    td = [r for r in k3 if r["arm"] == "TD"]
    print(f"  edited suites {sum(int(r['td_edited'] or 0) > 0 for r in td)}: by task "
          f"{dict(Counter(r['task'] for r in td if int(r['td_edited'] or 0) > 0))}; edited and hidden check failed "
          f"{sum(int(r['td_edited'] or 0) > 0 and not t(r['check_passed']) for r in td)}")
    for task in TASKS:
        for arm in ("TD", "S"):
            a = [r for r in k3 if r["arm"] == arm and r["task"] == task]
            turns = []
            for r in a:
                rec = RAW3 / r["trial"] / "record.json"
                if rec.exists():
                    nt = json.loads(rec.read_text()).get("num_turns")
                    if nt is not None:
                        turns.append(nt)
            print(f"  {task} {arm}: n {len(a)}, median seconds {statistics.median(float(r['seconds']) for r in a):.0f}, "
                  f"median turns {statistics.median(turns) if turns else 'n/a'} ({len(turns)} records), timeouts in arm "
                  f"{sum(t(r['timed_out']) for r in rows('study3-scores.csv') if r['arm'] == arm and r['task'] == task)}")


def benchmark():
    print("\n== Benchmark held-out confusion (overclaim/docs/claims.md, real-holdout, rows gold, columns predicted)")
    txt = (PKG / "overclaim/docs/claims.md").read_text().split("Real-holdout confusion", 1)[1].split("Real-tune", 1)[0]
    m = {}
    for line in txt.splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0] in ("complete", "partial", "incomplete", "none") and len(cells) == 5:
            m[cells[0]] = [int(x) for x in cells[1:]]
    n = sum(sum(v) for v in m.values())
    four = sum(m[g][i] for i, g in enumerate(("complete", "partial", "incomplete", "none")) if g in m)
    two = m["complete"][0] + sum(sum(v[1:]) for g, v in m.items() if g != "complete")
    print(f"  n {n}; four-label agreement {four}/{n} = {four / n:.3f}; complete against the rest {two}/{n} = {two / n * 100:.1f}%")


if __name__ == "__main__":
    pilot()
    study2_accounting()
    ppv()
    recount_141()
    status()
    reachability()
    td_edits()
    benchmark()
