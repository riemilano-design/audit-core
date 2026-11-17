# -*- coding: utf-8 -*-
"""封 docs/XBRL_TANSHIN_SELF_INJECT_SEAL_2026-11-14.md(TSS の便 1b ― 短信の概況の文に誤りを 1 件ずつ入れ、同じ短信の財務諸表に当てて止めるかを測る)の測定の門。封 §0-2・§1・§2・§3・§5。

**この門が縛るもの**(結果の門 ``test_xbrl_tanshin_self_inject_result.py`` は次の段。記録・文書・読んだ札を縛る)

1. 封の字: §3 が V-1〜V-11 の 11 行・種 20261114・cap 10・profile の対 (P33E, P33E)・r の 4 つ・本の名前の形・refs の作り・検証の関数・通した行の札 (a)〜(d)・記録の path。
2. 封の字と script の定数が同じ(定数を 1 つずつ替えると赤になる)。
3. engine 0 行: 封の commit から HEAD まで ``core/``・``adapters/``・``measure/lib``・``measure/inject.py``・2026-11-09 の便の script・TSS と第 2 便の script・封・記録を触っていない(未 commit の変更も見る)。
4. 順序: 封 bcc244ae ⊏ script・この門(**commit の順**。未 commit は赤。skip にしない)。
5. profile の対の差し替え: ``with`` の中で仕掛けが引く名前に届く・出たあとに戻る(例外でも)・戻らなければ止める・届かなければ止める・切り替え 2 つは中で真・出たあとで偽。
6. refs の作り(同じ key は最初の 1 件・None は飛ばす・float にできないものは飛ばして数える)・1 本の注入(丙にだけ期の名前の読み替え・種・cap・名前・検証の関数・土台の確かめ)・記録(欄・集計・覆い・byte の再現・文や値を持たない・止める所)・紙と札。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``・``CONST_MUTANTS``)。この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import ast
import collections
import contextlib
import copy
import importlib.util
import inspect
import io
import json
import os
import re
import shutil
import sys
import tempfile
import types
import unittest
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "measure"))


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


G2 = load_module("tests/measure/test_xbrl_tanshin_self2_seal.py", "tanshin_self2_seal_gate_helpers_for_inject_seal")      # 第 2 便の門の道具(fixture・iXBRL の作り物)。門としては走らせない
G1 = G2.G1
MS = load_module("measure/xbrl_tanshin_self_inject_2026-11-14.py", "tanshin_self_inject_script_for_seal_gate")
PR = G1.PR
SGR = G1.SGR      # 宣言された遷移の部品(2026-11-17 NRE: nre_record_fingerprint_ok)。第 2 便の門が読み込んだもの。門としては走らせない
S2, TSS, ST, TS = MS.S2, MS.TSS, MS.ST, MS.TS
patched, guard, tmpdir, eqp, expect_stop, strip_time = G1.patched, G1.guard, G1.tmpdir, G1.eqp, G1.expect_stop, G1.strip_time

SEAL_REL = "docs/XBRL_TANSHIN_SELF_INJECT_SEAL_2026-11-14.md"
SEAL_COMMIT_SHORT = "bcc244ae"                 # 封の commit(literal に留める。script の定数と違えば script_problems が赤)
SCRIPT_REL = "measure/xbrl_tanshin_self_inject_2026-11-14.py"
GATE_REL = "tests/measure/test_xbrl_tanshin_self_inject_seal.py"
LATER_GATE_REL = "tests/measure/test_xbrl_tanshin_self_inject_result.py"
DOC_REL = "docs/XBRL_TANSHIN_SELF_INJECT_RESULT_2026-11-14.md"
INJECT_REL = "fixtures/xbrl/tanshin_self/inject_2026-11-14.json"
PASSED_TYPES_REL = "fixtures/xbrl/tanshin_self/inject_passed_types_2026-11-14.json"
SCRIPT_RELS = (SCRIPT_REL,)
S2_REL = "measure/xbrl_tanshin_self2_2026-11-14.py"
TSS_REL = "measure/xbrl_tanshin_self_2026-11-14.py"
STAGE_REL = "measure/xbrl_tanshin_self_stage_2026-11-14.py"
TS_REL = "measure/xbrl_tanshin_2026-11-09.py"
TSS_SEAL_REL = "docs/XBRL_TANSHIN_SELF_SEAL_2026-11-14.md"
S2_SEAL_REL = "docs/XBRL_TANSHIN_SELF2_SEAL_2026-11-14.md"
RECDIR = "fixtures/xbrl/tanshin_self/"
POPULATION_REL = RECDIR + "population_2026-11-14.json"
STATES_REL = RECDIR + "states_2026-11-14.json"
INTERIM_REL = RECDIR + "states_interim_2026-11-14.json"
#: 封の commit から 0 行でなければならない path(engine・lib・仕掛け・前の便の script・封・記録。この便の記録 inject_*.json は後で足すので folder ごとは指さない)
NOT_TOUCHED_RELS = ("adapters", "core", "measure/lib", "measure/inject.py", TS_REL, "measure/xbrl_tanshin_fetch_2026-11-09.py", TSS_REL, STAGE_REL, S2_REL, TSS_SEAL_REL, S2_SEAL_REL,
                    POPULATION_REL, STATES_REL, INTERIM_REL, RECDIR + "near_2026-11-14.json", RECDIR + "near_types_2026-11-14.json", RECDIR + "vm_types_2026-11-14.json",
                    RECDIR + "vm_types_subreading_2026-11-14.json", "fixtures/xbrl/tanshin")
PRED_IDS = tuple("V-%d" % i for i in range(1, 12))
SEAL_PHRASES = (
    u"種は整数 `20261114`",
    u"本の名前の引数は `\"B\" + #`(例 `B7`・`B253`)",
    u"cap は型ごと・1 本あたり 10",
    u"r ∈ −0.10・−0.03・0.03・0.10",
    u"**1 回の検証で変えるのは 1 件だけ。**",
    u"`(\"P33E\", \"P33E\")`・`\"P33E\"`・`\"P33E\"`",
    u"**`with` の中だけ**",
    u"出るときに必ず戻す",
    u"`with TS.NS.yen_scan_on(): with TS.TY.t5_yen_on():`",
    u"出たあと偽に戻っていることを記録に書く",
    u"同じ `key` は最初の 1 件だけ採る",
    u"`float` にできない fact が出たら止めずに飛ばし、飛ばした数を本ごとに記録する",
    u"`verify = lambda _z, p, t: VD.verify_document(TSS.wrap(zb2, t)[0], p)`",
    u"`inject_text_ts` の第 1 引数には無改変の文で包んだ ZIP を渡す",
    u"**通した行が 1 行でも在れば**",
    u"(a) engine が誤りを通した・(b) 注入した値が偶然ほかの正しい fact の値になった(誤りとは言えない)・(c) 対応付けが別の claim を指した・(d) 読んでも分けられない",
    u"記録には 本の #・id・型・付けた札 だけ",
    u"鍵や文が混ざっていないことを記録の `key_leaks` で見る",
    u"TSS の記録 `fixtures/xbrl/tanshin_self/population_2026-11-14.json` を読み、sha256 が 1 つでも違えば止める",
    u"違う本が 1 本でも在れば止める",
    u"2 回走らせて、時間の欄を除き byte で同じか",
    u"**「通した」の率と「届いた」の率を 2 本並べる**",
    u"T9(前期の数を当期の値に入れ替える)を**参考**",
    u"この便は engine を変えない。**採る・採らないの判定は無い**",
    u"通した行が 0 なら file は作らない",
)
RESULT_WORDS = (u"通した", u"名指して原本の値を返した", u"名指したが別の値", u"止めたが名指さない(POINTER_NOT_FOUND)", u"止めたが名指さない(UNVERIFIABLE)", u"対応が付かない")
TYPE_NAMES = ("T1_VALUE", "T5_COINCIDENT", "T8_REL", "T9_PRIOR_TO_CURRENT")
SHEET_ROOT_NOTE = u"紙は scratchpad に書き追跡しない"


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. 封の字
def seal_problems(seal):
    out = []
    try:
        sec2 = seal[seal.index(u"## §2"):seal.index(u"## §3")]
        sec3 = seal[seal.index(u"## §3"):seal.index(u"## §4")]
        sec5 = seal[seal.index(u"## §5"):seal.index(u"## §6")]
    except ValueError:
        return [u"封の節(§1〜§6)が揃っていない"]
    ids = re.findall(r"^- \*\*(V-\d+)\*\*", sec3, re.M)
    if ids != list(PRED_IDS):
        out.append(u"封 §3 が V-1〜V-11 の 11 行でない: %s" % ids)
    for rel in (INJECT_REL, PASSED_TYPES_REL, DOC_REL, SCRIPT_REL, u"test_xbrl_tanshin_self_inject_seal.py", u"test_xbrl_tanshin_self_inject_result.py"):
        if rel not in sec2:
            out.append(u"封 §2 に path が無い: %s" % rel)
    for ph in SEAL_PHRASES:
        if ph not in seal:
            out.append(u"封に規則の要点の字が無い: %s" % ph)
    return out


# ---------------------------------------------------------------- 2. 封の字と script の定数
def script_problems(seal, ms=None):
    u"""封の字と script の定数が同じか。ms = script の module(試験が壊した写しを渡す)。"""
    ms = ms or MS
    out = []
    if ms.SEAL_REL != SEAL_REL or ms.SEAL_COMMIT != SEAL_COMMIT_SHORT:
        out.append(u"封の path・commit が違う")
    if ms.SCRIPT_REL != SCRIPT_REL or ms.DOC_REL != DOC_REL or ms.S2_SCRIPT_REL != S2_REL or ms.TSS_SCRIPT_REL != TSS_REL:
        out.append(u"script・結果の文書・前の便の path が封 §2・§5 と違う")
    if (ms.INJECT_REL, ms.PASSED_TYPES_REL) != (INJECT_REL, PASSED_TYPES_REL) or tuple(ms.PRODUCTION_RELS) != (INJECT_REL,):
        out.append(u"記録の path・本番の記録の guard の対象が封 §2 と違う")
    if (ms.STATES_REL, ms.INTERIM_REL) != (STATES_REL, INTERIM_REL):
        out.append(u"土台の記録の path が封 §2 の 1 と違う")
    if ms.PROFILE != "P33E":
        out.append(u"profile が P33E でない")
    if ms.SEED != 20261114 or not isinstance(ms.SEED, int) or isinstance(ms.SEED, bool):
        out.append(u"種が整数 20261114 でない")
    if ms.CAP != 10:
        out.append(u"cap が 10 でない")
    if ms.NAME_PREFIX != "B" or ms.book_name(7) != u"B7" or ms.book_name(253) != u"B253":
        out.append(u"本の名前の形が \"B\" + # でない")
    if tuple(ms.R_VALUES) != (-0.10, -0.03, 0.03, 0.10):
        out.append(u"T8 の r が封 §0-2 の 3 と違う")
    if tuple(ms.TYPES) != TYPE_NAMES or tuple(ms.MAIN_TYPES) != TYPE_NAMES[:3]:
        out.append(u"型の名前が封 §0-2 の 3 と違う(主は T1・T5・T8)")
    if tuple(ms.LABELS) != RESULT_WORDS:
        out.append(u"結果の語が封 §0-2 の 8 と違う")
    for w in RESULT_WORDS:
        if w not in seal:
            out.append(u"封に結果の語が無い: %s" % w)
    if (ms.A_GROUPS, ms.B_GROUPS, ms.GROUP_NAMES) != ((u"甲", u"乙"), (u"丙",), (u"A", u"丙")):
        out.append(u"群が封 §0-2 の 1 と違う")
    if list(ms.PASSED_LABELS) != [u"a", u"b", u"c", u"d"] or any(ph not in seal for ph in (u"(a) engine が誤りを通した", u"(b) 注入した値が偶然ほかの正しい fact の値になった(誤りとは言えない)", u"(c) 対応付けが別の claim を指した", u"(d) 読んでも分けられない")):
        out.append(u"通した行の札が封 §0-2 の 9 と違う")
    if u"AI の席" not in ms.TYPED_BY or u"人は読んでいない" not in ms.TYPED_BY:
        out.append(u"札を付けた席の字が封 §0-2 の 9 と違う")
    if u"20261114" not in seal or u"`float` にできない fact" not in seal:
        out.append(u"封に種・refs の字が無い")
    if ms.ST is not ms.TSS.ST or ms.TS is not ms.TSS.TS or ms.TSS is not ms.S2.TSS:
        out.append(u"前の便の script と別の instance を使っている")
    return out


# ---------------------------------------------------------------- 3. engine 0 行・4. 順序
def untouched_problems(root=REPO, base=None, rels=NOT_TOUCHED_RELS):
    return G2.untouched_problems(root=root, base=base, rels=rels, prefix=PREFIX, seal_rel=SEAL_REL)


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = list(SCRIPT_RELS + (GATE_REL,)) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others)


# ---------------------------------------------------------------- 配線・名前・docID・通信
#: 前の便の関数。この script は同名の関数を定義せず、(module の別名, 関数名)を呼ぶ
REUSED_FUNCS = (("S2", "load_population"), ("S2", "load_tss_states"), ("S2", "prepare"), ("S2", "read_material"),
                ("TSS", "judge_book"), ("TSS", "cut"), ("TSS", "wrap"), ("TSS", "load_json"), ("TSS", "inside_repo"), ("TSS.I", "load_instance"),
                ("TS", "inject_text_ts"), ("TS", "wiring_problems"), ("TS", "base_pair"), ("TS", "t8_base_status"), ("TS", "pct"), ("TS.NF", "map_pool"),
                ("ST", "dumps_record"), ("ST", "write_text_exclusive"), ("ST", "key_leaks"), ("ST", "sha256_file"), ("ST", "names_snapshot"), ("ST", "git_head"), ("ST", "display_path"), ("ST", "default_cache_dir"),
                ("VD", "verify_document"))
NOT_REDEFINED = ("cut", "cut_lines", "cut_html", "wrap", "overview_html", "judge_book", "block", "tally", "pick_sample", "inside_repo", "sheet_text", "html_to_lines", "prepare", "rewrite_zip",
                 "read_material", "load_population", "load_tss_states", "inject_text_ts", "build_row", "base_pair", "base_status_ts", "t8_base_status", "classify_ts", "wiring_problems",
                 "inject_summary", "inject_columns", "dumps_record", "write_text_exclusive", "key_leaks", "sha256_file", "sha256_bytes", "map_pool", "load_json", "same_states", "near_rules")
NETWORK_MODULES = G2.NETWORK_MODULES


def _reuse_problems(ms=None, src_path=None):
    ms = ms or MS
    path = src_path or os.path.join(ROOT, SCRIPT_REL)
    defs = G2.defined_functions(path)
    with open(path, encoding="utf-8") as fh:
        body = fh.read()
    out = []
    for name in NOT_REDEFINED:
        if name in defs:
            out.append(u"%s と同名の関数を script が定義している(呼ぶ)" % name)
    for alias, fn in REUSED_FUNCS:
        if not callable(getattr(G2.resolve(ms, alias), fn, None)):
            out.append(u"%s.%s が module に無い" % (alias, fn))
        if not re.search(r"\b%s\.%s\b" % (re.escape(alias), fn), body):
            out.append(u"script が %s.%s を呼んでいない" % (alias, fn))
    return out


def network_problems(path=None):
    return G2.network_problems(path or os.path.join(ROOT, SCRIPT_REL))


def name_problems(rels=SCRIPT_RELS + (GATE_REL,), base=ROOT, codes=None):
    return G1.name_problems(rels=rels, base=base, codes=codes)


def reserved_problems(rels=(GATE_REL,), base=ROOT):
    return G1.reserved_problems(rels=rels, base=base)


# ================================================================ 振る舞いの検査(``*_problems`` は問題の字の列を返す。変異した版でも呼べるよう、module の名前で引く)
SENTS = [u"売上高は1,234百万円となりました。", u"営業利益は234百万円となりました。", u"経常利益は9,999百万円となりました。"]
OP = '<ix:nonFraction name="jppfs_cor:OperatingIncome" contextRef="CurrentYearDuration" unitRef="JPY" decimals="-6" scale="6">234</ix:nonFraction><ix:nonFraction name="jppfs_cor:OperatingIncome" contextRef="Prior1YearDuration" unitRef="JPY" decimals="-6" scale="6">200</ix:nonFraction></body>'
IX_A = G1.IX.replace(u"</body>", OP)
IX_INTERIM = IX_A.replace(u"CurrentYearDuration", u"InterimDuration").replace(u"Prior1YearDuration", u"Prior1InterimDuration")
GRPS = (u"甲", u"乙", u"丙", u"丙")
KINDS = (u"acedjpsm", u"acedifsm", u"scedjpsy", u"scedjpsy")
#: 作り物の 4 本(1 甲・通期の名前 / 2 乙・中間の名前だが A なので写さない / 3 丙・中間の名前 / 4 丙・切れない)での注入の結果の語(型ごとの 2 行ずつ)
NAMED, PNF = RESULT_WORDS[1], RESULT_WORDS[3]
EXPECT_WORDS = {1: {"T1_VALUE": NAMED, "T5_COINCIDENT": PNF, "T8_REL": NAMED}, 2: {"T1_VALUE": PNF, "T5_COINCIDENT": PNF, "T8_REL": PNF}, 3: {"T1_VALUE": NAMED, "T5_COINCIDENT": PNF, "T8_REL": NAMED}}


def fixture4(d):
    u"""(表, 材料の folder, 土台の記録 {#: 本}, ZIP の列)。土台は、A は元の ZIP・丙は期の名前を写した ZIP の判定(記録と同じ作り。script の関数は使わず門が作る)。"""
    import hashlib
    zips = [G2.izip(SENTS, ix=IX_A, kind=KINDS[0], tag=b"1"), G2.izip(SENTS, ix=IX_INTERIM, kind=KINDS[1], tag=b"2"),
            G2.izip(SENTS, ix=IX_INTERIM, kind=KINDS[2], tag=b"3"), G2.izip(SENTS, ix=IX_INTERIM, kind=KINDS[3], tag=b"4", with_q=False)]
    pop = [(i + 1, g, k, hashlib.sha256(z).hexdigest()) for i, (g, k, z) in enumerate(zip(GRPS, KINDS, zips))]
    mat = os.path.join(d, "mat")
    os.makedirs(mat)
    for r, z in zip(pop, zips):
        with open(os.path.join(mat, r[3] + ".zip"), "wb") as fh:
            fh.write(z)
    bases = {}
    for r, z in zip(pop, zips):
        zz = S2.prepare(z, r[1] == u"丙")[0]
        bases[r[0]] = TSS.judge_book(r[0], r[1], r[2], r[3], zz)
    return pop, mat, bases, zips


def kw4(pop, mat, bases):
    return dict(root=ROOT, population=pop, bases=bases, material=mat, say=lambda *a: None)


def boom(*a, **k):
    raise AssertionError(u"止める前に先へ進んだ")


def ts_state():
    return (TS.INJECT_PROFILES, TS.OLD, TS.NEW)


def ts_restore(state):
    TS.INJECT_PROFILES, TS.OLD, TS.NEW = state


def words_of(book):
    return dict((t, set(r["P33E"]["結果"] for r in book["行"] if r["型"] == t)) for t in TYPE_NAMES)


# ---- refs
def F(name, ctx, value, unit=u"JPY"):
    return {"name": name, "context": ctx, "value": value, "unit": unit}


def refs_problems():
    u"""refs(封 §0-2 の 5): 先頭から・同じ key は最初の 1 件・None は飛ばす(数えない)・float にできないものは飛ばして数える(key は使った扱いにしない)・欄・型・単位。"""
    out = []
    facts = [F(u"jppfs_cor:A", u"C1", 5), F(u"jppfs_cor:A", u"C1", 8), F(u"x:B", u"C1", None), F(u"jppfs_cor:B", u"C1", 3.5, u"JPYPerShares"),
             F(u"jppfs_cor:C", u"C2", u"abc"), F(u"jppfs_cor:C", u"C2", 7), F(u"a:b:E", u"C3", 2.25, u"pure"), F(u"jppfs_cor:A", u"C2", 11), F(u"jppfs_cor:D", u"C2", None, None), F(u"jppfs_cor:Z", u"C4", 0), F(u"jppfs_cor:U", u"C5", 3, None)]
    refs, skipped = MS.refs_from_facts(facts)
    eqp(out, u"key の並び", [r["key"] for r in refs], [u"A@C1", u"B@C1", u"C@C2", u"E@C3", u"A@C2", u"Z@C4", u"U@C5"])
    eqp(out, u"値 0 の fact は採る(None だけ飛ばす)", (refs[5]["value"], type(refs[5]["value"]) is float), (0.0, True))
    eqp(out, u"同じ key は最初の 1 件(5。2 件目の 8 でない)", refs[0]["value"], 5.0)
    eqp(out, u"float にできない fact を飛ばして数える(None は数えない)", skipped, 1)
    eqp(out, u"float にできなかった fact は key を使わない(次の同じ key が採られる)", refs[2]["value"], 7.0)
    eqp(out, u"値は float", [type(r["value"]) is float for r in refs], [True] * 7)
    eqp(out, u"要素名は最後の : の後ろ", refs[3]["source_key"], u"E")
    eqp(out, u"欄", sorted(refs[0]), sorted(["key", "source_key", "label", "unit", "value", "role", "context"]))
    eqp(out, u"role・label・context", (refs[0]["role"], refs[0]["label"], refs[0]["context"]), (u"value", u"A", u"C1"))
    eqp(out, u"unit は prepare_material の字(円・1 株あたり・そのまま)", [r["unit"] for r in refs[:2]] + [refs[3]["unit"]], [u"円", MS.PM._money_unit_label(u"JPYPerShares"), u"pure"])
    eqp(out, u"unit が None で値が在る fact は unit None のまま(円にしない。封 §0-2 の 5 の字どおり _money_unit_label(unit))", (refs[6]["unit"], refs[6]["value"], MS.PM._money_unit_label(None)), (None, 3.0, None))
    eqp(out, u"空の facts", MS.refs_from_facts([]), ([], 0))
    return out


# ---- 差し替え(配線)
def wiring_probe():
    u"""with の中で見える値(仕掛けが引く名前)。"""
    g = TS.inject_text_ts.__globals__
    with TS.base_pair():
        rm = tuple(TS.RM.INJECT_PROFILES)
    return collections.OrderedDict([(u"INJECT_PROFILES", tuple(g["INJECT_PROFILES"])), (u"OLD", g["OLD"]), (u"NEW", g["NEW"]), (u"base_pair の中", rm),
                                    (u"切り替え", (bool(getattr(TS.N, TS.TY.FLAG)), bool(getattr(TS.S, TS.TY.FLAG2))))])


@contextlib.contextmanager
def noop_cm(*a, **k):
    yield


@contextlib.contextmanager
def half_pair(name=u"P33E"):
    u"""INJECT_PROFILES だけ差し替え OLD・NEW は替えない故障(戻さない)。"""
    TS.INJECT_PROFILES = (name, name)
    yield


@contextlib.contextmanager
def names_only(name=u"P33E"):
    u"""OLD・NEW だけ差し替え INJECT_PROFILES は替えない故障(戻さない)。"""
    TS.OLD = name
    TS.NEW = name
    yield


@contextlib.contextmanager
def right_base_pair(name=u"P33E"):
    u"""base_pair の中の RM だけ正しく届ける(OLD・NEW の届き方の検査を単独で見るため)。"""
    old = TS.RM.INJECT_PROFILES
    TS.RM.INJECT_PROFILES = (name, name)
    try:
        yield
    finally:
        TS.RM.INJECT_PROFILES = old


@contextlib.contextmanager
def leaky_pair(name=u"P33E"):
    u"""差し替えて戻さない故障。"""
    TS.INJECT_PROFILES, TS.OLD, TS.NEW = (name, name), name, name
    yield


@contextlib.contextmanager
def wrong_base_pair():
    old = TS.RM.INJECT_PROFILES
    TS.RM.INJECT_PROFILES = (u"P32E", u"P30E")
    try:
        yield
    finally:
        TS.RM.INJECT_PROFILES = old


def device_problems():
    u"""profile の対・切り替えの with(封 §0-2 の 4・7): 中で届く・出たら戻る(例外でも)・戻らない/届かない/切り替えが真のままなら止まる・記録の欄。"""
    out = []
    saved = ts_state()
    snap0 = MS.device_snapshot()
    try:
        with MS.device() as w:
            inside = wiring_probe()
            eqp(out, u"仕掛けが引く名前が (P33E, P33E)・P33E・P33E", (inside[u"INJECT_PROFILES"], inside[u"OLD"], inside[u"NEW"]), ((u"P33E", u"P33E"), u"P33E", u"P33E"))
            eqp(out, u"base_pair の中の RM が (P33E, P33E)", inside[u"base_pair の中"], (u"P33E", u"P33E"))
            eqp(out, u"切り替え 2 つは中で真", inside[u"切り替え"], (True, True))
        eqp(out, u"出たあとに元の対", ts_state(), saved)
        eqp(out, u"出たあとに切り替えが偽・RM も元", (MS.device_snapshot(), wiring_probe()[u"切り替え"]), (snap0, (False, False)))
        eqp(out, u"配線の記録の欄", sorted(w), sorted([u"with の前", u"with の中", u"with の中の届き方の問題", u"with の後", u"元に戻った", u"2026-11-09 の便の wiring_problems(with の外・前と後)"]))
        eqp(out, u"配線の記録の値(中は P33E・戻った・問題なし)", (w[u"with の中"][u"TS.INJECT_PROFILES"], w[u"with の中"][u"TS.OLD"], w[u"with の中"][u"TS.NEW"], w[u"元に戻った"], w[u"with の中の届き方の問題"], w[u"2026-11-09 の便の wiring_problems(with の外・前と後)"]),
             ([u"P33E", u"P33E"], u"P33E", u"P33E", True, [], []))
        eqp(out, u"配線の記録の前後が同じ", w[u"with の前"], w[u"with の後"])
        eqp(out, u"配線の記録の中の切り替えが真", [v for k, v in w[u"with の中"].items() if k.startswith(u"切り替え")], [True, True])
        eqp(out, u"配線の記録の前後の切り替えが偽", [v for k, v in w[u"with の後"].items() if k.startswith(u"切り替え")], [False, False])
        # 例外でも戻る
        try:
            with MS.device():
                raise RuntimeError(u"x")
        except RuntimeError:
            pass
        eqp(out, u"例外でも元の対・切り替えが偽", (ts_state(), MS.device_snapshot()), (saved, snap0))
        # 戻さない故障 → 出たあとで止まる
        got_w = []
        with patched(MS, profile_pair=leaky_pair):
            def run_leaky():
                with MS.device() as w_:
                    got_w.append(w_)
            expect_stop(out, u"対を戻さない(with を出たあと)", run_leaky)
        ts_restore(saved)
        eqp(out, u"戻っていないときの配線の記録は 元に戻った が偽", [w_[u"元に戻った"] for w_ in got_w], [False])
        # 届かない故障 → 中で止まる
        for label, repl, extra in ((u"INJECT_PROFILES だけ差し替える", half_pair, {}), (u"何も差し替えない", noop_cm, {}), (u"OLD・NEW だけ差し替える", names_only, {}),
                                   (u"INJECT_PROFILES だけ差し替え base_pair の RM は届く(OLD・NEW の届き方を単独で見る)", half_pair, {"base_pair": right_base_pair})):
            with patched(MS, profile_pair=repl), patched(TS, **extra):
                def run_x():
                    with MS.device():
                        out.append(u"届いていないのに with の中へ入った(%s)" % label)
                expect_stop(out, u"届かない: %s" % label, run_x)
            ts_restore(saved)
        for label, name, repl in ((u"base_pair が差し替えを届けない", "base_pair", wrong_base_pair), (u"t8 の土台の差し替えが届かない", "t8_base_status", noop_cm)):
            with patched(TS, wiring_problems=lambda: [], **{name: repl}):               # with の外の検査は通し、with の中の届き方の検査だけが止めることを見る
                def run_y():
                    with MS.device():
                        out.append(u"届いていないのに with の中へ入った(%s)" % label)
                expect_stop(out, label, run_y)
            ts_restore(saved)
        # 切り替え 2 つのうち 1 つ偽 → 止まる
        for label, name in ((u"yen_scan の切り替えが偽", "yen_scan_on"), (u"T5 の切り替えが偽", "t5_yen_on")):
            mod = TS.NS if name == "yen_scan_on" else TS.TY
            with patched(mod, **{name: noop_cm}):
                def run_z():
                    with MS.device():
                        out.append(u"切り替えが偽なのに with の中へ入った(%s)" % label)
                expect_stop(out, label, run_z)
            ts_restore(saved)
        # 切り替えが真のまま始める → 止まる
        with TS.NS.yen_scan_on():
            expect_stop(out, u"切り替えが真のまま始める", lambda: MS.device().__enter__())
        # with を出たあとの wiring_problems が問題を言えば止まる(前は空・あとは問題)
        seq = iter([[], [u"x"]])
        with patched(TS, wiring_problems=lambda: next(seq)):
            def run_after():
                with MS.device():
                    pass
            expect_stop(out, u"with を出たあとの wiring_problems", run_after)
        ts_restore(saved)
        # with の外の wiring_problems が問題を言えば止まる
        with patched(TS, wiring_problems=lambda: [u"x"]):
            expect_stop(out, u"with の外の wiring_problems", lambda: MS.device().__enter__())
        eqp(out, u"止めたあとも元の対・切り替えが偽", (ts_state(), MS.device_snapshot()), (saved, snap0))
    finally:
        ts_restore(saved)
    return out


# ---- 1 本の注入
def book_problems():
    out = []
    with tmpdir() as d:
        pop, mat, bases, zips = fixture4(d)
        saved = ts_state()
        rt = dict((r[0], [t[:3] for t in bases[r[0]][u"行"]]) for r in pop)
        books = {}
        with MS.device():
            for (n, g, k, sha), z in zip(pop, zips):
                books[n] = MS.inject_book(n, g, k, sha, z, (rt[n] if n != 4 else None))
        b1, b2, b3, b4 = [books[i] for i in (1, 2, 3, 4)]
        eqp(out, u"本の欄", [(b[u"#"], b[u"群"], b[u"名前"], b[u"切り出し"]) for b in (b1, b2, b3, b4)], [(1, u"甲", u"B1", True), (2, u"乙", u"B2", True), (3, u"丙", u"B3", True), (4, u"丙", u"B4", False)])
        eqp(out, u"切れない本は行 0・数えなし", (b4[u"行"], b4[u"数え"], b4[u"GROUNDED の行"]), ([], None, 0))
        eqp(out, u"土台の行・GROUNDED の行(3 行のうち 2)", [(b[u"土台の行"], b[u"GROUNDED の行"]) for b in (b1, b2, b3)], [(3, 2)] * 3)
        eqp(out, u"refs の数・飛ばした数", [(b[u"refs の数"], b[u"refs で飛ばした fact"]) for b in (b1, b2, b3)], [(4, 0)] * 3)
        for n, b in ((1, b1), (2, b2), (3, b3)):
            eqp(out, u"本 %d の型ごとの行の数" % n, collections.Counter(r[u"型"] for r in b[u"行"]), collections.Counter({"T1_VALUE": 2, "T5_COINCIDENT": 2, "T8_REL": 2}))
            eqp(out, u"本 %d の結果の語(丙にだけ期の名前の読み替え。土台の判定と注入後の判定が同じ ZIP の作り)" % n, words_of(b), dict((t, set([EXPECT_WORDS[n][t]]) if t in EXPECT_WORDS[n] else set()) for t in TYPE_NAMES))
            eqp(out, u"本 %d の行の先頭の欄・id の形" % n, ([list(r)[:3] for r in b[u"行"]][0], all(r[u"id"].startswith(u"B%d-" % n) for r in b[u"行"])), ([u"本の #", u"群", u"id"], True))
            eqp(out, u"本 %d の行の本の #・群" % n, set((r[u"本の #"], r[u"群"]) for r in b[u"行"]), set([(n, GRPS[n - 1])]))
            eqp(out, u"本 %d の数え(4 型)" % n, sorted(b[u"数え"]), sorted(TYPE_NAMES))
            eqp(out, u"本 %d の行の欄 P33E" % n, all(u"P33E" in r and r[u"P33E"][u"結果"] in RESULT_WORDS for r in b[u"行"]), True)
        # 仕掛けへ渡す引数(種・名前・cap・第 1 引数・検証の関数)
        calls = []

        def spy(zb, text, refs, seed, key, cap=None, verify=None):
            calls.append((zb, text, refs, seed, key, cap, verify))
            return [], collections.OrderedDict()
        with MS.device():
            with patched(TS, inject_text_ts=spy):
                MS.inject_book(1, u"甲", KINDS[0], pop[0][3], zips[0], rt[1])
                MS.inject_book(3, u"丙", KINDS[2], pop[2][3], zips[2], rt[3])
        eqp(out, u"仕掛けは 2 回(切れた本の数)呼ぶ", len(calls), 2)
        eqp(out, u"種・名前・cap", [(c[3], c[4], c[5]) for c in calls], [(20261114, u"B1", 10), (20261114, u"B3", 10)])
        eqp(out, u"種は整数", [type(c[3]) is int for c in calls], [True, True])
        for c, z, g in ((calls[0], zips[0], u"甲"), (calls[1], zips[2], u"丙")):
            zb2 = S2.prepare(z, g == u"丙")[0]
            text = TSS.cut(zb2)[0]
            eqp(out, u"第 1 引数は無改変の文で包んだ ZIP(%s)" % g, c[0], TSS.wrap(zb2, text)[0])
            eqp(out, u"文は切り出した文(%s)" % g, c[1], text)
            changed = text.replace(u"1,234", u"1,235")
            got = [(x["id"], x["state"]) for x in c[6](None, u"P33E", changed)["claims"]]
            want = [(x["id"], x["state"]) for x in MS.VD.verify_document(TSS.wrap(zb2, changed)[0], u"P33E")["claims"]]
            eqp(out, u"検証の関数は注入後の文で包み直した ZIP に P33E(%s)" % g, got, want)
            eqp(out, u"検証の関数で値の違う行が出る(門の自己確認)", any(s == u"VALUE_MISMATCH" for _i, s in got), True)
            eqp(out, u"refs が仕掛けに渡る(%s)" % g, [r["key"] for r in c[2]], [r["key"] for r in MS.refs_from_facts(TSS.I.load_instance(TSS.wrap(zb2, text)[0])["facts"])[0]])
        # 記録では切れた本が作り直しでは切れない → 止める(切れない本に記録の行が在る形)
        with MS.device():
            expect_stop(out, u"記録は切れた・作り直しは切れない", lambda: MS.inject_book(4, u"丙", KINDS[3], pop[3][3], zips[3], rt[1]))
            expect_stop(out, u"記録は切れた(行 0 の記録)・作り直しは切れない", lambda: MS.inject_book(4, u"丙", KINDS[3], pop[3][3], zips[3], []))
        # capture の build_row は戻る・refs で飛ばした fact の数
        orig_br = TS.build_row
        real_li = TSS.I.load_instance

        def with_bad_fact(wrapped):
            inst = real_li(wrapped)
            inst = dict(inst)
            inst["facts"] = list(inst["facts"]) + [{"name": u"jppfs_cor:Bad", "context": u"CurrentYearDuration", "value": u"abc", "unit": u"JPY"}]
            return inst
        with MS.device():
            cap = {}
            MS.inject_book(1, u"甲", KINDS[0], pop[0][3], zips[0], rt[1], capture=cap)
            eqp(out, u"capture のあと TS.build_row が元に戻る", TS.build_row is orig_br, True)
            eqp(out, u"capture に注入の中身が入る", len(cap.get("items", {})), 6)
            with patched(TSS.I, load_instance=with_bad_fact):
                bs = MS.inject_book(1, u"甲", KINDS[0], pop[0][3], zips[0], rt[1])
            eqp(out, u"飛ばした fact の数と refs の数(飛ばした数を足さない)", (bs[u"refs で飛ばした fact"], bs[u"refs の数"]), (1, 4))
            try:
                with patched(TS, inject_text_ts=boom):
                    MS.inject_book(1, u"甲", KINDS[0], pop[0][3], zips[0], rt[1], capture={})
            except AssertionError:
                pass
            eqp(out, u"仕掛けが落ちても TS.build_row が元に戻る", TS.build_row is orig_br, True)
        # 土台の確かめ
        bad = [list(t) for t in rt[1]]
        bad[0][2] = u"UNVERIFIABLE" if bad[0][2] != u"UNVERIFIABLE" else u"GROUNDED"
        with MS.device():
            expect_stop(out, u"無改変の文の判定が記録と違う", lambda: MS.inject_book(1, u"甲", KINDS[0], pop[0][3], zips[0], bad))
            for n_b, g_b in ((1, u"甲"), (2, u"乙"), (3, u"丙")):
                for how, bz in broken_bases(bases, n_b):
                    expect_stop(out, u"inject_book 直接: %s の本の土台の記録が違う(%s)" % (g_b, how), lambda bz=bz, n_b=n_b, g_b=g_b: MS.inject_book(n_b, g_b, KINDS[n_b - 1], pop[n_b - 1][3], zips[n_b - 1], [t[:3] for t in bz[n_b][u"行"]]))
            expect_stop(out, u"記録の行が空(行 0 の記録)で作り直しは非空", lambda: MS.inject_book(1, u"甲", KINDS[0], pop[0][3], zips[0], []))
            expect_stop(out, u"記録の行が足りない", lambda: MS.inject_book(1, u"甲", KINDS[0], pop[0][3], zips[0], rt[1][:-1]))
            expect_stop(out, u"行の順が違う", lambda: MS.inject_book(1, u"甲", KINDS[0], pop[0][3], zips[0], [rt[1][1], rt[1][0]] + rt[1][2:]))
            pos = [list(t) for t in rt[1]]
            pos[0][1] += 1
            expect_stop(out, u"位置が違う", lambda: MS.inject_book(1, u"甲", KINDS[0], pop[0][3], zips[0], pos))
            sen = [list(t) for t in rt[1]]
            sen[0][0] += 1
            expect_stop(out, u"文の番号が違う", lambda: MS.inject_book(1, u"甲", KINDS[0], pop[0][3], zips[0], sen))
        # 丙の本(作り物の本 3)でも土台の確かめは効く(丙だけ飛ばす変異を赤にする)
        with MS.device():
            st3 = [list(t) for t in rt[3]]
            st3[0][2] = u"UNVERIFIABLE" if st3[0][2] != u"UNVERIFIABLE" else u"GROUNDED"
            expect_stop(out, u"丙: 記録の state が違う", lambda: MS.inject_book(3, u"丙", KINDS[2], pop[2][3], zips[2], st3))
            ps3 = [list(t) for t in rt[3]]
            ps3[0][1] += 1
            expect_stop(out, u"丙: 記録の位置が違う", lambda: MS.inject_book(3, u"丙", KINDS[2], pop[2][3], zips[2], ps3))
            expect_stop(out, u"丙: 行の順が違う", lambda: MS.inject_book(3, u"丙", KINDS[2], pop[2][3], zips[2], [rt[3][1], rt[3][0]] + rt[3][2:]))
        # 差し替えの外では止まる(本の job の守り)
        expect_stop(out, u"with の外で呼ぶ", lambda: MS.inject_book(1, u"甲", KINDS[0], pop[0][3], zips[0], rt[1]))
        eqp(out, u"終わったあとも元の対", ts_state(), saved)
    return out


# ---- 集計
def mk_row(grp, typ, word, linked, reached, rt=True, reread=True):
    return {u"本の #": 1, u"群": grp, u"id": u"B1-x", u"型": typ, u"P33E": {u"対応": linked, u"結果": word, u"state": None, u"reason": None}, u"届いた": reached, u"round-trip": rt, u"読み直し": reread}


def summary_problems():
    u"""群 × 型の集計(封 §2 の 3): 通した率(分母 = 注入の行)と届いた率(分母 = 対応が付いた行)を別の欄に・通したを届いた/届いていないに分ける・群で割る。"""
    out = []
    P, N_, U = RESULT_WORDS[0], RESULT_WORDS[1], RESULT_WORDS[5]
    rows = [mk_row(u"甲", "T1_VALUE", P, True, True), mk_row(u"乙", "T1_VALUE", P, True, False), mk_row(u"甲", "T1_VALUE", N_, True, True, rt=False), mk_row(u"乙", "T1_VALUE", U, False, True, reread=False),
            mk_row(u"甲", "T1_VALUE", N_, True, True), mk_row(u"丙", "T1_VALUE", P, True, True), mk_row(u"丙", "T8_REL", N_, True, True), mk_row(u"丙", "T8_REL", N_, True, False),
            mk_row(u"丙", "T8_REL", P, True, False), mk_row(u"甲", "T9_PRIOR_TO_CURRENT", N_, True, True)]
    s = MS.summary(rows)
    eqp(out, u"群と型", ([list(s)] + [list(s[g]) for g in s]), [[u"A", u"丙"]] + [list(TYPE_NAMES)] * 2)
    a1 = s[u"A"]["T1_VALUE"]
    eqp(out, u"A・T1 の行・対応が付いた行", (a1[u"注入の行"], a1[u"対応が付いた行"]), (5, 4))
    eqp(out, u"A・T1 の通した(件・率・届いた・届いていない)", (a1[u"通した"][u"件"], a1[u"通した"][u"率"], a1[u"通した"][u"うち届いた"], a1[u"通した"][u"うち届いていない"]), (2, 40.0, 1, 1))
    eqp(out, u"A・T1 の届いた(分母は対応が付いた行 4 のうち 3)", (a1[u"届いた"][u"件"], a1[u"届いた"][u"率(分母は対応が付いた行)"]), (3, 75.0))
    eqp(out, u"A・T1 の結果の語の率(分母は注入の行)", [(a1[u"結果の語"][w][u"件"], a1[u"結果の語"][w][u"率"]) for w in RESULT_WORDS], [(2, 40.0), (2, 40.0), (0, 0.0), (0, 0.0), (0, 0.0), (1, 20.0)])
    eqp(out, u"A・T1 の round-trip・読み直し不一致", (a1[u"round-trip 不一致"], a1[u"読み直し不一致"]), (1, 1))
    p1 = s[u"丙"]["T1_VALUE"]
    eqp(out, u"丙・T1(丙だけ)", (p1[u"注入の行"], p1[u"通した"][u"件"], p1[u"通した"][u"率"], p1[u"届いた"][u"件"]), (1, 1, 100.0, 1))
    p8 = s[u"丙"]["T8_REL"]
    eqp(out, u"丙・T8(3 行・通した 1 行は届いていない)", (p8[u"注入の行"], p8[u"通した"][u"件"], p8[u"通した"][u"うち届いていない"], p8[u"届いた"][u"件"], p8[u"届いた"][u"率(分母は対応が付いた行)"], p8[u"通した"][u"率"]), (3, 1, 1, 1, 33.3, 33.3))
    eqp(out, u"A・T5 は行なし(率は None)", (s[u"A"]["T5_COINCIDENT"][u"注入の行"], s[u"A"]["T5_COINCIDENT"][u"通した"][u"率"], s[u"A"]["T5_COINCIDENT"][u"届いた"][u"率(分母は対応が付いた行)"]), (0, None, None))
    eqp(out, u"A・T9", s[u"A"]["T9_PRIOR_TO_CURRENT"][u"注入の行"], 1)
    return out


def book_stub(n, grp, g, rows_by_type, counts):
    return {u"#": n, u"群": grp, u"名前": u"B%d" % n, u"GROUNDED の行": g, u"refs の数": 3, u"refs で飛ばした fact": n % 2,
            u"行": [{u"型": t} for t, k in rows_by_type for _ in range(k)], u"数え": counts}


def coverage_problems():
    u"""覆い(封 §2 の 4): 本ごと・群ごと。分母 = GROUNDED が 1 行以上の本。作れる site は dict なら 3 形の合計・円族の token は T8 の欄・全角で注入しない本。"""
    out = []
    c1 = collections.OrderedDict([("T1_VALUE", {u"作れる site": 7}), ("T5_COINCIDENT", {u"作れる site": {u"既存": 2, u"万だけ": 1, u"複合": 0}}), ("T8_REL", {u"作れる site": 4, u"円族の token": 9}),
                                  ("T9_PRIOR_TO_CURRENT", {u"作れる site": {u"既存": 0, u"万だけ": 0, u"複合": 0}})])
    c2 = collections.OrderedDict([(u"注入しない", u"文に全角の数字がある")])
    c3 = collections.OrderedDict([("T1_VALUE", {u"作れる site": 0}), ("T5_COINCIDENT", {u"作れる site": {u"既存": 0, u"万だけ": 0, u"複合": 0}}), ("T8_REL", {u"作れる site": 0, u"円族の token": 3}),
                                  ("T9_PRIOR_TO_CURRENT", {u"作れる site": {u"既存": 1, u"万だけ": 0, u"複合": 0}})])
    books = [book_stub(1, u"甲", 5, [("T1_VALUE", 2), ("T5_COINCIDENT", 1), ("T8_REL", 3)], c1), book_stub(2, u"乙", 4, [], c2), book_stub(3, u"丙", 0, [], c3),
             book_stub(4, u"丙", 1, [("T8_REL", 1)], c1), book_stub(5, u"丙", 0, [("T1_VALUE", 1)], c3)]
    per, grp = MS.coverage(books)
    eqp(out, u"本ごとの欄", sorted(per[0]), sorted([u"#", u"群", u"名前", u"P33E が GROUNDED の行", u"円族の token", u"作れる site", u"注入の行", u"refs の数", u"refs で飛ばした fact", u"全角の数字で注入しない"]))
    eqp(out, u"本 1(作れる site は dict なら合計)", (per[0][u"円族の token"], dict(per[0][u"作れる site"]), dict(per[0][u"注入の行"]), per[0][u"全角の数字で注入しない"]),
        (9, {"T1": 7, "T5": 3, "T8": 4, "T9": 0}, {"T1": 2, "T5": 1, "T8": 3, "T9": 0}, False))
    eqp(out, u"本 2(全角で注入しない・円族の token なし)", (per[1][u"円族の token"], per[1][u"全角の数字で注入しない"], dict(per[1][u"作れる site"])), (None, True, {"T1": 0, "T5": 0, "T8": 0, "T9": 0}))
    a, b = grp[u"A"], grp[u"丙"]
    eqp(out, u"A の本・GROUNDED が 1 行以上・注入の行が 1 行以上", (a[u"切れた本"], a[u"GROUNDED が 1 行以上の本"], a[u"注入の行が 1 行以上の本"]), (2, 2, 1))
    eqp(out, u"A の率(分母は GROUNDED が 1 行以上の本)", dict(a[u"注入の行が 1 行以上の本(分母は GROUNDED が 1 行以上の本)"]), {u"件": 1, u"率": 50.0})
    eqp(out, u"A の合計", (a[u"P33E が GROUNDED の行の合計"], a[u"円族の token の合計"], a[u"全角の数字で注入しない本"], dict(a[u"作れる site の合計"]), dict(a[u"注入の行の合計"])),
        (9, 9, 1, {"T1": 7, "T5": 3, "T8": 4, "T9": 0}, {"T1": 2, "T5": 1, "T8": 3, "T9": 0}))
    eqp(out, u"丙の本・GROUNDED が 1 行以上・注入の行が 1 行以上(うち GROUNDED が 1 行以上)", (b[u"切れた本"], b[u"GROUNDED が 1 行以上の本"], b[u"注入の行が 1 行以上の本"], b[u"注入の行が 1 行以上の本(分母は GROUNDED が 1 行以上の本)"][u"件"]), (3, 1, 2, 1))
    eqp(out, u"丙の率", b[u"注入の行が 1 行以上の本(分母は GROUNDED が 1 行以上の本)"][u"率"], 100.0)
    eqp(out, u"丙の型ごとに注入の行が 1 行以上の本・作れる site が 0 の本", (dict(b[u"型ごとに注入の行が 1 行以上の本"]), dict(b[u"作れる site が 0 の本"])), ({"T1": 1, "T5": 0, "T8": 1, "T9": 0}, {"T1": 2, "T5": 2, "T8": 2, "T9": 1}))
    eqp(out, u"refs で飛ばした fact の合計", (a[u"refs で飛ばした fact の合計"], b[u"refs で飛ばした fact の合計"]), (1, 2))
    eqp(out, u"円族の token の合計(丙)", b[u"円族の token の合計"], 15)
    return out


# ---- 記録(run_inject)
def run_problems():
    u"""run_inject: 記録の形・本の数え・集計と覆い(行から別の書き方で数え直す)・文や値を持たない・2 回(procs 違い)で byte が同じ(時間を除く)・止める所。"""
    out = []
    with tmpdir() as d:
        pop, mat, bases, zips = fixture4(d)
        kw = kw4(pop, mat, bases)
        saved = ts_state()
        p1 = os.path.join(d, "o", "i1.json")
        ticks = iter([10.0, 13.5])
        rec = MS.run_inject(procs=1, out=p1, clock=lambda: next(ticks), **kw)
        text = open(p1, encoding="utf-8").read()
        eqp(out, u"返り値と file", json.loads(text), json.loads(json.dumps(rec)))
        eqp(out, u"終わったあとも元の対", ts_state(), saved)
        eqp(out, u"種・cap・profile", (rec[u"種"], rec[u"cap"], rec[u"profile"]), (20261114, 10, u"P33E"))
        eqp(out, u"seal・封の commit", (rec[u"seal"], rec[u"封の commit"]), (SEAL_REL, SEAL_COMMIT_SHORT))
        eqp(out, u"母集団", dict(rec[u"母集団"]), {u"対象の本(切れた本)": 3, u"切れない本": 1, u"A": 2, u"丙": 1})
        eqp(out, u"本ごとの数えの名前", list(rec[u"本ごとの数え"]), [u"B1", u"B2", u"B3"])
        rows = rec[u"行"]
        eqp(out, u"注入の行の数(3 本 × 6 行)", (rec[u"注入の行の数"], len(rows)), (18, 18))
        eqp(out, u"行の本の # の順", [r[u"本の #"] for r in rows], [1] * 6 + [2] * 6 + [3] * 6)
        eqp(out, u"行の欄は 本の #・群・id から始まる", rec[u"行の欄"][:3], [u"本の #", u"群", u"id"])
        eqp(out, u"土台の確かめ", (rec[u"土台の確かめ"][u"本"], rec[u"土台の確かめ"][u"行"], rec[u"土台の確かめ"][u"違う本"]), (3, 9, 0))
        w = rec[u"配線"]
        eqp(out, u"配線(戻った・届き方の問題なし・切り替えは中で真・出たあとで偽)", (w[u"元に戻った"], w[u"with の中の届き方の問題"], rec[u"切り替え"][u"inject の中の値"], rec[u"切り替え"][u"出たあとの値"],
                                                                 rec[u"切り替え"][u"T5 の切り替え inject の中の値"], rec[u"切り替え"][u"T5 の切り替え 出たあとの値"]), (True, [], True, False, True, False))
        eqp(out, u"時間は 1 つの欄", (rec[u"時間(秒)"], len(re.findall(u"時間", text))), (3.5, 1))
        eqp(out, u"key_leaks は空", rec[u"key_leaks"], [])
        eqp(out, u"記録の限界は封 §6 の字・欄名の注記は別の欄", (rec[u"限界"] == list(MS.INJECT_LIMITS), len(rec[u"限界"]), rec[u"欄名の注記"] == MS.FIELD_NAME_NOTE, MS.FIELD_NAME_NOTE in rec[u"限界"]), (True, 7, True, False))
        eqp(out, u"限界は封の file の字(記録の字)", limits_problems(read(SEAL_REL), ms=types.SimpleNamespace(INJECT_LIMITS=tuple(rec[u"限界"]))), [])
        eqp(out, u"材料の置き場の前後", (rec[u"材料"][u"置き場の一覧の前後"][u"変化なし"], rec[u"材料"][u"表と一致した ZIP"]), (True, 4))
        prov = ((u"第 2 便の script の sha256", S2_REL), (u"TSS の script の sha256", TSS_REL), (u"置く script の sha256", STAGE_REL), (u"2026-11-09 の便の script の sha256", TS_REL),
                (u"母集団の記録の sha256", POPULATION_REL), (u"TSS の判定の記録の sha256", STATES_REL), (u"interim の記録の sha256", INTERIM_REL))
        for k_, rel_ in prov:
            eqp(out, u"来歴 %s は実 file の sha256" % k_, rec[k_], ST.sha256_file(os.path.join(ROOT, rel_)))
        eqp(out, u"来歴 仕掛けの 2 file の sha256 は実 file", dict(rec[u"仕掛けの 2 file の sha256"]), dict((r_, ST.sha256_file(os.path.join(ROOT, r_))) for r_ in TS.DEVICE_RELS))
        eqp(out, u"来歴 lib の指紋は実 file", dict(rec[u"lib の指紋"]), dict((r_, ST.sha256_file(os.path.join(ROOT, r_))) for r_ in TS.LIB_RELS))
        for k in (u"この script の sha256", u"第 2 便の script の sha256", u"TSS の script の sha256", u"置く script の sha256", u"2026-11-09 の便の script の sha256", u"engine の指紋", u"仕掛けの 2 file の sha256", u"lib の指紋",
                  u"母集団の記録の sha256", u"TSS の判定の記録の sha256", u"interim の記録の sha256", u"HEAD の commit"):
            if not rec.get(k):
                out.append(u"記録に %s が無い" % k)
        eqp(out, u"この script の sha256 は file の sha256", rec[u"この script の sha256"], ST.sha256_file(os.path.join(ROOT, SCRIPT_REL)))
        eqp(out, u"2026-11-09 の便の script の sha256 は file の sha256", rec[u"2026-11-09 の便の script の sha256"], ST.sha256_file(os.path.join(ROOT, TS_REL)))
        eqp(out, u"記録に文・span・値・要素名の字が無い", [x in text for x in (u"売上高", u"営業利益", u"経常利益", u"となりました", u'"span"', u'"value"', u'"recomputed"', u"jpcrp_cor", u"NetSales", u"OperatingIncome", u"1,234", u"9,999")], [False] * 12)
        # 集計・覆いを、行から別の書き方で数え直す
        for g, nums in ((u"A", (1, 2)), (u"丙", (3,))):
            sel = [r for r in rows if r[u"本の #"] in nums]
            for t in TYPE_NAMES:
                tr = [r for r in sel if r[u"型"] == t]
                blk = rec[u"集計"][g][t]
                eqp(out, u"集計 %s %s の行" % (g, t), blk[u"注入の行"], len(tr))
                for wd in RESULT_WORDS:
                    eqp(out, u"集計 %s %s %s" % (g, t, wd), blk[u"結果の語"][wd][u"件"], sum(1 for r in tr if r[u"P33E"][u"結果"] == wd))
                eqp(out, u"集計 %s %s 届いた" % (g, t), blk[u"届いた"][u"件"], sum(1 for r in tr if r[u"P33E"][u"対応"] and r[u"届いた"]))
            cov = rec[u"覆い"][u"群ごと"][g]
            eqp(out, u"覆い %s の注入の行の合計" % g, dict(cov[u"注入の行の合計"]), dict((TS.TYPE_SHORT[t], sum(1 for r in sel if r[u"型"] == t)) for t in TYPE_NAMES))
        eqp(out, u"覆いの本ごと", [(p[u"#"], p[u"P33E が GROUNDED の行"], sum(p[u"注入の行"].values())) for p in rec[u"覆い"][u"本ごと"]], [(1, 2, 6), (2, 2, 6), (3, 2, 6)])
        eqp(out, u"覆い(A)の注入の行が 1 行以上の本(分母は GROUNDED が 1 行以上の本)", dict(rec[u"覆い"][u"群ごと"][u"A"][u"注入の行が 1 行以上の本(分母は GROUNDED が 1 行以上の本)"]), {u"件": 2, u"率": 100.0})
        # 記録の「切り替え」は配線の記録の値をそのまま写す(中と後を入れ替えた作り物の配線で見る)
        real_device = MS.device

        @contextlib.contextmanager
        def flipped_device(*a, **k):
            with real_device(*a, **k) as w_:
                yield w_
            for key_ in list(w_[u"with の中"]):
                if key_.startswith(u"切り替え"):
                    w_[u"with の中"][key_], w_[u"with の後"][key_] = False, True
        pf = os.path.join(d, "o", "flip.json")
        with patched(MS, device=flipped_device):
            recf = MS.run_inject(out=pf, **kw)
        eqp(out, u"切り替えの記録は配線の値を写す(中・後を入れ替えた作り物)", [recf[u"切り替え"][k_] for k_ in (u"inject の中の値", u"出たあとの値", u"T5 の切り替え inject の中の値", u"T5 の切り替え 出たあとの値")], [False, True, False, True])
        # 2 回(procs 違い)で byte が同じ(時間を除く)
        p2 = os.path.join(d, "o", "i2.json")
        MS.run_inject(procs=2, out=p2, clock=lambda: 99.0, **kw)
        eqp(out, u"2 回(procs 違い)で byte が同じ(時間を除く)", strip_time(open(p2, encoding="utf-8").read()), strip_time(text))
        eqp(out, u"2 回走らせたあとも元の対", ts_state(), saved)
        # 止める所(何も書かない)
        with patched(TS.NF, map_pool=boom):                                             # 在る出力で止まるのは材料を読む前
            expect_stop(out, u"出力が在る", lambda: MS.run_inject(out=p1, **kw))
        eqp(out, u"在る出力は変わらない", open(p1, encoding="utf-8").read(), text)
        expect_stop(out, u"--out が無い", lambda: MS.run_inject(out=None, **kw))
        prod = os.path.join(ROOT, INJECT_REL)
        prod_before = prod_state()
        with patched(TS.NF, map_pool=boom):
            expect_stop(out, u"本番の記録を使い捨ての材料から作る", lambda: MS.run_inject(out=prod, **kw))
        expect_stop(out, u"material_dir: 本番の記録の path に使い捨ての材料", lambda: MS.material_dir(mat, prod))
        eqp(out, u"material_dir: 使い捨ての出力なら通る", MS.material_dir(mat, os.path.join(d, "o", "z.json"))[1], False)
        eqp(out, u"本番の記録の存在・sha256 が実行の前後で同じ(この門は本番の記録を書かない・変えない)", prod_state(), prod_before)
        b2 = copy.deepcopy(bases)
        b2[1][u"行"][0][2] = u"UNVERIFIABLE" if b2[1][u"行"][0][2] != u"UNVERIFIABLE" else u"GROUNDED"
        expect_stop(out, u"無改変の文の判定が記録と違う", lambda: MS.run_inject(out=os.path.join(d, "o", "i3.json"), **dict(kw, bases=b2)))
        for n_b, lab in ((1, u"甲"), (2, u"乙"), (3, u"丙")):                                       # 呼び出し元(run_inject → jobs_of → job)を通して、群ごとに土台の記録を壊すと止まる(空の記録も)
            for how, bz in broken_bases(bases, n_b):
                po = os.path.join(d, "o", "bz_%d_%s.json" % (n_b, how))
                expect_stop(out, u"run_inject: %s の本の土台の記録が違う(%s)" % (lab, how), lambda bz=bz, po=po: MS.run_inject(out=po, **dict(kw, bases=bz)))
                if os.path.exists(po):
                    out.append(u"土台が違うのに記録を書いた(%s・%s)" % (lab, how))
        with open(os.path.join(mat, pop[2][3] + ".zip"), "ab") as fh:
            fh.write(b"x")
        expect_stop(out, u"材料の sha256 が違う", lambda: MS.run_inject(out=os.path.join(d, "o", "i4.json"), **kw))
        os.remove(os.path.join(mat, pop[1][3] + ".zip"))
        with patched(TS.NF, map_pool=boom):                                             # 材料が無いことは判定を始める前に見つける
            expect_stop(out, u"材料が無い", lambda: MS.run_inject(out=os.path.join(d, "o", "i5.json"), **kw))
        if any(os.path.exists(os.path.join(d, "o", n)) for n in ("i3.json", "i4.json", "i5.json")):
            out.append(u"止まったのに記録を書いた")
        eqp(out, u"止まったあとも元の対", ts_state(), saved)
    with tmpdir() as d:
        pop, mat, bases, zips = fixture4(d)
        snaps = iter([(4, u"a"), (4, u"b")])
        with patched(ST, names_snapshot=lambda folder: next(snaps)):
            expect_stop(out, u"材料の置き場が変わった", lambda: MS.run_inject(out=os.path.join(d, "o", "i6.json"), **kw4(pop, mat, bases)))
        if os.path.exists(os.path.join(d, "o", "i6.json")):
            out.append(u"材料の置き場が変わったのに記録を書いた")
    return out


def broken_bases(bases, n):
    u"""[(壊し方, 本 n の土台の行だけ壊した写し)]。壊す行の場所(先頭・真ん中・最後)の state・位置・順・行を 1 つ落とす・空(行 0)。行数が足りない壊し方は作らない。壊す前の bases は変えない。"""
    out = []
    rows0 = bases[n][u"行"]

    def flip(r):
        r[2] = u"UNVERIFIABLE" if r[2] != u"UNVERIFIABLE" else u"GROUNDED"
    plan = [(u"先頭の state", 0, None)]
    if len(rows0) >= 3:
        plan.append((u"真ん中の state", len(rows0) // 2, None))
    if len(rows0) >= 2:
        plan.append((u"最後の state", len(rows0) - 1, None))
    if len(rows0) >= 1:
        plan.append((u"位置", 0, None))
        plan.append((u"最後の位置", len(rows0) - 1, None))
    if len(rows0) >= 2:
        plan.append((u"順", 0, None))
    if len(rows0) >= 1:
        plan.append((u"行を 1 つ落とす", 0, None))
        plan.append((u"空(行 0)", 0, None))
    for how, i, _x in plan:
        bz = copy.deepcopy(bases)
        rw = bz[n][u"行"]
        if how.endswith(u"state"):
            flip(rw[i])
        elif how.endswith(u"位置"):
            rw[i][1] += 1
        elif how == u"順":
            rw[0], rw[1] = rw[1], rw[0]
        elif how == u"行を 1 つ落とす":
            del rw[-1]
        else:
            del rw[:]
        out.append((how, bz))
    return out


def fixture_small(d):
    u"""行数の違う作り物の 4 本(1 甲・2 丙は数の無い文で土台の行が 0 / 3 甲・4 丙は数が 1 つで土台の行が 1)。(表, 材料の folder, 土台の記録 {#: 本})。"""
    import hashlib
    nonum, one, two = [u"売上は増加しました。"], SENTS[:1], SENTS[:2]
    grp = (u"甲", u"丙", u"甲", u"丙", u"甲", u"丙")
    kind = (KINDS[0], KINDS[2], KINDS[0], KINDS[2], KINDS[0], KINDS[2])
    zips = [G2.izip(nonum, ix=IX_A, kind=kind[0], tag=b"s1"), G2.izip(nonum, ix=IX_INTERIM, kind=kind[1], tag=b"s2"),
            G2.izip(one, ix=IX_A, kind=kind[2], tag=b"s3"), G2.izip(one, ix=IX_INTERIM, kind=kind[3], tag=b"s4"),
            G2.izip(two, ix=IX_A, kind=kind[4], tag=b"s5"), G2.izip(two, ix=IX_INTERIM, kind=kind[5], tag=b"s6")]
    pop = [(i + 1, g, k, hashlib.sha256(z).hexdigest()) for i, (g, k, z) in enumerate(zip(grp, kind, zips))]
    mat = os.path.join(d, "mat_small")
    os.makedirs(mat)
    for r, z in zip(pop, zips):
        with open(os.path.join(mat, r[3] + ".zip"), "wb") as fh:
            fh.write(z)
    bases = dict((r[0], TSS.judge_book(r[0], r[1], r[2], r[3], S2.prepare(z, r[1] == u"丙")[0])) for r, z in zip(pop, zips))
    return pop, mat, bases, zips


def small_problems():
    u"""土台の行が 0 の本・1 行の本の確かめ(行数の軸)と、procs=2 でも土台を渡す(procs の軸)。作り直しが行 0 で記録が非空(逆向きの空)でも止まる。入口は inject_book 直接・run_inject・run_preview。"""
    out = []
    with tmpdir() as d:
        pop, mat, bases, zips = fixture_small(d)
        eqp(out, u"作り物の本の土台の行数(0・0・1・1)", [len(bases[i][u"行"]) for i in (1, 2, 3, 4, 5, 6)], [0, 0, 1, 1, 2, 2])
        kw = dict(root=ROOT, population=pop, bases=bases, material=mat, say=lambda *a: None)
        kwp = dict((k, v) for k, v in kw.items() if k != "say")
        fake = [0, 0, u"GROUNDED", None, None, None, None, None, None]
        variants = []                                                                       # (名前, 本 #, 壊した bases)
        for n in (1, 2):                                                                    # 逆向きの空: 記録は非空・作り直しは行 0
            bz = copy.deepcopy(bases)
            bz[n][u"行"] = [list(fake)]
            variants.append((u"記録は非空・作り直しは行 0", n, bz))
        for n in (3, 4, 5, 6):
            for how, bz in broken_bases(bases, n):
                variants.append((u"土台が %d 行の本: " % len(bases[n][u"行"]) + how, n, bz))
        with MS.device():
            for n in (1, 2, 3, 4, 5, 6):                                                     # 壊していない土台は通る
                MS.inject_book(n, pop[n - 1][1], pop[n - 1][2], pop[n - 1][3], zips[n - 1], [t[:3] for t in bases[n][u"行"]])
            for how, n, bz in variants:
                expect_stop(out, u"inject_book 直接(%s・本 %d)" % (how, n), lambda bz=bz, n=n: MS.inject_book(n, pop[n - 1][1], pop[n - 1][2], pop[n - 1][3], zips[n - 1], [t[:3] for t in bz[n][u"行"]]))
        for procs in (1, 2):
            rec = MS.run_inject(out=os.path.join(d, "o", "ok_%d.json" % procs), procs=procs, **kw)
            eqp(out, u"run_inject(壊していない・procs %d)" % procs, rec[u"注入の行の数"] > 0 and rec[u"土台の確かめ"][u"本"] == 6, True)
            for how, n, bz in variants:
                po = os.path.join(d, "o", "sm_%d_%d_%d.json" % (procs, n, len(how)))
                expect_stop(out, u"run_inject procs %d(%s・本 %d)" % (procs, how, n), lambda bz=bz, po=po, procs=procs: MS.run_inject(out=po, procs=procs, **dict(kw, bases=bz)))
                if os.path.exists(po):
                    out.append(u"土台が違うのに記録を書いた(small)")
                expect_stop(out, u"run_preview procs %d(%s・本 %d)" % (procs, how, n), lambda bz=bz, n=n, procs=procs: MS.run_preview([n], procs=procs, say=lambda *a: None, **dict(kwp, bases=bz)))
            eqp(out, u"run_preview(壊していない・procs %d)" % procs, len(MS.run_preview([3, 4, 5, 6], procs=procs, say=lambda *a: None, **kwp)[0]), 4)
    return out


def prod_state():
    u"""本番の記録 2 つの {path: sha256 か None(無い)}。門が実行の前後で比べる(記録が在る・無いのどちらでも緑になる)。"""
    return dict((rel, (ST.sha256_file(os.path.join(ROOT, rel)) if os.path.exists(os.path.join(ROOT, rel)) else None)) for rel in (INJECT_REL, PASSED_TYPES_REL))


def preview_problems():
    u"""preview: 指定した本だけ・記録も紙も書かない・本が母集団に無ければ止まる。"""
    out = []
    with tmpdir() as d:
        pop, mat, bases, zips = fixture4(d)
        before = sorted(os.listdir(d)), sorted(os.listdir(mat))
        lines = []
        books, rows = MS.run_preview([1, 4], procs=1, say=lambda *a: lines.append(u" ".join(u"%s" % x for x in a)), **dict((k, v) for k, v in kw4(pop, mat, bases).items() if k != "say"))
        eqp(out, u"指定した本だけ(切れない本は行 0)", ([b[u"#"] for b in books], len(rows)), ([1], 6))
        eqp(out, u"何も書かない", (sorted(os.listdir(d)), sorted(os.listdir(mat))), before)
        if not any(ln.startswith(u"T1 行 2 届いた 2 ") for ln in lines):
            out.append(u"型ごとの行の数と届いた数が標準出力に出ない")
        if not any(ln.startswith(u"T9 行 0 届いた 0 ") for ln in lines):
            out.append(u"T9 の行 0 の行が標準出力に出ない")
        for n_b, lab in ((1, u"甲"), (2, u"乙"), (3, u"丙")):
            for how, bz in broken_bases(bases, n_b):
                expect_stop(out, u"下見: %s の本の土台の記録が違う(%s)" % (lab, how), lambda bz=bz, n_b=n_b: MS.run_preview([n_b], **dict((k, v) for k, v in dict(kw4(pop, mat, bases), bases=bz).items() if k != "say"), say=lambda *a: None))
            eqp(out, u"下見: 壊していない土台(%s)は通る" % lab, len(MS.run_preview([n_b], **dict((k, v) for k, v in kw4(pop, mat, bases).items() if k != "say"), say=lambda *a: None)[1]), 6)
        expect_stop(out, u"本が母集団に無い", lambda: MS.run_preview([99], **dict((k, v) for k, v in kw4(pop, mat, bases).items() if k != "say"), say=lambda *a: None))
    return out


# ---- 土台の記録の読み(本物の記録・壊した写し)
def bases_problems():
    u"""load_bases: 本物の記録で 400 本・切れた 372(A 239・丙 133)・切れない 28。壊した写し(丙の本が足りない・丙の sha256 が違う)は止まる。"""
    out = []
    pop = S2.load_population(ROOT)
    bases = MS.load_bases(ROOT, pop)
    sel, uncut = MS.selection(pop, bases)
    eqp(out, u"記録の本の数", len(bases), 400)
    tss_b = dict((b[u"#"], b) for b in TSS.load_json(os.path.join(ROOT, STATES_REL))[u"本"])
    int_b = dict((b[u"#"], b) for b in TSS.load_json(os.path.join(ROOT, INTERIM_REL))[u"本"])
    eqp(out, u"A の土台は TSS の記録(写さない)", [bases[r[0]] == tss_b[r[0]] for r in pop if r[1] in (u"甲", u"乙")].count(False), 0)
    eqp(out, u"丙の土台は interim の記録(期の名前を写した)", [bases[r[0]] == int_b[r[0]] for r in pop if r[1] == u"丙"].count(False), 0)
    eqp(out, u"丙の土台は TSS の記録(写さない)と違う本が在る(門の自己確認)", any(bases[r[0]] != tss_b[r[0]] for r in pop if r[1] == u"丙"), True)
    eqp(out, u"切れた本・切れない本(封 §0-1 の 1 と TSS の記録)", (len(sel), uncut), (372, 28))
    eqp(out, u"切れた本の群(A 239・丙 133)", (sum(1 for r in sel if r[1] in (u"甲", u"乙")), sum(1 for r in sel if r[1] == u"丙")), (239, 133))
    eqp(out, u"下見の指定(本 # 1〜12・251〜258)で切れた本", (len(MS.selection(pop, bases, set(range(1, 13)) | set(range(251, 259)))[0]), MS.selection(pop, bases, set(range(1, 13)) | set(range(251, 259)))[1]), (16, 4))
    expect_stop(out, u"母集団に無い # を指定する", lambda: MS.selection(pop, bases, set([9999])))
    with tmpdir() as d:
        root = os.path.join(d, "root")
        os.makedirs(os.path.join(root, os.path.dirname(MS.STATES_REL)))
        shutil.copy(os.path.join(ROOT, MS.STATES_REL), os.path.join(root, MS.STATES_REL))
        irec = json.load(open(os.path.join(ROOT, MS.INTERIM_REL), encoding="utf-8"))
        ip = os.path.join(root, MS.INTERIM_REL)

        def put(rec):
            with open(ip, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False))
        put(irec)
        eqp(out, u"壊していない写しは通る", len(MS.load_bases(root, pop)), 400)
        r2 = copy.deepcopy(irec)
        r2[u"本"] = r2[u"本"][1:]
        put(r2)
        expect_stop(out, u"interim の記録に丙の本が足りない", lambda: MS.load_bases(root, pop))
        r3 = copy.deepcopy(irec)
        r3[u"本"][0][u"ZIP の sha256"] = u"0" * 64
        put(r3)
        expect_stop(out, u"interim の記録の本の sha256 が母集団と違う", lambda: MS.load_bases(root, pop))
        r4 = copy.deepcopy(irec)
        r4[u"本"][-1][u"ZIP の sha256"] = u"0" * 64
        put(r4)
        expect_stop(out, u"interim の記録の最後の本の sha256 が違う", lambda: MS.load_bases(root, pop))
        put(irec)
        srec = json.load(open(os.path.join(ROOT, MS.STATES_REL), encoding="utf-8"))
        srec[u"本"][-1][u"ZIP の sha256"] = u"0" * 64
        sp = os.path.join(root, MS.STATES_REL)
        with open(sp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(srec, ensure_ascii=False))
        expect_stop(out, u"TSS の記録の最後の本の sha256 が違う", lambda: MS.load_bases(root, pop))
        shutil.copy(os.path.join(ROOT, MS.STATES_REL), sp)
        pop2 = [tuple(r) for r in pop]
        pop2[0] = (pop2[0][0], pop2[0][1], pop2[0][2], u"0" * 64)
        put(irec)
        expect_stop(out, u"母集団の sha256 が TSS の記録と違う", lambda: MS.load_bases(root, pop2))
    return out


# ---- 紙・札
def passed_rec(rows):
    return {u"行": rows}


def sheet_types_problems():
    u"""紙(repo の外だけ・在れば書かない・通した行 0 なら作らない・作り直せない行は止まる)と札の file(番号がそろう・a〜d・同じ番号・通した行 0 なら作らない・check_clean を通る)。"""
    out = []
    P = RESULT_WORDS[0]
    items = MS.passed_items(passed_rec([{u"本の #": 5, u"id": u"B5-T1-01", u"型": "T1_VALUE", u"P33E": {u"結果": P}}, {u"本の #": 5, u"id": u"B5-T1-02", u"型": "T1_VALUE", u"P33E": {u"結果": RESULT_WORDS[1]}},
                                       {u"本の #": 7, u"id": u"B7-T8-01", u"型": "T8_REL", u"P33E": {u"結果": P}}]))
    eqp(out, u"通した行だけ・番号は 1 から・記録の順", [(k, n, r[u"id"]) for k, n, r in items], [(1, 5, u"B5-T1-01"), (2, 7, u"B7-T8-01")])
    t9 = MS.passed_items(passed_rec([{u"本の #": 5, u"id": u"B5-T9-01", u"型": "T9_PRIOR_TO_CURRENT", u"P33E": {u"結果": P}}, {u"本の #": 5, u"id": u"B5-T1-01", u"型": "T1_VALUE", u"P33E": {u"結果": P}}]))
    eqp(out, u"通した行に T9 も入る(参考の型も読む)", [r[u"id"] for _k, _n, r in t9], [u"B5-T9-01", u"B5-T1-01"])
    saved = ts_state()
    fake = lambda res, base: {u"対応": True, u"結果": P, u"state": u"GROUNDED", u"reason": None}
    with tmpdir() as d:
        pop, mat, bases, zips = fixture4(d)
        kw = kw4(pop, mat, bases)
        os.makedirs(os.path.join(d, "o"))
        with patched(TS, classify_ts=fake):                                                  # 全部の行が「通した」になる故障を差し込んで、紙・札の道を通す
            ip = os.path.join(d, "o", "inj_pass.json")
            rec = MS.run_inject(out=ip, **kw)
            eqp(out, u"全部の行が通した(門の自己確認)", sum(1 for r in rec[u"行"] if r[u"P33E"][u"結果"] == P), 18)
            sheet = os.path.join(d, "o", "sheet.txt")
            res = MS.run_sheet(ip, mat, sheet, root=ROOT, say=lambda *a: None, population=pop, bases=bases)
            eqp(out, u"紙の行の数", len(res), 18)
            txt = open(sheet, encoding="utf-8").read()
            eqp(out, u"紙は 18 ブロック・番号 1〜18", [int(x) for x in re.findall(r"^=== 番号 (\d+) /", txt, re.M)], list(range(1, 19)))
            eqp(out, u"紙は文と差し替えを持つ(repo の外の紙)", (u"売上高" in txt, u"元の字 → 差し替えの字" in txt, u"結果: 通した" in txt), (True, True, True))
            eqp(out, u"紙の本の # は記録の順", [int(x) for x in re.findall(r"本 # (\d+) /", txt)], [1] * 6 + [2] * 6 + [3] * 6)
            for n_b, lab in ((1, u"甲"), (2, u"乙"), (3, u"丙")):
                for how, bz in broken_bases(bases, n_b):
                    sz = os.path.join(d, "o", "sheet_bz_%d_%d.txt" % (n_b, len(how)))
                    expect_stop(out, u"紙: %s の本の土台の記録が違う(%s)" % (lab, how), lambda bz=bz, sz=sz: MS.run_sheet(ip, mat, sz, root=ROOT, say=lambda *a: None, population=pop, bases=bz))
            expect_stop(out, u"紙が repo の中", lambda: MS.run_sheet(ip, mat, os.path.join(ROOT, "x_sheet_probe.txt"), root=ROOT, say=lambda *a: None, population=pop, bases=bases))
            if os.path.exists(os.path.join(ROOT, "x_sheet_probe.txt")):
                out.append(u"repo の中に紙を書いた")
                os.remove(os.path.join(ROOT, "x_sheet_probe.txt"))
            expect_stop(out, u"紙が既に在る", lambda: MS.run_sheet(ip, mat, sheet, root=ROOT, say=lambda *a: None, population=pop, bases=bases))
            # 札
            typed = os.path.join(d, "o", "typed.txt")
            with open(typed, "w", encoding="utf-8") as fh:
                fh.write(u"\n".join(u"%d\t%s" % (i, u"abcd"[i % 4]) for i in range(1, 19)) + u"\n")
            tp = os.path.join(d, "o", "types.json")
            trec = MS.run_types(ip, typed, tp, root=ROOT, say=lambda *a: None)
            eqp(out, u"札の集計(1〜18 を a b c d の順)", dict(trec[u"札の集計"]), {u"a": 4, u"b": 5, u"c": 5, u"d": 4})
            eqp(out, u"札の行の欄・先頭の行", (trec[u"行の欄"], trec[u"行"][0]), ([u"番号", u"本の #", u"id", u"型", u"札"], [1, 1, rec[u"行"][0][u"id"], rec[u"行"][0][u"型"], u"b"]))
            eqp(out, u"札の記録は文・値を持たない", [x in open(tp, encoding="utf-8").read() for x in (u"売上高", u"百万円", u'"value"')], [False] * 3)
            eqp(out, u"札を付けた席・盲検でない", (trec[u"札を付けた席"], u"盲検ではない" in trec[u"盲検"]), (TSS.TYPED_BY, True))
            eqp(out, u"札の記録の inject の sha256", trec[u"inject の記録の sha256"], ST.sha256_file(ip))
            with patched(ST, write_text_exclusive=boom):                                      # 出力が在ることは書く前に見つける
                expect_stop(out, u"出力が在る", lambda: MS.run_types(ip, typed, tp, root=ROOT, say=lambda *a: None))
            for label, lines in ((u"番号が足りない", [u"%d\ta" % i for i in range(1, 18)]), (u"札が 4 つの外", [u"%d\te" % i for i in range(1, 19)]), (u"番号が重なる", [u"1\ta"] + [u"%d\ta" % i for i in range(1, 19)]),
                                 (u"列が違う", [u"%d a" % i for i in range(1, 19)]), (u"列が 3 つ", [u"%d\ta\tx" % i for i in range(1, 19)]), (u"番号が 19", [u"%d\ta" % i for i in range(2, 20)])):
                bad = os.path.join(d, "o", "bad.txt")
                with open(bad, "w", encoding="utf-8") as fh:
                    fh.write(u"\n".join(lines) + u"\n")
                bo = os.path.join(d, "o", "bad_%d.json" % len(label))
                expect_stop(out, u"札の file: %s" % label, lambda: MS.run_types(ip, bad, bo, root=ROOT, say=lambda *a: None))
                if os.path.exists(bo):
                    out.append(u"札の file が壊れているのに書いた: %s" % label)
            # check_clean を通る(止める故障を差し込む)
            calls = []

            def faulty(rec_, text_, key_value=None):
                calls.append(1)
                raise MS.Stop(u"差し込んだ故障")
            with patched(MS, check_clean=faulty):
                expect_stop(out, u"run_types が check_clean を呼ばない", lambda: MS.run_types(ip, typed, os.path.join(d, "o", "wt.json"), root=ROOT, say=lambda *a: None))
            eqp(out, u"run_types は check_clean を 1 回呼ぶ", calls, [1])
            if os.path.exists(os.path.join(d, "o", "wt.json")):
                out.append(u"check_clean が止めたのに札の記録を書いた")
        # 注入の結果が通したでなくなったら紙を作り直せない
        sheet2 = os.path.join(d, "o", "sheet2.txt")
        expect_stop(out, u"通した行を作り直せない", lambda: MS.run_sheet(ip, mat, sheet2, root=ROOT, say=lambda *a: None, population=pop, bases=bases))
        if os.path.exists(sheet2):
            out.append(u"作り直せないのに紙を書いた")
        # 通した行 0 なら紙も札も作らない
        ip0 = os.path.join(d, "o", "inj_none.json")
        MS.run_inject(out=ip0, **kw)
        s0, t0 = os.path.join(d, "o", "s0.txt"), os.path.join(d, "o", "t0.json")
        eqp(out, u"通した行 0 なら紙は作らない", (MS.run_sheet(ip0, mat, s0, root=ROOT, say=lambda *a: None, population=pop, bases=bases), os.path.exists(s0)), ([], False))
        eqp(out, u"通した行 0 なら札は作らない", (MS.run_types(ip0, typed, t0, root=ROOT, say=lambda *a: None), os.path.exists(t0)), (None, False))
        eqp(out, u"紙・札を作ったあとも元の対", ts_state(), saved)
    return out


def clean_problems():
    u"""記録に repo へ入れない欄・鍵らしい字が在れば止まる。3 つの封の path は長い英数字だが鍵に数えない。"""
    out = []
    ok = collections.OrderedDict([(u"seal", MS.SEAL_REL), (u"x", S2.SEAL_REL), (u"y", TSS.SEAL_REL), (u"本", [{u"行": [[1, 2]]}])])
    try:
        MS.check_clean(ok, json.dumps(ok, ensure_ascii=False))
    except SystemExit:
        out.append(u"良い記録で止まった")
    for key in (u"span", u"value", u"recomputed", u"text", u"文", u"sentence"):
        bad = collections.OrderedDict([(u"本", [{key: u"x"}])])
        expect_stop(out, u"欄 %s" % key, lambda bad=bad: MS.check_clean(bad, json.dumps(bad, ensure_ascii=False)))
    leak = collections.OrderedDict([(u"x", u"a" * 40 + u"Z" * 8)])
    expect_stop(out, u"鍵らしい字", lambda: MS.check_clean(leak, json.dumps(leak, ensure_ascii=False)))
    long_other = collections.OrderedDict([(u"x", u"docs/OTHER_LONG_NAME_SEAL_FOR_TEST_2026-11-14.md")])
    expect_stop(out, u"封でない長い英数字の連なり", lambda: MS.check_clean(long_other, json.dumps(long_other, ensure_ascii=False)))
    return out


def clean_wiring_problems():
    u"""check_clean が run_inject から呼ばれる(正常な記録では発火しない守りなので、止める故障を差し込んで止まり何も書かないことを見る)。"""
    out = []
    with tmpdir() as d:
        pop, mat, bases, zips = fixture4(d)
        calls = []

        def faulty(rec, text, key_value=None):
            calls.append(1)
            raise MS.Stop(u"差し込んだ故障")
        o = os.path.join(d, "o", "w.json")
        with patched(MS, check_clean=faulty):
            expect_stop(out, u"run_inject が check_clean を呼ばない", lambda: MS.run_inject(out=o, **kw4(pop, mat, bases)))
        eqp(out, u"run_inject は check_clean を 1 回呼ぶ", calls, [1])
        if os.path.exists(o):
            out.append(u"check_clean が止めたのに記録を書いた")
    return out


# ================================================================ 変異の表(約束の側から。関数の字を 1 か所替えた版を差し込み、検査が赤になることを見る)
@contextlib.contextmanager
def mutated(mod, name, old, new):
    u"""関数 ``name`` の字の ``old`` を ``new`` に替えた版を module の中に差し込む(contextmanager の関数は包み直す)。出るときは必ず元の object に戻す。"""
    orig = getattr(mod, name)
    src = inspect.getsource(orig)
    assert old in src, (name, old)
    exec(compile(src.replace(old, new, 1), "<mutant %s>" % name, "exec"), mod.__dict__)
    got = mod.__dict__[name]
    assert got is not orig
    if hasattr(orig, "__wrapped__") and not hasattr(got, "__wrapped__"):
        mod.__dict__[name] = contextlib.contextmanager(got)
    try:
        yield
    finally:
        mod.__dict__[name] = orig
        assert getattr(mod, name) is orig


def _m(label, fn, old, new, check):
    return (label, MS, fn, old, new, check)


MUTANTS = (
    # profile の対・切り替え(約束: with の中だけ・戻る・届いていなければ止める)
    _m(u"対を戻さない(出るとき元の対に戻さない)", "profile_pair", u"        TS.INJECT_PROFILES, TS.OLD, TS.NEW = old", u"        pass", device_problems),
    _m(u"OLD・NEW を差し替えない", "profile_pair", u"    TS.OLD = name\n    TS.NEW = name\n", u"", device_problems),
    _m(u"INJECT_PROFILES を差し替えない", "profile_pair", u"    TS.INJECT_PROFILES = (name, name)\n", u"", device_problems),
    _m(u"NEW だけ P32E のまま", "profile_pair", u"    TS.NEW = name\n", u"", device_problems),
    _m(u"切り替え yen_scan を真にしない", "device", u"with TS.NS.yen_scan_on():", u"with contextlib.nullcontext():", device_problems),
    _m(u"切り替え T5 を真にしない", "device", u"with TS.TY.t5_yen_on():", u"with contextlib.nullcontext():", device_problems),
    _m(u"出たあとに戻ったかを見ない", "device", u"    if after != before:\n        raise Stop(u\"**with を出ても元に戻っていない。止める**\")", u"    pass", device_problems),
    _m(u"届いていなくても with の中へ入る", "device", u"                if problems:\n                    raise Stop(u\"**差し替えが届いていない(with の中): %s。止める**\" % u\" / \".join(problems))", u"                pass", device_problems),
    _m(u"with の外の wiring_problems を見ない", "device", u"    bad = TS.wiring_problems()\n    if bad:", u"    bad = []\n    if bad:", device_problems),
    _m(u"切り替えが真のまま始めても止めない", "device", u"    if before[u\"切り替え \" + TS.TY.FLAG] or before[u\"切り替え \" + TS.TY.FLAG2]:", u"    if False:", device_problems),
    _m(u"届き方の検査が INJECT_PROFILES を見ない", "reach_problems", u"    if tuple(g[\"INJECT_PROFILES\"]) != (name, name):", u"    if False:", device_problems),
    _m(u"届き方の検査が OLD・NEW を見ない", "reach_problems", u"    if g[\"OLD\"] != name or g[\"NEW\"] != name:", u"    if False:", device_problems),
    _m(u"届き方の検査が base_pair の中を見ない", "reach_problems", u"        if tuple(TS.RM.INJECT_PROFILES) != (name, name):", u"        if False:", device_problems),
    _m(u"届き方の検査が t8 の土台の差し替えを見ない", "reach_problems", u"        if TS.RUN.t8_candidates4.__globals__[\"base_status4\"] is not TS.base_status_ts:", u"        if False:", device_problems),
    _m(u"届き方の検査が切り替えを見ない", "reach_problems", u"    if not getattr(TS.N, TS.TY.FLAG) or not getattr(TS.S, TS.TY.FLAG2):", u"    if False:", device_problems),
    _m(u"配線の記録に戻ったかを書かない(常に真)", "device", u"    wiring[u\"元に戻った\"] = bool(after == before)", u"    wiring[u\"元に戻った\"] = True", device_problems),
    # refs(約束: 先頭から・同じ key は最初の 1 件・None は飛ばす・float にできないものは飛ばして数える)
    _m(u"refs: 同じ key の 2 件目を採る", "refs_from_facts", u"        if key in seen:", u"        if False:", refs_problems),
    _m(u"refs: 同じ key の最後を採る(上書き)", "refs_from_facts", u"        if key in seen:\n            continue\n        seen.add(key)\n        refs.append(", u"        seen.add(key)\n        refs[:] = [x for x in refs if x[\"key\"] != key]\n        refs.append(", refs_problems),
    _m(u"refs: None を飛ばさない", "refs_from_facts", u"        if f.get(\"value\") is None:\n            continue\n", u"", refs_problems),
    _m(u"refs: float にできないと止まる", "refs_from_facts", u"        except (TypeError, ValueError, OverflowError):", u"        except OverflowError:", refs_problems),
    _m(u"refs: 飛ばした数を数えない", "refs_from_facts", u"            skipped += 1", u"            pass", refs_problems),
    _m(u"refs: float にできない fact が key を使った扱いになる", "refs_from_facts", u"            skipped += 1\n            continue", u"            skipped += 1\n            seen.add(u\"%s@%s\" % (f[\"name\"].split(u\":\")[-1], f[\"context\"]))\n            continue", refs_problems),
    _m(u"refs: 要素名を最初の : の後ろで切る", "refs_from_facts", u"el = f[\"name\"].split(u\":\")[-1]", u"el = f[\"name\"].split(u\":\")[1]", refs_problems),
    _m(u"refs: key に context を入れない", "refs_from_facts", u"key = u\"%s@%s\" % (el, f[\"context\"])", u"key = el", refs_problems),
    _m(u"refs: unit を素通しにする", "refs_from_facts", u"PM._money_unit_label(f.get(\"unit\"))", u"f.get(\"unit\")", refs_problems),
    _m(u"refs: 値を float にしない", "refs_from_facts", u"\"value\": value,", u"\"value\": f[\"value\"],", refs_problems),
    _m(u"refs: 先頭でなく末尾から見る", "refs_from_facts", u"    for f in facts:", u"    for f in reversed(list(facts)):", refs_problems),
    # 1 本の注入(約束: 丙にだけ読み替え・種・cap・名前・第 1 引数・検証の関数・土台の確かめ)
    _m(u"丙に期の名前の読み替えを掛けない", "inject_book", u"S2.prepare(zb, grp in B_GROUPS)", u"S2.prepare(zb, False)", book_problems),
    _m(u"A にも読み替えを掛ける", "inject_book", u"S2.prepare(zb, grp in B_GROUPS)", u"S2.prepare(zb, True)", book_problems),
    _m(u"種を変える", "inject_book", u"SEED, book_name(n), cap=CAP", u"SEED + 1, book_name(n), cap=CAP", book_problems),
    _m(u"cap を変える", "inject_book", u"SEED, book_name(n), cap=CAP", u"SEED, book_name(n), cap=CAP + 1", book_problems),
    _m(u"cap を渡さない", "inject_book", u"SEED, book_name(n), cap=CAP", u"SEED, book_name(n), cap=None", book_problems),
    _m(u"本の名前を # だけにする", "inject_book", u"SEED, book_name(n), cap=CAP", u"SEED, u\"%d\" % n, cap=CAP", book_problems),
    _m(u"第 1 引数に包む前の ZIP を渡す", "inject_book", u"TS.inject_text_ts(wrapped, text, refs", u"TS.inject_text_ts(zb2, text, refs", book_problems),
    _m(u"検証が無改変の ZIP のまま", "inject_book", u"return VD.verify_document(TSS.wrap(zb2, t)[0], p)", u"return VD.verify_document(wrapped, p)", book_problems),
    _m(u"検証が元の ZIP を包む(読み替える前)", "inject_book", u"return VD.verify_document(TSS.wrap(zb2, t)[0], p)", u"return VD.verify_document(TSS.wrap(zb, t)[0], p)", book_problems),
    _m(u"土台の確かめをしない", "inject_book", u"    if ref_triples is not None and triples != [tuple(t) for t in ref_triples]:", u"    if False:", book_problems),
    _m(u"土台の確かめが state を見ない", "inject_book", u"triples = [(r[0], r[1], r[2]) for r in book[u\"行\"]]", u"triples = [(r[0], r[1], None) for r in book[u\"行\"]]", book_problems),
    _m(u"切れない本にも注入する", "inject_book", u"    if not out[u\"切り出し\"]:", u"    if False:", book_problems),
    _m(u"差し替えの外でも走る(本の job の守りを外す)", "inject_book", u"    if tuple(TS.INJECT_PROFILES) != (PROFILE, PROFILE) or not getattr(TS.N, TS.TY.FLAG) or not getattr(TS.S, TS.TY.FLAG2):", u"    if False:", book_problems),
    _m(u"GROUNDED の行を全行にする", "inject_book", u"sum(1 for t in triples if t[2] == TS.G)", u"len(triples)", book_problems),
    _m(u"refs の数を数えない", "inject_book", u"out[u\"refs の数\"] = len(refs)", u"out[u\"refs の数\"] = 0", book_problems),
    _m(u"行に 本の #・群 を足さない", "inject_book", u"[(u\"本の #\", n), (u\"群\", grp)] + list(r.items())", u"list(r.items())", book_problems),
    _m(u"refs: 値 0 の fact を飛ばす(not value)", "refs_from_facts", u"        if f.get(\"value\") is None:", u"        if not f.get(\"value\"):", refs_problems),
    _m(u"土台の確かめを集合で比べる(行の順を見ない)", "inject_book", u"triples != [tuple(t) for t in ref_triples]", u"set(triples) != set(tuple(t) for t in ref_triples)", book_problems),
    _m(u"土台の確かめが位置を見ない", "inject_book", u"triples = [(r[0], r[1], r[2]) for r in book[u\"行\"]]", u"triples = [(r[0], None, r[2]) for r in book[u\"行\"]]", book_problems),
    _m(u"土台の確かめが文の番号を見ない", "inject_book", u"triples = [(r[0], r[1], r[2]) for r in book[u\"行\"]]", u"triples = [(None, r[1], r[2]) for r in book[u\"行\"]]", book_problems),
    _m(u"記録は切れた・作り直しは切れないでも止めない", "inject_book", u"        if ref_triples is not None:\n            raise Stop(", u"        if False:\n            raise Stop(", book_problems),
    _m(u"refs で飛ばした fact を書かない(0 固定)", "inject_book", u"out[u\"refs で飛ばした fact\"] = skipped", u"out[u\"refs で飛ばした fact\"] = 0", book_problems),
    _m(u"丙の本では土台の確かめを飛ばす", "inject_book", u"    if ref_triples is not None and triples != [tuple(t) for t in ref_triples]:", u"    if ref_triples is not None and grp not in B_GROUPS and triples != [tuple(t) for t in ref_triples]:", book_problems),
    _m(u"refs: unit None の fact を円にする", "refs_from_facts", u"PM._money_unit_label(f.get(\"unit\"))", u"PM._money_unit_label(f.get(\"unit\") or u\"JPY\")", refs_problems),
    _m(u"来歴: 母集団の記録の sha256 に別の file の sha256", "head_fields", u"ST.sha256_file(os.path.join(root, ST.POPULATION_REL))", u"ST.sha256_file(os.path.join(root, STATES_REL))", run_problems),
    _m(u"来歴: TSS の script の sha256 に別の file の sha256", "head_fields", u"os.path.basename(TSS_SCRIPT_REL)", u"os.path.basename(S2_SCRIPT_REL)", run_problems),
    _m(u"来歴: 第 2 便の script の sha256 に別の file の sha256", "head_fields", u"os.path.basename(S2_SCRIPT_REL)", u"os.path.basename(TSS_SCRIPT_REL)", run_problems),
    _m(u"来歴: 置く script の sha256 に別の file の sha256", "head_fields", u"os.path.basename(TSS.STAGE_SCRIPT_REL)", u"os.path.basename(TSS_SCRIPT_REL)", run_problems),
    _m(u"来歴: 2026-11-09 の便の script の sha256 に別の file の sha256", "head_fields", u"os.path.basename(TSS.TS_SCRIPT_REL)", u"os.path.basename(TSS_SCRIPT_REL)", run_problems),
    _m(u"来歴: TSS の判定の記録の sha256 に interim の sha256", "head_fields", u"ST.sha256_file(os.path.join(root, STATES_REL))", u"ST.sha256_file(os.path.join(root, INTERIM_REL))", run_problems),
    _m(u"来歴: interim の記録の sha256 に TSS の sha256", "head_fields", u"ST.sha256_file(os.path.join(root, INTERIM_REL))", u"ST.sha256_file(os.path.join(root, STATES_REL))", run_problems),
    _m(u"来歴: 仕掛けの 2 file の sha256 を lib の file で作る", "head_fields", u"for rel in TS.DEVICE_RELS)", u"for rel in TS.LIB_RELS)", run_problems),
    _m(u"job が丙のときだけ土台の記録を渡さない", "job", u"return inject_book(n, grp, kind, sha, zb, ref_triples)", u"return inject_book(n, grp, kind, sha, zb, None if grp in B_GROUPS else ref_triples)", run_problems),
    _m(u"jobs_of が丙のときだけ土台の行を None にする", "jobs_of", u"sha + u\".zip\"), tr) for", u"sha + u\".zip\"), (None if g in B_GROUPS else tr)) for", run_problems),
    _m(u"job が土台の記録を渡さない", "job", u"return inject_book(n, grp, kind, sha, zb, ref_triples)", u"return inject_book(n, grp, kind, sha, zb, None)", run_problems),
    _m(u"紙: 丙の本の土台の記録を渡さない", "run_sheet", u"[t[:3] for t in bases[num][u\"行\"]], capture=cap)", u"(None if grp in B_GROUPS else [t[:3] for t in bases[num][u\"行\"]]), capture=cap)", sheet_types_problems),
    _m(u"紙: 甲の本の土台の記録を渡さない", "run_sheet", u"[t[:3] for t in bases[num][u\"行\"]], capture=cap)", u"(None if grp in A_GROUPS else [t[:3] for t in bases[num][u\"行\"]]), capture=cap)", sheet_types_problems),
    _m(u"refs の数に飛ばした数を足す", "inject_book", u"out[u\"refs の数\"] = len(refs)", u"out[u\"refs の数\"] = len(refs) + skipped", book_problems),
    _m(u"capture の build_row を戻さない", "inject_book", u"    finally:\n        TS.build_row = original", u"    finally:\n        pass", book_problems),
    (u"TSS の記録の最後の本の sha256 を見ない(最初の本だけ)", S2, "load_tss_states", u"for r in pop)", u"for r in pop[:1])", bases_problems),
    _m(u"interim の記録の最後の本の sha256 を見ない(最初の本だけ)", "load_bases", u"for k in ibooks):", u"for k in list(ibooks)[:1]):", bases_problems),
    _m(u"with を出たあとの wiring_problems で止めない", "device", u"    if wiring[u\"2026-11-09 の便の wiring_problems(with の外・前と後)\"]:\n        raise Stop(u\"**with を出たあとの配線の問題。止める**\")", u"    pass", device_problems),
    _m(u"切り替えの記録の出たあとの値を偽に書く", "run_inject", u"(u\"出たあとの値\", wiring[u\"with の後\"][u\"切り替え \" + TS.TY.FLAG])", u"(u\"出たあとの値\", False)", run_problems),
    _m(u"切り替えの記録の中の値を真に書く", "run_inject", u"(u\"inject の中の値\", wiring[u\"with の中\"][u\"切り替え \" + TS.TY.FLAG])", u"(u\"inject の中の値\", True)", run_problems),
    _m(u"T5 の切り替えの記録の出たあとの値を偽に書く", "run_inject", u"(u\"T5 の切り替え 出たあとの値\", wiring[u\"with の後\"][u\"切り替え \" + TS.TY.FLAG2])", u"(u\"T5 の切り替え 出たあとの値\", False)", run_problems),
    _m(u"覆い: GROUNDED がちょうど 1 行の本を 1 行以上に数えない", "coverage", u"g1 = [p for p in sel if p[u\"P33E が GROUNDED の行\"] >= 1]", u"g1 = [p for p in sel if p[u\"P33E が GROUNDED の行\"] > 1]", coverage_problems),
    _m(u"紙: 通した行から T9 を外す", "passed_items", u"if r[PROFILE][u\"結果\"] == LABEL_PASS]", u"if r[PROFILE][u\"結果\"] == LABEL_PASS and r[u\"型\"] != u\"T9_PRIOR_TO_CURRENT\"]", sheet_types_problems),
    _m(u"下見: 届いた数を出さない", "run_preview", u"sum(1 for r in sel_t if r[u\"届いた\"])", u"0", preview_problems),
    # 集計・覆い
    _m(u"通した率の分母が対応が付いた行", "type_block", u"(u\"率\", pct(len(passed), n))", u"(u\"率\", pct(len(passed), len(linked)))", summary_problems),
    _m(u"届いた率の分母が注入の行", "type_block", u"pct(len(reached), len(linked))", u"pct(len(reached), n)", summary_problems),
    _m(u"届いたを対応が付かない行からも数える", "type_block", u"reached = [r for r in linked if r[u\"届いた\"]]", u"reached = [r for r in rows if r[u\"届いた\"]]", summary_problems),
    _m(u"通した行の届いていない数を数えない", "type_block", u"sum(1 for r in passed if not r[u\"届いた\"])", u"0", summary_problems),
    _m(u"結果の語の率の分母が対応が付いた行", "type_block", u"pct(c.get(w, 0), n)", u"pct(c.get(w, 0), len(linked))", summary_problems),
    _m(u"通したの判定が逆", "type_block", u"passed = [r for r in rows if r[PROFILE][u\"結果\"] == LABEL_PASS]", u"passed = [r for r in rows if r[PROFILE][u\"結果\"] != LABEL_PASS]", summary_problems),
    _m(u"round-trip 不一致の数が逆", "type_block", u"sum(1 for r in rows if not r[u\"round-trip\"])", u"sum(1 for r in rows if r[u\"round-trip\"])", summary_problems),
    _m(u"読み直し不一致を数えない", "type_block", u"sum(1 for r in rows if not r[u\"読み直し\"])", u"0", summary_problems),
    _m(u"群で割らない", "summary", u"if group_name(r[u\"群\"]) == g]", u"if True]", summary_problems),
    _m(u"群の名前が逆", "group_name", u"u\"A\" if grp in A_GROUPS else u\"丙\"", u"u\"A\" if grp in B_GROUPS else u\"丙\"", summary_problems),
    _m(u"覆い: 率の分子が注入の行が 1 行以上の本の全部", "coverage", u"inj_g1 = [p for p in g1 if sum(p[u\"注入の行\"].values()) >= 1]", u"inj_g1 = inj", coverage_problems),
    _m(u"覆い: 率の分母が切れた本", "coverage", u"pct(len(inj_g1), len(g1))", u"pct(len(inj_g1), len(sel))", coverage_problems),
    _m(u"覆い: 作れる site が dict のままの合計でない", "site_total", u"sum(v.values()) if isinstance(v, dict) else (v or 0)", u"(v or 0) if not isinstance(v, dict) else v.get(u\"既存\", 0)", coverage_problems),
    _m(u"覆い: 円族の token を拾わない", "coverage", u"(u\"円族の token\", t8.get(u\"円族の token\"))", u"(u\"円族の token\", None)", coverage_problems),
    _m(u"覆い: 全角で注入しない本を数えない", "coverage", u"bool(counts.get(u\"注入しない\"))", u"False", coverage_problems),
    _m(u"覆い: 作れる site が 0 の本の判定が ≥", "coverage", u"p[u\"作れる site\"][TYPE_SHORT[t]] == 0)", u"p[u\"作れる site\"][TYPE_SHORT[t]] >= 0)", coverage_problems),
    _m(u"覆い: 型ごとの注入の行の本が 0 以上", "coverage", u"p[u\"注入の行\"][TYPE_SHORT[t]] >= 1)", u"p[u\"注入の行\"][TYPE_SHORT[t]] >= 0)", coverage_problems),
    _m(u"覆い: GROUNDED の行を本の数にする", "coverage", u"sum(p[u\"P33E が GROUNDED の行\"] for p in sel)", u"len(sel)", coverage_problems),
    # 記録(run_inject)
    _m(u"行に値の欄を足す", "inject_book", u"[(u\"本の #\", n), (u\"群\", grp)]", u"[(u\"本の #\", n), (u\"群\", grp), (u\"value\", 1)]", run_problems),
    _m(u"行に文の字を入れる", "inject_book", u"[(u\"本の #\", n), (u\"群\", grp)]", u"[(u\"本の #\", n), (u\"群\", grp), (u\"x\", text[:12])]", run_problems),
    _m(u"記録: check_clean を呼ばない", "run_inject", u"    check_clean(rec, text, key_value)\n", u"    pass\n", clean_wiring_problems),
    _m(u"記録: 鍵らしい字を見ない", "check_clean", u"    if leaks:", u"    if False:", clean_problems),
    _m(u"記録: 欄の禁止を見ない", "check_clean", u"    if bad:", u"    if False:", clean_problems),
    _m(u"記録: 封の path を外さず見る", "check_clean", u"text.replace(SEAL_REL, u\"\").replace(S2.SEAL_REL, u\"\").replace(TSS.SEAL_REL, u\"\")", u"text", clean_problems),
    _m(u"記録: 時間を測らない", "run_inject", u"    elapsed = clock() - t0", u"    elapsed = 0.0", run_problems),
    _m(u"記録: 出力が在っても書く", "run_inject", u"    if os.path.exists(out):", u"    if False:", run_problems),
    _m(u"記録: 材料の置き場が変わっても止めない", "run_inject", u"    if before != after:", u"    if False:", run_problems),
    _m(u"記録: 本の数えを # で引く", "run_inject", u"collections.OrderedDict((b[u\"名前\"], b[u\"数え\"]) for b in books)", u"collections.OrderedDict((b[u\"#\"], b[u\"数え\"]) for b in books)", run_problems),
    _m(u"記録: 注入の行の数が本の数", "run_inject", u"rec[u\"注入の行の数\"] = len(rows)", u"rec[u\"注入の行の数\"] = len(books)", run_problems),
    _m(u"記録: 本番の記録を使い捨ての材料で作る", "material_dir", u"if out is not None and os.path.abspath(out) in [", u"if False and os.path.abspath(out) in [", run_problems),
    _m(u"記録: 切れない本も対象にする", "selection", u"cut = [r for r in rows if bases[r[0]][u\"切り出し\"] == TSS.CUT_OK]", u"cut = list(rows)", run_problems),
    _m(u"記録: 切れない本の数を数えない", "selection", u"len(rows) - len(cut)", u"0", run_problems),
    _m(u"記録: 材料が無くても進む", "need_material", u"        if not os.path.exists(os.path.join(mat, sha + u\".zip\")):", u"        if False:", run_problems),
    _m(u"記録: 土台の確かめの違う本を 0 に固定せず行を数えない", "run_inject", u"(u\"本\", len(books)), (u\"行\", sum(b[u\"土台の行\"] for b in books))", u"(u\"本\", len(books)), (u\"行\", 0)", run_problems),
    _m(u"記録: 母集団の A と丙の数が逆", "run_inject", u"(u\"A\", sum(1 for b in books if group_name(b[u\"群\"]) == u\"A\")), (u\"丙\", sum(1 for b in books if group_name(b[u\"群\"]) == u\"丙\"))", u"(u\"A\", sum(1 for b in books if group_name(b[u\"群\"]) == u\"丙\")), (u\"丙\", sum(1 for b in books if group_name(b[u\"群\"]) == u\"A\"))", run_problems),
    # 土台の記録の読み
    _m(u"土台: interim の記録の本・sha256 を見ない", "load_bases", u"    if sorted(ibooks) != [r[0] for r in pop if r[1] in B_GROUPS] or any(ibooks[k][u\"ZIP の sha256\"] != shas[k] for k in ibooks):", u"    if False:", bases_problems),
    _m(u"土台: 丙の記録を使わない(A の記録だけ)", "load_bases", u"    for k, b in ibooks.items():\n        out[k] = b\n", u"", bases_problems),
    _m(u"土台: 記録で切れた本でなく全部を対象にする", "selection", u"cut = [r for r in rows if bases[r[0]][u\"切り出し\"] == TSS.CUT_OK]", u"cut = list(rows)", bases_problems),
    _m(u"土台: 指定した本が母集団に無くても止めない", "selection", u"    if nums is not None and sorted(nums) != [r[0] for r in rows]:", u"    if False:", bases_problems),
    # preview
    _m(u"下見: 指定した本以外も走らせる", "selection", u"rows = [r for r in pop if nums is None or r[0] in nums]", u"rows = list(pop)", preview_problems),
    # 紙・札
    _m(u"紙: 通した行の判定が逆", "passed_items", u"if r[PROFILE][u\"結果\"] == LABEL_PASS]", u"if r[PROFILE][u\"結果\"] != LABEL_PASS]", sheet_types_problems),
    _m(u"紙: repo の中でも書く", "run_sheet", u"    if TSS.inside_repo(sheet, repo):", u"    if False:", sheet_types_problems),
    _m(u"紙: 在っても書く", "run_sheet", u"    if os.path.exists(sheet):", u"    if False:", sheet_types_problems),
    _m(u"紙: 作り直した結果が通したでなくても書く", "run_sheet", u"                if r2 is None or r2[PROFILE][u\"結果\"] != LABEL_PASS:", u"                if r2 is None:", sheet_types_problems),
    _m(u"紙: 通した行 0 でも書く", "run_sheet", u"    if not items:\n        say(u\"通した行 0。紙は作らない\")\n        return items\n", u"", sheet_types_problems),
    _m(u"札: 番号がそろわなくても通す", "run_types", u"    if sorted(typed) != [it[0] for it in items]:", u"    if False:", sheet_types_problems),
    _m(u"札: 4 つの外の字を通す", "read_typed", u" or parts[1] not in PASSED_LABELS", u"", sheet_types_problems),
    _m(u"札: 列の数を見ない", "read_typed", u"len(parts) != 2 or ", u"", sheet_types_problems),
    _m(u"札: 同じ番号を通す", "read_typed", u"            if k in out:", u"            if False:", sheet_types_problems),
    _m(u"札: 出力が在っても書く", "run_types", u"    if os.path.exists(out):", u"    if False:", sheet_types_problems),
    _m(u"札: 通した行 0 でも書く", "run_types", u"    if not items:\n        say(u\"通した行 0。札の file は作らない\")\n        return None\n", u"", sheet_types_problems),
    _m(u"札: check_clean を呼ばない", "run_types", u"    check_clean(rec, text, key_value)\n", u"    pass\n", sheet_types_problems),
    _m(u"札: 札の集計が数えない", "run_types", u"rec[u\"札の集計\"] = collections.OrderedDict((t, counts.get(t, 0)) for t in PASSED_LABELS)", u"rec[u\"札の集計\"] = collections.OrderedDict((t, 0) for t in PASSED_LABELS)", sheet_types_problems),
)

def _wiring_mutants():
    u"""土台の記録を受け渡す所 × 壊し方(None を渡す・空を None に落とす)× 群(全部・甲だけ・丙だけ)の変異。表は報告に書いた。"""
    out = []

    def forms(expr, g):
        return [(u"None を渡す", u"None"), (u"甲だけ None を渡す", u"(None if %s in A_GROUPS else %s)" % (g, expr)), (u"丙だけ None を渡す", u"(None if %s in B_GROUPS else %s)" % (g, expr)),
                (u"空を None に落とす", u"(%s or None)" % expr), (u"甲だけ空を None に落とす", u"((%s or None) if %s in A_GROUPS else %s)" % (expr, g, expr)),
                (u"丙だけ空を None に落とす", u"((%s or None) if %s in B_GROUPS else %s)" % (expr, g, expr))]
    pool = u"job, jobs_of(sel, mat), procs)"
    sites = ((u"run_preview", pool, lambda e, g: u"job, [j[:5] + (%s,) for j in jobs_of(sel, mat)], procs)" % e, u"j[5]", u"j[1]", preview_problems),
             (u"run_inject", pool, lambda e, g: u"job, [j[:5] + (%s,) for j in jobs_of(sel, mat)], procs)" % e, u"j[5]", u"j[1]", run_problems),
             (u"jobs_of", u"sha + u\".zip\"), tr) for", lambda e, g: u"sha + u\".zip\"), %s) for" % e, u"tr", u"g", run_problems),
             (u"job", u"return inject_book(n, grp, kind, sha, zb, ref_triples)", lambda e, g: u"return inject_book(n, grp, kind, sha, zb, %s)" % e, u"ref_triples", u"grp", run_problems),
             (u"selection", u"[t[:3] for t in bases[r[0]][u\"行\"]])", lambda e, g: u"%s)" % e, u"[t[:3] for t in bases[r[0]][u\"行\"]]", u"r[1]", run_problems),
             (u"run_sheet", u"[t[:3] for t in bases[num][u\"行\"]], capture=cap)", lambda e, g: u"%s, capture=cap)" % e, u"[t[:3] for t in bases[num][u\"行\"]]", u"grp", sheet_types_problems))
    for fn, old, build, expr, g, chk in sites:
        for label, new_expr in forms(expr, g):
            out.append(_m(u"配線: %s が土台の記録を %s" % (fn, label), fn, old, build(new_expr, g), chk))
        if fn == u"selection":
            out.append(_m(u"配線: selection の土台の記録が全群で行 0", fn, old, u"[])", run_problems))
    out.append(_m(u"inject_book: 空の土台の記録(行 0)を「記録なし」と読む", "inject_book", u"        if ref_triples is not None:\n            raise Stop(", u"        if ref_triples:\n            raise Stop(", book_problems))
    out.append(_m(u"inject_book: 空の土台の記録(行 0)を比べない", "inject_book", u"    if ref_triples is not None and triples != [tuple(t) for t in ref_triples]:", u"    if ref_triples and triples != [tuple(t) for t in ref_triples]:", book_problems))
    return tuple(out)


def _compare_mutants():
    u"""土台の確かめの比べ方の軸(行数・行の場所・向き・本の #・procs)で、形を変えた変異。"""
    g = u"    if ref_triples is not None and triples != [tuple(t) for t in ref_triples]:"
    r = u"[tuple(t) for t in ref_triples]"
    out = []
    for label, new in ((u"最後の 1 行だけ比べない", u"triples[:-1] != %s[:-1]" % r), (u"先頭の 1 行を比べない", u"triples[1:] != %s[1:]" % r), (u"先頭の 2 行だけ比べる", u"triples[:2] != %s[:2]" % r),
                       (u"1 行おきにしか比べない", u"triples[::2] != %s[::2]" % r), (u"真ん中を比べない(先頭と最後だけ)", u"(triples[:1] + triples[-1:]) != (%s[:1] + %s[-1:])" % (r, r))):
        out.append(_m(u"比べ方: " + label, "inject_book", g, u"    if ref_triples is not None and %s:" % new, small_or_book(label)))
    for label, cond in ((u"土台が 1 行の本は確かめない", u"len(triples) != 1"), (u"作り直しが行 0 の本だけ確かめを飛ばす(逆向きの空)", u"triples"), (u"土台の記録が 1 行以下の本は確かめない", u"len(ref_triples) > 1"),
                        (u"土台の記録が 3 行以上の本は確かめない", u"len(ref_triples) < 3"), (u"本の # が 3 の本は確かめない", u"n != 3"), (u"本の # が 2 の本は確かめない", u"n != 2"), (u"本の # が 1 の本は確かめない", u"n != 1"),
                        (u"本の # が奇数の本は確かめない", u"n % 2 == 0"), (u"本の # が 4 の本は確かめない", u"n != 4"), (u"行数が 2 の本は確かめない", u"len(triples) != 2")):
        out.append(_m(u"比べ方: " + label, "inject_book", g, u"    if ref_triples is not None and %s and triples != %s:" % (cond, r), small_or_book(label)))
    for fn, old, newf in (("run_inject", u"books = TS.NF.map_pool(job, jobs_of(sel, mat), procs)", u"books = TS.NF.map_pool(job, jobs_of(sel, mat) if procs < 2 else [j[:5] + (None,) for j in jobs_of(sel, mat)], procs)"),
                          ("run_preview", u"books = TS.NF.map_pool(job, jobs_of(sel, mat), procs)", u"books = TS.NF.map_pool(job, jobs_of(sel, mat) if procs < 2 else [j[:5] + (None,) for j in jobs_of(sel, mat)], procs)")):
        out.append(_m(u"比べ方: %s が procs 2 以上のときだけ土台を渡さない" % fn, fn, old, newf, small_problems))
    return tuple(out)


def compare_problems():
    u"""比べ方の変異用: 3 行の本(book_problems)と 0・1・2 行の本・procs 2(small_problems)の両方。"""
    return book_problems() + small_problems()


def small_or_book(label):
    return compare_problems


MUTANTS = MUTANTS + _wiring_mutants() + _compare_mutants()

#: 定数の変異(``script_problems`` が赤になること)。(説明, 名前, 替えた値)
CONST_MUTANTS = (
    (u"種が違う", "SEED", 20261115),
    (u"種が文字列", "SEED", "20261114"),
    (u"cap が違う", "CAP", 40),
    (u"profile が違う", "PROFILE", "P32E"),
    (u"本の名前の接頭辞が違う", "NAME_PREFIX", "T"),
    (u"r の値が違う", "R_VALUES", (-0.10, -0.03, 0.03, 0.20)),
    (u"r が 3 つ", "R_VALUES", (-0.10, -0.03, 0.03)),
    (u"型が 3 つ", "TYPES", TYPE_NAMES[:3]),
    (u"主の型に T9 を入れる", "MAIN_TYPES", TYPE_NAMES),
    (u"結果の語が違う", "LABELS", RESULT_WORDS[:-1] + (u"対応が付かぬ",)),
    (u"封の commit が違う", "SEAL_COMMIT", "0000000"),
    (u"封の path が違う", "SEAL_REL", "docs/x.md"),
    (u"記録の path が違う", "INJECT_REL", "fixtures/xbrl/tanshin_self/inject.json"),
    (u"札の path が違う", "PASSED_TYPES_REL", "fixtures/xbrl/tanshin_self/x.json"),
    (u"本番の記録の guard が空", "PRODUCTION_RELS", ()),
    (u"土台の記録の path が違う", "INTERIM_REL", "fixtures/x.json"),
    (u"A の群が違う", "A_GROUPS", (u"甲",)),
    (u"丙の群に乙を入れる", "B_GROUPS", (u"乙", u"丙")),
    (u"札の字が 3 つ", "PASSED_LABELS", collections.OrderedDict(list(MS.PASSED_LABELS.items())[:3])),
    (u"札を付けた席の字が違う", "TYPED_BY", u"人"),
    (u"群の名前が違う", "GROUP_NAMES", (u"A", u"B")),
    (u"結果の文書の path が違う", "DOC_REL", "docs/x.md"),
)


def _ns():
    return types.SimpleNamespace(**dict((k, getattr(MS, k)) for k in dir(MS) if not k.startswith("__")))


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_seal_phrases_paths_and_prediction_rows_are_complete(self):
        self.assertEqual([], seal_problems(self.seal))

    def test_a_2_a_changed_key_phrase_turns_the_seal_check_red(self):
        for ph in SEAL_PHRASES:
            self.assertIn(ph, self.seal)
            mutated_seal = self.seal.replace(ph, ph[:-1] + u"？", 1)
            self.assertNotEqual(mutated_seal, self.seal)
            self.assertNotEqual([], seal_problems(mutated_seal), ph)

    def test_a_3_a_broken_row_or_path_turns_it_red(self):
        lines = self.seal.split("\n")
        v7 = [i for i, ln in enumerate(lines) if ln.startswith("- **V-7**")][0]
        self.assertNotEqual([], seal_problems("\n".join(lines[:v7] + lines[v7 + 1:])))                                  # 11 行が 10 行
        self.assertNotEqual([], seal_problems(self.seal.replace("## §5 ", "## 五 ", 1)))                                # 節が揃わない
        self.assertNotEqual([], seal_problems(self.seal.replace(INJECT_REL, "fixtures/xbrl/tanshin_self/other.json")))
        self.assertNotEqual([], seal_problems(self.seal.replace(u"test_xbrl_tanshin_self_inject_result.py", u"test_other.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace(DOC_REL, "docs/OTHER.md")))

    def test_a_4_the_seal_is_in_history_as_the_sealed_commit(self):
        added = PR.added_commits(REPO, PREFIX + SEAL_REL)
        self.assertEqual(1, len(added))
        self.assertTrue(added[0].startswith(SEAL_COMMIT_SHORT))


def limits_problems(seal, ms=None):
    u"""記録の「限界」は封 §6 の 7 行と一字一句同じ(封の file から読んで比べる)。言い換え・足し引き・順の入れ替えで赤。"""
    ms = ms or MS
    try:
        sec = seal[seal.index(u"## §6"):seal.index(u"## §7")]
    except ValueError:
        return [u"封の節(§6・§7)が読めない"]
    want = [ln[2:] for ln in sec.split(u"\n") if ln.startswith(u"- ")]
    out = []
    if len(want) != 7:
        out.append(u"封 §6 が 7 行でない")
    if list(ms.INJECT_LIMITS) != want:
        out.append(u"限界の字が封 §6 と違う")
    return out


class ScriptConstantTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_b_1_the_script_constants_equal_the_seal(self):
        self.assertEqual([], script_problems(self.seal))

    def test_b_1b_the_limits_are_the_seal_section_6_verbatim(self):
        self.assertEqual([], limits_problems(self.seal))
        ms2 = _ns()
        ms2.INJECT_LIMITS = tuple(ms2.INJECT_LIMITS) + (MS.FIELD_NAME_NOTE,)
        self.assertNotEqual([], limits_problems(self.seal, ms=ms2))
        ms3 = _ns()
        ms3.INJECT_LIMITS = tuple(ms3.INJECT_LIMITS[:-1]) + (ms3.INJECT_LIMITS[-1][:-1],)
        self.assertNotEqual([], limits_problems(self.seal, ms=ms3))
        ms4 = _ns()
        ms4.INJECT_LIMITS = tuple(reversed(ms4.INJECT_LIMITS))
        self.assertNotEqual([], limits_problems(self.seal, ms=ms4))
        self.assertNotEqual([], limits_problems(self.seal.replace(u"上場会社全体の率ではない。", u"上場会社全体の率でない。")))

    def test_b_2_the_population_is_read_from_the_records_not_copied_into_the_script(self):
        pop = S2.load_population(ROOT)
        self.assertEqual(400, len(pop))
        for rel in (SCRIPT_REL, GATE_REL):
            src = read(rel)
            self.assertEqual([], [r[0] for r in pop if r[3] in src], rel)

    def test_b_3_each_script_constant_turns_the_check_red_when_changed(self):
        silent = []
        for label, name, val in CONST_MUTANTS:
            ms2 = _ns()
            setattr(ms2, name, val)
            if not script_problems(self.seal, ms=ms2):
                silent.append(label)
        self.assertEqual([], silent)
        ms3 = _ns()
        ms3.ST = types.SimpleNamespace()
        self.assertNotEqual([], script_problems(self.seal, ms=ms3))

    def test_b_4_a_changed_character_in_the_seal_turns_the_comparison_red(self):
        self.assertNotEqual([], script_problems(self.seal.replace(u"止めたが名指さない(POINTER_NOT_FOUND)", u"止めたが名指さぬ(POINTER_NOT_FOUND)",)))
        self.assertNotEqual([], script_problems(self.seal.replace(u"(c) 対応付けが別の claim を指した", u"(c) 対応付けが別の claim を指さない",)))
        self.assertNotEqual([], script_problems(self.seal.replace(u"`float` にできない fact", u"`int` にできない fact",)))

    def test_b_5_the_constants_are_pinned_by_value(self):
        self.assertEqual((20261114, 10, "P33E", "B"), (MS.SEED, MS.CAP, MS.PROFILE, MS.NAME_PREFIX))
        self.assertEqual((-0.10, -0.03, 0.03, 0.10), tuple(MS.R_VALUES))
        self.assertEqual(TYPE_NAMES, tuple(MS.TYPES))


class EngineZeroTest(unittest.TestCase):
    def test_c_1_the_real_history_has_no_engine_lib_device_or_previous_stage_change_since_the_seal(self):
        self.assertEqual([], untouched_problems())

    def _repo(self):
        r = PR.Repo()
        rels = [rel + ("" if "." in os.path.basename(rel) else "/a.py") for rel in NOT_TOUCHED_RELS] + ["measure/free.py"]
        for rel in rels:
            r.put(rel)
        r.commit(*rels)
        r.put("docs/seal.md")
        r.commit("docs/seal.md")
        return r

    def _problems(self, r):
        return G2.untouched_problems(root=r.d, seal_rel="docs/seal.md", rels=NOT_TOUCHED_RELS)

    def test_c_2_a_clean_range_is_green_and_each_touched_path_is_red_committed_or_not(self):
        r = self._repo()
        self.assertEqual([], self._problems(r))
        r.put("measure/free.py")                                      # 関係の無い file は触ってよい(未 commit のまま)
        self.assertEqual([], self._problems(r))
        for rel in NOT_TOUCHED_RELS:
            real = rel + ("" if "." in os.path.basename(rel) else "/a.py")
            r = self._repo()
            r.put(real)
            self.assertNotEqual([], self._problems(r), real + " (未 commit)")
            r.commit(real)
            self.assertNotEqual([], self._problems(r), real)

    def test_c_3_this_stages_own_records_are_not_in_the_frozen_list(self):
        for rel in (INJECT_REL, PASSED_TYPES_REL):
            self.assertNotIn(rel, NOT_TOUCHED_RELS)
            self.assertFalse(any(rel.startswith(x.rstrip("/") + "/") for x in NOT_TOUCHED_RELS), rel)

    def test_c_4_the_frozen_list_names_the_previous_stages_and_the_engine(self):
        for rel in ("core", "adapters", "measure/lib", "measure/inject.py", TS_REL, TSS_REL, S2_REL, STAGE_REL, TSS_SEAL_REL, S2_SEAL_REL, POPULATION_REL, STATES_REL, INTERIM_REL):
            self.assertIn(rel, NOT_TOUCHED_RELS)
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)


class OrderTest(unittest.TestCase):
    def test_i_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def _good(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        for o in ("measure/s.py", "tests/g.py"):
            r.put(o)
        r.commit("measure/s.py", "tests/g.py")
        return r, s

    def test_i_2_good_order_is_green_and_bad_orders_are_red(self):
        r, s = self._good()
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], ["measure/s.py", "tests/g.py"]))
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", [], ["measure/s.py"]))
        r.put("tests/new.py")                                                          # 未 commit
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], ["measure/s.py", "tests/new.py"]))
        r2 = PR.Repo()
        r2.put("measure/s.py")
        r2.commit("measure/s.py")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], [], ["measure/s.py"]))     # script が封より前

    def test_i_3_the_order_check_lists_the_script_and_this_gate(self):
        self.assertEqual([SCRIPT_REL, GATE_REL], list(SCRIPT_RELS) + [GATE_REL])
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in SCRIPT_RELS + (GATE_REL,)))


