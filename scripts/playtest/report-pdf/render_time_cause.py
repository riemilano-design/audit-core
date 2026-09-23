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

# STEP TIME-CAUSE-2(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §7.5)。--search <time_cause_search.json> は
# 任意(渡さなければ「探索の結果」のページは作らない ― render_front.py の第 3 引数と同じ流儀)。
_args = sys.argv[1:]
SEARCH_PATH = None
if "--search" in _args:
    _idx = _args.index("--search")
    if _idx + 1 >= len(_args):
        sys.exit("--search には値が要る")
    SEARCH_PATH = _args[_idx + 1]
    del _args[_idx : _idx + 2]

if len(_args) < 2:
    sys.exit("使い方: python3 -X utf8 render_time_cause.py <time_cause.json> <出力 PDF> [--search <time_cause_search.json>]")
src, out = _args[0], _args[1]
TC = json.load(open(src, encoding="utf-8"))
TS = json.load(open(SEARCH_PATH, encoding="utf-8")) if SEARCH_PATH is not None else None

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

# render_whatif.py の BANNED と同じ 15 語に、STEP TIME-CAUSE-3(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §9.1
# の 6.)の指示で「型」「クセ」「パターン」を足した(render_front.py の BANNED と同じ 18 語)。この付録は
# A/B/C の分類結果を書くため、「型」を書いてしまう誤りを機械でも止める(実装担当の判断)。
BANNED = [
    "悪手",
    "弱点",
    "癖",
    "型",
    "傾向",
    "原因",
    "ミス",
    "見落とし",
    "改善",
    "練習",
    "必ず",
    "明らか",
    "あなた",
    "ご自身",
    "いつも",
    "がち",
    "クセ",
    "パターン",
]

doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title="対局後診断・付録 4(時間の使い方)", author="将棋コーチ(試作)")
W = A4[0] - 28 * mm
story = []

# ==================== 数の照合・禁止語(render_direct.py の emit と同じ考え方) ====================
# 3 は「3 分」、10 は「10 分」の固定の語彙として常に許可する(render_direct.py の GLOBAL_ALLOWED_NUMBERS と
# 同じ考え方 ― 個々の事実ではなく、この付録の作り方そのものを表す数)。300 は「崩れ」の境(STANDING_BOUNDS.
# aheadCp。render_front.py の GLOBAL_ALLOWED_NUMBERS と同じ)。
GLOBAL_ALLOWED_NUMBERS = {1, 2, 3, 4, 5, 9, 10, 300}
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

# ==================== 探索の結果(STEP TIME-CAUSE-2。--search が渡されたときだけ) ====================
# lib/timeSearch.ts が数えた条件の組(単独・2・3 条件)を、そのまま並べる(判定・集計はしない)。
COLUMN_LABELS = {
    "prevOwnSpentBucket": "直前の自分の手の秒",
    "prev3SumBucket": "直前 3 手の合計秒",
    "prev5SumBucket": "直前 5 手の合計秒",
    "afterLongThink": "直前の自分の手が長考",
    "remainingBucket": "残り時間",
    "phase": "時期",
    "evalBand": "形勢",
    "evalChangePrev": "直前の自分の手番からの形勢の変化",
    "inCheck": "王手を受けている",
    "fork": "分かれ道",
    "top1Side": "第 1 候補の側",
    "actualSide": "実戦の手の側",
    "lossBand": "損失の大きさ",
    "inTop5": "実戦の手が候補内",
    "actualCapture": "実戦の手が取る",
    "actualDrop": "実戦の手が打つ",
    "actualGivesCheck": "実戦の手が王手",
    "actualSacrifice": "実戦の手が捨て駒",
    "actualRetreat": "実戦の手が引く",
    "top1Capture": "第 1 候補が取る",
    "top1Drop": "第 1 候補が打つ",
    "top1GivesCheck": "第 1 候補が王手",
    "top1Sacrifice": "第 1 候補が捨て駒",
    "top1Retreat": "第 1 候補が引く",
    "oppPrevCapture": "相手の直前の手が取る",
    "oppPrevDrop": "相手の直前の手が打つ",
    "oppPrevGivesCheck": "相手の直前の手が王手",
    "oppPrevPromotion": "相手の直前の手が成る",
    "ownRookMoved": "本人の飛車が動いた",
    "oppRookMoved": "相手の飛車が動いた",
}
VALUE_LABELS = {
    "phase": {"early": "序盤", "mid": "中盤", "late": "終盤"},
    "evalBand": {"ahead": "優勢", "level": "互角", "behind": "劣勢"},
    "evalChangePrev": {"up": "上", "same": "同", "down": "下"},
    "top1Side": {"attack": "攻め", "defense": "守り", "both": "両方", "none": "なし"},
    "actualSide": {"attack": "攻め", "defense": "守り", "both": "両方", "none": "なし"},
    "lossBand": {"over300": "300 以上", "under300": "300 未満", "outOfCandidates": "候補外"},
    "remainingBucket": {"<60": "60 秒未満", "60-119": "60〜119 秒", ">=120": "120 秒以上"},
}


