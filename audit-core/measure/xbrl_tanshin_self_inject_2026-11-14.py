# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TANSHIN_SELF_INJECT_SEAL_2026-11-14.md §0-2・§1・§2・§5 ― TSS の便 1b(注入)― 短信の概況の文に誤りを 1 件ずつ入れ、同じ短信の財務諸表に当てて止めるかを測る。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。engine(``core/``・``adapters/``)と ``measure/lib/`` は 1 行も変えない。**材料は TSS の置く script が置いた folder の ZIP を読むだけ(1 file も足さない)。
切り出し・包み直し・判定は TSS(``xbrl_tanshin_self_2026-11-14.py``)、丙の期の名前の読み替え・母集団の読みは第 2 便(``xbrl_tanshin_self2_2026-11-14.py``)、
注入の仕掛け(``inject_text_ts``)は 2026-11-09 の便(``xbrl_tanshin_2026-11-09.py``)の関数を **呼ぶ**(書き写さない)。

    python3 measure/xbrl_tanshin_self_inject_2026-11-14.py inject --out PATH [--material DIR] [--procs N]          # 切れた 372 本に T1・T5・T8・T9 を 1 件ずつ → fixtures/xbrl/tanshin_self/inject_2026-11-14.json
    python3 measure/xbrl_tanshin_self_inject_2026-11-14.py preview --nums 1,2,251 [--material DIR] [--procs N]       # 下見: 記録を書かず、指定した本の数だけ標準出力に出す
    python3 measure/xbrl_tanshin_self_inject_2026-11-14.py sheet --inject PATH --material DIR --sheet PATH           # 通した行を読む紙(repo の外。文・値を持つ)
    python3 measure/xbrl_tanshin_self_inject_2026-11-14.py types --inject PATH --typed PATH --out PATH               # 付けた札(a〜d)の file を確かめて inject_passed_types_2026-11-14.json を書く(通した行が 0 なら作らない)

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めはここに書き、報告にも書いた):
- 母集団(封 §1): 第 2 便の ``load_population`` を呼ぶ(TSS の記録の行と TSS の封の表が行ごとに同じでなければ止まる)。切れた本(TSS の判定で切り出せた本)が対象で、切れない本は数えるだけ。
- 土台の確かめ(封 §2 の 1): 本ごとに、無改変の文(A は元の ZIP・丙は期の名前を写した ZIP)を TSS の ``judge_book`` で判定した行の (文の番号, 位置, state) の並びが、記録(A は ``states_2026-11-14.json``・丙は ``states_interim_2026-11-14.json``)と同じでなければ止める(本の job の中で止める)。
- profile の対(封 §0-2 の 4): ``device()`` の ``with`` の中だけ ``TS.INJECT_PROFILES``・``TS.OLD``・``TS.NEW`` を P33E にする。``inject_text_ts``・``base_pair``・``t8_base_status`` が引く名前が届いていることを ``with`` の中で見て、届いていなければ止める。
  出たあとに ``with`` の前と同じ値に戻っていることも見て、戻っていなければ止める。2026-11-09 の便の ``wiring_problems()`` は対が (P30E, P32E) でないと問題と言うので ``with`` の外(前と後)で呼ぶ。
- refs(封 §0-2 の 5): 包んだ ZIP の fact を先頭から順に、value が None でなければ float にして(できなければ飛ばして数える)、key = 要素名 + "@" + context が既に採ったものなら飛ばす。
  float にできなかった fact は key を使った扱いにしない(同じ key の次の fact は採りうる)。unit は ``PM._money_unit_label(fact の unit)``。
- 「通した行」の読み(封 §0-2 の 9): 通した行は型を問わず(T9 も)読む。紙の番号は 本の # の順・行の記録の順に 1 から。札は ``a``〜``d``(a: engine が誤りを通した・b: 偶然ほかの正しい fact の値になった・c: 対応付けが別の claim を指した・d: 分けられない)。
- 記録は文・span・値・pointer の字・要素名・会社名・証券コード・docID を持たない。行の欄は 2026-11-09 の便の注入の記録と同じ欄の前に 本の #・群 を足したもの。時間(秒)は記録の中で 1 つの欄。ほかは 2 回走らせて byte で同じになる。
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
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    u"""importlib で読み込む。読み込んだ file が中で読む前の便の script は決まった名前で ``sys.modules`` に登録し直して先に居た module を上書きする。
    読み込みの前に居た名前は、読み込みの後に元の object へ戻す(自分の名前 ``mod_name`` は残す)。"""
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


S2 = load_module("xbrl_tanshin_self2_2026-11-14.py", "tanshin_self2_for_tanshin_self_inject")          # 第 2 便の script(母集団の読み・丙の期の名前の読み替え)
TSS = S2.TSS                                                                                             # 第 1 便の script(切り出し・包み直し・判定)
ST = TSS.ST                                                                                              # 置く script
TS = TSS.TS                                                                                              # 2026-11-09 の便(注入の仕掛け)
Stop = ST.Stop
TUNE = TS.TUNE

import prepare_material as PM                           # noqa: E402
from adapters.xbrl import verify_document as VD         # noqa: E402

