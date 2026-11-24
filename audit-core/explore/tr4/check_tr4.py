# -*- coding: utf-8 -*-
"""便 TR4: 札で資料を点検する(封 §3)。AI を使わない。

使い方: python3 -I check_tr4.py <audit-core の folder> <TR0 の根> <TR1 の根> <TR3 の根> <TR4 の根>
読むもの: <TR4>/doc/{n}.md・<TR4>/tag/{n}.json(書く席の答え。信頼しない data として字と JSON で読むだけ)・<TR1>/A/{n}.json(基準 A)
          回帰に <TR3>/check・<TR3>/miss・<TR3>/doc・<TR0>/check・<TR0>/mat
書くもの: <TR4>/check/{n}.json・<TR4>/report/{n}.html・<TR4>/mut/{n}.json・<TR4>/regress.json
照合は TR1 の check_tr1.verify(基準 A・engine を読むだけ)。札は照合先を選ぶ索引としてだけ使い、基準には触れない。
"""
import copy
import html
import json
import os
import re
import sys

AC, TR0, TR1, TR3, OUT = sys.argv[1:6]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], AC, TR0, TR1, OUT]
sys.path.insert(0, os.path.join(AC, "explore", "tr2"))
sys.path.insert(0, HERE)
import report_tr1_v2 as R  # noqa: E402  (中で check_tr1 を読み込む)
import judge_tr4 as J  # noqa: E402
import numbers_tr4 as N  # noqa: E402

C = R.C
KIND = {"金額": "single_value", "増減額": "difference", "増減率": "ratio_change", "人数": "single_value"}
PERIODS = ("当期", "前期", "当期末", "前期末")
UNITN = {"％": "%", "名": "人"}
SCALE = {"千円": 1000, "百万円": 1000000}
ORDER = ["売上高", "営業利益", "経常利益", "当期純利益", "減価償却費", "現金及び預金", "流動資産合計", "資産合計", "短期借入金",
         "長期借入金", "負債合計", "純資産合計"]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


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


def check_doc(md, tags, A):
    recs = N.extract_all(md)
    rows, used = [], set()
    for ti, tag in enumerate(tags):
        row = {"札の番号": ti, "札": tag}
        r = locate(recs, tag)
        if r is None:
            row.update({"区分": "要修正・精査", "訳": "札の数が資料に見つからない", "info": {}})
            rows.append(row)
            continue
        used.add((r["行"], r["始め"]))
        row.update({"行": r["行"], "始め": r["始め"], "字": r["字"], "値": r["値"], "場所": r["場所"], "抜粋": N.snippet(md, r)})
        kind = tag.get("種類")
        tunit = UNITN.get(tag.get("単位"), tag.get("単位"))
        runit = UNITN.get(r["単位"], r["単位"])
        if kind not in KIND or tag.get("期") not in PERIODS or tag.get("向き") not in ("+", "−", "-"):
            row.update({"区分": "要修正・精査", "訳": "札の形が読めない", "info": {}})
        elif runit and tunit and runit != tunit:
            row.update({"区分": "要修正・精査", "訳": "札と本文の単位が違う(本文 %s・札 %s)" % (runit, tunit), "info": {}})
        elif r["値"] < 0 and tag.get("向き") == "+":
            row.update({"区分": "要修正・精査", "訳": "本文は負の数なのに、札の向きが +", "info": {}})
        else:
            cf = N.conflicts(r, tag)
            if cf:
                row.update({"区分": "要修正・精査", "訳": "札と本文の%sが違う(本文の字「%s」)" % (cf[0][0], cf[0][1]), "info": {}})
            else:
                neg = tag.get("向き") in ("−", "-")
                unit = runit or tunit
                rv = {"項目": tag.get("項目"), "期": tag["期"], "種類": KIND[kind], "単位": "人" if kind == "人数" else unit,
                      "値": abs(r["値"]) * (-1 if (neg and kind == "金額") else 1), "符号": (-1 if neg else 1) if kind in ("増減額", "増減率") else None}
                cls, info = C.verify(rv, A, "A")
                if cls == "要確認":
                    cls = "軽量確認" if info.get("held") else "要修正・精査"
                row.update({"区分": cls, "訳": info.get("訳") or info.get("engine") or "", "info": info, "rv": rv})
        rows.append(row)
    for r in recs:
        if (r["行"], r["始め"]) not in used:
            rows.append({"札番号": None, "札": None, "行": r["行"], "始め": r["始め"], "字": r["字"], "値": r["値"], "場所": r["場所"],
                         "単位": r["単位"], "抜粋": N.snippet(md, r), "区分": "点検していない", "訳": "札が付いていない数", "info": {}})
    return rows


