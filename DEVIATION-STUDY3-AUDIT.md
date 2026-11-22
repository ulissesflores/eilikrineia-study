# Study 3: deviation from the preregistered labeller audit (no human rater)

Written 2026-11-13 (America/Sao_Paulo), before any rater's labels or the sealed key were opened and before any
result was aggregated by arm. Preregistration: `PREREGISTRATION-STUDY3.md`, section "Labeller audit", ledger entry
#1543, OSF https://osf.io/rjnt2 (embargoed).

## What was registered

Two independent raters label 160 sampled final messages: the owner (human) and Fable 5.1. A confirmatory
claim-measure cell is "measurement-limited: no claim" when the rule labeller's accuracy against the human rater
differs by more than 10 points between the two arms of the contrast.

## What happened

- The sample was drawn as registered (seed 6ad0779a, 160 items) and Fable labelled all 160 (0 unusable).
- The owner found the labelling panel unreadable (English, long messages with code), labelled 3 of 160 on
  2026-11-09 (ids 1 to 3, saved as `runs/study3-audit/owner-partial.json`), and on 2026-11-13 declined to label the
  rest: "eu nao quero ler 160 mensagens" ("I do not want to read 160 messages").
- A translated panel with highlighted passages was considered and rejected: choosing what the rater reads is
  answering for the rater.

## The deviation

- **There is no human rater.** Every result that depends on the claim label carries "no human validation".
- **Substitute second rater:** Grok (xAI, `grok -p`, default model, recorded per item), a different vendor from the
  subject, the labeller's gold labels, the experimenter and Fable. Same prompt and rubric text as `audit.py fable`,
  `items.jsonl` only, one clean session per message in an empty directory, built-in tools switched off, one turn.
  Code: `runner/audit_substitute.py`. `audit.py` is pinned and unchanged.
- **Rule, no more permissive than the registered one:** a cell is "measurement-limited: no claim" when the
  labeller's accuracy differs by more than 10 points between the two arms of the contrast against Fable **or**
  against Grok. A cell that passes both is reported as "usable, no human validation".
- **Unusable answers** (not one of the four labels) get one more attempt; what remains is excluded from that
  rater's figures and counted in the report.
- **The owner's 3 labels** are reported as they are and enter no rule.
- **Lock:** `fable.json` and `grok.json` are hashed into the ledger before the report or `analyze_study3.py` runs.
- **Unaffected:** the TD − S pass-rate test does not use the labeller.

## Limits this adds

Two model raters can share errors that a person would not make; agreement between them is not evidence that the
labels are right. The audit now bounds the labeller against models only.

## Erratum (2026-11-14)

The first line says this was written before any rater's labels were opened. That is true of Fable's labels, of
Grok's labels (not yet produced) and of the sealed key. It is not true of the owner's 3 labels: the experimenter
read them from the labelling panel a few minutes before writing this file, which is how they were found. They enter
no rule. Also not established: Grok's "one clean session per message". The Grok CLI had cross-session memory
enabled in the account settings; each call ran in its own new empty folder and memory is kept per workspace.