class DeviceTest(unittest.TestCase):
    def test_l_1_the_profile_pair_reaches_the_names_the_device_reads_and_comes_back(self):
        self.assertEqual([], device_problems())

    def test_l_2_the_real_names_are_back_after_every_check(self):
        self.assertEqual((("P30E", "P32E"), "P30E", "P32E"), ts_state())
        self.assertEqual((False, False), (bool(getattr(TS.N, TS.TY.FLAG)), bool(getattr(TS.S, TS.TY.FLAG2))))

    def test_l_3_the_device_changes_only_inside_the_with_by_a_direct_look(self):
        before = ts_state()
        with MS.profile_pair():
            self.assertEqual((("P33E", "P33E"), "P33E", "P33E"), ts_state())
        self.assertEqual(before, ts_state())
        with self.assertRaises(RuntimeError):
            with MS.profile_pair():
                raise RuntimeError("x")
        self.assertEqual(before, ts_state())


class RefsTest(unittest.TestCase):
    def test_d_1_the_refs_follow_the_seal(self):
        self.assertEqual([], refs_problems())

    def test_d_2_the_seal_names_the_same_rules(self):
        seal = read(SEAL_REL)
        for ph in (u"同じ `key` は最初の 1 件だけ採る", u"`float` にできない fact が出たら止めずに飛ばし", u"`el` = `name` の最後の `:` の後ろ", u"`key` = `el + \"@\" + context`"):
            self.assertIn(ph, seal)


