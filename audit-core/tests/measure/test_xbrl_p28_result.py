# -*- coding: utf-8 -*-
"""P28(「その他」の主語の結び直し O)の測定の結果の門。封 docs/XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02.md §7 の 2。

記録 5 つ(``fixtures/xbrl/p28/``: ai_prose・entry_output_ai_prose_p28・regress97・readings・zero_diag)から、封 §3 の予測 O-1〜O-7・N-1〜N-8 の判定と
§4 の採用の基準 K-1〜K-4 を**機械で求め**、結果の文書 ``docs/XBRL_OTHER_SUBJECT_ENGINE_RESULT_2026-11-02.md`` の表(``<!-- 門:start 名前 -->`` の中)を記録から作り直した表と
一行も違わないことを見る。縛るもの:

  a  記録の禁止欄(span・value・recomputed・文)が無い・key_leaks が空・cache の前後が同じ・docID が手元の 97 の一覧の中・script の sha256 が現物と一致・読みの指示文の字が script の定数と同じ。
  b  予測の判定(O・N)・採用の判定(K)を記録から求める。判定の関数は定数ではなく、記録を 1 つ変えると判定が変わる。
  c  文書の表 = 記録から作り直した表。門の外の散文は 3 桁以上の数を持たない(持つ行には【門なし】)。docID が文書に無い。
  d  zero_diag の記録の門: 分類の和 = 形が真の行、各 id が regress97 の形が真の一覧に在る、候補 0 の行の数が regress97 と同じ。
  i  順序: 封 S の commit ⊏ 実装 E ⊑ 記録・script・文書・門の commit ⊑ HEAD。封の commit は engine を触っていない。未 commit は赤(skip にしない)。
  g  変異: 記録の数・文書の 1 字・順序を壊した標本で赤になる。

この file は docID の字を持たない。
"""
import collections
import copy
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

SEAL_REL = "docs/XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02.md"
DOC_REL = "docs/XBRL_OTHER_SUBJECT_ENGINE_RESULT_2026-11-02.md"
SEAL_COMMIT_SHORT = "c6cbfae"
REC_REL = collections.OrderedDict([
    ("ai", "fixtures/xbrl/p28/ai_prose_2026-11-02.json"), ("entry", "fixtures/xbrl/p28/entry_output_ai_prose_p28_2026-11-02.json"),
    ("r97", "fixtures/xbrl/p28/regress97_2026-11-02.json"), ("read", "fixtures/xbrl/p28/readings_2026-11-02.json"), ("zero", "fixtures/xbrl/p28/zero_diag_2026-11-03.json")])
SCRIPT_REL = collections.OrderedDict([
    ("ai", "measure/xbrl_p28_ai_prose_2026-11-02.py"), ("r97", "measure/xbrl_p28_regress97_2026-11-02.py"), ("zero", "measure/xbrl_p28_zero_diag_2026-11-03.py")])
P27_R97_REL = "fixtures/xbrl/p27/regress97_2026-10-27.json"
GATE_FILES = ("tests/adapters/xbrl/test_recipes_p28.py", "tests/measure/test_xbrl_p28_seal.py", "tests/measure/test_xbrl_p28_result.py")
IMPL_FILES = ("adapters/xbrl/vocabulary.py", "adapters/xbrl/recipes.py")
NOT_GATED = u"【門なし】"
FORBIDDEN_KEYS = ("span", "value", "recomputed", u"文", u"理由")
HIT, MISS, NOJ = u"**当たり**", u"**外れ**", u"**判定しない**"
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
ALLOWED_DIRECTIONS = (("VALUE_MISMATCH", "GROUNDED"), ("UNVERIFIABLE", "GROUNDED"), ("POINTER_NOT_FOUND", "GROUNDED"))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def jload(rel):
    return json.loads(read(rel))


