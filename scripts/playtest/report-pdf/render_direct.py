# -*- coding: utf-8 -*-
# STEP ANSWER 追加作業 ANSWER-DIRECT(docs/STEP_ANSWER_PLAN_2026-09-23.md §9.2・§9.1)。
# 付録 3「直接の答え」の PDF を作る道具。CLAUDE.md ルール 5 の拡張 (4)(2026-09-23 の人間の決定)
# ― エンジンで答え合わせした指し手を局面つきで示す ― の実物。
#
# 使い方:
#   REPORT_DATA_DIR=<sfens.json のあるフォルダ>[,<フォルダ>…] \
#     python3 -X utf8 render_direct.py <direct_answers.json> <final_positions.json> <出力 PDF>
#
# REPORT_DATA_DIR はカンマ区切りで複数渡せる(direct_answers.json・final_positions.json は
# scripts/playtest/directAnswers.ts・finalPositions.ts の --whatif-v2-dir/--read-dir・--patient の
# 組をまたいで作れるため、対応する sfens.json も複数の組にまたがることがある ― 実装担当の判断)。
# 同じ kifuId が複数の sfens.json に出た場合は、最初に読んだものを使う(通常は組ごとに kifuId が
# 重ならないため起こらない)。
#
# 【この新規ファイルが再利用する「流儀」(既存の 6 本(_head/_util/_mid/_app_head/_app/_tail)は変えない)】
# - 書体の探し方・埋め込み・REPORT_DATA_DIR(_head.py と同じ)
# - SFEN を進める・盤面の描き方・手の表記(disp_move の考え方)・数の照合(emit)・禁止語(BANNED)は
#   report-pdf/render_whatif.py と**同じコード**をこのファイルの中に持つ(render_whatif.py も import せず
#   同じ考え方をコードとして持つ書き方をしている ― この README・render_whatif.py 冒頭コメントと同じ流儀)
#
# 【mirrored(本人が後手)の局の手の表記】direct_answers.json の sfen・USI(whatif-v2 の記録)は「本人 = 先手」
# にそろえた向き(測る段の解析用の向き)のまま入っている。final_positions.json の sfen も、固定棋譜の
# moves をそのまま進めた向き(同じそろえ)。**盤面図は sfens.json(本人が指した実際の向き)を使い、
# 候補・実戦の手は mirrored の局だけ rotate_usi で本人が指した向きへ戻してから当てる**(render_whatif.py と
# 同じ考え方)。mirrored かどうかは sfens.json の `side`("gote" なら mirrored。
# lib/reportData.ts の sideOf と同じ対応 ― 二重に判定ロジックを作らない)。
#
# 【第 1 候補の性質・side の出どころ(§9.1 の「(READ の印: 取る/打つ/王手/捨て駒/引く、と whatif-v2 の側)」)】
# direct_answers.json の `top1Tags`・`actualTags` は read.ts の印(capture/drop/givesCheck/sacrifice/retreat
# 他)、`top1Side`・`actualSide` は whatif-v2 の側(attack/defense/both/none)。lib/directAnswers.ts の
# 冒頭コメントに同じ判断の理由を書いてある。
import json
import math
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

if len(sys.argv) < 4:
    sys.exit("使い方: REPORT_DATA_DIR=<フォルダ>[,<フォルダ>…] python3 -X utf8 render_direct.py <direct_answers.json> <final_positions.json> <出力 PDF>")
direct_src, final_src, out = sys.argv[1], sys.argv[2], sys.argv[3]
DA = json.load(open(direct_src, encoding="utf-8"))
FP = json.load(open(final_src, encoding="utf-8"))

# ---- 書体(_head.py・render_whatif.py と同じ流儀) ----
_here = os.path.dirname(os.path.abspath(__file__))
_cands = [os.path.join(_here, "fonts", "IPAexfont00401", "ipaexg.ttf"), "/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"]
_font = next((p for p in _cands if os.path.exists(p)), None)
if _font is None:
    sys.exit("埋め込める日本語フォントが無い(埋め込まない PDF は読む側で文字が欠けるので作らない)")
