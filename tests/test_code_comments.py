import unittest
import sys
sys.path.insert(0, '../en')

from ste_lint import CodeCommentAnalyzer, check_code_comments


class TestCodeCommentAnalysis(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = CodeCommentAnalyzer()
    
    def test_low_comment_ratio(self):
        lines = ['x = ' + str(i) for i in range(30)]
        violations = self.analyzer.check_comment_density(lines)
        self.assertTrue(any(v['rule'] == 'code_low_comment_ratio' for v in violations))
    
    def test_obvious_comment(self):
        lines = ['# increment counter', 'counter += 1']
        violations = self.analyzer.check_obvious_comments(lines)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'code_obvious_comment')
    
    def test_todo_comment(self):
        lines = ['# TODO: implement this', 'pass']
        violations = self.analyzer.check_todo_in_comments(lines)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'code_todo_comment')
    
    def test_what_not_why(self):
        lines = ['# this function returns the value', 'return value']
        violations = self.analyzer.check_what_vs_why(lines)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'code_what_not_why')
    
    def test_good_comment(self):
        lines = [
            '# Use exponential backoff to avoid thundering herd on retries',
            'time.sleep(2 ** attempt)',
        ]
        violations = self.analyzer.analyze(lines)
        self.assertEqual(len(violations), 0)


if __name__ == '__main__':
    unittest.main()
