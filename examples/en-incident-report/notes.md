# en-incident-report

`before.md` is the incident report that protects the author. It uses the passive voice at every point where a person or a change would otherwise be named, and it never says how long the incident lasted.

## Scores

| File | Words | Total | Per 100 words | Longest sentence | slop | cl |
|---|---|---|---|---|---|---|
| `before.md` | 137 | 21 | 15.33 | 32 | 8 | 13 |
| `after.md` | 170 | 4 | 2.35 | 17 | 0 | 4 |

Measured with `python3 en/ste-lint.py --breakdown`.

## What the rewrite changed

- Put the effect first, with a duration and a percentage: 14:02 to 15:47 UTC, 12 percent of requests.
- Replaced `a subset of our valued customers may have experienced degraded performance` with the measured latency.
- Turned `it was ultimately determined that the root cause was related to` into three sentences that name the change and the mechanism.
- Made the timeline a table. A reader comparing this incident with the next one needs to scan times, not sentences.
- Gave each correction an owner state: done on a date, or planned for a date. The original promised safeguards without either.
- Removed the apology paragraph. The corrections are the apology.

This is the one pair where the after text is longer than the before text, by 33 words. Precision costs words here, and the score still falls by 85 percent.

## Provenance

The before text is hand-written, not model output. There is no incident-report task in `evals/tasks/` yet; adding one would let this pair be regenerated like the other two.
