# -*- coding: utf-8 -*-
"""段 5 の engine(封 docs/DOMAIN1_M5_SEAL_2026-10-15.md §1〜§4)。

前の 2 つは**どちらも触らない**(記録だから):
  `sheet_m4_engine_2026-10-15.py`     失敗を出した engine(`1378ec8`)
  `sheet_m4_engine_fix_2026-10-15.py` 診断に使った engine(`7e5df0c`)

この版で足すのは 3 つだけ。
  C-8  階層の手がかり(`款別`・`目別`)を読む。**階層内に候補が無ければ別階層へ逃げない**
  C-9  索引に**親**を持ち、**6 欄(会計・階層・親・科目名・列)で一意でなければ結ばない**
  別名 独立した裏づけ **3 本以上**・食い違い 0。独立の定義は封 §4-2 の I-1〜I-4
**合格線・帯・ルートの順位・採点規則は触らない。**
"""
import collections
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


FIX = _mod("m4fix_for_m5", "sheet_m4_engine_fix_2026-10-15.py")
BASE = FIX.BASE
M2 = FIX.M2
norm = FIX.norm

# 前の版から**変えずに**使う
AMOUNT, SENT, amount_value = BASE.AMOUNT, BASE.SENT, BASE.amount_value
pointer_of = BASE.pointer_of
column_cues, vocabulary = FIX.column_cues, FIX.vocabulary
_hits, _maximal, _depths = FIX._hits, FIX._maximal, FIX._depths
pick, FILE_ORDER = FIX.pick, FIX.FILE_ORDER

# 階層の手がかりは**この文書の階層の印だけ**にする。
# `会計`(「全20会計の」)と `合計`(「歳入決算額の合計は」)は**普通の名詞としても使われる**
# ので手がかりにしない ― 実測で、`歳出決算額の合計は` の `合計` を階層と読んで
# 「階層 合計 に候補が 0 件」で保留にした。**文が言っていない制約を作ってはいけない。**
LEVEL_CUES = ("款", "項", "目")
# ただし `会計`・`合計` は**覆い隠す語**としては残す(F-2)。外すと `合計` の中の `計` が
# 列の手がかりとして採られ、`歳入決算額の合計は` が「列が 2 つ」で保留になった(実測)。
# **覆い隠すこと(mask)と手がかりにすること(cue)は別の役目である。**
MASK_WORDS = ("会計", "合計", "款", "項", "目")
FIELDS6 = ("scope", "level", "parent", "name", "column")
MIN_INDEPENDENT = 3          # 封 §4-1。**人間が決めた数。字で留める**


