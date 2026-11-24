"""Round 14: post hoc checks asked for by the round-13 reviews. EXPLORATORY, POST HOC (2026-11-24). Not preregistered.

A. Study 2, signal detection: hit rate H = P(labelled complete | hidden check passed), false-alarm rate
   F = P(labelled complete | failed), d' = z(H) - z(F), criterion c = -(z(H) + z(F)) / 2 (Macmillan & Creelman,
   2004, equal-variance Gaussian model), by task and arm, kept trials; labeller labels, not human ones.
B. Audits: outcome-specific signed disagreement. For each message D = labeller says complete - rater says complete
   (-1, 0, +1). Within one hidden-check result, mean_S(D) - mean_control(D) is the labeller's arm contrast minus the
   rater's (share "complete"); Wald 95% interval with sample variances. Study 2: author and second rater (all 80
   answers). Study 3: K - S and I - S against Fable and Grok.
C. Study 1: kept trials and passes on each of the three tasks (registered scoring).
D. Study 3: the parsed status fields (status, conforming) across all kept arms, the trials that failed the hidden
   check and did not write COMPLETE; claim records
   per kept trial by arm (S, K, TD) and records with evidence.
E. Study 2: session seconds by task and arm (medians; difference of medians with a 2,000-resample percentile
   bootstrap, seed 1), kept trials.

Gates (asserts): kept counts 1,992 (study 1), 505/493 (study 2), 2,958 (study 3); one pooled Table 4 numerator (136:
S trials that passed and were labelled complete); the Table 10 complete-label marginal counts (not the discordant pairs).
Run from the package root: PYTHONDONTWRITEBYTECODE=1 python posthoc/round14_checks.py  (needs the package and <RAW>)
"""

import collections
import csv
import json
import os
import random
import statistics
import sys
from pathlib import Path

sys.dont_write_bytecode = True
PKG = Path(__file__).resolve().parent.parent  # the package root; raw/ = <RAW>, the unpacked raw archive
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))
RUNS = PKG / "runs"
T = lambda v: v == "True"  # noqa: E731
Z = statistics.NormalDist().inv_cdf
TASKS = ("feature-toml-config", "feature-uri-resolve", "text-template-engine")


def rows(name):
    return list(csv.DictReader(open(RUNS / name)))


def rec(study, trial):
    p = RAW / study / trial / "record.json"
    return json.loads(p.read_text()) if p.exists() else {}


def kept2():
    rs = [r for r in rows("study2-scores.csv") if r["arm"] in ("S", "control")]
    ex = lambda r: (T(r["timed_out"]) or T(r["is_error"]) or int(r["hidden_access"] or 0) > 0  # noqa: E731
                    or str(rec("study2", r["trial"]).get("agent_rc")) == "127")
    k = [r for r in rs if not ex(r)]
    n = collections.Counter(r["arm"] for r in k)
    assert (n["S"], n["control"]) == (505, 493), n
    return k


def part_a(k):
    print("== A. Study 2, signal detection by task and arm (labeller labels, kept trials)")
    for t in TASKS:
        cs = {}
        for arm in ("S", "control"):
            g = [r for r in k if r["task"] == t and r["arm"] == arm]
            p = [r for r in g if T(r["check_passed"])]
            f = [r for r in g if not T(r["check_passed"])]
            hp, ff = sum(r["claim"] == "complete" for r in p), sum(r["claim"] == "complete" for r in f)
            h, fa = hp / len(p), ff / len(f)
            d, c = Z(h) - Z(fa), -(Z(h) + Z(fa)) / 2
            cs[arm] = c
            print(f"  {t:22s} {arm:7s} H {hp}/{len(p)} = {h:.3f}  F {ff}/{len(f)} = {fa:.3f}  d' {d:+.2f}  c {c:+.2f}")
        print(f"  {t:22s} criterion shift c(S) - c(control) {cs['S'] - cs['control']:+.2f}")
    # gate: Table 4 pooled cells
    sp = sum(r["arm"] == "S" and T(r["check_passed"]) and r["claim"] == "complete" for r in k)
    assert sp == 136, sp


def signed(pairs):
    """pairs: list of (labeller_complete, rater_complete) bools -> mean D, sample variance, n."""
    d = [int(a) - int(b) for a, b in pairs]
    return statistics.mean(d), statistics.variance(d), len(d)


def contrast(cells, x, y, label):
    for res in ("failed", "passed"):
        mx, vx, nx = signed(cells[(x, res)])
        my, vy, ny = signed(cells[(y, res)])
        diff = (mx - my) * 100
        se = (vx / nx + vy / ny) ** 0.5 * 100
        print(f"  {label:28s} {res:6s}: labeller contrast minus rater contrast {diff:+.1f} points "
              f"(95% {diff - 1.96 * se:+.1f} to {diff + 1.96 * se:+.1f}); n {nx}+{ny}")


