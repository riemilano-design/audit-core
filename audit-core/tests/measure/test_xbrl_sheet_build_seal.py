# -*- coding: utf-8 -*-
u"""封 docs/XBRL_SHEET_BUILD_SEAL_2026-11-22.md(XS0 ― 行・列の紙から数の fact の属性を作り直し、便 XP0 の組む命令で包みを組むと、道具が読む fact は元と同じになるか)の封の門。

**この門は置き場を読まない**(書類の置き場 ``~/.cache/audit-core/edinet/`` は 1 度も開かない)。通信しない。道具(Arelle)は呼ばない(偽の ``runner`` を渡す)。subprocess を呼ぶのは git だけ
(紙を作る・属性を作る・組む命令の別の process は、同じ引数で呼ぶ同じ process の中の ``proc`` に替えて通す。別の process の呼び方そのものは引数の形を字で縛る)。
作り物の書類(手で書いた htm と最小のタクソノミの zip)で、規則を 1 つずつ本物の関数のまま通す。

**この門が縛るもの**

1. 封の字: 封の commit(483e3e93)・封の file が commit した blob と同じ・封の決め(紙の欄の式の 3・4・7・混ぜ物の字・予測の境・限界の字)が script の定数と同じ。
2. engine は読まない・封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 規則を 1 つずつ(作り物の書類): 表の外の fact・全部決まらない fact・文脈の ``id`` が 2 つ在る組・期間の種類が ``name`` の決めと違う fact・空の fact・決めが「無い」属性・そのほかの属性・負の字・書式の類・
   member・混ぜ物。どれも紙から作り直した ``attrs`` が元と同じになること、1 つずつ書く fact の数と理由が手で数えたとおりになること。
4. 紙の値を 1 つ変えると、作った ``attrs`` が変わる(または断る)。紙の欄の数は紙の file を読み戻して数えた値。
5. **属性を作る命令に渡す folder に元の ``attrs`` が無い**(``nonFraction`` の行の ``attrs`` は空・紙に非 1 つずつの fact の ``contextRef`` の字が無い)。属性を作る命令は元の包み・元の ``.htm``・元の fact を読む関数を呼ばない(字で縛る)。
6. 書類 1 本の通し(紙を作る → 属性を作る → 比べ方 1 → 混ぜ物 → 組む → 2 回組む → 道具)・断りの段と理由・塊・判定に要る数・欠陥を疑う条件・記録の形と合計と禁止のもの(記録がまだ無い間は作り物の記録で見る。在るときは本物の記録も見る)。
7. 封 → script → 記録の commit の順(script・門のどちらかが未 commit なら赤)。
8. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。変異の検査は変異した module そのものに当てる
(``check_by_name(name, mod, src)`` は変異した module の関数だけを呼ぶ)。表は実行より先に書いた(予測 = 赤になるべき検査の名前)。
"""
import ast
import collections
import copy
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
    mod = types.ModuleType("xbrl_sheet_build_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_SHEET_BUILD_SEAL_2026-11-22.md"
SEAL_COMMIT_SHORT = "483e3e93"
SCRIPT_REL = "measure/xbrl_sheet_build_2026-11-22.py"
GATE_REL = "tests/measure/test_xbrl_sheet_build_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/sheet_build_2026-11-22.json"
MS = load_module(SCRIPT_REL, "xbrl_sheet_build_script_for_seal_gate")
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
        self.d = tempfile.mkdtemp(prefix="xs0_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


def load_order_helpers():
    p = os.path.join(ROOT, "tests", "measure", "test_xbrl_p28_result.py")
    if not os.path.exists(p):
        return None
    return load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_sheet_build_seal")


def want_eq(out_, label, got, want):
    if got != want:
        out_.append(u"%s: 得 %r 正 %r" % (label, got, want))


# ======================================================================== 作り物の書類(手で書いた字)
AXIS = u"jppfs_cor:SegAxis"
XSD = b'<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" targetNamespace="http://example.com/x"/>'
LB = b'<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase"/>'


def fx(name=u"jppfs_cor:E0", ctx=u"KA", unit=u"JPY", dec=u"0", scale=None, sign=None, fmt=u"ixt:numdotdecimal", text=u"1,000", nil=False, extra=u"", shuffle=False):
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
    a += extra
    if shuffle:
        a = u" ".join(reversed(re.findall(r'\S+="[^"]*"', a)))
    return u"<ix:nonFraction %s>%s</ix:nonFraction>" % (a, text)


def tbl(rows):
    return u"<table>" + u"".join(u"<tr>" + u"".join(u"<td>%s</td>" % c for c in r) + u"</tr>" for r in rows) + u"</table>"


def cdef(cid, end=u"2025-03-31", start=None, mem=(), pad=False, forever=False):
    end = u" %s " % end if pad else end
    per = u"<xbrli:forever/>" if forever else u"<xbrli:instant>%s</xbrli:instant>" % end if start is None else u"<xbrli:startDate>%s</xbrli:startDate><xbrli:endDate>%s</xbrli:endDate>" % (start, end)
    scen = u"<xbrli:scenario>%s</xbrli:scenario>" % u"".join(u'<xbrldi:explicitMember dimension="%s">%s</xbrldi:explicitMember>' % (d, m) for d, m in mem) if mem else u""
    return (u'<xbrli:context id="%s"><xbrli:entity><xbrli:identifier scheme="http://x">E0</xbrli:identifier></xbrli:entity><xbrli:period>%s</xbrli:period>%s</xbrli:context>' % (cid, per, scen))


def cpage(body, defs):
    return u"<html><body><ix:header><ix:resources>%s</ix:resources></ix:header>\n%s\n</body></html>\n" % (u"".join(defs), body)


MEM1 = [(AXIS, u"jppfs_cor:Mem1")]


def doc_r1():
    u"""2 行 × 3 列。行ごとに要素(E0・E1)・列ごとに文脈(KA 時点 2025・KB 時点 2024・KM 時点 2025 と member)。全部決まる。"""
    defs = [cdef(u"KA"), cdef(u"KB", end=u"2024-03-31"), cdef(u"KM", mem=MEM1)]
    rows = [[fx(name=u"jppfs_cor:E0", ctx=c, dec=u"-3", scale=u"3") for c in (u"KA", u"KB", u"KM")], [fx(name=u"jppfs_cor:E1", ctx=c, dec=u"0") for c in (u"KA", u"KB", u"KM")]]
    return cpage(tbl(rows), defs)


def doc_outside():
    return cpage(tbl([[fx(ctx=u"KA"), fx(ctx=u"KB")]]) + fx(name=u"jppfs_cor:Ex", ctx=u"KA"), [cdef(u"KA"), cdef(u"KB", end=u"2024-03-31")])


def doc_odd(kind):
    u"""2 × 2 で全部同じ文脈。fact (1, 1) だけ ``kind`` が違う。決まるのは 3。"""
    kw = {"unit": dict(unit=u"USD"), "dec": dict(dec=u"-3"), "scale": dict(scale=u"3"), "name": dict(name=u"jppfs_cor:Rh9")}[kind]
    rows = [[fx(**dict(dict(name=u"jppfs_cor:Rh", ctx=u"KA"), **(kw if (r, c) == (1, 1) else {}))) for c in range(2)] for r in range(2)]
    return cpage(tbl(rows), [cdef(u"KA")])


def doc_dupctx():
    u"""3 行 × 1 列。R0・R1 の文脈は(期間・終わりの日・member の組)が同じで id が違う。R2 は時点。"""
    defs = [cdef(u"Dx1", start=u"2024-04-01"), cdef(u"Dx2", start=u"2023-04-01"), cdef(u"Cu")]
    return cpage(tbl([[fx(name=u"jppfs_cor:R0", ctx=u"Dx1")], [fx(name=u"jppfs_cor:R1", ctx=u"Dx2")], [fx(name=u"jppfs_cor:R2", ctx=u"Cu")]]), defs)


def doc_kind():
    u"""2 × 2。name は 1 つ。3 つは時点・(1, 1) だけ期間(終わりの日は列の決めと同じ)。name の期間の種類の決めは時点。"""
    defs = [cdef(u"KA"), cdef(u"KB", end=u"2024-03-31"), cdef(u"Kd", end=u"2024-03-31", start=u"2023-04-01")]
    return cpage(tbl([[fx(name=u"jppfs_cor:Ed", ctx=u"KA"), fx(name=u"jppfs_cor:Ed", ctx=u"KB")], [fx(name=u"jppfs_cor:Ed", ctx=u"KA"), fx(name=u"jppfs_cor:Ed", ctx=u"Kd")]]), defs)


def doc_nil():
    return cpage(tbl([[fx(ctx=u"KA"), fx(ctx=u"KB", nil=True)]]), [cdef(u"KA"), cdef(u"KB", end=u"2024-03-31")])


def doc_none():
    u"""決めが「無い」属性: 行 0 に scale が無い・行 1 に decimals が無い。"""
    return cpage(tbl([[fx(name=u"jppfs_cor:N0", dec=u"0", scale=None)], [fx(name=u"jppfs_cor:N1", dec=None, scale=u"3")]]), [cdef(u"KA")])


def doc_other():
    return cpage(tbl([[fx(extra=u' id="f1"'), fx(ctx=u"KB")]]), [cdef(u"KA"), cdef(u"KB", end=u"2024-03-31")])


def doc_other2():
    u"""1 行 4 つで全部同じ文脈。fact 0 だけが 3 つのそのほかの属性(escape・footnoteRefs・id)を持つ(そのほかの属性の数 3・持つ fact の数 1・fact の数 4 が互いに違う)。"""
    row = [fx(ctx=u"KA", extra=u' id="g1" escape="true" footnoteRefs="fn1"'), fx(ctx=u"KA"), fx(ctx=u"KA"), fx(ctx=u"KA")]
    return cpage(tbl([row]), [cdef(u"KA")])


def doc_nilhand():
    u"""表の 1 × 2(全部決まる)と、表の外の空の fact 1 つ(1 つずつ書く fact・unitRef は在る)。"""
    return cpage(tbl([[fx(ctx=u"KA"), fx(ctx=u"KB")]]) + fx(name=u"jppfs_cor:Ex", ctx=u"KA", nil=True), [cdef(u"KA"), cdef(u"KB", end=u"2024-03-31")])


def doc_forever():
    u"""3 行 × 1 列。文脈 KF は forever(期間の種類 N)・KA は使わない時点の文脈。全部決まる。"""
    return cpage(tbl([[fx(name=u"jppfs_cor:F%d" % r, ctx=u"KF")] for r in range(3)]), [cdef(u"KF", forever=True), cdef(u"KA")])


def doc_sign():
    u"""1 行 4 つ。負の字と sign が合う・負の字も sign も無い・sign だけ在る・負の字だけ在る。"""
    row = [u"△" + fx(sign=u"-"), fx(), fx(sign=u"-"), u"▲" + fx()]
    return cpage(tbl([row]), [cdef(u"KA")])


def doc_format():
    u"""1 行 4 つ。字の類 1(ダッシュ)・2・3 と、類 2 の中で format が違う 1 つ(類 2 の最頻は先の ixt:numdotdecimal)。"""
    row = [fx(text=u"-", fmt=u"ixt:zerodash"), fx(text=u"1,000"), fx(text=u"abc", fmt=u"ixt:other"), fx(text=u"2,000", fmt=u"ixt:numcommadecimal")]
    return cpage(tbl([row]), [cdef(u"KA")])


def doc_single_lines():
    u"""2 行 × 1 列。要素の線の上の fact は 1 つずつ(混ぜ物を作れない)。"""
    return cpage(tbl([[fx(name=u"jppfs_cor:S0")], [fx(name=u"jppfs_cor:S1")]]), [cdef(u"KA")])


def doc_odd0():
    u"""2 × 2 で全部同じ文脈。fact (0, 1) だけ unitRef が違う。行 0 の 1 つずつ書く fact でない fact は 1 つ(混ぜ物の当て先は行 1)。"""
    rows = [[fx(name=u"jppfs_cor:Rh", ctx=u"KA"), fx(name=u"jppfs_cor:Rh", ctx=u"KA", unit=u"USD")], [fx(name=u"jppfs_cor:Rh", ctx=u"KA"), fx(name=u"jppfs_cor:Rh", ctx=u"KA")]]
    return cpage(tbl(rows), [cdef(u"KA")])


def doc_dupmem():
    u"""3 行 × 1 列。R0・R1 の文脈は(期間・終わりの日・member の組)が同じで id が違う(member 付き)。R2 は時点で member は同じ。"""
    defs = [cdef(u"Dm1", start=u"2024-04-01", mem=MEM1), cdef(u"Dm2", start=u"2023-04-01", mem=MEM1), cdef(u"Cm", mem=MEM1)]
    return cpage(tbl([[fx(name=u"jppfs_cor:R0", ctx=u"Dm1")], [fx(name=u"jppfs_cor:R1", ctx=u"Dm2")], [fx(name=u"jppfs_cor:R2", ctx=u"Cm")]]), defs)


def doc_format2():
    u"""1 行 3 つ。類 2 の format は最頻(ixt:numdotdecimal 2 つ)が最初の fact(ixt:numcommadecimal)と違う。"""
    return cpage(tbl([[fx(text=u"1,000", fmt=u"ixt:numcommadecimal"), fx(text=u"2,000"), fx(text=u"3,000")]]), [cdef(u"KA")])


def doc_nilmix():
    u"""1 行 3 つ。空でない fact 1 つ(書式の類 3・decimals は 0)と空の fact 2 つ。空の fact を入れると最頻が「無い」に替わる。"""
    return cpage(tbl([[fx(text=u"abc", fmt=u"ixt:other", ctx=u"KA"), fx(ctx=u"KB", nil=True), fx(ctx=u"KC", nil=True)]]), [cdef(u"KA"), cdef(u"KB", end=u"2024-03-31"), cdef(u"KC", end=u"2023-03-31")])


def doc_nilunit():
    u"""2 行 × 3 列。行 0 は JPY(空でない)・USD(空)・USD(空)・行 1 は USD(空)・JPY(空でない)・USD(空)。行の unitRef の最頻は空の fact も入れた USD(列の決めでは決まる fact が増えない)。"""
    ds = [cdef(u"KA"), cdef(u"KB", end=u"2024-03-31"), cdef(u"KC", end=u"2023-03-31")]
    units = [[u"JPY", u"USD", u"USD"], [u"USD", u"JPY", u"USD"]]
    rows = [[fx(name=u"jppfs_cor:R%d" % r, ctx=u"K" + u"ABC"[c], unit=units[r][c], nil=(units[r][c] == u"USD")) for c in range(3)] for r in range(2)]
    return cpage(tbl(rows), ds)


def doc_nounit():
    return cpage(tbl([[fx(unit=None, ctx=u"KA"), fx(unit=None, ctx=u"KB")]]), [cdef(u"KA"), cdef(u"KB", end=u"2024-03-31")])


def doc_endrow():
    u"""2 行 × 3 列。終わりの日も member の組も要素の線(行)で決まる。"""
    defs = [cdef(u"Ke0", end=u"2024-03-31", mem=[(AXIS, u"jppfs_cor:Mem0")]), cdef(u"Ke1", mem=MEM1)]
    return cpage(tbl([[fx(name=u"jppfs_cor:R%d" % r, ctx=u"Ke%d" % r) for _c in range(3)] for r in range(2)]), defs)


def doc_padded():
    return cpage(tbl([[fx(ctx=u"KA"), fx(ctx=u"KB")]]), [cdef(u"KA", pad=True), cdef(u"KB", end=u"2024-03-31")])


def doc_unsorted():
    u"""文脈 Ku の member が定義の中で字の順に並んでいない。"""
    mem = [(u"jppfs_cor:BAxis", u"jppfs_cor:MemB"), (u"jppfs_cor:AAxis", u"jppfs_cor:MemA")]
    return cpage(tbl([[fx(ctx=u"Ku"), fx(ctx=u"Kv")]]), [cdef(u"Ku", mem=mem), cdef(u"Kv", end=u"2024-03-31")])


def doc_second_file():
    u"""2 つ目の .htm(頭の部が無い)。表の番号は file ごと。"""
    return u"<html><body>\n%s\n</body></html>\n" % tbl([[fx(name=u"jppfs_cor:Z0", ctx=u"KA"), fx(name=u"jppfs_cor:Z0", ctx=u"KB")]])


def doc_shuffled():
    u"""doc_r1 と同じ中身で fact の属性の並びが組む側の並びと違う(組み直した包みの字が元と違う)。"""
    defs = [cdef(u"KA"), cdef(u"KB", end=u"2024-03-31"), cdef(u"KM", mem=MEM1)]
    rows = [[fx(name=u"jppfs_cor:E0", ctx=c, dec=u"-3", scale=u"3", shuffle=True) for c in (u"KA", u"KB", u"KM")], [fx(name=u"jppfs_cor:E1", ctx=c, dec=u"0", shuffle=True) for c in (u"KA", u"KB", u"KM")]]
    return cpage(tbl(rows), defs)


def doc_only_outside():
    return cpage(fx() + fx(), [cdef(u"KA")])


def doc_missing():
    return cpage(tbl([[fx(ctx=u"KA"), fx(ctx=u"Kz9")]]), [cdef(u"KA")])


def doc_broken():
    return u"<html><body><table><tr><td>%s</td></table></body></html>" % fx(ctx=u"KA")


def write_pack(path, html, tag=u"1", extra=()):
    u"""作り物の包み 1 つ(PublicDoc に xsd・linkbase 5 つ・htm 1 つ・マニフェスト・画像)。"""
    base = u"XBRL/PublicDoc/jpcrp030000-asr-001_E9999%s-000_2026-03-31_01_2026-06-30" % tag
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(base + u".xsd", XSD)
        for s in (u"_cal", u"_def", u"_lab", u"_lab-en", u"_pre"):
            z.writestr(base + s + u".xml", LB)
        z.writestr(u"XBRL/PublicDoc/0100000_a_E9999%s-000_ixbrl.htm" % tag, html.encode("utf-8"))
        for n, h in extra:
            z.writestr(u"XBRL/PublicDoc/%s" % n, h.encode("utf-8"))
        z.writestr(u"XBRL/PublicDoc/manifest_PublicDoc.xml", b"<manifest/>")
        z.writestr(u"XBRL/PublicDoc/logo.png", b"PNG")


def make_docs(d, htmls):
    u"""作り物の置き場。書類ごとに包み 1 つ。ほかに有報でない zip を 1 つ。"""
    for i, h in enumerate(htmls, 1):
        write_pack(os.path.join(d, "S2FAKE%02d.zip" % i), h, u"%d" % i)
    with zipfile.ZipFile(os.path.join(d, "S2OTHER1.zip"), "w") as z:
        z.writestr("XBRL/PublicDoc/jpsps070000-xxx-001_E99999-000.xsd", b"<schema/>")
    return d


def alter_first_attr(ms, out):
    u"""出す folder の最初の nonFraction の name を別の字にする(比べ方 1 が違いを数えることを見る)。"""
    idx = ms.P.jload(ms.P.read_bytes(os.path.join(out, ms.P.INDEX_FILE)))
    p = os.path.join(out, idx["htm"][0]["tables"])
    tab = ms.P.jload(ms.P.read_bytes(p))
    for e in tab["F"]:
        if e["kind"] == "nonFraction":
            e["attrs"]["name"] = u"jppfs_cor:Altered"
            break
    ms.P.write_bytes(p, ms.P.jdump(tab))


def inproc(ms, log=None, fail_attrs=None, fail_build=None, alter_attrs=False, drop_build_file=False, second_build_differs=False):
    u"""別の process の呼び出し(``[python, -I, script, 命令, folder, folder]``)を、同じ process の中の同じ入口に替える。"""
    builds = []

    def proc(cmd, cwd, timeout):
        assert cmd[1] == "-I" and len(cmd) == 6, cmd
        if log is not None:
            log.append(cmd[3])
        buf = io.StringIO()
        old = sys.stderr
        sys.stderr = buf
        try:
            if cmd[3] == "attrs":
                if fail_attrs is not None:
                    return fail_attrs
                rc = ms.attrs_main(cmd[4:])
                if rc == 0 and alter_attrs:
                    alter_first_attr(ms, cmd[5])
            else:
                if fail_build is not None:
                    return fail_build
                rc = ms.P.build_main(cmd[4:])
                builds.append(cmd[5])
                if rc == 0 and drop_build_file:
                    os.remove(os.path.join(cmd[5], sorted(os.listdir(cmd[5]))[0]))
                if rc == 0 and second_build_differs and len(builds) == 2:
                    with open(os.path.join(cmd[5], sorted(os.listdir(cmd[5]))[0]), "ab") as fh:
                        fh.write(b" ")
        finally:
            sys.stderr = old
        return rc, buf.getvalue(), False
    return proc


def make_runner(mode=u"same", seen=None):
    u"""偽の道具。包みの sha256 を ``seen`` に足し、道具が書く CSV(fact と書き出し 7 つ)を ``mode`` どおりに書く: same(元と組み直しで同じ)・tax_differs(書き出しだけ違う)・facts_differs(fact だけ違う)。"""
    flags = ("--facts", "--concepts", "--pre", "--cal", "--dim", "--roleTypes", "--viewFile")

    def runner(cmd, timeout):
        z = cmd[cmd.index("-f") + 1]
        with open(z, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
        if seen is not None:
            seen.append(sha)
        for fl in flags:
            if fl in cmd:
                body = u"Name\nx%s\n" % (sha if mode == "facts_differs" else u"") if fl == "--facts" else u"h\nrow%s\n" % (sha if mode == "tax_differs" else u"")
                with io.open(cmd[cmd.index(fl) + 1], "w", encoding="utf-8") as fh:
                    fh.write(body)
        return u"", False
    return runner


FAKE_TOOL_INFO = od([(u"版", u"2.47.5"), (u"ModelValue.py の sha256", u"a" * 64), (u"package の一覧の sha256", u"b" * 64), (u"Python の版", u"3.11")])
fake_runner = make_runner()


def run_one(ms, html, d, tag=u"1", mode=u"same", seen=None, extra=(), **proc_kw):
    u"""作り物の書類 1 本を ``measure_one`` に通す(道具は偽の runner)。(rec, 呼んだ命令の並び)。"""
    z = os.path.join(d, "p%s.zip" % tag)
    write_pack(z, html, tag, extra)
    log = []
    tmp = os.path.join(d, "tmp")
    rec = ms.measure_one(u"tool", z, tmp if os.path.isdir(tmp) else None, make_runner(mode, seen), inproc(ms, log, **proc_kw))
    return rec, log


def make_folder(ms, html, d, tag=u"1", extra=()):
    u"""紙の folder まで(紙を作る命令)。(紙, 持ち込み側の情報, 元の表, 元の fact, folder)。"""
    z = os.path.join(d, "q%s.zip" % tag)
    write_pack(z, html, tag, extra)
    folder = os.path.join(d, "sheet%s" % tag)
    sheet, info, files, facts = ms.make_sheet_folder(ms.B.load_package(z), z, folder)
    return sheet, info, files, facts, folder


def roundtrip(ms, html, d, tag=u"1", extra=()):
    u"""紙の folder → 属性を作る(同じ process の入口)→ 元と比べる。dict(sheet, info, diff, by, files, new, folder)。"""
    sheet, info, files, facts, folder = make_folder(ms, html, d, tag, extra)
    out = os.path.join(d, "out%s" % tag)
    ms.write_attrs_folder(folder, out)
    idx = ms.P.jload(ms.P.read_bytes(os.path.join(out, ms.P.INDEX_FILE)))
    new = ms.P.load_htm_tables(out, idx)
    diff, by = ms.compare_attrs(files, new)
    return dict(sheet=sheet, info=info, diff=diff, by=dict(by), files=files, new=new, folder=folder, facts=facts)


def nf_attrs(files):
    return [dict(e["attrs"]) for _n, _p, F, _h in files for e in F if e["kind"] == "nonFraction"]


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XS0-1", (60, None)), ("XS0-2", (None, 0.2)), ("XS0-3", (4.8, 6.5)), ("XS0-4", (60, None)), ("XS0-5", (None, 2)), ("XS0-6", (33.6, 38)), ("XS0-7", (u"作れた数", None)), ("XS0-8", (2, 10))])
SEAL_BOUND_TEXT = od([("XS0-1", u"60 本以上"), ("XS0-2", u"fact の 0.2% 以下"), ("XS0-3", u"fact の 4.8% 以上 6.5% 未満"), ("XS0-4", u"60 本以上"), ("XS0-5", u"2 本以下"),
                      ("XS0-6", u"33.6% 以上 38% 未満"), ("XS0-7", u"作れた書類の全部"), ("XS0-8", u"fact の 2% 以上 10% 未満")])
SEAL_RULE_PHRASES = (
    u"`.htm` ごとの素の本文(便 XB0 の `strip_text`)・表 H・表 F のうち `nonFraction` でない行の全部・表 F の `nonFraction` の行の `kind`・`self`・`start`・`end`・`parent`(**数の置き場は持ち込み**)",
    u"元の包み・元の `.htm`・元の表 F の `nonFraction` の `attrs` を読まない。別の process で `python3 -I` で走らせ、folder に元の `attrs` が無いことを門で見る。",
    u"(a) 表の外 (b) 便 XA1 の段 2 で「全部決まる fact」でない (c) その fact の文脈と、期間の種類・終わりの日・member の組が同じ文脈の定義が、書類の中に 2 つ以上在る (d) その fact の文脈の期間の種類が、紙の「`name` ごとの期間の種類」と違う",
    u"`contextRef` は、表 H の中の文脈の定義のうち、期間の種類(`name` から)・終わりの日(その線の決め)・member の組(その線の決め)が同じ定義の `id`。ちょうど 1 つでなければ、その書類は「断った」",
    u"`sign` は、cell の開きタグの終わりから fact の `start` までの字(タグを除く)に便 XA0 の負の字が在れば `-`、無ければ付けない。",
    u"空の fact には `decimals`・`scale`・`format`・`sign` を付けず、`xsi:nil` を `true` にする。",
    u"字 `xs0:Changed` に変えて属性を作り直す。**その線の上の、1 つずつ書く fact でない fact の `name` だけが変わり、ほかの属性とほかの fact は 1 つも変わらない**なら「混ぜ物が効いた」。",
    u"書式の類の決めの数 + `name` ごとの期間の種類の数 + 表ごとの 3 + 要素の線 × 4 + 終わりの日の線 × 1 + member の組の線 × 1 + 空の fact の印の数 + そのほかの属性の数 + 1 つずつ書く fact × 7",
    u"**紙の欄の比** = 紙の欄の数 ÷(fact の数 × 7)",
    u"`fixtures/xbrl/cd8/sheet_build_2026-11-22.json`")
SEAL_LIMIT_PHRASES = (u"紙は答えから作っている", u"持ち込み", u"人が書く紙が正しいかは測っていない", u"「XBRL を作れる」「専用の道具が要らない」", u"その fact が元と同じになるのは当たり前", u"混ぜ物は 1 本につき 1 つ・`name` だけ")
LIMIT_PHRASES = (u"紙は答え(元の書類)から作っている", u"持ち込み(", u"人が書く紙が正しいかは測っていない", u"「XBRL を作れる」「専用の道具が要らない」", u"元と同じになるのは当たり前", u"混ぜ物は 1 本につき 1 つ・name だけ")


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out_ = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out_.append(u"script の封の commit・path・記録の path が門と違う")
    if RECORD_REL not in seal:
        out_.append(u"封に記録の path が無い")
    if ms.CELLS_PER_TABLE != 3 or ms.CELLS_PER_ELEMENT_LINE != 4 or ms.CELLS_PER_HAND_FACT != 7:
        out_.append(u"紙の欄の式の数(3・4・7)が封と違う")
    if tuple(ms.ATTRS) != ("name", "contextRef", "unitRef", "decimals", "scale", "sign", "format") or ms.NIL_ATTR != "xsi:nil":
        out_.append(u"1 つずつ書く fact の 7 つの値・空の fact の印が封と違う")
    if ms.MIX_NAME != u"xs0:Changed":
        out_.append(u"混ぜ物の name の字が封と違う")
    if ms.DOCS_WANT != 67 or ms.DEV_COUNT != 5 or ms.SUSPECT_DECLINED != 6:
        out_.append(u"67 本・開発の 5 本・欠陥を疑う条件の数が封と違う")
    if tuple(ms.STAGES) != (u"紙を作る", u"属性を作る", u"組む"):
        out_.append(u"断りの段が封と違う")
    if ms.TOOL_VERSION != ms.P.TOOL_VERSION or ms.SHA_P != ms.P.SHA_P or ms.YEAR != ms.P.YEAR or ms.TIMEOUT_SEC != ms.P.TIMEOUT_SEC:
        out_.append(u"道具の版・sha256・規則の年・時間の上限が便 XP0 と違う")
    for p in SEAL_RULE_PHRASES:
        if p not in seal:
            out_.append(u"封に字が無い: %s" % p[:30])
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS) or tuple(ms.BOUNDS_UPPER_EXCLUSIVE) != ("XS0-3", "XS0-6", "XS0-8"):
        out_.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [x for x in seal.splitlines() if x.startswith(u"| %s" % k)]
        if len(row_) != 1 or t not in row_[0]:
            out_.append(u"封の予測の行の字が違う: %s" % k)
    for p in SEAL_LIMIT_PHRASES:
        if p not in seal:
            out_.append(u"封に限界の字が無い: %s" % p)
    for p in LIMIT_PHRASES:
        if p not in u"".join(ms.LIMITS):
            out_.append(u"限界の字が script に無い: %s" % p)
    if u"docID・会社の名・EDINET コード・file の名・fact の値・要素の名・文脈の名・member の名・日付・表の字・紙の中身" not in seal and u"docID・会社の名・EDINET コード・file の名・fact の値・要素の名・文脈の名・member の名・日付・表の字" not in seal:
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


# ======================================================================== 2. 規則を 1 つずつ(作り物の書類)
CELLS_R1 = od([(u"書式の類の決め", 1), (u"name ごとの期間の種類", 2), (u"表ごとの 3", 3), (u"要素の線 × 4", 8), (u"終わりの日を決める側の線 × 1", 3), (u"member の組を決める側の線 × 1", 3),
               (u"空の fact の印", 0), (u"そのほかの属性", 0), (u"1 つずつ書く fact × 7", 0)])


def mixed(ms, r, d, tag):
    u"""混ぜ物の判定(使い捨ての folder で)。"""
    scratch = os.path.join(d, "mx%s" % tag)
    os.makedirs(scratch)
    return ms.mix_effect(r["folder"], r["sheet"], r["info"], ms.fact_ids(r["files"]), r["files"], scratch)


def reasons_of(info):
    return list(info["reasons"].values())


def rules_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        # --- R1 全部決まる(手で数える)
        r = roundtrip(ms, doc_r1(), d, u"1")
        want_eq(out_, u"R1 1 つずつ書く fact", r["info"]["hand"], [False] * 6)
        want_eq(out_, u"R1 理由", reasons_of(r["info"]), [0, 0, 0, 0])
        want_eq(out_, u"R1 attrs の違い", (r["diff"], r["by"]), (0, {}))
        s = r["sheet"]
        want_eq(out_, u"R1 書式", dict(s["format"]), {"2": "ixt:numdotdecimal"})
        want_eq(out_, u"R1 期間の種類", dict(s["kinds"]), {"jppfs_cor:E0": "I", "jppfs_cor:E1": "I"})
        t = s["tables"][0]
        want_eq(out_, u"R1 表の選び", (len(s["tables"]), t["orient"], t["end_src"], t["member_src"]), (1, "A", "C", "C"))
        want_eq(out_, u"R1 要素の線", dict(t["elements"]), {"0": ["jppfs_cor:E0", "JPY", "-3", "3"], "1": ["jppfs_cor:E1", "JPY", "0", None]})
        want_eq(out_, u"R1 終わりの日", dict(t["ends"]), {"0": "2025-03-31", "1": "2024-03-31", "2": "2025-03-31"})
        want_eq(out_, u"R1 member の組", dict(t["members"]), {"0": [], "1": [], "2": [[AXIS, u"jppfs_cor:Mem1"]]})
        want_eq(out_, u"R1 facts", list(s["facts"]), [])
        cells = ms.sheet_cells(s)
        want_eq(out_, u"R1 紙の欄の項", cells, CELLS_R1)
        want_eq(out_, u"R1 紙の欄の合計", sum(cells.values()), 20)
        want_eq(out_, u"R1 contextRef", [a["contextRef"] for a in nf_attrs(r["new"])], [u"KA", u"KB", u"KM"] * 2)
        # --- 表の外
        r = roundtrip(ms, doc_outside(), d, u"2")
        want_eq(out_, u"表の外 hand", r["info"]["hand"], [False, False, True])
        want_eq(out_, u"表の外 理由", reasons_of(r["info"]), [1, 0, 0, 0])
        want_eq(out_, u"表の外 diff", r["diff"], 0)
        want_eq(out_, u"表の外 values の数", ms.sheet_cells(r["sheet"])[u"1 つずつ書く fact × 7"], 7)
        # --- 全部決まらない fact(4 つの属性それぞれ)
        for i, kind in enumerate(("unit", "dec", "scale", "name")):
            r = roundtrip(ms, doc_odd(kind), d, u"3%d" % i)
            want_eq(out_, u"%s が違う fact hand" % kind, r["info"]["hand"], [False, False, False, True])
            want_eq(out_, u"%s が違う fact 理由" % kind, reasons_of(r["info"]), [0, 1, 0, 0])
            want_eq(out_, u"%s が違う fact diff" % kind, r["diff"], 0)
        # --- 文脈の定義が 2 つ以上
        r = roundtrip(ms, doc_dupctx(), d, u"4")
        want_eq(out_, u"重なる文脈 hand", r["info"]["hand"], [True, True, False])
        want_eq(out_, u"重なる文脈 理由", reasons_of(r["info"]), [0, 0, 2, 0])
        want_eq(out_, u"重なる文脈 diff", (r["diff"], [a["contextRef"] for a in nf_attrs(r["new"])]), (0, [u"Dx1", u"Dx2", u"Cu"]))
        # --- 期間の種類が name の決めと違う
        r = roundtrip(ms, doc_kind(), d, u"5")
        want_eq(out_, u"期間の種類が違う hand", r["info"]["hand"], [False, False, False, True])
        want_eq(out_, u"期間の種類が違う 理由", reasons_of(r["info"]), [0, 0, 0, 1])
        want_eq(out_, u"期間の種類が違う 決め", dict(r["sheet"]["kinds"]), {"jppfs_cor:Ed": "I"})
        want_eq(out_, u"期間の種類が違う diff", r["diff"], 0)
        # --- 空の fact
        r = roundtrip(ms, doc_nil(), d, u"6")
        want_eq(out_, u"空の fact hand", r["info"]["hand"], [False, False])
        want_eq(out_, u"空の fact の印", [(f["index"], f.get("nil")) for f in r["sheet"]["facts"]], [(1, True)])
        want_eq(out_, u"空の fact の attrs", nf_attrs(r["new"])[1], {"name": "jppfs_cor:E0", "contextRef": "KB", "unitRef": "JPY", "xsi:nil": "true"})
        want_eq(out_, u"空の fact diff", r["diff"], 0)
        want_eq(out_, u"空の fact の印の欄", ms.sheet_cells(r["sheet"])[u"空の fact の印"], 1)
        # --- 決めが「無い」
        r = roundtrip(ms, doc_none(), d, u"7")
        want_eq(out_, u"無い属性 要素の線", dict(r["sheet"]["tables"][0]["elements"]), {"0": ["jppfs_cor:N0", "JPY", "0", None], "1": ["jppfs_cor:N1", "JPY", None, "3"]})
        want_eq(out_, u"無い属性 attrs", ["scale" in a for a in nf_attrs(r["new"])] + ["decimals" in a for a in nf_attrs(r["new"])], [False, True, True, False])
        want_eq(out_, u"無い属性 diff", r["diff"], 0)
        # --- そのほかの属性
        r = roundtrip(ms, doc_other(), d, u"8")
        want_eq(out_, u"そのほかの属性 紙", [(f["index"], dict(f["other"]), "values" in f) for f in r["sheet"]["facts"]], [(0, {"id": "f1"}, False)])
        want_eq(out_, u"そのほかの属性 数", (r["info"]["other_facts"], ms.sheet_cells(r["sheet"])[u"そのほかの属性"], r["diff"], nf_attrs(r["new"])[0].get("id")), (1, 1, 0, "f1"))
        # --- そのほかの属性が 1 fact に 3 つ(属性の数で数える・fact の数で数えない)
        r = roundtrip(ms, doc_other2(), d, u"8b")
        want_eq(out_, u"そのほかの属性 3 つ 紙", [(f["index"], dict(f["other"]), "values" in f) for f in r["sheet"]["facts"]], [(0, {"escape": "true", "footnoteRefs": "fn1", "id": "g1"}, False)])
        want_eq(out_, u"そのほかの属性 3 つ hand", r["info"]["hand"], [False] * 4)
        want_eq(out_, u"そのほかの属性 3 つ 数", (r["info"]["other_facts"], ms.sheet_cells(r["sheet"])[u"そのほかの属性"], r["diff"]), (1, 3, 0))
        want_eq(out_, u"そのほかの属性 3 つ attrs", (nf_attrs(r["new"])[0].get("escape"), nf_attrs(r["new"])[0].get("footnoteRefs"), nf_attrs(r["new"])[0].get("id")), ("true", "fn1", "g1"))
        want_eq(out_, u"そのほかの属性 3 つ 紙の欄の合計", sum(ms.sheet_cells(r["sheet"]).values()), 1 + 1 + 3 + 4 + 4 + 4 + 0 + 3 + 0)  # 書式 1・kinds 1・表 3・線 1 本 × 4・終わりの日は列ごと 4・member も列ごと 4・そのほか 3
        # --- 1 つずつ書く fact(表の外)で空の fact: xsi:nil が在り decimals・scale・format・sign は無い
        r = roundtrip(ms, doc_nilhand(), d, u"6b")
        want_eq(out_, u"1 つずつ書く空の fact hand", (r["info"]["hand"], reasons_of(r["info"])), ([False, False, True], [1, 0, 0, 0]))
        want_eq(out_, u"1 つずつ書く空の fact 紙", [(f["index"], f.get("nil"), "values" in f) for f in r["sheet"]["facts"]], [(2, True, True)])
        got_ = nf_attrs(r["new"])[2]
        want_eq(out_, u"1 つずつ書く空の fact の attrs", got_, {"name": "jppfs_cor:Ex", "contextRef": "KA", "unitRef": "JPY", "xsi:nil": "true"})
        want_eq(out_, u"1 つずつ書く空の fact に値の属性が無い", [k for k in ("decimals", "scale", "format", "sign") if k in got_], [])
        want_eq(out_, u"1 つずつ書く空の fact diff", r["diff"], 0)
        want_eq(out_, u"1 つずつ書く空の fact の欄", (ms.sheet_cells(r["sheet"])[u"空の fact の印"], ms.sheet_cells(r["sheet"])[u"1 つずつ書く fact × 7"]), (1, 7))
        # --- forever の文脈(期間の種類 N)
        r = roundtrip(ms, doc_forever(), d, u"6c")
        want_eq(out_, u"forever kinds", dict(r["sheet"]["kinds"]), {"jppfs_cor:F0": "N", "jppfs_cor:F1": "N", "jppfs_cor:F2": "N"})
        want_eq(out_, u"forever hand・diff", (r["info"]["hand"], r["diff"], [a["contextRef"] for a in nf_attrs(r["new"])]), ([False] * 3, 0, [u"KF"] * 3))
        # --- 負の字
        r = roundtrip(ms, doc_sign(), d, u"9")
        want_eq(out_, u"符号 hand", r["info"]["hand"], [False, False, True, True])
        want_eq(out_, u"符号 理由", reasons_of(r["info"]), [0, 2, 0, 0])
        want_eq(out_, u"符号 attrs", ([a.get("sign") for a in nf_attrs(r["new"])], r["diff"]), ([u"-", None, u"-", None], 0))
        # --- 書式の類
        r = roundtrip(ms, doc_format(), d, u"10")
        want_eq(out_, u"書式 決め", dict(r["sheet"]["format"]), {"1": "ixt:zerodash", "2": "ixt:numdotdecimal", "3": "ixt:other"})
        want_eq(out_, u"書式 hand", r["info"]["hand"], [False, False, False, True])
        want_eq(out_, u"書式 attrs", ([a.get("format") for a in nf_attrs(r["new"])], r["diff"]), ([u"ixt:zerodash", u"ixt:numdotdecimal", u"ixt:other", u"ixt:numcommadecimal"], 0))
        # --- 混ぜ物
        r = roundtrip(ms, doc_r1(), d, u"11")
        want_eq(out_, u"混ぜ物 R1", mixed(ms, r, d, u"11"), (True, True))
        want_eq(out_, u"混ぜ物 当て先", ms.mix_target(r["info"])[:3], (0, 0, 0))
        r = roundtrip(ms, doc_single_lines(), d, u"12")
        want_eq(out_, u"混ぜ物 1 つだけの線", mixed(ms, r, d, u"12"), (False, False))
        r = roundtrip(ms, doc_only_outside(), d, u"13")
        want_eq(out_, u"混ぜ物 表の外だけ", mixed(ms, r, d, u"13"), (False, False))
        # --- 混ぜ物の当て先は 1 つずつ書く fact でない fact が 2 つ以上乗っている線(行 0 には 1 つしか無い)
        r = roundtrip(ms, doc_odd0(), d, u"20")
        want_eq(out_, u"片端だけ違う 2x2 hand", r["info"]["hand"], [False, True, False, False])
        want_eq(out_, u"片端だけ違う 2x2 当て先", ms.mix_target(r["info"])[:3], (0, 0, 1))
        want_eq(out_, u"片端だけ違う 2x2 混ぜ物", mixed(ms, r, d, u"20"), (True, True))
        # --- member 付きで id が重なる文脈
        r = roundtrip(ms, doc_dupmem(), d, u"21")
        want_eq(out_, u"member 付きの重なる文脈", (r["info"]["hand"], reasons_of(r["info"]), r["diff"]), ([True, True, False], [0, 0, 2, 0], 0))
        # --- 書式の最頻が最初の fact と違う
        r = roundtrip(ms, doc_format2(), d, u"22")
        want_eq(out_, u"書式の最頻", (dict(r["sheet"]["format"]), r["info"]["hand"], [a.get("format") for a in nf_attrs(r["new"])], r["diff"]),
                ({"2": "ixt:numdotdecimal"}, [True, False, False], [u"ixt:numcommadecimal", u"ixt:numdotdecimal", u"ixt:numdotdecimal"], 0))
        # --- 空の fact は書式の最頻・decimals の最頻に入らない・unitRef の最頻には入る
        r = roundtrip(ms, doc_nilmix(), d, u"23")
        want_eq(out_, u"空の fact を混ぜた線", (dict(r["sheet"]["format"]), dict(r["sheet"]["tables"][0]["elements"]), r["info"]["hand"], r["diff"]),
                ({"3": "ixt:other"}, {"0": ["jppfs_cor:E0", "JPY", "0", None]}, [False, False, False], 0))
        r = roundtrip(ms, doc_nilunit(), d, u"24")
        want_eq(out_, u"空の fact が多い線の unitRef", (r["sheet"]["tables"][0]["orient"], r["sheet"]["tables"][0]["elements"]["0"][1], r["info"]["hand"], r["diff"]), (u"A", u"USD", [True, False, False, False, True, False], 0))
        # --- unitRef の無い fact
        r = roundtrip(ms, doc_nounit(), d, u"25")
        want_eq(out_, u"unitRef の無い fact", (r["sheet"]["tables"][0]["elements"]["0"][1], ["unitRef" in a for a in nf_attrs(r["new"])], r["diff"]), (None, [False, False], 0))
        # --- 終わりの日・member の組を要素の線で決める表
        r = roundtrip(ms, doc_endrow(), d, u"26")
        t0_ = r["sheet"]["tables"][0]
        want_eq(out_, u"要素の線で決まる表", ((t0_["orient"], t0_["end_src"], t0_["member_src"]), sorted(t0_["ends"]), r["info"]["hand"], r["diff"]), (("A", "E", "E"), ["0", "1"], [False] * 6, 0))
        # --- 日の字の前後の空白・member の組の並び
        r = roundtrip(ms, doc_padded(), d, u"27")
        want_eq(out_, u"日の字の空白", (r["sheet"]["tables"][0]["ends"]["0"], r["diff"]), (u"2025-03-31", 0))
        r = roundtrip(ms, doc_unsorted(), d, u"28")
        want_eq(out_, u"member の組の並び", (r["sheet"]["tables"][0]["members"]["0"], r["diff"]), ([[u"jppfs_cor:AAxis", u"jppfs_cor:MemA"], [u"jppfs_cor:BAxis", u"jppfs_cor:MemB"]], 0))
        # --- 2 つ目の .htm(表の番号は file ごと)
        r = roundtrip(ms, doc_r1(), d, u"29", extra=[(u"0200000_b_E99999-000_ixbrl.htm", doc_second_file())])
        want_eq(out_, u"2 つの file", ([(t_["file"], t_["table"]) for t_ in r["sheet"]["tables"]], r["info"]["hand"], r["diff"]), ([(0, 0), (1, 0)], [False] * 8, 0))
        # --- 混ぜ物の判定そのもの(紙の写しを替える関数を差し替えて、判定が違いを見つける)
        r = roundtrip(ms, doc_r1(), d, u"40")
        saved = ms.mixed_sheet
        try:
            ms.mixed_sheet = lambda sheet, target: copy.deepcopy(sheet)
            want_eq(out_, u"混ぜ物 name を替えない紙", mixed(ms, r, d, u"40a"), (True, False))

            def also_other_line(sheet, target):
                m = saved(sheet, target)
                m["tables"][0]["elements"]["1"][0] = u"jppfs_cor:E0"
                return m
            ms.mixed_sheet = also_other_line
            want_eq(out_, u"混ぜ物 ほかの線も替わる紙", mixed(ms, r, d, u"40b"), (True, False))
        finally:
            ms.mixed_sheet = saved
        # --- 断り(紙を作る命令)
        z = os.path.join(d, "m.zip")
        write_pack(z, doc_missing(), u"14")
        want_eq(out_, u"定義の無い contextRef", refuses(ms, ms.make_sheet_folder, ms.B.load_package(z), z, os.path.join(d, "mf")), ms.A1.R_CTX_MISSING)
        write_pack(z, doc_broken(), u"15")
        want_eq(out_, u"表が読めない", refuses(ms, ms.make_sheet_folder, ms.B.load_package(z), z, os.path.join(d, "mg")), ms.X.R_TABLE)
    return out_


# ======================================================================== 3. 紙の値・紙に無いもの
def attrs_with(ms, folder, d, edit, tag):
    u"""紙の folder の写しの紙を ``edit`` で替えて属性を作る。(属性の並び か 断りの理由)。"""
    copy_ = os.path.join(d, "edit%s" % tag)
    shutil.copytree(folder, copy_)
    p = os.path.join(copy_, ms.SHEET_FILE)
    sheet = json.loads(read_text(p), object_pairs_hook=od)
    edit(sheet)
    ms.P.write_bytes(p, ms.P.jdump(sheet))
    try:
        _ix, files = ms.attrs_tables(copy_)
    except ms.Refuse as exc:
        return exc.reason
    return nf_attrs(files)


def with_h_edit(ms, folder, d, edit, tag):
    u"""紙の folder の写しの表 H を ``edit`` で替えて属性を作る。断りの理由か、断らなければ None。"""
    copy_ = os.path.join(d, "edith%s" % tag)
    shutil.copytree(folder, copy_)
    idx = ms.P.jload(ms.P.read_bytes(os.path.join(copy_, ms.P.INDEX_FILE)))
    p = os.path.join(copy_, idx["htm"][0]["tables"])
    tab = ms.P.jload(ms.P.read_bytes(p))
    edit(tab)
    ms.P.write_bytes(p, ms.P.jdump(tab))
    return refuses(ms, ms.attrs_tables, copy_)


def paper_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        r = roundtrip(ms, doc_r1(), d, u"1")
        base = nf_attrs(r["new"])
        folder = r["folder"]

        def changed(edit, tag):
            got = attrs_with(ms, folder, d, edit, tag)
            return got if isinstance(got, str) else [i for i, (a, b) in enumerate(zip(base, got)) if a != b]
        t0 = lambda s: s["tables"][0]
        # 1 つの値を変えると、その値が効く fact だけの attrs が変わる(行 0 = fact 0〜2)
        want_eq(out_, u"紙 name", changed(lambda s: t0(s)["elements"]["0"].__setitem__(0, u"jppfs_cor:E1"), "a"), [0, 1, 2])
        want_eq(out_, u"紙 unitRef", changed(lambda s: t0(s)["elements"]["0"].__setitem__(1, u"USD"), "b"), [0, 1, 2])
        want_eq(out_, u"紙 decimals", changed(lambda s: t0(s)["elements"]["0"].__setitem__(2, u"5"), "c"), [0, 1, 2])
        want_eq(out_, u"紙 scale", changed(lambda s: t0(s)["elements"]["1"].__setitem__(3, u"6"), "d"), [3, 4, 5])
        want_eq(out_, u"紙 format", changed(lambda s: s["format"].__setitem__("2", u"ixt:x"), "e"), [0, 1, 2, 3, 4, 5])
        want_eq(out_, u"紙 終わりの日", changed(lambda s: t0(s)["ends"].__setitem__("0", u"2024-03-31"), "f"), [0, 3])
        want_eq(out_, u"紙 member の組", changed(lambda s: t0(s)["members"].__setitem__("0", [[AXIS, u"jppfs_cor:Mem1"]]), "g"), [0, 3])
        want_eq(out_, u"紙 sign を付けない決め(負の字が無ければ変わらない)", changed(lambda s: s.__setitem__("kinds", s["kinds"]), "h"), [])
        # 紙の 1 つずつ書く fact の値・空の印・そのほかの属性
        want_eq(out_, u"紙 1 つずつ書く fact", changed(lambda s: s["facts"].append(od([("file", 0), ("index", 0), ("values", [u"jppfs_cor:E1", u"KB", None, None, None, None, None])])), "i"), [0])
        want_eq(out_, u"紙 空の印", changed(lambda s: s["facts"].append(od([("file", 0), ("index", 1), ("nil", True)])), "j"), [1])
        want_eq(out_, u"紙 そのほかの属性", changed(lambda s: s["facts"].append(od([("file", 0), ("index", 2), ("other", od([("id", u"zz")]))])), "k"), [2])
        # 断る(文脈が 1 つに決まらない・紙に表が無い・期間の種類が無い・向きを替える)
        want_eq(out_, u"紙 期間の種類を替える", changed(lambda s: s["kinds"].__setitem__("jppfs_cor:E0", u"D"), "l"), ms.R_CTX_AMBIG)
        want_eq(out_, u"紙 表を消す", changed(lambda s: s["tables"].pop(), "m"), ms.R_PAPER)
        want_eq(out_, u"紙 期間の種類を消す", changed(lambda s: s["kinds"].pop("jppfs_cor:E0"), "n"), ms.R_KIND)
        want_eq(out_, u"紙 向きを替える", changed(lambda s: t0(s).__setitem__("orient", "B"), "o"), ms.R_PAPER)
        want_eq(out_, u"紙 name の決めを消す", changed(lambda s: t0(s)["elements"]["0"].__setitem__(0, None), "p"), ms.R_KIND)
        # 重なる文脈の fact の 1 つずつ書く印を消すと、文脈が 1 つに決まらず断る
        r2 = roundtrip(ms, doc_dupctx(), d, u"2p")
        want_eq(out_, u"紙 重なる文脈の印を消す", attrs_with(ms, r2["folder"], d, lambda s: s.__setitem__("facts", []), "q"), ms.R_CTX_AMBIG)

        # 終わりの日・member の組を要素の線で決める表では、その線の値を変えるとその行の contextRef が変わる
        r3 = roundtrip(ms, doc_endrow(), d, u"3p")
        base3 = nf_attrs(r3["new"])

        def changed3(edit, tag):
            got = attrs_with(ms, r3["folder"], d, edit, tag)
            return got if isinstance(got, str) else [i for i, (a, b) in enumerate(zip(base3, got)) if a != b]
        want_eq(out_, u"紙 要素の線の終わりの日だけ替える(その文脈は無い)", changed3(lambda s: s["tables"][0]["ends"].__setitem__("0", u"2025-03-31"), "s"), ms.R_CTX_AMBIG)
        want_eq(out_, u"紙 要素の線の member の組だけ替える(その文脈は無い)", changed3(lambda s: s["tables"][0]["members"].__setitem__("1", [[AXIS, u"jppfs_cor:Mem0"]]), "t"), ms.R_CTX_AMBIG)

        def row0_as_row1(s):
            s["tables"][0]["ends"]["0"] = u"2025-03-31"
            s["tables"][0]["members"]["0"] = [[AXIS, u"jppfs_cor:Mem1"]]
        want_eq(out_, u"紙 要素の線の終わりの日と member の組を行 1 と同じにする", (changed3(row0_as_row1, "u"), [a["contextRef"] for a in attrs_with(ms, r3["folder"], d, row0_as_row1, "u2")][:3]), ([0, 1, 2], [u"Ke1"] * 3))
        # 表 H に同じ id で中身の違う文脈が在ると断る
        def dup_h(tab):
            c0 = copy.deepcopy([x for x in tab["H"]["resources"] if x.get("type") == "context"][0])
            c0["period"] = [["xbrli:instant", u"2020-01-01"]]
            tab["H"]["resources"].append(c0)
        want_eq(out_, u"表 H に同じ id で中身の違う文脈", with_h_edit(ms, folder, d, dup_h, "r"), ms.A1.R_CTX_DUP)
        # 紙に元の contextRef の字が無い(1 つずつ書く fact でない fact の分)
        text = read_text(os.path.join(folder, ms.SHEET_FILE))
        for ref in (u"KA", u"KB", u"KM"):
            if u'"%s"' % ref in text:
                out_.append(u"紙に 1 つずつ書く fact でない fact の contextRef の字が在る: %s" % ref)
        want_eq(out_, u"紙の folder の元の attrs", ms.leak_problems(folder), 0)
        # 元の attrs が folder に在れば数える(門が数える)
        leaky = os.path.join(d, "leaky")
        shutil.copytree(folder, leaky)
        idx = ms.P.jload(ms.P.read_bytes(os.path.join(leaky, ms.P.INDEX_FILE)))
        tp = os.path.join(leaky, idx["htm"][0]["tables"])
        tab = ms.P.jload(ms.P.read_bytes(tp))
        tab["F"][0]["attrs"] = {"name": "x"}
        ms.P.write_bytes(tp, ms.P.jdump(tab))
        want_eq(out_, u"元の attrs を置けば数える", ms.leak_problems(leaky), 1)
        # 紙の folder の本文の表の nonFraction 以外の行は元のまま・nonFraction の kind・start・end・parent は元のまま
        for (_n, _p, F, _h), (_n2, _p2, F2, _h2) in zip(r["files"], ms.P.load_htm_tables(folder, idx)):
            for e, e2 in zip(F, F2):
                if [e[k] for k in ("kind", "self", "start", "end", "parent")] != [e2[k] for k in ("kind", "self", "start", "end", "parent")] or (e["kind"] != "nonFraction" and e["attrs"] != e2["attrs"]):
                    out_.append(u"持ち込みが元と違う")
        # 紙の欄の数は紙の file を読み戻した値(書いた file を数える)
        want_eq(out_, u"紙の欄の数(読み戻し)", sum(ms.sheet_cells(ms.P.jload(ms.P.read_bytes(os.path.join(folder, ms.SHEET_FILE)))).values()), 20)
        # 混ぜ物の紙の写しは当て先の線だけ替える
        t = ms.mix_target(r["info"])
        m = ms.mixed_sheet(r["sheet"], t)
        want_eq(out_, u"混ぜ物の紙", (m["tables"][0]["elements"]["0"][0], m["kinds"].get(u"xs0:Changed"), r["sheet"]["tables"][0]["elements"]["0"][0]), (u"xs0:Changed", u"I", u"jppfs_cor:E0"))
    return out_


# ======================================================================== 4. 答えを読まない(字で縛る)
BLIND_FUNCS = ("attrs_tables", "write_attrs_folder", "attrs_main", "decided_attrs", "read_context", "context_index", "table_lookup", "values_attrs")
BLIND_DENY_ATTRS = ("doc_texts", "facts_of_files", "facts_of_text", "load_package", "peel_tables", "context_defs", "resolve_facts", "strip_text", "build_files", "contexts_of_text", "build_sheet",
                    "make_sheet_folder", "peel_folder")
BLIND_DENY_NAMES = ("make_sheet_folder", "build_sheet", "mix_effect", "compare_attrs", "measure_one", "blank_row", "fact_ids", "sheet_main", "sheet_cells", "mix_target")
BLIND_DENY_ARGS = ("entries", "zip_path", "zip", "orig", "original", "facts", "files_orig")


def blind_problems(src=None):
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out_ = []
    funcs = dict((n.name, n) for n in tree.body if isinstance(n, ast.FunctionDef))
    for name in BLIND_FUNCS:
        fn = funcs.get(name)
        if fn is None:
            out_.append(u"答えを読まない側の関数が無い: %s" % name)
            continue
        args = [a.arg for a in fn.args.args + fn.args.kwonlyargs]
        if any(a in BLIND_DENY_ARGS for a in args):
            out_.append(u"%s が元の包み・元の fact を受け取れる形(引数 %s)" % (name, args))
        for n in ast.walk(fn):
            if isinstance(n, ast.Attribute) and n.attr in BLIND_DENY_ATTRS:
                out_.append(u"%s が答えを読む関数 %s を呼んでいる" % (name, n.attr))
            if isinstance(n, ast.Name) and n.id in BLIND_DENY_NAMES:
                out_.append(u"%s が答えを読む側の関数 %s を呼んでいる" % (name, n.id))
    for name in ("attrs_command", "exec_attrs"):
        if name not in funcs:
            out_.append(u"%s が無い" % name)
    cmd = funcs.get("attrs_command")
    if cmd is not None:
        args = [a.arg for a in cmd.args.args]
        body = ast.dump(cmd.body[-1])
        if args != ["folder", "out"] or "Constant(value='-I')" not in body or "Constant(value='attrs')" not in body or "SCRIPT_PATH" not in body:
            out_.append(u"属性を作る命令の呼び方が python3 -I ... attrs <folder> <folder> でない")
    am = funcs.get("attrs_main")
    if am is not None and "len(args) != 2" not in ast.get_source_segment(src, am):
        out_.append(u"属性を作る命令が引数の数(2)を見ない")
    main = funcs.get("main")
    if main is not None and 'argv[0] == "attrs"' not in ast.get_source_segment(src, main):
        out_.append(u"main が attrs を別の入口に渡していない")
    return out_


def blind_behaviour_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    err = io.StringIO()
    old = sys.stderr
    sys.stderr = err
    try:
        rcs = (ms.attrs_main([]), ms.attrs_main(["a"]), ms.attrs_main(["a", "b", "c"]), ms.attrs_main(["/nonexistent/x", "/nonexistent/y"]))
    finally:
        sys.stderr = old
    want_eq(out_, u"attrs の終わりの値", rcs, (ms.EXIT_USAGE, ms.EXIT_USAGE, ms.EXIT_USAGE, ms.EXIT_DECLINE))
    want_eq(out_, u"attrs の命令の並び", ms.attrs_command(u"F", u"O")[1:], [u"-I", ms.SCRIPT_PATH, u"attrs", u"F", u"O"])
    with Temp() as d:
        # 属性を作る命令は元の包みを使わない: 包みを消した folder でも作れる
        sheet, info, files, facts, folder = make_folder(ms, doc_r1(), d, u"1")
        os.remove(os.path.join(d, "q1.zip"))
        ms.write_attrs_folder(folder, os.path.join(d, "o"))
        # 出す folder の file の集まりは紙の folder から紙を除いたもの
        want_eq(out_, u"出す folder の file", sorted(os.listdir(os.path.join(d, "o"))), sorted(x for x in os.listdir(folder) if x != ms.SHEET_FILE))
        # 呼び出し(proc)の失敗の読み
        z = os.path.join(d, "x.zip")
        write_pack(z, doc_r1(), u"2")
        want_eq(out_, u"exec_attrs の断り", ms.exec_attrs(folder, os.path.join(d, "o2"), d, lambda c, w, t: (2, u"DECLINE: 理由\n", False))[:2], (False, u"理由"))
        want_eq(out_, u"exec_attrs の終わりの値", ms.exec_attrs(folder, os.path.join(d, "o3"), d, lambda c, w, t: (1, u"", False))[:2], (False, u"属性を作る命令が 0 でない終わりの値で終わった"))
        want_eq(out_, u"exec_attrs の時間", ms.exec_attrs(folder, os.path.join(d, "o4"), d, lambda c, w, t: (None, u"", True))[:2], (False, u"属性を作る命令が時間の上限を超えた"))
    return out_


# ======================================================================== 5. 書類 1 本の通し・塊・記録
def measure_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        os.makedirs(os.path.join(d, "tmp"))
        rec, log = run_one(ms, doc_r1(), d, u"1")
        want_eq(out_, u"通し 呼んだ命令", log, [u"attrs", u"build", u"build"])
        want_eq(out_, u"通し 断り", (rec[u"断った"], rec[u"断った段"], rec[u"断った理由"]), (False, u"", u""))
        want_eq(out_, u"通し 数", (rec[u"fact の数"], rec[u"1 つずつ書く fact の数"], rec[u"そのほかの属性を持つ fact の数"], rec[u"紙の欄の数"]), (6, 0, 0, 20))
        want_eq(out_, u"通し 比べ方 1", (rec[u"属性を作れた"], rec[u"表 F が同じ"], rec[u"attrs が違う fact の数"]), (True, True, 0))
        want_eq(out_, u"通し 組む", (rec[u"組めた"], rec[u"2 回組んで同じ"]), (True, True))
        want_eq(out_, u"通し 混ぜ物", dict(rec[u"混ぜ物"]), {u"作れた": True, u"効いた": True})
        want_eq(out_, u"通し 道具の読みが同じ", (rec[u"fact が同じ"], rec[u"タクソノミが同じ"], rec[u"鳴り方が同じ"], rec[u"全部同じ"]), (True, True, True, True))
        want_eq(out_, u"通し 秒の欄", (rec[u"属性を作る命令の秒"] is not None, rec[u"組む命令の秒"] is not None, rec[u"組み直しの 1 回"] is not None), (True, True, True))
        want_eq(out_, u"通し 比べ方 1 の違いの欄", list(rec[u"attrs が違う属性ごとの fact の数(重ねて数える)"]), [ms.ATTR_LABELS[k] for k in ms.B.NUM_ATTRS])
        # 道具の読みが違う書類(偽の道具が書き出しだけ・fact だけ違う CSV を書く)
        rec, _log = run_one(ms, doc_shuffled(), d, u"1a", mode=u"tax_differs")
        want_eq(out_, u"通し 書き出しだけ違う", (rec[u"fact が同じ"], rec[u"タクソノミが同じ"], rec[u"全部同じ"]), (True, False, False))
        rec, _log = run_one(ms, doc_shuffled(), d, u"1b", mode=u"facts_differs")
        want_eq(out_, u"通し fact だけ違う", (rec[u"fact が同じ"], rec[u"タクソノミが同じ"], rec[u"全部同じ"]), (False, True, False))
        # 組み直した包みを道具に掛ける(元の包みを 2 度掛けない): 属性の並びの違う書類で、元の包みと組み直した包みの字が違う
        seen = []
        rec, _log = run_one(ms, doc_shuffled(), d, u"1c", seen=seen)
        want_eq(out_, u"通し 道具に掛けた包み", (len(seen), seen[0] == seen[1], seen[2] == seen[3], seen[0] != seen[2]) if len(seen) == 4 else len(seen), (4, True, True, True))
        # 1 つずつ書く fact の理由の数(書類の中)
        rec, _log = run_one(ms, doc_dupctx(), d, u"2")
        want_eq(out_, u"通し 重なる文脈", (rec[u"1 つずつ書く fact の数"], list(rec[u"1 つずつ書く fact の理由(重ねて数える)"].values()), rec[u"表 F が同じ"]), (2, [0, 0, 2, 0], True))
        rec, _log = run_one(ms, doc_other(), d, u"3")
        want_eq(out_, u"通し そのほかの属性", (rec[u"そのほかの属性を持つ fact の数"], rec[u"紙の欄の数(項ごと)"][u"そのほかの属性"], rec[u"表 F が同じ"]), (1, 1, True))
        rec, _log = run_one(ms, doc_outside(), d, u"3a")
        want_eq(out_, u"通し 表の外", (rec[u"1 つずつ書く fact の数"], rec[u"属性を作れた"], rec[u"表 F が同じ"], rec[u"組めた"]), (1, True, True, True))
        rec, _log = run_one(ms, doc_other2(), d, u"3c")
        want_eq(out_, u"通し そのほかの属性 3 つ", (rec[u"そのほかの属性を持つ fact の数"], rec[u"紙の欄の数(項ごと)"][u"そのほかの属性"], rec[u"表 F が同じ"]), (1, 3, True))
        rec, _log = run_one(ms, doc_nilhand(), d, u"3d")
        want_eq(out_, u"通し 1 つずつ書く空の fact", (rec[u"1 つずつ書く fact の数"], rec[u"紙の欄の数(項ごと)"][u"空の fact の印"], rec[u"表 F が同じ"], rec[u"attrs が違う fact の数"]), (1, 1, True, 0))
        rec, _log = run_one(ms, doc_nil(), d, u"3b")
        want_eq(out_, u"通し 空の fact", (rec[u"紙の欄の数(項ごと)"][u"空の fact の印"], rec[u"表 F が同じ"]), (1, True))
        # 断り: 紙を作る・属性を作る・組む
        rec, log = run_one(ms, doc_missing(), d, u"4")
        want_eq(out_, u"断り 紙を作る", (rec[u"断った"], rec[u"断った段"], rec[u"断った理由"], rec[u"fact の数"], log), (True, u"紙を作る", ms.A1.R_CTX_MISSING, None, []))
        rec, log = run_one(ms, doc_broken(), d, u"5")
        want_eq(out_, u"断り 表が読めない", (rec[u"断った段"], rec[u"断った理由"]), (u"紙を作る", ms.X.R_TABLE))
        rec, log = run_one(ms, doc_r1(), d, u"6", fail_attrs=(2, u"DECLINE: 紙の理由\n", False))
        want_eq(out_, u"断り 属性を作る", (rec[u"断った段"], rec[u"断った理由"], rec[u"属性を作れた"], rec[u"組めた"], log, rec[u"fact の数"], rec[u"紙の欄の数"]), (u"属性を作る", u"紙の理由", False, False, [u"attrs"], 6, 20))
        rec, log = run_one(ms, doc_r1(), d, u"7", fail_build=(1, u"", False))
        want_eq(out_, u"断り 組む", (rec[u"断った段"], rec[u"断った理由"], rec[u"属性を作れた"], rec[u"表 F が同じ"], rec[u"組めた"]), (u"組む", u"組む命令が 0 でない終わりの値で終わった", True, True, False))
        rec, log = run_one(ms, doc_r1(), d, u"7a", drop_build_file=True)
        want_eq(out_, u"断り 出す folder の file が足りない", (rec[u"断った段"], rec[u"断った理由"], rec[u"組めた"]), (u"組む", ms.R_BUILD_OUT, False))
        rec, log = run_one(ms, doc_r1(), d, u"7b", second_build_differs=True)
        want_eq(out_, u"2 回目の包みが違う", (rec[u"組めた"], rec[u"2 回組んで同じ"], rec[u"断った"]), (True, False, False))
        # 属性を作る命令が元と違う attrs を出せば、比べ方 1 が数える(出した folder の 1 つの name を替える)
        rec, log = run_one(ms, doc_r1(), d, u"8", alter_attrs=True)
        want_eq(out_, u"比べ方 1 が違いを数える", (rec[u"表 F が同じ"], rec[u"attrs が違う fact の数"], dict((k, v) for k, v in rec[u"attrs が違う属性ごとの fact の数(重ねて数える)"].items() if v), rec[u"組めた"]),
                (False, 1, {u"属性 name": 1}, True))
        # 紙の folder に元の attrs が在れば止まる(紙を作る側が元の attrs を残した場合)
        saved = ms.blank_row
        try:
            ms.blank_row = lambda e: od((k, (dict(v) if k == "attrs" else v)) for k, v in e.items())
            if not stops(ms, run_one, ms, doc_r1(), d, u"9"):
                out_.append(u"紙の folder に元の attrs が在るのに止まらない")
        finally:
            ms.blank_row = saved
        # 比べ方 1 の関数そのもの
        orig = ms.compare_attrs
        files = [(u"n", u"p", [od([("kind", "nonFraction"), ("attrs", {"name": "a", "unitRef": "J"})]), od([("kind", "nonNumeric"), ("attrs", {"x": "1"})])], None)]
        new = [(u"n", u"p", [od([("kind", "nonFraction"), ("attrs", {"name": "b", "unitRef": "K"})]), od([("kind", "nonNumeric"), ("attrs", {"x": "2"})])], None)]
        want_eq(out_, u"比べ方 1", (lambda r_: (r_[0], dict(r_[1])))(orig(files, new)), (1, {"name": 1, "unitRef": 1}))
        new2 = [(u"n", u"p", [od([("kind", "nonFraction"), ("attrs", {"unitRef": "J", "name": "a"})]), od([("kind", "nonNumeric"), ("attrs", {"x": "2"})])], None)]
        want_eq(out_, u"比べ方 1 は並びを見ない", (lambda r_: (r_[0], dict(r_[1])))(orig(files, new2)), (0, {}))
        new3 = [(u"n", u"p", [od([("kind", "nonFraction"), ("attrs", {"name": "a"})]), od([("kind", "nonNumeric"), ("attrs", {"x": "1"})])], None)]
        want_eq(out_, u"比べ方 1 は属性の有る無しを見る", (lambda r_: (r_[0], dict(r_[1])))(orig(files, new3)), (1, {"unitRef": 1}))
    return out_


def chunk_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        os.makedirs(os.path.join(d, "tmp"))
        plan = [(doc_r1(), {}), (doc_dupctx(), {}), (doc_missing(), {}), (doc_other(), {}), (doc_r1(), dict(second_build_differs=True)),
                (doc_r1(), dict(fail_attrs=(2, u"DECLINE: 紙の理由\n", False))), (doc_r1(), dict(alter_attrs=True))]
        recs = [run_one(ms, h, d, u"%d" % (i + 1), **kw)[0] for i, (h, kw) in enumerate(plan)]
        per = [od([(u"番号", i)] + list(r.items())) for i, r in enumerate(recs, 1)]
        tot = ms.group_totals(per)
        want_eq(out_, u"塊 書類・断り", (tot[u"書類の数"], tot[u"断った書類の数"], dict(tot[u"断った段ごとの数"]), dict(tot[u"断った理由ごとの数"])),
                (7, 2, {u"紙を作る": 1, u"属性を作る": 1, u"組む": 0}, {u"紙を作る: " + ms.A1.R_CTX_MISSING: 1, u"属性を作る: 紙の理由": 1}))
        want_eq(out_, u"塊 fact", (tot[u"紙を作れた書類の数"], tot[u"fact の数(紙を作れた書類)"], tot[u"1 つずつ書く fact の数"], tot[u"そのほかの属性を持つ fact の数"]), (6, 6 + 3 + 2 + 6 + 6 + 6, 2, 1))
        want_eq(out_, u"塊 理由", list(tot[u"1 つずつ書く fact の理由ごとの数(重ねて数える)"].values()), [0, 0, 2, 0])
        want_eq(out_, u"塊 比べ方 1", (tot[u"属性を作れた書類の数"], tot[u"表 F が同じ書類の数"], tot[u"attrs が違う fact の数"], tot[u"fact の数(属性を作れた書類)"]), (5, 4, 1, 6 + 3 + 2 + 6 + 6))
        want_eq(out_, u"塊 違う属性", dict((k, v) for k, v in tot[u"attrs が違う属性ごとの fact の数(重ねて数える)"].items() if v), {u"属性 name": 1})
        want_eq(out_, u"塊 組む", (tot[u"組めた書類の数"], tot[u"2 回組んで同じ書類の数"], tot[u"fact が同じ書類の数"], tot[u"鳴り方が同じ書類の数"], tot[u"タクソノミが同じ書類の数"], tot[u"全部同じ書類の数"]), (5, 4, 5, 5, 5, 5))
        want_eq(out_, u"塊 混ぜ物", (tot[u"混ぜ物を作れた書類の数"], tot[u"混ぜ物が効いた書類の数"]), (4, 4))
        facts = 6 + 3 + 2 + 6 + 6 + 6
        want_eq(out_, u"塊 紙の欄", (tot[u"紙の欄の数"], tot[u"fact の数 × 7"]), (sum(r[u"紙の欄の数"] for r in recs if r[u"紙の欄の数"] is not None), facts * 7))
        want_eq(out_, u"塊 紙の欄の比", (tot[u"紙の欄の比"][u"数"], tot[u"紙の欄の比"][u"分母"]), (tot[u"紙の欄の数"], facts * 7))
        want_eq(out_, u"塊 紙の欄の項", sum(tot[u"紙の欄の数(項ごと)"].values()), tot[u"紙の欄の数"])
        # 判定に要る数は本番の塊(2 本の後ろ)だけから
        rec = ms.assemble(per, u"c" * 64, FAKE_TOOL_INFO, 2)
        jk = [k for k in rec if k.startswith(u"予測の判定に要る数")]
        if len(jk) != 1:
            out_.append(u"判定に要る数の欄が 1 つでない")
        else:
            j = rec[jk[0]]
            want_eq(out_, u"判定 XS0-1", dict(j[u"XS0-1 表 F が同じ書類"]), {u"書類": 2, u"分母": 5})
            want_eq(out_, u"判定 XS0-2", dict(j[u"XS0-2 attrs が違う fact / fact(属性を作れた書類)"]), {u"数": 1, u"分母": 2 + 6 + 6, u"%": 7.1})
            want_eq(out_, u"判定 XS0-3", dict(j[u"XS0-3 1 つずつ書く fact / fact(紙を作れた書類)"]), {u"数": 0, u"分母": 2 + 6 + 6 + 6, u"%": 0.0})
            want_eq(out_, u"判定 XS0-4", dict(j[u"XS0-4 道具が読む fact が同じ書類"]), {u"書類": 3, u"分母": 5})
            want_eq(out_, u"判定 XS0-5", dict(j[u"XS0-5 属性を作る命令が断った書類"]), {u"書類": 1, u"分母": 5})
            want_eq(out_, u"判定 XS0-6", (j[u"XS0-6 紙の欄の数 / fact の数 × 7"][u"分母"], j[u"XS0-6 紙の欄の数 / fact の数 × 7"][u"数"]), (7 * (2 + 6 + 6 + 6), sum(r[u"紙の欄の数"] for r in recs[2:] if r[u"紙の欄の数"] is not None)))
            want_eq(out_, u"判定 XS0-7", dict(j[u"XS0-7 混ぜ物が効いた書類 / 作れた書類"]), {u"書類": 3, u"分母": 3})
            want_eq(out_, u"判定 XS0-8", (j[u"XS0-8 そのほかの属性を持つ fact / fact(紙を作れた書類)"][u"数"], j[u"XS0-8 そのほかの属性を持つ fact / fact(紙を作れた書類)"][u"分母"]), (1, 2 + 6 + 6 + 6))
        # 欠陥を疑う条件
        ch = copy.deepcopy(tot)
        want_eq(out_, u"疑い 開発の 5 本には 3071 を掛けない", u"1 つずつ書く fact が 3071 より少ない" in ms.suspicions(ch, whole=False), False)
        want_eq(out_, u"疑い 1 つずつ書く fact が少ない", u"1 つずつ書く fact が 3071 より少ない" in ms.suspicions(ch), True)
        ch[u"1 つずつ書く fact の数"] = 3070
        want_eq(out_, u"疑い 3070 は疑う", u"1 つずつ書く fact が 3071 より少ない" in ms.suspicions(ch), True)
        ch[u"1 つずつ書く fact の数"] = 3071
        want_eq(out_, u"疑い 3071 ちょうどは疑わない", u"1 つずつ書く fact が 3071 より少ない" in ms.suspicions(ch), False)
        ch[u"断った書類の数"] = 6
        want_eq(out_, u"疑い 断った書類 6 本", u"断った書類が 6 本以上" in ms.suspicions(ch), True)
        ch[u"断った書類の数"] = 5
        want_eq(out_, u"疑い 断った書類 5 本は疑わない", u"断った書類が 6 本以上" in ms.suspicions(ch), False)
        ch[u"断った段ごとの数"][u"属性を作る"] = 6
        want_eq(out_, u"疑い 属性を作る命令が 6 本断った", u"断った書類が 6 本以上" in ms.suspicions(ch), True)
        ch[u"断った段ごとの数"][u"属性を作る"] = 0
        ch[u"混ぜ物を作れた書類の数"] = ch[u"書類の数"] - 6
        want_eq(out_, u"疑い 混ぜ物を作れなかった書類 6 本", u"混ぜ物を作れなかった書類が 6 本以上" in ms.suspicions(ch), True)
        ch[u"混ぜ物を作れた書類の数"] = ch[u"書類の数"] - 5
        want_eq(out_, u"疑い 混ぜ物を作れなかった書類 5 本は疑わない", u"混ぜ物を作れなかった書類が 6 本以上" in ms.suspicions(ch), False)
        ch2 = copy.deepcopy(tot)
        ch2[u"表 F が同じ書類の数"], ch2[u"fact が同じ書類の数"] = 1, 2
        want_eq(out_, u"疑い 表 F が違うのに fact が同じ", any(u"表 F が違うのに" in s for s in ms.suspicions(ch2)), True)
    return out_


def record_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        docs = os.path.join(d, "docs")
        os.makedirs(docs)
        make_docs(docs, [doc_r1(), doc_missing(), doc_dupctx(), doc_other()])
        os.makedirs(os.path.join(d, "tmp"))
        calls = []
        ms.check_tool = lambda *a, **k: calls.append(1) or FAKE_TOOL_INFO
        proc = inproc(ms)
        rec, secret = ms.build_record(u"tool", docs, 4, fake_runner, None, os.path.join(d, "tmp"), dev_count=1, proc=proc)
        want_eq(out_, u"build_record は道具を確かめる", len(calls), 1)
        keys = list(rec)
        if keys[:5] != [u"seal", u"封の commit", u"step", u"この script の sha256", u"材料"] or keys[5:7] != [u"書類", u"集計"] or keys[-1] != u"限界":
            out_.append(u"記録の欄の並びが違う: %s" % keys)
        want_eq(out_, u"書類の数", len(rec[u"書類"]), 4)
        want_eq(out_, u"断った段", [r[u"断った段"] for r in rec[u"書類"]], [u"", u"紙を作る", u"", u""])
        want_eq(out_, u"script の sha256", rec[u"この script の sha256"], sha_of(SCRIPT_REL))
        want_eq(out_, u"材料", (rec[u"材料"][u"書類の本数"], rec[u"材料"][u"開発の 5 本の番号"], rec[u"材料"][u"script の決めの字"]), (4, [1], list(ms.RULES)))
        want_eq(out_, u"道具の欄", (rec[u"材料"][u"道具の版"], rec[u"材料"][u"規則の年"], rec[u"材料"][u"時間の上限(秒)"]), (u"2.47.5", ms.YEAR, ms.TIMEOUT_SEC))
        text = ms.dumps(rec)
        for t in (u"1,000", u"jppfs_cor", u"KA", u"KM", u".htm", u"E9999", u"S2FAKE", u"2025-03-31", u"2024-03-31", u"Mem1", u"SegAxis", u"ixt:", u"Dx1"):
            if t in text:
                out_.append(u"記録に禁止の字が在る: %s" % t)
        if not {u"SegAxis", u"Mem1", u"Dx1", u"Dx2"} <= set(secret[1]) or u"S2FAKE01" not in secret[2] or u"E99991" not in secret[3]:
            out_.append(u"secret に要素の名・文脈の名・member の名・docID・EDINET コードが入っていない")
        ms.verify_record(rec, text, 4, 1)
        mutate_cases = (
            (u"書類の数(塊)", lambda r: r[u"集計"][u"開発の 5 本"].__setitem__(u"書類の数", 2)),
            (u"書類の fact の数", lambda r: r[u"書類"][0].__setitem__(u"fact の数", 22)),
            (u"塊の fact の数", lambda r: r[u"集計"][u"開発の 5 本"].__setitem__(u"fact の数(紙を作れた書類)", 22)),
            (u"紙の欄の項", lambda r: r[u"書類"][0][u"紙の欄の数(項ごと)"].__setitem__(u"表ごとの 3", 9)),
            (u"紙の欄の合計", lambda r: r[u"書類"][0].__setitem__(u"紙の欄の数", 21)),
            (u"1 つずつ書く fact × 7", lambda r: r[u"書類"][2][u"紙の欄の数(項ごと)"].__setitem__(u"1 つずつ書く fact × 7", 8)),
            (u"1 つずつ書く fact の数", lambda r: r[u"書類"][0].__setitem__(u"1 つずつ書く fact の数", 99)),
            (u"全部同じ", lambda r: r[u"書類"][0].__setitem__(u"全部同じ", False)),
            (u"表 F が同じ", lambda r: r[u"書類"][0].__setitem__(u"表 F が同じ", False)),
            (u"番号", lambda r: r[u"書類"][2].__setitem__(u"番号", 9)),
            (u"断った理由", lambda r: r[u"書類"][1].__setitem__(u"断った理由", u"")),
            (u"断った段", lambda r: r[u"書類"][1].__setitem__(u"断った段", u"道具")),
            (u"断った書類の組めた", lambda r: r[u"書類"][1].__setitem__(u"組めた", True)),
            (u"混ぜ物の形", lambda r: r[u"書類"][1][u"混ぜ物"].__setitem__(u"効いた", True)),
            (u"属性の欄", lambda r: r[u"書類"][0][u"attrs が違う属性ごとの fact の数(重ねて数える)"].pop(u"属性 name")),
            (u"集計の合計", lambda r: r[u"集計"][u"全部"].__setitem__(u"表 F が同じ書類の数", 1)),
            (u"判定に要る数", lambda r: r[[k for k in r if k.startswith(u"予測の判定に要る数")][0]][u"XS0-1 表 F が同じ書類"].__setitem__(u"書類", 0)))
        bad = []
        for what, fn in mutate_cases:
            r2 = copy.deepcopy(rec)
            fn(r2)
            if not stops(ms, ms.verify_record, r2, None, 4, 1):
                bad.append(what)
        if bad:
            out_.append(u"verify_record が止めない: %s" % bad)
        if not stops(ms, ms.verify_record, rec, text, 67, 1):
            out_.append(u"書類が 67 本でないのに verify_record が止めない")
        rp = os.path.join(d, "rec", "r.json")
        if not stops(ms, ms.run, u"tool", docs=docs, out=rp, want=67, say=lambda *a: None, runner=fake_runner, proc=proc) or os.path.exists(rp):
            out_.append(u"67 本でないのに run が止まらない(か記録を書いた)")
        lines = []
        rec2 = ms.run(u"tool", docs=docs, out=rp, want=4, say=lambda *a: None, runner=fake_runner, tmp_root=os.path.join(d, "tmp"), dev_count=1, proc=proc, progress=lines.append)
        if not os.path.exists(rp) or ms.dumps(rec2)[:0] != u"" or len(lines) != 4:
            out_.append(u"記録が書かれていない・進みを出さない")
        want_eq(out_, u"書いた記録の検査", read_text(rp).count(u"\n") > 10, True)
        ms.check(rec_path=rp, say=lambda *a: None, want=4, dev_count=1)
        if not stops(ms, ms.run, u"tool", docs=docs, out=rp, want=4, say=lambda *a: None, runner=fake_runner, dev_count=1, proc=proc):
            out_.append(u"記録が既に在るのに run が止まらない")
        rp3 = os.path.join(d, "rec", "r3.json")
        with io.open(rp3, "w", encoding="utf-8") as fh:
            fh.write(read_text(rp).replace(u'"属性を作れた": true', u'"属性を作れた": false', 1))
        if not stops(ms, ms.check, rec_path=rp3, say=lambda *a: None, want=4, dev_count=1):
            out_.append(u"記録を書き換えたのに check が止まらない")
        if not stops(ms, ms.check, rec_path=os.path.join(d, "none.json"), say=lambda *a: None, want=4):
            out_.append(u"記録が無いのに check が止まらない")
        # 開発の入口は 5 本だけ(記録は書かない)
        docs2 = os.path.join(d, "docs2")
        os.makedirs(docs2)
        make_docs(docs2, [doc_r1()] * 7)
        out_lines = []
        before_calls = len(calls)
        per = ms.dev_run(u"tool", docs_dir=docs2, runner=fake_runner, tmp_root=os.path.join(d, "tmp"), say=out_lines.append, proc=proc)
        want_eq(out_, u"開発の入口は 5 本だけ", (len(per), sum(1 for x in out_lines if x.startswith(u"doc "))), (5, 5))
        want_eq(out_, u"dev_run は道具を確かめる", len(calls) - before_calls, 1)
        if not any(u"先に自分の欠陥を疑う場合に当たったもの" in x for x in out_lines):
            out_.append(u"欠陥を疑う場合の行を出さない")
        want_eq(out_, u"dev_docs の本数", len(ms.dev_docs(docs2, 2)), 2)
    return out_


def clean_problems(ms=None):
    ms = ms or MS
    out_ = []
    ok = od([(u"書類", [od([(u"番号", 1), (u"断った理由", u"固定の理由"), (u"fact の数", 5)])]), (u"hash", u"a" * 64)])
    secret = (set(), {u"NetSalesOfX", u"CurrentYearInstant", u"MemberY"}, [u"zzdoc"], {u"E99991"})
    if stops(ms, ms.check_clean, ok, ms.dumps(ok), secret):
        out_.append(u"きれいな記録で止まる")
    cases = [
        (u"禁止の欄(docid)", od([(u"DocID", 1)])), (u"禁止の欄(company)", od([(u"company", 1)])), (u"禁止の欄(element)", od([(u"element", 1)])), (u"禁止の欄(name)", od([(u"name", 1)])),
        (u"EDINET コードの形", od([(u"x", u"id E12345 x")])), (u"docID の形", od([(u"x", u"S100ABCD")])), (u"材料の docID", od([(u"x", u"id zzdoc.")])), (u"材料の EDINET コード", od([(u"x", u"E99991")])),
        (u"要素の名", od([(u"x", u"理由 NetSalesOfX")])), (u"文脈の名", od([(u"x", u"CurrentYearInstant")])), (u"member の名", od([(u"x", u"MemberY を含む")])),
        (u"日付の形", od([(u"x", u"終わりは 2025-03-31")])), (u"file の名(htm)", od([(u"x", u"0101010_honbun.htm")])), (u"file の名(xsd)", od([(u"x", u"jpcrp030000-asr-001.xsd")]))]
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


# ======================================================================== 6. 配線
STDLIB_OK = ("__future__", "argparse", "collections", "importlib", "io", "json", "os", "re", "shutil", "sys", "tempfile", "time")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "adapters", "core", "audit_core", "zipfile", "csv", "xml", "subprocess")
#: 前の便の script の関数を呼ぶ(写さない): (module の名, 関数の名)
CALLED = (("X", "doc_texts"), ("X", "facts_of_files"), ("X", "place_positions"), ("X", "mode_first"), ("X", "line_keys"), ("X", "reads_negative"), ("X", "format_class"), ("X", "strip_tags"),
          ("X", "check_clean"), ("A1", "context_defs"), ("A1", "resolve_facts"), ("A1", "choose_combo"), ("A1", "sign_format_flags"), ("A1", "end_of"), ("A1", "members_of"),
          ("A1", "secret_strings"), ("W", "select_docs"), ("W", "order_sha256"), ("P", "peel_tables"), ("P", "write_folder"), ("P", "load_htm_tables"), ("P", "exec_build"),
          ("P", "read_tree"), ("P", "expected_names"), ("P", "rebuilt_pack"), ("P", "check_tool"), ("T", "run_package"), ("T", "compare_into"), ("B", "load_package"), ("B", "write_package"), ("B", "dev_docs"))
NOT_COPIED = ("select_docs", "order_sha256", "strip_text", "load_package", "is_public_htm", "mismatches", "count_facts", "mode_first", "lines_of", "line_keys", "doc_texts", "facts_of_files",
              "reads_negative", "format_class", "strip_tags", "place_positions", "pct1", "sha256_file", "sha256_bytes", "facts_of_text", "table_tokens", "context_defs", "contexts_of_text",
              "resolve_facts", "choose_combo", "sign_format_flags", "peel_tables", "write_folder", "load_htm_tables", "exec_build", "read_tree", "expected_names", "rebuilt_pack", "run_package",
              "compare_into", "run_process", "decline_reason", "jdump", "jload", "build_text", "build_main", "render_folder")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
#: 別の門の規準の字(関数の名・呼び出し・説明文のどこにも使わない)
HARNESS_WORDS = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(", "tampered", u"注入")
OTHER_NAMES = (u"_xb0_inline_build_2026_11_21", u"_xt0_inline_build_2026_11_21", u"_xp0_taxonomy_build_2026_11_22", u"_xt0_taxonomy_build_2026_11_22", u"_xv0_tag_wall_2026_11_21", u"_xg1_tag_wall_2026_11_21",
               u"_xb0_tag_wall_2026_11_21", u"_xb0_tag_narrow", u"_xb0_edinet_validate_2026_11_21", u"_xa0_inline_build_2026_11_22", u"_xa1_sheet_wall_2026_11_22")


def attr_names(tree):
    return [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]


def import_problems(src=None):
    u"""script の import は標準ライブラリだけ(engine・zipfile・csv・subprocess を読まない)。前の便の script は X・A1・P・T・B・W から呼び、写さない。"""
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
    for want in (u"_xs0_sheet_context_2026_11_22", u"_xs0_pack_build_2026_11_22"):
        if want not in consts:
            out_.append(u"前の便の script を読む名が一意の名でない: %s" % want)
    if any(n in consts for n in OTHER_NAMES):
        out_.append(u"他の便と重なる名で読んでいる")
    for var, want in (("A1", ("_load_sibling", None)), ("P", ("_load_sibling", None)), ("X", ("A1", "X")), ("B", ("X", "B")), ("T", ("P", "T")), ("W", ("A1", "W"))):
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
            if u".env" in n.value or u"dotenv" in n.value or u"API_KEY" in n.value or u"/private/tmp" in n.value or u"scratchpad" in n.value:
                out_.append(u"鍵・.env・scratchpad の path の字が在る")
    if u"/private/tmp" in src or u"scratchpad" in src:
        out_.append(u"scratchpad の path の字が script の中に在る")
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


def called_same_problems(ms=None):
    u"""この便の script が呼ぶ前の便の関数は、前の便の script の関数そのもの(写していない)。"""
    ms = ms or MS
    out_ = []
    for mod, fn in CALLED:
        if not callable(getattr(getattr(ms, mod, None), fn, None)):
            out_.append(u"前の便の %s.%s が無い" % (mod, fn))
    if ms.Stop is not ms.X.Stop or ms.Stop is not ms.P.Stop or ms.Refuse is not ms.X.Refuse or ms.W is not ms.X.W or ms.W is not ms.P.W:
        out_.append(u"Stop・Refuse・W が前の便と同じ object でない")
    return out_


# ======================================================================== 変異
#: (名前, 置き換え前(script の中でちょうど 1 回)・置き換え後・赤になるべき検査の名前)。**予測は「その検査が赤になる」。** この表は実行より先に書いた。
#: 検査の名前: seal・rules・paper・blind・behaviour・measure・chunk・record・clean・wiring・called
MUTANTS = (
    # ---- 紙を作る(1 つずつ書く fact の決め・紙の決め)
    (u"S1 (a) 表の外を 1 つずつ書く fact にしない", u"        h = ra or rb or rc or rd", u"        h = rb or rc or rd", ("rules", "measure")),
    (u"S2 (b) 全部決まらない fact を 1 つずつ書く fact にしない", u"        h = ra or rb or rc or rd", u"        h = ra or rc or rd", ("rules",)),
    (u"S3 (c) 文脈の定義の重なりを見ない", u"        h = ra or rb or rc or rd", u"        h = ra or rb or rd", ("rules", "measure", "chunk")),
    (u"S4 (d) 期間の種類の違いを見ない", u"        h = ra or rb or rc or rd", u"        h = ra or rb or rc", ("rules",)),
    (u"S5 (c) の閾値を 3 つ以上にする", u"        rc = triple_ids[(c[0], c[2], c[3])] >= 2", u"        rc = triple_ids[(c[0], c[2], c[3])] >= 3", ("rules", "measure", "chunk")),
    (u"S6 (c) の組に終わりの日でなく始まりの日を使う", u"        rc = triple_ids[(c[0], c[2], c[3])] >= 2", u"        rc = triple_ids[(c[0], c[1], c[3])] >= 2", ("rules",)),
    (u"S7 (c) の組に member を使わない", u"        rc = triple_ids[(c[0], c[2], c[3])] >= 2", u"        rc = triple_ids[(c[0], c[2], ())] >= 2", ("rules",)),
    (u"S8 triple を数える側に member を入れない", u"        triple_ids[(content[0], content[2], content[3])] += 1", u"        triple_ids[(content[0], content[2], ())] += 1", ("rules",)),
    (u"S9 (d) で name の決めを見ない(いつも違うと読む)", u"        rd = kinds.get(f[\"attrs\"].get(\"name\")) != c[0]", u"        rd = True", ("rules", "measure", "chunk")),
    (u"S10 期間の種類の決めを最頻でなく最後にする", u"    kinds = od((nm, X.mode_first(ks)) for nm, ks in by_name.items())", u"    kinds = od((nm, ks[-1]) for nm, ks in by_name.items())", ("rules",)),
    (u"S11 書式の決めを最頻でなく最初の fact にする", u"            fmt[k] = mode_val(vals)", u"            fmt[k] = vals[0]", ("rules",)),
    (u"S12 書式の決めに空の fact も入れる", u"    live = [f for f in facts if not f[\"nil\"]]\n    fmt = od()", u"    live = list(facts)\n    fmt = od()", ("rules",)),
    (u"S13 空の fact の印を付けない", u"        if f[\"nil\"]:\n            row[\"nil\"] = True", u"        if False:\n            row[\"nil\"] = True", ("rules", "measure")),
    (u"S14 そのほかの属性を書かない", u"        if other:\n            row[\"other\"] = other", u"        if False:\n            row[\"other\"] = other", ("rules", "measure", "chunk")),
    (u"S15 そのほかの属性に sign も入れる", u"if k not in ATTRS and k != NIL_ATTR)", u"if k != NIL_ATTR)", ("rules", "chunk")),
    (u"S16 1 つずつ書く fact の値を 7 つでなく name だけにする", u"            row[\"values\"] = [f[\"attrs\"].get(k) for k in ATTRS]", u"            row[\"values\"] = [f[\"attrs\"].get(k) for k in ATTRS[:1]] + [None] * 6", ("rules", "measure")),
    (u"S17 要素の線の決めに空の fact の decimals も入れる", u"        elements[str(e)] = [mode_val([x.get(\"name\") for x in a]), mode_val([x.get(\"unitRef\") for x in a]),\n                            mode_val([x.get(\"decimals\") for x in live]), mode_val([x.get(\"scale\") for x in live])]",
     u"        elements[str(e)] = [mode_val([x.get(\"name\") for x in a]), mode_val([x.get(\"unitRef\") for x in a]),\n                            mode_val([x.get(\"decimals\") for x in a]), mode_val([x.get(\"scale\") for x in live])]", ("rules",)),
    (u"S18 要素の線の決めの unitRef に空の fact を入れない", u"mode_val([x.get(\"unitRef\") for x in a]),\n", u"mode_val([x.get(\"unitRef\") for x in live]),\n", ("rules",)),
    (u"S19 終わりの日の線を選んだ側でなく文脈の線に固定する", u"            by.setdefault(c if src == \"C\" else e, []).append(i)", u"            by.setdefault(c, []).append(i)", ("rules", "paper")),
    (u"S20 選びの名を紙に書かない(いつも ACC)", u"    return od([(\"orient\", orient), (\"end_src\", es), (\"member_src\", ms),", u"    return od([(\"orient\", \"A\"), (\"end_src\", \"C\"), (\"member_src\", \"C\"),", ("rules", "paper")),
    (u"S21 紙の欄の数に持ち込みを足す(表の線の 4 を 5 にする)", u"CELLS_PER_ELEMENT_LINE = 4", u"CELLS_PER_ELEMENT_LINE = 5", ("seal", "rules")),
    (u"S22 紙の欄の数の表ごとの 3 を 2 にする", u"CELLS_PER_TABLE = 3 ", u"CELLS_PER_TABLE = 2 ", ("seal", "rules")),
    (u"S23 紙の欄の数で member の線を数えない", u"    out[u\"member の組を決める側の線 × 1\"] = sum(len(t[\"members\"]) for t in tables)", u"    out[u\"member の組を決める側の線 × 1\"] = 0", ("rules", "paper")),
    (u"S24 紙の欄の数で name の期間の種類を数えない", u"    out[u\"name ごとの期間の種類\"] = len(sheet[\"kinds\"])", u"    out[u\"name ごとの期間の種類\"] = 0", ("rules", "paper")),
    (u"S25 紙の欄の数で書式の類を数えない", u"    out[u\"書式の類の決め\"] = len(sheet[\"format\"])", u"    out[u\"書式の類の決め\"] = 0", ("rules", "paper")),
    (u"S26 1 つずつ書く fact の欄を 7 でなく 6 で数える", u"CELLS_PER_HAND_FACT = 7", u"CELLS_PER_HAND_FACT = 6", ("seal", "rules")),
    (u"S27 紙の folder に元の attrs を残す", u"    return od((k, ({} if (k == \"attrs\" and e[\"kind\"] == \"nonFraction\") else (dict(v) if k == \"attrs\" else v))) for k, v in e.items())", u"    return od((k, (dict(v) if k == \"attrs\" else v)) for k, v in e.items())", ("paper", "measure")),
    (u"S28 紙に非 1 つずつの fact の contextRef を書く", u"        if h:\n            row[\"values\"] = [f[\"attrs\"].get(k) for k in ATTRS]", u"        if h or f[\"attrs\"].get(\"contextRef\") == \"KA\":\n            row[\"values\"] = [f[\"attrs\"].get(k) for k in ATTRS]", ("rules", "paper")),
    # ---- 属性を作る(答えを読まない側)
    (u"A1 sign を付けない", u"    if X.reads_negative(f[\"between\"]):\n        attrs[\"sign\"] = \"-\"", u"    if False:\n        attrs[\"sign\"] = \"-\"", ("rules",)),
    (u"A2 sign をいつも付ける", u"    if X.reads_negative(f[\"between\"]):\n        attrs[\"sign\"] = \"-\"", u"    if True:\n        attrs[\"sign\"] = \"-\"", ("rules",)),
    (u"A3 format を付けない", u"    fm = sheet[\"format\"].get(X.format_class(f[\"text\"]))\n    if fm is not None:", u"    fm = None\n    if fm is not None:", ("rules", "paper")),
    (u"A4 format の類を決めず最初の類の決めを使う", u"    fm = sheet[\"format\"].get(X.format_class(f[\"text\"]))", u"    fm = sheet[\"format\"].get(\"2\")", ("rules",)),
    (u"A5 空の fact に decimals を付ける", u"    if row.get(\"nil\"):\n        attrs[NIL_ATTR] = \"true\"\n        return attrs", u"    if row.get(\"nil\"):\n        attrs[NIL_ATTR] = \"true\"\n        if dec is not None:\n            attrs[\"decimals\"] = dec\n        return attrs", ("rules",)),
    (u"A6 空の fact の印を読まない", u"    if row.get(\"nil\"):\n        attrs[NIL_ATTR] = \"true\"\n        return attrs", u"    if False:\n        attrs[NIL_ATTR] = \"true\"\n        return attrs", ("rules", "paper")),
    (u"A7 「無い」decimals を空の字で付ける", u"    if dec is not None:\n        attrs[\"decimals\"] = dec", u"    attrs[\"decimals\"] = dec or \"\"", ("rules",)),
    (u"A8 「無い」scale を空の字で付ける", u"    if scale is not None:\n        attrs[\"scale\"] = scale", u"    attrs[\"scale\"] = scale or \"\"", ("rules",)),
    (u"A9 「無い」unitRef を空の字で付ける", u"    if unit is not None:\n        attrs[\"unitRef\"] = unit", u"    attrs[\"unitRef\"] = unit or \"\"", ("rules",)),
    (u"A10 文脈が 1 つに決まらなくても先の id を使う", u"    if len(ids) != 1:\n        raise Refuse(R_CTX_AMBIG)", u"    if len(ids) < 1:\n        raise Refuse(R_CTX_AMBIG)", "paper",),
    (u"A11 文脈の期間の種類を name から決めず時点にする", u"    kind = sheet[\"kinds\"].get(name)\n    end", u"    kind = \"I\"\n    end", ("paper",)),
    (u"A12 終わりの日を選んだ側でなく文脈の線に固定する", u"    end = t[\"ends\"].get(str(c if t[\"end_src\"] == \"C\" else e), u\"\\x00無い\")", u"    end = t[\"ends\"].get(str(c), u\"\\x00無い\")", ("paper",)),
    (u"A13 member の組を選んだ側でなく文脈の線に固定する", u"    mem = t[\"members\"].get(str(c if t[\"member_src\"] == \"C\" else e), u\"\\x00無い\")", u"    mem = t[\"members\"].get(str(c), u\"\\x00無い\")", ("paper",)),
    (u"A14 member の組を見ない", u"    ids = ctx_idx.get((kind, end, jtuple(mem)), [])", u"    ids = [i for k, v in ctx_idx.items() if k[:2] == (kind, end) for i in v]", ("rules", "paper")),
    (u"A15 終わりの日を見ない", u"    ids = ctx_idx.get((kind, end, jtuple(mem)), [])", u"    ids = [i for k, v in ctx_idx.items() if (k[0], k[2]) == (kind, jtuple(mem)) for i in v]", ("rules", "paper")),
    (u"A16 期間の種類を見ない", u"    ids = ctx_idx.get((kind, end, jtuple(mem)), [])", u"    ids = [i for k, v in ctx_idx.items() if k[1:] == (end, jtuple(mem)) for i in v]", ("rules", "paper")),
    (u"A17 文脈の定義の終わりの日の空白を落とさない", u"        kind, end = A1.KIND_INSTANT, per[0][1].strip()", u"        kind, end = A1.KIND_INSTANT, per[0][1]", ("rules",)),
    (u"A18 文脈の期間の種類を取り違える(期間を時点に読む)", u"        kind, end = A1.KIND_DURATION, per[1][1].strip()", u"        kind, end = A1.KIND_INSTANT, per[1][1].strip()", ("rules",)),
    (u"A19 member の組を並べない", u"    members = tuple(sorted((d or u\"\", m.strip()) for d, m in r[\"members\"]))", u"    members = tuple((d or u\"\", m.strip()) for d, m in r[\"members\"])", ("rules",)),
    (u"A20 同じ id で中身が違っても断らない", u"            if cid in defs and defs[cid] != content:\n                raise Refuse(A1.R_CTX_DUP)", u"            if False:\n                raise Refuse(A1.R_CTX_DUP)", "paper",),
    (u"A21 そのほかの属性を付けない", u"            for k, v in row.get(\"other\", {}).items():\n                attrs[k] = v", u"            for k, v in {}.items():\n                attrs[k] = v", ("rules", "paper")),
    (u"A22 1 つずつ書く fact の値を読まない(決めで作る)", u"            if \"values\" in row:", u"            if False:", ("rules", "paper")),
    (u"A23 向きを見ない(いつも向き A)", u"    orient = t[\"orient\"]\n    e, c = X.line_keys(f, orient)", u"    orient = \"A\"\n    e, c = X.line_keys(f, orient)", ("paper",)),
    (u"A24 cell の位置を file をまたいで数えない(表の番号を file の中だけで引く)", u"                t = tabs.get((fi, cell[0]))", u"                t = tabs.get((0, cell[0]))", "rules",),
    (u"A25 負の字を cell の開きタグの終わりからでなく fact の中から見る", u"(\"between\", X.strip_tags(plain[cell[3]:e[\"start\"]]))", u"(\"between\", X.strip_tags(plain[e[\"start\"]:e[\"end\"]]))", ("rules",)),
    (u"A26 属性を作る命令が元の包みを読める(zip_path を受ける)", u"def attrs_tables(folder):", u"def attrs_tables(folder, zip_path=None):", ("blind",)),
    (u"A27 属性を作る命令が元の fact を読む関数を呼ぶ", u"    ctx_idx = context_index(files)\n    tabs = table_lookup(sheet)", u"    B.load_package(folder)\n    ctx_idx = context_index(files)\n    tabs = table_lookup(sheet)", ("blind",)),
    (u"A28 属性を作る命令の引数の数を見ない", u"    if len(args) != 2:\n        print(u\"使い方: attrs", u"    if len(args) < 1:\n        print(u\"使い方: attrs", ("behaviour", "blind")),
    (u"A29 属性を作る命令を -I なしで呼ぶ", u"    return [sys.executable, \"-I\", SCRIPT_PATH, \"attrs\", folder, out]", u"    return [sys.executable, SCRIPT_PATH, \"attrs\", folder, out]", ("behaviour", "blind")),
    (u"A30 属性を作る命令の断りを 1 にする", u"        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)\n        return EXIT_DECLINE\n    except Exception:                                      # noqa: BLE001\n        print(u\"ERROR\", file=sys.stderr)\n        return EXIT_ERROR\n    return 0\n\n\ndef attrs_command", u"        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)\n        return EXIT_ERROR\n    except Exception:                                      # noqa: BLE001\n        print(u\"ERROR\", file=sys.stderr)\n        return EXIT_ERROR\n    return 0\n\n\ndef attrs_command", ("behaviour",)),
    # ---- 比べ方・混ぜ物
    (u"C1 比べ方 1 が違う属性を数えない", u"            if a != b:\n                diff += 1", u"            if False:\n                diff += 1", ("measure", "chunk")),
    (u"C2 比べ方 1 が属性の値を見ない(名だけ)", u"            a, b = e[\"attrs\"], e2[\"attrs\"]\n            if a != b:", u"            a, b = e[\"attrs\"], e2[\"attrs\"]\n            if set(a) != set(b):", ("measure",)),
    (u"C3 比べ方 1 が並びを見る", u"            if a != b:\n                diff += 1", u"            if list(a.items()) != list(b.items()):\n                diff += 1", ("measure",)),
    (u"C4 混ぜ物の当て先に 1 つずつ書く fact も数える", u"        free = [i for i in info[\"lines\"][key] if not hand[i]]\n        if len(free) >= 2:", u"        free = [i for i in info[\"lines\"][key]]\n        if len(free) >= 2:", ("rules",)),
    (u"C5 混ぜ物の当て先の閾値を 1 つにする", u"        if len(free) >= 2:\n            return key[0]", u"        if len(free) >= 1:\n            return key[0]", ("rules",)),
    (u"C6 混ぜ物の当て先を最後の線にする", u"    for key in sorted(info[\"lines\"]):\n        free", u"    for key in sorted(info[\"lines\"], reverse=True):\n        free", ("rules",)),
    (u"C7 混ぜ物で name を替えない", u"            t[\"elements\"][str(line)][0] = MIX_NAME", u"            t[\"elements\"][str(line)][0] = old", ("rules", "paper", "measure")),
    (u"C8 混ぜ物で期間の種類を足さない", u"            if old is not None and old in out[\"kinds\"]:\n                out[\"kinds\"][MIX_NAME] = out[\"kinds\"][old]", u"            pass", ("rules", "paper", "measure")),
    (u"C9 混ぜ物がほかの fact の変化を見ない", u"            elif e[\"attrs\"] != e2[\"attrs\"]:\n                return True, False", u"            elif False:\n                return True, False", ("rules",)),
    (u"C10 混ぜ物が替えた name を確かめない", u"                if e2[\"attrs\"] != want:\n                    return True, False\n                changed += 1", u"                changed += 1", ("rules",)),
    (u"C11 混ぜ物の効いたを常に真にする", u"    return True, changed == len(free)", u"    return True, True", ("rules",)),
    (u"C12 混ぜ物を作れなかった書類も作れたに数える", u"    if target is None:\n        return False, False", u"    if target is None:\n        return True, False", ("rules",)),
    # ---- 通し・断り・数え方
    (u"M1 断りの段を取り違える(属性を作る → 組む)", u"            return declined_rec(rec, STAGES[1], reason)", u"            return declined_rec(rec, STAGES[2], reason)", ("measure", "chunk")),
    (u"M2 属性を作る命令の断りの理由を捨てる", u"        reason = P.decline_reason(err)\n        return False, (reason if reason is not None else u\"属性を作る命令が 0 でない終わりの値で終わった\"), secs", u"        return False, u\"属性を作る命令が 0 でない終わりの値で終わった\", secs", ("behaviour", "measure")),
    (u"M3 属性を作る命令の時間の上限を見ない", u"    if timed_out:\n        return False, u\"属性を作る命令が時間の上限を超えた\", secs", u"    if False:\n        return False, u\"属性を作る命令が時間の上限を超えた\", secs", ("behaviour",)),
    (u"M4 組む命令の出力の file の名を見ない", u"        if set(tree) != P.expected_names(out_index):", u"        if False:", ("measure",)),
    (u"M5 2 回組んで同じを見ない(いつも真)", u"        rec[u\"2 回組んで同じ\"] = bool(ok2 and P.read_tree(bout2) == tree)", u"        rec[u\"2 回組んで同じ\"] = True", ("measure", "chunk")),
    (u"M6 組み直しの包みでなく元の包みを道具に掛ける", u"        B.write_package(P.rebuilt_pack(entries, tree), new_zip)", u"        B.write_package(entries, new_zip)", ("measure",)),
    (u"M7 組む命令に元の表 F の folder を渡す(属性を作った folder でなく紙の folder)", u"        ok, reason, secs = P.exec_build(out1, bout1, cwd, proc)", u"        ok, reason, secs = P.exec_build(folder, bout1, cwd, proc)", ("measure", "chunk")),
    (u"M8 紙の欄の数を紙の file でなく手元の紙で数える(読み戻さない)は同じ値なので、読み戻した紙の欄を 0 にする", u"        rec[u\"紙の欄の数\"] = sum(cells.values())", u"        rec[u\"紙の欄の数\"] = 0", ("measure", "chunk")),
    (u"M9 全部同じを fact が同じだけで決める", u"        for k in (u\"タクソノミが同じ\", u\"fact が同じ\", u\"鳴り方が同じ\", u\"全部同じ\"):\n            rec[k] = bool(cmp[k])", u"        for k in (u\"タクソノミが同じ\", u\"fact が同じ\", u\"鳴り方が同じ\"):\n            rec[k] = bool(cmp[k])\n        rec[u\"全部同じ\"] = rec[u\"fact が同じ\"]", "measure",),
    (u"M10 表 F が同じを違う fact の数に依らず真にする", u"        rec[u\"表 F が同じ\"] = diff == 0", u"        rec[u\"表 F が同じ\"] = True", ("measure", "chunk")),
    (u"M11 紙の folder に元の attrs が在っても止めない", u"        if leak_problems(folder):", u"        if False:", ("measure",)),
    (u"M12 道具の確かめを掛けない(build_record)", u"    info = check_tool(tool_p, runner, sha_reader, want_version, want_sha)\n    per_doc = []", u"    info = od([(u\"版\", u\"x\"), (u\"ModelValue.py の sha256\", u\"x\"), (u\"package の一覧の sha256\", u\"x\"), (u\"Python の版\", u\"x\")])\n    per_doc = []", ("record",)),
    (u"G1 判定の XS0-1 の分母を 62 でなく断らなかった書類にする", u"        (u\"XS0-1 表 F が同じ書類\", od([(u\"書類\", prod[u\"表 F が同じ書類の数\"]), (u\"分母\", prod[u\"書類の数\"])])),", u"        (u\"XS0-1 表 F が同じ書類\", od([(u\"書類\", prod[u\"表 F が同じ書類の数\"]), (u\"分母\", prod[u\"属性を作れた書類の数\"])])),", "chunk",),
    (u"G2 判定の XS0-5 を組む段の断りで数える", u"prod[u\"断った段ごとの数\"][STAGES[1]]", u"prod[u\"断った段ごとの数\"][STAGES[2]]", "chunk",),
    (u"G3 判定の XS0-7 の分母を書類の数にする", u"(u\"分母\", prod[u\"混ぜ物を作れた書類の数\"])", u"(u\"分母\", prod[u\"書類の数\"])", "chunk",),
    (u"G4 判定に要る数を 5 本も入れた全部の塊から作る", u"    prod = tot[[k for k in tot if k.startswith(u\"本番だけの\")][0]]", u"    prod = tot[u\"全部\"]", "chunk",),
    (u"G5 断った書類を紙を作れた書類に数える", u"    made = [e for e in entries if e[u\"fact の数\"] is not None]", u"    made = [e for e in entries]", ("chunk",)),
    (u"G6 疑いの 3071 を 3000 にする", u"SUSPECT_HAND_BELOW = 3071", u"SUSPECT_HAND_BELOW = 3000", ("chunk",)),
    (u"G7 疑いの断った書類の数を 7 にする", u"SUSPECT_DECLINED = 6", u"SUSPECT_DECLINED = 7", ("seal", "chunk")),
    (u"G8 予測の境(XS0-3 の上限)を変える", u"(\"XS0-3\", (4.8, 6.5))", u"(\"XS0-3\", (4.8, 6.6))", ("seal",)),
    (u"G9 予測の境(XS0-6 の下限)を変える", u"(\"XS0-6\", (33.6, 38))", u"(\"XS0-6\", (33.0, 38))", ("seal",)),
    (u"G10 予測の境(XS0-1)を変える", u"(\"XS0-1\", (60, None))", u"(\"XS0-1\", (59, None))", ("seal",)),
    (u"G11 封の commit を変える", u"SEAL_COMMIT = \"483e3e93\"", u"SEAL_COMMIT = \"483e3e94\"", ("seal",)),
    (u"G12 記録の path を変える", u"RECORD_REL = \"fixtures/xbrl/cd8/sheet_build_2026-11-22.json\"", u"RECORD_REL = \"fixtures/xbrl/cd8/sheet_build_2026-11-23.json\"", ("seal",)),
    (u"G13 混ぜ物の name の字を変える", u"MIX_NAME = \"xs0:Changed\"", u"MIX_NAME = \"xs0:Other\"", ("seal",)),
    (u"G14 断りの段を変える", u"STAGES = (u\"紙を作る\", u\"属性を作る\", u\"組む\")", u"STAGES = (u\"紙を作る\", u\"属性を作る\", u\"道具\")", ("seal",)),
    (u"G15 開発の本数を変える", u"DEV_COUNT = 5\n\n# ---- 封 §1", u"DEV_COUNT = 6\n\n# ---- 封 §1", ("seal",)),
    (u"G16 限界の字を消す", u"    u\"1 つずつ書く fact は 7 つの値を元から写すので、その fact が元と同じになるのは当たり前。\",\n", u"", ("seal",)),
    (u"G17 7 つの値の並びを変える", u"ATTRS = (\"name\", \"contextRef\", \"unitRef\", \"decimals\", \"scale\", \"sign\", \"format\")", u"ATTRS = (\"name\", \"contextRef\", \"unitRef\", \"decimals\", \"scale\", \"format\", \"sign\")", "seal",),
    (u"G18 記録に紙の中身の字(要素の名)を書く", u"        (u\"書類の本数\", len(per_doc)), (u\"書類の file 名の並びの sha256\", order_sha),", u"        (u\"書類の本数\", len(per_doc)), (u\"書類の file 名の並びの sha256\", order_sha), (u\"例\", u\"jppfs_cor:E0\"),", ("record",)),
    (u"G19 記録の日付の検査を外す", u"    if A1.DATE_FORM_RE.search(W.HEX_RE.sub(u\"\", text)):\n        raise Stop(u\"**記録に日付の形の字が在る。止める**\")", u"    pass", ("clean",)),
    (u"G20 secret の要素の名を渡さない", u"    secret = (set(), set(e for e in names if len(e) >= 3), [d[0] for d in docs], ecodes)\n    return assemble(per_doc,", u"    secret = (set(), set(), [d[0] for d in docs], ecodes)\n    return assemble(per_doc,", ("record",)),
    # ---- 監査 REVISE の直し(予測は実行より先に書いた)
    (u"S29 そのほかの属性を属性の数でなく持つ fact の数で数える", u"    out[u\"そのほかの属性\"] = sum(len(f[\"other\"]) for f in facts if \"other\" in f)", u"    out[u\"そのほかの属性\"] = sum(1 for f in facts if \"other\" in f)", ("rules", "measure")),
    (u"A31 1 つずつ書く fact の空の印を付けない", u"                if row.get(\"nil\"):\n                    attrs[NIL_ATTR] = \"true\"\n            else:", u"                pass\n            else:", ("rules", "measure")),
    (u"A32 forever の文脈を時点に潰す", u"        kind, end = A1.KIND_NONE, u\"\"\n    members", u"        kind, end = A1.KIND_INSTANT, u\"\"\n    members", ("rules",)),
    # ---- 配線
    (u"W1 別の門の規準の字を関数の名にする", u"def mode_val(values):", u"def mutate(x):\n    return x\n\n\ndef mode_val(values):", ("wiring",)),
    (u"W2 別の門の規準の字を説明文に書く", u"# 小さな部品\n", u"# 小さな部品(注入)\n", ("wiring",)),
    (u"W3 便 XA1 の script を他の便と重なる名で読む", u"CONTEXT_NAME = \"_xs0_sheet_context_2026_11_22\"", u"CONTEXT_NAME = \"_xa1_sheet_wall_2026_11_22\"", ("wiring",)),
    (u"W4 前の便の関数を写す", u"def mode_val(values):", u"def mode_first(values):\n    return values\n\n\ndef mode_val(values):", ("wiring",)),
    (u"W5 zipfile を import する", u"import time\n\nHERE", u"import time\nimport zipfile\n\nHERE", ("wiring",)),
    (u"W6 subprocess を import する", u"import time\n\nHERE", u"import time\nimport subprocess\n\nHERE", ("wiring",)),
    (u"W7 engine を import する", u"import time\n\nHERE", u"import time\nfrom adapters.xbrl import instance\n\nHERE", ("wiring",)),
    (u"W8 Stop を別に読む", u"W = A1.W ", u"W = _load_sibling(\"_xs0_other_wall\", \"xbrl_tag_wall_2026-11-21.py\")  # ", ("wiring", "called")),
    (u"W9 前の便の place_positions を写す", u"def mode_val(values):", u"def place_positions(text, positions):\n    return []\n\n\ndef mode_val(values):", ("wiring",)),
    (u"W10 前の便の choose_combo を呼ばない", u"        _d, combo, flags, _lines, _tally = A1.choose_combo(items, ends, mems)", u"        _d, combo, flags, _lines, _tally = (0, \"ACC\", [], None, None)", ("wiring", "rules")),
    (u"W11 scratchpad の path を書く", u"R_PAPER = u\"紙に表か線の決めが無い\"", u"R_PAPER = u\"紙に表か線の決めが無い\"\nSCRATCH = \"/private/tmp/x/scratchpad\"", ("wiring",)),
)
#: 黙ることが分かっている変異(理由つき)。予測は「黙る」ではなく、実行して黙った事実と理由を実行の後に書く(実行前は空)
SILENT_BY_DESIGN = {u"C11 混ぜ物の効いたを常に真にする": u"同値の変異: 混ぜ物の判定は、当て先の線の上の fact の 1 つでも期待と違えば先に偽を返す。ループを抜けたときの changed は必ず len(free) に等しい(free の fact は全部 nonFraction)ので、末尾の「changed == len(free)」は冗長で、真にしても何も変わらない"}


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"rules": rules_problems, u"paper": paper_problems, u"behaviour": blind_behaviour_problems, u"measure": measure_problems, u"chunk": chunk_problems,
             u"record": record_problems, u"clean": clean_problems, u"called": called_same_problems}
    if name in table:
        return table[name](mod)
    if name == u"blind":
        return blind_problems(src)
    if name == u"wiring":
        return import_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"rules", u"paper", u"blind", u"behaviour", u"measure", u"chunk", u"record", u"clean", u"called", u"wiring")


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
        for old, new in ((u"| XS0-1(主) | 表 F が同じ書類は 60 本以上。", u"| XS0-1(主) | 表 F が同じ書類は 61 本以上。"),
                         (u"fact の 4.8% 以上 6.5% 未満", u"fact の 4.8% 以上 6.6% 未満"), (u"33.6% 以上 38% 未満", u"33.6% 以上 39% 未満"),
                         (u"**紙の欄の比** = 紙の欄の数 ÷(fact の数 × 7)", u"**紙の欄の比** = 紙の欄の数 ÷(fact の数 × 8)"),
                         (u"空の fact には `decimals`・`scale`・`format`・`sign` を付けず", u"空の fact には `decimals`・`scale`・`format` を付けず"),
                         (u"字 `xs0:Changed` に変えて", u"字 `xs0:Other` に変えて"), (u"1 つずつ書く fact × 7", u"1 つずつ書く fact × 6")):
            self.assertGreaterEqual(seal.count(old), 1, old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"sheet_build", body)


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


