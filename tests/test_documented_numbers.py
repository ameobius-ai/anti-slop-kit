#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every number a document states about this repository, checked against code.

A document that states a number is making a claim, and claims rot. "112 tests"
was hand-written into two files, the suite grew three times in three merges,
and every copy went wrong at once. Two stale sample scores sat in README and
CONTRIBUTING for days. A reader cannot tell a stale number from a real
regression, which makes a wrong number worse than no number.

The gallery in examples/ raised the stakes: each pair states seven numbers,
including the slop and cl components, and nothing checked any of them. Those
tables are the kit's evidence that the rewrite works. Unverified evidence is
just prose.

This file owns that concern. test_repo_integrity.py owns bytes.
"""

import os
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

DOC_FILES = ("README.md", "AGENTS.md", "CONTRIBUTING.md")
EVALS_README = pathlib.Path("evals/README.md")

# "112 tests" in prose. The count belongs to the suite, not to a document.
HARDCODED_COUNT = re.compile(r"\b\d+\s+tests\b")

# | `ru/samples/baseline.md` | 34.19 | 27 words |
SCORE_ROW = re.compile(
    r"^\|\s*`((?:en|ru)/samples/[A-Za-z0-9_.-]+\.md)`\s*\|"
    r"\s*([0-9]+(?:\.[0-9]+)?)\s*\|"
    r"\s*([0-9]+)\s*words\s*\|"
)

# | `before.md` | 134 | 22 | 16.42 | 38 | 11 | 11 |
# Words, Total, Per 100 words, Longest sentence, slop, cl.
GALLERY_ROW = re.compile(
    r"^\|\s*`([A-Za-z0-9_.-]+\.md)`\s*\|"
    r"\s*([0-9]+)\s*\|"
    r"\s*([0-9]+)\s*\|"
    r"\s*([0-9]+(?:\.[0-9]+)?)\s*\|"
    r"\s*([0-9]+)\s*\|"
    r"\s*([0-9]+)\s*\|"
    r"\s*([0-9]+)\s*\|$"
)

# | `bare` | none | What does the model do by default? |
CONDITION_ROW = re.compile(r"^\|\s*`([a-z]+)`\s*\|")

# "en 23/24 cells", "ru 24/24". The denominator is a claim about the grid.
CELL_FRACTION = re.compile(r"\b([0-9]+)/([0-9]+)\b")

FIELDS = ("words", "total", "per100w", "maxsent", "slop", "cl")


def linter_for(sample):
    """Russian samples live under ru/ or in a gallery pair named ru-*."""
    parts = pathlib.PurePath(sample).parts
    russian = parts[0] == "ru" or (len(parts) > 1 and parts[1].startswith("ru-"))
    return "ru/ru-ste-lint.py" if russian else "en/ste-lint.py"


def measure(sample):
    """Score one file and return every number the documents might state.

    Always runs with --breakdown: the gallery tables carry the slop and cl
    components, and a second code path for the two-number tables would be a
    second thing to keep in step.
    """
    path = ROOT / sample
    if not path.is_file():
        raise AssertionError("%s does not exist" % sample)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run(
        [sys.executable, str(ROOT / linter_for(sample)), "--breakdown", str(path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    out = proc.stdout.decode("utf-8", "replace")
    numbers = {}
    for field in FIELDS:
        found = re.search(re.escape(field) + r"=\s*([0-9]+(?:\.[0-9]+)?)", out)
        if not found:
            raise AssertionError(
                "cannot read %s from the linter output for %s: %r"
                % (field, sample, out))
        numbers[field] = found.group(1)
    return numbers


def doc_lines(name):
    path = ROOT / name
    if not path.is_file():
        return []
    return list(enumerate(path.read_text(encoding="utf-8").splitlines(), 1))


class TestCounts(unittest.TestCase):
    def test_no_document_hardcodes_a_test_count(self):
        for name in DOC_FILES:
            for number, line in doc_lines(name):
                found = HARDCODED_COUNT.search(line)
                self.assertIsNone(
                    found,
                    "%s:%d states a test count (%r). Say 'the unittest suite' "
                    "instead: the number goes stale on the next merge."
                    % (name, number, found.group(0) if found else ""))


class SampleScores(unittest.TestCase):
    """The two-number tables in the top-level documents."""

    def test_score_tables_match_the_linters(self):
        checked = 0
        for name in DOC_FILES:
            for number, line in doc_lines(name):
                row = SCORE_ROW.match(line.strip())
                if not row:
                    continue
                sample, claimed, claimed_longest = row.groups()
                actual = measure(sample)
                self.assertAlmostEqual(
                    float(claimed), float(actual["per100w"]), places=2,
                    msg="%s:%d says %s scores %s; the linter says %s"
                        % (name, number, sample, claimed, actual["per100w"]))
                self.assertEqual(
                    claimed_longest, actual["maxsent"],
                    "%s:%d says %s has a %s-word longest sentence; the linter "
                    "says %s" % (name, number, sample, claimed_longest,
                                 actual["maxsent"]))
                checked += 1
        self.assertGreaterEqual(
            checked, 4,
            "found %d score rows to check; the regex has stopped matching the "
            "tables" % checked)


class GalleryScores(unittest.TestCase):
    """The seven numbers each examples/*/notes.md states about its pair.

    The gallery is the kit's public evidence: five before/after pairs with a
    measured drop. The numbers were produced by hand at authoring time and
    would go stale the first time a lexicon entry lands, exactly like the
    sample scores did. The slop column matters most: every after file claims
    slop=0, and that claim is what makes `--only slop --max 0` credible as a
    gate.
    """

    @classmethod
    def setUpClass(cls):
        cls.notes = sorted((ROOT / "examples").glob("*/notes.md"))

    def test_the_gallery_is_found(self):
        """An empty glob would make the checks below vacuous."""
        self.assertGreaterEqual(
            len(self.notes), 5,
            "found %d notes files under examples/" % len(self.notes))

    def test_every_pair_states_two_rows(self):
        """A pair with one row is a table someone edited halfway."""
        for path in self.notes:
            rows = [GALLERY_ROW.match(line.strip())
                    for line in path.read_text(encoding="utf-8").splitlines()]
            names = [row.group(1) for row in rows if row]
            self.assertEqual(
                len(names), 2,
                "%s states %d score rows, expected before and after: %r"
                % (path.relative_to(ROOT), len(names), names))

    def test_gallery_tables_match_the_linters(self):
        checked = 0
        for path in self.notes:
            pair = path.parent.name
            rel = path.relative_to(ROOT)
            for number, line in enumerate(
                    path.read_text(encoding="utf-8").splitlines(), 1):
                row = GALLERY_ROW.match(line.strip())
                if not row:
                    continue
                sample = "examples/%s/%s" % (pair, row.group(1))
                claimed = dict(zip(FIELDS, row.groups()[1:]))
                actual = measure(sample)
                for field in FIELDS:
                    if field == "per100w":
                        self.assertAlmostEqual(
                            float(claimed[field]), float(actual[field]), places=2,
                            msg="%s:%d says %s scores %s per 100 words; the "
                                "linter says %s" % (rel, number, sample,
                                                    claimed[field], actual[field]))
                    else:
                        self.assertEqual(
                            claimed[field], actual[field],
                            "%s:%d says %s has %s=%s; the linter says %s"
                            % (rel, number, sample, field, claimed[field],
                               actual[field]))
                checked += 1
        self.assertGreaterEqual(
            checked, 10,
            "checked %d gallery rows; the regex has stopped matching the "
            "tables" % checked)

    def test_every_after_file_has_no_slop_left(self):
        """The gallery's central claim, checked against the linter directly.

        Stated in examples/README.md and in the project status: the remaining
        findings in every after file are controlled-language mechanics, never
        banned words or filler. If that stops being true the gallery is
        arguing for something it no longer demonstrates.
        """
        for path in self.notes:
            after = path.parent / "after.md"
            if not after.is_file():
                matches = sorted(path.parent.glob("after*.md"))
                self.assertTrue(matches, "%s has no after file" % path.parent.name)
                after = matches[0]
            sample = str(after.relative_to(ROOT))
            self.assertEqual(
                measure(sample)["slop"], "0",
                "%s still carries slop findings" % sample)


