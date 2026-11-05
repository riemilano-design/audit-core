# -*- coding: utf-8 -*-
u"""封 docs/XBRL_INJECT_SCAN_FIX_SEAL_2026-11-05.md §5(追記 1 まで)― H(注入の仕掛けの数の読みに「万円」と「億+万の複合」を足す)の測定と、結果の表(tally)。**0 USD・通信なし・鍵は読まない・LLM は呼ばない。**

    python3 measure/xbrl_nscan_2026-11-05.py offcheck [--procs N] [--only <docID>] [--out PATH]   # 切り替え 偽 の不変(H-1)と K-4 の試験 → fixtures/xbrl/nscan/offcheck_2026-11-05.json
    python3 measure/xbrl_nscan_2026-11-05.py inject   [--procs N] [--only <docID>] [--out PATH]   # 切り替え 真 で新しい token の site だけに注入(P29E・P30E の T1_VALUE・T8_REL)→ fixtures/xbrl/nscan/inject_2026-11-05.json
    python3 measure/xbrl_nscan_2026-11-05.py tally    [--root DIR]                                 # 記録 2 つから H-1〜H-10 と K-1〜K-4 の表を出す(file は書かない)

RB の便の script ``xbrl_rmix_2026-11-04.py``(RM)は **1 byte も変えず**、importlib で読み込んで使う(RM が N の便の script ``xbrl_numfix_2026-11-04.py`` を読み込む作りと同じ)。
``lib.numbers``(N)は RM を読み込む**前に**この script が import する。RM・RUN・IJ・TUNE・``lib.sites``(S)が引く N が同じ module instance であることを ``N.__file__``(の realpath)と ``id()`` で
確かめ、``wiring_problems`` に書く(使う側の実体に届かないと切り替えが黙って効かない)。

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めは結果の報告に書いた):
- 切り替えの名前は封の追記 1 の 1 のとおり ``yen_scan_2026_11_05``。真にするのは ``inject`` の with の中だけで、出るときは必ず元の値(偽)に戻す(同じ process の他の試験を汚さない)。
  ``offcheck`` は偽のまま走らせる(真だと止める)。
- ``offcheck``: 200 本の ``N.scan`` の token の全欄(start・end・text・value・unit・unit_end・sentence_index・has_comma・has_frac・groups)と、``is_quantity``・``render_value``(4 つの値)・``_unit_after``・
  ``unit_family`` の出力の sha256 を本ごとに持つ。比べ先は 2 つ: 封の commit の ``measure/lib/numbers.py``(``git show`` で読んだ blob を module にして同じ文に当てる)と、RB の便の記録
  ``fixtures/xbrl/rmix/inject_2026-11-04.json`` の注入の行(id・型・基準の claim・P29E の土台に対応)と本ごとの数え(``inject_text_rb`` を偽で走らせる。注入した文の判定は
  土台の判定の写しで代用 = **選びと土台の結びだけ**を比べる。判定の列は比べない)。1 本でも違えば H-1 は外れ。
- K-4 の試験(``offcheck`` に入れた): ``measure/tests/test_inject.py``(既存。偽のまま全部緑)と ``measure/tests/test_yen_scan.py``(足した試験。封の追記 1 の 2)を unittest で 1 回ずつ走らせ、
  さらに封 §4 の K-4 が名指す変異 5 つ(名前は封の字から読む)を ``lib`` の属性の差し替えで 1 つずつ入れて ``test_yen_scan.py`` を走らせ、赤(失敗かエラーが 1 本以上)になることを記録する。
  変異は with の中だけで、出たら必ず戻す(戻ったことも記録する)。
- ``inject``: 土台 = 無改変の文で **P30E が GROUNDED** の claim、比較 = P29E(``RM.base_status_rb`` をそのまま使う)。site は**新しい token(``groups`` が None でない token)だけ**:
  T1 は ``S.t1_sites`` を新しい token に絞った版に with の中だけ差し替えて ``IJ.select(types=["T1_VALUE"])`` を呼ぶ。T8 は ``RUN.t8_candidates4`` の写し(token の並べ替え・r の選び・cap)を持ち、
  円族の filter を ``MONEY_FAMILY + ("万円",)`` と新しい token に絞る。cap は型ごと 1 本 10(``RUN.INJECT_CAP``)。
- 読み直し = 注入後の文を ``N.scan`` して、同じ start・同じ単位・意図した値の token が在ること(groups の有無は問わない = 「兆+億」の先頭の位が落ちて億だけになる形も、値と単位が合えば合い)。
  round-trip が合わない行は止めずに数える(H-10 が数える欄)。注入後の値を円に直して refs の値に在る行も数える(refs の守り ``build_t1`` は円に直さず比べる既存の欠陥なので、円に直して数え直す)。
- 既存の site の率は RB の記録をそのまま写す(作り直さない)。新しい site の率と並べるため inject の記録に持つ。
- 記録は文・span・value・会社名を持たない。docID は ``LATER_NAMING_FILES`` に宣言された記録だけ。

engine(``core/``・``adapters/``)・``measure/inject.py``・``measure/lib``・前の便の script と記録は 1 行も変えない。
"""
from __future__ import print_function

import argparse
import collections
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import random
import subprocess
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

# N は RM(→ N の便の script → 仕掛けの module 群)を読み込む前に import する。後で RM の側の N と同じ instance かを確かめる
from lib import numbers as N                         # noqa: E402
from lib import scales as SC                         # noqa: E402
from lib import sites as S                           # noqa: E402

N_ID_AT_IMPORT = id(N)


def load_module(name_file, mod_name):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name_file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RM = load_module("xbrl_rmix_2026-11-04.py", "rmix_for_nscan")
NF, RUN, GEN = RM.NF, RM.RUN, RM.GEN
TUNE, IJ = RM.TUNE, RM.IJ
Stop = GEN.Stop

from adapters.xbrl import verify_document as VD      # noqa: E402

FLAG = "yen_scan_2026_11_05"
SEAL_REL = "docs/XBRL_INJECT_SCAN_FIX_SEAL_2026-11-05.md"
SEAL_COMMIT = "89afc79"
DOC_REL = "docs/XBRL_INJECT_SCAN_FIX_RESULT_2026-11-05.md"
REC_DIR_REL = "fixtures/xbrl/nscan"
OFFCHECK_REL = REC_DIR_REL + "/offcheck_2026-11-05.json"
INJECT_REL = REC_DIR_REL + "/inject_2026-11-05.json"
REC_REL = collections.OrderedDict([("offcheck", OFFCHECK_REL), ("inject", INJECT_REL)])
LIB_RELS = ("measure/lib/numbers.py", "measure/lib/scales.py")
TEST_INJECT_REL = "measure/tests/test_inject.py"
TEST_YEN_REL = "measure/tests/test_yen_scan.py"
RB_INJECT_REL = RM.INJECT_REL                      # fixtures/xbrl/rmix/inject_2026-11-04.json(読むだけ)
RM_SCRIPT_REL = "measure/xbrl_rmix_2026-11-04.py"
SOURCES = RM.SOURCES
INJECT_PROFILES = RM.INJECT_PROFILES               # ("P29E", "P30E")
INJECT_TYPES = tuple(RUN.INJECT_TYPES)             # ("T1_VALUE", "T8_REL")
LINK_KEY = RM.LINK_KEY
COMPARE_KEY = RM.COMPARE_KEY
LINKED, UNLINKED = RM.LINKED, RM.UNLINKED
HIT, MISS = RM.HIT, RM.MISS
BASE_WORD = RM.BASE_WORD
NEW_WORD = u"新しい token(複合の数・万円)の site だけ"
EXISTING_KEY = u"既存の site の率(RB の記録 fixtures/xbrl/rmix/inject_2026-11-04.json の 集計 全体。そのまま写した)"
EXISTING_CMP_KEY = u"既存の site の率・比較用(RB の記録の 集計(比較用)全体。そのまま写した)"
BREAKDOWN_KEY = u"新しい site の内訳(P30E)"
H_KEY = u"H の欄"
SHAPE_NAMES = (u"億+万", u"万", u"兆+億")
STATUS_NO_BASE = u"基準に対応が付かない"
STATUS_NOT_G = u"P30E が GROUNDED でない"
NO_PICK = u"r が決まらず site にしない"
#: 封 §6 の字に足す、この script の限界(数は変えない)
EXTRA_LIMITS = (u"round-trip 不一致は止めずに数える(K-2 の欄)。封 §6 の 3 の「止める」より実装は厳しくなく、判定は K-2 に出る",
                u"K-4 の赤は失敗とエラーを分けない(記録の 赤 は失敗 + エラーの和)")


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def jround(x):
    return json.loads(json.dumps(x))


