# -*- coding: utf-8 -*-
"""封 docs/XBRL_TAG_WALL_SEAL_2026-11-21.md(XG0 ― 有価証券報告書の計算書の行で、行の字と標準タクソノミの表だけで要素が 1 つに決まる行はどれだけか)の封の門。

**この門は置き場を読まない**(書類の置き場 ``~/.cache/audit-core/edinet/``・標準ラベルの置き場は 1 度も開かない。作り物の zip と作り物のラベルの linkbase だけを使う)。通信しない。

**この門が縛るもの**

1. 封の字: 封の commit(3374e504)・封の file が commit した blob と同じ・67 本・path・role の決め(末尾が Label/label の和集合 = L2・標準の role だけ = L1)・類 U/A/W/N の字・予測の境の数・
   (a)〜(d) の字が script の定数と同じ。
2. engine は封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 作り物の zip(作り物の ``_ixbrl.htm`` と ``.xsd`` の名)と作り物のラベルの linkbase で、行の切り方 → 分母の条件 (a)〜(d) → 類分け → L2 と L1 → 書類ごとの率、を本物の関数(engine の
   ``_TR_RE``・``_row_label``・``parse_label_linkbase``・``_read_taxonomy_file`` を含む)のまま通す(手で数えた値と照らす)。
4. 記録の禁止の検査(欄・EDINET コードの形・docID の形・材料の docID・要素の名・行の字)が作り物で止まる。書く前と書いた後。67 本でなければ止まる。
5. script の import は標準ライブラリと engine の 2 module(instance・verify_document)だけ。通信しない。engine の関数を写さず呼ぶ。
6. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
黙る変異は ``SILENT_BY_DESIGN`` に理由とともに置き、「黙ること」自体を別の試験で縛る。
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
    mod = types.ModuleType("xbrl_tag_wall_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_TAG_WALL_SEAL_2026-11-21.md"
SEAL_COMMIT_SHORT = "3374e504"                # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_tag_wall_2026-11-21.py"
GATE_REL = "tests/measure/test_xbrl_tag_wall_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/tag_wall_2026-11-21.json"
MS = load_module(SCRIPT_REL, "xbrl_tag_wall_script_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_tag_wall_seal")       # 順序・履歴の部品。門としては走らせない
ORDER_FILES = (SCRIPT_REL, GATE_REL)          # 記録の順序は記録が在るときの結果の門に置く
od = collections.OrderedDict


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_of(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_or_none(rel):
    return sha_of(rel) if os.path.exists(os.path.join(ROOT, rel)) else None


def guard(fn, *a, **kw):
    u"""fn が例外(``SystemExit`` を含む)を投げたら、その例外の型の名前の字を返す。違いを見るための道具。"""
    try:
        return fn(*a, **kw)
    except BaseException as exc:                # noqa: BLE001
        return [u"例外: %s" % type(exc).__name__]


def stops(ms, fn, *a, **kw):
    u"""fn が ``ms.Stop`` を投げれば True。投げなければ False。別の例外は投げ直す。"""
    try:
        fn(*a, **kw)
    except ms.Stop:
        return True
    return False


class Temp(object):
    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="xg0_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


# ======================================================================== 作り物のラベルの linkbase
LB_HEAD = (u'<?xml version="1.0" encoding="UTF-8"?>\n<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" '
           u'xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xml="http://www.w3.org/XML/1998/namespace"><link:labelLink xlink:type="extended">')
LB_TAIL = u"</link:labelLink></link:linkbase>"
R_STD = "http://www.xbrl.org/2003/role/label"
R_VERBOSE = "http://www.xbrl.org/2003/role/verboseLabel"
R_TOTAL = "http://www.xbrl.org/2003/role/totalLabel"
R_DOC = "http://www.xbrl.org/2003/role/documentation"
R_GUIDE = "http://www.xbrl.org/2003/role/labelGuide"          # label を含むが末尾が Label/label でない role(L2 に入れない)


def linkbase(entries):
    u"""entries = [(要素の完全な id, role, 字, lang)] → 作り物のラベル linkbase の bytes。loc → labelArc → label の 3 つを本物のラベル file と同じ形で。"""
    parts = [LB_HEAD]
    for i, (full, role, text, lang) in enumerate(entries):
        parts.append(u'<link:loc xlink:type="locator" xlink:href="x.xsd#%s" xlink:label="loc_%d"/>' % (full, i))
        parts.append(u'<link:label xlink:type="resource" xlink:label="lab_%d" xlink:role="%s" xml:lang="%s">%s</link:label>' % (i, role, lang, text))
        parts.append(u'<link:labelArc xlink:type="arc" xlink:from="loc_%d" xlink:to="lab_%d"/>' % (i, i))
    parts.append(LB_TAIL)
    return u"".join(parts).encode("utf-8")


P = u"jppfs_cor_"
FAKE_ENTRIES = [
    (P + u"CashAndDeposits", R_STD, u"現金及び預金", "ja"), (P + u"CashAndDeposits", R_STD, u"Cash and deposits", "en"),
    (P + u"FeeA", R_STD, u"営業雑費", "ja"), (P + u"FeeB", R_STD, u"営業雑費", "ja"),                     # 同じ字の要素が 2 つ(A の元)
    (P + u"Sales1", R_STD, u"売上", "ja"), (P + u"Sales2", R_STD, u"営業収益", "ja"),                    # 行は Sales2 と付いていて、字「売上」は Sales1 の字(W の元)
    (P + u"Assets", R_STD, u"資産", "ja"), (P + u"Assets", R_TOTAL, u"資産合計", "ja"),                  # 合計の role でだけ当たる(L2 で U・L1 で N)
    (P + u"DtaQ", R_STD, u"繰延税金資産", "ja"), (P + u"DtaR", R_STD, u"繰延税金資産(その他)", "ja"), (P + u"DtaR", R_VERBOSE, u"繰延税金資産", "ja"),   # 冗長の role で同じ字(L2 で A)
    (P + u"SecWs", R_STD, u"有価 証券", "ja"),                                                            # 字の中に空白(表の側の空白の除き)
    (P + u"InvSec", R_STD, u"投資有価証券(注)", "ja"),                                                    # 行の側は全角の括弧(行の側の NFKC)
    (P + u"DocE", R_STD, u"文書", "ja"), (P + u"DocE", R_DOC, u"文書の説明", "ja"),                       # role の末尾が Label でない(使わない)
    (P + u"DocE", R_GUIDE, u"文書の説明", "ja")]                      # role に label を含むが末尾が Label/label でない(使わない。「abel を含む」で選ぶと行 DOC が N から U に変わる)
FAKE_LABELS = linkbase(FAKE_ENTRIES)
#: 提出者が自分の書類に付けたラベル(zip の中の _lab.xml。使ってはならない側)
SUBMITTER_LABELS = linkbase([(P + u"NoLab1", R_STD, u"未登録の勘定A", "ja")])
#: 手で数えた表の大きさ(L2 の role は label・verboseLabel・totalLabel の 3 つ。documentation・labelGuide は除く。labelGuide の行は字が documentation の行と同じなので表の大きさは変わらない)
HAND_TABLE = od([("roles", 3), ("l2", 11), ("l1", 10)])


# ======================================================================== 作り物の書類
NFTAG = u'<ix:nonFraction name="%s" contextRef="c1" unitRef="JPY" decimals="-6" scale="6">100</ix:nonFraction>'
SUB1 = u"jpcrp030000-asr-001_E99991-000"
SUB2 = u"jpcrp030000-asr-001_E99992-000"


def row(label, names):
    u"""``label`` を左端のセルに置き、names の 1 つにつき ix:nonFraction のセルを 1 つ(label が None なら左端に数字だけのセルと空のセル)。"""
    left = u"<td>%s</td>" % label if label is not None else u"<td></td><td>1</td>"
    return u"<tr>" + left + u"".join(u"<td>%s</td>" % (NFTAG % n) for n in names) + u"</tr>"


def two(n):
    return [n, n]


def table(rows):
    return u"<html><body><table>" + u"".join(rows) + u"</table></body></html>"


K = dict(
    U=lambda: row(u"現金及び預金", two(u"jppfs_cor:CashAndDeposits")),
    A=lambda: row(u"営業雑費", two(u"jppfs_cor:FeeB")),
    W=lambda: row(u"売上", two(u"jppfs_cor:Sales2")),
    W2=lambda: row(u"営業雑費", two(u"jppfs_cor:Sales2")),                                              # 字が 2 つの要素に当たり、どちらでもない(W。A ではない)
    N=lambda i: row(u"未登録の勘定" + u"ABCDZ"[i], two(u"jppfs_cor:NoLab%d" % (i + 1))),
    TOT=lambda: row(u"資産合計", two(u"jppfs_cor:Assets")),
    VB=lambda: row(u"繰延税金資産", two(u"jppfs_cor:DtaQ")),
    VB2=lambda: row(u"繰延税金資産", two(u"jppfs_cor:DtaR")),
    WS=lambda: row(u"有価証券", two(u"jppfs_cor:SecWs")),
    NF=lambda: row(u"投資有価証券（注）", two(u"jppfs_cor:InvSec")),
    DOC=lambda: row(u"文書の説明", two(u"jppfs_cor:DocE")),
    XB=lambda: row(u"現金及び預金", [u"jppfs_cor:CashAndDeposits", u"jppfs_cor:Sales1"]),           # 名が 2 つ
    XBD=lambda: row(None, [u"jppfs_cor:P1", u"jppfs_cor:Q1"]),                                         # 名が 2 つで字も無い(b だけに数える)
    XC=lambda: row(u"役員の名称", two(u"jpcrp_cor:Exec")),                                              # jppfs 以外
    XC2=lambda: row(u"提出者の科目", two(SUB1 + u":Cust")),                                             # 提出者別のタグ
    XCD=lambda: row(None, two(u"abc_cor:Z")),                                                           # jppfs 以外で字も無い(c だけに数える)
    XCI=lambda: row(u"連結の科目", two(u"jpigp_cor:Z")),
    XD=lambda: row(None, two(u"jppfs_cor:FooBar")),                                                     # 字が無い
    X0=lambda: u"<tr><td>見出しだけの行</td><td>注記</td></tr>")                                       # ix:nonFraction が無い(数えない)

OUT_TAGS = (u"<p>" + NFTAG % u"jpdei_cor:Dei" + u"</p>")                       # 表の外の標準 1 つ
OUT_SUB3 = u"".join(u"<p>" + NFTAG % (SUB1 + u":Custom") + u"</p>" for _ in range(3))
OUT_NONNUM = u"".join(u'<p><ix:nonNumeric name="jpcrp_cor:Text%d" contextRef="c1">x</ix:nonNumeric></p>' % i for i in range(5))   # nonNumeric は数えない


def fake_doc_texts():
    u"""作り物の 4 書類の ``_ixbrl.htm`` の字(書類ごとに 2 file に分ける)。"""
    d1a = table([K["U"](), K["U"](), K["U"](), K["A"](), K["A"](), K["W"](), K["N"](0)]) + OUT_TAGS + OUT_NONNUM
    d1b = table([K["N"](1), K["N"](2), K["N"](3), K["TOT"](), K["TOT"](), K["XB"](), K["XC"](), K["XC"](), K["XD"]()]) + OUT_SUB3
    d2a = table([K["VB"](), K["VB2"](), K["VB2"](), K["WS"](), K["WS"](), K["WS"](), K["NF"](), K["DOC"](), K["W2"]()])
    d2b = table([K["XBD"](), K["XC2"](), K["XCD"](), K["X0"](), K["X0"](), K["X0"]()]) + u"<p>" + NFTAG % u"jpcrp_cor:Out" + u"</p>"
    d3a = table([K["XCI"]()])
    d3b = u"<p>" + NFTAG % (SUB1 + u":Only") + u"</p>"
    d4a = table([K["U"]() for _ in range(9)] + [K["N"](4)])
    d4b = u"<html></html>"
    return [(d1a, d1b), (d2a, d2b), (d3a, d3b), (d4a, d4b)]


#: 手で数えた値(字で書く。script に作らせない)。(標準, 提出者別, b, c, d, L2 の U A W N, L1 の U A W N, U の率 L2)
HAND_DOCS = [
    dict(std=33, sub=3, b=1, c=2, d=1, l2=(5, 2, 1, 4), l1=(3, 2, 1, 6), rate=41.7),
    dict(std=21, sub=4, b=1, c=2, d=0, l2=(4, 3, 1, 1), l1=(5, 0, 3, 1), rate=44.4),
    dict(std=2, sub=1, b=0, c=1, d=0, l2=(0, 0, 0, 0), l1=(0, 0, 0, 0), rate=None),
    dict(std=20, sub=0, b=0, c=0, d=0, l2=(9, 0, 0, 1), l1=(9, 0, 0, 1), rate=90.0)]
HAND_TOTAL = dict(std=76, sub=8, rows=31, b=2, c=5, d=1, l2=(18, 5, 2, 6), l1=(17, 2, 4, 8), docs_rows=3, docs_zero=1, docs_u90=1)
HAND_RATES = dict(sub_tag=9.5, u2=58.1, u1=54.8, diff=3.2, a=16.1, w=6.5)
STEMS = ["S1FAKE01", "S1FAKE02", "S1FAKE03", "S1FAKE04"]
ORDER_SHA = hashlib.sha256(u"\n".join(STEMS).encode("utf-8")).hexdigest()


def xsd(stem_no, folder="PublicDoc", prefix="jpcrp030000-asr-001"):
    return "XBRL/%s/%s_E9999%d-000_2026-03-31_01_2026-06-30.xsd" % (folder, prefix, stem_no)


def make_zip(path, no, texts, submitter_labels=False, folder="PublicDoc", prefix="jpcrp030000-asr-001", decoy=True):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(xsd(no, folder, prefix), b"<schema/>")
        for i, t in enumerate(texts):
            z.writestr("XBRL/PublicDoc/010%d010_honbun_%s_E9999%d-000_ixbrl.htm" % (i, prefix, no), t.encode("utf-8"))
        if decoy:         # PublicDoc の外の ixbrl は読まない
            z.writestr("XBRL/AuditDoc/0000_audit_ixbrl.htm", table([K["U"](), K["U"]()]).encode("utf-8"))
        if submitter_labels:
            z.writestr("XBRL/PublicDoc/%s_E9999%d-000_lab.xml" % (prefix, no), SUBMITTER_LABELS)


def make_docs_dir(d, count=4, mix=False):
    u"""作り物の置き場。有価証券報告書 ``count`` 本(S1FAKE01…)・別の様式の zip 1 本・有価証券報告書の名の xsd が AuditDoc にだけ在る zip 1 本(どちらも数えない)。"""
    texts = fake_doc_texts()
    for i in range(count):
        make_zip(os.path.join(d, STEMS[i] + ".zip"), i + 1, texts[i], submitter_labels=(mix and i == 0))
    make_zip(os.path.join(d, "S1OTHER1.zip"), 8, texts[0], prefix="jpsps070000-xxx-001")
    make_zip(os.path.join(d, "S1AUDIT1.zip"), 9, texts[0], folder="AuditDoc")
    return d


def acc_tuple(acc):
    return dict(std=acc["std"], sub=acc["sub"], b=acc["b"], c=acc["c"], d=acc["d"], l2=tuple(acc["l2"].values()), l1=tuple(acc["l1"].values()))


def patched(ms, label_bytes=FAKE_LABELS):
    u"""``read_label_bytes`` を作り物のラベルに差し替える(本物の sha256 の照合は別の検査で通す)。module の実体に届くよう ms の属性を替える。"""
    ms.read_label_bytes = lambda d: (label_bytes, hashlib.sha256(label_bytes).hexdigest())
    return ms


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XG0-1", (None, 5)), ("XG0-2", (60, 85)), ("XG0-3", (None, 5)), ("XG0-4", (5, 25)), ("XG0-5", (None, 10)), ("XG0-6", (5, None))])
SEAL_BOUND_TEXT = od([("XG0-1", u"5% 以下"), ("XG0-2", u"60% 以上 85% 以下"), ("XG0-3", u"5% 以下"), ("XG0-4", u"5% 以上 25% 以下"), ("XG0-5", u"10 本以下"), ("XG0-6", u"5 ポイント以上低い")])


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out.append(u"script の封の commit・path・記録の path が門と違う")
    if ms.DOCS_WANT != 67 or u"**67 本**" not in seal:
        out.append(u"書類の本数 67 が封と違う")
    if ms.DOCS_DIR != os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet") or u"`~/.cache/audit-core/edinet/*.zip`" not in seal:
        out.append(u"書類の置き場が封と違う")
    if ms.XSD_PREFIX != u"jpcrp030000-asr" or ms.PUBLICDOC != u"XBRL/PublicDoc/" or u"`jpcrp030000-asr` で始まる" not in seal:
        out.append(u"書類の選び方(xsd の名)が封と違う")
    if (ms.TAXONOMY_DIR != os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-taxonomy", "2025-11-01") or ms.LABEL_FILE != u"jppfs_2025-11-01_lab.xml"
            or u"`~/.cache/audit-core/edinet-taxonomy/2025-11-01/jppfs_2025-11-01_lab.xml`" not in seal):
        out.append(u"標準のラベルの置き場・file が封と違う")
    if ms.STANDARD_ROLE != u"http://www.xbrl.org/2003/role/label" or u"role が `http://www.xbrl.org/2003/role/label`(標準)だけ" not in seal or ms.STANDARD_ROLE != ms.I.STANDARD_LABEL_ROLE:
        out.append(u"表 L1 の role が封か engine と違う")
    if tuple(ms.ROLE_SUFFIXES) != (u"Label", u"label") or u"末尾が `Label` か `label` のもの全部" not in seal:
        out.append(u"表 L2 の role の決めが封と違う")
    if ms.STATEMENT_PREFIX != u"jppfs_cor" or u"その接頭辞が `jppfs_cor`" not in seal:
        out.append(u"(c) の接頭辞が封と違う")
    for must in (u"(a) 1 つ以上在り", u"(b) 全部が同じ 1 つの名", u"(d) engine の `_row_label(row)` が字を返す行", u"空白の字(`\\s` と U+00A0)を全部除く",
                 u"提出者が自分の書類に付けたラベルの file", u"は **使わない**", u"NFKC にそろえ"):
        if must not in seal:
            out.append(u"封に字が無い: %s" % must)
    lines = dict((m.group(1), m.group(2)) for m in re.finditer(r"^\s*- \*\*([UAWN])\*\*(?:（[^）]*）|\([^)]*\))?: (.*)$", seal, re.M))
    if sorted(lines) != sorted(ms.CLASSES) or list(ms.CLASSES) != [u"U", u"A", u"W", u"N"]:
        out.append(u"類の名が封と違う(U・A・W・N)")
    else:
        if u"ちょうど 1 つで、それが E" not in lines["U"] or u"2 つ以上で、E を含む" not in lines["A"] or u"1 つ以上で、E を含まない" not in lines["W"] or u"当たる要素が無い" not in lines["N"]:
            out.append(u"類の字(当たる要素の数と E を含むか)が封と違う")
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS):
        out.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [ln for ln in seal.splitlines() if ln.startswith(u"| %s |" % k)]
        if len(row_) != 1 or t not in row_[0]:
            out.append(u"封の予測の行の字が違う: %s" % k)
    if ms.U_DOC_THRESHOLD_PCT != 90 or u"U の率が 90% 以上の書類は 10 本以下" not in seal:
        out.append(u"XG0-5 の 90% が封と違う")
    if u"engine の指紋" not in seal or u"材料の並びの sha256" not in seal or u"ラベルの file の sha256" not in seal:
        out.append(u"封に記録の項目が無い")
    for rel in (SCRIPT_REL, RECORD_REL, GATE_REL):
        if rel not in seal:
            out.append(u"封に path が無い: %s" % rel)
    sec7 = seal.split(u"## §7", 1)[-1]
    if len(ms.LIMITS) != 4 or u"専用の道具が組んだ後の字" not in sec7 or u"無作為ではない" not in sec7 or u"期・連結か個別か" not in sec7 or u"「XBRL を作れる」" not in sec7:
        out.append(u"限界の 4 行が封 §7 と違う")
    return out


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
    u"""封 ⊏ script・この門(足した commit が封の後)。未 commit は赤。"""
    others = list(ORDER_FILES) if others is None else others
    return list(PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others))


def engine_zero_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core"], stdout=subprocess.PIPE, universal_newlines=True)
    return [u"engine が封の後に変わっている: %s" % ln for ln in rc.stdout.splitlines() if ln.strip()]


# ======================================================================== 2. 純関数
def pure_problems(ms=None):
    u"""正規化・率・標準の判定・行の状態・類分けを、手で決めた値と照らす。"""
    ms = ms or MS
    out = []
    for raw, want in ((u"現金 及び\u00a0預金", u"現金及び預金"), (u"投資有価証券（注）", u"投資有価証券(注)"), (u"ＡＢＣ\u3000１", u"ABC1"), (u"普通", u"普通")):
        if ms.norm_label(raw) != want:
            out.append(u"norm_label(%r) が %r でない" % (raw, ms.norm_label(raw)))
    for n, d, want in ((1, 16, 6.3), (1, 8, 12.5), (5, 12, 41.7), (1, 30, 3.3), (-1, 30, -3.3), (0, 5, 0.0), (1, 0, None), (3, 3, 100.0)):
        if ms.pct1(n, d) != want:
            out.append(u"pct1(%d, %d) が %s(手で数えた値は %s)" % (n, d, ms.pct1(n, d), want))
    for p, want in ((u"jppfs_cor", True), (u"jpcrp_cor", True), (u"jpigp_cor", True), (u"jpdei_cor", True), (SUB1, False), (u"abc_cor", False), (u"jpcrp_cor_x", False), (u"", False)):
        if ms.is_standard(p) != want:
            out.append(u"is_standard(%r) が %s でない" % (p, want))
    cases = [
        (K["U"](), ("ok", u"現金及び預金", u"CashAndDeposits")),
        (K["NF"](), ("ok", u"投資有価証券(注)", u"InvSec")),
        (K["XB"](), ("b",)), (K["XBD"](), ("b",)),
        (K["XC"](), ("c",)), (K["XC2"](), ("c",)), (K["XCD"](), ("c",)), (K["XCI"](), ("c",)),
        (K["XD"](), ("d",)), (K["X0"](), ("none",)),
        (u"<tr><td>勘定</td><td>%s</td><td>%s</td></tr>" % (NFTAG % u"jppfs_cor:CashAndDeposits", NFTAG % u"jppfs_cor:CashAndDeposits"), ("ok", u"勘定", u"CashAndDeposits")),
        (u'<tr><td>勘定</td><td><ix:nonNumeric name="jppfs_cor:X" contextRef="c">t</ix:nonNumeric></td></tr>', ("none",))]
    for rowtext, want in cases:
        got = ms.row_status(rowtext)
        if got != want:
            out.append(u"row_status が %s(手で決めた値は %s): %s" % (got, want, rowtext[:40]))
    tabs = {u"甲": {u"E1"}, u"乙": {u"E1", u"E2"}, u"丙": {u"E3", u"E4", u"E5"}}
    for T, E, want in ((u"甲", u"E1", "U"), (u"甲", u"E2", "W"), (u"乙", u"E2", "A"), (u"乙", u"E9", "W"), (u"丙", u"E9", "W"), (u"丙", u"E5", "A"), (u"丁", u"E1", "N"), (u"", u"E1", "N")):
        if ms.classify(T, E, tabs) != want:
            out.append(u"classify(%s, %s) が %s(手で決めた値は %s)" % (T, E, ms.classify(T, E, tabs), want))
    return out


# ======================================================================== 3. ラベルの表
def tables_problems(ms=None):
    ms = ms or MS
    out = []
    roles = ms.label_roles(FAKE_LABELS)
    if roles != sorted([R_STD, R_VERBOSE, R_TOTAL]):
        out.append(u"role の選びが違う: %s" % roles)
    l2, l1 = ms.label_tables(FAKE_LABELS)
    if (len(roles), len(l2), len(l1)) != tuple(HAND_TABLE.values()):
        out.append(u"表の大きさが手で数えた値と違う: %s" % ((len(roles), len(l2), len(l1)),))
    want_l2 = {u"現金及び預金": {u"CashAndDeposits"}, u"営業雑費": {u"FeeA", u"FeeB"}, u"資産合計": {u"Assets"}, u"繰延税金資産": {u"DtaQ", u"DtaR"}, u"有価証券": {u"SecWs"},
               u"投資有価証券(注)": {u"InvSec"}, u"売上": {u"Sales1"}}
    for k, v in want_l2.items():
        if l2.get(k) != v:
            out.append(u"表 L2 の %s が違う: %s" % (k, l2.get(k)))
    if u"文書の説明" in l2 or u"Cash and deposits" in l2:
        out.append(u"role の末尾が Label でない字か ja でない字が表に入っている")
    if l1.get(u"繰延税金資産") != {u"DtaQ"} or u"資産合計" in l1 or l1.get(u"営業雑費") != {u"FeeA", u"FeeB"}:
        out.append(u"表 L1(標準の role だけ)が違う")
    if any(u" " in k or u"\u00a0" in k for k in l2):
        out.append(u"表の字に空白が残っている")
    if ms.I.parse_label_linkbase is not ms.__dict__["I"].parse_label_linkbase:
        out.append(u"engine の読み取りを使っていない")
    return out


def sha_problems(ms=None):
    u"""標準ラベルの file は engine の読み取りで読み、sha256 が違えば・file が無ければ止まる(作り物の置き場だけ。本物の置き場は開かない)。"""
    ms = ms or MS
    out = []
    names = [fn for _ns, fn, _s in ms.I.TAXONOMY_LABEL_FILES]
    if ms.LABEL_FILE not in names:
        out.append(u"engine の標準ラベルの一覧に file が無い")
    with Temp() as d:
        if not stops(ms, ms.read_label_bytes, d):
            out.append(u"ラベルの file が無いのに止まらない")
        with open(os.path.join(d, ms.LABEL_FILE), "wb") as fh:
            fh.write(FAKE_LABELS)
        if not stops(ms, ms.read_label_bytes, d):
            out.append(u"ラベルの file の sha256 が違うのに止まらない")
    return out


# ======================================================================== 4. 書類 → 数える
def pipeline_problems(ms=None):
    ms = ms or MS
    out = []
    tabs = ms.label_tables(FAKE_LABELS)
    with Temp() as d:
        make_docs_dir(d)
        secret = (set(), set(), [], set())
        for i, stem in enumerate(STEMS):
            with zipfile.ZipFile(os.path.join(d, stem + ".zip")) as z:
                acc = ms.analyze_zip(z, tabs, secret)
            if acc_tuple(acc) != dict(std=HAND_DOCS[i]["std"], sub=HAND_DOCS[i]["sub"], b=HAND_DOCS[i]["b"], c=HAND_DOCS[i]["c"], d=HAND_DOCS[i]["d"], l2=HAND_DOCS[i]["l2"], l1=HAND_DOCS[i]["l1"]):
                out.append(u"書類 %d の数が手で数えた値と違う: %s" % (i + 1, acc_tuple(acc)))
        if sorted(secret[1]) != sorted([u"CashAndDeposits", u"FeeB", u"Sales2", u"NoLab1", u"NoLab2", u"NoLab3", u"NoLab4", u"NoLab5", u"Assets", u"DtaQ", u"DtaR", u"SecWs", u"InvSec", u"DocE"]):
            out.append(u"材料の要素の局所名の集まりが違う")
        if u"現金及び預金" not in secret[0] or u"投資有価証券(注)" not in secret[0]:
            out.append(u"材料の行の字の集まりに正規化した字が入っていない")
    return out


def mix_problems(ms=None):
    u"""zip の中の提出者のラベルの file(答えの側)を表に混ぜない。混ぜると書類 1 の「未登録の勘定A」の行(N)が U になる。"""
    ms = ms or MS
    out = []
    tabs = ms.label_tables(FAKE_LABELS)
    with Temp() as d:
        make_docs_dir(d, mix=True)
        with zipfile.ZipFile(os.path.join(d, STEMS[0] + ".zip")) as z:
            if not any(n.endswith("_lab.xml") for n in z.namelist()):
                out.append(u"作り物の zip に提出者のラベルが無い(試験の作りの欠陥)")
            acc = ms.analyze_zip(z, tabs, (set(), set(), [], set()))
        if acc_tuple(acc)["l2"] != HAND_DOCS[0]["l2"] or acc_tuple(acc)["l1"] != HAND_DOCS[0]["l1"]:
            out.append(u"提出者のラベルが表に混ざった: %s" % (acc_tuple(acc),))
    return out


def select_problems(ms=None):
    ms = ms or MS
    out = []
    with Temp() as d:
        make_docs_dir(d)
        if not stops(ms, ms.select_docs, d):                       # 4 本は 67 本でない
            out.append(u"67 本でないのに止まらない")
        sel = ms.select_docs(d, want=4)
        if [s[0] for s in sel] != STEMS:
            out.append(u"選んだ書類が違う(別の様式の zip か PublicDoc の外の xsd を選んだ): %s" % [s[0] for s in sel])
        if not stops(ms, ms.select_docs, d, 5) or not stops(ms, ms.select_docs, d, 3):
            out.append(u"本数が want と違うのに止まらない")
        if ms.order_sha256(STEMS[::-1]) != ORDER_SHA or ms.order_sha256(STEMS) != ORDER_SHA:
            out.append(u"並びの sha256 が昇順に並べ \\n でつないだ字の sha256 と違う")
    with Temp() as d:
        with open(os.path.join(d, "bad.zip"), "wb") as fh:
            fh.write(b"not a zip")
        if not stops(ms, ms.select_docs, d, 0):
            out.append(u"壊れた zip で止まらない")
    return out


# ======================================================================== 5. 記録
def clean_problems(ms=None):
    ms = ms or MS
    out = []
    ok = od([(u"書類", [od([(u"番号", 1), (u"材料の sha256", u"a" * 64)])]), (u"git", u"b" * 40)])
    secret = ({u"現金", u"投資有価証券(注)"}, {u"CashAndDeposits"}, [u"zzdoc"], {u"E99991"})
    if stops(ms, ms.check_clean, ok, ms.dumps(ok), secret):
        out.append(u"きれいな記録で止まる(sha256 の 16 進を含む)")
    cases = [
        (u"禁止の欄(docid)", od([(u"DocID", 1)])), (u"禁止の欄(company)", od([(u"x", [od([(u"company", 1)])])])), (u"禁止の欄(label)", od([(u"label", 1)])),
        (u"禁止の欄(行の字)", od([(u"行の字", 1)])), (u"禁止の欄(要素の名)", od([(u"要素の名", 1)])), (u"禁止の欄(会社の名)", od([(u"会社の名", 1)])),
        (u"EDINET コードの形", od([(u"x", u"id E12345 x")])), (u"docID の形", od([(u"x", u"S100ABCD")])),
        (u"材料の docID", od([(u"x", u"id zzdoc.")])), (u"材料の EDINET コード", od([(u"x", u"E99991")])),
        (u"材料の要素の名", od([(u"x", u"a CashAndDeposits b")])),
        (u"材料の行の字(短い字は全部一致)", od([(u"x", u"現金")])), (u"材料の行の字(長い字は部分一致)", od([(u"x", u"文 投資有価証券(注) 文")]))]
    for what, rec in cases:
        if not stops(ms, ms.check_clean, rec, ms.dumps(rec), secret):
            out.append(u"%s が止まらない" % what)
        if not stops(ms, ms.record_text, rec, secret):
            out.append(u"%s が record_text で止まらない" % what)
    for what, rec in ((u"短い字の部分(現金は 5 字未満なので部分一致では止めない)", od([(u"x", u"現金化")])), (u"要素の名の部分だけ(別の語の一部)", od([(u"x", u"xCashAndDepositsy")]))):
        if stops(ms, ms.check_clean, rec, ms.dumps(rec), secret):
            out.append(u"%s で止まる(止め過ぎ)" % what)
    with Temp() as d:
        p = os.path.join(d, "r.json")
        bad = od([(u"x", u"E12345")])
        if not stops(ms, ms.write_record, p, bad) or os.path.exists(p):
            out.append(u"禁止の字が在る記録を書いた(書く前の検査)")
        good = od([(u"x", 1)])
        ms.write_record(p, good)
        if not stops(ms, ms.write_record, p, good):
            out.append(u"記録が既に在るのに書き直せる")
        # 書いた後の検査: 書いた字が検査した字と違った(書いた後に E コードが混ざった)ら止めて、file を消す
        q = os.path.join(d, "q.json")
        orig = ms.write_exclusive
        ms.write_exclusive = lambda path, data: orig(path, data + b" E12345")
        try:
            stopped = stops(ms, ms.write_record, q, good)
        finally:
            ms.write_exclusive = orig
        if not stopped or os.path.exists(q):
            out.append(u"書いた後の検査が止めない(か file を消さない)")
        # 書く前の検査: 書く字を検査と無関係なきれいな字に替えても、危ない記録なら書く前に止める(後の検査だけに頼らない)
        w = os.path.join(d, "w.json")
        ms.write_exclusive = lambda path, data: orig(path, b"{}")
        try:
            stopped = stops(ms, ms.write_record, w, bad)
        finally:
            ms.write_exclusive = orig
        if not stopped:
            out.append(u"書く前の検査が止めない(書いた後の検査だけで止まっている)")
    return out


def e2e_problems(ms=None):
    ms = patched(load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms)
    out = []
    with Temp() as d:
        docs, tax, rec_path = os.path.join(d, "docs"), os.path.join(d, "tax"), os.path.join(d, "rec", "r.json")
        os.makedirs(docs)
        make_docs_dir(docs)
        if not stops(ms, ms.run, root=d, docs=docs, taxonomy=tax, out=rec_path, say=lambda *a: None) or os.path.exists(rec_path):
            out.append(u"書類が 67 本でないのに run が止まらない(か記録を書いた)")
        rec = ms.run(root=d, docs=docs, taxonomy=tax, out=rec_path, want=4, say=lambda *a: None)
        now = ms.check(root=d, docs=docs, taxonomy=tax, rec_path=rec_path, want=4, say=lambda *a: None)
        if ms.dumps(rec) != ms.dumps(now):
            out.append(u"記録と --check の数え直しが違う")
        mat = rec[u"材料"]
        if (mat[u"書類の本数"], mat[u"書類の file 名の並びの sha256"], mat[u"表 L2 の role の数"], mat[u"表 L2 のラベルの字の数"], mat[u"表 L1 のラベルの字の数"]) != (4, ORDER_SHA, 3, 11, 10):
            out.append(u"材料の欄が手で数えた値と違う")
        if mat[u"標準ラベルの file の sha256"] != hashlib.sha256(FAKE_LABELS).hexdigest():
            out.append(u"ラベルの file の sha256 が読んだ bytes のものでない")
        for i, h in enumerate(HAND_DOCS):
            r = rec[u"書類"][i]
            want = (i + 1, (h["std"], h["sub"]), sum(h["l2"]), (h["b"], h["c"], h["d"]), h["l2"], h["l1"], h["rate"])
            got = (r[u"番号"], tuple(r[u"タグの数"].values()), r[u"計算書の行の数"], tuple(r[u"分母に入れなかった行の数"].values()), tuple(r[u"類別(表 L2)"].values()),
                   tuple(r[u"類別(表 L1)"].values()), r[u"U の率(表 L2。%)"])
            if got != want:
                out.append(u"書類 %d の記録が手で数えた値と違う: %s" % (i + 1, got))
        t = HAND_TOTAL
        agg = rec[u"集計"]
        if (tuple(agg[u"タグの数"].values()), agg[u"計算書の行の数"], tuple(agg[u"分母に入れなかった行の数"].values()), tuple(agg[u"類別(表 L2)"].values()), tuple(agg[u"類別(表 L1)"].values()),
                agg[u"計算書の行が 1 行以上在る書類の数"], agg[u"計算書の行が 0 で書類ごとの数から外した書類の数"]) != ((t["std"], t["sub"]), t["rows"], (t["b"], t["c"], t["d"]), t["l2"], t["l1"], t["docs_rows"], t["docs_zero"]):
            out.append(u"集計が手で数えた値と違う: %s" % dict(agg))
        pred = [v for k, v in rec.items() if k.startswith(u"予測の判定に要る数")][0]
        pv = list(pred.values())
        h = HAND_RATES
        if (pv[0][u"タグ"], pv[0][u"分母"], pv[0][u"%"]) != (8, 84, h["sub_tag"]) or (pv[1][u"行"], pv[1][u"分母"], pv[1][u"%"]) != (18, 31, h["u2"]):
            out.append(u"XG0-1・XG0-2 の数が手で数えた値と違う")
        if (pv[2][u"行"], pv[2][u"%"]) != (2, h["w"]) or (pv[3][u"行"], pv[3][u"%"]) != (5, h["a"]):
            out.append(u"XG0-3・XG0-4 の数が手で数えた値と違う")
        if (pv[4][u"書類"], pv[4][u"分母"]) != (t["docs_u90"], t["docs_rows"]):
            out.append(u"XG0-5 の数が手で数えた値と違う")
        if (pv[5][u"表 L2 の U の行"], pv[5][u"表 L1 の U の行"], pv[5][u"表 L1 の %"], pv[5][u"L2 から L1 を引いた差(ポイント)"]) != (18, 17, h["u1"], h["diff"]):
            out.append(u"XG0-6 の数が手で数えた値と違う")
        text = io.open(rec_path, encoding="utf-8").read()
        for leak in STEMS + [u"E9999", u"CashAndDeposits", u"現金及び預金", u"未登録の勘定", u"S1OTHER1", u"S1AUDIT1"]:
            if leak in text:
                out.append(u"記録に材料の字が在る: %s" % leak)
        if not stops(ms, ms.run, root=d, docs=docs, taxonomy=tax, out=rec_path, want=4, say=lambda *a: None):
            out.append(u"記録が既に在るのに run が止まらない")
        bad = text.replace(u'"計算書の行の数": 12', u'"計算書の行の数": 13', 1)
        bp = os.path.join(d, "bad.json")
        with io.open(bp, "w", encoding="utf-8") as fh:
            fh.write(bad)
        if bad == text or not stops(ms, ms.check, root=d, docs=docs, taxonomy=tax, rec_path=bp, want=4, say=lambda *a: None):
            out.append(u"数を変えた記録で --check が止まらない")
        make_zip(os.path.join(docs, STEMS[3] + ".zip"), 4, fake_doc_texts()[0])            # 置き場の書類を替える
        if not stops(ms, ms.check, root=d, docs=docs, taxonomy=tax, rec_path=rec_path, want=4, say=lambda *a: None):
            out.append(u"置き場の書類を変えても --check が止まらない")
        if not stops(ms, ms.check, root=d, docs=docs, taxonomy=tax, rec_path=os.path.join(d, "none.json"), want=4, say=lambda *a: None):
            out.append(u"記録が無いのに --check が止まらない")
    return out


def secret_problems(ms=None):
    u"""本番の ``build_record`` が作る secret(行の字・要素の名・docID・EDINET コード)の配線と、``check()`` が secret を ``check_clean`` に渡していること。作り物の置き場だけ。"""
    ms = patched(load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms)
    out = []
    with Temp() as d:
        docs, tax, rec_path = os.path.join(d, "docs"), os.path.join(d, "tax"), os.path.join(d, "rec", "r.json")
        os.makedirs(docs)
        make_docs_dir(docs)
        rec, secret = ms.build_record(docs, tax, 4)
        labels, elems, ids, ecodes = secret
        if list(ids) != STEMS:
            out.append(u"secret の docID の並びが作り物の置き場の書類と違う: %s" % (list(ids),))
        if set(ecodes) != set([u"E99991", u"E99992", u"E99993", u"E99994"]):
            out.append(u"secret の EDINET コードが作り物の xsd の名の 4 つと違う: %s" % (sorted(ecodes),))
        if sorted(elems) != sorted([u"CashAndDeposits", u"FeeB", u"Sales2", u"NoLab1", u"NoLab2", u"NoLab3", u"NoLab4", u"NoLab5", u"Assets", u"DtaQ", u"DtaR", u"SecWs", u"InvSec", u"DocE"]):
            out.append(u"secret の要素の名が作り物の行の要素と違う")
        if not set([u"現金及び預金", u"投資有価証券(注)", u"営業雑費", u"売上"]) <= set(labels):
            out.append(u"secret の行の字に作り物の行の字(正規化した字)が入っていない")
        # check() が secret を check_clean に渡す: 数は同じで、secret にしか当たらない字(要素の名・行の字)を仕込んだ記録で止まる
        real_build = ms.build_record
        # (docID・EDINET コードの形の字は secret が無くても形で止まるので、仕込みには使わない)
        for what, leak in ((u"要素の名", u"a CashAndDeposits b"), (u"行の字", u"現金及び預金")):
            leaky = od(rec)
            leaky[u"仕込み"] = leak
            lp = os.path.join(d, "leak_%d.json" % len(what))
            with io.open(lp, "w", encoding="utf-8") as fh:
                fh.write(ms.dumps(leaky))
            ms.build_record = lambda *a, **k: (leaky, secret)
            try:
                stopped = stops(ms, ms.check, root=d, docs=docs, taxonomy=tax, rec_path=lp, want=4, say=lambda *a: None)
            finally:
                ms.build_record = real_build
            if not stopped:
                out.append(u"check() が secret(%s)の仕込みで止まらない" % what)
        # 対照: 仕込みの無い記録は通る(止め過ぎでない)
        ms.run(root=d, docs=docs, taxonomy=tax, out=rec_path, want=4, say=lambda *a: None)
        ms.check(root=d, docs=docs, taxonomy=tax, rec_path=rec_path, want=4, say=lambda *a: None)
    return out


# ======================================================================== 6. 配線
STDLIB_OK = ("__future__", "argparse", "collections", "glob", "hashlib", "io", "json", "os", "re", "sys", "unicodedata", "xml", "zipfile", "adapters")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "subprocess", "importlib")
ENGINE_CALLED = ("_TR_RE", "_row_label", "parse_label_linkbase", "_read_taxonomy_file", "TAXONOMY_LABEL_FILES")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")


def import_problems(src=None):
    u"""script の import は標準ライブラリと engine の 2 module(instance・verify_document)だけ。通信しない。engine の関数は写さず ``I.`` から呼ぶ。環境変数・鍵・``.env`` を読まない。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out = []
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.Import):
            names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            names = [(n.module or u"")]
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("__import__", "eval", "exec"):
            out.append(u"動的な import・eval・exec の呼び出し")
        for nm in names:
            top = nm.split(".")[0]
            if top in NETWORK_MODULES:
                out.append(u"許さない module を import している: %s" % nm)
            elif top not in STDLIB_OK:
                out.append(u"許す一覧に無い module: %s" % nm)
    eng = sorted(a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "adapters.xbrl" for a in n.names)
    if eng != ["instance", "verify_document"]:
        out.append(u"engine から読む module が instance・verify_document の 2 つだけでない: %s" % eng)
    attrs = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]
    if ("os", "environ") in attrs or ("os", "getenv") in attrs:
        out.append(u"環境変数を読んでいる")
    for fn in ENGINE_CALLED:
        if ("I", fn) not in attrs:
            out.append(u"engine の %s を I から呼んでいない" % fn)
    defined = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            defined.add(n.name)
        elif isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name):
                    defined.add(tg.id)
    for fn in ENGINE_CALLED + ("parse_label_linkbase", "_read_taxonomy_file", "engine_fingerprint"):
        if fn in defined:
            out.append(u"engine の %s を script が自分で定義している(写している)" % fn)
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            doc.add(id(n.body[0].value))
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc and (u".env" in n.value or u"dotenv" in n.value or u"API_KEY" in n.value):
            out.append(u"鍵・.env の字が在る")
    return out


