#!/usr/bin/env python3
"""Benchmark suite for linter performance testing.

Generates test documents of various sizes and measures linting performance.
Part of issue #24: Optimize linter performance for large documents.
"""

import time
import sys
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.aslint.lint_tool import lint_file


def generate_test_document(word_count: int, slop_density: float = 0.01) -> str:
    """Generate a test document with specified word count and slop density.
    
    Args:
        word_count: Target number of words
        slop_density: Fraction of sentences containing slop patterns (0.0-1.0)
    
    Returns:
        Generated document text
    """
    # Base vocabulary
    words = [
        "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing",
        "elit", "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore",
        "et", "dolore", "magna", "aliqua", "enim", "ad", "minim", "veniam",
        "quis", "nostrud", "exercitation", "ullamco", "laboris", "nisi",
        "aliquip", "ex", "ea", "commodo", "consequat"
    ]
    
    # Slop patterns to inject
    slop_patterns = [
        "leverage synergies",
        "drill down into",
        "circle back",
        "move the needle",
        "low-hanging fruit",
        "think outside the box",
        "at the end of the day",
        "going forward",
        "best practices",
        "deep dive"
    ]
    
    sentences = []
    words_generated = 0
    
    while words_generated < word_count:
        # Decide if this sentence should contain slop
        has_slop = (words_generated % 100) < (slop_density * 100)
        
        if has_slop and slop_patterns:
            # Inject slop pattern
            sentence = slop_patterns[words_generated % len(slop_patterns)]
            words_generated += len(sentence.split())
        else:
            # Generate normal sentence (8-15 words)
            sentence_length = 8 + (words_generated % 8)
            sentence_words = []
            for _ in range(sentence_length):
                sentence_words.append(words[(words_generated + _) % len(words)])
            sentence = " ".join(sentence_words)
            words_generated += sentence_length
        
        sentences.append(sentence.capitalize() + ".")
    
    return "\n\n".join(sentences)


def benchmark_document(doc_text: str, doc_name: str, temp_path: Path) -> float:
    """Benchmark linting a single document.
    
    Args:
        doc_text: Document content
        doc_name: Name for reporting
        temp_path: Temporary file path
    
    Returns:
        Linting time in seconds
    """
    # Write document to temp file
    temp_path.write_text(doc_text, encoding='utf-8')
    
    # Benchmark linting
    start_time = time.perf_counter()
    try:
        lint_file(str(temp_path))
    except Exception as e:
        print(f"  Warning: linting failed: {e}")
    end_time = time.perf_counter()
    
    elapsed = end_time - start_time
    print(f"  {doc_name}: {elapsed:.4f}s")
    
    return elapsed


def run_benchmarks():
    """Run complete benchmark suite."""
    print("=" * 80)
    print("LINTER PERFORMANCE BENCHMARK")
    print("=" * 80)
    
    # Document sizes to test
    sizes = [
        (1_000, "1k words"),
        (5_000, "5k words"),
        (10_000, "10k words"),
        (50_000, "50k words"),
        (100_000, "100k words"),
    ]
    
    # Create temp directory
    temp_dir = Path("/tmp/anti-slop-benchmark")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / "test_doc.md"
    
    results = []
    
    print("\n1. Single document benchmarks:")
    print("-" * 80)
    
    for word_count, doc_name in sizes:
        print(f"\nGenerating {doc_name} document...")
        doc_text = generate_test_document(word_count, slop_density=0.01)
        
        print(f"Linting {doc_name}...")
        elapsed = benchmark_document(doc_text, doc_name, temp_path)
        results.append((doc_name, word_count, elapsed))
    
    # Calculate performance metrics
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"{'Document':<15} {'Words':>10} {'Time (s)':>10} {'Words/s':>12}")
    print("-" * 80)
    
    for doc_name, word_count, elapsed in results:
        words_per_sec = word_count / elapsed if elapsed > 0 else 0
        print(f"{doc_name:<15} {word_count:>10,} {elapsed:>10.4f} {words_per_sec:>12,.0f}")
    
    # Batch processing benchmark
    print("\n" + "=" * 80)
    print("BATCH PROCESSING BENCHMARK")
    print("=" * 80)
    
    print("\nGenerating 100 documents (1k words each)...")
    batch_docs = []
    for i in range(100):
        doc_text = generate_test_document(1_000, slop_density=0.01)
        batch_docs.append((f"doc_{i:03d}.md", doc_text))
    
    print("Linting 100 documents sequentially...")
    start_time = time.perf_counter()
    for doc_name, doc_text in batch_docs:
        temp_doc_path = temp_dir / doc_name
        temp_doc_path.write_text(doc_text, encoding='utf-8')
        try:
            lint_file(str(temp_doc_path))
        except Exception:
            pass
    end_time = time.perf_counter()
    
    sequential_time = end_time - start_time
    print(f"  Sequential: {sequential_time:.2f}s ({sequential_time/100:.4f}s per doc)")
    
    # Cleanup
    print("\nCleaning up...")
    for file in temp_dir.glob("*.md"):
        file.unlink()
    
    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    run_benchmarks()
