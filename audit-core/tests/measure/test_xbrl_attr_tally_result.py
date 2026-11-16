# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_ATTR_TALLY_SEAL_2026-11-17.md §4(AT ― 便をまたいだ集計の結果の文書)。

封の門 ``test_xbrl_attr_tally_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書だけを読む**(材料は読まない。数秒で終わる)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 本ずつ。木の file は変異させず、``Ctx`` の写しに当てる)
 a 記録と script の sha256(字で留める)
 b 記録の中の整合(内 + 外 + ク = 読んだ行・属性の和 = 内・外の理由の和 = 外・参考の合計 = 3 つの便の和・G の a + b + c = 読んだ行)
 c 結果の文書の §1〜§4 の数: 表の行も散文の行も、記録から組んだ 1 行と字で同じ(1 行ずつ。文書の行が 1 回ずつ在る)。そのどれにも当たらない行の 2 桁以上の数は、組んだ行の数の集合に在るものだけ
 d 予測 A-1〜A-7 の結果の欄と判定(当たり・外れ)を、封 §4 の予測の字から取った境と記録の数から門が自分で判定し直して、文書の表と同じ・字で留めた判定(外れ 2・当たり 5)と同じ
 e 文書に「証明した」「ハルシネーション」・会社名らしい字・「人の目」・3 桁以上の漢数字が無い・要点の字が在る
 f 封が 52f3a228 から 1 字も変わっていない・順序(commit の順。未 commit は赤)・engine 0 行・script と記録と封の門が fe0210de から変わっていない
この file は docID の字を持たない。
"""
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import unittest
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "measure"))


def load_module(rel, name):
    u"""importlib で読み込む。読み込みの前に居た名前は、読み込みの後に元の object へ戻す(自分の名前 ``name`` は残す)。"""
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for k, v in before.items():
            if k != name and sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SG = load_module("tests/measure/test_xbrl_attr_tally_seal.py", "at_seal_gate_for_at_result_gate")      # 封の門の部品。門としては走らせない
PR = SG.PR

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_attr_tally_result.py"
DOC_REL = "docs/XBRL_ATTR_TALLY_RESULT_2026-11-17.md"
IMPL_COMMIT = "fe0210de"                                     # script・封の門・記録を足した commit(この commit から 3 つは 0 行)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "dbbf45e5cd0363bfbc533b5a832454c325de546b845a292d08d17a58194545b6"),
    (SCRIPT_REL, "e6f66feaf3027ee425c3d421e97abd6edf49f77f5e9e2e515061afdcb4014346")])

BATCHES = (u"KAM", u"YS", u"TSS")
ATTRS = (u"項目", u"期", u"範囲", u"単位", u"1 株あたり")
ROW_LABEL = {u"KAM": u"KAM(監査報告書。全部の行)", u"YS": u"YS(有報の 3 つの節。全部の行)", u"TSS": u"TSS(短信の概況の文。標本 %d・母 1898)"}
MOTHER_TSS, MOTHER_KAM_G, MOTHER_NEAR = 1898, 136, 220      # 封 §0・§1 に在る母の数(記録は持たない。封に在るかを seal_problems が見る)
G_ROWS = (
    (u"KAM", u"G 連結", u"KAM 連結(標本 %d・母 136)", False),
    (u"KAM", u"G 単体", u"KAM 単体(全部)", False),
    (u"KAM", u"合計", u"KAM 計", True),
    (u"YS", u"G 研究", u"YS 研究開発活動", False),
    (u"YS", u"G 設備", u"YS 設備投資等の概要", False),
    (u"YS", u"G 配当", u"YS 配当政策", False),
    (u"YS", u"合計", u"YS 計", True))
PRED_CELLS = collections.OrderedDict([
    (u"A-1", u"V の率は 40% 以上 75% 以下"), (u"A-2", u"V の外でいちばん多いのは「見積り・計画」"), (u"A-3", u"V の内でいちばん多い属性は「範囲」"),
    (u"A-4", u"V の「単位」は 3 行以下"), (u"A-5", u"G の b のうち範囲に写る行が半分以上"), (u"A-6", u"G の c /(b + c)は 30% 以下"),
    (u"A-7", u"いちばん多い 1 本が持つ行は内の行の 25% 以下")])
PINNED_BOUNDS = {u"A-1": (40, 75), u"A-4": (3,), u"A-6": (30,), u"A-7": (25,)}
PINNED_JUDGE = (u"外れ", u"外れ", u"当たり", u"当たり", u"当たり", u"当たり", u"当たり")
PINNED_ACTUAL = (u"37/37(100.0%)", u"外は 0 行", u"範囲 25・項目 12", u"0 行", u"6/7", u"0/7", u"2/37(5.4%)")
HIT, MISS = u"当たり", u"**外れ**"
FORBIDDEN_WORDS = (u"証明" + u"した", u"ハルシ" + u"ネーション", u"人の" + u"目", u"精" + u"度", u"世界で 1 " + u"社")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
DOCID_RE = re.compile(r"S100[0-9A-Z]{4}")
POINTER_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)|formula:")
KANJI_NUM_RE = re.compile(u"[二三四五六七八九]百|[一二三四五六七八九]千|百[一二三四五六七八九十]|千[一二三四五六七八九百]")
REQUIRED_PHRASES = (u"AI の席 1 席", u"人は読んでいない", u"盲検でな", u"あと知恵", u"測っていない", u"外れた", u"割れた", u"言えないこと", u"人間の決定", u"限界")


# ======================================================================================================
# 道具
def read(rel, root=ROOT):
    with io.open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


def read_bytes(rel, root=ROOT):
    with io.open(os.path.join(root, rel), "rb") as fh:
        return fh.read()


def guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except BaseException as exc:                   # noqa: BLE001  変異で落ちた検査は「問題」として数える
        return [u"例外: %s" % type(exc).__name__]


def pct(a, b):
    return u"%.1f%%" % (100.0 * a / b) if b else u"-"


def frac(a, b):
    return u"%d/%d(%s)" % (a, b, pct(a, b))


class Ctx(object):
    u"""記録・封・文書・字の写し。変異は毎回 ``Ctx()`` の新しい写しに 1 か所だけ加える。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL))
        self.seal = read(SEAL_REL)
        self.doc = read(DOC_REL)
        self.texts = collections.OrderedDict((rel, read_bytes(rel)) for rel in SHA_PIN)


def counts(rec):
    return rec[u"便ごとの数"]


# ======================================================================================================
# a. sha256
def sha_problems(texts):
    return [u"sha256: %s が字で留めた値と違う" % rel for rel, want in SHA_PIN.items() if hashlib.sha256(texts.get(rel, b"")).hexdigest() != want]


