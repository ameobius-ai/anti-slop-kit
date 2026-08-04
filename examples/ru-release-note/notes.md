# ru-release-note

`before.ru.md` is the Russian release note that announces itself. The change is stated once, in a subordinate clause, after two sentences about the team and the platform.

## Scores

| File | Words | Total | Per 100 words | Longest sentence | slop | cl |
|---|---|---|---|---|---|---|
| `before.ru.md` | 110 | 24 | 21.82 | 23 | 7 | 17 |
| `after.ru.md` | 85 | 1 | 1.18 | 11 | 0 | 1 |

Measured with `python3 ru/ru-ste-lint.py --breakdown`.

This is the cleanest after file in the gallery: one violation in 85 words.

## What the rewrite changed

- Deleted the announcement frame (`Мы рады сообщить о том, что`) and the closing invitation.
- Replaced the passive chains (`была осуществлена реализация`, `была произведена оптимизация`) with active verbs.
- Turned `необходимо осуществить обновление файлов конфигурации` into the command that does it.
- Kept the same structure as the English release note in this gallery, so a reader can compare the two languages line by line.

## Provenance

The before text is hand-written, not model output. Issue #1 will produce bare-condition generations for `evals/tasks/ru-03-release-notes.md`; when it does, replace this file with the real generation and record the model and the date here.