def fmt(v, unit, like):
    q = int(round(abs(v) / SCALE[unit]))
    s = "{:,}".format(q)
    if v < 0:
        s = ("△" if not like.startswith(("-", "−")) else "-") + s
    return s


def report(n, rows, A, title):
    cnt = {k: sum(r["区分"] == k for r in rows) for k in ("確認済み", "要修正・精査", "軽量確認", "人の判断が必要", "点検していない")}
    e = html.escape
    b = ["<h1>資料点検レポート</h1><p>点検した資料: %s</p>" % e(title),
         '<p class="basis">照合の基準: 提出された有価証券報告書の XBRL(生のデータを機械で読んだもの)。資料の作り手が数ごとに付けた札(どの項目・期・種類の数か)は、照合先を選ぶためだけに使い、基準には使っていません。範囲: %s。</p>' % e(A.get("範囲") or "未定")]
    lead = "直すか精査が必要な数があります" if cnt["要修正・精査"] else ("元と合わない数は見つかりませんでした" if not cnt["軽量確認"] else "元と合わない数は見つかりませんでした(軽量確認あり)")
    b.append('<div class="lead%s"><b>点検結果: %s</b></div>' % ("" if cnt["要修正・精査"] else " ok", lead))
    b.append('<div class="counts">%s</div>' % "".join("<div>%s<span>%d</span></div>" % (k, v) for k, v in cnt.items()))
    b.append("<h2>要修正・精査</h2>")
    k = 0
    for r in rows:
        if r["区分"] != "要修正・精査":
            continue
        k += 1
        t = r["札"] or {}
        if r["info"].get("engine"):
            what, orig, tips, srcs = C.advice(dict(r["rv"], 字=r["字"], 場所=r["場所"], 行=r["行"]), r["info"], A)
        else:
            what, orig, tips, srcs = r["訳"], "-", ["資料の数と札を確かめ、どちらかを直してください。"], []
        b.append('<div class="card"><h3>%d. %s(%s・%s)― 資料の数「%s」</h3><p>%s</p><table><tr><th>原文の抜粋</th><td>%s</td></tr><tr><th>元の数</th><td>%s</td></tr><tr><th>元の数の出どころ</th><td>%s</td></tr><tr><th>資料の場所</th><td>%s</td></tr></table><ul>%s</ul></div>' % (
            k, e(str(t.get("項目"))), e(str(t.get("期"))), e(str(t.get("種類"))), e(r.get("字") or str(t.get("字"))), e(what), e(r.get("抜粋") or "(資料に見つからない)"),
            e(orig), "<br>".join(e(s) for s in srcs) or "-", e("%s・%s 行目" % (r.get("場所", "-"), (r.get("行", -1) + 1) if "行" in r else t.get("行"))),
            "".join("<li>%s</li>" % e(x) for x in tips)))
    if not k:
        b.append("<p>(ありません)</p>")
    b.append("<h2>軽量確認</h2><p>数は照合先と一致しています。同じ額が別の期・別の枠にも在るので、原文の抜粋を見て、資料で言いたい数かを確かめてください。</p><table><tr><th>札</th><th>資料の数</th><th>原文の抜粋</th><th>照合先と、同じ額の在る枠</th></tr>")
    for r in rows:
        if r["区分"] == "軽量確認":
            ent, words = R.siblings(dict(r["rv"], 字=r["字"], info=r["info"]), A)
            b.append("<tr><td>%s・%s・%s</td><td>%s</td><td>%s</td><td>%s<br>同じ額: %s</td></tr>" % (
                e(r["札"]["項目"]), e(r["札"]["期"]), e(r["札"]["種類"]), e(r["字"]), e(r["抜粋"]), e(C.source_line(ent)) if ent else "-", e(" / ".join(words))))
    b.append("</table><h2>確認済み</h2><p>札の示す元の XBRL の数と一致した数です。<b>原文の抜粋が札(項目・期・種類)と同じ意味かを、目で確かめてください。</b>機械は、抜粋の中の期の字と項目の字だけを札と比べています。</p>")
    b.append("<table><tr><th>札(項目・期・種類)</th><th>資料の数</th><th>原文の抜粋</th><th>確かめたこと</th></tr>")
    for r in rows:
        if r["区分"] == "確認済み":
            b.append("<tr><td>%s・%s・%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                e(r["札"]["項目"]), e(r["札"]["期"]), e(r["札"]["種類"]), e(r["字"]), e(r["抜粋"]),
                "<br>".join(e(x) for x in C.checked_text(dict(r["rv"], 字=r["字"]), r["info"], A))))
    b.append("</table><h2>点検していない数</h2><p>札が付いていない数と、元の XBRL に照合先の無い数です。必要なら人が確かめてください。</p><table><tr><th>資料の数</th><th>場所</th><th>原文の抜粋</th><th>訳</th></tr>")
    for r in rows:
        if r["区分"] == "点検していない":
            b.append("<tr><td>%s</td><td>%s・%d 行目</td><td>%s</td><td>%s</td></tr>" % (e(r["字"]), e(r["場所"]), r["行"] + 1, e(r["抜粋"]), e(r["訳"])))
    b.append("</table>" + R.LIMITS.replace("</ul>", "<li>札と本文の食い違いは、抜粋の中の期の字と項目の字だけを機械で見ています。文の意味(当期の数として書いた文に前期の数を置いた、など)は、確認済みの原文の抜粋を人が見て確かめてください。</li></ul>"))
    return '<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>資料点検レポート 第%s社</title><style>%s</style></head><body>%s</body></html>' % (n, C.CSS, "\n".join(b))


