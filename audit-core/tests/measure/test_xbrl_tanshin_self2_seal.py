# -*- coding: utf-8 -*-
"""封 docs/XBRL_TANSHIN_SELF2_SEAL_2026-11-14.md(TSS の第 2 便 ― (一)中間の短信の期の名前を measure/ の側で写して読む・(二)「値が違う」のうち表の値に近い行だけを拾って読む)の測定の門。封 §0-2・§1・§2・§3・§5。

**この門が縛るもの**(結果の門 ``test_xbrl_tanshin_self2_result.py`` は次の段。記録・文書・読んだ型を縛る)

1. 封の字: §3 が U-1〜U-10 の 10 行・3 つの置き換えとその順・名前がぶつかる 3 つの字・近い行の規則の幅(2%・0.5・3 桁)・当たる例と当たらない例・種 20261115・200 行・型 5 つの字・記録の path。
2. 封の字と script の定数が同じ(表は封の file から読む。script に写さない)。定数を 1 つずつ替えると赤になる。
3. engine 0 行: 封の commit から HEAD まで ``core/``・``adapters/``・``measure/lib``・``measure/inject.py``・読み込む前の便の script を触っていない(未 commit の変更も見る)。
   第 1 便の script・置く script・記録は、封より後ろに出来たので、第 1 便の結果の commit(10077555)から 0 行。
4. 順序: 封 a1fd09bf ⊏ script・この門(**commit の順**。未 commit は赤。skip にしない。第 1 便の門と同じ)。
5. 置き換え(``rewrite_zip``・``prepare``・``judge2``)・近い行の規則(``near_rules``・``digits_close``)・interim・near・sheet・types の振る舞い。
6. 配線: 第 1 便の関数を **呼ぶ**(同名の関数を定義しない)・読み込みの前に居た ``sys.modules`` の名前は戻る・包んだ ZIP を書かない・通信の module を import しない・docID・証券コード・TDnet の番号の字が無い。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``・``CONST_MUTANTS``)。変異の表に入れない「同じ出力になる変異」は次の 3 つ(出力が同じなので赤にならない。理由を書く):
(あ) ``REPLACEMENTS`` の順を入れ替える ― 3 つの置き換えは互いの出力に当たらないので出力は同じ。順は定数の照合(封の字の順)で赤にする。
(い) ``near_rules`` の ``f > 0`` を外す ― ``c != f`` と ``|c − f| ≤ f × 2%`` が残るので、f = 0 では常に外れる。
(う) ``digits_close`` の ``a == b`` を外す ― 同じ字なら違う桁が 0 個で、あとの 2 つの条件のどちらにも当たらない。
この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import ast
import collections
import contextlib
import copy
import importlib.util
import io
import json
import os
import random
import re
import sys
import tempfile
import types
import unittest
import warnings
import zipfile
from fractions import Fraction

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


G1 = load_module("tests/measure/test_xbrl_tanshin_self_seal.py", "tanshin_self_seal_gate_helpers_for_self2_seal")        # 第 1 便の門の道具(fixture・変異の差し込み・順序の部品)。門としては走らせない
MS = load_module("measure/xbrl_tanshin_self2_2026-11-14.py", "tanshin_self2_script_for_seal_gate")
PR = G1.PR
TSS, ST, TS = MS.TSS, MS.ST, MS.TS
patched, mutated, guard, tmpdir, eqp, expect_stop, make_zip, strip_time = G1.patched, G1.mutated, G1.guard, G1.tmpdir, G1.eqp, G1.expect_stop, G1.make_zip, G1.strip_time

SEAL_REL = "docs/XBRL_TANSHIN_SELF2_SEAL_2026-11-14.md"
SEAL_COMMIT_SHORT = "a1fd09bf"                 # 封の commit(literal に留める。script の定数と違えば script_problems が赤)
TSS_SEAL_REL = "docs/XBRL_TANSHIN_SELF_SEAL_2026-11-14.md"
SCRIPT_REL = "measure/xbrl_tanshin_self2_2026-11-14.py"
TSS_REL = "measure/xbrl_tanshin_self_2026-11-14.py"
STAGE_REL = "measure/xbrl_tanshin_self_stage_2026-11-14.py"
GATE_REL = "tests/measure/test_xbrl_tanshin_self2_seal.py"
LATER_GATE_REL = "tests/measure/test_xbrl_tanshin_self2_result.py"
DOC_REL = "docs/XBRL_TANSHIN_SELF2_RESULT_2026-11-14.md"
RECORD_RELS = ("fixtures/xbrl/tanshin_self/states_interim_2026-11-14.json", "fixtures/xbrl/tanshin_self/near_2026-11-14.json", "fixtures/xbrl/tanshin_self/near_types_2026-11-14.json")
SCRIPT_RELS = (SCRIPT_REL,)
TSS_STATES_REL = "fixtures/xbrl/tanshin_self/states_2026-11-14.json"
POPULATION_REL = "fixtures/xbrl/tanshin_self/population_2026-11-14.json"
#: 封の commit から 0 行でなければならない path(engine・lib・仕掛けと、この便が読み込む前の便の script・記録。第 1 便は封より後に出来たので別)
NOT_TOUCHED_RELS = ("adapters", "core", "measure/lib", "measure/inject.py", "measure/xbrl_tanshin_2026-11-09.py", "measure/xbrl_tanshin_fetch_2026-11-09.py", "fixtures/xbrl/tanshin")
#: 第 1 便の結果の commit(10077555)から 0 行でなければならない path(第 1 便の script・置く script・記録)
TSS_RESULT_COMMIT = "10077555"
TSS_FROZEN_RELS = (TSS_REL, STAGE_REL, POPULATION_REL, TSS_STATES_REL, TSS_SEAL_REL)
SEAL_PHRASES = (
    u"`\"Prior1InterimDuration` → `\"Prior1YearDuration`",
    u"`\"InterimDuration` → `\"CurrentYearDuration`",
    u"`\"InterimInstant` → `\"CurrentYearInstant`",
    u"`\"CurrentYearDuration`・`\"CurrentYearInstant`・`\"Prior1YearDuration`",
    u"**その本は写さずに**",
    u"`random.Random(20261115).sample(range(行の数), 200)`",
    u"`f > 0` かつ `0 < |c − f| / f ≤ 0.02`",
    u"四捨五入(0.5 は切り上げ)",
    u"`0 < | |v| − |r| | ≤ 0.5`",
    u"桁数が同じで 3 桁以上",
    u"司令塔(**AI の席。人は読んでいない**)",
    u"`v` 15960・百万円・`r` 16145000000.0 → `|c − f| / f` = 0.0115 → N-円",
    u"`v` 12345・百万円・`r` 12435000000.0 → N-円 と N-桁(入れ替わり)",
    u"`v` 104.6・%・`r` 104.2 → N-率",
    u"`v` 98000・百万円・`r` 94400000000.0(0.038)",
    u"`v` 104.6・%・`r` 103.47(1.13)",
    u"`v` 15960・百万円・`r` 15960000000.0(差 0",
    u"TSS の記録 `fixtures/xbrl/tanshin_self/population_2026-11-14.json` を読み、sha256 が 1 つでも違えば止める",
    u"A をもう 1 回走らせた行の state が、TSS の記録と行ごとに同じか",
    u"2 回走らせて、時間の欄を除き byte で同じか",
    u"採る・採らないの判定は無い",
)
PRED_IDS = tuple("U-%d" % i for i in range(1, 11))
#: 封 §0-2 の 2 の 3 つの置き換え(literal に留める。script の定数と照らす)
SEALED_REPLACEMENTS = ((b'"Prior1InterimDuration', b'"Prior1YearDuration'), (b'"InterimDuration', b'"CurrentYearDuration'), (b'"InterimInstant', b'"CurrentYearInstant'))
SEALED_MARKS = (b'"CurrentYearDuration', b'"CurrentYearInstant', b'"Prior1YearDuration')
SHAPE5 = (5, collections.OrderedDict([(u"甲", 1), (u"乙", 1), (u"丙", 3)]))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. 封の字
def seal_replacements(seal):
    u"""封 §0-2 の 2 の 3 つの置き換え [(前, 後)](番号つきの行)。"""
    try:
        sec = seal[seal.index(u"### §0-2"):seal.index(u"## §1")]
    except ValueError:
        return []
    return [(m[0].encode("ascii"), m[1].encode("ascii")) for m in re.findall(u"^\\s+\\d\\. `(\"\\w+)` → `(\"\\w+)`$", sec, re.M)]


def seal_problems(seal):
    out = []
    try:
        sec2 = seal[seal.index(u"## §2"):seal.index(u"## §3")]
        sec3 = seal[seal.index(u"## §3"):seal.index(u"## §4")]
        sec5 = seal[seal.index(u"## §5"):seal.index(u"## §6")]
    except ValueError:
        return [u"封の節(§1〜§6)が揃っていない"]
    ids = re.findall(r"^- \*\*(U-\d+)\*\*", sec3, re.M)
    if ids != list(PRED_IDS):
        out.append(u"封 §3 が U-1〜U-10 の 10 行でない: %s" % ids)
    if tuple(seal_replacements(seal)) != SEALED_REPLACEMENTS:
        out.append(u"封の 3 つの置き換え・順が門に留めた字と違う")
    for rel in RECORD_RELS + (DOC_REL, SCRIPT_REL):
        if rel not in sec2:
            out.append(u"封 §2 に path が無い: %s" % rel)
    for rel in (u"test_xbrl_tanshin_self2_seal.py", u"test_xbrl_tanshin_self2_result.py"):
        if rel not in sec2:
            out.append(u"封 §2 に門の path が無い: %s" % rel)
    if SCRIPT_REL not in sec2 and SCRIPT_REL not in sec5:
        out.append(u"封に script の path が無い")
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
    if ms.SCRIPT_REL != SCRIPT_REL or ms.DOC_REL != DOC_REL or ms.TSS_SCRIPT_REL != TSS_REL or ms.TSS_SEAL_REL != TSS_SEAL_REL:
        out.append(u"script・結果の文書・第 1 便の path が封 §2・§5 と違う")
    if (ms.INTERIM_REL, ms.NEAR_REL, ms.NEAR_TYPES_REL) != RECORD_RELS or ms.TSS_STATES_REL != TSS_STATES_REL:
        out.append(u"記録の path が封 §2 と違う")
    if tuple(ms.PRODUCTION_RELS) != RECORD_RELS[:2]:
        out.append(u"本番の記録の guard の対象が interim と near でない")
    if tuple(ms.REPLACEMENTS) != tuple(seal_replacements(seal)):
        out.append(u"置き換えの定数が封の字(順も)と違う")
    if tuple(ms.COLLISION_MARKS) != SEALED_MARKS or u"`\"CurrentYearDuration`・`\"CurrentYearInstant`・`\"Prior1YearDuration`" not in seal:
        out.append(u"名前がぶつかる印が封 §0-2 の 2 と違う")
    if ms.PROFILE != "P33E":
        out.append(u"profile が P33E でない")
    if (ms.INTERIM_GROUPS, ms.A_GROUPS, ms.B_GROUPS) != ((u"丙",), (u"甲", u"乙"), (u"丙",)):
        out.append(u"A・B・中間の群が封 §0-2 の 2・3 と違う")
    if list(ms.YEN_UNITS.items()) != [(u"円", 1), (u"千円", 10 ** 3), (u"万円", 10 ** 4), (u"百万円", 10 ** 6), (u"億円", 10 ** 8), (u"兆円", 10 ** 12)]:
        out.append(u"N-円・N-桁の単位と倍率が封 §0-2 の 4 と違う")
    for u in (u"円", u"千円", u"万円", u"百万円", u"億円", u"兆円"):
        if u"`%s`" % u not in seal:
            out.append(u"封に単位 %s が無い" % u)
    if u"倍率 `m` = 1・1e3・1e4・1e6・1e8・1e12" not in seal:
        out.append(u"封に倍率の字が無い")
    if ms.YEN_BAND != Fraction(2, 100) or ms.PCT_BAND != Fraction(1, 2) or ms.MIN_DIGITS != 3:
        out.append(u"規則の幅(2%・0.5・3 桁)が封 §0-2 の 4 と違う")
    if tuple(ms.RULES) != (u"N-円", u"N-桁", u"N-率"):
        out.append(u"規則の名前が封 §0-2 の 4 と違う")
    if (ms.SAMPLE_SEED, ms.SAMPLE_N) != (20261115, 200):
        out.append(u"読む行の種・本数が封 §0-2 の 5 と違う")
    if list(ms.TYPES) != list(u"あいうえお"):
        out.append(u"型が (あ)〜(お) の 5 つでない")
    for k, v in ms.TYPES.items():
        if u"(%s) %s\n" % (k, v) not in seal.replace(u"**", u""):                  # 行の終わりまで(字が途中で切れた版を通さない)
            out.append(u"型 (%s) の字が封 §0-2 の 5 と違う" % k)
    if u"AI の席" not in ms.TYPED_BY or u"人は読んでいない" not in ms.TYPED_BY:
        out.append(u"型を付けた席の字が封 §0-2 の 5 と違う")
    if tuple(ms.NEAR_ROW_COLUMNS) != (u"本の #", u"文の番号", u"位置", u"当たった規則", u"単位の族") or u"本の #・文の番号・位置・当たった規則・単位の族" not in seal:
        out.append(u"近い行の行の欄が封 §0-2 の 6 と違う")
    if ms.ST is not ms.TSS.ST or ms.TS is not ms.TSS.TS:
        out.append(u"第 1 便の script と別の instance(置く script・2026-11-09 の便)を使っている")
    if (ms.TSS.ATTACH_PREFIX, ms.TSS.OLD_SUFFIX, ms.TSS.ZIP_DATE_TIME) != ("XBRLData/Attachment/", "-ixbrl.htm", (1980, 1, 1, 0, 0, 0)):
        out.append(u"第 1 便の包み直しの定数が封 §0-2 の 2 の「wrap が入れる member」と違う")
    return out


# ---------------------------------------------------------------- 3. engine 0 行
def untouched_problems(root=REPO, base=None, rels=NOT_TOUCHED_RELS, prefix=PREFIX, seal_rel=SEAL_REL):
    u"""base(既定は封の commit)から HEAD までに rels を触った commit と、未 commit の変更を列挙する(1 つでも在れば問題)。"""
    if base is None:
        seal_commits = PR.added_commits(root, prefix + seal_rel)
        if len(seal_commits) != 1:
            return [u"封の commit が履歴に 1 つに決まらない"]
        base = seal_commits[0]
    rc, _ = PR.git_in(root, "cat-file", "-e", base + "^{commit}")
    if rc != 0:
        return [u"基準の commit が履歴に無い"]
    rc, log = PR.git_in(root, "log", "--format=%H", "%s..HEAD" % base, "--", *[prefix + r for r in rels])
    if rc != 0:
        return [u"git log が失敗した"]
    out = [u"基準の後に engine・lib・仕掛け・前の便を触った commit %s" % c[:7] for c in log.split() if c]
    rc, st = PR.git_in(root, "status", "--porcelain", "--", *[prefix + r for r in rels])
    if rc != 0:
        return out + [u"git status が失敗した"]
    return out + [u"未 commit の変更: %s" % ln[3:] for ln in st.split("\n") if ln.strip()]


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = list(SCRIPT_RELS + (GATE_REL,)) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others)


# ---------------------------------------------------------------- 6. 配線・名前・docID・通信
#: 第 1 便・置く script・前の便の関数。測る script は同名の関数を定義せず、(module の別名, 関数名)を呼ぶ
REUSED_FUNCS = (("TSS", "cut"), ("TSS", "wrap"), ("TSS", "judge_book"), ("TSS", "block"), ("TSS", "pick_sample"), ("TSS", "inside_repo"), ("TSS", "sheet_text"), ("TSS", "load_json"),
                ("TS", "unit_family"), ("TS", "dumps_states"), ("TS.NF", "map_pool"), ("TS.R", "build_raw_claims"), ("TS.RUN", "sentence_list"),
                ("ST", "read_population"), ("ST", "validate_population"), ("ST", "write_text_exclusive"), ("ST", "dumps_record"), ("ST", "key_leaks"), ("ST", "sha256_file"),
                ("ST", "sha256_bytes"), ("ST", "names_snapshot"), ("ST", "git_head"), ("ST", "display_path"), ("ST", "default_cache_dir"))
#: 測る script が定義してはいけない名前(第 1 便・前の便が持つ関数の名前)
NOT_REDEFINED = ("cut", "cut_lines", "cut_html", "wrap", "overview_html", "judge_book", "block", "tally", "pick_sample", "inside_repo", "sheet_text", "html_to_lines",
                 "profile_rows", "row_entry", "state_counts", "reason_counts", "vm_breakdown", "dumps_states", "dumps_record", "write_text_exclusive", "read_population",
                 "validate_population", "names_snapshot", "key_leaks", "sha256_file", "sha256_bytes", "map_pool", "sentence_list", "build_raw_claims", "load_json", "unit_family")
NETWORK_MODULES = ("urllib", "http", "socket", "ssl", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx")


def defined_functions(path):
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    return set(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))


def resolve(ms, dotted):
    obj = ms
    for part in dotted.split("."):
        obj = getattr(obj, part, None)
    return obj


def reuse_problems(ms=None, src_path=None):
    u"""測る script が第 1 便・前の便の関数を呼ぶ(同名の関数を定義しない)。"""
    ms = ms or MS
    path = src_path or os.path.join(ROOT, SCRIPT_REL)
    defs = defined_functions(path)
    with open(path, encoding="utf-8") as fh:
        body = fh.read()
    out = []
    for name in NOT_REDEFINED:
        if name in defs:
            out.append(u"%s と同名の関数を script が定義している(呼ぶ)" % name)
    for alias, fn in REUSED_FUNCS:
        if not callable(getattr(resolve(ms, alias), fn, None)):
            out.append(u"%s.%s が module に無い" % (alias, fn))
        if not re.search(r"\b%s\.%s\b" % (re.escape(alias), fn), body):
            out.append(u"script が %s.%s を呼んでいない" % (alias, fn))
    return out


def network_problems(path=None):
    path = path or os.path.join(ROOT, SCRIPT_REL)
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    out = []
    for n in ast.walk(tree):
        names = [a.name for a in n.names] if isinstance(n, ast.Import) else ([n.module or u""] if isinstance(n, ast.ImportFrom) else [])
        for nm in names:
            if nm.split(".")[0] in NETWORK_MODULES:
                out.append(u"通信の module を import している: %s" % nm)
    return out


def name_problems(rels=SCRIPT_RELS + (GATE_REL,), base=ROOT, codes=None):
    return G1.name_problems(rels=rels, base=base, codes=codes)


def reserved_problems(rels=(GATE_REL,), base=ROOT):
    return G1.reserved_problems(rels=rels, base=base)


# ================================================================ 振る舞いの検査(``*_problems`` は問題の字の列を返す。変異した版でも呼べるよう、module の名前で引く)
IX_I = G1.IX.replace(u"CurrentYearDuration", u"InterimDuration").replace(u"Prior1YearDuration", u"Prior1InterimDuration")      # 中間の期の名前の iXBRL
COLLIDE = u'<p id="CurrentYearDuration_x"></p>'
SENTS4 = [u"売上高は1,234百万円となりました。", u"売上高は1,250百万円となりました。", u"売上高は1,324百万円となりました。", u"売上高は1,300百万円となりました。"]
SENTS5 = SENTS4 + [u"売上高は1,245百万円となりました。"]           # 5 文目も N-円(1 冊に同じ規則の行が 2 つ在る形)


def izip(sents, ix=IX_I, kind=u"scedjpsm", tag=b"", with_q=True):
    q = u"<p>1.当中間決算に関する定性的情報</p>" + u"".join(u"<p>%s</p>" % s for s in sents) + u"<p>2.次の節</p>"
    m = []
    if with_q:
        m.append(("XBRLData/Attachment/qualitative.htm", q.encode("utf-8")))
    m.append(("XBRLData/Attachment/0200000-ixbrl.htm", ix.encode("utf-8")))
    m.append(("XBRLData/Summary/tse-%s-00001-ixbrl.htm" % kind, b"summary" + tag))
    return make_zip(m)


def fixture5(d):
    u"""作り物の材料 5 本。1 甲(通期の名前・5 文)・2 乙(中間の名前だが A なので写さない・2 文)・3 丙(中間・5 文・写す)・4 丙(中間・名前がぶつかる)・5 丙(切れない)。
    (表, 材料の folder, root, ZIP の列, TSS の記録の本 {#: 本(写さない判定)})。"""
    zips = [izip(SENTS5, ix=G1.IX, kind=u"acedjpsm", tag=b"1"), izip(SENTS5[:2], kind=u"acedifsm", tag=b"2"), izip(SENTS5, kind=u"scedjpsy", tag=b"3"),
            izip(SENTS5[1:2], ix=IX_I.replace(u"</body>", COLLIDE + u"</body>"), kind=u"scedjpsy", tag=b"4"), izip(SENTS5, kind=u"scedjpsy", tag=b"5", with_q=False)]
    kinds = [u"acedjpsm", u"acedifsm", u"scedjpsy", u"scedjpsy", u"scedjpsy"]
    import hashlib
    pop = [(i + 1, g, k, hashlib.sha256(z).hexdigest()) for i, (g, k, z) in enumerate(zip([u"甲", u"乙", u"丙", u"丙", u"丙"], kinds, zips))]
    mat = os.path.join(d, "mat")
    os.makedirs(mat)
    for r, z in zip(pop, zips):
        with open(os.path.join(mat, r[3] + ".zip"), "wb") as fh:
            fh.write(z)
    root = os.path.join(d, "root")
    os.makedirs(root)
    tss = dict((r[0], TSS.judge_book(r[0], r[1], r[2], r[3], z)) for r, z in zip(pop, zips))
    return pop, mat, root, zips, tss


def kw5(root, pop, mat, tss):
    return dict(root=root, population=pop, shape=SHAPE5, material=mat, tss_states=tss, say=lambda *a: None)


def boom(*a, **k):
    u"""止める前に呼ばれてはいけない関数の差し替え(呼ばれたら AssertionError。SystemExit ではないので expect_stop をすり抜けて赤になる)。"""
    raise AssertionError(u"止める前に先へ進んだ")


def dump_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False))


