# -*- coding: utf-8 -*-
# check_structure.py の試験。**変異試験**(STEP CUSTOMER-EXIT ④、司令塔の条件 3):
# 門が「落とすはずのもの」を本当に落とすかを、1 本ずつ変異させて測る。
# **落ちない変異が 1 本でもあれば、その項目は門ではない。**
#
# check_answer_test.py・check_delivery_test.py・answer_facts_test.py と同じ流儀:
# pytest 等の外部ライブラリは使わず標準ライブラリ unittest だけ。gitignore の実データは読まず、
# 材料は一時フォルダに書く**合成の** md・PDF(fitz で作る)。
#
# **なぜ合成なのか**: 実物(4 人目・3 人目の納品)には `page_index.json` も `<!-- pos: -->` も無い
# (どちらもこの段が新しく要求するもの)。実物では土台が作れないので、正本の 30 ページの形に合わせた
# 最小の一式をここで組む。
#
# 実行: `python3 -X utf8 scripts/playtest/report-pdf/check_structure_test.py`
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_structure as CS  # noqa: E402

# **商品の範囲の 1 段落は、わざと 2 行に折って置く。**実物の組版は文を行に折るので、折れていない土台で
# 測ると「折れた実物では通らない」門を通してしまう(最初の実測でここが落ち、`squeeze` を足した)。
# **実物でも同じ形を確かめた**: 4 人目の送付用 p1 は `この\n冊子は、…` と折れている(P-114)。
SCOPE_WRAPPED = ["この冊子は、エンジンの解析と機械の集計から、次の 20 局で",
                 "確かめる仮説を出すものです。"]

# 本人用 5 ページ。最後が対応表(見本用では抜くページ)。
HONBUN_PAGES = [
    ["合成材料の冊子(変異試験)"] + SCOPE_WRAPPED,
    ["ひとことで", "3 のうち 3 局は、時計の上で持ち時間に到達しています。"],
    ["局面で見る", "盤は 2 つ。"],
    ["試せること / 数え方", "分母は 20 局です。"],
    ["対応表", "局の番号と付録のページのつながり。"],
]
MAPPING_PAGE_INDEX = 4  # 0 起算
APPENDIX_BODY_PAGES = 20

# 行動は 2 本(M8・M9)。**1 本では「表の行を 1 本減らす」変異が「表が無い」と区別できない。**
ACTION_LINE_1 = "<!-- menu: M8 -->この 1 つだけを先に試してみては。\n"
ACTION_LINE_2 = "<!-- menu: M9 -->中盤の消費を目安にしてみては。\n"
ACTION_SECTION = "## 試せること\n\n" + ACTION_LINE_1 + "\n" + ACTION_LINE_2
COUNT_SECTION = "## 数え方\n\n分母は 20 局です。\n"

# 答え合わせの表(項目 6)。**1 行 = 1 行動**、印はちょうど 1 つ。
# 「今の値」の数は材料にある数だけを書く(`check_answer` の検査 1 が全行を見る)。
VERIFY_ROW_1 = "| <!-- menu: M8 -->1 つだけ先に試す | 時計で終わる局が減る | 3 局 |\n"
VERIFY_ROW_2 = "| <!-- menu: M9 -->中盤の消費を目安にする | 中盤の消費が中央値へ寄る | 3 局 |\n"
VERIFY_SECTION = "".join([
    "## 次の 20 局が来たら、何で答え合わせをするか\n\n",
    "| 試したこと | 動くはずの事実 | 今の値 |\n",
    "|---|---|---|\n",
    VERIFY_ROW_1,
    VERIFY_ROW_2,
])

MD = "".join([
    "# 合成材料の冊子(変異試験)\n\n",
    "".join(SCOPE_WRAPPED) + "\n\n",
    "## ひとことで\n\n",
    "3 のうち 3 局は、時計の上で持ち時間に到達しています。\n\n",
    "## 局面で見る\n\n",
    "<!-- pos: 1/40 付録1 -->\n\n",
    "<!-- pos: 2/70 付録1 -->\n\n",
    ACTION_SECTION,
    "\n",
    VERIFY_SECTION,
    "\n",
    COUNT_SECTION,
    "\n## 対応表\n\n",
    "局の番号と付録のページのつながり。\n",
])

