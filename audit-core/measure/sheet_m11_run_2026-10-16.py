# -*- coding: utf-8 -*-
"""段 11: 凍結した報告文に**旧と新の 2 本の engine**を当てる(封 §3・§11 の 6)。

**engine は 1 行も変えていない。**

  旧 = `measure/sheet_m7_engine_2026-10-15.py`(段 9 の新。**18 会計は未確認のまま**)
  新 = `measure/sheet_sainyuu_engine_2026-10-16.py`(歳入側の裏づけで**18 会計が昇格**)

**旧を並べる理由は増分のためではない**(封 §3)。
新 engine では**未確認の別名が 0 件**なので **A-1・A-3 は構造的に 0** になる。
**③が発火する機会が材料に在ったことは、旧 engine でしか観測できない。**

出すのは 2 本の接続の結果と、**ラベルを使わない**件数:

  A-1 ③が発火した主張数 / A-2 ③以外の理由の保留 / A-3 未確認の別名の行に結んだ数
      ― **旧と新の両方で数える**
  X-2 **3 通り**(対称 = 合否 / 非対称 = 開示だけ / 三欄 = 裏取り。封 §4)
  C-1〜C-4 生成前の O と同じものを**主張の単位**で(**単位が違うので並べない**)

**合否はここでは出さない**(採点は `sheet_m11_score_…py`)。

    python3 measure/sheet_m11_run_2026-10-16.py
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
REPORT = os.path.join(FX, "m11_report_2026-10-16.json")
MAT = os.path.join(FX, "m11_material_2026-10-16.json")
OUT = os.path.join(FX, "m11_binds_2026-10-16.json")
SEAL = "docs/DOMAIN1_M11_SEAL_2026-10-16.md"
OLDP = ("m4_binds_2026-10-15.json", "m5_binds_2026-10-15.json",
        "m6_binds_2026-10-15.json", "m7_binds_2026-10-15.json",
        "m8_binds_2026-10-16.json", "m9_binds_2026-10-16.json")
# 封 §1 の sha。**1 文字でも違えば結果を無効にする**
ENGINE_SHA = {
    "sheet_m5_engine_2026-10-15.py": "6eb5723ef518e1b4",
    "sheet_m7_engine_2026-10-15.py": "4574c3ea013d05a1",
    "sheet_parent_backing_2026-10-16.py": "8e387958c69398e8",
    "sheet_sainyuu_engine_2026-10-16.py": "3a70b599672832d3",
    "sheet_sainyuu_p1_2026-10-16.py": "91b15e0f7eaa5442",
    "sheet_sainyuu_p2_2026-10-16.py": "671c7dd81cea0ffe",
}
ALIAS_HOLD_MARK = "会計が未確認の別名"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


SE = _mod("sainyuu_for_run11", "sheet_sainyuu_engine_2026-10-16.py")
NEW = SE
OLD = SE.M7                      # 段 9 の新 engine(**凍結したまま**)
X2 = _mod("x2_for_run11", "sheet_m11_x2_2026-10-16.py")
OPP = X2.OPP11.OPP
M2 = SE.M2
norm = SE.norm


def engine_shas():
    out = {}
    for f in ENGINE_SHA:
        with io.open(os.path.join(HERE, f), "rb") as fh:
            out[f] = hashlib.sha256(fh.read()).hexdigest()[:16]
    return out


def check_shas():
    got = engine_shas()
    bad = {f: (ENGINE_SHA[f], got[f]) for f in ENGINE_SHA if got[f] != ENGINE_SHA[f]}
    if bad:
        raise SystemExit("**engine の sha が封と違う。結果は無効である**: %s"
                         % json.dumps(bad, ensure_ascii=False))
    return got


def a_counts(binds, alias, scorable):
    """A-1 / A-2 / A-3。**ラベルを使わない。**旧にも新にも同じ関数を当てる。

    **判定を 1 か所に置く** ― 新 engine では未確認が 0 件なので、
    字で書くと「③の判定を殺す変異」が新の側で黙る(封 §3)。
    """
    unconf = {norm(u["name"]) for u in alias["unconfirmed"]}
    a1, a2, a3 = [], [], []
    for cid in scorable:
        b = binds[cid]
        if b["state"] == "GROUNDED":
            ev = b.get("evidence") or {}
            if norm(ev.get("scope")) in unconf:
                a3.append({"id": cid, "会計": ev.get("scope"),
                           "科目名": ev.get("name"), "列": ev.get("column")})
            continue
        if b["state"] == "POINTER_NOT_FOUND":
            continue
        if b.get("unconfirmed_scope") or ALIAS_HOLD_MARK in (b.get("hold_reason") or ""):
            a1.append({"id": cid, "会計": b.get("unconfirmed_scope"),
                       "理由": b.get("hold_reason")})
        else:
            a2.append({"id": cid, "理由": b.get("hold_reason")})
    return {"A-1": a1, "A-2": a2, "A-3": a3,
            "未確認の別名の数": len(unconf)}


def main():
    if os.path.exists(OUT):
        raise SystemExit("接続の結果が既に在る: %s(当て直さない)" % OUT)
    shas = check_shas()
    report = json.load(io.open(REPORT, encoding="utf-8"))["report"]
    mat = json.load(io.open(MAT, encoding="utf-8"))
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
    sids = [c["id"] for c in scorable]

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
    a_old = a_counts(ob, o["alias"], sids)
    a_new = a_counts(nb, n["alias"], sids)

    # ---- X-2(**3 通り**。封 §4)**ラベルを使わない**
    cells = OPP.cells_of(OPP.extract_of(mat))
    x_old = X2.count(ob, cells, o["alias"]["table"])
    x_new = X2.count(nb, cells, n["alias"]["table"])

    # ---- C-1〜C-4(主張の単位)
    c1 = sum(1 for c in scorable if c.get("parent_cues"))
    c2 = sum(1 for c in scorable if nb[c["id"]].get("parent_filtered"))
    c3y = sum(1 for c in scorable if c.get("column") and not c.get("column_ambiguous"))
    c4 = sum(1 for c in scorable
             if ob[c["id"]]["state"] != "GROUNDED"
             and nb[c["id"]]["state"] == "GROUNDED")
    counts = {
        "A-1 ③が発火した主張(旧 engine)": len(a_old["A-1"]),
        "A-1 ③が発火した主張(新 engine)": len(a_new["A-1"]),
        "A-2 ③以外の理由で保留(旧 / 新)": [len(a_old["A-2"]), len(a_new["A-2"])],
        "A-3 未確認の別名の行に結んだ主張(旧 / 新)": [len(a_old["A-3"]),
                                        len(a_new["A-3"])],
        "未確認の別名の数(旧 / 新)": [a_old["未確認の別名の数"],
                             a_new["未確認の別名の数"]],
        "X-1 抜粋に在る行に結んだ主張(新・対称)": x_new["X-1対称"],
        "X-2対称(新。**合否**)": x_new["X-2対称"],
        "X-2非対称(新。**開示だけ**)": x_new["X-2非対称"],
        "X-2三欄(新。**裏取り**)": x_new["X-2三欄"],
        "X-2対称(旧)": x_old["X-2対称"],
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
    print("別名: 旧 %d 通り(未確認 %d)/ 新 %d 通り(未確認 %d・歳入で %d 昇格)"
          % (len(o["alias"]["table"]), len(o["alias"]["unconfirmed"]),
             len(n["alias"]["table"]), len(n["alias"]["unconfirmed"]),
             len(n["alias"]["promoted_by_sainyuu"])))
    print("旧:", json.dumps(o_split, ensure_ascii=False))
    print("新:", json.dumps(n_split, ensure_ascii=False))
    print(json.dumps(counts, ensure_ascii=False, indent=1))
    print("**X-2 の判定(新): %s**"
          % json.dumps(X2.verdict(x_new), ensure_ascii=False))
    if a_old["A-1"]:
        print("**③が発火した主張(旧 engine):**")
        for z in a_old["A-1"]:
            print("   ", z["id"], z["会計"])
    else:
        print("**③は旧 engine でも 1 件も発火していない。封 §8 により「未測定」。**")
    print("新の保留の理由:")
    for k, v in sorted(n_why.items(), key=lambda x: -x[1]):
        print("   %-58s %d" % (k, v))

    rec = {"purpose": ("段 11 の接続の結果(旧・新の 2 本)。"
                       "**合否は採点の script で出す**"),
           "seal": SEAL,
           "old_engine": "measure/sheet_m7_engine_2026-10-15.py",
           "new_engine": "measure/sheet_sainyuu_engine_2026-10-16.py",
           "engine_sha": shas, "engine_unchanged": True, "applied_times": 1,
           "min_independent": n["alias"]["min_independent"],
           "entries": n["entries"], "vocabulary": n["vocabulary"],
           "column_cues": n["column_cues"],
           "alias_old": {"通った": sorted(o["alias"]["table"]),
                         "未確認": len(o["alias"]["unconfirmed"])},
           "alias_new": {"通った": sorted(n["alias"]["table"]),
                         "未確認": len(n["alias"]["unconfirmed"]),
                         "歳入で昇格": [p["name"] for p in
                                  n["alias"]["promoted_by_sainyuu"]]},
           "counts": {"claims": len(claims), "scorable": len(scorable),
                      "old_split": o_split, "new_split": n_split,
                      "old_hold_reasons": o_why, "new_hold_reasons": n_why,
                      "novelty": dict(collections.Counter(
                          c["novelty"] for c in claims)),
                      "novelty_scorable": dict(collections.Counter(
                          c["novelty"] for c in scorable))},
           "claim_level_counts": counts,
           "A(旧 engine)": a_old, "A(新 engine)": a_new,
           "X-2(旧 engine)": x_old, "X-2(新 engine)": x_new,
           "X-2 の判定(新)": X2.verdict(x_new),
           "note": ("A-1〜A-3 と X-2 は**ラベルを使わない**指標。"
                    "**新 engine では未確認が 0 件なので A-1・A-3 は構造的に 0**"
                    "(封 §3。**生成より先に書いた**)。"
                    "**③の発火機会は旧 engine で観測する。**"),
           "x2_note": ("**X-2 は 3 通り。**合否は対称、非対称は**開示だけ**、"
                       "三欄は**別名表に依らない裏取り**(封 §4)。"
                       "**計数器の歯は人工材料で別に当ててある**"
                       "(`m11_x2_teeth_2026-10-16.json`)"),
           "unit_note": ("C-1〜C-4 は**主張の単位**。生成前に数えた "
                         "`m11_opportunity_2026-10-16.json` は**行(セル)の単位**で、"
                         "**単位が違うので並べて比べない**"),
           "claims": claims,
           "binds_old": [ob[c["id"]] for c in claims],
           "binds_new": [nb[c["id"]] for c in claims]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
