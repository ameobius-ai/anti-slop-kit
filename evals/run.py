#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate eval outputs for the four conditions and record the run.

Calls an OpenAI-compatible chat completions endpoint once per task, condition
and repeat, and writes each answer to <out>/<task>__<condition>[__rN].md.
Files that already exist are skipped, so an interrupted run can continue.

Every invocation also writes an immutable run record under --runs:

    evals/runs/<UTC>__<lang>__<model>/
        manifest.json         model, endpoint host, prompt digests, one entry
                              per cell, and why each cell has no new text
        prompts/<cond>.txt    the exact system prompt that was sent
        raw/<cell>.json       the unedited response body
        outputs/<cell>.md     the answer as generated

The first live run of this harness kept only the scored copies in
evals/outputs, so its generations could not be re-scored after a linter change
and could not be quoted as provenance. The gallery in examples/ had to be
written by hand for the same reason. A run that leaves no record is an anecdote.

Environment:
    ANTI_SLOP_API_KEY    required
    ANTI_SLOP_API_BASE   default https://api.openai.com/v1

Usage:
    python3 evals/run.py --model MODEL --lang en [--out DIR] [--runs DIR]
                         [--repeat N] [--timeout S]

Exit codes: 0 done, 1 one or more calls failed, 2 missing key.
Standard library only. The API key is never written to the run record.
"""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
TASKS = ROOT / "evals" / "tasks"

PLAIN = {
    "en": "Write clearly and concisely.",
    "ru": "Пишите ясно и кратко.",
}

BANLIST = {
    "en": (
        "Write clearly and concisely. Do not use these words and phrases: "
        "delve, leverage, utilize, robust, seamless, comprehensive, "
        "cutting-edge, game-changing, in today's world, it is important to "
        "note, unlock, elevate, empower, navigate the landscape."
    ),
    "ru": (
        "Пишите ясно и кратко. Не используйте эти слова и обороты: "
        "осуществлять, является, данный, в целях, в рамках, произвести "
        "настройку, инновационный, уникальный, мощный, в современном мире, "
        "важно отметить, стоит подчеркнуть."
    ),
}

SKILL_FILE = {"en": ROOT / "en" / "SKILL.md", "ru": ROOT / "ru" / "SKILL.md"}

UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def prompts(lang):
    return {
        "bare": "",
        "plain": PLAIN[lang],
        "banlist": BANLIST[lang],
        "skill": SKILL_FILE[lang].read_text(encoding="utf-8"),
    }


def tasks(lang):
    return sorted(TASKS.glob("%s-*.md" % lang))


def digest(text):
    """Short sha256 of a prompt, so two runs can be compared without diffing."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def slug(value):
    """A model name can carry slashes and colons; a directory name cannot."""
    return UNSAFE.sub("-", value).strip("-") or "model"


def endpoint_host(base):
    """Record where a run went without recording credentials.

    A base URL can carry a key in a query string or in userinfo, so only the
    host and path are kept. The key itself never reaches the manifest.
    """
    parsed = urllib.parse.urlsplit(base)
    host = parsed.hostname or ""
    if parsed.port:
        host = "%s:%d" % (host, parsed.port)
    return urllib.parse.urlunsplit((parsed.scheme, host, parsed.path, "", ""))


