# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Carlos Ulisses Flores (Codex Hash Ltda.)
"""Preregistration chronology of the four experiments, from files only (no network).

For each preregistration entry of the author's Eilikrineia ledger the script prints: entry number,
recorded time, hash, whether the SHA-256 of the shipped preregistration document is among the
entry's attachments, and whether the trial schedule saved at the start of the study's run
(<RAW>/<study>/schedule.txt) is reproduced by the package's shuffle with the seed taken from the
entry hash.

External timestamps: the first OpenTimestamps stamp of the public ledger repository whose sequence
number covers the entry (stamps/NNNNNN.txt names a head), its attestations as printed by `ots info`
(offline; never `ots verify`), and the commit time at which the entry file first appears in the
public repository's git history; for study 3, the three RFC 3161 tokens over prereg/study3/pins.txt
(time, imprint, signature checked offline with `openssl ts -verify`) and the OpenTimestamps proof of
pins.txt.

First trial: the earliest `started` in the record.json files of the raw trial folders (not folder
0001).

Inputs
------
- The raw archive <RAW> (environment variable EILIKRINEIA_RAW, default raw/): schedule.txt and
  record.json of each study.
- <CHAIN> (environment variable EILIKRINEIA_CHAIN, default ../eilikrineia relative to the package
  root): a git clone of the public ledger https://github.com/ulissesflores/eilikrineia (chain/,
  stamps/, full history).
- The package: the preregistration documents and prereg/study3/ (pins.txt, its timestamp tokens and
  proofs).
- The external tools git, openssl and ots, run offline. Trust anchors for the RFC 3161 check:
  freetsa -> prereg/study3/freetsa-cacert.pem; sectigo -> posthoc/usertrust-rsa-root.pem (the
  USERTrust RSA root, SHA-256 fingerprint E7:93:C9:B0:...:C3:D4:CB:D2; with the Mozilla bundle that
  Linux systems ship, OpenSSL 3.5 picked the self-signed Sectigo R46 root in a test and the token
  failed the signing certificate check); digicert -> the system CA bundle (the first existing of
  /etc/ssl/cert.pem, /etc/ssl/certs/ca-certificates.crt and /etc/pki/tls/certs/ca-bundle.crt; the
  script stops with an error if none exists).

Outputs
-------
- One block per study on standard output; the committed posthoc/prereg_chronology.txt must be
  reproduced byte for byte.

Usage
-----
    PYTHONDONTWRITEBYTECODE=1 python posthoc/prereg_chronology.py

Status
------
Post hoc, exploratory, not preregistered. The numbers it backs are listed in
posthoc/paper_numbers.json.

Author
------
Carlos Ulisses Flores, ORCID https://orcid.org/0000-0002-6034-7765

Repository
----------
https://github.com/ulissesflores/eilikrineia-study
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
# <RAW>: schedule.txt and record.json of each study
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))
# <CHAIN>: a git clone of the public ledger https://github.com/ulissesflores/eilikrineia (chain/,
# stamps/, full history)
LEDGER = Path(os.environ.get("EILIKRINEIA_CHAIN", PKG.parent / "eilikrineia"))
STUDIES = (
    ("Pilot", 1331, "PREREGISTRATION.md", "pilot"),
    ("Study 1", 1411, "PREREGISTRATION-STUDY.md", "study"),
    ("Study 2", 1536, "PREREGISTRATION-STUDY2.md", "study2"),
    ("Study 3", 1543, "PREREGISTRATION-STUDY3.md", "study3"),
)


def sh(*cmd, cwd=None):
    """Run a command and return its standard output.

    Parameters
    ----------
    cmd : str
        Command and arguments.
    cwd : Path or None
        Working directory.

    Returns
    -------
    str
        Standard output text.
    """
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd).stdout


def ca_bundle():
    """Return the system CA bundle that `openssl ts -verify` uses as `-CAfile`.

    The bundle lives at a different path on macOS, Debian/Ubuntu and Red Hat systems.

    Returns
    -------
    Path
        The first existing of `/etc/ssl/cert.pem`, `/etc/ssl/certs/ca-certificates.crt` and
        `/etc/pki/tls/certs/ca-bundle.crt`.

    Raises
    ------
    FileNotFoundError
        If none of them exists.
    """
    candidates = (
        "/etc/ssl/cert.pem",
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
    )
    for path in candidates:
        if Path(path).is_file():
            return Path(path)
    raise FileNotFoundError("no system CA bundle found; looked for " + ", ".join(candidates))


def plan(tasks, arms, reps, seed):
    """Return the shuffled schedule of a study.

    Parameters
    ----------
    tasks : list of str
        Task names.
    arms : list of str
        Arm names.
    reps : int
        Repetitions.
    seed : str
        Hex seed from the ledger hash.

    Returns
    -------
    list of tuple
        The (task, arm, repetition) schedule.
    """
    p = [
        (t, a, r) for t in tasks for a in arms for r in range(1, reps + 1)
    ]  # as runner/run_batch.py and run_pilot.py
    random.Random(int(seed[:8], 16)).shuffle(p)
    return p


def schedule_match(study, seed):
    """Tell whether a study's schedule file follows from the ledger hash.

    Parameters
    ----------
    study : str
        Study folder name.
    seed : str
        Hex seed from the ledger hash.

    Returns
    -------
    str
        A 'yes' or 'no' text.
    """
    lines = [x.split() for x in (RAW / study / "schedule.txt").read_text().splitlines()]
    want = [(t, a, int(r[1:])) for _, t, a, r in lines]
    tasks = sorted({t for t, _, _ in want})
    arms = sorted({a for _, a, _ in want})
    reps = max(r for *_, r in want)
    # run_pilot.py: sorted solvable tasks, then billing-month-end and oncall-rota; arms H, S, P
    if study == "pilot":
        extra = ["billing-month-end", "oncall-rota"]
        solv = sorted(t for t in tasks if t not in extra)
        cands = [(solv + extra, ["H", "S", "P"])]
    else:
        cands = [
            (list(t), list(a))
            for t in itertools.permutations(tasks)
            for a in itertools.permutations(arms)
        ]
    for t, a in cands:
        if plan(t, a, reps, seed) == want:
            return (
                f"yes ({len(want)} trials; --tasks "
                f"{','.join(t) if len(t) < 5 else 'as run_pilot.py'} --arms {','.join(a)})"
            )
    return f"no ({len(cands)} task/arm orders tried)"


def first_stamp(seq):
    """Return the first timestamp file that covers a ledger entry.

    Parameters
    ----------
    seq : int
        Ledger entry number.

    Returns
    -------
    tuple
        Stamp number, previous stamp, Bitcoin blocks, date added and stamp text.
    """
    seqs = sorted(int(p.name[:6]) for p in (LEDGER / "stamps").glob("[0-9]*.txt"))
    before = max(s for s in seqs if s < seq)
    s = min(x for x in seqs if x >= seq)
    f = LEDGER / "stamps" / f"{s:06d}.txt"
    info = sh("ots", "info", str(f) + ".ots")
    btc = sorted(set(re.findall(r"BitcoinBlockHeaderAttestation\((\d+)\)", info)))
    added = sh(
        "git", "log", "--diff-filter=A", "--format=%cI", "--", f"stamps/{s:06d}.txt.ots", cwd=LEDGER
    ).split()
    return s, before, btc, (added[-1] if added else None), f.read_text().split()


def first_trial(study):
    """Return the first and last trial starts of a study.

    Parameters
    ----------
    study : str
        Study folder name.

    Returns
    -------
    tuple
        First and last (start, trial) pairs and the count.
    """
    st = []
    for rec in (RAW / study).glob("*/record.json"):
        r = json.loads(rec.read_text())
        if r.get("started"):
            st.append((r["started"], rec.parent.name))
    st.sort()
    return st[0], st[-1], len(st)


def main():
    """Print the chronology table of the four experiments."""
    print(
        "| Experiment | Ledger entry | Entry time (UTC) | Entry hash | Prereg doc in attachments | "
        "Schedule from hash "
        "| First OTS stamp covering entry (seq; Bitcoin blocks; first commit of .ots) | Entry file "
        "first in public git "
        "| First trial start (UTC) |"
    )
    for name, seq, doc, study in STUDIES:
        e = json.loads((LEDGER / "chain" / f"{seq:06d}.json").read_text())
        dh = hashlib.sha256((PKG / doc).read_bytes()).hexdigest()
        att = dh in e.get("attachments", [])
        sched = schedule_match(study, e["hash"])
        s, before, btc, added, stxt = first_stamp(seq)
        git = sh(
            "git",
            "log",
            "--diff-filter=A",
            "--format=%cI",
            "--",
            f"chain/{seq:06d}.json",
            cwd=LEDGER,
        ).split()
        (t0, f0), (t1, f1), n = first_trial(study)
        print(
            f"| {name} | #{seq} ({e['type']}) | {e['time']} | {e['hash'][:16]}… | {att} ({doc} "
            f"{dh[:12]}…) | {sched} "
            f"| #{s} (head {stxt[-1][:12]}…; previous stamp #{before}); blocks "
            f"{', '.join(btc) or 'none'}; {added} "
            f"| {git[-1] if git else None} | {t0} ({f0}); last start {t1}; {n} records |"
        )

    print("\nStudy 3 seal: prereg/study3/pins.txt")
    pins = PKG / "prereg/study3/pins.txt"
    ph = hashlib.sha256(pins.read_bytes()).hexdigest()
    print(f"  sha256(pins.txt) {ph}; header: {pins.read_text().splitlines()[0]}")
    listed = dict(
        reversed(x.split())
        for x in pins.read_text().splitlines()
        if re.match(r"^[0-9a-f]{64}\s", x)
    )
    print(
        f"  files pinned {len(listed)}; PREREGISTRATION-STUDY3.md pinned hash equals shipped file: "
        f"{listed.get('PREREGISTRATION-STUDY3.md') == hashlib.sha256((PKG / 'PREREGISTRATION-STUDY3.md').read_bytes()).hexdigest()}"  # noqa: E501
    )
    for tsa in ("digicert", "freetsa", "sectigo"):
        tsr = PKG / f"prereg/study3/pins.txt.{tsa}.tsr"
        txt = sh("openssl", "ts", "-reply", "-in", str(tsr), "-text")
        when = re.search(r"Time stamp: (.+)", txt).group(1).strip()
        block = txt.split("Message data:")[1].split("Serial number")[0]
        imprint = "".join(
            "".join(re.findall(r"\b[0-9a-f]{2}\b", m.replace("-", " ")))
            for m in re.findall(r"^\s+[0-9a-f]{4} - (.{47})", block, re.M)
        )
        ca = {
            "freetsa": PKG / "prereg/study3/freetsa-cacert.pem",
            "sectigo": PKG / "posthoc/usertrust-rsa-root.pem",
        }.get(tsa) or ca_bundle()
        ver = subprocess.run(
            ["openssl", "ts", "-verify", "-data", str(pins), "-in", str(tsr), "-CAfile", str(ca)],
            capture_output=True,
            text=True,
        )
        print(
            f"  RFC 3161 {tsa}: {when}; imprint == sha256(pins.txt): {imprint[:64] == ph}; "
            f"openssl ts -verify: "
            f"{'OK' if 'Verification: OK' in ver.stdout + ver.stderr else 'NOT OK'}"
        )
    info = sh("ots", "info", str(pins) + ".ots")
    # outside the f-string: Python 3.11
    blocks = sorted(set(re.findall(r"BitcoinBlockHeaderAttestation[(](\d+)[)]", info)))
    print(f"  OpenTimestamps pins.txt.ots Bitcoin block attestations: {blocks}")
    print(
        "\nNote: block heights are printed as read from the proofs; their times need a Bitcoin "
        "node and were not looked up."
    )


if __name__ == "__main__":
    main()


def search_completeness():
    """Print checks behind the 'None' cells."""
    print("\n== Completeness checks for the 'None' cells")
    for root in (PKG,):
        hits = [
            p for p in root.rglob("*") if p.suffix in (".tsr", ".tsq", ".ots") or "pins" in p.name
        ]
        hits = [
            p
            for p in hits
            if not any(
                x in p.parts for x in ("raw", "pilot", "study", "study2", "study3", "prereg")
            )
            or (
                p.parent.name not in ("study3",)
                and "prereg" in p.parts
                and p.suffix in (".tsr", ".ots")
            )
        ]
        print(
            f"  <package root>: timestamp/pins files outside the study 3 seal: "
            f"{[str(p.relative_to(root)) for p in hits]}"
        )
    s2 = (PKG / "runs/study2-pins.txt").read_text().splitlines()[0]
    print(f"  runs/study2-pins.txt header: {s2!r} (a hash list; no token or proof beside it)")
    log = sh("git", "log", "--all", "--format=%cI %s", cwd=LEDGER).splitlines()
    c106 = [x for x in log if "through #106," in x]
    c1543 = [x for x in log if "through #1543," in x]
    between = [
        x for x in log if c106 and c1543 and c106[-1][:25] < x[:25] < min(y[:25] for y in c1543)
    ]
    print(
        f"  ledger commit for #106: {c106}; first commit for #1543: {sorted(c1543)[0]}; commits "
        f"strictly between (all refs): {between}"
    )
    print(
        f"  local main == origin/main: {sh('git', 'rev-parse', 'main', cwd=LEDGER).strip() == sh('git', 'rev-parse', 'origin/main', cwd=LEDGER).strip()}"  # noqa: E501
    )
    for seq in (1331, 1411, 1536):
        a = sh(
            "git",
            "log",
            "--all",
            "--diff-filter=A",
            "--format=%h %cI",
            "--",
            f"chain/{seq:06d}.json",
            cwd=LEDGER,
        ).split("\n")
        print(f"  chain/{seq:06d}.json first added (all refs): {[x for x in a if x]}")


if __name__ == "__main__":
    search_completeness()
