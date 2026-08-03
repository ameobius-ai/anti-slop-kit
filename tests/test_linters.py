#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for both linters. Standard library only: python3 -m unittest discover -s tests"""
import importlib.util
import io
import contextlib
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


en = load("en/ste-lint.py", "ste_lint")
ru = load("ru/ru-ste-lint.py", "ru_ste_lint")


class EnglishRules(unittest.TestCase):
    def test_banned_word(self):
        self.assertGreaterEqual(
            en.lint("You can utilize the tool.")["violations"]["banned_word"], 1)

    def test_marketing_adjective(self):
        r = en.lint("We built a seamless and world-class pipeline.")
        self.assertGreaterEqual(r["violations"]["marketing_adjective"], 2)

    def test_ai_slop_opener(self):
        r = en.lint("In today's fast-paced world, caching helps.")
        self.assertGreaterEqual(r["violations"]["ai_slop"], 1)

    def test_semicolon_and_contraction(self):
        r = en.lint("The job runs; it don't stop.")
        self.assertEqual(r["violations"]["semicolon"], 1)
        self.assertGreaterEqual(r["violations"]["contraction"], 1)

    def test_long_sentence(self):
        long_one = " ".join(["word"] * 30) + "."
        self.assertEqual(en.lint(long_one)["violations"]["long_sentence(>20w)"], 1)

    def test_short_sentence_is_clean(self):
        r = en.lint("The parser reads the file. It writes a report.")
        self.assertEqual(r["violations"]["long_sentence(>20w)"], 0)
        self.assertEqual(r["violations"]["banned_word"], 0)

    def test_passive_voice(self):
        r = en.lint("The file is read by the parser.")
        self.assertGreaterEqual(r["violations"]["passive_voice"], 1)

    def test_active_voice_is_not_passive(self):
        r = en.lint("The parser reads the file and writes a report.")
        self.assertEqual(r["violations"]["passive_voice"], 0)

    def test_ing_opener_stoplist(self):
        """Issue #13: sentence-initial -ing words that are not participles."""
        for text in ("Bring the file to the node.",
                     "During the meeting, write notes.",
                     "Something went wrong. Check the log."):
            self.assertEqual(en.lint(text)["violations"]["ing_main_verb"], 0)

    def test_ing_opener_true_positive(self):
        r = en.lint("Using the cache, write the key.")
        self.assertGreaterEqual(r["violations"]["ing_main_verb"], 1)

    def test_ing_stoplist_keeps_diagnostics_in_sync(self):
        text = "Bring the file. Something went wrong. Using the cache, write it."
        total = en.lint(text)["violations"]["ing_main_verb"]
        diags = [d for d in en.diagnostics(text) if d[1] == "ing_main_verb"]
        self.assertEqual(total, 1)  # only "Using" survives the stoplist
        self.assertEqual(len(diags), total)


class EnglishMarkupIsNotProse(unittest.TestCase):
    def test_code_fence_ignored(self):
        text = "Run it.\n\n```python\nutilize = 'seamless robust'\n```\n"
        r = en.lint(text)
        self.assertEqual(r["violations"]["banned_word"], 0)
        self.assertEqual(r["violations"]["marketing_adjective"], 0)

    def test_inline_code_ignored(self):
        self.assertEqual(
            en.lint("Call `utilize()` here.")["violations"]["banned_word"], 0)

    def test_frontmatter_ignored(self):
        text = "---\nname: demo\ndescription: utilize a seamless robust thing\n---\n\nOpen the file.\n"
        r = en.lint(text)
        self.assertEqual(r["violations"]["banned_word"], 0)
        self.assertEqual(r["violations"]["marketing_adjective"], 0)

    def test_link_target_ignored_label_kept(self):
        r = en.lint("See the [docs](https://example.com/utilize-seamless-guide).")
        self.assertEqual(r["violations"]["banned_word"], 0)
        self.assertEqual(r["violations"]["marketing_adjective"], 0)
        self.assertGreater(r["words"], 2)

    def test_bare_url_ignored(self):
        r = en.lint("Read https://example.com/robust-and-powerful for details.")
        self.assertEqual(r["violations"]["marketing_adjective"], 0)

    def test_ignore_region(self):
        text = ("Open the file.\n\n<!-- anti-slop: off -->\n"
                "utilize a seamless robust world-class solution\n"
                "<!-- anti-slop: on -->\n")
        r = en.lint(text)
        self.assertEqual(r["violations"]["banned_word"], 0)
        self.assertEqual(r["violations"]["marketing_adjective"], 0)


