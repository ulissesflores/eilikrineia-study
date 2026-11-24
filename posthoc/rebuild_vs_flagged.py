"""Round 12, part E: are the 141 study 1 rebuilds that did not reproduce the saved state among the trials flagged for
cross-trial reads? EXPLORATORY, POST HOC (2026-11-24). Reads runs/study-scores.csv, runs/study-rescore.csv and
posthoc/cross-trial-flagged.tsv of the package; no model call."""
import collections
import csv
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent  # the package root; raw/ = <RAW>, the unpacked raw archive
T = lambda v: v == "True"  # noqa: E731
s1 = {r["trial"]: r for r in csv.DictReader(open(PKG / "runs" / "study-scores.csv"))}
kept = {t for t, r in s1.items() if r["arm"] in ("P", "S")
        and not (T(r["timed_out"]) or T(r["is_error"]) or int(r.get("hidden_access") or 0) > 0)}
assert len(kept) == 1992
rec = {r["trial"]: r for r in csv.DictReader(open(PKG / "runs" / "study-rescore.csv"))}
fl = {r["trial"].split("/", 1)[1]: r for r in csv.DictReader(open(PKG / "posthoc" / "cross-trial-flagged.tsv"), delimiter="\t")
      if r["study"] == "study"}
div = [t for t in kept if not (T(rec[t]["diff_match"]) and T(rec[t]["fail_set_match"]))]
print("inexact rebuilds:", len(div), dict(sorted(collections.Counter(s1[t]["arm"] for t in div).items())))
cat = collections.Counter((s1[t]["arm"], fl[t]["evidence_category"] if t in fl else "not flagged") for t in div)
print("by arm and flag category:", dict(sorted(cat.items())))
print("in the broad flagged set (199):", sum(1 for t in div if t in fl and fl[t]["broad"] == "1"))
