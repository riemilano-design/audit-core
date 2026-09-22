# -*- coding: utf-8 -*-
# STEP TIME 作業 2(docs/STEP_TIME_PLAN_2026-09-22.md §6.4)。本編 4 ページを描く道具。
#
# 使い方: python3 -X utf8 render_front.py <patient_report_data.json> <出力 PDF>
#
# 【発見の判定はここではしない】
# 何を出すか(`findings[].shown`)・前回との比較(`previous`)は `lib/reportData.ts` の `buildFindings`・`buildPrevious`
# (TypeScript・試験できる側)がすでに決めている。この道具は、その結果(数・文)を 4 ページの PDF に描くだけ。
#
# 【この新規ファイルが再利用する「流儀」(既存の 6 本(_head.py・_util.py・_mid.py・_app_head.py・_app.py・_tail.py)は
# 変えない。_head.py は import せず、書体の探し方だけをこのファイルの中に書き写した)】
# - 書体の探し方・埋め込み(_head.py と同じ。この道具は sfens.json・prose.json を読まないので REPORT_DATA_DIR は使わない)
# - 段落・表の組み方(reportlab の Paragraph/Table)、数の照合・禁止語の確かめの考え方(_mid.py の allowed_numbers・BANNED
#   と同じ考え方。実装はこのファイルで完結する。render_whatif.py の emit() と同じ作り)
#
# 【この道具が絶対にやらないこと】将棋の判断・断定的な戦法名の表示・助言・予測の文。数の再計算(判定は TypeScript 側)。
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
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

if len(sys.argv) < 3:
    sys.exit("使い方: python3 -X utf8 render_front.py <patient_report_data.json> <出力 PDF>")
src, out = sys.argv[1], sys.argv[2]
m = json.load(open(src, encoding="utf-8"))

# ---- 書体(_head.py と同じ流儀。ヒラギノ系 CID → 無ければ埋め込みフォント) ----
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
LINE = colors.HexColor("#d5dde2")
BG = colors.HexColor("#f4f7f9")

st = lambda name, **kw: ParagraphStyle(name, fontName=kw.pop("font", FONT), textColor=kw.pop("color", INK), leading=kw.pop("leading", 15), wordWrap="CJK", alignment=TA_LEFT, **kw)
NB = " "  # 半角空白を改行しない空白にして、数字の前後で折れないようにする(_head.py の P と同じ考え方)


def P(text, style):
    parts = re.split(r"(<[^>]*>)", text)
    return Paragraph("".join(pt if pt.startswith("<") else pt.replace(" ", NB) for pt in parts), style)


S_TITLE = st("ftitle", font=FONT_B, fontSize=18, leading=23, spaceAfter=2 * mm)
S_LEAD = st("flead", fontSize=10.2, leading=15, color=MUTED, spaceAfter=3 * mm)
S_H3 = st("fh3", font=FONT_B, fontSize=11, leading=15, color=ACCENT, spaceBefore=3.5 * mm, spaceAfter=1.2 * mm)
S_BODY = st("fbody", fontSize=10.5, leading=15.5)
S_SMALL = st("fsmall", fontSize=9, leading=12.5, color=MUTED)
S_K = st("fk", fontSize=9.5, leading=13, color=MUTED)
S_V = st("fv", fontSize=9.8, leading=13.5)

doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title=m["title"], author="将棋コーチ(試作)")
W = A4[0] - 28 * mm
story = []


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


def kv_table(rows):
    t = Table([[P(k, S_K), P(v, S_V)] for k, v in rows], colWidths=[70 * mm, W - 70 * mm])
    t.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 1.4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
            ]
        )
    )
    return t


# ==================== 発見の種類ごとの題(固定。docs/STEP_TIME_PLAN_2026-09-22.md §6.4 に厳密な文言は無いため、
# この道具で最小限の事実だけの題を決めた ― 実装担当の判断。判断・助言の言葉は含まない) ====================
TITLE_JP = {
    "timeSpent": "時間をかけた手と、崩れの割合",
    "timeUpLoss": "持ち時間を使い切って負けた局の、最後の局面の評価",
    "aheadLoss": "優勢になった後に負けた対局",
    "phase": "崩れの時期(序盤・中盤・終盤)",
    "none": "時間と形勢の動きについて",
}

