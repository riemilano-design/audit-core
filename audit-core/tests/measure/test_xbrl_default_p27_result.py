# -*- coding: utf-8 -*-
u"""既定の profile を P26 から P27 に切り替えた(段 2)の結果の門 ― 封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md §2(S-1〜S-12)を縛る。

記録 ``fixtures/xbrl/default_p27_2026-10-28.json``(``measure/xbrl_default_p27_2026-10-28.py`` の出力)・文書 ``docs/XBRL_DEFAULT_P27_RESULT_2026-10-28.md``。

この門がやること(どれも、変異で赤くなることを確かめてから門と呼ぶ。変異は ``MutationTest`` が毎回走らせる):
  1. 記録を行から**数え直し**、記録の集計と一致させる(97 書類の byte 一致の行・4 state・動いた行の向き・報告形の節・注入の数)。
  2. 記録の数を**別の記録と突き合わせる**: 既定の 4 state・書類ごとの出力の sha256(engine の欄を除く)・動いた行の集合は、P27 を**明示して**E の engine で測った記録
     ``fixtures/xbrl/p27/regress97_2026-10-27.json`` の P27 の欄と 1 行ずつ同じ。儀式は P26 の記録の写し ``ritual_2026-10-20_p26.json`` と ``入力``・``注入``・``素の書類`` の 3 欄だけ違う。
  3. 予測 S-1〜S-12 の当たり外れを、**封の字の太字から**幅を読んで、記録の数から門が自分で求め直し(記録の ``予測の判定`` とは別の関数)、文書の表と一致させる。
     S-12 は ``test_xbrl_p27_result.py`` の ``decisions``(評価用の記録 3 つ + 97 書類の記録から D の 9 小項目を数え直す別の関数)で求め直した判定と一致させる。
  4. engine: 作業木の ``vocabulary.py``・``verify_document.py`` の sha16 は封の commit 時点の値から**宣言された遷移の値**に動き、``DEFAULT_PROFILE`` が P27。差分は封の commit からの
     ``git diff --numstat`` で ``vocabulary.py`` が挿入 ≤ 8・削除 1、``verify_document.py`` が挿入 1・削除 1、ほかの engine の file と ``core/`` は 0 行。
  5. 文書の数のある表は記録から門が作った字と 1 行も違わない(``<!-- 門:start 名前 -->`` の中)。門の外の散文の数には【門なし】の印が要る。
  6. 軽い走らせ直し(手元の cache の 2 書類)を script で走らせ、記録の該当行と一致。
縛っていないもの: 試験の赤の数(S-8・S-9)は実装席が走らせた実測を人が書いた表で、記録は入力の file の sha256 を持つ(門は表の内訳の足し算と封の幅との当たり外れだけを見る)、
読み(正しい文かどうか)は測っていない。
**変数名について**: 過去の門が tests/measure の行頭の名前を数えるので、この門は engine の留めを定義する変数を行頭に置かない(sha16 は ``EXPECT`` の中)。
この file は評価用・調整用の docID の字を持たない(引きの門 test_xbrl_fresh_seal が追跡 file の docID を数える)。
"""
import collections
import copy
import hashlib
import importlib.util
import io
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
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

REC = os.path.join(ROOT, "fixtures", "xbrl", "default_p27_2026-10-28.json")
DOC = os.path.join(ROOT, "docs", "XBRL_DEFAULT_P27_RESULT_2026-10-28.md")
SEAL_REL = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"
SEAL = os.path.join(ROOT, SEAL_REL)
SEAL_COMMIT = "87f83fd"
SCRIPT = os.path.join(ROOT, "measure", "xbrl_default_p27_2026-10-28.py")
REGRESS_REC = os.path.join(ROOT, "fixtures", "xbrl", "p27", "regress97_2026-10-27.json")
P26_REC = os.path.join(ROOT, "fixtures", "xbrl", "p26_2026-10-21.json")
FETCHED = os.path.join(ROOT, "fixtures", "xbrl", "fresh", "fetched_2026-10-21.json")
RITUAL_REC = os.path.join(ROOT, "fixtures", "xbrl", "ritual_2026-10-20.json")
RITUAL_P26 = os.path.join(ROOT, "fixtures", "xbrl", "ritual_2026-10-20_p26.json")
SUITE_REC = os.path.join(ROOT, "fixtures", "suite_coverage_2026-10-16.json")
FACTS_REL = "docs/FACTS_FOR_BUYERS_2026-10-20.md"
EXISTING_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
FRESH_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-fresh-2026-10-21")
LIGHT_DOCS = (("S100YMFV", False), ("S100YXFQ", True))        # 手元の 67 から 1・新しい標本の 30 から 1
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
README_REL = ("README.md", "README.en.md")
STEP_NAMES = (u"S-1", u"S-2", u"S-3", u"S-4", u"S-5", u"S-6", u"S-7", u"S-8", u"S-9", u"S-10", u"S-11", u"S-12")
POP67, POP30 = u"手元の 67", u"新しい標本 30"
NOT_GATED = u"【門なし】"
HEAVY_ENVS = ("AUDIT_CORE_PACKAGING", "AUDIT_CORE_CUSTOMER_REPORT", "AUDIT_CORE_CUSTOMER_REPORT_FIX", "AUDIT_CORE_POINT_PRIOR", "AUDIT_CORE_DEFAULT_P26", "AUDIT_CORE_FRESH",
              "AUDIT_CORE_ROUNDING", "AUDIT_CORE_VOCAB", "AUDIT_CORE_P26", "AUDIT_CORE_PERIOD_BIND", "AUDIT_CORE_LASTBRANCH", "AUDIT_CORE_RITUAL")

#: **字で留める**(測った事実。定数から作らない)。変えたら記録も文書も作り直す。
EXPECT = {
    "vocab_sha16": "514ebb8104451c07", "vd_sha16": "c3791080ab5aef2f",       # 封の commit 時点の値は git show で読む(下の s7 の表)
    "fingerprint": "92326a0f4dcefd21fae4393a611e4206ef174b19258ddadd0213117191e7b399",
    "frozen_bundle": "030455282c89661b4c0152498d76bc30314362b5896b15ab67a8886a6887b0f6",
    "docs": (67, 30), "claims": (7799, 3923),
    "states_default_67": (4371, 433, 1601, 1394), "states_p26_67": (4371, 433, 1579, 1416),
    "states_default_30": (2194, 250, 787, 692), "states_p26_30": (2194, 250, 774, 705),
    "moved": (28, 15),
    "ritual": (u"2 / 243 = 0.8%", u"210 / 243 = 86.4%", 31), "plain": (340, 25, 33, 14),
    "report": (433, 1773, 145, 1077, 4371),
    "hole_b": (0, 485, 480, 5), "step2_injected": (0, 64),
}
MODULES = {}


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    return json.loads(jtext(p))


def sha_path(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha16(rel):
    return sha_path(os.path.join(ROOT, rel))[:16]


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def comma(n):
    return format(n, ",")


def pct1(a, b):
    return u"%.1f%%" % (100.0 * a / b) if b else u"―"


def F(a, b):
    return u"%d / %d = %s" % (a, b, pct1(a, b))


def load_module(rel, name):
    if name not in MODULES:
        spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        MODULES[name] = m
    return MODULES[name]


def num(s):
    return int(s.replace(u",", u""))


# ----------------------------------------------------------------------------------------------------------------
# 封の字から幅を読む(記録の ``予測の判定`` を作る script とは別の書き方: 項目ごとの正規表現)
def seal_rows(seal):
    rows = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"\| \*\*S-(\d+)\*\* \| (.*) \| ([^|]*) \|$", l)
        if m:
            rows[u"S-" + m.group(1)] = (m.group(2), m.group(3))
    assert list(rows) == list(STEP_NAMES), list(rows)
    return rows


def _m(pattern, cell):
    m = re.search(pattern, cell)
    assert m, pattern
    return m.groups()


