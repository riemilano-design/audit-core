# -*- coding: utf-8 -*-
u"""封 docs/XBRL_NUMBER_READER_ENGINE_SEAL_2026-11-04.md §5-1・§5-4 ― 数の読み取り N の AI の文 200 本の判定・注入と、結果の表(tally)。**0 USD・通信なし・鍵は読まない・LLM は呼ばない。**

    python3 measure/xbrl_numfix_2026-11-04.py judge  [--procs N] [--only <docID>] [--out PATH]   # P28E・P29E・P29E-O の判定と旗が偽の byte 一致 → fixtures/xbrl/numfix/ai200_2026-11-04.json
    python3 measure/xbrl_numfix_2026-11-04.py inject [--procs N] [--only <docID>] [--out PATH]   # P28E・P29E の注入(T1_VALUE・T8_REL)→ fixtures/xbrl/numfix/inject_2026-11-04.json
    python3 measure/xbrl_numfix_2026-11-04.py tally  [--root DIR]                                 # 記録 4 つ(ai200・inject・regress97・shapes)から C-1〜C-13 と K-1〜K-5 の表を出す(file は書かない)

前の便の script(``xbrl_aiforms_{gen,run}_2026-11-03.py``・``xbrl_p27_tune_2026-10-27.py``)は **1 byte も変えず**、importlib で読み込んで使う(F5 の駆動 script ``xbrl_aiforms_f5_2026-11-03.py`` と同じ作り。
RUN.GEN に同じ GEN の instance を差し込む)。文は前の便の記録 ``fixtures/xbrl/aiforms/gen_2026-11-03.json``(160 本。置き場所 ``aiforms-2026-11-03/texts``)と ``f5_gen_2026-11-03.json``
(40 本。``aiforms-f5-2026-11-03/texts``)から **読むだけ**(cache に 1 file も足さない。札付けの束 dossiers も書かない)。件数と名前の一覧の sha256 を前後で記録し、変われば止める。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めは結果の報告に書いた):
- P29E-O = ``dataclasses.replace(V.P29E, name="P29E-O", other_subject_2026_11_02=False)``。engine には登録せず、この process の中だけ ``V.PROFILES["P29E-O"]`` に入れる(``verify_document`` は名前の字だけを受け ``V.PROFILES`` から引くため)。
- claim の対応は **id でなく位置**: 数の claim(raw の ``kind`` が num のもの)の鍵は ``(文の番号, 文の中の位置)``。P29E の数の claim で同じ鍵の P28E の claim が在れば「既存」、無ければ「新しい」。
  新しい行のうち、同じ文で P28E の claim の範囲(``recipes._numbers_of`` が返す [a, b))と交わるものは「置き換え」。
- 「既存の行で変わった行」= 既存の行のうち (state, reason, pointers) のどれかが P28E と P29E で違う行。「同じ文に新しい行が在る」= その文に P29E の新しい行が 1 つ以上在る。
- O の形の行 = 数の claim の raw の ``other_subject_2026_11_02`` が null でない行。決まった = その欄の 決まった が真。
- 「P29E 対 P29E−O で GROUNDED でなくなった行」= P29E−O で GROUNDED の行(鍵が同じ)のうち P29E で GROUNDED でない行(P29E に鍵が無い行を含む)。逆向き(O が GROUNDED にした行)も別に数える。
- 旗が偽の byte 一致(C-1)= ``RUN.judge_text`` を P27・P27E・P28・P28E のまま呼んで、``行``・``4 state``・``claim の数`` が前の便の記録の同じ name の欄と(JSON に通して)等しい本の数。
- 注入は ``RUN.PROFILES = ("P28E", "P29E")`` に替えてから。前の便の ``RUN.inject_text`` は土台の claim を **id** で profile 間に結ぶが、P29E は新しい数の claim で id が前にずれるので、
  土台の対応を ``(value, span, unit)`` で結び直す版をこの script に持つ(``base_status_n``・``inject_text_n``。手順の他の部分は ``RUN.inject_text`` と同じ。``IJ.select``・``TUNE.*``・``RUN.t8_candidates4``・``RUN.inject_summary`` を使う)。
  土台 = 無改変の文で **P29E が GROUNDED** の claim。ただし注入の仕掛け(``lib.numbers.scan``)は万・億のコンマの数(「1,234万円」「12億3,456万円」)を断片に切るため、
  新しく読めた数は土台に結べない(``find_base_claim`` が結べず「基準に対応が付かない」になる)。C-11・C-12・K-3 は新しく読めた数を測れず、測れるのは P28E・P29E の両方が読む数の site だけ。P28E の claim は同じ site に (value, span, unit) が同じ 1 件があれば結び、無ければその行の P28E の欄は『対応なし』。
  集計は 2 本: ``集計`` = 土台の全 site(C-11・C-12・K-3 は P29E のこちら)・``集計(比較用: P28E にも対応が付く site だけ)`` = P28E にも対応が付く site だけでの P28E と P29E。
- judge の本ごとの欄に、P28E・P29E それぞれの書類の丸め方の決定(``vocabulary.decide_rounding`` の返り値を ``capture_rounding`` の包みで写す)と、同じ文に新しい行が無いのに変わった既存の行の一覧を足した。

engine(``core/``・``adapters/``)は 1 行も変えない。
"""
from __future__ import print_function

import argparse
import collections
import dataclasses
import importlib.util
import io
import json
import multiprocessing
import os
import re
import sys
import tempfile

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


GEN = load_module("xbrl_aiforms_gen_2026-11-03.py", "aiforms_gen_for_numfix")
RUN = load_module("xbrl_aiforms_run_2026-11-03.py", "aiforms_run_for_numfix")
RUN.GEN = GEN                                                   # 同じ GEN の instance(別 instance に差し替えが届かない罠を避ける)
RUN.Stop = GEN.Stop
TUNE = RUN.TUNE
IJ = RUN.IJ
Stop = GEN.Stop

from adapters.xbrl import prose as PR                # noqa: E402
from adapters.xbrl import recipes as R               # noqa: E402
from adapters.xbrl import verify_document as VD      # noqa: E402
from adapters.xbrl import vocabulary as V            # noqa: E402