# ==================== 禁止語・数の照合(判定はしない。描いた文を確かめるだけ。render_whatif.py の emit() と同じ考え方) ====================
BANNED = ["悪手", "弱点", "癖", "型", "傾向", "原因", "ミス", "見落とし", "改善", "練習", "必ず", "明らか", "あなた", "ご自身", "いつも", "がち", "クセ", "パターン"]

# 構造上いつも出てよい数(ページ割り・区分そのものを表す数。個々の局面の事実ではない)。
# lib/reportData.ts の TIME_VALUES・FINDING_VALUES・STANDING_BOUNDS と同じ値を保つこと(この道具は TS を import できないので
# 手で合わせる ― 値がずれたら emit() が「データに無い数」として止める)。
GLOBAL_ALLOWED_NUMBERS = {0, 1, 2, 4, 5, 9, 10, 20, 60, 120, 300}
_problems = []


def _numbers_of_findings(findings):
    numbers = set()
    for f in findings:
        for v in f["numbers"].values():
            if v is not None:
                numbers.add(abs(v))
    return numbers


def allowed_numbers_of(patient):
    numbers = set(GLOBAL_ALLOWED_NUMBERS)
    numbers |= _numbers_of_findings(patient["findings"])
    overview = patient["overview"]
    for key in ("fell", "early", "mid", "late", "fromAhead", "fromAheadLoss"):
        v = overview.get(key)
        if isinstance(v, int):
            numbers.add(v)
    time_data = patient["time"]
    if time_data.get("available"):
        for bucket in time_data.get("bySpent") or []:
            numbers.add(bucket["n"])
            numbers.add(bucket["collapsed"])
        alt = time_data.get("afterLongThink")
        if alt:
            for row in (alt["quickAfterLongThink"], alt["afterLongThinkAny"]):
                numbers.add(row["n"])
                numbers.add(row["collapsed"])
        for game in time_data.get("timeUpLosses") or []:
            numbers.add(game["total"])
            numbers.add(game["usedSec"])
            if game["finalScore"] is not None:
                numbers.add(abs(game["finalScore"]))
    if patient.get("previous") is not None:
        numbers.add(patient["previous"]["games"])
        numbers |= _numbers_of_findings([{"numbers": c["numbersBefore"]} for c in patient["previous"]["findings"]])
        numbers |= _numbers_of_findings([{"numbers": c["numbersNow"]} for c in patient["previous"]["findings"]])
    return numbers


ALLOWED = allowed_numbers_of(m)


def emit(text, extra_allowed=frozenset()):
    """文に出てくる数字を、その場面で使ってよい数の集合と照合する(_mid.py の allowed_numbers と同じ考え方)。"""
    plain = re.sub(r"<[^>]*>", "", text)
    allowed_all = ALLOWED | set(extra_allowed)
    for token in re.findall(r"[0-9]+", plain):
        n = int(token)
        if n not in allowed_all:
            _problems.append(f"データに無い数 {n} が文に出ている: {text[:80]}…")
    for w in BANNED:
        if w in text:
            _problems.append(f"使わない語「{w}」: {text[:80]}…")
    return text


def numbers_text(numbers):
    parts = [f"{k} {v}" for k, v in numbers.items() if v is not None]
    return "、".join(parts) if parts else "(数なし)"


# ==================== 1 ページ目: 今回の n 局で分かったこと ====================
games_n = m["summary"]["games"]
story.append(P(f"今回の {games_n} 局で分かったこと", S_TITLE))
story.append(P(f"{m['person']} の記録(作成 {m['today']})から、数だけを並べています。", S_LEAD))

shown = [f for f in m["findings"] if f["shown"]]
if not shown:
    story.append(P("今回は、上に書ける数がありませんでした。", S_BODY))
for f in shown:
    story.append(P(TITLE_JP.get(f["kind"], f["kind"]), S_H3))
    story.append(P(emit(f["text"]), S_BODY))
story.append(PageBreak())

# ==================== 2 ページ目: 前回のことは、今回も起きたか ====================
story.append(P("前回のことは、今回も起きたか", S_TITLE))
previous = m.get("previous")
if previous is None:
    story.append(P("初回のため、前回との比較はありません。", S_BODY))
