# Deutsche Technische Prosa

## Beschreibung

de-ste-lint ist ein anti-slop linter für deutsche technische Prosa, basierend auf den Prinzipien der Leichten Sprache (Plain Language).

## Verwendung

Grundlegende Nutzung:
    python de/de-ste-lint.py dokument.md

Mit Schwellenwert:
    python de/de-ste-lint.py --max 5 dokument.md

JSON-Ausgabe:
    python de/de-ste-lint.py --json dokument.md

Detaillierte Erklärungen:
    python de/de-ste-lint.py --explain dokument.md

## Erkannte Muster

### Verbotene Wörter

- grundsätzlich, eigentlich, tatsächlich, praktisch
- sozusagen, gewissermaßen, gleichsam
- buchstäblich, wörtlich, aktuell, derzeit
- einfach, einfach nur, nur, bloß

### Marketing-Begriffe

- revolutionär, innovativ, disruptiv, transformativ
- leistungsstark, robust, skalierbar, flexibel
- intuitiv, nahtlos, modern, zukunftsweisend
- Spitzentechnologie, State-of-the-Art, High-End

### Füllwörter

- im Grunde genommen, tatsächlich, natürlich
- selbstverständlich, offensichtlich, klar
- die Wahrheit ist, die Tatsache ist
- meiner Meinung nach, ich denke, ich glaube

## Prinzipien der Leichten Sprache

1. **Einfache Wörter verwenden**
   - Vermeiden Sie komplexe oder vage Begriffe
   - Wählen Sie konkrete, spezifische Wörter

2. **Kurze Sätze**
   - Ein Gedanke pro Satz
   - Maximal 20-25 Wörter im strikten Modus

3. **Aktiv statt Passiv**
   - Das System verarbeitet die Datei statt Die Datei wird vom System verarbeitet

4. **Keine Nominalisierungen**
   - Um diese Aufgabe durchzuführen statt Die Durchführung dieser Aufgabe

5. **Spezifisch sein**
   - Vermeiden: sehr wichtig, sehr gut, sehr schwierig
   - Verwenden: präzise, messbare Beschreibungen

## Beispiele

Siehe de/samples/ für vollständige Beispiele:
- baseline.md: Dokument mit Slop-Mustern
- ste.md: Bereinigte Version nach Leichte-Sprache-Prinzipien

## Tests

Umfassende Tests finden Sie in tests/test_de_ste_lint.py