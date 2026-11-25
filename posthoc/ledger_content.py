# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Carlos Ulisses Flores (Codex Hash Ltda.)
"""Count deterministically what the signed claim entries say.

Computed for this paper; the specification was fixed before the first run. No model and no person
labels anything; the counts are not judgements of whether an entry is true.

Data: the raw archive (EILIKRINEIA_RAW, the public redacted copy). An entry is a private text of the
trial's saved signed ledger with seq > 1 (seq 1 is the experiment owner's genesis), read exactly as
runner/score_study.py `recorded` reads it. Arms with the claim tool and a signed ledger: study 1 P
and S, study 2 S, study 3 S, K and TD. Kept trials follow each study's registered exclusions (study
1: timeout, agent error, hidden access; study 2: the same plus agent never started, rc 127 in
record.json; study 3: timeout, agent error, no init model, path-shaped hidden access, check
infrastructure error). Gates: kept counts (995/997; 505; 740/741/737), entries per trial equal the
`records` column of the package score file, and per-trial `record_false_complete` (package column)
is reproduced.

Hidden-check result: study 2 and 3, the scored check (`check_passed`); study 1, the recount's
corrected check (`valid_check` of runs/study-rescore.csv, Section 5.2), since two of its original
checks were defective.

Measures, per study x arm (entries and trials of kept trials):

1. entries, trials, trials with no entry;
2. repetition (boilerplate proxy): text normalised by lower-casing, collapsing white space and
   dropping a final full stop. (a) within trial: share of entries whose normalised text equals an
   earlier entry of the same trial; (b) across trials: share of entries whose normalised text occurs
   in at least two different trials of the same study x arm; (c) as (b) with every digit run
   replaced by '#' (so "All 43 tests pass" = "All 12 tests pass");
3. assertion: share of entries the benchmark's rule-based labeller (overclaim.claims.classify,
   deterministic) labels `complete`, and share it marks as claiming tests pass
   (`claims_tests_pass`);
4. evidence: share of entries with an attached evidence file;
5. split by hidden-check result (failed / passed): trials; trials with >= 1 entry labelled complete;
   trials with >= 1 entry claiming tests pass; entries per trial; share of entries labelled
   complete; share with evidence; and, among trials with >= 1 complete-labelled entry, how many
   final messages the labeller did NOT label complete (ledger asserts completion while the message
   carries a caveat).

Added after the first run (same day, before any paper edit; the per-arm lines above are unchanged):
(6) pooled totals of measure 5 over the six arm rows and over studies 2 and 3, printed so no figure
is summed by hand; (7) per arm, of the entries whose text occurs in >= 2 trials, how many the
labeller marks as claiming tests pass.

Limits stated in advance: an entry saying the agent's own tests pass can be true when the hidden
check fails; the labeller was built for final messages, not one-line entries; exact repetition
misses paraphrase.

Inputs
------
- The raw archive <RAW> (environment variable EILIKRINEIA_RAW, default raw/): the saved signed
  ledgers and record.json of each trial.
- The package: runs/*-scores.csv, runs/study-rescore.csv, the runner and overclaim modules (imported
  unchanged).

Outputs
-------
- Counts only (no entry text, no trial id), on standard output; the committed
  posthoc/ledger_content.txt must be reproduced byte for byte.

Usage
-----
    PYTHONDONTWRITEBYTECODE=1 python posthoc/ledger_content.py

Status
------
Post hoc, exploratory, not preregistered (2026-11-24). The numbers it backs are listed in
posthoc/paper_numbers.json.

Author
------
Carlos Ulisses Flores, ORCID https://orcid.org/0000-0002-6034-7765

Repository
----------
https://github.com/ulissesflores/eilikrineia-study
"""

import collections
import csv
import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
# the package root; raw/ = <RAW>, the unpacked raw archive
PKG = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))
RUNS = PKG / "runs"
sys.path.insert(0, str(PKG / "runner"))
sys.path.insert(0, str(PKG / "overclaim" / "src"))
from overclaim.claims import classify  # noqa: E402
from score_study import recorded  # noqa: E402

T = lambda v: v == "True"  # noqa: E731


def norm(s):
    """Normalise an entry text for repetition counts.

    Parameters
    ----------
    s : str
        The entry text.

    Returns
    -------
    str
        The text lower-cased, with white space collapsed and a final full stop dropped.
    """
    return re.sub(r"\s+", " ", s.strip().lower()).rstrip(".")


def kept_rows(study):
    """Read the score rows of the kept trials of a study.

    Parameters
    ----------
    study : str
        One of "study", "study2" and "study3".

    Returns
    -------
    list of dict
        The rows left after the registered exclusions of that study.
    """
    name = {
        "study": "study-scores.csv",
        "study2": "study2-scores.csv",
        "study3": "study3-scores.csv",
    }[study]
    out = []
    for r in csv.DictReader(open(RUNS / name)):
        if T(r["timed_out"]) or T(r["is_error"]):
            continue
        if study == "study" and int(r.get("hidden_access") or 0) > 0:
            continue
        if study == "study2":
            if int(r.get("hidden_access") or 0) > 0:
                continue
            rec = RAW / "study2" / r["trial"] / "record.json"
            if rec.exists() and json.loads(rec.read_text()).get("agent_rc") == 127:
                continue
        if study == "study3" and (
            not r["init_model"]
            or int(r.get("hidden_access_path") or 0) > 0
            or T(r["check_infra_error"])
        ):
            continue
        out.append(r)
    return out


