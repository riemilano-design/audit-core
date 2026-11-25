# -*- coding: utf-8 -*-
"""便 TR10: XBRL でない経路の 7 → 5(封 §2)。札の数を、確定の台帳が会計ソフトの書き出しから読んだ値と照らす。AI を使わない。

点検の順(TR4・TR5 と同じ形。照合の基準だけを台帳に替える):
  札の数が資料に在るか → 単位 → 符号と向き → 期の字と項目の字の食い違い(TR4)→ R1・R2(TR5)→ 台帳の値と照らす。
  台帳の値: 金額は「項目@期」の値。増減額は当期(末)− 前期(末)。増減率は増減額 ÷ |前期(末)| × 100。
  資料の桁で同じ(四捨五入か切り捨て。judge_tr4._shown)なら確認済み。確認済みには、照らした台帳の値と、
  その値を読んだ元の升(シート・行・列・升の値)を付ける。台帳に無い項目と期は「点検していない」。
  札の付かない数は「点検していない」(TR4 と同じ)。
"""
import copy
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tr4"))
sys.path.insert(0, os.path.join(HERE, "..", "tr5"))
import judge_tr4 as J  # noqa: E402
import numbers_tr4 as N  # noqa: E402
import rules_tr5 as T  # noqa: E402

SCALE = {"円": 1, "千円": 1000, "百万円": 1000000}
UNITN = {"％": "%", "名": "人"}
PRIOR = {"当期": "前期", "当期末": "前期末"}
CUR = {"損益": "当期", "財政": "当期末"}
PL = {"売上高", "営業利益", "経常利益", "当期純利益", "減価償却費"}
ORDER = ["売上高", "営業利益", "経常利益", "当期純利益", "減価償却費", "現金及び預金", "流動資産合計", "資産合計", "短期借入金",
         "長期借入金", "負債合計", "純資産合計"]


def norm(s):
    s = (s or "").replace(" ", "").replace("＋", "+")
    s = re.sub(r"^[+]", "", s)
    return re.sub(r"^[△▲−]", "-", s)


def locate(recs, tag):
    try:
        line = int(tag.get("行")) - 1
        k = int(tag.get("何番目") or 1)
    except (TypeError, ValueError):
        return None
    cand = [r for r in recs if r["行"] == line and norm(r["字"]) == norm(str(tag.get("字")))]
    return cand[k - 1] if 1 <= k <= len(cand) else None


def expected(tag, ledger):
    """札の示す台帳の値(表の単位に直す前の円か %)と、使った台帳の鍵。台帳に無ければ (None, 鍵)。"""
    item, per, kind = tag.get("項目"), tag.get("期"), tag.get("種類")
    if kind == "金額":
        k = "%s@%s" % (item, per)
        return (ledger[k], [k]) if k in ledger else (None, [k])
    cur = per if per in PRIOR else CUR["損益" if item in PL else "財政"]
    a, b = "%s@%s" % (item, cur), "%s@%s" % (item, PRIOR[cur])
    if a not in ledger or b not in ledger:
        return None, [a, b]
    d = ledger[a] - ledger[b]
    if kind == "増減額":
        return d, [a, b]
    if kind == "増減率":
        return (d / abs(ledger[b]) * 100 if ledger[b] else None), [a, b]
    return None, [a, b]


