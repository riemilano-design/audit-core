# -*- coding: utf-8 -*-
# STEP CUSTOMER-EXIT。**局面・節 → 付録のページの索引を、置いた経路が書く**ための 1 か所
# (docs/STEP_CUSTOMER_EXIT_SPEC_2026-09-28.md §3 の 2 と、2026-09-28 の司令塔の追補)。
#
# 【なぜ 1 か所に置くか】節の固定名を**組版と `check_structure.py` が同じ定数で見る**(片方に文字列を
# 書き写さない)。`Board` と `parse_sfen` が 4 実装に散った P-111 と同じ病気を、索引では作らない。
#
# 【鍵の形は新しく作らない】**付録ごとの鍵の形は、`check_answer.py` の検査 7 がその付録について受ける形そのまま**:
# - **付録 1**(`_mid.py`): `局/手`(`prose.json` の `scenes[].ply`。組は無い)
# - **付録 3**(`render_direct.py`): **`組 → 局/手`**(局番号は組ごとに 1 から振られ、組をまたいで衝突する
#   ― 2026-09-25 の凍結の例外 7b。本編の印も `<!-- pos: 局/手 付録3 組 -->`)
# 平らな鍵に組を混ぜる形(`"C7/5/59"`)は採らない ― **組の有無が辞書の中で見えなくなる。**
#
# 【reportlab はページ番号を組んだ後にしか知らない】局面は流し込みで連続して並ぶ(`PageBreak` は数か所だけ)。
# だから `doc.afterFlowable` で **`doc.page` を読むだけ**にする。**flowable は 1 つも足さない**
# (足すと組版が変わる)。変わっていないことは、ページ数・ページごとの文字・**ベクタ描画の形**で測る
# (盤は埋め込み画像ではないので `get_images()` は 0 を返す ― 実測 2026-09-28)。
import json
import os

# 節の固定名。**印字される文字は鍵にしない** ― 印字は「25 局の形勢の流れ」のように顧客ごとに局数が入る。
# `check_structure.py` はこの定数を import して見る(文字列を写さない)。
APPENDIX_SECTIONS = {
    "付録1": ["調べたこと", "読み方", "形勢の流れ", "そのほかの局", "通して見えたこと"],
    "付録3": ["読み方", "印の数", "最後の局面", "分かれ道"],
}
# 付録 2(`render_whatif.py`)・付録 4(`render_time_cause.py`)は**まだ入れない**
# (両実物で付録 2 のページは 0 枚。本編が指すことになったら足す ― 司令塔の判断 2026-09-28)。


# ==================== 節の「印字される題」 ====================
# **索引の鍵と、付録の中に印字される題は別物。**鍵は `最後の局面`、印字は `最後の局面をエンジンで読むと`。
# **表紙の「節」の列は印字される題を出す** ― 表紙が節を別の名前で呼ぶと、顧客がページを探せない。
# **だから題も 1 か所に集める**(`_mid.py`・`render_direct.py`・表紙の 3 か所に写しを持たない ― P-111 の病気)。
# 付録 1 の題には**局数が入る**ので、値ではなく型で持つ。
SECTION_TITLES = {
    ("付録1", "形勢の流れ"): "{games} 局の形勢の流れ",
    # `rest` = 1 局ずつ見た局を除いた残り。**`_mid.py` がこの型で印字し、同じ関数から作る**
    # (2026-09-29 に足した ― 表紙がこの節を載せられるようにするため)。
    ("付録1", "そのほかの局"): "そのほかの {rest} 局",
    ("付録3", "最後の局面"): "最後の局面をエンジンで読むと",
    ("付録3", "分かれ道"): "浅い読みで見えた分かれ道",
}


def rest_count(games, featured):
    """「そのほかの局」の数 = 全部 − 1 局ずつ見た局。**引き算はここだけ**(2026-09-29)。

    **3 か所で同じ引き算をしていた** ― `exit_candidates.rest_games`・`exit_cover.numbers_of`・
    `_mid.py` の `assert`。`_mid.py` の `assert` は**自分が作った一覧と自分の引き算**を比べるだけで、
    別プロセスの 2 つが同じ形で引いていることは確かめられない(2026-09-29 の独立監査が実測 ―
    `exit_candidates` 側だけを変えても試験が 1 本も落ちなかった)。**題を持つこのモジュールに 1 本置く。**
    """
    return int(games) - int(featured)


