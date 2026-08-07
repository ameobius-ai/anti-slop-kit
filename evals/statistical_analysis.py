"""Statistical analysis utilities for eval harness.

Provides confidence intervals, effect sizes, and statistical tests.
Part of issue #23: Enhance eval harness with statistical analysis.
"""

import math
from typing import List, Tuple, Dict, Union, Any
# Import standard library statistics module (not this file)
import statistics as stdlib_statistics


def confidence_interval(
    data: List[float],
    confidence: float = 0.95
) -> Tuple[float, float, float]:
    """Calculate confidence interval for mean.
    
    Args:
        data: List of numeric values
        confidence: Confidence level (0.95 for 95% CI)
    
    Returns:
        Tuple of (mean, lower_bound, upper_bound)
    """
    if not data:
        return (0.0, 0.0, 0.0)
    
    if len(data) == 1:
        return (data[0], data[0], data[0])
    
    n = len(data)
    m = stdlib_statistics.mean(data)
    se = stdlib_statistics.stdev(data) / math.sqrt(n)
    
    if n > 30:
        z = 1.96
    else:
        z = 2.0 + (2.0 / n)
    
    margin = z * se
    lower = m - margin
    upper = m + margin
    
    return (m, lower, upper)


def cohens_d(group1: List[float], group2: List[float]) -> float:
    """Calculate Cohen's d effect size between two groups.
    
    Interpretation:
    - d = 0.2: small effect
    - d = 0.5: medium effect
    - d = 0.8: large effect
    """
    if not group1 or not group2:
        return 0.0
    
    m1 = stdlib_statistics.mean(group1)
    m2 = stdlib_statistics.mean(group2)
    
    n1 = len(group1)
    n2 = len(group2)
    
    if n1 == 1 or n2 == 1:
        return 0.0
    
    var1 = stdlib_statistics.stdev(group1) ** 2
    var2 = stdlib_statistics.stdev(group2) ** 2
    
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (m1 - m2) / pooled_std


def bootstrap_confidence_interval(
    data: List[float],
    n_bootstrap: int = 1000,
    confidence: float = 0.95
) -> Tuple[float, float, float]:
    """Calculate bootstrap confidence interval for mean."""
    if not data:
        return (0.0, 0.0, 0.0)
    
    import random
    
    n = len(data)
    bootstrap_means = []
    
    for _ in range(n_bootstrap):
        sample = [random.choice(data) for _ in range(n)]
        bootstrap_means.append(stdlib_statistics.mean(sample))
    
    bootstrap_means.sort()
    
    lower_idx = int((1 - confidence) / 2 * n_bootstrap)
    upper_idx = int((1 + confidence) / 2 * n_bootstrap)
    
    m = stdlib_statistics.mean(data)
    lower = bootstrap_means[lower_idx]
    upper = bootstrap_means[upper_idx]
    
    return (m, lower, upper)


def analyze_condition(
    scores: List[float],
    condition_name: str
) -> Dict[str, Any]:
    """Analyze a single condition's scores."""
    if not scores:
        return {
            "condition": condition_name,
            "n": 0,
            "mean": 0.0,
            "std": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
        }
    
    m, ci_lower, ci_upper = confidence_interval(scores, confidence=0.95)
    
    return {
        "condition": condition_name,
        "n": len(scores),
        "mean": round(m, 4),
        "std": round(stdlib_statistics.stdev(scores), 4) if len(scores) > 1 else 0.0,
        "ci_lower": round(ci_lower, 4),
        "ci_upper": round(ci_upper, 4),
        "min": round(min(scores), 4),
        "max": round(max(scores), 4),
    }


def compare_conditions(
    group1: List[float],
    group2: List[float],
    name1: str,
    name2: str
) -> Dict[str, Any]:
    """Compare two conditions statistically."""
    if not group1 or not group2:
        return {
            "comparison": f"{name1} vs {name2}",
            "n1": len(group1),
            "n2": len(group2),
            "cohens_d": 0.0,
            "effect_size": "none",
        }
    
    d = cohens_d(group1, group2)
    
    abs_d = abs(d)
    if abs_d < 0.2:
        effect_size = "negligible"
    elif abs_d < 0.5:
        effect_size = "small"
    elif abs_d < 0.8:
        effect_size = "medium"
    else:
        effect_size = "large"
    
    return {
        "comparison": f"{name1} vs {name2}",
        "n1": len(group1),
        "n2": len(group2),
        "mean1": round(stdlib_statistics.mean(group1), 4),
        "mean2": round(stdlib_statistics.mean(group2), 4),
        "mean_diff": round(stdlib_statistics.mean(group1) - stdlib_statistics.mean(group2), 4),
        "cohens_d": round(d, 4),
        "effect_size": effect_size,
    }


def print_analysis_report(conditions: Dict[str, List[float]]):
    """Print a complete statistical analysis report."""
    print("=" * 80)
    print("STATISTICAL ANALYSIS REPORT")
    print("=" * 80)
    
    print("\n1. Condition Analysis:")
    print("-" * 80)
    
    for name, scores in conditions.items():
        analysis = analyze_condition(scores, name)
        
        print(f"\n{name}:")
        print(f"  N: {analysis['n']}")
        print(f"  Mean: {analysis['mean']:.4f} +/- {analysis['std']:.4f}")
        print(f"  95% CI: [{analysis['ci_lower']:.4f}, {analysis['ci_upper']:.4f}]")
        print(f"  Range: [{analysis['min']:.4f}, {analysis['max']:.4f}]")
    
    print("\n2. Pairwise Comparisons:")
    print("-" * 80)
    
    condition_names = list(conditions.keys())
    for i in range(len(condition_names)):
        for j in range(i + 1, len(condition_names)):
            name1 = condition_names[i]
            name2 = condition_names[j]
            
            comparison = compare_conditions(
                conditions[name1],
                conditions[name2],
                name1,
                name2
            )
            
            print(f"\n{comparison['comparison']}:")
            print(f"  Mean difference: {comparison['mean_diff']:.4f}")
            print(f"  Cohen's d: {comparison['cohens_d']:.4f} ({comparison['effect_size']})")
    
    print("\n" + "=" * 80)
