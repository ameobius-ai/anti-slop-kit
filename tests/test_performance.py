"""Comprehensive tests for performance module.

Part of issue #208: Increase test coverage to 90%+
"""

import re
import time
from pathlib import Path

import pytest

from tools.aslint import performance


class TestRegexCache:
    """Tests for RegexCache class."""
    
    def setup_method(self):
        """Clear cache before each test."""
        performance.RegexCache.clear()
    
    def test_compile_basic_pattern(self):
        """Test compiling a basic regex pattern."""
        pattern = r"\bword\b"
        compiled = performance.RegexCache.compile(pattern)
        
        assert compiled is not None
        assert compiled.pattern == pattern
    
    def test_compile_with_flags(self):
        """Test compiling with regex flags."""
        pattern = r"test"
        compiled = performance.RegexCache.compile(pattern, re.IGNORECASE)
        
        assert compiled is not None
        assert compiled.flags & re.IGNORECASE
    
    def test_cache_returns_same_object(self):
        """Test that cache returns the same compiled pattern."""
        pattern = r"\btest\b"
        
        compiled1 = performance.RegexCache.compile(pattern)
        compiled2 = performance.RegexCache.compile(pattern)
        
        assert compiled1 is compiled2
    
    def test_different_flags_different_cache(self):
        """Test that different flags create different cache entries."""
        pattern = r"test"
        
        compiled1 = performance.RegexCache.compile(pattern, 0)
        compiled2 = performance.RegexCache.compile(pattern, re.IGNORECASE)
        
        assert compiled1 is not compiled2
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        pattern = r"\btest\b"
        compiled1 = performance.RegexCache.compile(pattern)
        
        performance.RegexCache.clear()
        
        compiled2 = performance.RegexCache.compile(pattern)
        
        # After clear, should be a different object
        assert compiled1 is not compiled2
    
    def test_complex_pattern(self):
        """Test compiling a complex regex pattern."""
        pattern = r"\b[A-Z][a-z]+\s+\d{4}\b"
        compiled = performance.RegexCache.compile(pattern)
        
        assert compiled is not None
        # Test that it works
        assert compiled.search("January 2024") is not None
    
    def test_empty_pattern(self):
        """Test compiling an empty pattern."""
        pattern = ""
        compiled = performance.RegexCache.compile(pattern)
        
        assert compiled is not None


class TestCachedFileHash:
    """Tests for cached_file_hash function."""
    
    def test_hash_existing_file(self, tmp_path):
        """Test hashing an existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")
        
        hash1 = performance.cached_file_hash(str(test_file))
        
        assert hash1 != ""
        assert len(hash1) == 32  # MD5 hash length
    
    def test_hash_same_content_same_hash(self, tmp_path):
        """Test that same content produces same hash."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("Hello, world!")
        file2.write_text("Hello, world!")
        
        hash1 = performance.cached_file_hash(str(file1))
        hash2 = performance.cached_file_hash(str(file2))
        
        assert hash1 == hash2
    
    def test_hash_different_content_different_hash(self, tmp_path):
        """Test that different content produces different hash."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("Hello, world!")
        file2.write_text("Goodbye, world!")
        
        hash1 = performance.cached_file_hash(str(file1))
        hash2 = performance.cached_file_hash(str(file2))
        
        assert hash1 != hash2
    
    def test_hash_nonexistent_file(self):
        """Test hashing a nonexistent file."""
        hash_value = performance.cached_file_hash("/nonexistent/file.txt")
        
        assert hash_value == ""
    
    def test_cache_returns_same_value(self, tmp_path):
        """Test that cache returns same value for same file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")
        
        hash1 = performance.cached_file_hash(str(test_file))
        hash2 = performance.cached_file_hash(str(test_file))
        
        assert hash1 == hash2


