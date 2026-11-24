# -*- coding: utf-8 -*-
"""便 TR0: できた資料の数を拾い、engine(verify_external)で材料と照合して、顧客向けの点検レポートを出す(封 §3・§4)。

使い方: python3 -I check_tr0.py <audit-core の folder> <TR0 の根>
  <TR0 の根>/doc/{n}.md(書く席の資料)を点検し、check/{n}.json と report/{n}.html を書く。
  次に確認済みの数から誤りを入れた資料 mut/{n}.md(入れた誤りは mut/{n}.json)を作り、
  同じ点検で check_mut/{n}.json と report_mut/{n}.html を書く。
数を拾うのはこの script(engine の外)。照合は engine を読むだけで呼ぶ。正解は読まない。
"""
import html
import json
import os
import re
import sys

AC, ROOT = sys.argv[1], sys.argv[2]
sys.path.insert(0, AC)
sys.path.insert(0, os.path.join(AC, "core", "py"))
import audit_core as core  # noqa: E402
from adapters.xbrl import registry_setup as RS  # noqa: E402
from adapters.xbrl import verify_external as VE  # noqa: E402

NUMS = [str(i) for i in range(31, 42)]
SCALE = {"円": 1, "千円": 1000, "百万円": 1000000, "億円": 100000000}
# (字, 項目, 符号)。長い字から当てる。
ALIAS = [("親会社株主に帰属する当期純利益", "当期純利益", 1), ("親会社株主に帰属する当期純損失", "当期純利益", -1),
         ("当期純利益", "当期純利益", 1), ("当期純損失", "当期純利益", -1),
         ("営業利益", "営業利益", 1), ("営業損失", "営業利益", -1), ("経常利益", "経常利益", 1), ("経常損失", "経常利益", -1),
         ("売上高", "売上高", 1), ("営業収益", "売上高", 1), ("事業収益", "売上高", 1), ("売上収益", "売上高", 1),
         ("減価償却費", "減価償却費", 1), ("現金及び預金", "現金及び預金", 1), ("現預金", "現金及び預金", 1),
         ("流動資産合計", "流動資産合計", 1), ("流動資産", "流動資産合計", 1), ("資産合計", "資産合計", 1), ("総資産", "資産合計", 1),
         ("短期借入金", "短期借入金", 1), ("長期借入金", "長期借入金", 1), ("負債合計", "負債合計", 1), ("総負債", "負債合計", 1),
         ("純資産合計", "純資産合計", 1), ("純資産", "純資産合計", 1), ("従業員数", "期末の従業員数", 1), ("従業員", "期末の従業員数", 1)]
ALIAS.sort(key=lambda a: -len(a[0]))
NOT_BEFORE = ("1株当たり", "１株当たり", "1株あたり")
CHG = ("前期比", "前年同期比", "前期から", "前年比", "前年度比", "前期に比べ", "前期と比べ", "前期末比", "前期末から", "前期末に比べ")
NUM_RE = re.compile(r"(?P<sign>[△▲\-−])?(?P<num>\d{1,3}(?:,\d{3})+|\d+)(?:\.(?P<dec>\d+))?\s*(?P<unit>百万円|千円|億円|円|％|%|人|名)")
CELL_RE = re.compile(r"^\(?(?P<sign>[△▲\-−])?(?P<num>\d{1,3}(?:,\d{3})+|\d+)(?:\.(?P<dec>\d+))?\)?$")
CTX = {"当期": "CurrentYearDuration", "前期": "Prior1YearDuration", "当期末": "CurrentYearInstant", "前期末": "Prior1YearInstant"}
REG = RS.register_all(core.Registry.default())


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def labels_in(text):
    """文の中の項目の字の位置: [(始め, 終わり, 項目, 符号)](重ならないよう長い字から)。"""
    taken, out = [False] * len(text), []
    for word, item, sign in ALIAS:
        for m in re.finditer(re.escape(word), text):
            a, b = m.start(), m.end()
            if any(taken[a:b]) or any(text[max(0, a - 6):a].endswith(x) for x in NOT_BEFORE):
                continue
            for k in range(a, b):
                taken[k] = True
            out.append((a, b, item, sign))
    return sorted(out)


