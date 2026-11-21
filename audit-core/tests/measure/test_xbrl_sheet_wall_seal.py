# -*- coding: utf-8 -*-
u"""封 docs/XBRL_SHEET_WALL_SEAL_2026-11-22.md(XA0 ― 受理済みの有報の数の fact の属性は、表の「行ごと・列ごとの決め」でどれだけ決まるか。人が 1 つずつ書かなければならない欄はどれだけ残るか)の封の門。

**この門は置き場を読まない**(書類の置き場 ``~/.cache/audit-core/edinet/`` は 1 度も開かない)。通信しない。道具(Arelle)は呼ばない。subprocess を呼ぶのは git だけ。
作り物の書類(手で書いた htm)と作り物の置き場(使い捨ての folder の zip)で、置き場の読み方・数え方・記録の検査を本物の関数のまま通す。

**この門が縛るもの**

1. 封の字: 封の commit(3062223e)・封の file が commit した blob と同じ・封の決め(見る属性 7 つ・符号の 6 つの字・書式の 3 つの類のダッシュと数字の字・書く欄の式の 4・1・7・向きの選び方・最頻が並んだときの選び方・予測の境の数・限界の字)が script の定数と同じ。
2. engine は読まない・封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 表の読み方(``table > tr > td・th``・向き・colspan 4 通り・入れ子の表の内側と外側・表の外 5 通り・``<!-- -->``・大文字・自己閉じの ``td``・rowspan・``thead``・``tbody`` の取り違え・閉じタグの欠けの断り 6 通り・fact の無い file は断らない)。
4. 数え方(向き A・向き B・同じ数なら A・最頻が並ぶ線・unitRef は空の fact も含む・decimals と scale は空の fact を含まない・空の fact の比べ方・符号の 6 つの字と 3 つの字でないもの・書式の 3 つの類と書類の最頻・fact が 1 つだけの線と表・書く欄の式の項ごと)。
5. 塊(5 本と 62 本)・判定に要る数・書類 90% の境・先に自分の欠陥を疑う 4 条件・記録の形と合計と禁止のもの・置き場から数え直す ``--check``・開発の入口は 5 本だけ。
6. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。表は実行より先に書いた(予測 = 赤になるべき検査の名前)。
"""
import ast
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)


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


def load_source(src):
    u"""script の字(``src``)から module を memory の中に作る。file は読み書きしない。``__file__`` は本物の script。"""
    mod = types.ModuleType("xbrl_sheet_wall_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_SHEET_WALL_SEAL_2026-11-22.md"
SEAL_COMMIT_SHORT = "3062223e"
SCRIPT_REL = "measure/xbrl_sheet_wall_2026-11-22.py"
GATE_REL = "tests/measure/test_xbrl_sheet_wall_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/sheet_wall_2026-11-22.json"
MS = load_module(SCRIPT_REL, "xbrl_sheet_wall_script_for_seal_gate")
ORDER_FILES = (SCRIPT_REL, GATE_REL)
od = collections.OrderedDict


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def read_text(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def sha_of(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_or_none(rel):
    return sha_of(rel) if os.path.exists(os.path.join(ROOT, rel)) else None


def guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except BaseException as exc:                # noqa: BLE001
        return [u"例外: %s" % type(exc).__name__]


def stops(ms, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except ms.Stop:
        return True
    return False


def refuses(ms, fn, *a, **kw):
    u"""``Refuse`` が上がれば断った理由の字・上がらなければ None。"""
    try:
        fn(*a, **kw)
    except ms.Refuse as exc:
        return exc.reason
    return None


class Temp(object):
    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="xa0_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


def load_order_helpers():
    p = os.path.join(ROOT, "tests", "measure", "test_xbrl_p28_result.py")
    if not os.path.exists(p):
        return None
    return load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_sheet_wall_seal")


def want_eq(out_, label, got, want):
    if got != want:
        out_.append(u"%s: 得 %r 正 %r" % (label, got, want))


# ======================================================================== 作り物の書類(手で書いた字)
def fx(name=u"jppfs_cor:E0", ctx=u"C0", unit=u"JPY", dec=u"0", scale=None, sign=None, fmt=u"ixt:numdotdecimal", text=u"1,000", nil=False):
    a = u'name="%s" contextRef="%s"' % (name, ctx)
    if unit is not None:
        a += u' unitRef="%s"' % unit
    if nil:
        return u'<ix:nonFraction %s xsi:nil="true" />' % a
    if dec is not None:
        a += u' decimals="%s"' % dec
    if scale is not None:
        a += u' scale="%s"' % scale
    if fmt is not None:
        a += u' format="%s"' % fmt
    if sign is not None:
        a += u' sign="%s"' % sign
    return u"<ix:nonFraction %s>%s</ix:nonFraction>" % (a, text)


def page(body):
    return u"<html><body>\n%s\n</body></html>\n" % body


def tbl(rows, tag=u"td"):
    return u"<table>" + u"".join(u"<tr>" + u"".join(u"<%s>%s</%s>" % (tag, c, tag) for c in r) + u"</tr>" for r in rows) + u"</table>"


def loc(ms, html):
    u"""[(表, 行, 列) か None]"""
    return [(f["table"], f["row"], f["col"]) if f["table"] is not None else None for f in ms.facts_of_text(page(html))]


# 書類 1 本(手で数えた値: 下の DOC1_WANT)。表 1 = 要素が行(4 × 3 の 12・2 つが線の決めと違う)・表 2 = 要素が列(3 × 2 の 6)・表 3 = 1 つだけ(負の符号つき)・表の外 2(空 1)
def doc1_html():
    t1 = [[fx(name=u"jppfs_cor:T1E%d" % r, ctx=u"K%d" % c, unit=(u"USD" if (r, c) == (2, 1) else u"JPY"), dec=(u"-6" if (r, c) == (3, 0) else u"-3"), scale=u"3") for c in range(3)] for r in range(4)]
    t2 = [[fx(name=u"jppfs_cor:T2E%d" % e, ctx=u"L%d" % c, unit=u"shares") for e in range(3)] for c in range(2)]
    t3 = [[u"△ " + fx(name=u"jppfs_cor:T3E", ctx=u"M0", sign=u"-", text=u"5")]]
    out = fx(name=u"jppfs_cor:OutA", ctx=u"N0", fmt=u"ixt:other") + u"<p>" + fx(name=u"jppfs_cor:OutB", ctx=u"N0", nil=True) + u"</p>"
    return page(tbl(t1) + tbl(t2) + tbl(t3) + out)


DOC1_WANT = od([("fact", 21), ("nil", 1), ("outside", 2), ("inside", 19), ("tables", 3), ("tables_A", 2), ("tables_B", 1), ("tables_B_more", 1), ("tables_single", 1), ("decided", 17),
                ("r_name", 0), ("r_context", 0), ("r_unit", 1), ("r_decimals", 1), ("r_scale", 0), ("live_inside", 19), ("sign_ok", 19), ("sign_neg_no_attr", 0), ("sign_attr_no_neg", 0),
                ("format_ok", 19), ("format_bad", 0), ("full", 17), ("single_lines", 1), ("single_facts", 1), ("c_orient", 3), ("c_elem", 32), ("c_ctx", 6), ("c_formats", 1), ("c_nil", 1),
                ("c_undecided", 14), ("c_outside", 14), ("elem_lines", 8), ("ctx_lines", 6)])
DOC1_CELLS = 71
DOC1_CELLS_FULL = 57


def doc2_html():
    u"""表 1 つに fact 1 つ(書く欄 7・全部決まる 1)。"""
    return page(tbl([[fx(name=u"jppfs_cor:D2E", ctx=u"Z0")]]))


def doc5_html():
    u"""1 行 3 つ(線の決めは全部合う・符号が合わない 1・書式が合わない 1 → 全部決まるのは 1)。"""
    return page(tbl([[fx(sign=u"-", ctx=u"S0"), fx(ctx=u"S0"), fx(ctx=u"S0", fmt=u"ixt:other")]]))


def broken_html():
    u"""閉じタグの欠け(tr が閉じない)と fact。"""
    return u"<html><body><table><tr><td>%s</td></table></body></html>" % fx(name=u"jppfs_cor:BrE", ctx=u"B0")


def make_docs(d, htmls):
    u"""作り物の置き場。書類ごとに zip 1 つ(PublicDoc に xsd 1 つ・htm 1 つ・マニフェスト・画像)。ほかに有報でない zip を 1 つ。"""
    for i, h in enumerate(htmls, 1):
        with zipfile.ZipFile(os.path.join(d, "S2FAKE%02d.zip" % i), "w") as z:
            z.writestr("XBRL/PublicDoc/jpcrp030000-asr-001_E9999%d-000_2026-03-31_01_2026-06-30.xsd" % i, b"<schema/>")
            z.writestr("XBRL/PublicDoc/0100000_a_E9999%d-000_ixbrl.htm" % i, h.encode("utf-8"))
            z.writestr("XBRL/PublicDoc/manifest_PublicDoc.xml", b"<manifest/>")
            z.writestr("XBRL/PublicDoc/logo.png", b"PNG")
    with zipfile.ZipFile(os.path.join(d, "S2OTHER1.zip"), "w") as z:
        z.writestr("XBRL/PublicDoc/jpsps070000-xxx-001_E99999-000.xsd", b"<schema/>")
    return d


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XA0-1", (97, None)), ("XA0-2", (75, 95)), ("XA0-3", (98, None)), ("XA0-4", (35, 60)), ("XA0-5", (5, 30)), ("XA0-6", (None, 30)), ("XA0-7", (98, None))])
SEAL_BOUND_TEXT = od([("XA0-1", u"fact の 97% 以上"), ("XA0-2", u"fact の 75% 以上 95% 未満"), ("XA0-3", u"表の中の空でない fact の 98% 以上"), ("XA0-4", u"35% 以上 60% 未満"),
                      ("XA0-5", u"5% 以上 30% 以下"), ("XA0-6", u"30 本以下"), ("XA0-7", u"表の中の空でない fact の 98% 以上")])
SEAL_RULE_PHRASES = (
    u"**見る属性 7 つ**: `name`・`contextRef`・`unitRef`・`decimals`・`scale`・`sign`・`format`",
    u"空の fact の 3 つだけを見る".replace(u"空の fact の 3 つだけを見る", u"空の fact は `name`・`contextRef`・`unitRef` の 3 つだけを見る"),
    u"`△`・`▲`・`-`・`－`・`−`・`‐` のどれかが在れば「負」と読む",
    u"(1) `－`・`―`・`‐`・`-`・`—`・`−` だけ (2) 半角か全角の数字・`,`・`，`・`.`・`．` だけ (3) そのほか",
    u"`rowspan` は見ない",
    u"同じなら向き A",
    u"最頻が並んだときは、並んだ値のうち、書類の中で先に現れた fact の値",
    u"1(向き)+ fact の在る要素の線の数 × 4(`name`・`unitRef`・`decimals`・`scale`)+ fact の在る文脈の線の数 × 1",
    u"空の fact の数 × 1、表の中で全部決まらない fact の数 × 7、表の外の fact の数 × 7",
    u"書く欄の比** = 書く欄の数 ÷(fact の数 × 7)",
    u"便 XG0 の封 §1 と同じ 67 本(同じ並び)",
    u"並びの頭の 5 本",
    u"全部決まる fact が 90% 以上の書類は、30 本以下",
    u"全部決まる fact がちょうど 100%・表の外の fact がちょうど 0・表の中の fact が 50% 未満・断った書類が 6 本以上")
SEAL_LIMIT_PHRASES = (u"線の決めは答え", u"1 つだけの線の数は別に書く", u"`rowspan` を見ないので", u"数の fact だけ", u"無作為ではない", u"「XBRL を作れる」「専用の道具が要らない」")
LIMIT_PHRASES = (u"線の決めは答え", u"1 つだけの線の数は別に書く", u"rowspan を見ないので", u"数の fact だけ", u"無作為ではない", u"「XBRL を作れる」「専用の道具が要らない」")


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out_ = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out_.append(u"script の封の commit・path・記録の path が門と違う")
    if RECORD_REL not in seal:
        out_.append(u"封に記録の path が無い")
    if tuple(ms.ATTRS) != ("name", "contextRef", "unitRef", "decimals", "scale", "sign", "format") or tuple(ms.NIL_ATTRS) != ("name", "contextRef", "unitRef"):
        out_.append(u"見る属性が封と違う")
    if set(ms.SIGN_CHARS) != set(u"△▲-－−‐") or len(ms.SIGN_CHARS) != 6:
        out_.append(u"符号の 6 つの字が封と違う")
    if set(ms.DASH_CHARS) != set(u"－―‐-—−") or len(ms.DASH_CHARS) != 6:
        out_.append(u"書式の類 (1) のダッシュの 6 つの字が封と違う")
    if set(ms.NUM_CHARS) != set(u"0123456789０１２３４５６７８９,，.．"):
        out_.append(u"書式の類 (2) の字が封と違う")
    if ms.CELL_ATTR_PER_ELEMENT_LINE != 4 or ms.CELL_PER_CONTEXT_LINE != 1 or ms.CELL_PER_TABLE != 1 or ms.CELLS_PER_FACT != 7:
        out_.append(u"書く欄の式の数(4・1・1・7)が封と違う")
    if tuple(ms.ORIENTS) != ("A", "B") or tuple(ms.FORMAT_CLASSES) != ("1", "2", "3"):
        out_.append(u"向き・書式の類が封と違う")
    if ms.DOCS_WANT != 67 or ms.DEV_COUNT != 5:
        out_.append(u"67 本・開発の 5 本が封と違う")
    if ms.DOC_FULL_PCT != 90 or ms.SUSPECT_ABSENT_FACTS_PCT != 50 or ms.SUSPECT_DECLINED != 6:
        out_.append(u"書類 90%・欠陥を疑う条件の数が封と違う")
    if ms.PUBLICDOC != u"XBRL/PublicDoc/":
        out_.append(u"PublicDoc の場所が違う")
    for p in SEAL_RULE_PHRASES:
        if p not in seal:
            out_.append(u"封に字が無い: %s" % p[:30])
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS) or tuple(ms.BOUNDS_UPPER_EXCLUSIVE) != ("XA0-2", "XA0-4"):
        out_.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [x for x in seal.splitlines() if x.startswith(u"| %s" % k)]
        if len(row_) != 1 or t not in row_[0]:
            out_.append(u"封の予測の行の字が違う: %s" % k)
    for p in SEAL_LIMIT_PHRASES:
        if p not in seal.split(u"## §7", 1)[-1] and p not in seal.split(u"## §6", 1)[-1]:
            out_.append(u"封に限界の字が無い: %s" % p)
    for p in LIMIT_PHRASES:
        if p not in u"".join(ms.LIMITS):
            out_.append(u"限界の字が script に無い: %s" % p)
    if u"docID・会社の名・EDINET コード・file の名・fact の値・要素の名・文脈の名・表の字" not in seal:
        out_.append(u"封の記録の禁止の字が違う")
    return out_


def seal_history_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "log", "--format=%H", "--", PREFIX + SEAL_REL], stdout=subprocess.PIPE, universal_newlines=True)
    hs = [x for x in rc.stdout.split() if x]
    if len(hs) != 1 or not hs[0].startswith(SEAL_COMMIT_SHORT):
        return [u"封の file の履歴が封 %s の 1 commit でない" % SEAL_COMMIT_SHORT]
    blob = subprocess.run(["git", "-C", root, "show", "%s:%s" % (hs[0], PREFIX + SEAL_REL)], stdout=subprocess.PIPE).stdout.decode("utf-8")
    if blob != seal_text():
        return [u"今の封が封の commit の blob と違う"]
    return []


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    pr = load_order_helpers()
    others = list(ORDER_FILES) if others is None else others
    return list(pr.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others))


