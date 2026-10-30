# -*- coding: utf-8 -*-
"""段 4 の engine ― **直した版**(封 docs/DOMAIN1_FIX_PREDICTION_SEAL_2026-10-15.md §2)。

**凍結した `sheet_m4_engine_2026-10-15.py`(`1378ec8`)は 1 バイトも触らない。**
あれは失敗を出した engine の記録そのものなので、別 file にする。

直した 6 点(封 §2。**閾値・帯・ルートの順位・科目名の照合は触っていない**):
  F-1  列の手がかりは**最も近い**語(候補一覧の並び順ではない)
  F-2  手がかりは**その位置で最長の語**でなければ採らない(`会計` の中の `計` を採らない)
  F-3  **一意に同定できなければ結ばない**(4 欄が割れる / 列の手がかりが 2 つ)
  F-4  会計名の別名は**接尾一致 + 会計の層 + 値の裏づけ**の 3 条件(前方一致は認めない)
  F-5  主語も最長一致(`産業労働費` を `労働費` に負けさせない)
  F-6  列名の**曖昧でない接頭辞**(2 文字以上)も手がかりにする(`歳入` → `歳入決算額`)
"""
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "m2fx", os.path.join(HERE, "sheet_m2_structure_2026-10-15.py"))
M2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M2)
norm = M2.norm

_bspec = importlib.util.spec_from_file_location(
    "m4base", os.path.join(HERE, "sheet_m4_engine_2026-10-15.py"))
BASE = importlib.util.module_from_spec(_bspec)
_bspec.loader.exec_module(BASE)

# 凍結した版から**変えずに**使うもの(切り出しの土台・金額の読み方・索引の作り方)
UNIT = BASE.UNIT
AMOUNT = BASE.AMOUNT
PART = BASE.PART
SENT = BASE.SENT
amount_value = BASE.amount_value
build_index = BASE.build_index
pointer_of = BASE.pointer_of

LEVEL_WORDS = ("会計", "款", "項", "目", "合計")
FILE_ORDER = ("総括", "決算書 歳出", "事項別明細")  # F-3: 重複はこの順で採る(値で選ばない)
FIELDS = ("scope", "level", "name", "column")
OPEN, CLOSE = "（(", "）)"


# ------------------------------------------------------- F-4 会計名の別名表
def alias_table(entries):
    """会計名の別名を**材料から機械で**作る(封 §2 の F-4)。

    3 条件を全部満たしたときだけ同一と認める。
      1. 接尾一致(長い名前が短い名前で**終わる**)。**前方一致は認めない**
      2. どちらも**会計の層**の名前(款・項・目 の科目名は対象にしない)
      3. **値の裏づけ**: 同じ款の名前・同じ列で値が一致し、**食い違いが 0 件**
    条件 1 だけ通って 3 が通らないものは `未確認` に入れ、**別名として使わない。**
    """
    canon = sorted({e["scope"] for e in entries if e["file"] in ("総括", "決算書 歳出")})
    others = sorted({e["scope"] for e in entries if e["scope"] not in canon})
    kan = {}
    for e in entries:
        if e["level"] == "款" and e["name"]:
            kan.setdefault((e["scope"], norm(e["name"]), norm(e["column"])), e["value"])

    table, unconfirmed = {}, []
    for x in others:
        ends = [c for c in canon if norm(x) != norm(c) and norm(x).endswith(norm(c))]
        if len(ends) != 1:                      # 単射でなければ使わない
            unconfirmed.append({"name": x, "why": "接尾一致が %d 件" % len(ends),
                                "candidates": ends})
            continue
        c = ends[0]
        agree, mismatch = [], []
        for (sc, nm, col), v in kan.items():
            if sc != x:
                continue
            w = kan.get((c, nm, col))
            if w is None:
                continue
            (agree if w == v else mismatch).append({"款": nm, "列": col})
        if mismatch or not agree:
            unconfirmed.append({"name": x, "canonical": c, "why": "値の裏づけが無い",
                                "agree": len(agree), "mismatch": len(mismatch)})
            continue
        table[x] = {"canonical": c,
                    "evidence": {"接尾一致": [x, c], "一致した款と列": len(agree),
                                 "食い違い": 0}}
    seen = {}
    for x, rec in table.items():               # 単射の確認(2 つが同じ正本に向いてよい)
        seen.setdefault(rec["canonical"], []).append(x)
    return {"table": table, "unconfirmed": unconfirmed, "canonical": canon,
            "fan_in": {k: v for k, v in seen.items() if len(v) > 1}}


def canonicalize(entries, table):
    """索引の会計名を正本の表記に直す(**元の表記も証拠に残す**)。"""
    out = []
    for e in entries:
        rec = table.get(e["scope"])
        if rec:
            e = dict(e)
            ev = dict(e["evidence"])
            ev["scope_as_written"] = e["scope"]
            ev["scope_alias_evidence"] = rec["evidence"]
            e["scope"], e["evidence"] = rec["canonical"], ev
        out.append(e)
    return out