def value_of(m):
    v = float(m.group("num").replace(",", "") + ("." + m.group("dec") if m.group("dec") else ""))
    return -v if m.group("sign") else v


def periods(state, item):
    keys = state["状態"]
    stock = any(k.startswith(item + "@") and "Instant" in k for k in keys)
    return ("当期末", "前期末") if stock else ("当期", "前期")


def extract(md, state):
    """資料から数を拾う: [{行, 始め, 字, 項目, 期, 種類, 値, 単位, 符号}]。項目に結べない数は 項目 None。"""
    lines = md.split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(i)
                i += 1
            before = " ".join(lines[max(0, block[0] - 3):block[0]])
            tunit = next((u for u in ("百万円", "千円", "億円", "円") if "単位" in before and u in before), "百万円")
            head = [c.strip() for c in lines[block[0]].strip().strip("|").split("|")]
            cols = {}
            for j, c in enumerate(head):
                if "前期" in c or "前年" in c:
                    cols[j] = 1
                elif "当期" in c or "当年" in c:
                    cols[j] = 0
            for li in block[1:]:
                raw = lines[li]
                if re.match(r"^\s*\|[\s\-:|]+\|\s*$", raw):
                    continue
                cells = raw.strip().strip("|").split("|")
                labs = labels_in(cells[0]) if cells else []
                pos = raw.index("|") + 1
                for j, c in enumerate(cells):
                    start = pos + (len(c) - len(c.lstrip()))
                    pos += len(c) + 1
                    if j == 0:
                        continue
                    m = CELL_RE.match(c.strip())
                    if not m:
                        continue
                    rec = {"行": li, "始め": start, "字": c.strip(), "値": value_of(m), "単位": tunit, "種類": "single_value",
                           "場所": "表", "項目": None, "期": None}
                    if labs and j in cols:
                        item, sign = labs[0][2], labs[0][3]
                        rec["項目"], rec["期"] = item, periods(state, item)[cols[j]]
                        if sign < 0 and rec["値"] > 0:
                            rec["値"] = -rec["値"]
                    out.append(rec)
            continue
        if line.startswith("#") or "単位" in line and len(line) < 30:
            i += 1
            continue
        offset = 0
        for sent in re.split(r"(?<=。)", line):
            labs = labels_in(sent)
            prev_end = 0
            for m in NUM_RE.finditer(sent):
                if m.group("unit") == "円" and m.start("unit") > 0 and sent[m.start("unit") - 1] in "万億千":
                    continue
                lab = [x for x in labs if x[1] <= m.start()]
                rec = {"行": i, "始め": offset + m.start(), "字": m.group(0), "値": value_of(m), "単位": m.group("unit"),
                       "場所": "文", "項目": None, "期": None, "種類": None, "符号": None}
                if lab:
                    a, b, item, sign = lab[-1]
                    win = sent[max(b, prev_end):m.start()]
                    after = sent[m.end():m.end() + 8]
                    cur, pri = periods(state, item)
                    rec["項目"] = item
                    unit = m.group("unit")
                    if any(x in win for x in CHG):
                        rec["種類"] = "ratio_change" if unit in ("％", "%") else "difference"
                        rec["期"] = cur
                        rec["符号"] = -1 if "減" in after else (1 if "増" in after else None)
                    elif unit in ("％", "%"):
                        rec["種類"] = None  # 増減でない率は点検の外
                    else:
                        rec["種類"] = "single_value"
                        rec["期"] = pri if ("前期" in win or "前年" in win) else cur
                        if sign < 0 and rec["値"] > 0:
                            rec["値"] = -rec["値"]
                out.append(rec)
                prev_end = m.end()
            offset += len(sent)
        i += 1
    return out