def value_text(column, value):
    by_column = VALUE_LABELS.get(column)
    if by_column is not None and value in by_column:
        return by_column[value]
    if isinstance(value, bool):
        return yn(value)
    return str(value)


def condition_text(condition):
    return "・".join(f"{COLUMN_LABELS.get(t['column'], t['column'])}: {value_text(t['column'], t['value'])}" for t in condition)


def cond_stats_text(stats):
    p_pct = round(stats["p"] * 100, 1)
    return f"{stats['longThink']} / {stats['n']}({p_pct:g}%)"


# STEP TIME-CAUSE-3(計画 §9.1 の 6.)。崩れ(q)の分数。分母 0(collapseCounted=0)なら「—」。
def cond_collapse_text(stats):
    if stats["collapseCounted"] == 0:
        return "—"
    q_pct = round(stats["q"] * 100, 1)
    return f"{stats['collapsed']} / {stats['collapseCounted']}({q_pct:g}%)"


# 偶然でも残る数の目安(小数第 1 位まで)。
def chance_text(x):
    return f"{round(x, 1):g}"


# 「関係」の欄は 3 語だけ(2026-09-25 の人間の修正。「強い」「弱い」「型」は使わない)。
EXPLAIN_LABELS = {"single": "単独で再現", "combo": "組で再現", None: "―"}


def explain_text(level):
    return EXPLAIN_LABELS.get(level, "―")


def factor_condition_text(f):
    return condition_text([{"column": f["column"], "value": f["value"]}])


