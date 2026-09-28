# -*- coding: utf-8 -*-
# STEP TIME 作業 2・作業 3・作業 4・作業 4b(docs/STEP_TIME_PLAN_2026-09-22.md §6.4・§6.7・§6.10・§6.12)。本編を描く道具。
#
# 使い方: python3 -X utf8 render_front.py <patient_report_data.json> <出力 PDF> [<finding_texts.json>]
#
# 【発見の判定はここではしない】
# 何を出すか(`findings[].shown`)・前回との比較(`previous`)・「ひとことで」(`findings[].oneLine`)は
# `lib/reportData.ts` の `buildFindings`・`buildPrevious`(TypeScript・試験できる側)がすでに決めている。
# この道具は、その結果(数・文)を PDF に描くだけ。
#
# 【STEP TIME 作業 3(§6.7)】第 3 引数 `finding_texts.json`(`reportData.ts` の CLI が `patient_report_data.json` の
# 隣に常に書く。`lib/findingTexts.ts` の定数の写し)を渡すと、1 ページ目に「考えられること」「次の 20 局で見分けが
# つくこと」「試せること」の 3 段(`phase` は無し)、2 ページ目に §5.3 の固定文、4 ページ目に評価の揺れの注記を足す。
# **渡さなければ(第 3 引数が無い)、今の形(数の文だけ)のまま動く** ― 発見の判定・文言の正本はどちらも TypeScript 側
# (`lib/reportData.ts`・`lib/findingTexts.ts`)で、この道具は写しを描くだけ(判定・新しい文言は作らない)。
#
# 【STEP TIME 作業 4「伝わる形」(§6.10)】判定・数・設計思想は変えず、読んで分かる順と言葉にする。
# - 1 ページ目: 冒頭に読み方の枠(`fdata["readingGuide"]`。fdata が無ければ足さない)→ 発見ごとに
#   題 → **ひとことで**(`findings[].oneLine`。太字)→ 数の文 → 考えられること(囲み)→ 見分け → 試せること →
#   末尾に「次の 20 局までに試せること(まとめ)」(fdata があるときだけ。shown の発見の tryable を出た順に番号で
#   再掲 + 末尾の 1 文)
# - 3 ページ目: 表の名を「(崩れた手 / 手)」に(§5.5「言い換え」。お客さん向けの文では「組」を使わない)
# - 4 ページ目: 頭に「言葉の意味」(fdata の `glossary`。5 項目)を足す
# - ページ数は 4〜6(節ごとに改ページは変えていない。3 段・読み方・まとめ・言葉の意味を足すと 1・4 ページ目が
#   2 ページ以上になり得るため、STEP TIME 作業 3 のときの緩め方をそのまま使う)
# - 検査: 禁止語・数の照合に加えて、**お客さん向けの文に「組」が残っていれば rc=1**(§6.10 の 2。finding_texts.json
#   経由の文・このファイルのテンプレートの文の両方が対象。`emit()` に組み込んだ)
#
# 【STEP TIME 作業 4b「文だけの直し」(§6.12)】判定・数は変えない。文だけを直す。
# - `phase` の数の文の下に `PHASE_NOTE`(fdata の `phaseNote`。考えられること・試せることの代わりの 1 文)を足す
#   (`append_considerations_block` に組み込み)
# - 4 ページ目の「言葉の意味」が 5 項目に(fdata の `glossary` をそのまま並べるだけなので、このファイルの描画コードは
#   変えていない ― 増えたのは `lib/findingTexts.ts` 側の `GLOSSARY` の中身)
# - 検査を追加: 「次の 20 局までに試せること(まとめ)」の各項目に `(a)`/`(b)`/`(c)` の裸の参照、または「同じ物差し」
#   が残っていれば rc=1(`check_summary_item()`。まとめは発見の題を伴わずに再掲されるため、裸の参照は読者に伝わらない)
#
# 【この新規ファイルが再利用する「流儀」(既存の 6 本(_head.py・_util.py・_mid.py・_app_head.py・_app.py・_tail.py)は
# 変えない。_head.py は import せず、書体の探し方だけをこのファイルの中に書き写した)】
# - 書体の探し方・埋め込み(_head.py と同じ。この道具は sfens.json・prose.json を読まないので REPORT_DATA_DIR は使わない)
# - 段落・表の組み方(reportlab の Paragraph/Table)、数の照合・禁止語の確かめの考え方(_mid.py の allowed_numbers・BANNED
#   と同じ考え方。実装はこのファイルで完結する。render_whatif.py の emit() と同じ作り)
#
# 【この道具が絶対にやらないこと】将棋の判断・断定的な戦法名の表示・助言・予測の文。数の再計算(判定は TypeScript 側)。
# 新しい文言を作ること(3 段・前回比較・揺れの注記・読み方・まとめ・言葉の意味はすべて finding_texts.json の写しを
# そのまま描くだけ)。
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
    sys.exit("使い方: python3 -X utf8 render_front.py <patient_report_data.json> <出力 PDF> [<finding_texts.json>]")
