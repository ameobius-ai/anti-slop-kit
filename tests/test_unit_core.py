#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for the kit's core helpers: tools/aslint/common.py.

Replaces the original scaffolding, whose TODOs referenced an
`anti_slop_kit` package that never existed in this repo (#247). These
tests pin the real behavior the wrapper tools rely on.
"""
import contextlib
import importlib.util
import io
import json
import pathlib
import unittest

from tools.aslint import common

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


en = load("en/ste-lint.py", "ste_lint")


class TestDetectLang(unittest.TestCase):
    """detect_lang routes by script: any Cyrillic block means ru."""

    def test_english_text_routes_to_en(self):
        self.assertEqual(common.detect_lang("The parser reads the file."), "en")

    def test_cyrillic_text_routes_to_ru(self):
        self.assertEqual(common.detect_lang("Парсер читает файл."), "ru")

    def test_single_cyrillic_word_routes_to_ru(self):
        self.assertEqual(common.detect_lang("The файл is read."), "ru")

    def test_empty_text_defaults_to_en(self):
        self.assertEqual(common.detect_lang(""), "en")


class TestFidelityTokens(unittest.TestCase):
    """fidelity_tokens extracts numbers, identifiers, and URLs."""

    def test_extracts_all_three_groups(self):
        text = "Version 2.0 uses config_key at https://example.com/api."
        tokens = common.fidelity_tokens(text)
        self.assertEqual(tokens["numbers"], ["2.0"])
        self.assertEqual(tokens["identifiers"], ["config_key"])
        self.assertEqual(tokens["urls"], ["https://example.com/api"])

    def test_url_trailing_punctuation_is_stripped(self):
        tokens = common.fidelity_tokens("See https://example.com/a, please.")
        self.assertEqual(tokens["urls"], ["https://example.com/a"])

    def test_numbers_inside_urls_are_not_double_counted(self):
        tokens = common.fidelity_tokens("https://example.com/v2/")
        self.assertEqual(tokens["numbers"], [])
        self.assertEqual(tokens["urls"], ["https://example.com/v2/"])

    def test_identifiers_require_underscore(self):
        tokens = common.fidelity_tokens("parser config_key version2")
        self.assertEqual(tokens["identifiers"], ["config_key"])

    def test_results_are_sorted_and_unique(self):
        tokens = common.fidelity_tokens("b_token a_token b_token 3 1 3")
        self.assertEqual(tokens["identifiers"], ["a_token", "b_token"])
        self.assertEqual(tokens["numbers"], ["1", "3"])

    def test_empty_text(self):
        self.assertEqual(
            common.fidelity_tokens(""),
            {"numbers": [], "identifiers": [], "urls": []})


class TestLostTokens(unittest.TestCase):
    """lost_tokens diffs the fidelity groups between two texts."""

    def test_nothing_lost(self):
        lost = common.lost_tokens(
            "Version 2.0 at https://example.com uses config_key.",
            "2.0 config_key https://example.com all present.")
        self.assertEqual(lost, {"numbers": [], "identifiers": [], "urls": []})

    def test_reports_each_missing_group(self):
        lost = common.lost_tokens(
            "Version 2.0 uses config_key at https://example.com.",
            "No tokens survive.")
        self.assertEqual(lost["numbers"], ["2.0"])
        self.assertEqual(lost["identifiers"], ["config_key"])
        self.assertEqual(lost["urls"], ["https://example.com"])

    def test_extra_tokens_in_transmission_are_ignored(self):
        lost = common.lost_tokens("2.0", "2.0 and 9.9 plus extra_token")
        self.assertEqual(lost, {"numbers": [], "identifiers": [], "urls": []})


class TestEmit(unittest.TestCase):
    """emit writes exactly one JSON object to stdout."""

    def test_output_is_single_json_object(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            common.emit({"ok": True, "tool": "demo"})
        self.assertEqual(json.loads(buf.getvalue()), {"ok": True, "tool": "demo"})

    def test_cyrillic_is_not_ascii_escaped(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            common.emit({"msg": "готово"})
        self.assertIn("готово", buf.getvalue())


class TestRunLinterContract(unittest.TestCase):
    """run_linter guards the language key before spawning a subprocess."""

    def test_unknown_language_raises_value_error(self):
        with self.assertRaises(ValueError):
            common.run_linter("xx", "README.md")

    def test_linters_map_points_at_real_files(self):
        for lang, path in common.LINTERS.items():
            self.assertTrue(path.is_file(), lang)


class TestLintResultContract(unittest.TestCase):
    """The wrappers key on these lint() fields; renaming one breaks tools."""

    CONTRACT_KEYS = {
        "words", "sentences", "violations", "per100w", "total",
        "total_per100w", "slop", "cl", "slop_per100w", "cl_per100w",
        "longest_sentence_words",
    }

    def test_lint_result_has_contract_keys(self):
        result = en.lint("The parser reads the file.")
        self.assertTrue(self.CONTRACT_KEYS.issubset(result.keys()))

    def test_violations_is_a_dict_of_counts(self):
        result = en.lint("The parser reads the file.")
        self.assertIsInstance(result["violations"], dict)
        self.assertTrue(
            all(isinstance(v, int) for v in result["violations"].values()))

    def test_clean_text_scores_zero(self):
        result = en.lint("The parser reads the file. It writes a report.")
        self.assertEqual(result["total"], 0)


if __name__ == "__main__":
    unittest.main()
