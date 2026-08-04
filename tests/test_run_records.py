#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the eval runner.

The runner had no tests at all. It is the one script in this repository that
produces data rather than checking it, and the first live run proved why that
matters: only the scored copies survived, so the generations could not be
re-scored after a linter change and the gallery in examples/ had to be written
by hand.

Nothing here touches the network. `generate` takes the caller as an argument,
so a fake returns a canned answer and every path is exercised offline.
"""

import importlib.util
import io
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run = load("evals/run.py", "run")

ANSWER = "Set the timeout to 30 seconds. Read the log file to find the error.\n"


def fake_caller(system, user):
    return ANSWER, {"choices": [{"message": {"content": ANSWER}}], "model": "fake"}


def exploding_caller(system, user):
    raise OSError("connection reset")


class Naming(unittest.TestCase):
    def test_a_single_run_keeps_the_scorer_convention(self):
        """score.py parses these names, so the suffix rule is a contract."""
        self.assertEqual(run.cell_name("en-01-api-doc", "bare", 1, 1),
                         "en-01-api-doc__bare")

    def test_repeats_are_numbered(self):
        self.assertEqual(run.cell_name("en-01-api-doc", "bare", 2, 3),
                         "en-01-api-doc__bare__r2")

    def test_a_model_name_becomes_a_safe_directory(self):
        self.assertEqual(run.slug("vendor/model:free"), "vendor-model-free")
        self.assertEqual(run.slug("///"), "model")

    def test_the_same_prompt_has_the_same_digest(self):
        self.assertEqual(run.digest("abc"), run.digest("abc"))
        self.assertNotEqual(run.digest("abc"), run.digest("abd"))


class EndpointRecording(unittest.TestCase):
    """A run record is committed. It must not carry credentials."""

    def test_a_query_string_is_dropped(self):
        self.assertEqual(run.endpoint_host("https://api.example.com/v1?key=secret"),
                         "https://api.example.com/v1")

    def test_userinfo_is_dropped(self):
        self.assertNotIn("secret",
                         run.endpoint_host("https://user:secret@api.example.com/v1"))

    def test_a_local_port_survives(self):
        self.assertEqual(run.endpoint_host("http://127.0.0.1:8317/v1"),
                         "http://127.0.0.1:8317/v1")


class Prompts(unittest.TestCase):
    """The prompts are the payload of the experiment, and nothing read them.

    The Russian prompts were briefly written into the source as \\u041f-style
    escapes. That turned out to be harmless: Python decodes those escapes in a
    normal string literal at import, so the run would have been correct. The
    point stands anyway. No test could tell that file apart from one where the
    escapes had leaked into the string as text, which is what a raw literal or
    a docstring would have produced. These checks read the prompts the way the
    API receives them.
    """

    def test_the_russian_prompts_are_cyrillic(self):
        prompts = run.prompts("ru")
        for condition in ("plain", "banlist", "skill"):
            text = prompts[condition]
            self.assertTrue(any("\u0410" <= ch <= "\u044f" for ch in text),
                            "the ru %s prompt has no Cyrillic in it" % condition)

    def test_no_prompt_carries_an_unrendered_escape(self):
        for lang in ("en", "ru"):
            for condition, text in run.prompts(lang).items():
                self.assertNotIn("\\u", text,
                                 "the %s %s prompt holds a literal escape"
                                 % (lang, condition))

    def test_bare_sends_no_system_prompt(self):
        """bare is the control. An instruction here would void the comparison."""
        for lang in ("en", "ru"):
            self.assertEqual(run.prompts(lang)["bare"], "")

    def test_the_skill_prompt_is_the_shipped_skill(self):
        for lang in ("en", "ru"):
            shipped = (ROOT / lang / "SKILL.md").read_text(encoding="utf-8")
            self.assertEqual(run.prompts(lang)["skill"], shipped)

    def test_the_four_conditions_have_distinct_prompts(self):
        for lang in ("en", "ru"):
            texts = list(run.prompts(lang).values())
            self.assertEqual(len(texts), len(set(texts)))


class RunRecords(unittest.TestCase):
    def go(self, caller, existing=None, repeat=1):
        self.tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self.tmp.name)
        out, record = base / "outputs", base / "record"
        out.mkdir()
        for name in existing or []:
            (out / name).write_text("old text\n", encoding="utf-8")
        entries, failures = run.generate(
            "en", "fake-model", out, record, repeat=repeat,
            caller=caller, stream=io.StringIO())
        return out, record, entries, failures

    def tearDown(self):
        if getattr(self, "tmp", None):
            self.tmp.cleanup()

    def test_every_cell_leaves_text_raw_and_a_manifest_entry(self):
        out, record, entries, failures = self.go(fake_caller)
        self.assertEqual(failures, 0)
        self.assertTrue(entries, "no tasks were found for en")
        for entry in entries:
            self.assertEqual(entry["status"], "written")
            name = entry["cell"]
            self.assertTrue((out / ("%s.md" % name)).is_file())
            self.assertTrue((record / "outputs" / ("%s.md" % name)).is_file())
            self.assertTrue((record / "raw" / ("%s.json" % name)).is_file())

    def test_the_four_conditions_are_all_present(self):
        _, _, entries, _ = self.go(fake_caller)
        self.assertEqual({e["condition"] for e in entries},
                         {"bare", "plain", "banlist", "skill"})

    def test_the_prompts_are_saved_verbatim(self):
        """Without the prompt, a score cannot be attributed to anything."""
        _, record, _, _ = self.go(fake_caller)
        saved = (record / "prompts" / "skill.txt").read_text(encoding="utf-8")
        self.assertEqual(saved, (ROOT / "en" / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual((record / "prompts" / "bare.txt").read_text(encoding="utf-8"), "")

    def test_the_raw_response_is_kept_whole(self):
        _, record, entries, _ = self.go(fake_caller)
        name = entries[0]["cell"]
        raw = json.loads((record / "raw" / ("%s.json" % name)).read_text(encoding="utf-8"))
        self.assertEqual(raw["model"], "fake")

    def test_a_skipped_cell_is_recorded_not_hidden(self):
        """A resumed run used to write nothing and say nothing."""
        first = sorted(p.stem for p in run.tasks("en"))[0]
        out, record, entries, _ = self.go(
            fake_caller, existing=["%s__bare.md" % first])
        statuses = {e["cell"]: e["status"] for e in entries}
        self.assertEqual(statuses["%s__bare" % first], "skipped_existing")
        self.assertEqual((out / ("%s__bare.md" % first)).read_text(encoding="utf-8"),
                         "old text\n")
        self.assertFalse((record / "raw" / ("%s__bare.json" % first)).exists())

    def test_a_failed_call_is_recorded_and_counted(self):
        _, record, entries, failures = self.go(exploding_caller)
        self.assertEqual(failures, len(entries))
        self.assertTrue(all(e["status"] == "failed" for e in entries))
        self.assertIn("connection reset", entries[0]["error"])

    def test_a_failure_does_not_stop_the_run(self):
        """One dead cell must not cost the other twenty-three."""
        calls = {"n": 0}

        def flaky(system, user):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("first cell died")
            return fake_caller(system, user)

        _, _, entries, failures = self.go(flaky)
        self.assertEqual(failures, 1)
        self.assertEqual(sum(1 for e in entries if e["status"] == "written"),
                         len(entries) - 1)

    def test_repeats_produce_distinct_cells(self):
        _, _, entries, _ = self.go(fake_caller, repeat=2)
        names = [e["cell"] for e in entries]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(any(name.endswith("__r2") for name in names))


class Manifest(unittest.TestCase):
    def test_it_counts_each_status_and_hides_the_key(self):
        entries = [{"cell": "a", "status": "written"},
                   {"cell": "b", "status": "failed"},
                   {"cell": "c", "status": "written"}]
        meta = run.manifest("en", "m", "https://api.example.com/v1?key=secret",
                            1, 180, entries, "start", "finish")
        self.assertEqual(meta["counts"], {"written": 2, "failed": 1})
        self.assertEqual(meta["cells"], 3)
        self.assertNotIn("secret", json.dumps(meta))


if __name__ == "__main__":
    unittest.main()
