# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PACK_BUILD_SEAL_2026-11-22.md(XP0 ― 受理済みの有報の PublicDoc を原稿の folder に落とし、その folder だけを読む別の process の組む命令で htm・xsd・linkbase を丸ごと組むと、公開の道具が読むタクソノミ・fact・検査の鳴り方は元と同じになるか)の封の門。

**この門は置き場も道具も読まない**(書類の置き場 ``~/.cache/audit-core/edinet/``・道具の venv は 1 度も開かない。道具が無い機械でも緑)。通信しない。道具の呼び出しは作り物の runner に差し替える。
subprocess を呼ぶのは git と、組む命令(``python3 -I <script> build <folder> <folder>``)を作り物の folder に掛ける所だけ。
作り物の包み(PublicDoc に htm 2 つ・xsd・linkbase 5 つ・マニフェスト・``.xbrl``・AuditDoc)で、落とす・別の process で組む・比べる・混ぜ物・数え方・記録の検査を本物の関数のまま通す。
作り物の道具・作り物の包み・手で数えた値は、便 XT0 の封の門の部品を importlib で読んで使う(写さない)。

**この門が縛るもの**

1. 封の字: 封の commit(c03a3348)・封の file が commit した blob と同じ・便 XT0 の封と同じ道具・掛け方・時間の上限・67 本・開発の 5 本・混ぜ物 4 種類・予測の境の数・限界の字が script の定数と同じ。
2. engine は読まない・封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 落とす(原稿の folder の file の名・目次・素の本文にタグが無いこと・表の JSON・元の htm・xsd・linkbase・マニフェスト・AuditDoc の字が folder に無いこと)・組む(folder だけを読む・同じ bytes を出す・出す folder の形・知らない形は断る・終わりの値)・別の process の組む命令(引数は folder 2 つだけ・cwd・shell を通さない・時間の上限・本物の process)・混ぜ物 4 つ(disk の上で 1 か所だけ)。
4. 組む命令の中身(``render_folder``)は folder だけを引数に取り、元の包み・zip を読まない。``process_doc`` は組む命令を別の process(``exec_build``)で呼ぶ。便 XB0・便 XT0 の剥がす・組むの関数を写さずに呼ぶ。
5. 書類 1 本の通し(元の包み・組み直した包みを同じ掛け方 A・B で 1 回ずつ・.xbrl を除く・ほかの file は元のまま・2 度組む・同じ process との一致・混ぜ物 4 つ)・数え方(§2)・記録の検査と禁止のもの。
6. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない。組む命令の本物の process の検査だけは、替えた版を使い捨ての場所に書いて走らせる)。表は実行より先に書いた(予測 = 赤になるべき検査の名前)。
"""
import ast
import collections
import contextlib
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
    mod = types.ModuleType("xbrl_pack_build_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_PACK_BUILD_SEAL_2026-11-22.md"
XT0_SEAL_REL = "docs/XBRL_TAXONOMY_BUILD_SEAL_2026-11-22.md"
SEAL_COMMIT_SHORT = "c03a3348"
SCRIPT_REL = "measure/xbrl_pack_build_2026-11-22.py"
GATE_REL = "tests/measure/test_xbrl_pack_build_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/pack_build_2026-11-22.json"
MS = load_module(SCRIPT_REL, "xbrl_pack_build_script_for_seal_gate")
X = load_module("tests/measure/test_xbrl_taxonomy_build_seal.py", "xp0_gate_helpers_from_taxonomy_gate")
ORDER_FILES = (SCRIPT_REL, GATE_REL)
od = collections.OrderedDict
TAXONOMY_NAME = "_xp0_taxonomy_build_2026_11_22"
SIBLINGS = ("xbrl_taxonomy_build_2026-11-22.py", "xbrl_inline_build_2026-11-21.py", "xbrl_edinet_validate_2026-11-21.py", "xbrl_tag_wall_2026-11-21.py")
KINDS = X.KINDS
read = X.read
read_text = X.read_text
read_bytes_sha = X.read_bytes_sha
Temp = X.Temp
stops = X.stops
guard = X.guard
sha_of = X.sha_of
sha_or_none = X.sha_or_none
b = X.b


def read_file(path):
    with open(path, "rb") as fh:
        return fh.read()


def write_file(path, data):
    with open(path, "wb") as fh:
        fh.write(data)


# ======================================================================== 作り物の包み(手で書いた字)
STEM1 = "XBRL/PublicDoc/jpcrp030000-asr-001_E99991-000_2026-03-31_01_2026-06-30"
HTM_A_NAME = "XBRL/PublicDoc/0100000_a_E99991-000_ixbrl.htm"
HTM_B_NAME = "XBRL/PublicDoc/0200000_b_E99991-000_ixbrl.htm"
HTM_SUB_NAME = "XBRL/PublicDoc/sub/0300000_c_E99991-000_ixbrl.htm"
#: 頭の部と 1 つの nonNumeric を持つ htm(``&amp;`` などの字・自己閉じでない形)
HTM_A = u"""<html><body>
<p>表紙 &amp; 前置き</p>
<ix:header>
<ix:references>
<link:schemaRef xlink:type="simple" xlink:href="x.xsd" />
</ix:references>
<ix:resources>
<xbrli:context id="C1">
<xbrli:entity>
<xbrli:identifier scheme="http://example.org/id">E99991</xbrli:identifier>
</xbrli:entity>
<xbrli:period>
<xbrli:instant>2026-03-31</xbrli:instant>
</xbrli:period>
</xbrli:context>
<xbrli:unit id="JPY">
<xbrli:measure>iso4217:JPY</xbrli:measure>
</xbrli:unit>
</ix:resources>
</ix:header>
<ix:nonNumeric name="jpcrp_cor:Title" contextRef="C1">題名</ix:nonNumeric>
</body></html>
"""
#: 0 だけの nonFraction の次に 0 だけでない nonFraction(``\r\n`` を含む)
HTM_B = u'<html><body>\r\n<p>売上 <ix:nonFraction name="jppfs_cor:Zero" contextRef="C1" unitRef="JPY" decimals="0">0</ix:nonFraction> と <ix:nonFraction name="jppfs_cor:Assets" contextRef="C1" unitRef="JPY" decimals="0" scale="3">1,234</ix:nonFraction></p>\r\n</body></html>\r\n'
HTM_SUB = u'<html><body><ix:nonFraction name="jppfs_cor:Other" contextRef="C1" unitRef="JPY" decimals="0">77</ix:nonFraction></body></html>'


def htm_one(content, name=u"jppfs_cor:Only"):
    return u'<html><body><ix:nonFraction name="%s" contextRef="C1" unitRef="JPY" decimals="0">%s</ix:nonFraction></body></html>' % (name, content)


def pack_texts(no=1):
    return X.doc_texts(no)


def make_pack(path, no=1, htms=None, declined=False, shuffle=False):
    u"""作り物の包み。``htms`` = [(PublicDoc の名, 字)](既定は htm 3 つ。名の昇順と違う順に並べる)。"""
    texts = pack_texts(no)
    if declined:
        texts["cal"] = texts["cal"].replace(u'weight="1"', u'weight="1" zzz="1"', 1)
    items = [(STEM1.replace("E99991", "E9999%d" % no) + X.FILE_SUFFIX_OF[k], texts[k].encode("utf-8")) for k in KINDS]
    htms = [(HTM_B_NAME, HTM_B), (HTM_A_NAME, HTM_A), (HTM_SUB_NAME, HTM_SUB)] if htms is None else htms
    items += [(n.replace("E99991", "E9999%d" % no), t.encode("utf-8")) for n, t in htms]
    if shuffle:
        items.reverse()
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("XBRL/PublicDoc/manifest_PublicDoc.xml", b"<manifest/>")
        z.writestr("XBRL/PublicDoc/logo.png", b"PNG-not-an-image")
        for n, data in items:
            z.writestr(n, data)
        z.writestr("XBRL/PublicDoc/api_added_E9999%d-000.xbrl" % no, b"<xbrl/>")
        z.writestr("XBRL/AuditDoc/audit.xml", b"<a/>")


def make_pack_docs(d, count=3, declined=()):
    for i in range(count):
        make_pack(os.path.join(d, "S2FAKE0%d.zip" % (i + 1)), i + 1, declined=(i + 1) in declined)
    with zipfile.ZipFile(os.path.join(d, "S2OTHER1.zip"), "w") as z:
        z.writestr("XBRL/PublicDoc/jpsps070000-xxx-001_E99999-000.xsd", b"<schema/>")
    return d


def entries_of(path, ms=None):
    return (ms or MS).B.load_package(path)


class PackRunner(X.FakeRunner):
    u"""作り物の道具。便 XT0 の門の作り物に、fact の行へ値(htm の nonFraction・nonNumeric の中の字)を足す。"""

    def __call__(self, cmd, timeout):
        c = X.strip_seed(cmd)
        res = X.FakeRunner.__call__(self, cmd, timeout)
        if os.path.basename(c[0]) == "arelleCmdLine" and "--facts" in c:
            blobs = self.calls[-1]["blobs"]
            rows = [(u"Name", u"Value")]
            for n, data in sorted(blobs.items()):
                if n.endswith(".htm"):
                    for m in re.finditer(r'<ix:(?:nonFraction|nonNumeric)\b[^>]*\bname="([^"]+)"[^>]*>([^<]*)<', data.decode("utf-8")):
                        rows.append((m.group(1), m.group(2)))
            self.write_csv(c[c.index("--facts") + 1], rows)
        return res


class InProc(object):
    u"""別の process の組む命令の作り物。呼ばれた引数・cwd の中身・folder の中身を覚え、組む命令の本体(``build_main``)を同じ process の中で走らせる。"""

    def __init__(self, ms, mangle=None, rc_after_first=None):
        self.ms = ms
        self.calls = []
        self.mangle = mangle
        self.rc_after_first = rc_after_first

    def __call__(self, cmd, cwd, timeout):
        folder, out = cmd[-2], cmd[-1]
        listing = sorted(os.listdir(cwd)) if os.path.isdir(cwd) else None
        ffiles = dict((n, read_file(os.path.join(folder, n))) for n in sorted(os.listdir(folder))) if os.path.isdir(folder) else {}
        self.calls.append(dict(cmd=list(cmd), cwd=cwd, timeout=timeout, listing=listing, folder=folder, folder_files=ffiles, out=out))
        if self.rc_after_first is not None and len(self.calls) >= 2:
            return self.rc_after_first
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = self.ms.build_main(list(cmd[4:]))
        if self.mangle is not None and rc == 0:
            self.mangle(out, len(self.calls))
        return rc, err.getvalue(), False


def mangle_second(out, n):
    u"""2 回目の出力だけ 1 つの file の字を変える(組む命令が走るたびに違う字を書く)。"""
    if n == 2:
        p = os.path.join(out, "0100000_a_E99991-000_ixbrl.htm")
        write_file(p, read_file(p) + b" ")


def mangle_first(out, n):
    u"""1 回目の出力だけ 1 つの file の字を変える(同じ process の字と違う)。"""
    if n == 1:
        p = os.path.join(out, "0100000_a_E99991-000_ixbrl.htm")
        write_file(p, read_file(p) + b" ")


def peeled(d, ms=None, **kw):
    u"""作り物の包みを落とした原稿の folder。(包みの場所, folder, 目次, entries)。"""
    ms = ms or MS
    zp = os.path.join(d, "p.zip")
    make_pack(zp, **kw)
    ent = entries_of(zp, ms)
    folder = os.path.join(d, "man")
    index = ms.peel_folder(ent, folder)
    return zp, folder, index, ent


def tree_of(folder):
    out = {}
    for dp, _dn, fns in os.walk(folder):
        for fn in fns:
            p = os.path.join(dp, fn)
            out[os.path.relpath(p, folder).replace(os.sep, "/")] = read_file(p)
    return out


def captured(fn, *a, **kw):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        try:
            r = fn(*a, **kw)
        except SystemExit as exc:
            r = ("exit", exc.code)
    return r, err.getvalue()


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XP0-1", (58, None)), ("XP0-2", (None, 2)), ("XP0-3", (58, None)), ("XP0-4", (u"断らなかった書類の数", None)), ("XP0-5", (u"断らなかった書類の数", None)), ("XP0-6", (u"作れた数", None)), ("XP0-7", (50, None))])
SEAL_BOUND_TEXT = od([("XP0-1", u"全部同じ書類は 58 本以上"), ("XP0-2", u"断った書類は 2 本以下"), ("XP0-3", u"鳴り方が同じ書類は 58 本以上"), ("XP0-4", u"2 度が同じ書類は、断らなかった書類の全部"),
                      ("XP0-5", u"道筋が同じ書類は、断らなかった書類の全部"), ("XP0-6", u"作れた混ぜ物の全部で、違いを見つける"), ("XP0-7", u"50 本以上")])
SEAL_MIX = (u"N1 本文の数を変える", u"N2 fact を抜く", u"N3 ラベルを変える", u"N4 計算の向きを返す")


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    x0 = read(XT0_SEAL_REL)
    out_ = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out_.append(u"script の封の commit・path・記録の path が門と違う")
    for rel in (SCRIPT_REL, RECORD_REL, GATE_REL):
        if rel not in seal:
            out_.append(u"封に path が無い: %s" % rel)
    if ms.TOOL_VERSION != u"2.47.5" or u"`arelle-release` の版 `2.47.5`" not in x0:
        out_.append(u"版の字が便 XT0 の封と違う")
    if ms.SHA_P != X.SEAL_SHA_P or (u"`%s`" % X.SEAL_SHA_P) not in x0:
        out_.append(u"ModelValue.py の sha256 が便 XT0 の封と違う")
    if ms.PLUGINS != u"validate/EDINET|inlineXbrlDocumentSet" or u"--plugins 'validate/EDINET|inlineXbrlDocumentSet'" not in x0:
        out_.append(u"plugins が便 XT0 の封と違う")
    if ms.YEAR != u"EDINET-2026" or u"--disclosureSystem EDINET-2026" not in x0:
        out_.append(u"規則の年が便 XT0 の封と違う")
    if ms.FACT_COLS != u"Name contextRef unitRef Dec Value EntityScheme EntityIdentifier Period Dimensions" or (u"--factListCols '%s'" % ms.FACT_COLS) not in x0:
        out_.append(u"--factListCols が便 XT0 の封と違う")
    if u"便 XT0 の封 §1 と同じ道具 P・同じ掛け方 A・B・同じ時間の上限" not in seal or u"`PYTHONHASHSEED=0`" not in seal:
        out_.append(u"封に便 XT0 の道具・掛け方・時間の上限・PYTHONHASHSEED=0 の字が無い")
    if ms.TIMEOUT_SEC != 600 or u"1 回の時間の上限は 600 秒" not in x0:
        out_.append(u"時間の上限が封と違う")
    if ms.DOCS_WANT != 67 or u"便 XG0 の封 §1 と同じ 67 本" not in seal or u"書類は 67 本(違えば script は止まる)" not in seal:
        out_.append(u"67 が封と違う")
    if ms.DEV_COUNT != 5 or u"並びの頭の 5 本" not in seal:
        out_.append(u"開発の 5 本が封と違う")
    if ms.PUBLICDOC != u"XBRL/PublicDoc/":
        out_.append(u"PublicDoc の場所が違う")
    if tuple(ms.OUTPUT_KEYS) != (u"概念", u"役割型", u"表示", u"計算", u"次元", u"ラベルの関係", u"一般特殊") or tuple(ms.FILE_KINDS) != ("xsd", "cal", "def", "lab", "lab-en", "pre"):
        out_.append(u"書き出し 7 つ・file の 6 種類が便 XT0 と違う")
    if tuple(ms.MIX_KINDS) != (u"本文の数を変える", u"fact を抜く", u"ラベルを変える", u"計算の向きを返す") or tuple(ms.MIX_IDS) != ("N1", "N2", "N3", "N4"):
        out_.append(u"混ぜ物の種類が script で封と違う")
    for m in SEAL_MIX:
        if (u"**%s**" % m) not in seal:
            out_.append(u"封に混ぜ物の字が無い: %s" % m)
    if u"開発の 5 本 × 4 種類 = 20 個" not in seal:
        out_.append(u"混ぜ物の数が封と違う")
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS):
        out_.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [x for x in seal.splitlines() if x.startswith(u"| %s" % k)]
        if len(row_) != 1 or t not in row_[0]:
            out_.append(u"封の予測の行の字が違う: %s" % k)
    if u"`python3 -I <script> build <原稿の folder> <出す folder>`" not in seal or u"引数は folder 2 つだけ" not in seal:
        out_.append(u"封の組む命令の字が違う")
    if ms.build_command(u"F", u"O")[1:] != [u"-I", ms.SCRIPT_PATH, u"build", u"F", u"O"] or ms.build_command(u"F", u"O")[0] != sys.executable:
        out_.append(u"組む命令の引数の並びが封と違う")
    if u"docID・会社の名・EDINET コード・file の名・fact の値・要素の名・ラベルの字・role の URI・指摘の行の本文は書かない" not in seal:
        out_.append(u"封の記録の禁止の字が違う")
    if u"**folder に置かないもの**: 元の `.htm`・`.xsd`・linkbase の字そのもの・元の包み・マニフェスト・画像・AuditDoc" not in seal:
        out_.append(u"封の folder に置かないものの字が違う")
    sec7 = seal.split(u"## §7", 1)[-1]
    want_phrases = (u"原稿の folder は元の包みから作っている", u"マニフェスト・画像・AuditDoc は元のまま", u"道具 P。司令塔が 1 行を直したもの", u"道具が書き出さない性質", u"EDINET の本物の検査とは照らしていない",
                    u"62 本は便 XB0・便 XT0 で既に組み直した書類", u"無作為ではない。有報だけ", u"「EDINET の検査に通る」「XBRL を作れる」「専用の道具が要らない」")
    got_phrases = (u"原稿の folder は元の包みから作っている", u"マニフェスト・画像・監査報告書の包みは元のまま", u"1 行を直したもの", u"道具が書き出さない性質", u"EDINET の本物の検査とは照らしていない",
                   u"62 本は便 XB0・便 XT0 で既に組み直した書類", u"無作為ではない。有報だけ", u"「EDINET の検査に通る」「XBRL を作れる」「専用の道具が要らない」")
    if any(p not in sec7 for p in want_phrases) or any(k not in u"".join(ms.LIMITS) for k in got_phrases):
        out_.append(u"限界の字が封 §7 と違う")
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
    pr = X.load_helpers()
    others = list(ORDER_FILES) if others is None else others
    return list(pr.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others))


def engine_zero_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core"], stdout=subprocess.PIPE, universal_newlines=True)
    return [u"engine が封の後に変わっている: %s" % x for x in rc.stdout.splitlines() if x.strip()]


# ======================================================================== 2. 落とす
HAND_INDEX_NAMES = [u"0100000_a_E99991-000_ixbrl.htm", u"0200000_b_E99991-000_ixbrl.htm", u"sub/0300000_c_E99991-000_ixbrl.htm"]
HAND_FILES = [u"index.json", u"t0000.json", u"t0000.txt", u"t0001.json", u"t0001.txt", u"t0002.json", u"t0002.txt", u"taxonomy.json"]


def folder_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        zp, folder, index, ent = peeled(d, ms)
        if sorted(os.listdir(folder)) != HAND_FILES:
            out_.append(u"原稿の folder の file の名が手で決めた値と違う: %s" % sorted(os.listdir(folder)))
        on_disk = ms.jload(read_file(os.path.join(folder, "index.json")))
        if json.dumps(on_disk, ensure_ascii=False) != json.dumps(index, ensure_ascii=False):
            out_.append(u"目次の返り値と file が違う")
        if [i["name"] for i in on_disk["htm"]] != HAND_INDEX_NAMES or [i["text"] for i in on_disk["htm"]] != [u"t0000.txt", u"t0001.txt", u"t0002.txt"] or [i["tables"] for i in on_disk["htm"]] != [u"t0000.json", u"t0001.json", u"t0002.json"]:
            out_.append(u"目次の htm の並び(名の昇順)・名が違う: %s" % json.dumps(on_disk["htm"], ensure_ascii=False))
        tax = on_disk["taxonomy"]
        want_names = dict((k, u"jpcrp030000-asr-001_E99991-000_2026-03-31_01_2026-06-30" + X.FILE_SUFFIX_OF[k]) for k in KINDS)
        if tax["file"] != u"taxonomy.json" or dict(tax["names"]) != want_names or list(tax["names"]) != list(KINDS) or list(on_disk) != ["htm", "taxonomy"]:
            out_.append(u"目次のタクソノミの名が違う: %s" % json.dumps(tax, ensure_ascii=False))
        B = ms.B
        want_plain = []
        for i, nm in enumerate(HAND_INDEX_NAMES):
            htm = dict((n, data) for n, data in [(HTM_A_NAME, HTM_A), (HTM_B_NAME, HTM_B), (HTM_SUB_NAME, HTM_SUB)])[ms.PUBLICDOC + nm.replace("E99991", "E99991")]
            plain, F, H = B.strip_text(htm.replace("E99991", "E99991"))
            got = read_file(os.path.join(folder, u"t%04d.txt" % i))
            if got != plain.encode("utf-8"):
                out_.append(u"素の本文の file が剥がした素の本文と違う(改行を変える・字を変える): %d" % i)
            if b"<ix:" in got or b"</ix:" in got:
                out_.append(u"素の本文にタグが残っている: %d" % i)
            tabs = ms.jload(read_file(os.path.join(folder, u"t%04d.json" % i)))
            if list(tabs) != ["F", "H"] or json.dumps(tabs["F"], ensure_ascii=False, sort_keys=True) != json.dumps(F, ensure_ascii=False, sort_keys=True) or json.dumps(tabs["H"], ensure_ascii=False, sort_keys=True) != json.dumps(H, ensure_ascii=False, sort_keys=True):
                out_.append(u"本文の表の JSON が剥がした表と違う: %d" % i)
            want_plain.append(plain)
        if b"\r\n" not in read_file(os.path.join(folder, u"t0001.txt")):
            out_.append(u"素の本文の改行(CRLF)が変わった")
        tabs0 = ms.jload(read_file(os.path.join(folder, u"t0000.json")))
        if tabs0["H"] is None or tabs0["H"].get("sections") != [u"ix:references", u"ix:resources"]:
            out_.append(u"頭の部の表が JSON に無い")
        tj = read_file(os.path.join(folder, "taxonomy.json"))
        tab_t = ms.jload(tj)["tables"]
        S, K = ms.T.strip_tables(od((k, v[1]) for k, v in ms.T.find_files(ent).items())), None
        if json.dumps(tab_t, ensure_ascii=False, sort_keys=True) != json.dumps(S, ensure_ascii=False, sort_keys=True) or list(tab_t) != list(KINDS):
            out_.append(u"タクソノミの表の JSON が剥がした表と違う")
        if u"売上".encode("utf-8") not in tj or b"\\u" in tj:
            out_.append(u"JSON を ensure_ascii=False で書いていない(日本語の字が escape されている)")
        for fn in HAND_FILES:
            raw = read_file(os.path.join(folder, fn))
            if fn.endswith(".json") and (b": " in raw or b", " in raw.split(b'"text"')[0][:200]) and False:
                pass
            if fn.endswith(".json") and (b'": ' in raw or b'", "' in raw or b"\n" in raw):
                out_.append(u"JSON が封の決め(separators=(',', ':'))の字でない: %s" % fn)
        # 元の字・マニフェスト・AuditDoc が folder に無い
        everything = b"".join(read_file(os.path.join(folder, fn)) for fn in HAND_FILES)
        origs = [data for info, data in ent if info.filename.startswith("XBRL/PublicDoc/") and (info.filename.endswith(".htm") or info.filename.endswith(".xsd") or info.filename.endswith(".xml"))]
        if not origs or any(o in everything for o in origs):
            out_.append(u"元の htm・xsd・linkbase の字そのものが folder に在る")
        for fn in HAND_FILES:
            raw = read_file(os.path.join(folder, fn))
            if any(raw == o for o in origs):
                out_.append(u"folder の file が元の file と同じ bytes: %s" % fn)
        for token in (b"<manifest/>", b"PNG-not-an-image", b"<a/>", b"<xbrl/>"):
            if token in everything:
                out_.append(u"マニフェスト・画像・AuditDoc の字が folder に在る")
        if b"<?xml" in everything or b"<ix:" in everything or b"<xsd:" in everything or b"<link:" in everything:
            out_.append(u"元の XML の字(宣言・タグ)が folder に在る")
        # 落とす側の断り
        zp2 = os.path.join(d, "bad_ix.zip")
        make_pack(zp2, htms=[(HTM_A_NAME, u"<html><ix:zzz>x</ix:zzz></html>")])
        f2 = os.path.join(d, "man2")
        try:
            ms.peel_folder(entries_of(zp2, ms), f2)
            out_.append(u"知らない ix の要素を断らない")
        except ms.Refuse as exc:
            if exc.reason != u"知らない ix の要素" or os.path.exists(f2):
                out_.append(u"断りの理由・folder が残る: %s" % exc.reason)
        zp3 = os.path.join(d, "bad_tax.zip")
        make_pack(zp3, declined=True)
        f3 = os.path.join(d, "man3")
        try:
            ms.peel_folder(entries_of(zp3, ms), f3)
            out_.append(u"知らない属性のタクソノミを断らない")
        except ms.Refuse as exc:
            if exc.reason != u"知らない属性" or os.path.exists(f3):
                out_.append(u"断りの理由・folder が残る(タクソノミ): %s" % exc.reason)
        # 落とす途中の例外(知らない形でない例外)も断り
        real_strip = ms.T.strip_tables
        ms.T.strip_tables = lambda *a, **k: (_ for _ in ()).throw(ValueError("x"))
        try:
            ms.peel_folder(ent, os.path.join(d, "man7"))
            out_.append(u"落とす途中の例外を断りにしない")
        except ms.Refuse as exc:
            if exc.reason != u"落とす途中の例外" or os.path.exists(os.path.join(d, "man7")):
                out_.append(u"落とす途中の例外の理由・folder が違う: %s" % exc.reason)
        except Exception as exc:                            # noqa: BLE001
            out_.append(u"落とす途中の例外が断りにならず外へ出る: %s" % type(exc).__name__)
        finally:
            ms.T.strip_tables = real_strip
        # 落とす命令
        rc, err = captured(ms.peel_main, [zp, os.path.join(d, "man4")])
        if rc != 0 or sorted(os.listdir(os.path.join(d, "man4"))) != HAND_FILES:
            out_.append(u"peel 命令が folder を作らない: %s" % (rc,))
        rc, err = captured(ms.peel_main, [zp3, os.path.join(d, "man5")])
        if rc != 2 or u"DECLINE: 知らない属性" not in err or os.path.exists(os.path.join(d, "man5")):
            out_.append(u"peel 命令の断りの終わりの値・理由の行が違う: %s %s" % (rc, err))
        rc, err = captured(ms.peel_main, [zp])
        if rc != 64:
            out_.append(u"peel 命令の引数が足りないとき 64 で終わらない")
        r, _e = captured(ms.main, ["peel", zp, os.path.join(d, "man6")])
        if r != ("exit", 0) or not os.path.isdir(os.path.join(d, "man6")):
            out_.append(u"main の peel が peel_main に着かない: %s" % (r,))
    return out_


# ======================================================================== 3. 組む(原稿の folder だけを読む)
def render_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        zp, folder, index, ent = peeled(d, ms)
        files, names, tables = ms.peel_tables(ent)
        want = ms.same_process_tree(files, names, tables)
        if want is None or set(want) != set(HAND_INDEX_NAMES) | set(want_names().values()):
            out_.append(u"同じ process の字の file の集まりが違う")
        # 読む file は folder の中の目次・表・素の本文だけ
        seen = []
        real = ms.read_bytes
        ms.read_bytes = lambda p: (seen.append(p), real(p))[1]
        try:
            got = ms.render_folder(folder)
        finally:
            ms.read_bytes = real
        if dict(got) != want or list(got) != HAND_INDEX_NAMES + [want_names()[k] for k in KINDS]:
            out_.append(u"組んだ字が同じ process の字と違う(か並びが目次の並びでない)")
        if sorted(os.path.relpath(p, folder) for p in seen) != sorted(HAND_FILES) or any(os.path.dirname(os.path.abspath(p)) != os.path.abspath(folder) for p in seen):
            out_.append(u"組む命令が folder の中の目次・表・素の本文のほかを読んでいる: %s" % seen)
        if any(not isinstance(v, bytes) for v in got.values()) or ms.render_folder(folder) != got:
            out_.append(u"組んだ字が bytes でない・2 度組むと違う")
        # 出す folder
        o1 = os.path.join(d, "o1")
        rc, err = captured(ms.build_main, [folder, o1])
        if rc != 0 or tree_of(o1) != want or err:
            out_.append(u"build_main の出す folder が組んだ字と違う(か標準のエラーに出す): %s" % (rc,))
        if not os.path.isdir(os.path.join(o1, "sub")):
            out_.append(u"出す folder に相対の名の下の folder を作らない")
        r, _e = captured(ms.main, ["build", folder, os.path.join(d, "o2")])
        if r != ("exit", 0) or tree_of(os.path.join(d, "o2")) != want:
            out_.append(u"main の build が build_main に着かない・終わりの値が 0 でない: %s" % (r,))
        # 引数は folder 2 つだけ
        for args in ([], [folder], [folder, os.path.join(d, "o3"), "x"]):
            rc, err = captured(ms.build_main, args)
            if rc != 64 or os.path.exists(os.path.join(d, "o3")):
                out_.append(u"引数が 2 つでないとき 64 で終わらない: %d 個 → %s" % (len(args), rc))
            r, _e = captured(ms.main, ["build"] + args)
            if r != ("exit", 64):
                out_.append(u"main の build が引数の数を縛らない: %d 個 → %s" % (len(args), r))
        # 知らない形は断る(2・固定の理由の行)
        def broken(label, fn, reason, code=2):
            fd = os.path.join(d, "b_" + re.sub(r"\W", "", label))
            shutil.copytree(folder, fd)
            fn(fd)
            ob = os.path.join(d, "ob_" + re.sub(r"\W", "", label))
            rc, err = captured(ms.build_main, [fd, ob])
            if rc != code or os.path.exists(ob):
                out_.append(u"%s: 終わりの値が %s でない(か出す folder が在る): %s" % (label, code, rc))
            elif code == 2 and (ms.DECLINE_PREFIX + reason) not in err.splitlines():
                out_.append(u"%s: 標準のエラーに理由の行が無い: %r" % (label, err))
            elif code != 2 and (ms.DECLINE_PREFIX in err):
                out_.append(u"%s: 例外なのに断りの行を出す" % label)

        def edit_index(fn):
            def go(fd):
                p = os.path.join(fd, "index.json")
                ix = ms.jload(read_file(p))
                fn(ix)
                write_file(p, ms.jdump(ix))
            return go

        def edit_tax(fn):
            def go(fd):
                p = os.path.join(fd, "taxonomy.json")
                t = ms.jload(read_file(p))
                fn(t)
                write_file(p, ms.jdump(t))
            return go

        def edit_tab(fn):
            def go(fd):
                p = os.path.join(fd, "t0001.json")
                t = ms.jload(read_file(p))
                fn(t)
                write_file(p, ms.jdump(t))
            return go
        broken(u"名に ..", edit_index(lambda ix: ix["htm"][0].__setitem__("name", u"../x.htm")), u"目次の名が知らない形")
        broken(u"名が絶対", edit_index(lambda ix: ix["htm"][0].__setitem__("name", u"/etc/x.htm")), u"目次の名が知らない形")
        broken(u"名が空の部分", edit_index(lambda ix: ix["htm"][0].__setitem__("name", u"a//x.htm")), u"目次の名が知らない形")
        broken(u"名に逆斜線", edit_index(lambda ix: ix["htm"][0].__setitem__("name", u"a\\x.htm")), u"目次の名が知らない形")
        broken(u"素の本文の名に /", edit_index(lambda ix: ix["htm"][0].__setitem__("text", u"../t0000.txt")), u"目次の名が知らない形")
        broken(u"表の名に /", edit_index(lambda ix: ix["htm"][0].__setitem__("tables", u"sub/t0000.json")), u"目次の名が知らない形")
        broken(u"htm の名が重なる", edit_index(lambda ix: ix["htm"][1].__setitem__("name", ix["htm"][0]["name"])), u"目次の名が重なる")
        broken(u"タクソノミの名に ..", edit_index(lambda ix: ix["taxonomy"]["names"].__setitem__("xsd", u"../a.xsd")), u"目次の名が知らない形")
        broken(u"タクソノミの名が htm と重なる", edit_index(lambda ix: ix["taxonomy"]["names"].__setitem__("xsd", ix["htm"][0]["name"])), u"目次の名が重なる")
        broken(u"タクソノミの file の名に /", edit_index(lambda ix: ix["taxonomy"].__setitem__("file", u"../taxonomy.json")), u"目次の名が知らない形")
        broken(u"要素の知らない属性", edit_tax(lambda t: t["tables"]["xsd"]["elements"][0].__setitem__("zzz", "1")), u"知らない属性")
        broken(u"知らない拡張 link", edit_tax(lambda t: t["tables"]["cal"]["links"][0].__setitem__("tag", u"zzzLink")), u"知らない拡張 link")
        broken(u"表 F の知らない kind", edit_tab(lambda t: t["F"][0].__setitem__("kind", u"zzz")), u"知らない ix の要素")
        broken(u"表 F の親の番号", edit_tab(lambda t: t["F"][0].__setitem__("parent", 9)), u"親の番号が合わない")
        broken(u"表 F の位置", edit_tab(lambda t: t["F"][0].__setitem__("start", 10 ** 6)), u"位置が合わない")
        broken(u"JSON でない", lambda fd: write_file(os.path.join(fd, "t0001.json"), b"{not json"), u"組む途中の例外")
        broken(u"file が無い", lambda fd: os.remove(os.path.join(fd, "t0001.txt")), u"組む途中の例外")
        broken(u"UTF-8 でない素の本文", lambda fd: write_file(os.path.join(fd, "t0001.txt"), b"\xff\xfe\x00"), u"組む途中の例外")
        rc, err = captured(ms.build_main, [os.path.join(d, "nofolder"), os.path.join(d, "ox")])
        if rc != 2 or (ms.DECLINE_PREFIX + u"組む途中の例外") not in err.splitlines() or os.path.exists(os.path.join(d, "ox")):
            out_.append(u"folder が無いとき断り(2)で終わらない: %s" % rc)
        # 出す folder が既に在る(組んだ後に書けない)→ 断りでなく例外(1)
        os.makedirs(os.path.join(d, "exists"))
        rc, err = captured(ms.build_main, [folder, os.path.join(d, "exists")])
        if rc != 1 or ms.DECLINE_PREFIX in err or "ERROR" not in err:
            out_.append(u"出す folder が既に在るとき例外(1)で終わらない: %s" % rc)
        # cwd に毒の目次が在っても読まない
        poison = os.path.join(d, "cwdpoison")
        os.makedirs(poison)
        write_file(os.path.join(poison, "index.json"), b"{poison")
        here = os.getcwd()
        os.chdir(poison)
        try:
            if ms.render_folder(os.path.abspath(folder)) != want:
                out_.append(u"cwd の目次が組んだ字に効く")
        except Exception:                                   # noqa: BLE001
            out_.append(u"cwd に毒の目次が在ると組めない(cwd の file を読んでいる)")
        finally:
            os.chdir(here)
        # folder の中の知らない file・cwd の poison を読まない
        fd = os.path.join(d, "decoy")
        shutil.copytree(folder, fd)
        write_file(os.path.join(fd, "extra.htm"), b"<html>poison</html>")
        write_file(os.path.join(fd, "orig.zip"), b"not a zip")
        if ms.render_folder(fd) != want:
            out_.append(u"folder の中の目次に無い file が組んだ字に効く")
        # 元の包みが無くても組める(包みを消した作業の場所で組む)
        os.remove(zp)
        if ms.render_folder(folder) != want:
            out_.append(u"元の包みを消すと組めない(包みを読んでいる)")
    return out_


def want_names():
    return dict((k, u"jpcrp030000-asr-001_E99991-000_2026-03-31_01_2026-06-30" + X.FILE_SUFFIX_OF[k]) for k in KINDS)


# ======================================================================== 4. 別の process
def spawn(cmd, cwd):
    p = subprocess.run(list(cmd), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
    return p.returncode, p.stderr.decode("utf-8", "replace")


class ScriptCopy(object):
    u"""``src`` を使い捨ての場所の measure/ に置き(前の便の script は symlink)、``python3 -I`` で走らせる入れ物。"""

    def __init__(self, d, src):
        mdir = os.path.join(d, "measure")
        os.makedirs(mdir)
        for fn in SIBLINGS:
            os.symlink(os.path.join(ROOT, "measure", fn), os.path.join(mdir, fn))
        for dn in ("core", "adapters"):                     # 便 XG0 の script が import だけする(呼ばない)。使い捨ての場所の根に置く
            os.symlink(os.path.join(ROOT, dn), os.path.join(d, dn))
        self.path = os.path.join(mdir, "xbrl_pack_build_copy.py")
        with io.open(self.path, "w", encoding="utf-8") as fh:
            fh.write(src)

    def run(self, args, cwd):
        return spawn([sys.executable, "-I", self.path] + list(args), cwd)


def proc_problems(src=None):
    u"""本物の process(``python3 -I``)で組む命令を走らせる。"""
    src = src if src is not None else read(SCRIPT_REL)
    out_ = []
    with Temp() as d:
        sc = ScriptCopy(d, src)
        cwd = os.path.join(d, "cwd")
        os.makedirs(cwd)
        write_file(os.path.join(cwd, "index.json"), b"{poison")
        _zp, folder, index, ent = peeled(os.path.join(d, "w") if os.makedirs(os.path.join(d, "w")) is None else d)
        want = MS.same_process_tree(*MS.peel_tables(ent))
        o1 = os.path.join(d, "o1")
        rc, err = sc.run(["build", folder, o1], cwd)
        if rc != 0 or not os.path.isdir(o1) or tree_of(o1) != want:
            out_.append(u"本物の process の組む命令の出す folder が同じ process の字と違う: rc=%s %s" % (rc, err[-200:]))
        o2 = os.path.join(d, "o2")
        rc, err = sc.run(["build", folder, o2], cwd)
        if rc != 0 or tree_of(o2) != tree_of(o1):
            out_.append(u"組む命令を 2 度走らせると違う字を書く")
        for args in (["build"], ["build", folder], ["build", folder, os.path.join(d, "o3"), "x"]):
            rc, err = sc.run(args, cwd)
            if rc != 64 or os.path.exists(os.path.join(d, "o3")):
                out_.append(u"本物の process: 引数が 2 つでないとき 64 で終わらない: %d 個 → %s" % (len(args) - 1, rc))
        fd = os.path.join(d, "bad")
        shutil.copytree(folder, fd)
        tp = os.path.join(fd, "taxonomy.json")
        t = MS.jload(read_file(tp))
        t["tables"]["xsd"]["elements"][0]["zzz"] = "1"
        write_file(tp, MS.jdump(t))
        rc, err = sc.run(["build", fd, os.path.join(d, "o4")], cwd)
        if rc != 2 or u"DECLINE: 知らない属性" not in err.splitlines() or os.path.exists(os.path.join(d, "o4")):
            out_.append(u"本物の process: 知らない形で 2 と理由の行を出さない: rc=%s %r" % (rc, err[-200:]))
        os.makedirs(os.path.join(d, "o5"))
        rc, err = sc.run(["build", folder, os.path.join(d, "o5")], cwd)
        if rc != 1 or u"DECLINE: " in err:
            out_.append(u"本物の process: 例外で 1 を出さない: %s" % rc)
        rc, err = sc.run(["peel", _zp, os.path.join(d, "o6")], cwd)
        if rc != 0 or sorted(os.listdir(os.path.join(d, "o6"))) != HAND_FILES:
            out_.append(u"本物の process: peel が folder を作らない: %s" % rc)
    return out_


def command_problems(ms=None):
    ms = ms or MS
    out_ = []
    if ms.SCRIPT_PATH != os.path.join(ROOT, SCRIPT_REL) or not os.path.isabs(ms.SCRIPT_PATH):
        out_.append(u"組む命令の script の場所が違う")
    cmd = ms.build_command(u"/f", u"/o")
    if cmd != [sys.executable, u"-I", ms.SCRIPT_PATH, u"build", u"/f", u"/o"] or len(cmd) != 6:
        out_.append(u"組む命令の引数が [python, -I, script, build, folder, folder] でない: %s" % cmd)
    log = []

    def fake(rc, err=u"", to=False):
        def proc(c, cwd, timeout):
            log.append((list(c), cwd, timeout))
            return rc, err, to
        return proc
    r = ms.exec_build(u"/f", u"/o", u"/w", fake(0))
    if r[0] is not True or r[1] != u"" or r[2] < 0 or log[-1] != (cmd[:4] + [u"/f", u"/o"], u"/w", 600):
        out_.append(u"成功の返り値・渡した引数・cwd・時間の上限が違う: %s %s" % (r, log[-1]))
    r = ms.exec_build(u"/f", u"/o", u"/w", fake(2, u"junk\nDECLINE: 知らない属性\n"))
    if r[:2] != (False, u"知らない属性"):
        out_.append(u"断り(終わりの値 2)の理由を読めない: %s" % (r,))
    r = ms.exec_build(u"/f", u"/o", u"/w", fake(1, u"ERROR\n"))
    if r[0] is not False or not r[1] or u"DECLINE" in r[1]:
        out_.append(u"例外(終わりの値 1)の返り値が違う: %s" % (r,))
    r = ms.exec_build(u"/f", u"/o", u"/w", fake(64, u"使い方\n"))
    if r[0] is not False:
        out_.append(u"終わりの値 64 を失敗に数えない")
    r = ms.exec_build(u"/f", u"/o", u"/w", fake(None, u"", True))
    if r[0] is not False or u"時間の上限" not in r[1]:
        out_.append(u"時間の上限を超えたとき失敗に数えない: %s" % (r,))
    r = ms.exec_build(u"/f", u"/o", u"/w", fake(0, u"DECLINE: x\n"))
    if r[0] is not True:
        out_.append(u"終わりの値が 0 なのに失敗に数える")
    if ms.decline_reason(u"a\nDECLINE: 理由\nb") != u"理由" or ms.decline_reason(u"a\nb") is not None or ms.decline_reason(u"x DECLINE: y") is not None or len(ms.decline_reason(u"DECLINE: " + u"あ" * 200)) != ms.REASON_MAX or ms.REASON_MAX != 80:
        out_.append(u"理由の行の読み方が違う")
    # 本物の呼び出しの引数(subprocess.run の呼び方)
    seen = {}

    def fake_run(c, **kw):
        seen["cmd"], seen["kw"] = list(c), kw
        return types.SimpleNamespace(returncode=3, stderr=u"エラー".encode("utf-8"))
    real = ms.subprocess.run
    ms.subprocess.run = fake_run
    try:
        rr = ms.run_process([u"a", u"b"], u"/cwd", 7)
    finally:
        ms.subprocess.run = real
    kw = seen.get("kw", {})
    if rr != (3, u"エラー", False) or seen.get("cmd") != [u"a", u"b"] or kw.get("cwd") != u"/cwd" or kw.get("timeout") != 7 or kw.get("shell") is not False or kw.get("stdout") != subprocess.PIPE or kw.get("stderr") != subprocess.PIPE:
        out_.append(u"run_process の呼び方が違う(shell を通す・cwd・時間の上限・出力の受け取り): %s" % kw)

    def timeout_run(c, **kw):
        raise subprocess.TimeoutExpired(c, 1)
    ms.subprocess.run = timeout_run
    try:
        rr = ms.run_process([u"a"], u"/c", 1)
    finally:
        ms.subprocess.run = real
    if rr != (None, u"", True):
        out_.append(u"時間の上限の超えを返さない")
    return out_


# ======================================================================== 5. 混ぜ物
def mix_run(ms, htms=None, n=0, tables=None):
    u"""folder を作って混ぜ物 ``n`` を掛ける。(変えたか, 変える前の folder の中身, 変えた後の folder の中身, 目次)。"""
    with Temp() as d:
        _zp, folder, index, _ent = peeled(d, ms, **({"htms": htms} if htms is not None else {}))
        before = tree_of(folder)
        ok = ms.change_folder(folder, n)
        return ok, before, tree_of(folder), index


def diff_files(before, after):
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))


def mix_problems(ms=None):
    ms = ms or MS
    out_ = []
    # N1: 0 だけの字を飛ばし、最初の 0 だけでない nonFraction の最初の 1〜9 を 1 つ大きくする(file の名の昇順・表 F の順)
    ok, before, after, index = mix_run(ms, n=0)
    if not ok or diff_files(before, after) != [u"t0001.txt"]:
        out_.append(u"N1: 変える file が b の素の本文 1 つだけでない: %s" % diff_files(before, after))
    else:
        a, c = before[u"t0001.txt"].decode("utf-8"), after[u"t0001.txt"].decode("utf-8")
        i = a.index(u"1,234")
        if c != a[:i] + u"2,234" + a[i + 5:]:
            out_.append(u"N1: 変え方が「0 を飛ばした最初の nonFraction の最初の 1〜9 を 1 つ大きく」でない")
    for content, want in ((u"9,5", u"1,5"), (u"08", u"09"), (u"1234", u"2234")):
        ok, before, after, _i = mix_run(ms, htms=[(HTM_A_NAME, htm_one(content))], n=0)
        if not ok or diff_files(before, after) != [u"t0000.txt"] or after[u"t0000.txt"].decode("utf-8").count(want) != 1 or before[u"t0000.txt"].decode("utf-8").count(content) != 1 or want not in after[u"t0000.txt"].decode("utf-8"):
            out_.append(u"N1: %s → %s にならない" % (content, want))
    ok, before, after, _i = mix_run(ms, htms=[(HTM_A_NAME, htm_one(u"0")), (HTM_B_NAME, htm_one(u"00", u"jppfs_cor:Two"))], n=0)
    if ok or before != after:
        out_.append(u"N1: 0 だけの字しか無いとき作れなかったにならない(か folder を変えた)")
    ok, before, after, _i = mix_run(ms, htms=[(HTM_A_NAME, htm_one(u"―"))], n=0)
    if ok or before != after:
        out_.append(u"N1: 数字の無い字しか無いとき作れなかったにならない")
    ok, before, after, _i = mix_run(ms, htms=[(HTM_A_NAME, HTM_A)], n=0)
    if ok or before != after:
        out_.append(u"N1: nonFraction が無いとき作れなかったにならない")
    # N2: 表 F の最初の nonFraction の行を除く(file の名の昇順・読み戻した表に XB0 の関数を掛けて書き戻す)
    ok, before, after, index = mix_run(ms, n=1)
    if not ok or diff_files(before, after) != [u"t0001.json"]:
        out_.append(u"N2: 変える file が b の表 1 つだけでない: %s" % diff_files(before, after))
    else:
        fb, fa = MS.jload(before[u"t0001.json"])["F"], MS.jload(after[u"t0001.json"])["F"]
        if len(fa) != len(fb) - 1 or [e["attrs"]["name"] for e in fb] != [u"jppfs_cor:Zero", u"jppfs_cor:Assets"] or [e["attrs"]["name"] for e in fa] != [u"jppfs_cor:Assets"]:
            out_.append(u"N2: 最初の nonFraction の行を 1 つだけ除いていない")
        if before[u"t0001.txt"] != after[u"t0001.txt"]:
            out_.append(u"N2: 素の本文を変えた")
    ok, before, after, _i = mix_run(ms, htms=[(HTM_A_NAME, HTM_A)], n=1)
    if ok or before != after:
        out_.append(u"N2: nonFraction が無いとき作れなかったにならない")
    # N3: 日本語のラベルの表の順で最初のラベルの字の後ろに X(読み戻した表に XT0 の関数を掛けて書き戻す)
    ok, before, after, _i = mix_run(ms, n=2)
    if not ok or diff_files(before, after) != [u"taxonomy.json"]:
        out_.append(u"N3: 変える file がタクソノミの表 1 つだけでない: %s" % diff_files(before, after))
    else:
        tb, ta = MS.jload(before[u"taxonomy.json"])["tables"], MS.jload(after[u"taxonomy.json"])["tables"]
        first = [e for L in tb["lab"]["links"] for e in L["ends"] if e["kind"] == "label"][0]
        first_a = [e for L in ta["lab"]["links"] for e in L["ends"] if e["kind"] == "label"][0]
        if first_a["text"] != first["text"] + u"X" or first["text"] != X.TXT1:
            out_.append(u"N3: 日本語のラベル(lab)の最初のラベルの後ろに X を足していない: %r" % first_a["text"])
        for k in KINDS:
            if k != "lab" and tb[k] != ta[k]:
                out_.append(u"N3: lab のほかの表(%s)を変えた" % k)
    # N4: 最初の arc の weight を返す(計算)
    ok, before, after, _i = mix_run(ms, n=3)
    if not ok or diff_files(before, after) != [u"taxonomy.json"]:
        out_.append(u"N4: 変える file がタクソノミの表 1 つだけでない: %s" % diff_files(before, after))
    else:
        tb, ta = MS.jload(before[u"taxonomy.json"])["tables"], MS.jload(after[u"taxonomy.json"])["tables"]
        arc_b, arc_a = tb["cal"]["links"][0]["arcs"][0], ta["cal"]["links"][0]["arcs"][0]
        if arc_b["attrs"]["weight"] != u"1" or arc_a["attrs"]["weight"] != u"-1":
            out_.append(u"N4: 最初の arc の weight(1)を -1 にしていない")
        for k in KINDS:
            if k != "cal" and tb[k] != ta[k]:
                out_.append(u"N4: cal のほかの表(%s)を変えた" % k)
    return out_


# ======================================================================== 6. 書類 1 本
def doc_run(ms, d, no=1, mixtures=True, proc=None, runner_cls=None, **kw):
    docs = os.path.join(d, "docs")
    os.makedirs(docs, exist_ok=True)
    zp = os.path.join(docs, "S2FAKE0%d.zip" % no)
    make_pack(zp, no, **kw)
    tool, mv = X.make_tool(d)
    tmp = os.path.join(d, "tmp")
    os.makedirs(tmp, exist_ok=True)
    r = (runner_cls or PackRunner)(mv)
    proc = proc or InProc(ms)
    rec = ms.process_doc(tool, zp, tmp, r, mixtures=mixtures, proc=proc)
    return rec, r, proc, zp, tmp


def blob(call, name):
    return call["blobs"].get(name)


def doc_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        rec, r, proc, zp, tmp = doc_run(ms, d)
        before = read_bytes_sha(zp)
        ent = entries_of(zp, ms)
        files, names, tables = ms.peel_tables(ent)
        want_tree = ms.same_process_tree(files, names, tables)
        # 道具の呼び出し: 元 A・B・組み直し A・B・混ぜ物 4 つ × (A・B) = 12 回
        if len(r.calls) != 12:
            out_.append(u"道具の呼び出しが 12 回でない: %d" % len(r.calls))
        else:
            for i in range(0, 12, 2):
                ca, cb = r.calls[i], r.calls[i + 1]
                if u"--validate" not in ca["cmd"] or u"--validate" in cb["cmd"] or u"--viewArcrole" not in cb["cmd"] or ca["zip"] != cb["zip"]:
                    out_.append(u"呼び出しの対(A・B)が違う: %d" % i)
                    break
            if any(c["timeout"] != 600 for c in r.calls) or any(not c["existed"] for c in r.calls):
                out_.append(u"時間の上限・zip が無い")
            if any(c["raw"][:2] != X.SEED or c["raw"][2:] != c["cmd"] for c in r.calls):
                out_.append(u"道具の呼び出しの前に /usr/bin/env PYTHONHASHSEED=0 を付けていない")
            if [os.path.basename(c["zip"]) for c in r.calls[:4]] != ["orig.zip", "orig.zip", "new.zip", "new.zip"] or [os.path.basename(c["zip"]) for c in r.calls[4::2]] != ["mix0.zip", "mix1.zip", "mix2.zip", "mix3.zip"]:
                out_.append(u"包みの名・順が違う")
            for c in r.calls:
                bl = c["blobs"]
                if any(n.endswith(".xbrl") for n in c["names"]) or bl["XBRL/AuditDoc/audit.xml"] != b"<a/>" or bl["XBRL/PublicDoc/manifest_PublicDoc.xml"] != b"<manifest/>" or bl["XBRL/PublicDoc/logo.png"] != b"PNG-not-an-image":
                    out_.append(u"掛けた包みの中身が違う(.xbrl が残る・マニフェスト・画像・AuditDoc が変わった)")
                    break
            o, n = r.calls[0]["blobs"], r.calls[2]["blobs"]
            texts = pack_texts(1)
            for k in KINDS:
                nm = STEM1 + X.FILE_SUFFIX_OF[k]
                if o[nm].decode("utf-8") != texts[k]:
                    out_.append(u"元の包みの %s が元の字でない" % k)
            for rel, data in want_tree.items():
                if n[ms.PUBLICDOC + rel] != data:
                    out_.append(u"組み直した包みの file が組む命令の出した字でない(比べる相手が同じ file になっている): %s" % rel[:12])
            for nm in o:
                if nm.startswith("XBRL/PublicDoc/") and nm.endswith(".htm") and n[nm] == o[nm] and False:
                    pass
            if len([nm for nm in o if o[nm] != n[nm]]) < 3:
                out_.append(u"元の包みと組み直した包みの file がほとんど同じ(比べ方が効かない)")
            if n[STEM1 + "_lab-en.xml"] != X.b(X.CANON_TEXTS["lab-en"]) or n[STEM1 + ".xsd"].decode("utf-8") != X.XSD_CANON:
                out_.append(u"組み直した包みのタクソノミが便 XT0 の組む字でない")
            if set(n) != set(o):
                out_.append(u"組み直した包みの file の集まりが元と違う")
        if rec[u"断った"] or rec[u"断った理由"] != u"":
            out_.append(u"断らない書類を断った: %s" % rec[u"断った理由"])
        if dict(rec[u"元の書き出しの行の数"]) != dict(X.HAND_ROWS) or dict(rec[u"組み直しの書き出しの行の数"]) != dict(X.HAND_ROWS):
            out_.append(u"書き出しの行の数が手で数えた値と違う")
        if rec[u"元の fact の行の数"] != 4 or rec[u"組み直しの fact の行の数"] != 4:
            out_.append(u"fact の行の数が違う(手で数えた値は 4): %s %s" % (rec[u"元の fact の行の数"], rec[u"組み直しの fact の行の数"]))
        if not all(rec[u"書き出しが同じ"].values()) or list(rec[u"書き出しが同じ"]) != list(ms.OUTPUT_KEYS) or not (rec[u"タクソノミが同じ"] and rec[u"fact が同じ"] and rec[u"鳴り方が同じ"] and rec[u"全部同じ"]):
            out_.append(u"組み直しで書き出し・fact・鳴り方が同じにならない")
        if rec[u"2 度が同じ"] is not True or rec[u"道筋が同じ"] is not True:
            out_.append(u"2 度・道筋が同じにならない")
        if rec[u"元の 1 回"][u"符号ごとの行"] != {u"EDINET.EC5611W": 1} or rec[u"元の 1 回"][u"類"] != u"走った" or rec[u"組み直しの 1 回"] != rec[u"元の 1 回"]:
            out_.append(u"元の 1 回の数が違う")
        # 原稿の folder と元の包みの bytes
        with Temp() as d2:
            _zp2, f2, idx2, _e2 = peeled(d2, ms)
            sizes = dict((n, os.path.getsize(os.path.join(f2, n))) for n in os.listdir(f2))
        fo = rec[u"原稿の folder"]
        want_fo = {u"素の本文": (3, sum(sizes[u"t000%d.txt" % i] for i in range(3))), u"本文の表": (3, sum(sizes[u"t000%d.json" % i] for i in range(3))), u"タクソノミの表": (1, sizes[u"taxonomy.json"]), u"目次": (1, sizes[u"index.json"])}
        got_fo = dict((k, (fo[k][u"file"], fo[k][u"bytes"])) for k in ms.FOLDER_GROUPS)
        if got_fo != want_fo or fo[u"合計 bytes"] != sum(sizes.values()) or list(fo) != list(ms.FOLDER_GROUPS) + [u"合計 bytes"]:
            out_.append(u"原稿の folder の file の数・bytes が手で数えた値と違う: %s" % json.dumps(fo, ensure_ascii=False))
        ob = rec[u"元の包みの bytes"]
        want_htm = sum(len(t.encode("utf-8")) for t in (HTM_A, HTM_B, HTM_SUB))
        want_tax = sum(len(v.encode("utf-8")) for v in pack_texts(1).values())
        if (ob[u"htm"][u"file"], ob[u"htm"][u"bytes"], ob[u"タクソノミ"][u"file"], ob[u"タクソノミ"][u"bytes"], ob[u"合計 bytes"]) != (3, want_htm, 6, want_tax, want_htm + want_tax):
            out_.append(u"元の包みの bytes が手で数えた値と違う(PublicDoc の htm と xsd・linkbase だけ数える): %s" % json.dumps(ob, ensure_ascii=False))
        if rec[u"原稿が元より大きい"] != (fo[u"合計 bytes"] > ob[u"合計 bytes"]):
            out_.append(u"原稿が元より大きいの導き方が違う")
        if not isinstance(rec[u"組む命令の秒"], float) or rec[u"組む命令の秒"] < 0 or rec[u"組む命令の秒"] != round(rec[u"組む命令の秒"], 1):
            out_.append(u"組む命令の秒が小数 1 桁の数でない: %r" % rec[u"組む命令の秒"])
        # 組む命令の呼び方(1 回目・2 回目・混ぜ物 4 つの 6 回)
        if len(proc.calls) != 6:
            out_.append(u"組む命令の呼び出しが 6 回でない(1 回目・2 回目・混ぜ物 4 つ): %d" % len(proc.calls))
        else:
            for k, c in enumerate(proc.calls):
                cmd = c["cmd"]
                if cmd[:4] != [sys.executable, "-I", ms.SCRIPT_PATH, "build"] or len(cmd) != 6 or c["timeout"] != 600:
                    out_.append(u"組む命令の引数・時間の上限が違う: %s" % cmd)
                    break
                if c["listing"] != [] or c["cwd"] == c["folder"] or os.path.dirname(c["cwd"]) != os.path.dirname(c["folder"]) or os.path.dirname(c["out"]) != os.path.dirname(c["cwd"]):
                    out_.append(u"組む命令の cwd が元の包みを置いていない空の作業の folder でない: %s" % c["listing"])
                    break
            if proc.calls[0]["folder"] != proc.calls[1]["folder"] or proc.calls[0]["out"] == proc.calls[1]["out"] or len(set(c["out"] for c in proc.calls)) != 6:
                out_.append(u"組む命令の folder・出す folder の使い方が違う(2 度は同じ原稿に別の出す folder)")
            if len(set(c["folder"] for c in proc.calls)) != 5 or [os.path.basename(c["folder"]) for c in proc.calls[2:]] != [u"mixf0", u"mixf1", u"mixf2", u"mixf3"]:
                out_.append(u"混ぜ物の組む命令が混ぜ物の folder に掛かっていない")
            ff = proc.calls[0]["folder_files"]
            if sorted(ff) != HAND_FILES:
                out_.append(u"組む命令に渡った folder の file が違う: %s" % sorted(ff))
            every = b"".join(ff.values())
            for info, data in ent:
                if info.filename.startswith("XBRL/PublicDoc/") and info.filename.endswith((".htm", ".xsd", ".xml")) and data in every:
                    out_.append(u"組む命令に渡った folder に元の file の字が在る")
                    break
            if any(raw == data for raw in ff.values() for _i, data in ent):
                out_.append(u"組む命令に渡った folder の file が元の file と同じ bytes")
        # 混ぜ物 4 つ: 変えた file だけが組み直した包みと違う・全部で違いを見つける・鳴り方が違うのは N4 だけ
        got = [(m[u"種類"], m[u"作った"], m[u"違いを見つけた"], m[u"鳴り方が違う"]) for m in rec[u"混ぜ物"]]
        want = [(k, True, True, i == 3) for i, k in enumerate(ms.MIX_KINDS)]
        if got != want:
            out_.append(u"混ぜ物 4 つの結果が手で決めた値と違う: %s" % got)
        if len(r.calls) == 12:
            newc = r.calls[2]["blobs"]
            wants = [[HTM_B_NAME], [HTM_B_NAME], [STEM1 + "_lab.xml"], [STEM1 + "_cal.xml"]]
            for i, w in enumerate(wants):
                bl = r.calls[4 + 2 * i]["blobs"]
                diff = sorted(k for k in bl if k in newc and bl[k] != newc[k])
                if diff != sorted(w):
                    out_.append(u"混ぜ物 %d の包みが組み直した包みと違うのは変えた file だけであるはず: %s" % (i + 1, diff))
        if read_bytes_sha(zp) != before:
            out_.append(u"置き場の zip が変わった")
        if os.listdir(tmp):
            out_.append(u"使い捨ての場所が残っている")
        # 既定の runner は V.exec_cmd・既定の proc は run_process(作り物に差し替えて呼ばれることを見る)
        tool, mv = X.make_tool(os.path.join(d, "t2"))
        fake_default = PackRunner(mv)
        saved = ms.V.exec_cmd
        ms.V.exec_cmd = fake_default
        saved_proc = ms.run_process
        got_proc = []
        ms.run_process = lambda c, cwd, t: (got_proc.append(c), (InProc(ms)(c, cwd, t)))[1]
        try:
            ms.process_doc(tool, zp, tmp, None, mixtures=False)
        finally:
            ms.V.exec_cmd = saved
            ms.run_process = saved_proc
        if len(fake_default.calls) != 4 or len(got_proc) != 2:
            out_.append(u"既定の runner が V.exec_cmd でない・既定の proc が run_process でない: %d %d" % (len(fake_default.calls), len(got_proc)))
        # 混ぜ物を作らない呼び方
        r2 = PackRunner(mv)
        rec2 = ms.process_doc(tool, zp, tmp, r2, mixtures=False, proc=InProc(ms))
        if len(r2.calls) != 4 or rec2[u"混ぜ物"] != []:
            out_.append(u"混ぜ物を作らない呼び方で 4 回でない")
        # zip の並びによらない
        zr = os.path.join(d, "docs", "S2REV.zip")
        make_pack(zr, 1, shuffle=True)
        rec3 = ms.process_doc(tool, zr, tmp, PackRunner(mv), mixtures=False, proc=InProc(ms))
        if not rec3[u"全部同じ"] or not rec3[u"2 度が同じ"] or not rec3[u"道筋が同じ"]:
            out_.append(u"zip の並びが違うと結果が変わる")
        # 道具が落ちても使い捨ての場所は残らない
        try:
            ms.process_doc(tool, zp, tmp, PackRunner(mv, crash_on=3), mixtures=False, proc=InProc(ms))
        except RuntimeError:
            pass
        if os.listdir(tmp):
            out_.append(u"途中で落ちたとき使い捨ての場所が残る")
    return out_


def decline_doc_problems(ms=None):
    u"""断る書類・組む命令の失敗・出力の食い違い・混ぜ物の作れなかった・道具の答えが変わる書類。"""
    ms = ms or MS
    out_ = []

    def declined_ok(rec, reason, what, folder_zero=False, facts=4):
        if not rec[u"断った"] or rec[u"断った理由"] != reason:
            out_.append(u"%s: 断った・理由が違う: %s %s" % (what, rec[u"断った"], rec[u"断った理由"]))
            return
        if rec[u"組み直しの 1 回"] is not None or rec[u"fact が同じ"] or rec[u"鳴り方が同じ"] or rec[u"全部同じ"] or rec[u"タクソノミが同じ"] or rec[u"2 度が同じ"] or rec[u"道筋が同じ"] or any(rec[u"書き出しが同じ"].values()):
            out_.append(u"%s: 断った書類に同じ・道筋・2 度が付く" % what)
        if [m[u"作った"] for m in rec[u"混ぜ物"]] != [False] * 4 or any(m[u"違いを見つけた"] or m[u"鳴り方が違う"] for m in rec[u"混ぜ物"]):
            out_.append(u"%s: 断った書類の混ぜ物の数え方が違う" % what)
        if rec[u"元の書き出しの行の数"][u"概念"] != 4 or rec[u"元の fact の行の数"] != facts or rec[u"組み直しの書き出しの行の数"] is not None:
            out_.append(u"%s: 断った書類でも元の書き出しの行・fact の行の数を数える" % what)
        if folder_zero != (rec[u"原稿の folder"][u"合計 bytes"] == 0) or (folder_zero and rec[u"組む命令の秒"] is not None) or (not folder_zero and rec[u"組む命令の秒"] is None):
            out_.append(u"%s: 原稿の folder の bytes・組む命令の秒が違う" % what)
        if rec[u"元の包みの bytes"][u"合計 bytes"] <= 0 or rec[u"原稿が元より大きい"] != (rec[u"原稿の folder"][u"合計 bytes"] > rec[u"元の包みの bytes"][u"合計 bytes"]):
            out_.append(u"%s: 元の包みの bytes・原稿が元より大きいが違う" % what)
    # 落とす側の断り: タクソノミ・本文
    with Temp() as d:
        rec, r, proc, zp, tmp = doc_run(ms, d, declined=True)
        declined_ok(rec, u"知らない属性", u"タクソノミの知らない形", folder_zero=True)
        if len(r.calls) != 2 or proc.calls:
            out_.append(u"落とす側で断ったのに組み直した包みを掛けた・組む命令を呼んだ")
    with Temp() as d:
        rec, r, proc, zp, tmp = doc_run(ms, d, htms=[(HTM_A_NAME, u"<html><ix:zzz>x</ix:zzz></html>")])
        declined_ok(rec, u"知らない ix の要素", u"本文の知らない形", folder_zero=True, facts=0)
    # 組む命令が失敗する(2・1・時間の上限)
    for what, ret, reason in ((u"組む命令の断り", (2, u"DECLINE: 固定の理由\n", False), u"固定の理由"), (u"組む命令の例外", (1, u"ERROR\n", False), u"組む命令が 0 でない終わりの値で終わった"), (u"組む命令の時間の上限", (None, u"", True), u"組む命令が時間の上限を超えた")):
        with Temp() as d:
            rec, r, proc, zp, tmp = doc_run(ms, d, proc=lambda c, cwd, t, ret=ret: ret)
            declined_ok(rec, reason, what)
            if len(r.calls) != 2:
                out_.append(u"%s: 断ったのに組み直した包みを掛けた" % what)
            if os.listdir(tmp):
                out_.append(u"%s: 使い捨ての場所が残る" % what)

    # 出す folder の file の名が目次と合わない(足りない・多い)
    def drop_one(c, cwd, t):
        p = InProc(ms)(c, cwd, t)
        os.remove(os.path.join(c[-1], "0100000_a_E99991-000_ixbrl.htm"))
        return p

    def add_one(c, cwd, t):
        p = InProc(ms)(c, cwd, t)
        write_file(os.path.join(c[-1], "extra.htm"), b"x")
        return p
    for what, fn in ((u"出す folder の file が足りない", drop_one), (u"出す folder に目次に無い file が在る", add_one)):
        with Temp() as d:
            rec, r, proc, zp, tmp = doc_run(ms, d, proc=fn)
            declined_ok(rec, u"出す folder の file の名が目次と合わない", what)
    # 2 回目の出力が違う・2 回目が失敗する → 断らず 2 度が同じ だけ偽
    for what, proc in ((u"2 回目の出力が違う", InProc(ms, mangle=mangle_second)), (u"2 回目の組む命令が失敗する", InProc(ms, rc_after_first=(1, u"ERROR\n", False)))):
        with Temp() as d:
            rec, r, p, zp, tmp = doc_run(ms, d, mixtures=False, proc=proc)
            if rec[u"断った"] or rec[u"2 度が同じ"] or not rec[u"道筋が同じ"] or not rec[u"全部同じ"]:
                out_.append(u"%s: 断った・2 度が同じ・道筋・全部同じの数え方が違う" % what)
    # 組む命令の出力が同じ process の字と違う(1 回目だけ違う) → 道筋が同じ だけ偽(組み直した包みは違う字なので比べも効く)
    with Temp() as d:
        rec, r, p, zp, tmp = doc_run(ms, d, mixtures=False, proc=InProc(ms, mangle=mangle_first))
        if rec[u"道筋が同じ"] or rec[u"2 度が同じ"] or rec[u"断った"]:
            out_.append(u"組む命令の出力が同じ process の字と違うのに道筋が同じ・2 度が同じ(か断った)")
    # 混ぜ物の作れなかった: 当て先が無い・混ぜ物の組む命令が失敗する
    with Temp() as d:
        rec, r, p, zp, tmp = doc_run(ms, d, htms=[(HTM_A_NAME, HTM_A)])
        got = [(m[u"作った"], m[u"違いを見つけた"], m[u"鳴り方が違う"]) for m in rec[u"混ぜ物"]]
        if got != [(False, False, False), (False, False, False), (True, True, False), (True, True, True)] or len(r.calls) != 4 + 4:
            out_.append(u"nonFraction が無い書類の混ぜ物(N1・N2 は作れなかった・N3・N4 は作れた)が違う: %s・道具 %d 回" % (got, len(r.calls)))

    class FailMix(InProc):
        def __call__(self, cmd, cwd, timeout):
            if len(self.calls) >= 2:
                self.calls.append(dict(cmd=list(cmd)))
                return 2, u"DECLINE: 固定の理由\n", False
            return InProc.__call__(self, cmd, cwd, timeout)
    with Temp() as d:
        rec, r, p, zp, tmp = doc_run(ms, d, proc=FailMix(ms))
        if rec[u"断った"] or [m[u"作った"] for m in rec[u"混ぜ物"]] != [False] * 4 or len(r.calls) != 4:
            out_.append(u"混ぜ物の組む命令が失敗したとき作れなかったにならない(か書類を断った・道具を掛けた)")

    class MixMismatch(InProc):
        def __call__(self, cmd, cwd, timeout):
            res = InProc.__call__(self, cmd, cwd, timeout)
            if len(self.calls) >= 3 and res[0] == 0:
                os.remove(os.path.join(cmd[-1], "0100000_a_E99991-000_ixbrl.htm"))
            return res
    with Temp() as d:
        rec, r, p, zp, tmp = doc_run(ms, d, proc=MixMismatch(ms))
        if rec[u"断った"] or [m[u"作った"] for m in rec[u"混ぜ物"]] != [False] * 4 or len(r.calls) != 4:
            out_.append(u"混ぜ物の出す folder の file が目次と合わないとき作れなかったにならない")
    # 混ぜ物を作る途中の例外 → 作れなかった(書類は断らない)
    with Temp() as d:
        real_change = ms.change_folder
        ms.change_folder = lambda *a, **k: (_ for _ in ()).throw(ValueError("x"))
        try:
            rec, r, p, zp, tmp = doc_run(ms, d)
        finally:
            ms.change_folder = real_change
        if rec[u"断った"] or [m[u"作った"] for m in rec[u"混ぜ物"]] != [False] * 4 or len(r.calls) != 4:
            out_.append(u"混ぜ物を作る途中の例外を作れなかったに数えない(か書類を断った)")
    # 書類 1 本の中の例外
    with Temp() as d:
        zp = os.path.join(d, "p.zip")
        make_pack(zp)
        tool, mv = X.make_tool(d)
        orig = ms.write_folder
        ms.write_folder = lambda *a, **k: (_ for _ in ()).throw(ValueError("x"))
        try:
            rec = ms.process_doc(tool, zp, d, PackRunner(mv), mixtures=True, proc=InProc(ms))
        finally:
            ms.write_folder = orig
        declined_ok(rec, u"folder に書けない形", u"folder に書く途中の例外", folder_zero=True)
    # 道具の答えが書き出し 1 つだけ変わる・fact が変わる・指摘の行が変わる(組み直した包みだけ)
    class Tamper(PackRunner):
        def __init__(self, mv, what):
            PackRunner.__init__(self, mv)
            self.what = what

        def __call__(self, cmd, timeout):
            res = PackRunner.__call__(self, cmd, timeout)
            c = X.strip_seed(cmd)
            if os.path.basename(c[0]) != "arelleCmdLine" or os.path.basename(self.calls[-1]["zip"]) != "new.zip":
                return res
            if self.what == "row" and "--cal" in c:
                with io.open(c[c.index("--cal") + 1], "a", encoding="utf-8", newline="") as fh:
                    fh.write(u"extra\r\n")
            if self.what == "fact" and "--facts" in c:
                with io.open(c[c.index("--facts") + 1], "a", encoding="utf-8", newline="") as fh:
                    fh.write(u"zzz,9\r\n")
            if self.what == "sound" and "--validate" in c:
                return res[0] + u"[EDINET.EC5611W] 追加\n", res[1]
            return res
    for what, check in (("row", lambda x: (not x[u"タクソノミが同じ"], x[u"書き出しが同じ"][u"計算"] is False, x[u"fact が同じ"], x[u"鳴り方が同じ"], not x[u"全部同じ"])),
                        ("fact", lambda x: (x[u"タクソノミが同じ"], not x[u"fact が同じ"], x[u"鳴り方が同じ"], not x[u"全部同じ"], True)),
                        ("sound", lambda x: (x[u"タクソノミが同じ"], x[u"fact が同じ"], not x[u"鳴り方が同じ"], x[u"全部同じ"], True))):
        with Temp() as d:
            tool, mv = X.make_tool(d)
            zp = os.path.join(d, "p.zip")
            make_pack(zp)
            rec = ms.process_doc(tool, zp, d, Tamper(mv, what), mixtures=False, proc=InProc(ms))
            if not all(check(rec)) or rec[u"断った"]:
                out_.append(u"組み直した包みだけ道具の答えが変わるとき比べが効かない: %s" % what)
            if what == "sound" and (rec[u"組み直しの 1 回"][u"符号ごとの行"] != {u"EDINET.EC5611W": 2} or rec[u"元の 1 回"][u"符号ごとの行"] != {u"EDINET.EC5611W": 1}):
                out_.append(u"組み直しの 1 回が組み直した包みの数でない: %s" % dict(rec[u"組み直しの 1 回"][u"符号ごとの行"]))
    return out_


# ======================================================================== 7. 数える
def ent(declined=False, same=None, facts=True, sound=True, cls=u"走った", mixes=(), rows=None, twice=True, path=True, folder=1000, orig=2000, secs=1.5, reason=u"組む命令の断り"):
    same = same if same is not None else [True] * 7
    keys = MS.OUTPUT_KEYS
    ss = od((k, (False if declined else same[i])) for i, k in enumerate(keys))
    tax = all(ss.values())
    rows = rows or [4] * 7
    fo = od((g, od([(u"file", 1 if folder else 0), (u"bytes", folder // 4)])) for g in MS.FOLDER_GROUPS)
    fo[u"合計 bytes"] = sum(v[u"bytes"] for v in fo.values())
    ob = od([(u"htm", od([(u"file", 2), (u"bytes", orig // 2)])), (u"タクソノミ", od([(u"file", 6), (u"bytes", orig // 2)])), (u"合計 bytes", orig // 2 * 2)])
    return od([(u"断った", declined), (u"断った理由", reason if declined else u""), (u"元の書き出しの行の数", od((k, rows[i]) for i, k in enumerate(keys))), (u"元の fact の行の数", 5),
               (u"元の 1 回", od([(u"類", u"走った"), (u"符号ごとの行", {})])), (u"元の包みの bytes", ob), (u"原稿の folder", fo), (u"原稿が元より大きい", fo[u"合計 bytes"] > ob[u"合計 bytes"]),
               (u"組む命令の秒", secs), (u"書き出しが同じ", ss), (u"タクソノミが同じ", tax), (u"fact が同じ", False if declined else facts), (u"鳴り方が同じ", False if declined else sound),
               (u"全部同じ", (not declined) and tax and facts), (u"2 度が同じ", False if declined else twice), (u"道筋が同じ", False if declined else path), (u"混ぜ物", list(mixes)),
               (u"組み直しの 1 回", None if declined else od([(u"類", cls), (u"符号ごとの行", {})]))])


def mx(made, found, sound, kind=u"本文の数を変える"):
    return od([(u"種類", kind), (u"作った", made), (u"違いを見つけた", found), (u"鳴り方が違う", sound)])


def totals_problems(ms=None):
    ms = ms or MS
    out_ = []
    ka, kb, kc, kd = ms.MIX_KINDS
    mixes_a = [mx(True, True, False, ka), mx(True, True, False, kb), mx(False, False, False, kc), mx(True, True, True, kd)]
    mixes_b = [mx(True, True, False, ka), mx(False, False, False, kb), mx(True, True, False, kc), mx(True, False, True, kd)]
    dev = [ent(mixes=mixes_a, same=[True] * 7, rows=[0, 1, 2, 3, 4, 5, 6]), ent(mixes=mixes_b, same=[True, True, True, True, True, True, False], facts=False)]
    prod = [ent(folder=4000, orig=2000, secs=0.3), ent(declined=True, rows=[1] * 7, folder=0, secs=None), ent(same=[True, False, True, True, True, True, True], sound=False, cls=u"止まった", twice=False, folder=1000, orig=2000),
            ent(facts=False, cls=u"走らなかった", path=False, folder=2000, orig=2000, secs=2.0), ent(folder=3000, orig=2000, twice=True, path=False, secs=0.2)]
    per = dev + prod
    t = ms.totals_of(per, 2)
    if list(t) != [u"開発の 5 本", u"本番だけの 5 本", u"全部", u"混ぜ物", u"混ぜ物の種類ごと"]:
        return [u"集計の群の名・並びが違う: %s" % list(t)]
    p = t[u"本番だけの 5 本"]
    got = (p[u"書類"], p[u"断った書類"], p[u"断らなかった書類"], p[u"全部同じ書類"], p[u"タクソノミが同じ書類"], p[u"fact が同じ書類"], p[u"鳴り方が同じ書類"], p[u"2 度が同じ書類"], p[u"道筋が同じ書類"], p[u"原稿が元より大きい書類"])
    # 全部同じ: 1 本目・5 本目(2)・タクソノミが同じ: 1・4・5 本目(3)・fact が同じ: 1・3・5(3)・鳴り方が同じ: 1・4・5(3)・2 度: 1・4・5(3)・道筋: 1・3(2)・大きい: 1(4000)・5(3000)(2)
    if got != (5, 1, 4, 2, 3, 3, 3, 3, 2, 2):
        out_.append(u"本番の群の数が手で数えた値と違う: %s" % (got,))
    if dict(p[u"組み直した包みの 1 回の類ごと"]) != {u"走った": 2, u"止まった": 1, u"走らなかった": 1} or dict(p[u"断った理由ごと"]) != {u"組む命令の断り": 1}:
        out_.append(u"類ごと・断った理由ごとの数が違う")
    if dict(p[u"書き出しごとに同じ書類"]) != {u"概念": 4, u"役割型": 3, u"表示": 4, u"計算": 4, u"次元": 4, u"ラベルの関係": 4, u"一般特殊": 4}:
        out_.append(u"書き出しごとに同じ書類の数が違う: %s" % dict(p[u"書き出しごとに同じ書類"]))
    if p[u"元の書き出しの行の数の合計"][u"概念"] != 4 + 1 + 4 + 4 + 4 or p[u"元の概念の行が 1 以下の書類"] != 1 or t[u"開発の 5 本"][u"元の概念の行が 1 以下の書類"] != 1:
        out_.append(u"元の書き出しの行の数の合計・概念の行が 1 以下の書類の数が違う")
    fo = p[u"原稿の folder の合計"]
    # 本番 5 本の folder: 4000・0・1000・2000・3000(合計 10000)。種類ごとの bytes は folder // 4 を 4 種類 → 4 種類の合計が folder の bytes。file は断った 1 本だけ 0
    if fo[u"bytes の合計"] != 10000 or fo[u"種類ごと"][u"素の本文"][u"bytes"] != 2500 or fo[u"種類ごと"][u"目次"][u"file"] != 4 or fo[u"種類ごと"][u"タクソノミの表"][u"bytes"] != 2500:
        out_.append(u"原稿の folder の合計が手で数えた値と違う: %s" % json.dumps(fo, ensure_ascii=False))
    oc = p[u"元の包みの合計"]
    if (oc[u"htm の bytes"], oc[u"タクソノミの bytes"], oc[u"bytes の合計"], oc[u"file"][u"htm"], oc[u"file"][u"タクソノミ"]) != (5000, 5000, 10000, 10, 30):
        out_.append(u"元の包みの合計が手で数えた値と違う: %s" % json.dumps(oc, ensure_ascii=False))
    if abs(p[u"組む命令の秒の合計"] - 4.0) > 1e-9:
        out_.append(u"組む命令の秒の合計が違う(秒が無い書類は足さない): %s" % p[u"組む命令の秒の合計"])
    dv = t[u"開発の 5 本"]
    if (dv[u"書類"], dv[u"全部同じ書類"], dv[u"断った書類"], dv[u"fact が同じ書類"]) != (2, 1, 0, 1) or t[u"全部"][u"書類"] != 7 or t[u"全部"][u"断った書類"] != 1:
        out_.append(u"開発の群・全部の数が違う")
    m = t[u"混ぜ物"]
    # 8 枠・作れた 6(a: 3・b: 3)・違いを見つけた 5(a: 3・b: 2)・鳴り方が違う 3(a: 1・b: 2 ... b の 4 つ目 True・1 つ目 False → a: 1・b: 1 = 2)
    if dict(m) != {u"混ぜ物の数": 8, u"作れた数": 6, u"違いを見つけた数": 5, u"鳴り方が違う数": 2}:
        out_.append(u"混ぜ物の合計が手で数えた値と違う(作れなかった混ぜ物を数えない): %s" % dict(m))
    mk = t[u"混ぜ物の種類ごと"]
    if list(mk) != list(ms.MIX_KINDS) or dict(mk[ka]) != {u"作れた": 2, u"違いを見つけた": 2, u"鳴り方が違う": 0} or dict(mk[kb]) != {u"作れた": 1, u"違いを見つけた": 1, u"鳴り方が違う": 0} or dict(mk[kd]) != {u"作れた": 2, u"違いを見つけた": 1, u"鳴り方が違う": 2}:
        out_.append(u"混ぜ物の種類ごとの数が違う: %s" % json.dumps(mk, ensure_ascii=False))
    j = ms.judged(t, 7)
    jv = list(j.values())
    got = (jv[0][u"書類"], jv[0][u"分母"], jv[1][u"書類"], jv[2][u"書類"], jv[3][u"書類"], jv[3][u"分母(断らなかった書類)"], jv[4][u"書類"], jv[4][u"分母(断らなかった書類)"], jv[5][u"個"], jv[5][u"分母"], jv[6][u"書類"], jv[6][u"分母"], jv[7][u"作れた"], jv[7][u"分母"])
    if got != (2, 5, 1, 3, 3, 4, 2, 4, 5, 6, 2, 5, 6, 8):
        out_.append(u"予測の判定に要る数が手で数えた値と違う: %s" % (got,))
    if [k[:5] for k in list(j)[:7]] != [u"XP0-1", u"XP0-2", u"XP0-3", u"XP0-4", u"XP0-5", u"XP0-6", u"XP0-7"]:
        out_.append(u"判定の鍵の並びが違う")
    return out_


def tools_problems(ms=None):
    ms = ms or MS
    out_ = []
    wp = hashlib.sha256(X.MV_P).hexdigest()
    with Temp() as d:
        tool, mv = X.make_tool(d)
        r = X.FakeRunner(mv)
        info = ms.check_tool(tool, r, read_bytes_sha, want_sha=wp)
        if (info[u"版"], info[u"ModelValue.py の sha256"]) != (u"2.47.5", wp):
            out_.append(u"道具の情報が違う: %s" % dict(info))
        if not stops(ms, ms.check_tool, tool, r, want_sha=wp, want_version=u"2.47.6") or not stops(ms, ms.check_tool, tool, r, want_sha=u"0" * 64) or not stops(ms, ms.check_tool, tool, r):
            out_.append(u"版・sha256 が封と違うのに止まらない")
        if not stops(ms, ms.check_tool, os.path.join(d, "none"), r, want_sha=wp):
            out_.append(u"道具の場所が無いのに止まらない")
    return out_


def dev_docs_problems(ms=None):
    u"""開発の入口は 5 本だけ: 7 本以上の zip で ``dev_docs`` は 5 本を選んだ所で止まり、6 本目を開かない。"""
    ms = ms or MS
    out_ = []
    with Temp() as d:
        make_pack_docs(d, 7)
        opened = []
        bz = ms.B.zipfile
        real = bz.ZipFile

        class Counting(real):
            def __init__(self, f, *a, **kw):
                opened.append(os.path.basename(str(f)))
                real.__init__(self, f, *a, **kw)
        bz.ZipFile = Counting
        try:
            got = ms.dev_docs(d, 5)
            got_default = ms.dev_docs(d)
        finally:
            bz.ZipFile = real
        want = [u"S2FAKE0%d" % i for i in range(1, 6)]
        if [g[0] for g in got] != want or [g[0] for g in got_default] != want:
            out_.append(u"開発の 5 本が並びの頭の 5 本でない: %s" % [g[0] for g in got])
        if opened != [u"S2FAKE0%d.zip" % i for i in range(1, 6)] * 2:
            out_.append(u"開いた zip が並びの頭の 5 本だけでない: %s" % opened)
        if ms.DEV_COUNT != 5 or ms.dev_docs.__defaults__ != (5,):
            out_.append(u"dev_docs の既定の本数が 5 でない")
    return out_


STEMS = [u"S2FAKE01", u"S2FAKE02", u"S2FAKE03"]
ORDER_SHA = hashlib.sha256(u"\n".join(STEMS).encode("utf-8")).hexdigest()


def record_args(d, ms, runner=None, count=3, proc=None, **kw):
    docs = os.path.join(d, "docs")
    os.makedirs(docs)
    make_pack_docs(docs, count)
    tool, mv = X.make_tool(os.path.join(d, "tool"))
    tmp = os.path.join(d, "tmp")
    os.makedirs(tmp)
    runner = runner or PackRunner(mv)
    proc = proc or InProc(ms)
    args = dict(want=count, runner=runner, tmp_root=tmp, want_sha=hashlib.sha256(X.MV_P).hexdigest(), dev_count=1, proc=proc)
    args.update(kw)
    return tool, docs, runner, tmp, args


def run_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        tool, docs, runner, tmp, args = record_args(d, ms)
        progress = []
        rec, secret = ms.build_record(tool, docs, progress=progress.append, **args)
        # 1 本目は混ぜ物つきで道具 12 回・組む命令 6 回・2 本目と 3 本目は道具 4 回・組む命令 2 回ずつ
        if len(runner.calls) != 12 + 4 + 4 or len(args["proc"].calls) != 6 + 2 + 2:
            out_.append(u"道具の呼び出し・組む命令の呼び出しの数が違う: %d・%d" % (len(runner.calls), len(args["proc"].calls)))
        if len(progress) != 3 or not progress[0].startswith(u"doc 1/3("):
            out_.append(u"書類ごとの進みを出さない: %s" % progress)
        mat = rec[u"材料"]
        if (mat[u"書類の本数"], mat[u"書類の file 名の並びの sha256"], mat[u"開発の 5 本の番号"], mat[u"道具の版"], mat[u"道具 P の ModelValue.py の sha256"], mat[u"規則の年"], mat[u"時間の上限(秒)"], mat[u"混ぜ物の種類"]) != (
                3, ORDER_SHA, [1], u"2.47.5", hashlib.sha256(X.MV_P).hexdigest(), u"EDINET-2026", 600, list(ms.MIX_KINDS)):
            out_.append(u"材料の欄が手で数えた値と違う: %s" % dict(mat))
        if [dd[u"番号"] for dd in rec[u"書類"]] != [1, 2, 3] or [len(dd[u"混ぜ物"]) for dd in rec[u"書類"]] != [4, 0, 0]:
            out_.append(u"書類の番号・混ぜ物の置き場所が違う(混ぜ物は開発の本数だけ)")
        t = rec[u"集計"]
        if (t[u"開発の 5 本"][u"書類"], t[u"本番だけの 2 本"][u"書類"], t[u"全部"][u"全部同じ書類"], t[u"混ぜ物"][u"混ぜ物の数"], t[u"混ぜ物"][u"作れた数"]) != (1, 2, 3, 4, 4):
            out_.append(u"集計が手で数えた値と違う")
        if rec[u"この script の sha256"] != sha_of(SCRIPT_REL) and ms is MS:
            out_.append(u"記録の script の sha256 が違う")
        text = ms.dumps(rec)
        for leak in STEMS + [u"E9999", u"S2OTHER1", u".xbrl", u".htm", u".xsd", u"audit", u"Alpha", u"Beta", u"Gamma", u"jppfs", u"http", u"冗長", u"売上", u"Sales", u"x_pre", u"role/a", u"題名", u"前置き", u"Assets", u"Zero", u"PublicDoc", u"1,234", u"index.json"]:
            if leak in text:
                out_.append(u"記録に材料の字が在る: %s" % leak)
        if set(secret[3]) != set([u"E9999%d" % i for i in (1, 2, 3)]) or list(secret[2]) != STEMS or not {"Alpha", "Gamma", "BetaHeading"} <= set(secret[1]) or u"冗長" in secret[0] or X.TXT1 not in secret[0]:
            out_.append(u"secret の docID・EDINET コード・要素の名・ラベルの字が違う")
        if os.listdir(tmp):
            out_.append(u"使い捨ての場所が残っている")
        r2 = PackRunner(runner.mv_path)
        a2 = dict(args, runner=r2, want=67, proc=InProc(ms))
        if not stops(ms, ms.build_record, tool, docs, **a2) or r2.calls or a2["proc"].calls:
            out_.append(u"書類が 67 本でないのに止まらない(か掛けた)")
        r3 = PackRunner(runner.mv_path)
        a3 = dict(args, runner=r3, want_sha=u"0" * 64, proc=InProc(ms))
        if not stops(ms, ms.build_record, tool, docs, **a3) or r3.calls or a3["proc"].calls:
            out_.append(u"道具の sha256 が封と違うのに止まらない(か掛けた)")
    return out_


def verify_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        tool, docs, runner, tmp, args = record_args(d, ms)
        rec, secret = ms.build_record(tool, docs, **args)
        p = os.path.join(d, "r.json")
        ms.write_record(p, rec, secret)
        if stops(ms, ms.check, rec_path=p, want=3, say=lambda *a: None, dev_count=1):
            out_.append(u"きれいな記録で --check が止まる")
        if not stops(ms, ms.check, rec_path=p, say=lambda *a: None):
            out_.append(u"書類が 67 本でない記録で --check が止まらない")
        if not stops(ms, ms.check, rec_path=os.path.join(d, "none.json"), want=3, say=lambda *a: None):
            out_.append(u"記録が無いのに --check が止まらない")
        base = ms.dumps(rec)
        if read_text(p) != base:
            out_.append(u"書いた字が dumps と違う")

        def refresh_after(fn):
            def go(r):
                fn(r)
                r[u"集計"] = ms.totals_of(r[u"書類"], 1)
                r[[k for k in r if k.startswith(u"予測の判定に要る数")][0]] = ms.judged(r[u"集計"], len(r[u"書類"]))
            return go

        def decline_doc1(r):
            e = r[u"書類"][1]
            e[u"断った"], e[u"断った理由"], e[u"組み直しの 1 回"] = True, u"固定の理由", None
        tampers = [
            (u"集計の数を変える", lambda r: r[u"集計"][u"全部"].__setitem__(u"断った書類", 9)),
            (u"書類ごとの fact が同じを変える(合計と合わない)", lambda r: r[u"書類"][0].__setitem__(u"fact が同じ", False)),
            (u"書類ごとの鳴り方を変える", lambda r: r[u"書類"][1].__setitem__(u"鳴り方が同じ", False)),
            (u"書類ごとの 2 度が同じを変える", lambda r: r[u"書類"][1].__setitem__(u"2 度が同じ", False)),
            (u"書類を 1 本消す", lambda r: r[u"書類"].pop()),
            (u"書類の番号を変える", lambda r: r[u"書類"][0].__setitem__(u"番号", 7)),
            (u"材料の書類の本数だけを変える", lambda r: r[u"材料"].__setitem__(u"書類の本数", 5)),
            (u"欄を消す", lambda r: r[u"書類"][0].pop(u"元の 1 回")),
            (u"原稿の folder の欄を消す", lambda r: r[u"書類"][0].pop(u"原稿の folder")),
            (u"類の字が違う", lambda r: r[u"書類"][0][u"元の 1 回"].__setitem__(u"類", u"壊れた")),
            (u"断ったのに組み直しの 1 回が在る", refresh_after(lambda r: r[u"書類"][1].__setitem__(u"断った", True))),
            (u"断っていないのに理由が在る", refresh_after(lambda r: r[u"書類"][1].__setitem__(u"断った理由", u"固定の理由"))),
            (u"断ったのに理由が無い", refresh_after(lambda r: (r[u"書類"][1].__setitem__(u"断った", True), r[u"書類"][1].__setitem__(u"組み直しの 1 回", None)))),
            (u"断ったのに全部同じ", refresh_after(decline_doc1)),
            (u"断ったのに理由が空", refresh_after(lambda r: (decline_doc1(r), r[u"書類"][1].update({u"断った理由": u"", u"全部同じ": False, u"タクソノミが同じ": False, u"fact が同じ": False, u"鳴り方が同じ": False, u"2 度が同じ": False, u"道筋が同じ": False}),
                                                         r[u"書類"][1].__setitem__(u"書き出しが同じ", od((k, False) for k in ms.OUTPUT_KEYS))))),
            (u"材料の欄に EDINET コードの形の字を足す", lambda r: r[u"材料"].__setitem__(u"メモ", u"E12345")),
            (u"断ったのに 2 度が同じ", refresh_after(lambda r: (decline_doc1(r), r[u"書類"][1].update({u"全部同じ": False, u"タクソノミが同じ": False, u"fact が同じ": False, u"鳴り方が同じ": False, u"道筋が同じ": False}), r[u"書類"][1].__setitem__(u"書き出しが同じ", od((k, False) for k in ms.OUTPUT_KEYS))))),
            (u"断ったのに道筋が同じ", refresh_after(lambda r: (decline_doc1(r), r[u"書類"][1].update({u"全部同じ": False, u"タクソノミが同じ": False, u"fact が同じ": False, u"鳴り方が同じ": False, u"2 度が同じ": False}), r[u"書類"][1].__setitem__(u"書き出しが同じ", od((k, False) for k in ms.OUTPUT_KEYS))))),
            (u"混ぜ物を本番の書類に置く", refresh_after(lambda r: r[u"書類"][1].__setitem__(u"混ぜ物", [od([(u"種類", k), (u"作った", True), (u"違いを見つけた", True), (u"鳴り方が違う", True)]) for k in ms.MIX_KINDS]))),
            (u"混ぜ物の種類を変える", refresh_after(lambda r: r[u"書類"][0][u"混ぜ物"][0].__setitem__(u"種類", u"消す"))),
            (u"作れなかった混ぜ物に違いを見つけたが付く", refresh_after(lambda r: r[u"書類"][0][u"混ぜ物"][0].update({u"作った": False, u"違いを見つけた": True}))),
            (u"書き出しが同じの欄の 1 つが違うのにタクソノミが同じのまま", refresh_after(lambda r: r[u"書類"][0][u"書き出しが同じ"].__setitem__(u"表示", False))),
            (u"全部同じが fact が同じと合わない", refresh_after(lambda r: r[u"書類"][0].__setitem__(u"fact が同じ", False))),
            (u"原稿が元より大きいが bytes と合わない", refresh_after(lambda r: r[u"書類"][0].__setitem__(u"原稿が元より大きい", not r[u"書類"][0][u"原稿が元より大きい"]))),
            (u"原稿の folder の欄の並びを変える", refresh_after(lambda r: r[u"書類"][0].__setitem__(u"原稿の folder", od(reversed(list(r[u"書類"][0][u"原稿の folder"].items())))))),
            (u"判定の数を変える", lambda r: [r[k] for k in r if k.startswith(u"予測の判定に要る数")][0].__setitem__(u"XP0-1 全部同じ書類", 99))]
        for what, fn in tampers:
            r2 = json.loads(base, object_pairs_hook=od)
            fn(r2)
            if ms.dumps(r2) == base or not stops(ms, ms.verify_record, r2, None, 3, 1):
                out_.append(u"記録を変えても検査が止まらない: %s" % what)
    return out_


def clean_problems(ms=None):
    ms = ms or MS
    out_ = []
    ok = od([(u"書類", [od([(u"番号", 1), (u"断った理由", u"固定の理由"), (u"材料の sha256", u"a" * 64)])])])
    secret = ({u"長めのラベルの字"}, {u"NetSalesOfX"}, [u"zzdoc"], {u"E99991"}, {u"[EDINET.EC5611W] ある指摘の行の本文"})
    if stops(ms, ms.check_clean, ok, ms.dumps(ok), secret):
        out_.append(u"きれいな記録で止まる")
    cases = [
        (u"禁止の欄(docid)", od([(u"DocID", 1)])), (u"禁止の欄(company)", od([(u"company", 1)])), (u"禁止の欄(label)", od([(u"label", 1)])), (u"禁止の欄(element)", od([(u"element", 1)])),
        (u"EDINET コードの形", od([(u"x", u"id E12345 x")])), (u"docID の形", od([(u"x", u"S100ABCD")])),
        (u"材料の docID", od([(u"x", u"id zzdoc.")])), (u"材料の EDINET コード", od([(u"x", u"E99991")])),
        (u"file の名(htm)", od([(u"x", u"0101010_honbun.htm")])), (u"file の名(xsd)", od([(u"x", u"jpcrp030000-asr-001.xsd")])), (u"file の名(PublicDoc)", od([(u"x", u"XBRL/PublicDoc/x")])),
        (u"要素の名", od([(u"x", u"理由 NetSalesOfX")])), (u"ラベルの字", od([(u"x", u"文 長めのラベルの字 文")])),
        (u"role の URI", od([(u"x", u"http://disclosure.edinet-fsa.go.jp/role/jppfs/rol_BalanceSheet")])), (u"role の URI(https)", od([(u"x", u"https://x/y")])),
        (u"指摘の行の本文", od([(u"x", u"文 [EDINET.EC5611W] ある指摘の行の本文 文")]))]
    for what, rec in cases:
        if not stops(ms, ms.check_clean, rec, ms.dumps(rec), secret):
            out_.append(u"%s が止まらない" % what)
        if not stops(ms, ms.record_text, rec, secret):
            out_.append(u"%s が record_text で止まらない" % what)
    with Temp() as d:
        p = os.path.join(d, "r.json")
        bad = od([(u"x", u"E12345")])
        if not stops(ms, ms.write_record, p, bad) or os.path.exists(p):
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


def e2e_problems(ms=None):
    u"""``run`` → 記録 → ``--check`` を作り物の置き場と道具で通す(置き場も道具も開かない)。"""
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        tool, docs, runner, tmp, args = record_args(d, ms)
        rp = os.path.join(d, "rec", "r.json")
        kw = dict(docs=docs, out=rp, runner=runner, tmp_root=tmp, say=lambda *a: None, want_sha=args["want_sha"], dev_count=1, proc=args["proc"])
        if not stops(ms, ms.run, tool, want=67, **kw) or os.path.exists(rp):
            out_.append(u"書類が 67 本でないのに run が止まらない(か記録を書いた)")
        lines = []
        rec = ms.run(tool, want=3, progress=lines.append, **kw)
        if not os.path.exists(rp) or ms.dumps(rec) != read_text(rp) or len(lines) != 3:
            out_.append(u"記録が書かれていない・字が違う・進みを出さない")
        if not stops(ms, ms.run, tool, want=3, **kw):
            out_.append(u"記録が既に在るのに run が止まらない")
        ms.check(rec_path=rp, want=3, say=lambda *a: None, dev_count=1)
        rp2 = os.path.join(d, "rec", "r2.json")
        kw2 = dict(kw, out=rp2, runner=PackRunner(runner.mv_path), want_sha=u"0" * 64, proc=InProc(ms))
        if not stops(ms, ms.run, tool, want=3, **kw2) or os.path.exists(rp2):
            out_.append(u"道具の sha256 が違うのに記録を書いた")
    return out_


def devrun_problems(ms=None):
    u"""開発の入口(``dev_run``): 置き場の並びの頭の本数だけを掛け、記録は書かない。"""
    ms = ms or MS
    out_ = []
    with Temp() as d:
        tool, docs, runner, tmp, args = record_args(d, ms, count=7)
        lines = []
        saved = ms.check_tool
        ms.check_tool = lambda t, r=None, *a, **k: saved(t, r, sha_reader=ms.sha256_file, want_sha=hashlib.sha256(X.MV_P).hexdigest())
        try:
            per = ms.dev_run(tool, docs_dir=docs, runner=runner, tmp_root=tmp, say=lines.append, proc=args["proc"])
        finally:
            ms.check_tool = saved
        if len(per) != 5 or len(runner.calls) != 5 * 12 or len(args["proc"].calls) != 5 * 6 or os.path.exists(os.path.join(d, "rec")):
            out_.append(u"開発の入口が 5 本だけ(混ぜ物つき)掛けていない: %d 本・道具 %d 回・組む命令 %d 回" % (len(per), len(runner.calls), len(args["proc"].calls)))
        if len(lines) != 6 or not lines[0].startswith(u"doc 1(") or u"全部同じ=True" not in lines[0] or u"2度=True" not in lines[0] or u"道筋=True" not in lines[0] or not lines[-1].startswith(u"開発の 5 本の合計"):
            out_.append(u"開発の入口の出力の形が違う: %s" % lines[:1])
    return out_


# ======================================================================== 8. 配線
STDLIB_OK = ("__future__", "argparse", "collections", "importlib", "io", "json", "os", "re", "shutil", "subprocess", "sys", "tempfile", "time")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "adapters", "core", "audit_core", "zipfile", "csv", "xml")
#: 前の便の script の関数を呼ぶ(写さない): (module の名, 関数の名)
CALLED = (("W", "select_docs"), ("W", "order_sha256"), ("V", "CLASSES"), ("B", "load_package"), ("B", "write_package"), ("B", "facts_same"), ("B", "sounds_same"), ("B", "dev_docs"), ("B", "build_files"),
          ("B", "build_text"), ("B", "rebuilt_texts"), ("B", "mix_tables"), ("B", "num_pool"), ("B", "is_zero_content"), ("B", "is_public_htm"), ("T", "strip_tables"), ("T", "build_tables"), ("T", "find_files"),
          ("T", "package_with"), ("T", "run_package"), ("T", "compare_into"), ("T", "outputs_same"), ("T", "mix_tables"), ("T", "check_tool"), ("T", "check_clean"), ("T", "secret_of"))
NOT_COPIED = ("select_docs", "order_sha256", "strip_text", "build_text", "strip_tables", "build_tables", "strip_xsd", "strip_linkbase", "build_xsd", "build_linkbase", "build_files", "rebuilt_texts", "find_files",
              "load_package", "write_package", "package_with", "run_package", "compare_into", "outputs_same", "output_same", "canon_rows", "facts_same", "sounds_same", "read_rows", "read_table_rows",
              "command_a", "command_b", "count_one", "exec_cmd", "mix_tables", "num_pool", "is_zero_content", "is_public_htm", "table_counts", "secret_of")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
#: 別の門の規準の字(関数の名・呼び出し・説明文のどこにも使わない)
HARNESS_WORDS = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(", "tampered", u"注入")
OTHER_NAMES = (u"_xv0_tag_wall_2026_11_21", u"_xg1_tag_wall_2026_11_21", u"_xb0_tag_wall_2026_11_21", u"_xb0_tag_narrow", u"_xb0_edinet_validate_2026_11_21", u"_xb0_inline_build_2026_11_21", u"_xt0_inline_build_2026_11_21", u"_xt0_taxonomy_build_2026_11_22")


def func_map(tree):
    return dict((n.name, n) for n in tree.body if isinstance(n, ast.FunctionDef))


def names_in(node):
    return set(n.id for n in ast.walk(node) if isinstance(n, ast.Name))


def attr_calls(node):
    return set((n.func.value.id, n.func.attr) for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name))


def name_calls(node):
    return [n.func.id for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]


def isolation_problems(src=None):
    u"""組む命令の中身(``render_folder``・``build_main``)は folder だけを引数に取り、元の包み・zip を読まない。``process_doc`` は組む命令を別の process で呼ぶ。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    funcs = func_map(tree)
    out_ = []
    for nm, args in (("render_folder", ["folder"]), ("build_main", ["args"]), ("build_command", ["folder", "out"]), ("write_out", ["out", "rendered"])):
        f = funcs.get(nm)
        if f is None or [a.arg for a in f.args.args] != args or f.args.vararg or f.args.kwarg or f.args.kwonlyargs or f.args.defaults:
            out_.append(u"%s の引数が (%s) だけでない" % (nm, ", ".join(args)))
    rf = funcs.get("render_folder")
    if rf is not None:
        bad = sorted(names_in(rf) & set(("entries", "zip_path", "zipfile", "load_package", "peel_tables", "peel_folder", "write_folder", "process_doc", "files", "names", "orig_zip", "open", "ET", "SCRIPT_PATH", "exec_build", "run_process")))
        if bad:
            out_.append(u"render_folder が元の包み・zip・file を直接読む名前を使っている: %s" % bad)
        if any(m == "B" and a in ("load_package", "strip_text", "build_files") for m, a in attr_calls(rf)) or any(m == "T" and a in ("find_files", "strip_tables") for m, a in attr_calls(rf)):
            out_.append(u"render_folder が剥がす側の関数を呼んでいる")
        reads = [n for n in ast.walk(rf) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "read_bytes"]
        for c in reads:
            a0 = c.args[0] if len(c.args) == 1 else None
            if not (isinstance(a0, ast.Call) and isinstance(a0.func, ast.Attribute) and a0.func.attr == "join" and a0.args and isinstance(a0.args[0], ast.Name) and a0.args[0].id == "folder"):
                out_.append(u"render_folder の read_bytes が folder の中の file を読んでいない")
        if len(reads) != 4:
            out_.append(u"render_folder が読む file が目次・本文・表・タクソノミの 4 か所でない: %d" % len(reads))
        if not {("B", "build_text"), ("T", "build_tables")} <= attr_calls(rf):
            out_.append(u"render_folder が便 XB0 の build_text・便 XT0 の build_tables を呼んでいない")
    bm = funcs.get("build_main")
    if bm is not None:
        allowed = set(("len", "print", "render_folder", "write_out"))
        extra = sorted(set(name_calls(bm)) - allowed)
        if extra:
            out_.append(u"build_main が render_folder・write_out のほかを呼んでいる: %s" % extra)
        if "render_folder" not in name_calls(bm) or "write_out" not in name_calls(bm):
            out_.append(u"build_main が render_folder・write_out を呼んでいない")
    bc = funcs.get("build_command")
    if bc is not None:
        rets = [n for n in ast.walk(bc) if isinstance(n, ast.Return)]
        lst = rets[0].value if len(rets) == 1 else None
        if not isinstance(lst, ast.List) or len(lst.elts) != 6 or [getattr(e, "id", None) for e in lst.elts[4:]] != ["folder", "out"] or getattr(lst.elts[3], "value", None) != "build" or getattr(lst.elts[1], "value", None) != "-I":
            out_.append(u"build_command が [python, -I, script, build, folder, folder] の 6 つでない")
    pd = funcs.get("process_doc")
    if pd is not None:
        nc = name_calls(pd)
        if "render_folder" in nc or "build_main" in nc or "render_folder" in names_in(pd) or "build_main" in names_in(pd):
            out_.append(u"process_doc が組む命令を同じ process で呼んでいる(別の process で呼ぶのは exec_build)")
        if nc.count("exec_build") != 3 or "same_process_tree" not in nc:
            out_.append(u"process_doc が exec_build を 3 か所(1 回目・2 回目・混ぜ物)・same_process_tree を呼んでいない: %d" % nc.count("exec_build"))
        for c in [n for n in ast.walk(pd) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "exec_build"]:
            if len(c.args) != 4 or [getattr(a, "id", None) for a in c.args[2:]] != ["cwd", "proc"]:
                out_.append(u"exec_build の呼び出しが (folder, out, cwd, proc) でない")
    eb = funcs.get("exec_build")
    if eb is not None and "build_command" not in name_calls(eb):
        out_.append(u"exec_build が build_command を呼んでいない")
    # 組む部品の呼び出しは render_folder・same_process_tree だけ
    callers = {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            for m, a in attr_calls(n):
                if (m, a) in (("B", "build_text"), ("T", "build_tables"), ("B", "rebuilt_texts")):
                    callers.setdefault((m, a), set()).add(n.name)
    if callers.get(("B", "build_text")) != set(["render_folder"]) or callers.get(("T", "build_tables")) != set(["render_folder", "same_process_tree"]) or callers.get(("B", "rebuilt_texts")) != set(["same_process_tree"]):
        out_.append(u"組む部品の呼び出し元が render_folder・same_process_tree だけでない: %s" % dict((k, sorted(v)) for k, v in callers.items()))
    if any(isinstance(n, ast.Name) and n.id in ("zipfile", "csv", "ET") for n in ast.walk(tree)):
        out_.append(u"script が zipfile・csv・ElementTree を使っている")
    # subprocess を使う所は run_process だけ(shell を通さない)
    users = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and any(isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == "subprocess" for x in ast.walk(n))]
    if sorted(users) != ["run_process"]:
        out_.append(u"subprocess を使う関数が run_process だけでない: %s" % users)
    return out_


