# -*- coding: utf-8 -*-
# STEP WHATIF 作業 2(docs/STEP_WHATIF_PLAN_2026-09-22.md §2.3・§7.3)。付録 2(分かれ道)の PDF を作る道具。
#
# 使い方: REPORT_DATA_DIR=<フォルダ> python3 -X utf8 render_whatif.py <whatif_report_data.json> <出力 PDF>
#   REPORT_DATA_DIR には sfens.json(scripts/playtest/lib/reportData.ts の buildSfens の出力)も置く。
#
# 【この新規ファイルが再利用する「流儀」(既存の 6 本(_head/_util/_mid/_app_head/_app/_tail)は変えない)】
# - 書体の探し方・埋め込み・REPORT_DATA_DIR(_head.py と同じ)
# - 盤面の描き方(Board Flowable。_util.py と同じ考え方 ― 本人の側を下にする・実戦の手/候補の矢印)
# - 手の表記(disp_move の考え方。ただしこのファイルの入力(whatif_report_data.json)は USI の生の手なので、
#   TS 側(既存の toJapaneseMove 等)を経由せず、この場で SFEN から直接組み立てる ― 下の「手の組み立て」節)
#
# 【mirrored(本人が後手)の局の手の表記(依頼の指示: 回し方を新しく決めない)】
# whatif.jsonl(→ whatif_report_data.json)の sfen・USI は、測る段(lib/whatif.ts)が「本人 = 先手」にそろえた
# 向き(180 度回した解析用の向き)のまま入っている。**盤面図・実戦の手は、sfens.json(reportData.ts の buildSfens。
# 本人が指した実際の向き)を使う**(付録 1(本編)の report-pdf が後手の局をどう表しているかと同じ ― 実際の SFEN を
# 使うのであって、盤面を回して見せない)。エンジンの候補・読み筋・攻め/守りの手(実戦では指されていない、
# whatif.jsonl にしか無い手)は、mirrored の局だけ `rotate_usi`(lib/usiRotation.ts の rotateUsiMove と同じ変換を
# python で書き直したもの。新しい回し方を作っていない)で本人が指した向きへ戻してから、sfens.json の実際の局面へ
# 適用する(このファイルの `apply_move`)。
import json
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

if len(sys.argv) < 3:
    sys.exit("使い方: REPORT_DATA_DIR=<フォルダ> python3 -X utf8 render_whatif.py <whatif_report_data.json> <出力 PDF>")
src, out = sys.argv[1], sys.argv[2]
m = json.load(open(src, encoding="utf-8"))

# ---- 書体(_head.py と同じ流儀。ヒラギノ系 CID → 無ければ埋め込みフォント) ----
_here = os.path.dirname(os.path.abspath(__file__))
_data_dir = os.environ.get("REPORT_DATA_DIR", _here)
_cands = [os.path.join(_here, "fonts", "IPAexfont00401", "ipaexg.ttf"), "/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"]
_font = next((p for p in _cands if os.path.exists(p)), None)
if _font is None:
    sys.exit("埋め込める日本語フォントが無い(埋め込まない PDF は読む側で文字が欠けるので作らない)")
pdfmetrics.registerFont(TTFont("JPEmbedded", _font))
FONT = FONT_B = "JPEmbedded"

SF = json.load(open(os.path.join(_data_dir, "sfens.json"), encoding="utf-8"))

INK = colors.HexColor("#1e2a32")
MUTED = colors.HexColor("#5a6a74")
ACCENT = colors.HexColor("#2d6a8a")
RED = colors.HexColor("#c9473f")
LINE = colors.HexColor("#d5dde2")
BG = colors.HexColor("#f4f7f9")
COL_PLAYED = colors.HexColor("#8a5a1e")
COL_CAND = colors.HexColor("#1f7a78")

st = lambda name, **kw: ParagraphStyle(name, fontName=kw.pop("font", FONT), textColor=kw.pop("color", INK), leading=kw.pop("leading", 15), wordWrap="CJK", alignment=TA_LEFT, **kw)
NB = " "


def P(text, style):
    # 半角空白を改行しない空白にして、数字の前後で折れないようにする(_head.py の P と同じ考え方)
    parts = re.split(r"(<[^>]*>)", text)
    return Paragraph("".join(pt if pt.startswith("<") else pt.replace(" ", NB) for pt in parts), style)


