import ast
import json
import os
import re
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE_DIR = os.path.abspath(os.path.join(_HERE, "..", ".."))
_CORE_SRC_DIR = os.path.join(_AUDIT_CORE_DIR, "core", "py", "audit_core")

_ALLOWED_IMPORT_ROOTS = {"dataclasses", "enum", "typing", "collections", "abc", "audit_core"}

_SHORT_WORDS = {"ply", "usi", "kif"}


def _core_source_files():
    return sorted(
        os.path.join(_CORE_SRC_DIR, name)
        for name in os.listdir(_CORE_SRC_DIR)
        if name.endswith(".py")
    )


def _imported_roots(path):
    with open(path, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    roots = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                roots.append("audit_core")  # relative import within the package itself
            elif node.module:
                roots.append(node.module.split(".")[0])
    return roots


class ImportBoundaryTest(unittest.TestCase):
    def test_only_allowed_modules_are_imported(self):
        used_roots = set()
        offenders = []
        for path in _core_source_files():
            for root in _imported_roots(path):
                used_roots.add(root)
                if root not in _ALLOWED_IMPORT_ROOTS:
                    offenders.append((os.path.basename(path), root))
        self.assertEqual(offenders, [])
        # record what was actually used, for the report (not a pass/fail condition)
        self.assertTrue(used_roots.issubset(_ALLOWED_IMPORT_ROOTS))

    def test_at_least_one_file_is_scanned(self):
        self.assertGreaterEqual(len(_core_source_files()), 1)


def _forbidden_words():
    words_path = os.path.join(_HERE, "forbidden_words.json")
    with open(words_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _find_forbidden_word_hits(text, words):
    hits = []
    lowered = text.lower()
    for word in words:
        if word in _SHORT_WORDS:
            pattern = r"\b" + re.escape(word) + r"\b"
            if re.search(pattern, lowered, flags=re.IGNORECASE):
                hits.append(word)
        else:
            if word.lower() in lowered:
                hits.append(word)
    return hits


class ForbiddenWordTest(unittest.TestCase):
    def test_forbidden_words_list_is_non_empty(self):
        self.assertGreaterEqual(len(_forbidden_words()), 1)

    def test_core_source_has_zero_forbidden_words(self):
        words = _forbidden_words()
        offenders = {}
        for path in _core_source_files():
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            hits = _find_forbidden_word_hits(text, words)
            if hits:
                offenders[os.path.basename(path)] = hits
        self.assertEqual(offenders, {})

    def test_short_word_matcher_does_not_false_positive_on_substrings(self):
        # "usi" as a short word must not fire on an unrelated word that merely
        # contains the same three letters without a word boundary.
        hits = _find_forbidden_word_hits("business logic only", ["usi"])
        self.assertEqual(hits, [])

    def test_short_word_matcher_fires_on_whole_word(self):
        hits = _find_forbidden_word_hits("the usi protocol", ["usi"])
        self.assertEqual(hits, ["usi"])


class SecretKeyBoundaryTest(unittest.TestCase):
    def test_no_edinet_api_key_value_anywhere_under_audit_core(self):
        pattern = re.compile(r"EDINET_API_KEY\s*[:=]\s*\S{8,}")
        offenders = []
        for root, dirs, files in os.walk(_AUDIT_CORE_DIR):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
            for name in files:
                path = os.path.join(root, name)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                        text = handle.read()
                except (IOError, OSError):
                    continue
                if pattern.search(text):
                    offenders.append(path)
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
