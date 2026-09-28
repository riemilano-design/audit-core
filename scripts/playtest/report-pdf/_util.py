SF = json.load(open(os.path.join(_data_dir, "sfens.json"), encoding="utf-8"))
# **盤と SFEN の読みは `board_draw.py` が正本**(後半の `exit_body.py` も同じものを使う)。
# ここは**薄い包み**で、`_head.py` の様式 6 つを束ねて渡すだけ ― `_mid.py` の呼び出しは変えない。
import board_draw
from board_draw import ZEN, KAN, PIECE, PROM, parse_sfen, usi_squares  # noqa: F401

_BOARD_STYLE = board_draw.BoardStyle(ink=INK, red=RED, bg=BG, line=LINE, muted=MUTED, font=FONT)


class Board(board_draw.Board):
    """`_head.py` の様式で描く盤(呼び出しの形は今までと同じ)。"""

    def __init__(self, sfen, user_sente, usi=None, size=52 * mm, person="本人", arrows=()):
        super().__init__(sfen, user_sente, _BOARD_STYLE, usi=usi, size=size,
                         person=person, arrows=arrows)

EV = {(e["gameNo"], e["ply"]): e for e in m["events"]}
REP = {(r["gameNo"], r["displayPly"]): r for r in c["reps"]}
def side_mark(ply): return "▲" if ply % 2 == 1 else "△"
def disp_move(g, ply, text):
    """KIF の表記(元の升の括弧つき)を、本人が読む表記にする。「同」は行き先の升を補う。"""
    t = _re.sub(r"\(\d+\)$", "", text).replace("　", "")
    if t.startswith("同"):
        _, to = usi_squares(SF[g["id"]]["moves"][ply - 1]); t = ZEN[to[0]] + KAN[to[1]] + t
    return side_mark(ply) + t

COL_PLAYED = colors.HexColor("#8a5a1e"); COL_CAND = colors.HexColor("#1f7a78")
class Legend(Flowable):
    def __init__(self, same=False): super().__init__(); self.same = same
    def wrap(self, aw, ah): return 60 * mm, 9 * mm if not self.same else 5 * mm
    def draw(self):
        c = self.canv; c.setFont(FONT, 7.5); y = 5.5 * mm if not self.same else 1.5 * mm
        c.setStrokeColor(COL_PLAYED); c.setLineWidth(1.6); c.line(0, y + 2, 9 * mm, y + 2); c.setFillColor(INK); c.drawString(10.5 * mm, y, "実戦の手" + ("(エンジンの候補も同じ手)" if self.same else ""))
        if not self.same:
            y = 1.5 * mm; c.setStrokeColor(COL_CAND); c.setDash(3, 2); c.line(0, y + 2, 9 * mm, y + 2); c.setDash(); c.drawString(10.5 * mm, y, "比べるためのエンジンの候補(丸は打つ手)")