S_TITLE = st("wtitle", font=FONT_B, fontSize=18, leading=23, spaceAfter=2 * mm)
S_LEAD = st("wlead", fontSize=10.2, leading=15, color=MUTED, spaceAfter=3 * mm)
S_H2 = st("wh2", font=FONT_B, fontSize=12.5, leading=17, color=ACCENT, spaceBefore=4 * mm, spaceAfter=1.5 * mm)
S_H3 = st("wh3", font=FONT_B, fontSize=11, leading=14, color=ACCENT, spaceBefore=3 * mm, spaceAfter=1.2 * mm)
S_BODY = st("wbody", fontSize=10, leading=14.5)
S_SMALL = st("wsmall", fontSize=8.6, leading=12, color=MUTED)
S_K = st("wk", fontSize=9.5, leading=13, color=MUTED)
S_V = st("wv", fontSize=9.8, leading=13.5)
S_CARDH = st("wcardh", font=FONT_B, fontSize=10.2, leading=13.5)
S_EYEBROW = st("weyebrow", fontSize=8.2, leading=11, color=ACCENT)
S_LABEL = st("wlabel", font=FONT_B, fontSize=8.4, leading=11, color=INK)

BANNED = ["悪手", "弱点", "癖", "傾向", "原因", "ミス", "見落とし", "改善", "練習", "必ず", "明らか", "あなた", "ご自身", "いつも", "がち"]

doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title="対局後診断・付録 2(分かれ道)", author="将棋コーチ(試作)")
W = A4[0] - 28 * mm
story = []

# ==================== SFEN の機構(このファイルで新しく書く。既存の 6 本は変えない) ====================
# _util.py の parse_sfen・usi_squares と同じマスの数え方(筋 1〜9・段 a〜i)を使う。ここは盤面を「進める」ために
# 駒の移動・持ち駒の増減・成りまで機械的に反映する(将棋の判断はしない。合法性の確認はしない ―
# 入力(候補・読み筋)はすでに測る段(whatif.ts)でエンジンが読んだ手であり、ここでは動かすだけ)。
ZEN = "０１２３４５６７８９"
KAN = "〇一二三四五六七八九"
PIECE = {"p": "歩", "l": "香", "n": "桂", "s": "銀", "g": "金", "b": "角", "r": "飛", "k": "玉"}
PROM = {"p": "と", "l": "杏", "n": "圭", "s": "全", "b": "馬", "r": "竜"}
RANKS = "abcdefghi"


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


def rotate_square(token):
    """lib/usiRotation.ts の rotateSquare と同じマスの変換(筋 f→10−f、段は abcdefghi を逆順)。新しい回し方は作らない。"""
    f, r = int(token[0]), token[1]
    return f"{10 - f}{RANKS[len(RANKS) - 1 - RANKS.index(r)]}"


def rotate_usi(usi):
    """lib/usiRotation.ts の rotateUsiMove と同じ変換(python で書き直したもの)。mirrored の局の、
    実戦では指されていない手(候補・読み筋・攻め/守りの手)を、本人が指した向きへ戻すために使う。"""
    if usi[1] == "*":
        return f"{usi[0]}*{rotate_square(usi[2:4])}"
    suffix = usi[4:]
    return rotate_square(usi[0:2]) + rotate_square(usi[2:4]) + suffix


def apply_move(cells, turn, hands, usi):
    """1 手ぶん盤を進める(合法性は確認しない。呼び出し元(測る段のエンジン)がすでに読んだ手だけを渡す)。"""
    new_cells = dict(cells)
    new_hands = dict(hands)
    if usi[1] == "*":
        to = sq(usi[2:4])
        letter = usi[0] if turn == "b" else usi[0].lower()
        new_cells[to] = letter
        key = usi[0] if turn == "b" else usi[0].lower()
        new_hands[key] = new_hands.get(key, 0) - 1
        if new_hands[key] <= 0:
            del new_hands[key]
    else:
        frm, to = sq(usi[0:2]), sq(usi[2:4])
        token = new_cells.pop(frm)
        if to in new_cells:
            captured_letter = new_cells[to].lstrip("+").upper()
            captured_key = captured_letter if turn == "b" else captured_letter.lower()
            new_hands[captured_key] = new_hands.get(captured_key, 0) + 1
        if usi.endswith("+"):
            token = "+" + token.lstrip("+")
        new_cells[to] = token
    new_turn = "w" if turn == "b" else "b"
    return new_cells, new_turn, new_hands


def serialize_sfen(cells, turn, hands):
    rows = []
    for r in range(1, 10):
        row = ""
        empty = 0
        for f in range(9, 0, -1):
            c = cells.get((f, r))
            if c is None:
                empty += 1
                continue
            if empty:
                row += str(empty)
                empty = 0
            row += c
        if empty:
            row += str(empty)
        rows.append(row)
    board_s = "/".join(rows)
    if not hands:
        hands_s = "-"
    else:
        order = "RBGSNLPrbgsnlp"
        parts = []
        for k in order:
            n = hands.get(k, 0)
            if n > 0:
                parts.append((str(n) if n > 1 else "") + k)
        hands_s = "".join(parts)
    return f"{board_s} {turn} {hands_s} 1"


def piece_kanji(token):
    letter = token.lstrip("+").lower()
    return (PROM if token.startswith("+") else PIECE)[letter]


