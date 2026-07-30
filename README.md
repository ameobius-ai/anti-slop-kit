# anti-slop-kit

Controlled-language writing skills and deterministic linters that remove AI slop
from technical prose. Two languages: English (ASD-STE100 mechanics) and Russian
(GOST R 58049-2017, clause 8.2.3).

A skill tells the model how to write. A linter proves whether the model did it.
The linter is the part most anti-slop advice leaves out.

## What is in here

```
AGENTS.md                instructions for an agent working in this repository
en/SKILL.md              ste-writing skill, English
en/ste-lint.py           English linter, 11 rule groups
en/samples/              one slop text and one clean rewrite
ru/SKILL.md              utrya-writing skill, Russian
ru/ru-ste-lint.py        Russian linter, 13 rule groups + typography
ru/samples/              one slop text and one clean rewrite
harness/SKILL.md         separate skill: how to design an agent harness
evals/                   eval harness: 12 tasks, 4 conditions, scorer, runner
tests/                   43 tests, standard library only
hooks/pre-commit         git hook that blocks a commit above the limit
.pre-commit-config.example.yaml
RESULTS.md               measured scores and their limits
```

## Quick start

```sh
git clone https://github.com/Username-ame/anti-slop-kit
cd anti-slop-kit

python3 en/ste-lint.py en/samples/baseline.md en/samples/ste.md
python3 ru/ru-ste-lint.py ru/samples/baseline.md ru/samples/utr.md

python3 -m unittest discover -s tests
```

No dependencies. Python 3.9 or later. The linters use the standard library only,
because a skill directory is copied as a unit and must keep working after the copy.

## Score

The score is violations per 100 words. Lower is cleaner.

| Text | Score | Longest sentence |
| --- | --- | --- |
| `en/samples/baseline.md` | 31.85 | 49 words |
| `en/samples/ste.md` | 0.83 | 14 words |
| `ru/samples/baseline.md` | 39.32 | 27 words |
| `ru/samples/utr.md` | 0.00 | 11 words |

Read `RESULTS.md` before you quote these numbers. Two texts per language is a
smoke test, not a benchmark. `evals/` holds the harness for a real measurement
across six tasks per language and four prompt conditions. It has not been run
yet, and no number on this page comes from it.

## Use it in a pipeline

The linters return exit code 1 when a file scores above the limit, so they can
gate a build:

```sh
python3 en/ste-lint.py --max 5 docs/*.md
python3 ru/ru-ste-lint.py --max 5 --json README.ru.md
```

Exit codes:

- `0`: every file is at or below the limit, or no limit was given
- `1`: at least one file is above the limit
- `2`: bad option or unreadable file

Git hook:

```sh
ln -s ../../hooks/pre-commit .git/hooks/pre-commit
chmod +x hooks/pre-commit
ANTI_SLOP_MAX=3 git commit          # change the limit for one commit
git commit --no-verify              # skip the hook
```

For [pre-commit](https://pre-commit.com), copy `.pre-commit-config.example.yaml`
and adjust the two paths.

## Exclude a region

The linters skip frontmatter, code blocks, inline code, link targets, bare URLs
and HTML comments. To exclude prose as well:

```markdown
<!-- anti-slop: off -->
A quoted paragraph that you must not rewrite.
<!-- anti-slop: on -->
```

## What the score does not tell you

The linters match patterns. They do not read.

- A score of 0 says nothing about whether the text is correct or complete.
- Every rule can produce a false positive. Passive voice is right when the actor
  is unknown. Some long sentences are clear.
- Use the score to find candidates for a rewrite, not to grade a writer.

## Sources

- ASD-STE100 Simplified Technical English, Issue 9 (15 January 2025), ASD and the
  STEMG: https://asd-ste100.org. The specification is copyrighted. This repository
  reproduces the mechanics and no part of the text. Request a free copy from ASD.
- GOST R 58049-2017, clause 8.2.3, controlled Russian technical language.
- The English skill follows the approach shown in
  https://github.com/woosal1337/blog/tree/main/videos/ep01-the-cure-for-ai-slop.
  The skill and the linter here are written from scratch and share no code with it.
- https://github.com/talkstream/ru-text is a larger Russian rule set (about 1044
  rules) and works well next to this kit.
- `harness/SKILL.md` is built from
  https://github.com/ai-boost/awesome-harness-engineering (CC0) and the sources it
  lists.

## License

MIT. See `LICENSE`.
