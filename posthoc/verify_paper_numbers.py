"""Check the numbers printed in the paper against the committed outputs of this package.

The manifest ``posthoc/paper_numbers.json`` lists, for each number group the paper prints, the
script that produces it, the committed output file, a line anchor in that file and the value as
printed. This script

1. checks the SHA-256 of every script and output named in the manifest (``files``);
2. checks every value: the anchor must match the recorded number of lines, the locator text must
   occur in the chosen line, and the number in it must give the printed value under the stated
   rule (``=``: equal after writing the paper's typography plainly, e.g. ``−6.6`` as ``-6.6``,
   ``4,884`` as ``4884``, ``.35`` as ``0.35``; ``r2``/``r3``: rounded; ``lt001``: below .001;
   ``abs``: absolute value; ``pct1``: a proportion printed as a percentage; ``word``: a number
   written as a word; ``frac_*``: one side of a printed fraction; ``contains``: an interval that
   contains the stated values; ``date``; ``text``: the printed text itself; ``str``: the locator
   text only, for a description such as "arm I"). ``derived`` entries
   recompute a sum, difference or ratio of numbers read from the outputs and compare it with the
   printed figure; their formula is written in ``note``;
3. with ``--rerun``, reruns each post hoc script that the manifest names and compares its standard
   output with the committed ``.txt`` byte for byte. Scripts that need the raw archive
   (``EILIKRINEIA_RAW``, default ``raw/``), a clone of the public ledger (``EILIKRINEIA_CHAIN``)
   or external tools are skipped, with the reason printed, when those are absent.

A hash match shows the files are the ones described; the rerun shows that the script prints that
output. Neither shows that the analysis is the right one: that is the paper's argument.
The ``unscripted`` list names the printed figures that no committed script produces, with the
reason.

Usage (from the package root)::

    python posthoc/verify_paper_numbers.py            # hashes and values
    python posthoc/verify_paper_numbers.py --rerun    # also rerun the post hoc scripts
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "posthoc" / "paper_numbers.json"
WORDS = {
    "none": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}
NUM = re.compile(r"[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?(?:/\d+)?")

# Output lines that depend on the interpreter (posthoc/README.md, "Expected"): ignored by --rerun.
VARIES = {"round13_checks": r"^  Python \d+\.\d+\.\d+ .*\n"}

# What each post hoc script needs besides the package (posthoc/README.md, "Inputs and how to run").
NEEDS = {
    "task_heterogeneity": (),
    "ceiling_9_1": (),
    "audit_py38_examples": (),
    "rebuild_vs_flagged": (),
    "power_543": (),
    "b1_split": (),
    "td_secondary": (),
    "claim_counts": (),
    "misc_counts": ("raw",),
    "mde": ("raw",),
    "python38_caveats": ("raw",),
    "cross_trial_sensitivity": ("raw",),
    "cross_trial_contacts": ("raw",),
    "round12_checks": ("raw",),
    "round13_checks": ("raw",),
    "round14_checks": ("raw",),
    "session_env": ("raw",),
    "network_scan": ("raw",),
    "ledger_audit": ("raw", "ssh-keygen"),
    "not_verified": ("raw",),
    "study2_preoutage": ("raw",),
    "gap_checks": ("raw",),
    "ledger_content": ("raw",),
    "ledger_share": ("raw",),
    "sdt_bootstrap": ("raw",),
    "prereg_chronology": ("raw", "chain", "git", "openssl", "ots"),
}


def plain(printed):
    """Write a number as printed in the paper in the plain form the outputs use.

    Parameters
    ----------
    printed : str
        The figure as the paper prints it.

    Returns
    -------
    str
        Minus sign as ``-``, no thousands separators, no ``%``, a leading zero before a bare point.
    """
    s = printed.replace("−", "-").replace("%", "").strip()
    s = re.sub(r"(?<=\d),(?=\d{3})", "", s)
    return re.sub(r"(^|[-+])\.(\d)", r"\g<1>0.\2", s)


def sha256(path):
    """Return the SHA-256 hex digest of a file.

    Parameters
    ----------
    path : pathlib.Path
        File to hash.

    Returns
    -------
    str
        Hex digest.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def anchored_line(text, anchor, nth, count):
    """Return the ``nth`` line containing ``anchor``, after checking how many lines contain it.

    Parameters
    ----------
    text : str
        File content.
    anchor : str
        Substring that identifies the line.
    nth : int
        1-based index among the matching lines.
    count : int
        Number of lines expected to contain the anchor.

    Returns
    -------
    str
        The selected line.
    """
    lines = [x for x in text.splitlines() if anchor in x]
    if len(lines) != count:
        raise AssertionError(
            f"anchor {anchor!r}: {len(lines)} matching lines, manifest says {count}"
        )
    return lines[nth - 1]


