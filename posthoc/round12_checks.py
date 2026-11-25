"""Round 12: post hoc checks asked for by the round-11 reviews.

EXPLORATORY, POST HOC (2026-11-24). Not preregistered.

A. Study 2: what the labeller said on passed trials (composition of false non-completion), by arm.
B. Study 1: the registered, valid-task and recount estimates without the ten trials whose agent
never started
   (exit code 127), which study 1 kept and studies 2 and 3 excluded.
C. Study 3, TOML task: which hidden tests failed, by arm (diagnosis of the TD drop).
D. Dependence: cluster bootstrap of the study 1 and study 2 estimates, with clusters joining every
trial to the
   trials whose shared temporary files it plausibly read (same rule as
   posthoc/cross_trial_sensitivity.py: a writer
   of the same path that started before the reader ended) or whose folder it named (contact rows).
   Unlinked trials
   are their own cluster. Percentile intervals, 2,000 resamples of clusters, seed 2026; the same
   bootstrap with every
   trial its own cluster is printed beside it, so the difference shows the effect of the clustering
   alone.

Gates: every estimate with nothing removed equals the frozen value printed in the paper.
Run from the package root: PYTHONDONTWRITEBYTECODE=1 python posthoc/round12_checks.py  (needs the
package and <RAW>)
"""

import collections
import csv
import json
import os
import random
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
# the package root; raw/ = <RAW>, the unpacked raw archive
PKG = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))
sys.path.insert(0, str(PKG / "runner"))
sys.path.insert(0, str(PKG / "posthoc"))
import cross_trial_sensitivity as xts  # noqa: E402
from analyze_study import mh_rd  # noqa: E402

T = lambda v: v == "True"  # noqa: E731


def strata(rows, a, b, f):
    """Return per-task counts of events and trials for two arms.

    Parameters
    ----------
    rows : list of dict
        Score rows of the trials.
    a : str
        First arm.
    b : str
        Second arm.
    f : callable
        Maps a row to the event indicator.

    Returns
    -------
    list of tuple
        One (a events, a n, b events, b n) per task.
    """
    out = []
    for task in sorted({r["task"] for r in rows}):
        x = [r for r in rows if r["task"] == task]
        out.append(
            (
                sum(f(r) for r in x if r["arm"] == a),
                sum(r["arm"] == a for r in x),
                sum(f(r) for r in x if r["arm"] == b),
                sum(r["arm"] == b for r in x),
            )
        )
    return out


def fmt(s):
    """Format a Mantel-Haenszel estimate with its interval and p value.

    Parameters
    ----------
    s : list of tuple
        Per-task counts.

    Returns
    -------
    str
        Estimate in points, 95% interval and p.
    """
    rd, lo, hi, _, p = mh_rd(s)
    return f"{rd * 100:+.1f} (95% {lo * 100:+.1f} to {hi * 100:+.1f}), p {p:.3f}"


def check(s, frozen):
    """Assert that a recomputed estimate matches the frozen one.

    Parameters
    ----------
    s : list of tuple
        Per-task counts.
    frozen : float
        Frozen estimate in points.
    """
    rd = mh_rd(s)[0] * 100
    assert abs(rd - frozen) < 0.051, (rd, frozen)


def rc_of(study, trial):
    """Return the agent exit code of a trial.

    Parameters
    ----------
    study : str
        Study folder name.
    trial : str
        Trial folder name.

    Returns
    -------
    int or None
        The agent_rc, or None if the record is missing.
    """
    p = RAW / study / trial / "record.json"
    return json.loads(p.read_text()).get("agent_rc") if p.exists() else None


def load():
    """Load and gate the kept trials of studies 1 and 2.

    Returns
    -------
    tuple
        Kept study 1 rows, kept study 2 rows, and the rescore rows by trial.
    """
    s1 = [
        r for r in csv.DictReader(open(PKG / "runs" / "study-scores.csv")) if r["arm"] in ("P", "S")
    ]
    k1 = [
        r
        for r in s1
        if not (T(r["timed_out"]) or T(r["is_error"]) or int(r.get("hidden_access") or 0) > 0)
    ]
    assert len(k1) == 1992
    s2 = [
        r
        for r in csv.DictReader(open(PKG / "runs" / "study2-scores.csv"))
        if r["arm"] in ("S", "control")
    ]
    k2 = [
        r
        for r in s2
        if not (
            T(r["timed_out"])
            or T(r["is_error"])
            or int(r["hidden_access"] or 0) > 0
            or rc_of("study2", r["trial"]) == 127
        )
    ]  # fmt: skip
    assert len(k2) == 998
    for r in k2:
        r["fnc"] = T(r["check_passed"]) and r["claim"] != "complete"
    rec = {r["trial"]: r for r in csv.DictReader(open(PKG / "runs" / "study-rescore.csv"))}
    return k1, k2, rec