pdfmetrics.registerFont(TTFont("JPEmbedded", _font))
FONT = FONT_B = "JPEmbedded"

_data_dirs = [d for d in os.environ.get("REPORT_DATA_DIR", _here).split(",") if d]
SF = {}
for _d in _data_dirs:
    _sf_path = os.path.join(_d, "sfens.json")
    if not os.path.exists(_sf_path):
        continue
    _loaded = json.load(open(_sf_path, encoding="utf-8"))
    for _kifu_id, _v in _loaded.items():
        if _kifu_id not in SF:
            SF[_kifu_id] = _v

INK = colors.HexColor("#1e2a32")
MUTED = colors.HexColor("#5a6a74")
ACCENT = colors.HexColor("#2d6a8a")
RED = colors.HexColor("#c9473f")
LINE = colors.HexColor("#d5dde2")
BG = colors.HexColor("#f4f7f9")
COL_PLAYED = colors.HexColor("#8a5a1e")  # 実戦の手(茶の実線)
COL_CAND = colors.HexColor("#1f7a78")  # 第 1 候補(青緑の破線)

st = lambda name, **kw: ParagraphStyle(name, fontName=kw.pop("font", FONT), textColor=kw.pop("color", INK), leading=kw.pop("leading", 15), wordWrap="CJK", alignment=TA_LEFT, **kw)
NB = " "


def P(text, style):
    parts = re.split(r"(<[^>]*>)", text)
    return Paragraph("".join(pt if pt.startswith("<") else pt.replace(" ", NB) for pt in parts), style)


S_TITLE = st("dtitle", font=FONT_B, fontSize=18, leading=23, spaceAfter=2 * mm)
S_LEAD = st("dlead", fontSize=10.2, leading=15, color=MUTED, spaceAfter=3 * mm)
S_H2 = st("dh2", font=FONT_B, fontSize=12.5, leading=17, color=ACCENT, spaceBefore=4 * mm, spaceAfter=1.5 * mm)
S_H3 = st("dh3", font=FONT_B, fontSize=11, leading=14, color=ACCENT, spaceBefore=3 * mm, spaceAfter=1.2 * mm)
S_BODY = st("dbody", fontSize=10, leading=14.5)
S_SMALL = st("dsmall", fontSize=8.6, leading=12, color=MUTED)
S_K = st("dk", fontSize=9.5, leading=13, color=MUTED)
S_V = st("dv", fontSize=9.8, leading=13.5)
S_EYEBROW = st("deyebrow", fontSize=8.2, leading=11, color=ACCENT)

# 2026-09-25 の人間の決定で空にした(凍結の例外 14 件目 ― 冊子の禁止語はすべて使ってよい)。ループと _problems の枠は残す。
BANNED = []

doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title="対局後診断・付録 3(直接の答え)", author="将棋コーチ(試作)")
W = A4[0] - 28 * mm
story = []

# ==================== SFEN の機構(render_whatif.py と同じコード) ====================
ZEN = "０１２３４５６７８９"
KAN = "〇一二三四五六七八九"
PIECE = {"p": "歩", "l": "香", "n": "桂", "s": "銀", "g": "金", "b": "角", "r": "飛", "k": "玉"}
PROM = {"p": "と", "l": "杏", "n": "圭", "s": "全", "b": "馬", "r": "竜"}
RANKS = "abcdefghi"
TAG_JP = [("capture", "取る"), ("drop", "打つ"), ("givesCheck", "王手"), ("sacrifice", "捨て駒"), ("retreat", "引く")]
SIDE_JP = {"attack": "攻め", "defense": "守り", "both": "攻め・守り両方", "none": "どちらでもない"}


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
    f, r = int(token[0]), token[1]
    return f"{10 - f}{RANKS[len(RANKS) - 1 - RANKS.index(r)]}"


def rotate_usi(usi):
    if usi[1] == "*":
        return f"{usi[0]}*{rotate_square(usi[2:4])}"
    suffix = usi[4:]
    return rotate_square(usi[0:2]) + rotate_square(usi[2:4]) + suffix


def apply_move(cells, turn, hands, usi):
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


