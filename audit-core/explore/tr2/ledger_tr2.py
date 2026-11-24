# -*- coding: utf-8 -*-
"""便 TR2: 確定の台帳の形と、台帳で元の升から読む規則(封 §2)。AI を使わない。

台帳 = 決める部分(シートの設定・項目と期ごとの成分・使わない行)+ 機械が期 1 の file から作る指紋と升の位置。
読む規則: S1 シートの名の集まり・S2 使うシートの頭の行と列の見出しと行の見出しの並び・S3 未決の行・S4 成分の升が数でない。
1 つでも当たれば読まずに止め、変わった所を返す。素朴な読み方(naive)は升の位置だけで、止めずに読む。
"""
import openpyxl

UNIT = {"円": 1, "千円": 1000}


def load_book(path):
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    out = {}
    for ws in wb.worksheets:
        out[ws.title] = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    return out


def text(x):
    return "" if x is None else str(x)


def layout(g, cfg):
    """(見出しの行の index, 行の見出しの列の index, データの行 [(index, 行の見出し, 何番目)])。作れなければ None。"""
    h = int(cfg["見出しの行"]) - 1
    if h < 0 or h >= len(g):
        return None
    head = [text(x) for x in g[h]]
    if cfg["行の見出しの列"] not in head:
        return None
    lc = head.index(cfg["行の見出しの列"])
    rows, seen = [], {}
    for i in range(h + 1, len(g)):
        lab = g[i][lc] if lc < len(g[i]) else None
        if lab is None or text(lab).strip() == "":
            continue
        lab = text(lab)
        seen[lab] = seen.get(lab, 0) + 1
        rows.append((i, lab, seen[lab]))
    return h, lc, rows


def fingerprint(book, sheets):
    fp = {"シートの名": sorted(book)}
    for name, cfg in sheets.items():
        if not cfg.get("使う") or name not in book:
            continue
        g = book[name]
        lay = layout(g, cfg)
        if lay is None:
            fp[name] = None
            continue
        h, lc, rows = lay
        fp[name] = {"頭": [" ".join(text(x) for x in r if x is not None) for r in g[:h]],
                    "列": [text(x) for x in g[h]], "行": [lab for _, lab, _ in rows]}
    return fp


def _key(c):
    return (c["シート"], c["行"], int(c.get("何番目") or 1))


def make_ledger(decided, book1):
    """decided(提案か確定)と期 1 の book から台帳を作る。成分が見つからない所は「誤り」に並べる。"""
    sheets = {k: dict(v) for k, v in (decided.get("シート") or {}).items()}
    items = {}
    errors, pos = [], {}
    for it in decided.get("項目") or []:
        key = "%s@%s" % (it["項目"], it["期"])
        comps = list(it.get("成分") or [])
        items[key] = comps
        plist = []
        for c in comps:
            s = c.get("シート")
            cfg = sheets.get(s)
            if s not in book1 or not cfg or not cfg.get("使う"):
                errors.append({"項目": key, "訳": "シートが無いか使わない", "成分": c})
                plist.append(None)
                continue
            lay = layout(book1[s], cfg)
            hit = next((i for i, lab, k in lay[2] if (s, lab, k) == _key(c)), None) if lay else None
            head = [text(x) for x in book1[s][lay[0]]] if lay else []
            if hit is None or c.get("列") not in head:
                errors.append({"項目": key, "訳": "行か列が無い", "成分": c})
                plist.append(None)
                continue
            plist.append({"シート": s, "r": hit, "c": head.index(c["列"]), "符号": int(c.get("符号") or 1),
                          "倍率": UNIT.get(cfg.get("単位"), 1)})
        pos[key] = plist
    used = {_key(c) for comps in items.values() for c in comps}
    unused = {_key(u) for u in decided.get("使わない行") or []} - used
    return {"シート": sheets, "項目": items, "使わない": sorted(unused), "指紋": fingerprint(book1, sheets),
            "位置": pos, "誤り": errors}


