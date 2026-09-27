# -*- coding: utf-8 -*-
# 対局後診断レポートの JSON(build_report.mts の出力)を reportlab で PDF に描く。使い捨て(コミットしない)。
import json, sys, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, KeepTogether, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

src, out = sys.argv[1], sys.argv[2]
m = json.load(open(src, encoding="utf-8"))

# フォント: ヒラギノ(TTC)→ 無ければ CID フォント
FONT, FONT_B = "HeiseiKakuGo-W5", "HeiseiKakuGo-W5"
_here = os.path.dirname(os.path.abspath(__file__))
# STEP PIPE 作業 B: prose.json・sfens.json の置き場だけ、環境変数 REPORT_DATA_DIR で渡せるようにする(既定は _here。中身は変えない)
_data_dir = os.environ.get("REPORT_DATA_DIR", _here)
_cands = [os.path.join(_here, "fonts", "IPAexfont00401", "ipaexg.ttf"), "/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"]
_font = next((p for p in _cands if os.path.exists(p)), None)
if _font is None:
    sys.exit("埋め込める日本語フォントが無い(埋め込まない PDF は読む側で文字が欠けるので作らない)")
pdfmetrics.registerFont(TTFont("JPEmbedded", _font))
FONT = FONT_B = "JPEmbedded"  # 太字は同じ書体(色と大きさで見分ける)

INK = colors.HexColor("#1e2a32"); MUTED = colors.HexColor("#5a6a74"); ACCENT = colors.HexColor("#2d6a8a")
RED = colors.HexColor("#c9473f"); LINE = colors.HexColor("#d5dde2"); BG = colors.HexColor("#f4f7f9"); BG_RED = colors.HexColor("#fbf1f0")

st = lambda name, **kw: ParagraphStyle(name, fontName=kw.pop("font", FONT), textColor=kw.pop("color", INK), leading=kw.pop("leading", 15), wordWrap="CJK", **kw)
NB = "\u00a0"
def P(text, style):
    # 半角空白を改行しない空白にして、数字の前後で折れないようにする(CJK の折り返しは文字ごと)
    import re as _re
    parts = _re.split(r"(<[^>]*>)", text)
    return Paragraph("".join(pt if pt.startswith("<") else pt.replace(" ", NB) for pt in parts), style)
S_TITLE = st("title", font=FONT_B, fontSize=19, leading=24, spaceAfter=2 * mm)
S_LEAD = st("lead", fontSize=10.5, leading=15, color=MUTED, spaceAfter=3 * mm)
S_H2 = st("h2", font=FONT_B, fontSize=13, leading=17, color=ACCENT, spaceBefore=6 * mm, spaceAfter=2 * mm)
S_BODY = st("body", fontSize=10.5, leading=15)
S_SMALL = st("small", fontSize=9, leading=12.5, color=MUTED)
S_NUM = st("num", font=FONT_B, fontSize=20, leading=24, color=ACCENT)
S_LBL = st("lbl", fontSize=8.5, leading=11, color=MUTED)
S_K = st("k", fontSize=9.5, leading=13, color=MUTED)
S_V = st("v", fontSize=10.5, leading=14)
S_CARDH = st("cardh", font=FONT_B, fontSize=10.5, leading=14)

def fmt(n):
    return "—" if n is None else (f"+{n}" if n > 0 else f"{n}")

