# -*- coding: utf-8 -*-
"""封 docs/XBRL_TANSHIN_HUMAN_TEXT_SEAL_2026-11-09.md(TS ― 人が書いた有報の外の文 = 同じ 20 社の決算短信「経営成績等の概況」17 社で engine を測る)の測定の門。封 §0-1 の 3・§0-2・§1・§2・§3・§5。

**この門が縛るもの**(結果の門 ``test_xbrl_tanshin_result.py`` は記録・文書・判定・行の欄を縛る)

1. 封の字: §1 の材料の表が 17 行で、証券コード・TDnet の番号・ZIP の sha256・字数・claim が揃う(字数の合計 84,378・claim の合計 1,283)・§3 が H-1〜H-10 の 10 行でどの行も欄・予測・外れ方を持つ・
   §5 の script の path・§2 の記録と結果の文書と門の path・規則の要点。封の字を 1 字変えると赤。
2. 封の字と script の定数が同じ: **取得の script の表(``TABLE``)の 17 行が封 §1 の表と字で同じ**(sha256 を 1 字変えると赤)・封の path と commit(5bba61e)・記録 3 つの path・結果の文書の path・
   profile の対(P30E → P32E)・注入の型 4 つ・切り出しの字(「１．経営成績等の概況」「２．」「……」)・URL の形・User-Agent・待ち 1 秒・置き場の名前。
3. engine 0 行: 封の commit から HEAD まで ``core/``・``adapters/``・``measure/lib``・``measure/inject.py`` を触っていない。**規則 T の engine の commit(message に封 eb281f1 を持ち、
   recipes.py と vocabulary.py だけを触る)が先に入っていれば、その宣言された遷移だけ許す**(PB の封の門の形)。
4. 順序: 封 5bba61e ⊏ script・門 2 本(記録・結果の文書の順序は結果の門が見る)。未 commit は赤(skip にしない)。
5. 切り出しの関数の境界: 目次の行(「……」を持つ)を除く・最後の「１．経営成績等の概況」・最初の「２．」・NFKC で半角・行の空白の連なりを 1 つに(行頭・行末は削らない)・空行を詰める・
   script と style を除く・br と閉じ tag で行を切る・無ければ止める。
6. 取得: sha256 が違う・HTTP の状態が 200 でない・応答が ZIP でない 本が 1 本でもあれば何も書かずに止める・cache に在れば取り直さず sha256 だけ照らす・1 本取るごとに 1 秒待つ・
   User-Agent に browser の字・``--only`` は ``--out`` が要り本番の置き場に書かない・出力が既に在れば止める・有報の対応は 1 対 1 でなければ止める・既存の cache が変われば止める。
7. 配線: 測定の script が前の便の script の同じ instance を使い(PB・TY)、前の便の関数を**そのまま呼ぶ**(同名の関数を定義しない)。読み込みの前に居た ``sys.modules`` の名前は読み込みの後に元の object に戻る。
   切り替え 2 つは inject の外で偽。新しい門が既存の門が行頭の名前を数える変数名を行頭に置かない。script・門に docID の字が無い。fetch の記録が ``LATER_NAMING_FILES`` に宣言されている。

この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import ast
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import types
import unittest
import zipfile

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


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_tanshin_seal")       # 順序の部品(order_problems・Repo・git_in・added_commits)。門としては走らせない
TS = load_module("measure/xbrl_tanshin_2026-11-09.py", "tanshin_script_for_seal_gate")
FE = TS.FE

SEAL_REL = TS.SEAL_REL
SEAL_COMMIT_SHORT = "5bba61e"                       # 封の commit(literal に留める。script の定数と違えば script_problems が赤)
DOC_REL = TS.DOC_REL
FETCH_SCRIPT_REL = "measure/xbrl_tanshin_fetch_2026-11-09.py"
SCRIPT_RELS = (FETCH_SCRIPT_REL, "measure/xbrl_tanshin_2026-11-09.py")
GATE_RELS = ("tests/measure/test_xbrl_tanshin_seal.py", "tests/measure/test_xbrl_tanshin_result.py")
RECORD_RELS = ("fixtures/xbrl/tanshin/fetched_2026-11-09.json", "fixtures/xbrl/tanshin/states_2026-11-09.json", "fixtures/xbrl/tanshin/inject_2026-11-09.json")
#: engine・lib・仕掛けのうち、封の commit から 0 行でなければならない path
NOT_TOUCHED_RELS = ("adapters", "core", "measure/lib", "measure/inject.py")
#: 規則 T(封 eb281f1)の engine の commit は宣言された遷移として許す: message に封の hash を持ち、触る file が下の 2 つだけ
RULE_T_MARKERS = ("eb281f1",)
RULE_T_FILES = ("adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS", "LATER_FINGERPRINT",
                     "FINGERPRINT_", "LATER_TARGET", "LATER_FROZEN", "FROZEN_BUNDLE_AT_SEAL", "TARGET_AT_SEAL", "ENGINE_AT_SEAL", "ENGINE_AT_MEASURE", "ENGINE_DECLARED")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
PRED_IDS = tuple("H-%d" % i for i in range(1, 11))
#: 封の字の要点(封に無ければ赤)
SEAL_PHRASES = (
    u"engine は変えない。profile は P27(既定)・P30E・P32E。",
    u"材料は 17 社の短信の「経営成績等の概況」だけ。",
    u"短信の文は「正しい」と仮定しない。",
    u"取った ZIP の sha256 は §1 の表の値と一致しなければ止める",
    u"文(短信の字)は repo に入れない。記録は件数・state・位置・id だけ",
    u"採用 / 不採用の判定は無い(engine を変えない便)。",
    u"全角の数字・括弧・％ を NFKC で半角にする",
)
#: 切り出しの字(封 §0-1 の 3。literal に留める)
CUT_PINS = (u"１．経営成績等の概況", u"２．", u"……")
SEAL_TABLE_ROW = re.compile(r"^\| (\d+) \| (\w+) \| (\d+) \| `([0-9a-f]{64})` \| ([\d,]+) \| (\d+) \|$", re.M)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. 封の字
def seal_table(seal):
    u"""封 §1 の表 [(#, 証券コード, 番号, sha256, 字数, claim)]。"""
    try:
        sec = seal[seal.index("## §1"):seal.index("## §2")]
    except ValueError:
        return []
    return [(int(m[0]), m[1], m[2], m[3], int(m[4].replace(",", "")), int(m[5])) for m in SEAL_TABLE_ROW.findall(sec)]


def seal_problems(seal):
    out = []
    try:
        sec3 = seal[seal.index("## §3"):seal.index("## §4")]
        sec2 = seal[seal.index("## §2"):seal.index("## §3")]
        sec5 = seal[seal.index("## §5"):seal.index("## §6")]
    except ValueError:
        return [u"封の節(§1〜§6)が揃っていない"]
    rows = seal_table(seal)
    if len(rows) != 17:
        out.append(u"封 §1 の表が 17 行でない: %d" % len(rows))
    if [r[0] for r in rows] != list(range(1, len(rows) + 1)):
        out.append(u"封 §1 の表の # が 1 から続いていない")
    if len(set(r[1] for r in rows)) != len(rows) or len(set(r[2] for r in rows)) != len(rows) or len(set(r[3] for r in rows)) != len(rows):
        out.append(u"封 §1 の表の証券コード・番号・sha256 に重複がある")
    if rows and (sum(r[4] for r in rows) != 84378 or sum(r[5] for r in rows) != 1283):
        out.append(u"封 §1 の字数の合計が 84,378・claim の合計が 1,283 でない")
    if any(not re.fullmatch(r"0812\d{14}", r[2]) for r in rows):
        out.append(u"TDnet の番号が 0812 で始まる 18 桁でない行がある")
    ids = re.findall(r"^\| (H-\d+) \| (.*) \|$", sec3, re.M)
    if [i[0] for i in ids] != list(PRED_IDS):
        out.append(u"封 §3 の表が H-1〜H-10 の 10 行でない: %s" % [i[0] for i in ids])
    for k, rest in ids:
        cells = rest.split(u" | ")
        if len(cells) < 3 or any(not c.strip() for c in cells[:3]):
            out.append(u"封 §3 の %s の欄(欄・予測・外れ方)が埋まっていない" % k)
    for rel in SCRIPT_RELS:
        if rel not in sec5:
            out.append(u"封 §5 に script の path が無い: %s" % rel)
    for rel in GATE_RELS + (DOC_REL,) + RECORD_RELS:
        if rel not in sec2 and rel not in sec5:
            out.append(u"封 §2・§5 に path が無い: %s" % rel)
    for ph in SEAL_PHRASES:
        if ph not in seal:
            out.append(u"封に規則の要点の字が無い: %s" % ph)
    return out


# ---------------------------------------------------------------- 2. 封の字と script の定数
def script_problems(seal, ts=None, fe=None):
    u"""封の字と script の定数が同じか。ts・fe = script の module(試験が壊した写しを渡す)。"""
    ts = ts or TS
    fe = fe or ts.FE
    out = []
    want = seal_table(seal)
    if [tuple(r) for r in fe.TABLE] != want:
        out.append(u"取得の script の表が封 §1 の表と違う")
    if ts.TABLE != fe.TABLE:
        out.append(u"測定の script が取得の script の表と別の表を持つ")
    if fe.SEAL_REL != SEAL_REL or ts.SEAL_REL != SEAL_REL or fe.SEAL_COMMIT != SEAL_COMMIT_SHORT or ts.SEAL_COMMIT != SEAL_COMMIT_SHORT:
        out.append(u"封の path・commit が違う")
    if list(ts.REC_REL.values()) != list(RECORD_RELS) or tuple(ts.REC_REL) != ("fetch", "states", "inject"):
        out.append(u"記録の path が封 §2 と違う")
    if ts.DOC_REL != DOC_REL or ts.SCRIPT_REL != SCRIPT_RELS[1] or ts.FETCH_SCRIPT_REL != SCRIPT_RELS[0] or fe.SCRIPT_REL != SCRIPT_RELS[0]:
        out.append(u"結果の文書・script の path が封 §5 と違う")
    if (ts.OLD, ts.NEW) != ("P30E", "P32E") or tuple(ts.INJECT_PROFILES) != ("P30E", "P32E"):
        out.append(u"注入の profile の対が (P30E, P32E) でない")
    if tuple(ts.STATES_PROFILES_BASE) != ("P27", "P30E", "P32E"):
        out.append(u"states の profile が P27・P30E・P32E でない")
    if tuple(ts.TYPES) != ("T1_VALUE", "T5_COINCIDENT", "T8_REL", "T9_PRIOR_TO_CURRENT"):
        out.append(u"注入の型が T1・T5・T8・T9 でない")
    if (ts.HEAD_PREFIX, ts.END_PREFIX, ts.TOC_MARK) != CUT_PINS:
        out.append(u"切り出しの字(始まり・終わり・目次の印)が封 §0-1 の 3 と違う")
    if ts.QUALITATIVE != "XBRLData/Attachment/qualitative.htm":
        out.append(u"qualitative.htm の path が封 §0-1 の 1 と違う")
    if fe.URL_FMT != "https://www2.jpx.co.jp/disc/%s/%s.zip" or "Mozilla" not in fe.USER_AGENT or fe.INTERVAL_SEC != 1.0 or fe.N_ROWS != 17:
        out.append(u"取得の URL の形・User-Agent・待ち・本数が封 §0-1 の 1・§2 の 1 と違う")
    if fe.CACHE_NAME != "tanshin-2026-11-09" or not fe.default_cache_dir().endswith(os.path.join(".cache", "audit-core", "tanshin-2026-11-09")):
        out.append(u"置き場の名前が封 §0-2 の 5 と違う")
    if fe.OUT_REL != RECORD_RELS[0]:
        out.append(u"取得の記録の path が違う")
    return out


# ---------------------------------------------------------------- 3. engine 0 行(規則 T の宣言された遷移だけ許す)
def engine_since_seal_problems(root=REPO, seal_rel=SEAL_REL, prefix=PREFIX, rels=NOT_TOUCHED_RELS, markers=RULE_T_MARKERS, allowed=RULE_T_FILES):
    u"""封の commit から HEAD までに rels を触った commit を列挙し、宣言された遷移(message に marker・触る file が allowed だけ)以外は問題として返す。"""
    seal_commits = PR.added_commits(root, prefix + seal_rel)
    if len(seal_commits) != 1:
        return [u"封の commit が履歴に 1 つに決まらない"]
    s = seal_commits[0]
    rc, log = PR.git_in(root, "log", "--format=%H", "%s..HEAD" % s, "--", *[prefix + r for r in rels])
    if rc != 0:
        return [u"git log が失敗した"]
    out = []
    for c in [x for x in log.split() if x]:
        msg = PR.git_in(root, "show", "-s", "--format=%B", c)[1]
        files = [x for x in PR.git_in(root, "diff-tree", "--no-commit-id", "--name-only", "-r", c, "--", *[prefix + r for r in rels])[1].split() if x]
        declared = any(m in msg for m in markers) and all(f in [prefix + a for a in allowed] for f in files)
        if not declared:
            out.append(u"封の後に engine・lib・仕掛けを触った commit %s(宣言された遷移でない)" % c[:7])
    return out


# ---------------------------------------------------------------- 4. 順序
def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = list(SCRIPT_RELS + GATE_RELS) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others)


# ---------------------------------------------------------------- 7. 配線・名前・docID・宣言
#: 前の便の関数(この script は同名の関数を定義せず、前の便の module の関数を呼ぶ)。(module の別名, 関数名)
REUSED_FUNCS = (("PB", "period5"), ("PB", "diff_rows"), ("PI", "id_map"), ("PI", "old_map"), ("PS", "t9_all_sites"), ("PS", "build_t9"), ("PS", "engine_cue"), ("PS", "has_prior_word"),
                ("PS", "shape_of_token"), ("PS", "reached_of"), ("TY", "t5_all_sites"), ("TY", "shape_counter"), ("TY", "partner_period"), ("TY", "same_element"),
                ("RM", "base_status_rb"), ("RUN", "t8_candidates4"), ("RUN", "refs_for"), ("RUN", "sentence_list"), ("RUN", "safe_reason"), ("IJ", "select"), ("IJ", "build_t5"), ("JT", "reread_j"))


def defined_functions(path):
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    return set(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))