def rules_problems():
    u"""近い行の規則(封 §0-2 の 4)の当たる例・当たらない例・境界・N-桁の丸め・桁数・入れ替わり・数でない値。"""
    out = []
    R = MS.near_rules
    D, P = u"direct_value", u"derived_value"
    # 封の例 6 つ
    eqp(out, u"封の例 N-円", R(15960, u"百万円", D, 16145000000.0), [u"N-円"])
    eqp(out, u"封の例 N-円 と N-桁(入れ替わり)", R(12345, u"百万円", D, 12435000000.0), [u"N-円", u"N-桁"])
    eqp(out, u"封の例 N-率", R(104.6, u"%", P, 104.2), [u"N-率"])
    eqp(out, u"封の当たらない例 0.038", R(98000, u"百万円", D, 94400000000.0), [])
    eqp(out, u"封の当たらない例 1.13", R(104.6, u"%", P, 103.47), [])
    eqp(out, u"封の当たらない例 差 0", R(15960, u"百万円", D, 15960000000.0), [])
    # 境界: ちょうど 2%(float の誤差で外れない)・2% を少し超える・差 0
    eqp(out, u"ちょうど 2%", R(10200, u"百万円", P, 10000000000.0), [u"N-円"])
    eqp(out, u"ちょうど 2%(float の計算では外れる値: 0.0357 千円 対 35.0)", R(0.0357, u"千円", P, 35.0), [u"N-円"])
    eqp(out, u"2% を超える", R(10201, u"百万円", P, 10000000000.0), [])
    eqp(out, u"ちょうど 2%(下側)", R(9800, u"百万円", P, 10000000000.0), [u"N-円"])
    eqp(out, u"2% を超える下側", R(9799, u"百万円", P, 10000000000.0), [])
    # 符号は見ない・倍率
    eqp(out, u"v が負でも |v| で比べる", R(-1250, u"百万円", P, 1234000000.0), [u"N-円"])
    eqp(out, u"r が負でも |r| で比べる", R(1250, u"百万円", P, -1234000000.0), [u"N-円"])
    eqp(out, u"倍率(億円)", R(12.5, u"億円", P, 1234000000.0), [u"N-円"])
    eqp(out, u"倍率(兆円)", R(1.25, u"兆円", P, 1234000000000.0), [u"N-円"])
    eqp(out, u"倍率(万円)", R(125000, u"万円", P, 1234000000.0), [u"N-円"])
    eqp(out, u"倍率(円)", R(1250000000, u"円", P, 1234000000.0), [u"N-円"])
    eqp(out, u"倍率を掛けないと当たらない(百万円の数を円として比べない)", R(1234, u"百万円", P, 1250.0), [])
    eqp(out, u"f = 0", R(5, u"百万円", D, 0.0), [])
    # N-桁: 入れ替わり・1 桁違い・桁数違い・2 桁しか無い・form・整数・丸め
    eqp(out, u"N-桁 1 桁違い", R(12445, u"百万円", D, 12345000000.0), [u"N-円", u"N-桁"])
    eqp(out, u"N-桁 v が負でも |v| の字で見る", R(-12435, u"百万円", D, 12345000000.0), [u"N-円", u"N-桁"])
    eqp(out, u"N-桁 r が負でも |r| で見る", R(12435, u"百万円", D, -12345000000.0), [u"N-円", u"N-桁"])
    eqp(out, u"N-桁 3 桁の 1 桁違い", R(123, u"百万円", D, 124000000.0), [u"N-円", u"N-桁"])
    eqp(out, u"N-桁 2 桁しか無い", R(12, u"百万円", D, 13000000.0), [])
    eqp(out, u"N-桁 1 桁しか無い", R(5, u"百万円", D, 6000000.0), [])
    eqp(out, u"N-桁 derived_value は入れない", R(12345, u"百万円", P, 12435000000.0), [u"N-円"])
    eqp(out, u"N-桁 v が整数でない", R(12435.5, u"百万円", D, 12345000000.0), [u"N-円"])
    eqp(out, u"N-桁 v が整数の float", R(12435.0, u"百万円", D, 12345000000.0), [u"N-円", u"N-桁"])
    eqp(out, u"N-桁 となり合わない入れ替わり", R(4231, u"百万円", D, 1234000000.0), [])
    eqp(out, u"N-桁 片方だけ一致(入れ替わりでない 2 桁違い)", R(1234, u"百万円", D, 1253000000.0), [u"N-円"])
    eqp(out, u"N-桁 3 桁違い", R(12345, u"百万円", D, 12999000000.0), [])
    eqp(out, u"N-桁 floor を切り上げ側だけで見ない(f / m = 12345.5 → floor 12345)", R(12435, u"百万円", D, 12345500000.0), [u"N-円", u"N-桁"])
    eqp(out, u"N-桁 四捨五入は 0.5 を切り上げる(f / m = 12344.5 → 12345。銀行丸めなら 12344)", R(12435, u"百万円", D, 12344500000.0), [u"N-円", u"N-桁"])
    eqp(out, u"N-桁 floor でも四捨五入でも合わない(f / m = 12344.4 → 12344 と 12344)", R(12435, u"百万円", D, 12344400000.0), [u"N-円"])
    eqp(out, u"N-桁 円の単位(円)", R(123456, u"円", D, 123546.0), [u"N-円", u"N-桁"])
    eqp(out, u"N-桁 % の unit には掛けない", R(12345, u"%", D, 12435.0), [])
    # N-率
    eqp(out, u"N-率 ちょうど 0.5(float の引き算では外れる: 1.1 対 0.6)", R(1.1, u"%", P, 0.6), [u"N-率"])
    eqp(out, u"N-率 ちょうど 0.5", R(104.7, u"%", P, 104.2), [u"N-率"])
    eqp(out, u"N-率 0.5 を超える", R(104.8, u"%", P, 104.2), [])
    eqp(out, u"N-率 差 0", R(104.2, u"%", P, 104.2), [])
    eqp(out, u"N-率 符号を除いて比べる", R(104.6, u"%", P, -104.2), [u"N-率"])
    eqp(out, u"N-率 direct_value でも見る(差 0.4)", R(104.6, u"%", D, 104.2), [u"N-率"])
    eqp(out, u"N-率 direct_value でも見る(差 0.6 は外れ)", R(104.8, u"%", D, 104.2), [])
    eqp(out, u"N-率 direct_value の整数値でも % では N-率だけ", R(104, u"%", D, 104.4), [u"N-率"])
    eqp(out, u"N-率 ポイントは入れない", R(104.6, u"ポイント", P, 104.2), [])
    eqp(out, u"N-率 円の unit では見ない", R(104.6, u"百万円", P, 104.2), [])
    eqp(out, u"他の unit", R(1, u"株", P, 2.0), [])
    # 数でない値
    for label, v, r in ((u"recomputed が None", 1250, None), (u"recomputed が文字", 1250, u"1234"), (u"value が None", None, 1234000000.0), (u"recomputed が bool", 1250, True),
                        (u"value が bool", True, 1.0), (u"recomputed が nan", 1250, float("nan")), (u"recomputed が inf", 1250, float("inf")), (u"value が inf", float("inf"), 1.0)):
        eqp(out, label, R(v, u"百万円", D, r), [])
    # digits_close の直接
    C = MS.digits_close
    eqp(out, u"digits 1 桁違い", [C(u"12345", u"12445"), C(u"123", u"124"), C(u"99", u"98")], [True, True, False])
    eqp(out, u"digits 入れ替わり", [C(u"12345", u"12435"), C(u"1234", u"2134"), C(u"4231", u"1234")], [True, True, False])
    eqp(out, u"digits 桁数違い", [C(u"1234", u"12355"), C(u"12355", u"1234"), C(u"123", u"1234")], [False, False, False])
    eqp(out, u"digits 同じ字・2 桁違いの入れ替えでない", [C(u"1234", u"1234"), C(u"1234", u"1256"), C(u"1234", u"1253")], [False, False, False])
    eqp(out, u"digits 下限 3", [C(u"12", u"13"), C(u"1", u"2"), C(u"100", u"101")], [False, False, True])
    # is_number・exact
    eqp(out, u"is_number", [MS.is_number(1), MS.is_number(1.5), MS.is_number(True), MS.is_number(None), MS.is_number(u"1"), MS.is_number(float("nan")), MS.is_number(float("inf"))],
        [True, True, False, False, False, False, False])
    eqp(out, u"exact は repr の 10 進", (MS.exact(0.1), MS.exact(104.7), MS.exact(3)), (Fraction(1, 10), Fraction(1047, 10), Fraction(3)))
    return out


