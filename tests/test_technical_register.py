import unittest
import sys
sys.path.insert(0, '../en')

from ste_lint import TECHNICAL_STEMS, _fold, _tech, _morph_count, _ing_main_count


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
        import re
        # Simple regex that matches any word ending in -ing
        test_re = re.compile(r'\b\w+ing\b', re.I)
        text = "caching processing beautiful amazing"
        
        # caching and processing are technical, beautiful and amazing are not
        # But only -ing words count, so beautiful/amazing don't match the regex
        count = _morph_count(test_re, text)
        # All 4 match the regex, but 2 are technical
        self.assertEqual(count, 2)  # beautiful, amazing
    
    def test_morph_count_with_stop(self):
        import re
        test_re = re.compile(r'\b\w+ing\b', re.I)
        text = "starting stopping caching"
        
        # Stop at "start" - should skip "starting"
        count = _morph_count(test_re, text, stop="start")
        # starting is stopped, stopping and caching: stopping is not technical, caching is
        self.assertEqual(count, 1)  # stopping
    
    def test_ing_main_count_basic(self):
        text = "The function is processing the data"
        count = _ing_main_count(text)
        # "processing" is technical, so should not count
        self.assertEqual(count, 0)
    
    def test_ing_main_count_non_technical(self):
        text = "The system is working well"
        count = _ing_main_count(text)
        # "working" is not in technical stems
        self.assertEqual(count, 1)
    
    def test_ing_main_count_multiple(self):
        text = "The service is running and the cache is caching data"
        count = _ing_main_count(text)
        # "running" is not technical, "caching" is technical
        self.assertEqual(count, 1)


if __name__ == '__main__':
    unittest.main()


class TestParticipleHandling(unittest.TestCase):
    
    def test_participle_re_matches(self):
        import re
        # Test that PARTICIPLE_RE matches -ing and -ed forms
        text = "processing cached used being"
        matches = PARTICIPLE_RE.findall(text)
        self.assertIn("processing", matches)
        self.assertIn("cached", matches)
        self.assertIn("used", matches)
        self.assertIn("being", matches)
    
    def test_participle_stop_excludes_lexicalized(self):
        from ste_lint import _participle_count
        # "being" and "used" are in PARTICIPLE_STOP
        text = "The system is being used for testing"
        count = _participle_count(text)
        # "being" and "used" are stopped, "testing" is technical
        self.assertEqual(count, 0)
    
    def test_participle_count_detects_violations(self):
        from ste_lint import _participle_count
        # "working" is not technical or stopped
        text = "The function is working correctly"
        count = _participle_count(text)
        self.assertEqual(count, 1)  # "working"
    
    def test_participle_excludes_technical(self):
        from ste_lint import _participle_count
        # "caching", "processing", "configured" are technical
        text = "The caching and processing is configured"
        count = _participle_count(text)
        self.assertEqual(count, 0)
