# STEP FIG-1: 分岐図(1 つの局面 → 相手玉の近くへ向かう候補 / 自玉の近くへ向かう候補 → 2 つを並べて比べる)
#
# 【この図が示すもの・示さないもの(人間の指定 2026-09-26)】
#   示す  : **思考手順**。「1 つの局面から候補が 2 本に分かれ、その 2 つを並べて比べる」という行為そのもの。
#           ②の承認済みの行動(`M4`「攻めの候補と自玉側の候補を 1 つずつ思い浮かべてから比べる」)を、
#           文だけでなく目で見せるのが狙い。
#   示さない: **正解表示なし**(どちらが良い手かを出さない)。**評価値なし**(cp を出さない)。
#           **どちらがエンジンの第一候補で、どちらが実戦の手かも図には出さない**
#           ― それを出すと「片方が正しい」に読めるため(人間の指定)。
#   材料  : **既存データのみ**(`direct_answers.json` の `answers[]`)。エンジンは回さない。
#
# 【既存の流儀に合わせたこと(`render_whatif.py`・`render_time_cause.py` と同じ)】
#   - `_head/_util/_mid/_app_head/_app/_tail` の 6 本は変えない。新しい図は独立した 1 本にする。
#   - 盤は「本人の側を下にする」。書体は埋め込みフォント(無ければ作らない)。
#   - 矢印の色と線種は**良し悪しを表さない**。ここでは**側の別**だけを表す。
#
# 【この図が数について言えること(既知事項 P-89・族 F-1)】
#   (**「p3」は冊子の 3 ページ目の呼び名**で、顧客の呼び名 `p4` とは別のもの ― 紛らわしいので出典を書く。
#    85・88 の出どころは `records/obs-3/p4-min3-r2/00-obs_snapshot.p4.min3.r2c.json`(顧客 `p4` の
#    3 分切れ負けの組)の `obs.fork.sideCrossTable`。独立監査の指摘 2026-09-26。)
#   **p3 の 85・88 は `obs.fork.sideCrossTable` の 259 行の母集団**で、
#   **この図の局面は `direct_answers` の 3 分 161 行の母集団**(側が食い違う行は 32)。**母集団が違う。**
#   → 図の説明に「85 件のうちの 1 つ」と書いてはいけない。書けるのは
#     「この 18 局の中で、2 つの候補が逆の側だった局面の 1 つ」まで。`CAPTION` がその文を持つ。
#
# 使い方:
#   python3 -X utf8 fig1.py <direct_answers.json> <出力 PDF> [--game N] [--ply M] [--group "3 分"]
#   局と手数を省くと、side が食い違う行のうち**局番号・手数の昇順で最初の 1 件**を使う(勝手に「良い例」を選ばない)。

import json
import os
import sys

import board_spec  # 持ち駒の語の 1 か所(P-176)
import check_answer  # 側の語の 1 か所(P-185)

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer

RANKS = "abcdefghi"
ZEN = "０１２３４５６７８９"
KAN = "〇一二三四五六七八九"
PIECE = {"p": "歩", "l": "香", "n": "桂", "s": "銀", "g": "金", "b": "角", "r": "飛", "k": "玉"}
PROM = {"p": "と", "l": "杏", "n": "圭", "s": "全", "b": "馬", "r": "竜"}

# 側の色。**良し悪しではなく向きだけ**を表す(攻め = 相手玉の側、自玉側 = 自分の玉の側)。
COL_ATTACK = colors.HexColor("#8a5a1e")
COL_DEFENSE = colors.HexColor("#1f7a78")
INK = colors.HexColor("#1e2a32")
MUTED = colors.HexColor("#5a6a74")
LINE = colors.HexColor("#d5dde2")
BG = colors.HexColor("#f4f7f9")

SIDE_LABEL = {"attack": "相手玉の近くへ向かう候補", "defense": "自玉の近くへ向かう候補"}
# 側の語は **`check_answer.SIDE_JP` の 1 か所**から作る(P-185。2026-09-29)。
# 「攻め側」は攻めの語 + 「側」。**語を別に書くと、片方だけ直して 2 通りに戻る。**
# この表は今は例外の文にしか出ないが、**写しは残さない**(P-111 の病気)。
# **文の中の語は表では覆えない** ― この図の `STEPS` と承認済みの行動の文は
# 「自玉側」を文として持っている(承認済みの文は変えない)。
SIDE_SHORT = {"attack": check_answer.SIDE_JP["attack"] + "側",
              "defense": check_answer.SIDE_JP["defense"]}

