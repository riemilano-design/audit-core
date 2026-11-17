# -*- coding: utf-8 -*-
u"""封 docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md(NRE ― engine の inline XBRL の読み取りが「自己閉じの空の欄」を始まりの tag と読まないようにする直し)の測定。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。**engine の直しは ``adapters/xbrl/instance.py`` の式 1 行(封 §1)で、この script は engine を書き換えない。
材料は TSS の置き場(~/.cache/audit-core/tanshin-self-2026-11-14/)の ZIP 400 本と、``~/.cache/audit-core/`` の EDINET の 4 folder の ZIP、2026-11-09 の便が engine に渡す ZIP。

    python3 measure/xbrl_nil_read_engine_2026-11-17.py states --out PATH [--material DIR] [--procs N]      # 400 本の作り直し・NRE-1〜NRE-5 → fixtures/xbrl/nil_read_engine/states_2026-11-17.json
    python3 measure/xbrl_nil_read_engine_2026-11-17.py states --check [--material DIR] [--procs N]         # 書かずに作り直し、在る記録と比べる(時間の欄は除く)

実装の注(封が 1 通りに決めていない細部の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 便 NR の script(``measure/xbrl_nil_read_2026-11-17.py``)は ``load_module`` の形で読み、その部品(``fix_zip``・``engine_counter``・``independent_counter``・``fact_diff``・``htm_members``・``rate``・``leaves``・``route_of``・
  ``tanshin_0911`` の道具)と TSS の部品(``cut``・``wrap``・``judge_book``)を **呼ぶ**(写さない)。NR の script の ``build_record`` と ``states_job`` は呼ばない
  (どちらも「そのままの本が TSS の記録と同じ」「engine の指紋が TSS の記録と同じ」でなければ止まる作りで、engine を直した後では必ず止まる。守りを外すのではなく、呼ぶ関数を選ぶ)。
- 「直した engine のそのまま」の本 = ``TSS.judge_book`` の結果(今の engine)。比べる相手は便 NR の記録の「直した入力」の行(``fixtures/xbrl/nil_read/states_2026-11-17.json``)と TSS の記録の行。
- NR の記録の行は [本の #, 文の番号, 位置, そのままの state, 直した入力の state, reason が同じか] で、直した入力の reason の字は持たない。
  NRE-1 の「同じ」= state が NR の直した入力の state と同じ **かつ** (直した engine の reason が TSS の記録の reason と同じか) が NR の ``reason が同じか`` と同じ。
  (NR の ``reason が同じか`` は TSS の記録の reason と直した入力の reason の比べ。字そのものは記録に無いので、この比べで同じことを確かめる。)
- 行の鍵は (本の #, 文の番号, 位置)。直した engine の行・NR の行・TSS の行の鍵の集合が本ごとに違えば止まる(数を出さない)。
- NRE-2 の fact の差 = ``NR.fact_diff(直した engine のそのまま, 直した engine で自己閉じを消した入力)``(作られた = そのままに在って消した入力に無い・消えた = 逆)。
- NRE-4 の「直す前」= 旧い engine の blob(封の commit の ``instance.py``)を ``git show`` で読み(sha16 が TSS の時の値と同じことを確かめる)、memory の module として走らせた ``load_instance``。式の写しではない。
  比べる = ``facts`` の列が同じか(順も含む)。``load_instance`` の返り値の全体(contexts・textblocks・names も)が同じかも別に数える。
  読む ZIP = EDINET の 4 folder の ZIP(``zipfile.is_zipfile`` が真の file を folder の下の名前の順に)・2026-11-09 の便が ``verify_document`` に渡す ZIP(zb)と ``build_raw_claims`` に渡す ZIP(zm)。
- NRE-5 の「始まりの位置」= ``<ix:nonFraction`` の字が在る位置 p のうち、式をその位置に当てて(``pattern.match(raw, p)``)一致するもの。直す前の式の一致で属性の列が ``/`` で終わるものは数えない(自己閉じ)は数えない。
  直した式の側は一致を全部数える(式が自己閉じを拾ってしまえば数が増える)。
  (``finditer`` で数えると、直す前の式は自己閉じの一致が次の fact の始まりを飲み込むので、飲み込まれた本物の fact が直した式の側にだけ数えられて数が合わない。位置ごとに当てれば式の違いだけを見る。)
  本ごとに 2 つの数と位置の集合が同じかを持つ。直した式が実際に ``finditer`` で拾う数も本ごとの全体として別に持つ。直す前の式・直した式の写しは script に置き、門が旧い blob・今の engine の行と同じことを確かめる。
- 記録に文・span・値・要素名・context の字・会社名・証券コード・docID は持たない。時間(秒)以外は 2 回走らせて byte で同じ。率は整数の分子・分母を並べ、% は小数 1 桁。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import time
import types
import zipfile

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


NR = load_module("xbrl_nil_read_2026-11-17.py", "nil_read_for_nil_read_engine")        # 便 NR の script(部品を呼ぶ)
TSS = NR.TSS
ST = NR.ST
TS = NR.TS
Stop = ST.Stop
I = NR.I
VD = NR.VD

SEAL_REL = "docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md"
SEAL_COMMIT = "36ca78f1"
SCRIPT_REL = "measure/xbrl_nil_read_engine_2026-11-17.py"
REC_DIR_REL = "fixtures/xbrl/nil_read_engine"
STATES_REL = REC_DIR_REL + "/states_2026-11-17.json"
POPULATION_REL = ST.POPULATION_REL
TSS_STATES_REL = "fixtures/xbrl/tanshin_self/states_2026-11-14.json"
NR_STATES_REL = "fixtures/xbrl/nil_read/states_2026-11-17.json"
INSTANCE_REL = "adapters/xbrl/instance.py"
INSTANCE_GIT_PATH = "audit-core/" + INSTANCE_REL

#: 入力(# , path, sha256)。違えば止まる。門が実物と 1 つずつ照らす
INPUTS = (
    (1, "fixtures/xbrl/tanshin_self/population_2026-11-14.json", "48ba8e5574be70d85b3d1affacc9403cffbfc698f529c095c6c882cd8ccfa9b0"),
    (2, "fixtures/xbrl/tanshin_self/states_2026-11-14.json", "00414222cfe8cb05d0a1fed3d3e5a09bacafa6547f1675975a3cebd3e4ef70f6"),
    (3, "measure/xbrl_tanshin_self_2026-11-14.py", "fa603d1c2dbfdee7c3ad4197ab9c4a9f1428419ada57293f346418bc0997aeb6"),
    (4, "measure/xbrl_tanshin_self_stage_2026-11-14.py", "4ed60b591366dd65a431dba5348aff6edb3889676d8e9a4154a5b0298486f7f9"),
    (5, "measure/xbrl_tanshin_2026-11-09.py", "b7ea491bf5cd34c4976bde86c4329583e0d9af09ec8895ea0caf48491492b5bd"),
    (6, "fixtures/xbrl/tanshin/states_2026-11-09.json", "6779b451b30aa7619923cbc8c390049f682deeb7bf5e198ddb21c9005b6362d4"),
    (7, "measure/xbrl_nil_read_2026-11-17.py", "f1489d091a55d420052b8f208d344d237b7f168ac0d66b6f2170b7d5f35e7ac4"),
    (8, "fixtures/xbrl/nil_read/states_2026-11-17.json", "16c07159f88973932f70e9c422734330dcdf7893b6ca26ed2898623b614c3864"),
)

PROFILE = "P33E"
#: 封の commit の ``instance.py`` の sha16(TSS の時の値。旧い blob の確かめに使う)
OLD_INSTANCE_SHA16 = "f2d9e040f19adebf"
#: 直す前の式・直した式(封 §1。写し。門が旧い blob・今の engine の行と同じことを確かめる)
OLD_FACT_RE_SRC = r'<ix:nonFraction([^>]*)>(.*?)</ix:nonFraction>'
NEW_FACT_RE_SRC = r'<ix:nonFraction([^>]*)(?<!/)>(.*?)</ix:nonFraction>'
OLD_FACT_RE = re.compile(OLD_FACT_RE_SRC, re.S)
NEW_FACT_RE = re.compile(NEW_FACT_RE_SRC, re.S)
START_LITERAL = "<ix:nonFraction"
STATE_G = u"GROUNDED"
STATES = tuple(TS.STATES)
#: NRE-4 の folder(EDINET の 4 つ。数は NR の棚卸しの封の数と同じ。違えば止まる)
EDINET_FOLDERS = collections.OrderedDict([("edinet", 281), ("edinet-demo-cabocia", 3), ("edinet-fresh-2026-10-21", 40), ("edinet-prior-2026-11-02", 94)])
N_0911 = 17
FP_KEYS = NR.FP_KEYS
LIMITS = (
    u"直す前の「そのまま」の行は TSS の記録(直す前の engine)と便 NR の記録(直した入力)を字で読んだもので、engine を戻して作り直していない。NRE-4 と NRE-5 の「直す前」だけは旧い engine の blob・式の写しで走らせた",
    u"数えたのは TSS の 400 本の states(判定)の差だけ。型の読み(AI の席)・注入(1b)・near・第 2 便・便 PS のサマリーの数は、直した engine で取り直していない。それらの記録は直す前の engine の数のまま",
    u"NRE-1 の reason の比べは、便 NR の記録が直した入力の reason の字を持たないため「TSS の記録の reason と同じか」の比べで置いた(字そのものの一致ではない)",
    u".htm の経路のほかの読み取り(入れ子・ix:continuation・負の表記の format・属性の値の中の >)は見ていない",
    u"英文短信の側(sales/)は load_instance を呼ばないことを grep で見ただけで、数は測らない。この直しで「短信の概況の文を engine が正しく結べる」とは言えない",
    u"NRE-4 の .xbrl の経路の確かめは手元の ZIP(EDINET の 4 folder と 2026-11-09 の便の ZIP)だけで、EDINET 全体の標本ではない",
    u"行は [本の #, 文の番号, 位置, 直した engine の state, NR の直した入力の state と同じか, TSS の state] だけで、文・span・値・要素名・context の字は持たない")
ROW_COLUMNS = (u"本の #", u"文の番号", u"位置", u"直した engine の state", u"NR の直した入力の state と同じか", u"TSS の state")
BOOK_COLUMNS = (u"本の #", u"NRE-1 で違う行", u"作られた fact", u"消えた fact", u"直す前の式の始まり(自己閉じでない)", u"直した式が拾う始まり", u"始まりの位置の集合が違う(1 = 違う)", u"直した式が finditer で拾う数")


def rate(n, d):
    return NR.rate(n, d)


def jsonable(o):
    return NR.jsonable(o)


# ======================================================================================================
# NRE-5(式の写し)
def start_positions(raw, pattern):
    u"""``<ix:nonFraction`` の字が在る位置のうち、``pattern`` をその位置に当てて(``pattern.match(raw, p)``)一致するものの [(位置, 属性の列が / で終わるか)] の列(位置の順)。"""
    out = []
    p = raw.find(START_LITERAL)
    while p >= 0:
        m = pattern.match(raw, p)
        if m:
            out.append((p, m.group(1).endswith("/")))
        p = raw.find(START_LITERAL, p + 1)
    return out


def start_block(zb):
    u"""包んだ ZIP の ``XBRL/PublicDoc/`` の ``.htm`` の全部で (直す前の式の始まり(自己閉じでないもの)の数・直した式が拾う始まりの数・位置の集合が違う・直した式が finditer で拾う数)。
    位置は (member の番号, 位置)。直す前の式の側は属性の列が ``/`` で終わる一致(自己閉じ)を除き、直した式の側は一致を全部数える(式が自己閉じを拾えば数が増えて違いに出る)。"""
    old_set, new_set, nfind = set(), set(), 0
    for i, (_n, data) in enumerate(NR.htm_members(zb)):
        raw = data.decode("utf-8", "ignore")
        old_set.update((i, p) for p, selfc in start_positions(raw, OLD_FACT_RE) if not selfc)
        new_set.update((i, p) for p, _selfc in start_positions(raw, NEW_FACT_RE))
        nfind += len(NEW_FACT_RE.findall(raw))
    return len(old_set), len(new_set), 1 if old_set != new_set else 0, nfind


# ======================================================================================================
# 旧い engine(NRE-4)
def git_blob(commit, path, root=ROOT):
    u"""``git show <commit>:<path>`` の bytes。読めなければ止める。"""
    repo = os.path.dirname(root)
    try:
        return subprocess.check_output(["git", "-C", repo, "show", "%s:%s" % (commit, path)], stderr=subprocess.STDOUT)
    except (subprocess.CalledProcessError, OSError):
        raise Stop(u"**旧い engine の blob を git から読めない。止める**")


def old_engine_module(src_bytes):
    u"""旧い ``instance.py`` の bytes から memory の module を作る(``sys.modules`` に登録しない)。"""
    if hashlib.sha256(src_bytes).hexdigest()[:16] != OLD_INSTANCE_SHA16:
        raise Stop(u"**旧い engine の instance.py の sha16 が TSS の時の値と違う。止める**")
    mod = types.ModuleType("old_instance_for_nil_read_engine")
    mod.__file__ = os.path.join(ROOT, INSTANCE_REL)
    exec(compile(src_bytes.decode("utf-8"), mod.__file__, "exec"), mod.__dict__)
    return mod


def compare_zip(old_mod, new_mod, zb):
    u"""(facts の列が同じか, 返り値の全体が同じか, .xbrl の経路か)。"""
    a, b = old_mod.load_instance(zb), new_mod.load_instance(zb)
    return a["facts"] == b["facts"], a == b, NR.route_of(zb) == NR.ROUTE_XBRL


def edinet_zip_paths(base, folder):
    top = os.path.join(base, folder)
    out = []
    for dp, dns, fns in os.walk(top):
        dns.sort()
        for fn in sorted(fns):
            p = os.path.join(dp, fn)
            if zipfile.is_zipfile(p):
                out.append(p)
    return out


def read_file(p):
    with io.open(p, "rb") as fh:
        return fh.read()


def zips_0911(root=ROOT):
    u"""2026-11-09 の便が engine に渡す ZIP。[(zb, zm)]。便の表の順。"""
    out = []
    for (_n, _code, _number, _sha, _chars, _claims, row, text) in TS.load_books(root):
        zb = TS.GEN.read_zip(row, TS.GEN.EXISTING_CACHES)
        zm = TS.PR.build_modified_zip(zb, text)[0]
        out.append((zb, zm))
    return out


def check_material_counts(counts, n_0911):
    u"""EDINET の folder の ZIP の数が封(便 NR の棚卸し)の数・2026-11-09 の便の本の数が 17 と違えば止める(数を出さない)。"""
    for name, want in EDINET_FOLDERS.items():
        if counts.get(name) != want:
            raise Stop(u"**EDINET の folder の ZIP の数が封の数と違う(%s)。止める**" % name)
    if n_0911 != N_0911:
        raise Stop(u"**2026-11-09 の便の ZIP の数が 17 と違う。止める**")


def nre4_block(old_mod, new_mod, groups):
    u"""``groups`` = [(群の名, [ZIP の bytes を返す関数の列])]。群ごとに [読んだ ZIP の数, 違う本(facts)の数, 全体が違う本の数, .xbrl の経路でない本の数, 違う本の番号]。"""
    per = collections.OrderedDict()
    for name, getters in groups:
        n = diff = diff_all = non_xbrl = 0
        idx = []
        for i, get in enumerate(getters):
            same, same_all, xb = compare_zip(old_mod, new_mod, get())
            n += 1
            diff += 0 if same else 1
            diff_all += 0 if same_all else 1
            non_xbrl += 0 if xb else 1
            if not same:
                idx.append(i)
        per[name] = collections.OrderedDict([(u"読んだ ZIP", n), (u"facts の列が違う ZIP", diff), (u"返り値の全体が違う ZIP", diff_all), (u".xbrl の経路でない ZIP", non_xbrl), (u"facts の列が違う ZIP の番号(群の中の順)", idx)])
    return per


def nre4_total(per):
    return collections.OrderedDict([
        (u"読んだ ZIP の合計", sum(v[u"読んだ ZIP"] for v in per.values())), (u"facts の列が違う ZIP の合計", sum(v[u"facts の列が違う ZIP"] for v in per.values())),
        (u"返り値の全体が違う ZIP の合計", sum(v[u"返り値の全体が違う ZIP"] for v in per.values())), (u".xbrl の経路でない ZIP の合計", sum(v[u".xbrl の経路でない ZIP"] for v in per.values()))])


# ======================================================================================================
# 1 本
def row_key(r):
    return (r[0], r[1])


def nr_rows_by_book(nr_rec):
    out = collections.OrderedDict()
    for r in nr_rec[u"行"]:
        out.setdefault(r[0], []).append(r)
    return out


def pair_book(n, new_rows, tss_rows, nr_rows):
    u"""1 本の行の対。new_rows = 直した engine の行(TSS の行の形)・tss_rows = TSS の記録の行・nr_rows = NR の記録の行([本の #, 文の番号, 位置, そのまま, 直した入力, reason が同じか])。
    返す = [[本の #, 文の番号, 位置, 直した engine の state, NR の直した入力の state と同じか, TSS の state]]。鍵の並びが 3 つで違えば止める。"""
    k_new = [row_key(r) for r in new_rows]
    if k_new != [row_key(r) for r in tss_rows] or k_new != [(r[1], r[2]) for r in nr_rows] or any(r[0] != n for r in nr_rows):
        raise Stop(u"**行の鍵の並びが 直した engine・TSS の記録・NR の記録で違う(# %d)。止める**" % n)
    out = []
    for rn, rt, rr in zip(new_rows, tss_rows, nr_rows):
        if rt[2] != rr[3]:
            raise Stop(u"**NR の記録の「そのまま」の state が TSS の記録と違う(# %d)。止める**" % n)
        same = rn[2] == rr[4] and ((rn[3] == rt[3]) == rr[5])
        out.append([n, rn[0], rn[1], rn[2], bool(same), rt[2]])
    return out


def states_job(args):
    u"""1 本: 直した engine の「そのまま」の本(``judge_book``)→ 行の対(NR・TSS の記録と)→ fact の差 → 始まりの位置。"""
    n, grp, kind, sha, path, tss_book, nr_rows = args
    if not os.path.exists(path):
        raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める**" % n)
    zb = read_file(path)
    if ST.sha256_bytes(zb) != sha:
        raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % n)
    book = TSS.judge_book(n, grp, kind, sha, zb)
    cut = book[u"切り出し"] == TSS.CUT_OK
    if cut != (tss_book[u"切り出し"] == TSS.CUT_OK):
        raise Stop(u"**切り出しの成否が TSS の記録と違う(# %d)。止める**" % n)
    res = collections.OrderedDict([(u"#", n), (u"群", grp), (u"切れた", cut)])
    if not cut:
        if nr_rows:
            raise Stop(u"**切れない本に NR の記録の行が在る(# %d)。止める**" % n)
        return res
    text, _head, _why = TSS.cut(zb)
    wrapped, _nfiles = TSS.wrap(zb, text)
    fixed_zb, nil = NR.fix_zip(wrapped)
    c_asis, c_fixed = NR.engine_counter(wrapped), NR.engine_counter(fixed_zb)
    made, gone, swap = NR.fact_diff(c_asis, c_fixed)
    res[u"行の対"] = pair_book(n, book[u"行"], tss_book[u"行"], nr_rows)
    res[u"fact の差"] = (made, gone, swap)
    res[u"独立の読みと同じ"] = NR.independent_counter(wrapped) == c_asis
    res[u"自己閉じの数"] = nil
    res[u"始まり"] = start_block(wrapped)
    return res


# ======================================================================================================
# 数える
def per_book_table(books):
    per = []
    for b in books:
        if not b[u"切れた"]:
            continue
        made, gone, _swap = b[u"fact の差"]
        old_n, new_n, diff, nfind = b[u"始まり"]
        per.append([b[u"#"], sum(1 for r in b[u"行の対"] if not r[4]), made, gone, old_n, new_n, diff, nfind])
    return per


def rows_of(books):
    return [r for b in books if b[u"切れた"] for r in b[u"行の対"]]


def nre1_block(rows, per):
    bad = [r for r in rows if not r[4]]
    return collections.OrderedDict([
        (u"切れた本", len(per)), (u"行の数", len(rows)),
        (u"NR の直した入力の行と違う行", rate(len(bad), len(rows))),
        (u"NR の直した入力の行と違う行を持つ本", sum(1 for p in per if p[1] > 0)),
        (u"NR の直した入力の行と同じ本", sum(1 for p in per if p[1] == 0))])


def nre2_block(per, books):
    cut = [b for b in books if b[u"切れた"]]
    return collections.OrderedDict([
        (u"切れた本", len(per)), (u"自己閉じの数(消した数)", sum(b[u"自己閉じの数"] for b in cut)),
        (u"作られた fact", sum(p[2] for p in per)), (u"消えた fact", sum(p[3] for p in per)),
        (u"作られた fact を持つ本", sum(1 for p in per if p[2] > 0)), (u"消えた fact を持つ本", sum(1 for p in per if p[3] > 0)),
        (u"独立の読みと直した engine の fact が同じ本", sum(1 for b in cut if b[u"独立の読みと同じ"]))])


def transition_table(rows):
    c = collections.Counter((r[5], r[3]) for r in rows)
    return collections.OrderedDict((u"%s → %s" % (a, b), c.get((a, b), 0)) for a in STATES for b in STATES)


def nre3_block(rows):
    changed = [r for r in rows if r[5] != r[3]]
    only_new = [r for r in rows if r[5] != STATE_G and r[3] == STATE_G]
    only_old = [r for r in rows if r[5] == STATE_G and r[3] != STATE_G]
    books = sorted(set(r[0] for r in changed))
    return collections.OrderedDict([
        (u"行の数", len(rows)), (u"state の移り変わり(TSS の記録 → 直した engine)", transition_table(rows)),
        (u"state が変わった行", rate(len(changed), len(rows))), (u"state が変わった行を持つ本", len(books)), (u"state が変わった行を持つ本の #", books),
        (u"直した engine でだけ値が合う行", len(only_new)), (u"TSS の記録(直す前)でだけ値が合う行", len(only_old))])


def nre5_block(per):
    return collections.OrderedDict([
        (u"包んだ本", len(per)), (u"直す前の式の始まり(自己閉じでない)の合計", sum(p[4] for p in per)), (u"直した式が拾う始まりの合計", sum(p[5] for p in per)),
        (u"始まりの位置の集合が違う本", sum(p[6] for p in per)), (u"始まりの数が違う本", sum(1 for p in per if p[4] != p[5])),
        (u"直した式が finditer で拾う数の合計", sum(p[7] for p in per))])


def prediction_numbers(b1, b2, b3, b4, b5):
    u"""予測 NRE-1〜NRE-5 の判定に要る分子と分母(当たり・外れの字は書かない)。"""
    return collections.OrderedDict([
        (u"NRE-1 NR の直した入力の行と違う本 / 切れた本", collections.OrderedDict([(u"分子", b1[u"切れた本"] - b1[u"NR の直した入力の行と同じ本"]), (u"分母", b1[u"切れた本"])])),
        (u"NRE-1 NR の直した入力の行と違う行 / 行", b1[u"NR の直した入力の行と違う行"]),
        (u"NRE-2 作られた fact・消えた fact", collections.OrderedDict([(u"作られた fact", b2[u"作られた fact"]), (u"消えた fact", b2[u"消えた fact"])])),
        (u"NRE-3 state が変わった行 / 行", b3[u"state が変わった行"]),
        (u"NRE-3 state が変わった行を持つ本", b3[u"state が変わった行を持つ本"]),
        (u"NRE-3 直した engine でだけ値が合う行・直す前でだけ値が合う行", collections.OrderedDict([(u"直した engine でだけ", b3[u"直した engine でだけ値が合う行"]), (u"直す前でだけ", b3[u"TSS の記録(直す前)でだけ値が合う行"])])),
        (u"NRE-4 facts の列が違う ZIP / 読んだ ZIP", collections.OrderedDict([(u"分子", b4[u"facts の列が違う ZIP の合計"]), (u"分母", b4[u"読んだ ZIP の合計"])])),
        (u"NRE-5 直す前の式の始まり(自己閉じでない)と直した式が拾う始まり", collections.OrderedDict([
            (u"直す前の式の始まりの合計", b5[u"直す前の式の始まり(自己閉じでない)の合計"]), (u"直した式が拾う始まりの合計", b5[u"直した式が拾う始まりの合計"]),
            (u"違う本", b5[u"始まりの位置の集合が違う本"]), (u"本", b5[u"包んだ本"])]))])


# ======================================================================================================
# 入力・記録
def load_json(p):
    return NR.load_json(p)


def check_inputs(root):
    u"""入力の sha256 が表と同じか。違えば止める。7 番目・8 番目(NR の script と記録)の表の値は NR の記録の字で書く。"""
    out = []
    for no, rel, want in INPUTS:
        p = os.path.join(root, rel)
        if not os.path.isfile(p) or ST.sha256_file(p) != want:
            raise Stop(u"**入力 %d の sha256 が表と違う。止める**" % no)
        out.append(collections.OrderedDict([(u"#", no), (u"path", rel), (u"sha256", want)]))
    return out


def engine_fp(tss_rec):
    u"""今の engine の指紋と、直す前の指紋(TSS の記録のもの)。同じなら止める(直した engine が走っていない)。"""
    fp = VD.engine_fingerprint()
    now = collections.OrderedDict((k, fp[k]) for k in FP_KEYS)
    was = collections.OrderedDict((k, tss_rec[u"engine の指紋"][k]) for k in FP_KEYS)
    if now == was:
        raise Stop(u"**engine の指紋が直す前(TSS の記録)と同じ。直した engine が走っていない。止める**")
    return now, was


def material_dir(material, out, root=ROOT):
    return NR.material_dir(material, out, root)


def build_record(root=ROOT, procs=1, material=None, out=None, say=print, clock=time.time, base=None, old_src=None, groups=None):
    u"""400 本の作り直し・NRE-1〜NRE-5 を数えた記録(OrderedDict)を返す。書かない。"""
    mat, prod = material_dir(material, out, root)
    inputs = check_inputs(root)
    pop = ST.validate_population(ST.read_population(root), ST.N_ROWS, ST.GROUP_COUNTS)
    NR.check_population(root, pop)
    tss_rec = load_json(os.path.join(root, TSS_STATES_REL))
    nr_rec = load_json(os.path.join(root, NR_STATES_REL))
    fp_now, fp_was = engine_fp(tss_rec)
    if tss_rec[u"profile"] != PROFILE or nr_rec[u"profile"] != PROFILE:
        raise Stop(u"**TSS・NR の記録の profile が %s でない。止める**" % PROFILE)
    by_book = dict((b[u"#"], b) for b in tss_rec[u"本"])
    nr_by_book = nr_rows_by_book(nr_rec)
    if sorted(by_book) != [r[0] for r in pop]:
        raise Stop(u"**TSS の記録の本が母集団とそろわない。止める**")
    for (n, _g, _k, sha) in pop:
        if not os.path.exists(os.path.join(mat, sha + u".zip")):
            raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める**" % n)
        if by_book[n][u"ZIP の sha256"] != sha:
            raise Stop(u"**TSS の記録の ZIP の sha256 が表と違う(# %d)。止める**" % n)
    before = ST.names_snapshot(mat)
    jobs = [(n, g, k, sha, os.path.join(mat, sha + u".zip"), by_book[n], nr_by_book.get(n, [])) for (n, g, k, sha) in pop]
    say(u"states %d 本 × %s ― procs %d" % (len(jobs), PROFILE, procs))
    t0 = clock()
    books = TS.NF.map_pool(states_job, jobs, procs)
    if before != ST.names_snapshot(mat):
        raise Stop(u"**材料の置き場の件数か名前が変わった。止める**")
    rows = rows_of(books)
    per = per_book_table(books)
    b1, b2, b3, b5 = nre1_block(rows, per), nre2_block(per, books), nre3_block(rows), nre5_block(per)
    # NRE-4
    base = base or NR.cache_base_dir()
    if old_src is None:
        old_src = git_blob(SEAL_COMMIT, INSTANCE_GIT_PATH, root)
    old_mod = old_engine_module(old_src)
    if groups is None:
        paths = collections.OrderedDict((name, edinet_zip_paths(base, name)) for name in EDINET_FOLDERS)
        z11 = zips_0911(root)
        check_material_counts(collections.OrderedDict((name, len(v)) for name, v in paths.items()), len(z11))
        groups = [(name, [(lambda p=p: read_file(p)) for p in v]) for name, v in paths.items()]
        groups.append((u"2026-11-09 の便の verify_document に渡す ZIP", [(lambda z=z[0]: z) for z in z11]))
        groups.append((u"2026-11-09 の便の build_raw_claims に渡す ZIP", [(lambda z=z[1]: z) for z in z11]))
    per4 = nre4_block(old_mod, I, groups)
    b4 = nre4_total(per4)
    elapsed = clock() - t0
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"NRE(engine の inline XBRL の読み取りが自己閉じの空の欄を始まりの tag と読まないようにする直し)― 400 本の作り直し・NRE-1〜NRE-5(0 USD・通信なし)"
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"入力"] = inputs
    rec[u"engine の指紋(直した後)"] = fp_now
    rec[u"engine の指紋(直す前。TSS の記録のもの)"] = fp_was
    rec[u"profile"] = PROFILE
    rec[u"材料"] = collections.OrderedDict([(u"置き場", ST.display_path(mat) if prod else u"使い捨ての置き場(本番の folder ではない)"), (u"表と一致した ZIP", len(pop))])
    rec[u"直した式(封 §1)"] = collections.OrderedDict([(u"前", OLD_FACT_RE_SRC), (u"後", NEW_FACT_RE_SRC)])
    rec[u"NRE-1(直した engine のそのままの行 対 NR の記録の直した入力の行)"] = b1
    rec[u"NRE-2(直した engine の fact の差。そのまま 対 自己閉じを消した入力)"] = b2
    rec[u"NRE-3(直した engine のそのままの行 対 TSS の記録の行)"] = b3
    rec[u"NRE-4(.xbrl の経路の ZIP。旧い engine の blob 対 今の load_instance)"] = collections.OrderedDict([(u"群ごと", per4), (u"合計", b4)])
    rec[u"NRE-5(直す前の式の始まり 対 直した式の始まり。位置ごと)"] = b5
    rec[u"予測の判定に要る数(NRE-1〜NRE-5。当たり・外れは結果の文書で)"] = prediction_numbers(b1, b2, b3, b4, b5)
    rec[u"本ごとの欄"] = list(BOOK_COLUMNS)
    rec[u"本ごと(切れた本だけ)"] = per
    rec[u"限界"] = list(LIMITS)
    rec[u"行の欄"] = list(ROW_COLUMNS)
    rec[u"時間(秒)"] = round(elapsed, 1)
    rec[u"key_leaks"] = []
    rec[u"行"] = rows
    return rec


def check_text(rec, text, key_value=None):
    scan = text.replace(SEAL_REL, u"")
    for _no, rel, _sha in INPUTS:
        scan = scan.replace(rel, u"")
    scan = scan.replace(OLD_FACT_RE_SRC, u"").replace(NEW_FACT_RE_SRC, u"")
    TSS.check_clean(rec, scan, key_value)


def record_text(rec, key_value=None):
    text = ST.dumps_record(rec)
    check_text(rec, text, key_value)
    return text


def run_states(root=ROOT, procs=1, out=None, material=None, say=print, check=False, **kw):
    if not check and out is None:
        raise Stop(u"**--out を指定する(書かずに比べるなら --check)。止める**")
    out = os.path.abspath(out) if out else None
    if out and os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    rec = build_record(root=root, procs=procs, material=material, out=out, say=say, **kw)
    text = record_text(rec)
    if check:
        want = os.path.join(root, STATES_REL)
        if not os.path.isfile(want):
            raise Stop(u"**在る記録が無い。止める**")
        cur = load_json(want)
        cur[u"時間(秒)"] = 0
        rec2 = collections.OrderedDict(rec)
        rec2[u"時間(秒)"] = 0
        if ST.dumps_record(cur) != ST.dumps_record(rec2):
            raise Stop(u"**作り直した記録が在る記録と違う(時間の欄は除く)。止める**")
        say(u"--check: 在る記録と同じ(時間の欄は除く)")
        return rec
    ST.write_text_exclusive(out, text)
    say(u"-> %s(行 %d)" % (os.path.basename(out), len(rec[u"行"])))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("states")
    a.add_argument("--root", default=ROOT)
    a.add_argument("--out", default=None)
    a.add_argument("--check", action="store_true")
    a.add_argument("--material", default=None)
    a.add_argument("--procs", type=int, default=1)
    a_ = ap.parse_args(argv)
    if a_.cmd == "states":
        run_states(root=a_.root, procs=a_.procs, out=a_.out, material=a_.material, check=a_.check)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
