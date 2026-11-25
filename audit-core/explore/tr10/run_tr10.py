# -*- coding: utf-8 -*-
"""便 TR10: 台帳の値を材料にして書く席に資料と札を書かせ、台帳の値で点検する(封 §1〜§3)。AI を使わない。

使い方:
  python3 -E run_tr10.py mat   <audit-core> <TR2 の根> <TR10 の根>   台帳で期 2 を読み、書く席の材料と台帳の値を書く
  python3 -E run_tr10.py check <audit-core> <TR2 の根> <TR10 の根>   資料と札を点検し、誤りを入れ、点検レポートを書く
書く席の答え(doc/{n}.md・tag/{n}.json)は信頼しない data として字と JSON で読むだけ。
"""
import json
import os
import sys

MODE, AC, TR2, ROOT = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AC, "explore", "tr2"))
sys.path.insert(0, HERE)
import ledger_tr2 as L  # noqa: E402
import check_tr10 as K  # noqa: E402

NUMS = [51, 52, 53, 54, 55, 56]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(obj, *parts):
    p = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def mat():
    for n in NUMS:
        conf = load(os.path.join(TR2, "confirm", "%d.applied.json" % n))
        led = L.make_ledger(conf, L.load_book(os.path.join(TR2, "co%d" % n, "期1", "書き出し.xlsx")))
        r = L.read(led, L.load_book(os.path.join(TR2, "co%d" % n, "期2", "書き出し.xlsx")))
        assert r[0] == "読めた", n
        vals, srcs = r[1], r[2]
        dump({"値": vals, "出どころ": srcs}, "ledger", "%d.json" % n)
        items = [{"項目": k.split("@")[0], "期": k.split("@")[1], "値": v, "単位": "円"} for k, v in sorted(vals.items())]
        dump({"会社": "第 %d 社" % n, "範囲": "単体", "当期": "(作り物の会社。期の日付は書かない)", "項目": items}, "mat", "%d.json" % n)
        print(n, len(items))


def check():
    for n in NUMS:
        lg = load(os.path.join(ROOT, "ledger", "%d.json" % n))
        ledger, srcs = lg["値"], lg["出どころ"]
        with open(os.path.join(ROOT, "doc", "%d.md" % n), encoding="utf-8") as f:
            md = f.read()
        tags = load(os.path.join(ROOT, "tag", "%d.json" % n)).get("札") or []
        rows = K.check_doc(md, tags, ledger, srcs)
        mat_ = {tuple(k.split("@")): v for k, v in ledger.items()}
        over = sum(K.J.is_correct(r["字"], r["値"], K.T.unit_at(md, r["行"], r["始め"]), mat_)
                   for r in rows if r["区分"] == "要修正・精査" and "字" in r)
        res = {"区分": {k: sum(r["区分"] == k for r in rows) for k in ("確認済み", "要修正・精査", "点検していない")},
               "札": len(tags), "札の付かない数": sum(r["札"] is None for r in rows), "拾った数": sum("行" in r and r.get("始め") is not None for r in rows if r["札"] is None or "字" in r),
               "資料に見つからない札": sum(r["訳"] == "札の数が資料に見つからない" for r in rows), "言い過ぎ": over,
               "確認済みで元の升を欠く": sum(1 for r in rows if r["区分"] == "確認済み" and not r.get("出どころ")),
               "止めた行": [{"訳": r["訳"], "抜粋": r.get("抜粋")} for r in rows if r["区分"] == "要修正・精査"],
               "点検していない行": [{"訳": r["訳"], "抜粋": r.get("抜粋")} for r in rows if r["区分"] == "点検していない"],
               "誤り": K.mutate_all(md, tags, rows, ledger, srcs)}
        dump(res, "out", "%d.json" % n)
        h = K.report(n, rows, "第 %d 社の資料" % n)
        p = os.path.join(ROOT, "report", "%d.html" % n)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(h)
        m = res["誤り"]
        print(n, res["区分"], "見つからない", res["資料に見つからない札"], "言い過ぎ", over, "| " + " ".join(
            "%s %d/%d" % (k, sum(x["止めた"] for x in v), len(v)) for k, v in m.items()))


if __name__ == "__main__":
    {"mat": mat, "check": check}[MODE]()
