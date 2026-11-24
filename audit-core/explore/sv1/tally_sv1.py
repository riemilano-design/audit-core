# -*- coding: utf-8 -*-
"""便 SV1 の照合と集計(封 explore/sv1/SEAL.md §2)。

使い方: python3 -I tally_sv1.py <sv0 の tally.py の folder> <SV0 の根> <SV1 の根> <record.json の path>
SV1 の根の下に map{9,10,11}.json・store{n}/貯め.csv・out{n}/答え.json が在る。
席の答えの番号を升に戻して SV0 の形に直し(<SV1 の根>/conv/)、SV0 の照合をそのまま当てる。
記録は数だけ。
"""
import json
import os
import shutil
import sys

sys.path.insert(0, sys.argv[1])
import tally  # noqa: E402


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    sv0, sv1, out_path = sys.argv[2], sys.argv[3], sys.argv[4]
    conv = os.path.join(sv1, "conv")
    extra = {"読めない番号": 0, "貯めた行の数": 0, "SV0 と同じ値を答えた行": 0, "正解が在るのに無いと答えた": 0}
    for num in tally.COMPANIES:
        mp = load(os.path.join(sv1, "map%s.json" % num))
        extra["貯めた行の数"] += len(mp)
        ans = load(os.path.join(sv1, "out" + num, "答え.json"))
        rows = []
        for r in ans["行"]:
            srcs = []
            for s in r.get("出どころ") or []:
                cell = mp.get(str(s.get("番号")))
                if cell is None:
                    extra["読めない番号"] += 1
                    srcs.append({"file": "(読めない番号)", "行": 0, "列": 0})
                    continue
                srcs.append(dict(cell, 倍率=s.get("倍率", 1), 符号=s.get("符号", 1)))
            rows.append({"項目": r.get("項目"), "値": r.get("値"), "出どころ": srcs})
        od = os.path.join(conv, "out" + num)
        os.makedirs(od, exist_ok=True)
        with open(os.path.join(od, "答え.json"), "w", encoding="utf-8") as f:
            json.dump({"行": rows}, f, ensure_ascii=False)
        shutil.copy(os.path.join(sv0, "out" + num, "札.json"), os.path.join(od, "札.json"))
        link = os.path.join(conv, "co" + num)
        if not os.path.exists(link):
            os.symlink(os.path.join(sv0, "co" + num), link)
        co = tally.Company(conv, num)
        old = {r["項目"]: r.get("値") for r in load(os.path.join(sv0, "out" + num, "答え.json"))["行"]}
        for item in tally.ITEMS:
            v = (co.answers.get(item) or {}).get("値")
            if v == old.get(item):
                extra["SV0 と同じ値を答えた行"] += 1
            if v is None and co.gold[item] is not None:
                extra["正解が在るのに無いと答えた"] += 1
    tmp = os.path.join(conv, "record_sv0_form.json")
    sys.argv = [sys.argv[0], conv, tmp]
    tally.main()
    rec = load(tmp)
    rec.update(extra)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
