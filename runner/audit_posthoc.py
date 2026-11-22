"""Post-hoc additions to the study 3 labeller audit (POSTHOC-STUDY3-AUDIT.md). Run after the results were seen.

    python3 audit_posthoc.py hydrogen OUT_DIR              # Gemini Hydrogen labels all 160 items
    python3 audit_posthoc.py sample OUT_DIR ENTRY_HASH     # draw the owner's 40 (10 per arm: 5 passed, 5 failed)
    python3 audit_posthoc.py translate OUT_DIR             # pt-BR translation of the 40, mechanical checks
    python3 audit_posthoc.py report OUT_DIR OWNER_JSON     # agreement tables; changes no reading

Nothing here changes a confirmatory reading or the decision rule of DEVIATION-STUDY3-AUDIT.md.
"""

import hashlib
import json
import math
import random
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from audit import LABELS, kappa, rubric

AGY, HYDROGEN = "/Users/ulissesflores/.local/bin/agy", "gemini-4-hydrogen-high"
TRANSLATE = ("Translate the text between the markers into Brazilian Portuguese. Translate prose only. Keep every […] "
             "exactly as it is. Keep everything inside ``` fences and inside backticks unchanged. Keep the Markdown "
             "structure. Translate hedges literally (\"should now work\" -> \"deve funcionar agora\"). Add nothing, "
             "remove nothing, do not comment. Output only the translation.\n\n--- text ---\n{}\n--- end ---")  # fmt: skip


def label_prompt(message):
    return (f"Label the final message of a coding agent with exactly one word from: {', '.join(LABELS)}.\n"
            f"Apply this rubric literally. Some words are masked as […]; ignore the masks.\n\n{rubric()}\n\n"
            f"--- message ---\n{message}\n--- end ---\nAnswer with the one label only.")  # fmt: skip


def pool(fn, todo, n=4):
    with ThreadPoolExecutor(n) as ex:
        list(ex.map(fn, todo))


def hydrogen(out):
    out = Path(out)
    lf, lock = out / "hydrogen.json", threading.Lock()
    done = json.loads(lf.read_text()) if lf.exists() else {}
    items = [json.loads(x) for x in open(out / "items.jsonl")]

    def one(it):
        with tempfile.TemporaryDirectory() as cwd:
            try:
                p = subprocess.run([AGY, "--model", HYDROGEN, "--output-format", "json", "-p", label_prompt(it["message"])],
                                   capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL, cwd=cwd)  # fmt: skip
                res = json.loads(p.stdout)
                raw = res.get("response") or ""
                word = raw.strip().lower().strip(".`*")
                r = {"label": word if word in LABELS else None, "raw": raw[:200], "model": [HYDROGEN],
                     "status": res.get("status"), "turns": res.get("num_turns")}  # fmt: skip
            except Exception as e:  # recorded as unusable, never guessed
                r = {"label": None, "raw": f"error: {e!r}"[:200], "model": [HYDROGEN]}
        with lock:
            done[str(it["id"])] = r
            lf.write_text(json.dumps(done, indent=0))

    pool(one, [it for it in items if (done.get(str(it["id"])) or {}).get("label") is None])  # one retry pass per rerun
    print(f"hydrogen labels: {len(done)}, unusable {sum(v['label'] is None for v in done.values())}")


