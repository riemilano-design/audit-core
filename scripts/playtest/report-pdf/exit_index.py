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