def import_problems(src=None):
    u"""script の import は標準ライブラリ・subprocess・importlib だけ(engine を読まない)。前の便の script は T・B・V・W から呼び写さない。"""
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
    attrs = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]
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
    if TAXONOMY_NAME not in consts:
        out_.append(u"便 XT0 の script を読む名が一意の名(%s)でない" % TAXONOMY_NAME)
    for want, var in (("B", "B"), ("V", "V"), ("W", "W")):
        if not any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == var for t in n.targets) and isinstance(n.value, ast.Attribute) and isinstance(n.value.value, ast.Name) and n.value.value.id == "T" and n.value.attr == want for n in tree.body):
            out_.append(u"%s を便 XT0 の script の %s から受けていない(Stop の型・module の実体が 2 つになる)" % (var, want))
    if not any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "T" for t in n.targets) and isinstance(n.value, ast.Call) and getattr(n.value.func, "id", None) == "_load_sibling" for n in tree.body):
        out_.append(u"T を _load_sibling で読んでいない")
    if any(n in consts for n in OTHER_NAMES):
        out_.append(u"他の便と重なる名で読んでいる")
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
MUTANTS = (
    # ---- 落とす・folder の形
    (u"P1 JSON を ensure_ascii=True で書く", u'json.dumps(o, ensure_ascii=False, separators=(",", ":"))', u'json.dumps(o, ensure_ascii=True, separators=(",", ":"))', ("folder",)),
    (u"P2 JSON を空白つきの区切りで書く", u'json.dumps(o, ensure_ascii=False, separators=(",", ":"))', u"json.dumps(o, ensure_ascii=False)", ("folder",)),
    (u"P3 素の本文の改行を落とす", u'write_bytes(os.path.join(folder, TEXT_FMT % i), plain.encode("utf-8"))', u'write_bytes(os.path.join(folder, TEXT_FMT % i), plain.replace(u"\\r", u"").encode("utf-8"))', ("folder", "doc")),
    (u"P4 htm の並びを逆にする", u"for i, (name, plain, F, H) in enumerate(files):", u"for i, (name, plain, F, H) in enumerate(reversed(files)):", ("folder",)),
    (u"P5 タクソノミの名を PublicDoc つきのまま持つ", u'("names", od((k, rel_of(names[k])) for k in FILE_KINDS))', u'("names", od((k, names[k]) for k in FILE_KINDS))', ("folder", "doc")),
    (u"P6 htm の名を PublicDoc つきのまま持つ", u'index["htm"].append(od([("name", rel_of(name)),', u'index["htm"].append(od([("name", name),', ("folder", "doc")),
    (u"P7 表 H を持たない", u'write_bytes(os.path.join(folder, TABLES_FMT % i), jdump(od([("F", F), ("H", H)])))', u'write_bytes(os.path.join(folder, TABLES_FMT % i), jdump(od([("F", F), ("H", None)])))', ("folder", "render", "doc")),
    (u"P8 目次をタクソノミの file の名ごと持たない", u'od([("file", TAXONOMY_FILE),', u'od([("file", "tax.json"),', ("folder",)),
    (u"P9 素の本文を表と同じ file に混ぜる(file の名の並びを変える)", u'TEXT_FMT = "t%04d.txt"', u'TEXT_FMT = "t%04d.html"', ("folder", "render")),
    (u"P10 folder に元の xsd・linkbase の bytes をそのまま置く", u'write_bytes(os.path.join(folder, TAXONOMY_FILE), jdump(od([("tables", tables)])))',
     u'write_bytes(os.path.join(folder, TAXONOMY_FILE), jdump(od([("tables", tables)])))\n    write_bytes(os.path.join(folder, "orig.xsd"), names and b"<x/>")', ("folder",)),
    (u"P11 落とす側の断りを例外のまま通す", u'    except (B.Decline, T.Decline) as exc:\n        raise Refuse(exc.reason)\n    except Exception:                                      # noqa: BLE001  知らない形は断る\n        raise Refuse(u"落とす途中の例外")',
     u'    except (B.Decline, T.Decline) as exc:\n        raise Refuse(exc.reason)', ("folder",)),
    (u"P12 peel の引数の数を縛らない", u'    u"""落とす命令。引数は zip と folder。"""\n    if len(args) != 2:', u'    u"""落とす命令。引数は zip と folder。"""\n    if False:', ("folder",)),
    (u"P13 main が peel を呼ばない", u'    if argv and argv[0] == "peel":\n        sys.exit(peel_main(argv[1:]))\n', u"", ("folder",)),
    # ---- 組む(folder だけを読む)
    (u"R1 htm の素の本文でなく空を組む(表 H を渡さない)", u'B.build_text(plain, tab["F"], tab["H"])', u'B.build_text(plain, tab["F"], None)', ("render", "doc")),
    (u"R2 タクソノミの名の対応を変える", u'out[rel] = built[k]', u'out[rel] = built["xsd"]', ("render", "doc")),
    (u"R3 目次の相対の名の ``..`` を断らない", u'''any(p in ("", "..", ".") for p in rel.split("/"))''', u'''any(p in ("",) for p in rel.split("/"))''', ("render",)),
    (u"R4 目次の相対の名の先頭の / を断らない", u'''rel.startswith("/") or "\\\\" in rel''', u'''"\\\\" in rel''', ("render",)),
    (u"R5 目次の相対の名の逆斜線を断らない", u'''rel.startswith("/") or "\\\\" in rel or "\\x00" in rel''', u'''rel.startswith("/") or "\\x00" in rel''', ("render",)),
    (u"R6 folder の中の名の / を断らない", u'''if not isinstance(name, str) or not name or "/" in name or "\\\\" in name''', u'''if not isinstance(name, str) or not name or "\\\\" in name''', ("render",)),
    (u"R7 htm の名の重なりを断らない", u'''            if rel in out:
                raise Refuse(u"目次の名が重なる")
            out[rel] = B.build_text''', u'''            out[rel] = B.build_text''', ("render",)),
    (u"R8 タクソノミの名の重なりを断らない", u'''            if rel in out:
                raise Refuse(u"目次の名が重なる")
            out[rel] = built[k]''', u'''            out[rel] = built[k]''', ("render",)),
    (u"R9 出す folder に下の folder を作らない", u"        os.makedirs(os.path.dirname(path), exist_ok=True)\n        write_bytes(path, data)", u"        write_bytes(path, data)", ("render", "doc")),
    (u"R10 build_main が引数の数を縛らない", u'    if len(args) != 2:\n        print(u"使い方: build <原稿の folder> <出す folder>", file=sys.stderr)', u'    if False:\n        print(u"使い方: build <原稿の folder> <出す folder>", file=sys.stderr)', ("render", "proc")),
    (u"R11 断りの終わりの値を 1 にする", u"EXIT_USAGE, EXIT_DECLINE, EXIT_ERROR = 64, 2, 1", u"EXIT_USAGE, EXIT_DECLINE, EXIT_ERROR = 64, 1, 1", ("render", "proc")),
    (u"R12 断りの理由の行の頭を付けない", u"print(DECLINE_PREFIX + exc.reason, file=sys.stderr)\n        return EXIT_DECLINE\n    except Exception:                                      # noqa: BLE001\n        print(u\"ERROR\", file=sys.stderr)\n        return EXIT_ERROR\n    return 0\n\n\ndef peel_main",
     u"print(exc.reason, file=sys.stderr)\n        return EXIT_DECLINE\n    except Exception:                                      # noqa: BLE001\n        print(u\"ERROR\", file=sys.stderr)\n        return EXIT_ERROR\n    return 0\n\n\ndef peel_main", ("render", "proc")),
    (u"R13 build_main が例外を断りと同じに扱う", u"        write_out(args[1], render_folder(args[0]))\n    except Refuse as exc:", u"        write_out(args[1], render_folder(args[0]))\n    except (Refuse, OSError, ValueError) as exc:", ("render",)),
    (u"R14 main の build に build ごと渡す", u"sys.exit(build_main(argv[1:]))\n    if argv and argv[0] == \"peel\"", u"sys.exit(build_main(argv))\n    if argv and argv[0] == \"peel\"", ("render", "proc")),
    (u"R15 main が終わりの値を返さない", u"sys.exit(build_main(argv[1:]))", u"build_main(argv[1:])", ("render", "proc")),
    (u"R16 render_folder が cwd の file を読む", u'index = jload(read_bytes(os.path.join(folder, INDEX_FILE)))\n        out = od()', u'index = jload(read_bytes(INDEX_FILE if os.path.exists(INDEX_FILE) else os.path.join(folder, INDEX_FILE)))\n        out = od()', ("render", "isolation", "proc")),
    (u"R17 render_folder が元の包みを引数に取る", u"def render_folder(folder):", u"def render_folder(folder, entries=None):", ("isolation",)),
    (u"R18 render_folder が zip を開く名前を使う", u'        index = jload(read_bytes(os.path.join(folder, INDEX_FILE)))\n        out = od()', u'        zipfile = None\n        index = jload(read_bytes(os.path.join(folder, INDEX_FILE)))\n        out = od()', ("isolation",)),
    (u"R19 render_folder が組む部品を使わず別の関数を呼ぶ", u"out[rel] = B.build_text(plain, tab[\"F\"], tab[\"H\"]).encode(\"utf-8\")", u"out[rel] = B.rebuilt_texts([(rel, plain, tab[\"F\"], tab[\"H\"])])[0][1].encode(\"utf-8\")", ("isolation",)),
    # ---- 別の process
    (u"C1 組む命令の引数から -I を落とす", u'return [sys.executable, "-I", SCRIPT_PATH, "build", folder, out]', u'return [sys.executable, SCRIPT_PATH, "build", folder, out]', ("cmd", "seal", "isolation", "doc")),
    (u"C2 組む命令に余計な引数を足す", u'return [sys.executable, "-I", SCRIPT_PATH, "build", folder, out]', u'return [sys.executable, "-I", SCRIPT_PATH, "build", folder, out, "--x"]', ("cmd", "seal", "isolation", "doc")),
    (u"C3 組む命令を shell 経由で呼ぶ", u"timeout=timeout, shell=False)", u"timeout=timeout, shell=True)", ("cmd",)),
    (u"C4 組む命令の cwd を渡さない", u"subprocess.run(list(cmd), cwd=cwd,", u"subprocess.run(list(cmd), cwd=None,", ("cmd",)),
    (u"C5 組む命令の時間の上限を渡さない", u"timeout=timeout, shell=False)", u"timeout=None, shell=False)", ("cmd",)),
    (u"C6 時間の上限の超えを失敗にしない", u'    if timed_out:\n        return False, u"組む命令が時間の上限を超えた", secs', u"    if False:\n        return False, u\"組む命令が時間の上限を超えた\", secs", ("cmd", "docdecl")),
    (u"C7 終わりの値を見ない", u"    if rc != 0:\n        reason = decline_reason(err)", u"    if False:\n        reason = decline_reason(err)", ("cmd", "docdecl")),
    (u"C8 断りの理由の行を行頭で見ない", u"        if line.startswith(DECLINE_PREFIX):\n            return line[len(DECLINE_PREFIX):][:REASON_MAX]", u"        if DECLINE_PREFIX in line:\n            return line[line.index(DECLINE_PREFIX) + len(DECLINE_PREFIX):][:REASON_MAX]", ("cmd",)),
    (u"C9 断りの理由の長さを切らない", u"return line[len(DECLINE_PREFIX):][:REASON_MAX]", u"return line[len(DECLINE_PREFIX):]", ("cmd",)),
    (u"C10 組む命令の cwd を原稿の folder にする", u"ok, reason, secs = exec_build(folder, out1, cwd, proc)", u"ok, reason, secs = exec_build(folder, out1, folder, proc)", ("doc",)),
    (u"C11 混ぜ物の組む命令の cwd を混ぜ物の folder にする", u"okm, _rm, _sm = exec_build(mf, mo, cwd, proc)", u"okm, _rm, _sm = exec_build(mf, mo, mf, proc)", ("doc",)),
    (u"C12 2 回目の組む命令の cwd を出す folder にする", u"ok2, _r2, _s2 = exec_build(folder, out2, cwd, proc)", u"ok2, _r2, _s2 = exec_build(folder, out2, out2, proc)", ("doc",)),
    (u"C13 組む命令を同じ process で呼ぶ", u"ok, reason, secs = exec_build(folder, out1, cwd, proc)", u"ok, reason, secs = (build_main([folder, out1]) == 0, u\"\", 0.0)", ("isolation", "doc")),
    (u"C14 元の包みを置いた作業の folder を cwd にする", u'cwd = os.path.join(d, "cwd")\n        os.makedirs(cwd)', u"cwd = d", ("doc",)),
    (u"C15 混ぜ物の組む命令が元の folder に掛かる", u"okm, _rm, _sm = exec_build(mf, mo, cwd, proc)", u"okm, _rm, _sm = exec_build(folder, mo, cwd, proc)", ("doc",)),
    (u"C16 run_process が標準のエラーを読まない", u'return p.returncode, p.stderr.decode("utf-8", "replace"), False', u'return p.returncode, u"", False', ("cmd",)),
    # ---- 書類 1 本
    (u"D1 出す folder の file の名を目次と照らさない", u"        if set(tree) != expected_names(index):\n            return declined_rec(rec, u\"出す folder の file の名が目次と合わない\", mixtures)\n        out2", u"        out2", ("docdecl",)),
    (u"D2 2 度が同じを見ない", u'rec[u"2 度が同じ"] = bool(ok2 and read_tree(out2) == tree)', u'rec[u"2 度が同じ"] = bool(ok2)', ("docdecl",)),
    (u"D3 2 度が同じを組む命令の失敗で偽にしない", u'rec[u"2 度が同じ"] = bool(ok2 and read_tree(out2) == tree)', u'rec[u"2 度が同じ"] = bool(read_tree(out2) == tree) if ok2 else True', ("docdecl",)),
    (u"D4 道筋が同じを見ない", u'rec[u"道筋が同じ"] = bool(same_tree is not None and same_tree == tree)', u'rec[u"道筋が同じ"] = True', ("docdecl",)),
    (u"D5 同じ process の字にタクソノミを入れない", u"        for k in FILE_KINDS:\n            out[rel_of(names[k])] = built[k]\n", u"        for k in FILE_KINDS:\n            pass\n", ("doc", "render", "docdecl")),
    (u"D6 組み直した包みに出す folder の字を使わない", u"B.write_package(rebuilt_pack(entries, tree), new_zip)", u"B.write_package(entries, new_zip)", ("doc",)),
    (u"D7 組み直した包みの置き換えの名に PublicDoc を付けない", u"return dict((PUBLICDOC + rel, data) for rel, data in tree.items())", u"return dict((rel, data) for rel, data in tree.items())", ("doc",)),
    (u"D8 元の包みの bytes に htm 以外も数える", u'        if B.is_public_htm(n):\n            htm[u"file"] += 1\n            htm[u"bytes"] += len(data)', u'        if n.startswith(PUBLICDOC):\n            htm[u"file"] += 1\n            htm[u"bytes"] += len(data)', ("doc",)),
    (u"D9 原稿の folder の目次を数えない", u'    add(u"目次", INDEX_FILE)\n', u"", ("doc",)),
    (u"D10 原稿の folder の合計に目次を足さない", u'sizes[u"合計 bytes"] = sum(v[u"bytes"] for v in sizes.values())\n    return sizes\n\n\ndef zero_stats', u'sizes[u"合計 bytes"] = sum(v[u"bytes"] for k, v in sizes.items() if k != u"目次")\n    return sizes\n\n\ndef zero_stats', ("doc",)),
    (u"D11 組む命令の秒を丸めない", u'rec[u"組む命令の秒"] = round(secs, 1)', u'rec[u"組む命令の秒"] = secs', ("doc",)),
    (u"D12 比べを便 XT0 の関数に任せず全部同じにする", u"        T.compare_into(rec, orig_outs, orig_facts, orig, new_outs, new_facts, new)\n", u"        T.compare_into(rec, orig_outs, orig_facts, orig, orig_outs, orig_facts, orig)\n", ("docdecl",)),
    (u"D13 断った書類に 2 度・道筋を真にする", u'    rec[u"2 度が同じ"] = rec[u"道筋が同じ"] = False\n    rec[u"混ぜ物"] = empty_mixes(mixtures)', u'    rec[u"2 度が同じ"] = rec[u"道筋が同じ"] = True\n    rec[u"混ぜ物"] = empty_mixes(mixtures)', ("docdecl",)),
    (u"D14 断った書類の混ぜ物を作った扱いにする", u'    rec[u"混ぜ物"] = empty_mixes(mixtures)\n    return rec\n\n\ndef process_doc', u'    rec[u"混ぜ物"] = [od([(u"種類", k), (u"作った", True), (u"違いを見つけた", True), (u"鳴り方が違う", True)]) for k in MIX_KINDS] if mixtures else []\n    return rec\n\n\ndef process_doc', ("docdecl",)),
    (u"D15 折り返し(folder に書けない形)の断りを例外にしない", u'        except Exception:                                  # noqa: BLE001\n            return declined_rec(rec, u"folder に書けない形", mixtures)', u"        except ZeroDivisionError:\n            return declined_rec(rec, u\"folder に書けない形\", mixtures)", ("docdecl",)),
    (u"D16 使い捨ての場所を消さない", u"    finally:\n        shutil.rmtree(d, ignore_errors=True)\n\n\n# ======================================================================================================\n# 数える", u"    finally:\n        pass\n\n\n# ======================================================================================================\n# 数える", ("doc",)),
    (u"D17 道具の既定の runner を使わない", u"orig, orig_outs, orig_facts = T.run_package(tool, orig_zip, d, \"orig\", runner)", u"orig, orig_outs, orig_facts = T.run_package(tool, orig_zip, d, \"orig\", runner or (lambda c, t: (u\"\", False)))", ("doc",)),
    (u"D18 組み直した包みを元と同じ名の zip にする", u'new_zip = os.path.join(d, "new.zip")', u'new_zip = os.path.join(d, "orig.zip")', ("doc",)),
    (u"D19 元の包みの 1 回を組み直した包みの 1 回にする", u'rec[u"組み直しの 1 回"] = new\n        T.compare_into', u'rec[u"組み直しの 1 回"] = orig\n        T.compare_into', ("docdecl",)),
    # ---- 混ぜ物
    (u"X1 N1 の数字の増やし方を 9 で直さない", u'return "1" if ch == "9" else chr(ord(ch) + 1)', u"return chr(ord(ch) + 1)", ("mix",)),
    (u"X2 N1 の数字を 0 から探す", u'm = re.search(r"[1-9]", content)', u'm = re.search(r"[0-9]", content)', ("mix",)),
    (u"X3 N1 の位置を中の字の頭にしない", u'return e["start"] + m.start() if m else None', u'return e["end"] - m.end() if m else None', ("mix",)),
    (u"X4 N1 の当て先を file の並びの逆から探す", u"for fi, i in B.num_pool(files):\n        _n, plain, F, _h = files[fi]", u"for fi, i in reversed(B.num_pool(files)):\n        _n, plain, F, _h = files[fi]", ("mix",)),
    (u"X5 N1 が書き戻す素の本文の file を最初の file にする", u'write_bytes(os.path.join(folder, index["htm"][fi]["text"]), (plain', u'write_bytes(os.path.join(folder, index["htm"][0]["text"]), (plain', ("mix",)),
    (u"X6 N1 が数字の無い行も当て先にする", u"        if at is not None:\n            write_bytes", u"        if True:\n            at = at if at is not None else F[i][\"start\"]\n            write_bytes", ("mix",)),
    (u"X7 N2 が別の混ぜ物の種類を呼ぶ", u"m = B.mix_tables(files, B.MIX_KINDS[0])", u"m = B.mix_tables(files, B.MIX_KINDS[1])", ("mix", "doc")),
    (u"X8 N2 が書き戻す表の file を最初の file にする", u'write_bytes(os.path.join(folder, index["htm"][fi]["tables"]), jdump(od([("F", F2), ("H", H2)])))', u'write_bytes(os.path.join(folder, index["htm"][0]["tables"]), jdump(od([("F", F2), ("H", H2)])))', ("mix",)),
    (u"X9 N3 と N4 の向きを入れ替える", u"return change_taxonomy(folder, index, 2 if n == 2 else 1)", u"return change_taxonomy(folder, index, 1 if n == 2 else 2)", ("mix", "doc")),
    (u"X10 N3・N4 が書き戻さない", u"    tables[kind] = T2\n", u"    pass\n", ("mix", "doc")),
    (u"X11 混ぜ物の folder を出す folder から複製する", u"shutil.copytree(folder, mf)", u"shutil.copytree(out1, mf)", ("doc",)),
    (u"X12 混ぜ物の包みに元の出す folder を使う", u"B.write_package(rebuilt_pack(entries, mtree), mz)", u"B.write_package(rebuilt_pack(entries, tree), mz)", ("doc", "docdecl")),
    (u"X13 混ぜ物の違いを見つけたを常に偽にする", u'item[u"違いを見つけた"] = not (tax and B.facts_same(orig_facts, mfacts))', u'item[u"違いを見つけた"] = False', ("doc",)),
    (u"X14 混ぜ物の違いを見つけたをタクソノミだけで決める", u'item[u"違いを見つけた"] = not (tax and B.facts_same(orig_facts, mfacts))', u'item[u"違いを見つけた"] = not tax', ("doc",)),
    (u"X15 混ぜ物の鳴り方が違うを常に偽にする", u'item[u"鳴り方が違う"] = not B.sounds_same(orig, mone)', u'item[u"鳴り方が違う"] = False', ("doc",)),
    (u"X16 混ぜ物の作れたを常に真にする", u"            if not changed:\n                continue", u"            if False:\n                continue", ("docdecl",)),
    (u"X17 混ぜ物の組む命令の失敗を見ない", u"            if not okm:\n                continue", u"            if False:\n                continue", ("docdecl",)),
    (u"X18 混ぜ物の出す folder を目次と照らさない", u"            if set(mtree) != expected_names(index):\n                continue\n", u"", ("docdecl",)),
    (u"X19 混ぜ物の例外を数えない", u"            except Exception:                              # noqa: BLE001\n                changed = False", u"            except ZeroDivisionError:\n                changed = False", ("docdecl",)),
    # ---- 数える・記録
    (u"T1 2 度が同じ書類の数に道筋を使う", u'twice += 1 if e[u"2 度が同じ"] else 0', u'twice += 1 if e[u"道筋が同じ"] else 0', ("totals",)),
    (u"T2 断らなかった書類を書類の数にする", u'(u"断らなかった書類", len(entries) - declined)', u'(u"断らなかった書類", len(entries))', ("totals",)),
    (u"T3 XP0-4 の分母を書類の数にする", u'(u"XP0-4 2 度が同じ書類", od([(u"書類", prod[u"2 度が同じ書類"]), (u"分母(断らなかった書類)", kept)]))', u'(u"XP0-4 2 度が同じ書類", od([(u"書類", prod[u"2 度が同じ書類"]), (u"分母(断らなかった書類)", prod[u"書類"])]))', ("totals",)),
    (u"T4 XP0-7 に断った書類も数える(原稿が元より大きいを数え違える)", u'bigger += 1 if e[u"原稿が元より大きい"] else 0', u'bigger += 1 if e[u"原稿が元より大きい"] or e[u"断った"] else 0', ("totals",)),
    (u"T5 混ぜ物の作れなかったも違いを見つけたに数える", u"found += 1 if m[u\"違いを見つけた\"] else 0\n                sound", u"found += 1\n                sound", ("totals",)),
    (u"T6 組む命令の秒の合計に断った書類も足す", u'        if e[u"組む命令の秒"] is not None:\n            secs += e[u"組む命令の秒"]', u'        secs += e[u"組む命令の秒"] or 0.0\n        secs += 1.0 if e[u"断った"] else 0.0', ("totals",)),
    (u"T7 原稿の folder の合計に file の数を足さない", u'                folder[g][f] += e[u"原稿の folder"][g][f]', u'                folder[g][f] += e[u"原稿の folder"][g][u"bytes"] if f == u"bytes" else 0', ("totals",)),
    (u"T8 verify が原稿が元より大きいの導き方を見ない", u'''        if d[u"原稿が元より大きい"] != (d[u"原稿の folder"][u"合計 bytes"] > d[u"元の包みの bytes"][u"合計 bytes"]):
            raise Stop(u"**原稿が元より大きいの導き方が違う。止める**")''', u"        pass", ("verify",)),
    (u"T9 verify が断った書類の 2 度・道筋を見ない", u' or d[u"2 度が同じ"] or d[u"道筋が同じ"])) or (not d[u"断った"] and', u")) or (not d[u\"断った\"] and", ("verify",)),
    (u"T10 verify が断った理由の有無を見ない", u" or (d[u\"断った\"] and not d[u\"断った理由\"]):", u":", ("verify",)),
    (u"T11 verify が混ぜ物の形を見ない", u'''        if len(d[u"混ぜ物"]) != (len(MIX_KINDS) if i <= dev_count else 0) or [m[u"種類"] for m in d[u"混ぜ物"]] != (list(MIX_KINDS) if i <= dev_count else []):
            raise Stop(u"**混ぜ物の形が違う。止める**")''', u"        pass", ("verify",)),
    (u"T12 check_clean が何も止めない", u"    T.check_clean(rec, text, secret)", u"    pass", ("clean", "verify")),
    (u"T13 build_record が混ぜ物を全部の書類に付ける", u"mixtures=(n <= dev_count)", u"mixtures=True", ("run",)),
    (u"T14 build_record が組む命令の入れ物を渡さない", u"process_doc(tool_p, p, tmp_root, runner, mixtures=(n <= dev_count), proc=proc)", u"process_doc(tool_p, p, tmp_root, runner, mixtures=(n <= dev_count), proc=InProc_for_mutant)", ("run", "e2e")),
    (u"T15 dev_run が混ぜ物を掛けない", u"r = process_doc(tool_p, p, tmp_root, runner, mixtures=True, proc=proc)", u"r = process_doc(tool_p, p, tmp_root, runner, mixtures=False, proc=proc)", ("devrun",)),
    (u"T16 build_record が進みを出さない", u"        if progress is not None:\n            progress(", u"        if False:\n            progress(", ("run", "e2e")),
    (u"T17 run が進みを渡さない", u"rec, secret = build_record(tool_p, docs, want, runner, sha_reader, tmp_root, want_version, want_sha, dev_count, proc, progress)", u"rec, secret = build_record(tool_p, docs, want, runner, sha_reader, tmp_root, want_version, want_sha, dev_count, proc, None)", ("e2e",)),
    (u"T18 dev_docs の既定の本数を変える", u"def dev_docs(docs_dir, count=DEV_COUNT):", u"def dev_docs(docs_dir, count=6):", ("devdocs",)),
    # ---- 封の字・配線
    (u"S1 予測の境の数を変える", u'("XP0-1", (58, None))', u'("XP0-1", (57, None))', ("seal",)),
    (u"S2 予測の境の数を変える(XP0-7)", u'("XP0-7", (50, None))', u'("XP0-7", (49, None))', ("seal",)),
    (u"S3 混ぜ物の名を変える", u'MIX_KINDS = (u"本文の数を変える", u"fact を抜く", u"ラベルを変える", u"計算の向きを返す")', u'MIX_KINDS = (u"本文の数を変える", u"fact を抜く", u"ラベルを替える", u"計算の向きを返す")', ("seal",)),
    (u"S4 封の commit の字を変える", u'SEAL_COMMIT = "c03a3348"', u'SEAL_COMMIT = "c03a3349"', ("seal",)),
    (u"S5 限界の字を落とす", u'    u"「EDINET の検査に通る」「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない。"]', u'    u"「EDINET の検査に通る」は、この便からは言えない。"]', ("seal",)),
    (u"S6 記録の path を変える", u'RECORD_REL = "fixtures/xbrl/cd8/pack_build_2026-11-22.json"', u'RECORD_REL = "fixtures/xbrl/cd8/pack_build_2026-11-23.json"', ("seal",)),
    (u"S7 時間の上限を変える(便 XT0 の字を受けず自分で持つ)", u"TIMEOUT_SEC = T.TIMEOUT_SEC", u"TIMEOUT_SEC = 60", ("seal",)),
    (u"S8 規則の年を変える", u"YEAR = T.YEAR", u'YEAR = "EDINET-2025"', ("seal",)),
    (u"S9 PublicDoc の場所を変える", u"PUBLICDOC = B.PUBLICDOC", u'PUBLICDOC = "XBRL/PublicDoc"', ("seal",)),
    (u"W1 別の門の規準の字を関数の名にする", u"def jload(data):", u"def mutate(x):\n    return x\n\n\ndef jload(data):", ("wiring",)),
    (u"W2 別の門の規準の字を説明文に書く", u"# ---- 原稿の folder の file の名\n", u"# ---- 原稿の folder の file の名(注入)\n", ("wiring",)),
    (u"W3 便 XT0 の script を他の便と重なる名で読む", u'TAXONOMY_NAME = "_xp0_taxonomy_build_2026_11_22"', u'TAXONOMY_NAME = "_xt0_taxonomy_build_2026_11_22"', ("wiring",)),
    (u"W4 前の便の関数を写す", u"def jdump(o):", u"def build_text(plain, F, H):\n    return plain\n\n\ndef jdump(o):", ("wiring",)),
    (u"W5 socket を import する", u"import subprocess\n", u"import subprocess\nimport socket\n", ("wiring",)),
    (u"W6 zipfile を import する", u"import subprocess\n", u"import subprocess\nimport zipfile\n", ("wiring",)),
    (u"W7 便 XT0 の Stop を使わない", u"W = T.W ", u'W = _load_sibling("_xp0_other_wall", "xbrl_tag_wall_2026-11-21.py")  # ', ("wiring",)),
    (u"W8 subprocess を使う関数を足す", u"def decline_reason(stderr_text):", u"def sneak(c):\n    return subprocess." + u"run(c)\n\n\ndef decline_reason(stderr_text):", ("isolation",)),
    (u"W9 便 XB0 の混ぜ物の関数を呼ばず自分で書く", u"m = B.mix_tables(files, B.MIX_KINDS[0])", u"m = (0, files[0][2][1:], files[0][3])", ("mix", "wiring")),
)
#: 黙ることが分かっている変異(理由つき)
SILENT_BY_DESIGN = {
    u"R4 目次の相対の名の先頭の / を断らない": u"先頭の / は split した最初の部分が空になるので、空の部分を断る規則が同じ名を断る(2 つの規則が重なる。どちらかだけ外しても名は断られる)",
    u"X17 混ぜ物の組む命令の失敗を見ない": u"組む命令が失敗すると出す folder が無く、読んだ file の集まりが空になって目次と合わず、出す folder の名の照合が同じ混ぜ物を作れなかったにする(2 つの規則が重なる)"}


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"folder": folder_problems, u"render": render_problems, u"cmd": command_problems, u"mix": mix_problems, u"doc": doc_problems, u"docdecl": decline_doc_problems,
             u"totals": totals_problems, u"tools": tools_problems, u"devdocs": dev_docs_problems, u"run": run_problems, u"verify": verify_problems, u"clean": clean_problems,
             u"e2e": e2e_problems, u"devrun": devrun_problems}
    if name == u"decl_doc":
        name = u"docdecl"
    if name in table:
        return table[name](mod)
    if name == u"wiring":
        return import_problems(src)
    if name == u"isolation":
        return isolation_problems(src)
    if name == u"proc":
        return proc_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"folder", u"render", u"cmd", u"mix", u"doc", u"docdecl", u"totals", u"tools", u"devdocs", u"run", u"verify", u"clean", u"e2e", u"devrun", u"wiring", u"isolation", u"proc")


