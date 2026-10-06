# -*- coding: utf-8 -*-
"""Two-way mutation testing for the shogi Adapter (mirrors
``tests/adapters/xbrl/test_mutations.py``'s shape; simplified because
this Adapter's own tests are entirely synthetic -- no cached material,
so one scope covers all of them and each run is fast).

For each row in ``mutations.json``: a fresh temporary tree mirroring
``audit-core/`` is built (unmutated ``core/py/audit_core``, the
bootstrap ``tests/__init__.py``/``tests/adapters/__init__.py`` files,
and a *copy* of ``adapters/shogi``), the one-line textual mutation is
applied to that copy's single target file, the full synthetic behavior
-test scope (every ``tests/adapters/shogi/test_*.py`` except this
module itself) is run in a *subprocess* against the mutated tree, and
the subprocess's exit code is checked against the row's
``predicted`` ("red" = nonzero exit, "green" = exit 0).

The real ``adapters/shogi`` source is never touched: this module checks
its sha256 (per file) is the same before and after the whole run.
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
_REPO_ROOT_DIR = os.path.abspath(os.path.join(_AUDIT_CORE_DIR, ".."))
_ADAPTERS_SHOGI_SRC_DIR = os.path.join(_AUDIT_CORE_DIR, "adapters", "shogi")
_CORE_PY_DIR = os.path.join(_AUDIT_CORE_DIR, "core", "py")
_TESTS_DIR = os.path.join(_AUDIT_CORE_DIR, "tests")
_MUTATIONS_PATH = os.path.join(_HERE, "mutations.json")
# test_packet_ref.py の RegexLineageTest が 1 ファイルだけ読む(repo_root 相対)。
# 変異木でも同じ相対位置(<temp_root>/audit-core/.. = <temp_root>)に置く -- repo
# 全体は要らない(scripts/ の他のファイルは読まない)。
_PACKET_REF_TS_REL = os.path.join("scripts", "playtest", "lib", "packetRef.ts")
_PACKET_REF_TS_SRC = os.path.join(_REPO_ROOT_DIR, _PACKET_REF_TS_REL)

_BEHAVIOR_TEST_FILENAMES = (
    "test_canonical.py",
    "test_packet_ref.py",
    "test_resolve.py",
    "test_comparators.py",
    "test_recipes.py",
    "test_registry_setup.py",
    "test_end_to_end.py",
)
_SUPPORT_FILENAMES = ("_material.py",)


def _load_mutations():
    with open(_MUTATIONS_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _sha256_of_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _sha256_of_adapter_source():
    digests = {}
    for root, _dirs, files in os.walk(_ADAPTERS_SHOGI_SRC_DIR):
        for name in files:
            if name.endswith(".py"):
                path = os.path.join(root, name)
                digests[os.path.relpath(path, _ADAPTERS_SHOGI_SRC_DIR)] = _sha256_of_file(path)
    return digests


def _build_tree(temp_root):
    """Builds ``<temp_root>/audit-core/{core,adapters,tests}`` (mirroring
    ``audit-core/`` itself) **plus** ``<temp_root>/scripts/playtest/lib/
    packetRef.ts`` (one file, read-only reference for
    ``test_packet_ref.py``'s lineage test) -- so that the relative-path
    math in that test (``.. .. ..`` from ``tests/adapters/shogi`` up to
    ``audit-core``, then one more ``..`` to the repo root) resolves the
    same way it does for the real source tree, without mirroring the
    rest of the repository."""

    audit_core_dir = os.path.join(temp_root, "audit-core")
    os.makedirs(audit_core_dir)
    shutil.copytree(_CORE_PY_DIR, os.path.join(audit_core_dir, "core", "py"))

    packet_ref_dst = os.path.join(temp_root, _PACKET_REF_TS_REL)
    os.makedirs(os.path.dirname(packet_ref_dst))
    shutil.copyfile(_PACKET_REF_TS_SRC, packet_ref_dst)

    adapters_dir = os.path.join(audit_core_dir, "adapters")
    os.makedirs(adapters_dir)
    with open(os.path.join(adapters_dir, "__init__.py"), "w", encoding="utf-8") as handle:
        handle.write(
            "import os, sys\n"
            "_HERE = os.path.dirname(os.path.abspath(__file__))\n"
            "_CORE_PY = os.path.join(os.path.dirname(_HERE), 'core', 'py')\n"
            "if _CORE_PY not in sys.path:\n    sys.path.insert(0, _CORE_PY)\n"
        )
    shutil.copytree(_ADAPTERS_SHOGI_SRC_DIR, os.path.join(adapters_dir, "shogi"))

    tests_dir = os.path.join(audit_core_dir, "tests")
    os.makedirs(tests_dir)
    shutil.copyfile(os.path.join(_TESTS_DIR, "__init__.py"), os.path.join(tests_dir, "__init__.py"))

    tests_adapters_dir = os.path.join(tests_dir, "adapters")
    os.makedirs(tests_adapters_dir)
    shutil.copyfile(
        os.path.join(_TESTS_DIR, "adapters", "__init__.py"), os.path.join(tests_adapters_dir, "__init__.py")
    )

    tests_shogi_dir = os.path.join(tests_adapters_dir, "shogi")
    os.makedirs(tests_shogi_dir)
    shutil.copyfile(os.path.join(_HERE, "__init__.py"), os.path.join(tests_shogi_dir, "__init__.py"))
    for name in _SUPPORT_FILENAMES:
        shutil.copyfile(os.path.join(_HERE, name), os.path.join(tests_shogi_dir, name))
    for name in _BEHAVIOR_TEST_FILENAMES:
        shutil.copyfile(os.path.join(_HERE, name), os.path.join(tests_shogi_dir, name))


def _run_mutation(mutation, temp_root):
    target_path = os.path.join(temp_root, "audit-core", "adapters", "shogi", mutation["file"])
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

    audit_core_dir = os.path.join(temp_root, "audit-core")
    pycache_dir = os.path.join(temp_root, "pyc")
    completed = subprocess.run(
        [sys.executable, "-X", "pycache_prefix=" + pycache_dir, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
        cwd=audit_core_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.returncode, completed.stdout.decode("utf-8", errors="replace")


def _run_mutation_fresh(mutation):
    import tempfile

    temp_root = tempfile.mkdtemp(prefix="audit-core-shogi-mutation-")
    try:
        _build_tree(temp_root)
        return _run_mutation(mutation, temp_root)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


class MutationOldStringUniquenessTest(unittest.TestCase):
    def test_each_mutation_old_string_occurs_exactly_once_in_real_source(self):
        for mutation in _load_mutations():
            path = os.path.join(_ADAPTERS_SHOGI_SRC_DIR, mutation["file"])
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            occurrences = text.count(mutation["old"])
            self.assertEqual(
                occurrences, 1,
                "mutation %r: old string occurs %d times in %s" % (mutation["id"], occurrences, mutation["file"]),
            )


class MutationCatalogShapeTest(unittest.TestCase):
    def test_catalog_has_minimum_red_and_green_counts(self):
        mutations = _load_mutations()
        reds = [m for m in mutations if m["predicted"] == "red"]
        greens = [m for m in mutations if m["predicted"] == "green"]
        self.assertGreaterEqual(len(reds), 5)
        self.assertGreaterEqual(len(greens), 1)

    def test_catalog_predictions_are_only_red_or_green(self):
        for mutation in _load_mutations():
            self.assertIn(mutation["predicted"], ("red", "green"))


class MutationTwoWayTest(unittest.TestCase):
    def test_all_mutations_match_their_prediction(self):
        mutations = _load_mutations()
        mismatches = []
        matched_ids = []
        missed_ids = []
        for mutation in mutations:
            returncode, output = _run_mutation_fresh(mutation)
            actual = "red" if returncode != 0 else "green"
            expected = mutation["predicted"]
            if actual != expected:
                mismatches.append(
                    "%s: predicted=%s actual=%s (rc=%d)\n--- subprocess output (tail) ---\n%s"
                    % (mutation["id"], expected, actual, returncode, output[-2000:])
                )
                missed_ids.append(mutation["id"])
            else:
                matched_ids.append(mutation["id"])

        print(
            "\npredicted == actual: %d 本 / 外れ: %d 本 (%s)"
            % (len(matched_ids), len(missed_ids), ", ".join(missed_ids))
        )
        self.assertEqual(mismatches, [], "mutation prediction mismatch(es):\n" + "\n\n".join(mismatches))


class MutationsDoNotTouchRealSourceTest(unittest.TestCase):
    def test_real_source_sha256_unchanged_after_mutation_run(self):
        before = _sha256_of_adapter_source()
        for mutation in _load_mutations():
            _run_mutation_fresh(mutation)
        after = _sha256_of_adapter_source()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