def locate(line, loc):
    """Check that the locator text occurs in the line as a whole number and return its last number.

    Parameters
    ----------
    line : str
        The anchored output line.
    loc : str
        Locator text copied from the output.

    Returns
    -------
    str or None
        The last number in the locator, or None when it holds none.
    """
    for m in re.finditer(re.escape(loc), line):
        before = line[m.start() - 1] if m.start() else " "
        after = line[m.end()] if m.end() < len(line) else " "
        if (loc[0] in "+-.0123456789" and (before.isdigit() or before == ".")) or after.isdigit():
            continue
        found = NUM.findall(loc)
        return found[-1] if found else None
    raise AssertionError(f"locator {loc!r} not found in line {line!r}")


def check_value(line, printed, loc, rule):
    """Check one printed value against its output line.

    Parameters
    ----------
    line : str
        The anchored output line.
    printed : str
        The value as the paper prints it.
    loc : str
        Locator text in the output line.
    rule : str
        How the printed value is derived from the number in the locator.
    """
    tok = locate(line, loc)
    want = plain(printed)
    if rule == "=":
        ok = tok == want
    elif rule in ("r0", "r1", "r2", "r3"):
        ok = round(float(tok), int(rule[1])) == float(want)
    elif rule == "lt001":
        ok = printed.strip() == "< .001" and float(tok) < 0.001
    elif rule == "abs":
        ok = abs(float(tok)) == float(want)
    elif rule == "pct1":
        ok = round(100 * float(tok), 1) == float(want)
    elif rule == "word":
        ok = int(float(tok)) == WORDS[printed.split()[0].lower()]
    elif rule in ("frac_num", "frac_den", "frac_both"):
        num, den = tok.split("/")
        ok = {"frac_num": num == want, "frac_den": den == want, "frac_both": num == den == want}[
            rule
        ]
    elif rule.startswith("contains"):
        lo, hi = map(float, re.findall(r"[-+]?\d+(?:\.\d+)?", loc)[:2])
        ok = all(lo <= float(x) <= hi for x in rule.split()[1:])
    elif rule == "date":
        d = datetime.strptime(printed + " 2026", "%d %B %Y").date().isoformat()
        ok = d in loc
    elif rule == "text":
        ok = printed == loc
    elif rule == "str":
        ok = True
    else:
        raise AssertionError(f"unknown rule {rule!r}")
    if not ok:
        raise AssertionError(f"printed {printed!r} does not follow from {loc!r} by rule {rule!r}")


def derived_value(entry, read):
    """Recompute a derived figure from the numbers it is built from.

    Parameters
    ----------
    entry : dict
        A manifest entry of kind ``derived``.
    read : callable
        ``read(path)`` returns the text of a package file.

    Returns
    -------
    str
        The recomputed figure, formatted as the entry says.
    """

    def term(t):
        """Read the number a term of the entry points to.

        Parameters
        ----------
        t : dict
            A term with ``file``, ``anchor``, ``count`` and ``regex`` keys.

        Returns
        -------
        float
            The first capture group of ``regex`` in the anchored line.
        """
        line = anchored_line(read(t["file"]), t["anchor"], t.get("nth", 1), t["count"])
        m = re.search(t["regex"], line)
        if not m:
            raise AssertionError(f"regex {t['regex']!r} not found in {line!r}")
        return float(m.group(1))

    value = sum(t["coef"] * term(t) for t in entry["terms"]) * entry.get("scale", 1)
    if entry.get("divisor"):
        value /= term(entry["divisor"])
    if entry["format"] in ("{}", "{:,}"):
        value = int(round(value))
    return entry["format"].format(value)


