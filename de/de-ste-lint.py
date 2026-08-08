#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
de-ste-lint - anti-slop linter for German technical prose.

Score = violations per 100 words (lower is cleaner).
Adapted from English ste-lint for German language patterns.
Based on "Leichte Sprache" (Plain Language) principles.

Usage:
    python3 de-ste-lint.py draft.md [more.md ...]
    python3 de-ste-lint.py --max 5 docs/*.md
    cat draft.md | python3 de-ste-lint.py
    python3 de-ste-lint.py --json draft.md
    python3 de-ste-lint.py --explain draft.md

Exit codes:
    0 - every file is at or below the threshold
    1 - at least one file is above the threshold
    2 - bad arguments or unreadable file
"""
import re, sys, json, glob, os

# German-specific slop patterns
BANNED = [
    "grundsätzlich", "im Grunde", "eigentlich", "tatsächlich",
    "praktisch", "sozusagen", "gewissermaßen", "gleichsam",
    "buchstäblich", "wörtlich", "aktuell", "derzeit",
    "einfach", "einfach nur", "nur", "bloß",
    "sehr wichtig", "sehr gut", "sehr schlecht", "sehr groß",
    "sehr klein", "sehr einfach", "sehr schwierig", "sehr komplex",
    "in Bezug auf", "bezüglich", "hinsichtlich", "im Hinblick auf",
    "es ist wichtig zu beachten", "es sollte erwähnt werden",
    "es ist erwähnenswert", "ohne Zweifel", "zweifellos",
]

MARKETING = [
    "revolutionär", "innovativ", "disruptiv", "transformativ",
    "leistungsstark", "robust", "skalierbar", "flexibel",
    "intuitiv", "nahtlos", "modern", "zukunftsweisend",
    "Spitzentechnologie", "State-of-the-Art", "High-End",
    "umfassend", "ganzheitlich", "nachhaltig", "effizient",
    "optimiert", "maximiert", "perfekt", "ideal",
]

FILLER = [
    "im Grunde genommen", "tatsächlich", "natürlich", "selbstverständlich",
    "offensichtlich", "klar", "grundsätzlich", "prinzipiell",
    "die Wahrheit ist", "die Tatsache ist", "meiner Meinung nach",
    "ich denke", "ich glaube", "aus meiner Sicht",
    "sozusagen", "gewissermaßen", "gleichsam", "quasi",
]

# Compile patterns
BANNED_RE = re.compile(r'\b(' + '|'.join(re.escape(w) for w in BANNED) + r')\b', re.IGNORECASE)
MARKETING_RE = re.compile(r'\b(' + '|'.join(re.escape(w) for w in MARKETING) + r')\b', re.IGNORECASE)
FILLER_RE = re.compile(r'\b(' + '|'.join(re.escape(w) for w in FILLER) + r')\b', re.IGNORECASE)

def count_words(text):
    """Count words in German text."""
    words = re.findall(r'\w+', text, re.UNICODE)
    return len(words)

def find_violations(text):
    """Find all violations in text."""
    violations = []
    
    # Check banned words
    for match in BANNED_RE.finditer(text):
        violations.append({
            'type': 'banned',
            'word': match.group(0),
            'position': match.start()
        })
    
    # Check marketing words
    for match in MARKETING_RE.finditer(text):
        violations.append({
            'type': 'marketing',
            'word': match.group(0),
            'position': match.start()
        })
    
    # Check filler words
    for match in FILLER_RE.finditer(text):
        violations.append({
            'type': 'filler',
            'word': match.group(0),
            'position': match.start()
        })
    
    return violations

def lint_file(path):
    """Lint a single file."""
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    word_count = count_words(text)
    violations = find_violations(text)
    
    score = (len(violations) / word_count * 100) if word_count > 0 else 0
    
    return {
        'path': str(path),
        'words': word_count,
        'violations': len(violations),
        'score': round(score, 2),
        'findings': violations
    }

def main(argv=None):
    """Main entry point."""
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print('Usage: de-ste-lint.py <file> [files...]', file=sys.stderr)
        sys.exit(2)
    
    files = []
    max_score = None
    json_output = False
    explain = False
    
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == '--max':
            i += 1
            if i >= len(argv):
                print('Error: --max needs a number', file=sys.stderr)
                sys.exit(2)
            try:
                max_score = float(argv[i])
            except ValueError:
                print('Error: --max needs a number', file=sys.stderr)
                sys.exit(2)
        elif arg.startswith('--max='):
            try:
                max_score = float(arg.split('=', 1)[1])
            except ValueError:
                print('Error: --max needs a number', file=sys.stderr)
                sys.exit(2)
        elif arg == '--json':
            json_output = True
        elif arg == '--explain':
            explain = True
        elif arg.startswith('--'):
            continue
        else:
            files.extend(glob.glob(arg))
        i += 1
    
    if not files:
        print('No files found', file=sys.stderr)
        sys.exit(2)
    
    results = []
    for f in files:
        try:
            result = lint_file(f)
            results.append(result)
        except Exception as e:
            print(f'Error processing {f}: {e}', file=sys.stderr)
            sys.exit(2)
    
    if json_output:
        output = {r['path']: r for r in results}
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        for r in results:
            print(f"{r['path']}: {r['violations']} violations, score {r['score']}")
            if explain:
                for v in r['findings']:
                    print(f"  - {v['type']}: {v['word']}")
    
    # Check max score
    if max_score is not None:
        for r in results:
            if r['score'] > max_score:
                sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main()
