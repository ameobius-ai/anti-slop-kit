#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Russian linter analyzer. Standard library only."""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = load("ru/ru-ste-lint.py", "ru_ste_lint")
MarkdownStructureAnalyzer = _mod.MarkdownStructureAnalyzer
check_markdown_structure = _mod.check_markdown_structure


class TestRuMarkdownStructure(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = MarkdownStructureAnalyzer()
    
    def test_heading_hierarchy_skip(self):
        lines = ['# Заголовок', 'Текст.', '### Подраздел', 'Ещё.']
        self.analyzer.check_heading_hierarchy(lines)
        violations = self.analyzer.violations
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'md_heading_skip')
    
    def test_heading_hierarchy_correct(self):
        lines = ['# Заголовок', '## Раздел', '### Подраздел', '## Другой']
        self.analyzer.check_heading_hierarchy(lines)
        violations = self.analyzer.violations
        self.assertEqual(len(violations), 0)
    
    def test_section_too_long(self):
        lines = ['# Раздел'] + ['Текст.'] * 35
        self.analyzer.check_section_lengths(lines)
        violations = self.analyzer.violations
        self.assertTrue(any(v['rule'] == 'md_section_too_long' for v in violations))
    
    def test_section_too_short(self):
        lines = ['# Раздел', 'Одна строка.', '# Следующий', 'Больше.']
        self.analyzer.check_section_lengths(lines)
        violations = self.analyzer.violations
        self.assertTrue(any(v['rule'] == 'md_section_too_short' for v in violations))
    
    def test_code_block_without_language(self):
        lines = ['Текст.', '`' + '`' + '`', 'код', '`' + '`' + '`']
        self.analyzer.check_code_blocks(lines)
        violations = self.analyzer.violations
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'md_code_no_lang')
    
    def test_code_block_with_language(self):
        lines = ['`' + '`' + '`python', 'def hello():', '    pass', '`' + '`' + '`']
        self.analyzer.check_code_blocks(lines)
        violations = self.analyzer.violations
        self.assertEqual(len(violations), 0)
    
    def test_list_abuse(self):
        lines = ['- Элемент ' + str(i) for i in range(8)]
        self.analyzer.check_list_abuse(lines)
        violations = self.analyzer.violations
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'md_list_abuse')
    
    def test_normal_list(self):
        lines = ['- Элемент 1', '- Элемент 2', '- Элемент 3']
        self.analyzer.check_list_abuse(lines)
        violations = self.analyzer.violations
        self.assertEqual(len(violations), 0)
    
    def test_integration(self):
        lines = ['# Заголовок', '### Пропущен H2', '`' + '`' + '`', 'код', '`' + '`' + '`',
                 '- Элемент 1', '- Элемент 2', '- Элемент 3', '- Элемент 4', '- Элемент 5', '- Элемент 6', '- Элемент 7']
        violations = check_markdown_structure(lines)
        rules = [v['rule'] for v in violations]
        self.assertIn('md_heading_skip', rules)
        self.assertIn('md_code_no_lang', rules)
        self.assertIn('md_list_abuse', rules)


if __name__ == '__main__':
    unittest.main()
