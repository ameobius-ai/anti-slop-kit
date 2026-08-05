#!/usr/bin/env python3
"""Score evaluation results for round-trip transmission fidelity.

This script scores how well rewrites preserve the original content's
meaning and structure across different evaluation conditions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class FidelityResult:
    """Result of fidelity scoring for a single task."""
    
    task_id: str
    condition: str
    score: float
    facts_preserved: int
    facts_total: int
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "condition": self.condition,
            "score": self.score,
            "facts_preserved": self.facts_preserved,
            "facts_total": self.facts_total,
            "details": self.details,
        }


def extract_facts(text: str) -> List[str]:
    """Extract factual claims from text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        List of extracted facts
    """
    facts: List[str] = []
    
    # Extract numbers and percentages
    number_pattern = r'\b\d+(?:\.\d+)?%?\b'
    facts.extend(re.findall(number_pattern, text))
    
    # Extract URLs
    url_pattern = r'https?://[^\s]+'
    facts.extend(re.findall(url_pattern, text))
    
    # Extract identifiers (camelCase, snake_case)
    id_pattern = r'\b[a-z][a-zA-Z0-9_]+\b'
    facts.extend(re.findall(id_pattern, text))
    
    # Extract quoted strings
    quote_pattern = r'["\']([^"\']+)["\']'
    facts.extend(re.findall(quote_pattern, text))
    
    return facts


def calculate_fidelity(
    original: str,
    rewrite: str,
    task_id: str,
    condition: str
) -> FidelityResult:
    """Calculate fidelity score between original and rewrite.
    
    Args:
        original: Original text
        rewrite: Rewritten text
        task_id: Task identifier
        condition: Evaluation condition name
        
    Returns:
        FidelityResult with score and details
    """
    original_facts = extract_facts(original)
    rewrite_facts = extract_facts(rewrite)
    
    if not original_facts:
        return FidelityResult(
            task_id=task_id,
            condition=condition,
            score=1.0,
            facts_preserved=0,
            facts_total=0,
            details={"note": "No facts in original"}
        )
    
    # Count preserved facts
    original_set = set(original_facts)
    rewrite_set = set(rewrite_facts)
    
    preserved = original_set.intersection(rewrite_set)
    facts_preserved = len(preserved)
    facts_total = len(original_set)
    
    score = facts_preserved / facts_total if facts_total > 0 else 1.0
    
    return FidelityResult(
        task_id=task_id,
        condition=condition,
        score=score,
        facts_preserved=facts_preserved,
        facts_total=facts_total,
        details={
            "original_facts": original_facts,
            "rewrite_facts": rewrite_facts,
            "preserved": list(preserved)
        }
    )


def score_task(task_dir: Path, condition: str) -> FidelityResult:
    """Score a single task directory.
    
    Args:
        task_dir: Path to task directory
        condition: Evaluation condition name
        
    Returns:
        FidelityResult for the task
    """
    task_id = task_dir.name
    
    original_path = task_dir / "original.md"
    rewrite_path = task_dir / f"rewrite_{condition}.md"
    
    if not original_path.exists():
        return FidelityResult(
            task_id=task_id,
            condition=condition,
            score=0.0,
            facts_preserved=0,
            facts_total=0,
            details={"error": "original.md not found"}
        )
    
    if not rewrite_path.exists():
        return FidelityResult(
            task_id=task_id,
            condition=condition,
            score=0.0,
            facts_preserved=0,
            facts_total=0,
            details={"error": f"rewrite_{condition}.md not found"}
        )
    
    original_text = original_path.read_text(encoding='utf-8')
    rewrite_text = rewrite_path.read_text(encoding='utf-8')
    
    return calculate_fidelity(original_text, rewrite_text, task_id, condition)


def score_all_tasks(
    tasks_dir: Path,
    condition: str
) -> List[FidelityResult]:
    """Score all tasks in a directory.
    
    Args:
        tasks_dir: Path to tasks directory
        condition: Evaluation condition name
        
    Returns:
        List of FidelityResult for all tasks
    """
    results: List[FidelityResult] = []
    
    for task_dir in sorted(tasks_dir.iterdir()):
        if task_dir.is_dir() and not task_dir.name.startswith('.'):
            result = score_task(task_dir, condition)
            results.append(result)
    
    return results


def aggregate_scores(results: List[FidelityResult]) -> Dict[str, Any]:
    """Aggregate scores across all results.
    
    Args:
        results: List of FidelityResult
        
    Returns:
        Dictionary with aggregate statistics
    """
    if not results:
        return {"mean": 0.0, "min": 0.0, "max": 0.0, "count": 0}
    
    scores = [r.score for r in results]
    
    return {
        "mean": sum(scores) / len(scores),
        "min": min(scores),
        "max": max(scores),
        "count": len(scores),
    }


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point.
    
    Args:
        argv: Command line arguments
        
    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(
        description="Score round-trip transmission fidelity"
    )
    parser.add_argument(
        "tasks_dir",
        type=Path,
        help="Directory containing task subdirectories"
    )
    parser.add_argument(
        "--condition",
        type=str,
        default="baseline",
        help="Evaluation condition to score (default: baseline)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON file (default: stdout)"
    )
    
    args = parser.parse_args(argv)
    
    if not args.tasks_dir.exists():
        print(f"Error: {args.tasks_dir} does not exist", file=sys.stderr)
        return 1
    
    results = score_all_tasks(args.tasks_dir, args.condition)
    aggregate = aggregate_scores(results)
    
    output_data = {
        "condition": args.condition,
        "results": [r.to_dict() for r in results],
        "aggregate": aggregate,
    }
    
    output_json = json.dumps(output_data, indent=2)
    
    if args.output:
        args.output.write_text(output_json, encoding='utf-8')
        print(f"Results written to {args.output}")
    else:
        print(output_json)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