def move_kanji(cells, usi, prev_to):
    """指し手の日本語表記(_util.py の disp_move と同じ考え方。ここでは生の USI + 局面から直接組み立てる)。"""
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


def line_of(cells, turn, hands, pv, user_is_sente, k=5):
    """読み筋(最大 k 手)を、表示用の文字列と、その先の局面(dict の cells/turn/hands)にする。"""
    texts = []
    prev_to = None
    cur_cells, cur_turn, cur_hands = cells, turn, hands
    last_usi = None
    applied = 0
    for usi in pv[:k]:
        texts.append(mark(cur_turn, user_is_sente) + move_kanji(cur_cells, usi, prev_to))
        prev_to = usi_squares(usi)[1]
        cur_cells, cur_turn, cur_hands = apply_move(cur_cells, cur_turn, cur_hands, usi)
        last_usi = usi
        applied += 1
    return " ".join(texts), (cur_cells, cur_turn, cur_hands), last_usi, applied


def sc(candidate):
    if candidate.get("mate") is not None:
        return "本人の側に詰みあり" if candidate["mate"] > 0 else "本人の玉に詰みあり"
    cp = candidate.get("scoreCp")
    if cp is None:
        return "—"
    return f"{cp:+d}".replace("-", "−")


# ==================== 盤面図(_util.py の Board Flowable と同じ考え方) ====================
class Board(Flowable):
    """本人側を下にした盤面図。`sfen` は表示したい局面そのもの(その手を指した後)。`hl` は動かした駒の行き先(と元の升)。"""

    def __init__(self, sfen, user_sente, usi=None, size=48 * mm, person="本人", arrows=()):
        super().__init__()
        self.arrows = list(arrows)
        self.cells, self.turn, self.hands = parse_sfen(sfen)
        self.us = user_sente
        self.usi = usi
        self.size = size
        self.person = person

    def wrap(self, aw, ah):
        return self.size + 8 * mm, self.size + 17 * mm

    def draw(self):
        c = self.canv
        S = self.size
        q = S / 9
        ox, oy = 1 * mm, 7.5 * mm

        def xy(f, r):
            col = (9 - f) if self.us else (f - 1)
            row = (r - 1) if self.us else (9 - r)
            return ox + col * q, oy + S - (row + 1) * q

        frm, to = usi_squares(self.usi) if self.usi else (None, None)
        c.setFillColor(colors.HexColor("#fdf8ec"))
        c.rect(ox, oy, S, S, stroke=0, fill=1)
        if frm:
            x, y = xy(*frm)
            c.setFillColor(colors.HexColor("#f3e3c0"))
            c.rect(x, y, q, q, stroke=0, fill=1)
        if to:
            x, y = xy(*to)
            c.setFillColor(colors.HexColor("#f2b8b2"))
            c.rect(x, y, q, q, stroke=0, fill=1)
        c.setStrokeColor(colors.HexColor("#7a6a55"))
        c.setLineWidth(0.4)
        for i in range(10):
            c.line(ox + i * q, oy, ox + i * q, oy + S)
            c.line(ox, oy + i * q, ox + S, oy + i * q)
        c.setLineWidth(1)
        c.rect(ox, oy, S, S, stroke=1, fill=0)
        fs = q * 0.72
        for (f, r), token in self.cells.items():
            is_sente = token[-1].isupper()
            x, y = xy(f, r)
            mine = is_sente == self.us
            c.saveState()
            c.translate(x + q / 2, y + q / 2)
            if not mine:
                c.rotate(180)
            name = piece_kanji(token)
            c.setFillColor(INK if not token.startswith("+") else RED)
            c.setFont(FONT, fs)
            c.drawCentredString(0, -fs * 0.36, name)
            c.restoreState()
        c.setFillColor(MUTED)
        c.setFont(FONT, 6)
        for i in range(9):
            f = (9 - i) if self.us else (i + 1)
            r = (i + 1) if self.us else (9 - i)
            c.drawCentredString(ox + i * q + q / 2, oy + S + 1.2, ZEN[f])
            c.drawString(ox + S + 1.5, oy + S - (i + 1) * q + q / 2 - 2, KAN[r])

        def hand_text(is_sente_side):
            items = []
            for letter in "RBGSNLP":
                key = letter if is_sente_side else letter.lower()
                n = self.hands.get(key, 0)
                if n > 0:
                    items.append(PIECE[letter.lower()] + (KAN[n] if n < 10 else str(n)))
            return "　".join(items) or "なし"

        for yy, lab, is_sente_side in ((oy - 6.2 * mm, f"{self.person}の持ち駒", self.us), (oy + S + 3.4 * mm, "相手の持ち駒", not self.us)):
            c.setFillColor(BG)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.4)
            c.rect(ox, yy, S, 4.6 * mm, stroke=1, fill=1)
            c.setFillColor(MUTED)
            c.setFont(FONT, 7)
            c.drawString(ox + 1.2 * mm, yy + 1.35 * mm, lab)
            c.setFillColor(INK)
            c.setFont(FONT, 9)
            c.drawRightString(ox + S - 1.2 * mm, yy + 1.2 * mm, hand_text(is_sente_side))