class Spark(Flowable):
    def __init__(self, scores, marks, w=72 * mm, h=16 * mm):
        super().__init__(); self.scores = scores; self.marks = set(marks); self.w = w; self.h = h
    def wrap(self, aw, ah): return self.w, self.h
    def draw(self):
        c = self.canv; w, h, pad = self.w, self.h, 2
        c.setFillColor(BG); c.setStrokeColor(LINE); c.rect(0, 0, w, h, stroke=1, fill=1)
        c.setStrokeColor(colors.HexColor("#b8c4cb")); c.setDash(2, 2); c.line(pad, h / 2, w - pad, h / 2); c.setDash()
        n = len(self.scores)
        if n < 2: return
        clamp = lambda v: max(-2000, min(2000, v))
        x = lambda i: pad + i * (w - 2 * pad) / (n - 1)
        y = lambda v: h / 2 + (clamp(v) / 2000) * (h / 2 - pad)
        c.setStrokeColor(ACCENT); c.setLineWidth(1.1)
        prev = None
        for i, v in enumerate(self.scores):
            if v is None: prev = None; continue
            if prev is not None: c.line(x(prev[0]), y(prev[1]), x(i), y(v))
            prev = (i, v)
        c.setFillColor(RED)
        for i in self.marks:
            v = self.scores[i] if i < len(self.scores) else None
            c.circle(x(i), y(v if v is not None else 0), 2.2, stroke=0, fill=1)
        c.setFillColor(MUTED); c.setFont(FONT, 6); c.drawString(pad + 1, h - 7, "+2000"); c.drawString(pad + 1, 2, "−2000")



doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title=m["title"], author="将棋コーチ(試作)")
W = A4[0] - 28 * mm
story = []
def boxes(items, n=4):
    t = Table([[[P(str(v), S_NUM), P(l, S_LBL)] for v, l in items]], colWidths=[W / n] * n)
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("INNERGRID", (0, 0), (-1, -1), 0.6, LINE), ("BACKGROUND", (0, 0), (-1, -1), BG), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 3.5 * mm)]))
    return t
def kv(rows, kw=36 * mm):
    t = Table([[P(k, S_K), P(v, S_V)] for k, v in rows], colWidths=[kw, W - kw])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.6 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6 * mm), ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm)]))
    return t
def notebox(lines):
    t = Table([[P("・" + n, S_SMALL)] for n in lines], colWidths=[W])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("BACKGROUND", (0, 0), (-1, -1), BG), ("LEFTPADDING", (0, 0), (-1, -1), 3.5 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5 * mm), ("TOPPADDING", (0, 0), (-1, -1), 1.2 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2 * mm)]))
    return t
def boxflow(items, bgc=BG, bar=ACCENT):
    t = Table([[items]], colWidths=[W])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE), ("LINEBEFORE", (0, 0), (0, -1), 2.2, bar), ("BACKGROUND", (0, 0), (-1, -1), bgc), ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm), ("TOPPADDING", (0, 0), (-1, -1), 2 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm)]))
    return t
S_BIG = st("big", font=FONT_B, fontSize=21, leading=26, spaceAfter=1 * mm)
S_TAG = st("tag", fontSize=9.5, leading=12, color=ACCENT)
S_BOXH = st("boxh", font=FONT_B, fontSize=12, leading=16, color=ACCENT)
S_B2 = st("b2", fontSize=10.4, leading=15)
S_NUM2 = st("num2", font=FONT_B, fontSize=24, leading=28, color=ACCENT)
S_H3 = st("h3", font=FONT_B, fontSize=11.5, leading=15, color=ACCENT, spaceBefore=4 * mm, spaceAfter=1.5 * mm)

s = m["summary"]; pr = m.get("pairs") or {"fell": m["overview"]["fell"]}; c = m.get("candidate") or {"reps": m["escapeScenes"]}; ph = c.get("phase") or m.get("overview", {})
G = {g["id"]: g for g in m["games"]}
def mx(g): return max(x for x in g["scores"] if x is not None)
def mn(g): return min(x for x in g["scores"] if x is not None)
losses = [g for g in m["games"] if g["result"] == "負け"]; wins = [g for g in m["games"] if g["result"] == "勝ち"]
la = sorted([g for g in losses if mx(g) >= 300], key=lambda g: -mx(g)); wb = sorted([g for g in wins if mn(g) <= -300], key=lambda g: mn(g))
sente = [g for g in m["games"] if g["side"] == "先手"]; gote = [g for g in m["games"] if g["side"] == "後手"]
sw = sum(g["result"] == "勝ち" for g in sente); gw = sum(g["result"] == "勝ち" for g in gote)
reps_by_game = {}
for r in c["reps"]: reps_by_game.setdefault(r["gameNo"], []).append(r)


