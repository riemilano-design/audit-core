# -*- coding: utf-8 -*-
"""X-2 の計数器に**歯**を当てる(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §4-1)。

**生成より先に走らせ、生成より先に commit する。**

> X-2 = 0 は、**計数器が動いていないだけ**かもしれない
> (記憶 `zero-count-may-be-my-own-bug` / `absence-of-false-positive-is-not-a-fix`)。

| 歯 | 人工の主張 | 期待 |
|---|---|---|
| **歯-1** | **抜粋に無い行**の値を主張する | **X-2対称 = 1** |
| **歯-2** | **抜粋に在る行**の値を主張する | **X-2対称 = 0** |
| **歯-3** | **昇格した別名の行**を主張する | **X-2対称 = 0・X-2非対称 = 1** |

歯-3 が示すのは「**段 9 の数え方をそのまま当てると偽の X-2 が出る**」という
封 §4 の主張が**実測で正しい**ことである。

**人工材料での診断結果は、実データでの安全性の証明とは分けて記録する**(人間の指示)。
**この歯は engine の安全性を何も示さない。計数器が数えられることだけを示す。**

    python3 measure/sheet_m11_x2_teeth_2026-10-16.py
"""
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m11_material_2026-10-16.json")
OUT = os.path.join(FX, "m11_x2_teeth_2026-10-16.json")
SEAL = "docs/DOMAIN1_M11_SEAL_2026-10-16.md"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


X2 = _mod("x2_for_teeth", "sheet_m11_x2_2026-10-16.py")
OPP11 = X2.OPP11
SE = OPP11.SE
E = OPP11.E
M2 = OPP11.M2
norm = OPP11.norm


def bind_of(scope, level, parent, name):
    """**人工の bind**。engine を通さずに計数器だけを当てる(歯の最小単位)。"""
    return {"state": "GROUNDED",
            "evidence": {"scope": scope, "level": level, "parent": parent,
                         "name": name}}


def checks_of(t1, t2, t3):
    """**歯の期待を 1 か所に置く。**(名, 通ったか, 実測)の一覧を返す。

    `main()` の中に字で書くと、**変異の走りでは記録を作り直さないので黙る**
    (2026-10-16 の変異 S8 で実測。P-6 でも同じ型を踏んだ)。
    **門が壊した入力を食わせて、期待の 1 本ずつが False になることを確かめられる。**
    """
    return [
        ("歯-1 抜粋に無い行 → X-2対称 = 1", t1["X-2対称"] == 1, t1["X-2対称"]),
        ("歯-1 同じ行は X-2三欄 でも数えられる", t1["X-2三欄"] >= 1, t1["X-2三欄"]),
        ("歯-2 抜粋に在る行 → X-2対称 = 0", t2["X-2対称"] == 0, t2["X-2対称"]),
        ("歯-3 昇格した別名の行 → X-2対称 = 0", t3["X-2対称"] == 0, t3["X-2対称"]),
        ("**歯-3 同じ行を段 9 の数え方で見ると X-2非対称 = 1**",
         t3["X-2非対称"] == 1, t3["X-2非対称"]),
        ("歯-3 会計を外した 3 欄では 0(別名表に依らない)",
         t3["X-2三欄"] == 0, t3["X-2三欄"]),
    ]


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(当て直さない)" % OUT)
    mat = json.load(io.open(MAT, encoding="utf-8"))
    cells = OPP11.OPP.cells_of(OPP11.OPP.extract_of(mat))
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    args = (M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
            M2.parse_meisai(books[M2.MEISAI]))
    raw = E.fix_total_level(E.build_index(*args))
    al = SE.alias_table(raw)
    table = al["table"]
    fold = X2.alias_fold(table)
    ents = E.canonicalize(raw, al)

    inside = {X2.key4(c["scope"], c["level"], c["parent"], c["name"], fold)
              for c in cells}
    # 歯-1 の材料: **索引に在って抜粋に無い行**
    outside = None
    for e in ents:
        k = X2.key4(e["scope"], e["level"], e["parent"], e["name"], fold)
        if k not in inside:
            outside = e
            break
    if outside is None:
        raise SystemExit("抜粋の外の行が無い ― 歯-1 を当てられない")
    # 歯-2 の材料: **抜粋に在る行**(正本の字で)
    c_in = cells[0]
    # 歯-3 の材料: **抜粋が別名の形で印字している行**(昇格した会計)
    alias_cell = None
    for c in cells:
        if norm(c["scope"]) in fold:
            alias_cell = c
            break
    if alias_cell is None:
        raise SystemExit("抜粋に昇格した別名の行が無い ― 歯-3 を当てられない")

    t1 = X2.count({"T1": bind_of(outside["scope"], outside["level"],
                                 outside["parent"], outside["name"])},
                  cells, table)
    t2 = X2.count({"T2": bind_of(fold.get(norm(c_in["scope"]), c_in["scope"]),
                                 c_in["level"], c_in["parent"], c_in["name"])},
                  cells, table)
    # 新 engine は別名を正本に直すので、**正本の字で**結ぶ
    t3 = X2.count({"T3": bind_of(fold[norm(alias_cell["scope"])],
                                 alias_cell["level"], alias_cell["parent"],
                                 alias_cell["name"])},
                  cells, table)

    checks = checks_of(t1, t2, t3)
    failed = [name for name, ok, _ in checks if not ok]
    rec = {"seal": SEAL, "step": "封 §4-1。**生成より先に当てた。費用 0 USD**",
           "material": "fixtures/sheet/m11_material_2026-10-16.json",
           "artificial": True,
           "**この結果は engine の安全性を何も示さない**":
               ("計数器が数えられることだけを示す。"
                "**人工材料での診断結果は、実データでの安全性の証明とは分けて記録する**"
                "(人間の指示 2026-10-16)"),
           "歯-1 の行(抜粋に無い)": {"会計": outside["scope"],
                              "階層": outside["level"],
                              "親": outside["parent"], "科目名": outside["name"]},
           "歯-2 の行(抜粋に在る)": {"会計": c_in["scope"], "階層": c_in["level"],
                              "親": c_in["parent"], "科目名": c_in["name"]},
           "歯-3 の行(抜粋は別名の形)": {
               "抜粋の字": alias_cell["scope"],
               "engine が結ぶ正本": fold[norm(alias_cell["scope"])],
               "階層": alias_cell["level"], "親": alias_cell["parent"],
               "科目名": alias_cell["name"]},
           "歯-1": {k: v for k, v in t1.items() if not k.endswith("の明細")},
           "歯-2": {k: v for k, v in t2.items() if not k.endswith("の明細")},
           "歯-3": {k: v for k, v in t3.items() if not k.endswith("の明細")},
           "検査": [{"名": n, "通った": ok, "実測": got} for n, ok, got in checks],
           "すべて通ったか": not failed, "落ちた検査": failed,
           "結論": ("**段 9 の数え方をそのまま当てると偽の X-2 が出る**ことを実測で示した"
                  "(歯-3)。だから合否には **X-2対称**を使い、"
                  "**非対称は開示だけ**にする(封 §4)")}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for n, ok, got in checks:
        print("%-52s %s(実測 %s)" % (n, "通った" if ok else "**落ちた**", got))
    print("**すべて通ったか: %s**" % (not failed))
    print("->", OUT)


if __name__ == "__main__":
    main()