# ======================================================================================================
# b. 記録の中の整合
def record_problems(c):
    out = []
    b = counts(c.rec)
    if tuple(b.keys()) != BATCHES + (u"参考の合計",):
        return [u"record: 便の並びが KAM・YS・TSS・参考の合計 でない"]
    tot_in = tot_den = tot_all = 0
    for name in BATCHES:
        v = b[name][u"V"]
        n, ink, outk, kk = v[u"読んだ行の数"], v[u"属性の内の行"], v[u"外の行"], v[u"ク の行(分母から除く)"]
        if ink + outk + kk != n:
            out.append(u"record[%s]: 内 + 外 + ク が読んだ行と違う" % name)
        if sum(v[u"属性ごとの行の数"].values()) != ink or list(v[u"属性ごとの行の数"].keys()) != list(ATTRS):
            out.append(u"record[%s]: 属性ごとの行の和が内と違う" % name)
        if sum(v[u"外の理由ごとの行の数"].values()) != outk:
            out.append(u"record[%s]: 外の理由の和が外と違う" % name)
        r = v[u"率(主。分母は ク を除く)"]
        r2 = v[u"率(2 本目。分母に ク を入れる)"]
        if (r[u"分子"], r[u"分母"]) != (ink, n - kk) or (r2[u"分子"], r2[u"分母"]) != (ink, n) or r[u"率"] != pct(ink, n - kk) or r2[u"率"] != pct(ink, n):
            out.append(u"record[%s]: 率の分子・分母・字が行から数え直した値と違う" % name)
        if v[u"属性ごとの行の数"][u"1 株あたり"] != 0:
            out.append(u"record[%s]: 1 株あたりが 0(作り)でない" % name)
        tot_in += ink
        tot_den += n - kk
        tot_all += n
    ref = b[u"参考の合計"]
    a1 = ref[u"V の行の単純な合計(KAM + YS + TSS。分母は ク を除く)"]
    a2 = ref[u"分母に ク を入れた場合"]
    if (a1[u"分子"], a1[u"分母"], a1[u"率"]) != (tot_in, tot_den, pct(tot_in, tot_den)) or (a2[u"分子"], a2[u"分母"], a2[u"率"]) != (tot_in, tot_all, pct(tot_in, tot_all)):
        out.append(u"record: 参考の合計が 3 つの便の和と違う")
    for name in (u"KAM", u"YS"):
        for key, g in b[name][u"G"].items():
            if g[u"a(合う)"] + g[u"b(違うもの)"] + g[u"c(分けられない)"] != g[u"読んだ行の数"]:
                out.append(u"record[%s %s]: a + b + c が読んだ行と違う" % (name, key))
            if sum(g[u"b の属性ごと(側は範囲に写す)"].values()) != g[u"b(違うもの)"]:
                out.append(u"record[%s %s]: b の属性の和が b と違う" % (name, key))
    return out


# ======================================================================================================
# d. 予測の判定
def seal_rows(seal):
    u"""封 §4 の A-1〜A-7(id → 予測の字)。"""
    sec = seal[seal.index(u"## §4"):]
    return collections.OrderedDict((m.group(1), m.group(2)) for m in re.finditer(r"^\| (A-\d) \| (.*?) \| .*? \|$", sec, re.M))


def seal_bounds(seal):
    u"""封の予測の字から境の数を取る(A-1 は下限と上限・A-4 の行数・A-6・A-7 の %)。"""
    rows = seal_rows(seal)
    out = {}
    m = re.search(r"(\d+)% 以上 (\d+)% 以下", rows[u"A-1"])
    out[u"A-1"] = (int(m.group(1)), int(m.group(2)))
    out[u"A-4"] = (int(re.search(r"(\d+) 行以下", rows[u"A-4"]).group(1)),)
    out[u"A-6"] = (int(re.search(r"(\d+)% 以下", rows[u"A-6"]).group(1)),)
    out[u"A-7"] = (int(re.search(r"(\d+)% 以下", rows[u"A-7"]).group(1)),)
    return out


def judge(rec, seal):
    u"""[(id, 結果の字, 当たりか)]。境は封の字から、数は記録から。"""
    bd = seal_bounds(seal)
    b = counts(rec)
    v = b[u"KAM"][u"V"]
    n, ink, kk = v[u"読んだ行の数"], v[u"属性の内の行"], v[u"ク の行(分母から除く)"]
    den = n - kk
    out = []
    lo, hi = bd[u"A-1"]
    out.append((u"A-1", frac(ink, den), Fraction(lo, 100) <= Fraction(ink, den) <= Fraction(hi, 100)))
    why = v[u"外の理由ごとの行の数"]
    outk = v[u"外の行"]
    top = max(why.values()) if why else 0
    sole = [k for k, x in why.items() if x == top]
    out.append((u"A-2", u"外は 0 行" if outk == 0 else u"・".join(u"%s %d" % (k, x) for k, x in why.items()), outk > 0 and sole == [u"見積り・計画"]))
    at = v[u"属性ごとの行の数"]
    others = [(k, x) for k, x in at.items() if k != u"範囲"]
    second = max(others, key=lambda kv: kv[1])
    out.append((u"A-3", u"範囲 %d・%s %d" % (at[u"範囲"], second[0], second[1]), all(at[u"範囲"] > x for _k, x in others)))
    out.append((u"A-4", u"%d 行" % at[u"単位"], at[u"単位"] <= bd[u"A-4"][0]))
    g = b[u"KAM"][u"G"][u"合計"]
    gb, gc = g[u"b(違うもの)"], g[u"c(分けられない)"]
    gr = g[u"b の属性ごと(側は範囲に写す)"][u"範囲"]
    out.append((u"A-5", u"%d/%d" % (gr, gb), gb > 0 and 2 * gr >= gb))
    out.append((u"A-6", u"%d/%d" % (gc, gb + gc), gb + gc > 0 and Fraction(gc, gb + gc) <= Fraction(bd[u"A-6"][0], 100)))
    sp = v[u"本の片寄り"]
    m, tot = sp[u"いちばん多い 1 本が持つ内の行の数"], sp[u"属性の内の行の数"]
    out.append((u"A-7", frac(m, tot), Fraction(m, tot) <= Fraction(bd[u"A-7"][0], 100)))
    return out