SEAL_REL = "docs/XBRL_TANSHIN_SELF_INJECT_SEAL_2026-11-14.md"
SEAL_COMMIT = "bcc244ae"
SCRIPT_REL = "measure/xbrl_tanshin_self_inject_2026-11-14.py"
S2_SCRIPT_REL = S2.SCRIPT_REL
TSS_SCRIPT_REL = TSS.SCRIPT_REL
REC_DIR_REL = ST.REC_DIR_REL
INJECT_REL = REC_DIR_REL + "/inject_2026-11-14.json"
PASSED_TYPES_REL = REC_DIR_REL + "/inject_passed_types_2026-11-14.json"
DOC_REL = "docs/XBRL_TANSHIN_SELF_INJECT_RESULT_2026-11-14.md"
PRODUCTION_RELS = (INJECT_REL,)

# ---- 封 §0-2 の決めごと(字で留める。門が封と照らす)
PROFILE = "P33E"
SEED = 20261114                                         # 封 §0-2 の 7: 種は整数
CAP = 10                                                # 封 §0-2 の 7: 型ごと・1 本あたり
NAME_PREFIX = "B"                                       # 封 §0-2 の 7: 本の名前の引数は "B" + #
TYPES = TS.TYPES
TYPE_SHORT = TS.TYPE_SHORT
T1, T5, T8, T9 = TYPES
MAIN_TYPES = (T1, T5, T8)
R_VALUES = tuple(TUNE.T8_R_VALUES)
A_GROUPS = TSS.A_GROUPS
B_GROUPS = TSS.B_GROUPS
GROUP_NAMES = (u"A", u"丙")
LABEL_PASS = TUNE.LABEL_PASS
LABELS = (TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
STATES_REL = TSS.STATES_REL
INTERIM_REL = S2.INTERIM_REL
SHEET_WINDOW = (80, 60)                                 # 紙に出す文の前後の字数
#: 通した行の札(封 §0-2 の 9。字は封と同じ)
PASSED_LABELS = collections.OrderedDict([
    (u"a", u"engine が誤りを通した"),
    (u"b", u"注入した値が偶然ほかの正しい fact の値になった(誤りとは言えない)"),
    (u"c", u"対応付けが別の claim を指した"),
    (u"d", u"読んでも分けられない")])
TYPED_BY = TSS.TYPED_BY

INJECT_LIMITS = (
    u"標本は英文短信を出している会社の 250 本(通期)と 150 本(中間)のうち切れた 372 本。上場会社全体の率ではない。",
    u"注入の site は仕掛けが作れる場所だけ。数を丸めて書く本・仕掛けの数の読みが token にしない数は分母に入らない(覆いの欄)。",
    u"土台は engine が結べた数(GROUNDED)だけ。止まった数・「値が違う」と言った数に誤りを入れた場合は測っていない。",
    u"丙は期の名前を `measure/` の側で写した読みの上の数で、engine の読みそのものではない。",
    u"「通した」「止めた」は engine の state で、人の目の札は無い。通した行の札は司令塔(AI の席)1 席で、盲検ではない。",
    u"refs は包んだ ZIP の fact から作った(有報の便の道具とは別の作り)。同じ要素・同じ context の fact は最初の 1 件だけ。",
    u"誤りの型は 4 つ(T1・T5・T8・T9)だけ。単位の取り違え・符号・主語の取り違えは入れていない。",
)
#: 記録の「欄名の注記」(封 §6 の「限界」とは別の欄。限界の字は封のまま)
FIELD_NAME_NOTE = u"行の欄名の一部(P32E の土台に対応)と本ごとの数えの状態ラベル(P30E が GROUNDED…)は 2026-11-09 の便の名前のままで、実体は P33E(profile の対は (P33E, P33E))"


def pct(a, b):
    return TS.pct(a, b)


# ======================================================================================================
# profile の対・切り替え(封 §0-2 の 4・7)。with の中だけ。出るときは必ず戻す
def device_snapshot():
    u"""差し替える名前と切り替えの今の値。"""
    return collections.OrderedDict([
        (u"TS.INJECT_PROFILES", list(TS.INJECT_PROFILES)), (u"TS.OLD", TS.OLD), (u"TS.NEW", TS.NEW),
        (u"RM.INJECT_PROFILES", list(TS.RM.INJECT_PROFILES)),
        (u"切り替え " + TS.TY.FLAG, bool(getattr(TS.N, TS.TY.FLAG))), (u"切り替え " + TS.TY.FLAG2, bool(getattr(TS.S, TS.TY.FLAG2)))])


@contextlib.contextmanager
def profile_pair(name=PROFILE):
    u"""``inject_text_ts`` が引く ``INJECT_PROFILES``・``OLD``・``NEW`` を with の中だけ (name, name)・name・name にする。出るときは必ず戻す。"""
    old = (TS.INJECT_PROFILES, TS.OLD, TS.NEW)
    TS.INJECT_PROFILES = (name, name)
    TS.OLD = name
    TS.NEW = name
    try:
        yield
    finally:
        TS.INJECT_PROFILES, TS.OLD, TS.NEW = old


def reach_problems(name=PROFILE):
    u"""with の中で、仕掛けが引く名前が name に届いているか(届いていない所の文の一覧)。"""
    out = []
    g = TS.inject_text_ts.__globals__
    if tuple(g["INJECT_PROFILES"]) != (name, name):
        out.append(u"inject_text_ts が引く INJECT_PROFILES が (%s, %s) でない" % (name, name))
    if g["OLD"] != name or g["NEW"] != name:
        out.append(u"inject_text_ts が引く OLD・NEW が %s でない" % name)
    with TS.base_pair():
        if tuple(TS.RM.INJECT_PROFILES) != (name, name):
            out.append(u"base_pair の中の RM.INJECT_PROFILES が (%s, %s) でない" % (name, name))
    with TS.t8_base_status():
        if TS.RUN.t8_candidates4.__globals__["base_status4"] is not TS.base_status_ts:
            out.append(u"t8_candidates4 が引く base_status4 が base_status_ts でない")
    if not getattr(TS.N, TS.TY.FLAG) or not getattr(TS.S, TS.TY.FLAG2):
        out.append(u"切り替えが偽")
    return out


@contextlib.contextmanager
def device(name=PROFILE):
    u"""profile の対の差し替えと切り替え 2 つ 真の with。(配線の記録 OrderedDict)を yield する。届いていなければ止める。出たあとの値と戻ったかは出たあとに記録へ足す(戻っていなければ止める)。"""
    before = device_snapshot()
    if before[u"切り替え " + TS.TY.FLAG] or before[u"切り替え " + TS.TY.FLAG2]:
        raise Stop(u"**切り替えが真のまま始めた。止める**")
    bad = TS.wiring_problems()
    if bad:
        raise Stop(u"**差し替えが届いていない(with の外): %s。止める**" % u" / ".join(bad))
    wiring = collections.OrderedDict()
    wiring[u"with の前"] = before
    with profile_pair(name):
        with TS.NS.yen_scan_on():
            with TS.TY.t5_yen_on():
                inside = device_snapshot()
                problems = reach_problems(name)
                wiring[u"with の中"] = inside
                wiring[u"with の中の届き方の問題"] = problems
                if problems:
                    raise Stop(u"**差し替えが届いていない(with の中): %s。止める**" % u" / ".join(problems))
                yield wiring
    after = device_snapshot()
    wiring[u"with の後"] = after
    wiring[u"元に戻った"] = bool(after == before)
    wiring[u"2026-11-09 の便の wiring_problems(with の外・前と後)"] = list(TS.wiring_problems())
    if after != before:
        raise Stop(u"**with を出ても元に戻っていない。止める**")
    if wiring[u"2026-11-09 の便の wiring_problems(with の外・前と後)"]:
        raise Stop(u"**with を出たあとの配線の問題。止める**")


# ======================================================================================================
# refs(封 §0-2 の 5)
def refs_from_facts(facts):
    u"""(refs, 飛ばした数)。facts を先頭から順に、value が None は飛ばす(数えない)・float にできなければ飛ばして数える・同じ key は最初の 1 件だけ。"""
    refs, seen, skipped = [], set(), 0
    for f in facts:
        if f.get("value") is None:
            continue
        try:
            value = float(f["value"])
        except (TypeError, ValueError, OverflowError):
            skipped += 1
            continue
        el = f["name"].split(u":")[-1]
        key = u"%s@%s" % (el, f["context"])
        if key in seen:
            continue
        seen.add(key)
        refs.append({"key": key, "source_key": el, "label": el, "unit": PM._money_unit_label(f.get("unit")), "value": value, "role": "value", "context": f["context"]})
    return refs, skipped


# ======================================================================================================
# 1 本の注入(封 §0-2 の 2〜7)
def site_total(v):
    return sum(v.values()) if isinstance(v, dict) else (v or 0)


def book_name(n):
    return u"%s%d" % (NAME_PREFIX, n)


def inject_book(n, grp, kind, sha, zb, ref_triples=None, capture=None):
    u"""1 本の結果(OrderedDict)。``with device()`` の中で呼ぶ。切れない本は行 0。
    ``ref_triples`` が在れば(記録の行 [文の番号, 位置, state])、無改変の文の判定が行ごとに同じでなければ止める。``capture`` を渡せば (refs・文・注入の中身・token) を入れる(紙用)。"""
    zb2, _hit, _counts = S2.prepare(zb, grp in B_GROUPS)
    book = TSS.judge_book(n, grp, kind, sha, zb2)
    out = collections.OrderedDict([(u"#", n), (u"群", grp), (u"名前", book_name(n)), (u"切り出し", book[u"切り出し"] == TSS.CUT_OK)])
    if not out[u"切り出し"]:
        if ref_triples is not None:
            raise Stop(u"**記録では切れた本が、作り直した判定では切れない(# %d)。止める**" % n)
        out.update([(u"GROUNDED の行", 0), (u"refs の数", 0), (u"refs で飛ばした fact", 0), (u"行", []), (u"数え", None), (u"土台の行", 0)])
        return out
    triples = [(r[0], r[1], r[2]) for r in book[u"行"]]
    if ref_triples is not None and triples != [tuple(t) for t in ref_triples]:
        raise Stop(u"**無改変の文の判定が記録と違う(# %d)。止める**" % n)
    text, _h, _why = TSS.cut(zb2)
    wrapped, _nf = TSS.wrap(zb2, text)
    refs, skipped = refs_from_facts(TSS.I.load_instance(wrapped)["facts"])

    def verify(_z, p, t):
        return VD.verify_document(TSS.wrap(zb2, t)[0], p)

    if tuple(TS.INJECT_PROFILES) != (PROFILE, PROFILE) or not getattr(TS.N, TS.TY.FLAG) or not getattr(TS.S, TS.TY.FLAG2):
        raise Stop(u"**差し替え・切り替えが届いていない本の job。止める**")
    original = TS.build_row
    if capture is not None:
        def recording(zb_, text_, verify_, base_claims, base_by_id, typ, inj, tok, bc, extra):
            row = original(zb_, text_, verify_, base_claims, base_by_id, typ, inj, tok, bc, extra)
            capture.setdefault("items", {})[row["id"]] = (inj, tok)
            return row
        TS.build_row = recording
    try:
        rows, counts = TS.inject_text_ts(wrapped, text, refs, SEED, book_name(n), cap=CAP, verify=verify)
    finally:
        TS.build_row = original
    if capture is not None:
        capture["refs"], capture["text"] = refs, text
    out[u"GROUNDED の行"] = sum(1 for t in triples if t[2] == TS.G)
    out[u"土台の行"] = len(triples)
    out[u"refs の数"] = len(refs)
    out[u"refs で飛ばした fact"] = skipped
    out[u"行"] = [collections.OrderedDict([(u"本の #", n), (u"群", grp)] + list(r.items())) for r in rows]
    out[u"数え"] = counts
    return out


def job(args):
    n, grp, kind, sha, path, ref_triples = args
    zb = S2.read_material(n, sha, path)
    return inject_book(n, grp, kind, sha, zb, ref_triples)


# ======================================================================================================
# 母集団・土台の記録
def load_bases(root, pop):
    u"""{#: 記録の本}。A は TSS の判定の記録・丙は第 2 便の interim の記録。本の ZIP の sha256 が母集団と違えば止める。"""
    out = dict(S2.load_tss_states(root, pop))
    irec = TSS.load_json(os.path.join(root, INTERIM_REL))
    ibooks = dict((b[u"#"], b) for b in irec[u"本"])
    shas = dict((r[0], r[3]) for r in pop)
    if sorted(ibooks) != [r[0] for r in pop if r[1] in B_GROUPS] or any(ibooks[k][u"ZIP の sha256"] != shas[k] for k in ibooks):
        raise Stop(u"**interim の記録の本が母集団の丙と合わない。止める**")
    for k, b in ibooks.items():
        out[k] = b
    return out


def selection(pop, bases, nums=None):
    u"""(対象の行 [(n, g, kind, sha, 記録の行)], 切れない本の数)。nums が在ればその本だけ(下見)。対象 = 記録で切れた本。"""
    rows = [r for r in pop if nums is None or r[0] in nums]
    if nums is not None and sorted(nums) != [r[0] for r in rows]:
        raise Stop(u"**指定した本の # が母集団に無い。止める**")
    cut = [r for r in rows if bases[r[0]][u"切り出し"] == TSS.CUT_OK]
    return [(r[0], r[1], r[2], r[3], [t[:3] for t in bases[r[0]][u"行"]]) for r in cut], len(rows) - len(cut)


def material_dir(material, out, root=ROOT):
    u"""材料の置き場。既定は本番の folder。本番の記録を書くときは本番の folder でなければ止める。"""
    prod = os.path.abspath(ST.default_cache_dir())
    mat = os.path.abspath(material) if material else prod
    if out is not None and os.path.abspath(out) in [os.path.abspath(os.path.join(root, rel)) for rel in PRODUCTION_RELS] and mat != prod:
        raise Stop(u"**本番の記録を使い捨ての材料から作らない。止める**")
    return mat, mat == prod


def check_clean(rec, text, key_value=None):
    u"""記録に repo へ入れない欄・鍵らしい字が無いか(あれば止める)。3 つの封の path は長い英数字なので外して見る。"""
    bad = sorted(set(k for k in TS.RUN.walk_keys(rec) if k in TS.RUN.FORBIDDEN_KEYS))
    if bad:
        raise Stop(u"**記録に repo へ入れない欄がある: %s。止める**" % u",".join(bad))
    leaks = ST.key_leaks(text.replace(SEAL_REL, u"").replace(S2.SEAL_REL, u"").replace(TSS.SEAL_REL, u""), key_value)
    if leaks:
        raise Stop(u"**鍵らしい字が記録に在る(%s)。書かずに止める**" % u" / ".join(sorted(set(leaks))))


def jobs_of(sel, mat):
    return [(n, g, k, sha, os.path.join(mat, sha + u".zip"), tr) for (n, g, k, sha, tr) in sel]


def need_material(sel, mat):
    for (n, _g, _k, sha, _t) in sel:
        if not os.path.exists(os.path.join(mat, sha + u".zip")):
            raise Stop(u"**材料の ZIP が置き場に無い(# %d)。何も書かずに止める(置く script を先に)**" % n)


# ======================================================================================================
# 集計(行から数える)
def group_name(grp):
    return u"A" if grp in A_GROUPS else u"丙"


def type_block(rows):
    u"""1 群・1 型の行の集計。通した率(分母 = 注入の行)と届いた率(分母 = 対応が付いた行)を別の欄にする。"""
    n = len(rows)
    c = collections.Counter(r[PROFILE][u"結果"] for r in rows)
    linked = [r for r in rows if r[PROFILE][u"対応"]]
    reached = [r for r in linked if r[u"届いた"]]
    passed = [r for r in rows if r[PROFILE][u"結果"] == LABEL_PASS]
    out = collections.OrderedDict([(u"注入の行", n)])
    out[u"結果の語"] = collections.OrderedDict((w, collections.OrderedDict([(u"件", c.get(w, 0)), (u"率", pct(c.get(w, 0), n))])) for w in LABELS)
    out[u"対応が付いた行"] = len(linked)
    out[u"届いた"] = collections.OrderedDict([(u"件", len(reached)), (u"率(分母は対応が付いた行)", pct(len(reached), len(linked)))])
    out[u"通した"] = collections.OrderedDict([(u"件", len(passed)), (u"率", pct(len(passed), n)),
                                           (u"うち届いた", sum(1 for r in passed if r[u"届いた"])), (u"うち届いていない", sum(1 for r in passed if not r[u"届いた"]))])
    out[u"round-trip 不一致"] = sum(1 for r in rows if not r[u"round-trip"])
    out[u"読み直し不一致"] = sum(1 for r in rows if not r[u"読み直し"])
    return out


def summary(rows):
    u"""群(A・丙)× 型。T9 は参考(率は結果の文書で言わない)。"""
    out = collections.OrderedDict()
    for g in GROUP_NAMES:
        sel = [r for r in rows if group_name(r[u"群"]) == g]
        out[g] = collections.OrderedDict((t, type_block([r for r in sel if r[u"型"] == t])) for t in TYPES)
    return out


def coverage(books):
    u"""覆い(封 §2 の 4)。本ごとの欄と群ごとの集計。``books`` は inject_book の結果(切れた本)。"""
    per = []
    for b in books:
        counts = b[u"数え"] or collections.OrderedDict()
        t8 = counts.get(T8) or {}
        per.append(collections.OrderedDict([
            (u"#", b[u"#"]), (u"群", b[u"群"]), (u"名前", b[u"名前"]), (u"P33E が GROUNDED の行", b[u"GROUNDED の行"]), (u"円族の token", t8.get(u"円族の token")),
            (u"作れる site", collections.OrderedDict((TYPE_SHORT[t], site_total((counts.get(t) or {}).get(u"作れる site"))) for t in TYPES)),
            (u"注入の行", collections.OrderedDict((TYPE_SHORT[t], sum(1 for r in b[u"行"] if r[u"型"] == t)) for t in TYPES)),
            (u"refs の数", b[u"refs の数"]), (u"refs で飛ばした fact", b[u"refs で飛ばした fact"]),
            (u"全角の数字で注入しない", bool(counts.get(u"注入しない")))]))
    grp = collections.OrderedDict()
    for g in GROUP_NAMES:
        sel = [p for p in per if group_name(p[u"群"]) == g]
        g1 = [p for p in sel if p[u"P33E が GROUNDED の行"] >= 1]
        inj = [p for p in sel if sum(p[u"注入の行"].values()) >= 1]
        inj_g1 = [p for p in g1 if sum(p[u"注入の行"].values()) >= 1]
        grp[g] = collections.OrderedDict([
            (u"切れた本", len(sel)), (u"P33E が GROUNDED の行の合計", sum(p[u"P33E が GROUNDED の行"] for p in sel)), (u"円族の token の合計", sum(p[u"円族の token"] or 0 for p in sel)),
            (u"GROUNDED が 1 行以上の本", len(g1)), (u"注入の行が 1 行以上の本", len(inj)),
            (u"注入の行が 1 行以上の本(分母は GROUNDED が 1 行以上の本)", collections.OrderedDict([(u"件", len(inj_g1)), (u"率", pct(len(inj_g1), len(g1)))])),
            (u"全角の数字で注入しない本", sum(1 for p in sel if p[u"全角の数字で注入しない"])),
            (u"作れる site の合計", collections.OrderedDict((TYPE_SHORT[t], sum(p[u"作れる site"][TYPE_SHORT[t]] for p in sel)) for t in TYPES)),
            (u"注入の行の合計", collections.OrderedDict((TYPE_SHORT[t], sum(p[u"注入の行"][TYPE_SHORT[t]] for p in sel)) for t in TYPES)),
            (u"型ごとに注入の行が 1 行以上の本", collections.OrderedDict((TYPE_SHORT[t], sum(1 for p in sel if p[u"注入の行"][TYPE_SHORT[t]] >= 1)) for t in TYPES)),
            (u"作れる site が 0 の本", collections.OrderedDict((TYPE_SHORT[t], sum(1 for p in sel if p[u"作れる site"][TYPE_SHORT[t]] == 0)) for t in TYPES)),
            (u"refs で飛ばした fact の合計", sum(p[u"refs で飛ばした fact"] for p in sel))])
    return per, grp


def columns_of(rows):
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    return cols


# ======================================================================================================
# preview(下見。記録を書かない)
def run_preview(nums, root=ROOT, procs=1, material=None, say=print, population=None, bases=None):
    u"""指定した本だけに注入し、数だけ標準出力に出す。記録も紙も書かない。(books, rows)を返す。"""
    mat, _prod = material_dir(material, None, root)
    pop = population if population is not None else S2.load_population(root)
    bases = bases if bases is not None else load_bases(root, pop)
    sel, uncut = selection(pop, bases, set(nums))
    need_material(sel, mat)
    say(u"preview 本 %d(切れた %d・切れない %d)× %s ― procs %d" % (len(nums), len(sel), uncut, PROFILE, procs))
    t0 = time.time()
    with device():
        books = TS.NF.map_pool(job, jobs_of(sel, mat), procs)
    rows = [r for b in books for r in b[u"行"]]
    for b in books:
        say(u"  # %d %s 行 %d" % (b[u"#"], b[u"群"], len(b[u"行"])))
    for t in TYPES:
        sel_t = [r for r in rows if r[u"型"] == t]
        c = collections.Counter(r[PROFILE][u"結果"] for r in sel_t)
        say(u"%s 行 %d 届いた %d  %s" % (TYPE_SHORT[t], len(sel_t), sum(1 for r in sel_t if r[u"届いた"]), json.dumps(dict((w, c[w]) for w in LABELS if c.get(w)), ensure_ascii=False, sort_keys=True)))
    say(u"注入の行が 1 行以上の本 %d / 切れた本 %d(%.0f 秒)" % (sum(1 for b in books if b[u"行"]), len(books), time.time() - t0))
    return books, rows


# ======================================================================================================
# inject(本番の記録)
def head_fields(rec, root, mat, prod, pop, before, after):
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"TSS 便 1b(注入)― 短信の概況の文に T1・T5・T8・T9 を 1 件ずつ入れ、同じ短信の財務諸表に当てる(P33E・切り替え 2 つ 真・0 USD・通信なし)"
    rec[u"HEAD の commit"] = ST.git_head(root)
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"第 2 便の script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(S2_SCRIPT_REL)))
    rec[u"TSS の script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(TSS_SCRIPT_REL)))
    rec[u"置く script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(TSS.STAGE_SCRIPT_REL)))
    rec[u"2026-11-09 の便の script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(TSS.TS_SCRIPT_REL)))
    rec[u"仕掛けの 2 file の sha256"] = collections.OrderedDict((rel, ST.sha256_file(os.path.join(root, rel))) for rel in TS.DEVICE_RELS)
    rec[u"lib の指紋"] = collections.OrderedDict((rel, ST.sha256_file(os.path.join(root, rel))) for rel in TS.LIB_RELS)
    rec[u"engine の指紋"] = VD.engine_fingerprint()
    rec[u"母集団の記録の sha256"] = ST.sha256_file(os.path.join(root, ST.POPULATION_REL))
    rec[u"TSS の判定の記録の sha256"] = ST.sha256_file(os.path.join(root, STATES_REL))
    rec[u"interim の記録の sha256"] = ST.sha256_file(os.path.join(root, INTERIM_REL))
    rec[u"profile"] = PROFILE
    rec[u"材料"] = collections.OrderedDict([
        (u"置き場", ST.display_path(mat) if prod else u"使い捨ての置き場(本番の folder ではない)"), (u"表と一致した ZIP", len(pop)),
        (u"置き場の一覧の前後", collections.OrderedDict([(u"前", list(before)), (u"後", list(after)), (u"変化なし", before == after)]))])


def run_inject(root=ROOT, procs=1, out=None, material=None, say=print, population=None, bases=None, key_value=None, clock=time.time):
    if out is None:
        raise Stop(u"**--out を指定する。止める**")
    out = os.path.abspath(out)
    mat, prod = material_dir(material, out, root)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    pop = population if population is not None else S2.load_population(root)
    bases = bases if bases is not None else load_bases(root, pop)
    sel, uncut = selection(pop, bases)
    need_material(sel, mat)
    before = ST.names_snapshot(mat)
    say(u"inject 切れた %d 本(切れない %d)× 4 型 × %s ― 種 %d・cap %d・procs %d(1 件ごとに判定。時間がかかる)" % (len(sel), uncut, PROFILE, SEED, CAP, procs))
    t0 = clock()
    with device() as wiring:
        books = TS.NF.map_pool(job, jobs_of(sel, mat), procs)
    elapsed = clock() - t0
    after = ST.names_snapshot(mat)
    if before != after:
        raise Stop(u"**材料の置き場の件数か名前が変わった。記録を書かずに止める**")
    rows = [r for b in books for r in b[u"行"]]
    per, grp = coverage(books)
    rec = collections.OrderedDict()
    head_fields(rec, root, mat, prod, pop, before, after)
    rec[u"配線"] = wiring
    rec[u"切り替え"] = collections.OrderedDict([
        (u"名前", TS.TY.FLAG), (u"inject の中の値", wiring[u"with の中"][u"切り替え " + TS.TY.FLAG]), (u"出たあとの値", wiring[u"with の後"][u"切り替え " + TS.TY.FLAG]),
        (u"T5 の切り替えの名前", TS.TY.FLAG2), (u"T5 の切り替え inject の中の値", wiring[u"with の中"][u"切り替え " + TS.TY.FLAG2]), (u"T5 の切り替え 出たあとの値", wiring[u"with の後"][u"切り替え " + TS.TY.FLAG2])])
    rec[u"種"] = SEED
    rec[u"cap"] = CAP
    rec[u"型"] = collections.OrderedDict([
        (T1, u"inject.select(types=[T1_VALUE])。cap は採用に掛ける(2026-11-09 の便の inject_text_ts のまま)"),
        (T5, u"土台が GROUNDED の site を先頭から cap 件(inject_text_ts のまま。切り替え 2 つ 真)"),
        (T8, u"t8_candidates4(円族の token・r ∈ %s・%d 回まで)。cap は site に掛ける(inject_text_ts のまま)" % (list(R_VALUES), TUNE.T8_TRIES)),
        (T9, u"T9 の第 2 便と同じ site・並べ替え・cap(参考。率は言わず数だけ並べる)"),
        (u"上限", u"型ごと・1 本あたり %d" % CAP), (u"本の名前の引数", u"%s + 本の #(例 %s)" % (NAME_PREFIX, book_name(7))),
        (u"土台", u"無改変の文(包み直した ZIP。丙は期の名前を写した ZIP)で P33E が GROUNDED の claim。profile の対は (P33E, P33E)"),
        (u"検証", u"注入後の文で包み直した ZIP に verify_document(P33E)。inject_text_ts の第 1 引数は無改変の文で包んだ ZIP")])
    rec[u"refs の作り"] = collections.OrderedDict([
        (u"元", u"包んだ ZIP(無改変の文)を load_instance で読んだ facts を先頭から順に"), (u"key", u"要素名の最後の : の後ろ + @ + context。同じ key は最初の 1 件だけ"),
        (u"飛ばす", u"value が None(数えない)・float にできない(数える。key は使った扱いにしない)"), (u"unit", u"prepare_material._money_unit_label"),
        (u"飛ばした fact の合計", sum(b[u"refs で飛ばした fact"] for b in books))])
    rec[u"母集団"] = collections.OrderedDict([(u"対象の本(切れた本)", len(sel)), (u"切れない本", uncut), (u"A", sum(1 for b in books if group_name(b[u"群"]) == u"A")), (u"丙", sum(1 for b in books if group_name(b[u"群"]) == u"丙"))])
    rec[u"土台の確かめ"] = collections.OrderedDict([
        (u"本", len(books)), (u"行", sum(b[u"土台の行"] for b in books)), (u"違う本", 0),
        (u"比べた記録", u"A は states_2026-11-14.json・丙は states_interim_2026-11-14.json。(文の番号, 位置, state) の並びが本ごとに同じ(違えば本の job で止まる)")])
    rec[u"本ごとの数え"] = collections.OrderedDict((b[u"名前"], b[u"数え"]) for b in books)
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"] = summary(rows)
    rec[u"覆い"] = collections.OrderedDict([(u"群ごと", grp), (u"本ごと", per)])
    rec[u"限界"] = list(INJECT_LIMITS)
    rec[u"欄名の注記"] = FIELD_NAME_NOTE
    rec[u"行の欄"] = columns_of(rows)
    rec[u"時間(秒)"] = round(elapsed, 1)
    rec[u"key_leaks"] = []
    rec[u"行"] = rows
    text = ST.dumps_record(rec)
    check_clean(rec, text, key_value)
    ST.write_text_exclusive(out, text)
    say(u"-> %s(注入の行 %d)" % (os.path.basename(out), len(rows)))
    return rec


# ======================================================================================================
# 通した行の紙・札(封 §0-2 の 9)
def passed_items(rec):
    u"""[(番号(1 から), 本の #, 行)]。本の # の順・記録の行の順。通した = P33E の結果が 通した。"""
    sel = [r for r in rec[u"行"] if r[PROFILE][u"結果"] == LABEL_PASS]
    return [(i + 1, r[u"本の #"], r) for i, r in enumerate(sel)]


def sheet_block(num, row, cap, text, tampered_window):
    inj, tok = cap["items"][row[u"id"]]
    target = TS.SC.scaled_value(inj["new_value"], tok.unit)
    same = [r["key"] for r in cap["refs"] if r["value"] == target][:5]
    s0, a = max(0, tok.start - SHEET_WINDOW[0]), tok.end + SHEET_WINDOW[1]
    return u"\n".join([
        u"=== 番号 %d / 本 # %d / id %s / 型 %s ===" % (num, row[u"本の #"], row[u"id"], row[u"型"]),
        u"原文(前後): %s" % text[s0:a].replace(u"\n", u" "),
        u"注入後(前後): %s" % tampered_window.replace(u"\n", u" "),
        u"元の字 → 差し替えの字: %s → %s  単位: %s  注入した値: %s" % (text[tok.start:tok.end], inj["replacement"], tok.unit, inj["new_value"]),
        u"結果: %s  state: %s  reason: %s  届いた: %s" % (row[PROFILE][u"結果"], row[PROFILE][u"state"], row[PROFILE][u"reason"], row[u"届いた"]),
        u"基準の claim: %s  pointer の期(注入後): %s" % (row[u"基準の claim"], row[PROFILE + u" の注入後の pointer の期"]),
        u"注入した値と同じ値の fact(最大 5): %s" % (u" , ".join(same) if same else u"なし"), u"", u""])


def run_sheet(inject_path, material, sheet, root=ROOT, say=print, repo=None, population=None, bases=None):
    if TSS.inside_repo(sheet, repo):
        raise Stop(u"**--sheet が repo の中(または git の木の中)。文を持つ紙は repo の外に書く。止める**")
    sheet = os.path.abspath(sheet)
    if os.path.exists(sheet):
        raise Stop(u"**--sheet が既に在る。止める**")
    rec = TSS.load_json(inject_path)
    items = passed_items(rec)
    if not items:
        say(u"通した行 0。紙は作らない")
        return items
    pop = population if population is not None else S2.load_population(root)
    bases = bases if bases is not None else load_bases(root, pop)
    prow = dict((r[0], r) for r in pop)
    mat = os.path.abspath(material)
    chunks = {}
    by_book = collections.OrderedDict()
    for it in items:
        by_book.setdefault(it[1], []).append(it)
    with device():
        for num, its in by_book.items():
            _n, grp, kind, sha = prow[num]
            zb = S2.read_material(num, sha, os.path.join(mat, sha + u".zip"))
            cap = {}
            b = inject_book(num, grp, kind, sha, zb, [t[:3] for t in bases[num][u"行"]], capture=cap)
            now = dict((r[u"id"], r) for r in b[u"行"])
            for (k, _n2, row) in its:
                r2 = now.get(row[u"id"])
                if r2 is None or r2[PROFILE][u"結果"] != LABEL_PASS:
                    raise Stop(u"**通した行を作り直せない(番号 %d)。記録と合わない。止める**" % k)
                inj, tok = cap["items"][row[u"id"]]
                tampered, _pl = TS.IJ.apply_edits(cap["text"], [inj])
                s0, e = max(0, tok.start - SHEET_WINDOW[0]), tok.end + SHEET_WINDOW[1] + len(inj["replacement"]) - (tok.end - tok.start)
                chunks[k] = sheet_block(k, row, cap, cap["text"], tampered[s0:e])
    d = os.path.dirname(sheet)
    if d:
        os.makedirs(d, exist_ok=True)
    with io.open(sheet, "w", encoding="utf-8", newline="") as fh:
        fh.write(u"".join(chunks[it[0]] + u"\n" for it in items))
    say(u"通した行 %d・本 %d" % (len(items), len(by_book)))
    return items


def read_typed(path):
    u"""1 行に「番号 TAB 札(a〜d)」。{番号: 札}。形が違う・番号が重なる・札が 4 つの外なら止める。"""
    out = {}
    with io.open(path, encoding="utf-8") as fh:
        for ln in fh.read().split(u"\n"):
            if not ln.strip():
                continue
            parts = ln.rstrip(u"\r").split(u"\t")
            if len(parts) != 2 or not re.fullmatch(r"[0-9]+", parts[0]) or parts[1] not in PASSED_LABELS:
                raise Stop(u"**札の file の行が「番号 TAB 札(a〜d)」でない。止める**")
            k = int(parts[0])
            if k in out:
                raise Stop(u"**札の file に同じ番号が 2 行ある。止める**")
            out[k] = parts[1]
    return out


def run_types(inject_path, typed_path, out, root=ROOT, say=print, key_value=None):
    out = os.path.abspath(out)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。止める**" % os.path.basename(out))
    rec_in = TSS.load_json(inject_path)
    items = passed_items(rec_in)
    if not items:
        say(u"通した行 0。札の file は作らない")
        return None
    typed = read_typed(typed_path)
    if sorted(typed) != [it[0] for it in items]:
        raise Stop(u"**札の file の番号が通した行(%d 行)とそろわない。止める**" % len(items))
    counts = collections.Counter(typed.values())
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"TSS 便 1b(注入)― 通した行を読んだ札(0 USD)"
    rec[u"HEAD の commit"] = ST.git_head(root)
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"inject の記録の sha256"] = ST.sha256_file(os.path.abspath(inject_path))
    rec[u"札を付けた席"] = TYPED_BY
    rec[u"盲検"] = u"盲検ではない(封の予測を知ったうえで付けた)"
    rec[u"読む行の規則"] = collections.OrderedDict([(u"母集団", u"inject の記録の行のうち P33E の結果が 通した の行(型を問わず)を、記録の行の順に"), (u"通した行の数", len(items))])
    rec[u"札の字"] = collections.OrderedDict(PASSED_LABELS)
    rec[u"札の集計"] = collections.OrderedDict((t, counts.get(t, 0)) for t in PASSED_LABELS)
    rec[u"行の欄"] = [u"番号", u"本の #", u"id", u"型", u"札"]
    rec[u"行"] = [[k, num, row[u"id"], row[u"型"], typed[k]] for (k, num, row) in items]
    rec[u"key_leaks"] = []
    text = ST.dumps_record(rec)
    check_clean(rec, text, key_value)
    ST.write_text_exclusive(out, text)
    say(u"-> %s(読んだ行 %d)" % (os.path.basename(out), len(items)))
    return rec


def parse_nums(s):
    out = []
    for part in s.split(u","):
        if not re.fullmatch(r"[0-9]+", part.strip()):
            raise Stop(u"**--nums は 1,2,3 の形で指定する。止める**")
        out.append(int(part))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("inject")
    a.add_argument("--root", default=ROOT)
    a.add_argument("--out", required=True)
    a.add_argument("--material", default=None)
    a.add_argument("--procs", type=int, default=1)
    p = sub.add_parser("preview")
    p.add_argument("--root", default=ROOT)
    p.add_argument("--nums", required=True)
    p.add_argument("--material", default=None)
    p.add_argument("--procs", type=int, default=1)
    s = sub.add_parser("sheet")
    s.add_argument("--root", default=ROOT)
    s.add_argument("--inject", required=True)
    s.add_argument("--material", required=True)
    s.add_argument("--sheet", required=True)
    t = sub.add_parser("types")
    t.add_argument("--root", default=ROOT)
    t.add_argument("--inject", required=True)
    t.add_argument("--typed", required=True)
    t.add_argument("--out", required=True)
    a_ = ap.parse_args(argv)
    if a_.cmd == "inject":
        run_inject(root=a_.root, procs=a_.procs, out=a_.out, material=a_.material)
    elif a_.cmd == "preview":
        run_preview(parse_nums(a_.nums), root=a_.root, procs=a_.procs, material=a_.material)
    elif a_.cmd == "sheet":
        run_sheet(a_.inject, a_.material, a_.sheet, root=a_.root)
    elif a_.cmd == "types":
        run_types(a_.inject, a_.typed, a_.out, root=a_.root)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
