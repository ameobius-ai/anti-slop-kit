import unittest
import sys
sys.path.insert(0, '../en')

from ste_lint import MarkdownStructureAnalyzer, check_markdown_structure


class TestMarkdownStructure(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = MarkdownStructureAnalyzer()
    
    def test_heading_hierarchy_skip(self):
        lines = ['# Main', 'Text.', '### Sub', 'More.']
        violations = self.analyzer.check_heading_hierarchy(lines)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'md_heading_skip')
    
    def test_heading_hierarchy_correct(self):
        lines = ['# Main', '## Section', '### Sub', '## Another']
        violations = self.analyzer.check_heading_hierarchy(lines)
        self.assertEqual(len(violations), 0)
    
    def test_section_too_long(self):
        lines = ['# Section'] + ['Text.'] * 35
        violations = self.analyzer.check_section_lengths(lines)
        self.assertTrue(any(v['rule'] == 'md_section_too_long' for v in violations))
    
    def test_section_too_short(self):
        lines = ['# Section', 'One line.', '# Next', 'More.']
        violations = self.analyzer.check_section_lengths(lines)
        self.assertTrue(any(v['rule'] == 'md_section_too_short' for v in violations))
    
    def test_code_block_without_language(self):
        lines = ['Text.', '`' + '`' + '`', 'code', '`' + '`' + '`']
        violations = self.analyzer.check_code_blocks(lines)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'md_code_no_lang')
    
    def test_code_block_with_language(self):
        lines = ['`' + '`' + '`python', 'def hello():', '    pass', '`' + '`' + '`']
        violations = self.analyzer.check_code_blocks(lines)
        self.assertEqual(len(violations), 0)
    
    def test_list_abuse(self):
        lines = ['- Item ' + str(i) for i in range(8)]
        violations = self.analyzer.check_list_abuse(lines)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'md_list_abuse')
    
    def test_normal_list(self):
        lines = ['- Item 1', '- Item 2', '- Item 3']
        violations = self.analyzer.check_list_abuse(lines)
        self.assertEqual(len(violations), 0)
    
    def test_integration(self):
        lines = ['# Title', '### Skipped H2', '`' + '`' + '`', 'code', '`' + '`' + '`',
                 '- Item 1', '- Item 2', '- Item 3', '- Item 4', '- Item 5', '- Item 6', '- Item 7']
        violations = check_markdown_structure(lines)
        rules = [v['rule'] for v in violations]
        self.assertIn('md_heading_skip', rules)
        self.assertIn('md_code_no_lang', rules)
        self.assertIn('md_list_abuse', rules)


if __name__ == '__main__':
    unittest.main()