def seal_bounds(seal):
    u"""封 §2 の予測の行から、判定に使う数を項目ごとに読む。"""
    rows = seal_rows(seal)
    c = dict((k, v[0]) for k, v in rows.items())
    b = {}
    s1 = re.findall(r"\*\*(\d+) / (\d+)\*\*", c[u"S-1"])
    b[u"S-1"] = {u"67": int(s1[0][0]), u"30": int(s1[1][0]), u"対照": int(s1[2][0]), u"対照の分母": int(s1[2][1])}
    for k, pop in ((u"S-2", u"67"), (u"S-3", u"30")):
        g, v, u_, p = _m(r"GROUNDED \*\*([\d,]+)\*\*・VALUE_MISMATCH \*\*([\d,]+)\*\*・UNVERIFIABLE \*\*([\d,]+)\*\*・POINTER_NOT_FOUND \*\*([\d,]+)\*\*", c[k])
        moved = _m(r"state の違う行 \*\*(\d+)\*\*", c[k])[0]
        pu, up = _m(r"POINTER_NOT_FOUND → UNVERIFIABLE \*\*(\d+)\*\*・UNVERIFIABLE → POINTER_NOT_FOUND \*\*(\d+)\*\*", c[k])
        other = _m(r"他の向き \*\*(\d+)\*\*", c[k])[0]
        leave, tovm, newg = _m(r"GROUNDED を離れる行 \*\*(\d+)\*\*・VALUE_MISMATCH に入る行 \*\*(\d+)\*\*・新しい GROUNDED \*\*(\d+)\*\*", c[k])
        diff = _m(r"過不足 \*\*(\d+)\*\*", c[k])[0]
        b[k] = {u"state": (num(g), num(v), num(u_), num(p)), u"moved": num(moved), u"PU": num(pu), u"UP": num(up), u"他の向き": num(other),
                u"離れる": num(leave), u"VM に入る": num(tovm), u"新 G": num(newg), u"集合の過不足": num(diff)}
        if k == u"S-2":
            b[k][u"reason か pointer"] = num(_m(r"state が同じで reason か pointer が違う行 \*\*(\d+)\*\*", c[k])[0])
    s4 = c[u"S-4"]
    b[u"S-4"] = {u"通した": _m(r"通した \*\*([^*]+)\*\*", s4)[0], u"止めた": _m(r"止めた\(VALUE_MISMATCH\)\*\*([^*]+)\*\*", s4)[0],
                 u"PNF": num(_m(r"結べない\(POINTER_NOT_FOUND\)\*\*(\d+)\*\*", s4)[0]),
                 u"素の書類": tuple(num(x) for x in _m(r"GROUNDED \*\*(\d+)\*\*・POINTER_NOT_FOUND \*\*(\d+)\*\*・UNVERIFIABLE \*\*(\d+)\*\*・VALUE_MISMATCH \*\*(\d+)\*\*", s4)),
                 u"違う欄": re.findall(r"`([^`]+)`", _m(r"\*\*((?:`[^`]+`・?)+) の 3 つだけ\*\*", s4)[0])}
    b[u"S-5"] = tuple(num(x) for x in _m(r"違う \*\*([\d,]+)\*\*・要確認 \*\*([\d,]+)\*\*・対象外 \*\*([\d,]+)\*\*・判断しない \*\*([\d,]+)\*\*・一致 \*\*([\d,]+)\*\*", c[u"S-5"]))
    s6 = c[u"S-6"]
    b[u"S-6"] = {u"穴 B 通した": int(_m(r"\*\*(\d+) / 485\*\*", s6)[0]), u"止めた": num(_m(r"止めた \*\*(\d+)\*\*", s6)[0]), u"その他": num(_m(r"その他 \*\*(\d+)\*\*", s6)[0]),
                 u"段 2": int(_m(r"\*\*(\d+) / 64\*\*", s6)[0]), u"違う行": tuple(num(x) for x in _m(r"穴 B \*\*(\d+)\*\*・段 2 \*\*(\d+)\*\*", s6))}
    s7 = c[u"S-7"]
    b[u"S-7"] = {u"voc 挿入": int(_m(r"`vocabulary.py` の挿入 \*\*≤ (\d+)\*\*", s7)[0]), u"voc 削除": int(_m(r"削除 \*\*(\d+)\*\*\(`DEFAULT_PROFILE` の行\)", s7)[0]),
                 u"vd 挿入": int(_m(r"`verify_document.py` の挿入 \*\*(\d+)\*\*", s7)[0]), u"vd 削除": int(_m(r"`verify_document.py` の挿入 \*\*\d+\*\*・削除 \*\*(\d+)\*\*", s7)[0]),
                 u"file": int(_m(r"`adapter_xbrl_py_files` \*\*(\d+)\*\*", s7)[0]), u"本数": int(_m(r"frozen_bundle の本数 \*\*(\d+)\*\*", s7)[0])}
    s8 = c[u"S-8"]
    p27 = dict((m[0], int(m[1])) for m in re.findall(r"`(test_xbrl_p27_\w+\.py)` \*\*(\d+)\*\*", s8))
    lo, hi = _m(r"合計の幅 \*\*(\d+)〜(\d+)\*\*", s8)
    b[u"S-8"] = {u"measure": int(_m(r"`tests/measure` の赤 \*\*(\d+) 本\*\*", s8)[0]), u"adapters": int(_m(r"`tests/adapters/xbrl` の赤 \*\*(\d+) 本\*\*", s8)[0]),
                 u"幅": (int(lo), int(hi)), u"P27 の門": p27}
    assert sorted(p27) == [u"test_xbrl_p27_engine_result.py", u"test_xbrl_p27_eval.py", u"test_xbrl_p27_order.py", u"test_xbrl_p27_result.py", u"test_xbrl_p27_seal.py"], sorted(p27)
    b[u"S-9"] = {u"増える赤": int(_m(r"増えた赤は \*\*(\d+) 本\*\*", c[u"S-9"])[0])}
    s11 = re.findall(r"\*\*(\d+)\*\*", c[u"S-11"])
    b[u"S-11"] = {u"いま": int(s11[0]), u"封の commit": int(s11[1]), u"実装の commit": int(s11[2])}
    return b


# ----------------------------------------------------------------------------------------------------------------
# 数え直し(記録の行から)
def population(rec, which):
    rows = [r for r in rec[u"S1"][u"書類別"] if r[u"標本"] == which]
    moved = rec[u"S2" if which == POP67 else u"S3"][u"動いた行"]
    st, st26 = collections.Counter(), collections.Counter()
    for r in rows:
        st.update(r[u"既定の state"])
        st26.update(r[u"P26 の state"])
    dirs = collections.Counter(u"%s → %s" % (m[u"P26"][u"state"], m[u"既定"][u"state"]) for m in moved)
    return {u"rows": rows, u"moved": moved, u"claims": sum(r[u"claims"] for r in rows),
            u"default": tuple(st.get(s, 0) for s in STATES), u"p26": tuple(st26.get(s, 0) for s in STATES), u"dirs": dirs,
            u"leave": sum(1 for m in moved if m[u"P26"][u"state"] == "GROUNDED"),
            u"to_vm": sum(1 for m in moved if m[u"既定"][u"state"] == "VALUE_MISMATCH" and m[u"P26"][u"state"] != "VALUE_MISMATCH"),
            u"new_g": sum(1 for m in moved if m[u"既定"][u"state"] == "GROUNDED"),
            u"not_same": sum(1 for r in rows if not r[u"既定と P27 明示が同じ byte"]),
            u"ctrl_differs": sum(1 for r in rows if not r[u"既定を P26 に戻した対照が既定と同じ byte"]),
            u"other_dir": sum(1 for m in moved if (m[u"P26"][u"state"], m[u"既定"][u"state"]) not in (("POINTER_NOT_FOUND", "UNVERIFIABLE"), ("UNVERIFIABLE", "POINTER_NOT_FOUND"))),
            u"extra": sum(r[u"state・reason・pointers のどれかが違う行の数"] for r in rows) - len(moved)}


def regress_view(which):
    u"""regress97 の記録(P27 を明示して E の engine で測った)から、その標本の書類ごとの 4 state・出力の sha256・動いた行の集合を取る。"""
    reg = jload(REGRESS_REC)
    docs = dict((d[u"docID"], d) for d in reg[u"書類"] if d[u"標本"] == which)
    moved = set((m["docID"], m["id"], m[u"前"]["state"], m[u"前"]["reason"], m[u"後"]["state"], m[u"後"]["reason"]) for m in reg[u"動いた行"][which][u"P26 → P27"])
    return docs, moved


def check_population(rec, which):
    p = population(rec, which)
    key = u"S2" if which == POP67 else u"S3"
    one, s = rec[u"S1"][which], rec[key]
    assert one[u"書類"] == len(p[u"rows"]) and one[u"claims"] == p[u"claims"], which
    assert one[u"既定と P27 明示で違った書類"] == p[u"not_same"] and one[u"対照(既定を実行中だけ P26 に戻す)で違った書類"] == p[u"ctrl_differs"], which
    assert one[u"既定の 4 state"] == dict(zip(STATES, p[u"default"])) and one[u"P26 の 4 state"] == dict(zip(STATES, p[u"p26"])), which
    assert s[u"既定の 4 state"] == one[u"既定の 4 state"] and s[u"P26 の 4 state"] == one[u"P26 の 4 state"], which
    assert sum(p[u"default"]) == sum(p[u"p26"]) == p[u"claims"], which
    assert s[u"既定と P26 で state の違う行"] == len(p[u"moved"]) and s[u"向き"] == dict(sorted(p[u"dirs"].items())), which
    assert (s[u"GROUNDED を離れる行"], s[u"VALUE_MISMATCH に入る行"], s[u"新しい GROUNDED"]) == (p[u"leave"], p[u"to_vm"], p[u"new_g"]), which
    assert s[u"state は同じで reason か pointer が違う行"] == p[u"extra"], which
    by_doc = collections.defaultdict(list)
    for m in p[u"moved"]:
        by_doc[m[u"doc"]].append(m)
    assert len({(m[u"doc"], m[u"id"]) for m in p[u"moved"]}) == len(p[u"moved"]), u"動いた行に重複"
    for r in p[u"rows"]:
        ms = by_doc.get(r[u"doc"], [])
        for st in STATES:
            net = sum(1 for m in ms if m[u"既定"][u"state"] == st) - sum(1 for m in ms if m[u"P26"][u"state"] == st)
            assert r[u"既定の state"].get(st, 0) - r[u"P26 の state"].get(st, 0) == net, (r[u"doc"], st)
        for m in ms:
            assert m[u"P26"][u"state"] != m[u"既定"][u"state"], (m[u"doc"], m[u"id"])
        assert sum(r[u"既定の state"].values()) == sum(r[u"P26 の state"].values()) == r[u"claims"], r[u"doc"]
        assert set(r[u"profile の欄"]) == {u"既定", u"P27 明示", u"対照"}
        assert r[u"profile の欄"][u"P27 明示"] == "P27" and r[u"profile の欄"][u"対照"] == "P26", r[u"doc"]
        if r[u"既定と P27 明示が同じ byte"]:
            assert r[u"profile の欄"][u"既定"] == "P27" and r[u"既定の state"] == r[u"P27 明示の state"], r[u"doc"]
        assert not r[u"既定を P26 に戻した対照が既定と同じ byte"], (r[u"doc"], u"対照(既定を実行中だけ P26 に戻す)が差を拾わなかった = 『差零』が自分の欠陥かもしれない")
    # regress97 の P27 の欄(P27 を明示して E の engine で測った)と 1 行ずつ: 書類ごとの 4 state・出力の sha256・動いた行の集合
    docs, reg_moved = regress_view(which)
    assert sorted(docs) == sorted(r[u"doc"] for r in p[u"rows"]), which
    for r in p[u"rows"]:
        d = docs[r[u"doc"]]
        assert d[u"4 state"]["P27"] == dict((st, r[u"既定の state"].get(st, 0)) for st in STATES), (r[u"doc"], u"regress97 の P27 の 4 state と違う")
        assert d[u"4 state"]["P26"] == dict((st, r[u"P26 の state"].get(st, 0)) for st in STATES), (r[u"doc"], u"regress97 の P26 の 4 state と違う")
        assert d[u"出力の sha256(engine の欄を除く)"]["P27"] == r[u"既定の出力の sha256(engine の欄を除く)"], (r[u"doc"], u"regress97 の P27 の出力の sha256 と違う")
        assert d[u"zip の sha256"] == r[u"zip の sha256"], r[u"doc"]
    got_moved = set((m[u"doc"], m[u"id"], m[u"P26"][u"state"], m[u"P26"][u"reason"], m[u"既定"][u"state"], m[u"既定"][u"reason"]) for m in p[u"moved"])
    assert got_moved == reg_moved, u"動いた行が regress97 の動いた行(P26 → P27)と集合として違う"
    assert (s[u"regress97 に無い動いた行"], s[u"regress97 に在って今回に無い行"]) == (0, 0) and s[u"regress97 の動いた行(P26 → P27)と同じ集合"] is True
    assert s[u"regress97 の P27 の 4 state と違う書類"] == [] and s[u"regress97 の P27 の出力の sha256 と違う書類"] == []
    return p