def sha_json(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=False).encode("utf-8")).hexdigest()


def sha256_rel(rel, root=ROOT):
    return GEN.sha256_file(os.path.join(root, rel))


# ======================================================================================================
# 配線(N が使う側の実体に届いているか)と鍵の検査
def key_leaks_h(text, key_value=None, long_alnum=True):
    u"""封の path は英数字・_・- が 32 字を超えて続く(``key_leaks`` の「32 字以上の英数字の連なり」に当たる)。この script の封と RM の封の path そのものの字だけを検査の前に除く。"""
    return NF.ORIG_KEY_LEAKS(text.replace(SEAL_REL, u"").replace(RM.SEAL_REL, u""), key_value, long_alnum)


GEN.key_leaks = key_leaks_h


def wiring_problems():
    u"""問題の列。N(仕掛けの数の読み)が RM・RUN・IJ・TUNE・S の使う N と同じ instance か・RM の差し替えが届いているか・鍵の検査が差し替わっているか。"""
    out = []
    want = os.path.realpath(os.path.join(ROOT, "measure", "lib", "numbers.py"))
    if os.path.realpath(N.__file__) != want:
        out.append(u"N.__file__ がこの木の measure/lib/numbers.py でない")
    if id(N) != N_ID_AT_IMPORT:
        out.append(u"N の id が import 時と違う(module が差し替わった)")
    for label, mod in (("RUN.N", RUN.N), ("IJ.N", IJ.N), ("TUNE.N", TUNE.N), ("S.N", S.N)):
        if mod is not N:
            out.append(u"%s がこの script の N と同じ instance でない" % label)
    for label, mod in (("TUNE.SC", TUNE.SC), ("S.SC", S.SC)):
        if mod is not SC:
            out.append(u"%s がこの script の scales と同じ instance でない" % label)
    if IJ.S is not S:
        out.append(u"IJ.S がこの script の sites と同じ instance でない")
    if not hasattr(N, FLAG):
        out.append(u"N に切り替え %s が無い" % FLAG)
    if GEN.key_leaks is not key_leaks_h or RUN.GEN is not GEN or RUN.GEN.key_leaks is not key_leaks_h:
        out.append(u"鍵の検査 key_leaks が差し替わっていない(封の path の字を除く版でない)")
    if RM.GEN is not GEN or NF.GEN is not GEN:
        out.append(u"RM・NF の GEN が同じ instance でない")
    return out


def inject_wiring_problems():
    u"""``inject``・``offcheck`` の前に: RM の注入の差し替え(``RUN.PROFILES``・``base_status4``)が届いているか。"""
    out = wiring_problems()
    if tuple(RUN.PROFILES) != INJECT_PROFILES:
        out.append(u"RUN.PROFILES が (P29E, P30E) でない")
    if RUN.base_status4 is not RM.base_status_rb:
        out.append(u"RUN.base_status4 が RM.base_status_rb でない")
    if RUN.t8_candidates4.__globals__["base_status4"] is not RM.base_status_rb:
        out.append(u"使う側 RUN.t8_candidates4 が引く base_status4 が RM.base_status_rb でない")
    return out


@contextlib.contextmanager
def yen_scan_on():
    u"""切り替えを with の中だけ真にする。出るときは必ず元の値に戻す。"""
    old = getattr(N, FLAG)
    setattr(N, FLAG, True)
    try:
        yield
    finally:
        setattr(N, FLAG, old)


# ======================================================================================================
# 封の commit の lib(切り替え 偽 の比べ先)
_ORIG = {}