def reuse_problems(ts=None, src_path=None):
    u"""この script が前の便の関数を呼ぶ(同名の関数を定義しない)。前の便の module の関数が実在し、script の本文がその名前で呼ぶ。"""
    ts = ts or TS
    path = src_path or os.path.join(ROOT, SCRIPT_RELS[1])
    defs = defined_functions(path)
    with open(path, encoding="utf-8") as fh:
        body = fh.read()
    out = []
    for alias, fn in REUSED_FUNCS:
        if fn in defs:
            out.append(u"%s.%s と同名の関数を script が定義している(前の便の関数を呼ぶ)" % (alias, fn))
        if not callable(getattr(getattr(ts, alias, None), fn, None)):
            out.append(u"%s.%s が前の便の module に無い" % (alias, fn))
        if not re.search(r"\b%s\.%s\b" % (alias, fn), body):
            out.append(u"script が %s.%s を呼んでいない" % (alias, fn))
    return out


def wiring_instance_problems(ts=None):
    ts = ts or TS
    out = []
    if ts.PI is not ts.TY.PI or ts.RUN is not ts.TY.RUN or ts.RM is not ts.TY.RM or ts.IJ is not ts.TY.IJ:
        out.append(u"PI・RUN・RM・IJ が T5Y の便と同じ instance でない")
    if ts.PB.PI is ts.PI:
        out.append(u"PB の便の PI と T5Y の便の PI が同じ instance(別々に読み込む前提が崩れた)")
    if ts.RUN.GEN is not ts.GEN:
        out.append(u"RUN.GEN が同じ instance でない")
    out += list(ts.wiring_problems())
    return out


