# en-release-note

`before.md` is a release note in the register a model reaches for without a skill: it announces the team rather than the change. A reader who wants to know what to do learns it in one clause, near the end.

## Scores

| File | Words | Total | Per 100 words | Longest sentence | slop | cl |
|---|---|---|---|---|---|---|
| `before.md` | 150 | 32 | 21.33 | 30 | 15 | 17 |
| `after.md` | 99 | 3 | 3.03 | 13 | 0 | 3 |

Measured with `python3 en/ste-lint.py --breakdown`.

## What the rewrite changed

- Removed the announcement frame: no thrill, no journey, no milestone. The first line states the two changes.
- Cut every marketing adjective (`robust`, `powerful`, `world-class`, `invaluable`) and every hedge (`may want to consider`, `may potentially`).
- Replaced `In order to utilize` with the action itself, in the imperative.
- Gave the breaking change its own section, before the change list, because it is the only part that blocks the reader.
- Split one 30-word sentence into steps that a person can follow while looking at a terminal.
- Added the numbers the original avoided: 40 percent, 1 million rows, the log path.

The rewrite is 34 percent shorter and says more.

## Provenance

The before text is hand-written, not model output. Issue #1 will produce bare-condition generations for the overlapping task (`evals/tasks/en-03-release-notes.md`); when it does, replace this file with the real generation and record the model and the date here. The pair format does not change, so the acceptance test survives the swap.
