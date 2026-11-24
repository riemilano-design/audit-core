# -*- coding: utf-8 -*-
"""便 TR1: 資料の数を拾い、基準 A(生の XBRL)と基準 B(AI の取り出した材料)で照合し、顧客向けの点検レポート(基準 A)を出す(封 §3)。

使い方: python3 -I check_tr1.py <audit-core の folder> <TR0 の根> <TR1 の根>
  新しい資料 <TR1>/doc/{n}.md を基準 A で check_A/・report_A/、基準 B で check_B/ に。
  基準 A で確認済みの数から誤りを入れた mut/{n}.md を作り、基準 A で check_mut/・report_mut/ に。
  TR0 の資料 <TR0>/doc/{n}.md を基準 A で check_tr0docs/ に。
数を拾うのはこの script(engine の外。AI を使わない)。照合は engine を読むだけで呼ぶ。正解は読まない。
"""
import html
import json
import os
import re
import sys

AC, TR0, ROOT = sys.argv[1:4]
sys.path.insert(0, AC)
sys.path.insert(0, os.path.join(AC, "core", "py"))
import audit_core as core  # noqa: E402
from adapters.xbrl import registry_setup as RS  # noqa: E402
from adapters.xbrl import verify_external as VE  # noqa: E402

NUMS = [str(i) for i in range(31, 42)]
SCALE = {"円": 1, "千円": 1000, "百万円": 1000000, "億円": 100000000}
# (字, 項目, 符号)。符号 0 は「損益」: 後ろの「の損失」で負にする。
ALIAS = [("親会社株主に帰属する当期純利益", "当期純利益", 1), ("親会社株主に帰属する当期純損失", "当期純利益", -1),
         ("親会社株主に帰属する当期純損益", "当期純利益", 0),
         ("当期純利益", "当期純利益", 1), ("当期純損失", "当期純利益", -1), ("当期純損益", "当期純利益", 0),
         ("営業利益", "営業利益", 1), ("営業損失", "営業利益", -1), ("営業損益", "営業利益", 0),
         ("経常利益", "経常利益", 1), ("経常損失", "経常利益", -1), ("経常損益", "経常利益", 0),
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
PERIOD_WORD = {"CurrentYearDuration": "当期", "Prior1YearDuration": "前期", "CurrentYearInstant": "当期末",
               "Prior1YearInstant": "前期末", "Prior2YearDuration": "前々期", "Prior2YearInstant": "前々期末"}
REG = RS.register_all(core.Registry.default())
STOCK = ("現金及び預金", "流動資産合計", "資産合計", "短期借入金", "長期借入金", "負債合計", "純資産合計", "期末の従業員数")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def periods(item):
    return ("当期末", "前期末") if item in STOCK else ("当期", "前期")


def labels_in(text):
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


def direction(text, loss):
    """節の中の増減の字で符号を決める(最初に出た字)。損失の拡大は負、縮小は正。"""
    best = None
    for w, s in (("拡大", -1 if loss else 1), ("縮小", 1 if loss else -1), ("改善", 1), ("悪化", -1), ("増", 1), ("減", -1)):
        i = text.find(w)
        if i >= 0 and (best is None or i < best[0]):
            best = (i, s)
    return best[1] if best else None


def extract(md):
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
                           "場所": "表", "項目": None, "期": None, "符号": None}
                    if labs and j in cols:
                        item, sign = labs[0][2], labs[0][3]
                        rec["項目"], rec["期"] = item, periods(item)[cols[j]]
                        if sign < 0 and rec["値"] > 0:
                            rec["値"] = -rec["値"]
                    out.append(rec)
            continue
        if line.startswith("#") or ("単位" in line and len(line) < 30):
            i += 1
            continue
        offset = 0
        for sent in re.split(r"(?<=。)", line):
            labs = labels_in(sent)
            nums = [m for m in NUM_RE.finditer(sent)
                    if not (m.group("unit") == "円" and m.start("unit") > 0 and sent[m.start("unit") - 1] in "万億千")]
            prev, prev_end = None, 0
            for k, m in enumerate(nums):
                nxt = nums[k + 1].start() if k + 1 < len(nums) else len(sent)
                lab = [x for x in labs if x[1] <= m.start()]
                rec = {"行": i, "始め": offset + m.start(), "字": m.group(0), "値": value_of(m), "単位": m.group("unit"),
                       "場所": "文", "項目": None, "期": None, "種類": None, "符号": None}
                if lab:
                    a, b, item, sign = lab[-1]
                    if prev is not None and prev.get("項目") != item:
                        prev = None
                    win = sent[max(b, prev_end):m.start()]
                    after = sent[m.end():m.end() + 25]
                    near = sent[m.end():nxt]
                    loss = sign <= 0 or "損失" in win or "損失" in near
                    cur, pri = periods(item)
                    unit = m.group("unit")
                    rec["項目"] = item
                    if unit in ("％", "%"):
                        if any(x in win for x in CHG) or (prev is not None and prev["種類"] == "difference"
                                                         and re.fullmatch(r"\s*[（(]\s*", win)):
                            rec["種類"], rec["期"], rec["符号"] = "ratio_change", cur, direction(after, loss)
                    elif any(x in win for x in CHG) or ("損失額が" in win or "損失が" in win) \
                            or (prev is not None and prev["種類"] == "single_value" and prev["期"] == pri and "から" in win):
                        rec["種類"], rec["期"], rec["符号"] = "difference", cur, direction(after, loss)
                    else:
                        rec["種類"] = "single_value"
                        rec["期"] = pri if ("前期" in win or "前年" in win) else cur
                        if sign < 0 and rec["値"] > 0:
                            rec["値"] = -rec["値"]
                        if sign == 0 and rec["値"] > 0 and "損失" in near[:8]:
                            rec["値"] = -rec["値"]
                    prev = rec
                out.append(rec)
                prev_end = m.end()
            offset += len(sent)
        i += 1
    return out


