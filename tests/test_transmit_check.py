"""Comprehensive tests for transmit_check module.

Part of issue #208: Increase test coverage to 90%+
"""

import os
import tempfile
from pathlib import Path

import pytest

from tools.aslint import transmit_check


class TestOrderingOk:
    """Tests for _ordering_ok helper function."""
    
    def test_tokens_in_order(self):
        """Test that tokens in correct order return True."""
        text = "First comes alpha, then beta, finally gamma."
        tokens = ["alpha", "beta", "gamma"]
        
        assert transmit_check._ordering_ok(text, tokens) is True
    
    def test_tokens_out_of_order(self):
        """Test that tokens in wrong order return False."""
        text = "First comes gamma, then alpha, finally beta."
        tokens = ["alpha", "beta", "gamma"]
        
        assert transmit_check._ordering_ok(text, tokens) is False
    
    def test_token_missing(self):
        """Test that missing token returns False."""
        text = "First comes alpha, then beta."
        tokens = ["alpha", "beta", "gamma"]
        
        assert transmit_check._ordering_ok(text, tokens) is False
    
    def test_empty_tokens_list(self):
        """Test with empty tokens list."""
        text = "Some text here."
        tokens = []
        
        assert transmit_check._ordering_ok(text, tokens) is True
    
    def test_single_token(self):
        """Test with single token."""
        text = "The alpha is here."
        tokens = ["alpha"]
        
        assert transmit_check._ordering_ok(text, tokens) is True
    
    def test_duplicate_tokens(self):
        """Test with duplicate tokens in list."""
        text = "First alpha, then beta, then alpha again."
        tokens = ["alpha", "beta", "alpha"]
        
        # Should check by first occurrence
        assert transmit_check._ordering_ok(text, tokens) is True


class TestTransmitCheck:
    """Tests for transmit_check function."""
    
    def test_all_checks_pass(self):
        """Test when all checks pass."""
        source = "Version 2.0 uses config_key at https://api.com."
        transmitted = "The version 2.0 uses config_key at https://api.com."
        
        result = transmit_check.transmit_check(source, transmitted)
        
        assert result["ok"] is True
        assert result["tool"] == "transmit_check"
        assert result["passed"] is True
        assert all(result["checks"].values())
    
    def test_numbers_lost(self):
        """Test when numbers are lost."""
        source = "Version 2.0 and 3.0 are available."
        transmitted = "Version 2.0 is available."
        
        result = transmit_check.transmit_check(source, transmitted)
        
        assert result["ok"] is True
        assert result["passed"] is False
        assert result["checks"]["numbers"] is False
        assert "3.0" in result["missing"]["numbers"]
    
    def test_identifiers_lost(self):
        """Test when identifiers are lost."""
        source = "Use config_key and api_secret."
        transmitted = "Use config_key."
        
        result = transmit_check.transmit_check(source, transmitted)
        
        assert result["ok"] is True
        assert result["passed"] is False
        assert result["checks"]["identifiers"] is False
        assert "api_secret" in result["missing"]["identifiers"]
    
    def test_urls_lost(self):
        """Test when URLs are lost."""
        source = "Visit https://example.com and https://test.org."
        transmitted = "Visit https://example.com."
        
        result = transmit_check.transmit_check(source, transmitted)
        
        assert result["ok"] is True
        assert result["passed"] is False
        assert result["checks"]["urls"] is False
        assert "https://test.org" in result["missing"]["urls"]
    
    def test_constraint_missing(self):
        """Test when constraint is missing."""
        source = "Some text here."
        transmitted = "Some text here."
        constraints = ["required_string"]
        
        result = transmit_check.transmit_check(source, transmitted, constraints=constraints)
        
        assert result["ok"] is True
        assert result["passed"] is False
        assert result["checks"]["constraints"] is False
        assert "required_string" in result["missing"]["constraints"]
    
    def test_constraint_present(self):
        """Test when constraint is present."""
        source = "Some text here."
        transmitted = "Some text here with required_string."
        constraints = ["required_string"]
        
        result = transmit_check.transmit_check(source, transmitted, constraints=constraints)
        
        assert result["ok"] is True
        assert result["checks"]["constraints"] is True
    
    def test_ordering_correct(self):
        """Test when ordering is correct."""
        source = "First alpha, then beta, finally gamma."
        transmitted = "First alpha, then beta, finally gamma."
        ordered = ["alpha", "beta", "gamma"]
        
        result = transmit_check.transmit_check(source, transmitted, ordered=ordered)
        
        assert result["ok"] is True
        assert result["checks"]["ordering"] is True
        assert result["ordered_tokens"] == ordered
    
    def test_ordering_incorrect(self):
        """Test when ordering is incorrect."""
        source = "First gamma, then alpha, finally beta."
        transmitted = "First gamma, then alpha, finally beta."
        ordered = ["alpha", "beta", "gamma"]
        
        result = transmit_check.transmit_check(source, transmitted, ordered=ordered)
        
        assert result["ok"] is True
        assert result["passed"] is False
        assert result["checks"]["ordering"] is False
    
    def test_empty_texts(self):
        """Test with empty texts."""
        result = transmit_check.transmit_check("", "")
        
        assert result["ok"] is True
        assert result["passed"] is True
    
    def test_multiple_failures(self):
        """Test when multiple checks fail."""
        source = "Version 2.0 uses config_key at https://api.com with required_string."
        transmitted = "This is completely different text."
        constraints = ["required_string"]
        ordered = ["2.0", "config_key"]
        
        result = transmit_check.transmit_check(source, transmitted, constraints, ordered)
        
        assert result["ok"] is True
        assert result["passed"] is False
        assert not result["checks"]["numbers"]
        assert not result["checks"]["identifiers"]
        assert not result["checks"]["urls"]
        assert not result["checks"]["constraints"]
    
    def test_none_constraints(self):
        """Test with None constraints."""
        source = "Some text."
        transmitted = "Some text."
        
        result = transmit_check.transmit_check(source, transmitted, constraints=None)
        
        assert result["ok"] is True
        assert result["checks"]["constraints"] is True
    
    def test_none_ordered(self):
        """Test with None ordered."""
        source = "Some text."
        transmitted = "Some text."
        
        result = transmit_check.transmit_check(source, transmitted, ordered=None)
        
        assert result["ok"] is True
        assert result["checks"]["ordering"] is True