def engine_zero_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core"], stdout=subprocess.PIPE, universal_newlines=True)
    return [u"engine が封の後に変わっている: %s" % x for x in rc.stdout.splitlines() if x.strip()]


def record_tracked(root=REPO):
    rc = subprocess.run(["git", "-C", root, "ls-files", "--error-unmatch", PREFIX + RECORD_REL], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return rc.returncode == 0


# ======================================================================== 2. 表の読み方(置き場)
def place_problems(ms=None):
    ms = ms or MS
    out_ = []
    f1, f2, f3 = fx(ctx=u"P1"), fx(ctx=u"P2"), fx(ctx=u"P3")
    # P1: colspan=2 が 2 つ目の cell に在る行(2 行目は 1 つ目の cell が colspan=3)
    html = u"<table><tr><td>%s</td><td colspan=\"2\">%s</td><td>%s</td></tr><tr><td colspan=\"3\">%s</td><td>%s</td></tr></table>" % (f1, f2, f3, f1, f2)
    want_eq(out_, u"colspan の列の番号", loc(ms, html), [(0, 0, 0), (0, 0, 1), (0, 0, 3), (0, 1, 0), (0, 1, 3)])
    # P2: colspan の読み方 6 通り(整数でない・0・負・引用符つき・単引用符・引用符なし・大文字の属性名)
    cases = [(u'colspan="x"', 1), (u'colspan="0"', 1), (u'colspan="-1"', 1), (u"colspan='3'", 3), (u"colspan=4", 4), (u'COLSPAN="5"', 5), (u'colspan=" 2 "', 2), (u'colspan="2.5"', 1), (u"", 1)]
    for attr, n in cases:
        html = u"<table><tr><td %s>a</td><td>%s</td></tr></table>" % (attr, f1)
        want_eq(out_, u"colspan %s" % attr, loc(ms, html), [(0, 0, n)])
    # P3: 入れ子の表(外の表の行の番号は内側の tr を数えない・内側の表が閉じた後の fact は外の表)
    html = (u"<table><tr><td>%s</td><td><table><tr><td>x</td></tr><tr><td>y</td><td>%s</td></tr></table>%s</td></tr><tr><td>z</td><td>%s</td></tr></table>" % (f1, f2, f3, f1))
    want_eq(out_, u"入れ子の表", loc(ms, html), [(0, 0, 0), (1, 1, 1), (0, 0, 1), (0, 1, 1)])
    # P4: 表の外 5 通り(表より前・表より後・行と行の間・行の中で cell の外・table の直下)
    html = u"%s<table><tr><td>a</td></tr>%s<tr>%s<td>b</td></tr>%s</table>%s" % (f1, f2, f3, f1, f2)
    want_eq(out_, u"表の外", loc(ms, html), [None, None, None, None, None])
    # 入れ子の内側の表の行と行の間は、外の cell の中でも表の外
    html = u"<table><tr><td><table><tr><td>a</td></tr>%s</table></td></tr></table>" % f1
    want_eq(out_, u"内側の表の行の間", loc(ms, html), [None])
    # P5: th・大文字・自己閉じの td(列の和に数える)・td の属性
    html = u'<TABLE><TR class="a"><TH>%s</TH><td/><TD id="q">%s</TD></TR></TABLE>' % (f1, f2)
    want_eq(out_, u"th・大文字・自己閉じ", loc(ms, html), [(0, 0, 0), (0, 0, 2)])
    # P6: コメントの中の表のタグは読まない
    html = u"<!-- <table><tr><td> -->%s<table><!-- </table> --><tr><td>%s</td></tr></table>" % (f1, f2)
    want_eq(out_, u"コメント", loc(ms, html), [None, (0, 0, 0)])
    # P7: rowspan は見ない・thead と tbody と track は表のタグでない
    html = u"<table><thead><tr><th rowspan=\"2\">a</th><th>%s</th></tr></thead><tbody><tr><td>%s</td></tr></tbody></table><track>" % (f1, f2)
    want_eq(out_, u"rowspan・thead・tbody", loc(ms, html), [(0, 0, 1), (0, 1, 0)])
    # P8: 2 つの表の番号と、行の番号は表ごとに 0 から
    html = u"<table><tr><td>a</td></tr><tr><td>%s</td></tr></table><table><tr><td>%s</td></tr></table>" % (f1, f2)
    want_eq(out_, u"表の番号", loc(ms, html), [(0, 1, 0), (1, 0, 0)])
    # P9: 閉じタグの欠け 6 通りは断る
    for what, h in ((u"tr が閉じない", u"<table><tr><td>%s</td></table>" % f1), (u"tr が無い td", u"<table><td>%s</td></table>" % f1), (u"余分な閉じタグ", u"</td>%s" % f1),
                    (u"th を td で閉じる", u"<table><tr><th>%s</td></tr></table>" % f1), (u"開いたまま終わる", u"<table><tr><td>%s</td></tr>" % f1), (u"td の中の tr", u"<table><tr><td><tr><td>%s</td></tr></td></tr></table>" % f1),
                    (u"table の外の td", u"<td>%s</td>" % f1)):
        if refuses(ms, ms.facts_of_text, page(h)) != ms.R_TABLE:
            out_.append(u"断らない・理由が違う: %s" % what)
    # P10: fact の無い file の表の形は見ない(fact の在る file だけ断る)
    if ms.facts_of_text(page(u"<table><tr><td>x</td></table>")) != [] or ms.facts_of_text(page(u"<table><tr><td>%s</td></table>" % fx(text=u"a").replace(u"nonFraction", u"nonNumeric"))) != []:
        out_.append(u"fact の無い file を断る")
    if refuses(ms, ms.facts_of_files, [(u"a.htm", page(u"<table><tr><td>x</td></table>")), (u"b.htm", page(tbl([[f1]])))]) is not None:
        out_.append(u"fact の無い file を断った")
    if refuses(ms, ms.facts_of_files, [(u"a.htm", page(tbl([[f1]]))), (u"b.htm", page(u"<table><tr><td>%s</td></table>" % f2))]) != ms.R_TABLE:
        out_.append(u"fact の在る file を断らない")
    # P11: 表の番号は file をまたいで重ならない・file は名の昇順
    fs = ms.facts_of_files([(u"b.htm", page(tbl([[f2]]))), (u"a.htm", page(tbl([[f1]])))])
    want_eq(out_, u"file をまたぐ表の番号", [(f["table"], f["attrs"]["contextRef"]) for f in fs], [((0, 0), u"P1"), ((1, 0), u"P2")])
    return out_


def facts_problems(ms=None):
    ms = ms or MS
    out_ = []
    # 種類: nonFraction だけ(nonNumeric・footnote は数えない)・ix:header の中は数えない・開きタグの順
    hdr = u'<ix:header><ix:hidden><ix:nonNumeric name="jpcrp_cor:H" contextRef="C0">h</ix:nonNumeric><ix:nonFraction name="jppfs_cor:HF" contextRef="C0" unitRef="JPY" decimals="0">9</ix:nonFraction></ix:hidden></ix:header>'
    html = hdr + u'<ix:nonNumeric name="jpcrp_cor:T" contextRef="C0">題</ix:nonNumeric><table><tr><td>' + fx(name=u"jppfs_cor:F1", ctx=u"Q1") + u'</td></tr></table><ix:nonNumeric name="jpcrp_cor:U" contextRef="C0">x</ix:nonNumeric>' + fx(name=u"jppfs_cor:F2", ctx=u"Q2")
    fs = ms.facts_of_text(page(html))
    want_eq(out_, u"nonFraction だけ・header の中を除く", [f["attrs"]["name"] for f in fs], [u"jppfs_cor:F1", u"jppfs_cor:F2"])
    if [f["table"] for f in fs] != [0, None]:
        out_.append(u"header・nonNumeric があって表の位置がずれる")
    # 空の fact(xsi:nil が true だけ)
    fs = ms.facts_of_text(page(fx(nil=True) + u'<ix:nonFraction name="n" contextRef="c" unitRef="u" decimals="0" xsi:nil="false">1</ix:nonFraction>' + fx()))
    want_eq(out_, u"空の fact", [f["nil"] for f in fs], [True, False, False])
    # 字: タグを落とす・前後の空白を落とす・実体参照は直さない
    fs = ms.facts_of_text(page(fx(text=u" <span>1</span>,<b>2</b>\n") + fx(text=u"&#160;5")))
    want_eq(out_, u"fact の字", [f["text"] for f in fs], [u"1,2", u"&#160;5"])
    # 符号の字の取り方: cell の開きタグの終わりから fact の開きタグの始まりまで(タグを除く)
    fs = ms.facts_of_text(page(u'<table><tr><td>前の cell △</td><td class="x">a<span>▲</span> ' + fx() + u'</td></tr></table>'))
    want_eq(out_, u"cell と fact の間の字", [f["between"] for f in fs], [u"a▲ "])
    # 表 F との対応が崩れたら断る(作り物の剥がしで確かめる)
    fake = types.SimpleNamespace(IX_TAG_RE=ms.B.IX_TAG_RE, Decline=ms.B.Decline, strip_text=lambda t: (u"", [dict(kind="nonFraction", start=0, end=0, attrs={})] * 3, None))
    real = ms.B
    ms.B = fake
    try:
        r = refuses(ms, ms.facts_of_text, page(fx()))
    finally:
        ms.B = real
    if r != ms.R_ALIGN:
        out_.append(u"表 F の行の数が合わないのに断らない")
    fake = types.SimpleNamespace(IX_TAG_RE=ms.B.IX_TAG_RE, Decline=ms.B.Decline, strip_text=lambda t: (u"", [dict(kind="nonNumeric", start=0, end=0, attrs={})], None))
    ms.B = fake
    try:
        r = refuses(ms, ms.facts_of_text, page(fx()))
    finally:
        ms.B = real
    if r != ms.R_ALIGN:
        out_.append(u"表 F の行の種類が合わないのに断らない")
    # 便 XB0 の断りは固定の理由のまま断る・知らない例外も断る
    r = refuses(ms, ms.facts_of_text, u'<ix:nonFraction name="a" contextRef="b" zzz="1">1</ix:nonFraction>')
    if not r or r == ms.R_EXC:
        out_.append(u"便 XB0 の断りの理由が渡らない: %r" % r)
    return out_


# ======================================================================== 3. 数え方
def item(row, col, name=u"N", ctx=u"C", unit=u"JPY", dec=u"0", scale=None, nil=False):
    a = {"name": name, "contextRef": ctx}
    if unit is not None:
        a["unitRef"] = unit
    if not nil:
        if dec is not None:
            a["decimals"] = dec
        if scale is not None:
            a["scale"] = scale
    return dict(attrs=a, nil=nil, text=u"1", table=0, row=row, col=col, between=u"")


def mode_problems(ms=None):
    ms = ms or MS
    out_ = []
    want_eq(out_, u"最頻", ms.mode_first([u"a", u"b", u"b"]), u"b")
    want_eq(out_, u"最頻が並ぶ(先に現れた値)", ms.mode_first([u"q", u"p", u"p", u"q"]), u"q")
    want_eq(out_, u"最頻が並ぶ 3 つ", ms.mode_first([u"z", u"y", u"x"]), u"z")
    want_eq(out_, u"値が無い", ms.mode_first([]), ms.NOMODE)
    want_eq(out_, u"None も 1 つの値", ms.mode_first([None, None, u"1"]), None)
    # 線の決め: unitRef の最頻が並ぶ(線の上の最初の fact の値)。向き A は行が要素の線
    its = [item(0, 0, unit=u"U2"), item(0, 1, unit=u"U1"), item(0, 2, unit=u"U1"), item(0, 3, unit=u"U2")]
    want_eq(out_, u"最頻が並ぶ線の unitRef", [m[2] for m in ms.mismatches(its, "A")], [False, True, True, False])
    # unitRef は空の fact も含む(空 2 つ U1・空でない 1 つ U2 → 決めは U1)
    its = [item(0, 0, unit=u"U1", nil=True), item(0, 1, unit=u"U1", nil=True), item(0, 2, unit=u"U2")]
    want_eq(out_, u"unitRef は空の fact も含む", [m[2] for m in ms.mismatches(its, "A")], [False, False, True])
    # decimals・scale は空でない fact だけ(空 2 つは decimals 無し・空でない 3 つは 0,0,-3 → 決めは 0)・空の fact は decimals・scale で違うと数えない
    its = [item(0, 0, nil=True), item(0, 1, nil=True), item(0, 2, dec=u"0", scale=u"3"), item(0, 3, dec=u"0", scale=u"3"), item(0, 4, dec=u"-3", scale=u"6")]
    mm = ms.mismatches(its, "A")
    want_eq(out_, u"decimals は空でない fact だけで決める", [m[3] for m in mm], [False, False, False, False, True])
    want_eq(out_, u"scale は空でない fact だけで決める", [m[4] for m in mm], [False, False, False, False, True])
    # 空の fact も name・contextRef・unitRef は見る
    its = [item(0, 0, name=u"A"), item(0, 1, name=u"A"), item(0, 2, name=u"B", nil=True)]
    want_eq(out_, u"空の fact の name", [m[0] for m in ms.mismatches(its, "A")], [False, False, True])
    its = [item(0, 0, ctx=u"X"), item(1, 0, ctx=u"X"), item(2, 0, ctx=u"Y", nil=True)]
    want_eq(out_, u"空の fact の contextRef(向き A は列が文脈の線)", [m[1] for m in ms.mismatches(its, "A")], [False, False, True])
    # 向き B は列が要素の線・行が文脈の線
    its = [item(0, 0, name=u"A", ctx=u"X"), item(1, 0, name=u"A", ctx=u"Y"), item(0, 1, name=u"B", ctx=u"X"), item(1, 1, name=u"B", ctx=u"Y")]
    want_eq(out_, u"向き B で全部決まる", ms.decided_count(ms.mismatches(its, "B")), 4)
    want_eq(out_, u"同じ表を向き A で見ると 1 つだけ(最頻が並んで先の fact に決まる)", ms.decided_count(ms.mismatches(its, "A")), 1)
    return out_


def acc_of(html, ms=None):
    ms = ms or MS
    return ms.count_facts(ms.facts_of_text(html))


def count_problems(ms=None):
    ms = ms or MS
    out_ = []
    acc = acc_of(doc1_html(), ms)
    for k, v in DOC1_WANT.items():
        if acc[k] != v:
            out_.append(u"書類 1 の %s: 得 %r 正 %r" % (k, acc[k], v))
    want_eq(out_, u"書く欄の数", ms.cells_of(acc), DOC1_CELLS)
    want_eq(out_, u"全部決まる場合の書く欄の数", ms.cells_if_all_decided(acc), DOC1_CELLS_FULL)
    if list(acc) != list(ms.ACC_KEYS):
        out_.append(u"数の欄の並びが違う")
    # 向きの選び方: 同じ数なら向き A(1 つだけの表・対角の 2 つ)・B が多ければ B
    a1 = acc_of(page(tbl([[fx()]])), ms)
    want_eq(out_, u"1 つだけの表", (a1["tables_A"], a1["tables_B"], a1["tables_single"], a1["single_lines"], a1["full"], ms.cells_of(a1)), (1, 0, 1, 1, 1, 7))
    a2 = acc_of(page(tbl([[fx(name=u"jppfs_cor:G0", ctx=u"G0"), u""], [u"", fx(name=u"jppfs_cor:G1", ctx=u"G1")]])), ms)
    want_eq(out_, u"同じ数なら向き A", (a2["tables_A"], a2["tables_B"], a2["tables_B_more"], a2["decided"], a2["single_lines"], a2["elem_lines"], a2["ctx_lines"], a2["tables_single"]), (1, 0, 0, 2, 2, 2, 2, 0))
    # 表の外だけの書類・fact が無い書類
    a3 = acc_of(page(fx() + fx(nil=True)), ms)
    want_eq(out_, u"表の外だけ", (a3["fact"], a3["outside"], a3["inside"], a3["tables"], a3["full"], ms.cells_of(a3)), (2, 2, 0, 0, 0, 1 + 1 + 14))
    a4 = acc_of(page(u"<p>x</p>"), ms)
    want_eq(out_, u"fact が無い書類", (a4["fact"], ms.cells_of(a4)), (0, 0))
    # 全部決まるは符号・書式が合って初めて(線の決めは全部合うが符号が合わない fact は全部決まらない)
    a5 = acc_of(page(tbl([[fx(sign=u"-", ctx=u"S0"), fx(ctx=u"S0"), fx(ctx=u"S0", fmt=u"ixt:other")]])), ms)
    want_eq(out_, u"符号・書式が合わない fact は全部決まらない", (a5["decided"], a5["sign_attr_no_neg"], a5["format_bad"], a5["full"]), (3, 1, 1, 1))
    return out_


def sign_problems(ms=None):
    ms = ms or MS
    out_ = []
    for ch in u"△▲-－−‐":
        a = acc_of(page(tbl([[u"%s %s" % (ch, fx(sign=u"-"))]])), ms)
        if (a["sign_ok"], a["sign_neg_no_attr"], a["sign_attr_no_neg"]) != (1, 0, 0):
            out_.append(u"負の字 %r が負と読まれない(sign あり)" % ch)
        a = acc_of(page(tbl([[u"%s%s" % (ch, fx())]])), ms)
        if (a["sign_ok"], a["sign_neg_no_attr"], a["sign_attr_no_neg"]) != (0, 1, 0):
            out_.append(u"負の字 %r が負と読まれない(sign なし)" % ch)
    for ch in (u"＋", u"+", u"ー", u"–", u"〜", u"▽"):
        a = acc_of(page(tbl([[u"%s%s" % (ch, fx())]])), ms)
        if (a["sign_ok"], a["sign_neg_no_attr"], a["sign_attr_no_neg"]) != (1, 0, 0):
            out_.append(u"負でない字 %r が負と読まれた" % ch)
    a = acc_of(page(tbl([[u"△" + fx(sign=u"+")]])), ms)
    want_eq(out_, u"sign が - でなければ sign が在るに数えない", (a["sign_ok"], a["sign_neg_no_attr"], a["sign_attr_no_neg"]), (0, 1, 0))
    a = acc_of(page(tbl([[fx(sign=u"+")]])), ms)
    want_eq(out_, u"sign が + で負と読めない", (a["sign_ok"], a["sign_neg_no_attr"], a["sign_attr_no_neg"]), (1, 0, 0))
    a = acc_of(page(tbl([[fx(sign=u"-")]])), ms)
    want_eq(out_, u"sign が - で負と読めない", (a["sign_ok"], a["sign_neg_no_attr"], a["sign_attr_no_neg"]), (0, 0, 1))
    a = acc_of(page(tbl([[fx()]])), ms)
    want_eq(out_, u"sign なしで負でない", (a["sign_ok"], a["sign_neg_no_attr"], a["sign_attr_no_neg"]), (1, 0, 0))
    # 前の cell の字・fact の後ろの字・fact の中の字は数えない
    a = acc_of(page(u"<table><tr><td>△</td><td>" + fx() + u"</td></tr></table>"), ms)
    want_eq(out_, u"前の cell の △", a["sign_ok"], 1)
    a = acc_of(page(u"<table><tr><td>" + fx() + u"△</td></tr></table>"), ms)
    want_eq(out_, u"fact の後ろの △", a["sign_ok"], 1)
    a = acc_of(page(tbl([[fx(text=u"△1")]])), ms)
    want_eq(out_, u"fact の中の △", a["sign_ok"], 1)
    # 空の fact は符号を見ない・表の外の fact は符号の分母に入らない
    a = acc_of(page(tbl([[u"△" + fx(nil=True)]]) + u"△" + fx()), ms)
    want_eq(out_, u"空の fact・表の外は符号の分母に入らない", (a["live_inside"], a["sign_ok"], a["sign_neg_no_attr"]), (0, 0, 0))
    return out_


def format_problems(ms=None):
    ms = ms or MS
    out_ = []
    dash = [fx(text=t, fmt=u"zd") for t in (u"－", u"―", u"‐", u"-", u"—", u"−")] + [fx(text=u"-", fmt=u"other")]
    nums = [fx(text=t, fmt=u"nd") for t in (u"１２,３４", u"1.5", u"1，2")] + [fx(text=u"9．9", fmt=u"x")]
    rest = [fx(text=u"n/a", fmt=u"tx"), fx(text=u"abc", fmt=u"tx"), fx(text=u"", fmt=u"ty"), fx(text=u"1 2", fmt=u"tx")]
    a = acc_of(page(tbl([dash + nums + rest])), ms)
    want_eq(out_, u"書式が合う・合わない", (a["format_ok"], a["format_bad"], a["c_formats"]), (12, 3, 3))
    # 最頻が並んだ類は、書類の中で先に現れた値(a は p・b は q → 先の p が最頻)
    a = acc_of(page(tbl([[fx(text=u"a", fmt=u"p"), fx(text=u"b", fmt=u"q")]])), ms)
    want_eq(out_, u"書式の最頻が並ぶ", (a["format_ok"], a["format_bad"]), (1, 1))
    # format の属性が無いことも 1 つの値(最頻が無い)
    a = acc_of(page(tbl([[fx(fmt=None), fx(fmt=None), fx(fmt=u"nd")]])), ms)
    want_eq(out_, u"format が無いことも 1 つの値", (a["format_ok"], a["format_bad"]), (2, 1))
    # 書類の最頻は表の外の fact も含む(表の中 1 つ nd・表の外 2 つ od → 最頻は od)
    a = acc_of(page(tbl([[fx(fmt=u"nd")]]) + fx(fmt=u"od") + fx(fmt=u"od")), ms)
    want_eq(out_, u"最頻は表の外の fact も含む", (a["format_ok"], a["format_bad"]), (0, 1))
    # 書式の類の数: 空の fact は数えない
    a = acc_of(page(tbl([[fx(), fx(nil=True)]])), ms)
    want_eq(out_, u"空の fact は書式の類に数えない", a["c_formats"], 1)
    want_eq(out_, u"書式の類の数(書類の中の全部)", acc_of(page(tbl([[fx()]]) + fx(text=u"－")), ms)["c_formats"], 2)
    want_eq(out_, u"format_class", [ms.format_class(s) for s in (u"－", u"", u"12", u"1a", u"-1", u"△")], ["1", "3", "2", "3", "3", "3"])
    return out_


# ======================================================================== 4. 塊・判定・記録
def chunk_inputs(ms=None):
    ms = ms or MS
    a1, a2, a5 = acc_of(doc1_html(), ms), acc_of(doc2_html(), ms), acc_of(doc5_html(), ms)
    rows = [ms.doc_row(1, a1, u""), ms.doc_row(2, None, ms.R_TABLE), ms.doc_row(3, a2, u""), ms.doc_row(4, a5, u"")]
    return rows, [a1, None, a2, a5]


def chunk_problems(ms=None):
    ms = ms or MS
    out_ = []
    rows, accs = chunk_inputs(ms)
    want_eq(out_, u"書類の行", [list(rows[0].values()), list(rows[1].values()), list(rows[3].values())], [[1, False, u"", 21, 2, 17, 71], [2, True, ms.R_TABLE, None, None, None, None], [4, False, u"", 3, 0, 1, 23]])
    ch = ms.chunk_of(rows, accs)
    want = [(u"書類の数", 4), (u"断った書類の数", 1), (u"断らなかった書類の数", 3), (u"fact の数", 25), (u"空の fact の数", 1), (u"表の外の fact の数", 2), (u"表の中の fact の数", 23), (u"fact の在る表の数", 5),
            (u"向き A を選んだ表の数", 4), (u"向き B を選んだ表の数", 1), (u"向き B の方が決まる fact が多かった表の数", 1), (u"fact が 1 つだけの表の数", 2), (u"表の決めで決まる fact の数", 21),
            (u"表の中の空でない fact の数", 23), (u"符号が合う fact の数", 22), (u"符号が合わない fact の数(sign が - だが負と読めない)", 1), (u"符号が合わない fact の数(負と読んだが sign が - でない)", 0),
            (u"書式が合う fact の数", 22), (u"書式が合わない fact の数", 1), (u"全部決まる fact の数", 19), (u"書く欄の数", 101), (u"fact の数 × 7", 175),
            (u"表の中の fact が全部決まる場合の書く欄の数", 73), (u"線の上の fact が 1 つだけの要素の線の数", 2), (u"その線の上の fact の数", 2),
            (u"全部決まる fact が 90% 以上の書類の数", 1), (u"fact が 1 つ以上在る書類の数(断らなかった)", 3), (u"要素の線の数(fact の在る)", 10), (u"文脈の線の数(fact の在る)", 10)]
    for k, v in want:
        if ch[k] != v:
            out_.append(u"塊の %s: 得 %r 正 %r" % (k, ch[k], v))
    want_eq(out_, u"断った理由ごとの数", dict(ch[u"断った理由ごとの数"]), {ms.R_TABLE: 1})
    want_eq(out_, u"書く欄の比", (ch[u"書く欄の比"][u"数"], ch[u"書く欄の比"][u"分母"], ch[u"書く欄の比"][u"%"]), (101, 175, 57.7))
    want_eq(out_, u"全部決まる場合の比", ch[u"表の中の fact が全部決まる場合の比"][u"%"], 41.7)
    want_eq(out_, u"書く欄の数(項ごと)の合計", sum(ch[u"書く欄の数(項ごと)"].values()), ch[u"書く欄の数"])
    want_eq(out_, u"理由ごとの数(重ねて数える)", list(ch[u"決まらなかった理由ごとの fact の数(重ねて数える)"].values()), [0, 0, 1, 1, 0])
    # 書類 90% の境(ちょうど 90% は含む)
    for f, full, want_n in ((10, 9, 1), (10, 8, 0), (20, 18, 1), (21, 18, 0), (0, 0, 0)):
        want_eq(out_, u"90%% の境 %d/%d" % (full, f), ms.docs_full([{"fact": f, "full": full}]), want_n)
    want_eq(out_, u"断った書類は 90% に数えない", ms.docs_full([None, {"fact": 1, "full": 1}]), 1)
    # 判定に要る数
    j = ms.judged(ch, accs)
    got = [(k.split(u" ")[0], v[u"数"], v[u"分母"], v[u"%"]) if u"%" in v else (k.split(u" ")[0], v[u"書類"], v[u"分母"], None) for k, v in j.items()]
    want_eq(out_, u"判定に要る数", got, [(u"XA0-1", 23, 25, 92.0), (u"XA0-2", 19, 25, 76.0), (u"XA0-3", 22, 23, 95.7), (u"XA0-4", 101, 175, 57.7), (u"XA0-5", 1, 5, 20.0), (u"XA0-6", 1, 3, None), (u"XA0-7", 22, 23, 95.7)])
    return out_


def suspicion_problems(ms=None):
    ms = ms or MS
    base = {u"fact の数": 100, u"全部決まる fact の数": 80, u"表の外の fact の数": 3, u"表の中の fact の数": 97, u"断った書類の数": 0, u"断らなかった書類の数": 5}
    out_ = []
    want_eq(out_, u"何も当たらない", ms.suspicions(base), [])
    for what, change in ((u"全部決まる fact がちょうど 100%", {u"全部決まる fact の数": 100}), (u"表の外の fact がちょうど 0", {u"表の外の fact の数": 0, u"表の中の fact の数": 100}),
                         (u"表の中の fact が 50% 未満", {u"表の中の fact の数": 49, u"表の外の fact の数": 51}), (u"断った書類が 6 本以上", {u"断った書類の数": 6})):
        got = ms.suspicions(dict(base, **change))
        if got != [what]:
            out_.append(u"%s: 得 %r" % (what, got))
    # 境: 50% ちょうどと断った 5 本は当たらない
    want_eq(out_, u"表の中が 50% ちょうど", ms.suspicions(dict(base, **{u"表の中の fact の数": 50, u"表の外の fact の数": 50})), [])
    want_eq(out_, u"断った 5 本", ms.suspicions(dict(base, **{u"断った書類の数": 5})), [])
    return out_


def build_args(d, htmls=None):
    htmls = [doc1_html(), broken_html(), doc5_html()] if htmls is None else htmls
    docs = os.path.join(d, "docs")
    os.makedirs(docs)
    make_docs(docs, htmls)
    return docs


def record_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        docs = build_args(d)
        rec, secret = ms.build_record(docs, want=3, dev_count=1)
        keys = list(rec)
        if keys[:5] != [u"seal", u"封の commit", u"step", u"この script の sha256", u"材料"] or keys[5:8] != [u"書類", u"開発の 5 本", u"本番だけの 62 本"] or keys[-1] != u"限界":
            out_.append(u"記録の欄の並びが違う: %s" % keys)
        want_eq(out_, u"書類の数", len(rec[u"書類"]), 3)
        want_eq(out_, u"開発の塊は 1 本目だけ", (rec[u"開発の 5 本"][u"書類の数"], rec[u"開発の 5 本"][u"fact の数"], rec[u"開発の 5 本"][u"書く欄の数"]), (1, 21, 71))
        want_eq(out_, u"本番の塊は 2 本目から(断った 1 本)", (rec[u"本番だけの 62 本"][u"書類の数"], rec[u"本番だけの 62 本"][u"断った書類の数"], rec[u"本番だけの 62 本"][u"fact の数"], rec[u"本番だけの 62 本"][u"書く欄の数"]), (2, 1, 3, 23))
        want_eq(out_, u"断った理由", dict(rec[u"本番だけの 62 本"][u"断った理由ごとの数"]), {ms.R_TABLE: 1})
        want_eq(out_, u"書類の行", [list(r.values()) for r in rec[u"書類"]], [[1, False, u"", 21, 2, 17, 71], [2, True, ms.R_TABLE, None, None, None, None], [3, False, u"", 3, 0, 1, 23]])
        jk = [k for k in rec if k.startswith(u"予測の判定に要る数")]
        if len(jk) != 1 or rec[jk[0]][list(rec[jk[0]])[1]][u"数"] != 1:
            out_.append(u"判定に要る数が本番の塊(62 本)だけから作られていない")
        want_eq(out_, u"script の sha256", rec[u"この script の sha256"], sha_of(SCRIPT_REL))
        want_eq(out_, u"材料", (rec[u"材料"][u"書類の本数"], rec[u"材料"][u"開発の 5 本の番号"], rec[u"材料"][u"見る属性"], rec[u"材料"][u"script の決めの字"]), (3, [1], list(ms.ATTRS), list(ms.RULES)))
        text = ms.dumps(rec)
        for t in (u"12,345,678", u"jppfs_cor", u"T1E0", u"K1", u".htm", u"E9999", u"S2FAKE"):
            if t in text:
                out_.append(u"記録に禁止の字が在る: %s" % t)
        if u"CurrentYear" in text:
            out_.append(u"文脈の名が在る")
        # secret(要素の局所名・文脈の名・docID・EDINET コード)
        if not {u"T1E0", u"K1", u"OutA"} <= set(secret[1]) or u"S2FAKE01" not in secret[2] or u"E99991" not in secret[3]:
            out_.append(u"secret に要素の名・文脈の名・docID・EDINET コードが入っていない")
        ms.verify_record(rec, text, 3, 1)
        # verify が壊れた記録を止める
        import copy
        bad = []
        for what, fn in ((u"書類の fact の数", lambda r: r[u"書類"][0].__setitem__(u"fact の数", 22)), (u"塊の fact の数", lambda r: r[u"開発の 5 本"].__setitem__(u"fact の数", 22)),
                         (u"書く欄の数", lambda r: r[u"本番だけの 62 本"].__setitem__(u"書く欄の数", 8)), (u"断った理由", lambda r: r[u"書類"][1].__setitem__(u"断った理由", u"")),
                         (u"番号", lambda r: r[u"書類"][2].__setitem__(u"番号", 9)), (u"向きの数", lambda r: r[u"開発の 5 本"].__setitem__(u"向き B を選んだ表の数", 0)),
                         (u"符号の数", lambda r: r[u"開発の 5 本"].__setitem__(u"符号が合う fact の数", 1)), (u"書式の数", lambda r: r[u"開発の 5 本"].__setitem__(u"書式が合う fact の数", 1)),
                         (u"90% の書類", lambda r: r[u"開発の 5 本"].__setitem__(u"全部決まる fact が 90% 以上の書類の数", 1)), (u"項ごと", lambda r: r[u"開発の 5 本"][u"書く欄の数(項ごと)"].__setitem__(u"書式の類の数", 9)),
                         (u"断った理由ごと", lambda r: r[u"本番だけの 62 本"].__setitem__(u"断った理由ごとの数", od())), (u"全部決まる", lambda r: r[u"書類"][0].__setitem__(u"全部決まる fact の数", 3))):
            r2 = copy.deepcopy(rec)
            fn(r2)
            if not stops(ms, ms.verify_record, r2, None, 3, 1):
                bad.append(what)
        if bad:
            out_.append(u"verify_record が止めない: %s" % bad)
        if not stops(ms, ms.verify_record, rec, text, 67, 1):
            out_.append(u"書類が 67 本でないのに verify_record が止めない")
        # run → 記録 → check(置き場から数え直す)
        rp = os.path.join(d, "rec", "r.json")
        if not stops(ms, ms.run, docs=docs, out=rp, want=67, say=lambda *a: None) or os.path.exists(rp):
            out_.append(u"67 本でないのに run が止まらない(か記録を書いた)")
        lines = []
        rec2 = ms.run(docs=docs, out=rp, want=3, say=lambda *a: None, dev_count=1, progress=lines.append)
        if not os.path.exists(rp) or ms.dumps(rec2) != read_text(rp) or ms.dumps(rec2) != ms.dumps(rec) or len(lines) != 3:
            out_.append(u"記録が書かれていない・字が違う・進みを出さない")
        if not stops(ms, ms.run, docs=docs, out=rp, want=3, say=lambda *a: None, dev_count=1):
            out_.append(u"記録が既に在るのに run が止まらない")
        ms.check(docs=docs, rec_path=rp, want=3, say=lambda *a: None, dev_count=1)
        # 置き場が変われば check が止まる(数え直している)
        d2 = os.path.join(d, "docs2")
        os.makedirs(d2)
        make_docs(d2, [doc1_html(), broken_html(), page(tbl([[fx(ctx=u"Z0"), fx(ctx=u"Z1")]]))])
        if not stops(ms, ms.check, docs=d2, rec_path=rp, want=3, say=lambda *a: None, dev_count=1):
            out_.append(u"置き場が変わったのに check が止まらない")
        # 記録の字が書き換えられていれば止まる
        rp3 = os.path.join(d, "rec", "r3.json")
        with io.open(rp3, "w", encoding="utf-8") as fh:
            fh.write(read_text(rp).replace(u'"fact の数": 21', u'"fact の数": 20', 1))
        if not stops(ms, ms.check, docs=docs, rec_path=rp3, want=3, say=lambda *a: None, dev_count=1):
            out_.append(u"記録を書き換えたのに check が止まらない")
        if not stops(ms, ms.check, docs=docs, rec_path=os.path.join(d, "none.json"), want=3, say=lambda *a: None):
            out_.append(u"記録が無いのに check が止まらない")
    return out_


def clean_problems(ms=None):
    ms = ms or MS
    out_ = []
    ok = od([(u"書類", [od([(u"番号", 1), (u"断った理由", u"固定の理由"), (u"fact の数", 5)])]), (u"hash", u"a" * 64)])
    secret = (set(), {u"NetSalesOfX", u"CurrentYearInstant"}, [u"zzdoc"], {u"E99991"})
    if stops(ms, ms.check_clean, ok, ms.dumps(ok), secret):
        out_.append(u"きれいな記録で止まる")
    cases = [
        (u"禁止の欄(docid)", od([(u"DocID", 1)])), (u"禁止の欄(company)", od([(u"company", 1)])), (u"禁止の欄(label)", od([(u"label", 1)])), (u"禁止の欄(element)", od([(u"element", 1)])),
        (u"禁止の欄(name)", od([(u"name", 1)])), (u"EDINET コードの形", od([(u"x", u"id E12345 x")])), (u"docID の形", od([(u"x", u"S100ABCD")])),
        (u"材料の docID", od([(u"x", u"id zzdoc.")])), (u"材料の EDINET コード", od([(u"x", u"E99991")])), (u"要素の名", od([(u"x", u"理由 NetSalesOfX")])),
        (u"文脈の名", od([(u"x", u"CurrentYearInstant")])), (u"file の名(htm)", od([(u"x", u"0101010_honbun.htm")])), (u"file の名(xsd)", od([(u"x", u"jpcrp030000-asr-001.xsd")]))]
    for what, rec in cases:
        if not stops(ms, ms.check_clean, rec, ms.dumps(rec), secret):
            out_.append(u"%s が止まらない" % what)
        if not stops(ms, ms.record_text, rec, secret):
            out_.append(u"%s が record_text で止まらない" % what)
    with Temp() as d:
        p = os.path.join(d, "r.json")
        if not stops(ms, ms.write_record, p, od([(u"x", u"E12345")])) or os.path.exists(p):
            out_.append(u"禁止の字が在る記録を書いた(書く前の検査)")
        good = od([(u"x", 1)])
        ms.write_record(p, good)
        if not stops(ms, ms.write_record, p, good):
            out_.append(u"記録が既に在るのに書き直せる")
        orig = ms.write_exclusive
        q = os.path.join(d, "q.json")
        ms.write_exclusive = lambda path, data: orig(path, data + b" E12345")
        try:
            stopped = stops(ms, ms.write_record, q, good)
        finally:
            ms.write_exclusive = orig
        if not stopped or os.path.exists(q):
            out_.append(u"書いた後の検査が止めない(か file を消さない)")
    return out_


def devrun_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        docs = os.path.join(d, "docs")
        os.makedirs(docs)
        make_docs(docs, [doc1_html()] * 7)
        lines = []
        ch, accs = ms.dev_run(docs_dir=docs, say=lines.append)
        want_eq(out_, u"開発の入口は 5 本だけ", (ch[u"書類の数"], len(accs), sum(1 for x in lines if x.startswith(u"doc "))), (5, 5, 5))
        want_eq(out_, u"開発の入口の数", (ch[u"fact の数"], ch[u"書く欄の数"]), (105, 355))
        if not any(u"先に自分の欠陥を疑う場合に当たったもの" in x for x in lines):
            out_.append(u"欠陥を疑う場合の行を出さない")
        if os.path.exists(os.path.join(d, "docs", "sheet_wall_2026-11-22.json")):
            out_.append(u"開発の入口が記録を書いた")
        want_eq(out_, u"dev_docs の本数", len(ms.dev_docs(docs, 2)), 2)
    return out_


def decode_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        p = os.path.join(d, "a.zip")
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("XBRL/PublicDoc/0100000_a_ixbrl.htm", b"<html>\xff\xfe\x80</html>")
        if refuses(ms, ms.doc_texts, p) != ms.R_ENC:
            out_.append(u"符号化が読めない file を断らない")
        acc, reason = ms.count_zip(p)
        if acc is not None or reason != ms.R_ENC:
            out_.append(u"count_zip が断った理由を返さない")
        p2 = os.path.join(d, "b.zip")
        with zipfile.ZipFile(p2, "w") as z:
            z.writestr("XBRL/PublicDoc/0200000_b_ixbrl.htm", page(tbl([[fx()]])).encode("utf-8"))
            z.writestr("XBRL/PublicDoc/0100000_a_ixbrl.htm", page(tbl([[fx(ctx=u"A")]])).encode("utf-8"))
            z.writestr("XBRL/PublicDoc/sub/x.png", b"\xff\xfe")
            z.writestr("XBRL/AuditDoc/audit_ixbrl.htm", b"\xff")
            z.writestr("XBRL/PublicDoc/y.xbrl", b"\xff")
        names = [n for n, _t in ms.doc_texts(p2)]
        want_eq(out_, u"PublicDoc の htm だけを名の昇順で", names, [u"XBRL/PublicDoc/0100000_a_ixbrl.htm", u"XBRL/PublicDoc/0200000_b_ixbrl.htm"])
        acc, reason = ms.count_zip(p2)
        if acc is None or acc["fact"] != 2 or acc["tables"] != 2:
            out_.append(u"count_zip が数えない")
    return out_


# ======================================================================== 5. 配線
STDLIB_OK = ("__future__", "argparse", "collections", "importlib", "io", "json", "os", "re", "sys", "time")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "adapters", "core", "audit_core", "zipfile", "csv", "xml", "subprocess", "shutil", "tempfile")
#: 前の便の script の関数を呼ぶ(写さない): (module の名, 関数の名)
CALLED = (("B", "strip_text"), ("B", "load_package"), ("B", "is_public_htm"), ("B", "dev_docs"), ("W", "select_docs"), ("W", "order_sha256"), ("W", "check_clean"))
NOT_COPIED = ("select_docs", "order_sha256", "strip_text", "load_package", "is_public_htm", "build_text", "parse_attrs", "check_clean_base", "norm_label", "pct1", "sha256_file", "sha256_bytes", "write_package",
              "strip_tables", "build_tables", "facts_same", "sounds_same")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
