"""lint_file / lint_text: the linters as JSON-returning agent tools.

Usage:
    python3 tools/aslint/lint_tool.py draft.md [more.md ...]
    python3 tools/aslint/lint_tool.py --stdin < draft.md
    python3 tools/aslint/lint_tool.py --lang ru draft.md

Output: one JSON object on stdout. Exit codes: 0 ran, 2 bad arguments
or unreadable input. Language defaults to auto-detect per input
(Cyrillic routes to the Russian linter).

Importable API: lint_file(path, lang=None), lint_text(text, lang=None).
"""

import pathlib
import sys

try:  # package import (tests, harness registry) or direct script run
    from tools.aslint.common import detect_lang, emit, lint_text, run_linter
except ImportError:
    from common import detect_lang, emit, lint_text, run_linter


def _slim(result):
    """Keep the fields an agent acts on. Drop the sample excerpts."""
    keys = ("words", "sentences", "total", "total_per100w",
            "slop", "cl", "slop_per100w", "cl_per100w",
            "longest_sentence_words", "findings")
    return {k: result[k] for k in keys if k in result}


def lint_file(path, lang=None):
    """Lint one file. Returns the tool result dict."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    if lang is None:
        lang = detect_lang(text)
    return {"ok": True, "tool": "lint_file", "path": str(path),
            "lang": lang, "result": _slim(run_linter(lang, path))}


def lint_text_tool(text, lang=None):
    """Lint a string. Same shape as lint_file, path is '<text>'."""
    used, result = lint_text(text, lang)
    return {"ok": True, "tool": "lint_text", "path": "<text>",
            "lang": used, "result": _slim(result)}


def main(argv):
    lang, use_stdin, files = None, False, []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--stdin":
            use_stdin = True
        elif a == "--lang":
            i += 1
            if i >= len(argv) or argv[i] not in ("en", "ru"):
                emit({"ok": False, "tool": "lint",
                      "error": "--lang needs en or ru"})
                return 2
            lang = argv[i]
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a.startswith("--"):
            emit({"ok": False, "tool": "lint",
                  "error": f"unknown option {a}"})
            return 2
        else:
            files.append(a)
        i += 1
    results = []
    try:
        if use_stdin:
            results.append(lint_text_tool(sys.stdin.read(), lang))
        for f in files:
            results.append(lint_file(f, lang))
    except (OSError, UnicodeDecodeError) as exc:
        emit({"ok": False, "tool": "lint", "error": str(exc)})
        return 2
    if not results:
        emit({"ok": False, "tool": "lint",
              "error": "give a file or --stdin"})
        return 2
    emit({"ok": True, "tool": "lint", "results": results})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
