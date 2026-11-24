"""Post hoc: preregistration chronology of the four experiments, from files only (no network).

For each preregistration entry of the author's Eilikrineia ledger: entry number, recorded time, hash, whether the
SHA-256 of the shipped preregistration document is among the entry's attachments, and whether the trial schedule saved
at the start of the batch (runs/<study>/schedule.txt) is reproduced by the package's shuffle with the seed taken from
the entry hash. External timestamps: the first OpenTimestamps stamp of the public ledger repository whose sequence
number covers the entry (stamps/NNNNNN.txt names a head), its attestations as printed by `ots info` (offline; never
`ots verify`), and the commit time at which the entry file first appears in the public repository's git history; for
study 3, the three RFC 3161 tokens over prereg/study3/pins.txt (time, imprint, signature checked offline with
`openssl ts -verify`) and the OpenTimestamps proof of pins.txt. First trial: the earliest `started` in the
record.json files of the raw trial folders (not folder 0001).
"""

import hashlib
import itertools
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
PKG = Path(__file__).resolve().parent.parent  # the package root
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))  # <RAW>: schedule.txt and record.json of each batch
# <CHAIN>: a git clone of the public ledger https://github.com/ulissesflores/eilikrineia (chain/, stamps/, full history)
LEDGER = Path(os.environ.get("EILIKRINEIA_CHAIN", PKG.parent / "eilikrineia"))
STUDIES = (("Pilot", 1331, "PREREGISTRATION.md", "pilot"), ("Study 1", 1411, "PREREGISTRATION-STUDY.md", "study"),
           ("Study 2", 1536, "PREREGISTRATION-STUDY2.md", "study2"), ("Study 3", 1543, "PREREGISTRATION-STUDY3.md", "study3"))


def sh(*cmd, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd).stdout


def plan(tasks, arms, reps, seed):
    p = [(t, a, r) for t in tasks for a in arms for r in range(1, reps + 1)]  # as runner/run_batch.py and run_pilot.py
    random.Random(int(seed[:8], 16)).shuffle(p)
    return p


def schedule_match(study, seed):
    lines = [x.split() for x in (RAW / study / "schedule.txt").read_text().splitlines()]
    want = [(t, a, int(r[1:])) for _, t, a, r in lines]
    tasks = sorted({t for t, _, _ in want})
    arms = sorted({a for _, a, _ in want})
    reps = max(r for *_, r in want)
    if study == "pilot":  # run_pilot.py: sorted solvable tasks, then billing-month-end and oncall-rota; arms H, S, P
        extra = ["billing-month-end", "oncall-rota"]
        solv = sorted(t for t in tasks if t not in extra)
        cands = [(solv + extra, ["H", "S", "P"])]
    else:
        cands = [(list(t), list(a)) for t in itertools.permutations(tasks) for a in itertools.permutations(arms)]
    for t, a in cands:
        if plan(t, a, reps, seed) == want:
            return f"yes ({len(want)} trials; --tasks {','.join(t) if len(t) < 5 else 'as run_pilot.py'} --arms {','.join(a)})"
    return f"no ({len(cands)} task/arm orders tried)"


def first_stamp(seq):
    seqs = sorted(int(p.name[:6]) for p in (LEDGER / "stamps").glob("[0-9]*.txt"))
    before = max(s for s in seqs if s < seq)
    s = min(x for x in seqs if x >= seq)
    f = LEDGER / "stamps" / f"{s:06d}.txt"
    info = sh("ots", "info", str(f) + ".ots")
    btc = sorted(set(re.findall(r"BitcoinBlockHeaderAttestation\((\d+)\)", info)))
    added = sh("git", "log", "--diff-filter=A", "--format=%cI", "--", f"stamps/{s:06d}.txt.ots", cwd=LEDGER).split()
    return s, before, btc, (added[-1] if added else None), f.read_text().split()


def first_trial(study):
    st = []
    for rec in (RAW / study).glob("*/record.json"):
        r = json.loads(rec.read_text())
        if r.get("started"):
            st.append((r["started"], rec.parent.name))
    st.sort()
    return st[0], st[-1], len(st)


