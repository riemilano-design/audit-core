# -*- coding: utf-8 -*-
u"""封 docs/XBRL_NUMBER_READER_ENGINE_SEAL_2026-11-04.md §0-1・§5-3 ― 円族の数の形ごとの「全部読む / 一部読む / 読まない」の数え(いまの読みと N の読み)。**0 USD・通信なし・鍵は読まない・LLM は呼ばない。**

    cd audit-core
    python3 measure/xbrl_numfix_shapes_2026-11-04.py [--out fixtures/xbrl/numfix/shapes_2026-11-04.json] [--procs 4] [--only <docID>]

数え方は封 §0-1 のとおり: 文を NFKC で正規化し、候補の正規表現
``(?<![\\d.,])\\d[\\d,.]*(?:兆[\\d,.]*)?(?:億[\\d,.]*)?(?:万[\\d,.]*)?(?:千[\\d,.]*)?(?:百[\\d,.]*)?円`` で円族の数の候補を拾い、``extract.iter_numbers_2026_10_27`` の当たりが候補の範囲を
**全部覆う**(読む)/ **一部だけ重なる**(一部読み)/ **重ならない**(読まない)に分け、桁を N に畳み N の連続を 1 つにした形で数える。同じ材料を ``extract.iter_numbers_2026_11_04`` でも数え、読まない数が 0 になるか(残った形)を書く。
材料: AI の文 200 本(前の便の記録の 160 本 + F5 の 40 本。形 F1〜F5 ごと。文は ``。`` と改行で切る)・有報の原文 fresh 40(``edinet-fresh-2026-10-21``)・prior 94(``edinet-prior-2026-11-02``)・
手元の 97 書類(前例 ``xbrl_p27_regress97_2026-10-27.py`` の doc_lists: 67 + 30)の MD&A の文(``RUN.sentence_list(zb, V.PROFILES["P27"])``)。
「その他」直後の円の数も同じ分け方で(正規表現は下の ``OTHER_RE``)。記録は形と数だけ(文・span・会社名は持たない)。cache は読むだけで 1 file も足さない(件数と名前の一覧の sha256 を前後で記録し、変われば止める)。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない):
- 「その他」の正規表現は封の字の全角の記号(：（）　)と半角を両方入れた(文は NFKC 済みなので半角だけが当たる)。直後の円の数 = 当たりの終わりの位置(あれば符号 1 字を飛ばして)から
  **数の頭まで戻した位置**に候補の正規表現が始まるもの(正規表現の語の部分 ``{0,8}`` は桁を食って数の途中で終わることがあり、そのまま ``match`` すると数の頭が取れず円の数を落とす。封 §0-1 の 24 か所に合わせるための決め)。
- 有報の 3 群は zip ごとに 1 書類。MD&A が取れない zip(``sentence_list`` が例外)は数に入れず、``取れなかった書類`` に数だけ書く。
- 97 書類の docID は記録に書かない(書類の数だけ)。

engine(``core/``・``adapters/``)は 1 行も変えない。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name_file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


NF = load_module("xbrl_numfix_2026-11-04.py", "numfix_for_shapes")     # 200 本の読み込み(load_books)・RUN・GEN・Stop・key_leaks の扱い
GEN, RUN = NF.GEN, NF.RUN
Stop = GEN.Stop
P27R = load_module("xbrl_p27_regress97_2026-10-27.py", "p27_regress97_for_shapes")
from adapters.xbrl import extract as E     # noqa: E402
from adapters.xbrl import vocabulary as V  # noqa: E402

SEAL_REL = NF.SEAL_REL
SEAL_COMMIT = NF.SEAL_COMMIT
OUT_REL = NF.SHAPES_REL
CAND = re.compile(r"(?<![\d.,])\d[\d,.]*(?:兆[\d,.]*)?(?:億[\d,.]*)?(?:万[\d,.]*)?(?:千[\d,.]*)?(?:百[\d,.]*)?円")
OTHER_RE = re.compile(u"その他(の[^、。:：()（）\\s|]{0,8})?[:： 、はがをでに　]*(?=[-−△▲]?\\d)")
SIGNS = u"-−△▲"
READERS = collections.OrderedDict([("10_27", E.iter_numbers_2026_10_27), ("11_04", E.iter_numbers_2026_11_04)])
KINDS = ("full", "part", "none")
KIND_JA = collections.OrderedDict([("full", u"全部読む"), ("part", u"一部読む"), ("none", u"読まない")])
FRESH_DIR = os.path.join(GEN.CACHE_BASE, "edinet-fresh-2026-10-21")
PRIOR_DIR = os.path.join(GEN.CACHE_BASE, "edinet-prior-2026-11-02")
FORMS = ("F1", "F2", "F3", "F4", "F5")


def shape_of(token):
    return re.sub(r"N+", "N", re.sub(r"\d", "N", token))


def kind_of(a, b, spans):
    if any(x <= a and b <= y for x, y in spans):
        return "full"
    if any(x < b and a < y for x, y in spans):
        return "part"
    return "none"


def new_acc():
    return {"n": 0, "cand": 0, "kind": dict((r, collections.Counter()) for r in READERS), "shape": {},
            "other": {"pos": 0, "yen": 0, "kind": dict((r, collections.Counter()) for r in READERS), "shape": {}}}


def count_sentences(sents, acc):
    u"""文の列 → acc に足す。acc は new_acc()。"""
    for s in sents:
        s = unicodedata.normalize("NFKC", s)
        spans = dict((r, [(a, b) for (a, b, _v, _u, _p) in fn(s)]) for r, fn in READERS.items())
        for m in CAND.finditer(s):
            sh = shape_of(m.group(0))
            acc["cand"] += 1
            cell = acc["shape"].setdefault(sh, {"n": 0, "kind": dict((r, collections.Counter()) for r in READERS)})
            cell["n"] += 1
            for r in READERS:
                k = kind_of(m.start(), m.end(), spans[r])
                acc["kind"][r][k] += 1
                cell["kind"][r][k] += 1
        for om in OTHER_RE.finditer(s):
            acc["other"]["pos"] += 1
            pos = om.end()
            if pos < len(s) and s[pos] in SIGNS:
                pos += 1
            while pos > 0 and (s[pos - 1].isdigit() or s[pos - 1] in ",."):      # 正規表現の語の部分({0,8})は桁を食って数の途中で終わりうる。数の頭まで戻す
                pos -= 1
            cm = CAND.match(s, pos)
            if cm is None:
                continue
            acc["other"]["yen"] += 1
            sh = shape_of(cm.group(0))
            cell = acc["other"]["shape"].setdefault(sh, {"n": 0, "kind": dict((r, collections.Counter()) for r in READERS)})
            cell["n"] += 1
            for r in READERS:
                k = kind_of(cm.start(), cm.end(), spans[r])
                acc["other"]["kind"][r][k] += 1
                cell["kind"][r][k] += 1


def merge(into, other):
    into["n"] += other["n"]
    into["cand"] += other["cand"]
    for r in READERS:
        into["kind"][r].update(other["kind"][r])
        into["other"]["kind"][r].update(other["other"]["kind"][r])
    for key in ("pos", "yen"):
        into["other"][key] += other["other"][key]
    for where, src in ((into["shape"], other["shape"]), (into["other"]["shape"], other["other"]["shape"])):
        for sh, cell in src.items():
            c = where.setdefault(sh, {"n": 0, "kind": dict((r, collections.Counter()) for r in READERS)})
            c["n"] += cell["n"]
            for r in READERS:
                c["kind"][r].update(cell["kind"][r])


def kinds_json(c):
    return collections.OrderedDict((KIND_JA[k], c.get(k, 0)) for k in KINDS)


def shapes_json(shapes):
    out = collections.OrderedDict()
    for sh, cell in sorted(shapes.items(), key=lambda kv: (-kv[1]["n"], kv[0])):
        d = collections.OrderedDict([(u"候補", cell["n"])])
        for r in READERS:
            d[r] = kinds_json(cell["kind"][r])
        out[sh] = d
    return out


def left(shapes, reader, kind):
    u"""reader で kind が 1 つ以上ある形 → その数。"""
    return collections.OrderedDict(sorted(((sh, c["kind"][reader].get(kind, 0)) for sh, c in shapes.items() if c["kind"][reader].get(kind, 0)), key=lambda kv: (-kv[1], kv[0])))


def group_json(acc, unit):
    out = collections.OrderedDict([(unit, acc["n"]), (u"円族の候補", acc["cand"])])
    for r in READERS:
        out[u"読み %s" % r] = kinds_json(acc["kind"][r])
    out[u"11_04 でも読まない形"] = left(acc["shape"], "11_04", "none")
    out[u"11_04 でも一部読む形"] = left(acc["shape"], "11_04", "part")
    out[u"形"] = shapes_json(acc["shape"])
    o = acc["other"]
    ob = collections.OrderedDict([(u"「その他」の位置", o["pos"]), (u"直後が円の数", o["yen"])])
    for r in READERS:
        ob[u"読み %s" % r] = kinds_json(o["kind"][r])
    ob[u"11_04 でも読まない形"] = left(o["shape"], "11_04", "none")
    ob[u"形"] = shapes_json(o["shape"])
    out[u"「その他」の直後"] = ob
    return out


# ======================================================================================================
def doc_sentences(zpath):
    with io.open(zpath, "rb") as fh:
        zb = fh.read()
    try:
        return RUN.sentence_list(zb, V.PROFILES["P27"])
    except Exception:          # noqa: BLE001  MD&A が取れない zip は数に入れない(数だけ書く)
        return None


def doc_job(zpath):
    acc = new_acc()
    sents = doc_sentences(zpath)
    if sents is None:
        return None
    count_sentences(sents, acc)
    acc["n"] = 1
    return acc


def run_docs(zpaths, procs):
    u"""zip の列 → (acc, 取れなかった書類の数)。"""
    out = new_acc()
    bad = 0
    for acc in NF.map_pool(doc_job, zpaths, procs):
        if acc is None:
            bad += 1
        else:
            merge(out, acc)
    return out, bad


def zips_of(folder):
    return [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.endswith(".zip")]


def book_job(job):
    src, name, item, text_dir = job
    t = RUN.read_text(name, item, text_dir)
    acc = new_acc()
    count_sentences(re.split(r"(?<=[。\n])", t), acc)
    acc["n"] = 1
    return item[u"form"], acc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--procs", type=int, default=1)
    ap.add_argument("--only", default=None, help="この docID の本・書類だけ(本番の記録を作らない確認用には --out を替える)")
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise Stop(u"**出力が既に在る。測り直さない。止める**")
    caches = NF.caches_all()
    before = GEN.caches_snapshot(caches)
    books = NF.load_books(a.root, None)
    if a.only is not None:
        books = [b for b in books if b[2][u"docID"] == a.only]
    by_form = collections.OrderedDict((f, new_acc()) for f in FORMS)
    for form, acc in NF.map_pool(book_job, [(src, n, item, NF.SOURCES[src]["cache"]) for (src, n, item, _row, _p) in books], a.procs):
        merge(by_form[form], acc)
    ai_all = new_acc()
    for acc in by_form.values():
        merge(ai_all, acc)
    P = P27R
    ids67, sha67, ids30, sha30 = P.doc_lists()
    z97 = [P.zip_path(d, False) for d in ids67] + [P.zip_path(d, True) for d in ids30]
    fresh, prior = zips_of(FRESH_DIR), zips_of(PRIOR_DIR)
    if a.only is not None:
        z97 = [z for z in z97 if os.path.basename(z)[:-4] == a.only]
        fresh = [z for z in fresh if os.path.basename(z)[:-4] == a.only]
        prior = [z for z in prior if os.path.basename(z)[:-4] == a.only]
    groups = collections.OrderedDict()
    for f, acc in by_form.items():
        groups[u"AI の文 %s" % f] = group_json(acc, u"本")
    groups[u"AI の文 200 本"] = group_json(ai_all, u"本")
    for label, zs in ((u"有報 fresh 40", fresh), (u"有報 prior 94", prior), (u"有報 手元の 97 書類", z97)):
        acc, bad = run_docs(zs, a.procs)
        g = group_json(acc, u"書類")
        g[u"取れなかった書類"] = bad
        groups[label] = g
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"step"] = u"数の読み取り N ― 円族の数の形ごとの全部読む / 一部読む / 読まない(いまの読み 10_27 と N の読み 11_04。0 USD)"
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"HEAD の commit"] = GEN.git_head(os.path.dirname(a.root))
    rec[u"この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    rec[u"numfix script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_numfix_2026-11-04.py"))
    rec[u"engine の指紋"] = RUN.engine_fingerprint()
    rec[u"数え方"] = collections.OrderedDict([
        (u"候補の正規表現", CAND.pattern), (u"「その他」の正規表現", OTHER_RE.pattern),
        (u"読み", u"10_27 = extract.iter_numbers_2026_10_27(いまの読み)・11_04 = extract.iter_numbers_2026_11_04(N の読み)"),
        (u"分け方", u"当たりが候補の範囲を全部覆う = 全部読む・一部だけ重なる = 一部読む・重ならない = 読まない"),
        (u"形", u"桁を N に畳み N の連続を 1 つにした候補の字"),
        (u"文の切り方", u"AI の文 = 『。』と改行で切る(区切りは前の文に付ける)・有報 = RUN.sentence_list(P27)。どちらも NFKC")])
    rec[u"範囲"] = u"全材料" if a.only is None else u"**--only の docID の分だけ(本番の記録ではない)**"
    rec[u"cache の前後"] = collections.OrderedDict([(u"前", before), (u"後", after), (u"変化なし", before == after)])
    rec[u"群"] = groups
    rec[u"key_leaks"] = []
    text = json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    RUN.write_record(a.out, text, rec)
    g = groups[u"AI の文 200 本"]
    print(u"-> %s" % a.out)
    print(u"AI の文 200 本", g[u"円族の候補"], g[u"読み 10_27"], g[u"読み 11_04"])
    for label in (u"有報 fresh 40", u"有報 prior 94", u"有報 手元の 97 書類"):
        g = groups[label]
        print(label, g[u"書類"], g[u"円族の候補"], g[u"読み 10_27"], g[u"読み 11_04"], g[u"取れなかった書類"])


if __name__ == "__main__":
    main()