def replace_at(md, line, start, old, new):
    lines = md.split("\n")
    s = lines[line]
    assert s[start:start + len(old)] == old
    lines[line] = s[:start] + new + s[start + len(old):]
    return "\n".join(lines)


def bump2(s):
    for i in range(len(s) - 1, -1, -1):
        if s[i].isdigit():
            d = int(s[i])
            return s[:i] + str(d + 2 if d <= 7 else d - 2) + s[i + 1:]
    return s


def mutants(md, tags, rows, A):
    ok = [r for r in rows if r["区分"] == "確認済み"]
    out = {}
    amt = [r for r in ok if r["札"]["種類"] == "金額" and r["札"]["期"] in PERIODS]
    text_amt = [r for r in amt if r["場所"] == "文" and r["札"].get("単位") in SCALE]
    # (a) 本文の数の最後の桁を 2 変える(札はそのまま)
    if amt:
        r = amt[0]
        out["a"] = (replace_at(md, r["行"], r["始め"], r["字"], bump2(r["字"])), tags, r["札番号"] if "札番号" in r else r["札の番号"])
    # (b) 期の隠し
    for r in text_amt:
        t = r["札"]
        if t["期"] not in ("当期", "当期末"):
            continue
        pk = "%s@%s" % (t["項目"], C.CTX[C.periods(t["項目"])[1]])
        if pk not in A["map"]:
            continue
        new = fmt(A["map"][pk]["値"], t["単位"], r["字"])
        if norm(new) == norm(r["字"]):
            continue
        t2 = copy.deepcopy(tags)
        t2[r["札の番号"]].update({"字": new, "期": C.periods(t["項目"])[1], "何番目": 1})
        out["b"] = (replace_at(md, r["行"], r["始め"], r["字"], new), t2, r["札の番号"])
        break
    # (c) 札を 1 枚外す
    if ok:
        r = ok[0]
        t2 = [t for i, t in enumerate(tags) if i != r["札の番号"]]
        out["c"] = (md, t2, ("外した", r["行"], r["始め"]))
    # (d) 項目の隠し
    for r in text_amt:
        t = r["札"]
        ctx = C.CTX[t["期"]]
        other = next((it for it in ORDER if it != t["項目"] and "%s@%s" % (it, ctx) in A["map"]
                      and norm(fmt(A["map"]["%s@%s" % (it, ctx)]["値"], t["単位"], r["字"])) != norm(r["字"])), None)
        if other is None:
            continue
        v = A["map"]["%s@%s" % (other, ctx)]["値"]
        new = fmt(v, t["単位"], r["字"])
        t2 = copy.deepcopy(tags)
        t2[r["札の番号"]].update({"字": new, "項目": other, "向き": "−" if v < 0 else "+", "何番目": 1})
        out["d"] = (replace_at(md, r["行"], r["始め"], r["字"], new), t2, r["札の番号"])
        break
    # (e) 単位の書き換え
    for r in ok:
        if r["場所"] != "文":
            continue
        line = md.split("\n")[r["行"]]
        end = r["始め"] + len(r["字"])
        m = re.match(r"(\s{0,2})(百万円|千円)", line[end:])
        if not m:
            continue
        new_u = "千円" if m.group(2) == "百万円" else "百万円"
        md2 = replace_at(md, r["行"], end + len(m.group(1)), m.group(2), new_u)
        out["e"] = (md2, tags, r["札の番号"])
        break
    return out


