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
# 【組版だけを読みやすく作り直した(発注者「今のレイアウトじゃ読みづらい」)】検査(check_answer.py)・markdown の
# 中身・文言は一切変えていない。変えたのは見た目(字の大きさ・行間・段落間・余白・見出しの強さ・太字の描き方・
# 箇条書きのぶら下げインデント・数の拾いやすさ・表の罫線と列幅・ページ番号)だけ。
#
# 【太字の実装(書体に本物の Bold が無い環境向け)】このリポジトリの環境には Bold の欠けた TrueType しか無い
# (IPAex ゴシックは 1 ウェイトのみ、フォールバックの Arial Unicode.ttf も 1 ウェイト、ヒラギノは CFF 輪郭で
# reportlab の TTFont が読めない)。そのため `**太字**` は、同じ物理フォントを 2 つの名前で登録し
# (`JPEmbedded` と `JPEmbeddedBold`)、`<b>` が後者に解決されるようにしたうえで、Canvas.beginText() を差し替えた
# 自前の PDFTextObject(`_FauxBoldTextObject`)で「フォント名が `JPEmbeddedBold` になった瞬間だけ、PDF の文字
# 描画モードを 2(塗り+縁取り)にして細い線幅を乗せる」ことで太らせる(=描画の太さで太字にする)。書体そのものの
# 形は変えていない。reportlab の内部 API(`_setFont`/`setFont`/`setTextRenderMode`)に依存するため、reportlab の
# バージョンが大きく変われば挙動が変わりうる(README の「依存」参照)。
#
# 【この道具が絶対にやらないこと】check_answer.py の判定を上書きすること。B の文を直すこと。将棋の判断。
import functools
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as canvas_mod
from reportlab.pdfgen.textobject import PDFTextObject
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
FONT = "JPEmbedded"
FONT_B = "JPEmbeddedBold"
pdfmetrics.registerFont(TTFont(FONT, _font))
pdfmetrics.registerFont(TTFont(FONT_B, _font))  # 同じ物理フォントを別名で登録(太字の判別用。字形は同じ)
registerFontFamily(FONT, normal=FONT, bold=FONT_B, italic=FONT, boldItalic=FONT_B)

INK = colors.HexColor("#1e2a32")
MUTED = colors.HexColor("#5a6a74")
ACCENT = colors.HexColor("#2d6a8a")
LINE = colors.HexColor("#d5dde2")
BG = colors.HexColor("#f4f7f9")

# ==================== ページの余白・本文の大きさ(項目 1) ====================
LEFT_MARGIN = RIGHT_MARGIN = 22 * mm
TOP_MARGIN = 20 * mm
BOTTOM_MARGIN = 20 * mm
PAGE_W = A4[0] - LEFT_MARGIN - RIGHT_MARGIN

BODY_SIZE = 11
BODY_LEADING = 18.2  # 11pt の 1.65 倍前後
PARA_SPACE = 9  # 段落の間 ≒ 0.5 行
BULLET_LEFT_INDENT = 7 * mm
BULLET_INDENT = 1.8 * mm

st = lambda name, **kw: ParagraphStyle(name, fontName=kw.pop("font", FONT), textColor=kw.pop("color", INK), leading=kw.pop("leading", BODY_LEADING), wordWrap="CJK", alignment=TA_LEFT, **kw)
NB = " "  # 半角空白を改行しない空白にして、数字の前後で折れないようにする

# ---- 見出し(項目 2)。# は表紙代わりに大きく、## は前に空き+下線、### は太字 ----
S_TITLE = st("atitle", font=FONT_B, fontSize=21, leading=27, spaceAfter=2.5 * mm)
S_LEAD = st("alead", fontSize=10.3, leading=15, color=MUTED, spaceAfter=3 * mm)
S_H2 = st("ah2", font=FONT_B, fontSize=13.5, leading=18, color=ACCENT, spaceBefore=BODY_LEADING, spaceAfter=1.2 * mm)
S_H3 = st("ah3", font=FONT_B, fontSize=BODY_SIZE + 0.5, leading=BODY_LEADING, spaceBefore=BODY_LEADING * 0.55, spaceAfter=1.8 * mm)

