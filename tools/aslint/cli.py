"""aslint CLI entry point for pyproject console scripts.

Dispatches to the lint tool by default; `--rewrite` and `--transmit-check`
route to the sibling tools so a single `aslint` binary covers the kit.
"""

from __future__ import annotations

import sys

from . import lint_tool, rewrite_tool, transmit_check


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "--rewrite":
        return rewrite_tool.main(argv[1:])
    if argv and argv[0] == "--transmit-check":
        return transmit_check.main(argv[1:])
    return lint_tool.main(argv)


if __name__ == "__main__":
    sys.exit(main())
