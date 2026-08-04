# ru-api-doc

`before.ru.md` is the Russian clerical register: `осуществляется рассмотрение`, `производится посредством`, `является`. It is the highest-scoring before file in the gallery, and the score is almost entirely controlled-language violations rather than slop vocabulary.

## Scores

| File | Words | Total | Per 100 words | Longest sentence | slop | cl |
|---|---|---|---|---|---|---|
| `before.ru.md` | 102 | 32 | 31.37 | 22 | 9 | 23 |
| `after.ru.md` | 100 | 4 | 4.00 | 8 | 0 | 4 |

Measured with `python3 ru/ru-ste-lint.py --breakdown`.

The split matters here. Of 32 violations, 23 are structural: nominalizations, participles, one gerund, and reflexive passives. A reviewer who saw only the total might look for banned words and find nine.

## What the rewrite changed

- Replaced every nominalization chain with a verb in the imperative: `осуществление процедуры создания задачи производится посредством отправки запроса` becomes `Отправьте запрос`.
- Removed `является` in all three places. Russian does not need a copula in the present tense.
- Dropped the participle clauses (`содержащего`, `являющимся`, `носящие`) and the gerund (`Используя`).
- Replaced `в целях обеспечения повышения надёжности` with the retry rule and its numbers.
- Moved the field list and the response codes into tables, as in the English pair.

The four remaining violations in `after.ru.md` are technical nominalizations that PR #34 correctly leaves in place, such as the noun forms a reader expects in a field description.

## Provenance

The before text is hand-written, not model output. Issue #1 will produce bare-condition generations for `evals/tasks/ru-01-api-doc.md`; when it does, replace this file with the real generation and record the model and the date here.