def read(ledger, book):
    """台帳で読む。止めるなら ("止める", 変わった所の一覧)、読めたら ("読めた", 値, 出どころ)。"""
    diffs = []
    fp0, fp1 = ledger["指紋"], fingerprint(book, ledger["シート"])
    a, b = set(fp0["シートの名"]), set(fp1["シートの名"])
    for x in sorted(a - b):
        diffs.append({"規則": "S1", "シート": x, "種類": "シートの名", "前": x, "今": "(無い)"})
    for x in sorted(b - a):
        diffs.append({"規則": "S1", "シート": x, "種類": "シートの名", "前": "(無い)", "今": x})
    used = [s for s, cfg in ledger["シート"].items() if cfg.get("使う")]
    for s in used:
        if s not in book:
            continue
        p0, p1 = fp0.get(s), fp1.get(s)
        if p1 is None:
            diffs.append({"規則": "S2", "シート": s, "種類": "列の見出し", "前": ledger["シート"][s].get("行の見出しの列"), "今": "(見つからない)"})
            continue
        for kind, name in (("頭", "頭の行"), ("列", "列の見出し"), ("行", "行の見出し")):
            x0, x1 = p0[kind], p1[kind]
            for i in range(max(len(x0), len(x1))):
                u = x0[i] if i < len(x0) else "(無い)"
                v = x1[i] if i < len(x1) else "(無い)"
                if u != v:
                    diffs.append({"規則": "S2", "シート": s, "種類": name, "前": u, "今": v, "位置": i + 1})
        lay = layout(book[s], ledger["シート"][s])
        known = {_key(c) for comps in ledger["項目"].values() for c in comps} | {tuple(u) for u in ledger["使わない"]}
        for _, lab, k in lay[2]:
            if (s, lab, k) not in known:
                diffs.append({"規則": "S3", "シート": s, "種類": "未決の行", "前": "(無い)", "今": lab})
    if diffs:
        return "止める", diffs
    vals, srcs = {}, {}
    for key, comps in ledger["項目"].items():
        total, src = 0, []
        for c in comps:
            s = c["シート"]
            cfg = ledger["シート"][s]
            lay = layout(book[s], cfg)
            head = [text(x) for x in book[s][lay[0]]]
            r = next(i for i, lab, k in lay[2] if (s, lab, k) == _key(c))
            j = head.index(c["列"])
            x = book[s][r][j] if j < len(book[s][r]) else None
            if not isinstance(x, (int, float)) or isinstance(x, bool):
                diffs.append({"規則": "S4", "シート": s, "種類": "升が数でない", "前": "数", "今": text(x), "項目": key})
                continue
            v = int(round(x * UNIT.get(cfg.get("単位"), 1))) * int(c.get("符号") or 1)
            total += v
            src.append({"シート": s, "行": c["行"], "何番目": int(c.get("何番目") or 1), "列": c["列"], "升の値": x,
                        "符号": int(c.get("符号") or 1)})
        vals[key], srcs[key] = total, src
    if diffs:
        return "止める", diffs
    return "読めた", vals, srcs


def naive(ledger, book):
    """升の位置だけで止めずに読む。値の dict と、読めなかった項目の一覧。"""
    vals, miss = {}, []
    for key, plist in ledger["位置"].items():
        total, ok = 0, True
        for p in plist:
            if p is None or p["シート"] not in book:
                ok = False
                break
            g = book[p["シート"]]
            x = g[p["r"]][p["c"]] if p["r"] < len(g) and p["c"] < len(g[p["r"]]) else None
            if not isinstance(x, (int, float)) or isinstance(x, bool):
                ok = False
                break
            total += int(round(x * p["倍率"])) * p["符号"]
        if ok:
            vals[key] = total
        else:
            miss.append(key)
    return vals, miss
