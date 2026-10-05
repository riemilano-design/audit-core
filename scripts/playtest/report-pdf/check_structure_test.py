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
import exit_index as EI  # noqa: E402

# **商品の範囲の 1 段落は、わざと 2 行に折って置く。**実物の組版は文を行に折るので、折れていない土台で
# 測ると「折れた実物では通らない」門を通してしまう(最初の実測でここが落ち、`squeeze` を足した)。
# **実物でも同じ形を確かめた**: 4 人目の送付用 p1 は `この\n冊子は、…` と折れている(P-114)。
SCOPE_WRAPPED = ["この冊子は、エンジンの解析と機械の集計から、次の 20 局で",
                 "確かめる仮説を出すものです。"]

# 冒頭の断り書き 2 文(P-162)。**道具の定数から引く**(写さない) ―
# 写すと、文を直したときに**土台だけが古い文で緑のまま通る**。
OPENING_CAVEATS = [CS.OPENING_NOT_A_JUDGE, CS.OPENING_APPENDIX]

# 用語の 4 文(C-3。2026-09-30)。**道具の表から引く**(写さない) ―
# 写すと、文を直したときに土台だけが古い文で緑のまま通る。
#
# **20 文字ずつに折って置く。**`write_pdf` は折り返さないので、長い文をそのまま 1 行に置くと
# **ページの外にはみ出して抽出できず**、門が「0 か所」と数えた(最初の実測でここが落ちた)。
# 折るのは実物に合わせた形でもある(組版は文を行に折る ― `SCOPE_WRAPPED` と同じ理由)。
TERM_SENTENCES = [sentence[i:i + 20]
                  for _term, sentence in CS.TERM_LINES
                  for i in range(0, len(sentence), 20)]

