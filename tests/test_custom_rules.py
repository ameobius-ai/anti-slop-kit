"""Tests for custom_rules module.

Part of issue #228: Add custom pattern rules support
Tests YAML-based custom pattern loading and application.
"""

import pytest
import tempfile
from pathlib import Path

from tools.aslint.custom_rules import (
    load_yaml_file, validate_rules, load_custom_rules,
    apply_custom_rules, find_custom_rules_files, merge_findings,
    CustomRulesError
)


class TestYAMLParsing:
    """Tests for YAML file parsing."""
    
    def test_parse_simple_yaml(self, tmp_path):
        """Test parsing simple key-value YAML."""
        yaml_file = tmp_path / "simple.yaml"
        yaml_file.write_text("""
name: test-rules
description: Test rules
version: 1.0
""")
        
        result = load_yaml_file(str(yaml_file))
        
        assert result['name'] == 'test-rules'
        assert result['description'] == 'Test rules'
        assert result['version'] == 1.0
    
    def test_parse_yaml_with_list(self, tmp_path):
        """Test parsing YAML with list."""
        yaml_file = tmp_path / "list.yaml"
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
        
        assert 'rules' in result
        assert len(result['rules']) == 2
        assert result['rules'][0]['id'] == 'rule1'
        assert result['rules'][1]['id'] == 'rule2'
    
    def test_parse_quoted_strings(self, tmp_path):
        """Test parsing quoted strings."""
        yaml_file = tmp_path / "quoted.yaml"
        yaml_file.write_text("""
name: "test-rules"
description: 'Test description'
""")
        
        result = load_yaml_file(str(yaml_file))
        
        assert result['name'] == 'test-rules'
        assert result['description'] == 'Test description'
    
    def test_parse_boolean_values(self, tmp_path):
        """Test parsing boolean values."""
        yaml_file = tmp_path / "bool.yaml"
        yaml_file.write_text("""
enabled: true
disabled: false
""")
        
        result = load_yaml_file(str(yaml_file))
        
        assert result['enabled'] is True
        assert result['disabled'] is False
    
    def test_parse_comments(self, tmp_path):
        """Test that comments are ignored."""
        yaml_file = tmp_path / "comments.yaml"
        yaml_file.write_text("""
# This is a comment
name: test-rules
# Another comment
description: Test
""")
        
        result = load_yaml_file(str(yaml_file))
        
        assert result['name'] == 'test-rules'
        assert result['description'] == 'Test'


class TestRuleValidation:
    """Tests for rule validation."""
    
    def test_validate_valid_rules(self, tmp_path):
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
        
        assert len(validated) == 2
        assert validated[0]['id'] == 'rule1'
        assert validated[0]['severity'] == 'high'
        assert validated[1]['category'] == 'custom'
    
    def test_validate_missing_rules_key(self):
        """Test validation fails when 'rules' key is missing."""
        rules_data = {'name': 'test'}
        
        with pytest.raises(CustomRulesError, match="missing 'rules' key"):
            validate_rules(rules_data, 'test.yaml')
    
    def test_validate_rules_not_list(self):
        """Test validation fails when 'rules' is not a list."""
        rules_data = {'rules': 'not a list'}
        
        with pytest.raises(CustomRulesError, match="'rules' must be a list"):
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
        
        with pytest.raises(CustomRulesError, match="missing required field 'message'"):
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
        
        with pytest.raises(CustomRulesError, match="invalid severity"):
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
        
        with pytest.raises(CustomRulesError, match="invalid regex pattern"):
            validate_rules(rules_data, 'test.yaml')


