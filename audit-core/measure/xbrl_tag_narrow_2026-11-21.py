# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TAG_NARROW_SEAL_2026-11-21.md(XG1 ― 便 XG0 で候補が 2 つ以上だった行を、数を持てる要素・計算書の種類・業種の科目の一覧で絞ると、要素が 1 つに決まる行はどれだけ増えるか)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。通信しない。** engine(``core/``・``adapters/``)は 1 行も変えない。便 XG0 の script の関数(行の状態・類分け・表 L2・書類の選び方・記録の検査)は importlib で読んで呼ぶ(写さない)。

    python3 measure/xbrl_tag_narrow_2026-11-21.py            # 置き場から数えて記録 fixtures/xbrl/cd8/tag_narrow_2026-11-21.json を書く。通信しない
    python3 measure/xbrl_tag_narrow_2026-11-21.py --check    # 置き場から数え直して記録と照らす。通信しない

置き場の既定は封の字(書類 ``~/.cache/audit-core/edinet/``・標準ラベル ``~/.cache/audit-core/edinet-taxonomy/2025-11-01/``・標準タクソノミの一式 ``~/.cache/audit-core/edinet-taxonomy-full/2025-11-01/1c_Taxonomy.zip``)。
**E(書類の行が付けている要素)は、類分けと「落とした行」の判定にだけ使う。候補の絞り(段 1〜3)の関数には渡さない。** 提出者の ``_lab.xml``・``_pre.xml``・``_def.xml``・``_cal.xml``・``.xsd`` は読まない。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 見出しが「行より前」: 見出しの当たりの始まりの位置(タグを除いた字の上)が、行の位置(行の頭までの字からタグを除いた字の長さ)より **小さい** もの(同じ位置は前に数えない)。その中の最後の 1 つ。
- 見出しは、行を持つ file ごとに、その file の字の中だけで探す(file をまたがない)。
- 業種の値は、PublicDoc の ``_ixbrl.htm`` を file 名の昇順に読み、各 file の中では先に在る当たりから、最初に空でなかった値。
- 業種の folder の集まりは、zip の中の ``jppfs/2025-11-01/r/<folder>/`` の folder 名全部(23)。値がその集まりに無ければ「決まらない」。
- 業種 I が決まるかの数は、K が決まる行のうち I が決まらない行だけ。I が決まり C(I, K) の file が無い行は、段 3 が段 2 のままで、この数には入れない。
- 行の類分けは、便 XG0 の ``classify`` に ``{T: その段の候補}`` の 1 項目の表を渡して使う(候補が空なら N)。
- 率は四捨五入(0.5 は上げる)で小数第 1 位。判定に要る数は丸める前の整数も書く。
"""
from __future__ import print_function

import argparse
import bisect
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

from adapters.xbrl import instance as I                 # noqa: E402
from adapters.xbrl import verify_document as VD         # noqa: E402


def _load_wall():
    u"""便 XG0 の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。"""
    name = "_xg1_tag_wall_2026_11_21"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "xbrl_tag_wall_2026-11-21.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


W = _load_wall()

SEAL_REL = "docs/XBRL_TAG_NARROW_SEAL_2026-11-21.md"
SEAL_COMMIT = "1bda1997"
SCRIPT_REL = "measure/xbrl_tag_narrow_2026-11-21.py"
RECORD_REL = "fixtures/xbrl/cd8/tag_narrow_2026-11-21.json"
PRIOR_RECORD_REL = "fixtures/xbrl/cd8/tag_wall_2026-11-21.json"
DOCS_DIR = W.DOCS_DIR
TAXONOMY_DIR = W.TAXONOMY_DIR
TAXZIP_PATH = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-taxonomy-full", "2025-11-01", "1c_Taxonomy.zip")

# ---- 封 §1・§2 の決めごと(字で留める。封の門が封の字と照らす)
DOCS_WANT = W.DOCS_WANT
TAXZIP_URL = "https://www.fsa.go.jp/search/20251111/1c_Taxonomy.zip"
TAXZIP_SHA256 = "8d57f84802b20a8dc6a517ad6d4768270c294aa6991621d66cb5adb562df5de2"
ZIP_MARK = "/taxonomy/"
XSD_NAME = "jppfs/2025-11-01/jppfs_cor_2025-11-01.xsd"
R_DIR = "jppfs/2025-11-01/r/"
DEF_NAME = "jppfs/2025-11-01/r/%s/jppfs_%s_cm_2025-11-01_def_%s.xml"
KINDS = ("bs", "pl", "ss", "cf")
XSD_NS = "{http://www.w3.org/2001/XMLSchema}"
EXCLUDED_TYPES = ("nonnum:domainItemType", "xbrli:stringItemType")
HREF_RE = re.compile(r'xlink:href="[^"]*#jppfs_cor_([^"]*)"')
FOLDER_RE = re.compile(r"^jppfs/2025-11-01/r/([^/]+)/")
TAG_RE = re.compile(r"<[^>]*>")
HEAD_RE = re.compile(u"【([^】]{0,40})】")
#: 見出しの字(NFKC・空白除きの後)から行の種類 K を決める。上から先に当たったもの
KIND_RULES = ((u"貸借対照表", "bs"), (u"キャッシュ・フロー計算書", "cf"), (u"株主資本等変動計算書", "ss"), (u"損益計算書", "pl"), (u"包括利益計算書", "pl"))
CONSOLIDATED_WORD = u"連結"
DEI_CONSOLIDATED = "jpdei_cor:IndustryCodeWhenConsolidatedFinancialStatementsArePreparedInAccordanceWithIndustrySpecificRegulationsDEI"
DEI_SINGLE = "jpdei_cor:IndustryCodeWhenFinancialStatementsArePreparedInAccordanceWithIndustrySpecificRegulationsDEI"
INDUSTRY_ALIAS = (("cte", "cai"),)
IXBRL_SUFFIX = W.IXBRL_SUFFIX
PUBLICDOC = W.PUBLICDOC
CLASSES = W.CLASSES
STAGES = ("段 0", "段 1", "段 2", "段 3")
ROWS_WANT = 16763
STAGE0_WANT = collections.OrderedDict([("U", 9571), ("A", 6880), ("W", 65), ("N", 247)])
U_DOC_THRESHOLD_PCT = 90
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。(下限, 上限) の % か None
BOUNDS = collections.OrderedDict([
    ("XG1-1", (61, 68)), ("XG1-2", (68, 84)), ("XG1-3", (80, 93)), ("XG1-4", (5, 15)), ("XG1-5", (None, 3)), ("XG1-6", (None, 10)), ("XG1-7", (None, 25))])
LIMITS = [
    u"材料は提出済みの書類で、専用の道具が組んだ後の字。行の字も、計算書の見出しの字も、道具を通った後のもの。原稿の字での率は測れない。この便の U は「上の限り」に近い読み。",
    u"業種のコードは提出済みの書類の DEI から読む。作る側では会社が自分で知っている値だが、この便はそれを答えの入った file から読んでいる。",
    u"67 本は無作為ではない。業種のコードは 1 本を除いて一般商工業。業種の段は、ほぼ 1 つの業種でしか試されない。",
    u"ラベルも科目の一覧も 2025-11-01 版の 1 つだけ。書類が古い版の要素を使っている所は、当たらないか落とす側に出る。",
    u"測るのは要素の名だけ。期・連結か個別か・単位・桁・提出者別の要素を新しく作る所・表示の並び・計算の関係は測っていない。注記と jpcrp の欄・便 XG0 の分母の外の行も測っていない。",
    u"「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」は、この便からは言えない。"]

Stop = W.Stop
od = collections.OrderedDict
sha256_bytes = W.sha256_bytes
sha256_file = W.sha256_file
dumps = W.dumps
pct1 = W.pct1
norm_label = W.norm_label
local_of = W.local_of


# ======================================================================================================
# 標準タクソノミ(封 §1)
def rel_name(name):
    u"""zip の中の file の名の ``/taxonomy/`` より後ろの字。無ければ None(頭の folder の名は日本語で、読み方に頼らない)。"""
    if ZIP_MARK not in name:
        return None
    return name.split(ZIP_MARK, 1)[1]


def build_x(xsd_bytes):
    u"""要素の表 X: ``xsd:element`` の ``name`` → (type, abstract)。"""
    root = ET.fromstring(xsd_bytes)
    out = {}
    for el in root.iter(XSD_NS + "element"):
        nm = el.get("name")
        if nm:
            out[nm] = (el.get("type") or u"", el.get("abstract") or u"")
    return out


def numeric_elements(x):
    u"""段 1 が残す要素の集まり: X に在り、abstract が ``true`` でなく、type が domainItemType でも stringItemType でもない。"""
    return set(nm for nm, (ty, ab) in x.items() if ab != "true" and ty not in EXCLUDED_TYPES)


def build_c(def_text):
    u"""科目の一覧 C: def の字の ``xlink:href`` のうち ``#jppfs_cor_`` に続く局所名の集まり。"""
    return set(HREF_RE.findall(def_text))