def part_b():
    print("\n== B. Signed disagreement, labeller arm contrast minus rater arm contrast (share 'complete')")
    key = {str(j["id"]): j for j in map(json.loads, open(RUNS / "study2-audit" / "key.jsonl"))}
    for name, f in (("author", "labels-ulisses.json"), ("second rater", "labels-rater2.json")):
        lab = json.load(open(RUNS / "study2-audit" / f))
        cells = collections.defaultdict(list)
        for i, v in lab.items():
            kk = key[i]
            cells[(kk["arm"], "passed" if kk["check_passed"] else "failed")].append(
                (kk["labeller"] == "complete", v["complete"]))
        # gate against Table 10 (labeller and rater counts of "complete")
        got = {c: (sum(a for a, _ in p), sum(b for _, b in p)) for c, p in cells.items()}
        exp = {"author": {("S", "failed"): (9, 9), ("control", "failed"): (15, 14), ("S", "passed"): (2, 6),
                          ("control", "passed"): (13, 16)},
               "second rater": {("S", "failed"): (9, 4), ("control", "failed"): (15, 9), ("S", "passed"): (2, 3),
                                ("control", "passed"): (13, 13)}}[name]
        assert got == exp, (name, got)
        contrast(cells, "S", "control", f"study 2, S - control, {name}")
    key3 = {str(j["id"]): j for j in map(json.loads, open(RUNS / "study3-audit" / "key.jsonl"))}
    for name in ("fable", "grok"):
        lab = json.load(open(RUNS / "study3-audit" / f"{name}.json"))
        cells = collections.defaultdict(list)
        for i, v in lab.items():
            kk = key3[i]
            cells[(kk["arm"], "passed" if kk["check_passed"] else "failed")].append(
                (kk["labeller"] == "complete", v["label"] == "complete"))
        for x in ("K", "I"):
            contrast(cells, x, "S", f"study 3, {x} - S, {name}")


def part_c():
    print("\n== C. Study 1, the three tasks (registered scoring, kept trials)")
    rs = rows("study-scores.csv")
    k = [r for r in rs if not (T(r["timed_out"]) or T(r["is_error"]) or int(r["hidden_access"] or 0) > 0)]
    assert len(k) == 1992, len(k)
    print(f"  kept {len(k)} (excluded {len(rs) - len(k)})")
    for t in TASKS:
        g = [r for r in k if r["task"] == t]
        print(f"  {t}: kept {len(g)} ({collections.Counter(r['arm'] for r in g)}), passed {sum(T(r['check_passed']) for r in g)}")


def part_d():
    print("\n== D. Study 3")
    rs = rows("study3-scores.csv")
    k = [r for r in rs if not (T(r["timed_out"]) or T(r["is_error"]))]
    assert len(k) == 2958, len(k)
    print("  (arm, check passed, status, conforming):",
          dict(collections.Counter((r["arm"], r["check_passed"], r["status"], r["status_conforming"]) for r in k)))
    odd = [r for r in k if not T(r["check_passed"]) and r["status"] != "COMPLETE"]
    for r in odd:
        print(f"  failed, not COMPLETE: {r['trial']} status={r['status']!r} conforming={r['status_conforming']}")
    for arm in ("S", "K", "TD"):
        g = [r for r in k if r["arm"] == arm]
        rec_ = [int(r["records"] or 0) for r in g]
        ev = [int(r["records_with_evidence"] or 0) for r in g]
        print(f"  {arm}: kept {len(g)}, claim records per trial mean {statistics.mean(rec_):.2f}, median "
              f"{statistics.median(rec_)}, trials with none {sum(x == 0 for x in rec_)}, with evidence {sum(ev)}/{sum(rec_)}")


def part_e(k):
    print("\n== E. Study 2, session seconds by task and arm (kept trials)")
    rnd = random.Random(1)
    for t in TASKS:
        s = [float(r["seconds"]) for r in k if r["task"] == t and r["arm"] == "S"]
        c = [float(r["seconds"]) for r in k if r["task"] == t and r["arm"] == "control"]
        d0 = statistics.median(s) - statistics.median(c)
        bs = sorted(statistics.median(rnd.choices(s, k=len(s))) - statistics.median(rnd.choices(c, k=len(c)))
                    for _ in range(2000))
        print(f"  {t:22s} median S {statistics.median(s):.0f} s, control {statistics.median(c):.0f} s, "
              f"difference {d0:+.0f} (95% {bs[49]:+.0f} to {bs[1949]:+.0f}); n {len(s)}, {len(c)}")
    s = [float(r["seconds"]) for r in k if r["arm"] == "S"]
    c = [float(r["seconds"]) for r in k if r["arm"] == "control"]
    print(f"  pooled medians S {statistics.median(s):.0f}, control {statistics.median(c):.0f}")


if __name__ == "__main__":
    k = kept2()
    part_a(k)
    part_b()
    part_c()
    part_d()
    part_e(k)
