#!/usr/bin/env python3
"""Score an eval run produced by run.py.

Reads a directory of files named <task>__<condition>.md, scores each file with
the linter for its language, and reports the mean per condition.

A file that does not match that pattern is skipped and named on stderr. A silent
skip would lower n and change the mean with nothing in the report to show it.

The language comes from the task prefix: en-* uses en/ste-lint.py, ru-* uses
ru/ru-ste-lint.py.

Usage:
    python3 evals/score.py DIRECTORY [--json]

Exit codes: 0 done, 2 bad arguments or unreadable directory.
Standard library only.
"""

import importlib.util
import json
import pathlib
import re
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^(?P<task>(?P<lang>en|ru)-[^_]+)__(?P<condition>[a-z0-9_]+)\.md$")
CONDITION_ORDER = ["bare", "plain", "banlist", "skill"]


def load(relpath, name):
    path = ROOT / relpath
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load %s" % path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect(directory):
    """Return (rows, skipped), where skipped holds the names that did not match."""
    rows = []
    skipped = []
    linters = {}
    for path in sorted(pathlib.Path(directory).iterdir()):
        match = NAME_RE.match(path.name)
        if match is None:
            if path.is_file():
                skipped.append(path.name)
            continue
        lang = match.group("lang")
        if lang not in linters:
            relpath = "en/ste-lint.py" if lang == "en" else "ru/ru-ste-lint.py"
            linters[lang] = load(relpath, "lint_" + lang)
        result = linters[lang].lint(path.read_text(encoding="utf-8"))
        rows.append(
            {
                "task": match.group("task"),
                "condition": match.group("condition"),
                "lang": lang,
                "words": result["words"],
                "score": result["total_per100w"],
                "max_sentence": result["longest_sentence_words"],
            }
        )
    return rows, skipped


def summarise(rows):
    summary = {}
    for lang in sorted({row["lang"] for row in rows}):
        per_condition = {}
        for condition in sorted({r["condition"] for r in rows if r["lang"] == lang}):
            scores = [r["score"] for r in rows if r["lang"] == lang and r["condition"] == condition]
            per_condition[condition] = {
                "n": len(scores),
                "mean": round(statistics.fmean(scores), 2),
                "median": round(statistics.median(scores), 2),
                "worst": round(max(scores), 2),
            }
        summary[lang] = per_condition
    return summary


def order(conditions):
    known = [c for c in CONDITION_ORDER if c in conditions]
    return known + sorted(c for c in conditions if c not in CONDITION_ORDER)


def report(rows, summary, stream=None, skipped=None):
    stream = sys.stdout if stream is None else stream
    for row in rows:
        print(
            "{task:24} {condition:10} words={words:5d} score={score:6.2f} maxsent={max_sentence:3d}".format(**row),
            file=stream,
        )
    print("", file=stream)
    for lang in sorted(summary):
        print("[%s] mean score per condition, lower is cleaner" % lang, file=stream)
        width = max([10] + [len(c) for c in summary[lang]])
        for condition in order(summary[lang]):
            stats = summary[lang][condition]
            print(
                "  {c:<{w}} n={n:2d} mean={mean:6.2f} median={median:6.2f} worst={worst:6.2f}".format(
                    c=condition, w=width, **stats
                ),
                file=stream,
            )
    print("", file=stream)
    if skipped:
        print(
            "Skipped %d file(s) that do not match <task>__<condition>.md: %s"
            % (len(skipped), ", ".join(skipped)),
            file=stream,
        )
    print("Score measures register, not correctness. Read the outputs too.", file=stream)


def main(argv):
    args = [a for a in argv if not a.startswith("-")]
    as_json = "--json" in argv
    unknown = [a for a in argv if a.startswith("-") and a != "--json"]
    if unknown or len(args) != 1:
        print("usage: score.py DIRECTORY [--json]", file=sys.stderr)
        return 2
    directory = pathlib.Path(args[0])
    if not directory.is_dir():
        print("score.py: not a directory: %s" % directory, file=sys.stderr)
        return 2
    rows, skipped = collect(directory)
    for name in skipped:
        print(
            "score.py: skipped file that does not match <task>__<condition>.md: %s" % name,
            file=sys.stderr,
        )
    if not rows:
        print("score.py: no files named <task>__<condition>.md in %s" % directory, file=sys.stderr)
        return 2
    summary = summarise(rows)
    if as_json:
        print(
            json.dumps(
                {"rows": rows, "summary": summary, "skipped": skipped},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        report(rows, summary, skipped=skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
