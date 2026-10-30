# -*- coding: utf-8 -*-
"""段 9 の**機会の件数**を、生成の前に数える(封 docs/DOMAIN1_M9_SEAL_2026-10-16.md §5)。

単位は**行(抜粋の値のセル)**で、主張ではない ― 生成前には主張が存在しない。
**同じものを生成後に主張の単位でも数える(C-1〜C-4)。単位が違うので並べて比べない。**

数えるもの(封 §5 の表のまま):
  O-1 抜粋の値のセルの総数
  O-2 **③が発火し得るセル** ― 会計の欄が `東京都○○会計`(未確認の別名)の行
  O-3 **6 欄すべてが抜粋から読めるセル** ― X-2 が 0 になるための前提
  O-4 **G-4 が発火し得るセル** ― **抜粋の中で**会計・階層・科目名・列・値まで同じで
      親が 2 通り以上。**席が抜粋から 1 つに決められない行である**
  O-4′ 同じことを**索引全体**で見たもの(engine が 6 欄で一意にできない行)。
      **O-4 と O-4′ は別物。G-4 の分母に効くのは O-4 である**
      ― 席は抜粋しか読まない(記憶 `engine-sees-more-than-the-grader.md`)
  O-5 親の全成分が抜粋から読めるセル
  O-6 列の手がかりが在る / 無いセル
  O-7 旧 engine では保留・新 engine で接続候補になり得るセル(親の絞りの機会)

**この数を見て表を増やしたり減らしたりしない。標本を選び直さない。生成文を誘導しない。**

    python3 measure/sheet_m9_opportunity_2026-10-16.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m9_material_2026-10-16.json")
OUT = os.path.join(FX, "m9_opportunity_2026-10-16.json")


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m5_for_opp9", "sheet_m5_engine_2026-10-15.py")
NEW = _mod("m7_for_opp9", "sheet_m7_engine_2026-10-15.py")
L9 = _mod("spec9_for_opp9", "sheet_label_spec_m9_2026-10-16.py")
M2 = E.M2
norm = M2.norm


def extract_of(mat):
    return (mat["prompt"].split("----- 表(ここから) -----")[1]
            .split("----- 表(ここまで) -----")[0].strip())


def cells_of(extract):
    """抜粋の値のセルを開く。**段 9 の表の形**(表 2 は 7 欄・表 3 は 6 欄)。"""
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


def readable_of(c, en, comps):
    """**6 欄すべてが抜粋から読めるか。**

    この材料では O-3 = O-1 になる(全部読める)。つまり**緩める変異が等価になり、
    O-3 の数だけでは歯が無い。**だから判定をここに切り出し、
    **壊した入力を食わせて False になること**を門で確かめる
    (記憶 `prediction-must-be-able-to-fail.md`・`mutations-miss-degenerate-inputs.md`)。
    """
    return bool(norm(c["scope"]) in en and norm(c["column"]) in en
                and (not comps or all(x in en for x in comps))
                and (c["level"] != "項" or bool(c["parent"])))


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
    alias = E.alias_table(raw)
    ents = E.canonicalize(raw, alias)
    unconf = {norm(u["name"]) for u in alias["unconfirmed"]}

    # 索引全体の重複(engine の側)
    k4 = collections.defaultdict(set)
    k5 = collections.defaultdict(set)
    g_idx = collections.defaultdict(set)
    for e in ents:
        k4[(norm(e["scope"]), norm(e["level"]), norm(e["name"]),
            norm(e["column"]))].add(e["value"])
        k5[E.field_key(e)].add(e["value"])
        g_idx[(norm(e["scope"]), norm(e["level"]), norm(e["name"]),
               norm(e["column"]), e["value"])].add(norm(e["parent"]) or "")
    dup4 = {k for k, v in k4.items() if len(v) > 1}
    dup5 = {k for k, v in k5.items() if len(v) > 1}
    coll_idx = {k for k, v in g_idx.items() if len(v) > 1}

    # **抜粋の中だけ**の重複(席の側)
    g_ext = collections.defaultdict(set)
    for c in cells:
        g_ext[(norm(c["scope"]), norm(c["level"]), norm(c["name"]),
               norm(c["column"]), c["value"])].add(norm(c["parent"]) or "")
    coll_ext = {k for k, v in g_ext.items() if len(v) > 1}

    LCOL = L9.COLUMN_ALIAS
    o2 = o3 = o4 = o4p = o5 = o7 = 0
    col_yes = col_no = 0
    by_table = collections.Counter()
    o2_by_account = collections.Counter()
    o4_by_name = collections.Counter()
    rows = []
    for c in cells:
        comps = NEW.parent_components(c["parent"])
        named = bool(comps) and all(x in en for x in comps)
        col_in = norm(c["column"]) in en
        canon_col = LCOL.get(c["column"], c["column"])
        key5 = (norm(c["scope"]), norm(c["level"]), norm(c["name"]),
                norm(c["column"]), c["value"])
        amb4 = ((norm(c["scope"]), norm(c["level"]), norm(c["name"]),
                 norm(c["column"])) in dup4
                or (norm(c["scope"]), norm(c["level"]), norm(c["name"]),
                    norm(canon_col)) in dup4)
        uniq5 = (norm(c["scope"]), norm(c["level"]), norm(c["parent"]),
                 norm(c["name"]), norm(canon_col)) not in dup5
        readable = readable_of(c, en, comps)
        is_unconf = norm(c["scope"]) in unconf
        if is_unconf:
            o2 += 1
            o2_by_account[c["scope"]] += 1
        if readable:
            o3 += 1
        if key5 in coll_ext:
            o4 += 1
            o4_by_name[c["name"]] += 1
        if key5 in coll_idx:
            o4p += 1
        if named:
            o5 += 1
        if named and amb4 and uniq5:
            o7 += 1
            by_table[c["表"]] += 1
        if col_in:
            col_yes += 1
        else:
            col_no += 1
        rows.append(dict(c, scope_unconfirmed=is_unconf,
                         parent_named_in_extract=named,
                         column_in_extract=col_in,
                         six_fields_readable=readable,
                         ambiguous_in_extract=key5 in coll_ext,
                         ambiguous_in_index=key5 in coll_idx,
                         ambiguous_without_parent=amb4,
                         unique_with_parent=uniq5))

    rec = {"purpose": ("段 9 の**機会**の件数。**生成の前に数えた。**"
                       "単位は行(値のセル)で、主張ではない"),
           "seal": "docs/DOMAIN1_M9_SEAL_2026-10-16.md",
           "material": "fixtures/sheet/m9_material_2026-10-16.json",
           "unit": "抜粋の値のセル(主張は生成されるまで存在しない)",
           "not_a_pass_condition": True,
           "will_not_reselect": ("この数を見て表を増やしたり減らしたりしない。"
                                 "標本を選び直さない。生成文も誘導しない"
                                 "(人間の指示 2026-10-16)"),
           "O-1 抜粋の値のセル": len(cells),
           "O-2 ③が発火し得るセル(会計が未確認の別名)": o2,
           "O-2 の会計ごとの内訳": dict(o2_by_account),
           "O-3 6 欄すべてが抜粋から読めるセル": o3,
           "O-3 の注": ("**O-3 = O-1 なので、この数だけでは歯が無い。**"
                        "`readable = True` に置き換える変異は**この材料では等価**で、"
                        "どの試験でも区別できない(全セルが実際に読めるため)。"
                        "だから `readable_of` の歯は**壊した入力**で別に確かめている"
                        "(門 test_21)。記憶 `prediction-must-be-able-to-fail.md`"),
           "O-4 抜粋の中で親が 2 通り以上に割れるセル(席が決められない)": o4,
           "O-4 の科目名ごとの内訳": dict(o4_by_name),
           "O-4′ 索引全体で親が 2 通り以上に割れるセル": o4p,
           "O-5 親の全成分が抜粋から読めるセル": o5,
           "O-6 列の手がかりが在るセル": col_yes,
           "O-6 列の手がかりが無いセル": col_no,
           "O-7 旧では保留・新では接続になりうるセル": o7,
           "O-7 の表ごとの内訳": dict(by_table),
           "limit": [
               "**O-2 > 0 でも③は発火しない場合がある。**報告文が表 3b の行を"
               "引かなければ主張が立たない。**0 件だったときは「未測定」として"
               "報告する**(封 §8)。生成文を誘導しない",
               "**O-4 の行は値が全部 0 である。**報告文が 0 円の数を引くかどうかは"
               "生成まで分からない。**G-4 の分母は再び 0 になり得る**(封 §5-1)",
               "**O-4 と O-4′ を足したり比べたりしない。**席は抜粋しか読まない。"
               "engine は材料の全部を読む",
               "**O-7 は③と無関係**(親の絞りの機会)。**G-7 は段 9 の線ではない**",
           ],
           "cells": rows}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in rec.items():
        if k.startswith("O-"):
            print("%s: %s" % (k, json.dumps(v, ensure_ascii=False)))
    print("->", OUT)


if __name__ == "__main__":
    main()
