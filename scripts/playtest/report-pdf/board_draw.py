# -*- coding: utf-8 -*-
# **盤面図を描く道具(`Board`)と SFEN を読む道具を、1 か所に置く。**
#
# 【なぜ切り出したか】STEP CUSTOMER-EXIT の後半(本編 md → PDF)が、付録 1 と**同じ盤**を出す。
# `_util.py` は `build.sh` で連結される断片(`m`・`_data_dir` が先に要る)なので **import できない。**
# 写すと P-111(`Board` が 4 実装に散っている)を**5 つ目に増やす**ことになるので、**移した。**
#
# 【様式は借りず、引数で受ける】もとの `Board.draw` は `INK`・`RED`・`BG`・`LINE`・`MUTED`・`FONT` を
# **連結の前(`_head.py`)の名前で借りていた**(そのまま切り出すと `NameError: INK` で落ちる ― 実測 2026-09-29)。
# **借りるのをやめ、`BoardStyle` で受ける。**呼ぶ側がそれぞれの様式を渡す
# (付録は `_head.py` の色、本編は `render_answer.py` の色)。
# **借りていないことは `board_draw_test.py` が AST で見る**(`exit_index.py` の型)。
#
# 【範囲】`fig1.py:184`・`render_direct.py:243`・`render_whatif.py:258` の `Board` は**別実装のまま**
# (矢印や打つ手の丸など、付録ごとに違う描き方を持つ)。**P-111 は 4 → 3 に減っただけ**で、残り 3 つは触っていない。
import collections
import math

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Flowable

# 盤を描くのに要る様式。**`_head.py` の名前を借りない**ための受け皿。
BoardStyle = collections.namedtuple("BoardStyle", "ink red bg line muted font")

ZEN = "０１２３４５６７８９"; KAN = "〇一二三四五六七八九"
PIECE = {"p": "歩", "l": "香", "n": "桂", "s": "銀", "g": "金", "b": "角", "r": "飛", "k": "玉"}
PROM = {"p": "と", "l": "杏", "n": "圭", "s": "全", "b": "馬", "r": "竜"}
def parse_sfen(sfen):
    board_s, turn, hands = sfen.split(" ")[:3]
    cells = {}
    for r, row in enumerate(board_s.split("/"), start=1):
        f = 9; prom = False
        for ch in row:
            if ch == "+": prom = True; continue
            if ch.isdigit(): f -= int(ch); continue
            k = ch.lower(); cells[(f, r)] = ((PROM if prom else PIECE)[k], ch.isupper()); prom = False; f -= 1
    hs = {True: [], False: []}
    if hands != "-":
        n = ""
        for ch in hands:
            if ch.isdigit(): n += ch; continue
            hs[ch.isupper()].append(PIECE[ch.lower()] + (KAN[int(n)] if n and int(n) < 10 else (n or ""))); n = ""
    return cells, hs
def usi_squares(usi):
    rk = lambda c: ord(c) - ord("a") + 1
    if usi[1] == "*": return None, (int(usi[2]), rk(usi[3]))
    return (int(usi[0]), rk(usi[1])), (int(usi[2]), rk(usi[3]))
