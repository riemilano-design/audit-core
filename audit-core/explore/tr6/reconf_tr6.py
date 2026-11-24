# -*- coding: utf-8 -*-
"""便 TR6: 止めた後の確定し直し(封 §2)。AI を使わない。TR2 の ledger_tr2 を変えずに読んで使う。

- diff(decided, ledger, book): 確定の台帳の指紋と今回の file を比べ、変わった所を「縮めた形」で返す。
  位置ごとの対(TR2)でなく、並びの差(difflib)で、足した・消えた・動いた・字が変わった、を 1 つずつ出す。
  変わった所ごとに、機械の案と、影響する項目を付ける。案の無い所(足した行・消えた行など)は人が決める。
- apply(decided, changes, decisions): 決めを台帳の決める部分に当て、新しい決める部分を返す(指紋は make_ledger が作り直す)。
決めの形(変わった所の番号ごと):
  シートの名の変更 / 列の字の変更 / 行の字の変更: {"対応": "<今回の字>"} か {"使わない": true}(行だけ)
  行の追加: {"使わない": true} か {"項目": ["<項目@期>", ...], "符号": 1|-1}
  単位の変更: {"単位": "円"|"千円"}
  列の追加・行の順の変更・頭の行の字の変更・使わないシートの増減: {"了承": true}(台帳は変えない)
  列の削除・行の削除: {"了承": true}(その列・行を使う成分を外す)
"""
import copy
import difflib
import re

import ledger_tr2 as L

NEED = {"行の追加", "列の削除", "行の削除", "シートが無い"}  # 案を出さない種類


def _uses(decided):
    """(シート, 行) と (シート, 列) → それを使う項目@期 の集まり。"""
    rows, cols, sheets = {}, {}, {}
    for it in decided["項目"]:
        key = "%s@%s" % (it["項目"], it["期"])
        for c in it.get("成分") or []:
            rows.setdefault((c["シート"], c["行"]), set()).add(key)
            cols.setdefault((c["シート"], c["列"]), set()).add(key)
            sheets.setdefault(c["シート"], set()).add(key)
    return rows, cols, sheets


def _unit_of(lines):
    for t in lines:
        m = re.search(r"単位[::]\s*(千円|円)", t)
        if m:
            return m.group(1)
    return None


def _seq(a, b, kind_add, kind_del, kind_ren, kind_move, sheet, use, rows_ctx=None):
    out = []
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    dels, adds = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                u, v = a[i1 + k], b[j1 + k]
                if u in b or v in a:
                    dels.append((i1 + k, u))
                    adds.append((j1 + k, v))
                else:
                    out.append({"種類": kind_ren, "シート": sheet, "前": u, "今": v, "位置": j1 + k + 1,
                                "影響": sorted(use.get((sheet, u), ())), "案": {"対応": v}})
            continue
        dels += [(i, a[i]) for i in range(i1, i2)]
        adds += [(j, b[j]) for j in range(j1, j2)]
    moved = {x for _, x in dels} & {x for _, x in adds}
    for x in sorted(moved):
        out.append({"種類": kind_move, "シート": sheet, "前": x, "今": x, "影響": sorted(use.get((sheet, x), ())), "案": {"了承": True}})
    for i, x in dels:
        if x not in moved:
            out.append({"種類": kind_del, "シート": sheet, "前": x, "今": "(無い)", "位置": i + 1, "影響": sorted(use.get((sheet, x), ())),
                        "案": None})
    for j, x in adds:
        if x not in moved:
            ch = {"種類": kind_add, "シート": sheet, "前": "(無い)", "今": x, "位置": j + 1, "影響": [], "案": None}
            if kind_add == "列の追加":
                ch["案"] = {"了承": True}
            out.append(ch)
    return out


def diff(decided, ledger, book):
    rows_use, cols_use, sheet_use = _uses(decided)
    fp0 = ledger["指紋"]
    out = []
    a, b = set(fp0["シートの名"]), set(book)
    used = [s for s, cfg in decided["シート"].items() if cfg.get("使う")]
    gone, new = sorted(a - b), sorted(b - a)
    rename = {}
    gone_used = [s for s in gone if s in used]
    if len(gone_used) == 1 and len(new) == 1:
        rename[gone_used[0]] = new[0]
    for s in gone:
        if s in rename:
            out.append({"種類": "シートの名の変更", "シート": s, "前": s, "今": rename[s], "影響": sorted(sheet_use.get(s, ())),
                        "案": {"対応": rename[s]}})
        elif s in used:
            out.append({"種類": "シートが無い", "シート": s, "前": s, "今": "(無い)", "影響": sorted(sheet_use.get(s, ())), "案": None})
        else:
            out.append({"種類": "使わないシートの増減", "シート": s, "前": s, "今": "(無い)", "影響": [], "案": {"了承": True}})
    for s in new:
        if s not in rename.values():
            out.append({"種類": "使わないシートの増減", "シート": s, "前": "(無い)", "今": s, "影響": [], "案": {"了承": True}})
    for s in used:
        s1 = rename.get(s, s)
        if s1 not in book:
            continue
        p0 = fp0.get(s)
        lay = L.layout(book[s1], decided["シート"][s])
        if lay is None or p0 is None:
            out.append({"種類": "列の見出しが見つからない", "シート": s, "前": decided["シート"][s].get("行の見出しの列"), "今": "(無い)",
                        "影響": sorted(sheet_use.get(s, ())), "案": None})
            continue
        h, lc, rws = lay
        head = [" ".join(L.text(x) for x in r if x is not None) for r in book[s1][:h]]
        cols = [L.text(x) for x in book[s1][h]]
        labs = [lab for _, lab, _ in rws]
        if head != p0["頭"]:
            u0, u1 = _unit_of(p0["頭"]), _unit_of(head)
            if u0 and u1 and u0 != u1:
                out.append({"種類": "単位の変更", "シート": s, "前": u0, "今": u1, "影響": sorted(sheet_use.get(s, ())), "案": {"単位": u1}})
            else:
                out.append({"種類": "頭の行の字の変更", "シート": s, "前": " / ".join(p0["頭"]), "今": " / ".join(head), "影響": [],
                            "案": {"了承": True}})
        out += _seq(p0["列"], cols, "列の追加", "列の削除", "列の字の変更", "列の順の変更", s, cols_use)
        out += _seq(p0["行"], labs, "行の追加", "行の削除", "行の字の変更", "行の順の変更", s, rows_use)
    for i, ch in enumerate(out, 1):
        ch["番号"] = i
    return out


