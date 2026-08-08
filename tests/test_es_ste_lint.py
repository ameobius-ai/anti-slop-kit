#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Spanish linter (es-ste-lint.py).

Written in unittest form so scripts/check.sh collects it; covers the
technical-register allowlist from issue #253 at rule level.
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


# The file name carries a dash, so a plain import cannot reach it.
es_ste_lint = load("es/es-ste-lint.py", "es_ste_lint")


class WithTmpDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = pathlib.Path(self._tmp.name)

    def write(self, name, text):
        path = self.tmp_path / name
        path.write_text(text, encoding="utf-8")
        return str(path)


class TestEsLintBasic(WithTmpDir):
    """Basic functionality of the Spanish linter."""

    def test_lint_returns_expected_structure(self):
        result = es_ste_lint.lint("El servidor reinicia el servicio.")
        for key in ("words", "violations", "total", "total_per100w",
                    "longest_sentence"):
            self.assertIn(key, result)

    def test_clean_spanish_text_scores_zero(self):
        result = es_ste_lint.lint("El servidor inicia el servicio tras el reinicio.\n")
        self.assertEqual(result["total"], 0)

    def test_empty_text_scores_zero(self):
        result = es_ste_lint.lint("")
        self.assertEqual(result["total"], 0)


class TestEsPatterns(unittest.TestCase):
    """Each slop category fires on its pattern."""

    def test_clerical(self):
        r = es_ste_lint.lint("A efectos de la revisión, abra el archivo.")
        self.assertGreaterEqual(r["violations"]["clerical_phrase"], 1)

    def test_marketing(self):
        r = es_ste_lint.lint("Esta solución innovadora y revolucionaria es robusta.")
        self.assertGreaterEqual(r["violations"]["marketing_language"], 2)

    def test_ai_slop(self):
        r = es_ste_lint.lint("En el mundo de hoy, el caché importa.")
        self.assertGreaterEqual(r["violations"]["ai_slop"], 1)

    def test_hedge(self):
        r = es_ste_lint.lint("Básicamente el servidor funciona.")
        self.assertGreaterEqual(r["violations"]["hedge_word"], 1)


class TestTechnicalRegister(unittest.TestCase):
    """The nominalization rule must not fire on standard doc vocabulary (#253).

    Mirrors the ru allowlist from issue #33: nouns like configuración or
    instalación are correct in documentation, not slop.
    """

    def test_technical_cion_words_do_not_fire(self):
        text = ("La configuración del sistema. La instalación del paquete. "
                "Inicia sesión. Verifica la conexión. La documentación del "
                "sistema de gestión. El funcionamiento es estable.\n")
        self.assertEqual(es_ste_lint.lint(text)["violations"]["nominalization"], 0)

    def test_real_nominalizations_still_fire(self):
        text = "La utilización de la realización del proceso.\n"
        self.assertGreaterEqual(
            es_ste_lint.lint(text)["violations"]["nominalization"], 2)

    def test_the_clean_sample_carries_no_nominalization(self):
        text = (ROOT / "es/samples/skill.md").read_text(encoding="utf-8")
        self.assertEqual(es_ste_lint.lint(text)["violations"]["nominalization"], 0)

    def test_the_clean_sample_passes_the_gate(self):
        text = (ROOT / "es/samples/skill.md").read_text(encoding="utf-8")
        self.assertLessEqual(es_ste_lint.lint(text)["total_per100w"], 2)


if __name__ == "__main__":
    unittest.main()