def piece_kanji(token):
    letter = token.lstrip("+").lower()
    return (PROM if token.startswith("+") else PIECE)[letter]


def move_kanji(cells, usi, prev_to):
    """指し手の日本語表記(render_whatif.py の move_kanji と同じ)。check_answer.py の検査 2 が
    --whatif-pdf の印字と付録 3 の印字を同じ文字列として照合できるよう、表記のコードは変えていない。"""
    if usi[1] == "*":
        to = sq(usi[2:4])
        return f"{ZEN[to[0]]}{KAN[to[1]]}{PIECE[usi[0].lower()]}打"
    frm, to = sq(usi[0:2]), sq(usi[2:4])
    name = piece_kanji(cells[frm])
    head = "同　" if prev_to == to else f"{ZEN[to[0]]}{KAN[to[1]]}"
    return head + name + ("成" if usi.endswith("+") else "")


def mark(turn, user_is_sente):
    return "▲" if (turn == "b") == user_is_sente else "△"


def line_of(cells, turn, hands, pv, user_is_sente, k=5):
    texts = []
    prev_to = None
    cur_cells, cur_turn, cur_hands = cells, turn, hands
    for usi in pv[:k]:
        texts.append(mark(cur_turn, user_is_sente) + move_kanji(cur_cells, usi, prev_to))
        prev_to = usi_squares(usi)[1]
        cur_cells, cur_turn, cur_hands = apply_move(cur_cells, cur_turn, cur_hands, usi)
    return " ".join(texts)


def sc_text(score_cp, mate):
    if mate is not None:
        return "本人の側に詰みあり" if mate > 0 else "本人の玉に詰みあり"
    if score_cp is None:
        return "—"
    return f"{score_cp:+d}".replace("-", "−")


# ==================== 盤面図(render_whatif.py の Board を土台に、矢印(2 本まで)・打つ手の丸を足す) ====================
class Board(Flowable):
    """本人側を下にした盤面図。`sfen` は表示したい局面。`arrows` は最大 2 本
    (`{"frm": (f,r) or None, "to": (f,r), "color": Color, "dashed": bool}`。`frm` が None なら打つ手 = 丸)。"""

    def __init__(self, sfen, user_sente, arrows=(), size=50 * mm, person="本人"):
        super().__init__()
        self.cells, self.turn, self.hands = parse_sfen(sfen)
        self.us = user_sente
        self.arrows = list(arrows)
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

        def center(f, r):
            x, y = xy(f, r)
            return x + q / 2, y + q / 2

        c.setFillColor(colors.HexColor("#fdf8ec"))
        c.rect(ox, oy, S, S, stroke=0, fill=1)
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

        # ---- 矢印(実戦の手 = 茶の実線、第 1 候補 = 青緑の破線)・打つ手は丸(このファイルの新規部分) ----
        for arrow in self.arrows:
            color = arrow["color"]
            c.setStrokeColor(color)
            c.setFillColor(color)
            if arrow["frm"] is None:
                # 打つ手: 行き先に丸
                tx, ty = center(*arrow["to"])
                c.setLineWidth(1.6)
                if arrow.get("dashed"):
                    c.setDash(2, 1.5)
                else:
                    c.setDash()
                c.circle(tx, ty, q * 0.4, stroke=1, fill=0)
                c.setDash()
                continue
            fx, fy = center(*arrow["frm"])
            tx, ty = center(*arrow["to"])
            c.setLineWidth(1.8)
            if arrow.get("dashed"):
                c.setDash(2.2, 1.6)
            else:
                c.setDash()
            # 矢の先端の手前で線を止め、そこに三角の矢じるしを描く(線と重ならないように)
            dx, dy = tx - fx, ty - fy
            dist = math.hypot(dx, dy) or 1.0
            ux, uy = dx / dist, dy / dist
            head_len = q * 0.34
            stop_x, stop_y = tx - ux * head_len, ty - uy * head_len
            c.line(fx, fy, stop_x, stop_y)
            c.setDash()
            perp_x, perp_y = -uy, ux
            half_w = q * 0.16
            p1 = (tx - ux * head_len * 0.2, ty - uy * head_len * 0.2)
            p2 = (stop_x + perp_x * half_w, stop_y + perp_y * half_w)
            p3 = (stop_x - perp_x * half_w, stop_y - perp_y * half_w)
            path = c.beginPath()
            path.moveTo(*p1)
            path.lineTo(*p2)
            path.lineTo(*p3)
            path.close()
            c.drawPath(path, stroke=0, fill=1)


