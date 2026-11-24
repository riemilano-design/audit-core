# -*- coding: utf-8 -*-
"""便 TR1 の集計(封 §4)。記録は数だけ。

使い方: python3 -I tally_tr1.py <TR1 の根> <record.json の path>
check_A/・check_B/・check_mut/・check_tr0docs/・mut/・mat/・corrupt/・A/・report_A/ を読む。
「補足」の欄は、結果を見てから足した数(封 §4 に無い)。
"""
import json
import os
import re
import sys

ROOT, OUT = sys.argv[1], sys.argv[2]
NUMS = [str(i) for i in range(31, 42)]
SCALE = {"円": 1, "千円": 1000, "百万円": 1000000, "億円": 100000000}
CTX = {"当期": "CurrentYearDuration", "前期": "Prior1YearDuration", "当期末": "CurrentYearInstant", "前期末": "Prior1YearInstant"}
STOCK = ("現金及び預金", "流動資産合計", "資産合計", "短期借入金", "長期借入金", "負債合計", "純資産合計", "期末の従業員数")
CHECKED = ("確認済み", "要確認", "人の判断が必要")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def periods(item):
    return ("当期末", "前期末") if item in STOCK else ("当期", "前期")


def refs_corrupt(r, cor):
    """封 §4: 誤りを入れた項目と期を参照するか。増減額・増減率は当期と前期の両方を参照する。"""
    if r.get("項目") is None:
        return False
    if r["種類"] == "single_value" or r["単位"] in ("人", "名"):
        return (r["項目"], r["期"]) in cor
    return any((r["項目"], p) in cor for p in periods(r["項目"]))


def decimals_of(s):
    m = re.search(r"\.(\d+)", s)
    return len(m.group(1)) if m else 0


def same_as_material(r, mat):
    """封 §4 の言い過ぎ: 資料の数が材料の値(と、そこからの増減額・増減率)と資料の桁で同じ。"""
    item = r.get("項目")
    if item is None:
        return False
    cur, pri = periods(item)
    v = {p: mat.get((item, p)) for p in (cur, pri, r.get("期"))}
    u = r["単位"]
    if u in ("人", "名"):
        return v.get(r["期"]) is not None and abs(r["値"]) == v[r["期"]]
    if r["種類"] == "single_value" and u in SCALE:
        return v.get(r["期"]) is not None and round(v[r["期"]] / SCALE[u]) == round(r["値"])
    if v[cur] is None or v[pri] is None:
        return False
    if r["種類"] == "difference" and u in SCALE:
        d = round((v[cur] - v[pri]) / SCALE[u])
        return d == round(abs(r["値"]) * (r.get("符号") or 1)) or (r.get("符号") is None and abs(d) == round(abs(r["値"])))
    if r["種類"] == "ratio_change" and v[pri]:
        k = decimals_of(r["字"])
        p = round((v[cur] - v[pri]) / abs(v[pri]) * 100, k)
        return p == round(abs(r["値"]) * (r.get("符号") or 1), k) or (r.get("符号") is None and abs(p) == round(abs(r["値"]), k))
    return False


