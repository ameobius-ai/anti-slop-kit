"""Visualization utilities for eval harness.

Generates plots and charts for eval results.
Part of issue #23: Enhance eval harness with visualization.
"""

from typing import List, Dict
from pathlib import Path


def generate_bar_chart(
    conditions: Dict[str, List[float]],
    output_path: str = "eval_bar_chart.png",
    title: str = "Mean Fidelity Score by Condition"
):
    """Generate bar chart showing mean scores by condition."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("Warning: matplotlib not available, skipping chart generation")
        return
    
    names = []
    means = []
    errors = []
    
    for name, scores in conditions.items():
        if scores:
            names.append(name)
            m = sum(scores) / len(scores)
            means.append(m)
            if len(scores) > 1:
                std = (sum((x - m)**2 for x in scores) / (len(scores) - 1)) ** 0.5
                errors.append(std / (len(scores) ** 0.5))
            else:
                errors.append(0)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x_pos = np.arange(len(names))
    bars = ax.bar(x_pos, means, yerr=errors, capsize=5, alpha=0.7)
    
    ax.set_xlabel("Condition")
    ax.set_ylabel("Mean Fidelity Score")
    ax.set_title(title)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)
    
    for bar, m in zip(bars, means):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{m:.3f}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Bar chart saved to {output_path}")
    plt.close()


def generate_box_plot(
    conditions: Dict[str, List[float]],
    output_path: str = "eval_box_plot.png",
    title: str = "Score Distribution by Condition"
):
    """Generate box plot showing score distributions."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Warning: matplotlib not available, skipping chart generation")
        return
    
    names = []
    data = []
    
    for name, scores in conditions.items():
        if scores:
            names.append(name)
            data.append(scores)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bp = ax.boxplot(data, labels=names, patch_artist=True)
    
    colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC']
    for patch, color in zip(bp['boxes'], colors[:len(names)]):
        patch.set_facecolor(color)
    
    ax.set_xlabel("Condition")
    ax.set_ylabel("Fidelity Score")
    ax.set_title(title)
    ax.grid(axis='y', alpha=0.3)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Box plot saved to {output_path}")
    plt.close()


def generate_all_charts(
    conditions: Dict[str, List[float]],
    output_dir: str = "evals/charts"
):
    """Generate all visualization charts."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("\nGenerating visualizations...")
    
    generate_bar_chart(
        conditions,
        str(output_path / "bar_chart.png"),
        "Mean Fidelity Score by Condition"
    )
    
    generate_box_plot(
        conditions,
        str(output_path / "box_plot.png"),
        "Score Distribution by Condition"
    )
    
    print(f"✓ All charts saved to {output_dir}/")
