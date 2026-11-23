"""The published numbers as assertions.

Three kinds of check:

1. counts recomputed from the per-trial files (``scripts/make_results.py``) equal the published ones;
2. each published estimate with an interval is the line in the frozen analysis output;
3. the README, ``docs/findings.md`` and the results documents state those same numbers.

Study 2's denominators and the study 2 and study 3 estimates need the raw trial folders, which are
not in this repository; they are locked as text against the frozen outputs (kind 2).
"""

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
AUDIT = RUNS / "study3-audit"
sys.path.insert(0, str(ROOT / "scripts"))

import make_results  # noqa: E402

RESULTS = make_results.compute()


def test_results_file_matches_recomputation():
    """The committed ``output/results.json`` is what the script recomputes."""
    assert json.loads((ROOT / "output" / "results.json").read_text()) == RESULTS


def test_trial_totals():
    """Trial counts of the four experiments and their sum."""
    assert RESULTS["trials"] == {
        "pilot": 180,
        "study1": 1998,
        "study2": 1082,
        "study3": 2964,
        "total": 6224,
    }


@pytest.mark.parametrize(
    (
        "arm",
        "kept",
        "passed",
        "said",
        "false_completion",
        "false_non_completion",
        "status_complete",
    ),
    [
        ("S", 740, 608, 248, 56, 416, 132),
        ("I", 740, 613, 290, 73, 396, 125),
        ("K", 741, 608, 275, 65, 398, 133),
        ("TD", 737, 620, 371, 78, 327, 117),
    ],
)
def test_study3_counts(
    arm, kept, passed, said, false_completion, false_non_completion, status_complete
):
    """Study 3 counts per arm, recomputed from the per-trial scores."""
    got = RESULTS["study3"][arm]
    assert got["kept"] == kept
    assert got["passed"] == passed
    assert got["said_complete"] == said
    assert got["false_completion"] == false_completion
    assert got["false_non_completion"] == false_non_completion
    assert got["status_complete_on_failure"] == status_complete


def test_study3_status_total():
    """Across the four arms, 507 of 509 failed trials answered STATUS: COMPLETE."""
    assert RESULTS["study3_status_complete_on_failure"] == {"complete": 507, "failed": 509}


def test_study3_percentages():
    """The percentages quoted for study 3 follow from the recomputed counts."""
    s, td = RESULTS["study3"]["S"], RESULTS["study3"]["TD"]
    assert f"{100 * td['passed'] / td['kept']:.1f}" == "84.1"
    assert f"{100 * s['passed'] / s['kept']:.1f}" == "82.2"
    assert f"{100 * s['false_completion'] / s['kept']:.1f}" == "7.6"


@pytest.mark.parametrize(
    ("arm", "passed", "false_completion", "false_non_completion"),
    [("S", 402, 48, 266), ("control", 396, 81, 119)],
)
def test_study2_numerators(arm, passed, false_completion, false_non_completion):
    """Study 2 numerators, recomputed from the per-trial scores."""
    assert RESULTS["study2_numerators"][arm] == {
        "passed": passed,
        "false_completion": false_completion,
        "false_non_completion": false_non_completion,
    }


# arm, task, kept (frozen per-task line), passed, "complete" after passing, "complete" after failing
STUDY2_BY_TASK = [
    ("S", "feature-toml-config", 171, 165, 48, 4),
    ("S", "feature-uri-resolve", 163, 120, 28, 14),
    ("S", "text-template-engine", 171, 117, 60, 30),
    ("control", "feature-toml-config", 156, 151, 71, 4),
    ("control", "feature-uri-resolve", 166, 136, 109, 25),
    ("control", "text-template-engine", 171, 109, 97, 52),
]