SEAL_REL = "docs/XBRL_NUMBER_READER_ENGINE_SEAL_2026-11-04.md"
SEAL_COMMIT = "48e7078"
DOC_REL = "docs/XBRL_NUMBER_READER_ENGINE_RESULT_2026-11-04.md"
REC_DIR_REL = "fixtures/xbrl/numfix"
AI200_REL = REC_DIR_REL + "/ai200_2026-11-04.json"
INJECT_REL = REC_DIR_REL + "/inject_2026-11-04.json"
REGRESS97_REL = REC_DIR_REL + "/regress97_2026-11-04.json"
SHAPES_REL = REC_DIR_REL + "/shapes_2026-11-04.json"
REC_REL = collections.OrderedDict([("ai200", AI200_REL), ("inject", INJECT_REL), ("regress97", REGRESS97_REL), ("shapes", SHAPES_REL)])
RUN_SCRIPT_REL = "measure/xbrl_aiforms_run_2026-11-03.py"
GEN_SCRIPT_REL = "measure/xbrl_aiforms_gen_2026-11-03.py"

#: 材料(前の便の記録 → 文の置き場所)。160 本 + 40 本 = 200 本
PREV_AI_DIR = GEN.REC_DIR_REL
SOURCES = collections.OrderedDict([
    ("aiforms", collections.OrderedDict([("gen", PREV_AI_DIR + "/gen_2026-11-03.json"), ("claims", PREV_AI_DIR + "/claims_2026-11-03.json"),
                                          ("cache", os.path.join(GEN.CACHE_BASE, "aiforms-2026-11-03"))])),
    ("f5", collections.OrderedDict([("gen", PREV_AI_DIR + "/f5_gen_2026-11-03.json"), ("claims", PREV_AI_DIR + "/f5_claims_2026-11-03.json"),
                                    ("cache", os.path.join(GEN.CACHE_BASE, "aiforms-f5-2026-11-03"))]))])
PREV_PROFILES = ("P27", "P27E", "P28", "P28E")
NOW_PROFILES = ("P28E", "P29E", "P29E-O")
STATES = RUN.STATES
INJECT_PROFILES = ("P28E", "P29E")
SAME_SENTENCE_NEW = u"同じ文に新しい行が在る"
SAME_SENTENCE_NONE = u"同じ文に新しい行が無い"
HIT, MISS = u"**当たり**", u"**外れ**"

#: P29E−O(measure の process の中だけ)。engine の source には登録しない。``V.PROFILES`` への登録は judge の実行の間だけ(``registered_p29e_no_o``。import しただけの process の
#: ``V.PROFILES`` を変えない = profile の一覧を数える他の試験を汚さない)
P29E_NO_O = dataclasses.replace(V.P29E, name="P29E-O", other_subject_2026_11_02=False)


class registered_p29e_no_o(object):
    u"""``with`` の間だけ ``V.PROFILES["P29E-O"]`` に入れる(入れ子でもよい。自分が入れたときだけ戻す)。fork した worker は入った状態を引き継ぐ。"""

    def __enter__(self):
        self.added = "P29E-O" not in V.PROFILES
        V.PROFILES["P29E-O"] = P29E_NO_O
        return self

    def __exit__(self, *a):
        if self.added:
            V.PROFILES.pop("P29E-O", None)
        return False


def key_leaks_n(text, key_value=None, long_alnum=True):
    u"""封の path は英数字・_・- が 32 字を超えて続く(前の便の ``key_leaks`` の「32 字以上の英数字の連なり」に当たる)。封の path そのものの字だけを検査の前に除く(F5 の駆動 script と同じ扱い)。"""
    return ORIG_KEY_LEAKS(text.replace(SEAL_REL, u""), key_value, long_alnum)


ORIG_KEY_LEAKS = GEN.key_leaks
GEN.key_leaks = key_leaks_n


def caches_all():
    u"""読むだけの folder(既存の cache 3 つ + 文の置き場所 2 つ)。件数と名前の一覧の sha256 を前後で記録する。"""
    c = collections.OrderedDict(GEN.EXISTING_CACHES)
    for k, v in SOURCES.items():
        c[os.path.basename(v["cache"])] = v["cache"]
    return c


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def jround(x):
    return json.loads(json.dumps(x))


# ======================================================================================================
# 材料
def load_books(root=ROOT, only=None):
    u"""200 本の (source, name, item, row, prior の本の欄)。前の便の claims の記録の ``本`` の並び(160 本 → 40 本)のまま。"""
    out = []
    for src, p in SOURCES.items():
        gen = GEN.jload(os.path.join(root, p["gen"]))
        claims = GEN.jload(os.path.join(root, p["claims"]))
        items = RUN.gen_items(gen)
        by_doc = dict((r["docID"], r) for r in RUN.company_rows(gen, root))
        for b in claims[u"本"]:
            if b.get(u"欠け"):
                continue
            n = b[u"name"]
            if n not in items:
                raise Stop(u"**前の便の claims の本が gen の記録の現行の ok に無い: %s。止める**" % n)
            if only is not None and b[u"docID"] != only:
                continue
            out.append((src, n, items[n], by_doc[b[u"docID"]], b))
    if only is not None and not out:
        raise Stop(u"**--only の docID が 200 本に無い。止める**")
    return out


# ======================================================================================================
# 並列(fork + queue。plain data だけ)
_POOL = {}


def map_pool(fn, jobs_, procs):
    _POOL["fn"] = fn
    if procs <= 1 or len(jobs_) <= 1:
        return [fn(j) for j in jobs_]
    ctx = multiprocessing.get_context("fork")
    todo, done = ctx.Queue(), ctx.Queue()
    for i in range(len(jobs_)):
        todo.put(i)
    n = min(procs, len(jobs_))
    for _ in range(n):
        todo.put(None)

    def loop():
        while True:
            i = todo.get()
            if i is None:
                return
            try:
                done.put((i, "ok", _POOL["fn"](jobs_[i])))
            except BaseException as exc:                     # noqa: BLE001  Stop を含む。文言に値は入っていない
                done.put((i, "err", str(exc) if isinstance(exc, SystemExit) else type(exc).__name__))

    ps = [ctx.Process(target=loop) for _ in range(n)]
    for p in ps:
        p.start()
    out = [None] * len(jobs_)
    try:
        for _ in range(len(jobs_)):
            i, st, val = done.get()
            if st == "err":
                raise Stop(u"%s" % (val or u"**worker が止まった。止める**"))
            out[i] = val
    finally:
        for p in ps:
            p.terminate()
    return out


# ======================================================================================================
# judge: 1 本
ROUNDING_NONE = collections.OrderedDict([(u"決定", None), (u"round-only", 0), (u"truncate-only", 0), (u"両方", 0)])