def orig_numbers():
    u"""封の commit の ``measure/lib/numbers.py`` の blob を module にして返す(``git show`` で読む。numbers.py は標準 library だけを import する)。"""
    if "mod" not in _ORIG:
        p = subprocess.run(["git", "show", "%s:./measure/lib/numbers.py" % SEAL_COMMIT], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode != 0:
            raise Stop(u"**封の commit の numbers.py を git から読めない。止める**")
        mod = types.ModuleType("orig_numbers_at_seal")
        mod.__file__ = "<%s:measure/lib/numbers.py>" % SEAL_COMMIT
        exec(compile(p.stdout.decode("utf-8"), mod.__file__, "exec"), mod.__dict__)
        _ORIG["mod"] = mod
        _ORIG["sha256"] = hashlib.sha256(p.stdout).hexdigest()
    return _ORIG["mod"]


def orig_sha256():
    orig_numbers()
    return _ORIG["sha256"]


def token_fields(t):
    return [t.start, t.end, t.text, t.value, t.unit, t.unit_end, t.sentence_index, t.has_comma, t.has_frac, getattr(t, "groups", None)]


def functions_view(mod, text, tokens):
    u"""token ごとの ``is_quantity``・``render_value``(like の値 +0・+7・×1.1 を丸めたもの・×3)・``_unit_after``・``unit_family``。"""
    out = []
    for t in tokens:
        vals = (t.value, t.value + 7, round(t.value * 1.1, 1 if t.has_frac else 0), t.value * 3)
        out.append([mod.is_quantity(text, t), [mod.render_value(v, t) for v in vals], list(mod._unit_after(text, t.end)), mod.unit_family(t.unit)])
    return out


def tokens_sha(tokens):
    return sha_json([token_fields(t) for t in tokens])


# ======================================================================================================
# 新しい token の数え(封の commit の lib と、真の lib の scan を比べる)
def shape_of(t):
    return u"+".join(ch for ch, _c in t.groups) if t.groups else None


def token_stats(text):
    u"""本ごとの token の数え(判定なし)。比べ元 = 封の commit の lib の scan、比べ先 = いまの N(真のとき)の scan。"""
    O = orig_numbers()
    before = O.scan(text)
    after = N.scan(text)
    new = [t for t in after if t.groups is not None]
    shapes = collections.Counter(shape_of(t) for t in new)
    qs = [t for t in new if N.is_quantity(text, t)]
    same_span = set((t.start, t.end) for t in new)
    cover = [(t.start, t.unit_end) for t in new]
    replaced = dropped = dropped_q = dropped_unit = 0
    for e in before:
        if not any(a <= e.start < b for a, b in cover):
            continue
        if (e.start, e.end) in same_span:
            replaced += 1
        else:
            dropped += 1
            dropped_q += 1 if O.is_quantity(text, e) else 0
            dropped_unit += 1 if e.unit is not None else 0
    old_by = dict(((t.start, t.end), t) for t in before)
    unit_changed = unit_changed_q = 0
    for t in after:
        if t.groups is not None:
            continue
        o = old_by.get((t.start, t.end))
        if o is not None and o.unit != t.unit:
            unit_changed += 1
            unit_changed_q += 1 if N.is_quantity(text, t) else 0
    fam0 = tuple(TUNE.MONEY_FAMILY)
    fam1 = fam0 + (u"万円",)
    other = sum(v for k, v in shapes.items() if k not in SHAPE_NAMES)
    return collections.OrderedDict([
        (u"新しい token", collections.OrderedDict([(u"億+万", shapes.get(u"億+万", 0)), (u"万", shapes.get(u"万", 0)), (u"兆+億", shapes.get(u"兆+億", 0)), (u"その他", other),
                                                  (u"計", len(new)), (u"is_quantity 真", len(qs))])),
        (u"覆われた既存の token", collections.OrderedDict([(u"同じ span の置き換え", replaced), (u"捨てた", dropped), (u"うち is_quantity 真", dropped_q), (u"うち単位が付いていた", dropped_unit)])),
        (u"既存の token の単位だけ 万円 に変わったもの", collections.OrderedDict([(u"件", unit_changed), (u"うち is_quantity 真", unit_changed_q)])),
        (u"円族の token(is_quantity 真)", collections.OrderedDict([
            (u"偽", sum(1 for t in before if t.unit in fam0 and O.is_quantity(text, t))), (u"真", sum(1 for t in after if t.unit in fam1 and N.is_quantity(text, t)))]))])


# ======================================================================================================
# 材料と記録の書き方
def caches_all():
    return RM.caches_all()


def load_books(root=ROOT, only=None):
    return NF.load_books(root, only)


def header_h(root, step, seed_meta, before, after, profiles):
    h = RUN.header(root, step, os.path.join(root, SOURCES["aiforms"]["gen"]), seed_meta, before, after)
    h[u"seal"] = SEAL_REL
    h[u"封の commit"] = SEAL_COMMIT
    h[u"この script の sha256"] = GEN.sha256_file(os.path.abspath(__file__))
    h[u"rmix script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_rmix_2026-11-04.py"))
    h[u"numfix script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_numfix_2026-11-04.py"))
    h[u"前の便の run script の sha256"] = GEN.sha256_file(os.path.join(HERE, "xbrl_aiforms_run_2026-11-03.py"))
    h[u"生成の記録の sha256"] = collections.OrderedDict((src, GEN.sha256_file(os.path.join(root, p["gen"]))) for src, p in SOURCES.items())
    h[u"RB の記録の sha256"] = GEN.sha256_file(os.path.join(root, RB_INJECT_REL))
    h[u"lib の指紋"] = collections.OrderedDict((rel, GEN.sha256_file(os.path.join(root, rel))) for rel in LIB_RELS)
    h[u"封の commit の numbers.py の sha256"] = orig_sha256()
    h[u"profile"] = list(profiles)
    return h


def write_json(out, rec, key_value=None, text=None):
    text = text if text is not None else json.dumps(rec, ensure_ascii=False, indent=1) + u"\n"
    RUN.write_record(out, text, rec, key_value)


def scope_word(only):
    return u"全 200 本" if only is None else u"**--only(本番の記録ではない)**"


def load_rb(root=ROOT):
    return GEN.jload(os.path.join(root, RB_INJECT_REL))


