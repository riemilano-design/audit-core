# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TAG_WALL_SEAL_2026-11-21.md(XG0 ― 有価証券報告書の計算書の行で、行の字と標準タクソノミの表だけで XBRL の要素が 1 つに決まる行はどれだけか。XBRL を作る側の壁の確かめ)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。通信しない。** engine(``core/``・``adapters/``)は 1 行も変えない。行の切り方(``_TR_RE``)・行の字(``_row_label``)・ラベルの読み取り(``parse_label_linkbase``)・
標準ラベルの file の読み取りと sha256 の照合(``_read_taxonomy_file``・``TAXONOMY_LABEL_FILES``)は engine の関数を呼ぶ(写さない)。

    python3 measure/xbrl_tag_wall_2026-11-21.py            # 置き場から数えて記録 fixtures/xbrl/cd8/tag_wall_2026-11-21.json を書く。通信しない
    python3 measure/xbrl_tag_wall_2026-11-21.py --check    # 置き場から数え直して記録と照らす。通信しない

置き場の既定は封の字(書類 ``~/.cache/audit-core/edinet/``・標準ラベル ``~/.cache/audit-core/edinet-taxonomy/2025-11-01/``)。``--docs``・``--taxonomy`` で差し替えられる(封の門が作り物の置き場を渡す)。
書類が 67 本でなければ止まる。記録には docID・会社の名・EDINET コード・行の字・要素の名を書かない。書く前と書いた後に検査し、在れば止まる。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 標準の判定: 接頭辞 P の頭が ``jp`` で、``_cor`` で終わるもの(封 §2-1 の括弧の中の字)。``jppfs_cor``・``jpcrp_cor``・``jpigp_cor``・``jpdei_cor`` は全部これに当たる。名に ``:`` が無ければ提出者別に数える。
- (b)(c)(d) は順に見て、最初に満たさなかった 1 つだけに数える(足すと分母に入れなかった行の数になる)。ix:nonFraction が 1 つも無い行(a)は数えない。
- 行の字の NFKC・空白除きは ``norm_label`` 1 本を表の側と行の側の両方に掛ける。
- 「当たる」= 正規化した字の完全な一致。表 L2 は role の末尾が ``Label`` か ``label`` の role 全部の和集合(要素の局所名の集まり)。要素の局所名は engine の ``taxonomy_label_map`` と同じく ``_cor_`` の後ろ。
- 材料の並びの sha256 = zip の file 名(拡張子を除く)を昇順に並べ、``\\n`` でつないだ字(最後に改行を付けない)の UTF-8 の sha256。
- 率は四捨五入(0.5 は上げる)で小数第 1 位。判定に要る数は丸める前の整数も書く。
"""
from __future__ import print_function

import argparse
import collections
import glob
import hashlib
import io
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

from adapters.xbrl import instance as I                 # noqa: E402
from adapters.xbrl import verify_document as VD         # noqa: E402

SEAL_REL = "docs/XBRL_TAG_WALL_SEAL_2026-11-21.md"
SEAL_COMMIT = "3374e504"
SCRIPT_REL = "measure/xbrl_tag_wall_2026-11-21.py"
RECORD_REL = "fixtures/xbrl/cd8/tag_wall_2026-11-21.json"
DOCS_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
TAXONOMY_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-taxonomy", "2025-11-01")

# ---- 封 §1 の決めごと(字で留める。封の門が封の字と照らす)
DOCS_WANT = 67
XSD_PREFIX = "jpcrp030000-asr"
PUBLICDOC = "XBRL/PublicDoc/"
IXBRL_SUFFIX = "_ixbrl.htm"
LABEL_FILE = "jppfs_2025-11-01_lab.xml"
STANDARD_ROLE = "http://www.xbrl.org/2003/role/label"
ROLE_SUFFIXES = ("Label", "label")
STATEMENT_PREFIX = "jppfs_cor"
CLASSES = ("U", "A", "W", "N")
U_DOC_THRESHOLD_PCT = 90                       # XG0-5: U の率がこれ以上の書類
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。(下限, 上限) の % か None
BOUNDS = collections.OrderedDict([
    ("XG0-1", (None, 5)), ("XG0-2", (60, 85)), ("XG0-3", (None, 5)), ("XG0-4", (5, 25)), ("XG0-5", (None, 10)), ("XG0-6", (5, None))])
LIMITS = [
    u"材料は提出済みの書類で、専用の道具が組んだ後の字。道具が標準のラベルを行の字として入れている所は当たって当然で、この率は「上の限り」に近い読み。",
    u"67 本は過去の便のために置き場に在った書類で、無作為ではない。日本基準が 65 本。",
    u"測るのは要素の名だけ。期・連結か個別か・単位・桁・提出者別の要素を新しく作る所・表示の並び・計算の関係・注記と jpcrp の欄は測っていない。",
    u"「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」は、この便からは言えない。"]

NF_RE = re.compile(r'<ix:nonFraction\b[^>]*?\bname="([^"]+)"', re.I)
WS_RE = re.compile(r"[\s ]+")

# ---- 記録の禁止(封 §5)。欄の名(小文字にして照らす)と、字の形
FORBIDDEN_KEYS = ("docid", "doc_id", "edinet", "edinetcode", "company", "name", "label", "row", "element", "tag",
                  u"会社の名", u"会社名", u"書類id", u"行の字", u"要素の名", u"要素名", u"ラベル", u"提出者名")
ECODE_FORM_RE = re.compile(r"(?<![0-9A-Za-z])E\d{5}(?![0-9A-Za-z])")
DOCID_FORM_RE = re.compile(r"(?<![0-9A-Za-z])S[0-9A-Z]{7}(?![0-9A-Za-z])")
HEX_RE = re.compile(r"[0-9a-fA-F]{32,}")
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
LABEL_SUBSTRING_MIN = 5


class Stop(SystemExit):
    pass


def od(pairs=()):
    return collections.OrderedDict(pairs)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    with open(path, "rb") as fh:
        return sha256_bytes(fh.read())


def dumps(o):
    return json.dumps(o, ensure_ascii=False, indent=2) + u"\n"


def walk_keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            for x in walk_keys(v):
                yield x
    elif isinstance(o, list):
        for v in o:
            for x in walk_keys(v):
                yield x


def walk_strings(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield str(k)
            for x in walk_strings(v):
                yield x
    elif isinstance(o, list):
        for v in o:
            for x in walk_strings(v):
                yield x
    elif isinstance(o, str):
        yield o


def pct1(n, d):
    u"""n/d の % を小数第 1 位まで四捨五入(0.5 は上げる)。d が 0 なら None。符号は付けたまま。"""
    if not d:
        return None
    sign = -1 if n < 0 else 1
    tenths = (2000 * abs(n) + d) // (2 * d)
    return sign * tenths / 10.0


# ======================================================================================================
# ラベルの表(封 §1)
def norm_label(s):
    u"""NFKC にそろえ、空白の字(``\\s`` と U+00A0)を全部除く。表の側と行の側の両方に掛ける。"""
    return WS_RE.sub(u"", unicodedata.normalize("NFKC", s))


def local_of(full):
    return full.split("_cor_")[-1] if "_cor_" in full else full


def label_roles(data):
    u"""ラベル linkbase に在る ``xlink:role`` の値のうち、末尾が ``Label`` か ``label`` のもの(昇順)。"""
    root = ET.fromstring(data)
    roles = set()
    for el in root.iter():
        if el.tag.split("}")[-1] == "label":
            r = el.get(I.XLINK + "role") or ""
            if r.endswith(ROLE_SUFFIXES):
                roles.add(r)
    return sorted(roles)


def label_tables(data):
    u"""(表 L2, 表 L1)。どちらも {正規化したラベルの字: {要素の局所名}}。L2 = 末尾が Label/label の role 全部。L1 = 標準の role だけ。"""
    l2, l1 = {}, {}
    for r in label_roles(data):
        for full, word in I.parse_label_linkbase(data, role=r).items():
            key = norm_label(word)
            if not key:
                continue
            l2.setdefault(key, set()).add(local_of(full))
            if r == STANDARD_ROLE:
                l1.setdefault(key, set()).add(local_of(full))
    return l2, l1


def read_label_bytes(taxonomy_dir):
    u"""標準ラベルの file を engine の読み取りで読む(sha256 は engine の ``TAXONOMY_LABEL_FILES`` の字と照らす)。(bytes, sha256)。"""
    sha = dict((fn, s) for _ns, fn, s in I.TAXONOMY_LABEL_FILES).get(LABEL_FILE)
    if sha is None:
        raise Stop(u"**engine の標準ラベルの一覧に %s が無い。止める**" % LABEL_FILE)
    try:
        return I._read_taxonomy_file(taxonomy_dir, LABEL_FILE, sha)
    except (OSError, ValueError) as exc:
        raise Stop(u"**標準ラベルの file を読めない(無いか sha256 が違う): %s。止める**" % type(exc).__name__)


# ======================================================================================================
# 書類(封 §1)
def doc_xsd_names(z):
    return [n for n in z.namelist() if n.startswith(PUBLICDOC) and n.endswith(".xsd")]


def select_docs(docs_dir, want=DOCS_WANT):
    u"""置き場の zip のうち PublicDoc の .xsd の file 名が ``jpcrp030000-asr`` で始まるもの。[(file 名の stem, path, xsd の名の並び)] を昇順で。本数が ``want`` でなければ止まる。"""
    found = []
    for p in sorted(glob.glob(os.path.join(docs_dir, "*.zip"))):
        try:
            with zipfile.ZipFile(p) as z:
                xs = [os.path.basename(n) for n in doc_xsd_names(z)]
        except zipfile.BadZipFile:
            raise Stop(u"**zip が読めない。止める**")
        if any(x.startswith(XSD_PREFIX) for x in xs):
            found.append((os.path.basename(p)[:-4], p, xs))
    found.sort(key=lambda t: t[0])
    if len(found) != want:
        raise Stop(u"**有価証券報告書の zip が %d 本でない(%d 本)。止める**" % (want, len(found)))
    return found


def order_sha256(stems):
    return sha256_bytes(u"\n".join(sorted(stems)).encode("utf-8"))


# ======================================================================================================
# 数える(封 §2)
def is_standard(prefix):
    return prefix.startswith("jp") and prefix.endswith("_cor")


def row_status(row):
    u"""``<tr>`` 1 行 → ``("none",)``(ix:nonFraction が無い)・``("b",)``・``("c",)``・``("d",)``(分母に入れない)・``("ok", 行の字 T, 要素 E)``。"""
    names = NF_RE.findall(row)
    if not names:
        return ("none",)
    if len(set(names)) != 1:
        return ("b",)
    if names[0].split(":")[0] != STATEMENT_PREFIX:
        return ("c",)
    label = I._row_label(row)
    if not label:
        return ("d",)
    return ("ok", norm_label(label), names[0].split(":")[-1])


def classify(T, E, table):
    u"""類 U・A・W・N(封 §2-3)。"""
    cands = table.get(T)
    if not cands:
        return "N"
    if E not in cands:
        return "W"
    return "U" if len(cands) == 1 else "A"


def new_doc():
    return od([("std", 0), ("sub", 0), ("b", 0), ("c", 0), ("d", 0),
               ("l2", od((c, 0) for c in CLASSES)), ("l1", od((c, 0) for c in CLASSES))])


def analyze_text(text, tabs, acc, secret):
    l2, l1 = tabs
    for name in NF_RE.findall(text):
        acc["std" if is_standard(name.split(":")[0]) else "sub"] += 1
    for row in I._TR_RE.findall(text):
        st = row_status(row)
        if st[0] in ("b", "c", "d"):
            acc[st[0]] += 1
        elif st[0] == "ok":
            _k, T, E = st
            acc["l2"][classify(T, E, l2)] += 1
            acc["l1"][classify(T, E, l1)] += 1
            secret[0].add(T)
            secret[1].add(E)


def analyze_zip(z, tabs, secret):
    l2, l1 = tabs
    acc = new_doc()
    for n in sorted(z.namelist()):
        if n.startswith(PUBLICDOC) and n.endswith(IXBRL_SUFFIX):
            analyze_text(z.read(n).decode("utf-8", "replace"), (l2, l1), acc, secret)
    return acc


def doc_rows(acc):
    return sum(acc["l2"].values())


# ======================================================================================================
# 記録
def build_record(docs_dir=None, taxonomy_dir=None, want=DOCS_WANT):
    u"""置き場 → (記録, 漏れの検査に使う材料)。書かない。"""
    docs = select_docs(docs_dir or DOCS_DIR, want)
    label_data, label_sha = read_label_bytes(taxonomy_dir or TAXONOMY_DIR)
    tabs = label_tables(label_data)
    fp = VD.engine_fingerprint()
    secret = (set(), set(), [d[0] for d in docs], set())            # (行の字, 要素の局所名, docID, EDINET コード)
    for _stem, _p, xs in docs:
        for x in xs:
            secret[3].update(re.findall(r"E\d{5}", x))
    rows = []
    tot = od([("std", 0), ("sub", 0), ("b", 0), ("c", 0), ("d", 0), ("l2", od((c, 0) for c in CLASSES)), ("l1", od((c, 0) for c in CLASSES))])
    docs_with_rows = 0
    docs_u90 = 0
    for n, (_stem, p, _xs) in enumerate(docs, 1):
        with zipfile.ZipFile(p) as z:
            acc = analyze_zip(z, tabs, secret)
        r = doc_rows(acc)
        rate = pct1(acc["l2"]["U"], r)
        if r:
            docs_with_rows += 1
            if 100 * acc["l2"]["U"] >= U_DOC_THRESHOLD_PCT * r:
                docs_u90 += 1
        for k in ("std", "sub", "b", "c", "d"):
            tot[k] += acc[k]
        for c in CLASSES:
            tot["l2"][c] += acc["l2"][c]
            tot["l1"][c] += acc["l1"][c]
        rows.append(od([
            (u"番号", n),
            (u"タグの数", od([(u"標準", acc["std"]), (u"提出者別", acc["sub"])])),
            (u"計算書の行の数", r),
            (u"分母に入れなかった行の数", od([(u"(b) 名が 2 つ以上", acc["b"]), (u"(c) 接頭辞が jppfs_cor 以外", acc["c"]), (u"(d) 行の字が無い", acc["d"])])),
            (u"類別(表 L2)", od((c, acc["l2"][c]) for c in CLASSES)),
            (u"類別(表 L1)", od((c, acc["l1"][c]) for c in CLASSES)),
            (u"U の率(表 L2。%)", rate)]))
    rows_all = sum(tot["l2"].values())
    tags_all = tot["std"] + tot["sub"]
    u2, u1 = tot["l2"]["U"], tot["l1"]["U"]
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XG0(有価証券報告書の計算書の行で、行の字と標準タクソノミの表だけで要素が 1 つに決まる行はどれだけか。XBRL を作る側の壁の確かめ)(0 USD・engine は 0 行)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"engine の指紋"] = od((k, fp[k]) for k in ("adapter_xbrl_py_sha256", "adapter_xbrl_py_files", "core_py_sha256", "core_py_files"))
    rec[u"材料"] = od([
        (u"書類の本数", len(docs)),
        (u"書類の file 名の並びの sha256", order_sha256([d[0] for d in docs])),
        (u"標準ラベルの file の sha256", label_sha),
        (u"表 L2 の role の数", len(label_roles(label_data))),
        (u"表 L2 のラベルの字の数", len(tabs[0])), (u"表 L1 のラベルの字の数", len(tabs[1]))])
    rec[u"書類"] = rows
    rec[u"集計"] = od([
        (u"タグの数", od([(u"標準", tot["std"]), (u"提出者別", tot["sub"])])),
        (u"計算書の行の数", rows_all),
        (u"分母に入れなかった行の数", od([(u"(b) 名が 2 つ以上", tot["b"]), (u"(c) 接頭辞が jppfs_cor 以外", tot["c"]), (u"(d) 行の字が無い", tot["d"])])),
        (u"類別(表 L2)", od((c, tot["l2"][c]) for c in CLASSES)),
        (u"類別(表 L1)", od((c, tot["l1"][c]) for c in CLASSES)),
        (u"計算書の行が 1 行以上在る書類の数", docs_with_rows), (u"計算書の行が 0 で書類ごとの数から外した書類の数", len(docs) - docs_with_rows)])
    ord_rate = lambda n: od([(u"行", n), (u"分母", rows_all), (u"%", pct1(n, rows_all))])      # noqa: E731
    rec[u"予測の判定に要る数(XG0-1〜XG0-6。当たり・外れは結果の文書で)"] = od([
        (u"XG0-1 提出者別のタグ / 全部のタグ", od([(u"タグ", tot["sub"]), (u"分母", tags_all), (u"%", pct1(tot["sub"], tags_all))])),
        (u"XG0-2 類 U / 計算書の行(表 L2)", ord_rate(tot["l2"]["U"])),
        (u"XG0-3 類 W / 計算書の行(表 L2)", ord_rate(tot["l2"]["W"])),
        (u"XG0-4 類 A / 計算書の行(表 L2)", ord_rate(tot["l2"]["A"])),
        (u"XG0-5 U の率が %d%% 以上の書類(表 L2)" % U_DOC_THRESHOLD_PCT, od([(u"書類", docs_u90), (u"分母", docs_with_rows)])),
        (u"XG0-6 表 L1 と表 L2 の U の率", od([
            (u"表 L2 の U の行", u2), (u"表 L1 の U の行", u1), (u"分母", rows_all),
            (u"表 L2 の %", pct1(u2, rows_all)), (u"表 L1 の %", pct1(u1, rows_all)),
            (u"L2 から L1 を引いた差(ポイント)", pct1(u2 - u1, rows_all))]))])
    rec[u"限界"] = list(LIMITS)
    return rec, secret


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(欄・字の形・材料の字)が無いか。在れば止める。secret = (行の字の集まり, 要素の局所名の集まり, docID の並び, EDINET コードの集まり)。"""
    bad = sorted(set(str(k) for k in walk_keys(rec) if str(k).lower() in FORBIDDEN_KEYS))
    if bad:
        raise Stop(u"**記録に repo へ入れない欄がある: %s。止める**" % u",".join(bad))
    scan = HEX_RE.sub(u"", text)
    if ECODE_FORM_RE.search(scan):
        raise Stop(u"**記録に EDINET コードの形の字が在る。止める**")
    if DOCID_FORM_RE.search(scan):
        raise Stop(u"**記録に docID の形の字が在る。止める**")
    if secret:
        labels, elems, ids, ecodes = secret
        tokens = set(TOKEN_RE.findall(scan))
        if tokens & set(ids) or tokens & set(ecodes):
            raise Stop(u"**記録に材料の docID か EDINET コードが在る。止める**")
        if tokens & set(e for e in elems if len(e) >= 3):
            raise Stop(u"**記録に要素の名が在る。止める**")
        strs = set(walk_strings(rec))
        if strs & set(labels):
            raise Stop(u"**記録に行の字が在る。止める**")
        for lab in labels:
            if len(lab) >= LABEL_SUBSTRING_MIN and lab in scan:
                raise Stop(u"**記録に行の字が在る。止める**")


def record_text(rec, secret=None):
    text = dumps(rec)
    check_clean(rec, text, secret)
    return text


def write_exclusive(path, data):
    with open(path, "xb") as fh:
        fh.write(data)


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


def run(root=ROOT, docs=None, taxonomy=None, out=None, want=DOCS_WANT, say=print):
    rec, secret = build_record(docs, taxonomy, want)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    say(u"-> %s(書類 %d)" % (os.path.basename(out), rec[u"材料"][u"書類の本数"]))
    return rec


def check(root=ROOT, docs=None, taxonomy=None, rec_path=None, want=DOCS_WANT, say=print):
    u"""置き場から数え直して記録と照らす。通信しない。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    now, secret = build_record(docs, taxonomy, want)
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
    a = ap.parse_args(argv)
    if a.check:
        check(root=a.root, docs=a.docs, taxonomy=a.taxonomy)
    else:
        run(root=a.root, docs=a.docs, taxonomy=a.taxonomy)


if __name__ == "__main__":
    main()
