#!/bin/sh
# One-command demo: score the samples, show per-line findings, run the tests.
# No dependencies, no network. Expected: baselines above 20 per 100 words,
# clean samples below 2, tests OK.
set -eu
cd "$(dirname "$0")"

echo "== 1/4 English scores =="
python3 en/ste-lint.py en/samples/baseline.md en/samples/ste.md

echo
echo "== 2/4 English findings (first 8) =="
python3 en/ste-lint.py --explain en/samples/baseline.md | head -9

echo
echo "== 3/4 Russian scores =="
python3 ru/ru-ste-lint.py ru/samples/baseline.md ru/samples/utr.md

echo
echo "== 4/4 Tests =="
python3 -m unittest discover -s tests

echo
echo "Demo OK. Try: python3 en/ste-lint.py --explain your-file.md"
