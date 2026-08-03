"""Tests for --explain and --format github output modes.

Runs en/ste-lint.py and ru/ru-ste-lint.py as subprocesses so the CLI
contract is tested the way users and CI invoke it.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN_LINT = os.path.join(ROOT, "en", "ste-lint.py")
RU_LINT = os.path.join(ROOT, "ru", "ru-ste-lint.py")

SLOP = (
    "In today's fast-paced world, it is important to note that we utilize "
    "a robust solution in order to facilitate the work.\n"
    "\n"
    "The data is written by the service; the service doesn't stop.\n"
)

CLEAN = (
    "The cache stores keys in memory.\n"
    "\n"
    "Use three nodes for failover. Check the logs each week.\n"
)

MARKUP = (
    "---\ntitle: utilize leverage herein\n---\n\n"
    "We utilize real things.\n\n"
    "```\ncode utilizes leverage; it is handled\n```\n\n"
    "<!-- anti-slop: off -->\nquoted leverage in today's fast-paced world\n"
    "<!-- anti-slop: on -->\n\n"
    "Inline `leverage` code. A [link](https://x.com/robust) here.\n"
)


def run_lint(*args, stdin=None):
    return subprocess.run(
        [sys.executable, EN_LINT, *args],
        capture_output=True, text=True, input=stdin,
    )


class ExplainTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.slop = os.path.join(self.dir, "slop.md")
        self.clean = os.path.join(self.dir, "clean.md")
        self.markup = os.path.join(self.dir, "markup.md")
        for path, body in ((self.slop, SLOP), (self.clean, CLEAN),
                           (self.markup, MARKUP)):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)

    def test_explain_lists_line_numbers_and_suggestions(self):
        p = run_lint("--explain", self.slop)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("L1", p.stdout)
        self.assertIn("banned_word", p.stdout)
        self.assertIn("passive_voice", p.stdout)
        self.assertIn("Use 'use' instead.", p.stdout)

    def test_explain_finding_count_matches_total(self):
        p = run_lint("--explain", self.slop)
        lines = [ln for ln in p.stdout.splitlines() if ln.startswith("  L")]
        # summary line reports total=N; findings must account for it
        total = int(p.stdout.split("total=")[1].split()[0])
        self.assertEqual(len(lines), total)

    def test_explain_clean_file_has_no_findings(self):
        p = run_lint("--explain", self.clean)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("banned_word", p.stdout)
        self.assertNotIn("  L", p.stdout.split("\n", 1)[1] or "")

    def test_explain_skips_markup_regions(self):
        p = run_lint("--explain", self.markup)
        findings = [ln for ln in p.stdout.splitlines() if ln.startswith("  L")]
        # only the prose "utilizes" on its own line may appear
        self.assertEqual(len(findings), 1)
        self.assertIn("utilize", findings[0])

    def test_github_format_emits_annotations(self):
        p = run_lint("--format", "github", self.slop)
        self.assertEqual(p.returncode, 0, p.stderr)
        anns = [ln for ln in p.stdout.splitlines()
                if ln.startswith("::warning ")]
        self.assertTrue(anns)
        self.assertIn("file=", anns[0])
        self.assertIn("line=1", anns[0])
        self.assertIn("title=", anns[0])

    def test_github_format_respects_max_exit_code(self):
        p = run_lint("--format", "github", "--max", "1", self.slop)
        self.assertEqual(p.returncode, 1)
        self.assertIn("FAIL", p.stderr)

    def test_github_format_does_not_pollute_json(self):
        p = run_lint("--json", "--format", "github", self.slop)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("::warning", p.stdout)
        json.loads(p.stdout)  # must stay parseable

    def test_bad_format_rejected(self):
        p = run_lint("--format", "xml", self.slop)
        self.assertEqual(p.returncode, 2)

    def test_default_output_unchanged_by_new_flags(self):
        p1 = run_lint(self.slop)
        p2 = run_lint(self.slop, self.clean)
        self.assertNotIn("  L", p1.stdout)
        self.assertNotIn("::warning", p1.stdout)
        self.assertEqual(p1.returncode, 0)
        self.assertEqual(p2.returncode, 0)


RU_SLOP = (
    "В современном мире кэширование является важным.\n"
    "\n"
    "В случае, если узел недоступен, запрос направляется дальше.\n"
)

RU_CLEAN = "Кэш держит ключи в памяти.\n\nВозьмите три узла.\n"


def run_ru(*args, stdin=None):
    return subprocess.run(
        [sys.executable, RU_LINT, *args],
        capture_output=True, text=True, input=stdin, cwd=ROOT,
    )


class RuExplainTests(unittest.TestCase):
    """The RU linter must expose the same --explain/--format contract."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.slop = os.path.join(self.dir.name, "slop.md")
        self.clean = os.path.join(self.dir.name, "clean.md")
        with open(self.slop, "w", encoding="utf-8") as fh:
            fh.write(RU_SLOP)
        with open(self.clean, "w", encoding="utf-8") as fh:
            fh.write(RU_CLEAN)

    def test_default_output_is_unchanged_by_the_new_flags(self):
        """Rule 5: the summary line other tools parse must not move."""
        plain = run_ru(self.slop).stdout
        self.assertIn("words=", plain)
        self.assertIn("per100w=", plain)
        self.assertEqual(len(plain.strip().split("\n")), 1)
        self.assertEqual(
            plain, run_ru("--explain", self.slop).stdout.split("\n")[0] + "\n"
        )

    def test_explain_prints_line_numbers_and_suggestions(self):
        out = run_ru("--explain", self.slop).stdout
        self.assertIn("  L1", out)
        self.assertIn("ai_slop", out)
        self.assertIn("clerical", out)
        # Canned rewrite from REPLACE, not the generic category hint.
        self.assertIn("если", out)

    def test_finding_count_matches_the_score(self):
        """--explain must account for every violation the score counts."""
        summary = json.loads(run_ru("--json", self.slop).stdout)
        total = summary[self.slop]["total"]
        out = run_ru("--explain", self.slop).stdout.split("\n")[1:]
        self.assertEqual(len([ln for ln in out if ln.startswith("  L")]), total)

    def test_clean_file_has_no_findings(self):
        out = run_ru("--explain", self.clean).stdout
        self.assertNotIn("  L", out)

    def test_github_format_emits_annotations(self):
        out = run_ru("--format", "github", self.slop).stdout
        self.assertIn("::warning file=", out)
        self.assertIn(",line=1,", out)
        self.assertIn("title=ai_slop::", out)

    def test_json_output_is_not_polluted_by_annotations(self):
        out = run_ru("--json", "--format", "github", self.slop).stdout
        self.assertNotIn("::warning", out)
        json.loads(out)

    def test_bad_format_exits_two(self):
        self.assertEqual(run_ru("--format", "xml", self.slop).returncode, 2)

    def test_max_still_controls_the_exit_code_with_explain(self):
        self.assertEqual(run_ru("--explain", "--max", "5", self.slop).returncode, 1)
        self.assertEqual(run_ru("--explain", "--max", "5", self.clean).returncode, 0)


if __name__ == "__main__":
    unittest.main()
