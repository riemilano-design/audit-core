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



def strings_outside_docstrings(path):
    """その py ファイルの**文字定数**(docstring は除く)。

    **docstring を除くのがこの関数の全部。**2026-09-29 に 5 回続けて踏んだ型 ―
    「語を写していないこと」を字面や文字定数で見ると、**なぜ外したかを書いた説明文が当たる。**
    コメント(`#`)は `ast` に残らないので、除くのは docstring だけでよい。
    """
    with io.open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", None) or []
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
               and isinstance(body[0].value.value, str):
                docs.add(id(body[0].value))
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs]


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



class PositionsInSectionTest(unittest.TestCase):
    """`exit_index.positions_in_section`(束に入る局面を節ごとに数える 1 か所。P-179)。

    表紙が「この冊子に載せているのは N 局面」と言う N を出す。**2 つのふるいが両方効くこと**を測る:
    (1) 束に入るページに乗っていること (2) その節のページの範囲に在ること。
    """

    # 付録 3 の形(組 → 局/手 → ページ)。節は 4 ページ目から 29 ページ目まで。
    INDEX = {"appendix": "付録3",
             "sections": {"読み方": 1, "最後の局面": 2, "分かれ道": 4, "通して見えたこと": 30},
             "positions": {"3 分": {"1/10": 2, "5/20": 5, "6/30": 5, "7/40": 20, "8/50": 31}}}
    # 付録 1 の形(平ら)も受ける。
    FLAT = {"appendix": "付録1", "sections": {"形勢の流れ": 2, "そのほかの局": 20},
            "positions": {"1/40": 3, "2/70": 4, "3/90": 21}}

    def test_q1_counts_only_pages_in_the_bundle(self):
        self.assertEqual(EI.positions_in_section(self.INDEX, [5, 20], "分かれ道"), 3)
        self.assertEqual(EI.positions_in_section(self.INDEX, [5], "分かれ道"), 2)
        self.assertEqual(EI.positions_in_section(self.INDEX, [], "分かれ道"), 0)

    def test_q2_counts_only_pages_inside_the_section(self):
        """節の外のページは、束に入っていても数えない。

        2 ページ目は「最後の局面」、31 ページ目は「通して見えたこと」の側。
        """
        self.assertEqual(EI.positions_in_section(self.INDEX, [2, 5, 31], "分かれ道"), 2)
        self.assertEqual(EI.positions_in_section(self.INDEX, [2], "最後の局面"), 1)

    def test_q3_the_last_section_has_no_upper_edge(self):
        self.assertEqual(EI.positions_in_section(self.INDEX, [31], "通して見えたこと"), 1)

    def test_q4_a_flat_index_works_too(self):
        """付録 1 の鍵は組を持たない(平ら)。**両方の形を受ける。**"""
        self.assertEqual(EI.positions_in_section(self.FLAT, [3, 4], "形勢の流れ"), 2)
        self.assertEqual(EI.positions_in_section(self.FLAT, [21], "そのほかの局"), 1)

    def test_q5_an_unknown_section_is_an_error(self):
        """知らない節は落とす(黙って 0 と言わない ― 0 は「無かった」と読まれる)。"""
        with self.assertRaises(ValueError):
            EI.positions_in_section(self.INDEX, [5], "無い節")

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

    def test_03b_the_helper_agrees_with_what_build_bundled(self):
        """**表紙が使う `bundled_source_pages` と、束ねが実際に抜いたページが一致すること**(P-179)。

        表紙は「この冊子に載せているのは N 局面」と言うために**束ねる前に**ページを知る必要がある。
        判定が 2 か所になると、**表紙の数と束の中身が食い違う**(顧客が数えて合わない)。
        だから**同じ入力で両方を出して比べる** ― これが食い違ったら、どちらかが写しになっている。
        """
        bundled = self.run_build()
        indexes = {"付録1": INDEX_1, "付録3": INDEX_3}
        with io.open(self.j("honbun.md"), encoding="utf-8") as f:
            md = f.read()
        self.assertEqual(ER.bundled_source_pages(md, indexes), bundled["sourcePages"])

    def test_03c_asking_for_one_appendix_gives_only_that_one(self):
        """1 つの付録だけを聞ける(表紙は付録 3 の数だけが要る)。"""
        indexes = {"付録1": INDEX_1, "付録3": INDEX_3}
        with io.open(self.j("honbun.md"), encoding="utf-8") as f:
            md = f.read()
        only = ER.bundled_source_pages(md, indexes, appendix="付録3")
        self.assertEqual(sorted(only), ["付録3"])
        self.assertEqual(only["付録3"], [2, 3])

    def test_03d_strict_false_skips_a_mark_it_cannot_resolve(self):
        """`strict=False`(表紙だけが使う)は引けない印を数に入れない。**既定は落とす。**

        落とすことは `build()` が同じ実行で行う(順は 表紙 → 本編 → 束ね)ので、
        黙って通る道にはならない。
        """
        thin = {"付録3": {"appendix": "付録3", "positions": {}, "sections": {}}}
        with io.open(self.j("honbun.md"), encoding="utf-8") as f:
            md = f.read()
        with self.assertRaises(ER.ExitRenderError):
            ER.bundled_source_pages(md, thin, appendix="付録3")
        self.assertEqual(ER.bundled_source_pages(md, thin, appendix="付録3", strict=False), {})

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



