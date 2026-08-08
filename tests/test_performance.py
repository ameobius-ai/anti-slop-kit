"""Comprehensive tests for performance module.

Part of issue #208: Increase test coverage to 90%+
Ported to unittest so scripts/check.sh collects it (issue #242).
"""

import contextlib
import io
import re
import tempfile
import time
import unittest
from pathlib import Path

from tools.aslint import performance


class TestRegexCache(unittest.TestCase):
    """Tests for RegexCache class."""

    def setUp(self):
        """Clear cache before each test."""
        performance.RegexCache.clear()

    def test_compile_basic_pattern(self):
        """Test compiling a basic regex pattern."""
        pattern = r"\bword\b"
        compiled = performance.RegexCache.compile(pattern)

        self.assertIsNotNone(compiled)
        self.assertEqual(compiled.pattern, pattern)

    def test_compile_with_flags(self):
        """Test compiling with regex flags."""
        pattern = r"test"
        compiled = performance.RegexCache.compile(pattern, re.IGNORECASE)

        self.assertIsNotNone(compiled)
        self.assertTrue(compiled.flags & re.IGNORECASE)

    def test_cache_returns_same_object(self):
        """Test that cache returns the same compiled pattern."""
        pattern = r"\btest\b"

        compiled1 = performance.RegexCache.compile(pattern)
        compiled2 = performance.RegexCache.compile(pattern)

        self.assertIs(compiled1, compiled2)

    def test_different_flags_different_cache(self):
        """Test that different flags create different cache entries."""
        pattern = r"test"

        compiled1 = performance.RegexCache.compile(pattern, 0)
        compiled2 = performance.RegexCache.compile(pattern, re.IGNORECASE)

        self.assertIsNot(compiled1, compiled2)

    def test_clear_cache(self):
        """Clearing empties the cache dict. re.compile keeps its own
        internal cache, so identity of compiled objects cannot be the check."""
        performance.RegexCache.compile(r"\btest\b")
        self.assertTrue(performance.RegexCache._cache)

        performance.RegexCache.clear()

        self.assertEqual(performance.RegexCache._cache, {})

    def test_complex_pattern(self):
        """Test compiling a complex regex pattern."""
        pattern = r"\b[A-Z][a-z]+\s+\d{4}\b"
        compiled = performance.RegexCache.compile(pattern)

        self.assertIsNotNone(compiled)
        # Test that it works
        self.assertIsNotNone(compiled.search("January 2024"))

    def test_empty_pattern(self):
        """Test compiling an empty pattern."""
        pattern = ""
        compiled = performance.RegexCache.compile(pattern)

        self.assertIsNotNone(compiled)


class TestCachedFileHash(unittest.TestCase):
    """Tests for cached_file_hash function."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)

    def test_hash_existing_file(self):
        """Test hashing an existing file."""
        test_file = self.tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        hash1 = performance.cached_file_hash(str(test_file))

        self.assertNotEqual(hash1, "")
        self.assertEqual(len(hash1), 32)  # MD5 hash length

    def test_hash_same_content_same_hash(self):
        """Test that same content produces same hash."""
        file1 = self.tmp_path / "file1.txt"
        file2 = self.tmp_path / "file2.txt"

        file1.write_text("Hello, world!")
        file2.write_text("Hello, world!")

        hash1 = performance.cached_file_hash(str(file1))
        hash2 = performance.cached_file_hash(str(file2))

        self.assertEqual(hash1, hash2)

    def test_hash_different_content_different_hash(self):
        """Test that different content produces different hash."""
        file1 = self.tmp_path / "file1.txt"
        file2 = self.tmp_path / "file2.txt"

        file1.write_text("Hello, world!")
        file2.write_text("Goodbye, world!")

        hash1 = performance.cached_file_hash(str(file1))
        hash2 = performance.cached_file_hash(str(file2))

        self.assertNotEqual(hash1, hash2)

    def test_hash_nonexistent_file(self):
        """Test hashing a nonexistent file."""
        hash_value = performance.cached_file_hash("/nonexistent/file.txt")

        self.assertEqual(hash_value, "")

    def test_cache_returns_same_value(self):
        """Test that cache returns same value for same file."""
        test_file = self.tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        hash1 = performance.cached_file_hash(str(test_file))
        hash2 = performance.cached_file_hash(str(test_file))

        self.assertEqual(hash1, hash2)


class TestParallelLintFiles(unittest.TestCase):
    """Tests for parallel_lint_files function."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)

    def test_parallel_lint_single_file(self):
        """Test parallel linting with single file."""
        test_file = self.tmp_path / "test.txt"
        test_file.write_text("Test content")

        def dummy_lint(path):
            return {"path": path, "result": "ok"}

        results = performance.parallel_lint_files([str(test_file)], dummy_lint)

        self.assertEqual(len(results), 1)
        self.assertIn(str(test_file), results)
        self.assertEqual(results[str(test_file)]["result"], "ok")

    def test_parallel_lint_multiple_files(self):
        """Test parallel linting with multiple files."""
        files = []
        for i in range(5):
            f = self.tmp_path / f"file{i}.txt"
            f.write_text(f"Content {i}")
            files.append(str(f))

        def dummy_lint(path):
            return {"path": path, "result": "ok"}

        results = performance.parallel_lint_files(files, dummy_lint)

        self.assertEqual(len(results), 5)
        for f in files:
            self.assertIn(f, results)
            self.assertEqual(results[f]["result"], "ok")

    def test_parallel_lint_with_max_workers(self):
        """Test parallel linting with explicit max_workers."""
        files = []
        for i in range(3):
            f = self.tmp_path / f"file{i}.txt"
            f.write_text(f"Content {i}")
            files.append(str(f))

        def dummy_lint(path):
            return {"path": path, "result": "ok"}

        results = performance.parallel_lint_files(files, dummy_lint, max_workers=2)

        self.assertEqual(len(results), 3)

    def test_parallel_lint_with_exception(self):
        """Test parallel linting when lint function raises exception."""
        test_file = self.tmp_path / "test.txt"
        test_file.write_text("Test content")

        def failing_lint(path):
            raise ValueError("Lint failed")

        results = performance.parallel_lint_files([str(test_file)], failing_lint)

        self.assertEqual(len(results), 1)
        self.assertIn(str(test_file), results)
        self.assertIn("error", results[str(test_file)])

    def test_parallel_lint_empty_list(self):
        """Test parallel linting with empty file list."""
        def dummy_lint(path):
            return {"path": path, "result": "ok"}

        results = performance.parallel_lint_files([], dummy_lint)

        self.assertEqual(len(results), 0)


