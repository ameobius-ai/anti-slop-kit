"""Tests for the Hermes-facing wrapper tools in tools/aslint/.

The wrappers call the linters as subprocesses, so every test here also
exercises the linter it wraps. The suite asserts no fixed score: scores
move when rules move, and rule 8 of AGENTS.md forbids pinning them in
prose. Structure, verdicts, and fidelity behaviour are the contract.
"""

import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.aslint import common, lint_tool, rewrite_tool, transmit_check  # noqa: E402

SLOP_WITH_NUMBER = (
    "It should be noted that the service must be restarted after "
    "2.5 seconds in order to facilitate the cache refresh. The "
    "restart_window_ms setting controls the delay, and the docs at "
    "https://example.com/cache describe it."
)
CLEAN_KEEPS_BITS = (
    "Restart the service after 2.5 seconds to refresh the cache. "
    "The restart_window_ms setting controls the delay. "
    "The docs at https://example.com/cache describe it."
)
CLEAN_DROPS_NUMBER = (
    "Restart the service to refresh the cache. "
    "The restart_window_ms setting controls the delay. "
    "The docs at https://example.com/cache describe it."
)


def run_tool(*args, stdin=None):
    cmd = [sys.executable] + [str(a) for a in args]
    return subprocess.run(cmd, input=stdin, capture_output=True,
                          text=True, cwd=str(ROOT))


class TestLintTool(unittest.TestCase):
    def test_clean_sample_scores_low(self):
        out = lint_tool.lint_file(ROOT / "en" / "samples" / "ste.md")
        self.assertTrue(out["ok"])
        self.assertEqual(out["lang"], "en")
        self.assertLessEqual(out["result"]["total_per100w"], 2)
        self.assertIsInstance(out["result"]["findings"], list)

    def test_baseline_scores_above_clean_sample(self):
        clean = lint_tool.lint_file(ROOT / "en" / "samples" / "ste.md")
        slop = lint_tool.lint_file(ROOT / "en" / "samples" / "baseline.md")
        self.assertGreater(slop["result"]["total_per100w"],
                           clean["result"]["total_per100w"])

    def test_language_autodetect(self):
        _, ru = common.lint_text("Сервис перезапускается после обновления.")
        _, en = common.lint_text("Restart the service after the update.")
        self.assertIsInstance(ru["total"], int)
        self.assertIsInstance(en["total"], int)
        self.assertEqual(common.detect_lang("Текст по-русски"), "ru")
        self.assertEqual(common.detect_lang("English text"), "en")

    def test_determinism(self):
        first = lint_tool.lint_text_tool(SLOP_WITH_NUMBER)
        second = lint_tool.lint_text_tool(SLOP_WITH_NUMBER)
        self.assertEqual(first, second)

    def test_cli_stdout_is_exactly_one_json_object(self):
        proc = run_tool(ROOT / "tools" / "aslint" / "lint_tool.py",
                        ROOT / "en" / "samples" / "ste.md")
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["results"]), 1)

    def test_cli_stdin(self):
        proc = run_tool(ROOT / "tools" / "aslint" / "lint_tool.py",
                        "--stdin", stdin=SLOP_WITH_NUMBER)
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["results"][0]["path"], "<text>")

    def test_cli_bad_option_exits_2(self):
        proc = run_tool(ROOT / "tools" / "aslint" / "lint_tool.py",
                        "--nope")
        self.assertEqual(proc.returncode, 2)
        self.assertFalse(json.loads(proc.stdout)["ok"])

    def test_cli_missing_file_exits_2(self):
        proc = run_tool(ROOT / "tools" / "aslint" / "lint_tool.py",
                        ROOT / "no-such-file.md")
        self.assertEqual(proc.returncode, 2)
        self.assertFalse(json.loads(proc.stdout)["ok"])