class BookTest(unittest.TestCase):
    def test_e_1_one_book_follows_the_seal(self):
        self.assertEqual([], book_problems())
        self.assertEqual([], small_problems())

    def test_e_2_the_bases_are_read_from_the_records(self):
        self.assertEqual([], bases_problems())


class RecordTest(unittest.TestCase):
    def test_f_1_the_record_is_whole_and_reproducible(self):
        self.assertEqual([], run_problems())
        self.assertEqual([], clean_problems())

    def test_f_2_the_record_writer_calls_check_clean_before_writing(self):
        self.assertEqual([], clean_wiring_problems())

    def test_f_3_preview_writes_nothing(self):
        self.assertEqual([], preview_problems())

    def test_f_4_the_summary_and_coverage_count_from_rows(self):
        self.assertEqual([], summary_problems())
        self.assertEqual([], coverage_problems())

    def test_f_5_the_sheet_is_written_outside_the_repo_only_and_the_labels_follow_the_rules(self):
        self.assertEqual([], sheet_types_problems())


class MutantTest(unittest.TestCase):
    def test_k_1_every_check_is_green_on_the_real_code_and_red_on_each_mutant(self):
        checks = sorted(set(m[5] for m in MUTANTS), key=lambda f: f.__name__)
        for chk in checks:
            self.assertEqual([], chk(), chk.__name__)
        silent = []
        sha_before = ST.sha256_file(os.path.join(ROOT, SCRIPT_REL))
        for (label, mod, fn, old, new, chk) in MUTANTS:
            orig = getattr(mod, fn)
            saved = ts_state()
            saved_br = TS.build_row
            try:
                with mutated(mod, fn, old, new), warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    got = guard(chk)
            finally:
                ts_restore(saved)                                # 「戻さない」変異が残した差し替えは、変異と一緒に戻す
                TS.build_row = saved_br
            self.assertIs(getattr(mod, fn), orig)
            self.assertEqual(saved, ts_state())
            if not got:
                silent.append(label)
        self.assertEqual([], silent)
        self.assertEqual(sha_before, ST.sha256_file(os.path.join(ROOT, SCRIPT_REL)))                    # 変異は memory の中だけ。script の file は byte で同じ

    def test_k_2_a_mutant_is_always_put_back(self):
        orig, dev = MS.refs_from_facts, MS.device
        with self.assertRaises(RuntimeError):
            with mutated(MS, "refs_from_facts", u"        if key in seen:", u"        if False:"):
                self.assertIsNot(MS.refs_from_facts, orig)
                raise RuntimeError("x")
        self.assertIs(MS.refs_from_facts, orig)
        with self.assertRaises(AssertionError):
            with mutated(MS, "refs_from_facts", u"this text is not in the function", u"x"):
                pass
        self.assertIs(MS.refs_from_facts, orig)
        with mutated(MS, "device", u"    bad = TS.wiring_problems()", u"    bad = TS.wiring_problems()"):
            with MS.device():                                      # contextmanager の関数も変異した版で with として使える
                pass
        self.assertIs(MS.device, dev)

    def test_k_3_the_mutant_table_covers_each_effect_named_in_the_brief(self):
        labels = u" ".join(m[0] for m in MUTANTS) + u" ".join(m[0] for m in CONST_MUTANTS)
        for key in (u"対を戻さない", u"丙に期の名前の読み替えを掛けない", u"種を変える", u"cap を変える", u"切り替え yen_scan を真にしない", u"切り替え T5 を真にしない", u"同じ key の 2 件目を採る",
                    u"行に値の欄を足す", u"行に文の字を入れる", u"通した率の分母が対応が付いた行", u"届いた率の分母が注入の行", u"本番の記録を使い捨ての材料で作る", u"紙: repo の中でも書く"):
            self.assertIn(key, labels)

    def test_k_4_every_mutant_check_is_one_of_the_named_behaviour_checks(self):
        names = set(m[5].__name__ for m in MUTANTS)
        self.assertEqual(set(["device_problems", "refs_problems", "book_problems", "summary_problems", "coverage_problems", "run_problems", "clean_wiring_problems", "clean_problems",
                              "bases_problems", "preview_problems", "sheet_types_problems", "small_problems", "compare_problems"]), names)