class capture_rounding(object):
    u"""``with`` の間だけ ``vocabulary.decide_rounding``(recipes が書類の丸め方を決めるのに呼ぶ engine の関数)を、返り値をそのまま返し、呼ばれた根拠の列の長さと返り値を記録する包みに替える。
    engine の関数の字は変えず、戻す。決定 = 返り値の mode・round-only = R・truncate-only = T・両方 = 根拠の数 − R − T(どちらでも説明できる根拠)。profile が doc_rounding を持たなければ呼ばれず、``ROUNDING_NONE``。"""

    def __enter__(self):
        self.calls = []
        self.orig = V.decide_rounding

        def spy(evidence):
            ev = list(evidence)
            out = self.orig(ev)
            self.calls.append((out, len(ev)))
            return out
        V.decide_rounding = spy
        return self

    def __exit__(self, *a):
        V.decide_rounding = self.orig
        return False

    def result(self):
        if not self.calls:
            return collections.OrderedDict(ROUNDING_NONE)
        (mode, r, t), n = self.calls[-1]
        return collections.OrderedDict([(u"決定", mode), (u"round-only", r), (u"truncate-only", t), (u"両方", n - r - t)])


def profile_view(zb, text, zm, pname):
    u"""1 profile の数の claim の鍵 → 欄。(行の辞書, 対応が付いたか, 文書の states, 書類の丸め方の決定)。"""
    prof = V.PROFILES[pname]
    out = VD.verify_document(zb, pname, text)
    with capture_rounding() as cap:
        nums, texts = R.build_raw_claims(zm, prof)
    raws = nums + texts
    cl = out["claims"]
    ok = len(cl) == len(raws) and all(c["id"] == r["id"] for c, r in zip(cl, raws))
    sents = RUN.sentence_list(zm, prof)
    ends = {}
    rows = collections.OrderedDict()
    for c, r in zip(cl, raws):
        if c["kind"] != "num":
            continue
        si, a = r["sentence"], r["pos"]
        if si not in ends:
            ends[si] = dict((a2, b2) for (a2, b2, _v, _u, _p) in R._numbers_of(prof, sents[si]))
        key = (si, a)
        if key in rows:
            ok = False
        rows[key] = {"b": ends[si][a], "state": c["state"], "reason": RUN.safe_reason(c["reason"]), "pointers": RUN.pointer_strings(c["pointers"]),
                     "o": RUN.other_subject_cell(r)}
    return rows, ok, out["document"]["states"], cap.result()


def overlaps(a, b, a2, b2):
    return a < b2 and a2 < b


def analyse_book(rows, oks, rounding=None):
    u"""3 profile の行(と P28E・P29E の書類の丸め方の決定 rounding)から、本の記録の欄(数だけ。文・span・値は持たない)。"""
    rounding = rounding or dict((p, collections.OrderedDict(ROUNDING_NONE)) for p in ("P28E", "P29E"))
    r28, r29, r29o = rows["P28E"], rows["P29E"], rows["P29E-O"]
    new = [k for k in r29 if k not in r28]
    existing = [k for k in r29 if k in r28]
    gone = [k for k in r28 if k not in r29]
    by_sent_28 = collections.defaultdict(list)
    for k, v in r28.items():
        by_sent_28[k[0]].append((k[1], v["b"]))
    replaced = [k for k in new if any(overlaps(k[1], r29[k]["b"], a2, b2) for a2, b2 in by_sent_28[k[0]])]
    by_sent_29_new = collections.defaultdict(list)
    for k in new:
        by_sent_29_new[k[0]].append((k[1], r29[k]["b"]))
    gone_unexplained = [k for k in gone if not any(overlaps(k[1], r28[k]["b"], a2, b2) for a2, b2 in by_sent_29_new[k[0]])]
    new_states = collections.Counter(r29[k]["state"] for k in new)
    changed = []
    for k in existing:
        a, b = r28[k], r29[k]
        if (a["state"], a["reason"], a["pointers"]) != (b["state"], b["reason"], b["pointers"]):
            changed.append([k[0], k[1], a["state"], b["state"], a["reason"] == b["reason"], a["pointers"] == b["pointers"], k[0] in by_sent_29_new])
    ch_new = sum(1 for c in changed if c[6])
    no_new = [[u"num", c[0], c[1], c[2], c[3], r28[(c[0], c[1])]["reason"], r29[(c[0], c[1])]["reason"]] for c in changed if not c[6]]
    o28 = [k for k, v in r28.items() if v["o"] is not None]
    o29 = [k for k, v in r29.items() if v["o"] is not None]
    d28 = [k for k in o28 if r28[k]["o"][2]]
    d29 = [k for k in o29 if r29[k]["o"][2]]
    lost = [k for k, v in r29o.items() if v["state"] == "GROUNDED" and (k not in r29 or r29[k]["state"] != "GROUNDED")]
    gained = [k for k, v in r29.items() if v["state"] == "GROUNDED" and (k not in r29o or r29o[k]["state"] != "GROUNDED")]
    return collections.OrderedDict([
        (u"対応", collections.OrderedDict((p, oks[p]) for p in NOW_PROFILES)),
        (u"数の claim の数", collections.OrderedDict((p, len(rows[p])) for p in NOW_PROFILES)),
        (u"新しい行の数", len(new)), (u"置き換えの行の数", len(replaced)),
        (u"P28E にあって P29E に無い行", len(gone)), (u"そのうち新しい行と範囲が交わらない行", len(gone_unexplained)),
        (u"新しい行の state", collections.OrderedDict((s, new_states.get(s, 0)) for s in STATES)),
        (u"既存の行", collections.OrderedDict([
            (u"行の数", len(existing)), (u"変わった行", len(changed)),
            (u"変わった行の内訳", collections.OrderedDict([(SAME_SENTENCE_NEW, ch_new), (SAME_SENTENCE_NONE, len(changed) - ch_new)])),
            (u"変わった行のうち state が変わった行", sum(1 for c in changed if c[2] != c[3])),
            (u"変わった行の中身", changed)])),
        (u"書類の丸め方", collections.OrderedDict((p, collections.OrderedDict(rounding[p])) for p in ("P28E", "P29E"))),
        (u"丸め方の決定が P28E と P29E で違う", rounding["P28E"][u"決定"] != rounding["P29E"][u"決定"]),
        (u"同じ文に新しい行が無いのに変わった既存の行", no_new),
        (u"O の形の行", collections.OrderedDict([("P28E", len(o28)), ("P29E", len(o29))])),
        (u"O が決めた行", collections.OrderedDict([("P28E", len(d28)), ("P29E", len(d29))])),
        (u"P29E 対 P29E-O", collections.OrderedDict([
            (u"数の claim の鍵が同じ", sorted(r29) == sorted(r29o)),
            (u"GROUNDED でなくなった行", len(lost)), (u"O が GROUNDED にした行", len(gained))]))])


