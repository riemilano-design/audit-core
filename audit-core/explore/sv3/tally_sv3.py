# -*- coding: utf-8 -*-
"""便 SV3 の照合と集計(封 explore/sv3/SEAL.md §2)。

使い方: python3 -I tally_sv3.py <explore の folder> <SV1 の conv の根> <SV2 の根> <SV3 の根> <record.json の path>
SV2 の印(<SV2 の根>/out{n}/紛れ.json)に、SV3 の標準の升(<SV3 の根>/out{n}/標準.json)を並び順で足し、
<SV3 の根>/merged/out{n}/紛れ.json に書く。SV2 の集計(tally_sv2.py)の「印の中」を
「印の中で、かつその印の標準の升でない」に替えて、そのまま走らせる。記録は数だけ。
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
            std = {(c.get("行"), c.get("列")) for c in m.get("標準の升") or [] if isinstance(c, dict)}
            if (src["行"], src["列"]) not in std:
                return True
    return False


def main():
    conv, sv2, sv3, out_path = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
    merged = os.path.join(sv3, "merged")
    extra = {"標準の升を挙げた印": 0, "空にした印": 0, "標準の升の数": 0, "対応の無い印": 0}
    for num in tally.COMPANIES:
        marks = load(os.path.join(sv2, "out" + num, "紛れ.json")).get("印") or []
        std = {}
        for s in load(os.path.join(sv3, "out" + num, "標準.json")).get("標準") or []:
            if isinstance(s.get("番号"), int):
                std[s["番号"]] = s.get("標準の升") or []
        for i, m in enumerate(marks):
            if i not in std:
                extra["対応の無い印"] += 1
            cells = std.get(i, [])
            m["標準の升"] = cells
            extra["標準の升の数"] += len(cells)
            extra["標準の升を挙げた印" if cells else "空にした印"] += 1
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
