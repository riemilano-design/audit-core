# -*- coding: utf-8 -*-
"""便 TR2 の集計(封 §4・§6)。記録は数だけ。

使い方: python3 -I tally_tr2.py <TR2 の根> <record.json の path>
out/{n}.json・inject/{n}.json・co{n}/正解/変異.json・report_v2.json を読む。
変異を入れた所が依頼に出ているか: 依頼の「変わった所」のどれかで、前か今の字が変異の字と同じで、
シートが変異のシート(シート名の変更なら前の名か新しい名)と同じもの。
"""
import json
import os
import sys

ROOT, OUT = sys.argv[1], sys.argv[2]
NUMS = [51, 52, 53, 54, 55, 56]
KINDS = ["列の挿入", "行の並べ替え", "シート名の変更", "行の見出しの微修正", "列の見出しの微修正", "科目の追加", "単位の変更"]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    g = {"社": len(NUMS), "項目と期": 15 * len(NUMS),
         "提案の台帳で期 1 を読んで正しい": 0, "確定の台帳で期 1・期 2 を読んで正しい": 0, "確定の台帳で読めずに止めた(期 1・期 2)": 0,
         "入れた誤り": 0, "確定の席が直した": 0, "期 2 で止めた社": 0,
         "変異": 0, "変異を止めた": 0, "変異を止めた(種類ごと)": {k: 0 for k in KINDS},
         "止めた依頼に変異の所が出ている": 0,
         "素朴な読み方": {"黙って違う値を読んだ": 0, "読めなかった": 0, "全部正しく読めた": 0, "黙った誤り(種類ごと)": {k: 0 for k in KINDS}},
         "補足": {"確定の席が直した項目の数": 0, "確定の席が入れた誤りでない所を直した": 0}}
    for n in NUMS:
        o = load(os.path.join(ROOT, "out", "%d.json" % n))
        inj = load(os.path.join(ROOT, "inject", "%d.json" % n))
        where = load(os.path.join(ROOT, "co%d" % n, "正解", "変異.json"))
        rep = load(os.path.join(ROOT, "confirm", "%d.json" % n))
        g["提案の台帳で期 1 を読んで正しい"] += 15 - len(o["提案"]["違う"]) if not o["提案"]["読めない"] else 15 - len(set(o["提案"]["違う"]) | set(o["提案"]["読めない"]))
        for per in ("期1", "期2"):
            c = o["確定"][per]
            g["確定の台帳で期 1・期 2 を読んで正しい"] += 15 - len(c["違う"])
            g["確定の台帳で読めずに止めた(期 1・期 2)"] += c["状態"] == "止める"
        g["期 2 で止めた社"] += o["確定"]["期2"]["状態"] == "止める"
        g["入れた誤り"] += 1
        g["確定の席が直した"] += o["確定"]["期1"]["状態"] == "読めた" and inj["項目"] not in o["確定"]["期1"]["違う"]
        fixed = [r for r in rep.get("項目") or [] if isinstance(r, dict) and r.get("選び") == "直す"]
        g["補足"]["確定の席が直した項目の数"] += len(fixed)
        g["補足"]["確定の席が入れた誤りでない所を直した"] += sum(1 for r in fixed if "%s@%s" % (r.get("項目"), r.get("期")) != inj["項目"])
        for k in KINDS:
            v = o["変異"][k]
            g["変異"] += 1
            if v["状態"] == "止める":
                g["変異を止めた"] += 1
                g["変異を止めた(種類ごと)"][k] += 1
                w = where[k]
                sheets = {w["シート"], w["字"]} if k == "シート名の変更" else {w["シート"]}
                g["止めた依頼に変異の所が出ている"] += any(d.get("シート") in sheets and w["字"] in (d.get("前"), d.get("今"))
                                                for d in v["変わった所"])
            s = v["素朴"]
            if s["読めない"]:
                g["素朴な読み方"]["読めなかった"] += 1
            elif s["違う"]:
                g["素朴な読み方"]["黙って違う値を読んだ"] += 1
                g["素朴な読み方"]["黙った誤り(種類ごと)"][k] += 1
            else:
                g["素朴な読み方"]["全部正しく読めた"] += 1
    p = os.path.join(ROOT, "report_v2.json")
    g["TR1 の点検レポートの直し"] = load(p) if os.path.exists(p) else None
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(g, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
