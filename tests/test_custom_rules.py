"""Tests for custom_rules module.

Part of issue #228: Add custom pattern rules support
Tests YAML-based custom pattern loading and application.
Ported to unittest so scripts/check.sh collects it (issue #242).
"""

import os
import tempfile
import unittest
from pathlib import Path

from tools.aslint.custom_rules import (
    load_yaml_file, validate_rules, load_custom_rules,
    apply_custom_rules, find_custom_rules_files, merge_findings,
    CustomRulesError
)


class WithTmpDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)


class TestYAMLParsing(WithTmpDir):
    """Tests for YAML file parsing."""

    def test_parse_simple_yaml(self):
        """Test parsing simple key-value YAML."""
        yaml_file = self.tmp_path / "simple.yaml"
        yaml_file.write_text("""
name: test-rules
description: Test rules
version: 1.0
""")

        result = load_yaml_file(str(yaml_file))

        self.assertEqual(result['name'], 'test-rules')
        self.assertEqual(result['description'], 'Test rules')
        self.assertEqual(result['version'], 1.0)

    def test_parse_yaml_with_list(self):
        """Test parsing YAML with list."""
        yaml_file = self.tmp_path / "list.yaml"
        yaml_file.write_text("""
name: test-rules
rules:
  - id: rule1
    pattern: "foo"
    severity: high
    message: "Found foo"
  - id: rule2
    pattern: "bar"
    severity: medium
    message: "Found bar"
""")

        result = load_yaml_file(str(yaml_file))

        self.assertIn('rules', result)
        self.assertEqual(len(result['rules']), 2)
        self.assertEqual(result['rules'][0]['id'], 'rule1')
        self.assertEqual(result['rules'][1]['id'], 'rule2')

    def test_parse_quoted_strings(self):
        """Test parsing quoted strings."""
        yaml_file = self.tmp_path / "quoted.yaml"
        yaml_file.write_text("""
name: "test-rules"
description: 'Test description'
""")

        result = load_yaml_file(str(yaml_file))

        self.assertEqual(result['name'], 'test-rules')
        self.assertEqual(result['description'], 'Test description')

    def test_parse_boolean_values(self):
        """Test parsing boolean values."""
        yaml_file = self.tmp_path / "bool.yaml"
        yaml_file.write_text("""
enabled: true
disabled: false
""")

        result = load_yaml_file(str(yaml_file))

        self.assertIs(result['enabled'], True)
        self.assertIs(result['disabled'], False)

    def test_parse_comments(self):
        """Test that comments are ignored."""
        yaml_file = self.tmp_path / "comments.yaml"
        yaml_file.write_text("""
# This is a comment
name: test-rules
# Another comment
description: Test
""")

        result = load_yaml_file(str(yaml_file))

        self.assertEqual(result['name'], 'test-rules')
        self.assertEqual(result['description'], 'Test')


class TestRuleValidation(unittest.TestCase):
    """Tests for rule validation."""

    def test_validate_valid_rules(self):
        """Test validation of valid rules."""
        rules_data = {
            'rules': [
                {
                    'id': 'rule1',
                    'pattern': r'\bfoo\b',
                    'severity': 'high',
                    'message': 'Found {match}'
                },
                {
                    'id': 'rule2',
                    'pattern': r'bar|baz',
                    'severity': 'medium',
                    'message': 'Found {match}',
                    'category': 'custom'
                }
            ]
        }

        validated = validate_rules(rules_data, 'test.yaml')

        self.assertEqual(len(validated), 2)
        self.assertEqual(validated[0]['id'], 'rule1')
        self.assertEqual(validated[0]['severity'], 'high')
        self.assertEqual(validated[1]['category'], 'custom')

    def test_validate_missing_rules_key(self):
        """Test validation fails when 'rules' key is missing."""
        rules_data = {'name': 'test'}

        with self.assertRaisesRegex(CustomRulesError, "missing 'rules' key"):
            validate_rules(rules_data, 'test.yaml')

    def test_validate_rules_not_list(self):
        """Test validation fails when 'rules' is not a list."""
        rules_data = {'rules': 'not a list'}

        with self.assertRaisesRegex(CustomRulesError, "'rules' must be a list"):
            validate_rules(rules_data, 'test.yaml')

    def test_validate_missing_required_field(self):
        """Test validation fails when required field is missing."""
        rules_data = {
            'rules': [
                {
                    'id': 'rule1',
                    'pattern': 'foo',
                    'severity': 'high'
                    # Missing 'message'
                }
            ]
        }

        with self.assertRaisesRegex(CustomRulesError, "missing required field 'message'"):
            validate_rules(rules_data, 'test.yaml')

    def test_validate_invalid_severity(self):
        """Test validation fails with invalid severity."""
        rules_data = {
            'rules': [
                {
                    'id': 'rule1',
                    'pattern': 'foo',
                    'severity': 'invalid',
                    'message': 'Found {match}'
                }
            ]
        }

        with self.assertRaisesRegex(CustomRulesError, "invalid severity"):
            validate_rules(rules_data, 'test.yaml')

    def test_validate_invalid_regex(self):
        """Test validation fails with invalid regex pattern."""
        rules_data = {
            'rules': [
                {
                    'id': 'rule1',
                    'pattern': r'[invalid(regex',
                    'severity': 'high',
                    'message': 'Found {match}'
                }
            ]
        }

        with self.assertRaisesRegex(CustomRulesError, "invalid regex pattern"):
            validate_rules(rules_data, 'test.yaml')