def judge_problems(c):
    out = []
    rows = seal_rows(c.seal)
    if list(rows.keys()) != list(PRED_CELLS.keys()):
        return [u"judge: 封 §4 の予測が A-1〜A-7 の 7 行でない"]
    bd = seal_bounds(c.seal)
    if bd != PINNED_BOUNDS:
        out.append(u"judge: 封の予測の境が字で留めた値と違う")
    jd = judge(c.rec, c.seal)
    if tuple(u"当たり" if ok else u"外れ" for _i, _t, ok in jd) != PINNED_JUDGE:
        out.append(u"judge: 判定が字で留めた「外れ・外れ・当たり 5」と違う")
    if tuple(t for _i, t, _ok in jd) != PINNED_ACTUAL:
        out.append(u"judge: 結果の字が字で留めた値と違う")
    lines = c.doc.split(u"\n")
    for (i, text, ok), cell in zip(jd, PRED_CELLS.values()):
        want = u"| %s | %s | %s | %s |" % (i, cell, text, HIT if ok else MISS)
        if lines.count(want) != 1:
            out.append(u"judge: 文書の予測の表の %s が門の判定し直しと違う" % i)
    hits = sum(1 for _i, _t, ok in jd if ok)
    if u"- 当たり %d・外れ %d。" % (hits, len(jd) - hits) not in c.doc:
        out.append(u"judge: 文書の「当たり・外れ」の数が判定し直した数と違う")
    return out


# ======================================================================================================
# c. 文書の行
def cond(ok, text):
    return text if ok else u"【条件が合わない】" + text