def union_by_kind(c):
    u"""{K: どれかの業種 I の C(I, K) の和集合}。"""
    out = dict((k, set()) for k in KINDS)
    for (_i, k), s in c.items():
        out[k] |= s
    return out


def make_tax(x, c, folders):
    return dict(numeric=numeric_elements(x), c=c, union=union_by_kind(c), folders=set(folders))


def read_taxzip(path):
    u"""zip の sha256 が封の字と違えば止まる。(bytes を読んだ ZipFile 用の path, sha256)。"""
    try:
        sha = sha256_file(path)
    except OSError:
        raise Stop(u"**標準タクソノミの zip を読めない。止める**")
    if sha != TAXZIP_SHA256:
        raise Stop(u"**標準タクソノミの zip の sha256 が封と違う。止める**")
    return sha


def load_tax(path, check_sha=True):
    u"""zip → (tax, 材料の数)。要素の表・業種の folder・科目の一覧(file が在る (I, K) だけ)。"""
    sha = read_taxzip(path) if check_sha else sha256_file(path)
    with zipfile.ZipFile(path) as z:
        rels = {}
        for n in z.namelist():
            r = rel_name(n)
            if r is not None:
                rels[r] = n
        if XSD_NAME not in rels:
            raise Stop(u"**要素の表の xsd が zip に無い。止める**")
        x = build_x(z.read(rels[XSD_NAME]))
        folders = sorted(set(m.group(1) for m in (FOLDER_RE.match(r) for r in rels) if m))
        c = {}
        for i in folders:
            for k in KINDS:
                nm = DEF_NAME % (i, i, k)
                if nm in rels:
                    c[(i, k)] = build_c(z.read(rels[nm]).decode("utf-8", "replace"))
    tax = make_tax(x, c, folders)
    mat = od([(u"要素の表の要素の数", len(x)), (u"段 1 が残す要素の数", len(tax["numeric"])), (u"業種の folder の数", len(folders)), (u"科目の一覧の数", len(c))])
    return tax, sha, mat


