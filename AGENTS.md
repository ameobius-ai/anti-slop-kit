# AGENTS.md

Instructions for an agent that works in this repository.

## What this repository is

Two controlled-language writing skills and two deterministic linters that
measure the result. English follows ASD-STE100 mechanics. Russian follows GOST R
58049-2017, clause 8.2.3.

The linter is the point. A skill claims an effect; only the linter shows one.

## Layout

```
en/SKILL.md, en/ste-lint.py, en/samples/     English skill, linter, samples
ru/SKILL.md, ru/ru-ste-lint.py, ru/samples/  Russian skill, linter, samples
harness/SKILL.md                             separate skill: agent harness design
evals/                                       eval harness, never run yet
tests/                                       unittest suite, 43 tests
hooks/pre-commit                             local git hook
RESULTS.md                                   measured scores and their limits
```

## Commands

```sh
python3 -m unittest discover -s tests            # must pass before any push
python3 en/ste-lint.py --max 2 en/samples/ste.md
python3 ru/ru-ste-lint.py --max 2 ru/samples/utr.md
python3 evals/score.py evals/outputs
```

Exit codes for both linters: 0 at or below the limit, 1 above it, 2 bad option
or unreadable file.

## Rules

1. Standard library only. A skill directory is copied as a unit, and a copy with
   a dependency stops working somewhere else.
2. Do not merge the two linters into a shared helper module. The duplication is
   deliberate: each file must run alone after it is copied.
3. A rule change needs a test in the same commit. A rule with no test is a guess.
4. Do not tune the sample texts to make a score look better. Change the rule or
   accept the number.
5. Do not change the output format of the linters. `evals/score.py`, the hook and
   the CI job read it.
6. Push code before the workflow that runs it. The reverse order left CI red for
   two commits.

## Verification gate

Do not report a task as done until the test suite passes and the two sample
commands print the expected scores. State the numbers you saw. Do not claim a
command ran unless its output is in front of you.

## Out of scope

- No copy of the ASD-STE100 specification text. It is copyrighted. Mechanics
  only.
- No new language until an existing one has a real eval run behind it.
- No web service, no package, no plugin. The kit is files and two scripts.

## When a part of this repository should be removed

| Part | Exists because | Remove when |
| --- | --- | --- |
| Word lists in the linters | Models repeat a small set of filler words | The lists stop matching new model output |
| The skills | Models do not hold a register without instruction | A model holds the register with a one-line prompt |
| `evals/` | Nobody has measured the skills on tasks | The measurement is done and repeated |
