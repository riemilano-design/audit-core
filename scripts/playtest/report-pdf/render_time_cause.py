# -*- coding: utf-8 -*-
# STEP TIME-CAUSE(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §2・§3)。付録 4「時間の使い方」の PDF を作る道具。
# `scripts/playtest/timeCause.ts` が作る `time_cause.json` を描くだけ(判定・集計は TypeScript 側
# 〈lib/timeCause.ts〉がすでに済ませている。この道具は数を並べるだけで、新しい判定はしない)。
#
# 使い方: python3 -X utf8 render_time_cause.py <time_cause.json> <出力 PDF>
#
# 【この新規ファイルが再利用する「流儀」(既存の 6 本(_head/_util/_mid/_app_head/_app/_tail)は変えない)】
# - 書体の探し方・埋め込み(`render_front.py`・`render_direct.py` と同じ)
# - 段落・表の組み方(reportlab の Paragraph/Table)、数の照合・禁止語(`render_whatif.py` の `BANNED` と
#   文字どおり同じ 15 語)の確かめ方は `render_direct.py` の `emit()` と同じ考え方
#
# 【この道具が絶対にやらないこと】将棋の判断・戦法の名前・「原因」「傾向」の語(禁止語。見出しは「時間の使い方」
# 「要因の候補」)。断定する言い回し(「〜が原因です」等)。数の再計算(すべて `time_cause.json` の値をそのまま描く)。
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
from reportlab.platypus import Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

if len(sys.argv) < 3:
    sys.exit("使い方: python3 -X utf8 render_time_cause.py <time_cause.json> <出力 PDF>")
src, out = sys.argv[1], sys.argv[2]
TC = json.load(open(src, encoding="utf-8"))

# ---- 書体(render_direct.py・render_front.py と同じ流儀) ----
_here = os.path.dirname(os.path.abspath(__file__))
_cands = [os.path.join(_here, "fonts", "IPAexfont00401", "ipaexg.ttf"), "/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"]
_font = next((p for p in _cands if os.path.exists(p)), None)
if _font is None:
    sys.exit("埋め込める日本語フォントが無い(埋め込まない PDF は読む側で文字が欠けるので作らない)")
pdfmetrics.registerFont(TTFont("JPEmbedded", _font))
FONT = FONT_B = "JPEmbedded"

INK = colors.HexColor("#1e2a32")
MUTED = colors.HexColor("#5a6a74")
ACCENT = colors.HexColor("#2d6a8a")
RED = colors.HexColor("#c9473f")
LINE = colors.HexColor("#d5dde2")
BG = colors.HexColor("#f4f7f9")
BAR = colors.HexColor("#2d6a8a")
BAR_FORK = colors.HexColor("#c9473f")

st = lambda name, **kw: ParagraphStyle(name, fontName=kw.pop("font", FONT), textColor=kw.pop("color", INK), leading=kw.pop("leading", 15), wordWrap="CJK", alignment=TA_LEFT, **kw)
NB = " "


def P(text, style):
    parts = re.split(r"(<[^>]*>)", text)
    return Paragraph("".join(pt if pt.startswith("<") else pt.replace(" ", NB) for pt in parts), style)


S_TITLE = st("ttitle", font=FONT_B, fontSize=18, leading=23, spaceAfter=2 * mm)
S_LEAD = st("tlead", fontSize=10.2, leading=15, color=MUTED, spaceAfter=3 * mm)
S_H2 = st("th2", font=FONT_B, fontSize=12.5, leading=17, color=ACCENT, spaceBefore=4 * mm, spaceAfter=1.5 * mm)
S_H3 = st("th3", font=FONT_B, fontSize=11, leading=14, color=ACCENT, spaceBefore=3 * mm, spaceAfter=1.2 * mm)
S_BODY = st("tbody", fontSize=10, leading=14.5)
S_SMALL = st("tsmall", fontSize=8.2, leading=11.5, color=MUTED)
S_K = st("tk", fontSize=9.5, leading=13, color=MUTED)
S_V = st("tv", fontSize=8.6, leading=12)
S_EYEBROW = st("teyebrow", fontSize=8.2, leading=11, color=ACCENT)

