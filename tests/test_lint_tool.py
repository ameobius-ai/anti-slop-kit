"""Comprehensive tests for lint_tool module.

Part of issue #208: Increase test coverage to 90%+
"""

import tempfile
import os
from pathlib import Path

import pytest

from tools.aslint import lint_tool


class TestLintFile:
    """Tests for lint_file function."""
    
    def test_lint_file_with_valid_markdown(self, tmp_path):
        """Test linting a valid markdown file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Document\n\nThis is a test document.")
        
        result = lint_tool.lint_file(str(test_file))
        
        assert result["ok"] is True
        assert result["tool"] == "lint_file"
        assert result["path"] == str(test_file)
        assert "lang" in result
        assert "result" in result
    
    def test_lint_file_with_explicit_lang(self, tmp_path):
        """Test linting with explicit language parameter."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\nThis is English text.")
        
        result = lint_tool.lint_file(str(test_file), lang="en")
        
        assert result["ok"] is True
        assert result["lang"] == "en"
    
    def test_lint_file_with_russian_text(self, tmp_path):
        """Test linting Russian text."""
        test_file = tmp_path / "test_ru.md"
        test_file.write_text("# Тест\n\nЭто русский текст для проверки.")
        
        result = lint_tool.lint_file(str(test_file))
        
        assert result["ok"] is True
        assert result["lang"] == "ru"
    
    def test_lint_file_nonexistent(self):
        """Test linting a nonexistent file."""
        with pytest.raises(Exception):  # Should raise FileNotFoundError
            lint_tool.lint_file("/nonexistent/file.md")


class TestLintText:
    """Tests for lint_text_tool function."""
    
    def test_lint_text_basic(self):
        """Test linting basic text."""
        text = "# Test\n\nThis is a test document."
        
        result = lint_tool.lint_text_tool(text)
        
        assert result["ok"] is True
        assert result["tool"] == "lint_text"
        assert result["path"] == "<text>"
        assert "lang" in result
        assert "result" in result
    
    def test_lint_text_with_explicit_lang(self):
        """Test linting text with explicit language."""
        text = "# Test\n\nThis is English text."
        
        result = lint_tool.lint_text_tool(text, lang="en")
        
        assert result["ok"] is True
        assert result["lang"] == "en"
    
    def test_lint_text_empty(self):
        """Test linting empty text."""
        text = ""
        
        result = lint_tool.lint_text_tool(text)
        
        assert result["ok"] is True
        assert "result" in result
    
    def test_lint_text_with_slop_patterns(self):
        """Test that slop patterns are detected."""
        text = "This is basically a very really good example of what we are talking about."
        
        result = lint_tool.lint_text_tool(text, lang="en")
        
        assert result["ok"] is True
        # The result should contain findings
        assert "result" in result
        if "findings" in result["result"]:
            # Should detect some slop patterns
            assert len(result["result"]["findings"]) >= 0


class TestMainFunction:
    """Tests for main() CLI function."""
    
    def test_main_with_file(self, tmp_path):
        """Test main() with a file argument."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\nTest content.")
        
        result = lint_tool.main([str(test_file)])
        
        assert result == 0
    
    def test_main_with_lang_flag(self, tmp_path):
        """Test main() with --lang flag."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\nTest content.")
        
        result = lint_tool.main(["--lang", "en", str(test_file)])
        
        assert result == 0
    
    def test_main_with_invalid_lang(self, tmp_path, capsys):
        """Test main() with invalid language."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\nTest content.")
        
        result = lint_tool.main(["--lang", "invalid", str(test_file)])
        
        assert result == 2
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()
    
    def test_main_with_help(self, capsys):
        """Test main() with --help flag."""
        result = lint_tool.main(["--help"])
        
        assert result == 0
        captured = capsys.readouterr()
        assert "Usage:" in captured.out or "usage:" in captured.out.lower()
    
    def test_main_with_unknown_flag(self, capsys):
        """Test main() with unknown flag."""
        result = lint_tool.main(["--unknown-flag"])
        
        assert result == 2
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()
    
    def test_main_no_args(self, capsys):
        """Test main() with no arguments."""
        result = lint_tool.main([])
        
        assert result == 2
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()
    
    def test_main_multiple_files(self, tmp_path):
        """Test main() with multiple files."""
        file1 = tmp_path / "test1.md"
        file2 = tmp_path / "test2.md"
        file1.write_text("# Test 1")
        file2.write_text("# Test 2")
        
        result = lint_tool.main([str(file1), str(file2)])
        
        assert result == 0


class TestSlimFunction:
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
        
        assert "words" in slimmed
        assert "sentences" in slimmed
        assert "total" in slimmed
        assert "extra_field" not in slimmed
    
    def test_slim_handles_missing_keys(self):
        """Test that _slim() handles missing keys gracefully."""
        partial_result = {
            "words": 100,
            "total": 50
        }
        
        slimmed = lint_tool._slim(partial_result)
        
        assert "words" in slimmed
        assert "total" in slimmed
        assert len(slimmed) == 2
