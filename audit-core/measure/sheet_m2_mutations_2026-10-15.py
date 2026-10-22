# -*- coding: utf-8 -*-
"""M-2 段 3 の「全部 GROUNDED」が**外れようがない数でない**ことを測る(2026-10-15)。

段 3 の検査は文書自身の内部整合を使う。全部一致したときは、まず
**「この検査は外れうるのか」**を確かめなければ、数に意味が無い。
ここでは規則を 1 つずつ壊して、検査がいくつ赤くなるかを数える。

**これは合否ではない。**壊して赤くならない規則が在れば、それは
「段 3 では通っていない規則」であり、そう記録する(実際に △ の規則がそうだった)。

usage: python3 measure/sheet_m2_mutations_2026-10-15.py
"""
import collections
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TARGET = os.path.join(HERE, "sheet_m2_structure_2026-10-15.py")
OUT = os.path.join(ROOT, "fixtures", "sheet", "m2_mutations_2026-10-15.json")


def fresh():
    spec = importlib.util.spec_from_file_location("m2_%d" % len(sys.modules), TARGET)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run(m):
    books = {}
    for f in (m.SOUKATU, m.KESSAN, m.MEISAI):
        books[f], _ = m.M1.read(os.path.join(m.CACHE, f))
    s = m.parse_soukatu(books[m.SOUKATU])
    k = m.parse_kessan(books[m.KESSAN])
    mi = m.parse_meisai(books[m.MEISAI])
    checks = m.stage3(s, k, mi)
    return {"checks": len(checks),
            "states": dict(collections.Counter(c["state"] for c in checks)),
            "not_grounded_by_check": dict(collections.Counter(
                c["check"].split(" (")[0] for c in checks if c["state"] != "GROUNDED")),
            "sheets_without_toc_entry": len(mi["sheets_without_toc_entry"])}


def mut_all_children(m):
    m.children_between = lambda children, parent_row, sibling_rows: list(children)


def mut_shift_value_row(m):
    _vr = m.Sheet.value_row
    m.Sheet.value_row = lambda self, row, span, limit=3: (
        None if _vr(self, row, span, limit) is None else _vr(self, row, span, limit) + 1)


def mut_ignore_minus(m):
    m.MINUS = "＠この字は材料に無い＠"


def mut_absolute_value(m):
    _vis = m.Sheet.value_in_span

    def flipped(self, span, row):
        v, vref, sref = _vis(self, span, row)
        return (None if v is None else (abs(v) if sref else v), vref, sref)
    m.Sheet.value_in_span = flipped


def mut_mix_grandchildren(m):
    _st3 = m.stage3

    def stage3_mixed(s, k, mi):
        for sh in mi["sheets"]:
            sh["items"] = sh["items"] + sh["moku"]
        return _st3(s, k, mi)
    m.stage3 = stage3_mixed


def mut_wrong_column(m):
    _sc = m.sum_children
    m.sum_children = lambda children, key: _sc(
        children, "不用額" if key == m.norm("支出済額") else key)


def mut_no_normalization(m):
    m.norm = lambda s: None if s is None else str(s)


def mut_double_one_child(m):
    _sc = m.sum_children
    m.sum_children = lambda children, key: _sc(list(children) + list(children[:1]), key)


MUTATIONS = [
    ("1 子の範囲を「次の兄弟まで」ではなく全部にする", mut_all_children),
    ("2 値の行を 1 行ずらす", mut_shift_value_row),
    ("3 △ を符号として見ない", mut_ignore_minus),
    ("4 △ を無視して絶対値を使う", mut_absolute_value),
    ("5 孫(目)を項の一覧に混ぜる", mut_mix_grandchildren),
    ("6 列の対応を 1 つずらす", mut_wrong_column),
    ("7 全角半角の正規化を外す", mut_no_normalization),
    ("8 子を 1 件だけ二重に数える", mut_double_one_child),
]


def main():
    base = run(fresh())
    print("0 そのまま                                         %s" % base["states"])
    rows = []
    for name, patch in MUTATIONS:
        m = fresh()
        patch(m)
        r = run(m)
        silent = (r["states"] == base["states"] and r["checks"] == base["checks"])
        rows.append({"mutation": name, "result": r, "silent": silent})
        print("%-48s 検査 %4d  %s%s" % (name, r["checks"], r["states"],
                                        "   ← **黙った**" if silent else ""))
    rec = {"purpose": "段 3 の検査が外れうることを確かめる変異。**合否ではない**",
           "spec": "docs/DOMAIN1_M2_SPEC_2026-10-15.md",
           "base": base, "mutations": rows,
           "silent": [r["mutation"] for r in rows if r["silent"]]}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print("黙った変異:", rec["silent"] or "無し")
    print("->", OUT)


if __name__ == "__main__":
    main()
