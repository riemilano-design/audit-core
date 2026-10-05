# -*- coding: utf-8 -*-
# 指し手の字(日本語表記)の **1 か所**。
#
# 【出どころ】`render_direct.py`(付録 3)と `render_whatif.py`(付録 2)が同じコードを 2 つ持っていた
# (ZEN/KAN/PIECE/PROM・parse_sfen・sq・usi_squares・piece_kanji・move_kanji・mark)。
# ⑥ 束 3(2026-10-05。司令塔の裁定 5)で**移した**(写しではない ― 2 本の renderer はここを束縛する)。
# 【なぜ別 module か】2 本の renderer は冒頭で `sys.argv` を読んで走る(import できない)。
# ⑥(`exit_fill.py`)が本編の盤の見出しに「▲４四歩打」を書くには、import できる置き場が要る。
# 【ここに無いもの】盤を進める `apply_move`・`serialize_sfen`・向きを戻す `rotate_*`(`board_spec.py`)。
# **将棋の判断は無い** ― USI と局面から字を組むだけ(合法性も見ない)。
# 【副作用なし】argv・環境変数・ファイルを読まない(⑥ と試験が import する)。
from board_spec import RANKS  # マスの段の並びは `board_spec` の 1 か所

ZEN = "０１２３４５６７８９"
KAN = "〇一二三四五六七八九"
PIECE = {"p": "歩", "l": "香", "n": "桂", "s": "銀", "g": "金", "b": "角", "r": "飛", "k": "玉"}
PROM = {"p": "と", "l": "杏", "n": "圭", "s": "全", "b": "馬", "r": "竜"}


def parse_sfen(sfen):
    board_s, turn, hands_s = sfen.split(" ")[:3]
    cells = {}
    for r, row in enumerate(board_s.split("/"), start=1):
        f = 9
        prom = False
        for ch in row:
            if ch == "+":
                prom = True
                continue
            if ch.isdigit():
                f -= int(ch)
                continue
            cells[(f, r)] = ("+" if prom else "") + ch
            prom = False
            f -= 1
    hands = {}
    if hands_s != "-":
        n = ""
        for ch in hands_s:
            if ch.isdigit():
                n += ch
                continue
            hands[ch] = hands.get(ch, 0) + (int(n) if n else 1)
            n = ""
    return cells, turn, hands


def sq(token):
    return (int(token[0]), RANKS.index(token[1]) + 1)


def usi_squares(usi):
    if usi[1] == "*":
        return None, sq(usi[2:4])
    return sq(usi[0:2]), sq(usi[2:4])


def piece_kanji(token):
    letter = token.lstrip("+").lower()
    return (PROM if token.startswith("+") else PIECE)[letter]


def move_kanji(cells, usi, prev_to):
    """指し手の日本語表記(_util.py の disp_move と同じ考え方。生の USI + 局面から直接組み立てる)。
    `check_answer.py` の検査 2 が付録 2・付録 3 の印字と本編の字を同じ文字列として照合する ― 表記のコードは変えない。"""
    if usi[1] == "*":
        to = sq(usi[2:4])
        return f"{ZEN[to[0]]}{KAN[to[1]]}{PIECE[usi[0].lower()]}打"
    frm, to = sq(usi[0:2]), sq(usi[2:4])
    name = piece_kanji(cells[frm])
    head = "同　" if prev_to == to else f"{ZEN[to[0]]}{KAN[to[1]]}"
    return head + name + ("成" if usi.endswith("+") else "")


def mark(turn, user_is_sente):
    """▲ が本人、△ が相手(先手・後手にかかわらず)。"""
    return "▲" if (turn == "b") == user_is_sente else "△"