# ==================== 形勢のグラフ(小さく。実戦の折れ線と、その局面の赤い縦線 1 本と「● n 手目」だけ) ====================
class WhatifGraph(Flowable):
    def __init__(self, scores, plies, mark_ply, w=118 * mm, h=20 * mm):
        super().__init__()
        self.scores = scores
        self.plies = plies
        self.mark_ply = mark_ply
        self.w = w
        self.h = h

    def wrap(self, aw, ah):
        return self.w, self.h + 3 * mm

    def draw(self):
        c = self.canv
        w, h, pad = self.w, self.h, 3
        points = [(p, v) for p, v in zip(self.plies, self.scores) if v is not None]
        c.setFillColor(BG)
        c.setStrokeColor(LINE)
        c.rect(0, 0, w, h, stroke=1, fill=1)
        if len(points) < 2:
            return
        xmax = max(max(p for p, _ in points), self.mark_ply)
        clamp = lambda v: max(-2500, min(2500, v))
        x = lambda p: pad + p / xmax * (w - 2 * pad)
        y = lambda v: h / 2 + (clamp(v) / 2500) * (h / 2 - pad)
        c.setStrokeColor(colors.HexColor("#b8c4cb"))
        c.setDash(1.5, 1.5)
        c.line(pad, h / 2, w - pad, h / 2)
        c.setDash()
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1)
        prev = None
        for p, v in points:
            if prev is not None:
                c.line(x(prev[0]), y(prev[1]), x(p), y(v))
            prev = (p, v)
        c.setStrokeColor(RED)
        c.setLineWidth(0.8)
        c.line(x(self.mark_ply), 0, x(self.mark_ply), h)
        c.setFillColor(RED)
        c.setFont(FONT, 7)
        c.drawString(min(x(self.mark_ply) + 1.5, w - 22 * mm), h - 6, f"● {self.mark_ply} 手目")
        c.setFillColor(MUTED)
        c.setFont(FONT, 5.5)
        c.drawString(pad + 1, h - 7, "+2500")
        c.drawString(pad + 1, 2, "−2500")


# ==================== レイアウトの小道具(_head.py の boxes/kv/notebox/boxflow と同じ考え方) ====================
def notebox(lines):
    t = Table([[P("・" + n, S_SMALL)] for n in lines], colWidths=[W])
    t.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("BACKGROUND", (0, 0), (-1, -1), BG),
                ("LEFTPADDING", (0, 0), (-1, -1), 3.5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3.5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 1.2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2 * mm),
            ]
        )
    )
    return t


def boxflow(items, bgc=BG, bar=ACCENT):
    t = Table([[items]], colWidths=[W])
    t.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LINEBEFORE", (0, 0), (0, -1), 2.2, bar),
                ("BACKGROUND", (0, 0), (-1, -1), bgc),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
            ]
        )
    )
    return t


S_FLOWNUM = st("wflownum", font=FONT_B, fontSize=13, leading=16, color=ACCENT)
LABEL_STYLE = ParagraphStyle("wlabelbox", fontName=FONT, fontSize=8, leading=10, textColor=colors.white, backColor=ACCENT, alignment=TA_LEFT)


def caption_label(text):
    """依頼の追加 2 点の (1): 盤面の上に置く、背景色つきの短いラベル。"""
    t = Table([[P(text, LABEL_STYLE)]])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
                ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 1 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1 * mm),
            ]
        )
    )
    return t


# ==================== 数の照合(この段は LLM を使わないが、文に出す数がデータに無ければ止める) ====================
# 「用語」として文に出す、方式そのものの数(第 1 候補・第 2 候補・上位 3 つ・上位 5 つ・読み筋 5 手)は、
# 個々の局面の事実ではなく、この付録の作り方そのもの(計画・レイアウトの決め方)を表す数として、常に許可する。
GLOBAL_ALLOWED_NUMBERS = {1, 2, 3, 5}
_problems = []


def emit(text, allowed):
    """文に出てくる数字を、その場面で使ってよい数の集合と照合する(_mid.py の allowed_numbers と同じ考え方)。
    将棋の升目の表記(全角数字 + 漢数字。例: ９四)は「数」として扱わない(ASCII の 0〜9 の並びだけを見る)。"""
    plain = re.sub(r"<[^>]*>", "", text)
    plain = re.sub(r"[０-９][〇一二三四五六七八九]", "", plain)  # 升目(例: ９四)を先に取り除く
    allowed_all = allowed | GLOBAL_ALLOWED_NUMBERS
    for token in re.findall(r"[0-9]+", plain):
        n = int(token)
        if n not in allowed_all:
            _problems.append(f"データに無い数 {n} が文に出ている: {text[:60]}…")
    for w in BANNED:
        if w in text:
            _problems.append(f"使わない語「{w}」: {text[:60]}…")
    return text


