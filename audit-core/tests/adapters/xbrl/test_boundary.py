# -*- coding: utf-8 -*-
"""C-1c B-2/B-3: 境界の試験(Adapter 側)。

B-2: ``audit_core`` を import するのは ``recipes.py`` と ``run.py`` だけ
(``edinet.py``・``instance.py``・``extract.py``・``vocabulary.py`` は 0 件)。
Core 側(``core/py/audit_core``)が ``adapters`` を import しないことは
``tests/core/test_boundary.py`` の ``ImportBoundaryTest``(許可された import
元の一覧に ``adapters`` が無い)で既に強制されているが、ここでも明示的に
確かめる。

B-3: ``adapters`` 以下に ``EDINET_API_KEY=`` の値の形が 0 件(Core 側の
``tests/core/test_boundary.py::SecretKeyBoundaryTest`` が audit-core 全体を
既に見ているが、Adapter 側でも明示的に確かめる)。試験の経路
(``tests/adapters/xbrl/``)が ``edinet.fetch`` / ``urllib.request.urlopen``
を静的に呼んでいないことも確かめる。
"""

import ast
import os
import re
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE_DIR = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_ADAPTERS_XBRL_DIR = os.path.join(_AUDIT_CORE_DIR, "adapters", "xbrl")
_ADAPTERS_DIR = os.path.join(_AUDIT_CORE_DIR, "adapters")
_CORE_SRC_DIR = os.path.join(_AUDIT_CORE_DIR, "core", "py", "audit_core")
_TESTS_ADAPTERS_DIR = os.path.join(_AUDIT_CORE_DIR, "tests", "adapters")

_FORBIDDEN_TO_IMPORT_CORE = ("edinet.py", "instance.py", "extract.py", "vocabulary.py", "__init__.py")
# C-1d adds three Core-touching modules: comparators.py (Comparison),
# resolve.py (Resolved) and registry_setup.py (Registry/State). None of
# them import vocabulary/instance/extract (comparators.py and resolve.py
# are checked for that specifically in test_lineage.py /
# C1D_PREDICTION.md §A/§3.2's "pure" requirement); they do legitimately
# import audit_core itself.
_ALLOWED_TO_IMPORT_CORE = ("recipes.py", "run.py", "comparators.py", "resolve.py", "registry_setup.py")


def _py_files(directory):
    return sorted(
        os.path.join(directory, name)
        for name in os.listdir(directory)
        if name.endswith(".py")
    )


def _imports_sibling_modules(path, sibling_names):
    """AST scan: True if this file imports any of ``sibling_names`` from
    the same package, as ``from . import <name>`` / ``from .<name> import
    ...`` / ``import adapters.xbrl.<name>``.
    """

    with open(path, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module in (None,) or node.module == "":
                for alias in node.names:
                    if alias.name in sibling_names:
                        hits.append(alias.name)
            elif node.module and node.module.split(".")[-1] in sibling_names:
                hits.append(node.module.split(".")[-1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                last = alias.name.split(".")[-1]
                if last in sibling_names:
                    hits.append(last)
    return hits


def _imports_audit_core(path):
    with open(path, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "audit_core":
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] == "audit_core":
                return True
    return False


def _calls_matching(path, names):
    """Static AST scan: True if a Call expression's full dotted name chain
    ends with (or matches) any of ``names`` (e.g. ``"edinet.fetch"`` or
    ``"urlopen"``).
    """

    with open(path, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)

    def dotted(node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            base = dotted(node.value)
            return (base + "." + node.attr) if base else node.attr
        return None

    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = dotted(node.func)
            if name and any(name == n or name.endswith("." + n) for n in names):
                hits.append(name)
    return hits


class CoreImportBoundaryTest(unittest.TestCase):
    def test_forbidden_modules_do_not_import_core(self):
        offenders = []
        for name in _FORBIDDEN_TO_IMPORT_CORE:
            path = os.path.join(_ADAPTERS_XBRL_DIR, name)
            if os.path.exists(path) and _imports_audit_core(path):
                offenders.append(name)
        self.assertEqual(offenders, [])

    def test_recipes_and_run_import_core(self):
        # Not a requirement per se (the instructions say these two *may*
        # import the Core), but recipes.py uses Core types directly, so we
        # assert that one does; run.py is checked by presence of the
        # module-level ``import audit_core`` statement (kept for C-1d).
        self.assertTrue(_imports_audit_core(os.path.join(_ADAPTERS_XBRL_DIR, "recipes.py")))

    def test_only_recipes_and_run_import_core_among_adapter_files(self):
        offenders = []
        for path in _py_files(_ADAPTERS_XBRL_DIR):
            name = os.path.basename(path)
            if _imports_audit_core(path) and name not in _ALLOWED_TO_IMPORT_CORE:
                offenders.append(name)
        self.assertEqual(offenders, [])

    def test_comparators_and_resolve_do_not_import_vocabulary_instance_extract(self):
        # C-1d task §A/§3.2: comparators.py reads only evidence/claim.value/
        # contract.params (the match_value ladder is copied locally, not
        # imported); resolve.py takes a facts list as a plain argument
        # instead of importing instance.py to load one itself.
        siblings = ("vocabulary", "instance", "extract")
        offenders = {}
        for name in ("comparators.py", "resolve.py"):
            hits = _imports_sibling_modules(os.path.join(_ADAPTERS_XBRL_DIR, name), siblings)
            if hits:
                offenders[name] = hits
        self.assertEqual(offenders, {})

    def test_core_does_not_import_adapters(self):
        offenders = []
        for path in _py_files(_CORE_SRC_DIR):
            with open(path, "r", encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] == "adapters":
                            offenders.append(os.path.basename(path))
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split(".")[0] == "adapters":
                        offenders.append(os.path.basename(path))
        self.assertEqual(offenders, [])


class SecretKeyBoundaryTest(unittest.TestCase):
    def test_no_edinet_api_key_value_under_adapters(self):
        pattern = re.compile(r"EDINET_API_KEY\s*[:=]\s*\S{8,}")
        offenders = []
        for root, dirs, files in os.walk(_ADAPTERS_DIR):
            dirs[:] = [d for d in dirs if d not in ("__pycache__",)]
            for name in files:
                path = os.path.join(root, name)
                with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                    text = handle.read()
                if pattern.search(text):
                    offenders.append(path)
        self.assertEqual(offenders, [])

    def test_edinet_py_only_references_the_env_var_name(self):
        path = os.path.join(_ADAPTERS_XBRL_DIR, "edinet.py")
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn('os.environ.get("EDINET_API_KEY")', text)


class NoNetworkInTestsTest(unittest.TestCase):
    def test_test_suite_never_calls_fetch_or_urlopen(self):
        offenders = {}
        for root, dirs, files in os.walk(_TESTS_ADAPTERS_DIR):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(root, name)
                hits = _calls_matching(path, ("fetch", "urlopen"))
                if hits:
                    offenders[os.path.relpath(path, _TESTS_ADAPTERS_DIR)] = hits
        self.assertEqual(offenders, {})

    def test_adapter_source_isolates_network_to_edinet_fetch(self):
        # urlopen must appear only inside edinet.py's fetch().
        offenders = []
        for path in _py_files(_ADAPTERS_XBRL_DIR):
            name = os.path.basename(path)
            hits = _calls_matching(path, ("urlopen",))
            if hits and name != "edinet.py":
                offenders.append(name)
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