def arrows_of(genuine_actual_usi, genuine_top1_usi):
    """実戦の手(茶の実線)・第 1 候補(青緑の破線)の矢印を組む(§9.1「実戦の手 = 茶の実線、第 1 候補 =
    青緑の破線。打つ手は丸」)。"""
    result = []
    for usi, color, dashed in ((genuine_actual_usi, COL_PLAYED, False), (genuine_top1_usi, COL_CAND, True)):
        if usi is None:
            continue
        frm, to = usi_squares(usi)
        result.append({"frm": frm, "to": to, "color": color, "dashed": dashed})
    return result


# ==================== 凡例 ====================
LEGEND_TEXT = "盤面の色つきの実線が実戦の手、破線が第 1 候補です。打つ手は行き先に丸で示します(持ち駒から打つため、元の升がありません)。"


# ==================== 数の照合・禁止語(render_whatif.py の emit と同じ考え方) ====================
# 10 は「10 分」(組のラベル。report-pdf/check_answer.py の tag_of_time_limit_sec と同じ 600 秒 = 10 分の組)の
# 固定の語彙として常に許可する(render_whatif.py の GLOBAL_ALLOWED_NUMBERS の考え方と同じ ― 個々の局面の事実
# ではなく、この付録の作り方そのものを表す数)。3 は「3 分」の語彙と、方式そのものの数(候補の順位等)を兼ねる。
GLOBAL_ALLOWED_NUMBERS = {1, 2, 3, 5, 10}
_problems = []


def emit(text, allowed):
    plain = re.sub(r"<[^>]*>", "", text)
    plain = re.sub(r"[０-９][〇一二三四五六七八九]", "", plain)
    allowed_all = allowed | GLOBAL_ALLOWED_NUMBERS
    for token in re.findall(r"[0-9]+", plain):
        n = int(token)
        if n not in allowed_all:
            _problems.append(f"データに無い数 {n} が文に出ている: {text[:60]}…")
    for w in BANNED:
        if w in text:
            _problems.append(f"使わない語「{w}」: {text[:60]}…")
    return text


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


def genuine_move(usi, mirrored):
    return rotate_usi(usi) if mirrored and usi is not None else usi


def tags_text_of(tags_obj):
    names = [jp for key, jp in TAG_JP if tags_obj.get(key)]
    return "・".join(names) if names else "特になし"


# ==================== 1 ページ目(表と印の数) ====================
answers = DA["answers"]
counts = DA["counts"]

# STEP ENDING_CLOCK §4 の 23(2026-09-28)。**節の題は中立の 1 つだけ。条件分岐を作らない。**
# もとは固定文字列「盤上はこう勝てた」だった。5 人目の顧客では最後の局面の評価が −4800(盤の上でも
# 下がっていた)で、**題が中身と逆のことを言っていた**(文脈ゼロの批評席が指摘。私と司令塔は同じページの
# 本文から数を抜きながら、題を読んでいなかった)。
# **評価で題を切り替える案は採らない**(司令塔の決定、2026-09-28): この題は entries 全部にかかる
# **局をまたぐ文**であり、#19 で決めた規則「局をまたぐ文には、和に対して真である中立の呼び名だけ」が
# そのまま当たる。切り替えにすると「どの線で勝ちと呼ぶか」という**判定**を道具に入れることになり(線は
# 人間の持ち物)、**分岐の条件を間違える道も残る**。勝ち負けは局ごとの行(`scoreCp`・`mate`)に書く。
FINAL_SECTION_TITLE = "最後の局面をエンジンで読むと"