src, out = sys.argv[1], sys.argv[2]
m = json.load(open(src, encoding="utf-8"))
# STEP TIME 作業 3(§6.7 の 3): 第 3 引数が無ければ fdata は None(今の形のまま。判定・新しい文言はここで作らない)。
fdata = json.load(open(sys.argv[3], encoding="utf-8")) if len(sys.argv) >= 4 else None

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
# STEP TIME 作業 3(§6.7 の 2): 3 段(考えられること・次の 20 局で見分けがつくこと・試せること)の見出し。
S_H4 = st("fh4", font=FONT_B, fontSize=9.5, leading=13, color=MUTED, spaceBefore=2.2 * mm, spaceAfter=0.8 * mm)
S_BODY = st("fbody", fontSize=10.5, leading=15.5)
S_SMALL = st("fsmall", fontSize=9, leading=12.5, color=MUTED)
S_K = st("fk", fontSize=9.5, leading=13, color=MUTED)
S_V = st("fv", fontSize=9.8, leading=13.5)
# STEP TIME 作業 4(§6.10 の 2): 「ひとことで」(太字の 1 行。数の文の上)。
S_ONELINE = st("foneline", font=FONT_B, fontSize=11.2, leading=15.5, spaceAfter=0.8 * mm)

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


def box(paragraphs):
    """STEP TIME 作業 4(§6.10 の 2): notebox と同じ見た目の枠だが、先頭に「・」を付けない
    (読み方の枠のような、1 つの続いた文を入れる場所で使う)。"""
    t = Table([[p] for p in paragraphs], colWidths=[W])
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
    "timeUpLoss": "持ち時間に到達した局の、最後の局面の評価",
    "aheadLoss": "優勢になった後に負けた対局",
    "phase": "崩れの時期(序盤・中盤・終盤)",
    "none": "時間と形勢の動きについて",
}

# ==================== 禁止語・数の照合(判定はしない。描いた文を確かめるだけ。render_whatif.py の emit() と同じ考え方) ====================
# 2026-09-25 の人間の決定で空にした(凍結の例外 14 件目 ― 冊子の禁止語はすべて使ってよい)。ループと _problems の枠は残す。
BANNED = []

