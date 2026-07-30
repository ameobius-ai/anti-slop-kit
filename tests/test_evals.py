"""Tests for the eval scorer.

The scorer decides which linter to use from the file name, so the naming
convention is part of the contract and is tested here.
"""

import contextlib
import importlib.util
import io
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


score = load("evals/score.py", "score")

SLOP = (
    "It is important to note that this comprehensive and robust solution will "
    "leverage cutting-edge technology in order to seamlessly empower the "
    "utilization of the system, which is considered by many to be a "
    "game-changing capability that unlocks value.\n"
)

CLEAN = "Set the timeout to 30 seconds. The server closes idle connections.\n"


class Naming(unittest.TestCase):
    def test_accepts_the_convention(self):
        match = score.NAME_RE.match("en-01-api-doc__bare.md")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("task"), "en-01-api-doc")
        self.assertEqual(match.group("lang"), "en")
        self.assertEqual(match.group("condition"), "bare")

    def test_rejects_a_missing_condition(self):
        self.assertIsNone(score.NAME_RE.match("en-01-api-doc.md"))

    def test_rejects_an_unknown_language(self):
        self.assertIsNone(score.NAME_RE.match("de-01-api-doc__bare.md"))


class Scoring(unittest.TestCase):
    def rows(self, files):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)
            for name, text in files.items():
                (path / name).write_text(text, encoding="utf-8")
            return score.collect(path)

    def test_slop_scores_above_clean(self):
        rows = self.rows(
            {
                "en-01-api-doc__bare.md": SLOP,
                "en-01-api-doc__skill.md": CLEAN,
            }
        )
        by_condition = {row["condition"]: row["score"] for row in rows}
        self.assertGreater(by_condition["bare"], 20)
        self.assertLess(by_condition["skill"], 5)

    def test_ignores_unrelated_files(self):
        rows = self.rows({"notes.md": SLOP, "en-01-a__bare.md": CLEAN})
        self.assertEqual([row["task"] for row in rows], ["en-01-a"])

    def test_routes_russian_to_the_russian_linter(self):
        rows = self.rows(
            {
                "ru-01-api-doc__bare.md": "\u0414\u0430\u043d\u043d\u044b\u0439 \u0441\u0435\u0440\u0432\u0438\u0441 \u044f\u0432\u043b\u044f\u0435\u0442\u0441\u044f \u0443\u043d\u0438\u043a\u0430\u043b\u044c\u043d\u044b\u043c \u0440\u0435\u0448\u0435\u043d\u0438\u0435\u043c \u0432 \u0446\u0435\u043b\u044f\u0445 \u043e\u0441\u0443\u0449\u0435\u0441\u0442\u0432\u043b\u0435\u043d\u0438\u044f \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0438 \u0434\u0430\u043d\u043d\u044b\u0445.\n"
            }
        )
        self.assertEqual(rows[0]["lang"], "ru")
        self.assertGreater(rows[0]["score"], 0)

    def test_summary_counts_every_cell(self):
        rows = self.rows(
            {
                "en-01-a__bare.md": SLOP,
                "en-02-b__bare.md": SLOP,
                "en-01-a__skill.md": CLEAN,
                "en-02-b__skill.md": CLEAN,
            }
        )
        summary = score.summarise(rows)
        self.assertEqual(summary["en"]["bare"]["n"], 2)
        self.assertEqual(summary["en"]["skill"]["n"], 2)
        self.assertGreater(summary["en"]["bare"]["mean"], summary["en"]["skill"]["mean"])

    def test_known_conditions_come_first(self):
        self.assertEqual(
            score.order({"skill", "zzz", "bare"}),
            ["bare", "skill", "zzz"],
        )

    def test_report_writes_to_the_given_stream(self):
        rows = self.rows({"en-01-a__bare.md": SLOP})
        summary = score.summarise(rows)
        buffer = io.StringIO()
        leaked = io.StringIO()
        with contextlib.redirect_stdout(leaked):
            score.report(rows, summary, stream=buffer)
        self.assertIn("en-01-a", buffer.getvalue())
        self.assertEqual(leaked.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
