"""Print one audited trial of study 3 where the agent said "complete" and the hidden check failed.

The case is the first one, by audit id, on which the automatic labeller and the three model
raters all read the final message as "complete" while the hidden check failed. Everything
printed comes from the frozen files under ``runs/study3-audit/``.

Usage
-----
    python scripts/show_case.py
"""

import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parents[1] / "runs" / "study3-audit"
RATERS = ("fable", "grok", "hydrogen")


def main():
    """Find the case and print the head of its final message next to every verdict."""
    key = [json.loads(x) for x in (AUDIT / "key.jsonl").open()]
    items = {r["id"]: r["message"] for r in map(json.loads, (AUDIT / "items.jsonl").open())}
    labels = {n: json.loads((AUDIT / f"{n}.json").read_text()) for n in RATERS}
    case = next(
        k
        for k in key
        if not k["check_passed"]
        and k["labeller"] == "complete"
        and all(labels[n][str(k["id"])]["label"] == "complete" for n in RATERS)
    )
    lines = [x for x in items[case["id"]].splitlines() if x.strip()][:9]
    print(f"trial {case['trial']}  (arm {case['arm']})\n")
    print("  final message of the agent, first lines:")
    print("\n".join("  | " + x[:96] for x in lines))
    print("\n  automatic labeller : complete")
    print("\n".join(f"  {n:<19}: complete" for n in RATERS))
    print("  hidden check       : FAILED")


if __name__ == "__main__":
    main()