# ---- 本文・箇条書き(項目 1・3) ----
S_BODY = st("abody", fontSize=BODY_SIZE, leading=BODY_LEADING, spaceAfter=PARA_SPACE)
S_BULLET = st("abullet", fontSize=BODY_SIZE, leading=BODY_LEADING, leftIndent=BULLET_LEFT_INDENT, bulletIndent=BULLET_INDENT, spaceAfter=PARA_SPACE * 0.75)

# ---- 「こうしてみては」の番号つき項目: 行動の文(1 段大きい太字)+ 根拠(1 段小さい薄字)(項目 3) ----
S_ACTION = st("aaction", font=FONT_B, fontSize=BODY_SIZE + 1.3, leading=BODY_LEADING + 2, leftIndent=BULLET_LEFT_INDENT, bulletIndent=BULLET_INDENT, spaceAfter=1 * mm)
S_REASON = st("areason", fontSize=BODY_SIZE - 1.6, leading=BODY_LEADING - 2.5, color=MUTED, leftIndent=BULLET_LEFT_INDENT, spaceAfter=PARA_SPACE * 0.85)

# ---- 表(項目 5) ----
S_TABLE = st("atablecell", fontSize=9.6, leading=13.6)
S_TABLE_HEAD = st("atablehead", font=FONT_B, fontSize=9.6, leading=13.6)

NUMBERED_ACTION_RE = re.compile(r"^\*\*(.+?)\*\*\s*(根拠[:：].*)$")

# ==================== 項目 4: 「数」を拾いやすく太字にする ====================
# `[0-9０-９+−-]+(?: ?/ ?[0-9０-９]+)?` の形で、(a)「局・回・手・秒・%・ポイント」が続く、または
# (b) 符号つきの評価値(+2407 のような形)のどちらかに当たれば太字にする。数そのものは変えない・増やさない
# (印字は markdown の文字列そのまま。ここでは <b>…</b> で囲むだけ)。
_UNIT_WORDS = "局|回|手|秒|%|ポイント"
_NUM_CORE = r"[0-9０-９+−\-]+(?: ?/ ?[0-9０-９]+)?"
_NUM_RE = re.compile(_NUM_CORE)
_HAS_DIGIT_RE = re.compile(r"[0-9０-９]")
_UNIT_AFTER_RE = re.compile(r"^[ 　]*(?:%s)" % _UNIT_WORDS)
_SIGN_CHARS = ("+", "−", "-")


def _embolden_numbers(text):
    def repl(m):
        span = m.group(0)
        if not _HAS_DIGIT_RE.search(span):
            return span  # 符号だけ・区切りの「-」だけは数ではない
        if span[0] in _SIGN_CHARS or _UNIT_AFTER_RE.match(text[m.end():]):
            return f"<b>{span}</b>"
        return span

    return _NUM_RE.sub(repl, text)


