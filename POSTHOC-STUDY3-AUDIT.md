# Study 3: post-hoc additions to the labeller audit (plan, written before they run)

Written 2026-11-14 (America/Sao_Paulo). The results of study 3 (`RESULTS-STUDY3.md`, ledger #1865, corrections #1866
and #1867) have been seen by the experimenter and the owner. Nothing below changes a confirmatory reading or the
decision rule of `DEVIATION-STUDY3-AUDIT.md`: I − S stays measurement-limited whatever these additions show.

Purpose: `RESULTS-STUDY3.md` says no person validated the labeller. The owner now agrees to label a small set.

1. **Owner labels 40 of the 160 audit messages.** Drawn by code (`runner/audit_posthoc.py sample`): 10 per arm, 5
   with the hidden check passed and 5 failed, seed = first 8 hex digits of sha256(this entry's hash + "owner40").
   Never chosen by label.
2. **What the owner sees:** a machine translation into Brazilian Portuguese (`claude -p --model opus`, no tools;
   prose only, masks and code unchanged), fenced code collapsed behind a button, the English original one click
   away, no highlighting, no arm, trial, check result or any rater's label. A translation that fails the mechanical
   checks (same number of masks and fences, length ratio 0.7 to 1.6) is retried once, then shown in English.
3. **Third model rater:** Gemini 4 Hydrogen (`agy --model gemini-4-hydrogen-high`), all 160 items, same prompt and
   rubric as Fable and Grok, one call per message in a new empty folder. Checked before the run: the CLI loads the
   owner's global instruction file and keeps conversation summaries, so a clean session is not established; the
   CLI's JSON does not report the model, so the requested id is recorded.
4. **Reported:** owner against the labeller and each model rater on complete vs not complete (n 40, Wilson interval,
   about ±12 points near 80%); Hydrogen against the labeller overall and per arm, and against Fable and Grok.
5. **Limits:** post-hoc; the owner knows the results and the hypotheses; he reads a translation; 40 items cannot
   run the per-arm rule. The owner's 3 earlier labels stay out.
6. **Lock:** the owner's labels and `hydrogen.json` are hashed into the ledger before `audit_posthoc.py report` runs.
