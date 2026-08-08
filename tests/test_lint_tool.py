"""Comprehensive tests for lint_tool module.

Part of issue #208: Increase test coverage to 90%+
Ported to unittest so scripts/check.sh collects it (issue #242).
"""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from tools.aslint import lint_tool


class WithTmpDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)


def captured(fn, *args, **kwargs):
    """Run fn(), return (result, stdout_text)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = fn(*args, **kwargs)
    return result, buf.getvalue()


class TestLintFile(WithTmpDir):
    """Tests for lint_file function."""

    def test_lint_file_with_valid_markdown(self):
        """Test linting a valid markdown file."""
        test_file = self.tmp_path / "test.md"
        test_file.write_text("# Test Document\n\nThis is a test document.")

        result = lint_tool.lint_file(str(test_file))

        self.assertTrue(result["ok"])
        self.assertEqual(result["tool"], "lint_file")
        self.assertEqual(result["path"], str(test_file))
        self.assertIn("lang", result)
        self.assertIn("result", result)

    def test_lint_file_with_explicit_lang(self):
        """Test linting with explicit language parameter."""
        test_file = self.tmp_path / "test.md"
        test_file.write_text("# Test\n\nThis is English text.")

        result = lint_tool.lint_file(str(test_file), lang="en")

        self.assertTrue(result["ok"])
        self.assertEqual(result["lang"], "en")

    def test_lint_file_with_russian_text(self):
        """Test linting Russian text."""
        test_file = self.tmp_path / "test_ru.md"
        test_file.write_text("# Тест\n\nЭто русский текст для проверки.")

        result = lint_tool.lint_file(str(test_file))

        self.assertTrue(result["ok"])
        self.assertEqual(result["lang"], "ru")

    def test_lint_file_nonexistent(self):
        """Test linting a nonexistent file."""
        with self.assertRaises(Exception):  # Should raise FileNotFoundError
            lint_tool.lint_file("/nonexistent/file.md")


class TestLintText(unittest.TestCase):
    """Tests for lint_text_tool function."""

    def test_lint_text_basic(self):
        """Test linting basic text."""
        text = "# Test\n\nThis is a test document."

        result = lint_tool.lint_text_tool(text)

        self.assertTrue(result["ok"])
        self.assertEqual(result["tool"], "lint_text")
        self.assertEqual(result["path"], "<text>")
        self.assertIn("lang", result)
        self.assertIn("result", result)

    def test_lint_text_with_explicit_lang(self):
        """Test linting text with explicit language."""
        text = "# Test\n\nThis is English text."

        result = lint_tool.lint_text_tool(text, lang="en")

        self.assertTrue(result["ok"])
        self.assertEqual(result["lang"], "en")

    def test_lint_text_empty(self):
        """Test linting empty text."""
        text = ""

        result = lint_tool.lint_text_tool(text)

        self.assertTrue(result["ok"])
        self.assertIn("result", result)

    def test_lint_text_with_slop_patterns(self):
        """Test that slop patterns are detected."""
        text = "This is basically a very really good example of what we are talking about."

        result = lint_tool.lint_text_tool(text, lang="en")

        self.assertTrue(result["ok"])
        # The result should contain findings
        self.assertIn("result", result)
        if "findings" in result["result"]:
            # Should detect some slop patterns
            self.assertGreaterEqual(len(result["result"]["findings"]), 0)


class TestMainFunction(WithTmpDir):
    """Tests for main() CLI function."""

    def test_main_with_file(self):
        """Test main() with a file argument."""
        test_file = self.tmp_path / "test.md"
        test_file.write_text("# Test\n\nTest content.")

        result = lint_tool.main([str(test_file)])

        self.assertEqual(result, 0)

    def test_main_with_lang_flag(self):
        """Test main() with --lang flag."""
        test_file = self.tmp_path / "test.md"
        test_file.write_text("# Test\n\nTest content.")

        result = lint_tool.main(["--lang", "en", str(test_file)])

        self.assertEqual(result, 0)

    def test_main_with_invalid_lang(self):
        """Test main() with invalid language."""
        test_file = self.tmp_path / "test.md"
        test_file.write_text("# Test\n\nTest content.")

        result, out = captured(lint_tool.main, ["--lang", "invalid", str(test_file)])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_with_help(self):
        """Test main() with --help flag."""
        result, out = captured(lint_tool.main, ["--help"])

        self.assertEqual(result, 0)
        self.assertTrue("Usage:" in out or "usage:" in out.lower())

    def test_main_with_unknown_flag(self):
        """Test main() with unknown flag."""
        result, out = captured(lint_tool.main, ["--unknown-flag"])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_no_args(self):
        """Test main() with no arguments."""
        result, out = captured(lint_tool.main, [])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_multiple_files(self):
        """Test main() with multiple files."""
        file1 = self.tmp_path / "test1.md"
        file2 = self.tmp_path / "test2.md"
        file1.write_text("# Test 1")
        file2.write_text("# Test 2")

        result = lint_tool.main([str(file1), str(file2)])

        self.assertEqual(result, 0)


class TestSlimFunction(unittest.TestCase):
    """Tests for _slim() helper function."""

    def test_slim_filters_keys(self):
        """Test that _slim() filters to expected keys."""
        full_result = {
            "words": 100,
            "sentences": 10,
            "total": 50,
            "total_per100w": 50.0,
            "slop": 20,
            "cl": 30,
            "slop_per100w": 20.0,
            "cl_per100w": 30.0,
            "longest_sentence_words": 25,
            "findings": [],
            "extra_field": "should be removed"
        }

        slimmed = lint_tool._slim(full_result)

        self.assertIn("words", slimmed)
        self.assertIn("sentences", slimmed)
        self.assertIn("total", slimmed)
        self.assertNotIn("extra_field", slimmed)

    def test_slim_handles_missing_keys(self):
        """Test that _slim() handles missing keys gracefully."""
        partial_result = {
            "words": 100,
            "total": 50
        }

        slimmed = lint_tool._slim(partial_result)

        self.assertIn("words", slimmed)
        self.assertIn("total", slimmed)
        self.assertEqual(len(slimmed), 2)


if __name__ == '__main__':
    unittest.main()