def inline_markup(text):
    """`**太字**` を reportlab の `<b>` に、単位つきの数・評価値を太字に、半角空白を改行しない空白に
    (数字前後で折れないように)。`<!-- menu: … -->`・`<!-- priority: … -->` の印は描かない(取り除く)。"""
    text = check_answer.MENU_TAG_RE.sub("", text)
    text = check_answer.PRIORITY_TAG_RE.sub("", text)
    text = _embolden_numbers(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    parts = re.split(r"(<[^>]*>)", text)
    return "".join(pt if pt.startswith("<") else pt.replace(" ", NB) for pt in parts)


def P(text, style, bullet=None):
    return Paragraph(inline_markup(text), style, bulletText=bullet)


def is_table_row(line):
    return line.strip().startswith("|") and line.strip().endswith("|")


def is_table_separator(line):
    return bool(re.match(r"^\|[\s:|-]+\|$", line.strip()))


def table_cells(line):
    parts = line.strip().strip("|").split("|")
    return [c.strip() for c in parts]


def _plain_len(text):
    """列の内容幅を測るための、markup を除いた見かけの文字数(項目 5「列は内容幅で」)。"""
    plain = check_answer.MENU_TAG_RE.sub("", text)
    plain = check_answer.PRIORITY_TAG_RE.sub("", plain)
    plain = re.sub(r"\*\*(.+?)\*\*", r"\1", plain)
    return len(plain)


def compute_col_widths(raw_rows, total_width, min_width=20 * mm):
    """列は内容幅で(項目 5)。列ごとの最長の見かけの文字数を重みにするが、そのまま比例配分すると
    文字数が極端に違う列(短い見出しの列と、長文の列)で差が出すぎるため、重みを 0.6 乗で緩めてから配分する
    (実装担当の判断。表計算ソフトの自動列幅に近い、素朴な緩和)。"""
    ncols = len(raw_rows[0])
    weights = [max(1, max(_plain_len(r[c]) for r in raw_rows)) ** 0.6 for c in range(ncols)]
    raw_widths = [total_width * w / sum(weights) for w in weights]
    widths = [max(w, min_width) for w in raw_widths]
    scale = total_width / sum(widths)
    return [w * scale for w in widths]


def _is_lead_candidate(line):
    """項目 2: `#` の下の 1 行の説明として扱ってよい行か(見出し・箇条書き・表・区切り線ではない、空でもない)。"""
    if not line:
        return False
    if line.startswith("#") or line.startswith("- ") or line == "---" or is_table_row(line):
        return False
    if re.match(r"^\d+\.\s", line):
        return False
    return True


def build_story(markdown_text, doc_title):
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
            story.append(HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=4 * mm, spaceAfter=4 * mm))
            i += 1
            continue
        if line.startswith("# "):
            story.append(P(line[2:], S_TITLE))
            i += 1
            nxt = lines[i].strip() if i < n else ""
            if _is_lead_candidate(nxt):
                story.append(P(nxt, S_LEAD))
                i += 1
            story.append(HRFlowable(width="100%", thickness=1.4, color=ACCENT, spaceBefore=0.5 * mm, spaceAfter=5 * mm))
            continue
        if line.startswith("### "):
            story.append(P(line[4:], S_H3))
            i += 1
            continue
        if line.startswith("## "):
            story.append(P(line[3:], S_H2))
            story.append(HRFlowable(width="100%", thickness=0.8, color=ACCENT, spaceBefore=0, spaceAfter=3.2 * mm))
            i += 1
            continue
        if is_table_row(line):
            raw_rows = []
            while i < n and is_table_row(lines[i].strip()):
                row_line = lines[i].strip()
                if not is_table_separator(row_line):
                    raw_rows.append(table_cells(row_line))
                i += 1
            if raw_rows:
                col_widths = compute_col_widths(raw_rows, PAGE_W)
                table_data = []
                for r_idx, cells in enumerate(raw_rows):
                    cell_style = S_TABLE_HEAD if r_idx == 0 else S_TABLE
                    table_data.append([P(c, cell_style) for c in cells])
                t = Table(table_data, colWidths=col_widths, repeatRows=1)
                t.setStyle(
                    TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                            ("LINEBELOW", (0, 0), (-1, 0), 1.1, ACCENT),
                            ("BACKGROUND", (0, 0), (-1, 0), BG),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
                            ("LEFTPADDING", (0, 0), (-1, -1), 2.5 * mm),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 2.5 * mm),
                        ]
                    )
                )
                story.append(Spacer(1, 1.5 * mm))
                story.append(t)
                story.append(Spacer(1, 4 * mm))
            continue
        m_num = re.match(r"^(\d+)\.\s+(.*)$", line)
        if m_num:
            num, rest = m_num.groups()
            rest = check_answer.MENU_TAG_RE.sub("", rest)
            rest = check_answer.PRIORITY_TAG_RE.sub("", rest)
            m_action = NUMBERED_ACTION_RE.match(rest)
            if m_action:
                action_text, reason_text = m_action.group(1), m_action.group(2)
                story.append(P(action_text, S_ACTION, bullet=f"{num}."))
                story.append(P(reason_text, S_REASON))
            else:
                story.append(P(rest, S_BULLET, bullet=f"{num}."))
            i += 1
            continue
        if line.startswith("- "):
            story.append(P(line[2:], S_BULLET, bullet="•"))
            i += 1
            continue
        story.append(P(line, S_BODY))
        i += 1
    return story