@pytest.mark.parametrize(
    ("arm", "task", "kept", "passed", "after_pass", "after_fail"), STUDY2_BY_TASK
)
def test_study2_complete_by_task(arm, task, kept, passed, after_pass, after_fail):
    """Study 2 per task: "complete" after passing and after failing (the paper's Table 5)."""
    assert RESULTS["study2_by_task"][arm][task] == {
        "passed": passed,
        "complete_after_passing": after_pass,
        "complete_after_failing": after_fail,
    }
    frozen = (RUNS / "study2-analysis.txt").read_text()
    name = "S" if arm == "S" else "control"
    assert (
        f"{name} {after_fail}/{kept}" in frozen
    )  # the frozen false-completion line gives the kept trials


def test_study2_pooled_rows_hide_a_task_reversal():
    """In the control, template task, "complete" is more frequent after passing than after failing."""
    assert 97 / 109 > 52 / 62
    assert sum(r[4] for r in STUDY2_BY_TASK if r[0] == "S") == 136  # Table 4, primary file


def test_study2_said_and_did_on_the_primary_cohort():
    """The paper's Table 4 on the kept trials: "complete" after passing, after failing, and true."""
    tot = {
        arm: [sum(r[i] for r in STUDY2_BY_TASK if r[0] == arm) for i in (2, 3, 4, 5)]
        for arm in ("S", "control")
    }
    assert tot == {"S": [505, 402, 136, 48], "control": [493, 396, 277, 81]}
    rate = [f"{100 * n / d:.1f}" for n, d in ((136, 184), (277, 358), (48, 103), (81, 97))]
    assert rate == ["73.9", "77.4", "46.6", "83.5"]


def test_exploratory_estimates_added_by_the_paper():
    """K - S equivalence interval (within the margin of 5 points) and the study 2 pass-rate difference."""
    assert RESULTS["exploratory"] == {
        "study3_k_minus_s_false_completion_tost": [1.2, -2.1, 4.5],
        "study2_pass_rate_s_minus_control": [-1.2, -6.0, 3.5],
    }


def test_study2_percentages():
    """The study 2 percentages follow from the numerators and the frozen denominators (505 and 493)."""
    assert [f"{100 * n / d:.1f}" for n, d in ((48, 505), (81, 493), (266, 505), (119, 493))] == [
        "9.5",
        "16.4",
        "52.7",
        "24.1",
    ]
    assert [f"{100 * n / d:.1f}" for n, d in ((402, 505), (396, 493), (184, 505), (358, 493))] == [
        "79.6",
        "80.3",
        "36.4",
        "72.6",
    ]