# ---------------------------------------------------------------- 照合
def spec_of(rec, ptr):
    """rec と鍵 → 参照先の写像から、verify_external の spec と使った鍵。鍵が無ければ None。"""
    item, kind = rec["項目"], rec["種類"]
    cur, pri = periods(item)
    k_cur, k_pri = "%s@%s" % (item, CTX[rec["期"]]), "%s@%s" % (item, CTX[pri])
    if kind == "single_value":
        if k_cur not in ptr:
            return None, [k_cur]
        return {"kind": "single_value", "value": rec["値"], "unit": rec["単位"], "pointers": [ptr[k_cur]]}, [k_cur]
    k_cur = "%s@%s" % (item, CTX[cur])
    if kind == "difference":
        if k_cur not in ptr or k_pri not in ptr:
            return None, [k_cur, k_pri]
        val = abs(rec["値"]) * (rec["符号"] if rec["符号"] else 1)
        return {"kind": "difference", "value": val, "unit": rec["単位"], "pointers": [ptr[k_cur], ptr[k_pri]]}, [k_cur, k_pri]
    if k_cur not in ptr:
        return None, [k_cur, k_pri]
    return {"kind": "ratio_change", "value": abs(rec["値"]), "unit": "%", "pointers": [ptr[k_cur]], "sign": rec["符号"]}, [k_cur, k_pri]