# ------------------------------------------------------- C-9 索引に親を足す
def build_index(soukatu, kessan, meisai):
    """凍結版と**同じ順・同じ欄**の索引に `parent` を足す(門 IndexParityTest で同値)。

    **参照(`D10` のような文字列)で親を引いてはいけない。**明細は 22 枚の sheet が
    同じ `file` 名を持つので、参照が sheet をまたいで衝突する(実測で目の親が
    別の sheet の款になった)。だから**その場で親を決める。**
    """
    entries = []

    def add(parent=None, **kw):
        kw["parent"] = parent
        entries.append(kw)

    for a in soukatu["accounts"]:
        for col, v in a["values"].items():
            if v is None:
                continue
            ev = a["value_rows"][col]
            add(scope=a["name"], level="会計", name=a["name"], column=col, value=v,
                file="総括", code=None,
                evidence={"scope_from": "総括の会計の行", "name_ref": a["name_ref"],
                          "value_ref": ev["value_ref"], "header_ref": ev["header_ref"],
                          "sign_ref": ev.get("sign_ref")},
                children=None)
    for b in kessan["blocks"]:
        kids_by_kan = {}
        for it in b["items"]:
            kids_by_kan.setdefault(it.get("parent_row"), []).append(it)
        kan_name_by_row = {k["row"]: k.get("name") for k in b["kan"]}
        for k in b["kan"]:
            for col, v in k["values"].items():
                if v is None:
                    continue
                kids = kids_by_kan.get(k["row"], [])
                add(scope=b["account"], level="款", name=k.get("name"), code=k.get("code"),
                    column=col, value=v, file="決算書 歳出",
                    evidence={"scope_from": "決算書のブロックの表題行",
                              "code_ref": k.get("code_ref"), "name_ref": k.get("name_ref"),
                              "value_ref": k["evidence"][col]["value_ref"],
                              "header_ref": k["evidence"][col]["header_ref"]},
                    children=[{"name": c.get("name"), "value": c["values"].get(col),
                               "value_ref": (c["evidence"].get(col) or {}).get("value_ref")}
                              for c in kids])
        for it in b["items"]:
            for col, v in it["values"].items():
                if v is None:
                    continue
                add(scope=b["account"], level="項", name=it.get("name"), code=it.get("code"),
                    column=col, value=v, file="決算書 歳出",
                    parent=kan_name_by_row.get(it.get("parent_row")),
                    evidence={"scope_from": "決算書のブロックの表題行",
                              "code_ref": it.get("code_ref"), "name_ref": it.get("name_ref"),
                              "value_ref": it["evidence"][col]["value_ref"],
                              "header_ref": it["evidence"][col]["header_ref"]},
                    children=None)
        if b["total"]:
            for col, v in b["total"]["values"].items():
                if v is None:
                    continue
                add(scope=b["account"], level="合計", name="歳出合計", code=None,
                    column=col, value=v, file="決算書 歳出",
                    evidence={"scope_from": "決算書のブロックの表題行",
                              "name_ref": b["total"].get("name_ref"),
                              "value_ref": b["total"]["evidence"][col]["value_ref"],
                              "header_ref": b["total"]["evidence"][col]["header_ref"]},
                    children=[{"name": k.get("name"), "value": k["values"].get(col),
                               "value_ref": k["evidence"][col]["value_ref"]}
                              for k in b["kan"] if col in k["values"]])
    for s in meisai["sheets"]:
        # **この sheet の中だけ**で親を決める(行の順。参照では引かない)
        kan_rows = sorted((x["row"], x.get("name")) for x in s["kan"])
        item_rows = sorted((x["row"], x.get("name")) for x in s["items"])

        def _before(rows, r):
            hit = [n for rr, n in rows if rr < r]
            return hit[-1] if hit else None

        for level, rows in (("款", s["kan"]), ("項", s["items"]), ("目", s["moku"])):
            for x in rows:
                if level == "項":
                    par = _before(kan_rows, x["row"])
                elif level == "目":
                    kan, ko = _before(kan_rows, x["row"]), _before(item_rows, x["row"])
                    par = "%s > %s" % (kan, ko) if (kan and ko) else (kan or ko)
                else:
                    par = None
                for col, v in x["values"].items():
                    if v is None:
                        continue
                    add(scope=s["account"], level=level, name=x.get("name"),
                        code=x.get("code"), column=col, value=v, file="事項別明細",
                        parent=par,
                        evidence={"scope_from": "明細の目次(シート名と会計名)",
                                  "code_ref": x.get("code_ref"), "name_ref": x.get("name_ref"),
                                  "value_ref": (x["evidence"].get(col) or {}).get("value_ref"),
                                  "sign_ref": (x["evidence"].get(col) or {}).get("sign_ref")},
                        children=None)
    return entries


def fix_total_level(entries):
    """封 §1-2(C-4)。**総括の合計の行は階層も `合計`** にする。

    凍結版の索引は総括の全行を `会計` にしていた。封は「会計 = `合計` / 階層 = `合計`」と
    決めたので、**engine 側も同じ字を出す**(封 §1-2 の最後の行)。
    索引の他の欄は触らない(門 IndexParityTest は `build_index` に当たる)。
    """
    out = []
    for e in entries:
        if e["file"] == "総括" and norm(e["name"]) == norm("合計"):
            e = dict(e)
            e["level"] = "合計"
        out.append(e)
    return out


def duplication_report(entries):
    """封 §1-3・U-4。**6 欄で何行が重なるかを、生成の前に数える。**"""
    groups = collections.defaultdict(set)
    for e in entries:
        groups[tuple(norm(e[f]) or "" for f in FIELDS6)].add(e["value"])
    per_level = collections.defaultdict(int)
    worst = {}
    for key, vals in groups.items():
        lv = key[1]
        if len(vals) > per_level[lv]:
            per_level[lv] = len(vals)
            worst[lv] = {"key": list(key), "distinct_values": len(vals)}
    return {"max_distinct_values_per_level": dict(per_level), "worst": worst,
            "levels_not_unique": sorted(lv for lv, n in per_level.items() if n > 1)}


