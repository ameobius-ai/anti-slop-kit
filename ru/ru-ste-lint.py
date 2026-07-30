#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ru-ste-lint - anti-slop linter for Russian technical prose.

Score = violations per 100 words (lower is cleaner).
Basis: GOST R 58049-2017 (8.2.3 UTR) mechanics + Russian AI-slop markers.

Usage:
    python3 ru-ste-lint.py draft.md [more.md ...]
    cat draft.md | python3 ru-ste-lint.py
    python3 ru-ste-lint.py --json draft.md
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
    "путем", "путём", "посредством", "ввиду того что", "с тем чтобы",
    "для того чтобы", "необходимо отметить", "следует отметить",
    "стоит отметить", "важно понимать", "важно отметить", "нужно понимать",
    "как известно", "не секрет что", "не секрет, что",
]

MARKETING = [
    "инновационный", "инновационное", "инновационная", "уникальный",
    "уникальное", "уникальная", "передовой", "передовые", "передовых",
    "лидирующий", "лидирующие", "ведущий поставщик", "мощный", "мощная",
    "мощные", "гибкий инструмент", "надежное решение", "надёжное решение",
    "качественный сервис", "комплексный подход", "индивидуальный подход",
    "команда профессионалов", "широкий спектр", "широкий ассортимент",
    "бесшовный", "бесшовная", "бесшовно", "революционный", "прорывной",
    "первоклассный", "высокотехнологичный", "беспрецедентный",
    "максимально эффективно", "оптимальное решение", "лучшие практики",
]

AI_SLOP = [
    "давайте разберемся", "давайте разберёмся", "давайте рассмотрим",
    "погрузимся", "давайте погрузимся", "в современном мире",
    "в эпоху цифровизации", "в мире технологий", "отличный вопрос",
    "надеюсь, это помогло", "надеюсь это помогло", "надеюсь, я помог",
    "если коротко", "подводя итог", "в заключение хочется",
    "стоит подчеркнуть", "игра меняется", "меняет правила игры",
    "не просто инструмент", "это не просто", "четко, по делу, без воды",
    "чётко, по делу, без воды", "без лишней воды", "простыми словами говоря",
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

# participles: -ущий/-ющий/-ащий/-ящий/-вший/-ший/-нный/-емый/-имый/-тый
PARTICIPLE_RE = re.compile(
    r"\b[а-яё]{3,}(?:ующ|ирующ|ующи|ющий|ющая|ющее|ющие|ющих|ющим|ющего|"
    r"ащий|ящий|ящая|ящие|ящих|вший|вшая|вшие|вших|вшего|"
    r"нный|нная|нное|нные|нных|нным|нного|емый|емая|емые|емых|имый|имая|имые)\b",
    re.I)

# gerunds: -ая/-яя (deeprichastie) is ambiguous; use safer -в/-вши/-ав/-ив forms
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


def strip_code(t: str) -> str:
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`[^`]*`", " ", t)
    return t


def sentences(text: str):
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


def wc(s: str) -> int:
    return len(WORD_RE.findall(s))


def count_phrases(text: str, phrases):
    low = text.lower().replace("ё", "е")
    n, hits = 0, []
    for ph in phrases:
        p = ph.lower().replace("ё", "е")
        for _ in re.finditer(r"(?<![а-яa-z])" + re.escape(p) + r"(?![а-яa-z])", low):
            n += 1
            hits.append(ph)
    return n, hits


def lint(text: str) -> dict:
    raw = text
    text = strip_code(text)
    sents = sentences(text)
    words = sum(wc(s) for s in sents) or 1

    v = {}
    longs = [(wc(s), s) for s in sents if wc(s) > 20]
    v["long_sentence(>20w)"] = len(longs)
    v["semicolon"] = text.count(";")
    v["passive_reflexive"] = len(PASSIVE_RE.findall(text))
    v["passive_short"] = len(SHORT_PASSIVE_RE.findall(text))
    v["participle"] = len(PARTICIPLE_RE.findall(text))
    v["gerund"] = len(GERUND_RE.findall(text))
    v["nominalization"] = len(NOMINAL_RE.findall(text))
    v["noun_chain(3+)"] = len(GEN_NOUN_RE.findall(text))
    v["clerical"], ch = count_phrases(text, CLERICAL)
    v["marketing"], mh = count_phrases(text, MARKETING)
    v["ai_slop"], ah = count_phrases(text, AI_SLOP)
    v["hedge"], _ = count_phrases(text, HEDGE)

    paras = [p for p in re.split(r"\n\s*\n", raw) if p.strip()]
    v["long_paragraph(>6s)"] = sum(
        1 for p in paras if len(sentences(strip_code(p))) > 6)

    total = sum(v.values())
    typo = {
        "straight_quotes": raw.count('"'),
        "hyphen_as_dash": len(re.findall(r"\s-\s", raw)),
        "em_dash": raw.count("—"),
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


def main():
    args = [a for a in sys.argv[1:]]
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