def run_mutants(table=MUTANTS, only=None):
    base = read(SCRIPT_REL)
    out_ = []
    for name, old, new, checks in table:
        if only is not None and name not in only:
            continue
        src = base
        assert base.count(old) == 1, (name, base.count(old))
        src = src.replace(old, new)
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
        for old, new in ((u"| XP0-1(主) | 全部同じ書類は 58 本以上", u"| XP0-1(主) | 全部同じ書類は 57 本以上"), (u"開発の 5 本 × 4 種類 = 20 個", u"開発の 5 本 × 4 種類 = 21 個"), (u"**N1 本文の数を変える**", u"**N1 本文の数を消す**"),
                         (u"`python3 -I <script> build <原稿の folder> <出す folder>`", u"`python3 <script> build <原稿の folder> <出す folder>`"), (u"便 XG0 の封 §1 と同じ 67 本", u"便 XG0 の封 §1 と同じ 66 本"),
                         (u"書類は 67 本(違えば script は止まる)", u"書類は 66 本(違えば script は止まる)"), (u"| XP0-7 | 原稿の folder の bytes の合計が、元の `.htm` と `.xsd`・linkbase の bytes の合計より大きい書類は 50 本以上", u"| XP0-7 | 原稿の folder の bytes の合計が、元の `.htm` と `.xsd`・linkbase の bytes の合計より大きい書類は 51 本以上"),
                         (u"| XP0-4 | 2 度が同じ書類は、断らなかった書類の全部", u"| XP0-4 | 2 度が同じ書類は、断らなかった書類の半分")):
            self.assertGreaterEqual(seal.count(old), 1, old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"pack_build", body)


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_good_order_is_green_and_bad_orders_are_red(self):
        pr = X.load_helpers()
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


