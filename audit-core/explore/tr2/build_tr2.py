# -*- coding: utf-8 -*-
"""便 TR2: 作り物の会計ソフトの書き出し(xlsx)・翌期の版・変異 7 種・正解の値・提案の席に渡す CSV を作る(封 §1)。

使い方: python3 -I build_tr2.py <TR2 の根>
書くもの(社 n = 51〜56):
  co{n}/期1/書き出し.xlsx・co{n}/期2/書き出し.xlsx・co{n}/変異/{種類}/書き出し.xlsx
  co{n}/sheets/(期 1 のシートごとの CSV と 一覧.json。提案の席に渡す)
  co{n}/正解/値.json(項目@期 → 円。期1・期2・変異ごと)・co{n}/正解/変異.json(変異を入れた所。集計だけが読む)
AI を使わない。乱数は社の番号で固定。
"""
import copy
import csv
import json
import os
import random
import sys

import openpyxl

OUT = sys.argv[1]
NUMS = [51, 52, 53, 54, 55, 56]
KINDS = ["列の挿入", "行の並べ替え", "シート名の変更", "行の見出しの微修正", "列の見出しの微修正", "科目の追加", "単位の変更"]

CFG = {
    51: dict(bs="貸借対照表", pl="損益計算書", mfg=None, dept=None, unit="円", code=False, cur_first=False, profit=True,
             split=False, nebiki=False, cash=["現金", "普通預金", "定期預金"], st=["短期借入金(A銀行)", "短期借入金(B銀行)"],
             lt=["長期借入金"], cash_sub=False, sga_total=False, label="科目", bscol=("前期末", "当期末"), plcol=("前期", "当期"),
             sections=True, dup=False, loss=False, blank=True),
    52: dict(bs="BS", pl="PL", mfg="製造原価", dept=None, unit="千円", code=True, cur_first=True, profit=False,
             split=False, nebiki=False, cash=["現金", "当座預金", "普通預金"], st=["短期借入金"],
             lt=["長期借入金(C銀行)", "長期借入金(D銀行)"], cash_sub=False, sga_total=False, label="勘定科目",
             bscol=("前期末", "当期末"), plcol=("前期", "当期"), sections=False, dup=False, loss=False, blank=False),
    53: dict(bs="残高試算表", pl="損益計算書", mfg=None, dept="部門別売上", unit="円", code=False, cur_first=False, profit=True,
             split=True, nebiki=True, cash=["現金", "普通預金"], st=["短期借入金(A銀行)", "短期借入金(B銀行)"],
             lt=["長期借入金"], cash_sub=False, sga_total=False, label="科目名", bscol=("前期末残高", "当期末残高"),
             plcol=("前期", "当期"), sections=True, dup=False, loss=False, blank=True),
    54: dict(bs="貸借対照表", pl="損益計算書", mfg="製造原価報告書", dept=None, unit="千円", code=True, cur_first=False,
             profit=True, split=False, nebiki=False, cash=["現金", "当座預金", "普通預金", "定期預金"], st=["短期借入金"],
             lt=["長期借入金"], cash_sub=True, sga_total=True, label="勘定科目", bscol=("前期末", "当期末"),
             plcol=("前期実績", "当期実績"), sections=True, dup=False, loss=False, blank=False),
    55: dict(bs="貸借表", pl="損益表", mfg=None, dept=None, unit="円", code=False, cur_first=True, profit=False,
             split=True, nebiki=False, cash=["現金", "普通預金"],
             st=["短期借入金(A銀行)", "短期借入金(B銀行)", "短期借入金(C銀行)"], lt=["長期借入金(D銀行)", "長期借入金(E銀行)"],
             cash_sub=False, sga_total=True, label="科目", bscol=("前期末", "当期末"), plcol=("前期", "当期"),
             sections=False, dup=False, loss=True, blank=True),
    56: dict(bs="貸借", pl="損益", mfg=None, dept="部門別", unit="千円", code=False, cur_first=False, profit=True,
             split=False, nebiki=False, cash=["現金", "普通預金", "定期預金"], st=["短期借入金(A銀行)", "短期借入金(B銀行)"],
             lt=["長期借入金"], cash_sub=False, sga_total=False, label="科目", bscol=("前期末", "当期末"),
             plcol=("前期", "当期"), sections=True, dup=True, loss=False, blank=True),
}
SGA = ["給料手当", "地代家賃", "減価償却費", "広告宣伝費", "支払手数料", "雑費"]
SGA_R = [0.12, 0.03, 0.02, 0.02, 0.015, 0.01]


def r(rng, x):
    return x * rng.uniform(0.9, 1.1)