else:
    story.append(P(f"前回({previous['games']} 局)と比べます。", S_LEAD))
    any_row = False
    for comp in previous["findings"]:
        sb, sn = comp["shownBefore"], comp["shownNow"]
        if sb and sn:
            state = "前回も今回も出ています。"
        elif sb and not sn:
            state = "前回は出ていましたが、今回は出ていません。"
        elif (not sb) and sn:
            state = "前回は出ていませんでしたが、今回は出ています。"
        else:
            continue  # 前回も今回も出ていない種類は載せない(比べる材料が無い)
        any_row = True
        row_allowed = set(v for v in comp["numbersBefore"].values() if v is not None) | set(v for v in comp["numbersNow"].values() if v is not None)
        row_allowed = {abs(v) for v in row_allowed} | {previous["games"]}
        story.append(P(TITLE_JP.get(comp["kind"], comp["kind"]), S_H3))
        story.append(P(emit(state, row_allowed), S_BODY))
        story.append(kv_table([("前回の数", numbers_text(comp["numbersBefore"])), ("今回の数", numbers_text(comp["numbersNow"]))]))
        story.append(Spacer(1, 1.5 * mm))
    if not any_row:
        story.append(P("前回・今回のどちらでも出ていない種類だけでした。", S_BODY))
story.append(PageBreak())

# ==================== 3 ページ目: 次の n 局で見るもの ====================
story.append(P(f"次の {games_n} 局で見るもの", S_TITLE))
story.append(P("今回、数として出した名前と、今回の値です(次はこう数えます。予測や助言はありません)。", S_LEAD))

time_data = m["time"]
overview = m["overview"]


def bucket_text(bucket):
    return f"{bucket['collapsed']} / {bucket['n']}" if bucket is not None else "—(比べられない)"


rows = []
if time_data.get("available"):
    by_spent = time_data["bySpent"]
    labels = ["0〜1 秒", "2〜4 秒", "5〜9 秒", "10 秒以上"]
    for label, bucket in zip(labels, by_spent):
        rows.append((f"かけた時間 {label}(崩れ / 組)", bucket_text(bucket)))
    time_up_n = len(time_data["timeUpLosses"]) if time_data.get("timeUpLosses") is not None else None
    rows.append(("持ち時間を使い切って負けた局", str(time_up_n) if time_up_n is not None else "—(比べられない)"))
else:
    rows.append(("かけた時間・持ち時間を使い切って負けた局", "—(比べられない)"))
rows.append(("優勢になった対局(延べ)", str(overview["fromAhead"])))
rows.append(("優勢から負けた対局(延べ)", str(overview["fromAheadLoss"])))
rows.append(("崩れ(序盤)", str(overview["early"])))
rows.append(("崩れ(中盤)", str(overview["mid"])))
rows.append(("崩れ(終盤)", str(overview["late"])))

story.append(kv_table([(k, emit(v)) for k, v in rows]))
story.append(PageBreak())

# ==================== 4 ページ目: 数え方 ====================
story.append(P("数え方", S_TITLE))
story.append(P("この報告の数がどう決まっているかを書きます。", S_LEAD))
notes = [
    "「かけた時間」は、棋譜に書かれた秒をそのまま使います(切り捨ての整数)。0〜1 秒・2〜4 秒・5〜9 秒・10 秒以上の 4 段に分けます。",
    "「崩れ」は、直前の評価の区分(優勢・互角・劣勢)が優勢または互角だった局面から、直後に区分が 1 段以上下がったことです。+300 以上を優勢、−300 以下を劣勢、その間を互角とします。",
    "「持ち時間を使い切って負けた局」は、終局の種類が切れ負けで、かつ本人が負けた局です。",
    "「優勢から負けた対局」の数は、評価の区分が優勢から下がった場面(崩れ)のうち、その対局が負けだったものを数えた延べ回数です(同じ対局で複数回数えることがあります)。",
    "この報告の数は、棋力や手の良し悪しを表す数ではありません。",
]
story.append(notebox([emit(n) for n in notes]))

if _problems:
    print("\n".join(_problems), file=sys.stderr)
    sys.exit(1)

doc.build(story)

try:
    import fitz  # pymupdf

    _pdf = fitz.open(out)
    _pages = _pdf.page_count
    _pdf.close()
except ImportError:
    _pages = None

if _pages is not None and _pages != 4:
    print(f"ページ数が 4 ではない({_pages} ページ。はみ出した可能性がある)", file=sys.stderr)
    sys.exit(1)

print(f"wrote {out}({_pages if _pages is not None else '?'} ページ)")