# render_whatif.py の BANNED と文字どおり同じ 15 語(このファイルの固定文にも使わない)。
BANNED = ["悪手", "弱点", "癖", "傾向", "原因", "ミス", "見落とし", "改善", "練習", "必ず", "明らか", "あなた", "ご自身", "いつも", "がち"]

doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title="対局後診断・付録 4(時間の使い方)", author="将棋コーチ(試作)")
W = A4[0] - 28 * mm
story = []

# ==================== 数の照合・禁止語(render_direct.py の emit と同じ考え方) ====================
# 3 は「3 分」、10 は「10 分」の固定の語彙として常に許可する(render_direct.py の GLOBAL_ALLOWED_NUMBERS と
# 同じ考え方 ― 個々の事実ではなく、この付録の作り方そのものを表す数)。
GLOBAL_ALLOWED_NUMBERS = {1, 2, 3, 4, 5, 9, 10}
_problems = []


def emit(text, allowed):
    plain = re.sub(r"<[^>]*>", "", text)
    allowed_all = allowed | GLOBAL_ALLOWED_NUMBERS
    for token in re.findall(r"[0-9]+", plain):
        n = int(token)
        if n not in allowed_all:
            _problems.append(f"データに無い数 {n} が文に出ている: {text[:60]}…")
    for w in BANNED:
        if w in text:
            _problems.append(f"使わない語「{w}」: {text[:60]}…")
    return text


def num(n):
    return "—" if n is None else str(n)


def sec_text(n):
    if n is None:
        return "—"
    return f"{round(n, 1):g} 秒"


def digits_of(text):
    """文字列に出る数字の並びをすべて整数として取り出す(`emit()` の許す集合を作るための道具。
    `round(x, 1)` で表示する小数〈例: 11.5〉は正規表現 `[0-9]+` で「11」「5」に割れるため、
    表示に使う文字列そのものから許す数を作る ― 別に丸め方を再実装しない)。"""
    return {int(t) for t in re.findall(r"[0-9]+", text)}


def mark_text(b):
    if b is None:
        return "—"
    return "そのまま" if b else "動いた"


def yn(b):
    return "はい" if b else "いいえ"


HEADER_STYLE = TableStyle(
    [
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
        ("BACKGROUND", (0, 0), (-1, 0), BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0.9 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0.9 * mm),
    ]
)


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


# ==================== 1 ページ目(局ごとの表) ====================
games = TC["games"]
groups = TC["groups"]

allowed_p1 = {len(games), len(groups)}
for g in groups:
    allowed_p1.add(g["timeLimitSec"])

story.append(P("対局後診断・付録 4(試作)", S_EYEBROW))
story.append(P("時間の使い方", S_TITLE))
story.append(
    P(
        emit(
            f"時間切れで負けたことに、機械で数えられる材料からどんな要因の候補が見つかるかを並べます。全 <b>{len(games)}</b> 局"
            f"(組は <b>{len(groups)}</b> つ)について、序盤・中盤・終盤の消費秒、長考(10 秒以上)の回数・最長の 1 手・連続、"
            f"中考(5〜9 秒)の回数、本人・相手の飛車が初期の筋のままかを並べます。",
            allowed_p1,
        ),
        S_LEAD,
    )
)

