"""transmit_check: the fidelity primitive for a hop in the channel.

Given a source text and what arrived after one hop (a human rewrite, a
robot re-expression, a summarizer), report which bits survived:

- numbers: counts, offsets, versions;
- identifiers: tokens with an underscore (config keys, function names);
- urls: every link, stripped of trailing punctuation;
- constraints: exact strings the caller names via --require;
- ordering: --order tokens must keep their relative order, by first
  occurrence in the transmitted text.

Usage:
    python3 tools/aslint/transmit_check.py SOURCE.md TRANSMITTED.md \
        [--require "exact string" ...] [--order TOKEN ...]

Exit codes: 0 every check passed, 1 something was lost, 2 bad
arguments or unreadable input.
"""

import pathlib
import sys

try:  # package import (tests, harness registry) or direct script run
    from tools.aslint.common import emit, lost_tokens
except ImportError:
    from common import emit, lost_tokens


def _ordering_ok(transmitted, tokens):
    """True when tokens appear in the given order, by first index."""
    pos = -1
    for tok in tokens:
        idx = transmitted.find(tok)
        if idx < 0 or idx < pos:
            return False
        pos = idx
    return True


def transmit_check(source, transmitted, constraints=None, ordered=None):
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


def main(argv):
    files, requires, ordered = [], [], []
    i = 0
    mode = None
    while i < len(argv):
        a = argv[i]
        if a == "--require":
            mode = "require"
        elif a == "--order":
            mode = "order"
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a.startswith("--"):
            emit({"ok": False, "tool": "transmit_check",
                  "error": f"unknown option {a}"})
            return 2
        elif mode == "require":
            requires.append(a)
        elif mode == "order":
            ordered.append(a)
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