# --------------------------------------------- F-2/F-5/F-6 語の当て方
def column_cues(entries):
    """列の手がかり: **材料の見出しに在る列名**と、その曖昧でない接頭辞(2 文字以上)。"""
    cols = sorted({e["column"] for e in entries if e["column"]})
    cues = {norm(c): c for c in cols}
    pref = {}
    for c in cols:
        n = norm(c)
        for k in range(2, len(n)):
            pref.setdefault(n[:k], set()).add(c)
    for p, owners in pref.items():
        if len(owners) == 1 and p not in cues:          # F-6: 一意な接頭辞だけ
            cues[p] = sorted(owners)[0]
    return cues


def vocabulary(entries):
    """主語の手がかりに使う語(表に在る名前だけ)。"""
    names = {}
    for e in entries:
        if e["name"]:
            names.setdefault(norm(e["name"]), e["name"])
        names.setdefault(norm(e["scope"]), e["scope"])
    return sorted(names.items(), key=lambda kv: -len(kv[0]))


def _hits(sn, words):
    """`sn` の中の当たりを (開始, 終わり, 語) で全部返す。"""
    out = []
    for w in words:
        if not w:
            continue
        i = sn.find(w)
        while i >= 0:
            out.append((i, i + len(w), w))
            i = sn.find(w, i + 1)
    return out


def _maximal(hits):
    """**より長い語に覆われた当たりを捨てる**(F-2/F-5)。"""
    keep = []
    for a, b, w in hits:
        covered = any(c <= a and d >= b and (d - c) > (b - a) for c, d, _ in hits)
        if not covered:
            keep.append((a, b, w))
    return keep


def _depths(s):
    """1 文字ごとの括弧の深さ。"""
    out, d = [], 0
    for ch in s:
        if ch in OPEN:
            d += 1
            out.append(d)
        elif ch in CLOSE:
            out.append(d)
            d = max(0, d - 1)
        else:
            out.append(d)
    return out


# ------------------------------------------------------------------ 切り出し
def extract_claims(text, vocab, cues):
    """封 §3 の規則 + F-1/F-2/F-5/F-6/F-3(列の不定)。"""
    claims, seen = [], set()
    words = set(cues) | {k for k, _ in vocab} | {norm(w) for w in LEVEL_WORDS}
    for si, raw in enumerate(SENT.split(text)):
        s = raw.strip()
        if not s:
            continue
        sn = norm(s)
        if len(sn) != len(s):          # 正規化で位置がずれる文は扱わない(開示して止める)
            claims.append({"id": "R%03d" % (len(claims) + 1), "sentence_index": si,
                           "sentence": s, "skipped": "正規化で文字数が変わる"})
            continue
        depth = _depths(s)
        maximal = _maximal(_hits(sn, words))
        col_hits = [(a, b, cues[w]) for a, b, w in maximal if w in cues]
        name_hits = [(a, b, dict(vocab)[w]) for a, b, w in maximal if w in dict(vocab)]
        prev_end, last_by_depth = 0, {}
        for m in AMOUNT.finditer(s):
            value, scale = amount_value(m.group(1), m.group(2))
            start = m.start()
            d = depth[start]
            # F-1/F-3: 区間は「直前の数の終わり(無ければ文頭)からこの数の開始まで」
            span = [(a, b, c) for a, b, c in col_hits if a >= prev_end and b <= start]
            distinct = sorted({c for _, _, c in span})
            if len(distinct) >= 2:
                column, ambiguous = None, distinct          # F-3: 列が不定
            elif distinct:
                # F-1: 区間に在る手がかりは 1 種類しかないので、位置の比較は要らない
                # (`max`/`min` が同じ答えになることは試験 EquivalenceTest で固定する)
                column, ambiguous = distinct[0], None
            else:
                column, ambiguous = last_by_depth.get(d), None   # 同じ深さから引き継ぐ
            # F-5: 主語は数より前で最も近い名前(最長一致済み)
            before_names = [(a, b, n) for a, b, n in name_hits if b <= start]
            subject = max(before_names, key=lambda x: x[0])[2] if before_names else None
            others = [n for _, _, n in name_hits if n != subject]
            key = (value, norm(subject), norm(column), tuple(ambiguous or ()))
            prev_end = m.end()
            if column is not None and ambiguous is None:
                last_by_depth[d] = column
            if key in seen:
                continue
            seen.add(key)
            claims.append({"id": "R%03d" % (len(claims) + 1), "sentence_index": si,
                           "sentence": s, "text": m.group(0), "value": value,
                           "written_scale": scale, "subject": subject,
                           "subject_candidates": others[:6], "column": column,
                           "column_ambiguous": ambiguous, "paren_depth": d,
                           "scorable": bool(subject),
                           "undecidable": bool(subject) and len(set(
                               [norm(subject)] + [norm(o) for o in others])) > 1})
    return claims