# 構造上いつも出てよい数(ページ割り・区分そのものを表す数。個々の局面の事実ではない)。
# lib/reportData.ts の TIME_VALUES・FINDING_VALUES・STANDING_BOUNDS と同じ値を保つこと(この道具は TS を import できないので
# 手で合わせる ― 値がずれたら emit() が「データに無い数」として止める)。
# STEP TIME 作業 3(§6.7 の 2): 固定文(finding_texts.json)に出る「10 秒」「60 秒」「4 秒」「5 局」「20 局」「40 局」
# 「10 分 + 30 秒」の数は、finding_texts.json から来た文としてまとめて許す(10・60・4・5・20 は既存のまま、30・40 を追加)。
# STEP TIME 作業 4(§6.10 の 2): 「言葉の意味」(GLOSSARY)の「第 1 候補より 600 以上低かった局面」(分かれ道の定義。
# lib/whatif.ts の WHATIF_VALUES.minLossCp と同じ値)の 600 を追加。1・2・5・300 は既存のまま。
GLOBAL_ALLOWED_NUMBERS = {0, 1, 2, 4, 5, 9, 10, 20, 30, 40, 60, 120, 300, 600}
_problems = []
# STEP TIME 作業 4(§6.10 の 2): お客さん向けの文に「組」が残っていたら rc=1(§5.5「言い換え」)。emit() を通る
# すべての文と、テンプレートの数の照合を経ない文字列(見出し等)の両方をここで見張る。
_KUMI = "組"


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
    """文に出てくる数字を、その場面で使ってよい数の集合と照合する(_mid.py の allowed_numbers と同じ考え方)。
    STEP TIME 作業 4(§6.10 の 2): 「組」(お客さん向けの文では使わない。§5.5「言い換え」)もここで見張る。"""
    plain = re.sub(r"<[^>]*>", "", text)
    allowed_all = ALLOWED | set(extra_allowed)
    for token in re.findall(r"[0-9]+", plain):
        n = int(token)
        if n not in allowed_all:
            _problems.append(f"データに無い数 {n} が文に出ている: {text[:80]}…")
    for w in BANNED:
        if w in text:
            _problems.append(f"使わない語「{w}」: {text[:80]}…")
    if _KUMI in text:
        _problems.append(f"お客さん向けの文に「{_KUMI}」が残っている(§5.5 言い換え): {text[:80]}…")
    return text


# STEP TIME 作業 4b(§6.12): 「次の 20 局までに試せること(まとめ)」の各項目が単独で読める文であることの検査。
# まとめは発見の題(「考えられること」の (a)(b)(c) の説明)を伴わずに再掲されるため、(a)/(b)/(c) の裸の参照が
# 残っていると読者に何を指すか伝わらない(§5.1 の答えの形。docs §5.2 で T1・T4・T3 の tryable から裸の参照を
# 取り除いた)。「同じ物差し」→「同じ数え方」の言い換えも、まとめの項目で崩れていないかここで見張る。
_BARE_LETTER_REF = re.compile(r"\([abc]\)")
_SAME_YARDSTICK = "同じ物差し"


def check_summary_item(text):
    """まとめの 1 項目(§6.12 の検査)。emit() の禁止語・数の照合とは別に、この 2 つを見る。"""
    if _BARE_LETTER_REF.search(text):
        _problems.append(f"まとめの項目に (a)/(b)/(c) の裸の参照が残っている: {text[:80]}…")
    if _SAME_YARDSTICK in text:
        _problems.append(f"まとめの項目に「{_SAME_YARDSTICK}」が残っている(§6.12: 「同じ数え方」に統一): {text[:80]}…")
    return text


def numbers_text(numbers, labels):
    """「名 数」を読点で並べる(司令塔の指示、2026-09-23: キーの英字のまま出さない。名は labels から引く)。"""
    parts = [f"{labels[k]} {v}" for k, v in numbers.items() if v is not None]
    return emit("、".join(parts) if parts else "(数なし)")


# `findings[].kind` → その発見(numbers・labels を含む)。page2(前回との比較)・page3(次の n 局で見るもの)の両方で使う。
findings_by_kind = {f["kind"]: f for f in m["findings"]}

# ==================== 1 ページ目: 今回の n 局で分かったこと ====================
games_n = m["summary"]["games"]
story.append(P(f"今回の {games_n} 局で分かったこと", S_TITLE))
story.append(P(f"{m['person']} の記録(作成 {m['today']})から、数だけを並べています。", S_LEAD))

