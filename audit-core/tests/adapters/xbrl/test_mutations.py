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
  - a *scope* of this package's tests is run against the mutated tree in
    a *subprocess*, with its own fresh ``pycache_prefix``,
  - the subprocess's exit code is checked against the row's fixed fact
    ("red" = nonzero exit, "green" = exit 0) -- normally ``predicted``,
    but see the ``"prediction_miss"`` row below.

Three scopes (C-1d adds the second and third; C-1c's ``"A-"``-prefixed
rows keep the original, unchanged scope so their established
red/green outcomes are not disturbed by the new material):

  - ``"legacy"`` (every ``"A-"``-id row): ``test_claim_layer`` + C-1c's
    ``test_vocabulary``/``test_extract``/``test_instance``/``test_recipes``.
    Never ``test_lineage``/``test_boundary``/``test_run``/this module.
  - ``"default"`` (``"D-"``-id rows without an explicit ``"scope"``
    key): the legacy five *plus* ``test_comparators``/``test_resolve``/
    ``test_registry_setup`` (unit tests for the three C-1d modules) and
    ``tests/golden/test_instrument3.py`` (the 224-claim ``verify_all``
    gate) -- C-1d's comparators/resolver/registry are not exercised by
    any C-1c test, so ``test_instrument3`` has to be in scope for a
    mutation there to have a chance of turning red.
  - ``"gate_only"`` (an explicit ``"scope": "gate_only"`` row): just
    ``test_claim_layer`` + ``test_instrument3`` -- the two gates driven
    by the 224-claim real material, as opposed to the synthetic
    multi-member data ``test_instance`` uses, or the diff==0 case
    ``test_comparators`` constructs directly. Used by ``D-R7`` (the
    prediction itself, §3.6, says "計器 3 では green") and by
    ``D-R3b`` (added after ``D-R3``'s default-scope prediction turned
    out wrong -- see below; ``D-R3b``'s own prediction has no value
    since it was written after seeing the result, per its own note).

``"prediction_miss": true`` (currently only ``D-R3``): the coordinator's
2026-10-06 instruction is that a wrong prediction is recorded as a miss,
not repaired by narrowing the row's scope after the fact. Such a row
keeps its original ``predicted`` value unedited and carries
``"actual_first_measurement"`` (the fact ``_run_mutation_fresh`` is
actually checked against for *this* row, instead of ``predicted``). The
test still tallies, for every row, whether ``actual == predicted`` and
prints "predicted == actual: N 本 / 外れ: M 本 (ids)" at the end.

A mismatch (``actual`` against whichever fact a row is checked against)
is **not** repaired by touching the mutation, the ``predicted`` value,
or (except via the ``"prediction_miss"``/``"actual_first_measurement"``
mechanism above) the row's scope; it is left failing so it surfaces in
the report.

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
_GOLDEN_DIR = os.path.join(_TESTS_DIR, "golden")
_MUTATIONS_PATH = os.path.join(_HERE, "mutations.json")

# "legacy" scope: unchanged from C-1c, so the 10 "A-"-id rows' already
# -established outcomes are not affected by anything added in C-1d.
_LEGACY_BEHAVIOR_TEST_FILENAMES = (
    "test_claim_layer.py",
    "test_vocabulary.py",
    "test_extract.py",
    "test_instance.py",
    "test_recipes.py",
)
_DEFAULT_NEW_BEHAVIOR_TEST_FILENAMES = _LEGACY_BEHAVIOR_TEST_FILENAMES + (
    "test_comparators.py",
    "test_resolve.py",
    "test_registry_setup.py",
)
_GATE_ONLY_BEHAVIOR_TEST_FILENAMES = ("test_claim_layer.py",)

_GOLDEN_TEST_FILENAMES = ("test_instrument3.py",)
_GOLDEN_SUPPORT_FILENAMES = ("_instrument.py",)

_EXPECTATION_FILENAMES = ("core_expectation_1B.json", "core_expectation_5F.json",
                          # XBRL 直し §8(2026-10-08): 標準タクソノミのラベルの sha256 の記録。
                          # test_instance がコードの字面と突き合わせるので砂場にも写す
                          # (写さないと**全部の変異が同じ理由で赤くなり**、変異の測定が死ぬ ―
                          # 1 回これで 8 本の green の予測を赤にした)。
                          "taxonomy_labels_sha256.txt")


