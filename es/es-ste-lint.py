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
    v["nominalization"] = len(re.findall(r'\b\w+(ción|miento|aje)\b', text, re.I))
    
    total = sum(v.values())
    
    return {
        "words": words,
        "violations": v,
        "total": total,
        "total_per100w": round(total * 100.0 / words, 2) if words > 0 else 0,
        "longest_sentence": max(len(s.split()) for s in sentences) if sentences else 0
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 es-ste-lint.py archivo.md", file=sys.stderr)
        sys.exit(2)
    
    for filename in sys.argv[1:]:
        with open(filename, 'r', encoding='utf-8') as f:
            text = f.read()
        result = lint(text)
        print(f"{filename:30} words={result['words']:5d} total={result['total']:4d} per100w={result['total_per100w']:6.2f}")
