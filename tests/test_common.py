"""Comprehensive tests for common module.

Part of issue #208: Increase test coverage to 90%+
"""

import json
import os
import tempfile

import pytest

from tools.aslint import common


class TestDetectLang:
    """Tests for detect_lang function."""
    
    def test_detect_english(self):
        """Test detection of English text."""
        text = "This is English text with no Cyrillic characters."
        assert common.detect_lang(text) == "en"
    
    def test_detect_russian(self):
        """Test detection of Russian text."""
        text = "Это русский текст с кириллическими символами."
        assert common.detect_lang(text) == "ru"
    
    def test_detect_mixed_prefers_russian(self):
        """Test that Cyrillic presence routes to Russian."""
        text = "This is mixed text with русский word."
        assert common.detect_lang(text) == "ru"
    
    def test_detect_empty_text(self):
        """Test detection with empty text."""
        text = ""
        assert common.detect_lang(text) == "en"  # Default to English


class TestFidelityTokens:
    """Tests for fidelity_tokens function."""
    
    def test_extract_numbers(self):
        """Test extraction of numbers."""
        text = "There are 42 items and 3.14 is pi."
        tokens = common.fidelity_tokens(text)
        
        assert "numbers" in tokens
        assert "42" in tokens["numbers"]
        assert "3.14" in tokens["numbers"]
    
    def test_extract_identifiers(self):
        """Test extraction of identifiers with underscores."""
        text = "The config_key and API_VERSION are important."
        tokens = common.fidelity_tokens(text)
        
        assert "identifiers" in tokens
        assert "config_key" in tokens["identifiers"]
        assert "API_VERSION" in tokens["identifiers"]
    
    def test_extract_urls(self):
        """Test extraction of URLs."""
        text = "Visit https://example.com and http://test.org/path."
        tokens = common.fidelity_tokens(text)
        
        assert "urls" in tokens
        assert "https://example.com" in tokens["urls"]
        assert "http://test.org/path" in tokens["urls"]
    
    def test_url_trailing_punctuation_stripped(self):
        """Test that trailing punctuation is stripped from URLs."""
        text = "See https://example.com. and https://test.org!"
        tokens = common.fidelity_tokens(text)
        
        assert "https://example.com" in tokens["urls"]
        assert "https://test.org" in tokens["urls"]
    
    def test_empty_text(self):
        """Test with empty text."""
        tokens = common.fidelity_tokens("")
        
        assert tokens["numbers"] == []
        assert tokens["identifiers"] == []
        assert tokens["urls"] == []
    
    def test_no_identifiers_without_underscore(self):
        """Test that identifiers without underscore are not extracted."""
        text = "The config and API are important."
        tokens = common.fidelity_tokens(text)
        
        assert "config" not in tokens["identifiers"]
        assert "API" not in tokens["identifiers"]


class TestLostTokens:
    """Tests for lost_tokens function."""
    
    def test_no_tokens_lost(self):
        """Test when no tokens are lost."""
        source = "The API_VERSION is 2.0 at https://api.com."
        transmitted = "The API_VERSION remains 2.0 at https://api.com."
        
        lost = common.lost_tokens(source, transmitted)
        
        assert lost["numbers"] == []
        assert lost["identifiers"] == []
        assert lost["urls"] == []
    
    def test_number_lost(self):
        """Test when a number is lost."""
        source = "Version 2.0 and 3.0 are available."
        transmitted = "Version 2.0 is available."
        
        lost = common.lost_tokens(source, transmitted)
        
        assert "3.0" in lost["numbers"]
    
    def test_identifier_lost(self):
        """Test when an identifier is lost."""
        source = "Use config_key and api_secret."
        transmitted = "Use config_key."
        
        lost = common.lost_tokens(source, transmitted)
        
        assert "api_secret" in lost["identifiers"]
    
    def test_url_lost(self):
        """Test when a URL is lost."""
        source = "Visit https://example.com and https://test.org."
        transmitted = "Visit https://example.com."
        
        lost = common.lost_tokens(source, transmitted)
        
        assert "https://test.org" in lost["urls"]
    
    def test_multiple_tokens_lost(self):
        """Test when multiple tokens are lost."""
        source = "Version 2.0 uses config_key at https://api.com."
        transmitted = "The system works."
        
        lost = common.lost_tokens(source, transmitted)
        
        assert "2.0" in lost["numbers"]
        assert "config_key" in lost["identifiers"]
        assert "https://api.com" in lost["urls"]


class TestLintText:
    """Tests for lint_text function."""
    
    def test_lint_text_with_auto_detect(self):
        """Test lint_text with automatic language detection."""
        text = "# Test\n\nThis is English text."
        lang, result = common.lint_text(text)
        
        assert lang == "en"
        assert isinstance(result, dict)
    
    def test_lint_text_with_explicit_lang(self):
        """Test lint_text with explicit language."""
        text = "# Test\n\nThis is English text."
        lang, result = common.lint_text(text, lang="en")
        
        assert lang == "en"
        assert isinstance(result, dict)
    
    def test_lint_text_russian(self):
        """Test lint_text with Russian text."""
        text = "# Тест\n\nЭто русский текст."
        lang, result = common.lint_text(text)
        
        assert lang == "ru"
        assert isinstance(result, dict)


class TestEmit:
    """Tests for emit function."""
    
    def test_emit_simple_dict(self, capsys):
        """Test emit with simple dictionary."""
        obj = {"key": "value", "number": 42}
        common.emit(obj)
        
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        
        assert parsed["key"] == "value"
        assert parsed["number"] == 42
    
    def test_emit_unicode(self, capsys):
        """Test emit with unicode characters."""
        obj = {"text": "Русский текст"}
        common.emit(obj)
        
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        
        assert parsed["text"] == "Русский текст"
    
    def test_emit_nested_dict(self, capsys):
        """Test emit with nested dictionary."""
        obj = {
            "level1": {
                "level2": {
                    "value": 123
                }
            }
        }
        common.emit(obj)
        
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        
        assert parsed["level1"]["level2"]["value"] == 123


class TestRunLinter:
    """Tests for run_linter function."""
    
    def test_run_linter_invalid_lang(self, tmp_path):
        """Test run_linter with invalid language."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")
        
        with pytest.raises(ValueError, match="unknown language"):
            common.run_linter("invalid", str(test_file))