class Board(Flowable):
    """本人側を下にした盤面図。sfen は「その手を指した後」、hl は動かした駒の行き先(と元の升)。"""
    def __init__(self, sfen, user_sente, style, usi=None, size=52 * mm, person="本人", arrows=()):
        super().__init__(); self.st = style; self.arrows = list(arrows); self.cells, self.hands = parse_sfen(sfen); self.us = user_sente; self.usi = usi; self.size = size; self.person = person
    def wrap(self, aw, ah): return self.size + 8 * mm, self.size + 17 * mm
    def draw(self):
        c = self.canv; S = self.size; q = S / 9; ox, oy = 1 * mm, 7.5 * mm
        def xy(f, r):  # 升の左下
            col = (9 - f) if self.us else (f - 1); row = (r - 1) if self.us else (9 - r)
            return ox + col * q, oy + S - (row + 1) * q
        frm, to = usi_squares(self.usi) if self.usi else (None, None)
        c.setFillColor(colors.HexColor("#fdf8ec")); c.rect(ox, oy, S, S, stroke=0, fill=1)
        if frm: x, y = xy(*frm); c.setFillColor(colors.HexColor("#f3e3c0")); c.rect(x, y, q, q, stroke=0, fill=1)
        if to: x, y = xy(*to); c.setFillColor(colors.HexColor("#f2b8b2")); c.rect(x, y, q, q, stroke=0, fill=1)
        c.setStrokeColor(colors.HexColor("#7a6a55")); c.setLineWidth(0.4)
        for i in range(10): c.line(ox + i * q, oy, ox + i * q, oy + S); c.line(ox, oy + i * q, ox + S, oy + i * q)
        c.setLineWidth(1); c.rect(ox, oy, S, S, stroke=1, fill=0)
        fs = q * 0.72
        for (f, r), (name, is_sente) in self.cells.items():
            x, y = xy(f, r); mine = (is_sente == self.us)
            c.saveState(); c.translate(x + q / 2, y + q / 2)
            if not mine: c.rotate(180)
            c.setFillColor(self.st.ink if name not in PROM.values() else self.st.red); c.setFont(self.st.font, fs); c.drawCentredString(0, -fs * 0.36, name); c.restoreState()
        c.setFillColor(self.st.muted); c.setFont(self.st.font, 6)
        for i in range(9):
            f = (9 - i) if self.us else (i + 1); r = (i + 1) if self.us else (9 - i)
            c.drawCentredString(ox + i * q + q / 2, oy + S + 1.2, ZEN[f]); c.drawString(ox + S + 1.5, oy + S - (i + 1) * q + q / 2 - 2, KAN[r])
        for yy, lab, hs in ((oy - 6.2 * mm, f"{self.person}の持ち駒", self.hands[self.us]), (oy + S + 3.4 * mm, "相手の持ち駒", self.hands[not self.us])):
            c.setFillColor(self.st.bg); c.setStrokeColor(self.st.line); c.setLineWidth(0.4); c.rect(ox, yy, S, 4.6 * mm, stroke=1, fill=1)
            c.setFillColor(self.st.muted); c.setFont(self.st.font, 7); c.drawString(ox + 1.2 * mm, yy + 1.35 * mm, lab)
            c.setFillColor(self.st.ink); c.setFont(self.st.font, 9); c.drawRightString(ox + S - 1.2 * mm, yy + 1.2 * mm, " ".join(hs) or "なし")
        # 矢印(実戦の手 = 実線、比べる候補 = 破線)。色は良し悪しを表さない
        def center(sq): x, y = xy(*sq); return x + q / 2, y + q / 2
        def arrow(usi, col, dash, shift):
            import math
            fr, to_ = usi_squares(usi); tx, ty = center(to_)
            c.saveState(); c.setStrokeColor(col); c.setFillColor(col); c.setLineWidth(1.6)
            if dash: c.setDash(3, 2)
            if fr is None:  # 打つ手: 行き先を丸で囲む
                c.circle(tx, ty, q * 0.46, stroke=1, fill=0)
            else:
                fx, fy = center(fr); ang = math.atan2(ty - fy, tx - fx); nx, ny = -math.sin(ang) * shift, math.cos(ang) * shift
                fx, fy, tx, ty = fx + nx, fy + ny, tx + nx, ty + ny
                ex, ey = tx - math.cos(ang) * q * 0.28, ty - math.sin(ang) * q * 0.28
                c.line(fx, fy, ex, ey); c.setDash(); hl = q * 0.34
                pth = c.beginPath(); pth.moveTo(tx, ty)
                pth.lineTo(tx - hl * math.cos(ang - 0.45), ty - hl * math.sin(ang - 0.45)); pth.lineTo(tx - hl * math.cos(ang + 0.45), ty - hl * math.sin(ang + 0.45)); pth.close()
                c.drawPath(pth, stroke=0, fill=1)
            c.restoreState()
        for usi, col, dash, shift in self.arrows: arrow(usi, col, dash, shift)
