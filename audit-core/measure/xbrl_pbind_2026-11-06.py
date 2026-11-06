# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md §3・§4・§5(追記 1 を含む)― PB(前期の手がかりがある数を当期の fact に落とさない。P32E = P30E + 旗)の測定と、結果の表(tally)。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。** 測る側から engine(``core/``・``adapters/``)・``measure/lib``・``measure/inject.py``・前の便の script・記録・門は 1 行も変えない。

    python3 measure/xbrl_pbind_2026-11-06.py moves     [--procs N] [--only <docID>] [--out PATH]   # AI の文 200 本で P30E → P32E の動いた行 → fixtures/xbrl/pbind/moves_200_2026-11-06.json
    python3 measure/xbrl_pbind_2026-11-06.py regress97 [--procs N] [--only <docID>] [--out PATH]   # 手元の 97 書類の原文での退行・動いた行・engine の差分 → fixtures/xbrl/pbind/regress97_2026-11-06.json
    python3 measure/xbrl_pbind_2026-11-06.py inject    [--procs N] [--only <docID>] [--out PATH]   # T9 の id の対応付けの注入を P30E・P32E で → fixtures/xbrl/pbind/inject_2026-11-06.json
    python3 measure/xbrl_pbind_2026-11-06.py tally     [--root DIR]                                 # 記録 3 つ(と T9 の第 2 便の記録)から E-1〜E-10 と K-1〜K-5 の表を出す(file は書かない)

``--only`` を付けた走らせ方は本番の記録ではない: ``--out`` を必ず指定する(指定が無ければ止める)。
RB の便の script ``xbrl_rmix_2026-11-04.py``(RM)・``xbrl_rmix_regress97_2026-11-04.py``(RR)と T9 の第 2 便の script ``xbrl_pswap_idmap_2026-11-06.py``(PI)は **1 byte も変えず**、
importlib で読み込んで使う(写さない)。RM の ``load_jobs``・``id_map``・``label_of``・``RUN.judge_text``、RR の ``XR``(``doc_job``・``doc_rows``・``engine_commits``・``engine_link``。
差し替える先は XR の module の属性)、PI の ``PS``(``t9_all_sites``・``build_t9``・``engine_cue``・``has_prior_word``・``pointer_period``・``shape_of_token``)・``id_map``・
``yen_scan_on``・``load_books`` をそのまま呼ぶ。この script が自分で持つのは、profile の対(P30E → P32E)・期の語 5 つ(Prior2Year を分ける)・前期の fact の有無・
行の欄・集計・封の字から幅を読む tally だけ。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めは結果の報告に書いた):
- 200 本の「動いた行」(E-4)= 両方の profile に在る数の claim(鍵 = (文の番号, 位置))のうち **state か pointers が違う行**(封 E-4 の字。reason だけが違う行は別に数える)。
- 97 書類の E-3 の「動いた行」・「動いた書類」と E-10 の「VALUE_MISMATCH に動いた行」は、封 §0-1 の 3 の数(動いた行 19 = UNVERIFIABLE → VALUE_MISMATCH 12・POINTER_NOT_FOUND → VALUE_MISMATCH 6・
  UNVERIFIABLE → POINTER_NOT_FOUND 1。state が変わった行だけを数えた値)と同じ量として、**state が変わった行**で判定する(封の字に定義が無いので封に無い決め)。E-10 は state が変わって VALUE_MISMATCH になった行の期。
  state か pointers が違う行(pointers だけが違う行を足したもの)・state は VALUE_MISMATCH のまま pointer の期が動いた行・XR の定義(state・reason・pointers のどれか)の行は記録の別の欄に残し、判定に使わない。
- 「既存の行」= P27 にも同じ鍵がある行(``RM.id_map`` が結んだ鍵)。札は前の便の盲検の 1 席目(``RM.label_of``)。新しい行には札が無い。
- pointer の期は pointers の先頭の context の先頭の語: CurrentYear / Prior1Year / Prior2Year / 他 / なし(T9 の ``pointer_period`` は Prior2Year を 他 に畳むので、E-10 の追記 1 の 4 のためにこの script が 5 つに分ける)。
- 「前期の fact が無い要素」(追記 1 の 1)= P32E の claim の先頭の pointer が xbrl の fact を指し、その要素に context が Prior1Year で始まる JPY の fact が書類に無い。行の欄は真偽だけ。
  pointers が空・xbrl でない行は偽(要素が分からないので『無い』と言わない)。
- E-7・E-9 は engine の commit の message の字を読んで写す(この木で変異を走らせ直さない。司令塔が許した決め)。E-7 は『変異 N 本全部赤』が封 §2-1 の変異の本数以上なら封の本数が全部赤、
  E-9 は『赤は <試験> の M 本だけ(pytest M failed / P passed / S skipped、unittest failures=U)』を読む。message に無ければ None = 外れ。
- 手がかりの欄は 2 つ: ``engine の手がかり``(T9 の ``recipes._prior_cue``。封 E-5 の『手がかり真 129 行』はこちら)と ``窓の手がかり``(PB の ``_prior_cue_window_2026_11_06``)。E-5 は前者で分ける。
- E-5 の三つ組: 当期の fact に GROUNDED = state が GROUNDED で注入後の pointer の期が CurrentYear / 前期の fact を名指して VALUE_MISMATCH = state が VALUE_MISMATCH で期が Prior1Year /
  別の fact に GROUNDED = state が GROUNDED で期が CurrentYear でない。残りは その他。手がかり偽の行が『P30E と同じ』= 結果・state・期が P30E と同じ。
- E-6 の通した率の分母 = 注入の行の数(封の字『分母 141』)、止めた行 = P32E で対応が付く行 − 通した行、名指して原本 = ``TUNE.LABEL_NAMED_ORIGINAL``。分母 0 の率は None = 外れ。
- E-10 は 97 書類で P32E の state が VALUE_MISMATCH の動いた行の期。Prior2Year・CurrentYear が 1 行でも在れば外れ(追記 1 の 4)。
- 記録は文・span・value・会社名・pointer の字(要素名)を持たない。docID は ``LATER_NAMING_FILES`` に宣言された記録だけ。
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
    u"""importlib で読み込む。``sys.modules`` にも登録する(``--procs`` 2 以上の fork で pickle に落ちないため)。"""
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name_file))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


RM = load_module("xbrl_rmix_2026-11-04.py", "rmix_for_pbind")
RR = load_module("xbrl_rmix_regress97_2026-11-04.py", "rmix_regress97_for_pbind")
PI = load_module("xbrl_pswap_idmap_2026-11-06.py", "pswap_idmap_for_pbind")
PS = PI.PS
XR = RR.XR
R97, D = RR.R97, RR.D
NF, GEN, RUN, TUNE = RM.NF, RM.GEN, RM.RUN, RM.TUNE
Stop = GEN.Stop

from adapters.xbrl import instance as INST            # noqa: E402
from adapters.xbrl import prose as PR                 # noqa: E402
from adapters.xbrl import recipes as R                # noqa: E402
from adapters.xbrl import verify_document as VD       # noqa: E402
from adapters.xbrl import vocabulary as V             # noqa: E402

