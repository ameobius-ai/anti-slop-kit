"""Performance optimization utilities for linter.

Provides caching, parallelization, and other performance enhancements.
Part of issue #24: Optimize linter performance for large documents.
"""

import re
import hashlib
from functools import lru_cache
from typing import Pattern, Dict, Any
from pathlib import Path
import concurrent.futures
from multiprocessing import cpu_count


class RegexCache:
    """Cache compiled regex patterns to avoid repeated compilation.
    
    Regex compilation is expensive. This cache ensures each unique pattern
    is compiled only once per process lifetime.
    """
    
    _cache: Dict[str, Pattern] = {}
    
    @classmethod
    def compile(cls, pattern: str, flags: int = 0) -> Pattern:
        """Compile and cache a regex pattern.
        
        Args:
            pattern: Regex pattern string
            flags: Regex flags (re.IGNORECASE, etc.)
        
        Returns:
            Compiled regex pattern
        """
        cache_key = f"{pattern}:{flags}"
        
        if cache_key not in cls._cache:
            cls._cache[cache_key] = re.compile(pattern, flags)
        
        return cls._cache[cache_key]
    
    @classmethod
    def clear(cls):
        """Clear the pattern cache."""
        cls._cache.clear()


@lru_cache(maxsize=1024)
def cached_file_hash(file_path: str) -> str:
    """Cache file hash to avoid re-reading unchanged files.
    
    Args:
        file_path: Path to file
    
    Returns:
        MD5 hash of file content
    """
    path = Path(file_path)
    if not path.exists():
        return ""
    
    content = path.read_bytes()
    return hashlib.md5(content).hexdigest()


def parallel_lint_files(
    file_paths: list,
    lint_func: callable,
    max_workers: int = None
) -> dict:
    """Lint multiple files in parallel using ThreadPoolExecutor.
    
    Args:
        file_paths: List of file paths to lint
        lint_func: Linting function that takes a file path
        max_workers: Maximum number of worker threads (default: CPU count)
    
    Returns:
        Dictionary mapping file paths to linting results
    """
    if max_workers is None:
        max_workers = min(cpu_count(), len(file_paths))
    
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(lint_func, path): path
            for path in file_paths
        }
        
        for future in concurrent.futures.as_completed(future_to_path):
            path = future_to_path[future]
            try:
                result = future.result()
                results[path] = result
            except Exception as e:
                results[path] = {"error": str(e)}
    
    return results


class PerformanceMetrics:
    """Track and report performance metrics."""
    
    def __init__(self):
        self.metrics = {}
        self._start_times = {}
    
    def start_timer(self, name: str):
        """Start timing an operation."""
        import time
        self._start_times[name] = time.perf_counter()
    
    def stop_timer(self, name: str):
        """Stop timing an operation and record duration."""
        import time
        if name in self._start_times:
            elapsed = time.perf_counter() - self._start_times[name]
            self.metrics[name] = elapsed
            del self._start_times[name]
    
    def increment(self, name: str, amount: int = 1):
        """Increment a counter metric."""
        self.metrics[name] = self.metrics.get(name, 0) + amount
    
    def record(self, name: str, value: Any):
        """Record a metric value."""
        self.metrics[name] = value
    
    def get_report(self) -> dict:
        """Get all recorded metrics."""
        return self.metrics.copy()
    
    def print_report(self):
        """Print a formatted performance report."""
        print("\nPerformance Metrics:")
        print("-" * 60)
        for name, value in sorted(self.metrics.items()):
            if isinstance(value, float):
                print(f"  {name}: {value:.4f}s")
            else:
                print(f"  {name}: {value}")
        print("-" * 60)


# Global metrics instance
metrics = PerformanceMetrics()