# ==================== 太字を「描画の太さ」で作る(項目 3。ファイル冒頭のコメント参照) ====================
BOLD_FONT_NAME = FONT_B


class _FauxBoldTextObject(PDFTextObject):
    def _bold_toggle(self, psfontname, size):
        is_bold = psfontname == BOLD_FONT_NAME
        was_bold = getattr(self, "_fb_bold", False)
        if is_bold and not was_bold:
            fill = getattr(self, "_fillColorObj", None) or INK
            self.setStrokeColor(fill)
            self._code.append("%.2f w" % max(0.35, (size or BODY_SIZE) * 0.032))
            self.setTextRenderMode(2)  # 塗り+縁取り(=描画の太さで太くする)
        elif was_bold and not is_bold:
            self.setTextRenderMode(0)
        self._fb_bold = is_bold

    def _setFont(self, psfontname, size):
        self._bold_toggle(psfontname, size)
        return PDFTextObject._setFont(self, psfontname, size)

    def setFont(self, psfontname, size, leading=None):
        self._bold_toggle(psfontname, size)
        return PDFTextObject.setFont(self, psfontname, size, leading)


class _ReportCanvas(canvas_mod.Canvas):
    """項目 7: ページ番号(ページ n / N)と、2 ページ目以降の小さい題。総ページ数は save() まで分からないため、
    reportlab の定番の手順(各ページの内容を貯めておき、save() で総数が分かってから 1 ページずつ描き直す)を使う。"""

    def __init__(self, *args, report_title="", **kwargs):
        canvas_mod.Canvas.__init__(self, *args, **kwargs)
        self._report_title = report_title
        self._saved_page_states = []

    def beginText(self, x=0, y=0, direction=None):
        return _FauxBoldTextObject(self, x, y, direction=direction)

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(total_pages)
            canvas_mod.Canvas.showPage(self)
        canvas_mod.Canvas.save(self)

    def _draw_footer(self, total_pages):
        page_no = self._pageNumber
        self.saveState()
        self.setFont(FONT, 8.3)
        self.setFillColor(MUTED)
        # **1 ページの文書にはノンブルを出さない**(P-163。2026-09-29)。
        # 「ページ 1 / 1」は読者に何も渡さない ― むしろ「この冊子は 1 ページなのか」と読める
        # (実物: 付録の表紙が 1 ページで、束ねた付録は 4 ページある)。
        # **この道具で組む 1 ページの文書はいまのところ表紙だけ**(納品の 10 冊を数えた)。
        if total_pages > 1:
            self.drawCentredString(A4[0] / 2, 10 * mm, f"ページ {page_no} / {total_pages}")
        if page_no > 1 and self._report_title:
            self.drawString(LEFT_MARGIN, A4[1] - 12.5 * mm, self._report_title)
        self.restoreState()


def _find_doc_title(markdown_text):
    for raw in markdown_text.split("\n"):
        line = raw.strip()
        if line.startswith("# "):
            return line[2:]
    return ""


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
    doc_title = _find_doc_title(body)
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="対局後診断・どうしたら",
        author="将棋コーチ(試作)",
    )
    doc.build(build_story(body, doc_title), canvasmaker=functools.partial(_ReportCanvas, report_title=doc_title))

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