def reserved_problems(rels=GATE_RELS, base=ROOT):
    out = []
    for rel in rels:
        with open(os.path.join(base, rel), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        for n, line in enumerate(lines, 1):
            if any(re.match(r"%s\w*\s*=" % re.escape(p), line) for p in RESERVED_PREFIXES):
                out.append(u"%s:%d が既存の門の数える名前を行頭に置いている" % (rel, n))
    return out


def docid_problems(rels=SCRIPT_RELS + GATE_RELS, base=ROOT):
    out = []
    for rel in rels:
        p = os.path.join(base, rel)
        if os.path.exists(p) and DOCID_RE.search(open(p, encoding="utf-8").read()):
            out.append(u"%s に docID の字がある" % rel)
    return out


def naming_files_problems(src):
    u"""``LATER_NAMING_FILES``(引きの門の宣言)に fetch の記録の path があるか。"""
    m = re.search(r"^LATER_NAMING_FILES = \((.*?)\n\s*\)\s*$", src, re.S | re.M)
    block = m.group(1) if m else src
    return [] if RECORD_RELS[0] in block else [u"fetch の記録 %s が LATER_NAMING_FILES に宣言されていない" % RECORD_RELS[0]]


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_seal_tables_paths_and_key_phrases_are_complete(self):
        self.assertEqual([], seal_problems(self.seal))
        self.assertEqual(17, len(seal_table(self.seal)))

    def test_a_2_a_changed_key_phrase_turns_the_seal_check_red(self):
        for ph in SEAL_PHRASES:
            self.assertIn(ph, self.seal)
            mutated = self.seal.replace(ph, ph[:-1] + u"？", 1)
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], seal_problems(mutated), ph)

    def test_a_3_a_broken_table_or_prediction_row_turns_it_red(self):
        lines = self.seal.split("\n")
        first = [i for i, ln in enumerate(lines) if ln.startswith("| 1 | 151A0 |")][0]
        self.assertNotEqual([], seal_problems("\n".join(lines[:first] + lines[first + 1:])))                           # 17 行が 16 行
        h10 = [i for i, ln in enumerate(lines) if ln.startswith("| H-10 |")][0]
        self.assertNotEqual([], seal_problems("\n".join(lines[:h10] + lines[h10 + 1:])))                              # 10 行が 9 行
        h5 = [i for i, ln in enumerate(lines) if ln.startswith("| H-5 |")][0]
        cells = lines[h5].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:h5] + [" | ".join(cells[:2]) + " |"] + lines[h5 + 1:])))   # 外れ方が無い
        self.assertNotEqual([], seal_problems("\n".join(lines[:h5] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[h5 + 1:])))   # 予測が空
        self.assertNotEqual([], seal_problems(self.seal.replace("`f534e693f2fbb9769e4659b0facea8bd48c129a462809d4f36aa00415184c905`", "`f534e693f2fbb9769e4659b0facea8bd48c129a462809d4f36aa00415184c906`", 1).replace("3,586", "3,587", 1)))   # 字数の合計が崩れる
        self.assertNotEqual([], seal_problems(self.seal.replace("## §5 ", "## 五 ", 1)))                                # 節が揃わない

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

    def test_b_2_the_fetch_table_is_the_seal_table_character_for_character(self):
        want = seal_table(self.seal)
        self.assertEqual(want, [tuple(r) for r in FE.TABLE])
        for i in range(17):
            for col in (1, 2, 3):                                   # 証券コード・番号・sha256 の 1 字を変えた表は赤
                row = list(FE.TABLE[i])
                row[col] = row[col][:-1] + (u"0" if row[col][-1] != u"0" else u"1")
                bad = tuple(FE.TABLE[:i]) + (tuple(row),) + tuple(FE.TABLE[i + 1:])
                fe2 = types.SimpleNamespace(**dict((k, getattr(FE, k)) for k in dir(FE) if not k.startswith("__")))
                fe2.TABLE = bad
                self.assertNotEqual([], script_problems(self.seal, fe=fe2), (i, col))

    def test_b_3_each_script_constant_turns_the_check_red_when_changed(self):
        base = dict((k, getattr(FE, k)) for k in dir(FE) if not k.startswith("__"))
        for name, val in (("SEAL_COMMIT", "0000000"), ("URL_FMT", "https://example.invalid/%s/%s.zip"), ("USER_AGENT", "python-urllib"), ("INTERVAL_SEC", 0.0),
                          ("N_ROWS", 16), ("CACHE_NAME", "tanshin-x"), ("OUT_REL", "fixtures/xbrl/tanshin/x.json")):
            fe2 = types.SimpleNamespace(**base)
            setattr(fe2, name, val)
            self.assertNotEqual([], script_problems(self.seal, fe=fe2), name)
        base_ts = dict((k, getattr(TS, k)) for k in dir(TS) if not k.startswith("__"))
        for name, val in (("NEW", "P30E"), ("OLD", "P27"), ("INJECT_PROFILES", ("P30E", "P30E")), ("STATES_PROFILES_BASE", ("P27", "P30E")), ("TYPES", ("T1_VALUE",)),
                          ("HEAD_PREFIX", u"１．経営成績"), ("END_PREFIX", u"３．"), ("TOC_MARK", u"..."), ("QUALITATIVE", "x.htm"), ("DOC_REL", "docs/x.md")):
            ts2 = types.SimpleNamespace(**base_ts)
            setattr(ts2, name, val)
            self.assertNotEqual([], script_problems(self.seal, ts=ts2), name)
        ts3 = types.SimpleNamespace(**base_ts)
        ts3.REC_REL = collections.OrderedDict([("fetch", "a"), ("states", "b"), ("inject", "c")])
        self.assertNotEqual([], script_problems(self.seal, ts=ts3))
        ts4 = types.SimpleNamespace(**base_ts)
        ts4.TABLE = tuple(FE.TABLE[:-1])
        self.assertNotEqual([], script_problems(self.seal, ts=ts4))

    def test_b_4_a_changed_character_in_the_seal_turns_the_comparison_red(self):
        self.assertNotEqual([], script_problems(self.seal.replace("081220260810517389", "081220260810517380", 1)))
        self.assertNotEqual([], script_problems(self.seal.replace("`20810e54b3e96c408c", "`20810e54b3e96c408d", 1)))


