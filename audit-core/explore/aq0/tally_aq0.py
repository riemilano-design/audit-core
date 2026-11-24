# -*- coding: utf-8 -*-
"""便 AQ0 の集計(封 explore/aq0/SEAL.md §4)。記録は数だけ。

使い方: python3 -I tally_aq0.py <audit-core の folder> <RD2 の根> <AQ0 の根> <record.json の path>
画面の対応(<AQ0 の根>/{O,F}/key{n}.json)と席の返事(<AQ0 の根>/reply/{O,F}/{n}/返事.json)を、
RD2 の正解(co{n}/正解/正解.json)と、正解を作った時の連結か単体か(XBRL を読むだけで出し直す)で数える。
"""
import hashlib
import json
import os
import sys

AC, RD2, AQ0, OUT = sys.argv[1:5]
sys.path.insert(0, AC)
from adapters.xbrl.instance import load_instance  # noqa: E402  (読むだけ)

CACHE = os.path.expanduser("~/.cache/audit-core")
ROWS = {str(31 + i): str(7 + i) for i in range(11)}  # 社の番号 → fixture の行の `#`


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def consolidated():
    """正解を作った時と同じ決め方(build_rd0.py)で、社ごとの連結か単体か。"""
    d = load(os.path.join(AC, "fixtures/xbrl/tanshin/fetched_2026-11-09.json"))
    rows = {str(r["#"]): r for r in d["行"]}
    sha2path = {}
    for sub in ("edinet", "edinet-fresh-2026-10-21", "edinet-prior-2026-11-02"):
        for f in os.listdir(os.path.join(CACHE, sub)):
            p = os.path.join(CACHE, sub, f)
            sha2path[hashlib.sha256(open(p, "rb").read()).hexdigest()] = p
    out = {}
    for n, key in ROWS.items():
        facts = load_instance(open(sha2path[rows[key]["有報の ZIP の sha256"]], "rb").read())["facts"]
        out[n] = any(f["context"] == "CurrentYearDuration" and f["name"].split(":")[-1] == "NetSales" for f in facts) \
            or any(f["context"] == "CurrentYearInstant" and f["name"].split(":")[-1] == "Assets" for f in facts)
    return out


def final_value(q, a):
    s = a.get("選び")
    if s == "そのまま":
        return q["埋めた値"]
    if isinstance(s, str) and s.startswith("候補"):
        try:
            return q["候補"][int(s[2:]) - 1]
        except (ValueError, IndexError):
            return "形が読めない"
    if s == "別の値":
        return a.get("値")
    return None  # わからない


def main():
    cons = consolidated()
    rd2 = load(os.path.join(AC, "explore", "rd2", "record.json"))
    g = {"RD2 で止めた 16 項目の行": rd2["そのうち S1〜S9 で止めた"] + rd2["決めの行を S1〜S9 で止めた"]
         + (rd2["正解が無いのに答えた"] - rd2["正解が無いのに答えた行のうち S1〜S9 を全部通った"]),
         "画面の B に出した行(版 O)": 0, "版 F の行": 0, "席の数": 0, "返事が無い・形が読めない席": 0,
         "A1 の問い": 0, "A1 で正解の範囲を選んだ": 0, "A1 でわからない": 0, "機械の案が正解の範囲": 0,
         "A2 の問い": 0, "A2 で親会社株主に帰属を選んだ": 0, "A2 でわからない": 0, "A2 が出た単体の社": 0,
         "問いの数(A と B、版 O と F)": 0, "足りないと書いた問い": 0, "版": {}}
    for ver in ("O", "F"):
        v = {"正解の在る行": 0, "最後の値が正解": 0, "正解でない値": 0, "わからない": 0, "形が読めない選び": 0,
             "埋めた値から正解でない値に替えた": 0, "入れ替えた行": 0, "入れ替えた行で最後の値が正解": 0}
        d = os.path.join(AQ0, ver)
        for name in sorted(os.listdir(d)):
            if not name.startswith("key"):
                continue
            key = load(os.path.join(d, name))
            n = key["会社"]
            gold = load(os.path.join(RD2, "co" + n, "正解", "正解.json"))["期1"]
            g["席の数"] += 1
            p = os.path.join(AQ0, "reply", ver, n, "返事.json")
            try:
                reply = {a.get("問い"): a for a in load(p).get("答え") or []}
            except (OSError, ValueError, AttributeError):
                g["返事が無い・形が読めない席"] += 1
                reply = {}
            for q in key["問い"]:
                a = reply.get(q["問い"]) or {}
                g["問いの数(A と B、版 O と F)"] += 1
                g["足りないと書いた問い"] += a.get("足りた") is False
                if q["種類"] == "範囲":
                    if ver == "O":
                        g["A1 の問い"] += 1
                        want = "連結" if cons[n] else "単体"
                        g["A1 で正解の範囲を選んだ"] += a.get("選び") == want
                        g["A1 でわからない"] += a.get("選び") == "わからない"
                        g["機械の案が正解の範囲"] += q["案"] == want
                    continue
                if q["種類"] == "当期純利益":
                    if ver == "O":
                        g["A2 の問い"] += 1
                        g["A2 で親会社株主に帰属を選んだ"] += a.get("選び") == "親会社株主に帰属"
                        g["A2 でわからない"] += a.get("選び") == "わからない"
                        g["A2 が出た単体の社"] += not cons[n]
                    continue
                if ver == "O":
                    g["画面の B に出した行(版 O)"] += 1
                else:
                    g["版 F の行"] += q.get("入れ替えた") is True
                want = gold.get(q["項目"])
                if want is None:
                    continue
                v["正解の在る行"] += 1
                fv = final_value(q, a)
                if fv == "形が読めない":
                    v["形が読めない選び"] += 1
                elif fv is None:
                    v["わからない"] += 1
                elif fv == want:
                    v["最後の値が正解"] += 1
                else:
                    v["正解でない値"] += 1
                    v["埋めた値から正解でない値に替えた"] += q["埋めた値"] == want
                if q.get("入れ替えた") is True:
                    v["入れ替えた行"] += 1
                    v["入れ替えた行で最後の値が正解"] += fv == want
        g["版"][ver] = v
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(g, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