def check_doc(md, tags, ledger, srcs):
    recs = N.extract_all(md)
    rows, used, located = [], set(), []
    for ti, tag in enumerate(tags):
        row = {"札の番号": ti, "札": tag}
        r = locate(recs, tag)
        if r is None:
            row.update({"区分": "要修正・精査", "訳": "札の数が資料に見つからない"})
            rows.append(row)
            continue
        used.add((r["行"], r["始め"]))
        located.append((r, tag, ti))
        row.update({"行": r["行"], "始め": r["始め"], "字": r["字"], "値": r["値"], "場所": r["場所"], "抜粋": N.snippet(md, r), "_rec": r})
        rows.append(row)
    hit1 = T.r1(md, located)
    for row in rows:
        if "_rec" not in row:
            continue
        r, tag = row.pop("_rec"), row["札"]
        kind = tag.get("種類")
        tunit = UNITN.get(tag.get("単位"), tag.get("単位"))
        runit = UNITN.get(r["単位"], r["単位"])
        if kind not in ("金額", "増減額", "増減率", "人数") or tag.get("期") not in ("当期", "前期", "当期末", "前期末") \
                or tag.get("向き") not in ("+", "−", "-"):
            row.update({"区分": "要修正・精査", "訳": "札の形が読めない"})
            continue
        if runit and tunit and runit != tunit:
            row.update({"区分": "要修正・精査", "訳": "札と本文の単位が違う(本文 %s・札 %s)" % (runit, tunit)})
            continue
        if r["値"] < 0 and tag.get("向き") == "+":
            row.update({"区分": "要修正・精査", "訳": "本文は負の数なのに、札の向きが +"})
            continue
        cf = N.conflicts(r, tag)
        if cf:
            row.update({"区分": "要修正・精査", "訳": "札と本文の%sが違う(本文の字「%s」)" % (cf[0][0], cf[0][1])})
            continue
        if ti_in(row, hit1):
            row.update({"区分": "要修正・精査", "訳": "同じ文に、同じ項目・同じ期の金額の札が 2 枚在る", "規則": "R1"})
            continue
        stop, why = T.r2(r, tag)
        if stop:
            row.update({"区分": "要修正・精査", "訳": why, "規則": "R2"})
            continue
        v, keys = expected(tag, ledger)
        if v is None:
            row.update({"区分": "点検していない", "訳": "台帳にこの項目・期が無い", "台帳の鍵": keys})
            continue
        unit = runit or tunit
        scale = 1 if unit == "%" else SCALE.get(unit)
        if scale is None:
            row.update({"区分": "点検していない", "訳": "単位が読めない", "台帳の鍵": keys})
            continue
        k = J.decimals_of(r["字"])
        neg = tag.get("向き") in ("−", "-")
        sign_ok = (v < 0) == neg or v == 0
        got = int(round(abs(r["値"]) * 10 ** k))
        if got in J._shown(v / scale, k) and sign_ok:
            row.update({"区分": "確認済み", "訳": "台帳の値と一致", "台帳の鍵": keys, "台帳の値": v,
                        "出どころ": [dict(s, 鍵=kk) for kk in keys for s in srcs.get(kk, [])]})
        else:
            row.update({"区分": "要修正・精査", "訳": "台帳の値と合わない" if sign_ok else "台帳の値と向きが違う", "台帳の鍵": keys, "台帳の値": v})
    for r in recs:
        if (r["行"], r["始め"]) not in used:
            rows.append({"札の番号": None, "札": None, "行": r["行"], "始め": r["始め"], "字": r["字"], "値": r["値"], "場所": r["場所"],
                         "単位": r["単位"], "抜粋": N.snippet(md, r), "区分": "点検していない", "訳": "札が付いていない数"})
    return rows


def ti_in(row, hit):
    return row["札の番号"] in hit


def fmt(v, unit, like):
    q = int(round(abs(v) / SCALE[unit]))
    s = "{:,}".format(q)
    if v < 0:
        s = ("△" if not like.startswith(("-", "−")) else "-") + s
    return s


def replace_at(md, line, start, old, new):
    lines = md.split("\n")
    s = lines[line]
    assert s[start:start + len(old)] == old
    lines[line] = s[:start] + new + s[start + len(old):]
    return "\n".join(lines)


def nth_at(md, line, start, text):
    """置き換えた後の行で、start の位置の数が、同じ字の数の左から何番目か。"""
    recs = [r for r in N.extract_all(md) if r["行"] == line and norm(r["字"]) == norm(text)]
    return next((i for i, r in enumerate(recs, 1) if r["始め"] == start), 1)


def bump2(s):
    for i in range(len(s) - 1, -1, -1):
        if s[i].isdigit():
            d = int(s[i])
            return s[:i] + str(d + 2 if d <= 7 else d - 2) + s[i + 1:]
    return s