# 「どちらが良い手かは示していません」という否定文は**入れない**(統括の判断 2026-09-26)。理由は 2 つ:
#   (1) 冊子の 1 ページ目の冒頭に既に「手の良し悪しを採点するものではありません」がある。同じことを
#       図の脇で繰り返すと、**いちばん見てほしい瞬間に「良い手」という語を顧客の目に入れる**ことになる。
#   (2) 下の肯定文(「見てほしいのは〜手順です」)が同じ仕事をしている。否定文を消しても期待は折れる。
# **母集団の一文は消さない**(P-89・族 F-1)。この図の局面は `direct_answers` の 3 分 161 行から来ており、
# p3 の 85・88 は `obs.fork.sideCrossTable` の 259 行から来ている。**「85 件のうちの 1 つ」とは書けない。**
CAPTION = (
    "この 18 局の中で、2 つの候補が逆の側になっていた局面の 1 つです。"
    "見てほしいのは、<b>1 つの局面から候補が 2 本に分かれること</b>と、"
    "<b>その 2 つを並べて比べるという手順</b>です。"
)

# ---- 材料の読み方 ----


def parse_sfen(sfen):
    """`board turn hands [ply]` の先頭 3 欄だけを見る(4 欄目の手数は使わない)。"""
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
            k = ch.lower()
            cells[(f, r)] = ((PROM if prom else PIECE)[k], ch.isupper())
            prom = False
            f -= 1
    hands = {True: [], False: []}
    if hands_s != "-":
        n = ""
        for ch in hands_s:
            if ch.isdigit():
                n += ch
                continue
            hands[ch.isupper()].append(board_spec.hand_word(PIECE[ch.lower()], int(n) if n else 1))
            n = ""
    return cells, turn, hands


def usi_squares(usi):
    rk = lambda c: RANKS.index(c) + 1
    if usi[1] == "*":
        return None, (int(usi[2]), rk(usi[3]))
    return (int(usi[0]), rk(usi[1])), (int(usi[2]), rk(usi[3]))


def pick_branch_rows(answers, group=None):
    """2 つの候補が **攻め と 自玉側 で逆**だった行だけを返す(局番号・手数の昇順)。

    **`both`・`none` は入れない** ― 側が付いていない行は「2 本に分かれた」と言えないため。
    絞り込みだけを行い、「良い例」を選ばない(選ぶのは呼び出し側)。
    """
    out = []
    for r in answers:
        if group is not None and r.get("group") != group:
            continue
        sides = {r.get("top1Side"), r.get("actualSide")}
        if sides == {"attack", "defense"}:
            out.append(r)
    return sorted(out, key=lambda r: (r["gameNo"], r["displayPly"]))


def side_moves(row):
    """行から **{側: 指し手}** を作る。

    **どちらがエンジンの第一候補で、どちらが実戦の手かは返さない**(人間の指定でこの図には出さないため、
    図を組む側がうっかり出せないように、この段で落としておく)。
    """
    out = {}
    for key_move, key_side in (("top1Move", "top1Side"), ("actualMove", "actualSide")):
        side = row.get(key_side)
        move = row.get(key_move)
        if side in ("attack", "defense") and move:
            out[side] = move
    return out


def check_branch_row(row):
    """図を描く前に材料を確かめる。**通らなければ例外**(組んだ後に気づく形にしない)。

    見るのは 3 つ:
      1. `sfen` があり、盤・手番・持ち駒の 3 欄が読めること。
      2. 側が **攻め と 自玉側 の 2 つ**そろっていること。
      3. **2 つの手の「元の升」に、手番側自身の駒が実在すること**(= `sfen` が「指す前」の局面であること)。
         打つ手は元の升が無いので、代わりに**その駒が手番側の持ち駒にあること**を見る。
    3 を見ないと、矢印の元に駒が無い図が静かに出る。

    **「駒が実在する」だけでは足りない**(独立監査の指摘 2026-09-26): 升の取り違えが起きたとき、
    その升に**相手の駒**があれば「実在する」を通ってしまう。実例として、第 1 局 41 手目で
    `7h6i` を `8h6i` に書き換えると、8 八には**後手の成桂**が実在するので、所有者を見ない検査は沈黙した
    (**等価変異ではない**ことを監査が確かめている)。→ **所有者まで見る。**
    """
    where = f"gameNo {row.get('gameNo')} displayPly {row.get('displayPly')}"
    sfen = row.get("sfen")
    if not sfen or len(sfen.split(" ")) < 3:
        raise ValueError(f"{where}: sfen が無いか欄が足りない")
    cells, turn, hands = parse_sfen(sfen)
    moves = side_moves(row)
    if set(moves) != {"attack", "defense"}:
        raise ValueError(f"{where}: 側が攻めと自玉側の 2 つそろっていない({sorted(moves)})")
    us = turn == "b"
    for side, usi in moves.items():
        frm, _to = usi_squares(usi)
        if frm is None:
            piece = PIECE[usi[0].lower()]
            if not any(h.startswith(piece) for h in hands[us]):
                raise ValueError(f"{where}: 打つ手 {usi} の駒 {piece} が手番側の持ち駒に無い")
        elif frm not in cells:
            raise ValueError(f"{where}: {SIDE_SHORT[side]} の手 {usi} の元の升 {frm} に駒が無い")
        elif cells[frm][1] != us:
            # 升に駒はあるが**相手の駒**。手番側がそこから指せないので、升か局面のどちらかが壊れている。
            raise ValueError(f"{where}: {SIDE_SHORT[side]} の手 {usi} の元の升 {frm} の駒 {cells[frm][0]} が手番側の駒でない")
    return True