class TestMain:
    """Tests for main() CLI function."""
    
    def test_main_with_valid_files(self, tmp_path):
        """Test main() with valid source and transmitted files."""
        source = tmp_path / "source.md"
        transmitted = tmp_path / "transmitted.md"
        
        source.write_text("# Source\n\nVersion 2.0.")
        transmitted.write_text("# Transmitted\n\nVersion 2.0.")
        
        result = transmit_check.main([str(source), str(transmitted)])
        
        assert result in [0, 1]
    
    def test_main_with_require_flag(self, tmp_path):
        """Test main() with --require flag."""
        source = tmp_path / "source.md"
        transmitted = tmp_path / "transmitted.md"
        
        source.write_text("# Source\n\nSome text with API_VERSION.")
        transmitted.write_text("# Transmitted\n\nSome text with API_VERSION.")
        
        result = transmit_check.main([
            "--require", "API_VERSION",
            str(source), str(transmitted)
        ])
        
        assert result == 0
    
    def test_main_with_order_flag(self, tmp_path):
        """Test main() with --order flag."""
        source = tmp_path / "source.md"
        transmitted = tmp_path / "transmitted.md"
        
        source.write_text("# Source\n\nFirst alpha, then beta.")
        transmitted.write_text("# Transmitted\n\nFirst alpha, then beta.")
        
        result = transmit_check.main([
            "--order", "alpha", "--order", "beta",
            str(source), str(transmitted)
        ])
        
        assert result == 0
    
    def test_main_with_multiple_requires(self, tmp_path):
        """Test main() with multiple --require flags."""
        source = tmp_path / "source.md"
        transmitted = tmp_path / "transmitted.md"
        
        source.write_text("# Source\n\nVersion 2.0 with API_KEY.")
        transmitted.write_text("# Transmitted\n\nVersion 2.0 with API_KEY.")
        
        result = transmit_check.main([
            "--require", "2.0", "--require", "API_KEY",
            str(source), str(transmitted)
        ])
        
        assert result == 0
    
    def test_main_with_help(self, capsys):
        """Test main() with --help flag."""
        result = transmit_check.main(["--help"])
        
        assert result == 0
        captured = capsys.readouterr()
        assert "transmit_check" in captured.out.lower()
    
    def test_main_with_unknown_flag(self, capsys):
        """Test main() with unknown flag."""
        result = transmit_check.main(["--unknown-flag"])
        
        assert result == 2
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()
    
    def test_main_no_args(self, capsys):
        """Test main() with no arguments."""
        result = transmit_check.main([])
        
        assert result == 2
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()
    
    def test_main_one_file_only(self, tmp_path, capsys):
        """Test main() with only one file."""
        source = tmp_path / "source.md"
        source.write_text("# Source")
        
        result = transmit_check.main([str(source)])
        
        assert result == 2
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()
    
    def test_main_nonexistent_file(self, tmp_path, capsys):
        """Test main() with nonexistent file."""
        transmitted = tmp_path / "transmitted.md"
        transmitted.write_text("# Transmitted")
        
        result = transmit_check.main([str(tmp_path / "nonexistent.md"), str(transmitted)])
        
        assert result == 2
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()
    
    def test_main_pass_returns_zero(self, tmp_path):
        """Test that main() returns 0 when check passes."""
        source = tmp_path / "source.md"
        transmitted = tmp_path / "transmitted.md"
        
        source.write_text("# Source\n\nVersion 2.0.")
        transmitted.write_text("# Transmitted\n\nVersion 2.0.")
        
        result = transmit_check.main([str(source), str(transmitted)])
        
        assert result == 0
    
    def test_main_fail_returns_one(self, tmp_path):
        """Test that main() returns 1 when check fails."""
        source = tmp_path / "source.md"
        transmitted = tmp_path / "transmitted.md"
        
        source.write_text("# Source\n\nVersion 2.0 and 3.0.")
        transmitted.write_text("# Transmitted\n\nVersion 2.0.")  # Lost 3.0
        
        result = transmit_check.main([str(source), str(transmitted)])
        
        assert result == 1
    
    def test_main_mixed_flags(self, tmp_path):
        """Test main() with mixed --require and --order flags."""
        source = tmp_path / "source.md"
        transmitted = tmp_path / "transmitted.md"
        
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
        assert result in [0, 1]
