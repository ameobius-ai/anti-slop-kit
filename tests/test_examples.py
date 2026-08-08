"""Acceptance tests for the examples/ gallery.

The tests walk examples/*/ instead of naming the pairs, so a new pair is
covered on the day it is added and the suite cannot rot when the sixth pair
lands. The linters run as subprocesses, as tests/test_explain.py does, so the
numbers come from the same command a reader would run.

The language of a file is its name: *.ru.md goes to the Russian linter,
everything else goes to the English one. This is the rule hooks/pre-commit
uses, so a file that the test routes one way cannot be routed the other way
by the hook.
"""

import os
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
EN_LINT = str(ROOT / "en" / "ste-lint.py")
RU_LINT = str(ROOT / "ru" / "ru-ste-lint.py")

# The summary line ends with: words= 150 total= 32 per100w= 21.33 maxsent= 30
SCORE = re.compile(r"per100w=\s*([0-9]+(?:\.[0-9]+)?)")

# The after files must also pass the pre-commit hook at its default limit.
HOOK_DEFAULT_MAX = 5.0


def linter_for(path):
    return RU_LINT if path.name.endswith(".ru.md") else EN_LINT


def score(path):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, linter_for(path), str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    out = proc.stdout.decode("utf-8", "replace")
    match = SCORE.search(out)
    if match is None:
        raise AssertionError(
            "no score in the linter output for %s:\n%s%s"
            % (path, out, proc.stderr.decode("utf-8", "replace"))
        )
    return float(match.group(1))


def pair_dirs():
    if not EXAMPLES.is_dir():
        return []
    # Only en-*/ru-* dirs are before/after pairs; the tool demos
    # (basic-lint, custom-rules, rewrite-validation, transmit-check)
    # are not, and the walk must not claim them (#256).
    return sorted(p for p in EXAMPLES.iterdir()
                  if p.is_dir() and p.name.startswith(("en-", "ru-")))


class GalleryLayout(unittest.TestCase):
    def test_gallery_has_pairs(self):
        self.assertTrue(EXAMPLES.is_dir(), "examples/ is missing")
        self.assertTrue(pair_dirs(), "examples/ has no pair directories")

    def test_each_pair_has_one_before_and_one_after(self):
        for d in pair_dirs():
            before = sorted(d.glob("before*.md"))
            after = sorted(d.glob("after*.md"))
            self.assertEqual(
                len(before), 1, "%s needs exactly one before file, found %s" % (d.name, before)
            )
            self.assertEqual(
                len(after), 1, "%s needs exactly one after file, found %s" % (d.name, after)
            )

    def test_each_pair_has_notes(self):
        for d in pair_dirs():
            self.assertTrue(
                (d / "notes.md").is_file(),
                "%s needs a notes.md that says what the rewrite changed" % d.name,
            )

    def test_language_suffix_matches_directory_name(self):
        """A ru- pair uses *.ru.md, so the hook picks the Russian linter."""
        for d in pair_dirs():
            russian = d.name.startswith("ru-")
            for f in sorted(d.glob("before*.md")) + sorted(d.glob("after*.md")):
                self.assertEqual(
                    f.name.endswith(".ru.md"),
                    russian,
                    "%s/%s: a ru- pair needs the .ru.md suffix and an en- pair must not have it"
                    % (d.name, f.name),
                )


class GalleryScores(unittest.TestCase):
    def test_after_scores_lower_than_before(self):
        for d in pair_dirs():
            before = sorted(d.glob("before*.md"))
            after = sorted(d.glob("after*.md"))
            if not before or not after:
                continue  # reported by the layout test
            before_score = score(before[0])
            after_score = score(after[0])
            self.assertLess(
                after_score,
                before_score,
                "%s: after scores %.2f, before scores %.2f -- the pair shows nothing"
                % (d.name, after_score, before_score),
            )

    def test_after_files_pass_the_hook_default(self):
        for d in pair_dirs():
            after = sorted(d.glob("after*.md"))
            if not after:
                continue  # reported by the layout test
            after_score = score(after[0])
            self.assertLessEqual(
                after_score,
                HOOK_DEFAULT_MAX,
                "%s: after scores %.2f, above the hook default of %.1f"
                % (d.name, after_score, HOOK_DEFAULT_MAX),
            )


if __name__ == "__main__":
    unittest.main()