def replace_problems():
    u"""置き換え(封 §0-2 の 2): 当たる例・当たらない例・順・wrap が入れる member だけ・名前がぶつかる本は写さない・``prepare``・``judge2``・文の block は TSS のまま。"""
    out = []
    attach = (u'<x contextRef="InterimDuration" id="InterimInstant_NonConsolidatedMember" a="Prior1InterimDuration_x" b="Prior1InterimInstant" c="Prior1YearInstant" '
              u'd="Prior2YearInstant" e="CurrentQuarterDuration" f=InterimDuration g="xInterimDuration" h="InterimDuration" i="InterimDuration"/>').encode("utf-8")
    want = (u'<x contextRef="CurrentYearDuration" id="CurrentYearInstant_NonConsolidatedMember" a="Prior1YearDuration_x" b="Prior1InterimInstant" c="Prior1YearInstant" '
            u'd="Prior2YearInstant" e="CurrentQuarterDuration" f=InterimDuration g="xInterimDuration" h="CurrentYearDuration" i="CurrentYearDuration"/>').encode("utf-8")
    members = [("XBRLData/Attachment/0200000-ixbrl.htm", attach), ("XBRLData/Attachment/sub/b-ixbrl.htm", b'"InterimDuration"'), ("XBRLData/Attachment/qualitative.htm", b'"InterimDuration"'),
               ("XBRLData/Summary/tse-scedjpsm-1-ixbrl.htm", b'"InterimInstant"'), ("XBRLData/Attachment/c.htm", b'"InterimDuration"'), ("XBRLData/Other/e-ixbrl.htm", b'"InterimDuration"'),
               ("a-ixbrl.htm", b'"InterimDuration"'), ("XBRLData/Attachment/d-ixbrl.html", b'"InterimDuration"')]
    zb = make_zip(members)
    zb2, hit, counts = MS.rewrite_zip(zb)
    z2 = zipfile.ZipFile(io.BytesIO(zb2))
    eqp(out, u"ぶつからない・回数(規則 1・2・3)", (hit, counts), (False, [1, 3 + 1, 1]))
    eqp(out, u"member の名前と順は同じ", z2.namelist(), [m[0] for m in members])
    got = [z2.read(m[0]) for m in members]
    eqp(out, u"置き換えるのは wrap が入れる member だけ", got, [want, b'"CurrentYearDuration"'] + [m[1] for m in members[2:6]] + [members[6][1], members[7][1]])
    eqp(out, u"入れる member が 2 つ", sum(1 for m in members if MS.is_wrapped_member(m[0])), 2)
    eqp(out, u"is_wrapped_member", [MS.is_wrapped_member(x) for x in ("XBRLData/Attachment/a-ixbrl.htm", "XBRLData/Attachment/x/a-ixbrl.htm", "XBRLData/Summary/a-ixbrl.htm", "XBRLData/Attachment/a.htm",
                                                                      "a-ixbrl.htm", "XBRLData/Attachment/a-ixbrl.html")], [True, True, False, False, False, False])
    # 順に掛ける(置き換えが重ならない)・複数回の当たりを全部置き換える
    one = zipfile.ZipFile(io.BytesIO(MS.rewrite_zip(make_zip([("XBRLData/Attachment/a-ixbrl.htm", b'"InterimDuration "InterimDuration "InterimDuration')]))[0])).read("XBRLData/Attachment/a-ixbrl.htm")
    eqp(out, u"3 回とも置き換える", one, b'"CurrentYearDuration "CurrentYearDuration "CurrentYearDuration')
    # 名前がぶつかる本は ZIP をそのまま返す(3 つの印のそれぞれ)
    for mark in SEALED_MARKS:
        zc = make_zip([("XBRLData/Attachment/a-ixbrl.htm", mark + b'x "InterimDuration')])
        r = MS.rewrite_zip(zc)
        eqp(out, u"ぶつかる(%s)" % mark.decode("ascii"), (r[0] == zc, r[1], r[2]), (True, True, [0, 0, 0]))
    # 入れる member が 2 つ以上で、印が 2 つ目の member にだけ在る(最初の member だけでぶつかりを見ると通ってしまう)
    for mark in SEALED_MARKS:
        zc = make_zip([("XBRLData/Attachment/a-ixbrl.htm", b'"InterimDuration'), ("XBRLData/Attachment/sub/b-ixbrl.htm", b'y ' + mark + b'x')])
        r = MS.rewrite_zip(zc)
        eqp(out, u"ぶつかる(2 つ目の member にだけ。%s)" % mark.decode("ascii"), (r[0] == zc, r[1], r[2]), (True, True, [0, 0, 0]))
    # 印が wrap の入れない member(サマリー・文の元の file)に在るだけならぶつからない
    for nm in ("XBRLData/Summary/tse-x-1-ixbrl.htm", "XBRLData/Attachment/qualitative.htm"):
        zc = make_zip([("XBRLData/Attachment/a-ixbrl.htm", b'"InterimDuration'), (nm, b'"CurrentYearDuration')])
        r = MS.rewrite_zip(zc)
        eqp(out, u"印が入れない member(%s)に在るだけ" % nm, (r[1], r[2], zipfile.ZipFile(io.BytesIO(r[0])).read("XBRLData/Attachment/a-ixbrl.htm")), (False, [0, 1, 0], b'"CurrentYearDuration'))
    try:
        MS.rewrite_zip(b"not a zip")
        out.append(u"ZIP でない bytes で止まらない")
    except SystemExit:
        pass
    # prepare
    eqp(out, u"prepare(写さない)は ZIP をそのまま", MS.prepare(zb, False), (zb, False, [0, 0, 0]))
    eqp(out, u"prepare(写す)", MS.prepare(zb, True)[1:], (False, [1, 4, 1]))
    # judge2
    sha = u"a" * 64
    ziz = izip(SENTS4)
    b0, z0 = MS.judge2(1, u"丙", u"scedjpsm", sha, ziz, False)
    b1, z1 = MS.judge2(1, u"丙", u"scedjpsm", sha, ziz, True)
    eqp(out, u"写さない判定は TSS の judge_book と同じ(+ 3 つの欄)", json.loads(json.dumps(dict((k, v) for k, v in b0.items() if k not in (u"名前がぶつかる", u"写した", u"置き換えた回数")))),
        json.loads(json.dumps(TSS.judge_book(1, u"丙", u"scedjpsm", sha, ziz))))
    eqp(out, u"写さない本の 3 つの欄", (b0[u"名前がぶつかる"], b0[u"写した"], b0[u"置き換えた回数"], z0 is ziz), (False, False, [0, 0, 0], True))
    eqp(out, u"写した本の 3 つの欄", (b1[u"名前がぶつかる"], b1[u"写した"], b1[u"置き換えた回数"]), (False, True, [2, 2, 0]))
    eqp(out, u"写した行の state", [r[2] for r in b1[u"行"]], [u"GROUNDED", u"VALUE_MISMATCH", u"VALUE_MISMATCH", u"VALUE_MISMATCH"])
    eqp(out, u"写さない行の state", [r[2] for r in b0[u"行"]], [u"GROUNDED", u"POINTER_NOT_FOUND", u"POINTER_NOT_FOUND", u"POINTER_NOT_FOUND"])
    eqp(out, u"欄の順", list(b1)[-3:], [u"名前がぶつかる", u"写した", u"置き換えた回数"])
    zcol = izip(SENTS4[1:2], ix=IX_I.replace(u"</body>", COLLIDE + u"</body>"))
    bc, zc2 = MS.judge2(2, u"丙", u"scedjpsm", sha, zcol, True)
    eqp(out, u"ぶつかる本は写さない", (bc[u"名前がぶつかる"], bc[u"写した"], bc[u"置き換えた回数"], zc2 is zcol, [r[2] for r in bc[u"行"]]), (True, False, [0, 0, 0], True, [u"POINTER_NOT_FOUND"]))
    bn, _ = MS.judge2(3, u"丙", u"scedjpsm", sha, izip(SENTS4, with_q=False), True)
    eqp(out, u"切れない本は写した数に入れない", (bn[u"切り出し"], bn[u"名前がぶつかる"], bn[u"写した"], bn[u"置き換えた回数"]), (u"切れない", False, False, [0, 0, 0]))
    # 文の block は TSS のまま・添付の member は置き換えだけが違う
    text = MS.TSS.cut(ziz)[0]
    w_orig, _n = MS.TSS.wrap(ziz, text)
    w_new, _n = MS.TSS.wrap(z1, text)
    zo, zn = zipfile.ZipFile(io.BytesIO(w_orig)), zipfile.ZipFile(io.BytesIO(w_new))
    eqp(out, u"包み直しの名前は同じ・文の block は byte で同じ", (zo.namelist() == zn.namelist(), zo.read(MS.TSS.OVERVIEW_MEMBER) == zn.read(MS.TSS.OVERVIEW_MEMBER)), (True, True))
    att = "XBRL/PublicDoc/0200000_ixbrl.htm"
    manual = zo.read(att)
    for old_b, new_b in SEALED_REPLACEMENTS:
        manual = manual.replace(old_b, new_b)
    eqp(out, u"添付の byte 列は置き換えの分だけ違う", (zo.read(att) == zn.read(att), zn.read(att) == manual), (False, True))
    return out


def moves_problems():
    u"""``moves``: 4 × 4 の遷移・動いた行・GROUNDED でなくなった行・片方にしか無い行・切り出しが違えば止まる。"""
    out = []

    def book(n, cut, rows):
        return {u"#": n, u"切り出し": cut, u"行": [[r[0], r[1], r[2]] for r in rows]}
    G_, V_, U_, P_ = u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND"
    old = {1: book(1, u"切れた", [(1, 1, G_), (1, 2, P_), (2, 1, P_), (2, 2, U_), (3, 1, G_)]), 2: book(2, u"切れた", [(1, 1, V_)]), 3: book(3, u"切れない", [])}
    new = [book(1, u"切れた", [(1, 1, G_), (1, 2, V_), (2, 1, G_), (2, 2, U_), (9, 9, G_)]), book(3, u"切れない", [])]
    m = MS.moves(old, new)
    t = m[u"行(写す前 → 写した後)"]
    eqp(out, u"遷移", [[t[s][u] for u in MS.STATES] for s in MS.STATES], [[1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 1, 0], [1, 1, 0, 0]])
    eqp(out, u"動いた行・GROUNDED でなくなった行・片方にしか無い行", (m[u"動いた行"], m[u"GROUNDED だった行のうち GROUNDED でなくなった行"], m[u"写す前にだけ在る行"], m[u"写した後にだけ在る行"]), (2, 0, 1, 1))
    new2 = [book(1, u"切れた", [(1, 1, P_), (1, 2, P_), (2, 1, P_), (2, 2, U_), (3, 1, G_)])]
    m2 = MS.moves(old, new2)
    eqp(out, u"GROUNDED でなくなった行", (m2[u"GROUNDED だった行のうち GROUNDED でなくなった行"], m2[u"動いた行"]), (1, 1))
    expect_stop(out, u"切り出しの結果が違う", lambda: MS.moves(old, [book(1, u"切れない", [])]))
    return out


def interim_problems():
    u"""run_interim: 記録の形・集計・4 × 4・名前がぶつかる本は写さない・文を持たない・2 回(procs 違い)で byte が同じ(時間を除く)・止める所。"""
    out = []
    with tmpdir() as d:
        pop, mat, root, zips, tss = fixture5(d)
        kw = kw5(root, pop, mat, tss)
        p1 = os.path.join(d, "o", "i1.json")
        ticks = iter([10.0, 13.5])
        rec = MS.run_interim(procs=1, out=p1, clock=lambda: next(ticks), **kw)
        text = open(p1, encoding="utf-8").read()
        eqp(out, u"返り値と file", json.loads(text), json.loads(json.dumps(rec)))
        books = rec[u"本"]
        eqp(out, u"本の順と群", [(b[u"#"], b[u"群"]) for b in books], [(3, u"丙"), (4, u"丙"), (5, u"丙")])
        eqp(out, u"本の数・ぶつかる本・写した本", (rec[u"本の数"], rec[u"名前がぶつかる本"], rec[u"名前がぶつかる本のうち切れた本"], rec[u"写した本"]), (3, 1, 1, 1))
        eqp(out, u"置き換えた回数の合計", rec[u"置き換えた回数の合計(規則 1・2・3)"], [2, 2, 0])
        eqp(out, u"本ごとの 3 つの欄", [(b[u"名前がぶつかる"], b[u"写した"], b[u"置き換えた回数"]) for b in books], [(False, True, [2, 2, 0]), (True, False, [0, 0, 0]), (False, False, [0, 0, 0])])
        g = rec[u"集計"]
        eqp(out, u"集計", (g[u"本"], g[u"切れた"], g[u"切れない"], g[u"claim"], dict(g[u"4 state"])), (3, 2, 1, 6, {u"GROUNDED": 1, u"VALUE_MISMATCH": 4, u"UNVERIFIABLE": 0, u"POINTER_NOT_FOUND": 1}))
        eqp(out, u"VALUE_MISMATCH の内訳", (g[u"VALUE_MISMATCH の内訳"][u"行"], g[u"VALUE_MISMATCH が 1 以上の本"], g[u"切れた本のうち GROUNDED が 0 の本"]), (4, 1, 1))
        m = rec[u"TSS の B(写さない)との動き"]
        eqp(out, u"遷移の表", [[m[u"行(写す前 → 写した後)"][s][t] for t in MS.STATES] for s in MS.STATES], [[1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 4, 0, 1]])
        eqp(out, u"動いた行・GROUNDED でなくなった行・片方にしか無い行", (m[u"動いた行"], m[u"GROUNDED だった行のうち GROUNDED でなくなった行"], m[u"写す前にだけ在る行"], m[u"写した後にだけ在る行"]), (4, 0, 0, 0))
        eqp(out, u"置き換えの記録", rec[u"置き換え(この順。二重引用符から始まる byte 列)"], [[a.decode("ascii"), b.decode("ascii")] for a, b in SEALED_REPLACEMENTS])
        eqp(out, u"時間は 1 つの欄", (rec[u"時間(秒)"], len(re.findall(u"時間", text))), (3.5, 1))
        eqp(out, u"記録に文・span・値・要素名の字が無い", [x in text for x in (u"売上高", u"百万円", u'"span"', u'"value"', u'"recomputed"', u"jpcrp_cor", u"1,250")], [False] * 7)
        eqp(out, u"材料の置き場の前後", (rec[u"材料"][u"置き場の一覧の前後"][u"変化なし"], rec[u"材料"][u"表と一致した ZIP"]), (True, 5))
        eqp(out, u"行の欄は TSS と同じ", rec[u"行の欄"], list(TSS.ROW_COLUMNS))
        p2 = os.path.join(d, "o", "i2.json")
        MS.run_interim(procs=2, out=p2, clock=lambda: 99.0, **kw)
        eqp(out, u"2 回(procs 違い)で byte が同じ(時間を除く)", strip_time(open(p2, encoding="utf-8").read()), strip_time(text))
        # 止める所(何も書かない)
        with patched(TS.NF, map_pool=boom):                                             # 在る出力で止まるのは材料を読む前
            expect_stop(out, u"出力が在る", lambda: MS.run_interim(out=p1, **kw))
        eqp(out, u"在る出力は変わらない", open(p1, encoding="utf-8").read(), text)
        expect_stop(out, u"--out が無い", lambda: MS.run_interim(out=None, **kw))
        for rel in MS.PRODUCTION_RELS:
            expect_stop(out, u"本番の記録を使い捨ての材料から作る(%s)" % rel, lambda rel=rel: MS.run_interim(out=os.path.join(root, rel), **kw))
            if os.path.exists(os.path.join(root, rel)):
                out.append(u"本番の記録の path に書いた")
        t2 = copy.deepcopy(tss)
        t2[3][u"切り出し"] = u"切れない"
        expect_stop(out, u"TSS の記録と切り出しの結果が違う", lambda: MS.run_interim(out=os.path.join(d, "o", "i3.json"), **dict(kw, tss_states=t2)))
        expect_stop(out, u"表の形が違う", lambda: MS.run_interim(out=os.path.join(d, "o", "i4.json"), **dict(kw, shape=(3, SHAPE5[1]))))
        with open(os.path.join(mat, pop[3][3] + ".zip"), "ab") as fh:
            fh.write(b"x")
        expect_stop(out, u"材料の sha256 が違う", lambda: MS.run_interim(out=os.path.join(d, "o", "i5.json"), **kw))
        os.remove(os.path.join(mat, pop[2][3] + ".zip"))
        expect_stop(out, u"材料が無い", lambda: MS.run_interim(out=os.path.join(d, "o", "i6.json"), **kw))
        if any(os.path.exists(os.path.join(d, "o", n)) for n in ("i3.json", "i4.json", "i5.json", "i6.json")):
            out.append(u"止まったのに記録を書いた")
    with tmpdir() as d:
        pop, mat, root, zips, tss = fixture5(d)
        snaps = iter([(4, u"a"), (4, u"b")])
        with patched(ST, names_snapshot=lambda folder: next(snaps)):
            expect_stop(out, u"材料の置き場が変わった", lambda: MS.run_interim(out=os.path.join(d, "o", "i7.json"), **kw5(root, pop, mat, tss)))
        if os.path.exists(os.path.join(d, "o", "i7.json")):
            out.append(u"材料の置き場が変わったのに記録を書いた")
    return out