def verify(rec, basis, kind_of_basis):
    """(区分, info)。basis は A なら {"map","facts","範囲"}、B なら TR0 の state。"""
    if rec["項目"] is None:
        return "点検していない", {"訳": "どの項目の数かを結べませんでした"}
    if rec["種類"] is None:
        return "点検していない", {"訳": "増減率でない率・比率は、今の点検の外です"}
    if rec["単位"] == "円":
        return "点検していない", {"訳": "円の単位の金額は、今の点検の外です"}
    if kind_of_basis == "A":
        ptr = {k: v["pointer"] for k, v in basis["map"].items()}
        vals = {k: v["値"] for k, v in basis["map"].items()}
        facts = basis["facts"]
        if basis.get("範囲") not in ("連結", "単体"):
            return "人の判断が必要", {"訳": "資料を連結と単体のどちらで作るかが決まっていません"}
    else:
        ptr = {k: k for k in basis["状態"]}
        vals = {k: v["値"] for k, v in basis["状態"].items()}
        facts = basis["facts"]
    if rec["単位"] in ("人", "名"):
        if rec["項目"] != "期末の従業員数":
            return "点検していない", {"訳": "人数で、項目に結べませんでした"}
        k = "%s@%s" % (rec["項目"], CTX[rec["期"]])
        if k not in vals:
            return "点検していない", {"訳": "元の XBRL に、この項目の要素がありません", "keys": [k]}
        ok = abs(rec["値"]) == vals[k]
        return ("確認済み" if ok else "要確認"), {"engine": "GROUNDED" if ok else "VALUE_MISMATCH", "keys": [k], "人数": True}
    spec, keys = spec_of(rec, ptr)
    if spec is None:
        if kind_of_basis == "A":
            return "点検していない", {"訳": "元の XBRL に、この項目の要素がありません", "keys": keys}
        return "要確認", {"engine": "POINTER_NOT_FOUND", "keys": keys}
    out = VE.verify_external(spec, facts, None, REG)
    info = {"engine": out["state"], "reason": out.get("reason"), "held": out.get("held"), "keys": keys,
            "derived": list(out.get("derived_pointers") or [])}
    if out["state"] != "GROUNDED":
        return "要確認", info
    if kind_of_basis == "B":
        sts = [basis["状態"].get(k, {}).get("状態") for k in keys]
        if any(s == "未決" for s in sts):
            return "人の判断が必要", info
    return "確認済み", info


# ---------------------------------------------------------------- 点検レポート(顧客向け・基準 A)
def prec_word(dec):
    try:
        d = int(dec)
    except (TypeError, ValueError):
        return "記載なし"
    return {-6: "百万円単位", -3: "千円単位", 0: "円単位"}.get(d, "10 の %d 乗の単位" % (-d))


def scope_word(ctx):
    return "単体" if "NonConsolidated" in ctx else "連結"


def source_line(entry):
    return "XBRL の要素「%s」・%s・%s・値 %s 円・開示の精度 %s" % (
        entry["要素"], PERIOD_WORD.get(entry["枠"].split("_")[0], entry["枠"]), scope_word(entry["枠"]),
        "{:,}".format(int(round(entry["値"]))), prec_word(entry.get("decimals")))


def fact_by_pointer(facts, p):
    name, _, ctx = p.partition("@")
    f = next((x for x in facts if x["name"] == name and x["context"] == ctx), None)
    if f is None:
        return None
    return {"要素": name.split(":")[-1], "枠": ctx, "値": f["value"], "decimals": f.get("decimals")}


def both_units(v, dec, unit):
    pw = {-6: "百万円", -3: "千円", 0: "円"}
    try:
        u0 = pw.get(int(dec), "円")
    except (TypeError, ValueError):
        u0 = "円"
    a = "{:,} {}".format(int(round(v / SCALE[u0])), u0)
    b = "{:,} {}".format(int(round(v / SCALE[unit])), unit) if unit in SCALE else ""
    return a if (not b or u0 == unit) else "%s(資料の単位では %s)" % (a, b)