# ---- 描くもの ----


class Board(Flowable):
    """本人側を下にした盤面図。`sfen` は**指す前**の局面。矢印は側ごとに 1 本ずつ。"""

    def __init__(self, sfen, user_sente, size=52 * mm, person="本人", arrows=()):
        super().__init__()
        self.arrows = list(arrows)
        self.cells, self.turn, self.hands = parse_sfen(sfen)
        self.us = user_sente
        self.size = size
        self.person = person

    def wrap(self, aw, ah):
        return self.size + 8 * mm, self.size + 17 * mm

    def draw(self):
        import math

        c = self.canv
        S = self.size
        q = S / 9
        ox, oy = 1 * mm, 7.5 * mm

        def xy(f, r):
            col = (9 - f) if self.us else (f - 1)
            row = (r - 1) if self.us else (9 - r)
            return ox + col * q, oy + S - (row + 1) * q

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
        for (f, r), (name, is_sente) in self.cells.items():
            x, y = xy(f, r)
            mine = is_sente == self.us
            c.saveState()
            c.translate(x + q / 2, y + q / 2)
            if not mine:
                c.rotate(180)
            c.setFillColor(INK if name not in PROM.values() else colors.HexColor("#c9473f"))
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
        for yy, lab, hs in (
            (oy - 6.2 * mm, f"{self.person}の持ち駒", self.hands[self.us]),
            (oy + S + 3.4 * mm, "相手の持ち駒", self.hands[not self.us]),
        ):
            c.setFillColor(BG)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.4)
            c.rect(ox, yy, S, 4.6 * mm, stroke=1, fill=1)
            c.setFillColor(MUTED)
            c.setFont(FONT, 7)
            c.drawString(ox + 1.2 * mm, yy + 1.35 * mm, lab)
            c.setFillColor(INK)
            c.setFont(FONT, 9)
            c.drawRightString(ox + S - 1.2 * mm, yy + 1.2 * mm, " ".join(hs) or "なし")

        def center(s):
            x, y = xy(*s)
            return x + q / 2, y + q / 2

        # 矢印。**色と線種は側の別だけを表す**(良し悪しではない)。打つ手は行き先を丸で囲む。
        for usi, col, shift in self.arrows:
            fr, to_ = usi_squares(usi)
            tx, ty = center(to_)
            c.saveState()
            c.setStrokeColor(col)
            c.setFillColor(col)
            c.setLineWidth(1.6)
            if fr is None:
                c.circle(tx, ty, q * 0.46, stroke=1, fill=0)
            else:
                fx, fy = center(fr)
                ang = math.atan2(ty - fy, tx - fx)
                nx, ny = -math.sin(ang) * shift, math.cos(ang) * shift
                fx, fy, tx, ty = fx + nx, fy + ny, tx + nx, ty + ny
                ex, ey = tx - math.cos(ang) * q * 0.28, ty - math.sin(ang) * q * 0.28
                c.line(fx, fy, ex, ey)
                hl = q * 0.34
                pth = c.beginPath()
                pth.moveTo(tx, ty)
                pth.lineTo(tx - hl * math.cos(ang - 0.45), ty - hl * math.sin(ang - 0.45))
                pth.lineTo(tx - hl * math.cos(ang + 0.45), ty - hl * math.sin(ang + 0.45))
                pth.close()
                c.drawPath(pth, stroke=0, fill=1)
            c.restoreState()


class SideLegend(Flowable):
    """凡例。**側の別だけ**を書く(どちらが実戦か・どちらが第一候補かは書かない)。"""

    def wrap(self, aw, ah):
        return 90 * mm, 10 * mm

    def draw(self):
        c = self.canv
        c.setFont(FONT, 8)
        for i, side in enumerate(("attack", "defense")):
            y = (6.0 - i * 4.4) * mm
            c.setStrokeColor(COL_ATTACK if side == "attack" else COL_DEFENSE)
            c.setLineWidth(1.6)
            c.line(0, y + 2, 9 * mm, y + 2)
            c.setFillColor(INK)
            c.drawString(10.5 * mm, y, SIDE_LABEL[side] + "(丸は打つ手)")