import re as _re
# STEP ENDING_CLOCK(docs/STEP_ENDING_CLOCK_PLAN_2026-09-27.md §4 の 7)。
# 判定は `lib/reportData.ts` の `buildTimeUpLosses` が唯一の出所(ここでは判定を作り直さない ― 判定を 2 つにしない)。
# `time_up_by_game`: 本人が時間で負けたと判定された局(gameNo → { via: "word" | "clock", … })。
# `loss_used_sec_by_game`・`time_limit_sec`: 併記(§3 の (3))専用。判定はしない、数だけ。
_time_data = m.get("time") or {}
time_up_by_game = {t["gameNo"]: t for t in (_time_data.get("timeUpLosses") or [])}
loss_used_sec_by_game = {r["gameNo"]: r["usedSec"] for r in (_time_data.get("lossUsedSecs") or [])}
time_limit_sec = _time_data.get("timeLimitSec")
# ---- 局ごとの材料 ----
def game_facts(g):
    off = 1 if g["side"] == "後手" else 0
    pts = [(p + off, sc) for p, sc in zip(g["plies"], g["scores"]) if sc is not None]
    def rank(v): return "ahead" if v >= 300 else ("behind" if v <= -300 else "level")
    trans = []; cur = "level"
    for p, v in pts:
        r = rank(v)
        if r != cur: trans.append((p, cur, r)); cur = r
    mxp, mxv = max(pts, key=lambda x: x[1]); mnp, mnv = min(pts, key=lambda x: x[1])
    ever_ahead = mxv >= 300; ever_behind = mnv <= -300
    final = pts[-1][1]
    drop_after_max = next((p for p, v in pts if p > mxp and v < 300), None) if ever_ahead else None
    recover = next((p for p, v in pts if p > mnp and v > -300), None) if ever_behind else None
    def phase(p): return "序盤" if p / g["total"] < 1 / 3 else ("中盤" if p / g["total"] < 2 / 3 else "終盤")
    # STEP ENDING_CLOCK §3 の (1)・(1b)。`time_loss` は `lib/reportData.ts` の `isTimeUpLoss`(語 `切れ負け` に加え、
    # 語が `投了` でも時計〈累計消費時間 = 持ち時間〉が一致すれば真)の結果をそのまま読む(ここで判定を作り直さない)。
    # `via` は「どちらで分かったか」("word" = 棋譜の語 / "clock" = 時計)。
    time_up_info = time_up_by_game.get(g["no"])
    time_loss = time_up_info is not None
    via = time_up_info["via"] if time_up_info is not None else None
    used_sec = loss_used_sec_by_game.get(g["no"])
    # STEP FILL 作業 Y(H4-2、独立監査 REVISE 2026-09-22 の直し)。「切れ負けでない」だけでは、詰み・反則負け・
    # 終局の記録なしの負けも「投了で終わった」と断定してしまう(誤った断定)。実際の終局の語(ending)が
    # 「投了」であることを見て判定する(g.get("ending") はレポート道具が持つ唯一の終局の事実。lib/kifuImport.ts
    # の ENDING_KIF_WORDS の日本語語をそのまま比べる ― 新しい語を作らない)。
    ending_word = g.get("ending") or ""
    # STEP ENDING_CLOCK §4 の 9(計画の直し、904d317)。時計で分かった局(via == "clock")は resigned_ahead から外す
    # ― 外さないと time_loss と resigned_ahead の両方に数えられ、_mid.py:52 の 3 分割の assert が将来破綻する
    # (新しい閾値ではなく、既存の 3 分割を排他に保つだけ)。
    resigned_ahead = ending_word == "投了" and final >= 300 and via != "clock"
    if g["result"] == "負け":
        # STEP ENDING_CLOCK §4 の 8。時計で分かった局(via == "clock")は「持ち時間切れ」と断定しない。
        if time_loss and final >= 300 and via == "clock": title = "盤上は優勢のまま、時計上、持ち時間に到達して負けた将棋"
        elif time_loss and final >= 300: title = "盤上は優勢のまま、持ち時間切れで負けた将棋"
        # 「持ち時間切れ」の次、「途中で崩れた」の前に置く。投了でない「切れ負けでない・+300 以上」の負け
        # (詰み・反則負け・終局の記録なし等)は、この分岐に入れず、直しの前と同じ ever_ahead の分岐へ流す。
        elif resigned_ahead: title = "盤上は優勢のまま、投了で終わった将棋"
        elif ever_ahead: title = f"一度は良くなったが、{phase(drop_after_max or mxp)}に崩れた将棋"
        else: title = "途中で良くなる場面がないまま負けた将棋"
    else:
        # 劣勢(−300 以下)になってから一度も −300 より上に戻らないまま勝った局は recover が None で、戻した手目が無い。
        # recover が None なら最後の評価は必ず −300 以下(最小の後の点がすべて −300 以下)なので「盤上は劣勢のまま」は事実。
        # 言い方は負け側(「盤上は優勢のまま、持ち時間切れで負けた将棋」「盤上は優勢のまま、投了で終わった将棋」)の鏡写し。
        if ever_behind and recover is None:
            if "切れ負け" in ending_word: title = "盤上は劣勢のまま、持ち時間切れで勝った将棋"
            elif ending_word == "投了": title = "盤上は劣勢のまま、投了で終わった将棋"
            else: title = "一度は悪くなったが、戻せないまま勝った将棋"
        elif ever_behind: title = f"一度は悪くなったが、{recover} 手目に戻して勝った将棋"
        else: title = "形勢を落とさずに勝った将棋"
    return dict(off=off, pts=pts, trans=trans, mxp=mxp, mxv=mxv, mnp=mnp, mnv=mnv, ever_ahead=ever_ahead, ever_behind=ever_behind, final=final, drop=drop_after_max, recover=recover, phase=phase, time_loss=time_loss, via=via, used_sec=used_sec, time_limit_sec=time_limit_sec, resigned_ahead=resigned_ahead, title=title)
