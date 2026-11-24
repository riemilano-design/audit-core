# -*- coding: utf-8 -*-
"""便 SV5 の照合と集計(封 explore/sv5/SEAL.md §2)。SV0〜SV4 の script をそのまま使い、会社だけ 12・13・14 に替える。

使い方: python3 -I tally_sv5.py <explore の folder> <SV5 の根> <record.json の path>
SV5 の根の下:
  r0/co{n}(素材への symlink)・r0/out{n}/札.json・r0/out{n}/答え.json(元の file を見た席の答え)
  r1/map{n}.json・r1/store{n}/貯め.csv(build_store.py の出力)・r1/out{n}/答え.json(貯めた行だけの席の答え)
  r2/out{n}/紛れ.json・r3/out{n}/標準.json・r4/out{n}/種類.json
記録は数だけ。
"""
import json
import os
import sys

EXPLORE, ROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
NUMS = ["12", "13", "14"]
sys.argv = [sys.argv[0], os.path.join(EXPLORE, "sv0")]
sys.path.insert(0, os.path.join(EXPLORE, "sv0"))
sys.path.insert(0, os.path.join(EXPLORE, "sv1"))
sys.path.insert(0, os.path.join(EXPLORE, "sv2"))
sys.path.insert(0, os.path.join(EXPLORE, "sv4"))
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


def main():
    r0, r1, r2, r3, r4 = (os.path.join(ROOT, x) for x in ("r0", "r1", "r2", "r3", "r4"))
    work = os.path.join(ROOT, "work_tally")
    os.makedirs(work, exist_ok=True)
    raw = run(tally.main, ["", r0, os.path.join(work, "raw.json")], os.path.join(work, "raw.json"))
    store = run(tally_sv1.main, ["", "", r0, r1, os.path.join(work, "store.json")], os.path.join(work, "store.json"))
    conv = os.path.join(r1, "conv")
    s8 = run(tally_sv4.main, ["", "", conv, r2, r3, r4, os.path.join(work, "s8.json")], os.path.join(work, "s8.json"))
    # tally_sv4.main は tally_sv2.marked を SV4 の形に替えている
    extra = {"文の中の項目": 0, "文の中の項目を元の file の席が正しく出した": 0, "文の中の項目を貯めた行だけの席が正しく出した": 0,
             "保存の席が貯めるにした txt": 0, "数の表だが使わない file": 0, "そのうち貯めるへ": 0,
             "決めの行": 0, "決めの行を無いと答えた": 0,
             "違う行(決めの行を除く)": 0, "そのうち S1〜S8 を全部通った": 0}
    for num in NUMS:
        co = tally.Company(conv, num)
        raw_ans = {r["項目"]: r.get("値") for r in load(os.path.join(r0, "out" + num, "答え.json"))["行"]}
        text_items = load(os.path.join(co.dir, "正解", "文の中.json"))
        for it in text_items:
            extra["文の中の項目"] += 1
            if raw_ans.get(it) is not None and raw_ans.get(it) == co.gold.get(it):
                extra["文の中の項目を元の file の席が正しく出した"] += 1
            v = (co.answers.get(it) or {}).get("値")
            if v is not None and v == co.gold.get(it):
                extra["文の中の項目を貯めた行だけの席が正しく出した"] += 1
        for name, tag in co.tags.items():
            if name.lower().endswith(".txt") and tag.get("扱い") == "貯める":
                extra["保存の席が貯めるにした txt"] += 1
        unused = load(os.path.join(co.dir, "正解", "使わない.json"))
        for name in (unused.get("数の表") or []) if isinstance(unused, dict) else []:
            extra["数の表だが使わない file"] += 1
            tag = co.tags.get(os.path.basename(name))
            if tag is not None and tag.get("扱い") == "貯める":
                extra["そのうち貯めるへ"] += 1
        marks = load(os.path.join(r4, "merged", "out" + num, "紛れ.json"))["印"]
        decide = {x["項目"] for x in co.trap.get("決め", [])}
        for it in tally.ITEMS:
            a = co.answers.get(it) or {}
            v = a.get("値")
            if it in decide:
                extra["決めの行"] += 1
                if v is None:
                    extra["決めの行を無いと答えた"] += 1
                continue
            if v is None or v == co.gold[it]:
                continue
            extra["違う行(決めの行を除く)"] += 1
            if tally_sv2.judge(co, marks, it, v, a.get("出どころ") or []) is None:
                extra["そのうち S1〜S8 を全部通った"] += 1
    rec = {"元の file を見た席": raw, "貯めた行だけの席": store, "S8 を足した照合(SV4 の形)": s8, "足した数": extra}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
