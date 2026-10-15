# -*- coding: utf-8 -*-
"""段 4 の engine: 報告文の主張を切り出し、表の範囲へ接続する(封 §3・仕様 §1/§4)。

**この file は報告文が存在する前に commit する**(封 §0 の ⑤)。
報告文を見てから切り出しや接続を変えないための順序である。

置き場所は `measure/`。`adapters/` に入れるのは、採用を決めてから独立監査を経て行う
(保護面を変える = 委任の条件 1)。

接続のルート(仕様 §1。**下位が上位を置き換えない**):
  R-1 見出しで同定したセルの完全一致
  R-2 式が示す範囲        … この材料には式が無いので**走らない**
  R-3 独立に特定した範囲の合計(式が無いときだけの別ルート。**範囲の証拠が必須**)
  R-4 書かれた桁の帯      … R-1〜R-3 が無いときだけ
  値が一致するだけのセルは**結ばない**(証拠が無ければ `UNVERIFIABLE`)
"""
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "m2", os.path.join(HERE, "sheet_m2_structure_2026-10-15.py"))
M2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M2)
norm = M2.norm

UNIT = {"兆": 10 ** 12, "億": 10 ** 8, "百万": 10 ** 6, "万": 10 ** 4, "千": 10 ** 3}
# 「2兆1,234億5,000万円」のような連結と、「1,234百万円」「5,000円」
AMOUNT = re.compile(r"((?:\d[\d,]*(?:兆|億|百万|万|千))+|\d[\d,]*)(兆|億|百万|万|千)?円")
PART = re.compile(r"(\d[\d,]*)(兆|億|百万|万|千)")
COLUMNS = ("歳入決算額", "歳出決算額", "差額", "予算現額", "支出済額",
           "翌年度繰越額", "不用額", "計")
SENT = re.compile(r"[。\n]")
LEVELS = ("会計", "款", "項", "目")


def amount_value(body, tail):
    """表記から円の値と、**書かれた桁**(帯の単位)を返す。"""
    if PART.search(body):
        total, smallest = 0, None
        for num, unit in PART.findall(body):
            total += int(num.replace(",", "")) * UNIT[unit]
            smallest = UNIT[unit]
        if tail:
            total *= UNIT[tail]
            smallest = UNIT[tail]
        return total, (smallest or 1)
    n = int(body.replace(",", ""))
    if tail:
        return n * UNIT[tail], UNIT[tail]
    return n, 1


# ------------------------------------------------------------------ 表の索引
def build_index(soukatu, kessan, meisai):
    """1 セル = 1 件の索引。**証拠(どのセルで同定したか)を全部持つ**(仕様 §2)。"""
    entries = []

    def add(**kw):
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
        for level, rows in (("款", s["kan"]), ("項", s["items"]), ("目", s["moku"])):
            for x in rows:
                for col, v in x["values"].items():
                    if v is None:
                        continue
                    add(scope=s["account"], level=level, name=x.get("name"),
                        code=x.get("code"), column=col, value=v, file="事項別明細",
                        evidence={"scope_from": "明細の目次(シート名と会計名)",
                                  "code_ref": x.get("code_ref"), "name_ref": x.get("name_ref"),
                                  "value_ref": (x["evidence"].get(col) or {}).get("value_ref"),
                                  "sign_ref": (x["evidence"].get(col) or {}).get("sign_ref")},
                        children=None)
    return entries


def vocabulary(entries):
    """主語の手がかりに使う語(表に在る名前だけ)。**長い名前を先に当てる。**"""
    names = {}
    for e in entries:
        if not e["name"]:
            continue
        names.setdefault(norm(e["name"]), e["name"])
        names.setdefault(norm(e["scope"]), e["scope"])
    return sorted(names.items(), key=lambda kv: -len(kv[0]))


