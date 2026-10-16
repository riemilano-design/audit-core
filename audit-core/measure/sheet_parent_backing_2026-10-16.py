# -*- coding: utf-8 -*-
"""段 8 の裏づけ B-1〜B-5(封 docs/DOMAIN1_M8_SEAL_2026-10-16.md §2)。

**材料に親の名前を書けるのは、裏づけがそろった行だけ。**推測で補完しない。

  項の款名(表 2): **B-1 決算書の配置 + B-2 決算書のコード + B-3 明細の配置**の 3 本
  目の款名・項名(表 3): **B-4 明細の配置 + B-5 明細のコード**の **2 本**
    → **決算書に目の行は無いので別 file の裏づけは作れない。**封 §2-2 に書いたとおり、
      **表 2 の項より裏づけが 1 本少ない。**この差を同じ強さの根拠として扱わない。

この file は**索引の親の決め方を変えない**(段 5 の `build_index` のまま)。
決めるのは「**材料に書いてよいか**」だけである。

    python3 measure/sheet_parent_backing_2026-10-16.py   # 数を印字して記録を書く
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "fixtures", "sheet", "parent_backing_2026-10-16.json")


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m5_for_backing", "sheet_m5_engine_2026-10-15.py")
M2 = E.M2
norm = M2.norm


def _bundles(children, parents, key_row="row", code="code"):
    """親の行ごとに子のコードを並べる。**行の順だけで束にする**(値は見ない)。"""
    rows = sorted(p[key_row] for p in parents)
    g = collections.defaultdict(list)
    for c in children:
        above = [r for r in rows if r < c[key_row]]
        g[above[-1] if above else None].append(c.get(code))
    return g


def _is_restarting_sequence(codes):
    """B-2 / B-5: `01` から始まる 1..n の連番か。**1 つでも欠ければ False。**"""
    if not codes or not all(codes):
        return False
    try:
        nums = [int(x) for x in codes]
    except (TypeError, ValueError):
        return False
    return nums == list(range(1, len(nums) + 1))


def kou_parents(kessan, meisai, alias=None):
    """項の款名を返す。**3 本そろった (会計, 項名) だけ。**

    返すのは {(会計, 項名): 款名} と、落とした理由の内訳。
    `alias` は明細の会計名を正本に直す表(`alias_table()["table"]`)。
    **裏づけの通った別名しか入っていないので、未確認の会計は B-3 が成立しない。**
    それでよい ― 同じ会計だと確かめられない file を 2 本目の裏づけに数えない。
    """
    ok, why = {}, collections.Counter()
    detail = []
    # ---- B-1 / B-2: 決算書の中だけで決まる
    b12 = {}
    for b in kessan["blocks"]:
        kan_by_row = {k["row"]: k.get("name") for k in b["kan"]}
        g = _bundles(b["items"], b["kan"])
        good_rows = {r for r, codes in g.items()
                     if r is not None and _is_restarting_sequence(codes)}
        for it in b["items"]:
            pr = it.get("parent_row")
            key = (norm(b["account"]), norm(it.get("name")))
            if pr is None or pr not in kan_by_row:
                why["B-1 款の行が上に無い"] += 1
                continue
            if pr not in good_rows:
                why["B-2 コードが 01 からの連番でない"] += 1
                continue
            b12.setdefault(key, set()).add(kan_by_row[pr])
    # ---- B-3: 明細の配置と突き合わせる
    alias = alias or {}
    m3 = collections.defaultdict(set)
    for s in meisai["sheets"]:
        acc = s["account"]
        acc = (alias.get(acc) or {}).get("canonical", acc)
        kan_rows = sorted((x["row"], x.get("name")) for x in s["kan"])
        for it in s["items"]:
            above = [n for r, n in kan_rows if r < it["row"]]
            if above and it.get("name"):
                m3[(norm(acc), norm(it["name"]))].add(above[-1])
    for key, kans in b12.items():
        if len(kans) != 1:
            why["B-1 決算書の中で款が 2 通り"] += 1
            detail.append({"key": list(key), "why": "決算書の中で款が 2 通り",
                           "kessan": sorted(kans)})
            continue
        kan = list(kans)[0]
        mk = m3.get(key)
        if not mk:
            why["B-3 明細に対応する項が無い"] += 1
            detail.append({"key": list(key), "why": "明細に対応する項が無い",
                           "kessan": [kan]})
            continue
        if len(mk) != 1:
            why["B-3 明細の款が 2 通り以上"] += 1
            detail.append({"key": list(key), "why": "明細の款が 2 通り以上",
                           "kessan": [kan], "meisai": sorted(mk)})
            continue
        if norm(list(mk)[0]) != norm(kan or ""):
            why["B-3 明細と決算書で款が食い違う"] += 1
            detail.append({"key": list(key), "why": "明細と決算書で款が食い違う",
                           "kessan": [kan], "meisai": sorted(mk)})
            continue
        ok[key] = kan
    return ok, dict(why), detail


def moku_parents(meisai):
    """目の (款名, 項名) を返す。**B-4 + B-5 の 2 本だけ。**別 file の裏づけは無い。"""
    ok, why = {}, collections.Counter()
    for s in meisai["sheets"]:
        kan_rows = sorted((x["row"], x.get("name")) for x in s["kan"])
        item_rows = sorted((x["row"], x.get("name")) for x in s["items"])
        g = _bundles(s["moku"], s["items"])
        good = {r for r, codes in g.items()
                if r is not None and _is_restarting_sequence(codes)}
        for mk in s["moku"]:
            kan = [n for r, n in kan_rows if r < mk["row"]]
            ko = [(r, n) for r, n in item_rows if r < mk["row"]]
            if not kan or not ko:
                why["B-4 款か項の行が上に無い"] += 1
                continue
            if ko[-1][0] not in good:
                why["B-5 コードが 01 からの連番でない"] += 1
                continue
            key = (norm(s["account"]), norm(mk.get("name")), mk["row"], s.get("sheet"))
            ok[key] = (kan[-1], ko[-1][1])
    return ok, dict(why)


def main():
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    ks = M2.parse_kessan(books[M2.KESSAN])
    ms = M2.parse_meisai(books[M2.MEISAI])
    raw = E.fix_total_level(E.build_index(
        M2.parse_soukatu(books[M2.SOUKATU]), ks, ms))
    alias = E.alias_table(raw)["table"]
    kou, kou_why, detail = kou_parents(ks, ms, alias)
    moku, moku_why = moku_parents(ms)
    gen = [k for k in kou if k[0] == norm("一般会計")]
    rec = {"purpose": "段 8 の裏づけ B-1〜B-5。**材料に親の名前を書けるかだけを決める**",
           "seal": "docs/DOMAIN1_M8_SEAL_2026-10-16.md",
           "別名_裏づけの通った会計": sorted(alias),
           "項の款名_3本そろった": len(kou),
           "項の款名_一般会計で成立": len(gen),
           "項の款名_落ちた理由": kou_why,
           "項の款名_落ちた明細": detail,
           "目の親_2本そろった": len(moku),
           "目の親_落ちた理由": moku_why,
           "backings": {"項": ["B-1 決算書の配置", "B-2 決算書のコード", "B-3 明細の配置"],
                        "目": ["B-4 明細の配置", "B-5 明細のコード"]},
           "note": ("**目の裏づけは 2 本で、項の 3 本より 1 本少ない。**"
                    "決算書に目の行が無いので別 file の裏づけは作れない(封 §2-2)。"
                    "**この差を同じ強さの根拠として扱わない。**")}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("項の款名: 3 本そろった %d 件(一般会計 %d 件)" % (len(kou), len(gen)))
    for k, v in kou_why.items():
        print("   落ちた: %-32s %d" % (k, v))
    print("目の親: 2 本そろった %d 件" % len(moku))
    for k, v in moku_why.items():
        print("   落ちた: %-32s %d" % (k, v))
    print("->", OUT)


if __name__ == "__main__":
    main()
