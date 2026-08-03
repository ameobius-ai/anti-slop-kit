#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Byte-level checks over every text file in the repository.

A corrupted REPLACE key in the Russian linter survived several commits:
the file parsed, every test passed, and the rule it belonged to had
silently stopped working. The only visible trace was a byte count.

The guards in test_linters.py cover five named files. These cover the
whole tree, so a new file is protected the day it is added rather than
the day someone remembers to list it.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules"}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".ico",
                   ".woff", ".woff2", ".pyc"}


def text_files():
    """Every tracked-looking text file, sorted for a stable failure order."""
    out = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        out.append(path)
    return out


class RepositoryBytes(unittest.TestCase):
    """These run on the working tree, so they also guard uncommitted edits."""

    @classmethod
    def setUpClass(cls):
        cls.files = text_files()

    def test_the_walk_finds_the_repository(self):
        """A silent empty walk would make every other check vacuous."""
        names = {p.name for p in self.files}
        self.assertIn("ste-lint.py", names)
        self.assertIn("ru-ste-lint.py", names)
        self.assertGreater(len(self.files), 10)

    def test_every_file_is_valid_utf8(self):
        for path in self.files:
            rel = path.relative_to(ROOT)
            try:
                path.read_bytes().decode("utf-8")
            except UnicodeDecodeError as exc:
                self.fail("%s is not valid UTF-8: %s" % (rel, exc))

    def test_no_file_carries_a_replacement_character(self):
        """U+FFFD is a byte that was lost in an edit, not a character."""
        for path in self.files:
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count("\\ufffd"), 0,
                             "%s carries U+FFFD" % path.relative_to(ROOT))

    def test_no_file_uses_carriage_returns(self):
        """CRLF breaks the linters' line numbers and the hook's diffing."""
        for path in self.files:
            self.assertNotIn(b"\\r", path.read_bytes(),
                             "%s uses CR line endings" % path.relative_to(ROOT))

    def test_every_file_ends_with_a_newline(self):
        """A missing final newline turns any later edit into a two-line diff.

        Trailing blank lines are not checked. That is a style preference,
        and this file is for defects, not taste.
        """
        for path in self.files:
            raw = path.read_bytes()
            if not raw:
                continue
            self.assertTrue(raw.endswith(b"\\n"),
                            "%s has no final newline" % path.relative_to(ROOT))


if __name__ == "__main__":
    unittest.main()