def expected_lines(c):
    u"""結果の文書の数を持つ行を、記録から 1 行ずつ組む。[(名前, 行)]。"""
    rec, seal = c.rec, c.seal
    b = counts(rec)
    E = []
    V = dict((n, b[n][u"V"]) for n in BATCHES)
    for n in BATCHES:                                                  # §1 の表
        v = V[n]
        label = ROW_LABEL[n] % v[u"読んだ行の数"] if n == u"TSS" else ROW_LABEL[n]
        den = v[u"読んだ行の数"] - v[u"ク の行(分母から除く)"]
        E.append((u"s1 %s" % n, u"| %s | %d | %d | %d | %d | %s | %s |" % (label, v[u"読んだ行の数"], v[u"ク の行(分母から除く)"], v[u"属性の内の行"], v[u"外の行"],
                                                                      frac(v[u"属性の内の行"], den), frac(v[u"属性の内の行"], v[u"読んだ行の数"]))))
    for n in BATCHES:                                                  # 属性ごと
        a = V[n][u"属性ごとの行の数"]
        E.append((u"attr %s" % n, u"| %s | %s |" % (n, u" | ".join(str(a[k]) for k in ATTRS))))
    for n in BATCHES:                                                  # 外の理由ごと
        w = V[n][u"外の理由ごとの行の数"]
        cells = []
        for k in (u"見積り・計画", u"数の読み取り", u"計算の形", u"向き・増減の書き方", u"符号", u"分けられない"):
            if k in w:
                cells.append(str(w[k]))
            else:
                cells.append(u"―(語彙に無い)" if (n == u"KAM" and k == u"数の読み取り") else u"―")
        E.append((u"why %s" % n, u"| %s | %s |" % (n, u" | ".join(cells))))
    k = V[u"KAM"]
    kc, kt = b[u"KAM"][u"V"][u"組別"][u"V 連結"], b[u"KAM"][u"V"][u"組別"][u"V 単体"]
    other = sum(x for t, x in k[u"型・細目ごとの行の数"].items() if t not in (u"ア", u"ウ", u"オ"))
    E.append((u"kam 組別", u"- KAM の組別: V 連結 %d 行は項目 %d・範囲 %d、V 単体 %d 行は項目 %d・範囲 %d。型の字では ア %d・ウ %d・オ %d で、ほかの型は %d 行。" % (
        kc[u"読んだ行の数"], kc[u"属性ごとの行の数"][u"項目"], kc[u"属性ごとの行の数"][u"範囲"], kt[u"読んだ行の数"], kt[u"属性ごとの行の数"][u"項目"], kt[u"属性ごとの行の数"][u"範囲"],
        k[u"型・細目ごとの行の数"][u"ア"], k[u"型・細目ごとの行の数"][u"ウ"], k[u"型・細目ごとの行の数"][u"オ"], other)))
    ys = V[u"YS"]
    yd = ys[u"組別"][u"V 配当"]
    E.append((u"ys 外", cond(ys[u"外の理由ごとの行の数"][u"見積り・計画"] == ys[u"外の行"] == yd[u"外の行"],
                         u"- YS の外 %d 行は全部が配当政策の節の「見積り・計画」。" % ys[u"外の行"])))
    sp = dict((n, V[n][u"本の片寄り"]) for n in BATCHES)
    E.append((u"偏り", u"- 本の片寄り: 属性の内の行を持つ本は KAM %d 本・YS %d 本・TSS %d 本。いちばん多い 1 本が持つ行は KAM %d 行(%d/%d、%s)・YS %d 行(%d/%d、%s)・TSS %d 行(%d/%d、%s)。1 本に片寄ってはいない。" % (
        sp[u"KAM"][u"属性の内の行を持つ本の数"], sp[u"YS"][u"属性の内の行を持つ本の数"], sp[u"TSS"][u"属性の内の行を持つ本の数"],
        sp[u"KAM"][u"いちばん多い 1 本が持つ内の行の数"], sp[u"KAM"][u"いちばん多い 1 本が持つ内の行の数"], sp[u"KAM"][u"属性の内の行の数"], pct(sp[u"KAM"][u"いちばん多い 1 本が持つ内の行の数"], sp[u"KAM"][u"属性の内の行の数"]),
        sp[u"YS"][u"いちばん多い 1 本が持つ内の行の数"], sp[u"YS"][u"いちばん多い 1 本が持つ内の行の数"], sp[u"YS"][u"属性の内の行の数"], pct(sp[u"YS"][u"いちばん多い 1 本が持つ内の行の数"], sp[u"YS"][u"属性の内の行の数"]),
        sp[u"TSS"][u"いちばん多い 1 本が持つ内の行の数"], sp[u"TSS"][u"いちばん多い 1 本が持つ内の行の数"], sp[u"TSS"][u"属性の内の行の数"], pct(sp[u"TSS"][u"いちばん多い 1 本が持つ内の行の数"], sp[u"TSS"][u"属性の内の行の数"]))))
    tin = sum(V[n][u"属性の内の行"] for n in BATCHES)
    tden = sum(V[n][u"読んだ行の数"] - V[n][u"ク の行(分母から除く)"] for n in BATCHES)
    tall = sum(V[n][u"読んだ行の数"] for n in BATCHES)
    E.append((u"参考", u"- 参考(母集団の率ではない。引き方が違う 3 つの便の行を単純に足しただけ): %s。ク を分母に入れると %s。" % (frac(tin, tden), frac(tin, tall))))
    near = b[u"TSS"][u"近い行の型(並べるだけ。率に入れない。写さない)"]
    E.append((u"近い行", cond(near[u"近い行の数(母)"] == MOTHER_NEAR, u"- 並べるだけ(率に入れていない): TSS の近い行 %d(母 %d)の型は %s。" % (
        near[u"読む行の数"], near[u"近い行の数(母)"], u"・".join(u"%s %d" % (t, x) for t, x in near[u"型ごとの行の数"].items())))))
    for name, key, label, is_total in G_ROWS:                           # §2 の表
        g = b[name][u"G"][key]
        lab = label % g[u"読んだ行の数"] if u"%d" in label else label
        bb, cc = g[u"b(違うもの)"], g[u"c(分けられない)"]
        at = g[u"b の属性ごと(側は範囲に写す)"]
        ccell = (u"%d/%d(%s)" % (cc, bb + cc, pct(cc, bb + cc))) if is_total else u"%d/%d" % (cc, bb + cc)
        E.append((u"s2 %s" % lab, u"| %s | %d | %d | %d | %d | %d / %d | %s |" % (lab, g[u"読んだ行の数"], g[u"a(合う)"], bb, cc, at[u"項目"], at[u"範囲"], ccell)))
    kg = b[u"KAM"][u"G"][u"合計"]
    kraw, ksum = kg[u"b の違うもの(記録の字のまま)"], kg[u"b の属性ごと(側は範囲に写す)"]
    both_period = ksum[u"期"] == 0 and b[u"YS"][u"G"][u"合計"][u"b の属性ごと(側は範囲に写す)"][u"期"] == 0
    E.append((u"側", cond(kraw[u"範囲"] == 0 and kraw[u"側"] == ksum[u"範囲"] and both_period,
                         u"KAM の b の「範囲」%d 行は、元の字では全部が「側」(連結と単体)。b の「期」は 2 つの便とも 0 行。" % ksum[u"範囲"])))
    jd = judge(rec, seal)                                              # §3
    for (i, text, ok), cell in zip(jd, PRED_CELLS.values()):
        E.append((u"s3 %s" % i, u"| %s | %s | %s | %s |" % (i, cell, text, HIT if ok else MISS)))
    miss = [i for i, _t, ok in jd if not ok]
    E.append((u"s3 当たり外れ", cond(V[u"KAM"][u"外の理由ごとの行の数"][u"見積り・計画"] == 0,
                              u"- 当たり %d・外れ %d。外れ %d 本は同じ 1 つの見立て違い(KAM の文には見積りの数が多いので警報の外も多いはず)から出た。KAM の「値が違う」の行には、見積り・計画の型が 1 行も付いていなかった。" % (
                                  len(jd) - len(miss), len(miss), len(miss)))))
    E.append((u"s0 予測", u"- 予測 %d 本のうち **%d 本が外れた**(%s。§3)。" % (len(jd), len(miss), u"・".join(miss))))
    per, unit = sum(V[n][u"属性ごとの行の数"][u"期"] for n in BATCHES), sum(V[n][u"属性ごとの行の数"][u"単位"] for n in BATCHES)
    rng, item = sum(V[n][u"属性ごとの行の数"][u"範囲"] for n in BATCHES), sum(V[n][u"属性ごとの行の数"][u"項目"] for n in BATCHES)
    E.append((u"s0 属性", cond(sorted([rng, item]) == sorted(sorted(x for x in (rng, item, unit, per))[-2:]) and sum(V[n][u"属性ごとの行の数"][u"1 株あたり"] for n in BATCHES) == 0,
                             u"- 「5 つの属性」と言ったが、行が写ったのは**ほぼ 2 つ(範囲と項目)だけ**だった。期は %d 行、単位は %d 行、1 株あたりは作りで 0。**期・単位・1 株あたりが効くかどうかは、この便では何も言えない。**" % (per, unit))))
    rates = [pct(V[n][u"属性の内の行"], V[n][u"読んだ行の数"] - V[n][u"ク の行(分母から除く)"]) for n in BATCHES]   # §4
    E.append((u"s4 決め", cond(u"**3 つの便とも 60% 以上**" in seal and all(float(r[:-1]) >= 60.0 for r in rates),
                             u"封 §4 の決め: 3 つの便とも 60%% 以上なら「警報の多くは属性の取り違えに写る」と読む。結果は %s で、**字のうえでは 60%% 以上の側**。ただし:" % u"・".join(rates))))
    yi, yn = ys[u"属性の内の行"], ys[u"読んだ行の数"]
    E.append((u"s4 1", cond(Fraction(yi - 1, yn) * 100 >= 50 and Fraction(yi - 1, yn) * 100 < 60,
                          u"1. **YS は %d 行で %s。1 行が外へ動けば %sで「割れた」になる。** 余裕は無い。" % (yn, pct(yi, yn), frac(yi - 1, yn)))))
    E.append((u"s4 2", u"2. 写ったのは範囲 %d 行・項目 %d 行・単位 %d 行(3 つの便の内の行 %d のうち)。**中身は「部分と全体・連結と単体の取り違え」がほとんど**で、「5 つの属性」という言い方は広すぎた。" % (rng, item, unit, tin)))
    E.append((u"s4 3", u"3. 「項目」は元の字が「定義の違い」で、ほかに入らないものの受け皿でもある。項目の %d 行は、属性を条件に足して止められる形かどうかが分からない。" % item))
    plan = sum(V[n][u"外の理由ごとの行の数"][u"見積り・計画"] for n in BATCHES)
    allout = sum(V[n][u"外の行"] for n in BATCHES)
    reasons = collections.Counter()
    for n in BATCHES:
        for key, x in V[n][u"外の理由ごとの行の数"].items():
            reasons[key] += x
    E.append((u"s4 4", cond(reasons.most_common(1)[0][0] == u"見積り・計画", u"4. 外でいちばん多いのは「見積り・計画」%d 行(外 %d 行のうち)。実績の数か計画の数かは、5 つの属性の外に在るいちばん大きい束。" % (plan, allout))))
    E.append((u"s4 言えること", u"**言えること**: 3 つの便の「値が違う」と読んだ行(計 %d。ク を除く)のうち、この封の写し方で %d 行が属性の取り違えに写り、その %d 行は範囲だった。**言えないこと**: 範囲を結ぶ条件に入れれば警報が減ること・ほかの文書でも同じ割合になること・型の読みが正しいこと。" % (tden, tin, rng)))
    E.append((u"s6 4", u"4. 行が少ない(YS の V は %d 行、KAM の V は %d 行)。" % (V[u"YS"][u"読んだ行の数"], V[u"KAM"][u"読んだ行の数"])))
    return E


NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers_of(text, min_digits=2):
    out = set()
    for m in NUM_RE.findall(text):
        s = m.rstrip(u",").replace(u",", u"")
        if len(s.split(u".")[0]) >= min_digits:
            out.add(s)
    return out


def prose_clean(line):
    t = re.sub(r"`[^`]*`", u"", line)
    t = t.replace(u"sha256", u"")
    t = re.sub(r"\d{4}-\d{2}-\d{2}", u"", t)
    t = re.sub(r"\b[0-9a-f]{7,}\b", u"", t)
    t = re.sub(r"https?://\S+|\S+\.(?:md|py|json)\b", u"", t)
    t = re.sub(r"\b[A-Z]+-?\d+[A-Z]*\b", u"", t)
    t = re.sub(u"§[0-9\\-]+", u"", t)
    return t


def table_numbers(c, exp):
    u"""組んだ行に出る数と、封の字(母の数)から作れる数。"""
    allowed = set()
    for _n, line in exp:
        allowed |= numbers_of(line)
    allowed |= set(str(x) for x in (MOTHER_TSS, MOTHER_KAM_G, MOTHER_NEAR))
    return allowed


def doc_problems(c):
    doc = c.doc
    out = []
    lines = doc.split(u"\n")
    exp = expected_lines(c)
    names = [n for n, _l in exp]
    if len(set(names)) != len(names):
        out.append(u"文書: 組んだ行の名前が重なる")
    for n, line in exp:
        k = lines.count(line)
        if k != 1:
            out.append(u"文書: 記録から組んだ行「%s」が文書に 1 回ずつ無い(%d 回): %s" % (n, k, line[:40]))
    expset = set(l for _n, l in exp)
    allowed = table_numbers(c, exp)
    for ln, line in enumerate(lines, 1):
        if line in expset:
            continue
        bad = sorted(numbers_of(prose_clean(line)) - allowed)
        if bad:
            out.append(u"文書: 組んだ行の外の数が記録から作った数の集合に無い: 行 %d %s" % (ln, u",".join(bad)))
    out += words_problems(c)
    return out


def words_problems(c):
    doc = c.doc
    out = []
    for w in FORBIDDEN_WORDS:
        if w in doc:
            out.append(u"words: 禁止語 %s" % w)
    for w in COMPANY_WORDS:
        if w in doc:
            out.append(u"words: 会社名らしい字 %s" % w)
    if DOCID_RE.search(doc) or POINTER_RE.search(doc):
        out.append(u"words: docID・pointer の形の字がある")
    for ln, line in enumerate(doc.split(u"\n"), 1):
        if KANJI_NUM_RE.search(line):
            out.append(u"words: 3 桁以上の数を漢数字で書いている: 行 %d" % ln)
    for need in (os.path.basename(SEAL_REL), SEAL_COMMIT_SHORT, IMPL_COMMIT, os.path.basename(SCRIPT_REL), os.path.basename(RECORD_REL)) + REQUIRED_PHRASES:
        if need not in doc:
            out.append(u"words: 要点の字が無い: %s" % need)
    return out


# ======================================================================================================
# f. 封・順序・engine
def seal_frozen_problems(seal_text, root=REPO):
    rc, _ = PR.git_in(root, "cat-file", "-e", SEAL_COMMIT_SHORT + "^{commit}")
    if rc != 0:
        return [u"封の commit が履歴に無い"]
    r = subprocess.run(["git", "show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL)], cwd=root, capture_output=True)
    if r.returncode != 0:
        return [u"封の commit に封の file が無い"]
    if r.stdout != seal_text.encode("utf-8"):
        return [u"封が %s のときの byte から変わっている" % SEAL_COMMIT_SHORT]
    return []


def seal_text_problems(c):
    u"""封に母の数・読み方の字が在る(文書が持つ封の字の根)。"""
    out = []
    for need in (u"標本 120(母 1898)", u"母 136", u"**3 つの便とも 60% 以上**"):
        if need not in c.seal:
            out.append(u"seal: 封に %s が無い" % need)
    return out


def order_others():
    return [RECORD_REL, SEAL_GATE_REL, DOC_REL, GATE_REL]


def order_problems_real(root=REPO):
    return PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL], order_others())


def engine_problems(root=REPO):
    u"""engine・lib・入力は封の commit から 0 行(未 commit も)。script・記録・封の門は足した commit から 0 行(未 commit の編集も)。"""
    out = list(SG.engine_since_seal_problems(root)) + list(SG.engine_worktree_problems(root))
    rc, txt = PR.git_in(root, "diff", "--numstat", IMPL_COMMIT, "--", *[PREFIX + r for r in (SCRIPT_REL, RECORD_REL, SEAL_GATE_REL)])
    if rc != 0:
        out.append(u"engine: git diff が失敗した")
    elif txt:
        out.append(u"engine: script・記録・封の門が %s から変わっている" % IMPL_COMMIT)
    return out


# ======================================================================================================
# 変異の表(1 行 = 1 つの検査を赤にする 1 か所の変異。木の file は変異させず、Ctx の写しを変える)
CHECKS = collections.OrderedDict([
    (u"sha", lambda c: sha_problems(c.texts)),
    (u"rec", record_problems),
    (u"doc", doc_problems),
    (u"judge", judge_problems),
    (u"words", words_problems),
    (u"seal", seal_text_problems),
    (u"frozen", lambda c: seal_frozen_problems(c.seal)),
])

MUTATIONS = []


def M(label, check, fn):
    MUTATIONS.append((label, check, fn))


def doc_replace(old, new, every=False):
    def fn(c):
        assert old in c.doc, old
        c.doc = c.doc.replace(old, new) if every else c.doc.replace(old, new, 1)
    return fn


def seal_replace(old, new, every=False):
    def fn(c):
        assert old in c.seal, old
        c.seal = c.seal.replace(old, new) if every else c.seal.replace(old, new, 1)
    return fn


def rec_set(path, value):
    def fn(c):
        d = c.rec
        for k in path[:-1]:
            d = d[k]
        d[path[-1]] = value
    return fn


def doc_append(text):
    return lambda c: setattr(c, "doc", c.doc + text)


def set_text(rel, fn):
    return lambda c: c.texts.__setitem__(rel, fn(c.texts[rel]))


