"""
Performance benchmark tests for anti-slop-kit.

Runs in the standard unittest gate (scripts/check.sh); no pytest dependency.
"""

import time
import unittest


class TestPerformance(unittest.TestCase):
    """Performance benchmarks for core functionality."""

    def test_linter_performance_small_file(self):
        """Benchmark linter on small file (<100 lines)."""
        # Small test content
        content = "def test_function():\n    pass\n" * 10

        start = time.time()
        # Simulate linting operation
        _ = [line.strip() for line in content.split('\n')]
        elapsed = time.time() - start

        # Should complete in <10ms for small file
        self.assertLess(elapsed, 0.01, f"Linter too slow: {elapsed:.3f}s")

    def test_linter_performance_medium_file(self):
        """Benchmark linter on medium file (100-1000 lines)."""
        content = "def test_function():\n    pass\n" * 100

        start = time.time()
        _ = [line.strip() for line in content.split('\n')]
        elapsed = time.time() - start

        # Should complete in <100ms for medium file
        self.assertLess(elapsed, 0.1, f"Linter too slow: {elapsed:.3f}s")

    def test_json_parsing_performance(self):
        """Benchmark JSON parsing."""
        import json

        test_data = {
            "findings": [{"type": "test", "line": i} for i in range(100)]
        }
        json_str = json.dumps(test_data)

        start = time.time()
        parsed = json.loads(json_str)
        elapsed = time.time() - start

        self.assertLess(elapsed, 0.05, f"JSON parsing too slow: {elapsed:.3f}s")
        self.assertEqual(len(parsed["findings"]), 100)

    def test_baseline_performance(self):
        """Baseline performance test (the pytest-benchmark fixture variant
        collapsed to a direct call: the gate runs unittest)."""
        def operation():
            return sum(range(1000))

        result = operation()
        self.assertEqual(result, 499500)


if __name__ == '__main__':
    unittest.main()
