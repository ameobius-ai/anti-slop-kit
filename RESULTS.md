# Measured results

All numbers come from the linters in this repository. Score is violations per 100 words. Lower is cleaner.

## Russian

```
$ python3 ru/ru-ste-lint.py ru/samples/baseline.md ru/samples/utr.md
baseline.md   words=117  total=46  per100w=39.32  maxsent=27
utr.md        words= 94  total= 0  per100w= 0.00  maxsent=11
```

Breakdown of the 46 violations in the baseline:

| Category | Count | Per 100 words |
| --- | --- | --- |
| nominalization | 12 | 10.26 |
| participle | 9 | 7.69 |
| clerical | 8 | 6.84 |
| marketing | 5 | 4.27 |
| passive (reflexive + short) | 4 | 3.42 |
| long_sentence (>20w) | 3 | 2.56 |
| semicolon, gerund, noun_chain, ai_slop, hedge | 5 | 4.28 |

## English

```
$ python3 en/ste-lint.py en/samples/baseline.md en/samples/ste.md
baseline.md   words=157  total=51  per100w=32.48  maxsent=49
ste.md        words=121  total= 1  per100w= 0.83  maxsent=14
```

## Honest caveats

- Two sample texts per language is a smoke test, not a benchmark. It proves the linter reacts to the rules. It does not prove the skill improves real model output.
- A proper evaluation needs several tasks, several models, and a baseline condition. That work is open.
- The linters are heuristic regex matchers. They produce false positives, especially on Russian participles and nominalizations that are legitimate technical nouns.
- A score of zero means the form is clean. It says nothing about whether the content is correct or useful.
