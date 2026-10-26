# -*- coding: utf-8 -*-
u"""既定の profile を P22 から P26 に切り替えた(段 2)の結果の門 ― 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md §2(S-1〜S-12)を縛る。

記録 ``fixtures/xbrl/default_p26_2026-10-23.json``(``measure/xbrl_default_p26_2026-10-23.py`` の出力)・文書 ``docs/XBRL_DEFAULT_P26_RESULT_2026-10-23.md``。

この門がやること(どれも、変異で赤くなることを確かめてから門と呼ぶ。変異は ``MutationTest`` が毎回走らせる):
  1. 記録を行から**数え直し**、記録の集計と一致させる(97 書類の byte 一致の行・4 state・動いた行の向き・報告形の節・注入の数)。
  2. 記録の数を**別の記録と突き合わせる**: 既定の 4 state は P26 を明示して測った記録(``p26_2026-10-21.json``・``fresh/fresh_2026-10-21.json``)の P26 の欄と同じ、
     新しい標本の動いた行は ``fresh_2026-10-21.json`` の claim ごとの state(P22 の欄と P26 の欄)から別に求めた行と同じ、儀式は ``ritual_2026-10-20.json`` と同じ。
  3. 予測 S-1〜S-12 の当たり外れを、**封の字の太字から**幅を読んで、記録の数から門が自分で求め直し、文書の表と一致させる。S-12 は ``test_xbrl_fresh_result.py`` の
     ``judge``(別の関数)で K-1〜K-3 を数え直した判定と一致させる。
  4. engine: 作業木の ``vocabulary.py`` の sha16 は封の commit 時点の値から**宣言された遷移の値**に動き、``DEFAULT_PROFILE`` が P26。差分は封の commit からの
     ``git diff --numstat`` で挿入 4 行・削除 1 行(封の幅 ≤ 8・1)、ほかの engine の file は 0 行。
  5. 文書の数のある表と文は、記録から門が作った字と一致(散文の数は漢数字。算用数字は記録から作った表と、コードの字・識別子・日付だけ)。
  6. 軽い走らせ直し(手元の cache の 2 書類)を script で走らせ、記録の該当行と一致。全部の走らせ直しは ``AUDIT_CORE_DEFAULT_P26=1`` のときだけ。
縛っていないもの: 試験の赤の数(S-8・S-9)は試作の clone の実測を人が書いた表で、記録は入力の file の sha256 を持つ(門は表の内訳の足し算と封の幅との当たり外れだけを見る)、
読み(正しい文かどうか)は測っていない、漢数字で書いた数(``residual_numbers`` は算用数字だけを探す)。
**変数名について**: 過去の門が tests/measure の行頭の名前を数えるので、この門は engine の留めを定義する変数を置かない(sha16 は ``EXPECT`` の中)。
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

REC = os.path.join(ROOT, "fixtures", "xbrl", "default_p26_2026-10-23.json")
DOC = os.path.join(ROOT, "docs", "XBRL_DEFAULT_P26_RESULT_2026-10-23.md")
SEAL_REL = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"
SEAL = os.path.join(ROOT, SEAL_REL)
SEAL_COMMIT = "6a78b42"
SCRIPT = os.path.join(ROOT, "measure", "xbrl_default_p26_2026-10-23.py")
P26_REC = os.path.join(ROOT, "fixtures", "xbrl", "p26_2026-10-21.json")
FRESH_REC = os.path.join(ROOT, "fixtures", "xbrl", "fresh", "fresh_2026-10-21.json")
FETCHED = os.path.join(ROOT, "fixtures", "xbrl", "fresh", "fetched_2026-10-21.json")
RITUAL_REC = os.path.join(ROOT, "fixtures", "xbrl", "ritual_2026-10-20.json")
RITUAL_P22 = os.path.join(ROOT, "fixtures", "xbrl", "ritual_2026-10-20_p22.json")
SUITE_REC = os.path.join(ROOT, "fixtures", "suite_coverage_2026-10-16.json")
FACTS_DOC = os.path.join(ROOT, "docs", "FACTS_FOR_BUYERS_2026-10-20.md")
EXISTING_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
FRESH_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-fresh-2026-10-21")
RUN_HEAVY = os.environ.get("AUDIT_CORE_DEFAULT_P26") == "1"
LIGHT_DOCS = (("S100YMFV", False), ("S100YXFQ", True))        # 手元の 67 から 1・新しい標本の 30 から 1
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
README_REL = ("README.md", "README.en.md")
FACTS_REL = "docs/FACTS_FOR_BUYERS_2026-10-20.md"
STEP_NAMES = (u"S-1", u"S-2", u"S-3", u"S-4", u"S-5", u"S-6", u"S-7", u"S-8", u"S-9", u"S-10", u"S-11", u"S-12")

#: **字で留める**(測った事実。定数から作らない)。変えたら記録も文書も作り直す。
EXPECT = {
    "vocab_sha16": "e28733067b1f17f5",                  # 段 2 の後の vocabulary.py(封の commit 時点は 83025e9c0525d08b)
    "docs": (67, 30), "claims": (7799, 3923),
    "states_default_67": (4371, 433, 1579, 1416), "states_p22_67": (4242, 1410, 1323, 824),
    "states_default_30": (2194, 250, 774, 705), "states_p22_30": (2142, 677, 690, 414),
    "moved_30": 507,
    "ritual": (u"2 / 243 = 0.8%", u"210 / 243 = 86.4%", 31),
    "report": (433, 1775, 151, 1069, 4371),
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


_D = u"零一二三四五六七八九"


def kan(n):
    u"""整数(0〜九万九千九百九十九)を漢数字で。"""
    assert isinstance(n, int) and 0 <= n < 100000, n
    if n == 0:
        return u"零"
    out = u""
    for unit, base in ((10000, u"万"), (1000, u"千"), (100, u"百"), (10, u"十")):
        q, n = divmod(n, unit)
        if q:
            out += (u"" if (q == 1 and unit != 10000) else _D[q]) + base
    if n:
        out += _D[n]
    return out


def load_module(rel, name):
    if name not in MODULES:
        spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        MODULES[name] = m
    return MODULES[name]


# ----------------------------------------------------------------------------------------------------------------
# 封の字から幅を読む(太字の並び)
def seal_bounds(seal):
    b = {}
    for l in seal.splitlines():
        m = re.match(r"\| \*\*S-(\d+)\*\* \|", l)
        if m:
            cells = [c.strip() for c in l.strip().strip(u"|").split(u"|")]
            b[u"S-" + m.group(1)] = (re.findall(r"\*\*([^*]+)\*\*", cells[1]), cells[1], cells[2])
    assert sorted(b, key=lambda k: int(k[2:])) == list(STEP_NAMES), sorted(b)
    return b


def num(s):
    return int(s.replace(u",", u""))


def rng(s):
    a, b = s.split(u"〜")
    return int(a), int(b)


S3_DIRS = (u"VALUE_MISMATCH → POINTER_NOT_FOUND", u"VALUE_MISMATCH → UNVERIFIABLE", u"UNVERIFIABLE → GROUNDED", u"POINTER_NOT_FOUND → GROUNDED",
           u"GROUNDED → VALUE_MISMATCH", u"UNVERIFIABLE → VALUE_MISMATCH", u"GROUNDED → UNVERIFIABLE", u"POINTER_NOT_FOUND → UNVERIFIABLE")


# ----------------------------------------------------------------------------------------------------------------
# 数え直し(記録の行から)
def population(rec, which):
    rows = [r for r in rec[u"S1"][u"書類別"] if r[u"標本"] == which]
    moved_key = u"S2" if which == u"手元の 67" else u"S3"
    moved = rec[moved_key][u"動いた行"]
    st = collections.Counter()
    st22 = collections.Counter()
    for r in rows:
        st.update(r[u"既定の state"])
        st22.update(r[u"P22 の state"])
    dirs = collections.Counter(u"%s → %s" % (m[u"P22"][u"state"], m[u"既定"][u"state"]) for m in moved)
    leave = [m for m in moved if m[u"P22"][u"state"] == "GROUNDED"]
    return {u"rows": rows, u"moved": moved, u"claims": sum(r[u"claims"] for r in rows),
            u"default": tuple(st.get(s, 0) for s in STATES), u"p22": tuple(st22.get(s, 0) for s in STATES), u"dirs": dirs,
            u"leave": len(leave), u"leave_vm": sum(1 for m in leave if m[u"既定"][u"state"] == "VALUE_MISMATCH"),
            u"new_g": sum(1 for m in moved if m[u"既定"][u"state"] == "GROUNDED"),
            u"not_same": sum(1 for r in rows if not r[u"既定と P26 明示が同じ byte"]),
            u"ctrl_differs": sum(1 for r in rows if not r[u"既定を P22 に戻した対照が既定と同じ byte"])}


def check_population(rec, which):
    p = population(rec, which)
    key = u"S2" if which == u"手元の 67" else u"S3"
    one = rec[u"S1"][which]
    s = rec[key]
    assert one[u"書類"] == len(p[u"rows"]) and one[u"claims"] == p[u"claims"], which
    assert one[u"既定と P26 明示で違った書類"] == p[u"not_same"], which
    assert one[u"対照(既定を実行中だけ P22 に戻す)で違った書類"] == p[u"ctrl_differs"], which
    assert one[u"既定の 4 state"] == dict(zip(STATES, p[u"default"])) and one[u"P22 の 4 state"] == dict(zip(STATES, p[u"p22"])), which
    assert s[u"既定の 4 state"] == one[u"既定の 4 state"] and s[u"P22 の 4 state"] == one[u"P22 の 4 state"], which
    assert sum(p[u"default"]) == sum(p[u"p22"]) == p[u"claims"], which
    assert s[u"既定と P22 で state の違う行"] == len(p[u"moved"]) and s[u"向き"] == dict(sorted(p[u"dirs"].items())), which
    assert (s[u"GROUNDED を離れる行"], s[u"GROUNDED を離れてうち VALUE_MISMATCH に移る行"], s[u"新しい GROUNDED"]) == (p[u"leave"], p[u"leave_vm"], p[u"new_g"]), which
    # 動いた行と書類ごとの state の整合: 既定の数 - P22 の数 = (終わりが s の動いた行) - (始まりが s の動いた行)
    by_doc = collections.defaultdict(list)
    for m in p[u"moved"]:
        by_doc[m[u"doc"]].append(m)
    assert len({(m[u"doc"], m[u"id"]) for m in p[u"moved"]}) == len(p[u"moved"]), u"動いた行に重複"
    for r in p[u"rows"]:
        ms = by_doc.get(r[u"doc"], [])
        for st in STATES:
            net = sum(1 for m in ms if m[u"既定"][u"state"] == st) - sum(1 for m in ms if m[u"P22"][u"state"] == st)
            assert r[u"既定の state"].get(st, 0) - r[u"P22 の state"].get(st, 0) == net, (r[u"doc"], st)
        for m in ms:
            assert m[u"P22"][u"state"] != m[u"既定"][u"state"], (m[u"doc"], m[u"id"])
        assert sum(r[u"既定の state"].values()) == sum(r[u"P22 の state"].values()) == r[u"claims"], r[u"doc"]
        assert set(r[u"profile の欄"]) == {u"既定", u"P26 明示", u"対照"}
        # 『同じ byte』と profile の欄の整合: P26 明示は P26、対照は P22 の経路(欄は P22)、同じ byte なら既定の欄も P26 で state も同じ
        assert r[u"profile の欄"][u"P26 明示"] == "P26" and r[u"profile の欄"][u"対照"] == "P22", r[u"doc"]
        if r[u"既定と P26 明示が同じ byte"]:
            assert r[u"profile の欄"][u"既定"] == "P26" and r[u"既定の state"] == r[u"P26 明示の state"], r[u"doc"]
        assert not r[u"既定を P22 に戻した対照が既定と同じ byte"], (r[u"doc"], u"対照(既定を実行中だけ P22 に戻す)が差を拾わなかった = 『差零』が自分の欠陥かもしれない")
    return p


def check_against_other_records(rec):
    u"""P26 を明示して測った記録の P26 の欄・claim ごとの state と、既定の測定が同じ。"""
    p26 = jload(P26_REC)
    q1 = p26[u"Q1"][u"集計"]
    p67 = population(rec, u"手元の 67")
    assert p67[u"default"] == (q1[u"GROUNDED の合計 P26"], q1[u"VALUE_MISMATCH の合計 P26"], q1[u"UNVERIFIABLE の合計 P26"], q1[u"POINTER_NOT_FOUND の合計 P26"]), u"67 の既定が P26 明示の記録と違う"
    assert p67[u"claims"] == q1[u"総 claim"] and len(p67[u"rows"]) == q1[u"書類数"]
    fresh = jload(FRESH_REC)
    p30 = population(rec, u"新しい標本 30")
    a = fresh[u"A"]
    assert p30[u"default"] == tuple(a["P26"][s][u"件"] for s in STATES), u"30 の既定が P26 明示の記録の欄と違う"
    assert p30[u"p22"] == tuple(a["P22"][s][u"件"] for s in STATES), u"30 の P22 が記録の欄と違う"
    # claim ごと: fresh の claims[doc][i].states = [P22, P23, P24, P25, P26]、reasons も
    want = {}
    for doc, rows in fresh[u"claims"].items():
        for r in rows:
            if r[u"states"][0] != r[u"states"][4]:
                want[(doc, r[u"id"])] = ({u"state": r[u"states"][0], u"reason": r[u"reasons"][0]}, {u"state": r[u"states"][4], u"reason": r[u"reasons"][4]})
    got = dict(((m[u"doc"], m[u"id"]), (m[u"P22"], m[u"既定"])) for m in p30[u"moved"])
    assert got == want, u"30 の動いた行が fresh の claim ごとの state(P22 の欄と P26 の欄)から別に求めた行と違う"
    for r in p30[u"rows"]:
        assert r[u"claims"] == len(fresh[u"claims"][r[u"doc"]]), r[u"doc"]
    # 報告形: 書類ごとに P26 明示の記録の Q7 と同じ
    q7 = dict((d[u"doc"], d) for d in p26[u"Q7"][u"書類別"])
    assert rec[u"S5"][u"書類別"] == [q7[d[u"doc"]] for d in rec[u"S5"][u"書類別"]], u"報告形の節が P26 明示の記録の書類ごとの欄と違う"
    # 穴 B・段 2 の材料
    s6 = rec[u"S6"]
    q3 = p26[u"Q3"]
    assert s6[u"穴 B"][u"記録(P26 の欄)の行"] == len(q3[u"穴 B"][u"行"]) == s6[u"穴 B"][u"注入"]
    assert s6[u"段 2"][u"記録(P26 の欄)の行"] == len(q3[u"段 2"][u"行"]) == s6[u"段 2"][u"行"]
    assert q3[u"穴 B"][u"集計"][u"P26 で通した(GROUNDED のまま)"][u"件"] == s6[u"穴 B"][u"既定で通した"][u"件"]
    # 儀式
    ritual = jload(RITUAL_REC)
    s4 = rec[u"S4"]
    assert (s4[u"通した"], s4[u"止めた"], s4[u"止めた でも 通した でもない結果"]) == (ritual[u"通した"], ritual[u"止めた"], ritual[u"止めた でも 通した でもない結果"])
    assert s4[u"素の書類の state の分布"] == ritual[u"素の書類"][u"state の分布"] and s4[u"素の書類 claim"] == ritual[u"素の書類"][u"claim"]
    assert s4[K_P22_PASS] == jload(RITUAL_P22)[u"通した"] and s4[u"P22 の記録の止めた"] == jload(RITUAL_P22)[u"止めた"]


def check_record(rec):
    u"""記録の集計を、行から数え直した値と突き合わせる。壊した記録で赤くなる。"""
    p67 = check_population(rec, u"手元の 67")
    p30 = check_population(rec, u"新しい標本 30")
    assert (len(p67[u"rows"]), len(p30[u"rows"])) == (67, 30) and len(rec[u"S1"][u"書類別"]) == 97
    assert len({r[u"doc"] for r in rec[u"S1"][u"書類別"]}) == 97
    s4 = rec[u"S4"]
    assert s4[u"profile"] == "P26" and rec[u"環境"][u"DEFAULT_PROFILE"] == "P26"
    assert s4[u"通した"][u"字"] == F(s4[u"通した"][u"件"], s4[u"通した"][u"分母"]) and s4[u"止めた"][u"字"] == F(s4[u"止めた"][u"件"], s4[u"止めた"][u"分母"])
    assert s4[u"通した"][u"件"] + s4[u"止めた"][u"件"] + sum(s4[u"止めた でも 通した でもない結果"].values()) == s4[u"通した"][u"分母"] == s4[u"注入の対象"]
    assert s4[u"採り直した儀式の記録(ritual_2026-10-20.json)と違う欄(所要秒・実行環境を除く)"] == []
    assert sum(s4[u"素の書類の state の分布"].values()) == s4[u"素の書類 claim"]
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
    assert h[u"P26 の記録の P26 の欄と違った行"] == 0 and h[u"違った行"] == []
    t = rec[u"S6"][u"段 2"]
    assert t[u"行"] == 192 and t[u"注入"] == 64 and t[u"全注入で Core 自身(既定)が GROUNDED"][u"分母"] == 64
    assert t[u"P26 の記録の P26 の欄と違った行"] == 0 and t[u"違った行"] == []
    s7 = rec[u"S7"]
    assert s7[u"core/"] == {u"差の行数": 0, u"status": u""}
    for f, v in s7.items():
        if f.startswith(u"adapters/") and isinstance(v, dict) and f != "adapters/xbrl/vocabulary.py":
            assert v == {u"挿入": 0, u"削除": 0}, f
    assert s7[u"vocabulary.py 以外で封の commit から動いた file"] == [] and s7[u"adapters/xbrl の file 数"] == 16
    check_against_other_records(rec)
    return p67, p30


def check_inputs(rec):
    inp = rec[u"入力"]
    p26 = jload(P26_REC)
    in67 = p26[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"]
    assert inp[u"手元の 67 書類の sha256"] == in67, u"67 書類の sha256 が P26 明示の記録の入力と違う"
    fetched = jload(FETCHED)
    in30 = dict((x["docID"], x["sha256"]) for x in fetched[u"取得した書類"] if x["docID"] in fetched[u"使う書類"])
    assert inp[u"新しい標本 30 書類の sha256"] == in30 and sorted(in30) == sorted(fetched[u"使う書類"]), u"30 書類の sha256 が取得の記録と違う"
    assert inp[u"手元の 67 が P26 の記録の入力と同じ"] is True and inp[u"新しい標本 30 が取得の記録の入力と同じ"] is True
    assert inp[u"既存の cache の件数(開始時)"] == inp[u"既存の cache の件数(終了時)"], u"測定の間に既存の cache の件数が変わった"
    assert inp[u"新しい標本の folder の件数(開始時)"] == inp[u"新しい標本の folder の件数(終了時)"], u"測定の間に新しい標本の folder の件数が変わった"
    assert [r[u"zip の sha256"] for r in rec[u"S1"][u"書類別"]] == [in67[r[u"doc"]] if r[u"標本"] == u"手元の 67" else in30[r[u"doc"]] for r in rec[u"S1"][u"書類別"]]
    env = rec[u"環境"]
    assert env[u"費用"] == u"0 USD" and env[u"DEFAULT_PROFILE"] == "P26" and env[u"vocabulary.py の sha16"] == EXPECT["vocab_sha16"]
    assert env[u"比べた profile"] == [u"省略(None = vocabulary.DEFAULT_PROFILE)", u"P26(明示)", u"P22(既定を実行中だけ P22 に戻した対照)"]
    assert env[u"ラベル 2 file の sha256(起動時に照合)"] == jload(RITUAL_REC)[u"実行環境"][u"ラベル 2 file の sha256(起動時に照合)"]
    assert not any(v for k, v in env[u"鍵の名前の有無(値は読まない)"].items() if k != u"ANTHROPIC_BASE_URL"), u"鍵の名前が設定されている"


# ----------------------------------------------------------------------------------------------------------------
# 予測の判定(封の字の太字から幅を読み、記録の数から)
def judge(rec, bounds):
    J = {}
    p67, p30 = population(rec, u"手元の 67"), population(rec, u"新しい標本 30")
    b = bounds[u"S-1"][0]
    J[u"S-1"] = (p67[u"not_same"] == int(b[0].split(u" / ")[0]) and p30[u"not_same"] == int(b[1].split(u" / ")[0])
                 and p67[u"ctrl_differs"] + p30[u"ctrl_differs"] == int(b[2].split(u" / ")[0]) == len(rec[u"S1"][u"書類別"]))
    b = bounds[u"S-2"][0]
    lo, hi = rng(b[4])
    lo_v, hi_v = rng(b[5])
    lo_n, hi_n = rng(b[6])
    J[u"S-2"] = (p67[u"default"] == tuple(num(x) for x in b[:4]) and lo <= p67[u"leave"] <= hi and lo_v <= p67[u"leave_vm"] <= hi_v and lo_n <= p67[u"new_g"] <= hi_n)
    b = bounds[u"S-3"][0]
    J[u"S-3"] = (p30[u"default"] == tuple(num(x) for x in b[:4]) and len(p30[u"moved"]) == num(b[4])
                 and dict(p30[u"dirs"]) == dict((S3_DIRS[i], num(b[5 + i])) for i in range(8)))
    b = bounds[u"S-4"][0]
    s4 = rec[u"S4"]
    st = s4[u"素の書類の state の分布"]
    o = s4[u"止めた でも 通した でもない結果"]
    J[u"S-4"] = (s4[u"通した"][u"字"] == b[0] and s4[u"止めた"][u"字"] == b[1] and o == {"detected:POINTER_NOT_FOUND": num(b[2])}
                 and (st["GROUNDED"], st["POINTER_NOT_FOUND"], st["UNVERIFIABLE"], st["VALUE_MISMATCH"]) == tuple(num(x) for x in b[3:7])
                 and s4[u"採り直した儀式の記録(ritual_2026-10-20.json)と違う欄(所要秒・実行環境を除く)"] == [])
    b = bounds[u"S-5"][0]
    s5 = rec[u"S5"]
    J[u"S-5"] = [s5[u"違う"], s5[u"要確認"], s5[u"対象外"], s5[u"判断しない"], s5[u"一致"]] == [num(x) for x in b] and s5[u"違う"] == s5[u"VALUE_MISMATCH(state)の合計"]
    b = bounds[u"S-6"][0]
    s6 = rec[u"S6"]
    J[u"S-6"] = (s6[u"穴 B"][u"既定で通した"][u"件"] == int(b[0].split(u" / ")[0]) and s6[u"穴 B"][u"既定で止めた"] == num(b[1]) and s6[u"穴 B"][u"既定のその他"] == num(b[2])
                 and s6[u"段 2"][u"全注入で Core 自身(既定)が GROUNDED"][u"件"] == int(b[3].split(u" / ")[0])
                 and s6[u"穴 B"][u"P26 の記録の P26 の欄と違った行"] + s6[u"段 2"][u"P26 の記録の P26 の欄と違った行"] == num(b[4]))
    b = bounds[u"S-7"][0]
    voc = rec[u"S7"][u"adapters/xbrl/vocabulary.py"]
    J[u"S-7"] = (voc[u"挿入"] <= int(b[0].split(u"≤")[1]) and voc[u"削除"] == num(b[1]) and rec[u"S7"][u"core/"][u"差の行数"] == 0
                 and rec[u"S7"][u"vocabulary.py 以外で封の commit から動いた file"] == [])
    return J


def reds(rec):
    u"""S-8・S-9 の判定。試験の赤の表(人が書いた表。記録は入力の file の sha256 を持つ)の内訳の足し算と封の幅との当たり外れ。"""
    r = rec[u"試験の赤"]
    s8, s9 = r[u"S8"], r[u"S9"]
    assert s8[u"tests/measure"][u"赤"] == len(s8[u"tests/measure"][u"ids"]) and s8[u"tests/adapters/xbrl"][u"赤"] == len(s8[u"tests/adapters/xbrl"][u"ids"])
    assert s8[u"tests/measure"][u"file"] == len(set(i.split(u"::")[0] for i in s8[u"tests/measure"][u"ids"]))
    assert s8[u"tests/adapters/xbrl"][u"file"] == len(set(i.split(u"::")[0] for i in s8[u"tests/adapters/xbrl"][u"ids"]))
    kinds = collections.Counter(s8[u"種類"][i] for i in s8[u"tests/measure"][u"ids"] + s8[u"tests/adapters/xbrl"][u"ids"])
    assert set(kinds) <= {u"1", u"2", u"3", u"4"}, kinds
    assert sum(kinds.values()) == s8[u"tests/measure"][u"赤"] + s8[u"tests/adapters/xbrl"][u"赤"]
    assert s9[u"増えた赤"] == len(s9[u"増えた赤の id"])
    af = s9[u"実装の後"]
    runs = af[u"走らせ直し"]
    assert sum(v[u"赤"] for v in runs.values()) == af[u"赤"] == len(af[u"赤の id"]) == sum(len(v[u"赤の id"]) for v in runs.values())
    assert all(v[u"赤"] == len(v[u"赤の id"]) for v in runs.values())
    assert len(af[u"段 2 の前から赤"]) + len(af[u"段 2 が原因の赤"]) == af[u"赤"]
    assert set(af[u"段 2 の前から赤"]) <= set(af[u"何も変えない clone(6a78b42)で env を付けて走らせた赤"]), u"『段 2 の前から赤』は何も変えない clone で赤を確かめたものだけ"
    assert set(af[u"段 2 の前から赤"]) | set(af[u"段 2 が原因の赤"]) == set(af[u"赤の id"])
    for env, paths in af[u"出力の差"].items():
        assert env in runs and paths, env
        assert all(any(t in x for t in (u"DEFAULT_PROFILE", u"/HEAD", u"vocabulary.py", u"adapter_xbrl_py_sha256", u"engine の束ねた sha256")) for x in paths), (env, paths)
    assert set(s8[u"種類"]) == set(s8[u"tests/measure"][u"ids"] + s8[u"tests/adapters/xbrl"][u"ids"]), u"種類の表が赤の一覧と 1 対 1 でない"
    return {u"measure": s8[u"tests/measure"][u"赤"], u"measure_file": s8[u"tests/measure"][u"file"], u"adapters": s8[u"tests/adapters/xbrl"][u"赤"],
            u"others": s8[u"golden・fixtures・measure/tests の赤"], u"record_gate": s8[u"記録を書き換えないと緑にならない門"],
            u"human_gate": s8[u"人間の決定の字の門の赤"], u"kinds": dict(kinds), u"extra": s9[u"増えた赤"],
            u"seal_gate": sum(1 for i in s8[u"tests/measure"][u"ids"] if i.startswith(u"tests/measure/test_xbrl_default_p26_seal.py::")),
            u"core": s8[u"tests/core(段 2 と無関係で既に赤)"][u"赤"],
            u"cmp": dict((e, len(x)) for e, x in af[u"出力の差"].items()),
            u"after": af[u"赤"], u"after_pre": len(af[u"段 2 の前から赤"]), u"after_cause": len(af[u"段 2 が原因の赤"]), u"after_runs": len(runs), u"after_table": af}


def judge_reds(rec, bounds):
    R = reds(rec)
    b8 = bounds[u"S-8"][0]       # ['66 本', '24 file', '15 本', '78〜84', '0', '記録(fixtures)…門 0', '0']
    lo, hi = rng(b8[3])
    ok8 = (R[u"measure"] == int(b8[0].split(u" ")[0]) and R[u"measure_file"] == int(b8[1].split(u" ")[0]) and R[u"adapters"] == int(b8[2].split(u" ")[0])
           and lo <= R[u"measure"] + R[u"adapters"] <= hi and R[u"others"] == int(b8[4]) and R[u"record_gate"] == int(b8[5].rsplit(u" ", 1)[1])
           and R[u"human_gate"] == int(b8[6]) and set(R[u"kinds"]) <= {u"1", u"2", u"3", u"4"})
    # 封 S-9 の外れ条件は『増える赤が 6 でない / 実装の後に赤が残る』の 2 つ(太字の 6 と、実装の後の赤 0)
    ok9 = R[u"extra"] == int(bounds[u"S-9"][0][0].split(u" ")[0]) and R[u"after"] == 0
    return {u"S-8": ok8, u"S-9": ok9}


def judge_docs(rec, bounds):
    J = {}
    p10 = rec[u"S10"]
    J[u"S-10"] = (all(p10[r][u"節に 通した の字"] and p10[r][u"節に 止めた の字"] for r in README_REL) and p10[FACTS_REL][u"P22 の字の数"] == 0 and p10[FACTS_REL][u"P26 の字の数"] == 0)
    b = bounds[u"S-11"][0]
    J[u"S-11"] = rec[u"S11"][u"試験 file の数(ディスク上)"] == num(b[1]) and rec[u"S11"][u"覆われていない file"] == 0
    J[u"S-12"] = rec[u"S12"][u"既定"] == bounds[u"S-12"][0][0] and rec[u"S12"][u"候補の順"] == [u"P26", u"P25", u"P24"]
    return J


def judge_all(rec, bounds):
    J = {}
    J.update(judge(rec, bounds))
    J.update(judge_reds(rec, bounds))
    J.update(judge_docs(rec, bounds))
    assert sorted(J, key=lambda k: int(k[2:])) == list(STEP_NAMES)
    return J


def recorded_judgments(rec):
    j = rec[u"予測の判定"]
    return dict((k, v[u"当たり"]) for k, v in j.items())


# ----------------------------------------------------------------------------------------------------------------
# 文書の字(記録から作る)。散文の数は漢数字
def table(head, rows):
    L = [u"| " + u" | ".join(head) + u" |", u"|" + u"|".join(u"---" for _ in head) + u"|"]
    for r in rows:
        L.append(u"| " + u" | ".join(r) + u" |")
    return u"\n".join(L)


def cell(s):
    return (s if s is not None else u"").replace(u"|", u"｜").replace(u"\n", u" ")


def measured_cells(rec, bounds, J):
    u"""予測の行ごとの『実測』の字(記録から)。"""
    p67, p30 = population(rec, u"手元の 67"), population(rec, u"新しい標本 30")
    s4, s5, s6, s7 = rec[u"S4"], rec[u"S5"], rec[u"S6"], rec[u"S7"]
    R = reds(rec)
    voc = s7[u"adapters/xbrl/vocabulary.py"]
    M = {}
    M[u"S-1"] = u"違った書類 %d / 67・%d / 30。対照(既定を実行中だけ P22 に戻す)で違った書類 %d / 97" % (p67[u"not_same"], p30[u"not_same"], p67[u"ctrl_differs"] + p30[u"ctrl_differs"])
    M[u"S-2"] = u"GROUNDED %s・VALUE_MISMATCH %s・UNVERIFIABLE %s・POINTER_NOT_FOUND %s。GROUNDED を離れる行 %d(うち VALUE_MISMATCH %d)・新しい GROUNDED %d" % (
        tuple(comma(x) for x in p67[u"default"]) + (p67[u"leave"], p67[u"leave_vm"], p67[u"new_g"]))
    M[u"S-3"] = u"GROUNDED %s・VALUE_MISMATCH %s・UNVERIFIABLE %s・POINTER_NOT_FOUND %s。P22 と state の違う行 %d(%s)" % (
        tuple(comma(x) for x in p30[u"default"]) + (len(p30[u"moved"]), u"・".join(u"%s %d" % (d, p30[u"dirs"].get(d, 0)) for d in S3_DIRS)))
    M[u"S-4"] = u"通した %s・止めた %s・POINTER_NOT_FOUND %d。素の書類(claim %d)GROUNDED %d・POINTER_NOT_FOUND %d・UNVERIFIABLE %d・VALUE_MISMATCH %d。記録 `ritual_2026-10-20.json` と違う欄 %d" % (
        s4[u"通した"][u"字"], s4[u"止めた"][u"字"], sum(s4[u"止めた でも 通した でもない結果"].values()), s4[u"素の書類 claim"],
        s4[u"素の書類の state の分布"]["GROUNDED"], s4[u"素の書類の state の分布"]["POINTER_NOT_FOUND"], s4[u"素の書類の state の分布"]["UNVERIFIABLE"],
        s4[u"素の書類の state の分布"]["VALUE_MISMATCH"], len(s4[u"採り直した儀式の記録(ritual_2026-10-20.json)と違う欄(所要秒・実行環境を除く)"]))
    M[u"S-5"] = u"違う %s・要確認 %s・対象外 %s・判断しない %s・一致 %s(合計 %s)。「違う」の節と VALUE_MISMATCH の差 %d" % (
        comma(s5[u"違う"]), comma(s5[u"要確認"]), comma(s5[u"対象外"]), comma(s5[u"判断しない"]), comma(s5[u"一致"]), comma(s5[u"節の合計"]), s5[u"違う"] - s5[u"VALUE_MISMATCH(state)の合計"])
    M[u"S-6"] = u"穴 B で通した %s・止めた %d・その他 %d(P22 明示の対照は通した %s)。段 2 の材料で Core 自身が GROUNDED %s。P26 の記録の P26 の欄と違う行 %d" % (
        F(s6[u"穴 B"][u"既定で通した"][u"件"], 485), s6[u"穴 B"][u"既定で止めた"], s6[u"穴 B"][u"既定のその他"], F(s6[u"穴 B"][u"P22 明示(対照)で通した"][u"件"], 485),
        F(s6[u"段 2"][u"全注入で Core 自身(既定)が GROUNDED"][u"件"], 64), s6[u"穴 B"][u"P26 の記録の P26 の欄と違った行"] + s6[u"段 2"][u"P26 の記録の P26 の欄と違った行"])
    M[u"S-7"] = u"`vocabulary.py` 挿入 %d・削除 %d。`core/` %d 行。ほかの engine の file で動いたもの %d" % (
        voc[u"挿入"], voc[u"削除"], s7[u"core/"][u"差の行数"], len(s7[u"vocabulary.py 以外で封の commit から動いた file"]))
    M[u"S-8"] = u"`tests/measure` の赤 %d 本(%d file)・`tests/adapters/xbrl` の赤 %d 本。合計 %d。`golden`・`fixtures`・`measure/tests` の赤 %d。記録を書き換えないと緑にならない門 %d。人間の決定の字の門の赤 %d。種類 %s" % (
        R[u"measure"], R[u"measure_file"], R[u"adapters"], R[u"measure"] + R[u"adapters"], R[u"others"], R[u"record_gate"], R[u"human_gate"],
        u"・".join(u"%s が %d 本" % (k, v) for k, v in sorted(R[u"kinds"].items())))
    M[u"S-9"] = u"軽い門の赤のほかに増えた赤 %d 本" % R[u"extra"]
    p10 = rec[u"S10"]
    M[u"S-10"] = u"README の儀式の節に 通した・止めた の字が在る: %s。`FACTS_FOR_BUYERS` の P22 の字 %d・P26 の字 %d" % (
        u"・".join(u"%s %s" % (r, u"在る" if p10[r][u"節に 通した の字"] and p10[r][u"節に 止めた の字"] else u"無い") for r in README_REL),
        p10[FACTS_REL][u"P22 の字の数"], p10[FACTS_REL][u"P26 の字の数"])
    M[u"S-11"] = u"試験 file %d 本(ディスク上)。覆われていない file %d" % (rec[u"S11"][u"試験 file の数(ディスク上)"], rec[u"S11"][u"覆われていない file"])
    M[u"S-12"] = u"記録の判定: 既定 %s・候補の順 %s" % (rec[u"S12"][u"既定"], u"→".join(rec[u"S12"][u"候補の順"]))
    return M


K_P22_PASS = u"P22 の記録(ritual_2026-10-20_p22.json)の通した"


def render_blocks(rec, bounds):
    J = judge_all(rec, bounds)
    M = measured_cells(rec, bounds, J)
    p67, p30 = population(rec, u"手元の 67"), population(rec, u"新しい標本 30")
    B = {}
    B["pred"] = table([u"#", u"予測(封の字)", u"実測", u"当たり外れ"],
                      [[u"**%s**" % k, cell(bounds[k][1]), cell(M[k]), u"**当たり**" if J[k] else u"**外れ**"] for k in STEP_NAMES])
    B["s1"] = table([u"標本", u"書類", u"claim", u"既定と P26 明示で違った書類", u"既定を実行中だけ P22 に戻した対照で違った書類"],
                    [[w, str(len(p[u"rows"])), comma(p[u"claims"]), str(p[u"not_same"]), str(p[u"ctrl_differs"])] for w, p in ((u"手元の 67", p67), (u"新しい標本 30", p30))])
    B["s2"] = table([u"標本", u"profile", u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND"],
                    [[w, name] + [F(v, p[u"claims"]) for v in vals] for w, p in ((u"手元の 67", p67), (u"新しい標本 30", p30))
                     for name, vals in ((u"P22", p[u"p22"]), (u"既定(P26)", p[u"default"]))])
    B["s3"] = table([u"標本", u"向き(P22 → 既定)", u"行"],
                    [[w, d, str(p[u"dirs"][d])] for w, p in ((u"手元の 67", p67), (u"新しい標本 30", p30)) for d in sorted(p[u"dirs"])])
    s4 = rec[u"S4"]
    B["s4"] = table([u"儀式(同梱の 1 書類)", u"通した", u"止めた(VALUE_MISMATCH)", u"止めた(POINTER_NOT_FOUND)", u"注入の対象"],
                    [[u"P22(`ritual_2026-10-20_p22.json`)", s4[K_P22_PASS][u"字"], s4[u"P22 の記録の止めた"][u"字"], u"0", str(s4[K_P22_PASS][u"分母"])],
                     [u"既定(P26。`ritual_2026-10-20.json`)", s4[u"通した"][u"字"], s4[u"止めた"][u"字"], str(sum(s4[u"止めた でも 通した でもない結果"].values())), str(s4[u"注入の対象"])]])
    s5 = rec[u"S5"]
    B["s5"] = table([u"報告形の節(67 書類)", u"件"], [[k, comma(s5[k])] for k in (u"違う", u"要確認", u"対象外", u"判断しない", u"一致")] + [[u"合計", comma(s5[u"節の合計"])]])
    s6 = rec[u"S6"]
    B["s6"] = table([u"誤りを通す側", u"既定", u"P22 明示(対照)"],
                    [[u"穴 B の注入 485 件で通した", F(s6[u"穴 B"][u"既定で通した"][u"件"], 485), F(s6[u"穴 B"][u"P22 明示(対照)で通した"][u"件"], 485)],
                     [u"穴 B の注入で止めた(VALUE_MISMATCH)", str(s6[u"穴 B"][u"既定で止めた"]), str(s6[u"穴 B"][u"P22 明示(対照)で止めた"])],
                     [u"段 2 の材料の注入 64 件で Core 自身が GROUNDED", F(s6[u"段 2"][u"全注入で Core 自身(既定)が GROUNDED"][u"件"], 64), u"(測っていない)"]])
    R = reds(rec)
    B["reds"] = table([u"試作の clone(`DEFAULT_PROFILE` の 1 行だけ P26)の赤", u"本", u"file"],
                      [[u"`tests/measure`", str(R[u"measure"]), str(R[u"measure_file"])], [u"`tests/adapters/xbrl`", str(R[u"adapters"]), str(len(set(i.split(u"::")[0] for i in rec[u"試験の赤"][u"S8"][u"tests/adapters/xbrl"][u"ids"])))]]
                      + [[u"種類 %s" % k, str(v), u""] for k, v in sorted(R[u"kinds"].items())])
    af = R[u"after_table"][u"走らせ直し"]
    B["after"] = table([u"実装の後の重い走らせ直し(環境変数)", u"赤", u"うち段 2 の前から赤"],
                       [[u"`%s`" % env, str(v[u"赤"]), str(len(v[u"段 2 の前から赤"]))] for env, v in sorted(af.items())])
    return B


def prose_facts(rec, bounds):
    J = judge_all(rec, bounds)
    p67, p30 = population(rec, u"手元の 67"), population(rec, u"新しい標本 30")
    P = {}
    hit = sum(1 for v in J.values() if v)
    P["head"] = u"予測 S-1〜S-12 の機械判定: 当たり %s・外れ %s。" % (kan(hit), kan(len(J) - hit))
    P["miss"] = u"外れた予測: %s。" % (u"・".join(k for k in STEP_NAMES if not J[k]) or u"なし")
    P["s1"] = u"profile を省いた経路と P26 を明示した経路の出力は、手元の六十七書類で %s書類、新しい標本の三十書類で %s書類が違った(違った書類の数。零なら 1 byte も違わない)。" % (
        kan(p67[u"not_same"]), kan(p30[u"not_same"]))
    P["ctrl"] = u"対照(既定を実行中だけ P22 に戻す)では、九十七書類のうち %s書類が違った。『差零』は自分の欠陥ではない。" % kan(p67[u"ctrl_differs"] + p30[u"ctrl_differs"])
    P["n"] = u"測った書類は手元の %s・新しい標本の %s、claim は %s と %s。" % (kan(len(p67[u"rows"])), kan(len(p30[u"rows"])), kan(p67[u"claims"]), kan(p30[u"claims"]))
    P["moved"] = u"既定(P26)と P22 で state の違う行は、手元の六十七書類で %s・新しい標本の三十書類で %s。" % (kan(len(p67[u"moved"])), kan(len(p30[u"moved"])))
    P["leave"] = u"手元の六十七書類で P22 の GROUNDED を離れる行は %s(うち VALUE_MISMATCH に移る行 %s)、新しい GROUNDED になる行は %s。" % (
        kan(p67[u"leave"]), kan(p67[u"leave_vm"]), kan(p67[u"new_g"]))
    s6 = rec[u"S6"]
    P["pass"] = u"誤りを通す側は、穴 B の注入四百八十五件で既定が通した数が %s・段 2 の材料の注入六十四件で Core 自身が GROUNDED にした数が %s。" % (
        kan(s6[u"穴 B"][u"既定で通した"][u"件"]), kan(s6[u"段 2"][u"全注入で Core 自身(既定)が GROUNDED"][u"件"]))
    s7 = rec[u"S7"][u"adapters/xbrl/vocabulary.py"]
    P["engine"] = u"engine の差分は `vocabulary.py` の挿入 %s 行・削除 %s 行だけ。" % (kan(s7[u"挿入"]), kan(s7[u"削除"]))
    R = reds(rec)
    P["reds"] = u"既定の一行だけを替えた clone の赤は、`tests/measure` が %s本(%s file)・`tests/adapters/xbrl` が %s本。" % (kan(R[u"measure"]), kan(R[u"measure_file"]), kan(R[u"adapters"]))
    b8 = bounds[u"S-8"][0]
    P["why"] = (u"封の予測は `tests/measure` が %s本(%s file)・`tests/adapters/xbrl` が %s本。実測との差のうち、封の commit で足された `test_xbrl_default_p26_seal.py` の赤は %s本"
                u"(封の試作の clone にはこの file が無かった)。`tests/core` の赤は %s本。" % (
                    kan(int(b8[0].split(u" ")[0])), kan(int(b8[1].split(u" ")[0])), kan(int(b8[2].split(u" ")[0])), kan(R[u"seal_gate"]), kan(R[u"core"])))
    P["after"] = (u"実装の後の重い走らせ直し %s本の赤は %s本。うち、何も変えない clone(`6a78b42`)で同じ環境変数を付けて走らせても赤だった(段 2 の前から赤)が %s本、段 2 が原因の赤は %s本。封の S-9 の『実装の後は全部緑』は%s。"
                  % (kan(R[u"after_runs"]), kan(R[u"after"]), kan(R[u"after_pre"]), kan(R[u"after_cause"]), u"当たり" if R[u"after"] == 0 else u"外れ"))
    P["cmp"] = (u"何も変えない clone と段 2 の clone で、報告形の走らせ直しの出力は %s欄・報告形の直しの出力は %s欄・期の縛りの段 2 の出力は %s欄だけ違った。違った欄はどれも既定・HEAD・`vocabulary.py` の sha・束ねた指紋の欄だけで、測った値の欄は一字も違わない。"
                % (kan(R[u"cmp"][u"AUDIT_CORE_CUSTOMER_REPORT"]), kan(R[u"cmp"][u"AUDIT_CORE_CUSTOMER_REPORT_FIX"]), kan(R[u"cmp"][u"AUDIT_CORE_PERIOD_BIND"])))
    P["extra"] = u"重い走らせ直しで軽い門の赤のほかに増えた赤は %s本。" % kan(R[u"extra"])
    P["suite"] = u"試験 file はディスク上で %s本。" % kan(rec[u"S11"][u"試験 file の数(ディスク上)"])
    return P


#: 散文に残ってよい数字の並び(記録に縛られない構造上の字)。空にできるよう、散文は漢数字で書く。
ALLOWED_RESIDUAL = []


def residual_numbers(doc, rec, bounds):
    t = doc
    pieces = list(render_blocks(rec, bounds).values()) + list(prose_facts(rec, bounds).values())
    for v in sorted(pieces, key=len, reverse=True):
        t = t.replace(v, u"")
    t = re.sub(r"```.*?```", u"", t, flags=re.S)
    t = re.sub(r"`[^`]*`", u"", t)
    t = re.sub(r"[A-Za-z_][A-Za-z_0-9\-]*\d[A-Za-z_0-9\-]*", u"", t)      # S100YMFV・N076・K-1・P26・S-8・sha16 など
    t = re.sub(r"(?m)^#+ [\d\-\.]+", u"", t)
    t = re.sub(r"段 \d", u"", t)
    t = t.replace(u"0 USD", u"")
    t = re.sub(r"§[\d\-]+", u"", t)
    t = re.sub(r"\d{4}-\d{2}-\d{2}", u"", t)
    return re.findall(r"\d[\d,\.]*", t)


def check_doc(rec, doc, bounds):
    B = render_blocks(rec, bounds)
    for k, v in B.items():
        assert v in doc, u"文書に『%s』の表(記録から作った字)が無い" % k
    for k, v in prose_facts(rec, bounds).items():
        assert v in doc, u"文書に数のある文『%s』(記録から作った字)が無い" % k
    for lit in (u"読みはエージェントの読みで人間の読みではない", u"判定は覆さない", u"試作の clone の実測", u"S-8", u"S-9", u"verify_document.py", u"HUMAN"):
        assert lit in doc, lit
    assert doc.count(u"## ") >= 5
    res = residual_numbers(doc, rec, bounds)
    assert res == ALLOWED_RESIDUAL, u"文書の散文に、記録に縛られない数が在る: %s" % res
    # 文書の当たり外れは記録の判定と同じ
    J = judge_all(rec, bounds)
    assert recorded_judgments(rec) == dict((k, J[k]) for k in recorded_judgments(rec)), u"記録の予測の判定が門の判定と違う"


# ----------------------------------------------------------------------------------------------------------------
def engine_ok():
    u"""いまの engine: vocabulary.py は段 2 の後の値(封の commit 時点の値でも、字で留めた段 2 の後の値でもなければ赤)、ほかの adapters の file は封の commit のまま。"""
    from adapters.xbrl import vocabulary as V
    assert sha16("adapters/xbrl/vocabulary.py") == EXPECT["vocab_sha16"], u"vocabulary.py が段 2 の後の値と違う"
    assert V.DEFAULT_PROFILE == "P26", V.DEFAULT_PROFILE
    for rel in sorted(f for f in os.listdir(os.path.join(ROOT, "adapters", "xbrl")) if f.endswith(".py")):
        r = git("diff", SEAL_COMMIT, "--numstat", "--", "adapters/xbrl/" + rel)
        if rel != "vocabulary.py":
            assert r.stdout.strip() == u"", u"vocabulary.py 以外の engine の file が封の commit から動いている: " + rel
    r = git("diff", SEAL_COMMIT, "--numstat", "--", "adapters/xbrl/vocabulary.py")
    assert r.stdout.split()[:2] == ["4", "1"], r.stdout
    assert git("diff", SEAL_COMMIT, "--numstat", "--", "core").stdout.strip() == u""
    assert git("status", "--porcelain", "--", "core").stdout.strip() == u""


def have_cache(docs):
    return all(os.path.exists(os.path.join(FRESH_DIR if fresh else EXISTING_CACHE, d + ".zip")) for d, fresh in docs)


def labels_ok():
    try:
        from adapters.xbrl import instance as I
        for _ns, fn, _sha in I.TAXONOMY_LABEL_FILES:
            if not os.path.exists(os.path.join(I.taxonomy_dir(), fn)):
                return False
        return True
    except Exception:
        return False


class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)
        cls.bounds = seal_bounds(cls.seal)

    def test_1_record_is_consistent(self):
        check_record(self.rec)

    def test_2_inputs_are_pinned(self):
        check_inputs(self.rec)

    def test_3_document_tables_equal_the_record(self):
        check_doc(self.rec, self.doc, self.bounds)

    def test_4_facts_as_measured(self):
        u"""この実行の事実を字で留める(行から数えた値。変えたら記録も文書も作り直す)。"""
        p67, p30 = population(self.rec, u"手元の 67"), population(self.rec, u"新しい標本 30")
        self.assertEqual((len(p67[u"rows"]), len(p30[u"rows"])), EXPECT["docs"])
        self.assertEqual((p67[u"claims"], p30[u"claims"]), EXPECT["claims"])
        self.assertEqual(p67[u"default"], EXPECT["states_default_67"])
        self.assertEqual(p67[u"p22"], EXPECT["states_p22_67"])
        self.assertEqual(p30[u"default"], EXPECT["states_default_30"])
        self.assertEqual(p30[u"p22"], EXPECT["states_p22_30"])
        self.assertEqual(len(p30[u"moved"]), EXPECT["moved_30"])
        self.assertEqual((p67[u"not_same"], p30[u"not_same"]), (0, 0))
        self.assertEqual((p67[u"ctrl_differs"], p30[u"ctrl_differs"]), (67, 30))
        s4 = self.rec[u"S4"]
        self.assertEqual((s4[u"通した"][u"字"], s4[u"止めた"][u"字"], sum(s4[u"止めた でも 通した でもない結果"].values())), EXPECT["ritual"])
        s5 = self.rec[u"S5"]
        self.assertEqual((s5[u"違う"], s5[u"要確認"], s5[u"対象外"], s5[u"判断しない"], s5[u"一致"]), EXPECT["report"])
        h = self.rec[u"S6"][u"穴 B"]
        self.assertEqual((h[u"既定で通した"][u"件"], h[u"注入"], h[u"既定で止めた"], h[u"既定のその他"]), EXPECT["hole_b"])
        t = self.rec[u"S6"][u"段 2"]
        self.assertEqual((t[u"全注入で Core 自身(既定)が GROUNDED"][u"件"], t[u"注入"]), EXPECT["step2_injected"])

    def test_5_engine_is_the_declared_after_value_and_the_default_is_p26(self):
        engine_ok()
        voc = self.rec[u"S7"][u"adapters/xbrl/vocabulary.py"]
        self.assertEqual((voc[u"挿入"], voc[u"削除"]), (4, 1))

    def test_6_judgments_equal_the_document_table_and_the_seal_rows_are_not_edited(self):
        J = judge_all(self.rec, self.bounds)
        self.assertEqual(recorded_judgments(self.rec), dict((k, J[k]) for k in recorded_judgments(self.rec)))
        for k in STEP_NAMES:
            row = [l for l in self.doc.splitlines() if l.startswith(u"| **%s** |" % k)]
            self.assertEqual(len(row), 1, k)
            cells = [c.strip() for c in row[0].strip().strip(u"|").split(u"|")]
            self.assertEqual(len(cells), 4, k)
            self.assertEqual(cells[1], cell(self.bounds[k][1]), u"%s の予測欄が封の字と違う" % k)
            self.assertEqual(cells[3], u"**当たり**" if J[k] else u"**外れ**", k)
        # 封は封の commit から 1 字も直していない(数を見てから封を直さない)
        self.assertEqual(git("diff", "--numstat", SEAL_COMMIT, "--", SEAL_REL).stdout, "")
        self.assertEqual(git("status", "--porcelain", "--", SEAL_REL).stdout, "")

    def test_7_s12_is_recomputed_by_another_function(self):
        u"""S-12: 判定を ``test_xbrl_fresh_result.py`` の judge(K-1・K-2・K-3 を候補ごとに数える別の関数)で求め直しても P26(順は P26 → P25 → P24)。"""
        fr = load_module("tests/measure/test_xbrl_fresh_result.py", "fresh_result_for_default_p26")
        rec = fr.jload(FRESH_REC)
        params = fr.seal_params(fr.jtext(fr.SEAL))
        j = fr.judge(rec, params)
        self.assertEqual((j[u"既定"], j[u"順"]), ("P26", ["P26", "P25", "P24"]))
        self.assertEqual((j[u"既定"], j[u"順"]), (self.rec[u"S12"][u"既定"], self.rec[u"S12"][u"候補の順"]))

    def test_8_readme_facts_and_suite_count_are_live(self):
        u"""S-10・S-11 を記録でなく**いまの木**から。README の節は記録から作った字と 1 対 1(儀式の門が全文を縛る)。ここは記録の欄と木の一致。(2026-10-27 追記: 試験 file の数の比べは、いまのディスクでなく段 2 の commit 917157c の木と。いまの木の数は覆いの記録だけが縛る。)"""
        ritual = jload(RITUAL_REC)
        for rel, head in (("README.md", u"## 10 分の再現"), ("README.en.md", u"## 10-minute reproduction")):
            t = jtext(os.path.join(ROOT, rel))
            i = t.index(u"\n" + head) + 1
            j = t.find(u"\n## ", i + 1)
            sec = t[i:j + 1] if j >= 0 else t[i:]
            self.assertIn(ritual[u"通した"][u"字"], sec, rel)
            self.assertIn(ritual[u"止めた"][u"字"], sec, rel)
            self.assertNotIn(jload(RITUAL_P22)[u"通した"][u"字"].split(u" = ")[0] + u" = ", sec, rel + u": P22 の字が節の先頭の数に残っている")
        facts = jtext(FACTS_DOC)
        self.assertEqual((facts.count(u"P22"), facts.count(u"P26")), (0, 0))
        n = 0
        for base, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__", ".pytest_cache")]
            n += sum(1 for f in files if f.startswith("test_") and f.endswith(".py"))
        ls = subprocess.run(["git", "ls-tree", "-r", "--name-only", "917157c"], cwd=ROOT, capture_output=True, text=True)
        if ls.returncode == 0:
            n_stage2 = sum(1 for path in ls.stdout.splitlines()
                           if os.path.basename(path).startswith("test_") and path.endswith(".py")
                           and not any(x in path for x in (".git", "node_modules", "__pycache__", ".pytest_cache")))
            self.assertEqual(n_stage2, self.rec[u"S11"][u"試験 file の数(ディスク上)"], u"段 2 の commit 917157c の木の試験 file の数が記録と違う")
        else:
            print(u"SKIP: git ls-tree 917157c が失敗(履歴の無い写し)。段 2 の試験 file の数と記録の比べを省く")
        suite = jload(SUITE_REC)
        self.assertEqual(suite["test_files_on_disk"], n, u"覆いの記録が古い(`measure/suite_coverage_2026-10-16.py --write`)")
        self.assertEqual(suite["uncovered_files"], [])

    def test_9_p22_ritual_copy_is_the_byte_identical_record_in_history(self):
        sha = sha_path(RITUAL_P22)
        self.assertEqual(sha, "c89824f71e8002421fd27eb98044884ef94b2adb047c9fab0235a489d69f0249")
        r = subprocess.run(["git", "show", "d0b544c:./fixtures/xbrl/ritual_2026-10-20.json"], cwd=ROOT, capture_output=True)
        if r.returncode == 0:
            self.assertEqual(hashlib.sha256(r.stdout).hexdigest(), sha)
        self.assertNotEqual(sha_path(RITUAL_REC), sha, u"ritual_2026-10-20.json が P22 の記録のまま(採り直していない)")

    def test_10_order_in_git_the_seal_comes_before_the_stage_2_files(self):
        base = git("log", "--diff-filter=A", "--format=%H", "--", SEAL_REL).stdout.split()
        self.assertTrue(base, u"封が履歴に無い")
        seal = base[-1]
        self.assertTrue(seal.startswith(SEAL_COMMIT))
        for rel in ("measure/xbrl_default_p26_2026-10-23.py", "fixtures/xbrl/default_p26_2026-10-23.json", "docs/XBRL_DEFAULT_P26_RESULT_2026-10-23.md",
                    "tests/measure/test_xbrl_default_p26_result.py", "fixtures/xbrl/ritual_2026-10-20_p22.json"):
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
        for x in got[u"S1"][u"書類別"]:
            self.assertEqual(x, want[x[u"doc"]], x[u"doc"])
        wm = [m for key in (u"S2", u"S3") for m in self.rec[key][u"動いた行"] if m[u"doc"] in want]
        gm = [m for key in (u"S2", u"S3") for m in got[key][u"動いた行"]]
        self.assertEqual(json.dumps(gm, sort_keys=True), json.dumps(wm, sort_keys=True))

    def test_light_the_script_stops_when_the_default_is_not_p26(self):
        u"""既定が P26 でないと測定は止まる(『既定を測る』script が既定でない経路を測らない)。コピーした script を P22 の既定の vocabulary で走らせる代わりに、字の守りを見る。"""
        src = jtext(SCRIPT)
        self.assertIn(u'if V.DEFAULT_PROFILE != NEW:', src)
        self.assertEqual(src.count(u'OLD, NEW = "P22", "P26"'), 1)

    @unittest.skipUnless(RUN_HEAVY, u"AUDIT_CORE_DEFAULT_P26=1 のときだけ走る(97 書類 + 注入 + 報告形の走らせ直し。約 十五分)")
    def test_heavy_everything_matches_the_record(self):
        tmp = tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None)
        out = os.path.join(tmp, "all.json")
        r = run_script(["--stage", "all", "--out", out, "--jobs", "3"])
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        got, want = jload(out), copy.deepcopy(self.rec)
        for part in (got, want):
            part.pop(u"所要秒", None)
            part[u"環境"].pop(u"HEAD", None)
            for k in (u"S10", u"S11", u"S12", u"試験の赤", u"予測の判定", u"limits"):
                part.pop(k, None)
            part[u"S7"].pop(u"adapters/xbrl の file 数", None)
            part[u"入力"].pop(u"試験の赤の入力 file の sha256", None)      # 試験の赤の表は人が書いた入力で、走らせ直しでは測らない
        self.assertEqual(json.dumps(got, sort_keys=True), json.dumps(want, sort_keys=True))


# ----------------------------------------------------------------------------------------------------------------
# 門自身の変異(壊した標本で赤くなること)
class MutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec0 = jload(REC)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)
        cls.bounds = seal_bounds(cls.seal)

    def _mut(self):
        return copy.deepcopy(self.rec0)

    def _red(self, fn, *a):
        with self.assertRaises((AssertionError, KeyError, IndexError, TypeError, ValueError, ZeroDivisionError)):
            fn(*a)

    def test_baseline_is_green(self):
        check_record(self._mut())
        check_inputs(self._mut())
        check_doc(self._mut(), self.doc, self.bounds)
        engine_ok()

    def test_m1_a_row_that_differs_in_byte_is_red(self):
        r = self._mut()
        r[u"S1"][u"書類別"][0][u"既定と P26 明示が同じ byte"] = False
        self._red(check_record, r)
        r = self._mut()
        r[u"S1"][u"書類別"][0][u"既定を P22 に戻した対照が既定と同じ byte"] = True        # 対照が差を拾わなかった
        self._red(check_record, r)

    def test_m2_a_changed_state_count_is_red(self):
        r = self._mut()
        r[u"S1"][u"書類別"][0][u"既定の state"]["GROUNDED"] += 1
        self._red(check_record, r)
        r = self._mut()
        r[u"S2"][u"既定の 4 state"]["GROUNDED"] += 1
        self._red(check_record, r)

    def test_m3_a_dropped_or_changed_moved_row_is_red(self):
        r = self._mut()
        r[u"S3"][u"動いた行"].pop()
        self._red(check_record, r)
        r = self._mut()
        r[u"S3"][u"動いた行"][0][u"既定"][u"state"] = "GROUNDED" if r[u"S3"][u"動いた行"][0][u"既定"][u"state"] != "GROUNDED" else "VALUE_MISMATCH"
        self._red(check_record, r)
        r = self._mut()
        r[u"S2"][u"動いた行"].pop()
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

    def test_m6_engine_diff_or_core_diff_is_red(self):
        r = self._mut()
        r[u"S7"][u"core/"][u"差の行数"] = 1
        self._red(check_record, r)
        r = self._mut()
        r[u"S7"][u"adapters/xbrl/recipes.py"][u"挿入"] = 1
        self._red(check_record, r)
        r = self._mut()
        r[u"S7"][u"vocabulary.py 以外で封の commit から動いた file"] = [u"recipes.py"]
        self._red(check_record, r)

    def test_m7_a_spoiled_input_digest_is_red(self):
        r = self._mut()
        k = sorted(r[u"入力"][u"手元の 67 書類の sha256"])[0]
        r[u"入力"][u"手元の 67 書類の sha256"][k] = u"0" * 64
        self._red(check_inputs, r)
        r = self._mut()
        r[u"入力"][u"既存の cache の件数(終了時)"] += 1
        self._red(check_inputs, r)
        r = self._mut()
        r[u"環境"][u"DEFAULT_PROFILE"] = "P22"
        self._red(check_inputs, r)

    def test_m8_a_number_in_a_document_table_or_a_prose_sentence_is_red(self):
        B = render_blocks(self.rec0, self.bounds)
        for k, v in B.items():
            m = re.search(r"\d+", v)
            self.assertIsNotNone(m, k)
            mutated = self.doc.replace(v, v[:m.start()] + str(int(m.group(0)) + 7) + v[m.end():], 1)
            self.assertNotEqual(mutated, self.doc, k)
            self._red(check_doc, self.rec0, mutated, self.bounds)
        swap = dict(zip(u"零一二三四五六七八九", u"一二三四五六七八九零"))
        for k, v in prose_facts(self.rec0, self.bounds).items():
            hits = [v.index(c) for c in swap if c in v]
            if hits:
                i = min(hits)
                changed = v[:i] + swap[v[i]] + v[i + 1:]
            else:                       # 漢数字の無い文(外れた予測が無い、など)は末尾の『。』の前に字を足す
                changed = v[:-1] + u"(改)" + v[-1:]
            mutated = self.doc.replace(v, changed, 1)
            self.assertNotEqual(mutated, self.doc, k)
            self._red(check_doc, self.rec0, mutated, self.bounds)

    def test_m9_a_new_unbound_number_in_prose_is_red(self):
        self._red(check_doc, self.rec0, self.doc + u"\n影響は 12345 行。\n", self.bounds)
        self.assertEqual(residual_numbers(self.doc, self.rec0, self.bounds), [])

    def test_m10_the_reader_caveat_must_stay_in_the_document(self):
        self._red(check_doc, self.rec0, self.doc.replace(u"読みはエージェントの読みで人間の読みではない", u"読みは人間の読み"), self.bounds)

    def test_m11_a_wrong_judgment_in_the_record_is_red(self):
        r = self._mut()
        r[u"予測の判定"][u"S-1"][u"当たり"] = not r[u"予測の判定"][u"S-1"][u"当たり"]
        self._red(check_doc, r, self.doc, self.bounds)

    def test_m12_the_judgment_moves_with_the_numbers(self):
        J0 = judge_all(self.rec0, self.bounds)
        r = self._mut()
        r[u"S1"][u"書類別"][0][u"既定と P26 明示が同じ byte"] = False
        self.assertFalse(judge(r, self.bounds)[u"S-1"])
        r = self._mut()
        r[u"S6"][u"穴 B"][u"既定で通した"][u"件"] = 1
        self.assertFalse(judge(r, self.bounds)[u"S-6"])
        r = self._mut()
        r[u"S7"][u"adapters/xbrl/vocabulary.py"][u"挿入"] = 9
        self.assertFalse(judge(r, self.bounds)[u"S-7"])
        r = self._mut()
        r[u"S12"][u"既定"] = "P25"
        self.assertFalse(judge_docs(r, self.bounds)[u"S-12"])
        r = self._mut()
        r[u"S11"][u"試験 file の数(ディスク上)"] += 1
        self.assertFalse(judge_docs(r, self.bounds)[u"S-11"])
        self.assertTrue(all(J0[k] in (True, False) for k in J0))

    def test_m13_seal_bounds_are_read_from_the_seal_text(self):
        b = seal_bounds(self.seal)
        self.assertEqual(b[u"S-2"][0][:4], [u"4,371", u"433", u"1,579", u"1,416"])
        spoiled = self.seal.replace(u"**4,371**", u"**4,372**", 1)
        self.assertNotEqual(seal_bounds(spoiled)[u"S-2"][0][0], b[u"S-2"][0][0])
        self.assertFalse(judge(self.rec0, seal_bounds(spoiled))[u"S-2"])
        self._red(seal_bounds, self.seal.replace(u"| **S-5** |", u"| S-5 |", 1))

    def test_m14_a_wrong_engine_sha_is_red(self):
        old = dict(EXPECT)
        try:
            EXPECT["vocab_sha16"] = u"0" * 16
            self._red(engine_ok)
        finally:
            EXPECT.clear()
            EXPECT.update(old)
        engine_ok()

    def test_m15_reds_table_must_add_up(self):
        r = self._mut()
        r[u"試験の赤"][u"S8"][u"tests/measure"][u"赤"] += 1
        self._red(reds, r)
        r = self._mut()
        r[u"試験の赤"][u"S8"][u"種類"][r[u"試験の赤"][u"S8"][u"tests/measure"][u"ids"][0]] = u"5"
        self._red(reds, r)
        r = self._mut()
        r[u"試験の赤"][u"S9"][u"増えた赤の id"].pop()
        self._red(reds, r)

    def test_m16_the_reds_after_the_implementation_are_bound_to_the_pristine_clone(self):
        af = lambda r: r[u"試験の赤"][u"S9"][u"実装の後"]
        r = self._mut()
        self.assertEqual(af(r)[u"段 2 が原因の赤"], [])
        self.assertFalse(judge_reds(r, self.bounds)[u"S-9"])              # 実装の後に赤が残る(段 2 の前から赤の 3 本)= 封の外れ条件
        r = self._mut()
        ids = list(af(r)[u"段 2 の前から赤"])
        af(r)[u"段 2 の前から赤"] = []                                       # 何も変えない clone で確かめた赤を、確かめなかったことにする(足し算が合わない)
        self._red(reds, r)
        r = self._mut()
        af(r)[u"何も変えない clone(6a78b42)で env を付けて走らせた赤"] = [i for i in af(r)[u"何も変えない clone(6a78b42)で env を付けて走らせた赤"] if i != ids[0]]
        self._red(reds, r)                                                   # 確かめていない赤を『段 2 の前から赤』と言えない
        r = self._mut()
        env0 = sorted(af(r)[u"走らせ直し"])[0]
        af(r)[u"走らせ直し"][env0][u"赤の id"] = af(r)[u"走らせ直し"][env0][u"赤の id"] + [u"tests/measure/x.py::T::t"]
        self._red(reds, r)
        r = self._mut()
        env1 = sorted(af(r)[u"出力の差"])[0]
        af(r)[u"出力の差"][env1] = af(r)[u"出力の差"][env1] + [u"/C3/登録簿"]                # 既定・HEAD・sha・指紋の欄でない差が出たら赤
        self._red(reds, r)
        r = self._mut()                                                      # 赤を全部消した記録では S-9 が当たりに動く(判定が数に付いている)
        a = af(r)
        a[u"走らせ直し"] = dict((e, dict(v, **{u"赤": 0, u"赤の id": [], u"段 2 の前から赤": []})) for e, v in a[u"走らせ直し"].items())
        a[u"赤"], a[u"赤の id"], a[u"段 2 の前から赤"], a[u"段 2 が原因の赤"] = 0, [], [], []
        self.assertTrue(judge_reds(r, self.bounds)[u"S-9"])


if __name__ == "__main__":
    unittest.main()
