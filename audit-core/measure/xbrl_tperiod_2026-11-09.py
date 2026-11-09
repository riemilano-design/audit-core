# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md §3・§4・§5 ― 規則 T(表の見出しの「前期」の列の数を前期の手がかりがある数として扱う。P33E = P32E + 旗)の測定と、結果の表(tally)。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。** 測る側から engine(``core/``・``adapters/``)・``measure/lib``・``measure/inject.py``・前の便の script・記録・門は 1 行も変えない。

    python3 measure/xbrl_tperiod_2026-11-09.py moves     [--procs N] [--only <docID>] [--out PATH]   # AI の文 200 本で P32E → P33E の動いた行 → fixtures/xbrl/tperiod/moves_200_2026-11-09.json
    python3 measure/xbrl_tperiod_2026-11-09.py regress97 [--procs N] [--only <docID>] [--out PATH]   # 手元の 97 書類の原文での退行・動いた行・行頭が | の文 → fixtures/xbrl/tperiod/regress97_2026-11-09.json
    python3 measure/xbrl_tperiod_2026-11-09.py inject    [--procs N] [--only <docID>] [--out PATH]   # (a) T9 の id の対応付けの注入を P30E・P33E で (b) 表の期の入れ替え TP・TC を P32E・P33E で → fixtures/xbrl/tperiod/inject_2026-11-09.json
    python3 measure/xbrl_tperiod_2026-11-09.py tally     [--root DIR]                                 # 記録 3 つ(と PB の記録 2 つ)から T-1〜T-10 と K-1〜K-5 の表を出す(file は書かない)

``--only`` を付けた走らせ方は本番の記録ではない: ``--out`` を必ず指定する(指定が無ければ止める)。
PB の便の script ``xbrl_pbind_2026-11-06.py``(PB)は **1 byte も変えず**、importlib で読み込んで使う(写さない)。PB の ``judge_book_pb``・``doc_moves_pb``・``moves_block``・``inject_job_pb``・``write_record``・
``key_check_pb``・``engine_numstat``・``engine_message``・``moves_inputs``・``period5``・``install``、PB が読み込んだ RB の便の ``RM``・``RR``(``XR``)、T9 の第 2 便の ``PI``(``PS``)をそのまま呼ぶ。
PB の module の ``OLD``・``NEW``・``PROFILES``・``NOW_PROFILES``・``BASE_PROFILES``・``PAIRS``・``KEYED``・記録と封の path・封の commit は、この script が読み込みのあとに差し替える
(F5 の駆動 script と同じ形。差し替えは PB の module の中だけで、PB の file は変わらない)。この script が自分で持つのは、profile の対(P32E → P33E)・表の前期の列か・regress97 の集計・
表の期の入れ替え TP・TC の注入・封の字から幅を読む tally だけ。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めは結果の報告に書いた):
- 「動いた行」(T-3・T-4)= 両方の profile に在る数の claim(鍵 = (文の番号, 位置))のうち **state か pointers が違う行**(封 T-4 の字)。T-3 の「動いた行」も同じ定義(封の字に定義が無いので封に無い決め)。
  state が変わった行は別の欄に残す。reason だけが違う行は別に数える。
- 「表の前期の列の数か」= engine の ``_table_prior_keys_2026_11_09(文の列, V.P33E)`` の集合に (文の字, 位置) が在るか。文の列は ``RUN.sentence_list(zm, prof)``(zm = ``PR.build_modified_zip(zb, text)[0]``。97 書類の原文は zb)。
  moves の動いた行の中身の 11 番目の欄(PB の 10 欄の後ろ)。
- 「行頭が | の文」= 文の列のうち ``strip()`` が ``|`` で始まる文。200 本は moves の本ごとに、97 書類は regress97 の書類ごとに数える(T-3 は 97 書類の数、200 本の数は moves)。
- 「札」= 前の便の盲検の 1 席目(``RM.label_of``)。T-5 の「VALUE_MISMATCH → GROUNDED の行のうち札 真」= 前の state が VALUE_MISMATCH・後の state が GROUNDED・札 真の行、
  「札 偽の行が GROUNDED になった行」= 前の state が GROUNDED でなく後の state が GROUNDED・札 偽の行。
- 表の期の入れ替え(封 §0-1 の 5・§5 の 3 の字): 見出しに前期の列が 1 つ・当期の列が 1 つの表の行で、そのセルに ``_numbers_of`` の数がちょうど 1 つずつあり、無改変の P33E で前期のセル = Prior1Year の fact に GROUNDED・
  当期のセル = CurrentYear の fact に GROUNDED、2 つのセルの字が違い、行の字が元の文に 1 回だけ在る行を site にする(cap なし。全部採る)。TP = 前期のセルの数の字を当期のセルの字に替える、TC = 当期のセルの字を前期のセルの字に替える。
  1 回に 1 か所だけ替え、P32E・P33E で判定する。対応 = 注入後の文の列が元の文の列と同じ長さで、同じ番号の文が替えた文と同じ字で、(文の番号, 替えたセルの数の位置)の数の claim が在る。違えば「対応なし」(行には残す)。
  行の ``結果`` は (state, pointer の期)から決める小さい語(通した = state が GROUNDED / 前期の fact を名指して VALUE_MISMATCH / VALUE_MISMATCH(前期以外を名指す) / その他の state / 対応なし)で、封の字に無いので封に無い決め。
- T-6 の率の分母 = TP の行(対応なしを含む。封の字「分母 = 注入の行」)。止めた行 = P33E で対応が付いて通さなかった行。分母 0 の率は None = 外れ。T-7 = TC の行のうち P32E と P33E で ``結果`` か state が違う行(参考に期だけが違う行)。
- T-1 は git の numstat(封の commit から engine の commit まで)、T-9 は git の name-status の M(tests)から数える。T-8・T-10 は engine の commit の message の字を読んで写す
  (この木で変異・全数を走らせ直さない。PB の便と同じ決め)。T-10 は message の「全数(clone)で赤は <試験> の <本数> 本だけ(tests/measure 2 通りの順とも ... failed)」から (赤の試験, ほかの赤 = failed − 赤の本数)を読む。
  message に無ければ None = 外れ。