def judge_mut(kind, rows, key):
    if kind == "c":
        _, line, start = key
        r = next((x for x in rows if x.get("行") == line and x.get("始め") == start), None)
        return {"止めた": r is not None and r["区分"] == "点検していない", "区分": r["区分"] if r else None, "訳": r["訳"] if r else None}
    r = next(x for x in rows if x.get("札の番号") == key)
    out = {"止めた": r["区分"] != "確認済み", "区分": r["区分"], "訳": r["訳"]}
    if kind in ("b", "d"):
        out["食い違いで止めた"] = "が違う(本文の字" in r["訳"]
        out["抜粋"] = r.get("抜粋")
    return out


def regress():
    g = {"TR3 の要修正・精査": 0, "そのうち新しい判定で正しい数": 0, "TR0 の要確認": 0, "そのうち新しい判定で正しい数(TR0)": 0,
         "TR3 の拾わなかった字": 0, "そのうち新しい拾い方が拾う": 0}
    for n in C.NUMS:
        mat = {(m["項目"], m["期"]): m["値"] for m in load(os.path.join(TR0, "mat", n + ".json"))["項目"]}
        for r in load(os.path.join(TR3, "check", n + ".json")):
            if r["区分"] == "要確認" and not r["info"].get("held"):
                g["TR3 の要修正・精査"] += 1
                g["そのうち新しい判定で正しい数"] += J.is_correct(r["字"], r["値"], r["単位"], mat)
        for r in load(os.path.join(TR0, "check", n + ".json")):
            if r["区分"] == "要確認":
                g["TR0 の要確認"] += 1
                g["そのうち新しい判定で正しい数(TR0)"] += J.is_correct(r["字"], r["値"], r["単位"], mat)
        with open(os.path.join(TR3, "doc", n + ".md"), encoding="utf-8") as f:
            recs = N.extract_all(f.read())
        for t in load(os.path.join(TR3, "miss", n + ".json"))["拾わなかった"]:
            g["TR3 の拾わなかった字"] += 1
            g["そのうち新しい拾い方が拾う"] += any(r["行"] == t["行"] and t["始め"] <= r["始め"] < t["終わり"] for r in recs)
    return g


def dump(obj, *parts):
    p = os.path.join(*parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, ensure_ascii=False, indent=1, default=str)


def main():
    for n in C.NUMS:
        A = load(os.path.join(TR1, "A", n + ".json"))
        with open(os.path.join(OUT, "doc", n + ".md"), encoding="utf-8") as f:
            md = f.read()
        tags = load(os.path.join(OUT, "tag", n + ".json")).get("札") or []
        rows = check_doc(md, tags, A)
        title = next((l.lstrip("#").strip() for l in md.split("\n") if l.startswith("#")), "資料")
        dump(rows, OUT, "check", n + ".json")
        dump(report(n, rows, A, title), OUT, "report", n + ".html")
        res = {}
        for kind, (md2, tags2, key) in mutants(md, tags, rows, A).items():
            res[kind] = judge_mut(kind, check_doc(md2, tags2, A), key)
        dump(res, OUT, "mut", n + ".json")
        c = {k: sum(r["区分"] == k for r in rows) for k in ("確認済み", "要修正・精査", "軽量確認", "点検していない")}
        print(n, "札", len(tags), c, "| 変異", {k: v["止めた"] for k, v in res.items()})
    g = regress()
    dump(g, OUT, "regress.json")
    print(g)


if __name__ == "__main__":
    main()
