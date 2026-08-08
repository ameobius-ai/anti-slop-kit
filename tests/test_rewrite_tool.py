"""Comprehensive tests for rewrite_tool module.

Part of issue #208: Increase test coverage to 90%+
Ported to unittest so scripts/check.sh collects it (issue #242).
"""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from tools.aslint import rewrite_tool


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


class TestValidateRewrite(unittest.TestCase):
    """Tests for validate_rewrite function."""

    def test_accept_when_score_same(self):
        """Test that identical texts are accepted."""
        text = "# Test\n\nThis is a test document with some content."
        result = rewrite_tool.validate_rewrite(text, text)

        self.assertTrue(result["ok"])
        self.assertEqual(result["tool"], "validate_rewrite")
        self.assertEqual(result["verdict"], "accept")
        self.assertEqual(result["reasons"], [])
        self.assertEqual(result["score"]["delta_per100w"], 0)

    def test_accept_when_score_decreases(self):
        """Test that rewrite with lower score is accepted."""
        original = "# Test\n\nThis is basically a very really good example."
        rewrite = "# Test\n\nThis is a good example."

        result = rewrite_tool.validate_rewrite(original, rewrite)

        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"], "accept")
        self.assertLessEqual(result["score"]["delta_per100w"], 0)

    def test_reject_when_score_increases(self):
        """Test that rewrite with higher score is rejected."""
        original = "# Test\n\nThis is a simple test."
        rewrite = "# Test\n\nThis is basically a very really complex test."

        result = rewrite_tool.validate_rewrite(original, rewrite)

        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"], "reject")
        self.assertIn("score rose", result["reasons"][0])
        self.assertGreater(result["score"]["delta_per100w"], 0)

    def test_reject_when_numbers_lost(self):
        """Test that rewrite losing numbers is rejected."""
        original = "Version 2.0 and 3.0 are available."
        rewrite = "Version 2.0 is available."

        result = rewrite_tool.validate_rewrite(original, rewrite)

        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"], "reject")
        self.assertTrue(any("lost numbers" in r for r in result["reasons"]))
        self.assertIn("3.0", result["fidelity"]["numbers"])

    def test_reject_when_identifiers_lost(self):
        """Test that rewrite losing identifiers is rejected."""
        original = "Use config_key and api_secret."
        rewrite = "Use config_key."

        result = rewrite_tool.validate_rewrite(original, rewrite)

        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"], "reject")
        self.assertTrue(any("lost identifiers" in r for r in result["reasons"]))
        self.assertIn("api_secret", result["fidelity"]["identifiers"])

    def test_reject_when_urls_lost(self):
        """Test that rewrite losing URLs is rejected."""
        original = "Visit https://example.com and https://test.org."
        rewrite = "Visit https://example.com."

        result = rewrite_tool.validate_rewrite(original, rewrite)

        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"], "reject")
        self.assertTrue(any("lost urls" in r for r in result["reasons"]))
        self.assertIn("https://test.org", result["fidelity"]["urls"])

    def test_accept_when_all_preserved(self):
        """Test that rewrite preserving all tokens is accepted."""
        original = "Version 2.0 uses config_key at https://api.com."
        rewrite = "The version 2.0 uses config_key at https://api.com."

        result = rewrite_tool.validate_rewrite(original, rewrite)

        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"], "accept")

    def test_explicit_language_parameter(self):
        """Test validate_rewrite with explicit language."""
        original = "# Test\n\nThis is English text."
        rewrite = "# Test\n\nThis is rewritten English text."

        result = rewrite_tool.validate_rewrite(original, rewrite, lang="en")

        self.assertTrue(result["ok"])
        self.assertEqual(result["lang"], "en")

    def test_russian_text_detection(self):
        """Test validate_rewrite with Russian text."""
        original = "# Тест\n\nЭто русский текст."
        rewrite = "# Тест\n\nЭто переписанный русский текст."

        result = rewrite_tool.validate_rewrite(original, rewrite)

        self.assertTrue(result["ok"])
        self.assertEqual(result["lang"], "ru")

    def test_empty_texts(self):
        """Test validate_rewrite with empty texts."""
        result = rewrite_tool.validate_rewrite("", "")

        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"], "accept")

    def test_multiple_reasons_for_rejection(self):
        """Test that multiple reasons are collected."""
        original = "Version 2.0 uses config_key at https://api.com. This is basically good."
        rewrite = "This is a very really complex test."

        result = rewrite_tool.validate_rewrite(original, rewrite)

        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"], "reject")
        self.assertGreaterEqual(len(result["reasons"]), 1)


