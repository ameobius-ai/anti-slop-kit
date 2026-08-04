# Contributing

Thank you for improving the kit. The lexicons are the heart of this repository,
and they are also the easiest place to break its invariants, so please read this
before opening a pull request.

## The ground rules

These come from `AGENTS.md`, restated for humans:

1. **Standard library only.** The linters must keep working when a skill
   directory is copied as a unit. No third-party imports, ever.
2. **The two linters are edited by hand.** `en/ste-lint.py` and
   `ru/ru-ste-lint.py` duplicate structure on purpose. Do not extract a shared
   module; a change lands in both files or in neither.
3. **A rule change ships with a test in the same commit.** No test, no merge.
4. **Do not tune the sample texts to improve scores.** The files under
   `en/samples/` and `ru/samples/` pin linter behaviour. Making the baseline
   score worse or the clean sample score better by editing the text is gaming
   the fixture, not improving the tool.
5. **Do not change the linter output format.** `evals/score.py`,
   `hooks/pre-commit`, and CI parse the summary line. New information goes
   behind a new flag; the default line stays byte-identical.
6. **Push code before the workflow that runs it.** CI must never reference a
   flag that does not exist on the branch it checks out.

## How to add a banned word or phrase

1. Pick the right list.
   - English: `BANNED`, `MARKETING`, `AI_SLOP`, `HEDGE`.
   - Russian: `CLERICAL`, `MARKETING`, `AI_SLOP`, `HEDGE`.

   Lexicons are for wording that is almost always wrong. Mechanics (passive
   voice, nominalization, sentence length) are structural and live in the
   regexes instead.
2. Apply the bar: there must be a plainer replacement that works in most
   contexts. If the word is sometimes the right word, it does not belong in
   the list.
3. Add the word and, where a canned rewrite exists, add it to `REPLACE` so
   `--explain` can suggest the fix.
4. Make the same class of change in the other linter if an equivalent exists.
5. Add a test in the same commit.

## How to report a false positive

Open an issue with:

- the exact sentence,
- the category that fired,
- why the original was correct.

False positives are more valuable than new rules. A tool that cries wolf gets
uninstalled.

## What will not be merged

- Changes to sample texts that improve scores (rule 4).
- Changes to the default output format (rule 5).
- Third-party dependencies (rule 1).
- Shared helper modules between the linters (rule 2).

## Run the checks

```sh
./demo.sh
```

Or individually:

```sh
bash scripts/check.sh
```

Or one piece at a time:

```sh
python3 -m unittest discover -s tests
python3 en/ste-lint.py en/samples/baseline.md en/samples/ste.md
python3 ru/ru-ste-lint.py ru/samples/baseline.md ru/samples/utr.md
```

GitHub Actions is disabled at the account level for the account that hosts this
repository, so no pull request here gets a check run. Run the gate locally and
quote the output, and install both hooks:

```sh
ln -s ../../hooks/pre-commit .git/hooks/pre-commit
ln -s ../../hooks/pre-push   .git/hooks/pre-push
```

Expected scores (from `RESULTS.md`):

| Text | Score | Longest sentence |
| --- | --- | --- |
| `en/samples/baseline.md` | 33.12 | 49 words |
| `en/samples/ste.md` | 0.83 | 14 words |
| `ru/samples/baseline.md` | 34.19 | 27 words |
| `ru/samples/utr.md` | 0.00 | 11 words |

If your numbers differ and you did not intend to change scoring, something
broke. Do not report the work as done without running the tests and quoting
the numbers you saw — that is the project's verification gate.

## Scope

This kit is a smoke alarm for technical prose, not a grammar checker, not a
style guide for fiction, and not a replacement for an editor. Rules that help
a maintenance manual may hurt an essay. Keep the tool in its lane.
