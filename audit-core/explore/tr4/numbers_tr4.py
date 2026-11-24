# -*- coding: utf-8 -*-
"""便 TR4: 資料の数を機械で全部拾い、原文の抜粋と、札と本文の食い違い(期の字・項目の字)を見る。AI を使わない。

- 拾う: 表でない行の数と、表の第 1 列以外の升の数(符号 △▲+-− と小数と % の付いたものも)。
  除く: 日付と年月(年・月・日が続く・- や / で数がつながる)、「第 N 社」「第 N 期」、見出しの番号(「1.」)、
  括弧の中が数だけのもの(「(1)」)、表の区切りの行。
- 単位: 表でない行は数のすぐ後ろの字(百万円・千円・億円・円・%・％・人・名)。表の升は、升の中の字 → 列の見出しの括弧
  → 行の見出しの括弧 → 表の上 3 行の「単位」の行、の順。分からなければ None。
- 食い違い(札が金額・人数の時の期、札の種類によらず項目):
  - 期: 表でない行は、前の数の終わりからこの数までの字の中の、最後の期の字(後ろ 2 字以内に「比」が在るものは比べる字、
    項目の字の中のもの(「当期純利益」の「当期」)は項目の字なので除く。同じ所に長い字と短い字が在れば長い字)。
    表の升は列の見出しの字。「当」の字なら当期・当期末、「前」の字なら前期・前期末。
  - 項目: 表でない行は同じ区間の最後の項目の字、表の升は行の見出しの項目の字。字は TR1 の拾い方の項目の字の表の写し。
  どちらも、字が無ければ見ない(食い違いにしない)。文の意味は読まない。
"""
import re

NUM = re.compile(r"(?P<sign>[△▲+＋\-−]?)(?P<int>\d{1,3}(?:,\d{3})+|\d+)(?:\.(?P<dec>\d+))?")
UNIT_AFTER = re.compile(r"^\s{0,2}(百万円|千円|億円|円|％|%|人|名)")
PERIOD_WORDS = [("当連結会計年度末", "当"), ("前連結会計年度末", "前"), ("当事業年度末", "当"), ("前事業年度末", "前"),
                ("当連結会計年度", "当"), ("前連結会計年度", "前"), ("当事業年度", "当"), ("前事業年度", "前"),
                ("当期末", "当"), ("前期末", "前"), ("当年度", "当"), ("前年度", "前"), ("前年同期", "前"),
                ("当期", "当"), ("前期", "前")]
# TR1 の拾い方(check_tr1.ALIAS)の項目の字の写し(符号は使わない)
ALIAS = [("親会社株主に帰属する当期純利益", "当期純利益"), ("親会社株主に帰属する当期純損失", "当期純利益"),
         ("親会社株主に帰属する当期純損益", "当期純利益"), ("当期純利益", "当期純利益"), ("当期純損失", "当期純利益"),
         ("当期純損益", "当期純利益"), ("営業利益", "営業利益"), ("営業損失", "営業利益"), ("営業損益", "営業利益"),
         ("経常利益", "経常利益"), ("経常損失", "経常利益"), ("経常損益", "経常利益"), ("売上高", "売上高"), ("営業収益", "売上高"),
         ("事業収益", "売上高"), ("売上収益", "売上高"), ("減価償却費", "減価償却費"), ("現金及び預金", "現金及び預金"),
         ("現預金", "現金及び預金"), ("流動資産合計", "流動資産合計"), ("流動資産", "流動資産合計"), ("資産合計", "資産合計"),
         ("総資産", "資産合計"), ("短期借入金", "短期借入金"), ("長期借入金", "長期借入金"), ("負債合計", "負債合計"),
         ("総負債", "負債合計"), ("純資産合計", "純資産合計"), ("純資産", "純資産合計"), ("従業員数", "期末の従業員数"),
         ("従業員", "期末の従業員数")]
ALIAS.sort(key=lambda a: -len(a[0]))
UNIT_WORDS = ("百万円", "千円", "億円", "円")


def _is_excluded(line, m):
    s, e = m.start(), m.end()
    before, after = line[:s], line[e:]
    if re.match(r"^\s?(年|月|日|社|期|四半期|か月|ヶ月|カ月)", after):
        return True
    if re.search(r"第\s?$", before):
        return True
    if re.match(r"^[\-/]\d", after) or re.search(r"\d[\-/]$", before):
        return True
    if m.group("sign") in ("-", "−") and re.search(r"\d$", before):
        return True  # 「2025-07-01」の「-01」
    if not m.group("dec") and re.match(r"^\.(\s|$)", after):
        return True
    if re.search(r"[（(]\s?$", before) and re.match(r"^\s?[)）]", after):
        return True
    return False