F = {g["no"]: game_facts(g) for g in m["games"]}
n_never_ahead_loss = sum(1 for g in losses if not F[g["no"]]["ever_ahead"]); n_never_behind_win = sum(1 for g in wins if not F[g["no"]]["ever_behind"]); n_time = sum(1 for g in losses if F[g["no"]]["time_loss"])
RANK_JP = {"ahead": "優勢", "level": "互角", "behind": "劣勢"}
def trans_text(p, frm, to):
    if to == "ahead": return f"{p} 手目に優勢になる(+300 以上)"
    if to == "behind": return f"{p} 手目に劣勢になる(−300 以下)"
    return f"{p} 手目に互角に{'戻る' if frm == 'ahead' else '戻す'}"
def narrative(g, f):
    # 形勢の段(優勢・互角・劣勢)が変わった手を時系列で並べる。多いときは最初と最後を残し、最大・最小は必ず書く
    phr = []
    for p, frm, to in f["trans"]:
        if to == "ahead": phr.append(f"{p} 手目に評価が +300 を超えて優勢になり")
        elif to == "behind": phr.append(f"{p} 手目に −300 を下回って劣勢になり")
        else: phr.append(f"{p} 手目に互角に{'戻り' if frm == 'ahead' else '戻し'}")
    if not phr: text = "評価は最後まで互角の範囲(−300 から +300)にとどまり"
    elif len(phr) <= 6: text = "、".join(phr)
    else: text = "、".join(phr[:3]) + "、(途中の上下を省略)、" + "、".join(phr[-3:])
    # STEP ENDING_CLOCK §3 の (1b)。時計で分かった局(via == "clock")は、棋譜の語で分かった局と同じ言い方(断定)を
    # 使わない ―「持ち時間切れとなりました」は語 `切れ負け` があるときだけ(via == "word")。
    if f["time_loss"] and f["via"] == "clock":
        text += f"、{g['total']} 手で、時計上、持ち時間に到達しました(最後の評価は {fmt(f['final'])})。"
    elif f["time_loss"]:
        text += f"、{g['total']} 手で持ち時間切れとなりました(最後の評価は {fmt(f['final'])})。"
    elif g["result"] == "負け" and f["resigned_ahead"] and f["used_sec"] is not None and f["time_limit_sec"] is not None:
        # STEP ENDING_CLOCK §3 の (3)。判定はしない(via は付けない)。数を置くだけ(人間の決定、2026-09-27)。
        text += f"、{g['total']} 手で{g.get('ending') or '終局'}、{g['result']}となりました。本人の累計消費時間は {f['used_sec']} 秒(持ち時間は {f['time_limit_sec']} 秒)。"
    else:
        text += f"、{g['total']} 手で{g.get('ending') or '終局'}、{g['result']}となりました。"
    extra = []
    if f["ever_ahead"]: extra.append(f"最も良かったのは {f['mxp']} 手目の {fmt(f['mxv'])}")
    if f["ever_behind"]: extra.append(f"最も悪かったのは {f['mnp']} 手目の {fmt(f['mnv'])}")
    if extra: text += "、".join(extra) + "です。"
    return text