class EnglishSpansAreChargedOnce(unittest.TestCase):
    """One span, one violation, even when a short entry sits inside a long one.

    The lists do not carry a nested pair yet. These tests pin the mechanism
    now, so adding 'delve' next to 'delve into' cannot start double-counting.
    """

    def test_longest_phrase_wins(self):
        hits = en.phrase_matches("Let us delve into the data.",
                                 ["delve", "delve into"])
        self.assertEqual([ph for ph, _ in hits], ["delve into"])

    def test_each_occurrence_still_counts(self):
        n, hits = en.count_phrases("Delve into logs and delve into traces.",
                                   ["delve", "delve into"])
        self.assertEqual((n, hits), (2, ["delve into", "delve into"]))

    def test_word_boundaries_still_hold(self):
        for text in ("The delved report.", "An undelve step."):
            self.assertEqual(en.count_phrases(text, ["delve"])[0], 0, text)

    def test_hits_come_back_in_reading_order(self):
        n, hits = en.count_phrases("Alpha then zebra.", ["zebra", "alpha"])
        self.assertEqual((n, hits), (2, ["alpha", "zebra"]))

    def test_a_long_phrase_keeps_its_own_suggestion(self):
        out = []
        en._phrase_hits("We utilize a comprehensive solution.",
                        ["utilize", "comprehensive solution"], 1,
                        "banned_word", out)
        self.assertEqual([m for _, _, m, _ in out],
                         ["utilize", "comprehensive solution"])

    def test_real_lists_do_not_double_charge_the_samples(self):
        for rel in ("en/samples/baseline.md", "en/samples/ste.md"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            for name in ("BANNED", "MARKETING", "AI_SLOP", "HEDGE"):
                spans = [sp for _, sp in
                         en.phrase_matches(text, getattr(en, name))]
                self.assertEqual(len(spans), len(set(spans)),
                                 "%s repeats a span in %s" % (name, rel))


class RussianRules(unittest.TestCase):
    def test_clerical(self):
        r = ru.lint("В целях проверки откройте файл.")
        self.assertGreaterEqual(r["violations"]["clerical"], 1)

    def test_yo_folding(self):
        """путём и путем — одно и то же для линтера."""
        a = ru.lint("Настройка путём замены.")["violations"]["clerical"]
        b = ru.lint("Настройка путем замены.")["violations"]["clerical"]
        self.assertEqual(a, b)
        self.assertGreaterEqual(a, 1)

    def test_participle(self):
        r = ru.lint("Сервис, позволяющий читать файлы.")
        self.assertGreaterEqual(r["violations"]["participle"], 1)

    def test_nominalization(self):
        r = ru.lint("Обеспечение снижения нагрузки.")
        self.assertGreaterEqual(r["violations"]["nominalization"], 2)

    def test_passive_reflexive(self):
        r = ru.lint("Обращение к модели выполняется сервером.")
        self.assertGreaterEqual(r["violations"]["passive_reflexive"], 1)

    def test_marketing(self):
        r = ru.lint("Это инновационный и мощный инструмент.")
        self.assertGreaterEqual(r["violations"]["marketing"], 2)

    def test_ai_slop(self):
        r = ru.lint("В современном мире кэш важен.")
        self.assertGreaterEqual(r["violations"]["ai_slop"], 1)

    def test_clean_text_scores_zero(self):
        r = ru.lint("Откройте конфиг. Измените три поля. Сохраните файл.")
        self.assertEqual(r["total"], 0)

    def test_straight_quotes_flagged(self):
        r = ru.lint('Откройте файл "кэш".')
        self.assertEqual(r["typography"]["straight_quotes"], 2)

    def test_code_fence_ignored(self):
        text = "Откройте файл.\n\n```python\n# в целях осуществления\nx = 1\n```\n"
        self.assertEqual(ru.lint(text)["violations"]["clerical"], 0)

    def test_frontmatter_ignored(self):
        text = "---\nname: demo\ndescription: в целях осуществления инновационного\n---\n\nОткройте файл.\n"
        r = ru.lint(text)
        self.assertEqual(r["violations"]["clerical"], 0)
        self.assertEqual(r["violations"]["marketing"], 0)

    def test_participle_stoplist(self):
        """Issue #14: lexicalized -щий adjectives are not participles."""
        for text in ("Откройте следующий файл.",
                     "См. соответствующий раздел.",
                     "Установите подходящий драйвер.",
                     "Обновите существующий узел."):
            self.assertEqual(ru.lint(text)["violations"]["participle"], 0)

    def test_participle_stoplist_keeps_diagnostics_in_sync(self):
        text = "Откройте следующий файл. Сервис, позволяющий читать файлы."
        total = ru.lint(text)["violations"]["participle"]
        diags = [d for d in ru.diagnostics(text) if d[1] == "participle"]
        self.assertEqual(total, 1)  # only «позволяющий» survives
        self.assertEqual(len(diags), total)


class RussianSpansAreChargedOnce(unittest.TestCase):
    """Issue #18: one span on the page is one violation in the report."""

    def test_yo_pair_counts_once(self):
        """«путем» и «путём» лежали в списке оба, но это одно слово."""
        for text in ("Данные передаются путём шифрования.",
                     "Данные передаются путем шифрования."):
            self.assertEqual(ru.lint(text)["violations"]["clerical"], 1)

    def test_marketing_yo_pair_counts_once(self):
        self.assertEqual(
            ru.lint("Это надёжное решение.")["violations"]["marketing"], 1)

    def test_nested_phrase_counts_once(self):
        """«данный» внутри «в данный момент» — один штамп, не два."""
        self.assertEqual(
            ru.lint("В данный момент сервис недоступен.")[
                "violations"]["clerical"], 1)

    def test_nested_ai_slop_counts_once(self):
        self.assertEqual(
            ru.lint("Давайте погрузимся в тему.")["violations"]["ai_slop"], 1)

    def test_longer_phrase_wins_the_span(self):
        """Побеждать должна длинная фраза: у неё точнее подсказка."""
        hits = [ph for ph, _ in ru.phrase_matches(
            "В данный момент сервис недоступен.", ru.CLERICAL)]
        self.assertEqual(hits, ["в данный момент"])

    def test_separate_spans_still_both_count(self):
        """Фикс гасит двойной счёт, а не второе вхождение."""
        r = ru.lint("В данный момент так. Настройка путём замены.")
        self.assertEqual(r["violations"]["clerical"], 2)

    def test_diagnostics_agree_with_the_count(self):
        text = "В данный момент данные передаются путём шифрования."
        total = ru.lint(text)["violations"]["clerical"]
        diags = [d for d in ru.diagnostics(text) if d[1] == "clerical"]
        self.assertEqual(len(diags), total)


class SpansAreChargedOnceAcrossLists(unittest.TestCase):
    """One span belongs to one list, even when two lists could claim it.

    phrase_matches() guards a single list at a time. These tests pin the
    wider invariant (issue #21), so #11 can put 'delve' in BANNED while
    'delve into' stays in AI_SLOP without charging the reader twice.
    The pairs below are injected rather than real: no phrase in the
    shipped lists is nested inside a phrase from another list today.
    """

    def _with_extra(self, mod, category, phrase):
        return tuple((c, (list(ph) + [phrase]) if c == category else ph)
                     for c, ph in mod.PHRASE_GROUPS)

    def test_en_long_phrase_wins_over_a_short_one_from_another_list(self):
        groups = self._with_extra(en, "banned_word", "delve")
        hits = en.categorised_matches("We delve into the logs.", groups)
        self.assertEqual([(c, p) for c, p, _ in hits],
                         [("ai_slop", "delve into")])

    def test_en_short_word_still_fires_on_its_own(self):
        groups = self._with_extra(en, "banned_word", "delve")
        hits = en.categorised_matches("We delve deeper.", groups)
        self.assertEqual([(c, p) for c, p, _ in hits],
                         [("banned_word", "delve")])

    def test_ru_long_phrase_wins_over_a_short_one_from_another_list(self):
        groups = self._with_extra(ru, "hedge", "разберемся")
        hits = ru.categorised_matches("Давайте разберёмся с логами.", groups)
        self.assertEqual([c for c, _, _ in hits], ["ai_slop"])

    def test_ru_short_word_still_fires_on_its_own(self):
        groups = self._with_extra(ru, "hedge", "разберемся")
        hits = ru.categorised_matches("Разберёмся с логами.", groups)
        self.assertEqual([c for c, _, _ in hits], ["hedge"])

    def test_a_tie_goes_to_the_earlier_list(self):
        groups = (("banned_word", ["robust"]),
                  ("marketing_adjective", ["robust"]))
        hits = en.categorised_matches("A robust API.", groups)
        self.assertEqual([(c, p) for c, p, _ in hits],
                         [("banned_word", "robust")])

    def test_no_phrase_lives_in_two_lists(self):
        for mod, fold in ((en, lambda s: s.lower()), (ru, ru._fold)):
            seen = {}
            for cat, phrases in mod.PHRASE_GROUPS:
                for ph in phrases:
                    seen.setdefault(fold(ph), []).append(cat)
            dupes = {p: c for p, c in seen.items() if len(c) > 1}
            self.assertEqual(dupes, {}, "a phrase sits in two lists: %s" % dupes)

    def test_hits_come_back_in_reading_order(self):
        groups = (("banned_word", ["whilst"]), ("marketing_adjective", ["robust"]))
        hits = en.categorised_matches("A robust API, whilst small.", groups)
        self.assertEqual([p for _, p, _ in hits], ["robust", "whilst"])

    def test_lint_and_diagnostics_agree_on_the_samples(self):
        pairs = ((en, "en/samples/baseline.md",
                  ("banned_word", "marketing_adjective", "ai_slop")),
                 (en, "en/samples/ste.md",
                  ("banned_word", "marketing_adjective", "ai_slop")),
                 (ru, "ru/samples/baseline.md",
                  ("clerical", "marketing", "ai_slop", "hedge")),
                 (ru, "ru/samples/utr.md",
                  ("clerical", "marketing", "ai_slop", "hedge")))
        for mod, rel, cats in pairs:
            text = (ROOT / rel).read_text(encoding="utf-8")
            counts = mod.lint(text)["violations"]
            diags = mod.diagnostics(text)
            for cat in cats:
                self.assertEqual(sum(1 for d in diags if d[1] == cat),
                                 counts[cat], "%s %s" % (rel, cat))


class LexiconIntegrity(unittest.TestCase):
    """Guard the lists themselves, so a bad entry fails at edit time."""

    RU_LISTS = ("CLERICAL", "MARKETING", "AI_SLOP", "HEDGE")
    EN_LISTS = ("BANNED", "MARKETING", "AI_SLOP", "HEDGE")

    def test_ru_has_no_entry_duplicated_by_yo_folding(self):
        """Обе орфографии одной фразы — мёртвый вес после сворачивания ё."""
        for name in self.RU_LISTS:
            folded = [ru._fold(p) for p in getattr(ru, name)]
            dupes = sorted({p for p in folded if folded.count(p) > 1})
            self.assertEqual(dupes, [], "%s carries both spellings of %s" % (name, dupes))

    def test_en_has_no_duplicate_entries(self):
        for name in self.EN_LISTS:
            lowered = [p.lower() for p in getattr(en, name)]
            dupes = sorted({p for p in lowered if lowered.count(p) > 1})
            self.assertEqual(dupes, [], "%s repeats %s" % (name, dupes))

    def test_en_prefix_overlaps_do_not_double_count(self):
        """EN опирается на lookaround: следим, что это так и осталось."""
        for text, category in (("The tool facilitates review.", "banned_word"),
                               ("A seamlessly integrated pipeline.", "marketing_adjective"),
                               ("Our next-generation platform.", "marketing_adjective")):
            self.assertEqual(en.lint(text)["violations"][category], 1, text)


class SampleRegression(unittest.TestCase):
    """The samples are the contract: a slop text scores high, a clean one low."""

    def read(self, rel):
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_en_samples(self):
        bad = en.lint(self.read("en/samples/baseline.md"))
        good = en.lint(self.read("en/samples/ste.md"))
        self.assertGreater(bad["total_per100w"], 20.0)
        self.assertLess(good["total_per100w"], 2.0)
        self.assertGreater(bad["total_per100w"], good["total_per100w"] * 10)
        self.assertGreater(bad["longest_sentence_words"], 20)
        self.assertLessEqual(good["longest_sentence_words"], 20)

    def test_ru_samples(self):
        bad = ru.lint(self.read("ru/samples/baseline.md"))
        good = ru.lint(self.read("ru/samples/utr.md"))
        self.assertGreater(bad["total_per100w"], 20.0)
        self.assertLess(good["total_per100w"], 2.0)
        self.assertGreater(bad["longest_sentence_words"], 20)
        self.assertLessEqual(good["longest_sentence_words"], 20)


class ExitCodes(unittest.TestCase):
    """Without a usable exit code the linters cannot gate CI or a git hook."""

    def call(self, mod, argv):
        buf = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            code = mod.main(argv)
        return code, buf.getvalue(), err.getvalue()

    def test_no_threshold_always_passes(self):
        code, _, _ = self.call(en, [str(ROOT / "en/samples/baseline.md")])
        self.assertEqual(code, 0)

    def test_threshold_fails_on_slop(self):
        code, _, err = self.call(
            en, ["--max", "5", str(ROOT / "en/samples/baseline.md")])
        self.assertEqual(code, 1)
        self.assertIn("FAIL", err)

    def test_threshold_passes_on_clean(self):
        code, _, _ = self.call(
            en, ["--max", "5", str(ROOT / "en/samples/ste.md")])
        self.assertEqual(code, 0)

    def test_ru_threshold(self):
        bad, _, _ = self.call(
            ru, ["--max", "5", str(ROOT / "ru/samples/baseline.md")])
        good, _, _ = self.call(
            ru, ["--max", "5", str(ROOT / "ru/samples/utr.md")])
        self.assertEqual((bad, good), (1, 0))

    def test_max_equals_syntax(self):
        code, _, _ = self.call(ru, ["--max=5", str(ROOT / "ru/samples/utr.md")])
        self.assertEqual(code, 0)

    def test_unknown_option_is_usage_error(self):
        code, _, err = self.call(en, ["--nope", str(ROOT / "en/samples/ste.md")])
        self.assertEqual(code, 2)
        self.assertIn("unknown option", err)

    def test_missing_file_is_usage_error(self):
        code, _, err = self.call(en, [str(ROOT / "en/samples/nope.md")])
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)

    def test_json_output_is_valid(self):
        import json
        code, out, _ = self.call(en, ["--json", str(ROOT / "en/samples/ste.md")])
        self.assertEqual(code, 0)
        parsed = json.loads(out)
        self.assertEqual(len(parsed), 1)
        self.assertIn("total_per100w", list(parsed.values())[0])


if __name__ == "__main__":
    unittest.main()