class NeighbourPromiseTest(unittest.TestCase):
    """**束ねたページが、束に入っていない隣のページを約束していないこと**(P-171。2026-09-29)。

    3 周目の批評席 (a) が実物で挙げ、私が数え直した: 付録 1 の折れ線のページが
    「色のついた枠は、次のページから 1 局ずつ見ていく局です」と書き、**1 局ずつのページは
    束のどこにも無かった。**4 周目の実物でも残っていた(付録 1 は元の 2 ページ目だけ、
    付録 3 は元の 6・20・21 ページ目 ― 6 ページ目の「ここから先は」の次は 20 ページ目)。
    """

    PAGES = [["付録 1 の 1 ページ", "読み方"],
             ["付録 1 の 2 ページ", "形勢の流れ", "色のついた枠は、次のページから見ていく局です。"],
             ["付録 1 の 3 ページ", "40 手目の局面"],
             ["付録 1 の 4 ページ", "70 手目の局面"]]

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        write_json(self.j("i1.json"), INDEX_1)

    def tearDown(self):
        self._tmp.cleanup()

    def j(self, name):
        return os.path.join(self.dir, name)

    def build(self, pages, md):
        write_pdf(self.j("a1.pdf"), pages)
        with io.open(self.j("honbun.md"), "w", encoding="utf-8") as f:
            f.write(md)
        return ER.build(ER.parse_args([
            "--honbun-md", self.j("honbun.md"),
            "--source-index", f"{self.j('i1.json')}:{self.j('a1.pdf')}",
            "--out-appendix", self.j("out.pdf"),
            "--out-index", self.j("out_index.json")]))

    ONLY_THE_GRAPH = "# 試し\n\n## 数え方\n\n<!-- sec: 付録1/形勢の流れ -->\n"
    GRAPH_AND_NEXT = ("# 試し\n\n## 数え方\n\n<!-- sec: 付録1/形勢の流れ -->\n\n"
                      "<!-- pos: 1/40 付録1 -->\n")

    def test_n1_the_promise_without_the_promised_page_stops(self):
        """約束したページを束ねていないと**止まる**(嘘の冊子を出さない)。"""
        with self.assertRaises(ER.ExitRenderError) as cm:
            self.build(self.PAGES, self.ONLY_THE_GRAPH)
        msg = str(cm.exception)
        self.assertIn("次のページ", msg)
        self.assertIn("付録1 の元の 2 ページ目", msg)
        self.assertIn("3 ページ目を束ねていない", msg)

    def test_n2_no_pdf_is_written_when_it_stops(self):
        """**落ちたときに PDF を残さない。**出力を読んで判定すると、先に書くしかなくなり、
        **嘘のページを約束した冊子がフォルダに残る**(次の段がそれを拾う)。"""
        with self.assertRaises(ER.ExitRenderError):
            self.build(self.PAGES, self.ONLY_THE_GRAPH)
        self.assertFalse(os.path.exists(self.j("out.pdf")), "落ちたのに PDF が残っている")

    def test_n3_the_promise_with_the_promised_page_passes(self):
        """**校正**: 約束したページ(元の 3 ページ目)も束ねれば通る ―
        検査が何にでも落ちるのではないこと。"""
        bundled = self.build(self.PAGES, self.GRAPH_AND_NEXT)
        self.assertEqual(bundled["sourcePages"], {"付録1": [2, 3]})

    def test_n4_the_same_page_without_the_phrase_passes(self):
        """**校正**: 同じ束ね方でも、言い方を外してあれば通る
        (= 実際の直し方の 2 つ目。組版から語を外す)。"""
        pages = [list(p) for p in self.PAGES]
        pages[1] = ["付録 1 の 2 ページ", "形勢の流れ", "色のついた枠は、形勢が大きく動いた局です。"]
        bundled = self.build(pages, self.ONLY_THE_GRAPH)
        self.assertEqual(bundled["sourcePages"], {"付録1": [2]})

    def test_n5_a_line_break_inside_the_phrase_is_still_found(self):
        """**改行で割れていても見つかる。**`fitz` は「次のページか / ら」のように行で割る
        ― 割れた字面をそのまま探すと、**検査が黙る。**"""
        pages = [list(p) for p in self.PAGES]
        pages[1] = ["付録 1 の 2 ページ", "形勢の流れ", "色のついた枠は、次のペ", "ージから見ていく局です。"]
        with self.assertRaises(ER.ExitRenderError):
            self.build(pages, self.ONLY_THE_GRAPH)

    def test_n6_pointing_backwards_needs_the_page_before(self):
        """前を指す言い方は**前のページ**を要求する(向きを 1 つにしていない)。"""
        pages = [list(p) for p in self.PAGES]
        pages[1] = ["付録 1 の 2 ページ", "形勢の流れ", "前のページの表と見比べてください。"]
        with self.assertRaises(ER.ExitRenderError) as cm:
            self.build(pages, self.ONLY_THE_GRAPH)
        self.assertIn("1 ページ目を束ねていない", str(cm.exception))

    def test_n7_the_phrases_live_in_one_place(self):
        """語は `exit_index.NEIGHBOUR_PROMISES` の 1 か所。**束ねる道具に写しを持たない**
        (片方だけ足すと、検査と組版が別の語を見る ― P-111 の病気)。

        **字面ではなく `ast` で文字定数を見る** ― 説明のコメントに語を書くと字面の試験は当たる。
        """
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exit_render.py")
        hits = sorted({s for s in strings_outside_docstrings(path)
                       for p in EI.NEIGHBOUR_PROMISES if p in s})
        self.assertEqual(hits, [], f"exit_render.py が語を写している: {hits}")

    def test_n8_the_two_bundled_renderers_do_not_promise_a_neighbour(self):
        """**束ねられる付録を組む 2 本に、隣を指す言い方が無いこと**(2026-09-29 の直し)。

        付録 1 = `_mid.py`(`build.sh` が `render_main.py` に連結する断片)、
        付録 3 = `render_direct.py`。**この 2 本だけ**が束ねられる(`APPENDIX_SECTIONS`)。
        **`ast` の文字定数だけを見る** ― 両方とも、なぜ外したかを**コメントに語で書いてある。**
        """
        here = os.path.dirname(os.path.abspath(__file__))
        for name in ("_mid.py", "render_direct.py"):
            hits = sorted({s for s in strings_outside_docstrings(os.path.join(here, name))
                           for p in EI.NEIGHBOUR_PROMISES if p in s})
            self.assertEqual(hits, [], f"{name} が隣のページを約束している: {hits}")

    def test_n9_the_helper_really_drops_docstrings(self):
        """**校正**: この助けが docstring を落とし、ふつうの文字定数は落とさないこと。

        落としすぎれば n7・n8 は**何も見ていない試験**になる(常に緑)。
        """
        import tempfile as _t
        with _t.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write('"""次のページ(docstring)"""\n'
                    "def g():\n"
                    '    """次のページ(関数の docstring)"""\n'
                    '    return "次のページ(ふつうの定数)"\n')
            path = f.name
        self.addCleanup(os.unlink, path)
        self.assertEqual(strings_outside_docstrings(path), ["次のページ(ふつうの定数)"])

if __name__ == "__main__":
    unittest.main()
