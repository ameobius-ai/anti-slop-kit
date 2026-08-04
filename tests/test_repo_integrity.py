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
import os
import pathlib
import re
import subprocess
import sys
import unittest

# Written as code points on purpose. A file about mangled bytes should
# not depend on its own escape sequences surviving every editor and
# transport that touches it.
REPLACEMENT = chr(0xFFFD)
CR = bytes([13])
LF = bytes([10])

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
            self.assertEqual(text.count(REPLACEMENT), 0,
                             "%s carries U+FFFD" % path.relative_to(ROOT))

    def test_no_file_uses_carriage_returns(self):
        """CRLF breaks the linters' line numbers and the hook's diffing."""
        for path in self.files:
            self.assertNotIn(CR, path.read_bytes(),
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
            self.assertTrue(raw.endswith(LF),
                            "%s has no final newline" % path.relative_to(ROOT))


DOC_FILES = ("README.md", "AGENTS.md", "CONTRIBUTING.md")
CI_WORKFLOW = pathlib.Path(".github/workflows/ci.yml")
GATE = pathlib.Path("scripts/check.sh")

# "112 tests" was written into two documents by hand. The suite then grew
# three times in three merges, and every copy of the number went wrong at
# once. Prose cannot hold a count that a test file changes.
HARDCODED_COUNT = re.compile(r"\b\d+\s+tests\b")

# | `ru/samples/baseline.md` | 34.19 | 27 words |
SCORE_ROW = re.compile(
    r"^\|\s*`((?:en|ru)/samples/[A-Za-z0-9_.-]+\.md)`\s*\|"
    r"\s*([0-9]+(?:\.[0-9]+)?)\s*\|"
    r"\s*([0-9]+)\s*words\s*\|"
)
PER100 = re.compile(r"per100w=\s*([0-9]+(?:\.[0-9]+)?)")
MAXSENT = re.compile(r"maxsent=\s*([0-9]+)")


def measure(sample):
    """Run the linter that owns this sample and return (per100w, maxsent)."""
    linter = "ru/ru-ste-lint.py" if sample.startswith("ru/") else "en/ste-lint.py"
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run([sys.executable, str(ROOT / linter), str(ROOT / sample)],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    out = proc.stdout.decode("utf-8", "replace")
    score = PER100.search(out)
    longest = MAXSENT.search(out)
    if not score or not longest:
        raise AssertionError("cannot parse linter output for %s: %r" % (sample, out))
    return float(score.group(1)), int(longest.group(1))


class DocumentedNumbers(unittest.TestCase):
    """Every number a document states about this repository must be current.

    Two classes of number drifted repeatedly: the test count and the sample
    scores. Both were correct when written and wrong one merge later. A
    reader cannot tell a stale number from a real regression, so the number
    is worse than no number at all.
    """

    def test_no_document_hardcodes_a_test_count(self):
        for name in DOC_FILES:
            path = ROOT / name
            if not path.is_file():
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                found = HARDCODED_COUNT.search(line)
                self.assertIsNone(
                    found,
                    "%s:%d states a test count (%r). Say 'the unittest suite' "
                    "instead: the number goes stale on the next merge."
                    % (name, number, found.group(0) if found else ""))

    def test_score_tables_match_the_linters(self):
        """A score table is a claim. Check it against the code that makes it."""
        checked = 0
        for name in DOC_FILES:
            path = ROOT / name
            if not path.is_file():
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                row = SCORE_ROW.match(line.strip())
                if not row:
                    continue
                sample, claimed, claimed_longest = row.group(1), row.group(2), row.group(3)
                actual, actual_longest = measure(sample)
                self.assertAlmostEqual(
                    float(claimed), actual, places=2,
                    msg="%s:%d says %s scores %s; the linter says %.2f"
                        % (name, number, sample, claimed, actual))
                self.assertEqual(
                    int(claimed_longest), actual_longest,
                    "%s:%d says %s has a %s-word longest sentence; the linter "
                    "says %d" % (name, number, sample, claimed_longest, actual_longest))
                checked += 1
        self.assertGreaterEqual(checked, 4,
                                "found %d score rows to check; the regex has "
                                "stopped matching the tables" % checked)


class TheGateIsOneScript(unittest.TestCase):
    """CI and a developer must run the same checks, or green means nothing.

    Before scripts/check.sh, the workflow listed its own commands. The
    local instructions and the workflow disagreed about which samples were
    linted, and neither side could tell.
    """

    def test_the_gate_script_exists(self):
        self.assertTrue((ROOT / GATE).is_file(), "%s is missing" % GATE)

    def test_the_workflow_delegates_to_the_gate(self):
        path = ROOT / CI_WORKFLOW
        self.assertTrue(path.is_file(), "%s is missing" % CI_WORKFLOW)
        text = path.read_text(encoding="utf-8")
        self.assertIn("scripts/check.sh tests", text)
        self.assertIn("scripts/check.sh lint", text)
        self.assertNotIn("unittest discover", text,
                         "%s runs the tests directly instead of through %s"
                         % (CI_WORKFLOW, GATE))

    def test_the_push_hook_runs_the_gate(self):
        """Actions is disabled for this account, so this hook is the gate."""
        path = ROOT / "hooks/pre-push"
        self.assertTrue(path.is_file(), "hooks/pre-push is missing")
        text = path.read_text(encoding="utf-8")
        self.assertIn("check.sh", text)


if __name__ == "__main__":
    unittest.main()
