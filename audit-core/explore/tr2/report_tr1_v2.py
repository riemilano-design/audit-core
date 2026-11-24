# -*- coding: utf-8 -*-
"""便 TR2 §6: TR1 の点検レポートを、要確認を「要修正・精査」と「軽量確認」に分けて作り直す(人間の決め 2026-11-25)。

使い方: python3 -I report_tr1_v2.py <audit-core の folder> <TR0 の根> <TR1 の根> <出力の folder>
TR1 の check_A/{n}.json と A/{n}.json を読み、<出力>/report_v2/{n}.html と <出力>/report_v2.json(数だけ)を書く。
engine は読むだけ(holds の同額の兄弟の関数で、同じ額の在る枠を探す)。拾い方と照合は TR1 のまま(やり直さない)。
"""
import html
import json
import os
import sys

AC, TR0, TR1, OUT = sys.argv[1:5]
sys.argv = [sys.argv[0], AC, TR0, TR1]
sys.path.insert(0, os.path.join(AC, "explore", "tr1"))
import check_tr1 as C  # noqa: E402  (TR1 の点検レポートの部品を使う)
from adapters.xbrl import holds as H  # noqa: E402  (読むだけ)
from adapters.xbrl import verify_external as VE  # noqa: E402  (読むだけ)

MEMBER = {"NonConsolidatedMember": "単体", "RetainedEarningsMember": "株主資本等変動計算書の利益剰余金の列",
          "ShareholdersEquityMember": "株主資本等変動計算書の株主資本の列",
          "RetainedEarningsBroughtForwardMember": "株主資本等変動計算書の繰越利益剰余金の列",
          "ReportableSegmentsMember": "セグメント情報の報告セグメントの列", "TotalOfReportableSegmentsAndOthersMember": "セグメント情報の合計の列"}


def frame_word(ctx):
    per, _, dim = ctx.partition("_")
    p = C.PERIOD_WORD.get(per, per)
    if not dim:
        return p + "・連結"
    parts = [m for m in dim.split("_") if m.endswith("Member")]
    return p + "・" + "・".join(MEMBER.get(m.split(":")[-1], m.split(":")[-1]) for m in parts)


def siblings(rec, A):
    """保留になった行の照合先の fact と、engine の規則で同じ額とされる兄弟の枠の字。"""
    keys = rec["info"].get("keys") or []
    if not keys or keys[0] not in A["map"]:
        return None, []
    p = A["map"][keys[0]]["pointer"]
    name, _, ctx = p.partition("@")
    f = next((x for x in A["facts"] if x["name"] == name and x["context"] == ctx), None)
    if f is None:
        return None, []
    unit = "%" if rec["種類"] == "ratio_change" else rec["単位"]
    tol = VE.tol_of(unit)
    sib = H.dimension_siblings(A["facts"], f, tol) + H.period_siblings(A["facts"], f, tol)
    words = []
    for g in sib:
        w = frame_word(g["context"])
        if w not in words:
            words.append(w)
    return A["map"][keys[0]], words


LIMITS = ("<h2>この点検の限界</h2><ul>"
          "<li>元の XBRL の値との差が、資料の 1 桁(例: 百万円の資料なら 1 百万円)より小さい数は、照合が通ります。資料の桁より細かい誤りは見ていません(機械で入れた誤り 44 のうち、1 桁を変えた 3 がこの幅で通りました。便 TR1)。</li>"
          "<li>円の単位の金額(百万円・千円でなく円で書いた数)は、照合していません。「点検していない数」に入ります。</li>"
          "<li>提出された XBRL そのものが、会社の帳簿と合っているかは見ていません。</li></ul>")