def verify(rec, state):
    """1 つの数の照合: (区分, 説明の材料)。"""
    st = state["状態"]
    item, period, kind = rec["項目"], rec["期"], rec["種類"]
    if item is None:
        return "点検していない", {"訳": "どの項目の数かを結べませんでした"}
    if kind is None:
        return "点検していない", {"訳": "増減でない率・比率は、今の点検の外です"}
    cur_key = "%s@%s" % (item, CTX[period])
    if rec["単位"] in ("人", "名"):
        if item != "期末の従業員数":
            return "点検していない", {"訳": "人数で、項目に結べませんでした"}
        s = st.get(cur_key)
        if s is None:
            return "要確認", {"訳": "元の材料に、この期の人数がありません", "元": None}
        ok = abs(rec["値"]) == s["値"]
        return ("確認済み" if ok and s["状態"] != "未決" else ("人の判断が必要" if ok else "要確認")), {"訳": "", "元": s["値"], "keys": [cur_key]}
    if rec["単位"] == "円" or rec["単位"] not in SCALE and kind != "ratio_change":
        return "点検していない", {"訳": "円の単位の金額は、今の点検の外です"}
    if kind == "single_value":
        spec = {"kind": "single_value", "value": rec["値"], "unit": rec["単位"], "pointers": [cur_key]}
        keys = [cur_key]
    elif kind == "difference":
        pri = periods(state, item)[1]
        pri_key = "%s@%s" % (item, CTX[pri])
        val = abs(rec["値"]) * (rec["符号"] if rec["符号"] else 1)
        spec = {"kind": "difference", "value": val, "unit": rec["単位"], "pointers": [cur_key, pri_key]}
        keys = [cur_key, pri_key]
    else:
        spec = {"kind": "ratio_change", "value": abs(rec["値"]), "unit": "%", "pointers": [cur_key], "sign": rec["符号"]}
        keys = [cur_key, "%s@%s" % (item, CTX[periods(state, item)[1]])]
    out = VE.verify_external(spec, state["facts"], None, REG)
    info = {"engine": out["state"], "reason": out.get("reason"), "recomputed": out.get("recomputed"),
            "held": out.get("held"), "keys": keys}
    if out["state"] != "GROUNDED":
        return "要確認", info
    sts = [st.get(k, {}).get("状態") for k in keys]
    if any(s is None for s in sts):
        return "要確認", info
    if any(s == "未決" for s in sts):
        return "人の判断が必要", info
    return "確認済み", info


def yen_text(v, unit):
    if v is None:
        return "(無し)"
    if unit in SCALE:
        return "{:,} {}".format(int(round(v / SCALE[unit])), unit)
    return "{:,} {}".format(int(v), unit)


def what_checked(rec, info, state):
    st = state["状態"]
    parts = []
    if rec["種類"] == "difference":
        parts.append("当期と前期の元の数から計算した増減額と、資料の桁で一致")
    elif rec["種類"] == "ratio_change":
        parts.append("当期と前期の元の数から計算した増減率と一致")
    else:
        parts.append("元の数と資料の桁で一致")
    for k in info.get("keys") or []:
        s = st.get(k) or {}
        if s.get("状態") == "照合を通った" and s.get("出どころ"):
            o = s["出どころ"][0]
            parts.append("%s(%s)の元の資料: 表「%s」の行「%s」・期 %s・単位 %s・範囲 %s" % (
                s["項目"], s["期"], o.get("表"), o.get("行"), o.get("期") or "-", o.get("単位"), o.get("範囲")))
        elif s.get("状態") == "人が画面で決めた":
            parts.append("%s(%s)は、作る前の確認で人が選んだ値" % (s["項目"], s["期"]))
    return parts


