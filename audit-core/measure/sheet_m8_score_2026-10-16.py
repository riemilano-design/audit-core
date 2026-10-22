# -*- coding: utf-8 -*-
"""段 8 の採点(封 docs/DOMAIN1_M8_SEAL_2026-10-16.md §3〜§5)。**ラベルを見る前に書く。**

  G-1 接続の正確さ   `agree_6` が一致 / 採点対象         ≥ 50%
  G-2 誤接続         GROUNDED だがラベルと違う / 保留なのに GROUNDED   = 0 件
  G-3 根拠なしの接続 ラベルが「根拠なし」なのに GROUNDED               = 0 件
  G-4 保留の適切さ   ラベルが保留の主張を GROUNDED 以外にできた割合    ≥ 80%
  G-5 母数           採点対象の数                                      ≥ 20
  **G-7 正しい接続の増分(新 − 旧)                                    ≥ 1 件**
  **G-8 誤受理の増分(新 − 旧)                                        = 0 件**

**合否は新 engine の数で出す。旧は増分のためだけに並べ、良い方を選ばない**(封 §4)。
**主指標 E2 = 誤受理の件数 = G-2 + G-3。線は 0 件。**
封 §3 の N-1〜N-5 を**別々に**書く。**N-1 の分母が 0 なら `未測定`**(`合格` と書かない)。
**G-4 も分母が 0 なら `未測定`**(段 6 の封 §4-1 を継ぐ)。
2 席が食い違った行は**判定不能として分母に残す**。
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
BINDS = os.path.join(FX, "m8_binds_2026-10-16.json")
MAT = os.path.join(FX, "m8_material_2026-10-16.json")
SEAT1 = os.path.join(FX, "m8_answers_seat1_2026-10-16.json")
SEAT2 = os.path.join(FX, "m8_answers_seat2_2026-10-16.json")
OUT = os.path.join(FX, "m8_score_2026-10-16.json")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


L = _mod("label_spec_for_score7", "sheet_label_spec_2026-10-15.py")
E = _mod("m7_for_score", "sheet_m7_engine_2026-10-15.py")
M2 = L.M2
norm = M2.norm
ALIAS = None
F6 = L.FIELDS
F4 = ("会計", "階層", "科目名", "列")


def answer_key(a, fields):
    n = L.normalize_answer(a, ALIAS)
    if n.get("verdict"):
        return ("verdict", n["verdict"])
    return ("label", tuple(n.get(f, "") for f in fields))


def engine_key(b, fields):
    lab = L.engine_label(b, ALIAS)
    if lab is None:
        return None
    return ("label", tuple(lab.get(f, "") for f in fields))


def confirmed(a1, a2, fields):
    k1, k2 = answer_key(a1, fields), answer_key(a2, fields)
    if k1 == k2:
        return k1, True
    return ("verdict", norm("判定不能")), False


def tally(binds, claims, scorable, s1, s2):
    """1 本の engine を採点する。**旧にも新にも同じ関数を当てる。**"""
    rows, agree, g1, g2, g3, agree4, only4 = [], 0, 0, 0, 0, 0, 0
    hold_total = hold_ok = 0
    split = {"接続数": 0, "保留数": 0, "対象外数": 0}
    why = collections.Counter()
    for cid in scorable:
        a1, a2 = s1.get(cid, {}), s2.get(cid, {})
        label6, same = confirmed(a1, a2, F6)
        label4, _ = confirmed(a1, a2, F4)
        agree += 1 if same else 0
        b = binds[cid]
        ek6, ek4 = engine_key(b, F6), engine_key(b, F4)
        row = {"id": cid, "value": claims[cid]["value"],
               "novelty": claims[cid].get("novelty"),
               "sentence": claims[cid]["sentence"],
               "label6": label6, "label4": label4, "seats_agree": same,
               "state": b["state"], "route": b["route"], "pointer": b["pointer"],
               "hold_reason": b.get("hold_reason"),
               "parent_cues": b.get("parent_cues"),
               "parent_filtered": b.get("parent_filtered"),
               "parent_kept": b.get("parent_kept"),
               "engine_parent": (b.get("evidence") or {}).get("parent"),
               "engine_key6": ek6, "agree_6": False, "agree_4": False,
               "only_4": False, "verdict": None, "parent_correct": None}
        if b["state"] == "GROUNDED":
            split["接続数"] += 1
        elif b["state"] == "POINTER_NOT_FOUND":
            split["対象外数"] += 1
        else:
            split["保留数"] += 1
            why[b.get("hold_reason") or "(理由なし)"] += 1
        row["agree_6"] = bool(ek6 is not None and label6[0] == "label" and ek6 == label6)
        row["agree_4"] = bool(ek4 is not None and label4[0] == "label" and ek4 == label4)
        row["only_4"] = bool(row["agree_4"] and not row["agree_6"])
        agree4 += 1 if row["agree_4"] else 0
        only4 += 1 if row["only_4"] else 0
        # N-1 / N-2: 親で絞った主張について、残った親がラベルの親と合うか
        if b.get("parent_filtered"):
            kept = [norm(x.replace(" ", "")) for x in (b.get("parent_kept") or [])]
            lp = label6[1][2] if label6[0] == "label" else None
            row["label_parent"] = lp
            row["parent_correct"] = (None if lp is None
                                     else (len(kept) == 1 and kept[0] == lp))
        if label6[0] == "label":
            if row["agree_6"]:
                g1 += 1
                row["verdict"] = "正しい接続"
            elif ek6 is not None:
                g2 += 1
                row["verdict"] = "誤接続"
                row["wrong_fields"] = [f for f, x, y in zip(F6, ek6[1], label6[1])
                                       if x != y]
            else:
                row["verdict"] = "結べなかった(誤接続ではない)"
        else:
            hold_total += 1
            if ek6 is None:
                hold_ok += 1
                row["verdict"] = "正しく保留"
            else:
                row["verdict"] = "根拠なし/判定不能なのに接続した"
                if label6[1] == norm("根拠なし"):
                    g3 += 1
                else:
                    g2 += 1
        rows.append(row)
    return {"rows": rows, "seats_agree_6": agree, "g1": g1, "g2": g2, "g3": g3,
            "e2": g2 + g3, "hold_total": hold_total, "hold_ok": hold_ok,
            "agree_4": agree4, "only_4": only4, "split": split,
            "hold_reasons": dict(why),
            "n1": sum(1 for r in rows if r["parent_correct"] is True),
            "n2": sum(1 for r in rows if r["parent_correct"] is False),
            "n1_unknown": sum(1 for r in rows if r["parent_filtered"]
                              and r["parent_correct"] is None),
            "parent_filtered": sum(1 for r in rows if r["parent_filtered"])}


def main():
    global ALIAS
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    raw = E.fix_total_level(E.build_index(
        M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
        M2.parse_meisai(books[M2.MEISAI])))
    ALIAS = E.alias_table(raw)["table"]
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
    g1_rate = (float(new["g1"]) / n) if n else None
    g4_rate = (float(new["hold_ok"]) / new["hold_total"]) if new["hold_total"] else None
    g7 = new["g1"] - old["g1"]
    g8 = new["e2"] - old["e2"]
    lines = {
        "G-1 接続の正確さ": {"rate": g1_rate, "num": new["g1"], "den": n,
                             "pass": "≥ 50%",
                             "ok": (g1_rate is not None and g1_rate >= 0.50)},
        "G-2 誤接続": {"count": new["g2"], "pass": "= 0 件", "ok": new["g2"] == 0},
        "G-3 根拠なしの接続": {"count": new["g3"], "pass": "= 0 件", "ok": new["g3"] == 0},
        "G-4 保留の適切さ": {"rate": g4_rate, "num": new["hold_ok"],
                             "den": new["hold_total"], "pass": "≥ 80%",
                             "status": ("未測定" if new["hold_total"] == 0
                                        else ("合格" if g4_rate >= 0.80 else "失敗")),
                             "ok": (True if new["hold_total"] == 0 else g4_rate >= 0.80)},
        "G-5 母数": {"count": n, "pass": "≥ 20", "ok": n >= 20},
        "G-7 正しい接続の増分": {"count": g7, "pass": "≥ 1 件", "ok": g7 >= 1,
                                 "old": old["g1"], "new": new["g1"]},
        "G-8 誤受理の増分": {"count": g8, "pass": "= 0 件", "ok": g8 == 0,
                             "old": old["e2"], "new": new["e2"]},
    }
    # 封 §4-1 の X-1〜X-4。**X-2 に入った主張が全部誤受理になる**という予測の照合。
    OPP = _mod("opp8_for_score", "sheet_m8_opportunity_2026-10-16.py")
    mat = json.load(io.open(MAT, encoding="utf-8"))
    # **両側に同じ正規化を掛ける。**`norm(None)` は `None` を返すので、
    # 空欄を `""` に畳んでから比べる(engine 側の鍵は空欄を `""` で持つ)。
    def _k(scope, level, parent, name):
        return tuple(norm(x) or "" for x in (scope, level, parent, name))

    in_extract = {_k(c["scope"], c["level"], c["parent"], c["name"])
                  for c in OPP.cells_of(OPP.extract_of(mat))}
    x1 = x2 = x3 = x4 = 0
    x_detail = []
    for r in new["rows"]:
        if r["state"] != "GROUNDED" or r["engine_key6"] is None:
            continue
        k = r["engine_key6"][1]
        inside = _k(k[0], k[1], k[2], k[3]) in in_extract
        wrong = r["verdict"] in ("誤接続", "根拠なし/判定不能なのに接続した")
        if inside:
            x1 += 1
            x4 += 1 if wrong else 0
        else:
            x2 += 1
            x3 += 1 if wrong else 0
        if wrong or not inside:
            x_detail.append({"id": r["id"], "抜粋に在る行": inside,
                             "verdict": r["verdict"],
                             "engine_row": list(k[:4])})
    xs = {"X-1 抜粋に在る行に結んだ": x1, "X-2 抜粋に無い行に結んだ": x2,
          "X-3 X-2 のうち誤受理": x3, "X-4 抜粋に在る行に結んで誤受理": x4}

    # 封 §3: **N-1 の分母が 0 なら主目的は `未測定`**
    n1_den = new["parent_filtered"]
    main_status = "未測定" if n1_den == 0 else ("合格" if new["n2"] == 0 else "失敗")
    g4_unmeasured = (lines["G-4 保留の適切さ"]["status"] == "未測定")
    if n < 20:
        overall = "判定不能(母数不足)"
    elif not all(v["ok"] for v in lines.values()):
        overall = "失敗"
    elif main_status == "未測定" and g4_unmeasured:
        overall = "合格(ただし主目的と G-4 は未測定)"
    elif main_status == "未測定":
        overall = "合格(ただし主目的は未測定)"
    elif g4_unmeasured:
        overall = "合格(ただし G-4 は未測定)"
    else:
        overall = "合格"
    novelty = collections.Counter(r["novelty"] for r in new["rows"])

    print("採点対象 %d 件 / 2 席が 6 欄で一致 %d 件 / ラベルが保留 %d 件"
          % (n, new["seats_agree_6"], new["hold_total"]))
    print("主指標 **E2(誤受理)= %d 件**(G-2 %d + G-3 %d)"
          % (new["e2"], new["g2"], new["g3"]))
    print("旧:", json.dumps(old["split"], ensure_ascii=False),
          "/ 正しい接続 %d / E2 %d" % (old["g1"], old["e2"]))
    print("新:", json.dumps(new["split"], ensure_ascii=False),
          "/ 正しい接続 %d / E2 %d" % (new["g1"], new["e2"]))
    for k, v in lines.items():
        if "rate" in v:
            print("  %-16s %s (%d/%d)  合格線 %s  %s"
                  % (k, "―" if v["rate"] is None else "%.1f%%" % (v["rate"] * 100),
                     v["num"], v["den"], v["pass"], "○" if v["ok"] else "×"))
        else:
            print("  %-16s %d 件  合格線 %s  %s"
                  % (k, v["count"], v["pass"], "○" if v["ok"] else "×"))
    print("封 §3 の 5 つ:")
    print("  N-1 親を正しく抽出 %d 件 / N-2 親を誤って抽出 %d 件 "
          "(分母 = 親で絞った主張 %d 件、判定できず %d 件)"
          % (new["n1"], new["n2"], n1_den, new["n1_unknown"]))
    print("  N-3 正しく接続 %d 件 / N-4 誤接続(E2)%d 件 / N-5 保留 %d 件"
          % (new["g1"], new["e2"], new["split"]["保留数"]))
    print("  主目的(親の抽出)の判定: **%s**" % main_status)
    if g4_unmeasured:
        print("  ※ G-4 は**未測定**(ラベルが保留の行が 0 件)")
    print("封 §4-1 の X:", json.dumps(xs, ensure_ascii=False))
    for z in x_detail:
        print("   ", z["id"], "抜粋に在る行" if z["抜粋に在る行"] else "**抜粋に無い行**",
              z["verdict"], z["engine_row"])
    print("総合: %s" % overall)
    print("参考(合否に使わない): agree_4 %d / **only_4 %d**"
          % (new["agree_4"], new["only_4"]))
    print("新規 %d / 再出 %d" % (novelty.get("新規", 0), novelty.get("再出", 0)))
    if missing:
        print("席の回答が無い主張:", missing)

    rec = {"purpose": "段 8 の採点(封 §3〜§5)。閾値は封じたもので、結果を見て変えていない",
           "seal": "docs/DOMAIN1_M8_SEAL_2026-10-16.md",
           "verdict_from": "新 engine。旧は増分のためだけに並べた(封 §4)",
           "scorable": n, "seats_agree_6": new["seats_agree_6"],
           "hold_total": new["hold_total"],
           "E2_誤受理": new["e2"], "lines": lines, "overall": overall,
           "main_objective_status": main_status,
           "N-1_親を正しく抽出": new["n1"], "N-2_親を誤って抽出": new["n2"],
           "N-1_分母_親で絞った主張": n1_den, "N-1_判定できず": new["n1_unknown"],
           "N-3_正しく接続": new["g1"], "N-4_誤接続": new["e2"],
           "N-5_保留": new["split"]["保留数"],
           "X": xs, "X_詳細": x_detail,
           "X_note": ("封 §4-1。段 7 の実測は X-1 20・X-2 6・X-3 6・X-4 0 で、"
                      "**抜粋に無い行に結んだ 6 件が 6 件すべて誤受理**だった"),
           "old": {k: old[k] for k in ("g1", "g2", "g3", "e2", "split",
                                       "hold_reasons", "agree_4", "only_4",
                                       "hold_total", "hold_ok")},
           "new_split": new["split"], "new_hold_reasons": new["hold_reasons"],
           "reference_only": {"agree_4": new["agree_4"], "only_4": new["only_4"]},
           "g4_unmeasured": g4_unmeasured,
           "spec_version": L.SPEC["version"],
           "novelty": dict(novelty),
           "independent_confirmation": novelty.get("新規", 0) >= 10,
           "novelty_rule": "新規 10 件未満なら『独立に確認した』とは表現しない",
           "missing_answers": missing,
           "rows": new["rows"], "rows_old": old["rows"]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
