#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail the gate when source files carry invisible characters.

LLM-generated code has shipped with stray control bytes (a 0x08 backspace
after "TODO" once silenced a whole regex family). Tab, newline and CR are
fine; every other C0 control char and the common zero-width format chars
are not. Standard library only.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCAN_DIRS = ('en', 'ru', 'scripts', 'evals', 'tests')
SUFFIXES = ('.py', '.sh', '.md')

ALLOWED = {0x09, 0x0A, 0x0D}  # tab, LF, CR
INVISIBLE_UNICODE = {
    0x200B,  # zero-width space
    0x200C,  # zero-width non-joiner
    0x200D,  # zero-width joiner
    0x2060,  # word joiner
    0xFEFF,  # BOM / zero-width no-break space
}


def scan(path):
    hits = []
    try:
        text = path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError) as exc:
        return [(1, f'unreadable: {exc}')]
    for lineno, line in enumerate(text.split('\n'), 1):
        for ch in line:
            code = ord(ch)
            if code < 0x20 and code not in ALLOWED:
                hits.append((lineno, f'C0 control char U+{code:04X}'))
            elif code in INVISIBLE_UNICODE:
                hits.append((lineno, f'invisible char U+{code:04X}'))
    return hits


def main():
    problems = []
    for dirname in SCAN_DIRS:
        base = ROOT / dirname
        if not base.is_dir():
            continue
        for path in sorted(base.rglob('*')):
            if not path.is_file() or path.suffix not in SUFFIXES:
                continue
            for lineno, desc in scan(path):
                problems.append(f'{path.relative_to(ROOT)}:{lineno}: {desc}')
    if problems:
        for problem in problems:
            print(problem)
        print(f'\n{len(problems)} invisible-character problem(s) found.')
        return 1
    print('no invisible characters found')
    return 0


if __name__ == '__main__':
    sys.exit(main())
