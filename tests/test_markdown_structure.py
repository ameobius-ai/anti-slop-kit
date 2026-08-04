#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the markdown structure analyzer. Standard library only."""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


en = load("en/ste-lint.py", "ste_lint")
MarkdownStructureAnalyzer = en.MarkdownStructureAnalyzer
check_markdown_structure = en.check_markdown_structure


class TestMarkdownStructure(unittest.TestCase):

    def setUp(self):
        self.analyzer = MarkdownStructureAnalyzer()

    def check(self, method, lines):
        method(lines)
        return self.analyzer.violations

    def test_heading_hierarchy_skip(self):
        lines = [
            '# Main Title',
            'Some text here.',
            '### Subsection',
            'More text.'
        ]
        violations = self.check(self.analyzer.check_heading_hierarchy, lines)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'md_heading_skip')

    def test_heading_hierarchy_correct(self):
        lines = [
            '# Main Title',
            '## Section',
            '### Subsection',
            '## Another Section'
        ]
        violations = self.check(self.analyzer.check_heading_hierarchy, lines)
        self.assertEqual(len(violations), 0)

    def test_section_too_long(self):
        lines = ['# Section'] + ['Text line.'] * 35
        violations = self.check(self.analyzer.check_section_lengths, lines)
        self.assertTrue(any(v['rule'] == 'md_section_too_long' for v in violations))

    def test_section_too_short(self):
        lines = [
            '# Section',
            'Just one line.',
            '# Next Section',
            'More content here.'
        ]
        violations = self.check(self.analyzer.check_section_lengths, lines)
        self.assertTrue(any(v['rule'] == 'md_section_too_short' for v in violations))

    def test_code_block_without_language(self):
        lines = [
            'Some text.',
            '`' + '`' + '`',
            'code here',
            '`' + '`' + '`'
        ]
        violations = self.check(self.analyzer.check_code_blocks, lines)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'md_code_no_lang')

    def test_code_block_with_language(self):
        lines = [
            '`' + '`' + '`python',
            'def hello():',
            '    pass',
            '`' + '`' + '`'
        ]
        violations = self.check(self.analyzer.check_code_blocks, lines)
        self.assertEqual(len(violations), 0)

    def test_list_abuse(self):
        lines = ['- Item ' + str(i) for i in range(8)]
        violations = self.check(self.analyzer.check_list_abuse, lines)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'md_list_abuse')

    def test_normal_list(self):
        lines = ['- Item 1', '- Item 2', '- Item 3']
        violations = self.check(self.analyzer.check_list_abuse, lines)
        self.assertEqual(len(violations), 0)

    def test_integration(self):
        lines = [
            '# Title',
            '### Skipped H2',
            '`' + '`' + '`',
            'code',
            '`' + '`' + '`',
            '- Item 1',
            '- Item 2',
            '- Item 3',
            '- Item 4',
            '- Item 5',
            '- Item 6',
            '- Item 7'
        ]
        violations = check_markdown_structure(lines)
        rules = [v['rule'] for v in violations]
        self.assertIn('md_heading_skip', rules)
        self.assertIn('md_code_no_lang', rules)
        self.assertIn('md_list_abuse', rules)


if __name__ == '__main__':
    unittest.main()