FROZEN = [
    ("pilot-analysis.txt", "P-S M1: +3.2 points (95% -9.7 to +16.0)"),
    ("study-analysis.txt", "P: 266/995 = 26.7%"),
    ("study-analysis.txt", "S: 255/997 = 25.6%"),
    ("study-analysis.txt", "MH P-S by task: +1.2 points (95% -2.7 to +5.0)"),
    (
        "study-check-validity.txt",
        "text-template-engine only: P 84/333 S 83/333; MH P-S +0.3 (95% -6.3 to +6.9)",
    ),
    (
        "study-rescore-analysis.txt",
        "all trials:      P 119/995 S 113/997; MH P-S +0.6 (95% -2.1 to +3.3)",
    ),
    ("study2-analysis.txt", "S: 48/505 = 9.5%"),
    ("study2-analysis.txt", "control: 81/493 = 16.4%"),
    ("study2-analysis.txt", "MH S-control by task: -6.6 points (95% -10.6 to -2.6)"),
    ("study2-analysis.txt", "S: 266/505 = 52.7%"),
    ("study2-analysis.txt", "control: 119/493 = 24.1%"),
    ("study2-analysis.txt", "MH S-control by task: +27.9 points (95% +22.4 to +33.3)"),
    ("study2-analysis.txt", "S: passed 402/505, says complete 184/505"),
    ("study2-analysis.txt", "control: passed 396/493, says complete 358/493"),
    ("study2-sensitivity.txt", "'complete' true 136/185 = 73.5%"),
    ("study2-sensitivity.txt", "'complete' true 279/360 = 77.5%"),
    ("study2-z1.txt", "MH S-control by task: -4.4 points (95% -8.6 to -0.2)"),
    ("study2-z1.txt", "MH S-control by task: +16.7 points (95% +11.3 to +22.2)"),
    ("study3-analysis.txt", "alpha 0.0083, margin +-5 points"),
    ("study3-analysis.txt", "I-S CONFIRMATORY: +2.3 points (95% -0.5 to +5.1), CMH p 0.1242"),
    (
        "study3-analysis.txt",
        "K-S CONFIRMATORY: +1.2 points (95% -1.5 to +3.9), CMH p 0.4322, events 121 -> equivalent",
    ),
    (
        "study3-analysis.txt",
        "I-S CONFIRMATORY: -2.8 points (95% -7.4 to +1.9), CMH p 0.2651, events 812 -> inconclusive",
    ),
    (
        "study3-analysis.txt",
        "K-S CONFIRMATORY: -2.5 points (95% -7.1 to +2.1), CMH p 0.3063, events 814 -> inconclusive",
    ),
    (
        "study3-analysis.txt",
        "TD-S secondary: -11.8 points (95% -16.4 to -7.2), CMH p 0.0000, events 743 -> lower",
    ),
    (
        "study3-analysis.txt",
        "TD-S CONFIRMATORY: +2.0 points (95% -1.6 to +5.5), CMH p 0.3077, events 249 -> inconclusive "
        "(rules out below -2.8 and above +6.7 points)",
    ),
    ("study3-analysis.txt", "feature-uri-resolve: TD 247/247, S 209/247, difference +15.4"),
    ("study3-analysis.txt", "feature-toml-config: TD 224/244, S 240/246, difference -5.8"),
    ("study3-analysis.txt", "text-template-engine: TD 149/246, S 159/247, difference -3.8"),
]


@pytest.mark.parametrize(("name", "line"), FROZEN)
def test_frozen_output_has_line(name, line):
    """The frozen analysis output carries the published estimate."""
    assert line in (RUNS / name).read_text()


@pytest.mark.parametrize(
    ("rater", "arm", "agree", "n"),
    [
        ("fable", "all", 126, 160),
        ("grok", "all", 117, 160),
        ("hydrogen", "all", 121, 160),
        ("fable", "I", 27, 40),
        ("fable", "S", 32, 40),
        ("grok", "I", 27, 40),
        ("grok", "S", 30, 40),
        ("hydrogen", "S", 26, 40),
        ("hydrogen", "K", 31, 40),
        ("hydrogen", "I", 30, 40),
    ],
)
def test_labeller_against_model_raters(rater, arm, agree, n):
    """Labeller agreement with each model rater, complete vs not complete."""
    assert RESULTS["labeller_audit"][rater][arm] == {"agree": agree, "n": n}


def test_labeller_gaps():
    """The accuracy gaps the documents quote: 12.5 (Fable, I vs S), 7.5 (Grok), 12.5 (Hydrogen, K vs S)."""
    a = RESULTS["labeller_audit"]
    pct = lambda r, arm: 100 * a[r][arm]["agree"] / a[r][arm]["n"]  # noqa: E731
    assert pct("fable", "S") - pct("fable", "I") == 12.5
    assert pct("grok", "S") - pct("grok", "I") == 7.5
    assert pct("hydrogen", "K") - pct("hydrogen", "S") == 12.5
    assert pct("hydrogen", "I") - pct("hydrogen", "S") == 10.0
    assert [f"{pct(r, 'all'):.1f}" for r in ("grok", "hydrogen", "fable")] == [
        "73.1",
        "75.6",
        "78.8",
    ]


