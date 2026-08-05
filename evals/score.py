#!/usr/bin/env python3
"""Score eval tasks for fact preservation and task-type aggregates.

Proof sources:
- User-provided previous session artifact: task directories contain source.md,
  rewritten.md, metadata.json; metadata fields task_type/population are required.
- Local Python stdlib behavior: json, pathlib, re, argparse.

Environment-dependent values:
- DEFAULT_TASKS_DIR assumes repo layout evals/tasks/<task-id>/.
- MAX_FILE_BYTES is a corruption guard; tune if fixtures grow.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_TASKS_DIR = Path("evals/tasks")

# Bound external input. A corrupted or oversized fixture must cost a rejected
# operation, not a hang or memory blowup.
MAX_TASKS = 10_000
MAX_FILE_BYTES = 5 * 1024 * 1024

# Keep JSON output bounded. Full missing-fact debugging can be done by lowering
# this locally; do not emit unbounded lists into CI artifacts.
MISSING_FACT_REPORT_LIMIT = 200

# Fact patterns are intentionally lexical, not semantic. This scorer measures
# whether machine-checkable atoms survived the rewrite: endpoints, timestamps,
# paths, header names, HTTP error classes, and numeric constraints.
_METHOD_PATH = r"\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/[A-Za-z0-9_\-./{}%]+"
_TIMESTAMP = r"\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?(?:\s*UTC)?"
_PATH = r"/[A-Za-z0-9_\-./{}%]+"
_HEADER = r"\b[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+\b"
_ERROR_CLASS = r"\b[1-5]xx\b"
_NUMBER = r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?%?\b|\b\d+%?\b"

_TOKEN_RE = re.compile(
    rf"(?P<endpoint>{_METHOD_PATH})"
    rf"|(?P<timestamp>{_TIMESTAMP})"
    rf"|(?P<path>{_PATH})"
    rf"|(?P<header>{_HEADER})"
    rf"|(?P<errorclass>{_ERROR_CLASS})"
    rf"|(?P<number>{_NUMBER})",
    re.IGNORECASE,
)


def _canonical_number(raw: str) -> str:
    value = raw.strip().lower()

    # Preserve percent semantics; 1% and 1 are different constraints.
    percent = "%" if value.endswith("%") else ""
    if percent:
        value = value[:-1]

    # Treat 1,247 and 1247 as the same fact.
    value = value.replace(",", "")
    return f"{value}{percent}"


def _canonical_timestamp(raw: str) -> str:
    value = raw.strip().lower().replace("t", " ")

    # "2024-11-15 02:00 UTC" and "2024-11-15 02:00" should compare equal.
    if value.endswith(" utc"):
        value = value[:-4]

    return re.sub(r"\s+", " ", value).strip()


def _canonical_token(kind: str, raw: str) -> str:
    value = raw.strip()

    if kind == "number":
        value = _canonical_number(value)
    elif kind == "timestamp":
        value = _canonical_timestamp(value)
    else:
        value = value.lower()
        value = re.sub(r"\s+", " ", value).strip()
        value = value.rstrip(".,;:")

    return f"{kind}:{value}"


def extract_facts(text: str):
    facts = set()

    for match in _TOKEN_RE.finditer(text):
        kind = match.lastgroup or "token"
        raw = match.group(0)
        if not raw:
            continue
        facts.add(_canonical_token(kind, raw))

    return facts


def read_text_guarded(path: Path) -> Tuple[Optional[str], Optional[str]]:
    try:
        if not path.exists():
            return None, f"missing_file:{path.name}"

        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            return None, f"file_too_large:{path.name}"

        return path.read_text(encoding="utf-8"), None
    except OSError as exc:
        return None, f"os_error:{exc.__class__.__name__}"
    except UnicodeDecodeError:
        return None, "utf8_decode_error"


def load_metadata(path: Path) -> Tuple[Dict[str, Any], Optional[str]]:
    text, error = read_text_guarded(path)
    if error is not None:
        return {}, error

    try:
        data = json.loads(text or "")
    except json.JSONDecodeError as exc:
        return {}, f"metadata_json_error:{exc.msg}"

    if not isinstance(data, dict):
        return {}, "metadata_not_object"

    return data, None


@dataclass
class TaskResult:
    task_id: str
    task_type: str = "unknown"
    population: str = "unknown"
    fidelity_score: float = 0.0
    source_fact_count: int = 0
    matched_fact_count: int = 0
    missing_fact_count: int = 0
    missing_facts: List[str] = field(default_factory=list)
    error: Optional[str] = None
    metadata_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "population": self.population,
            "fidelity_score": self.fidelity_score,
            "source_fact_count": self.source_fact_count,
            "matched_fact_count": self.matched_fact_count,
            "missing_fact_count": self.missing_fact_count,
            "missing_facts": self.missing_facts,
            "error": self.error,
            "metadata_error": self.metadata_error,
        }


def score_task(task_dir: Path) -> Dict[str, Any]:
    result = TaskResult(task_id=task_dir.name)

    if not task_dir.is_dir():
        result.error = "not_a_directory"
        return result.to_dict()

    metadata, metadata_error = load_metadata(task_dir / "metadata.json")

    if metadata:
        result.task_type = str(metadata.get("task_type", "unknown"))
        result.population = str(metadata.get("population", "unknown"))

    # Older tasks may lack metadata.json; that is unknown, not fatal.
    # Corrupt metadata is surfaced separately.
    if metadata_error is not None and not metadata_error.startswith("missing_file:"):
        result.metadata_error = metadata_error

    source_text, source_error = read_text_guarded(task_dir / "source.md")
    rewritten_text, rewritten_error = read_text_guarded(task_dir / "rewritten.md")

    if source_error is not None or rewritten_error is not None:
        result.error = source_error if source_error is not None else rewritten_error
        return result.to_dict()

    source_facts = extract_facts(source_text or "")
    rewritten_facts = extract_facts(rewritten_text or "")

    if not source_facts:
        result.error = "no_source_facts_extracted"
        return result.to_dict()

    matched = source_facts.intersection(rewritten_facts)
    missing = sorted(source_facts - matched)

    result.source_fact_count = len(source_facts)
    result.matched_fact_count = len(matched)
    result.missing_fact_count = len(missing)
    result.missing_facts = missing[:MISSING_FACT_REPORT_LIMIT]
    result.fidelity_score = round(result.matched_fact_count / result.source_fact_count, 4)

    return result.to_dict()


def _aggregate(results: List[Dict[str, Any]], key: str) -> Dict[str, Any]:
    groups: Dict[str, List[float]] = {}

    for row in results:
        group_key = str(row.get(key, "unknown") or "unknown")
        groups.setdefault(group_key, []).append(float(row.get("fidelity_score", 0.0)))

    aggregated = {}
    for group_key in sorted(groups):
        scores = groups[group_key]
        aggregated[group_key] = {
            "aggregate_fidelity": round(sum(scores) / len(scores), 4),
            "task_count": len(scores),
        }

    return aggregated


def score_all(tasks_dir: Path, task_filter: Optional[str] = None) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tasks_dir": str(tasks_dir),
        "truncated": False,
        "task_count": 0,
        "aggregate_fidelity": 0.0,
        "by_task_type": {},
        "by_population": {},
        "results": [],
    }

    if not tasks_dir.exists() or not tasks_dir.is_dir():
        summary["error"] = f"tasks_dir_missing:{tasks_dir}"
        return summary

    task_dirs = []
    truncated = False

    for path in sorted(tasks_dir.iterdir()):
        if not path.is_dir():
            continue

        if task_filter is not None and path.name != task_filter:
            continue

        task_dirs.append(path)

        if len(task_dirs) >= MAX_TASKS:
            truncated = True
            break

    results = [score_task(path) for path in task_dirs]

    aggregate_fidelity = 0.0
    if results:
        aggregate_fidelity = round(
            sum(row["fidelity_score"] for row in results) / len(results),
            4,
        )

    summary.update(
        {
            "truncated": truncated,
            "task_count": len(results),
            "aggregate_fidelity": aggregate_fidelity,
            "by_task_type": _aggregate(results, "task_type"),
            "by_population": _aggregate(results, "population"),
            "results": results,
        }
    )

    if not results:
        summary["error"] = "no_tasks_found"

    return summary


def _md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Eval results",
        "",
        f"Generated: {summary.get('generated_at', 'unknown')}",
        f"Tasks dir: {summary.get('tasks_dir', 'unknown')}",
    ]

    if summary.get("error"):
        lines.append(f"Error: {summary['error']}")

    lines.append(
        "Aggregate fidelity: "
        f"{summary.get('aggregate_fidelity', 0.0)} "
        f"across {summary.get('task_count', 0)} tasks"
    )

    lines.extend(
        [
            "",
            "## By task type",
            "",
            "| task_type | aggregate_fidelity | task_count |",
            "|---|---:|---:|",
        ]
    )

    for key, value in (summary.get("by_task_type") or {}).items():
        lines.append(
            f"| {_md_escape(key)} "
            f"| {value['aggregate_fidelity']} "
            f"| {value['task_count']} |"
        )

    lines.extend(
        [
            "",
            "## By population",
            "",
            "| population | aggregate_fidelity | task_count |",
            "|---|---:|---:|",
        ]
    )

    for key, value in (summary.get("by_population") or {}).items():
        lines.append(
            f"| {_md_escape(key)} "
            f"| {value['aggregate_fidelity']} "
            f"| {value['task_count']} |"
        )

    lines.extend(
        [
            "",
            "## Tasks",
            "",
            "| task | type | population | fidelity | missing | error |",
            "|---|---|---|---:|---:|---|",
        ]
    )

    for row in summary.get("results", []):
        error = row.get("error") or row.get("metadata_error") or ""
        lines.append(
            f"| {_md_escape(row['task_id'])} "
            f"| {_md_escape(row['task_type'])} "
            f"| {_md_escape(row['population'])} "
            f"| {row['fidelity_score']} "
            f"| {row['missing_fact_count']} "
            f"| {_md_escape(error)} |"
        )

    return "\n".join(lines) + "\n"


def _write_output(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Score anti-slop eval tasks for fact preservation."
    )
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=DEFAULT_TASKS_DIR,
        help="Path to evals/tasks directory.",
    )
    parser.add_argument(
        "--task",
        help="Score only one task directory name, e.g. en-16.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Write full JSON summary to this path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        help="Write Markdown summary to this path.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any task has an error or metadata error.",
    )

    args = parser.parse_args(argv)

    summary = score_all(args.tasks_dir, args.task)

    if args.json_out is not None:
        _write_output(
            args.json_out,
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        )

    if args.markdown_out is not None:
        _write_output(args.markdown_out, render_markdown(summary))

    if args.json_out is None and args.markdown_out is None:
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    error = str(summary.get("error", ""))
    if error.startswith("tasks_dir_missing") or summary.get("task_count", 0) == 0:
        return 2

    if args.strict and any(
        row.get("error") or row.get("metadata_error")
        for row in summary.get("results", [])
    ):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
