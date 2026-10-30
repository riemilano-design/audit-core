# -*- coding: utf-8 -*-
"""段 9: 凍結した報告文に**旧と新の 2 本の engine**を当てる(封 §4・§11 の 6)。

**engine は 1 行も変えていない。**2 本を並べるのは増分のためではなく、
**親の絞りが③の結果に混ざっていないか**を見るためである(封 §4)。

出すのは 2 本の接続の結果と、**ラベルを使わない**件数:

  A-1 **③が発火した主張数** ― 保留の理由が「会計が未確認の別名」だったもの
  A-2 ③以外の理由で保留になった主張数(**③の成功に数えない**)
  A-3 **未確認の別名の行に結んだ主張数**(③の規則が破れた数。線は 0 件)
  X-1 抜粋に在る行に結んだ主張 / X-2 抜粋に無い行に結んだ主張
  C-1〜C-4 生成前の O と同じ 4 つを**主張の単位**で数え直したもの
      (**単位が違うので O と並べて比べない**)

**合否はここでは出さない**(採点は `sheet_m9_score_…py`)。

    python3 measure/sheet_m9_run_2026-10-16.py
"""
import collections
import hashlib
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
REPORT = os.path.join(FX, "m9_report_2026-10-16.json")
MAT = os.path.join(FX, "m9_material_2026-10-16.json")
OUT = os.path.join(FX, "m9_binds_2026-10-16.json")
OLDP = ("m4_binds_2026-10-15.json", "m5_binds_2026-10-15.json",
        "m6_binds_2026-10-15.json", "m7_binds_2026-10-15.json",
        "m8_binds_2026-10-16.json")
# 封 §4 の sha。**1 文字でも違えば結果を無効にする**
ENGINE_SHA = {
    "sheet_m5_engine_2026-10-15.py": "6eb5723ef518e1b4",
    "sheet_m7_engine_2026-10-15.py": "4574c3ea013d05a1",
    "sheet_parent_backing_2026-10-16.py": "8e387958c69398e8",
}
ALIAS_HOLD_MARK = "会計が未確認の別名"


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


NEW = _mod("m7_for_run9", "sheet_m7_engine_2026-10-15.py")
OLD = _mod("m5_for_run9", "sheet_m5_engine_2026-10-15.py")
OPP = _mod("opp9_for_run9", "sheet_m9_opportunity_2026-10-16.py")
M2 = NEW.M2
norm = M2.norm


def engine_shas():
    out = {}
    for f in ENGINE_SHA:
        out[f] = hashlib.sha256(
            io.open(os.path.join(HERE, f), "rb").read()).hexdigest()[:16]
    return out


def check_shas():
    got = engine_shas()
    bad = {f: (ENGINE_SHA[f], got[f]) for f in ENGINE_SHA if got[f] != ENGINE_SHA[f]}
    if bad:
        raise SystemExit("**engine の sha が封と違う。結果は無効である**: %s"
                         % json.dumps(bad, ensure_ascii=False))
    return got


