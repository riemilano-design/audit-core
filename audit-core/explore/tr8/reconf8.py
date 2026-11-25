# -*- coding: utf-8 -*-
"""便 TR8: TR6 の確定し直しと TR7 の部分の読みの小さな穴を直す(封 §2)。TR6・TR7 の file を変えずに上に足す。AI を使わない。

- diff8: TR6 の diff に、(a) 同じ見出しの列の追加(使う列と同じ字の列が足された。案を出さない)、
  (b) 行の追加に「入りうる項目」(その表を使う項目)、(c) 行の字の変更に「確定した時の字の行が今回も在るか」、
  (d) シートの名の変更に「今回の file のシートの一覧」を足す。
- waiting8: TR7 の待たせる規則に P5(同じ見出しの列の追加は、その字の列を使う項目を待たせる)を足す。
- screen8: TR6 の画面の穴を直した画面。前後の行に列の見出しの行を付ける。単位の変更・列の変化にも表の頭の 3 行を出す。
  行の追加の影響は「未決」と入りうる項目。先に読めた数(部分の読み)を出す。
"""
import html

import ledger_tr2 as L
import partial_tr7 as P
import reconf_tr6 as R


def _cols_used(decided, s):
    return {c["列"] for it in decided["項目"] for c in it.get("成分") or [] if c["シート"] == s}


def diff8(decided, ledger, book):
    changes = R.diff(decided, ledger, book)
    _, cols_use, sheet_use = R._uses(decided)
    rename = {ch["シート"]: ch["今"] for ch in changes if ch["種類"] == "シートの名の変更"}
    for ch in changes:
        s = ch["シート"]
        s1 = rename.get(s, s)
        if ch["種類"] == "列の追加" and ch["今"] in _cols_used(decided, s):
            ch.update({"種類": "同じ見出しの列の追加", "案": None, "影響": sorted(cols_use.get((s, ch["今"]), ()))})
        elif ch["種類"] == "行の追加":
            ch["入りうる項目"] = sorted(sheet_use.get(s, ()))
        elif ch["種類"] == "行の字の変更":
            cfg = decided["シート"].get(s)
            lay = L.layout(book[s1], cfg) if (cfg and s1 in book) else None
            ch["前の字が今も在る"] = bool(lay) and any(lab == ch["前"] for _, lab, _ in lay[2])
        elif ch["種類"] == "シートの名の変更":
            ch["今回のシート"] = sorted(book)
    return changes


def waiting8(decided, changes, book):
    w = P.waiting(decided, changes, book)
    for ch in changes:
        if ch["種類"] == "同じ見出しの列の追加":
            w |= set(ch["影響"])
    return w


def _table(decided, book, sheet, rename, label=None, k=2):
    """列の見出しの行 + (label の前後 k 行 か、頭の 3 行)。"""
    s1 = rename.get(sheet, sheet)
    cfg = decided["シート"].get(sheet)
    if not cfg or s1 not in book:
        return ""
    lay = L.layout(book[s1], cfg)
    if lay is None:
        return ""
    h, lc, rws = lay
    if label is not None:
        idx = [n for n, (_, lab, _) in enumerate(rws) if lab == label]
        if not idx:
            return ""
        part = rws[max(0, idx[0] - k): idx[0] + k + 1]
    else:
        part = rws[:3]
    head = "<tr>%s</tr>" % "".join("<th>%s</th>" % html.escape(L.text(x)) for x in book[s1][h])
    body = "".join("<tr%s>%s</tr>" % (' class="me"' if (label is not None and lab == label) else "",
                                      "".join("<td>%s</td>" % html.escape(L.text(x)) for x in book[s1][i])) for i, lab, _ in part)
    return "<table class=ctx>%s%s</table>" % (head, body)


def plan_text(ch):
    a = ch["案"]
    if a is None:
        return "(案なし。決めてください)"
    if "対応" in a:
        return "「%s」を「%s」として読む" % (ch["前"], a["対応"])
    if "単位" in a:
        return "単位を %s にする" % a["単位"]
    return "台帳は変えない(了承)"


