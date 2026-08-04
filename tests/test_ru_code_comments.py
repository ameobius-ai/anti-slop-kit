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
CodeCommentAnalyzer = _mod.CodeCommentAnalyzer
check_code_comments = _mod.check_code_comments


class TestRuCodeCommentAnalysis(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = CodeCommentAnalyzer()
    
    def test_low_comment_ratio(self):
        lines = ['x = ' + str(i) for i in range(30)]
        self.analyzer.check_comment_density(lines)
        violations = self.analyzer.violations
        self.assertTrue(any(v['rule'] == 'code_low_comment_ratio' for v in violations))
    
    def test_obvious_comment(self):
        lines = ['# инкремент счётчика', 'counter += 1']
        self.analyzer.check_obvious_comments(lines)
        violations = self.analyzer.violations
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'code_obvious_comment')
    
    def test_todo_comment(self):
        lines = ['# TODO: реализовать это', 'pass']
        self.analyzer.check_todo_in_comments(lines)
        violations = self.analyzer.violations
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'code_todo_comment')
    
    def test_what_not_why(self):
        lines = ['# эта функция возвращает значение', 'return value']
        self.analyzer.check_what_vs_why(lines)
        violations = self.analyzer.violations
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]['rule'], 'code_what_not_why')
    
    def test_good_comment(self):
        lines = [
            '# Использовать экспоненциальную задержку для избежания thundering herd',
            'time.sleep(2 ** attempt)',
        ]
        violations = self.analyzer.analyze(lines)
        self.assertEqual(len(violations), 0)


if __name__ == '__main__':
    unittest.main()