# kifuId を持たせる理由(実装担当の判断): --time-limit-sec が同じ複数の --kifu-dir(例: tatsunami20・tatsunami3
# の両方が 180 秒 = 「3 分」)を 1 つの組に合算すると、局番号(gameNo)は元の --patient ごとに 1 から始まるため、
# 同じ組・同じ局番号が別の対局を指すことがある(下の表で実際に起きる)。kifuId で一意に見分けられるようにする。
header = ["組", "局", "kifuId", "手数", "序", "中", "終", "長考", "最長", "連続", "中考", "飛車(本人)", "飛車(相手)", "時間切れ"]
rows = [[P(x, S_K) for x in header]]
for g in games:
    row_allowed = {
        g["gameNo"],
        g["total"],
        g["phaseSpentSec"]["early"],
        g["phaseSpentSec"]["mid"],
        g["phaseSpentSec"]["late"],
        g["longThinkTotal"],
        g["longThinkStreakCount"],
        g["midThinkTotal"]["count"],
    }
    if g["longestMove"] is not None:
        row_allowed.add(g["longestMove"]["sec"])
        row_allowed.add(g["longestMove"]["kifPly"])
    longest_text = "—" if g["longestMove"] is None else f"{g['longestMove']['sec']}秒({g['longestMove']['kifPly']}手目)"
    rows.append(
        [
            P(g["group"], S_V),
            P(emit(str(g["gameNo"]), row_allowed), S_V),
            P(g["kifuId"], S_V),
            P(emit(str(g["total"]), row_allowed), S_V),
            P(emit(str(g["phaseSpentSec"]["early"]), row_allowed), S_V),
            P(emit(str(g["phaseSpentSec"]["mid"]), row_allowed), S_V),
            P(emit(str(g["phaseSpentSec"]["late"]), row_allowed), S_V),
            P(emit(str(g["longThinkTotal"]), row_allowed), S_V),
            P(emit(longest_text, row_allowed), S_V),
            P(emit(str(g["longThinkStreakCount"]), row_allowed), S_V),
            P(emit(str(g["midThinkTotal"]["count"]), row_allowed), S_V),
            P(mark_text(g["rookMark"]["own"] if g["rookMark"] else None), S_V),
            P(mark_text(g["rookMark"]["opponent"] if g["rookMark"] else None), S_V),
            P(yn(g["timeUpLoss"]), S_V),
        ]
    )
col_widths = [11 * mm, 8 * mm, 14 * mm, 11 * mm, 9 * mm, 9 * mm, 9 * mm, 10 * mm, 20 * mm, 10 * mm, 10 * mm, 17 * mm, 17 * mm, 15 * mm]
if sum(col_widths) > W:
    scale = W / sum(col_widths)
    col_widths = [w * scale for w in col_widths]
table1 = Table(rows, colWidths=col_widths, repeatRows=1)
table1.setStyle(HEADER_STYLE)
story.append(table1)
story.append(Spacer(1, 2.5 * mm))
story.append(P("この付録の読み方", S_K))
story.append(
    notebox(
        [
            "序・中・終は本人の手だけの消費秒の合計です(序盤・中盤・終盤は対局の総手数の 3 分の 1 ずつ)。",
            "長考は 10 秒以上、中考は 5〜9 秒の本人の手の回数です。連続は、間に他の手を挟まない本人の 2 手が"
            "ともに長考だった回数です。",
            "飛車(本人)/飛車(相手)は、序盤の終わり(中盤に入る最初の本人の手の直前)の局面で、飛車が初期の筋"
            "(先手 2 筋・後手 8 筋)のままかどうかです。「—」は該当する局面が無かった対局です。",
            "この表・次のページの数はすべて機械で数えたものであり、良し悪しの判定ではありません。",
        ]
    )
)
story.append(PageBreak())

# ==================== 2 ページ目以降(組ごとの集計) ====================
story.append(P("要因の候補", S_H2))
story.append(P("時間切れで負けた対局と、それ以外の対局を組ごとに分けて並べます。", S_BODY))
story.append(Spacer(1, 1.5 * mm))

CAND_LABELS = [
    ("medianEarlySec", "序盤の消費(秒)の中央値", sec_text),
    ("medianMidSec", "中盤の消費(秒)の中央値", sec_text),
    ("medianLateSec", "終盤の消費(秒)の中央値", sec_text),
    ("medianLongThinkTotal", "長考(10 秒以上)の回数の中央値", num),
    ("medianLongestMoveSec", "最長の 1 手(秒)の中央値", sec_text),
    ("medianStreakCount", "長考の連続の回数の中央値", num),
    ("medianMidThinkCount", "中考(5〜9 秒)の回数の中央値", num),
    ("medianMidThinkSec", "中考の合計秒の中央値", sec_text),
]