def seal_text(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def seal_limits(seal):
    u"""封 §6 の番号つきの文(記録の 限界 に写す。封の字をその場で読む)。"""
    sec = seal[seal.index("## §6"):seal.index("## §7")]
    return [m.group(1).strip() for m in (re.match(r"^\d+\. (.*)$", ln) for ln in sec.splitlines()) if m]


def seal_mutation_names(seal):
    u"""封 §4 の K-4 が名指す変異の名前(括弧の中を ・ で分けたもの)。"""
    sec4 = seal[seal.index("## §4"):seal.index("## §5")]
    m = re.search(r"^- K-4:.*?変異\(([^)]*)\)で赤", sec4, re.M)
    if not m:
        raise Stop(u"**封 §4 の K-4 から変異の名前を読めない。止める**")
    return [x.strip() for x in m.group(1).split(u"・")]


# ======================================================================================================
# offcheck(切り替え 偽 の不変)
def offcheck_job(args):
    src, name, item, row, text_dir, zip_caches, seed, work_root, expect = args
    if getattr(N, FLAG):
        raise Stop(u"**切り替えが真のまま offcheck を走らせた。止める**")
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    O = orig_numbers()
    toks, otoks = N.scan(text), O.scan(text)
    th, oth = tokens_sha(toks), tokens_sha(otoks)
    fh, ofh = sha_json(functions_view(N, text, toks)), sha_json(functions_view(O, text, otoks))
    refs = RUN.refs_for(row, zip_caches, work_root)
    cache = {}

    def verify(zb_, p, t):                                   # 注入した文の判定は土台の判定の写し(選びと土台の結びだけを比べる)
        if p not in cache:
            cache[p] = VD.verify_document(zb_, p, text)
        return cache[p]
    rows, counts = RM.inject_text_rb(zb, text, refs, seed, name, verify=verify)
    mine = [[r["id"], r[u"型"], r[u"基準の claim"], r[LINK_KEY]] for r in rows]
    rows_ok = mine == expect["rows"]
    counts_ok = jround(counts) == expect["counts"]
    same_lib = th == oth and fh == ofh
    return collections.OrderedDict([
        (u"name", name), (u"docID", item[u"docID"]), (u"form", item[u"form"]), (u"model", item[u"model"]), (u"writer", item[u"writer"]), (u"材料", src),
        (u"token の数", len(toks)), (u"groups を持つ token", sum(1 for t in toks if t.groups is not None)),
        (u"token の sha256", th), (u"封の commit の lib の token の sha256", oth),
        (u"関数の出力の sha256", fh), (u"封の commit の lib の関数の出力の sha256", ofh), (u"lib が封の commit と一致", same_lib),
        (u"行の数", len(mine)), (u"RB の記録の行の数", len(expect["rows"])),
        (u"RB の記録の行と一致", rows_ok), (u"RB の記録の数えと一致", counts_ok),
        (u"一致", bool(same_lib and rows_ok and counts_ok and all(t.groups is None for t in toks)))])


def offcheck_aggregate(books):
    return collections.OrderedDict([
        (u"本", len(books)), (u"H-1 一致した本", sum(1 for b in books if b[u"一致"])),
        (u"封の commit の lib と一致した本", sum(1 for b in books if b[u"lib が封の commit と一致"])),
        (u"RB の記録の行と一致した本", sum(1 for b in books if b[u"RB の記録の行と一致"])),
        (u"RB の記録の数えと一致した本", sum(1 for b in books if b[u"RB の記録の数えと一致"])),
        (u"token の数", sum(b[u"token の数"] for b in books)), (u"groups を持つ token", sum(b[u"groups を持つ token"] for b in books)),
        (u"行の数", collections.OrderedDict([(u"今回", sum(b[u"行の数"] for b in books)), (u"RB の記録", sum(b[u"RB の記録の行の数"] for b in books))]))])


# ---- K-4 の試験
def run_unittests(rel, mod_name, root=ROOT):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(root, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
    stream = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()):                 # test_inject の試験が標準出力に書く行を捨てる
        res = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    return collections.OrderedDict([(u"path", rel), (u"sha256", sha256_rel(rel, root)), (u"試験", res.testsRun), (u"失敗", len(res.failures)), (u"エラー", len(res.errors)), (u"skip", len(res.skipped))])


def _render_groups_keep_leading_zero(value, like):
    u"""変異用: ``N.render_groups`` から『先頭の 0 の group を落とす』処理だけを除いた写し。"""
    smallest = min(N._YEN_SCAN_EXP[ch] for ch, _c in like.groups)
    rem = int(round(value))
    parts = []
    for i, (ch, comma) in enumerate(like.groups):
        if i == len(like.groups) - 1:
            q = rem
        else:
            q, rem = divmod(rem, 10 ** (N._YEN_SCAN_EXP[ch] - smallest))
        parts.append((ch, q, comma))
    out = ""
    for j, (ch, q, comma) in enumerate(parts):
        out += N._yen_scan_group(q, comma) + (ch if j < len(parts) - 1 else "")
    return out


@contextlib.contextmanager
def _patched(obj, names_values):
    saved = [(n, getattr(obj, n)) for n, _v in names_values]
    try:
        for n, v in names_values:
            setattr(obj, n, v)
        yield
    finally:
        for n, v in saved:
            setattr(obj, n, v)


@contextlib.contextmanager
def mutation_switch_off():
    u"""切り替えを外す: 真でも偽のときと同じ出力にする(封の commit の lib の関数に差し替える)。"""
    O = orig_numbers()
    names = ("scan", "_unit_after", "unit_family", "render_value", "is_quantity")
    with _patched(N, [(n, getattr(O, n)) for n in names]):
        yield


@contextlib.contextmanager
def mutation_man_scale():
    old = SC.MONEY_SCALE["万円"]
    SC.MONEY_SCALE["万円"] = 1000
    try:
        yield
    finally:
        SC.MONEY_SCALE["万円"] = old


@contextlib.contextmanager
def mutation_comma():
    with _patched(N, [("_yen_scan_group", lambda q, comma: "%d" % q)]):
        yield


@contextlib.contextmanager
def mutation_leading_zero():
    with _patched(N, [("render_groups", _render_groups_keep_leading_zero)]):
        yield


@contextlib.contextmanager
def mutation_exponent():
    old = N._YEN_SCAN_EXP["万"]
    N._YEN_SCAN_EXP["万"] = 3
    try:
        yield
    finally:
        N._YEN_SCAN_EXP["万"] = old


#: 封 §4 の K-4 が名指す変異の名前 → 入れ方(名前は封の字と一字一句同じ)
MUTATIONS = collections.OrderedDict([
    (u"切り替えを外す", mutation_switch_off), (u"万円 の行を 1e3 に壊す", mutation_man_scale), (u"描きのコンマ", mutation_comma),
    (u"先頭の 0", mutation_leading_zero), (u"複合の value の指数", mutation_exponent)])


def lib_state():
    u"""変異が戻ったことを見るための、lib の差し替え対象の属性の同一性と値。"""
    names = ("scan", "_unit_after", "unit_family", "render_value", "is_quantity", "render_groups", "_yen_scan_group", "_yen_scan_merge")
    return (tuple(id(getattr(N, n)) for n in names), SC.MONEY_SCALE["万円"], dict(N._YEN_SCAN_EXP), getattr(N, FLAG))


def k4_tests(root=ROOT, names=None):
    u"""K-4 の記録: 既存の試験(偽のまま)・足した試験・変異ごとの赤の本数・戻したか。"""
    names = list(names) if names is not None else seal_mutation_names(seal_text(root))
    if getattr(N, FLAG):
        raise Stop(u"**切り替えが真のまま K-4 の試験を走らせた。止める**")
    before = lib_state()
    rec = collections.OrderedDict()
    rec[u"既存の試験(偽のまま)"] = run_unittests(TEST_INJECT_REL, "test_inject_for_nscan", root)
    rec[u"足した試験"] = run_unittests(TEST_YEN_REL, "test_yen_scan_for_nscan", root)
    muts = []
    for n in names:
        if n not in MUTATIONS:
            raise Stop(u"**封の K-4 の変異の名前を script が知らない: %s。止める**" % n)
        with MUTATIONS[n]():
            r = run_unittests(TEST_YEN_REL, "test_yen_scan_mut_for_nscan", root)
        muts.append(collections.OrderedDict([(u"名前", n), (u"試験", r[u"試験"]), (u"赤", r[u"失敗"] + r[u"エラー"]), (u"戻した", lib_state() == before)]))
    rec[u"変異"] = muts
    rec[u"変異のあと lib が元に戻った"] = lib_state() == before
    return rec


def run_offcheck(root=ROOT, procs=1, only=None, out=None, key_value=None, say=print, work_root=None, run_tests=True):
    out = out or os.path.join(root, OFFCHECK_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    if getattr(N, FLAG):
        raise Stop(u"**切り替えが真のまま offcheck を走らせた。止める**")
    RM.install_inject()
    bad = inject_wiring_problems()
    if bad:
        raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    seed, seed_meta = GEN.seed_value(root)
    books = load_books(root, only)
    rb = load_rb(root)
    by_book = collections.defaultdict(list)
    for r in rb[u"行"]:
        by_book[(r["docID"], r["form"], r["model"])].append([r["id"], r[u"型"], r[u"基準の claim"], r[LINK_KEY]])
    caches = caches_all()
    before = GEN.caches_snapshot(caches)
    work_root = work_root or tempfile.mkdtemp(prefix="nscan_off_", dir=os.environ.get("TMPDIR"))
    jobs_ = []
    for (src, n, item, row, _prior) in books:
        expect = {"rows": by_book.get((item[u"docID"], item[u"form"], item[u"model"]), []), "counts": rb[u"本ごとの数え"][n]}
        jobs_.append((src, n, item, row, SOURCES[src]["cache"], GEN.EXISTING_CACHES, seed, work_root, expect))
    say(u"offcheck %d 本(切り替え 偽。封の commit の lib と RB の記録に照らす)― procs %d" % (len(jobs_), procs))
    recs = NF.map_pool(offcheck_job, jobs_, procs)
    tests = k4_tests(root) if run_tests else None
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = header_h(root, u"H(注入の仕掛けの数の読み)― 切り替え 偽 の不変(0 USD)", seed_meta, before, after, INJECT_PROFILES)
    rec[u"範囲"] = scope_word(only)
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", FLAG), (u"この記録を作ったときの値", bool(getattr(N, FLAG))), (u"配線の問題", [])])
    rec[u"欄"] = collections.OrderedDict([
        (u"一致", u"token の全欄 sha256 と関数の出力 sha256 が封の commit の numbers.py(git show の blob)と等しく、groups を持つ token が 0 で、inject_text_rb を偽で走らせた行(id・型・基準の claim・P29E の土台に対応)と本ごとの数えが RB の記録と等しい"),
        (u"注入した文の判定", u"土台の判定の写しで代用した(選びと土台の結びだけを比べる。判定の列は比べない)"),
        (u"試験", u"K-4: 既存の試験(偽のまま)・足した試験・封 §4 が名指す変異 5 つ(lib の属性の差し替え。with の中だけ)で足した試験が赤になるか")])
    rec[u"本"] = recs
    rec[u"集計"] = offcheck_aggregate(recs)
    if tests is not None:
        rec[u"試験"] = tests
    write_json(out, rec, key_value)
    say(u"-> %s(本 %d)" % (out, len(recs)))
    return rec


# ======================================================================================================
# inject(新しい token の site だけ)
def only_new_t1(orig):
    def fn(text, refs):
        return [s for s in orig(text, refs) if s["token"].groups is not None]
    return fn


@contextlib.contextmanager
def t1_sites_only_new():
    u"""``S.t1_sites`` を新しい token に絞った版に with の中だけ差し替える(出るときは必ず戻す)。"""
    orig = S.t1_sites
    S.t1_sites = only_new_t1(orig)
    try:
        yield orig
    finally:
        S.t1_sites = orig


def t8_candidates_new(text, refs, base_claims, base_by_id, seed, key, cap):
    u"""``RUN.t8_candidates4`` の写し(token の並べ替え・r の選び・cap)。円族の filter を ``MONEY_FAMILY + ("万円",)`` と新しい token(groups が None でない)に絞る。(採った inj の列, 数え)。"""
    counts = collections.Counter()
    vindex = S._value_index(refs)
    fam = tuple(TUNE.MONEY_FAMILY) + (u"万円",)
    toks = [t for t in N.scan(text) if t.groups is not None and t.unit in fam and N.is_quantity(text, t)]
    random.Random("%s|%s|T8_REL" % (seed, key)).shuffle(toks)
    counts[u"円族の新しい token"] = len(toks)
    valid = []
    for t in toks:
        status, bc = RM.base_status_rb(base_claims, base_by_id, t, text)
        counts[status] += 1
        if bc is None:
            continue
        pick = TUNE.pick_r(seed, key, bc["id"], t, vindex)
        if pick is None:
            counts[NO_PICK] += 1
            continue
        valid.append((t, bc, pick))
    counts[u"作れる site"] = len(valid)
    out = []
    for t, bc, (r, new, tries) in valid[:cap]:
        inj = {"type": "T8_REL", "id": "%s-T8-%02d" % (key, len(out) + 1), "new_value": new, "replacement": N.render_value(new, t),
               "span": [t.start, t.end], "detail": {"original_value": t.value, "relative": r, "tries": tries, "unit": t.unit}}
        out.append((inj, t, bc))
    counts[u"採った"] = len(out)
    return out, counts


def reread_ok(tampered, tok, new_value):
    u"""注入後の文を読み直す: 同じ start・同じ単位・意図した値の token が在る(groups の有無は問わない)。"""
    return any(t2.start == tok.start and t2.unit == tok.unit and abs(t2.value - new_value) < 1e-9 for t2 in N.scan(tampered))


def groups_in(replacement):
    return 1 + sum(replacement.count(ch) for ch in (u"兆", u"億", u"万"))


def inject_text_h(zb, text, refs, seed, key, cap=RUN.INJECT_CAP, verify=None):
    u"""``RM.inject_text_rb`` と同じ手順(1 回に 1 件・round-trip を確かめる)。site は新しい token だけ。round-trip が合わない行は止めずに行の欄に持つ。(行, 数え)。"""
    stats = token_stats(text)
    if N.normalize_digits(text) != text:
        return [], collections.OrderedDict([(u"token の数え", stats), (u"注入しない", u"文に全角の数字がある(select は半角の文を前提にする)")])
    verify = verify or VD.verify_document
    profiles = tuple(RUN.PROFILES)
    base_claims = dict((p, verify(zb, p, text)["claims"]) for p in profiles)
    base_by_id = dict((p, dict((c["id"], c) for c in base_claims[p])) for p in profiles)
    toks = dict(((t.start, t.end), t) for t in N.scan(text))
    refyen = set(round(r["value"], 6) for r in refs)
    counts = collections.OrderedDict([(u"token の数え", stats)])
    work = []
    with t1_sites_only_new() as orig_t1:
        chosen, cat, _a, _w = IJ.select(text, refs, "xbrl", seed, key, cap, types=["T1_VALUE"])
        all_t1 = only_new_t1(orig_t1)(text, refs)
    pop = collections.Counter()
    for s in all_t1:
        st, bc = RM.base_status_rb(base_claims, base_by_id, s["token"], text)
        pop[st] += 1
    c1 = collections.Counter()
    c1[u"作れる site"], c1[u"採った"] = cat["T1_VALUE"], len(chosen)
    for inj in chosen:
        tok = toks[tuple(inj["span"])]
        st, bc = RM.base_status_rb(base_claims, base_by_id, tok, text)
        c1[st] += 1
        work.append((inj, tok, bc))
    counts["T1_VALUE"] = collections.OrderedDict(sorted(c1.items()))
    counts[u"T1_VALUE の作れる site の状態"] = collections.OrderedDict(sorted(pop.items()))
    t8, c8 = t8_candidates_new(text, refs, base_claims, base_by_id, seed, key, cap)
    counts["T8_REL"] = collections.OrderedDict(sorted(c8.items()))
    work += t8
    rows = []
    for inj, tok, bc in work:
        tampered, placements = IJ.apply_edits(text, [inj])
        rt = IJ.revert(tampered, [inj], placements, text) == text
        if bc is None:
            continue
        row = collections.OrderedDict([("id", inj["id"]), (u"型", inj["type"]), (u"形", shape_of(tok)), (u"コンマ", bool(tok.has_comma)), (u"単位", tok.unit),
                                      (u"基準の claim", bc["id"]), (LINK_KEY, bc["ids"][profiles[0]] is not None),
                                      (u"round-trip", bool(rt)), (u"読み直し", bool(reread_ok(tampered, tok, inj["new_value"]))),
                                      (u"注入後の値(円)が refs に在る", round(TUNE.scaled(inj["new_value"], tok.unit), 6) in refyen),
                                      (u"先頭の位が減った", groups_in(inj["replacement"]) < len(tok.groups))])
        if inj["type"] == "T8_REL":
            row["r"], row[u"r を決めた回"] = inj["detail"]["relative"], inj["detail"]["tries"]
        for p in profiles:
            if bc["ids"][p] is None:
                row[p] = TUNE.classify(None, None)
                continue
            res = TUNE.claim_for_p27(verify(zb, p, tampered)["claims"], inj, tok.unit)
            row[p] = TUNE.classify(res, base_by_id[p][bc["ids"][p]])
        rows.append(row)
    return rows, counts


def inject_job_h(args):
    src, name, item, row, text_dir, zip_caches, seed, work_root = args
    if not getattr(N, FLAG):
        raise Stop(u"**切り替えが偽のまま inject を走らせた。止める**")
    zb = GEN.read_zip(row, zip_caches)
    text = RUN.read_text(name, item, text_dir)
    refs = RUN.refs_for(row, zip_caches, work_root)
    rows, counts = inject_text_h(zb, text, refs, seed, name)
    base = {u"docID": item[u"docID"], u"form": item[u"form"], u"model": item[u"model"], u"writer": item[u"writer"]}
    return name, [collections.OrderedDict(list(base.items()) + list(r.items())) for r in rows], counts


# ---- 集計(門が記録の rows と 本ごとの数え から作り直して照らす)
def inject_summaries(rows):
    return RM.inject_summaries(rows)


def unlinked_counts(rows):
    return RM.unlinked_counts(rows)


def breakdown(rows):
    u"""新しい site の P30E の率を 形別・コンマ別に。"""
    out = collections.OrderedDict()
    for t in INJECT_TYPES:
        sel = [r for r in rows if r[u"型"] == t]
        o = collections.OrderedDict()
        o[u"形別"] = collections.OrderedDict((k, RUN.inject_cell([r for r in sel if r[u"形"] == k], "P30E")) for k in sorted(set(r[u"形"] for r in sel)))
        o[u"コンマ別"] = collections.OrderedDict((k, RUN.inject_cell([r for r in sel if (u"コンマ有" if r[u"コンマ"] else u"コンマ無") == k], "P30E")) for k in (u"コンマ有", u"コンマ無"))
        out[t] = o
    return out


def sum_counts(per, path):
    u"""本ごとの数え ``per`` の ``path``(キーの列)の値の和。無い本は 0。"""
    total = 0
    for c in per.values():
        v = c
        for k in path:
            v = v.get(k, 0) if isinstance(v, dict) else 0
        total += v if isinstance(v, int) and not isinstance(v, bool) else 0
    return total


def h_columns(per, rows):
    u"""H-2〜H-10 の欄を ``本ごとの数え`` と ``行`` から数える(記録の ``H の欄`` と tally の判定が使う)。"""
    new = collections.OrderedDict((k, sum_counts(per, (u"token の数え", u"新しい token", k))) for k in (u"億+万", u"万", u"兆+億", u"その他", u"計", u"is_quantity 真"))
    fam = collections.OrderedDict((k, sum_counts(per, (u"token の数え", u"円族の token(is_quantity 真)", k))) for k in (u"偽", u"真"))
    t1r = [r for r in rows if r[u"型"] == "T1_VALUE"]
    t8r = [r for r in rows if r[u"型"] == "T8_REL"]
    t8_new = sum_counts(per, ("T8_REL", u"円族の新しい token"))
    t8_nobase = sum_counts(per, ("T8_REL", STATUS_NO_BASE))
    t8_lt = sum_counts(per, ("T8_REL", STATUS_NOT_G))
    linked = [r for r in rows if r[LINK_KEY]]
    differ = sum(1 for r in linked if r["P29E"][u"結果"] != r["P30E"][u"結果"])

    def rate(t, p, key):
        sel = [r for r in rows if r[u"型"] == t]
        return RUN.inject_cell(sel, p)[key][u"率"]
    return collections.OrderedDict([
        (u"H-2 新しい token", new), (u"H-3 円族の token(is_quantity 真)", fam),
        (u"H-4 T1_VALUE", collections.OrderedDict([(u"作れる site", sum_counts(per, ("T1_VALUE", u"作れる site"))), (u"採った", sum_counts(per, ("T1_VALUE", u"採った"))), (u"うち P30E が GROUNDED", len(t1r))])),
        (u"H-5 T8_REL", collections.OrderedDict([(u"作れる site", sum_counts(per, ("T8_REL", u"作れる site"))), (u"採った", sum_counts(per, ("T8_REL", u"採った"))),
                                                (u"P29E に対応が付く行", sum(1 for r in t8r if r[LINK_KEY]))])),
        (u"H-6 T8_REL 基準に対応が付かない", collections.OrderedDict([(u"件", t8_nobase), (u"円族の新しい token", t8_new), (u"率", pct(t8_nobase, t8_new)), (u"P30E が GROUNDED でない", t8_lt)])),
        (u"H-7 通した率(P30E)", collections.OrderedDict((t, rate(t, "P30E", TUNE.LABEL_PASS)) for t in INJECT_TYPES)),
        (u"H-8 名指して原本の率(P30E)", collections.OrderedDict((t, rate(t, "P30E", TUNE.LABEL_NAMED_ORIGINAL)) for t in INJECT_TYPES)),
        (u"H-9 P29E と P30E で判定が違う行(P29E に対応が付く行)", differ),
        (u"H-10", collections.OrderedDict([(u"round-trip 不一致", sum(1 for r in rows if not r[u"round-trip"])), (u"読み直し不一致", sum(1 for r in rows if not r[u"読み直し"])),
                                         (u"注入後の値(円)が refs に在る行", sum(1 for r in rows if r[u"注入後の値(円)が refs に在る"]))])),
        (u"先頭の位が減った行", sum(1 for r in rows if r[u"先頭の位が減った"]))])


def existing_rates(rb):
    u"""RB の記録の 集計(全体)と 比較用(全体)をそのまま写す。"""
    a = collections.OrderedDict((t, collections.OrderedDict((p, rb[u"集計"][t][p][u"全体"]) for p in INJECT_PROFILES)) for t in INJECT_TYPES)
    b = collections.OrderedDict((t, collections.OrderedDict((p, rb[COMPARE_KEY][t][p][u"全体"]) for p in INJECT_PROFILES)) for t in INJECT_TYPES)
    return a, b


def run_inject(root=ROOT, procs=1, only=None, out=None, key_value=None, say=print, work_root=None):
    out = out or os.path.join(root, INJECT_REL)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    RM.install_inject()
    bad = inject_wiring_problems()
    if bad:
        raise Stop(u"**差し替えが届いていない: %s。止める**" % u" / ".join(bad))
    seed, seed_meta = GEN.seed_value(root)
    books = load_books(root, only)
    rb = load_rb(root)
    caches = caches_all()
    before = GEN.caches_snapshot(caches)
    work_root = work_root or tempfile.mkdtemp(prefix="nscan_inject_", dir=os.environ.get("TMPDIR"))
    jobs_ = [(src, n, item, row, SOURCES[src]["cache"], GEN.EXISTING_CACHES, seed, work_root) for (src, n, item, row, _prior) in books]
    say(u"注入 %d 本 × 2 profile(P29E・P30E)。切り替え 真・新しい token の site だけ ― procs %d(1 件ごとに判定。時間がかかる)" % (len(jobs_), procs))
    with yen_scan_on():
        if not getattr(N, FLAG) or wiring_problems():
            raise Stop(u"**切り替えを真にできない・配線が崩れた。止める**")
        results = NF.map_pool(inject_job_h, jobs_, procs)
    if getattr(N, FLAG):
        raise Stop(u"**with を出ても切り替えが真のまま。止める**")
    rows, per = [], collections.OrderedDict()
    for n, r, c in results:
        rows += r
        per[n] = c
    after = GEN.caches_snapshot(caches)
    if before != after:
        raise Stop(u"**cache の件数か名前が変わった。記録を書かずに止める**")
    rec = header_h(root, u"H(注入の仕掛けの数の読み)― 切り替え 真・新しい token の site だけの注入(P29E・P30E の T1_VALUE・T8_REL。0 USD)", seed_meta, before, after, INJECT_PROFILES)
    rec[u"範囲"] = scope_word(only)
    rec[u"切り替え"] = collections.OrderedDict([(u"名前", FLAG), (u"inject の中の値", True), (u"出たあとの値", bool(getattr(N, FLAG))), (u"配線の問題", wiring_problems())])
    rec[u"種"] = {u"file": RUN.SEED_REL_STR, u"種の確認": seed_meta}
    rec[u"型"] = collections.OrderedDict([
        ("T1_VALUE", u"inject.select(types=[T1_VALUE]) のまま。S.t1_sites を新しい token(groups が None でない token)に絞った版に with の中だけ差し替えた。cap は採用に掛ける(基準で絞る前)"),
        ("T8_REL", u"円族(MONEY_FAMILY + 万円)の新しい token・r ∈ %s・%d 回まで。RUN.t8_candidates4 の写し。cap は site に掛ける" % (list(TUNE.T8_R_VALUES), TUNE.T8_TRIES)),
        (u"上限", u"型ごと・1 本あたり %d" % RUN.INJECT_CAP),
        (u"site", NEW_WORD),
        (u"土台", BASE_WORD),
        (u"土台の結び方", u"P30E の claim を find_base_claim で 1 件に決め、P29E の claim は (value, span, unit) が同じ 1 件があれば結ぶ。無ければその行の P29E の欄は対応なし(判定しない)"),
        (u"集計の2本", u"集計 = 新しい site の全部での P29E・P30E の率(H-7・H-8 は P30E のこちら)。" + COMPARE_KEY + u" = そのうち P29E の claim にも対応が付く site だけでの P29E と P30E の率"),
        (u"inject.select の docID の引数", u"本の名前(<docID>_<形>_<model>)")])
    rec[u"本ごとの数え"] = per
    rec[u"注入の行の数"] = len(rows)
    rec[u"集計"], rec[COMPARE_KEY] = inject_summaries(rows)
    rec[BREAKDOWN_KEY] = breakdown(rows)
    rec[u"P29E に対応なしの行の数"] = unlinked_counts(rows)
    rec[H_KEY] = h_columns(per, rows)
    rec[EXISTING_KEY], rec[EXISTING_CMP_KEY] = existing_rates(rb)
    rec[u"限界"] = seal_limits(seal_text(root)) + list(EXTRA_LIMITS)
    rec[u"行"] = rows
    write_json(out, rec, key_value, text=RUN.dumps_inject(rec))
    say(u"-> %s(注入の行 %d)" % (out, len(rows)))
    return rec


# ======================================================================================================
# tally: 封の表(§3 の H-1〜H-10・§4 の K-1〜K-4)を読み、記録 2 つから判定する
def read_seal(root=ROOT):
    return seal_text(root)


def seal_pred_rows(seal):
    u"""封 §3 の表の行 {H-n: (欄, 予測, 外れ方)}。"""
    sec = seal[seal.index("## §3"):seal.index("## §4")]
    out = collections.OrderedDict()
    for line in sec.splitlines():
        m = re.match(r"^\| (H-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            out[m.group(1)] = (cells[0], cells[1], cells[2] if len(cells) > 2 else u"")
    return out


def seal_k_rows(seal):
    u"""封 §4 の K の行 {K-n: 本文}。"""
    sec4 = seal[seal.index("## §4"):seal.index("## §5")]
    return collections.OrderedDict((m.group(1), m.group(2)) for m in re.finditer(r"^- (K-\d): (.*)$", sec4, re.M))


NUM = r"[\d,]+(?:\.\d+)?"


def _pairs(text):
    return [(NF.num(a), NF.num(b)) for a, b in re.findall(r"(%s)〜(%s)" % (NUM, NUM), text)]


def seal_bounds(seal):
    u"""封の字から予測の幅と採用の基準の閾値を読む(字のコピーにしない)。{名前: 値}。"""
    P = seal_pred_rows(seal)
    K = seal_k_rows(seal)
    b = collections.OrderedDict()
    m = re.match(r"(\d+) / (\d+)$", P["H-1"][1])
    b["H-1"] = (int(m.group(1)), int(m.group(2)))
    t = P["H-2"][1]
    m = re.search(r"億\+万 (%s)〜(%s)・万だけ (%s)〜(%s)・兆\+億 (%s)〜(%s)" % ((NUM,) * 6), t)
    q = re.search(r"is_quantity 真 (%s)〜(%s)" % (NUM, NUM), t)
    b["H-2"] = collections.OrderedDict([
        (u"計", _pairs(t)[0]), (u"億+万", (NF.num(m.group(1)), NF.num(m.group(2)))), (u"万", (NF.num(m.group(3)), NF.num(m.group(4)))),
        (u"兆+億", (NF.num(m.group(5)), NF.num(m.group(6)))), (u"is_quantity 真", (NF.num(q.group(1)), NF.num(q.group(2))))])
    b["H-3"] = _pairs(P["H-3"][1])[0]
    b["H-4"] = collections.OrderedDict(zip((u"作れる site", u"採った", u"うち P30E が GROUNDED"), _pairs(P["H-4"][1])))
    b["H-5"] = collections.OrderedDict(zip((u"作れる site", u"採った", u"P29E に対応が付く行"), _pairs(P["H-5"][1])))
    b["H-6"] = _pairs(P["H-6"][1])[0]
    t1 = re.search(r"T1_VALUE (%s)〜(%s)%%" % (NUM, NUM), P["H-7"][1])
    t8 = re.search(r"T8_REL (%s)〜(%s)%%" % (NUM, NUM), P["H-7"][1])
    b["H-7"] = collections.OrderedDict([("T1_VALUE", (float(t1.group(1)), float(t1.group(2)))), ("T8_REL", (float(t8.group(1)), float(t8.group(2))))])
    t1 = re.search(r"T1 (%s)〜(%s)%%" % (NUM, NUM), P["H-8"][1])
    t8 = re.search(r"T8 (%s)〜(%s)%%" % (NUM, NUM), P["H-8"][1])
    b["H-8"] = collections.OrderedDict([("T1_VALUE", (float(t1.group(1)), float(t1.group(2)))), ("T8_REL", (float(t8.group(1)), float(t8.group(2))))])
    b["H-9"] = _pairs(P["H-9"][1])[0]
    m = re.match(r"(\d+) / (\d+) / (\d+)〜(\d+)$", P["H-10"][1])
    b["H-10"] = collections.OrderedDict([(u"round-trip 不一致", int(m.group(1))), (u"読み直し不一致", int(m.group(2))), (u"注入後の値(円)が refs に在る行", (int(m.group(3)), int(m.group(4))))])
    m = re.search(r"H-1 が (\d+) / (\d+)", K["K-1"])
    b["K-1"] = (int(m.group(1)), int(m.group(2)))
    m = re.search(r"round-trip 不一致 (\d+)・読み直し不一致 (\d+)", K["K-2"])
    b["K-2"] = collections.OrderedDict([(u"round-trip 不一致", int(m.group(1))), (u"読み直し不一致", int(m.group(2)))])
    b["K-3"] = NF.num(re.search(r"和 ≥ (%s)" % NUM, K["K-3"]).group(1))
    b["K-4"] = seal_mutation_names(seal)
    return b


within = RM.within


def k4_problems(tests, names):
    u"""K-4 の記録が封の字を満たすか: 既存の試験は 1 本以上走って全部緑、足した試験も全部緑、変異は封の名前の列と同じで、どれも赤・戻した。問題の列。"""
    out = []
    try:
        old, added, muts = tests[u"既存の試験(偽のまま)"], tests[u"足した試験"], tests[u"変異"]
    except (KeyError, TypeError):
        return [u"試験の記録が無い・形が違う"]
    for label, t in ((u"既存の試験", old), (u"足した試験", added)):
        if not (isinstance(t[u"試験"], int) and t[u"試験"] > 0):
            out.append(u"%s が 1 本も走っていない" % label)
        if t[u"失敗"] != 0 or t[u"エラー"] != 0:
            out.append(u"%s が緑でない" % label)
    if [m[u"名前"] for m in muts] != list(names):
        out.append(u"変異の名前が封の字と違う")
    for m in muts:
        if not (m[u"赤"] > 0 and m[u"戻した"] is True):
            out.append(u"変異 %s が赤にならないか戻っていない" % m[u"名前"])
    if tests.get(u"変異のあと lib が元に戻った") is not True:
        out.append(u"変異のあと lib が元に戻っていない")
    return out


def build_J(R_, seal):
    u"""{H: {H-n: {判定, 値}}, K: ..., 採用, 欄}。R_ = {"offcheck", "inject"}(記録の JSON)。欄は inject の記録の 本ごとの数え と 行 から数え直す(記録の ``H の欄`` は使わない)。"""
    inj = R_["inject"]
    return judge_from(R_["offcheck"], h_columns(inj[u"本ごとの数え"], inj[u"行"]), seal)


def judge_from(off, cols, seal):
    u"""off = offcheck の記録、cols = ``h_columns`` の返り値。封の幅に照らして判定する。"""
    B = seal_bounds(seal)
    P = seal_pred_rows(seal)
    J = collections.OrderedDict()

    def put(k, ok, val):
        J[k] = {u"判定": HIT if ok else MISS, u"値": val}
    a = off[u"集計"]
    put("H-1", (a[u"H-1 一致した本"], a[u"本"]) == B["H-1"], collections.OrderedDict([(u"一致した本", a[u"H-1 一致した本"]), (u"本", a[u"本"])]))
    n = cols[u"H-2 新しい token"]
    ok2 = all(within(n[k], B["H-2"][k]) for k in B["H-2"])
    put("H-2", ok2, collections.OrderedDict([(u"計", n[u"計"]), (u"億+万", n[u"億+万"]), (u"万だけ", n[u"万"]), (u"兆+億", n[u"兆+億"]), (u"is_quantity 真", n[u"is_quantity 真"])]))
    f = cols[u"H-3 円族の token(is_quantity 真)"]
    put("H-3", within(f[u"真"], B["H-3"]), collections.OrderedDict([(u"真", f[u"真"])]))
    h4, h5 = cols[u"H-4 T1_VALUE"], cols[u"H-5 T8_REL"]
    put("H-4", all(within(h4[k], B["H-4"][k]) for k in B["H-4"]), collections.OrderedDict((k, h4[k]) for k in B["H-4"]))
    put("H-5", all(within(h5[k], B["H-5"][k]) for k in B["H-5"]), collections.OrderedDict((k, h5[k]) for k in B["H-5"]))
    h6 = cols[u"H-6 T8_REL 基準に対応が付かない"]
    put("H-6", within(h6[u"率"], B["H-6"]), collections.OrderedDict([(u"件", h6[u"件"]), (u"円族の新しい token", h6[u"円族の新しい token"]), (u"率", h6[u"率"])]))
    h7 = cols[u"H-7 通した率(P30E)"]
    put("H-7", all(within(h7[t], B["H-7"][t]) for t in INJECT_TYPES), collections.OrderedDict((t + u" 通した率 P30E", h7[t]) for t in INJECT_TYPES))
    h8 = cols[u"H-8 名指して原本の率(P30E)"]
    put("H-8", all(within(h8[t], B["H-8"][t]) for t in INJECT_TYPES), collections.OrderedDict((t + u" 名指して原本 P30E", h8[t]) for t in INJECT_TYPES))
    d = cols[u"H-9 P29E と P30E で判定が違う行(P29E に対応が付く行)"]
    put("H-9", within(d, B["H-9"]), collections.OrderedDict([(u"違う行", d)]))
    h10 = cols[u"H-10"]
    put("H-10", h10[u"round-trip 不一致"] == B["H-10"][u"round-trip 不一致"] and h10[u"読み直し不一致"] == B["H-10"][u"読み直し不一致"]
        and within(h10[u"注入後の値(円)が refs に在る行"], B["H-10"][u"注入後の値(円)が refs に在る行"]),
        collections.OrderedDict([(u"round-trip 不一致", h10[u"round-trip 不一致"]), (u"読み直し不一致", h10[u"読み直し不一致"]), (u"注入後の値(円)が refs に在る行", h10[u"注入後の値(円)が refs に在る行"])]))
    K = collections.OrderedDict()
    K["K-1"] = {u"判定": J["H-1"][u"判定"], u"値": collections.OrderedDict([("H-1", J["H-1"][u"判定"])])}
    k2 = h10[u"round-trip 不一致"] == B["K-2"][u"round-trip 不一致"] and h10[u"読み直し不一致"] == B["K-2"][u"読み直し不一致"]
    K["K-2"] = {u"判定": HIT if k2 else MISS, u"値": collections.OrderedDict([(u"round-trip 不一致", h10[u"round-trip 不一致"]), (u"読み直し不一致", h10[u"読み直し不一致"])])}
    total = h4[u"採った"] + h5[u"採った"]
    K["K-3"] = {u"判定": HIT if total >= B["K-3"] else MISS, u"値": collections.OrderedDict([(u"採った site の和", total)])}
    prob = k4_problems(off.get(u"試験"), B["K-4"])
    tests = off.get(u"試験") or {}
    old_t = tests.get(u"既存の試験(偽のまま)") or {}
    muts = tests.get(u"変異") or []
    K["K-4"] = {u"判定": HIT if not prob else MISS,
                u"値": collections.OrderedDict([(u"既存の試験の失敗とエラー", old_t.get(u"失敗", 0) + old_t.get(u"エラー", 0) if old_t else None),
                                              (u"赤になった変異", sum(1 for m in muts if m.get(u"赤", 0) > 0)), (u"変異", len(muts))])}
    adopt = all(K[k][u"判定"] == HIT for k in K)
    return collections.OrderedDict([(u"H", J), (u"K", K), (u"採用", adopt), (u"欄", collections.OrderedDict((k, v[0]) for k, v in P.items()))])


fmt = RM.fmt


def render_pred(J, seal=None):
    seal = seal if seal is not None else read_seal()
    P = seal_pred_rows(seal)
    lines = [u"| # | 欄 | 予測 | 測った値 | 判定 |", u"|---|---|---|---|---|"]
    for k, v in J[u"H"].items():
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
    ap.add_argument("cmd", choices=("offcheck", "inject", "tally"))
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", default=None, help="offcheck・inject: この docID の本だけ")
    ap.add_argument("--procs", type=int, default=1)
    a = ap.parse_args(argv)
    if a.cmd == "offcheck":
        run_offcheck(root=a.root, procs=a.procs, only=a.only, out=a.out)
    elif a.cmd == "inject":
        run_inject(root=a.root, procs=a.procs, only=a.only, out=a.out)
    else:
        run_tally(root=a.root)


if __name__ == "__main__":
    main()