# ==================== 1 ページ目(§7.3 の集計) ====================
s = m["summary"]
games = m["games"]
pos_read = s["positionsRead"]
matches_top1 = s["matchesTop1"]
within_top5 = s["withinMultiPv"]
sc_ = s["scenes"]
side = s["sideCompare"]
lwn = s["lossesWithNarrowHeld"]
values = m["values"]
radius = values["sideZoneRadius"]
start_ply = values["startPly"]
narrow_gap_cp = values["narrowGapCp"]


def pct(a, b):
    return f"{round(100 * a / b)}%" if b else "—"


allowed_p1 = {
    m["gamesCount"],
    pos_read,
    matches_top1,
    within_top5,
    sc_["fork"],
    sc_["narrowHeld"],
    sc_["chanceHeld"],
    sc_["rawTotal"],
    sc_["distinctTotal"],
    side["bothFound"],
    side["scenesRead"],
    side["attackNoLegalMove"],
    side["defenseNoLegalMove"],
    lwn["withNarrow"],
    lwn["lossesTotal"],
    radius,
    start_ply,
    narrow_gap_cp,
}
for a, b in [(matches_top1, pos_read), (within_top5, pos_read), (side["bothFound"], side["scenesRead"])]:
    if b:
        allowed_p1.add(round(100 * a / b))

story.append(P("対局後診断・付録 2(試作)", S_EYEBROW))
story.append(P(f"{m['gamesCount']} 局を調べて、どんな局面が見つかったか", S_TITLE))
story.append(
    P(
        emit(
            f"今回の {m['gamesCount']} 局について、{start_ply} 手目より後の本人の手番 <b>{pos_read} 局面</b>を分析しました。それぞれの局面で、"
            f"実戦の手とエンジンの候補(上位 5 つ)を比べ、特徴のある局面を機械的に拾っています。負けた場面だけを探しているわけではありません。",
            allowed_p1,
        ),
        S_LEAD,
    )
)

flow_row = Table(
    [
        [
            P(emit(f"<b>{m['gamesCount']} 局</b>", allowed_p1), S_FLOWNUM),
            P("→", S_BODY),
            P(emit(f"<b>{pos_read} 局面</b><br/>を分析", allowed_p1), S_K),
            P("→", S_BODY),
            P("実戦の手と<br/>候補を比べる", S_K),
            P("→", S_BODY),
            [
                P(emit(f"<b>{sc_['fork']}</b> 実戦の手で評価が下がった分かれ道", allowed_p1), S_SMALL),
                P(
                    emit(f"<b>{sc_['narrowHeld']}</b> 選択肢が限られた局面(第 1 候補と第 2 候補の差が {narrow_gap_cp} 以上)で、第 1 候補と同じ手", allowed_p1),
                    S_SMALL,
                ),
                P(emit(f"<b>{sc_['chanceHeld']}</b> 相手の手の後に生まれた機会で、第 1 候補と同じ手", allowed_p1), S_SMALL),
            ],
        ]
    ],
    colWidths=[20 * mm, 6 * mm, 24 * mm, 6 * mm, 26 * mm, 6 * mm, W - 88 * mm],
)
flow_row.setStyle(
    TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (0, 0), BG),
            ("BACKGROUND", (2, 0), (2, 0), BG),
            ("BACKGROUND", (4, 0), (4, 0), BG),
            ("BACKGROUND", (6, 0), (6, 0), BG),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("ALIGN", (3, 0), (3, 0), "CENTER"),
            ("ALIGN", (5, 0), (5, 0), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ]
    )
)
story.append(flow_row)
story.append(
    P(
        emit(f"3 つの項目は重なることがあります(1 つの局面が 2 つの項目に入る)。重なりを除いた局面の数は {sc_['distinctTotal']} です。", allowed_p1),
        S_SMALL,
    )
)
story.append(Spacer(1, 2.5 * mm))

