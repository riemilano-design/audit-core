# -*- coding: utf-8 -*-
"""便 TR6: 確定し直しの流れを回す(封 §2〜§4)。AI を使わない。

使い方:
  python3 -E run_tr6.py prep <audit-core> <TR2 の根> <TR6 の根>   止める・縮めた差分・案だけで読む・席の画面を作る
  python3 -E run_tr6.py seat <audit-core> <TR2 の根> <TR6 の根>   席の決めを当てて、変異の file(期 2)と期 3 を読む
確定の台帳は TR2 の確定(confirm/{n}.applied.json)と TR2 の期 1 の file から作る(TR2 と同じ)。
席の答え(reply/{n}.json)は信頼しない data として JSON で読むだけ。正解は読んだ値と比べるためだけに読む。
画面の順は社ごとに固定の乱数で混ぜ、種類との対は key/{n}.json に置く(席には渡さない)。
"""
import html
import json
import os
import random
import sys

MODE, AC, TR2, ROOT = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AC, "explore", "tr2"))
sys.path.insert(0, HERE)
import ledger_tr2 as L  # noqa: E402
import reconf_tr6 as R  # noqa: E402
import build_tr2 as B  # noqa: E402

KINDS = B.KINDS + ["意味の変わる改名", "紛れの科目の追加"]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(obj, *parts):
    p = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def compare(vals, truth):
    return sorted(k for k in truth if vals.get(k) != truth[k])


def base(n):
    conf = load(os.path.join(TR2, "confirm", "%d.applied.json" % n))
    b1 = L.load_book(os.path.join(TR2, "co%d" % n, "期1", "書き出し.xlsx"))
    return conf, L.make_ledger(conf, b1)


def book(n, kind, per):
    return L.load_book(os.path.join(ROOT, "co%d" % n, kind, per, "書き出し.xlsx"))


def read_with(decided, bk, truth):
    led = L.make_ledger(decided, bk)
    r = L.read(led, bk)
    if led["誤り"]:
        return {"状態": "台帳が作れない", "誤り": len(led["誤り"])}, led
    if r[0] != "読めた":
        return {"状態": "止める", "変わった所": len(r[1])}, led
    return {"状態": "読めた", "違う": compare(r[1], truth)}, led


def plan_text(ch):
    a = ch["案"]
    if a is None:
        return "(案なし。決めてください)"
    if "対応" in a:
        return "「%s」を「%s」として読む" % (ch["前"], a["対応"])
    if "単位" in a:
        return "単位を %s にする" % a["単位"]
    return "台帳は変えない(了承)"


def screen(n, sk, changes, conf, bk, plan_read):
    rows = []
    rename = {ch["シート"]: ch["案"]["対応"] for ch in changes if ch["種類"] == "シートの名の変更"}
    for ch in changes:
        ctx = ""
        if ch["種類"].startswith("行の"):
            lab = ch["今"] if ch["今"] != "(無い)" else None
            cx = R.context(conf, bk, ch["シート"], lab, rename) if lab else []
            if cx:
                ctx = "<table class=ctx>" + "".join("<tr%s><td>%s</td></tr>" % (
                    ' class="me"' if c["これ"] else "", "</td><td>".join(html.escape(v) for v in c["値"])) for c in cx) + "</table>"
        rows.append("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            ch["番号"], html.escape(ch["シート"]), html.escape(ch["種類"]), html.escape(str(ch["前"])), html.escape(str(ch["今"])),
            html.escape("・".join(ch["影響"]) or "なし"), html.escape(plan_text(ch)), ctx))
    if plan_read is None:
        pv = "<p>案だけでは読めません(決めていない所が在ります)。</p>"
    else:
        pv = "<table><tr><th>項目@期</th><th>案を当てて今回の file から読んだ値(円)</th></tr>" + "".join(
            "<tr><td>%s</td><td style='text-align:right'>{:,}</td></tr>".format(v) % html.escape(k) for k, v in plan_read.items()) + "</table>"
    return ('<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>台帳の確定し直し</title>'
            '<style>body{font-family:sans-serif;font-size:10pt;max-width:260mm;margin:8mm auto}table{border-collapse:collapse;margin:4px 0}'
            'td,th{border:1px solid #ccd;padding:2px 6px;vertical-align:top}th{background:#f3f5f9}.ctx td{border:1px solid #eee;font-size:9pt}'
            '.me td{background:#fff3c4}.lead{border-left:5px solid #b7791f;background:#fbf1dc;padding:8px 12px}</style></head><body>'
            '<h1>台帳の確定し直し(第 %d 社・画面 %s)</h1>'
            '<div class="lead">今回の file は、確定した台帳と様式が違うため、数を読まずに止めました。変わった所は <b>%d か所</b>です。'
            '所ごとに機械の案を見て、案のままでよいか、直すかを決めてください。案の無い所は決めてください。</div>'
            '<h2>変わった所</h2><table><tr><th>番号</th><th>シート</th><th>変わったもの</th><th>確定した時の字</th><th>今回の字</th>'
            '<th>影響する項目</th><th>機械の案</th><th>今回の file の前後の行(黄色がその行)</th></tr>%s</table>'
            '<h2>案を当てた時の値</h2>%s</body></html>') % (n, sk, len(changes), "".join(rows), pv)


