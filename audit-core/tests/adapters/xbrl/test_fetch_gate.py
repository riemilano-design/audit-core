# -*- coding: utf-8 -*-
"""封じた材料への関門が、**取る入口すべてで呼ばれている**ことを留める。

2026-10-09、本線の席の指摘で数えたら、EDINET から ZIP を取る道具は **4 つ**あり、
**錠はそのうち 1 つにしか入っていなかった。** しかも 2 つは**日付で選ぶ**ので、
docID の一覧では原理的に守れない。

**import は呼び出しではない。** だからこの試験は「import しているか」ではなく
**「木の中に ``refuse_if_sealed`` の呼び出しが在るか」**を見る。

関連する記憶の型:
- 「正常な入力では発火しない守りは、故障を作って当てないと測れない」
- 「鍵を使う CLI からしか呼ばれない門は 0 円の経路の外」
- 「試験が材料を読むなら、変異の砂場がそれを写すかを先に見る」
  → ``test_mutations._EXPECTATION_FILENAMES`` に 5 本足してある。

通信しない。ファイルを書かない。
"""

import ast
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
_FIXTURES_XBRL_DIR = os.path.join(_AUDIT_CORE_DIR, "fixtures", "xbrl")
if _FIXTURES_XBRL_DIR not in sys.path:
    sys.path.insert(0, _FIXTURES_XBRL_DIR)

import sealed_material as G  # noqa: E402

GATE = "refuse_if_sealed"

# **字で留める。**封を持っている席からの依頼が無いのに消えたら赤くなる。
SEALED_DOC_IDS = ("S100Z3JY", "S100Z35K", "S100Z3V1", "S100Z3HP")
SEALED_DATE_STRINGS = ("2026-09-24", "2026-09-25")

# 取る入口(2026-10-09 に数えた 4 本)。**字で書く。**
FETCHING_TOOLS = ("xbrl_probe.py", "select_third_2026-10-01.py",
                  "fetch_allocated_2026-10-08.py", "fetch_new_draw_2026-10-09.py")


def _tree(name):
    with open(os.path.join(_FIXTURES_XBRL_DIR, name), encoding="utf-8") as fh:
        return ast.parse(fh.read(), filename=name)


def _called_names(tree):
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                out.append(f.id)
            elif isinstance(f, ast.Attribute):
                out.append(f.attr)
    return out


class SealedListsTest(unittest.TestCase):
    def test_the_four_sealed_doc_ids_are_listed(self):
        for doc in SEALED_DOC_IDS:
            self.assertIn(doc, G.SEALED_DOCS, doc)

    def test_the_two_sealed_dates_are_listed(self):
        for d in SEALED_DATE_STRINGS:
            self.assertIn(d, G.SEALED_DATES, d)

    def test_every_entry_has_a_reason_written_on_it(self):
        for table in (G.SEALED_DOCS, G.SEALED_DATES):
            for key, reason in table.items():
                self.assertTrue(reason and len(reason) > 10, (key, reason))


class RefuseIfSealedTest(unittest.TestCase):
    def test_a_sealed_doc_id_raises(self):
        for doc in SEALED_DOC_IDS:
            with self.assertRaises(G.SealedMaterial):
                G.refuse_if_sealed(doc_id=doc, where="試験")

    def test_a_sealed_date_raises(self):
        for d in SEALED_DATE_STRINGS:
            with self.assertRaises(G.SealedMaterial):
                G.refuse_if_sealed(date=d, where="試験")

    def test_a_sealed_date_raises_through_a_timestamp(self):
        # 日付は "2026-09-24T09:00" のような形で渡ることがある
        with self.assertRaises(G.SealedMaterial):
            G.refuse_if_sealed(date="2026-09-24T09:00:00", where="試験")

    def test_our_own_material_passes(self):
        for doc in ("S100Z3CO", "S100Z4PA", "S100Z4Q1"):
            self.assertIsNone(G.refuse_if_sealed(doc_id=doc, where="試験"))

    def test_calling_with_neither_raises(self):
        # **守っているつもりで何も見ていない**形も止める
        with self.assertRaises(G.SealedMaterial):
            G.refuse_if_sealed(where="試験")


class EveryFetchingToolCallsTheGateTest(unittest.TestCase):
    """**import ではなく呼び出し**を見る(本線の席の指摘、2026-10-09)。"""

    def test_each_fetching_tool_calls_the_gate(self):
        for name in FETCHING_TOOLS:
            self.assertIn(GATE, _called_names(_tree(name)), name)

    def test_the_date_selecting_tools_pass_a_date_or_a_doc_id(self):
        # 日付で選ぶ道具が docID だけ見ていたら守れない
        for name in ("xbrl_probe.py", "select_third_2026-10-01.py"):
            kws = []
            for node in ast.walk(_tree(name)):
                if isinstance(node, ast.Call) and getattr(node.func, "id", None) == GATE:
                    kws.extend(k.arg for k in node.keywords)
            self.assertTrue({"date", "doc_id"} & set(kws), (name, kws))

    def test_any_fixture_that_opens_a_url_is_in_the_listed_tools(self):
        """**一覧が古くなったら赤くなる。** 新しい取得の道具を足したら気づく。"""
        opens = []
        for fn in sorted(os.listdir(_FIXTURES_XBRL_DIR)):
            if not fn.endswith(".py"):
                continue
            try:
                tree = _tree(fn)
            except (SyntaxError, OSError):
                continue
            if "urlopen" in _called_names(tree):
                opens.append(fn)
        self.assertEqual(sorted(opens), sorted(FETCHING_TOOLS + ("allocate_documents_2026-10-08.py",)),
                         "urlopen を呼ぶ fixtures が一覧と違う: %s" % opens)


if __name__ == "__main__":
    unittest.main()