def near_problems():
    u"""run_near: 近い行・規則ごとの数・A を写さない(中間の名前の A は読み替えない)・A と B の state が記録と同じ・2 回で byte が同じ・止める所。"""
    out = []
    with tmpdir() as d:
        pop, mat, root, zips, tss = fixture5(d)
        kw = kw5(root, pop, mat, tss)
        ip = os.path.join(d, "o", "i.json")
        MS.run_interim(out=ip, **kw)
        n1 = os.path.join(d, "o", "n1.json")
        ticks = iter([5.0, 7.5])
        rec = MS.run_near(procs=1, interim=ip, out=n1, clock=lambda: next(ticks), **kw)
        text = open(n1, encoding="utf-8").read()
        eqp(out, u"返り値と file", json.loads(text), json.loads(json.dumps(rec)))
        eqp(out, u"近い行(A が先・# の順・文の番号の順)", rec[u"行"], [[1, 2, 4, [u"N-円"], u"円族"], [1, 3, 4, [u"N-桁"], u"円族"], [1, 5, 4, [u"N-円"], u"円族"],
                                                      [3, 2, 4, [u"N-円"], u"円族"], [3, 3, 4, [u"N-桁"], u"円族"], [3, 5, 4, [u"N-円"], u"円族"]])
        s = rec[u"集計"]
        eqp(out, u"A の集計", dict((k, (dict(v) if isinstance(v, collections.OrderedDict) else v)) for k, v in s[u"A(甲 + 乙)"].items()),
            {u"本": 2, u"VALUE_MISMATCH の行": 4, u"うち recomputed が数でない行": 0, u"近い行": 3, u"規則ごとの行の数": {u"N-円": 2, u"N-桁": 1, u"N-率": 0},
             u"規則ごとの 1 行以上持つ本の数": {u"N-円": 1, u"N-桁": 1, u"N-率": 0}, u"近い行を 1 行以上持つ本": 1})
        eqp(out, u"B の集計", dict((k, (dict(v) if isinstance(v, collections.OrderedDict) else v)) for k, v in s[u"B(丙)"].items()),
            {u"本": 3, u"VALUE_MISMATCH の行": 4, u"うち recomputed が数でない行": 0, u"近い行": 3, u"規則ごとの行の数": {u"N-円": 2, u"N-桁": 1, u"N-率": 0},
             u"規則ごとの 1 行以上持つ本の数": {u"N-円": 1, u"N-桁": 1, u"N-率": 0}, u"近い行を 1 行以上持つ本": 1})
        eqp(out, u"A・B の state が記録と同じ", (dict(rec[u"A の state が TSS の記録と同じか"]), dict(rec[u"B の state が interim の記録と同じか"])),
            ({u"本": 2, u"行": 7, u"違う本": 0}, {u"本": 3, u"行": 6, u"違う本": 0}))
        eqp(out, u"近い行の数・読む行の数", (rec[u"近い行の数(A と B)"], rec[u"読む行の規則"][u"読む行の数"], rec[u"読む行の規則"][u"種"], rec[u"読む行の規則"][u"標本の数"]), (6, 6, 20261115, 200))
        eqp(out, u"時間は 1 つの欄", (rec[u"時間(秒)"], len(re.findall(u"時間", text))), (2.5, 1))
        eqp(out, u"行の長さ", set(len(r) for r in rec[u"行"]), set([5]))
        eqp(out, u"記録に文・span・値・要素名の字が無い", [x in text for x in (u"売上高", u"となりました", u'"span"', u'"value"', u'"recomputed"', u"jpcrp_cor", u"1,250", u"1250", u"1324")], [False] * 9)
        eqp(out, u"interim の記録の sha256 を持つ", rec[u"interim の記録の sha256"], ST.sha256_file(ip))
        n2 = os.path.join(d, "o", "n2.json")
        MS.run_near(procs=2, interim=ip, out=n2, clock=lambda: 99.0, **kw)
        eqp(out, u"2 回(procs 違い)で byte が同じ(時間を除く)", strip_time(open(n2, encoding="utf-8").read()), strip_time(text))
        # 止める所(何も書かない)
        with patched(TS.NF, map_pool=boom):                                             # 在る出力で止まるのは材料を読む前
            expect_stop(out, u"出力が在る", lambda: MS.run_near(interim=ip, out=n1, **kw))
        eqp(out, u"在る出力は変わらない", open(n1, encoding="utf-8").read(), text)
        expect_stop(out, u"--out が無い", lambda: MS.run_near(interim=ip, out=None, **kw))
        expect_stop(out, u"--interim が無い", lambda: MS.run_near(interim=None, out=os.path.join(d, "o", "x0.json"), **kw))
        expect_stop(out, u"本番の記録を使い捨ての材料から作る", lambda: MS.run_near(interim=ip, out=os.path.join(root, MS.NEAR_REL), **kw))
        t2 = copy.deepcopy(tss)
        t2[1][u"行"][1][2] = u"GROUNDED"                                              # A の 1 行の state が TSS の記録と違う
        expect_stop(out, u"A の state が TSS の記録と違う", lambda: MS.run_near(interim=ip, out=os.path.join(d, "o", "x1.json"), **dict(kw, tss_states=t2)))
        t3 = copy.deepcopy(tss)
        t3[2][u"行"][1][2] = u"VALUE_MISMATCH"                                         # 中間の名前の A を写すと動く行(A は写さないので、TSS の記録は写さない判定)
        expect_stop(out, u"A の 2 本目の state が TSS の記録と違う", lambda: MS.run_near(interim=ip, out=os.path.join(d, "o", "x1b.json"), **dict(kw, tss_states=t3)))
        ij = json.load(open(ip, encoding="utf-8"))
        ij2 = copy.deepcopy(ij)
        ij2[u"本"][0][u"行"][1][2] = u"POINTER_NOT_FOUND"                               # B の 1 行の state が interim の記録と違う
        dump_json(os.path.join(d, "o", "ij2.json"), ij2)
        expect_stop(out, u"B の state が interim の記録と違う", lambda: MS.run_near(interim=os.path.join(d, "o", "ij2.json"), out=os.path.join(d, "o", "x2.json"), **kw))
        ij3 = copy.deepcopy(ij)
        ij3[u"この script の sha256"] = u"0" * 64
        dump_json(os.path.join(d, "o", "ij3.json"), ij3)
        expect_stop(out, u"interim の記録が別の script で作られた", lambda: MS.run_near(interim=os.path.join(d, "o", "ij3.json"), out=os.path.join(d, "o", "x3.json"), **kw))
        ij4 = copy.deepcopy(ij)
        ij4[u"本"] = ij4[u"本"][:-1]
        dump_json(os.path.join(d, "o", "ij4.json"), ij4)
        expect_stop(out, u"interim の記録の本が丙と合わない", lambda: MS.run_near(interim=os.path.join(d, "o", "ij4.json"), out=os.path.join(d, "o", "x4.json"), **kw))
        with patched(MS, near_of_book=lambda zb2: (99, 0, [])):                         # 判定の行の VALUE_MISMATCH の数と claim から数えた数が違う
            expect_stop(out, u"判定の行と claim の数が違う", lambda: MS.run_near(interim=ip, out=os.path.join(d, "o", "x7.json"), **kw))
        with open(os.path.join(mat, pop[3][3] + ".zip"), "ab") as fh:
            fh.write(b"x")
        expect_stop(out, u"材料の sha256 が違う", lambda: MS.run_near(interim=ip, out=os.path.join(d, "o", "x5.json"), **kw))
        if any(os.path.exists(os.path.join(d, "o", n)) for n in ("x0.json", "x1.json", "x1b.json", "x2.json", "x3.json", "x4.json", "x5.json", "x7.json")) or os.path.exists(os.path.join(root, MS.NEAR_REL)):
            out.append(u"止まったのに記録を書いた")
    with tmpdir() as d:
        pop, mat, root, zips, tss = fixture5(d)
        ip = os.path.join(d, "o", "i.json")
        MS.run_interim(out=ip, **kw5(root, pop, mat, tss))
        snaps = iter([(4, u"a"), (4, u"b")])
        with patched(ST, names_snapshot=lambda folder: next(snaps)):
            expect_stop(out, u"材料の置き場が変わった", lambda: MS.run_near(interim=ip, out=os.path.join(d, "o", "x6.json"), **kw5(root, pop, mat, tss)))
        if os.path.exists(os.path.join(d, "o", "x6.json")):
            out.append(u"材料の置き場が変わったのに記録を書いた")
    return out


def near_book_problems():
    u"""near_of_book: recomputed が数でない VALUE_MISMATCH の行は近い行の母集団に入れずに数える。切れない本は (0, 0, [])。"""
    out = []
    zb = izip(SENTS4, ix=G1.IX)
    eqp(out, u"通期の名前の本", MS.near_of_book(zb), (3, 0, [[2, 4, [u"N-円"], u"円族"], [3, 4, [u"N-桁"], u"円族"]]))
    eqp(out, u"切れない本", MS.near_of_book(izip(SENTS4, with_q=False)), (0, 0, []))
    ordr = [u"当期の連結の売上高は1,250百万円となりました。", u"売上高は1,324百万円となりました。", u"売上高は1,234百万円となりました。"]       # 位置は 1 文目が後ろ(10)・2 文目が前(4)
    eqp(out, u"並びは文の番号が先(位置が先ではない)", MS.near_of_book(izip(ordr, ix=G1.IX))[2], [[1, 10, [u"N-円"], u"円族"], [2, 4, [u"N-桁"], u"円族"]])
    real = MS.VD.verify_document

    def fake(zb_, prof, *a, **k):
        r = real(zb_, prof, *a, **k)
        n = 0
        for c in r["claims"]:
            if c["kind"] == "num" and c["state"] == u"VALUE_MISMATCH":
                n += 1
                if n == 1:
                    c["recomputed"] = None
        return r
    with patched(MS.VD, verify_document=fake):
        eqp(out, u"recomputed が数でない行", MS.near_of_book(zb), (3, 1, [[3, 4, [u"N-桁"], u"円族"]]))
    if MS.VD.verify_document is not real:
        out.append(u"verify_document が戻っていない")
    return out


def items_problems():
    u"""near_items: 200 行以下は全部・超えたら種 20261115 で 200 行・番号の順。"""
    out = []
    for n in (500, 1000):
        rec = {u"行": [[i + 1, i, 0, [u"N-円"], u"円族"] for i in range(n)]}
        want = sorted(random.Random(20261115).sample(list(range(n)), 200))
        eqp(out, u"引き方 %d" % n, [it[1] - 1 for it in MS.near_items(rec)], want)
        eqp(out, u"番号が 1 から続く %d" % n, [it[0] for it in MS.near_items(rec)], list(range(1, 201)))
    p = [it[1] - 1 for it in MS.near_items({u"行": [[i + 1, 0, 0, [], u""] for i in range(500)]})]
    eqp(out, u"pin 500", (p[:5], p[-3:], sum(p), len(set(p))), ([0, 4, 9, 11, 12], [492, 494, 496], 49188, 200))
    p = [it[1] - 1 for it in MS.near_items({u"行": [[i + 1, 0, 0, [], u""] for i in range(1000)]})]
    eqp(out, u"pin 1000", (p[:5], p[-3:], sum(p)), ([1, 8, 18, 22, 23], [982, 991, 994], 99251))
    for n in (0, 7, 199, 200):
        eqp(out, u"200 行以下は全部 %d" % n, [it[1] for it in MS.near_items({u"行": [[i, 0, 0, [], u""] for i in range(n)]})], list(range(n)))
    eqp(out, u"201 行は引く", len(MS.near_items({u"行": [[i, 0, 0, [], u""] for i in range(201)]})), 200)
    eqp(out, u"項目の形(番号, 本の #, 文の番号, 位置)", MS.near_items({u"行": [[7, 3, 9, [u"N-円"], u"円族"]]}), [(1, 7, 3, 9)])
    return out