if TS is not None:
    story.append(PageBreak())
    story.append(P("時間と一緒に起きている条件(探索)", S_H2))
    story.append(
        P(
            emit(
                f"発見用(手 <b>{TS['discover']['moves']}</b>)で単独・2 条件・3 条件の組を機械に全部試させ、採用候補(手の数が十分に多く、長考の"
                f"割合が全体よりはっきり高い組)を選びました。検証用(手 <b>{TS['validate']['moves']}</b>)でも同じ組を数え直し、当てはまる状態が"
                f"保たれた組だけを「再現した」とします。同じやり方を「崩れ」(このあと形勢の区分が下がること)にも当て、長考と崩れの両方を"
                f"一緒に説明する条件・崩れだけを説明する条件を分けます。ここに並ぶのは長考・崩れと一緒に起きている条件を数えたものであり、"
                f"何かを決めつけるものではありません。",
                {TS["discover"]["moves"], TS["validate"]["moves"]},
            ),
            S_LEAD,
        )
    )
    story.append(
        notebox(
            [
                "「崩れ」は、直前の評価の区分(優勢・互角・劣勢)が優勢または互角だった局面から、次の自分の手番の直前に区分が 1 段以上"
                "下がったことです。+300 以上を優勢、−300 以下を劣勢、その間を互角とします。",
            ]
        )
    )
    story.append(Spacer(1, 2 * mm))

    def depth_table_of(depths):
        rows = [[P(x, S_K) for x in ["深さ(条件の数)", "試した組の数", "採用候補の数", "再現の数", "偶然の目安"]]]
        allowed = set()
        for d in depths:
            chance_str = chance_text(d["chanceReproduced"])
            allowed |= {d["depth"], d["tried"], d["adopted"], d["reproduced"]} | digits_of(chance_str)
            rows.append(
                [
                    P(emit(f"{d['depth']} 条件", allowed), S_V),
                    P(emit(str(d["tried"]), allowed), S_V),
                    P(emit(str(d["adopted"]), allowed), S_V),
                    P(emit(str(d["reproduced"]), allowed), S_V),
                    P(emit(chance_str, allowed), S_V),
                ]
            )
        t = Table(rows, colWidths=[30 * mm, (W - 30 * mm) / 4, (W - 30 * mm) / 4, (W - 30 * mm) / 4, (W - 30 * mm) / 4], repeatRows=1)
        t.setStyle(HEADER_STYLE)
        return t

    story.append(P("深さごとの表(長考と一緒に起きている条件)", S_K))
    story.append(depth_table_of(TS["depths"]))
    story.append(Spacer(1, 2.5 * mm))
    story.append(P("深さごとの表(崩れと一緒に起きている条件)", S_K))
    story.append(depth_table_of(TS["collapseSearch"]["depths"]))
    story.append(Spacer(1, 2 * mm))
    story.append(
        notebox(
            [
                "偶然の目安は、長考(または崩れ)と関係の無い条件でも、この深さの採用候補と同じ数だけ試せば偶然で再現してしまう組の数です"
                "(二項分布の裾から計算します)。再現の数がこの目安に近いほど、偶然と見分けにくいということです。",
                "深さは組み合わせた条件の数です(1 = 単独の条件、2・3 = 条件を組み合わせたもの)。",
            ]
        )
    )
    story.append(Spacer(1, 2 * mm))

    story.append(P("共通因子の表(部品ごとに、どのアウトカムを説明する部品かを分類。上位 15)", S_H3))
    story.append(
        P(
            "「よく登場する部品」を答えにはしません。部品(単独の条件)ごとに、単独で線を越えるか、組み合わせでだけ再現した組に"
            "入るかを分けます。「―」はどちらでもありません。",
            S_BODY,
        )
    )
    story.append(Spacer(1, 1.5 * mm))
    factor_rows = [[P(x, S_K) for x in ["条件", "長考との関係", "時間と崩れとの関係", "速く指して崩れとの関係", "発見 → 検証(長考)"]]]
    for f in TS["factors"][:15]:
        cond_text = factor_condition_text(f)
        disc_text = cond_stats_text(f["single"]["discover"])
        val_text = cond_stats_text(f["single"]["validate"])
        trans_text = f"{disc_text} → {val_text}"
        row_allowed = digits_of(cond_text) | digits_of(trans_text)
        factor_rows.append(
            [
                P(emit(cond_text, row_allowed), S_V),
                P(explain_text(f["explains"]["longThink"]), S_V),
                P(explain_text(f["explains"]["timeAndCollapse"]), S_V),
                P(explain_text(f["explains"]["quickCollapse"]), S_V),
                P(emit(trans_text, row_allowed), S_V),
            ]
        )
    factor_col = (W - 55 * mm) / 4
    factor_table = Table(factor_rows, colWidths=[55 * mm, factor_col, factor_col, factor_col, factor_col], repeatRows=1)
    factor_table.setStyle(HEADER_STYLE)
    story.append(factor_table)
    story.append(Spacer(1, 2.5 * mm))

    def kind_list_of(label, entries, cap=None):
        story.append(P(label, S_H3))
        shown = entries if cap is None else entries[:cap]
        if len(shown) == 0:
            story.append(P("0 件でした。", S_SMALL))
            return
        rows = [[P(x, S_K) for x in ["条件", "発見用の長考", "検証用の長考", "発見用の崩れ", "検証用の崩れ"]]]
        for r in shown:
            cond_text = condition_text(r["condition"])
            disc_time = cond_stats_text(r["discover"])
            val_time = cond_stats_text(r["validate"])
            disc_collapse = cond_collapse_text(r["discover"])
            val_collapse = cond_collapse_text(r["validate"])
            row_allowed = digits_of(cond_text) | digits_of(disc_time) | digits_of(val_time) | digits_of(disc_collapse) | digits_of(val_collapse)
            rows.append(
                [
                    P(emit(cond_text, row_allowed), S_V),
                    P(emit(disc_time, row_allowed), S_V),
                    P(emit(val_time, row_allowed), S_V),
                    P(emit(disc_collapse, row_allowed), S_V),
                    P(emit(val_collapse, row_allowed), S_V),
                ]
            )
        col = (W - 55 * mm) / 4
        t = Table(rows, colWidths=[55 * mm, col, col, col, col], repeatRows=1)
        t.setStyle(HEADER_STYLE)
        story.append(t)
        story.append(Spacer(1, 2.5 * mm))

    time_and_collapse = [r for r in TS["reproduced"] if r["kind"] == "B"]
    kind_list_of("時間と崩れの両方を説明する条件(発見用・検証用とも再現)", time_and_collapse)

    quick_collapse = [r for r in TS["collapseSearch"]["reproduced"] if r["kind"] == "C"]
    kind_list_of("速く指した手が崩れと一緒に起きている条件(上位 10)", quick_collapse, cap=10)

    story.append(
        notebox(
            [
                "この表は条件どうしの一緒の起き方を数えたものであり、どれが理由かを決めるものではありません。",
                "「時間と崩れの両方を説明する条件」は、長考の探索と崩れの探索の両方で再現した条件です。「速く指した手が崩れと一緒に"
                "起きている条件」は、長考の採用候補にはならなかったが、崩れの探索では再現した条件です。",
            ]
        )
    )

story.append(Spacer(1, 3 * mm))
story.append(P("試作版につき、有段者による確認はまだ受けていません。数はすべて機械で数えたものです。", st("tfoot", fontSize=8, leading=11, color=MUTED)))

if _problems:
    print("\n".join(_problems), file=sys.stderr)
    sys.exit(1)

doc.build(story)
search_note = "" if TS is None else f"・探索の再現 {sum(d['reproduced'] for d in TS['depths'])} 組"
print(f"wrote {out}({len(games)} 局・{len(groups)} 組・{len(time_up_games)} 局の帯{search_note})")
