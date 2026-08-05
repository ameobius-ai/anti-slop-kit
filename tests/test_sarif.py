import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


en = load("en/ste-lint.py", "ste_lint")
format_sarif = en.format_sarif
lint = en.lint


class TestSARIFOutput(unittest.TestCase):
    """Test SARIF 2.1.0 output format."""

    def setUp(self):
        self.sample_text = '''# Test Document

This document utilizes seamless solutions to facilitate robust outcomes.
We leverage cutting-edge technologies to empower users and harness innovation.

The vast majority of stakeholders have noted that it is important
to delve into the myriad possibilities that exist in today's
fast-paced world.
'''
        self.filename = "test.md"

    def test_sarif_is_valid_json(self):
        """SARIF output must be valid JSON."""
        r = lint(self.sample_text)
        sarif = format_sarif(self.filename, r, self.sample_text, None)

        # Should be a dict
        self.assertIsInstance(sarif, dict)

        # Should be serializable to JSON
        json_str = json.dumps(sarif, ensure_ascii=False)
        self.assertIsInstance(json_str, str)

        # Should be parseable back
        parsed = json.loads(json_str)
        self.assertEqual(parsed, sarif)

    def test_sarif_has_required_fields(self):
        """SARIF must have version, schema, and runs."""
        r = lint(self.sample_text)
        sarif = format_sarif(self.filename, r, self.sample_text, None)

        # Required top-level fields
        self.assertIn("version", sarif)
        self.assertIn("$schema", sarif)
        self.assertIn("runs", sarif)

        # Version must be 2.1.0
        self.assertEqual(sarif["version"], "2.1.0")

        # Schema must be SARIF 2.1.0
        self.assertIn("sarif-schema-2.1.0", sarif["$schema"])

        # Must have at least one run
        self.assertGreaterEqual(len(sarif["runs"]), 1)

    def test_sarif_has_tool_driver(self):
        """SARIF must have tool driver with rules."""
        r = lint(self.sample_text)
        sarif = format_sarif(self.filename, r, self.sample_text, None)

        run = sarif["runs"][0]

        # Must have tool
        self.assertIn("tool", run)

        # Must have driver
        self.assertIn("driver", run["tool"])

        driver = run["tool"]["driver"]

        # Driver must have name, version, rules
        self.assertIn("name", driver)
        self.assertIn("version", driver)
        self.assertIn("rules", driver)

        # Name must be anti-slop-kit
        self.assertEqual(driver["name"], "anti-slop-kit")

        # Must have at least one rule
        self.assertGreaterEqual(len(driver["rules"]), 1)

    def test_sarif_rules_have_required_fields(self):
        """Each rule must have id, name, and shortDescription."""
        r = lint(self.sample_text)
        sarif = format_sarif(self.filename, r, self.sample_text, None)

        rules = sarif["runs"][0]["tool"]["driver"]["rules"]

        for rule in rules:
            self.assertIn("id", rule)
            self.assertIn("name", rule)
            self.assertIn("shortDescription", rule)
            self.assertIn("text", rule["shortDescription"])
            self.assertIn("helpUri", rule)

    def test_sarif_results_have_required_fields(self):
        """Each result must have ruleId, level, message, and locations."""
        r = lint(self.sample_text)
        sarif = format_sarif(self.filename, r, self.sample_text, None)

        results = sarif["runs"][0]["results"]

        # Should have at least one result (sample text has violations)
        self.assertGreater(len(results), 0)

        for result in results:
            self.assertIn("ruleId", result)
            self.assertIn("ruleIndex", result)
            self.assertIn("level", result)
            self.assertIn("message", result)
            self.assertIn("locations", result)

            # Level must be warning
            self.assertEqual(result["level"], "warning")

            # Message must have text
            self.assertIn("text", result["message"])

            # Locations must have physicalLocation
            self.assertGreater(len(result["locations"]), 0)
            loc = result["locations"][0]
            self.assertIn("physicalLocation", loc)

            phys = loc["physicalLocation"]
            self.assertIn("artifactLocation", phys)
            self.assertIn("region", phys)

            # Region must have startLine
            self.assertIn("startLine", phys["region"])
            self.assertGreater(phys["region"]["startLine"], 0)

    def test_sarif_respects_only_flag(self):
        """SARIF must respect --only flag for filtering."""
        r = lint(self.sample_text)

        # Test with only="slop"
        sarif_slop = format_sarif(self.filename, r, self.sample_text, "slop")
        results_slop = sarif_slop["runs"][0]["results"]

        # All results should be slop categories
        slop_rules = ["banned_word", "marketing_adjective", "ai_slop", "modal_hedge"]
        for result in results_slop:
            self.assertIn(result["ruleId"], slop_rules)

    def test_sarif_empty_for_clean_text(self):
        """SARIF should have empty results for clean text."""
        clean_text = "# Notes\n\nThe proxy restarts after a config change.\n"

        r = lint(clean_text)
        sarif = format_sarif("clean.md", r, clean_text, None)

        # Should have no results
        results = sarif["runs"][0]["results"]
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()