class StepStrip(Flowable):
    """思考手順の帯。①いまの局面 → ②2 つ挙げる → ③並べて比べる。**どちらを選ぶかは書かない**。"""

    STEPS = ("①いまの局面を見る", "②2 つ挙げる(攻め側・自玉側)", "③並べて比べる")

    def wrap(self, aw, ah):
        self.aw = aw
        return aw, 11 * mm

    def draw(self):
        c = self.canv
        n = len(self.STEPS)
        gap = 5 * mm
        w = (self.aw - gap * (n - 1)) / n
        for i, label in enumerate(self.STEPS):
            x = i * (w + gap)
            c.setFillColor(BG)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.5)
            c.roundRect(x, 1.5 * mm, w, 8 * mm, 1.5 * mm, stroke=1, fill=1)
            c.setFillColor(INK)
            c.setFont(FONT, 8)
            c.drawCentredString(x + w / 2, 4.2 * mm, label)
            if i < n - 1:
                c.setStrokeColor(MUTED)
                c.setLineWidth(0.8)
                c.line(x + w + 1.2 * mm, 5.5 * mm, x + w + gap - 1.2 * mm, 5.5 * mm)


def build_fig1(row):
    """1 行から、分岐図の Flowable の並びを作る。**呼ぶ前に `check_branch_row` を通す。**"""
    check_branch_row(row)
    cells, turn, hands = parse_sfen(row["sfen"])
    us = turn == "b"
    moves = side_moves(row)
    arrows = [
        (moves["attack"], COL_ATTACK, 1.1),
        (moves["defense"], COL_DEFENSE, -1.1),
    ]
    head = P(f"第 {row['gameNo']} 局 {row['displayPly']} 手目の局面", ST_H)
    return [head, StepStrip(), Spacer(1, 2 * mm), Board(row["sfen"], us, arrows=arrows), SideLegend(), Spacer(1, 2 * mm), P(CAPTION, ST_BODY)]


# ---- 書体と台本(既存の流儀。埋め込めるフォントが無ければ作らない) ----

_here = os.path.dirname(os.path.abspath(__file__))
_cands = [
    os.path.join(_here, "fonts", "IPAexfont00401", "ipaexg.ttf"),
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
]
_font = next((p for p in _cands if os.path.exists(p)), None)
if _font is None and __name__ == "__main__":
    sys.exit("埋め込める日本語フォントが無い(埋め込まない PDF は読む側で文字が欠けるので作らない)")
if _font is not None:
    pdfmetrics.registerFont(TTFont("JPEmbedded", _font))
FONT = "JPEmbedded"

ST_H = ParagraphStyle("h", fontName=FONT, textColor=INK, fontSize=10.5, leading=15, wordWrap="CJK", alignment=TA_LEFT)
ST_BODY = ParagraphStyle("b", fontName=FONT, textColor=INK, fontSize=9, leading=14, wordWrap="CJK", alignment=TA_LEFT)


def P(text, style):
    return Paragraph(text, style)


def main(argv):
    if len(argv) < 3:
        sys.exit("使い方: python3 -X utf8 fig1.py <direct_answers.json> <出力 PDF> [--game N] [--ply M] [--group \"3 分\"]")
    src, out = argv[1], argv[2]
    game = ply = None
    group = "3 分"
    for i, a in enumerate(argv):
        if a == "--game":
            game = int(argv[i + 1])
        elif a == "--ply":
            ply = int(argv[i + 1])
        elif a == "--group":
            group = argv[i + 1]
    data = json.load(open(src, encoding="utf-8"))
    rows = pick_branch_rows(data["answers"], group=group)
    if not rows:
        sys.exit(f"側が攻めと自玉側で逆の行が {group} の組に無い(図を出さない)")
    if game is not None and ply is not None:
        rows = [r for r in rows if r["gameNo"] == game and r["displayPly"] == ply]
        if not rows:
            sys.exit(f"gameNo {game} displayPly {ply} は「側が逆の行」に無い(勝手に別の局面へ替えない)")
    row = rows[0]
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title="分岐図")
    doc.build([KeepTogether(build_fig1(row))])
    print(f"書いた {out} / gameNo {row['gameNo']} displayPly {row['displayPly']} / 候補になった行 {len(pick_branch_rows(data['answers'], group=group))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