class FolderTest(unittest.TestCase):
    def test_b_1_peel_writes_the_manuscript_folder_and_holds_no_original_text(self):
        self.assertEqual([], folder_problems())

    def test_b_2_build_reads_only_the_folder_and_writes_the_same_bytes(self):
        self.assertEqual([], render_problems())

    def test_b_3_the_build_command_in_a_real_process(self):
        self.assertEqual([], proc_problems())

    def test_b_4_the_command_line_and_the_way_the_process_is_called(self):
        self.assertEqual([], command_problems())

    def test_b_5_the_four_mixtures_change_one_place_on_disk(self):
        self.assertEqual([], mix_problems())

    def test_b_6_the_fake_pack_covers_every_form(self):
        u"""作り物の包みが頭の部・自己閉じでない nonNumeric・0 だけの nonFraction・0 でない nonFraction・CRLF・下の folder の htm・マニフェスト・画像・``.xbrl``・AuditDoc・weight -1 の arc を含む。"""
        self.assertIn(u"<ix:header>", HTM_A)
        self.assertIn(u"<ix:nonNumeric", HTM_A)
        self.assertIn(u">0</ix:nonFraction>", HTM_B)
        self.assertIn(u">1,234</ix:nonFraction>", HTM_B)
        self.assertIn(u"\r\n", HTM_B)
        self.assertIn(u"/sub/", HTM_SUB_NAME)
        self.assertTrue(HTM_A_NAME < HTM_B_NAME < HTM_SUB_NAME)
        self.assertIn(u'weight="-1"', X.CAL_ALT)
        self.assertEqual(len(KINDS), 6)
        self.assertEqual(len(MS.MIX_KINDS), 4)
        with Temp() as d:
            zp = os.path.join(d, "p.zip")
            make_pack(zp)
            with zipfile.ZipFile(zp) as z:
                names = z.namelist()
        self.assertTrue(any(n.endswith(".xbrl") for n in names) and any("AuditDoc" in n for n in names) and any(n.endswith("manifest_PublicDoc.xml") for n in names) and any(n.endswith(".png") for n in names))
        htm_names = [n for n in names if n.endswith(".htm")]
        self.assertEqual(len(htm_names), 3)
        self.assertNotEqual(htm_names, sorted(htm_names))