class EvalGrid(unittest.TestCase):
    """The cell counts in evals/README.md describe a grid that exists on disk.

    "en 23/24 cells" is two claims: how many cells were generated, and how big
    the grid is. The second is checkable. It went unchecked, and three
    documents state 24 while examples/ carries an incident-report pair that no
    task file backs, so the grid and the gallery already disagree about what
    the kit measures.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / EVALS_README).read_text(encoding="utf-8")
        cls.conditions = [CONDITION_ROW.match(line.strip()).group(1)
                          for line in cls.text.splitlines()
                          if CONDITION_ROW.match(line.strip())]

    def tasks(self, lang):
        return sorted((ROOT / "evals" / "tasks").glob("%s-*.md" % lang))

    def test_the_conditions_table_is_read(self):
        self.assertEqual(sorted(set(self.conditions)),
                         ["banlist", "bare", "plain", "skill"],
                         "read conditions %r from %s" % (self.conditions,
                                                         EVALS_README))

    def test_both_languages_have_the_same_number_of_tasks(self):
        """A lopsided grid makes the per-language means incomparable."""
        self.assertEqual(len(self.tasks("en")), len(self.tasks("ru")),
                         "en has %d tasks, ru has %d"
                         % (len(self.tasks("en")), len(self.tasks("ru"))))
        self.assertGreater(len(self.tasks("en")), 0, "no task files found")

    def test_the_stated_cell_count_matches_the_task_files(self):
        expected = len(self.tasks("en")) * len(set(self.conditions))
        fractions = CELL_FRACTION.findall(self.text)
        self.assertTrue(fractions, "%s states no cell counts" % EVALS_README)
        for done, total in fractions:
            self.assertEqual(
                int(total), expected,
                "%s says the grid holds %s cells; %d task files times %d "
                "conditions is %d" % (EVALS_README, total,
                                      len(self.tasks("en")),
                                      len(set(self.conditions)), expected))
            self.assertLessEqual(
                int(done), int(total),
                "%s reports %s of %s cells generated"
                % (EVALS_README, done, total))


if __name__ == "__main__":
    unittest.main()
