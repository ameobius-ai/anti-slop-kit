# Skill evaluation harness

The scores in `RESULTS.md` come from two hand-written texts per language. That
is a smoke test. This directory holds the harness for a real measurement.

**Status: first full run executed 2026-08-04** via a local OpenAI-compatible gateway
(cliproxy at `127.0.0.1:8317`, key `proxypal-local`, model `deepseek-v4-flash-free`).
en 23/28 cells (1 timeout on `en-05__banlist`), ru 24/28. The 07-task cells are
not generated yet; the means below come from the six-task grid. Mean per
condition (lower is cleaner):

| lang | bare | plain | banlist | skill |
|---|---|---|---|---|
| en | 5.78 | 7.89 | 5.18 | **2.64** |
| ru | 10.73 | 10.70 | 9.59 | **7.22** |

> The ru row is **pre-fix** (linter before PR #34). After the technical-register
> allowlist (issue #33), re-scoring the same outputs gives ru: bare 10.73, plain 6.80,
> banlist 3.63, skill **2.00** — RU skill at parity with EN (2.00 vs 2.64).

Earlier scaffolding note: the authoring environment had no external network/API key;
the harness itself is OpenAI-compatible, so any endpoint works.

## Design

Seven tasks per language, four conditions, one model per run.

The four conditions exist to separate three different claims that are easy to
confuse:

| Condition | Prompt addition | Answers the question |
| --- | --- | --- |
| `bare` | none | What does the model do by default? |
| `plain` | "Write clearly and concisely." | Does any instruction help? |
| `banlist` | a list of words to avoid | Is the skill better than a word list? |
| `skill` | the full SKILL.md | Does the skill add anything on top? |

Without `plain` and `banlist` a large delta proves nothing: it may only show
that some instruction is better than none.

## Run it

```sh
export ANTI_SLOP_API_KEY=...
export ANTI_SLOP_API_BASE=https://api.example.com/v1   # OpenAI-compatible
python3 evals/run.py --model MODEL_NAME --lang en --out evals/outputs
python3 evals/score.py evals/outputs
```

Against a local OpenAI-compatible gateway (no external network/key — this stack ships one):

```sh
export ANTI_SLOP_API_KEY=proxypal-local
export ANTI_SLOP_API_BASE=http://127.0.0.1:8317/v1   # cliproxy
python3 evals/run.py --model deepseek-v4-flash-free --lang en --out evals/outputs-en
python3 evals/score.py evals/outputs-en
```

`run.py` writes one file per cell named `<task>__<condition>.md`. `score.py`
reads that naming convention, scores every file with the linter for its
language, and reports the mean per condition.

## What a run leaves behind

The scoring copies in `--out` are working files: they get re-scored, edited and
overwritten. Every invocation also writes a record that is meant to stay
untouched and to be committed:

```
evals/runs/20260804T153000Z__en__deepseek-v4-flash-free/
    manifest.json         model, endpoint, prompt digests, one entry per cell
    prompts/skill.txt     the exact system prompt that was sent
    raw/<cell>.json       the unedited response body
    outputs/<cell>.md     the answer as generated
```

The record answers the questions a score cannot: which prompt produced this
text, from which model, on which endpoint, and what the API actually returned.
The prompt is stored whole and by digest, so two runs can be compared without
diffing files. The API key is never written: only the scheme, host and path of
the endpoint reach the manifest, and a key passed in a query string or in
userinfo is stripped.

Every cell appears in `manifest.json`, including the ones that produced no new
text. A cell whose output file already exists is recorded as `skipped_existing`
and a failed call is recorded as `failed` with its error, because a resumed run
that writes nothing used to look exactly like a run that never happened. If a
run generates nothing at all, `run.py` says so on stderr.

The first live run, on 2026-08-04, predates all of this. Only its scored copies
were kept, and they are gone: the numbers above cannot be re-scored against a
newer linter, and the before/after pairs in `examples/` had to be written by
hand instead of taken from real `bare` output. That is the gap this record
closes, and it is why the run scores here are reported with a date and a model
rather than as a property of the kit.

## Read the output honestly

- The linter measures register, not correctness. A condition can win on score
  and lose on facts. Read a sample of the outputs.
- Report the model name and date. A result from one model does not transfer;
  the source experiment this kit builds on found the ban-list condition helped
  one model and barely moved another.
- Run each cell three times (`--repeat 3`). Single samples from a sampling
  process are noise, and the repeats land as separate cells (`__r2`, `__r3`) so
  the spread stays visible instead of being averaged away at write time.
- Check task-level results, not only the mean. In the source experiment the
  skill made one task of six worse.


## Task en-07: System Prompt

Added 2026-08-05. Tests prompt engineering quality for CI/CD code review agents. Measures specificity of role definition, evaluation criteria, and output format.