class TestParallelLintFiles:
    """Tests for parallel_lint_files function."""
    
    def test_parallel_lint_single_file(self, tmp_path):
        """Test parallel linting with single file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        def dummy_lint(path):
            return {"path": path, "result": "ok"}
        
        results = performance.parallel_lint_files([str(test_file)], dummy_lint)
        
        assert len(results) == 1
        assert str(test_file) in results
        assert results[str(test_file)]["result"] == "ok"
    
    def test_parallel_lint_multiple_files(self, tmp_path):
        """Test parallel linting with multiple files."""
        files = []
        for i in range(5):
            f = tmp_path / f"file{i}.txt"
            f.write_text(f"Content {i}")
            files.append(str(f))
        
        def dummy_lint(path):
            return {"path": path, "result": "ok"}
        
        results = performance.parallel_lint_files(files, dummy_lint)
        
        assert len(results) == 5
        for f in files:
            assert f in results
            assert results[f]["result"] == "ok"
    
    def test_parallel_lint_with_max_workers(self, tmp_path):
        """Test parallel linting with explicit max_workers."""
        files = []
        for i in range(3):
            f = tmp_path / f"file{i}.txt"
            f.write_text(f"Content {i}")
            files.append(str(f))
        
        def dummy_lint(path):
            return {"path": path, "result": "ok"}
        
        results = performance.parallel_lint_files(files, dummy_lint, max_workers=2)
        
        assert len(results) == 3
    
    def test_parallel_lint_with_exception(self, tmp_path):
        """Test parallel linting when lint function raises exception."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        def failing_lint(path):
            raise ValueError("Lint failed")
        
        results = performance.parallel_lint_files([str(test_file)], failing_lint)
        
        assert len(results) == 1
        assert str(test_file) in results
        assert "error" in results[str(test_file)]
    
    def test_parallel_lint_empty_list(self):
        """Test parallel linting with empty file list."""
        def dummy_lint(path):
            return {"path": path, "result": "ok"}
        
        results = performance.parallel_lint_files([], dummy_lint)
        
        assert len(results) == 0


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics class."""
    
    def test_start_and_stop_timer(self):
        """Test starting and stopping a timer."""
        metrics = performance.PerformanceMetrics()
        
        metrics.start_timer("test_operation")
        time.sleep(0.01)  # Small delay
        metrics.stop_timer("test_operation")
        
        report = metrics.get_report()
        assert "test_operation" in report
        assert report["test_operation"] >= 0.01
    
    def test_increment_counter(self):
        """Test incrementing a counter."""
        metrics = performance.PerformanceMetrics()
        
        metrics.increment("counter")
        metrics.increment("counter")
        metrics.increment("counter")
        
        report = metrics.get_report()
        assert report["counter"] == 3
    
    def test_increment_with_amount(self):
        """Test incrementing with custom amount."""
        metrics = performance.PerformanceMetrics()
        
        metrics.increment("counter", 5)
        metrics.increment("counter", 3)
        
        report = metrics.get_report()
        assert report["counter"] == 8
    
    def test_record_metric(self):
        """Test recording a metric value."""
        metrics = performance.PerformanceMetrics()
        
        metrics.record("files_processed", 42)
        
        report = metrics.get_report()
        assert report["files_processed"] == 42
    
    def test_get_report_copy(self):
        """Test that get_report returns a copy."""
        metrics = performance.PerformanceMetrics()
        metrics.record("test", 123)
        
        report1 = metrics.get_report()
        report2 = metrics.get_report()
        
        # Should be equal but not the same object
        assert report1 == report2
        assert report1 is not report2
    
    def test_print_report(self, capsys):
        """Test printing a report."""
        metrics = performance.PerformanceMetrics()
        metrics.record("test_metric", 42)
        metrics.start_timer("test_timer")
        time.sleep(0.001)
        metrics.stop_timer("test_timer")
        
        metrics.print_report()
        
        captured = capsys.readouterr()
        assert "Performance Metrics:" in captured.out
        assert "test_metric" in captured.out
        assert "test_timer" in captured.out
    
    def test_stop_timer_without_start(self):
        """Test stopping a timer that was never started."""
        metrics = performance.PerformanceMetrics()
        
        # Should not raise an error
        metrics.stop_timer("nonexistent")
        
        report = metrics.get_report()
        assert "nonexistent" not in report
    
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
        assert "timer1" in report
        assert "timer2" in report
        # timer2 should be longer than timer1
        assert report["timer2"] > report["timer1"]


class TestGlobalMetrics:
    """Tests for global metrics instance."""
    
    def test_global_metrics_exists(self):
        """Test that global metrics instance exists."""
        assert performance.metrics is not None
        assert isinstance(performance.metrics, performance.PerformanceMetrics)
    
    def test_global_metrics_functional(self):
        """Test that global metrics instance is functional."""
        performance.metrics.increment("global_counter")
        
        report = performance.metrics.get_report()
        assert "global_counter" in report
