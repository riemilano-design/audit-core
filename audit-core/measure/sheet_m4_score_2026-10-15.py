# -*- coding: utf-8 -*-
"""段 4 の採点(封 docs/DOMAIN1_M4_SEAL_2026-10-15.md §5)。**ラベルを見る前に書く。**

  G-1 接続の正確さ  確定ラベルの 4 欄(会計・階層・科目名・列)と engine の接続先が全部一致 / 採点対象
  G-2 誤接続        GROUNDED にしたが確定ラベルと違う根拠(別会計・別項目・別範囲・値の取り違え)
  G-3 根拠なしの接続 ラベルが「根拠なし」なのに GROUNDED
  G-4 保留の適切さ   ラベルが「根拠なし」または「判定不能」の主張を GROUNDED 以外にできた割合
  G-5 母数          採点対象の主張の数

**率と件数を並べて書く。**2 席が食い違った行は**判定不能として分母に残す**(封 §4-1)。
engine の接続先とラベルの欄の対応は**この script で固定**する:
  会計 = engine の scope / 階層 = level / 科目名 = name(会計・合計の層では空欄)/ 列 = column
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
BINDS = os.path.join(FX, "m4_binds_2026-10-15.json")
SEAT1 = os.path.join(FX, "m4_answers_seat1_2026-10-15.json")
SEAT2 = os.path.join(FX, "m4_answers_seat2_2026-10-15.json")
OUT = os.path.join(FX, "m4_score_2026-10-15.json")

_spec = importlib.util.spec_from_file_location(
    "m2", os.path.join(HERE, "sheet_m2_structure_2026-10-15.py"))
M2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M2)
norm = M2.norm
FIELDS = ("会計", "階層", "科目名", "列")
VERDICTS = ("根拠なし", "判定不能")


def answer_key(a):
    """1 席の 1 件を比べられる形にする。"""
    if a.get("verdict"):
        return ("verdict", norm(a["verdict"]))
    return ("label", tuple(norm(a.get(f)) or "" for f in FIELDS))


def engine_key(b):
    """engine の接続先を同じ形にする。GROUNDED 以外は接続していない。"""
    if b["state"] != "GROUNDED":
        return None
    e = b["evidence"] or {}
    level = norm(e.get("level")) or ""
    name = "" if level in (norm("会計"), norm("合計")) else (norm(e.get("name")) or "")
    return ("label", (norm(e.get("scope")) or "", level, name, norm(e.get("column")) or ""))


def confirmed(a1, a2):
    """2 席が一致した行だけを確定ラベルにする。食い違いは判定不能。"""
    k1, k2 = answer_key(a1), answer_key(a2)
    if k1 == k2:
        return k1, True
    return ("verdict", norm("判定不能")), False


def main():
    binds_rec = json.load(io.open(BINDS, encoding="utf-8"))
    claims = {c["id"]: c for c in binds_rec["claims"]}
    binds = {b["claim_id"]: b for b in binds_rec["binds"]}
    s1 = {a["id"]: a for a in json.load(io.open(SEAT1, encoding="utf-8"))["answers"]}
    s2 = {a["id"]: a for a in json.load(io.open(SEAT2, encoding="utf-8"))["answers"]}

    scorable = [cid for cid, c in claims.items() if c["scorable"]]
    missing = [cid for cid in scorable if cid not in s1 or cid not in s2]
    rows, agree = [], 0
    g1 = g2 = g3 = 0
    hold_total = hold_ok = 0
    for cid in sorted(scorable):
        a1, a2 = s1.get(cid, {}), s2.get(cid, {})
        label, same = confirmed(a1, a2), None
        (label, same) = confirmed(a1, a2)
        agree += 1 if same else 0
        b = binds[cid]
        ek = engine_key(b)
        row = {"id": cid, "value": claims[cid]["value"], "sentence": claims[cid]["sentence"],
               "seat1": answer_key(a1), "seat2": answer_key(a2),
               "label": label, "seats_agree": same,
               "engine_state": b["state"], "engine_route": b["route"],
               "engine_pointer": b["pointer"], "engine_key": ek, "verdict": None}
        if label[0] == "label":
            if ek == label:
                g1 += 1
                row["verdict"] = "正しい接続"
            elif ek is not None:
                g2 += 1
                row["verdict"] = "誤接続"
                row["wrong_fields"] = [f for f, x, y in zip(FIELDS, ek[1], label[1]) if x != y]
            else:
                row["verdict"] = "結べなかった(誤接続ではない)"
        else:
            hold_total += 1
            if ek is None:
                hold_ok += 1
                row["verdict"] = "正しく保留"
            else:
                row["verdict"] = "根拠なし/判定不能なのに接続した"
                if label[1] == norm("根拠なし"):
                    g3 += 1
                else:
                    g2 += 1
        rows.append(row)

    n = len(scorable)
    g1_rate = (float(g1) / n) if n else None
    g4_rate = (float(hold_ok) / hold_total) if hold_total else None
    lines = {
        "G-1 接続の正確さ": {"rate": g1_rate, "num": g1, "den": n, "pass": "≥ 50%",
                             "ok": (g1_rate is not None and g1_rate >= 0.50)},
        "G-2 誤接続": {"count": g2, "pass": "= 0 件", "ok": g2 == 0},
        "G-3 根拠なしの接続": {"count": g3, "pass": "= 0 件", "ok": g3 == 0},
        "G-4 保留の適切さ": {"rate": g4_rate, "num": hold_ok, "den": hold_total,
                             "pass": "≥ 80%",
                             "ok": (g4_rate is None or g4_rate >= 0.80)},
        "G-5 母数": {"count": n, "pass": "≥ 20", "ok": n >= 20},
    }
    overall = ("判定不能(母数不足)" if n < 20
               else ("合格" if all(v["ok"] for v in lines.values()) else "失敗"))

    print("採点対象 %d 件 / 2 席が一致 %d 件 / ラベルが保留(根拠なし・判定不能) %d 件"
          % (n, agree, hold_total))
    for k, v in lines.items():
        if "rate" in v:
            print("  %-16s %s (%d/%d)  合格線 %s  %s"
                  % (k, "―" if v["rate"] is None else "%.1f%%" % (v["rate"] * 100),
                     v["num"], v["den"], v["pass"], "○" if v["ok"] else "×"))
        else:
            print("  %-16s %d 件  合格線 %s  %s" % (k, v["count"], v["pass"],
                                                   "○" if v["ok"] else "×"))
    print("総合: %s" % overall)
    if missing:
        print("席の回答が無い主張:", missing)

    rec = {"purpose": "段 4 の採点(封 §5)。閾値は封じたもので、結果を見て変えていない",
           "seal": "docs/DOMAIN1_M4_SEAL_2026-10-15.md",
           "scorable": n, "seats_agree": agree, "hold_total": hold_total,
           "lines": lines, "overall": overall, "missing_answers": missing,
           "routes": dict(collections.Counter(b["route"] for b in binds.values() if b["route"])),
           "states": dict(collections.Counter(b["state"] for b in binds.values())),
           "rows": rows}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