def check_record(rec):
    u"""記録の集計を、行から数え直した値と突き合わせる。壊した記録で赤くなる。"""
    p67 = check_population(rec, POP67)
    p30 = check_population(rec, POP30)
    assert (len(p67[u"rows"]), len(p30[u"rows"])) == (67, 30) and len(rec[u"S1"][u"書類別"]) == 97
    assert len({r[u"doc"] for r in rec[u"S1"][u"書類別"]}) == 97
    # 儀式: 記録の欄は、P27(既定)で採り直した記録と P26 の記録の写しの両方と突き合わせる
    s4 = rec[u"S4"]
    ritual, r26 = jload(RITUAL_REC), jload(RITUAL_P26)
    assert s4[u"profile"] == "P27" and rec[u"環境"][u"DEFAULT_PROFILE"] == "P27"
    assert s4[u"通した"][u"字"] == F(s4[u"通した"][u"件"], s4[u"通した"][u"分母"]) and s4[u"止めた"][u"字"] == F(s4[u"止めた"][u"件"], s4[u"止めた"][u"分母"])
    assert s4[u"通した"][u"件"] + s4[u"止めた"][u"件"] + sum(s4[u"止めた でも 通した でもない結果"].values()) == s4[u"通した"][u"分母"] == s4[u"注入の対象"]
    assert sum(s4[u"素の書類の state の分布"].values()) == s4[u"素の書類 claim"]
    assert s4[u"土台の state の分布"] == s4[u"素の書類の state の分布"]
    assert (s4[u"通した"], s4[u"止めた"], s4[u"止めた でも 通した でもない結果"]) == (ritual[u"通した"], ritual[u"止めた"], ritual[u"止めた でも 通した でもない結果"])
    assert s4[u"素の書類の state の分布"] == ritual[u"素の書類"][u"state の分布"] and s4[u"素の書類 claim"] == ritual[u"素の書類"][u"claim"]
    assert s4[u"採り直した儀式の記録(ritual_2026-10-20.json)と違う欄(所要秒・実行環境を除く)"] == []
    vol = lambda r: dict((k, v) for k, v in r.items() if k not in (u"所要秒", u"実行環境"))
    assert s4[u"P26 の記録(ritual_2026-10-20_p26.json)と違う欄(所要秒・実行環境を除く)"] == [k for k in sorted(set(vol(r26)) | set(vol(ritual))) if r26.get(k) != ritual.get(k)]
    assert (s4[u"P26 の記録の通した"], s4[u"P26 の記録の止めた"], s4[u"P26 の記録のその他"]) == (r26[u"通した"], r26[u"止めた"], r26[u"止めた でも 通した でもない結果"])
    assert s4[u"P26 の記録の素の書類の state の分布"] == r26[u"素の書類"][u"state の分布"]
    assert s4[u"通した の一覧の (id, 型)"] == sorted([x[u"id"], x[u"型"]] for x in ritual[u"通した の一覧"])
    s5 = rec[u"S5"]
    per = s5[u"書類別"]
    assert len(per) == 67 and [d[u"doc"] for d in per] == sorted(d[u"doc"] for d in per)
    for k, f in ((u"違う", u"違う(節の件数)"), (u"要確認", u"要確認(節の件数)"), (u"対象外", u"対象外"), (u"判断しない", u"判断しない"), (u"一致", u"一致(節の件数)"),
                 (u"VALUE_MISMATCH(state)の合計", u"VALUE_MISMATCH(state)"), (u"総 claim", u"claims")):
        assert s5[k] == sum(d[f] for d in per), k
    assert s5[u"節の合計"] == s5[u"違う"] + s5[u"要確認"] + s5[u"対象外"] + s5[u"判断しない"] + s5[u"一致"] == s5[u"総 claim"] == p67[u"claims"]
    assert s5[u"違う"] == s5[u"VALUE_MISMATCH(state)の合計"] == p67[u"default"][1] and s5[u"一致"] == p67[u"default"][0]
    for d in per:
        assert d[u"違う(節の件数)"] == d[u"VALUE_MISMATCH(state)"], d[u"doc"]
    h = rec[u"S6"][u"穴 B"]
    assert sum(h[u"既定の結果"].values()) == h[u"注入"] == 485
    assert h[u"既定で止めた"] + h[u"既定のその他"] + h[u"既定で通した"][u"件"] == h[u"注入"]
    assert h[u"既定で通した"] == {u"件": h[u"既定で通した"][u"件"], u"分母": 485, u"率": round(100.0 * h[u"既定で通した"][u"件"] / 485, 1)}
    assert h[u"P26 の記録の P26 の欄と違った行"] == 0 and h[u"違った行"] == [] and h[u"P26 明示(対照)と違った行"] == 0
    q3 = jload(P26_REC)[u"Q3"]
    assert h[u"記録(P26 の欄)の行"] == len(q3[u"穴 B"][u"行"]) == h[u"注入"] and h[u"P26 明示(対照)で通した"][u"件"] == q3[u"穴 B"][u"集計"][u"P26 で通した(GROUNDED のまま)"][u"件"]
    t = rec[u"S6"][u"段 2"]
    assert t[u"行"] == 192 and t[u"注入"] == 64 and t[u"全注入で Core 自身(既定)が GROUNDED"][u"分母"] == 64
    assert t[u"P26 の記録の P26 の欄と違った行"] == 0 and t[u"違った行"] == [] and t[u"記録(P26 の欄)の行"] == len(q3[u"段 2"][u"行"]) == t[u"行"]
    s7 = rec[u"S7"]
    assert s7[u"core/"] == {u"差の行数": 0, u"status": u""}
    for f, v in s7.items():
        if f.startswith(u"adapters/") and isinstance(v, dict) and f not in (u"adapters/xbrl/vocabulary.py", u"adapters/xbrl/verify_document.py"):
            assert v == {u"挿入": 0, u"削除": 0}, f
    assert s7[u"vocabulary.py・verify_document.py 以外で封の commit から動いた file"] == [] and s7[u"adapters/xbrl の file 数"] == 16
    assert len(s7[u"vocabulary.py の削除された行(封の commit から)"]) == s7[u"adapters/xbrl/vocabulary.py"][u"削除"]
    assert len(s7[u"verify_document.py の削除された行(封の commit から)"]) == s7[u"adapters/xbrl/verify_document.py"][u"削除"]
    assert s7[u"vocabulary.py の削除された行(封の commit から)"] == [u'DEFAULT_PROFILE = "P26"']
    return p67, p30


