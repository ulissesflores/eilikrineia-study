# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Carlos Ulisses Flores (Codex Hash Ltda.)
"""Lock every number the paper prints to the committed output it comes from.

This file sits in posthoc/ and not in tests/ because tests/ is inside the sealed chain_hash of
version 1.0.0 and adding a file there would change the seal.

What runs where:

- hashes and printed values: always (they read only committed files);
- reruns of the post hoc scripts that need only the package: always;
- reruns that need the raw archive (EILIKRINEIA_RAW, default raw/), the ledger clone
  (EILIKRINEIA_CHAIN) or external tools: skipped when those are absent, with the reason;
- the check that each quoted context still occurs in the paper's text: only when EILIKRINEIA_PAPER
  points to the paper's Markdown source (skipped otherwise).

Inputs
------
- posthoc/paper_numbers.json, the committed outputs it names and posthoc/SHA256SUMS; the
  verification functions of posthoc/verify_paper_numbers.py.
- Optional: the raw archive (EILIKRINEIA_RAW), the ledger clone (EILIKRINEIA_CHAIN) and the paper's
  Markdown source (EILIKRINEIA_PAPER).

Outputs
-------
- A pytest report: one test per file hash, per printed number and per rerun, plus the coverage and
  manifest checks; a skipped test states the missing input.

Usage
-----
    python -m pytest -q posthoc/test_paper_numbers.py

Status
------
Test of the paper's printed numbers (draft 0.1 of 2026-11-24); it is a check on the committed
outputs, not an analysis, and carries no preregistration.

Author
------
Carlos Ulisses Flores, ORCID https://orcid.org/0000-0002-6034-7765

Repository
----------
https://github.com/ulissesflores/eilikrineia-study
"""

import copy
import json
import os
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_paper_numbers as V  # noqa: E402

MAN = V.load()
READ = V.reader()


@pytest.mark.parametrize("path", sorted(MAN["files"]))
def test_file_hash(path):
    """Each script and output named in the manifest has the recorded SHA-256.

    Parameters
    ----------
    path : str
        Repository-relative path of a file listed in the manifest.
    """
    assert V.sha256(V.ROOT / path) == MAN["files"][path]


@pytest.mark.parametrize("entry", MAN["numbers"], ids=[e["id"] for e in MAN["numbers"]])
def test_printed_number(entry):
    """Each printed value follows from its committed output line.

    Parameters
    ----------
    entry : dict
        One number entry of the manifest.
    """
    V.check_entry(entry, READ)


def test_every_source_is_hashed():
    """Every output, script and derived-term file the entries use is in the hashed file list."""
    used = set()
    for e in MAN["numbers"]:
        if e["kind"] == "output":
            used.add(e["output"])
            if e["script"]:
                used.add(e["script"])
        else:
            used.update(t["file"] for t in e["terms"])
            used.update(e["scripts"])
    assert used <= set(MAN["files"])


def test_checker_rejects_wrong_values():
    """Check that the checker fails when a printed value or a derived figure is changed.

    It is not a tautology.
    """
    out = copy.deepcopy(next(e for e in MAN["numbers"] if e["id"] == "t3.fc"))
    out["values"][0]["printed"] = "−6.7"
    with pytest.raises(AssertionError):
        V.check_entry(out, READ)
    out = copy.deepcopy(next(e for e in MAN["numbers"] if e["id"] == "t3.fc"))
    out["values"][0]["in_output"] = "-6.7"
    with pytest.raises(AssertionError):
        V.check_entry(out, READ)
    der = copy.deepcopy(next(e for e in MAN["numbers"] if e["id"] == "abs.kept"))
    der["printed"] = "6,125"
    with pytest.raises(AssertionError):
        V.check_entry(der, READ)


@pytest.mark.parametrize("name", MAN["rerun"])
def test_rerun_post_hoc_script(name):
    """Check that rerunning a post hoc script prints its committed output.

    Skipped if its inputs are absent.

    Parameters
    ----------
    name : str
        Script name without ``.py``.
    """
    absent = V.missing_inputs(name)
    if absent:
        pytest.skip("needs " + ", ".join(absent))
    assert V.rerun(name) == "same"


@pytest.mark.skipif(not os.environ.get("EILIKRINEIA_PAPER"), reason="EILIKRINEIA_PAPER not set")
def test_contexts_occur_in_paper():
    """Each quoted context occurs in the paper and contains the printed values."""
    paper = " ".join(Path(os.environ["EILIKRINEIA_PAPER"]).read_text().split())
    for e in MAN["numbers"]:
        assert " ".join(e["context"].split()) in paper, e["id"]
        if e["kind"] == "output":
            printed = [v["printed"] for v in e["values"] if v["rule"] != "str"]
        else:
            printed = [e["printed"]]
        for p in printed:
            assert p in e["context"] or p in V.WORDS, (e["id"], p)


def test_manifest_has_no_private_paths():
    """The public manifest names no home folder or private project path."""
    text = json.dumps(MAN)
    for needle in ("/Users/", "/home/", "private/"):
        assert needle not in text, needle
