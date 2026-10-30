# -*- coding: utf-8 -*-
"""段 7 の**機会の件数**を、生成の前に数える(人間の指示 2026-10-16)。

> 標本を選んだあと、生成前に、次の件数を記録してください。
>   親の手がかりになり得る名前が、金額直前の区間にある主張数 /
>   親の全成分が支持され得る主張数 / 列の手がかりがある主張数・ない主張数 /
>   旧エンジンでは保留になり、新エンジンで接続候補になり得る主張数
> 記録した件数を見て標本を選び直したり、生成文を誘導したりしてはいけません。

**単位について(ここだけ指示の字どおりにできない):**
生成の前には**主張が 1 件も存在しない。**主張は報告文が書かれて初めて生まれる。
だからここで数えるのは**行(= 抜粋の値のセル)の単位の「機会」**である。
**同じ 4 つを、生成後に主張の単位でもう一度数える**(`sheet_m7_run_…py`)。
2 つの数は単位が違うので**並べて比べない。**

数え方(**抜粋だけから機械で決まるもの**):
  O-1 親の成分が**全部抜粋の中に書かれている**値のセル(= 書き手が親を名指せる)
  O-2 O-1 のうち、**親を使わないと 4 欄で一意にならない**セル(= 親が効く)
  O-3 列の見出しが抜粋に在るセル / 無いセル
  O-4 **旧では保留・新では接続になりうる**セル
      (4 欄で一意でない **かつ** 親を足した 5 欄 + 列で一意)

    python3 measure/sheet_m7_opportunity_2026-10-15.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m7_material_2026-10-15.json")
OUT = os.path.join(FX, "m7_opportunity_2026-10-15.json")


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m5_for_opp", "sheet_m5_engine_2026-10-15.py")
NEW = _mod("m7_for_opp", "sheet_m7_engine_2026-10-15.py")
M2 = E.M2
norm = M2.norm


def extract_of(mat):
    return (mat["prompt"].split("----- 表(ここから) -----")[1]
            .split("----- 表(ここまで) -----")[0].strip())


def cells_of(extract):
    """抜粋の値のセルを (表, 会計, 階層, 親, 科目名, 列, 値) に開く。"""
    out, table, head = [], None, None
    for line in extract.split("\n"):
        if line.startswith("【表"):
            table, head = line.split("】")[0].strip("【"), None
            continue
        cells = [c.strip() for c in line.split("\t")]
        if not line.strip():
            continue
        if head is None:
            head = cells
            continue
        if table == "表 1":
            continue
        if table == "表 2" and len(cells) == len(head):
            scope, level, name = cells[0], cells[1], cells[2]
            parent = None
            for col, v in zip(head[3:], cells[3:]):
                if v:
                    out.append({"表": table, "scope": scope, "level": level,
                                "parent": parent, "name": name, "column": col,
                                "value": int(v.replace(",", ""))})
        if table == "表 3" and len(cells) == len(head):
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

    # 列の別名(表 3 の `計` は決算書の `予算現額`)を索引側の字に直して照合する
    alias_col = NEW.OLD and None
    LCOL = _mod("label_spec_for_opp", "sheet_label_spec_2026-10-15.py").COLUMN_ALIAS

    o1 = o2 = o4 = 0
    col_yes = col_no = 0
    rows = []
    for c in cells:
        comps = NEW.parent_components(c["parent"])
        named = bool(comps) and all(x in en for x in comps)
        col_in_extract = norm(c["column"]) in en
        k4key = (norm(c["scope"]), norm(c["level"]), norm(c["name"]), norm(c["column"]))
        canon_col = LCOL.get(c["column"], c["column"])
        k4key_canon = (norm(c["scope"]), norm(c["level"]), norm(c["name"]),
                       norm(canon_col))
        k5key = (norm(c["scope"]), norm(c["level"]), norm(c["parent"]),
                 norm(c["name"]), norm(canon_col))
        amb4 = (k4key in dup4) or (k4key_canon in dup4)
        uniq5 = k5key not in dup5
        o1 += 1 if named else 0
        o2 += 1 if (named and amb4) else 0
        o4 += 1 if (named and amb4 and uniq5) else 0
        if col_in_extract:
            col_yes += 1
        else:
            col_no += 1
        rows.append(dict(c, parent_named_in_extract=named,
                         column_in_extract=col_in_extract,
                         ambiguous_without_parent=amb4,
                         unique_with_parent=uniq5))

    rec = {"purpose": ("段 7 の**機会**の件数。**生成の前に数えた。**"
                       "単位は行(値のセル)で、主張ではない"),
           "seal": "docs/DOMAIN1_M7_SEAL_2026-10-15.md",
           "material": "fixtures/sheet/m7_material_2026-10-15.json",
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
           "note": ("O-3 は**抜粋に見出しが在るか**しか見ていない。"
                    "報告文が列の名前を書くかどうかは生成するまで分からない。"
                    "段 6 の診断では、親が取れた 4 件のうち 3 件が"
                    "**文に列が無くて**保留になった"),
           "limit": ("**O-1 の 120 は表 3(目)のセルだけである。**"
                     "表 2 は `会計・階層・科目名` しか示さないので、"
                     "**項の親(款名)は抜粋に書かれていない。**"
                     "したがって**親の成分が 1 つの場合(項)は、この標本では試されない。**"
                     "試されるのは成分が 2 つの場合(目)だけである。"
                     "**この数を見て表 2 に款名の欄を足すことはしない**"
                     "(人間の指示: 記録した件数を見て標本を選び直さない)"),
           "rows": rows}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in rec.items():
        if k.startswith("O-") or k == "cells":
            print("  %-44s %s" % (k, v))
    print("->", OUT)


if __name__ == "__main__":
    main()
