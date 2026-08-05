"""Tests for the eval scorer.

The scorer measures fact preservation across rewrites: lexical facts are
extracted from source.md and rewritten.md, and fidelity is the share of
source facts that survived. Task directories live under evals/tasks/<id>/
with source.md, rewritten.md, and optional metadata.json.
"""

import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    # dataclasses in score.py resolve annotations via sys.modules on py<3.11
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


score = load("evals/score.py", "score")

SOURCE = (
    "Call GET /api/v1/users before 2024-11-15T02:00 UTC. "
    "Send the X-Request-Id header. Budget is 1,247 requests; 5% get a "
    "4xx reply.\n"
)

# Same facts in different dress: canonicalization must keep fidelity at 1.0.
REWRITTEN_CANON = (
    "GET /api/v1/users has to be called before 2024-11-15 02:00. "
    "Include header X-Request-Id. The budget is 1247 requests and 5% "
    "receive a 4xx response.\n"
)


def make_task(tasks_dir, task_id, source, rewritten, metadata=None):
    task_dir = tasks_dir / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "source.md").write_text(source, encoding="utf-8")
    (task_dir / "rewritten.md").write_text(rewritten, encoding="utf-8")
    if metadata is not None:
        (task_dir / "metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )
    return task_dir


class ExtractFacts(unittest.TestCase):
    def test_detects_every_token_kind(self):
        facts = score.extract_facts(SOURCE)
        self.assertIn("endpoint:get /api/v1/users", facts)
        self.assertIn("header:x-request-id", facts)
        self.assertIn("errorclass:4xx", facts)
        self.assertIn("number:1247", facts)
        self.assertIn("number:5%", facts)
        self.assertTrue(any(f.startswith("timestamp:") for f in facts))

    def test_number_canonicalization_drops_thousands_separators(self):
        self.assertEqual(
            score.extract_facts("limit 1,247"), score.extract_facts("limit 1247")
        )

    def test_percent_stays_distinct_from_plain_numbers(self):
        self.assertNotEqual(
            score.extract_facts("5% of calls"), score.extract_facts("5 calls")
        )

    def test_timestamp_canonicalization(self):
        self.assertEqual(
            score.extract_facts("due 2024-11-15T02:00 UTC"),
            score.extract_facts("due 2024-11-15 02:00"),
        )

    def test_empty_text_has_no_facts(self):
        self.assertEqual(score.extract_facts(""), set())


class TaskScoring(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tasks_dir = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_identical_rewrite_scores_one(self):
        task_dir = make_task(self.tasks_dir, "en-01", SOURCE, SOURCE)
        result = score.score_task(task_dir)
        self.assertIsNone(result["error"])
        self.assertEqual(result["fidelity_score"], 1.0)
        self.assertEqual(result["missing_fact_count"], 0)

    def test_canonical_forms_count_as_preserved(self):
        task_dir = make_task(self.tasks_dir, "en-01", SOURCE, REWRITTEN_CANON)
        result = score.score_task(task_dir)
        self.assertEqual(result["fidelity_score"], 1.0)

    def test_dropped_fact_is_reported(self):
        rewritten = SOURCE.replace("X-Request-Id", "request identifier")
        task_dir = make_task(self.tasks_dir, "en-01", SOURCE, rewritten)
        result = score.score_task(task_dir)
        self.assertIn("header:x-request-id", result["missing_facts"])
        self.assertLess(result["fidelity_score"], 1.0)
        self.assertEqual(result["missing_fact_count"], len(result["missing_facts"]))

    def test_missing_source_is_an_error(self):
        task_dir = make_task(self.tasks_dir, "en-01", SOURCE, SOURCE)
        (task_dir / "source.md").unlink()
        result = score.score_task(task_dir)
        self.assertEqual(result["error"], "missing_file:source.md")

    def test_factless_source_is_rejected(self):
        task_dir = make_task(self.tasks_dir, "en-01", "no facts here", "same")
        self.assertEqual(
            score.score_task(task_dir)["error"], "no_source_facts_extracted"
        )

    def test_not_a_directory(self):
        result = score.score_task(self.tasks_dir / "ghost")
        self.assertEqual(result["error"], "not_a_directory")

    def test_missing_metadata_is_unknown_not_fatal(self):
        task_dir = make_task(self.tasks_dir, "en-01", SOURCE, SOURCE)
        result = score.score_task(task_dir)
        self.assertIsNone(result["metadata_error"])
        self.assertEqual(result["task_type"], "unknown")

    def test_metadata_fills_task_type_and_population(self):
        task_dir = make_task(
            self.tasks_dir,
            "en-01",
            SOURCE,
            SOURCE,
            {"task_type": "api-doc", "population": "en"},
        )
        result = score.score_task(task_dir)
        self.assertEqual(result["task_type"], "api-doc")
        self.assertEqual(result["population"], "en")

    def test_corrupt_metadata_is_surfaced_separately(self):
        task_dir = make_task(self.tasks_dir, "en-01", SOURCE, SOURCE)
        (task_dir / "metadata.json").write_text("{nope", encoding="utf-8")
        result = score.score_task(task_dir)
        self.assertIsNone(result["error"])
        self.assertTrue(result["metadata_error"].startswith("metadata_json_error:"))

    def test_oversized_source_hits_the_guard(self):
        task_dir = make_task(self.tasks_dir, "en-01", SOURCE, SOURCE)
        original = score.MAX_FILE_BYTES
        score.MAX_FILE_BYTES = 10
        try:
            result = score.score_task(task_dir)
        finally:
            score.MAX_FILE_BYTES = original
        self.assertEqual(result["error"], "file_too_large:source.md")


class Aggregation(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tasks_dir = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        make_task(
            self.tasks_dir,
            "task-a",
            SOURCE,
            SOURCE,
            {"task_type": "api-doc", "population": "en"},
        )
        # Drops the X-Request-Id fact: fidelity below 1.0.
        make_task(
            self.tasks_dir,
            "task-b",
            SOURCE,
            SOURCE.replace("X-Request-Id", "a header"),
            {"task_type": "api-doc", "population": "ru"},
        )

    def test_aggregate_and_grouping(self):
        summary = score.score_all(self.tasks_dir)
        self.assertEqual(summary["task_count"], 2)
        self.assertFalse(summary["truncated"])
        self.assertNotIn("error", summary)
        self.assertAlmostEqual(
            summary["aggregate_fidelity"],
            round((1.0 + summary["results"][1]["fidelity_score"]) / 2, 4),
        )
        by_type = summary["by_task_type"]["api-doc"]
        self.assertEqual(by_type["task_count"], 2)
        self.assertEqual(summary["by_population"]["en"]["task_count"], 1)
        self.assertEqual(
            summary["by_population"]["en"]["aggregate_fidelity"], 1.0
        )
        self.assertLess(
            summary["by_population"]["ru"]["aggregate_fidelity"], 1.0
        )

    def test_task_filter_limits_the_run(self):
        summary = score.score_all(self.tasks_dir, task_filter="task-a")
        self.assertEqual(summary["task_count"], 1)
        self.assertEqual(summary["results"][0]["task_id"], "task-a")

    def test_filter_without_match_is_no_tasks_found(self):
        summary = score.score_all(self.tasks_dir, task_filter="ghost")
        self.assertEqual(summary["task_count"], 0)
        self.assertEqual(summary["error"], "no_tasks_found")

    def test_missing_tasks_dir(self):
        summary = score.score_all(self.tasks_dir / "nope")
        self.assertTrue(summary["error"].startswith("tasks_dir_missing:"))


class Markdown(unittest.TestCase):
    def test_render_includes_tables_and_task_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            tasks_dir = pathlib.Path(directory)
            make_task(
                tasks_dir,
                "en-01",
                SOURCE,
                SOURCE,
                {"task_type": "api-doc", "population": "en"},
            )
            text = score.render_markdown(score.score_all(tasks_dir))
        self.assertIn("# Eval results", text)
        self.assertIn("## By task type", text)
        self.assertIn("## By population", text)
        self.assertIn("| en-01 | api-doc | en |", text)

    def test_render_shows_summary_errors(self):
        text = score.render_markdown({"error": "no_tasks_found"})
        self.assertIn("Error: no_tasks_found", text)


class Cli(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tasks_dir = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_clean_run_exits_zero_and_writes_outputs(self):
        make_task(self.tasks_dir, "en-01", SOURCE, SOURCE)
        json_out = self.tasks_dir / "out.json"
        md_out = self.tasks_dir / "out.md"
        exit_code = score.main(
            [
                "--tasks-dir",
                str(self.tasks_dir),
                "--json-out",
                str(json_out),
                "--markdown-out",
                str(md_out),
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(json_out.read_text(encoding="utf-8"))["task_count"], 1)
        self.assertIn("# Eval results", md_out.read_text(encoding="utf-8"))

    def test_missing_tasks_dir_exits_two(self):
        self.assertEqual(
            score.main(["--tasks-dir", str(self.tasks_dir / "nope"), "--strict"]),
            2,
        )

    def test_empty_tasks_dir_exits_two(self):
        self.assertEqual(
            score.main(["--tasks-dir", str(self.tasks_dir), "--strict"]), 2
        )

    def test_strict_fails_on_metadata_errors(self):
        task_dir = make_task(self.tasks_dir, "en-01", SOURCE, SOURCE)
        (task_dir / "metadata.json").write_text("{bad", encoding="utf-8")
        self.assertEqual(
            score.main(["--tasks-dir", str(self.tasks_dir), "--strict"]), 1
        )

    def test_not_strict_tolerates_metadata_errors(self):
        task_dir = make_task(self.tasks_dir, "en-01", SOURCE, SOURCE)
        (task_dir / "metadata.json").write_text("{bad", encoding="utf-8")
        self.assertEqual(score.main(["--tasks-dir", str(self.tasks_dir)]), 0)

    def test_task_filter_selects_one_task(self):
        make_task(self.tasks_dir, "task-a", SOURCE, SOURCE)
        make_task(self.tasks_dir, "task-b", SOURCE, SOURCE)
        json_out = self.tasks_dir / "out.json"
        exit_code = score.main(
            [
                "--tasks-dir",
                str(self.tasks_dir),
                "--task",
                "task-b",
                "--json-out",
                str(json_out),
            ]
        )
        self.assertEqual(exit_code, 0)
        summary = json.loads(json_out.read_text(encoding="utf-8"))
        self.assertEqual([row["task_id"] for row in summary["results"]], ["task-b"])


if __name__ == "__main__":
    unittest.main()