for g in groups:
    story.append(P(f"{g['group']}の組({g['games']} 局)", S_H3))
    allowed_g = {g["timeLimitSec"], g["timeUpLoss"]["games"], g["other"]["games"]}

    cand_rows = [[P(x, S_K) for x in ["候補", "時間切れの局", "他の局"]]]
    for key, label, fmt in CAND_LABELS:
        up_text = fmt(g["timeUpLoss"][key])
        ot_text = fmt(g["other"][key])
        row_allowed = allowed_g | digits_of(up_text) | digits_of(ot_text)
        cand_rows.append([P(label, S_V), P(emit(up_text, row_allowed), S_V), P(emit(ot_text, row_allowed), S_V)])
    cand_table = Table(cand_rows, colWidths=[70 * mm, (W - 70 * mm) / 2, (W - 70 * mm) / 2], repeatRows=1)
    cand_table.setStyle(HEADER_STYLE)
    story.append(cand_table)
    story.append(Spacer(1, 2 * mm))

    def fraction_text(fr):
        if fr is None:
            return "(この組には whatif-v2 の記録がありません)"
        return f"{fr['numerator']} / {fr['denominator']}"

    for label, fr in (("時間切れの局", g["timeUpLoss"]), ("他の局", g["other"])):
        fork = fr["forkFraction"]
        opp = fr["oppositeSideFraction"]
        allowed_f = set(allowed_g)
        if fork is not None:
            allowed_f.add(fork["numerator"])
            allowed_f.add(fork["denominator"])
        if opp is not None:
            allowed_f.add(opp["numerator"])
            allowed_f.add(opp["denominator"])
        story.append(
            P(
                emit(f"{label}: 長考のうち分かれ道に当たった数 {fraction_text(fork)}、そのうち側が逆だった数 {fraction_text(opp)}", allowed_f),
                S_SMALL,
            )
        )
    story.append(Spacer(1, 2.5 * mm))

    story.append(P("飛車の筋(序盤の終わりの局面)", S_K))
    rook_rows = [[P(x, S_K) for x in ["本人", "相手", "局数", "序の中央値", "中の中央値"]]]
    for cell in g["rookMarkBreakdown"]:
        early_text = sec_text(cell["medianEarlySec"])
        mid_text = sec_text(cell["medianMidSec"])
        allowed_c = {cell["games"]} | digits_of(early_text) | digits_of(mid_text)
        rook_rows.append(
            [
                P(mark_text(cell["own"]), S_V),
                P(mark_text(cell["opponent"]), S_V),
                P(emit(str(cell["games"]), allowed_c), S_V),
                P(emit(early_text, allowed_c), S_V),
                P(emit(mid_text, allowed_c), S_V),
            ]
        )
    rook_table = Table(rook_rows, colWidths=[22 * mm, 22 * mm, 20 * mm, (W - 64 * mm) / 2, (W - 64 * mm) / 2], repeatRows=1)
    rook_table.setStyle(HEADER_STYLE)
    story.append(rook_table)
    story.append(Spacer(1, 2.5 * mm))

    story.append(P("局ごとの序・中の消費と、終局時の残り秒(相関の値は出しません。並べるだけです)", S_K))
    c10_rows = [[P(x, S_K) for x in ["局", "序", "中", "残り"]]]
    for row in g["c10Table"]:
        early_text = sec_text(row["earlySec"])
        mid_text = sec_text(row["midSec"])
        remaining_text = sec_text(row["remainingSec"])
        allowed_r = {row["gameNo"]} | digits_of(early_text) | digits_of(mid_text) | digits_of(remaining_text)
        c10_rows.append(
            [
                P(emit(str(row["gameNo"]), allowed_r), S_V),
                P(emit(early_text, allowed_r), S_V),
                P(emit(mid_text, allowed_r), S_V),
                P(emit(remaining_text, allowed_r), S_V),
            ]
        )
    c10_table = Table(c10_rows, colWidths=[15 * mm, (W - 15 * mm) / 3, (W - 15 * mm) / 3, (W - 15 * mm) / 3], repeatRows=1)
    c10_table.setStyle(HEADER_STYLE)
    story.append(c10_table)
    story.append(PageBreak())