def call(base, key, model, system, user, timeout):
    """One chat completion. Returns (text, raw payload)."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    body = json.dumps({"model": model, "messages": messages}).encode("utf-8")
    request = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"], payload


def cell_name(task, condition, index, repeat):
    suffix = "" if repeat == 1 else "__r%d" % index
    return "%s__%s%s" % (task, condition, suffix)


def utc_stamp(now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%Y%m%dT%H%M%SZ")


def generate(lang, model, out, record, repeat=1, timeout=180, caller=None,
             base="", key="", stream=None):
    """Run every cell and write both the scoring copy and the run record.

    `caller` is injected so the harness can be tested without a network: it
    takes (system, user) and returns (text, raw). Every cell appears in the
    manifest, including the ones that produced no new text, because a run that
    silently writes nothing looks identical to a run that never happened.
    """
    caller = caller or (lambda system, user: call(base, key, model, system, user, timeout))
    stream = stream or sys.stdout

    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    record = pathlib.Path(record)
    for sub in ("prompts", "raw", "outputs"):
        (record / sub).mkdir(parents=True, exist_ok=True)

    conditions = prompts(lang)
    for condition, system in conditions.items():
        (record / "prompts" / ("%s.txt" % condition)).write_text(system, encoding="utf-8")

    entries = []
    failures = 0
    for task_path in tasks(lang):
        task = task_path.stem
        user = task_path.read_text(encoding="utf-8")
        for condition, system in conditions.items():
            for index in range(1, repeat + 1):
                name = cell_name(task, condition, index, repeat)
                entry = {
                    "cell": name,
                    "task": task,
                    "condition": condition,
                    "repeat": index,
                    "prompt_sha256": digest(system),
                    "status": "",
                }
                target = out / ("%s.md" % name)
                if target.exists():
                    entry["status"] = "skipped_existing"
                    entries.append(entry)
                    continue
                try:
                    answer, raw = caller(system, user)
                except Exception as error:      # noqa: BLE001 - recorded, not raised
                    entry["status"] = "failed"
                    entry["error"] = "%s: %s" % (type(error).__name__, error)
                    entries.append(entry)
                    failures += 1
                    print("FAIL %s: %s" % (name, error), file=sys.stderr)
                    continue
                target.write_text(answer, encoding="utf-8")
                (record / "outputs" / ("%s.md" % name)).write_text(answer, encoding="utf-8")
                (record / "raw" / ("%s.json" % name)).write_text(
                    json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
                entry["status"] = "written"
                entry["words"] = len(answer.split())
                entries.append(entry)
                print("wrote %s" % name, file=stream)
    return entries, failures


def manifest(lang, model, base, repeat, timeout, entries, started, finished):
    counts = {}
    for entry in entries:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
    return {
        "model": model,
        "lang": lang,
        "endpoint": endpoint_host(base),
        "repeat": repeat,
        "timeout": timeout,
        "started": started,
        "finished": finished,
        "cells": len(entries),
        "counts": counts,
        "entries": entries,
    }


def main(argv):
    parser = argparse.ArgumentParser(description="Generate eval outputs.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--lang", required=True, choices=["en", "ru"])
    parser.add_argument("--out", default="evals/outputs")
    parser.add_argument("--runs", default="evals/runs",
                        help="where the immutable run record is written")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args(argv)

    key = os.environ.get("ANTI_SLOP_API_KEY")
    if not key:
        print("run.py: set ANTI_SLOP_API_KEY", file=sys.stderr)
        return 2
    base = os.environ.get("ANTI_SLOP_API_BASE", "https://api.openai.com/v1")

    started = utc_stamp()
    record = pathlib.Path(args.runs) / ("%s__%s__%s" % (started, args.lang, slug(args.model)))
    entries, failures = generate(
        args.lang, args.model, args.out, record,
        repeat=args.repeat, timeout=args.timeout, base=base, key=key)

    meta = manifest(args.lang, args.model, base, args.repeat, args.timeout,
                    entries, started, utc_stamp())
    (record / "manifest.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # The old run.json overwrote itself every run and lost the history it was
    # supposed to keep. It stays for the scorer's sake and now points at the record.
    (pathlib.Path(args.out) / "run.json").write_text(
        json.dumps({"model": args.model, "lang": args.lang, "repeat": args.repeat,
                    "record": str(record)}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    counts = meta["counts"]
    print("%d cells: %s" % (meta["cells"], ", ".join(
        "%s %d" % (name, counts[name]) for name in sorted(counts))))
    print("record: %s" % record)
    if counts.get("skipped_existing") and not counts.get("written"):
        print("nothing new was generated: every output file already existed",
              file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
