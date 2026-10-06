# -*- coding: utf-8 -*-
"""Two-way mutation testing for the XBRL Adapter (TESTING_STRATEGY: both
directions, predicted before run).

For each row in ``mutations.json``:
  - a fresh temporary tree mirroring ``audit-core/`` is built (unmutated
    ``core/py/audit_core``, the two expectation JSON files under
    ``fixtures/xbrl/``, the ``tests/__init__.py`` / ``tests/adapters/``
    bootstrap files, and a *copy* of ``adapters/``),
  - the one-line/one-block textual mutation is applied to that copy's
    single target file only,
  - a behavioral subset of this package's tests (``test_claim_layer`` --
    the 224-claim gate against real material -- plus
    ``test_vocabulary``/``test_extract``/``test_instance``/``test_recipes``;
    never this file, never ``test_lineage``/``test_boundary``/``test_run``)
    is run against the mutated tree in a *subprocess*, with its own fresh
    ``pycache_prefix``,
  - the subprocess's exit code is compared against the mutation's
    ``predicted`` value ("red" = nonzero exit, "green" = exit 0).

A mismatch is **not** repaired by touching the mutation or the predicted
value here; it is left failing so it surfaces in the report.

The real ``adapters/`` source is never touched: this module checks that
its sha256 (per file) is the same before and after the whole run. The
cached EDINET ZIPs under ``~/.cache/audit-core/edinet/`` are read (not
copied) by the mutated subprocess, via the real, absolute cache path.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE_DIR = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_ADAPTERS_SRC_DIR = os.path.join(_AUDIT_CORE_DIR, "adapters")
_CORE_PY_DIR = os.path.join(_AUDIT_CORE_DIR, "core", "py")
_FIXTURES_XBRL_DIR = os.path.join(_AUDIT_CORE_DIR, "fixtures", "xbrl")
_TESTS_DIR = os.path.join(_AUDIT_CORE_DIR, "tests")
_MUTATIONS_PATH = os.path.join(_HERE, "mutations.json")

# Behavioral test modules a mutated Adapter copy is checked against.
# Deliberately excludes test_lineage (compares against the probe originals,
# unrelated to whether a mutation breaks the Adapter's own behavior and
# would require copying the (unchanged) probe scripts into every temp
# tree), test_boundary/test_run (not behavior tests of the claim-building
# pipeline), and this module itself (must not recurse into itself).
_BEHAVIOR_TEST_FILENAMES = (
    "test_claim_layer.py",
    "test_vocabulary.py",
    "test_extract.py",
    "test_instance.py",
    "test_recipes.py",
)
_EXPECTATION_FILENAMES = ("core_expectation_1B.json", "core_expectation_5F.json")


def _load_mutations():
    with open(_MUTATIONS_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _sha256_of_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _sha256_of_adapters_source():
    digests = {}
    for root, _dirs, files in os.walk(_ADAPTERS_SRC_DIR):
        for name in files:
            if name.endswith(".py"):
                path = os.path.join(root, name)
                digests[os.path.relpath(path, _ADAPTERS_SRC_DIR)] = _sha256_of_file(path)
    return digests


def _build_tree(temp_root):
    """Mirror just enough of ``audit-core/`` for the behavioral subset to
    run with its real (unmodified) relative-path assumptions intact.
    """

    shutil.copytree(_CORE_PY_DIR, os.path.join(temp_root, "core", "py"))
    shutil.copytree(_ADAPTERS_SRC_DIR, os.path.join(temp_root, "adapters"))

    fixtures_dir = os.path.join(temp_root, "fixtures", "xbrl")
    os.makedirs(fixtures_dir)
    for name in _EXPECTATION_FILENAMES:
        shutil.copyfile(os.path.join(_FIXTURES_XBRL_DIR, name), os.path.join(fixtures_dir, name))

    tests_dir = os.path.join(temp_root, "tests")
    os.makedirs(tests_dir)
    shutil.copyfile(os.path.join(_TESTS_DIR, "__init__.py"), os.path.join(tests_dir, "__init__.py"))

    tests_adapters_dir = os.path.join(tests_dir, "adapters")
    os.makedirs(tests_adapters_dir)
    shutil.copyfile(
        os.path.join(_TESTS_DIR, "adapters", "__init__.py"),
        os.path.join(tests_adapters_dir, "__init__.py"),
    )

    tests_xbrl_dir = os.path.join(tests_adapters_dir, "xbrl")
    os.makedirs(tests_xbrl_dir)
    shutil.copyfile(os.path.join(_HERE, "__init__.py"), os.path.join(tests_xbrl_dir, "__init__.py"))
    shutil.copyfile(os.path.join(_HERE, "_material.py"), os.path.join(tests_xbrl_dir, "_material.py"))
    for name in _BEHAVIOR_TEST_FILENAMES:
        shutil.copyfile(os.path.join(_HERE, name), os.path.join(tests_xbrl_dir, name))


def _run_mutation(mutation, temp_root):
    """Apply one mutation to the tree's single target file and run the
    behavioral subset against it. Returns (returncode, output)."""

    target_path = os.path.join(temp_root, "adapters", "xbrl", mutation["file"])
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
            "tests/adapters/xbrl",
            "-t",
            ".",
        ],
        cwd=temp_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.returncode, completed.stdout.decode("utf-8", errors="replace")


def _run_mutation_fresh(mutation):
    import tempfile

    temp_root = tempfile.mkdtemp(prefix="audit-core-adapter-mutation-")
    try:
        _build_tree(temp_root)
        return _run_mutation(mutation, temp_root)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


class MutationOldStringUniquenessTest(unittest.TestCase):
    """The 'old' text of every mutation must be unique in its source file,
    checked against the real (unmutated) source."""

    def test_each_mutation_old_string_occurs_exactly_once_in_real_source(self):
        for mutation in _load_mutations():
            path = os.path.join(_ADAPTERS_SRC_DIR, "xbrl", mutation["file"])
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
        self.assertGreaterEqual(len(reds), 6)
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
            returncode, output = _run_mutation_fresh(mutation)
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
        before = _sha256_of_adapters_source()
        for mutation in _load_mutations():
            _run_mutation_fresh(mutation)
        after = _sha256_of_adapters_source()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