class EngineZeroTest(unittest.TestCase):
    def test_c_1_the_real_history_has_no_engine_lib_or_device_change_since_the_seal(self):
        self.assertEqual([], engine_since_seal_problems())

    def _repo(self):
        r = PR.Repo()
        r.put("adapters/xbrl/recipes.py")
        r.put("adapters/xbrl/vocabulary.py")
        r.put("adapters/xbrl/other.py")
        r.put("measure/lib/numbers.py")
        r.put("measure/inject.py")
        r.commit("adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/other.py", "measure/lib/numbers.py", "measure/inject.py")
        r.put("docs/seal.md")
        r.commit("docs/seal.md")
        return r

    def _problems(self, r):
        return engine_since_seal_problems(root=r.d, seal_rel="docs/seal.md")

    def test_c_2_a_clean_range_is_green_and_each_touched_path_is_red(self):
        r = self._repo()
        self.assertEqual([], self._problems(r))
        for rel in ("adapters/xbrl/other.py", "core/py/x.py", "measure/lib/numbers.py", "measure/inject.py", "adapters/xbrl/recipes.py"):
            r = self._repo()
            r.put(rel)
            r.commit(rel)
            self.assertNotEqual([], self._problems(r), rel)

    def test_c_3_only_the_declared_rule_t_transition_is_allowed(self):
        r = self._repo()
        r.put("adapters/xbrl/recipes.py")
        r.put("adapters/xbrl/vocabulary.py")
        r.g("add", PREFIX + "adapters/xbrl/recipes.py", PREFIX + "adapters/xbrl/vocabulary.py")
        r.g("commit", "-q", "-m", "engine(規則 T ― 封 eb281f1 の P33E)")
        self.assertEqual([], self._problems(r))                                    # 宣言された遷移(message に封の hash・触る file が 2 つだけ)
        r.put("measure/lib/numbers.py")
        r.g("add", PREFIX + "measure/lib/numbers.py")
        r.g("commit", "-q", "-m", "lib(封 eb281f1)")
        self.assertNotEqual([], self._problems(r))                                 # 宣言の外の file を触る commit は赤
        r2 = self._repo()
        r2.put("adapters/xbrl/recipes.py")
        r2.g("add", PREFIX + "adapters/xbrl/recipes.py")
        r2.g("commit", "-q", "-m", "engine(別の封)")
        self.assertNotEqual([], self._problems(r2))                                # message に封の hash が無い
        r3 = self._repo()
        r3.put("adapters/xbrl/recipes.py")
        r3.put("adapters/xbrl/other.py")
        r3.g("add", PREFIX + "adapters/xbrl/recipes.py", PREFIX + "adapters/xbrl/other.py")
        r3.g("commit", "-q", "-m", "engine(封 eb281f1)")
        self.assertNotEqual([], self._problems(r3))                                # 宣言の外の file を混ぜた commit

    def test_c_4_an_unknown_seal_is_red(self):
        r = self._repo()
        self.assertNotEqual([], engine_since_seal_problems(root=r.d, seal_rel="docs/none.md"))


class OrderTest(unittest.TestCase):
    def test_i_1_the_real_history_has_the_seal_before_the_scripts_and_gates(self):
        u"""script・門のどれかが未 commit なら赤(足した commit が無い)。全部 commit された後で初めて緑。"""
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


