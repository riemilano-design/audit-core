# -*- coding: utf-8 -*-
# STEP PIPE 作業 B(docs/STEP_PIPE_PLAN_2026-09-21.md §2.2)。作った PDF の全書体が埋め込みかを確かめる道具(pymupdf)。
# 「作った後に全書体が埋め込みかを確かめる仕組み」は、いままで司令塔の手作業だった。pymupdf が使える環境なので、ここに足す。
#
# 使い方: python3 -X utf8 check_fonts_embedded.py <PDF ...>
# 埋め込まれていない書体が 1 つでもあれば、そのファイル名と書体を標準エラーへ書いて exit 1。全部埋め込みなら exit 0。
import sys

import fitz  # pymupdf

# PDF の規格上、埋め込まなくても読む側が持っている前提の 14 書体(Base14)。日本語は含まれないので、
# 「埋め込まない PDF は読む側で文字が欠ける」の心配はこの 14 書体には当たらない(reportlab が既定で resource に足すことがある)。
BASE14_FONTS = {
    "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
    "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
    "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
    "Symbol", "ZapfDingbats",
}


def unembedded_fonts(pdf_path: str) -> list[str]:
    doc = fitz.open(pdf_path)
    problems: list[str] = []
    try:
        for page_index in range(doc.page_count):
            for font in doc.get_page_fonts(page_index):
                # get_page_fonts の要素: (xref, ext, type, basefont, name, encoding, ...)。埋め込みでない書体は ext が "n/a"
                embedded = font[1] != "n/a"
                if not embedded and font[3] not in BASE14_FONTS:
                    problems.append(f"{pdf_path}: page {page_index + 1}: {font[3]}({font[4]}) が埋め込まれていない")
    finally:
        doc.close()
    return problems


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("使い方: python3 -X utf8 check_fonts_embedded.py <PDF ...>", file=sys.stderr)
        return 1
    problems: list[str] = []
    for pdf_path in argv[1:]:
        problems += unembedded_fonts(pdf_path)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print(f"{len(argv) - 1} 本とも全書体が埋め込みだった")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
