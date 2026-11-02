# -*- coding: utf-8 -*-
u"""導出の検証の診断(前半): 候補の行 296 に固定した式の集合を当て、式ごとの一致を数える(封 docs/XBRL_DERIVATION_DIAG_SEAL_2026-11-02.md)。

読む材料は前の便の記録 fixtures/xbrl/delta_naming_2026-10-30.json(sha256 を封の値と照らす)1 本。
engine(core/・adapters/)は import しない。ZIP・cache・instance を開かない。通信しない。
記録 fixtures/xbrl/derivation_2026-11-02.json には docID・claim id・pointer を書かない(位置で引く)。

    python3 measure/xbrl_derivation_2026-11-02.py [--out fixtures/xbrl/derivation_2026-11-02.json]
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SEAL_REL = "docs/XBRL_DERIVATION_DIAG_SEAL_2026-11-02.md"
SEAL_COMMIT = "67efc7a"
INPUT_REL = "fixtures/xbrl/delta_naming_2026-10-30.json"
INPUT_SHA256 = "27aca660570ddb37e8d9d1bc4826d8d2cfef931e0120c2484d688a4fe449b78f"
PREV_REL = "fixtures/xbrl/delta_decimals_2026-11-01.json"      # F1 の再現にだけ使う(帯の中 50)
OUT_REL = "fixtures/xbrl/derivation_2026-11-02.json"

# 封 §1 の式の集合: 名前 → (要る fact, v の計算, t と u に掛ける倍率)
FORMULAS = collections.OrderedDict([
    (u"F1", ((u"c", u"p"), lambda c, p: c - p, 1.0)),
    (u"F3", ((u"c",), lambda c, p: c, 1.0)),
    (u"F4", ((u"p",), lambda c, p: p, 1.0)),
    (u"F5", ((u"c", u"p"), lambda c, p: c + p, 1.0)),
    (u"F1k", ((u"c", u"p"), lambda c, p: c - p, 1e3)),
    (u"F1m", ((u"c", u"p"), lambda c, p: c - p, 1e-3)),
    (u"F3k", ((u"c",), lambda c, p: c, 1e3)),
    (u"F3m", ((u"c",), lambda c, p: c, 1e-3)),
    (u"F4k", ((u"p",), lambda c, p: p, 1e3)),
    (u"F4m", ((u"p",), lambda c, p: p, 1e-3)),
])
SCALE_FORMULAS = (u"F1k", u"F1m", u"F3k", u"F3m", u"F4k", u"F4m")
STAGES = (u"完全一致", u"丸めの帯 H", u"丸めの帯 F", u"不一致", u"比較不能")
IN_BAND = (u"完全一致", u"丸めの帯 H", u"丸めの帯 F")
VERDICTS = (u"導出一致", u"保留", u"不一致", u"比較不能")
OUTSIDE_BEFORE = (u"不一致", u"比較不能")                      # 前の便(F1)で帯の外 = 母数 246
COPIED = (u"位置", u"期", u"member", u"単位", u"型", u"探索/検証", u"10 行", u"比較不能の理由")
FORBIDDEN_RECORD_KEYS = (u"span", u"文", u"段落", u"窓", u"ラベル", u"理由の自由文", u"pointers", u"named", u"doc", u"id")
KEY_PATTERNS = (r"sk-[A-Za-z0-9_\-]{10,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{20,}", r"xox[baprs]-[A-Za-z0-9\-]{10,}",
                r"-----BEGIN", r"Bearer [A-Za-z0-9._\-]{16,}", r"AIza[0-9A-Za-z_\-]{30,}")
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
CLAIM_ID_RE = re.compile(r"\bN\d{3}\b")


class Stop(SystemExit):
    pass


def sha256_file(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def g_of(dec):
    if dec is None:
        return None
    return float(10) ** (-int(dec))


def stage_of(e, G, H):
    if e == 0:
        return u"完全一致"
    if e <= H:
        return u"丸めの帯 H"
    if e <= G:
        return u"丸めの帯 F"
    return u"不一致"


def eval_formula(name, t, u, c, p, g_c, g_p):
    u"""1 つの式。要る fact が無ければ 比較不能。G = Σg + u'、H = G/2、e = | |v| − t' |。"""
    need, fn, scale = FORMULAS[name]
    facts = {u"c": (c, g_c), u"p": (p, g_p)}
    if any(facts[k][0] is None or facts[k][1] is None for k in need):
        return collections.OrderedDict([(u"段", u"比較不能"), (u"v", None), (u"G", None), (u"H", None), (u"e", None)])
    v = fn(c, p)
    t2, u2 = t * scale, u * scale
    G = sum(facts[k][1] for k in need) + u2
    H = G / 2.0
    e = abs(abs(v) - t2)
    return collections.OrderedDict([(u"段", stage_of(e, G, H)), (u"v", v), (u"G", G), (u"H", H), (u"e", e)])


def verdict_of(per_formula):
    stages = [x[u"段"] for x in per_formula.values()]
    if all(s == u"比較不能" for s in stages):
        return u"比較不能", []
    hit = [n for n, x in per_formula.items() if x[u"段"] in IN_BAND]
    if len(hit) == 1:
        return u"導出一致", hit
    if len(hit) >= 2:
        return u"保留", hit
    return u"不一致", hit


def build_rows(src_rows, prev_rows):
    u"""prev_rows = 前の便(decimals の帯の F1)の行。封 §2 の「前の便で帯の外」はこの便の段(不一致 230・比較不能 16 = 246)で見る。
    (2026-11-02 の最初の走らせは 1 つ前の naming の便の段を読んでいて母数が 257 になった。封の字に合わせて直した。)"""
    assert len(src_rows) == len(prev_rows)
    out = []
    for r, q in zip(src_rows, prev_rows):
        assert r[u"位置"] == q[u"位置"]
        t, u = r[u"文の値"], r[u"帯の幅"]
        c, p = r[u"当期の値"], (r[u"前期の値"] if r[u"前期の fact 在り"] else None)
        g_c, g_p = g_of(r[u"当期の decimals"]), g_of(r[u"前期の decimals"]) if r[u"前期の fact 在り"] else None
        row = collections.OrderedDict((k, r[k]) for k in COPIED)
        row[u"前の便の段"] = q[u"段"]                       # decimals の便(F1)の段
        row[u"前々便の段"] = r[u"段"]                       # naming の便(文の単位 1 つの帯)の段。参考
        row[u"文の値"] = t
        row[u"当期の値"] = c
        row[u"前期の値"] = p
        row[u"帯の幅"] = u
        row[u"当期の decimals"] = r[u"当期の decimals"]
        row[u"前期の decimals"] = r[u"前期の decimals"] if r[u"前期の fact 在り"] else None
        pf = collections.OrderedDict((n, eval_formula(n, t, u, c, p, g_c, g_p)) for n in FORMULAS)
        row[u"式"] = pf
        v, hit = verdict_of(pf)
        row[u"帯の中の式"] = hit
        row[u"判定"] = v
        row[u"前の便で帯の外"] = q[u"段"] in OUTSIDE_BEFORE          # decimals の便の段で見る(母数 246)
        row[u"新しく説明が付いた"] = row[u"前の便で帯の外"] and v in (u"導出一致", u"保留")
        out.append(row)
    return out


def _cnt(items):
    c = collections.Counter(items)
    return collections.OrderedDict(sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0]))))


def tally(rows):
    T = collections.OrderedDict()
    T[u"行"] = len(rows)
    T[u"式ごとの段"] = collections.OrderedDict(
        (n, collections.OrderedDict((s, sum(1 for r in rows if r[u"式"][n][u"段"] == s)) for s in STAGES)) for n in FORMULAS)
    T[u"式ごとの帯の中"] = collections.OrderedDict((n, sum(1 for r in rows if r[u"式"][n][u"段"] in IN_BAND)) for n in FORMULAS)
    T[u"判定"] = collections.OrderedDict((v, sum(1 for r in rows if r[u"判定"] == v)) for v in VERDICTS)
    outside = [r for r in rows if r[u"前の便で帯の外"]]
    T[u"前の便で帯の外の行(母数)"] = len(outside)
    new = [r for r in outside if r[u"新しく説明が付いた"]]
    T[u"新しく説明が付いた行"] = len(new)
    T[u"新しく説明が付いた行の判定"] = _cnt(r[u"判定"] for r in new)
    T[u"新しく説明が付いた行の型"] = _cnt(r[u"型"] for r in new)
    T[u"新しく説明が付いた行の単位"] = _cnt(r[u"単位"] for r in new)
    T[u"新しく説明が付いた行の式(導出一致)"] = _cnt(r[u"帯の中の式"][0] for r in new if r[u"判定"] == u"導出一致")
    T[u"新しく説明が付いた行の式の組(保留)"] = _cnt(u"+".join(r[u"帯の中の式"]) for r in new if r[u"判定"] == u"保留")
    T[u"母数のうち本便でも不一致"] = sum(1 for r in outside if r[u"判定"] == u"不一致")
    T[u"母数のうち本便でも比較不能"] = sum(1 for r in outside if r[u"判定"] == u"比較不能")
    T[u"母数のうち保留"] = sum(1 for r in outside if r[u"判定"] == u"保留")
    T[u"倍率の変種のどれかが帯の中(母数)"] = sum(1 for r in outside if any(r[u"式"][n][u"段"] in IN_BAND for n in SCALE_FORMULAS))
    T[u"母数のうち F3 が帯の中"] = sum(1 for r in outside if r[u"式"][u"F3"][u"段"] in IN_BAND)
    T[u"母数のうち F4 が帯の中"] = sum(1 for r in outside if r[u"式"][u"F4"][u"段"] in IN_BAND)
    T[u"母数のうち F5 が帯の中"] = sum(1 for r in outside if r[u"式"][u"F5"][u"段"] in IN_BAND)
    T[u"前の便で比較不能のうち F3 が帯の中"] = sum(1 for r in rows if r[u"前の便の段"] == u"比較不能" and r[u"式"][u"F3"][u"段"] in IN_BAND)
    T[u"導出一致の式(全行)"] = _cnt(r[u"帯の中の式"][0] for r in rows if r[u"判定"] == u"導出一致")
    T[u"導出一致の式(母数)"] = _cnt(r[u"帯の中の式"][0] for r in outside if r[u"判定"] == u"導出一致")
    T[u"新しく説明が付いた行の位置"] = [r[u"位置"] for r in new]
    # 追加の実測(封の予測の対象ではない): 母数の各行で、式のうち最も近いものの e / G(1 以下なら帯の中)。0 件の結果が
    # 「惜しい行も無い」のか「帯の幅だけの問題」なのかを見る。分位は昇順で floor(n × q) 番目の値。
    best = sorted(min(x[u"e"] / x[u"G"] for x in r[u"式"].values() if x[u"e"] is not None) for r in outside)
    n = len(best)
    T[u"母数の各行の最小 e/G"] = collections.OrderedDict([
        (u"min", round(best[0], 2)), (u"p10", round(best[n // 10], 2)), (u"p50", round(best[n // 2], 2)),
        (u"p90", round(best[9 * n // 10], 2)), (u"max", round(best[-1], 2)),
        (u"2 未満の行", sum(1 for v in best if v < 2)), (u"10 未満の行", sum(1 for v in best if v < 10))])
    T[u"母数の各行で最も近い式"] = _cnt(min(((x[u"e"] / x[u"G"], nme) for nme, x in r[u"式"].items() if x[u"e"] is not None))[1] for r in outside)
    return T


def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def judge(T):
    u"""封 §3 の字をそのまま規則にする(母数 246)。"""
    J = collections.OrderedDict()
    J[u"B-1"] = 0 <= T[u"母数のうち F3 が帯の中"] <= 10
    J[u"B-2"] = 5 <= T[u"母数のうち F4 が帯の中"] <= 30
    J[u"B-3"] = 0 <= T[u"母数のうち F5 が帯の中"] <= 3
    J[u"B-4"] = 3 <= T[u"倍率の変種のどれかが帯の中(母数)"] <= 20
    J[u"B-5"] = 10 <= T[u"新しく説明が付いた行"] <= 50
    J[u"B-6"] = 0 <= T[u"母数のうち保留"] <= 8
    J[u"B-7"] = 190 <= T[u"母数のうち本便でも不一致"] <= 236
    J[u"B-8"] = 0 <= T[u"前の便で比較不能のうち F3 が帯の中"] <= 4
    new = T[u"新しく説明が付いた行"]
    share = pct(T[u"新しく説明が付いた行の型"].get(u"増減の型", 0), new)
    J[u"B-9"] = (share is not None and share <= 30.0)
    top = list(T[u"導出一致の式(母数)"].items())
    J[u"B-10"] = bool(top) and top[0][0] == u"F4" and (len(top) == 1 or top[0][1] > top[1][1])
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    out[u"B-9 の割合"] = share
    return out


def wiring(src, sha, rows, prev):
    W = collections.OrderedDict()
    W[u"(a) 入力の sha256 が封の値"] = sha == INPUT_SHA256
    W[u"(b) 行が 296"] = len(rows) == 296 and len(src[u"行"]) == 296 and len(prev[u"行"]) == 296
    W[u"(b) 母数が 246"] = sum(1 for r in rows if r[u"前の便で帯の外"]) == 246
    f1 = collections.OrderedDict((s, sum(1 for r in rows if r[u"式"][u"F1"][u"段"] == s)) for s in STAGES)
    prev_stages = prev[u"集計"][u"全体"][u"stages"][u"段"] if u"全体" in prev[u"集計"] else prev[u"集計"][u"stages"][u"段"]
    W[u"(c) F1 の段が前の便の記録と同じ"] = all(f1.get(s, 0) == prev_stages.get(s, 0) for s in STAGES)
    W[u"(c) F1 の段"] = f1
    W[u"(c) 前の便の段"] = collections.OrderedDict((s, prev_stages.get(s, 0)) for s in STAGES)
    text = json.dumps(rows, ensure_ascii=False)
    W[u"(d) 記録に docID・claim id が無い"] = not DOCID_RE.search(text) and not CLAIM_ID_RE.search(text)
    W[u"(e) 全行に判定がちょうど 1 つ"] = all(r[u"判定"] in VERDICTS for r in rows)
    W[u"通った"] = all(v for k, v in W.items() if k.startswith(u"(") and isinstance(v, bool))
    return W


def record_key_leaks(obj):
    t = json.dumps(obj, ensure_ascii=False)
    return sorted(set(p for p in KEY_PATTERNS if re.search(p, t)))


def forbidden_keys(obj):
    bad = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in FORBIDDEN_RECORD_KEYS:
                    bad.add(k)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(obj)
    return sorted(bad)


def git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode().strip() if r.returncode == 0 else None


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % a.out)
    inp = os.path.join(ROOT, INPUT_REL)
    sha = sha256_file(inp)
    if sha != INPUT_SHA256:
        raise Stop(u"入力の sha256 が封と違う: %s" % sha)
    src = jload(inp)
    prev = jload(os.path.join(ROOT, PREV_REL))
    rows = build_rows(src[u"行"], prev[u"行"])
    T = tally(rows)
    rec = collections.OrderedDict()
    rec[u"注意"] = (u"候補の要素の 2 期の値から固定した式の集合で文の数字が導出できるかを数えた記録。式が当たっても出所として正しいとは"
                  u"言えない(偶然の一致を除いていない)。当たらなくても導出できないとは言えない(要素が違う可能性)。docID・claim id は書かない。")
    rec[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT}
    rec[u"HEAD の commit"] = git_head()
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"読んだ入力の sha256"] = sha
    rec[u"定数"] = collections.OrderedDict([
        (u"式", collections.OrderedDict((n, {u"fact": list(FORMULAS[n][0]), u"倍率": FORMULAS[n][2]}) for n in FORMULAS)),
        (u"G", u"式に使う fact の g の和 + u(倍率を掛けた u)"), (u"H", u"G / 2"), (u"e", u"| |v| − t'|"),
        (u"段", list(STAGES)), (u"帯の中", list(IN_BAND)), (u"判定", list(VERDICTS)), (u"母数", u"前の便(F1)で 不一致・比較不能 の行")])
    rec[u"配線の門"] = wiring(src, sha, rows, prev)
    rec[u"行"] = rows
    rec[u"集計"] = T
    rec[u"予測の判定"] = judge(T)
    rec[u"limits"] = [u"c・p は候補の要素(名前で選ばれた)の 2 期の値で、文が参照した要素とは限らない",
                     u"計算リンクの合算・増減率・一株あたりは測っていない", u"AI の文の 214 件は測っていない(後半の封)"]
    rec[u"key_leaks"] = record_key_leaks(rec)
    bad = forbidden_keys(rec)
    if bad:
        raise Stop(u"記録に禁じた key: %s" % bad)
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(dumps(rec))
    print(u"written: %s" % a.out)
    print(json.dumps(rec[u"配線の門"][u"通った"]), json.dumps(T[u"判定"], ensure_ascii=False))
    print(json.dumps(rec[u"予測の判定"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
