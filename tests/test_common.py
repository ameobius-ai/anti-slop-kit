"""Comprehensive tests for common module.

Part of issue #208: Increase test coverage to 90%+
Ported to unittest so scripts/check.sh collects it (issue #242).
"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tools.aslint import common


def emit_out(fn, *args, **kwargs):
    """Run fn() with stdout captured; return the captured text."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args, **kwargs)
    return buf.getvalue()


class TestDetectLang(unittest.TestCase):
    """Tests for detect_lang function."""

    def test_detect_english(self):
        """Test detection of English text."""
        text = "This is English text with no Cyrillic characters."
        self.assertEqual(common.detect_lang(text), "en")

    def test_detect_russian(self):
        """Test detection of Russian text."""
        text = "Это русский текст с кириллическими символами."
        self.assertEqual(common.detect_lang(text), "ru")

    def test_detect_mixed_prefers_russian(self):
        """Test that Cyrillic presence routes to Russian."""
        text = "This is mixed text with русский word."
        self.assertEqual(common.detect_lang(text), "ru")

    def test_detect_empty_text(self):
        """Test detection with empty text."""
        text = ""
        self.assertEqual(common.detect_lang(text), "en")  # Default to English


class TestFidelityTokens(unittest.TestCase):
    """Tests for fidelity_tokens function."""

    def test_extract_numbers(self):
        """Test extraction of numbers."""
        text = "There are 42 items and 3.14 is pi."
        tokens = common.fidelity_tokens(text)

        self.assertIn("numbers", tokens)
        self.assertIn("42", tokens["numbers"])
        self.assertIn("3.14", tokens["numbers"])

    def test_extract_identifiers(self):
        """Test extraction of identifiers with underscores."""
        text = "The config_key and API_VERSION are important."
        tokens = common.fidelity_tokens(text)

        self.assertIn("identifiers", tokens)
        self.assertIn("config_key", tokens["identifiers"])
        self.assertIn("API_VERSION", tokens["identifiers"])

    def test_extract_urls(self):
        """Test extraction of URLs."""
        text = "Visit https://example.com and http://test.org/path."
        tokens = common.fidelity_tokens(text)

        self.assertIn("urls", tokens)
        self.assertIn("https://example.com", tokens["urls"])
        self.assertIn("http://test.org/path", tokens["urls"])

    def test_url_trailing_punctuation_stripped(self):
        """Test that trailing punctuation is stripped from URLs."""
        text = "See https://example.com. and https://test.org!"
        tokens = common.fidelity_tokens(text)

        self.assertIn("https://example.com", tokens["urls"])
        self.assertIn("https://test.org", tokens["urls"])

    def test_empty_text(self):
        """Test with empty text."""
        tokens = common.fidelity_tokens("")

        self.assertEqual(tokens["numbers"], [])
        self.assertEqual(tokens["identifiers"], [])
        self.assertEqual(tokens["urls"], [])

    def test_no_identifiers_without_underscore(self):
        """Test that identifiers without underscore are not extracted."""
        text = "The config and API are important."
        tokens = common.fidelity_tokens(text)

        self.assertNotIn("config", tokens["identifiers"])
        self.assertNotIn("API", tokens["identifiers"])


class TestLostTokens(unittest.TestCase):
    """Tests for lost_tokens function."""

    def test_no_tokens_lost(self):
        """Test when no tokens are lost."""
        source = "The API_VERSION is 2.0 at https://api.com."
        transmitted = "The API_VERSION remains 2.0 at https://api.com."

        lost = common.lost_tokens(source, transmitted)

        self.assertEqual(lost["numbers"], [])
        self.assertEqual(lost["identifiers"], [])
        self.assertEqual(lost["urls"], [])

    def test_number_lost(self):
        """Test when a number is lost."""
        source = "Version 2.0 and 3.0 are available."
        transmitted = "Version 2.0 is available."

        lost = common.lost_tokens(source, transmitted)

        self.assertIn("3.0", lost["numbers"])

    def test_identifier_lost(self):
        """Test when an identifier is lost."""
        source = "Use config_key and api_secret."
        transmitted = "Use config_key."

        lost = common.lost_tokens(source, transmitted)

        self.assertIn("api_secret", lost["identifiers"])

    def test_url_lost(self):
        """Test when a URL is lost."""
        source = "Visit https://example.com and https://test.org."
        transmitted = "Visit https://example.com."

        lost = common.lost_tokens(source, transmitted)

        self.assertIn("https://test.org", lost["urls"])

    def test_multiple_tokens_lost(self):
        """Test when multiple tokens are lost."""
        source = "Version 2.0 uses config_key at https://api.com."
        transmitted = "The system works."

        lost = common.lost_tokens(source, transmitted)

        self.assertIn("2.0", lost["numbers"])
        self.assertIn("config_key", lost["identifiers"])
        self.assertIn("https://api.com", lost["urls"])


class TestLintText(unittest.TestCase):
    """Tests for lint_text function."""

    def test_lint_text_with_auto_detect(self):
        """Test lint_text with automatic language detection."""
        text = "# Test\n\nThis is English text."
        lang, result = common.lint_text(text)

        self.assertEqual(lang, "en")
        self.assertIsInstance(result, dict)

    def test_lint_text_with_explicit_lang(self):
        """Test lint_text with explicit language."""
        text = "# Test\n\nThis is English text."
        lang, result = common.lint_text(text, lang="en")

        self.assertEqual(lang, "en")
        self.assertIsInstance(result, dict)

    def test_lint_text_russian(self):
        """Test lint_text with Russian text."""
        text = "# Тест\n\nЭто русский текст."
        lang, result = common.lint_text(text)

        self.assertEqual(lang, "ru")
        self.assertIsInstance(result, dict)


class TestEmit(unittest.TestCase):
    """Tests for emit function."""

    def test_emit_simple_dict(self):
        """Test emit with simple dictionary."""
        obj = {"key": "value", "number": 42}
        out = emit_out(common.emit, obj)
        parsed = json.loads(out)

        self.assertEqual(parsed["key"], "value")
        self.assertEqual(parsed["number"], 42)

    def test_emit_unicode(self):
        """Test emit with unicode characters."""
        obj = {"text": "Русский текст"}
        out = emit_out(common.emit, obj)
        parsed = json.loads(out)

        self.assertEqual(parsed["text"], "Русский текст")

    def test_emit_nested_dict(self):
        """Test emit with nested dictionary."""
        obj = {
            "level1": {
                "level2": {
                    "value": 123
                }
            }
        }
        out = emit_out(common.emit, obj)
        parsed = json.loads(out)

        self.assertEqual(parsed["level1"]["level2"]["value"], 123)


class TestRunLinter(unittest.TestCase):
    """Tests for run_linter function."""

    def test_run_linter_invalid_lang(self):
        """Test run_linter with invalid language."""
        with tempfile.TemporaryDirectory() as tmp:
            test_file = Path(tmp) / "test.md"
            test_file.write_text("# Test")

            with self.assertRaisesRegex(ValueError, "unknown language"):
                common.run_linter("invalid", str(test_file))


if __name__ == '__main__':
    unittest.main()
