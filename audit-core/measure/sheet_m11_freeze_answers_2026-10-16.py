# -*- coding: utf-8 -*-
"""席の答えを**凍結する**(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §7・§11 の 9)。

**席には `task.txt` だけを渡し、席が自分で `answers.json` に書いた。**
**やり直しはしない** ― 機械検査に落ちた答えは**その件を「判定不能」として数える。**

機械検査(**落ちても再生成しない。落ちたことを記録する**):
  * JSON の配列であること
  * id が (B) の一覧と**同じ集合**であること(欠け・余りを記録する)
  * 欄が 6 つそろっているか、`verdict` が在るか
  * 値がカンマ無しの整数か(カンマが在れば**落とさずに「判定不能」に倒す**)

    python3 measure/sheet_m11_freeze_answers_2026-10-16.py <seat1|seat2> <answers.json>
"""
import datetime
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FX = os.path.join(ROOT, "fixtures", "sheet")
LAB = os.path.join(FX, "m11_label_material_2026-10-16.json")
BINDS = os.path.join(FX, "m11_binds_2026-10-16.json")
SEAL = "docs/DOMAIN1_M11_SEAL_2026-10-16.md"
FIELDS = ("会計", "階層", "親", "科目名", "列", "値")


def check(answers, want_ids):
    """**答えの形を機械で検査する。**(通った答え, 落ちた件の記録)を返す。

    判定を 1 か所に置く ― 正常な答えでは発火しないので、
    門が**壊した答え**を食わせて 1 本ずつ当てられるようにする。
    """
    seen, out, bad = set(), [], []
    for a in answers:
        cid = a.get("id")
        if cid not in want_ids:
            bad.append({"id": cid, "理由": "一覧に無い id"})
            continue
        if cid in seen:
            bad.append({"id": cid, "理由": "同じ id が 2 回"})
            continue
        seen.add(cid)
        if a.get("verdict"):
            out.append({"id": cid, "verdict": a["verdict"]})
            continue
        miss = [f for f in FIELDS if f not in a]
        if miss:
            bad.append({"id": cid, "理由": "欄が欠けている: %s" % "・".join(miss)})
            out.append({"id": cid, "verdict": "判定不能"})
            continue
        v = a["値"]
        if isinstance(v, str):
            s = v.replace(",", "").replace("円", "").strip()
            try:
                v = int(s)
            except ValueError:
                bad.append({"id": cid, "理由": "値が整数でない: %r" % a["値"]})
                out.append({"id": cid, "verdict": "判定不能"})
                continue
            bad.append({"id": cid, "理由": "値が文字列だった(整数に直した): %r" % a["値"]})
        rec = {"id": cid}
        for f in FIELDS:
            rec[f] = v if f == "値" else a[f]
        out.append(rec)
    for cid in sorted(want_ids - seen):
        bad.append({"id": cid, "理由": "**答えが無い**"})
        out.append({"id": cid, "verdict": "判定不能"})
    return out, bad


def main():
    seat, path = sys.argv[1], sys.argv[2]
    out_p = os.path.join(FX, "m11_answers_%s_2026-10-16.json" % seat)
    if os.path.exists(out_p):
        raise SystemExit("答えが既に在る: %s(**やり直さない**)" % out_p)
    lab = json.load(io.open(LAB, encoding="utf-8"))
    meta = [s for s in lab["seats"] if s["seat"] == seat][0]
    want = {c["id"] for c in json.load(io.open(BINDS, encoding="utf-8"))["claims"]
            if not c.get("skipped")}
    raw = io.open(path, encoding="utf-8").read().strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    answers = json.loads(raw)
    if not isinstance(answers, list):
        raise SystemExit("JSON の配列でない")
    ok, bad = check(answers, want)
    rec = {"seal": SEAL, "seat": seat, "model": meta["model"],
           "order": meta["order"], "blind": True, "runs": 1,
           "regenerated": False,
           "material": "fixtures/sheet/m11_label_material_2026-10-16.json",
           "answered_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
           "機械検査に落ちた件": bad,
           "落ちた件の扱い": ("**その件を「判定不能」として数える。再生成しない**"
                      "(封 §7)"),
           "answers": sorted(ok, key=lambda a: a["id"])}
    json.dump(rec, io.open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%s: %d 件(一覧 %d 件)/ 機械検査に落ちた件 %d"
          % (seat, len(ok), len(want), len(bad)))
    for b in bad:
        print("   ", json.dumps(b, ensure_ascii=False))
    print("->", out_p)


if __name__ == "__main__":
    main()