class TestMain(WithTmpDir):
    """Tests for main() CLI function."""

    def test_main_with_valid_files(self):
        """Test main() with valid original and rewrite files."""
        original = self.tmp_path / "original.md"
        rewrite = self.tmp_path / "rewrite.md"

        original.write_text("# Test\n\nThis is a test.")
        rewrite.write_text("# Test\n\nThis is rewritten test.")

        result = rewrite_tool.main([str(original), str(rewrite)])

        # Should return 0 (accept) or 1 (reject), not 2 (error)
        self.assertIn(result, [0, 1])

    def test_main_with_lang_flag(self):
        """Test main() with --lang flag."""
        original = self.tmp_path / "original.md"
        rewrite = self.tmp_path / "rewrite.md"

        original.write_text("# Test\n\nThis is English.")
        rewrite.write_text("# Test\n\nThis is rewritten English.")

        result = rewrite_tool.main(["--lang", "en", str(original), str(rewrite)])

        self.assertIn(result, [0, 1])

    def test_main_with_invalid_lang(self):
        """Test main() with invalid language."""
        original = self.tmp_path / "original.md"
        rewrite = self.tmp_path / "rewrite.md"

        original.write_text("# Test")
        rewrite.write_text("# Test")

        result, out = captured(rewrite_tool.main,
                               ["--lang", "invalid", str(original), str(rewrite)])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_with_missing_lang_value(self):
        """Test main() with --lang but no value."""
        original = self.tmp_path / "original.md"
        rewrite = self.tmp_path / "rewrite.md"

        original.write_text("# Test")
        rewrite.write_text("# Test")

        result, out = captured(rewrite_tool.main,
                               ["--lang", str(original), str(rewrite)])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_with_help(self):
        """Test main() with --help flag."""
        result, out = captured(rewrite_tool.main, ["--help"])

        self.assertEqual(result, 0)
        self.assertIn("validate_rewrite", out.lower())

    def test_main_with_unknown_flag(self):
        """Test main() with unknown flag."""
        result, out = captured(rewrite_tool.main, ["--unknown-flag"])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_no_args(self):
        """Test main() with no arguments."""
        result, out = captured(rewrite_tool.main, [])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_one_file_only(self):
        """Test main() with only one file."""
        original = self.tmp_path / "original.md"
        original.write_text("# Test")

        result, out = captured(rewrite_tool.main, [str(original)])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_three_files(self):
        """Test main() with three files."""
        file1 = self.tmp_path / "file1.md"
        file2 = self.tmp_path / "file2.md"
        file3 = self.tmp_path / "file3.md"

        file1.write_text("# Test")
        file2.write_text("# Test")
        file3.write_text("# Test")

        result, out = captured(rewrite_tool.main,
                               [str(file1), str(file2), str(file3)])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_nonexistent_file(self):
        """Test main() with nonexistent file."""
        rewrite = self.tmp_path / "rewrite.md"
        rewrite.write_text("# Test")

        result, out = captured(
            rewrite_tool.main,
            [str(self.tmp_path / "nonexistent.md"), str(rewrite)])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_accept_returns_zero(self):
        """Test that main() returns 0 when rewrite is accepted."""
        original = self.tmp_path / "original.md"
        rewrite = self.tmp_path / "rewrite.md"

        # Create rewrite with lower or same score
        original.write_text("# Test\n\nThis is basically a very really good test.")
        rewrite.write_text("# Test\n\nThis is a good test.")

        result = rewrite_tool.main([str(original), str(rewrite)])

        self.assertEqual(result, 0)

    def test_main_reject_returns_one(self):
        """Test that main() returns 1 when rewrite is rejected."""
        original = self.tmp_path / "original.md"
        rewrite = self.tmp_path / "rewrite.md"

        # Create rewrite with higher score or lost tokens
        original.write_text("# Test\n\nVersion 2.0 is available.")
        rewrite.write_text("# Test\n\nVersion is available.")  # Lost "2.0"

        result = rewrite_tool.main([str(original), str(rewrite)])

        self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()