def mutate_all(md, tags, rows, ledger, srcs):
    """確認済みの札の全部に、1 つずつ誤りを入れる。(b) 期の隠し・(d) 項目の隠し・(a′) 数と札の字・(c) 札を外す・(e) 単位の字。"""
    out = {"b": [], "d": [], "a2": [], "c": [], "e": []}
    ok = [r for r in rows if r["区分"] == "確認済み"]

    def run(md2, t2, idx):
        r2 = next(x for x in check_doc(md2, t2, ledger, srcs) if x.get("札の番号") == idx)
        return {"止めた": r2["区分"] != "確認済み", "訳": r2["訳"]}

    for r in ok:
        t, i = r["札"], r["札の番号"]
        if t["種類"] == "金額" and t.get("単位") in SCALE and t["期"] in PRIOR:
            pk = "%s@%s" % (t["項目"], PRIOR[t["期"]])
            if pk in ledger:
                new = fmt(ledger[pk], t["単位"], r["字"])
                if norm(new) != norm(r["字"]):
                    md2 = replace_at(md, r["行"], r["始め"], r["字"], new)
                    t2 = copy.deepcopy(tags)
                    t2[i].update({"字": new, "期": PRIOR[t["期"]], "何番目": nth_at(md2, r["行"], r["始め"], new)})
                    out["b"].append(dict(run(md2, t2, i), 場所=r["場所"]))
        if t["種類"] == "金額" and r["場所"] == "文" and t.get("単位") in SCALE:
            other = next((it for it in ORDER if it != t["項目"] and "%s@%s" % (it, t["期"]) in ledger
                          and norm(fmt(ledger["%s@%s" % (it, t["期"])], t["単位"], r["字"])) != norm(r["字"])), None)
            if other:
                v = ledger["%s@%s" % (other, t["期"])]
                new = fmt(v, t["単位"], r["字"])
                md2 = replace_at(md, r["行"], r["始め"], r["字"], new)
                t2 = copy.deepcopy(tags)
                t2[i].update({"字": new, "項目": other, "向き": "−" if v < 0 else "+", "何番目": nth_at(md2, r["行"], r["始め"], new)})
                out["d"].append(run(md2, t2, i))
        new = bump2(r["字"])
        md2 = replace_at(md, r["行"], r["始め"], r["字"], new)
        t2 = copy.deepcopy(tags)
        t2[i].update({"字": new, "何番目": nth_at(md2, r["行"], r["始め"], new)})
        out["a2"].append(run(md2, t2, i))
        t2 = [x for j, x in enumerate(tags) if j != i]
        rr = next((x for x in check_doc(md, t2, ledger, srcs) if x.get("行") == r["行"] and x.get("始め") == r["始め"]), None)
        out["c"].append({"止めた": rr is not None and rr["区分"] == "点検していない"})
        if r["場所"] == "文":
            line = md.split("\n")[r["行"]]
            end = r["始め"] + len(r["字"])
            m = re.match(r"(\s{0,2})(百万円|千円)", line[end:])
            if m:
                md2 = replace_at(md, r["行"], end + len(m.group(1)), m.group(2), "千円" if m.group(2) == "百万円" else "百万円")
                out["e"].append(run(md2, tags, i))
    return out