M(u"a1 記録の 1 byte", u"sha", set_text(RECORD_REL, lambda t: t + b" "))
M(u"a2 script の 1 byte", u"sha", set_text(SCRIPT_REL, lambda t: t + b" "))
# b 記録の中の整合
M(u"b1 KAM の V の読んだ行を 1 つ変える", u"rec", rec_set([u"便ごとの数", u"KAM", u"V", u"読んだ行の数"], 38))
M(u"b2 YS の V の内を 1 つ変える", u"rec", rec_set([u"便ごとの数", u"YS", u"V", u"属性の内の行"], 12))
M(u"b3 TSS の範囲を 1 つ変える", u"rec", rec_set([u"便ごとの数", u"TSS", u"V", u"属性ごとの行の数", u"範囲"], 77))
M(u"b4 TSS の外の理由を 1 つ変える", u"rec", rec_set([u"便ごとの数", u"TSS", u"V", u"外の理由ごとの行の数", u"見積り・計画"], 21))
M(u"b5 参考の合計の分子を変える", u"rec", rec_set([u"便ごとの数", u"参考の合計", u"V の行の単純な合計(KAM + YS + TSS。分母は ク を除く)", u"分子"], 133))
M(u"b6 率の字を変える", u"rec", rec_set([u"便ごとの数", u"YS", u"V", u"率(主。分母は ク を除く)", u"率"], u"61.2%"))
M(u"b7 KAM の G 合計の a を変える", u"rec", rec_set([u"便ごとの数", u"KAM", u"G", u"合計", u"a(合う)"], 90))
M(u"b8 1 株あたりを 1 にする", u"rec", rec_set([u"便ごとの数", u"KAM", u"V", u"属性ごとの行の数", u"1 株あたり"], 1))
# c 文書の行(表の数 1 つ・散文の数 1 つ)
M(u"c1 表の数 §1 の KAM の内の数字 1 つ", u"doc", doc_replace(u"| 37 | 0 | 37 | 0 | 37/37(100.0%)", u"| 37 | 0 | 36 | 0 | 37/37(100.0%)"))
M(u"c2 §1 の TSS の率の字 1 つ", u"doc", doc_replace(u"84/119(70.6%)", u"84/119(70.7%)"))
M(u"c3 属性ごとの表の TSS の範囲", u"doc", doc_replace(u"| TSS | 7 | 0 | 76 | 1 | 0 |", u"| TSS | 7 | 0 | 75 | 1 | 0 |"))
M(u"c4 外の理由の表の TSS の見積り", u"doc", doc_replace(u"| TSS | 20 | 6 | 1 | 7 | 0 | 1 |", u"| TSS | 21 | 6 | 1 | 7 | 0 | 1 |"))
M(u"c5 外の理由の表の KAM の「―(語彙に無い)」", u"doc", doc_replace(u"―(語彙に無い)", u"―"))
M(u"c6 KAM の組別の散文の数 1 つ", u"doc", doc_replace(u"V 連結 29 行は項目 10・範囲 19", u"V 連結 29 行は項目 11・範囲 19"))
M(u"c7 YS の外の散文の数 1 つ", u"doc", doc_replace(u"YS の外 7 行は", u"YS の外 8 行は"))
M(u"c8 本の片寄りの散文の数 1 つ", u"doc", doc_replace(u"TSS 4 行(4/84、4.8%)", u"TSS 5 行(4/84、4.8%)"))
M(u"c9 参考の 132/174 の散文", u"doc", doc_replace(u"132/174(75.9%)", u"133/174(75.9%)"))
M(u"c10 参考の ク を入れた率の散文", u"doc", doc_replace(u"132/175(75.4%)", u"132/175(75.5%)"))
M(u"c11 近い行の型の数 1 つ", u"doc", doc_replace(u"い 114", u"い 115"))
M(u"c12 §2 の KAM 計の行の数字 1 つ", u"doc", doc_replace(u"| KAM 計 | 96 | 89 | 7 | 0 | 1 / 6 |", u"| KAM 計 | 96 | 89 | 7 | 0 | 2 / 6 |"))
M(u"c13 §2 の YS 配当の b の属性の数字 1 つ", u"doc", doc_replace(u"| 16 | 0 | 3 / 13 |", u"| 16 | 0 | 3 / 12 |"))
M(u"c14 §2 の YS 計の c の率の字", u"doc", doc_replace(u"6/26(23.1%)", u"6/26(23.2%)"))
M(u"c15 §2 の側の散文の数", u"doc", doc_replace(u"KAM の b の「範囲」6 行は", u"KAM の b の「範囲」5 行は"))
M(u"c16 §3 の当たり外れの散文の数(当たり 5)", u"doc", doc_replace(u"- 当たり 5・外れ 2。", u"- 当たり 6・外れ 2。"))
M(u"c17 §0 の予測の本数の散文", u"doc", doc_replace(u"予測 7 本のうち **2 本が外れた**", u"予測 7 本のうち **3 本が外れた**"))
M(u"c18 §0 の期・単位の散文の数", u"doc", doc_replace(u"期は 0 行、単位は 1 行、", u"期は 0 行、単位は 2 行、"))
M(u"c19 §4 の 10/18(55.6%) の散文", u"doc", doc_replace(u"10/18(55.6%)", u"10/18(55.7%)"))
M(u"c20 §4 の範囲 105 行・項目 26 行・単位 1 行の範囲", u"doc", doc_replace(u"範囲 105 行・項目 26 行・単位 1 行", u"範囲 104 行・項目 26 行・単位 1 行"))
M(u"c21 §4 の 132 の散文", u"doc", doc_replace(u"(3 つの便の内の行 132 のうち)", u"(3 つの便の内の行 133 のうち)"))
M(u"c22 §4 の項目 26 行の散文", u"doc", doc_replace(u"項目の 26 行は", u"項目の 27 行は"))
M(u"c23 §4 の見積り・計画 27 行・外 42 行の 27", u"doc", doc_replace(u"「見積り・計画」27 行(外 42 行のうち)", u"「見積り・計画」28 行(外 42 行のうち)"))
M(u"c24 §4 の外 42 行", u"doc", doc_replace(u"(外 42 行のうち)", u"(外 43 行のうち)"))
M(u"c25 §4 の計 174", u"doc", doc_replace(u"(計 174。ク を除く)", u"(計 175。ク を除く)"))
M(u"c26 §4 の 132 行が属性の取り違えに写り", u"doc", doc_replace(u"で 132 行が属性の取り違えに写り、その 105 行は", u"で 131 行が属性の取り違えに写り、その 105 行は"))
M(u"c27 §4 の 結果は 100.0%・61.1%・70.6%", u"doc", doc_replace(u"結果は 100.0%・61.1%・70.6% で", u"結果は 100.0%・61.1%・70.5% で"))
M(u"c28 §4 の YS は 18 行で 61.1%", u"doc", doc_replace(u"YS は 18 行で 61.1%", u"YS は 17 行で 61.1%"))
M(u"c29 §6 の 行が少ない の YS 18 行", u"doc", doc_replace(u"(YS の V は 18 行、KAM の V は 37 行)", u"(YS の V は 19 行、KAM の V は 37 行)"))
M(u"c30 §1 の TSS の標本の字", u"doc", doc_replace(u"標本 120・母 1898", u"標本 120・母 1899"))
M(u"c31 散文に記録に無い数を足す(組んだ行の外)", u"doc", doc_append(u"\n- 新しい行が 77 行ある。\n"))
M(u"c32 散文の外れ・当たりの行を 1 行消す", u"doc", doc_replace(u"- 当たり 5・外れ 2。", u"- 当たり。"))
M(u"c33 §1 の行を 1 つ消す(KAM)", u"doc", doc_replace(u"| KAM(監査報告書。全部の行) | 37 |", u"| KAM | 37 |"))
M(u"c34 組んだ行を重ねる(1 回でなく 2 回)", u"doc", doc_append(u"\n- 参考(母集団の率ではない。引き方が違う 3 つの便の行を単純に足しただけ): 132/174(75.9%)。ク を分母に入れると 132/175(75.4%)。\n"))
# d 判定
M(u"d1 A-1 の判定を逆にする(外れ → 当たり)", u"judge", doc_replace(u"| A-1 | V の率は 40% 以上 75% 以下 | 37/37(100.0%) | **外れ** |", u"| A-1 | V の率は 40% 以上 75% 以下 | 37/37(100.0%) | 当たり |"))
M(u"d2 A-2 の判定を逆にする(外れ → 当たり)", u"judge", doc_replace(u"| 外は 0 行 | **外れ** |", u"| 外は 0 行 | 当たり |"))
M(u"d3 A-3 の判定を逆にする(当たり → 外れ)", u"judge", doc_replace(u"| 範囲 25・項目 12 | 当たり |", u"| 範囲 25・項目 12 | **外れ** |"))
M(u"d4 A-5 の判定を逆にする", u"judge", doc_replace(u"| 6/7 | 当たり |", u"| 6/7 | **外れ** |"))
M(u"d5 A-7 の判定を逆にする", u"judge", doc_replace(u"| 2/37(5.4%) | 当たり |", u"| 2/37(5.4%) | **外れ** |"))
M(u"d6 A-4 の結果の字", u"judge", doc_replace(u"| 0 行 | 当たり |", u"| 1 行 | 当たり |"))
M(u"d7 A-6 の結果の字", u"judge", doc_replace(u"| 0/7 | 当たり |", u"| 0/6 | 当たり |"))
M(u"d8 「当たり 5」を変える(散文)", u"judge", doc_replace(u"- 当たり 5・外れ 2。", u"- 当たり 4・外れ 3。"))
M(u"d9 封の A-1 の上限を替える(判定の境が字で留めた値と違う)", u"judge", seal_replace(u"40% 以上 75% 以下", u"40% 以上 99% 以下"))
M(u"d10 封の A-7 の境を替える(A-7 が外れに動く)", u"judge", seal_replace(u"内の行の 25% 以下", u"内の行の 5% 以下"))
M(u"d11 封の A-4 の境を替える(A-4 の境が変わる)", u"judge", seal_replace(u"は 3 行以下", u"は 0 行以下"))
M(u"d12 記録の KAM の範囲を 1 にする(A-3 が外れに動き、判定が字で留めた値と違う)", u"judge", rec_set([u"便ごとの数", u"KAM", u"V", u"属性ごとの行の数", u"範囲"], 1))
M(u"d13 記録の KAM の外に見積り・計画を足す(A-2 が当たりに動く)", u"judge", lambda c: (c.rec[u"便ごとの数"][u"KAM"][u"V"].__setitem__(u"外の行", 3), c.rec[u"便ごとの数"][u"KAM"][u"V"][u"外の理由ごとの行の数"].__setitem__(u"見積り・計画", 3)))
M(u"d14 予測の字の予測の行を 1 つ消す", u"judge", seal_replace(u"| A-7 | KAM で V", u"| A-8 | KAM で V"))
M(u"d15 文書の予測の字を替える", u"judge", doc_replace(u"V の「単位」は 3 行以下", u"V の「単位」は 4 行以下"))
# e 文書の字
M(u"e1 禁止語(証明した)", u"words", doc_append(u"\n証明" + u"した。\n"))
M(u"e2 禁止語(ハルシネーション)", u"words", doc_append(u"\nハルシ" + u"ネーション。\n"))
M(u"e3 禁止語(人の目)", u"words", doc_append(u"\n人の" + u"目。\n"))
M(u"e4 会社名らしい字(株式会社)", u"words", doc_append(u"\n株式会社。\n"))
M(u"e5 3 桁以上の漢数字", u"words", doc_append(u"\n三百行。\n"))
M(u"e6 docID の形の字", u"words", doc_append(u"\nS100" + u"ABCD\n"))
M(u"e7 要点の字(盲検でな)を落とす", u"words", doc_replace(u"盲検でな", u"盲検", True))
M(u"e8 要点の字(あと知恵)を落とす", u"words", doc_replace(u"あと知恵", u"後知恵", True))
M(u"e9 封の commit を言わない", u"words", doc_replace(u"commit 52f3a228", u"commit"))
M(u"e10 禁止語を doc の check にも通す(doc の中の証明した)", u"doc", doc_append(u"\n証明" + u"した。\n"))
# f 封
M(u"f1 封の母の数の字(標本 120(母 1898))を替える", u"seal", seal_replace(u"標本 120(母 1898)", u"標本 120(母 1899)", True))
M(u"f2 封の読み方の字を替える", u"seal", seal_replace(u"**3 つの便とも 60% 以上**", u"**3 つの便とも 50% 以上**"))
M(u"f3 封の文の途中の 1 字", u"frozen", seal_replace(u"結果を見る前に固定する", u"結果を見る前に固定す"))


