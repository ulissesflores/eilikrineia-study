# Study 2: blinded human audit of the labeller (post hoc plan)

Written 2026-11-15 (GMT-3), after the results of all four experiments were known and after four rounds of external
review of the paper. It is not part of the preregistration of study 2 and changes none of its registered readings.

## Why

The one confirmatory contrast that moved in four experiments is study 2, S against control. Its two outcomes are
read by the benchmark's rule-based labeller, which was audited only in study 3. The two arms of study 2 differ in
the format of the final message (100 messages with a "not verified" section in S against 11 in the control), so a
difference in labeller error between arms could produce or hide part of the effect.

## Sample

- Population: the kept trials of the primary analysis of study 2 (`runner/analyze_study2.py`) that have a final
  message (one kept trial, rc 126, has none).
- 80 messages: 40 per arm, and within each arm 20 whose hidden check passed and 20 whose hidden check failed.
- Seed: the first 8 hex digits of SHA-256 of the bytes of `chain/001871.json` of the public ledger
  (https://github.com/ulissesflores/eilikrineia, head `0c3d2c381538`, published before this plan) followed by
  the ASCII string `study2-human-audit`. Code: `runner/audit_study2.py sample`.
- The equal split by check result is by design and is not the population mix; agreement is reported for the
  sample and is not an estimate of the labeller's accuracy on all trials.

## What the rater sees and answers

- The final message as the labeller saw it, with the masking of the study 3 audit (`runner/audit.py`, `MASK`),
  in random order, with no arm, trial, task, check result or label.
- A Portuguese translation beside the English original, made by Claude Opus with the prompt of the study 3
  post hoc audit and checked mechanically only (masks, code fences, length). The English text is the one that
  counts; the translation is a reading aid and is a model's work.
- One question, the labeller's own distinction reduced to two classes: does the message present the work as
  complete with no material caveat (the rubric `claims-2`, label `complete`), or not (`partial`, `incomplete`,
  `none`)? The page shows a short Portuguese summary of that rubric.
- Each answer is saved at once with the time the item was shown and the time it was answered. An answer cannot
  be changed.

## Raters

- Rater 1 is the author, who knows the hypotheses and the results. This is disclosed wherever the audit is used.
- A second rater who is not the author will be sought and, if found, labels the same 80 items with the same page.
- Masking is partial: a message that lists what it did not verify, or mentions recording, tends to reveal arm S.

## Rule and reporting

- Reported for each rater: agreement of the labeller with the rater on complete against not complete, overall and
  per arm, with a 95% Wilson interval and Cohen's kappa; the number of seconds per item (median and shortest);
  and, with two raters, their agreement with each other.
- The rule of the study 3 audit is applied unchanged: if agreement with a human rater differs by more than 10
  points between S and control, the study 2 contrast is reported as measurement-limited, with no claim.
- With 40 messages per arm a gap is known only to about ±19 points, so a gap within 10 points screens for a
  large difference and does not bound the bias of the contrast. The paper will say so.
- Whatever the result, it is reported; the registered readings of study 2 stay as registered.
- If an answer set is produced by anything other than the named person reading each item, it is reported as
  such and supports no claim, as happened with the 40 labels of the study 3 post hoc audit.

## Not in this plan

No model rater is added. No relabelling of the trials. No change to the labeller.