allowed_p1 = {counts["gamesCount"], counts["totalCount"], counts["totalForkCount"]}
for k, v in counts["top1TagCounts"].items():
    allowed_p1.add(v)
for k, v in counts["top1SideCounts"].items():
    allowed_p1.add(v)
for k, v in counts["actualTagCounts"].items():
    allowed_p1.add(v)

story.append(P("対局後診断・付録 3(試作)", S_EYEBROW))
story.append(P("直接の答え ― この局面では、この手", S_TITLE))
story.append(
    P(
        emit(
            # STEP ENDING_CLOCK §4 の 13(計画の直し、7a40122)。局をまたぐ呼び名は via を問わず使える言い方にする
            # (人間の決定。「時間切れ」と断定しない)。
            f"エンジンで答え合わせした指し手を、局面つきで示します。まず、持ち時間に到達した対局の最後の局面から"
            f"エンジンで読んだ手順(「{FINAL_SECTION_TITLE}」)。次に、長く読まなくても第 1 候補と実戦の手の評価差が"
            f"見えた分かれ道 <b>{counts['totalCount']}</b> 局面(全 <b>{counts['totalForkCount']}</b> 分かれ道のうち)を、"
            f"実戦の手が第 1 候補からどれだけ下がったか(実戦との差)が大きい順に並べます。",
            allowed_p1,
        ),
        S_LEAD,
    )
)

rows = [[P(x, S_K) for x in ["組", "局", "手数", "実戦の手", "第 1 候補", "第 1 候補の性質", "実戦との差"]]]
for a in answers:
    group = a["group"]
    kifu_id = a["kifuId"]
    game_no = a["gameNo"]
    dply = a["displayPly"]
    k = SF.get(kifu_id)
    if k is None:
        _problems.append(f"{kifu_id}: sfens.json にこの局が無い(付録 3 の材料と局が食い違っている)")
        continue
    mirrored = k["side"] == "gote"
    user_is_sente = not mirrored
    genuine_actual = genuine_move(a["actualMove"], mirrored)
    genuine_top1 = genuine_move(a["top1Move"], mirrored)
    before_sfen = k["sfens"][dply - 1]
    cells0, turn0, hands0 = parse_sfen(before_sfen)
    actual_text = mark(turn0, user_is_sente) + move_kanji(cells0, genuine_actual, None)
    top1_text = mark(turn0, user_is_sente) + move_kanji(cells0, genuine_top1, None)
    tag_text = tags_text_of(a["top1Tags"]) + f"({SIDE_JP[a['top1Side']]})"
    gap_text = f"{a['actualGapCp']:+d}".replace("-", "−") if a["actualGapCp"] is not None else "—"
    row_allowed = {game_no, dply}
    if a["actualGapCp"] is not None:
        row_allowed.add(abs(a["actualGapCp"]))
    rows.append(
        [
            P(group, S_V),
            P(emit(str(game_no), row_allowed), S_V),
            P(emit(str(dply), row_allowed), S_V),
            P(actual_text, S_V),
            P(top1_text, S_V),
            P(tag_text, S_SMALL),
            P(emit(gap_text, row_allowed), S_V),
        ]
    )
table1 = Table(rows, colWidths=[13 * mm, 10 * mm, 15 * mm, 25 * mm, 25 * mm, W - 13 * mm - 10 * mm - 15 * mm - 25 * mm - 25 * mm - 22 * mm, 22 * mm], repeatRows=1)
table1.setStyle(CAND_HEADER_STYLE)
story.append(table1)
story.append(Spacer(1, 2.5 * mm))

