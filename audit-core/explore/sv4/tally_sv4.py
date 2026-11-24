# -*- coding: utf-8 -*-
"""便 SV4 の照合と集計(封 explore/sv4/SEAL.md §2)。

使い方: python3 -I tally_sv4.py <explore の folder> <SV1 の conv の根> <SV2 の根> <SV3 の根> <SV4 の根> <record.json の path>
SV2 の印に、SV3 の標準の升と SV4 の種類を並び順で足し、<SV4 の根>/merged/out{n}/紛れ.json に書く。
SV2 の集計(tally_sv2.py)の「印の中」を「印の中で、かつ (種類が A でない か 標準の升でない)」に替えて走らせる。
対応の無い印・A でも B でもない印は B とみなす。記録は数だけ。
"""
import json
import os
import sys

EXPLORE = sys.argv[1]
sys.path.insert(0, os.path.join(EXPLORE, "sv0"))
sys.path.insert(0, os.path.join(EXPLORE, "sv2"))
import tally  # noqa: E402
import tally_sv2  # noqa: E402


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def marked(marks, src):
    name = os.path.basename(src["file"])
    for m in marks:
        if os.path.basename(str(m.get("file"))) != name:
            continue
        if src["行"] in (m.get("行") or []) and (not m.get("列") or src["列"] in m["列"]):
            if m.get("種類") != "A":
                return True
            std = {(c.get("行"), c.get("列")) for c in m.get("標準の升") or [] if isinstance(c, dict)}
            if (src["行"], src["列"]) not in std:
                return True
    return False


def by_number(items, key):
    out = {}
    for s in items or []:
        if isinstance(s.get("番号"), int):
            out[s["番号"]] = s.get(key)
    return out


def main():
    conv, sv2, sv3, sv4, out_path = sys.argv[2:7]
    merged = os.path.join(sv4, "merged")
    extra = {"種類 A の印": 0, "種類 B の印": 0, "種類が無いか A・B でない印(B とみなす)": 0}
    for num in tally.COMPANIES:
        marks = load(os.path.join(sv2, "out" + num, "紛れ.json")).get("印") or []
        std = by_number(load(os.path.join(sv3, "out" + num, "標準.json")).get("標準"), "標準の升")
        kind = by_number(load(os.path.join(sv4, "out" + num, "種類.json")).get("種類"), "種類")
        for i, m in enumerate(marks):
            m["標準の升"] = std.get(i) or []
            k = kind.get(i)
            if k == "A":
                extra["種類 A の印"] += 1
            elif k == "B":
                extra["種類 B の印"] += 1
            else:
                extra["種類が無いか A・B でない印(B とみなす)"] += 1
                k = "B"
            m["種類"] = k
        d = os.path.join(merged, "out" + num)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "紛れ.json"), "w", encoding="utf-8") as f:
            json.dump({"印": marks}, f, ensure_ascii=False)
    tally_sv2.marked = marked
    tmp = os.path.join(merged, "record_sv2_form.json")
    sys.argv = [sys.argv[0], "", conv, merged, tmp]
    tally_sv2.main()
    rec = load(tmp)
    rec.update(extra)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
