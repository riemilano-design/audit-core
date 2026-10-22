# -*- coding: utf-8 -*-
"""段 9 の採点(封 docs/DOMAIN1_M9_SEAL_2026-10-16.md §6)。**ラベルを見る前に書く。**

主実験(③)の線 ― **6 本すべてを満たして初めて合格**:
  A-1 ③が発火した主張数                                     ≥ 1 件
  A-3 未確認の別名の行に結んだ主張数                         = 0 件
  E2  誤受理 = G-2 誤接続 + G-3 根拠なしの接続               = 0 件
  X-2 抜粋に無い行に結んだ主張数                             = 0 件
  G-5 採点対象の数                                           ≥ 20 件
  G-1′ **③で止めた主張を分母から除いた**接続の正確さ        ≥ 50%

併測(**③の合否に入れない**):
  G-4 ラベルが保留の主張を GROUNDED 以外にできた割合  ≥ 80%(**分母 0 なら未測定**)
      分母は (a) 両席が一致して保留 / (b) 2 席が食い違って保留 に**割って書く**

記録のみ(線にしない): **生の G-1**・G-7・席の一致率・N-1 / N-2。
**G-8 = 0 は線に残す。G-7 は線から外す**(③は接続を増やす規則ではない)。

**A-1 = 0 なら③は「未測定」**(封 §8)。合格と書かない。
**止めた主張(A-1 + A-2)が採点対象の半分を超えたら G-1′ を成果として書かない。**

    python3 measure/sheet_m9_score_2026-10-16.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
BINDS = os.path.join(FX, "m9_binds_2026-10-16.json")
MAT = os.path.join(FX, "m9_material_2026-10-16.json")
SEAT1 = os.path.join(FX, "m9_answers_seat1_2026-10-16.json")
SEAT2 = os.path.join(FX, "m9_answers_seat2_2026-10-16.json")
OUT = os.path.join(FX, "m9_score_2026-10-16.json")

G1P_MIN = 0.50
G4_MIN = 0.80
G5_MIN = 20
ALIAS_HOLD_MARK = "会計が未確認の別名"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


L9 = _mod("spec9_for_score", "sheet_label_spec_m9_2026-10-16.py")
S8 = _mod("m8score_for_m9", "sheet_m8_score_2026-10-16.py")
RUN = _mod("run9_for_score", "sheet_m9_run_2026-10-16.py")
E = _mod("m7_for_score9", "sheet_m7_engine_2026-10-15.py")
OPP = _mod("opp9_for_score", "sheet_m9_opportunity_2026-10-16.py")
M2 = L9.M2
norm = M2.norm

# **採点の対の作り方・正規化は段 8 と同じ器を使う**(両側に同じ正規化が掛かることは
# `measure/sheet_symmetry_audit_2026-10-16.py` が S-1〜S-5 で確かめてある)
tally = S8.tally
confirmed = S8.confirmed


def main():
    if os.path.exists(OUT):
        raise SystemExit("採点が既に在る: %s(採点し直さない)" % OUT)
    shas = RUN.check_shas()          # **封 §4。違えば結果は無効**
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    raw = E.fix_total_level(E.build_index(
        M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
        M2.parse_meisai(books[M2.MEISAI])))
    alias = E.alias_table(raw)
    S8.ALIAS = alias["table"]
    unconf = {norm(u["name"]) for u in alias["unconfirmed"]}

    rec_in = json.load(io.open(BINDS, encoding="utf-8"))
    claims = {c["id"]: c for c in rec_in["claims"]}
    bo = {b["claim_id"]: b for b in rec_in["binds_old"]}
    bn = {b["claim_id"]: b for b in rec_in["binds_new"]}
    s1 = {a["id"]: a for a in json.load(io.open(SEAT1, encoding="utf-8"))["answers"]}
    s2 = {a["id"]: a for a in json.load(io.open(SEAT2, encoding="utf-8"))["answers"]}
    scorable = sorted(cid for cid, c in claims.items() if c.get("scorable"))
    missing = [cid for cid in scorable if cid not in s1 or cid not in s2]

    old = tally(bo, claims, scorable, s1, s2)
    new = tally(bn, claims, scorable, s1, s2)
    n = len(scorable)

    # ---- ③の 3 つの件数(**ラベルを使わない**。run と同じ定義で数え直す)
    a1, a2, a3 = [], [], []
    for cid in scorable:
        b = bn[cid]
        if b["state"] == "GROUNDED":
            if norm((b.get("evidence") or {}).get("scope")) in unconf:
                a3.append(cid)
            continue
        if b["state"] == "POINTER_NOT_FOUND":
            continue
        if b.get("unconfirmed_scope") or ALIAS_HOLD_MARK in (b.get("hold_reason") or ""):
            a1.append(cid)
        else:
            a2.append(cid)

    # ---- X-1 / X-2 / X-3 / X-4(**両側に同じ正規化を掛け、空欄を "" に畳む**)
    mat = json.load(io.open(MAT, encoding="utf-8"))

    def key4(d):
        return tuple(norm(d.get(k)) or ""
                     for k in ("scope", "level", "parent", "name"))

    in_extract = {key4(c) for c in OPP.cells_of(OPP.extract_of(mat))}
    x1 = x2 = x3 = x4 = 0
    x_detail = []
    for r in new["rows"]:
        if r["state"] != "GROUNDED" or r["engine_key6"] is None:
            continue
        ev = bn[r["id"]].get("evidence") or {}
        inside = key4(ev) in in_extract
        wrong = r["verdict"] in ("誤接続", "根拠なし/判定不能なのに接続した")
        if inside:
            x1 += 1
            if wrong:
                x4 += 1
        else:
            x2 += 1
            x_detail.append({"id": r["id"], "engine_row": list(key4(ev)),
                             "verdict": r["verdict"]})
            if wrong:
                x3 += 1

    # ---- G-1′: **③で止めた主張を分母から除く**
    g1 = new["g1"]
    den_p = n - len(a1)
    g1p = (float(g1) / den_p) if den_p else None
    g1_rate = (float(g1) / n) if n else None
    # ---- G-4 の分母を (a) 両席一致 / (b) 食い違い に割る
    g4a = g4b = g4a_ok = g4b_ok = 0
    for r in new["rows"]:
        if r["label6"][0] != "verdict":
            continue
        ok = r["engine_key6"] is None
        if r["seats_agree"]:
            g4a += 1
            g4a_ok += 1 if ok else 0
        else:
            g4b += 1
            g4b_ok += 1 if ok else 0
    g4_den = new["hold_total"]
    g4_rate = (float(new["hold_ok"]) / g4_den) if g4_den else None
    g7 = new["g1"] - old["g1"]
    g8 = new["e2"] - old["e2"]
    stopped = len(a1) + len(a2)

    lines = {
        "A-1 ③が発火した主張": {"count": len(a1), "pass": "≥ 1 件",
                                "ok": len(a1) >= 1, "ids": a1},
        "A-3 未確認の別名の行に結んだ主張": {"count": len(a3), "pass": "= 0 件",
                                            "ok": len(a3) == 0, "ids": a3},
        "E2 誤受理": {"count": new["e2"], "pass": "= 0 件", "ok": new["e2"] == 0,
                      "G-2": new["g2"], "G-3": new["g3"]},
        "X-2 抜粋に無い行に結んだ主張": {"count": x2, "pass": "= 0 件",
                                        "ok": x2 == 0},
        "G-5 母数": {"count": n, "pass": "≥ %d" % G5_MIN, "ok": n >= G5_MIN},
        "G-1′ ③で止めた主張を除いた接続の正確さ": {
            "rate": g1p, "num": g1, "den": den_p, "pass": "≥ 50%",
            "ok": (g1p is not None and g1p >= G1P_MIN),
            "status": ("未測定" if den_p == 0
                       else ("合格" if g1p >= G1P_MIN else "失敗"))},
    }
    main_ok = all(v["ok"] for v in lines.values())
    unmeasured = len(a1) == 0 or den_p == 0
    if unmeasured:
        overall = "未測定(③が発火していない)" if len(a1) == 0 else "未測定(分母 0)"
    else:
        overall = "合格" if main_ok else "失敗"

    g4_line = {"rate": g4_rate, "num": new["hold_ok"], "den": g4_den,
               "pass": "≥ 80%",
               "status": ("未測定" if g4_den == 0
                          else ("合格" if g4_rate >= G4_MIN else "失敗")),
               "(a) 両席が一致して保留": {"den": g4a, "ok": g4a_ok},
               "(b) 2 席が食い違って保留": {"den": g4b, "ok": g4b_ok},
               "注": ("**(b) は「席が決められなかった」であって"
                      "「保留が適切だった」ではない。**"
                      "分母が 2 件以下なら「4 段続けて未確認」と書く"),
               "evaluable": g4_den > 2}
    recorded = {
        "生の G-1(線にしない)": {"rate": g1_rate, "num": g1, "den": n},
        "G-7 正しい接続の増分(線にしない)": {"count": g7, "old": old["g1"],
                                             "new": new["g1"]},
        "G-8 誤受理の増分": {"count": g8, "pass": "= 0 件", "ok": g8 == 0,
                             "old": old["e2"], "new": new["e2"]},
        "A-2 ③以外の理由で保留": {"count": len(a2), "ids": a2,
                                  "注": "**③の成功に数えない**"},
        "X-1": x1, "X-3 X-2 のうち誤受理": x3, "X-4 抜粋に在る行に結んで誤受理": x4,
        "席の一致率(成果として書かない)": {
            "num": new["seats_agree_6"], "den": n,
            "rate": (float(new["seats_agree_6"]) / n) if n else None},
        "N-1 親で絞って親が合った": new["n1"],
        "N-2 親で絞って親が違った": new["n2"],
        "N-1 の分母(親で絞った主張)": new["parent_filtered"],
    }
    g1p_usable = stopped * 2 <= n
    rec = {"purpose": "段 9 の採点。**③と G-4 を別々に判定する**",
           "seal": "docs/DOMAIN1_M9_SEAL_2026-10-16.md",
           "spec_version": L9.SPEC["version"],
           "engine_sha": shas,
           "scored_claims": n, "missing_answers": missing,
           "主実験(③)": lines,
           "主実験の判定": overall,
           "併測 G-4(③の合否に入れない)": g4_line,
           "記録のみ": recorded,
           "G-1′ を成果として書けるか": {
               "止めた主張(A-1 + A-2)": stopped, "採点対象": n,
               "usable": g1p_usable,
               "注": ("**止めた主張が採点対象の半分を超えたら G-1′ を成果として"
                      "書かない。**分母が偏っているので接続の正確さは測れていない")},
           "旧 engine": {"G-1": old["g1"], "E2": old["e2"],
                         "保留": old["split"]["保留数"]},
           "rows": new["rows"], "rows_old": old["rows"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=== 段 9 の採点(封 §6)===")
    print("採点対象 %d 件 / 回答の欠け %d" % (n, len(missing)))
    print("--- 主実験(③)---")
    for k, v in lines.items():
        if "rate" in v:
            print("  %-42s %s (%d/%d) [%s] %s"
                  % (k, "—" if v["rate"] is None else "%.1f%%" % (v["rate"] * 100),
                     v["num"], v["den"], v["pass"], "○" if v["ok"] else "×"))
        else:
            print("  %-42s %d 件 [%s] %s"
                  % (k, v["count"], v["pass"], "○" if v["ok"] else "×"))
    print("  **主実験の判定: %s**" % overall)
    print("--- 併測 G-4(③の合否に入れない)---")
    print("  G-4: %s (%d/%d) [%s] -> %s"
          % ("—" if g4_rate is None else "%.1f%%" % (g4_rate * 100),
             new["hold_ok"], g4_den, "≥ 80%", g4_line["status"]))
    print("     (a) 両席一致 %d 件(うち正しく保留 %d) / (b) 食い違い %d 件(うち %d)"
          % (g4a, g4a_ok, g4b, g4b_ok))
    if g4_den <= 2:
        print("     **分母が %d 件。4 段続けて未確認。合格扱いにしない。**" % g4_den)
    print("--- 記録のみ ---")
    print("  生の G-1: %s (%d/%d)"
          % ("—" if g1_rate is None else "%.1f%%" % (g1_rate * 100), g1, n))
    print("  G-7 %+d(旧 %d → 新 %d) / G-8 %+d"
          % (g7, old["g1"], new["g1"], g8))
    print("  A-2 %d 件(③の成功に数えない) / X-1 %d / X-3 %d / X-4 %d"
          % (len(a2), x1, x3, x4))
    print("  N-1 %d / N-2 %d(分母 %d)"
          % (new["n1"], new["n2"], new["parent_filtered"]))
    if not g1p_usable:
        print("  **止めた主張 %d 件が採点対象 %d 件の半分を超えた。"
              "G-1′ を成果として書かない。**" % (stopped, n))
    print("  新の保留の理由:")
    for k, v in sorted(new["hold_reasons"].items(), key=lambda x: -x[1]):
        print("     %-58s %d" % (k, v))
    if x_detail:
        print("  **抜粋に無い行に結んだ主張(X-2):**")
        for z in x_detail:
            print("     ", z)
    print("->", OUT)


if __name__ == "__main__":
    main()