class DocTest(unittest.TestCase):
    def test_c_1_the_tool_check(self):
        self.assertEqual([], tools_problems())

    def test_c_2_one_document_goes_through_with_a_fake_tool_and_a_fake_process(self):
        self.assertEqual([], doc_problems())

    def test_c_3_declines_failures_and_the_mixtures_that_could_not_be_made(self):
        self.assertEqual([], decline_doc_problems())

    def test_c_4_totals_and_the_judged_numbers(self):
        self.assertEqual([], totals_problems())

    def test_c_5_build_record_with_fake_documents_and_a_fake_tool(self):
        self.assertEqual([], run_problems())

    def test_c_6_run_record_check_with_fake_tools_and_a_fake_cache(self):
        self.assertEqual([], e2e_problems())

    def test_c_7_the_record_check_catches_tampering(self):
        self.assertEqual([], verify_problems())

    def test_c_8_the_forbidden_checks_stop_planted_content(self):
        self.assertEqual([], clean_problems())

    def test_c_9_the_dev_entry_runs_only_the_first_five_documents(self):
        self.assertEqual([], devrun_problems())
        self.assertEqual([], dev_docs_problems())

    def test_c_10_the_real_record_when_present_is_clean_and_consistent(self):
        p = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(p):
            self.skipTest(u"記録は本番の走りの後に書かれる。記録の中身の検査は結果の門に置く")
        text = read(RECORD_REL)
        MS.verify_record(json.loads(text, object_pairs_hook=od), text)