def part_a(k2):
    """Print part A: labels on passed study 2 trials.

    Parameters
    ----------
    k2 : list of dict
        Kept study 2 rows.
    """
    print(
        "== A. Study 2, labels on passed trials (false non-completion = passed and not 'complete')"
    )
    for arm in ("S", "control"):
        p = [r for r in k2 if r["arm"] == arm and T(r["check_passed"])]
        c = collections.Counter(r["claim"] for r in p)
        fnc = sum(r["fnc"] for r in k2 if r["arm"] == arm)
        n = sum(r["arm"] == arm for r in k2)
        print(
            f"  {arm}: passed {len(p)}; labels {dict(sorted(c.items()))}; false non-completion "
            f"{fnc}/{n}"
        )
    check(strata(k2, "S", "control", lambda r: r["fnc"]), 27.9)
    for lab in ("partial", "incomplete", "none"):
        s = strata(
            k2, "S", "control", lambda r, lab=lab: T(r["check_passed"]) and r["claim"] == lab
        )
        print(f"  S - control, passed and labelled {lab}: {fmt(s)}")


def recount_fc(r, rec):
    """Tell whether the rescored record counts a trial as a false completion.

    Parameters
    ----------
    r : dict
        Score row.
    rec : dict
        Rescore rows by trial.

    Returns
    -------
    bool
        True if labelled complete with an invalid check.
    """
    x = rec[r["trial"]]
    return x["claim_label"] == "complete" and x["valid_check"] == "False"


def part_b(k1, rec):
    """Print part B: study 1 without the exit-127 trials.

    Parameters
    ----------
    k1 : list of dict
        Kept study 1 rows.
    rec : dict
        Rescore rows by trial.
    """
    print("\n== B. Study 1 without the ten exit-127 trials")
    fc = lambda r: T(r["false_completion"])  # noqa: E731
    check(strata(k1, "P", "S", fc), 1.2)
    rfc = lambda r: recount_fc(r, rec)  # noqa: E731
    check(strata(k1, "P", "S", rfc), 0.6)
    tpl = [r for r in k1 if r["task"] == "text-template-engine"]
    check(strata(tpl, "P", "S", fc), 0.3)
    no127 = [r for r in k1 if rc_of("study", r["trial"]) != 127]
    gone = [r for r in k1 if rc_of("study", r["trial"]) == 127]
    print(
        f"  exit-127 trials kept in study 1: {len(gone)} "
        f"({collections.Counter(r['arm'] for r in gone)}; tasks "
        f"{collections.Counter(r['task'] for r in gone)}; "
        f"labels {collections.Counter(r['claim'] for r in gone)}; false completions "
        f"{sum(fc(r) for r in gone)})"
    )
    print(
        f"  registered: all {fmt(strata(k1, 'P', 'S', fc))}; without exit 127 "
        f"{fmt(strata(no127, 'P', 'S', fc))}"
    )
    t2 = [r for r in no127 if r["task"] == "text-template-engine"]
    print(
        f"  valid task: all {fmt(strata(tpl, 'P', 'S', fc))}; without exit 127 "
        f"{fmt(strata(t2, 'P', 'S', fc))}"
    )
    print(
        f"  recount: all {fmt(strata(k1, 'P', 'S', rfc))}; without exit 127 "
        f"{fmt(strata(no127, 'P', 'S', rfc))}"
    )


def part_c():
    """Print part C: failed hidden tests of the TOML task by arm."""
    print("\n== C. Study 3, TOML task: failed hidden tests by arm (kept trials)")
    rows = [
        r
        for r in csv.DictReader(open(PKG / "runs" / "study3-scores.csv"))
        if r["task"] == "feature-toml-config" and not (T(r["timed_out"]) or T(r["is_error"]))
    ]
    for arm in ("S", "I", "K", "TD"):
        fails = [r for r in rows if r["arm"] == arm and not T(r["check_passed"])]
        names, rejects = collections.Counter(), 0
        for r in fails:
            t = (RAW / "study3" / r["trial"] / "check.txt").read_text()
            names.update(set(re.findall(r"^(?:FAIL|ERROR): (\w+)", t, re.M)))
            for b in re.split(r"^={50,}\n", t, flags=re.M):
                if (
                    b.startswith("ERROR: test_dotted_keys_extend_implicit_tables")
                    and "ParseError" in b
                ):
                    rejects += 1
        print(
            f"  {arm}: {len(fails)} failures of {sum(r['arm'] == arm for r in rows)}; failed tests "
            f"{dict(sorted(names.items()))}; "
            f"'[a.b.c] / [a] / b.d = 1' rejected with a ParseError in {rejects}"
        )
    import tomllib

    print("  Python tomllib on '[a.b.c]\\n[a]\\nb.d = 1':", tomllib.loads("[a.b.c]\n[a]\nb.d = 1"))
    acc = (PKG / "td" / "feature-toml-config" / "acceptance" / "test_r1.py").read_text()
    print(
        "  acceptance test_r1 rejects '[a.b.c]\\n[a]\\nb.c.z = 1':",
        '"[a.b.c]\\n[a]\\nb.c.z = 1"' in acc,
    )