- 記録は文・span・value・会社名・pointer の字(要素名)を持たない。欄の名前に P30E・P32E とあるのは PB の便の名前のまま(この記録では OLD・NEW = P32E・P33E、(a) は P30E・P33E の意味)。
"""
from __future__ import print_function

import argparse
import collections
import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    u"""importlib で読み込む。``sys.modules`` にも登録する(``--procs`` 2 以上の fork で pickle に落ちないため)。読み込みの前に居た名前は、読み込みの後に元の object へ戻す
    (PB の script が中で読む前の便の script は決まった名前で登録し直して先に居た module を上書きするため。2026-11-06 の 7109c97 の直しと同じ)。読み込んだ module 自身の名前は残す。"""
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name_file))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for k, v in before.items():
            if k != mod_name and sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


PB = load_module("xbrl_pbind_2026-11-06.py", "pbind_for_tperiod")
RM, RR, PI, PS, XR = PB.RM, PB.RR, PB.PI, PB.PS, PB.XR
NF, GEN, RUN, TUNE = PB.NF, PB.GEN, PB.RUN, PB.TUNE
R97, D = PB.R97, PB.D
Stop = GEN.Stop

from adapters.xbrl import prose as PR                 # noqa: E402
from adapters.xbrl import recipes as R                # noqa: E402
from adapters.xbrl import verify_document as VD       # noqa: E402
from adapters.xbrl import vocabulary as V             # noqa: E402

SEAL_REL = "docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md"
SEAL_COMMIT = "eb281f1"
DOC_REL = "docs/XBRL_TABLE_PERIOD_ENGINE_RESULT_2026-11-09.md"
SCRIPT_REL = "measure/xbrl_tperiod_2026-11-09.py"
REC_DIR_REL = "fixtures/xbrl/tperiod"
MOVES_REL = REC_DIR_REL + "/moves_200_2026-11-09.json"
REGRESS97_REL = REC_DIR_REL + "/regress97_2026-11-09.json"
INJECT_REL = REC_DIR_REL + "/inject_2026-11-09.json"
REC_REL = collections.OrderedDict([("moves", MOVES_REL), ("regress97", REGRESS97_REL), ("inject", INJECT_REL)])
#: 読むだけの PB の便の記録・script(PB の便の script は PB の記録が script の sha256 を留めている)
PB_SCRIPT_REL = "measure/xbrl_pbind_2026-11-06.py"
PB_REGRESS97_REL = PB.REGRESS97_REL                                     # fixtures/xbrl/pbind/regress97_2026-11-06.json(T-2 の 97 書類の比べ先)
PB_INJECT_REL = PB.INJECT_REL                                           # fixtures/xbrl/pbind/inject_2026-11-06.json(T-2 の 141 行の比べ先)
PREV_SCRIPT_RELS = (PB_SCRIPT_REL,) + tuple(PB.PREV_SCRIPT_RELS)
LABELS_REL = PB.LABELS_REL
SOURCES = PB.SOURCES
LIB_RELS = PB.LIB_RELS
OLD, NEW = "P32E", "P33E"
BASE_OLD = "P30E"                                                       # (a) の土台の profile(T9 の id の対応付けは P30E 土台)
PROFILES = (OLD, NEW)
INJECT_A_PROFILES = (BASE_OLD, NEW)
BASE_PROFILES = tuple(PB.NOW_PROFILES)                                  # P22〜P32E の 10 profile(PB の記録の 10 profile)
NOW_PROFILES = BASE_PROFILES + (NEW,)
PAIRS = ((u"P33E 対 P32E", OLD, NEW),)
KEYED = (OLD, NEW)
ENGINE_FILES = ("adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py")
STATES = PB.STATES
G, VM, UNV, PNF = PB.G, PB.VM, PB.UNV, PB.PNF
HIT, MISS = PB.HIT, PB.MISS
LABEL_WORDS, NO_LABEL = PB.LABEL_WORDS, PB.NO_LABEL
EXISTING, NEWROW = PB.EXISTING, PB.NEWROW
PERIODS5 = PB.PERIODS5
LABEL_PASS, LABEL_NAMED_ORIGINAL = PB.LABEL_PASS, PB.LABEL_NAMED_ORIGINAL
TP, TC = u"TP", u"TC"
UNMAPPED_WORD = u"対応なし"
PASSED_WORD = u"通した"
NAMED_PRIOR_WORD = u"前期の fact を名指して VALUE_MISMATCH"
NAMED_OTHER_WORD = u"VALUE_MISMATCH(前期以外を名指す)"
SECTION_A = u"a T9 の id の対応付け(PB の記録の P32E の欄との照らし)"
SECTION_B = u"b 表の期の入れ替え TP・TC"
PB_SWAP = (("OLD", OLD), ("NEW", NEW), ("PROFILES", PROFILES), ("NOW_PROFILES", NOW_PROFILES), ("BASE_PROFILES", BASE_PROFILES), ("PAIRS", PAIRS), ("KEYED", KEYED),
           ("SEAL_REL", SEAL_REL), ("SEAL_COMMIT", SEAL_COMMIT), ("DOC_REL", DOC_REL), ("SCRIPT_REL", SCRIPT_REL), ("MOVES_REL", MOVES_REL), ("REGRESS97_REL", REGRESS97_REL),
           ("INJECT_REL", INJECT_REL), ("RB_RECORD_REL", PB_REGRESS97_REL))
XR_SWAP = (("SEAL_REL", SEAL_REL), ("SEAL_COMMIT", SEAL_COMMIT), ("OUT_REL", REGRESS97_REL), ("PREV_RECORD_REL", PB_REGRESS97_REL), ("NOW_PROFILES", NOW_PROFILES),
           ("BASE_PROFILES", BASE_PROFILES), ("PAIRS", PAIRS), ("KEYED", KEYED), ("ENGINE_FILES", ENGINE_FILES))
MOVES_LIMITS = (
    u"通した・止めたは engine の state で、動いた行の札は前の便の盲検の 1 席目(既存の行だけ。P28E でなく P27 にある行)。新しい行には札が無い",
    u"200 本は Claude の model 2 つが書いた文。表は F3 の 40 本だけで、見出しは全部 項目 / 当期 / 前期 / 増減(書き手への指示が決めた形)。動いた行の中身は (種類, 文の番号, 位置, 前後の state, 前後の pointer の期, 札, 既存 / 新, 前期の fact が無い要素, 表の前期の列の数か) だけで、文・span・値・要素名は持たない",
    u"表の前期の列の数か = engine の _table_prior_keys_2026_11_09 の集合に (文の字, 位置) が在るか。見出しの読み違いを行ごとに目で確かめてはいない")
REGRESS_LIMITS = (
    u"97 書類は 2026 年提出の有報に偏る(P27 の封 §8 と同じ標本)。原文の表は HTML を剥がした字で | を持たず、規則 T は原文では届かない(退行が無いことの確認で、規則が客の書類で効くことの確認ではない)",
    u"札が無いので動いた行の正しさは見ていない(T-3 は『壊さない』の確認)。T-8・T-10 は engine の commit の message の字を写した(この木で変異・全数を走らせ直していない)")
INJECT_LIMITS = (
    u"(a) は T9 の 1 型だけ(前期の fact に結ばれた数に当期の値を入れる)。site・並べ替え・cap・差し替え・対応付け(id で引く 3 条件)は T9 の第 2 便のまま。土台は P30E が GROUNDED の claim で、P33E の claim は (value, span, unit) が同じ 1 件があれば結ぶ",
    u"(b) の TP・TC は司令塔が作った新しい注入で、site は P33E が無改変で両方のセルを正しく結んだ行だけ(P33E に都合のよい母集団)。P32E が通す率の高さは P32E が表の前期の列を見ていないことの確認で、他の型の誤り(値の書き違い・単位の取り違え)を止める力は測らない",
    u"通した・止めたは engine の state で、札(人の目)は無い。表は AI の文の F3 だけで、見出しは 項目 / 当期 / 前期 / 増減。年だけの見出し・| 以外の区切りは規則 T の外")


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def within(x, lo_hi):
    return x is not None and lo_hi[0] <= x <= lo_hi[1]


# ======================================================================================================
# 配線: PB の module の名前をこの便の値に差し替える(使う側 ``PB.judge_book_pb`` などが引く名前)
def swap_into_pb():
    u"""PB の module の profile の対・path・封をこの便の値に差し替え、XR(RB の regress97 script)も差し替える。"""
    for name, v in PB_SWAP:
        setattr(PB, name, v)
    PB.XR_SWAP = XR_SWAP
    PB.install()


@contextlib.contextmanager
def swap_pb(**kv):
    u"""PB の module の名前を with の中だけ替える。出るときは必ず戻す((a) の P30E・P33E の対に使う)。"""
    old = dict((k, getattr(PB, k)) for k in kv)
    for k, v in kv.items():
        setattr(PB, k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            setattr(PB, k, v)


def wiring_problems():
    u"""PB の差し替えが届いているか・XR の差し替えが届いているか・PB 自身の配線。問題の列。"""
    out = [u"PB.%s が差し替えた先でない" % name for name, v in PB_SWAP if getattr(PB, name) != v]
    out += [u"XR.%s が差し替えた先でない" % name for name, v in XR_SWAP if getattr(XR, name) != v]
    out += list(PB.wiring_problems())
    if not hasattr(R, "_table_prior_keys_2026_11_09"):
        out.append(u"engine に _table_prior_keys_2026_11_09 が無い(規則 T の engine の commit の木でない)")
    if NEW not in V.PROFILES or not getattr(V.PROFILES[NEW], "table_period_2026_11_09", False):
        out.append(u"vocabulary に P33E が無いか旗が偽")
    return out


swap_into_pb()


def header_t(root, kind, step, before, after, e_commit, inputs, extra=None):
    u"""3 つの記録に共通の頭(封の追記は無い)。inputs = 読んだ入力の記録の path の列。"""
    h = collections.OrderedDict()
    h[u"seal"] = SEAL_REL
    h[u"封の commit"] = SEAL_COMMIT
    h[u"step"] = step
    h[u"HEAD の commit"] = GEN.git_head(os.path.dirname(root))
    h[u"engine の commit"] = e_commit
    h[u"この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    h[u"前の便の script の sha256"] = collections.OrderedDict((rel, PB.sha_rel(root, rel)) for rel in PREV_SCRIPT_RELS)
    h[u"入力の記録の sha256"] = collections.OrderedDict((rel, PB.sha_rel(root, rel)) for rel in inputs)
    h[u"engine の指紋"] = VD.engine_fingerprint()
    h[u"lib の指紋"] = collections.OrderedDict((rel, PB.sha_rel(root, rel)) for rel in LIB_RELS)
    h[u"profile"] = list(NOW_PROFILES) if kind == "regress97" else (list(PROFILES) if kind == "moves" else list(PROFILES) + [BASE_OLD])
    h[u"cache の前後"] = collections.OrderedDict([(u"前", before), (u"後", after), (u"変化なし", before == after)])
    if extra:
        h.update(extra)
    return h


# ======================================================================================================
# 表の前期の列か(engine の関数を読むだけ)
def bar_sentences(sents):
    u"""文の列のうち strip() が | で始まる文の数。"""
    return sum(1 for s in sents if s.strip().startswith("|"))


def table_view(zm, prof):
    u"""(文の列, 表の前期の列の数の集合)。文の列は engine の build_raw_claims と同じ手順(RUN.sentence_list)。"""
    sents = RUN.sentence_list(zm, prof)
    return sents, R._table_prior_keys_2026_11_09(sents, prof)


def is_table_prior(sents, keys, sentence, pos):
    return bool(isinstance(sentence, int) and 0 <= sentence < len(sents) and (sents[sentence], pos) in keys)


# ======================================================================================================
# moves: AI の文 200 本で P32E → P33E の動いた行
def judge_book_t(job):
    u"""1 本(RM.load_jobs の job)。PB の ``judge_book_pb``(OLD・NEW = P32E・P33E に差し替え済み)を呼び、動いた行に『表の前期の列の数か』を足す。"""
    head = PB.judge_book_pb(job)
    src, name, item, row, text_dir, zip_caches = job[:6]
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    zm = PR.build_modified_zip(zb, text)[0]
    prof = V.PROFILES[NEW]
    sents, keys = table_view(zm, prof)
    for x in head[u"動いた行の中身"]:
        x.append(is_table_prior(sents, keys, x[1], x[2]))
    head[u"行頭が | の文の数"] = bar_sentences(sents)
    head[u"表の前期の列の数"] = len(keys)
    return head


def moves_block_t(bs):
    u"""``本`` の列 → 集計 1 ブロック(全体・形別・model 別で同じ関数)。PB の ``moves_block`` に T の欄を足す。門が記録の ``本`` から作り直して照らす(集計の正本はこの関数)。"""
    blk = PB.moves_block(bs)
    rename = {u"E-4 動いた行": u"動いた行", u"E-4 GROUNDED を失う行": u"GROUNDED を失う行", u"E-4 POINTER_NOT_FOUND → VALUE_MISMATCH": u"POINTER_NOT_FOUND → VALUE_MISMATCH"}
    out = collections.OrderedDict((rename.get(k, k), v) for k, v in blk.items())
    X = [x for b in bs for x in b[u"動いた行の中身"]]
    table = [x for x in X if x[10] is True]
    other = [x for x in X if x[10] is not True]
    vmg = [x for x in X if x[3] == VM and x[4] == G]
    gained = [x for x in X if x[3] != G and x[4] == G]

    def lab(sel, w):
        return sum(1 for x in sel if x[8] == EXISTING and x[7] == w)
    out[u"表の前期の列の数の動いた行"] = len(table)
    out[u"表の前期の列の数でない動いた行"] = len(other)
    out[u"T-5 VALUE_MISMATCH → GROUNDED"] = collections.OrderedDict([(u"行", len(vmg)), (u"札 真", lab(vmg, u"真")), (u"札 偽", lab(vmg, u"偽")), (u"札 判定不能", lab(vmg, u"判定不能")),
                                                                    (u"新しい行(札なし)", sum(1 for x in vmg if x[8] == NEWROW)), (u"既存で札なし", sum(1 for x in vmg if x[8] == EXISTING and x[7] is None))])
    out[u"T-5 札 偽の行が GROUNDED になった行"] = lab(gained, u"偽")
    out[u"行頭が | の文"] = sum(b[u"行頭が | の文の数"] for b in bs)
    out[u"表の前期の列の数"] = sum(b[u"表の前期の列の数"] for b in bs)
    return out


def aggregate_moves_t(books):
    out = collections.OrderedDict([(u"全体", moves_block_t(books))])
    out[u"形別"] = collections.OrderedDict((f, moves_block_t([b for b in books if b[u"form"] == f])) for f in sorted(set(b[u"form"] for b in books)))
    out[u"model 別"] = collections.OrderedDict((m, moves_block_t([b for b in books if b[u"model"] == m])) for m in sorted(set(b[u"model"] for b in books)))
    return out


def run_moves(root=ROOT, procs=1, only=None, out=None, key_value=None, say=print):
    if out is None:
        if only is not None:
            raise Stop(u"**--only を付けた走らせ方は本番の記録を作らない。--out を指定する。止める**")
        out = os.path.join(root, MOVES_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    if tuple(RUN.PROFILES) != NF.PREV_PROFILES:
        raise Stop(u"**RUN.PROFILES が前の便の 4 つでない(P27 の鍵を引けない)。止める**")
    bad = wiring_problems()
    if bad:
        raise Stop(u"**配線が崩れている: %s。止める**" % u" / ".join(bad))
    seal, e, _num, _tests = XR.engine_commits()
    jobs_ = RM.load_jobs(root, only)
    caches = RM.caches_all()
    before = GEN.caches_snapshot(caches)
    say(u"動いた行 %d 本 × 2 profile(P32E・P33E)― procs %d" % (len(jobs_), procs))
    recs = NF.map_pool(judge_book_t, jobs_, procs)
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = header_t(root, "moves", u"規則 T(表の前期の列の数を前期の手がかりがある数として扱う)― AI の文 200 本の P32E → P33E の動いた行(0 USD)", before, after, e, PB.moves_inputs())
    rec[u"範囲"] = u"全 200 本" if only is None else u"**--only の本だけ(本番の記録ではない)**"
    rec[u"欄"] = collections.OrderedDict([
        (u"数の claim の鍵", u"(文の番号, 文の中の位置)。id は profile 間で替わるので使わない"),
        (u"動いた行", u"P32E と P33E の両方にある鍵のうち state か pointers が違う行(封 T-4 の字)。reason だけが違う行は別に数える"),
        (u"動いた行の中身", u"[種類, 文の番号, 位置, 前の state, 後の state, 前の期, 後の期, 札 or null, 既存 / 新, 前期の fact が無い要素, 表の前期の列の数か]。文・span・値・要素名は持たない"),
        (u"表の前期の列の数か", u"engine の _table_prior_keys_2026_11_09(文の列, P33E)の集合に (文の字, 位置) が在るか(動いた行の中身の 11 番目)"),
        (u"本の欄の名前", u"P30E と P32E で数の claim の鍵が同じ・P30E と P32E で鍵が違う本 の P30E・P32E は PB の便の名前のまま。この記録では P32E・P33E の意味"),
        (u"札", u"前の便の盲検の 1 席目の札(labels・f5_labels)。鍵 → id は P27 の raw claim の並び。既存 = P27 にも在る行。新しい行には札が無い"),
        (u"期", u"pointers の先頭の context の先頭の語: CurrentYear / Prior1Year / Prior2Year / 他 / なし")])
    rec[u"本"] = recs
    rec[u"集計"] = aggregate_moves_t(recs)
    rec[u"限界"] = list(MOVES_LIMITS)
    rec[u"key_leaks"] = []
    PB.write_record(out, rec, RUN, GEN, key_value=key_value)
    say(u"-> %s(本 %d)" % (out, len(recs)))
    return rec


# ======================================================================================================
# regress97: 手元の 97 書類の原文での退行・動いた行・行頭が | の文
def doc_job_t(args):
    u"""1 書類。XR の ``doc_job``(11 profile の出力の sha256・P32E・P33E の鍵つきの行)に、行頭が | の文の数と表の前期の列の数を足す(原文は zb を直接読む)。"""
    res = XR.doc_job(args)
    with io.open(args[4], "rb") as fh:
        zb = fh.read()
    sents, keys = table_view(zb, V.PROFILES[NEW])
    res[u"表"] = (bar_sentences(sents), len(keys))
    return res


def regress_block_t(docs):
    u"""``書類`` の行 → 集計(判定に使う欄)。門が記録の ``書類`` から作り直して照らす(集計の正本はこの関数)。"""
    out = collections.OrderedDict()
    out[u"4 state"] = collections.OrderedDict((p, collections.OrderedDict((s, sum(d[u"4 state"][p][s] for d in docs)) for s in STATES)) for p in NOW_PROFILES)
    out[u"claims"] = collections.OrderedDict((p, sum(d[u"claims"][p] for d in docs)) for p in NOW_PROFILES)
    c2 = collections.OrderedDict()
    for p in BASE_PROFILES:
        same = [d[u"docID"] for d in docs if d[u"出力の sha256(engine の欄を除く)"][p] == d[u"前の便の記録の sha256"][p]]
        c2[p] = collections.OrderedDict([(u"byte が同じ書類", len(same)), (u"書類", len(docs)), (u"違った書類", sorted(set(d[u"docID"] for d in docs) - set(same)))])
    out[u"T-2 旗が偽の profile の byte 一致"] = c2
    ents = [x for d in docs for x in d[u"P33E の動いた行"]]
    sch = [x for x in ents if x[8]]                                    # state が変わった行
    lost = [x for x in ents if x[4] == G and x[5] != G]
    gained = [x for x in ents if x[4] != G and x[5] == G]
    dirs = collections.Counter(u"%s → %s" % (x[4], x[5]) for x in sch)
    out[u"T-3 P33E 対 P32E"] = collections.OrderedDict([
        (u"行頭が | の文", sum(d[u"行頭が | の文の数"] for d in docs)), (u"動いた行", len(ents)), (u"GROUNDED を失う行", len(lost)), (u"GROUNDED になった行", len(gained)),
        (u"動いた書類", sum(1 for d in docs if d[u"P33E の動いた行"])), (u"state が変わった行", len(sch)), (u"向き別", collections.OrderedDict(sorted(dirs.items()))),
        (u"pointers だけが違う行", len(ents) - len(sch)), (u"reason だけが違う行", sum(d[u"reason だけが違う行"] for d in docs)),
        (u"XR の定義(state・reason・pointers のどれか)の動いた行", sum(len(d[u"動いた行と増えた行"][PAIRS[0][0]][u"動いた既存の行"]) for d in docs)),
        (u"増えた行", sum(d[u"動いた行と増えた行"][PAIRS[0][0]][u"増えた行"] for d in docs)), (u"消えた行", sum(d[u"動いた行と増えた行"][PAIRS[0][0]][u"消えた行"] for d in docs)),
        (u"claim の数が違う書類", sum(1 for d in docs if d[u"claims"][NEW] != d[u"claims"][OLD])), (u"表の前期の列の数", sum(d[u"表の前期の列の数"] for d in docs)),
        (u"行頭が | の文のある書類", sum(1 for d in docs if d[u"行頭が | の文の数"]))])
    return out


def regress_inputs():
    return [PB_REGRESS97_REL]


def run_regress97(root=ROOT, procs=1, only=None, out=None, say=print):
    if out is None:
        if only is not None:
            raise Stop(u"**--only を付けた走らせ方は本番の記録を作らない。--out を指定する。止める**")
        out = os.path.join(root, REGRESS97_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る。測り直さない。止める**")
    bad = wiring_problems()
    if bad:
        raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    P = R97.prec()
    names_before = collections.OrderedDict((k, P.names_sha(v)) for k, v in R97.CACHES.items())
    jobs, ids67, ids30 = R97.make_jobs(NOW_PROFILES)
    prev = D.jload(os.path.join(root, PB_REGRESS97_REL))
    prev_by = dict((r["docID"], r) for r in prev[u"書類"])
    if sorted(prev_by) != sorted(ids67 + ids30):
        raise Stop(u"**PB の便の記録の書類が 97 書類の一覧と合わない。止める**")
    if only is not None:
        jobs = [j for j in jobs if j[0] == only]
        if not jobs:
            raise Stop(u"**--only の docID が 97 書類に無い。止める**")
    zpath = dict((j[0], j[4]) for j in jobs)
    res = R97.run_pool(doc_job_t, jobs, procs)
    names_after = collections.OrderedDict((k, P.names_sha(v)) for k, v in R97.CACHES.items())
    if names_before != names_after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    docs = XR.doc_rows(res, prev_by)
    by_doc = dict((r[u"doc"], r) for r in res)
    for d in docs:
        ents, ro = PB.doc_moves_pb(by_doc[d[u"docID"]], zpath[d[u"docID"]])
        d[u"P33E の動いた行"] = ents
        d[u"reason だけが違う行"] = ro
        d[u"行頭が | の文の数"], d[u"表の前期の列の数"] = by_doc[d[u"docID"]][u"表"]
    seal, e, num, tests = XR.engine_commits()
    link = XR.engine_link()
    link[u"numstat"] = PB.engine_numstat()
    msg = message_numbers_t(PB.engine_message(e))
    rec = header_t(root, "regress97", u"規則 T(表の前期の列の数を前期の手がかりがある数として扱う)― 手元の 97 書類の有報の原文での退行・動いた行・行頭が | の文・engine の差分(0 USD)", names_before, names_after, e, regress_inputs())
    rec[u"範囲"] = u"全 97 書類" if only is None else u"**--only の 1 書類だけ(本番の記録ではない)**"
    rec[u"どの 97 か"] = u"67 = fixtures/xbrl/p26_2026-10-21.json の `書類 67` の key。30 = fixtures/xbrl/fresh/fetched_2026-10-21.json の `取得した書類` で `使う` が真。ZIP の sha256 はそれぞれの記録と照らした"
    rec[u"評価用の AI の文・DB の応答"] = u"開いていない(この script は edinetdb-p27/ の下を読まない)"
    rec[u"欄"] = collections.OrderedDict([
        (u"P33E の動いた行", u"[文の番号を含む鍵 (種類, 文の番号, 位置, 順), P32E の state, P33E の state, 前の期, 後の期, state が違う, pointers が違う, 前期の fact が無い要素]。state か pointers が違う行(封 T-4 の字。T-3 も同じ定義)"),
        (u"動いた行と増えた行", u"XR(N の便の regress97 script)の定義: state・reason・pointers のどれかが違う行と、増えた行・消えた行"),
        (u"行頭が | の文の数・表の前期の列の数", u"文の列(engine の build_raw_claims と同じ手順)のうち strip() が | で始まる文の数と、engine の _table_prior_keys_2026_11_09 の集合の大きさ"),
        (u"T-8・T-10 の写し", u"engine の commit の message の字を読んで写した(この木で変異・全数を走らせ直していない。PB の便と同じ決め)")])
    rec[u"T-1・T-9 engine の差分"] = link
    rec[u"T-8・T-10 の写し"] = collections.OrderedDict([(u"出どころ", u"engine の commit の message"), (u"engine の commit", e)] + [(k, v) for k, v in msg.items()])
    rec[u"集計"] = regress_block_t(docs)
    rec[u"書類"] = docs
    rec[u"限界"] = list(REGRESS_LIMITS)
    rec[u"key_leaks"] = D.record_key_leaks(rec)
    if rec[u"key_leaks"]:
        raise Stop(u"記録に鍵が入った")
    PB.write_record(out, rec, RUN, GEN)
    say(u"-> %s" % out)
    return rec


def message_numbers_t(message):
    u"""engine の commit の message から T-8・T-10 の数を読む。{T-8: {...} or None, T-10: {...} or None}。字が無ければ None(外れ)。"""
    m8 = re.search(r"変異 (\d+) 本全部赤", message or u"")
    m10 = re.search(r"全数\(clone\)で赤は ([A-Za-z0-9_ ]+?) の (\d+) 本だけ\(tests/measure 2 通りの順とも ([\d,]+) passed / (\d+) skipped / (\d+) failed\)", message or u"")
    t8 = collections.OrderedDict([(u"変異の本数", int(m8.group(1))), (u"赤", int(m8.group(1))), (u"原文", m8.group(0))]) if m8 else None
    t10 = None
    if m10:
        t10 = collections.OrderedDict([(u"赤の試験", [m10.group(1).strip()]), (u"赤の本数", int(m10.group(2))),
                                       (u"tests/measure", collections.OrderedDict([("passed", int(m10.group(3).replace(",", ""))), ("skipped", int(m10.group(4))), ("failed", int(m10.group(5)))])),
                                       (u"原文", m10.group(0))])
    return collections.OrderedDict([("T-8", t8), ("T-10", t10)])


# ======================================================================================================
# inject (a): T9 の id の対応付けを P30E・P33E で
def inject_a_rows(rows):
    u"""PB の ``inject_job_pb`` の行の LINK_KEY の名前を、この便の profile の名前にする(値は変えない)。"""
    out = []
    for r in rows:
        d = collections.OrderedDict()
        for k, v in r.items():
            d[u"%s の土台に対応" % NEW if k == PB.LINK_KEY else k] = v
        out.append(d)
    return out


# ======================================================================================================
# inject (b): 表の期の入れ替え TP・TC
def period_of(c):
    return PB.period5(tuple(c["pointers"] or ()))


def claims_by_key(zb, text, pname):
    u"""({(文の番号, 位置): claim}, 文の列)。数の claim だけ。文の列は注入後の文の列。"""
    zm = PR.build_modified_zip(zb, text)[0]
    prof = V.PROFILES[pname]
    out = VD.verify_document(zb, pname, text)
    nums, texts = R.build_raw_claims(zm, prof)
    cl = out["claims"]
    if len(cl) != len(nums) + len(texts):
        raise Stop(u"**検証の出力と raw claim の数が合わない。止める**")
    rows = {}
    for c, r in zip(cl, nums + texts):
        if c["kind"] == "num":
            rows[(r["sentence"], r["pos"])] = c
    return rows, RUN.sentence_list(zm, prof)


def table_sites(sents, prof):
    u"""[(文の番号, 当期のセルの数 (a, b), 前期のセルの数 (a, b))]。見出しの前期 1 列・当期 1 列、行のセルの数が見出しと同じで、前期・当期のセルに数がちょうど 1 つずつ。
    表の切り方・見出しの種類は engine と同じ(``R._table_head_kind_2026_11_09``・``R._numbers_of``)。"""
    out = []
    head = None
    prev = False
    for i, s in enumerate(sents):
        t = s.strip()
        if not t.startswith("|"):
            prev = False
            head = None
            continue
        cells = t.strip("|").split("|")
        if not prev:
            kinds = [R._table_head_kind_2026_11_09(c) for c in cells]
            head = kinds if (kinds.count("prior") == 1 and kinds.count("current") == 1) else None
            prev = True
            continue
        if head is None or len(cells) != len(head):
            continue
        bycol = collections.defaultdict(list)
        for (a, b, _signed, _unit, _prec) in R._numbers_of(prof, s):
            bycol[s[:a].count("|") - 1].append((a, b))
        ci, pi = head.index("current"), head.index("prior")
        if len(bycol[ci]) == 1 and len(bycol[pi]) == 1:
            out.append((i, bycol[ci][0], bycol[pi][0]))
    return out


def locate(text, sent):
    u"""元の文の字が text に 1 回だけ在れば その位置、無い・2 回以上なら None。"""
    k = text.find(sent)
    if k < 0 or text.find(sent, k + 1) >= 0:
        return None
    return k


def result_word(cell):
    u"""行の ``結果`` の語(state と pointer の期から決める。封の字に無いので封に無い決め)。"""
    if not cell[u"対応"]:
        return UNMAPPED_WORD
    if cell[u"state"] == G:
        return PASSED_WORD
    if cell[u"state"] == VM:
        return NAMED_PRIOR_WORD if cell[u"期"] == "Prior1Year" else NAMED_OTHER_WORD
    return cell[u"state"]


def cell_of(claim, ok):
    u"""profile ごとの欄 {対応, state, 期, 結果}。対応が付かない行は state None・期 なし。"""
    if not ok or claim is None:
        c = collections.OrderedDict([(u"対応", False), (u"state", None), (u"期", u"なし")])
    else:
        c = collections.OrderedDict([(u"対応", True), (u"state", claim["state"]), (u"期", period_of(claim))])
    c[u"結果"] = result_word(c)
    return c


def table_book(job):
    u"""1 本の表の期の入れ替え(job = RM.load_jobs の job の先頭 6 つ)。(name, form, 数え, 行)。"""
    src, name, item, row, text_dir, zip_caches = job[:6]
    form, model = item[u"form"], item[u"model"]
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    base = dict((p, claims_by_key(zb, text, p)) for p in PROFILES)
    sents = base[NEW][1]
    prof = V.PROFILES[NEW]
    counts = collections.OrderedDict([(u"表の前期の列の数", len(R._table_prior_keys_2026_11_09(sents, prof))), (u"site 候補(見出しの前期 1 列・当期 1 列・セルに数 1 つずつ)", 0), (u"土台が合わない", 0),
                                      (u"2 つのセルの字が同じ", 0), (u"行の字が文に 1 回でない", 0), (u"採った site", 0)])
    rows = []
    n = 0
    for (i, (ca, cb), (pa, pb)) in table_sites(sents, prof):
        counts[u"site 候補(見出しの前期 1 列・当期 1 列・セルに数 1 つずつ)"] += 1
        bt = base[NEW][0]
        c_cur, c_pri = bt.get((i, ca)), bt.get((i, pa))
        if not (c_cur and c_pri and c_cur["state"] == G and period_of(c_cur) == "CurrentYear" and c_pri["state"] == G and period_of(c_pri) == "Prior1Year"):
            counts[u"土台が合わない"] += 1
            continue
        s = sents[i]
        cur_txt, pri_txt = s[ca:cb], s[pa:pb]
        if cur_txt == pri_txt:
            counts[u"2 つのセルの字が同じ"] += 1
            continue
        k = locate(text, s)
        if k is None:
            counts[u"行の字が文に 1 回でない"] += 1
            continue
        counts[u"採った site"] += 1
        n += 1
        for typ in (TP, TC):
            if typ == TP:
                ns, key_a = s[:pa] + cur_txt + s[pb:], pa
            else:
                ns, key_a = s[:ca] + pri_txt + s[cb:], ca
            t2 = text[:k] + ns + text[k + len(s):]
            r = collections.OrderedDict([(u"id", u"%s-TT-%03d-%s" % (name, n, typ)), (u"形", form), (u"model", model), (u"型", typ)])
            for p in PROFILES:
                rows2, sents2 = claims_by_key(zb, t2, p)
                mapped = len(sents2) == len(sents) and i < len(sents2) and sents2[i] == ns
                r[p] = cell_of(rows2.get((i, key_a)) if mapped else None, mapped)
            rows.append(r)
    return name, form, counts, rows


def table_job(job):
    name, form, counts, rows = table_book(job)
    return name, [collections.OrderedDict([(u"docID", job[2][u"docID"])] + list(r.items())) for r in rows], counts


def _same_result(a, b):
    return a[u"結果"] == b[u"結果"] and a[u"state"] == b[u"state"]


def inject_columns_t(rows_a, rows_b, pb_rows):
    u"""T-2(141 行)・T-6・T-7 の欄を (a) の行・(b) の行・PB の記録の行から数える(記録の ``集計`` と tally の判定が使う。門が行から数え直す)。"""
    pb = dict((r[u"id"], r) for r in pb_rows)
    ids, pbids = set(r[u"id"] for r in rows_a), set(pb)
    t2 = collections.OrderedDict([
        (u"行の数", len(rows_a)), (u"PB の記録の行の数", len(pb_rows)), (u"id の集合が PB の記録と同じ", ids == pbids),
        (u"P33E の結果と state が PB の記録の P32E の欄と同じ行", sum(1 for r in rows_a if r[u"id"] in pb and _same_result(r[NEW], pb[r[u"id"]][OLD]))),
        (u"参考 P30E の結果と state が PB の記録の P30E の欄と同じ行", sum(1 for r in rows_a if r[u"id"] in pb and _same_result(r[BASE_OLD], pb[r[u"id"]][BASE_OLD])))])
    tp = [r for r in rows_b if r[u"型"] == TP]
    tc = [r for r in rows_b if r[u"型"] == TC]
    stopped = [r for r in tp if r[NEW][u"対応"] and r[NEW][u"state"] != G]
    named = [r for r in stopped if r[NEW][u"結果"] == NAMED_PRIOR_WORD]
    p32 = sum(1 for r in tp if r[OLD][u"state"] == G)
    p33 = sum(1 for r in tp if r[NEW][u"state"] == G)
    t6 = collections.OrderedDict([
        (u"site(TP の行)", len(tp)), (u"P32E が通した率", pct(p32, len(tp))), (u"P33E が通した率", pct(p33, len(tp))), (u"P32E が通した行", p32), (u"P33E が通した行", p33),
        (u"P33E が止めた行", len(stopped)), (u"うち前期の fact を名指して VALUE_MISMATCH", len(named)), (u"名指した割合", pct(len(named), len(stopped))),
        (u"対応が付かない行", collections.OrderedDict([(OLD, sum(1 for r in tp if not r[OLD][u"対応"])), (NEW, sum(1 for r in tp if not r[NEW][u"対応"]))]))])
    diff = [r for r in tc if not _same_result(r[OLD], r[NEW])]
    t7 = collections.OrderedDict([
        (u"TC の行", len(tc)), (u"P32E と P33E で結果か state が違う行", len(diff)), (u"参考 期だけが違う行", sum(1 for r in tc if _same_result(r[OLD], r[NEW]) and r[OLD][u"期"] != r[NEW][u"期"])),
        (u"対応が付かない行", collections.OrderedDict([(OLD, sum(1 for r in tc if not r[OLD][u"対応"])), (NEW, sum(1 for r in tc if not r[NEW][u"対応"]))]))])
    return collections.OrderedDict([(u"T-2 PB の記録との照らし", t2), (u"T-6 TP", t6), (u"T-7 TC", t7)])


def inject_summary_t(rows_b):
    u"""TP・TC ごと・profile ごとの結果の語の数(分母 = その型の行)。"""
    words = (PASSED_WORD, NAMED_PRIOR_WORD, NAMED_OTHER_WORD, UNV, PNF, UNMAPPED_WORD)
    out = collections.OrderedDict()
    for typ in (TP, TC):
        sel = [r for r in rows_b if r[u"型"] == typ]
        d = collections.OrderedDict([(u"行", len(sel))])
        for p in PROFILES:
            c = collections.Counter(r[p][u"結果"] for r in sel)
            d[p] = collections.OrderedDict((w, c.get(w, 0)) for w in words)
        out[typ] = d
    return out


def run_inject(root=ROOT, procs=1, only=None, out=None, key_value=None, say=print, work_root=None):
    if out is None:
        if only is not None:
            raise Stop(u"**--only を付けた走らせ方は本番の記録を作らない。--out を指定する。止める**")
        out = os.path.join(root, INJECT_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    if getattr(PI.N, PI.FLAG):
        raise Stop(u"**切り替えが真のまま inject を始めた。止める**")
    bad = list(PI.wiring_problems()) + wiring_problems()
    if bad:
        raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    seed, seed_meta = PI.GEN.seed_value(root)
    books = PI.load_books(root, only)
    jobs_b = RM.load_jobs(root, only)
    caches = PI.caches_all()
    before = PI.GEN.caches_snapshot(caches)
    work_root = work_root or tempfile.mkdtemp(prefix="tperiod_inject_", dir=os.environ.get("TMPDIR"))
    jobs_a = [(src, n, item, row, PI.SOURCES[src]["cache"], PI.GEN.EXISTING_CACHES, seed, work_root) for (src, n, item, row, _prior) in books]
    say(u"(a) T9 の注入 %d 本 × 2 profile(P30E・P33E)。切り替え 真・T9_PRIOR_TO_CURRENT・id で引く対応付け ― procs %d(1 件ごとに判定。時間がかかる)" % (len(jobs_a), procs))
    with swap_pb(OLD=BASE_OLD, NEW=NEW, PROFILES=INJECT_A_PROFILES):
        with PI.yen_scan_on():
            if not getattr(PI.N, PI.FLAG) or PI.wiring_problems():
                raise Stop(u"**切り替えを真にできない・配線が崩れた。止める**")
            results_a = PI.NF.map_pool(PB.inject_job_pb, jobs_a, procs)
    if getattr(PI.N, PI.FLAG):
        raise Stop(u"**with を出ても切り替えが真のまま。止める**")
    if tuple(PB.PROFILES) != PROFILES or (PB.OLD, PB.NEW) != (OLD, NEW):
        raise Stop(u"**PB の profile の対が with を出ても戻らない。止める**")
    rows_a, per_a = [], collections.OrderedDict()
    for n, r, c in results_a:
        rows_a += inject_a_rows(r)
        per_a[n] = c
    say(u"(b) 表の期の入れ替え %d 本 × 2 profile(P32E・P33E)― procs %d" % (len(jobs_b), procs))
    results_b = PI.NF.map_pool(table_job, [j[:6] for j in jobs_b], procs)
    rows_b, per_b = [], collections.OrderedDict()
    for n, r, c in results_b:
        rows_b += r
        per_b[n] = c
    after = PI.GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    pb_rec = PI.GEN.jload(os.path.join(root, PB_INJECT_REL))
    _s, e, _n, _t = XR.engine_commits()
    rec = header_t(root, "inject", u"規則 T(表の前期の列の数を前期の手がかりがある数として扱う)― (a) T9 の id の対応付けの注入を P30E・P33E で、(b) 表の期の入れ替え TP・TC を P32E・P33E で(0 USD)", before, after, e,
                   [PB_INJECT_REL] + [p["gen"] for p in SOURCES.values()])
    rec[u"範囲"] = u"全 200 本" if only is None else u"**--only(本番の記録ではない)**"
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", PI.FLAG), (u"(a) の inject の中の値", True), (u"出たあとの値", bool(getattr(PI.N, PI.FLAG))), (u"配線の問題", PI.wiring_problems())])
    rec[u"種"] = {u"file": PI.RUN.SEED_REL_STR, u"種の確認": seed_meta}
    rec[u"型"] = collections.OrderedDict([
        (u"a", u"PB の便と同じ site・並べ替え・cap・差し替え・対応付け(T9 の第 2 便のまま)。P30E 土台・P33E で判定し、id ごとに PB の記録の P32E の欄と照らす"),
        (u"b", u"表の期の入れ替え。site = 見出しに前期の列 1 つ・当期の列 1 つの表の行で、セルに _numbers_of の数がちょうど 1 つずつ、無改変の P33E で前期のセル = Prior1Year の fact に GROUNDED・当期のセル = CurrentYear の fact に GROUNDED、"
              u"2 つのセルの字が違い、行の字が元の文に 1 回だけ。cap なし(site は全部)。TP = 前期のセルの数の字を当期のセルの字に、TC = 当期のセルの字を前期のセルの字に。1 回に 1 か所、P32E・P33E で判定"),
        (u"対応", u"b: 注入後の文の列が元の文の列と同じ長さで、同じ番号の文が替えた文と同じ字で、(文の番号, 替えたセルの数の位置)の数の claim が在る。違えば 対応なし(行には残す)"),
        (u"結果", u"b: state と pointer の期から決める。通した = state が GROUNDED / 前期の fact を名指して VALUE_MISMATCH / VALUE_MISMATCH(前期以外を名指す) / その他の state / 対応なし"),
        (u"期", u"pointers の先頭の context の先頭の語: CurrentYear / Prior1Year / Prior2Year / 他 / なし。要素名は持たない")])
    rec[SECTION_A] = collections.OrderedDict([(u"本ごとの数え", per_a), (u"注入の行の数", len(rows_a))])
    rec[SECTION_B] = collections.OrderedDict([(u"本ごとの数え", per_b), (u"注入の行の数", len(rows_b)), (u"集計", inject_summary_t(rows_b))])
    rec[u"集計の欄"] = inject_columns_t(rows_a, rows_b, pb_rec[u"行"])
    rec[u"限界"] = list(INJECT_LIMITS)
    rec[u"key_leaks"] = []
    rec[u"行"] = collections.OrderedDict([(SECTION_A, rows_a), (SECTION_B, rows_b)])                     # 鍵の検査は ``行`` の中を『32 字以上の英数字』では見ない(行の id は 本の名前 + 番号で 32 字を超える)
    text = json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    PB.write_record(out, rec, PI.RUN, PI.GEN, text=text, key_value=key_value)
    say(u"-> %s(a %d 行・b %d 行)" % (out, len(rows_a), len(rows_b)))
    return rec


# ======================================================================================================
# tally: 封の表(§3 の T-1〜T-10・§4 の K-1〜K-5)を読み、記録から判定する
def read_seal(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def seal_pred_rows(seal):
    u"""封 §3 の表の行 {T-n: (欄, 予測, 外れ方)}。"""
    sec = seal[seal.index("## §3"):seal.index("## §4")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| (T-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            out[m.group(1)] = (cells[0], cells[1], cells[2] if len(cells) > 2 else u"")
    return out


def seal_k_rows(seal):
    sec4 = seal[seal.index("## §4"):seal.index("## §5")]
    return collections.OrderedDict((m.group(1), m.group(2)) for m in re.finditer(r"^- (K-\d): (.*)$", sec4, re.M))


def seal_bounds(seal):
    u"""封の字から予測の幅と採用の基準の閾値を読む(字のコピーにしない)。{名前: 値}。"""
    P = seal_pred_rows(seal)
    K = seal_k_rows(seal)
    b = collections.OrderedDict()

    def ints(m):
        return [int(x) for x in m.groups()]
    a = ints(re.match(r"^(\d+)〜(\d+) / (\d+)、(\d+)〜(\d+) / (\d+)、(\d+)$", P["T-1"][1].strip()))
    b["T-1"] = collections.OrderedDict([(u"recipes 挿入", (a[0], a[1])), (u"recipes 削除", a[2]), (u"vocabulary 挿入", (a[3], a[4])), (u"vocabulary 削除", a[5]), (u"他の file", a[6])])
    a = ints(re.match(r"^(\d+) / (\d+)、(\d+) / (\d+)$", P["T-2"][1].strip()))
    b["T-2"] = collections.OrderedDict([(u"byte が同じ書類", a[0]), (u"書類", a[1]), (u"P33E の結果と state が同じ行", a[2]), (u"行", a[3])])
    a = ints(re.match(r"^(\d+) / (\d+) / (\d+)$", P["T-3"][1].strip()))
    b["T-3"] = collections.OrderedDict([(u"行頭が | の文", a[0]), (u"動いた行", a[1]), (u"GROUNDED を失う行", a[2])])
    a = ints(re.match(r"^(\d+)〜(\d+) / (\d+) / (\d+) / \+(\d+)〜\+(\d+)$", P["T-4"][1].strip()))
    b["T-4"] = collections.OrderedDict([(u"動いた行", (a[0], a[1])), (u"表の前期の列の数でない動いた行", a[2]), (u"GROUNDED を失う行", a[3]), (u"GROUNDED の数の増え", (a[4], a[5]))])
    a = ints(re.match(r"^(\d+)〜(\d+) / (\d+)$", P["T-5"][1].strip()))
    b["T-5"] = collections.OrderedDict([(u"VALUE_MISMATCH → GROUNDED の札 真", (a[0], a[1])), (u"札 偽の行が GROUNDED になった行", a[2])])
    a = ints(re.match(r"^(\d+)〜(\d+) / (\d+)〜(\d+)% / (\d+)〜(\d+)% / (\d+)〜(\d+)%$", P["T-6"][1].strip()))
    b["T-6"] = collections.OrderedDict([(u"site", (a[0], a[1])), (u"P32E が通した率", (a[2], a[3])), (u"P33E が通した率", (a[4], a[5])), (u"名指した割合", (a[6], a[7]))])
    a = ints(re.match(r"^(\d+)〜(\d+)$", P["T-7"][1].strip()))
    b["T-7"] = (a[0], a[1])
    a = ints(re.match(r"^(\d+) / (\d+)$", P["T-8"][1].strip()))
    b["T-8"] = collections.OrderedDict([(u"赤", a[0]), (u"変異の本数", a[1])])
    a = ints(re.match(r"^(\d+)〜(\d+)$", P["T-9"][1].strip()))
    b["T-9"] = (a[0], a[1])
    m = re.match(r"^([A-Za-z0-9_]+) の ([A-Za-z0-9_]+) だけ、(\d+)$", P["T-10"][1].strip())
    b["T-10"] = collections.OrderedDict([(u"赤の試験", [u"%s %s" % (m.group(1), m.group(2))]), (u"ほかの赤", int(m.group(3)))])
    b["K-1"] = tuple(int(x) for x in re.search(r"T-2 が (\d+) / (\d+) かつ (\d+) / (\d+)", K["K-1"]).groups())
    m = re.search(r"T-3 の GROUNDED を失う行 (\d+)、かつ T-4 の GROUNDED を失う行 (\d+)", K["K-2"])
    b["K-2"] = (int(m.group(1)), int(m.group(2)))
    m = re.search(r"T-4 の表の前期の列でない動いた行 (\d+)、かつ T-5 の札 偽が GROUNDED になった行 (\d+)", K["K-3"])
    b["K-3"] = (int(m.group(1)), int(m.group(2)))
    m = re.search(r"T-6 の P33E の通した率 ≤ (\d+)%.*P32E の通した率 ≥ (\d+)%", K["K-4"])
    b["K-4"] = collections.OrderedDict([(u"P33E の通した率の上限", int(m.group(1))), (u"P32E の通した率の下限", int(m.group(2)))])
    m = re.search(r"T-8 が (\d+) / (\d+) かつ T-10", K["K-5"])
    b["K-5"] = collections.OrderedDict([(u"赤", int(m.group(1))), (u"変異の本数", int(m.group(2)))])
    return b


def t8_value(copy_, bound):
    u"""T-8: 写した『変異 N 本全部赤』が封の変異の本数以上なら、封の変異は全部赤。写しが無ければ None。"""
    t8 = (copy_ or {}).get("T-8")
    if not t8 or t8.get(u"変異の本数") != t8.get(u"赤"):
        return None
    if t8[u"赤"] < bound[u"変異の本数"]:
        return None
    return collections.OrderedDict([(u"赤", bound[u"赤"]), (u"変異の本数", bound[u"変異の本数"]), (u"写した全部赤の本数", t8[u"赤"])])


def t10_value(copy_):
    u"""T-10: 写した『全数(clone)で赤は <試験> の M 本だけ(... F failed)』から (赤の試験, ほかの赤 = F − M)。ほかの赤が負なら None。"""
    t10 = (copy_ or {}).get("T-10")
    if not t10:
        return None
    other = t10[u"tests/measure"]["failed"] - t10[u"赤の本数"]
    if other < 0:
        return None
    return collections.OrderedDict([(u"赤の試験", list(t10[u"赤の試験"])), (u"赤の本数", t10[u"赤の本数"]), (u"ほかの赤", other)])


def judge_from(cols, seal):
    u"""cols = {"moves": 集計の全体, "regress": regress_block_t, "inject": inject_columns_t, "link": T-1・T-9 の欄, "copy": T-8・T-10 の写し}。"""
    B = seal_bounds(seal)
    P = seal_pred_rows(seal)
    mv, rg, ij, link, cp = cols["moves"], cols["regress"], cols["inject"], cols["link"], cols["copy"]
    E = collections.OrderedDict()

    def put(k, ok, val):
        E[k] = {u"判定": HIT if ok else MISS, u"値": val}
    ns = link[u"numstat"]
    rec_n, voc_n = ns.get(ENGINE_FILES[0]), ns.get(ENGINE_FILES[1])
    others = sorted(f for f in ns if f not in ENGINE_FILES)
    v1 = collections.OrderedDict([(u"recipes 挿入", rec_n[0] if rec_n else None), (u"recipes 削除", rec_n[1] if rec_n else None), (u"vocabulary 挿入", voc_n[0] if voc_n else None),
                                  (u"vocabulary 削除", voc_n[1] if voc_n else None), (u"他の file", len(others))])
    t1 = B["T-1"]
    put("T-1", rec_n is not None and voc_n is not None and within(v1[u"recipes 挿入"], t1[u"recipes 挿入"]) and v1[u"recipes 削除"] == t1[u"recipes 削除"]
        and within(v1[u"vocabulary 挿入"], t1[u"vocabulary 挿入"]) and v1[u"vocabulary 削除"] == t1[u"vocabulary 削除"] and v1[u"他の file"] == t1[u"他の file"], v1)
    c2 = rg[u"T-2 旗が偽の profile の byte 一致"]
    cn = collections.OrderedDict((p, v[u"byte が同じ書類"]) for p, v in c2.items())
    cd = set(v[u"書類"] for v in c2.values())
    t2, t2b = ij[u"T-2 PB の記録との照らし"], B["T-2"]
    v2 = collections.OrderedDict([(u"97 byte が同じ書類(profile 間の最小)", min(cn.values()) if cn else None), (u"書類", t2b[u"書類"]), (u"profile", len(c2)),
                                  (u"P33E の結果と state が同じ行", t2[u"P33E の結果と state が PB の記録の P32E の欄と同じ行"]), (u"行", t2[u"行の数"])])
    put("T-2", len(c2) == len(BASE_PROFILES) and cd == {t2b[u"書類"]} and all(n == t2b[u"byte が同じ書類"] for n in cn.values()) and t2[u"id の集合が PB の記録と同じ"] is True
        and t2[u"行の数"] == t2b[u"行"] and t2[u"P33E の結果と state が PB の記録の P32E の欄と同じ行"] == t2b[u"P33E の結果と state が同じ行"], v2)
    r3, t3 = rg[u"T-3 P33E 対 P32E"], B["T-3"]
    v3 = collections.OrderedDict([(u"行頭が | の文", r3[u"行頭が | の文"]), (u"動いた行", r3[u"動いた行"]), (u"GROUNDED を失う行", r3[u"GROUNDED を失う行"])])
    put("T-3", all(v3[k] == t3[k] for k in t3), v3)
    t4 = B["T-4"]
    v4 = collections.OrderedDict([(u"動いた行", mv[u"動いた行"]), (u"表の前期の列の数でない動いた行", mv[u"表の前期の列の数でない動いた行"]), (u"GROUNDED を失う行", mv[u"GROUNDED を失う行"][u"行"]),
                                  (u"GROUNDED の数の増え", mv[u"GROUNDED の数"][u"差"])])
    put("T-4", within(v4[u"動いた行"], t4[u"動いた行"]) and v4[u"表の前期の列の数でない動いた行"] == t4[u"表の前期の列の数でない動いた行"] and v4[u"GROUNDED を失う行"] == t4[u"GROUNDED を失う行"]
        and within(v4[u"GROUNDED の数の増え"], t4[u"GROUNDED の数の増え"]), v4)
    t5 = B["T-5"]
    vm = mv[u"T-5 VALUE_MISMATCH → GROUNDED"]
    v5 = collections.OrderedDict([(u"VALUE_MISMATCH → GROUNDED の札 真", vm[u"札 真"]), (u"札 偽の行が GROUNDED になった行", mv[u"T-5 札 偽の行が GROUNDED になった行"])])
    put("T-5", within(v5[u"VALUE_MISMATCH → GROUNDED の札 真"], t5[u"VALUE_MISMATCH → GROUNDED の札 真"]) and v5[u"札 偽の行が GROUNDED になった行"] == t5[u"札 偽の行が GROUNDED になった行"], v5)
    c6, t6 = ij[u"T-6 TP"], B["T-6"]
    v6 = collections.OrderedDict([(u"site", c6[u"site(TP の行)"]), (u"P32E が通した率", c6[u"P32E が通した率"]), (u"P33E が通した率", c6[u"P33E が通した率"]), (u"名指した割合", c6[u"名指した割合"])])
    put("T-6", all(within(v6[k], t6[k]) for k in t6), v6)
    c7 = ij[u"T-7 TC"]
    v7 = collections.OrderedDict([(u"P32E と P33E で結果か state が違う行", c7[u"P32E と P33E で結果か state が違う行"])])
    put("T-7", within(v7[u"P32E と P33E で結果か state が違う行"], B["T-7"]), v7)
    v8 = t8_value(cp, B["T-8"])
    put("T-8", v8 is not None and v8[u"赤"] == B["T-8"][u"赤"] and v8[u"変異の本数"] == B["T-8"][u"変異の本数"], v8 if v8 is not None else collections.OrderedDict([(u"赤", None)]))
    t9 = link[u"直した file(M)"]
    put("T-9", within(t9, B["T-9"]), collections.OrderedDict([(u"直した file(M)", t9), (u"新しい file(A)", link[u"新しい file(A)"]), (u"engine の挿入の行数", link[u"engine の挿入の行数"])]))
    v10 = t10_value(cp)
    put("T-10", v10 is not None and v10[u"赤の試験"] == B["T-10"][u"赤の試験"] and v10[u"ほかの赤"] == B["T-10"][u"ほかの赤"], v10 if v10 is not None else collections.OrderedDict([(u"赤の試験", None)]))
    K = collections.OrderedDict()
    K["K-1"] = {u"判定": HIT if E["T-2"][u"判定"] == HIT else MISS, u"値": collections.OrderedDict([("T-2", E["T-2"][u"判定"])])}
    k2 = B["K-2"]
    K["K-2"] = {u"判定": HIT if v3[u"GROUNDED を失う行"] == k2[0] and v4[u"GROUNDED を失う行"] == k2[1] else MISS,
                u"値": collections.OrderedDict([(u"T-3 の GROUNDED を失う行", v3[u"GROUNDED を失う行"]), (u"T-4 の GROUNDED を失う行", v4[u"GROUNDED を失う行"])])}
    k3 = B["K-3"]
    K["K-3"] = {u"判定": HIT if v4[u"表の前期の列の数でない動いた行"] == k3[0] and v5[u"札 偽の行が GROUNDED になった行"] == k3[1] else MISS,
                u"値": collections.OrderedDict([(u"表の前期の列の数でない動いた行", v4[u"表の前期の列の数でない動いた行"]), (u"札 偽の行が GROUNDED になった行", v5[u"札 偽の行が GROUNDED になった行"])])}
    k4 = B["K-4"]
    K["K-4"] = {u"判定": HIT if (v6[u"P33E が通した率"] is not None and v6[u"P33E が通した率"] <= k4[u"P33E の通した率の上限"]
                                 and v6[u"P32E が通した率"] is not None and v6[u"P32E が通した率"] >= k4[u"P32E の通した率の下限"]) else MISS,
                u"値": collections.OrderedDict([(u"P33E が通した率", v6[u"P33E が通した率"]), (u"P32E が通した率", v6[u"P32E が通した率"])])}
    K["K-5"] = {u"判定": HIT if v8 is not None and (v8[u"赤"], v8[u"変異の本数"]) == (B["K-5"][u"赤"], B["K-5"][u"変異の本数"]) and E["T-10"][u"判定"] == HIT else MISS,
                u"値": collections.OrderedDict([("T-8", E["T-8"][u"判定"]), ("T-10", E["T-10"][u"判定"])])}
    adopt = all(K[k][u"判定"] == HIT for k in K)
    return collections.OrderedDict([(u"E", E), (u"K", K), (u"採用", adopt), (u"欄", collections.OrderedDict((k, v[0]) for k, v in P.items()))])


def columns_from_records(R_):
    u"""記録 3 つ + PB の記録(R_ = {"moves", "regress97", "inject", "pb_inject"})から判定に使う欄を行・本・書類から数え直す(記録の集計・集計の欄は使わない)。"""
    rg = R_["regress97"]
    inj = R_["inject"]
    return collections.OrderedDict([
        ("moves", moves_block_t(R_["moves"][u"本"])), ("regress", regress_block_t(rg[u"書類"])),
        ("inject", inject_columns_t(inj[u"行"][SECTION_A], inj[u"行"][SECTION_B], R_["pb_inject"][u"行"])),
        ("link", rg[u"T-1・T-9 engine の差分"]), ("copy", dict((k, v) for k, v in rg[u"T-8・T-10 の写し"].items() if k in ("T-8", "T-10")))])


def build_E(R_, seal):
    return judge_from(columns_from_records(R_), seal)


def fmt(v):
    u"""表の『測った値』の字。list は ・ でつなぎ、それ以外は RM.fmt(真偽・小数 1 桁・桁区切りの整数・dict)。"""
    if isinstance(v, (list, tuple)):
        return u"・".join(fmt(x) for x in v)
    if isinstance(v, dict):
        return u"・".join(u"%s %s" % (k, fmt(x)) for k, x in v.items())
    if v is None:
        return u"なし"
    return RM.fmt(v)


def render_pred(J, seal=None):
    seal = seal if seal is not None else read_seal()
    P = seal_pred_rows(seal)
    lines = [u"| # | 欄 | 予測 | 測った値 | 判定 |", u"|---|---|---|---|---|"]
    for k, v in J[u"E"].items():
        lines.append(u"| %s | %s | %s | %s | %s |" % (k, P[k][0], P[k][1], fmt(v[u"値"]), v[u"判定"]))
    return u"\n".join(lines)


def k_cell(text):
    u"""封の K の本文の最初の一文(「。」の前まで)。表を短くする。決め方は固定。"""
    return text.split(u"。")[0].strip()


def render_judge(J, seal=None):
    seal = seal if seal is not None else read_seal()
    names = seal_k_rows(seal)
    lines = [u"| # | 基準 | 測った値 | 判定 |", u"|---|---|---|---|"]
    for k, v in J[u"K"].items():
        lines.append(u"| %s | %s | %s | %s |" % (k, k_cell(names[k]), fmt(v[u"値"]), v[u"判定"]))
    lines.append(u"")
    lines.append(u"採用の判定(K-1〜K-5 を全部満たす): **%s**。最後に決めるのは人間。" % (u"採用" if J[u"採用"] else u"採用しない(人間に返す)"))
    return u"\n".join(lines)


def load_records(root=ROOT):
    out = collections.OrderedDict((k, GEN.jload(os.path.join(root, v))) for k, v in REC_REL.items())
    out["pb_inject"] = GEN.jload(os.path.join(root, PB_INJECT_REL))
    return out


def run_tally(root=ROOT, say=print):
    seal = read_seal(root)
    J = build_E(load_records(root), seal)
    say(render_pred(J, seal))
    say(u"")
    say(render_judge(J, seal))
    return J


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("moves", "regress97", "inject", "tally"))
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", default=None, help="この docID の本・書類だけ(--out が要る)")
    ap.add_argument("--procs", type=int, default=1)
    a = ap.parse_args(argv)
    if a.cmd == "moves":
        run_moves(root=a.root, procs=a.procs, only=a.only, out=a.out)
    elif a.cmd == "regress97":
        run_regress97(root=a.root, procs=a.procs, only=a.only, out=a.out)
    elif a.cmd == "inject":
        run_inject(root=a.root, procs=a.procs, only=a.only, out=a.out)
    else:
        run_tally(root=a.root)


if __name__ == "__main__":
    main()
