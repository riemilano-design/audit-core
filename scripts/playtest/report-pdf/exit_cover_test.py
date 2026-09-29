# -*- coding: utf-8 -*-
# `exit_cover.py`(付録の表紙の md)の試験。**合成材料だけ**を使う。
#
# 【なぜ合成材料だけか】① の制約(仕様 §4・司令塔承認 2026-09-28):
# **実物での確認は門にできない** ― 顧客の棋譜と診断データをリポジトリに置けないため。
# 実物での確認は `deliver_log.jsonl` の記録にする。
#
# 【変異は両向き】材料を壊して落ちるか + 検査の行を黙らせて落ちなくなるか
# (`docs/TESTING_STRATEGY.md`「変異は両向きに回す」)。
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_answer as CA
import exit_cover as EC
import exit_index as EI

HERE = os.path.dirname(os.path.abspath(__file__))
# 語の実在を `git grep` で見るので、リポジトリの根が要る。
# **`EXIT_COVER_REPO` で渡せる**のは、写しを作って変異の校正をするときのため
# (原本のツリーを壊さずに校正する ― 2026-09-15 の規則)。
# **継ぎ目が嘘をつけないように、下の test_16b が「その場所に CLAUDE.md があるか」を見る。**
REPO = os.environ.get("EXIT_COVER_REPO") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CJK_RUN = re.compile(r"[぀-ヿ一-鿿][぀-ヿ一-鿿、。]{3,}")


def write(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False)