def assemble_book(src, name, item, same, rows, oks, rounding=None):
    u"""1 本の記録の欄(``旗が偽の byte 一致`` の欄 same と 3 profile の行 rows・対応 oks から)。門が小さい標本の記録を作るのにも使う。"""
    same = collections.OrderedDict(same)
    same[u"一致"] = all(same.values())
    head = collections.OrderedDict([(u"name", name), (u"docID", item[u"docID"]), (u"form", item[u"form"]), (u"model", item[u"model"]), (u"writer", item[u"writer"]),
                                    (u"材料", src), (u"文の sha256", item[u"sha256"])])
    head[u"旗が偽の byte 一致"] = same
    head.update(analyse_book(rows, oks, rounding))
    return head


def judge_book(job):
    src, name, item, row, text_dir, zip_caches, prior = job
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    zm = PR.build_modified_zip(zb, text)[0]
    rows, oks, states, rounding = {}, {}, {}, {}
    with registered_p29e_no_o():
        for p in NOW_PROFILES:
            rows[p], oks[p], states[p], rounding[p] = profile_view(zb, text, zm, p)
    old = RUN.judge_text(zb, text)[0]                       # 旗が偽の profile(前の便の 4 つ)のまま
    same = collections.OrderedDict([
        (u"行", jround(old[u"行"]) == prior[u"行"]), (u"4 state", jround(old[u"4 state"]) == prior[u"4 state"]),
        (u"claim の数", jround(old[u"claim の数"]) == prior[u"claim の数"])])
    return assemble_book(src, name, item, same, rows, oks, rounding)


# ---- 集計(門が記録の ``本`` から作り直して照らす)
def sum_books(books, fn):
    return sum(fn(b) for b in books)


def aggregate(books):
    u"""``本`` の列 → 集計。全体と形別・model 別。"""
    def block(bs):
        n28 = sum_books(bs, lambda b: b[u"数の claim の数"]["P28E"])
        n29 = sum_books(bs, lambda b: b[u"数の claim の数"]["P29E"])
        n29o = sum_books(bs, lambda b: b[u"数の claim の数"]["P29E-O"])
        newn = sum_books(bs, lambda b: b[u"新しい行の数"])
        ns = collections.OrderedDict((s, sum_books(bs, lambda b: b[u"新しい行の state"][s])) for s in STATES)
        ex = collections.OrderedDict([
            (u"既存の行", sum_books(bs, lambda b: b[u"既存の行"][u"行の数"])), (u"変わった行", sum_books(bs, lambda b: b[u"既存の行"][u"変わった行"])),
            (SAME_SENTENCE_NEW, sum_books(bs, lambda b: b[u"既存の行"][u"変わった行の内訳"][SAME_SENTENCE_NEW])),
            (SAME_SENTENCE_NONE, sum_books(bs, lambda b: b[u"既存の行"][u"変わった行の内訳"][SAME_SENTENCE_NONE])),
            (u"うち state が変わった行", sum_books(bs, lambda b: b[u"既存の行"][u"変わった行のうち state が変わった行"]))])
        return collections.OrderedDict([
            (u"本", len(bs)),
            (u"C-1 旗が偽の byte 一致", collections.OrderedDict([(u"一致した本", sum(1 for b in bs if b[u"旗が偽の byte 一致"][u"一致"])), (u"本", len(bs))])),
            (u"C-5 数の claim", collections.OrderedDict([("P28E", n28), ("P29E", n29), ("P29E-O", n29o), (u"P29E − P28E", n29 - n28)])),
            (u"新しい行", collections.OrderedDict([(u"行の数", newn), (u"置き換えの行", sum_books(bs, lambda b: b[u"置き換えの行の数"])),
                                                  (u"P28E にあって P29E に無い行", sum_books(bs, lambda b: b[u"P28E にあって P29E に無い行"])),
                                                  (u"そのうち新しい行と範囲が交わらない行", sum_books(bs, lambda b: b[u"そのうち新しい行と範囲が交わらない行"]))])),
            (u"C-6 新しい行の state", collections.OrderedDict([(u"state", ns), (u"GROUNDED の率", pct(ns["GROUNDED"], newn)), (u"分母", newn)])),
            (u"C-7 既存の行", ex),
            (u"K-2 の外れの説明", collections.OrderedDict([
                (u"同じ文に新しい行が無いのに変わった既存の行", sum_books(bs, lambda b: len(b[u"同じ文に新しい行が無いのに変わった既存の行"]))),
                (u"うち丸め方の決定が P28E と P29E で違う本に在る行", sum_books(bs, lambda b: len(b[u"同じ文に新しい行が無いのに変わった既存の行"]) if b[u"丸め方の決定が P28E と P29E で違う"] else 0)),
                (u"丸め方の決定が P28E と P29E で違う本", sum(1 for b in bs if b[u"丸め方の決定が P28E と P29E で違う"])),
                (u"同じ文に新しい行が無いのに変わった既存の行がある本", sum(1 for b in bs if b[u"同じ文に新しい行が無いのに変わった既存の行"]))])),
            (u"C-8 O の形の行", collections.OrderedDict([("P28E", sum_books(bs, lambda b: b[u"O の形の行"]["P28E"])), ("P29E", sum_books(bs, lambda b: b[u"O の形の行"]["P29E"]))])),
            (u"C-9 O が決めた行", collections.OrderedDict([("P28E", sum_books(bs, lambda b: b[u"O が決めた行"]["P28E"])), ("P29E", sum_books(bs, lambda b: b[u"O が決めた行"]["P29E"]))])),
            (u"C-10 P29E 対 P29E-O", collections.OrderedDict([
                (u"GROUNDED でなくなった行", sum_books(bs, lambda b: b[u"P29E 対 P29E-O"][u"GROUNDED でなくなった行"])),
                (u"O が GROUNDED にした行", sum_books(bs, lambda b: b[u"P29E 対 P29E-O"][u"O が GROUNDED にした行"])),
                (u"数の claim の鍵が違う本", sum(1 for b in bs if not b[u"P29E 対 P29E-O"][u"数の claim の鍵が同じ"]))])),
            (u"対応が付かなかった本", sum(1 for b in bs if not all(b[u"対応"].values())))])

    out = collections.OrderedDict([(u"全体", block(books))])
    out[u"形別"] = collections.OrderedDict((f, block([b for b in books if b[u"form"] == f])) for f in sorted(set(b[u"form"] for b in books)))
    out[u"model 別"] = collections.OrderedDict((m, block([b for b in books if b[u"model"] == m])) for m in sorted(set(b[u"model"] for b in books)))
    return out


