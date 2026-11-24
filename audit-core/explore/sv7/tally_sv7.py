# -*- coding: utf-8 -*-
"""便 SV7 の照合と集計(封 explore/sv7/SEAL.md §2)。SV1・SV4・SV6 の script をそのまま使い、会社だけ 15・16・17 に替える。

使い方: python3 -I tally_sv7.py <explore の folder> <SV7 の根> <record.json の path>
SV7 の根の下:
  r0/co{n}(素材への symlink)・r0/out{n}/札.json・r0/out{n}/答え.json(空の {"行": []}。SV1 の集計が読むだけ)
  r1/map{n}.json・r1/store{n}/貯め.csv(build_sv5.py の出力)・r1/out{n}/答え.json(貯めた行だけの席の答え)
  r2/out{n}/紛れ.json・r3/out{n}/標準.json・r4/out{n}/種類.json(保存の 1 席の出力)
  ask/out{n}/聞く.json(項目の席の出力)
記録は数だけ。
"""
import json
import os
import sys

EXPLORE, ROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
NUMS = ["15", "16", "17"]
sys.argv = [sys.argv[0], os.path.join(EXPLORE, "sv0")]
for d in ("sv0", "sv1", "sv2", "sv4"):
    sys.path.insert(0, os.path.join(EXPLORE, d))
import tally  # noqa: E402
tally.COMPANIES = NUMS
import tally_sv1  # noqa: E402
sys.argv = [sys.argv[0], EXPLORE]
import tally_sv2  # noqa: E402
import tally_sv4  # noqa: E402


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def run(main, argv, path):
    sys.argv = argv
    main()
    return load(path)


def ask_set(num):
    out = set()
    for r in load(os.path.join(ROOT, "ask", "out" + num, "聞く.json")).get("項目") or []:
        if r.get("聞く") is True:
            if r.get("項目") == "月次の売上高_当期":
                out.update(tally.MONTHLY)
            else:
                out.add(r.get("項目"))
    return out


def main():
    r0, r1, r2, r3, r4 = (os.path.join(ROOT, x) for x in ("r0", "r1", "r2", "r3", "r4"))
    work = os.path.join(ROOT, "work_tally")
    os.makedirs(work, exist_ok=True)
    store = run(tally_sv1.main, ["", "", r0, r1, os.path.join(work, "store.json")], os.path.join(work, "store.json"))
    conv = os.path.join(r1, "conv")
    s8 = run(tally_sv4.main, ["", "", conv, r2, r3, r4, os.path.join(work, "s8.json")], os.path.join(work, "s8.json"))
    # tally_sv4.main は tally_sv2.marked を SV4 の形に替えている
    g = {"聞く項目": 0, "正しい行": 0, "違う行": 0, "無いと答えた": 0, "正解が在るのに無いと答えた": 0,
         "決めの行で値の在る行": 0, "決めの行を S1〜S9 で止めた": 0,
         "正しい行(決めの行を除く)": 0, "そのうち S1〜S8 で止めた": 0, "そのうち S9 で止めた": 0,
         "違う行(決めの行を除く)": 0, "そのうち S1〜S9 を全部通った(資料に残る誤り)": 0,
         "罠": 0, "罠を S1〜S8 で止めた": 0, "罠を S9 で止めた": 0,
         "文の中の項目": 0, "文の中の項目を正しく出した": 0}
    for num in NUMS:
        co = tally.Company(conv, num)
        marks = load(os.path.join(r4, "merged", "out" + num, "紛れ.json"))["印"]
        ask = ask_set(num)
        g["聞く項目"] += len({("月次" if a in tally.MONTHLY else a) for a in ask})
        decide = {x["項目"] for x in co.trap.get("決め", [])}
        for item in tally.ITEMS:
            a = co.answers.get(item) or {}
            v, src = a.get("値"), a.get("出どころ") or []
            gold = co.gold[item]
            if v is None:
                g["無いと答えた"] += 1
                g["正解が在るのに無いと答えた"] += gold is not None
                continue
            g["正しい行" if v == gold else "違う行"] += 1
            w8 = tally_sv2.judge(co, marks, item, v, src)
            w9 = w8 if w8 is not None else ("S9" if item in ask else None)
            if item in decide:
                g["決めの行で値の在る行"] += 1
                g["決めの行を S1〜S9 で止めた"] += w9 is not None
            elif v == gold:
                g["正しい行(決めの行を除く)"] += 1
                if w8 is not None:
                    g["そのうち S1〜S8 で止めた"] += 1
                elif w9 == "S9":
                    g["そのうち S9 で止めた"] += 1
            else:
                g["違う行(決めの行を除く)"] += 1
                g["そのうち S1〜S9 を全部通った(資料に残る誤り)"] += w9 is None
        for t in co.trap.get("罠", []):
            g["罠"] += 1
            s = [{"file": t["file"], "行": t["行"], "列": t["列"], "倍率": 1, "符号": 1}]
            if tally_sv2.judge(co, marks, t["項目"], t["罠の値"], s) is not None:
                g["罠を S1〜S8 で止めた"] += 1
            elif t["項目"] in ask:
                g["罠を S9 で止めた"] += 1
        for it in load(os.path.join(co.dir, "正解", "文の中.json")):
            g["文の中の項目"] += 1
            v = (co.answers.get(it) or {}).get("値")
            g["文の中の項目を正しく出した"] += v is not None and v == co.gold.get(it)
    rec = {"流れ": g, "貯めた行だけの席(SV0 の集計の形)": store, "S1〜S8 の照合(SV4 の形)": s8}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(g, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