# ---------------------------------------------------------------- 5. 切り出しの関数の境界
HTML_T = (u"<html><head><style>.x{color:red}</style><script>var a=1;</script></head><body>\n"
          u"<p>目次</p><div>１．経営成績等の概況……………２</div><div>２．会計基準の選択に関する基本的な考え方……………９</div>\n"
          u"<p>１．経営成績等の概況</p><p>(１)当期の　経営成績の概況</p><p>売上高は１２３，４５６百万円(前期比３．５％増)でした。</p><br/>\n"
          u"<div>注: 見出し「１．経営成績等の概況」の補足</div><p>  営業利益は７８９百万円です。  </p>\n"
          u"<ul><li>項目 A</li><li>項目 B</li></ul><table><tr><td>表</td><td>の行</td></tr></table>\n"
          u"<h2>２．会計基準の選択に関する基本的な考え方</h2><p>当社は日本基準です。</p><p>２．後ろの別の節</p></body></html>")


class OverviewCutTest(unittest.TestCase):
    def test_d_1_the_lines_drop_script_style_and_tags_and_split_on_the_closing_tags(self):
        lines = TS.html_to_lines(HTML_T)
        text = u"\n".join(lines)
        self.assertNotIn(u"color:red", text)
        self.assertNotIn(u"var a", text)
        self.assertNotIn(u"<", text)
        self.assertIn(u"項目 A", lines)                                              # </li> で切れる
        self.assertIn(u"項目 B", lines)
        self.assertNotIn(u"", lines)
        self.assertTrue(all(ln.strip() for ln in lines))                             # 空行・空白だけの行は詰める
        self.assertIn(u"表の行", u"".join(lines))                                    # </td> は改行にしない(</tr> で切れる)
        self.assertEqual(lines.count(u"項目 A"), 1)

    def test_d_2_the_whitespace_runs_become_one_space_and_the_edges_are_kept(self):
        lines = TS.html_to_lines(u"<p>a \t　 b</p><p>  c  </p>")
        self.assertEqual([u"a b", u" c "], lines)                                    # 行頭・行末の空白は削らない(下見の字数と同じ作り)
        self.assertEqual([u"x y"], TS.html_to_lines(u"<div>x&nbsp;y</div>".replace(u"&nbsp;", u" ")))
        self.assertEqual([u"a&b"], TS.html_to_lines(u"<p>a&amp;b</p>"))              # unescape
        self.assertEqual([u"a", u"b"], TS.html_to_lines(u"a<br>b<br/>"))
        self.assertEqual([u"h", u"t"], TS.html_to_lines(u"<h3>h</h3>t"))

    def test_d_3_the_overview_starts_at_the_last_body_heading_and_stops_before_the_first_section_two(self):
        text = TS.overview_from_html(HTML_T)
        lines = text.split(u"\n")
        self.assertEqual(u"1.経営成績等の概況", lines[0])                              # 目次の行(……)ではなく本文の見出しから
        self.assertNotIn(u"目次", text)
        self.assertNotIn(u"……", text)
        self.assertIn(u"営業利益は789百万円です。", text)
        self.assertNotIn(u"当社は日本基準です", text)                                  # 「２．」の行の直前まで
        self.assertNotIn(u"後ろの別の節", text)
        self.assertFalse(any(ln.lstrip().startswith(u"2.") for ln in lines))

    def test_d_4_the_last_heading_wins_and_a_toc_line_never_starts_the_cut(self):
        lines = [u"１．経営成績等の概況……2", u"x", u"１．経営成績等の概況", u"a", u"１．経営成績等の概況", u"b", u"２．次", u"c"]
        self.assertEqual([u"１．経営成績等の概況", u"b"], TS.cut_overview(lines))
        lines2 = [u"１．経営成績等の概況……2", u"x", u"１．経営成績等の概況", u"a", u"２．次", u"c", u"２．さらに次"]
        self.assertEqual([u"１．経営成績等の概況", u"a"], TS.cut_overview(lines2))     # 最初の「２．」
        self.assertEqual([u" １．経営成績等の概況", u"a"], TS.cut_overview([u" １．経営成績等の概況", u"a", u" ２．次"]))   # 行頭の空白は無視して始まりと終わりを決める

    def test_d_5_a_missing_start_or_end_stops(self):
        with self.assertRaises(SystemExit):
            TS.cut_overview([u"１．経営成績等の概況……2", u"x"])                         # 本文の見出しが無い(目次だけ)
        with self.assertRaises(SystemExit):
            TS.cut_overview([u"１．経営成績等の概況", u"a"])                              # 終わりが無い
        with self.assertRaises(SystemExit):
            TS.cut_overview([u"１．経営成績等の概況……2", u"x", u"２．次"])                    # 目次の行は始まりにならない(本文の見出しが無ければ止まる)
        with self.assertRaises(SystemExit):
            TS.overview_from_html(u"<p>無関係</p>")

    def test_d_6_the_overview_is_nfkc(self):
        text = TS.overview_from_html(u"<p>１．経営成績等の概況</p><p>売上高は１，２３４百万円(前期比＋５．６％増)でした。（注）</p><p>２．x</p>")
        self.assertIn(u"1,234百万円(前期比+5.6%増)でした。(注)", text)
        self.assertEqual(text, __import__("unicodedata").normalize("NFKC", text))
        self.assertEqual(u"1.経営成績等の概況", text.split(u"\n")[0])

    def test_d_7_the_zip_reader_needs_qualitative_htm(self):
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w") as z:
            z.writestr(TS.QUALITATIVE, HTML_T.encode("utf-8"))
        self.assertIn(u"営業利益は789百万円です。", TS.overview_from_zip(bio.getvalue()))
        bio2 = io.BytesIO()
        with zipfile.ZipFile(bio2, "w") as z:
            z.writestr("other.htm", b"x")
        with self.assertRaises(SystemExit):
            TS.overview_from_zip(bio2.getvalue())

    def test_d_8_read_tanshin_checks_the_sha256_before_cutting(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            bio = io.BytesIO()
            with zipfile.ZipFile(bio, "w") as z:
                z.writestr(TS.QUALITATIVE, HTML_T.encode("utf-8"))
            zb = bio.getvalue()
            p = FE.zip_path(d, "99990", "0812x")
            os.makedirs(os.path.dirname(p))
            with open(p, "wb") as fh:
                fh.write(zb)
            self.assertIn(u"営業利益", TS.read_tanshin(d, "99990", "0812x", hashlib.sha256(zb).hexdigest()))
            with self.assertRaises(SystemExit):
                TS.read_tanshin(d, "99990", "0812x", hashlib.sha256(zb + b"x").hexdigest())
            with self.assertRaises(SystemExit):
                TS.read_tanshin(d, "99990", "0812y", hashlib.sha256(zb).hexdigest())      # ZIP が cache に無い


# ---------------------------------------------------------------- 6. 取得
def fake_zip(i):
    return b"PK\x03\x04fake-%d" % i


def fake_table(n=2):
    return tuple((i + 1, u"9000%d" % i, u"08129999999999999%d" % i, hashlib.sha256(fake_zip(i)).hexdigest(), 100, 10) for i in range(n))


class Patches(object):
    u"""FE の属性を with の中だけ差し替え、出るときに必ず戻す。"""

    def __init__(self, **kw):
        self.kw = kw

    def __enter__(self):
        self.old = dict((k, getattr(FE, k)) for k in self.kw)
        for k, v in self.kw.items():
            setattr(FE, k, v)
        return self

    def __exit__(self, *a):
        for k, v in self.old.items():
            setattr(FE, k, v)
        return False


def fake_mapping(root, codes, caches=None):
    return collections.OrderedDict((c, (u"D%s" % c, u"%064x" % int(c))) for c in codes)


def run_fake(d, table=None, fetch_map=None, only=None, cache=None, out=None, pre=None, snapshots=None, sleeps=None, urls=None):
    table = table or fake_table()
    zips = fetch_map if fetch_map is not None else dict((u"https://www2.jpx.co.jp/disc/%s/%s.zip" % (r[1], r[2]), (200, fake_zip(i))) for i, r in enumerate(table))
    urls = urls if urls is not None else []
    sleeps = sleeps if sleeps is not None else []

    def fetcher(url):
        urls.append(url)
        return zips[url]
    snaps = iter(snapshots) if snapshots else None
    kw = dict(TABLE=table, map_docids=fake_mapping, read_caches=lambda: collections.OrderedDict())
    with Patches(**kw):
        old_snap = FE.GEN.caches_snapshot
        if snaps is not None:
            FE.GEN.caches_snapshot = lambda existing=None: next(snaps)
        try:
            return FE.run_fetch(root=d, only=only, out=out or os.path.join(d, "rec", "fetched.json"), cache_dir=cache or os.path.join(d, "cache"),
                                fetcher=fetcher, sleep=sleeps.append, say=lambda *a: None, now=lambda: u"2026-11-09T00:00:00Z")
        finally:
            FE.GEN.caches_snapshot = old_snap


class FetchTest(unittest.TestCase):
    def test_e_1_a_good_run_writes_the_zips_and_a_record_with_17_style_rows(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            urls, sleeps = [], []
            rec = run_fake(d, urls=urls, sleeps=sleeps)
            self.assertEqual([u"https://www2.jpx.co.jp/disc/90000/081299999999999990.zip", u"https://www2.jpx.co.jp/disc/90001/081299999999999991.zip"], urls)
            self.assertEqual([1.0, 1.0], sleeps)                                         # 1 本取るごとに 1 秒
            for i, r in enumerate(fake_table()):
                p = os.path.join(d, "cache", r[1], r[2] + ".zip")
                self.assertEqual(fake_zip(i), open(p, "rb").read())
            on_disk = json.load(open(os.path.join(d, "rec", "fetched.json"), encoding="utf-8"))
            self.assertEqual(json.loads(json.dumps(rec)), on_disk)
            self.assertEqual(2, on_disk[u"表と一致した ZIP"])
            self.assertEqual(set([u"#", u"証券コード", u"番号", u"ZIP の sha256", u"取得", u"HTTP の状態", u"byte 数", u"docID", u"有報の ZIP の sha256"]), set(on_disk[u"行"][0]))
            self.assertEqual([200, 200], [r[u"HTTP の状態"] for r in on_disk[u"行"]])
            self.assertEqual([u"D90000", u"D90001"], [r[u"docID"] for r in on_disk[u"行"]])
            self.assertTrue(on_disk[u"cache の前後"][u"変化なし"])
            self.assertEqual([], on_disk[u"key_leaks"])
            self.assertEqual(FE.SEAL_COMMIT, on_disk[u"封の commit"])
            self.assertEqual(hashlib.sha256(open(FE.__file__, "rb").read()).hexdigest(), on_disk[u"この script の sha256"])

    def test_e_2_one_sha256_that_differs_stops_and_writes_nothing(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            table = fake_table()
            zips = dict((u"https://www2.jpx.co.jp/disc/%s/%s.zip" % (r[1], r[2]), (200, fake_zip(i))) for i, r in enumerate(table))
            zips[u"https://www2.jpx.co.jp/disc/90001/081299999999999991.zip"] = (200, fake_zip(1) + b"x")        # 2 本目が差し替わった
            with self.assertRaises(SystemExit):
                run_fake(d, table=table, fetch_map=zips)
            self.assertFalse(os.path.exists(os.path.join(d, "cache")))                  # 1 本目も書かれない
            self.assertFalse(os.path.exists(os.path.join(d, "rec", "fetched.json")))

    def test_e_3_a_non_200_or_a_non_zip_response_stops_and_writes_nothing(self):
        for bad in ((404, b""), (403, b"<html>"), (200, b"<html>not a zip")):
            with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
                table = fake_table()
                zips = dict((u"https://www2.jpx.co.jp/disc/%s/%s.zip" % (r[1], r[2]), (200, fake_zip(i))) for i, r in enumerate(table))
                zips[u"https://www2.jpx.co.jp/disc/90001/081299999999999991.zip"] = bad
                with self.assertRaises(SystemExit):
                    run_fake(d, table=table, fetch_map=zips)
                self.assertFalse(os.path.exists(os.path.join(d, "cache")), bad)
                self.assertFalse(os.path.exists(os.path.join(d, "rec", "fetched.json")), bad)

    def test_e_4_an_existing_zip_is_not_fetched_again_and_its_sha256_is_checked(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            table = fake_table()
            p = os.path.join(d, "cache", table[0][1], table[0][2] + ".zip")
            os.makedirs(os.path.dirname(p))
            with open(p, "wb") as fh:
                fh.write(fake_zip(0))
            urls, sleeps = [], []
            rec = run_fake(d, urls=urls, sleeps=sleeps)
            self.assertEqual([u"https://www2.jpx.co.jp/disc/90001/081299999999999991.zip"], urls)     # 1 本目は取り直さない
            self.assertEqual([1.0], sleeps)
            self.assertIsNone(rec[u"行"][0][u"HTTP の状態"])
            self.assertIn(u"cache に在った", rec[u"行"][0][u"取得"])
            self.assertEqual(200, rec[u"行"][1][u"HTTP の状態"])
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            table = fake_table()
            p = os.path.join(d, "cache", table[0][1], table[0][2] + ".zip")
            os.makedirs(os.path.dirname(p))
            with open(p, "wb") as fh:
                fh.write(fake_zip(0) + b"x")                                           # 在る ZIP の sha256 が表と違う
            with self.assertRaises(SystemExit):
                run_fake(d)
            self.assertFalse(os.path.exists(os.path.join(d, "rec", "fetched.json")))

    def test_e_5_only_needs_out_and_never_writes_the_production_folder(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with Patches(TABLE=fake_table(), map_docids=fake_mapping, read_caches=lambda: collections.OrderedDict()):
                with self.assertRaises(SystemExit):
                    FE.run_fetch(root=d, only=u"90000", out=None, fetcher=lambda u: (200, b""), say=lambda *a: None)      # --out が無い
                with self.assertRaises(SystemExit):
                    FE.run_fetch(root=d, only=u"99999", out=os.path.join(d, "r.json"), cache_dir=os.path.join(d, "c"), fetcher=lambda u: (200, b""), say=lambda *a: None)   # 表に無い
                with Patches(default_cache_dir=lambda: os.path.join(d, "prod")):
                    with self.assertRaises(SystemExit):
                        FE.run_fetch(root=d, only=u"90000", out=os.path.join(d, "r.json"), cache_dir=os.path.join(d, "prod"), fetcher=lambda u: (200, b""), say=lambda *a: None)    # 本番の置き場
            urls = []
            rec = run_fake(d, only=u"90001", urls=urls)
            self.assertEqual([u"https://www2.jpx.co.jp/disc/90001/081299999999999991.zip"], urls)
            self.assertEqual(1, len(rec[u"行"]))
            self.assertIn(u"本番の記録ではない", rec[u"範囲"])
            self.assertEqual(os.path.join(d, "cache", "90001", "081299999999999991.zip"), os.path.join(d, "cache", "90001", "081299999999999991.zip"))
            self.assertTrue(os.path.exists(os.path.join(d, "cache", "90001", "081299999999999991.zip")))
            self.assertFalse(os.path.exists(os.path.join(d, "cache", "90000")))
            self.assertIn(u"使い捨て", rec[u"置き場"])

    def test_e_6_an_existing_output_stops(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            os.makedirs(os.path.join(d, "rec"))
            with open(os.path.join(d, "rec", "fetched.json"), "w") as fh:
                fh.write("{}")
            urls = []
            with self.assertRaises(SystemExit):
                run_fake(d, urls=urls)
            self.assertEqual([], urls)                                                  # 取る前に止まる

    def test_e_7_a_changed_existing_cache_stops_and_writes_nothing(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            a = collections.OrderedDict([("edinet", {u"件数": 1})])
            b = collections.OrderedDict([("edinet", {u"件数": 2})])
            with self.assertRaises(SystemExit):
                run_fake(d, snapshots=[a, b])
            self.assertFalse(os.path.exists(os.path.join(d, "rec", "fetched.json")))

    def test_e_8_the_default_fetcher_sends_a_browser_user_agent_and_returns_the_status(self):
        got = {}

        class Resp(object):
            status = 200

            def read(self):
                return b"PK\x03\x04x"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout=None):
            got["ua"] = req.get_header("User-agent")
            got["url"] = req.full_url
            got["timeout"] = timeout
            return Resp()
        old = FE.urllib.request.urlopen
        FE.urllib.request.urlopen = fake_urlopen
        try:
            self.assertEqual((200, b"PK\x03\x04x"), FE.default_fetcher(u"https://www2.jpx.co.jp/disc/1/2.zip"))
        finally:
            FE.urllib.request.urlopen = old
        self.assertIn("Mozilla", got["ua"])
        self.assertEqual(u"https://www2.jpx.co.jp/disc/1/2.zip", got["url"])
        self.assertTrue(got["timeout"])

    def test_e_9_the_docid_mapping_must_be_one_to_one(self):
        codes_of = {u"DA": u"11110", u"DB": u"22220", u"DC": u"22220", u"DD": None}
        ids = [u"DA", u"DB", u"DC", u"DD"]
        by = dict((d, {u"docID": d}) for d in ids)
        with Patches(company_rows=lambda root: (ids, by), security_code=lambda zb: codes_of[zb.decode()]):
            old = FE.GEN.read_zip
            FE.GEN.read_zip = lambda row, caches=None: row[u"docID"].encode()
            try:
                self.assertEqual({u"11110": (u"DA", hashlib.sha256(b"DA").hexdigest())}, dict(FE.map_docids(ROOT, [u"11110"])))
                with self.assertRaises(SystemExit):
                    FE.map_docids(ROOT, [u"22220"])                                     # 2 つの書類に結ぶ
                with self.assertRaises(SystemExit):
                    FE.map_docids(ROOT, [u"33330"])                                     # どれにも結ばない
                with self.assertRaises(SystemExit):
                    FE.map_docids(ROOT, [u"11110", u"11110"])                           # 同じ書類に 2 つの証券コード
            finally:
                FE.GEN.read_zip = old

    def test_e_10_the_security_code_is_read_from_the_public_doc_xbrl(self):
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w") as z:
            z.writestr("XBRL/PublicDoc/a.xbrl", u'<x><jpdei_cor:SecurityCodeDEI contextRef="c">151A0</jpdei_cor:SecurityCodeDEI></x>'.encode("utf-8"))
            z.writestr("XBRL/AuditDoc/b.xbrl", u'<jpdei_cor:SecurityCodeDEI contextRef="c">99999</jpdei_cor:SecurityCodeDEI>'.encode("utf-8"))
        self.assertEqual(u"151A0", FE.security_code(bio.getvalue()))
        bio2 = io.BytesIO()
        with zipfile.ZipFile(bio2, "w") as z:
            z.writestr("XBRL/PublicDoc/a.xbrl", b"<x/>")
        self.assertIsNone(FE.security_code(bio2.getvalue()))

    def test_e_11_a_key_like_string_in_the_record_stops_before_anything_is_written(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            old = FE.SEAL_COMMIT
            FE.SEAL_COMMIT = u"a" * 40 + u"Z" * 8
            try:
                with self.assertRaises(SystemExit):
                    run_fake(d)
            finally:
                FE.SEAL_COMMIT = old
            self.assertFalse(os.path.exists(os.path.join(d, "cache")))
            self.assertFalse(os.path.exists(os.path.join(d, "rec", "fetched.json")))


# ---------------------------------------------------------------- 7. 配線
class WiringTest(unittest.TestCase):
    def test_f_1_the_script_calls_the_previous_functions_and_defines_none_of_the_same_name(self):
        self.assertEqual([], reuse_problems())

    def test_f_2_a_same_name_definition_or_a_missing_call_turns_it_red(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            src = open(os.path.join(ROOT, SCRIPT_RELS[1]), encoding="utf-8").read()
            p = os.path.join(d, "s.py")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(src + u"\n\ndef t9_all_sites(a, b, c, d):\n    return None\n")
            self.assertNotEqual([], reuse_problems(src_path=p))
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(src.replace(u"PS.build_t9", u"PS.build_t9x"))
            self.assertNotEqual([], reuse_problems(src_path=p))
        ts2 = types.SimpleNamespace(**dict((k, getattr(TS, k)) for k in dir(TS) if not k.startswith("__")))
        ts2.PS = types.SimpleNamespace()
        self.assertNotEqual([], reuse_problems(ts=ts2))

    def test_f_3_the_previous_script_instances_are_shared_and_the_wiring_is_whole(self):
        self.assertEqual([], wiring_instance_problems())
        ts2 = types.SimpleNamespace(**dict((k, getattr(TS, k)) for k in dir(TS) if not k.startswith("__")))
        ts2.PI = TS.PB.PI
        self.assertNotEqual([], wiring_instance_problems(ts2))

    def test_f_4_names_that_existed_before_loading_are_put_back(self):
        marker = types.ModuleType("pswap_for_idmap")
        before = sys.modules.get("pswap_for_idmap")
        sys.modules["pswap_for_idmap"] = marker
        sentinel = types.ModuleType("rmix_for_pbind")
        before2 = sys.modules.get("rmix_for_pbind")
        sys.modules["rmix_for_pbind"] = sentinel
        try:
            mod = load_module(SCRIPT_RELS[1], "tanshin_script_reload_probe")
            self.assertIs(marker, sys.modules["pswap_for_idmap"])                      # 先に居た名前は元の object
            self.assertIs(sentinel, sys.modules["rmix_for_pbind"])
            self.assertIs(mod, sys.modules["tanshin_script_reload_probe"])             # 自分の名前は残る
            self.assertIsNot(mod.PI, None)
        finally:
            for k, v in (("pswap_for_idmap", before), ("rmix_for_pbind", before2)):
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v
            sys.modules.pop("tanshin_script_reload_probe", None)

    def test_f_5_the_switches_are_false_outside_and_the_job_refuses_a_false_switch(self):
        self.assertFalse(getattr(TS.N, TS.TY.FLAG))
        self.assertFalse(getattr(TS.S, TS.TY.FLAG2))
        with self.assertRaises(SystemExit):
            TS.inject_job_ts((1, u"90000", u"x", u"y", {}, u"t", {}, u"seed", u"w"))
        with TS.NS.yen_scan_on():
            with self.assertRaises(SystemExit):                                         # 片方だけ真でも止まる
                TS.inject_job_ts((1, u"90000", u"x", u"y", {}, u"t", {}, u"seed", u"w"))
        self.assertFalse(getattr(TS.N, TS.TY.FLAG))

    def test_f_6_the_inject_and_states_commands_refuse_only_without_out_and_an_existing_output(self):
        with self.assertRaises(SystemExit):
            TS.run_states(only=u"78130", out=None)
        with self.assertRaises(SystemExit):
            TS.run_inject(only=u"78130", out=None)
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            p = os.path.join(d, "o.json")
            with open(p, "w") as fh:
                fh.write("{}")
            with self.assertRaises(SystemExit):
                TS.run_states(only=u"78130", out=p)
            with self.assertRaises(SystemExit):
                TS.run_inject(only=u"78130", out=p)

    def test_f_7_the_material_folder_follows_out_unless_the_record_is_the_production_one(self):
        self.assertEqual(FE.default_cache_dir(), TS.cache_dir_for(None, None))
        self.assertEqual(os.path.join("/a/b", "cache"), TS.cache_dir_for("/a/b/x.json", None))
        self.assertEqual(os.path.abspath("/c/d"), TS.cache_dir_for("/a/b/x.json", "/c/d"))
        self.assertTrue(TS.is_production_out(ROOT, os.path.join(ROOT, TS.STATES_REL), TS.STATES_REL))
        self.assertFalse(TS.is_production_out(ROOT, "/tmp/x.json", TS.STATES_REL))

    def test_f_8_no_reserved_names_and_no_docid_in_the_new_files(self):
        self.assertEqual([], reserved_problems(rels=tuple(r for r in GATE_RELS if os.path.exists(os.path.join(ROOT, r)))))
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with open(os.path.join(d, "g.py"), "w") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rels=("g.py",), base=d))
            with open(os.path.join(d, "g.py"), "w") as fh:
                fh.write("X_ENGINE_LATER = 1\n")
            self.assertEqual([], reserved_problems(rels=("g.py",), base=d))
        self.assertEqual([], docid_problems(rels=tuple(r for r in SCRIPT_RELS + GATE_RELS if os.path.exists(os.path.join(ROOT, r)))))
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with open(os.path.join(d, "s.py"), "w") as fh:
                fh.write("x = 'S100" + "ABCD'\n")
            self.assertNotEqual([], docid_problems(rels=("s.py",), base=d))

    def test_f_9_the_fetch_record_is_declared_as_a_naming_file(self):
        src = open(os.path.join(ROOT, "tests/measure/test_xbrl_fresh_seal.py"), encoding="utf-8").read()
        self.assertEqual([], naming_files_problems(src))
        self.assertNotEqual([], naming_files_problems(src.replace(RECORD_RELS[0], "fixtures/xbrl/tanshin/other.json")))
        # states・inject の記録は docID を持たない(証券コードで本を引く)ので宣言しない
        self.assertNotIn(RECORD_RELS[1], src)
        self.assertNotIn(RECORD_RELS[2], src)


if __name__ == "__main__":
    unittest.main()
