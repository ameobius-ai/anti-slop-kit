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