class RuleTest(unittest.TestCase):
    def test_b_1_the_rules_one_by_one_on_made_up_documents(self):
        self.assertEqual([], rules_problems())

    def test_b_2_a_changed_paper_value_changes_the_attributes_and_the_folder_has_no_answer(self):
        self.assertEqual([], paper_problems())


class BlindTest(unittest.TestCase):
    def test_h_1_the_attribute_side_has_no_door_to_the_answer(self):
        self.assertEqual([], blind_problems())

    def test_h_2_the_attribute_command_takes_two_folders_only(self):
        self.assertEqual([], blind_behaviour_problems())

    def test_h_3_the_blind_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        for old, new in ((u"def attrs_tables(folder):", u"def attrs_tables(folder, entries=None):"),
                         (u"    ctx_idx = context_index(files)\n    tabs = table_lookup(sheet)", u"    X.doc_texts(folder)\n    ctx_idx = context_index(files)\n    tabs = table_lookup(sheet)"),
                         (u"    ctx_idx = context_index(files)\n    tabs = table_lookup(sheet)", u"    make_sheet_folder(folder, folder, folder)\n    ctx_idx = context_index(files)\n    tabs = table_lookup(sheet)")):
            self.assertEqual(1, base.count(old), old)
            self.assertNotEqual([], blind_problems(base.replace(old, new)), new)


