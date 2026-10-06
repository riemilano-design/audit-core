"""Two-way mutation testing for the Core (TESTING_STRATEGY: mutations run
both ways, predicted before they are run).

For each row in ``mutations.json``:
  - a *copy* of ``audit_core`` is made in a fresh temporary directory,
  - the one-line/one-block textual mutation is applied to that copy only,
  - the three behavioral unit test modules (``test_model``,
    ``test_registry``, ``test_verify`` -- never this file, never
    ``test_boundary``) are run against the mutated copy in a *subprocess*,
    with a fresh ``pycache_prefix`` for that run so a stale compiled
    ``.pyc`` (see docs/TESTING_STRATEGY.md on Apple's python pycache_prefix)
    cannot hide the mutation,
  - the subprocess's exit code is compared against the mutation's
    ``predicted`` value ("red" = nonzero exit, "green" = exit 0).

A mismatch is **not** repaired by touching the mutation or the predicted
value here; it is left failing so it surfaces in the report.

The original source under ``core/py/audit_core/`` is never touched: this
module checks that its sha256 is the same before and after the whole run.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE_DIR = os.path.abspath(os.path.join(_HERE, "..", ".."))
_CORE_SRC_DIR = os.path.join(_AUDIT_CORE_DIR, "core", "py", "audit_core")
_MUTATIONS_PATH = os.path.join(_HERE, "mutations.json")

# The behavioral unit test modules a mutated copy is checked against.
# Deliberately excludes test_boundary (not a behavior test of verify/registry
# semantics) and this module itself (must not recurse into itself).
_UNIT_TEST_FILENAMES = ("test_model.py", "test_registry.py", "test_verify.py")


def _load_mutations():
    with open(_MUTATIONS_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _sha256_of_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _sha256_of_core_source():
    digests = {}
    for name in sorted(os.listdir(_CORE_SRC_DIR)):
        if name.endswith(".py"):
            digests[name] = _sha256_of_file(os.path.join(_CORE_SRC_DIR, name))
    return digests


def _run_mutation(mutation):
    """Apply one mutation to a fresh copy and run the unit tests against it.

    Returns the subprocess's return code (0 means every unit test passed).
    """

    temp_root = tempfile.mkdtemp(prefix="audit-core-mutation-")
    try:
        mutated_core_dir = os.path.join(temp_root, "audit_core")
        shutil.copytree(_CORE_SRC_DIR, mutated_core_dir)

        target_path = os.path.join(mutated_core_dir, mutation["file"])
        with open(target_path, "r", encoding="utf-8") as handle:
            text = handle.read()
        occurrences = text.count(mutation["old"])
        if occurrences != 1:
            raise AssertionError(
                "mutation %r: old string occurs %d times in %s (expected exactly 1)"
                % (mutation["id"], occurrences, mutation["file"])
            )
        mutated_text = text.replace(mutation["old"], mutation["new"], 1)
        with open(target_path, "w", encoding="utf-8") as handle:
            handle.write(mutated_text)

        tests_subset_dir = os.path.join(temp_root, "tests_subset")
        os.makedirs(tests_subset_dir)
        with open(os.path.join(tests_subset_dir, "__init__.py"), "w", encoding="utf-8") as handle:
            handle.write("")
        for filename in _UNIT_TEST_FILENAMES:
            shutil.copyfile(
                os.path.join(_HERE, filename), os.path.join(tests_subset_dir, filename)
            )

        pycache_dir = os.path.join(temp_root, "pyc")
        completed = subprocess.run(
            [
                sys.executable,
                "-X",
                "pycache_prefix=" + pycache_dir,
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests_subset",
                "-t",
                ".",
            ],
            cwd=temp_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return completed.returncode, completed.stdout.decode("utf-8", errors="replace")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


class MutationOldStringUniquenessTest(unittest.TestCase):
    """The 'old' text of every mutation must be unique in its source file,
    checked against the real (unmutated) source."""

    def test_each_mutation_old_string_occurs_exactly_once_in_real_source(self):
        for mutation in _load_mutations():
            path = os.path.join(_CORE_SRC_DIR, mutation["file"])
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            occurrences = text.count(mutation["old"])
            self.assertEqual(
                occurrences,
                1,
                "mutation %r: old string occurs %d times in %s"
                % (mutation["id"], occurrences, mutation["file"]),
            )


class MutationCatalogShapeTest(unittest.TestCase):
    def test_catalog_has_minimum_red_and_green_counts(self):
        mutations = _load_mutations()
        reds = [m for m in mutations if m["predicted"] == "red"]
        greens = [m for m in mutations if m["predicted"] == "green"]
        self.assertGreaterEqual(len(reds), 8)
        self.assertGreaterEqual(len(greens), 2)

    def test_catalog_predictions_are_only_red_or_green(self):
        for mutation in _load_mutations():
            self.assertIn(mutation["predicted"], ("red", "green"))


class MutationTwoWayTest(unittest.TestCase):
    """Runs every registered mutation and checks predicted vs. actual.

    This does not repair a mismatch by editing the mutation or the
    prediction; a mismatch fails the test, with the mismatching ids
    reported, for a human to read.
    """

    def test_all_mutations_match_their_prediction(self):
        mutations = _load_mutations()
        mismatches = []
        for mutation in mutations:
            returncode, output = _run_mutation(mutation)
            actual = "red" if returncode != 0 else "green"
            if actual != mutation["predicted"]:
                mismatches.append(
                    "%s: predicted=%s actual=%s (rc=%d)\n--- subprocess output (tail) ---\n%s"
                    % (mutation["id"], mutation["predicted"], actual, returncode, output[-2000:])
                )
        self.assertEqual(
            mismatches,
            [],
            "mutation prediction mismatch(es):\n" + "\n\n".join(mismatches),
        )


class MutationsDoNotTouchRealSourceTest(unittest.TestCase):
    def test_real_source_sha256_unchanged_after_mutation_run(self):
        before = _sha256_of_core_source()
        for mutation in _load_mutations():
            _run_mutation(mutation)
        after = _sha256_of_core_source()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