class TestValidateRewrite(unittest.TestCase):
    def test_accepts_clean_rewrite_that_keeps_bits(self):
        out = rewrite_tool.validate_rewrite(SLOP_WITH_NUMBER,
                                            CLEAN_KEEPS_BITS)
        self.assertEqual(out["verdict"], "accept")
        self.assertLessEqual(out["score"]["delta_per100w"], 0)
        self.assertEqual(out["fidelity"]["numbers"], [])
        self.assertEqual(out["fidelity"]["identifiers"], [])
        self.assertEqual(out["fidelity"]["urls"], [])

    def test_rejects_rewrite_that_drops_a_number(self):
        out = rewrite_tool.validate_rewrite(SLOP_WITH_NUMBER,
                                            CLEAN_DROPS_NUMBER)
        self.assertEqual(out["verdict"], "reject")
        self.assertIn("2.5", out["fidelity"]["numbers"])
        self.assertTrue(out["reasons"])

    def test_cli_exit_codes(self):
        tool = ROOT / "tools" / "aslint" / "rewrite_tool.py"
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            orig = pathlib.Path(tmp, "orig.md")
            good = pathlib.Path(tmp, "good.md")
            orig.write_text(SLOP_WITH_NUMBER, encoding="utf-8")
            good.write_text(CLEAN_KEEPS_BITS, encoding="utf-8")
            ok = run_tool(tool, orig, good)
            self.assertEqual(ok.returncode, 0)
            self.assertEqual(json.loads(ok.stdout)["verdict"], "accept")
        bad = run_tool(tool)
        self.assertEqual(bad.returncode, 2)


class TestTransmitCheck(unittest.TestCase):
    def test_identical_text_passes(self):
        out = transmit_check.transmit_check(SLOP_WITH_NUMBER,
                                            SLOP_WITH_NUMBER)
        self.assertTrue(out["passed"])
        self.assertTrue(all(out["checks"].values()))

    def test_lost_number_and_identifier_are_reported(self):
        mangled = "Restart the service to refresh the cache."
        out = transmit_check.transmit_check(SLOP_WITH_NUMBER, mangled)
        self.assertFalse(out["passed"])
        self.assertIn("2.5", out["missing"]["numbers"])
        self.assertIn("restart_window_ms", out["missing"]["identifiers"])
        self.assertIn("https://example.com/cache", out["missing"]["urls"])

    def test_constraints_and_ordering(self):
        source = "step alpha, then beta, then gamma"
        intact = "first alpha, next beta, finally gamma"
        out = transmit_check.transmit_check(
            source, intact, constraints=["then beta"],
            ordered=["alpha", "gamma"])
        self.assertFalse(out["checks"]["constraints"])
        self.assertTrue(out["checks"]["ordering"])
        reordered = "gamma first, alpha second, beta third"
        out2 = transmit_check.transmit_check(
            source, reordered, ordered=["alpha", "gamma"])
        self.assertFalse(out2["checks"]["ordering"])

    def test_cli_flags(self):
        tool = ROOT / "tools" / "aslint" / "transmit_check.py"
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            src = pathlib.Path(tmp, "src.md")
            dst = pathlib.Path(tmp, "dst.md")
            src.write_text("port 8443 stays open", encoding="utf-8")
            dst.write_text("open port 8443", encoding="utf-8")
            ok = run_tool(tool, src, dst, "--require", "port 8443")
            self.assertEqual(ok.returncode, 0)
            bad = run_tool(tool, src, dst, "--require", "port 9999")
            self.assertEqual(bad.returncode, 1)
            self.assertIn("port 9999",
                          json.loads(bad.stdout)["missing"]["constraints"])


class TestRegistry(unittest.TestCase):
    def test_registry_lists_the_four_tools(self):
        reg = json.loads(
            (ROOT / "tools" / "hermes_registry.json").read_text())
        names = {t["name"] for t in reg["tools"]}
        self.assertEqual(names, {"lint_file", "lint_text",
                                 "validate_rewrite", "transmit_check"})
        self.assertTrue(reg["contract"]["properties"]["deterministic"])
        self.assertFalse(
            reg["contract"]["properties"]["generates_rewrites"])


if __name__ == "__main__":
    unittest.main()
