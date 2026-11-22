#!/usr/bin/env python3
"""`claim` — the one record tool every arm gets. Same command, same workflow; only the record's status differs.

    claim "STATEMENT" [--evidence FILE]

EXP_ARM (H, S or P) and EXP_LEDGER are set by the runner. H appends to a private, unsigned notes file. S and P
append a signed entry to a hash-chained Eilikrineia ledger (P's ledgers are published with the study's results).
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ap = argparse.ArgumentParser(prog="claim")
ap.add_argument("statement")
ap.add_argument("--evidence")
a = ap.parse_args()
arm, ledger = os.environ.get("EXP_ARM"), Path(os.environ.get("EXP_LEDGER", ""))
ev = Path(a.evidence).resolve() if a.evidence else None
if ev and not ev.is_file():
    sys.exit(f"claim: evidence file not found: {a.evidence}")

if arm == "H":
    digest = hashlib.sha256(ev.read_bytes()).hexdigest() if ev else None
    line = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "statement": a.statement,
            "evidence": a.evidence, "sha256": digest}  # fmt: skip
    with (ledger / "notes.jsonl").open("a") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    print("noted in the private, unsigned notes file")
elif arm in ("S", "P"):
    cmd = [sys.executable, str(ledger / "eilikrineia.py"), "--root", str(ledger), "record", "--role", "agent",
           "--type", "run" if ev else "opinion", "--text", a.statement]  # fmt: skip
    if ev:
        cmd += ["--attach", str(ev)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit("claim: could not record: " + r.stderr[-300:])
    seq = json.loads(r.stdout)["seq"]
    where = "the ledger that will be published with the study" if arm == "P" else "the owner's private ledger"
    print(f"signed entry #{seq} appended to {where}")
else:
    sys.exit("claim: not configured")