def _scope_for(mutation):
    """Return ``(behavior_filenames, golden_filenames)`` for one mutation
    row. See the module docstring for what each of the three scopes is
    and why ``D-R7`` alone uses ``"gate_only"``.
    """

    if mutation["id"].startswith("A-"):
        return _LEGACY_BEHAVIOR_TEST_FILENAMES, ()
    scope = mutation.get("scope", "default")
    if scope == "gate_only":
        return _GATE_ONLY_BEHAVIOR_TEST_FILENAMES, _GOLDEN_TEST_FILENAMES
    if scope == "default":
        return _DEFAULT_NEW_BEHAVIOR_TEST_FILENAMES, _GOLDEN_TEST_FILENAMES
    raise ValueError("mutation %r: unknown scope %r" % (mutation["id"], scope))


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


def _build_tree(temp_root, behavior_filenames, golden_filenames):
    """Mirror just enough of ``audit-core/`` for the given test scope to
    run with its real (unmodified) relative-path assumptions intact.
    ``golden_filenames`` (may be empty) are mirrored under
    ``tests/golden/`` alongside ``_instrument.py``.
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
    for name in behavior_filenames:
        shutil.copyfile(os.path.join(_HERE, name), os.path.join(tests_xbrl_dir, name))

    if golden_filenames:
        tests_golden_dir = os.path.join(tests_dir, "golden")
        os.makedirs(tests_golden_dir)
        shutil.copyfile(os.path.join(_GOLDEN_DIR, "__init__.py"), os.path.join(tests_golden_dir, "__init__.py"))
        for name in _GOLDEN_SUPPORT_FILENAMES:
            shutil.copyfile(os.path.join(_GOLDEN_DIR, name), os.path.join(tests_golden_dir, name))
        for name in golden_filenames:
            shutil.copyfile(os.path.join(_GOLDEN_DIR, name), os.path.join(tests_golden_dir, name))


def _run_mutation(mutation, temp_root):
    """Apply one mutation to the tree's single target file and run its
    scope (see ``_scope_for``) against it. Returns (returncode, output)."""

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
            "tests",
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

    behavior_filenames, golden_filenames = _scope_for(mutation)
    temp_root = tempfile.mkdtemp(prefix="audit-core-adapter-mutation-")
    try:
        _build_tree(temp_root, behavior_filenames, golden_filenames)
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
        """For most rows, the fact that must hold is ``actual == predicted``
        (the sealed prediction). A row with ``"prediction_miss": true`` is
        a prediction already known (and reported) to be wrong; for that
        row the fact this test fixes as reproducible is
        ``actual == actual_first_measurement`` instead -- the prediction
        value itself is left untouched (not rewritten to match the
        result; see 2026-10-06 coordinator instruction). The predicted-
        vs-actual tally (independent of which fact a row is checked
        against) is printed at the end either way.
        """

        mutations = _load_mutations()
        mismatches = []
        matched_predicted_ids = []
        missed_predicted_ids = []
        for mutation in mutations:
            returncode, output = _run_mutation_fresh(mutation)
            actual = "red" if returncode != 0 else "green"
            if mutation.get("prediction_miss"):
                expected = mutation["actual_first_measurement"]
                fact_label = "actual_first_measurement"
            else:
                expected = mutation["predicted"]
                fact_label = "predicted"
            if actual != expected:
                mismatches.append(
                    "%s: %s=%s actual=%s (rc=%d)\n--- subprocess output (tail) ---\n%s"
                    % (mutation["id"], fact_label, expected, actual, returncode, output[-2000:])
                )
            if actual == mutation["predicted"]:
                matched_predicted_ids.append(mutation["id"])
            else:
                missed_predicted_ids.append(mutation["id"])

        print(
            "\npredicted == actual: %d 本 / 外れ: %d 本 (%s)"
            % (len(matched_predicted_ids), len(missed_predicted_ids), ", ".join(missed_predicted_ids))
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
