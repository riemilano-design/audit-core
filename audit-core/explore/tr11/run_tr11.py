# -*- coding: utf-8 -*-
"""便 TR11: 1 本の流れを 6 社で回す(封 §1〜§3)。AI を使わない。

使い方: python3 -E run_tr11.py {stop|reread|check} <audit-core> <TR2> <TR6> <TR9> <TR11>
  stop:   1〜2(今期の file を読み、止めたら画面を作る)
  reread: 3(確定し直しの席の決めを当てて読み直し、書く席の材料を書く)
  check:  5(書く席の資料と札を台帳の値で点検し、誤りを入れ、点検レポートを書く)
席の答え(reply/{n}.json・doc/{n}.md・tag/{n}.json)は信頼しない data として読むだけ。正解は読んだ値と比べるためだけに読む。
"""
import json
import os
import sys

MODE, AC, TR2, TR6, TR9, ROOT = sys.argv[1:7]
HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("tr2", "tr6", "tr7", "tr8", "tr9", "tr10"):
    sys.path.insert(0, os.path.join(AC, "explore", d))
sys.path.insert(0, HERE)
import ledger_tr2 as L  # noqa: E402
import reconf_tr6 as R  # noqa: E402
import partial_tr7 as P  # noqa: E402
import reconf8 as R8  # noqa: E402
import ledger9 as G9  # noqa: E402
import reconf9 as R9  # noqa: E402
import check_tr10 as K  # noqa: E402
import flow_tr11 as F  # noqa: E402

# 今期の file(社ごとに様式の変化 1 つ)。TR6・TR9 の素材の期 2。
CASE = {51: ("tr6", "科目の追加"), 52: ("tr6", "シート名の変更"), 53: ("tr6", "意味の変わる改名"),
        54: ("tr6", "単位の変更"), 55: ("tr6", "紛れの科目の追加"), 56: ("tr9", "同じ見出しの列(手がかりあり)")}
NUMS = sorted(CASE)


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(obj, *parts):
    p = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def case(n):
    src, kind = CASE[n]
    base = TR6 if src == "tr6" else TR9
    bk = L.load_book(os.path.join(base, "co%d" % n, kind, "期2", "書き出し.xlsx"))
    truth = load(os.path.join(base, "co%d" % n, "正解.json"))["値"][kind]["期2"]
    conf = load(os.path.join(TR2, "confirm", "%d.applied.json" % n))
    b1 = L.load_book(os.path.join(TR2, "co%d" % n, "期1", "書き出し.xlsx"))
    return conf, L.make_ledger(conf, b1), G9.make(conf, b1), bk, truth


def stop():
    for n in NUMS:
        conf, led, led9, bk, truth = case(n)
        r = G9.read(conf, led9, bk)
        ch = R9.diff9(conf, led, bk)
        early = P.read_some(conf, bk, set(truth) - R8.waiting8(conf, ch, bk))
        d2, bad = R9.apply(conf, ch, R.plan_only(ch))
        plan_read = None
        if not bad:
            r2 = G9.read(d2, G9.make(d2, bk), bk)
            if r2[0] == "読めた":
                plan_read = {a: r2[1][a] for a in sorted({a for c in ch for a in c["影響"]})}
        p = os.path.join(ROOT, "screen", str(n), "s1.html")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(F.screen11(n, "s1", ch, conf, bk, plan_read, early))
        dump({"止めた": r[0] == "止める", "変わった所": len(ch), "先に読んだ": len(early),
              "先に読んで違う": sum(1 for k, v in early.items() if v != truth[k])}, "out", "stop", "%d.json" % n)
        print(n, r[0], len(ch), len(early))


