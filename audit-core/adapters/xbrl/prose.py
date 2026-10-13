# -*- coding: utf-8 -*-
"""書類の経営分析の節(MD&A の TextBlock)を、渡された文章で差し替える。

``fixtures/xbrl/ai_prose_claims_2026-10-09.py`` の ``prose_to_html`` /
``build_modified_zip`` を **中身を変えずに**写したもの(2026-10-13、人間の決定の
第 3 段階: 入口を 1 本作る)。写した理由は、入口(``verify_document``)と
開発書類の測定が**同じ差し替え方**であることを、日付つきの道具に触らずに保つため。

**変えたのは止め方だけ**: 呼び出し側が扱えるように ``SystemExit`` を
``ProseReplacementError`` にした。差し替えの規則(1 行 = 1 段落・本文の文字は
変えない・要素がちょうど 1 個でなければ止まる)は 1 文字も変えていない。

同一性の証拠: ``tests/adapters/xbrl/test_verify_entry.py`` が、封じた文章
(``fixtures/xbrl/ai_prose_2026-10-09.txt``)を入れたときの ZIP の sha256 が
``AI_PROSE_ZIP_SHA256`` と一致することを留める(日付つき道具が作った値)。

通信しない。
"""

import io
import re
import zipfile
from xml.sax.saxutils import escape as xml_escape

from . import instance as I

# 日付つき道具 ai_prose_claims_2026-10-09.py が作った ZIP の sha256(封)。
AI_PROSE_ZIP_SHA256 = "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799"


class ProseReplacementError(Exception):
    """差し替えができない(節が無い・要素が 1 個でない)。**差し替えは起きていない。**"""


def prose_to_html(text):
    """1 行 = 1 段落。**本文の文字は変えない**(HTML の特殊文字だけ逃がす)。"""
    out = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        out.append("<p>%s</p>" % xml_escape(line))
    return "\n".join(out)


def build_modified_zip(zb, prose):
    """``(新しい ZIP のバイト列, 差し替えた要素名, 差し替えた file 名)``。"""

    inst = I.load_instance(zb)
    mdna = I.select_mdna(inst["textblocks"])
    if mdna is None:
        raise ProseReplacementError("MD&A の textBlock が見つからない")
    src = inst["source"]
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        raw = z.read(src).decode("utf-8")
        members = [(i, z.read(i.filename)) for i in z.infolist()]
    # 要素を 1 つだけ差し替える
    pat = re.compile(
        r"(<%s\b[^>]*>)(.*?)(</%s>)" % (re.escape(mdna), re.escape(mdna)), re.S)
    hits = pat.findall(raw)
    if len(hits) != 1:
        raise ProseReplacementError("MD&A の要素が %d 個 ― 1 個でないので止まる" % len(hits))
    new_inner = xml_escape(prose_to_html(prose))
    new_raw = pat.sub(lambda m: m.group(1) + new_inner + m.group(3), raw, count=1)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        for info, data in members:
            out.writestr(info, new_raw.encode("utf-8") if info.filename == src else data)
    return buf.getvalue(), mdna, src