def check_entry(entry, read):
    """Check one manifest entry; raise AssertionError on a mismatch.

    Parameters
    ----------
    entry : dict
        A manifest entry (``kind`` ``output`` or ``derived``).
    read : callable
        ``read(path)`` returns the text of a package file.
    """
    if entry["kind"] == "derived":
        got = derived_value(entry, read)
        want = entry["printed"].replace("−", "-")
        want = str(WORDS[want]) if want in WORDS else want
        if got != want:
            raise AssertionError(f"{entry['id']}: recomputed {got!r}, printed {entry['printed']!r}")
        return
    line = anchored_line(
        read(entry["output"]), entry["anchor"], entry.get("nth", 1), entry["count"]
    )
    for v in entry["values"]:
        check_value(line, v["printed"], v["in_output"], v["rule"])


def load():
    """Return the manifest.

    Returns
    -------
    dict
        The parsed ``paper_numbers.json``.
    """
    return json.loads(MANIFEST.read_text())


def reader():
    """Return a cached reader of package files.

    Returns
    -------
    callable
        ``read(path)`` -> text of ``ROOT / path``.
    """
    cache = {}

    def read(path):
        """Return the text of a package file, reading it once.

        Parameters
        ----------
        path : str
            The path relative to the package root.

        Returns
        -------
        str
            The file text.
        """
        if path not in cache:
            cache[path] = (ROOT / path).read_text()
        return cache[path]

    return read


def missing_inputs(name):
    """Name the inputs a post hoc script needs that are absent here.

    Parameters
    ----------
    name : str
        Script name without ``.py``.

    Returns
    -------
    list of str
        Absent inputs (empty when the script can run).
    """
    raw = Path(os.environ.get("EILIKRINEIA_RAW", ROOT / "raw"))
    chain = Path(os.environ.get("EILIKRINEIA_CHAIN", ROOT.parent / "eilikrineia"))
    out = []
    for need in NEEDS[name]:
        if need == "raw" and not (raw / "study3").is_dir():
            out.append(f"raw archive ({raw})")
        elif need == "chain" and not (chain / ".git").exists():
            out.append(f"ledger clone ({chain})")
        elif need not in ("raw", "chain") and not shutil.which(need):
            out.append(need)
    return out


def rerun(name):
    """Rerun one post hoc script and compare its output with the committed ``.txt``.

    Parameters
    ----------
    name : str
        Script name without ``.py``.

    Returns
    -------
    str
        ``same``, ``DIFFERENT`` or ``skipped (...)``.
    """
    absent = missing_inputs(name)
    if absent:
        return "skipped (needs " + ", ".join(absent) + ")"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    run = subprocess.run(
        [sys.executable, f"posthoc/{name}.py"], cwd=ROOT, env=env, capture_output=True, text=True
    )
    frozen = (ROOT / "posthoc" / f"{name}.txt").read_text()
    new = run.stdout
    # the committed output was printed by Python 3.11; drop the line that names it
    if name in VARIES:
        new, frozen = (re.sub(VARIES[name], "", x, flags=re.M) for x in (new, frozen))
    return "same" if run.returncode == 0 and new == frozen else "DIFFERENT"


def main():
    """Run the checks and return the exit code.

    Returns
    -------
    int
        0 when every check passes, 1 otherwise.
    """
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--rerun", action="store_true", help="also rerun the post hoc scripts")
    args = ap.parse_args()
    man, read, bad = load(), reader(), 0
    for path, digest in sorted(man["files"].items()):
        if sha256(ROOT / path) != digest:
            print(f"HASH MISMATCH {path}")
            bad += 1
    print(f"hashes: {len(man['files']) - bad} of {len(man['files'])} files match")
    fails = 0
    for e in man["numbers"]:
        try:
            check_entry(e, read)
        except AssertionError as err:
            print(f"VALUE MISMATCH {e['id']}: {err}")
            fails += 1
    nvals = sum(len(e.get("values", [])) or 1 for e in man["numbers"])
    print(
        f"values: {len(man['numbers']) - fails} of {len(man['numbers'])} entries "
        f"({nvals} printed values) "
        f"match the committed outputs; {len(man['unscripted'])} number groups have no script "
        f"(listed in "
        f"the manifest)"
    )
    bad += fails
    if args.rerun:
        for name in man["rerun"]:
            verdict = rerun(name)
            print(f"  {verdict}: posthoc/{name}.py -> posthoc/{name}.txt")
            bad += verdict == "DIFFERENT"
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
