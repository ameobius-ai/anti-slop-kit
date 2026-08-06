#!/usr/bin/env python3
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

API = "https://api.github.com"

TRACKER_MARKER = "<!-- autonomous-maintainer-tracker -->"
BLOCKER_MARKER = "<!-- autonomous-blocker:pr:{} -->"
INFRA_MARKER = "<!-- autonomous-infra-task:{} -->"
PR_COMMENT_MARKER = "<!-- autonomous-pr-status:{} -->"

DEFAULT_CONFIG = {
    "target_pulls": [106],
    "auto_merge_green_prs": True,
    "max_new_issues_per_run": 5,
    "default_branch": None,
}

CATALOG = [
    {"key": "docs", "title": "MkDocs documentation site", "paths": ["mkdocs.yml", "docs/index.md", ".github/workflows/docs.yml"]},
    {"key": "devcontainer", "title": "DevContainer / Codespaces environment", "paths": [".devcontainer/devcontainer.json"]},
    {"key": "strict_typing", "title": "Mypy strict type checking workflow", "paths": [".github/workflows/mypy.yml"]},
    {"key": "supply_chain", "title": "OpenSSF Scorecard workflow", "paths": [".github/workflows/scorecard.yml"]},
    {"key": "stale_bot", "title": "Stale issues/PRs workflow", "paths": [".github/workflows/stale.yml"]},
    {"key": "dependabot", "title": "Dependabot configuration", "paths": [".github/dependabot.yml"]},
    {"key": "commitlint", "title": "Conventional commit enforcement", "paths": [".github/workflows/commitlint.yml", ".commitlintrc.json"]},
    {"key": "release_drafter", "title": "Release Drafter automation", "paths": [".github/release-drafter.yml", ".github/workflows/release-drafter.yml"]},
    {"key": "precommit_mirror", "title": "Pre-commit hook mirror manifest", "paths": [".pre-commit-hooks.yaml"]},
    {"key": "docker", "title": "Docker support", "paths": ["Dockerfile", ".dockerignore"]},
    {"key": "cli_entrypoints", "title": "CLI entry points in pyproject.toml", "paths": [], "file_contains": {"path": "pyproject.toml", "needle": "[project.scripts]"}},
]

class ApiError(Exception):
    def __init__(self, code, method, path, body):
        self.code = code
        self.method = method
        self.path = path
        self.body = body
        super().__init__(f"HTTP {code} {method} {path}: {body[:500]}")

