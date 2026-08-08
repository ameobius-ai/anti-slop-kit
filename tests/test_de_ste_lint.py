"""Tests for German language linter (de-ste-lint.py)

Part of issue #227: Add German language support
Tests the German language support based on Leichte Sprache principles.
Ported to unittest so scripts/check.sh collects it (issue #242).
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
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# The file name carries a dash, so a plain import cannot reach it.
de_ste_lint = load("de/de-ste-lint.py", "de_ste_lint")


def captured(fn, *args, **kwargs):
    """Run fn(), return (result_or_Exit, stdout_text).

    SystemExit is caught: the return value is the exception's code."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            result = fn(*args, **kwargs)
        except SystemExit as exc:
            result = exc
    return result, buf.getvalue()


class WithTmpDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = pathlib.Path(self._tmp.name)


class TestGermanLintBasic(WithTmpDir):
    """Basic functionality tests for German linter."""

    def test_lint_file_returns_correct_structure(self):
        """Test that lint_file returns expected dictionary structure."""
        test_file = self.tmp_path / "test.md"
        test_file.write_text("Dies ist ein Testdokument.")

        result = de_ste_lint.lint_file(test_file)

        self.assertIn("path", result)
        self.assertIn("words", result)
        self.assertIn("violations", result)
        self.assertIn("score", result)
        self.assertIn("findings", result)

    def test_count_words_counts_correctly(self):
        """Test that word counting works for German text."""
        text = "Dies ist ein Testdokument mit mehreren Wörtern"
        count = de_ste_lint.count_words(text)
        self.assertEqual(count, 7)

    def test_clean_german_text_has_no_violations(self):
        """Test that clean German text has minimal violations."""
        test_file = self.tmp_path / "clean.md"
        test_file.write_text("Dieses technische Dokument beschreibt das Authentifizierungssystem.")

        result = de_ste_lint.lint_file(test_file)

        # Clean text should have low score
        self.assertLess(result["score"], 5.0)


class TestGermanLintPatterns(WithTmpDir):
    """Tests for German-specific pattern detection."""

    def test_detects_banned_words(self):
        """Test that banned German words are detected."""
        test_file = self.tmp_path / "banned.md"
        test_file.write_text("Dies ist grundsätzlich ein eigentlich einfaches Dokument.")

        result = de_ste_lint.lint_file(test_file)

        # Should detect "grundsätzlich" and "eigentlich"
        self.assertGreaterEqual(result["violations"], 2)
        self.assertGreater(result["score"], 0)

    def test_detects_marketing_terms(self):
        """Test that marketing buzzwords are detected."""
        test_file = self.tmp_path / "marketing.md"
        test_file.write_text("Diese revolutionäre Lösung ist robust und skalierbar.")

        result = de_ste_lint.lint_file(test_file)

        # Should detect marketing terms
        self.assertGreaterEqual(result["violations"], 2)
        findings_text = " ".join([f["word"] for f in result["findings"]])
        self.assertTrue("revolutionär" in findings_text.lower() or "robust" in findings_text.lower())

    def test_detects_filler_phrases(self):
        """Test that filler phrases are detected."""
        test_file = self.tmp_path / "filler.md"
        test_file.write_text("Im Grunde genommen ist dieses Dokument tatsächlich einfach.")

        result = de_ste_lint.lint_file(test_file)

        # Should detect filler phrases
        self.assertGreaterEqual(result["violations"], 2)
        self.assertGreater(result["score"], 0)


class TestGermanLintEdgeCases(WithTmpDir):
    """Edge case tests for German linter."""

    def test_empty_file(self):
        """Test handling of empty file."""
        test_file = self.tmp_path / "empty.md"
        test_file.write_text("")

        result = de_ste_lint.lint_file(test_file)

        self.assertEqual(result["words"], 0)
        self.assertEqual(result["violations"], 0)
        self.assertEqual(result["score"], 0.0)

    def test_special_german_characters(self):
        """Test handling of German special characters."""
        test_file = self.tmp_path / "special.md"
        test_file.write_text("Wie geht es Ihnen? Sehr gut! Der Schüler ist hier.")

        result = de_ste_lint.lint_file(test_file)

        # Should handle special characters without errors
        self.assertGreater(result["words"], 0)
        self.assertGreaterEqual(result["violations"], 0)

    def test_german_umlauts(self):
        """Test handling of German umlauts."""
        test_file = self.tmp_path / "umlauts.md"
        test_file.write_text("ä ö ü Ä Ö Ü ß")

        result = de_ste_lint.lint_file(test_file)

        # Should handle all German umlauts without errors
        self.assertGreater(result["words"], 0)


class TestGermanLintCLI(WithTmpDir):
    """Tests for CLI functionality."""

    def test_main_with_valid_file(self):
        """Test main() with valid file."""
        test_file = self.tmp_path / "test.md"
        test_file.write_text("Einfaches Testdokument.")

        result, _ = captured(de_ste_lint.main, [str(test_file)])

        # Should exit with 0 (clean) or 1 (violations)
        self.assertIsInstance(result, SystemExit)
        self.assertIn(result.code, [0, 1])

    def test_main_with_no_arguments(self):
        """Test main() with no arguments."""
        result, _ = captured(de_ste_lint.main, [])

        # Should fail
        self.assertIsInstance(result, SystemExit)
        self.assertEqual(result.code, 2)

    def test_main_with_json_output(self):
        """Test main() with --json flag."""
        test_file = self.tmp_path / "test.md"
        test_file.write_text("Testdokument.")

        result, out = captured(de_ste_lint.main, ["--json", str(test_file)])

        # Should succeed and output JSON
        self.assertIsInstance(result, SystemExit)
        self.assertIn(result.code, [0, 1])
        self.assertIn("{", out)  # JSON output contains braces


if __name__ == '__main__':
    unittest.main()
