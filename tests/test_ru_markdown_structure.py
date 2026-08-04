import unittest
import sys
sys.path.insert(0, '../ru')

from ru_ste_lint import MarkdownStructureAnalyzer, check_markdown_structure


class TestRuMarkdownStructure(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = MarkdownStructureAnalyzer()
    
    def test_heading_hierarchy_skip(self):
        lines = [
            '# Главный заголовок',
            'Какой-то текст.',
            '### Подраздел',
            'Ещё текст.'
        ]
        violations = self.analyzer.check_heading_hierarchy(lines)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'md_heading_skip')
    
    def test_heading_hierarchy_correct(self):
        lines = [
            '# Главный заголовок',
            '## Раздел',
            '### Подраздел',
            '## Другой раздел'
        ]
        violations = self.analyzer.check_heading_hierarchy(lines)
        self.assertEqual(len(violations), 0)
    
    def test_section_too_long(self):
        lines = ['# Раздел'] + ['Строка текста.'] * 35
        violations = self.analyzer.check_section_lengths(lines)
        self.assertTrue(any(v['rule'] == 'md_section_too_long' for v in violations))
    
    def test_section_too_short(self):
        lines = [
            '# Раздел',
            'Только одна строка.',
            '# Следующий раздел',
            'Больше контента здесь.'
        ]
        violations = self.analyzer.check_section_lengths(lines)
        self.assertTrue(any(v['rule'] == 'md_section_too_short' for v in violations))
    
    def test_code_block_without_language(self):
        lines = [
            'Какой-то текст.',
            '\x60\x60\x60',
            'код здесь',
            '\x60\x60\x60'
        ]
        violations = self.analyzer.check_code_blocks(lines)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'md_code_no_lang')
    
    def test_code_block_with_language(self):
        lines = [
            '\x60\x60\x60python',
            'def hello():',
            '    pass',
            '\x60\x60\x60'
        ]
        violations = self.analyzer.check_code_blocks(lines)
        self.assertEqual(len(violations), 0)
    
    def test_list_abuse(self):
        lines = ['- Элемент ' + str(i) for i in range(8)]
        violations = self.analyzer.check_list_abuse(lines)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'md_list_abuse')
    
    def test_normal_list(self):
        lines = ['- Элемент 1', '- Элемент 2', '- Элемент 3']
        violations = self.analyzer.check_list_abuse(lines)
        self.assertEqual(len(violations), 0)
    
    def test_integration(self):
        lines = [
            '# Заголовок',
            '### Пропущен H2',
            '\x60\x60\x60',
            'код',
            '\x60\x60\x60',
            '- Элемент 1',
            '- Элемент 2',
            '- Элемент 3',
            '- Элемент 4',
            '- Элемент 5',
            '- Элемент 6',
            '- Элемент 7'
        ]
        violations = check_markdown_structure(lines)
        rules = [v['rule'] for v in violations]
        self.assertIn('md_heading_skip', rules)
        self.assertIn('md_code_no_lang', rules)
        self.assertIn('md_list_abuse', rules)


if __name__ == '__main__':
    unittest.main()