story.append(P("印の数", S_H3))
tag_rows_top1 = "・".join(f"{jp} {counts['top1TagCounts'][key]}" for key, jp in TAG_JP)
tag_rows_actual = "・".join(f"{jp} {counts['actualTagCounts'][key]}" for key, jp in TAG_JP)
side_rows = "・".join(f"{SIDE_JP[key]} {counts['top1SideCounts'][key]}" for key in ("attack", "defense", "both", "none"))
story.append(notebox([emit(f"第 1 候補の性質: {tag_rows_top1}", allowed_p1), emit(f"第 1 候補の側: {side_rows}", allowed_p1), emit(f"実戦の手の性質: {tag_rows_actual}", allowed_p1)]))
story.append(Spacer(1, 2 * mm))
story.append(P("この付録の読み方", S_K))
story.append(
    notebox(
        [
            LEGEND_TEXT,
            "手の表記は、先手・後手にかかわらず ▲ が本人、△ が相手の手です。盤面図は本人の側を下にしています。",
            "エンジンの候補は「正解」ではなく、比べるための材料です。読み筋は、エンジンが読んだ一例で、実際の相手がそう指すとは限りません。",
        ]
    )
)
story.append(PageBreak())

# ==================== 最後の局面の節(持ち時間に到達した対局) ====================
story.append(P(FINAL_SECTION_TITLE, S_H2))
story.append(
    P(
        # STEP ENDING_CLOCK §4 の 13。局をまたぐ呼び名は via を問わず使える言い方にする(人間の決定)。
        "持ち時間に到達した対局の、最後の局面からエンジンで読みました。持ち時間が残っていて指し続けていたら、という"
        "仮定の読みです(実際にこう進んだわけではありません)。",
        S_BODY,
    )
)
story.append(Spacer(1, 2 * mm))

for e in FP["entries"]:
    kifu_id = e["kifuId"]
    k = SF.get(kifu_id)
    if k is None:
        _problems.append(f"{kifu_id}: sfens.json にこの局が無い(final_positions.json の材料と局が食い違っている)")
        continue
    mirrored = k["side"] == "gote"
    user_is_sente = not mirrored
    final_sfen = k["sfens"][-1]  # 本人が指した実際の向きの、最後の局面(genuine)
    cells0, turn0, hands0 = parse_sfen(final_sfen)
    top1_usi = e.get("top1Move")
    genuine_top1 = genuine_move(top1_usi, mirrored)
    arrows = arrows_of(None, genuine_top1) if genuine_top1 is not None else []

    board = Board(final_sfen, user_is_sente, arrows=arrows, person="本人", size=50 * mm)

    # STEP ENDING_CLOCK §4 の 13。局ごとの見出しは via(final_positions.json が運ぶ印)で書き分ける(人間の決定、
    # 断定しない)。via == "word" は棋譜に `切れ負け` と書かれている局なので断定にならない。
    via = e.get("via")
    if via == "word":
        ending_clause = "切れ負け"
    elif via == "clock":
        ending_clause = "持ち時間に到達(終局の表示は投了)"
    else:
        _problems.append(f"{e['kifuId']}: final_positions.json の via が無い/不明({via!r})")
        ending_clause = "持ち時間に到達"

    allowed_g = {e["gameNo"], e["moves"]}
    lines = [P(f"{e['group']} の {e['gameNo']} 局目 ・ {e['moves']} 手で{ending_clause}", S_EYEBROW), P("最後の局面から、エンジンの読み", S_H3)]
    if e.get("mate") is not None:
        n = abs(e["mate"])
        allowed_g.add(n)
        if e["mate"] > 0:
            lines.append(P(emit(f"エンジンの読みでは、ここから <b>{n} 手で本人の勝ちの詰み</b>です。", allowed_g), S_BODY))
        else:
            lines.append(P(emit(f"エンジンの読みでは、ここから <b>{n} 手で本人の玉に詰み</b>です。", allowed_g), S_BODY))
    elif e.get("scoreCp") is not None:
        allowed_g.add(abs(e["scoreCp"]))
        lines.append(P(emit(f"エンジンの読みでは、この局面の評価は <b>{sc_text(e['scoreCp'], None)}</b> です。", allowed_g), S_BODY))
    else:
        lines.append(P("エンジンの評価を読めませんでした。", S_BODY))
    if genuine_top1 is not None:
        pv_genuine = [genuine_move(u, mirrored) for u in e.get("pv", [])]
        pv_text = line_of(cells0, turn0, hands0, pv_genuine, user_is_sente, 7)
        lines.append(P("エンジンの読み筋(青緑の破線・丸が最初の手)", S_K))
        lines.append(P(emit(pv_text, allowed_g), S_SMALL))

    row = Table([[board, lines]], colWidths=[62 * mm, W - 62 * mm])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(KeepTogether([row]))
    story.append(Spacer(1, 4 * mm))