MENU = {"items": [
    # 土台が使う 2 本。どちらも条件が成り立ち、分母(時計上、持ち時間に到達した 3 局)が minN 2 以上。
    {"id": "M8", "stage": "中盤", "minN": 2, "actionCore": "1 つだけ先に試す",
     "evidenceName": "時計上、持ち時間に到達した局", "verifyName": "同じ局の数"},
    {"id": "M9", "stage": "中盤", "minN": 2, "actionCore": "中盤の消費を目安にする",
     "evidenceName": "時計上、持ち時間に到達した局", "verifyName": "同じ局の数"},
    # 変異 6 が使う項目。条件は成り立つが、10 分の組は 1 局しかなく minN 10 に届かない。
    {"id": "M2", "stage": "全体", "minN": 10, "actionCore": "10 分の将棋を混ぜる",
     "evidenceName": "10 分の組の局", "verifyName": "同じ局の数"},
]}


# 組版が書いた索引(`exit_index.py` が書く形)。**付録 1 は `局/手`・付録 3 は `組 → 局/手`。**
SOURCE_INDEX_1 = {"appendix": "付録1", "source": "appendix1.pdf", "pages": 8,
                  "positions": {"1/40": 3, "2/70": 5},
                  "sections": {"読み方": 1, "形勢の流れ": 2}}
SOURCE_INDEX_3 = {"appendix": "付録3", "source": "appendix3.pdf", "pages": 9,
                  "positions": {"3 分": {"5/59": 8}},
                  "sections": {"分かれ道": 6}}

def patient(games, time_up_losses):
    return {
        "summary": {"games": games},
        "overview": {"fell": 5, "early": 0},
        "time": {
            "timeUpLosses": time_up_losses,
            "bySpent": [{"n": 5, "collapsed": 1} for _ in range(4)],
            "afterLongThink": {"afterLongThinkAny": {"n": 8, "collapsed": 2},
                               "quickAfterLongThink": {"n": 6, "collapsed": 3}},
            "phaseSpent": {"otherGames": {"early": 2, "mid": 4},
                           "perGame": [{"timeUpLoss": True, "midSec": 79},
                                       {"timeUpLoss": True, "midSec": 68},
                                       {"timeUpLoss": True, "midSec": 66}]},
        },
        "findings": [],
    }


def write_pdf(path, pages):
    """fitz でページごとに行を置く(check_delivery_test.py と同じ流儀)。"""
    import fitz

    doc = fitz.open()
    try:
        for lines in pages:
            page = doc.new_page()
            y = 72
            for line in lines:
                page.insert_text((72, y), line, fontname="japan", fontsize=11)
                y += 28
        doc.save(path)
    finally:
        doc.close()


def appendix_pages(n_body):
    return [["付録(表紙)"]] + [[f"付録のページ {i}"] for i in range(1, n_body + 1)]


def write_json(path, obj):
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def build_base(out_dir):
    j = lambda name: os.path.join(out_dir, name)
    with io.open(j("honbun.md"), "w", encoding="utf-8") as f:
        f.write(MD)
    write_pdf(j("honbun_personal.pdf"), HONBUN_PAGES)
    write_pdf(j("honbun_sample.pdf"), [p for i, p in enumerate(HONBUN_PAGES) if i != MAPPING_PAGE_INDEX])
    write_pdf(j("appendix.pdf"), appendix_pages(APPENDIX_BODY_PAGES))
    # 付録 1 の材料(`<!-- pos: -->` が指す局面が実在すること)。
    write_json(j("prose.json"), {"1": {"scenes": [{"type": "move", "ply": 40, "text": "x"}]},
                                 "2": {"scenes": [{"type": "still", "ply": 70, "text": "y"}]}})
    write_json(j("patient_min3.json"), patient(20, [{"finalScore": 400}, {"finalScore": 500}, {"finalScore": 600}]))
    write_json(j("patient_min10.json"), patient(1, []))
    write_json(j("answer_menu.json"), MENU)
    # 束ねた索引。**`positions`(上の階層)は束ねた後のページ**で `exit-render` が新しく書く値。
    # **`付録N.positions` は元の付録のページ**で、組版が書いた索引と 1 バイトも違ってはいけない。
    write_json(j("page_index.json"), {
        "boardsDrawn": 2,
        "hasCover": True,
        "appendixPages": list(range(2, APPENDIX_BODY_PAGES + 2)),
        "sourcePages": {"付録1": [2, 3]},
        "outputPositions": {"1/40": 2, "2/70": 3},
        "付録1": {"positions": dict(SOURCE_INDEX_1["positions"]), "sections": dict(SOURCE_INDEX_1["sections"])},
        "付録3": {"positions": {g: dict(d) for g, d in SOURCE_INDEX_3["positions"].items()},
                  "sections": dict(SOURCE_INDEX_3["sections"])},
    })
    # 組版が書いた索引(付録ごとに 1 本)。`exit-render` が束ねる前の値。
    write_json(j("appendix1_page_index.json"), SOURCE_INDEX_1)
    write_json(j("appendix3_page_index.json"), SOURCE_INDEX_3)
    return out_dir