def reserved_problems(rel=GATE_REL, base=ROOT):
    out = []
    with open(os.path.join(base, rel), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for n, line in enumerate(lines, 1):
        if any(line.startswith(p) for p in RESERVED_PREFIXES):
            out.append(u"%s:%d" % (rel, n))
    return out


# ======================================================================== 変異
#: (名前, 置き換え前(script の中でちょうど 1 回)・置き換え後・赤になるべき検査の名前)。**予測は「その検査が赤になる」。** この表は実行より先に書いた。
MUTANTS = (
    (u"M1 U と A の境(1 つ → 2 つ以下)", u'    return "U" if len(cands) == 1 else "A"', u'    return "U" if len(cands) <= 2 else "A"', ("pure", "pipeline")),
    (u"M2 U と A の境(A を U にする)", u'    return "U" if len(cands) == 1 else "A"', u'    return "U"', ("pure", "pipeline")),
    (u"M3 W と N の境(W を N にする)", u'    if E not in cands:\n        return "W"', u'    if E not in cands:\n        return "N"', ("pure", "pipeline")),
    (u"M4 E を含むかの判定を外す", u"    if E not in cands:", u"    if False:", ("pure", "pipeline")),
    (u"M5 A に E を含むかを問わない(含まない 2 つ以上は A)", u'    if E not in cands:\n        return "W"\n', u'    if E not in cands and len(cands) == 1:\n        return "W"\n', ("pure", "pipeline")),
    (u"M6 L2 を L1 に替える(標準の role だけ)", u"            l2.setdefault(key, set()).add(local_of(full))\n", u"            if r == STANDARD_ROLE:\n                l2.setdefault(key, set()).add(local_of(full))\n", ("tables", "pipeline", "e2e")),
    (u"M7 L1 を L2 に替える(全部の role)", u"            if r == STANDARD_ROLE:\n                l1.setdefault(key, set()).add(local_of(full))", u"            if True:\n                l1.setdefault(key, set()).add(local_of(full))", ("tables", "pipeline", "e2e")),
    (u"M8 L2 の role を ``label`` だけにする(Label で終わる role を落とす)", u'ROLE_SUFFIXES = ("Label", "label")', u'ROLE_SUFFIXES = ("label",)', ("seal", "tables", "pipeline")),
    (u"M9 L2 の role を全部にする(末尾の字を問わない)", u"            if r.endswith(ROLE_SUFFIXES):", u"            if True:", ("tables", "pipeline")),
    (u"M10 表の側の空白の除きを外す(NFKC だけ掛ける)", u"            key = norm_label(word)", u'            key = unicodedata.normalize("NFKC", word)', ("tables", "pipeline")),
    (u"M11 行の側の NFKC を外す(空白の除きだけ掛ける)", u'    return ("ok", norm_label(label), names[0].split(":")[-1])', u'    return ("ok", WS_RE.sub(u"", label), names[0].split(":")[-1])', ("pure", "pipeline")),
    (u"M12 分母の条件 (b) を外す", u'    if len(set(names)) != 1:\n        return ("b",)', u'    if False:\n        return ("b",)', ("pure", "pipeline")),
    (u"M13 分母の条件 (c) を外す", u'    if names[0].split(":")[0] != STATEMENT_PREFIX:\n        return ("c",)', u'    if False:\n        return ("c",)', ("pure", "pipeline")),
    (u"M14 分母の条件 (d) を外す", u'    if not label:\n        return ("d",)', u'    if not label:\n        label = u"?"', ("pure", "pipeline")),
    (u"M15 (b) を「名の数」にする(同じ名が 2 回出ても b)", u"    if len(set(names)) != 1:", u"    if len(names) != 1:", ("pure", "pipeline")),
    (u"M16 標準の判定: ``_cor`` で終わるを外す", u'    return prefix.startswith("jp") and prefix.endswith("_cor")', u'    return prefix.startswith("jp")', ("pure", "pipeline")),
    (u"M17 標準の判定: 頭が jp を外す", u'    return prefix.startswith("jp") and prefix.endswith("_cor")', u'    return prefix.endswith("_cor")', ("pure", "pipeline")),
    (u"M18 標準の判定: jppfs_cor だけにする", u'    return prefix.startswith("jp") and prefix.endswith("_cor")', u'    return prefix == STATEMENT_PREFIX', ("pure", "pipeline")),
    (u"M19 67 の止めを外す", u"    if len(found) != want:", u"    if False:", ("select", "e2e")),
    (u"M20 別の様式の zip も選ぶ(xsd の名を問わない)", u"        if any(x.startswith(XSD_PREFIX) for x in xs):", u"        if xs:", ("select", "e2e")),
    (u"M21 xsd を PublicDoc の外からも探す", u"    return [n for n in z.namelist() if n.startswith(PUBLICDOC) and n.endswith(\".xsd\")]", u"    return [n for n in z.namelist() if n.endswith(\".xsd\")]", ("select", "e2e")),
    (u"M22 PublicDoc の外の ixbrl も読む", u"        if n.startswith(PUBLICDOC) and n.endswith(IXBRL_SUFFIX):", u"        if n.endswith(IXBRL_SUFFIX):", ("pipeline", "e2e")),
    (u"M23 nonNumeric も数える", u"""NF_RE = re.compile(r'<ix:nonFraction\\b[^>]*?\\bname="([^"]+)"', re.I)""", u"""NF_RE = re.compile(r'<ix:non(?:Fraction|Numeric)\\b[^>]*?\\bname="([^"]+)"', re.I)""", ("pure", "pipeline")),
    (u"M24 並びの sha256 を改行なしでつなぐ", u'u"\\n".join(sorted(stems))', u'u"".join(sorted(stems))', ("select", "e2e")),
    (u"M25 提出者のラベルの file を表に混ぜる", u"    l2, l1 = tabs\n    acc = new_doc()\n",
     u"    l2, l1 = tabs\n    l2 = dict((k, set(v)) for k, v in l2.items())\n    l1 = dict((k, set(v)) for k, v in l1.items())\n"
     u"    for _n in z.namelist():\n        if _n.endswith(\"_lab.xml\"):\n            _a, _b = label_tables(z.read(_n))\n"
     u"            for _k, _v in _a.items():\n                l2.setdefault(_k, set()).update(_v)\n            for _k, _v in _b.items():\n                l1.setdefault(_k, set()).update(_v)\n    acc = new_doc()\n", ("mix",)),
    (u"M26 U の率 90% 以上を「より大きい」にする", u'            if 100 * acc["l2"]["U"] >= U_DOC_THRESHOLD_PCT * r:', u'            if 100 * acc["l2"]["U"] > U_DOC_THRESHOLD_PCT * r:', ("e2e",)),
    (u"M27 計算書の行が 0 の書類も書類ごとの数に入れる", u"        if r:\n            docs_with_rows += 1", u"        if True:\n            docs_with_rows += 1", ("e2e",)),
    (u"M28 率を切り捨てにする", u"    tenths = (2000 * abs(n) + d) // (2 * d)", u"    tenths = (2000 * abs(n)) // (2 * d)", ("pure", "e2e")),
    (u"M29 禁止の欄の検査を外す", u"    if bad:", u"    if False:", ("clean",)),
    (u"M30 EDINET コードの形の検査を外す", u"    if ECODE_FORM_RE.search(scan):", u"    if False:", ("clean",)),
    (u"M31 docID の形の検査を外す", u"    if DOCID_FORM_RE.search(scan):", u"    if False:", ("clean",)),
    (u"M32 材料の docID・EDINET コードの検査を外す", u"        if tokens & set(ids) or tokens & set(ecodes):", u"        if False:", ("clean",)),
    (u"M33 要素の名の検査を外す", u"        if tokens & set(e for e in elems if len(e) >= 3):", u"        if False:", ("clean",)),
    (u"M34 行の字の全部一致の検査を外す", u"        if strs & set(labels):", u"        if False:", ("clean",)),
    (u"M35 行の字の部分一致の検査を外す", u"            if len(lab) >= LABEL_SUBSTRING_MIN and lab in scan:", u"            if False:", ("clean",)),
    (u"M36 書いた後の検査を外す", u"        check_clean(rec, back, secret)\n    except SystemExit:", u"        pass\n    except SystemExit:", ("clean",)),
    (u"M37 書く前の検査を外す", u"    text = record_text(rec, secret)\n    os.makedirs", u"    text = dumps(rec)\n    os.makedirs", ("clean",)),
    (u"M38 標準ラベルの sha256 の照合を engine に任せず飛ばす(file を直接読む)", u"        return I._read_taxonomy_file(taxonomy_dir, LABEL_FILE, sha)", u'        return open(os.path.join(taxonomy_dir, LABEL_FILE), "rb").read(), sha', ("sha",)),
    (u"M39 予測の境の数を 1 つ替える(XG0-2 の上限)", u'("XG0-2", (60, 85))', u'("XG0-2", (60, 86))', ("seal",)),
    (u"M40 書類の本数を 66 にする", u"DOCS_WANT = 67", u"DOCS_WANT = 66", ("seal",)),
    # ---- 監査 REVISE の直し(1 点目・2 点目)で足した変異。**予測は実行より先に書いた**(赤になるべき検査は各行の最後)。
    # J: EDINET コードの収集を外すと secret[3] が空 → secret の EDINET コードの検査(secret)が赤。J2: docID の並びを空にすると secret[2] が空 → secret が赤。
    # J3: check() が secret を渡さないと、要素の名・行の字を仕込んだ記録で止まらない → secret が赤。M41: L2 の role の選びを「abel を含む」にすると
    #     labelGuide の role が L2 に入り、role の数 3→4・表 L2 の字の数 11→12・書類 2 の行 DOC が N→U → tables・pipeline・e2e が赤。
    (u"J 本番の build_record が EDINET コードを secret に集めない", u'            secret[3].update(re.findall(r"E\\d{5}", x))', u"            pass", ("secret",)),
    (u"J2 本番の build_record の secret の docID の並びが空", u"    secret = (set(), set(), [d[0] for d in docs], set())", u"    secret = (set(), set(), [], set())", ("secret",)),
    (u"J3 check() が secret を check_clean に渡さない", u"    check_clean(rec, text, secret)\n    say(", u"    check_clean(rec, text)\n    say(", ("secret",)),
    (u"M41 L2 の role の選びを「abel を含む」にする", u"            if r.endswith(ROLE_SUFFIXES):", u'            if "abel" in r:', ("tables", "pipeline", "e2e")),
)
#: 黙ることが分かっている変異(理由つき)。黙ること自体を ``SilentTest`` が縛る
SILENT_BY_DESIGN = (
    (u"S1 行の側の空白の除きを外す(NFKC だけ掛ける)",
     u'    return ("ok", norm_label(label), names[0].split(":")[-1])', u'    return ("ok", unicodedata.normalize("NFKC", label), names[0].split(":")[-1])',
     u"行の字は engine の ``_row_label`` が空白(``\\s`` と U+00A0)を全部除いて返す。NFKC は U+00A8 など互換の字を空白つきの字に替えることがあり「空白を新しく作らない」とは言えないが、作り物の入力にそういう字は無く、外しても作り物の数は変わらない(本物の書類の行の字に在るかは測っていない)。行の側の空白の除きは engine と大半が二重"),
    (u"S2 表の側の NFKC を外す(空白の除きだけ掛ける)",
     u"            key = norm_label(word)", u'            key = WS_RE.sub(u"", word)',
     u"engine の ``parse_label_linkbase`` が返すラベルの字は既に NFKC にそろえてある。表の側の NFKC は engine と二重で、外しても表は変わらない"),
)


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"pure": pure_problems, u"tables": tables_problems, u"sha": sha_problems, u"pipeline": pipeline_problems, u"mix": mix_problems,
             u"select": select_problems, u"clean": clean_problems, u"e2e": e2e_problems, u"secret": secret_problems}
    if name in table:
        return table[name](mod)
    if name == u"import":
        return import_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"pure", u"tables", u"sha", u"pipeline", u"mix", u"select", u"clean", u"e2e", u"secret", u"import")