# STEP TIME 作業 4(§6.10 の 2): 読み方の枠(1 ページ目冒頭。fdata が無ければ足さない ― 今の形のまま動く)。
if fdata is not None:
    story.append(box([P(emit(fdata["readingGuide"]), S_SMALL)]))
    story.append(Spacer(1, 2 * mm))

shown = [f for f in m["findings"] if f["shown"]]
if not shown:
    story.append(P("今回は、上に書ける数がありませんでした。", S_BODY))


def append_considerations_block(kind):
    """STEP TIME 作業 3(§6.7 の 2): 発見の種類 kind の 3 段(考えられること・次の 20 局で見分けがつくこと・
    試せること)を story に足す(fdata が無い、またはその種類の considerations が null(phase)なら何も足さない)。
    STEP TIME 作業 4b(§6.12): `phase` は 3 段の代わりに `PHASE_NOTE`(考えられること・試せることを付けない
    理由の 1 文)を数の文の下に足す(fdata があるときだけ)。
    """
    if fdata is None:
        return
    text_set = fdata["findings"].get(kind)
    if text_set is None or text_set["considerations"] is None:
        if kind == "phase":
            story.append(P(emit(fdata["phaseNote"]), S_SMALL))
        return
    lead = fdata["considerationsLead"]
    story.append(P(emit(f"考えられること({lead})"), S_H4))
    story.append(notebox([emit(item) for item in text_set["considerations"]]))
    story.append(P("次の 20 局で見分けがつくこと", S_H4))
    story.append(P(emit(text_set["distinguish"]), S_BODY))
    story.append(P("試せること", S_H4))
    story.append(P(emit(text_set["tryable"]), S_BODY))


for f in shown:
    story.append(P(emit(TITLE_JP.get(f["kind"], f["kind"])), S_H3))
    # STEP TIME 作業 4(§6.10 の 2): 「ひとことで」(太字。数の文の上)。判定はしない ― Finding["oneLine"] は
    # すでに reportData.ts(TypeScript)が numbers から選んだ文字列。
    story.append(P(emit(f["oneLine"]), S_ONELINE))
    story.append(P(emit(f["text"]), S_BODY))
    append_considerations_block(f["kind"])

