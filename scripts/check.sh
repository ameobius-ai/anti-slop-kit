#!/usr/bin/env bash
# The single gate: the checks CI runs, in one command you can run yourself.
#
#   bash scripts/check.sh          # everything
#   bash scripts/check.sh tests    # the unit tests and the compile check
#   bash scripts/check.sh lint     # the clean samples must stay clean
#
# Set ANTI_SLOP_FORMAT=github to make the linters print GitHub annotations.
# Set PYTHON to choose an interpreter. Exit code 0 means every check passed.
# Exit code 2 means the script was called with an argument it does not know.

set -euo pipefail

cd "$(dirname "$0")/.."

target="${1:-all}"
case "$target" in
	all | tests | lint) ;;
	*)
		printf 'usage: %s [all|tests|lint]\n' "$0" >&2
		exit 2
		;;
esac

python_bin="${PYTHON:-python3}"

format_args=()
if [ -n "${ANTI_SLOP_FORMAT:-}" ]; then
	format_args=(--format "${ANTI_SLOP_FORMAT}")
fi

step() {
	printf '\n== %s\n' "$1"
}

if [ "$target" != lint ]; then
	step 'unit tests'
	"$python_bin" -m unittest discover -s tests

	step 'the eval scripts must compile'
	"$python_bin" -m compileall -q evals

	step 'source files must not carry invisible characters'
	"$python_bin" scripts/check_control_chars.py
fi

if [ "$target" != tests ]; then
	step 'the clean English sample must stay clean'
	"$python_bin" en/ste-lint.py ${format_args[@]+"${format_args[@]}"} --max 2 en/samples/ste.md

	step 'the clean Russian sample must stay clean'
	"$python_bin" ru/ru-ste-lint.py ${format_args[@]+"${format_args[@]}"} --max 2 ru/samples/utr.md

	# no format_args on this line: es has no --format flag yet (#252)
	step 'the clean Spanish sample must stay clean'
	"$python_bin" es/es-ste-lint.py --max 2 es/samples/skill.md

	step 'baseline scores, for the log'
	"$python_bin" en/ste-lint.py en/samples/baseline.md
	"$python_bin" ru/ru-ste-lint.py ru/samples/baseline.md
	"$python_bin" es/es-ste-lint.py es/samples/baseline.md
fi

printf '\nAll checks passed.\n'
