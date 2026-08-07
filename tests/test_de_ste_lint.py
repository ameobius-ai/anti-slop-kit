"""Tests for German language linter (de-ste-lint.py)

Part of issue #227: Add German language support
Tests the German language support based on Leichte Sprache principles.
"""

import pytest
from pathlib import Path
import sys

# Add de/ to path to import the linter
sys.path.insert(0, str(Path(__file__).parent.parent / "de"))
import de_ste_lint


class TestGermanLintBasic:
    """Basic functionality tests for German linter."""
    
    def test_lint_file_returns_correct_structure(self, tmp_path):
        """Test that lint_file returns expected dictionary structure."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Dies ist ein Testdokument.")
        
        result = de_ste_lint.lint_file(test_file)
        
        assert "path" in result
        assert "words" in result
        assert "violations" in result
        assert "score" in result
        assert "findings" in result
    
    def test_count_words_counts_correctly(self):
        """Test that word counting works for German text."""
        text = "Dies ist ein Testdokument mit mehreren Wörtern"
        count = de_ste_lint.count_words(text)
        assert count == 7
    
    def test_clean_german_text_has_no_violations(self, tmp_path):
        """Test that clean German text has minimal violations."""
        test_file = tmp_path / "clean.md"
        test_file.write_text("Dieses technische Dokument beschreibt das Authentifizierungssystem.")
        
        result = de_ste_lint.lint_file(test_file)
        
        # Clean text should have low score
        assert result["score"] < 5.0


class TestGermanLintPatterns:
    """Tests for German-specific pattern detection."""
    
    def test_detects_banned_words(self, tmp_path):
        """Test that banned German words are detected."""
        test_file = tmp_path / "banned.md"
        test_file.write_text("Dies ist grundsätzlich ein eigentlich einfaches Dokument.")
        
        result = de_ste_lint.lint_file(test_file)
        
        # Should detect "grundsätzlich" and "eigentlich"
        assert result["violations"] >= 2
        assert result["score"] > 0
    
    def test_detects_marketing_terms(self, tmp_path):
        """Test that marketing buzzwords are detected."""
        test_file = tmp_path / "marketing.md"
        test_file.write_text("Diese revolutionäre Lösung ist robust und skalierbar.")
        
        result = de_ste_lint.lint_file(test_file)
        
        # Should detect marketing terms
        assert result["violations"] >= 2
        findings_text = " ".join([f["word"] for f in result["findings"]])
        assert "revolutionär" in findings_text.lower() or "robust" in findings_text.lower()
    
    def test_detects_filler_phrases(self, tmp_path):
        """Test that filler phrases are detected."""
        test_file = tmp_path / "filler.md"
        test_file.write_text("Im Grunde genommen ist dieses Dokument tatsächlich einfach.")
        
        result = de_ste_lint.lint_file(test_file)
        
        # Should detect filler phrases
        assert result["violations"] >= 2
        assert result["score"] > 0


class TestGermanLintEdgeCases:
    """Edge case tests for German linter."""
    
    def test_empty_file(self, tmp_path):
        """Test handling of empty file."""
        test_file = tmp_path / "empty.md"
        test_file.write_text("")
        
        result = de_ste_lint.lint_file(test_file)
        
        assert result["words"] == 0
        assert result["violations"] == 0
        assert result["score"] == 0.0
    
    def test_special_german_characters(self, tmp_path):
        """Test handling of German special characters."""
        test_file = tmp_path / "special.md"
        test_file.write_text("Wie geht es Ihnen? Sehr gut! Der Schüler ist hier.")
        
        result = de_ste_lint.lint_file(test_file)
        
        # Should handle special characters without errors
        assert result["words"] > 0
        assert result["violations"] >= 0
    
    def test_german_umlauts(self, tmp_path):
        """Test handling of German umlauts."""
        test_file = tmp_path / "umlauts.md"
        test_file.write_text("ä ö ü Ä Ö Ü ß")
        
        result = de_ste_lint.lint_file(test_file)
        
        # Should handle all German umlauts without errors
        assert result["words"] > 0


class TestGermanLintCLI:
    """Tests for CLI functionality."""
    
    def test_main_with_valid_file(self, tmp_path, capsys):
        """Test main() with valid file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Einfaches Testdokument.")
        
        with pytest.raises(SystemExit) as exc_info:
            de_ste_lint.main([str(test_file)])
        
        # Should exit with 0 (clean) or 1 (violations)
        assert exc_info.value.code in [0, 1]
    
    def test_main_with_no_arguments(self, capsys):
        """Test main() with no arguments."""
        with pytest.raises(SystemExit) as exc_info:
            de_ste_lint.main([])
        
        # Should fail
        assert exc_info.value.code == 2
    
    def test_main_with_json_output(self, tmp_path, capsys):
        """Test main() with --json flag."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Testdokument.")
        
        with pytest.raises(SystemExit) as exc_info:
            de_ste_lint.main(["--json", str(test_file)])
        
        # Should succeed and output JSON
        assert exc_info.value.code in [0, 1]
        captured = capsys.readouterr()
        assert "{" in captured.out  # JSON output contains braces