two_col = Table(
    [
        [
            [
                P("実戦の手とエンジンの候補", S_H3),
                Table(
                    [
                        [P("第 1 候補と同じ手", S_K), P(emit(f"{matches_top1} / {pos_read} 局面({pct(matches_top1, pos_read)})", allowed_p1), S_V)],
                        [P("上位 5 つの候補に入っていた手", S_K), P(emit(f"{within_top5} / {pos_read} 局面({pct(within_top5, pos_read)})", allowed_p1), S_V)],
                    ],
                    colWidths=[52 * mm, (W / 2) - 10 * mm - 52 * mm],
                    style=TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("TOPPADDING", (0, 0), (-1, -1), 1 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 1 * mm)]),
                ),
                P(
                    "この数は、エンジンの読み(100 万局面)の中での一致で、棋力や手の良し悪しを表す数ではありません。次の対局と並べて、変化を見るための数です。",
                    S_SMALL,
                ),
            ],
            [
                P("攻める手と守る手を比べられた局面", S_H3),
                Table(
                    [
                        [P("両方の手が見つかった", S_K), P(emit(f"{side['bothFound']} / {side['scenesRead']} 局面({pct(side['bothFound'], side['scenesRead'])})", allowed_p1), S_V)],
                        [P("攻めの側の手が 1 つも無かった", S_K), P(emit(f"{side['attackNoLegalMove']} 局面", allowed_p1), S_V)],
                    ],
                    colWidths=[52 * mm, (W / 2) - 10 * mm - 52 * mm],
                    style=TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("TOPPADDING", (0, 0), (-1, -1), 1 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 1 * mm)]),
                ),
                P(
                    emit(
                        f"「攻めの側」は、王手になる手か、行き先が相手の玉から {radius} マス以内の手。「守りの側」は、行き先が自分の玉から {radius} マス以内の手か、"
                        f"玉を動かす手です(行き先だけで機械的に分けています。決め方 v1: 玉から {radius} マス以内)。攻めの側の手が無い局面は、まだ相手の玉に手が届かない局面です。",
                        allowed_p1,
                    ),
                    S_SMALL,
                ),
            ],
        ]
    ],
    colWidths=[W / 2, W / 2],
)
two_col.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 6 * mm)]))
story.append(two_col)
story.append(Spacer(1, 2 * mm))

story.append(P("この付録の読み方", S_K))
story.append(
    notebox(
        [
            emit(
                f"各対局を代表する局面を 1 つずつ取り上げています。負けた対局は「実戦の手と第 1 候補の評価の差が、いちばん大きかった局面」、"
                f"勝った対局は「選択肢が限られた局面で、第 1 候補と同じ手を指した場面」(無ければ他の種類の場面)です。負けた {lwn['lossesTotal']} 局のうち "
                f"{lwn['withNarrow']} 局にも、選択肢が限られた中で第 1 候補と同じ手を指した場面がありました。",
                allowed_p1,
            ),
            "エンジンの評価は、お互いが最善を指し続けた場合の見込みです。自分の手で上がることはなく、上がった所は相手の手の後です。",
            "エンジンの候補は「正解」ではなく、比べるための材料です。読み筋は、エンジンが双方の手を読んだ一例で、実際の相手がそう指すとは限りません。",
            "手の表記は、先手・後手にかかわらず ▲ が本人、△ が相手の手です。盤面図は本人の側を下にしています。",
        ]
    )
)
story.append(PageBreak())

# ==================== 2 ページ目以降(1 局 1 場面) ====================
KIND_HEAD = {
    "fork": "いちばん大きな分かれ道",
    "narrowHeld": "選べる手が限られていた局面で、第 1 候補と同じ手",
    "chanceHeld": "相手の手で評価が上がった直後に、第 1 候補と同じ手",
}
KIND_LEAD = {
    "fork": "この対局で、実戦の手とエンジンの第 1 候補の評価の差が、いちばん大きかった局面です。",
    "narrowHeld": f"選択肢が限られた局面(第 1 候補と第 2 候補の差が {narrow_gap_cp} 以上)で、実戦の手が第 1 候補と同じでした。",
    "chanceHeld": "相手の手の後に生まれた機会で、実戦の手が第 1 候補と同じでした。",
}

CAND_HEADER_STYLE = TableStyle(
    [
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
        ("BACKGROUND", (0, 0), (-1, 0), BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1 * mm),
    ]
)

no_representative_games = []