def sheet_problems():
    u"""run_sheet: 近い行の文・span・値・結んだ先・群・規則を紙に書く(標準出力は件数だけ)・repo の中は断る・在れば止める・記録と合わなければ止める。"""
    out = []
    with tmpdir() as d:
        pop, mat, root, zips, tss = fixture5(d)
        kw = kw5(root, pop, mat, tss)
        ip, npth = os.path.join(d, "o", "i.json"), os.path.join(d, "o", "n.json")
        MS.run_interim(out=ip, **kw)
        rec = MS.run_near(interim=ip, out=npth, **kw)
        said = []
        sheet = os.path.join(d, "paper", "sheet.txt")
        items = MS.run_sheet(npth, mat, sheet, root=root, say=said.append, population=pop)
        eqp(out, u"標本", items, [(1, 1, 2, 4), (2, 1, 3, 4), (3, 1, 5, 4), (4, 3, 2, 4), (5, 3, 3, 4), (6, 3, 5, 4)])
        text = open(sheet, encoding="utf-8").read()
        eqp(out, u"紙に文と読んだ値と結んだ先と群と規則", [x in text for x in (
            u"=== 標本 1 / 本 # 1 / 文 2 / 位置 4 ===", u"=== 標本 5 / 本 # 3 / 文 3 / 位置 4 ===", u"群: A  当たった規則: N-円", u"群: A  当たった規則: N-桁", u"群: B  当たった規則: N-円",
            u"群: B  当たった規則: N-桁", u"文: 売上高は1,250百万円となりました。", u"文: 売上高は1,324百万円となりました。", u"span: ", u"読んだ値: 1250", u"state: VALUE_MISMATCH",
            u"結んだ先: xbrl:jppfs_cor:NetSales@CurrentYearDuration", u"その値: 1234000000")], [True] * 13)
        eqp(out, u"群と規則の行は標本の見出しの直後", [x in text for x in (u"=== 標本 1 / 本 # 1 / 文 2 / 位置 4 ===\n群: A  当たった規則: N-円\n文: ", u"=== 標本 4 / 本 # 3 / 文 2 / 位置 4 ===\n群: B  当たった規則: N-円\n文: ")], [True, True])
        eqp(out, u"標準出力は件数だけ", [u"売上高" in x or u"百万円" in x for x in said] + [bool(said)], [False] * len(said) + [True])
        eqp(out, u"件数の字", said, [u"近い行 %d・読む行 %d・本 %d" % (len(rec[u"行"]), 6, 2)])
        expect_stop(out, u"紙が在る", lambda: MS.run_sheet(npth, mat, sheet, root=root, say=lambda *a: None, population=pop))
        inside = os.path.join(ROOT, "zz_sheet2_must_not_exist.txt")
        expect_stop(out, u"repo の中", lambda: MS.run_sheet(npth, mat, inside, root=root, say=lambda *a: None, population=pop))
        if os.path.exists(inside):
            out.append(u"repo の中に紙を書いた")
            os.remove(inside)
        nj = json.load(open(npth, encoding="utf-8"))
        bad = copy.deepcopy(nj)
        bad[u"行"][0][3] = [u"N-率"]                                                    # 記録の規則と測り直した規則が違う
        dump_json(os.path.join(d, "o", "bad1.json"), bad)
        bad2 = copy.deepcopy(nj)
        bad2[u"行"][1][2] = 5                                                          # 位置が違う行(測り直した claim が無い)
        dump_json(os.path.join(d, "o", "bad2.json"), bad2)
        bad3 = copy.deepcopy(nj)
        bad3[u"行"].append([1, 1, 4, [], u"円族"])                                         # GROUNDED の行(規則は空で測り直しと同じ。VALUE_MISMATCH でない)
        dump_json(os.path.join(d, "o", "bad3.json"), bad3)
        for k, label in ((1, u"規則が違う"), (2, u"位置が違う"), (3, u"state が違う")):
            expect_stop(out, u"記録と合わない(%s)" % label, lambda k=k: MS.run_sheet(os.path.join(d, "o", "bad%d.json" % k), mat, os.path.join(d, "paper", "s%d.txt" % k), root=root,
                                                                             say=lambda *a: None, population=pop))
            if os.path.exists(os.path.join(d, "paper", "s%d.txt" % k)):
                out.append(u"記録と合わないのに紙を書いた(%s)" % label)
        with open(os.path.join(mat, pop[0][3] + ".zip"), "ab") as fh:
            fh.write(b"x")
        expect_stop(out, u"材料の sha256 が違う", lambda: MS.run_sheet(npth, mat, os.path.join(d, "paper", "s9.txt"), root=root, say=lambda *a: None, population=pop))
    return out


def typed_file(d, lines):
    p = os.path.join(d, "typed.tsv")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(u"\n".join(lines) + u"\n")
    return p


def types_problems():
    u"""run_types: 型の file が読む行とそろう・型が 5 つのどれか・番号が重ならない・付けた席を書く・A と B の集計・文を持たない。"""
    out = []
    with tmpdir() as d:
        pop, mat, root, zips, tss = fixture5(d)
        kw = kw5(root, pop, mat, tss)
        ip, npth = os.path.join(d, "o", "i.json"), os.path.join(d, "o", "n.json")
        MS.run_interim(out=ip, **kw)
        MS.run_near(interim=ip, out=npth, **kw)
        k2 = dict(root=root, say=lambda *a: None, population=pop)
        o1 = os.path.join(d, "o", "t1.json")
        good = [u"1\tあ", u"2\tい", u"3\tい", u"4\tお", u"5\tう", u"6\tえ"]
        rec = MS.run_types(npth, typed_file(d, good), o1, **k2)
        text = open(o1, encoding="utf-8").read()
        eqp(out, u"返り値と file", json.loads(text), json.loads(json.dumps(rec)))
        eqp(out, u"行", rec[u"行"], [[1, 1, 2, 4, u"あ"], [2, 1, 3, 4, u"い"], [3, 1, 5, 4, u"い"], [4, 3, 2, 4, u"お"], [5, 3, 3, 4, u"う"], [6, 3, 5, 4, u"え"]])
        eqp(out, u"型の集計", [rec[u"型の集計"][k] for k in u"あいうえお"], [1, 2, 1, 1, 1])
        eqp(out, u"型の集計(A)・(B)", ([rec[u"型の集計(A)"][k] for k in u"あいうえお"], [rec[u"型の集計(B)"][k] for k in u"あいうえお"]), ([1, 2, 0, 0, 0], [0, 0, 1, 1, 1]))
        eqp(out, u"付けた席・盲検", (u"AI の席" in rec[u"型を付けた席"] and u"人は読んでいない" in rec[u"型を付けた席"], u"盲検ではない" in rec[u"盲検"]), (True, True))
        eqp(out, u"読む行の規則", (rec[u"読む行の規則"][u"種"], rec[u"読む行の規則"][u"読む行の数"], rec[u"読む行の規則"][u"近い行の数"]), (20261115, 6, 6))
        eqp(out, u"型の字", list(rec[u"型の字"]), list(u"あいうえお"))
        eqp(out, u"記録に文の字が無い", [x in text for x in (u"売上高", u"百万円", u"span", u"1,250")], [False] * 4)
        for label, lines in ((u"行が足りない", good[:1]), (u"行が多い", good + [u"7\tお"]), (u"番号が違う", good[:5] + [u"7\tえ"]),
                             (u"重なる", good + [u"1\tい"]), (u"型が 5 つの外", good[:5] + [u"6\tか"]),
                             (u"第 1 便の型(ア)は使わない", [u"1\tア"] + good[1:]), (u"TAB でない", [ln.replace(u"\t", u" ") for ln in good]),
                             (u"番号が数でない", [u"x\tあ"] + good[1:]), (u"3 列", [u"1\tあ\tx"] + good[1:])):
            o = os.path.join(d, "o", "bad_%d.json" % abs(hash(label)))
            expect_stop(out, label, lambda lines=lines, o=o: MS.run_types(npth, typed_file(d, lines), o, **k2))
            if os.path.exists(o):
                out.append(u"%s: 止まったのに記録を書いた" % label)
        with patched(MS, read_typed=boom):                                              # 在る出力で止まるのは型の file を読む前
            expect_stop(out, u"出力が在る", lambda: MS.run_types(npth, typed_file(d, good), o1, **k2))
    return out


def population_problems():
    u"""load_population(TSS の記録の行を TSS の封の表と行ごとに比べる)・load_tss_states(本の sha256 を母集団と比べる)・material_dir・check_clean。"""
    out = []
    pop = MS.load_population(ROOT)
    eqp(out, u"本番の母集団は 400 行で封の表と同じ", (len(pop), [tuple(r) for r in pop] == [tuple(r) for r in ST.read_population(ROOT)]), (400, True))
    with tmpdir() as d:
        for rel in (ST.POPULATION_REL, ST.SEAL_REL, MS.TSS_STATES_REL):
            os.makedirs(os.path.join(d, os.path.dirname(rel)), exist_ok=True)
            with open(os.path.join(ROOT, rel), "rb") as fi, open(os.path.join(d, rel), "wb") as fo:
                fo.write(fi.read())
        eqp(out, u"写した root でも通る", len(MS.load_population(d)), 400)
        books = MS.load_tss_states(d, MS.load_population(d))
        eqp(out, u"TSS の判定の記録の本", (len(books), sorted(books)[:3]), (400, [1, 2, 3]))
        rec = json.load(open(os.path.join(d, ST.POPULATION_REL), encoding="utf-8"))
        rec[u"行"][5][3] = rec[u"行"][5][3][:-1] + (u"0" if rec[u"行"][5][3][-1] != u"0" else u"1")           # 記録の sha256 が 1 字違う
        dump_json(os.path.join(d, ST.POPULATION_REL), rec)
        expect_stop(out, u"記録の sha256 が 1 字違う", lambda: MS.load_population(d))
        rec2 = json.load(open(os.path.join(ROOT, ST.POPULATION_REL), encoding="utf-8"))
        rec2[u"行"][5][1] = u"乙"                                                       # 群が違う(本数も変わる)
        dump_json(os.path.join(d, ST.POPULATION_REL), rec2)
        expect_stop(out, u"記録の群が違う", lambda: MS.load_population(d))
        rec3 = json.load(open(os.path.join(ROOT, ST.POPULATION_REL), encoding="utf-8"))
        rec3[u"行"][5], rec3[u"行"][6] = rec3[u"行"][6], rec3[u"行"][5]                       # 行の順が違う(番号が飛ぶ)
        dump_json(os.path.join(d, ST.POPULATION_REL), rec3)
        expect_stop(out, u"記録の行の順が違う", lambda: MS.load_population(d))
        rec4 = json.load(open(os.path.join(ROOT, ST.POPULATION_REL), encoding="utf-8"))
        rec4[u"行"][5][2] = u"acedjpsm" if rec4[u"行"][5][2] != u"acedjpsm" else u"acedifsm"       # 様式の種類が表と違う
        dump_json(os.path.join(d, ST.POPULATION_REL), rec4)
        expect_stop(out, u"記録の様式の種類が表と違う", lambda: MS.load_population(d))
        st = json.load(open(os.path.join(d, MS.TSS_STATES_REL), encoding="utf-8"))
        st[u"本"][3][u"ZIP の sha256"] = u"0" * 64
        dump_json(os.path.join(d, "bad_states.json"), st)
        expect_stop(out, u"TSS の判定の記録の本の sha256 が母集団と違う", lambda: MS.load_tss_states(d, pop, os.path.join(d, "bad_states.json")))
        st2 = json.load(open(os.path.join(d, MS.TSS_STATES_REL), encoding="utf-8"))
        st2[u"本"] = st2[u"本"][:-1]
        dump_json(os.path.join(d, "bad_states2.json"), st2)
        expect_stop(out, u"TSS の判定の記録の本が足りない", lambda: MS.load_tss_states(d, pop, os.path.join(d, "bad_states2.json")))
    # material_dir
    prod = os.path.abspath(ST.default_cache_dir())
    eqp(out, u"既定は本番の folder", MS.material_dir(None, os.path.join(ROOT, "x.json")), (prod, True))
    eqp(out, u"使い捨ての材料で本番でない path に書く", MS.material_dir("/tmp/zz", os.path.join("/tmp", "x.json")), (os.path.abspath("/tmp/zz"), False))
    for rel in RECORD_RELS[:2]:
        expect_stop(out, u"本番の記録の path に使い捨ての材料(%s)" % rel, lambda rel=rel: MS.material_dir("/tmp/zz", os.path.join(ROOT, rel)))
        eqp(out, u"本番の記録の path に本番の材料(%s)" % rel, MS.material_dir(None, os.path.join(ROOT, rel)), (prod, True))
    return out


def clean_problems():
    u"""記録に repo へ入れない欄・鍵らしい字が在れば止まる。封の path は長い英数字だが鍵に数えない。"""
    out = []
    ok = collections.OrderedDict([(u"seal", MS.SEAL_REL), (u"x", TSS_SEAL_REL), (u"本", [{u"行": [[1, 2]]}])])
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
    u"""check_clean が run_interim・run_near・run_types の各々から呼ばれる(正常な記録では発火しない守りなので、止める故障を差し込んで各 run が止まり何も書かないことを見る)。"""
    out = []
    with tmpdir() as d:
        pop, mat, root, zips, tss = fixture5(d)
        kw = kw5(root, pop, mat, tss)
        ip, npth = os.path.join(d, "o", "i.json"), os.path.join(d, "o", "n.json")
        MS.run_interim(out=ip, **kw)
        MS.run_near(interim=ip, out=npth, **kw)
        typed = typed_file(d, [u"1\tあ", u"2\tい", u"3\tい", u"4\tお", u"5\tう", u"6\tえ"])
        k2 = dict(root=root, say=lambda *a: None, population=pop)
        calls = []

        def faulty(rec, text, key_value=None):
            calls.append(1)
            raise MS.Stop(u"差し込んだ故障")
        jobs = ((u"run_interim", os.path.join(d, "o", "wi.json"), lambda o: MS.run_interim(out=o, **kw)),
                (u"run_near", os.path.join(d, "o", "wn.json"), lambda o: MS.run_near(interim=ip, out=o, **kw)),
                (u"run_types", os.path.join(d, "o", "wt.json"), lambda o: MS.run_types(npth, typed, o, **k2)))
        for name, o, job in jobs:
            del calls[:]
            with patched(MS, check_clean=faulty):
                expect_stop(out, u"%s が check_clean を呼ばない" % name, lambda: job(o))
            eqp(out, u"%s は check_clean を 1 回呼ぶ" % name, calls, [1])
            if os.path.exists(o):
                out.append(u"%s: check_clean が止めたのに記録を書いた" % name)
    return out


# ================================================================ 変異の表(約束の側から。関数の字を 1 か所替えた版を差し込み、検査が赤になることを見る)
def _m(label, mod, fn, old, new, check):
    return (label, mod, fn, old, new, check)