# 本人用 5 ページ。最後が対応表(見本用では抜くページ)。
HONBUN_PAGES = [
    ["合成材料の冊子(変異試験)"] + SCOPE_WRAPPED + OPENING_CAVEATS + TERM_SENTENCES,
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

    def test_10b_missing_term_sentences_fall(self):
        """**用語の説明を抜いた本編は通らない**(C-3。2026-09-30)。

        **門に配線されていることをここで測る** ― 単体の `check_term_lines` が緑でも、
        `main` から呼んでいなければ**顧客には定義の無い冊子が出る**(呼び出しを外す変異が黙る道)。
        """
        pages = [list(p) for p in HONBUN_PAGES]
        pages[0] = [line for line in pages[0] if line not in TERM_SENTENCES]
        write_pdf(os.path.join(self.dir, "honbun_personal.pdf"), pages)
        write_pdf(os.path.join(self.dir, "honbun_sample.pdf"),
                  [p for i, p in enumerate(pages) if i != MAPPING_PAGE_INDEX])
        self.assert_falls("用語")

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


class TermLinesTest(unittest.TestCase):
    """**用語の 4 文が本編にちょうど 1 回ずつ在る**(器の単独束 C-3。2026-09-30)。

    5 人目の感想が「第一候補 = ソフトの最善手か」と聞いた ―
    **冊子の中でいちばん使う語が、冊子の中で定義されていなかった。**
    """

    def test_t1_four_lines_with_the_term_and_the_sentence(self):
        """md の 4 行。**語と文の両方**が入る(語だけでは定義にならない)。"""
        lines = CS.term_md_lines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(len(CS.TERM_LINES), 4)
        for line, (term, sentence) in zip(lines, CS.TERM_LINES):
            self.assertTrue(line.startswith("- "), line)
            self.assertIn(term, line)
            self.assertIn(sentence, line)

    def test_t1d_only_the_term_is_bold(self):
        """**太字は語だけ・文は太字にしない**(2026-10-01 の司令塔の条件)。

        本編の他の箇条書きと同じ形(`- **名前**: 文`)にする。
        文まで太字にすると、**冒頭の 4 行が本文の中でいちばん強い見た目**になり、
        顧客が最初に読むべき「数 3 つ」より目立つ。
        """
        for line, (term, sentence) in zip(CS.term_md_lines(), CS.TERM_LINES):
            self.assertEqual(line, "- **" + term + "**: " + sentence)
            # **文の側に太字の印が無いこと**(語の分の 2 組だけ)。
            self.assertNotIn("**", sentence)
            self.assertEqual(line.count("**"), 2)

    def test_t1b_the_terms_are_the_four_we_decided(self):
        """**どの語かを試験の側に書く**(表を読むと、語を入れ替える変異と一緒に動いて黙る)。"""
        self.assertEqual([term for term, _s in CS.TERM_LINES],
                         ["第 1 候補", "分かれ道", "自玉側", "一致率"])
        # **「最善手」は使わない**(`check_delivery.ALWAYS_FORBIDDEN_WORDS` が納品を止める語)。
        self.assertNotIn("最善手", "".join(CS.term_md_lines()))

    def test_t1c_the_term_and_the_sentence_are_not_swapped(self):
        """**語と文の組が入れ替わっていないこと**(監査の指摘。2026-09-30)。

        t1・t1b は**表から作った行が自己整合的**であることしか見ていないので、
        **表そのものの語と文の組を入れ替えても全部緑だった**(監査が変異で実測)。
        文が 1 回ずつ在るかを数える門も、**どの語に付いた文かは見ていない。**
        入れ替わると、顧客は「分かれ道」の欄で第 1 候補の説明を読む ―
        **いちばん使う語の定義が、別の語の定義になる。**

        【写しにしない】文全体を書き写すと、文を直したときに**土台だけ古い文で緑のまま通る**
        (`TERM_SENTENCES` を道具の表から引いているのと同じ理由)。
        だから見るのは**その語だけが持つ短い断片**で、文の同一性ではなく**対応関係**だけを測る。
        """
        by_term = dict(CS.TERM_LINES)
        self.assertIn("エンジンが 1 番に挙げた", by_term["第 1 候補"])
        self.assertIn("候補 5 つに入らなかった", by_term["分かれ道"])
        self.assertIn("自分の玉のまわり", by_term["自玉側"])
        self.assertIn("同じ側だった割合", by_term["一致率"])
        # **断片は 1 つの文にしか出ないこと**(どの文に当てても通る断片では入れ替えを見分けられない)。
        for fragment in ("エンジンが 1 番に挙げた", "候補 5 つに入らなかった",
                         "自分の玉のまわり", "同じ側だった割合"):
            hits = [term for term, sentence in CS.TERM_LINES if fragment in sentence]
            self.assertEqual(len(hits), 1, (fragment, hits))

    def test_t7_the_fork_line_is_in_the_counting_notes(self):
        """**分かれ道の線(600)が数え方に在る**(C-6。2026-10-01 の司令塔の判断)。

        **分かれ道の数は本編の主題**なのに、その線だけが冊子の中に無かった ―
        封じた最終版では **300 が 2 か所・600 が 0 か所**だった(非対称)。
        崩れの 300 と**同じ扱い**で、数え方の節に線を書く。

        【冒頭の用語とは語が違う】冒頭の 4 行は「差が大きかった」と書く
        (顧客が最初に読む所に cp の線を出さない)。**ここは数え方なので線そのものを書く。**
        """

        fork = [s for s in EI.COUNTING_NOTES if s.startswith("「分かれ道」は、")]
        self.assertEqual(len(fork), 1, EI.COUNTING_NOTES)
        # **線の向きまで見る。**`assertIn("600 以上")` だけでは
        # 「600 以上**ではなかった**局面」という**意味を反転させる変異**が通る(独立監査が実測)。
        # 文全体は写さない(写すと文を直したとき土台だけ古い文で緑になる)ので、
        # **向きを決める語の組**で見る ― 「600 以上だった局面」が在り、打ち消しの語が無い。
        # **文を全部で固定する**(2026-10-01。独立監査の 3 回目の指摘)。
        #
        # 【なぜ部分では足りなかったか】3 回やって 3 回抜けた ―
        # (1) `assertIn("600 以上")` だけ → 「600 以上**ではなかった**」が通った。
        # (2) 頭(「…局面、または実戦の手が」)+ 文末の 2 点で挟む → **その間**が裸で、
        #     「候補 **5** つ」→「候補 **3** つ」(どちらも実在する構造の数)が通った。
        # **部分で縛るたびに、縛っていない区間が残る。**区間を足し続けるのは、全部を書くのと同じである。
        #
        # 【写しにしてよい理由】この文は**人が承認した固定文**である(2026-10-01 の司令塔の判断)。
        # 「写すと土台だけ古い文で緑になる」という心配は、**材料から出てくる文**に当てはまる話で、
        # **承認された固定文では逆** ― 文を変えたら試験が赤くなるのが**歯止め**である
        # (`lib/findingTexts.test.ts` が承認済みの用語を正本の文と突き合わせているのと同じ考え方)。
        # **直すときは、司令塔の承認と一緒にここも直す。**
        self.assertEqual(
            fork[0],
            "「分かれ道」は、実戦の手と第 1 候補の評価の差が 600 以上だった局面、"
            "または実戦の手が第 1 候補から数えて候補 5 つに入らなかった局面です。")
        # **崩れの 300 と並んでいる**(片方だけ在る状態に戻ったら落ちる)。
        self.assertTrue(any("+300 以上を優勢" in s for s in EI.COUNTING_NOTES))
        # **冒頭の用語の文には線を書かない**(2 つの節で役目が違う)。
        for _term, sentence in CS.TERM_LINES:
            self.assertNotIn("600", sentence)

    def _pages_with_all_terms(self):
        """4 文が 1 回ずつ在る本編(ページに散らして置く ― ページをまたいで探すことも測る)。"""
        sentences = [s for _t, s in CS.TERM_LINES]
        return ["1 ページ目。" + sentences[0] + sentences[1],
                "2 ページ目。" + sentences[2],
                "3 ページ目。" + sentences[3]]

    def test_t2_all_four_present_passes(self):
        problems = []
        CS.check_term_lines(self._pages_with_all_terms(), problems)
        self.assertEqual(problems, [])

    def test_t3_a_missing_sentence_falls(self):
        """**1 文でも抜ければ落とす。**どの語かを指摘に出す。"""
        pages = self._pages_with_all_terms()
        pages[1] = "2 ページ目。説明は消えました。"
        problems = []
        CS.check_term_lines(pages, problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("自玉側", problems[0])
        self.assertIn("0 か所", problems[0])

    def test_t4_the_term_alone_is_not_enough(self):
        """**語の数では数えない。**「第 1 候補」は本文に何度も出るので、語だけでは定義が在るか分からない。"""
        problems = []
        CS.check_term_lines(["第 1 候補 第 1 候補 第 1 候補 分かれ道 自玉側 一致率"], problems)
        self.assertEqual(len(problems), 4, problems)

    def test_t5_twice_falls_too(self):
        """**2 回出るのも落とす**(冒頭と別の節で二重に定義した形)。"""
        pages = self._pages_with_all_terms()
        pages.append("4 ページ目。" + CS.TERM_LINES[0][1])
        problems = []
        CS.check_term_lines(pages, problems)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("2 か所", problems[0])

    def test_t6_line_wrap_does_not_hide_the_sentence(self):
        """折り返しを越えて探す(`squeeze`。門の他の検査と同じ流儀)。"""
        sentences = [s for _t, s in CS.TERM_LINES]
        folded = sentences[0][:10] + "\n" + sentences[0][10:]
        problems = []
        CS.check_term_lines([folded, sentences[1], sentences[2], sentences[3]], problems)
        self.assertEqual(problems, [])


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


class QuestionSectionTest(unittest.TestCase):
    """**⑧ の G-4・G-5・G-7。**節「お預かりした問い」の 有無・位置・長さ。

    **節は `SECTIONS` に足さない**(司令塔の判断 2026-10-01)。表に足すと
    `check_sections` が全行を必須にするので、問いが 0 件の顧客の本編が門を通れなくなる。
    だから**別の検査**。位置も `SECTIONS` ではなく**行番号**で留める。
    """

    # 「ひとことで」と、その次の節。**md は節の並びだけを持つ最小の形**。
    HEAD = ["# 対局後診断", "", "## ひとことで", "", "- 25 局のうち 18 局でした。", ""]
    TAIL = ["## 局面で見る", "", "(盤)", "", "## 数え方", "", "(数え方)", ""]
    # **土台は顧客に出してよい形だけを使う**(司令塔 2026-10-01)。
    # 前の土台は「― 読み: 普段と違う型の 4 局では…」を持っていた ―
    # **人間が却下した「25 局内の頻度を『普段』の代用にする」読み**そのものなので、
    # 残すと後で誰かが写す。だから**人間が書いた文**(`EI.unanswerable_past_games`)に替えた。
    # **問いの行には「普段」が出る**(顧客の問いの字)― これは正しい。
    # 「普段」を文書全体の黒名簿にすると**この行と人間の文の 2 か所が壊れる。**
    Q = ["## お預かりした問い", "",
         "お預かりした問い: 「3 切れで普段指さない戦型を採用したときの影響」", "",
         EI.unanswerable_past_games(25), ""]

    def md(self, question=True, place="直後"):
        """`place`: 直後 / 前 / 間に節 / 末尾。"""
        if not question:
            return "\n".join(self.HEAD + self.TAIL)
        if place == "直後":
            return "\n".join(self.HEAD + self.Q + self.TAIL)
        if place == "前":
            return "\n".join(["# 対局後診断", ""] + self.Q + self.HEAD[2:] + self.TAIL)
        if place == "間に節":
            return "\n".join(self.HEAD + self.TAIL[:4] + self.Q + self.TAIL[4:])
        if place == "末尾":
            return "\n".join(self.HEAD + self.TAIL + self.Q)
        raise AssertionError(place)

    def problems(self, md_text, question_count):
        out = []
        CS.check_question_section(md_text, question_count, out)
        return out

    # ---- G-4 有無(0 = 0 で通る・片方だけでは落ちる)----
    def test_q1_no_question_no_section_passes(self):
        """問いが 0 件で節も無ければ**通る**(「問いは無かった」とも書かない)。"""
        self.assertEqual(self.problems(self.md(question=False), 0), [])

    def test_q2_question_with_section_passes(self):
        """問いが 1 件で節が「ひとことで」の直後なら**通る**。"""
        self.assertEqual(self.problems(self.md(), 1), [])

    def test_q3_question_without_section_falls(self):
        """問いが在るのに節が無ければ落ちる(**必須の向き**)。"""
        got = self.problems(self.md(question=False), 1)
        self.assertEqual(len(got), 1)
        self.assertIn("1 件あるのに", got[0])
        self.assertIn("お預かりした問い", got[0])

    def test_q4_section_without_question_falls(self):
        """問いが 0 件なのに節が在れば落ちる(**余った向き**)。
        **向きが 2 つあるので、片方だけ実装した変異が黙らない。**"""
        got = self.problems(self.md(), 0)
        self.assertEqual(len(got), 1)
        self.assertIn("0 件なのに", got[0])

    def test_q5_unknown_count_does_not_judge_presence(self):
        """**件数が分からない(`None`)ときは有無を判定しない。**
        0 件と決めつけると、問いが在る顧客の節を「余った節」として落としてしまう。"""
        self.assertEqual(self.problems(self.md(), None), [])
        self.assertEqual(self.problems(self.md(question=False), None), [])

    def test_q6_many_questions_still_one_section(self):
        """問いが 3 件でも節は 1 つ(件数ぶん節を要求しない)。"""
        self.assertEqual(self.problems(self.md(), 3), [])

    # ---- G-5 位置 ----
    def test_q7_section_before_hitokotode_falls(self):
        got = self.problems(self.md(place="前"), 1)
        self.assertEqual(len(got), 1)
        self.assertIn("より前に在る", got[0])

    def test_q8_section_not_immediately_after_falls(self):
        """間に別の見出しが在れば落ちる(**「直後」を見ている** ― 「後ろのどこか」ではない)。"""
        got = self.problems(self.md(place="間に節"), 1)
        self.assertEqual(len(got), 1)
        self.assertIn("直後でない", got[0])
        self.assertIn("局面で見る", got[0])

    def test_q9_section_at_the_end_falls(self):
        got = self.problems(self.md(place="末尾"), 1)
        self.assertEqual(len(got), 1)
        self.assertIn("直後でない", got[0])

    def test_q10_missing_anchor_is_not_said_twice(self):
        """「ひとことで」そのものが無いときは**位置を言わない**(`check_sections` が落とす)。"""
        md_text = "\n".join(["# 対局後診断", ""] + self.Q + self.TAIL)
        self.assertEqual(self.problems(md_text, 1), [])

    # ---- G-7 長さ(両側で校正する)----
    def test_q11_at_the_limit_passes(self):
        """**ちょうど上限は通る。**(上限 + 1 で落ちる試験と対にする)"""
        limit = CS.MAX_QUESTION_SECTION_CHARS
        body = "あ" * limit
        md_text = "\n".join(self.HEAD + ["## お預かりした問い", "", body, ""] + self.TAIL)
        self.assertEqual(len(CS.question_section_body(md_text)), limit)
        self.assertEqual(self.problems(md_text, 1), [])

    def test_q12_one_over_the_limit_falls(self):
        limit = CS.MAX_QUESTION_SECTION_CHARS
        body = "あ" * (limit + 1)
        md_text = "\n".join(self.HEAD + ["## お預かりした問い", "", body, ""] + self.TAIL)
        got = self.problems(md_text, 1)
        self.assertEqual(len(got), 1)
        self.assertIn(f"{limit + 1} 文字", got[0])
        self.assertIn(f"上限 {limit}", got[0])

    def test_q13_length_counts_only_the_section(self):
        """長さは**節の中だけ**を数える(本編ぜんたいでも、見出しの行でもない)。
        **範囲を広げる変異が黙らない** ― 他の節は上限を超える量を持っている。"""
        limit = CS.MAX_QUESTION_SECTION_CHARS
        big = "い" * limit
        md_text = "\n".join(self.HEAD + ["", big, ""] + self.Q + self.TAIL + ["", big])
        self.assertLess(len(CS.question_section_body(md_text)), limit)
        self.assertEqual(self.problems(md_text, 1), [])

    def test_q14_heading_line_is_not_counted(self):
        """見出しの行(`## お預かりした問い`)は長さに入らない。"""
        md_text = "\n".join(self.HEAD + ["## お預かりした問い", ""] + self.TAIL)
        self.assertEqual(CS.question_section_body(md_text), "")

    def test_q15_two_sections_fall(self):
        """節が 2 つあれば落ちる(**位置と長さは見ない** ― どちらを見るべきか決まらない)。"""
        md_text = "\n".join(self.HEAD + self.Q + self.TAIL + self.Q)
        got = self.problems(md_text, 1)
        self.assertEqual(len(got), 1)
        self.assertIn("2 個", got[0])

    def test_q16_real_estimate_fits_the_limit(self):
        """**実物の文**が上限に収まること。上限を小さくする変異が黙らない。

        **2026-10-01 に土台を替えた**(司令塔の指示): 前の土台は却下された読みを模した文で
        **156 文字の見込み**(便 116 で測った数)だった。いまは**問いの字 + 人間が書いた文**で、
        **実測 115 文字**(問いの行 35 + 人間の文 80)。
        """
        md_text = self.md()
        body = CS.question_section_body(md_text)
        # **字で留める**(土台が人間の文に変わったら気づく)。
        self.assertEqual(len(body), 115)
        self.assertIn(EI.unanswerable_past_games(25), body)
        self.assertLessEqual(len(body), CS.MAX_QUESTION_SECTION_CHARS)
        # **近くの数と同じにしない**: 上限そのものでも 0 でもない。
        self.assertNotEqual(len(body), CS.MAX_QUESTION_SECTION_CHARS)
        self.assertGreater(len(body), 60)

    def test_q17_marks_are_not_counted(self):
        """**印は数えない**(2026-10-05。司令塔の訂正 2026-10-01: 印は印字されない)。
        印つきと印なしで同じ 115。印を数えると 144(+29)、空白も数えると 145。"""
        marked = list(self.Q)
        marked[4] = marked[4] + " <!-- ans: q1 unanswerable -->"
        md_marked = "\n".join(self.HEAD + marked + self.TAIL)
        body = CS.question_section_body(md_marked)
        self.assertEqual(len(body), 115)
        self.assertEqual(len(body), len(CS.question_section_body(self.md())))
        self.assertNotIn("<!--", body)
        self.assertNotEqual(len(body), 144)
        self.assertNotEqual(len(body), 145)
        # 家族の印ぜんぶが落ちる(1 家族だけ剥く変異が赤に)。
        marked[4] = marked[4] + "<!-- pos: 11/48 付録3 3 分 --><!-- menu: M4 --><!-- agg: a.b --><!-- priority: M4 -->"
        body2 = CS.question_section_body("\n".join(self.HEAD + marked + self.TAIL))
        self.assertEqual(len(body2), 115)
        # 剥くのは `check_answer.strip_marks` の 1 か所(数える側だけを直した)。
        import inspect
        self.assertIn("CA.strip_marks(", inspect.getsource(CS.question_section_body))

    # ---- 人が決めた数と中身を**字で留める**(2026-10-01 の変異で見つけた沈黙)----
    #
    # 上の q11・q12 は `CS.MAX_QUESTION_SECTION_CHARS` から土台を作るので、
    # **上限そのものを 1000 や 100 に変える変異が 1 本も赤くならなかった**
    # (「表から作った出力を同じ表と比べても中身は測れない」の家族)。
    # 200 は**司令塔が決めた数**なので、字で留めて**動かしたら赤**にする。
    def test_q17_the_limit_is_the_approved_number(self):
        """**上限 200 は人が決めた数**(司令塔の判断 2026-10-01。見込みの文 156 文字 + 余裕 44)。
        動かすには判断が要る ― **字で留める。**"""
        self.assertEqual(CS.MAX_QUESTION_SECTION_CHARS, 200)
        # **近くの数と同じにしない**(ページ数の定数・見込みの文の長さと取り違えない)。
        for near in (4, 5, 100, 156, 240, 1000):
            self.assertNotEqual(CS.MAX_QUESTION_SECTION_CHARS, near)

    def test_q18_two_hundred_one_characters_fall(self):
        """**201 文字は落ちる**(土台を定数から作らず、**字で 201 文字**を置く)。
        上限を緩める変異がここで赤くなる。"""
        md_text = "\n".join(self.HEAD + ["## お預かりした問い", "", "あ" * 201, ""] + self.TAIL)
        got = self.problems(md_text, 1)
        self.assertEqual(len(got), 1)
        self.assertIn("201 文字", got[0])

    def test_q19_two_hundred_characters_pass(self):
        """**ちょうど 200 文字は通る**(字で 200 文字)。上限を厳しくする変異がここで赤くなる。"""
        md_text = "\n".join(self.HEAD + ["## お預かりした問い", "", "あ" * 200, ""] + self.TAIL)
        self.assertEqual(self.problems(md_text, 1), [])

    def test_q20_the_body_strips_each_line(self):
        """`question_section_body` は**各行の前後の空白を落とす** ― 字で留める。

        **独立監査が実測(2026-10-01)**: `.strip()` を外す変異が **121 本全部を素通り**した。
        いまの実物(`out/c5` の本編)は節の行に前後の空白を持たないので影響しないが、
        **実物の「試せること」節にはインデント付きの続き行が在る**(`   ※「10秒以上」は…` の形)。
        ⑥ が節の中身をその形で書けば、落とさないぶんだけ**長さが実際より多く数えられ**、
        G-7 の 200 文字の門が**本当は収まる文を落とす**。
        方向は安全側(過剰に厳しくなる)だが、**この束が N8〜N11 で埋めたのと同じ型の抜け**なので
        同じ基準を当てる ― **数も中身も字で留める。**
        """
        md_text = "\n".join(self.HEAD + [
            "## お預かりした問い", "",
            "  前後に半角空白  ",
            "　全角空白　",
            "\t前にタブ",
            ""] + self.TAIL)
        body = CS.question_section_body(md_text)
        # **中身を字で留める**(空白が 1 つでも残れば一致しない)。
        self.assertEqual(body, "前後に半角空白全角空白前にタブ")
        # **長さも字で留める**(中身の照合が緩んだときの二重の留め)。
        self.assertEqual(len(body), 15)
        # **落とさなければ長くなる**(方向を留める ― `.strip()` を外す変異がここでも赤くなる)。
        raw = "".join(["  前後に半角空白  ", "　全角空白　", "\t前にタブ", ""])
        self.assertGreater(len(raw), 15)


class NoGlossaryTextTest(unittest.TestCase):
    """**⑧ の G-8。**却下済みの 6 冊形の用語の文(TS `findingTexts.GLOSSARY`)が
    出口の本編に出ないこと(司令塔の判断 2026-10-01。寄せない・照合しない・黒名簿 1 本)。"""

    def problems(self, md_text):
        out = []
        CS.check_no_glossary_text(md_text, out)
        return out

    def test_g8a_clean_md_passes(self):
        md_text = "## ひとことで\n\n" + "\n".join(CS.term_md_lines())
        self.assertEqual(self.problems(md_text), [])

    def test_g8b_each_fragment_falls_on_its_own(self):
        """**断片ごとに別々に落ちる**(1 語だけ見る変異が黙らない)。"""
        self.assertGreaterEqual(len(CS.GLOSSARY_FRAGMENTS), 2)
        for term, fragment in CS.GLOSSARY_FRAGMENTS:
            got = self.problems(f"## ひとことで\n\n- **{term}**: {fragment}です\n")
            self.assertEqual(len(got), 1, f"{term} が落ちない")
            self.assertIn(fragment, got[0])

    def test_g8c_all_fragments_at_once(self):
        md_text = "\n".join(f"- {fragment}" for _term, fragment in CS.GLOSSARY_FRAGMENTS)
        self.assertEqual(len(self.problems(md_text)), len(CS.GLOSSARY_FRAGMENTS))

    def test_g8d_fragments_are_in_the_ts_glossary(self):
        """**断片が TS の実物に在ること。**TS が文を書き換えたら**ここが赤になる** ―
        黒名簿が写しのまま黙って効き目を失う道を閉じる(これが赤くなる日に、1 か所へ寄せる判断をする)。"""
        ts = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "lib", "findingTexts.ts")
        with open(ts, encoding="utf-8") as f:
            src = f.read()
        start = src.index("export const GLOSSARY")
        block = src[start:src.index("];", start)]
        for term, fragment in CS.GLOSSARY_FRAGMENTS:
            self.assertIn(fragment, block, f"TS の GLOSSARY に無い断片: {term}")
            self.assertIn(f'term: "{term}"', block, f"TS の GLOSSARY に無い語: {term}")

    def test_g8e_fragments_are_not_in_the_exit_terms(self):
        """**断片が出口の `TERM_LINES` には出ないこと。**出ていたら黒名簿は
        **正しい本編を落とす**(重なる 2 語の文が一致していないことの裏返し)。"""
        exit_text = "\n".join(CS.term_md_lines())
        for term, fragment in CS.GLOSSARY_FRAGMENTS:
            self.assertNotIn(fragment, exit_text, f"出口の用語に在る断片: {term}")

    def test_g8f_the_blacklist_holds_both_overlapping_terms(self):
        """**黒名簿の中身を字で留める**(2026-10-01 の変異で見つけた沈黙)。

        上の `test_g8c` は `len(CS.GLOSSARY_FRAGMENTS)` と問題の件数を比べるので、
        **黒名簿を 1 語に縮める変異・空にする変異のどちらも、件数がそろって黙った**
        (「件数がそろうと母集団の入れ替えが黙る」の家族)。
        **重なる 2 語は TS と python の両方に在る語**なので、字で留める。
        """
        self.assertEqual(sorted(term for term, _fragment in CS.GLOSSARY_FRAGMENTS),
                         sorted(["第 1 候補", "分かれ道"]))
        self.assertEqual(len(CS.GLOSSARY_FRAGMENTS), 2)
        # 断片そのものも空でない(語だけ在って断片が空だと、検査は全文に当たってしまう)。
        for term, fragment in CS.GLOSSARY_FRAGMENTS:
            self.assertGreaterEqual(len(fragment), 8, f"断片が短すぎる: {term}")


if __name__ == "__main__":
    unittest.main()