for g in games:
    rep = g["representative"]
    if rep is None:
        no_representative_games.append(g)
        continue
    gid = g["id"]
    k = SF.get(gid)
    if k is None:
        _problems.append(f"{gid}: sfens.json にこの局が無い(付録 2 の材料と局が食い違っている)")
        continue

    dply = rep["displayPly"]
    mir = g["plyOffset"] == 1
    user_is_sente = g["side"] == "先手"

    def to_genuine(usi, _mir=mir):
        # mirrored(本人が後手)の局だけ、実戦では指されていない手を本人が指した向きへ戻す(回し方は lib/usiRotation.ts と同じ)
        return rotate_usi(usi) if _mir else usi

    before_sfen = k["sfens"][dply - 1]
    genuine_actual_usi = k["moves"][dply - 1]
    cells0, turn0, hands0 = parse_sfen(before_sfen)

    allowed_g = {g["gameNo"], dply, g["total"], radius, narrow_gap_cp, g["positionsRead"], g["matchesTop1"]}
    for p, v in zip(g["plies"], g["scores"]):
        if v is not None:
            allowed_g.add(p + g["plyOffset"])
            allowed_g.add(abs(v))
    if rep["actualRank"] is not None:
        allowed_g.add(rep["actualRank"])
    if rep["topGapCp"] is not None:
        allowed_g.add(abs(rep["topGapCp"]))
    if rep["actual"]["scoreCp"] is not None:
        allowed_g.add(abs(rep["actual"]["scoreCp"]))
    for c in rep["candidates"]:
        if c["scoreCp"] is not None:
            allowed_g.add(abs(c["scoreCp"]))
    if rep["scene"] is not None:
        for side_key in ("attack", "defense"):
            sd = rep["scene"][side_key]
            if sd.get("scoreCp") is not None:
                allowed_g.add(abs(sd["scoreCp"]))
        if rep["scene"]["sideGapCp"] is not None:
            allowed_g.add(abs(rep["scene"]["sideGapCp"]))
    if rep["afterCandidate"] is not None and rep["afterCandidate"]["scoreCp"] is not None:
        allowed_g.add(abs(rep["afterCandidate"]["scoreCp"]))

    eyebrow = f"{g['gameNo']} 局目 ・ {g['side']} ・ {g['total']} 手 ・ {g['result']}" + (f"({g['ending']})" if g.get("ending") else "")
    story.append(P(emit(eyebrow, allowed_g), S_EYEBROW))
    story.append(P(emit(f"{dply} 手目 ― {KIND_HEAD[rep['kind']]}", allowed_g), S_H2))
    story.append(P(emit(KIND_LEAD[rep["kind"]], allowed_g), S_BODY))
    story.append(Spacer(1, 1.5 * mm))
    story.append(WhatifGraph(g["scores"], [p + g["plyOffset"] for p in g["plies"]], dply))
    story.append(Spacer(1, 3 * mm))

    # ---- 実戦の局面(指す前) ----
    played_text = mark(turn0, user_is_sente) + move_kanji(cells0, genuine_actual_usi, None)
    board_before = Board(before_sfen, user_is_sente, usi=genuine_actual_usi, person="本人", size=44 * mm)
    tx = [P("実戦の手", S_K), P(emit(f"<b>{played_text}</b>(盤の色つきのマス)", allowed_g), S_BODY)]
    if rep["actual"]["found"]:
        tx.append(P(emit(f"エンジンの読みでは、この手の後の評価は <b>{sc(rep['actual'])}</b>。", allowed_g), S_BODY))
    else:
        tx.append(P("エンジンの上位 5 つの候補には入っていませんでした。", S_BODY))
    if rep["actualRank"] is not None:
        tx.append(P(emit(f"上位 5 つの中の {rep['actualRank']} 番目でした。", allowed_g), S_BODY))
    row1 = Table(
        [[caption_label("実戦の局面(指す前)"), ""], [board_before, tx]],
        colWidths=[62 * mm, W - 62 * mm],
    )
    row1.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (1, 0)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 1), (-1, 1), 1.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 1.5 * mm),
            ]
        )
    )
    story.append(KeepTogether([row1]))
    story.append(Spacer(1, 3 * mm))

    # ---- 候補(上位 3 つ)と読み筋 ----
    story.append(P("エンジンの候補(上位 3 つ)と、その先の読み筋", S_H3))
    cand_rows = [[P(x, S_K) for x in ["", "手", "評価", "読み筋(5 手)"]]]
    for i, c in enumerate(rep["candidates"], start=1):
        gm = to_genuine(c["move"])
        nm = mark(turn0, user_is_sente) + move_kanji(cells0, gm, None)
        pv_genuine = [to_genuine(u) for u in c["pv"]]
        pv_text, _, _, _ = line_of(cells0, turn0, hands0, pv_genuine, user_is_sente, 5)
        same = "<font size='7.5' color='#2d6a8a'>(実戦と同じ)</font>" if gm == genuine_actual_usi else ""
        cand_rows.append(
            [P(str(i), S_V), P(emit(nm, allowed_g) + same, S_V), P(emit(sc(c), allowed_g), S_V), P(emit(pv_text, allowed_g), S_SMALL)]
        )
    cand_table = Table(cand_rows, colWidths=[7 * mm, 30 * mm, 18 * mm, W - 55 * mm], repeatRows=1)
    cand_table.setStyle(CAND_HEADER_STYLE)
    story.append(cand_table)

    # ---- 攻めの側・守りの側 ----
    if rep["scene"] is not None:
        story.append(P("この局面で、攻めの側・守りの側それぞれで、いちばん評価を保てた手", S_H3))
        scene_rows = [[P(x, S_K) for x in ["", "手", "評価", "読み筋(5 手)"]]]
        for label, sd in (("攻めの側", rep["scene"]["attack"]), ("守りの側", rep["scene"]["defense"])):
            if sd["state"] != "found":
                text = "その側の手はありませんでした" if sd["state"] == "noLegalMove" else "測れませんでした"
                scene_rows.append([P(label, S_K), P(text, S_SMALL), P("", S_V), P("", S_V)])
            else:
                gm = to_genuine(sd["move"])
                nm = mark(turn0, user_is_sente) + move_kanji(cells0, gm, None)
                pv_genuine = [to_genuine(u) for u in sd["pv"]]
                pv_text, _, _, _ = line_of(cells0, turn0, hands0, pv_genuine, user_is_sente, 5)
                same = "<font size='7.5' color='#2d6a8a'>(実戦と同じ)</font>" if gm == genuine_actual_usi else ""
                scene_rows.append(
                    [P(label, S_K), P(emit(nm, allowed_g) + same, S_V), P(emit(sc(sd), allowed_g), S_V), P(emit(pv_text, allowed_g), S_SMALL)]
                )
        scene_table = Table(scene_rows, colWidths=[16 * mm, 28 * mm, 18 * mm, W - 62 * mm], repeatRows=1)
        scene_table.setStyle(CAND_HEADER_STYLE)
        story.append(scene_table)
        if rep["scene"]["sideGapCp"] is not None:
            gap_text = f"攻めの側と守りの側の差: {rep['scene']['sideGapCp']:+d} ポイント(正なら攻めの側が高い)".replace("+-", "−")
            story.append(P(emit(gap_text, allowed_g), S_SMALL))

    # ---- 第 1 候補(実戦が第 1 候補なら第 2 候補)で 5 手進めた局面 ----
    ac = rep["afterCandidate"]
    if ac is not None:
        cand = rep["candidates"][ac["candidateIndex"]]
        pv_genuine = [to_genuine(u) for u in cand["pv"]]
        pv_text, (cells_a, turn_a, hands_a), last_usi, applied = line_of(cells0, turn0, hands0, pv_genuine, user_is_sente, 5)
        if applied > 0:
            after_sfen = serialize_sfen(cells_a, turn_a, hands_a)
            board_after = Board(after_sfen, user_is_sente, usi=last_usi, person="本人", size=44 * mm)
            which = "第 1 候補" if ac["candidateIndex"] == 0 else "第 2 候補"
            tx2 = [
                P(f"{which}を指していたら(エンジンの読み筋どおりに 5 手進めた局面)", S_K),
                P(emit(pv_text, allowed_g), S_BODY),
                P(
                    emit(
                        f"エンジンの読みでは、この進行の評価は <b>{sc(cand)}</b> でした。相手がこのとおりに指すとは限りません。",
                        allowed_g,
                    ),
                    S_BODY,
                ),
            ]
            row2 = Table(
                [[caption_label("エンジンの読み筋で 5 手進めた局面(実戦ではありません)"), ""], [board_after, tx2]],
                colWidths=[62 * mm, W - 62 * mm],
            )
            row2.setStyle(
                TableStyle(
                    [
                        ("SPAN", (0, 0), (1, 0)),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 1), (-1, 1), 1.5 * mm),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 1.5 * mm),
                    ]
                )
            )
            story.append(Spacer(1, 3 * mm))
            story.append(KeepTogether([row2]))

    story.append(Spacer(1, 3 * mm))
    story.append(
        P(
            emit(f"この対局で読んだ本人の手 {g['positionsRead']} のうち、第 1 候補と同じ手は {g['matchesTop1']}。", allowed_g),
            S_SMALL,
        )
    )
    story.append(PageBreak())

