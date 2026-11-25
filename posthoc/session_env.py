"""Round 13: what the Claude Code session of each trial loaded.

EXPLORATORY, POST HOC (2026-11-24). Not preregistered.

Reads each trial's saved stream (agent.stdout in the raw archive) up to its first assistant event:
the system events
before it (hooks started, hook responses, which are only COUNTED, never printed) and the init event,
from which only
selected fields are used (tools, MCP servers, slash commands, skills, plugin names, permission mode,
Claude Code
version, model). Configuration labels, arm labels and Claude Code versions are checked against
allowlists (the versions against the exact values in the archive); anything else prints as `other`.
No trial ids
and no raw excerpts are printed. The invocation itself is in runner/run_trial.py (the one command
line used by every
study).
Also: the context size of the first model request of each session (input + cache-creation +
cache-read tokens of the
first assistant event), by study and arm. A first assistant event with zero tokens is a synthetic
error event (a
connection error written by the client, not a model request): it is counted separately and left out
of the token
summary. This script makes no claim about the size of instructions that only the host sessions
loaded.

Run from the package root: PYTHONDONTWRITEBYTECODE=1 python posthoc/session_env.py  (needs <RAW>)
"""

import collections
import json
import os
import statistics
from pathlib import Path

ALLOWED = {
    "hook": {"SessionStart:startup"},
    "tool": {"Bash", "Edit", "Glob", "Grep", "Read", "Write"},
    "plugin": {
        "cc-plugin-agents-md",
        "cc-plugin-telemetry",
        "cc-plugin-privacy",
        "cc-plugin-plugin-authoring",
    },
    "mode": {"bypassPermissions"},
    "model": {"claude-haiku-5-5"},
}


def lab(kind, v):
    """Return v if it is an allowlisted label of this kind, else 'other'."""
    return v if v in ALLOWED[kind] else "other"


ARMS = {"H", "S", "P", "control", "I", "K", "TD"}  # the study arms
VERSIONS = {"2.1.318", "2.1.319"}  # the exact values in the init events of the archive


def ver(v):
    """Return a version string only if it is one of the exact values in VERSIONS, else 'other'."""
    return v if v in VERSIONS else "other"


# the package root; raw/ = <RAW>, the unpacked raw archive
PKG = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("EILIKRINEIA_RAW", PKG / "raw"))

for study in ("pilot", "study", "study2", "study3"):
    n = no_init = 0
    hooks, nonempty, inits = collections.Counter(), 0, collections.Counter()
    synthetic = collections.Counter()
    first = collections.defaultdict(list)
    for d in sorted(p for p in (RAW / study).iterdir() if p.is_dir()):
        f = d / "agent.stdout"
        if not f.exists():
            continue
        n += 1
        init = None
        for line in f.read_text(errors="replace").splitlines():
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("type") == "assistant":
                u = e["message"].get("usage", {})
                arm = d.name.split("-")[1] if len(d.name.split("-")) > 1 else "other"
                arm = arm if arm in ARMS else "other"
                tok = sum(
                    u.get(k, 0)
                    for k in (
                        "input_tokens",
                        "cache_creation_input_tokens",
                        "cache_read_input_tokens",
                    )
                )
                if tok == 0:
                    synthetic[arm] += 1
                else:
                    first[arm].append(tok)
                break
            if e.get("type") != "system":
                continue
            if e.get("subtype") == "hook_started":
                hooks[lab("hook", e.get("hook_name"))] += 1
            if e.get("subtype") == "hook_response" and (e.get("output") or "").strip() not in (
                "",
                "{}",
            ):
                nonempty += 1
            if e.get("subtype") == "init":
                init = e
        if init is None:
            no_init += 1
            continue
        key = (
            tuple(lab("tool", t) for t in init.get("tools", [])),
            len(init.get("mcp_servers", [])),
            len(init.get("slash_commands", [])),
            len(init.get("skills", [])),
            tuple(lab("plugin", p.get("name")) for p in init.get("plugins", [])),
            lab("mode", init.get("permissionMode")),
            ver(init.get("claude_code_version")),
            lab("model", init.get("model")),
        )
        inits[key] += 1
    print(f"== {study}: {n} trials with a stream, {no_init} without an init event")
    print(f"  hooks started: {dict(hooks)}")
    print(f"  hook responses with non-empty output (counted, not shown): {nonempty}")
    print(
        f"  synthetic zero-token first events (error events, not model requests; left out below): "
        f"{dict(sorted(synthetic.items()))}"
    )
    print(
        "  first-request context tokens of the other sessions, median (min to max) by arm:",
        {
            a: f"{statistics.median(v):.0f} ({min(v)} to {max(v)}), n {len(v)}"
            for a, v in sorted(first.items())
        },
    )
    for k, c in inits.most_common():
        print(
            f"  {c} x tools={k[0]} mcp servers={k[1]} slash commands={k[2]} skills={k[3]} "
            f"plugins={k[4]} mode={k[5]} version={k[6]} model={k[7]}"
        )