def check_problems(check, c):
    return guard(CHECKS[check], c)


# ======================================================================================================
# 試験
class RealRecordsTest(unittest.TestCase):
    def test_a_1_the_record_and_the_script_equal_the_pinned_sha256(self):
        self.assertEqual([], sha_problems(Ctx().texts))

    def test_a_2_the_pinned_sha256_equal_the_record_header_script(self):
        c = Ctx()
        self.assertEqual(SHA_PIN[SCRIPT_REL], c.rec[u"この script の sha256"])

    def test_b_1_the_record_is_consistent_inside(self):
        self.assertEqual([], record_problems(Ctx()))

    def test_c_1_the_document_lines_equal_the_lines_rebuilt_from_the_record(self):
        self.assertEqual([], doc_problems(Ctx()))

    def test_c_2_the_rebuilt_lines_are_the_ones_the_brief_names(self):
        c = Ctx()
        exp = dict(expected_lines(c))
        self.assertIn(u"- 当たり 5・外れ 2。", exp[u"s3 当たり外れ"])
        self.assertIn(u"範囲 105 行・項目 26 行・単位 1 行(3 つの便の内の行 132 のうち)", exp[u"s4 2"])
        self.assertIn(u"10/18(55.6%)", exp[u"s4 1"])
        self.assertIn(u"「見積り・計画」27 行(外 42 行のうち)", exp[u"s4 4"])
        self.assertIn(u"(計 174。ク を除く)", exp[u"s4 言えること"])
        self.assertIn(u"132/174(75.9%)", exp[u"参考"])

    def test_d_1_the_judgement_is_redone_from_the_seal_text_and_the_record(self):
        self.assertEqual([], judge_problems(Ctx()))

    def test_d_2_the_real_judgement_is_five_hits_and_two_misses(self):
        jd = judge(Ctx().rec, Ctx().seal)
        self.assertEqual([i for i, _t, ok in jd if not ok], [u"A-1", u"A-2"])
        self.assertEqual(5, sum(1 for _i, _t, ok in jd if ok))

    def test_e_1_the_words_are_clean(self):
        self.assertEqual([], words_problems(Ctx()))

    def test_e_2_the_seal_has_the_texts_the_document_roots_on(self):
        self.assertEqual([], seal_text_problems(Ctx()))

    def test_f_1_the_seal_is_the_text_of_the_sealed_commit(self):
        self.assertEqual([], seal_frozen_problems(Ctx().seal))

    def test_f_2_the_real_history_has_the_seal_before_the_script_before_the_record_the_seal_gate_the_document_and_this_gate(self):
        u"""文書・この門のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_f_3_the_real_order_failure_before_the_commit_is_only_the_uncommitted_files(self):
        got = order_problems_real()
        self.assertTrue(all(p.startswith(u"UNCOMMITTED:") for p in got), got)

    def test_f_4_the_order_check_lists_the_record_the_seal_gate_the_document_and_this_gate(self):
        self.assertEqual([RECORD_REL, SEAL_GATE_REL, DOC_REL, GATE_REL], order_others())
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, r)) for r in order_others() + [SCRIPT_REL]))

    def test_f_5_engine_lib_inputs_are_untouched_and_the_three_files_are_unchanged_since_their_commit(self):
        self.assertEqual([], engine_problems())


class OrderGateTest(unittest.TestCase):
    u"""順序の検査自体が、悪い順を赤にできること(使い捨ての git で)。"""

    def test_o_1_good_and_bad_orders(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        r.put("measure/s.py")
        r.commit("measure/s.py")
        for o in ("fixtures/a.json", "docs/r.md", "tests/g.py"):
            r.put(o)
        others = ["fixtures/a.json", "docs/r.md", "tests/g.py"]
        self.assertEqual([u"UNCOMMITTED:" + o for o in others], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], ["measure/s.py"], others))
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], ["measure/s.py"], others))
        r2 = PR.Repo()
        r2.put("docs/r.md")
        r2.commit("docs/r.md")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], [], ["docs/r.md"]))     # 文書が封より前


class MutationTest(unittest.TestCase):
    def test_m_1_every_check_is_green_on_the_real_records(self):
        c = Ctx()
        for name in CHECKS:
            self.assertEqual([], check_problems(name, c), name)

    def test_m_2_every_mutation_turns_its_check_red(self):
        silent, crashed = [], []
        for label, check, fn in MUTATIONS:
            c = Ctx()                                     # 毎回新しい写し(変異は 1 か所だけ)
            fn(c)
            got = check_problems(check, c)
            if not got:
                silent.append(label)
            elif got[0].startswith(u"例外"):
                crashed.append(label)
        self.assertEqual([], silent, u"赤にならなかった変異: %s" % silent)
        self.assertEqual([], crashed, u"検査が例外で落ちて赤になった変異: %s" % crashed)

    def test_m_3_each_mutation_gets_a_new_copy_and_leaves_the_real_files_alone(self):
        before = dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in (RECORD_REL, SCRIPT_REL, SEAL_REL, DOC_REL))
        c = Ctx()
        c.rec[u"便ごとの数"][u"KAM"][u"V"][u"読んだ行の数"] = -1
        c.doc = u"x"
        self.assertEqual(37, Ctx().rec[u"便ごとの数"][u"KAM"][u"V"][u"読んだ行の数"])
        self.assertNotEqual(u"x", Ctx().doc)
        self.assertEqual(before, dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in before))

    def test_m_4_the_mutation_table_covers_every_check_and_every_effect_named_in_the_brief(self):
        self.assertEqual(set(CHECKS), set(ch for _l, ch, _f in MUTATIONS))
        labels = u"\n".join(l for l, _c, _f in MUTATIONS)
        for need in (u"判定を逆にする", u"「当たり 5」を変える", u"散文の数", u"禁止語", u"漢数字", u"表の数", u"封の文の途中の 1 字", u"範囲 105 行", u"10/18(55.6%)", u"見積り・計画 27 行", u"計 174"):
            self.assertIn(need, labels)

    def test_m_5_a_hit_turned_to_a_miss_is_caught_by_the_judge_and_not_only_by_the_table(self):
        c = Ctx()
        c.rec[u"便ごとの数"][u"KAM"][u"V"][u"属性ごとの行の数"][u"範囲"] = 1                    # A-3 が外れに動く。文書の表は当たりのまま
        jd = dict((i, ok) for i, _t, ok in judge(c.rec, c.seal))
        self.assertFalse(jd[u"A-3"])


class WiringTest(unittest.TestCase):
    def test_n_1_this_gate_carries_no_docid_and_no_key(self):
        src = read(GATE_REL)
        for bad in (u"ANTHRO" + u"PIC", u"API_" + u"KEY", u"url" + u"lib", u"sock" + u"et"):
            self.assertNotIn(bad, src)

    def test_n_2_this_gate_does_not_widen_the_boundary_import_list(self):
        self.assertEqual([], SG.boundary_problems())


if __name__ == "__main__":
    unittest.main()