def advice(rec, info, A):
    m, facts = A["map"], A["facts"]
    if info.get("人数"):
        k = info["keys"][0]
        return ("資料の人数と、元の XBRL の人数が合いません。", "{:,} 人".format(int(m[k]["値"])),
                ["資料の人数を元の人数に直すか、どの時点・どの範囲の人数かを確かめてください。"], [source_line(m[k])])
    e = info.get("engine")
    keys = info.get("keys") or []
    if e == "POINTER_NOT_FOUND":
        return ("この数に当たる元の数が XBRL にありません。", "(無し)", ["どこから来た数かを確かめてください。"], [])
    if e == "UNPROVABLE" or info.get("held"):
        return ("元の XBRL と照らして決めきれませんでした(同じ額が別の期・範囲にもある、など)。", "-",
                ["この数がどの期・どの範囲の数かを確かめてください。"], [source_line(m[k]) for k in keys if k in m])
    unit = rec["単位"]
    cur = m.get(keys[0]) if keys else None
    pri = m.get(keys[1]) if len(keys) > 1 else None
    tips, srcs = [], [source_line(x) for x in (cur, pri) if x]
    got = round(abs(rec["値"]))
    if rec["種類"] == "single_value" and cur and unit in SCALE:
        orig = both_units(cur["値"], cur.get("decimals"), unit)
        if pri is None:
            k2 = "%s@%s" % (rec["項目"], CTX[periods(rec["項目"])[1]])
            pri = m.get(k2)
        if pri and round(abs(cur["値"] - pri["値"]) / SCALE[unit]) == got:
            tips.append("資料の数は、前期からの増減額と同じです。増減額のつもりなら、増減額と分かる書き方か確かめてください。")
        el = cur["要素"]
        for f in facts:
            if f["name"].split(":")[-1] == el and f["context"] != cur["枠"] and round(abs(f["value"]) / SCALE[unit]) == got:
                tips.append("資料の数は、XBRL の同じ要素の「%s・%s」の数と同じです。期か範囲の取り違えがないか確かめてください。" % (
                    PERIOD_WORD.get(f["context"].split("_")[0], f["context"].split("_")[0]), scope_word(f["context"])))
                break
        for u2, sc in SCALE.items():
            if u2 != unit and round(abs(cur["値"]) / sc) == got:
                tips.append("数字は元の数を %s で表したものと同じです。単位の書き間違いがないか確かめてください。" % u2)
        tips.append("資料の数を元の数に直すか、資料の数の出どころを確かめてください。")
        return ("資料の数と、元の XBRL の数が合いません。", orig, tips, srcs)
    if rec["種類"] == "difference" and cur and pri:
        d = cur["値"] - pri["値"]
        tips.append("資料の増減額を、元の数から計算した増減額に直すか、増減の向き(増・減)を確かめてください。")
        return ("資料の増減額と、元の XBRL の数から計算した増減額が合いません。", both_units(d, cur.get("decimals"), unit), tips, srcs)
    if rec["種類"] == "ratio_change" and cur:
        pf = fact_by_pointer(facts, info["derived"][0]) if info.get("derived") else pri
        if pf and pf["値"]:
            p = (cur["値"] - pf["値"]) / abs(pf["値"]) * 100
            return ("資料の増減率と、元の XBRL の数から計算した増減率が合いません。", "%.1f%%" % p,
                    ["資料の増減率を直すか、増減の向きを確かめてください。"], srcs)
    return ("資料の数と、元の XBRL の数が合いません。", "-", ["資料の数の出どころを確かめてください。"], srcs)


def checked_text(rec, info, A):
    m = A["map"]
    head = {"difference": "当期と前期の XBRL の数から計算した増減額と、資料の桁で一致",
            "ratio_change": "当期と前期の XBRL の数から計算した増減率と一致"}.get(rec["種類"], "XBRL の数と資料の桁で一致")
    if info.get("人数"):
        head = "XBRL の人数と一致"
    src = [source_line(m[k]) for k in (info.get("keys") or []) if k in m]
    if rec["種類"] == "ratio_change" and info.get("derived"):
        f = fact_by_pointer(A["facts"], info["derived"][0])
        if f and not any(f["要素"] in s and "前期" in s for s in src):
            src.append(source_line(f))
    return [head] + src


