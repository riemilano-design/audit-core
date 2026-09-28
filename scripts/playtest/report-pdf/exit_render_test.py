# -*- coding: utf-8 -*-
# exit_render.py(付録のページ抜きと索引の束ね)の変異試験。
# check_answer_test.py・check_structure_test.py・compare_render_test.py と同じ流儀
# (外部ライブラリなし・unittest だけ・材料は一時フォルダの合成・PDF は fitz)。
#
# **`exit_index.py` が定数だけのモジュールであることも、ここで固定する**(司令塔の条件 2026-09-28)。
# 門(`check_structure.py`)が `exit_index.py` を import するのは「定数」だからで、
# **組版の道具(reportlab・fitz・pypdf)を import し始めたら、門が組版に依存する** ― それを赤にする。
#
# 実行: `python3 -X utf8 scripts/playtest/report-pdf/exit_render_test.py`
import ast
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import exit_index as EI  # noqa: E402
import exit_render as ER  # noqa: E402

# 合成の付録。**ページごとに手数・節の名前を印字**して、抜いたページが正しいかを文字で確かめられるようにする。
APPENDIX_1_PAGES = [["付録 1 の 1 ページ", "読み方"], ["付録 1 の 2 ページ", "形勢の流れ"],
                    ["付録 1 の 3 ページ", "40 手目の局面"], ["付録 1 の 4 ページ", "70 手目の局面"]]
APPENDIX_3_PAGES = [["付録 3 の 1 ページ", "読み方"], ["付録 3 の 2 ページ", "分かれ道"],
                    ["付録 3 の 3 ページ", "59 手目の局面"]]

INDEX_1 = {"appendix": "付録1", "source": "a1.pdf", "pages": 4,
           "positions": {"1/40": 3, "2/70": 4},
           "sections": {"読み方": 1, "形勢の流れ": 2}}
INDEX_3 = {"appendix": "付録3", "source": "a3.pdf", "pages": 3,
           "positions": {"3 分": {"5/59": 3}},
           "sections": {"読み方": 1, "分かれ道": 2}}

MD = "".join([
    "# 束ねの試し\n\n",
    "## 局面で見る\n\n",
    "<!-- pos: 1/40 付録1 -->\n\n",
    "<!-- pos: 5/59 付録3 3 分 -->\n\n",
    "## 数え方\n\n",
    "<!-- sec: 付録1/形勢の流れ -->\n\n",
    "<!-- sec: 付録3/分かれ道 -->\n",
])


def write_pdf(path, pages):
    import fitz

    doc = fitz.open()
    try:
        for lines in pages:
            page = doc.new_page()
            y = 72
            for line in lines:
                page.insert_text((72, y), line, fontname="japan", fontsize=11)
                y += 24
        doc.save(path)
    finally:
        doc.close()


def write_json(path, obj):
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