class TestLoadCustomRules(WithTmpDir):
    """Tests for loading custom rules from files."""

    def test_load_single_file(self):
        """Test loading rules from single file."""
        yaml_file = self.tmp_path / "rules.yaml"
        yaml_file.write_text("""
name: test-rules
rules:
  - id: rule1
    pattern: "foo"
    severity: high
    message: "Found {match}"
""")

        rules = load_custom_rules([str(yaml_file)])

        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]['id'], 'rule1')

    def test_load_multiple_files(self):
        """Test loading rules from multiple files."""
        file1 = self.tmp_path / "rules1.yaml"
        file1.write_text("""
rules:
  - id: rule1
    pattern: "foo"
    severity: high
    message: "Found {match}"
""")

        file2 = self.tmp_path / "rules2.yaml"
        file2.write_text("""
rules:
  - id: rule2
    pattern: "bar"
    severity: medium
    message: "Found {match}"
""")

        rules = load_custom_rules([str(file1), str(file2)])

        self.assertEqual(len(rules), 2)
        self.assertEqual(rules[0]['id'], 'rule1')
        self.assertEqual(rules[1]['id'], 'rule2')

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file raises error."""
        with self.assertRaisesRegex(CustomRulesError, "Rules file not found"):
            load_custom_rules(['/nonexistent/rules.yaml'])


class TestApplyCustomRules(unittest.TestCase):
    """Tests for applying custom rules to text."""

    def test_apply_single_rule(self):
        """Test applying single rule to text."""
        rules = [
            {
                'id': 'test-rule',
                'pattern': r'\bfoo\b',
                'severity': 'high',
                'message': 'Found {match}',
                'category': 'test'
            }
        ]

        text = "This is foo and more foo."
        findings = apply_custom_rules(text, rules)

        self.assertEqual(len(findings), 2)
        self.assertTrue(all(f['rule_id'] == 'test-rule' for f in findings))
        self.assertTrue(all(f['match'] == 'foo' for f in findings))

    def test_apply_multiple_rules(self):
        """Test applying multiple rules to text."""
        rules = [
            {
                'id': 'rule1',
                'pattern': r'\bfoo\b',
                'severity': 'high',
                'message': 'Found {match}',
                'category': 'test1'
            },
            {
                'id': 'rule2',
                'pattern': r'\bbar\b',
                'severity': 'medium',
                'message': 'Found {match}',
                'category': 'test2'
            }
        ]

        text = "This has foo and bar."
        findings = apply_custom_rules(text, rules)

        self.assertEqual(len(findings), 2)
        self.assertTrue(any(f['rule_id'] == 'rule1' for f in findings))
        self.assertTrue(any(f['rule_id'] == 'rule2' for f in findings))

    def test_apply_case_insensitive(self):
        """Test that pattern matching is case-insensitive."""
        rules = [
            {
                'id': 'test-rule',
                'pattern': r'\bfoo\b',
                'severity': 'high',
                'message': 'Found {match}',
                'category': 'test'
            }
        ]

        text = "This has FOO and Foo and foo."
        findings = apply_custom_rules(text, rules)

        self.assertEqual(len(findings), 3)

    def test_line_and_column_tracking(self):
        """Test that line and column numbers are tracked."""
        rules = [
            {
                'id': 'test-rule',
                'pattern': r'\bfoo\b',
                'severity': 'high',
                'message': 'Found {match}',
                'category': 'test'
            }
        ]

        text = "Line one.\nLine two with foo.\nLine three."
        findings = apply_custom_rules(text, rules)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['line'], 2)
        self.assertGreater(findings[0]['column'], 0)

    def test_message_placeholder_replacement(self):
        """Test that {match} placeholder is replaced."""
        rules = [
            {
                'id': 'test-rule',
                'pattern': r'\bfoo\b',
                'severity': 'high',
                'message': 'Avoid using {match} in text',
                'category': 'test'
            }
        ]

        text = "This has foo."
        findings = apply_custom_rules(text, rules)

        self.assertEqual(len(findings), 1)
        self.assertIn('foo', findings[0]['message'])
        self.assertNotIn('{match}', findings[0]['message'])

    def test_no_matches(self):
        """Test when no patterns match."""
        rules = [
            {
                'id': 'test-rule',
                'pattern': r'\bfoo\b',
                'severity': 'high',
                'message': 'Found {match}',
                'category': 'test'
            }
        ]

        text = "This has bar and baz."
        findings = apply_custom_rules(text, rules)

        self.assertEqual(len(findings), 0)

    def test_regex_pattern(self):
        """Test that regex patterns work correctly."""
        rules = [
            {
                'id': 'test-rule',
                'pattern': r'\b(foo|bar)\b',
                'severity': 'high',
                'message': 'Found {match}',
                'category': 'test'
            }
        ]

        text = "This has foo and bar."
        findings = apply_custom_rules(text, rules)

        self.assertEqual(len(findings), 2)
        matches = [f['match'] for f in findings]
        self.assertIn('foo', matches)
        self.assertIn('bar', matches)


class TestFindCustomRulesFiles(WithTmpDir):
    """Tests for finding custom rules files."""

    def test_find_project_rules(self):
        """Test finding project-level rules file."""
        # Create .anti-slop/rules.yaml in temp directory
        anti_slop_dir = self.tmp_path / ".anti-slop"
        anti_slop_dir.mkdir()
        rules_file = anti_slop_dir / "rules.yaml"
        rules_file.write_text("name: test")

        # Change to temp directory (monkeypatch.chdir equivalent)
        old_cwd = os.getcwd()
        os.chdir(self.tmp_path)
        try:
            found = find_custom_rules_files()
        finally:
            os.chdir(old_cwd)

        self.assertGreaterEqual(len(found), 1)
        # Project rules are reported as the relative path .anti-slop/rules.yaml
        self.assertTrue(any(f.replace(os.sep, "/").endswith(".anti-slop/rules.yaml")
                            for f in found))

    def test_find_additional_paths(self):
        """Test finding rules in additional paths."""
        custom_file = self.tmp_path / "custom.yaml"
        custom_file.write_text("name: test")

        found = find_custom_rules_files([str(custom_file)])

        self.assertGreaterEqual(len(found), 1)
        self.assertIn(str(custom_file), found)


class TestMergeFindings(unittest.TestCase):
    """Tests for merging built-in and custom findings."""

    def test_merge_empty_findings(self):
        """Test merging when both lists are empty."""
        result = merge_findings([], [])
        self.assertEqual(result, [])

    def test_merge_builtin_only(self):
        """Test merging with only built-in findings."""
        builtin = [
            {'line': 1, 'column': 5, 'message': 'Builtin finding'}
        ]

        result = merge_findings(builtin, [])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['message'], 'Builtin finding')

    def test_merge_custom_only(self):
        """Test merging with only custom findings."""
        custom = [
            {'line': 2, 'column': 10, 'message': 'Custom finding'}
        ]

        result = merge_findings([], custom)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['message'], 'Custom finding')

    def test_merge_both_sorted(self):
        """Test merging both lists with proper sorting."""
        builtin = [
            {'line': 2, 'column': 5, 'message': 'Builtin 1'},
            {'line': 1, 'column': 10, 'message': 'Builtin 2'}
        ]

        custom = [
            {'line': 1, 'column': 5, 'message': 'Custom 1'},
            {'line': 3, 'column': 1, 'message': 'Custom 2'}
        ]

        result = merge_findings(builtin, custom)

        self.assertEqual(len(result), 4)
        # Should be sorted by line, then column
        self.assertEqual(result[0]['line'], 1)
        self.assertEqual(result[0]['column'], 5)  # Custom 1
        self.assertEqual(result[1]['line'], 1)
        self.assertEqual(result[1]['column'], 10)  # Builtin 2
        self.assertEqual(result[2]['line'], 2)
        self.assertEqual(result[3]['line'], 3)


class TestCustomRulesIntegration(WithTmpDir):
    """Integration tests for custom rules."""

    def test_full_workflow(self):
        """Test complete workflow from YAML to findings."""
        # Create YAML file
        yaml_file = self.tmp_path / "rules.yaml"
        yaml_file.write_text("""
name: project-rules
description: Custom rules for project
version: 1.0
rules:
  - id: avoid-jargon
    pattern: "synergy|paradigm|leverage"
    severity: high
    message: "Avoid corporate jargon: {match}"
    category: jargon
  - id: domain-terms
    pattern: "foo|bar"
    severity: medium
    message: "Consider better terms: {match}"
    category: domain
""")

        # Load rules
        rules = load_custom_rules([str(yaml_file)])

        # Apply to text
        text = "We leverage synergy to create foo solutions."
        findings = apply_custom_rules(text, rules)

        # Verify
        self.assertEqual(len(findings), 3)
        self.assertTrue(any(f['match'] == 'leverage' for f in findings))
        self.assertTrue(any(f['match'] == 'synergy' for f in findings))
        self.assertTrue(any(f['match'] == 'foo' for f in findings))
        self.assertTrue(all(f['severity'] in ('high', 'medium') for f in findings))


if __name__ == '__main__':
    unittest.main()
