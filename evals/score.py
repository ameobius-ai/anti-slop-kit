#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.transmit_check import transmit_check

TASKS_DIR = Path(__file__).parent / "tasks"

def score_task(task_dir):
    task_id = task_dir.name
    source_path = task_dir / "source.md"
    rewritten_path = task_dir / "rewritten.md"
    if not source_path.exists():
        return {"task": task_id, "error": "source.md missing", "fidelity_score": 0.0}
    source = source_path.read_text(encoding="utf-8")
    rewritten = rewritten_path.read_text(encoding="utf-8") if rewritten_path.exists() else source
    result = transmit_check(source, rewritten)
    result["task"] = task_id
    result["rewritten_provided"] = rewritten_path.exists()
    return result

def main():
    results = []
    for task_dir in sorted(TASKS_DIR.iterdir()):
        if task_dir.is_dir():
            results.append(score_task(task_dir))
    scored = [r for r in results if "error" not in r]
    if scored:
        avg = sum(r["fidelity_score"] for r in scored) / len(scored)
        print(f"Aggregate fidelity: {avg:.4f}")
        print(f"Tasks scored: {len(scored)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
