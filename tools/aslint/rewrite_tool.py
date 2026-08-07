"""validate_rewrite: score a rewrite against its original."""

from __future__ import annotations

import pathlib
import sys
from typing import Any

try:
    from tools.aslint.common import emit, lint_text, lost_tokens
except ImportError:
    from common import emit, lint_text, lost_tokens  # type: ignore[no-redef]


def validate_rewrite(original: str, rewrite: str, lang: str | None = None) -> dict[str, Any]:
    """Compare two texts. Returns the tool result dict with a verdict."""
    orig_lang, orig = lint_text(original, lang)
    _, rew = lint_text(rewrite, orig_lang)
    lost = lost_tokens(original, rewrite)
    reasons: list[str] = []
    delta = round(rew["total_per100w"] - orig["total_per100w"], 2)
    if delta > 0:
        reasons.append("score rose by %.2f per 100 words" % delta)
    for group in ("numbers", "identifiers", "urls"):
        if lost[group]:
            reasons.append("lost %s: %s" % (group, ", ".join(lost[group])))
    verdict = "reject" if reasons else "accept"
    return {
        "ok": True,
        "tool": "validate_rewrite",
        "lang": orig_lang,
        "verdict": verdict,
        "reasons": reasons,
        "score": {
            "original_per100w": orig["total_per100w"],
            "rewrite_per100w": rew["total_per100w"],
            "delta_per100w": delta,
        },
        "fidelity": lost,
    }


def main(argv: list[str]) -> int:
    """Main entry point for rewrite validation tool."""
    lang: str | None = None
    files: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--lang":
            i += 1
            if i >= len(argv) or argv[i] not in ("en", "ru"):
                emit({"ok": False, "tool": "validate_rewrite",
                      "error": "--lang needs en or ru"})
                return 2
            lang = argv[i]
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a.startswith("--"):
            emit({"ok": False, "tool": "validate_rewrite",
                  "error": f"unknown option {a}"})
            return 2
        else:
            files.append(a)
        i += 1
    if len(files) != 2:
        emit({"ok": False, "tool": "validate_rewrite",
              "error": "usage: rewrite_tool.py ORIGINAL.md REWRITE.md"})
        return 2
    try:
        original = pathlib.Path(files[0]).read_text(encoding="utf-8")
        rewrite = pathlib.Path(files[1]).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        emit({"ok": False, "tool": "validate_rewrite",
              "error": str(exc)})
        return 2
    result = validate_rewrite(original, rewrite, lang)
    emit(result)
    return 0 if result["verdict"] == "accept" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