class ExitIndexIsConstantsOnlyTest(unittest.TestCase):
    """**`exit_index.py` は定数だけ。**組版の道具を import し始めたら赤にする
    ― 門が `exit_index.py` を import してよいのは、それが組版ではないから(司令塔の条件)。"""

    FORBIDDEN = {"reportlab", "fitz", "pymupdf", "pypdf"}

    def test_imports_no_typesetting_libraries(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exit_index.py")
        with io.open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        self.assertEqual(names & self.FORBIDDEN, set(),
                         f"exit_index.py が組版の道具を import している: {sorted(names & self.FORBIDDEN)}")

    def test_key_list_is_one_place(self):
        """鍵の一覧が**同じオブジェクト**であること(写しが 2 か所に無い証拠)。
        `exit_index.py` の鍵を改名すると、**書く側と読む側が同時に落ちる。**"""
        import check_structure as CS

        self.assertIs(ER.OWN_KEYS, EI.EXIT_RENDER_KEYS)
        self.assertIs(CS.EXIT_RENDER_KEYS, EI.EXIT_RENDER_KEYS)


class ExitRenderTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        d = self.dir = self._tmp.name
        write_pdf(os.path.join(d, "a1.pdf"), APPENDIX_1_PAGES)
        write_pdf(os.path.join(d, "a3.pdf"), APPENDIX_3_PAGES)
        write_json(os.path.join(d, "i1.json"), INDEX_1)
        write_json(os.path.join(d, "i3.json"), INDEX_3)
        with io.open(os.path.join(d, "honbun.md"), "w", encoding="utf-8") as f:
            f.write(MD)

    def tearDown(self):
        self._tmp.cleanup()

    def j(self, name):
        return os.path.join(self.dir, name)

    def argv(self, extra=()):
        return ["--honbun-md", self.j("honbun.md"),
                "--source-index", f"{self.j('i1.json')}:{self.j('a1.pdf')}",
                "--source-index", f"{self.j('i3.json')}:{self.j('a3.pdf')}",
                "--out-appendix", self.j("out.pdf"),
                "--out-index", self.j("out_index.json"), *extra]

    def run_build(self, extra=()):
        return ER.build(ER.parse_args(self.argv(extra)))

    def page_texts(self):
        import fitz
        import unicodedata

        doc = fitz.open(self.j("out.pdf"))
        try:
            return [unicodedata.normalize("NFKC", p.get_text()) for p in doc]
        finally:
            doc.close()

    # ---- 土台 ----
    def test_00_bundles_pages_in_appendix_then_page_order(self):
        """**付録番号 → 元のページ番号**の順に並ぶ(2026-09-29 に「印の出た順」から変えた)。

        変えた理由(司令塔の ⑥ が実物で見つけた D7): 本編が「局面で見る」で付録 3 を指し、
        あとの節で付録 1 を指すと、束ねた付録が **分かれ道 → 形勢の流れ → 最後の局面** の順になり、
        **表紙の表の順(付録 1 → 付録 3)と食い違った。**顧客は表紙の順でページを探す。
        実物(4 人目)は**付録番号順**(付録 1 → 3 → 4)。
        **どのページを入れるかは変わらない**(本編が指すページだけ)― 順だけが変わる。
        """
        bundled = self.run_build()
        self.assertEqual(bundled["boardsDrawn"], 2)
        self.assertFalse(bundled["hasCover"])
        self.assertEqual(bundled["appendixPages"], [1, 2, 3, 4])
        # この土台は付録 1 の p3・p2 と付録 3 の p3・p2 をこの順で指している(印の順)。
        # **元のページ番号の昇順**に並ぶ。
        self.assertEqual(bundled["sourcePages"], {"付録1": [2, 3], "付録3": [2, 3]})
        # **付録 1 の 2 枚が先、付録 3 の 2 枚が後**(付録番号の順)。
        by_page = {p: label for label, p in bundled["outputPositions"].items()}
        self.assertEqual(sorted(by_page), [1, 2, 3, 4])

    def test_00b_the_appendix_number_must_be_readable(self):
        """**付録の名前から番号が取れなければ落ちる**(黙って並び順を諦めない)。"""
        with self.assertRaises(ER.ExitRenderError):
            ER.appendix_number("付録おまけ")
        self.assertEqual(ER.appendix_number("付録3"), 3)

    # **抜いたページに本当にその局面・節があるか**(索引が合っていても、抜くページを間違えれば無い)。
    def test_01_extracted_pages_contain_the_marks(self):
        bundled = self.run_build()
        texts = self.page_texts()
        want = {"1/40 付録1": "40 手目", "5/59 付録3 3 分": "59 手目",
                "付録1/形勢の流れ": "形勢の流れ", "付録3/分かれ道": "分かれ道"}
        for label, page in bundled["outputPositions"].items():
            self.assertIn(want[label], texts[page - 1], f"{label} → 出力 p{page}")

    # **組版が書いた値をそのまま写しているか**(1 バイトでも変えたら門が落とす側だが、書く側でも見る)。
    def test_02_source_index_values_are_copied_verbatim(self):
        bundled = self.run_build()
        self.assertEqual(bundled["付録1"]["positions"], INDEX_1["positions"])
        self.assertEqual(bundled["付録1"]["sections"], INDEX_1["sections"])
        self.assertEqual(bundled["付録3"]["positions"], INDEX_3["positions"])

    # 同じページを 2 回指しても 1 枚だけ入れる。
    def test_03_same_page_twice_is_one_sheet(self):
        with io.open(self.j("honbun.md"), "w", encoding="utf-8") as f:
            f.write("<!-- pos: 1/40 付録1 -->\n\n<!-- pos: 1/40 付録1 -->\n")
        bundled = self.run_build()
        self.assertEqual(len(bundled["appendixPages"]), 1)
        self.assertEqual(bundled["boardsDrawn"], 2, "印は 2 件・ページは 1 枚")
        # **PDF そのものを数える。**索引の辞書だけを見ると、重複除去を外しても
        # 鍵が 1 つのままなので試験が通ってしまう(校正でここが「覆われていない」と出た)。
        self.assertEqual(len(self.page_texts()), 1, "PDF に 2 枚入っていないか")

    # ---- 変異(落ちなければならないもの) ----
    def test_04_mark_not_in_source_index(self):
        with io.open(self.j("honbun.md"), "w", encoding="utf-8") as f:
            f.write("<!-- pos: 9/99 付録1 -->\n")
        with self.assertRaises(ER.ExitRenderError) as e:
            self.run_build()
        self.assertIn("局面 9/99 が無い", str(e.exception))

    def test_05_appendix_not_passed(self):
        with io.open(self.j("honbun.md"), "w", encoding="utf-8") as f:
            f.write("<!-- pos: 1/40 付録2 -->\n")
        with self.assertRaises(ER.ExitRenderError) as e:
            self.run_build()
        self.assertIn("その索引が渡されていない", str(e.exception))

    def test_06_section_not_in_source_index(self):
        with io.open(self.j("honbun.md"), "w", encoding="utf-8") as f:
            f.write("<!-- sec: 付録1/知らない節 -->\n")
        with self.assertRaises(ER.ExitRenderError) as e:
            self.run_build()
        self.assertIn("節「知らない節」が無い", str(e.exception))

    def test_07_index_points_past_end_of_pdf(self):
        broken = dict(INDEX_1, positions={"1/40": 99, "2/70": 4})
        write_json(self.j("i1.json"), broken)
        with self.assertRaises(ER.ExitRenderError) as e:
            self.run_build()
        self.assertIn("PDF は 4 ページ", str(e.exception))

    def test_08_group_missing_for_grouped_appendix(self):
        # 付録 3 は組つきの鍵。組を書かない印は落とす。
        with io.open(self.j("honbun.md"), "w", encoding="utf-8") as f:
            f.write("<!-- pos: 5/59 付録3 -->\n")
        with self.assertRaises(ER.ExitRenderError) as e:
            self.run_build()
        self.assertIn("組が要る", str(e.exception))

    def test_09_same_appendix_index_twice(self):
        argv = self.argv(["--source-index", f"{self.j('i1.json')}:{self.j('a1.pdf')}"])
        with self.assertRaises(ER.ExitRenderError) as e:
            ER.build(ER.parse_args(argv))
        self.assertIn("索引が 2 本渡されている", str(e.exception))

    def test_10_unknown_appendix_name(self):
        write_json(self.j("i1.json"), dict(INDEX_1, appendix="付録9"))
        with self.assertRaises(ER.ExitRenderError) as e:
            self.run_build()
        self.assertIn("知らない付録", str(e.exception))

    def test_11_no_source_index_at_all(self):
        with self.assertRaises(ER.ExitRenderError) as e:
            ER.parse_args(["--honbun-md", self.j("honbun.md"),
                           "--out-appendix", self.j("out.pdf"), "--out-index", self.j("out_index.json")])
        self.assertIn("--source-index を 1 本以上", str(e.exception))

    def test_13_dev_section_marks_are_ignored(self):
        """**「書いた側の記録(顧客には見せない)」の中の印は拾わない。**
        2026-09-28 の監査が実際に再現した穴 ― 外さないと、**顧客に見えない下書きのために
        付録のページを抜く**。`check_answer.strip_dev_section` をそのまま呼ぶ形で直した。"""
        with io.open(self.j("honbun.md"), "w", encoding="utf-8") as f:
            f.write("".join([
                "# 本文\n\n",
                "<!-- pos: 1/40 付録1 -->\n\n",
                "## 書いた側の記録(顧客には見せない)\n\n",
                "TODO: 70 手目も見せるか検討中\n",
                "<!-- pos: 2/70 付録1 -->\n",
                "<!-- sec: 付録3/分かれ道 -->\n",
            ]))
        bundled = self.run_build()
        # 本文の 1 件だけが束ねられる(dev 節の 2 件は拾わない)。
        self.assertEqual(list(bundled["outputPositions"]), ["1/40 付録1"])
        self.assertEqual(len(self.page_texts()), 1, "dev 節のためにページを抜いていないか")
        self.assertEqual(bundled["boardsDrawn"], 1)
        self.assertEqual(bundled["sourcePages"], {"付録1": [3]})

    def test_12_cover_is_placed_first(self):
        bundled = self.run_build(["--cover", f"{self.j('a1.pdf')}:1"])
        self.assertTrue(bundled["hasCover"])
        self.assertIn("付録 1 の 1 ページ", self.page_texts()[0])
        # 表紙を足したぶん、印の指す出力ページが 1 つずれる。
        self.assertEqual(min(bundled["outputPositions"].values()), 2)


if __name__ == "__main__":
    unittest.main()