class TestPerformanceMetrics(unittest.TestCase):
    """Tests for PerformanceMetrics class."""

    def test_start_and_stop_timer(self):
        """Test starting and stopping a timer."""
        metrics = performance.PerformanceMetrics()

        metrics.start_timer("test_operation")
        time.sleep(0.01)  # Small delay
        metrics.stop_timer("test_operation")

        report = metrics.get_report()
        self.assertIn("test_operation", report)
        self.assertGreaterEqual(report["test_operation"], 0.01)

    def test_increment_counter(self):
        """Test incrementing a counter."""
        metrics = performance.PerformanceMetrics()

        metrics.increment("counter")
        metrics.increment("counter")
        metrics.increment("counter")

        report = metrics.get_report()
        self.assertEqual(report["counter"], 3)

    def test_increment_with_amount(self):
        """Test incrementing with custom amount."""
        metrics = performance.PerformanceMetrics()

        metrics.increment("counter", 5)
        metrics.increment("counter", 3)

        report = metrics.get_report()
        self.assertEqual(report["counter"], 8)

    def test_record_metric(self):
        """Test recording a metric value."""
        metrics = performance.PerformanceMetrics()

        metrics.record("files_processed", 42)

        report = metrics.get_report()
        self.assertEqual(report["files_processed"], 42)

    def test_get_report_copy(self):
        """Test that get_report returns a copy."""
        metrics = performance.PerformanceMetrics()
        metrics.record("test", 123)

        report1 = metrics.get_report()
        report2 = metrics.get_report()

        # Should be equal but not the same object
        self.assertEqual(report1, report2)
        self.assertIsNot(report1, report2)

    def test_print_report(self):
        """Test printing a report."""
        metrics = performance.PerformanceMetrics()
        metrics.record("test_metric", 42)
        metrics.start_timer("test_timer")
        time.sleep(0.001)
        metrics.stop_timer("test_timer")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            metrics.print_report()
        out = buf.getvalue()

        self.assertIn("Performance Metrics:", out)
        self.assertIn("test_metric", out)
        self.assertIn("test_timer", out)

    def test_stop_timer_without_start(self):
        """Test stopping a timer that was never started."""
        metrics = performance.PerformanceMetrics()

        # Should not raise an error
        metrics.stop_timer("nonexistent")

        report = metrics.get_report()
        self.assertNotIn("nonexistent", report)

    def test_multiple_timers(self):
        """Test multiple timers running concurrently."""
        metrics = performance.PerformanceMetrics()

        metrics.start_timer("timer1")
        metrics.start_timer("timer2")
        time.sleep(0.01)
        metrics.stop_timer("timer1")
        time.sleep(0.01)
        metrics.stop_timer("timer2")

        report = metrics.get_report()
        self.assertIn("timer1", report)
        self.assertIn("timer2", report)
        # timer2 should be longer than timer1
        self.assertGreater(report["timer2"], report["timer1"])


class TestGlobalMetrics(unittest.TestCase):
    """Tests for global metrics instance."""

    def test_global_metrics_exists(self):
        """Test that global metrics instance exists."""
        self.assertIsNotNone(performance.metrics)
        self.assertIsInstance(performance.metrics, performance.PerformanceMetrics)

    def test_global_metrics_functional(self):
        """Test that global metrics instance is functional."""
        performance.metrics.increment("global_counter")

        report = performance.metrics.get_report()
        self.assertIn("global_counter", report)


if __name__ == '__main__':
    unittest.main()
