"""Post hoc: real excerpts for Appendix A (study 2 audit items that mention Python 3.8 or hedge a result),
with the labeller's, the author's and the second rater's answers. POST HOC (2026-11-23). Reads the package's
runs/study2-audit/ (items.jsonl, key.jsonl, labels-ulisses.json, labels-rater2.json) only."""
import json
import re
from pathlib import Path

A = Path(__file__).resolve().parent.parent / "runs" / "study2-audit"  # the package root
items = {json.loads(x)["id"]: json.loads(x) for x in open(A / "items.jsonl")}
key = {json.loads(x)["id"]: json.loads(x) for x in open(A / "key.jsonl")}
au = json.loads((A / "labels-ulisses.json").read_text())
r2 = json.loads((A / "labels-rater2.json").read_text())
PY38 = re.compile(r"(?<![\d.])3\.8(?![\d])")
c = lambda b: "complete" if b else "not complete"  # noqa: E731
n = lab = a = b = 0
for i, it in sorted(items.items()):
    if not PY38.search(it["message"]):
        continue
    k = key[i]
    n += 1
    lab += k["labeller"] == "complete"
    a += au[str(i)]["complete"]
    b += r2[str(i)]["complete"]
    lines = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", it["message"]) if PY38.search(s)]
    print(f"item {i} ({k['arm']}, check {'passed' if k['check_passed'] else 'failed'}): labeller {k['labeller']}, "
          f"author {c(au[str(i)]['complete'])}, second rater {c(r2[str(i)]['complete'])}")
    for s in lines:
        print("    " + s)
print(f"\naudited messages that mention 3.8: {n} of {len(items)}; called complete by the labeller {lab}, "
      f"the author {a}, the second rater {b}")

# Task composition of the audit sample: arms are balanced on pass/fail, not on task.
from collections import Counter  # noqa: E402

comp = Counter((k["arm"], "passed" if k["check_passed"] else "failed", k["task"]) for k in key.values())
print("\naudit sample by arm, hidden check and task:")
for arm in ("S", "control"):
    for res in ("passed", "failed"):
        print(f"  {arm}, {res}: " + ", ".join(f"{t} {comp[(arm, res, t)]}" for t in
                                             ("feature-toml-config", "feature-uri-resolve", "text-template-engine")))