def gh_api(method: str, path: str, token: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = path if path.startswith("http") else f"{API}/{path.lstrip('/')}"
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    last_error = None
    for attempt in range(3):
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        if body is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8", "replace")
                if not raw: return {}
                try: return json.loads(raw)
                except json.JSONDecodeError: return {"raw": raw[:2000]}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            last_error = ApiError(exc.code, method, path, raw)
            if exc.code in (500, 502, 503, 504):
                time.sleep(2 ** attempt); continue
            if exc.code == 403 and "rate limit" in raw.lower():
                time.sleep(5 * (attempt + 1)); continue
            raise last_error
        except Exception as exc:
            last_error = exc
            if attempt == 2: raise
            time.sleep(2 ** attempt)
    if last_error is not None: raise last_error
    raise RuntimeError("unreachable")

def load_config() -> Dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(".autonomous/config.json", encoding="utf-8") as fh:
            user_cfg = json.load(fh)
            if isinstance(user_cfg, dict): cfg.update(user_cfg)
    except Exception: pass
    if not cfg.get("default_branch"): cfg["default_branch"] = None
    return cfg

def ensure_label(repo: str, token: str, name: str, color: str, description: str) -> None:
    quoted = urllib.parse.quote(name, safe="")
    try:
        gh_api("GET", f"repos/{repo}/labels/{quoted}", token); return
    except ApiError as exc:
        if exc.code != 404: return
    try:
        gh_api("POST", f"repos/{repo}/labels", token, {"name": name, "color": color, "description": description})
    except ApiError: pass

def ensure_labels(repo: str, token: str) -> None:
    ensure_label(repo, token, "autonomous", "0E8A16", "Managed by autonomous maintainer")
    ensure_label(repo, token, "blocker", "D93F0B", "Blocks delivery")
    ensure_label(repo, token, "infrastructure", "1D76DB", "Repository infrastructure")

def find_by_marker(items: List[Dict[str, Any]], marker: str) -> Optional[Dict[str, Any]]:
    for item in items:
        body = item.get("body") or ""
        if marker in body: return item
    return None

def create_issue(repo: str, token: str, title: str, body: str, labels: Optional[List[str]] = None) -> Dict[str, Any]:
    payload = {"title": title, "body": body}
    if labels: payload["labels"] = labels
    try: return gh_api("POST", f"repos/{repo}/issues", token, payload)
    except ApiError as exc:
        if exc.code == 422 and labels:
            payload.pop("labels", None)
            return gh_api("POST", f"repos/{repo}/issues", token, payload)
        raise

def upsert_issue(repo: str, token: str, marker: str, title: str, body: str, labels: Optional[List[str]], open_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    issue = find_by_marker(open_issues, marker)
    if issue:
        return gh_api("PATCH", f"repos/{repo}/issues/{issue['number']}", token, {"title": title, "body": body, "state": "open"})
    return create_issue(repo, token, title, body, labels)

def close_issue_by_marker(repo: str, token: str, marker: str, open_issues: List[Dict[str, Any]]) -> None:
    issue = find_by_marker(open_issues, marker)
    if not issue: return
    if issue.get("state") != "open": return
    gh_api("PATCH", f"repos/{repo}/issues/{issue['number']}", token, {"state": "closed", "state_reason": "completed"})

def upsert_comment(repo: str, token: str, number: int, marker: str, body: str) -> Dict[str, Any]:
    comments = gh_api("GET", f"repos/{repo}/issues/{number}/comments?per_page=100", token)
    if isinstance(comments, list):
        for comment in comments:
            if marker in (comment.get("body") or ""):
                return gh_api("PATCH", f"repos/{repo}/issues/comments/{comment['id']}", token, {"body": body})
    return gh_api("POST", f"repos/{repo}/issues/{number}/comments", token, {"body": body})

def fetch_file_text(repo: str, token: str, branch: str, path: str) -> Optional[str]:
    quoted = urllib.parse.quote(path, safe="/")
    try:
        data = gh_api("GET", f"repos/{repo}/contents/{quoted}?ref={urllib.parse.quote(branch, safe='')}", token)
    except ApiError as exc:
        if exc.code == 404: return None
        raise
    content = data.get("content") or ""
    encoding = data.get("encoding")
    if encoding == "base64": return base64.b64decode(content).decode("utf-8", "replace")
    return content

def commit_health(repo: str, token: str, sha: str) -> Tuple[str, List[str]]:
    details = []; pending = 0; green = 0; red = 0
    check_runs = gh_api("GET", f"repos/{repo}/commits/{sha}/check-runs?per_page=100", token).get("check_runs", [])
    for run in check_runs:
        name = run.get("name") or "unknown"
        status = run.get("status") or "unknown"
        conclusion = run.get("conclusion") or "unknown"
        details.append(f"check: {name} status={status} conclusion={conclusion}")
        if status != "completed": pending += 1
        elif conclusion in ("success", "neutral", "skipped"): green += 1
        else: red += 1
    statuses = gh_api("GET", f"repos/{repo}/commits/{sha}/status", token).get("statuses", [])
    for status in statuses:
        context = status.get("context") or "unknown"
        state = status.get("state") or "unknown"
        details.append(f"status: {context} state={state}")
        if state == "pending": pending += 1
        elif state == "success": green += 1
        else: red += 1
    if red: classification = "red"
    elif pending: classification = "pending"
    elif green: classification = "green"
    else: classification = "unknown"
    return classification, details[:100]

def pr_comment_body(pr_number: int, classification: str, mergeable_state: str, details: List[str], action: str) -> str:
    marker = PR_COMMENT_MARKER.format(pr_number)
    lines = [marker, "Autonomous maintainer status.", "", f"classification: `{classification}`", f"mergeable_state: `{mergeable_state}`", f"action: `{action}`", ""]
    if details: lines.append("Details:"); lines.extend([f"- {item}" for item in details])
    else: lines.append("Details: none")
    lines.append(""); lines.append("Fail-closed rule: merge only when checks and mergeability are green.")
    return "\n".join(lines)

def blocker_body(pr_number: int, classification: str, mergeable_state: str, details: List[str], action: str) -> str:
    marker = BLOCKER_MARKER.format(pr_number)
    lines = [marker, f"PR #{pr_number} is blocked.", "", f"classification: `{classification}`", f"mergeable_state: `{mergeable_state}`", f"action: `{action}`", ""]
    if details: lines.append("Details:"); lines.extend([f"- {item}" for item in details])
    else: lines.append("Details: none")
    lines.append(""); lines.append("Close this issue after the blocker is resolved. The maintainer will recreate it if the blocker returns.")
    return "\n".join(lines)

def create_or_update_blocker(repo: str, token: str, pr_number: int, classification: str, mergeable_state: str, details: List[str], action: str, open_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    marker = BLOCKER_MARKER.format(pr_number)
    title = f"Blocker: PR #{pr_number} requires attention"
    body = blocker_body(pr_number, classification, mergeable_state, details, action)
    return upsert_issue(repo, token, marker, title, body, ["blocker", "autonomous"], open_issues)

def process_pr(repo: str, token: str, pr_number: int, cfg: Dict[str, Any], open_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    row = {"pr": pr_number, "state": "missing", "classification": "missing", "action": "none"}
    try: pr = gh_api("GET", f"repos/{repo}/pulls/{pr_number}", token)
    except ApiError as exc:
        if exc.code == 404: close_issue_by_marker(repo, token, BLOCKER_MARKER.format(pr_number), open_issues); return row
        raise
    if pr.get("merged_at"): state = "merged"
    else: state = pr.get("state") or "unknown"
    row["state"] = state
    if state != "open":
        classification = "merged" if state == "merged" else "closed"
        row["classification"] = classification; row["action"] = "none"
        close_issue_by_marker(repo, token, BLOCKER_MARKER.format(pr_number), open_issues)
        upsert_comment(repo, token, pr_number, PR_COMMENT_MARKER.format(pr_number), pr_comment_body(pr_number, classification, pr.get("mergeable_state") or "unknown", [], "none"))
        return row
    mergeable_state = pr.get("mergeable_state") or "unknown"
    sha = (pr.get("head") or {}).get("sha")
    if not sha: health = "unknown"; details = ["No head SHA found"]
    else:
        try: health, details = commit_health(repo, token, sha)
        except ApiError as exc: health = "unknown"; details = [f"Failed to fetch checks: {exc}"]
    if mergeable_state == "dirty": classification = "conflict"
    elif mergeable_state == "blocked": classification = "blocked"
    elif health == "red": classification = "red"
    elif health == "pending": classification = "pending"
    elif health == "green": classification = "green"
    else: classification = "unknown"
    action = "none"
    if classification == "green" and cfg.get("auto_merge_green_prs") and mergeable_state == "clean":
        try:
            gh_api("PUT", f"repos/{repo}/pulls/{pr_number}/merge", token, {"merge_method": "squash"})
            classification = "merged"; state = "merged"; action = "merged"
        except ApiError as exc: classification = "merge_failed"; action = "merge_failed"; details.append(f"merge failed: {exc}")
    row["state"] = state; row["classification"] = classification; row["action"] = action
    upsert_comment(repo, token, pr_number, PR_COMMENT_MARKER.format(pr_number), pr_comment_body(pr_number, classification, mergeable_state, details, action))
    if classification in ("red", "conflict", "blocked", "merge_failed", "unknown"):
        create_or_update_blocker(repo, token, pr_number, classification, mergeable_state, details, action, open_issues)
    else: close_issue_by_marker(repo, token, BLOCKER_MARKER.format(pr_number), open_issues)
    return row

def missing_infrastructure(repo: str, token: str, branch: str) -> List[Dict[str, Any]]:
    tree = gh_api("GET", f"repos/{repo}/git/trees/{urllib.parse.quote(branch, safe='')}?recursive=1", token)
    paths = set()
    for item in tree.get("tree", []):
        if item.get("type") == "blob": paths.add(item.get("path"))
    missing = []
    for item in CATALOG:
        required_paths = item.get("paths", [])
        if any(path not in paths for path in required_paths): missing.append(item); continue
        contains = item.get("file_contains")
        if not contains: continue
        text = fetch_file_text(repo, token, branch, contains["path"])
        if text is None or contains["needle"] not in text: missing.append(item)
    return missing

def infra_issue_body(item: Dict[str, Any], branch: str) -> str:
    marker = INFRA_MARKER.format(item["key"])
    lines = [marker, f"Missing infrastructure: {item['title']}", "", f"Autonomous research detected this on default branch `{branch}`.", "", "Expected artifacts:"]
    for path in item.get("paths", []): lines.append(f"- `{path}`")
    contains = item.get("file_contains")
    if contains: lines.append(f"- `{contains['path']}` must contain `{contains['needle']}`")
    lines.extend(["", "Acceptance criteria:", "- Add the missing artifacts.", "- Keep CI green.", "- Do not weaken existing security or test gates."])
    return "\n".join(lines)

def create_infra_issues(repo: str, token: str, missing: List[Dict[str, Any]], open_issues: List[Dict[str, Any]], branch: str, max_new: int) -> List[Dict[str, Any]]:
    created = []
    for item in missing:
        if len(created) >= max_new: break
        marker = INFRA_MARKER.format(item["key"])
        if find_by_marker(open_issues, marker): continue
        issue = create_issue(repo, token, f"Infra: add {item['title']}", infra_issue_body(item, branch), ["infrastructure", "autonomous"])
        created.append(issue)
    return created

def tracker_body(pr_rows: List[Dict[str, Any]], missing: List[Dict[str, Any]], created_issues: List[Dict[str, Any]], branch: str) -> str:
    now = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    lines = [TRACKER_MARKER, f"Last autonomous run: {now}", f"Default branch: `{branch}`", "", "## Target PRs", "", "| PR | state | classification | action |", "| ---: | --- | --- | --- |"]
    if pr_rows:
        for row in pr_rows: lines.append(f"| #{row['pr']} | {row['state']} | {row['classification']} | {row['action']} |")
    else: lines.append("| - | - | no target PRs configured | - |")
    lines.extend(["", "## Missing infrastructure", ""])
    if missing:
        for item in missing: lines.append(f"- {item['title']} (`{item['key']}`)")
    else: lines.append("- none detected")
    lines.extend(["", "## Issues created in this run", ""])
    if created_issues:
        for issue in created_issues: lines.append(f"- #{issue.get('number')} {issue.get('title')}")
    else: lines.append("- none")
    lines.extend(["", "This issue is maintained automatically.", "Do not remove the marker comment."])
    return "\n".join(lines)

def create_or_update_tracker(repo: str, token: str, pr_rows: List[Dict[str, Any]], missing: List[Dict[str, Any]], created_issues: List[Dict[str, Any]], open_issues: List[Dict[str, Any]], branch: str) -> Dict[str, Any]:
    title = "Autonomous task tracker"
    body = tracker_body(pr_rows, missing, created_issues, branch)
    issue = find_by_marker(open_issues, TRACKER_MARKER)
    if issue:
        return gh_api("PATCH", f"repos/{repo}/issues/{issue['number']}", token, {"title": title, "body": body, "state": "open"})
    return create_issue(repo, token, title, body, ["autonomous"])

def main() -> int:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("GITHUB_TOKEN/GH_TOKEN and GITHUB_REPOSITORY are required", file=sys.stderr); return 1
    cfg = load_config()
    ensure_labels(repo, token)
    repo_info = gh_api("GET", f"repos/{repo}", token)
    branch = cfg.get("default_branch") or repo_info.get("default_branch") or "main"
    open_items = gh_api("GET", f"repos/{repo}/issues?state=open&per_page=100", token)
    if not isinstance(open_items, list): open_items = []
    open_issues = [item for item in open_items if "pull_request" not in item]
    pr_rows = []
    for pr_number in cfg.get("target_pulls", []):
        pr_rows.append(process_pr(repo, token, int(pr_number), cfg, open_issues))
    missing = missing_infrastructure(repo, token, branch)
    created_issues = create_infra_issues(repo, token, missing, open_issues, branch, int(cfg.get("max_new_issues_per_run", 5)))
    tracker = create_or_update_tracker(repo, token, pr_rows, missing, created_issues, open_issues, branch)
    result = {
        "tracker": tracker.get("html_url"),
        "target_prs": pr_rows,
        "created_issues": [issue.get("number") for issue in created_issues],
        "missing_infrastructure": [item["key"] for item in missing]
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
