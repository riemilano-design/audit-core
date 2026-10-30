# -*- coding: utf-8 -*-
"""段 7 の engine(封 docs/DOMAIN1_M7_SEAL_2026-10-15.md §2 の P-1〜P-7)。

**旧 engine(`sheet_m5_engine_2026-10-15.py`)は 1 byte も変えない。**
増分は「同じ報告文に旧と新を当てる」ことで測る(封 §4)。この file が新の側である。

足すのは**親の手がかり 1 つだけ。**列・階層・別名・ルートの順位・帯・6 欄の一意性は
旧のまま使う(`BASE` から取る)。

  P-1 親は**答えではなく、候補を絞る条件**。文から親の名前を合成しない
  P-2 手がかりの語は索引に在る名前だけ(旧の `vocabulary`)
  P-3 区間は列・階層と同じ。**引き継ぎはしない**(②は別の実験)
  P-4 「親の成分が**全部**手がかりに在る」ときだけ支持とする
  P-5 **支持が 1 つも無ければ絞らない**(親の無い行を既定にしない。款と項の双子は②へ)
  P-6 絞った後も 6 欄が 1 通りでなければ保留。**値では絞らない**
  P-7 親で絞った事実を**接続できたかに関係なく記録する**
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


OLD = _mod("m5_for_m7", "sheet_m5_engine_2026-10-15.py")
BASE = OLD.BASE
M2 = OLD.M2
norm = OLD.norm

# 旧からそのまま使う(**この file で定義し直さない**)
AMOUNT, SENT, amount_value = OLD.AMOUNT, OLD.SENT, OLD.amount_value
LEVEL_CUES, MASK_WORDS, FIELDS6 = OLD.LEVEL_CUES, OLD.MASK_WORDS, OLD.FIELDS6
MIN_INDEPENDENT = OLD.MIN_INDEPENDENT
_hits, _maximal, _depths, _cue = OLD._hits, OLD._maximal, OLD._depths, OLD._cue
column_cues, vocabulary = OLD.column_cues, OLD.vocabulary
build_index, fix_total_level = OLD.build_index, OLD.fix_total_level
alias_table, canonicalize = OLD.alias_table, OLD.canonicalize
duplication_report = OLD.duplication_report
field_key, pointer_of, pick, done = OLD.field_key, OLD.pointer_of, OLD.pick, OLD.done


def parent_components(parent):
    """`款名 > 項名` を成分に割る。**成分が 0 個なら親を持たない行**(会計・合計・款)。"""
    return [norm(x.strip()) for x in (parent or "").split(">") if x.strip()]


# ------------------------------------------------------------------ 切り出し
def extract_claims(text, vocab, cues):
    """旧の切り出しに **`parent_cues` を足すだけ**(P-3)。

    旧と同じ欄は 1 つも変えない(門 `ExtractParityTest` が同値を約束する)。
    `parent_cues` = 区間(直前の金額の終わり〜この金額)に在り、
    **かつ主語より前で終わる**名前。区間に無ければ**空**にする(**使い回さない**)。
    """
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
            top = max(before_names, key=lambda x: x[0]) if before_names else None
            subject = top[2] if top else None
            others = [n for _, _, n in name_hits if n != subject]
            # ---- P-3 親の手がかり(区間の中・主語より前)。**引き継がない**
            pcues = sorted({n for a, b, n in name_hits
                            if a >= prev_end and top is not None and b <= top[0]})
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
                           "parent_cues": pcues,
                           "scorable": bool(subject),
                           "undecidable": bool(subject) and len(set(
                               [norm(subject)] + [norm(o) for o in others])) > 1})
    return claims


# ------------------------------------------------------------------ 親で絞る
def narrow_by_parent(claim, cands):
    """P-1・P-4・P-5。**絞ったかどうかと、残った親を返す**(P-7 の記録のため)。"""
    cues = {norm(x) for x in (claim.get("parent_cues") or [])}
    info = {"parent_cues": sorted(claim.get("parent_cues") or []),
            "parent_filtered": False, "parent_kept": [],
            "parent_before": len(cands), "parent_after": len(cands)}
    if not cues or not cands:
        return cands, info
    supported = [e for e in cands
                 if parent_components(e["parent"])
                 and all(c in cues for c in parent_components(e["parent"]))]
    if not supported:
        # P-5 **支持が無ければ絞らない。**親の無い行を既定にしない
        return cands, info
    info["parent_filtered"] = True
    info["parent_after"] = len(supported)
    info["parent_kept"] = sorted({e["parent"] for e in supported})
    return supported, info


def candidates(claim, entries):
    """旧の絞り込みに**親の絞り込みを足す**。旧の返り値の形は変えない。"""
    cands, kind, blocked = OLD.candidates(claim, entries)
    if blocked:
        return cands, kind, blocked, {"parent_cues": sorted(claim.get("parent_cues") or []),
                                      "parent_filtered": False, "parent_kept": [],
                                      "parent_before": len(cands),
                                      "parent_after": len(cands)}
    cands, info = narrow_by_parent(claim, cands)
    return cands, kind, blocked, info


def bind(claim, entries):
    """旧の `bind` と同じ順・同じ判定。**候補の集合だけが親で絞られている。**

    P-7: 親の記録は、保留でも誤接続でも**必ず**付ける。
    """
    res = {"claim_id": claim["id"], "route": None, "pointer": None, "recomputed": None,
           "range_identified": False, "value_match": False, "state": None,
           "evidence": None, "match_kind": None, "candidates": 0, "hold_reason": None,
           "parent_cues": sorted(claim.get("parent_cues") or []),
           "parent_filtered": False, "parent_kept": [],
           "parent_before": None, "parent_after": None}
    if claim.get("skipped"):
        res["state"], res["hold_reason"] = "UNVERIFIABLE", claim["skipped"]
        return res
    for field, what in (("column_ambiguous", "列"), ("level_ambiguous", "階層")):
        if claim.get(field):
            res["state"] = "UNVERIFIABLE"
            res["hold_reason"] = ("%s の手がかりが 2 つ以上: %s"
                                  % (what, "・".join(claim[field])))
            return res
    cands, kind, blocked, info = candidates(claim, entries)
    res.update(info)
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
