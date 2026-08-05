# tools/

JSON wrappers around the two linters, built for agent harnesses.

The linters in `en/` and `ru/` are the engine. These wrappers expose
that engine as tools an agent can call: one JSON object in, one JSON
object out, no prose on stdout.

Rule 1 of AGENTS.md applies here too: standard library only. A wrapper
with a dependency stops working the day the harness changes.

## The four tools

| Tool | Entry point | What it does |
|------|-------------|--------------|
| `lint_file` | `tools/aslint/lint_tool.py FILE [FILE ...]` | Lint files, one result per file. |
| `lint_text` | `tools/aslint/lint_tool.py --stdin` | Lint text from stdin. |
| `validate_rewrite` | `tools/aslint/rewrite_tool.py ORIGINAL.md REWRITE.md` | Accept or reject a rewrite. |
| `transmit_check` | `tools/aslint/transmit_check.py SOURCE.md TRANSMITTED.md` | Check what survived one hop. |

Language is auto-detected per input: Cyrillic routes to the Russian
linter, everything else to the English one. `--lang ru` or `--lang en`
overrides detection.

## Contract

- stdout carries exactly one JSON object per run. Diagnostics go to
  stderr. A parser never meets prose.
- Exit codes: 0 ran and passed, 1 ran and failed its check, 2 bad
  arguments or unreadable input.
- Deterministic. The same input twice gives the same output. No
  network, no clock, no randomness.
- `validate_rewrite` does not generate rewrites. Generation belongs to
  the model; the tool only measures what the model produced. Per
  PURPOSE.md the LLM stays outside the tool.

`tools/hermes_registry.json` lists the four tools and this contract in
machine readers. The tests in `tests/test_hermes_tools.py` keep the
registry honest.

## validate_rewrite

A rewrite passes when both hold:

1. the score does not rise: rewrite total per 100 words is at most the
   original's;
2. nothing lossy disappeared: every number, every underscore
   identifier, and every URL in the original still appears in the
   rewrite.

The second condition is the fidelity half. A rewrite that reads better
but drops `restart_window_ms` has changed the meaning, and the tool
rejects it with the missing tokens named in the output.

## transmit_check

The fidelity primitive for a hop in the channel: a source text goes
in, whatever arrived at the next hop goes in, and the tool reports
which bits survived.

Checks:

- `numbers`: counts, offsets, versions from the source;
- `identifiers`: tokens with an underscore (config keys, names);
- `urls`: every link, stripped of trailing punctuation;
- `constraints`: exact strings the caller names with `--require`;
- `ordering`: `--order` tokens keep their relative order.

A hop that loses a number fails the check, and the output names the
missing tokens. This is the building block for measuring drift across
human and robot hops.

## Examples

```sh
python3 tools/aslint/lint_tool.py en/samples/ste.md
python3 tools/aslint/lint_tool.py --stdin < draft.md
python3 tools/aslint/rewrite_tool.py original.md rewrite.md
python3 tools/aslint/transmit_check.py source.md transmitted.md \
    --require "port 8443" --order alpha gamma
```