class WiringTest(unittest.TestCase):
    def test_e_1_imports_and_the_earlier_functions_are_called_not_copied(self):
        self.assertEqual([], import_problems())

    def test_e_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        for extra in (u"\nimport socket\n", u"\nimport zipfile\n", u"\nimport csv\n", u"\nfrom adapters.xbrl import instance\n", u"\nX = os.system('a')\n", u"\ndef select_docs(a, b):\n    return None\n",
                      u"\ndef load_package(a):\n    return None\n", u"\ndef run_doc(a):\n    return None\n", u"\ndef strip_tables(a):\n    return None\n"):
            self.assertNotEqual([], import_problems(base + extra), extra)
        self.assertNotEqual([], import_problems(base.replace(u"W.order_sha256(", u"order_sha256(")))
        self.assertNotEqual([], import_problems(base.replace(u"B.load_package(", u"load_package(")))
        self.assertNotEqual([], import_problems(base.replace(u"T.strip_tables(", u"strip_tables(")))

    def test_e_3_the_build_side_reads_nothing_but_the_folder(self):
        self.assertEqual([], isolation_problems())

    def test_e_4_the_isolation_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        for old, new in ((u"def render_folder(folder):", u"def render_folder(folder, original=None):"), (u"def build_main(args):", u"def build_main(args, more=None):"),
                         (u'        index = jload(read_bytes(os.path.join(folder, INDEX_FILE)))\n        out = od()', u'        data = open(folder)\n        index = jload(read_bytes(os.path.join(folder, INDEX_FILE)))\n        out = od()'),
                         (u"def render_folder(folder):\n", u"def render_folder(folder):\n    entries = B.load_package(folder)\n"), (u"ok, reason, secs = exec_build(folder, out1, cwd, proc)", u"ok, reason, secs = (build_main([folder, out1]) == 0, u'', 0.0)")):
            self.assertEqual(base.count(old), 1, old)
            self.assertNotEqual([], isolation_problems(base.replace(old, new)), old)
        self.assertNotEqual([], isolation_problems(base + u"\ndef reader(p):\n    return ET.parse(p)\n"))

    def test_e_5_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_e_6_the_script_leaves_sys_modules_as_it_found_them_except_its_own_earlier_script_names(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_pack_build_script_for_sysmodules_check")
        changed = [k for k in before if sys.modules.get(k) is not before[k]]
        self.assertEqual([], changed)
        self.assertEqual(mod.T.__name__, TAXONOMY_NAME)
        self.assertIs(mod.B, mod.T.B)
        self.assertIs(mod.V, mod.T.V)
        self.assertIs(mod.W, mod.T.W)
        self.assertIs(mod.Stop, mod.V.Stop)
        del mod

    def test_e_7_the_default_place_is_outside_the_repo_and_the_gate_never_opens_it(self):
        top = os.path.realpath(REPO)
        self.assertFalse(os.path.realpath(MS.DOCS_DIR).startswith(top + os.sep))
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(select_docs|run|check|build_record|dev_docs|dev_run)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"docs|rec_path|\*\*kw|rp|\bd\b|\btool\b|\*\*args|\*\*a2|\*\*a3", m.group(2)), m.group(0))

    def test_e_8_the_gate_calls_subprocess_only_for_git_and_for_the_build_command(self):
        src = read(GATE_REL)
        calls = re.findall(r"subprocess\.(\w+)", src)
        self.assertEqual(set(calls), {"run", "PIPE", "TimeoutExpired"})
        runs = [m.group(1) for m in re.finditer(r"subprocess\.run\(([^)]*)\)", src)]
        for r in runs:
            self.assertTrue(r.startswith(u'["git"') or r.startswith(u"list(cmd"), r)
        self.assertGreaterEqual(sum(1 for r in runs if r.startswith(u"list(cmd")), 1)


class MutantTest(unittest.TestCase):
    def test_f_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
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

    def test_f_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ALL_CHECKS:
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
