# -*- coding: utf-8 -*-
# STEP ANSWER 作業(docs/STEP_ANSWER_PLAN_2026-09-23.md §2.2)。B(「どうしたら」の冊子)の markdown を
# check_answer.py に通してから、A4 縦の PDF にする道具。
#
# 使い方:
#   python3 -X utf8 render_answer.py <B.md> <出力 PDF>
#     [--patient <patient_report_data.json> --time-limit-sec <秒>]…
#     [--whatif-data <whatif_report_data.json>]… [--whatif-v2-dir <dir>]… [--read-dir <dir>]…
#     [--type-summary <summary.json>]… [--whatif-pdf <whatif.pdf>]… --menu <answer_menu.json>
#   (引数の形は check_answer.py と同じ。この道具は check_answer.py の関数をそのまま呼ぶ)
#
# 先に check_answer.check_answer() を呼び、rc≠0(落ちた文がある)なら描かずに理由を標準エラーへ出して exit 1。
# 通れば、markdown を見出し・箇条書き・表・太字の PDF にする(書体は render_front.py と同じ流儀。
# `<!-- menu: … -->`・`<!-- priority: … -->` の印は描かない)。ページ数の上限 8。
#
# 【この道具が絶対にやらないこと】check_answer.py の判定を上書きすること。B の文を直すこと。将棋の判断。
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
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_answer  # noqa: E402

USAGE = "使い方: python3 -X utf8 render_answer.py <B.md> <出力 PDF> [check_answer.py と同じ引数…]"

# ---- 書体(render_front.py と同じ流儀。ヒラギノ系 CID → 無ければ埋め込みフォント) ----
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
NB = " "

S_TITLE = st("atitle", font=FONT_B, fontSize=15.5, leading=20, spaceBefore=2 * mm, spaceAfter=2 * mm)
S_H2 = st("ah2", font=FONT_B, fontSize=12.5, leading=17, color=ACCENT, spaceBefore=4 * mm, spaceAfter=1.5 * mm)
S_BODY = st("abody", fontSize=10, leading=15)
S_BULLET = st("abullet", fontSize=10, leading=15, leftIndent=4 * mm)
S_TABLE = st("atablecell", fontSize=9, leading=12.5)


def inline_markup(text):
    """`**太字**` を reportlab の `<b>` に、半角空白を改行しない空白に(数字前後で折れないように)。
    `<!-- menu: … -->`・`<!-- priority: … -->` の印は描かない(取り除く)。"""
    text = check_answer.MENU_TAG_RE.sub("", text)
    text = check_answer.PRIORITY_TAG_RE.sub("", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    parts = re.split(r"(<[^>]*>)", text)
    return "".join(pt if pt.startswith("<") else pt.replace(" ", NB) for pt in parts)


def P(text, style):
    return Paragraph(inline_markup(text), style)


def is_table_row(line):
    return line.strip().startswith("|") and line.strip().endswith("|")


def is_table_separator(line):
    return bool(re.match(r"^\|[\s:|-]+\|$", line.strip()))


def table_cells(line):
    parts = line.strip().strip("|").split("|")
    return [c.strip() for c in parts]


def build_story(markdown_text):
    lines = markdown_text.split("\n")
    story = []
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        line = raw.strip()
        if line == "":
            i += 1
            continue
        if line == "---":
            story.append(HRFlowable(width="100%", thickness=0.5, color=LINE, spaceBefore=2 * mm, spaceAfter=2 * mm))
            i += 1
            continue
        if line.startswith("# "):
            story.append(P(line[2:], S_TITLE))
            i += 1
            continue
        if line.startswith("## "):
            story.append(P(line[3:], S_H2))
            i += 1
            continue
        if is_table_row(line):
            rows = []
            while i < n and is_table_row(lines[i].strip()):
                row_line = lines[i].strip()
                if not is_table_separator(row_line):
                    rows.append([P(c, S_TABLE) for c in table_cells(row_line)])
                i += 1
            if rows:
                ncols = len(rows[0])
                width = A4[0] - 28 * mm
                col_width = width / ncols
                t = Table(rows, colWidths=[col_width] * ncols, repeatRows=1)
                t.setStyle(
                    TableStyle(
                        [
                            ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT),
                            ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
                            ("BACKGROUND", (0, 0), (-1, 0), BG),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 1.2 * mm),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2 * mm),
                            ("LEFTPADDING", (0, 0), (-1, -1), 1.5 * mm),
                        ]
                    )
                )
                story.append(t)
                story.append(Spacer(1, 2 * mm))
            continue
        m_num = re.match(r"^(\d+)\.\s+(.*)$", line)
        if m_num:
            story.append(P(f"{m_num.group(1)}. {m_num.group(2)}", S_BULLET))
            i += 1
            continue
        if line.startswith("- "):
            story.append(P(f"・{line[2:]}", S_BULLET))
            i += 1
            continue
        story.append(P(line, S_BODY))
        i += 1
    return story


def main(argv):
    if len(argv) < 2:
        sys.exit(USAGE)
    markdown_path, out_path = argv[0], argv[1]
    args = check_answer.parse_args([markdown_path] + argv[2:])
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    ctx = check_answer.build_materials(args, repo_root)
    with open(args.markdown_path, encoding="utf-8") as f:
        markdown_text = f.read()
    problems = check_answer.check_answer(markdown_text, ctx)
    if problems:
        for line_no, reason, line in problems:
            print(f"{line_no}: {reason}: {line.strip()[:100]}", file=sys.stderr)
        sys.exit(1)

    body = check_answer.strip_dev_section(markdown_text)
    doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title="対局後診断・どうしたら", author="将棋コーチ(試作)")
    doc.build(build_story(body))

    try:
        import fitz  # pymupdf

        pdf = fitz.open(out_path)
        pages = pdf.page_count
        pdf.close()
    except ImportError:
        pages = None

    if pages is not None and pages > 8:
        sys.exit(f"ページ数が上限 8 を超えている({pages} ページ)")

    from check_fonts_embedded import unembedded_fonts

    font_problems = unembedded_fonts(out_path)
    if font_problems:
        sys.exit("\n".join(font_problems))

    print(f"wrote {out_path}({pages if pages is not None else '?'} ページ)")


if __name__ == "__main__":
    main(sys.argv[1:])
