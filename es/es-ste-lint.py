#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys, json

CLERICAL = [
    "a efectos de", "en virtud de", "por medio de la presente",
    "en el marco de", "con el objeto de", "en el ámbito de",
]

MARKETING = [
    "innovador", "innovadora", "revolucionario", "revolucionaria",
    "de vanguardia", "solución integral", "de última generación",
]

AI_SLOP = [
    "en el mundo de hoy", "en la era digital", "cabe destacar",
    "es importante destacar", "es importante mencionar",
]

HEDGE = [
    "básicamente", "simplemente", "realmente", "actualmente",
]

# Technical register (mirrors the ru allowlist from issue #33): standard
# documentation nouns built on these stems are correct doc vocabulary,
# not slop. Lowercase prefix match.
TECHNICAL_STEMS = (
    "configuraci", "instalaci", "conexi", "sesi", "gesti",
    "documentaci", "funcionamiento", "autenticaci", "autorizaci",
    "validaci", "ejecuci", "eliminaci", "actualizaci", "migraci",
    "integraci", "almacenamiento", "procesamiento", "rendimiento",
)


def _technical(word):
    """True if the (lowered) word is technical-register doc vocabulary."""
    w = word.lower()
    return any(w.startswith(stem) for stem in TECHNICAL_STEMS)


def lint(text):
    words = len(text.split())
    v = {}
    
    v["clerical_phrase"] = sum(text.lower().count(p) for p in CLERICAL)
    v["marketing_language"] = sum(text.lower().count(w) for w in MARKETING)
    v["ai_slop"] = sum(text.lower().count(p) for p in AI_SLOP)
    v["hedge_word"] = sum(text.lower().count(w) for w in HEDGE)
    
    sentences = re.split(r'[.!?]+', text)
    v["long_sentence(>20w)"] = sum(1 for s in sentences if len(s.split()) > 20)
    
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    v["long_paragraph(>6s)"] = sum(1 for p in paragraphs if len(re.split(r'[.!?]+', p)) > 6)
    
    v["passive_voice"] = len(re.findall(r'\b(es|son|fue|fueron)\s+\w+(ado|ido|ada|ida)\b', text, re.I))
    v["nominalization"] = sum(
        1 for m in re.finditer(r'\b\w+(ción|miento|aje)\b', text, re.I)
        if not _technical(m.group(0)))
    
    total = sum(v.values())
    
    return {
        "words": words,
        "violations": v,
        "total": total,
        "total_per100w": round(total * 100.0 / words, 2) if words > 0 else 0,
        "longest_sentence": max(len(s.split()) for s in sentences) if sentences else 0
    }

def main(argv):
    max_score = None
    files = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--max":
            i += 1
            if i >= len(argv):
                print("ERROR: --max needs a number", file=sys.stderr)
                return 2
            try:
                max_score = float(argv[i])
            except ValueError:
                print("ERROR: --max needs a number", file=sys.stderr)
                return 2
        elif a.startswith("--max="):
            try:
                max_score = float(a.split("=", 1)[1])
            except ValueError:
                print("ERROR: --max needs a number", file=sys.stderr)
                return 2
        elif a.startswith("--"):
            print(f"ERROR: unknown option {a}", file=sys.stderr)
            return 2
        else:
            files.append(a)
        i += 1
    if not files:
        print("Uso: python3 es-ste-lint.py [--max N] archivo.md [más.md ...]", file=sys.stderr)
        return 2
    failed = 0
    for filename in files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                text = f.read()
        except OSError as exc:
            print(f"ERROR {filename}: {exc}", file=sys.stderr)
            return 2
        result = lint(text)
        print(f"{filename:30} words={result['words']:5d} total={result['total']:4d} per100w={result['total_per100w']:6.2f}")
        if max_score is not None and result["total_per100w"] > max_score:
            print(f"FAIL {filename}: {result['total_per100w']:.2f} per 100 words "
                  f"is above the limit of {max_score:.2f}", file=sys.stderr)
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