def section_title(appendix, name, **numbers):
    """印字される題を 1 か所から引く。**知らない組み合わせは落とす**(黙って鍵をそのまま出さない)。"""
    if (appendix, name) not in SECTION_TITLES:
        raise ValueError(f"題を持っていない節: {appendix}/{name}(SECTION_TITLES が正本)")
    return SECTION_TITLES[(appendix, name)].format(**numbers)


# ==================== 数え方の固定文 ====================
# **`render_front.py` から移した**(2026-09-29。写していない ― あちらは `sys.argv` を読んで走る形で
# import できないため、`exit-candidates` が写せば同じ文が 2 か所になる)。
# **機械の分類の説明**であり、顧客に見せる固定文(正本の「数え方」の節)。
# 評価の揺れの注記(`finding_texts.json` の `evalJitterNote`)は材料から来るので**ここには置かない**。
# **行動が 0 本のときの固定文**(2026-09-29。司令塔の判断 ― 差が無ければ行動にしない)。
# 家の言い方に合わせる(`render_front.py` の「今回は、上に書ける数がありませんでした。」と同じ形)。
NO_ACTION_SENTENCE = "今回の数からは、試せることとして出せる行動がありませんでした。"

# **「なぜこの N つだけなのか」の 1 文**(2026-09-29)。批評席 (b)(GPT)の提案文をそのまま採る ―
# 3 席が 2 周続けて「選定の基準が読めない」を挙げ、(b) が「大きな説明は要らない・この 1 文でかなり閉じる」
# と具体案を出した。**その文が候補の段の実際の選び方(`MENU_HOLDS` 真 + 分数を印字できる)と一致する**
# ことを確かめてから採った。**局数は型に入れる**(D1 と同じ ― 直書きすると別の顧客の冊子で食い違う)。
SELECTION_SENTENCE_TEMPLATE = ("今回は、判定で差が確認でき、次の {games} 局で同じ数を"
                               "測り直せるものだけを「試せること」にしました。")

# **「無いものは無いと書きます。」**(4 人目の実物の型。2026-09-29)。
# 4 人目の本編 p1 の 3 本目は「長く考えた手で崩れる、という形はこの 18 局には出ていません。
# 無いものは無いと書きます。」で、**行動にしない理由を明示した 1 本**だった(P-164)。
#
# **前half(「〜という形は出ていません」)の主語は道具が作らない。** 4 人目のあの主語
# (「長く考えた手で崩れる」)は書き手が材料の数(10 秒以上で 0 / 8)から書いたもので、
# **材料のどこにも文として無い**(実測 2026-09-29)。道具が埋めれば、**私が将棋の言い方を決める**ことになる。
# したがって出すのは**この尾の 1 文**と、下の「否定の型の承認済みの文」だけ。
NOTHING_TO_HIDE_SENTENCE = "無いものは無いと書きます。"


def selection_sentence(games):
    """「なぜこの N つだけなのか」の 1 文。**組版と門が同じここから作る。**"""
    return SELECTION_SENTENCE_TEMPLATE.format(games=int(games))

COUNTING_NOTES = [
    "「かけた時間」は、棋譜に書かれた秒をそのまま使います(切り捨ての整数)。0〜1 秒・2〜4 秒・5〜9 秒・10 秒以上の 4 段に分けます。",
    "「崩れ」は、直前の評価の区分(優勢・互角・劣勢)が優勢または互角だった局面から、直後に区分が 1 段以上下がったことです。+300 以上を優勢、−300 以下を劣勢、その間を互角とします。",
    # STEP ENDING_CLOCK §4 の 11(計画の直し、904d317)。「終局の種類が切れ負けで」だけでは、
    # 終局の語が投了でも時計(累計消費時間 = 持ち時間)が一致した局(§3 の (1))を含められず、直した後は偽になる。
    "「持ち時間に到達した局」は、本人が負けた局のうち、終局の種類が切れ負けだった局、または本人の累計消費時間が持ち時間とぴったり一致した局です。",
    "「優勢から負けた対局」は、対局中に一度でも評価が +300 以上になり、その対局の結果が負けだった局の数です。",
    "この報告の数は、棋力や手の良し悪しを表す数ではありません。",
]


