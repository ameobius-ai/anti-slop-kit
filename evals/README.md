# Skill evaluation harness

The scores in `RESULTS.md` come from two hand-written texts per language. That
is a smoke test. This directory holds the harness for a real measurement.

**Status: scaffolding. No run has been executed yet.** `score.py` works and is
tested. `run.py` needs network access and a model endpoint, which the authoring
environment did not have. Nothing in `RESULTS.md` comes from this directory.

## Design

Six tasks per language, four conditions, one model per run.

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

`run.py` writes one file per cell named `<task>__<condition>.md`. `score.py`
reads that naming convention, scores every file with the linter for its
language, and reports the mean per condition.

## Read the output honestly

- The linter measures register, not correctness. A condition can win on score
  and lose on facts. Read a sample of the outputs.
- Report the model name and date. A result from one model does not transfer;
  the source experiment this kit builds on found the ban-list condition helped
  one model and barely moved another.
- Run each cell three times. Single samples from a sampling process are noise.
- Check task-level results, not only the mean. In the source experiment the
  skill made one task of six worse.