def reread():
    for n in NUMS:
        conf, led, led9, bk, truth = case(n)
        ch = R9.diff9(conf, led, bk)
        reply = load(os.path.join(ROOT, "reply", "%d.json" % n))
        ans = (reply.get("画面") or {}).get("s1") or {}
        dec = {}
        for x in ans.get("決め") or []:
            if not isinstance(x, dict) or not isinstance(x.get("番号"), int):
                continue
            c = next((c for c in ch if c["番号"] == x["番号"]), None)
            if x.get("選び") == "案のまま" and c is not None and c["案"] is not None:
                dec[x["番号"]] = c["案"]
            elif x.get("選び") == "決める" and isinstance(x.get("決め"), dict):
                dec[x["番号"]] = x["決め"]
        d2, bad = R9.apply(conf, ch, dec)
        res = {"決め": {str(k): v for k, v in dec.items()}, "決めた所": sum(1 for x in ans.get("決め") or [] if isinstance(x, dict) and x.get("選び") == "決める"),
               "当てられなかった": ["%s: %s" % b for b in bad], "気づき": ans.get("気づき", "")}
        if not bad:
            r = G9.read(d2, G9.make(d2, bk), bk)
            res["読み直し"] = r[0]
            if r[0] == "読めた":
                vals = r[1]
                srcs = L.read(L.make_ledger(d2, bk), bk)
                srcs = srcs[2] if srcs[0] == "読めた" else {}
                # 列の何番目を使う社は TR2 の read の出どころが最初の列になるので、ledger9 の値で升の値を書き直す
                srcs = fix_sources(d2, bk, srcs)
                res["違う"] = sorted(k for k in truth if vals.get(k) != truth[k])
                dump({"値": vals, "出どころ": srcs}, "ledger", "%d.json" % n)
                dump({"会社": "第 %d 社" % n, "範囲": "単体", "当期": "(作り物の会社。期の日付は書かない)",
                      "項目": [{"項目": k.split("@")[0], "期": k.split("@")[1], "値": v, "単位": "円"} for k, v in sorted(vals.items())]},
                     "mat", "%d.json" % n)
        dump(res, "out", "reread", "%d.json" % n)
        print(n, res.get("読み直し"), res.get("違う"), res["当てられなかった"])


def fix_sources(decided, book, srcs):
    out = {}
    for it in decided["項目"]:
        key = "%s@%s" % (it["項目"], it["期"])
        lst = []
        for c in it.get("成分") or []:
            s = c["シート"]
            lay = L.layout(book[s], decided["シート"][s])
            head = [L.text(x) for x in book[s][lay[0]]]
            r = next(i for i, lab, k in lay[2] if (lab, k) == (c["行"], int(c.get("何番目") or 1)))
            j = G9.col_index(head, c["列"], c.get("列の何番目"))
            col = c["列"] + ("(%d 本目)" % c["列の何番目"] if c.get("列の何番目") else "")
            lst.append({"シート": s, "行": c["行"], "何番目": int(c.get("何番目") or 1), "列": col, "升の値": book[s][r][j], "符号": int(c.get("符号") or 1)})
        out[key] = lst
    return out


def check():
    for n in NUMS:
        lg = load(os.path.join(ROOT, "ledger", "%d.json" % n))
        with open(os.path.join(ROOT, "doc", "%d.md" % n), encoding="utf-8") as f:
            md = f.read()
        tags = load(os.path.join(ROOT, "tag", "%d.json" % n)).get("札") or []
        rows = K.check_doc(md, tags, lg["値"], lg["出どころ"])
        mat = {tuple(k.split("@")): v for k, v in lg["値"].items()}
        over = sum(K.J.is_correct(r["字"], r["値"], K.T.unit_at(md, r["行"], r["始め"]), mat) for r in rows if r["区分"] == "要修正・精査" and "字" in r)
        h = F.report11(n, rows, "第 %d 社の資料" % n)
        p = os.path.join(ROOT, "report", "%d.html" % n)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(h)
        neg = sum(1 for r in rows if r["区分"] == "確認済み" for s in r.get("出どころ") or [] if int(s.get("符号") or 1) == -1)
        m = K.mutate_all(md, tags, rows, lg["値"], lg["出どころ"])
        res = {"区分": {k: sum(r["区分"] == k for r in rows) for k in ("確認済み", "要修正・精査", "点検していない")}, "札": len(tags),
               "札の付かない数": sum(r["札"] is None for r in rows), "言い過ぎ": over, "確認済みで元の升を欠く": sum(1 for r in rows if r["区分"] == "確認済み" and not r.get("出どころ")),
               "引く升": neg, "引く升の印": h.count("(引く)"), "誤り": {k: [len(v), sum(x["止めた"] for x in v)] for k, v in m.items()}}
        dump(res, "out", "check", "%d.json" % n)
        print(n, res["区分"], "引く", neg, h.count("(引く)"), res["誤り"])


if __name__ == "__main__":
    {"stop": stop, "reread": reread, "check": check}[MODE]()
