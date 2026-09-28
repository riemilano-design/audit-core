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
        self.assertIn("形勢が大きく動いた 2 局", text)
        self.assertIn("持ち時間に到達した 4 局", text)
        self.assertIn("差が見えた 11 局面", text)

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
    def test_08_section_not_pointed_at_by_honbun_is_an_error(self):
        """本編が指していない節を表に載せない(顧客が本編から辿れないページを案内される)。"""
        honbun = self.honbun("## ひとことで\n\n数を並べます。<!-- sec: 付録1/形勢の流れ -->\n")
        with self.assertRaises(EC.ExitCoverError) as e:
            self.build(honbun=honbun)
        self.assertIn("本編が指していない節", str(e.exception))

    def test_09_dev_section_marks_are_ignored(self):
        """**「書いた側の記録」の節の印は読まない**(`exit_render.py` と同じ扱い)。

        dev 節の中だけで指された節は「本編が指していない」として落ちる。
        **静かに skip する枝は置かない** ― `check_answer` の関数が無くなったら赤で気づく。
        """
        honbun = self.honbun(
            "## ひとことで\n\n数を並べます。<!-- sec: 付録1/形勢の流れ -->\n"
            "<!-- sec: 付録3/最後の局面 -->\n\n"
            "## 書いた側の記録(顧客には見せない)\n\n"
            "<!-- sec: 付録3/分かれ道 -->\n")
        with self.assertRaises(EC.ExitCoverError) as e:
            self.build(honbun=honbun)
        self.assertIn("付録3/分かれ道", str(e.exception))

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
    PHRASES = ["形勢の流れ", "形勢が大きく動いた", "1 局ずつ",
               "持ち時間に到達した", "最後の局面を", "エンジンで読んだ手順",
               "長く読まなくても実戦の手と第 1 候補の差が見えた", "実戦の手と第 1 候補",
               "局面つきで", "並べています"]
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
            r = subprocess.run(["git", "grep", "-l", phrase, "--", *self.SCAN],
                               capture_output=True, text=True, cwd=REPO)
            files = [ln for ln in r.stdout.splitlines() if ln.strip()]
            self.assertTrue(files, f"道具に無い語を中身に書いている: 「{phrase}」"
                                   f"(実物にしかない言い回しは『新しい文』なので承認が要る)")

    def test_18_the_declared_list_tiles_the_templates(self):
        """**宣言した語句で型を敷き詰められるか**を機械で見る(一覧の抜けを人の目に頼らない)。

        「どれかに入っているか」では**短い語句 1 つで覆われたことになってしまう**
        (「形勢」を宣言すると「局の形勢と、形勢が大きく動いた」が丸ごと通る)。
        だから**型から宣言した語句を取り去って、日本語が残らないこと**を見る。
        残れば、それは**道具から採っていない、書くときに作った語**である。
        """
        for key, template in EI.COVER_CONTENT.items():
            rest = re.sub(r"\{[a-z]+\}", "\x00", template)
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
