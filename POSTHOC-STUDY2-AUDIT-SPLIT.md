# Study 2 human audit: split by check result and a speed screen (post hoc plan, second)

Written 2026-11-22 (GMT-3), after the agreement of the study 2 audit was computed and recorded (ledger #2648) and
after seven rounds of external review of the paper. Nothing in this plan has been computed when it is recorded.
It changes none of the registered readings of study 2 and none of the readings of the first audit plan
(`POSTHOC-STUDY2-AUDIT.md`, #1872), whose result stands as reported.

## Why

Reviewers raised two questions that the first plan does not answer.

1. The first audit pools, within each arm, the 20 messages whose hidden check passed and the 20 whose check failed.
   False completion is a "complete" on a trial that failed, so the pooled counts do not show whether the people
   who read the messages saw fewer "complete" in S than in the control among the failed trials. Equal agreement
   in two arms can also hide errors in opposite directions.
2. The second rater answered one item 0.6 seconds after it was shown (#2648: "shortest 0.6 (one answer under
   10 s)"), and that rater's gap in agreement between arms was exactly 10.0 points, the threshold of the rule.

## Data

Only files already in the ledger: `runs/study2-audit/key.jsonl` (arm, check result and labeller label per item),
`labels-ulisses.json` and `labels-rater2.json` (#1873, #2647). No new label, rater, message or model call.

## Computation A: split by check result (descriptive)

For each of the three readers (labeller, author, second rater) and each of the four cells (arm S or control,
check passed or failed, 20 items each): the number of items read as complete.
For each human rater and each cell: the 2 x 2 table of labeller against rater (complete / not complete).
Reported with 95% Wilson intervals, no test. With 20 items per cell an interval spans about ±20 points; the
counts describe this sample, which has an equal split by design, and are not estimates for the population.

## Computation B: speed screen (sensitivity)

Answers given in under 5 seconds are removed (messages average about 2,400 characters; no one reads one in under
5 seconds). By the recorded report this removes exactly one answer, the second rater's 0.6-second one; the
author's shortest answer was 9.7 seconds. The first plan's agreement table (overall, per arm, gap) is recomputed
for the second rater without it, and Computation A is repeated without it.

## Reporting, decided now

- Both computations are reported in the paper and the package whatever they show, labelled post hoc, beside the
  recorded result and never in place of it. They are computed once, by `runner/audit_study2_split.py` (a new file;
  `runner/audit_study2.py` stays byte-identical to its recorded hash), whose SHA-256 is given in the ledger entry
  that records this plan; the output file `runs/study2-audit/report-split.txt` is recorded in the ledger.
- If, among failed trials, a human rater read "complete" no less often in S than in the control, the paper says so
  in Section 5.3, in Section 5.8 and in the Abstract's sentence on the human readers.
- If the gap of Computation B exceeds 10 points, the paper reports that the second rater's screen fails without
  that answer, and the study 2 contrast is described as measurement-limited on that sensitivity reading; the
  registered readings still stand as registered, as the first plan requires.

## Not in this plan

No new rater, no new labels, no change to the labeller, no other threshold for the speed screen, no test of a
treatment-by-task interaction.