def _value(m):
    v = float(m.group("int").replace(",", "") + ("." + m.group("dec") if m.group("dec") else ""))
    return -v if m.group("sign") in ("△", "▲", "-", "−") else v


def _paren_unit(text):
    m = re.search(r"[（(]\s*(百万円|千円|億円|円|人|名|%|％)\s*[)）]", text or "")
    return m.group(1) if m else None


def extract_all(md):
    lines = md.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(i)
                i += 1
            above = " ".join(lines[max(0, block[0] - 3):block[0]])
            tunit = next((u for u in UNIT_WORDS if "単位" in above and u in above), None)
            head = [c.strip() for c in lines[block[0]].strip().strip("|").split("|")]
            for li in block[1:]:
                raw = lines[li]
                if re.match(r"^\s*\|[\s\-:|]+\|\s*$", raw):
                    continue
                cells = raw.strip().strip("|").split("|")
                label = cells[0].strip() if cells else ""
                pos = raw.index("|") + 1
                for j, c in enumerate(cells):
                    a = pos
                    pos += len(c) + 1
                    if j == 0:
                        continue
                    for m in NUM.finditer(c):
                        if _is_excluded(c, m):
                            continue
                        rest = c[m.end():]
                        u = UNIT_AFTER.match(rest)
                        unit = u.group(1) if u else (_paren_unit(head[j] if j < len(head) else "") or _paren_unit(label) or tunit)
                        out.append({"行": li, "始め": a + m.start(), "終わり": a + m.end(), "字": m.group(0).strip(), "値": _value(m),
                                    "単位": unit, "場所": "表", "列の見出し": head[j] if j < len(head) else "", "行の見出し": label,
                                    "区間": label})
            continue
        if not line.startswith("#"):
            prev = 0
            for m in NUM.finditer(line):
                if _is_excluded(line, m):
                    continue
                u = UNIT_AFTER.match(line[m.end():])
                out.append({"行": i, "始め": m.start(), "終わり": m.end(), "字": m.group(0), "値": _value(m),
                            "単位": u.group(1) if u else None, "場所": "文", "区間": line[prev:m.start()]})
                prev = m.end() + (u.end() if u else 0)
        i += 1
    return out


def snippet(md, rec, width=18):
    line = md.split("\n")[rec["行"]]
    if rec["場所"] == "表":
        return "%s | … %s" % (rec["行の見出し"], line[max(0, rec["始め"] - width):rec["終わり"] + width].strip())
    return line[max(0, rec["始め"] - width):rec["終わり"] + width]


def period_word(rec):
    """数の期の字(「当」「前」と、その字)。無ければ (None, None)。"""
    if rec["場所"] == "表":
        h = rec.get("列の見出し") or ""
        for w, k in PERIOD_WORDS:
            if w in h:
                return k, w
        if "当" in h:
            return "当", h
        if "前" in h:
            return "前", h
        return None, None
    seg = rec["区間"]
    spans = [(m.start(), m.end()) for w, _ in ALIAS for m in re.finditer(re.escape(w), seg)]
    best = None
    for w, k in PERIOD_WORDS:
        for m in re.finditer(re.escape(w), seg):
            if "比" in seg[m.end():m.end() + 2]:
                continue
            if any(s <= m.start() and m.end() <= e for s, e in spans):
                continue  # 「当期純利益」の中の「当期」は項目の字
            if best is None or m.start() > best[0] or (m.start() == best[0] and len(w) > len(best[2])):
                best = (m.start(), k, w)
    return (best[1], best[2]) if best else (None, None)


def item_word(rec):
    seg = rec["区間"]
    taken = [False] * len(seg)
    found = []
    for w, item in ALIAS:
        for m in re.finditer(re.escape(w), seg):
            if any(taken[m.start():m.end()]):
                continue
            for k in range(m.start(), m.end()):
                taken[k] = True
            found.append((m.start(), item, w))
    if not found:
        return None, None
    found.sort()
    return found[-1][1], found[-1][2]


def conflicts(rec, tag):
    """札と本文の食い違いの一覧 [(種類, 本文の字)]。"""
    out = []
    if tag.get("種類") in ("金額", "人数"):
        k, w = period_word(rec)
        want = "当" if tag.get("期") in ("当期", "当期末") else "前"
        if k and k != want:
            out.append(("期の字", w))
    it, w = item_word(rec)
    if it and it != tag.get("項目"):
        out.append(("項目の字", w))
    return out