MUTANTS = (
    # 近い行の規則
    _m(u"N-円: ちょうど 2% を外す(< にする)", MS, "near_rules", u"abs(c - f) <= f * YEN_BAND", u"abs(c - f) < f * YEN_BAND", rules_problems),
    _m(u"N-円: 差 0 を通す", MS, "near_rules", u"c != f and ", u"", rules_problems),
    _m(u"N-円: 倍率を掛けない", MS, "near_rules", u"c, f = abs(v) * m, abs(r)", u"c, f = abs(v), abs(r)", rules_problems),
    _m(u"N-円: v の符号を見る", MS, "near_rules", u"c, f = abs(v) * m, abs(r)", u"c, f = v * m, abs(r)", rules_problems),
    _m(u"N-円: r の符号を見る", MS, "near_rules", u"c, f = abs(v) * m, abs(r)", u"c, f = abs(v) * m, r", rules_problems),
    _m(u"N-円: 分母が c", MS, "near_rules", u"abs(c - f) <= f * YEN_BAND", u"abs(c - f) <= c * YEN_BAND", rules_problems),
    _m(u"N-円: float で比べる(0.0357 千円 対 35.0 が外れる)", MS, "near_rules", u"c, f = abs(v) * m, abs(r)", u"c, f = float(abs(v)) * m, float(abs(r))", rules_problems),
    _m(u"N-円: 数を 2 進の値で厳密に見る", MS, "exact", u"return Fraction(repr(x))", u"return Fraction(x)", rules_problems),
    _m(u"N-円: 数を float にする", MS, "exact", u"return Fraction(repr(x))", u"return float(x)", rules_problems),
    _m(u"N-円: 単位が % でも倍率 1 で見る", MS, "near_rules", u"    m = YEN_UNITS.get(unit)", u"    m = YEN_UNITS.get(unit, 1)", rules_problems),
    _m(u"N-桁: form を見ない", MS, "near_rules", u"if form == u\"direct_value\" and v.denominator == 1:", u"if v.denominator == 1:", rules_problems),
    _m(u"N-桁: 整数かを見ない", MS, "near_rules", u"if form == u\"direct_value\" and v.denominator == 1:", u"if form == u\"direct_value\":", rules_problems),
    _m(u"N-桁: floor の b を見ない", MS, "near_rules", u"if digits_close(a, floor_b) or digits_close(a, half_b):", u"if digits_close(a, half_b):", rules_problems),
    _m(u"N-桁: 四捨五入の b を見ない", MS, "near_rules", u"if digits_close(a, floor_b) or digits_close(a, half_b):", u"if digits_close(a, floor_b):", rules_problems),
    _m(u"N-桁: 四捨五入が銀行丸め", MS, "near_rules", u"half = fm + Fraction(1, 2)\n            half_b = u\"%d\" % (half.numerator // half.denominator)", u"half = Fraction(round(fm))\n            half_b = u\"%d\" % (half.numerator // half.denominator)", rules_problems),
    _m(u"N-桁: 四捨五入が 0.5 を切り捨てる", MS, "near_rules", u"half = fm + Fraction(1, 2)", u"half = fm + Fraction(49, 100)", rules_problems),
    _m(u"N-桁: 倍率で割らない", MS, "near_rules", u"fm = f / m", u"fm = f", rules_problems),
    _m(u"N-桁: a が |v| でない", MS, "near_rules", u"a = u\"%d\" % abs(int(v))", u"a = u\"%d\" % int(v)", rules_problems),
    _m(u"digits: 桁数の下限を外す", MS, "digits_close", u" or len(a) < MIN_DIGITS", u"", rules_problems),
    _m(u"digits: 桁数が同じかを見ない", MS, "digits_close", u"if len(a) != len(b) or ", u"if ", rules_problems),
    _m(u"digits: 1 桁違いを通さない", MS, "digits_close", u"    if len(diff) == 1:\n        return True\n", u"", rules_problems),
    _m(u"digits: 2 桁違いなら何でも通す", MS, "digits_close", u"len(diff) == 2 and diff[1] == diff[0] + 1 and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]", u"len(diff) == 2", rules_problems),
    _m(u"digits: となり合うかを見ない", MS, "digits_close", u"len(diff) == 2 and diff[1] == diff[0] + 1 and ", u"len(diff) == 2 and ", rules_problems),
    _m(u"digits: 入れ替わりの片側だけ見る", MS, "digits_close", u" and a[diff[1]] == b[diff[0]]", u"", rules_problems),
    _m(u"N-率: ポイントも入れる", MS, "near_rules", u"    if unit == u\"%\":", u"    if unit in (u\"%\", u\"ポイント\"):", rules_problems),
    _m(u"N-率: ちょうど 0.5 を外す(< にする)", MS, "near_rules", u"if 0 < d <= PCT_BAND:", u"if 0 < d < PCT_BAND:", rules_problems),
    _m(u"N-率: derived_value の行だけに限る", MS, "near_rules", u"    if unit == u\"%\":", u"    if unit == u\"%\" and form == u\"derived_value\":", rules_problems),
    _m(u"N-率: 差 0 を通す", MS, "near_rules", u"if 0 < d <= PCT_BAND:", u"if d <= PCT_BAND:", rules_problems),
    _m(u"N-率: 符号を除かない", MS, "near_rules", u"d = abs(abs(v) - abs(r))", u"d = abs(v - r)", rules_problems),
    _m(u"N-率: 差が float", MS, "near_rules", u"d = abs(abs(v) - abs(r))", u"d = Fraction(abs(float(v) - float(r)))", rules_problems),
    _m(u"数: bool を数にする", MS, "is_number", u"if isinstance(x, bool) or not isinstance(x, (int, float)):", u"if not isinstance(x, (int, float)):", rules_problems),
    _m(u"数: nan・inf を数にする", MS, "is_number", u"return isinstance(x, int) or math.isfinite(x)", u"return True", rules_problems),
    _m(u"数: recomputed が数かを見ない", MS, "near_rules", u"if not is_number(value) or not is_number(recomputed):", u"if not is_number(value):", rules_problems),
    _m(u"数: value が数かを見ない", MS, "near_rules", u"if not is_number(value) or not is_number(recomputed):", u"if not is_number(recomputed):", rules_problems),
    # 置き換え
    _m(u"置き換え: ぶつかる本も写す", MS, "rewrite_zip", u"    if any(collides(d) for nm, d in members if is_wrapped_member(nm)):", u"    if False:", replace_problems),
    _m(u"置き換え: ぶつかりの判定を最初の wrapped member だけに掛ける", MS, "rewrite_zip", u"    if any(collides(d) for nm, d in members if is_wrapped_member(nm)):",
       u"    if any(collides(d) for nm, d in [(nm, d) for nm, d in members if is_wrapped_member(nm)][:1]):", replace_problems),
    _m(u"置き換え: ぶつかりを入れない member でも見る", MS, "rewrite_zip", u"    if any(collides(d) for nm, d in members if is_wrapped_member(nm)):", u"    if any(collides(d) for nm, d in members):", replace_problems),
    _m(u"置き換え: 入れない member(サマリー・文の元の file)にも掛ける", MS, "rewrite_zip", u"            if is_wrapped_member(nm):", u"            if True:", replace_problems),
    _m(u"置き換え: 最初の 1 か所だけ置き換える", MS, "rewrite_zip", u"                    d = d.replace(old, new)", u"                    d = d.replace(old, new, 1)", replace_problems),
    _m(u"置き換え: 当たった回数を数えない", MS, "rewrite_zip", u"                    counts[k] += d.count(old)", u"                    pass", replace_problems),
    _m(u"置き換え: member の順を変える", MS, "rewrite_zip", u"        for nm, d in members:", u"        for nm, d in reversed(members):", replace_problems),
    _m(u"置き換え: member の名前を変える", MS, "rewrite_zip", u"zipfile.ZipInfo(nm, date_time=TSS.ZIP_DATE_TIME)", u"zipfile.ZipInfo(nm + u\"x\", date_time=TSS.ZIP_DATE_TIME)", replace_problems),
    _m(u"置き換え: ぶつかりの印を 2 つだけ見る", MS, "collides", u"for m in COLLISION_MARKS)", u"for m in COLLISION_MARKS[:2])", replace_problems),
    _m(u"置き換え: wrap の入れる member を Attachment の外にも広げる", MS, "is_wrapped_member", u"name.startswith(TSS.ATTACH_PREFIX) and ", u"", replace_problems),
    _m(u"置き換え: wrap の入れる member を .htm 全部にする", MS, "is_wrapped_member", u"base.endswith(TSS.OLD_SUFFIX)", u"base.endswith(u\".htm\")", replace_problems),
    _m(u"置き換え: 写さない判定でも置き換える", MS, "prepare", u"    if not replace:", u"    if False:", replace_problems),
    _m(u"置き換え: 判定に置き換え前の ZIP を渡す", MS, "judge2", u"    book = TSS.judge_book(n, grp, kind, sha, zb2)", u"    book = TSS.judge_book(n, grp, kind, sha, zb)", replace_problems),
    _m(u"置き換え: 写した = ぶつかっても真", MS, "judge2", u"bool(replace and not hit and ", u"bool(replace and ", replace_problems),
    _m(u"置き換え: 写した = 写さない判定でも真", MS, "judge2", u"bool(replace and not hit and ", u"bool(not hit and ", replace_problems),
    _m(u"置き換え: 写した = 切れない本でも真", MS, "judge2", u"bool(replace and not hit and book[u\"切り出し\"] == TSS.CUT_OK)", u"bool(replace and not hit)", replace_problems),
    _m(u"置き換え: 回数を写さない本にも持たせる", MS, "judge2", u"counts if book[u\"写した\"] else [0] * len(REPLACEMENTS)", u"counts", replace_problems),
    _m(u"置き換え: ぶつかるかを書かない", MS, "judge2", u"book[u\"名前がぶつかる\"] = hit", u"book[u\"名前がぶつかる\"] = False", replace_problems),
    _m(u"置き換え: 置き換えを掛けた ZIP を捨てる", MS, "rewrite_zip", u"    return buf.getvalue(), False, counts", u"    return zb, False, counts", replace_problems),
    _m(u"置き換え: ZIP でなくても止めない", MS, "rewrite_zip", u"raise Stop(u\"**ZIP として読めない。止める**\")", u"return zb, True, [0, 0, 0]", replace_problems),
    # moves・interim
    _m(u"moves: 遷移の向きが逆", MS, "moves", u"table[s][nrow[k]] += 1", u"table[nrow[k]][s] += 1", moves_problems),
    _m(u"moves: 動いた行が対角", MS, "moves", u"if s != t)", u"if s == t)", moves_problems),
    _m(u"moves: GROUNDED でなくなった行が GROUNDED のまま", MS, "moves", u"for t in STATES if t != G)", u"for t in STATES if t == G)", moves_problems),
    _m(u"moves: 切り出しの違いで止めない", MS, "moves", u"        if o[u\"切り出し\"] != b[u\"切り出し\"]:", u"        if False:", moves_problems),
    _m(u"moves: 写す前にだけ在る行を数えない", MS, "moves", u"                only_old += 1", u"                pass", moves_problems),
    _m(u"moves: 写した後にだけ在る行を数えない", MS, "moves", u"        only_new += sum(1 for k in nrow if k not in orow)", u"        pass", moves_problems),
    _m(u"interim: 丙でない本も判定する", MS, "run_interim", u"sel = [r for r in pop if r[1] in INTERIM_GROUPS]", u"sel = list(pop)", interim_problems),
    _m(u"interim: 材料の置き場が変わっても止めない", MS, "run_interim", u"    if before != after:", u"    if False:", interim_problems),
    _m(u"interim: 本番の記録を使い捨ての材料で作る", MS, "material_dir", u"if os.path.abspath(out) in [", u"if False and os.path.abspath(out) in [", interim_problems),
    _m(u"interim: 本番の記録の guard が interim だけ", MS, "material_dir", u"for rel in PRODUCTION_RELS]", u"for rel in PRODUCTION_RELS[:1]]", interim_problems),
    _m(u"interim: 材料の sha256 を見ない", MS, "read_material", u"    if ST.sha256_bytes(zb) != sha:", u"    if False:", interim_problems),
    _m(u"interim: 時間を測らない", MS, "run_interim", u"    elapsed = clock() - t0", u"    elapsed = 0.0", interim_problems),
    _m(u"interim: ぶつかる本の数を数えない", MS, "run_interim", u"rec[u\"名前がぶつかる本\"] = sum(1 for b in books if b[u\"名前がぶつかる\"])", u"rec[u\"名前がぶつかる本\"] = 0", interim_problems),
    _m(u"interim: 写した本の数が切れた本", MS, "run_interim", u"rec[u\"写した本\"] = sum(1 for b in books if b[u\"写した\"])", u"rec[u\"写した本\"] = sum(1 for b in books if b[u\"切り出し\"] == TSS.CUT_OK)", interim_problems),
    _m(u"interim: 出力が在っても書く", MS, "run_interim", u"    if os.path.exists(out):", u"    if False:", interim_problems),
    _m(u"interim: 動きの表を別の記録(写した判定どうし)と比べる", MS, "run_interim", u"rec[u\"TSS の B(写さない)との動き\"] = moves(tss_books, books)", u"rec[u\"TSS の B(写さない)との動き\"] = moves(dict((b[u\"#\"], b) for b in books), books)", interim_problems),
    _m(u"記録: 鍵らしい字を見ない", MS, "check_clean", u"    if leaks:", u"    if False:", clean_problems),
    _m(u"記録: 欄の禁止を見ない", MS, "check_clean", u"    if bad:", u"    if False:", clean_problems),
    _m(u"記録: 封の path を外さず見る", MS, "check_clean", u"text.replace(SEAL_REL, u\"\").replace(TSS_SEAL_REL, u\"\")", u"text", clean_problems),
    _m(u"記録: run_interim が check_clean を呼ばない", MS, "run_interim", u"    check_clean(rec, text, key_value)\n", u"    pass\n", clean_wiring_problems),
    _m(u"記録: run_near が check_clean を呼ばない", MS, "run_near", u"    check_clean(rec, text, key_value)\n", u"    pass\n", clean_wiring_problems),
    _m(u"記録: run_types が check_clean を呼ばない", MS, "run_types", u"    check_clean(rec, text, key_value)\n", u"    pass\n", clean_wiring_problems),
    # 母集団・TSS の記録
    _m(u"母集団: 封の表と比べない", MS, "load_population", u"    if [tuple(r) for r in pop] != [tuple(r) for r in ST.read_population(root)]:", u"    if False:", population_problems),
    _m(u"TSS の記録: 本の sha256 を母集団と比べない", MS, "load_tss_states", u"or any(books[r[0]][u\"ZIP の sha256\"] != r[3] for r in pop)", u"", population_problems),
    _m(u"TSS の記録: 本の数を見ない", MS, "load_tss_states", u"if sorted(books) != [r[0] for r in pop]", u"if False", population_problems),
    # near
    _m(u"near: A の state が TSS の記録と違っても止めない", MS, "same_states", u"        if triples(b) != [tuple(t) for t in triples(ref[n])]:", u"        if False:", near_problems),
    _m(u"near: 違う本の数え方が逆", MS, "same_states", u"        if triples(b) != [tuple(t) for t in triples(ref[n])]:", u"        if triples(b) == [tuple(t) for t in triples(ref[n])]:", near_problems),
    _m(u"near: A の確かめだけで B を見ない", MS, "run_near", u"if a_same[u\"違う本\"] or b_same[u\"違う本\"]:", u"if a_same[u\"違う本\"]:", near_problems),
    _m(u"near: B の確かめだけで A を見ない", MS, "run_near", u"if a_same[u\"違う本\"] or b_same[u\"違う本\"]:", u"if b_same[u\"違う本\"]:", near_problems),
    _m(u"near: interim の記録の script の違いで止めない", MS, "run_near", u"    if irec.get(u\"この script の sha256\") != ST.sha256_file(os.path.abspath(__file__)):", u"    if False:", near_problems),
    _m(u"near: interim の記録の本が丙と違っても止めない", MS, "run_near", u"    if sorted(ibooks) != [r[0] for r in pop if r[1] in B_GROUPS]:", u"    if False:", near_problems),
    _m(u"near: A も写す", MS, "near_job", u"grp in B_GROUPS)", u"True)", near_problems),
    _m(u"near: B を写さない", MS, "near_job", u"grp in B_GROUPS)", u"False)", near_problems),
    _m(u"near: 判定の行と claim の数が違っても止めない", MS, "near_job", u"    if rows_vm != vm:", u"    if False:", near_problems),
    _m(u"near: 材料の置き場が変わっても止めない", MS, "run_near", u"    if before != after:", u"    if False:", near_problems),
    _m(u"near: 本番の記録の guard を外す", MS, "material_dir", u"if os.path.abspath(out) in [", u"if False and os.path.abspath(out) in [", near_problems),
    _m(u"near: 出力が在っても書く", MS, "run_near", u"    if os.path.exists(out):", u"    if False:", near_problems),
    _m(u"near: 近い行の並びが # の逆", MS, "run_near", u"for n in sorted(near_by)", u"for n in sorted(near_by, reverse=True)", near_problems),
    _m(u"near: 規則ごとの行の数が本の数", MS, "group_block", u"per_rule = collections.OrderedDict((k, sum(1 for _n, r in rows if k in r[2])) for k in RULES)", u"per_rule = collections.OrderedDict((k, len(set(n for n, r in rows if k in r[2]))) for k in RULES)", near_problems),
    _m(u"near: 規則ごとの本の数が行の数", MS, "group_block", u"per_rule_books = collections.OrderedDict((k, len(set(n for n, r in rows if k in r[2]))) for k in RULES)", u"per_rule_books = collections.OrderedDict((k, sum(1 for _n, r in rows if k in r[2])) for k in RULES)", near_problems),
    _m(u"near: 近い行を持つ本の数が行の数", MS, "group_block", u"(u\"近い行を 1 行以上持つ本\", len(set(n for n, _r in rows)))", u"(u\"近い行を 1 行以上持つ本\", len(rows))", near_problems),
    _m(u"near: 時間を測らない", MS, "run_near", u"    elapsed = clock() - t0", u"    elapsed = 0.0", near_problems),
    _m(u"near: VALUE_MISMATCH 以外も近い行にする", MS, "near_of_book", u"if c[\"kind\"] != \"num\" or c[\"state\"] != VM:", u"if c[\"kind\"] != \"num\":", near_book_problems),
    _m(u"near: recomputed が数でない行を数えない", MS, "near_of_book", u"            nonnum += 1\n", u"            pass\n", near_book_problems),
    _m(u"near: 切れない本を数える", MS, "near_of_book", u"    if text is None:\n        return 0, 0, []", u"    if text is None:\n        return 0, 0, [[0, 0, [u\"N-円\"], u\"円族\"]]", near_book_problems),
    _m(u"near: 並びの鍵が位置が先", MS, "near_of_book", u"key=lambda x: (x[0], x[1])", u"key=lambda x: (x[1], x[0])", near_book_problems),
    _m(u"near: 近い行の並びを整えない", MS, "near_of_book", u"return vm, nonnum, sorted(rows, key=lambda x: (x[0], x[1]))", u"return vm, nonnum, list(reversed(rows))", near_book_problems),
    _m(u"near: 読む行の引き方の種が違う", MS, "near_items", u"seed=SAMPLE_SEED", u"seed=SAMPLE_SEED + 1", items_problems),
    _m(u"near: 読む行の数が違う", MS, "near_items", u"k=SAMPLE_N", u"k=SAMPLE_N - 1", items_problems),
    _m(u"near: 読む行の番号が 0 から", MS, "near_items", u"(i + 1, rows[j][0]", u"(i, rows[j][0]", items_problems),
    _m(u"near: 読む行を番号の順にしない", MS, "near_items", u"picked = TSS.pick_sample(len(rows), seed=SAMPLE_SEED, k=SAMPLE_N)", u"picked = TSS.pick_sample(len(rows), seed=SAMPLE_SEED, k=SAMPLE_N)[::-1]", items_problems),
    # sheet・types
    _m(u"紙: repo の中でも書く", MS, "run_sheet", u"    if TSS.inside_repo(sheet, repo):", u"    if False:", sheet_problems),
    _m(u"紙: 在っても書く", MS, "run_sheet", u"    if os.path.exists(sheet):", u"    if False:", sheet_problems),
    _m(u"紙: 記録の規則と違っても通す", MS, "run_sheet", u" or near_rules(c[\"value\"], c[\"unit\"], c[\"form\"], c.get(\"recomputed\")) != want:", u":", sheet_problems),
    _m(u"紙: state が違っても通す", MS, "run_sheet", u"c is None or c[\"state\"] != VM or", u"c is None or", sheet_problems),
    _m(u"紙: 群の字が逆", MS, "run_sheet", u"u\"A\" if grp in A_GROUPS else u\"B\"", u"u\"B\" if grp in A_GROUPS else u\"A\"", sheet_problems),
    _m(u"紙: B を写さずに測り直す", MS, "run_sheet", u"prepare(zb, grp in B_GROUPS)", u"prepare(zb, False)", sheet_problems),
    _m(u"紙: 材料の sha256 を見ない", MS, "read_material", u"    if ST.sha256_bytes(zb) != sha:", u"    if False:", sheet_problems),
    _m(u"型: 標本と型の番号がそろわなくても通す", MS, "run_types", u"    if sorted(typed) != [it[0] for it in items]:", u"    if False:", types_problems),
    _m(u"型: 5 つの外の字を通す", MS, "read_typed", u" or parts[1] not in TYPES", u"", types_problems),
    _m(u"型: 列の数を見ない", MS, "read_typed", u"len(parts) != 2 or ", u"", types_problems),
    _m(u"型: 同じ番号を通す", MS, "read_typed", u"            if k in out:", u"            if False:", types_problems),
    _m(u"型: 付けた席を書かない", MS, "run_types", u"rec[u\"型を付けた席\"] = TYPED_BY", u"rec[u\"型を付けた席\"] = u\"人\"", types_problems),
    _m(u"型: 出力が在っても書く", MS, "run_types", u"    if os.path.exists(out):", u"    if False:", types_problems),
    _m(u"型: A と B の集計が逆", MS, "run_types", u"((u\"A\", A_GROUPS), (u\"B\", B_GROUPS))", u"((u\"A\", B_GROUPS), (u\"B\", A_GROUPS))", types_problems),
)

