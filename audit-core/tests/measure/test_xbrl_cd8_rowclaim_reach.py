# -*- coding: utf-8 -*-
u"""cd8 の系統の「行 -> claim」を位置で引き直した診断の門 ― 封 docs/XBRL_CD8_ROWCLAIM_REACH_SEAL_2026-10-29.md §5 の (a)〜(k)。

記録 ``fixtures/xbrl/cd8/rowclaim_reach_2026-10-29.json``(``measure/xbrl_cd8_rowclaim_reach_2026-10-29.py`` の出力)・文書 ``docs/XBRL_CD8_ROWCLAIM_REACH_DIAG_2026-10-29.md``。

  (a) 記録の行の (母集団, profile, 書類, id) の集合が、既存の記録の行の集合と同じ(A1 は p20_rerun の rows、A2 は period_bind の E4 > 行、B は W-B-1 の記録の rows)。字で留めない。母集団・型ごとの数も既存の記録と同じ。
  (b) 配線の門が全部通ったと記録されている(門の名前の集合・門ごとの数を既存の記録の行数から数え直す・cache の件数・key_leaks)。
  (c) 文書の表を記録から作り直して 1 行も違わない(``<!-- 門:start 名前 -->`` の中)。門の外の散文の数には【門なし】の印が要る。
  (d) CR-1〜CR-25 の当否を記録から求め(幅は封の表の字から読む。字で留めない)、封の字(予測・外れ方)と、文書の当否の表の字が一致する。
  (e) 分類(封 §2-4)と判定が変わる(封 §2-5)を、記録の行の欄から別の書き方で求め直して一致する。
  (f) engine の sha16 を ``ENGINE_AT_MEASURE``・``ENGINE_DECLARED`` で留める。
  (g) 偽物で赤: 記録の写しの分類・位置の claim の id・配線の旗・数え直しの 1 欄を変えると (b)(c)(e)(k) のどれかが赤、文書の表の 1 字で (c) が赤、封の予測の 1 字で (d) が赤。
  (h) 封と文書に 24 書類と新しい標本 30 書類の docID、claim の id の字が無い。
  (i) 封の commit が script・記録・文書・門の commit より前(git の commit の順)。
  (j) 記録が持つ読んだ記録の sha256 がいまの file と一致する。生きた文書 2 本(台帳・総点検の文書)だけは file 全体でなく「読んだ部分」で照らす(封の追記 2026-10-29)。
      台帳 = §2-7 の対象の行の字を改行でつないだものの sha256、総点検の文書 = 読み分けの表(ledger)の門のブロックの中の字の sha256。
      部分の切り方は script の関数を使わず、この門が自分で切る(script と同じ誤りを共有しない)。file 全体の sha256 は情報で、門は照らさない。
  (k) 封 §2-6 の 1 の数え直しを記録の行から別の実装で作り直して一致し、§2-7 の台帳の行の語を facts_check で求め直して一致する。

**(i) は、script・記録・文書・門のどれかが commit される前は赤になる**(追跡されていない file には『足した commit』が無い)。skip にしない。
**変数名について**: 過去の門が tests/measure の行頭の名前(``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``)を数えるので、この門はそれらを行頭に置かない。
この file は docID の字を持たない(記録・取得の記録から読む)。
"""
import collections
import copy
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"

SEAL_REL = "docs/XBRL_CD8_ROWCLAIM_REACH_SEAL_2026-10-29.md"
DOC_REL = "docs/XBRL_CD8_ROWCLAIM_REACH_DIAG_2026-10-29.md"
REC_REL = "fixtures/xbrl/cd8/rowclaim_reach_2026-10-29.json"
SCRIPT_REL = "measure/xbrl_cd8_rowclaim_reach_2026-10-29.py"
GATE_REL = "tests/measure/test_xbrl_cd8_rowclaim_reach.py"
FETCHED_FRESH_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"
HARNESS_REL = "docs/XBRL_INJECT_HARNESS_REVIEW_2026-10-29.md"
FACTS_REL = "docs/FACTS_FOR_BUYERS_2026-10-20.md"
SEAL, DOC, REC = [os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL)]
SCRIPT = os.path.join(ROOT, SCRIPT_REL)
SEAL_COMMIT_SHORT = "5f3ae0a"

POPS = ("A1", "A2", "B1", "B2")
PROFS = {"A1": ("P16",), "A2": ("P22", "P27"), "B1": ("P16", "P20", "P21"), "B2": ("P16", "P20", "P21")}
UNITS = [(p, f) for p in POPS for f in PROFS[p]]
NOT_GATED = u"【門なし】"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
FORBIDDEN = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")

W_UNFIX, W_MANY, W_NONE = u"(位置が決まらない)", u"(位置で 1 件に決まらない)", u"(両方なし)"
W_VONLY, W_PONLY, W_SAME, W_DIFF = u"(値だけ)", u"(位置だけ)", u"(同じ)", u"(違う)"
WORDS7 = (W_UNFIX, W_MANY, W_NONE, W_VONLY, W_PONLY, W_SAME, W_DIFF)
T_SAME, T_WS, T_OTHER = u"字で同じ", u"空白だけ違う", u"空白以外が違う"
D_SAMESENT = u"同じ文・別の数"
HIT, MISS, NOJ = u"**当たり**", u"**外れ**", u"**判定しない**"

#: engine の sha16(記録を測った時点の値。字で留める ― 測った事実)。変えるなら宣言された遷移として下の ENGINE_DECLARED に足す。
ENGINE_AT_MEASURE = {
    "adapters/xbrl/extract.py": "3cf55966f12919f0", "adapters/xbrl/vocabulary.py": "514ebb8104451c07", "adapters/xbrl/recipes.py": "52d645e713c53c1c",
    "adapters/xbrl/resolve.py": "a41043763c1d4073", "adapters/xbrl/comparators.py": "d8706338325e725b", "adapters/xbrl/verify_document.py": "c3791080ab5aef2f",
}
#: 宣言された遷移 {file: (遷移の後の sha16, その遷移を宣言した封)}。今は 0 件。足すときは、封が履歴に在り、値が宣言の値のときだけ受け入れる。
# 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。この 6 本のうち動くのは vocabulary.py(旗 1 つ・P27C・PROFILES の登録)と
# verify_document.py(Claim の欄 candidate)。測った時点の値は ENGINE_AT_MEASURE に残す。受け入れるのは、その封が履歴に在り、値が候補の欄の後の値のときだけ。
ENGINE_DECLARED = {"adapters/xbrl/vocabulary.py": ("7fbcfbf0e472f366", "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md"),
                   "adapters/xbrl/verify_document.py": ("6c76c8ade6c7b1c8", "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md")}

#: 記録から求めた当否のうち外れ・判定しないの名前(測った事実。外れは外れのまま残す。封も予測も直さない)。食い違えば d_5 が赤。
MISSES = ["CR-3", "CR-6", "CR-7", "CR-9", "CR-11", "CR-16", "CR-19", "CR-25"]
UNDECIDED = []


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    return json.loads(jtext(p))


