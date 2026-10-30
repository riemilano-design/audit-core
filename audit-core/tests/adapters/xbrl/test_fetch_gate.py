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
# 2026-10-13(merge の整合): 2026-10-09 の封A/封B 4 件は main 側で開封済み
# (NORMALIZATION_SEAL_A_RESULT / SIGN_SEAL_B_RESULT)。いまの封は D-002 の手順 4 専用 2 件。
# 正本は fixtures/xbrl/holdout_reserved_2026-10-12.json(下の試験で突き合わせる)。
SEALED_DOC_IDS = ("S100Z39P", "S100Z4N9")
SEALED_DATE_STRINGS = ("2026-09-24", "2026-09-28")   # candidates_2026-09.json の date
FORMER_SEALED_DOC_IDS = ("S100Z3JY", "S100Z35K", "S100Z3V1", "S100Z3HP")
RESERVED_RECORD = "holdout_reserved_2026-10-12.json"

# 取る入口(2026-10-09 に数えた 4 本 + main 側の人間が回す道具 1 本、2026-10-13)。**字で書く。**
FETCHING_TOOLS = ("xbrl_probe.py", "select_third_2026-10-01.py",
                  "fetch_allocated_2026-10-08.py", "fetch_new_draw_2026-10-09.py",
                  "fetch_sealed_material_2026-10-09.py")
# urlopen を呼ぶが EDINET ではない(LLM の端点)。関門の対象外。**字で書き、host を試験で確かめる。**
NON_EDINET_OPENERS = ("ai_prose_generate_2026-10-09.py",)
# urlopen を呼ぶが取る道具ではない(割当の記録を作る)。2026-10-09 から一覧に在る。
OTHER_OPENERS = ("allocate_documents_2026-10-08.py",)


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
    def test_the_sealed_doc_ids_are_listed(self):
        for doc in SEALED_DOC_IDS:
            self.assertIn(doc, G.SEALED_DOCS, doc)

    def test_the_gate_matches_the_reservation_record_exactly(self):
        """関門の字の一覧 == 正本(D-002 の予約記録)の docID。片方だけ変えたら赤くなる。"""
        import json
        with open(os.path.join(_FIXTURES_XBRL_DIR, RESERVED_RECORD), encoding="utf-8") as fh:
            rec = json.load(fh)
        reserved = sorted(r["docID"] for r in rec["reserved"])
        self.assertEqual(sorted(G.SEALED_DOCS), reserved)
        self.assertEqual(sorted(SEALED_DOC_IDS), reserved)

    def test_the_former_seals_are_history_not_refused(self):
        """2026-10-09 の封 4 件は開封済み(main の RESULT 文書)。関門は止めない・履歴には残す。"""
        for doc in FORMER_SEALED_DOC_IDS:
            self.assertIn(doc, G.OPENED_FORMER_SEALS, doc)
            self.assertNotIn(doc, G.SEALED_DOCS, doc)
            self.assertIsNone(G.refuse_if_sealed(doc_id=doc, where="試験"))

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
        self.assertEqual(sorted(opens), sorted(FETCHING_TOOLS + OTHER_OPENERS + NON_EDINET_OPENERS),
                         "urlopen を呼ぶ fixtures が一覧と違う: %s" % opens)

    def test_non_edinet_openers_really_do_not_name_edinet(self):
        """関門の対象外にした道具は、字の中に EDINET の host を 1 つも持たない。"""
        for name in NON_EDINET_OPENERS:
            consts = [n.value for n in ast.walk(_tree(name))
                      if isinstance(n, ast.Constant) and isinstance(n.value, str)]
            self.assertFalse([c for c in consts if "edinet" in c.lower()], name)
            self.assertTrue([c for c in consts if "api.anthropic.com" in c], name)

    def test_the_human_run_tool_hits_the_gate_before_reading_the_key(self):
        """fetch_sealed_material の fetch_zip は、字の一覧(門③)を通っても他の席の封で止まる。
        **故障を作って当てる**: 字の一覧に封じた docID を足し、鍵を消して呼ぶ。
        関門が鍵より前に在れば SealedMaterial、無ければ鍵の SystemExit が先に出る。"""
        import importlib.util
        from unittest import mock
        path = os.path.join(_FIXTURES_XBRL_DIR, "fetch_sealed_material_2026-10-09.py")
        spec = importlib.util.spec_from_file_location("fetch_sealed_material_for_test", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sealed = SEALED_DOC_IDS[0]
        faulted = mod.SEALED + ((sealed, "封X", "試験", "2026-09-24"), ("S100ZZZZ", "封X", "試験", "2026-01-01"))
        env = {k: v for k, v in os.environ.items() if k != "EDINET_API_KEY"}
        with mock.patch.object(mod, "SEALED", faulted), mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(G.SealedMaterial):
                mod.fetch_zip(sealed)
            # 対照: 封じていない id は関門を通り、鍵が無いので SystemExit で止まる(通信しない)
            with self.assertRaises(SystemExit):
                mod.fetch_zip("S100ZZZZ")


if __name__ == "__main__":
    unittest.main()