# ==================== 「載せる局面なし」の局(表にだけ出す。ページは作らない) ====================
if no_representative_games:
    story.append(P("代表の場面が無かった局", S_H2))
    story.append(P("分かれ道・選択肢が限られた局面・相手の手の後の機会のどれも見つからなかった局です。ページは作らず、この表にだけ出します。", S_LEAD))
    rows = [[P(x, S_K) for x in ["局", "先後", "結果", "手数", "終局"]]]
    allowed_tail = set()
    for g in no_representative_games:
        allowed_tail.add(g["gameNo"])
        allowed_tail.add(g["total"])
        rows.append([P(emit(str(g["gameNo"]), allowed_tail), S_V), P(g["side"], S_V), P(g["result"], S_V), P(emit(str(g["total"]), allowed_tail), S_V), P(g.get("ending") or "—", S_V)])
    tail_table = Table(rows, colWidths=[16 * mm, 18 * mm, 18 * mm, 18 * mm, W - 70 * mm], repeatRows=1)
    tail_table.setStyle(CAND_HEADER_STYLE)
    story.append(tail_table)
    story.append(Spacer(1, 4 * mm))

story.append(P("試作版につき、有段者による確認はまだ受けていません。エンジンの読みは 1 局面あたり 100 万ノードです。", st("wfoot", fontSize=8, leading=11, color=MUTED)))

if _problems:
    print("\n".join(_problems), file=sys.stderr)
    sys.exit(1)

doc.build(story)
print(f"wrote {out}({len(games)} 局・付録ページ {len(games) - len(no_representative_games)})")