def rload(rel):
    return jload(os.path.join(ROOT, rel))


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def sha64(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def rate(a, b):
    return u"%d / %d = %.1f%%" % (a, b, 100.0 * a / b) if b else u"%d / 0" % a


def n_of(n, d):
    return u"%d / %d" % (n, d)


def table(head, rows):
    lines = [u"| " + u" | ".join(head) + u" |", u"|" + u"|".join(u"---" for _ in head) + u"|"]
    for r in rows:
        lines.append(u"| " + u" | ".join(str(c) for c in r) + u" |")
    return lines


def rt(x):
    return json.loads(json.dumps(x, ensure_ascii=False))


def U(rec, pop, prof=None):
    return [r for r in rec[u"rows"] if r[u"母集団"] == pop and (prof is None or r[u"profile"] == prof)]


def C(rows):
    c = collections.Counter(r[u"分類"] for r in rows)
    return c


# ----------------------------------------------------------------------------------------------------------------
# (a)(b) 記録の行の集合・配線の門
EXPECTED_GATES = (
    u"W-A1-1 ZIP の sha256", u"W-A1-1 材料の sha256", u"W-A1-2 値で引いた id = p20_rerun の主張 id(P16)", u"W-A1-3 判定 = 材料の Core・Core(厳しい読み方)",
    u"W-A1-4 rowclaim_map の合計 10 欄", u"W-A1-5 role_swap の主張 id = 値で引いた id", u"W-A1-5 verify_inventory の主張 id = 値で引いた id", u"W-A1-5 pnf_diag の主張 id = 値で引いた id",
    u"W-A2-1 材料の sha256", u"W-A2-2 P22 core_say_for と同じ", u"W-A2-2 P27 core_say_for と同じ", u"W-A2-2 P22 の判定 = E4 の Core 自身 P22",
    u"W-A2-3 P27 の注入で GROUNDED の数 = default_p27 の記録",
    u"W-B-2 Recorder の件数 = rows", u"W-B-2 拾った claim の id = c0 の記録(P16)", u"W-B-2 拾った claim の id = c0 の記録(P20)",
    u"W-S 値で引いた判定のまま数え直すと記録と同じ", u"DEFAULT_PROFILE が P27",
) + tuple(u"W-B-1 run_doc の rows = 記録の rows(%s %s)" % (p, f) for p in ("B1", "B2") for f in ("P16", "P20", "P21")) + (
    u"集合 A1 の行 = p20_rerun の rows", u"集合 A2 の行 = period_bind の E4 > 行",
    u"集合 W-A1-5 role_swap の行がこの便の行に全部在る", u"集合 W-A1-5 verify_inventory の行がこの便の行に全部在る", u"集合 W-A1-5 pnf_diag の行がこの便の行に全部在る",
) + tuple(u"集合 %s %s の注入 = 記録の rows" % (p, f) for p in ("B1", "B2") for f in ("P16", "P20", "P21"))


def sources():
    u"""既存の記録(読むだけ)。(a)(b) の期待を作る。"""
    S = {}
    for k, rel in (("draw", "fixtures/xbrl/cd8/draw_2026-10-17.json"), ("mat", "fixtures/xbrl/cd8/material_2026-10-17.json"),
                   ("p20", "fixtures/xbrl/cd8/p20_rerun_2026-10-17.json"), ("s2", "fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json"),
                   ("pb", "fixtures/xbrl/period_bind_2026-10-20.json"), ("acp16", "fixtures/xbrl/cd8/a_core_vs_grep_2026-10-17.json"),
                   ("acp20", "fixtures/xbrl/cd8/a_core_vs_grep_P20_2026-10-17.json"), ("nf", "fixtures/xbrl/naming_fix/p21_2026-10-20.json"),
                   ("c0", "fixtures/xbrl/gen_c/c0_2026-10-20.json"), ("c0p", "fixtures/xbrl/gen_c/c0_p20_2026-10-20.json")):
        S[k] = rload(rel)
    return S


def source_rows(S):
    u"""{(母集団, profile): [(doc, id, 型 or None)]}。"""
    out = {}
    out[("A1", "P16")] = [(r["doc"], r["id"]) for r in S["p20"]["rows"]]
    for f in PROFS["A2"]:
        out[("A2", f)] = [(r["doc"], r["id"]) for r in S["pb"]["E4"][u"行"]]
    brec = {("B1", "P16"): S["acp16"]["rows"], ("B1", "P20"): S["acp20"]["rows"], ("B1", "P21"): S["nf"][u"cd8 (ア) rows(P21)"],
            ("B2", "P16"): S["c0"][u"C0-2 rows"], ("B2", "P20"): S["c0p"][u"C0-2 rows(P20)"], ("B2", "P21"): S["nf"][u"gen_c (ア) rows(P21)"]}
    for k, v in brec.items():
        out[k] = [(r["doc"], r["id"]) for r in v]
    return out, brec


def source_types(S, brec):
    u"""{(母集団, profile): Counter(型)}。型は既存の記録から(A1 は材料の注入の型の内訳 + 無改変、A2 は E4 の注入の型、B は rows の 型)。"""
    out = {}
    c = collections.Counter()
    for p in S["mat"][u"書類ごと"]:
        for t, n in p[u"注入"][u"型の内訳"].items():
            c[t] += n
        c[None] += p[u"行"][u"無改変の行"]
    out[("A1", "P16")] = c
    for f in PROFS["A2"]:
        out[("A2", f)] = collections.Counter(r[u"注入の型"] for r in S["pb"]["E4"][u"行"])
    for k, v in brec.items():
        out[k] = collections.Counter(r[u"型"] for r in v)
    return out


def check_a(rec, S=None):
    out = []
    S = S or sources()
    want, brec = source_rows(S)
    wtype = source_types(S, brec)
    if rec.get(u"全書類") is not True:
        out.append(u"全書類の記録でない")
    docs = rec[u"書類(出てくる順)"]
    exp_docs = {"A1": list(S["draw"][u"引いた 8 件"]), "A2": [p["docID"] for p in S["s2"][u"書類ごと"]], "B1": list(S["acp16"][u"書類"]), "B2": list(S["c0"][u"材料"][u"書類"])}
    if docs != exp_docs:
        out.append(u"書類の並びが既存の記録と違う")
    for pop, prof in UNITS:
        got = [(r["doc"], r["id"]) for r in U(rec, pop, prof)]
        if sorted(got) != sorted(want[(pop, prof)]) or len(set(got)) != len(got):
            out.append(u"%s %s の行の集合が既存の記録の行の集合と違う" % (pop, prof))
        gt = collections.Counter(r[u"型"] for r in U(rec, pop, prof))
        if gt != wtype[(pop, prof)]:
            out.append(u"%s %s の型ごとの数が既存の記録と違う" % (pop, prof))
    if rec[u"rows"] and set(r[u"母集団"] for r in rec[u"rows"]) != set(POPS):
        out.append(u"母集団が 4 つでない")
    return out


def expected_gate_counts(S):
    want, brec = source_rows(S)
    n = {}
    d8 = len(S["draw"][u"引いた 8 件"])
    n[u"W-A1-1 ZIP の sha256"] = n[u"W-A1-1 材料の sha256"] = d8
    n[u"W-A1-2 値で引いた id = p20_rerun の主張 id(P16)"] = n[u"W-A1-3 判定 = 材料の Core・Core(厳しい読み方)"] = len(want[("A1", "P16")])
    n[u"W-A1-4 rowclaim_map の合計 10 欄"] = 10
    n[u"W-A2-1 材料の sha256"] = len(S["s2"][u"書類ごと"])
    n[u"W-A2-2 P22 core_say_for と同じ"] = n[u"W-A2-2 P27 core_say_for と同じ"] = n[u"W-A2-2 P22 の判定 = E4 の Core 自身 P22"] = len(want[("A2", "P22")])
    for p in ("B1", "B2"):
        for f in PROFS[p]:
            n[u"W-B-1 run_doc の rows = 記録の rows(%s %s)" % (p, f)] = 8
    n[u"W-B-2 Recorder の件数 = rows"] = 8 * 6
    n[u"W-B-2 拾った claim の id = c0 の記録(P16)"] = n[u"W-B-2 拾った claim の id = c0 の記録(P20)"] = len(want[("B2", "P16")])
    return n


def check_b(rec, S=None):
    out = []
    S = S or sources()
    g = rec[u"配線の門"]
    if set(g) != set(EXPECTED_GATES):
        out.append(u"配線の門の名前の集合が封の門と違う: 足りない %s / 余り %s" % (sorted(set(EXPECTED_GATES) - set(g)), sorted(set(g) - set(EXPECTED_GATES))))
    for k, v in g.items():
        if not (v[u"通った"] is True and v[u"一致"] == v[u"数"] and v[u"数"] > 0):
            out.append(u"門が通っていない: %s" % k)
    for k, n in expected_gate_counts(S).items():
        if k in g and g[k][u"数"] != n:
            out.append(u"門の数が既存の記録から数えた数と違う: %s %d / %d" % (k, g[k][u"数"], n))
    for k in (u"W-A1-5 role_swap の主張 id = 値で引いた id", u"W-A1-5 verify_inventory の主張 id = 値で引いた id", u"W-A1-5 pnf_diag の主張 id = 値で引いた id"):
        rel = {"role_swap": ("fixtures/xbrl/cd8/role_swap_2026-10-17.json", u"主張 id"), "verify_inventory": ("fixtures/xbrl/cd8/verify_inventory_2026-10-17.json", u"主張 id"),
               "pnf_diag": ("fixtures/xbrl/cd8/pnf_diag_2026-10-17.json", u"Core の主張 id")}[k.split(" ")[1]]
        j = rload(rel[0])
        rows = j[u"**第 2 部 実物での発火**"]["rows"] if "verify_inventory" in rel[0] else j["rows"]
        if k in g and g[k][u"数"] != sum(1 for r in rows if r.get(rel[1]) is not None):
            out.append(u"%s の数が記録の主張 id が None でない行の数と違う" % k)
    c = rec[u"cache"]
    if c[u"開始"] != c[u"終了"] or c[u"開始"][u"edinet"] != 281 or c[u"開始"][u"edinet-fresh-2026-10-21"] != 40:
        out.append(u"cache の件数が 281 / 40 のまま動いていない")
    if rec[u"key_leaks"] != []:
        out.append(u"key_leaks が空でない")
    if rec[u"DEFAULT_PROFILE"] != "P27":
        out.append(u"DEFAULT_PROFILE が P27 でない")
    return out


LIVE_DOCS = (FACTS_REL, HARNESS_REL)


def ledger_block_cut(text):
    u"""総点検の文書の ``<!-- 門:start ledger -->`` と次の ``<!-- 門:end -->`` の間の行を改行でつないだもの。印は 1 つずつ在らなければ None。
    (script の正規表現とは別の書き方 ― 行を 1 本ずつ見る。)"""
    lines = text.split(u"\n")
    starts = [i for i, ln in enumerate(lines) if ln == u"<!-- 門:start ledger -->"]
    if len(starts) != 1:
        return None
    ends = [i for i in range(starts[0] + 1, len(lines)) if lines[i] == u"<!-- 門:end -->"]
    if not ends:
        return None
    return u"\n".join(lines[starts[0] + 1:ends[0]])


def ledger_rows_cut(harness_text, facts_text):
    u"""(ID の列, 行の字を改行でつないだもの)。対象の ID = 門のブロックの表の行のうち 2 つ目の欄が M-03・05・13・16・18・20・21・23 のどれかを含む行の ID。
    台帳の file の並びで取り、対象の ID の行が 1 つずつ在らなければ None。"""
    blk = ledger_block_cut(harness_text)
    if blk is None:
        return None
    want = set()
    for ln in blk.split(u"\n"):
        if not ln.startswith(u"|"):
            continue
        cells = [c.strip() for c in ln.strip().strip(u"|").split(u"|")]
        if len(cells) >= 4 and re.match(r"^[A-Z]+-\d+$", cells[0]) and re.search(r"M-(03|05|13|16|18|20|21|23)\b", cells[1]):
            want.add(cells[0])
    got = collections.OrderedDict()
    for ln in facts_text.split(u"\n"):
        if ln.startswith(u"|"):
            c0 = ln.strip().strip(u"|").split(u"|")[0].strip()
            if c0 in want:
                got.setdefault(c0, []).append(ln)
    if set(got) != want or any(len(v) != 1 for v in got.values()):
        return None
    return list(got), u"\n".join(v[0] for v in got.values())


def text_sha(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def check_j(rec, harness_text=None, facts_text=None):
    u"""読んだ記録の sha256(file 全体)と、生きた文書 2 本の読んだ部分の sha256 を、いまの file から求め直して照らす。
    生きた文書の file 全体の sha256 は情報で、照らさない(``harness_text``・``facts_text`` は作り物の入力で試すための引数)。"""
    out = []
    got = rec[u"読んだ記録の sha256"]
    if not got:
        out.append(u"読んだ記録の sha256 が空")
    for rel, want in got.items():
        if not os.path.exists(os.path.join(ROOT, rel)) or sha64(rel) != want:
            out.append(u"%s の sha256 が記録の写しと違う(読み直しの元が動いた)" % rel)
    for rel in ("fixtures/xbrl/cd8/material_2026-10-17.json", "fixtures/xbrl/cd8/score_2026-10-17.json", "fixtures/xbrl/period_bind_2026-10-20.json"):
        if rel not in got:
            out.append(u"読んだ記録の一覧に無い: %s" % rel)
    for rel in LIVE_DOCS:
        if rel in got:
            out.append(u"生きた文書 %s が file 全体の sha256 で照らす側に在る(読んだ部分で照らす)" % rel)
    part = rec.get(u"読んだ生きた文書の部分の sha256")
    if not isinstance(part, dict) or set(part) != set(LIVE_DOCS):
        out.append(u"読んだ生きた文書の部分の sha256 が 2 本そろっていない")
        return out
    if harness_text is None:
        harness_text = jtext(os.path.join(ROOT, HARNESS_REL))
    if facts_text is None:
        facts_text = jtext(os.path.join(ROOT, FACTS_REL))
    blk = ledger_block_cut(harness_text)
    if blk is None:
        out.append(u"総点検の文書に読み分けの表の門のブロックが 1 つだけ在らない")
    elif text_sha(blk) != part[HARNESS_REL].get(u"sha256"):
        out.append(u"総点検の文書の読み分けの表の門のブロックが記録の写しと違う")
    rows = ledger_rows_cut(harness_text, facts_text)
    if rows is None:
        out.append(u"台帳に §2-7 の対象の行が 1 つずつ在らない")
    else:
        if rows[0] != part[FACTS_REL].get(u"ID の列"):
            out.append(u"台帳の §2-7 の対象の ID の列が記録の写しと違う")
        if text_sha(rows[1]) != part[FACTS_REL].get(u"sha256"):
            out.append(u"台帳の §2-7 の対象の行の字が記録の写しと違う")
    return out


# ----------------------------------------------------------------------------------------------------------------
# (e) 分類と判定が変わるを、記録の行の欄から別の書き方で求め直す
def class_again(r):
    u"""行の欄だけから分類(封 §2-4)を求める。"""
    if r[u"文の番号"] is None or r[u"写した範囲"] is None:
        return W_UNFIX
    cand = r[u"位置の候補"]
    vid = (r[u"値で引いた"] or {}).get(u"id")
    pid = (r[u"位置で引いた"] or {}).get(u"id")
    if len(cand) > 1:
        return W_MANY
    if not cand:
        return W_NONE if vid is None else W_VONLY
    if vid is None:
        return W_PONLY
    return W_SAME if pid == vid else W_DIFF


def judge_key(pop, j):
    if j is None:
        return None
    if pop == "A1":
        return [j[u"Core"][:2], j[u"Core(厳しい読み方)"][:2]]
    return j


def changed_again(r):
    jv, jp = r[u"判定(値)"], r[u"判定(位置)"]
    if r[u"分類"] in (W_UNFIX, W_MANY):
        return None
    return judge_key(r[u"母集団"], jv) != judge_key(r[u"母集団"], jp)


def check_e(rec):
    out = []
    for i, r in enumerate(rec[u"rows"]):
        w = class_again(r)
        if r[u"分類"] != w:
            out.append(u"行 %d: 分類が欄から求めた語と違う: %s / %s" % (i, r[u"分類"], w))
        if r[u"分類"] not in WORDS7:
            out.append(u"行 %d: 分類が 7 語の外" % i)
        cand = r[u"位置の候補"]
        pid = (r[u"位置で引いた"] or {}).get(u"id")
        if (len(cand) == 1) != (r[u"位置で引いた"] is not None) or (cand and len(cand) == 1 and pid != cand[0]):
            out.append(u"行 %d: 位置で引いた claim が候補の 1 件と合わない" % i)
        if r[u"分類"] in (W_UNFIX, W_MANY):
            if r[u"判定(位置)"] is not None or r[u"判定が変わる"] is not None:
                out.append(u"行 %d: 決まらない行に判定(位置)がある" % i)
        else:
            if r[u"判定(位置)"] is None:
                out.append(u"行 %d: 決まった行に判定(位置)が無い" % i)
            elif r[u"判定が変わる"] != changed_again(r):
                out.append(u"行 %d: 判定が変わるが欄から求めた値と違う" % i)
        if r[u"分類"] == W_UNFIX and r[u"細目"] is None:
            out.append(u"行 %d: 決まらない行に理由が無い" % i)
        if r[u"写した範囲"] is not None and r[u"本文"] == T_OTHER:
            out.append(u"行 %d: 空白以外が違うのに範囲を写している" % i)
        if r[u"分類"] == W_DIFF and r[u"細目"] not in (D_SAMESENT, u"別の文", u"値で引いた claim が num の claim でない"):
            out.append(u"行 %d: (違う)の細目が決まった語でない" % i)
    # A1 の共有された行は値で引いた id から数え直す
    by = collections.defaultdict(collections.Counter)
    for r in U(rec, "A1"):
        if r[u"値で引いた"]:
            by[r["doc"]][r[u"値で引いた"][u"id"]] += 1
    for r in U(rec, "A1"):
        sh = bool(r[u"値で引いた"] and by[r["doc"]][r[u"値で引いた"][u"id"]] > 1)
        if r[u"共有された"] != sh:
            out.append(u"A1 の共有された行が値で引いた id から数えた値と違う")
            break
    # B: diff_sentence との照合の欄
    for r in rec[u"rows"]:
        if r[u"母集団"] in ("B1", "B2") and r.get(u"diff_sentence と同じ") is not None:
            if r[u"型"] == "T3_ABSENT" or (r[u"diff_sentence と同じ"] != (r[u"diff_sentence の番号"] == r[u"文の番号"])):
                out.append(u"B の diff_sentence の照合の欄が行の欄と合わない")
                break
    return out


# ----------------------------------------------------------------------------------------------------------------
# (d) CR-1〜CR-25 の当否を記録から求める(幅は封の表の字から読む)
BOLD = re.compile(r"\*\*(.+?)\*\*")
RANGE_RE = re.compile(r"^(\d+(?:\.\d+)?)%? 以上 (\d+(?:\.\d+)?)%? 以下$")
LOW_RE = re.compile(r"^(\d+(?:\.\d+)?)%? 以上$")
UP_RE = re.compile(r"^(\d+(?:\.\d+)?)%? 以下$")


def seal_predictions(seal):
    u"""封 §3 の表の行 {名前: (欄, 予測, 外れ方)}(封の字のまま)。"""
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(CR-\d+)\*\* \| (.*) \|$", l)
        if m:
            cells = m.group(2).split(u" | ")
            assert len(cells) == 3, l
            out[m.group(1)] = tuple(c.strip() for c in cells)
    return out


def ranges_of(cell):
    return [(float(m.group(1)), float(m.group(2))) for m in (RANGE_RE.match(b) for b in BOLD.findall(cell)) if m]


def lows_of(cell):
    return [float(m.group(1)) for m in (LOW_RE.match(b) for b in BOLD.findall(cell)) if m]


def ups_of(cell):
    return [float(m.group(1)) for m in (UP_RE.match(b) for b in BOLD.findall(cell)) if m]


def within(n, rg):
    return rg[0] <= n <= rg[1]


def hit_word(b):
    return NOJ if b is None else (HIT if b else MISS)


def item(rec, pop, prof, label):
    xs = [x for x in rec[u"数え直し(§2-6 の 1)"] if x[u"母集団"] == pop and x[u"profile"] == prof and x[u"欄"] == label]
    assert len(xs) == 1, (pop, prof, label)
    return xs[0]


def leaf(d, *path):
    for k in path:
        d = d[k]
    return d


def ovl(rec, pop, prof, rel_part, name_part):
    xs = [o for o in rec[u"行の重なり(§2-6 の 2)"] if o[u"母集団"] == pop and o[u"profile"] == prof and rel_part in o[u"記録"] and name_part in o[u"節"]]
    assert len(xs) == 1, (pop, prof, rel_part, name_part)
    return xs[0]


def judge(rec, seal):
    u"""{名前: (実測の字, 当たりか(True / False / None=判定しない))}。封 §3 の予測を記録から。幅は封の字から読む。"""
    SP = seal_predictions(seal)
    out = collections.OrderedDict()
    A1, A2 = U(rec, "A1", "P16"), None
    g = rec[u"配線の門"]
    gA1 = [k for k in g if k.startswith(u"W-A1-")]

    def A(name):
        return g[name]
    # CR-1
    pairs = [tuple(int(x) for x in m) for m in re.findall(r"(\d+) / (\d+)", SP["CR-1"][1])]
    got = [(A(k)[u"一致"], A(k)[u"数"]) for k in (u"W-A1-1 ZIP の sha256", u"W-A1-1 材料の sha256", u"W-A1-2 値で引いた id = p20_rerun の主張 id(P16)", u"W-A1-3 判定 = 材料の Core・Core(厳しい読み方)")]
    out["CR-1"] = (u"A1 の門 %d 本が全部通った(%s)" % (len(gA1), u"・".join(n_of(a, b) for a, b in got)), all(g[k][u"通った"] for k in gA1) and got == pairs and len(gA1) == 8)
    # CR-2
    gO = [k for k in g if not k.startswith(u"W-A1-")]
    out["CR-2"] = (u"A1 以外の門 %d 本が全部通った" % len(gO), all(g[k][u"通った"] for k in gO))
    # CR-3
    wt = collections.Counter()
    for u in rec[u"W-T の単位ごと"]:
        for w, n in u[u"本文の語ごとの verify の数"].items():
            wt[(u[u"母集団"], w)] += n
    tot = lambda pops: sum(n for (p, w), n in wt.items() if p in pops)
    same = lambda pops: sum(n for (p, w), n in wt.items() if p in pops and w == T_SAME)
    want = [int(x) for x in re.findall(r"(\d+) / (\d+)", SP["CR-3"][1])[0]], [int(x) for x in re.findall(r"(\d+) / (\d+)", SP["CR-3"][1])[1]]
    out["CR-3"] = (u"本文が字で同じ verify: A1 %s・A2 %s・B1 %s・B2 %s(空白だけ違う: %d・空白以外が違う: %d)" % (
        n_of(same(("A1",)), tot(("A1",))), n_of(same(("A2",)), tot(("A2",))), n_of(same(("B1",)), tot(("B1",))), n_of(same(("B2",)), tot(("B2",))),
        sum(n for (p, w), n in wt.items() if w == T_WS), sum(n for (p, w), n in wt.items() if w == T_OTHER)),
        tot(("A1",)) == want[0][1] and tot(("A2",)) == want[1][1] and same(("A1", "A2", "B1", "B2")) == tot(("A1", "A2", "B1", "B2")))
    c1 = C(A1)
    # CR-4
    n = c1[W_UNFIX] + c1[W_MANY]
    out["CR-4"] = (u"A1 の%s+%s: %s" % (W_UNFIX, W_MANY, n_of(n, len(A1))), within(n, ranges_of(SP["CR-4"][1])[0]))
    out["CR-5"] = (u"A1 の%s: %s" % (W_SAME, n_of(c1[W_SAME], len(A1))), within(c1[W_SAME], ranges_of(SP["CR-5"][1])[0]))
    out["CR-6"] = (u"A1 の%s: %s" % (W_DIFF, n_of(c1[W_DIFF], len(A1))), within(c1[W_DIFF], ranges_of(SP["CR-6"][1])[0]))
    out["CR-7"] = (u"A1 の%s: %s" % (W_VONLY, n_of(c1[W_VONLY], len(A1))), within(c1[W_VONLY], ranges_of(SP["CR-7"][1])[0]))
    out["CR-8"] = (u"A1 の%s: %s" % (W_PONLY, n_of(c1[W_PONLY], len(A1))), within(c1[W_PONLY], ranges_of(SP["CR-8"][1])[0]))
    # CR-9
    sh = [r for r in A1 if r[u"共有された"]]
    cs = C(sh)
    rg = ranges_of(SP["CR-9"][1])
    out["CR-9"] = (u"A1 の共有された行 %d: %s %d・%s %d" % (len(sh), W_SAME, cs[W_SAME], W_DIFF, cs[W_DIFF]), within(cs[W_SAME], rg[0]) and within(cs[W_DIFF], rg[1]))
    # CR-10
    t5 = [r for r in A1 if r[u"型"] == "T5_COINCIDENT"]
    c5 = C(t5)
    rg = ranges_of(SP["CR-10"][1])
    z = c5[W_VONLY] + c5[W_UNFIX]
    out["CR-10"] = (u"A1 の T5 %d 行: %s %d・%s %d・%s+%s %d" % (len(t5), W_SAME, c5[W_SAME], W_DIFF, c5[W_DIFF], W_VONLY, W_UNFIX, z),
                    within(c5[W_SAME], rg[0]) and within(c5[W_DIFF], rg[1]) and within(z, rg[2]))
    # CR-11 / CR-12
    df = [r for r in A1 if r[u"分類"] == W_DIFF]
    same_sent = sum(1 for r in df if r[u"細目"] == D_SAMESENT)
    lo = lows_of(SP["CR-11"][1])[0]
    out["CR-11"] = (u"A1 の%s の細目 %s: %s" % (W_DIFF, D_SAMESENT, rate(same_sent, len(df)) if df else u"分母 0"), (same_sent * 100 >= lo * len(df)) if df else None)
    chg = sum(1 for r in df if r[u"判定が変わる"])
    lo = lows_of(SP["CR-12"][1])[0]
    out["CR-12"] = (u"A1 の%s のうち判定が変わる: %s" % (W_DIFF, rate(chg, len(df)) if df else u"分母 0"), (chg * 100 >= lo * len(df)) if df else None)
    # CR-13
    sc = item(rec, "A1", "P16", u"採点")
    zi = item(rec, "A1", "P16", u"主比較の判定")
    cell = SP["CR-13"][1]
    a_num, a_den = [int(x) for x in re.search(r"(\d+) / (\d+) のまま", cell).groups()]
    tol = int(re.search(r"±(\d+) 以内", cell).group(1))
    center = int(re.search(r"記録\((\d+)\)", cell).group(1))
    P = sc[u"位置で数え直し"]
    ident = P[u"C′"][u"正しい参照先の特定"]
    wrong = P[u"C′"][u"誤認定"][u"分子"]
    others = [p for p in sc[u"動いた欄"] if not p.startswith(u"C′ > ")]
    zz = zi[u"位置で数え直し"]
    out["CR-13"] = (u"C′ の特定 %s(記録 %d)・Z-1 %s・Z-2 %s・C′ の誤認定の分子 %d(記録 %d)・A・D′・D″ の動いた欄 %d" % (
        n_of(ident[u"分子"], ident[u"分母(T5 の件)"]), sc[u"記録"][u"C′"][u"正しい参照先の特定"][u"分子"], zz[u"Z-1 誤認定が減った"], zz[u"Z-2 正しい特定が増えた"], wrong,
        sc[u"記録"][u"C′"][u"誤認定"][u"分子"], len(others)),
        (ident[u"分子"], ident[u"分母(T5 の件)"]) == (a_num, a_den) and zz[u"Z-1 誤認定が減った"] is False and zz[u"Z-2 正しい特定が増えた"] is False
        and abs(wrong - center) <= tol and not others)
    # CR-14
    ce = item(rec, "A1", "P16", u"α の天井")
    sp = item(rec, "A1", "P16", u"Core 自身の特定率(本番)")
    rg = ranges_of(SP["CR-14"][1])
    fx = ce[u"位置で数え直し"][u"**Core が正解を持っていた**"]
    num = sp[u"位置で数え直し"][u"分子"]
    out["CR-14"] = (u"Core が正解を持っていた %d(記録 %d)・Core 自身の特定率の分子 %d / %d(記録 %d)" % (
        fx, ce[u"記録"][u"**Core が正解を持っていた**"], num, sp[u"位置で数え直し"][u"分母"], sp[u"記録"][u"分子"]), within(fx, rg[0]) and within(num, rg[1]))
    # CR-15
    o = ovl(rec, "A1", "P16", "role_swap", u"主張 id が None でない")
    out["CR-15"] = (u"role_swap の主張 id が None でない行 %d のうち%s%s%s: %d" % (o[u"行の集合"], W_DIFF, W_VONLY, W_PONLY, o[u"分類が(違う)(値だけ)(位置だけ)の行"]),
                    within(o[u"分類が(違う)(値だけ)(位置だけ)の行"], ranges_of(SP["CR-15"][1])[0]))
    # CR-16
    a22, a27 = U(rec, "A2", "P22"), U(rec, "A2", "P27")
    c22, c27 = C(a22), C(a27)
    rg = ranges_of(SP["CR-16"][1])
    tl = int(re.search(r"±(\d+) 以内", SP["CR-16"][1]).group(1))
    z = c22[W_UNFIX] + c22[W_MANY]
    out["CR-16"] = (u"A2 P22: %s %d・%s %d・決まらない 2 語 %d。P27 の%s %d" % (W_DIFF, c22[W_DIFF], W_SAME, c22[W_SAME], z, W_DIFF, c27[W_DIFF]),
                    within(c22[W_DIFF], rg[0]) and within(c22[W_SAME], rg[1]) and within(z, rg[2]) and abs(c27[W_DIFF] - c22[W_DIFF]) <= tl)
    # CR-17
    rg = ranges_of(SP["CR-17"][1])
    s6 = item(rec, "A2", "P27", u"全注入で Core 自身(既定)が GROUNDED")[u"位置で数え直し"]
    e4 = item(rec, "A2", "P22", u"E4 の集計")[u"位置で数え直し"][u"T6 で Core 自身 P22 が GROUNDED"]
    out["CR-17"] = (u"P27 の全注入で GROUNDED %s・P22 の T6 で GROUNDED %s" % (n_of(s6[u"件"], s6[u"分母"]), n_of(e4[u"件"], e4[u"分母"])), within(s6[u"件"], rg[0]) and within(e4[u"件"], rg[1]))
    # CR-18
    rg = ranges_of(SP["CR-18"][1])[0]
    ds = [(p, f, C(U(rec, p, f))[W_DIFF]) for p in ("B1", "B2") for f in PROFS[p]]
    out["CR-18"] = (u"B の%s: %s" % (W_DIFF, u"・".join(u"%s %s %d" % x for x in ds)), all(within(d, rg) for _, _, d in ds))
    # CR-19
    rg = ranges_of(SP["CR-19"][1])
    b1, b2 = C(U(rec, "B1", "P16"))[W_PONLY], C(U(rec, "B2", "P16"))[W_PONLY]
    out["CR-19"] = (u"B の%s(P16): B1 %d・B2 %d" % (W_PONLY, b1, b2), within(b1, rg[0]) and within(b2, rg[1]))
    # CR-20
    lo = lows_of(SP["CR-20"][1])[0]
    t3 = [(p, f, sum(1 for r in U(rec, p, f) if r[u"型"] == "T3_ABSENT" and r[u"分類"] == W_SAME), sum(1 for r in U(rec, p, f) if r[u"型"] == "T3_ABSENT")) for p in ("B1", "B2") for f in PROFS[p]]
    out["CR-20"] = (u"B の T3 の%s: %s" % (W_SAME, u"・".join(u"%s %s %d / %d" % x for x in t3)), all(s >= lo for _, _, s, _ in t3))
    # CR-21
    cell = SP["CR-21"][1]
    rg = ranges_of(cell)
    zero, zden = [int(x) for x in re.search(r"B1 P16 は (\d+) / (\d+)", cell).groups()]
    core_ok, parts, nodrop = True, [], True
    cp = {}
    for p in ("B1", "B2"):
        for f in PROFS[p]:
            it = [x for x in rec[u"数え直し(§2-6 の 1)"] if x[u"母集団"] == p and x[u"profile"] == f and x[u"欄"].startswith(u"採点(AC.tally")][0]
            v, q = it[u"値で数え直し"], it[u"位置で数え直し"]
            k0 = (v[u"Core"][u"特定率(分母 = T5 の件数)"][u"分子"], q[u"Core"][u"特定率(分母 = T5 の件数)"][u"分子"])
            k1 = (v[u"Core-P"][u"特定率(分母 = T5 の件数)"][u"分子"], q[u"Core-P"][u"特定率(分母 = T5 の件数)"][u"分子"])
            core_ok = core_ok and k0[0] == k0[1]
            nodrop = nodrop and k1[1] >= k1[0]
            cp[(p, f)] = k1
            parts.append(u"%s %s Core %d→%d・Core-P %d→%d" % (p, f, k0[0], k0[1], k1[0], k1[1]))
    b1p = [x for x in rec[u"数え直し(§2-6 の 1)"] if x[u"母集団"] == "B1" and x[u"profile"] == "P16" and x[u"欄"].startswith(u"採点(AC.tally")][0]
    z_ok = b1p[u"位置で数え直し"][u"Core"][u"特定率(分母 = T5 の件数)"][u"分子"] == zero and b1p[u"位置で数え直し"][u"Core"][u"特定率(分母 = T5 の件数)"][u"分母"] == zden
    out["CR-21"] = (u"・".join(parts), core_ok and z_ok and nodrop and within(cp[("B1", "P16")][1], rg[0]) and within(cp[("B2", "P16")][1], rg[1]))
    # CR-22
    led = rec[u"台帳の行(§2-7)"]
    ok12 = [x for x in led if x[u"読み"] == u"通った"]
    rg = ranges_of(SP["CR-22"][1])
    mv = sum(1 for x in ok12 if x[u"語"] == u"数が動く")
    pm = sum(1 for x in ok12 if x[u"語"] == u"動きうる(数え直していない)")
    out["CR-22"] = (u"台帳の『通った』%d 行: 数が動く %d・動きうる %d" % (len(ok12), mv, pm), within(mv, rg[0]) and within(pm, rg[1]))
    # CR-23
    ids = re.findall(r"[LDHP]-\d+", SP["CR-23"][0])
    five = [x for x in led if x[u"台帳の行"] in ids]
    ok5 = all(x[u"語"] in (u"動かない", u"この便の外") for x in five) and len(five) == len(ids)
    out["CR-23"] = (u"台帳の『通っていない』%d 行の語: %s。A1 の A・D′・D″ の動いた欄 %d" % (len(five), u"・".join(u"%s %s" % (x[u"台帳の行"], x[u"語"]) for x in five), len(others)), ok5 and not others)
    # CR-24
    allr = rec[u"rows"]
    nd = sum(1 for r in allr if r[u"分類"] in (W_UNFIX, W_MANY))
    cap = int(re.search(r"\((\d+) 以下\)", SP["CR-24"][1]).group(1))
    up = ups_of(SP["CR-24"][1])[0]
    out["CR-24"] = (u"決まらない 2 語の合計 %s" % n_of(nd, len(allr)), nd <= cap and nd * 100 <= up * len(allr))
    # CR-25
    nchg = sum(1 for r in allr if r[u"判定が変わる"])
    out["CR-25"] = (u"判定が変わる行の合計 %s" % n_of(nchg, len(allr)), within(nchg, ranges_of(SP["CR-25"][1])[0]))
    return out


# ----------------------------------------------------------------------------------------------------------------
# (c) 文書の表を記録から作る
def leaves(x, pre=u""):
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            out.update(leaves(v, pre + u" > " + str(k) if pre else str(k)))
        return out
    return {pre: x}


def fmt_leaf(v):
    if isinstance(v, list):
        return u"%d 件" % len(v)
    return str(v).replace(u"|", u"¦")


def fmt_moves(it, limit=6):
    a, b = leaves(rt(it[u"記録"])), leaves(rt(it[u"位置で数え直し"]))
    ps = it[u"動いた欄"]
    shown = [u"%s: %s → %s" % (p, fmt_leaf(a.get(p, u"(欄なし)")), fmt_leaf(b.get(p, u"(欄なし)"))) for p in ps[:limit]]
    if len(ps) > limit:
        shown.append(u"ほか %d 欄" % (len(ps) - limit))
    return u"、".join(shown) if shown else u"動いた欄なし"


def type_label(t):
    return {None: u"(注入なし)", "T1_VALUE": u"T1", "T2_UNIT": u"T2", "T3_ABSENT": u"T3", "T5_COINCIDENT": u"T5", "T6_PRIOR": u"T6", "T7_ROUND": u"T7"}[t]


def render_blocks(rec, seal):
    B = collections.OrderedDict()
    J = judge(rec, seal)
    SP = seal_predictions(seal)
    B["pred"] = table([u"#", u"欄", u"予測(封の字)", u"外れ方(封の字)", u"実測", u"当否"],
                      [(u"**%s**" % k, SP[k][0], SP[k][1], SP[k][2], J[k][0], hit_word(J[k][1])) for k in J])
    B["env"] = table([u"項目", u"値"], [(u"cache edinet 開始 / 終了", u"%d / %d" % (rec[u"cache"][u"開始"][u"edinet"], rec[u"cache"][u"終了"][u"edinet"])),
                                         (u"cache edinet-fresh 開始 / 終了", u"%d / %d" % (rec[u"cache"][u"開始"][u"edinet-fresh-2026-10-21"], rec[u"cache"][u"終了"][u"edinet-fresh-2026-10-21"])),
                                         (u"DEFAULT_PROFILE", rec[u"DEFAULT_PROFILE"]), (u"全書類", rec[u"全書類"]), (u"行(母集団 × profile の全部)", len(rec[u"rows"]))]
                     + [(u"engine sha16 " + k, v) for k, v in rec[u"engine sha16"].items()])
    B["gates"] = table([u"門", u"一致", u"数", u"通った"], [(k, v[u"一致"], v[u"数"], u"はい" if v[u"通った"] else u"いいえ") for k, v in rec[u"配線の門"].items()])
    B["rowclaim"] = table([u"rowclaim_map の合計の欄", u"記録", u"値で引いた id から数え直し"], [(k, v[0], v[1]) for k, v in rec[u"W-A1-4 の欄ごと(記録, 数え直し)"].items()])
    wt = collections.OrderedDict()
    for u in rec[u"W-T の単位ごと"]:
        for w, n in u[u"本文の語ごとの verify の数"].items():
            wt[(u[u"母集団"], u[u"profile"], w)] = wt.get((u[u"母集団"], u[u"profile"], w), 0) + n
    B["wt"] = table([u"母集団", u"profile", u"verify の数", T_SAME, T_WS, T_OTHER],
                    [(p, f, sum(wt.get((p, f, w), 0) for w in (T_SAME, T_WS, T_OTHER)), wt.get((p, f, T_SAME), 0), wt.get((p, f, T_WS), 0), wt.get((p, f, T_OTHER), 0)) for p, f in UNITS])
    rows = []
    for p, f in UNITS:
        rs = U(rec, p, f)
        c = C(rs)
        rows.append([p, f, len(rs)] + [c[w] for w in WORDS7] + [sum(1 for r in rs if r[u"判定が変わる"])])
    B["classes"] = table([u"母集団", u"profile", u"行"] + list(WORDS7) + [u"判定が変わる"], rows)
    rows = []
    for p, f in UNITS:
        ts = collections.OrderedDict()
        for r in U(rec, p, f):
            ts.setdefault(r[u"型"], []).append(r)
        for t in sorted(ts, key=lambda x: (x is not None, str(x))):
            c = C(ts[t])
            rows.append([p, f, type_label(t), len(ts[t])] + [c[w] for w in WORDS7] + [sum(1 for r in ts[t] if r[u"判定が変わる"])])
    B["types"] = table([u"母集団", u"profile", u"型", u"行"] + list(WORDS7) + [u"判定が変わる"], rows)
    rows = []
    for p, f in UNITS:
        c = collections.Counter((r[u"分類"], r[u"細目"]) for r in U(rec, p, f) if r[u"細目"] is not None)
        for (w, d), n in sorted(c.items(), key=lambda x: (WORDS7.index(x[0][0]), str(x[0][1]))):
            rows.append([p, f, w, d, n])
    B["detail"] = table([u"母集団", u"profile", u"分類", u"細目", u"行"], rows)
    a1 = U(rec, "A1", "P16")
    rows = []
    for nm, sel in ((u"共有された行(値で引いた claim を 2 行以上が指す)", [r for r in a1 if r[u"共有された"]]), (u"共有されていない行", [r for r in a1 if not r[u"共有された"]])):
        c = C(sel)
        rows.append([nm, len(sel)] + [c[w] for w in WORDS7] + [sum(1 for r in sel if r[u"判定が変わる"])])
    B["shared"] = table([u"A1 の行", u"行"] + list(WORDS7) + [u"判定が変わる"], rows)
    rows = []
    for k, v in rec[u"W-B-3 diff_sentence との照合"].items():
        rows.append([k, v[u"照合した行"], v[u"同じ"]])
    B["diffsent"] = table([u"単位", u"文の番号を diff_sentence と照合した行", u"同じ"], rows)
    rows = []
    for p in POPS:
        f = PROFS[p][0]
        docs = rec[u"書類(出てくる順)"][p]
        per = collections.defaultdict(list)
        for r in U(rec, p, f):
            per[r["doc"]].append(r)
        for w in (W_DIFF, W_PONLY, W_VONLY):
            n = 0
            for d in docs:
                for k, r in enumerate(per[d], 1):
                    if r[u"分類"] == w and n < 2:
                        n += 1
                        rows.append([p, f, docs.index(d) + 1, k, type_label(r[u"型"]), w, r[u"細目"], r[u"文の番号"], r[u"文の中の範囲"],
                                     (r[u"値で引いた"] or {}).get(u"文の番号"), (r[u"位置で引いた"] or {}).get(u"文の番号")])
    B["examples"] = table([u"母集団", u"profile", u"書類の位置", u"書類の中の行の位置", u"型", u"分類", u"細目", u"行の文の番号", u"文の中の範囲", u"値で引いた claim の文の番号", u"位置で引いた claim の文の番号"], rows)
    rows = []
    for p, f in UNITS:
        c = collections.Counter(r[u"分類"] for r in U(rec, p, f) if r[u"判定が変わる"])
        rows.append([p, f] + [c[w] for w in (W_DIFF, W_VONLY, W_PONLY, W_SAME, W_NONE, W_UNFIX, W_MANY)])
    B["changed"] = table([u"母集団", u"profile", u"判定が変わる行のうち" + W_DIFF, W_VONLY, W_PONLY, W_SAME, W_NONE, W_UNFIX, W_MANY], rows)
    B["recount"] = table([u"母集団", u"profile", u"欄", u"記録の節", u"値で数え直すと記録と同じ", u"動いた欄の数", u"動いた欄(記録 → 位置)"],
                         [(x[u"母集団"], x[u"profile"], x[u"欄"], x[u"記録の節"] or u"(記録に欄なし)", {True: u"はい", False: u"いいえ", None: u"(記録なし)"}[x[u"値で数え直しが記録と一致"]],
                           len(x[u"動いた欄"]), fmt_moves(x)) for x in rec[u"数え直し(§2-6 の 1)"]])
    B["overlap"] = table([u"母集団", u"profile", u"記録の節", u"行の集合", u"この便の行に在る", u"分類が" + W_DIFF + W_VONLY + W_PONLY + u"の行", u"決まらない 2 語", u"判定が変わる行"],
                         [(o[u"母集団"], o[u"profile"], o[u"記録"] + u" " + o[u"節"], o[u"行の集合"], o[u"この便の行に在る"], o[u"分類が(違う)(値だけ)(位置だけ)の行"],
                           o[u"(位置が決まらない)+(位置で 1 件に決まらない)"], o[u"判定が変わる行"]) for o in rec[u"行の重なり(§2-6 の 2)"]])
    B["ledger"] = table([u"台帳の行", u"引いた仕掛け", u"総点検の読み", u"印の数", u"本物で通らなかった印", u"動く印", u"引く記録の数", u"語"],
                        [(x[u"台帳の行"], x[u"引いた仕掛け"], x[u"読み"], x[u"印"], x[u"本物で通らなかった印"], x[u"動く印"], len(x[u"引く記録"]), x[u"語"]) for x in rec[u"台帳の行(§2-7)"]])
    c = collections.Counter((x[u"読み"], x[u"語"]) for x in rec[u"台帳の行(§2-7)"])
    words = (u"数が動く", u"動きうる(数え直していない)", u"動かない", u"この便の外")
    B["ledger_sum"] = table([u"総点検の読み", u"行"] + list(words),
                            [(rd, sum(c[(rd, w)] for w in words)) + tuple(c[(rd, w)] for w in words) for rd in (u"通った", u"通っていない", u"記録から分からない")])
    return B


BLOCK_RE = re.compile(r"<!-- 門:start (\S+) -->\n(.*?)\n<!-- 門:end -->", re.S)


def doc_blocks(doc):
    out = collections.OrderedDict()
    for m in BLOCK_RE.finditer(doc):
        if m.group(1) in out:
            raise AssertionError(u"同じ名前の門の表が 2 つ: " + m.group(1))
        out[m.group(1)] = m.group(2).split(u"\n")
    return out


def check_c(rec, seal, doc):
    u"""文書の表を記録から作り直して比べる。問題の列。"""
    out = []
    try:
        B = render_blocks(rec, seal)
    except Exception as e:      # 記録が壊れていれば作り直せない(それも赤)
        return [u"記録から表を作れない: %r" % (e,)]
    got = doc_blocks(doc)
    if list(got) != list(B):
        out.append(u"文書の門の表の名前と順が違う: %s" % list(got))
        return out
    for k, lines in B.items():
        if got[k] != lines:
            out.append(u"文書の表『%s』が記録から作った表と違う" % k)
    return out


def check_doc_prose(rec, seal, doc):
    out = []
    stripped = BLOCK_RE.sub(u"", doc)
    if [l for l in stripped.split(u"\n") if l.lstrip().startswith(u"|")]:
        out.append(u"門の外に表の行がある")
    bad = [l[:40] for l in stripped.split(u"\n") if re.search(r"\d+(?:\.\d+)?\s*(?:%|行|件|社|席|書類|試行|回|本|ポイント|USD|file|倍|桁|字|組|つ)", l) and NOT_GATED not in l]
    if bad:
        out.append(u"散文の数に【門なし】の印が無い: %s" % bad)
    heads = re.findall(r"^## (\d+)\.", doc, re.M)
    if heads != [str(i) for i in range(1, len(heads) + 1)] or len(heads) < 9:
        out.append(u"節の番号が 1 から続いていない・9 節に足りない: %s" % heads)
    if not (doc.index(u"<!-- 門:start pred -->") < doc.index(u"## 2.")):
        out.append(u"予測の当否が先頭(第 2 節より前)にない")
    J = judge(rec, seal)
    missed = [k for k, v in J.items() if v[1] is False]
    want = u"外れた予測: " + (u"・".join(missed) if missed else u"なし") + u"。外れは外れのまま残す(封も予測も直さない)。" + NOT_GATED
    if sum(1 for l in doc.split(u"\n") if l.strip() == want) != 1:
        out.append(u"『外れた予測』の行が記録から求めた当否と違う(期待: %s)" % want)
    undecided = [k for k, v in J.items() if v[1] is None]
    want2 = u"判定しない予測: " + u"・".join(undecided) + u"(当たりにも外れにも数えない)。" + NOT_GATED
    n2 = sum(1 for l in doc.split(u"\n") if l.strip() == want2)
    if undecided and n2 != 1:
        out.append(u"『判定しない予測』の行が記録から求めた当否と違う(期待: %s)" % want2)
    if not undecided and u"判定しない予測:" in doc:
        out.append(u"判定しない予測が無いのに、その行がある")
    for lit in (u"記録は不変", u"診断だけ", u"位置で引いた claim が正しいとは言っていない", u"測っていない", NOT_GATED, u"edinetdb-p27", u"仮説。測るまで断定しない", u"封にない判断", u"次に測ること", u"言えないこと",
                u"LATER_NAMING_FILES", u"fresh_seal"):
        if lit not in doc:
            out.append(u"必要な字が無い: %s" % lit)
    for w in FORBIDDEN:
        if w in doc:
            out.append(u"禁止語: %s" % w)
    if u"```" in doc:
        out.append(u"code fence がある")
    return out


# ----------------------------------------------------------------------------------------------------------------
# (h)
def check_h(seal, doc, rec=None):
    out = []
    fetched = rload(FETCHED_FRESH_REL)
    docs = list(fetched[u"使う書類"])
    cids = set()
    if rec is not None:
        for p in POPS:
            docs += rec[u"書類(出てくる順)"][p]
        for r in rec[u"rows"]:
            if r[u"値で引いた"]:
                cids.add(r[u"値で引いた"][u"id"])
            cids.update(r[u"位置の候補"])
    docs = sorted(set(docs))
    for name, t in ((u"封", seal), (u"文書", doc)):
        for d in docs:
            if d in t:
                out.append(u"%s に docID の字がある: %s" % (name, d))
        if re.findall(r"S100[0-9A-Z]{4}", t):
            out.append(u"%s に docID らしい字がある" % name)
        if re.findall(r"\b[NT]\d{3}\b", t):
            out.append(u"%s に claim の id らしい字がある" % name)
        for cid in cids:
            if re.search(r"(?<![0-9A-Za-z])%s(?![0-9A-Za-z])" % re.escape(cid), t):
                out.append(u"%s に記録の claim の id の字がある: %s" % (name, cid))
                break
        if u"```" in t:
            out.append(u"%s に code fence がある" % name)
        for w in FORBIDDEN:
            if w in t:
                out.append(u"%s に禁止語: %s" % (name, w))
    return out


# ----------------------------------------------------------------------------------------------------------------
# (k) 数え直し(封 §2-6 の 1)・重なり(§2-6 の 2)・台帳の行の語(§2-7)を、記録の行から別の実装で作り直す
_MODS = {}


def mods():
    if not _MODS:
        _MODS["XS"] = mod("measure/xbrl_cd_score_2026-10-17.py", "cd_score_in_gate")
        _MODS["XC"] = mod("measure/xbrl_cd_ceiling_2026-10-17.py", "cd_ceiling_in_gate")
        _MODS["AC"] = mod("measure/xbrl_a_core_vs_grep_2026-10-17.py", "a_core_in_gate")
        _MODS["NF"] = mod("measure/xbrl_naming_fix_2026-10-20.py", "naming_fix_in_gate")
        _MODS["PB"] = mod("measure/xbrl_period_bind_2026-10-20.py", "period_bind_in_gate")
        _MODS["FC"] = mod("measure/facts_check_2026-10-20.py", "facts_check_in_gate")
    return _MODS


def judge_maps(rec, pop, prof):
    u"""({(doc, id): 判定(値)}, {(doc, id): 判定(位置)があればそれ、無ければ判定(値)})。"""
    val, pos = {}, {}
    for r in U(rec, pop, prof):
        k = (r["doc"], r["id"])
        val[k] = r[u"判定(値)"]
        pos[k] = r[u"判定(位置)"] if r[u"判定(位置)"] is not None else r[u"判定(値)"]
    return val, pos


def a1_numbers(S, jm):
    M = mods()
    XS, XC = M["XS"], M["XC"]
    mat = copy.deepcopy(S["mat"])
    pre_by = {}
    for p in mat[u"書類ごと"]:
        for rid, v in p[u"席の前に出せる分"].items():
            j = jm[(p["docID"], rid)]
            v[u"Core"] = {u"言うこと": j[u"Core"][0], u"参照先": j[u"Core"][1], u"state": j[u"Core"][2]}
            v[u"Core(厳しい読み方)"] = {u"言うこと": j[u"Core(厳しい読み方)"][0], u"参照先": j[u"Core(厳しい読み方)"][1], u"state": j[u"Core(厳しい読み方)"][2]}
            pre_by[(p["docID"], rid)] = v
    sc = S["score"]
    rows = []
    for r in sc["rows"]:
        pre = pre_by[(r["doc"], r["id"])]
        row = {"doc": r["doc"], "id": r["id"], u"注入か": pre[u"注入か"], u"正解": pre[u"正解"], u"席": r[u"席"], u"腕": {}}
        for nm, arm in XS.arms_of(r[u"席"], pre).items():
            row[u"腕"][nm] = dict(arm, **{u"判定結果": XS.verdict(arm, pre[u"正解"], pre[u"注入か"])})
        rows.append(row)
    t = XS.tally(rows)
    t5 = XC.t5_rows(mat, dict(((r["doc"], r["id"]), r) for r in sc["rows"]))
    out = {u"採点": t, u"主比較の判定": XS.judge_z(t), u"α の天井": XC.ceiling(t5),
           u"Core 自身の特定率(本番)": XC.rate(sum(1 for r in t5 if r[u"Core の参照先"] == r[u"正解"]), len(t5))}
    # 手で数える(関数を通さない): C′ の正しい参照先の特定の分子・Core 自身の特定の分子
    hand = 0
    for r in sc["rows"]:
        g = pre_by[(r["doc"], r["id"])][u"正解"]
        if not (g and g[u"種類"] == u"参照先が在る") or r[u"席"][u"判定"] == u"欠け":
            continue
        ptr = pre_by[(r["doc"], r["id"])]["Core"][u"参照先"] if r[u"席"][u"判定"] == u"判定できない" else r[u"席"][u"参照先"]
        hand += (ptr == g[u"正解"])
    own = sum(1 for k, v in pre_by.items() if v[u"正解"] and v[u"正解"][u"種類"] == u"参照先が在る" and v["Core"][u"参照先"] == v[u"正解"][u"正解"])
    return out, hand, own


def a2_numbers(S, jm22, jm27):
    PB = mods()["PB"]
    rows = copy.deepcopy(S["pb"]["E4"][u"行"])
    for r in rows:
        j = jm22[(r["doc"], r["id"])]
        r[u"Core 自身 P22"] = {u"state": j[0], u"参照先": j[1]}
    inj = [r for r in S["pb"]["E4"][u"行"] if r[u"注入か"]]
    g = sum(1 for r in inj if jm27[(r["doc"], r["id"])][0] == "GROUNDED")
    hand = sum(1 for r in rows if r[u"注入の型"] == "T6_PRIOR" and r[u"Core 自身 P22"][u"state"] == "GROUNDED")
    return {u"E4 集計": PB.e4_summary(rows), u"S6 段 2": PB.frac(g, len(inj))}, hand


def b_numbers(recrows, jm):
    M = mods()
    rows = copy.deepcopy(recrows)
    for r in rows:
        j = jm[(r["doc"], r["id"])]
        for nm in (u"Core", u"Core-P"):
            r[u"腕"][nm] = {u"言うこと": j[nm][0], u"参照先": j[nm][1], u"判定": j[nm][2]}
    hand = sum(1 for r in rows if r[u"型"] == "T5_COINCIDENT" and r[u"腕"][u"Core-P"][u"判定"].get(u"特定"))
    return {u"AC.tally": M["AC"].tally(rows), u"NF.score": M["NF"].score(rows)}, hand


def recount_again(rec, S):
    u"""[{母集団, profile, 欄, 記録の節, 記録, 値で数え直し, 位置で数え直し, 動いた欄}] と手で数えた数 {key: (数え直しの値, 手で数えた値)}。"""
    out, hands = [], {}
    sc, ce, pb, dp = S["score"], S["ceiling"], S["pb"], S["dp27"]
    val, pos = judge_maps(rec, "A1", "P16")
    rv, hv, ov = a1_numbers(S, val)
    rp, hp, op = a1_numbers(S, pos)
    hands["A1 C′ の特定の分子"] = (rp[u"採点"][u"C′"][u"正しい参照先の特定"][u"分子"], hp)
    hands["A1 Core 自身の特定の分子"] = (rp[u"Core 自身の特定率(本番)"][u"分子"], op)

    def add(pop, prof, label, rel, kp, rec_v, v, p):
        out.append({u"母集団": pop, u"profile": prof, u"欄": label, u"記録の節": rel + u"#" + u" > ".join(kp), u"記録": rec_v, u"値で数え直し": v, u"位置で数え直し": p,
                    u"値で数え直しが記録と一致": rt(v) == rt(rec_v), u"動いた欄": sorted(k for k in set(leaves(rt(rec_v))) | set(leaves(rt(p))) if leaves(rt(rec_v)).get(k, u"(欄なし)") != leaves(rt(p)).get(k, u"(欄なし)"))})
    k1, k2 = "fixtures/xbrl/cd8/score_2026-10-17.json", "fixtures/xbrl/cd8/ceiling_2026-10-17.json"
    add("A1", "P16", u"採点", k1, [u"採点"], sc[u"採点"], rv[u"採点"], rp[u"採点"])
    add("A1", "P16", u"主比較の判定", k1, [u"**主比較の判定**"], sc[u"**主比較の判定**"], rv[u"主比較の判定"], rp[u"主比較の判定"])
    cl = u"**α の天井(席が外した行で Core が正解を持っていたか)**"
    add("A1", "P16", u"α の天井", k2, [cl], ce[cl], rv[u"α の天井"], rp[u"α の天井"])
    add("A1", "P16", u"Core 自身の特定率(本番)", k2, [u"Core 自身の特定率", u"本番(未使用 8 書類)"], ce[u"Core 自身の特定率"][u"本番(未使用 8 書類)"], rv[u"Core 自身の特定率(本番)"], rp[u"Core 自身の特定率(本番)"])
    v22, p22 = judge_maps(rec, "A2", "P22")
    v27, p27 = judge_maps(rec, "A2", "P27")
    av, _h = a2_numbers(S, v22, v27)
    ap, hp2 = a2_numbers(S, p22, p27)
    hands["A2 T6 で GROUNDED の件"] = (ap[u"E4 集計"][u"T6 で Core 自身 P22 が GROUNDED"][u"件"], hp2)
    add("A2", "P22", u"E4 の集計", "fixtures/xbrl/period_bind_2026-10-20.json", ["E4", u"集計"], pb["E4"][u"集計"], av[u"E4 集計"], ap[u"E4 集計"])
    add("A2", "P27", u"全注入で Core 自身(既定)が GROUNDED", "fixtures/xbrl/default_p27_2026-10-28.json", ["S6", u"段 2", u"全注入で Core 自身(既定)が GROUNDED"],
        dp["S6"][u"段 2"][u"全注入で Core 自身(既定)が GROUNDED"], av[u"S6 段 2"], ap[u"S6 段 2"])
    nf = S["nf"]
    ac_sec = {("B1", "P16"): ("fixtures/xbrl/cd8/a_core_vs_grep_2026-10-17.json", [u"採点"], S["acp16"][u"採点"]),
              ("B1", "P20"): ("fixtures/xbrl/cd8/a_core_vs_grep_P20_2026-10-17.json", [u"採点"], S["acp20"][u"採点"]),
              ("B2", "P16"): ("fixtures/xbrl/gen_c/c0_2026-10-20.json", [u"**C0-2 (ア) の main() の出力**", u"採点"], S["c0"][u"**C0-2 (ア) の main() の出力**"][u"採点"]),
              ("B2", "P20"): ("fixtures/xbrl/gen_c/c0_p20_2026-10-20.json", [u"**C0-2 (ア) の main() の出力(P20)**", u"採点"], S["c0p"][u"**C0-2 (ア) の main() の出力(P20)**"][u"採点"])}
    nf_sec = {("B1", "P20"): u"cd8 (ア) P20(記録)の採点", ("B1", "P21"): u"cd8 (ア) P21 の採点", ("B2", "P20"): u"gen_c (ア) P20 の採点", ("B2", "P21"): u"gen_c (ア) P21 の採点"}
    _, brec = source_rows(S)
    for pop in ("B1", "B2"):
        for prof in PROFS[pop]:
            v, p = judge_maps(rec, pop, prof)
            bv, _h = b_numbers(brec[(pop, prof)], v)
            bp, hh = b_numbers(brec[(pop, prof)], p)
            hands["%s %s Core-P の特定の分子" % (pop, prof)] = (bp[u"AC.tally"][u"Core-P"][u"特定率(分母 = T5 の件数)"][u"分子"], hh)
            if (pop, prof) in ac_sec:
                rel, kp, rv_ = ac_sec[(pop, prof)]
                add(pop, prof, u"採点(AC.tally)", rel, kp, rv_, bv[u"AC.tally"], bp[u"AC.tally"])
            else:
                out.append({u"母集団": pop, u"profile": prof, u"欄": u"採点(AC.tally。記録の欄なし)", u"記録の節": None, u"記録": None, u"値で数え直し": bv[u"AC.tally"], u"位置で数え直し": bp[u"AC.tally"],
                            u"値で数え直しが記録と一致": None,
                            u"動いた欄": sorted(k for k in set(leaves(rt(bv[u"AC.tally"]))) | set(leaves(rt(bp[u"AC.tally"]))) if leaves(rt(bv[u"AC.tally"])).get(k, u"(欄なし)") != leaves(rt(bp[u"AC.tally"])).get(k, u"(欄なし)"))})
            if (pop, prof) in nf_sec:
                add(pop, prof, u"採点(NF.score)", "fixtures/xbrl/naming_fix/p21_2026-10-20.json", [nf_sec[(pop, prof)]], nf[nf_sec[(pop, prof)]], bv[u"NF.score"], bp[u"NF.score"])
    return out, hands


def overlaps_again(rec, S):
    u"""§2-6 の 2。表で持つ(母集団, profile, 記録, 節の名, 行の集合を作る式)。"""
    R = lambda rel: rload(rel)
    cd8 = "fixtures/xbrl/cd8/"
    k = lambda rows, key="id": [(r["doc"], r[key]) for r in rows]
    rs, cv, vi, pn, pr, pc = (R(cd8 + "role_swap_2026-10-17.json"), R(cd8 + "contract_v1_2026-10-17.json"), R(cd8 + "verify_inventory_2026-10-17.json"),
                              R(cd8 + "pnf_diag_2026-10-17.json"), R(cd8 + "p20_rerun_2026-10-17.json"), R(cd8 + "p20_pred_recheck_2026-10-17.json"))
    c1, nf = R("fixtures/xbrl/gen_c/c1_2026-10-20.json"), S["nf"]
    spec = [
        ("A1", ["P16"], cd8 + "role_swap_2026-10-17.json", u"rows(主張 id が None でない行)", k([r for r in rs["rows"] if r.get(u"主張 id") is not None])),
        ("A1", ["P16"], cd8 + "role_swap_2026-10-17.json", u"rows(全部)", k(rs["rows"])),
        ("A1", ["P16"], cd8 + "contract_v1_2026-10-17.json", u"rows", k(cv["rows"])),
        ("A1", ["P16"], cd8 + "verify_inventory_2026-10-17.json", u"第 2 部 rows", k(vi[u"**第 2 部 実物での発火**"]["rows"])),
        ("A1", ["P16"], cd8 + "pnf_diag_2026-10-17.json", u"rows", k(pn["rows"])),
        ("A1", ["P16"], cd8 + "p20_rerun_2026-10-17.json", u"rows", k(pr["rows"])),
        ("A1", ["P16"], cd8 + "p20_pred_recheck_2026-10-17.json", u"rows(行)", k(pc["rows"], u"行")),
        ("A2", ["P22", "P27"], "fixtures/xbrl/period_bind_2026-10-20.json", u"E4 > 行(P21 の欄)", k(S["pb"]["E4"][u"行"])),
        ("B1", ["P16"], cd8 + "ceiling_2026-10-17.json", u"Core 自身の特定率 > (ア)(T5 で対応が付いた行)", k([r for r in S["acp16"]["rows"] if r[u"型"] == "T5_COINCIDENT" and r[u"対応が付いた"]])),
        ("B2", ["P16"], "fixtures/xbrl/gen_c/c1_2026-10-20.json", u"**K-4・K-5 の数** > rows", k(c1[u"**K-4・K-5 の数**"]["rows"], u"注入の id")),
        ("B2", ["P20", "P21"], "fixtures/xbrl/naming_fix/p21_2026-10-20.json", u"**K-4 の再計算** > rows", k(nf[u"**K-4 の再計算**"]["rows"], u"注入の id")),
        ("B2", ["P16"], "fixtures/xbrl/gen_c/c0_2026-10-20.json", u"**C0-3 ...** > rows", k(S["c0"][u"**C0-3 engine を Core-P の参照先に当てた**"]["rows"])),
        ("B2", ["P20"], "fixtures/xbrl/gen_c/c0_p20_2026-10-20.json", u"**C0-3 ...(P20)** > rows", k(S["c0p"][u"**C0-3 engine を Core-P(P20)の参照先に当てた**"]["rows"])),
        ("B2", ["P21"], "fixtures/xbrl/naming_fix/p21_2026-10-20.json", u"**C0-3 ...(P21)** > rows", k(nf[u"**C0-3 engine を Core-P(P21)の参照先に当てた**"]["rows"])),
    ]
    idx = dict(((r[u"母集団"], r["profile"], r["doc"], r["id"]), r) for r in rec[u"rows"])
    out = []
    for pop, profs, rel, name, keys in spec:
        for prof in profs:
            hit = [idx[(pop, prof, d, i)] for d, i in keys if (pop, prof, d, i) in idx]
            out.append({u"母集団": pop, u"profile": prof, u"記録": rel, u"節": name, u"行の集合": len(keys), u"この便の行に在る": len(hit),
                        u"(違う)": sum(1 for r in hit if r[u"分類"] == W_DIFF), u"(値だけ)": sum(1 for r in hit if r[u"分類"] == W_VONLY), u"(位置だけ)": sum(1 for r in hit if r[u"分類"] == W_PONLY),
                        u"分類が(違う)(値だけ)(位置だけ)の行": sum(1 for r in hit if r[u"分類"] in (W_DIFF, W_VONLY, W_PONLY)),
                        u"(位置が決まらない)+(位置で 1 件に決まらない)": sum(1 for r in hit if r[u"分類"] in (W_UNFIX, W_MANY)),
                        u"判定が変わる行": sum(1 for r in hit if r[u"判定が変わる"])})
    return out


def ledger_again(items, ovl):
    FCm = mods()["FC"]
    harness = jtext(os.path.join(ROOT, HARNESS_REL))
    blk = dict(BLOCK_RE.findall(harness))["ledger"]
    tg = []
    for line in blk.split(u"\n"):
        cells = [c.strip() for c in line.strip().strip(u"|").split(u"|")]
        if line.startswith(u"|") and len(cells) >= 4 and re.match(r"^[A-Z]+-\d+$", cells[0]) and re.search(r"M-(03|05|13|16|18|20|21|23)\b", cells[1]):
            tg.append((cells[0], cells[1], cells[3]))
    ids = [t[0] for t in tg]
    marks = [(rid, kind, body) for (_l, rid, kind, body, _b) in FCm.claims(jtext(os.path.join(ROOT, FACTS_REL))) if rid in ids]

    def run(shadow):
        FCm._CACHE.clear()
        for rel, v in shadow.items():
            FCm._CACHE[rel] = v
        res = []
        for _rid, kind, body in marks:
            try:
                FCm.evaluate(kind, body)
                res.append(True)
            except Exception:
                res.append(False)
        FCm._CACHE.clear()
        return res
    shadow = {}
    for it in items:
        if it[u"記録の節"] is None:
            continue
        rel, kp = it[u"記録の節"].split(u"#", 1)
        keys = kp.split(u" > ")
        if rel not in shadow:
            shadow[rel] = copy.deepcopy(rload(rel))
        node = shadow[rel]
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = it[u"位置で数え直し"]
    real, shad = run({}), run(shadow)
    rel1 = set(it[u"記録の節"].split(u"#", 1)[0] for it in items if it[u"記録の節"])
    rel2 = set(o[u"記録"] for o in ovl)
    chg2 = set(o[u"記録"] for o in ovl if o[u"判定が変わる行"] >= 1)
    out = []
    for rid, mech, read in tg:
        ks = [k for k, m in enumerate(marks) if m[0] == rid]
        mv = [k for k in ks if real[k] and not shad[k]]
        files = sorted(set(f for k in ks for f in re.findall(r"(\S+?\.json)#", marks[k][2])))
        if mv:
            w = u"数が動く"
        elif set(files) & chg2:
            w = u"動きうる(数え直していない)"
        elif set(files) & (rel1 | rel2):
            w = u"動かない"
        else:
            w = u"この便の外"
        out.append({u"台帳の行": rid, u"引いた仕掛け": mech, u"読み": read, u"印": len(ks), u"本物で通らなかった印": sum(1 for k in ks if not real[k]), u"動く印": len(mv), u"引く記録": files, u"語": w})
    return out


def check_k(rec, S=None):
    out = []
    S = S or sources()
    S = dict(S)
    for k, rel in (("score", "fixtures/xbrl/cd8/score_2026-10-17.json"), ("ceiling", "fixtures/xbrl/cd8/ceiling_2026-10-17.json"), ("dp27", "fixtures/xbrl/default_p27_2026-10-28.json")):
        S[k] = rload(rel)
    try:
        items, hands = recount_again(rec, S)
    except Exception as e:
        return [u"数え直しを作れない: %r" % (e,)]
    got = rec[u"数え直し(§2-6 の 1)"]
    if len(got) != len(items):
        out.append(u"数え直しの欄の数が違う: %d / %d" % (len(got), len(items)))
        return out
    for a, b in zip(got, items):
        for key in (u"母集団", u"profile", u"欄", u"記録の節"):
            if a[key] != b[key]:
                out.append(u"数え直しの %s が違う: %s / %s" % (key, a[key], b[key]))
        for key in (u"記録", u"値で数え直し", u"位置で数え直し", u"値で数え直しが記録と一致", u"動いた欄"):
            if rt(a[key]) != rt(b[key]):
                out.append(u"数え直し『%s %s %s』の %s が別の実装で求めた値と違う" % (a[u"母集団"], a[u"profile"], a[u"欄"], key))
        if a[u"値で数え直しが記録と一致"] is False:
            out.append(u"値で引いた判定のまま数え直した値が記録と違う: %s" % a[u"欄"])
    for k, (x, y) in hands.items():
        if x != y:
            out.append(u"手で数えた数と数え直しの値が違う: %s %s / %s" % (k, x, y))
    ov = overlaps_again(rec, S)
    if rt(ov) != rt(rec[u"行の重なり(§2-6 の 2)"]):
        out.append(u"行の重なりが別の実装で求めた値と違う")
    try:
        led = ledger_again(items, ov)
    except Exception as e:
        return out + [u"台帳の行の語を求め直せない: %r" % (e,)]
    if rt(led) != rt(rec[u"台帳の行(§2-7)"]):
        out.append(u"台帳の行の語が facts_check で求め直した値と違う")
    if len(led) != 28:
        out.append(u"台帳の対象の行が 28 行でない")
    return out


# ----------------------------------------------------------------------------------------------------------------
# (i) 封の commit が script・記録・文書・門の commit より前
def make_run(repo_dir):
    def run(*args):
        r = subprocess.run(["git", "-C", repo_dir] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r.returncode, r.stdout.decode("utf-8", "replace").strip()
    return run


def added_commits(run, path):
    rc, out = run("log", "--diff-filter=A", "--format=%H", "--", path)
    return [l for l in out.splitlines() if l.strip()] if rc == 0 else []


def is_anc(run, a, b):
    return a is not None and b is not None and run("merge-base", "--is-ancestor", a, b)[0] == 0


def order_problems(run, prefix, head="HEAD"):
    u"""(i) 封の commit が script・記録・文書・門の commit より前。問題の列 [(符号, 文)]。追跡されていない file は『足した commit が無い』で赤(skip にしない)。"""
    problems = []
    seal = prefix + SEAL_REL
    s_list = added_commits(run, seal)
    if len(s_list) != 1 or not HEX40.match(s_list[0]):
        problems.append(("SEAL_ONCE", u"封を足した commit がちょうど 1 つに決まらない(%d 行)" % len(s_list)))
        return problems
    S = s_list[0]
    if not is_anc(run, S, head):
        problems.append(("SEAL<=HEAD", u"封の commit が HEAD の祖先でない"))
    for name, rel in (("SCRIPT", SCRIPT_REL), ("RECORD", REC_REL), ("DOC", DOC_REL), ("GATE", GATE_REL)):
        lst = added_commits(run, prefix + rel)
        if len(lst) == 0:
            problems.append((name + "_UNCOMMITTED", u"%s がまだ commit されていない(足した commit が無い)" % rel))
        elif len(lst) != 1 or not HEX40.match(lst[0]):
            problems.append((name + "_ONCE", u"%s を足した commit がちょうど 1 つに決まらない(%d 行)" % (rel, len(lst))))
        elif not (lst[0] != S and is_anc(run, S, lst[0])):
            problems.append((name + "_BEFORE_SEAL", u"%s の commit が封の commit より前か同じ" % rel))
    # 封を後から直していない(削除の行が 0 = 日付つきの追記だけ)
    rc, txt = run("log", "--format=%H", "%s..%s" % (S, head), "--", seal)
    for h in [l for l in txt.splitlines() if l.strip()]:
        rc2, parent = run("rev-parse", h + "^")
        base = parent if rc2 == 0 else EMPTY_TREE
        rc3, num = run("diff", "--numstat", base, h, "--", seal)
        for line in num.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[1] != "0":
                problems.append(("SEAL_REWRITE", u"封の commit より後の commit %s が封の行を消している" % h[:7]))
    return problems


def codes(problems):
    return sorted(set(c for c, _m in problems))


class Tmp(object):
    def __init__(self, base):
        self.dir = tempfile.mkdtemp(prefix="rowclaim_", dir=base)
        self.run = make_run(self.dir)
        self._g("init", "-q")

    def _g(self, *args):
        r = subprocess.run(["git", "-C", self.dir, "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"] + list(args),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert r.returncode == 0, (args, r.stderr[:300])
        return r.stdout.decode("utf-8").strip()

    def write(self, rel, text):
        p = os.path.join(self.dir, rel)
        if os.path.dirname(p) and not os.path.isdir(os.path.dirname(p)):
            os.makedirs(os.path.dirname(p))
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)

    def commit(self, msg, *paths):
        self._g("add", "--", *paths)
        self._g("commit", "-q", "-m", msg)
        return self._g("rev-parse", "HEAD")


FILES = {"SEAL": SEAL_REL, "SCRIPT": SCRIPT_REL, "RECORD": REC_REL, "DOC": DOC_REL, "GATE": GATE_REL}


def build(base, steps):
    u"""steps は 'SEAL' 'SCRIPT' 'RECORD' 'DOC' 'GATE'(その file を 1 つの commit で足す)と変異の手 'SEAL_REWRITE' 'SEAL_APPEND' 'SEAL_TWICE' 'ALL4'(4 つを 1 commit)。"""
    t = Tmp(base)
    for s in steps:
        if s in FILES:
            t.write(FILES[s], u"# %s\n\n行 1\n行 2\n行 3\n" % s)
            t.commit(s, FILES[s])
        elif s == "ALL4":
            for k in ("SCRIPT", "RECORD", "DOC", "GATE"):
                t.write(FILES[k], u"# %s\n" % k)
            t.commit("ALL4", *[FILES[k] for k in ("SCRIPT", "RECORD", "DOC", "GATE")])
        elif s == "SEAL_REWRITE":
            t.write(FILES["SEAL"], u"# SEAL\n\n行 1\n行 3\n")
            t.commit("封を書き換える", FILES["SEAL"])
        elif s == "SEAL_APPEND":
            with open(os.path.join(t.dir, FILES["SEAL"]), "a", encoding="utf-8") as f:
                f.write(u"\n## 追記\n行 4\n")
            t.commit("封に追記", FILES["SEAL"])
        elif s == "SEAL_TWICE":
            t._g("rm", "-q", "--", FILES["SEAL"])
            t._g("commit", "-q", "-m", "封を消す")
            t.write(FILES["SEAL"], u"# SEAL\n")
            t.commit("封を足し直す", FILES["SEAL"])
        else:
            raise AssertionError(s)
    return t


# ----------------------------------------------------------------------------------------------------------------
class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.S = sources()

    def test_a_1_the_row_sets_and_types_equal_the_existing_records(self):
        self.assertEqual(check_a(self.rec, self.S), [])

    def test_a_2_the_row_sets_are_read_from_the_records_not_hardcoded(self):
        want, brec = source_rows(self.S)
        self.assertEqual(len(want[("A1", "P16")]), 192)
        self.assertEqual(len(want[("A2", "P22")]), 192)
        self.assertEqual(sum(len(v) for k, v in want.items() if k[0] in ("B1", "B2")), 142 * 3 + 128 * 3)
        self.assertEqual(len(self.rec[u"rows"]), 192 + 192 * 2 + 142 * 3 + 128 * 3)

    def test_b_1_the_wiring_gates_all_passed(self):
        self.assertEqual(check_b(self.rec, self.S), [])

    def test_b_2_every_row_has_the_known_fields(self):
        base = [u"母集団", u"profile", u"doc", u"id", u"型", u"注入か", u"本文", u"範囲", u"写した範囲", u"値で引いた", u"文の番号", u"文の中の範囲", u"位置の候補", u"数の終わりが決まらない",
                u"位置で引いた", u"分類", u"細目", u"判定(値)", u"判定(位置)", u"判定が変わる"]
        for r in self.rec[u"rows"]:
            self.assertTrue(set(base) <= set(r), r[u"id"])
            self.assertIn(r[u"本文"], (T_SAME, T_WS, T_OTHER))
            if r[u"母集団"] == "A1":
                self.assertIn(u"共有された", r)
            if r[u"母集団"] in ("B1", "B2"):
                self.assertIn(u"diff_sentence の番号", r)

    def test_e_1_the_classes_and_judgement_changes_are_recomputed_from_the_fields(self):
        self.assertEqual(check_e(self.rec), [])

    def test_e_2_the_seven_words_cover_every_row_once(self):
        self.assertEqual(sum(C(self.rec[u"rows"]).values()), len(self.rec[u"rows"]))
        self.assertTrue(set(C(self.rec[u"rows"])) <= set(WORDS7))

    def test_e_3_w_t_units_equal_the_rows(self):
        c = collections.Counter()
        for u in self.rec[u"W-T の単位ごと"]:
            for w, n in u[u"本文の語ごとの verify の数"].items():
                c[(u[u"母集団"], u[u"profile"], w)] += n
        d = collections.Counter((r[u"母集団"], r[u"profile"], r[u"本文"]) for r in self.rec[u"rows"] if r[u"母集団"] in ("B1", "B2"))
        for k, n in d.items():
            self.assertEqual(c[k], n, k)
        for p in ("A1", "A2"):                  # A は 1 書類 1 verify。行の数ではなく verify の数
            for f in PROFS[p]:
                self.assertEqual(sum(v for k, v in c.items() if k[0] == p and k[1] == f), len(self.rec[u"書類(出てくる順)"][p]))

    def test_j_1_the_inputs_read_are_unchanged(self):
        self.assertEqual(check_j(self.rec), [])

    def test_k_1_recounts_overlaps_and_the_ledger_words_are_recomputed(self):
        self.assertEqual(check_k(self.rec, self.S), [])

    def test_d_1_judgments_are_recomputed_and_cover_the_twenty_five_predictions(self):
        J = judge(self.rec, jtext(SEAL))
        self.assertEqual(list(J), ["CR-%d" % i for i in range(1, 26)])

    def test_d_2_the_judge_is_not_a_constant(self):
        seal = jtext(SEAL)
        base = judge(self.rec, seal)
        rec = copy.deepcopy(self.rec)
        for r in U(rec, "A1", "P16"):
            if r[u"分類"] == W_SAME:
                r[u"分類"] = W_DIFF
        self.assertNotEqual(judge(rec, seal)[("CR-5")], base["CR-5"])


class EngineTest(unittest.TestCase):
    def test_f_1_engine_sha16_are_pinned_or_declared(self):
        rec = jload(REC)
        self.assertEqual(rec[u"engine sha16"], ENGINE_AT_MEASURE)
        self.assertEqual(rec[u"DEFAULT_PROFILE"], "P27")
        for rel, want in ENGINE_AT_MEASURE.items():
            got = sha16(rel)
            if got != want and rel in ENGINE_DECLARED:
                later, seal_rel = ENGINE_DECLARED[rel]
                added = git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split()
                self.assertTrue(added, u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % rel)
                continue
            self.assertEqual(got, want, u"**%s が動いている**" % rel)

    def test_f_2_the_declared_transition_form_is_red_for_an_unknown_value(self):
        u"""宣言の無い file の sha が違えば赤、宣言があっても値が違えば赤(型の確認。実 file は触らない)。"""
        def accepts(got, rel, want, declared):
            if got != want and rel in declared:
                return got == declared[rel][0]
            return got == want
        rel = "adapters/xbrl/vocabulary.py"
        want = ENGINE_AT_MEASURE[rel]
        self.assertTrue(accepts(want, rel, want, {}))
        self.assertFalse(accepts("0" * 16, rel, want, {}))
        self.assertTrue(accepts("1" * 16, rel, want, {rel: ("1" * 16, "x")}))
        self.assertFalse(accepts("2" * 16, rel, want, {rel: ("1" * 16, "x")}))

    def test_f_3_core_and_adapters_have_no_uncommitted_change(self):
        r = git("status", "--porcelain", "--", "adapters", "core")
        self.assertEqual(r.stdout.strip(), u"", u"engine の file に未 commit の変更がある")


class SealAndDocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def test_c_1_the_tables_equal_the_ones_rebuilt_from_the_record(self):
        self.assertEqual(check_c(self.rec, self.seal, self.doc), [])

    def test_c_2_the_prose_outside_the_tables_is_in_order(self):
        self.assertEqual(check_doc_prose(self.rec, self.seal, self.doc), [])

    def test_d_3_the_prediction_table_copies_the_seal_and_the_judgments(self):
        SP = seal_predictions(self.seal)
        J = judge(self.rec, self.seal)
        got = doc_blocks(self.doc)["pred"]
        self.assertEqual(len(got), 2 + len(J))
        for line, k in zip(got[2:], J):
            cells = [c.strip() for c in line.strip().strip(u"|").split(u" | ")]
            self.assertEqual(cells[0], u"**%s**" % k)
            self.assertEqual(tuple(cells[1:4]), SP[k], k)                  # 封の字(欄・予測・外れ方)のまま
            self.assertEqual(cells[4], J[k][0], k)                          # 実測は記録から
            self.assertEqual(cells[5], hit_word(J[k][1]), k)                # 当否は記録から

    def test_d_4_the_seal_prediction_table_is_what_this_gate_reads(self):
        u"""封の表の形(幅の数は字で留めない。『幅が何本あるか』の形だけを見る)。"""
        SP = seal_predictions(self.seal)
        self.assertEqual(list(SP), ["CR-%d" % i for i in range(1, 26)])
        self.assertEqual([len(ranges_of(SP["CR-%d" % i][1])) for i in range(1, 26)], [0, 0, 0, 1, 1, 1, 1, 1, 2, 3, 0, 0, 0, 2, 1, 3, 2, 1, 2, 0, 2, 2, 0, 0, 1])
        self.assertEqual(len(lows_of(SP["CR-11"][1])), 1)
        self.assertEqual(len(lows_of(SP["CR-12"][1])), 1)
        self.assertEqual(len(lows_of(SP["CR-20"][1])), 1)
        self.assertEqual(len(ups_of(SP["CR-24"][1])), 1)

    def test_d_5_the_misses_are_kept_as_misses(self):
        J = judge(self.rec, self.seal)
        self.assertEqual([k for k, v in J.items() if v[1] is False], MISSES)
        self.assertEqual([k for k, v in J.items() if v[1] is None], UNDECIDED)

    def test_h_1_no_docid_and_no_claim_id_in_the_seal_and_the_document(self):
        self.assertEqual(check_h(self.seal, self.doc, self.rec), [])

    def test_h_2_the_record_names_the_documents_and_that_is_why_it_is_gated(self):
        u"""記録は docID を持つ(行の同定のため)。24 書類は引きの門の窓の外なので LATER_NAMING_FILES への宣言は要らない ― 引きの門 fresh_seal を走らせて確かめる(別の試験)。"""
        docs = self.rec[u"書類(出てくる順)"]
        self.assertEqual(sorted(docs), list(POPS))
        text = jtext(REC)
        for p in POPS:
            for d in docs[p]:
                self.assertIn(d, text)


class ScriptTest(unittest.TestCase):
    def test_script_does_not_remeasure_when_the_output_exists(self):
        before = hashlib.sha256(open(REC, "rb").read()).hexdigest()
        env = dict((k, v) for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "EDINET_API_KEY", "EDINETDB_API_KEY"))
        r = subprocess.run(["python3", SCRIPT, "--out", REC], cwd=ROOT, capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        self.assertIn(u"測り直さない", r.stdout)
        self.assertEqual(hashlib.sha256(open(REC, "rb").read()).hexdigest(), before)

    def test_the_overlap_line_of_claim_at_is_one_line(self):
        u"""総点検の門の宣言の根拠の字(重なりを見る 1 行)が script の claim_at の中に 1 度だけ在る。"""
        import ast
        src = jtext(SCRIPT)
        fn = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "claim_at"][0]
        body = ast.get_source_segment(src, fn)
        self.assertEqual(body.count(u"if pos < b2 and a2 < e:"), 1)


class ScriptUnitTest(unittest.TestCase):
    u"""script の位置の規則(本文の位置 -> 文 -> 数の範囲と重なる claim)を、作り物の入力で振る舞いとして確かめる(実 engine の数の切り出しを使う)。"""

    @classmethod
    def setUpClass(cls):
        cls.M = mod(SCRIPT_REL, "rowclaim_script_in_gate")

    def test_u_1_claim_at_takes_only_num_claims_that_overlap_by_one_character(self):
        M = self.M
        sent = u"売上高は100億円である。"
        end = [t[1] for t in M.R._numbers_of(M.V.PROFILES["P22"], sent) if t[0] == 4][0]
        self.assertEqual(end, 9)
        snap = {"num": {"N1": {"sentence": 0, "pos": 4}, "N2": {"sentence": 1, "pos": 4}}, "sentences": [sent, sent]}
        claims = [{"id": "N1"}, {"id": "N2"}, {"id": "T1"}]            # N2 は別の文、T1 は num の claim でない
        ids = lambda a, b: [c["id"] for c in M.claim_at(claims, snap, "P22", 0, (a, b))[0]]
        self.assertEqual(ids(4, 5), ["N1"])
        self.assertEqual(ids(end - 1, end + 3), ["N1"])
        self.assertEqual(ids(0, 4), [])                                 # 触れるだけ(重ならない)
        self.assertEqual(ids(end, end + 2), [])
        self.assertEqual(ids(0, 20), ["N1"])                           # 別の文・num でない claim は入らない

    def test_u_2_claim_at_counts_numbers_whose_end_is_unknown(self):
        M = self.M
        sent = u"売上高は100億円である。"
        snap = {"num": {"N1": {"sentence": 0, "pos": 6}}, "sentences": [sent]}       # pos 6 から始まる数は engine に無い
        c, unknown = M.claim_at([{"id": "N1"}], snap, "P22", 0, (6, 7))
        self.assertEqual((len(c), unknown), (1, 1))                     # e = pos + 1 として重なる

    def test_u_3_loc_maps_a_whitespace_only_difference_and_nfkc(self):
        M = self.M
        given = u"㈱甲は\n\n売上が100億円。"
        eng = u"㈱甲は\n売上が100億円。"
        sents = M.E.split_sentences(eng, True)
        L = M.Loc(given, {"text_": eng, "sentences": sents, "num": {}}, "P22")
        self.assertEqual(L.word, M.T_WS)
        a = given.index(u"100")
        a0, b0, why = L.map_range(a, a + 3)
        self.assertEqual((eng[a0:b0], why), (u"100", None))
        si, ab, why = L.locate(a0, b0)
        self.assertEqual((si, why), (1, None))
        self.assertEqual(sents[si][ab[0]:ab[1]], u"100")                # NFKC で字数が変わる文でも文の中の位置が合う
        a1 = given.index(u"\n\n")
        self.assertEqual(L.map_range(a1, a1 + 2)[2], M.U_WSONLY)        # 範囲が空白だけ
        L2 = M.Loc(u"㈱乙は\n\n売上が100億円。", {"text_": eng, "sentences": sents, "num": {}}, "P22")
        self.assertEqual(L2.word, M.T_OTHER)                            # 空白以外が違う
        self.assertEqual(L2.map_range(0, 3)[2], M.U_OTHER)
        L3 = M.Loc(eng, {"text_": eng, "sentences": sents, "num": {}}, "P22")
        self.assertEqual(L3.word, M.T_SAME)
        one = u"㈱甲の売上は100億円。"                                       # 数の前の字が NFKC で字数を変える文(同じ文の中で位置を写す)
        s1 = M.E.split_sentences(one, True)
        L4 = M.Loc(one, {"text_": one, "sentences": s1, "num": {}}, "P22")
        b = one.index(u"100")
        si1, ab1, why1 = L4.locate(*L4.map_range(b, b + 3)[:2])
        self.assertEqual((si1, why1, s1[si1][ab1[0]:ab1[1]]), (0, None, u"100"))
        self.assertNotEqual(ab1[0], b)                                    # 本文の位置のままでは合わない

    def test_u_4_loc_stops_when_the_rebuilt_sentences_differ_from_the_engines(self):
        M = self.M
        with self.assertRaises(SystemExit):
            M.Loc(u"あ。い。", {"text_": u"あ。い。", "sentences": [u"あ。い。"], "num": {}}, "P22")

    def test_u_5_a_range_across_two_sentences_does_not_fit(self):
        M = self.M
        eng = u"あ。い。"
        L = M.Loc(eng, {"text_": eng, "sentences": M.E.split_sentences(eng, True), "num": {}}, "P22")
        self.assertEqual(L.locate(0, 3)[2], M.U_NOSENT)
        self.assertEqual(L.locate(0, 2)[0], 0)

    def test_u_6_classify_takes_the_first_matching_word(self):
        M = self.M
        c = M.classify
        self.assertEqual(c(True, 5, "N1", True), M.C_UNFIX)
        self.assertEqual(c(False, 2, "N1", True), M.C_MANY)
        self.assertEqual(c(False, 0, None, False), M.C_NONE)
        self.assertEqual(c(False, 0, "N1", False), M.C_VONLY)
        self.assertEqual(c(False, 1, None, False), M.C_PONLY)
        self.assertEqual(c(False, 1, "N1", True), M.C_SAME)
        self.assertEqual(c(False, 1, "N1", False), M.C_DIFF)

    def test_u_7_value_kind_separates_the_three_forms(self):
        M = self.M
        self.assertEqual(M.value_kind(1e8, 100.0), M.P_POW10)
        self.assertEqual(M.value_kind(-11.1, 11.1), M.P_SIGN)
        self.assertEqual(M.value_kind(5.0, 5.0), M.P_SAME)
        self.assertEqual(M.value_kind(7.0, 3.0), M.P_ELSE)
        self.assertEqual(M.value_kind(None, 3.0), M.P_ELSE)

    def test_u_8_leaves_and_moved_see_a_changed_scalar_and_a_missing_field(self):
        M = self.M
        self.assertEqual(M.moved({"a": {"b": 1, "c": [1]}}, {"a": {"b": 2, "c": [1]}}), ["a > b"])
        self.assertEqual(M.moved({"a": 1}, {"a": 1, "b": 2}), ["b"])
        self.assertEqual(M.moved({"a": 1}, {"a": 1}), [])


class FalseRecordsAreRedTest(unittest.TestCase):
    u"""(g) 偽物で赤: 記録の写しを 1 か所変えると (b)(c)(e)(k) のどれかが赤になる(変異)。"""

    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.S = sources()
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def test_g_0_baseline_is_green(self):
        self.assertEqual(check_b(self.rec, self.S), [])
        self.assertEqual(check_c(self.rec, self.seal, self.doc), [])
        self.assertEqual(check_e(self.rec), [])
        self.assertEqual(check_k(self.rec, self.S), [])

    def test_g_1_changing_one_class_turns_e_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in U(rec, "A1", "P16") if x[u"分類"] == W_DIFF][0]
        r[u"分類"] = W_SAME
        self.assertNotEqual(check_e(rec), [])
        self.assertNotEqual(check_c(rec, self.seal, self.doc), [])

    def test_g_2_changing_the_position_claim_id_turns_e_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in U(rec, "A1", "P16") if x[u"分類"] == W_SAME][0]
        r[u"位置で引いた"][u"id"] = r[u"位置で引いた"][u"id"] + u"x"
        self.assertNotEqual(check_e(rec), [])

    def test_g_3_changing_the_wiring_flag_turns_b_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        k = list(rec[u"配線の門"])[0]
        rec[u"配線の門"][k][u"通った"] = False
        self.assertNotEqual(check_b(rec, self.S), [])
        self.assertNotEqual(check_c(rec, self.seal, self.doc), [])

    def test_g_4_changing_the_wiring_count_turns_b_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        k = u"W-A1-2 値で引いた id = p20_rerun の主張 id(P16)"
        rec[u"配線の門"][k][u"一致"] -= 1
        self.assertNotEqual(check_b(rec, self.S), [])
        self.assertNotEqual(check_c(rec, self.seal, self.doc), [])

    def test_g_5_changing_the_judgement_turns_e_red(self):
        rec = copy.deepcopy(self.rec)
        r = [x for x in U(rec, "A1", "P16") if x[u"判定が変わる"]][0]
        r[u"判定が変わる"] = False
        self.assertNotEqual(check_e(rec), [])
        rec = copy.deepcopy(self.rec)
        r = [x for x in U(rec, "A2", "P22") if x[u"判定が変わる"]][0]
        r[u"判定(位置)"] = r[u"判定(値)"]
        self.assertNotEqual(check_e(rec), [])

    def test_g_6_one_character_of_the_document_table_turns_c_red(self):
        for name in ("gates", "classes", "recount", "ledger"):
            blk = BLOCK_RE.search(self.doc[self.doc.index(u"<!-- 門:start %s -->" % name):])
            body = blk.group(2)
            i = body.index(u"| ", body.index(u"\n", body.index(u"\n") + 1)) + 2
            bad = body[:i] + (u"Z" if body[i] != u"Z" else u"Y") + body[i + 1:]
            doc = self.doc.replace(body, bad, 1)
            self.assertNotEqual(check_c(self.rec, self.seal, doc), [], name)

    def test_g_7_changing_a_prediction_character_of_the_seal_turns_d_and_c_red(self):
        i = self.seal.index(u"**CR-5**")
        j = self.seal.index(u"**95 以上 120 以下**", i)
        seal = self.seal[:j] + u"**95 以上 130 以下**" + self.seal[j + len(u"**95 以上 120 以下**"):]
        self.assertNotEqual(check_c(self.rec, seal, self.doc), [])
        # 当否そのものが変わる 1 字
        seal2 = self.seal[:j] + u"**95 以上 105 以下**" + self.seal[j + len(u"**95 以上 120 以下**"):]
        self.assertNotEqual(judge(self.rec, seal2)["CR-5"][1], judge(self.rec, self.seal)["CR-5"][1])

    def test_g_8_a_docid_or_a_claim_id_in_the_document_turns_h_red(self):
        d = self.rec[u"書類(出てくる順)"]["A1"][0]
        self.assertNotEqual(check_h(self.seal, self.doc + u"\n" + d, self.rec), [])
        cid = [r[u"値で引いた"][u"id"] for r in self.rec[u"rows"] if r[u"値で引いた"]][0]
        self.assertNotEqual(check_h(self.seal, self.doc + u"\n " + cid + u" ", self.rec), [])

    def test_g_9_an_unmarked_number_in_prose_turns_the_prose_check_red(self):
        doc = self.doc.replace(u"## 7.", u"この節は 99 行の話である。\n\n## 7.", 1)
        self.assertNotEqual(check_doc_prose(self.rec, self.seal, doc), [])

    def test_g_10_changing_the_hit_word_in_the_prose_turns_the_prose_check_red(self):
        lines = self.doc.split(u"\n")
        i = [k for k, l in enumerate(lines) if l.startswith(u"外れた予測: ")][0]
        lines[i] = lines[i].replace(u"外れた予測: ", u"外れた予測: CR-99・", 1)
        self.assertNotEqual(check_doc_prose(self.rec, self.seal, u"\n".join(lines)), [])

    def test_g_11_changing_one_recount_value_turns_k_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        it = [x for x in rec[u"数え直し(§2-6 の 1)"] if x[u"欄"] == u"Core 自身の特定率(本番)"][0]
        it[u"位置で数え直し"][u"分子"] += 1
        self.assertNotEqual(check_k(rec, self.S), [])
        self.assertNotEqual(check_c(rec, self.seal, self.doc), [])

    def test_g_12_changing_the_ledger_word_or_the_overlap_turns_k_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"台帳の行(§2-7)"][0][u"語"] = u"動かない" if rec[u"台帳の行(§2-7)"][0][u"語"] != u"動かない" else u"数が動く"
        self.assertNotEqual(check_k(rec, self.S), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行の重なり(§2-6 の 2)"][0][u"判定が変わる行"] += 1
        self.assertNotEqual(check_k(rec, self.S), [])

    def test_g_13_a_row_set_or_a_type_changed_turns_a_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"rows"].pop(0)
        self.assertNotEqual(check_a(rec, self.S), [])
        rec = copy.deepcopy(self.rec)
        U(rec, "B1", "P16")[0][u"型"] = u"T9"
        self.assertNotEqual(check_a(rec, self.S), [])

    def test_g_14_changing_a_read_record_sha_turns_j_red(self):
        rec = copy.deepcopy(self.rec)
        k = list(rec[u"読んだ記録の sha256"])[0]
        rec[u"読んだ記録の sha256"][k] = u"0" * 64
        self.assertNotEqual(check_j(rec), [])

    def test_g_15_the_live_docs_are_checked_by_the_part_read_not_the_whole_file(self):
        u"""対象の行・門のブロックの 1 字で赤、対象でない行の 1 字・総点検の文書の末尾の 1 行・情報の file 全体の sha256 では赤にならない。"""
        harness = jtext(os.path.join(ROOT, HARNESS_REL))
        facts = jtext(os.path.join(ROOT, FACTS_REL))
        rec = self.rec
        self.assertEqual(check_j(rec, harness, facts), [])
        ids, _rows = ledger_rows_cut(harness, facts)
        lines = facts.split(u"\n")
        k_in = [i for i, ln in enumerate(lines) if ln.startswith(u"| %s |" % ids[0])][0]
        out_ids = set(ids)
        k_out = [i for i, ln in enumerate(lines) if ln.startswith(u"| ") and ln.split(u"|")[1].strip() not in out_ids and re.match(r"^[A-Z]+-\d+$", ln.split(u"|")[1].strip())][0]
        lines2 = list(lines)
        lines2[k_in] = lines[k_in].replace(u"|", u"|", 1) + u"x"
        self.assertNotEqual(check_j(rec, harness, u"\n".join(lines2)), [])
        lines3 = list(lines)
        lines3[k_out] = lines[k_out] + u"x"
        self.assertEqual(check_j(rec, harness, u"\n".join(lines3)), [])
        self.assertEqual(check_j(rec, harness + u"末尾に足した 1 行\n", facts), [])
        st = harness.index(u"<!-- 門:start ledger -->")
        i = harness.index(u"|", st)
        self.assertNotEqual(check_j(rec, harness[:i] + u"x" + harness[i:], facts), [])
        r2 = copy.deepcopy(rec)
        for rel in r2[u"生きた文書の file 全体の sha256(情報。門は照らさない)"]:
            r2[u"生きた文書の file 全体の sha256(情報。門は照らさない)"][rel] = u"0" * 64
        self.assertEqual(check_j(r2, harness, facts), [])
        r3 = copy.deepcopy(rec)
        r3[u"読んだ記録の sha256"][FACTS_REL] = sha64(FACTS_REL)
        self.assertNotEqual(check_j(r3, harness, facts), [])
        r4 = copy.deepcopy(rec)
        r4[u"読んだ生きた文書の部分の sha256"][FACTS_REL][u"sha256"] = u"0" * 64
        self.assertNotEqual(check_j(r4, harness, facts), [])
        r5 = copy.deepcopy(rec)
        r5[u"読んだ生きた文書の部分の sha256"][HARNESS_REL][u"sha256"] = u"0" * 64
        self.assertNotEqual(check_j(r5, harness, facts), [])


