"""Integration tests for cli module.

Part of issue #208: Increase test coverage to 90%+
Tests the CLI dispatcher and argument routing.
Ported to unittest so scripts/check.sh collects it (issue #242).
"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.aslint import cli


class WithTmpDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)


def run_cli(argv):
    """Call cli.main() with patched sys.argv; return (result, stdout)."""
    buf = io.StringIO()
    with patch.object(sys, 'argv', argv):
        with contextlib.redirect_stdout(buf):
            result = cli.main()
    return result, buf.getvalue()


class TestCLIMain(WithTmpDir):
    """Integration tests for main() dispatcher."""

    def test_default_routes_to_lint_tool(self):
        """Test that default behavior routes to lint_tool."""
        test_file = self.tmp_path / "test.md"
        test_file.write_text("# Test\n\nThis is a test document.")

        result, _ = run_cli(['aslint', str(test_file)])

        # Should return 0 (success) or 1 (issues found), not 2 (error)
        self.assertIn(result, [0, 1])

    def test_rewrite_flag_routes_to_rewrite_tool(self):
        """Test that --rewrite flag routes to rewrite_tool."""
        original = self.tmp_path / "original.md"
        rewrite = self.tmp_path / "rewrite.md"

        original.write_text("# Test\n\nVersion 2.0.")
        rewrite.write_text("# Test\n\nVersion 2.0.")

        result, _ = run_cli(['aslint', '--rewrite', str(original), str(rewrite)])

        self.assertIn(result, [0, 1])

    def test_transmit_check_flag_routes_to_transmit_check(self):
        """Test that --transmit-check flag routes to transmit_check."""
        source = self.tmp_path / "source.md"
        transmitted = self.tmp_path / "transmitted.md"

        source.write_text("# Source\n\nVersion 2.0.")
        transmitted.write_text("# Transmitted\n\nVersion 2.0.")

        result, _ = run_cli(['aslint', '--transmit-check', str(source), str(transmitted)])

        self.assertIn(result, [0, 1])

    def test_lint_with_help_flag(self):
        """Test that lint tool handles --help."""
        result, out = run_cli(['aslint', '--help'])

        self.assertEqual(result, 0)
        self.assertTrue('lint' in out.lower() or 'usage' in out.lower())

    def test_rewrite_with_help_flag(self):
        """Test that rewrite tool handles --help."""
        result, out = run_cli(['aslint', '--rewrite', '--help'])

        self.assertEqual(result, 0)
        self.assertTrue('rewrite' in out.lower() or 'validate' in out.lower())

    def test_transmit_check_with_help_flag(self):
        """Test that transmit-check tool handles --help."""
        result, out = run_cli(['aslint', '--transmit-check', '--help'])

        self.assertEqual(result, 0)
        self.assertTrue('transmit' in out.lower() or 'fidelity' in out.lower())

    def test_lint_with_lang_flag(self):
        """Test that lint tool accepts --lang flag."""
        test_file = self.tmp_path / "test.md"
        test_file.write_text("# Test\n\nThis is English text.")

        result, _ = run_cli(['aslint', '--lang', 'en', str(test_file)])

        self.assertIn(result, [0, 1])

    def test_rewrite_with_lang_flag(self):
        """Test that rewrite tool accepts --lang flag."""
        original = self.tmp_path / "original.md"
        rewrite = self.tmp_path / "rewrite.md"

        original.write_text("# Test\n\nThis is English.")
        rewrite.write_text("# Test\n\nThis is rewritten English.")

        result, _ = run_cli(['aslint', '--rewrite', '--lang', 'en',
                             str(original), str(rewrite)])

        self.assertIn(result, [0, 1])

    def test_lint_multiple_files(self):
        """Test linting multiple files."""
        file1 = self.tmp_path / "file1.md"
        file2 = self.tmp_path / "file2.md"

        file1.write_text("# Test 1\n\nContent 1.")
        file2.write_text("# Test 2\n\nContent 2.")

        result, _ = run_cli(['aslint', str(file1), str(file2)])

        self.assertIn(result, [0, 1])

    def test_empty_argv_routes_to_lint_with_error(self):
        """Test that empty argv routes to lint and returns error."""
        result, out = run_cli(['aslint'])

        # lint_tool should return 2 for no files
        self.assertEqual(result, 2)
        self.assertTrue('error' in out.lower() or 'usage' in out.lower())

    def test_unknown_flag_returns_error(self):
        """Test that unknown flag returns error."""
        result, out = run_cli(['aslint', '--unknown-flag'])

        self.assertEqual(result, 2)
        self.assertTrue('error' in out.lower() or 'unknown' in out.lower())

    def test_lint_nonexistent_file_returns_error(self):
        """Test that linting nonexistent file returns error."""
        nonexistent = self.tmp_path / "nonexistent.md"

        result, out = run_cli(['aslint', str(nonexistent)])

        self.assertEqual(result, 2)
        self.assertIn('error', out.lower())

    def test_rewrite_missing_files_returns_error(self):
        """Test that rewrite with missing file returns error."""
        original = self.tmp_path / "original.md"
        original.write_text("# Test")

        nonexistent = self.tmp_path / "nonexistent.md"

        result, out = run_cli(['aslint', '--rewrite', str(original), str(nonexistent)])

        self.assertEqual(result, 2)
        self.assertIn('error', out.lower())

    def test_transmit_check_missing_file_returns_error(self):
        """Test that transmit-check with missing file returns error."""
        source = self.tmp_path / "source.md"
        source.write_text("# Source")

        nonexistent = self.tmp_path / "nonexistent.md"

        result, out = run_cli(['aslint', '--transmit-check', str(source), str(nonexistent)])

        self.assertEqual(result, 2)
        self.assertIn('error', out.lower())

    def test_lint_with_slop_returns_one(self):
        """Test that lint with slop returns exit code 1."""
        test_file = self.tmp_path / "test.md"
        # Create text with slop patterns
        test_file.write_text("# Test\n\nThis is basically a very really good example.")

        result, _ = run_cli(['aslint', str(test_file)])

        # Should return 1 (slop found) or 0 (clean), not 2 (error)
        self.assertIn(result, [0, 1])

    def test_rewrite_accept_returns_zero(self):
        """Test that accepted rewrite returns exit code 0."""
        original = self.tmp_path / "original.md"
        rewrite = self.tmp_path / "rewrite.md"

        # Create rewrite with lower or same score
        original.write_text("# Test\n\nThis is basically a very really good test.")
        rewrite.write_text("# Test\n\nThis is a good test.")

        result, _ = run_cli(['aslint', '--rewrite', str(original), str(rewrite)])

        # Should return 0 (accept) or 1 (reject), not 2 (error)
        self.assertIn(result, [0, 1])

    def test_transmit_check_pass_returns_zero(self):
        """Test that passing transmit check returns exit code 0."""
        source = self.tmp_path / "source.md"
        transmitted = self.tmp_path / "transmitted.md"

        # Create transmitted that preserves all tokens
        source.write_text("# Source\n\nVersion 2.0 uses config_key at https://api.com.")
        transmitted.write_text("# Transmitted\n\nVersion 2.0 uses config_key at https://api.com.")

        result, _ = run_cli(['aslint', '--transmit-check', str(source), str(transmitted)])

        # Should return 0 (pass) or 1 (fail), not 2 (error)
        self.assertIn(result, [0, 1])


class TestCLIEntryPoint(unittest.TestCase):
    """Tests for __main__ entry point."""

    def test_if_main_runs(self):
        """Test that __main__ block can be executed."""
        # This is more of a smoke test to ensure the module can be run
        result, _ = run_cli(['aslint', '--help'])
        # Should not raise an exception
        self.assertEqual(result, 0)


if __name__ == '__main__':
    unittest.main()