# ------------------------------------------- 別名: 独立した裏づけ(封 §4-2)
def alias_table(entries):
    """I-1〜I-4 を満たす裏づけを数え、**3 本以上・食い違い 0** のときだけ通す。"""
    canon = sorted({e["scope"] for e in entries if e["file"] in ("総括", "決算書 歳出")})
    others = sorted({e["scope"] for e in entries if e["scope"] not in canon})
    rows = {}
    for e in entries:
        if e["name"] and e["level"] in ("款", "項"):
            k = (e["scope"], e["level"], norm(e["name"]), norm(e["column"]))
            rows.setdefault(k, {"files": {}, "parent": e["parent"]})
            rows[k]["files"][e["file"]] = e["value"]

    table, unconfirmed = {}, []
    for x in others:
        ends = [c for c in canon if norm(x) != norm(c) and norm(x).endswith(norm(c))]
        if len(ends) != 1:
            unconfirmed.append({"name": x, "why": "接尾一致が %d 件" % len(ends),
                                "candidates": ends, "independent": 0})
            continue
        c = ends[0]
        hits, mismatch = [], 0
        for (sc, lv, nm, col), rec in rows.items():
            if sc != x:
                continue
            other = rows.get((c, lv, nm, col))
            if not other:
                continue
            v = sorted(rec["files"].values())[0]
            w = sorted(other["files"].values())[0]
            files = set(rec["files"]) | set(other["files"])
            if v != w:
                mismatch += 1
            elif len(files) >= 2:                       # I-4 2 つの file をまたぐ
                hits.append({"level": lv, "name": nm, "column": col, "value": v,
                             "parent": norm(rec["parent"]) or None,
                             "files": sorted(files)})
        ind, why = _independent(hits)
        if mismatch or len(ind) < MIN_INDEPENDENT:
            unconfirmed.append({"name": x, "canonical": c,
                                "why": ("食い違い %d 件" % mismatch if mismatch
                                        else "独立した裏づけが %d 本(要 %d 本)"
                                             % (len(ind), MIN_INDEPENDENT)),
                                "independent": len(ind), "mismatch": mismatch,
                                "dropped": why})
            continue
        table[x] = {"canonical": c,
                    "evidence": {"接尾一致": [x, c], "独立した裏づけ": len(ind),
                                 "食い違い": 0,
                                 "裏づけの行": [h["name"] for h in ind][:20]}}
    fan_in = collections.defaultdict(list)
    for x, rec in table.items():
        fan_in[rec["canonical"]].append(x)
    return {"table": table, "unconfirmed": unconfirmed, "canonical": canon,
            "min_independent": MIN_INDEPENDENT,
            "fan_in": {k: v for k, v in fan_in.items() if len(v) > 1}}


def _independent(hits):
    """封 §4-2。I-1 名前で 1 本 / I-2 親子は 1 本 / I-3 同じ値は 1 本。"""
    dropped = []
    by_name = {}
    for h in hits:                                   # I-1 相異なる科目名
        if h["name"] not in by_name or h["level"] == "款":
            by_name.setdefault(h["name"], h)
    kept_names = set(by_name)
    step2 = []
    for h in by_name.values():                       # I-2 親子関係にない
        if h["level"] == "項" and h["parent"] and h["parent"] in kept_names:
            dropped.append({"name": h["name"], "why": "親 %s が既に数えられている"
                                                      % h["parent"]})
            continue
        step2.append(h)
    out, seen = [], set()
    for h in sorted(step2, key=lambda x: (x["level"] != "款", x["name"])):
        if h["value"] in seen:                       # I-3 値が互いに異なる
            dropped.append({"name": h["name"], "why": "同じ値 %d を既に数えている"
                                                      % h["value"]})
            continue
        seen.add(h["value"])
        out.append(h)
    return out, dropped


def canonicalize(entries, alias):
    """通った別名だけ正本の表記に直し、**落ちた別名には印をつける**(結ばないため)。"""
    table, bad = alias["table"], {u["name"] for u in alias["unconfirmed"]}
    out = []
    for e in entries:
        e = dict(e)
        rec = table.get(e["scope"])
        if rec:
            ev = dict(e["evidence"])
            ev["scope_as_written"] = e["scope"]
            ev["scope_alias_evidence"] = rec["evidence"]
            e["scope"], e["evidence"] = rec["canonical"], ev
            e["scope_unconfirmed"] = False
        else:
            e["scope_unconfirmed"] = e["scope"] in bad
        out.append(e)
    return out


