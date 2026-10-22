# -*- coding: utf-8 -*-
"""新領域① M-2 段 2・段 3(仕様 docs/DOMAIN1_M2_SPEC_2026-10-15.md)。

段 2 = 構造の抽出(会計・款・項・目・列を何件同定できたか)
段 3 = 集計の整合(款 = Σ項、合計 = Σ款、総括 = 決算書、明細 = 決算書)

**接続精度は測らない**(段 4)。**合格線は無い**(仕様 §8)。
範囲の証拠(`range_identified`)と値の一致(`value_match`)は**別の欄**に持つ(仕様 §4)。
一致は**完全一致**。合わない件は帯を広げず、1 件ずつ読むために明細を記録する(仕様 §3)。

材料は `~/.cache/audit-core/sheet/`。通信しない。
出典: 「令和６年度東京都各会計歳入歳出決算書及び東京都各会計歳入歳出決算附属書類等」、
東京都会計管理局、CC BY 4.0 を機械で読み取って加工。
"""
import collections
import importlib.util
import io
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.expanduser("~/.cache/audit-core/sheet")
OUT = os.path.join(ROOT, "fixtures", "sheet", "m2_structure_2026-10-15.json")
SOUKATU = "op20251218_06kessan_01_soukatu.xlsx"
KESSAN = "op20251218_06kessan_03_saisyutu.xlsx"
MEISAI = "op20251218_06kessan_05_jikoubetu_saisyutu.xlsx"

_spec = importlib.util.spec_from_file_location(
    "m1", os.path.join(HERE, "sheet_read_m1_2026-10-15.py"))
M1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M1)

CODE_RE = re.compile(r"^\d{2}$")
MINUS = "△"
NORMALIZATIONS = ["NFKC(全角→半角)", "空白の除去", "ふりがなは読み取り段で除去済み"]


def norm(s):
    """全角半角と空白を揃える。**掛けたことを記録に書く**(仕様 §2)。"""
    if s is None:
        return None
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(s)))


