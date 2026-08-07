"""Custom pattern rules loader and matcher.

Loads user-defined slop patterns from YAML files and applies them to text.
Custom rules complement the built-in language-specific linter patterns.

YAML format:
    name: my-project-rules
    description: Custom rules for my project
    version: 1.0
    rules:
      - id: avoid-jargon
        pattern: "synergy|paradigm|leverage"
        severity: high
        message: "Avoid corporate jargon: {match}"
        category: custom_jargon
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


class CustomRulesError(Exception):
    """Raised when custom rules are invalid."""
    pass


def load_yaml_file(path: str) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except OSError as e:
        raise CustomRulesError(f"Cannot read {path}: {e}")
    
    return _parse_yaml(content, path)


def _parse_yaml(content: str, path: str) -> Dict[str, Any]:
    """Parse YAML content into a dictionary."""
    result = {}
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if not stripped or stripped.startswith('#'):
            i += 1
            continue
        
        if ':' in line and not line.startswith(' '):
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            
            if value:
                result[key] = _parse_value(value)
            else:
                i += 1
                nested_lines = []
                while i < len(lines) and (not lines[i].strip() or lines[i].startswith('  ')):
                    nested_lines.append(lines[i])
                    i += 1
                
                if nested_lines and any(l.strip().startswith('-') for l in nested_lines):
                    result[key] = _parse_list(nested_lines)
                else:
                    result[key] = _parse_dict(nested_lines)
                continue
        i += 1
    
    return result


def _parse_value(value: str) -> Any:
    """Parse a YAML value."""
    if not value:
        return None
    
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    
    if value.lower() in ('true', 'yes'):
        return True
    if value.lower() in ('false', 'no'):
        return False
    
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    
    return value


def _parse_list(lines: List[str]) -> List[Dict[str, Any]]:
    """Parse a YAML list."""
    result = []
    current_item = {}
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        if stripped.startswith('-'):
            if current_item:
                result.append(current_item)
                current_item = {}
            
            item_content = stripped[1:].strip()
            if ':' in item_content:
                key, _, value = item_content.partition(':')
                current_item[key.strip()] = _parse_value(value.strip())
        elif ':' in stripped:
            key, _, value = stripped.partition(':')
            current_item[key.strip()] = _parse_value(value.strip())
    
    if current_item:
        result.append(current_item)
    
    return result


def _parse_dict(lines: List[str]) -> Dict[str, Any]:
    """Parse a YAML dictionary."""
    result = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if ':' in stripped:
            key, _, value = stripped.partition(':')
            result[key.strip()] = _parse_value(value.strip())
    return result



def validate_rules(rules_data: Dict[str, Any], path: str) -> List[Dict[str, Any]]:
    """Validate custom rules and return list of rule objects."""
    if 'rules' not in rules_data:
        raise CustomRulesError(f"{path}: missing 'rules' key")
    
    rules_list = rules_data['rules']
    if not isinstance(rules_list, list):
        raise CustomRulesError(f"{path}: 'rules' must be a list")
    
    validated = []
    for i, rule in enumerate(rules_list):
        if not isinstance(rule, dict):
            raise CustomRulesError(f"{path}: rule {i} must be a dictionary")
        
        for field in ('id', 'pattern', 'severity', 'message'):
            if field not in rule:
                raise CustomRulesError(f"{path}: rule {i} missing required field '{field}'")
        
        if rule['severity'] not in ('high', 'medium', 'low'):
            raise CustomRulesError(f"{path}: rule {i} has invalid severity '{rule['severity']}'")
        
        try:
            re.compile(rule['pattern'])
        except re.error as e:
            raise CustomRulesError(f"{path}: rule {i} has invalid regex pattern: {e}")
        
        validated.append({
            'id': rule['id'],
            'pattern': rule['pattern'],
            'severity': rule['severity'],
            'message': rule['message'],
            'category': rule.get('category', 'custom'),
        })
    
    return validated


def load_custom_rules(paths: List[str]) -> List[Dict[str, Any]]:
    """Load custom rules from multiple YAML files."""
    all_rules = []
    
    for path in paths:
        if not os.path.exists(path):
            raise CustomRulesError(f"Rules file not found: {path}")
        
        rules_data = load_yaml_file(path)
        validated = validate_rules(rules_data, path)
        all_rules.extend(validated)
    
    return all_rules


def apply_custom_rules(text: str, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply custom rules to text and return findings."""
    findings = []
    lines = text.split('\n')
    
    for rule in rules:
        pattern = re.compile(rule['pattern'], re.IGNORECASE)
        
        for line_num, line in enumerate(lines, 1):
            for match in pattern.finditer(line):
                matched_text = match.group(0)
                message = rule['message'].replace('{match}', matched_text)
                
                findings.append({
                    'rule_id': rule['id'],
                    'category': rule['category'],
                    'severity': rule['severity'],
                    'message': message,
                    'match': matched_text,
                    'line': line_num,
                    'column': match.start() + 1,
                })
    
    return findings


def find_custom_rules_files(search_paths: Optional[List[str]] = None) -> List[str]:
    """Find custom rules files in standard locations."""
    found = []
    
    project_rules = Path('.anti-slop/rules.yaml')
    if project_rules.exists():
        found.append(str(project_rules))
    
    user_rules = Path.home() / '.anti-slop' / 'rules.yaml'
    if user_rules.exists():
        found.append(str(user_rules))
    
    if search_paths:
        for path in search_paths:
            if os.path.exists(path):
                found.append(path)
    
    return found


def merge_findings(builtin_findings: List[Dict[str, Any]], 
                   custom_findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge built-in and custom findings, sorting by line and column."""
    all_findings = builtin_findings + custom_findings
    all_findings.sort(key=lambda f: (f.get('line', 0), f.get('column', 0)))
    return all_findings
