# -*- coding: utf-8 -*-
"""便 TR2: 確定の台帳を作り、期 1・期 2・変異を読み、止めた時は確定し直しの依頼(顧客向け)を出す(封 §2〜§4)。AI を使わない。

使い方: python3 -E run_tr2.py <TR2 の根>
読むもの: propose/{n}.json・shown/{n}.json・confirm/{n}.json(席の答えは信頼しない data として JSON で読むだけ)・co{n}/ の xlsx
書くもの: out/{n}.json(読んだ結果と、正解との比べ)・stop/{n}/{種類}.html(確定し直しの依頼)
確定の当て方: 確定の席が「直す」とした項目は成分を置き換え、ほかは画面の候補のまま。単位の直しを当てる。
使わない行 = 画面の候補の使わない行 + 確定の席の使わない行(どれかの成分に使う行は除く。ledger_tr2.make_ledger)。
正解(co{n}/正解/値.json)は、読んだ値と比べるためだけに読む。
"""
import copy
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger_tr2 as L  # noqa: E402

ROOT = sys.argv[1]
NUMS = [51, 52, 53, 54, 55, 56]
KINDS = ["列の挿入", "行の並べ替え", "シート名の変更", "行の見出しの微修正", "列の見出しの微修正", "科目の追加", "単位の変更"]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def apply_confirm(shown, reply):
    d = copy.deepcopy(shown)
    rep = {}
    for r in (reply.get("項目") or []):
        if isinstance(r, dict):
            rep["%s@%s" % (r.get("項目"), r.get("期"))] = r
    for it in d["項目"]:
        r = rep.get("%s@%s" % (it["項目"], it["期"]))
        if r and r.get("選び") == "直す" and isinstance(r.get("成分"), list):
            it["成分"] = r["成分"]
    for u in reply.get("単位") or []:
        if isinstance(u, dict) and u.get("シート") in d["シート"]:
            d["シート"][u["シート"]]["単位"] = u.get("単位")
    d["使わない行"] = list(d.get("使わない行") or []) + [u for u in (reply.get("使わない行") or []) if isinstance(u, dict)]
    return d


def compare(vals, truth):
    return sorted(k for k in truth if vals.get(k) != truth[k])


def stop_html(n, kind, diffs):
    rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % tuple(
        html.escape(str(d.get(k, ""))) for k in ("シート", "種類", "前", "今")) for d in diffs)
    return ('<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>台帳の確定し直しのお願い</title>'
            '<style>body{font-family:sans-serif;font-size:10pt;max-width:190mm;margin:8mm auto}table{border-collapse:collapse}'
            'td,th{border:1px solid #ccd;padding:2px 6px}th{background:#f3f5f9}.lead{border-left:5px solid #b7791f;background:#fbf1dc;padding:8px 12px}</style>'
            '</head><body><h1>台帳の確定し直しのお願い(第 %d 社)</h1>'
            '<div class="lead"><b>今回の file は、確定した台帳と様式が違うため、数を 1 つも読まずに止めました。</b><br>'
            '違う升から読んだ数を資料に載せないためです。下の変わった所を見て、台帳を確定し直してください。</div>'
            '<h2>変わった所</h2><table><tr><th>シート</th><th>変わったもの</th><th>確定した時の字</th><th>今回の字</th></tr>%s</table>'
            '<h2>読まなかった数</h2><p>資料に載せる 15 の数すべて。確定し直すまで、資料のこの数は前の台帳で埋めません。</p>'
            '</body></html>') % (n, rows)


def main():
    for n in NUMS:
        co = os.path.join(ROOT, "co%d" % n)
        truth = load(os.path.join(co, "正解", "値.json"))
        b1 = L.load_book(os.path.join(co, "期1", "書き出し.xlsx"))
        b2 = L.load_book(os.path.join(co, "期2", "書き出し.xlsx"))
        out = {}
        pled = L.make_ledger(load(os.path.join(ROOT, "propose", "%d.json" % n)), b1)
        pv, pm = L.naive(pled, b1)
        out["提案"] = {"台帳の誤り": len(pled["誤り"]), "読めない": pm, "違う": compare(pv, truth["期1"])}
        conf = apply_confirm(load(os.path.join(ROOT, "shown", "%d.json" % n)), load(os.path.join(ROOT, "confirm", "%d.json" % n)))
        with open(os.path.join(ROOT, "confirm", "%d.applied.json" % n), "w", encoding="utf-8") as f:
            json.dump(conf, f, ensure_ascii=False, indent=1)
        led = L.make_ledger(conf, b1)
        out["確定"] = {"台帳の誤り": len(led["誤り"])}
        for per, book in (("期1", b1), ("期2", b2)):
            r = L.read(led, book)
            if r[0] == "読めた":
                out["確定"][per] = {"状態": "読めた", "違う": compare(r[1], truth[per])}
            else:
                out["確定"][per] = {"状態": "止める", "違う": sorted(truth[per]), "変わった所": r[1]}
        out["変異"] = {}
        for kind in KINDS:
            bm = L.load_book(os.path.join(co, "変異", kind, "書き出し.xlsx"))
            r = L.read(led, bm)
            nv, nm = L.naive(led, bm)
            rec = {"状態": r[0], "素朴": {"読めない": nm, "違う": compare(nv, truth["変異"][kind]) if not nm else
                                         sorted(k for k in nv if nv[k] != truth["変異"][kind][k])}}
            if r[0] == "止める":
                rec["変わった所"] = r[1]
                d = os.path.join(ROOT, "stop", str(n))
                os.makedirs(d, exist_ok=True)
                with open(os.path.join(d, kind + ".html"), "w", encoding="utf-8") as f:
                    f.write(stop_html(n, kind, r[1]))
            else:
                rec["違う"] = compare(r[1], truth["変異"][kind])
            out["変異"][kind] = rec
        os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
        with open(os.path.join(ROOT, "out", "%d.json" % n), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print(n, "提案の違う", len(out["提案"]["違う"]), "| 確定 期1", out["確定"]["期1"]["状態"], len(out["確定"]["期1"]["違う"]),
              "期2", out["確定"]["期2"]["状態"], len(out["確定"]["期2"]["違う"]), "| 変異の止め",
              sum(v["状態"] == "止める" for v in out["変異"].values()), "/ 7 | 素朴の黙った誤り",
              sum(1 for v in out["変異"].values() if not v["素朴"]["読めない"] and v["素朴"]["違う"]))


if __name__ == "__main__":
    main()