def prep():
    for n in B.NUMS:
        conf, led = base(n)
        truth = load(os.path.join(ROOT, "co%d" % n, "正解.json"))["値"]
        order = KINDS[:]
        random.Random(n * 11).shuffle(order)
        key, rec = {}, {}
        for k, kind in enumerate(order, 1):
            sk = "s%d" % k
            key[sk] = kind
            bk = book(n, kind, "期2")
            r = L.read(led, bk)
            changes = R.diff(conf, led, bk)
            d2, bad = R.apply(conf, changes, R.plan_only(changes))
            st, led2 = read_with(d2, bk, truth[kind]["期2"])
            plan_read = None
            if st["状態"] == "読めた":
                r2 = L.read(led2, bk)
                aff = sorted({a for ch in changes for a in ch["影響"]})
                plan_read = {a: r2[1][a] for a in aff}
            rec[kind] = {"画面": sk, "止めた": r[0] == "止める", "TR2 の形の行": len(r[1]) if r[0] == "止める" else 0,
                         "縮めた行": len(changes), "案の無い所": sum(ch["案"] is None for ch in changes), "案だけ": st,
                         "変わった所": [{k2: ch[k2] for k2 in ("番号", "種類", "シート", "前", "今", "影響", "案")} for ch in changes]}
            p = os.path.join(ROOT, "screen", str(n), sk + ".html")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(screen(n, sk, changes, conf, bk, plan_read))
        dump(key, "key", "%d.json" % n)
        dump(rec, "out", "prep", "%d.json" % n)
        print(n, {k: (v["TR2 の形の行"], v["縮めた行"], v["案だけ"]["状態"], len(v["案だけ"].get("違う", []))) for k, v in rec.items()})


def seat():
    for n in B.NUMS:
        conf, led = base(n)
        truth = load(os.path.join(ROOT, "co%d" % n, "正解.json"))["値"]
        key = load(os.path.join(ROOT, "key", "%d.json" % n))
        prep_rec = load(os.path.join(ROOT, "out", "prep", "%d.json" % n))
        rp = os.path.join(ROOT, "reply", "%d.json" % n)
        reply = load(rp) if os.path.exists(rp) else {}
        out = {}
        for sk, kind in key.items():
            bk = book(n, kind, "期2")
            changes = R.diff(conf, led, bk)
            ans = ((reply.get("画面") or {}).get(sk) or {})
            dec, form = {}, []
            for x in ans.get("決め") or []:
                if not isinstance(x, dict) or not isinstance(x.get("番号"), int):
                    form.append("読めない決め")
                    continue
                ch = next((c for c in changes if c["番号"] == x["番号"]), None)
                if x.get("選び") == "案のまま" and ch is not None and ch["案"] is not None:
                    dec[x["番号"]] = ch["案"]
                elif x.get("選び") == "決める" and isinstance(x.get("決め"), dict):
                    dec[x["番号"]] = x["決め"]
                else:
                    form.append("番号 %s の選びが読めない" % x["番号"])
            d2, bad = R.apply(conf, changes, dec)
            st2, led2 = read_with(d2, bk, truth[kind]["期2"])
            res = {"決め": {str(k): v for k, v in dec.items()}, "形の誤り": form + ["%s: %s" % b for b in bad],
                   "案から変えた": sum(1 for c in changes if c["番号"] in dec and c["案"] is not None and dec[c["番号"]] != c["案"]),
                   "期2": st2}
            if st2["状態"] == "読めた":
                res["期3"], _ = read_with(d2, book(n, kind, "期3"), truth[kind]["期3"])
            res["気づき"] = ans.get("気づき", "")
            out[kind] = res
        dump(out, "out", "seat", "%d.json" % n)
        print(n, {k: (v["期2"]["状態"], len(v["期2"].get("違う", [])), v.get("期3", {}).get("状態"),
                      len(v.get("期3", {}).get("違う", [])), v["案から変えた"], len(v["形の誤り"])) for k, v in out.items()})


if __name__ == "__main__":
    {"prep": prep, "seat": seat}[MODE]()
