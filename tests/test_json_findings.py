"""Tests for enhanced JSON output with findings (issue #17)."""

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run_lint(*args, text=None):
    """Run ste-lint.py with given arguments and optional stdin."""
    cmd = [sys.executable, str(ROOT / "en" / "ste-lint.py")] + list(args)
    result = subprocess.run(
        cmd,
        input=text,
        capture_output=True,
        text=True,
        cwd=str(ROOT)
    )
    return result


class TestJSONOutputWithFindings(unittest.TestCase):
    """Test enhanced JSON output includes detailed findings."""
    
    def setUp(self):
        """Create test file with known violations."""
        self.slop_text = """This document utilizes seamless solutions to facilitate
robust outcomes. We leverage cutting-edge technologies to empower
users and harness the power of innovation.

The vast majority of stakeholders have noted that it is important
to delve into the myriad possibilities that exist in today's
fast-paced world.

This is a very long sentence that definitely exceeds twenty words and should be flagged by the linter as a violation of the sentence length rule.
"""
        # Write to temp file
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        )
        self.temp_file.write(self.slop_text)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up temp file."""
        import os
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
    
    def test_json_output_is_valid_json(self):
        """JSON output must be parseable."""
        result = run_lint("--json", self.temp_file.name)
        # Should be valid JSON
        data = json.loads(result.stdout)
        self.assertIsInstance(data, dict)
    
    def test_json_output_contains_findings(self):
        """JSON output must include findings array."""
        result = run_lint("--json", self.temp_file.name)
        data = json.loads(result.stdout)
        
        # Get the first file's data
        file_data = list(data.values())[0]
        
        # Should have findings key
        self.assertIn("findings", file_data)
        self.assertIsInstance(file_data["findings"], list)
    
    def test_findings_have_required_fields(self):
        """Each finding must have line, rule, match, suggestion."""
        result = run_lint("--json", self.temp_file.name)
        data = json.loads(result.stdout)
        file_data = list(data.values())[0]
        
        findings = file_data["findings"]
        self.assertGreater(len(findings), 0, "Should have at least one finding")
        
        # Check first finding
        finding = findings[0]
        required_fields = ["line", "rule", "match", "suggestion"]
        for field in required_fields:
            self.assertIn(field, finding, f"Finding must have {field} field")
    
    def test_findings_line_numbers_are_positive(self):
        """Line numbers must be positive integers."""
        result = run_lint("--json", self.temp_file.name)
        data = json.loads(result.stdout)
        file_data = list(data.values())[0]
        
        for finding in file_data["findings"]:
            self.assertIsInstance(finding["line"], int)
            self.assertGreater(finding["line"], 0)
    
    def test_findings_match_explain_output(self):
        """JSON findings should match --explain output."""
        # Get JSON output
        json_result = run_lint("--json", self.temp_file.name)
        json_data = json.loads(json_result.stdout)
        json_findings = list(json_data.values())[0]["findings"]
        
        # Get explain output
        explain_result = run_lint("--explain", self.temp_file.name)
        # First line is the summary ("words= ... per100w= ..."), findings follow
        explain_lines = explain_result.stdout.strip().split('\n')[1:]
        
        # Count findings
        self.assertEqual(
            len(json_findings),
            len(explain_lines),
            "JSON findings count should match --explain line count"
        )
    
    def test_json_backward_compatible(self):
        """JSON output must still contain original fields."""
        result = run_lint("--json", self.temp_file.name)
        data = json.loads(result.stdout)
        file_data = list(data.values())[0]
        
        # Original fields must still exist
        original_fields = [
            "words", "sentences", "violations", "per100w",
            "total", "total_per100w", "slop", "cl",
            "longest_sentence_words"
        ]
        for field in original_fields:
            self.assertIn(field, file_data, f"Original field {field} must exist")
    
    def test_json_with_max_flag(self):
        """JSON output works with --max flag."""
        result = run_lint("--json", "--max", "100", self.temp_file.name)
        # Should still produce valid JSON
        data = json.loads(result.stdout)
        self.assertIsInstance(data, dict)
    
    def test_json_with_only_flag(self):
        """JSON output respects --only flag."""
        result = run_lint("--json", "--only", "slop", self.temp_file.name)
        data = json.loads(result.stdout)
        file_data = list(data.values())[0]
        
        # Should have findings
        self.assertIn("findings", file_data)
        
        # All findings should be slop categories
        slop_categories = [
            "banned_word", "marketing_adjective", "ai_slop", "modal_hedge"
        ]
        for finding in file_data["findings"]:
            self.assertIn(
                finding["rule"],
                slop_categories,
                f"Only slop findings expected, got {finding['rule']}"
            )


if __name__ == '__main__':
    unittest.main()