# ------------------------------------------------------------------ 切り出し
def extract_claims(text, vocab):
    """封 §3 の規則で主張を切り出す。**報告文を見てから規則を変えない。**"""
    claims, seen = [], set()
    for si, raw in enumerate(SENT.split(text)):
        s = raw.strip()
        if not s:
            continue
        sn = norm(s)
        for m in AMOUNT.finditer(s):
            value, scale = amount_value(m.group(1), m.group(2))
            before = norm(s[:m.start()])
            # 主語の手がかり: 数より前にある最も近い名前(長い名前を優先)
            subject, subject_pos = None, -1
            for key, orig in vocab:
                p = before.rfind(key)
                if p > subject_pos or (p == subject_pos and subject and len(key) > len(norm(subject))):
                    if p >= 0:
                        subject, subject_pos = orig, p
            others = [orig for key, orig in vocab if key in sn and orig != subject]
            column = None
            for c in COLUMNS:
                p = before.rfind(norm(c))
                if p >= 0:
                    column = c if column is None else column
            key = (value, norm(subject), norm(column))
            if key in seen:
                continue
            seen.add(key)
            claims.append({"id": "R%03d" % (len(claims) + 1), "sentence_index": si,
                           "sentence": s, "text": m.group(0), "value": value,
                           "written_scale": scale, "subject": subject,
                           "subject_candidates": others[:6], "column": column,
                           "scorable": bool(subject),
                           "undecidable": bool(subject) and len(set(
                               [norm(subject)] + [norm(o) for o in others])) > 1})
    return claims


# ------------------------------------------------------------------ 接続
def candidates(claim, entries):
    """主語の手がかりが**表の名前に当たる**ものだけ(値では絞らない)。"""
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


def bind(claim, entries):
    """仕様 §1 の順でルートを試す。**下位のルートで上位を置き換えない。**"""
    cands, kind = candidates(claim, entries)
    res = {"claim_id": claim["id"], "route": None, "pointer": None, "recomputed": None,
           "range_identified": False, "value_match": False, "state": None,
           "evidence": None, "match_kind": kind, "candidates": len(cands)}
    if cands:
        res["range_identified"] = True
        # R-1 完全一致のセル
        for e in cands:
            if e["value"] == claim["value"]:
                return done(res, "R-1", e, e["value"])
        # R-3 範囲の合計(式が無いときだけの別ルート。証拠として子の参照を残す)
        for e in cands:
            if not e.get("children"):
                continue
            vals = [c["value"] for c in e["children"]]
            if vals and all(v is not None for v in vals) and sum(vals) == claim["value"]:
                r = done(res, "R-3", e, sum(vals))
                r["evidence"] = dict(r["evidence"] or {})
                r["evidence"]["included"] = [c["value_ref"] for c in e["children"]]
                r["evidence"]["excluded"] = [{"ref": e["evidence"].get("value_ref"),
                                              "why": "親自身の値(二重計上の防止)"}]
                return r
        # R-4 書かれた桁の帯(切り捨てと丸めの両方。帯は 1 単位)
        u = claim["written_scale"]
        if u > 1:
            for e in cands:
                v, t = e["value"], claim["value"]
                if abs(v - t) <= u / 2.0 or 0 <= v - t < u:
                    return done(res, "R-4", e, v)
        # 候補は在るが値が合わない
        res["state"] = "VALUE_MISMATCH"
        e = cands[0]
        res["pointer"] = pointer_of(e)
        res["evidence"] = e["evidence"]
        res["recomputed"] = e["value"]
        return res
    # 主語が表の名前に当たらない: 値だけ一致しても結ばない(仕様 §4)
    value_only = [e for e in entries if e["value"] == claim["value"]]
    res["value_match"] = bool(value_only)
    res["state"] = "UNVERIFIABLE" if value_only else "POINTER_NOT_FOUND"
    res["value_only_hits"] = len(value_only)
    return res


def done(res, route, entry, recomputed):
    res["route"] = route
    res["pointer"] = pointer_of(entry)
    res["recomputed"] = recomputed
    res["value_match"] = True
    res["state"] = "GROUNDED"
    res["evidence"] = dict(entry["evidence"])
    res["evidence"].update({"scope": entry["scope"], "level": entry["level"],
                            "name": entry["name"], "column": entry["column"]})
    return res


def pointer_of(entry):
    return "sheet:%s!%s" % (entry["file"], entry["evidence"].get("value_ref"))


def run(text, soukatu, kessan, meisai):
    entries = build_index(soukatu, kessan, meisai)
    vocab = vocabulary(entries)
    claims = extract_claims(text, vocab)
    binds = [bind(c, entries) for c in claims]
    return {"entries": len(entries), "vocabulary": len(vocab),
            "claims": claims, "binds": binds}
