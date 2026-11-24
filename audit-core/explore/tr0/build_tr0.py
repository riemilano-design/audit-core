# -*- coding: utf-8 -*-
"""便 TR0: 1〜6 段の出力(RD2 の答え・照合、AQ0 の人の選び)から、7 段に渡す材料と engine に渡す facts を作る(封 §1)。

使い方: python3 -I build_tr0.py <explore の folder> <RD2 の根> <AQ0 の根> <TR0 の根>
<TR0 の根>/mat/{n}.json(書く席に渡す材料)と <TR0 の根>/state/{n}.json(facts と項目の状態。点検だけが読む)を書く。
正解の値は読まない(当期の始まりと終わりの日だけを RD2 の co{n}/正解/期.json から読む)。
"""
import csv
import json
import os
import sys

EXPLORE, RD2, AQ0, OUT = sys.argv[1:5]
UNIT = {"円": 1, "千円": 1000, "百万円": 1000000}
DEC = {"円": 0, "千円": -3, "百万円": -6}
PERIOD = {"当期": "CurrentYearDuration", "前期": "Prior1YearDuration",
          "当期末": "CurrentYearInstant", "前期末": "Prior1YearInstant"}
SCOPE = ["売上高_当期", "売上高_前期", "営業利益_当期", "営業利益_前期", "経常利益_当期", "当期純利益_当期",
         "減価償却費_当期", "現金及び預金_当期末", "流動資産合計_当期末", "資産合計_当期末", "短期借入金_当期末",
         "長期借入金_当期末", "負債合計_当期末", "純資産合計_当期末", "純資産合計_前期末", "期末の従業員数_当期末"]
NUMS = [str(i) for i in range(31, 42)]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    os.makedirs(os.path.join(OUT, "mat"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "state"), exist_ok=True)
    for n in NUMS:
        per = load(os.path.join(RD2, "co" + n, "正解", "期.json"))
        with open(os.path.join(RD2, "r1", "store" + n, "貯め.csv"), encoding="utf-8") as f:
            rows = {int(r["番号"]): r for r in csv.DictReader(f)}
        ans = {r["項目"]: r for r in load(os.path.join(RD2, "r1", "out" + n, "答え.json"))["行"]}
        key = load(os.path.join(AQ0, "O", "key%s.json" % n))
        reply = {a.get("問い"): a for a in load(os.path.join(AQ0, "reply", "O", n, "返事.json")).get("答え") or []}
        scope = next((reply.get(q["問い"], {}).get("選び") for q in key["問い"] if q["種類"] == "範囲"), None)
        asked = {q["項目"]: q for q in key["問い"] if q["種類"] == "項目"}
        mat, facts, status = [], [], {}
        for item in SCOPE:
            a = ans.get(item) or {}
            v = a.get("値")
            if v is None:
                continue
            label, period = item.split("_")
            srcs = [rows[s["番号"]] for s in a.get("出どころ") or [] if s.get("番号") in rows]
            src_text = [{"表": r.get("表"), "行": r.get("行の見出し"), "列": r.get("列の見出し"), "期": r.get("期"),
                         "単位": r.get("単位"), "範囲": r.get("範囲")} for r in srcs]
            if item in asked:
                q = asked[item]
                r = reply.get(q["問い"]) or {}
                s = r.get("選び")
                if s == "そのまま":
                    st = "人が画面で決めた"
                elif isinstance(s, str) and s.startswith("候補") and s[2:].isdigit() and 1 <= int(s[2:]) <= len(q["候補"]):
                    v, st = q["候補"][int(s[2:]) - 1], "人が画面で決めた"
                elif s == "別の値" and isinstance(r.get("値"), int):
                    v, st = r["値"], "人が画面で決めた"
                else:
                    st = "未決"
            else:
                st = "照合を通った"
            unit = "人" if label == "期末の従業員数" else "円"
            mat.append({"項目": label, "期": period, "値": v, "単位": unit})
            status["%s@%s" % (label, PERIOD[period])] = {"項目": label, "期": period, "状態": st, "値": v, "単位": unit,
                                                        "出どころ": src_text if st == "照合を通った" else []}
            if unit == "円":
                su = (srcs[0].get("単位") if srcs else None) or "円"
                facts.append({"name": label, "context": PERIOD[period], "unit": "JPY",
                              "decimals": str(DEC.get(su, 0)), "value": float(v)})
        doc = {"会社": "第 %s 社" % n, "範囲": scope if scope in ("連結", "単体") else None,
               "当期": "%s〜%s" % (per["当期の始まり"], per["当期の終わり"]), "項目": mat}
        with open(os.path.join(OUT, "mat", n + ".json"), "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        with open(os.path.join(OUT, "state", n + ".json"), "w", encoding="utf-8") as f:
            json.dump({"facts": facts, "状態": status, "範囲": doc["範囲"]}, f, ensure_ascii=False, indent=1)
        print(n, "項目", len(mat), "未決", sum(s["状態"] == "未決" for s in status.values()),
              "人が決めた", sum(s["状態"] == "人が画面で決めた" for s in status.values()))


if __name__ == "__main__":
    main()