def run_mutants(table=MUTANTS):
    base = read(SCRIPT_REL)
    out = []
    for name, old, new, checks in table:
        assert base.count(old) == 1, (name, base.count(old))
        src = base.replace(old, new)
        try:
            mod = load_source(src)
        except BaseException as exc:                # noqa: BLE001
            out.append((name, [(c, True) for c in checks], u"読めない: %s" % type(exc).__name__))
            continue
        res = [(c, bool(guard(check_by_name, c, mod, src))) for c in checks]
        out.append((name, res, u""))
    return out


# ======================================================================== 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_constants_equal_the_seal(self):
        self.assertEqual([], seal_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        for old, new in ((u"**67 本**", u"**66 本**"), (u"| XG0-2 | 類 U は計算書の行の 60% 以上 85% 以下(表 L2)", u"| XG0-2 | 類 U は計算書の行の 60% 以上 86% 以下(表 L2)"),
                         (u"U の率が 90% 以上の書類は 10 本以下", u"U の率が 80% 以上の書類は 10 本以下"), (u"末尾が `Label` か `label` のもの全部", u"末尾が `label` のもの全部"),
                         (u"role が `http://www.xbrl.org/2003/role/label`(標準)だけ", u"role が `http://www.xbrl.org/2003/role/totalLabel`(標準)だけ"),
                         (u"(b) 全部が同じ 1 つの名", u"(b) 全部が違う名"), (u"2 つ以上で、E を含む", u"2 つ以上で、E を含まない")):
            self.assertEqual(1, seal.count(old), old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"tag_wall", body)
        self.assertNotIn(u"xbrl_tag_wall", body)


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_good_order_is_green_and_bad_orders_are_red(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        others = ["measure/s.py", "tests/g.py"]
        for f in others:
            r.put(f)
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others))
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", [], others))
        r.put("tests/new.py")
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others + ["tests/new.py"]))
        r2 = PR.Repo()
        r2.put("measure/s.py")
        r2.commit("measure/s.py")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], [], ["measure/s.py"]))

    def test_d_3_the_order_check_lists_the_script_and_the_gate_and_not_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)


