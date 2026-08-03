#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ste-lint - anti-slop linter for English technical prose.

Score = violations per 100 words (lower is cleaner).
Basis: ASD-STE100 mechanics (sentence length, active voice, one word per
meaning) plus common LLM slop markers.

Usage:
    python3 ste-lint.py draft.md [more.md ...]
    python3 ste-lint.py --max 5 docs/*.md      # exit 1 if a file scores above 5
    cat draft.md | python3 ste-lint.py
    python3 ste-lint.py --json draft.md
    python3 ste-lint.py --explain draft.md     # per-line findings with fixes
    python3 ste-lint.py --format github --max 5 docs/*.md   # CI annotations

Exit codes:
    0 - every file is at or below the threshold (or no threshold was given)
    1 - at least one file is above the threshold
    2 - bad arguments or unreadable file

To exclude a region from the score, wrap it:
    <!-- anti-slop: off -->
    ... text the linter must ignore ...
    <!-- anti-slop: on -->

This file is standalone on purpose. A skill directory is copied as a unit,
so the linter must not import anything outside the standard library.
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
    "utilizes", "utilized", "utilising", "utilised", "leverages",
    "leveraged", "delve", "delves", "delved", "delving", "harness",
    "harnesses", "harnessing", "showcase", "showcases", "showcasing",
    "unlock", "unlocks", "unlocking", "elevate", "elevates", "elevating",
    "empower", "empowers", "empowering", "embark", "embarks", "embarking",
]

MARKETING = [
    "seamless", "seamlessly", "robust", "powerful", "cutting-edge",
    "state-of-the-art", "effortless", "effortlessly", "world-class",
    "next-generation", "next-gen", "revolutionary", "groundbreaking",
    "game-changing", "game changer", "best-in-class", "industry-leading",
    "unparalleled", "unlock the power", "supercharge", "blazing fast",
    "comprehensive solution", "holistic approach", "rich set of features",
    "comprehensive", "plethora", "myriad", "renowned", "meticulous",
    "meticulously", "invaluable", "vibrant", "fast-paced", "ever-evolving",
    "boasts",
]

AI_SLOP = [
    "let's dive in", "let us dive in", "dive deep", "deep dive into",
    "in today's fast-paced world", "in the ever-evolving landscape",
    "in the world of", "great question", "i hope this helps",
    "hope that helps", "at the end of the day", "the bottom line is",
    "when it comes to", "it's not just", "it is not just",
    "more than just", "navigating the complexities", "delve into",
    "tapestry", "testament to", "in conclusion,", "to sum up,",
    "in today's world", "at its core", "look no further",
    "navigate the landscape", "navigating the landscape",
]

HEDGE = [
    "maybe", "perhaps", "arguably", "generally speaking",
    "in most cases", "typically", "tends to", "somewhat", "fairly",
    "relatively", "essentially", "basically", "actually", "quite possibly",
]

CONTRACTION_RE = re.compile(
    r"\b\w+'(?:s|t|re|ve|ll|d|m)\b|\b\w+\u2019(?:s|t|re|ve|ll|d|m)\b", re.I)

# Irregular past participles that do not end in -ed/-en, so the suffix rule
# alone misses "is read", "is put", "was held".
IRREGULAR_PARTICIPLES = (
    "read|made|done|run|set|put|kept|held|found|left|lost|met|paid|said|"
    "told|cut|hit|let|split|spread|hurt|cost|heard|felt|sold|dealt|meant"
)
PASSIVE_RE = re.compile(
    r"\b(?:am|is|are|was|were|be|been|being|get|gets|got)\s+"
    r"(?:\w+ly\s+)?(?:\w+(?:ed|en|own|ought|uilt|ent)|"
    + IRREGULAR_PARTICIPLES + r")\b", re.I)

NOMINAL_RE = re.compile(
    r"\b\w{4,}(?:tion|sion|ment|ance|ence|ility|ization|isation)s?\b", re.I)
ING_MAIN_RE = re.compile(r"(?:^|(?<=[.!?]\s))\s*\w+ing\b", re.I)
# Sentence-initial words that merely end in "-ing" and are not participle
# openers (issue #13). Imperatives like "Bring the file." are good STE.
ING_STOP = frozenset({
    "anything", "bring", "cling", "during", "everything", "evening",
    "fling", "king", "morning", "nothing", "offspring", "ring",
    "something", "spring", "sting", "string", "swing", "thing", "wing",
})
MODAL_RE = re.compile(r"\b(?:could|should|would|may|might)\b", re.I)
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\u2019\-/]*")

# --- markup that must not be scored -------------------------------------------

FRONTMATTER_RE = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.S)
IGNORE_RE = re.compile(
    r"<!--\s*anti-slop:\s*off\s*-->.*?<!--\s*anti-slop:\s*on\s*-->", re.S | re.I)
FENCE_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
BARE_URL_RE = re.compile(r"https?://\S+")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def preprocess(text):
    """Remove everything that is markup, not prose.

    Frontmatter, ignored regions, code, image and link targets, bare URLs,
    and HTML comments are not written in prose mode, so scoring them adds
    noise to the result.
    """
    t = FRONTMATTER_RE.sub("", text)
    t = IGNORE_RE.sub(" ", t)
    t = FENCE_RE.sub(" ", t)
    t = INLINE_CODE_RE.sub(" ", t)
    t = MD_IMAGE_RE.sub(" ", t)
    t = MD_LINK_RE.sub(r"\1", t)
    t = BARE_URL_RE.sub(" ", t)
    t = HTML_COMMENT_RE.sub(" ", t)
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


def phrase_matches(text, phrases):
    """Return [(phrase, span)], charging each span once (issue #18).

    Longest phrase wins, so 'delve into' is one hit, not 'delve' plus
    'delve into'. The lists are deliberately kept per-language, so this
    mirrors the Russian helper instead of sharing it.
    """
    low = text.lower()
    found, taken = [], []
    for ph in sorted(phrases, key=len, reverse=True):
        pat = r"(?<![a-z])" + re.escape(ph.lower()) + r"(?![a-z])"
        for m in re.finditer(pat, low):
            start, end = m.span()
            if any(start >= s and end <= e for s, e in taken):
                continue
            taken.append((start, end))
            found.append((ph, (start, end)))
    found.sort(key=lambda f: f[1][0])
    return found


def count_phrases(text, phrases):
    hits = [ph for ph, _ in phrase_matches(text, phrases)]
    return len(hits), hits


PHRASE_GROUPS = (
    ("banned_word", BANNED),
    ("marketing_adjective", MARKETING),
    ("ai_slop", AI_SLOP),
    ("modal_hedge", HEDGE),
)


def categorised_matches(text, groups=PHRASE_GROUPS):
    """Return [(category, phrase, span)], one charge per span (issue #21).

    phrase_matches() guards one list at a time, so 'delve' in BANNED and
    'delve into' in AI_SLOP would each fire on the same words. Scanning the
    lists together, longest phrase first, keeps the count honest whichever
    list an entry sits in. A tie goes to the earlier group; LexiconIntegrity
    keeps one phrase out of two lists so ties stay hypothetical.
    """
    low = text.lower()
    pairs = [(cat, ph) for cat, phrases in groups for ph in phrases]
    pairs.sort(key=lambda cp: len(cp[1]), reverse=True)
    found, taken = [], []
    for cat, ph in pairs:
        pat = r"(?<![a-z])" + re.escape(ph.lower()) + r"(?![a-z])"
        for m in re.finditer(pat, low):
            start, end = m.span()
            if any(start >= s and end <= e for s, e in taken):
                continue
            taken.append((start, end))
            found.append((cat, ph, (start, end)))
    found.sort(key=lambda f: f[2][0])
    return found


def _ing_main_count(text):
    """Sentence-initial -ing matches, minus the non-participle stoplist."""
    return sum(1 for m in ING_MAIN_RE.finditer(text)
               if m.group(0).strip().lower() not in ING_STOP)


def lint(text):
    text = preprocess(text)
    sents = sentences(text)
    words = sum(wc(s) for s in sents) or 1

    v = {}
    v["long_sentence(>20w)"] = sum(1 for s in sents if wc(s) > 20)
    v["semicolon"] = text.count(";")
    v["contraction"] = len(CONTRACTION_RE.findall(text))
    v["passive_voice"] = len(PASSIVE_RE.findall(text))
    v["ing_main_verb"] = _ing_main_count(text)
    v["nominalization"] = len(NOMINAL_RE.findall(text))
    cm = categorised_matches(text)
    bh = [ph for cat, ph, _ in cm if cat == "banned_word"]
    mh = [ph for cat, ph, _ in cm if cat == "marketing_adjective"]
    ah = [ph for cat, ph, _ in cm if cat == "ai_slop"]
    v["banned_word"] = len(bh)
    v["marketing_adjective"] = len(mh)
    v["ai_slop"] = len(ah)
    v["modal_hedge"] = (len(MODAL_RE.findall(text))
                        + sum(1 for cat, _, _ in cm if cat == "modal_hedge"))

    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    v["long_paragraph(>6s)"] = sum(1 for p in paras if len(sentences(p)) > 6)

    total = sum(v.values())
    return {
        "words": words,
        "sentences": len(sents),
        "violations": v,
        "per100w": {k: round(x * 100.0 / words, 2) for k, x in v.items()},
        "total": total,
        "total_per100w": round(total * 100.0 / words, 2),
        "em_dash(slop-marker)": text.count("\u2014"),
        "longest_sentence_words": max((wc(s) for s in sents), default=0),
        "sample_banned": list(dict.fromkeys(bh))[:8],
        "sample_marketing": list(dict.fromkeys(mh))[:8],
        "sample_ai_slop": list(dict.fromkeys(ah))[:8],
    }


SUGGEST = {
    "long_sentence(>20w)": "Split into sentences of 20 words or fewer.",
    "semicolon": "Use a full stop. One sentence, one idea.",
    "contraction": "Write both words in full.",
    "passive_voice": "Name the actor. Use active voice.",
    "ing_main_verb": "Start with the subject and a finite verb.",
    "nominalization": "Prefer the verb form.",
    "banned_word": "Use the plain word.",
    "marketing_adjective": "Delete, or give the number that proves it.",
    "ai_slop": "Delete the filler phrase.",
    "modal_hedge": "State the fact or the condition.",
    "long_paragraph(>6s)": "Split into paragraphs of 6 sentences or fewer.",
}

REPLACE = {
    "utilize": "use", "utilise": "use", "utilization": "use",
    "leverage": "use", "leveraging": "use", "facilitate": "help",
    "facilitates": "helps", "commence": "start", "terminate": "end",
    "endeavor": "try", "endeavour": "try", "ascertain": "find out",
    "aforementioned": "above", "heretofore": "until now", "thereof": "of it",
    "herein": "here", "whilst": "while", "amongst": "among",
    "in order to": "to", "due to the fact that": "because",
    "for the purpose of": "to", "in the event that": "if",
    "at this point in time": "now", "prior to": "before",
    "subsequent to": "after", "with regard to": "about",
    "in terms of": "in", "a number of": "several",
    "the vast majority of": "most",
    "utilizes": "uses", "utilized": "used", "utilising": "using",
    "utilised": "used", "leverages": "uses", "leveraged": "used",
    "delve": "examine", "delves": "examines", "delved": "examined",
    "delving": "examining", "harness": "use", "harnesses": "uses",
    "harnessing": "using", "showcase": "show", "showcases": "shows",
    "showcasing": "showing", "unlock": "enable", "unlocks": "enables",
    "unlocking": "enabling", "elevate": "improve", "elevates": "improves",
    "elevating": "improving", "empower": "let", "empowers": "lets",
    "empowering": "letting", "embark": "start", "embarks": "starts",
    "embarking": "starting", "comprehensive": "full", "plethora": "many",
    "myriad": "many", "boasts": "has",
}


def _phrase_hits(text, phrases, lineno, category, out):
    for ph, _span in phrase_matches(text, phrases):
        rep = REPLACE.get(ph.lower())
        sug = f"Use '{rep}' instead." if rep else SUGGEST[category]
        out.append((lineno, category, ph, sug))


def _categorised_hits(text, lineno, out):
    """Per-line phrase findings, one charge per span across all lists."""
    for cat, ph, _span in categorised_matches(text):
        rep = REPLACE.get(ph.lower())
        sug = f"Use '{rep}' instead." if rep else SUGGEST[cat]
        out.append((lineno, cat, ph, sug))


def diagnostics(text):
    """Per-line findings: list of (line, category, match, suggestion).

    Reads the original text, so line numbers match the editor. Skips
    frontmatter, fences, ignored regions, comments; strips inline markup.
    """
    out = []
    lines = text.split("\n")
    in_fm = bool(FRONTMATTER_RE.match(text))
    fm_end = 0
    if in_fm:
        m = re.search(r"\r?\n---\r?\n", text[4:])
        if m:
            fm_end = text[:].count("\n", 0, 4 + m.end())
    in_fence = in_ignore = False
    para_start, para_sents = None, 0
    for i, line in enumerate(lines, 1):
        if i <= fm_end:
            continue
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if re.search(r"<!--\s*anti-slop:\s*off\s*-->", s, re.I):
            in_ignore = True
            continue
        if re.search(r"<!--\s*anti-slop:\s*on\s*-->", s, re.I):
            in_ignore = False
            continue
        if in_ignore or re.fullmatch(r"<!--.*-->", s):
            continue
        s = INLINE_CODE_RE.sub(" ", s)
        s = MD_IMAGE_RE.sub(" ", s)
        s = MD_LINK_RE.sub(r"\1", s)
        s = BARE_URL_RE.sub(" ", s)
        s = re.sub(r"^\s*#{1,6}\s*", "", s)
        s = re.sub(r"^\s*(?:[-*+\u2022]|\d+[.)])\s+", "", s)
        if not s:
            if para_start is not None and para_sents > 6:
                out.append((para_start, "long_paragraph(>6s)",
                            f"{para_sents} sentences", SUGGEST["long_paragraph(>6s)"]))
            para_start, para_sents = None, 0
            continue
        if para_start is None:
            para_start = i
        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", s) if p.strip()]
        para_sents += len(parts)
        for p in parts:
            if wc(p) > 20:
                out.append((i, "long_sentence(>20w)",
                            f"{wc(p)} words: " + (p[:47] + "..." if len(p) > 50 else p),
                            SUGGEST["long_sentence(>20w)"]))
        for _ in re.finditer(";", s):
            out.append((i, "semicolon", ";", SUGGEST["semicolon"]))
        for cre, cat in ((CONTRACTION_RE, "contraction"), (PASSIVE_RE, "passive_voice"),
                         (ING_MAIN_RE, "ing_main_verb"), (NOMINAL_RE, "nominalization"),
                         (MODAL_RE, "modal_hedge")):
            for m in cre.finditer(s):
                if cre is ING_MAIN_RE and m.group(0).strip().lower() in ING_STOP:
                    continue
                out.append((i, cat, m.group(0), SUGGEST[cat]))
        _categorised_hits(s, i, out)
    if para_start is not None and para_sents > 6:
        out.append((para_start, "long_paragraph(>6s)",
                    f"{para_sents} sentences", SUGGEST["long_paragraph(>6s)"]))
    out.sort(key=lambda d: (d[0], d[1]))
    return out


def _gh_escape(v):
    return v.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def report(name, r, as_json, max_score, explain=False, fmt="text", text=None):
    if as_json:
        print(json.dumps({name: r}, ensure_ascii=False, indent=2))
    else:
        print(f"{os.path.basename(name):28} words={r['words']:5d} "
              f"total={r['total']:4d} per100w={r['total_per100w']:6.2f} "
              f"maxsent={r['longest_sentence_words']:3d}")
    if text is not None and fmt == "github" and not as_json:
        for line, cat, match, sug in diagnostics(text):
            print(f"::warning file={name},line={line},title={cat}::"
                  f"{_gh_escape(match)} -- {_gh_escape(sug)}")
    elif text is not None and explain and not as_json:
        for line, cat, match, sug in diagnostics(text):
            print(f"  L{line:<5} {cat:22} {match!r:40} {sug}")
    if max_score is not None and r["total_per100w"] > max_score:
        print(f"FAIL {name}: {r['total_per100w']:.2f} per 100 words "
              f"is above the limit of {max_score:.2f}", file=sys.stderr)
        return 1
    return 0


def run(files, as_json=False, max_score=None, explain=False, fmt="text"):
    if not files:
        return report("<stdin>", lint(sys.stdin.read()), True, max_score)
    expanded = []
    for f in files:
        expanded += sorted(glob.glob(f)) if any(c in f for c in "*?[") else [f]
    failed = 0
    for f in expanded:
        try:
            with open(f, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            print(f"ERROR {f}: {exc}", file=sys.stderr)
            return 2
        failed += report(f, lint(text), as_json, max_score,
                         explain, fmt, text)
    return 1 if failed else 0


def main(argv):
    as_json, max_score, explain, fmt, files = False, None, False, "text", []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--json":
            as_json = True
        elif a == "--explain":
            explain = True
        elif a == "--format":
            i += 1
            if i >= len(argv) or argv[i] not in ("text", "github"):
                print("ERROR: --format needs text or github", file=sys.stderr)
                return 2
            fmt = argv[i]
        elif a.startswith("--format="):
            fmt = a.split("=", 1)[1]
            if fmt not in ("text", "github"):
                print(f"ERROR: unknown format {fmt}", file=sys.stderr)
                return 2
        elif a == "--max":
            i += 1
            if i >= len(argv):
                print("ERROR: --max needs a number", file=sys.stderr)
                return 2
            max_score = float(argv[i])
        elif a.startswith("--max="):
            max_score = float(a.split("=", 1)[1])
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a.startswith("--"):
            print(f"ERROR: unknown option {a}", file=sys.stderr)
            return 2
        else:
            files.append(a)
        i += 1
    return run(files, as_json, max_score, explain, fmt)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