def lesson(g, f, reps):
    # STEP FILL 作業 Y(H4-3)。このファイル内では呼び出し元が無い(render_main.py・render_appendix.py のどちらの
    # 連結先からも参照されない ― 出力に影響しない死んだコード)。固定の「20」だけ、ほかの箇所と揃えて s['games'] にした。
    if g["result"] == "負け":
        if f["time_loss"] and f["final"] >= 300 and f["via"] == "clock": t = f"この対局は盤上では{m['person']}が良い形勢のまま、時計上、持ち時間に到達して負けています。{s['games']} 局のうち、時間切れの負けは {n_time} 局です。"
        elif f["time_loss"] and f["final"] >= 300: t = f"この対局は盤上では{m['person']}が良い形勢のまま、持ち時間切れで負けています。{s['games']} 局のうち、時間切れの負けは {n_time} 局です。"
        elif f["ever_ahead"]: t = f"この対局は、最初から悪かったわけではありません。一度は優勢になっています。その後、{f['phase'](f['drop'] or f['mxp'])}に形勢が大きく動き、優勢を保てないまま負けています。{s['games']} 局全体でも、同じように「良くなってから崩れた」負けが {len(la)} 局あります。"
        else: t = f"この対局では、途中で優勢になる場面がありませんでした。{s['games']} 局のうち、良くならないまま負けた局は {n_never_ahead_loss} 局で、多くはありません。"
    else:
        if f["ever_behind"]: t = f"この対局は、一度 {fmt(f['mnv'])} まで悪くなってから、{f['recover']} 手目に戻して勝っています。{s['games']} 局のうち、同じように悪くなってから勝った局は {len(wb)} 局あります。"
        else: t = f"この対局は、評価が −300 を下回る場面がないまま勝っています。{s['games']} 局のうち、同じ勝ち方は {n_never_behind_win} 局です。"
    t += f" この一局だけから「{m['person']}の決まった特徴」とは判断しません。"
    return t
def esc_from_cf(cf, key):
    try:
        for ln in cf[key]:
            mm = _re.search(r"逃げ道 (\d+)", ln)
            if mm: return mm.group(1)
    except Exception: pass
    return None


# STEP FILL 作業 Y(H4-2、独立監査 REVISE 2026-09-22 の直し)。la(途中まで優勢だった負け)を 3 つに分ける:
# 持ち時間切れ(n_time_ahead、_mid.py で計算)、優勢のまま投了(n_la_resigned_ahead。上の title の resigned_ahead と
# 同じ条件 ― ending が「投了」であることを見る)、それ以外の「崩れた」(n_la_collapsed。詰み・反則負け・
# 終局の記録なしで +300 以上のまま負けた局や、投了だが最後の評価が +300 未満まで下がった局を含む)。
n_la_resigned_ahead = sum(1 for g in la if F[g["no"]]["resigned_ahead"])
n_la_collapsed = sum(1 for g in la if not F[g["no"]]["time_loss"] and not F[g["no"]]["resigned_ahead"])