# ======================================================================================================
# 見出し・種類・業種(封 §2-2・§2-3)
def strip_tags(s):
    return TAG_RE.sub(u"", s)


def file_rows(text):
    u"""file の字 → [(行の字, その行より前の最後の見出しの中の字か None)]。行の切り方は engine の ``_TR_RE``。見出しは ``【([^】]{0,40})】`` の当たり(タグを除いた字の上)。
    見出しが前に在るのは、見出しの当たりの始まりの位置が、行の位置(行の頭までの字からタグを除いた字の長さ)より小さいとき。"""
    spans = [(m.start(), m.end()) for m in TAG_RE.finditer(text)]
    starts = [s for s, _e in spans]
    cum = [0]
    for s, e in spans:
        cum.append(cum[-1] + (e - s))
    heads = [(m.start(), m.group(1)) for m in HEAD_RE.finditer(strip_tags(text))]
    hpos = [h[0] for h in heads]
    out = []
    for m in I._TR_RE.finditer(text):
        p = m.start()
        k = bisect.bisect_left(starts, p)
        removed = cum[k]
        if k and spans[k - 1][1] > p:
            removed -= spans[k - 1][1] - p
        pos = p - removed
        j = bisect.bisect_left(hpos, pos)
        out.append((m.group(0), heads[j - 1][1] if j else None))
    return out