SEAL_REL = "docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md"
SEAL_COMMIT = "b7824e6"
ADDENDUM_COMMIT = "56317fb"
DOC_REL = "docs/XBRL_PRIOR_CUE_BIND_ENGINE_RESULT_2026-11-06.md"
SCRIPT_REL = "measure/xbrl_pbind_2026-11-06.py"
REC_DIR_REL = "fixtures/xbrl/pbind"
MOVES_REL = REC_DIR_REL + "/moves_200_2026-11-06.json"
REGRESS97_REL = REC_DIR_REL + "/regress97_2026-11-06.json"
INJECT_REL = REC_DIR_REL + "/inject_2026-11-06.json"
REC_REL = collections.OrderedDict([("moves", MOVES_REL), ("regress97", REGRESS97_REL), ("inject", INJECT_REL)])
REC_KIND_SCRIPT = SCRIPT_REL
#: 読むだけの前の便の script・記録
RM_SCRIPT_REL, RR_SCRIPT_REL = "measure/xbrl_rmix_2026-11-04.py", "measure/xbrl_rmix_regress97_2026-11-04.py"
PI_SCRIPT_REL, PS_SCRIPT_REL = "measure/xbrl_pswap_idmap_2026-11-06.py", "measure/xbrl_pswap_2026-11-06.py"
PREV_SCRIPT_RELS = (RM_SCRIPT_REL, RR_SCRIPT_REL, PI_SCRIPT_REL, PS_SCRIPT_REL)
RB_RECORD_REL = "fixtures/xbrl/rmix/regress97_2026-11-04.json"          # E-2: P22〜P30E の出力の sha256(97 書類)の比べ先
T9_RECORD_REL = PI.INJECT_REL                                          # fixtures/xbrl/pswap/inject_idmap_2026-11-06.json(T9 の第 2 便。E-2 の 141 行の比べ先)
LABELS_REL = RM.LABELS_REL
SOURCES = RM.SOURCES
LIB_RELS = PI.LIB_RELS
OLD, NEW = "P30E", "P32E"
PROFILES = (OLD, NEW)
NOW_PROFILES = ("P22", "P26", "P27", "P27E", "P28", "P28E", "P29", "P29E", "P30E", "P32E")
BASE_PROFILES = ("P22", "P26", "P27", "P27E", "P28", "P28E", "P29", "P29E", "P30E")        # RB の便の記録(RR.NOW_PROFILES)の 9 つ
PAIRS = (("P32E 対 P30E", OLD, NEW),)
KEYED = (OLD, NEW)
ENGINE_FILES = ("adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py")
STATES = NF.STATES
G, VM, UNV, PNF = "GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"
HIT, MISS = RM.HIT, RM.MISS
LABEL_WORDS = RM.LABEL_WORDS
NO_LABEL = RM.NO_LABEL
EXISTING, NEWROW = u"既存", u"新"
PERIODS5 = ("CurrentYear", "Prior1Year", "Prior2Year", u"他", u"なし")
LINK_KEY = u"P32E の土台に対応"
T9 = PS.T9
SHAPES = PS.SHAPES
LABEL_PASS, LABEL_NAMED_ORIGINAL = TUNE.LABEL_PASS, TUNE.LABEL_NAMED_ORIGINAL
COND_NAMES = PI.CONDS
INJECT_LIMITS = (
    u"注入は T9 の 1 型だけ(前期の fact に結ばれた数に当期の値を入れる)。site・並べ替え・cap・差し替え・対応付け(id で引く 3 条件)は T9 の第 2 便のまま",
    u"土台は P30E が GROUNDED の claim。P32E の claim は (value, span, unit) が同じ 1 件があれば結ぶ(無ければ P32E の欄は対応なし)",
    u"engine の手がかりは T9 の recipes._prior_cue の真偽、窓の手がかりは PB の _prior_cue_window_2026_11_06 の真偽(どちらも注入前の文・token。読むだけで site の選びには使わない)",
    u"通した・止めたは engine の state で、札(人の目)は無い。pointer の期は id で引いた claim の pointers の先頭の context の先頭の語(要素名は持たない)")
MOVES_LIMITS = (
    u"通した・止めたは engine の state で、動いた行の札は前の便の盲検の 1 席目(既存の行だけ。P28E でなく P27 にある行)。新しい行には札が無い",
    u"200 本は Claude の model 2 つが書いた文。動いた行の中身は (種類, 文の番号, 位置, 前後の state, 前後の pointer の期, 札, 既存 / 新, 前期の fact が無い要素) だけで、文・span・値・要素名は持たない",
    u"前期の fact が無い要素は P32E の claim の先頭の pointer の要素に Prior1Year の JPY の fact が書類に無いこと。pointers が空・xbrl でない行は偽")
REGRESS_LIMITS = (
    u"97 書類は 2026 年提出の有報に偏る(P27 の封 §8 と同じ標本)",
    u"札が無いので動いた行の正しさは見ていない(E-3 は『壊さない』の確認)。E-7・E-9 は engine の commit の message の字を写した(この木で変異・全数を走らせ直していない)")


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def jround(x):
    return json.loads(json.dumps(x))


def within(x, lo_hi):
    return x is not None and lo_hi[0] <= x <= lo_hi[1]


# ======================================================================================================
# 期・前期の fact(この script が持つ小さい部品。T9 の ``pointer_period`` は Prior2Year を 他 に畳むので別に持つ)
_PTR_RE = re.compile(r"^xbrl:([^@]+)@(.+)$")


def pointer_parts(pointers):
    u"""pointers の先頭が xbrl の fact なら (要素, context)、無ければ (None, None)。"""
    ptrs = list(pointers or [])
    if not ptrs or not isinstance(ptrs[0], str):
        return None, None
    m = _PTR_RE.match(ptrs[0])
    return (m.group(1), m.group(2)) if m else (None, None)


def period5(pointers):
    u"""pointers の先頭の context の先頭の語。無ければ なし、xbrl の fact でなければ 他。要素名は返さない。"""
    ptrs = list(pointers or [])
    if not ptrs:
        return u"なし"
    _e, ctx = pointer_parts(ptrs)
    if ctx is None:
        return u"他"
    for p in PERIODS5[:3]:
        if ctx.startswith(p):
            return p
    return u"他"


def prior_elements(zb):
    u"""書類に context が Prior1Year で始まる JPY の fact を持つ要素の集合(B の ``fs`` と同じ絞り)。"""
    out = set()
    for f in INST.load_instance(zb)["facts"]:
        if (f.get("context") or "").startswith("Prior1Year") and (f.get("unit") or "").upper().startswith("JPY"):
            out.add(f["name"])
    return out


def no_prior_fact(pointers, prior_set):
    u"""『前期の fact が無い要素』(追記 1 の 1)。pointers が空・xbrl でない行は偽。"""
    elem, _c = pointer_parts(pointers)
    return bool(elem is not None and elem not in prior_set)


def window_cue(text, tok):
    u"""PB の窓の手がかり(``recipes._prior_cue_window_2026_11_06(s, a)``)の真偽。読むだけ。"""
    return bool(R._prior_cue_window_2026_11_06(text, tok.start))


# ======================================================================================================
# 配線・鍵の検査
def install():
    u"""XR(RR が RB の便のために差し替えた module)を PB の便の値に差し替える(使う側 ``XR.doc_job``・``XR.doc_rows``・``XR.engine_commits`` が引く名前)。"""
    for name, v in XR_SWAP:
        setattr(XR, name, v)


XR_SWAP = (("SEAL_REL", SEAL_REL), ("SEAL_COMMIT", SEAL_COMMIT), ("OUT_REL", REGRESS97_REL), ("PREV_RECORD_REL", RB_RECORD_REL), ("NOW_PROFILES", NOW_PROFILES),
           ("BASE_PROFILES", BASE_PROFILES), ("PAIRS", PAIRS), ("KEYED", KEYED), ("ENGINE_FILES", ENGINE_FILES))


def wiring_problems():
    u"""XR の差し替えが全部届いているか・RM の NF の差し替えがそのままか・PI の配線。問題の列。"""
    out = [u"XR.%s が差し替えた先でない" % name for name, v in XR_SWAP if getattr(XR, name) != v]
    out += list(RM.wiring_problems())
    if RM.R is not R and RM.R.__file__ != R.__file__:
        out.append(u"RM の recipes がこの script の recipes と違う file")
    if not hasattr(R, "_prior_cue_window_2026_11_06"):
        out.append(u"engine に _prior_cue_window_2026_11_06 が無い(PB の engine の commit の木でない)")
    if NEW not in V.PROFILES or OLD not in V.PROFILES:
        out.append(u"vocabulary に P30E か P32E が無い")
    return out


install()


def key_leaks_pb(gen):
    u"""``gen.key_leaks`` の版: この便の封の path(32 字に近い英数字・_・- の連なり)を除いて元の検査に渡す。"""
    orig = gen.key_leaks

    def fn(text, key_value=None, long_alnum=True):
        return orig(text.replace(SEAL_REL, u""), key_value, long_alnum)
    return fn


@contextlib.contextmanager
def key_check_pb(gen):
    u"""``gen.key_leaks`` を with の中だけこの便の封の path を除く版にする。出るときは必ず戻す。"""
    old = gen.key_leaks
    gen.key_leaks = key_leaks_pb(gen)
    try:
        yield
    finally:
        gen.key_leaks = old


def write_record(path, rec, run, gen, text=None, key_value=None):
    u"""記録を書く(禁止欄・鍵の検査を通してから。出力が既に在れば止める)。run・gen = 書く側の RUN・GEN(module の instance は便ごとに別)。"""
    text = text if text is not None else json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    with key_check_pb(gen):
        run.write_record(path, text, rec, key_value)


def sha_rel(root, rel):
    return GEN.sha256_file(os.path.join(root, rel))


