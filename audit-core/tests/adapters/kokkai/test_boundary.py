# -*- coding: utf-8 -*-
"""境界: Core(``audit_core``)を **モジュールの先頭で** import してよいのは
``recipes.py``・``registry_setup.py``・``verify_meeting.py`` の 3 本だけ。
``comparators.py``・``resolve.py`` は関数の中でだけ import する(将棋 adapter
と同じ形)。``load.py``・``numerals.py`` は一切 import しない。
試験は通信しない(``urlopen``・``requests`` を呼ばない)。"""

import ast
import os
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_ADAPTER = os.path.join(_AUDIT_CORE, "adapters", "kokkai")

MODULE_LEVEL_CORE_IMPORTERS = ("recipes.py", "registry_setup.py", "verify_meeting.py")
FUNCTION_LEVEL_ONLY = ("comparators.py", "resolve.py")
NEVER = ("__init__.py", "load.py", "numerals.py")


def _core_imports(path):
    """``(module_level, function_level)`` の件数。"""

    with open(path, "r", encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    top, inner = 0, 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [(node.module or "").split(".")[0]]
        else:
            continue
        if "audit_core" not in names:
            continue
        if node.col_offset == 0:
            top += 1
        else:
            inner += 1
    return top, inner


class CoreImportBoundaryTest(unittest.TestCase):
    def test_every_adapter_file_is_classified(self):
        files = sorted(n for n in os.listdir(_ADAPTER) if n.endswith(".py"))
        self.assertEqual(files, sorted(MODULE_LEVEL_CORE_IMPORTERS + FUNCTION_LEVEL_ONLY + NEVER))

    def test_module_level_importers(self):
        for name in MODULE_LEVEL_CORE_IMPORTERS:
            top, _ = _core_imports(os.path.join(_ADAPTER, name))
            self.assertGreaterEqual(top, 1, name)

    def test_function_level_only(self):
        for name in FUNCTION_LEVEL_ONLY:
            top, inner = _core_imports(os.path.join(_ADAPTER, name))
            self.assertEqual(top, 0, name)
            self.assertGreaterEqual(inner, 1, name)

    def test_never_importers(self):
        for name in NEVER:
            self.assertEqual(_core_imports(os.path.join(_ADAPTER, name)), (0, 0), name)


class NoNetworkTest(unittest.TestCase):
    def test_adapter_and_tests_do_not_open_the_network(self):
        offenders = []
        for d in (_ADAPTER, _HERE):
            for name in os.listdir(d):
                if not name.endswith(".py"):
                    continue
                with open(os.path.join(d, name), "r", encoding="utf-8") as fh:
                    text = fh.read()
                if name == os.path.basename(__file__):
                    continue
                if ("url" + "open(") in text or ("import " + "requests") in text:
                    offenders.append(name)
        self.assertEqual(offenders, [])