class CountTest(unittest.TestCase):
    def test_c_1_one_document_end_to_end(self):
        self.assertEqual([], measure_problems())

    def test_c_2_chunks_judging_numbers_and_suspicions(self):
        self.assertEqual([], chunk_problems())


class RecordTest(unittest.TestCase):
    def test_e_1_the_record_path_from_a_fake_place(self):
        self.assertEqual([], record_problems())

    def test_e_2_forbidden_things_stop_the_record(self):
        self.assertEqual([], clean_problems())

    def test_e_3_the_real_record_when_present_is_clean_and_consistent(self):
        p = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(p):
            self.skipTest(u"記録は本番の走りの後に書かれる。記録の中身の検査は結果の門に置く(作り物の記録の検査は test_e_1)")
        text = read(RECORD_REL)
        MS.verify_record(json.loads(text, object_pairs_hook=od), text)


class WiringTest(unittest.TestCase):
    def test_f_1_imports_and_the_earlier_functions_are_called_not_copied(self):
        self.assertEqual([], import_problems())

    def test_f_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        for extra in (u"\nimport socket\n", u"\nimport zipfile\n", u"\nimport csv\n", u"\nimport subprocess\n", u"\nfrom adapters.xbrl import instance\n", u"\nX2 = os.system('a')\n",
                      u"\ndef select_docs(a, b):\n    return None\n", u"\ndef place_positions(a, b):\n    return None\n", u"\ndef run_doc(a):\n    return None\n", u"\ndef doc_texts(a):\n    return None\n",
                      u"\nSCRATCH = '/private/tmp/x'\n"):
            self.assertNotEqual([], import_problems(base + extra), extra)
        self.assertNotEqual([], import_problems(base.replace(u"A1.choose_combo(", u"choose_combo(")))
        self.assertNotEqual([], import_problems(base.replace(u"P.exec_build(", u"exec_build(")))
        self.assertNotEqual([], import_problems(base.replace(u"W.select_docs(", u"select_docs(")))

    def test_f_3_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_f_4_the_script_leaves_sys_modules_as_it_found_them(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_sheet_build_script_for_sysmodules_check")
        changed = [k for k in before if sys.modules.get(k) is not before[k]]
        self.assertEqual([], changed)
        self.assertEqual(mod.A1.__name__, u"_xs0_sheet_context_2026_11_22")
        self.assertEqual(mod.P.__name__, u"_xs0_pack_build_2026_11_22")
        self.assertIs(mod.W, mod.A1.W)
        self.assertIs(mod.Stop, mod.P.Stop)
        self.assertEqual([], called_same_problems())
        del mod

    def test_f_5_the_default_place_is_outside_the_repo_and_the_gate_never_opens_it(self):
        top = os.path.realpath(REPO)
        self.assertFalse(os.path.realpath(MS.DOCS_DIR).startswith(top + os.sep))
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(select_docs|run|check|build_record|dev_docs|dev_run)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"docs|rec_path|\bd\b|docs2", m.group(2)), m.group(0))

    def test_f_6_the_gate_calls_subprocess_only_for_git(self):
        src = read(GATE_REL)
        calls = re.findall(r"subprocess\.(\w+)", src)
        self.assertEqual(set(calls), {"run", "PIPE"})
        for m in re.finditer(r"subprocess\.run\(([^)]*)\)", src):
            self.assertTrue(m.group(1).startswith(u'["git"'), m.group(1))

    def test_f_7_the_script_has_no_scratchpad_path_and_calls_no_paid_api(self):
        src = read(SCRIPT_REL)
        for w in (u"scratchpad", u"/private/tmp", u"anthropic", u"openai", u"API_KEY", u"urllib", u"requests"):
            self.assertNotIn(w, src, w)


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

    def test_g_3_the_mutant_module_is_the_one_the_checks_look_at(self):
        u"""変異を入れた module の関数だけが検査の対象(実物の module を見て黙る型を防ぐ)。1 つの変異で、変異した module では赤・実物の module では緑。"""
        base = read(SCRIPT_REL)
        old, new = u"        rc = triple_ids[(c[0], c[2], c[3])] >= 2", u"        rc = triple_ids[(c[0], c[2], c[3])] >= 3"
        mod = load_source(base.replace(old, new))
        self.assertNotEqual([], guard(check_by_name, u"rules", mod, base))
        self.assertEqual([], check_by_name(u"rules", MS, base))
        self.assertIsNot(mod.build_sheet, MS.build_sheet)


if __name__ == "__main__":
    unittest.main()
