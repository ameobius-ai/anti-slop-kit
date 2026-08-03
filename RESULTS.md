# Results

All numbers below are produced by the linters in this repository, from the sample
files in this repository. Reproduce them with:

```sh
python3 en/ste-lint.py en/samples/baseline.md en/samples/ste.md
python3 ru/ru-ste-lint.py ru/samples/baseline.md ru/samples/utr.md
```

The score is violations per 100 words. Lower is cleaner.

## Method

For each language there is one text written in a typical AI-assistant register
(the baseline) and one rewrite of the same content under the skill rules. Both
texts describe the same cache service and carry the same facts. Only the writing
changes.

## English

| File | Words | Violations | Score | Longest sentence |
| --- | --- | --- | --- | --- |
| `en/samples/baseline.md` | 157 | 52 | 33.12 | 49 words |
| `en/samples/ste.md` | 121 | 1 | 0.83 | 14 words |

An earlier version of this file reported 32.48 for the baseline. That number
counted markup as prose. The linters now remove frontmatter, code, link targets
and URLs before scoring, and the corrected figure was 31.85.

The baseline then moved from 31.85 to 33.12 when the word lists grew. The sample
text was not touched. Five raw hits appeared, but the score rose by two, because
three of the new words (`unlock`, `fast-paced`, `comprehensive`) sit inside
longer phrases the lists already carried. One span is one violation, so those
three add nothing here. Before that rule was in place they would have been
charged twice.

## Russian

| File | Words | Violations | Score | Longest sentence |
| --- | --- | --- | --- | --- |
| `ru/samples/baseline.md` | 117 | 46 | 39.32 | 27 words |
| `ru/samples/utr.md` | 94 | 0 | 0.00 | 11 words |

The Russian numbers did not move when the Russian lists grew: none of the new
entries appear in either Russian sample. A lexicon addition that changes no
sample is normal, and it is the reason the samples alone are a smoke test rather
than a measurement.

Baseline by category, per 100 words:

| Category | Count | Per 100 words |
| --- | --- | --- |
| nominalization | 12 | 10.26 |
| participle | 9 | 7.69 |
| clerical | 8 | 6.84 |
| marketing | 5 | 4.27 |
| long_sentence (>20w) | 3 | 2.56 |
| passive_reflexive | 2 | 1.71 |
| passive_short | 2 | 1.71 |
| semicolon | 1 | 0.85 |
| gerund | 1 | 0.85 |
| noun_chain (3+) | 1 | 0.85 |
| ai_slop | 1 | 0.85 |
| hedge | 1 | 0.85 |
| long_paragraph (>6s) | 0 | 0.00 |

Nominalization and participles carry most of the weight in Russian. This differs
from English, where banned words and marketing adjectives dominate. A Russian
anti-slop rule set that only bans words will therefore miss the main problem.

## Limits of these numbers

Read this section before you quote the deltas.

1. Two texts per language is a smoke test. It shows the linter reacts to the
   difference between slop and controlled prose. It does not measure how much a
   model improves across real tasks.
2. A real evaluation needs several tasks, several models, and a condition that
   is not the skill (for example: a plain instruction to write clearly). Without
   that control, the delta may only show that the rewrite was written to satisfy
   the linter.
3. The linters match regular expressions. They produce false positives, and a
   writer can lower the score without improving the text.
4. A score of 0 says nothing about accuracy, completeness, or usefulness.
5. The baseline score is not a constant. It moves when the lists move, as it did
   above. Compare texts scored by the same version of the linter, and treat any
   number quoted here as tied to the commit that produced it.

## Regression protection

`tests/test_linters.py` asserts the shape of these results:

- each baseline scores above 20 per 100 words
- each clean sample scores below 2 per 100 words
- each clean sample keeps every sentence at 20 words or fewer

The tests pin the shape rather than the exact score, so a lexicon addition that
moves the baseline by a point does not fail the build, while a change that
collapses the gap between slop and clean prose does.

CI also runs both linters against the clean samples with `--max 2`, so a change
to a rule that quietly breaks the samples fails the build.

## Open work

- Reproduce a full evaluation: several tasks, at least two models, four
  conditions (no instruction, plain instruction, banned-word list, skill).
- Build an approved-word dictionary for Russian, similar in role to the STE
  controlled vocabulary.
- Measure the false-positive rate of each rule against human-written text.
