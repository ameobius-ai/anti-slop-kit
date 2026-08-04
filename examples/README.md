# Before and after

Five pairs. Each directory holds the same document twice: `before` as a model writes it without the skill, `after` as the skill asks for it, and `notes.md` with the scores and the reasoning.

| Pair | Before | After | Fall |
|---|---|---|---|
| [en-release-note](en-release-note/) | 21.33 | 3.03 | 86 % |
| [en-api-doc](en-api-doc/) | 16.42 | 2.42 | 85 % |
| [en-incident-report](en-incident-report/) | 15.33 | 2.35 | 85 % |
| [ru-api-doc](ru-api-doc/) | 31.37 | 4.00 | 87 % |
| [ru-release-note](ru-release-note/) | 21.82 | 1.18 | 95 % |

The numbers are violations per 100 words. Reproduce them:

```sh
python3 en/ste-lint.py --breakdown examples/en-api-doc/before.md
python3 ru/ru-ste-lint.py --breakdown examples/ru-api-doc/after.ru.md
```

Every `after` file scores 0 for slop vocabulary. What remains is controlled language: sentence length and the noun forms a field description needs.

## Reading the pairs

The rewrites are not compressions. `en-incident-report/after.md` is 33 words longer than its before file, because a timeline with times and a correction with a date cost words that an apology does not. Length is not the target; the score is.

## Conventions

- A directory is `en-*` or `ru-*`. Russian files carry the `.ru.md` suffix, which is how both the linter selection in `hooks/pre-commit` and `tests/test_examples.py` route them.
- One `before` file, one `after` file, one `notes.md` per directory.
- `tests/test_examples.py` walks this directory. It does not name the pairs, so a sixth pair is covered as soon as it is added. It asserts that every `after` file scores lower than its `before` file, and that every `after` file passes the pre-commit hook at its default limit of 5.

## The before texts are hand-written

They are written to look like unassisted model output, not captured from a run. Issue #1 will produce bare-condition generations for the tasks in `evals/tasks/`; three of these five pairs map onto a task there, and each `notes.md` names the task to swap in. Until then, read the before files as illustrations rather than as evidence. The evidence lives in `RESULTS.md`.

## The hook skips the before files

`before` files are slop by design and would block every commit that touches them. `hooks/pre-commit` skips `examples/*/before*.md` and `*/samples/baseline.md` for that reason, and says so when it does.