class PureTest(unittest.TestCase):
    def test_b_1_normalisation_rates_standard_row_status_and_classes(self):
        self.assertEqual([], pure_problems())

    def test_b_2_the_label_tables_l2_and_l1(self):
        self.assertEqual([], tables_problems())

    def test_b_3_the_label_file_goes_through_the_engine_reader_and_its_sha256(self):
        self.assertEqual([], sha_problems())

    def test_b_4_made_up_zips_go_through_every_real_function_and_equal_the_hand_count(self):
        self.assertEqual([], pipeline_problems())

    def test_b_5_the_submitter_label_file_in_the_zip_is_not_mixed_into_the_table(self):
        self.assertEqual([], mix_problems())

    def test_b_6_the_hand_counts_are_not_the_same_as_nearby_numbers(self):
        u"""手で数えた値が互いに違う・合計が足し算と合う・境(90%・5 ポイント)の手前と上の両方が在る。"""
        t = HAND_TOTAL
        self.assertEqual(t["rows"], sum(t["l2"]))
        self.assertEqual(t["rows"], sum(t["l1"]))
        self.assertEqual(t["rows"], sum(sum(h["l2"]) for h in HAND_DOCS))
        self.assertEqual(t["l2"], tuple(sum(h["l2"][i] for h in HAND_DOCS) for i in range(4)))
        self.assertEqual(t["l1"], tuple(sum(h["l1"][i] for h in HAND_DOCS) for i in range(4)))
        self.assertEqual(t["std"], sum(h["std"] for h in HAND_DOCS))
        self.assertEqual(t["sub"], sum(h["sub"] for h in HAND_DOCS))
        self.assertGreater(len(set(t["l2"])), 3)
        self.assertNotEqual(t["l2"], t["l1"])
        rates = [h["rate"] for h in HAND_DOCS if h["rate"] is not None]
        self.assertTrue(any(r >= 90 for r in rates) and any(r < 90 for r in rates))
        self.assertTrue(any(h["rate"] is None for h in HAND_DOCS))
        self.assertEqual(len(set(HAND_RATES.values())), len(HAND_RATES))         # 率が互いに全部違う

    def test_b_7_the_fake_files_are_what_the_checks_say(self):
        with Temp() as d:
            make_docs_dir(d)
            names = sorted(os.listdir(d))
            self.assertEqual(sorted([s + ".zip" for s in STEMS] + ["S1OTHER1.zip", "S1AUDIT1.zip"]), names)
            with zipfile.ZipFile(os.path.join(d, "S1AUDIT1.zip")) as z:
                self.assertEqual([], [n for n in z.namelist() if n.startswith("XBRL/PublicDoc/") and n.endswith(".xsd")])


