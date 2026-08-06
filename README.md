[![CI](https://github.com/ameoblius-ai/anti-slop-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/ameoblius-ai/anti-slop-kit/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Dependabot](https://img.shields.io/badge/dependabot-enabled-blue.svg)](https://github.com/ameoblius-ai/anti-slop-kit/network/updates)

# anti-slop-kit

Controlled-language writing skills and deterministic linters that remove AI slop
from technical prose. Two languages: English (ASD-STE100 mechanics) and Russian
(GOST R 58049-2017, clause 8.2.3).

A skill tells the model how to write. A linter proves whether the model did it.
The linter is the part most anti-slop advice leaves out.

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Quick Install

Install via pip:

    pip install anti-slop-kit

### Development Install

Clone and install in development mode:

    git clone https://github.com/ameoblius-ai/anti-slop-kit.git
    cd anti-slop-kit
    pip install -e ".[dev]"
    pip install pre-commit
    pre-commit install

### Verify Installation

Check if package is installed:

    anti-slop-kit --version

Or run tests:

    python -m pytest tests/


## Usage

See the [documentation](docs/) for detailed usage examples and API reference.

### Quick Start

1. Install the package
2. Import the main module
3. Use the analysis functions
4. Review the results

For more examples, check the [examples directory](examples/) and [API documentation](docs/api.md).

### Configuration

Create a configuration file to customize behavior. See [configuration guide](docs/configuration.md) for details.

### Command Line

Use the CLI tool for batch processing and automation. Run `anti-slop --help` for available commands.

## Who this is for

**Use this for:** API docs, runbooks, release notes, incident reports, onboarding
docs, support macros, changelogs — any text where a reader must act correctly on
the first read. Also useful as a gate on LLM-generated documentation.

**Do not use this for:** essays, marketing copy where voice is the point, fiction,
or anything where rhythm and register matter more than being parsed correctly.
The sentence-length and semicolon rules will fight you, and they should: they come
from maintenance-manual standards, not from general writing advice.

**What the score means:** violations per 100 words. A smoke alarm, not a grade.
The useful signal is the delta across revisions of the same text. An absolute
threshold means something only once a team picks one for a document class — the
CI samples gate at 2, and that is a convention, not a law.

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
examples/                five before/after pairs with measured scores
tests/                   unittest suite, standard library only
scripts/check.sh         the whole gate: tests, then the sample linters
hooks/pre-commit         git hook that blocks a commit above the limit
hooks/pre-push           git hook that runs the whole gate before a push
.pre-commit-config.example.yaml
RESULTS.md               measured scores and their limits
CONTRIBUTING.md          how to contribute rules, tests, and fixes
demo.sh                  one-command demo: samples, findings, tests
```

## Quick start

```sh
git clone https://github.com/ameobius-ai/anti-slop-kit
cd anti-slop-kit

./demo.sh
```

Or step by step:

```sh
python3 en/ste-lint.py en/samples/baseline.md en/samples/ste.md
python3 ru/ru-ste-lint.py ru/samples/baseline.md ru/samples/utr.md

python3 -m unittest discover -s tests
```

No dependencies. Python 3.9 or later. The linters use the standard library only,
because a skill directory is copied as a unit and must keep working after the copy.

## The gate

One entry point runs everything this project checks:

```sh
bash scripts/check.sh          # tests, then the sample linters
bash scripts/check.sh tests
bash scripts/check.sh lint
```

`.github/workflows/ci.yml` calls the same script, so a green local run and a
green CI run cannot disagree about what they checked.

GitHub Actions is disabled at the account level for the account that hosts this
repository: `POST /actions/workflows/ci.yml/dispatches` answers 422, `Actions
has been disabled for this user`. Until that is lifted the workflow never runs
here, and the local hooks are the only enforcement that exists:

```sh
ln -s ../../hooks/pre-commit .git/hooks/pre-commit   # blocks one bad file
ln -s ../../hooks/pre-push   .git/hooks/pre-push     # blocks a bad push
```

The workflow file stays in the tree because a fork with Actions enabled runs it
unchanged.

## Score

The score is violations per 100 words. Lower is cleaner.

| Text | Score | Longest sentence |
| --- | --- | --- |
| `en/samples/baseline.md` | 33.12 | 49 words |
| `en/samples/ste.md` | 0.83 | 14 words |
| `ru/samples/baseline.md` | 34.19 | 27 words |
| `ru/samples/utr.md` | 0.00 | 11 words |

Read `RESULTS.md` before you quote these numbers. Two texts per language is a
smoke test, not a benchmark. `evals/` holds the harness for a real measurement
across six tasks per language and four prompt conditions. First live runs were
executed on 2026-08-04 (EN 23/24 cells, RU 24/24, via a local OpenAI-compatible
gateway); see `evals/README.md` for the setup and scores. No number on this page
comes from it yet.

## Russian is a first-class citizen

The RU side is not a translation of the EN side. English plain-language tooling
is crowded; a deterministic Russian linter is rare. It targets канцелярит,
отглагольные существительные, цепочки родительного падежа and причастные
обороты, plus typography (ёлочки, тире), against ГОСТ Р 58049-2017 §8.2.3 (УТР).
It carries its own lexicon, its own morphology handling (ё-folding, a participle
stoplist), and its own samples and scores.

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

## Explain a score

A score says where the problems are, not only how many. `--explain` prints one
line per finding: line number, rule, matched text, and the suggested fix.

```sh
python3 en/ste-lint.py --explain docs/draft.md
```

```text
draft.md                     words=  412 total=   9 per100w=  2.18 maxsent= 24
  L14    passive_voice         'is handled'                           Name the actor. Use active voice.
  L22    banned_word           'utilize'                              Use 'use' instead.
```

## Split the score

One total hides two different problems. `--breakdown` prints them apart: `slop`
counts banned words, marketing adjectives, AI filler and hedges; `cl` counts the
controlled-language mechanics, which are sentence length, passive voice,
nominalizations and participle chains.

```sh
python3 ru/ru-ste-lint.py --breakdown ru/samples/baseline.md
python3 en/ste-lint.py --only slop docs/draft.md
```

```text
baseline.md            words=  117 total=  40 per100w= 34.19 maxsent= 27 slop=  15 cl=  25
```

The split changes what you do next. In `ru/samples/baseline.md`, 25 of the 40
findings are structural, so a search for banned words finds 15 and misses the
larger half. `--only slop` and `--only cl` gate on one component alone, which
helps when a document class tolerates long sentences but not marketing language.

## GitHub Actions annotations

`--format github` emits workflow commands, so findings appear inline on pull
request diffs when the linter runs in GitHub Actions:

```yaml
- name: Lint prose
  run: python3 en/ste-lint.py --format github --max 5 docs/*.md
```

Each finding becomes a `::warning` annotation with file, line, rule name and
suggested fix. Combine with `--max` to fail the job and annotate at once.

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

## Performance
Benchmarks and optimization information for anti-slop-kit.

### Benchmarks
Performance varies by file size:
- Small files (<10KB): <0.1s, ~50MB memory
- Medium files (10-100KB): 0.1-1s, ~100MB memory
- Large files (100KB-1MB): 1-10s, ~200MB memory
- Very large files (>1MB): 10s+, ~500MB memory

### Optimization Tips
1. Exclude large directories (node_modules, .git, dist)
2. Enable parallel processing for multiple files
3. Use incremental analysis with git diff
4. Filter by file types to skip irrelevant files
5. Process in batches for better memory management

### Resource Usage
- CPU: 1 core for single file, multiple cores for batch
- Memory: 50MB base + 10-50MB per file
- Disk: Read-only analysis, minimal writes

### Performance Tuning
Configure in .anti-slop.yaml: parallel, workers, chunk_size, cache

### Known Limitations
- Large files (>10MB) may cause high memory usage
- Complex regex patterns slow down analysis
- Network features add latency

For more details, see performance benchmarks in the test suite.
## Security

### Security Features

anti-slop-kit includes several security-focused features:

- **Dependency Scanning**: Automated checks for known vulnerabilities
- **Code Analysis**: Detection of potentially unsafe patterns
- **Input Validation**: Sanitization of user-provided content
- **Secure Defaults**: Conservative security settings out of the box

### Best Practices

Follow these security best practices when using anti-slop-kit:

1. **Keep Dependencies Updated**: Regularly update anti-slop-kit and its dependencies
2. **Review Configuration**: Audit your `.anti-slop.yaml` for sensitive data
3. **Use Virtual Environments**: Isolate dependencies to prevent conflicts
4. **Monitor Logs**: Check analysis logs for suspicious patterns
5. **Limit Permissions**: Run with minimal required permissions
6. **Secure Configuration Files**: Don't commit secrets to version control

### Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT open a public issue**
2. Email: security@ameoblius.ai
3. Include detailed description and reproduction steps
4. Allow reasonable time for response and fix

We will acknowledge receipt within 48 hours and provide a timeline for fixing the issue.

### Security Considerations

- **Data Privacy**: anti-slop-kit processes text locally, no data sent to external servers
- **File Access**: Only reads files you explicitly specify
- **Network Access**: Minimal network requests (only for dependency updates if enabled)
- **Code Execution**: Does not execute analyzed code, only parses and analyzes

### Dependency Security

anti-slop-kit uses Dependabot for automated dependency updates:

- Weekly security scans
- Automatic PRs for security updates
- Manual review required before merging

For production use, consider:
- Pinning dependency versions
- Running `pip-audit` regularly
- Using lock files (requirements.txt or Pipfile.lock)

### Security Updates

Security updates are released as soon as possible after vulnerability discovery.
Subscribe to GitHub releases or watch the repository for security announcements.

For more information, see [SECURITY.md](SECURITY.md).
## Contributing

See `CONTRIBUTING.md` for the ground rules (standard library only, no shared
modules between linters, a test in the same commit as a rule change) and how to
add a banned word or report a false positive.

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