def main():
    g = {"資料": len(NUMS),
         "新しい資料": {"拾った数": 0, "基準 A": {k: 0 for k in CHECKED + ("点検していない",)},
                      "基準 B": {k: 0 for k in CHECKED + ("点検していない",)},
                      "基準 A で照合した数": 0, "基準 A で照合した増減率": 0, "基準 A で照合した増減額": 0},
         "取り出しの誤り": {"入れた項目": 0, "誤りから来た数(基準 A で照合)": 0, "そのうち基準 A で要確認": 0,
                       "誤りから来た数(基準 B で照合)": 0, "そのうち基準 B で要確認": 0},
         "基準 A の言い過ぎ": 0,
         "TR0 の資料を基準 A で": {"拾った数": 0, "確認済み": 0, "要確認": 0, "人の判断が必要": 0, "点検していない": 0},
         "基準 A の確認済みの行で一次ソースを欠く": 0,
         "入れた誤り(4 種)": {"入れた": 0, "基準 A で要確認": 0, "種類": {}},
         "補足": {"基準 A の要確認のうち engine の保留": 0, "TR0 の資料の基準 A の要確認のうち engine の保留": 0,
                 "基準 A の要確認のうち誤りの項目を参照せず保留でもない": 0,
                 "点検レポート(基準 A)の確認済みの行で「XBRL の要素」の字を欠く": 0}}
    for n in NUMS:
        cor = {(c["項目"], c["期"]) for c in load(os.path.join(ROOT, "corrupt", n + ".json"))}
        mat = {(m["項目"], m["期"]): m["値"] for m in load(os.path.join(ROOT, "mat", n + ".json"))["項目"]}
        A = load(os.path.join(ROOT, "A", n + ".json"))
        ra = load(os.path.join(ROOT, "check_A", n + ".json"))
        rb = load(os.path.join(ROOT, "check_B", n + ".json"))
        assert len(ra) == len(rb)
        g["取り出しの誤り"]["入れた項目"] += len(cor)
        g["新しい資料"]["拾った数"] += len(ra)
        for a, b in zip(ra, rb):
            assert (a["行"], a["始め"]) == (b["行"], b["始め"])
            g["新しい資料"]["基準 A"][a["区分"]] += 1
            g["新しい資料"]["基準 B"][b["区分"]] += 1
            if a["区分"] in CHECKED:
                g["新しい資料"]["基準 A で照合した数"] += 1
                g["新しい資料"]["基準 A で照合した増減率"] += a["種類"] == "ratio_change"
                g["新しい資料"]["基準 A で照合した増減額"] += a["種類"] == "difference"
            hit = refs_corrupt(a, cor)
            if hit and a["区分"] in CHECKED:
                g["取り出しの誤り"]["誤りから来た数(基準 A で照合)"] += 1
                g["取り出しの誤り"]["そのうち基準 A で要確認"] += a["区分"] == "要確認"
            if hit and b["区分"] in CHECKED:
                g["取り出しの誤り"]["誤りから来た数(基準 B で照合)"] += 1
                g["取り出しの誤り"]["そのうち基準 B で要確認"] += b["区分"] == "要確認"
            if a["区分"] == "要確認":
                held = bool(a["info"].get("held"))
                g["補足"]["基準 A の要確認のうち engine の保留"] += held
                if not hit:
                    g["基準 A の言い過ぎ"] += same_as_material(a, mat)
                    g["補足"]["基準 A の要確認のうち誤りの項目を参照せず保留でもない"] += not held
            if a["区分"] == "確認済み":
                keys = a["info"].get("keys") or []
                if not keys or any(not (A["map"].get(k) or {}).get("要素") or not (A["map"].get(k) or {}).get("枠") for k in keys):
                    g["基準 A の確認済みの行で一次ソースを欠く"] += 1
        with open(os.path.join(ROOT, "report_A", n + ".html"), encoding="utf-8") as f:
            h = f.read()
        sec = h.split("<h2>確認済み</h2>", 1)[1].split("<h2>点検していない数</h2>", 1)[0]
        for row in re.findall(r"<tr><td>(.*?)</tr>", sec):
            g["補足"]["点検レポート(基準 A)の確認済みの行で「XBRL の要素」の字を欠く"] += "XBRL の要素「" not in row
        for r in load(os.path.join(ROOT, "check_tr0docs", n + ".json")):
            g["TR0 の資料を基準 A で"]["拾った数"] += 1
            g["TR0 の資料を基準 A で"][r["区分"]] += 1
            if r["区分"] == "要確認":
                g["補足"]["TR0 の資料の基準 A の要確認のうち engine の保留"] += bool(r["info"].get("held"))
        muts = load(os.path.join(ROOT, "mut", n + ".json"))
        at = {(r["行"], r["始め"]): r for r in load(os.path.join(ROOT, "check_mut", n + ".json"))}
        for m in muts:
            shift = sum(len(o["入れた字"]) - len(o["元の字"]) for o in muts if o["行"] == m["行"] and o["始め"] < m["始め"])
            r = at.get((m["行"], m["始め"] + shift))
            g["入れた誤り(4 種)"]["入れた"] += 1
            g["入れた誤り(4 種)"]["種類"][m["種類"]] = g["入れた誤り(4 種)"]["種類"].get(m["種類"], 0) + 1
            g["入れた誤り(4 種)"]["基準 A で要確認"] += r is not None and r["区分"] == "要確認"
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(g, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