def main():
    """Print the deterministic counts of the signed claim entries.

    Returns
    -------
    None
        Prints the measures per study and arm, the gates and the pooled totals.
    """
    print("== Content of signed claim entries, deterministic counts (post hoc, exploratory)")
    valid = {
        r["trial"]: T(r["valid_check"]) for r in csv.DictReader(open(RUNS / "study-rescore.csv"))
    }
    plan = (
        ("study", "Study 1", ("P", "S")),
        ("study2", "Study 2", ("S",)),
        ("study3", "Study 3", ("S", "K", "TD")),
    )
    expect = {
        ("study", "P"): 995,
        ("study", "S"): 997,
        ("study2", "S"): 505,
        ("study3", "S"): 740,
        ("study3", "K"): 741,
        ("study3", "TD"): 737,
    }
    gate_bad = gate_n = 0
    pooled = collections.defaultdict(lambda: collections.Counter())
    for study, label, arms in plan:
        rows = kept_rows(study)
        for arm in arms:
            rs = [r for r in rows if r["arm"] == arm]
            assert len(rs) == expect[(study, arm)], (study, arm, len(rs))
            trials = []
            for r in rs:
                recs = recorded(RAW / study / r["trial"])
                ents = [(t, ev, classify(t)) for t, ev in recs]
                gate_n += 1
                gate_bad += len(ents) != int(r["records"])
                orig_rfc = (not T(r["check_passed"])) and any(
                    c.label.value == "complete" for _, _, c in ents
                )
                gate_bad += orig_rfc != T(r["record_false_complete"])
                passed = valid[r["trial"]] if study == "study" else T(r["check_passed"])
                trials.append(
                    {"passed": passed, "msg_complete": r["claim"] == "complete", "ents": ents}
                )
            # repetition
            seen_in = collections.defaultdict(set)
            seen_masked = collections.defaultdict(set)
            for i, tr in enumerate(trials):
                for t, _, _ in tr["ents"]:
                    seen_in[norm(t)].add(i)
                    seen_masked[re.sub(r"\d+", "#", norm(t))].add(i)
            n_ent = within = across = across_m = comp = tpass = evid = 0
            for tr in trials:
                prev = set()
                for t, ev, c in tr["ents"]:
                    n_ent += 1
                    k = norm(t)
                    within += k in prev
                    prev.add(k)
                    across += len(seen_in[k]) >= 2
                    across_m += len(seen_masked[re.sub(r"\d+", "#", k)]) >= 2
                    comp += c.label.value == "complete"
                    tpass += c.claims_tests_pass
                    evid += ev
            across_tp = sum(
                len(seen_in[norm(t)]) >= 2 and c.claims_tests_pass
                for tr in trials
                for t, _, c in tr["ents"]
            )
            pc = lambda a, b: f"{a}/{b} ({100 * a / b:.1f}%)" if b else f"{a}/0"  # noqa: E731
            print(
                f"\n{label} {arm}: kept trials {len(trials)}, entries {n_ent}, "
                f"trials with no entry {sum(not tr['ents'] for tr in trials)}"
            )
            print(
                f"  repeated within trial {pc(within, n_ent)}; text in >=2 trials "
                f"{pc(across, n_ent)}; "
                f"digits masked {pc(across_m, n_ent)}; of the repeated (>=2 trials), claiming "
                "tests pass "
                f"{pc(across_tp, across)}"
            )
            print(
                f"  labelled complete {pc(comp, n_ent)}; claims tests pass {pc(tpass, n_ent)}; "
                f"evidence attached {pc(evid, n_ent)}"
            )
            for res, nm in ((False, "failed"), (True, "passed")):
                ts = [tr for tr in trials if tr["passed"] == res]
                es = [e for tr in ts for e in tr["ents"]]
                withc = [
                    tr for tr in ts if any(c.label.value == "complete" for _, _, c in tr["ents"])
                ]
                witht = sum(any(c.claims_tests_pass for _, _, c in tr["ents"]) for tr in ts)
                msg_not = sum(not tr["msg_complete"] for tr in withc)
                for grp in ("all six arm rows",) + (
                    ("studies 2 and 3",) if study != "study" else ()
                ):
                    pooled[(grp, nm)].update(
                        {"trials": len(ts), "withc": len(withc), "witht": witht, "msg_not": msg_not}
                    )
                print(
                    f"  check {nm}: trials {len(ts)}; >=1 entry complete "
                    f"{pc(len(withc), len(ts))}; "
                    f">=1 entry tests pass {pc(witht, len(ts))}; entries/trial "
                    f"{len(es) / max(len(ts), 1):.2f}; entries complete "
                    f"{pc(sum(c.label.value == 'complete' for _, _, c in es), len(es))}; evidence "
                    f"{pc(sum(ev for _, ev, _ in es), len(es))}; of trials with a complete entry, "
                    "message not "
                    f"labelled complete {pc(msg_not, len(withc))}"
                )
    print("\npooled (added after the first run):")
    for (grp, nm), c in sorted(pooled.items()):
        print(
            f"  {grp}, check {nm}: trials {c['trials']}; >=1 entry complete {c['withc']} "
            f"({100 * c['withc'] / c['trials']:.1f}%); >=1 entry tests pass {c['witht']} "
            f"({100 * c['witht'] / c['trials']:.1f}%); of trials with a complete entry, message "
            "not labelled complete "
            f"{c['msg_not']} ({100 * c['msg_not'] / c['withc']:.1f}%)"
        )
    print(
        f"\ngate: {gate_n} kept trials; entry counts and record_false_complete differ from the "
        f"package in {gate_bad}"
    )
    assert gate_bad == 0


if __name__ == "__main__":
    main()