def year(rng, c, S, f):
    """1 年分の科目の値(円)。千円の社は科目ごとに千円に丸め、合計は丸めた科目から作る。"""
    q = 1000 if c["unit"] == "千円" else 1
    rd = lambda x: int(round(x / q)) * q
    pl, bs, mfg = {}, {}, {}
    ns0 = S * f
    if c["split"]:
        pl["製品売上高"] = rd(r(rng, ns0 * 0.6))
        pl["商品売上高"] = rd(r(rng, ns0 * 0.4))
    else:
        pl["売上高"] = rd(r(rng, ns0))
    if c["nebiki"]:
        pl["売上値引"] = rd(r(rng, ns0 * 0.01))
    ns = sum(v for k, v in pl.items() if k != "売上値引") - pl.get("売上値引", 0)
    pl["売上原価"] = rd(r(rng, ns * (0.80 if c["loss"] else 0.65)))
    for k, a in zip(SGA, SGA_R):
        pl[k] = rd(r(rng, ns * a * (1.4 if c["loss"] else 1)))
    sga = sum(pl[k] for k in SGA)
    for k, a in (("受取利息", 0.001), ("雑収入", 0.003), ("支払利息", 0.004), ("雑損失", 0.001),
                 ("固定資産売却益", 0.002), ("固定資産除却損", 0.001)):
        pl[k] = rd(r(rng, ns * a))
    op = ns - pl["売上原価"] - sga
    od = op + pl["受取利息"] + pl["雑収入"] - pl["支払利息"] - pl["雑損失"]
    pre = od + pl["固定資産売却益"] - pl["固定資産除却損"]
    pl["法人税等"] = rd(max(0, pre * 0.3))
    net = pre - pl["法人税等"]
    d = dict(売上高=ns, 売上総利益=ns - pl["売上原価"], 販管費合計=sga, 営業利益=op, 経常利益=od, 税引前当期純利益=pre, 当期純利益=net)
    if c["mfg"]:
        for k, a in (("材料費", 0.3), ("労務費", 0.15), ("減価償却費", 0.03), ("経費", 0.08)):
            mfg[k] = rd(r(rng, ns * a))
    cash = {k: rd(r(rng, S * (0.002 if k == "現金" else 0.06))) for k in c["cash"]}
    bs.update(cash)
    for k, a in (("売掛金", 0.15), ("商品", 0.08), ("その他流動資産", 0.01)):
        bs[k] = rd(r(rng, S * f * a))
    ca = sum(bs.values())
    fa = {k: rd(r(rng, S * a)) for k, a in (("建物", 0.2), ("機械装置", 0.1), ("土地", 0.15), ("投資有価証券", 0.05))}
    bs.update(fa)
    st = {k: rd(r(rng, S * 0.05)) for k in c["st"]}
    lt = {k: rd(r(rng, S * 0.08)) for k in c["lt"]}
    bs["買掛金"] = rd(r(rng, S * f * 0.1))
    bs.update(st)
    bs["1年以内返済予定の長期借入金"] = rd(r(rng, S * 0.02))
    bs["未払法人税等"] = rd(max(q, pl["法人税等"] * 0.5))
    bs["その他流動負債"] = rd(r(rng, S * 0.01))
    cl = bs["買掛金"] + sum(st.values()) + bs["1年以内返済予定の長期借入金"] + bs["未払法人税等"] + bs["その他流動負債"]
    bs.update(lt)
    bs["退職給付引当金"] = rd(r(rng, S * 0.02))
    fl = sum(lt.values()) + bs["退職給付引当金"]
    bs["資本金"] = rd(S * 0.05)
    ta = ca + sum(fa.values())
    na = ta - cl - fl
    bs["利益剰余金"] = na - bs["資本金"]
    t = dict(現金及び預金=sum(cash.values()), 流動資産合計=ca, 固定資産合計=sum(fa.values()), 資産合計=ta, 流動負債合計=cl,
             固定負債合計=fl, 負債合計=cl + fl, 純資産合計=na, 負債純資産合計=ta, 短期借入金=sum(st.values()), 長期借入金=sum(lt.values()))
    return {"pl": pl, "bs": bs, "mfg": mfg, "d": d, "t": t}


