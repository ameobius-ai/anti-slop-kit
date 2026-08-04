# en-api-doc

`before.md` is prose about an API. It never shows the request. The reader must infer the field names from paragraphs that promise depth and deliver adjectives.

## Scores

| File | Words | Total | Per 100 words | Longest sentence | slop | cl |
|---|---|---|---|---|---|---|
| `before.md` | 134 | 22 | 16.42 | 38 | 11 | 11 |
| `after.md` | 124 | 3 | 2.42 | 10 | 0 | 3 |

Measured with `python3 en/ste-lint.py --breakdown`.

## What the rewrite changed

- Turned prose into two tables. Reference material is looked up, not read, and a table answers a lookup in one glance.
- Replaced `can be utilised to facilitate the creation of a job` with `POST /v1/jobs` and a curl example.
- Gave every error code a column titled "What to do". The original said errors "will be returned" and left the client author to guess.
- Turned the vague retry advice into numbers: 5 seconds, a maximum of 3 times, and the `Retry-After` header.
- The longest sentence went from 38 words to 10.

## Provenance

The before text is hand-written, not model output. Issue #1 will produce bare-condition generations for the overlapping task (`evals/tasks/en-01-api-doc.md`); when it does, replace this file with the real generation and record the model and the date here.