def report(n, rows, title):
    """顧客に渡す点検レポート(HTML)。社内の符号(S の番号など)は出さない。"""
    e = html.escape
    cnt = {k: sum(r["区分"] == k for r in rows) for k in ("確認済み", "要修正・精査", "点検していない")}
    b = ["<h1>資料点検レポート</h1><p>点検した資料: %s</p>" % e(title),
         '<p class="basis">照合の基準: お預かりした会計ソフトの書き出しから、確定した台帳で機械が読んだ数。資料の作り手が数ごとに付けた札'
         '(どの項目・期・種類の数か)は、照合先を選ぶためだけに使い、基準には使っていません。</p>']
    lead = "直すか精査が必要な数があります" if cnt["要修正・精査"] else "台帳と合わない数は見つかりませんでした"
    b.append('<div class="lead%s"><b>点検結果: %s</b></div>' % ("" if cnt["要修正・精査"] else " ok", lead))
    b.append('<div class="counts">%s</div>' % "".join("<div>%s<span>%d</span></div>" % (k, v) for k, v in cnt.items()))
    b.append("<h2>要修正・精査</h2>")
    k = 0
    for r in rows:
        if r["区分"] == "要修正・精査":
            k += 1
            t = r["札"] or {}
            b.append('<div class="card"><h3>%d. %s(%s・%s)― 資料の数「%s」</h3><p>%s</p><p>原文の抜粋: %s</p><p>台帳の値: %s</p></div>' % (
                k, e(str(t.get("項目"))), e(str(t.get("期"))), e(str(t.get("種類"))), e(r.get("字") or str(t.get("字"))), e(r["訳"]),
                e(r.get("抜粋") or "(資料に見つからない)"), e(_val(r))))
    if not k:
        b.append("<p>(ありません)</p>")
    b.append("<h2>確認済み</h2><p>札の示す台帳の数と一致した数です。<b>原文の抜粋が札(項目・期・種類)と同じ意味かを、目で確かめてください。</b></p>"
             "<table><tr><th>札(項目・期・種類)</th><th>資料の数</th><th>原文の抜粋</th><th>台帳の値と、元の升</th></tr>")
    for r in rows:
        if r["区分"] == "確認済み":
            src = "<br>".join("%s: シート「%s」・行「%s」・列「%s」・升の値 %s" % (e(s["鍵"]), e(s["シート"]), e(s["行"]), e(s["列"]), e(str(s["升の値"])))
                              for s in r["出どころ"])
            b.append("<tr><td>%s・%s・%s</td><td>%s</td><td>%s</td><td>%s<br>%s</td></tr>" % (
                e(r["札"]["項目"]), e(r["札"]["期"]), e(r["札"]["種類"]), e(r["字"]), e(r["抜粋"]), e(_val(r)), src))
    b.append("</table><h2>点検していない数</h2><p>札が付いていない数と、台帳に照合先の無い数です。必要なら人が確かめてください。</p>"
             "<table><tr><th>資料の数</th><th>場所</th><th>原文の抜粋</th><th>訳</th></tr>")
    for r in rows:
        if r["区分"] == "点検していない":
            b.append("<tr><td>%s</td><td>%s・%d 行目</td><td>%s</td><td>%s</td></tr>" % (e(r["字"]), e(r["場所"]), r["行"] + 1, e(r["抜粋"]), e(r["訳"])))
    b.append("</table><h2>この点検の限界</h2><ul><li>資料の桁(四捨五入か切り捨て)で一致すれば一致とみなします。</li>"
             "<li>台帳が正しく確定されていることを前提にします。台帳と帳簿の一致は見ません。</li>"
             "<li>札と本文の食い違いは、抜粋の中の期の字と項目の字だけを機械で見ています。文の意味は、確認済みの原文の抜粋を人が見て確かめてください。</li></ul>")
    css = ("body{font-family:sans-serif;font-size:10pt;max-width:200mm;margin:8mm auto}table{border-collapse:collapse}td,th{border:1px solid #ccd;"
           "padding:2px 6px;vertical-align:top}th{background:#f3f5f9}.lead{border-left:5px solid #b7791f;background:#fbf1dc;padding:8px 12px}"
           ".lead.ok{border-color:#2f855a;background:#e6f4ea}.counts{display:flex;gap:12px;margin:8px 0}.counts div{border:1px solid #ccd;padding:4px 10px}"
           ".counts span{display:block;font-size:14pt;font-weight:bold}.card{border:1px solid #e2b4b4;padding:4px 10px;margin:6px 0}")
    return '<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>資料点検レポート 第%s社</title><style>%s</style></head><body>%s</body></html>' % (
        n, css, "\n".join(b))


def _val(r):
    v = r.get("台帳の値")
    if v is None:
        return "-"
    if r["札"] and r["札"].get("種類") == "増減率":
        return "%.2f%%" % v
    return "{:,} 円".format(v)