def truth(c, y_prior, y_cur):
    dep = y_cur["pl"]["減価償却費"] + (y_cur["mfg"].get("減価償却費", 0) if c["mfg"] else 0)
    return {"売上高@当期": y_cur["d"]["売上高"], "売上高@前期": y_prior["d"]["売上高"],
            "営業利益@当期": y_cur["d"]["営業利益"], "営業利益@前期": y_prior["d"]["営業利益"],
            "経常利益@当期": y_cur["d"]["経常利益"], "当期純利益@当期": y_cur["d"]["当期純利益"], "減価償却費@当期": dep,
            "現金及び預金@当期末": y_cur["t"]["現金及び預金"], "流動資産合計@当期末": y_cur["t"]["流動資産合計"],
            "資産合計@当期末": y_cur["t"]["資産合計"], "短期借入金@当期末": y_cur["t"]["短期借入金"],
            "長期借入金@当期末": y_cur["t"]["長期借入金"], "負債合計@当期末": y_cur["t"]["負債合計"],
            "純資産合計@当期末": y_cur["t"]["純資産合計"], "純資産合計@前期末": y_prior["t"]["純資産合計"]}


def bs_rows(c, y):
    """(行の見出し, 値の鍵 or None)。値の鍵は ("bs", 科目) か ("t", 合計)。"""
    sec = c["sections"]
    rows = []
    if sec:
        rows += [("【資産の部】", None), ("流動資産", None)]
    rows += [(k, ("bs", k)) for k in c["cash"]]
    if c["cash_sub"]:
        rows.append(("現金及び預金合計", ("t", "現金及び預金")))
    rows += [("売掛金", ("bs", "売掛金")), ("商品", ("bs", "商品")),
             ("その他" if c["dup"] else "その他流動資産", ("bs", "その他流動資産")), ("流動資産合計", ("t", "流動資産合計"))]
    if sec:
        rows.append(("固定資産", None))
    rows += [(k, ("bs", k)) for k in ("建物", "機械装置", "土地", "投資有価証券")]
    rows += [("固定資産合計", ("t", "固定資産合計")), ("資産合計", ("t", "資産合計"))]
    if sec:
        rows += [("【負債の部】", None), ("流動負債", None)]
    rows.append(("買掛金", ("bs", "買掛金")))
    rows += [(k, ("bs", k)) for k in c["st"]]
    rows += [("1年以内返済予定の長期借入金", ("bs", "1年以内返済予定の長期借入金")), ("未払法人税等", ("bs", "未払法人税等")),
             ("その他" if c["dup"] else "その他流動負債", ("bs", "その他流動負債")), ("流動負債合計", ("t", "流動負債合計"))]
    if sec:
        rows.append(("固定負債", None))
    rows += [(k, ("bs", k)) for k in c["lt"]]
    rows += [("退職給付引当金", ("bs", "退職給付引当金")), ("固定負債合計", ("t", "固定負債合計")), ("負債合計", ("t", "負債合計"))]
    if sec:
        rows.append(("【純資産の部】", None))
    rows += [("資本金", ("bs", "資本金")), ("利益剰余金", ("bs", "利益剰余金")), ("純資産合計", ("t", "純資産合計")),
             ("負債純資産合計", ("t", "負債純資産合計"))]
    return rows


def pl_rows(c):
    rows = []
    if c["split"]:
        rows += [("製品売上高", ("pl", "製品売上高")), ("商品売上高", ("pl", "商品売上高"))]
    else:
        rows.append(("売上高", ("pl", "売上高")))
    if c["nebiki"]:
        rows.append(("売上値引", ("pl", "売上値引")))
    rows.append(("売上原価", ("pl", "売上原価")))
    if c["profit"]:
        rows.append(("売上総利益", ("d", "売上総利益")))
    rows.append(("販売費及び一般管理費", None))
    rows += [(k, ("pl", k)) for k in SGA]
    if c["sga_total"]:
        rows.append(("販売費及び一般管理費合計", ("d", "販管費合計")))
    if c["profit"]:
        rows.append(("営業損失" if c["loss"] else "営業利益", ("d", "営業利益")))
    rows += [("営業外収益", None), ("受取利息", ("pl", "受取利息")), ("雑収入", ("pl", "雑収入")),
             ("営業外費用", None), ("支払利息", ("pl", "支払利息")), ("雑損失", ("pl", "雑損失"))]
    if c["profit"]:
        rows.append(("経常利益", ("d", "経常利益")))
    rows += [("特別利益", None), ("固定資産売却益", ("pl", "固定資産売却益")),
             ("特別損失", None), ("固定資産除却損", ("pl", "固定資産除却損"))]
    if c["profit"]:
        rows.append(("税引前当期純利益", ("d", "税引前当期純利益")))
    rows.append(("法人税等", ("pl", "法人税等")))
    if c["profit"]:
        rows.append(("当期純利益", ("d", "当期純利益")))
    return rows


def val(y, key):
    part, k = key
    return y[part][k] if part != "t" else y["t"][k]