def report(n, recs, A, title):
    fix = [r for r in recs if r["区分"] == "要確認" and not r["info"].get("held")]
    light = [r for r in recs if r["区分"] == "要確認" and r["info"].get("held")]
    cnt = {"確認済み": sum(r["区分"] == "確認済み" for r in recs), "要修正・精査": len(fix), "軽量確認": len(light),
           "人の判断が必要": sum(r["区分"] == "人の判断が必要" for r in recs), "点検していない": sum(r["区分"] == "点検していない" for r in recs)}
    b = ['<h1>資料点検レポート</h1><p>点検した資料: %s</p>' % html.escape(title)]
    b.append('<p class="basis">照合の基準: 提出された有価証券報告書の XBRL(生のデータを機械で読んだもの。基準を作るのに AI は使っていません)。範囲: %s(作る前の確認で人が決めたもの)。</p>' % html.escape(A.get("範囲") or "未定"))
    if fix or cnt["人の判断が必要"]:
        b.append('<div class="lead"><b>点検結果: 直すか精査が必要な数があります</b><br>要修正・精査 %d 件・軽量確認 %d 件・人の判断が必要 %d 件。「要修正・精査」から確かめてください。</div>' % (len(fix), len(light), cnt["人の判断が必要"]))
    elif light:
        b.append('<div class="lead ok"><b>点検結果: 元と合わない数は見つかりませんでした</b><br>軽量確認 %d 件(数は合っているが、同じ額が別の枠にも在るもの)を目で確かめてください。</div>' % len(light))
    else:
        b.append('<div class="lead ok"><b>点検結果: 点検した数に、問題は見つかりませんでした</b></div>')
    b.append('<div class="counts">%s</div>' % "".join('<div>%s<span>%d</span></div>' % (k, v) for k, v in cnt.items()))
    b.append("<h2>要修正・精査</h2><p>元の XBRL の数と合わないか、元の数が見つからない数です。</p>")
    for k, r in enumerate(fix, 1):
        what, orig, tips, srcs = C.advice(r, r["info"], A)
        kind = {"difference": "増減額", "ratio_change": "増減率"}.get(r["種類"], "")
        b.append('<div class="card"><h3>%s %s(%s%s)― 資料の数「%s」</h3><p>%s</p><table><tr><th>資料の数</th><td>%s</td></tr><tr><th>元の数</th><td>%s</td></tr><tr><th>元の数の出どころ</th><td>%s</td></tr><tr><th>資料の場所</th><td>%s</td></tr></table><b>確認してください</b><ul>%s</ul></div>' % (
            C.MARK[k - 1] if k <= 20 else str(k), html.escape(r["項目"]), html.escape(r["期"] or "-"), "・" + kind if kind else "",
            html.escape(r["字"]), html.escape(what), html.escape(r["字"]), html.escape(orig), "<br>".join(html.escape(s) for s in srcs) or "-",
            html.escape(r["場所"] + "・" + str(r["行"] + 1) + " 行目"), "".join("<li>%s</li>" % html.escape(t) for t in tips)))
    if not fix:
        b.append("<p>(ありません)</p>")
    b.append("<h2>軽量確認</h2><p>資料の数は、照合先の XBRL の数と一致しています。ただし、同じ額が別の期・別の枠にも在るため、機械だけでは「どの枠の数か」を決めきれません。照合先の枠が、資料で言いたい数の枠と同じかを目で確かめてください。</p>")
    if light:
        b.append("<table><tr><th>項目(期)</th><th>資料の数</th><th>照合先(一致した数)</th><th>同じ額の在る枠</th><th>資料の場所</th></tr>")
        for r in light:
            e, words = siblings(r, A)
            kind = {"difference": "・増減額", "ratio_change": "・増減率"}.get(r["種類"], "")
            b.append("<tr><td>%s(%s%s)</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                html.escape(r["項目"]), html.escape(r["期"]), kind, html.escape(r["字"]), html.escape(C.source_line(e)) if e else "-",
                html.escape("・".join(words) if len(words) < 2 else " / ".join(words)) if words else "-",
                html.escape(r["場所"] + "・" + str(r["行"] + 1) + " 行目")))
        b.append("</table>")
    else:
        b.append("<p>(ありません)</p>")
    b.append("<h2>人の判断が必要</h2>")
    j = [r for r in recs if r["区分"] == "人の判断が必要"]
    b.extend('<div class="card"><h3>%s ― 資料の数「%s」</h3><p>%s</p></div>' % (html.escape(r["項目"]), html.escape(r["字"]), html.escape(r["info"].get("訳", ""))) for r in j)
    if not j:
        b.append("<p>(ありません)</p>")
    b.append("<h2>確認済み</h2><p>元の XBRL の数と照らして一致した数です。行ごとに、照らした XBRL の要素・期・範囲・値・開示の精度を書いています。</p>")
    for place, name in (("表", "資料の表の数"), ("文", "資料の文の中の数")):
        rows = [r for r in recs if r["区分"] == "確認済み" and r["場所"] == place]
        if not rows:
            continue
        b.append("<h3>%s(%d)</h3><table><tr><th>項目(期)</th><th>資料の数</th><th>確かめたこと</th></tr>" % (name, len(rows)))
        for r in rows:
            kind = {"difference": "・増減額", "ratio_change": "・増減率"}.get(r["種類"], "")
            b.append("<tr><td>%s(%s%s)</td><td>%s</td><td>%s</td></tr>" % (html.escape(r["項目"]), html.escape(r["期"]), kind, html.escape(r["字"]),
                     "<br>".join(html.escape(x) for x in C.checked_text(r, r["info"], A))))
        b.append("</table>")
    b.append("<h2>点検していない数</h2><table><tr><th>資料の数</th><th>場所</th><th>訳</th></tr>")
    for r in recs:
        if r["区分"] == "点検していない":
            b.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (html.escape(r["字"]), html.escape(r["場所"] + "・" + str(r["行"] + 1) + " 行目"), html.escape(r["info"].get("訳", ""))))
    b.append("</table>" + LIMITS)
    return '<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>資料点検レポート 第%s社</title><style>%s</style></head><body>%s</body></html>' % (n, C.CSS, "\n".join(b)), cnt


def main():
    total = {"要修正・精査": 0, "軽量確認": 0, "軽量確認で同じ額の枠の名を欠く": 0, "軽量確認で照合先の一次ソースを欠く": 0}
    os.makedirs(os.path.join(OUT, "report_v2"), exist_ok=True)
    for n in C.NUMS:
        A = C.load(os.path.join(TR1, "A", n + ".json"))
        recs = C.load(os.path.join(TR1, "check_A", n + ".json"))
        with open(os.path.join(TR1, "doc", n + ".md"), encoding="utf-8") as f:
            title = next((l.lstrip("#").strip() for l in f.read().split("\n") if l.startswith("#")), "資料")
        h, cnt = report(n, recs, A, title)
        with open(os.path.join(OUT, "report_v2", n + ".html"), "w", encoding="utf-8") as f:
            f.write(h)
        total["要修正・精査"] += cnt["要修正・精査"]
        total["軽量確認"] += cnt["軽量確認"]
        for r in recs:
            if r["区分"] == "要確認" and r["info"].get("held"):
                e, words = siblings(r, A)
                total["軽量確認で同じ額の枠の名を欠く"] += not words
                total["軽量確認で照合先の一次ソースを欠く"] += e is None
    with open(os.path.join(OUT, "report_v2.json"), "w", encoding="utf-8") as f:
        json.dump(total, f, ensure_ascii=False, indent=1)
    print(total)


if __name__ == "__main__":
    main()