def kind_of(heading):
    u"""見出しの字 → ``bs``・``cf``・``ss``・``pl`` か None(見出しが無い・どれも含まない)。NFKC にそろえ空白の字を除いた字で、上から先に当たったもの。"""
    if heading is None:
        return None
    t = norm_label(heading)
    for word, k in KIND_RULES:
        if word in t:
            return k
    return None


def dei_value(text, name):
    u"""``name`` の ``ix:nonNumeric`` の中身からタグと空白の字を除いて小文字にした字のうち、先に在る空でないもの。無ければ空の字。"""
    pat = re.compile(r'<ix:nonNumeric\b[^>]*?\bname="%s"[^>]*>(.*?)</ix:nonNumeric>' % re.escape(name), re.S | re.I)
    for m in pat.finditer(text):
        v = W.WS_RE.sub(u"", strip_tags(m.group(1))).lower()
        if v:
            return v
    return u""


def dei_values(texts):
    u"""[(file 名, 字)] を file 名の昇順に読み、(連結の欄, 個別の欄) の最初の空でない値(無ければ空の字)。"""
    out = []
    for name in (DEI_CONSOLIDATED, DEI_SINGLE):
        v = u""
        for _n, t in sorted(texts, key=lambda p: p[0]):
            v = dei_value(t, name)
            if v:
                break
        out.append(v)
    return tuple(out)


def industry_of(heading, dei, folders):
    u"""見出しに ``連結`` が在れば連結の欄・無ければ個別の欄の値(``cte`` は ``cai``)。空・folder が無い値・見出しが無いときは None。"""
    if heading is None:
        return None
    v = dei[0] if CONSOLIDATED_WORD in norm_label(heading) else dei[1]
    for a, b in INDUSTRY_ALIAS:
        if v == a:
            v = b
    return v if v and v in folders else None


# ======================================================================================================
# 3 つの段(封 §2。E は渡さない)
def stage1(cand0, tax):
    return set(cand0) & tax["numeric"]


def stage2(cand1, kind, tax):
    if kind is None:
        return set(cand1)
    return set(cand1) & tax["union"].get(kind, set())


def stage3(cand1, cand2, kind, ind, tax):
    if kind is not None and ind is not None and (ind, kind) in tax["c"]:
        return set(cand1) & tax["c"][(ind, kind)]
    return set(cand2)


def narrow(cand0, kind, ind, tax):
    u"""(cand1, cand2, cand3)。"""
    c1 = stage1(cand0, tax)
    c2 = stage2(c1, kind, tax)
    c3 = stage3(c1, c2, kind, ind, tax)
    return c1, c2, c3


def classify_stage(T, E, cand):
    u"""類 U・A・W・N(便 XG0 の ``classify``)。候補が空なら N。"""
    return W.classify(T, E, {T: set(cand)})


def is_dropped(E, cand0, cand):
    u"""絞りで正しい要素を落とした: E が cand0 に在り、その段の候補に無い。"""
    return E in cand0 and E not in cand


def new_doc():
    return od([("stages", od((s, od((c, 0) for c in CLASSES)) for s in STAGES)), ("dropped", od((s, 0) for s in STAGES[1:])),
               ("kinds", od((k, 0) for k in KINDS)), ("k_none", 0), ("i_none", 0)])