def grid(c, title, cols, rows, y_prior, y_cur, n, codes):
    """シートの升の並び(行の list)。列の見出しの行の番号も返す。"""
    q = 1000 if c["unit"] == "千円" else 1
    head = [[title], ["第%d社" % n], ["(単位:%s)" % c["unit"]]]
    if c["blank"]:
        head.append([])
    pri, cur = cols
    order = [cur, pri] if c["cur_first"] else [pri, cur]
    hdr = (["コード"] if c["code"] else []) + [c["label"]] + order
    out = [list(h) for h in head] + [hdr]
    for i, (lab, key) in enumerate(rows):
        line = ([codes.get(lab, "")] if c["code"] else []) + [lab]
        if key is None:
            line += [None, None]
        else:
            vv = {pri: val(y_prior, key), cur: val(y_cur, key)}
            # 営業損失の行は損失を正の数で出す
            if lab == "営業損失":
                vv = {k: -v for k, v in vv.items()}
            line += [vv[o] // q if q > 1 else vv[o] for o in order]
        out.append(line)
    return out, len(head) + 1


def book(c, n, yp, yc):
    rng = random.Random(n * 7)
    codes = {}
    sheets = {}
    bsr = bs_rows(c, yc)
    plr = pl_rows(c)
    for lab, _ in bsr + plr:
        codes.setdefault(lab, str(1000 + rng.randint(0, 8999)))
    sheets[c["bs"]], _ = grid(c, "貸借対照表", c["bscol"], bsr, yp, yc, n, codes)
    sheets[c["pl"]], _ = grid(c, "損益計算書", c["plcol"], plr, yp, yc, n, codes)
    if c["mfg"]:
        mr = [(k, ("mfg", k)) for k in ("材料費", "労務費", "減価償却費", "経費")]
        sheets[c["mfg"]], _ = grid(c, "製造原価報告書", c["plcol"], mr, yp, yc, n, codes)
    if c["dept"]:
        q = 1000 if c["unit"] == "千円" else 1
        ns = yc["d"]["売上高"]
        a = int(round(ns * 0.55 / q)) * q
        dr = [["部門別売上高"], ["(単位:%s)" % c["unit"]], ["部門", "当期"], ["売上高(第一営業部)", a // q],
              ["売上高(第二営業部)", (ns - a) // q], ["売上高合計", ns // q]]
        sheets[c["dept"]] = dr
    return sheets


def write_xlsx(sheets, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, g in sheets.items():
        ws = wb.create_sheet(name)
        for row in g:
            ws.append(row if row else [None])
    wb.save(path)


def hdr_row(g):
    for i, row in enumerate(g):
        if row and any(isinstance(x, str) and x in ("科目", "勘定科目", "科目名", "部門") for x in row):
            return i
    raise ValueError("見出しの行が無い")


def label_col(g):
    h = g[hdr_row(g)]
    return next(i for i, x in enumerate(h) if x in ("科目", "勘定科目", "科目名", "部門"))


def find_row(g, label):
    lc = label_col(g)
    return next(i for i, row in enumerate(g) if i > hdr_row(g) and len(row) > lc and row[lc] == label)


def mutate(c, n, sheets, y2, yp2, kind):
    """変異 1 つ。返すのは (新しい sheets, 変異の所, 正解の差し替え)。"""
    s = copy.deepcopy(sheets)
    bs = s[c["bs"]]
    h = hdr_row(bs)
    lc = label_col(bs)
    q = 1000 if c["unit"] == "千円" else 1
    fix = {}
    if kind == "列の挿入":
        cols = bs[h]
        a, b = len(cols) - 2, len(cols) - 1
        for i, row in enumerate(bs):
            if i < h:
                continue
            if i == h:
                row.insert(b, "増減")
            elif len(row) > b:
                x, y = row[a], row[b]
                row.insert(b, (y - x) if isinstance(x, int) and isinstance(y, int) else None)
        where = {"シート": c["bs"], "種類": "列の見出し", "字": "増減"}
    elif kind == "行の並べ替え":
        i = find_row(bs, "買掛金")
        bs[i], bs[i + 1] = bs[i + 1], bs[i]
        where = {"シート": c["bs"], "種類": "行の見出し", "字": "買掛金"}
    elif kind == "シート名の変更":
        new = c["pl"] + "(2)"
        s = {(new if k == c["pl"] else k): v for k, v in s.items()}
        where = {"シート": c["pl"], "種類": "シートの名", "字": new}
    elif kind == "行の見出しの微修正":
        old = c["st"][0]
        new = old.replace("(", " ").replace(")", "") if "(" in old else old + "(本店)"
        bs[find_row(bs, old)][lc] = new
        where = {"シート": c["bs"], "種類": "行の見出し", "字": new}
    elif kind == "列の見出しの微修正":
        j = len(bs[h]) - 1 if not c["cur_first"] else len(bs[h]) - 2
        old = bs[h][j]
        bs[h][j] = old + "残高" if not old.endswith("残高") else old.replace("残高", " 残高")
        where = {"シート": c["bs"], "種類": "列の見出し", "字": bs[h][j]}
    elif kind == "科目の追加":
        x = 30000000
        new = "短期借入金(F銀行)"
        i = find_row(bs, c["st"][-1])
        line = ([""] if c["code"] else []) + [new] + ([0, x // q] if not c["cur_first"] else [x // q, 0])
        bs.insert(i + 1, line)
        cur_j = (len(bs[h]) - 1) if not c["cur_first"] else (len(bs[h]) - 2)
        for lab in ("普通預金", "流動資産合計", "資産合計", "流動負債合計", "負債合計", "負債純資産合計") + (("現金及び預金合計",) if c["cash_sub"] else ()):
            bs[find_row(bs, lab)][cur_j] += x // q
        fix = {"短期借入金@当期末": x, "現金及び預金@当期末": x, "流動資産合計@当期末": x, "資産合計@当期末": x, "負債合計@当期末": x}
        where = {"シート": c["bs"], "種類": "行の見出し", "字": new}
    elif kind == "単位の変更":
        to = "円" if c["unit"] == "千円" else "千円"
        for i, row in enumerate(bs):
            if i < h and row and isinstance(row[0], str) and "単位" in row[0]:
                row[0] = row[0].replace("千円", "円") if to == "円" else row[0].replace("円", "千円")
            if i > h:
                for j in range(len(row)):
                    if j != lc and isinstance(row[j], int) and not (c["code"] and j == 0):
                        row[j] = row[j] * 1000 if to == "円" else int(round(row[j] / 1000))
        where = {"シート": c["bs"], "種類": "頭の行", "字": "(単位:%s)" % to}
    return s, where, fix


def main():
    for n in NUMS:
        c = CFG[n]
        rng = random.Random(n)
        S = rng.randint(800, 5000) * 1000000
        f0 = 1.0
        f1 = f0 * rng.uniform(0.92, 1.15)
        f2 = f1 * rng.uniform(0.92, 1.15)
        y0, y1, y2 = year(rng, c, S, f0), year(rng, c, S, f1), year(rng, c, S, f2)
        root = os.path.join(OUT, "co%d" % n)
        s1 = book(c, n, y0, y1)
        s2 = book(c, n, y1, y2)
        write_xlsx(s1, os.path.join(root, "期1", "書き出し.xlsx"))
        write_xlsx(s2, os.path.join(root, "期2", "書き出し.xlsx"))
        t1, t2 = truth(c, y0, y1), truth(c, y1, y2)
        vals = {"期1": t1, "期2": t2, "変異": {}}
        wheres = {}
        for kind in KINDS:
            sm, where, fix = mutate(c, n, s2, y2, y1, kind)
            write_xlsx(sm, os.path.join(root, "変異", kind, "書き出し.xlsx"))
            tv = dict(t2)
            for k, v in fix.items():
                tv[k] += v
            vals["変異"][kind] = tv
            wheres[kind] = where
        os.makedirs(os.path.join(root, "正解"), exist_ok=True)
        with open(os.path.join(root, "正解", "値.json"), "w", encoding="utf-8") as f:
            json.dump(vals, f, ensure_ascii=False, indent=1)
        with open(os.path.join(root, "正解", "変異.json"), "w", encoding="utf-8") as f:
            json.dump(wheres, f, ensure_ascii=False, indent=1)
        # 提案の席に渡す CSV(期 1 の xlsx を読み直して、升の字のまま)
        sd = os.path.join(root, "sheets")
        os.makedirs(sd, exist_ok=True)
        wb = openpyxl.load_workbook(os.path.join(root, "期1", "書き出し.xlsx"), data_only=True)
        idx = {}
        for k, ws in enumerate(wb.worksheets, 1):
            fn = "sheet_%d.csv" % k
            idx[fn] = ws.title
            with open(os.path.join(sd, fn), "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                for row in ws.iter_rows(values_only=True):
                    w.writerow(["" if x is None else x for x in row])
        with open(os.path.join(sd, "一覧.json"), "w", encoding="utf-8") as f:
            json.dump(idx, f, ensure_ascii=False, indent=1)
        print(n, "シート", list(s1), "単位", c["unit"], "利益の行", c["profit"])


if __name__ == "__main__":
    main()
