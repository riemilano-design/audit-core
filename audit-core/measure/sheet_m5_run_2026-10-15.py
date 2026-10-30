# -*- coding: utf-8 -*-
"""段 5: 凍結した engine を凍結した報告文に当てる(封 §6・追記 2 の C/D)。

出すのは主張の一覧(分母)と接続の結果、そして
**接続数・保留数・対象外数**(追記 2 の C)と **新規 / 再出**(追記 2 の D)。
**合否はまだ書かない**(採点は別の script)。
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
REPORT = os.path.join(FX, "m5_report_2026-10-15.json")
OLD = os.path.join(FX, "m4_binds_2026-10-15.json")
OUT = os.path.join(FX, "m5_binds_2026-10-15.json")


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m5", "sheet_m5_engine_2026-10-15.py")
M2 = E.M2


def main():
    if os.path.exists(OUT):
        raise SystemExit("接続の結果が既に在る: %s(当て直さない)" % OUT)
    report = json.load(io.open(REPORT, encoding="utf-8"))["report"]
    old_values = {c["value"] for c in json.load(io.open(OLD, encoding="utf-8"))["claims"]}

    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    out = E.run(report,
                M2.parse_soukatu(books[M2.SOUKATU]),
                M2.parse_kessan(books[M2.KESSAN]),
                M2.parse_meisai(books[M2.MEISAI]))
    claims, binds = out["claims"], {b["claim_id"]: b for b in out["binds"]}
    for c in claims:
        c["novelty"] = "再出" if c.get("value") in old_values else "新規"

    scorable = [c for c in claims if c.get("scorable")]
    states = collections.Counter(binds[c["id"]]["state"] for c in claims)
    # 追記 2 の C: 接続数・保留数・対象外数を**分けて**数える
    split = {"接続数": 0, "保留数": 0, "対象外数": 0}
    hold_reasons = collections.Counter()
    for c in claims:
        b = binds[c["id"]]
        if b["state"] == "GROUNDED":
            split["接続数"] += 1
        elif not c.get("scorable") or b["state"] == "POINTER_NOT_FOUND":
            split["対象外数"] += 1
        else:
            split["保留数"] += 1
            hold_reasons[_reason_kind(b.get("hold_reason"))] += 1
    novelty = collections.Counter(c["novelty"] for c in claims)
    nov_scorable = collections.Counter(c["novelty"] for c in scorable)

    print("索引 %d / 語彙 %d / 列の手がかり %d" % (out["entries"], out["vocabulary"],
                                                 out["column_cues"]))
    print("切り出した数 %d / 採点対象(主語あり)%d" % (len(claims), len(scorable)))
    print("追記 2 の C ―", json.dumps(split, ensure_ascii=False))
    print("  保留の理由:", json.dumps(dict(hold_reasons), ensure_ascii=False))
    print("追記 2 の D ― 全体", json.dumps(dict(novelty), ensure_ascii=False),
          "/ 採点対象", json.dumps(dict(nov_scorable), ensure_ascii=False))
    print("状態:", json.dumps(dict(states), ensure_ascii=False))
    print("ルート:", json.dumps(dict(collections.Counter(
        b["route"] for b in binds.values() if b["route"])), ensure_ascii=False))
    print("別名: 通った %d / 未確認 %d" % (len(out["alias"]["table"]),
                                          len(out["alias"]["unconfirmed"])))
    print("一意でない階層:", out["duplication"]["levels_not_unique"])

    rec = {"purpose": "段 5 の接続の結果。**合否は採点の script で出す**",
           "seal": "docs/DOMAIN1_M5_SEAL_2026-10-15.md",
           "engine": "measure/sheet_m5_engine_2026-10-15.py",
           "applied_times": 1,
           "entries": out["entries"], "vocabulary": out["vocabulary"],
           "column_cues": out["column_cues"],
           "alias_passed": sorted(out["alias"]["table"]),
           "alias_unconfirmed": len(out["alias"]["unconfirmed"]),
           "duplication": out["duplication"],
           "counts": {"claims": len(claims), "scorable": len(scorable),
                      "split": split, "hold_reasons": dict(hold_reasons),
                      "novelty": dict(novelty), "novelty_scorable": dict(nov_scorable),
                      "states": dict(states),
                      "routes": dict(collections.Counter(
                          b["route"] for b in binds.values() if b["route"]))},
           "claims": claims, "binds": [binds[c["id"]] for c in claims]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


def _reason_kind(r):
    if not r:
        return "(理由なし)"
    for k in ("列 の手がかりが 2 つ以上", "階層 の手がかりが 2 つ以上",
              "に候補が 0 件", "6 欄が一意でない", "会計が未確認の別名",
              "file 間で食い違う", "値だけでは結ばない", "正規化で文字数が変わる"):
        if k in r:
            return k
    return r


if __name__ == "__main__":
    main()
