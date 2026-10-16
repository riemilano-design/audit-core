# -*- coding: utf-8 -*-
"""段 11 の採点(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §6)。**ラベルを見る前に書く。**

線は **7 本。すべて満たして初めて合格**:

  A-1(旧) 旧 engine で③が発火した主張数                     ≥ 1 件(0 なら未測定)
  E2(新・対称) 誤接続 + 根拠なしの接続                        = 0 件
  X-2対称(新) 抜粋に無い行に結んだ主張                        = 0 件
  X-2三欄(新) 同(会計を外した・別名表に依らない)               = 0 件
  β の 5 欄  別名表に依って一致した件の 5 欄の食い違い           = 0 件
  G-5       採点対象の数                                   ≥ 20 件
  G-1′(新)  ③で止めた主張を分母から除いた接続の正確さ            ≥ 50%(段 9 と同じ)

**合否に入れない**: N-接続-増・G-4・席の一致率・生の G-1。

**採点器は engine と同じ別名表を使う**(両側に同じ正規化)。
**非対称にした数も必ず併記する**(封 §4。片側だけ正規化するのは段 8 の欠陥)。
**循環は β の 5 欄で切る**(封 §5)。

    python3 measure/sheet_m11_score_2026-10-16.py
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
BINDS = os.path.join(FX, "m11_binds_2026-10-16.json")
MAT = os.path.join(FX, "m11_material_2026-10-16.json")
SEAT1 = os.path.join(FX, "m11_answers_seat1_2026-10-16.json")
SEAT2 = os.path.join(FX, "m11_answers_seat2_2026-10-16.json")
OUT = os.path.join(FX, "m11_score_2026-10-16.json")
SEAL = "docs/DOMAIN1_M11_SEAL_2026-10-16.md"

G1P_MIN = 0.50          # **段 9 の線。動かさない**
G4_MIN = 0.80
G5_MIN = 20
ALIAS_HOLD_MARK = "会計が未確認の別名"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


RUN = _mod("run11_for_score", "sheet_m11_run_2026-10-16.py")
X2 = RUN.X2
S8 = _mod("m8score_for_m11", "sheet_m8_score_2026-10-16.py")
L9 = _mod("spec9_for_m11score", "sheet_label_spec_m9_2026-10-16.py")
OPP = RUN.OPP
norm = RUN.norm
tally = S8.tally
confirmed = S8.confirmed


def beta_and_five_fields(binds, claims, ids, s1, s2, alias_table):
    """**β と循環を切る 5 欄**(封 §5)。

    β = 「別名表に依って一致した主張」 ―
    **会計の素の字では一致せず、別名表を当てて初めて一致した**主張。
    その β 件について、**会計を除いた 5 欄**を**別名表を切った状態で**数える。

    **判定を 1 か所に置く。**β = 0 の材料では字で書いた判定が黙る。
    """
    F6 = S8.F6
    F5 = tuple(f for f in F6 if f != "会計")
    beta, same, diff, unknown, detail = [], 0, 0, 0, []
    for cid in ids:
        a1, a2 = s1.get(cid, {}), s2.get(cid, {})
        S8.ALIAS = alias_table
        lab_sym, _ = confirmed(a1, a2, F6)
        ek_sym = S8.engine_key(binds[cid], F6)
        S8.ALIAS = {}
        lab_raw, _ = confirmed(a1, a2, F6)
        ek_raw = S8.engine_key(binds[cid], F6)
        hit_sym = (ek_sym is not None and lab_sym[0] == "label"
                   and ek_sym == lab_sym)
        hit_raw = (ek_raw is not None and lab_raw[0] == "label"
                   and ek_raw == lab_raw)
        if not (hit_sym and not hit_raw):
            continue                      # 別名表に依らずに一致した / 一致していない
        beta.append(cid)
        S8.ALIAS = {}                     # **別名表を使わない**
        lab5, _ = confirmed(a1, a2, F5)
        ek5 = S8.engine_key(binds[cid], F5)
        if lab5[0] != "label" or ek5 is None:
            unknown += 1
        elif ek5 == lab5:
            same += 1
        else:
            diff += 1
            detail.append({"id": cid, "engine": ek5[1], "label": lab5[1]})
    S8.ALIAS = alias_table
    return {"β 別名表に依って一致した主張": len(beta), "ids": beta,
            "5 欄の一致": same, "5 欄の食い違い": diff, "5 欄の判定不能": unknown,
            "食い違いの明細": detail[:5], "欄": list(F5),
            "空振りか": len(beta) == 0,
            "注": ("**β = 0 なら、この線は空振りである** ― "
                   "どの接続も別名表に依っていないので、循環を切る必要が生じなかった。"
                   "**空振りを「安全性の証拠」として書かない。**"
                   if not beta else
                   "**5 欄が食い違う件は正しい接続に数えない**(封 §5)")}


def main():
    if os.path.exists(OUT):
        raise SystemExit("採点が既に在る: %s(採点し直さない)" % OUT)
    shas = RUN.check_shas()          # **封 §1。違えば結果は無効**
    rec_in = json.load(io.open(BINDS, encoding="utf-8"))
    mat = json.load(io.open(MAT, encoding="utf-8"))
    claims = {c["id"]: c for c in rec_in["claims"]}
    bo = {b["claim_id"]: b for b in rec_in["binds_old"]}
    bn = {b["claim_id"]: b for b in rec_in["binds_new"]}
    s1 = {a["id"]: a for a in json.load(io.open(SEAT1, encoding="utf-8"))["answers"]}
    s2 = {a["id"]: a for a in json.load(io.open(SEAT2, encoding="utf-8"))["answers"]}
    scorable = sorted(cid for cid, c in claims.items() if c.get("scorable"))
    missing = [cid for cid in scorable if cid not in s1 or cid not in s2]
    n = len(scorable)

    # **engine を当て直して別名表を取る**(記録の字を信じない)
    books = {}
    for f in (RUN.M2.SOUKATU, RUN.M2.KESSAN, RUN.M2.MEISAI):
        books[f], _ = RUN.M2.M1.read(os.path.join(RUN.M2.CACHE, f))
    args = (RUN.M2.parse_soukatu(books[RUN.M2.SOUKATU]),
            RUN.M2.parse_kessan(books[RUN.M2.KESSAN]),
            RUN.M2.parse_meisai(books[RUN.M2.MEISAI]))
    raw = RUN.OLD.fix_total_level(RUN.OLD.build_index(*args))
    al_old = RUN.OLD.alias_table(raw)
    al_new = RUN.NEW.alias_table(raw)

    def score(binds, table):
        S8.ALIAS = table
        return tally(binds, claims, scorable, s1, s2)

    old = score(bo, al_old["table"])                  # 旧(対称)
    new = score(bn, al_new["table"])                  # 新(対称。**これが答え**)
    asym = score(bn, al_old["table"])                 # **非対称。開示だけ**
    S8.ALIAS = al_new["table"]

    # ---- ③の件数(**ラベルを使わない**。run と同じ関数で数え直す)
    a_old = RUN.a_counts(bo, al_old, scorable)
    a_new = RUN.a_counts(bn, al_new, scorable)
    a1_old = [z["id"] for z in a_old["A-1"]]
    a1_new = [z["id"] for z in a_new["A-1"]]
    a2_new = [z["id"] for z in a_new["A-2"]]
    a3_new = [z["id"] for z in a_new["A-3"]]

    # ---- X-2(**3 通り**。封 §4)
    cells = OPP.cells_of(OPP.extract_of(mat))
    x_new = X2.count(bn, cells, al_new["table"])
    x_verdict = X2.verdict(x_new)
    # X-2 のうち誤受理だったもの(段 9 の X-3 / X-4)
    wrongs = {r["id"] for r in new["rows"]
              if r["verdict"] in ("誤接続", "根拠なし/判定不能なのに接続した")}
    x2_ids = {z["id"] for z in x_new["X-2対称の明細"]}
    x3 = len(x2_ids & wrongs)
    x4 = len(wrongs - x2_ids)

    # ---- β と 5 欄(封 §5)
    ok_ids = [r["id"] for r in new["rows"] if r["verdict"] == "正しい接続"]
    beta = beta_and_five_fields(bn, claims, ok_ids, s1, s2, al_new["table"])
    # **5 欄が食い違う件は正しい接続に数えない**
    g1_adjusted = new["g1"] - beta["5 欄の食い違い"]

    # ---- G-1′: **③で止めた主張(新 engine)を分母から除く**(段 9 と同じ式)
    den_p = n - len(a1_new)
    g1p = (float(g1_adjusted) / den_p) if den_p else None
    g1_rate = (float(g1_adjusted) / n) if n else None
    stopped = len(a1_new) + len(a2_new)

    # ---- G-4(併測)
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

    lines = {
        "A-1(旧)③が発火した主張": {"count": len(a1_old), "pass": "≥ 1 件",
                             "ok": len(a1_old) >= 1, "ids": a1_old,
                             "注": "**新 engine では構造的に 0 件**(封 §3)"},
        "E2(新・対称)誤受理": {"count": new["e2"], "pass": "= 0 件",
                         "ok": new["e2"] == 0,
                         "G-2 誤接続": new["g2"], "G-3 根拠なし": new["g3"]},
        "X-2対称(新)": {"count": x_new["X-2対称"], "pass": "= 0 件",
                    "ok": x_new["X-2対称"] == 0},
        "X-2三欄(新)": {"count": x_new["X-2三欄"], "pass": "= 0 件",
                    "ok": x_new["X-2三欄"] == 0},
        "β の 5 欄の食い違い": {"count": beta["5 欄の食い違い"], "pass": "= 0 件",
                         "ok": beta["5 欄の食い違い"] == 0,
                         "β": beta["β 別名表に依って一致した主張"],
                         "空振りか": beta["空振りか"]},
        "G-5 母数": {"count": n, "pass": "≥ %d" % G5_MIN, "ok": n >= G5_MIN},
        "G-1′(新)③で止めた主張を除いた接続の正確さ": {
            "rate": g1p, "num": g1_adjusted, "den": den_p, "pass": "≥ 50%",
            "ok": (g1p is not None and g1p >= G1P_MIN),
            "status": ("未測定" if den_p == 0
                       else ("合格" if g1p >= G1P_MIN else "失敗"))},
    }
    main_ok = all(v["ok"] for v in lines.values())
    if len(a1_old) == 0:
        overall = "**未測定**(③が旧 engine でも発火していない)"
    elif den_p == 0 or x_new["結んだ主張"] == 0:
        overall = "**未測定**(分母 0)"
    else:
        overall = "合格" if main_ok else "**失敗**"

    g7 = new["g1"] - old["g1"]
    g8 = new["e2"] - old["e2"]
    rec = {"purpose": "段 11 の採点。**線は 7 本。合否に増分を入れない**",
           "seal": SEAL, "spec_version": L9.SPEC["version"],
           "engine_sha": shas, "min_independent": al_new["min_independent"],
           "scored_claims": n, "missing_answers": missing,
           "主実験の線(7 本)": lines,
           "主実験の判定": overall,
           "X-2 の 3 通り(封 §4)": {
               "X-2対称(合否)": x_new["X-2対称"],
               "X-2非対称(開示だけ)": x_new["X-2非対称"],
               "X-2三欄(裏取り)": x_new["X-2三欄"],
               "X-1対称": x_new["X-1対称"], "結んだ主張": x_new["結んだ主張"],
               "判定": x_verdict,
               "X-3 X-2 のうち誤受理": x3, "X-4 抜粋に在る行に結んで誤受理": x4,
               "機会": "fixtures/sheet/m11_opportunity_2026-10-16.json の O-8",
               "計数器の歯": "fixtures/sheet/m11_x2_teeth_2026-10-16.json(**人工材料**)"},
           "β と 5 欄(封 §5。循環を切る)": beta,
           "**非対称にしたときの数(開示。性能として書かない)**": {
               "正しい接続": asym["g1"], "誤接続": asym["g2"],
               "根拠なし": asym["g3"], "E2": asym["e2"],
               "注": ("**採点器だけ旧 engine の別名表にした場合。**"
                      "片側だけ正規化を掛けるのは段 8 の欠陥そのものなので、"
                      "**合否には使わない**(封 §4)")},
           "5 つを分けて数える(封 §6-1)": {
               "N-接続-正": {"旧": old["g1"], "新": new["g1"],
                          "5 欄で落とした件": beta["5 欄の食い違い"],
                          "採用した数": g1_adjusted},
               "N-接続-誤": {"旧": old["g2"], "新": new["g2"]},
               "N-保留": {"旧": old["hold_total"], "新": new["hold_total"],
                        "理由ごと(新)": new["hold_reasons"]},
               "N-別名-通": {"旧": len(al_old["table"]), "新": len(al_new["table"]),
                          "歳入で昇格した会計":
                              [p["name"] for p in al_new["promoted_by_sainyuu"]]},
               "N-別名-止": {"旧": len(al_old["unconfirmed"]),
                          "新": len(al_new["unconfirmed"]),
                          "理由ごと(旧)": dict(collections.Counter(
                              u.get("why") or "(理由なし)"
                              for u in al_old["unconfirmed"]))}},
           "併測 G-4(合否に入れない)": {
               "rate": g4_rate, "num": new["hold_ok"], "den": g4_den,
               "pass": "≥ 80%",
               "status": ("未測定" if g4_den == 0
                          else ("合格" if g4_rate >= G4_MIN else "失敗")),
               "(a) 両席が一致して保留": {"den": g4a, "ok": g4a_ok},
               "(b) 2 席が食い違って保留": {"den": g4b, "ok": g4b_ok},
               "注": ("**(b) は「席が決められなかった」であって"
                      "「保留が適切だった」ではない**")},
           "記録のみ(線にしない)": {
               "生の G-1": {"rate": g1_rate, "num": g1_adjusted, "den": n},
               "N-接続-増(合否に入れない)": {"count": g7, "旧": old["g1"],
                                   "新": new["g1"],
                                   "注": "**増えても合格にしない。減っても失敗にしない**"},
               "G-8 誤受理の増分": {"count": g8, "旧": old["e2"], "新": new["e2"]},
               "A-2 ③以外の理由で保留(新)": {"count": len(a2_new), "ids": a2_new,
                                     "注": "**③の成功に数えない**"},
               "A-3(新)": len(a3_new),
               "席の一致率(成果として書かない)": {
                   "num": new["seats_agree_6"], "den": n,
                   "rate": (float(new["seats_agree_6"]) / n) if n else None},
               "N-1 親で絞って親が合った": new["n1"],
               "N-2 親で絞って親が違った": new["n2"],
               "N-1 の分母": new["parent_filtered"]},
           "G-1′ を成果として書けるか": {
               "止めた主張(A-1 + A-2)": stopped, "採点対象": n,
               "usable": stopped * 2 <= n,
               "注": ("**止めた主張が採点対象の半分を超えたら G-1′ を成果として"
                      "書かない。**分母が偏っているので接続の正確さは測れていない")},
           "rows": new["rows"], "rows_old": old["rows"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=== 段 11 の採点(封 §6)===")
    print("採点対象 %d 件 / 回答の欠け %d" % (n, len(missing)))
    print("--- 主実験の線(7 本)---")
    for k, v in lines.items():
        if "rate" in v:
            print("  %-46s %s (%d/%d) [%s] %s"
                  % (k, "—" if v["rate"] is None else "%.1f%%" % (v["rate"] * 100),
                     v["num"], v["den"], v["pass"], "○" if v["ok"] else "×"))
        else:
            print("  %-46s %d 件 [%s] %s"
                  % (k, v["count"], v["pass"], "○" if v["ok"] else "×"))
    print("  **主実験の判定: %s**" % overall)
    print("--- X-2(3 通り)---")
    print("  対称 %d / **非対称 %d(開示だけ)** / 三欄 %d / 結んだ主張 %d"
          % (x_new["X-2対称"], x_new["X-2非対称"], x_new["X-2三欄"],
             x_new["結んだ主張"]))
    print("--- β(循環を切る)---")
    print("  β %d 件 / 5 欄 一致 %d・食い違い %d・判定不能 %d%s"
          % (beta["β 別名表に依って一致した主張"], beta["5 欄の一致"],
             beta["5 欄の食い違い"], beta["5 欄の判定不能"],
             " **← 空振り**" if beta["空振りか"] else ""))
    print("--- 非対称(開示。性能として書かない)---")
    print("  正しい接続 %d / 誤接続 %d / E2 %d"
          % (asym["g1"], asym["g2"], asym["e2"]))
    print("--- 併測・記録のみ ---")
    print("  G-4: %s (%d/%d) -> %s"
          % ("—" if g4_rate is None else "%.1f%%" % (g4_rate * 100),
             new["hold_ok"], g4_den, rec["併測 G-4(合否に入れない)"]["status"]))
    print("  生の G-1: %s (%d/%d) / N-接続-増 %+d(合否に入れない)/ G-8 %+d"
          % ("—" if g1_rate is None else "%.1f%%" % (g1_rate * 100),
             g1_adjusted, n, g7, g8))
    print("  A-1 旧 %d / 新 %d / A-2(新) %d / A-3(新) %d"
          % (len(a1_old), len(a1_new), len(a2_new), len(a3_new)))
    print("  席の一致率 %.1f%%(成果として書かない)"
          % (100.0 * new["seats_agree_6"] / n if n else 0))
    if stopped * 2 > n:
        print("  **止めた主張 %d 件が採点対象 %d 件の半分を超えた。"
              "G-1′ を成果として書かない。**" % (stopped, n))
    print("  新の保留の理由:")
    for k, v in sorted(new["hold_reasons"].items(), key=lambda x: -x[1]):
        print("     %-58s %d" % (k, v))
    print("->", OUT)


if __name__ == "__main__":
    main()
