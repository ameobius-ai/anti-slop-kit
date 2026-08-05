import importlib.util
import pathlib
import re
import unittest

# Linter filenames are hyphenated, so load by path (same pattern as
# tests/test_linters.py).
ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ste_lint = load("en/ste-lint.py", "ste_lint")

TECHNICAL_STEMS = ste_lint.TECHNICAL_STEMS
PARTICIPLE_RE = ste_lint.PARTICIPLE_RE
_fold = ste_lint._fold
_tech = ste_lint._tech
_morph_count = ste_lint._morph_count
_ing_progressive_count = ste_lint._ing_progressive_count
_participle_count = ste_lint._participle_count


class TestTechnicalRegister(unittest.TestCase):

    def test_technical_stems_not_empty(self):
        self.assertGreater(len(TECHNICAL_STEMS), 0)

    def test_fold_lowercase(self):
        self.assertEqual(_fold("Hello"), "hello")
        self.assertEqual(_fold("WORLD"), "world")
        self.assertEqual(_fold("MixedCase"), "mixedcase")

    def test_tech_recognizes_technical_terms(self):
        # Should recognize technical stems
        self.assertTrue(_tech("caching"))
        self.assertTrue(_tech("configuration"))
        self.assertTrue(_tech("initialization"))
        self.assertTrue(_tech("deprecated"))
        self.assertTrue(_tech("documented"))

    def test_tech_rejects_non_technical(self):
        # Should not recognize non-technical words
        self.assertFalse(_tech("beautiful"))
        self.assertFalse(_tech("wonderful"))
        self.assertFalse(_tech("amazing"))
        self.assertFalse(_tech("synergy"))

    def test_morph_count_basic(self):
        # Simple regex that matches any word ending in -ing
        test_re = re.compile(r'\b\w+ing\b', re.I)
        text = "caching processing running falling"

        # caching and processing are technical, running and falling are not
        count = _morph_count(test_re, text)
        self.assertEqual(count, 2)  # running, falling

    def test_morph_count_with_stop(self):
        test_re = re.compile(r'\b\w+ing\b', re.I)
        text = "starting stopping caching"

        # Stop prefix "start" skips "starting"; "caching" is technical
        count = _morph_count(test_re, text, stop="start")
        self.assertEqual(count, 1)  # stopping

    def test_ing_progressive_count_basic(self):
        text = "The function is processing the data"
        count = _ing_progressive_count(text)
        # "processing" is technical, so should not count
        self.assertEqual(count, 0)

    def test_ing_progressive_count_non_technical(self):
        text = "The system is working well"
        count = _ing_progressive_count(text)
        # "working" is not in technical stems
        self.assertEqual(count, 1)

    def test_ing_progressive_count_multiple(self):
        text = "The service is running and the cache is caching data"
        count = _ing_progressive_count(text)
        # "running" is not technical, "caching" is technical
        self.assertEqual(count, 1)


class TestParticipleHandling(unittest.TestCase):

    def test_participle_re_matches(self):
        text = "processing cached used being"
        matches = PARTICIPLE_RE.findall(text)
        self.assertIn("processing", matches)
        self.assertIn("cached", matches)
        self.assertIn("used", matches)
        self.assertIn("being", matches)

    def test_participle_stop_excludes_lexicalized(self):
        # "being" and "used" are in PARTICIPLE_STOP
        text = "The system is being used for testing"
        count = _participle_count(text)
        # "being" and "used" are stopped, "testing" is technical
        self.assertEqual(count, 0)

    def test_participle_count_detects_violations(self):
        # "working" is not technical or stopped
        text = "The function is working correctly"
        count = _participle_count(text)
        self.assertEqual(count, 1)  # "working"

    def test_participle_excludes_technical(self):
        # "caching", "processing", "configured" are technical
        text = "The caching and processing is configured"
        count = _participle_count(text)
        self.assertEqual(count, 0)


if __name__ == '__main__':
    unittest.main()