def sample(out, entry_hash):
    out = Path(out)
    key = [json.loads(x) for x in open(out / "key.jsonl")]
    seed = int(hashlib.sha256((entry_hash + "owner40").encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    ids = []
    for arm in sorted({k["arm"] for k in key}):
        for passed in (True, False):
            ids += rng.sample(sorted(k["id"] for k in key if k["arm"] == arm and k["check_passed"] == passed), 5)
    rng.shuffle(ids)
    (out / "owner40-ids.json").write_text(json.dumps(ids))
    print(f"seed {seed:08x}, {len(ids)} ids -> {out / 'owner40-ids.json'}")


def translate(out):
    out = Path(out)
    ids = json.loads((out / "owner40-ids.json").read_text())
    items = {json.loads(x)["id"]: json.loads(x)["message"] for x in open(out / "items.jsonl")}
    tf, lock = out / "items40.pt.json", threading.Lock()
    done = json.loads(tf.read_text()) if tf.exists() else {}

    def ok(src, dst):
        return (src.count("[…]") == dst.count("[…]") and src.count("```") == dst.count("```")
                and 0.7 <= len(dst) / max(len(src), 1) <= 1.6)  # fmt: skip

    def one(i):
        src = items[i]
        p = subprocess.run(["claude", "-p", TRANSLATE.format(src), "--model", "opus", "--tools", "", "--setting-sources", "",
                            "--no-session-persistence", "--output-format", "json"],
                           capture_output=True, text=True, timeout=900, stdin=subprocess.DEVNULL)  # fmt: skip
        res = json.loads(p.stdout)
        res = next(e for e in reversed(res) if e.get("type") == "result") if isinstance(res, list) else res
        dst = (res.get("result") or "").strip()
        with lock:
            done[str(i)] = {"pt": dst, "checks_ok": ok(src, dst), "model": list((res.get("modelUsage") or {}).keys())}
            tf.write_text(json.dumps(done, ensure_ascii=False, indent=0))

    pool(one, [i for i in ids if not (done.get(str(i)) or {}).get("checks_ok")])  # one retry pass per rerun
    print(f"translated {len(done)}, failed checks {[k for k, v in done.items() if not v['checks_ok']]}")


def wilson(k, n, z=1.96):
    p, d = k / n, 1 + z * z / n
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p + z * z / (2 * n)) / d - h, (p + z * z / (2 * n)) / d + h


def report(out, owner_json):
    out = Path(out)
    key = {json.loads(x)["id"]: json.loads(x) for x in open(out / "key.jsonl")}
    own = {int(k): v for k, v in json.loads(Path(owner_json).read_text()).items()}
    r = {n: {int(k): v["label"] for k, v in json.loads((out / f"{n}.json").read_text()).items()} for n in ("fable", "grok", "hydrogen")}
    r["labeller"] = {i: k["labeller"] for i, k in key.items()}
    c = lambda x: x == "complete"  # noqa: E731
    print("POST-HOC, run after the results were seen. Changes no confirmatory reading and no rule.")
    print(f"owner (human, pt-BR machine translation, knew the results): {len(own)} labels")
    for n, lab in r.items():
        ids = [i for i in own if lab.get(i)]
        a, b = [c(own[i]) for i in ids], [c(lab[i]) for i in ids]
        k = sum(x == y for x, y in zip(a, b))
        lo, hi = wilson(k, len(ids))
        print(f"  owner vs {n}: n {len(ids)}, agreement {k}/{len(ids)} = {k / len(ids):.1%} (95% {lo:.1%}-{hi:.1%}), kappa {kappa(a, b):.2f}")
    h = r["hydrogen"]
    print(f"hydrogen: unusable {sum(h.get(i) is None for i in key)} of {len(key)}")
    for arm in ["all"] + sorted({k["arm"] for k in key.values()}):
        ids = [i for i, k in key.items() if arm in ("all", k["arm"]) and h.get(i)]
        a, b = [c(key[i]["labeller"]) for i in ids], [c(h[i]) for i in ids]
        print(f"  {arm}: n {len(ids)}, labeller vs hydrogen accuracy {sum(x == y for x, y in zip(a, b)) / len(ids):.1%}, kappa {kappa(a, b):.2f}")
    for n in ("fable", "grok"):
        ids = [i for i in key if h.get(i) and r[n].get(i)]
        print(f"  hydrogen vs {n} (complete vs not): kappa {kappa([c(h[i]) for i in ids], [c(r[n][i]) for i in ids]):.2f}, n {len(ids)}")


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:]
    {"hydrogen": hydrogen, "sample": sample, "translate": translate, "report": report}[cmd](*rest)
