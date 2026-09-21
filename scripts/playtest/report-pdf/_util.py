SF = json.load(open(os.path.join(_data_dir, "sfens.json"), encoding="utf-8"))
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
    def __init__(self, sfen, user_sente, usi=None, size=52 * mm, person="本人", arrows=()):
        super().__init__(); self.arrows = list(arrows); self.cells, self.hands = parse_sfen(sfen); self.us = user_sente; self.usi = usi; self.size = size; self.person = person
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
            c.setFillColor(INK if name not in PROM.values() else RED); c.setFont(FONT, fs); c.drawCentredString(0, -fs * 0.36, name); c.restoreState()
        c.setFillColor(MUTED); c.setFont(FONT, 6)
        for i in range(9):
            f = (9 - i) if self.us else (i + 1); r = (i + 1) if self.us else (9 - i)
            c.drawCentredString(ox + i * q + q / 2, oy + S + 1.2, ZEN[f]); c.drawString(ox + S + 1.5, oy + S - (i + 1) * q + q / 2 - 2, KAN[r])
        for yy, lab, hs in ((oy - 6.2 * mm, f"{self.person}の持ち駒", self.hands[self.us]), (oy + S + 3.4 * mm, "相手の持ち駒", self.hands[not self.us])):
            c.setFillColor(BG); c.setStrokeColor(LINE); c.setLineWidth(0.4); c.rect(ox, yy, S, 4.6 * mm, stroke=1, fill=1)
            c.setFillColor(MUTED); c.setFont(FONT, 7); c.drawString(ox + 1.2 * mm, yy + 1.35 * mm, lab)
            c.setFillColor(INK); c.setFont(FONT, 9); c.drawRightString(ox + S - 1.2 * mm, yy + 1.2 * mm, " ".join(hs) or "なし")
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