def advice(rec, info, state):
    """要確認の説明: (何が起きているか, 元の数の字, 確認してください[])。"""
    st = state["状態"]
    unit = rec["単位"]
    if rec["単位"] in ("人", "名"):
        return ("資料の人数と、元の材料の人数が合いません。", yen_text(info.get("元"), "人"),
                ["資料の人数を元の人数に直すか、どの時点の人数かを確かめてください。"])
    e = info.get("engine")
    if e == "POINTER_NOT_FOUND":
        return ("この数に当たる元の数がありません(元の材料に、この項目のこの期の数がありません)。", "(無し)",
                ["どこから来た数かを確かめてください。材料に無い数なら、資料から外してください。"])
    if e == "UNPROVABLE" or info.get("held"):
        return ("元の数と照らして決めきれませんでした(同じ額が別の期にもある、など)。", "-",
                ["この数がどの期の数かを確かめてください。"])
    keys = info.get("keys") or []
    cur = st.get(keys[0], {}).get("値") if keys else None
    pri = st.get(keys[1], {}).get("値") if len(keys) > 1 else None
    tips = ["資料の数を元の数に直すか、元の数の出どころを確かめてください。"]
    if rec["種類"] == "single_value":
        orig = yen_text(cur, unit)
        if cur and unit in SCALE:
            for k2, s2 in st.items():
                if s2.get("項目") == rec["項目"] and k2 != keys[0] and s2.get("値") is not None \
                        and int(round(s2["値"] / SCALE[unit])) == int(round(abs(rec["値"]))):
                    tips.insert(0, "資料の数は %s の数と同じです。期の取り違えがないか確かめてください。" % s2["期"])
            for u2, sc in SCALE.items():
                if u2 != unit and cur and int(round(cur / sc)) == int(round(abs(rec["値"]))):
                    tips.insert(0, "数字は元の数を %s で表したものと同じです。単位の書き間違いがないか確かめてください。" % u2)
        return ("資料の数と、元の材料の数が合いません。", orig, tips)
    if rec["種類"] == "difference" and cur is not None and pri is not None:
        return ("資料の増減額と、元の数から計算した増減額が合いません。", yen_text(cur - pri, unit), tips)
    if rec["種類"] == "ratio_change" and cur is not None and pri:
        return ("資料の増減率と、元の数から計算した増減率が合いません。", "%.1f%%" % ((cur - pri) / abs(pri) * 100), tips)
    return ("資料の数と、元の材料の数が合いません。", "-", tips)


CSS = """body{font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif;color:#16233b;font-size:10pt;line-height:1.65;max-width:190mm;margin:8mm auto;padding:0 4mm}
h1{font-size:16pt;margin:0 0 2mm}h2{font-size:12.5pt;margin:7mm 0 2mm;border-bottom:.4mm solid #16233b;padding-bottom:1mm}
.lead{border-left:1.4mm solid #b7791f;background:#fbf1dc;padding:3mm 5mm;margin:3mm 0 4mm}.lead.ok{border-color:#2f855a;background:#e6f4ea}
.lead b{font-size:13pt}.counts{display:flex;gap:3mm;margin:3mm 0}.counts div{flex:1;border:.3mm solid #d9dee8;padding:2mm;text-align:center}
.counts span{display:block;font-size:17pt;font-weight:700}.card{border:.3mm solid #d9dee8;border-left:1.4mm solid #c05621;padding:2mm 4mm;margin:3mm 0;break-inside:avoid}
.card.judge{border-left-color:#6b46c1}.card h3{margin:0 0 1mm;font-size:11pt}table{border-collapse:collapse;width:100%;font-size:9pt;margin:2mm 0}
th{background:#f3f5f9;text-align:left}th,td{border:.25mm solid #d9dee8;padding:1.2mm 1.8mm;vertical-align:top}small{color:#51607a}ul{margin:1mm 0 1mm 5mm;padding:0}"""