def sha256_rel(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load_script(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def records():
    return dict((k, jload(v)) for k, v in REC_REL.items())


# ---------------------------------------------------------------- 封の予測の字
def seal_rows(seal, start, end):
    u"""封の ``start`` 節から ``end`` 節までの表の行 {#: (予測, 外れ方)}。"""
    sec = seal[seal.index(start):seal.index(end)]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| \*\*([ON]-\d)\*\* \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            out[m.group(1)] = (cells[0], cells[1] if len(cells) > 1 else u"")
    return out


def seal_predictions(seal):
    P = seal_rows(seal, "### §3-1", "### §3-2")
    P.update(seal_rows(seal, "### §3-2", "## §4"))
    return P


# ---------------------------------------------------------------- 判定(記録から)
def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def judge_ai(ai, bounds):
    T = ai[u"集計"]
    rows = ai[u"行"]
    shape = [r for r in rows if r[u"形が真"]]
    decided = [r for r in shape if r[u"決まった"]]
    hold = [r for r in shape if r[u"候補"] is not None and r[u"候補"] >= 2 and not r[u"決まった"]]
    zero = [r for r in shape if r[u"候補"] == 0]
    moved = [r for r in rows if r[u"動いた"]]
    shape_ids = set(r[u"id"] for r in shape)
    expect = ai[u"定数"][u"O-4 の表"]
    o4_bad = [r[u"id"] for r in decided if r[u"id"] not in expect or [r[u"P28 の要素"], (r[u"P28 の context"] or u"")[:len(expect[r[u"id"]][1])]] != list(expect[r[u"id"]])]
    st27 = collections.Counter(r[u"P27 の state"] for r in rows)
    st28 = collections.Counter(r[u"P28 の state"] for r in rows)
    g = T[u"O-1 P27 の出力(engine の欄を除く sort_keys JSON)の sha256"]
    J = collections.OrderedDict()
    J["O-1"] = bool(g[u"一致"] and T[u"O-1 P27 の claims が記録 entry_output_ai_prose_p27 と欄ごとに一致"] and [st27[s] for s in STATES] == [340, 14, 33, 25])
    J["O-2"] = bounds["O-2"][0] <= len(shape) <= bounds["O-2"][1]
    J["O-3"] = bounds["O-3"][0] <= len(decided) <= bounds["O-3"][1]
    J["O-4"] = bool(decided) and not o4_bad
    J["O-5"] = bounds["O-5 保留"][0] <= len(hold) <= bounds["O-5 保留"][1] and bounds["O-5 候補 0"][0] <= len(zero) <= bounds["O-5 候補 0"][1]
    off_shape = [r for r in moved if r[u"id"] not in shape_ids]
    g_changed = [r for r in rows if r[u"P27 の state"] == "GROUNDED" and r[u"動いた"]]
    J["O-6"] = not off_shape and not g_changed and st27["GROUNDED"] == 340
    J["O-7"] = all(bounds["O-7"][s][0] <= st28[s] <= bounds["O-7"][s][1] for s in STATES)
    M = collections.OrderedDict()
    M["O-1"] = u"P27 の出力(engine の欄を除く)の sha256 が HEAD の engine と%s・記録 entry_output_ai_prose_p27 と%s。P27 の 4 state %s" % (
        u"一致" if g[u"一致"] else u"不一致", u"欄ごとに一致" if T[u"O-1 P27 の claims が記録 entry_output_ai_prose_p27 と欄ごとに一致"] else u"不一致", u"/".join(str(st27[s]) for s in STATES))
    M["O-2"] = u"形が真の行 %d" % len(shape)
    M["O-3"] = u"決まって GROUNDED になった行 %d(%s)" % (len(decided), u"・".join(r[u"id"] for r in decided))
    M["O-4"] = u"決まった行 %d のうち表と同じ %d。表と違う %d。表の行で決まらなかった %d" % (len(decided), len(decided) - len(o4_bad), len(o4_bad), len([i for i in expect if i not in [r[u"id"] for r in decided]]))
    M["O-5"] = u"候補 2 以上で保留の行 %d・候補 0 の行 %d(%s)" % (len(hold), len(zero), u"・".join(r[u"id"] for r in zero))
    M["O-6"] = u"形が偽の行で動いた行 %d・P27 で GROUNDED の行が替わった行 %d・P27 の GROUNDED %d" % (len(off_shape), len(g_changed), st27["GROUNDED"])
    M["O-7"] = u"P28 の 4 state GROUNDED %d・VALUE_MISMATCH %d・UNVERIFIABLE %d・POINTER_NOT_FOUND %d" % tuple(st28[s] for s in STATES)
    return J, M


def derive_97(r97):
    T = r97[u"集計"]
    shape = r97[u"形が真の行"]
    decided = [r for r in shape if r[u"決まった"]]
    moved = r97[u"動いた行"]
    shape_keys = set((r[u"docID"], r[u"id"]) for r in shape)
    d = collections.OrderedDict()
    d["n1"] = collections.OrderedDict((p, (v[u"byte が同じ書類"], v[u"書類"])) for p, v in r97[u"N-1"].items())
    d["shape"] = len(shape)
    d["shape_docs"] = len(set(r[u"docID"] for r in shape))
    d["decided"] = len(decided)
    d["decided_docs"] = len(set(r[u"docID"] for r in decided))
    d["hold"] = sum(1 for r in shape if r[u"候補"] is not None and r[u"候補"] >= 2 and not r[u"決まった"])
    d["moved"] = len(moved)
    d["dirs"] = collections.OrderedDict(sorted(collections.Counter(u"%s → %s" % (m[u"前の state"], m[u"後の state"]) for m in moved).items()))
    d["bad_dir"] = sum(1 for m in moved if (m[u"前の state"], m[u"後の state"]) not in ALLOWED_DIRECTIONS)
    d["g_ptr"] = sum(1 for r in shape if r[u"pointer だけ替わった"] and r[u"P27 の state"] == "GROUNDED" and r[u"P28 の state"] == "GROUNDED")
    d["g_leave"] = sum(1 for m in moved if m[u"前の state"] == "GROUNDED" and m[u"後の state"] != "GROUNDED")
    d["off_shape"] = sum(1 for m in moved if (m[u"docID"], m[u"id"]) not in shape_keys)
    d["r1"] = collections.OrderedDict((k, sum(1 for r in decided if r[u"R1"] == k)) for k in (u"同じ", u"違う", u"指せず"))
    d["r1_pct"] = pct(d["r1"][u"同じ"], len(decided))
    ev = d["r1"][u"同じ"] + d["r1"][u"違う"]
    d["r1_pct_ref"] = pct(d["r1"][u"同じ"], ev)
    d["no_subject"] = sum(1 for r in decided if r[u"主語なし(claim の subject が空)"])
    d["elements"] = collections.OrderedDict(sorted(collections.Counter(r[u"結んだ要素"] for r in decided).items()))
    d["states"] = copy.deepcopy(T[u"4 state"])
    return d


def judge_97(d):
    J = collections.OrderedDict()
    J["N-1"] = all(a == b == 97 for a, b in d["n1"].values()) and sorted(d["n1"]) == ["P22", "P26", "P27"]
    J["N-2"] = 40 <= d["shape"] <= 300
    J["N-3"] = 10 <= d["decided"] <= 120
    J["N-4"] = d["bad_dir"] == 0 and d["g_ptr"] == 0 and d["g_leave"] == 0 and d["off_shape"] == 0
    J["N-5"] = d["hold"] <= d["decided"]
    J["N-6"] = d["r1_pct"] is not None and d["r1_pct"] >= 85.0
    return J


def derive_read(rd):
    rows = rd[u"行"]
    n = len(rows)
    ok = sum(1 for r in rows if r[u"席 1"] == r[u"席 2"] == u"合う")
    other = sum(1 for r in rows if r[u"席 1"] == r[u"席 2"] == u"違う項目")
    unk = sum(1 for r in rows if u"判定不能" in (r[u"席 1"], r[u"席 2"]))
    dis = sum(1 for r in rows if r[u"席 1"] != r[u"席 2"])
    return collections.OrderedDict([("n", n), ("ok", ok), ("other", other), ("unk", unk), ("dis", dis), ("pct", pct(ok, n))])


def judge_k(ai_j, d97, jd, dr):
    J = collections.OrderedDict()
    J["K-1"] = bool(J_all(d97) and ai_j["O-1"] and d97["bad_dir"] == 0 and d97["off_shape"] == 0)
    J["K-2"] = bool(ai_j["O-3_n"] >= 6 and ai_j["O-4"])
    J["K-3"] = bool(dr["n"] and dr["other"] <= 1 and dr["pct"] >= 85.0)
    J["K-4"] = bool(d97["r1_pct"] is not None and d97["r1_pct"] >= 80.0)
    return J


def J_all(d97):
    return all(a == b == 97 for a, b in d97["n1"].values()) and sorted(d97["n1"]) == ["P22", "P26", "P27"]


def judge_7(dr):
    return bool(dr["n"] and dr["pct"] >= 90.0 and 0 <= dr["other"] <= 1)


def word(v):
    return HIT if v else MISS


def build_all(R, seal):
    u"""記録 R(dict)と封の字から、文書の表の全部と判定の全部。"""
    P = seal_predictions(seal)
    bounds = collections.OrderedDict()
    ai_bounds = R["ai"][u"定数"][u"予測の幅"]
    bounds["O-2"], bounds["O-3"] = ai_bounds["O-2"], ai_bounds["O-3"]
    bounds["O-5 保留"], bounds["O-5 候補 0"], bounds["O-7"] = ai_bounds["O-5 保留"], ai_bounds["O-5 候補 0"], ai_bounds["O-7"]
    Jo, Mo = judge_ai(R["ai"], bounds)
    d = derive_97(R["r97"])
    Jn = judge_97(d)
    dr = derive_read(R["read"])
    Jn["N-7"] = judge_7(dr)
    n_decided = sum(1 for r in R["ai"][u"行"] if r[u"形が真"] and r[u"決まった"])
    Jk = judge_k(dict(Jo, **{"O-3_n": n_decided}), d, None, dr)
    Mn = collections.OrderedDict()
    Mn["N-1"] = u"byte が同じ書類: " + u"・".join(u"%s %d / %d" % (p, a, b) for p, (a, b) in d["n1"].items())
    Mn["N-2"] = u"形が真の行 %d(%d 書類)" % (d["shape"], d["shape_docs"])
    Mn["N-3"] = u"決まって GROUNDED になった行 %d(%d 書類)" % (d["decided"], d["decided_docs"])
    Mn["N-4"] = u"動いた行 %d(向き: %s)・許す向き以外 %d・GROUNDED のまま pointer が替わる行 %d・GROUNDED を離れる行 %d・形が偽の行で動いた行 %d" % (
        d["moved"], u"、".join(u"%s %d" % kv for kv in d["dirs"].items()) or u"なし", d["bad_dir"], d["g_ptr"], d["g_leave"], d["off_shape"])
    Mn["N-5"] = u"候補 2 以上で保留の行 %d ≤ 決まった行 %d" % (d["hold"], d["decided"])
    Mn["N-6"] = u"決まった行の R1: 同じ %d・違う %d・指せず %d。割合 %s%%(分母 = 決まった行の全部 %d)。参考(分母 = E の取れた行だけ) %s" % (
        d["r1"][u"同じ"], d["r1"][u"違う"], d["r1"][u"指せず"], d["r1_pct"], d["decided"], (u"%s%%" % d["r1_pct_ref"]) if d["r1_pct_ref"] is not None else u"なし(分母 0)")
    Mn["N-7"] = u"読んだ行 %d(分母 %d)・2 席とも合う %d・2 席とも違う項目 %d・どちらかが判定不能 %d・2 席の答えが違う行 %d。2 席とも合う割合 %s%%" % (
        dr["n"], dr["n"], dr["ok"], dr["other"], dr["unk"], dr["dis"], dr["pct"])
    Mn["N-8"] = u"結んだ要素 %s。決まった行のうち主語なし(claim の subject が空) %d / %d。主語を条件にすると 97 書類の決まった行は %d" % (
        u"・".join(u"%s %d" % kv for kv in d["elements"].items()), d["no_subject"], d["decided"], d["decided"] - d["no_subject"])
    blocks = collections.OrderedDict()
    pa = [u"| # | 予測(封の字) | 外れ方(封の字) | 実測(記録から) | 当たり外れ |", u"|---|---|---|---|---|"]
    for k in ("O-%d" % i for i in range(1, 8)):
        pa.append(u"| **%s** | %s | %s | %s | %s |" % (k, P[k][0], P[k][1], Mo[k], word(Jo[k])))
    blocks["pred_ai"] = pa
    pn = [u"| # | 予測(封の字) | 外れ方(封の字) | 実測(記録から) | 当たり外れ |", u"|---|---|---|---|---|"]
    for k in ("N-%d" % i for i in range(1, 9)):
        pn.append(u"| **%s** | %s | %s | %s | %s |" % (k, P[k][0], P[k][1], Mn[k], NOJ if k == "N-8" else word(Jn[k])))
    blocks["pred_97"] = pn
    kk = [u"| # | 基準(封 §4 の見出し) | 実測(記録から) | 満たすか |", u"|---|---|---|---|"]
    kk.append(u"| **K-1** | 壊さない | N-1 %s・O-1 %s・N-4 の他の向き %d・形が偽の行で動いた行 %d | %s |" % (
        u"97 / 97 ×3" if J_all(d) else u"97 / 97 でない", u"byte 一致" if Jo["O-1"] else u"不一致", d["bad_dir"], d["off_shape"], u"はい" if Jk["K-1"] else u"いいえ"))
    kk.append(u"| **K-2** | 決める | O-3 = %d(6 以上)・O-4 %s | %s |" % (n_decided, u"全部同じ" if Jo["O-4"] else u"違いあり", u"はい" if Jk["K-2"] else u"いいえ"))
    kk.append(u"| **K-3** | 偽の一致を作らない | 読んだ行 %d(分母 %d)・2 席とも違う項目 %d(1 以下)・2 席とも合う %s%%(85%% 以上) | %s |" % (
        dr["n"], dr["n"], dr["other"], dr["pct"], u"はい" if Jk["K-3"] else u"いいえ"))
    kk.append(u"| **K-4** | 近傍なしで足りる | N-6 = %s%%(80%% 以上。分母 %d) | %s |" % (d["r1_pct"], d["decided"], u"はい" if Jk["K-4"] else u"いいえ"))
    adopt_not = not (Jk["K-1"] and Jk["K-2"] and Jk["K-3"])
    cand = all(Jk.values())
    kk.append(u"| **採用しない** | K-1〜K-3 のどれかが外れ | %s | %s |" % (u"K-1〜K-3 は全部満たす" if not adopt_not else u"K-1〜K-3 に満たさないものがある", u"いいえ" if not adopt_not else u"はい"))
    kk.append(u"| **既定の候補として記録** | K-1〜K-4 の全部 | %s | %s |" % (u"K-1〜K-4 の全部を満たす" if cand else u"K-4 を満たさないので全部ではない" if not Jk["K-4"] else u"満たさないものがある", u"はい" if cand else u"いいえ"))
    blocks["adopt"] = kk
    mv = [u"| 動いた行(AI の文) | 前の state | 後の state | 結んだ要素 | 期 |", u"|---|---|---|---|---|"]
    for r in R["ai"][u"行"]:
        if r[u"動いた"]:
            mv.append(u"| %s | %s | %s | %s | %s |" % (r[u"id"], r[u"P27 の state"], r[u"P28 の state"], r[u"P28 の要素"], r[u"P28 の期"]))
    blocks["moved_ai"] = mv
    z = R["zero"][u"集計"]
    zt = [u"| 分類(形が真の行。上から順に 1 つ) | 行 | うち候補 0 |", u"|---|---|---|"]
    cnt0 = z[u"候補 0 の行の分類"]
    for c, n in z[u"分類(形が真の 42 行。上から順に 1 つ)"].items():
        zt.append(u"| %s | %d | %s |" % (c, n, cnt0.get(c, u"―") if c in cnt0 else u"―"))
    zt.append(u"| 合計 | %d | %d |" % (z[u"形が真の行"], z[u"候補 0 の行"]))
    zt.append(u"| (b) の内訳: 数の直後 6 字に増減 / form が derived_value | %d / %d | |" % (z[u"(b) の内訳"][u"数の直後 6 字に増減"], z[u"(b) の内訳"][u"form が derived_value"]))
    zt.append(u"| (d) の内訳: member つきだけ / 別の期だけ / 両方 | %d / %d / %d | |" % tuple(z[u"(d) の内訳"].values()))
    blocks["zero"] = zt
    lo = z[u"緩めた字の内訳"]
    lt = [u"| 緩めた字(「その他」+数)で数えた件数 | 件 |", u"|---|---|", u"| 全部 | %d |" % z[u"緩めた字で数えた件数(97 書類の MD&A)"]]
    for k, v in lo.items():
        lt.append(u"| %s | %d |" % (k, v))
    blocks["loose"] = lt
    wt = [u"| 配線の門 | 値 |", u"|---|---|"]
    wt.append(u"| 手元の cache の件数(前 = 後) | %s |" % u"・".join(u"%s %d" % (k, v[u"件数"]) for k, v in R["r97"][u"cache の前後"][u"前"].items()))
    wt.append(u"| cache の前後が同じ(3 記録) | %s |" % (u"はい" if all(R[k][u"cache の前後"][u"変化なし"] for k in ("r97", "zero")) else u"いいえ"))
    wt.append(u"| AI の文の行の対応(同じ位置で鍵が同じ) | %d 行 / 対応しない %d |" % tuple(R["ai"][u"配線の門"][u"(e) 行の対応"].values()))
    wt.append(u"| 読みの指示文の sha256(script の定数 = 記録) | %s |" % R["read"][u"席の指示文の sha256"][:16])
    wt.append(u"| 読みに引いた行 / 決まった行 | %d / %d |" % (R["r97"][u"読みの行の引き方"][u"引いた行"], R["r97"][u"読みの行の引き方"][u"決まった行"]))
    wt.append(u"| 決まった行のうち主語なし(claim の subject が空): AI の文 / 97 書類 | %d / %d |" % (R["ai"][u"集計"][u"決まった行のうち主語なし(P28 の claim の subject が空)"], d["no_subject"]))
    blocks["wiring"] = wt
    et = [u"| engine の file(測った時点の作業木) | sha16 |", u"|---|---|"]
    for rel in IMPL_FILES:
        et.append(u"| `%s` | `%s` |" % (rel, sha256_rel(rel)[:16]))
    blocks["engine"] = et
    return blocks, Jo, Jn, Jk, d, dr


# ---------------------------------------------------------------- 文書
def doc_blocks(doc):
    out = collections.OrderedDict()
    for m in re.finditer(r"<!-- 門:start (\w+) -->\n(.*?)\n<!-- 門:end -->", doc, re.S):
        out[m.group(1)] = m.group(2).split("\n")
    return out


def outside_blocks(doc):
    return re.sub(r"<!-- 門:start \w+ -->\n.*?\n<!-- 門:end -->", u"", doc, flags=re.S)


def prose_problems(doc):
    u"""門の外の散文: 3 桁以上の数を持つ行には【門なし】が要る。コード片・日付・16 進・path・commit は除く。"""
    out = []
    for ln, line in enumerate(outside_blocks(doc).splitlines(), 1):
        t = re.sub(r"`[^`]*`", u"", line)
        t = re.sub(r"\d{4}-\d{2}-\d{2}", u"", t)
        t = re.sub(r"\b[0-9a-f]{7,}\b", u"", t)
        t = re.sub(r"https?://\S+|\S+\.(?:md|py|json)\b", u"", t)
        if re.search(r"\d{3,}", t) and NOT_GATED not in line:
            out.append((ln, line[:60]))
    return out


def doc_problems(doc, R, seal):
    blocks = build_all(R, seal)[0]
    got = doc_blocks(doc)
    out = []
    for k, lines in blocks.items():
        if got.get(k) != lines:
            out.append(u"表 %s が記録から作り直した表と違う" % k)
    for k in got:
        if k not in blocks:
            out.append(u"知らない表 %s" % k)
    if re.search(r"S100[0-9A-Z]{4}", doc):
        out.append(u"docID が文書にある")
    for w in (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社"):
        if w in doc:
            out.append(u"禁止語: " + w)
    out += [u"散文の数に【門なし】が無い: 行 %d %s" % x for x in prose_problems(doc)]
    return out


# ---------------------------------------------------------------- 記録
def record_problems(R, scripts, p27_docs):
    out = []
    for k, rec in R.items():
        if k == "entry":
            continue
        txt = json.dumps(rec, ensure_ascii=False)
        if rec.get(u"key_leaks"):
            out.append(u"%s: key_leaks が空でない" % k)
        def walk(o):
            if isinstance(o, dict):
                for kk, vv in o.items():
                    if kk in FORBIDDEN_KEYS:
                        out.append(u"%s: 禁止欄 %s" % (k, kk))
                    walk(vv)
            elif isinstance(o, list):
                for vv in o:
                    walk(vv)
        walk(rec)
        for m in re.finditer(r"S100[0-9A-Z]{4}", txt):
            if k in ("ai",):
                out.append(u"%s: docID が入っている" % k)
            elif m.group(0) not in p27_docs:
                out.append(u"%s: 97 の一覧に無い docID %s" % (k, m.group(0)))
    for k in ("r97", "zero"):
        if not R[k][u"cache の前後"][u"変化なし"]:
            out.append(u"%s: cache の前後が違う" % k)
    for k, rel in SCRIPT_REL.items():
        want = sha256_rel(rel)
        got = R[k][u"この script の sha256"] if k != "ai" else R["ai"][u"この script の sha256"]
        if got != want:
            out.append(u"%s: 記録の script の sha256 が現物と違う" % k)
    if R["read"][u"この script の sha256"] != sha256_rel(SCRIPT_REL["r97"]):
        out.append(u"read: 記録の script の sha256 が regress97 の script と違う")
    if R["read"][u"席の指示文の sha256"] != scripts["r97"].READER_PROMPT_SHA256 or hashlib.sha256(scripts["r97"].READER_PROMPT.encode("utf-8")).hexdigest() != scripts["r97"].READER_PROMPT_SHA256:
        out.append(u"read: 席の指示文の字が script の定数と違う")
    if R["r97"][u"読みの行の引き方"][u"席の指示文の sha256"] != scripts["r97"].READER_PROMPT_SHA256:
        out.append(u"r97: 席の指示文の sha256 が script の定数と違う")
    drawn = [tuple(x) for x in R["r97"][u"読みの行の引き方"][u"引いた行(docID, id)"]]
    read_keys = [(r[u"docID"], r[u"id"]) for r in R["read"][u"行"]]
    if drawn != read_keys:
        out.append(u"read: 読んだ行が r97 の引いた行と違う")
    dec = set((r[u"docID"], r[u"id"]) for r in R["r97"][u"形が真の行"] if r[u"決まった"])
    if not set(read_keys) <= dec:
        out.append(u"read: 読んだ行が決まった行の中に無い")
    if len(read_keys) != min(30, len(dec)):
        out.append(u"read: 読んだ行の数が min(30, 決まった行)でない")
    return out


def zero_problems(R):
    z, r97 = R["zero"], R["r97"]
    out = []
    rows = z[u"行"]
    keys = set((r[u"docID"], r[u"id"]) for r in r97[u"形が真の行"])
    if sorted((r[u"docID"], r[u"id"]) for r in rows) != sorted(keys) or len(rows) != len(keys):
        out.append(u"zero: 行の集合が regress97 の形が真の一覧と違う")
    cats = z[u"集計"][u"分類(形が真の 42 行。上から順に 1 つ)"]
    if sum(cats.values()) != r97[u"集計"][u"形が真の行"] or sum(cats.values()) != len(rows):
        out.append(u"zero: 分類の和が形が真の行と違う")
    zero_rows = [r for r in rows if r[u"候補"] == 0]
    if len(zero_rows) != r97[u"集計"][u"候補 0 の行(engine が GROUNDED にした行を含む)"] or z[u"集計"][u"候補 0 の行"] != len(zero_rows):
        out.append(u"zero: 候補 0 の行の数が regress97 と違う")
    if sum(z[u"集計"][u"候補 0 の行の分類"].values()) != len(zero_rows):
        out.append(u"zero: 候補 0 の行の分類の和が違う")
    by97 = dict(((r[u"docID"], r[u"id"]), r) for r in r97[u"形が真の行"])
    for r in rows:
        s = by97.get((r[u"docID"], r[u"id"]))
        if s is None or s[u"候補"] != r[u"候補"] or s[u"P27 の state"] != r[u"P27 の state"]:
            out.append(u"zero: 行が regress97 と合わない")
            break
        if (r[u"分類"] == u"決まった(候補 1)") != bool(s[u"決まった"]):
            out.append(u"zero: 決まった行の分類が regress97 と合わない")
            break
        if r[u"分類"] == u"(a) engine が P27 で GROUNDED" and r[u"P27 の state"] != "GROUNDED":
            out.append(u"zero: (a) なのに P27 が GROUNDED でない")
            break
    ids = z[u"集計"][u"各分類の id"]
    for c, lst in ids.items():
        if len(lst) != (cats[c] if c in cats else sum(1 for r in rows if r[u"分類"] == c)):
            out.append(u"zero: 分類 %s の id の数が違う" % c)
    if cats.get(u"(f) その他", 0) != 0:
        pass
    return out


# ---------------------------------------------------------------- 順序
def git_in(root, *args):
    r = subprocess.run(["git"] + list(args), cwd=root, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def added_commits(root, rel):
    return [c for c in git_in(root, "log", "--diff-filter=A", "--format=%H", "--", rel)[1].split() if c]


def is_anc(root, a, b):
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b], cwd=root, capture_output=True).returncode == 0


def order_problems(root, prefix, seal_rel, seal_short, impl_files, others):
    u"""封 S の commit ⊏ 実装 E ⊑ others の各 file を足した commit ⊑ HEAD。S が engine を触らない。未 commit は赤。"""
    out = []
    s = added_commits(root, prefix + seal_rel)
    if len(s) != 1:
        return [u"SEAL_ONCE"]
    seal = s[0]
    if not seal.startswith(seal_short):
        out.append(u"SEAL_NOT_THE_SEALED")
    if git_in(root, "diff", "--numstat", seal + "^", seal, "--", prefix + "adapters", prefix + "core")[1]:
        out.append(u"SEAL_TOUCHES_ENGINE")
    impl = []
    for rel in impl_files:
        lst = [c for c in git_in(root, "log", "--format=%H", seal + "..HEAD", "--", prefix + rel)[1].split() if c]
        if not lst:
            out.append(u"IMPL_UNCOMMITTED:" + rel)
        else:
            impl.append(lst[-1])
    if impl:
        e = impl[0]
        for c in impl:
            if is_anc(root, e, c):
                e = c
        if e == seal or not is_anc(root, seal, e):
            out.append(u"IMPL_NOT_AFTER_SEAL")
    else:
        e = None
    for rel in others:
        a = added_commits(root, prefix + rel)
        if not a:
            out.append(u"UNCOMMITTED:" + rel)
            continue
        c = a[-1]
        if c == seal or not is_anc(root, seal, c):
            out.append(u"BEFORE_SEAL:" + rel)
        elif e is not None and not is_anc(root, e, c):
            out.append(u"BEFORE_IMPL:" + rel)
        if not is_anc(root, c, "HEAD"):
            out.append(u"NOT_IN_HEAD:" + rel)
    return out


def order_others():
    return list(REC_REL.values()) + list(SCRIPT_REL.values()) + [DOC_REL] + list(GATE_FILES)


# ---------------------------------------------------------------- 試験
class Fixture(object):
    @classmethod
    def load(cls):
        cls.seal = read(SEAL_REL)
        cls.R = records()
        cls.scripts = dict((k, load_script(v, "p28_result_script_" + k)) for k, v in SCRIPT_REL.items() if k in ("ai", "r97"))
        cls.p27_docs = set(x[u"docID"] for x in jload(P27_R97_REL)[u"書類"]) if u"書類" in jload(P27_R97_REL) else set()


class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture.load()
        cls.F = Fixture

    def test_a_1_records_scripts_and_cache_are_clean(self):
        self.assertEqual(97, len(self.F.p27_docs))
        self.assertEqual([], record_problems(self.F.R, self.F.scripts, self.F.p27_docs))

    def test_a_2_the_97_documents_are_the_precedent_97(self):
        docs = sorted(d[u"docID"] for d in self.F.R["r97"][u"書類"])
        self.assertEqual(sorted(self.F.p27_docs), docs)

    def test_a_3_the_entry_has_no_docid_and_the_same_rows_as_the_record(self):
        txt = json.dumps(self.F.R["entry"], ensure_ascii=False)
        self.assertFalse(re.search(r"S100[0-9A-Z]{4}", txt))
        ids = [c["id"] for c in self.F.R["entry"]["claims"]]
        self.assertEqual(ids, [r[u"id"] for r in self.F.R["ai"][u"行"]])
        for c, r in zip(self.F.R["entry"]["claims"], self.F.R["ai"][u"行"]):
            self.assertEqual(c["state"], r[u"P28 の state"])

    def test_b_1_judgments_are_recomputed_and_equal_the_record_fields(self):
        _b, Jo, Jn, Jk, _d, _dr = build_all(self.F.R, self.F.seal)
        rec_ai = self.F.R["ai"][u"予測の判定"]
        for k, v in Jo.items():
            self.assertEqual(rec_ai[k], u"当たり" if v else u"外れ", k)
        rec_97 = self.F.R["r97"][u"予測の判定"]
        for k, v in Jn.items():
            if k in rec_97 and k != "N-7":
                self.assertEqual(rec_97[k], u"当たり" if v else u"外れ", k)
        self.assertEqual(self.F.R["read"][u"予測の判定"]["N-7"], u"当たり" if Jn["N-7"] else u"外れ")
        self.assertEqual(self.F.R["read"][u"予測の判定"]["K-3"], u"当たり" if Jk["K-3"] else u"外れ")

    def test_b_2_the_measured_judgments_of_this_run(self):
        _b, Jo, Jn, Jk, d, dr = build_all(self.F.R, self.F.seal)
        self.assertEqual(dict(Jo), dict((k, True) for k in Jo))
        self.assertEqual({"N-1": True, "N-2": True, "N-3": False, "N-4": True, "N-5": True, "N-6": False, "N-7": True}, dict(Jn))
        self.assertEqual({"K-1": True, "K-2": True, "K-3": True, "K-4": False}, dict(Jk))

    def test_b_3_the_bounds_in_the_record_are_the_ones_in_the_seal(self):
        P = seal_predictions(self.F.seal)
        b = self.F.R["ai"][u"定数"][u"予測の幅"]
        self.assertIn(u"**%d〜%d**" % tuple(b["O-2"]), P["O-2"][0])
        self.assertIn(u"**%d〜%d**" % tuple(b["O-3"]), P["O-3"][0])
        self.assertIn(u"**%d〜%d**" % tuple(b["O-5 保留"]), P["O-5"][0])
        self.assertIn(u"**%d〜%d**" % tuple(b["O-5 候補 0"]), P["O-5"][0])
        for s, (lo, hi) in b["O-7"].items():
            self.assertIn(s, P["O-7"][0])
        self.assertIn(u"**40〜300**", P["N-2"][0])
        self.assertIn(u"**10〜120**", P["N-3"][0])
        self.assertIn(u"**85% 以上**", P["N-6"][0]) if u"**85% 以上**" in P["N-6"][0] else self.assertIn(u"85% 以上", P["N-6"][0])

    def test_d_1_zero_diag_record_gate(self):
        self.assertEqual([], zero_problems(self.F.R))

    def test_d_2_zero_diag_has_no_other_class_row_so_the_engine_condition_has_no_unexplained_zero(self):
        z = self.F.R["zero"][u"集計"][u"分類(形が真の 42 行。上から順に 1 つ)"]
        self.assertEqual(0, z[u"(f) その他"])
        self.assertEqual(0, z[u"(e) member なし・同じ期に 2 つ以上(保留)"])


class DocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture.load()
        cls.F = Fixture
        cls.doc = read(DOC_REL)

    def test_c_1_the_tables_equal_the_ones_rebuilt_from_the_records_and_the_prose_is_in_order(self):
        self.assertEqual([], doc_problems(self.doc, self.F.R, self.F.seal))

    def test_c_2_the_document_states_the_required_sentences(self):
        for s in (u"候補の数は形が真の行の全部に数え、決まったは engine が GROUNDED にしなかった行だけ", u"分母 1", u"`subj` を条件にすると", u"言えない", u"K-4",
                  u"R1 の近傍を engine に入れる封"):
            self.assertIn(s, self.doc, s)

    def test_c_3_the_prediction_tables_copy_the_seal(self):
        P = seal_predictions(self.F.seal)
        self.assertEqual(15, len(P))
        got = doc_blocks(self.doc)
        for key, ids in (("pred_ai", ["O-%d" % i for i in range(1, 8)]), ("pred_97", ["N-%d" % i for i in range(1, 9)])):
            for line, k in zip(got[key][2:], ids):
                cells = [c.strip() for c in line.strip(u"|").split(u" | ")]
                self.assertEqual(cells[0], u"**%s**" % k)
                self.assertEqual(cells[1], P[k][0])
                self.assertEqual(cells[2], P[k][1])


class OrderTest(unittest.TestCase):
    def test_i_1_the_real_history_has_the_seal_before_the_implementation_before_the_files(self):
        u"""実装・記録・script・文書・門のどれかが未 commit なら赤(足した commit が無い)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_problems(REPO, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, IMPL_FILES, order_others()))


class Repo(object):
    u"""順序の試験用の使い捨て repo。"""

    def __init__(self):
        self.d = tempfile.mkdtemp(prefix="p28_order_")
        self.g("init", "-q")
        self.n = 0

    def g(self, *a):
        r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid"] + list(a), cwd=self.d, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return r.stdout

    def put(self, rel, text=u"x\n"):
        p = os.path.join(self.d, PREFIX, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text + (u"# %d\n" % self.n))
        self.n += 1

    def commit(self, *rels):
        for r in rels:
            self.g("add", PREFIX + r)
        self.g("commit", "-q", "-m", "c%d" % self.n)
        return self.g("rev-parse", "HEAD").strip()


OTHERS = ["a/rec.json", "b/script.py", "docs/doc.md", "tests/gate.py"]
IMPLS = ["adapters/xbrl/vocabulary.py", "adapters/xbrl/recipes.py"]
SEALF = "docs/seal.md"


def order_of(r, seal_short):
    return order_problems(r.d, PREFIX, SEALF, seal_short, IMPLS, OTHERS)


class OrderMutationTest(unittest.TestCase):
    def _good(self):
        r = Repo()
        r.put("adapters/xbrl/vocabulary.py")
        r.commit("adapters/xbrl/vocabulary.py")
        r.put(SEALF)
        s = r.commit(SEALF)
        r.put(IMPLS[0])
        r.put(IMPLS[1])
        r.commit(*IMPLS)
        for o in OTHERS:
            r.put(o)
        r.commit(*OTHERS)
        return r, s[:7]

    def test_i_2_a_correct_order_is_green_and_the_same_commit_for_impl_and_files_is_green(self):
        r, s = self._good()
        self.assertEqual([], order_of(r, s))
        r2 = Repo()
        r2.put(SEALF)
        s2 = r2.commit(SEALF)
        for f in IMPLS + OTHERS:
            r2.put(f)
        r2.commit(*(IMPLS + OTHERS))
        self.assertEqual([], order_of(r2, s2[:7]))

    def test_i_3_an_uncommitted_file_is_red_not_skipped(self):
        r3 = Repo()
        r3.put(SEALF)
        s3 = r3.commit(SEALF)
        for f in IMPLS:
            r3.put(f)
        r3.commit(*IMPLS)
        self.assertEqual(sorted("UNCOMMITTED:" + o for o in OTHERS), sorted(order_of(r3, s3[:7])))
        r4 = Repo()
        r4.put(SEALF)
        s4 = r4.commit(SEALF)
        self.assertTrue(any(p.startswith("IMPL_UNCOMMITTED:") for p in order_of(r4, s4[:7])))

    def test_i_4_a_file_before_the_seal_or_before_the_implementation_is_red(self):
        r = Repo()
        r.put(OTHERS[0])
        r.commit(OTHERS[0])
        r.put(SEALF)
        s = r.commit(SEALF)
        for f in IMPLS:
            r.put(f)
        r.commit(*IMPLS)
        for o in OTHERS[1:]:
            r.put(o)
        r.commit(*OTHERS[1:])
        self.assertIn("BEFORE_SEAL:" + OTHERS[0], order_of(r, s[:7]))
        r2 = Repo()
        r2.put(SEALF)
        s2 = r2.commit(SEALF)
        r2.put(OTHERS[0])
        r2.commit(OTHERS[0])
        for f in IMPLS:
            r2.put(f)
        r2.commit(*IMPLS)
        for o in OTHERS[1:]:
            r2.put(o)
        r2.commit(*OTHERS[1:])
        self.assertIn("BEFORE_IMPL:" + OTHERS[0], order_of(r2, s2[:7]))

    def test_i_5_the_seal_missing_twice_or_touching_the_engine_is_red(self):
        r = Repo()
        r.put(IMPLS[0])
        r.commit(IMPLS[0])
        self.assertEqual(["SEAL_ONCE"], order_of(r, "0000000"))
        r2 = Repo()
        r2.put(OTHERS[0])
        r2.commit(OTHERS[0])
        r2.put(SEALF)
        r2.put(IMPLS[0])
        s = r2.commit(SEALF, IMPLS[0])
        self.assertIn("SEAL_TOUCHES_ENGINE", order_of(r2, s[:7]))
        r3, s3 = self._good()
        self.assertIn("SEAL_NOT_THE_SEALED", order_of(r3, "abcdef0"))

    def test_i_6_the_seal_commit_of_the_real_repo_is_the_sealed_one(self):
        lst = added_commits(REPO, PREFIX + SEAL_REL)
        self.assertEqual(1, len(lst))
        self.assertTrue(lst[0].startswith(SEAL_COMMIT_SHORT))
        self.assertTrue(is_anc(REPO, lst[0], "HEAD"))


class MutationTest(unittest.TestCase):
    u"""門自身が、壊した標本で赤くなる。"""

    @classmethod
    def setUpClass(cls):
        Fixture.load()
        cls.F = Fixture
        cls.doc = read(DOC_REL)

    def test_g_0_baseline_is_green(self):
        self.assertEqual([], doc_problems(self.doc, self.F.R, self.F.seal))
        self.assertEqual([], record_problems(self.F.R, self.F.scripts, self.F.p27_docs))
        self.assertEqual([], zero_problems(self.F.R))

    def test_g_1_one_character_of_a_table_turns_c_red(self):
        for key in ("pred_ai", "pred_97", "adopt", "zero", "wiring"):
            body = doc_blocks(self.doc)[key]
            bad = self.doc.replace(u"\n".join(body), u"\n".join(body).replace(u"1", u"2", 1), 1)
            self.assertNotEqual(bad, self.doc, key)
            self.assertTrue(doc_problems(bad, self.F.R, self.F.seal), key)

    def test_g_2_changing_a_record_number_changes_the_judgment_or_the_table(self):
        R = copy.deepcopy(self.F.R)
        next(r for r in R["r97"][u"形が真の行"] if not r[u"決まった"])[u"決まった"] = True
        self.assertTrue(doc_problems(self.doc, R, self.F.seal))
        R = copy.deepcopy(self.F.R)
        for r in R["ai"][u"行"]:
            if r[u"形が真"] and r[u"決まった"]:
                r[u"決まった"] = False
                break
        self.assertTrue(doc_problems(self.doc, R, self.F.seal))
        R = copy.deepcopy(self.F.R)
        R["read"][u"行"][0][u"席 2"] = u"違う項目"
        self.assertTrue(doc_problems(self.doc, R, self.F.seal))

    def test_g_3_the_judgments_move_with_the_records(self):
        R = copy.deepcopy(self.F.R)
        _b, Jo, Jn, Jk, _d, _dr = build_all(R, self.F.seal)
        self.assertTrue(Jk["K-3"])
        R["read"][u"行"][0][u"席 1"] = R["read"][u"行"][0][u"席 2"] = u"違う項目"
        _b, Jo, Jn, Jk, _d, dr = build_all(R, self.F.seal)
        self.assertFalse(Jk["K-3"])
        self.assertFalse(Jn["N-7"])
        R = copy.deepcopy(self.F.R)
        for r in R["r97"][u"形が真の行"]:
            if r[u"決まった"]:
                r[u"R1"] = u"同じ"
        _b, _Jo, Jn, Jk, d, _dr = build_all(R, self.F.seal)
        self.assertTrue(Jk["K-4"] and Jn["N-6"])
        R = copy.deepcopy(self.F.R)
        R["r97"][u"N-1"]["P22"][u"byte が同じ書類"] = 96
        _b, _Jo, Jn, Jk, _d, _dr = build_all(R, self.F.seal)
        self.assertFalse(Jn["N-1"])
        self.assertFalse(Jk["K-1"])

    def test_g_4_a_forbidden_key_a_leak_or_a_wrong_sha_turns_a_red(self):
        for f in (lambda R: R["r97"].__setitem__(u"key_leaks", ["x"]),
                  lambda R: R["zero"][u"行"][0].__setitem__("span", "x"),
                  lambda R: R["ai"][u"行"][0].__setitem__(u"文", "x"),
                  lambda R: R["r97"][u"cache の前後"].__setitem__(u"変化なし", False),
                  lambda R: R["read"].__setitem__(u"席の指示文の sha256", "0" * 64),
                  lambda R: R["zero"].__setitem__(u"この script の sha256", "0" * 64),
                  lambda R: R["r97"][u"形が真の行"][0].__setitem__(u"docID", "S100ZZZZ")):
            R = copy.deepcopy(self.F.R)
            f(R)
            self.assertTrue(record_problems(R, self.F.scripts, self.F.p27_docs))

    def test_g_5_zero_diag_gate_goes_red(self):
        for f in (lambda R: R["zero"][u"集計"][u"分類(形が真の 42 行。上から順に 1 つ)"].__setitem__(u"(f) その他", 1),
                  lambda R: R["zero"][u"行"].pop(),
                  lambda R: R["zero"][u"行"][0].__setitem__(u"id", "N999"),
                  lambda R: R["zero"][u"集計"].__setitem__(u"候補 0 の行", 40),
                  lambda R: R["r97"][u"集計"].__setitem__(u"候補 0 の行(engine が GROUNDED にした行を含む)", 40)):
            R = copy.deepcopy(self.F.R)
            f(R)
            self.assertTrue(zero_problems(R))

    def test_g_6_prose_checks(self):
        self.assertEqual([], prose_problems(self.doc))
        self.assertTrue(prose_problems(self.doc + u"\n本文に 1234 という数がある。\n"))
        self.assertEqual([], prose_problems(self.doc + u"\n本文に 1234 という数がある。【門なし】\n"))
        self.assertTrue(doc_problems(self.doc + u"\nS100ABCD\n", self.F.R, self.F.seal))
        self.assertTrue(doc_problems(self.doc + u"\n精度\n", self.F.R, self.F.seal))

    def test_g_7_a_changed_seal_prediction_character_turns_c_red(self):
        seal = self.F.seal.replace(u"**10〜120**", u"**10〜121**", 1)
        self.assertNotEqual(seal, self.F.seal)
        self.assertTrue(doc_problems(self.doc, self.F.R, seal))


if __name__ == "__main__":
    unittest.main()