def run_judge(root=ROOT, procs=1, only=None, out=None, key_value=None, say=print):
    out = out or os.path.join(root, AI200_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    if tuple(RUN.PROFILES) != PREV_PROFILES:
        raise Stop(u"**RUN.PROFILES が前の便の 4 つでない(旗が偽の byte 一致を測れない)。止める**")
    seed, seed_meta = GEN.seed_value(root)
    books = load_books(root, only)
    caches = caches_all()
    before = GEN.caches_snapshot(caches)
    jobs_ = [(src, n, item, row, SOURCES[src]["cache"], GEN.EXISTING_CACHES, prior) for (src, n, item, row, prior) in books]
    say(u"判定 %d 本 × 3 profile(P28E・P29E・P29E-O)+ 旗が偽の byte 一致 ― procs %d" % (len(jobs_), procs))
    with registered_p29e_no_o():
        recs = map_pool(judge_book, jobs_, procs)
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = header(root, u"数の読み取り N ― AI の文 200 本の判定(P28E・P29E・P29E-O。0 USD)", seed_meta, before, after, NOW_PROFILES)
    rec[u"欄"] = collections.OrderedDict([
        (u"P29E-O", u"P29E−O は measure の process の中だけの登録(dataclasses.replace(V.P29E, name=\"P29E-O\", other_subject_2026_11_02=False)。engine の source には登録しない)"),
        (u"数の claim の鍵", u"(文の番号, 文の中の位置)。id は profile 間で替わるので使わない"),
        (u"新しい行", u"P29E の数の claim のうち同じ鍵の P28E の数の claim が無い行"),
        (u"置き換えの行", u"新しい行のうち、同じ文で P28E の数の claim の範囲と交わる行"),
        (u"変わった行の中身", u"[文の番号, 位置, 前の state, 後の state, reason が同じ, pointers が同じ, その文に新しい行が在る]"),
        (u"書類の丸め方", u"P28E・P29E それぞれ build_raw_claims の中で engine の vocabulary.decide_rounding が返した決定(mode)と根拠の数(round-only = R・truncate-only = T・両方 = 根拠の数 − R − T)。包みで返り値を写しただけ(engine の字は変えない)"),
        (u"同じ文に新しい行が無いのに変わった既存の行", u"[種類, 文の番号, 位置, 前の state, 後の state, 前の reason, 後の reason]。文・span・値は持たない"),
        (u"旗が偽の byte 一致", u"RUN.judge_text(P27・P27E・P28・P28E) の 行・4 state・claim の数 が前の便の記録の同じ name の欄と等しい(JSON に通して比べた)")])
    rec[u"入力の記録の sha256"] = collections.OrderedDict(
        (u"%s_%s" % (src, k), GEN.sha256_file(os.path.join(root, p[k]))) for src, p in SOURCES.items() for k in ("gen", "claims"))
    rec[u"本"] = recs
    rec[u"集計"] = aggregate(recs)
    rec[u"repo の外に置いたもの"] = u"なし(この便は何も書かない。文は前の便の folder から読むだけ)"
    write_json(out, rec, key_value)
    say(u"-> %s(本 %d)" % (out, len(recs)))
    return rec


def header(root, step, seed_meta, before, after, profiles):
    h = RUN.header(root, step, os.path.join(root, SOURCES["aiforms"]["gen"]), seed_meta, before, after)
    h[u"seal"] = SEAL_REL
    h[u"封の commit"] = SEAL_COMMIT
    h[u"この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    h[u"前の便の run script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_aiforms_run_2026-11-03.py"))
    h[u"生成の記録の sha256"] = collections.OrderedDict((src, GEN.sha256_file(os.path.join(root, p["gen"]))) for src, p in SOURCES.items())
    h[u"profile"] = list(profiles)
    return h


def write_json(out, rec, key_value=None, text=None):
    text = text if text is not None else json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    RUN.write_record(out, text, rec, key_value)


# ======================================================================================================
# inject
COMPARE_KEY = u"集計(比較用: P28E にも対応が付く site だけ)"
BASE_WORD = u"無改変の文で P29E が GROUNDED の claim"
#: 記録の 限界 の 1 つ(事実の字。門が同じ字を留める)
LIMIT_SCAN = u"注入の仕掛け(N.scan)は万・億のコンマの数を断片に切るため、C-11・C-12・K-3 は新しく読めた数を測れない。測れるのは P28E・P29E の両方が読む数の site だけ"
LINKED, UNLINKED = u"P29E が GROUNDED(P28E の claim と対応が付く)", u"P29E が GROUNDED(P28E の claim に対応なし)"


def base_status_n(base_claims, base_by_id, tok, text):
    u"""(状態, 土台)。土台 = 無改変の文で **P29E が GROUNDED** の claim(封 §3 C-11「P29E の claim から site を選ぶ」)。P29E の claim を ``find_base_claim`` で 1 件に決め、
    P28E の claim は (value, span, unit) が同じ 1 件があれば結び(id は profile 間で替わる)、無ければ ``ids`` の P28E を None にする(その行の P28E の欄は『対応なし』)。
    返す土台は P29E の claim に ``ids``(profile → id か None)を足した写し。"""
    p0, p1 = INJECT_PROFILES
    digits = text[tok.start:tok.end]
    bc = TUNE.find_base_claim(base_claims[p1], tok.value, digits, tok.unit)
    if bc is None:
        return u"基準に対応が付かない", None
    if bc["state"] != "GROUNDED":
        return u"P29E が GROUNDED でない", None
    key = (bc["value"], bc["span"], bc["unit"])
    twin = [c for c in base_claims[p0] if (c["value"], c["span"], c["unit"]) == key]
    out = dict(bc)
    out["ids"] = {p0: twin[0]["id"] if len(twin) == 1 else None, p1: bc["id"]}
    return (LINKED if len(twin) == 1 else UNLINKED), out


def inject_text_n(zb, text, refs, seed, key, cap=RUN.INJECT_CAP, verify=None):
    u"""``RUN.inject_text`` と同じ手順(1 回に 1 件・round-trip を確かめる)。土台は P29E が GROUNDED の claim。行の判定の引きは profile ごとの id で、P28E の claim が無い行の P28E の欄は『対応なし』(判定しない)。"""
    if RUN.N.normalize_digits(text) != text:
        return [], {u"注入しない": u"文に全角の数字がある(select は半角の文を前提にする)"}
    verify = verify or VD.verify_document
    profiles = tuple(RUN.PROFILES)
    base_claims = dict((p, verify(zb, p, text)["claims"]) for p in profiles)
    base_by_id = dict((p, dict((c["id"], c) for c in base_claims[p])) for p in profiles)
    toks = dict(((t.start, t.end), t) for t in RUN.N.scan(text))
    counts, work_list = {}, []
    chosen, cat, _a, _w = IJ.select(text, refs, "xbrl", seed, key, cap, types=["T1_VALUE"])
    c1 = collections.Counter()
    c1[u"作れる site"], c1[u"採った"] = cat["T1_VALUE"], len(chosen)
    for inj in chosen:
        tok = toks[tuple(inj["span"])]
        status, bc = RUN.base_status4(base_claims, base_by_id, tok, text)
        c1[status] += 1
        work_list.append((inj, tok, bc))
    counts["T1_VALUE"] = dict(c1)
    t8, c8 = RUN.t8_candidates4(text, refs, base_claims, base_by_id, seed, key, cap)
    counts["T8_REL"] = dict(c8)
    work_list += t8
    rows = []
    for inj, tok, bc in work_list:
        tampered, placements = IJ.apply_edits(text, [inj])
        if IJ.revert(tampered, [inj], placements, text) != text:
            raise Stop(u"**round-trip が合わない: %s。止める**" % inj["id"])
        if bc is None:
            continue
        row = collections.OrderedDict([("id", inj["id"]), (u"型", inj["type"]), (u"基準の claim", bc["id"]), (u"P28E の土台に対応", bc["ids"][profiles[0]] is not None)])
        if inj["type"] == "T8_REL":
            row["r"], row[u"r を決めた回"] = inj["detail"]["relative"], inj["detail"]["tries"]
        for p in profiles:
            if bc["ids"][p] is None:
                row[p] = TUNE.classify(None, None)                       # 土台に対応する claim が無い = 対応なし
                continue
            res = TUNE.claim_for_p27(verify(zb, p, tampered)["claims"], inj, tok.unit)
            row[p] = TUNE.classify(res, base_by_id[p][bc["ids"][p]])
        rows.append(row)
    return rows, counts


def inject_summaries(rows):
    u"""(集計 = 土台の全 site, 比較用 = P28E の claim にも対応が付く site だけ)。RUN.PROFILES が (P28E, P29E) のときに呼ぶ。"""
    return RUN.inject_summary(rows), RUN.inject_summary([r for r in rows if r[u"P28E の土台に対応"]])


def unlinked_counts(rows):
    u"""P28E の claim に結べず P28E の欄が対応なしの行の数(全体と型別)。"""
    out = collections.OrderedDict([(u"全体", sum(1 for r in rows if not r[u"P28E の土台に対応"]))])
    for t in RUN.INJECT_TYPES:
        out[t] = sum(1 for r in rows if r[u"型"] == t and not r[u"P28E の土台に対応"])
    return out


def inject_job_n(args):
    src, name, item, row, text_dir, zip_caches, seed, work_root = args
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    refs = RUN.refs_for(row, zip_caches, work_root)
    rows, counts = inject_text_n(zb, text, refs, seed, name)
    base = {u"docID": item[u"docID"], u"form": item[u"form"], u"model": item[u"model"], u"writer": item[u"writer"]}
    return name, [collections.OrderedDict(list(base.items()) + list(r.items())) for r in rows], counts


def install_inject():
    u"""注入の入れ替え(inject の command のときだけ)。RUN.PROFILES と土台の判定を差し替える(使う側の ``RUN.t8_candidates4`` が引く名前 ``base_status4`` に届く)。"""
    RUN.PROFILES = INJECT_PROFILES
    RUN.base_status4 = base_status_n


def inject_wiring_problems():
    out = []
    if tuple(RUN.PROFILES) != INJECT_PROFILES:
        out.append(u"RUN.PROFILES が (P28E, P29E) でない")
    if RUN.base_status4 is not base_status_n:
        out.append(u"RUN.base_status4 が差し替えた先でない")
    if RUN.GEN is not GEN:
        out.append(u"RUN.GEN が同じ instance でない")
    return out


def run_inject(root=ROOT, procs=1, only=None, out=None, key_value=None, say=print, work_root=None):
    out = out or os.path.join(root, INJECT_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    install_inject()
    bad = inject_wiring_problems()
    if bad:
        raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    seed, seed_meta = GEN.seed_value(root)
    books = load_books(root, only)
    caches = caches_all()
    before = GEN.caches_snapshot(caches)
    work_root = work_root or tempfile.mkdtemp(prefix="numfix_inject_", dir=os.environ.get("TMPDIR"))
    jobs_ = [(src, n, item, row, SOURCES[src]["cache"], GEN.EXISTING_CACHES, seed, work_root) for (src, n, item, row, _prior) in books]
    say(u"注入 %d 本 × 2 profile(P28E・P29E)― procs %d(1 件ごとに判定。時間がかかる)" % (len(jobs_), procs))
    results = map_pool(inject_job_n, jobs_, procs)
    rows, per = [], collections.OrderedDict()
    for n, r, c in results:
        rows += r
        per[n] = c
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = header(root, u"数の読み取り N ― 注入(P28E・P29E の T1_VALUE・T8_REL。0 USD)", seed_meta, before, after, INJECT_PROFILES)
    rec[u"種"] = {u"file": RUN.SEED_REL_STR, u"種の確認": seed_meta}
    rec[u"型"] = collections.OrderedDict([
        ("T1_VALUE", u"inject.select(types=[T1_VALUE]) のまま。cap は採用に掛ける(基準で絞る前)"),
        ("T8_REL", u"円の単位族の token・r ∈ %s・%d 回まで。cap は site に掛ける" % (list(TUNE.T8_R_VALUES), TUNE.T8_TRIES)),
        (u"上限", u"型ごと・1 本あたり %d" % RUN.INJECT_CAP),
        (u"土台", BASE_WORD),
        (u"土台の結び方", u"P29E の claim を find_base_claim で 1 件に決め、P28E の claim は (value, span, unit) が同じ 1 件があれば結ぶ(id は profile 間で替わる)。無ければその行の P28E の欄は対応なし(判定しない)"),
        (u"集計の2本", u"集計 = 土台の全 site での P28E・P29E の率(C-11・C-12・K-3 は P29E のこちら)。" + COMPARE_KEY + u" = そのうち P28E の claim にも対応が付く site だけでの P28E と P29E の率(比較用)"),
        (u"inject.select の docID の引数", u"本の名前(<docID>_<形>_<model>)")])
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"], rec[COMPARE_KEY] = inject_summaries(rows)
    rec[u"P28E に対応なしの行の数"] = unlinked_counts(rows)
    rec[u"行"] = rows
    rec[u"限界"] = [u"注入は 2 型だけ(値・相対のずれ)。期・単位・主語の取り違えは注入しない", u"T8_REL の r の 4 値は前例の決め打ち",
                  LIMIT_SCAN, u"土台は P29E が GROUNDED の claim。P28E の claim に結べない site の行は P28E の欄が対応なし(P28E との比較は " + COMPARE_KEY + u" の site だけ)"]
    write_json(out, rec, key_value, text=RUN.dumps_inject(rec))
    say(u"-> %s(注入の行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
# tally: 封の表(§3 の C-1〜C-13・§4 の K-1〜K-5)を読み、記録 4 つから判定する
def read_seal(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def seal_pred_rows(seal):
    u"""封 §3 の表の行 {C-n: (欄, 予測, 外れ方)}。"""
    sec = seal[seal.index("## §3"):seal.index("## §4")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| (C-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            out[m.group(1)] = (cells[0], cells[1], cells[2] if len(cells) > 2 else u"")
    return out


def num(s):
    return float(s.replace(",", "").replace("+", ""))


def pair_of(text):
    u"""``a〜b`` の字 → (a, b)。最初の 1 組。"""
    m = re.search(r"([+\-]?[\d,]+(?:\.\d+)?)〜([+\-]?[\d,]+(?:\.\d+)?)", text)
    return (num(m.group(1)), num(m.group(2)))


def seal_bounds(seal):
    u"""封の字から予測の幅を読む(字のコピーにしない)。{名前: 値}。"""
    P = seal_pred_rows(seal)
    b = collections.OrderedDict()
    m = re.match(r"(\d+) / (\d+)$", P["C-1"][1])
    b["C-1"] = (int(m.group(1)), int(m.group(2)))
    m = re.match(r"(\d+) / (\d+) × (\d+)$", P["C-2"][1])
    b["C-2"] = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    b["C-3"] = int(re.match(r"(\d+)$", P["C-3"][1]).group(1))
    b["C-4"] = pair_of(P["C-4"][1])
    b["C-5"] = pair_of(P["C-5"][1])
    b["C-6"] = pair_of(P["C-6"][1])
    b["C-7"] = pair_of(P["C-7"][1])
    b["C-8"] = pair_of(P["C-8"][1])
    b["C-9"] = pair_of(P["C-9"][1])
    b["C-10"] = int(re.match(r"(\d+)$", P["C-10"][1]).group(1))
    t1 = re.search(r"T1_VALUE (\d+(?:\.\d+)?)〜(\d+(?:\.\d+)?)%", P["C-11"][1])
    t8 = re.search(r"T8_REL (\d+(?:\.\d+)?)〜(\d+(?:\.\d+)?)%", P["C-11"][1])
    b["C-11"] = collections.OrderedDict([("T1_VALUE", (float(t1.group(1)), float(t1.group(2)))), ("T8_REL", (float(t8.group(1)), float(t8.group(2))))])
    b["C-12"] = pair_of(P["C-12"][1])
    b["C-13"] = pair_of(P["C-13"][1])
    sec4 = seal[seal.index("## §4"):seal.index("## §5")]
    b["K-4"] = float(re.search(r"\*\*K-4\*\*[^\n]*?≥ (\d+(?:\.\d+)?)%", sec4).group(1))
    b["K-5"] = int(re.search(r"\*\*K-5[^*]*\*\*[^\n]*?C-9 の O が決めた行 ≥ (\d+)", sec4).group(1))
    return b


def within(x, lo_hi):
    return x is not None and lo_hi[0] <= x <= lo_hi[1]


def inj_rate(rec, t, p, key, summary=u"集計"):
    return rec[summary][t][p][u"全体"][key][u"率"]


def build_J(R_, seal):
    u"""{C-n: {判定, 値}, K-n: ..., 採用}。R_ = {"ai200", "inject", "regress97", "shapes"}(記録の JSON)。"""
    B = seal_bounds(seal)
    P = seal_pred_rows(seal)
    A = R_["ai200"][u"集計"][u"全体"]
    r97 = R_["regress97"]
    inj = R_["inject"]
    J = collections.OrderedDict()

    def put(k, ok, val):
        J[k] = {u"判定": HIT if ok else MISS, u"値": val}
    c1 = A[u"C-1 旗が偽の byte 一致"]
    put("C-1", (c1[u"一致した本"], c1[u"本"]) == B["C-1"], collections.OrderedDict([(u"一致した本", c1[u"一致した本"]), (u"本", c1[u"本"])]))
    c2 = r97[u"集計"][u"C-2 旗が偽の profile の byte 一致"]
    c2n = collections.OrderedDict((p, v[u"byte が同じ書類"]) for p, v in c2.items())
    c2d = set(v[u"書類"] for v in c2.values())
    ok2 = len(c2) == B["C-2"][2] and c2d == {B["C-2"][1]} and all(n == B["C-2"][0] for n in c2n.values())
    put("C-2", ok2, collections.OrderedDict([(u"byte が同じ書類(profile 間の最小)", min(c2n.values())), (u"書類", B["C-2"][1]), (u"profile", len(c2))]))
    c3 = r97[u"集計"][u"C-3 動いた既存の行"]
    put("C-3", c3["P29 対 P28"] == B["C-3"] and c3["P29E 対 P28E"] == B["C-3"], collections.OrderedDict(c3))
    c4 = r97[u"集計"][u"C-4 増えた claim"]
    put("C-4", within(c4["P29E"], B["C-4"]), collections.OrderedDict(c4))
    c5 = A[u"C-5 数の claim"]
    put("C-5", within(c5[u"P29E − P28E"], B["C-5"]), collections.OrderedDict([("P28E", c5["P28E"]), ("P29E", c5["P29E"]), (u"差", c5[u"P29E − P28E"])]))
    c6 = A[u"C-6 新しい行の state"]
    put("C-6", within(c6[u"GROUNDED の率"], B["C-6"]), collections.OrderedDict([(u"新しい行", c6[u"分母"]), (u"GROUNDED の率", c6[u"GROUNDED の率"])]))
    c7 = A[u"C-7 既存の行"]
    put("C-7", within(c7[u"変わった行"], B["C-7"]) and c7[SAME_SENTENCE_NONE] == 0,
        collections.OrderedDict([(u"変わった行", c7[u"変わった行"]), (SAME_SENTENCE_NEW, c7[SAME_SENTENCE_NEW]), (SAME_SENTENCE_NONE, c7[SAME_SENTENCE_NONE])]))
    c8 = A[u"C-8 O の形の行"]
    put("C-8", within(c8["P29E"], B["C-8"]), collections.OrderedDict([("P28E", c8["P28E"]), ("P29E", c8["P29E"])]))
    c9 = A[u"C-9 O が決めた行"]
    put("C-9", within(c9["P29E"], B["C-9"]), collections.OrderedDict([("P28E", c9["P28E"]), ("P29E", c9["P29E"])]))
    c10 = A[u"C-10 P29E 対 P29E-O"]
    put("C-10", c10[u"GROUNDED でなくなった行"] == B["C-10"], collections.OrderedDict([(u"GROUNDED でなくなった行", c10[u"GROUNDED でなくなった行"]), (u"O が GROUNDED にした行", c10[u"O が GROUNDED にした行"])]))
    t1, t8 = inj_rate(inj, "T1_VALUE", "P29E", u"通した"), inj_rate(inj, "T8_REL", "P29E", u"通した")
    put("C-11", within(t1, B["C-11"]["T1_VALUE"]) and within(t8, B["C-11"]["T8_REL"]),
        collections.OrderedDict([(u"T1_VALUE 通した率 P29E", t1), (u"T8_REL 通した率 P29E", t8),
                                 (u"T1_VALUE 通した率 P28E(比較用)", inj_rate(inj, "T1_VALUE", "P28E", u"通した", COMPARE_KEY)),
                                 (u"T8_REL 通した率 P28E(比較用)", inj_rate(inj, "T8_REL", "P28E", u"通した", COMPARE_KEY))]))
    o29 = inj_rate(inj, "T8_REL", "P29E", u"名指して原本の値を返した")
    put("C-12", within(o29, B["C-12"]), collections.OrderedDict([(u"T8_REL 名指して原本 P29E", o29), (u"P28E(比較用)", inj_rate(inj, "T8_REL", "P28E", u"名指して原本の値を返した", COMPARE_KEY))]))
    c13 = r97[u"集計"][u"C-13 engine の留めの連動で直す試験 file"]
    put("C-13", within(c13[u"直した file(M)"], B["C-13"]),
        collections.OrderedDict([(u"直した file(M)", c13[u"直した file(M)"]), (u"新しい file(A)", c13[u"新しい file(A)"]), (u"engine の挿入の行数", c13[u"engine の挿入の行数"])]))
    # 採用の基準
    K = collections.OrderedDict()
    K["K-1"] = {u"判定": HIT if J["C-1"][u"判定"] == HIT and J["C-2"][u"判定"] == HIT else MISS,
                u"値": collections.OrderedDict([("C-1", J["C-1"][u"判定"]), ("C-2", J["C-2"][u"判定"])])}
    K["K-2"] = {u"判定": HIT if c7[SAME_SENTENCE_NONE] == 0 else MISS, u"値": collections.OrderedDict([(u"新しく読めた数が同じ文に無い行で変わった行", c7[SAME_SENTENCE_NONE])])}
    k3 = t1 is not None and t8 is not None and t1 <= B["C-11"]["T1_VALUE"][1] and t8 <= B["C-11"]["T8_REL"][1]
    K["K-3"] = {u"判定": HIT if k3 else MISS, u"値": collections.OrderedDict([(u"T1_VALUE", t1), (u"T8_REL", t8)])}
    g = c6[u"GROUNDED の率"]
    K["K-4"] = {u"判定": HIT if g is not None and g >= B["K-4"] else MISS, u"値": collections.OrderedDict([(u"新しい行の GROUNDED の率", g)])}
    d9 = c9["P29E"]
    K["K-5"] = {u"判定": u"記録", u"値": collections.OrderedDict([(u"O が決めた行(P29E)", d9), (u"読み", u"O は N のあとで効く" if d9 >= B["K-5"] else u"O は 2 便続けて効かない")])}
    adopt = all(K[k][u"判定"] == HIT for k in ("K-1", "K-2", "K-3", "K-4"))
    return collections.OrderedDict([(u"C", J), (u"K", K), (u"採用", adopt), (u"欄", collections.OrderedDict((k, v[0]) for k, v in P.items()))])


def fmt(v):
    if isinstance(v, bool):
        return u"はい" if v else u"いいえ"
    if isinstance(v, float):
        return (u"%.1f" % v)
    if isinstance(v, int):
        return format(v, ",")
    if isinstance(v, dict):
        return u"・".join(u"%s %s" % (k, fmt(x)) for k, x in v.items())
    return u"%s" % (v,)


def pred_cell(text):
    u"""封の予測の字の、括弧の前まで(表を短くする。決め方は固定)。"""
    return re.split(r"[(（]", text)[0].strip()


def render_pred(J, seal=None):
    seal = seal if seal is not None else read_seal()
    P = seal_pred_rows(seal)
    lines = [u"| # | 欄 | 予測 | 測った値 | 判定 |", u"|---|---|---|---|---|"]
    for k, v in J[u"C"].items():
        lines.append(u"| %s | %s | %s | %s | %s |" % (k, P[k][0], pred_cell(P[k][1]), fmt(v[u"値"]), v[u"判定"]))
    return u"\n".join(lines)


def render_judge(J, seal=None):
    seal = seal if seal is not None else read_seal()
    sec4 = seal[seal.index("## §4"):seal.index("## §5")]
    names = collections.OrderedDict()
    for m in re.finditer(r"^- \*\*(K-\d)[^*]*\*\*:?\s*(.*)$", sec4, re.M):
        names[m.group(1)] = m.group(2)
    lines = [u"| # | 基準 | 測った値 | 判定 |", u"|---|---|---|---|"]
    for k, v in J[u"K"].items():
        lines.append(u"| %s | %s | %s | %s |" % (k, pred_cell(names[k]), fmt(v[u"値"]), v[u"判定"] if v[u"判定"] in (HIT, MISS) else u"**%s**" % v[u"判定"]))
    lines.append(u"")
    lines.append(u"採用の判定(K-1〜K-4 を全部満たす): **%s**。最後に決めるのは人間。" % (u"採用" if J[u"採用"] else u"採用しない(人間に返す)"))
    return u"\n".join(lines)


def load_records(root=ROOT):
    return collections.OrderedDict((k, GEN.jload(os.path.join(root, v))) for k, v in REC_REL.items())


def run_tally(root=ROOT, say=print):
    seal = read_seal(root)
    J = build_J(load_records(root), seal)
    say(render_pred(J, seal))
    say(u"")
    say(render_judge(J, seal))
    return J


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("judge", "inject", "tally"))
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", default=None, help="judge・inject: この docID の本だけ")
    ap.add_argument("--procs", type=int, default=1)
    a = ap.parse_args(argv)
    if a.cmd == "judge":
        run_judge(root=a.root, procs=a.procs, only=a.only, out=a.out)
    elif a.cmd == "inject":
        run_inject(root=a.root, procs=a.procs, only=a.only, out=a.out)
    else:
        run_tally(root=a.root)


if __name__ == "__main__":
    main()
