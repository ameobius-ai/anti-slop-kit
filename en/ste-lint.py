#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ste-lint - anti-slop linter for English technical prose.

Score = violations per 100 words (lower is cleaner).
Basis: ASD-STE100 mechanics (sentence length, active voice, one word per
meaning) plus common LLM slop markers.

Usage:
    python3 ste-lint.py draft.md [more.md ...]
    cat draft.md | python3 ste-lint.py
    python3 ste-lint.py --json draft.md
"""
import re, sys, json, glob, os

BANNED = [
    "utilize", "utilise", "utilization", "leverage", "leveraging",
    "facilitate", "facilitates", "commence", "terminate", "endeavor",
    "endeavour", "ascertain", "aforementioned", "heretofore", "thereof",
    "herein", "whilst", "amongst", "in order to", "due to the fact that",
    "for the purpose of", "in the event that", "at this point in time",
    "prior to", "subsequent to", "with regard to", "in terms of",
    "a number of", "the vast majority of", "it should be noted that",
    "it is important to note", "it is worth noting", "needless to say",
]

MARKETING = [
    "seamless", "seamlessly", "robust", "powerful", "cutting-edge",
    "state-of-the-art", "effortless", "effortlessly", "world-class",
    "next-generation", "next-gen", "revolutionary", "groundbreaking",
    "game-changing", "game changer", "best-in-class", "industry-leading",
    "unparalleled", "unlock the power", "supercharge", "blazing fast",
    "comprehensive solution", "holistic approach", "rich set of features",
]

AI_SLOP = [
    "let's dive in", "let us dive in", "dive deep", "deep dive into",
    "in today's fast-paced world", "in the ever-evolving landscape",
    "in the world of", "great question", "i hope this helps",
    "hope that helps", "at the end of the day", "the bottom line is",
    "when it comes to", "it's not just", "it is not just",
    "more than just", "navigating the complexities", "delve into",
    "tapestry", "testament to", "in conclusion,", "to sum up,",
]

HEDGE = [
    "might", "maybe", "perhaps", "arguably", "generally speaking",
    "in most cases", "typically", "tends to", "somewhat", "fairly",
    "relatively", "essentially", "basically", "actually", "quite possibly",
]

CONTRACTION_RE = re.compile(
    r"\b\w+'(?:s|t|re|ve|ll|d|m)\b|\b\w+\u2019(?:s|t|re|ve|ll|d|m)\b", re.I)
PASSIVE_RE = re.compile(
    r"\b(?:am|is|are|was|were|be|been|being|get|gets|got)\s+"
    r"(?:\w+ly\s+)?\w+(?:ed|en|own|ought|uilt|ent)\b", re.I)
NOMINAL_RE = re.compile(
    r"\b\w{4,}(?:tion|sion|ment|ance|ence|ility|ization|isation)s?\b", re.I)
ING_MAIN_RE = re.compile(r"(?:^|(?<=[.!?]\s))\s*\w+ing\b", re.I)
MODAL_RE = re.compile(r"\b(?:could|should|would|may|might)\b", re.I)
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\u2019\-/]*")


def strip_code(t):
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`[^`]*`", " ", t)
    return t


def sentences(text):
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        s = re.sub(r"^\s*#{1,6}\s*", "", s)
        s = re.sub(r"^\s*(?:[-*+\u2022]|\d+[.)])\s+", "", s)
        if not s:
            continue
        for p in re.split(r"(?<=[.!?])\s+", s):
            p = p.strip()
            if p:
                out.append(p)
    return out


def wc(s):
    return len(WORD_RE.findall(s))


def count_phrases(text, phrases):
    low = text.lower()
    n, hits = 0, []
    for ph in phrases:
        p = ph.lower()
        pat = r"(?<![a-z])" + re.escape(p) + r"(?![a-z])"
        for _ in re.finditer(pat, low):
            n += 1
            hits.append(ph)
    return n, hits


def lint(text):
    raw = text
    text = strip_code(text)
    sents = sentences(text)
    words = sum(wc(s) for s in sents) or 1

    v = {}
    v["long_sentence(>20w)"] = sum(1 for s in sents if wc(s) > 20)
    v["semicolon"] = text.count(";")
    v["contraction"] = len(CONTRACTION_RE.findall(text))
    v["passive_voice"] = len(PASSIVE_RE.findall(text))
    v["ing_main_verb"] = len(ING_MAIN_RE.findall(text))
    v["nominalization"] = len(NOMINAL_RE.findall(text))
    v["banned_word"], bh = count_phrases(text, BANNED)
    v["marketing_adjective"], mh = count_phrases(text, MARKETING)
    v["ai_slop"], ah = count_phrases(text, AI_SLOP)
    v["modal_hedge"] = len(MODAL_RE.findall(text)) + count_phrases(text, HEDGE)[0]

    paras = [p for p in re.split(r"\n\s*\n", raw) if p.strip()]
    v["long_paragraph(>6s)"] = sum(
        1 for p in paras if len(sentences(strip_code(p))) > 6)

    total = sum(v.values())
    return {
        "words": words,
        "sentences": len(sents),
        "violations": v,
        "per100w": {k: round(x * 100.0 / words, 2) for k, x in v.items()},
        "total": total,
        "total_per100w": round(total * 100.0 / words, 2),
        "em_dash(slop-marker)": raw.count("\u2014"),
        "longest_sentence_words": max((wc(s) for s in sents), default=0),
        "sample_banned": list(dict.fromkeys(bh))[:8],
        "sample_marketing": list(dict.fromkeys(mh))[:8],
        "sample_ai_slop": list(dict.fromkeys(ah))[:8],
    }


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    files = [a for a in args if not a.startswith("--")]
    if not files:
        print(json.dumps(lint(sys.stdin.read()), ensure_ascii=False, indent=2))
        return
    expanded = []
    for f in files:
        expanded += sorted(glob.glob(f)) if any(c in f for c in "*?[") else [f]
    for f in expanded:
        with open(f, encoding="utf-8") as fh:
            r = lint(fh.read())
        if as_json:
            print(json.dumps({f: r}, ensure_ascii=False, indent=2))
        else:
            print(f"{os.path.basename(f):28} words={r['words']:5d} "
                  f"total={r['total']:4d} per100w={r['total_per100w']:6.2f} "
                  f"maxsent={r['longest_sentence_words']:3d}")


if __name__ == "__main__":
    main()
