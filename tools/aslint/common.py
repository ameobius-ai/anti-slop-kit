"""Shared helpers for the aslint wrapper tools.

Contract for every tool in this directory:

- stdout carries exactly one JSON object, nothing else;
- exit code 0 means the run succeeded (a lint ran, a rewrite passed),
  1 means the run succeeded and the verdict is negative, 2 means bad
  arguments or unreadable input;
- no rule logic lives here. The linters stay the source of truth; the
  wrappers call them as subprocesses and reshape the output.

Stdlib only, like the rest of the kit.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[2]
LINTERS = {
    "de": KIT_ROOT / "de" / "de-ste-lint.py",
    "en": KIT_ROOT / "en" / "ste-lint.py",
    "ru": KIT_ROOT / "ru" / "ru-ste-lint.py",
}

CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")
IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
URL_RE = re.compile(r"https?://[^\s)>\"']+")


def detect_lang(text):
    """Pick the linter by script. Any Cyrillic block routes to ru."""
    return "ru" if CYRILLIC_RE.search(text) else "en"


def run_linter(lang, path):
    """Run one linter on one file, return its parsed --json payload.

    The wrappers never pass --max, so the linter exits 0 here. A
    non-zero exit means the linter itself failed, which the caller
    reports as an error object instead of a traceback.
    """
    linter = LINTERS.get(lang)
    if linter is None:
        raise ValueError(f"unknown language: {lang}")
    proc = subprocess.run(
        [sys.executable, str(linter), "--json", str(path)],
        capture_output=True, text=True, cwd=str(KIT_ROOT))
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()
                           or f"linter exited {proc.returncode}")
    payload = json.loads(proc.stdout)
    return next(iter(payload.values()))


def lint_text(text, lang=None):
    """Lint a string. Returns (lang, result).

    The linter reads files, so the text goes through a temp file.
    The name of the temp file never reaches the output: callers key
    results by their own input path or by "<text>".
    """
    if lang is None:
        lang = detect_lang(text)
    suffix = ".ru.md" if lang == "ru" else ".md"
    fd, tmp = tempfile.mkstemp(suffix=suffix, prefix="aslint-", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        return lang, run_linter(lang, tmp)
    finally:
        os.unlink(tmp)


def fidelity_tokens(text):
    """Extract the bits that must survive any rewrite or hop.

    A lost token from any of these groups is information loss, not
    style: neither a human nor a robot can re-derive it from prose.
    Returns a dict with sorted unique lists: numbers (counts, offsets,
    versions), identifiers (tokens with an underscore: config keys,
    function names, env vars), and URLs.
    """
    urls = set()
    for m in URL_RE.finditer(text):
        urls.add(m.group(0).rstrip(".,;:!?"))
    rest = URL_RE.sub(" ", text)
    numbers = sorted(set(NUMBER_RE.findall(rest)))
    identifiers = sorted({tok for tok in IDENTIFIER_RE.findall(rest)
                          if "_" in tok})
    return {"numbers": numbers, "identifiers": identifiers,
            "urls": sorted(urls)}


def lost_tokens(source, transmitted):
    """Diff the fidelity groups. Returns groups -> missing list."""
    src = fidelity_tokens(source)
    dst = fidelity_tokens(transmitted)
    return {group: [tok for tok in src[group] if tok not in set(dst[group])]
            for group in ("numbers", "identifiers", "urls")}


def emit(obj):
    """The one way every tool in this directory writes its output."""
    print(json.dumps(obj, ensure_ascii=False, indent=2))