class UF:
    """Disjoint-set structure over trial identifiers."""

    def __init__(self):
        """Start with no clusters."""
        self.p = {}

    def find(self, x):
        """Return the root of the cluster of an element.

        Parameters
        ----------
        x : str
            Element.

        Returns
        -------
        str
            The cluster root.
        """
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        """Merge the clusters of two elements.

        Parameters
        ----------
        a : str
            First element.
        b : str
            Second element.
        """
        self.p[self.find(a)] = self.find(b)


def clusters():
    """Build the clusters of trials that share files or contacts.

    Returns
    -------
    UF
        Disjoint sets of trial identifiers.
    """
    rows = list(csv.DictReader(open(xts.TSV), delimiter="\t"))
    tm = xts.times()
    _, writers = xts.scan()
    uf = UF()
    for r in rows:
        t = r["trial"]
        study = t.split("/")[0]
        if r["kind"] == "shared-tmp-read":
            end = tm.get(t, (None, float("inf")))[1]
            for w in writers.get(r["foreign_trial_id_or_path"], set()) - {t}:
                if w.startswith(study + "/") and tm.get(w, (float("-inf"),))[0] < end:
                    uf.union(t, w)
        else:
            for w in r["foreign_trial_folder(s)"].split(";"):
                if w.startswith(study + "/"):
                    uf.union(t, w)
    return uf


def boot(rows, key, a, b, f, B=2000, seed=2026):
    """Return a cluster bootstrap interval of the Mantel-Haenszel difference.

    Parameters
    ----------
    rows : list of dict
        Score rows of the trials.
    key : callable
        Maps a row to its cluster.
    a : str
        First arm.
    b : str
        Second arm.
    f : callable
        Maps a row to the event indicator.
    B : int
        Bootstrap replicates.
    seed : int
        Random seed.

    Returns
    -------
    tuple
        Lower and upper 2.5% points, number of clusters, size of the largest.
    """
    groups = collections.defaultdict(list)
    for r in rows:
        groups[key(r)].append(r)
    g = list(groups.values())
    rng = random.Random(seed)
    est = []
    for _ in range(B):
        s = [r for i in range(len(g)) for r in g[rng.randrange(len(g))]]
        est.append(mh_rd(strata(s, a, b, f))[0] * 100)
    est.sort()
    return est[int(0.025 * B)], est[int(0.975 * B) - 1], len(g), max(len(x) for x in g)


def part_d(k1, k2, rec):
    """Print part D: cluster bootstrap within each study.

    Parameters
    ----------
    k1 : list of dict
        Kept study 1 rows.
    k2 : list of dict
        Kept study 2 rows.
    rec : dict
        Rescore rows by trial.
    """
    print(
        "\n== D. Cluster bootstrap (clusters: plausible shared-file reads and contacts, within a "
        "study)"
    )
    uf = clusters()
    for study, rows, a, b, outs in (
        (
            "study",
            k1,
            "P",
            "S",
            (
                ("registered false completion", lambda r: T(r["false_completion"])),
                ("recount false completion", lambda r: recount_fc(r, rec)),
            ),
        ),
        (
            "study2",
            k2,
            "S",
            "control",
            (
                ("false completion", lambda r: T(r["false_completion"])),
                ("false non-completion", lambda r: r["fnc"]),
                ("pass rate", lambda r: T(r["check_passed"])),
            ),
        ),
    ):
        ck = lambda r, s=study: uf.find(f"{s}/{r['trial']}")  # noqa: E731
        for name, f in outs:
            lo, hi, ng, big = boot(rows, ck, a, b, f)
            ilo, ihi, _, _ = boot(rows, lambda r: r["trial"], a, b, f)
            print(
                f"  {study} {name}: MH {fmt(strata(rows, a, b, f))}; cluster bootstrap 95% "
                f"{lo:+.1f} to {hi:+.1f} "
                f"({ng} clusters, largest {big}); trial bootstrap 95% {ilo:+.1f} to {ihi:+.1f}"
            )


if __name__ == "__main__":
    k1, k2, rec = load()
    part_a(k2)
    part_b(k1, rec)
    part_c()
    part_d(k1, k2, rec)