# STEP TIME 作業 4(§6.10 の 2): 1 ページ目の末尾に「次の 20 局までに試せること(まとめ)」(fdata があるときだけ。
# shown の発見の tryable を出た順に 1. 2. 3. と番号で再掲 + 末尾の 1 文。tryable が 1 つも無ければ何も出さない
# ― 空のまとめを見せない。実装担当の判断、計画に無い判断)。
if fdata is not None:
    tryable_items = []
    for f in shown:
        text_set = fdata["findings"].get(f["kind"])
        if text_set is not None and text_set.get("tryable"):
            tryable_items.append(text_set["tryable"])
    if tryable_items:
        story.append(P(emit(fdata["tryableSummaryHeading"]), S_H3))
        for i, item in enumerate(tryable_items, start=1):
            check_summary_item(item)
            # 番号(1. 2. 3.)は本文の数ではないので、その番号だけをこの行に限って許す(extra_allowed)。
            story.append(P(emit(f"{i}. {item}", extra_allowed={i}), S_BODY))
        story.append(P(emit(fdata["tryableSummaryTail"]), S_SMALL))

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
            fixed_key = "both"
        elif sb and not sn:
            state = "前回は出ていましたが、今回は出ていません。"
            fixed_key = "beforeOnly"
        elif (not sb) and sn:
            state = "前回は出ていませんでしたが、今回は出ています。"
            fixed_key = "nowOnly"
        else:
            continue  # 前回も今回も出ていない種類は載せない(比べる材料が無い)
        any_row = True
        row_allowed = set(v for v in comp["numbersBefore"].values() if v is not None) | set(v for v in comp["numbersNow"].values() if v is not None)
        row_allowed = {abs(v) for v in row_allowed} | {previous["games"]}
        # labels は前回の JSON には無い(numbersBefore・numbersNow は数だけ)。名の集合は種類ごとに変わらないので、
        # 今回の同じ種類の発見(findings_by_kind)が持つ labels をそのまま使う(python 側に手写ししない)。
        comp_labels = findings_by_kind[comp["kind"]]["labels"]
        story.append(P(emit(TITLE_JP.get(comp["kind"], comp["kind"])), S_H3))
        story.append(P(emit(state, row_allowed), S_BODY))
        # STEP TIME 作業 3(§6.7 の 2): 種類ごとの 3 通りの文の下に §5.3 の固定文(fdata が無ければ足さない)。
        if fdata is not None:
            story.append(P(emit(fdata["previous"][fixed_key]), S_BODY))
        story.append(kv_table([("前回の数", numbers_text(comp["numbersBefore"], comp_labels)), ("今回の数", numbers_text(comp["numbersNow"], comp_labels))]))
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
        # STEP TIME 作業 4(§6.10 の 3・§5.5「言い換え」): 表の名を「(崩れた手 / 手)」に(「組」を使わない)。
        rows.append((f"かけた時間 {label}(崩れた手 / 手)", bucket_text(bucket)))
    time_up_n = len(time_data["timeUpLosses"]) if time_data.get("timeUpLosses") is not None else None
    rows.append(("持ち時間に到達した局", str(time_up_n) if time_up_n is not None else "—(比べられない)"))
else:
    rows.append(("かけた時間・持ち時間に到達した局", "—(比べられない)"))
ahead_loss_numbers = findings_by_kind["aheadLoss"]["numbers"]
rows.append(("優勢になった対局", str(ahead_loss_numbers["aheadGames"])))
rows.append(("優勢から負けた対局", str(ahead_loss_numbers["aheadLossGames"])))
rows.append(("崩れ(序盤)", str(overview["early"])))
rows.append(("崩れ(中盤)", str(overview["mid"])))
rows.append(("崩れ(終盤)", str(overview["late"])))

story.append(kv_table([(emit(k), emit(v)) for k, v in rows]))
story.append(PageBreak())

# ==================== 4 ページ目: 言葉の意味 → 数え方 ====================
story.append(P("数え方", S_TITLE))
# STEP TIME 作業 4(§6.10 の 2): 「言葉の意味」を「数え方」の前に足す(fdata が無ければ足さない)。
if fdata is not None:
    story.append(P("言葉の意味", S_H3))
    story.append(kv_table([(emit(item["term"]), emit(item["text"])) for item in fdata["glossary"]]))
    story.append(Spacer(1, 2 * mm))
story.append(P("この報告の数がどう決まっているかを書きます。", S_LEAD))
# 数え方の固定文は `exit_index.py` の 1 か所(2026-09-29 に移した)。**顧客に見せる文を 2 か所に持たない。**
import exit_index as _EI

notes = list(_EI.COUNTING_NOTES)
# STEP TIME 作業 3(§6.7 の 2): 評価の揺れの注記を足す(fdata が無ければ足さない)。
if fdata is not None:
    notes.append(fdata["evalJitterNote"])
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

# STEP TIME 作業 3(§6.7 の 2): 4 節・節ごとに改ページ(3 回の PageBreak)。3 段を足すと 1 ページ目が
# 2 ページ以上になり得るため、4 ページ固定はやめて 4〜6 ページの範囲に緩める(超えたら rc=1)。
if _pages is not None and not (4 <= _pages <= 6):
    print(f"ページ数が 4〜6 の範囲外({_pages} ページ。はみ出した可能性がある)", file=sys.stderr)
    sys.exit(1)

print(f"wrote {out}({_pages if _pages is not None else '?'} ページ)")