#: 別の門の規準の字(関数の名・呼び出し・説明文のどこにも使わない)
HARNESS_WORDS = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(", "tampered", u"注入")
OTHER_NAMES = (u"_xb0_inline_build_2026_11_21", u"_xt0_inline_build_2026_11_21", u"_xp0_taxonomy_build_2026_11_22", u"_xt0_taxonomy_build_2026_11_22", u"_xv0_tag_wall_2026_11_21", u"_xg1_tag_wall_2026_11_21",
               u"_xb0_tag_wall_2026_11_21", u"_xb0_tag_narrow", u"_xb0_edinet_validate_2026_11_21")


def attr_names(tree):
    return [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]


def import_problems(src=None):
    u"""script の import は標準ライブラリだけ(engine・zipfile・csv・subprocess を読まない)。前の便の script は B・W から呼び写さない。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out_ = []
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.Import):
            names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            names = [(n.module or u"")]
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("__import__", "eval", "exec"):
            out_.append(u"動的な import・eval・exec の呼び出し")
        for nm in names:
            top = nm.split(".")[0]
            if top in NETWORK_MODULES:
                out_.append(u"許さない module を import している: %s" % nm)
            elif top not in STDLIB_OK:
                out_.append(u"許す一覧に無い module: %s" % nm)
    attrs = attr_names(tree)
    if any(a in (("os", "environ"), ("os", "getenv"), ("os", "system"), ("os", "popen")) for a in attrs):
        out_.append(u"環境変数・shell を読んで/呼んでいる")
    for mod, fn in CALLED:
        if (mod, fn) not in attrs:
            out_.append(u"前の便の %s を %s から呼んでいない" % (fn, mod))
    funcs = set(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    for fn in NOT_COPIED:
        if fn in funcs:
            out_.append(u"前の便の %s を script が自分で定義している(写している)" % fn)
    consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    if u"_xa0_inline_build_2026_11_22" not in consts:
        out_.append(u"便 XB0 の script を読む名が一意の名でない")
    if any(n in consts for n in OTHER_NAMES):
        out_.append(u"他の便と重なる名で読んでいる")
    for var, want in (("B", ("_load_sibling", None)), ("W", ("B", "W"))):
        ok = False
        for n in tree.body:
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == var for t in n.targets):
                v = n.value
                if want[1] is None:
                    ok = isinstance(v, ast.Call) and getattr(v.func, "id", None) == want[0]
                else:
                    ok = isinstance(v, ast.Attribute) and isinstance(v.value, ast.Name) and v.value.id == want[0] and v.attr == want[1]
        if not ok:
            out_.append(u"%s を前の便の script から受けていない(Stop の型・module の実体が 2 つになる)" % var)
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            doc.add(id(n.body[0].value))
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc:
            if u".env" in n.value or u"dotenv" in n.value or u"API_KEY" in n.value:
                out_.append(u"鍵・.env の字が在る")
    for w in HARNESS_WORDS:
        bare = w.rstrip("(")
        for n in ast.walk(tree):
            if isinstance(n, ast.FunctionDef) and n.name == bare:
                out_.append(u"別の門の規準の字を関数の名に使っている: %s" % w)
            if isinstance(n, ast.Call):
                f = n.func
                nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else u"")
                if nm == bare:
                    out_.append(u"別の門の規準の字を呼んでいる: %s" % w)
        if w in src:
            out_.append(u"別の門の規準の字が script の字の中に在る(説明文も含む): %s" % w)
    return out_


def reserved_problems(rel=GATE_REL, base=ROOT):
    out_ = []
    with open(os.path.join(base, rel), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for n, line in enumerate(lines, 1):
        if any(line.startswith(p) for p in RESERVED_PREFIXES):
            out_.append(u"%s:%d" % (rel, n))
    return out_


# ======================================================================== 変異
#: (名前, 置き換え前(script の中でちょうど 1 回)・置き換え後・赤になるべき検査の名前)。**予測は「その検査が赤になる」。** この表は実行より先に書いた。
#: 検査の名前: seal・place・facts・mode・count・sign・format・chunk・suspicion・record・clean・devrun・decode・wiring
MUTANTS = (
    # ---- 表の読み方
    (u"A1 colspan を見ない", u"stack[-1][2] += colspan_of(attrs)", u"stack[-1][2] += 1", ("place",)),
    (u"A2 colspan の 1 未満を 1 に直さない", u"return n if n >= 1 else 1", u"return n", ("place",)),
    (u"A3 colspan の整数でない字を 1 に直さない", u"    if not INT_RE.match(v):\n        return 1\n", u"", ("place",)),
    (u"A4 colspan の前後の空白を落とさない", u"v = next(g for g in m.groups() if g is not None).strip()", u"v = next(g for g in m.groups() if g is not None)", ("place",)),
    (u"A5 行の番号を 2 ずつ進める", u"        stack[-1][2] += 1\n        if not selfc:\n            stack.append([\"tr\", row, 0])", u"        stack[-1][2] += 2\n        if not selfc:\n            stack.append([\"tr\", row, 0])", ("place",)),
    (u"A6 最も内側でなく最も外側の table を表にする", u"for i in range(len(stack) - 1, -1, -1):\n        if stack[i][0] == \"table\":\n            k = i\n            break", u"for i in range(len(stack)):\n        if stack[i][0] == \"table\":\n            k = i\n            break", ("place",)),
    (u"A7 コメントの中も読む", u"        if j < len(masked) and masked[j][0] <= m.start() < masked[j][1]:\n            continue\n", u"", ("place",)),
    (u"A8 タグの大文字・小文字を分ける", u'TABLE_TAG_RE = re.compile(r"<(/?)(table|tr|td|th)(?=[\\s/>])([^>]*)>", re.I)', u'TABLE_TAG_RE = re.compile(r"<(/?)(table|tr|td|th)(?=[\\s/>])([^>]*)>")', ("place",)),
    (u"A9 自己閉じの td も積む", u"        if not selfc:\n            stack.append([name, col, end])", u"        stack.append([name, col, end])", ("place",)),
    (u"A10 閉じタグが合わなくても断らない", u"        if not stack or stack[-1][0] != name:\n            raise Refuse(R_TABLE)\n        stack.pop()", u"        if stack:\n            stack.pop()", ("place",)),
    (u"A11 開いたまま終わっても断らない", u"    if stack:\n        raise Refuse(R_TABLE)\n    return out", u"    return out", ("place",)),
    (u"A12 th を cell に数えない", u"(table|tr|td|th)(?=", u"(table|tr|td)(?=", ("place",)),
    (u"A13 fact の無い file も表を読んで断る", u"    if not idx:\n        return []\n", u"    if not idx:\n        place_positions(text, [])\n        return []\n", ("place",)),
    (u"A14 タグ名の後ろの区切りを見ない(thead・tbody を th・tr に読む)", u"(?=[\\s/>])", u"", ("place",)),
    (u"A15 tr の親が table でなくても通す", u"        if not stack or stack[-1][0] != \"table\":\n            raise Refuse(R_TABLE)\n        row = stack[-1][2]", u"        if not stack:\n            raise Refuse(R_TABLE)\n        row = stack[-1][2]", ("place",)),
    (u"A16 td の親が tr でなくても通す", u"        if not stack or stack[-1][0] != \"tr\":\n            raise Refuse(R_TABLE)\n        col = stack[-1][2]", u"        if not stack:\n            raise Refuse(R_TABLE)\n        col = stack[-1][2]", ("place",)),
    (u"A17 行の下に td が無くても cell を返す", u'if k is not None and len(stack) >= k + 3 and stack[k + 1][0] == "tr" and stack[k + 2][0] in ("td", "th"):', u'if k is not None and len(stack) >= k + 2 and stack[k + 1][0] == "tr":', ("place",)),
    (u"A18 表の番号を file ごとに 0 から数える(file をまたぐ重なり)", u'f["table"] = (fi, f["table"])', u'f["table"] = (0, f["table"])', ("place",)),
    (u"A19 file を名の昇順に並べない", u"for fi, (_n, text) in enumerate(sorted(files, key=lambda p: p[0])):", u"for fi, (_n, text) in enumerate(files):", ("place",)),
    # ---- fact の読み方
    (u"B1 nonNumeric も fact に数える", u'idx = [i for i, e in enumerate(F) if e["kind"] == "nonFraction"]', u'idx = [i for i, e in enumerate(F) if e["kind"] != "footnote"]', ("facts",)),
    (u"B2 ix:header の中も開きタグに数える", u"        if name == \"ix:header\":\n            in_header = True\n            continue\n", u"", ("facts",)),
    (u"B3 表 F との対応を見ない", u"    if len(opens) != len(F) or any(k != e[\"kind\"] for (_p, k), e in zip(opens, F)):\n        raise Refuse(R_ALIGN)", u"    pass", ("facts",)),
    (u"B4 表 F との種類の合いを見ない", u"or any(k != e[\"kind\"] for (_p, k), e in zip(opens, F))", u"", ("facts",)),
    (u"B5 xsi:nil が false でも空の fact", u'nil=attrs.get(NIL_ATTR) == "true"', u"nil=attrs.get(NIL_ATTR) is not None", ("facts",)),
    (u"B6 fact の字のタグを落とさない", u'text=strip_tags(plain[e["start"]:e["end"]]).strip()', u'text=plain[e["start"]:e["end"]].strip()', ("facts",)),
    (u"B7 fact の字の前後の空白を落とさない", u'text=strip_tags(plain[e["start"]:e["end"]]).strip()', u'text=strip_tags(plain[e["start"]:e["end"]])', ("facts",)),
    (u"B8 符号の字を cell の開きタグの終わりでなく表の頭から取る", u'f["between"] = strip_tags(text[cell[3]:p])', u'f["between"] = strip_tags(text[:p])', ("facts",)),
    (u"B9 符号の字のタグを落とさない", u'f["between"] = strip_tags(text[cell[3]:p])', u'f["between"] = text[cell[3]:p]', ("facts",)),
    (u"B10 便 XB0 の断りの理由を捨てる", u"        raise Refuse(exc.reason)\n    except Exception:", u"        raise Refuse(R_EXC)\n    except Exception:", ("facts",)),
    (u"B11 符号化が読めない file を飛ばす", u"            except UnicodeDecodeError:\n                raise Refuse(R_ENC)", u"            except UnicodeDecodeError:\n                pass", ("decode",)),
    (u"B12 PublicDoc 以外の htm も読む", u"        if B.is_public_htm(info.filename):\n            try:", u"        if info.filename.endswith(\".htm\"):\n            try:", ("decode",)),
    (u"B13 file を名の昇順に並べない(doc_texts)", u"    out.sort(key=lambda t: t[0])\n    return out", u"    return out", ("decode",)),
    # ---- 数え方
    (u"C1 最頻が並んだら後に現れた値", u"    for v, c in counts.items():\n        if c == best:\n            return v", u"    for v, c in reversed(list(counts.items())):\n        if c == best:\n            return v", ("mode",)),
    (u"C2 unitRef の最頻から空の fact を除く", u'mode_first([x.get("unitRef") for x in a])', u'mode_first([x.get("unitRef") for x in live])', ("mode",)),
    (u"C3 decimals の最頻に空の fact も入れる", u'mode_first([x.get("decimals") for x in live])', u'mode_first([x.get("decimals") for x in a])', ("mode",)),
    (u"C4 scale の最頻に空の fact も入れる", u'mode_first([x.get("scale") for x in live])', u'mode_first([x.get("scale") for x in a])', ("mode",)),
    (u"C5 空の fact も decimals で違うと数える", u'(not f["nil"]) and a.get("decimals") != d[2]', u'a.get("decimals") != d[2]', ("mode",)),
    (u"C6 空の fact も scale で違うと数える", u'(not f["nil"]) and a.get("scale") != d[3]', u'a.get("scale") != d[3]', ("mode",)),
    (u"C7 空の fact の name を見ない", u'out.append((a.get("name") != d[0],', u'out.append(((not f["nil"]) and a.get("name") != d[0],', ("mode",)),
    (u"C8 向き B の線を向き A と同じにする", u'    return (f["row"], f["col"]) if orient == "A" else (f["col"], f["row"])', u'    return (f["row"], f["col"])', ("mode", "count")),
    (u"C9 同じ数なら向き B", u'("B", fb) if db > da else ("A", fa)', u'("B", fb) if db >= da else ("A", fa)', ("count",)),
    (u"C10 決まる fact が少ない向きを選ぶ", u'("B", fb) if db > da else ("A", fa)', u'("B", fb) if db < da else ("A", fa)', ("count",)),
    (u"C11 要素の線の欄が 4 でなく 3", u"CELL_ATTR_PER_ELEMENT_LINE = 4 ", u"CELL_ATTR_PER_ELEMENT_LINE = 3 ", ("seal", "count")),
    (u"C12 全部決まらない fact に 7 を掛けない", u'acc["c_undecided"] = (acc["inside"] - acc["full"]) * CELLS_PER_FACT', u'acc["c_undecided"] = (acc["inside"] - acc["full"])', ("count",)),
    (u"C13 全部決まらない fact を表の外も含めて数える", u'acc["c_undecided"] = (acc["inside"] - acc["full"]) * CELLS_PER_FACT', u'acc["c_undecided"] = (acc["fact"] - acc["full"]) * CELLS_PER_FACT', ("count",)),
    (u"C14 表の外の fact に 7 を掛けない", u'acc["c_outside"] = acc["outside"] * CELLS_PER_FACT', u'acc["c_outside"] = acc["outside"]', ("count",)),
    (u"C15 空の fact の項を数えない", u'acc["c_nil"] = acc["nil"]', u'acc["c_nil"] = 0', ("count",)),
    (u"C16 書式の類の数に空の fact も入れる", u'acc["c_formats"] = len(set(format_class(f["text"]) for f in live))', u'acc["c_formats"] = len(set(format_class(f["text"]) for f in facts))', ("format", "count")),
    (u"C17 表ごとの向きの欄を数えない", u'acc["c_orient"] = acc["tables"] * CELL_PER_TABLE', u'acc["c_orient"] = 0', ("count",)),
    (u"C18 文脈の線の欄を数えない", u'acc["c_ctx"] = acc["ctx_lines"] * CELL_PER_CONTEXT_LINE', u'acc["c_ctx"] = 0', ("count",)),
    (u"C19 1 つだけの線を 2 つ以下に広げる", u"sum(1 for n in el.values() if n == 1)", u"sum(1 for n in el.values() if n <= 2)", ("count",)),
    (u"C20 1 つだけの表を 2 つ以下に広げる", u"        if len(items) == 1:\n            acc[\"tables_single\"] += 1", u"        if len(items) <= 2:\n            acc[\"tables_single\"] += 1", ("count",)),
    (u"C21 全部決まるが符号・書式を見ない", u"                ok = ok and neg == has and fmt_ok", u"                ok = ok", ("count",)),
    (u"C22 全部決まるが書式だけ見ない", u"                ok = ok and neg == has and fmt_ok", u"                ok = ok and neg == has", ("count",)),
    (u"C23 全部決まるが符号だけ見ない", u"                ok = ok and neg == has and fmt_ok", u"                ok = ok and fmt_ok", ("count",)),
    (u"C24 向き B の方が多かった表を B を選んだ表と別に数えない", u'        if orient == "B":\n            acc["tables_B_more"] += 1', u"        pass", ("count",)),
    (u"C25 決まらなかった理由を name だけ数える", u'for key, hit in zip(("r_name", "r_context", "r_unit", "r_decimals", "r_scale"), fl):', u'for key, hit in zip(("r_name", "r_name", "r_name", "r_name", "r_name"), fl):', ("count",)),
    (u"C26 表の外の fact の format も最頻に入れない", u"    live = [f for f in facts if not f[\"nil\"]]\n    modes = {}", u"    live = [f for f in facts if not f[\"nil\"] and f[\"table\"] is not None]\n    modes = {}", ("format",)),
    # ---- 符号・書式
    (u"D1 符号の字から ‐ を落とす", u'SIGN_CHARS = u"△▲-－−‐"', u'SIGN_CHARS = u"△▲-－−"', ("seal", "sign")),
    (u"D2 符号の字から △ を落とす", u'SIGN_CHARS = u"△▲-－−‐"', u'SIGN_CHARS = u"▲-－−‐"', ("seal", "sign")),
    (u"D3 符号の字に + を足す", u'SIGN_CHARS = u"△▲-－−‐"', u'SIGN_CHARS = u"△▲-－−‐+"', ("seal", "sign")),
    (u"D4 符号が合うを負と読んだことだけで決める", u"                if neg == has:", u"                if neg or not has:", ("sign",)),
    (u"D5 符号が合わない 2 つの数を取り違える", u"                elif neg:\n                    acc[\"sign_neg_no_attr\"] += 1", u"                elif not neg:\n                    acc[\"sign_neg_no_attr\"] += 1", ("sign",)),
    (u"D6 sign が - 以外でも在るに数える", u'has = f["attrs"].get("sign") == "-"', u'has = f["attrs"].get("sign") is not None', ("sign",)),
    (u"D7 ダッシュの字から − を落とす", u'DASH_CHARS = u"－―‐-—−"', u'DASH_CHARS = u"－―‐-—"', ("seal", "format")),
    (u"D8 数字の字から全角を落とす", u'NUM_CHARS = u"0123456789０１２３４５６７８９,，.．"', u'NUM_CHARS = u"0123456789,，.．"', ("seal", "format")),
    (u"D9 空の字をダッシュの類に入れる", u"    if s and all(ch in DASH_CHARS for ch in s):", u"    if all(ch in DASH_CHARS for ch in s):", ("format",)),
    (u"D11 書式が合うを最頻でなく最初の fact の値と比べる", u'fmt_ok = f["attrs"].get("format") == modes[format_class(f["text"])]', u'fmt_ok = f["attrs"].get("format") == live[0]["attrs"].get("format")', ("format",)),
    (u"D12 書式の類の数を 3 に固定", u'acc["c_formats"] = len(set(format_class(f["text"]) for f in live))', u'acc["c_formats"] = 3', ("format", "count")),
    # ---- 塊・判定
    (u"E1 全部決まる書類の境を 90% より大きいにする", u"100 * a[\"full\"] >= DOC_FULL_PCT * a[\"fact\"]", u"100 * a[\"full\"] > DOC_FULL_PCT * a[\"fact\"]", ("chunk",)),
    (u"E2 判定 XA0-1 の分母を空でない fact にする", u'(u"XA0-1 表の中の fact / fact", rate(tot["inside"], tot["fact"])),', u'(u"XA0-1 表の中の fact / fact", rate(tot["inside"], tot["live_inside"])),', ("chunk",)),
    (u"E3 判定 XA0-2 の分子を表の決めで決まる fact にする", u'(u"XA0-2 全部決まる fact / fact", rate(tot["full"], tot["fact"])),', u'(u"XA0-2 全部決まる fact / fact", rate(tot["decided"], tot["fact"])),', ("chunk",)),
    (u"E4 判定 XA0-5 の分母を表の向き A にする", u'rate(tot["tables_B_more"], tot["tables"])', u'rate(tot["tables_B_more"], tot["tables_A"])', ("chunk",)),
    (u"E5 全部決まる場合の比に全部決まらない項を残す", u"    return cells_of(acc) - acc[\"c_undecided\"]", u"    return cells_of(acc)", ("count", "chunk")),
    (u"E6 断った書類の理由を塊に数えない", u"            reasons[r[u\"断った理由\"]] = reasons.get(r[u\"断った理由\"], 0) + 1", u"            pass", ("chunk", "record")),
    (u"E7 断った書類も合計に足す", u"        if a is None:\n            reasons[", u"        if False:\n            reasons[", ("chunk", "record")),
    (u"E8 欠陥を疑う条件(100%)を外す", u'if f and ch[u"全部決まる fact の数"] == f:', u'if f and ch[u"全部決まる fact の数"] > f:', ("suspicion",)),
    (u"E9 欠陥を疑う条件(表の外 0)を外す", u'if ch[u"断らなかった書類の数"] and ch[u"表の外の fact の数"] == 0:', u'if ch[u"断らなかった書類の数"] and ch[u"表の外の fact の数"] < 0:', ("suspicion",)),
    (u"E10 欠陥を疑う条件(50% 未満)の境を変える", u"100 * ch[u\"表の中の fact の数\"] < SUSPECT_ABSENT_FACTS_PCT * f", u"100 * ch[u\"表の中の fact の数\"] <= SUSPECT_ABSENT_FACTS_PCT * f", ("suspicion",)),
    (u"E11 欠陥を疑う条件(断った 6 本)の境を変える", u"if ch[u\"断った書類の数\"] >= SUSPECT_DECLINED:", u"if ch[u\"断った書類の数\"] > SUSPECT_DECLINED:", ("suspicion",)),
    (u"E12 書類の行が全部決まる fact でなく表の決めで決まる fact を書く", u"(u\"全部決まる fact の数\", acc[\"full\"]), (u\"書く欄の数\", cells_of(acc))", u"(u\"全部決まる fact の数\", acc[\"decided\"]), (u\"書く欄の数\", cells_of(acc))", ("chunk", "record")),
    # ---- 記録
    (u"F1 塊の分け目を 1 つずらす", u"prod_rows, prod_accs = rows[dev_count:], accs[dev_count:]", u"prod_rows, prod_accs = rows[dev_count + 1:], accs[dev_count + 1:]", ("record",)),
    (u"F2 判定に要る数を 5 本の塊から作る", u"judged(rec[u\"本番だけの 62 本\"], prod_accs)", u"judged(rec[u\"開発の 5 本\"], dev_accs)", ("record",)),
    (u"F3 verify が塊の数を書類ごとの数と照らさない", u"            if ch[k] != v:\n                raise Stop(u\"**塊の数が書類ごとの数と合わない: %s。止める**\" % k)", u"            pass", ("record",)),
    (u"F4 verify が向きの数を見ない", u"        if ch[u\"向き A を選んだ表の数\"] + ch[u\"向き B を選んだ表の数\"] != ch[u\"fact の在る表の数\"] or ch[u\"向き B を選んだ表の数\"] != ch[u\"向き B の方が決まる fact が多かった表の数\"]:\n            raise Stop(u\"**表の向きの数が合わない。止める**\")", u"        pass", ("record",)),
    (u"F5 verify が符号の数を見ない", u"        if ch[u\"符号が合う fact の数\"] + ch[u\"符号が合わない fact の数(負と読んだが sign が - でない)\"] + ch[u\"符号が合わない fact の数(sign が - だが負と読めない)\"] != ch[u\"表の中の空でない fact の数\"]:\n            raise Stop(u\"**符号の数が合わない。止める**\")", u"        pass", ("record",)),
    (u"F6 verify が書式の数を見ない", u"        if ch[u\"書式が合う fact の数\"] + ch[u\"書式が合わない fact の数\"] != ch[u\"表の中の空でない fact の数\"]:\n            raise Stop(u\"**書式の数が合わない。止める**\")", u"        pass", ("record",)),
    (u"F7 verify が書く欄の項を見ない", u"        if sum(ch[u\"書く欄の数(項ごと)\"].values()) != ch[u\"書く欄の数\"] or ch[u\"fact の数 × 7\"] != 7 * ch[u\"fact の数\"]:\n            raise Stop(u\"**書く欄の数の項が合わない。止める**\")", u"        pass", ("record",)),
    (u"F8 verify が書類の形(断ったと理由)を見ない", u"        if r[u\"断った\"] != bool(r[u\"断った理由\"]) or r[u\"断った\"] != (r[u\"fact の数\"] is None):", u"        if False:", ("record",)),
    (u"F9 verify が書類の番号を見ない", u"        if r.get(u\"番号\") != i or list(r) != [", u"        if list(r) != [", ("record",)),
    (u"F10 verify が 67 本を見ない", u"    if not isinstance(rows, list) or len(rows) != want or rec[u\"材料\"][u\"書類の本数\"] != want:", u"    if not isinstance(rows, list):", ("record",)),
    (u"F11 check が置き場から数え直さない", u"    if dumps(now) != dumps(rec):", u"    if False:", ("record",)),
    (u"F12 check が verify を通さない", u"    verify_record(rec, text, want, dev_count)\n    now, secret", u"    now, secret", ("record",)),
    (u"F13 write_record が既に在る記録を上書きできる", u"    if os.path.exists(path):\n        raise Stop(u\"**記録が既に在る: %s。止める**\" % os.path.basename(path))\n    text = record_text(rec, secret)", u"    text = record_text(rec, secret)", ("clean", "record")),
    (u"F14 run が進みを渡さない", u"rec, secret = build_record(docs, want, dev_count, progress)", u"rec, secret = build_record(docs, want, dev_count, None)", ("record",)),
    (u"F15 check_clean が何も止めない", u"    W.check_clean(rec, text, secret)\n", u"    pass\n", ("clean",)),
    (u"F16 check_clean が file の名の形を見ない", u"    if re.search(r\"\\.(?:htm|xsd|xml|zip)\\b\", W.HEX_RE.sub(u\"\", text), re.I):\n        raise Stop(u\"**記録に file の名の形の字が在る。止める**\")", u"    pass", ("clean",)),
    (u"F17 secret に文脈の名を入れない", u"                if re.search(r\"[A-Za-z]\", c):\n                    ctxs.add(c)", u"                pass", ("record",)),
    (u"F18 secret に要素の名を入れない", u"                names.add((f[\"attrs\"].get(\"name\") or u\"\").split(u\":\")[-1])", u"                pass", ("record",)),
    (u"F19 secret に EDINET コードを入れない", u"            ecodes.update(re.findall(r\"E\\d{5}\", x))", u"            pass", ("record",)),
    (u"F20 build_record が断った書類で止まる", u"        except Refuse as exc:\n            acc, reason = None, exc.reason\n        rows.append(doc_row(n, acc, reason))", u"        except ZeroDivisionError:\n            acc, reason = None, u\"\"\n        rows.append(doc_row(n, acc, reason))", ("record",)),
    (u"F21 開発の入口が 5 本より多く開く", u"    docs = dev_docs(docs_dir or DOCS_DIR, count)\n    rows, accs = [], []", u"    docs = dev_docs(docs_dir or DOCS_DIR, count + 2)\n    rows, accs = [], []", ("devrun",)),
    (u"F22 開発の入口が記録を書く", u"    ch = chunk_of(rows, accs)\n    say(u\"開発の 5 本の合計", u"    ch = chunk_of(rows, accs)\n    write_exclusive(os.path.join(docs_dir or DOCS_DIR, 'sheet_wall_2026-11-22.json'), b'x')\n    say(u\"開発の 5 本の合計", ("devrun",)),
    (u"F23 開発の入口が欠陥を疑う行を出さない", u"    say(u\"先に自分の欠陥を疑う場合に当たったもの: %s\" % (u\"・\".join(suspicions(ch)) or u\"なし\"))", u"    pass", ("devrun",)),
    (u"F24 count_zip が断った理由を捨てる", u"        return None, exc.reason", u"        return None, u\"\"", ("decode",)),
    # ---- 封の字・配線
    (u"S1 予測の境の数を変える", u'("XA0-1", (97, None))', u'("XA0-1", (96, None))', ("seal",)),
    (u"S2 予測の境の数を変える(XA0-2 の上限)", u'("XA0-2", (75, 95))', u'("XA0-2", (75, 96))', ("seal",)),
    (u"S3 上限を含まない予測の名を落とす", u'BOUNDS_UPPER_EXCLUSIVE = ("XA0-2", "XA0-4")', u'BOUNDS_UPPER_EXCLUSIVE = ("XA0-2",)', ("seal",)),
    (u"S4 封の commit の字を変える", u'SEAL_COMMIT = "3062223e"', u'SEAL_COMMIT = "3062223f"', ("seal",)),
    (u"S5 限界の字を落とす", u'    u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない。"]', u'    u"「XBRL を作れる」は、この便からは言えない。"]', ("seal",)),
    (u"S6 記録の path を変える", u'RECORD_REL = "fixtures/xbrl/cd8/sheet_wall_2026-11-22.json"', u'RECORD_REL = "fixtures/xbrl/cd8/sheet_wall_2026-11-23.json"', ("seal",)),
    (u"S7 見る属性の並びを変える", u'ATTRS = ("name", "contextRef", "unitRef", "decimals", "scale", "sign", "format")', u'ATTRS = ("name", "contextRef", "unitRef", "decimals", "scale", "format", "sign")', ("seal",)),
    (u"S8 空の fact が見る属性を増やす", u'NIL_ATTRS = ("name", "contextRef", "unitRef")', u'NIL_ATTRS = ("name", "contextRef", "unitRef", "decimals")', ("seal",)),
    (u"S9 書類 90% を変える", u"DOC_FULL_PCT = 90", u"DOC_FULL_PCT = 80", ("seal", "chunk")),
    (u"S10 7 を 6 にする", u"CELLS_PER_FACT = 7", u"CELLS_PER_FACT = 6", ("seal", "count")),
    (u"S11 開発の本数を変える", u"DEV_COUNT = 5", u"DEV_COUNT = 6", ("seal",)),
    (u"S12 書類の本数を変える(W の字を自分で持つ)", u"DOCS_WANT = W.DOCS_WANT", u"DOCS_WANT = 66", ("seal",)),
    (u"S13 欠陥を疑う条件の数を変える", u"SUSPECT_DECLINED = 6", u"SUSPECT_DECLINED = 7", ("seal", "suspicion")),
    (u"W1 別の門の規準の字を関数の名にする", u"def strip_tags(s):", u"def mutate(x):\n    return x\n\n\ndef strip_tags(s):", ("wiring",)),
    (u"W2 別の門の規準の字を説明文に書く", u"# 字の読み方(封 §1)\n", u"# 字の読み方(封 §1)(注入)\n", ("wiring",)),
    (u"W3 便 XB0 の script を他の便と重なる名で読む", u'INLINE_NAME = "_xa0_inline_build_2026_11_22"', u'INLINE_NAME = "_xb0_inline_build_2026_11_21"', ("wiring",)),
    (u"W4 前の便の関数を写す", u"def strip_tags(s):", u"def strip_text(text):\n    return text\n\n\ndef strip_tags(s):", ("wiring",)),
    (u"W5 zipfile を import する", u"import time\n", u"import time\nimport zipfile\n", ("wiring",)),
    (u"W6 subprocess を import する", u"import time\n", u"import time\nimport subprocess\n", ("wiring",)),
    (u"W7 engine を import する", u"import time\n", u"import time\nfrom adapters.xbrl import instance\n", ("wiring",)),
    (u"W8 Stop を便 XG0 から別に読む", u"W = B.W ", u'W = _load_sibling("_xa0_other_wall", "xbrl_tag_wall_2026-11-21.py")  # ', ("wiring",)),
    (u"W9 便 XB0 の strip_text を呼ばず自分で剥がす", u"        plain, F, _H = B.strip_text(text)", u"        plain, F, _H = (text, [], None)", ("facts", "wiring")),
    (u"W10 B.load_package を呼ばず zip を自分で開く", u"for info, data in B.load_package(zip_path):", u"for info, data in load_package(zip_path):", ("wiring", "decode")),
)
#: 黙ることが分かっている変異(理由つき)。予測は「黙る」ではなく、実行して黙った事実と理由を実行の後に書く(実行前は空)
SILENT_BY_DESIGN = {
    u"F12 check が verify を通さない": u"verify_record が見るのは記録の内側の食い違いで、置き場からの数え直しの比べ(dumps の一致)も同じ食い違いを止める。2 つの規則が重なる(どちらかだけ外しても書き換えた記録は止まる)。verify は置き場の無い所の単独の検査としては F3〜F10 で縛っている"}


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"place": place_problems, u"facts": facts_problems, u"mode": mode_problems, u"count": count_problems, u"sign": sign_problems, u"format": format_problems,
             u"chunk": chunk_problems, u"suspicion": suspicion_problems, u"record": record_problems, u"clean": clean_problems, u"devrun": devrun_problems, u"decode": decode_problems}
    if name in table:
        return table[name](mod)
    if name == u"wiring":
        return import_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"place", u"facts", u"mode", u"count", u"sign", u"format", u"chunk", u"suspicion", u"record", u"clean", u"devrun", u"decode", u"wiring")


def run_mutants(table=MUTANTS, only=None):
    base = read(SCRIPT_REL)
    out_ = []
    for name, old, new, checks in table:
        if only is not None and name not in only:
            continue
        assert base.count(old) == 1, (name, base.count(old))
        src = base.replace(old, new)
        try:
            mod = load_source(src)
        except BaseException as exc:                # noqa: BLE001
            out_.append((name, [(c, True) for c in checks], u"読めない: %s" % type(exc).__name__))
            continue
        res = [(c, bool(guard(check_by_name, c, mod, src))) for c in checks]
        out_.append((name, res, u""))
    return out_


# ======================================================================== 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_constants_equal_the_seal(self):
        self.assertEqual([], seal_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        for old, new in ((u"| XA0-2(主) | 全部決まる fact は、fact の 75% 以上 95% 未満", u"| XA0-2(主) | 全部決まる fact は、fact の 75% 以上 96% 未満"),
                         (u"**見る属性 7 つ**: `name`・`contextRef`・`unitRef`・`decimals`・`scale`・`sign`・`format`", u"**見る属性 6 つ**: `name`・`contextRef`・`unitRef`・`decimals`・`scale`・`sign`"),
                         (u"`△`・`▲`・`-`・`－`・`−`・`‐` のどれかが在れば「負」と読む", u"`△`・`▲`・`-`・`－`・`−` のどれかが在れば「負」と読む"),
                         (u"× 4(`name`・`unitRef`・`decimals`・`scale`)", u"× 3(`name`・`unitRef`・`decimals`・`scale`)"), (u"同じなら向き A", u"同じなら向き B"),
                         (u"表の外の fact の数 × 7", u"表の外の fact の数 × 8"), (u"便 XG0 の封 §1 と同じ 67 本(同じ並び)", u"便 XG0 の封 §1 と同じ 66 本(同じ並び)")):
            self.assertGreaterEqual(seal.count(old), 1, old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"sheet_wall", body)


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_good_order_is_green_and_bad_orders_are_red(self):
        pr = load_order_helpers()
        r = pr.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        others = ["measure/s.py", "tests/g.py"]
        for f in others:
            r.put(f)
        r.commit(*others)
        self.assertEqual([], pr.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others))
        self.assertNotEqual([], pr.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", [], others))
        r.put("tests/new.py")
        self.assertNotEqual([], pr.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others + ["tests/new.py"]))

    def test_d_3_the_order_check_lists_the_script_and_the_gate_and_not_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)

    def test_d_4_the_record_when_tracked_is_committed_after_the_script_and_the_gate(self):
        if not record_tracked():
            self.skipTest(u"記録は本番の走りの後に書かれ、commit される。commit された後で順を見る")
        self.assertEqual([], order_of(others=list(ORDER_FILES) + [RECORD_REL]))


class ReadTest(unittest.TestCase):
    def test_b_1_the_table_reading_is_decided_by_the_seal(self):
        self.assertEqual([], place_problems())

    def test_b_2_the_fact_reading_is_decided_by_the_seal(self):
        self.assertEqual([], facts_problems())

    def test_b_3_the_place_reading_of_zips(self):
        self.assertEqual([], decode_problems())


class CountTest(unittest.TestCase):
    def test_c_1_modes_and_line_decisions(self):
        self.assertEqual([], mode_problems())

    def test_c_2_counts_by_hand(self):
        self.assertEqual([], count_problems())

    def test_c_3_sign(self):
        self.assertEqual([], sign_problems())

    def test_c_4_format(self):
        self.assertEqual([], format_problems())

    def test_c_5_chunks_and_judging_numbers(self):
        self.assertEqual([], chunk_problems())

    def test_c_6_suspicion_conditions(self):
        self.assertEqual([], suspicion_problems())

    def test_c_7_the_acc_keys_match_the_hand_counted_keys(self):
        self.assertEqual(list(MS.ACC_KEYS), list(DOC1_WANT))


class RecordTest(unittest.TestCase):
    def test_e_1_the_record_path_from_a_fake_place(self):
        self.assertEqual([], record_problems())

    def test_e_2_forbidden_things_stop_the_record(self):
        self.assertEqual([], clean_problems())

    def test_e_3_the_dev_entry_opens_only_the_first_five(self):
        self.assertEqual([], devrun_problems())

    def test_e_4_the_real_record_when_present_is_clean_and_consistent(self):
        p = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(p):
            self.skipTest(u"記録は本番の走りの後に書かれる。記録の中身の検査は結果の門に置く")
        text = read(RECORD_REL)
        MS.verify_record(json.loads(text, object_pairs_hook=od), text)


class WiringTest(unittest.TestCase):
    def test_f_1_imports_and_the_earlier_functions_are_called_not_copied(self):
        self.assertEqual([], import_problems())

    def test_f_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        for extra in (u"\nimport socket\n", u"\nimport zipfile\n", u"\nimport csv\n", u"\nimport subprocess\n", u"\nfrom adapters.xbrl import instance\n", u"\nX = os.system('a')\n",
                      u"\ndef select_docs(a, b):\n    return None\n", u"\ndef load_package(a):\n    return None\n", u"\ndef run_doc(a):\n    return None\n", u"\ndef strip_text(a):\n    return None\n"):
            self.assertNotEqual([], import_problems(base + extra), extra)
        self.assertNotEqual([], import_problems(base.replace(u"B.strip_text(", u"strip_text(")))
        self.assertNotEqual([], import_problems(base.replace(u"B.load_package(", u"load_package(")))
        self.assertNotEqual([], import_problems(base.replace(u"W.select_docs(", u"select_docs(")))

    def test_f_3_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_f_4_the_script_leaves_sys_modules_as_it_found_them(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_sheet_wall_script_for_sysmodules_check")
        changed = [k for k in before if sys.modules.get(k) is not before[k]]
        self.assertEqual([], changed)
        self.assertEqual(mod.B.__name__, u"_xa0_inline_build_2026_11_22")
        self.assertIs(mod.W, mod.B.W)
        self.assertIs(mod.Stop, mod.B.V.Stop)
        del mod

    def test_f_5_the_default_place_is_outside_the_repo_and_the_gate_never_opens_it(self):
        top = os.path.realpath(REPO)
        self.assertFalse(os.path.realpath(MS.DOCS_DIR).startswith(top + os.sep))
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(select_docs|run|check|build_record|dev_docs|dev_run)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"docs|rec_path|\bd\b", m.group(2)), m.group(0))

    def test_f_6_the_gate_calls_subprocess_only_for_git(self):
        src = read(GATE_REL)
        calls = re.findall(r"subprocess\.(\w+)", src)
        self.assertEqual(set(calls), {"run", "PIPE"})
        for m in re.finditer(r"subprocess\.run\(([^)]*)\)", src):
            self.assertTrue(m.group(1).startswith(u'["git"'), m.group(1))


class MutantTest(unittest.TestCase):
    def test_g_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL))
        modules_before = dict(sys.modules)
        results = run_mutants()
        self.assertEqual(before, (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL)))
        self.assertEqual([], [k for k, v in modules_before.items() if sys.modules.get(k) is not v])
        silent = [(n, c) for n, res, _w in results for c, red in res if not red and n not in SILENT_BY_DESIGN]
        self.assertEqual([], silent)
        self.assertEqual(set(SILENT_BY_DESIGN), set(n for n, res, _w in results if any(not red for _c, red in res)))
        self.assertEqual(len(MUTANTS), len(results))
        self.assertGreaterEqual(len(MUTANTS), 100)
        self.assertEqual(len(set(m[0] for m in MUTANTS)), len(MUTANTS))

    def test_g_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ALL_CHECKS:
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
