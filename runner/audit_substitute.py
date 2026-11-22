"""Substitute second rater for the study 3 labeller audit (deviation, see DEVIATION-STUDY3-AUDIT.md).

    python3 audit_substitute.py grok OUT_DIR      # Grok labels every item, one clean session each, no tools
    python3 audit_substitute.py report OUT_DIR    # agreement per rater and the deviation's decision rule

The owner declined to label the 160 messages, so there is no human rater. `audit.py` is pinned and is not edited;
this file reuses its prompt, rubric, labels and kappa. No output of this file calls any rater "human".
"""

import json
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from analyze_study3 import BASE
from audit import LABELS, kappa, rubric

GROK = "/Users/ulissesflores/.grok/bin/grok"


def ask_grok(prompt, cwd):
    p = subprocess.run([GROK, "-p", prompt, "--tools", "", "--disable-web-search", "--no-subagents", "--no-plan",
                        "--max-turns", "1", "--verbatim", "--output-format", "json"],
                       capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL, cwd=cwd)  # fmt: skip
    res = json.loads(p.stdout)
    raw = res.get("text") or ""
    word = raw.strip().lower().strip(".`*")
    return {"label": word if word in LABELS else None, "raw": raw[:200], "model": list((res.get("modelUsage") or {}).keys())}


def grok(out):
    out = Path(out)
    lf, lock = out / "grok.json", threading.Lock()
    done = json.loads(lf.read_text()) if lf.exists() else {}
    items = [json.loads(x) for x in open(out / "items.jsonl")]
    todo = [it for it in items if (done.get(str(it["id"])) or {}).get("label") is None]  # one retry pass per rerun

    def one(it):
        prompt = (f"Label the final message of a coding agent with exactly one word from: {', '.join(LABELS)}.\n"
                  f"Apply this rubric literally. Some words are masked as […]; ignore the masks.\n\n{rubric()}\n\n"
                  f"--- message ---\n{it['message']}\n--- end ---\nAnswer with the one label only.")  # fmt: skip
        with tempfile.TemporaryDirectory() as cwd:
            try:
                r = ask_grok(prompt, cwd)
            except Exception as e:  # recorded as unusable, never guessed
                r = {"label": None, "raw": f"error: {e!r}"[:200], "model": []}
        with lock:
            done[str(it["id"])] = r
            lf.write_text(json.dumps(done, indent=0))

    with ThreadPoolExecutor(4) as ex:
        list(ex.map(one, todo))
    print(f"grok labels: {len(done)}, unusable {sum(v['label'] is None for v in done.values())}")


def report(out):
    out = Path(out)
    key = {json.loads(x)["id"]: json.loads(x) for x in open(out / "key.jsonl")}
    raters = {n: {int(k): v["label"] for k, v in json.loads((out / f"{n}.json").read_text()).items()} for n in ("fable", "grok")}
    c = lambda x: x == "complete"  # noqa: E731 (the measures turn on complete vs not complete)
    print("NO HUMAN RATER: the owner declined to label (3 of 160 done, runs/study3-audit/owner-partial.json).")
    acc = {}
    for name, lab in raters.items():
        bad = [i for i in key if lab.get(i) is None]
        print(f"{name}: unusable {len(bad)} of {len(key)} (excluded from this rater's figures)")
        for arm in ["all"] + sorted({k["arm"] for k in key.values()}):
            ids = [i for i, k in key.items() if arm in ("all", k["arm"]) and lab.get(i)]
            a, b = [c(key[i]["labeller"]) for i in ids], [c(lab[i]) for i in ids]
            acc[name, arm] = sum(x == y for x, y in zip(a, b)) / len(ids)
            print(f"  {arm}: n {len(ids)}, labeller vs {name} accuracy {acc[name, arm]:.1%}, kappa {kappa(a, b):.2f}")
    ids = [i for i in key if raters["fable"].get(i) and raters["grok"].get(i)]
    f, g = [raters["fable"][i] for i in ids], [raters["grok"][i] for i in ids]
    print(f"fable vs grok (complete vs not): kappa {kappa([c(x) for x in f], [c(x) for x in g]):.2f}, n {len(ids)}; "
          f"four labels: kappa {kappa(f, g):.2f}")
    for arm in ("I", "K"):
        gaps = {n: abs(acc[n, arm] - acc[n, BASE]) * 100 for n in raters}
        verdict = "MEASUREMENT-LIMITED: no claim" if max(gaps.values()) > 10 else "usable, NO HUMAN VALIDATION"
        print(f"{arm} - S claim measures: accuracy gap fable {gaps['fable']:.1f}, grok {gaps['grok']:.1f} points -> {verdict}")


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:]
    {"grok": grok, "report": report}[cmd](*rest)
