# anti-slop-kit

Controlled-language writing skills and deterministic linters that remove AI slop from technical prose.

Two tracks:

| Track | Basis | Skill | Linter |
| --- | --- | --- | --- |
| English | ASD-STE100 (Simplified Technical English) | `en/SKILL.md` | `en/ste-lint.py` |
| Russian | GOST R 58049-2017 section 8.2.3 (UTR) | `ru/SKILL.md` | `ru/ru-ste-lint.py` |

## Why

AI writing assistants produce prose that is grammatical and empty. Ban-word lists do not fix this, because the problem is structure, not vocabulary.

Controlled natural languages solve the same problem for aircraft maintenance manuals since 1986. ASD-STE100 constrains vocabulary, sentence length, voice, and paragraph structure. The Russian standard GOST R 58049-2017 does the same for Russian technical documentation.

This repository ports both into agent skills, and adds a linter so the result is a number, not an opinion.

## Score

Both linters report violations per 100 words. Lower is cleaner.

The useful signal is the delta between a draft and a rewrite, not the absolute value.

### Russian, measured

```
sample-baseline.md   words=117  total=46  per100w=39.32  maxsent=27
sample-utr.md        words= 94  total= 0  per100w= 0.00  maxsent=11
```

Top categories in the baseline: verbal nouns 10.26, participles 7.69, bureaucratese 6.84 per 100 words.

Two texts is a smoke test, not a benchmark. A full run is open work.

## Install

```bash
# Claude Code
mkdir -p ~/.claude/skills/utrya-writing
cp ru/SKILL.md ru/ru-ste-lint.py ~/.claude/skills/utrya-writing/

mkdir -p ~/.claude/skills/ste-writing
cp en/SKILL.md en/ste-lint.py ~/.claude/skills/ste-writing/
```

Copilot CLI uses `~/.copilot/skills/`. Amp and cross-agent hosts use `~/.agents/skills/`.

## Run the linter

```bash
python3 ru/ru-ste-lint.py draft.md
python3 ru/ru-ste-lint.py --json draft.md
cat draft.md | python3 ru/ru-ste-lint.py
```

Python 3, standard library only. No dependencies.

## Scope

Apply to documentation, README files, pull request descriptions, error messages, release notes, and comments.

Do not apply to code, variable names, or command syntax.

Do not apply to marketing copy, essays, or fiction. Controlled language removes voice on purpose.

## Limits

- The linters are heuristic. They match surface patterns and produce false positives.
- They check form. They cannot tell you whether a paragraph is true or worth writing.
- Russian morphology is harder than English. The participle and nominalization patterns over-match some legitimate technical nouns.

## Prior art

- ASD-STE100, Issue 9, 15 January 2025. Owned by ASD (Brussels) and maintained by STEMG. Free copy on request from asd-ste100.org. The specification text is copyrighted and is not reproduced here.
- GOST R 58049-2017, section 8.2.3. Introduces UTR, simplified technical Russian.
- GOST 2.105, clause 4.2. Prefer a Russian word when an equivalent exists.
- Glavred and the infostyle school (Ilyahov, Nora Gal) for Russian editing heuristics.
- `talkstream/ru-text`. A broader Russian style plugin, roughly 1044 rules across typography, UX copy, and business writing. Complementary, not a competitor: it gives breadth, this gives a deterministic number for CI.
- `woosal1337/blog`, episode 01, for the original English experiment that showed a controlled-language skill beats ban-word lists.

## License

MIT. See `LICENSE`.
