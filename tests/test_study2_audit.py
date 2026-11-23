"""The post hoc human audit of study 2, locked against the ledger and the paper.

The report was run once, as the closing rule of ledger entry #1873 fixed, and is frozen here; these
tests do not run it again. They check that every shipped file is the one whose hash the ledger
recorded, that the sample has the planned design, and that the report states the numbers the paper
prints (Table 9). A reader can regenerate the report with
``python runner/audit_study2.py report runs/study2-audit ulisses rater2``. The second post hoc plan
(#2649) and its output (#2650, ``report-split.txt``, Table 10) are locked the same way; regenerate with
``cd runner && python audit_study2_split.py ../runs/study2-audit ulisses rater2``.
"""

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "runs" / "study2-audit"

# file -> (ledger entry that recorded it, sha256 in that entry)
LEDGER_HASHES = {
    "POSTHOC-STUDY2-AUDIT.md": (
        1872,
        "c96ae9bfd4143e10cbcf0632c4f253115d94a4f2fc74c7f7f62a1213b3a9017c",
    ),
    "runner/audit_study2.py": (
        1872,
        "4c780dcf3480bb30cabd2dc3164e7a92795a61b38e92dc097535a6ec3bc24e61",
    ),
    "runs/study2-audit/items.jsonl": (
        1872,
        "4421e0c892c52e9c2d93ae1d7432c8e3c4ee638bae73dc6dd286afde89fbd06e",
    ),
    "runs/study2-audit/key.jsonl": (
        1872,
        "0d0c4b21724d31f567e675b95beec8b743ef6b360fdfe747619b0740fd53bff0",
    ),
    "runs/study2-audit/items.pt.json": (
        1872,
        "c306b097d3c11fc7bf64ffa9f3b9e2b759c28b8e99beba03fd19adda2536e044",
    ),
    "runs/study2-audit/labels-ulisses.json": (
        1873,
        "fecb8f12ca2d449bea45b74f9a9caff7178fec0e63e91dec469f7304aa4df87d",
    ),
    "runs/study2-audit/labels-rater2.json": (
        2647,
        "c7b45e7fc3f16d580d7903204a9fa2039eda7570fb2eac30e66d8638f406e780",
    ),
    "runs/study2-audit/report.txt": (
        2648,
        "470d83a29a9498ae209f23b1ee16a96465155d046a22114830eefd3676cd14a2",
    ),
    "POSTHOC-STUDY2-AUDIT-SPLIT.md": (
        2649,
        "f7ea648543717d608ec30c5a95ca8c51760230b4c938dcf2c26901c1788191bd",
    ),
    "runner/audit_study2_split.py": (
        2649,
        "0c8b12ea796c23bde6cc09a864128b362903aaa0d4e97201c5bbdc3b568c9b3d",
    ),
    "runs/study2-audit/report-split.txt": (
        2650,
        "7e2e83bd192911e58aa84ea7d8c7874b339242ce5a0ab683dcc4b1bf8c2f2a7a",
    ),
}

# Four files are published as redacted derivatives of the files the ledger attached: wall-clock times of
# the raters and the machine's temporary-folder prefix were removed (labels, items and `seconds` are
# unchanged). The ledger hash above is the hash of the original; this is the hash of the shipped file.
REDACTED_HASHES = {
    "runs/study2-audit/items.jsonl": "d0a92c73cf9a78ce88b4eeb5837bba4a39aaa7c35c8cc0ba4dedf65ad53aa01a",
    "runs/study2-audit/items.pt.json": "3fa17b813c440f8bcdd0b05cf5d253480df6c0be8bdf72d7f39d26d6b3b916ff",
    "runs/study2-audit/labels-ulisses.json": "3bd0821fc5828dbbe73f40a6735aeedbd29e51286c4e27102c0ec5c923ffc8a5",
    "runs/study2-audit/labels-rater2.json": "2b4fcb3b2dbee18e411bb6837d83d4422441d3f03e70f7c83636df126820cc78",
}


def test_files_are_the_ones_the_ledger_recorded():
    """Each shipped file hashes to its ledger value (or, if redacted, to its recorded derivative hash), and the entry lists the original."""
    entries = {e["seq"]: e for e in json.loads((AUDIT / "ledger-entries.json").read_text())}
    for path, (seq, digest) in LEDGER_HASHES.items():
        shipped = REDACTED_HASHES.get(path, digest)
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == shipped, path
        assert digest in {a["sha256"] for a in entries[seq]["attachments"]}, (path, seq)


