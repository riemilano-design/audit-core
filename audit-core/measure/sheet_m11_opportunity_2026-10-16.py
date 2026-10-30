# -*- coding: utf-8 -*-
"""段 11 の**機会の件数**を、生成の前に数える(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §11 の 3)。

単位は**行(抜粋の値のセル)**で、主張ではない ― 生成前には主張が存在しない。

**O-1〜O-7 は段 9 の script をそのまま呼ぶ**(`sheet_m9_opportunity_2026-10-16.py`。
sha `eace3e1bbd2c480b`)。数え方を書き直さない。

**O-8 だけが新しい ― X-2 の機会である**(封 §4・§9 の限界 9)。
段 9 は X-2 = 0 件だったが、**それは engine が抜粋の外に結べなかったからではない。**
engine は材料の全部を索引に持つので、**抜粋に無い行にも結べる。**
だから「結べる先が抜粋の外にどれだけ在るか」を数える。

  O-8  **索引に在って抜粋に無い行**の数(engine が結べる先。別名表は両側に当てる)
  O-8′ **抜粋に無い行だけが持つ値**の数
       ― 報告文がこの値を引けば **X-2 が発火する**。これが本当の機会である

**この数を見て表を増やしたり減らしたりしない。標本を選び直さない。生成文を誘導しない。**

    python3 measure/sheet_m11_opportunity_2026-10-16.py
"""
import collections
import importlib.util
import io
import json
import os
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m11_material_2026-10-16.json")
OUT = os.path.join(FX, "m11_opportunity_2026-10-16.json")
SEAL = "docs/DOMAIN1_M11_SEAL_2026-10-16.md"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


OPP = _mod("opp9_for_m11opp", "sheet_m9_opportunity_2026-10-16.py")
SE = _mod("sainyuu_for_m11opp", "sheet_sainyuu_engine_2026-10-16.py")
E = OPP.E
M2 = OPP.M2
norm = OPP.norm


def alias_fold(table):
    """別名 → 正本の畳み込みを返す。**両側に同じものを当てるために 1 か所に置く。**"""
    return {norm(k): norm(v["canonical"]) for k, v in table.items()}


def key4(scope, level, parent, name, fold):
    """`(会計, 階層, 親, 科目名)`。**会計は別名表で畳む**(両側に同じ正規化)。

    記憶 `normalize-both-sides-of-a-comparison`。**片側だけ畳むと嘘の差が出る。**
    """
    s = norm(scope)
    return (fold.get(s, s), norm(level), norm(parent) or "", norm(name))


def x2_opportunity(cells, entries, fold):
    """**O-8 / O-8′**: engine が結べる先のうち抜粋に無いもの(封 §4)。

    判定を 1 か所に置く ― 字で書くと「抜粋の外が 0 件」の材料で変異が黙る。
    """
    in_extract = {key4(c["scope"], c["level"], c["parent"], c["name"], fold)
                  for c in cells}
    ext_vals = {c["value"] for c in cells}
    outside, outside_vals = set(), set()
    for e in entries:
        k = key4(e["scope"], e["level"], e["parent"], e["name"], fold)
        if k not in in_extract:
            outside.add(k)
            outside_vals.add(e["value"])
    return {"O-8 索引に在って抜粋に無い行": len(outside),
            "O-8′ 抜粋に無い行だけが持つ値": len(outside_vals - ext_vals),
            "抜粋の行": len(in_extract), "抜粋の値": len(ext_vals),
            "索引の行": len({key4(e["scope"], e["level"], e["parent"], e["name"], fold)
                           for e in entries}),
            "注": ("**X-2 = 0 は「engine が抜粋の外に結べなかった」ことではない。**"
                   "結べる先は O-8 件在る。**報告文が O-8′ の値を引けば X-2 は発火する。**"
                   "引くかどうかは生成まで分からないので、"
                   "**計数器の歯は人工材料で別に当てる**(封 §4-1)")}


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(数え直さない)" % OUT)
    tmp = tempfile.mkdtemp(prefix="m11opp_")
    old_mat, old_out = OPP.MAT, OPP.OUT
    OPP.MAT, OPP.OUT = MAT, os.path.join(tmp, "base.json")
    try:
        OPP.main()                      # **O-1〜O-7 は段 9 の字のまま**
        rec = json.load(io.open(OPP.OUT, encoding="utf-8"))
    finally:
        OPP.MAT, OPP.OUT = old_mat, old_out

    mat = json.load(io.open(MAT, encoding="utf-8"))
    cells = OPP.cells_of(OPP.extract_of(mat))
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    args = (M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
            M2.parse_meisai(books[M2.MEISAI]))
    raw = E.fix_total_level(E.build_index(*args))
    al_new = SE.alias_table(raw)                 # **新 engine の別名表**
    ents_new = E.canonicalize(raw, al_new)
    fold = alias_fold(al_new["table"])

    rec["seal"] = SEAL
    rec["material"] = "fixtures/sheet/m11_material_2026-10-16.json"
    rec["purpose"] = ("段 11 の**機会**の件数。**生成の前に数えた。**"
                      "単位は行(値のセル)で、主張ではない")
    rec["O-1〜O-7 の出どころ"] = ("measure/sheet_m9_opportunity_2026-10-16.py の main()"
                             "(**数え方を書き直していない**)")
    rec["O-8 X-2 の機会(新。封 §4)"] = x2_opportunity(cells, ents_new, fold)
    rec["別名表"] = {"新 engine で通った": len(al_new["table"]),
                  "歳入で昇格した": len(al_new["promoted_by_sainyuu"]),
                  "未確認のまま": len(al_new["unconfirmed"]),
                  "注": ("**新 engine では未確認が 0 件になる見込みである**"
                         "(封 §3)。だから A-1・A-3 は構造的に 0 になり、"
                         "③の発火機会は**旧 engine でしか観測できない**")}
    rec["limit"] = list(rec["limit"]) + [
        "**O-8 > 0 でも X-2 は発火しない場合がある。**報告文が抜粋の外の値を"
        "引かなければ主張が立たない。**0 件だったときは「機会は在ったが発火しなかった」"
        "と書き、安全性の証明にしない**(封 §9 の限界 9)",
        "**O-8 は別名表を両側に当てて数えた。**片側だけ畳むと、昇格した 18 会計の行が"
        "全部「抜粋に無い」に数えられる(封 §4 の非対称の罠そのもの)",
    ]
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in rec.items():
        if k.startswith("O-") or k == "別名表":
            print("%s: %s" % (k, json.dumps(v, ensure_ascii=False)[:300]))
    print("->", OUT)


if __name__ == "__main__":
    main()
