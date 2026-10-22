# -*- coding: utf-8 -*-
"""P-1 出どころの確認(封 docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md §4)。

> 歳入側の数値が歳出側の情報から**再掲・導出**されたものではないか、
> 資料の構造と出典を確認する。(人間の判断 2026-10-16)

**数を数える前にこれを書く。**封 §7: 「P-1 を飛ばして数を数えた」は失敗条件。
**この段では「独立した裏づけが何本」も「3 本に達する会計が何件」も出さない。**
出すのは**構造**だけ ― 列・階層・注記・会計の集合・再掲の有無。

通信しない。材料は `~/.cache/audit-core/sheet/`。
出典: 「令和６年度東京都各会計歳入歳出決算書及び東京都各会計歳入歳出決算附属書類等」、
東京都会計管理局、CC BY 4.0 を機械で読み取って加工。
  usage: python3 measure/sheet_sainyuu_p1_2026-10-16.py
"""
import collections
import importlib.util
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "fixtures", "sheet", "sainyuu_p1_2026-10-16.json")
SEAL = "docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md"

_sp = importlib.util.spec_from_file_location(
    "m2_for_p1", os.path.join(HERE, "sheet_m2_structure_2026-10-15.py"))
M2 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(M2)
norm = M2.norm
CACHE = M2.CACHE

SAINYUU = "op20251218_06kessan_02_sainyuu.xlsx"
MEISAI_SAINYUU = "op20251218_06kessan_04_jikoubetu_sainyuu.xlsx"

TITLE_RE = re.compile(r"^令和６年度東京都(.+)歳入歳出決算書$")
# **書類の表題は「再掲」ではない。**除く形を字で残す(でないと 0 件が自分の欠陥になる)
TITLE_FORMS = ("歳入歳出決算書", "歳入歳出決算事項別明細書")
CROSS_REF = re.compile("再掲|歳出に同じ|歳出と同じ|歳出参照|別表|歳出の")


def _val(c):
    return c.get("value") if isinstance(c, dict) else c


def cells_by_row(cells):
    rows = {}
    for ref, c in cells.items():
        m = re.match(r"([A-Z]+)(\d+)$", ref)
        if m:
            rows.setdefault(int(m.group(2)), {})[m.group(1)] = _val(c)
    return rows


# 科目の階層が入る列(ここは**値の列ではない**)
LEVEL_COLS = ("A", "B", "C", "D")


def header_cols(rows, head_label="科目", level_cols=LEVEL_COLS):
    """`科目` の行と、その次の行の**値の列の見出し**だけを集める。

    **科目の階層が入る列(A〜D)と、数字だけのセルは見出しに数えない** ―
    2 行ぶん丸ごと拾うと `01`・`都税` のような**行の中身**が列の集合に混ざる
    (最初にそう書いて実際に混ざった)。
    """
    head = None
    for r in sorted(rows):
        if norm(rows[r].get("A")) == norm(head_label):
            head = r
            break
    if head is None:
        return None, []
    out = []
    for rr in (head, head + 1):
        for col, v in sorted((rows.get(rr) or {}).items()):
            if not isinstance(v, str) or not v.strip():
                continue
            flat = re.sub(r"\s+", "", v)
            if rr != head and col in level_cols:
                continue                       # 款・項・目・節 の見出しは別に取る
            if flat.isdigit() or flat in ("円",):
                continue                       # 行の中身・単位は列名ではない
            out.append({"row": rr, "col": col, "text": flat})
    return head, out


def text_cells(cells):
    return [(ref, _val(c)) for ref, c in cells.items()
            if isinstance(_val(c), str) and _val(c).strip()]


def cross_references(cells):
    """**歳出への再掲・参照**を数える。**書類の表題は除き、除いた件数も残す。**"""
    hit, excluded = [], []
    for ref, v in text_cells(cells):
        flat = re.sub(r"\s+", "", v)
        if "歳出" not in flat and not CROSS_REF.search(flat):
            continue
        if any(flat.endswith(t) for t in TITLE_FORMS) or any(t in flat for t in TITLE_FORMS):
            excluded.append({"ref": ref, "text": v[:60], "why": "書類の表題"})
            continue
        hit.append({"ref": ref, "text": v[:120]})
    return hit, excluded


def notes(cells):
    out = []
    for ref, v in text_cells(cells):
        flat = re.sub(r"\s+", "", v)
        if flat.startswith("注") or flat.startswith("備考"):
            out.append({"ref": ref, "text": v[:160]})
    return sorted(out, key=lambda x: x["ref"])


