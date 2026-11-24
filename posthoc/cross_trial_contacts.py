"""Post hoc: the first transcript line of each 'contact' trial (a trial-id-* row of cross-trial-reads.tsv), with context,
so the description of contact trials can be checked. Reads the raw archive (<RAW>, default raw/), read only."""
import csv
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # never write .pyc into the sealed runner/ folder
HERE = Path(__file__).resolve().parent
PKG = HERE.parent  # the package root: run from there, the paths below are relative to it
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))  # <RAW>: the raw trial archive, unpacked
TSV = HERE / "cross-trial-reads.tsv"
# the host's per-user temp prefix (macOS /private/var/folders/<xx>/<hash>/T/ or /var/folders/...) is machine-specific:
# replace it by <TMPDIR> before the excerpt is cut, so the trial id after it stays and the prefix never is printed
TMP_PREFIX = re.compile(r"(?:/private)?/var/folders/[^/\\\s\"]+/[^/\\\s\"]+/T/")
rows = [r for r in csv.DictReader(open(TSV), delimiter="\t") if r["kind"].startswith("trial-id-")]
seen = {}
for r in sorted(rows, key=lambda r: (r["trial"], int(r["line"]))):
    seen.setdefault(r["trial"], r)
print(f"contact trials: {len(seen)}")
for t, r in seen.items():
    line = (RAW / t / "agent.stdout").read_text(errors="replace").splitlines()[int(r["line"]) - 1]
    line = TMP_PREFIX.sub("<TMPDIR>/", line)
    i = line.find(TMP_PREFIX.sub("<TMPDIR>/", r["foreign_trial_id_or_path"]))
    print(f"{t} | line {r['line']} | {r['kind']} | ...{line[max(0, i - 110):i + 50]}...".replace("\\n", " "))