def test_ledger_order():
    """Plan, author's answers, second rater's answers, report, second plan, its output: in that order."""
    times = [e["time"] for e in json.loads((AUDIT / "ledger-entries.json").read_text())]
    assert [e["seq"] for e in json.loads((AUDIT / "ledger-entries.json").read_text())] == [
        1872,
        1873,
        2647,
        2648,
        2649,
        2650,
    ]
    assert times == sorted(times)


def test_sample_design():
    """80 messages: 40 per arm, 20 passed and 20 failed in each; both raters answered all 80."""
    key = [json.loads(x) for x in (AUDIT / "key.jsonl").read_text().splitlines() if x.strip()]
    assert len(key) == 80
    assert Counter((k["arm"], k["check_passed"]) for k in key) == {
        ("S", True): 20,
        ("S", False): 20,
        ("control", True): 20,
        ("control", False): 20,
    }
    for rater in ("ulisses", "rater2"):
        labels = json.loads((AUDIT / f"labels-{rater}.json").read_text())
        assert sorted(int(i) for i in labels) == sorted(k["id"] for k in key), rater


def test_report_states_the_published_numbers():
    """The frozen report holds every number of Table 9 of the paper."""
    report = (AUDIT / "report.txt").read_text()
    for line in (
        "== rater ulisses: 80 of 80 items; seconds per item: median 38.6, shortest 9.7",
        "all      n  80  agreement 54/80 = 67.5% (95% 56.6 to 76.8)  kappa 0.35  "
        "rater says complete 45, labeller says complete 39",
        "S        n  40  agreement 26/40 = 65.0% (95% 49.5 to 77.9)  kappa 0.21  "
        "rater says complete 15, labeller says complete 11",
        "control  n  40  agreement 28/40 = 70.0% (95% 54.6 to 81.9)  kappa 0.25  "
        "rater says complete 30, labeller says complete 28",
        "gap in agreement between arms: 5.0 points -> within 10 points",
        "== rater rater2: 80 of 80 items; seconds per item: median 30.6, shortest 0.6",
        "all      n  80  agreement 56/80 = 70.0% (95% 59.2 to 78.9)  kappa 0.40  "
        "rater says complete 29, labeller says complete 39",
        "S        n  40  agreement 30/40 = 75.0% (95% 59.8 to 85.8)  kappa 0.29  "
        "rater says complete 7, labeller says complete 11",
        "control  n  40  agreement 26/40 = 65.0% (95% 49.5 to 77.9)  kappa 0.27  "
        "rater says complete 22, labeller says complete 28",
        "gap in agreement between arms: 10.0 points -> within 10 points",
        "== ulisses against rater2: n 80, kappa 0.32",
    ):
        assert line in report, line


def test_split_report_states_the_published_numbers():
    """The frozen output of the second plan holds every count of Table 10 and the 9.4-point gap."""
    report = (AUDIT / "report-split.txt").read_text()
    for line in (
        "S        check failed  n 20  labeller complete 9 (25.8 to 65.8)  rater complete 9 (25.8 to 65.8)  "
        "2x2 [both 6, labeller only 3, rater only 3, neither 8]",
        "control  check failed  n 20  labeller complete 15 (53.1 to 88.8)  rater complete 14 (48.1 to 85.5)  "
        "2x2 [both 12, labeller only 3, rater only 2, neither 3]",
        "S        check passed  n 20  labeller complete 2 (2.8 to 30.1)  rater complete 6 (14.5 to 51.9)  "
        "2x2 [both 0, labeller only 2, rater only 6, neither 12]",
        "control  check passed  n 20  labeller complete 13 (43.3 to 81.9)  rater complete 16 (58.4 to 91.9)  "
        "2x2 [both 11, labeller only 2, rater only 5, neither 2]",
        "S        check failed  n 20  labeller complete 9 (25.8 to 65.8)  rater complete 4 (8.1 to 41.6)  "
        "2x2 [both 4, labeller only 5, rater only 0, neither 11]",
        "control  check failed  n 20  labeller complete 15 (53.1 to 88.8)  rater complete 9 (25.8 to 65.8)  "
        "2x2 [both 9, labeller only 6, rater only 0, neither 5]",
        "S        check passed  n 20  labeller complete 2 (2.8 to 30.1)  rater complete 3 (5.2 to 36.0)  "
        "2x2 [both 0, labeller only 2, rater only 3, neither 15]",
        "control  check passed  n 20  labeller complete 13 (43.3 to 81.9)  rater complete 13 (43.3 to 81.9)  "
        "2x2 [both 9, labeller only 4, rater only 4, neither 3]",
        "== rater rater2: removed 1 answer(s) [63]",
        "== rater ulisses: removed 0 answer(s) []",
        "gap in agreement between arms: 9.4 points -> within 10 points",
    ):
        assert line in report, line