# ==================== 表紙 ====================
# **表紙の表に出す節**(付録ごとの並び。**付録の全部の節ではない** ― 実物は付録 1 の 5 節のうち
# 「形勢の流れ」1 行だけを出し、付録 3 は 2 行出す)。**実物 2 件を fitz で読んで確かめた形**
# (4 人目 17p の p1・3 人目 v3 23p の p1。どちらも 4 行で、付録 3 が 2 行)。
# 正本 §8 の「束ねた付録ごとに 1 行」は司令塔の書き誤りで、同じ表のデータ(実測)の方が正
# (2026-09-28 に自動化レーンが実物を読んで指摘、司令塔が訂正)。
# **束ねるのは付録 1 + 付録 3 なので表は 3 行になる。**
# **2026-09-29 に「そのほかの局」を足した**(司令塔の判断 (a))。
# 表の行が節ごとになったので、**中身も節ごとの型**にする ― それまで「形勢の流れ」の中身が
# 「…形勢の流れと、形勢が大きく動いた M 局を 1 局ずつ」で、**束ねた付録 1 が折れ線 1 ページだけのとき、
# 束ねていない中身を言っていた**(実物で出た)。
# **載るのは本編が指した節だけ**なので、足しても指されなければ表に出ない(`exit_cover.build_rows`)。
COVER_SECTIONS = {
    "付録1": ("形勢の流れ", "そのほかの局"),
    "付録3": ("最後の局面", "分かれ道"),
}

# **表紙の枠の固定文。**出どころは **4 人目の実物**(`kori/deliver1_送付用/2_付録_数の出どころ.pdf` の p1 を
# fitz で読んだもの。mtime `2026-09-25T07:06`)。**改名の一覧(§9・§10)を通してある。**
# 3 人目 v3 からは写していない ― 3 人目の末尾には **2026-09-24 に廃止した免責 2 文**が付いており、
# 段落にも顧客の名前が入っている(「〇〇さんを下にして」)。**4 人目の形が現行**(正本 §8 (iv))。
# **この 5 つは「道具に実在する語」の検査を通らない** ― 表紙を作る道具がこれまで無かったため
# (`git grep` で 0 件。実測 2026-09-28)。**枠の根拠は道具ではなく実物**で、
# 中身の欄のように本編の言い方を写すものとは分けて扱う。
COVER_HEADING = "付録 ― 数の出どころ"
COVER_LEAD = ("本編「{games} 局で起きていたこと」の数と局面を、ここで引けます。"
              "読み通すものではなく、本編で気になった数の出どころを確かめるための冊子です。")
COVER_TABLE_HEADING = "この冊子に入っているもの"
COVER_TABLE_COLUMNS = ("節", "中身", "本編との対応")
COVER_TAIL = ("盤の図は、後手番の局でも本人を下にして回しています。"
              "エンジンの候補は「正解」ではなく、比べるための材料です。")

# **「中身」の欄の型。**数は材料から入れ、**新しい数は作らない**(正本 §8 (ii))。
# **語はすべて道具に実在する行から採った**(司令塔の条件 2026-09-28。実測の件数を添える):
# - 「形勢の流れ」「形勢が大きく動いた」「1 局ずつ見ていきます」「途中で優勢だった」 ― `_mid.py`(各 1〜2 件)
# - 「最後の局面をエンジンで読むと」 ― `answer_facts.py`・`render_direct.py`(2 件)
# - 「持ち時間に到達した」 ― 8 件(`answerMenu.ts` ほか。**「時計で終わった」は 0 件なので使わない**)
# - 「実戦の手と第 1 候補」 ― 3 件、「浅い読みで見えた分かれ道」 ― 6 件
# **実物の中身の欄はそのまま写せない** ― 4 人目は「時計で終わった」(道具に 0 件)、
# 3 人目は「時間切れ」(2026-09-27 `5bb7ae9` で断定をやめた語)を使っている(実測 2026-09-28)。
# **最初に書いた型は「第 1 候補との差」で、これも道具に無かった**(道具は「実戦の手と第 1 候補の差が見えた」)。
# `exit_cover_test.py` の敷き詰めの試験が捕まえた ― **語を道具から採ると決めても、書くときに崩れる。**
# **2 つ目に踏んだ穴**: 「盤つき」も道具に無かった(道具は「局面つきで」)。最初は 1 件と数えたが、
# **その 1 件はこのファイル自身**だった ― 実在の検査が自分の型を数えていた(循環)。
# `exit_cover_test.py` の検査は `exit_index.py`・`exit_cover.py` を数から除く。
# **2026-09-29: 4 人目の固定文を「と、」で 2 つに割った**(司令塔の判断 (a)。**新しい語は作らない**)。
# 割る前: 「{group} {games} 局の形勢の流れと、形勢が大きく動いた {featured} 局を 1 局ずつ」
# 割った理由: **表の行が節ごとになったので、中身も束ねた範囲だけを言う。**
COVER_CONTENT = {
    ("付録1", "形勢の流れ"): "{group} {games} 局の形勢の流れ",
    ("付録1", "そのほかの局"): "形勢が大きく動いた {featured} 局を 1 局ずつ",
    ("付録3", "最後の局面"): "持ち時間に到達した {finals} 局の最後の局面を、エンジンで読んだ手順",
    ("付録3", "分かれ道"): "長く読まなくても実戦の手と第 1 候補の差が見えた {forks} 局面。実戦の手と第 1 候補を局面つきで並べています",
}