def add_row(acc, T, E, cand0, kind, ind, tax):
    u"""行 1 つを数える。"""
    c1, c2, c3 = narrow(cand0, kind, ind, tax)
    cands = (cand0, c1, c2, c3)
    for s, cd in zip(STAGES, cands):
        acc["stages"][s][classify_stage(T, E, cd)] += 1
    for s, cd in zip(STAGES[1:], cands[1:]):
        if is_dropped(E, cand0, cd):
            acc["dropped"][s] += 1
    if kind is None:
        acc["k_none"] += 1
    else:
        acc["kinds"][kind] += 1
        if ind is None:
            acc["i_none"] += 1


def count_doc(texts, l2, tax, secret=None):
    u"""書類 1 本([(file 名, 字)] の PublicDoc の ``_ixbrl.htm``)を数える。"""
    texts = sorted(texts, key=lambda p: p[0])
    dei = dei_values(texts)
    acc = new_doc()
    for _n, text in texts:
        for rowtext, head in file_rows(text):
            st = W.row_status(rowtext)
            if st[0] != "ok":
                continue
            _k, T, E = st
            kind = kind_of(head)
            ind = industry_of(head, dei, tax["folders"]) if kind is not None else None
            add_row(acc, T, E, set(l2.get(T, ())), kind, ind, tax)
            if secret is not None:
                secret[0].add(T)
                secret[1].add(E)
                if head is not None:
                    secret[4].add(norm_label(head))
    if secret is not None:
        secret[5].update(v for v in dei if v)
    return acc


def doc_texts(z):
    return [(n, z.read(n).decode("utf-8", "replace")) for n in sorted(z.namelist()) if n.startswith(PUBLICDOC) and n.endswith(IXBRL_SUFFIX)]


def doc_rows(acc):
    return sum(acc["stages"]["段 0"].values())


def add_into(tot, acc):
    for s in STAGES:
        for c in CLASSES:
            tot["stages"][s][c] += acc["stages"][s][c]
    for s in STAGES[1:]:
        tot["dropped"][s] += acc["dropped"][s]
    for k in KINDS:
        tot["kinds"][k] += acc["kinds"][k]
    tot["k_none"] += acc["k_none"]
    tot["i_none"] += acc["i_none"]


def totals(accs):
    u"""書類ごとの数 → 合計。"""
    tot = new_doc()
    for a in accs:
        add_into(tot, a)
    return tot


def check_expected(tot, rows_want=ROWS_WANT, stage0_want=STAGE0_WANT, prior=None):
    u"""計算書の行の合計が 16763 でなければ止まる。段 0 の U・A・W・N が封の字(便 XG0 の記録の数)と違えば止まる。``prior`` があれば、その記録の数とも照らす。"""
    rows = doc_rows(tot)
    if rows_want is not None and rows != rows_want:
        raise Stop(u"**計算書の行の合計が %d でない(%d)。止める**" % (rows_want, rows))
    if stage0_want is not None and list(tot["stages"]["段 0"].values()) != list(stage0_want.values()):
        raise Stop(u"**段 0 の U・A・W・N が封の字と違う。止める**")
    if prior is not None:
        agg = prior[u"集計"]
        if agg[u"計算書の行の数"] != rows or list(agg[u"類別(表 L2)"].values()) != list(tot["stages"]["段 0"].values()):
            raise Stop(u"**段 0 の数が便 XG0 の記録と違う。止める**")


# ======================================================================================================
# 記録
def rate_of(n, d):
    return od([(u"行", n), (u"分母", d), (u"%", pct1(n, d))])


