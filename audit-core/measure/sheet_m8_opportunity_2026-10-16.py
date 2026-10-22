# -*- coding: utf-8 -*-
"""段 8 の**機会の件数**を、生成の前に数える(封 §8 の 3。人間の指示 2026-10-16)。

単位は**行(抜粋の値のセル)**で、主張ではない ― 生成前には主張が存在しない。
**同じものを生成後に主張の単位でも数える。単位が違うので並べて比べない。**

数えるもの:
  O-1 親の成分が**全部抜粋の中に書かれている**セル(書き手が親を名指せる)
  O-2 O-1 のうち、**親を使わないと 4 欄で一意にならない**セル(親が効く)
  O-3 列の見出しが抜粋に在るセル / 無いセル
  O-4 **旧では保留・新では接続になりうる**セル
  **O-5 抜粋の行のうち、6 欄すべてが抜粋から読めるセル**(段 7 の失敗を測る指標)
  **O-6 表 2 と表 3 のどちらが O-4 を持つか**(増分がどこから来るか)

    python3 measure/sheet_m8_opportunity_2026-10-16.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m8_material_2026-10-16.json")
OUT = os.path.join(FX, "m8_opportunity_2026-10-16.json")


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m5_for_opp8", "sheet_m5_engine_2026-10-15.py")
NEW = _mod("m7_for_opp8", "sheet_m7_engine_2026-10-15.py")
L = _mod("label_spec_for_opp8", "sheet_label_spec_2026-10-15.py")
M2 = E.M2
norm = M2.norm


def extract_of(mat):
    return (mat["prompt"].split("----- 表(ここから) -----")[1]
            .split("----- 表(ここまで) -----")[0].strip())


def cells_of(extract):
    """抜粋の値のセルを開く。**表 2 は 款名 の欄を持つ**(段 8 の変更点)。"""
    out, table, head = [], None, None
    for line in extract.split("\n"):
        if line.startswith("【表"):
            table, head = line.split("】")[0].strip("【"), None
            continue
        if not line.strip():
            continue
        cells = [c.strip() for c in line.split("\t")]
        if head is None:
            head = cells
            continue
        if table == "表 1" or len(cells) != len(head):
            continue
        if table == "表 2":
            scope, level, kan, name = cells[0], cells[1], cells[2], cells[3]
            parent = kan or None
            for col, v in zip(head[4:], cells[4:]):
                if v:
                    out.append({"表": table, "scope": scope, "level": level,
                                "parent": parent, "name": name, "column": col,
                                "value": int(v.replace(",", ""))})
        if table == "表 3":
            scope, kan, ko, name = cells[0], cells[1], cells[2], cells[3]
            parent = "%s > %s" % (kan, ko)
            for col, v in zip(head[4:], cells[4:]):
                if v:
                    out.append({"表": table, "scope": scope, "level": "目",
                                "parent": parent, "name": name, "column": col,
                                "value": int(v.replace(",", ""))})
    return out


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(数え直さない)" % OUT)
    mat = json.load(io.open(MAT, encoding="utf-8"))
    extract = extract_of(mat)
    cells = cells_of(extract)
    en = norm(extract)

    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    raw = E.fix_total_level(E.build_index(
        M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
        M2.parse_meisai(books[M2.MEISAI])))
    ents = E.canonicalize(raw, E.alias_table(raw))
    k4 = collections.defaultdict(set)
    k5 = collections.defaultdict(set)
    for e in ents:
        k4[(norm(e["scope"]), norm(e["level"]), norm(e["name"]),
            norm(e["column"]))].add(e["value"])
        k5[E.field_key(e)].add(e["value"])
    dup4 = {k for k, v in k4.items() if len(v) > 1}
    dup5 = {k for k, v in k5.items() if len(v) > 1}
    LCOL = L.COLUMN_ALIAS

    o1 = o2 = o4 = o5 = 0
    col_yes = col_no = 0
    by_table = collections.Counter()
    rows = []
    for c in cells:
        comps = NEW.parent_components(c["parent"])
        named = bool(comps) and all(x in en for x in comps)
        col_in = norm(c["column"]) in en
        canon_col = LCOL.get(c["column"], c["column"])
        amb4 = ((norm(c["scope"]), norm(c["level"]), norm(c["name"]),
                 norm(c["column"])) in dup4
                or (norm(c["scope"]), norm(c["level"]), norm(c["name"]),
                    norm(canon_col)) in dup4)
        uniq5 = (norm(c["scope"]), norm(c["level"]), norm(c["parent"]),
                 norm(c["name"]), norm(canon_col)) not in dup5
        # O-5: 6 欄すべてが抜粋から読めるか(会計・階層・親・科目名・列・値)
        readable = (norm(c["scope"]) in en and col_in
                    and (not comps or named)
                    and (c["level"] != "項" or bool(c["parent"])))
        o1 += 1 if named else 0
        o2 += 1 if (named and amb4) else 0
        if named and amb4 and uniq5:
            o4 += 1
            by_table[c["表"]] += 1
        o5 += 1 if readable else 0
        if col_in:
            col_yes += 1
        else:
            col_no += 1
        rows.append(dict(c, parent_named_in_extract=named, column_in_extract=col_in,
                         ambiguous_without_parent=amb4, unique_with_parent=uniq5,
                         six_fields_readable=readable))

    rec = {"purpose": ("段 8 の**機会**の件数。**生成の前に数えた。**"
                       "単位は行(値のセル)で、主張ではない"),
           "seal": "docs/DOMAIN1_M8_SEAL_2026-10-16.md",
           "material": "fixtures/sheet/m8_material_2026-10-16.json",
           "unit": "抜粋の値のセル(主張は生成されるまで存在しない)",
           "not_a_pass_condition": True,
           "will_not_reselect": ("この数を見て標本を選び直さない。生成文も誘導しない"
                                 "(人間の指示 2026-10-16)"),
           "cells": len(cells),
           "O-1 親の成分が全部抜粋に在るセル": o1,
           "O-2 そのうち親が無いと 4 欄で一意にならないセル": o2,
           "O-3 列の見出しが抜粋に在るセル": col_yes,
           "O-3 列の見出しが抜粋に無いセル": col_no,
           "O-4 旧では保留・新では接続になりうるセル": o4,
           "O-4 の表ごとの内訳": dict(by_table),
           "O-5 6 欄すべてが抜粋から読めるセル": o5,
           "limit": ("**O-4 は表 3 の 4 行(12 セル)からしか出ない。**"
                     "表 2 の 40 行は 1 行も 4 欄で一意でないので、"
                     "**旧 engine も結べる = 増分にならない。**"
                     "したがって **G-7(増分 ≥ 1 件)は、報告文が表 3 の行を"
                     "列つきで書くかどうかに掛かっている。**"
                     "書かなければ G-7 = 0 で失敗になる。"
                     "**この数を見て表 3 を増やすことはしない**"
                     "(段 6・段 7 の抜粋の行を外す規則を封に書いたため、"
                     "条件を満たす目の行が 4 行しか残っていない)"),
           "unverifiable_prediction": (
               "封 §4 の X 系の機会: **O-5 が全セルと一致すれば、"
               "段 7 の失敗の型(抜粋から 6 欄が読めない)はこの標本では起きない。**"
               "一致しないセルが在れば、そこが X-2 の候補である"),
           "rows": rows}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in rec.items():
        if k.startswith("O-") or k == "cells":
            print("  %-44s %s" % (k, v))
    print("->", OUT)


if __name__ == "__main__":
    main()