#: 定数の変異(``patched``)。(説明, 名前, 替えた値, 赤になるべき検査)。検査は定数を見るもの・振る舞いを見るもののどちらか
CONST_MUTANTS = (
    (u"置き換えの順を入れ替える(出力は同じ。封の字の順と照らす検査だけが赤)", "REPLACEMENTS", (SEALED_REPLACEMENTS[1], SEALED_REPLACEMENTS[0], SEALED_REPLACEMENTS[2]), "const"),
    (u"置き換えを 1 つ抜く(先頭)", "REPLACEMENTS", SEALED_REPLACEMENTS[1:], "both"),
    (u"置き換えを 1 つ抜く(末尾)", "REPLACEMENTS", SEALED_REPLACEMENTS[:2], "both"),
    (u"置き換えの後ろの字が違う", "REPLACEMENTS", (SEALED_REPLACEMENTS[0], SEALED_REPLACEMENTS[1], (b'"InterimInstant', b'"Prior1YearInstant')), "both"),
    (u"置き換えの前の字が違う(引用符を外す)", "REPLACEMENTS", (SEALED_REPLACEMENTS[0], (b'InterimDuration', b'CurrentYearDuration'), SEALED_REPLACEMENTS[2]), "both"),
    (u"ぶつかる印を 1 つ抜く", "COLLISION_MARKS", SEALED_MARKS[:2], "both"),
    (u"2% が 3%", "YEN_BAND", Fraction(3, 100), "both"),
    (u"2% が 1%", "YEN_BAND", Fraction(1, 100), "both"),
    (u"0.5 が 0.6", "PCT_BAND", Fraction(6, 10), "both"),
    (u"0.5 が 0.4", "PCT_BAND", Fraction(4, 10), "both"),
    (u"3 桁が 2 桁", "MIN_DIGITS", 2, "both"),
    (u"3 桁が 4 桁", "MIN_DIGITS", 4, "both"),
    (u"種が違う", "SAMPLE_SEED", 20261114, "const"),
    (u"200 行が 120 行", "SAMPLE_N", 120, "const"),
    (u"規則の名前が違う", "RULES", (u"N-円", u"N-数", u"N-率"), "const"),
    (u"億円の倍率が違う", "YEN_UNITS", collections.OrderedDict([(u"円", 1), (u"千円", 10 ** 3), (u"万円", 10 ** 4), (u"百万円", 10 ** 6), (u"億円", 10 ** 7), (u"兆円", 10 ** 12)]), "both"),
    (u"兆円を単位に入れない", "YEN_UNITS", collections.OrderedDict([(u"円", 1), (u"千円", 10 ** 3), (u"万円", 10 ** 4), (u"百万円", 10 ** 6), (u"億円", 10 ** 8)]), "both"),
    (u"profile が違う", "PROFILE", "P32E", "const"),
    (u"中間の群に乙も入れる", "INTERIM_GROUPS", (u"乙", u"丙"), "const"),
    (u"型が 4 つ", "TYPES", collections.OrderedDict(list(MS.TYPES.items())[:-1]), "const"),
    (u"型(あ)の字が違う", "TYPES", collections.OrderedDict([(u"あ", u"本当の差")] + list(MS.TYPES.items())[1:]), "const"),
    (u"封の commit が違う", "SEAL_COMMIT", "0000000", "const"),
    (u"記録の path が違う", "NEAR_REL", "fixtures/xbrl/tanshin_self/near.json", "const"),
    (u"本番の記録の guard が near だけ", "PRODUCTION_RELS", (RECORD_RELS[1],), "const"),
    (u"行の欄が違う", "NEAR_ROW_COLUMNS", (u"本の #", u"文の番号", u"位置", u"規則", u"単位の族"), "const"),
    (u"付けた席の字が違う", "TYPED_BY", u"司令塔", "const"),
)


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_seal_phrases_paths_and_prediction_rows_are_complete(self):
        self.assertEqual([], seal_problems(self.seal))
        self.assertEqual(list(SEALED_REPLACEMENTS), seal_replacements(self.seal))

    def test_a_2_a_changed_key_phrase_turns_the_seal_check_red(self):
        for ph in SEAL_PHRASES:
            self.assertIn(ph, self.seal)
            mutated_seal = self.seal.replace(ph, ph[:-1] + u"？", 1)
            self.assertNotEqual(mutated_seal, self.seal)
            self.assertNotEqual([], seal_problems(mutated_seal), ph)

    def test_a_3_a_broken_row_replacement_order_or_path_turns_it_red(self):
        lines = self.seal.split("\n")
        u7 = [i for i, ln in enumerate(lines) if ln.startswith("- **U-7**")][0]
        self.assertNotEqual([], seal_problems("\n".join(lines[:u7] + lines[u7 + 1:])))                                  # 10 行が 9 行
        i1 = [i for i, ln in enumerate(lines) if u"`\"Prior1InterimDuration` → " in ln][0]
        swapped = lines[:i1] + [lines[i1 + 1], lines[i1]] + lines[i1 + 2:]
        self.assertNotEqual([], seal_problems("\n".join(swapped)))                                                    # 置き換えの順を入れ替える
        self.assertNotEqual([], seal_problems("\n".join(lines[:i1] + lines[i1 + 1:])))                                  # 置き換えが 2 つ
        self.assertNotEqual([], seal_problems(self.seal.replace("## §5 ", "## 五 ", 1)))                                # 節が揃わない
        self.assertNotEqual([], seal_problems(self.seal.replace(RECORD_RELS[1], "fixtures/xbrl/tanshin_self/other.json")))
        self.assertNotEqual([], seal_problems(self.seal.replace(u"test_xbrl_tanshin_self2_result.py", u"test_other.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace(DOC_REL, "docs/OTHER.md")))

    def test_a_4_the_seal_is_in_history_as_the_sealed_commit(self):
        added = PR.added_commits(REPO, PREFIX + SEAL_REL)
        self.assertEqual(1, len(added))
        self.assertTrue(added[0].startswith(SEAL_COMMIT_SHORT))


class ScriptConstantTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_b_1_the_script_constants_equal_the_seal(self):
        self.assertEqual([], script_problems(self.seal))

    def test_b_2_the_population_is_read_from_the_records_not_copied_into_the_script(self):
        pop = MS.load_population(ROOT)
        self.assertEqual(400, len(pop))
        for rel in (SCRIPT_REL, GATE_REL):
            src = read(rel)
            self.assertEqual([], [r[0] for r in pop if r[3] in src], rel)

    def _ns(self):
        return types.SimpleNamespace(**dict((k, getattr(MS, k)) for k in dir(MS) if not k.startswith("__")))

    def test_b_3_each_script_constant_turns_the_check_red_when_changed(self):
        changes = (
            ("SEAL_REL", "docs/x.md"), ("SEAL_COMMIT", "0000000"), ("SCRIPT_REL", "measure/x.py"), ("TSS_SCRIPT_REL", "measure/x.py"), ("TSS_SEAL_REL", "docs/x.md"), ("DOC_REL", "docs/x.md"),
            ("INTERIM_REL", "fixtures/x.json"), ("NEAR_REL", "fixtures/x.json"), ("NEAR_TYPES_REL", "fixtures/x.json"), ("TSS_STATES_REL", "fixtures/x.json"), ("PRODUCTION_RELS", ()),
            ("COLLISION_MARKS", SEALED_MARKS[:2]), ("PROFILE", "P32E"), ("INTERIM_GROUPS", (u"乙", u"丙")), ("A_GROUPS", (u"甲",)), ("B_GROUPS", (u"乙", u"丙")),
            ("YEN_UNITS", collections.OrderedDict([(u"円", 1)])), ("YEN_BAND", Fraction(1, 50) + 1), ("PCT_BAND", Fraction(1, 2) + 1), ("MIN_DIGITS", 4), ("RULES", (u"N-円", u"N-桁")),
            ("SAMPLE_SEED", 1), ("SAMPLE_N", 199), ("TYPES", collections.OrderedDict()), ("TYPED_BY", u"人"), ("NEAR_ROW_COLUMNS", (u"本の #",)), ("ST", types.SimpleNamespace()),
            ("TS", types.SimpleNamespace()))
        for name, val in changes:
            ms2 = self._ns()
            setattr(ms2, name, val)
            self.assertNotEqual([], script_problems(self.seal, ms=ms2), name)
        ms3 = self._ns()
        ms3.TSS = types.SimpleNamespace(ATTACH_PREFIX="x", OLD_SUFFIX="y", ZIP_DATE_TIME=(2000, 1, 1, 0, 0, 0), STAGE_SCRIPT_REL="", ST=ms3.ST, TS=ms3.TS)
        self.assertNotEqual([], script_problems(self.seal, ms=ms3))

    def test_b_4_a_changed_character_in_the_seal_turns_the_comparison_red(self):
        self.assertNotEqual([], script_problems(self.seal.replace(u"`\"InterimInstant` → `\"CurrentYearInstant`", u"`\"InterimInstant` → `\"CurrentYearInstan`", 1)))
        self.assertNotEqual([], script_problems(self.seal.replace(u"(お) 読んでも分けられない", u"(お) 読んでも分けない")))
        self.assertNotEqual([], script_problems(self.seal.replace(u"倍率 `m` = 1・1e3・1e4・1e6・1e8・1e12", u"倍率 `m` = 1・1e3")))
        self.assertNotEqual([], script_problems(self.seal.replace(u"本の #・文の番号・位置・当たった規則・単位の族", u"本の #・文の番号")))

    def test_b_5_the_constants_are_pinned_by_value(self):
        self.assertEqual(Fraction(1, 50), MS.YEN_BAND)
        self.assertEqual(Fraction(1, 2), MS.PCT_BAND)
        self.assertEqual(3, MS.MIN_DIGITS)
        self.assertEqual((20261115, 200), (MS.SAMPLE_SEED, MS.SAMPLE_N))
        self.assertEqual(SEALED_REPLACEMENTS, MS.REPLACEMENTS)
        self.assertEqual(SEALED_MARKS, MS.COLLISION_MARKS)


class EngineZeroTest(unittest.TestCase):
    def test_c_1_the_real_history_has_no_engine_lib_device_or_previous_script_change_since_the_seal(self):
        self.assertEqual([], untouched_problems())

    def test_c_1b_the_first_stage_scripts_and_records_are_unchanged_since_their_result_commit(self):
        self.assertEqual([], untouched_problems(base=TSS_RESULT_COMMIT, rels=TSS_FROZEN_RELS))

    def _repo(self):
        r = PR.Repo()
        for rel in NOT_TOUCHED_RELS + ("measure/free.py",):
            r.put(rel + ("" if "." in os.path.basename(rel) else "/a.py"))
        r.commit(*[rel + ("" if "." in os.path.basename(rel) else "/a.py") for rel in NOT_TOUCHED_RELS + ("measure/free.py",)])
        r.put("docs/seal.md")
        r.commit("docs/seal.md")
        return r

    def _problems(self, r):
        return untouched_problems(root=r.d, seal_rel="docs/seal.md")

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

    def test_c_3_an_unknown_seal_or_base_is_red(self):
        r = self._repo()
        self.assertNotEqual([], untouched_problems(root=r.d, seal_rel="docs/none.md"))
        self.assertNotEqual([], untouched_problems(root=r.d, base="0" * 40, rels=("measure/free.py",)))

    def test_c_4_the_base_for_the_first_stage_is_in_history(self):
        rc, _ = PR.git_in(REPO, "cat-file", "-e", TSS_RESULT_COMMIT + "^{commit}")
        self.assertEqual(0, rc)


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


class RulesTest(unittest.TestCase):
    def test_d_1_the_near_row_rules_hold(self):
        self.assertEqual([], rules_problems())

    def test_d_2_the_seal_examples_are_in_the_seal_text(self):
        seal = read(SEAL_REL)
        for ph in (u"`v` 15960・百万円・`r` 16145000000.0", u"`v` 12345・百万円・`r` 12435000000.0", u"`v` 104.6・%・`r` 104.2", u"`v` 98000・百万円・`r` 94400000000.0",
                   u"`v` 104.6・%・`r` 103.47", u"`v` 15960・百万円・`r` 15960000000.0"):
            self.assertIn(ph, seal)

    def test_d_3_the_rule_never_uses_pythons_round_or_float_division_for_the_decision(self):
        with open(os.path.join(ROOT, SCRIPT_REL), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in ("near_rules", "digits_close", "exact")):
            names = [c.func.id for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)]
            self.assertNotIn("round", names, fn.name)                              # 銀行丸めを使わない
            self.assertNotIn("float", names, fn.name)                              # float で境界を比べない


class ReplaceTest(unittest.TestCase):
    def test_e_1_the_replacement_follows_the_seal(self):
        self.assertEqual([], replace_problems())

    def test_e_2_the_replaced_zip_is_never_written_by_the_script(self):
        src = read(SCRIPT_REL)
        self.assertEqual([], [m for m in re.findall(r"open\([^)]*[\"']wb[\"']", src)])        # 置き換えた ZIP を書く経路が無い(binary で書く open が無い)

    def test_e_3_the_three_replacements_do_not_touch_each_others_output(self):
        u"""順を入れ替えても出力が同じことを、実際の入力で確かめる(変異の表に入れない理由。順は定数の照合で赤にする)。"""
        sample = (b'"Prior1InterimDuration"x"InterimDuration"x"InterimInstant"x"Prior1InterimInstant"x"Prior1YearInstant"x"Prior2YearInstant"x"CurrentQuarterDuration"')
        want = sample
        for old, new in SEALED_REPLACEMENTS:
            want = want.replace(old, new)
        import itertools
        for perm in itertools.permutations(SEALED_REPLACEMENTS):
            got = sample
            for old, new in perm:
                got = got.replace(old, new)
            self.assertEqual(want, got)
        self.assertNotEqual(sample, want)

    def test_e_4_a_reordered_replacement_list_is_caught_by_the_constant_check_and_a_dropped_one_by_both(self):
        seal = read(SEAL_REL)
        for label, name, val, kind in CONST_MUTANTS[:5]:
            ms2 = types.SimpleNamespace(**dict((k, getattr(MS, k)) for k in dir(MS) if not k.startswith("__")))
            setattr(ms2, name, val)
            self.assertNotEqual([], script_problems(seal, ms=ms2), label)


class InterimTest(unittest.TestCase):
    def test_f_1_the_moves_follow_the_rules(self):
        self.assertEqual([], moves_problems())

    def test_f_2_the_interim_record_is_whole_and_reproducible(self):
        self.assertEqual([], interim_problems())
        self.assertEqual([], clean_problems())

    def test_f_3_every_record_writer_calls_check_clean_before_writing(self):
        self.assertEqual([], clean_wiring_problems())


class NearTest(unittest.TestCase):
    def test_h_1_the_near_record_is_whole_and_reproducible(self):
        self.assertEqual([], near_problems())

    def test_h_2_the_per_book_rows_and_the_non_number_rows(self):
        self.assertEqual([], near_book_problems())

    def test_h_3_the_reading_rows_are_drawn_by_the_rule(self):
        self.assertEqual([], items_problems())

    def test_h_4_the_population_and_the_first_stage_record_checks_hold(self):
        self.assertEqual([], population_problems())


class SheetTypesTest(unittest.TestCase):
    def test_j_1_the_sheet_is_written_outside_the_repo_only(self):
        self.assertEqual([], sheet_problems())

    def test_j_2_the_types_record_follows_the_rules(self):
        self.assertEqual([], types_problems())


class MutantTest(unittest.TestCase):
    def test_k_1_every_check_is_green_on_the_real_code_and_red_on_each_mutant(self):
        checks = sorted(set(m[5] for m in MUTANTS), key=lambda f: f.__name__)
        for chk in checks:
            self.assertEqual([], chk(), chk.__name__)
        silent = []
        for (label, mod, fn, old, new, chk) in MUTANTS:
            orig = getattr(mod, fn)
            with mutated(mod, fn, old, new), warnings.catch_warnings():
                warnings.simplefilter("ignore")                  # 「名前が重なっても止めない」型の変異は zipfile が Duplicate name を警告することがある
                got = guard(chk)
            self.assertIs(getattr(mod, fn), orig)
            if not got:
                silent.append(label)
        self.assertEqual([], silent)

    def test_k_2_every_constant_mutant_turns_a_check_red(self):
        seal = read(SEAL_REL)
        silent = []
        for label, name, val, kind in CONST_MUTANTS:
            orig = getattr(MS, name)
            ms2 = types.SimpleNamespace(**dict((k, getattr(MS, k)) for k in dir(MS) if not k.startswith("__")))
            setattr(ms2, name, val)
            const_red = bool(script_problems(seal, ms=ms2))
            with patched(MS, **{name: val}), warnings.catch_warnings():
                warnings.simplefilter("ignore")
                behave_red = bool(guard(replace_problems) or guard(rules_problems) or guard(items_problems))
            self.assertIs(getattr(MS, name), orig)
            if kind == "const" and not const_red:
                silent.append(label + u"(定数の照合)")
            if kind == "both" and not (const_red and behave_red):
                silent.append(label + u"(定数 %s・振る舞い %s)" % (const_red, behave_red))
        self.assertEqual([], silent)

    def test_k_3_a_mutant_is_always_put_back(self):
        orig = MS.near_rules
        with self.assertRaises(RuntimeError):
            with mutated(MS, "near_rules", u"abs(c - f) <= f * YEN_BAND", u"abs(c - f) < f * YEN_BAND"):
                self.assertIsNot(MS.near_rules, orig)
                raise RuntimeError("x")
        self.assertIs(MS.near_rules, orig)
        with self.assertRaises(AssertionError):
            with mutated(MS, "near_rules", u"this text is not in the function", u"x"):
                pass
        self.assertIs(MS.near_rules, orig)

    def test_k_4_the_mutant_table_covers_each_effect_named_in_the_brief(self):
        labels = u" ".join(m[0] for m in MUTANTS) + u" ".join(m[0] for m in CONST_MUTANTS)
        for key in (u"置き換えの順", u"置き換えを 1 つ抜く", u"2% が", u"ぶつかる本も写す", u"桁数の下限を外す", u"銀行丸め", u"A も写す", u"B を写さない", u"本番の記録を使い捨ての材料で作る"):
            self.assertIn(key, labels)


class WiringTest(unittest.TestCase):
    def test_l_1_the_script_calls_the_first_stage_functions_and_defines_none_of_the_same_name(self):
        self.assertEqual([], reuse_problems())

    def test_l_2_a_same_name_definition_or_a_missing_call_turns_it_red(self):
        with tmpdir() as d:
            src = read(SCRIPT_REL)
            p = os.path.join(d, "s.py")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(src + u"\n\ndef wrap(zb, text):\n    return zb, 0\n")
            self.assertNotEqual([], reuse_problems(src_path=p))
            for name in NOT_REDEFINED:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(src + u"\n\ndef %s(*a):\n    return None\n" % name)
                self.assertNotEqual([], reuse_problems(src_path=p), name)
            for alias, fn in REUSED_FUNCS:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(src.replace(u"%s.%s" % (alias, fn), u"%s.%sx" % (alias, fn)))
                self.assertNotEqual([], reuse_problems(src_path=p), (alias, fn))
        ms2 = types.SimpleNamespace(**dict((k, getattr(MS, k)) for k in dir(MS) if not k.startswith("__")))
        ms2.TSS = types.SimpleNamespace()
        self.assertNotEqual([], reuse_problems(ms=ms2))

    def test_l_3_the_script_imports_no_network_module(self):
        self.assertEqual([], network_problems())
        with tmpdir() as d:
            for line in (u"import urllib.request", u"from urllib import request", u"import socket", u"import http.client", u"from http import client", u"import ssl", u"import requests"):
                p = os.path.join(d, "s.py")
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(u"import os\n" + line + u"\n")
                self.assertNotEqual([], network_problems(p), line)

    def test_l_4_names_that_existed_before_loading_are_put_back(self):
        marker = types.ModuleType("pswap_for_idmap")
        before = sys.modules.get("pswap_for_idmap")
        sys.modules["pswap_for_idmap"] = marker
        sentinel = types.ModuleType("rmix_for_pbind")
        before2 = sys.modules.get("rmix_for_pbind")
        sys.modules["rmix_for_pbind"] = sentinel
        names = ("tanshin_self_for_tanshin_self2", "tanshin_self_stage_for_tanshin_self", "tanshin_for_tanshin_self")
        before3 = dict((n, sys.modules.get(n)) for n in names)
        try:
            mod = load_module(SCRIPT_REL, "tanshin_self2_script_reload_probe")
            self.assertIs(marker, sys.modules["pswap_for_idmap"])                      # 先に居た名前は元の object
            self.assertIs(sentinel, sys.modules["rmix_for_pbind"])
            self.assertIs(mod, sys.modules["tanshin_self2_script_reload_probe"])       # 自分の名前は残る
            self.assertIsNot(mod.TSS, None)
            for n in names:                                                            # 読み込んだ先の便が決まった名前で入れ直したものも戻る(先に居なかった名前は増えてよい)
                if before3[n] is not None:
                    self.assertIs(before3[n], sys.modules[n])
        finally:
            for k, v in (("pswap_for_idmap", before), ("rmix_for_pbind", before2)):
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v
            sys.modules.pop("tanshin_self2_script_reload_probe", None)

    def test_l_5_no_reserved_names_no_docid_no_tdnet_no_known_code_in_the_new_files(self):
        self.assertEqual([], reserved_problems())
        self.assertEqual([], name_problems())
        with tmpdir() as d:
            with open(os.path.join(d, "g.py"), "w") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rels=("g.py",), base=d))
            for text, codes in (("x = 'S100" + "ABCD'\n", None), ("x = '0812" + "20260810517389'\n", None), ("x = 'ab" + "12345cd'\n", ["12345"])):
                with open(os.path.join(d, "s.py"), "w") as fh:
                    fh.write(text)
                self.assertNotEqual([], name_problems(rels=("s.py",), base=d, codes=codes), text)

    def test_l_6_the_new_files_carry_no_secret_material_markers_and_no_skip_folder_name(self):
        handoff = u"sgogi-coach" + u"-handoff"                                        # 開かない folder(この file が自分の字に当たらないよう、つないで書く)
        skipped = ST.SKIP_CACHES[0]
        for rel in SCRIPT_RELS + (GATE_REL,):
            self.assertNotIn(handoff, read(rel), rel)
            self.assertNotIn(skipped, read(rel), rel)

    def test_l_7_the_script_shares_the_first_stage_instances(self):
        self.assertIs(MS.ST, MS.TSS.ST)
        self.assertIs(MS.TS, MS.TSS.TS)
        self.assertTrue(callable(MS.TSS.judge_book) and callable(MS.TSS.wrap) and callable(MS.TSS.cut))
        self.assertIs(MS.Stop, MS.ST.Stop)


if __name__ == "__main__":
    unittest.main()