def test_owner_labels_and_pace():
    """The owner's labels: 3 at first, 40 post hoc, 29 of them saved in 72.6 seconds."""
    assert RESULTS["owner_labels"] == {
        "first_attempt": 3,
        "posthoc": 40,
        "posthoc_agree_with_labeller": 29,
    }
    raw = json.loads((AUDIT / "owner40-raw.json").read_text())
    # Times are seconds from the first save; the burst is the 29 ids fixed in owner40-burst29.json.
    burst_ids = json.loads((AUDIT / "owner40-burst29.json").read_text())
    burst = sorted(raw[i]["at"] for i in burst_ids)
    assert len(burst) == 29
    assert round(burst[-1] - burst[0], 1) == 72.6


def test_study3_pins_match():
    """Every file sealed before study 3 ran is shipped byte-identical."""
    pins = [x.split() for x in (ROOT / "prereg/study3/pins.txt").read_text().splitlines()]
    pins = [(h, p) for h, p in (x for x in pins if len(x) == 2) if len(h) == 64]
    assert len(pins) == 114
    for digest, path in pins:
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    assert RESULTS["sealed_third_party_files"] == 70


RESULT_DOCS = [
    ("RESULTS.md", "+3.2"),
    ("RESULTS.md", "In 23 of its 25 events"),
    ("RESULTS-STUDY.md", "+0.3 points (−6.3 to +6.9)"),
    ("RESULTS-STUDY2.md", "−6.6 (−10.6 to −2.6)"),
    ("RESULTS-STUDY2.md", "+27.9 (+22.4 to +33.3)"),
    ("RESULTS-STUDY2.md", "73.5% against 77.5%"),
    ("RESULTS-STUDY2.md", "would not meet the preregistered threshold"),
    ("RESULTS-STUDY3.md", "620/737 (84.1%)"),
    ("RESULTS-STUDY3.md", "608/740 (82.2%)"),
    ("RESULTS-STUDY3.md", "No human validated the labeller"),
    ("RESULTS-STUDY3.md", "29/40 = 72.5%"),
    ("RESULTS-STUDY3.md", "Had it been one, K − S would also be measurement-limited"),
]

# Numbers the reader-facing pages must state exactly as the tests above establish them.
READER_PAGES = {
    "README.md": [
        "6,224 trials",
        "+0.3 points, 95% −6.3 to +6.9",
        "from 16.4% to 9.5%",
        "from 24.1% to 52.7%",
        "73.5% against 77.5%",
        "79.6% against",
        "84.1% against 82.2% (+2.0 points, 95%",
        "a gain above 6.7 points is excluded",
        "56 of 740 trials (7.6%)",
        "P − S +3.2 points, −9.7 to +16.0",
        "−6.6 points (−10.6 to −2.6)",
        "+27.9 (+22.4 to +33.3)",
        "402/505 against 396/493",
        "| 73/740 (9.9%) | 56/740 (7.6%) | +2.3 (−0.5 to +5.1) |",
        "| 396/740 (53.5%) | 416/740 (56.2%) | −2.8 (−7.4 to +1.9) |",
        "| 65/741 (8.8%) | 56/740 (7.6%) | +1.2 (−1.5 to +3.9) |",
        "| 398/741 (53.7%) | 416/740 (56.2%) | −2.5 (−7.1 to +2.1) |",
        "| 620/737 (84.1%) | 608/740 (82.2%) | +2.0 (−1.6 to +5.5) |",
        "371/737 against 248/740",
        "−11.8 points, −16.4 to −7.2",
        "+15.4 on one task, −5.8 and −3.8",
        "507 of",
        "−4.4 and +16.7",
        "73% to 79% of 160",
        "29 of them were saved in 72.6 seconds",
        "differs by 12.5 points between K and S",
        "26.7% and 25.6%",
        "The 114 files",
        "the 70 third-party files",
        "no person validated",
    ],
    "docs/findings.md": [
        "+3.2 points, 95% −9.7 to +16.0",
        "in 23 of its 25 events",
        "26.7% against 25.6%",
        "+1.2 points, −2.7 to +5.0",
        "+0.3 points (−6.3 to +6.9)",
        "+0.6 points (−2.1 to +3.3)",
        "| False completion | 48/505 (9.5%) | 81/493 (16.4%) | −6.6 (−10.6 to −2.6) |",
        "| False non-completion | 266/505 (52.7%) | 119/493 (24.1%) | +27.9 (+22.4 to +33.3) |",
        "402/505 (79.6%) | 396/493 (80.3%)",
        "73.5% against 77.5%",
        "−4.4 (−8.6 to −0.2) and +16.7 (+11.3 to +22.2)",
        "84.1% against 82.2%, +2.0 points (−1.6 to +5.5)",
        "+15.4, −5.8 and",
        "371/737 against 248/740",
        "11.8 points (−16.4 to −7.2",
        "+1.2 points (−1.5 to +3.9)",
        "3 of 160",
        "29 were saved in 72.6 seconds",
        "73% to 79% of the 160",
    ],
}