class OrderTest(unittest.TestCase):
    u"""(i) 封の commit が script・記録・文書・門の commit より前。"""

    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="rowclaim_root_")
        cls.grun = staticmethod(make_run(REPO))

    def _p(self, steps):
        t = build(self.base, steps)
        return order_problems(t.run, "")

    def test_i_1_the_real_history_has_the_seal_before_the_four_files(self):
        u"""script・記録・文書・門のどれかが未 commit なら赤(足した commit が無い)。4 つとも commit された後で初めて緑。"""
        p = order_problems(self.grun, PREFIX)
        self.assertEqual(p, [])

    def test_i_2_the_real_seal_is_one_commit_and_an_ancestor_of_head(self):
        lst = added_commits(self.grun, PREFIX + SEAL_REL)
        self.assertEqual(len(lst), 1)
        self.assertTrue(lst[0].startswith(SEAL_COMMIT_SHORT))
        self.assertTrue(is_anc(self.grun, lst[0], "HEAD"))

    def test_i_3_a_correct_order_is_green(self):
        self.assertEqual(self._p(["SEAL", "SCRIPT", "RECORD", "DOC", "GATE"]), [])
        self.assertEqual(self._p(["SEAL", "ALL4"]), [])
        self.assertEqual(self._p(["SEAL", "ALL4", "SEAL_APPEND"]), [])               # 日付つきの追記(削除 0)は許される

    def test_i_4_a_file_before_the_seal_is_red(self):
        for first in ("SCRIPT", "RECORD", "DOC", "GATE"):
            steps = [first, "SEAL"] + [k for k in ("SCRIPT", "RECORD", "DOC", "GATE") if k != first]
            self.assertIn(first + "_BEFORE_SEAL", codes(self._p(steps)), first)

    def test_i_5_an_uncommitted_file_is_red_not_skipped(self):
        self.assertIn("GATE_UNCOMMITTED", codes(self._p(["SEAL", "SCRIPT", "RECORD", "DOC"])))
        self.assertIn("SCRIPT_UNCOMMITTED", codes(self._p(["SEAL"])))

    def test_i_6_the_seal_missing_or_added_twice_is_red(self):
        self.assertIn("SEAL_ONCE", codes(self._p(["ALL4"])))
        self.assertIn("SEAL_ONCE", codes(self._p(["SEAL", "ALL4", "SEAL_TWICE"])))

    def test_i_7_rewriting_the_seal_after_the_fact_is_red(self):
        self.assertIn("SEAL_REWRITE", codes(self._p(["SEAL", "ALL4", "SEAL_REWRITE"])))

    def test_i_8_the_same_commit_as_the_seal_is_red(self):
        t = Tmp(self.base)
        for k in ("SEAL", "SCRIPT", "RECORD", "DOC", "GATE"):
            t.write(FILES[k], u"# %s\n" % k)
        t.commit("all", *FILES.values())
        self.assertIn("SCRIPT_BEFORE_SEAL", codes(order_problems(t.run, "")))


if __name__ == "__main__":
    unittest.main()