class TestLoadCustomRules:
    """Tests for loading custom rules from files."""
    
    def test_load_single_file(self, tmp_path):
        """Test loading rules from single file."""
        yaml_file = tmp_path / "rules.yaml"
        yaml_file.write_text("""
name: test-rules
rules:
  - id: rule1
    pattern: "foo"
    severity: high
    message: "Found {match}"
""")
        
        rules = load_custom_rules([str(yaml_file)])
        
        assert len(rules) == 1
        assert rules[0]['id'] == 'rule1'
    
    def test_load_multiple_files(self, tmp_path):
        """Test loading rules from multiple files."""
        file1 = tmp_path / "rules1.yaml"
        file1.write_text("""
rules:
  - id: rule1
    pattern: "foo"
    severity: high
    message: "Found {match}"
""")
        
        file2 = tmp_path / "rules2.yaml"
        file2.write_text("""
rules:
  - id: rule2
    pattern: "bar"
    severity: medium
    message: "Found {match}"
""")
        
        rules = load_custom_rules([str(file1), str(file2)])
        
        assert len(rules) == 2
        assert rules[0]['id'] == 'rule1'
        assert rules[1]['id'] == 'rule2'
    
    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file raises error."""
        with pytest.raises(CustomRulesError, match="Rules file not found"):
            load_custom_rules(['/nonexistent/rules.yaml'])


class TestApplyCustomRules:
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
        
        assert len(findings) == 2
        assert all(f['rule_id'] == 'test-rule' for f in findings)
        assert all(f['match'] == 'foo' for f in findings)
    
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
        
        assert len(findings) == 2
        assert any(f['rule_id'] == 'rule1' for f in findings)
        assert any(f['rule_id'] == 'rule2' for f in findings)
    
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
        
        assert len(findings) == 3
    
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
        
        assert len(findings) == 1
        assert findings[0]['line'] == 2
        assert findings[0]['column'] > 0
    
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
        
        assert len(findings) == 1
        assert 'foo' in findings[0]['message']
        assert '{match}' not in findings[0]['message']
    
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
        
        assert len(findings) == 0
    
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
        
        assert len(findings) == 2
        matches = [f['match'] for f in findings]
        assert 'foo' in matches
        assert 'bar' in matches


class TestFindCustomRulesFiles:
    """Tests for finding custom rules files."""
    
    def test_find_project_rules(self, tmp_path, monkeypatch):
        """Test finding project-level rules file."""
        # Create .anti-slop/rules.yaml in temp directory
        anti_slop_dir = tmp_path / ".anti-slop"
        anti_slop_dir.mkdir()
        rules_file = anti_slop_dir / "rules.yaml"
        rules_file.write_text("name: test")
        
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        found = find_custom_rules_files()
        
        assert len(found) == 1
        assert str(rules_file) in found[0]
    
    def test_find_additional_paths(self, tmp_path):
        """Test finding rules in additional paths."""
        custom_file = tmp_path / "custom.yaml"
        custom_file.write_text("name: test")
        
        found = find_custom_rules_files([str(custom_file)])
        
        assert len(found) >= 1
        assert str(custom_file) in found


class TestMergeFindings:
    """Tests for merging built-in and custom findings."""
    
    def test_merge_empty_findings(self):
        """Test merging when both lists are empty."""
        result = merge_findings([], [])
        assert result == []
    
    def test_merge_builtin_only(self):
        """Test merging with only built-in findings."""
        builtin = [
            {'line': 1, 'column': 5, 'message': 'Builtin finding'}
        ]
        
        result = merge_findings(builtin, [])
        
        assert len(result) == 1
        assert result[0]['message'] == 'Builtin finding'
    
    def test_merge_custom_only(self):
        """Test merging with only custom findings."""
        custom = [
            {'line': 2, 'column': 10, 'message': 'Custom finding'}
        ]
        
        result = merge_findings([], custom)
        
        assert len(result) == 1
        assert result[0]['message'] == 'Custom finding'
    
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
        
        assert len(result) == 4
        # Should be sorted by line, then column
        assert result[0]['line'] == 1
        assert result[0]['column'] == 5  # Custom 1
        assert result[1]['line'] == 1
        assert result[1]['column'] == 10  # Builtin 2
        assert result[2]['line'] == 2
        assert result[3]['line'] == 3


class TestCustomRulesIntegration:
    """Integration tests for custom rules."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete workflow from YAML to findings."""
        # Create YAML file
        yaml_file = tmp_path / "rules.yaml"
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
        assert len(findings) == 3
        assert any(f['match'] == 'leverage' for f in findings)
        assert any(f['match'] == 'synergy' for f in findings)
        assert any(f['match'] == 'foo' for f in findings)
        assert all(f['severity'] in ('high', 'medium') for f in findings)