if len(FP["entries"]) == 0:
    story.append(P("該当する局はありませんでした。", S_SMALL))
story.append(PageBreak())

# ==================== 「浅い読みで見えた分かれ道」(問題 2) ====================
story.append(P("浅い読みで見えた分かれ道", S_H2))
story.append(
    P(
        emit(
            f"長く読まなくても、実戦の手と第 1 候補の評価差が見えた局面(全 {counts['totalForkCount']} 分かれ道のうち "
            f"{counts['totalCount']} 局面)を、実戦との差が大きい順に並べます。",
            allowed_p1,
        ),
        S_BODY,
    )
)
story.append(Spacer(1, 2 * mm))

for a in answers:
    group = a["group"]
    kifu_id = a["kifuId"]
    game_no = a["gameNo"]
    dply = a["displayPly"]
    k = SF.get(kifu_id)
    if k is None:
        continue  # 1 ページ目ですでに問題を記録済み
    mirrored = k["side"] == "gote"
    user_is_sente = not mirrored
    genuine_actual = genuine_move(a["actualMove"], mirrored)
    genuine_top1 = genuine_move(a["top1Move"], mirrored)
    before_sfen = k["sfens"][dply - 1]
    cells0, turn0, hands0 = parse_sfen(before_sfen)

    arrows = arrows_of(genuine_actual, genuine_top1)
    board = Board(before_sfen, user_is_sente, arrows=arrows, person="本人", size=46 * mm)

    allowed_g = {game_no, dply}
    if a["actualGapCp"] is not None:
        allowed_g.add(abs(a["actualGapCp"]))
    allowed_g.add(a["firstVisibleNodes"])

    actual_text = mark(turn0, user_is_sente) + move_kanji(cells0, genuine_actual, None)
    top1_text = mark(turn0, user_is_sente) + move_kanji(cells0, genuine_top1, None)
    pv_genuine = [genuine_move(u, mirrored) for u in a["pv"]]
    pv_text = line_of(cells0, turn0, hands0, pv_genuine, user_is_sente, 5)
    gap_text = f"{a['actualGapCp']:+d}".replace("-", "−") if a["actualGapCp"] is not None else "—"

    lines = [
        P(emit(f"{group} の {game_no} 局目 {dply} 手目", allowed_g), S_EYEBROW),
        P(f"実戦の手(茶の実線): <b>{actual_text}</b>", S_BODY),
        P(f"第 1 候補(青緑の破線): <b>{top1_text}</b>", S_BODY),
        P(emit(pv_text, allowed_g), S_SMALL),
        P(emit(f"第 1 候補の性質: {tags_text_of(a['top1Tags'])}({SIDE_JP[a['top1Side']]})", allowed_g), S_SMALL),
        P(emit(f"実戦の手の性質: {tags_text_of(a['actualTags'])}({SIDE_JP[a['actualSide']]})", allowed_g), S_SMALL),
        P(emit(f"実戦との差: {gap_text}(浅い読みで見えたノード数: {a['firstVisibleNodes']})", allowed_g), S_SMALL),
    ]
    row = Table([[board, lines]], colWidths=[58 * mm, W - 58 * mm])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm)]))
    story.append(KeepTogether([row, Spacer(1, 3 * mm)]))

if len(answers) == 0:
    story.append(P("該当する局面はありませんでした。", S_SMALL))

story.append(Spacer(1, 3 * mm))
story.append(P("試作版につき、有段者による確認はまだ受けていません。エンジンの読みは 1 局面あたり 100 万ノードです。", st("dfoot", fontSize=8, leading=11, color=MUTED)))

if _problems:
    print("\n".join(_problems), file=sys.stderr)
    sys.exit(1)

doc.build(story)
print(f"wrote {out}({len(FP['entries'])} 局({FINAL_SECTION_TITLE})・{len(answers)} 局面(浅い読みで見えた分かれ道))")
