"""Comprehensive tests for transmit_check module.

Part of issue #208: Increase test coverage to 90%+
Ported to unittest so scripts/check.sh collects it (issue #242).
"""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from tools.aslint import transmit_check


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


class TestOrderingOk(unittest.TestCase):
    """Tests for _ordering_ok helper function."""

    def test_tokens_in_order(self):
        """Test that tokens in correct order return True."""
        text = "First comes alpha, then beta, finally gamma."
        tokens = ["alpha", "beta", "gamma"]

        self.assertTrue(transmit_check._ordering_ok(text, tokens))

    def test_tokens_out_of_order(self):
        """Test that tokens in wrong order return False."""
        text = "First comes gamma, then alpha, finally beta."
        tokens = ["alpha", "beta", "gamma"]

        self.assertFalse(transmit_check._ordering_ok(text, tokens))

    def test_token_missing(self):
        """Test that missing token returns False."""
        text = "First comes alpha, then beta."
        tokens = ["alpha", "beta", "gamma"]

        self.assertFalse(transmit_check._ordering_ok(text, tokens))

    def test_empty_tokens_list(self):
        """Test with empty tokens list."""
        text = "Some text here."
        tokens = []

        self.assertTrue(transmit_check._ordering_ok(text, tokens))

    def test_single_token(self):
        """Test with single token."""
        text = "The alpha is here."
        tokens = ["alpha"]

        self.assertTrue(transmit_check._ordering_ok(text, tokens))

    def test_duplicate_tokens(self):
        """Test with duplicate tokens in list."""
        text = "First alpha, then beta, then alpha again."
        tokens = ["alpha", "beta", "alpha"]

        # Contract: tokens are matched by first index, so a repeat of an
        # earlier token after a later one breaks the order.
        self.assertFalse(transmit_check._ordering_ok(text, tokens))


class TestTransmitCheck(unittest.TestCase):
    """Tests for transmit_check function."""

    def test_all_checks_pass(self):
        """Test when all checks pass."""
        source = "Version 2.0 uses config_key at https://api.com."
        transmitted = "The version 2.0 uses config_key at https://api.com."

        result = transmit_check.transmit_check(source, transmitted)

        self.assertTrue(result["ok"])
        self.assertEqual(result["tool"], "transmit_check")
        self.assertTrue(result["passed"])
        self.assertTrue(all(result["checks"].values()))

    def test_numbers_lost(self):
        """Test when numbers are lost."""
        source = "Version 2.0 and 3.0 are available."
        transmitted = "Version 2.0 is available."

        result = transmit_check.transmit_check(source, transmitted)

        self.assertTrue(result["ok"])
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["numbers"])
        self.assertIn("3.0", result["missing"]["numbers"])

    def test_identifiers_lost(self):
        """Test when identifiers are lost."""
        source = "Use config_key and api_secret."
        transmitted = "Use config_key."

        result = transmit_check.transmit_check(source, transmitted)

        self.assertTrue(result["ok"])
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["identifiers"])
        self.assertIn("api_secret", result["missing"]["identifiers"])

    def test_urls_lost(self):
        """Test when URLs are lost."""
        source = "Visit https://example.com and https://test.org."
        transmitted = "Visit https://example.com."

        result = transmit_check.transmit_check(source, transmitted)

        self.assertTrue(result["ok"])
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["urls"])
        self.assertIn("https://test.org", result["missing"]["urls"])

    def test_constraint_missing(self):
        """Test when constraint is missing."""
        source = "Some text here."
        transmitted = "Some text here."
        constraints = ["required_string"]

        result = transmit_check.transmit_check(source, transmitted, constraints=constraints)

        self.assertTrue(result["ok"])
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["constraints"])
        self.assertIn("required_string", result["missing"]["constraints"])

    def test_constraint_present(self):
        """Test when constraint is present."""
        source = "Some text here."
        transmitted = "Some text here with required_string."
        constraints = ["required_string"]

        result = transmit_check.transmit_check(source, transmitted, constraints=constraints)

        self.assertTrue(result["ok"])
        self.assertTrue(result["checks"]["constraints"])

    def test_ordering_correct(self):
        """Test when ordering is correct."""
        source = "First alpha, then beta, finally gamma."
        transmitted = "First alpha, then beta, finally gamma."
        ordered = ["alpha", "beta", "gamma"]

        result = transmit_check.transmit_check(source, transmitted, ordered=ordered)

        self.assertTrue(result["ok"])
        self.assertTrue(result["checks"]["ordering"])
        self.assertEqual(result["ordered_tokens"], ordered)

    def test_ordering_incorrect(self):
        """Test when ordering is incorrect."""
        source = "First gamma, then alpha, finally beta."
        transmitted = "First gamma, then alpha, finally beta."
        ordered = ["alpha", "beta", "gamma"]

        result = transmit_check.transmit_check(source, transmitted, ordered=ordered)

        self.assertTrue(result["ok"])
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["ordering"])

    def test_empty_texts(self):
        """Test with empty texts."""
        result = transmit_check.transmit_check("", "")

        self.assertTrue(result["ok"])
        self.assertTrue(result["passed"])

    def test_multiple_failures(self):
        """Test when multiple checks fail."""
        source = "Version 2.0 uses config_key at https://api.com with required_string."
        transmitted = "This is completely different text."
        constraints = ["required_string"]
        ordered = ["2.0", "config_key"]

        result = transmit_check.transmit_check(source, transmitted, constraints, ordered)

        self.assertTrue(result["ok"])
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["numbers"])
        self.assertFalse(result["checks"]["identifiers"])
        self.assertFalse(result["checks"]["urls"])
        self.assertFalse(result["checks"]["constraints"])

    def test_none_constraints(self):
        """Test with None constraints."""
        source = "Some text."
        transmitted = "Some text."

        result = transmit_check.transmit_check(source, transmitted, constraints=None)

        self.assertTrue(result["ok"])
        self.assertTrue(result["checks"]["constraints"])

    def test_none_ordered(self):
        """Test with None ordered."""
        source = "Some text."
        transmitted = "Some text."

        result = transmit_check.transmit_check(source, transmitted, ordered=None)

        self.assertTrue(result["ok"])
        self.assertTrue(result["checks"]["ordering"])


