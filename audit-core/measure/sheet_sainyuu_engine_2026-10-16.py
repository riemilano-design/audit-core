# -*- coding: utf-8 -*-
"""歳入側の裏づけを使う engine(封 docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md)。

**既存の engine は 1 文字も触らない。**この file だけが新しい。
変えるのは**別名表の作り方 1 か所だけ** ―
`alias_table` の独立した裏づけに、**歳入側の款の一致(R-独立-6 を当てたもの)**を足す。

  `MIN_INDEPENDENT` は engine の字をそのまま使う(**3**)。
  I-1〜I-4・A-規則-1/4/5・6 欄の鍵・親の規則・接続の経路は**一切変えない。**

**歳入側の裏づけは「同じ会計である」ことの証拠**であり、
「数が独立に観測された」ことの証拠ではない(P-2 §4)。
  usage: import して `run(text, soukatu, kessan, meisai)` を呼ぶ
"""
import collections
import importlib.util
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEAL = "docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md"
P1REC = os.path.join(ROOT, "fixtures", "sheet", "sainyuu_p1_2026-10-16.json")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


# **凍結した engine。**接続の経路はこちらを使う(段 9 の NEW と同じ)
M7 = _mod("m7_for_sainyuu", "sheet_m7_engine_2026-10-15.py")
P2 = _mod("p2_for_sainyuu", "sheet_sainyuu_p2_2026-10-16.py")
# `_independent` は凍結した m5 engine が持つ(m7 は再公開していない)
OLD = M7.OLD
M2 = M7.M2
norm = M2.norm
MIN_INDEPENDENT = M7.MIN_INDEPENDENT        # **人が決めた数。ここでは触らない**

_CACHE = {}


def sainyuu_backing():
    """会計ごとに「歳入側で採れた独立した値」を返す(R-独立-6 を当てたあと)。"""
    if "b" in _CACHE:
        return _CACHE["b"]
    p1 = json.load(io.open(P1REC, encoding="utf-8"))
    sk, _ = P2.P1M.read(P2.P1M.SAINYUU)
    sm, _ = P2.P1M.read(P2.P1M.MEISAI_SAINYUU)
    kk, _k = P2.kessan_kan(sk)
    mk, _m = P2.meisai_kan(sm, p1["meisai_sainyuu"]["toc"])
    det, _d = P2.determined_keys(kk)
    holders = P2.value_holders(kk)
    _CACHE["b"] = (kk, mk, det, holders)
    return _CACHE["b"]


def promote(mismatch, values, min_independent=None):
    """**昇格の判定を 1 か所に置く。**(通すか, 理由)を返す。

    `alias_table` の中にだけ書くと、この材料では
    「食い違い 0 件・全部 3 本以上」なので**判定を壊す変異が黙る**
    (2026-10-16 の変異 S2・S4 で実測)。**門が壊した入力で当てられるようにする。**
    """
    m = MIN_INDEPENDENT if min_independent is None else min_independent
    if mismatch:
        return False, "食い違い %d 件(A-規則-4。値が合っても通さない)" % mismatch
    if len(values) < m:
        return False, ("独立した裏づけが %d 本(要 %d 本。歳入側を足しても足りない)"
                       % (len(values), m))
    return True, None


def alias_table(entries, out_vals=None):
    """`M7.alias_table` の結果に**歳入側の裏づけを足して**作り直す。

    足すのは独立した裏づけの**本数**だけである。
    **接尾一致がちょうど 1 件(A-規則-1)・食い違い 0(A-規則-4)は変えない。**
    """
    base = M7.alias_table(entries)
    if out_vals is None:
        out_vals = collections.defaultdict(set)
        for e in entries:
            out_vals[norm(e["scope"])].add(e["value"])
    kk, mk, det, holders = sainyuu_backing()
    rows = {}
    for e in entries:
        if e["name"] and e["level"] in ("款", "項"):
            k = (e["scope"], e["level"], norm(e["name"]), norm(e["column"]))
            rows.setdefault(k, {"files": {}, "parent": e["parent"]})
            rows[k]["files"][e["file"]] = e["value"]

    table = dict(base["table"])
    still, promoted = [], []
    for u in base["unconfirmed"]:
        c = u.get("canonical")
        if not c:
            still.append(u)                      # 接尾一致が 1 件でない(A-規則-1)
            continue
        x = u["name"]
        hits = []
        for (sc, lv, nm, col), rec in rows.items():
            if sc != x:
                continue
            other = rows.get((c, lv, nm, col))
            if not other:
                continue
            v = sorted(rec["files"].values())[0]
            w = sorted(other["files"].values())[0]
            if v == w and len(set(rec["files"]) | set(other["files"])) >= 2:
                hits.append({"level": lv, "name": nm, "column": col, "value": v,
                             "parent": norm(rec["parent"]) or None,
                             "files": sorted(set(rec["files"]) | set(other["files"]))})
        ind_out, _ = OLD._independent(hits)
        sain, why = P2.judge_account(norm(x), norm(c), mk.get(norm(x), {}),
                                     kk.get(norm(c), {}), det, holders, out_vals)
        ind_in, _ = OLD._independent(sain)
        vals = {h["value"] for h in ind_out} | {h["value"] for h in ind_in}
        ok, reason = promote(u.get("mismatch") or 0, vals)
        if ok:
            table[x] = {"canonical": c,
                        "evidence": {"接尾一致": [x, c],
                                     "独立した裏づけ": len(vals),
                                     "食い違い": 0,
                                     "歳出側の本数": len(ind_out),
                                     "歳入側の本数": len(ind_in),
                                     "歳入側の列": sorted({h["column"] for h in ind_in}),
                                     "裏づけの行": [h["name"] for h in ind_in][:20]}}
            promoted.append({"name": x, "canonical": c,
                             "independent": len(vals),
                             "from_sainyuu": len(ind_in)})
        else:
            v = dict(u)
            v["why"] = reason
            v["independent"] = len(vals)
            v["sainyuu_dropped_why"] = why
            still.append(v)
    fan_in = collections.defaultdict(list)
    for x, rec in table.items():
        fan_in[rec["canonical"]].append(x)
    return {"table": table, "unconfirmed": still, "canonical": base["canonical"],
            "min_independent": MIN_INDEPENDENT,
            "fan_in": {k: v for k, v in fan_in.items() if len(v) > 1},
            "promoted_by_sainyuu": promoted,
            "note": ("**歳入側の裏づけは「同じ会計である」ことの証拠**であり、"
                     "数が独立に観測されたことの証拠ではない")}


def run(text, soukatu, kessan, meisai):
    """`M7.run` と**同じ順**で、別名表だけ差し替える。"""
    raw = M7.fix_total_level(M7.build_index(soukatu, kessan, meisai))
    al = alias_table(raw)
    entries = M7.canonicalize(raw, al)
    cues = M7.column_cues(entries)
    vocab = M7.vocabulary(entries)
    claims = M7.extract_claims(text, vocab, cues)
    binds = [M7.bind(c, entries) for c in claims]
    return {"entries": len(entries), "vocabulary": len(vocab),
            "column_cues": len(cues), "alias": al,
            "duplication": M7.duplication_report(entries),
            "claims": claims, "binds": binds}
