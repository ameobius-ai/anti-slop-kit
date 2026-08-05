# Skill eval suite

The scores in `RESULTS.md` come from two hand-written texts per language. That
is a smoke test. This directory holds the tools to measure for real.

**Status: first full run executed 2026-08-04** via a local OpenAI-compatible gateway
(cliproxy at `127.0.0.1:8317`, key `proxypal-local`, model `deepseek-v4-flash-free`).

en covered 23/28 cells with one timeout on `en-05__banlist`. ru covered 24/28.
The tools have not generated the 07-task cells yet. The means below come
from the six-task grid. Mean per variant (lower is cleaner):

| lang | bare | plain | banlist | skill |
|---|---|---|---|---|
| en | 5.78 | 7.89 | 5.18 | **2.64** |
| ru | 10.73 | 10.70 | 9.59 | **7.22** |

> The ru row is **pre-fix** (linter before PR #34). After the technical-register
> allowlist (issue #33), re-scoring the same outputs gives ru: bare 10.73, plain 6.80,
> banlist 3.63, skill **2.00**. RU skill now sits at parity with EN (2.00 vs 2.64).

Scaffolding note: the author's setup had no external network or API key. The
runner speaks OpenAI-compatible, so any endpoint works.

## Design

Seven tasks per language, four prompt variants, one model per run.

The four variants separate three claims that are easy to confuse:

| Variant | Added to the prompt | Answers |
| --- | --- | --- |
| `bare` | nothing | What does the model do by default? |
| `plain` | "Write clearly and concisely." | Does any rule help? |
| `banlist` | a list of words to avoid | Is the skill better than a word list? |
| `skill` | the full SKILL.md | Does the skill add anything on top? |

Without `plain` and `banlist`, a large delta proves nothing. It then shows only
that some prompt beats none.

## Run it

```sh
export ANTI_SLOP_API_KEY=...
export ANTI_SLOP_API_BASE=https://api.example.com/v1   # OpenAI-compatible
python3 evals/run.py --model MODEL_NAME --lang en --out evals/outputs
python3 evals/score.py                            # scores evals/tasks fixtures
```

Against a local OpenAI-compatible gateway (no external network or key needed.
This stack ships a gateway):

```sh
export ANTI_SLOP_API_KEY=proxypal-local
export ANTI_SLOP_API_BASE=http://127.0.0.1:8317/v1   # cliproxy
python3 evals/run.py --model deepseek-v4-flash-free --lang en --out evals/outputs-en
python3 evals/score.py                            # scores evals/tasks fixtures
```

`run.py` writes one file per cell named `<task>__<condition>.md` under
`--out`. `score.py` is a separate lane: it scores the committed
`evals/tasks/<id>/` fixtures (source.md vs rewritten.md) for kept facts and
prints a JSON summary to stdout (`--json-out`, `--markdown-out`, `--strict`
optional).

## What a run leaves behind

The scoring copies in `--out` are working files. The scorer re-scores, edits,
and overwrites them. Every run also writes a record. Keep that record untouched
and commit it:

```
evals/runs/20260804T153000Z__en__deepseek-v4-flash-free/
    manifest.json         model, endpoint, prompt digests, one entry per cell
    prompts/skill.txt     the exact system prompt that was sent
    raw/<cell>.json       the unedited response body
    outputs/<cell>.md     the answer as generated
```

The record answers what a score cannot say: which prompt produced this text,
from which model, on which endpoint, and what the API returned. The manifest
stores each prompt whole and by digest, so two runs compare by digest without a
file diff. The runner never writes the API key. Only the scheme, host, and path
of the endpoint reach the manifest. The runner strips a key from any query
string or userinfo.

The manifest lists every cell, including cells that produced no new text. It
marks an existing output file as `skipped_existing` and a failed call as
`failed` with its error. Before this record existed, a resumed run that wrote
nothing looked like a run that never happened. If a run generates nothing at
all, `run.py` says so on stderr.

The first live run, on 2026-08-04, predates all of this. The team kept only its
scored copies, and they are gone now. Nobody can re-score those numbers against
a newer linter. The authors wrote the before/after pairs in `examples/` by hand
instead of copying real `bare` output. This record closes that gap. It also
explains why run scores here carry a date and a model instead of standing as a
property of the kit.

## Read the output honestly

- The linter measures register, not correctness. A variant can win on score and
  lose on facts. Read a sample of the outputs.

- Report the model name and date. A result from one model does not transfer.
  The source study behind this kit found the ban-list variant helped one model
  and barely moved another.

- Run each cell three times (`--repeat 3`). Single samples from a sampling
  process are noise. The repeats land as separate cells (`__r2`, `__r3`), so
  the spread stays visible at write time.

- Check task-level results, not only the mean. In the source study the skill
  made one task of six worse.

## Task en-07: System Prompt

Added 2026-08-05. Tests prompt quality for CI/CD code review agents. It scores
how well the prompt defines the role, the review criteria, and the output
format.
