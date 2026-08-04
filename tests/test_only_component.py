#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for --only, the flag that gates one component of the score.

The split from issue #2 exists so that CI can hold slop at zero while the
controlled-language rules stay advisory. --only moved the threshold correctly
and stopped there: the summary line still printed the combined score, and
--explain still listed every finding. Running `--only slop` on an API doc
printed nominalizations, a passive and four long sentences, none of which the
gate was measuring. Output that argues for edits the gate ignores is worse
than no output, because it is credible.
"""

import importlib.util
import os
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

EN_LINTER = ROOT / "en" / "ste-lint.py"
RU_LINTER = ROOT / "ru" / "ru-ste-lint.py"

# before: slop and cl both present. after: slop is zero, cl is not.
EN_DIRTY = ROOT / "examples" / "en-api-doc" / "before.md"
EN_CLEAN = ROOT / "examples" / "en-api-doc" / "after.md"
RU_DIRTY = ROOT / "examples" / "ru-api-doc" / "before.ru.md"
RU_CLEAN = ROOT / "examples" / "ru-api-doc" / "after.ru.md"

SUMMARY = re.compile(r"total=\s*(\d+)\s+per100w=\s*([0-9.]+)")
EXPLAIN_ROW = re.compile(r"^  L\d+\s+(\S+)")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


en = load(EN_LINTER, "en_lint")
ru = load(RU_LINTER, "ru_lint")


def lint(linter, *args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run([sys.executable, str(linter)] + [str(a) for a in args],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"))


def categories(out):
    return [m.group(1) for m in
            (EXPLAIN_ROW.match(line) for line in out.splitlines()) if m]


def summary(out):
    found = SUMMARY.search(out)
    if not found:
        raise AssertionError("no summary line in %r" % out)
    return int(found.group(1)), float(found.group(2))


class Partition(unittest.TestCase):
    """select() must lose nothing: every finding is slop or cl, never both."""

    def check(self, module, sample):
        text = sample.read_text(encoding="utf-8")
        rows = module.diagnostics(text)
        self.assertTrue(rows, "%s produced no diagnostics" % sample.name)
        slop = module.select(rows, "slop")
        cl = module.select(rows, "cl")
        self.assertEqual(len(slop) + len(cl), len(rows))
        self.assertEqual([], [row for row in slop if row in cl])

    def test_english_findings_split_in_two(self):
        self.check(en, EN_DIRTY)

    def test_russian_findings_split_in_two(self):
        self.check(ru, RU_DIRTY)

    def test_without_the_flag_nothing_is_dropped(self):
        rows = en.diagnostics(EN_DIRTY.read_text(encoding="utf-8"))
        self.assertEqual(en.select(rows, None), rows)
        self.assertEqual(en.select(rows, "total"), rows)


class ExplainRespectsTheFlag(unittest.TestCase):
    def test_only_slop_hides_controlled_language_findings(self):
        _, out, _ = lint(EN_LINTER, "--only", "slop", "--explain", EN_DIRTY)
        cats = categories(out)
        self.assertTrue(cats, "nothing was listed")
        for cat in cats:
            self.assertIn(cat, en.SLOP_CATEGORIES,
                          "--only slop listed %r, which the gate ignores" % cat)

    def test_only_cl_hides_banned_words(self):
        _, out, _ = lint(EN_LINTER, "--only", "cl", "--explain", EN_DIRTY)
        cats = categories(out)
        self.assertTrue(cats, "nothing was listed")
        for cat in cats:
            self.assertNotIn(cat, en.SLOP_CATEGORIES)
        self.assertIn("long_sentence(>20w)", cats)

    def test_russian_obeys_the_flag_too(self):
        _, out, _ = lint(RU_LINTER, "--only", "slop", "--explain", RU_DIRTY)
        for cat in categories(out):
            self.assertIn(cat, ru.SLOP_CATEGORIES)

    def test_the_two_listings_add_up_to_the_full_one(self):
        _, full, _ = lint(EN_LINTER, "--explain", EN_DIRTY)
        _, slop, _ = lint(EN_LINTER, "--only", "slop", "--explain", EN_DIRTY)
        _, cl, _ = lint(EN_LINTER, "--only", "cl", "--explain", EN_DIRTY)
        self.assertEqual(sorted(categories(full)),
                         sorted(categories(slop) + categories(cl)))

    def test_github_annotations_are_filtered_as_well(self):
        """CI annotations must match the check that failed the build."""
        _, out, _ = lint(EN_LINTER, "--only", "slop", "--format", "github",
                         EN_DIRTY)
        titles = re.findall(r"title=([^:]+)::", out)
        self.assertTrue(titles)
        for title in titles:
            self.assertIn(title, en.SLOP_CATEGORIES)


class SummaryMatchesTheGate(unittest.TestCase):
    """The number printed must be the number that decides pass or fail."""

    def test_only_slop_reports_the_slop_score(self):
        _, full, _ = lint(EN_LINTER, "--breakdown", EN_DIRTY)
        slop_count = int(re.search(r"slop=\s*(\d+)", full).group(1))
        _, out, _ = lint(EN_LINTER, "--only", "slop", EN_DIRTY)
        count, per100 = summary(out)
        self.assertEqual(count, slop_count)
        self.assertLess(per100, summary(full)[1])

    def test_the_flag_is_named_in_the_output(self):
        _, out, _ = lint(EN_LINTER, "--only", "cl", EN_DIRTY)
        self.assertIn("only=cl", out)

    def test_plain_output_is_unchanged(self):
        """No marker and the combined score when the flag is absent."""
        _, out, _ = lint(EN_LINTER, EN_DIRTY)
        self.assertNotIn("only=", out)
        self.assertEqual(summary(out)[0],
                         en.lint(EN_DIRTY.read_text(encoding="utf-8"))["total"])

    def test_russian_summary_follows_the_flag(self):
        _, full, _ = lint(RU_LINTER, "--breakdown", RU_DIRTY)
        cl_count = int(re.search(r"cl=\s*(\d+)", full).group(1))
        _, out, _ = lint(RU_LINTER, "--only", "cl", RU_DIRTY)
        self.assertEqual(summary(out)[0], cl_count)


class Gating(unittest.TestCase):
    """The point of the split: hold slop at zero, leave cl advisory."""

    def test_a_clean_file_passes_a_zero_slop_gate(self):
        for linter, sample in ((EN_LINTER, EN_CLEAN), (RU_LINTER, RU_CLEAN)):
            code, _, err = lint(linter, "--only", "slop", "--max", "0", sample)
            self.assertEqual(code, 0, "%s failed a zero-slop gate: %s"
                             % (sample.name, err))

    def test_the_same_file_fails_a_zero_cl_gate(self):
        """after.md still has controlled-language findings. That is the design."""
        code, _, err = lint(EN_LINTER, "--only", "cl", "--max", "0", EN_CLEAN)
        self.assertEqual(code, 1)
        self.assertIn("cl per 100 words", err)

    def test_a_dirty_file_fails_a_zero_slop_gate(self):
        code, _, err = lint(EN_LINTER, "--only", "slop", "--max", "0", EN_DIRTY)
        self.assertEqual(code, 1)
        self.assertIn("slop per 100 words", err)

    def test_an_unknown_component_is_refused(self):
        code, _, err = lint(EN_LINTER, "--only", "tone", EN_DIRTY)
        self.assertEqual(code, 2)
        self.assertIn("--only needs slop or cl", err)


if __name__ == "__main__":
    unittest.main()