@pytest.mark.parametrize(
    ("doc", "text"), RESULT_DOCS + [(d, t) for d, ts in READER_PAGES.items() for t in ts]
)
def test_documents_state_the_numbers(doc, text):
    """The results documents and the reader-facing pages state the numbers the tests establish."""
    assert " ".join(text.split()) in " ".join((ROOT / doc).read_text().split())


def _numbers(path):
    """Every number in a page, with decimal and thousands separators removed."""
    found = re.findall(r"\d[\d.,]*\d|\d", (ROOT / path).read_text())
    return Counter(re.sub(r"[.,]", "", n) for n in found)


@pytest.mark.parametrize("lang", ["pt-BR", "es", "it", "he"])
def test_translated_readme_carries_the_same_numbers(lang):
    """A translated README states exactly the numbers of the English one, whatever the separators."""
    assert _numbers(f"README.{lang}.md") == _numbers("README.md")


def test_no_private_key_beyond_the_sealed_trial_key():
    """Only the throwaway agent key sealed with the study 3 template is shipped."""
    skip = {".git", ".venv"}
    small = [
        p
        for p in ROOT.rglob("*")
        if p.is_file() and not skip & set(p.parts) and p.stat().st_size < 10_000
    ]
    found = [
        p.relative_to(ROOT).as_posix() for p in small if b"PRIVATE " + b"KEY" in p.read_bytes()
    ]
    assert found == ["template3/ledger/private/keys/agent"]


@pytest.mark.parametrize("stratum", [(48, 505, 81, 493), (10, 40, 25, 60), (0, 30, 5, 45)])
def test_estimator_reduces_to_the_two_proportion_variance_with_one_stratum(stratum):
    """With a single stratum the Sato (1989) variance is the usual one for two proportions."""
    import math

    a1, n1, a0, n0 = stratum
    rd, lo, hi, _, _ = make_results.mh_rd([stratum])
    p1, p0 = a1 / n1, a0 / n0
    se = math.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    assert rd == pytest.approx(p1 - p0, abs=1e-12)
    assert (hi - lo) / (2 * make_results.Z) == pytest.approx(se, abs=1e-12)


def test_estimator_is_antisymmetric_in_the_arms():
    """Swapping the arms flips the sign of the difference and keeps the interval width."""
    strata = [(48, 171, 30, 156), (20, 163, 25, 166), (9, 171, 26, 171)]
    rd, lo, hi, _, _ = make_results.mh_rd(strata)
    rd2, lo2, hi2, _, _ = make_results.mh_rd([(a0, n0, a1, n1) for a1, n1, a0, n0 in strata])
    assert rd2 == pytest.approx(-rd, abs=1e-12)
    assert hi2 - lo2 == pytest.approx(hi - lo, abs=1e-12)


def test_study2_scored_trials_per_arm():
    """542 scored trials in S and 540 in the control (543 started in each)."""
    import csv

    arms = Counter(r["arm"] for r in csv.DictReader(open(ROOT / "runs" / "study2-scores.csv")))
    assert arms == {"S": 542, "control": 540}