class CoverTestBase(unittest.TestCase):
    """合成の材料と、節を指す印つきの本編 md を一時フォルダに作る。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.addCleanup(self.tmp.cleanup)
        self.material()

    def material(self, games=25, featured=9, finals=1, forks=103):
        write(f"{self.d}/patient.json", {"summary": {"games": games},
                                         "person": "この名前は表紙に出てはいけない"})
        write(f"{self.d}/prose.json", {str(i): {"scenes": []} for i in range(1, featured + 1)})
        write(f"{self.d}/finals.json", {"entries": [{"gameNo": i} for i in range(1, finals + 1)]})
        write(f"{self.d}/direct.json", {"answers": [{"ply": i} for i in range(1, forks + 1)]})
        for name in ("付録1", "付録3"):
            write(f"{self.d}/idx_{name}.json",
                  {"appendix": name, "source": f"{name}.pdf", "pages": 3,
                   "positions": {}, "sections": {}})

    def index_with_pages(self, appendix, positions, sections, pages=9):
        """組版の索引に節と局面のページを入れる(D2 の逆引きを測るため)。"""
        write(f"{self.d}/idx_{appendix}.json",
              {"appendix": appendix, "source": f"{appendix}.pdf", "pages": pages,
               "positions": positions, "sections": sections})

    def honbun(self, body=None):
        text = body if body is not None else (
            "# 20 局で起きていたこと\n\n"
            "## ひとことで\n\n"
            "3 つの数を並べます。<!-- sec: 付録1/形勢の流れ -->\n"
            "持ち時間に到達した局があります。<!-- sec: 付録3/最後の局面 -->\n\n"
            "## 局面で見る\n\n"
            "盤を 2 つ置きます。<!-- sec: 付録3/分かれ道 -->\n"
        )
        write(f"{self.d}/honbun.md", text)
        return f"{self.d}/honbun.md"

    def args(self, sources=("付録1", "付録3"), honbun=None):
        argv = ["--honbun-md", honbun or self.honbun()]
        for name in sources:
            argv += ["--source-index", f"{self.d}/idx_{name}.json"]
        argv += ["--patient", f"{self.d}/patient.json", "--group", "3 分切れ負け",
                 "--prose", f"{self.d}/prose.json",
                 "--final-positions", f"{self.d}/finals.json",
                 "--direct", f"{self.d}/direct.json",
                 "--out", f"{self.d}/cover.md"]
        return EC.parse_args(argv)

    def build(self, **kw):
        return EC.build_md(self.args(**kw))


class ShapeTest(CoverTestBase):
    def test_00_three_rows_in_the_constant_order(self):
        """束ねるのが付録 1 + 3 なら **3 行**(付録ごとに 1 行ではない ― 実物を読んで確かめた形)。"""
        _, rows = self.build()
        self.assertEqual([(r["appendix"], r["section"]) for r in rows],
                         [("付録1", "形勢の流れ"), ("付録3", "最後の局面"), ("付録3", "分かれ道")])

    def test_01_section_column_prints_the_appendix_own_title(self):
        """「節」の列は**付録の中に印字される題**を出す(索引の鍵ではない)。"""
        text, _ = self.build()
        self.assertIn("1. 25 局の形勢の流れ", text)
        self.assertIn("2. 最後の局面をエンジンで読むと", text)
        self.assertIn("3. 浅い読みで見えた分かれ道", text)

    def test_02_the_renamed_old_title_never_appears(self):
        """改名した旧い題が表紙に戻らない(正本 §9 ― 写せば直しが戻る)。"""
        text, _ = self.build()
        self.assertNotIn("盤上はこう勝てた", text)

    def test_03_numbers_come_from_the_material(self):
        """数は材料から。**材料を変えたら表紙の数も変わる**(表紙が自分で数を作っていない証拠)。"""
        self.material(games=7, featured=2, finals=4, forks=11)
        text, _ = self.build()
        self.assertIn("7 局の形勢の流れ", text)
        self.assertIn("持ち時間に到達した 4 局", text)
        # 2026-09-29(P-179): 型が「…分かれ道は {forks} 局面ありました。この冊子に載せているのは…
        # {bundled_forks} 局面です」に変わった。**材料の数(11)と束に入る数(この材料では 0)は別物。**
        self.assertIn("分かれ道は 11 局面ありました", text)
        self.assertIn("含む 0 局面です", text)
        # 「形勢が大きく動いた M 局を 1 局ずつ」は**「そのほかの局」の行**に移った
        # (2026-09-29。司令塔の判断 (a)。下の test_03b が本編から指した場合を測る)。
        self.assertNotIn("形勢が大きく動いた", text)

    def test_03b_the_other_games_row_carries_the_split_half(self):
        """**中身は節ごと**(4 人目の固定文を「と、」で割った片方が「そのほかの局」の行に出る)。

        割った理由(2026-09-29。司令塔の判断 (a)): 表の行が節ごとになったのに中身が 2 つの節の話を
        していて、**束ねた付録 1 が折れ線 1 ページだけのとき、束ねていない中身を言っていた**(実物で出た)。
        題の数(`rest`)は `games - featured` で出す ― **`_mid.py` 側に「この引き算と一致すること」の
        検査を置いてある**(食い違えば組版が落ちる)。
        """
        self.material(games=7, featured=2, finals=4, forks=11)
        honbun = self.honbun(
            "## ひとことで\n\n数<!-- sec: 付録1/形勢の流れ -->\n"
            "残り<!-- sec: 付録1/そのほかの局 -->\n\n"
            "## 局面で見る\n\n盤<!-- sec: 付録3/分かれ道 -->\n")
        text, rows = self.build(honbun=honbun)
        self.assertEqual([(r["appendix"], r["section"]) for r in rows],
                         [("付録1", "形勢の流れ"), ("付録1", "そのほかの局"), ("付録3", "分かれ道")])
        self.assertIn("2. そのほかの 5 局", text)           # 7 - 2
        # **1 局ずつのページを約束しない**(2026-09-29。P-171)。この節のページに在るのは
        # 「そのほかの局」の一覧(局・先後・結果・手数・形勢の変化)だけで、
        # **1 局ずつのページは束に入らない**(元の付録の 3〜19 ページ目。実測 2026-09-29)。
        self.assertIn("そのほかの 5 局の一覧(先後・結果・手数・形勢の変化)", text)
        self.assertNotIn("1 局ずつ", text)
        # 「形勢の流れ」の行は**束ねた範囲だけ**を言う。
        flow = next(r for r in rows if r["section"] == "形勢の流れ")
        self.assertEqual(flow["content"], "3 分切れ負け 7 局の形勢の流れ")

    def test_04_the_customer_name_is_not_printed(self):
        """表紙に顧客の名前を入れない(3 人目の実物は入っていた ― 廃止済み)。"""
        text, _ = self.build()
        self.assertNotIn("この名前は表紙に出てはいけない", text)

    def test_05_frame_comes_from_the_constants(self):
        """枠の 4 要素が揃っている(実物 4 人目から写した固定文)。"""
        text, _ = self.build()
        self.assertTrue(text.startswith(f"# {EI.COVER_HEADING}"))
        self.assertIn(EI.COVER_TABLE_HEADING, text)
        self.assertIn(EI.COVER_TAIL, text)
        self.assertIn("本編「25 局で起きていたこと」", text)

    def test_06_reference_column_names_the_honbun_heading(self):
        """「本編との対応」は印の逆引き。**実物より粗い**(節の中の順番は印から出せない)。"""
        _, rows = self.build()
        self.assertEqual(rows[0]["ref"], "「ひとことで」")
        self.assertEqual(rows[2]["ref"], "「局面で見る」")

    def test_07_one_appendix_only_gives_one_row(self):
        """束ねる付録が 1 本なら表も 1 行(表は束ねたものだけを案内する)。"""
        _, rows = self.build(sources=("付録1",))
        self.assertEqual(len(rows), 1)


class MutationTest(CoverTestBase):
    def test_08_an_appendix_with_no_reference_at_all_is_an_error(self):
        """**索引を渡した付録が 1 行も持たないなら落ちる**(束ねられない付録の索引が渡されている)。

        2026-09-29 に契約を変えた: **指していない「節」は落とすのではなく載せない** ―
        束ねた付録に入るのは本編が指すページだけで、載せれば顧客は在りもしないページを案内される。
        書き手が節を 1 つ使わないだけで工程が止まるのは道具の不具合だった
        (実測: 書き手が「最後の局面」〈標本 1 局〉を使わないことにして止まった)。
        **付録ごと 1 行も無いのは引数の食い違い**なので、そちらは落とす。
        """
        honbun = self.honbun("## ひとことで\n\n数を並べます。<!-- sec: 付録1/形勢の流れ -->\n")
        with self.assertRaises(EC.ExitCoverError) as e:
            self.build(honbun=honbun)
        self.assertIn("付録3", str(e.exception))
        self.assertIn("1 つも指していない", str(e.exception))

    def test_08b_a_section_the_honbun_skips_is_simply_not_listed(self):
        """**使わなかった節は表に出ない**(行数は書き手が決める)。"""
        honbun = self.honbun(
            "## ひとことで\n\n数を並べます。<!-- sec: 付録1/形勢の流れ -->\n\n"
            "## 局面で見る\n\n盤<!-- sec: 付録3/分かれ道 -->\n")
        text, rows = self.build(honbun=honbun)
        self.assertEqual([(r["appendix"], r["section"]) for r in rows],
                         [("付録1", "形勢の流れ"), ("付録3", "分かれ道")])
        # 番号は詰まる(1. 2. で、3. は無い)。
        self.assertIn("1. 25 局の形勢の流れ", text)
        self.assertIn("2. 浅い読みで見えた分かれ道", text)
        self.assertNotIn("最後の局面", text)

    def test_09_dev_section_marks_are_ignored(self):
        """**「書いた側の記録」の節の印は読まない**(`exit_render.py` と同じ扱い)。

        dev 節の中だけで指された節は**表に出ない**。
        (2026-09-29 に「落ちる」から「出ない」へ ― 契約が変わったので、**出力で測る**。)
        """
        honbun = self.honbun(
            "## ひとことで\n\n数を並べます。<!-- sec: 付録1/形勢の流れ -->\n"
            "<!-- sec: 付録3/最後の局面 -->\n\n"
            "## 書いた側の記録(顧客には見せない)\n\n"
            "<!-- sec: 付録3/分かれ道 -->\n")
        text, rows = self.build(honbun=honbun)
        self.assertEqual([(r["appendix"], r["section"]) for r in rows],
                         [("付録1", "形勢の流れ"), ("付録3", "最後の局面")])
        self.assertNotIn("分かれ道", text)

    def test_09b_the_dev_section_marker_is_the_one_check_answer_uses(self):
        """dev 節の印を**写していない**ことを確かめる(`check_answer` の正規表現で照合)。"""
        self.assertIsNotNone(CA.DEV_SECTION_RE.search("## 書いた側の記録(顧客には見せない)"))

    def test_10_unknown_appendix_in_the_index_is_an_error(self):
        """表紙に出す節を持っていない付録は落とす(黙って行を飛ばさない)。"""
        write(f"{self.d}/idx_付録9.json", {"appendix": "付録9", "source": "x.pdf",
                                          "pages": 1, "positions": {}, "sections": {}})
        with self.assertRaises(EC.ExitCoverError) as e:
            self.build(sources=("付録9",))
        self.assertIn("表紙に出す節を持っていない付録", str(e.exception))

    def test_11_the_same_index_twice_is_an_error(self):
        """同じ付録の索引が 2 回渡されたら落とす(表が二重になる)。"""
        with self.assertRaises(EC.ExitCoverError) as e:
            self.build(sources=("付録1", "付録1"))
        self.assertIn("2 回渡された", str(e.exception))

    def test_12_missing_games_in_the_material_is_an_error(self):
        """数の出どころが無いのに表紙を作らない。"""
        write(f"{self.d}/patient.json", {"summary": {}})
        with self.assertRaises(EC.ExitCoverError) as e:
            self.build()
        self.assertIn("summary.games", str(e.exception))


class ConstantsTest(unittest.TestCase):
    def test_13_cover_sections_are_members_of_appendix_sections(self):
        """**写しを 2 か所に持たない**(司令塔の条件 2026-09-28)。

        表紙に出す節の名前は、索引の節の一覧に実在するものだけ。
        """
        for appendix, names in EI.COVER_SECTIONS.items():
            self.assertIn(appendix, EI.APPENDIX_SECTIONS, f"知らない付録: {appendix}")
            for name in names:
                self.assertIn(name, EI.APPENDIX_SECTIONS[appendix],
                              f"{appendix} に無い節: {name}")

    def test_14_every_cover_section_has_a_title_and_a_content(self):
        """表に出す節はすべて、題と中身の型を持つ(片方だけ足すと表が崩れる)。"""
        for appendix, names in EI.COVER_SECTIONS.items():
            for name in names:
                self.assertIn((appendix, name), EI.SECTION_TITLES)
                self.assertIn((appendix, name), EI.COVER_CONTENT)

    def test_15_section_titles_are_shared_with_the_renderers(self):
        """組版が**同じ定数から**題を出している(文字列を写していない)。

        写しがあると、題を直しても表紙だけ古いままになる。
        """
        for base in ("_mid.py", "render_direct.py"):
            src = open(os.path.join(HERE, base), encoding="utf-8").read()
            self.assertIn("exit_index.section_title(", src, f"{base} が題を定数から引いていない")
        for (appendix, name), template in EI.SECTION_TITLES.items():
            fixed = template.replace("{games}", "").strip()
            if not fixed:
                continue
            for base in ("_mid.py", "render_direct.py"):
                src = open(os.path.join(HERE, base), encoding="utf-8").read()
                self.assertNotIn(f'"{fixed}"', src,
                                 f"{base} に題「{fixed}」の写しが残っている")

    def test_16_unknown_section_title_is_an_error(self):
        """知らない節の題を黙って鍵のまま出さない。"""
        with self.assertRaises(ValueError):
            EI.section_title("付録1", "調べたこと")


class WordingExistsInToolsTest(unittest.TestCase):
    """**中身の欄の語は、いまの道具に実在する行から採る。**

    実物の中身はそのまま写せない ― 4 人目は「時計で終わった」(道具に 0 件)、
    3 人目は「時間切れ」(2026-09-27 に断定をやめた語)を使っている。
    **実在しない語は「写し」ではなく「新しい文」**で、承認の対象になる(司令塔の決定 2026-09-28)。

    **一覧を手で並べるだけにしない**(§40 ― 手の一覧は代表だけになる)。
    型の中の日本語のひとつづきが、**どれも宣言した語句のどれかに入っている**ことも確かめる。
    """

    # 中身の型に出る語句。**道具に実在することを test_17 が測り、
    # 型を覆っていることを test_18 が測る**(どちらか一方だけでは足りない ―
    # 実在だけ見ると型の残りが野放しになり、覆いだけ見ると実在しない語が通る)。
    # 2026-09-29(P-171): 「形勢が大きく動いた」「1 局ずつ」を**外した** ―
    # 「そのほかの局」の中身が**束ねていない 1 局ずつのページを約束していた**ため、
    # その節のページに実際に在る欄(一覧・先後・結果・手数・形勢の変化)を言う型に変えた。
    PHRASES = ["形勢の流れ", "そのほかの", "局の一覧", "先後", "結果", "手数", "形勢の変化",
               "持ち時間に到達した", "最後の局面を", "エンジンで読んだ手順",
               "実戦の手と第 1 候補", "の評価差が見えた分かれ道は", "局面ありました",
               "この冊子に載せているのは、そのうち本編で引いた局面を含む", "局面です", "局面つき"]

    # **司令塔が書いて承認した新しい文**(2026-09-29。P-179)。`COVER_HEADING` などの枠と同じ扱いで、
    # **「道具に実在する語」の検査(test_17)から外す** ― 枠が外れている理由と同じで、
    # **この言い方を持つ道具がまだ無い**(表紙が初めて言う)。
    # 外す代わりに**ここに名前で並べる**(検査をゆるめるのではなく、例外を一覧にする)。
    # 元の型は「…見えた {forks} 局面。実戦の手と第 1 候補を局面つきで並べています」で、
    # **束に入るのは 9 局面なのに 103 並んでいると読めた**(P-179)。
    APPROVED_NEW_PHRASES = ["この冊子に載せているのは、そのうち本編で引いた局面を含む",
                            "の評価差が見えた分かれ道は", "局面です", "局面つき"]
    # **型を置いているファイル自身を数から除く。**除かないと**循環する** ―
    # 型に書いた語はそのファイルに存在するので、どんな新語でも「道具にある」ことになる
    # (実測: 「盤つき」を 1 件と数えたが、その 1 件は `exit_index.py` の型自身だった)。
    SCAN = ["scripts/playtest", ":!scripts/playtest/out", ":!scripts/playtest/records",
            ":!*_test.py", ":!*.test.ts",
            ":!scripts/playtest/report-pdf/exit_index.py",
            ":!scripts/playtest/report-pdf/exit_cover.py"]

    def test_16b_the_scanned_repo_is_really_the_repo(self):
        """**語の実在を測る場所が本当にリポジトリか**を先に確かめる。

        ここが違う場所を指していると、`git grep` が何も見つけずに
        「道具に無い語」と言い続けるか、逆に何も測っていないのに通る。
        """
        self.assertTrue(os.path.isfile(os.path.join(REPO, "CLAUDE.md")),
                        f"リポジトリの根ではない: {REPO}")

    def test_17_every_declared_phrase_exists_in_the_tools(self):
        for phrase in self.PHRASES:
            if phrase in self.APPROVED_NEW_PHRASES:
                continue   # 司令塔が承認した新しい文(上の注)。**一覧に名前が在ることが例外の根拠。**
            r = subprocess.run(["git", "grep", "-l", phrase, "--", *self.SCAN],
                               capture_output=True, text=True, cwd=REPO)
            files = [ln for ln in r.stdout.splitlines() if ln.strip()]
            self.assertTrue(files, f"道具に無い語を中身に書いている: 「{phrase}」"
                                   f"(実物にしかない言い回しは『新しい文』なので承認が要る)")

    def test_17b_the_approved_new_phrases_are_really_in_the_templates(self):
        """**例外の一覧に、型に出てこない語を書けないようにする。**

        書けてしまうと、`APPROVED_NEW_PHRASES` が「検査を外す抜け道」になる。
        """
        joined = "".join(EI.COVER_CONTENT.values())
        for phrase in self.APPROVED_NEW_PHRASES:
            self.assertIn(phrase, joined, f"型に無い語を例外にしている: 「{phrase}」")
        self.assertTrue(set(self.APPROVED_NEW_PHRASES) <= set(self.PHRASES),
                        "例外が PHRASES に入っていない(test_18 の敷き詰めから漏れる)")

    def test_18_the_declared_list_tiles_the_templates(self):
        """**宣言した語句で型を敷き詰められるか**を機械で見る(一覧の抜けを人の目に頼らない)。

        「どれかに入っているか」では**短い語句 1 つで覆われたことになってしまう**
        (「形勢」を宣言すると「局の形勢と、形勢が大きく動いた」が丸ごと通る)。
        だから**型から宣言した語句を取り去って、日本語が残らないこと**を見る。
        残れば、それは**道具から採っていない、書くときに作った語**である。
        """
        for key, template in EI.COVER_CONTENT.items():
            # 鍵に `_` が入るもの(`{bundled_forks}`。2026-09-29)も外す ―
            # 外さないと、型に残った `{bundled_forks}` を「覆えない日本語」と数えかける。
            rest = re.sub(r"\{[a-z_]+\}", "\x00", template)
            for phrase in sorted(self.PHRASES, key=len, reverse=True):
                rest = rest.replace(phrase, "\x00")
            leftovers = [r for r in CJK_RUN.findall(rest) if len(r.strip("、。")) >= 3]
            self.assertEqual(leftovers, [],
                             f"{key} の型に、宣言した語句で覆えない日本語が残っている: {leftovers}"
                             f"(道具にある語なら一覧に足す。無ければ型を直す)")


class CheckAnswerTest(CoverTestBase):
    def test_19_no_banned_word_in_the_cover(self):
        """表紙の文に禁止語を入れない(`check_answer.py` の一覧を import ― 語を写さない)。"""
        text, _ = self.build()
        banned = [w for w in CA.BANNED_WORDS if w and w in text]
        self.assertEqual(banned, [], f"表紙に禁止語: {banned}")

    def test_20_the_cover_asserts_nothing(self):
        """断定しない(CLAUDE.md 5 番 (3))。表紙は案内なので、良し悪しを言う語を置かない。"""
        text, _ = self.build()
        for word in ("べき", "間違い", "正しい手", "良い手", "悪い"):
            self.assertNotIn(word, text, f"表紙に断定の語: {word}")


class PositionMarkRefTest(CoverTestBase):
    """**局面の印からの逆引き**(2026-09-29。司令塔の ⑥ が実物で見つけた D2)。

    局面の印を読まないと、**節の印を置いた 1 か所の見出しが 3 行とも並ぶ** ―
    実物で「本編との対応」列が 3 行とも「数の出どころを引ける付録」になった。
    顧客は「どの節から引ける付録か」が分からない。
    """

    def setUp(self):
        super().setUp()
        # 付録 3: 最後の局面 = p2 から、分かれ道 = p4 から。局面 16/93 は p5(= 分かれ道の中)。
        self.index_with_pages("付録3",
                              {"3 分": {"16/93": 5, "1/20": 3}},
                              {"最後の局面": 2, "分かれ道": 4})

    def honbun_with_pos(self):
        return self.honbun(
            "# 25 局で起きていたこと\n\n"
            "## ひとことで\n\n"
            "数を並べます。<!-- sec: 付録1/形勢の流れ -->\n\n"
            "## 局面で見る\n\n"
            "この局面です<!-- pos: 16/93 付録3 3 分 -->\n\n"
            "## 数え方\n\n"
            "付録で引けます。<!-- sec: 付録3/最後の局面 -->\n")

    def test_p0_a_position_mark_counts_as_a_reference_to_its_section(self):
        """**局面が在る節**への参照として数える(どの節かは索引から決める)。"""
        text, rows = self.build(honbun=self.honbun_with_pos())
        by = {(r["appendix"], r["section"]): r["ref"] for r in rows}
        # 16/93 は p5 = 分かれ道(p4 から)の中。**本編の「局面で見る」から引ける**。
        self.assertEqual(by[("付録3", "分かれ道")], "「局面で見る」")
        # 節の印は書かれた見出しのまま。
        self.assertEqual(by[("付録3", "最後の局面")], "「数え方」")
        self.assertEqual(by[("付録1", "形勢の流れ")], "「ひとことで」")

    def test_p4_the_cover_says_how_many_positions_the_bundle_holds(self):
        """**表紙の「この冊子に載せているのは N 局面」の N は、束に入る数**(P-179。2026-09-29)。

        直す前は材料の全部(103)を出していて、**束に入るのは 9 局面なのに 103 並んでいると読めた**
        (1 周目から 3 周続いた家族。5 周目の席 (a) も挙げた)。

        この材料: 付録 3 の索引は「分かれ道」が p4 から。本編は **16/93(p5)の局面の印**と
        **「最後の局面」(p2)の節の印**を引くので、**束に入るページは p2 と p5 の 2 枚**。
        p5 には「分かれ道」の局面を **4 つ**(16/93・17/99・18/105・19/111)置き、p3 にもう 1 つ(1/20)置く。
        したがって答えは **4**。

        **近くにある数を全部ずらしてある** ― 材料の全部 **103**・本編の印の数 **3**(付録 1 の節 1 +
        付録 3 の局面 1 + 付録 3 の節 1)・束のページ数 **2**・節の外の局面 **1**・答え **4**。
        **同じ数にすると、別のものを返す変異が緑のまま通る**(実測 2026-09-29 に 2 回踏んだ:
        最初は答え 2 = 束のページ数 2 で `len(pages)` が通り、次は答え 3 = 印の数 3 で
        `len(marks_of(...))` が通った)。**「近い数を全部ずらす」まで変異を回し直すこと。**
        """
        self.material(forks=103)
        self.index_with_pages("付録3",
                              {"3 分": {"16/93": 5, "17/99": 5, "18/105": 5, "19/111": 5, "1/20": 3}},
                              {"最後の局面": 2, "分かれ道": 4})
        text, _ = self.build(honbun=self.honbun_with_pos())
        self.assertIn("分かれ道は 103 局面ありました", text)
        self.assertIn("含む 4 局面です", text)
        for wrong in ("含む 103 局面です", "含む 1 局面です", "含む 2 局面です", "含む 3 局面です",
                      "含む 5 局面です"):
            self.assertNotIn(wrong, text, f"束に入る数が {wrong} になっている")

    def test_p1_the_section_is_chosen_by_page_not_by_order(self):
        """節は**ページで決める**(索引の辞書の並び順ではない)。

        1/20 は p3 = 最後の局面(p2 から)の中で、分かれ道(p4)より前。
        """
        self.assertEqual(EC.section_of_position(
            {"positions": {"3 分": {"1/20": 3}}, "sections": {"最後の局面": 2, "分かれ道": 4}},
            "3 分", "1/20"), "最後の局面")
        self.assertEqual(EC.section_of_position(
            {"positions": {"3 分": {"16/93": 5}}, "sections": {"最後の局面": 2, "分かれ道": 4}},
            "3 分", "16/93"), "分かれ道")

    def test_p2_an_unknown_position_is_not_guessed(self):
        """索引に無い局面は**黙って別の節に混ぜない**(None を返す)。

        **1 ページ目から始まる節がある索引で測る。**最初は `sections` が `{"分かれ道": 4}` だけの
        索引で測っていたが、**「引けなければ 1 ページ目とみなす」変異でも None のまま**だった
        (4 ページ目より前に節が無いため)。**校正で黙ったので、1 ページ目の節を置いて測る。**
        """
        index = {"positions": {"3 分": {"1/20": 3}}, "sections": {"読み方": 1, "分かれ道": 4}}
        self.assertIsNone(EC.section_of_position(index, "3 分", "99/1"))
        # 在る局面はちゃんと引ける(上の None が「何も引けない」ではないことの対照)。
        self.assertEqual(EC.section_of_position(index, "3 分", "1/20"), "読み方")
        # 節が 1 つも無ければ決められない。
        self.assertIsNone(EC.section_of_position(
            {"positions": {"3 分": {"1/20": 3}}, "sections": {}}, "3 分", "1/20"))

    def test_p3_a_position_pointing_at_an_unbundled_appendix_is_skipped(self):
        """束ねていない付録の局面の印は無視する(落とすのは束ねの側の仕事)。"""
        refs = EC.honbun_refs("## 局面で見る\n\n盤<!-- pos: 5/59 付録4 3 分 -->\n", {})
        self.assertEqual(refs, {})

    def test_p4_a_broken_position_mark_falls(self):
        """印の形が崩れていれば落ちる(黙って飛ばさない)。"""
        with self.assertRaises(EC.ExitCoverError):
            EC.honbun_refs("## 局面で見る\n\n盤<!-- pos: こわれた -->\n", {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