CSS = """body{font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif;color:#16233b;font-size:10pt;line-height:1.65;max-width:190mm;margin:8mm auto;padding:0 4mm}
h1{font-size:16pt;margin:0 0 2mm}h2{font-size:12.5pt;margin:7mm 0 2mm;border-bottom:.4mm solid #16233b;padding-bottom:1mm}h3{font-size:10.5pt;margin:4mm 0 1mm}
.lead{border-left:1.4mm solid #b7791f;background:#fbf1dc;padding:3mm 5mm;margin:3mm 0 4mm}.lead.ok{border-color:#2f855a;background:#e6f4ea}
.lead b{font-size:13pt}.basis{font-size:9pt;color:#334;background:#f3f5f9;padding:2mm 4mm}.counts{display:flex;gap:3mm;margin:3mm 0}
.counts div{flex:1;border:.3mm solid #d9dee8;padding:2mm;text-align:center}.counts span{display:block;font-size:17pt;font-weight:700}
.card{border:.3mm solid #d9dee8;border-left:1.4mm solid #c05621;padding:2mm 4mm;margin:3mm 0;break-inside:avoid}.card h3{margin:0 0 1mm;font-size:11pt}
table{border-collapse:collapse;width:100%;font-size:9pt;margin:2mm 0}th{background:#f3f5f9;text-align:left}
th,td{border:.25mm solid #d9dee8;padding:1.2mm 1.8mm;vertical-align:top}small{color:#51607a}ul{margin:1mm 0 1mm 5mm;padding:0}"""
MARK = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"


def report(n, recs, A, title):
    cnt = {k: sum(r["区分"] == k for r in recs) for k in ("確認済み", "要確認", "人の判断が必要", "点検していない")}
    checked = cnt["確認済み"] + cnt["要確認"] + cnt["人の判断が必要"]
    b = ['<h1>資料点検レポート</h1><p>点検した資料: %s</p>' % html.escape(title)]
    b.append('<p class="basis">照合の基準: 提出された有価証券報告書の XBRL(生のデータを機械で読んだもの。基準を作るのに AI は使っていません)。範囲: %s(作る前の確認で人が決めたもの)。</p>' % html.escape(A.get("範囲") or "未定"))
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
        what, orig, tips, srcs = advice(r, r["info"], A)
        kind = {"difference": "増減額", "ratio_change": "増減率"}.get(r["種類"], "")
        b.append('<div class="card"><h3>%s %s(%s%s)― 資料の数「%s」</h3><p>%s</p><table><tr><th>資料の数</th><td>%s</td></tr><tr><th>元の数</th><td>%s</td></tr><tr><th>元の数の出どころ</th><td>%s</td></tr><tr><th>資料の場所</th><td>%s</td></tr></table><b>確認してください</b><ul>%s</ul></div>' % (
            MARK[k - 1] if k <= 20 else str(k), html.escape(r["項目"]), html.escape(r["期"] or "-"), "・" + kind if kind else "",
            html.escape(r["字"]), html.escape(what), html.escape(r["字"]), html.escape(orig),
            "<br>".join(html.escape(s) for s in srcs) or "-", html.escape(r["場所"] + "・" + str(r["行"] + 1) + " 行目"),
            "".join("<li>%s</li>" % html.escape(t) for t in tips)))
    if not k:
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
                     "<br>".join(html.escape(x) for x in checked_text(r, r["info"], A))))
        b.append("</table>")
    b.append("<h2>点検していない数</h2><p>次の数は、今の点検では確かめていません。必要なら人が確かめてください。</p><table><tr><th>資料の数</th><th>場所</th><th>訳</th></tr>")
    for r in recs:
        if r["区分"] == "点検していない":
            b.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (html.escape(r["字"]), html.escape(r["場所"] + "・" + str(r["行"] + 1) + " 行目"), html.escape(r["info"].get("訳", ""))))
    b.append("</table><h2>この点検で見ていないこと</h2><ul><li>提出された XBRL そのものが、会社の帳簿と合っているか。</li><li>資料の文の言い回しや、数以外の内容。</li><li>上の「点検していない数」。</li></ul>")
    return '<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>資料点検レポート 第%s社</title><style>%s</style></head><body>%s</body></html>' % (n, CSS, "\n".join(b))