def context(decided, book, sheet, label, rename=None, k=2):
    """今回の file で、その行の前後 k 行(行の見出しと升の値)。"""
    s1 = (rename or {}).get(sheet, sheet)
    lay = L.layout(book[s1], decided["シート"][sheet])
    if lay is None:
        return []
    h, lc, rws = lay
    idx = [n for n, (_, lab, _) in enumerate(rws) if lab == label]
    if not idx:
        return []
    n = idx[0]
    out = []
    for i, lab, kk in rws[max(0, n - k): n + k + 1]:
        out.append({"行": lab, "値": [L.text(x) for x in book[s1][i]], "これ": lab == label})
    return out


def apply(decided, changes, decisions):
    """決めを当てた新しい決める部分と、当てられなかった所の一覧を返す。"""
    d = copy.deepcopy(decided)
    bad = []
    byn = {ch["番号"]: ch for ch in changes}
    for num, dec in decisions.items():
        ch = byn.get(num)
        if ch is None or not isinstance(dec, dict):
            bad.append((num, "番号か決めが読めない"))
            continue
        k, s = ch["種類"], ch["シート"]
        if k == "シートの名の変更" and dec.get("対応"):
            new = dec["対応"]
            d["シート"] = {(new if x == s else x): v for x, v in d["シート"].items()}
            for it in d["項目"]:
                for c in it.get("成分") or []:
                    if c["シート"] == s:
                        c["シート"] = new
            for u in d.get("使わない行") or []:
                if u.get("シート") == s:
                    u["シート"] = new
        elif k == "列の字の変更" and dec.get("対応"):
            for it in d["項目"]:
                for c in it.get("成分") or []:
                    if c["シート"] == s and c["列"] == ch["前"]:
                        c["列"] = dec["対応"]
        elif k == "行の字の変更" and dec.get("対応"):
            for it in d["項目"]:
                for c in it.get("成分") or []:
                    if c["シート"] == s and c["行"] == ch["前"]:
                        c["行"] = dec["対応"]
            for u in d.get("使わない行") or []:
                if u.get("シート") == s and u.get("行") == ch["前"]:
                    u["行"] = dec["対応"]
        elif k in ("行の字の変更", "行の追加") and dec.get("使わない"):
            for it in d["項目"]:
                it["成分"] = [c for c in it.get("成分") or [] if not (c["シート"] == s and c["行"] == ch["前"])]
            d.setdefault("使わない行", []).append({"シート": s, "行": ch["今"], "何番目": 1})
        elif k == "行の追加" and isinstance(dec.get("項目"), list) and dec["項目"]:
            for key in dec["項目"]:
                it = next((x for x in d["項目"] if "%s@%s" % (x["項目"], x["期"]) == key), None)
                col = next((c["列"] for c in (it or {}).get("成分") or [] if c["シート"] == s), None)
                if it is None or col is None:
                    bad.append((num, "項目か列が決まらない: %s" % key))
                    continue
                it["成分"].append({"シート": s, "行": ch["今"], "何番目": 1, "列": col, "符号": -1 if dec.get("符号") == -1 else 1})
        elif k == "単位の変更" and dec.get("単位") in L.UNIT:
            d["シート"][s]["単位"] = dec["単位"]
        elif k in ("列の削除", "行の削除") and dec.get("了承"):
            key = "列" if k == "列の削除" else "行"
            for it in d["項目"]:
                it["成分"] = [c for c in it.get("成分") or [] if not (c["シート"] == s and c[key] == ch["前"])]
        elif dec.get("了承") and k in ("列の追加", "行の順の変更", "列の順の変更", "頭の行の字の変更", "使わないシートの増減"):
            pass
        else:
            bad.append((num, "決めの形が種類に合わない: %s" % k))
    missing = [ch["番号"] for ch in changes if ch["番号"] not in decisions]
    bad += [(m, "決めが無い") for m in missing]
    return d, bad


def plan_only(changes):
    """機械の案だけの決め(案の無い所は決めない)。"""
    return {ch["番号"]: ch["案"] for ch in changes if ch["案"] is not None}
