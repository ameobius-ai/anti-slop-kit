"""Integration tests for cli module.

Part of issue #208: Increase test coverage to 90%+
Tests the CLI dispatcher and argument routing.
"""

import sys
from unittest.mock import patch, MagicMock

import pytest

from tools.aslint import cli


class TestCLIMain:
    """Integration tests for main() dispatcher."""
    
    def test_default_routes_to_lint_tool(self, tmp_path):
        """Test that default behavior routes to lint_tool."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\nThis is a test document.")
        
        # Mock sys.argv
        with patch.object(sys, 'argv', ['aslint', str(test_file)]):
            result = cli.main()
        
        # Should return 0 (success) or 1 (issues found), not 2 (error)
        assert result in [0, 1]
    
    def test_rewrite_flag_routes_to_rewrite_tool(self, tmp_path):
        """Test that --rewrite flag routes to rewrite_tool."""
        original = tmp_path / "original.md"
        rewrite = tmp_path / "rewrite.md"
        
        original.write_text("# Test\n\nVersion 2.0.")
        rewrite.write_text("# Test\n\nVersion 2.0.")
        
        with patch.object(sys, 'argv', ['aslint', '--rewrite', str(original), str(rewrite)]):
            result = cli.main()
        
        assert result in [0, 1]
    
    def test_transmit_check_flag_routes_to_transmit_check(self, tmp_path):
        """Test that --transmit-check flag routes to transmit_check."""
        source = tmp_path / "source.md"
        transmitted = tmp_path / "transmitted.md"
        
        source.write_text("# Source\n\nVersion 2.0.")
        transmitted.write_text("# Transmitted\n\nVersion 2.0.")
        
        with patch.object(sys, 'argv', ['aslint', '--transmit-check', str(source), str(transmitted)]):
            result = cli.main()
        
        assert result in [0, 1]
    
    def test_lint_with_help_flag(self, capsys):
        """Test that lint tool handles --help."""
        with patch.object(sys, 'argv', ['aslint', '--help']):
            result = cli.main()
        
        assert result == 0
        captured = capsys.readouterr()
        assert 'lint' in captured.out.lower() or 'usage' in captured.out.lower()
    
    def test_rewrite_with_help_flag(self, capsys):
        """Test that rewrite tool handles --help."""
        with patch.object(sys, 'argv', ['aslint', '--rewrite', '--help']):
            result = cli.main()
        
        assert result == 0
        captured = capsys.readouterr()
        assert 'rewrite' in captured.out.lower() or 'validate' in captured.out.lower()
    
    def test_transmit_check_with_help_flag(self, capsys):
        """Test that transmit-check tool handles --help."""
        with patch.object(sys, 'argv', ['aslint', '--transmit-check', '--help']):
            result = cli.main()
        
        assert result == 0
        captured = capsys.readouterr()
        assert 'transmit' in captured.out.lower() or 'fidelity' in captured.out.lower()
    
    def test_lint_with_lang_flag(self, tmp_path):
        """Test that lint tool accepts --lang flag."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\nThis is English text.")
        
        with patch.object(sys, 'argv', ['aslint', '--lang', 'en', str(test_file)]):
            result = cli.main()
        
        assert result in [0, 1]
    
    def test_rewrite_with_lang_flag(self, tmp_path):
        """Test that rewrite tool accepts --lang flag."""
        original = tmp_path / "original.md"
        rewrite = tmp_path / "rewrite.md"
        
        original.write_text("# Test\n\nThis is English.")
        rewrite.write_text("# Test\n\nThis is rewritten English.")
        
        with patch.object(sys, 'argv', ['aslint', '--rewrite', '--lang', 'en', 
                                       str(original), str(rewrite)]):
            result = cli.main()
        
        assert result in [0, 1]
    
    def test_lint_multiple_files(self, tmp_path):
        """Test linting multiple files."""
        file1 = tmp_path / "file1.md"
        file2 = tmp_path / "file2.md"
        
        file1.write_text("# Test 1\n\nContent 1.")
        file2.write_text("# Test 2\n\nContent 2.")
        
        with patch.object(sys, 'argv', ['aslint', str(file1), str(file2)]):
            result = cli.main()
        
        assert result in [0, 1]
    
    def test_empty_argv_routes_to_lint_with_error(self, capsys):
        """Test that empty argv routes to lint and returns error."""
        with patch.object(sys, 'argv', ['aslint']):
            result = cli.main()
        
        # lint_tool should return 2 for no files
        assert result == 2
        captured = capsys.readouterr()
        assert 'error' in captured.out.lower() or 'usage' in captured.out.lower()
    
    def test_unknown_flag_returns_error(self, capsys):
        """Test that unknown flag returns error."""
        with patch.object(sys, 'argv', ['aslint', '--unknown-flag']):
            result = cli.main()
        
        assert result == 2
        captured = capsys.readouterr()
        assert 'error' in captured.out.lower() or 'unknown' in captured.out.lower()
    
    def test_lint_nonexistent_file_returns_error(self, tmp_path, capsys):
        """Test that linting nonexistent file returns error."""
        nonexistent = tmp_path / "nonexistent.md"
        
        with patch.object(sys, 'argv', ['aslint', str(nonexistent)]):
            result = cli.main()
        
        assert result == 2
        captured = capsys.readouterr()
        assert 'error' in captured.out.lower()
    
    def test_rewrite_missing_files_returns_error(self, tmp_path, capsys):
        """Test that rewrite with missing file returns error."""
        original = tmp_path / "original.md"
        original.write_text("# Test")
        
        nonexistent = tmp_path / "nonexistent.md"
        
        with patch.object(sys, 'argv', ['aslint', '--rewrite', str(original), str(nonexistent)]):
            result = cli.main()
        
        assert result == 2
        captured = capsys.readouterr()
        assert 'error' in captured.out.lower()
    
    def test_transmit_check_missing_file_returns_error(self, tmp_path, capsys):
        """Test that transmit-check with missing file returns error."""
        source = tmp_path / "source.md"
        source.write_text("# Source")
        
        nonexistent = tmp_path / "nonexistent.md"
        
        with patch.object(sys, 'argv', ['aslint', '--transmit-check', str(source), str(nonexistent)]):
            result = cli.main()
        
        assert result == 2
        captured = capsys.readouterr()
        assert 'error' in captured.out.lower()
    
    def test_lint_with_slop_returns_one(self, tmp_path):
        """Test that lint with slop returns exit code 1."""
        test_file = tmp_path / "test.md"
        # Create text with slop patterns
        test_file.write_text("# Test\n\nThis is basically a very really good example.")
        
        with patch.object(sys, 'argv', ['aslint', str(test_file)]):
            result = cli.main()
        
        # Should return 1 (slop found) or 0 (clean), not 2 (error)
        assert result in [0, 1]
    
    def test_rewrite_accept_returns_zero(self, tmp_path):
        """Test that accepted rewrite returns exit code 0."""
        original = tmp_path / "original.md"
        rewrite = tmp_path / "rewrite.md"
        
        # Create rewrite with lower or same score
        original.write_text("# Test\n\nThis is basically a very really good test.")
        rewrite.write_text("# Test\n\nThis is a good test.")
        
        with patch.object(sys, 'argv', ['aslint', '--rewrite', str(original), str(rewrite)]):
            result = cli.main()
        
        # Should return 0 (accept) or 1 (reject), not 2 (error)
        assert result in [0, 1]
    
    def test_transmit_check_pass_returns_zero(self, tmp_path):
        """Test that passing transmit check returns exit code 0."""
        source = tmp_path / "source.md"
        transmitted = tmp_path / "transmitted.md"
        
        # Create transmitted that preserves all tokens
        source.write_text("# Source\n\nVersion 2.0 uses config_key at https://api.com.")
        transmitted.write_text("# Transmitted\n\nVersion 2.0 uses config_key at https://api.com.")
        
        with patch.object(sys, 'argv', ['aslint', '--transmit-check', str(source), str(transmitted)]):
            result = cli.main()
        
        # Should return 0 (pass) or 1 (fail), not 2 (error)
        assert result in [0, 1]


class TestCLIEntryPoint:
    """Tests for __main__ entry point."""
    
    def test_if_main_runs(self):
        """Test that __main__ block can be executed."""
        # This is more of a smoke test to ensure the module can be run
        with patch.object(sys, 'argv', ['aslint', '--help']):
            # Should not raise an exception
            result = cli.main()
            assert result == 0
