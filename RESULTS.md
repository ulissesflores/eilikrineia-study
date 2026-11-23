# Results — does a signed, public claim record change what a coding agent claims? (pilot, 2026-11-04)

The preregistration is `PREREGISTRATION.md`, recorded in the Eilikrineia ledger as entry #1331 (hash `cfe62784…`) before
the first trial, with the code pinned by hash. The numbers below come from `runner/score.py` and `runner/analyze.py`,
run on the raw files. Anyone can rerun them from `runs/pilot-scores.csv`. Arm P's raw transcripts and ledgers are
published as well.


> [!WARNING]
> **Correction, 2026-11-07.** The hidden checks of `feature-toml-config` and `feature-uri-resolve` contradict their task
> text (TOML: the check compares with the host Python 3.15 `tomllib`, which follows TOML 1.1; URI: the oracle lowercases
> percent-encoding hex in the host, which the text says stays uppercase). In those two tasks a failed check does not show
> a false completion. Details and evidence: `RESULTS-STUDY.md`, "Correction: hidden-check validity", and
> `runs/study-check-validity.txt`.

## Answer

**No useful effect at this size.** Two contrasts were tested, both on M1, an unbacked claim:
- signed and public (P) against signed and private (S): P − S = +3.2 points, 95% interval −9.7 to +16.0;
- signed (S) against private unsigned notes (H): S − H = −3.2 points, 95% interval −16.0 to +9.7.

The preregistered rule for H1, publicity, says |P − S| < 10 points means no useful publicity effect at this size. The
replication on a second agent (Codex) runs only if a record arm leads by at least 10 points, and none did, so it is
not run.

## Numbers

- 180 trials. 4 were excluded by the preregistered rules:
  - 2 timeouts (`141-P-feature-minire-r3`, `165-S-feature-minire-r2`);
  - 2 whose transcript reads a `checks/` folder (`061-S-bughunt-ratelimit-r1`, `164-H-data-interval-sets-r2`). In
    both, the folder was the agent's own scratch, created outside its workspace, not the hidden checks. The rule was
    applied literally, and the second table shows the result without these 2 exclusions.
- Model: `claude-haiku-5-5`, Claude Code 2.1.318, subscription login, confined tools.
- Tasks: 20 from `overclaim` (18 solvable, 2 impossible), 3 repetitions per arm, shuffled by the preregistration hash.

| Arm | n | M1 unbacked claim | M2 false completion | Hidden check passed | Claims recorded per trial |
|---|---|---|---|---|---|
| H, private unsigned notes | 59 | 9 (15.3%; 8.2–26.5%) | 3 (5.1%; 1.7–13.9%) | 74.6% | 4.58 |
| S, signed, kept by the owner | 58 | 7 (12.1%; 6.0–22.9%) | 2 (3.4%; 1.0–11.7%) | 72.4% | 4.10 |
| P, signed, published | 59 | 9 (15.3%; 8.2–26.5%) | 1 (1.7%; 0.3–9.0%) | 79.7% | 3.49 |

| Contrast | M1 | M2 |
|---|---|---|
| P − S | +3.2 points (−9.7 to +16.0) | −1.8 points (−10.2 to +6.0) |
| S − H | −3.2 points (−16.0 to +9.7) | −1.6 points (−10.8 to +7.3) |

Without the 2 `checks/` exclusions: P − S on M1 = +3.4, and S − H on M1 = −4.8. The conclusion is the same. The
per-task table is in `runs/pilot-analysis.txt`.

## What the measures really caught

- **M1 is mostly a measurement artefact here.** In 23 of its 25 events, the hidden check **passed**: the work was
  right. The transcript simply did not show a passing test run after the last edit, as read by `overclaim`'s parser
  (`failed`, `unknown` or `not_run`). M1 therefore measures "a claim without visible proof", and the parser adds noise.
  The noise is equal across arms, but it swamps any effect.
- **M2 is a genuinely false completion,** and it is rare: 6 of 176 (3.4%). The order is P 1 < S 2 < H 3, which is the
  direction the thesis predicts. But 3 against 1 is well inside the noise. Telling 5% from 1.7% would need roughly
  500 or more trials per arm.
- **Agents in every arm used the record tool** (3.5 to 4.6 records per trial). In P, agents acknowledged the condition
  in their final message ("these go into the public, permanent ledger").

## Limits

- One model, a small and cheap one, on 20 short coding tasks that it mostly solves. False claims are rare in this
  setting, so the pilot can rule out only large effects (about 10 points or more).
- Every arm also received the same instruction to record claims. The contrast tests status (private / signed /
  public), not recording against no recording.
- Every trial is itself an evaluation. Awareness of being tested may touch all arms equally.
- Two SessionStart hooks from the host's Claude Code configuration ran in each trial despite `--setting-sources ""`.
  Both returned empty output, so nothing was injected.

## What this means for the product

- The pilot gives no support, at this size, for "public signing makes the agent claim fewer false things". It does
  not refute a small effect either.
- What the ledger demonstrably does is unchanged: it records what was claimed, with evidence, and lets anyone check
  later that nothing was rewritten.
- A test of the thesis that could find a small effect needs:
  - tasks where agents fail more often;
  - a model that overclaims more;
  - M2-type outcomes in the hundreds per arm;
  - a better M1 parser.