def report(n, recs, state, title):
    cnt = {k: sum(r["区分"] == k for r in recs) for k in ("確認済み", "要確認", "人の判断が必要", "点検していない")}
    checked = cnt["確認済み"] + cnt["要確認"] + cnt["人の判断が必要"]
    b = ['<h1>資料点検レポート</h1><p>点検した資料: %s(第 %s 社)</p>' % (html.escape(title), n)]
    if cnt["要確認"] or cnt["人の判断が必要"]:
        b.append('<div class="lead"><b>点検結果: 確認が必要な数があります</b><br>要確認 %d 件・人の判断が必要 %d 件。下の「要確認事項」から順に確かめてください。</div>' % (cnt["要確認"], cnt["人の判断が必要"]))
    else:
        b.append('<div class="lead ok"><b>点検結果: 点検した数に、問題は見つかりませんでした</b><br>ただし「点検していない数」は確かめていません。</div>')
    b.append('<div class="counts">%s</div>' % "".join('<div>%s<span>%d</span></div>' % (k, v) for k, v in
             (("点検した数", checked), ("確認済み", cnt["確認済み"]), ("要確認", cnt["要確認"]),
              ("人の判断が必要", cnt["人の判断が必要"]), ("点検していない数", cnt["点検していない"]))))
    b.append("<h2>要確認事項</h2>")
    k = 0
    for r in recs:
        if r["区分"] != "要確認":
            continue
        k += 1
        what, orig, tips = advice(r, r["info"], state)
        b.append('<div class="card"><h3>%s %s(%s)― 資料の数「%s」</h3><p>%s</p><table><tr><th>資料の数</th><td>%s</td></tr><tr><th>元の数</th><td>%s</td></tr><tr><th>資料の場所</th><td>%s</td></tr></table><b>確認してください</b><ul>%s</ul></div>' % (
            "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"[k - 1] if k <= 20 else str(k), html.escape(r["項目"] or "(項目不明)"),
            html.escape(r["期"] or "-"), html.escape(r["字"]), html.escape(what), html.escape(r["字"]), html.escape(orig),
            html.escape(r["場所"] + "・" + str(r["行"] + 1) + " 行目"), "".join("<li>%s</li>" % html.escape(t) for t in tips)))
    if not k:
        b.append("<p>(ありません)</p>")
    b.append("<h2>人の判断が必要</h2>")
    j = [r for r in recs if r["区分"] == "人の判断が必要"]
    for r in j:
        b.append('<div class="card judge"><h3>%s(%s)― 資料の数「%s」</h3><p>資料の数は元の数と合っています。ただ、元の数そのものが、元の資料の中で候補が食い違い、作る前の確認でまだ決まっていません。</p><b>確認してください</b><ul><li>この項目の数として、どの時点・どの範囲の数を使うかを決めてください。</li><li>決めた数が資料の数と違えば、資料を直してください。</li></ul></div>' % (
            html.escape(r["項目"]), html.escape(r["期"]), html.escape(r["字"])))
    if not j:
        b.append("<p>(ありません)</p>")
    b.append("<h2>確認済み</h2><p>元の数と照らして一致し、元の数の出どころも確かめた数です。行ごとに、確かめたことを書いています。</p><table><tr><th>項目(期)</th><th>資料の数</th><th>確かめたこと</th></tr>")
    for r in recs:
        if r["区分"] == "確認済み":
            b.append("<tr><td>%s(%s)</td><td>%s</td><td>%s</td></tr>" % (html.escape(r["項目"]), html.escape(r["期"]), html.escape(r["字"]),
                     "<br>".join(html.escape(x) for x in what_checked(r, r["info"], state))))
    b.append("</table><h2>点検していない数</h2><p>次の数は、今の点検では確かめていません。必要なら人が確かめてください。</p><table><tr><th>資料の数</th><th>場所</th><th>訳</th></tr>")
    for r in recs:
        if r["区分"] == "点検していない":
            b.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (html.escape(r["字"]), html.escape(r["場所"] + "・" + str(r["行"] + 1) + " 行目"), html.escape(r["info"].get("訳", ""))))
    b.append("</table><h2>この点検で見ていないこと</h2><ul><li>元の材料の値そのものの正しさ(作る前の照合と確認で決めた値を正としています)。</li><li>資料の文の言い回しや、数以外の内容。</li><li>上の「点検していない数」。</li></ul>")
    return '<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>資料点検レポート 第%s社</title><style>%s</style></head><body>%s</body></html>' % (n, CSS, "\n".join(b))


def check(n, md, state, out_json, out_html):
    recs = extract(md, state)
    for r in recs:
        r["区分"], r["info"] = verify(r, state)
    title = next((l.lstrip("#").strip() for l in md.split("\n") if l.startswith("#")), "資料")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    os.makedirs(os.path.dirname(out_html), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1, default=str)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(report(n, recs, state, title))
    return recs


