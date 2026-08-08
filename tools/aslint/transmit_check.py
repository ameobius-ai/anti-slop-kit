"""transmit_check: the fidelity primitive for a hop in the channel."""

from __future__ import annotations

import pathlib
import sys
from typing import Any

try:
    from tools.aslint.common import emit, lost_tokens
except ImportError:
    from common import emit, lost_tokens  # type: ignore[no-redef]


def _ordering_ok(transmitted: str, tokens: list[str]) -> bool:
    """True when tokens appear in the given order, by first index."""
    pos = -1
    for tok in tokens:
        idx = transmitted.find(tok)
        if idx < 0 or idx < pos:
            return False
        pos = idx
    return True


def transmit_check(source: str, transmitted: str, constraints: list[str] | None = None,
                   ordered: list[str] | None = None) -> dict[str, Any]:
    """Diff one hop. Returns the tool result dict."""
    constraints = constraints or []
    ordered = ordered or []
    lost = lost_tokens(source, transmitted)
    missing_constraints = [c for c in constraints if c not in transmitted]
    order_ok = _ordering_ok(transmitted, ordered)
    checks = {
        "numbers": not lost["numbers"],
        "identifiers": not lost["identifiers"],
        "urls": not lost["urls"],
        "constraints": not missing_constraints,
        "ordering": order_ok,
    }
    return {
        "ok": True,
        "tool": "transmit_check",
        "passed": all(checks.values()),
        "checks": checks,
        "missing": {
            "numbers": lost["numbers"],
            "identifiers": lost["identifiers"],
            "urls": lost["urls"],
            "constraints": missing_constraints,
        },
        "ordered_tokens": ordered,
    }


def main(argv: list[str]) -> int:
    """Main entry point for transmit check tool."""
    files: list[str] = []
    requires: list[str] = []
    ordered: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--require", "--order"):
            i += 1
            if i >= len(argv):
                emit({"ok": False, "tool": "transmit_check",
                      "error": f"{a} needs a value"})
                return 2
            if a == "--require":
                requires.append(argv[i])
            else:
                ordered.append(argv[i])
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a.startswith("--"):
            emit({"ok": False, "tool": "transmit_check",
                  "error": f"unknown option {a}"})
            return 2
        else:
            files.append(a)
        i += 1
    if len(files) != 2:
        emit({"ok": False, "tool": "transmit_check",
              "error": "usage: transmit_check.py SOURCE.md TRANSMITTED.md"})
        return 2
    try:
        source = pathlib.Path(files[0]).read_text(encoding="utf-8")
        transmitted = pathlib.Path(files[1]).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        emit({"ok": False, "tool": "transmit_check", "error": str(exc)})
        return 2
    result = transmit_check(source, transmitted, requires, ordered)
    emit(result)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