# ==================== 帯(時間切れで負けた対局ごとの、中盤の手ごとの秒) ====================
class MidBars(Flowable):
    """中盤の本人の手ごとの秒を、手目を横軸にした縦棒で描く(計画 §3「中盤の手ごとの秒の横棒」)。
    分かれ道(fork: true)の手は棒の色を変えて印にする。fork が全部 null(whatif-v2 が無い組)なら
    色分けはしない(データに無い印を描かない)。"""

    # TIME_VALUES.longThinkSec(lib/reportData.ts)と同じ値。新しい閾値ではなく、既存の値を目盛りの参考線として使う。
    LONG_THINK_SEC = 10

    def __init__(self, moves, width=170 * mm, height=32 * mm):
        super().__init__()
        self.moves = moves
        self.width = width
        self.height = height

    def wrap(self, aw, ah):
        return self.width, self.height + 6 * mm

    def draw(self):
        c = self.canv
        w, h = self.width, self.height
        ox, oy = 0, 5 * mm
        if len(self.moves) == 0:
            return
        max_sec = max(1, max(m["sec"] for m in self.moves))
        n = len(self.moves)
        slot = w / n
        bar_w = min(slot * 0.6, 4 * mm)

        c.setStrokeColor(LINE)
        c.setLineWidth(0.4)
        c.line(ox, oy, ox + w, oy)

        # 長考(10 秒以上)の参考線
        if max_sec >= self.LONG_THINK_SEC:
            ref_y = oy + h * (self.LONG_THINK_SEC / max_sec)
            c.setDash(1.5, 1.5)
            c.setStrokeColor(MUTED)
            c.line(ox, ref_y, ox + w, ref_y)
            c.setDash()

        c.setFont(FONT, 6)
        for i, m in enumerate(self.moves):
            x = ox + i * slot + (slot - bar_w) / 2
            bh = h * (m["sec"] / max_sec)
            c.setFillColor(BAR_FORK if m.get("fork") else BAR)
            c.rect(x, oy, bar_w, bh, stroke=0, fill=1)
            if m.get("fork"):
                c.setFillColor(BAR_FORK)
                c.circle(x + bar_w / 2, oy + bh + 1.6 * mm, 0.6 * mm, stroke=0, fill=1)
            if i % max(1, n // 12) == 0 or i == n - 1:
                c.setFillColor(MUTED)
                c.drawCentredString(x + bar_w / 2, oy - 3 * mm, str(m["kifPly"]))


time_up_games = [g for g in games if g["timeUpLoss"]]
story.append(P("時間切れで負けた対局の、中盤の手ごとの秒", S_H2))
story.append(
    P(
        "横軸は手目、棒の高さがその手にかけた秒です。破線は 10 秒(長考の目安)の参考線です。"
        + ("丸い印が付いた棒は分かれ道に当たった手です。" if any(any(m.get("fork") for m in g["midMoveSeconds"]) for g in time_up_games) else ""),
        S_BODY,
    )
)
story.append(Spacer(1, 2 * mm))

if len(time_up_games) == 0:
    story.append(P("該当する対局はありませんでした。", S_SMALL))
else:
    for g in time_up_games:
        allowed_g = {g["gameNo"], g["total"]}  # 組のラベルの数(3 分・10 分)は GLOBAL_ALLOWED_NUMBERS 側で許可
        story.append(P(emit(f"{g['group']}の {g['gameNo']} 局目(kifuId: {g['kifuId']}・全 {g['total']} 手)", allowed_g), S_EYEBROW))
        if len(g["midMoveSeconds"]) == 0:
            story.append(P("中盤に秒の読めた本人の手がありませんでした。", S_SMALL))
        else:
            story.append(MidBars(g["midMoveSeconds"], width=W))
        story.append(Spacer(1, 4 * mm))

story.append(Spacer(1, 3 * mm))
story.append(P("試作版につき、有段者による確認はまだ受けていません。数はすべて機械で数えたものです。", st("tfoot", fontSize=8, leading=11, color=MUTED)))

if _problems:
    print("\n".join(_problems), file=sys.stderr)
    sys.exit(1)

doc.build(story)
print(f"wrote {out}({len(games)} 局・{len(groups)} 組・{len(time_up_games)} 局の帯)")