# ------------------------------------------------------ C-8 階層の手がかり
def extract_claims(text, vocab, cues):
    """列(前の版のまま)に加えて**階層の手がかり**を拾う。区間の規則は同じ。"""
    claims, seen = [], set()
    vmap = dict(vocab)
    words = set(cues) | set(vmap) | {norm(w) for w in MASK_WORDS}
    for si, raw in enumerate(SENT.split(text)):
        s = raw.strip()
        if not s:
            continue
        sn = norm(s)
        if len(sn) != len(s):
            claims.append({"id": "R%03d" % (len(claims) + 1), "sentence_index": si,
                           "sentence": s, "skipped": "正規化で文字数が変わる"})
            continue
        depth = _depths(s)
        maximal = _maximal(_hits(sn, words))
        col_hits = [(a, b, cues[w]) for a, b, w in maximal if w in cues]
        lv_hits = [(a, b, w) for a, b, w in maximal
                   if w in {norm(x) for x in LEVEL_CUES} and w not in cues]
        name_hits = [(a, b, vmap[w]) for a, b, w in maximal if w in vmap]
        prev_end, last_col, last_lv = 0, {}, {}
        for m in AMOUNT.finditer(s):
            value, scale = amount_value(m.group(1), m.group(2))
            start, d = m.start(), depth[m.start()]
            column, col_amb = _cue(col_hits, prev_end, start, d, last_col)
            level, lv_amb = _cue(lv_hits, prev_end, start, d, last_lv)
            before_names = [(a, b, n) for a, b, n in name_hits if b <= start]
            subject = max(before_names, key=lambda x: x[0])[2] if before_names else None
            others = [n for _, _, n in name_hits if n != subject]
            key = (value, norm(subject), norm(column), norm(level),
                   tuple(col_amb or ()), tuple(lv_amb or ()))
            prev_end = m.end()
            if column is not None and not col_amb:
                last_col[d] = column
            if level is not None and not lv_amb:
                last_lv[d] = level
            if key in seen:
                continue
            seen.add(key)
            claims.append({"id": "R%03d" % (len(claims) + 1), "sentence_index": si,
                           "sentence": s, "text": m.group(0), "value": value,
                           "written_scale": scale, "subject": subject,
                           "subject_candidates": others[:6], "column": column,
                           "column_ambiguous": col_amb, "level": level,
                           "level_ambiguous": lv_amb, "paren_depth": d,
                           "scorable": bool(subject),
                           "undecidable": bool(subject) and len(set(
                               [norm(subject)] + [norm(o) for o in others])) > 1})
    return claims


def _cue(hits, prev_end, start, depth, last):
    """区間(直前の数の終わり〜この数)の手がかり。2 種類在れば**不定**。"""
    span = sorted({c for a, b, c in hits if a >= prev_end and b <= start})
    if len(span) >= 2:
        return None, span
    if span:
        return span[0], None
    return last.get(depth), None


# ------------------------------------------------------------------ 接続
def field_key(e):
    return tuple(norm(e[f]) or "" for f in FIELDS6)


def candidates(claim, entries):
    """名前で当て、**階層の語が在れば階層で絞る**。絞って 0 件なら逃げない(K-3)。"""
    sub = norm(claim["subject"])
    if not sub:
        return [], None, None
    exact = [e for e in entries if norm(e["name"]) == sub or norm(e["scope"]) == sub]
    kind = "完全一致" if exact else None
    if not exact:
        exact = [e for e in entries if norm(e["name"]) and norm(e["name"]) in sub]
        kind = "部分一致" if exact else None
    if claim.get("level") and exact:
        inside = [e for e in exact if norm(e["level"]) == norm(claim["level"])]
        if not inside:
            return [], kind, "階層 %s に候補が 0 件(他の階層へ落ちない)" % claim["level"]
        exact = inside
    if claim["column"]:
        narrowed = [e for e in exact if norm(e["column"]) == norm(claim["column"])]
        if narrowed:
            return narrowed, kind, None
    return exact, kind, None