def read(name):
    sheets, nts = M2.M1.read(os.path.join(CACHE, name))
    return sheets, nts


def kessan_sainyuu(sheets):
    cells = sheets["歳入"]["cells"]
    rows = cells_by_row(cells)
    strict, loose, wrapped = [], [], 0
    for r in sorted(rows):
        a = rows[r].get("A")
        if not isinstance(a, str):
            continue
        flat = re.sub(r"\s+", "", a)
        if not flat.endswith("歳入歳出決算書"):
            continue
        loose.append({"row": r, "text": a[:60]})
        m = TITLE_RE.match(flat)
        if m:
            strict.append({"row": r, "account": m.group(1), "rows": 1})
            continue
        # **表題は 2 行にまたがる。**長い会計名が折り返されている
        # (実測: 19 行のうち 16 行がこの形。1 行だけ見ると会計名が空白になる)
        prev = rows.get(r - 1, {}).get("A")
        joined = re.sub(r"\s+", "", (prev or "")) + flat
        m2 = TITLE_RE.match(joined)
        if m2:
            strict.append({"row": r, "account": m2.group(1), "rows": 2,
                           "joined_from": r - 1})
            wrapped += 1
    head, cols = header_cols(rows)
    xref, excluded = cross_references(cells)
    return {"sheet_count": len(sheets), "sheets": list(sheets),
            "title_rows_loose": len(loose),
            "title_rows_identified": len(strict),
            "titles_spanning_two_rows": wrapped,
            "titles_not_identified":
                [l for l in loose
                 if l["row"] not in {s["row"] for s in strict}],
            "accounts": [s["account"] for s in strict],
            "header_row": head, "header_cells": cols,
            "notes": notes(cells),
            "cross_references_to_saisyutu": xref,
            "excluded_as_document_title": len(excluded),
            "excluded_examples": excluded[:3]}


def meisai_sainyuu(sheets):
    toc = sheets.get("目次")
    toc_rows = cells_by_row(toc["cells"]) if toc else {}
    entries = []
    for r in sorted(toc_rows):
        label, name = toc_rows[r].get("B"), toc_rows[r].get("C")
        if isinstance(label, str) and isinstance(name, str) \
                and norm(label) not in ("シート名",):
            entries.append({"sheet": label, "account": name})
    first = next((s for s in sheets if s != "目次"), None)
    cells = sheets[first]["cells"]
    rows = cells_by_row(cells)
    head, cols = header_cols(rows)
    levels = []
    for rr in (head, (head or 0) + 1):
        for col, v in sorted((rows.get(rr) or {}).items()):
            if isinstance(v, str) and re.sub(r"\s+", "", v) in ("款", "項", "目", "節", "区分"):
                levels.append(re.sub(r"\s+", "", v))
    xref_all, excl_all = [], 0
    for sname in sheets:
        h, e = cross_references(sheets[sname]["cells"])
        xref_all += [dict(x, sheet=sname) for x in h]
        excl_all += len(e)
    return {"sheet_count": len(sheets), "sheets": list(sheets),
            "toc_entries": len(entries), "toc": entries,
            "first_sheet": first, "header_row": head, "header_cells": cols,
            "levels_in_header": levels,
            "notes": notes(cells),
            "cross_references_to_saisyutu": xref_all,
            "excluded_as_document_title": excl_all}


def value_columns(k):
    """決算書 歳入の**値の列**の集合(科目の見出しは外す)。**その場で測り直せる。**"""
    return sorted({c["text"] for c in k["header_cells"]
                   if c["text"] not in ("科目", "款", "項", "目", "節", "円")})


def saisyutu_accounts():
    """歳出側の決算書の会計名(正規化済み)。**実物を読む。**"""
    book, _ = M2.M1.read(os.path.join(CACHE, M2.KESSAN))
    return sorted({norm(b["account"]) for b in M2.parse_kessan(book)["blocks"]
                   if b["account"]})


def account_sets(k):
    """歳入と歳出の会計の集合を**その場で**比べる。"""
    out_accounts = saisyutu_accounts()
    in_accounts = sorted({norm(a) for a in k["accounts"]})
    return {"sainyuu": in_accounts, "saisyutu": out_accounts,
            "only_in_sainyuu": sorted(set(in_accounts) - set(out_accounts)),
            "only_in_saisyutu": sorted(set(out_accounts) - set(in_accounts)),
            "same_set": in_accounts == out_accounts}


