#!/usr/bin/env python3
"""Generate eval outputs for the four conditions.

Calls an OpenAI-compatible chat completions endpoint once per task and
condition, and writes each answer to <out>/<task>__<condition>.md. Files that
already exist are skipped, so an interrupted run can continue.

Environment:
    ANTI_SLOP_API_KEY    required
    ANTI_SLOP_API_BASE   default https://api.openai.com/v1

Usage:
    python3 evals/run.py --model MODEL --lang en [--out DIR] [--repeat N]

Exit codes: 0 done, 1 one or more calls failed, 2 missing key.
Standard library only. This script needs network access and has never been
executed by its author.
"""

import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
TASKS = ROOT / "evals" / "tasks"

PLAIN = {
    "en": "Write clearly and concisely.",
    "ru": "\u041f\u0438\u0448\u0438\u0442\u0435 \u044f\u0441\u043d\u043e \u0438 \u043a\u0440\u0430\u0442\u043a\u043e.",
}

BANLIST = {
    "en": (
        "Write clearly and concisely. Do not use these words and phrases: "
        "delve, leverage, utilize, robust, seamless, comprehensive, "
        "cutting-edge, game-changing, in today's world, it is important to "
        "note, unlock, elevate, empower, navigate the landscape."
    ),
    "ru": (
        "\u041f\u0438\u0448\u0438\u0442\u0435 \u044f\u0441\u043d\u043e \u0438 \u043a\u0440\u0430\u0442\u043a\u043e. \u041d\u0435 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 \u044d\u0442\u0438 \u0441\u043b\u043e\u0432\u0430 \u0438 \u043e\u0431\u043e\u0440\u043e\u0442\u044b: "
        "\u043e\u0441\u0443\u0449\u0435\u0441\u0442\u0432\u043b\u044f\u0442\u044c, \u044f\u0432\u043b\u044f\u0435\u0442\u0441\u044f, \u0434\u0430\u043d\u043d\u044b\u0439, \u0432 \u0446\u0435\u043b\u044f\u0445, \u0432 \u0440\u0430\u043c\u043a\u0430\u0445, \u043f\u0440\u043e\u0438\u0437\u0432\u0435\u0441\u0442\u0438 "
        "\u043d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0443, \u0438\u043d\u043d\u043e\u0432\u0430\u0446\u0438\u043e\u043d\u043d\u044b\u0439, \u0443\u043d\u0438\u043a\u0430\u043b\u044c\u043d\u044b\u0439, \u043c\u043e\u0449\u043d\u044b\u0439, \u0432 \u0441\u043e\u0432\u0440\u0435\u043c\u0435\u043d\u043d\u043e\u043c \u043c\u0438\u0440\u0435, "
        "\u0432\u0430\u0436\u043d\u043e \u043e\u0442\u043c\u0435\u0442\u0438\u0442\u044c, \u0441\u0442\u043e\u0438\u0442 \u043f\u043e\u0434\u0447\u0435\u0440\u043a\u043d\u0443\u0442\u044c."
    ),
}

SKILL_FILE = {"en": ROOT / "en" / "SKILL.md", "ru": ROOT / "ru" / "SKILL.md"}


def prompts(lang):
    return {
        "bare": "",
        "plain": PLAIN[lang],
        "banlist": BANLIST[lang],
        "skill": SKILL_FILE[lang].read_text(encoding="utf-8"),
    }


def tasks(lang):
    return sorted(TASKS.glob("%s-*.md" % lang))


def call(base, key, model, system, user, timeout):
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
    return payload["choices"][0]["message"]["content"]


def main(argv):
    parser = argparse.ArgumentParser(description="Generate eval outputs.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--lang", required=True, choices=["en", "ru"])
    parser.add_argument("--out", default="evals/outputs")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args(argv)

    key = os.environ.get("ANTI_SLOP_API_KEY")
    if not key:
        print("run.py: set ANTI_SLOP_API_KEY", file=sys.stderr)
        return 2
    base = os.environ.get("ANTI_SLOP_API_BASE", "https://api.openai.com/v1")

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    conditions = prompts(args.lang)
    failures = 0
    written = []

    for task_path in tasks(args.lang):
        task = task_path.stem
        user = task_path.read_text(encoding="utf-8")
        for condition, system in conditions.items():
            for index in range(1, args.repeat + 1):
                suffix = "" if args.repeat == 1 else "__r%d" % index
                target = out / ("%s__%s%s.md" % (task, condition, suffix))
                if target.exists():
                    continue
                try:
                    answer = call(base, key, args.model, system, user, args.timeout)
                except (urllib.error.URLError, KeyError, ValueError, OSError) as error:
                    print("FAIL %s: %s" % (target.name, error), file=sys.stderr)
                    failures += 1
                    continue
                target.write_text(answer, encoding="utf-8")
                written.append(target.name)
                print("wrote %s" % target.name)

    meta = out / "run.json"
    meta.write_text(
        json.dumps(
            {"model": args.model, "lang": args.lang, "repeat": args.repeat, "written": written},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