# **束ねた索引の上の階層に置いてよい鍵**(`exit-render` が新しく書く 5 つ)。
# **ここが正本の 1 か所** ― `exit_render.py`(書く側)と `check_structure.py`(読む側)の両方が import する。
# **写しを 2 か所に持たない**(写しは片方だけ直る ― §8「分けて書くだけでは足りない。分けられない形で書く」)。
# **接頭辞では判定しない**(付録名の付け方に依存させず、知らない鍵が黙って混ざる道も閉じる)。
# 付録名は `--source-index` で渡されたものだけを許す。
EXIT_RENDER_KEYS = ("outputPositions", "appendixPages", "boardsDrawn", "hasCover", "sourcePages")

# **このモジュールは定数だけを置く。**reportlab・fitz・pypdf などの組版の道具は import しない
# ― **門(`check_structure.py`)が import するのは「定数」であって「組版」ではない**、を保つため
# (司令塔の条件 2026-09-28)。`exit_render_test.py` が import 文を見て固定している。

def pos_key(game_no, ply):
    """本編の `<!-- pos: 局/手 付録N -->` と同じ鍵の形(変換を挟まない)。"""
    return f"{int(game_no)}/{int(ply)}"


class PageIndexRecorder:
    """組んだ結果のページ番号を記録して、PDF の隣に索引を書く。

    `grouped=True` の付録(付録 3)は `positions` を **組 → 局/手** の入れ子にする。
    **最初に置かれたページだけ**を採る(同じ節が分割されても先頭を指す)。
    """

    def __init__(self, doc, appendix, grouped=False):
        if appendix not in APPENDIX_SECTIONS:
            raise ValueError(f"知らない付録: {appendix}(APPENDIX_SECTIONS に足してから使う)")
        self.doc = doc
        self.appendix = appendix
        self.grouped = grouped
        self.positions = {}
        self.sections = {}
        doc.afterFlowable = self._record

    def mark_pos(self, flowable, game_no, ply, group=None):
        if self.grouped and group is None:
            raise ValueError(f"{self.appendix} の局面には組が要る(組をまたいで局番号が衝突する)")
        if not self.grouped and group is not None:
            raise ValueError(f"{self.appendix} の局面に組は書かない")
        flowable._index_pos = (group, pos_key(game_no, ply))
        return flowable

    def mark_sec(self, flowable, name):
        if name not in APPENDIX_SECTIONS[self.appendix]:
            raise ValueError(f"{self.appendix} に無い節の名前: {name}(APPENDIX_SECTIONS が正本)")
        flowable._index_sec = name
        return flowable

    def _record(self, flowable):
        pos = getattr(flowable, "_index_pos", None)
        if pos is not None:
            group, key = pos
            if group is None:
                self.positions.setdefault(key, self.doc.page)
            else:
                self.positions.setdefault(group, {}).setdefault(key, self.doc.page)
        name = getattr(flowable, "_index_sec", None)
        if name is not None:
            self.sections.setdefault(name, self.doc.page)

    def path_for(self, out_pdf):
        return os.path.splitext(out_pdf)[0] + "_page_index.json"

    def write(self, out_pdf):
        """**書けなければ落ちる**(黙って飛ばすと、索引の無い PDF が「できた」ことになる)。"""
        path = self.path_for(out_pdf)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"appendix": self.appendix, "source": os.path.basename(out_pdf),
                       "pages": self.doc.page, "positions": self.positions, "sections": self.sections},
                      f, ensure_ascii=False, indent=1, sort_keys=True)
        return path