def column_sets(k):
    in_cols = value_columns(k)
    out_cols = sorted(M2.KESSAN_COLS)
    return {"sainyuu(決算書 歳入)": in_cols,
            "saisyutu(決算書 歳出)": out_cols,
            "shared_names": sorted(set(in_cols) & set(out_cols)),
            "note": ("**名前が同じでも同じ数とは限らない。**"
                     "値が一致するかは 6a(値の重複)で別に測る")}


def main():
    sk, nk = read(SAINYUU)
    sm, nm = read(MEISAI_SAINYUU)
    k = kessan_sainyuu(sk)
    m = meisai_sainyuu(sm)
    acc = account_sets(k)
    cols_rec = column_sets(k)
    in_cols = cols_rec["sainyuu(決算書 歳入)"]
    out_cols = cols_rec["saisyutu(決算書 歳出)"]
    shared = cols_rec["shared_names"]

    rec = {
        "seal": SEAL,
        "step": "P-1 出どころの確認",
        "what_this_step_does_not_do": (
            "**独立した裏づけの本数・3 本に達する会計の数は出さない。**"
            "構造だけを書く(封 §4。P-2 以降は別の段)"),
        "source": ("令和６年度東京都各会計歳入歳出決算書及び東京都各会計"
                   "歳入歳出決算附属書類等、東京都会計管理局、CC BY 4.0"),
        "kessan_sainyuu": k, "meisai_sainyuu": m,
        "reader_notes": {"kessan": {kk: vv for kk, vv in nk.items()
                                    if kk in ("shared_strings", "phonetic_strings",
                                              "inline_strings", "shared_formulas")},
                         "meisai": {kk: vv for kk, vv in nm.items()
                                    if kk in ("shared_strings", "phonetic_strings",
                                              "inline_strings", "shared_formulas")}},
        "column_sets": cols_rec,
        "account_sets": acc,
        "restatement_6e": {
            "excluded_form": list(TITLE_FORMS),
            "why_excluded": "**書類の表題は再掲ではない。**除いた件数も記録する",
            "hits_kessan": len(k["cross_references_to_saisyutu"]),
            "hits_meisai": len(m["cross_references_to_saisyutu"]),
            "excluded_kessan": k["excluded_as_document_title"],
            "excluded_meisai": m["excluded_as_document_title"],
        },
    }
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)

    print("=== P-1 出どころの確認(構造だけ。数は出さない)===")
    print("決算書 歳入: sheet %d / 表題(緩い)%d 行 / 同定 %d 件 / "
          "**2 行にまたがる表題 %d 件**"
          % (k["sheet_count"], k["title_rows_loose"], k["title_rows_identified"],
             k["titles_spanning_two_rows"]))
    if k["titles_not_identified"]:
        print("  **同定できなかった表題 %d 件**" % len(k["titles_not_identified"]))
        for t in k["titles_not_identified"][:3]:
            print("    行 %s  %r" % (t["row"], t["text"]))
    print("明細 歳入: sheet %d / 目次 %d 件 / 階層の見出し %s"
          % (m["sheet_count"], m["toc_entries"], "・".join(m["levels_in_header"])))
    print("列(決算書 歳入): %s" % "・".join(in_cols))
    print("列(決算書 歳出): %s" % "・".join(out_cols))
    print("**名前が共通の列: %s**" % ("・".join(shared) if shared else "無し"))
    print("会計の集合は歳出と同じか: %s(歳入だけ %d / 歳出だけ %d)"
          % (acc["same_set"], len(acc["only_in_sainyuu"]),
             len(acc["only_in_saisyutu"])))
    print("6e 再掲・参照(表題を除く): 決算書 %d 件 / 明細 %d 件"
          % (rec["restatement_6e"]["hits_kessan"],
             rec["restatement_6e"]["hits_meisai"]))
    print("   **除いた「書類の表題」: 決算書 %d 件 / 明細 %d 件**"
          % (rec["restatement_6e"]["excluded_kessan"],
             rec["restatement_6e"]["excluded_meisai"]))
    for lbl, d in (("決算書 歳入", k), ("明細 歳入", m)):
        for n in d["notes"]:
            print("   注(%s %s): %s" % (lbl, n["ref"], re.sub(r"\s+", " ", n["text"])))
    print("->", OUT)


if __name__ == "__main__":
    main()