def bump(tok):
    """字の中の最後の数字を 1 つ変える(9 は 8 に)。"""
    for i in range(len(tok) - 1, -1, -1):
        if tok[i].isdigit():
            d = int(tok[i])
            return tok[:i] + str(d + 1 if d < 9 else d - 1) + tok[i + 1:]
    return tok


def mutate(md, recs, state):
    """封 §4 の (a)〜(d)。確認済みの数から番号の若い順に選ぶ。"""
    lines = md.split("\n")
    ok = sorted([r for r in recs if r["区分"] == "確認済み" and r["単位"] not in ("人", "名")], key=lambda r: (r["行"], r["始め"]))
    table = [r for r in ok if r["場所"] == "表"]
    sent = [r for r in ok if r["場所"] == "文"]
    used, muts = set(), []

    def take(pool, cond=lambda r: True):
        for r in pool:
            if (r["行"], r["始め"]) not in used and cond(r):
                used.add((r["行"], r["始め"]))
                return r
        return None

    def put(r, new, kind):
        line = lines[r["行"]]
        old = r["字"]
        assert line[r["始め"]:r["始め"] + len(old)] == old, (line, r["始め"], old)
        lines[r["行"]] = line[:r["始め"]] + new + line[r["始め"] + len(old):]
        muts.append({"種類": kind, "行": r["行"], "始め": r["始め"], "元の字": old, "入れた字": new, "項目": r["項目"], "期": r["期"]})

    r = take(table)
    if r:
        put(r, bump(r["字"]), "a")

    def has_prior(r):
        if r["期"] not in ("当期", "当期末"):
            return False
        k = "%s@%s" % (r["項目"], CTX[periods(state, r["項目"])[1]])
        s = state["状態"].get(k)
        return s is not None and int(round(s["値"] / SCALE[r["単位"]])) != int(round(abs(r["値"])))
    r = take(table, has_prior)
    if r:
        s = state["状態"]["%s@%s" % (r["項目"], CTX[periods(state, r["項目"])[1]])]
        v = int(round(s["値"] / SCALE[r["単位"]]))
        put(r, ("△" if v < 0 else "") + "{:,}".format(abs(v)), "b")
    else:
        r = take(table)
        if r:
            put(r, bump(r["字"]), "a")
    r = take(sent, lambda r: r["種類"] in ("single_value", "difference"))
    if r:
        put(r, bump(r["字"]), "c")
    else:
        r = take(table)
        if r:
            put(r, bump(r["字"]), "a")
    r = take(sent, lambda r: r["単位"] == "百万円")
    if r:
        put(r, r["字"].replace("百万円", "千円"), "d")
    else:
        r = take(table)
        if r:
            put(r, bump(r["字"]), "a")
    return "\n".join(lines), muts


def main():
    for n in NUMS:
        state = load(os.path.join(ROOT, "state", n + ".json"))
        with open(os.path.join(ROOT, "doc", n + ".md"), encoding="utf-8") as f:
            md = f.read()
        recs = check(n, md, state, os.path.join(ROOT, "check", n + ".json"), os.path.join(ROOT, "report", n + ".html"))
        mmd, muts = mutate(md, recs, state)
        os.makedirs(os.path.join(ROOT, "mut"), exist_ok=True)
        with open(os.path.join(ROOT, "mut", n + ".md"), "w", encoding="utf-8") as f:
            f.write(mmd)
        with open(os.path.join(ROOT, "mut", n + ".json"), "w", encoding="utf-8") as f:
            json.dump(muts, f, ensure_ascii=False, indent=1)
        mrecs = check(n, mmd, state, os.path.join(ROOT, "check_mut", n + ".json"), os.path.join(ROOT, "report_mut", n + ".html"))
        c = lambda rs, k: sum(r["区分"] == k for r in rs)
        print(n, "拾った", len(recs), "確認済み", c(recs, "確認済み"), "要確認", c(recs, "要確認"), "判断", c(recs, "人の判断が必要"),
              "外", c(recs, "点検していない"), "| 入れた", len(muts), "要確認", c(mrecs, "要確認"))


if __name__ == "__main__":
    main()
