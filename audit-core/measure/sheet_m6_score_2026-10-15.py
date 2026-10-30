# -*- coding: utf-8 -*-
"""段 6 の採点(封 docs/DOMAIN1_M6_SEAL_2026-10-15.md §5)。**ラベルを見る前に書く。**

  G-1 接続の正確さ   `agree_6` が一致 / 採点対象        合格線 ≥ 50%
  G-2 誤接続         GROUNDED だがラベルと違う / 保留なのに GROUNDED   = 0 件
  G-3 根拠なしの接続 ラベルが「根拠なし」なのに GROUNDED               = 0 件
  G-4 保留の適切さ   ラベルが保留の主張を GROUNDED 以外にできた割合    ≥ 80%
  G-5 母数           採点対象の数                                      ≥ 20

**合否は `agree_6`(新形式)だけで出す。`agree_4` は参考として併記する**(封 §1-4)。
**主指標 E2 = 誤受理の件数 = G-2 + G-3**(封 §7-2。率ではなく件数)。
**接続数・保留数・対象外数を分けて書く**(追記 2 の C)。
2 席が食い違った行は**判定不能として分母に残す**(封 §1-5)。

欄の対応(**この script で固定する**):
  会計 = scope / 階層 = level / 親 = parent(会計・合計・款 は空欄)/
  科目名 = name(会計・合計 は空欄)/ 列 = column / 値 = そのセルの値
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
BINDS = os.path.join(FX, "m6_binds_2026-10-15.json")
SEAT1 = os.path.join(FX, "m6_answers_seat1_2026-10-15.json")
SEAT2 = os.path.join(FX, "m6_answers_seat2_2026-10-15.json")
OUT = os.path.join(FX, "m6_score_2026-10-15.json")

def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


# **欄の対応は `SPEC` が持つ。この script は持たない**(封 §1-1)
L = _mod("label_spec_for_score", "sheet_label_spec_2026-10-15.py")
E = _mod("m5_for_score", "sheet_m5_engine_2026-10-15.py")
M2 = L.M2
norm = M2.norm
ALIAS_FOR_NORM = None       # main() で材料から作る

F6 = L.FIELDS
F4 = ("会計", "階層", "科目名", "列")


def _n(v):
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        return str(int(v))
    return norm(v) or ""


def answer_key(a, fields):
    """**`SPEC` の正規化を通してから**比べる(封 §1-3)。"""
    n = L.normalize_answer(a, ALIAS_FOR_NORM)
    if n.get("verdict"):
        return ("verdict", n["verdict"])
    return ("label", tuple(n.get(f, "") for f in fields))


def engine_key(b, fields):
    """GROUNDED 以外は接続していない。**欄の対応は `SPEC` が決める。**"""
    lab = L.engine_label(b, ALIAS_FOR_NORM)
    if lab is None:
        return None
    return ("label", tuple(lab.get(f, "") for f in fields))


def confirmed(a1, a2, fields):
    k1, k2 = answer_key(a1, fields), answer_key(a2, fields)
    if k1 == k2:
        return k1, True
    return ("verdict", norm("判定不能")), False


def main():
    global ALIAS_FOR_NORM
    books = {}
    for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
        books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
    raw = E.fix_total_level(E.build_index(
        M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
        M2.parse_meisai(books[M2.MEISAI])))
    ALIAS_FOR_NORM = E.alias_table(raw)["table"]
    rec_in = json.load(io.open(BINDS, encoding="utf-8"))
    claims = {c["id"]: c for c in rec_in["claims"]}
    binds = {b["claim_id"]: b for b in rec_in["binds"]}
    s1 = {a["id"]: a for a in json.load(io.open(SEAT1, encoding="utf-8"))["answers"]}
    s2 = {a["id"]: a for a in json.load(io.open(SEAT2, encoding="utf-8"))["answers"]}

    scorable = sorted(cid for cid, c in claims.items() if c.get("scorable"))
    missing = [cid for cid in scorable if cid not in s1 or cid not in s2]
    rows, agree = [], 0
    g1 = g2 = g3 = only4 = agree4 = 0
    hold_total = hold_ok = 0
    split = {"接続数": 0, "保留数": 0, "対象外数": 0}
    hold_reasons = collections.Counter()
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
               "seat1": answer_key(a1, F6), "seat2": answer_key(a2, F6),
               "label6": label6, "label4": label4, "seats_agree": same,
               "state": b["state"], "route": b["route"], "pointer": b["pointer"],
               "hold_reason": b.get("hold_reason"),
               "engine_key6": ek6, "engine_key4": ek4,
               "agree_6": False, "agree_4": False, "only_4": False, "verdict": None}
        if b["state"] == "GROUNDED":
            split["接続数"] += 1
        elif b["state"] == "POINTER_NOT_FOUND":
            split["対象外数"] += 1
        else:
            split["保留数"] += 1
            hold_reasons[b.get("hold_reason") or "(理由なし)"] += 1

        row["agree_6"] = bool(ek6 is not None and label6[0] == "label" and ek6 == label6)
        row["agree_4"] = bool(ek4 is not None and label4[0] == "label" and ek4 == label4)
        row["only_4"] = bool(row["agree_4"] and not row["agree_6"])
        agree4 += 1 if row["agree_4"] else 0
        only4 += 1 if row["only_4"] else 0

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

    n = len(scorable)
    g1_rate = (float(g1) / n) if n else None
    g4_rate = (float(hold_ok) / hold_total) if hold_total else None
    e2 = g2 + g3
    lines = {
        "G-1 接続の正確さ": {"rate": g1_rate, "num": g1, "den": n, "pass": "≥ 50%",
                             "ok": (g1_rate is not None and g1_rate >= 0.50)},
        "G-2 誤接続": {"count": g2, "pass": "= 0 件", "ok": g2 == 0},
        "G-3 根拠なしの接続": {"count": g3, "pass": "= 0 件", "ok": g3 == 0},
        # 封 §4-1: **分母が 0 なら合格と書かない。`未測定` にする**
        "G-4 保留の適切さ": {"rate": g4_rate, "num": hold_ok, "den": hold_total,
                             "pass": "≥ 80%",
                             "status": ("未測定" if hold_total == 0
                                        else ("合格" if g4_rate >= 0.80 else "失敗")),
                             "ok": (True if hold_total == 0 else g4_rate >= 0.80)},
        "G-5 母数": {"count": n, "pass": "≥ 20", "ok": n >= 20},
    }
    g4_unmeasured = (lines["G-4 保留の適切さ"]["status"] == "未測定")
    if n < 20:
        overall = "判定不能(母数不足)"
    elif not all(v["ok"] for v in lines.values()):
        overall = "失敗"
    elif g4_unmeasured:
        overall = "合格(ただし G-4 は未測定)"
    else:
        overall = "合格"
    novelty = collections.Counter(r["novelty"] for r in rows)
    independent = novelty.get("新規", 0) >= 10

    print("採点対象 %d 件 / 2 席が 6 欄で一致 %d 件 / ラベルが保留 %d 件"
          % (n, agree, hold_total))
    print("主指標 **E2(誤受理)= %d 件**(G-2 %d + G-3 %d)" % (e2, g2, g3))
    print("追記 2 の C ―", json.dumps(split, ensure_ascii=False))
    for k, v in hold_reasons.items():
        print("   保留の理由: %s = %d 件" % (k, v))
    for k, v in lines.items():
        if "rate" in v:
            print("  %-16s %s (%d/%d)  合格線 %s  %s"
                  % (k, "―" if v["rate"] is None else "%.1f%%" % (v["rate"] * 100),
                     v["num"], v["den"], v["pass"], "○" if v["ok"] else "×"))
        else:
            print("  %-16s %d 件  合格線 %s  %s"
                  % (k, v["count"], v["pass"], "○" if v["ok"] else "×"))
    print("親が必要だった主張 %d 件 / そのうち正しく結べた %d 件"
          % (sum(1 for r in rows if binds[r["id"]].get("parent_required")),
             sum(1 for r in rows if binds[r["id"]].get("parent_required")
                 and r["agree_6"])))
    if g4_unmeasured:
        print("  ※ G-4 は**未測定**(ラベルが保留の行が 0 件)。"
              "「保留の適切さを確かめた」とは書かない")
    print("総合: %s" % overall)
    print("参考(合否に使わない): agree_4 %d 件 / **only_4 %d 件**" % (agree4, only4))
    print("追記 2 の D ― 新規 %d / 再出 %d → 独立した確認と呼べるか: %s"
          % (novelty.get("新規", 0), novelty.get("再出", 0),
             "呼べる" if independent else "**呼べない(新規 10 件未満)**"))
    if missing:
        print("席の回答が無い主張:", missing)

    rec = {"purpose": "段 6 の採点(封 §7)。閾値は封じたもので、結果を見て変えていない",
           "seal": "docs/DOMAIN1_M6_SEAL_2026-10-15.md",
           "scorable": n, "seats_agree_6": agree, "hold_total": hold_total,
           "E2_誤受理": e2, "lines": lines, "overall": overall,
           "split": split, "hold_reasons": dict(hold_reasons),
           "reference_only": {"agree_4": agree4, "only_4": only4},
           "g4_unmeasured": g4_unmeasured,
           "parent_required": {
               "主張": sum(1 for r in rows if binds[r["id"]].get("parent_required")),
               "正しく結べた": sum(1 for r in rows
                                   if binds[r["id"]].get("parent_required")
                                   and r["agree_6"])},
           "spec_version": L.SPEC["version"],
           "novelty": dict(novelty),
           "independent_confirmation": independent,
           "novelty_rule": "新規 10 件未満なら『別の報告文で独立に確認した』とは表現しない",
           "missing_answers": missing,
           "routes": dict(collections.Counter(b["route"] for b in binds.values()
                                              if b["route"])),
           "states": dict(collections.Counter(b["state"] for b in binds.values())),
           "rows": rows}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