def header_pb(root, kind, step, before, after, e_commit, inputs, extra=None):
    u"""3 つの記録に共通の頭。inputs = 読んだ入力の記録の path の列。"""
    h = collections.OrderedDict()
    h[u"seal"] = SEAL_REL
    h[u"封の commit"] = SEAL_COMMIT
    h[u"封の追記の commit"] = ADDENDUM_COMMIT
    h[u"step"] = step
    h[u"HEAD の commit"] = GEN.git_head(os.path.dirname(root))
    h[u"engine の commit"] = e_commit
    h[u"この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    h[u"前の便の script の sha256"] = collections.OrderedDict((rel, sha_rel(root, rel)) for rel in PREV_SCRIPT_RELS)
    h[u"入力の記録の sha256"] = collections.OrderedDict((rel, sha_rel(root, rel)) for rel in inputs)
    h[u"engine の指紋"] = VD.engine_fingerprint()
    h[u"lib の指紋"] = collections.OrderedDict((rel, sha_rel(root, rel)) for rel in LIB_RELS)
    h[u"profile"] = list(PROFILES) if kind != "regress97" else list(NOW_PROFILES)
    h[u"cache の前後"] = collections.OrderedDict([(u"前", before), (u"後", after), (u"変化なし", before == after)])
    if extra:
        h.update(extra)
    return h


def caches_all():
    return RM.caches_all()


# ======================================================================================================
# moves: AI の文 200 本で P30E → P32E の動いた行
def keyed_claims(zb, text, zm, pname):
    u"""({(文の番号, 位置): (state, reason, 生の pointers)}, 並びが対応したか)。数の claim だけ。"""
    prof = V.PROFILES[pname]
    out = VD.verify_document(zb, pname, text)
    nums, texts = R.build_raw_claims(zm, prof)
    raws = nums + texts
    cl = out["claims"]
    ok = len(cl) == len(raws) and all(c["id"] == r["id"] for c, r in zip(cl, raws))
    rows = collections.OrderedDict()
    for c, r in zip(cl, raws):
        if c["kind"] != "num":
            continue
        key = (r["sentence"], r["pos"])
        if key in rows:
            ok = False
        rows[key] = (c["state"], RUN.safe_reason(c["reason"]), tuple(c["pointers"] or ()))
    return rows, ok


def diff_rows(ra, rb):
    u"""(共通の鍵の列, 動いた鍵の列(state か pointers が違う), reason だけが違う鍵の列)。"""
    common = [k for k in ra if k in rb]
    moved = [k for k in common if ra[k][0] != rb[k][0] or ra[k][2] != rb[k][2]]
    mset = set(moved)
    reason_only = [k for k in common if k not in mset and ra[k][1] != rb[k][1]]
    return common, moved, reason_only


def move_entry(key, a, b, label, existing, nopf):
    u"""動いた行 1 つの記録の形 [種類, 文の番号, 位置, 前の state, 後の state, 前の期, 後の期, 札, 既存 / 新, 前期の fact が無い要素]。文・span・値・要素名は持たない。"""
    return [u"num", key[0], key[1], a[0], b[0], period5(a[2]), period5(b[2]), label, EXISTING if existing else NEWROW, bool(nopf)]


def judge_book_pb(job):
    u"""1 本(RM.load_jobs の job)。P30E・P32E の数の claim を鍵で突き合わせ、動いた行を記録の形にする。"""
    src, name, item, row, text_dir, zip_caches, prior, labels, n_book = job
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    zm = PR.build_modified_zip(zb, text)[0]
    r_old, ok_old = keyed_claims(zb, text, zm, OLD)
    r_new, ok_new = keyed_claims(zb, text, zm, NEW)
    old = RUN.judge_text(zb, text)[0]                       # 旗が偽の 4 profile。P27 の raw claim の並び(札の id を引く)
    idmap, idok = RM.id_map(zm, old)
    common, moved, reason_only = diff_rows(r_old, r_new)
    prior_set = prior_elements(zb) if moved else set()
    entries = []
    for k in moved:
        existing = k in idmap
        entries.append(move_entry(k, r_old[k], r_new[k], RM.label_of(k, idmap, labels, existing), existing, no_prior_fact(r_new[k][2], prior_set)))
    head = collections.OrderedDict([(u"name", name), (u"docID", item[u"docID"]), (u"form", item[u"form"]), (u"model", item[u"model"]), (u"writer", item[u"writer"]),
                                    (u"材料", src), (u"文の sha256", item[u"sha256"])])
    head[u"対応"] = collections.OrderedDict([(OLD, ok_old), (NEW, ok_new)])
    head[u"数の claim の数"] = collections.OrderedDict([(OLD, len(r_old)), (NEW, len(r_new))])
    head[u"P30E と P32E で数の claim の鍵が同じ"] = sorted(r_old) == sorted(r_new)
    head[u"P27 の鍵が一意"] = bool(idok)
    head[u"GROUNDED の数"] = collections.OrderedDict([(OLD, sum(1 for v in r_old.values() if v[0] == G)), (NEW, sum(1 for v in r_new.values() if v[0] == G))])
    head[u"動いた行"] = len(moved)
    head[u"state が変わった行"] = sum(1 for k in moved if r_old[k][0] != r_new[k][0])
    head[u"reason だけが違う行"] = len(reason_only)
    head[u"動いた行の中身"] = entries
    return head


def moves_block(bs):
    u"""``本`` の列 → 集計 1 ブロック(全体・形別・model 別で同じ関数)。門が記録の ``本`` から作り直して照らす(集計の正本はこの関数)。"""
    ents = [(b, x) for b in bs for x in b[u"動いた行の中身"]]
    X = [x for _b, x in ents]

    def of(pred):
        return [x for x in X if pred(x)]

    def lab(sel):
        c = collections.Counter(x[7] if x[7] is not None else NO_LABEL for x in sel if x[8] == EXISTING)
        out = collections.OrderedDict((w, c.get(w, 0)) for w in LABEL_WORDS + (NO_LABEL,))
        out[NEWROW] = sum(1 for x in sel if x[8] == NEWROW)
        return out
    lost = of(lambda x: x[3] == G and x[4] != G)
    gained = of(lambda x: x[3] != G and x[4] == G)
    pv = of(lambda x: x[3] == PNF and x[4] == VM)
    stay = of(lambda x: x[3] == VM and x[4] == VM and x[5] != x[6])
    unp = of(lambda x: x[3] == UNV and x[4] == PNF)
    dirs = collections.Counter(u"%s → %s" % (x[3], x[4]) for x in X if x[3] != x[4])
    stay_dirs = collections.Counter(u"%s → %s" % (x[5], x[6]) for x in stay)
    return collections.OrderedDict([
        (u"本", len(bs)),
        (u"数の claim の数", collections.OrderedDict((p, sum(b[u"数の claim の数"][p] for b in bs)) for p in PROFILES)),
        (u"GROUNDED の数", collections.OrderedDict([(OLD, sum(b[u"GROUNDED の数"][OLD] for b in bs)), (NEW, sum(b[u"GROUNDED の数"][NEW] for b in bs)),
                                                   (u"差", sum(b[u"GROUNDED の数"][NEW] - b[u"GROUNDED の数"][OLD] for b in bs))])),
        (u"E-4 動いた行", len(X)),
        (u"state が変わった行", sum(1 for x in X if x[3] != x[4])),
        (u"state は同じで pointer の期だけ変わった行", sum(1 for x in X if x[3] == x[4] and x[5] != x[6])),
        (u"向き別", collections.OrderedDict(sorted(dirs.items()))),
        (u"E-4 GROUNDED を失う行", collections.OrderedDict([(u"行", len(lost)), (u"札", lab(lost))])),
        (u"GROUNDED になった行", collections.OrderedDict([(u"行", len(gained)), (u"札", lab(gained))])),
        (u"E-4 POINTER_NOT_FOUND → VALUE_MISMATCH", collections.OrderedDict([(u"行", len(pv)), (u"札", lab(pv))])),
        (u"VALUE_MISMATCH のまま pointer の期が変わる行", collections.OrderedDict([(u"行", len(stay)), (u"札", lab(stay)), (u"期の変わり方", collections.OrderedDict(sorted(stay_dirs.items())))])),
        (u"UNVERIFIABLE → POINTER_NOT_FOUND", collections.OrderedDict([(u"行", len(unp)), (u"札", lab(unp))])),
        (u"動いた行の札", lab(X)),
        (u"後の期が Prior2Year の動いた行", sum(1 for x in X if x[6] == "Prior2Year")),
        (u"前期の fact が無い要素の動いた行", sum(1 for x in X if x[9] is True)),
        (u"reason だけが違う行", sum(b[u"reason だけが違う行"] for b in bs)),
        (u"対応が付かなかった本", sum(1 for b in bs if not all(b[u"対応"].values()))),
        (u"P30E と P32E で鍵が違う本", sum(1 for b in bs if not b[u"P30E と P32E で数の claim の鍵が同じ"])),
        (u"P27 の鍵が一意でない本", sum(1 for b in bs if not b[u"P27 の鍵が一意"]))])


def aggregate_moves(books):
    out = collections.OrderedDict([(u"全体", moves_block(books))])
    out[u"形別"] = collections.OrderedDict((f, moves_block([b for b in books if b[u"form"] == f])) for f in sorted(set(b[u"form"] for b in books)))
    out[u"model 別"] = collections.OrderedDict((m, moves_block([b for b in books if b[u"model"] == m])) for m in sorted(set(b[u"model"] for b in books)))
    return out


def moves_inputs():
    ins = []
    for src, p in SOURCES.items():
        ins += [p["gen"], p["claims"]]
    return ins + list(LABELS_REL.values()) + [RM.N_AI200_REL]


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
    caches = caches_all()
    before = GEN.caches_snapshot(caches)
    say(u"動いた行 %d 本 × 2 profile(P30E・P32E)― procs %d" % (len(jobs_), procs))
    recs = NF.map_pool(judge_book_pb, jobs_, procs)
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = header_pb(root, "moves", u"PB(前期の手がかりがある数を当期の fact に落とさない)― AI の文 200 本の P30E → P32E の動いた行(0 USD)", before, after, e, moves_inputs())
    rec[u"範囲"] = u"全 200 本" if only is None else u"**--only の本だけ(本番の記録ではない)**"
    rec[u"欄"] = collections.OrderedDict([
        (u"数の claim の鍵", u"(文の番号, 文の中の位置)。id は profile 間で替わるので使わない"),
        (u"動いた行", u"P30E と P32E の両方にある鍵のうち state か pointers が違う行(封 E-4 の字)。reason だけが違う行は別に数える"),
        (u"動いた行の中身", u"[種類, 文の番号, 位置, 前の state, 後の state, 前の期, 後の期, 札 or null, 既存 / 新, 前期の fact が無い要素]。文・span・値・要素名は持たない"),
        (u"札", u"前の便の盲検の 1 席目の札(labels・f5_labels)。鍵 → id は P27 の raw claim の並び。既存 = P27 にも在る行。新しい行には札が無い"),
        (u"期", u"pointers の先頭の context の先頭の語: CurrentYear / Prior1Year / Prior2Year / 他 / なし"),
        (u"前期の fact が無い要素", u"P32E の claim の先頭の pointer の要素に、Prior1Year の JPY の fact が書類に無い(追記 1 の 1)。pointers が空・xbrl でない行は偽")])
    rec[u"本"] = recs
    rec[u"集計"] = aggregate_moves(recs)
    rec[u"限界"] = list(MOVES_LIMITS)
    rec[u"key_leaks"] = []
    write_record(out, rec, RUN, GEN, key_value=key_value)
    say(u"-> %s(本 %d)" % (out, len(recs)))
    return rec


# ======================================================================================================
# regress97: 手元の 97 書類の原文での退行・動いた行・engine の差分
def doc_moves_pb(res, zpath):
    u"""1 書類の P32E 対 P30E の動いた行(state か pointers が違う行)と reason だけが違う行の数。(entries, reason_only)。zpath = 書類の ZIP(前期の fact を読む)。"""
    ra, rb = res[u"keyed"][OLD], res[u"keyed"][NEW]
    common = [k for k in rb if k in ra]
    moved = [k for k in common if ra[k][0] != rb[k][0] or ra[k][2] != rb[k][2]]
    mset = set(moved)
    reason_only = sum(1 for k in common if k not in mset and ra[k][1] != rb[k][1])
    prior_set = set()
    if moved:
        with io.open(zpath, "rb") as fh:
            prior_set = prior_elements(fh.read())
    entries = []
    for k in moved:
        entries.append([k[0], k[1], k[2], k[3], ra[k][0], rb[k][0], period5(ra[k][2]), period5(rb[k][2]), ra[k][0] != rb[k][0], ra[k][2] != rb[k][2], no_prior_fact(rb[k][2], prior_set)])
    return entries, reason_only


def engine_numstat():
    u"""封の commit から engine の commit までの numstat を file ごとに(``XR.engine_commits`` の行)。{file: [挿入, 削除]}。"""
    _seal, _e, num, _tests = XR.engine_commits()
    out = collections.OrderedDict()
    for x in num:
        ins, dele, path = x.split("\t")
        out[path[len(XR.PREFIX):]] = [int(ins) if ins != "-" else None, int(dele) if dele != "-" else None]
    return out


def message_numbers(message):
    u"""engine の commit の message から E-7・E-9 の数を読む。{E-7: {...} or None, E-9: {...} or None}。字が無ければ None(外れ)。"""
    m7 = re.search(r"変異 (\d+) 本全部赤", message or u"")
    m9 = re.search(r"赤は ([A-Za-z0-9_ ]+?) の (\d+) 本だけ\(pytest (\d+) failed / ([\d,]+) passed / (\d+) skipped、unittest failures=(\d+)\)", message or u"")
    e7 = collections.OrderedDict([(u"変異の本数", int(m7.group(1))), (u"赤", int(m7.group(1))), (u"原文", m7.group(0))]) if m7 else None
    e9 = None
    if m9:
        e9 = collections.OrderedDict([(u"赤の試験", [m9.group(1).strip()]), (u"赤の本数", int(m9.group(2))),
                                      (u"pytest", collections.OrderedDict([("failed", int(m9.group(3))), ("passed", int(m9.group(4).replace(",", ""))), ("skipped", int(m9.group(5)))])),
                                      (u"unittest failures", int(m9.group(6))), (u"原文", m9.group(0))])
    return collections.OrderedDict([("E-7", e7), ("E-9", e9)])


def engine_message(e_commit):
    p = subprocess.run(["git", "-C", XR.REPO, "log", "-1", "--format=%B", e_commit], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise Stop(u"**engine の commit の message を git から読めない。止める**")
    return p.stdout.decode("utf-8", "replace")


def regress_block(docs):
    u"""``書類`` の行 → 集計(判定に使う欄)。門が記録の ``書類`` から作り直して照らす(集計の正本はこの関数)。"""
    out = collections.OrderedDict()
    out[u"4 state"] = collections.OrderedDict((p, collections.OrderedDict((s, sum(d[u"4 state"][p][s] for d in docs)) for s in STATES)) for p in NOW_PROFILES)
    out[u"claims"] = collections.OrderedDict((p, sum(d[u"claims"][p] for d in docs)) for p in NOW_PROFILES)
    c2 = collections.OrderedDict()
    for p in BASE_PROFILES:
        same = [d[u"docID"] for d in docs if d[u"出力の sha256(engine の欄を除く)"][p] == d[u"前の便の記録の sha256"][p]]
        c2[p] = collections.OrderedDict([(u"byte が同じ書類", len(same)), (u"書類", len(docs)), (u"違った書類", sorted(set(d[u"docID"] for d in docs) - set(same)))])
    out[u"E-2 旗が偽の profile の byte 一致"] = c2
    ents = [x for d in docs for x in d[u"P32E の動いた行"]]
    sch = [x for x in ents if x[8]]                                    # state が変わった行(E-3・E-10 の定義)
    lost = [x for x in sch if x[4] == G and x[5] != G]
    gained = [x for x in sch if x[4] != G and x[5] == G]
    dirs = collections.Counter(u"%s → %s" % (x[4], x[5]) for x in sch)
    out[u"E-3 P32E 対 P30E"] = collections.OrderedDict([
        (u"動いた行", len(sch)), (u"GROUNDED を失う行", len(lost)), (u"GROUNDED になった行", len(gained)),
        (u"動いた書類", sum(1 for d in docs if any(x[8] for x in d[u"P32E の動いた行"]))),
        (u"向き別", collections.OrderedDict(sorted(dirs.items()))),
        (u"state か pointers が違う行", len(ents)), (u"pointers だけが違う行", len(ents) - len(sch)),
        (u"state か pointers が違う行のある書類", sum(1 for d in docs if d[u"P32E の動いた行"])),
        (u"reason だけが違う行", sum(d[u"reason だけが違う行"] for d in docs)),
        (u"XR の定義(state・reason・pointers のどれか)の動いた行", sum(len(d[u"動いた行と増えた行"][PAIRS[0][0]][u"動いた既存の行"]) for d in docs)),
        (u"増えた行", sum(d[u"動いた行と増えた行"][PAIRS[0][0]][u"増えた行"] for d in docs)),
        (u"消えた行", sum(d[u"動いた行と増えた行"][PAIRS[0][0]][u"消えた行"] for d in docs)),
        (u"claim の数が違う書類", sum(1 for d in docs if d[u"claims"][NEW] != d[u"claims"][OLD]))])
    vm = [x for x in sch if x[5] == VM]
    pc = collections.Counter(x[7] for x in vm)
    out[u"E-10 VALUE_MISMATCH に動いた行の pointer の期"] = collections.OrderedDict([(u"行", len(vm))] + [(p, pc.get(p, 0)) for p in PERIODS5])
    stay = [x for x in ents if not x[8] and x[5] == VM]
    sc_ = collections.Counter(u"%s → %s" % (x[6], x[7]) for x in stay)
    out[u"参考 VALUE_MISMATCH のまま pointer の期が動いた行"] = collections.OrderedDict([(u"行", len(stay)), (u"期の変わり方", collections.OrderedDict(sorted(sc_.items())))])
    out[u"前期の fact が無い要素の動いた行"] = collections.OrderedDict([(u"動いた行(state か pointers)", sum(1 for x in ents if x[10] is True)), (u"うち state が変わった行", sum(1 for x in sch if x[10] is True)),
                                                                  (u"うち VALUE_MISMATCH に動いた行", sum(1 for x in vm if x[10] is True)), (u"うち GROUNDED を失う行", sum(1 for x in lost if x[10] is True))])
    return out


def regress_inputs():
    return [RB_RECORD_REL]


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
    prev = D.jload(os.path.join(root, RB_RECORD_REL))
    prev_by = dict((r["docID"], r) for r in prev[u"書類"])
    if sorted(prev_by) != sorted(ids67 + ids30):
        raise Stop(u"**RB の便の記録の書類が 97 書類の一覧と合わない。止める**")
    if only is not None:
        jobs = [j for j in jobs if j[0] == only]
        if not jobs:
            raise Stop(u"**--only の docID が 97 書類に無い。止める**")
    zpath = dict((j[0], j[4]) for j in jobs)
    res = R97.run_pool(XR.doc_job, jobs, procs)
    names_after = collections.OrderedDict((k, P.names_sha(v)) for k, v in R97.CACHES.items())
    if names_before != names_after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    docs = XR.doc_rows(res, prev_by)
    by_doc = dict((r[u"doc"], r) for r in res)
    for d in docs:
        ents, ro = doc_moves_pb(by_doc[d[u"docID"]], zpath[d[u"docID"]])
        d[u"P32E の動いた行"] = ents
        d[u"reason だけが違う行"] = ro
    seal, e, num, tests = XR.engine_commits()
    link = XR.engine_link()
    link[u"numstat"] = engine_numstat()
    msg = message_numbers(engine_message(e))
    rec = header_pb(root, "regress97", u"PB(前期の手がかりがある数を当期の fact に落とさない)― 手元の 97 書類の有報の原文での退行・動いた行・engine の差分(0 USD)", names_before, names_after, e, regress_inputs())
    rec[u"範囲"] = u"全 97 書類" if only is None else u"**--only の 1 書類だけ(本番の記録ではない)**"
    rec[u"どの 97 か"] = u"67 = fixtures/xbrl/p26_2026-10-21.json の `書類 67` の key。30 = fixtures/xbrl/fresh/fetched_2026-10-21.json の `取得した書類` で `使う` が真。ZIP の sha256 はそれぞれの記録と照らした"
    rec[u"評価用の AI の文・DB の応答"] = u"開いていない(この script は edinetdb-p27/ の下を読まない)"
    rec[u"欄"] = collections.OrderedDict([
        (u"P32E の動いた行", u"[文の番号を含む鍵 (種類, 文の番号, 位置, 順), P30E の state, P32E の state, 前の期, 後の期, state が違う, pointers が違う, 前期の fact が無い要素]。state か pointers が違う行(封 E-3 の字)"),
        (u"動いた行と増えた行", u"XR(N の便の regress97 script)の定義: state・reason・pointers のどれかが違う行と、増えた行・消えた行"),
        (u"E-7・E-9 の写し", u"engine の commit の message の字を読んで写した(この木で変異・全数を走らせ直していない。司令塔が許した決め)")])
    rec[u"E-1・E-8 engine の差分"] = link
    rec[u"E-7・E-9 の写し"] = collections.OrderedDict([(u"出どころ", u"engine の commit の message"), (u"engine の commit", e)] + [(k, v) for k, v in msg.items()])
    rec[u"集計"] = regress_block(docs)
    rec[u"書類"] = docs
    rec[u"限界"] = list(REGRESS_LIMITS)
    rec[u"key_leaks"] = D.record_key_leaks(rec)
    if rec[u"key_leaks"]:
        raise Stop(u"記録に鍵が入った")
    write_record(out, rec, RUN, GEN)
    say(u"-> %s" % out)
    return rec


# ======================================================================================================
# inject: T9 の id の対応付けの注入を P30E・P32E で
def base_pair():
    u"""``RM.base_status_rb`` が引く (比較, 土台) の対を with の中だけ (P32E, P30E) にする。出るときは必ず戻す。"""
    return _SwapAttr(PI.RM, "INJECT_PROFILES", (NEW, OLD))


class _SwapAttr(object):
    def __init__(self, mod, name, value):
        self.mod, self.name, self.value = mod, name, value

    def __enter__(self):
        self.old = getattr(self.mod, self.name)
        setattr(self.mod, self.name, self.value)
        return self

    def __exit__(self, *a):
        setattr(self.mod, self.name, self.old)
        return False


def base_status_pb(base_claims, base_by_id, tok, text):
    u"""(状態, 土台)。土台 = 無改変の文で P30E が GROUNDED の claim(T9 と同じ)。P32E の claim は (value, span, unit) が同じ 1 件があれば結ぶ。``RM.base_status_rb`` をそのまま呼ぶ(対だけ替える)。"""
    with base_pair():
        return PI.RM.base_status_rb(base_claims, base_by_id, tok, text)


def inject_text_pb(zb, text, refs, seed, key, cap=RUN.INJECT_CAP, verify=None):
    u"""T9 の 1 本の注入(site・並べ替え・cap・差し替え・対応付けは T9 の第 2 便のまま)を P30E・P32E で。(行, 数え)。"""
    N_ = PI.N
    if N_.normalize_digits(text) != text:
        return [], collections.OrderedDict([(u"注入しない", u"文に全角の数字がある(select は半角の文を前提にする)")])
    verify = verify or VD.verify_document
    base_claims = dict((p, verify(zb, p, text)["claims"]) for p in PROFILES)
    base_by_id = dict((p, dict((c["id"], c) for c in base_claims[p])) for p in PROFILES)
    stages, sites = PS.t9_all_sites(text, refs, seed, key)
    ok = []
    for s in sites:
        st, bc = base_status_pb(base_claims, base_by_id, s["token"], text)
        if bc is not None:
            ok.append((s, bc))
    counts = collections.OrderedDict([(u"作れる site", len(sites)), (u"土台 P30E が GROUNDED の site", len(ok)), (u"cap を基準で絞る前に掛けた数", min(cap, len(sites)))])
    rows = []
    n = 0
    for s, bc in ok[:cap]:
        n += 1
        tok = s["token"]
        inj = PS.build_t9(s, "%s-T9-%02d" % (key, n))
        target = PI.SC.scaled_value(inj["new_value"], tok.unit)
        tampered, placements = PI.IJ.apply_edits(text, [inj])
        rt = PI.IJ.revert(tampered, [inj], placements, text) == text
        row = collections.OrderedDict([
            (u"id", inj["id"]), (u"型", T9), (u"形", PS.shape_of_token(tok)), (u"基準の claim", bc["id"]), (LINK_KEY, bc["ids"][NEW] is not None),
            (u"round-trip", bool(rt)), (u"読み直し", bool(PS.JT.reread_j(tampered, tok, inj["new_value"], tok.unit))),
            (u"engine の手がかり", PS.engine_cue(text, tok)), (u"窓の手がかり", window_cue(text, tok)), (u"文に前期の語", PS.has_prior_word(text, tok)),
            (u"基準の pointer の期", PS.pointer_period(bc.get("pointers")))])
        cells, periods, miss = {}, {}, {}
        for p in PROFILES:
            if bc["ids"][p] is None:
                cells[p], periods[p], miss[p] = TUNE.classify(None, None), u"なし", [PI.NO_BASE]
                continue
            claims = verify(zb, p, tampered)["claims"]
            res, _conds, miss[p], found = PI.id_map(claims, bc["ids"][p], target, inj["replacement"])
            cells[p] = TUNE.classify(res, base_by_id[p][bc["ids"][p]])
            periods[p] = period5(found.get("pointers")) if found is not None else u"なし"
        for p in PROFILES:
            row[p] = cells[p]
        for p in PROFILES:
            row[u"%s の注入後の pointer の期" % p] = periods[p]
        for p in PROFILES:
            row[u"%s の欠けた条件" % p] = miss[p]
        rows.append(row)
    counts[u"採った"] = n
    return rows, counts


def inject_job_pb(args):
    src, name, item, row, text_dir, zip_caches, seed, work_root = args
    if not getattr(PI.N, PI.FLAG):
        raise Stop(u"**切り替えが偽のまま inject を走らせた。止める**")
    zb = PI.GEN.read_zip(row, zip_caches)
    text = PI.RUN.read_text(name, item, text_dir)
    refs = PI.RUN.refs_for(row, zip_caches, work_root)
    rows, counts = inject_text_pb(zb, text, refs, seed, name)
    base = collections.OrderedDict([(u"docID", item[u"docID"]), (u"form", item[u"form"]), (u"model", item[u"model"]), (u"writer", item[u"writer"])])
    out = []
    for r in rows:
        d = collections.OrderedDict(base)
        d.update(r)
        out.append(d)
    return name, out, counts


def same_cell(a, b):
    return a[u"結果"] == b[u"結果"] and a[u"state"] == b[u"state"]


def inject_columns(rows, t9_rows):
    u"""E-2(141 行の P30E)・E-5・E-6 の欄を ``行`` と T9 の第 2 便の記録の ``行`` から数える(記録の ``E の欄`` と tally の判定が使う)。"""
    t9 = dict((r[u"id"], r) for r in t9_rows)
    ids, t9ids = set(r[u"id"] for r in rows), set(t9)
    e2 = collections.OrderedDict([
        (u"行の数", len(rows)), (u"T9 の第 2 便の記録の行の数", len(t9_rows)), (u"id の集合が T9 の第 2 便の記録と同じ", ids == t9ids),
        (u"P30E の結果と state が T9 の第 2 便の記録と同じ行", sum(1 for r in rows if r[u"id"] in t9 and same_cell(r[OLD], t9[r[u"id"]][OLD])))])
    cue = [r for r in rows if r[u"engine の手がかり"] is True]
    off = [r for r in rows if r[u"engine の手がかり"] is not True]

    def cls(r):
        c, per = r[NEW], r[u"%s の注入後の pointer の期" % NEW]
        if c[u"state"] == G and per == "CurrentYear":
            return u"当期の fact に GROUNDED"
        if c[u"state"] == VM and per == "Prior1Year":
            return u"前期の fact を名指して VALUE_MISMATCH"
        if c[u"state"] == G:
            return u"別の fact に GROUNDED"
        return u"その他"
    cc = collections.Counter(cls(r) for r in cue)
    keys = (u"当期の fact に GROUNDED", u"前期の fact を名指して VALUE_MISMATCH", u"別の fact に GROUNDED", u"その他")
    same_off = [r for r in off if same_cell(r[NEW], r[OLD]) and r[u"%s の注入後の pointer の期" % NEW] == r[u"%s の注入後の pointer の期" % OLD]]
    e5 = collections.OrderedDict([(u"手がかり真の行", len(cue))] + [(k, cc.get(k, 0)) for k in keys] +
                                 [(u"手がかり偽の行", len(off)), (u"手がかり偽の行のうち P30E と同じ行", len(same_off))])
    passed = [r for r in rows if r[NEW][u"結果"] == LABEL_PASS]
    stopped = [r for r in rows if r[NEW][u"対応"] and r[NEW][u"結果"] != LABEL_PASS]
    named = [r for r in stopped if r[NEW][u"結果"] == LABEL_NAMED_ORIGINAL]
    e6 = collections.OrderedDict([(u"通した率(P32E)", pct(len(passed), len(rows))), (u"通した行", len(passed)), (u"注入の行", len(rows)),
                                  (u"止めた行", len(stopped)), (u"うち名指して原本", len(named)), (u"名指して原本の割合", pct(len(named), len(stopped)))])
    ref = collections.OrderedDict([
        (u"P30E の通した行", sum(1 for r in rows if r[OLD][u"結果"] == LABEL_PASS)),
        (u"P32E に対応が付かない行", sum(1 for r in rows if not r[NEW][u"対応"])),
        (u"engine の手がかりと窓の手がかりが違う行", sum(1 for r in rows if r[u"engine の手がかり"] != r[u"窓の手がかり"])),
        (u"窓の手がかり真の行", sum(1 for r in rows if r[u"窓の手がかり"] is True)),
        (u"round-trip 不一致", sum(1 for r in rows if not r[u"round-trip"])), (u"読み直し不一致", sum(1 for r in rows if not r[u"読み直し"])),
        (u"P32E の注入後の期が Prior2Year の行", sum(1 for r in rows if r[u"%s の注入後の pointer の期" % NEW] == "Prior2Year"))])
    return collections.OrderedDict([(u"E-2 T9 の第 2 便の記録との照らし", e2), (u"E-5 手がかり別の P32E", e5), (u"E-6 通した率と名指して原本", e6), (u"参考", ref)])


def inject_summary(rows):
    u"""profile ごとの結果の語の数(分母 = 注入の行)。"""
    labels = (LABEL_PASS, LABEL_NAMED_ORIGINAL, TUNE.LABEL_NAMED_OTHER, TUNE.LABEL_PNF, TUNE.LABEL_UNV, TUNE.LABEL_UNMAPPED)
    out = collections.OrderedDict()
    for p in PROFILES:
        c = collections.Counter(r[p][u"結果"] for r in rows)
        d = collections.OrderedDict([(u"注入の行", len(rows))])
        for w in labels:
            d[w] = collections.OrderedDict([(u"件", c.get(w, 0)), (u"率", pct(c.get(w, 0), len(rows)))])
        out[p] = d
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
    caches = PI.caches_all()
    before = PI.GEN.caches_snapshot(caches)
    work_root = work_root or tempfile.mkdtemp(prefix="pbind_inject_", dir=os.environ.get("TMPDIR"))
    jobs_ = [(src, n, item, row, PI.SOURCES[src]["cache"], PI.GEN.EXISTING_CACHES, seed, work_root) for (src, n, item, row, _prior) in books]
    say(u"注入 %d 本 × 2 profile(P30E・P32E)。切り替え 真・T9_PRIOR_TO_CURRENT・id で引く対応付け ― procs %d(1 件ごとに判定。時間がかかる)" % (len(jobs_), procs))
    with PI.yen_scan_on():
        if not getattr(PI.N, PI.FLAG) or PI.wiring_problems():
            raise Stop(u"**切り替えを真にできない・配線が崩れた。止める**")
        results = PI.NF.map_pool(inject_job_pb, jobs_, procs)
    if getattr(PI.N, PI.FLAG):
        raise Stop(u"**with を出ても切り替えが真のまま。止める**")
    rows, per = [], collections.OrderedDict()
    for n, r, c in results:
        rows += r
        per[n] = c
    after = PI.GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    t9_rec = PI.GEN.jload(os.path.join(root, T9_RECORD_REL))
    _s, e, _n, _t = XR.engine_commits()
    rec = header_pb(root, "inject", u"PB(前期の手がかりがある数を当期の fact に落とさない)― T9 の id の対応付けの注入を P30E・P32E で(切り替え 真。0 USD)", before, after, e, [T9_RECORD_REL] +
                    [p["gen"] for p in SOURCES.values()])
    rec[u"範囲"] = u"全 200 本" if only is None else u"**--only(本番の記録ではない)**"
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", PI.FLAG), (u"inject の中の値", True), (u"出たあとの値", bool(getattr(PI.N, PI.FLAG))), (u"配線の問題", PI.wiring_problems())])
    rec[u"種"] = {u"file": PI.RUN.SEED_REL_STR, u"種の確認": seed_meta}
    rec[u"型"] = collections.OrderedDict([
        (T9, u"T9 の第 2 便と同じ site・並べ替え・cap・差し替え・対応付け(S.identified_sites の (token, ref) のうち ref の context が Prior1Year で始まり、同じ要素の CurrentYear の fact がちょうど 1 件の数に、その当期の値を元の字の形で入れる。"
             u"注入後の claim は基準の claim と同じ id の claim を引く)"),
        (u"上限", u"1 本あたり %d" % RUN.INJECT_CAP), (u"site", PS.SITE_WORD), (u"土台", PS.BASE_WORD),
        (u"土台の結び方", u"P30E の claim を find_base_claim で 1 件に決め、P32E の claim は (value, span, unit) が同じ 1 件があれば結ぶ。無ければその行の P32E の欄は対応なし(判定しない)"),
        (u"手がかり", u"engine の手がかり = recipes._prior_cue(注入前の文, token.start, token.end)、窓の手がかり = recipes._prior_cue_window_2026_11_06(注入前の文, token.start)。どちらも読むだけ"),
        (u"期", u"id で引いた claim の pointers の先頭の context の先頭の語: CurrentYear / Prior1Year / Prior2Year / 他 / なし。要素名は持たない"),
        (u"inject の docID の引数", u"本の名前(<docID>_<形>_<model>)")])
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"] = inject_summary(rows)
    rec[u"E の欄"] = inject_columns(rows, t9_rec[u"行"])
    rec[u"限界"] = list(INJECT_LIMITS)
    rec[u"key_leaks"] = []
    rec[u"行"] = rows
    write_record(out, rec, PI.RUN, PI.GEN, text=PI.RUN.dumps_inject(rec), key_value=key_value)
    say(u"-> %s(注入の行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
# tally: 封の表(§3 の E-1〜E-10・§4 の K-1〜K-5)を読み、記録から判定する
def read_seal(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def seal_pred_rows(seal):
    u"""封 §3 の表の行 {E-n: (欄, 予測, 外れ方)}。"""
    sec = seal[seal.index("## §3"):seal.index("## §4")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| (E-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            out[m.group(1)] = (cells[0], cells[1], cells[2] if len(cells) > 2 else u"")
    return out


def seal_k_rows(seal):
    sec4 = seal[seal.index("## §4"):seal.index("## §5")]
    return collections.OrderedDict((m.group(1), m.group(2)) for m in re.finditer(r"^- (K-\d): (.*)$", sec4, re.M))


NUM = r"[\d,]+(?:\.\d+)?"


def _rng(m, i):
    return (NF.num(m.group(i)), NF.num(m.group(i + 1)))


def seal_bounds(seal):
    u"""封の字から予測の幅と採用の基準の閾値を読む(字のコピーにしない)。{名前: 値}。"""
    P = seal_pred_rows(seal)
    K = seal_k_rows(seal)
    b = collections.OrderedDict()
    m = re.match(r"^(\d+)〜(\d+) / (\d+)、(\d+)〜(\d+) / (\d+)、(\d+)$", P["E-1"][1].strip())
    b["E-1"] = collections.OrderedDict([(u"recipes 挿入", (int(m.group(1)), int(m.group(2)))), (u"recipes 削除", int(m.group(3))), (u"vocabulary 挿入", (int(m.group(4)), int(m.group(5)))),
                                        (u"vocabulary 削除", int(m.group(6))), (u"他の file", int(m.group(7)))])
    m = re.match(r"^(\d+) / (\d+)、(\d+) / (\d+)$", P["E-2"][1].strip())
    b["E-2"] = collections.OrderedDict([(u"byte が同じ書類", int(m.group(1))), (u"書類", int(m.group(2))), (u"P30E の結果と state が同じ行", int(m.group(3))), (u"行", int(m.group(4)))])
    m = re.match(r"^(\d+) / (%s)〜(%s) / (\d+)〜(\d+)$" % (NUM, NUM), P["E-3"][1].strip())
    b["E-3"] = collections.OrderedDict([(u"GROUNDED を失う行", int(m.group(1))), (u"動いた行", (NF.num(m.group(2)), NF.num(m.group(3)))), (u"動いた書類", (int(m.group(4)), int(m.group(5))))])
    m = re.match(r"^(\d+)〜(\d+) / (\d+)〜(\d+)\((\d+)〜(\d+)\)\s*/ (\d+)〜(\d+)$", P["E-4"][1].strip())
    b["E-4"] = collections.OrderedDict([(u"動いた行", (int(m.group(1)), int(m.group(2)))), (u"GROUNDED を失う行", (int(m.group(3)), int(m.group(4)))),
                                        (u"うち札 真", (int(m.group(5)), int(m.group(6)))), (u"POINTER_NOT_FOUND → VALUE_MISMATCH", (int(m.group(7)), int(m.group(8))))])
    m = re.match(r"^(\d+) / (\d+)〜(\d+) / (\d+)〜(\d+)、(\d+) / (\d+)$", P["E-5"][1].strip())
    b["E-5"] = collections.OrderedDict([(u"当期の fact に GROUNDED", int(m.group(1))), (u"前期の fact を名指して VALUE_MISMATCH", (int(m.group(2)), int(m.group(3)))),
                                        (u"別の fact に GROUNDED", (int(m.group(4)), int(m.group(5)))), (u"手がかり偽の行のうち P30E と同じ行", int(m.group(6))), (u"手がかり偽の行", int(m.group(7)))])
    m = re.match(r"^(%s)〜(%s)%%、(%s)〜(%s)%%$" % (NUM, NUM, NUM, NUM), P["E-6"][1].strip())
    b["E-6"] = collections.OrderedDict([(u"通した率(P32E)", _rng(m, 1)), (u"名指して原本の割合", _rng(m, 3))])
    m = re.match(r"^(\d+) / (\d+)$", P["E-7"][1].strip())
    b["E-7"] = collections.OrderedDict([(u"赤", int(m.group(1))), (u"変異の本数", int(m.group(2)))])
    m = re.match(r"^(\d+)〜(\d+)$", P["E-8"][1].strip())
    b["E-8"] = (int(m.group(1)), int(m.group(2)))
    m = re.match(r"^([A-Za-z0-9_]+) の ([A-Za-z0-9_]+) だけ、(\d+)$", P["E-9"][1].strip())
    b["E-9"] = collections.OrderedDict([(u"赤の試験", [u"%s %s" % (m.group(1), m.group(2))]), (u"ほかの赤", int(m.group(3)))])
    m = re.match(r"^全部 (Prior1Year)\((\d+)〜(\d+) 行\)$", P["E-10"][1].strip())
    b["E-10"] = collections.OrderedDict([(u"期", m.group(1)), (u"行", (int(m.group(2)), int(m.group(3))))])
    b["K-1"] = tuple(int(x) for x in re.search(r"E-2 が (\d+) / (\d+) かつ (\d+) / (\d+)", K["K-1"]).groups())
    b["K-2"] = int(re.search(r"E-3 の GROUNDED を失う行 (\d+)", K["K-2"]).group(1))
    b["K-3"] = int(re.search(r"E-4 の GROUNDED を失う行 ≤ (\d+)", K["K-3"]).group(1))
    m = re.search(r"E-5 の当期の fact に GROUNDED (\d+)〜(\d+)、かつ手がかり偽の (\d+) 行が P30E と同じ", K["K-4"])
    b["K-4"] = collections.OrderedDict([(u"当期の fact に GROUNDED", (int(m.group(1)), int(m.group(2)))), (u"手がかり偽の行", int(m.group(3)))])
    m = re.search(r"E-7 が (\d+) / (\d+) かつ E-9", K["K-5"])
    b["K-5"] = collections.OrderedDict([(u"赤", int(m.group(1))), (u"変異の本数", int(m.group(2)))])
    return b


def e7_value(copy_, bound):
    u"""E-7: 写した『変異 N 本全部赤』が封の変異の本数以上なら、封の変異は全部赤。写しが無ければ None。"""
    e7 = (copy_ or {}).get("E-7")
    if not e7 or e7.get(u"変異の本数") != e7.get(u"赤"):
        return None
    if e7[u"赤"] < bound[u"変異の本数"]:
        return None
    return collections.OrderedDict([(u"赤", bound[u"赤"]), (u"変異の本数", bound[u"変異の本数"]), (u"写した全部赤の本数", e7[u"赤"])])


def e9_value(copy_):
    u"""E-9: 写した『赤は <試験> の M 本だけ』から (赤の試験, ほかの赤)。ほかの赤 = pytest の failed − 赤の本数(tests/measure の名指しの試験以外の赤)。unittest の failures が違えば None。"""
    e9 = (copy_ or {}).get("E-9")
    if not e9:
        return None
    other = e9[u"pytest"]["failed"] - e9[u"赤の本数"]
    if e9[u"unittest failures"] != e9[u"赤の本数"] or other < 0:
        return None
    return collections.OrderedDict([(u"赤の試験", list(e9[u"赤の試験"])), (u"赤の本数", e9[u"赤の本数"]), (u"ほかの赤", other)])


def judge_from(cols, seal):
    u"""cols = {"moves": 集計の全体, "regress": regress_block, "inject": inject_columns, "link": E-1・E-8 の欄, "copy": E-7・E-9 の写し}。"""
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
    e1 = B["E-1"]
    put("E-1", rec_n is not None and voc_n is not None and within(v1[u"recipes 挿入"], e1[u"recipes 挿入"]) and v1[u"recipes 削除"] == e1[u"recipes 削除"]
        and within(v1[u"vocabulary 挿入"], e1[u"vocabulary 挿入"]) and v1[u"vocabulary 削除"] == e1[u"vocabulary 削除"] and v1[u"他の file"] == e1[u"他の file"], v1)
    c2 = rg[u"E-2 旗が偽の profile の byte 一致"]
    cn = collections.OrderedDict((p, v[u"byte が同じ書類"]) for p, v in c2.items())
    cd = set(v[u"書類"] for v in c2.values())
    e2, e2b = ij[u"E-2 T9 の第 2 便の記録との照らし"], B["E-2"]
    v2 = collections.OrderedDict([(u"97 byte が同じ書類(profile 間の最小)", min(cn.values()) if cn else None), (u"書類", e2b[u"書類"]), (u"profile", len(c2)),
                                  (u"P30E の結果と state が同じ行", e2[u"P30E の結果と state が T9 の第 2 便の記録と同じ行"]), (u"行", e2[u"行の数"])])
    put("E-2", len(c2) == len(BASE_PROFILES) and cd == {e2b[u"書類"]} and all(n == e2b[u"byte が同じ書類"] for n in cn.values()) and e2[u"id の集合が T9 の第 2 便の記録と同じ"] is True
        and e2[u"行の数"] == e2b[u"行"] and e2[u"P30E の結果と state が T9 の第 2 便の記録と同じ行"] == e2b[u"P30E の結果と state が同じ行"], v2)
    r3, e3 = rg[u"E-3 P32E 対 P30E"], B["E-3"]
    v3 = collections.OrderedDict([(u"GROUNDED を失う行", r3[u"GROUNDED を失う行"]), (u"動いた行", r3[u"動いた行"]), (u"動いた書類", r3[u"動いた書類"])])
    put("E-3", v3[u"GROUNDED を失う行"] == e3[u"GROUNDED を失う行"] and within(v3[u"動いた行"], e3[u"動いた行"]) and within(v3[u"動いた書類"], e3[u"動いた書類"]), v3)
    e4 = B["E-4"]
    lost = mv[u"E-4 GROUNDED を失う行"]
    v4 = collections.OrderedDict([(u"動いた行", mv[u"E-4 動いた行"]), (u"GROUNDED を失う行", lost[u"行"]), (u"うち札 真", lost[u"札"][u"真"]),
                                  (u"POINTER_NOT_FOUND → VALUE_MISMATCH", mv[u"E-4 POINTER_NOT_FOUND → VALUE_MISMATCH"][u"行"])])
    put("E-4", all(within(v4[k], e4[k]) for k in e4), v4)
    c5, e5 = ij[u"E-5 手がかり別の P32E"], B["E-5"]
    v5 = collections.OrderedDict([(k, c5[k]) for k in (u"手がかり真の行", u"当期の fact に GROUNDED", u"前期の fact を名指して VALUE_MISMATCH", u"別の fact に GROUNDED", u"その他",
                                                      u"手がかり偽の行", u"手がかり偽の行のうち P30E と同じ行")])
    put("E-5", v5[u"当期の fact に GROUNDED"] == e5[u"当期の fact に GROUNDED"] and within(v5[u"前期の fact を名指して VALUE_MISMATCH"], e5[u"前期の fact を名指して VALUE_MISMATCH"])
        and within(v5[u"別の fact に GROUNDED"], e5[u"別の fact に GROUNDED"]) and v5[u"手がかり偽の行"] == e5[u"手がかり偽の行"] and v5[u"手がかり偽の行のうち P30E と同じ行"] == e5[u"手がかり偽の行のうち P30E と同じ行"], v5)
    c6, e6 = ij[u"E-6 通した率と名指して原本"], B["E-6"]
    v6 = collections.OrderedDict([(u"通した率(P32E)", c6[u"通した率(P32E)"]), (u"名指して原本の割合", c6[u"名指して原本の割合"])])
    put("E-6", all(within(v6[k], e6[k]) for k in e6), v6)
    v7 = e7_value(cp, B["E-7"])
    put("E-7", v7 is not None and v7[u"赤"] == B["E-7"][u"赤"] and v7[u"変異の本数"] == B["E-7"][u"変異の本数"], v7 if v7 is not None else collections.OrderedDict([(u"赤", None)]))
    e8 = link[u"直した file(M)"]
    put("E-8", within(e8, B["E-8"]), collections.OrderedDict([(u"直した file(M)", e8), (u"新しい file(A)", link[u"新しい file(A)"]), (u"engine の挿入の行数", link[u"engine の挿入の行数"])]))
    v9 = e9_value(cp)
    put("E-9", v9 is not None and v9[u"赤の試験"] == B["E-9"][u"赤の試験"] and v9[u"ほかの赤"] == B["E-9"][u"ほかの赤"], v9 if v9 is not None else collections.OrderedDict([(u"赤の試験", None)]))
    c10, e10 = rg[u"E-10 VALUE_MISMATCH に動いた行の pointer の期"], B["E-10"]
    v10 = collections.OrderedDict([(u"行", c10[u"行"])] + [(p, c10[p]) for p in PERIODS5])
    put("E-10", within(v10[u"行"], e10[u"行"]) and v10[e10[u"期"]] == v10[u"行"], v10)
    K = collections.OrderedDict()
    K["K-1"] = {u"判定": HIT if E["E-2"][u"判定"] == HIT else MISS, u"値": collections.OrderedDict([("E-2", E["E-2"][u"判定"])])}
    K["K-2"] = {u"判定": HIT if v3[u"GROUNDED を失う行"] == B["K-2"] else MISS, u"値": collections.OrderedDict([(u"GROUNDED を失う行", v3[u"GROUNDED を失う行"])])}
    K["K-3"] = {u"判定": HIT if v4[u"GROUNDED を失う行"] <= B["K-3"] else MISS, u"値": collections.OrderedDict([(u"GROUNDED を失う行", v4[u"GROUNDED を失う行"])])}
    k4 = B["K-4"]
    K["K-4"] = {u"判定": HIT if within(v5[u"当期の fact に GROUNDED"], k4[u"当期の fact に GROUNDED"]) and v5[u"手がかり偽の行"] == k4[u"手がかり偽の行"]
                and v5[u"手がかり偽の行のうち P30E と同じ行"] == k4[u"手がかり偽の行"] else MISS,
                u"値": collections.OrderedDict([(u"当期の fact に GROUNDED", v5[u"当期の fact に GROUNDED"]), (u"手がかり偽の行のうち P30E と同じ行", v5[u"手がかり偽の行のうち P30E と同じ行"]),
                                               (u"手がかり偽の行", v5[u"手がかり偽の行"])])}
    K["K-5"] = {u"判定": HIT if v7 is not None and (v7[u"赤"], v7[u"変異の本数"]) == (B["K-5"][u"赤"], B["K-5"][u"変異の本数"]) and E["E-9"][u"判定"] == HIT else MISS,
                u"値": collections.OrderedDict([("E-7", E["E-7"][u"判定"]), ("E-9", E["E-9"][u"判定"])])}
    adopt = all(K[k][u"判定"] == HIT for k in K)
    return collections.OrderedDict([(u"E", E), (u"K", K), (u"採用", adopt), (u"欄", collections.OrderedDict((k, v[0]) for k, v in P.items()))])


def columns_from_records(R_):
    u"""記録 3 つ + T9 の第 2 便の記録(R_ = {"moves", "regress97", "inject", "t9"})から判定に使う欄を行・本・書類から数え直す(記録の集計・E の欄は使わない)。"""
    rg = R_["regress97"]
    return collections.OrderedDict([
        ("moves", moves_block(R_["moves"][u"本"])), ("regress", regress_block(rg[u"書類"])), ("inject", inject_columns(R_["inject"][u"行"], R_["t9"][u"行"])),
        ("link", rg[u"E-1・E-8 engine の差分"]), ("copy", dict((k, v) for k, v in rg[u"E-7・E-9 の写し"].items() if k in ("E-7", "E-9")))])


def build_E(R_, seal):
    return judge_from(columns_from_records(R_), seal)


def fmt(v):
    u"""表の『測った値』の字。list は ・ でつなぎ、それ以外は RM.fmt(真偽・小数 1 桁・桁区切りの整数・dict)。"""
    if isinstance(v, (list, tuple)):
        return u"・".join(fmt(x) for x in v)
    if isinstance(v, dict):
        return u"・".join(u"%s %s" % (k, fmt(x)) for k, x in v.items())
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
    out["t9"] = GEN.jload(os.path.join(root, T9_RECORD_REL))
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
