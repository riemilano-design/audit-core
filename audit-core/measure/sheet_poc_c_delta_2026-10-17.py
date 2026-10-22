# -*- coding: utf-8 -*-
"""**A と C の答えの差を件ごとに数える**(方式 C の結果 §2-2)。

採点とは別の記録にする。採点器(`sheet_poc_c_score_2026-10-17.py`)は
**指標**を測るもので、ここで測るのは「**同じ席が証拠を渡される前と後で
答えを変えたか**」という素の差である。

**これは「2 つの LLM が一致したことを証拠に数える」ことではない**
(CLAUDE.md 8(2) が禁じているのはそれである)。
**同じ席の前後の差**であり、観測として記録する。

    python3 measure/sheet_poc_c_delta_2026-10-17.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX = os.path.join(ROOT, "fixtures", "sheet")
OUT = os.path.join(FX, "poc_c_delta_2026-10-17.json")
SEAL = "docs/DOMAIN1_POC_C_SEAL_2026-10-17.md"
PAIRS = (("seat1", "claude-sonnet-4-5",
          "m11_answers_seat1_2026-10-16.json",
          "poc_c_answers_seat1_2026-10-17.json"),
         ("seat2", "claude-haiku-4-5",
          "m11_answers_seat2_2026-10-16.json",
          "poc_c_answers_seat2_2026-10-17.json"))
FIELDS = ("会計", "階層", "親", "科目名", "列", "値", "verdict")


def answers(name):
    with io.open(os.path.join(FX, name), encoding="utf-8") as fh:
        return {a["id"]: a for a in json.load(fh)["answers"]}


def diff_of(a, c):
    """**どの欄が違ったか**を返す(欄の名前まで出す。件数だけでは中身が見えない)。"""
    return sorted(f for f in FIELDS if a.get(f) != c.get(f))


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る: %s(測り直さない)" % OUT)
    rec = {"seal": SEAL,
           "step": "**同じ席の前後の差。採点とは別の記録**",
           "注": ("**「2 つの LLM が一致した」ことを証拠に数えているのではない**"
                 "(CLAUDE.md 8(2))。**同じ席が証拠を渡される前と後で"
                 "答えを変えたかを観測している**"),
           "席ごと": {}}
    for seat, model, ap, cp in PAIRS:
        a, c = answers(ap), answers(cp)
        assert sorted(a) == sorted(c), "id の集合が違う"
        same = sorted(i for i in a if a[i] == c[i])
        diff = sorted(i for i in a if a[i] != c[i])
        rec["席ごと"][seat] = {
            "model": model, "件数": len(a),
            "同じ答え": len(same), "違った答え": len(diff),
            "違った件": [{"id": i, "違った欄": diff_of(a[i], c[i]),
                      "A": {f: a[i].get(f) for f in diff_of(a[i], c[i])},
                      "C": {f: c[i].get(f) for f in diff_of(a[i], c[i])}}
                     for i in diff]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== A と C の答えの差(同じ席の前後)===")
    for seat, v in rec["席ごと"].items():
        print("%s(%s): 同じ %d / 違った %d" % (seat, v["model"],
                                          v["同じ答え"], v["違った答え"]))
        for d in v["違った件"]:
            print("   %s: 欄 %s / A %s / C %s"
                  % (d["id"], "・".join(d["違った欄"]),
                     json.dumps(d["A"], ensure_ascii=False),
                     json.dumps(d["C"], ensure_ascii=False)))
    print("->", OUT)


if __name__ == "__main__":
    main()
