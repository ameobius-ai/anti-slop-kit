"""lint_file / lint_text: the linters as JSON-returning agent tools.

Usage:
    python3 tools/aslint/lint_tool.py draft.md [more.md ...]
    python3 tools/aslint/lint_tool.py --stdin < draft.md
    python3 tools/aslint/lint_tool.py --lang ru draft.md
    python3 tools/aslint/lint_tool.py --rules path/to/rules.yaml draft.md

Output: one JSON object on stdout. Exit codes: 0 ran, 2 bad arguments
or unreadable input. Language defaults to auto-detect per input
(Cyrillic routes to the Russian linter).

Importable API: lint_file(path, lang=None), lint_text(text, lang=None).
"""

import pathlib
import sys

try:  # package import (tests, harness registry) or direct script run
    from tools.aslint.common import detect_lang, emit, lint_text, run_linter
    from tools.aslint.custom_rules import (
        load_custom_rules, apply_custom_rules, merge_findings,
        find_custom_rules_files, CustomRulesError
    )
except ImportError:
    from common import detect_lang, emit, lint_text, run_linter
    from custom_rules import (
        load_custom_rules, apply_custom_rules, merge_findings,
        find_custom_rules_files, CustomRulesError
    )


def _slim(result):
    """Keep the fields an agent acts on. Drop the sample excerpts."""
    keys = ("words", "sentences", "total", "total_per100w",
            "slop", "cl", "slop_per100w", "cl_per100w",
            "longest_sentence_words", "findings")
    return {k: result[k] for k in keys if k in result}


def _apply_custom_to_result(result, text, custom_rules):
    """Apply custom rules and merge with built-in findings."""
    if not custom_rules:
        return result
    
    # Get built-in findings
    builtin_findings = result.get('findings', [])
    
    # Apply custom rules
    custom_findings = apply_custom_rules(text, custom_rules)
    
    # Merge findings
    merged_findings = merge_findings(builtin_findings, custom_findings)
    
    # Update result
    result = result.copy()
    result['findings'] = merged_findings
    
    # Recalculate counts if custom findings were added
    if custom_findings:
        custom_count = len(custom_findings)
        result['custom_rules_count'] = custom_count
    
    return result


def lint_file(path, lang=None, custom_rules=None):
    """Lint one file. Returns the tool result dict."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    if lang is None:
        lang = detect_lang(text)
    result = {"ok": True, "tool": "lint_file", "path": str(path),
              "lang": lang, "result": _slim(run_linter(lang, path))}
    
    # Apply custom rules if provided
    if custom_rules:
        result['result'] = _apply_custom_to_result(result['result'], text, custom_rules)
    
    return result


def lint_text_tool(text, lang=None, custom_rules=None):
    """Lint a string. Same shape as lint_file, path is '<text>'."""
    used, result = lint_text(text, lang)
    final_result = {"ok": True, "tool": "lint_text", "path": "<text>",
                    "lang": used, "result": _slim(result)}
    
    # Apply custom rules if provided
    if custom_rules:
        final_result['result'] = _apply_custom_to_result(final_result['result'], text, custom_rules)
    
    return final_result


def main(argv):
    lang, use_stdin, files, rules_paths = None, False, [], []
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
        elif a == "--rules":
            i += 1
            if i >= len(argv):
                emit({"ok": False, "tool": "lint",
                      "error": "--rules needs a path"})
                return 2
            rules_paths.append(argv[i])
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
    
    # Load custom rules if specified or auto-discover
    custom_rules = None
    if rules_paths:
        try:
            custom_rules = load_custom_rules(rules_paths)
        except CustomRulesError as e:
            emit({"ok": False, "tool": "lint", "error": f"custom rules error: {e}"})
            return 2
    else:
        # Auto-discover rules files
        discovered = find_custom_rules_files()
        if discovered:
            try:
                custom_rules = load_custom_rules(discovered)
            except CustomRulesError as e:
                emit({"ok": False, "tool": "lint", "error": f"custom rules error: {e}"})
                return 2
    
    results = []
    try:
        if use_stdin:
            results.append(lint_text_tool(sys.stdin.read(), lang, custom_rules))
        for f in files:
            results.append(lint_file(f, lang, custom_rules))
    except (OSError, UnicodeDecodeError) as exc:
        emit({"ok": False, "tool": "lint", "error": str(exc)})
        return 2
    if not results:
        emit({"ok": False, "tool": "lint",
              "error": "give a file or --stdin"})
        return 2
    
    # Add custom rules info to output if used
    output = {"ok": True, "tool": "lint", "results": results}
    if custom_rules:
        output["custom_rules_loaded"] = len(custom_rules)
    
    emit(output)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