class TestMain(WithTmpDir):
    """Tests for main() CLI function."""

    def test_main_with_valid_files(self):
        """Test main() with valid source and transmitted files."""
        source = self.tmp_path / "source.md"
        transmitted = self.tmp_path / "transmitted.md"

        source.write_text("# Source\n\nVersion 2.0.")
        transmitted.write_text("# Transmitted\n\nVersion 2.0.")

        result = transmit_check.main([str(source), str(transmitted)])

        self.assertIn(result, [0, 1])

    def test_main_with_require_flag(self):
        """Test main() with --require flag."""
        source = self.tmp_path / "source.md"
        transmitted = self.tmp_path / "transmitted.md"

        source.write_text("# Source\n\nSome text with API_VERSION.")
        transmitted.write_text("# Transmitted\n\nSome text with API_VERSION.")

        result = transmit_check.main([
            "--require", "API_VERSION",
            str(source), str(transmitted)
        ])

        self.assertEqual(result, 0)

    def test_main_with_order_flag(self):
        """Test main() with --order flag."""
        source = self.tmp_path / "source.md"
        transmitted = self.tmp_path / "transmitted.md"

        source.write_text("# Source\n\nFirst alpha, then beta.")
        transmitted.write_text("# Transmitted\n\nFirst alpha, then beta.")

        result = transmit_check.main([
            "--order", "alpha", "--order", "beta",
            str(source), str(transmitted)
        ])

        self.assertEqual(result, 0)

    def test_main_with_multiple_requires(self):
        """Test main() with multiple --require flags."""
        source = self.tmp_path / "source.md"
        transmitted = self.tmp_path / "transmitted.md"

        source.write_text("# Source\n\nVersion 2.0 with API_KEY.")
        transmitted.write_text("# Transmitted\n\nVersion 2.0 with API_KEY.")

        result = transmit_check.main([
            "--require", "2.0", "--require", "API_KEY",
            str(source), str(transmitted)
        ])

        self.assertEqual(result, 0)

    def test_main_with_help(self):
        """Test main() with --help flag."""
        result, out = captured(transmit_check.main, ["--help"])

        self.assertEqual(result, 0)
        self.assertIn("transmit_check", out.lower())

    def test_main_with_unknown_flag(self):
        """Test main() with unknown flag."""
        result, out = captured(transmit_check.main, ["--unknown-flag"])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_no_args(self):
        """Test main() with no arguments."""
        result, out = captured(transmit_check.main, [])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_one_file_only(self):
        """Test main() with only one file."""
        source = self.tmp_path / "source.md"
        source.write_text("# Source")

        result, out = captured(transmit_check.main, [str(source)])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_nonexistent_file(self):
        """Test main() with nonexistent file."""
        transmitted = self.tmp_path / "transmitted.md"
        transmitted.write_text("# Transmitted")

        result, out = captured(
            transmit_check.main,
            [str(self.tmp_path / "nonexistent.md"), str(transmitted)])

        self.assertEqual(result, 2)
        self.assertIn("error", out.lower())

    def test_main_pass_returns_zero(self):
        """Test that main() returns 0 when check passes."""
        source = self.tmp_path / "source.md"
        transmitted = self.tmp_path / "transmitted.md"

        source.write_text("# Source\n\nVersion 2.0.")
        transmitted.write_text("# Transmitted\n\nVersion 2.0.")

        result = transmit_check.main([str(source), str(transmitted)])

        self.assertEqual(result, 0)

    def test_main_fail_returns_one(self):
        """Test that main() returns 1 when check fails."""
        source = self.tmp_path / "source.md"
        transmitted = self.tmp_path / "transmitted.md"

        source.write_text("# Source\n\nVersion 2.0 and 3.0.")
        transmitted.write_text("# Transmitted\n\nVersion 2.0.")  # Lost 3.0

        result = transmit_check.main([str(source), str(transmitted)])

        self.assertEqual(result, 1)

    def test_main_mixed_flags(self):
        """Test main() with mixed --require and --order flags."""
        source = self.tmp_path / "source.md"
        transmitted = self.tmp_path / "transmitted.md"

        source.write_text("# Source\n\nFirst alpha, then beta with API_KEY.")
        transmitted.write_text("# Transmitted\n\nFirst alpha, then beta with API_KEY.")

        result = transmit_check.main([
            "--require", "API_KEY",
            "--order", "alpha",
            "--require", "2.0",
            "--order", "beta",
            str(source), str(transmitted)
        ])

        # Should handle mixed flags correctly
        self.assertIn(result, [0, 1])


if __name__ == '__main__':
    unittest.main()