def main():
    if os.path.exists(OUT):
        raise SystemExit("接続の結果が既に在る: %s(当て直さない)" % OUT)
    shas = check_shas()
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
    claims = n["claims"]
    assert sorted(c["id"] for c in claims) == sorted(ob), "旧と新で主張の id が違う"
    for c in claims:
        c["novelty"] = "再出" if c.get("value") in old_values else "新規"
    scorable = [c for c in claims if c.get("scorable")]

    unconf = {norm(u["name"]) for u in n["alias"]["unconfirmed"]}

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

    # ---- A-1 / A-2 / A-3(**ラベルを使わない**)
    a1, a2, a3 = [], [], []
    for c in scorable:
        b = nb[c["id"]]
        if b["state"] == "GROUNDED":
            ev = b.get("evidence") or {}
            if norm(ev.get("scope")) in unconf:
                a3.append({"id": c["id"], "会計": ev.get("scope"),
                           "科目名": ev.get("name"), "列": ev.get("column")})
            continue
        if b["state"] == "POINTER_NOT_FOUND":
            continue
        if b.get("unconfirmed_scope") or ALIAS_HOLD_MARK in (b.get("hold_reason") or ""):
            a1.append({"id": c["id"], "会計": b.get("unconfirmed_scope"),
                       "理由": b.get("hold_reason")})
        else:
            a2.append({"id": c["id"], "理由": b.get("hold_reason")})

    # ---- X-1 / X-2(**ラベルを使わない**)
    mat = json.load(io.open(MAT, encoding="utf-8"))
    cells = OPP.cells_of(OPP.extract_of(mat))
    # **両側に同じ正規化を掛け、空欄を `""` に畳む**
    # (記憶 `normalize-both-sides-of-a-comparison.md`。段 8 でこの型を 5 回目に踏んだ)
    def key4(d):
        return tuple(norm(d.get(k)) or ""
                     for k in ("scope", "level", "parent", "name"))

    in_extract = {key4(c) for c in cells}
    x1, x2, x2_ids = 0, 0, []
    for c in claims:
        b = nb[c["id"]]
        if b["state"] != "GROUNDED":
            continue
        k = key4(b.get("evidence") or {})
        if k in in_extract:
            x1 += 1
        else:
            x2 += 1
            x2_ids.append({"id": c["id"], "engine_row": list(k)})

    # ---- C-1〜C-4(主張の単位)
    c1 = sum(1 for c in scorable if c.get("parent_cues"))
    c2 = sum(1 for c in scorable if nb[c["id"]].get("parent_filtered"))
    c3y = sum(1 for c in scorable if c.get("column") and not c.get("column_ambiguous"))
    c4 = sum(1 for c in scorable
             if ob[c["id"]]["state"] != "GROUNDED"
             and nb[c["id"]]["state"] == "GROUNDED")
    counts = {
        "A-1 ③が発火した主張(会計が未確認の別名で保留)": len(a1),
        "A-2 ③以外の理由で保留になった主張": len(a2),
        "A-3 未確認の別名の行に結んだ主張": len(a3),
        "X-1 抜粋に在る行に結んだ主張": x1,
        "X-2 抜粋に無い行に結んだ主張": x2,
        "C-1 親の手がかりになり得る名前が区間に在る主張": c1,
        "C-2 親の全成分が支持され、絞りが働いた主張": c2,
        "C-3 列の手がかりが在る主張": c3y,
        "C-3 列の手がかりが無い主張": len(scorable) - c3y,
        "C-4 旧では保留・新では接続になった主張": c4,
    }

    print("engine の sha:", json.dumps(shas, ensure_ascii=False))
    print("索引 %d / 語彙 %d / 列の手がかり %d"
          % (n["entries"], n["vocabulary"], n["column_cues"]))
    print("切り出した数 %d / 採点対象(主語あり)%d" % (len(claims), len(scorable)))
    print("旧:", json.dumps(o_split, ensure_ascii=False))
    print("新:", json.dumps(n_split, ensure_ascii=False))
    print(json.dumps(counts, ensure_ascii=False, indent=1))
    if a1:
        print("**③が発火した主張:**")
        for z in a1:
            print("   ", z["id"], z["会計"])
    else:
        print("**③は 1 件も発火していない。封 §8 により「未測定」になる。**")
    if a3:
        print("**未確認の別名の行に結んだ主張(A-3。線は 0 件):**")
        for z in a3:
            print("   ", z)
    if x2_ids:
        print("**抜粋に無い行に結んだ主張(X-2):**")
        for z in x2_ids:
            print("   ", z["id"], z["engine_row"])
    print("新の保留の理由:")
    for k, v in sorted(n_why.items(), key=lambda x: -x[1]):
        print("   %-58s %d" % (k, v))

    rec = {"purpose": ("段 9 の接続の結果(旧・新の 2 本)。"
                       "**合否は採点の script で出す**"),
           "seal": "docs/DOMAIN1_M9_SEAL_2026-10-16.md",
           "old_engine": "measure/sheet_m5_engine_2026-10-15.py",
           "new_engine": "measure/sheet_m7_engine_2026-10-15.py",
           "engine_sha": shas,
           "engine_unchanged": True,
           "applied_times": 1,
           "entries": n["entries"], "vocabulary": n["vocabulary"],
           "column_cues": n["column_cues"],
           "alias_passed": sorted(n["alias"]["table"]),
           "alias_unconfirmed": len(n["alias"]["unconfirmed"]),
           "counts": {"claims": len(claims), "scorable": len(scorable),
                      "old_split": o_split, "new_split": n_split,
                      "old_hold_reasons": o_why, "new_hold_reasons": n_why,
                      "novelty": dict(collections.Counter(
                          c["novelty"] for c in claims)),
                      "novelty_scorable": dict(collections.Counter(
                          c["novelty"] for c in scorable))},
           "claim_level_counts": counts,
           "A-1_詳細": a1, "A-2_詳細": a2, "A-3_詳細": a3, "X-2_詳細": x2_ids,
           "note": ("A-1〜A-3 と X-1 / X-2 は**ラベルを使わない**指標。"
                    "**A-2 を③の成功に数えない**(封 §6-1)。"
                    "**A-1 = 0 なら③は未測定**(封 §8)"),
           "unit_note": ("C-1〜C-4 は**主張の単位**。生成前に数えた "
                         "`m9_opportunity_2026-10-16.json` は**行(セル)の単位**で、"
                         "**単位が違うので並べて比べない**"),
           "claims": claims,
           "binds_old": [ob[c["id"]] for c in claims],
           "binds_new": [nb[c["id"]] for c in claims]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
