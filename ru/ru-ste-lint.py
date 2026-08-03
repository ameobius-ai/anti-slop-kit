#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ru-ste-lint - anti-slop linter for Russian technical prose.

Score = violations per 100 words (lower is cleaner).
Basis: GOST R 58049-2017 clause 8.2.3 (UTR) mechanics + Russian AI-slop markers.

Usage:
    python3 ru-ste-lint.py draft.md [more.md ...]
    python3 ru-ste-lint.py --max 5 docs/*.md   # exit 1 if a file scores above 5
    cat draft.md | python3 ru-ste-lint.py
    python3 ru-ste-lint.py --json draft.md
    python3 ru-ste-lint.py --explain draft.md   # per-line findings with fixes
    python3 ru-ste-lint.py --format github --max 5 docs/*.md   # CI annotations

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

# --- lexicon -----------------------------------------------------------------

CLERICAL = [
    "в целях", "с целью", "в случае если", "в случае, если", "при наличии",
    "при отсутствии", "в связи с тем что", "в связи с тем, что",
    "в соответствии с", "в рамках", "в части", "в отношении", "по вопросу",
    "на предмет", "в целом ряде случаев", "в настоящее время",
    "на сегодняшний день", "в данный момент", "данный", "данного", "данной",
    "данные меры", "вышеуказанный", "вышеупомянутый", "нижеследующий",
    "осуществлять", "осуществляется", "осуществляют", "осуществление",
    "производить", "производится", "производятся", "реализовывать",
    "реализуется", "обеспечивать", "обеспечивается", "позволяет обеспечить",
    "имеет место", "является", "являются", "являлся", "представляет собой",
    "путем", "посредством", "ввиду того что", "с тем чтобы",
    "для того чтобы", "необходимо отметить", "следует отметить",
    "стоит отметить", "важно понимать", "важно отметить", "нужно понимать",
    "как известно", "не секрет что", "не секрет, что",
]

MARKETING = [
    "инновационный", "инновационное", "инновационная", "уникальный",
    "уникальное", "уникальная", "передовой", "передовые", "передовых",
    "лидирующий", "лидирующие", "ведущий поставщик", "мощный", "мощная",
    "мощные", "гибкий инструмент", "надежное решение",
    "качественный сервис", "комплексный подход", "индивидуальный подход",
    "команда профессионалов", "широкий спектр", "широкий ассортимент",
    "бесшовный", "бесшовная", "бесшовно", "революционный", "прорывной",
    "первоклассный", "высокотехнологичный", "беспрецедентный",
    "максимально эффективно", "оптимальное решение", "лучшие практики",
]

AI_SLOP = [
    "давайте разберемся", "давайте рассмотрим",
    "погрузимся", "давайте погрузимся", "в современном мире",
    "в эпоху цифровизации", "в мире технологий", "отличный вопрос",
    "надеюсь, это помогло", "надеюсь это помогло", "надеюсь, я помог",
    "если коротко", "подводя итог", "в заключение хочется",
    "стоит подчеркнуть", "игра меняется", "меняет правила игры",
    "не просто инструмент", "это не просто", "четко, по делу, без воды",
    "без лишней воды", "простыми словами говоря",
]

HEDGE = [
    "возможно", "вероятно", "как правило", "в большинстве случаев",
    "может быть", "скорее всего", "в некотором смысле", "довольно часто",
    "относительно", "достаточно часто", "в принципе", "по сути",
    "фактически", "в общем-то", "так сказать",
]

# verbal-noun suffixes (nominalization)
NOMINAL_RE = re.compile(
    r"\b[а-яё]{3,}(?:ание|ения|ение|аний|ений|ация|ации|аций|ирование|"
    r"ирования|ированию|изация|изации)\b", re.I)

# participles: -ущий/-ющий/-ащий/-ящий/-вший/-нный/-емый/-имый
PARTICIPLE_RE = re.compile(
    r"\b[а-яё]{3,}(?:ующ|ирующ|ующи|ющий|ющая|ющее|ющие|ющих|ющим|ющего|"
    r"ащий|ящий|ящая|ящие|ящих|вший|вшая|вшие|вших|вшего|"
    r"нный|нная|нное|нные|нных|нным|нного|емый|емая|емые|емых|имый|имая|имые)\b",
    re.I)

# Лексикализованные прилагательные на -щий, а не причастия (issue #14):
# «следующий раздел» не образовано от глагола в контексте документации.
PARTICIPLE_STOP = (
    "следующ", "соответствующ", "настоящ", "подходящ", "существующ",
    "вышеупомянут", "нижеследующ",
)

# gerunds
GERUND_RE = re.compile(
    r"\b[а-яё]{3,}(?:ывая|ивая|уя|юя|авши|ивши|вшись|ясь|аясь|уясь)\b", re.I)

# passive: reflexive -ся present/past + short participles
PASSIVE_RE = re.compile(
    r"\b[а-яё]{3,}(?:ется|ются|ался|алась|алось|ались|ится|ятся)\b", re.I)
SHORT_PASSIVE_RE = re.compile(
    r"\b(?:был[аио]?|будет|будут|быть)\s+[а-яё]{3,}(?:ан|ана|ано|аны|ен|ена|ено|ены|т|та|то|ты)\b",
    re.I)

WORD_RE = re.compile(r"[А-Яа-яЁёA-Za-z0-9][А-Яа-яЁёA-Za-z0-9'’\-/]*")
GEN_NOUN_RE = re.compile(
    r"\b[а-яё]{4,}(?:ия|ии|ов|ей|ам|ах|ями|ости|ения|ания)\s+"
    r"[а-яё]{4,}(?:ия|ии|ов|ей|ам|ах|ями|ости|ения|ания)\s+"
    r"[а-яё]{4,}(?:ия|ии|ов|ей|ам|ах|ями|ости|ения|ания)\b", re.I)

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
    and HTML comments are not prose, so scoring them adds noise.
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
        s = re.sub(r"^\s*(?:[-*+•]|\d+[.)])\s+", "", s)
        if not s:
            continue
        for p in re.split(r"(?<=[.!?])\s+", s):
            p = p.strip()
            if p:
                out.append(p)
    return out


def wc(s):
    return len(WORD_RE.findall(s))


def _fold(s):
    return s.lower().replace("ё", "е")


def phrase_matches(text, phrases):
    """Return [(phrase, span)], charging each span once (issue #18).

    Two lexicon entries can cover the same span: the lists carry both
    spellings of a yo-phrase, which the folding above makes identical, and
    they carry short phrases nested inside longer ones. Matching
    longest-first and skipping a span already taken keeps one span worth
    one violation.
    """
    low = _fold(text)
    found, taken = [], []
    for ph in sorted(phrases, key=len, reverse=True):
        pat = r"(?<![а-яa-z])" + re.escape(_fold(ph)) + r"(?![а-яa-z])"
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
    ("clerical", CLERICAL),
    ("marketing", MARKETING),
    ("ai_slop", AI_SLOP),
    ("hedge", HEDGE),
)


def categorised_matches(text, groups=PHRASE_GROUPS):
    """Return [(category, phrase, span)], one charge per span (issue #21).

    phrase_matches() guards one list at a time, so a short entry in one
    list and the longer phrase containing it in another would each fire on
    the same words. Scanning the lists together, longest phrase first,
    keeps the count honest whichever list an entry sits in. A tie goes to
    the earlier group; LexiconIntegrity keeps ties hypothetical.
    """
    low = _fold(text)
    pairs = [(cat, ph) for cat, phrases in groups for ph in phrases]
    pairs.sort(key=lambda cp: len(cp[1]), reverse=True)
    found, taken = [], []
    for cat, ph in pairs:
        pat = r"(?<![а-яa-z])" + re.escape(_fold(ph)) + r"(?![а-яa-z])"
        for m in re.finditer(pat, low):
            start, end = m.span()
            if any(start >= s and end <= e for s, e in taken):
                continue
            taken.append((start, end))
            found.append((cat, ph, (start, end)))
    found.sort(key=lambda f: f[2][0])
    return found


def _participle_count(text):
    """Participle matches minus lexicalized -щий adjectives (issue #14)."""
    return sum(1 for m in PARTICIPLE_RE.finditer(text)
               if not m.group(0).lower().startswith(PARTICIPLE_STOP))


def lint(text):
    text = preprocess(text)
    sents = sentences(text)
    words = sum(wc(s) for s in sents) or 1

    v = {}
    v["long_sentence(>20w)"] = sum(1 for s in sents if wc(s) > 20)
    v["semicolon"] = text.count(";")
    v["passive_reflexive"] = len(PASSIVE_RE.findall(text))
    v["passive_short"] = len(SHORT_PASSIVE_RE.findall(text))
    v["participle"] = _participle_count(text)
    v["gerund"] = len(GERUND_RE.findall(text))
    v["nominalization"] = len(NOMINAL_RE.findall(text))
    v["noun_chain(3+)"] = len(GEN_NOUN_RE.findall(text))
    cm = categorised_matches(text)
    ch = [ph for cat, ph, _ in cm if cat == "clerical"]
    mh = [ph for cat, ph, _ in cm if cat == "marketing"]
    ah = [ph for cat, ph, _ in cm if cat == "ai_slop"]
    v["clerical"] = len(ch)
    v["marketing"] = len(mh)
    v["ai_slop"] = len(ah)
    v["hedge"] = sum(1 for cat, _, _ in cm if cat == "hedge")

    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    v["long_paragraph(>6s)"] = sum(1 for p in paras if len(sentences(p)) > 6)

    total = sum(v.values())
    typo = {
        "straight_quotes": text.count('"'),
        "hyphen_as_dash": len(re.findall(r"\s-\s", text)),
        "em_dash": text.count("—"),
    }
    return {
        "words": words,
        "sentences": len(sents),
        "violations": v,
        "per100w": {k: round(x * 100.0 / words, 2) for k, x in v.items()},
        "total": total,
        "total_per100w": round(total * 100.0 / words, 2),
        "typography": typo,
        "longest_sentence_words": max((wc(s) for s in sents), default=0),
        "sample_clerical": list(dict.fromkeys(ch))[:8],
        "sample_marketing": list(dict.fromkeys(mh))[:8],
        "sample_ai_slop": list(dict.fromkeys(ah))[:8],
    }


SUGGEST = {
    "long_sentence(>20w)": "Разбейте на фразы до 20 слов.",
    "semicolon": "Поставьте точку. Одна фраза — одна мысль.",
    "passive_reflexive": "Назовите исполнителя. Активный залог.",
    "passive_short": "Назовите исполнителя. Активный залог.",
    "participle": "Замените причастие на глагол или придаточное.",
    "gerund": "Замените деепричастие на второе сказуемое.",
    "nominalization": "Используйте глагол вместо отглагольного существительного.",
    "noun_chain(3+)": "Разорвите цепочку родительных падежей.",
    "clerical": "Уберите канцелярит. Напишите просто.",
    "marketing": "Удалите или дайте цифру, которая это доказывает.",
    "ai_slop": "Удалите штамп.",
    "hedge": "Сформулируйте факт или условие.",
    "long_paragraph(>6s)": "Разбейте абзац: не более 6 фраз.",
}

REPLACE = {
    "осуществлять": "делать", "осуществляется": "идёт",
    "осуществление": "работа", "является": "— (тире или прямое сказуемое)",
    "являются": "— (тире или прямое сказуемое)",
    "представляет собой": "— (тире)", "в целях": "чтобы",
    "с целью": "чтобы", "для того чтобы": "чтобы",
    "в случае если": "если", "в случае, если": "если",
    "при наличии": "если есть", "при отсутствии": "если нет",
    "в настоящее время": "сейчас", "на сегодняшний день": "сейчас",
    "в данный момент": "сейчас", "данный": "этот",
    "данного": "этого", "данной": "этой",
    "вышеуказанный": "названный выше", "путем": "через",
    "посредством": "через",
    "ввиду того что": "потому что", "в связи с тем что": "потому что",
    "производить": "делать", "реализовывать": "делать",
}


def _phrase_hits(text, phrases, lineno, category, out):
    for ph, _span in phrase_matches(text, phrases):
        rep = REPLACE.get(_fold(ph))
        sug = f"Напишите «{rep}»." if rep else SUGGEST[category]
        out.append((lineno, category, ph, sug))


def _categorised_hits(text, lineno, out):
    """Построчные находки по спискам: один спан — одно нарушение."""
    for cat, ph, _span in categorised_matches(text):
        rep = REPLACE.get(_fold(ph))
        sug = f"Напишите «{rep}»." if rep else SUGGEST[cat]
        out.append((lineno, cat, ph, sug))


def diagnostics(text):
    """Per-line findings: list of (line, category, match, suggestion).

    Reads the original text, so line numbers match the editor. Skips
    frontmatter, fences, ignored regions, comments; strips inline markup.
    """
    out = []
    lines = text.split("\n")
    fm_end = 0
    if FRONTMATTER_RE.match(text):
        m = re.search(r"\r?\n---\r?\n", text[4:])
        if m:
            fm_end = text.count("\n", 0, 4 + m.end())
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
        s = re.sub(r"^\s*(?:[-*+•]|\d+[.)])\s+", "", s)
        if not s:
            if para_start is not None and para_sents > 6:
                out.append((para_start, "long_paragraph(>6s)",
                            f"{para_sents} фраз", SUGGEST["long_paragraph(>6s)"]))
            para_start, para_sents = None, 0
            continue
        if para_start is None:
            para_start = i
        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", s) if p.strip()]
        para_sents += len(parts)
        for p in parts:
            if wc(p) > 20:
                out.append((i, "long_sentence(>20w)",
                            f"{wc(p)} слов: " + (p[:47] + "..." if len(p) > 50 else p),
                            SUGGEST["long_sentence(>20w)"]))
        for _ in re.finditer(";", s):
            out.append((i, "semicolon", ";", SUGGEST["semicolon"]))
        for cre, cat in ((PASSIVE_RE, "passive_reflexive"),
                         (SHORT_PASSIVE_RE, "passive_short"),
                         (PARTICIPLE_RE, "participle"),
                         (GERUND_RE, "gerund"),
                         (NOMINAL_RE, "nominalization"),
                         (GEN_NOUN_RE, "noun_chain(3+)")):
            for m in cre.finditer(s):
                if (cre is PARTICIPLE_RE
                        and m.group(0).lower().startswith(PARTICIPLE_STOP)):
                    continue
                out.append((i, cat, m.group(0), SUGGEST[cat]))
        _categorised_hits(s, i, out)
    if para_start is not None and para_sents > 6:
        out.append((para_start, "long_paragraph(>6s)",
                    f"{para_sents} фраз", SUGGEST["long_paragraph(>6s)"]))
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
