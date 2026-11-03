# -*- coding: utf-8 -*-
"""P28E(= P27E + O。外部の数の文のための profile の候補)の測定の結果の門。封 docs/XBRL_P28E_SEAL_2026-11-03.md §6。

記録 4 つ(``fixtures/xbrl/p28e/``: ai_prose・entry_output_ai_prose_p28e・regress97・ritual)から、封 §3 の予測 E-1〜E-10 の判定と §4 の採用の基準 R-1〜R-3 を**機械で求め**、
結果の文書 ``docs/XBRL_P28E_RESULT_2026-11-03.md`` の表(``<!-- 門:start 名前 -->`` の中)を記録から作り直した表と一行も違わないことを見る。縛るもの:

  a  記録の禁止欄(span・value・recomputed・文・注入の字)が無い・key_leaks が空・cache の前後が同じ・docID が手元の 97 の一覧の中(AI の文・儀式の記録には docID が無い)・script の sha256 が現物と一致。
  b  予測の判定(E)・採用の判定(R)を記録から求める(記録の書いた判定欄と一致)。判定の関数は定数ではなく、記録を 1 つ変えると判定が変わる。
  c  文書の表 = 記録から作り直した表。門の外の散文は 3 桁以上の数を持たない(持つ行には【門なし】)。docID が文書に無い。
  e  engine の変更は vocabulary.py への挿入だけ(P28E を足した commit の numstat が vocabulary.py の挿入 6 行以下・削除 0 行で、ほかの engine の file を触らない)。
  i  順序: 封 S の commit ⊏ 実装 E ⊑ 記録・script・文書・門の commit ⊑ HEAD。封の commit は engine を触っていない。未 commit は赤(skip にしない)。
  g  変異: 記録の数・文書の 1 字・順序を壊した標本で赤になる。

この file は docID の字を持たない。新しい門の行頭に既存の門が数える名前(``ENGINE_LATER`` ほか)を使わない。
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
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))


def load_module(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_p28e")   # 前の便の門の部品(doc_blocks・prose_problems・order_problems・Repo)。門としては走らせない

SEAL_REL = "docs/XBRL_P28E_SEAL_2026-11-03.md"
DOC_REL = "docs/XBRL_P28E_RESULT_2026-11-03.md"
SEAL_COMMIT_SHORT = "7bfad77"
REC_REL = collections.OrderedDict([
    ("ai", "fixtures/xbrl/p28e/ai_prose_2026-11-03.json"), ("entry", "fixtures/xbrl/p28e/entry_output_ai_prose_p28e_2026-11-03.json"),
    ("r97", "fixtures/xbrl/p28e/regress97_2026-11-03.json"), ("rit", "fixtures/xbrl/p28e/ritual_2026-11-03.json")])
SCRIPT_REL = collections.OrderedDict([
    ("ai", "measure/xbrl_p28e_ai_prose_2026-11-03.py"), ("r97", "measure/xbrl_p28e_regress97_2026-11-03.py"), ("rit", "measure/xbrl_p28e_ritual_2026-11-03.py")])
P27_R97_REL = "fixtures/xbrl/p27/regress97_2026-10-27.json"
P28_R97_REL = "fixtures/xbrl/p28/regress97_2026-11-02.json"
GATE_FILES = ("tests/measure/test_xbrl_p28e_result.py",)
IMPL_FILES = ("adapters/xbrl/vocabulary.py",)
NOT_GATED = PR.NOT_GATED
FORBIDDEN_KEYS = ("span", "value", "recomputed", u"文", u"理由", u"元の字", u"後の字", u"文脈")
HIT, MISS, NOJ = PR.HIT, PR.MISS, PR.NOJ
STATES = PR.STATES
BASE5 = ("P22", "P26", "P27", "P27E", "P28")
DIR_UG = "UNVERIFIABLE → GROUNDED"
RESERVED_HEADS = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def jload(rel):
    return json.loads(read(rel))


def sha256_rel(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def records():
    return dict((k, jload(v)) for k, v in REC_REL.items())


# ---------------------------------------------------------------- 封の予測の字
def seal_preds(seal):
    u"""封 §3 の表の行 {E-n: (予測, 外れ方)}。"""
    sec = seal[seal.index("## §3"):seal.index("## §4")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| \*\*(E-\d+)\*\* \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            out[m.group(1)] = (cells[0], cells[1] if len(cells) > 1 else u"")
    return out


def seal_range(text):
    m = re.search(r"\*\*(\d+)〜(\d+)\*\*", text)
    return [int(m.group(1)), int(m.group(2))] if m else None


def seal_four(text):
    m = re.search(r"4 state は \*{0,2}(\d+)・(\d+)・(\d+)・(\d+)\*{0,2}", text)
    return [int(x) for x in m.groups()] if m else None


# ---------------------------------------------------------------- 判定(記録から)
def derive_ai(ai, preds):
    rows = ai[u"行"]
    T = ai[u"集計"]
    c27 = collections.Counter(r[u"P27E の state"] for r in rows)
    c28 = collections.Counter(r[u"P28E の state"] for r in rows)
    cp = collections.Counter(r[u"P28 の state"] for r in rows)
    shape = [r for r in rows if r[u"形が真"]]
    decided = [r for r in shape if r[u"決まった"]]
    moved = [r for r in rows if r[u"P27E → P28E で動いた"]]
    shape_ids = set(r[u"id"] for r in shape)
    g = T[u"E-1 P27E の出力(engine の欄を除く sort_keys JSON)の sha256"]
    d = collections.OrderedDict()
    d["st27"] = [c27[s] for s in STATES]
    d["st28"] = [c28[s] for s in STATES]
    d["stp"] = [cp[s] for s in STATES]
    d["sha_same"] = bool(g[u"このtree"] == g[u"HEAD の engine"])
    d["claims_same"] = bool(T[u"E-1 P27E の claims が記録 entry_output_ai_prose_p27e と欄ごとに一致"])
    d["diff_p28"] = sum(1 for r in rows if r[u"P28E と P28 で state が違う"])
    d["shape"] = len(shape)
    d["decided_ids"] = sorted(r[u"id"] for r in decided)
    d["moved"] = len(moved)
    d["dirs"] = collections.OrderedDict(sorted(collections.Counter(u"%s → %s" % (r[u"P27E の state"], r[u"P28E の state"]) for r in moved).items()))
    d["off_shape_moved"] = sum(1 for r in moved if r[u"id"] not in shape_ids)
    g27 = [r for r in rows if r[u"P27E の state"] == "GROUNDED"]
    d["g27"] = len(g27)
    d["g27_leave"] = sum(1 for r in g27 if r[u"P28E の state"] != "GROUNDED")
    d["expect_ids"] = sorted(re.findall(r"N\d{3}", preds["E-3"][0]))
    d["expect_dirs"] = collections.OrderedDict(sorted((u"POINTER_NOT_FOUND → GROUNDED" if "POINTER" in k else u"VALUE_MISMATCH → GROUNDED", int(v)) for k, v in
                                                      re.findall(r"(POINTER_NOT_FOUND|VALUE_MISMATCH) → GROUNDED \*\*(\d+)\*\*", preds["E-3"][0])))
    d["expect_st27"] = seal_four(preds["E-1"][0])
    d["expect_st28"] = seal_four(preds["E-2"][0])
    return d


def derive_97(r97, p28_moved):
    docs = r97[u"書類"]
    d = collections.OrderedDict()
    d["docs"] = len(docs)
    d["e5"] = collections.OrderedDict((p, sum(1 for x in docs if x[u"出力の sha256(engine の欄を除く)"][p] == x[u"比べる側の engine の出力の sha256"][p])) for p in BASE5)
    moved = r97[u"動いた行"]
    d["moved"] = len(moved)
    d["dirs"] = collections.OrderedDict(sorted(collections.Counter(u"%s → %s" % (m[u"前の state"], m[u"後の state"]) for m in moved).items()))
    d["other_dir"] = sum(1 for m in moved if u"%s → %s" % (m[u"前の state"], m[u"後の state"]) != DIR_UG)
    d["leave"] = sum(1 for m in moved if m[u"前の state"] == "GROUNDED" and m[u"後の state"] != "GROUNDED")
    d["same_as_p28"] = sorted([m[u"docID"], m[u"id"]] for m in moved) == sorted([m[u"docID"], m[u"id"]] for m in p28_moved)
    d["shape"] = len(r97[u"形が真の行"])
    d["decided"] = sum(1 for r in r97[u"形が真の行"] if r[u"決まった"])
    d["hold"] = sum(1 for r in r97[u"形が真の行"] if r[u"候補"] is not None and r[u"候補"] >= 2 and not r[u"決まった"])
    d["zero"] = sum(1 for r in r97[u"形が真の行"] if r[u"候補"] == 0)
    d["off_shape"] = sum(1 for m in moved if not m[u"形が真"])
    d["states"] = copy.deepcopy(r97[u"集計"][u"4 state"])
    return d


def derive_rit(rit):
    rows = rit[u"注入ごとの結果"]
    d = collections.OrderedDict()
    for p in ("P27E", "P28E"):
        got = [r for r in rows if r[p + u" の結果"] is not None]
        d[p] = collections.OrderedDict([("targets", len(got)), ("passed", sum(1 for r in got if r[p + u" の結果"] == "PASSED")),
                                        ("detected", sum(1 for r in got if r[p + u" の結果"] == "detected:VALUE_MISMATCH")),
                                        ("other", sum(1 for r in got if r[p + u" の結果"] not in ("PASSED", "detected:VALUE_MISMATCH")))])
    d["only28"] = [r[u"id"] for r in rows if r[u"P27E の結果"] is None]
    d["only27"] = [r[u"id"] for r in rows if r[u"P28E の結果"] is None]
    d["passed28_ids"] = [r[u"id"] for r in rows if r[u"P28E の結果"] == "PASSED"]
    d["passed27_ids"] = [r[u"id"] for r in rows if r[u"P27E の結果"] == "PASSED"]
    return d


def judge_all(R, seal, p28_moved):
    preds = seal_preds(seal)
    a = derive_ai(R["ai"], preds)
    b = derive_97(R["r97"], p28_moved)
    c = derive_rit(R["rit"])
    lo, hi = seal_range(preds["E-7"][0])
    J = collections.OrderedDict()
    J["E-1"] = bool(a["sha_same"] and a["claims_same"] and a["st27"] == a["expect_st27"])
    J["E-2"] = bool(a["st28"] == a["expect_st28"] and a["diff_p28"] == 0)
    J["E-3"] = bool(len(a["decided_ids"]) == 7 and a["decided_ids"] == a["expect_ids"] and a["moved"] == 7 and a["dirs"] == a["expect_dirs"])
    J["E-4"] = bool(a["off_shape_moved"] == 0 and a["g27_leave"] == 0)
    J["E-5"] = bool(b["docs"] == 97 and all(v == 97 for v in b["e5"].values()) and sorted(b["e5"]) == sorted(BASE5))
    J["E-6"] = bool(b["moved"] == 1 and b["same_as_p28"] and b["dirs"] == {DIR_UG: 1} and b["other_dir"] == 0 and b["leave"] == 0)
    J["E-7"] = bool(lo <= c["P27E"]["passed"] <= hi)
    J["E-8"] = bool(c["P28E"]["passed"] <= c["P27E"]["passed"])
    J["E-9"] = bool(c["P28E"]["detected"] >= c["P27E"]["detected"])
    R1 = bool(J["E-1"] and J["E-5"] and b["other_dir"] == 0 and b["leave"] == 0 and J["E-4"])
    R2 = bool(len(a["decided_ids"]) >= 6)
    R3 = bool(J["E-8"])
    K = collections.OrderedDict([("R-1", R1), ("R-2", R2), ("R-3", R3)])
    return preds, a, b, c, J, K


def word(v):
    return HIT if v else MISS


def build_blocks(R, seal, p28_moved):
    preds, a, b, c, J, K = judge_all(R, seal, p28_moved)
    M = collections.OrderedDict()
    M["E-1"] = u"P27E の出力(engine の欄を除く)の sha256 が HEAD の engine と%s・記録 entry_output_ai_prose_p27e と%s。P27E の 4 state %s" % (
        u"一致" if a["sha_same"] else u"不一致", u"欄ごとに一致" if a["claims_same"] else u"不一致", u"/".join(str(x) for x in a["st27"]))
    M["E-2"] = u"P28E の 4 state %s。P28E と P28 で state が違う行 %d(P28 の 4 state %s)" % (u"/".join(str(x) for x in a["st28"]), a["diff_p28"], u"/".join(str(x) for x in a["stp"]))
    M["E-3"] = u"決まって GROUNDED になった行 %d(%s)。P27E → P28E で動いた行 %d(向き: %s)" % (
        len(a["decided_ids"]), u"・".join(a["decided_ids"]), a["moved"], u"、".join(u"%s %d" % kv for kv in a["dirs"].items()))
    M["E-4"] = u"形が偽の行で P27E から動いた行 %d。P27E で GROUNDED の %d 行のうち P28E で GROUNDED でない行 %d" % (a["off_shape_moved"], a["g27"], a["g27_leave"])
    M["E-5"] = u"byte が同じ書類(%d 書類中): %s" % (b["docs"], u"・".join(u"%s %d" % kv for kv in b["e5"].items()))
    M["E-6"] = u"P27E → P28E で動いた行 %d(向き: %s)。P28 の記録の動いた行と同じ docID・id %s。他の向き %d・GROUNDED を離れる行 %d" % (
        b["moved"], u"、".join(u"%s %d" % kv for kv in b["dirs"].items()) or u"なし", u"はい" if b["same_as_p28"] else u"いいえ", b["other_dir"], b["leave"])
    M["E-7"] = u"P27E の 通した %d(注入の対象 %d)" % (c["P27E"]["passed"], c["P27E"]["targets"])
    M["E-8"] = u"P28E の 通した %d(注入の対象 %d)。P27E の 通した %d" % (c["P28E"]["passed"], c["P28E"]["targets"], c["P27E"]["passed"])
    M["E-9"] = u"止めた(VALUE_MISMATCH): P28E %d・P27E %d" % (c["P28E"]["detected"], c["P27E"]["detected"])
    blocks = collections.OrderedDict()
    for key, ids in (("pred_ai", ["E-1", "E-2", "E-3", "E-4"]), ("pred_97", ["E-5", "E-6"]), ("pred_rit", ["E-7", "E-8", "E-9", "E-10"])):
        t = [u"| # | 予測(封の字) | 外れ方(封の字) | 実測(記録から) | 当たり外れ |", u"|---|---|---|---|---|"]
        for k in ids:
            if k == "E-10":
                t.append(u"| **E-10** | %s | %s | 止め方の型 P27E %s・P28E %s。素の書類の 4 state P27E %s・P28E %s | %s |" % (
                    preds[k][0], preds[k][1], u"、".join(u"%s %d" % kv for kv in R["rit"][u"profile ごとの集計"]["P27E"][u"止めた でも 通した でもない結果"].items()) or u"なし",
                    u"、".join(u"%s %d" % kv for kv in R["rit"][u"profile ごとの集計"]["P28E"][u"止めた でも 通した でもない結果"].items()) or u"なし",
                    u"/".join(str(R["rit"][u"profile ごとの集計"]["P27E"][u"素の書類の state の分布"][s]) for s in STATES),
                    u"/".join(str(R["rit"][u"profile ごとの集計"]["P28E"][u"素の書類の state の分布"][s]) for s in STATES), NOJ))
            else:
                t.append(u"| **%s** | %s | %s | %s | %s |" % (k, preds[k][0], preds[k][1], M[k], word(J[k])))
        blocks[key] = t
    adopt_ok = all(K.values())
    kk = [u"| # | 基準(封 §4) | 実測(記録から) | 満たすか |", u"|---|---|---|---|"]
    kk.append(u"| **R-1** | 壊さない | E-1 %s・E-5 %s・E-6 の他の向き %d・GROUNDED を離れる行 %d・E-4 の動いた行 %d | %s |" % (
        u"当たり" if J["E-1"] else u"外れ", u"97 / 97 ×5" if J["E-5"] else u"97 / 97 でない", b["other_dir"], b["leave"], a["off_shape_moved"] + a["g27_leave"], u"はい" if K["R-1"] else u"いいえ"))
    kk.append(u"| **R-2** | 決める | E-3 の決まった行 %d(6 以上) | %s |" % (len(a["decided_ids"]), u"はい" if K["R-2"] else u"いいえ"))
    kk.append(u"| **R-3** | 誤りを通さない | E-8: P28E の 通した %d ≤ P27E の 通した %d | %s |" % (c["P28E"]["passed"], c["P27E"]["passed"], u"はい" if K["R-3"] else u"いいえ"))
    kk.append(u"| **判定** | R-1〜R-3 の全部 | %s | %s |" % (u"全部満たす" if adopt_ok else u"満たさないものがある", u"採用(推奨を P27E から P28E に替える。既定は P27 のまま)" if adopt_ok else u"採用しない(推奨は P27E のまま。P28E は engine に残す)"))
    blocks["adopt"] = kk
    mv = [u"| 動いた行(AI の文) | 前の state | 後の state | 結んだ要素 | 期 |", u"|---|---|---|---|---|"]
    for r in R["ai"][u"行"]:
        if r[u"P27E → P28E で動いた"]:
            mv.append(u"| %s | %s | %s | %s | %s |" % (r[u"id"], r[u"P27E の state"], r[u"P28E の state"], r[u"P28E の要素"], r[u"P28E の期"]))
    blocks["moved_ai"] = mv
    m97 = [u"| 動いた行(97 書類) | 前の state | 前の reason | 後の state | 結んだ要素 | 期 | 主語なし |", u"|---|---|---|---|---|---|---|"]
    for i, m in enumerate(R["r97"][u"動いた行"], 1):
        m97.append(u"| %d 行目 | %s | %s | %s | %s | %s | %s |" % (i, m[u"前の state"], m[u"前の reason"], m[u"後の state"], m[u"結んだ要素"], m[u"結んだ期"], u"はい" if m[u"no_subject(claim の subject が空)"] else u"いいえ"))
    blocks["moved_97"] = m97
    rt = [u"| 儀式の注入(同梱の AI の文の書類) | P27E | P28E |", u"|---|---|---|"]
    for lab, key in ((u"注入の対象", "targets"), (u"通した", "passed"), (u"止めた(VALUE_MISMATCH)", "detected"), (u"止めた でも 通した でもない結果", "other")):
        rt.append(u"| %s | %d | %d |" % (lab, c["P27E"][key], c["P28E"][key]))
    rt.append(u"| 通した の id | %s | %s |" % (u"・".join(c["passed27_ids"]), u"・".join(c["passed28_ids"])))
    rt.append(u"| P28E だけの注入の対象 | ― | %s |" % u"・".join(c["only28"]))
    rt.append(u"| 共通の注入の対象で数えた 通した(参考。判定に使わない) | %d | %d |" % (R["rit"][u"共通の id だけで数えた件数(参考。判定に使わない)"][u"通した"]["P27E"], R["rit"][u"共通の id だけで数えた件数(参考。判定に使わない)"][u"通した"]["P28E"]))
    blocks["ritual"] = rt
    sh = [u"| 97 書類の形が真の行(P28E) | 行 |", u"|---|---|",
          u"| 形が真の行 | %d |" % b["shape"], u"| 決まって GROUNDED になった行 | %d |" % b["decided"], u"| 候補 2 以上で保留の行 | %d |" % b["hold"], u"| 候補 0 の行 | %d |" % b["zero"]]
    blocks["shape97"] = sh
    wt = [u"| 配線の門 | 値 |", u"|---|---|"]
    wt.append(u"| 手元の cache の件数(前 = 後) | %s |" % u"・".join(u"%s %d" % (k, v[u"件数"]) for k, v in R["r97"][u"cache の前後"][u"前"].items()))
    wt.append(u"| cache の前後が同じ | %s |" % (u"はい" if R["r97"][u"cache の前後"][u"変化なし"] else u"いいえ"))
    wt.append(u"| AI の文の行の対応(同じ位置で鍵が 3 profile で同じ) | 対応 %d 行・対応しない %d |" % tuple(R["ai"][u"配線の門"][u"(e) 行の対応"].values()))
    wt.append(u"| 比べる側の engine の commit | %s |" % R["r97"][u"比べた engine"][u"commit"])
    wt.append(u"| 儀式のラベル 2 file の sha256 を起動時に照合した | %s |" % (u"はい" if len(R["rit"][u"ラベル 2 file の sha256(起動時に照合)"]) == 2 else u"いいえ"))
    key_names = [k for k in R["rit"][u"鍵の名前の有無(値は読まない)"] if k != "ANTHROPIC_BASE_URL"]       # ANTHROPIC_BASE_URL は URL で鍵ではない(親の環境に在る。前例の儀式の記録も同じ)
    wt.append(u"| 鍵の名前(%s)が環境に在った(儀式の記録) | %s |" % (u"・".join(key_names), u"在った" if any(R["rit"][u"鍵の名前の有無(値は読まない)"][k] for k in key_names) else u"無かった"))
    blocks["wiring"] = wt
    return blocks, preds, a, b, c, J, K


# ---------------------------------------------------------------- 文書
def doc_problems(doc, R, seal, p28_moved):
    blocks = build_blocks(R, seal, p28_moved)[0]
    got = PR.doc_blocks(doc)
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
    out += [u"散文の数に【門なし】が無い: 行 %d %s" % x for x in PR.prose_problems(doc)]
    return out


# ---------------------------------------------------------------- 記録
def record_problems(R, p27_docs):
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
            if k != "r97":
                out.append(u"%s: docID が入っている" % k)
            elif m.group(0) not in p27_docs:
                out.append(u"%s: 97 の一覧に無い docID %s" % (k, m.group(0)))
    if not R["r97"][u"cache の前後"][u"変化なし"]:
        out.append(u"r97: cache の前後が違う")
    for k, rel in SCRIPT_REL.items():
        if R[k][u"この script の sha256"] != sha256_rel(rel):
            out.append(u"%s: 記録の script の sha256 が現物と違う" % k)
    if R["ai"][u"配線の門"][u"通った"] is not True:
        out.append(u"ai: 配線の門が通っていない")
    if R["ai"][u"配線の門"][u"(e) 行の対応"][u"対応しない"] != 0:
        out.append(u"ai: 行の対応が取れていない行がある")
    for k in ("ai", "r97", "rit"):
        got = R[k][u"封の commit"] if k == "r97" else R[k][u"封"][u"commit"]
        if got != SEAL_COMMIT_SHORT:
            out.append(u"%s: 記録の封の commit が封の commit でない" % k)
    ids = [c["id"] for c in R["entry"]["claims"]]
    if ids != [r[u"id"] for r in R["ai"][u"行"]]:
        out.append(u"entry: id の並びが ai の行と違う")
    for c, r in zip(R["entry"]["claims"], R["ai"][u"行"]):
        if c["state"] != r[u"P28E の state"]:
            out.append(u"entry: state が ai の行と違う: " + c["id"])
            break
    return out


def engine_problems(root, prefix, seal_rel=SEAL_REL):
    u"""P28E を足した commit(封より後で vocabulary.py を最初に変えた commit)の numstat が vocabulary.py の挿入 6 行以下・削除 0 行だけ。"""
    s = PR.added_commits(root, prefix + seal_rel)
    if len(s) != 1:
        return [u"SEAL_ONCE"]
    lst = [c for c in PR.git_in(root, "log", "--format=%H", "--reverse", s[0] + "..HEAD", "--", prefix + IMPL_FILES[0])[1].split() if c]
    if not lst:
        return [u"IMPL_UNCOMMITTED"]
    rc, stat = PR.git_in(root, "show", "--numstat", "--format=", lst[0], "--", prefix + "adapters", prefix + "core")
    rows = [l.split("\t") for l in stat.splitlines() if l.strip()]
    out = []
    if [r[2] for r in rows] != [prefix + IMPL_FILES[0]]:
        out.append(u"ENGINE_FILES:" + u",".join(r[2] for r in rows))
    for r in rows:
        if r[1] != "0":
            out.append(u"DELETIONS:" + r[2])
        if r[0] == "-" or int(r[0]) > 6:
            out.append(u"INSERTIONS:" + r[2] + ":" + r[0])
    return out


def order_others():
    return list(REC_REL.values()) + list(SCRIPT_REL.values()) + [DOC_REL] + list(GATE_FILES)


# ---------------------------------------------------------------- 試験
class Fixture(object):
    @classmethod
    def load(cls):
        cls.seal = read(SEAL_REL)
        cls.R = records()
        cls.p28_moved = jload(P28_R97_REL)[u"動いた行"]
        cls.p27_docs = set(x[u"docID"] for x in jload(P27_R97_REL)[u"書類"])


class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture.load()
        cls.F = Fixture

    def test_a_1_records_scripts_and_cache_are_clean(self):
        self.assertEqual(97, len(self.F.p27_docs))
        self.assertEqual([], record_problems(self.F.R, self.F.p27_docs))

    def test_a_2_the_97_documents_are_the_precedent_97(self):
        self.assertEqual(sorted(self.F.p27_docs), sorted(d[u"docID"] for d in self.F.R["r97"][u"書類"]))

    def test_b_1_judgments_are_recomputed_and_equal_the_record_fields(self):
        _p, _a, _b, _c, J, _K = judge_all(self.F.R, self.F.seal, self.F.p28_moved)
        for k in ("E-1", "E-2", "E-3", "E-4"):
            self.assertEqual(self.F.R["ai"][u"予測の判定"][k], u"当たり" if J[k] else u"外れ", k)
        for k in ("E-5", "E-6"):
            self.assertEqual(self.F.R["r97"][u"予測の判定"][k], u"当たり" if J[k] else u"外れ", k)
        for k in ("E-7", "E-8", "E-9"):
            self.assertEqual(self.F.R["rit"][u"予測の判定"][k], u"当たり" if J[k] else u"外れ", k)

    def test_b_2_the_bounds_in_the_seal_are_the_ones_the_scripts_use(self):
        preds = seal_preds(self.F.seal)
        self.assertEqual(10, len(preds))
        self.assertEqual([2, 4], seal_range(preds["E-7"][0]))
        self.assertEqual([340, 15, 33, 24], seal_four(preds["E-1"][0]))
        self.assertEqual([347, 12, 33, 20], seal_four(preds["E-2"][0]))
        c = self.F.R["ai"][u"定数"]
        self.assertEqual(sorted(c["E-3 の id"]), sorted(re.findall(r"N\d{3}", preds["E-3"][0])))
        self.assertEqual([340, 15, 33, 24], [c["E-1 の 4 state"][s] for s in STATES])
        self.assertEqual([347, 12, 33, 20], [c["E-2 の 4 state"][s] for s in STATES])

    def test_b_3_the_measured_judgments_of_this_run(self):
        _p, _a, _b, _c, J, K = judge_all(self.F.R, self.F.seal, self.F.p28_moved)
        self.assertEqual(dict((k, True) for k in ("E-1", "E-2", "E-3", "E-4", "E-5", "E-6", "E-7", "E-8", "E-9")), dict(J))
        self.assertEqual({"R-1": True, "R-2": True, "R-3": True}, dict(K))


class DocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Fixture.load()
        cls.F = Fixture
        cls.doc = read(DOC_REL)

    def test_c_1_the_tables_equal_the_ones_rebuilt_from_the_records_and_the_prose_is_in_order(self):
        self.assertEqual([], doc_problems(self.doc, self.F.R, self.F.seal, self.F.p28_moved))

    def test_c_2_the_document_states_the_required_sentences(self):
        for s in (u"言えない", u"1 書類", u"分母", u"既定は P27 のまま", u"走らせた回数", u"採用"):
            self.assertIn(s, self.doc, s)

    def test_c_3_the_prediction_tables_copy_the_seal(self):
        P = seal_preds(self.F.seal)
        got = PR.doc_blocks(self.doc)
        for key, ids in (("pred_ai", ["E-1", "E-2", "E-3", "E-4"]), ("pred_97", ["E-5", "E-6"]), ("pred_rit", ["E-7", "E-8", "E-9", "E-10"])):
            for line, k in zip(got[key][2:], ids):
                cells = [c.strip() for c in line.strip(u"|").split(u" | ")]
                self.assertEqual(cells[0], u"**%s**" % k)
                self.assertEqual(cells[1], P[k][0])
                self.assertEqual(cells[2], P[k][1])


class EngineAndOrderTest(unittest.TestCase):
    def test_e_1_the_engine_change_is_the_insertion_in_vocabulary_only(self):
        self.assertEqual([], engine_problems(REPO, PREFIX))

    def test_e_2_the_live_profile_is_p27e_plus_the_other_flag_and_the_default_is_unchanged(self):
        from adapters.xbrl import vocabulary as V
        import dataclasses
        self.assertEqual(dataclasses.replace(V.P27E, name="P28E", other_subject_2026_11_02=True), V.P28E)
        self.assertEqual("P27", V.DEFAULT_PROFILE)

    def test_i_1_the_real_history_has_the_seal_before_the_implementation_before_the_files(self):
        u"""実装・記録・script・文書・門のどれかが未 commit なら赤(足した commit が無い)。全部 commit された後で初めて緑。"""
        self.assertEqual([], PR.order_problems(REPO, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, IMPL_FILES, order_others()))

    def test_i_6_the_seal_commit_of_the_real_repo_is_the_sealed_one(self):
        lst = PR.added_commits(REPO, PREFIX + SEAL_REL)
        self.assertEqual(1, len(lst))
        self.assertTrue(lst[0].startswith(SEAL_COMMIT_SHORT))
        self.assertTrue(PR.is_anc(REPO, lst[0], "HEAD"))

    def test_n_1_the_new_gate_does_not_define_reserved_names_at_the_line_start(self):
        for rel in GATE_FILES:
            for line in read(rel).splitlines():
                m = re.match(r"^([A-Za-z_][A-Za-z_0-9]*)\s*[=:]", line)
                if m:
                    self.assertFalse(any(m.group(1).startswith(p) for p in RESERVED_HEADS), (rel, m.group(1)))
        self.assertIn("RESERVED_HEADS", read(GATE_FILES[0]))


OTHERS = ["a/rec.json", "b/script.py", "docs/doc.md", "tests/gate.py"]
IMPLS = list(IMPL_FILES)
SEALF = "docs/seal.md"


def order_of(r, seal_short):
    return PR.order_problems(r.d, PREFIX, SEALF, seal_short, IMPLS, OTHERS)


class OrderMutationTest(unittest.TestCase):
    def _good(self):
        r = PR.Repo()
        r.put(IMPLS[0])
        r.commit(IMPLS[0])
        r.put(SEALF)
        s = r.commit(SEALF)
        r.put(IMPLS[0])
        r.commit(IMPLS[0])
        for o in OTHERS:
            r.put(o)
        r.commit(*OTHERS)
        return r, s[:7]

    def test_i_2_a_correct_order_is_green_and_the_same_commit_for_impl_and_files_is_green(self):
        r, s = self._good()
        self.assertEqual([], order_of(r, s))
        r2 = PR.Repo()
        r2.put(SEALF)
        s2 = r2.commit(SEALF)
        for f in IMPLS + OTHERS:
            r2.put(f)
        r2.commit(*(IMPLS + OTHERS))
        self.assertEqual([], order_of(r2, s2[:7]))

    def test_i_3_an_uncommitted_file_is_red_not_skipped(self):
        r3 = PR.Repo()
        r3.put(SEALF)
        s3 = r3.commit(SEALF)
        for f in IMPLS:
            r3.put(f)
        r3.commit(*IMPLS)
        self.assertEqual(sorted("UNCOMMITTED:" + o for o in OTHERS), sorted(order_of(r3, s3[:7])))
        r4 = PR.Repo()
        r4.put(SEALF)
        s4 = r4.commit(SEALF)
        self.assertTrue(any(p.startswith("IMPL_UNCOMMITTED:") for p in order_of(r4, s4[:7])))

    def test_i_4_a_file_before_the_seal_or_before_the_implementation_is_red(self):
        r = PR.Repo()
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
        r2 = PR.Repo()
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
        r = PR.Repo()
        r.put(IMPLS[0])
        r.commit(IMPLS[0])
        self.assertEqual(["SEAL_ONCE"], order_of(r, "0000000"))
        r2 = PR.Repo()
        r2.put(OTHERS[0])
        r2.commit(OTHERS[0])
        r2.put(SEALF)
        r2.put(IMPLS[0])
        s = r2.commit(SEALF, IMPLS[0])
        self.assertIn("SEAL_TOUCHES_ENGINE", order_of(r2, s[:7]))
        r3, s3 = self._good()
        self.assertIn("SEAL_NOT_THE_SEALED", order_of(r3, "abcdef0"))

    def test_e_3_the_engine_change_check_goes_red_on_a_bigger_or_wider_change(self):
        def repo_with(extra_lines, extra_files, deletions=False):
            r = PR.Repo()
            r.put(IMPLS[0], u"a\nb\n")
            r.commit(IMPLS[0])
            r.put(SEALF)
            r.commit(SEALF)
            p = os.path.join(r.d, PREFIX, IMPLS[0])
            with open(p, encoding="utf-8") as fh:
                before = fh.read()
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(u"x\n" if deletions else before)          # 削除ありの標本は先頭の行を別の字に替える(削除 1 行・挿入 1 行)
                fh.write(u"".join(u"n%d\n" % i for i in range(extra_lines)))
            files = [IMPLS[0]]
            for f in extra_files:
                r.put(f)
                files.append(f)
            r.commit(*files)
            return r

        def probe(r):
            return engine_problems(r.d, PREFIX, SEALF)

        self.assertEqual([], probe(repo_with(5, [])))
        self.assertTrue(any(p.startswith("INSERTIONS") for p in probe(repo_with(7, []))))
        self.assertTrue(any(p.startswith("ENGINE_FILES") for p in probe(repo_with(3, ["adapters/xbrl/recipes.py"]))))
        self.assertTrue(any(p.startswith("DELETIONS") for p in probe(repo_with(3, [], deletions=True))))


class MutationTest(unittest.TestCase):
    u"""門自身が、壊した標本で赤くなる。"""

    @classmethod
    def setUpClass(cls):
        Fixture.load()
        cls.F = Fixture
        cls.doc = read(DOC_REL)

    def dp(self, doc=None, R=None, seal=None):
        return doc_problems(self.doc if doc is None else doc, self.F.R if R is None else R, self.F.seal if seal is None else seal, self.F.p28_moved)

    def test_g_0_baseline_is_green(self):
        self.assertEqual([], self.dp())
        self.assertEqual([], record_problems(self.F.R, self.F.p27_docs))

    def test_g_1_one_character_of_a_table_turns_c_red(self):
        for key in ("pred_ai", "pred_97", "pred_rit", "adopt", "ritual", "wiring", "moved_ai", "moved_97"):
            body = PR.doc_blocks(self.doc)[key]
            bad = self.doc.replace(u"\n".join(body), u"\n".join(body).replace(u"1", u"2", 1), 1)
            self.assertNotEqual(bad, self.doc, key)
            self.assertTrue(self.dp(doc=bad), key)

    def test_g_2_changing_a_record_number_changes_the_judgment_or_the_table(self):
        R = copy.deepcopy(self.F.R)
        R["rit"][u"注入ごとの結果"][0][u"P28E の結果"] = "PASSED" if R["rit"][u"注入ごとの結果"][0][u"P28E の結果"] != "PASSED" else "detected:VALUE_MISMATCH"
        self.assertTrue(self.dp(R=R))
        R = copy.deepcopy(self.F.R)
        next(r for r in R["ai"][u"行"] if r[u"形が真"] and r[u"決まった"])[u"決まった"] = False
        self.assertTrue(self.dp(R=R))
        R = copy.deepcopy(self.F.R)
        R["r97"][u"書類"][0][u"出力の sha256(engine の欄を除く)"]["P27E"] = "0" * 64
        self.assertTrue(self.dp(R=R))

    def test_g_3_the_judgments_move_with_the_records(self):
        base = judge_all(self.F.R, self.F.seal, self.F.p28_moved)
        self.assertTrue(base[5]["R-3"])
        R = copy.deepcopy(self.F.R)       # P28E が 1 件多く通すと E-8 と R-3 が赤
        row = next(r for r in R["rit"][u"注入ごとの結果"] if r[u"P28E の結果"] == "detected:VALUE_MISMATCH" and r[u"P27E の結果"] == "detected:VALUE_MISMATCH")
        row[u"P28E の結果"] = "PASSED"
        _p, _a, _b, _c, J, K = judge_all(R, self.F.seal, self.F.p28_moved)
        self.assertFalse(J["E-8"])
        self.assertFalse(K["R-3"])
        R = copy.deepcopy(self.F.R)       # P28E の止めた が P27E を下回ると E-9 が赤
        c = derive_rit(R["rit"])
        need = c["P28E"]["detected"] - c["P27E"]["detected"] + 1                  # P27E より 1 少なくなるまで変える
        rows = [r for r in R["rit"][u"注入ごとの結果"] if r[u"P28E の結果"] == "detected:VALUE_MISMATCH" and r[u"P27E の結果"] == "detected:VALUE_MISMATCH"]
        self.assertGreaterEqual(len(rows), need)
        for row in rows[:need]:
            row[u"P28E の結果"] = "detected:POINTER_NOT_FOUND"
        self.assertTrue(judge_all(self.F.R, self.F.seal, self.F.p28_moved)[4]["E-9"])
        self.assertFalse(judge_all(R, self.F.seal, self.F.p28_moved)[4]["E-9"])
        R = copy.deepcopy(self.F.R)       # 97 書類の byte 一致が 1 つ崩れると E-5 と R-1 が赤
        R["r97"][u"書類"][0][u"出力の sha256(engine の欄を除く)"]["P22"] = "0" * 64
        _p, _a, _b, _c, J, K = judge_all(R, self.F.seal, self.F.p28_moved)
        self.assertFalse(J["E-5"])
        self.assertFalse(K["R-1"])
        R = copy.deepcopy(self.F.R)       # 動いた行が増える / 向きが違う / GROUNDED を離れると E-6 と R-1 が赤
        m = copy.deepcopy(R["r97"][u"動いた行"][0])
        m[u"id"] = "N000"
        R["r97"][u"動いた行"].append(m)
        self.assertFalse(judge_all(R, self.F.seal, self.F.p28_moved)[4]["E-6"])
        R = copy.deepcopy(self.F.R)
        R["r97"][u"動いた行"][0][u"前の state"] = "GROUNDED"
        _p, _a, _b, _c, J, K = judge_all(R, self.F.seal, self.F.p28_moved)
        self.assertFalse(J["E-6"])
        self.assertFalse(K["R-1"])
        R = copy.deepcopy(self.F.R)       # 決まった行が 6 未満なら R-2 が赤
        for r in R["ai"][u"行"]:
            if r[u"形が真"] and r[u"決まった"]:
                r[u"決まった"] = False
                break
        _p, _a, _b, _c, J, K = judge_all(R, self.F.seal, self.F.p28_moved)
        self.assertFalse(J["E-3"])
        self.assertTrue(K["R-2"])         # 6 は 6 以上(境界)
        for r in R["ai"][u"行"]:
            if r[u"形が真"] and r[u"決まった"]:
                r[u"決まった"] = False
                break
        self.assertFalse(judge_all(R, self.F.seal, self.F.p28_moved)[5]["R-2"])
        R = copy.deepcopy(self.F.R)       # E-1: 4 state が違うと赤
        next(r for r in R["ai"][u"行"] if r[u"P27E の state"] == "GROUNDED")[u"P27E の state"] = "VALUE_MISMATCH"
        self.assertFalse(judge_all(R, self.F.seal, self.F.p28_moved)[4]["E-1"])

    def test_g_4_a_forbidden_key_a_leak_or_a_wrong_sha_turns_a_red(self):
        for f in (lambda R: R["r97"].__setitem__(u"key_leaks", ["x"]),
                  lambda R: R["rit"][u"注入ごとの結果"][0].__setitem__(u"元の字", "x"),
                  lambda R: R["ai"][u"行"][0].__setitem__(u"文", "x"),
                  lambda R: R["r97"][u"cache の前後"].__setitem__(u"変化なし", False),
                  lambda R: R["ai"].__setitem__(u"この script の sha256", "0" * 64),
                  lambda R: R["rit"].__setitem__(u"この script の sha256", "0" * 64),
                  lambda R: R["r97"][u"形が真の行"][0].__setitem__(u"docID", "S100ZZZZ") if R["r97"][u"形が真の行"] else R["r97"].__setitem__(u"key_leaks", ["x"]),
                  lambda R: R["ai"].__setitem__(u"注意", R["ai"][u"注意"] + " S100ZZZZ"),
                  lambda R: R["entry"]["claims"][0].__setitem__("state", "X"),
                  lambda R: R["ai"][u"配線の門"][u"(e) 行の対応"].__setitem__(u"対応しない", 1)):
            R = copy.deepcopy(self.F.R)
            f(R)
            self.assertTrue(record_problems(R, self.F.p27_docs))

    def test_g_6_prose_checks(self):
        self.assertEqual([], PR.prose_problems(self.doc))
        self.assertTrue(PR.prose_problems(self.doc + u"\n本文に 1234 という数がある。\n"))
        self.assertEqual([], PR.prose_problems(self.doc + u"\n本文に 1234 という数がある。【門なし】\n"))
        self.assertTrue(self.dp(doc=self.doc + u"\nS100ABCD\n"))
        self.assertTrue(self.dp(doc=self.doc + u"\n精度\n"))

    def test_g_7_a_changed_seal_prediction_character_turns_c_red(self):
        seal = self.F.seal.replace(u"**2〜4**", u"**2〜5**", 1)
        self.assertNotEqual(seal, self.F.seal)
        self.assertTrue(self.dp(seal=seal))


if __name__ == "__main__":
    unittest.main()