def run(n, md, basis, kind, out_json, out_html=None):
    recs = extract(md)
    for r in recs:
        r["区分"], r["info"] = verify(r, basis, kind)
    for p in (out_json, out_html):
        if p:
            os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1, default=str)
    if out_html:
        title = next((l.lstrip("#").strip() for l in md.split("\n") if l.startswith("#")), "資料")
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(report(n, recs, basis, title))
    return recs


def bump(tok):
    for i in range(len(tok) - 1, -1, -1):
        if tok[i].isdigit():
            d = int(tok[i])
            return tok[:i] + str(d + 1 if d < 9 else d - 1) + tok[i + 1:]
    return tok


def mutate(md, recs, A):
    """TR0 の (a)〜(d) を、基準 A で確認済みの数から番号の若い順に入れる。"""
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
        assert line[r["始め"]:r["始め"] + len(r["字"])] == r["字"]
        lines[r["行"]] = line[:r["始め"]] + new + line[r["始め"] + len(r["字"]):]
        muts.append({"種類": kind, "行": r["行"], "始め": r["始め"], "元の字": r["字"], "入れた字": new, "項目": r["項目"], "期": r["期"]})

    def prior_of(r):
        if r["期"] not in ("当期", "当期末"):
            return None
        e = A["map"].get("%s@%s" % (r["項目"], CTX[periods(r["項目"])[1]]))
        if e is None:
            return None
        v = int(round(e["値"] / SCALE[r["単位"]]))
        return None if v == int(round(abs(r["値"]))) else v

    r = take(table)
    if r:
        put(r, bump(r["字"]), "a")
    r = take(table, lambda r: prior_of(r) is not None)
    if r:
        v = prior_of(r)
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
    c = lambda rs, k: sum(r["区分"] == k for r in rs)
    for n in NUMS:
        A = load(os.path.join(ROOT, "A", n + ".json"))
        B = load(os.path.join(ROOT, "B", n + ".json"))
        with open(os.path.join(ROOT, "doc", n + ".md"), encoding="utf-8") as f:
            md = f.read()
        ra = run(n, md, A, "A", os.path.join(ROOT, "check_A", n + ".json"), os.path.join(ROOT, "report_A", n + ".html"))
        rb = run(n, md, B, "B", os.path.join(ROOT, "check_B", n + ".json"))
        mmd, muts = mutate(md, ra, A)
        os.makedirs(os.path.join(ROOT, "mut"), exist_ok=True)
        with open(os.path.join(ROOT, "mut", n + ".md"), "w", encoding="utf-8") as f:
            f.write(mmd)
        with open(os.path.join(ROOT, "mut", n + ".json"), "w", encoding="utf-8") as f:
            json.dump(muts, f, ensure_ascii=False, indent=1)
        rm = run(n, mmd, A, "A", os.path.join(ROOT, "check_mut", n + ".json"), os.path.join(ROOT, "report_mut", n + ".html"))
        with open(os.path.join(TR0, "doc", n + ".md"), encoding="utf-8") as f:
            r0 = run(n, f.read(), A, "A", os.path.join(ROOT, "check_tr0docs", n + ".json"))
        print(n, "A: 拾った", len(ra), "確認済み", c(ra, "確認済み"), "要確認", c(ra, "要確認"), "外", c(ra, "点検していない"),
              "| B: 確認済み", c(rb, "確認済み"), "要確認", c(rb, "要確認"),
              "| 誤り", len(muts), "要確認", c(rm, "要確認"), "| TR0 の資料 A 要確認", c(r0, "要確認"))


if __name__ == "__main__":
    main()