# ------------------------------------------------------------------ 接続
def candidates(claim, entries):
    sub = norm(claim["subject"])
    if not sub:
        return [], None
    exact = [e for e in entries if norm(e["name"]) == sub or norm(e["scope"]) == sub]
    kind = "完全一致" if exact else None
    if not exact:
        exact = [e for e in entries if norm(e["name"]) and norm(e["name"]) in sub]
        kind = "部分一致" if exact else None
    if claim["column"]:
        narrowed = [e for e in exact if norm(e["column"]) == norm(claim["column"])]
        if narrowed:
            return narrowed, kind
    return exact, kind


def field_key(e):
    return tuple(norm(e[f]) or "" for f in FIELDS)


def pick(group):
    """4 欄が同じ候補(= 同じ論理セルの重複)から 1 つ採る。**順は先に決めてある。**"""
    return sorted(group, key=lambda e: (FILE_ORDER.index(e["file"])
                                        if e["file"] in FILE_ORDER else len(FILE_ORDER)))[0]


def bind(claim, entries):
    """仕様 §1 の順でルートを試す。**一意に同定できなければ結ばない**(F-3)。"""
    res = {"claim_id": claim["id"], "route": None, "pointer": None, "recomputed": None,
           "range_identified": False, "value_match": False, "state": None,
           "evidence": None, "match_kind": None, "candidates": 0, "hold_reason": None}
    if claim.get("skipped"):
        res["state"] = "UNVERIFIABLE"
        res["hold_reason"] = claim["skipped"]
        return res
    if claim.get("column_ambiguous"):
        res["state"] = "UNVERIFIABLE"
        res["hold_reason"] = "列の手がかりが 2 つ以上: %s" % "・".join(claim["column_ambiguous"])
        return res
    cands, kind = candidates(claim, entries)
    res["match_kind"], res["candidates"] = kind, len(cands)
    if cands:
        keys = {}
        for e in cands:
            keys.setdefault(field_key(e), []).append(e)
        if len(keys) > 1:
            res["state"] = "UNVERIFIABLE"
            res["hold_reason"] = ("4 欄が一意でない(%d 通り。値で選ばない)" % len(keys))
            res["distinct_keys"] = len(keys)
            res["range_identified"] = False
            return res
        group = list(keys.values())[0]
        if len({e["value"] for e in group}) > 1:
            # 同じ 4 欄なのに file 間で値が違う = 材料が食い違っている。**どちらも採らない**
            res["state"] = "UNVERIFIABLE"
            res["hold_reason"] = ("同じ欄の値が file 間で食い違う: %s"
                                  % sorted({e["value"] for e in group}))
            res["duplicates"] = len(group)
            return res
        res["range_identified"] = True
        res["duplicates"] = len(group)
        chosen = pick(group)
        # R-1 見出しで同定したセルの完全一致
        if chosen["value"] == claim["value"]:
            return done(res, "R-1", chosen, chosen["value"], group)
        # R-3 範囲の合計(式が無いときだけの別ルート。範囲の証拠が必須)
        if chosen.get("children"):
            vals = [c["value"] for c in chosen["children"]]
            if vals and all(v is not None for v in vals) and sum(vals) == claim["value"]:
                r = done(res, "R-3", chosen, sum(vals), group)
                r["evidence"] = dict(r["evidence"])
                r["evidence"]["included"] = [c["value_ref"] for c in chosen["children"]]
                r["evidence"]["excluded"] = [{"ref": chosen["evidence"].get("value_ref"),
                                              "why": "親自身の値(二重計上の防止)"}]
                return r
        # R-4 書かれた桁の帯(**帯は 1 単位。広げていない**)
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
    res["route"] = route
    res["pointer"] = pointer_of(entry)
    res["recomputed"] = recomputed
    res["value_match"] = True
    res["state"] = "GROUNDED"
    res["evidence"] = dict(entry["evidence"])
    res["evidence"].update({"scope": entry["scope"], "level": entry["level"],
                            "name": entry["name"], "column": entry["column"]})
    if len(group) > 1:
        res["evidence"]["duplicate_pointers"] = [pointer_of(e) for e in group]
    return res


def run(text, soukatu, kessan, meisai):
    raw = build_index(soukatu, kessan, meisai)
    al = alias_table(raw)
    entries = canonicalize(raw, al["table"])
    cues = column_cues(entries)
    vocab = vocabulary(entries)
    claims = extract_claims(text, vocab, cues)
    binds = [bind(c, entries) for c in claims]
    return {"entries": len(entries), "vocabulary": len(vocab), "column_cues": len(cues),
            "alias": al, "claims": claims, "binds": binds}