def gate_argv(out_dir):
    j = lambda name: os.path.join(out_dir, name)
    return [out_dir,
            "--honbun-md", j("honbun.md"),
            "--honbun-personal", j("honbun_personal.pdf"),
            "--honbun-sample", j("honbun_sample.pdf"),
            "--appendix", j("appendix.pdf"),
            "--page-index", j("page_index.json"),
            "--patient", j("patient_min3.json"), "--time-limit-sec", "180",
            "--patient", j("patient_min10.json"), "--time-limit-sec", "600",
            "--prose", j("prose.json"),
            "--menu", j("answer_menu.json"),
            "--source-index", j("appendix1_page_index.json"),
            "--source-index", j("appendix3_page_index.json")]


def read_md(d):
    with io.open(os.path.join(d, "honbun.md"), encoding="utf-8") as f:
        return f.read()


def write_md(d, text):
    with io.open(os.path.join(d, "honbun.md"), "w", encoding="utf-8") as f:
        f.write(text)


def read_index(d):
    with io.open(os.path.join(d, "page_index.json"), encoding="utf-8") as f:
        return json.load(f)


class CheckStructureTest(unittest.TestCase):
    """土台を 1 回だけ組み、試験ごとに複製して 1 本ずつ変異させる。"""

    @classmethod
    def setUpClass(cls):
        cls._base_tmp = tempfile.TemporaryDirectory()
        cls.base = build_base(cls._base_tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls._base_tmp.cleanup()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = os.path.join(self._tmp.name, "c")
        shutil.copytree(self.base, self.dir)

    def tearDown(self):
        self._tmp.cleanup()

    def run_gate(self):
        old = sys.stderr
        sys.stderr = captured = io.StringIO()
        try:
            rc = CS.main(gate_argv(self.dir))
        finally:
            sys.stderr = old
        return rc, captured.getvalue()

    def assert_falls(self, phrase):
        rc, out = self.run_gate()
        self.assertEqual(rc, 1, f"変異が落ちなかった(この項目は門ではない)。出力: {out}")
        self.assertIn(phrase, out)

    # ---- 土台 ----
    # 変異を測る前に、土台が rc=0 で通ることを確かめる(通らない土台では変異の意味が無い)。
    def test_00_base_passes(self):
        rc, out = self.run_gate()
        self.assertEqual(rc, 0, out)

    # ---- 司令塔の条件 3 の 7 本 ----
    def test_01_drop_board(self):
        write_md(self.dir, read_md(self.dir).replace("<!-- pos: 2/70 付録1 -->\n\n", ""))
        self.assert_falls("検査 7")

    def test_02_extra_appendix_page(self):
        write_pdf(os.path.join(self.dir, "appendix.pdf"), appendix_pages(APPENDIX_BODY_PAGES + 1))
        self.assert_falls("指していないページが混ざっている")

    def test_03_personal_without_mapping(self):
        write_pdf(os.path.join(self.dir, "honbun_personal.pdf"),
                  [p for i, p in enumerate(HONBUN_PAGES) if i != MAPPING_PAGE_INDEX])
        self.assert_falls("対応表のページが本人用に無い")

    def test_04_sample_keeps_mapping(self):
        write_pdf(os.path.join(self.dir, "honbun_sample.pdf"), HONBUN_PAGES)
        self.assert_falls("対応表のページが見本用に残っている")

    def test_05_drop_section(self):
        write_md(self.dir, read_md(self.dir).replace("## 数え方\n\n", ""))
        self.assert_falls("「数え方」の節が本編に無い")

    def test_06_action_below_min_n(self):
        text = read_md(self.dir)
        self.assertIn(ACTION_LINE_1, text)
        write_md(self.dir, text.replace(ACTION_LINE_1, ACTION_LINE_1 + "\n<!-- menu: M2 -->10 分の将棋を混ぜてみては。\n"))
        self.assert_falls("minN(10)未満")

    def test_07_index_one_past_end(self):
        index = read_index(self.dir)
        index["outputPositions"]["1/40"] = len(appendix_pages(APPENDIX_BODY_PAGES)) + 1
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("索引と PDF の整合")

    # ---- 自分で足した 5 本(上の 7 本が通らない枝) ----
    def test_08_sections_out_of_order(self):
        # 「数え方」と「対応表」を入れ替える(6 節すべてある・並びだけが崩れる)。
        text = read_md(self.dir)
        mapping = "## 対応表\n\n局の番号と付録のページのつながり。\n"
        self.assertIn(COUNT_SECTION + "\n" + mapping, text)
        write_md(self.dir, text.replace(COUNT_SECTION + "\n" + mapping,
                                        mapping + "\n" + COUNT_SECTION))
        self.assert_falls("節の並びが正本の順でない")

    def test_09_board_declared_but_not_drawn(self):
        index = read_index(self.dir)
        index["boardsDrawn"] = 1
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("差し込んだ盤 1 件が合わない")

    def test_10_honbun_six_pages(self):
        pages = HONBUN_PAGES + [["おまけのページ"]]
        write_pdf(os.path.join(self.dir, "honbun_personal.pdf"), pages)
        write_pdf(os.path.join(self.dir, "honbun_sample.pdf"),
                  [p for i, p in enumerate(pages) if i != MAPPING_PAGE_INDEX])
        self.assert_falls("本編(本人用)が 6 ページ")

    def test_11_index_missing_appendix_pages(self):
        index = read_index(self.dir)
        del index["appendixPages"]
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("appendixPages")

    def test_12_scope_sentence_twice(self):
        pages = [list(p) for p in HONBUN_PAGES]
        pages[1] = pages[1] + SCOPE_WRAPPED
        write_pdf(os.path.join(self.dir, "honbun_personal.pdf"), pages)
        write_pdf(os.path.join(self.dir, "honbun_sample.pdf"),
                  [p for i, p in enumerate(pages) if i != MAPPING_PAGE_INDEX])
        self.assert_falls("商品の範囲の 1 段落が 2 か所")

    # ---- 門の行そのものを変異させて分かった不足(1 回目の校正で「D 本人用と見本用のページ数の差を
    # 見ない」が OK で通った)。対応表の判定と**重ならない**形で差だけを崩す 2 本。 ----
    def test_14_page_count_differs_by_two(self):
        # 本人用 5(対応表あり)・見本用 3(対応表と、もう 1 ページを抜く)。
        # 対応表の在り処は正しいままなので、**ページ数の差の行だけ**が落とす。
        write_pdf(os.path.join(self.dir, "honbun_sample.pdf"),
                  [p for i, p in enumerate(HONBUN_PAGES) if i not in (2, MAPPING_PAGE_INDEX)])
        self.assert_falls("差は 1 ページでなければならない")

    def test_15_body_differs_between_personal_and_sample(self):
        # ページ数の差は 1・対応表の在り処も正しいが、**本文が違う**。
        pages = [list(p) for p in HONBUN_PAGES]
        pages[2] = ["局面で見る", "盤は 3 つ。"]
        write_pdf(os.path.join(self.dir, "honbun_sample.pdf"),
                  [p for i, p in enumerate(pages) if i != MAPPING_PAGE_INDEX])
        self.assert_falls("ページ目の本文が本人用と見本用で違う")

    def test_16_three_boards_consistently_drawn(self):
        # 盤を 3 つ宣言し、索引の差し込んだ回数も 3 に揃える。宣言と差し込みは一致するので、
        # **「正本は 2 件」の行だけ**が落とす(test_01 はこの行と不一致の行の両方を鳴らすため、
        # 門の行を 1 本ずつ黙らせる校正で「件数の行は門ではない」と出た ― その穴をふさぐ 1 本)。
        write_md(self.dir, read_md(self.dir).replace(
            "<!-- pos: 2/70 付録1 -->\n", "<!-- pos: 2/70 付録1 -->\n\n<!-- pos: 1/40 付録1 -->\n"))
        index = read_index(self.dir)
        index["boardsDrawn"] = 3
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("正本は 2 件")

    # ---- 2026-09-28 の監査で「覆われていない」と出た 5 行(私は落とす行を**手で並べて**数え、
    # 19 本のうち 5 本を落としていた。以後、校正の一覧は AST で機械に数えさせる) ----
    # どの変異も他の行を同時に鳴らすが、`assert_falls` は**その行の文言**を見るので、
    # 行を黙らせればこの試験だけが落ちる。
    def test_17_sample_over_page_limit(self):
        pages = HONBUN_PAGES + [["おまけ 1"], ["おまけ 2"]]
        write_pdf(os.path.join(self.dir, "honbun_personal.pdf"), pages)
        write_pdf(os.path.join(self.dir, "honbun_sample.pdf"),
                  [p for i, p in enumerate(pages) if i != MAPPING_PAGE_INDEX])
        self.assert_falls("本編(見本用)が 6 ページ")

    def test_18_appendix_over_page_limit(self):
        write_pdf(os.path.join(self.dir, "appendix.pdf"), appendix_pages(APPENDIX_BODY_PAGES + 5))
        self.assert_falls("付録が 26 ページ(上限 25)")

    def test_19_total_over_page_limit(self):
        write_pdf(os.path.join(self.dir, "appendix.pdf"), appendix_pages(APPENDIX_BODY_PAGES + 5))
        self.assert_falls("本人用 + 付録が 31 ページ")

    def test_20_index_missing_boards_drawn(self):
        index = read_index(self.dir)
        del index["boardsDrawn"]
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("boardsDrawn(差し込んだ盤の回数)が無い")

    def test_21_source_page_below_one(self):
        index = read_index(self.dir)
        index["sourcePages"]["付録1"] = [0, 3]
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("ページ番号が 0")

    # ---- 項目 6(答え合わせの表)。承認済み仕様 §4 の 8 項目のうち実装が抜けていた 1 項目
    # (2026-09-28 の監査で発覚)。司令塔の指定は 3 本: 節を落とす / 行を 1 本減らす / 「今の値」を 1 つ変える ----
    def test_22_verify_section_dropped(self):
        write_md(self.dir, read_md(self.dir).replace(VERIFY_SECTION, ""))
        self.assert_falls("「答え合わせ」の節が本編に無い")

    def test_23_verify_table_row_dropped(self):
        # 行動は 2 本のまま、表の行を 1 本だけ落とす。**表が空になるのとは別の落ち方**でなければならない。
        write_md(self.dir, read_md(self.dir).replace(VERIFY_ROW_2, ""))
        self.assert_falls("表に無い行動: ['M9']")

    def test_24_verify_table_value_not_in_materials(self):
        # 「今の値」を材料に無い数に変える。**この道具は値を見ない** ―
        # `check_answer.py` の検査 1 が表の行も含めて全行を見るので、そこで落ちる(二重に判定しない)。
        write_md(self.dir, read_md(self.dir).replace("| 時計で終わる局が減る | 3 局 |",
                                                    "| 時計で終わる局が減る | 99 局 |"))
        self.assert_falls("データに無い数 99")

    def test_25_verify_table_row_without_mark(self):
        # 表に印の無い行を 1 本足す(行動に紐づかない行を混ぜる)。
        write_md(self.dir, read_md(self.dir).replace(
            VERIFY_ROW_2, VERIFY_ROW_2 + "| 印の無い行 | 何かが動く | 3 局 |\n"))
        self.assert_falls("メニューの印が 0 個")

    def test_26_verify_section_without_table(self):
        # 節はあるが**表が無い**(見出しだけ残す)。行を減らすのとも、節を落とすのとも別の落ち方。
        write_md(self.dir, read_md(self.dir).replace(
            VERIFY_SECTION, "## 次の 20 局が来たら、何で答え合わせをするか\n\n次の 20 局で確かめます。\n"))
        self.assert_falls("答え合わせの節に表が無い")

    # ---- 束ねた索引が組版の索引と等しいか(司令塔の条件 2026-09-28。
    # **`exit-render` が黙って書き換える道を閉じる** ― 「書き換えず足すだけ」を機械で確かめる) ----
    def test_27_bundled_value_changed(self):
        # **司令塔が名指しした変異**: 束ねた値を 1 つ変える。
        index = read_index(self.dir)
        index["付録1"]["positions"]["1/40"] = 99
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("値が違う: ['1/40']")

    def test_28_bundled_key_dropped(self):
        # 束ねるときに 1 件落とす(組版は書いたのに、束ねた側に無い)。
        index = read_index(self.dir)
        del index["付録1"]["positions"]["2/70"]
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("束ねた側に無い: ['2/70']")

    def test_29_bundled_key_invented(self):
        # 束ねるときに 1 件でっち上げる(組版が書いていない局面が索引に入る)。
        index = read_index(self.dir)
        index["付録1"]["positions"]["9/99"] = 4
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("組版に無い: ['9/99']")

    def test_30_bundled_section_changed(self):
        # 節の側も同じように見る(局面だけの検査になっていないか)。
        index = read_index(self.dir)
        index["付録3"]["sections"]["分かれ道"] = 1
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("sections が組版の索引と違う")

    def test_31_appendix_missing_from_bundle(self):
        # 付録 1 つを束ねるのを忘れる。
        index = read_index(self.dir)
        del index["付録3"]
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("付録「付録3」が束ねた索引に無い")

    def test_32_source_index_not_passed(self):
        # 組版の索引を 1 本も渡さない(突き合わせずに通す道を閉じる)。
        argv = [a for a in gate_argv(self.dir)]
        drop = {"--source-index"}
        trimmed, i = [], 0
        while i < len(argv):
            if argv[i] in drop:
                i += 2
                continue
            trimmed.append(argv[i])
            i += 1
        old = sys.stderr
        sys.stderr = captured = io.StringIO()
        try:
            rc = CS.main(trimmed)
        finally:
            sys.stderr = old
        self.assertEqual(rc, 1, captured.getvalue())
        self.assertIn("--source-index が 1 本も無い", captured.getvalue())

    def test_33_source_index_appendix_field_missing(self):
        # 組版の索引に appendix の欄が無い(どの付録のものか分からない)。
        src = dict(SOURCE_INDEX_1)
        del src["appendix"]
        write_json(os.path.join(self.dir, "appendix1_page_index.json"), src)
        self.assert_falls("appendix の欄が無い")

    def test_34_same_appendix_twice(self):
        # 同じ付録の索引を 2 本渡す(どちらが正か決められない)。
        write_json(os.path.join(self.dir, "appendix3_page_index.json"), SOURCE_INDEX_1)
        self.assert_falls("の索引が 2 本渡されている")

    def test_35_source_index_file_missing(self):
        # 組版の索引のファイルが無い(パスを渡したのに存在しない)。
        os.remove(os.path.join(self.dir, "appendix1_page_index.json"))
        self.assert_falls("--source-index のファイルが無い")

    def test_36_bundled_appendix_without_source(self):
        # 束ねた索引に、組版の索引が渡されていない付録が入っている
        # (`exit-render` が自分で付録の節を書き足した形)。
        index = read_index(self.dir)
        index["付録2"] = {"positions": {}, "sections": {"分かれ道": 1}}
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("組版の索引が渡されていない付録がある")

    def test_37_old_key_name_remains(self):
        # **改名を門にする**(司令塔の条件 2026-09-28)。上の階層に旧い名前が残っていたら落とす ―
        # これが無いと、旧い名前で書かれたとき `outputPositions` が「無い」だけになり、
        # 索引と PDF の整合の検査が**黙って何も見ない**道が残る。
        index = read_index(self.dir)
        index["positions"] = dict(index["outputPositions"])
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("旧い名前が残っている")

    # ---- 折り返しを越えて数えること自体の試験(最初の実測で見つけた穴) ----
    # 商品の範囲の 1 段落が 2 行に折られていても 1 か所と数える。`squeeze` を外すと
    # この試験と test_00 の両方が落ちる。
    def test_13_scope_survives_line_wrap(self):
        joined = "".join(CS.page_texts(os.path.join(self.dir, "honbun_personal.pdf")))
        self.assertNotIn(CS.SCOPE_SENTENCE, joined, "土台の PDF は折り返されていなければ意味が無い")
        self.assertIn(CS.squeeze(CS.SCOPE_SENTENCE), CS.squeeze(joined))


if __name__ == "__main__":
    unittest.main()
