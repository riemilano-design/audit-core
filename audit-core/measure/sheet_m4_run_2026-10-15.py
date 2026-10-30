# -*- coding: utf-8 -*-
"""段 4: 凍結した engine を報告文に当てる(封 §3)。**ラベルの前に commit する。**

出すのは主張の一覧(分母)と接続の結果。**合否はまだ書かない**(採点は別の script)。
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPORT = os.path.join(ROOT, "fixtures", "sheet", "m4_report_2026-10-15.json")
OUT = os.path.join(ROOT, "fixtures", "sheet", "m4_binds_2026-10-15.json")


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m4e", os.path.join(HERE, "sheet_m4_engine_2026-10-15.py"))
M2 = E.M2


def main():
    report = json.load(io.open(REPORT, encoding="utf-8"))["report"]
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    out = E.run(report,
                M2.parse_soukatu(books[M2.SOUKATU]),
                M2.parse_kessan(books[M2.KESSAN]),
                M2.parse_meisai(books[M2.MEISAI]))
    claims, binds = out["claims"], out["binds"]
    scorable = [c for c in claims if c["scorable"]]
    states = collections.Counter(b["state"] for b in binds)
    routes = collections.Counter(b["route"] for b in binds if b["route"])
    print("索引のセル %d / 語彙 %d" % (out["entries"], out["vocabulary"]))
    print("切り出した数 %d / 採点対象(主語あり)%d / 判定不能の印 %d"
          % (len(claims), len(scorable), sum(1 for c in claims if c["undecidable"])))
    print("状態:", dict(states))
    print("ルート:", dict(routes))
    rec = {"purpose": "段 4 の接続の結果。**合否は採点の script で出す**",
           "seal": "docs/DOMAIN1_M4_SEAL_2026-10-15.md",
           "entries": out["entries"], "vocabulary": out["vocabulary"],
           "claims": claims, "binds": binds,
           "counts": {"claims": len(claims), "scorable": len(scorable),
                      "undecidable": sum(1 for c in claims if c["undecidable"]),
                      "states": dict(states), "routes": dict(routes)}}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