class RecordTest(unittest.TestCase):
    def test_d_1_the_forbidden_checks_stop_planted_content(self):
        self.assertEqual([], clean_problems())

    def test_d_2_the_stop_at_67_and_the_selection(self):
        self.assertEqual([], select_problems())

    def test_d_3_cache_to_record_to_check_without_reading_the_real_cache(self):
        self.assertEqual([], e2e_problems())

    def test_d_5_the_production_secret_is_built_and_check_passes_it_to_the_clean_check(self):
        self.assertEqual([], secret_problems())

    def test_d_4_the_real_record_when_present_is_clean(self):
        p = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(p):
            self.skipTest(u"記録は本番の走りの後に書かれる。記録の中身の検査は結果の門に置く")
        text = read(RECORD_REL)
        rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
        MS.check_clean(rec, text)


class WiringTest(unittest.TestCase):
    def test_e_1_imports_and_the_engine_functions_are_called_not_copied(self):
        self.assertEqual([], import_problems())

    def test_e_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], import_problems(base + u"\nimport socket\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport urllib.request\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport subprocess\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = os.environ.get('A')\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef _row_label(row):\n    return None\n"))
        self.assertNotEqual([], import_problems(base.replace(u"I._row_label(row)", u"None")))
        self.assertNotEqual([], import_problems(base.replace(u"from adapters.xbrl import instance as I", u"from adapters.xbrl import instance as I\nfrom adapters.xbrl import recipes as R")))

    def test_e_3_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_e_4_the_script_leaves_sys_modules_as_it_found_them(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_tag_wall_script_for_sysmodules_check")
        self.assertEqual([], [k for k, v in before.items() if sys.modules.get(k) is not v])
        del mod

    def test_e_5_the_default_places_are_outside_the_repo_and_the_gate_never_opens_them(self):
        top = os.path.realpath(REPO)
        for p in (MS.DOCS_DIR, MS.TAXONOMY_DIR):
            self.assertFalse(os.path.realpath(p).startswith(top + os.sep), p)
        src = read(GATE_REL)
        # この門が置き場を開く道: 既定の定数を使う関数を呼んでいない(select_docs・build_record・run・check は引数を必ず渡す)
        for m in re.finditer(r"ms\.(select_docs|build_record|run|check)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"\bd\b|docs", m.group(2)), m.group(0))


class MutantTest(unittest.TestCase):
    def test_f_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL))
        modules_before = dict(sys.modules)
        results = run_mutants()
        self.assertEqual(before, (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL)))
        self.assertEqual([], [k for k, v in modules_before.items() if sys.modules.get(k) is not v])
        silent = [(n, c) for n, res, _w in results for c, red in res if not red]
        self.assertEqual([], silent)
        self.assertEqual(len(MUTANTS), len(results))

    def test_f_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ALL_CHECKS:
            self.assertEqual([], check_by_name(name, mod, base), name)

    def test_f_3_the_silent_mutants_are_silent_for_the_stated_reason(self):
        u"""行の側の空白の除き・表の側の NFKC は engine が先に掛けているので、外しても作り物の全部の検査の数も、字を足した入力の行の字・表も変わらない。"""
        base = read(SCRIPT_REL)
        for name, old, new, _why in SILENT_BY_DESIGN:
            self.assertEqual(1, base.count(old), name)
            mod = load_source(base.replace(old, new))
            for c in (u"pure", u"tables", u"pipeline", u"mix", u"clean", u"e2e", u"select"):
                self.assertEqual([], check_by_name(c, mod, None), (name, c))
            for r in (u"<tr><td>勘定\u3000科目\u00a0Ａ</td><td>%s</td></tr>" % (NFTAG % u"jppfs_cor:CashAndDeposits"), K["NF"](), K["WS"]()):
                self.assertEqual(MS.row_status(r), mod.row_status(r), name)
            self.assertEqual(MS.label_tables(FAKE_LABELS), mod.label_tables(FAKE_LABELS), name)
            self.assertEqual(MS.label_tables(linkbase([(P + u"X", R_STD, u"ＡＢＣ　ｄ", "ja")])), mod.label_tables(linkbase([(P + u"X", R_STD, u"ＡＢＣ　ｄ", "ja")])), name)


if __name__ == "__main__":
    unittest.main()