def bind(claim, entries):
    res = {"claim_id": claim["id"], "route": None, "pointer": None, "recomputed": None,
           "range_identified": False, "value_match": False, "state": None,
           "evidence": None, "match_kind": None, "candidates": 0, "hold_reason": None}
    if claim.get("skipped"):
        res["state"], res["hold_reason"] = "UNVERIFIABLE", claim["skipped"]
        return res
    for field, what in (("column_ambiguous", "列"), ("level_ambiguous", "階層")):
        if claim.get(field):
            res["state"] = "UNVERIFIABLE"
            res["hold_reason"] = ("%s の手がかりが 2 つ以上: %s"
                                  % (what, "・".join(claim[field])))
            return res
    cands, kind, blocked = candidates(claim, entries)
    res["match_kind"], res["candidates"] = kind, len(cands)
    if blocked:
        res["state"], res["hold_reason"] = "UNVERIFIABLE", blocked
        return res
    if cands:
        keys = {}
        for e in cands:
            keys.setdefault(field_key(e), []).append(e)
        if len(keys) > 1:
            res["state"] = "UNVERIFIABLE"
            res["hold_reason"] = "6 欄が一意でない(%d 通り。値で選ばない)" % len(keys)
            res["distinct_keys"] = len(keys)
            return res
        group = list(keys.values())[0]
        if any(e.get("scope_unconfirmed") for e in group):
            res["state"] = "UNVERIFIABLE"
            res["hold_reason"] = ("会計が未確認の別名(独立した裏づけ %d 本未満。"
                                  "値が合っても結ばない)" % MIN_INDEPENDENT)
            res["unconfirmed_scope"] = group[0]["scope"]
            return res
        if len({e["value"] for e in group}) > 1:
            res["state"] = "UNVERIFIABLE"
            res["hold_reason"] = ("同じ欄の値が file 間で食い違う: %s"
                                  % sorted({e["value"] for e in group}))
            res["duplicates"] = len(group)
            return res
        res["range_identified"] = True
        res["duplicates"] = len(group)
        chosen = pick(group)
        if chosen["value"] == claim["value"]:
            return done(res, "R-1", chosen, chosen["value"], group)
        if chosen.get("children"):
            vals = [c["value"] for c in chosen["children"]]
            if vals and all(v is not None for v in vals) and sum(vals) == claim["value"]:
                r = done(res, "R-3", chosen, sum(vals), group)
                r["evidence"] = dict(r["evidence"])
                r["evidence"]["included"] = [c["value_ref"] for c in chosen["children"]]
                r["evidence"]["excluded"] = [{"ref": chosen["evidence"].get("value_ref"),
                                              "why": "親自身の値(二重計上の防止)"}]
                return r
        u = claim["written_scale"]
        if u > 1:
            v, t = chosen["value"], claim["value"]
            if abs(v - t) <= u / 2.0 or 0 <= v - t < u:
                return done(res, "R-4", chosen, v, group)
        res["state"] = "VALUE_MISMATCH"
        res["pointer"] = pointer_of(chosen)
        res["evidence"] = chosen["evidence"]
        res["recomputed"] = chosen["value"]
        return res
    value_only = [e for e in entries if e["value"] == claim["value"]]
    res["value_match"] = bool(value_only)
    res["state"] = "UNVERIFIABLE" if value_only else "POINTER_NOT_FOUND"
    res["value_only_hits"] = len(value_only)
    if value_only:
        res["hold_reason"] = "主語が表の名前に当たらない(値だけでは結ばない)"
    return res


def done(res, route, entry, recomputed, group):
    res.update({"route": route, "pointer": pointer_of(entry), "recomputed": recomputed,
                "value_match": True, "state": "GROUNDED"})
    res["evidence"] = dict(entry["evidence"])
    res["evidence"].update({"scope": entry["scope"], "level": entry["level"],
                            "parent": entry["parent"], "name": entry["name"],
                            "column": entry["column"], "value": entry["value"]})
    if len(group) > 1:
        res["evidence"]["duplicate_pointers"] = [pointer_of(e) for e in group]
    return res


def run(text, soukatu, kessan, meisai):
    raw = fix_total_level(build_index(soukatu, kessan, meisai))
    al = alias_table(raw)
    entries = canonicalize(raw, al)
    cues = column_cues(entries)
    vocab = vocabulary(entries)
    claims = extract_claims(text, vocab, cues)
    binds = [bind(c, entries) for c in claims]
    return {"entries": len(entries), "vocabulary": len(vocab), "column_cues": len(cues),
            "alias": al, "duplication": duplication_report(entries),
            "claims": claims, "binds": binds}