class WiringTest(unittest.TestCase):
    def test_m_1_the_script_calls_the_previous_stage_functions_and_defines_none_of_the_same_name(self):
        self.assertEqual([], _reuse_problems())

    def test_m_2_a_same_name_definition_or_a_missing_call_turns_it_red(self):
        with tmpdir() as d:
            src = read(SCRIPT_REL)
            p = os.path.join(d, "s.py")
            for name in NOT_REDEFINED:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(src + u"\n\ndef %s(*a):\n    return None\n" % name)
                self.assertNotEqual([], _reuse_problems(src_path=p), name)
            for alias, fn in REUSED_FUNCS:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(src.replace(u"%s.%s" % (alias, fn), u"%s.%sx" % (alias, fn)))
                self.assertNotEqual([], _reuse_problems(src_path=p), (alias, fn))
        ms2 = _ns()
        ms2.S2 = types.SimpleNamespace()
        self.assertNotEqual([], _reuse_problems(ms=ms2))

    def test_m_3_the_script_imports_no_network_module(self):
        self.assertEqual([], network_problems())
        with tmpdir() as d:
            for line in (u"import urllib.request", u"from urllib import request", u"import socket", u"import http.client", u"import ssl", u"import requests"):
                p = os.path.join(d, "s.py")
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(u"import os\n" + line + u"\n")
                self.assertNotEqual([], network_problems(p), line)

    def test_m_4_names_that_existed_before_loading_are_put_back(self):
        marker = types.ModuleType("pswap_for_idmap")
        before = sys.modules.get("pswap_for_idmap")
        sys.modules["pswap_for_idmap"] = marker
        names = ("tanshin_self2_for_tanshin_self_inject", "tanshin_self_for_tanshin_self2", "tanshin_self_stage_for_tanshin_self", "tanshin_for_tanshin_self")
        before3 = dict((n, sys.modules.get(n)) for n in names)
        try:
            mod = load_module(SCRIPT_REL, "tanshin_self_inject_script_reload_probe")
            self.assertIs(marker, sys.modules["pswap_for_idmap"])                      # 先に居た名前は元の object
            self.assertIs(mod, sys.modules["tanshin_self_inject_script_reload_probe"])  # 自分の名前は残る
            for n in names:                                                            # 読み込んだ先の便が決まった名前で入れ直したものも戻る(先に居なかった名前は増えてよい)
                if before3[n] is not None:
                    self.assertIs(before3[n], sys.modules[n])
        finally:
            if before is None:
                sys.modules.pop("pswap_for_idmap", None)
            else:
                sys.modules["pswap_for_idmap"] = before
            sys.modules.pop("tanshin_self_inject_script_reload_probe", None)

    def test_m_5_no_reserved_names_no_docid_no_tdnet_no_known_code_in_the_new_files(self):
        self.assertEqual([], reserved_problems())
        self.assertEqual([], name_problems())

    def test_m_6_the_new_files_carry_no_secret_material_markers_and_no_skip_folder_name(self):
        handoff = u"sgogi-coach" + u"-handoff"                                        # 開かない folder(この file が自分の字に当たらないよう、つないで書く)
        skipped = ST.SKIP_CACHES[0]
        for rel in SCRIPT_RELS + (GATE_REL,):
            self.assertNotIn(handoff, read(rel), rel)
            self.assertNotIn(skipped, read(rel), rel)

    def test_m_7_the_script_shares_the_previous_stage_instances(self):
        self.assertIs(MS.ST, MS.TSS.ST)
        self.assertIs(MS.TS, MS.TSS.TS)
        self.assertIs(MS.TSS, MS.S2.TSS)
        self.assertIs(MS.Stop, MS.ST.Stop)

    def test_m_8_the_script_never_writes_a_production_record_by_default(self):
        for name in ("run_inject", "run_sheet", "run_types"):
            sig = inspect.signature(getattr(MS, name))
            self.assertNotIn(os.path.join(ROOT, INJECT_REL), [str(p.default) for p in sig.parameters.values()])
        before = prod_state()
        with tmpdir() as d:                                                                  # 書く入口を使い捨ての場所で走らせても本番の記録は変わらない
            pop, mat, bases, zips = fixture4(d)
            MS.run_inject(out=os.path.join(d, "o", "x.json"), **kw4(pop, mat, bases))
        self.assertEqual(before, prod_state())

    def test_m_9_the_script_does_not_touch_modules_names_outside_the_with(self):
        u"""device() の外で TS.INJECT_PROFILES・OLD・NEW を代入する文が profile_pair の外に無い(ast で見る)。"""
        with open(os.path.join(ROOT, SCRIPT_REL), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        offenders = []
        for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
            if fn.name == "profile_pair":
                continue
            for node in ast.walk(fn):
                targets = node.targets if isinstance(node, ast.Assign) else ([node.target] if isinstance(node, ast.AugAssign) else [])
                for t in targets:
                    for x in ast.walk(t):
                        if isinstance(x, ast.Attribute) and x.attr in ("INJECT_PROFILES", "OLD", "NEW") and isinstance(x.value, ast.Name) and x.value.id == "TS":
                            offenders.append((fn.name, x.attr))
        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