def note(ch):
    k = ch["種類"]
    if k == "行の追加":
        return "影響する項目: 未決(決めた項目に入る)。この表を使う項目: %s" % ("・".join(ch.get("入りうる項目") or []) or "なし")
    if k == "行の字の変更":
        return "確定した時の字「%s」の行は、今回の file に%s" % (ch["前"], "も在ります" if ch.get("前の字が今も在る") else "は在りません")
    if k == "シートの名の変更":
        return "今回の file のシート: %s(確定した時の名「%s」は%s)" % (
            "・".join(ch.get("今回のシート") or []), ch["前"], "在ります" if ch["前"] in (ch.get("今回のシート") or []) else "在りません")
    if k == "同じ見出しの列の追加":
        return "同じ見出しの列が 2 本になりました。どちらを読むか機械は決めません"
    return ""


def screen8(n, sk, changes, decided, book, plan_read, early):
    rename = {ch["シート"]: ch["案"]["対応"] for ch in changes if ch["種類"] == "シートの名の変更" and ch["案"]}
    rows = []
    for ch in changes:
        if ch["種類"].startswith("行の"):
            lab = ch["今"] if ch["今"] != "(無い)" else None
            ctx = _table(decided, book, ch["シート"], rename, lab) if lab else ""
        elif ch["種類"] in ("単位の変更", "頭の行の字の変更") or ch["種類"].startswith("列の") or ch["種類"] == "同じ見出しの列の追加":
            ctx = _table(decided, book, ch["シート"], rename)
        else:
            ctx = ""
        aff = "未決" if ch["種類"] == "行の追加" else ("・".join(ch["影響"]) or "なし")
        rows.append("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            ch["番号"], html.escape(ch["シート"]), html.escape(ch["種類"]), html.escape(str(ch["前"])), html.escape(str(ch["今"])),
            html.escape(aff), html.escape(plan_text(ch)), html.escape(note(ch)), ctx))
    if plan_read is None:
        pv = "<p>案だけでは読めません(決めていない所が在ります)。</p>"
    else:
        pv = "<table><tr><th>項目@期</th><th>案を当てて今回の file から読んだ値(円)</th></tr>" + "".join(
            "<tr><td>%s</td><td style='text-align:right'>%s</td></tr>" % (html.escape(k), "{:,}".format(v)) for k, v in plan_read.items()) + "</table>"
    ev = ("<table><tr><th>項目@期</th><th>値(円)</th></tr>" + "".join(
        "<tr><td>%s</td><td style='text-align:right'>%s</td></tr>" % (html.escape(k), "{:,}".format(v)) for k, v in sorted(early.items()))
          + "</table>") if early else "<p>ありません(変わった所が全部の項目に触れています)。</p>"
    return ('<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>台帳の確定し直し</title>'
            '<style>body{font-family:sans-serif;font-size:10pt;max-width:280mm;margin:8mm auto}table{border-collapse:collapse;margin:4px 0}'
            'td,th{border:1px solid #ccd;padding:2px 6px;vertical-align:top}th{background:#f3f5f9}.ctx td,.ctx th{border:1px solid #eee;font-size:9pt}'
            '.me td{background:#fff3c4}.lead{border-left:5px solid #b7791f;background:#fbf1dc;padding:8px 12px}</style></head><body>'
            '<h1>台帳の確定し直し(第 %d 社・画面 %s)</h1>'
            '<div class="lead">今回の file は、確定した台帳と様式が違うため、変わった所に触れる数を読まずに止めました。変わった所は <b>%d か所</b>です。'
            '所ごとに機械の案を見て、案のままでよいか、直すかを決めてください。案の無い所は決めてください。</div>'
            '<h2>変わった所</h2><table><tr><th>番号</th><th>シート</th><th>変わったもの</th><th>確定した時の字</th><th>今回の字</th>'
            '<th>影響する項目</th><th>機械の案</th><th>補足</th><th>今回の file の表(列の見出しつき。黄色がその行)</th></tr>%s</table>'
            '<h2>変わった所に触れないので先に読んだ数</h2>%s'
            '<h2>案を当てた時の値</h2>%s</body></html>') % (n, sk, len(changes), "".join(rows), ev, pv)