def build_record(docs_dir=None, taxonomy_dir=None, taxzip=None, want=DOCS_WANT, expect=True, prior_path=None, check_sha=True):
    u"""置き場 → (記録, 漏れの検査に使う材料)。書かない。``expect`` が False なら 16763・段 0 の止めを掛けない(封の門の作り物の置き場だけ)。"""
    docs = W.select_docs(docs_dir or DOCS_DIR, want)
    label_data, label_sha = W.read_label_bytes(taxonomy_dir or TAXONOMY_DIR)
    l2 = W.label_tables(label_data)[0]
    tax, zip_sha, tmat = load_tax(taxzip or TAXZIP_PATH, check_sha)
    fp = VD.engine_fingerprint()
    secret = (set(), set(), [d[0] for d in docs], set(), set(), set())     # (行の字, 要素の局所名, docID, EDINET コード, 見出しの字, 業種の値)
    for _stem, _p, xs in docs:
        for x in xs:
            secret[3].update(re.findall(r"E\d{5}", x))
    accs = []
    rows_out = []
    docs_with_rows = docs_u90 = 0
    for n, (_stem, p, _xs) in enumerate(docs, 1):
        with zipfile.ZipFile(p) as z:
            acc = count_doc(doc_texts(z), l2, tax, secret)
        accs.append(acc)
        r = doc_rows(acc)
        u3 = acc["stages"]["段 3"]["U"]
        if r:
            docs_with_rows += 1
            if 100 * u3 >= U_DOC_THRESHOLD_PCT * r:
                docs_u90 += 1
        rows_out.append(od([
            (u"番号", n), (u"計算書の行の数", r),
            (u"段ごとの類別", od((s, od(acc["stages"][s])) for s in STAGES)),
            (u"段ごとの落とした行", od(acc["dropped"])),
            (u"種類 K ごとの行", od(acc["kinds"])), (u"K が決まらない行", acc["k_none"]), (u"K が決まり I が決まらない行", acc["i_none"]),
            (u"段 3 の U の率(%)", pct1(u3, r))]))
    tot = totals(accs)
    prior = None
    if expect:
        pp = prior_path or os.path.join(ROOT, PRIOR_RECORD_REL)
        if not os.path.isfile(pp):
            raise Stop(u"**便 XG0 の記録が無い。止める**")
        with io.open(pp, encoding="utf-8") as fh:
            prior = json.load(fh, object_pairs_hook=collections.OrderedDict)
    check_expected(tot, ROWS_WANT if expect else None, STAGE0_WANT if expect else None, prior)
    rows_all = doc_rows(tot)
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XG1(便 XG0 で候補が 2 つ以上だった行を、数を持てる要素・計算書の種類・業種の科目の一覧で絞ると、要素が 1 つに決まる行はどれだけ増えるか)(0 USD・engine は 0 行)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"engine の指紋"] = od((k, fp[k]) for k in ("adapter_xbrl_py_sha256", "adapter_xbrl_py_files", "core_py_sha256", "core_py_files"))
    mat = od([
        (u"書類の本数", len(docs)),
        (u"書類の file 名の並びの sha256", W.order_sha256([d[0] for d in docs])),
        (u"標準ラベルの file の sha256", label_sha),
        (u"表 L2 のラベルの字の数", len(l2)),
        (u"標準タクソノミの zip の sha256", zip_sha)])
    mat.update(tmat)
    rec[u"材料"] = mat
    rec[u"書類"] = rows_out
    rec[u"集計"] = od([
        (u"計算書の行の数", rows_all),
        (u"段ごとの類別", od((s, od(tot["stages"][s])) for s in STAGES)),
        (u"段ごとの落とした行", od(tot["dropped"])),
        (u"種類 K ごとの行", od(tot["kinds"])), (u"K が決まらない行", tot["k_none"]), (u"K が決まり I が決まらない行", tot["i_none"]),
        (u"計算書の行が 1 行以上在る書類の数", docs_with_rows)])
    st = tot["stages"]
    rec[u"予測の判定に要る数(XG1-1〜XG1-7。当たり・外れは結果の文書で)"] = od([
        (u"XG1-1 段 1 の類 U / 計算書の行", rate_of(st["段 1"]["U"], rows_all)),
        (u"XG1-2 段 2 の類 U / 計算書の行", rate_of(st["段 2"]["U"], rows_all)),
        (u"XG1-3 段 3 の類 U / 計算書の行", rate_of(st["段 3"]["U"], rows_all)),
        (u"XG1-4 段 3 の類 A / 計算書の行", rate_of(st["段 3"]["A"], rows_all)),
        (u"XG1-5 段 3 で正しい要素を落とした行 / 計算書の行", rate_of(tot["dropped"]["段 3"], rows_all)),
        (u"XG1-6 種類 K が決まらない行 / 計算書の行", rate_of(tot["k_none"], rows_all)),
        (u"XG1-7 段 3 の U の率が %d%% 以上の書類 / 計算書の行が 1 行以上在る書類" % U_DOC_THRESHOLD_PCT, od([(u"書類", docs_u90), (u"分母", docs_with_rows)]))])
    rec[u"限界"] = list(LIMITS)
    return rec, secret


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(便 XG0 の検査 + 見出しの字・業種の値)が無いか。在れば止める。secret = (行の字, 要素の局所名, docID, EDINET コード, 見出しの字, 業種の値)。"""
    W.check_clean(rec, text, secret[:4] if secret else None)
    if secret:
        heads, inds = secret[4], secret[5]
        scan = W.HEX_RE.sub(u"", text)
        tokens = set(W.TOKEN_RE.findall(scan))
        if tokens & set(inds):
            raise Stop(u"**記録に業種のコードの値が在る。止める**")
        strs = set(W.walk_strings(rec))
        if strs & set(heads):
            raise Stop(u"**記録に見出しの字が在る。止める**")
        for h in heads:
            if len(h) >= W.LABEL_SUBSTRING_MIN and h in scan:
                raise Stop(u"**記録に見出しの字が在る。止める**")


def record_text(rec, secret=None):
    text = dumps(rec)
    check_clean(rec, text, secret)
    return text


def write_record(path, rec, secret=None):
    u"""書く前と書いた後に検査する。既に在れば止める(測り直さない)。"""
    if os.path.exists(path):
        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(path))
    text = record_text(rec, secret)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_exclusive(path, text.encode("utf-8"))
    with io.open(path, encoding="utf-8") as fh:
        back = fh.read()
    try:
        check_clean(rec, back, secret)
    except SystemExit:
        os.remove(path)
        raise


def write_exclusive(path, data):
    with open(path, "xb") as fh:
        fh.write(data)


def run(root=ROOT, docs=None, taxonomy=None, taxzip=None, out=None, want=DOCS_WANT, expect=True, prior_path=None, check_sha=True, say=print):
    rec, secret = build_record(docs, taxonomy, taxzip, want, expect, prior_path, check_sha)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    say(u"-> %s(書類 %d)" % (os.path.basename(out), rec[u"材料"][u"書類の本数"]))
    return rec


def check(root=ROOT, docs=None, taxonomy=None, taxzip=None, rec_path=None, want=DOCS_WANT, expect=True, prior_path=None, check_sha=True, say=print):
    u"""置き場から数え直して記録と照らす。通信しない。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    now, secret = build_record(docs, taxonomy, taxzip, want, expect, prior_path, check_sha)
    if dumps(now) != dumps(rec):
        raise Stop(u"**置き場から数え直した記録が、今の記録と違う。止める**")
    check_clean(rec, text, secret)
    say(u"--check: 記録は置き場から数え直した数と同じ(書類 %d)" % now[u"材料"][u"書類の本数"])
    return now


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="置き場から数え直して記録と照らす。通信しない")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--docs", default=None, help="書類の置き場(既定は封の字)")
    ap.add_argument("--taxonomy", default=None, help="標準ラベルの置き場(既定は封の字)")
    ap.add_argument("--taxzip", default=None, help="標準タクソノミの zip(既定は封の字)")
    a = ap.parse_args(argv)
    if a.check:
        check(root=a.root, docs=a.docs, taxonomy=a.taxonomy, taxzip=a.taxzip)
    else:
        run(root=a.root, docs=a.docs, taxonomy=a.taxonomy, taxzip=a.taxzip)


if __name__ == "__main__":
    main()
