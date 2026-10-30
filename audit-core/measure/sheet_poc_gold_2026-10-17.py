# -*- coding: utf-8 -*-
"""PoC 第 1 便の**正解集合**を機械で作る(封 docs/DOMAIN1_POC_ABC_SEAL_2026-10-17.md §2)。

**採点より先に commit する。**

**2 段構え**(人間の修正 2026-10-17):

  第 1 段 **値の分類**。抜粋の中でその金額を持つセルを数える。
          1 件 = 値の候補が一意 / 2 件以上 = 値だけでは曖昧 / 0 件 = 値が不一致。
          **この段では正解と断定しない。**
  第 2 段 **独立した確認**。**Core の規則を一切使わない** ―
          G-独立-1 値の候補が一意
          G-独立-2 科目名が主張の文にそのまま出る
          G-独立-3 親の成分(款/項)か会計名(印字形・正本形)が同じ文に出る
          G-独立-4 列が同じ文に出る(§2-4 の表層形を許す)
          **4 つすべてで正解集合。1 つでも欠けたら別枠(欠けた条件を記録)。**

**使うのは「読む・解析する」部分と「文に字が在るか」だけである。**
**接続の規則・別名表・親の絞り・6 欄の鍵・値の照合は 1 つも使わない。**

    python3 measure/sheet_poc_gold_2026-10-17.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m11_material_2026-10-16.json")
BINDS = os.path.join(FX, "m11_binds_2026-10-16.json")
OUT = os.path.join(FX, "poc_gold_2026-10-17.json")
SEAL = "docs/DOMAIN1_POC_ABC_SEAL_2026-10-17.md"

# 封 §2-4。**盲検ではない(`予算現在額` は報告文を読んでから入れた)。**
# **結果を見てから書き換えない。**
SURFACE = {
    "予算現額": ("予算現額", "予算現在額", "計"),
    "支出済額": ("支出済額",),
    "不用額": ("不用額",),
    "補正予算額": ("補正予算額",),
}
# 封 §2-2 の G-独立-3。印字形 → 正本形(**会計名が文に出るかを見るためだけ**に使う。
# 接続の判定には使わない)。字は**抜粋の印字から機械で作る**。
PREFIX = "東京都"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


# **読む・解析する部分だけを借りる**(封 §2-3 で開示した共有部分)
OPP = _mod("opp9_for_gold", "sheet_m9_opportunity_2026-10-16.py")


def scope_forms(printed):
    """会計名の**印字形と正本形**を返す。`東京都○○会計` → (印字, 正本)。

    **別名表を使わない。**印字の字から接頭辞を外すだけである
    (正本かどうかの判定はしない。**文に出るかを見るためだけ**に使う)。
    """
    p = (printed or "").strip()
    out = {p}
    if p.startswith(PREFIX) and len(p) > len(PREFIX):
        out.add(p[len(PREFIX):])
    return tuple(sorted(out))


def classify_value(value, cells):
    """**第 1 段**: 値の分類。(分類, 当たったセル) を返す。**正解と断定しない。**"""
    hits = [c for c in cells if c["value"] == value]
    if len(hits) == 1:
        return "値の候補が一意", hits
    if len(hits) > 1:
        return "値だけでは曖昧", hits
    return "値が不一致", hits


def independent_check(cell, sentence, strict_column=False):
    """**第 2 段**: 独立した確認。(通った条件, 欠けた条件) を返す。

    **Core の規則を 1 つも使わない。**文にその字がそのまま在るかだけを見る。
    判定を 1 か所に置く ― 字で書くと「全部通る材料」で変異が黙る。
    """
    ok, miss = [], []
    name = (cell["name"] or "").strip()
    if name and name in sentence:
        ok.append("G-独立-2 科目名が文に在る")
    else:
        miss.append("G-独立-2 科目名が文に無い(%r)" % name)
    parents = [x.strip() for x in (cell["parent"] or "").split(">") if x.strip()]
    scopes = scope_forms(cell["scope"])
    hit3 = [x for x in parents + list(scopes) if x and x in sentence]
    if hit3:
        ok.append("G-独立-3 親か会計名が文に在る(%s)" % "・".join(hit3[:2]))
    else:
        miss.append("G-独立-3 親も会計名も文に無い")
    col = (cell["column"] or "").strip()
    forms = (col,) if strict_column else SURFACE.get(col, (col,))
    hit4 = [f for f in forms if f and f in sentence]
    if hit4:
        ok.append("G-独立-4 列が文に在る(%s)" % hit4[0])
    else:
        miss.append("G-独立-4 列が文に無い(%s / 許した字 %s)"
                    % (col, "・".join(forms)))
    return ok, miss


def build(strict_column=False):
    mat = json.load(io.open(MAT, encoding="utf-8"))
    cells = OPP.cells_of(OPP.extract_of(mat))
    claims = json.load(io.open(BINDS, encoding="utf-8"))["claims"]
    rows, gold, apart = [], [], []
    for c in sorted(claims, key=lambda x: x["id"]):
        kind, hits = classify_value(c["value"], cells)
        rec = {"id": c["id"], "値": c["value"], "文": c["sentence"],
               "第 1 段": kind, "候補の数": len(hits)}
        if kind != "値の候補が一意":
            rec["正解"] = None
            rec["別枠の理由"] = ["G-独立-1 %s" % kind]
            rec["候補"] = [{k: h[k] for k in ("scope", "level", "parent", "name",
                                              "column")} for h in hits[:4]]
            apart.append(rec["id"])
        else:
            cell = hits[0]
            ok, miss = independent_check(cell, c["sentence"], strict_column)
            rec["通った条件"] = ok
            if miss:
                rec["正解"] = None
                rec["別枠の理由"] = miss
                apart.append(rec["id"])
            else:
                rec["正解"] = {"会計(印字)": cell["scope"],
                             "会計(接頭辞なし)": scope_forms(cell["scope"])[0]
                             if len(scope_forms(cell["scope"])) == 1
                             else [s for s in scope_forms(cell["scope"])
                                   if not s.startswith(PREFIX)][0],
                             "階層": cell["level"], "親": cell["parent"],
                             "科目名": cell["name"], "列": cell["column"],
                             "値": cell["value"], "表": cell.get("表")}
                gold.append(rec["id"])
        rows.append(rec)
    return {"rows": rows, "gold": gold, "apart": apart, "cells": len(cells)}


def main():
    if os.path.exists(OUT):
        raise SystemExit("正解集合が既に在る: %s(作り直さない)" % OUT)
    b = build(strict_column=False)
    strict = build(strict_column=True)
    kinds = collections.Counter(r["第 1 段"] for r in b["rows"])
    miss = collections.Counter()
    for r in b["rows"]:
        for m in r.get("別枠の理由") or []:
            miss[m.split("(")[0].strip()] += 1
    rec = {"seal": SEAL,
           "step": "封 §9 の 2。**採点より先に commit する。費用 0 USD**",
           "material": "fixtures/sheet/m11_material_2026-10-16.json",
           "claims": "fixtures/sheet/m11_binds_2026-10-16.json の claims(35 件)",
           "抜粋の値のセル": b["cells"],
           "**Core の規則を使っていない**": (
               "使ったのは帳簿を読む・解析する部分と、抜粋を行に開く部分と、"
               "**主張の文にその字がそのまま在るか**だけである。"
               "**接続の規則・別名表・親の絞り・6 欄の鍵・値の照合は 1 つも使わない。**"
               "**だから「完全に独立した正解」ではない** ― "
               "独立しているのは**Core の判定規則から**である(封 §2-3)"),
           "第 1 段(値の分類。**正解と断定しない**)": dict(kinds),
           "正解集合": {"件数": len(b["gold"]), "ids": b["gold"]},
           "別枠": {"件数": len(b["apart"]), "ids": b["apart"],
                  "理由ごと": dict(miss),
                  "注": "**正解不明として数え、どちらが正しいかを決めない**(封 §8 の 6)"},
           "厳格な列(表層形なし)": {
               "正解集合": len(strict["gold"]),
               "減った件数": len(b["gold"]) - len(strict["gold"]),
               "ids": strict["gold"],
               "注": ("**封 §2-4。`予算現在額` を許さない数。**"
                      "表層形の表は盲検でないので、**この数も必ず併記する**")},
           "列の表層形(盲検ではない)": {k: list(v) for k, v in SURFACE.items()},
           "rows": b["rows"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("抜粋の値のセル %d / 主張 %d" % (b["cells"], len(b["rows"])))
    print("第 1 段:", json.dumps(dict(kinds), ensure_ascii=False))
    print("**正解集合 %d 件 / 別枠 %d 件**" % (len(b["gold"]), len(b["apart"])))
    print("別枠の理由:")
    for k, v in sorted(miss.items(), key=lambda x: -x[1]):
        print("   %-44s %d" % (k, v))
    print("**厳格な列(表層形なし)の正解集合 %d 件(−%d)**"
          % (len(strict["gold"]), len(b["gold"]) - len(strict["gold"])))
    print("->", OUT)


if __name__ == "__main__":
    main()
