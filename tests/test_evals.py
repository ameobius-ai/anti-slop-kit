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

# The score is violations per 100 words, so a short fixture is unstable: one
# match in eleven words reads as 9.09. Keep the clean fixture above 30 words.
CLEAN = (
    "Set the timeout to 30 seconds. The server closes idle links after that "
    "time. Use the flag --retry to try again. Each retry waits two seconds "
    "longer than the one before it. Read the log file to find the last error.\n"
)


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
    def collect(self, files):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)
            for name, text in files.items():
                (path / name).write_text(text, encoding="utf-8")
            return score.collect(path)

    def rows(self, files):
        return self.collect(files)[0]

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

    def test_skipped_files_are_reported(self):
        """Issue #16: a dropped file must not lower n in silence."""
        rows, skipped = self.collect(
            {"en-01-a__bare.md": CLEAN, "en-02-bad-name.md": SLOP}
        )
        self.assertEqual([row["task"] for row in rows], ["en-01-a"])
        self.assertEqual(skipped, ["en-02-bad-name.md"])

    def test_nothing_is_skipped_when_every_name_matches(self):
        _, skipped = self.collect({"en-01-a__bare.md": CLEAN})
        self.assertEqual(skipped, [])

    def test_report_names_the_skipped_files(self):
        rows, _ = self.collect({"en-01-a__bare.md": CLEAN})
        buffer = io.StringIO()
        score.report(rows, score.summarise(rows), stream=buffer,
                     skipped=["en-02-bad-name.md"])
        self.assertIn("en-02-bad-name.md", buffer.getvalue())
        self.assertIn("Skipped 1 file", buffer.getvalue())

    def test_report_stays_quiet_when_nothing_was_skipped(self):
        rows, skipped = self.collect({"en-01-a__bare.md": CLEAN})
        buffer = io.StringIO()
        score.report(rows, score.summarise(rows), stream=buffer, skipped=skipped)
        self.assertNotIn("Skipped", buffer.getvalue())

    def test_long_condition_name_keeps_the_columns_aligned(self):
        rows = self.rows(
            {"en-01-a__bare.md": CLEAN, "en-01-a__very_long_condition.md": CLEAN}
        )
        buffer = io.StringIO()
        score.report(rows, score.summarise(rows), stream=buffer)
        lines = [ln for ln in buffer.getvalue().splitlines() if " n=" in ln]
        self.assertEqual(len({ln.index(" n=") for ln in lines}), 1)

    def test_routes_russian_to_the_russian_linter(self):
        rows = self.rows(
            {
                "ru-01-api-doc__bare.md": "Данный сервис является уникальным решением в целях осуществления обработки данных.\n"
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