def check_inputs(rec):
    inp = rec[u"入力"]
    p26 = jload(P26_REC)
    in67 = p26[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"]
    assert inp[u"手元の 67 書類の sha256"] == in67, u"67 書類の sha256 が P26 の記録の入力と違う"
    fetched = jload(FETCHED)
    in30 = dict((x["docID"], x["sha256"]) for x in fetched[u"取得した書類"] if x["docID"] in fetched[u"使う書類"])
    assert inp[u"新しい標本 30 書類の sha256"] == in30 and sorted(in30) == sorted(fetched[u"使う書類"]), u"30 書類の sha256 が取得の記録と違う"
    assert inp[u"手元の 67 が P26 の記録の入力と同じ"] is True and inp[u"新しい標本 30 が取得の記録の入力と同じ"] is True
    assert inp[u"regress97 の記録の sha256"] == sha_path(REGRESS_REC), u"regress97 の記録が測定の時と違う"
    c = rec[u"cache の前後"]
    assert c[u"変化なし"] is True and c[u"前"] == c[u"後"], u"測定の間に既存の cache が変わった"
    assert c[u"前"][u"edinet"][u"件数"] == 281 and c[u"前"][u"edinet-fresh-2026-10-21"][u"件数"] == 40, u"cache の件数が 281・40 でない"
    assert [r[u"zip の sha256"] for r in rec[u"S1"][u"書類別"]] == [in67[r[u"doc"]] if r[u"標本"] == POP67 else in30[r[u"doc"]] for r in rec[u"S1"][u"書類別"]]
    env = rec[u"環境"]
    assert env[u"費用"] == u"0 USD" and env[u"DEFAULT_PROFILE"] == "P27"
    assert env[u"vocabulary.py の sha16"] == EXPECT["vocab_sha16"] and env[u"verify_document.py の sha16"] == EXPECT["vd_sha16"]
    assert env[u"engine の指紋"][u"adapter_xbrl_py_sha256"] == EXPECT["fingerprint"] and env[u"engine の指紋"][u"adapter_xbrl_py_files"] == 16
    assert env[u"engine の指紋"][u"core_py_sha256"] == "34e836bb39762d5af831a9aa11d4ea095e73221beb5bd4510d3b234363a2a6e8" and env[u"engine の指紋"][u"core_py_files"] == 4
    assert env[u"frozen_bundle の束ねた sha"] == EXPECT["frozen_bundle"] and env[u"frozen_bundle の本数"] == 37
    assert env[u"比べた profile"] == [u"省略(None = vocabulary.DEFAULT_PROFILE)", u"P27(明示)", u"P26(既定を実行中だけ P26 に戻した対照)"]
    assert env[u"ラベル 2 file の sha256(起動時に照合)"] == jload(RITUAL_REC)[u"実行環境"][u"ラベル 2 file の sha256(起動時に照合)"]
    assert not any(v for k, v in env[u"鍵の名前の有無(値は読まない)"].items() if k != u"ANTHROPIC_BASE_URL"), u"鍵の名前が設定されている"
    assert u"開いていない" in env[u"評価用・調整用の AI の文・DB の応答"]
    assert re.match(r"^[0-9a-f]{40}$", rec[u"封の commit"]) and rec[u"封の commit"].startswith(SEAL_COMMIT)
    assert re.match(r"^[0-9a-f]{40}$", env[u"HEAD"])


# ----------------------------------------------------------------------------------------------------------------
# 試験の赤(S-8・S-9)。人が書いた表(記録は入力 file の sha256 を持つ)の内訳の足し算と、封の幅との当たり外れだけを縛る
P27_GATES = (u"test_xbrl_p27_result.py", u"test_xbrl_p27_seal.py", u"test_xbrl_p27_engine_result.py", u"test_xbrl_p27_eval.py", u"test_xbrl_p27_order.py")


def reds(rec):
    r = rec[u"試験の赤"]
    s8, s9 = r[u"S8"], r[u"S9"]
    me, ad = s8[u"tests/measure"], s8[u"tests/adapters/xbrl"]
    assert me[u"赤"] == len(me[u"ids"]) == len(set(me[u"ids"])) and ad[u"赤"] == len(ad[u"ids"]) == len(set(ad[u"ids"]))
    assert me[u"file"] == len(set(i.split(u"::")[0] for i in me[u"ids"])) and ad[u"file"] == len(set(i.split(u"::")[0] for i in ad[u"ids"]))
    assert all(i.startswith(u"tests/measure/") for i in me[u"ids"]) and all(i.startswith(u"tests/adapters/xbrl/") for i in ad[u"ids"])
    allids = me[u"ids"] + ad[u"ids"]
    assert set(s8[u"種類"]) == set(allids), u"種類の表が赤の一覧と 1 対 1 でない"
    kinds = collections.Counter(s8[u"種類"][i] for i in allids)
    assert set(kinds) <= {u"1", u"2", u"3", u"4"}, kinds
    p27 = dict((n, sum(1 for i in me[u"ids"] if i.startswith(u"tests/measure/" + n + u"::"))) for n in P27_GATES)
    assert s8[u"P27 の門 5 本の赤"] == p27, u"P27 の門の赤の数が、赤の id の一覧から数えた数と違う"
    assert s9[u"増えた赤"] == len(s9[u"増えた赤の id"]) == len(set(s9[u"増えた赤の id"]))
    af = s9[u"実装の後"]
    runs = af[u"走らせ直し"]
    assert sorted(runs) == sorted(HEAVY_ENVS), u"12 変数が全部あるか"
    assert all(v[u"赤"] == len(v[u"赤の id"]) for v in runs.values())
    assert af[u"赤"] == sum(v[u"赤"] for v in runs.values()) == sum(len(v[u"赤の id"]) for v in runs.values())
    assert all((v[u"rc"] == 0) == (v[u"赤"] == 0) for v in runs.values()), u"rc と赤の数が食い違う"
    return {u"measure": me[u"赤"], u"measure_file": me[u"file"], u"adapters": ad[u"赤"], u"adapters_file": ad[u"file"], u"total": me[u"赤"] + ad[u"赤"],
            u"others": s8[u"golden・fixtures・measure/tests・core の赤"], u"record_gate": s8[u"記録を書き換えないと緑にならない門"], u"human_gate": s8[u"人間の決定の字の門の赤"],
            u"kinds": dict(kinds), u"p27": p27, u"extra": s9[u"増えた赤"], u"after": af[u"赤"], u"runs": runs, u"after_table": af}


def judge_reds(rec, b):
    R = reds(rec)
    b8, b9 = b[u"S-8"], b[u"S-9"]
    lo, hi = b8[u"幅"]
    ok8 = (lo <= R[u"total"] <= hi and R[u"others"] == 0 and R[u"record_gate"] == 0 and R[u"human_gate"] == 0
           and set(R[u"kinds"]) <= {u"1", u"2", u"3", u"4"} and R[u"p27"] == b8[u"P27 の門"])
    ok9 = R[u"extra"] == b9[u"増える赤"] and R[u"after"] == 0
    return {u"S-8": ok8, u"S-9": ok9}


# ----------------------------------------------------------------------------------------------------------------
# 判定(記録の数と封の字の太字から。記録の ``予測の判定`` を作る script とは別の関数)
def moved_set(p):
    return set((m[u"doc"], m[u"id"], m[u"P26"][u"state"], m[u"P26"][u"reason"], m[u"既定"][u"state"], m[u"既定"][u"reason"]) for m in p[u"moved"])


def judge_pop(p, which, bb):
    docs, reg_moved = regress_view(which)
    sym = len(moved_set(p) ^ reg_moved)
    dirs = dict(p[u"dirs"])
    return (p[u"default"] == tuple(bb[u"state"]) and len(p[u"moved"]) == bb[u"moved"]
            and dirs == dict((k, v) for k, v in ((u"POINTER_NOT_FOUND → UNVERIFIABLE", bb[u"PU"]), (u"UNVERIFIABLE → POINTER_NOT_FOUND", bb[u"UP"])) if v)
            and p[u"other_dir"] == bb[u"他の向き"] and p[u"leave"] == bb[u"離れる"] and p[u"to_vm"] == bb[u"VM に入る"] and p[u"new_g"] == bb[u"新 G"]
            and (which != POP67 or p[u"extra"] == bb[u"reason か pointer"]) and sym == bb[u"集合の過不足"])


def judge(rec, b):
    J = {}
    p67, p30 = population(rec, POP67), population(rec, POP30)
    s1 = b[u"S-1"]
    J[u"S-1"] = (p67[u"not_same"] == s1[u"67"] and p30[u"not_same"] == s1[u"30"] and p67[u"ctrl_differs"] + p30[u"ctrl_differs"] == s1[u"対照"] == s1[u"対照の分母"] == len(rec[u"S1"][u"書類別"]))
    J[u"S-2"] = judge_pop(p67, POP67, b[u"S-2"])
    J[u"S-3"] = judge_pop(p30, POP30, b[u"S-3"])
    s4, bb = rec[u"S4"], b[u"S-4"]
    st = s4[u"素の書類の state の分布"]
    J[u"S-4"] = (s4[u"通した"][u"字"] == bb[u"通した"] and s4[u"止めた"][u"字"] == bb[u"止めた"] and s4[u"止めた でも 通した でもない結果"] == {"detected:POINTER_NOT_FOUND": bb[u"PNF"]}
                 and (st["GROUNDED"], st["POINTER_NOT_FOUND"], st["UNVERIFIABLE"], st["VALUE_MISMATCH"]) == tuple(bb[u"素の書類"])
                 and sorted(s4[u"P26 の記録(ritual_2026-10-20_p26.json)と違う欄(所要秒・実行環境を除く)"]) == sorted(bb[u"違う欄"])
                 and s4[u"採り直した儀式の記録(ritual_2026-10-20.json)と違う欄(所要秒・実行環境を除く)"] == []
                 and s4[u"通した の一覧の (id, 型)"] == s4[u"P26 の記録の 通した の一覧の (id, 型)"])
    s5 = rec[u"S5"]
    J[u"S-5"] = [s5[u"違う"], s5[u"要確認"], s5[u"対象外"], s5[u"判断しない"], s5[u"一致"]] == list(b[u"S-5"]) and s5[u"違う"] == s5[u"VALUE_MISMATCH(state)の合計"] and s5[u"節の合計"] == s5[u"総 claim"]
    s6, bb = rec[u"S6"], b[u"S-6"]
    J[u"S-6"] = (s6[u"穴 B"][u"既定で通した"][u"件"] == bb[u"穴 B 通した"] and s6[u"穴 B"][u"既定で止めた"] == bb[u"止めた"] and s6[u"穴 B"][u"既定のその他"] == bb[u"その他"]
                 and s6[u"段 2"][u"全注入で Core 自身(既定)が GROUNDED"][u"件"] == bb[u"段 2"]
                 and (s6[u"穴 B"][u"P26 の記録の P26 の欄と違った行"], s6[u"段 2"][u"P26 の記録の P26 の欄と違った行"]) == tuple(bb[u"違う行"]))
    s7, bb = rec[u"S7"], b[u"S-7"]
    voc, vd = s7[u"adapters/xbrl/vocabulary.py"], s7[u"adapters/xbrl/verify_document.py"]
    J[u"S-7"] = (voc[u"挿入"] <= bb[u"voc 挿入"] and voc[u"削除"] == bb[u"voc 削除"] and vd[u"挿入"] == bb[u"vd 挿入"] and vd[u"削除"] == bb[u"vd 削除"]
                 and s7[u"core/"][u"差の行数"] == 0 and s7[u"vocabulary.py・verify_document.py 以外で封の commit から動いた file"] == []
                 and rec[u"環境"][u"engine の指紋"][u"adapter_xbrl_py_files"] == bb[u"file"] == s7[u"adapters/xbrl の file 数"] and rec[u"環境"][u"frozen_bundle の本数"] == bb[u"本数"]
                 and rec[u"環境"][u"engine の指紋"][u"core_py_sha256"] == "34e836bb39762d5af831a9aa11d4ea095e73221beb5bd4510d3b234363a2a6e8")
    return J


def judge_docs(rec, b, decision=None):
    J = {}
    p10 = rec[u"S10"]
    line = p10[u"README.md の いまの段 の行"]
    J[u"S-10"] = (all(p10[r][u"節に 通した の字"] and p10[r][u"節に 止めた の字"] for r in README_REL)
                  and line[u"P27(2026-10-28、既定を P27)"] == 1 and line[u"P26(2026-10-23、既定を P26)"] == 1
                  and p10[FACTS_REL][u"P26 の字の数"] == 0 and p10[FACTS_REL][u"P27 の字の数"] == 0)
    s11, bb = rec[u"S11"], b[u"S-11"]
    J[u"S-11"] = s11[u"試験 file の数(ディスク上)"] == bb[u"実装の commit"] and s11[u"覆われていない file"] == 0 and s11[u"覆いの記録の試験 file の数"] == bb[u"実装の commit"]
    J[u"S-12"] = decision is not None and rec[u"S12"][u"判定の文"] == list(decision)
    return J


def judge_all(rec, b, decision=None):
    J = {}
    J.update(judge(rec, b))
    J.update(judge_reds(rec, b))
    J.update(judge_docs(rec, b, decision))
    assert sorted(J, key=lambda k: int(k[2:])) == list(STEP_NAMES)
    return J


def recorded_judgments(rec):
    return dict((k, v[u"当たり"]) for k, v in rec[u"予測の判定"].items())


_PR = {}


def p27_result_module():
    u"""評価用の結果の門(test_xbrl_p27_result.py)の関数 ``decisions``・``verdict_sentences`` と ``load_all`` を使う(別の関数で D の 9 小項目を数え直す)。"""
    if "m" not in _PR:
        _PR["m"] = load_module("tests/measure/test_xbrl_p27_result.py", "p27_result_gate_for_default_p27")
    return _PR["m"]


def eval_decision():
    PR = p27_result_module()
    file_bytes, recs, e_recs = PR.load_all()
    seal_text = PR.read_text(PR.SEAL_REL)
    meas = PR.measures_of(recs, e_recs, seal_text)
    dec = PR.decisions(meas, seal_text)
    return dec, PR.verdict_sentences(dec)


# ----------------------------------------------------------------------------------------------------------------
# 文書の表(記録から作る)
def table(head, rows):
    L = [u"| " + u" | ".join(head) + u" |", u"|" + u"|".join(u"---" for _ in head) + u"|"]
    for r in rows:
        L.append(u"| " + u" | ".join(r) + u" |")
    return L


def cell(s):
    return (s if s is not None else u"").replace(u"|", u"｜").replace(u"\n", u" ")


def bold_tokens(seal, k):
    return re.findall(r"\*\*([^*]+)\*\*", seal_rows(seal)[k][0])


def measured_cells(rec, b, J):
    p67, p30 = population(rec, POP67), population(rec, POP30)
    s4, s5, s6, s7 = rec[u"S4"], rec[u"S5"], rec[u"S6"], rec[u"S7"]
    voc, vd = s7[u"adapters/xbrl/vocabulary.py"], s7[u"adapters/xbrl/verify_document.py"]
    R = reds(rec)
    st = s4[u"素の書類の state の分布"]
    M = {}
    M[u"S-1"] = u"違った書類 %d / 67・%d / 30。対照で違った書類 %d / 97" % (p67[u"not_same"], p30[u"not_same"], p67[u"ctrl_differs"] + p30[u"ctrl_differs"])
    for k, p in ((u"S-2", p67), (u"S-3", p30)):
        M[k] = u"GROUNDED %s・VALUE_MISMATCH %s・UNVERIFIABLE %s・POINTER_NOT_FOUND %s。state の違う行 %d(%s)。他の向き %d・離れる %d・VALUE_MISMATCH に入る %d・新しい GROUNDED %d・reason か pointer だけ違う %d" % (
            tuple(comma(x) for x in p[u"default"]) + (len(p[u"moved"]), u"・".join(u"%s %d" % (d, p[u"dirs"][d]) for d in sorted(p[u"dirs"])),
                                                       p[u"other_dir"], p[u"leave"], p[u"to_vm"], p[u"new_g"], p[u"extra"]))
    M[u"S-4"] = u"通した %s・止めた %s・POINTER_NOT_FOUND %d。素の書類 GROUNDED %d・POINTER_NOT_FOUND %d・UNVERIFIABLE %d・VALUE_MISMATCH %d。P26 の記録と違う欄 %s" % (
        s4[u"通した"][u"字"], s4[u"止めた"][u"字"], sum(s4[u"止めた でも 通した でもない結果"].values()), st["GROUNDED"], st["POINTER_NOT_FOUND"], st["UNVERIFIABLE"], st["VALUE_MISMATCH"],
        u"・".join(s4[u"P26 の記録(ritual_2026-10-20_p26.json)と違う欄(所要秒・実行環境を除く)"]))
    M[u"S-5"] = u"違う %s・要確認 %s・対象外 %s・判断しない %s・一致 %s(合計 %s)" % tuple(comma(x) for x in (s5[u"違う"], s5[u"要確認"], s5[u"対象外"], s5[u"判断しない"], s5[u"一致"], s5[u"節の合計"]))
    M[u"S-6"] = u"穴 B で通した %s・止めた %d・その他 %d。段 2 の材料で Core 自身が GROUNDED %s。P26 の記録の P26 の欄と違う行 穴 B %d・段 2 %d" % (
        F(s6[u"穴 B"][u"既定で通した"][u"件"], 485), s6[u"穴 B"][u"既定で止めた"], s6[u"穴 B"][u"既定のその他"], F(s6[u"段 2"][u"全注入で Core 自身(既定)が GROUNDED"][u"件"], 64),
        s6[u"穴 B"][u"P26 の記録の P26 の欄と違った行"], s6[u"段 2"][u"P26 の記録の P26 の欄と違った行"])
    M[u"S-7"] = u"`vocabulary.py` 挿入 %d・削除 %d。`verify_document.py` 挿入 %d・削除 %d。ほかで動いた file %d・`core/` %d 行。`adapter_xbrl_py_files` %d・frozen_bundle の本数 %d" % (
        voc[u"挿入"], voc[u"削除"], vd[u"挿入"], vd[u"削除"], len(s7[u"vocabulary.py・verify_document.py 以外で封の commit から動いた file"]), s7[u"core/"][u"差の行数"],
        rec[u"環境"][u"engine の指紋"][u"adapter_xbrl_py_files"], rec[u"環境"][u"frozen_bundle の本数"])
    M[u"S-8"] = u"`tests/measure` %d 本(%d file)・`tests/adapters/xbrl` %d 本(%d file)。合計 %d。種類 %s。P27 の門 5 本 %s。ほか %d・記録を書き換える門 %d・人間の決定の字の門 %d" % (
        R[u"measure"], R[u"measure_file"], R[u"adapters"], R[u"adapters_file"], R[u"total"], u"・".join(u"%s が %d" % (k, v) for k, v in sorted(R[u"kinds"].items())),
        u"・".join(u"%s %d" % (n.replace(u"test_xbrl_p27_", u"").replace(u".py", u""), R[u"p27"][n]) for n in P27_GATES), R[u"others"], R[u"record_gate"], R[u"human_gate"])
    M[u"S-9"] = u"実装の前の基準の木(封の commit + engine 2 file)で増えた赤 %d 本。実装の後の 12 変数の赤 %d 本" % (R[u"extra"], R[u"after"])
    p10 = rec[u"S10"]
    M[u"S-10"] = u"README の儀式の節に 通した・止めた の字: %s。「いまの段」の P27 の行 %d・P26 の行 %d。`FACTS_FOR_BUYERS` の P26 の字 %d・P27 の字 %d" % (
        u"・".join(u"%s %s" % (r, u"在る" if p10[r][u"節に 通した の字"] and p10[r][u"節に 止めた の字"] else u"無い") for r in README_REL),
        p10[u"README.md の いまの段 の行"][u"P27(2026-10-28、既定を P27)"], p10[u"README.md の いまの段 の行"][u"P26(2026-10-23、既定を P26)"],
        p10[FACTS_REL][u"P26 の字の数"], p10[FACTS_REL][u"P27 の字の数"])
    M[u"S-11"] = u"試験 file %d 本(ディスク上)・覆いの記録 %d 本・覆われていない file %d" % (rec[u"S11"][u"試験 file の数(ディスク上)"], rec[u"S11"][u"覆いの記録の試験 file の数"], rec[u"S11"][u"覆われていない file"])
    M[u"S-12"] = u"記録の判定の文: " + u" / ".join(rec[u"S12"][u"判定の文"])
    return M


def reason_pairs(p):
    c = collections.Counter(u"%s → %s" % (u"%s / %s" % (m[u"P26"][u"state"], m[u"P26"][u"reason"]) if m[u"P26"][u"reason"] else m[u"P26"][u"state"],
                                         u"%s / %s" % (m[u"既定"][u"state"], m[u"既定"][u"reason"]) if m[u"既定"][u"reason"] else m[u"既定"][u"state"]) for m in p[u"moved"])
    return sorted(c.items())


def render_blocks(rec, b, decision=None, seal=None):
    seal = seal if seal is not None else jtext(SEAL)
    J = judge_all(rec, b, decision)
    M = measured_cells(rec, b, J)
    p67, p30 = population(rec, POP67), population(rec, POP30)
    B = collections.OrderedDict()
    B["pred"] = table([u"#", u"予測の太字(封の字)", u"外れ方(封の字)", u"実測(記録から)", u"当たり外れ"],
                      [[u"**%s**" % k, cell(u"・".join(bold_tokens(seal, k))), cell(seal_rows(seal)[k][1].strip()), cell(M[k]), u"**当たり**" if J[k] else u"**外れ**"] for k in STEP_NAMES])
    B["s1"] = table([u"標本", u"書類", u"claim", u"既定と P27 明示で違った書類", u"対照(既定を実行中だけ P26 に戻す)で違った書類"],
                    [[w, str(len(p[u"rows"])), comma(p[u"claims"]), str(p[u"not_same"]), str(p[u"ctrl_differs"])] for w, p in ((POP67, p67), (POP30, p30))])
    B["s2"] = table([u"標本", u"profile", u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND"],
                    [[w, name] + [F(v, p[u"claims"]) for v in vals] for w, p in ((POP67, p67), (POP30, p30)) for name, vals in ((u"P26", p[u"p26"]), (u"既定(P27)", p[u"default"]))])
    B["s3"] = table([u"標本", u"向き(P26 → 既定)", u"行"], [[w, d, str(p[u"dirs"][d])] for w, p in ((POP67, p67), (POP30, p30)) for d in sorted(p[u"dirs"])])
    B["s3reason"] = table([u"標本", u"動いた行の state と reason(P26 → 既定)", u"行"], [[w, k, str(v)] for w, p in ((POP67, p67), (POP30, p30)) for k, v in reason_pairs(p)])
    s4 = rec[u"S4"]
    B["s4"] = table([u"儀式(同梱の 1 書類)", u"通した", u"止めた(VALUE_MISMATCH)", u"止めた(POINTER_NOT_FOUND)", u"注入の対象"],
                    [[u"P26(`ritual_2026-10-20_p26.json`)", s4[u"P26 の記録の通した"][u"字"], s4[u"P26 の記録の止めた"][u"字"], str(sum(s4[u"P26 の記録のその他"].values())), str(s4[u"通した"][u"分母"])],
                     [u"既定(P27。`ritual_2026-10-20.json`)", s4[u"通した"][u"字"], s4[u"止めた"][u"字"], str(sum(s4[u"止めた でも 通した でもない結果"].values())), str(s4[u"注入の対象"])]])
    B["s4base"] = table([u"素の書類(claim %d)の state" % s4[u"素の書類 claim"], u"P26", u"既定(P27)"],
                        [[k, str(s4[u"P26 の記録の素の書類の state の分布"][k]), str(s4[u"素の書類の state の分布"][k])] for k in STATES])
    s5 = rec[u"S5"]
    B["s5"] = table([u"報告形の節(67 書類)", u"件"], [[k, comma(s5[k])] for k in (u"違う", u"要確認", u"対象外", u"判断しない", u"一致")] + [[u"合計", comma(s5[u"節の合計"])]])
    s6 = rec[u"S6"]
    B["s6"] = table([u"誤りを通す側", u"既定(P27)", u"P26 明示(対照)"],
                    [[u"穴 B の注入 485 件で通した", F(s6[u"穴 B"][u"既定で通した"][u"件"], 485), F(s6[u"穴 B"][u"P26 明示(対照)で通した"][u"件"], 485)],
                     [u"穴 B の注入で止めた(VALUE_MISMATCH)", str(s6[u"穴 B"][u"既定で止めた"]), str(s6[u"穴 B"][u"P26 明示(対照)で止めた"])],
                     [u"段 2 の材料の注入 64 件で Core 自身が GROUNDED", F(s6[u"段 2"][u"全注入で Core 自身(既定)が GROUNDED"][u"件"], 64), u"(測っていない)"]])
    s7, env = rec[u"S7"], rec[u"環境"]
    rows = []
    for rel, now in (("adapters/xbrl/vocabulary.py", env[u"vocabulary.py の sha16"]), ("adapters/xbrl/verify_document.py", env[u"verify_document.py の sha16"])):
        base = hashlib.sha256(subprocess.run(["git", "show", SEAL_COMMIT + ":audit-core/" + rel], cwd=ROOT, capture_output=True).stdout).hexdigest()[:16]
        rows.append([u"`%s`" % rel, base, now, str(s7[rel][u"挿入"]), str(s7[rel][u"削除"])])
    B["s7"] = table([u"engine の file", u"封の commit の sha16", u"いまの sha16", u"挿入", u"削除"], rows)
    B["s7fp"] = table([u"束ねた指紋・frozen_bundle", u"値"],
                      [[u"`adapter_xbrl_py_sha256`(%d file)" % env[u"engine の指紋"][u"adapter_xbrl_py_files"], u"`%s`" % env[u"engine の指紋"][u"adapter_xbrl_py_sha256"]],
                       [u"`core_py_sha256`(%d file)" % env[u"engine の指紋"][u"core_py_files"], u"`%s`" % env[u"engine の指紋"][u"core_py_sha256"]],
                       [u"frozen_bundle の束ねた sha(%d 本)" % env[u"frozen_bundle の本数"], u"`%s`" % env[u"frozen_bundle の束ねた sha"]]])
    R = reds(rec)
    s8 = rec[u"試験の赤"][u"S8"]
    B["reds"] = table([u"実装の前の基準の木(封の commit + engine 2 file)で、試験を直す前の赤", u"本", u"file"],
                      [[u"`tests/measure`", str(R[u"measure"]), str(R[u"measure_file"])], [u"`tests/adapters/xbrl`", str(R[u"adapters"]), str(R[u"adapters_file"])], [u"合計", str(R[u"total"]), u""]]
                      + [[u"種類 %s" % k, str(v), u""] for k, v in sorted(R[u"kinds"].items())]
                      + [[u"P27 の門 `%s`" % n, str(R[u"p27"][n]), u""] for n in P27_GATES])
    B["after"] = table([u"実装の後の重い走らせ直し(環境変数)", u"rc", u"赤"], [[u"`%s`" % e, str(R[u"runs"][e][u"rc"]), str(R[u"runs"][e][u"赤"])] for e in HEAVY_ENVS])
    s11 = rec[u"S11"]
    B["s11"] = table([u"覆い", u"本"], [[u"試験 file(ディスク上)", str(s11[u"試験 file の数(ディスク上)"])], [u"覆いの記録の試験 file", str(s11[u"覆いの記録の試験 file の数"])], [u"覆われていない file", str(s11[u"覆われていない file"])]])
    inp = rec[u"入力"]
    B["sha"] = table([u"記録・入力", u"sha256"], [[u"`fixtures/xbrl/ritual_2026-10-20_p26.json`", sha_path(RITUAL_P26)], [u"`fixtures/xbrl/p27/regress97_2026-10-27.json`", inp[u"regress97 の記録の sha256"]],
                                              [u"`fixtures/xbrl/p26_2026-10-21.json`", sha_path(P26_REC)]])
    return B


def block_text(name, lines):
    return u"<!-- 門:start %s -->\n%s\n<!-- 門:end -->" % (name, u"\n".join(lines))


BLOCK_RE = re.compile(r"<!-- 門:start (\S+) -->\n(.*?)\n<!-- 門:end -->", re.S)


def doc_blocks(doc):
    out = collections.OrderedDict()
    for m in BLOCK_RE.finditer(doc):
        assert m.group(1) not in out, u"同じ名前の門の表が 2 つ: " + m.group(1)
        out[m.group(1)] = m.group(2).split(u"\n")
    return out


def check_doc(rec, doc, b, decision):
    B = render_blocks(rec, b, decision)
    got = doc_blocks(doc)
    assert list(got) == list(B), u"文書の門の表の名前と順が違う: %s" % list(got)
    for k, lines in B.items():
        assert got[k] == lines, u"文書の表『%s』が記録から作った表と違う" % k
    stripped = BLOCK_RE.sub(u"", doc)
    assert [l for l in stripped.split(u"\n") if l.lstrip().startswith(u"|")] == [], u"門の外に表の行がある"
    bad = [l[:50] for l in stripped.split(u"\n") if re.search(r"\d+(?:\.\d+)?\s*(?:%|行|件|社|席|書類|試行|回|本|ポイント)", l) and NOT_GATED not in l]
    assert bad == [], u"散文の数に【門なし】の印が無い: %s" % bad
    for lit in (u"読みはエージェントの読み", u"判定は覆さない", u"基準の木", u"S-8", u"S-9", u"verify_document.py", u"人間の決定", u"【門なし】", u"測っていない"):
        assert lit in doc, lit
    heads = re.findall(r"^## (\d+)\.", doc, re.M)
    assert heads == [str(i) for i in range(1, len(heads) + 1)] and len(heads) >= 8, heads
    assert doc.index(u"<!-- 門:start pred -->") < doc.index(u"## 2."), u"予測の当否が先頭にない"
    # 判定の文は 2 つ、字のまま(反対の字は無い)
    for s in decision:
        assert sum(1 for l in doc.split(u"\n") if l.strip() == s) == 1, s
    # 評価用・調整用の docID と claim の id を持たない
    assert not re.findall(r"S100[0-9A-Z]{4}", doc), u"文書に docID の字が在る"
    assert not re.findall(r"\b[NT]\d{3}\b", doc), u"文書に claim の id の字が在る"
    J = judge_all(rec, b, decision)
    assert recorded_judgments(rec) == J, u"記録の予測の判定が門の判定と違う"


def have_cache(docs):
    return all(os.path.exists(os.path.join(FRESH_DIR if fresh else EXISTING_CACHE, d + ".zip")) for d, fresh in docs)


def labels_ok():
    try:
        from adapters.xbrl import instance as I
        return all(os.path.exists(os.path.join(I.taxonomy_dir(), fn)) for _ns, fn, _sha in I.TAXONOMY_LABEL_FILES)
    except Exception:
        return False


# ----------------------------------------------------------------------------------------------------------------
# engine: 宣言された遷移(封が履歴に在り、値が宣言の値のときだけ)
ENGINE_DECL = {"adapters/xbrl/vocabulary.py": (EXPECT["vocab_sha16"], 8, 1), "adapters/xbrl/verify_document.py": (EXPECT["vd_sha16"], 1, 1)}


def engine_ok():
    assert git("log", "--diff-filter=A", "--format=%H", "--", SEAL_REL).stdout.split(), u"封が履歴に無い"
    from adapters.xbrl import vocabulary as V
    assert V.DEFAULT_PROFILE == "P27", V.DEFAULT_PROFILE
    for rel, (want, ins_max, dele) in sorted(ENGINE_DECL.items()):
        assert sha16(rel) == want, u"**%s が、宣言された遷移の値とも違う**" % rel
        p = git("diff", SEAL_COMMIT, "--numstat", "--", rel).stdout.split()
        assert int(p[0]) <= ins_max and int(p[1]) == dele, (rel, p)
    for f in sorted(os.listdir(os.path.join(ROOT, "adapters", "xbrl"))):
        if f.endswith(".py") and ("adapters/xbrl/" + f) not in ENGINE_DECL:
            assert git("diff", SEAL_COMMIT, "--numstat", "--", "adapters/xbrl/" + f).stdout.strip() == u"", u"封の commit から動いた: " + f
    assert git("diff", SEAL_COMMIT, "--numstat", "--", "core").stdout.strip() == u"" and git("status", "--porcelain", "--", "core").stdout.strip() == u""
    from adapters.xbrl import verify_document as VD
    fp = VD.engine_fingerprint()
    assert fp["adapter_xbrl_py_sha256"] == EXPECT["fingerprint"] and fp["adapter_xbrl_py_files"] == 16, u"束ねた指紋が宣言の値と違う"
    assert fp["core_py_sha256"] == "34e836bb39762d5af831a9aa11d4ea095e73221beb5bd4510d3b234363a2a6e8" and fp["core_py_files"] == 4
    return True


# ----------------------------------------------------------------------------------------------------------------
STAGE2_FILES = ("measure/xbrl_default_p27_2026-10-28.py", "fixtures/xbrl/default_p27_2026-10-28.json", "docs/XBRL_DEFAULT_P27_RESULT_2026-10-28.md",
                "tests/measure/test_xbrl_default_p27_result.py", "tests/measure/test_xbrl_default_p27_seal.py", "fixtures/xbrl/ritual_2026-10-20_p26.json")


class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)
        cls.bounds = seal_bounds(cls.seal)
        cls.decision = eval_decision()

    def test_1_record_is_consistent(self):
        check_record(self.rec)

    def test_2_inputs_are_pinned(self):
        check_inputs(self.rec)

    def test_3_document_tables_equal_the_record(self):
        check_doc(self.rec, self.doc, self.bounds, self.decision[1])

    def test_4_facts_as_measured(self):
        u"""この実行の事実を字で留める(行から数えた値。変えたら記録も文書も作り直す)。"""
        p67, p30 = population(self.rec, POP67), population(self.rec, POP30)
        self.assertEqual((len(p67[u"rows"]), len(p30[u"rows"])), EXPECT["docs"])
        self.assertEqual((p67[u"claims"], p30[u"claims"]), EXPECT["claims"])
        self.assertEqual(p67[u"default"], EXPECT["states_default_67"])
        self.assertEqual(p67[u"p26"], EXPECT["states_p26_67"])
        self.assertEqual(p30[u"default"], EXPECT["states_default_30"])
        self.assertEqual(p30[u"p26"], EXPECT["states_p26_30"])
        self.assertEqual((len(p67[u"moved"]), len(p30[u"moved"])), EXPECT["moved"])
        self.assertEqual((p67[u"not_same"], p30[u"not_same"]), (0, 0))
        self.assertEqual((p67[u"ctrl_differs"], p30[u"ctrl_differs"]), (67, 30))
        s4 = self.rec[u"S4"]
        self.assertEqual((s4[u"通した"][u"字"], s4[u"止めた"][u"字"], sum(s4[u"止めた でも 通した でもない結果"].values())), EXPECT["ritual"])
        st = s4[u"素の書類の state の分布"]
        self.assertEqual((st["GROUNDED"], st["POINTER_NOT_FOUND"], st["UNVERIFIABLE"], st["VALUE_MISMATCH"]), EXPECT["plain"])
        s5 = self.rec[u"S5"]
        self.assertEqual((s5[u"違う"], s5[u"要確認"], s5[u"対象外"], s5[u"判断しない"], s5[u"一致"]), EXPECT["report"])
        h = self.rec[u"S6"][u"穴 B"]
        self.assertEqual((h[u"既定で通した"][u"件"], h[u"注入"], h[u"既定で止めた"], h[u"既定のその他"]), EXPECT["hole_b"])
        t = self.rec[u"S6"][u"段 2"]
        self.assertEqual((t[u"全注入で Core 自身(既定)が GROUNDED"][u"件"], t[u"注入"]), EXPECT["step2_injected"])

    def test_5_engine_is_the_declared_after_value_and_the_default_is_p27(self):
        self.assertTrue(engine_ok())
        s7 = self.rec[u"S7"]
        self.assertEqual((s7[u"adapters/xbrl/vocabulary.py"][u"挿入"], s7[u"adapters/xbrl/vocabulary.py"][u"削除"]), (5, 1))
        self.assertEqual((s7[u"adapters/xbrl/verify_document.py"][u"挿入"], s7[u"adapters/xbrl/verify_document.py"][u"削除"]), (1, 1))
        self.assertEqual(self.rec[u"環境"][u"vocabulary.py の sha16"], sha16("adapters/xbrl/vocabulary.py"))
        self.assertEqual(self.rec[u"環境"][u"verify_document.py の sha16"], sha16("adapters/xbrl/verify_document.py"))

    def test_6_judgments_equal_the_document_table_and_the_seal_rows_are_not_edited(self):
        J = judge_all(self.rec, self.bounds, self.decision[1])
        self.assertEqual(recorded_judgments(self.rec), J)
        for k in STEP_NAMES:
            row = [l for l in self.doc.splitlines() if l.startswith(u"| **%s** |" % k)]
            self.assertEqual(len(row), 1, k)
            cells = [c.strip() for c in row[0].strip().strip(u"|").split(u"|")]
            self.assertEqual(len(cells), 5, k)
            self.assertEqual(cells[2], cell(seal_rows(self.seal)[k][1].strip()), u"%s の外れ方の欄が封の字と違う" % k)
            self.assertEqual(cells[4], u"**当たり**" if J[k] else u"**外れ**", k)
        # 封は封の commit から 1 字も直していない(数を見てから封を直さない)
        self.assertEqual(git("diff", "--numstat", SEAL_COMMIT, "--", SEAL_REL).stdout, "")
        self.assertEqual(git("status", "--porcelain", "--", SEAL_REL).stdout, "")

    def test_7_s12_is_recomputed_by_another_function(self):
        u"""S-12: 判定を評価用の結果の門(記録 4 つから D の 9 小項目を数え直す別の関数)で求め直しても『P27 を既定の候補として記録する』。"""
        dec, sentences = self.decision
        self.assertTrue(dec["default_P27"] and dec["adopt_P27E"])
        self.assertIn(u"P27 を「既定の候補」として記録する", sentences[1])
        self.assertEqual(self.rec[u"S12"][u"判定の文"], list(sentences))
        self.assertIn(u"P27 を既定の候補として記録する", u"".join(bold_tokens(self.seal, u"S-12")).replace(u"「", u"").replace(u"」", u""))

    def test_8_suite_count_and_coverage_are_live(self):
        u"""S-11 を記録でなく**いまの木**から。覆いの記録・SUITE_COVERAGE §2-1 の数がいまのディスクと一致。(2026-10-28 追記: 試験 file の数の比べは、いまのディスクでなく段 2 の commit 6a34db5 の木と。いまの木の数は覆いの記録だけが縛る。前例 test_xbrl_default_p26_result.py の test_8 の 2026-10-27 の追記と同じ。記録 S11 の 234 は測った時点の値で書き換えない。)"""
        n = 0
        for base, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__", ".pytest_cache")]
            n += sum(1 for f in files if f.startswith("test_") and f.endswith(".py"))
        ls = subprocess.run(["git", "ls-tree", "-r", "--name-only", "6a34db5"], cwd=ROOT, capture_output=True, text=True)
        if ls.returncode == 0:
            n_stage2 = sum(1 for path in ls.stdout.splitlines()
                           if os.path.basename(path).startswith("test_") and path.endswith(".py")
                           and not any(x in path for x in (".git", "node_modules", "__pycache__", ".pytest_cache")))
            self.assertEqual(n_stage2, self.rec[u"S11"][u"試験 file の数(ディスク上)"], u"段 2 の commit 6a34db5 の木の試験 file の数が記録と違う")
        else:
            print(u"SKIP: git ls-tree 6a34db5 が失敗(履歴の無い写し)。段 2 の試験 file の数と記録の比べを省く")
        suite = jload(SUITE_REC)
        self.assertEqual(suite["test_files_on_disk"], n, u"覆いの記録が古い(`measure/suite_coverage_2026-10-16.py --write`)")
        self.assertEqual(suite["uncovered_files"], [])
        cov = jtext(os.path.join(ROOT, "docs", "SUITE_COVERAGE_2026-10-16.md"))
        self.assertIn(u"%d" % n, cov)

    def test_9_p26_ritual_copy_is_the_byte_identical_record_in_history_and_the_ritual_record_is_recaptured(self):
        self.assertEqual(sha_path(RITUAL_P26), "42ff63e2" + sha_path(RITUAL_P26)[8:])
        r = subprocess.run(["git", "show", "aeae608:audit-core/fixtures/xbrl/ritual_2026-10-20.json"], cwd=REPO, capture_output=True)
        if r.returncode == 0:
            self.assertEqual(hashlib.sha256(r.stdout).hexdigest(), sha_path(RITUAL_P26))
        else:
            print(u"SKIP: git show aeae608 が失敗(履歴の無い写し)")
        self.assertNotEqual(sha_path(RITUAL_REC), sha_path(RITUAL_P26), u"ritual_2026-10-20.json が P26 の記録のまま(採り直していない)")
        self.assertEqual(jload(RITUAL_REC)[u"入力"][u"profile"], "P27")
        self.assertEqual(jload(RITUAL_P26)[u"入力"][u"profile"], "P26")

    def test_10_order_in_git_the_seal_comes_before_the_stage_2_files(self):
        base = git("log", "--diff-filter=A", "--format=%H", "--", SEAL_REL).stdout.split()
        self.assertTrue(base, u"封が履歴に無い")
        seal = base[-1]
        self.assertTrue(seal.startswith(SEAL_COMMIT))
        for rel in STAGE2_FILES:
            added = git("log", "--diff-filter=A", "--format=%H", "--", rel).stdout.split()
            if added:
                self.assertEqual(git("merge-base", "--is-ancestor", seal, added[-1]).returncode, 0, rel)
                self.assertNotEqual(seal, added[-1], rel)


def run_script(args):
    return subprocess.run([sys.executable, SCRIPT] + args, cwd=ROOT, capture_output=True, text=True, env=dict(os.environ))


@unittest.skipUnless(have_cache(LIGHT_DOCS) and labels_ok(), u"手元の cache の ZIP とラベルが要る")
class RerunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)

    def test_light_two_documents_match_the_record(self):
        out = os.path.join(tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None), "s1.json")
        r = run_script(["--stage", "s1", "--docs", ",".join(d for d, _f in LIGHT_DOCS), "--out", out, "--jobs", "2"])
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        got = jload(out)
        want = dict((x[u"doc"], x) for x in self.rec[u"S1"][u"書類別"] if x[u"doc"] in dict(LIGHT_DOCS))
        self.assertEqual(sorted(want), sorted(d for d, _f in LIGHT_DOCS))
        self.assertEqual(sorted(x[u"doc"] for x in got[u"S1"][u"書類別"]), sorted(want))
        for x in got[u"S1"][u"書類別"]:
            self.assertEqual(x, want[x[u"doc"]], x[u"doc"])
        want_moved = [m for k in (u"S2", u"S3") for m in self.rec[k][u"動いた行"] if m[u"doc"] in want]
        got_moved = [m for k in (u"S2", u"S3") for m in got[k][u"動いた行"]]
        self.assertEqual(sorted(got_moved, key=lambda m: (m[u"doc"], m[u"id"])), sorted(want_moved, key=lambda m: (m[u"doc"], m[u"id"])))

    def test_light_the_script_stops_when_the_default_is_not_p27(self):
        code = ("import sys, runpy; sys.path.insert(0, %r); sys.path.insert(0, %r); from adapters.xbrl import vocabulary as V; V.DEFAULT_PROFILE = 'P26'; "
                "sys.argv = [%r, '--stage', 's1', '--docs', 'S100YMFV', '--out', %r]; runpy.run_path(%r, run_name='__main__')") % (
                    os.path.join(ROOT, "core", "py"), ROOT, SCRIPT, os.path.join(tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None), "x.json"), SCRIPT)
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(u"既定 profile が P27 でない", r.stderr + r.stdout)


class MutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec0 = jload(REC)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)
        cls.bounds = seal_bounds(cls.seal)
        cls.decision = eval_decision()[1]

    def _mut(self):
        return copy.deepcopy(self.rec0)

    def _red(self, fn, *a):
        with self.assertRaises((AssertionError, KeyError, IndexError, TypeError, ValueError, ZeroDivisionError)):
            fn(*a)

    def test_baseline_is_green(self):
        check_record(self._mut())
        check_inputs(self._mut())
        check_doc(self._mut(), self.doc, self.bounds, self.decision)
        engine_ok()

    def test_m1_a_row_that_differs_in_byte_is_red(self):
        r = self._mut()
        r[u"S1"][u"書類別"][0][u"既定と P27 明示が同じ byte"] = False
        self._red(check_record, r)
        r = self._mut()
        r[u"S1"][u"書類別"][0][u"既定を P26 に戻した対照が既定と同じ byte"] = True        # 対照が差を拾わなかった
        self._red(check_record, r)

    def test_m2_a_changed_state_count_is_red(self):
        r = self._mut()
        r[u"S1"][u"書類別"][0][u"既定の state"]["GROUNDED"] += 1
        self._red(check_record, r)
        r = self._mut()
        r[u"S2"][u"既定の 4 state"]["GROUNDED"] += 1
        self._red(check_record, r)

    def test_m3_a_dropped_or_changed_moved_row_is_red(self):
        for k in (u"S2", u"S3"):
            r = self._mut()
            r[k][u"動いた行"].pop()
            self._red(check_record, r)
            r = self._mut()
            m = r[k][u"動いた行"][0]
            m[u"既定"][u"reason"] = (m[u"既定"][u"reason"] or u"") + u"x"
            self._red(check_record, r)

    def test_m4_a_report_section_or_injection_count_is_red(self):
        r = self._mut()
        r[u"S5"][u"書類別"][0][u"要確認(節の件数)"] += 1
        self._red(check_record, r)
        r = self._mut()
        r[u"S5"][u"違う"] += 1
        self._red(check_record, r)
        r = self._mut()
        r[u"S6"][u"穴 B"][u"既定で通した"][u"件"] = 1
        self._red(check_record, r)
        r = self._mut()
        r[u"S6"][u"段 2"][u"P26 の記録の P26 の欄と違った行"] = 1
        self._red(check_record, r)

    def test_m5_the_ritual_must_equal_the_ritual_record(self):
        r = self._mut()
        r[u"S4"][u"通した"] = dict(r[u"S4"][u"通した"], 件=15, 字=u"15 / 243 = 6.2%")
        self._red(check_record, r)
        r = self._mut()
        r[u"S4"][u"採り直した儀式の記録(ritual_2026-10-20.json)と違う欄(所要秒・実行環境を除く)"] = [u"通した"]
        self._red(check_record, r)
        r = self._mut()
        r[u"S4"][u"素の書類の state の分布"] = dict(r[u"S4"][u"素の書類の state の分布"], GROUNDED=r[u"S4"][u"素の書類の state の分布"]["GROUNDED"] + 1)
        self._red(check_record, r)

    def test_m6_engine_diff_or_core_diff_is_red(self):
        r = self._mut()
        r[u"S7"][u"core/"][u"差の行数"] = 1
        self._red(check_record, r)
        r = self._mut()
        r[u"S7"][u"adapters/xbrl/recipes.py"] = {u"挿入": 1, u"削除": 0}
        self._red(check_record, r)
        r = self._mut()
        r[u"S7"][u"vocabulary.py・verify_document.py 以外で封の commit から動いた file"] = [u"recipes.py"]
        self._red(check_record, r)

    def test_m7_a_spoiled_input_digest_is_red(self):
        r = self._mut()
        k = sorted(r[u"入力"][u"手元の 67 書類の sha256"])[0]
        r[u"入力"][u"手元の 67 書類の sha256"][k] = u"0" * 64
        self._red(check_inputs, r)
        r = self._mut()
        r[u"cache の前後"][u"後"][u"edinet"][u"件数"] += 1
        self._red(check_inputs, r)
        r = self._mut()
        r[u"環境"][u"DEFAULT_PROFILE"] = "P26"
        self._red(check_inputs, r)
        r = self._mut()
        r[u"環境"][u"vocabulary.py の sha16"] = u"0" * 16
        self._red(check_inputs, r)

    def test_m8_a_number_in_a_document_table_is_red(self):
        B = render_blocks(self.rec0, self.bounds, self.decision)
        for k, lines in B.items():
            v = block_text(k, lines)
            m = re.search(r"\d+", v[v.index(u"\n"):])
            self.assertIsNotNone(m, k)
            at = v.index(u"\n") + m.start()
            mutated = self.doc.replace(v, v[:at] + str(int(m.group(0)) + 7) + v[at + len(m.group(0)):], 1)
            self.assertNotEqual(mutated, self.doc, k)
            self._red(check_doc, self.rec0, mutated, self.bounds, self.decision)

    def test_m9_a_new_unbound_number_in_prose_is_red(self):
        self._red(check_doc, self.rec0, self.doc + u"\n影響は 12345 行。\n", self.bounds, self.decision)
        self._red(check_doc, self.rec0, self.doc + u"\n| 表 | 99 |\n", self.bounds, self.decision)

    def test_m10_the_reader_caveat_must_stay_in_the_document(self):
        self._red(check_doc, self.rec0, self.doc.replace(u"読みはエージェントの読み", u"読みは人間の読み"), self.bounds, self.decision)

    def test_m11_a_wrong_judgment_in_the_record_is_red(self):
        r = self._mut()
        r[u"予測の判定"][u"S-1"][u"当たり"] = not r[u"予測の判定"][u"S-1"][u"当たり"]
        self._red(check_doc, r, self.doc, self.bounds, self.decision)
        self._red(check_doc, self.rec0, self.doc.replace(self.decision[1], u"判定(P27): P27 を「既定の候補」として記録しない。", 1), self.bounds, self.decision)

    def test_m12_the_judgment_moves_with_the_numbers(self):
        r = self._mut()
        r[u"S1"][u"書類別"][0][u"既定と P27 明示が同じ byte"] = False
        r[u"S1"][POP67 if r[u"S1"][u"書類別"][0][u"標本"] == POP67 else POP30][u"既定と P27 明示で違った書類"] = 1
        self.assertFalse(judge(r, self.bounds)[u"S-1"])
        r = self._mut()
        r[u"S6"][u"穴 B"][u"既定で通した"][u"件"] = 1
        self.assertFalse(judge(r, self.bounds)[u"S-6"])
        r = self._mut()
        r[u"S7"][u"adapters/xbrl/vocabulary.py"][u"挿入"] = 9
        self.assertFalse(judge(r, self.bounds)[u"S-7"])
        r = self._mut()
        r[u"S7"][u"adapters/xbrl/verify_document.py"][u"挿入"] = 2
        self.assertFalse(judge(r, self.bounds)[u"S-7"])
        r = self._mut()
        r[u"S12"][u"判定の文"] = [u"判定(P27E): P27E を「外部の数の文に使う profile」として採用する。", u"判定(P27): P27 を「既定の候補」として記録しない。"]
        self.assertFalse(judge_docs(r, self.bounds, self.decision)[u"S-12"])
        r = self._mut()
        r[u"S11"][u"試験 file の数(ディスク上)"] += 1
        self.assertFalse(judge_docs(r, self.bounds, self.decision)[u"S-11"])
        r = self._mut()
        r[u"S2"][u"動いた行"].pop()
        r[u"S1"][u"書類別"][0][u"既定の state"]["GROUNDED"] += 1
        self.assertFalse(judge_pop(population(r, POP67), POP67, self.bounds[u"S-2"]) and judge(r, self.bounds)[u"S-2"])

    def test_m13_seal_bounds_are_read_from_the_seal_text(self):
        b = seal_bounds(self.seal)
        self.assertEqual(list(b[u"S-2"][u"state"]), [4371, 433, 1601, 1394])
        spoiled = u"\n".join(l.replace(u"**4,371**", u"**4,372**", 1) if l.startswith(u"| **S-2** |") else l for l in self.seal.split(u"\n"))
        self.assertNotEqual(spoiled, self.seal)
        self.assertEqual(seal_bounds(spoiled)[u"S-2"][u"state"][0], 4372)
        self.assertFalse(judge(self.rec0, seal_bounds(spoiled))[u"S-2"])
        spoiled = u"\n".join(l.replace(u"**≤ 8**", u"**≤ 3**", 1) if l.startswith(u"| **S-7** |") else l for l in self.seal.split(u"\n"))
        self.assertNotEqual(spoiled, self.seal)
        self.assertFalse(judge(self.rec0, seal_bounds(spoiled))[u"S-7"])

    def test_m14_a_wrong_engine_sha_is_red(self):
        saved = dict(ENGINE_DECL)
        try:
            ENGINE_DECL["adapters/xbrl/verify_document.py"] = ("0" * 16, 1, 1)
            self._red(engine_ok)
        finally:
            ENGINE_DECL.clear()
            ENGINE_DECL.update(saved)
        self.assertTrue(engine_ok())

    def test_m15_reds_table_must_add_up(self):
        r = self._mut()
        r[u"試験の赤"][u"S8"][u"tests/measure"][u"赤"] += 1
        self._red(reds, r)
        r = self._mut()
        ids = r[u"試験の赤"][u"S8"][u"tests/measure"][u"ids"]
        del r[u"試験の赤"][u"S8"][u"種類"][ids[0]]
        self._red(reds, r)
        r = self._mut()
        r[u"試験の赤"][u"S9"][u"実装の後"][u"走らせ直し"][HEAVY_ENVS[0]][u"赤"] += 1
        self._red(reds, r)
        r = self._mut()
        del r[u"試験の赤"][u"S9"][u"実装の後"][u"走らせ直し"][HEAVY_ENVS[-1]]
        self._red(reds, r)
        r = self._mut()
        r[u"試験の赤"][u"S8"][u"P27 の門 5 本の赤"][u"test_xbrl_p27_seal.py"] += 1
        self._red(reds, r)
        # 実装の後に赤が残れば S-9 は外れ
        r = self._mut()
        env = HEAVY_ENVS[0]
        r[u"試験の赤"][u"S9"][u"実装の後"][u"走らせ直し"][env] = {u"赤": 1, u"赤の id": [u"tests/measure/x.py::T::t"], u"rc": 1}
        r[u"試験の赤"][u"S9"][u"実装の後"][u"赤"] += 1
        self.assertFalse(judge_reds(r, self.bounds)[u"S-9"])


if __name__ == "__main__":
    unittest.main()
