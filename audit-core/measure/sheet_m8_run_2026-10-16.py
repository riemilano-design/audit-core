# -*- coding: utf-8 -*-
"""段 8: 凍結した報告文に**旧と新の 2 本の engine**を当てる(封 §4・§8 の 6)。

出すのは 2 本の接続の結果と、人間が求めた 4 つの件数の**主張の単位**の数
(生成前の行の単位の数は `sheet_m7_opportunity_…json`。**単位が違うので並べない**)。
**合否はここでは出さない**(採点は `sheet_m7_score_…py`)。

    python3 measure/sheet_m8_run_2026-10-16.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
REPORT = os.path.join(FX, "m8_report_2026-10-16.json")
OLDP = ("m4_binds_2026-10-15.json", "m5_binds_2026-10-15.json",
        "m6_binds_2026-10-15.json", "m7_binds_2026-10-15.json")
MAT = os.path.join(FX, "m8_material_2026-10-16.json")
OUT = os.path.join(FX, "m8_binds_2026-10-16.json")


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


NEW = _mod("m7", "sheet_m7_engine_2026-10-15.py")
OLD = _mod("m5_for_run7", "sheet_m5_engine_2026-10-15.py")
M2 = NEW.M2
norm = M2.norm


def main():
    if os.path.exists(OUT):
        raise SystemExit("接続の結果が既に在る: %s(当て直さない)" % OUT)
    report = json.load(io.open(REPORT, encoding="utf-8"))["report"]
    old_values = set()
    for p in OLDP:
        for c in json.load(io.open(os.path.join(FX, p), encoding="utf-8"))["claims"]:
            if c.get("value") is not None:
                old_values.add(c["value"])

    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    args = (M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
            M2.parse_meisai(books[M2.MEISAI]))
    o = OLD.run(report, *args)
    n = NEW.run(report, *args)
    ob = {b["claim_id"]: b for b in o["binds"]}
    nb = {b["claim_id"]: b for b in n["binds"]}
    oc = {c["id"]: c for c in o["claims"]}
    nc = {c["id"]: c for c in n["claims"]}
    assert sorted(oc) == sorted(nc), "旧と新で主張の id が違う"
    for cid in oc:
        assert (oc[cid].get("sentence_index"), oc[cid].get("value")) == \
               (nc[cid].get("sentence_index"), nc[cid].get("value")), cid
    claims = n["claims"]
    for c in claims:
        c["novelty"] = "再出" if c.get("value") in old_values else "新規"

    scorable = [c for c in claims if c.get("scorable")]

    def split_of(binds):
        s = {"接続数": 0, "保留数": 0, "対象外数": 0}
        why = collections.Counter()
        for c in claims:
            b = binds[c["id"]]
            if b["state"] == "GROUNDED":
                s["接続数"] += 1
            elif not c.get("scorable") or b["state"] == "POINTER_NOT_FOUND":
                s["対象外数"] += 1
            else:
                s["保留数"] += 1
                why[b.get("hold_reason") or "(理由なし)"] += 1
        return s, dict(why)

    o_split, o_why = split_of(ob)
    n_split, n_why = split_of(nb)

    # 人間の指示 4 つ ― **主張の単位**(生成前の行の単位とは別の数)
    c1 = sum(1 for c in scorable if c.get("parent_cues"))
    c2 = sum(1 for c in scorable if nb[c["id"]].get("parent_filtered"))
    c3y = sum(1 for c in scorable if c.get("column") and not c.get("column_ambiguous"))
    c3n = len(scorable) - c3y
    c4 = sum(1 for c in scorable
             if ob[c["id"]]["state"] != "GROUNDED" and nb[c["id"]]["state"] == "GROUNDED")
    # 封 §4-1 の X-1 / X-2(**ラベルを使わない**)。
    # engine が結んだ 6 欄の行が、**抜粋に書かれている行**かどうか。
    OPP = _mod("opp8", "sheet_m8_opportunity_2026-10-16.py")
    mat = json.load(io.open(MAT, encoding="utf-8"))
    rows_in_extract = {(norm(c["scope"]), norm(c["level"]), norm(c["parent"]),
                        norm(c["name"]))
                       for c in OPP.cells_of(OPP.extract_of(mat))}
    x1 = x2 = 0
    x2_ids = []
    for c in claims:
        b = nb[c["id"]]
        if b["state"] != "GROUNDED":
            continue
        ev = b.get("evidence") or {}
        key = (norm(ev.get("scope")), norm(ev.get("level")), norm(ev.get("parent")),
               norm(ev.get("name")))
        if key in rows_in_extract:
            x1 += 1
        else:
            x2 += 1
            x2_ids.append({"id": c["id"], "engine_row": list(key)})
    counts4 = {
        "C-1 親の手がかりになり得る名前が区間に在る主張": c1,
        "C-2 親の全成分が支持され、絞りが働いた主張": c2,
        "C-3 列の手がかりが在る主張": c3y,
        "C-3 列の手がかりが無い主張": c3n,
        "C-4 旧では保留・新では接続になった主張": c4,
        "X-1 抜粋に在る行に結んだ主張": x1,
        "X-2 抜粋に無い行に結んだ主張": x2,
    }

    print("索引 %d / 語彙 %d / 列の手がかり %d" % (n["entries"], n["vocabulary"],
                                                 n["column_cues"]))
    print("切り出した数 %d / 採点対象(主語あり)%d" % (len(claims), len(scorable)))
    print("旧:", json.dumps(o_split, ensure_ascii=False))
    print("新:", json.dumps(n_split, ensure_ascii=False))
    print("主張の単位の 4 つ + X:", json.dumps(counts4, ensure_ascii=False, indent=1))
    if x2_ids:
        print("**抜粋に無い行に結んだ主張(X-2):**")
        for z in x2_ids:
            print("   ", z["id"], z["engine_row"])
    print("新の保留の理由:")
    for k, v in n_why.items():
        print("   %-58s %d" % (k, v))
    print("新規 / 再出:", json.dumps(
        dict(collections.Counter(c["novelty"] for c in scorable)), ensure_ascii=False))

    rec = {"purpose": "段 8 の接続の結果(旧・新の 2 本)。**合否は採点の script で出す**",
           "seal": "docs/DOMAIN1_M8_SEAL_2026-10-16.md",
           "old_engine": "measure/sheet_m5_engine_2026-10-15.py",
           "new_engine": "measure/sheet_m7_engine_2026-10-15.py",
           "applied_times": 1,
           "entries": n["entries"], "vocabulary": n["vocabulary"],
           "column_cues": n["column_cues"],
           "alias_passed": sorted(n["alias"]["table"]),
           "alias_unconfirmed": len(n["alias"]["unconfirmed"]),
           "counts": {"claims": len(claims), "scorable": len(scorable),
                      "old_split": o_split, "new_split": n_split,
                      "old_hold_reasons": o_why, "new_hold_reasons": n_why,
                      "novelty": dict(collections.Counter(c["novelty"] for c in claims)),
                      "novelty_scorable": dict(collections.Counter(
                          c["novelty"] for c in scorable))},
           "claim_level_counts": counts4,
           "X-2_詳細": x2_ids,
           "X_note": ("X-1 / X-2 は封 §4-1。**ラベルを使わない指標**で、"
                      "X-3(X-2 のうち誤受理)と X-4 は採点の script が出す。"
                      "段 7 の実測は X-1 20・X-2 6・X-3 6・X-4 0 だった"),
           "unit_note": ("この 4 つは**主張の単位**。生成前に数えた"
                         "`m8_opportunity_2026-10-16.json` は**行(セル)の単位**で、"
                         "**単位が違うので並べて比べない**"),
           "claims": claims,
           "binds_old": [ob[c["id"]] for c in claims],
           "binds_new": [nb[c["id"]] for c in claims]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
