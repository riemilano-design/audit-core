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

# 冒頭の断り書き 2 文(P-162)。**道具の定数から引く**(写さない) ―
# 写すと、文を直したときに**土台だけが古い文で緑のまま通る**。
OPENING_CAVEATS = [CS.OPENING_NOT_A_JUDGE, CS.OPENING_APPENDIX]

# 本人用 5 ページ。最後が対応表(見本用では抜くページ)。
HONBUN_PAGES = [
    ["合成材料の冊子(変異試験)"] + SCOPE_WRAPPED + OPENING_CAVEATS,
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

# 土台の 3 分の組の局数(`build_base` が書く `patient_min3.json`)。
# 商品の範囲の 1 段落は**この局数で作られる**(D1。`CS.scope_sentence`)。
BASE_GAMES = 20


# 土台の材料の実名(**PDF には 1 か所も入れない** ― 入れると土台が落ちる。項目 11)。
FIXTURE_PERSON = "ぷる"


def patient(games, time_up_losses):
    return {
        # **実名は材料に在る**(冊子に出ていないことを門が見る。項目 11・P-170)。
        "person": FIXTURE_PERSON,
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
    write_json(j("patient_min3.json"), patient(BASE_GAMES, [{"finalScore": 400}, {"finalScore": 500}, {"finalScore": 600}]))
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
    # **本編の索引**(`exit_body.py` が書く)。検査 4 が「差 = 対応表のページ数」を見るのに使う
    # (司令塔の判断 2026-09-29・案 1。P-133)。**PDF の文字からは数えない** ―
    # 対応表が 2 ページに伸びたとき、2 枚目には見出しの語が無い。
    write_json(j("honbun_page_index.json"), {
        "mappingPages": [MAPPING_PAGE_INDEX + 1],
        "personPages": len(HONBUN_PAGES),
        "samplePages": len(HONBUN_PAGES) - 1,
        "boardsDrawn": 2,
    })
    return out_dir


def gate_argv(out_dir):
    j = lambda name: os.path.join(out_dir, name)
    return [out_dir,
            "--honbun-md", j("honbun.md"),
            "--honbun-personal", j("honbun_personal.pdf"),
            "--honbun-sample", j("honbun_sample.pdf"),
            "--appendix", j("appendix.pdf"),
            "--page-index", j("page_index.json"),
            "--honbun-index", j("honbun_page_index.json"),
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
        self.assert_falls("索引が 5 ページを指しているが、本人用は 4 ページ")

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
        self.assert_falls("差は索引が示す対応表の 1 ページでなければならない")

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

    # 上の階層の鍵は**許可一覧**で見る(接頭辞では見ない ― 司令塔の指示 2026-09-28)。
    # 司令塔が名指しした 2 つの形を、それぞれ 1 本ずつ:
    def test_36_appendix_without_source_index(self):
        # (1) **付録名だが、その組版の索引が渡されていない**(`exit-render` が勝手に足した形)。
        index = read_index(self.dir)
        index["付録9"] = {"positions": {}, "sections": {}}
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("上の階層に置いてよくない鍵がある: ['付録9']")

    def test_38_unknown_top_level_key(self):
        # (2) **名前の規則から外れた鍵**。接頭辞で見ていたら「付録」で始まらないので**素通りしていた**。
        index = read_index(self.dir)
        index["foo"] = 1
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("上の階層に置いてよくない鍵がある: ['foo']")

    def test_37_old_key_name_remains(self):
        # **改名を門にする**(司令塔の条件 2026-09-28)。上の階層に旧い名前が残っていたら落とす ―
        # これが無いと、旧い名前で書かれたとき `outputPositions` が「無い」だけになり、
        # 索引と PDF の整合の検査が**黙って何も見ない**道が残る。
        index = read_index(self.dir)
        index["positions"] = dict(index["outputPositions"])
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("旧い名前が残っている")

    def test_39_cover_is_missing(self):
        # **表紙を抜いたら赤**(正本 §8。承認済みの形に表紙が入っている)。
        # 抜けると顧客は「この冊子に入っているもの」の案内を失い、本編から付録のページを辿れなくなる。
        index = read_index(self.dir)
        index["hasCover"] = False
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("付録に表紙が無い")

    def test_40_cover_key_absent_is_also_red(self):
        # **鍵ごと無い場合も赤**(偽を書く道だけ塞いでも、書かない道が残る)。
        index = read_index(self.dir)
        del index["hasCover"]
        write_json(os.path.join(self.dir, "page_index.json"), index)
        self.assert_falls("付録に表紙が無い")

    # ---- 折り返しを越えて数えること自体の試験(最初の実測で見つけた穴) ----
    # 商品の範囲の 1 段落が 2 行に折られていても 1 か所と数える。`squeeze` を外すと
    # この試験と test_00 の両方が落ちる。
    def test_13_scope_survives_line_wrap(self):
        joined = "".join(CS.page_texts(os.path.join(self.dir, "honbun_personal.pdf")))
        sentence = CS.scope_sentence(BASE_GAMES)
        self.assertNotIn(sentence, joined, "土台の PDF は折り返されていなければ意味が無い")
        self.assertIn(CS.squeeze(sentence), CS.squeeze(joined))


    # ---- 項目 11 実名がどこにも無い(P-170。2026-09-29)----
    # **門を通して測る。**関数だけを呼ぶ試験は書いたが、**`main` が呼んでいなければ門ではない** ―
    # 実際に「呼び出しを消す」変異で関数の試験は全部黙った(定義の行に当たっていた)。
    def test_43_a_real_name_in_the_personal_pdf_falls(self):
        """本人用に実名が出たら落ちる(人間の決定: 本人用でも名前で呼ばない)。"""
        pages = [list(p) for p in HONBUN_PAGES]
        pages[2].append(f"{FIXTURE_PERSON} の持ち駒 銀")
        write_pdf(os.path.join(self.dir, "honbun_personal.pdf"), pages)
        write_pdf(os.path.join(self.dir, "honbun_sample.pdf"),
                  [p for i, p in enumerate(pages) if i != MAPPING_PAGE_INDEX])
        # **この検査だけが出す文で見る。**「本人用」だけでは
        # 「本人用と見本用の本文が違う」など別の検査の文にも当たる(実測: 呼び出しを消す変異で黙った)。
        self.assert_falls("本人用の [3] ページ目に顧客の実名が出ている")
        self.assert_falls("見本用の [3] ページ目に顧客の実名が出ている")

    def test_44_a_real_name_only_on_the_mapping_page_still_falls(self):
        """**抜くページに置いても落ちる。**

        人間の決定は「呼ばない」なので、**対応表のページの例外は使わない**
        (見本用から消えても本人用に残るため)。
        """
        pages = [list(p) for p in HONBUN_PAGES]
        pages[MAPPING_PAGE_INDEX].append(f"{FIXTURE_PERSON} さんの局")
        write_pdf(os.path.join(self.dir, "honbun_personal.pdf"), pages)
        self.assert_falls("本人用の [5] ページ目に顧客の実名が出ている")

    def test_45_a_real_name_in_the_appendix_falls(self):
        """付録は 1 冊で本人用にも見本用にも付くので、付録の実名は見本用の一式に乗る。"""
        pages = appendix_pages(APPENDIX_BODY_PAGES)
        pages[2].append(f"上に行くほど {FIXTURE_PERSON} が良く")
        write_pdf(os.path.join(self.dir, "appendix.pdf"), pages)
        self.assert_falls("付録の [3] ページ目に顧客の実名が出ている")

    # ---- 項目 12 呼び方が 1 通り(P-174。2026-09-29)----
    # **門を通して測る**(項目 11 と同じ理由 ― 関数だけを呼ぶ試験では「呼び出しを消す」変異が黙る)。
    def test_46_a_honorific_in_the_appendix_falls(self):
        """**付録が「〜さん」と呼んだら落ちる。**4 周目の実物で出た形そのもの。

        実測(4 周目の封): 本編は「本人」6 か所・「さん」0 か所なのに、
        **付録の 2 ページ目だけ「上に行くほど〇〇さんが良く」**。実名ではないので項目 11 では落ちない。
        """
        pages = appendix_pages(APPENDIX_BODY_PAGES)
        pages[1].append("上に行くほど 〇〇さん が良く、下に行くほど相手が良い")
        write_pdf(os.path.join(self.dir, "appendix.pdf"), pages)
        self.assert_falls("付録の [2] ページ目が顧客を「〜さん」と呼んでいる")

    def test_47_a_honorific_in_the_personal_pdf_falls(self):
        """本編に出ても落ちる(呼び方は 3 冊で 1 通り)。"""
        pages = [list(p) for p in HONBUN_PAGES]
        pages[0].append("〇〇さん の 25 局を調べました")
        write_pdf(os.path.join(self.dir, "honbun_personal.pdf"), pages)
        write_pdf(os.path.join(self.dir, "honbun_sample.pdf"),
                  [p for i, p in enumerate(pages) if i != MAPPING_PAGE_INDEX])
        self.assert_falls("本人用の [1] ページ目が顧客を「〜さん」と呼んでいる")
        self.assert_falls("見本用の [1] ページ目が顧客を「〜さん」と呼んでいる")

    def test_48_a_honorific_split_across_lines_still_falls(self):
        """**行で割れていても落ちる**(`squeeze` を通す ― `fitz` は「〇〇さ / ん」と割る)。"""
        pages = appendix_pages(APPENDIX_BODY_PAGES)
        pages[1] += ["上に行くほど 〇〇さ", "ん が良く"]
        write_pdf(os.path.join(self.dir, "appendix.pdf"), pages)
        self.assert_falls("付録の [2] ページ目が顧客を「〜さん」と呼んでいる")

    def test_49_the_normal_books_pass_this_check(self):
        """**校正**: ふつうの材料(「本人」で呼んでいる)では、この文が出ないこと。

        出てしまうと、この検査は何にでも落ちる番人になる。
        """
        rc, out = self.run_gate()
        self.assertEqual(rc, 0, f"土台が通らない: {out}")
        self.assertNotIn("〜さん", out)

class MappingPagesTest(unittest.TestCase):
    """**差は索引が示す対応表のページ数**(司令塔の判断 2026-09-29・案 1。P-133)。

    前は「差 = 1」に固定していた。**26 局以上の顧客では対応表が 2 ページになる**ので
    (実測: 節がページ先頭から始まる場合 25 行 = 1 ページ・26 行 = 2 ページ)、
    1 に固定すると**その顧客の本編がこの門を通れない**。
    """

    # **土台は 1 回だけ組む**(既存の `CheckStructureTest` と同じ流儀)。
    # 試験ごとに `build_base` を呼ぶと PDF を 3 回組み直すことになり、
    # **`check_structure_test.py` 全体が 5 秒を超えて、vitest の門が時々落ちた**
    # (実測 2026-09-29: 3 回に 1 回・5483ms。揺れではなく時間切れだった)。
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
        buf = io.StringIO()
        err = sys.stderr
        sys.stderr = buf
        try:
            rc = CS.main(gate_argv(self.dir))
        finally:
            sys.stderr = err
        return rc, buf.getvalue()

    def test_40_a_two_page_mapping_section_passes(self):
        """**対応表が 2 ページでも通る**(索引が 2 ページだと言い、差も 2 のとき)。"""
        j = lambda name: os.path.join(self.dir, name)
        pages = list(HONBUN_PAGES)
        # 対応表のページの直後に「つづき」のページを足す(本人用は 1 枚増える)
        # 1 ページは行の一覧(`HONBUN_PAGES` の要素は行のリスト)。
        # 対応表の「つづき」は、**見出しの行を持たないページ**にする ―
        # 実物でも 2 枚目に見出しは出ない(だから検査 4 は文字で数えない)。
        extra = [line for line in pages[MAPPING_PAGE_INDEX] if "対応表" not in line] or ["つづき"]
        pages.insert(MAPPING_PAGE_INDEX + 1, extra)
        write_pdf(j("honbun_personal.pdf"), pages)
        write_pdf(j("honbun_sample.pdf"),
                  [x for i, x in enumerate(pages)
                   if i not in (MAPPING_PAGE_INDEX, MAPPING_PAGE_INDEX + 1)])
        write_json(j("honbun_page_index.json"), {
            "mappingPages": [MAPPING_PAGE_INDEX + 1, MAPPING_PAGE_INDEX + 2],
            "personPages": len(pages), "samplePages": len(pages) - 2, "boardsDrawn": 2})
        rc, out = self.run_gate()
        self.assertEqual(rc, 0, out)

    def test_41_a_missing_index_falls(self):
        """**索引が無ければ検査 4 が落ちる。**黙って「差は 1」に戻らない
        (戻れば 26 局以上の顧客で嘘になる)。
        """
        j = lambda name: os.path.join(self.dir, name)
        write_json(j("honbun_page_index.json"), {"personPages": 5})
        rc, out = self.run_gate()
        self.assertEqual(rc, 1)
        self.assertIn("本編の索引に mappingPages が無い", out)

    def test_42_an_index_pointing_at_a_page_without_the_section_falls(self):
        """**索引が指すページに対応表の節が無ければ落ちる。**

        索引だけを信じると、**別のページを抜いても「できた」ことになる**。
        """
        j = lambda name: os.path.join(self.dir, name)
        write_json(j("honbun_page_index.json"), {
            "mappingPages": [1], "personPages": len(HONBUN_PAGES),
            "samplePages": len(HONBUN_PAGES) - 1, "boardsDrawn": 2})
        rc, out = self.run_gate()
        self.assertEqual(rc, 1)
        self.assertIn("索引が指す 1 ページに対応表の節が無い", out)


class ScopeSentenceTest(unittest.TestCase):
    """**商品の範囲の 1 段落は局数で変わる**(D1。2026-09-29)。"""

    def test_s1_the_sentence_carries_the_game_count(self):
        """局数を変えれば文も変わる。

        **土台の局数(20)以外で測る。**土台だけで測っていたら、
        **「いつでも 20 で作る」変異が緑のまま通った**(校正で実測)。
        """
        self.assertIn("次の 25 局で確かめる", CS.scope_sentence(25))
        self.assertIn("次の 7 局で確かめる", CS.scope_sentence(7))
        self.assertNotEqual(CS.scope_sentence(25), CS.scope_sentence(20))

    def test_s2_the_check_uses_the_given_count(self):
        """門は**渡された局数で作った文**を探す(違う局数の文は 0 か所になる)。"""
        personal = ["".join(CS.opening_paragraph(25, (("3 分", 25),), "2026-09-29"))]
        problems = []
        CS.check_scope_and_mapping(personal, 25, problems)
        self.assertEqual(problems, [])
        problems = []
        CS.check_scope_and_mapping(personal, 20, problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("20 局", problems[0])

    def test_s3_the_two_caveats_are_required(self):
        """**冒頭の断り書き 2 文がちょうど 1 か所**(P-162)。

        **とくに「手の良し悪しを判定するものではありません。」** ―
        2 周目の冊子はこの文が本編に無いまま顧客に出た(付録の表紙には在った)。
        **無ければ落ちる**ことをここで測る。
        """
        full = CS.opening_paragraph(25, (("3 分", 25),), "2026-09-29")
        for dropped in (CS.OPENING_NOT_A_JUDGE, CS.OPENING_APPENDIX):
            personal = ["".join(x for x in full if x != dropped)]
            problems = []
            CS.check_scope_and_mapping(personal, 25, problems)
            self.assertEqual(len(problems), 1, problems)
            self.assertIn(dropped, problems[0])
        # 2 回出ても落ちる(片方だけ直した版が混ざるのを防ぐ)。
        problems = []
        CS.check_scope_and_mapping(["".join(full) + CS.OPENING_APPENDIX], 25, problems)
        self.assertEqual(len(problems), 1, problems)

    def test_s4_two_groups_name_both(self):
        """**組が 2 つなら 6 文**(4 人目の実物と同じ並び)。和が合わなければ落ちる。"""
        got = CS.opening_paragraph(20, (("3 分切れ負け", 18), ("10 分 + 30 秒", 2)), "2026-09-25")
        self.assertEqual(len(got), 6)
        self.assertEqual(got[0], "3 分切れ負け 18 局と、10 分 + 30 秒 2 局を、"
                                 "1 手ずつ将棋エンジンで調べました(2026-09-25)。")
        self.assertEqual(got[5], "以下の数は、断りが無ければ 3 分切れ負けの 18 局のものです。")
        with self.assertRaises(CS.CheckStructureError):
            CS.opening_paragraph(20, (("3 分切れ負け", 18),), "2026-09-25")
        with self.assertRaises(CS.CheckStructureError):
            CS.opening_paragraph(20, (("3 分切れ負け", 20),), "2026/09/25")


class NameAgreesTest(unittest.TestCase):
    """**本編と付録で名前が同じ**(D5。2026-09-29)。

    見本用は本人用からページを抜いたもので名前を分けられず、付録は 1 冊で両方に付く ―
    **付録に実名が乗れば見本用の一式に乗る。**実物で出た(付録 p4「上に行くほど〈実名〉が良く」)。
    """

    def test_n1_a_name_only_in_the_appendix_falls(self):
        problems = []
        CS.check_name_agrees(["本編は〇〇さんの話"], ["付録は ぷる の話"], "ぷる", problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("付録", problems[0])
        # **落ちたときほど、ログに名前そのものを残さない**(2026-09-29。P-170)。
        self.assertNotIn("ぷる", problems[0])

    def test_n1b_a_name_only_in_the_body_falls(self):
        """**逆向きも落とす**(2026-09-29。P-170)。

        もとは「付録に在って本編に無い」だけを見ていたので、**実物で出た向きが通った** ―
        本編の盤の名札に実名が入り、付録は「本人」だったため、この検査は黙った。
        docstring は「本編と付録で名前が違うこと」を禁じると書いていたのに、
        実装はその片側だけだった。
        """
        problems = []
        CS.check_name_agrees(["本編は ぷる の話"], ["付録は〇〇さんの話"], "ぷる", problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("本編", problems[0])
        self.assertNotIn("ぷる", problems[0])

    def test_n2_the_same_name_in_both_passes(self):
        """**実名そのものを禁じない** ― 本人用に本人の名前を出すのは正しい。"""
        problems = []
        CS.check_name_agrees(["本編は ぷる の話"], ["付録も ぷる の話"], "ぷる", problems)
        self.assertEqual(problems, [])

    def test_n3_a_name_in_neither_passes(self):
        problems = []
        CS.check_name_agrees(["本編は〇〇さん"], ["付録も〇〇さん"], "ぷる", problems)
        self.assertEqual(problems, [])

    def test_n4_line_wrap_does_not_hide_the_name(self):
        """折り返しを越えて探す(`squeeze`。門の他の検査と同じ流儀)。"""
        problems = []
        CS.check_name_agrees(["本編は〇〇さん"], ["上に行くほど ぷ\nる が良く"], "ぷる", problems)
        self.assertEqual(len(problems), 1, problems)

    def test_n5_the_appendix_render_can_be_told_the_name(self):
        """**付録 1 の組版が表示名を受け取れること。**

        受け取れなければ、門が落としたまま**直せない**(門が仕事を止める)。
        `_mid.py` は `build.sh` の断片で import できないので、**中身を読んで確かめる**。
        校正で黙ったので足した(2026-09-29)。
        """
        here = os.path.dirname(os.path.abspath(__file__))
        with io.open(os.path.join(here, "_mid.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertIn("REPORT_DISPLAY_NAME", src,
                      "付録 1 の組版が表示名を受け取れない(本編と名前を揃えられない)")
        # 既定は材料の `person`(渡さなければ出力は変わらない)。
        self.assertIn('or m["person"]', src)


class NoRealNameTest(unittest.TestCase):
    """**実名が 3 冊のどこにも無いこと**(2026-09-29 の人間の決定。P-170)。

    決定は「本人用でも顧客を名前で呼ばない」 ― 盤の名札も本文も「本人」。
    実物で出た: 盤の名札「〈実名〉の持ち駒」が**本人用にも見本用にも**入った(各 2 か所)。
    **見本用は他人に見せる冊子**なので、他人に顧客の実名が出る。
    """

    def test_r1_a_name_in_the_personal_book_falls(self):
        """**陽性対照から始める。**実名を入れた本人用で赤くなること。"""
        problems = []
        CS.check_no_real_name(["1 ページ目", "ぷる の持ち駒"], ["1 ページ目"], ["付録"], "ぷる", problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("本人用", problems[0])
        self.assertIn("[2]", problems[0], "何ページ目かを言わない")

    def test_r2_a_name_in_the_sample_book_falls(self):
        """**見本用も別に見る** ― ページの抜き方が変わったときに黙って通らないため。"""
        problems = []
        CS.check_no_real_name(["1 ページ目"], ["ぷる の持ち駒"], ["付録"], "ぷる", problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("見本用", problems[0])

    def test_r3_a_name_in_the_appendix_falls(self):
        problems = []
        CS.check_no_real_name(["1 ページ目"], ["1 ページ目"], ["上に行くほど ぷる が良く"], "ぷる", problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("付録", problems[0])

    def test_r4_no_name_anywhere_passes(self):
        problems = []
        CS.check_no_real_name(["本人の持ち駒"], ["本人の持ち駒"], ["本人の持ち駒"], "ぷる", problems)
        self.assertEqual(problems, [])

    def test_r5_the_message_does_not_carry_the_name(self):
        """**落ちたときほど、ログに名前そのものを残さない。**"""
        problems = []
        CS.check_no_real_name(["ぷる"], ["ぷる"], ["ぷる"], "ぷる", problems)
        self.assertEqual(len(problems), 3, problems)
        for problem in problems:
            self.assertNotIn("ぷる", problem)

    def test_r6_line_wrap_does_not_hide_the_name(self):
        """折り返しを越えて探す(`squeeze`。門の他の検査と同じ流儀)。"""
        problems = []
        CS.check_no_real_name(["ぷ\nる の持ち駒"], ["1 ページ目"], ["付録"], "ぷる", problems)
        self.assertEqual(len(problems), 1, problems)

    def test_r7_no_person_in_the_material_does_nothing(self):
        """材料に名前が無い顧客では**何も言わない**(空文字を全ページに見つけない)。"""
        problems = []
        CS.check_no_real_name(["本編"], ["見本"], ["付録"], "", problems)
        self.assertEqual(problems, [])

    def test_r8_the_gate_runs_this_check(self):
        """**`main` がこの検査を呼んでいること。**関数を書いても呼ばれなければ門ではない。

        **字面で探すときは、定義の行に当たらない形で探す** ― 最初に書いた
        `assertIn("check_no_real_name(personal, sample, appendix, person, problems)")` は
        **`def check_no_real_name(...)` の行にも当たる**ので、呼び出しを消す変異で黙った(実測)。
        **本物の校正は門を通す試験**(`CheckStructureTest` の test_43〜45)で、ここは字面の念押し。
        """
        here = os.path.dirname(os.path.abspath(__file__))
        with io.open(os.path.join(here, "check_structure.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertRegex(src, r"(?m)^    check_no_real_name\(")


class HeadingMatchesTest(unittest.TestCase):
    """**節の見出しの見分け**(`heading_matches`)。`exit_body.py`・`exit_gate.py` が共有する 1 か所。"""

    def test_h1_the_head_alone_is_not_enough_when_a_word_is_required(self):
        """**頭が合っても、要る語が無ければ節ではない。**

        答え合わせの節は「次の」で始まり「答え合わせ」を含む(顧客ごとに局数が変わるため)。
        `contains` を見ない作りにすると、**「次の」で始まる別の見出しが答え合わせの節として通る** ―
        そのとき項目 6 が「表が無い」ではなく**違う節の表**を数える。
        校正で黙っていた(2026-09-29)のでここで測る。
        """
        self.assertTrue(CS.heading_matches(CS.VERIFY_ROLE, "次の 20 局で、何で答え合わせをするか"))
        self.assertFalse(CS.heading_matches(CS.VERIFY_ROLE, "次の 20 局で起きそうなこと"))

    def test_h2_the_head_must_be_at_the_front(self):
        """**頭は前方一致**(語が含まれるだけでは節ではない)。"""
        self.assertTrue(CS.heading_matches(CS.MAPPING_ROLE, "対応表 ― 何局目がどのファイルか"))
        self.assertFalse(CS.heading_matches(CS.MAPPING_ROLE, "この対応表について"))

    def test_h3_every_role_in_the_table_can_be_matched(self):
        """**表の 6 役割すべてが、自分の見出しで見分けられる。**役割を足して題を忘れる道を閉じる。"""
        for role, head, contains in CS.SECTIONS:
            heading = head if contains is None else f"{head} 20 局で、何で{contains}をするか"
            self.assertTrue(CS.heading_matches(role, heading), (role, heading))


class CoverPagesTest(unittest.TestCase):
    """**検査 8 は表紙の枚数を索引から読む**(器の単独束 C-4。2026-09-30)。

    付録へ回した節(分母の表)が表紙 PDF の 2 ページ目に付くので、**表紙は 1 ページとは限らない。**
    枚数を真偽値(`hasCover`)で数え続けると、**付録が 1 ページ増えたことが「指していないページが
    混ざっている」という嘘の指摘になり**、門が通らなくなる ― 直し方は「検査を消す」に流れる。
    """

    # 付録は 5 ページ・指しているのは 3 ページ・表紙は 2 ページ(**3 つとも違う数**にする ―
    # そろえると足し算の向きを変える変異が黙る)。
    INDEX = {"appendixPages": [1, 2, 3], "hasCover": True, "coverPages": 2}
    APPENDIX = ["付録 1 ページ目", "付録 2", "付録 3", "付録 4", "付録 5"]

    def test_c1_two_cover_pages_add_up(self):
        problems = []
        CS.check_appendix_pages(dict(self.INDEX), list(self.APPENDIX), problems)
        self.assertEqual(problems, [])

    def test_c2_without_the_key_the_old_count_falls(self):
        """**`coverPages` を読まなければ落ちる。**表紙を 1 ページと数えると 3 + 1 ≠ 5。"""
        index = dict(self.INDEX)
        del index["coverPages"]
        problems = []
        CS.check_appendix_pages(index, list(self.APPENDIX), problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("検査 8", problems[0])
        self.assertIn("表紙 1 ページ", problems[0])

    def test_c3_a_non_integer_falls_back(self):
        """**文字の "2" は数として使わない**(索引が壊れていたら黙って通さない)。"""
        index = dict(self.INDEX)
        index["coverPages"] = "2"
        problems = []
        CS.check_appendix_pages(index, list(self.APPENDIX), problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("表紙 1 ページ", problems[0])

    def test_c4_the_cover_is_still_required(self):
        """**枚数が在っても表紙そのものは必須**(正本 §8)。2 つの検査が混ざっていない。"""
        index = dict(self.INDEX)
        index["hasCover"] = False
        problems = []
        CS.check_appendix_pages(index, list(self.APPENDIX), problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("表紙が無い", problems[0])

    def test_c5_a_wrong_count_still_falls(self):
        """**枚数を読むようにしても、合わない束は落ちる**(検査が甘くなっていない)。"""
        index = dict(self.INDEX)
        index["coverPages"] = 3
        problems = []
        CS.check_appendix_pages(index, list(self.APPENDIX), problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("表紙 3 ページ", problems[0])


class MovedToAppendixTest(unittest.TestCase):
    """**検査 9(付録へ回した節)は両側を見る**(器の単独束 C-4。2026-09-30。司令塔の条件)。

    印の付いた節が**本編の PDF に出ない**こと、かつ**付録の PDF に出る**こと。
    片側だけ見ると片方が腐る(P-171 の型) ― 本編から外れたのに付録に組まれなければ、
    **顧客が読む表がどこにも出ない。**
    """

    HEAD = "数の分母がどこから来たか"
    # 印の付いた節(`### ` の小見出しを 1 つ持つ)。本編に残る節を前後に置き、
    # **切り出しの範囲**(次の `## ` の直前まで)も一緒に通す。
    MD = ("## 本編の節\n\n本文。\n\n"
          "<!-- appendix: 数の出どころ -->\n### " + HEAD + "\n\n"
          "| 名前 | 分母 |\n| --- | --- |\n| 崩れ | 20 局 |\n\n"
          "## 次の節\n\n次の本文。\n")
    # 本編は 2 ページ・付録は 3 ページ(**数をそろえない**)。
    PERSONAL = ["本編の節\n本文。", "次の節\n次の本文。"]
    APPENDIX = ["付録の表紙", HEAD + "\n崩れ 20 局", "付録 3 ページ目"]

    def test_m1_moved_out_of_the_body_and_into_the_appendix_passes(self):
        problems = []
        CS.check_moved_to_appendix(self.MD, list(self.PERSONAL), list(self.APPENDIX), problems)
        self.assertEqual(problems, [])

    def test_m2_still_in_the_body_falls(self):
        """**二重に出る向き。**印が付いているのに本編から外れていない。"""
        problems = []
        CS.check_moved_to_appendix(self.MD, self.PERSONAL + [self.HEAD], list(self.APPENDIX), problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("本編の PDF に出ている", problems[0])

    def test_m3_missing_from_the_appendix_falls(self):
        """**どこにも出ない向き。**本編から外したのに付録に組まれていない。"""
        problems = []
        CS.check_moved_to_appendix(self.MD, list(self.PERSONAL), ["付録の表紙", "別の話", "3"], problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("付録の PDF に無い", problems[0])

    def test_m4_both_sides_can_fall_together(self):
        """**片側を消す変異で 1 件に減る**(2 つの指摘が別々に立っている)。"""
        problems = []
        CS.check_moved_to_appendix(self.MD, self.PERSONAL + [self.HEAD],
                                   ["付録の表紙", "別の話", "3"], problems)
        self.assertEqual(len(problems), 2, problems)

    def test_m5_no_marker_says_nothing(self):
        """**印が無ければ何も言わない**(既に送った冊子・印を付けない顧客でも通る)。
        本編に見出しが在っても指摘しない ― 印が無ければ「回した節」ではない。"""
        problems = []
        CS.check_moved_to_appendix("## 節\n\n### " + self.HEAD + "\n\n本文。\n",
                                   self.PERSONAL + [self.HEAD], ["付録の表紙"], problems)
        self.assertEqual(problems, [])

    def test_m6_a_section_without_a_heading_falls(self):
        """**照合する語が取れないまま通さない**(印だけ置いて見出しを書き忘れた道)。"""
        problems = []
        CS.check_moved_to_appendix("<!-- appendix: 数の出どころ -->\n本文だけ。\n",
                                   list(self.PERSONAL), list(self.APPENDIX), problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("見出し", problems[0])

    def test_m7_line_wrap_in_the_appendix_does_not_look_missing(self):
        """**付録側の折り返し。**組版は見出しも折るので、そのままでは「無い」と数える。"""
        problems = []
        wrapped = ["付録の表紙", "数の分母がど\nこから来たか\n崩れ 20 局", "3"]
        CS.check_moved_to_appendix(self.MD, list(self.PERSONAL), wrapped, problems)
        self.assertEqual(problems, [])

    def test_m8_line_wrap_in_the_body_does_not_hide_it(self):
        """**本編側の折り返し。**折れたまま残っているのを見逃さない(両側で空白を落としている)。"""
        problems = []
        body = self.PERSONAL + ["数の分母がど\nこから来たか"]
        CS.check_moved_to_appendix(self.MD, body, list(self.APPENDIX), problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("本編の PDF に出ている", problems[0])


if __name__ == "__main__":
    unittest.main()