def col_index(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def col_letters(n):
    s = ""
    while n >= 0:
        s = chr(ord("A") + n % 26) + s
        n = n // 26 - 1
    return s


class Sheet(object):
    """1 シートを (列, 行) で引ける形にし、結合範囲を列の範囲として持つ。"""

    def __init__(self, name, raw):
        self.name = name
        self.cells = raw["cells"]
        self.merged = raw["merged"]
        self.rows = sorted({int(re.match(r"[A-Z]+(\d+)", r).group(1)) for r in self.cells})
        self.span = {}                       # 見出しのセル -> 結合の列の範囲
        for m in self.merged:
            a, b = m.split(":")
            ca, ra = re.match(r"([A-Z]+)(\d+)", a).groups()
            cb, _ = re.match(r"([A-Z]+)(\d+)", b).groups()
            self.span[a] = (col_index(ca), col_index(cb), int(ra))

    def get(self, col, row):
        c = self.cells.get("%s%d" % (col, row))
        return None if c is None else c["value"]

    def ref(self, col, row):
        return "%s%d" % (col, row)

    def header_span(self, col, row):
        """見出しセルの結合の列の範囲。結合が無ければ自分 1 列だけ。"""
        s = self.span.get(self.ref(col, row))
        if s is None:
            i = col_index(col)
            return (i, i)
        return (s[0], s[1])

    def value_in_span(self, span, row):
        """見出しの結合範囲の中から数を取る。**△ は符号**(仕様 §2)。

        返すのは (値, 値のセル参照, 符号のセル参照 or None)。
        """
        sign, sign_ref, found = 1, None, None
        for i in range(span[0], span[1] + 1):
            v = self.get(col_letters(i), row)
            if v is None:
                continue
            if isinstance(v, str) and v.strip() == MINUS:
                sign, sign_ref = -1, self.ref(col_letters(i), row)
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                found = (v, self.ref(col_letters(i), row))
        if found is None:
            return (None, None, sign_ref)
        return (sign * found[0], found[1], sign_ref)

    def value_row(self, row, span, limit=3):
        """見出しの行から下へ、その列に数が現れる最初の行(仕様 §2 の 2 様式)。"""
        for r in range(row, row + limit + 1):
            v, ref, _ = self.value_in_span(span, r)
            if v is not None:
                return r
        return None


# ---------------------------------------------------------------- 総括
def parse_soukatu(book):
    sh = Sheet("総括", book["総括"])
    head_row = next(r for r in sh.rows if norm(sh.get("A", r)) == "会計別")
    cols = {}
    for i in range(0, 12):
        L = col_letters(i)
        name = norm(sh.get(L, head_row))
        if name in ("歳入決算額", "歳出決算額", "差額"):
            cols[name] = {"header_ref": sh.ref(L, head_row),
                          "span": sh.header_span(L, head_row)}
    accounts, unidentified = [], []
    for r in sh.rows:
        name = sh.get("B", r)
        if not isinstance(name, str) or not name.strip():
            continue
        rec = {"name": name, "name_ref": sh.ref("B", r), "values": {}, "value_rows": {}}
        ok = True
        for key, c in cols.items():
            vr = sh.value_row(r, c["span"])
            if vr is None:
                ok = False
                continue
            v, vref, sref = sh.value_in_span(c["span"], vr)
            rec["values"][key] = v
            rec["value_rows"][key] = {"value_ref": vref, "sign_ref": sref,
                                      "header_ref": c["header_ref"]}
        rec["range_identified"] = ok
        (accounts if ok else unidentified).append(rec)
    return {"columns": {k: v["header_ref"] for k, v in cols.items()},
            "accounts": accounts, "unidentified": unidentified}


# ---------------------------------------------------------------- 決算書 歳出
KESSAN_COLS = ("予算現額", "支出済額", "翌年度繰越額", "不用額")


def parse_kessan(book):
    sh = Sheet("歳出", book["歳出"])
    blocks, titles = [], []
    for r in sh.rows:
        a = sh.get("A", r)
        if isinstance(a, str) and a.startswith("令和６年度東京都") and a.endswith("決算書"):
            titles.append((r, a))
    for n, (start, title) in enumerate(titles):
        end = titles[n + 1][0] - 1 if n + 1 < len(titles) else sh.rows[-1]
        blocks.append(parse_kessan_block(sh, start, end, title))
    return {"blocks": blocks, "block_count": len(blocks)}


def account_from_title(title):
    m = re.match(r"^令和６年度東京都(.+)歳入歳出決算書$", title)
    return m.group(1) if m else None


def parse_kessan_block(sh, start, end, title):
    rows = [r for r in sh.rows if start <= r <= end]
    head_row = next((r for r in rows if norm(sh.get("A", r)) == "科目"), None)
    cols = {}
    if head_row is not None:
        for i in range(0, 12):
            L = col_letters(i)
            name = norm(sh.get(L, head_row))
            if name in [norm(x) for x in KESSAN_COLS]:
                cols[name] = {"header_ref": sh.ref(L, head_row),
                              "span": sh.header_span(L, head_row)}
    kan, items, total, excluded = [], [], None, []
    for r in rows:
        a, b, c = sh.get("A", r), sh.get("B", r), sh.get("C", r)
        if isinstance(a, str) and norm(a) == "歳出合計":
            total = read_values(sh, r, cols, {"name": "歳出合計", "name_ref": sh.ref("A", r)})
            continue
        if isinstance(c, str) and norm(c) == "歳入歳出差引残額":
            excluded.append({"row": r, "why": "差引残額の行(仕様 §3 の除外)"})
            continue
        if isinstance(a, str) and CODE_RE.match(a.strip()) and isinstance(b, str) and b.strip():
            kan.append(read_values(sh, r, cols, {"code": a.strip(), "code_ref": sh.ref("A", r),
                                                 "name": b, "name_ref": sh.ref("B", r)}))
        elif isinstance(b, str) and CODE_RE.match(b.strip()) and isinstance(c, str) and c.strip():
            items.append(read_values(sh, r, cols, {"code": b.strip(), "code_ref": sh.ref("B", r),
                                                   "name": c, "name_ref": sh.ref("C", r),
                                                   "parent_row": max([k["row"] for k in kan] or [None])}))
        elif isinstance(a, str) and a.strip() and norm(a) not in ("科目", "款", "歳出"):
            excluded.append({"row": r, "why": "表題・見出しの行", "text": str(a)[:40]})
    return {"title": title, "account": account_from_title(title),
            "header_row": head_row, "columns": {k: v["header_ref"] for k, v in cols.items()},
            "kan": kan, "items": items, "total": total, "excluded": excluded}


def read_values(sh, row, cols, base):
    rec = dict(base)
    rec["row"] = row
    rec["values"], rec["evidence"] = {}, {}
    ok = bool(cols) and ("code" not in base or base.get("code"))
    for key, c in cols.items():
        vr = sh.value_row(row, c["span"])
        if vr is None:
            ok = False
            continue
        v, vref, sref = sh.value_in_span(c["span"], vr)
        rec["values"][key] = v
        rec["evidence"][key] = {"value_ref": vref, "sign_ref": sref,
                                "header_ref": c["header_ref"]}
    rec["range_identified"] = ok and len(rec["values"]) == len(cols)
    return rec


# ---------------------------------------------------------------- 事項別明細
# 予算現額の内訳(**△ が別のセルに入る列**を含む。仕様 §2)
MEISAI_BREAKDOWN = ("当初予算額", "補正予算額", "継続費及び繰越事業費繰越額",
                    "予備費支出及び流用増減")
MEISAI_COLS = dict([("計", "予算現額(計)"), ("支出済額", "支出済額"), ("不用額", "不用額")]
                   + [(c, c) for c in MEISAI_BREAKDOWN])


def parse_meisai(book):
    toc = Sheet("目次", book["目次"])
    mapping, toc_rows = {}, []
    for r in toc.rows:
        label, name = toc.get("B", r), toc.get("C", r)
        if isinstance(label, str) and isinstance(name, str) and norm(label) not in ("シート名",):
            key = norm(label)
            mapping[key] = {"account": name, "label": label, "label_ref": toc.ref("B", r),
                            "name_ref": toc.ref("C", r)}
            toc_rows.append(key)
    sheets, unmatched = [], []
    for sheet_name in book:
        if sheet_name == "目次":
            continue
        key = norm(sheet_name)
        if key not in mapping:
            unmatched.append(sheet_name)
            continue
        sheets.append(parse_meisai_sheet(Sheet(sheet_name, book[sheet_name]), mapping[key]))
    return {"toc_entries": len(mapping), "sheets": sheets,
            "sheets_without_toc_entry": unmatched,
            "toc_keys_without_sheet": [k for k in toc_rows
                                       if k not in {norm(s["sheet"]) for s in sheets}],
            "normalizations": NORMALIZATIONS}


def parse_meisai_sheet(sh, toc):
    head5 = next((r for r in sh.rows if norm(sh.get("A", r)) == "科目"), None)
    head6 = head5 + 1 if head5 is not None else None
    cols = {}
    if head6 is not None:
        for i in range(0, 30):
            L = col_letters(i)
            for row in (head5, head6):
                name = norm(sh.get(L, row))
                if name in MEISAI_COLS and name not in cols:
                    cols[name] = {"header_ref": sh.ref(L, row),
                                  "span": sh.header_span(L, row)}
    kan, items, moku = [], [], []
    for r in sh.rows:
        for col, bucket, name_col in (("A", kan, "B"), ("B", items, "C"), ("C", moku, "D")):
            v = sh.get(col, r)
            if isinstance(v, str) and CODE_RE.match(v.strip()) and r > (head6 or 0):
                # 明細の様式: **名前は 1 つ上の行**(仕様 §2 の 2 様式)
                name, name_ref = None, None
                for back in (1, 2):
                    cand = sh.get(name_col, r - back)
                    if isinstance(cand, str) and cand.strip():
                        name, name_ref = cand, sh.ref(name_col, r - back)
                        break
                rec = read_values(sh, r, cols, {"code": v.strip(), "code_ref": sh.ref(col, r),
                                                "name": name, "name_ref": name_ref})
                rec["range_identified"] = bool(rec["range_identified"] and name)
                bucket.append(rec)
                break
    return {"sheet": sh.name, "account": toc["account"], "toc_ref": toc["name_ref"],
            "columns": {k: v["header_ref"] for k, v in cols.items()},
            "kan": kan, "items": items, "moku": moku}


# ---------------------------------------------------------------- 段 3 整合
def check(name, scope, expected, actual, evidence, included, excluded=None):
    """1 件の照合。**範囲の証拠と値の一致を別の欄に持つ**(仕様 §4)。"""
    ri = bool(evidence) and all(evidence.values()) and bool(included)
    vm = (expected is not None and actual is not None and expected == actual)
    if ri and vm:
        state = "GROUNDED"
    elif ri and not vm:
        state = "VALUE_MISMATCH"
    elif (not ri) and vm:
        state = "UNVERIFIABLE"            # 値だけ合っても範囲の証拠が無ければ結ばない
    else:
        state = "POINTER_NOT_FOUND"
    return {"check": name, "scope": scope, "range_identified": ri, "value_match": vm,
            "state": state, "expected": expected, "actual": actual,
            "diff": (None if (expected is None or actual is None) else actual - expected),
            "evidence": evidence, "included": included, "excluded": excluded or []}


def sum_children(children, key):
    vals = [c["values"].get(key) for c in children]
    if any(v is None for v in vals) or not vals:
        return None, [c.get("code_ref") for c in children]
    return sum(vals), [c["evidence"][key]["value_ref"] for c in children]


def stage3(soukatu, kessan, meisai):
    out = []
    # C-1 決算書: 款 = Σ項 / C-2: 歳出合計 = Σ款
    for b in kessan["blocks"]:
        by_parent = collections.defaultdict(list)
        for it in b["items"]:
            by_parent[it.get("parent_row")].append(it)
        for k in b["kan"]:
            kids = by_parent.get(k["row"], [])
            for col in [norm(c) for c in KESSAN_COLS]:
                if col not in k["values"]:
                    continue
                total, refs = sum_children(kids, col)
                out.append(check(
                    "C-1 款 = Σ項 (%s)" % col, "%s / %s %s" % (b["account"], k.get("code"), k.get("name")),
                    k["values"][col], total,
                    {"kan_code": k.get("code_ref"), "kan_name": k.get("name_ref"),
                     "kan_value": k["evidence"][col]["value_ref"],
                     "header": k["evidence"][col]["header_ref"]},
                    refs, [{"row": k["row"], "why": "親自身の値行(二重計上の防止)"}]))
        for col in [norm(c) for c in KESSAN_COLS]:
            if not b["total"] or col not in b["total"].get("values", {}):
                continue
            total, refs = sum_children(b["kan"], col)
            out.append(check(
                "C-2 歳出合計 = Σ款 (%s)" % col, b["account"],
                b["total"]["values"][col], total,
                {"total_name": b["total"].get("name_ref"),
                 "total_value": b["total"]["evidence"][col]["value_ref"],
                 "header": b["total"]["evidence"][col]["header_ref"]},
                refs, [{"why": "差引残額・見出しの行(仕様 §3)"}]))
    # C-3 総括の歳出決算額 = 決算書の歳出合計(支出済額)  ★ファイルをまたぐ
    kessan_by_account = {norm(b["account"]): b for b in kessan["blocks"]}
    for a in soukatu["accounts"]:
        key = norm(a["name"])
        if key == norm("合計"):
            continue
        b = kessan_by_account.get(key)
        if b is None or not b.get("total"):
            out.append(check("C-3 総括 = 決算書(支出済額)", a["name"], a["values"].get("歳出決算額"),
                             None, {"soukatu_name": a["name_ref"]}, []))
            continue
        out.append(check(
            "C-3 総括 = 決算書(支出済額)", a["name"],
            a["values"].get("歳出決算額"), b["total"]["values"].get(norm("支出済額")),
            {"soukatu_name": a["name_ref"],
             "soukatu_value": a["value_rows"]["歳出決算額"]["value_ref"],
             "kessan_total": b["total"]["evidence"][norm("支出済額")]["value_ref"],
             "kessan_title_account": b["account"]},
            [b["total"]["evidence"][norm("支出済額")]["value_ref"]]))
    # C-4 総括の合計 = Σ会計
    tot = next((a for a in soukatu["accounts"] if norm(a["name"]) == norm("合計")), None)
    if tot:
        for key in ("歳入決算額", "歳出決算額"):
            kids = [a for a in soukatu["accounts"] if norm(a["name"]) != norm("合計")]
            vals = [a["values"].get(key) for a in kids]
            s = None if any(v is None for v in vals) else sum(vals)
            out.append(check("C-4 総括 合計 = Σ会計 (%s)" % key, "総括", tot["values"].get(key), s,
                             {"total_name": tot["name_ref"],
                              "total_value": tot["value_rows"][key]["value_ref"]},
                             [a["value_rows"][key]["value_ref"] for a in kids],
                             [{"why": "合計行そのもの(二重計上の防止)"}]))
    # C-5 明細: 款 = Σ項 / 項 = Σ目(計 と 支出済額)/ C-6 明細の款 = 決算書の款
    for s in meisai["sheets"]:
        kan_rows = sorted(k["row"] for k in s["kan"])
        for col in ("計", "支出済額"):
            if col not in (s["columns"] or {}):
                continue
            for k in s["kan"]:
                kids = children_between(s["items"], k["row"], kan_rows)
                total, refs = sum_children(kids, col)
                out.append(check(
                    "C-5 明細 款 = Σ項 (%s)" % col,
                    "%s / %s %s" % (s["account"], k.get("code"), k.get("name")),
                    k["values"].get(col), total,
                    {"kan_code": k.get("code_ref"), "kan_name": k.get("name_ref"),
                     "kan_value": (k["evidence"].get(col) or {}).get("value_ref")},
                    refs, [{"row": k["row"], "why": "親自身の値行"}]))
            item_rows = sorted(i["row"] for i in s["items"])
            for it in s["items"]:
                kids = children_between(s["moku"], it["row"], item_rows)
                total, refs = sum_children(kids, col)
                out.append(check(
                    "C-5 明細 項 = Σ目 (%s)" % col,
                    "%s / %s %s" % (s["account"], it.get("code"), it.get("name")),
                    it["values"].get(col), total,
                    {"item_code": it.get("code_ref"), "item_name": it.get("name_ref"),
                     "item_value": (it["evidence"].get(col) or {}).get("value_ref")},
                    refs, [{"row": it["row"], "why": "親自身の値行"}]))
        # C-7 明細の「計」= 当初予算額 + 補正予算額 + 繰越 + 流用増減(**△ の符号を通す列**)
        parts = [c for c in MEISAI_BREAKDOWN if c in (s["columns"] or {})]
        if "計" in (s["columns"] or {}) and len(parts) == len(MEISAI_BREAKDOWN):
            for level, rowsets in (("款", s["kan"]), ("項", s["items"]), ("目", s["moku"])):
                for x in rowsets:
                    vals = [x["values"].get(c) for c in parts]
                    total = None if any(v is None for v in vals) else sum(vals)
                    ev = {"code": x.get("code_ref"), "name": x.get("name_ref"),
                          "kei": (x["evidence"].get("計") or {}).get("value_ref")}
                    out.append(check(
                        "C-7 明細 計 = 当初+補正+繰越+流用 (%s)" % level,
                        "%s / %s %s" % (s["account"], x.get("code"), x.get("name")),
                        x["values"].get("計"), total, ev,
                        [(x["evidence"].get(c) or {}).get("value_ref") for c in parts],
                        [{"why": "符号は △ のセルから取る(仕様 §2)",
                          "sign_refs": [(x["evidence"].get(c) or {}).get("sign_ref")
                                        for c in parts]}]))
        b = kessan_by_account.get(norm(s["account"].replace("東京都", "", 1)))
        if b is None:
            continue
        kessan_kan = {norm(k.get("name")): k for k in b["kan"]}
        for k in s["kan"]:
            kk = kessan_kan.get(norm(k.get("name")))
            if kk is None:
                continue
            out.append(check(
                "C-6 明細の款 = 決算書の款(支出済額)", "%s / %s" % (s["account"], k.get("name")),
                kk["values"].get(norm("支出済額")), k["values"].get("支出済額"),
                {"meisai_code": k.get("code_ref"), "meisai_name": k.get("name_ref"),
                 "kessan_code": kk.get("code_ref"), "kessan_name": kk.get("name_ref")},
                [(k["evidence"].get("支出済額") or {}).get("value_ref")]))
    return out


def children_between(children, parent_row, sibling_rows):
    """親の行から**次の同じ階層の行まで**の子だけを取る(孫は別の層で数える)。"""
    nxt = min([r for r in sibling_rows if r > parent_row] or [10 ** 9])
    return [c for c in children if parent_row < c["row"] < nxt]


def main():
    books = {}
    for f in (SOUKATU, KESSAN, MEISAI):
        p = os.path.join(CACHE, f)
        if not os.path.exists(p):
            raise SystemExit("材料が無い: %s" % f)
        books[f], _ = M1.read(p)
    soukatu = parse_soukatu(books[SOUKATU])
    kessan = parse_kessan(books[KESSAN])
    meisai = parse_meisai(books[MEISAI])

    stage2 = {
        "soukatu": {"accounts": len(soukatu["accounts"]),
                    "unidentified": len(soukatu["unidentified"]),
                    "columns": soukatu["columns"]},
        "kessan": {"blocks": kessan["block_count"],
                   "kan": sum(len(b["kan"]) for b in kessan["blocks"]),
                   "items": sum(len(b["items"]) for b in kessan["blocks"]),
                   "totals": sum(1 for b in kessan["blocks"] if b["total"]),
                   "rows_excluded": sum(len(b["excluded"]) for b in kessan["blocks"]),
                   "not_identified": sum(1 for b in kessan["blocks"]
                                         for x in b["kan"] + b["items"]
                                         if not x["range_identified"])},
        "meisai": {"toc_entries": meisai["toc_entries"], "sheets": len(meisai["sheets"]),
                   "sheets_without_toc_entry": meisai["sheets_without_toc_entry"],
                   "toc_keys_without_sheet": meisai["toc_keys_without_sheet"],
                   "kan": sum(len(s["kan"]) for s in meisai["sheets"]),
                   "items": sum(len(s["items"]) for s in meisai["sheets"]),
                   "moku": sum(len(s["moku"]) for s in meisai["sheets"]),
                   "not_identified": sum(1 for s in meisai["sheets"]
                                         for x in s["kan"] + s["items"] + s["moku"]
                                         if not x["range_identified"])},
        "normalizations": NORMALIZATIONS}

    checks = stage3(soukatu, kessan, meisai)
    by_check = collections.Counter(c["check"].split(" (")[0] for c in checks)
    by_state = collections.Counter(c["state"] for c in checks)
    grouped = collections.defaultdict(collections.Counter)
    for c in checks:
        grouped[c["check"].split(" (")[0]][c["state"]] += 1

    print("=== 段 2 構造の抽出 ===")
    print(" 総括: 会計 %d / 同定できなかった %d" % (stage2["soukatu"]["accounts"],
                                                   stage2["soukatu"]["unidentified"]))
    print(" 決算書: ブロック %d / 款 %d / 項 %d / 歳出合計 %d / 除いた行 %d / 同定できなかった %d"
          % (stage2["kessan"]["blocks"], stage2["kessan"]["kan"], stage2["kessan"]["items"],
             stage2["kessan"]["totals"], stage2["kessan"]["rows_excluded"],
             stage2["kessan"]["not_identified"]))
    print(" 明細: 目次 %d / シート %d / 款 %d / 項 %d / 目 %d / 同定できなかった %d"
          % (stage2["meisai"]["toc_entries"], stage2["meisai"]["sheets"],
             stage2["meisai"]["kan"], stage2["meisai"]["items"], stage2["meisai"]["moku"],
             stage2["meisai"]["not_identified"]))
    print("=== 段 3 集計の整合(合格線は無い) ===")
    for name in sorted(grouped):
        g = grouped[name]
        print(" %-34s 件数 %5d  GROUNDED %5d  VALUE_MISMATCH %4d  UNVERIFIABLE %3d  POINTER_NOT_FOUND %3d"
              % (name, sum(g.values()), g["GROUNDED"], g["VALUE_MISMATCH"],
                 g["UNVERIFIABLE"], g["POINTER_NOT_FOUND"]))
    print(" 合計 %d / %s" % (len(checks), dict(by_state)))

    rec = {"purpose": "M-2 段 2・段 3。**接続精度ではない**(仕様 §5)",
           "spec": "docs/DOMAIN1_M2_SPEC_2026-10-15.md",
           "source": "東京都オープンデータカタログ / 東京都会計管理局 / CC BY 4.0",
           "stage2": stage2,
           "stage3": {"by_check": dict(by_check), "by_state": dict(by_state),
                      "grouped": {k: dict(v) for k, v in grouped.items()},
                      "checks": len(checks),
                      "not_grounded": [c for c in checks if c["state"] != "GROUNDED"]}}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
