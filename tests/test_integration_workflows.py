#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests: end-to-end workflows through the real entry points.

Replaces the original scaffolding, whose TODOs referenced an
`anti_slop_kit` package that never existed in this repo (#247).
Everything below drives the actual linters and wrapper tools.
"""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import tempfile
import unittest

from tools.aslint import custom_rules, rewrite_tool

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


en = load("en/ste-lint.py", "ste_lint")

CLEAN_EN = "The parser reads the file. It writes a report.\n"
SLOP_EN = "You can utilize this seamless, world-class tool.\n"


def call_main(mod, argv):
    """Run main() like a CLI call. Returns (exit code, stdout, stderr)."""
    buf, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        code = mod.main(argv)
    return code, buf.getvalue(), err.getvalue()


class WithTmpDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = pathlib.Path(self._tmp.name)

    def write(self, name, text):
        path = self.tmp_path / name
        path.write_text(text, encoding="utf-8")
        return str(path)


class TestEnCliEndToEnd(WithTmpDir):
    """The en linter CLI: files in, verdict out, exit codes honored."""

    def test_clean_file_exits_zero(self):
        path = self.write("clean.md", CLEAN_EN)
        code, out, _ = call_main(en, [path])
        self.assertEqual(code, 0)
        self.assertIn("clean.md", out)

    def test_json_payload_shape(self):
        path = self.write("slop.md", SLOP_EN)
        code, out, _ = call_main(en, ["--json", path])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(list(payload), [path])
        result = payload[path]
        self.assertGreaterEqual(result["violations"]["banned_word"], 1)
        self.assertIn("total_per100w", result)

    def test_max_gate_blocks_slop(self):
        path = self.write("slop.md", SLOP_EN)
        code, _, err = call_main(en, ["--max", "0", path])
        self.assertEqual(code, 1)
        self.assertIn("FAIL", err)

    def test_max_gate_passes_clean_file(self):
        path = self.write("clean.md", CLEAN_EN)
        code, _, _ = call_main(en, ["--max", "0", path])
        self.assertEqual(code, 0)

    def test_unreadable_file_exits_two(self):
        missing = str(self.tmp_path / "missing.md")
        code, _, err = call_main(en, [missing])
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)

    def test_unknown_option_exits_two(self):
        code, _, err = call_main(en, ["--nope"])
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)


class TestCustomRulesWorkflow(WithTmpDir):
    """The .anti-slop/rules.yaml project-rules workflow, end to end."""

    RULES_YAML = (
        "name: project-rules\n"
        "rules:\n"
        "  - id: no-foo\n"
        '    pattern: "foo"\n'
        "    severity: high\n"
        '    message: "Found foo"\n'
    )

    def test_find_load_apply_in_project_dir(self):
        rules_dir = self.tmp_path / ".anti-slop"
        rules_dir.mkdir()
        (rules_dir / "rules.yaml").write_text(self.RULES_YAML, encoding="utf-8")

        cwd = os.getcwd()
        os.chdir(self.tmp_path)
        try:
            found = custom_rules.find_custom_rules_files()
        finally:
            os.chdir(cwd)

        self.assertIn(".anti-slop/rules.yaml", found)

        rules = custom_rules.load_custom_rules([str(rules_dir / "rules.yaml")])
        self.assertEqual([r["id"] for r in rules], ["no-foo"])

        findings = custom_rules.apply_custom_rules("bar\nfoo bar\n", rules)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["rule_id"], "no-foo")
        self.assertEqual(findings[0]["line"], 2)


class TestValidateRewriteWorkflow(unittest.TestCase):
    """validate_rewrite: accept improvements, reject fidelity loss."""

    def test_improvement_is_accepted(self):
        original = "You can utilize this seamless, world-class tool.\n"
        rewrite = "You can use this tool.\n"
        result = rewrite_tool.validate_rewrite(original, rewrite, "en")
        self.assertTrue(result["ok"])
        self.assertEqual(result["verdict"], "accept")
        self.assertLess(result["score"]["rewrite_per100w"],
                        result["score"]["original_per100w"])

    def test_lost_number_is_rejected(self):
        original = "Version 2.0 reads the config_key.\n"
        rewrite = "Version 3.0 reads the config_key.\n"
        result = rewrite_tool.validate_rewrite(original, rewrite, "en")
        self.assertEqual(result["verdict"], "reject")
        self.assertIn("2.0", result["fidelity"]["numbers"])
        self.assertTrue(any("numbers" in r for r in result["reasons"]))

    def test_lang_autodetect_routes_cyrillic_to_ru(self):
        result = rewrite_tool.validate_rewrite(
            "Сервер читает файл.\n", "Сервер читает файл.\n")
        self.assertEqual(result["lang"], "ru")


if __name__ == "__main__":
    unittest.main()