def main():
    print("| Experiment | Ledger entry | Entry time (UTC) | Entry hash | Prereg doc in attachments | Schedule from hash "
          "| First OTS stamp covering entry (seq; Bitcoin blocks; first commit of .ots) | Entry file first in public git "
          "| First trial start (UTC) |")
    for name, seq, doc, study in STUDIES:
        e = json.loads((LEDGER / "chain" / f"{seq:06d}.json").read_text())
        dh = hashlib.sha256((PKG / doc).read_bytes()).hexdigest()
        att = dh in e.get("attachments", [])
        sched = schedule_match(study, e["hash"])
        s, before, btc, added, stxt = first_stamp(seq)
        git = sh("git", "log", "--diff-filter=A", "--format=%cI", "--", f"chain/{seq:06d}.json", cwd=LEDGER).split()
        (t0, f0), (t1, f1), n = first_trial(study)
        print(f"| {name} | #{seq} ({e['type']}) | {e['time']} | {e['hash'][:16]}… | {att} ({doc} {dh[:12]}…) | {sched} "
              f"| #{s} (head {stxt[-1][:12]}…; previous stamp #{before}); blocks {', '.join(btc) or 'none'}; {added} "
              f"| {git[-1] if git else None} | {t0} ({f0}); last start {t1}; {n} records |")

    print("\nStudy 3 seal: prereg/study3/pins.txt")
    pins = PKG / "prereg/study3/pins.txt"
    ph = hashlib.sha256(pins.read_bytes()).hexdigest()
    print(f"  sha256(pins.txt) {ph}; header: {pins.read_text().splitlines()[0]}")
    listed = dict(reversed(x.split()) for x in pins.read_text().splitlines() if re.match(r"^[0-9a-f]{64}\s", x))
    print(f"  files pinned {len(listed)}; PREREGISTRATION-STUDY3.md pinned hash equals shipped file: "
          f"{listed.get('PREREGISTRATION-STUDY3.md') == hashlib.sha256((PKG / 'PREREGISTRATION-STUDY3.md').read_bytes()).hexdigest()}")
    for tsa in ("digicert", "freetsa", "sectigo"):
        tsr = PKG / f"prereg/study3/pins.txt.{tsa}.tsr"
        txt = sh("openssl", "ts", "-reply", "-in", str(tsr), "-text")
        when = re.search(r"Time stamp: (.+)", txt).group(1).strip()
        block = txt.split("Message data:")[1].split("Serial number")[0]
        imprint = "".join("".join(re.findall(r"\b[0-9a-f]{2}\b", m.replace("-", " "))) for m in
                          re.findall(r"^\s+[0-9a-f]{4} - (.{47})", block, re.M))
        ca = PKG / "prereg/study3/freetsa-cacert.pem" if tsa == "freetsa" else Path("/etc/ssl/cert.pem")
        ver = subprocess.run(["openssl", "ts", "-verify", "-data", str(pins), "-in", str(tsr), "-CAfile", str(ca)],
                             capture_output=True, text=True)
        print(f"  RFC 3161 {tsa}: {when}; imprint == sha256(pins.txt): {imprint[:64] == ph}; "
              f"openssl ts -verify: {'OK' if 'Verification: OK' in ver.stdout + ver.stderr else 'NOT OK'}")
    info = sh("ots", "info", str(pins) + ".ots")
    blocks = sorted(set(re.findall(r"BitcoinBlockHeaderAttestation[(](\d+)[)]", info)))  # outside the f-string: Python 3.11
    print(f"  OpenTimestamps pins.txt.ots Bitcoin block attestations: {blocks}")
    print("\nNote: block heights are printed as read from the proofs; their times need a Bitcoin node and were not looked up.")


if __name__ == "__main__":
    main()


def search_completeness():
    """Checks behind the 'None' cells: other timestamp files, and the ledger repository's commits around the gap."""
    print("\n== Completeness checks for the 'None' cells")
    for root in (PKG,):
        hits = [p for p in root.rglob("*") if p.suffix in (".tsr", ".tsq", ".ots") or "pins" in p.name]
        hits = [p for p in hits if not any(x in p.parts for x in ("raw", "pilot", "study", "study2", "study3", "prereg"))
                or (p.parent.name not in ("study3",) and "prereg" in p.parts and p.suffix in (".tsr", ".ots"))]
        print(f"  <package root>: timestamp/pins files outside the study 3 seal: {[str(p.relative_to(root)) for p in hits]}")
    s2 = (PKG / "runs/study2-pins.txt").read_text().splitlines()[0]
    print(f"  runs/study2-pins.txt header: {s2!r} (a hash list; no token or proof beside it)")
    log = sh("git", "log", "--all", "--format=%cI %s", cwd=LEDGER).splitlines()
    c106 = [x for x in log if "through #106," in x]
    c1543 = [x for x in log if "through #1543," in x]
    between = [x for x in log if c106 and c1543 and c106[-1][:25] < x[:25] < min(y[:25] for y in c1543)]
    print(f"  ledger commit for #106: {c106}; first commit for #1543: {sorted(c1543)[0]}; commits strictly between (all refs): {between}")
    print(f"  local main == origin/main: {sh('git', 'rev-parse', 'main', cwd=LEDGER).strip() == sh('git', 'rev-parse', 'origin/main', cwd=LEDGER).strip()}")
    for seq in (1331, 1411, 1536):
        a = sh("git", "log", "--all", "--diff-filter=A", "--format=%h %cI", "--", f"chain/{seq:06d}.json", cwd=LEDGER).split("\n")
        print(f"  chain/{seq:06d}.json first added (all refs): {[x for x in a if x]}")


if __name__ == "__main__":
    search_completeness()
