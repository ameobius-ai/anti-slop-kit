#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate tests for --max in all five linters (issues #241, #246, #250).

de/fr accepted --max but never parsed its value, so the threshold never
fired and every run exited 0 (#241). en/ru parsed it but crashed with
ValueError on a non-numeric value (#246). es had no --max parsing and no
main(argv) at all (#250). These tests are unittest-style, so the standard
gate (scripts/check.sh) actually runs them.
"""
import contextlib
import importlib.util
import io
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


de = load("de/de-ste-lint.py", "de_ste_lint")
fr = load("fr/fr-ste-lint.py", "fr_ste_lint")
en = load("en/ste-lint.py", "ste_lint")
ru = load("ru/ru-ste-lint.py", "ru_ste_lint")
es = load("es/es-ste-lint.py", "es_ste_lint")

SLOP = {
    "de": "Dieses System ist grundsätzlich sehr wichtig, revolutionär und nahtlos robust.\n",
    "fr": "Ce système est basiquement révolutionnaire et robuste, très important.\n",
}
CLEAN = {
    "de": "Der Server startet den Dienst nach einem Neustart.\n",
    "fr": "Le serveur démarre le service après un redémarrage.\n",
}

SLOP_ES = "Esta solución innovadora y revolucionaria es muy robusta.\n"
CLEAN_ES = "El servidor inicia el servicio después del reinicio.\n"


def call(mod, argv):
    """Run main() like a CLI call. Returns (exit code, stdout, stderr)."""
    buf, err = io.StringIO(), io.StringIO()
    code = 0
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        try:
            mod.main(argv)
        except SystemExit as exc:
            code = exc.code
    return code, buf.getvalue(), err.getvalue()


def call_return(mod, argv):
    """Run main() like a CLI call, taking the exit code from its return."""
    buf, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        code = mod.main(argv)
    return code, buf.getvalue(), err.getvalue()


class MaxGateDeFr(unittest.TestCase):
    """--max must gate de/fr runs the way it gates en/ru runs."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        path = pathlib.Path(self.tmp.name) / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_slop_fails_at_max_zero(self):
        for mod, lang in ((de, "de"), (fr, "fr")):
            path = self.write("slop.md", SLOP[lang])
            code, _, _ = call(mod, ["--max", "0", path])
            self.assertEqual(code, 1, lang)

    def test_slop_passes_above_its_score(self):
        for mod, lang in ((de, "de"), (fr, "fr")):
            path = self.write("slop.md", SLOP[lang])
            code, _, _ = call(mod, ["--max", "100", path])
            self.assertEqual(code, 0, lang)

    def test_max_equals_syntax(self):
        for mod, lang in ((de, "de"), (fr, "fr")):
            path = self.write("slop.md", SLOP[lang])
            code, _, _ = call(mod, ["--max=0", path])
            self.assertEqual(code, 1, lang)

    def test_missing_value_is_usage_error(self):
        for mod, lang in ((de, "de"), (fr, "fr")):
            code, _, err = call(mod, ["--max"])
            self.assertEqual(code, 2, lang)
            self.assertIn("--max", err)

    def test_clean_text_passes_at_max_zero(self):
        for mod, lang in ((de, "de"), (fr, "fr")):
            path = self.write("clean.md", CLEAN[lang])
            code, _, _ = call(mod, ["--max", "0", path])
            self.assertEqual(code, 0, lang)

    def test_value_is_not_treated_as_file(self):
        # Regression: the value after --max used to be globbed as a path.
        for mod, lang in ((de, "de"), (fr, "fr")):
            path = self.write("slop.md", SLOP[lang])
            code, out, _ = call(mod, ["--max", "0", path])
            self.assertIn("slop.md", out, lang)
            self.assertEqual(code, 1, lang)


class MaxGateEnRu(unittest.TestCase):
    """en/ru must reject a non-numeric --max value instead of crashing (#246)."""

    def test_nonnumeric_value_is_usage_error(self):
        for mod, lang in ((en, "en"), (ru, "ru")):
            code, _, err = call_return(mod, ["--max", "abc", "x.md"])
            self.assertEqual(code, 2, lang)
            self.assertIn("--max", err, lang)

    def test_nonnumeric_equals_syntax_is_usage_error(self):
        for mod, lang in ((en, "en"), (ru, "ru")):
            code, _, err = call_return(mod, ["--max=abc", "x.md"])
            self.assertEqual(code, 2, lang)
            self.assertIn("--max", err, lang)

    def test_missing_value_is_usage_error(self):
        for mod, lang in ((en, "en"), (ru, "ru")):
            code, _, err = call_return(mod, ["--max"])
            self.assertEqual(code, 2, lang)
            self.assertIn("--max", err, lang)


class MaxGateEs(unittest.TestCase):
    """es gets the same --max gate as the other four linters (#250)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        path = pathlib.Path(self.tmp.name) / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_slop_fails_at_max_zero(self):
        path = self.write("slop.md", SLOP_ES)
        code, _, _ = call_return(es, ["--max", "0", path])
        self.assertEqual(code, 1)

    def test_slop_passes_above_its_score(self):
        path = self.write("slop.md", SLOP_ES)
        code, _, _ = call_return(es, ["--max", "100", path])
        self.assertEqual(code, 0)

    def test_max_equals_syntax(self):
        path = self.write("slop.md", SLOP_ES)
        code, _, _ = call_return(es, ["--max=0", path])
        self.assertEqual(code, 1)

    def test_clean_text_passes_at_max_zero(self):
        path = self.write("clean.md", CLEAN_ES)
        code, _, _ = call_return(es, ["--max", "0", path])
        self.assertEqual(code, 0)

    def test_missing_value_is_usage_error(self):
        code, _, err = call_return(es, ["--max"])
        self.assertEqual(code, 2)
        self.assertIn("--max", err)

    def test_nonnumeric_value_is_usage_error(self):
        code, _, err = call_return(es, ["--max", "abc", "x.md"])
        self.assertEqual(code, 2)
        self.assertIn("--max", err)

    def test_unreadable_file_is_error_not_traceback(self):
        missing = str(pathlib.Path(self.tmp.name) / "missing.md")
        code, _, err = call_return(es, [missing])
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)


if __name__ == "__main__":
    unittest.main()
