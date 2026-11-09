# -*- coding: utf-8 -*-
"""封 docs/XBRL_PERIOD_SWAP_SEAL_2026-11-06.md(T9 ― 前期の fact に結ばれた数に当期の値を入れる注入 T9_PRIOR_TO_CURRENT)の測定の門。封 §1・§2-1・§5。

**この門が縛るもの**(結果の門 ``test_xbrl_pswap_result.py`` は記録・文書・採用の判定・行の欄を縛る)

1. 封の字: §1 の乱数の種の字(T9_PRIOR_TO_CURRENT)・cap(型 1 本 10)・土台(P30E が GROUNDED)・比較(P29E)・型の名前・site の条件の字・前期の語 6 つ・pointer の期の分け方の語 4 つ・
   §3 の予測の表が PS-1〜PS-10 の 10 行でどの行も予測と外れ方の欄を持つ・§4 の K-1〜K-4・§5 の path。封の字を 1 字変えると赤。
2. 封の字と script の定数が同じ: 種の字(script の定数 = 封の字。site の並べ替えが実際にその字で乱数を作る)・cap・型・profile・封の commit・path・前期の語・期の語。
3. 触らない file は封の commit から 0 行: ``measure/inject.py``・``measure/lib``・``core/``・``adapters/``。
   前の便(J・H・RB・N)の script・記録・門と、この便が読むだけの file は封の commit の blob と byte が同じ。
4. 順序: 封 3a6aefa ⊏ script・門 3 本(記録・結果の文書の順序は結果の門が見る)。未 commit は赤(skip にしない)。
5. 配線: この script が J の便の script の同じ instance(NS・N・RUN・IJ・TUNE・S・SC・RM・GEN)を使う。切り替えは with の中だけ真(出るとき・例外のときも元に戻す)。
   engine の手がかり ``recipes._prior_cue`` は行の欄のために読むだけで、site の選びには使わない(site の関数が呼ばない・呼んでも site が変わらない)。
6. site: 当期の fact が 1 件・単位が同じ・両方正・値が違う・描いた字を読み直して一致・元の字と違う、の全部を要る。複合も同じ経路。同じ token が 2 回 site にならない。
7. 新しい門が、既存の門が行頭の名前を数える変数名を行頭に置いていない。script・門に docID の字が無い。
8. 門の変異: 封の字・script の定数・numstat・順序・配線・site の条件を 1 つずつ壊した標本で上の検査が赤になる。

この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import importlib.util
import os
import random
import re
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "measure"))


def load_module(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


JSG = load_module("tests/measure/test_xbrl_jtypes_seal.py", "jtypes_seal_gate_for_pswap_seal")     # J の封の門の部品(READ_ONLY_RELS・frozen_problems)。門としては走らせない
SGR = JSG.SGR
PR = JSG.PR                                                                                       # order_problems・Repo・added_commits・git_in
PS = load_module("measure/xbrl_pswap_2026-11-06.py", "pswap_script_for_seal_gate")
JT = PS.JT
NS = PS.NS
N, S, SC, RUN, IJ, TUNE, RM = PS.N, PS.S, PS.SC, PS.RUN, PS.IJ, PS.TUNE, PS.RM

SEAL_REL = PS.SEAL_REL
SEAL_COMMIT_SHORT = "3a6aefa"                     # 封の commit(literal に留める。script の定数と違えば script_problems が赤)
FLAG = PS.FLAG
SCRIPT_RELS = ("measure/xbrl_pswap_2026-11-06.py",)
GATE_RELS = ("tests/measure/test_xbrl_pswap_seal.py", "tests/measure/test_xbrl_pswap_result.py")
ROWS_REL = "tests/measure/test_xbrl_jtypes_rows.py"
RECORD_RELS = tuple(PS.REC_REL.values())
DOC_REL = PS.DOC_REL
#: 触らない file(封の commit から 0 行)
NOT_TOUCHED_RELS = ("measure/inject.py", "measure/lib", "adapters", "core")
#: この便が読むだけの前の便の script・記録・門(封の commit の blob と byte が同じでなければならない)。J の便の分 + J の script・記録・門
READ_ONLY_RELS = JSG.READ_ONLY_RELS + (
    "measure/xbrl_jtypes_2026-11-05.py", "fixtures/xbrl/jtypes/inject_2026-11-05.json",
    "tests/measure/test_xbrl_jtypes_seal.py", "tests/measure/test_xbrl_jtypes_result.py")
#: 既存の門が行頭の名前を数える変数名(新しい門はこれらを行頭に置かない。前の便の封の門と同じ一覧)
RESERVED_PREFIXES = SGR.RESERVED_PREFIXES
DOCID_RE = SGR.DOCID_RE
PRED_IDS = tuple("PS-%d" % i for i in range(1, 11))
K_IDS = tuple("K-%d" % i for i in range(1, 5))
#: 封の字の要点(封に無ければ赤)
SEAL_PHRASES = (
    u"random.Random(\"%s|%s|T9_PRIOR_TO_CURRENT\" % (seed, 本の名前))",
    u"型の名前 `T9_PRIOR_TO_CURRENT`",
    u"`S.identified_sites(text, refs)` の (token, ref) のうち、ref の context が `Prior1Year` で始まり",
    u"`Prior1Year` を `CurrentYear` に替えた key の fact がちょうど 1 件(cur)",
    u"`cur[\"unit\"] == ref[\"unit\"]`",
    u"`cur[\"value\"] > 0` かつ `ref[\"value\"] > 0` かつ値が違う(`IJ.TOL`)",
    u"`rendered = N.render_value(cur[\"value\"] / factor, token)`",
    u"`N.scan(rendered + (token.unit or \"\"))`",
    u"`rendered != token.text`",
    u"土台が P30E GROUNDED の site だけを先頭から cap 件",
    u"`recipes._prior_cue(text, token.start, token.end)`",
    u"`_prior_cue` は**行の欄のため読むだけ**(site の選びに使わない",
    u"`IJ.apply_edits`・`IJ.revert`",
    u"差し替えは `[token.start, token.end]` を rendered に(単位の字は触らない)",
    u"土台 = 無改変で P30E が GROUNDED の claim、比較 = P29E、cap 型 1 本 10",
    u"仕掛け `measure/inject.py`・`measure/lib/sites.py` は触らず",
    u"(基準の claim の pointers[0] の context の先頭: CurrentYear / Prior1Year / 他 / なし)",
    u"前期の語(前期・前年・前連結会計年度・前事業年度・前年同期・前年度)",
    u"切り替えは process の中だけ真",
)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. 封の字
def table_ids(seal, start, end, pat):
    sec = seal[seal.index(start):seal.index(end)]
    return [m.group(1) for m in (re.match(pat, line) for line in sec.splitlines()) if m]


def seal_problems(seal):
    out = []
    try:
        ids = table_ids(seal, "## §3", "## §4", r"^\| (PS-\d+) \| (.*) \|$")
        sec = seal[seal.index("## §3"):seal.index("## §4")]
        sec4 = seal[seal.index("## §4"):seal.index("## §5")]
        sec5 = seal[seal.index("## §5"):seal.index("## §6")]
        sec21 = seal[seal.index("### §2-1"):seal.index("### §2-2")]
    except ValueError:
        return [u"封の節(§2-1・§2-2・§3・§4・§5・§6)が揃っていない"]
    if ids != list(PRED_IDS):
        out.append(u"封 §3 の表が PS-1〜PS-10 の 10 行でない: %s" % ids)
    for line in sec.splitlines():
        m = re.match(r"^\| (PS-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            if len(cells) < 3 or any(not c.strip() for c in cells[:3]):
                out.append(u"封 §3 の %s の欄(欄・予測・外れ方)が埋まっていない" % m.group(1))
    got_k = re.findall(r"^- (K-\d):", sec4, re.M)
    if got_k != list(K_IDS):
        out.append(u"封 §4 の K-1〜K-4 が揃っていない: %s" % got_k)
    for rel in SCRIPT_RELS + GATE_RELS:
        if rel not in sec5:
            out.append(u"封 §5 に path が無い: %s" % rel)
    for rel in RECORD_RELS + (DOC_REL, ROWS_REL) + SCRIPT_RELS + GATE_RELS:
        if rel not in sec21:
            out.append(u"封 §2-1 に path が無い: %s" % rel)
    for ph in SEAL_PHRASES:
        if ph not in seal:
            out.append(u"封に規則の要点の字が無い: %s" % ph)
    return out


def seal_seed_forms(seal):
    u"""封の字から乱数の種の字(``random.Random("...")`` の中。出る順)を読む。"""
    return re.findall(r"random\.Random\(\"([^\"]+)\" % \(seed, 本の名前\)\)", seal)


def seal_cap(seal):
    m = re.search(r"cap 型 1 本 (\d+)", seal)
    return int(m.group(1)) if m else None


def seal_type(seal):
    m = re.search(r"型の名前 `(T\d_[A-Z_]+)`", seal)
    return m.group(1) if m else None


def seal_prior_words(seal):
    m = re.search(r"前期の語\(([^)]*)\)", seal)
    return tuple(m.group(1).split(u"・")) if m else None


def seal_periods(seal):
    m = re.search(r"context の先頭: ([^)]*)\)", seal)
    return tuple(x.strip() for x in m.group(1).split(u"/")) if m else None


# ---------------------------------------------------------------- 2. 封の字と script の定数
def script_problems(seal, ps=None):
    u"""封の字と script の定数が同じか。ps = script の module(試験が壊した写しを渡す)。"""
    ps = ps or PS
    out = []
    forms = seal_seed_forms(seal)
    if forms != [ps.SEED_T9]:
        out.append(u"乱数の種の字が封の字と違う: 封 %r / script %r" % (forms, [ps.SEED_T9]))
    if seal_cap(seal) != ps.RUN.INJECT_CAP:
        out.append(u"cap が封の字(型 1 本 10)と違う")
    if ps.T9 != "T9_PRIOR_TO_CURRENT" or seal_type(seal) != ps.T9:
        out.append(u"型が封の字(T9_PRIOR_TO_CURRENT)と違う")
    if tuple(ps.INJECT_PROFILES) != ("P29E", "P30E"):
        out.append(u"profile が (P29E, P30E) でない")
    if ps.SEAL_REL != SEAL_REL or ps.SEAL_COMMIT != SEAL_COMMIT_SHORT or ps.FLAG != "yen_scan_2026_11_05":
        out.append(u"封の path・commit・切り替えの名前が違う")
    if tuple(ps.SHAPES) != (u"既存", u"万だけ", u"複合"):
        out.append(u"形が 既存 / 万だけ / 複合 でない")
    if ps.BASE_WORD != u"無改変の文で P30E が GROUNDED の claim":
        out.append(u"土台の字が P30E が GROUNDED の claim でない")
    if tuple(ps.PRIOR_WORDS) != seal_prior_words(seal):
        out.append(u"前期の語が封の字(6 語)と違う")
    if tuple(ps.PERIODS) != tuple(seal_periods(seal) or ()):
        out.append(u"pointer の期の語が封の字(CurrentYear / Prior1Year / 他 / なし)と違う")
    return out


REAL_RANDOM = random.Random


class RecordingRandom(REAL_RANDOM):
    u"""``random.Random`` の種の字を記録する(site の並べ替えの乱数が封の字で作られるかを見る)。"""
    seen = []

    def __init__(self, x=None):
        RecordingRandom.seen.append(x)
        REAL_RANDOM.__init__(self, x)


def seeds_used(fn):
    u"""``fn()`` の間 ``PS.random.Random`` を記録版に替えて、作られた乱数の種の字の列を返す(戻す)。"""
    real = PS.random.Random
    RecordingRandom.seen = []
    PS.random.Random = RecordingRandom
    try:
        fn()
    finally:
        PS.random.Random = real
    return list(RecordingRandom.seen)


# ---------------------------------------------------------------- 3. 触らない file
def seal_commit(root=REPO):
    s = PR.added_commits(root, PREFIX + SEAL_REL)
    return s[0] if len(s) == 1 else None


def untouched_problems(lines):
    u"""``git diff --numstat <封> -- <触らない path>`` の行が 0 本か。"""
    return [u"封の commit から変わった(触らない file): %s" % ln.split("\t")[2] for ln in lines if ln]


def real_untouched_problems(root=REPO):
    sh = seal_commit(root)
    if sh is None:
        return [u"封の commit が履歴に 1 つに決まらない"]
    paths = [PREFIX + p for p in NOT_TOUCHED_RELS]
    # 2026-11-06(PB): 封 docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md §2-3 が宣言した遷移(recipes.py +24・vocabulary.py +5。削除 0)だけは触らない file から外す(SGR.pb_declared_numstat。他の行・他の値は赤のまま)
    # 2026-11-06(T5Y): 封 docs/XBRL_T5_YEN_SEAL_2026-11-06.md §2-1 が宣言した遷移(仕掛けの 2 file に挿入だけ: inject.py +30・sites.py +81。削除 0)も外す(SGR.t5y_declared_numstat。他の行・他の値は赤のまま)
    return untouched_problems([x for x in PR.git_in(root, "diff", "--numstat", sh, "--", *paths)[1].splitlines() if x and not SGR.pb_declared_numstat(x, root) and not SGR.t_declared_numstat(x, root) and not SGR.t5y_declared_numstat(x, root)])      # 2026-11-09(T): 封 docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md §2-3 が宣言した遷移(recipes.py +57・vocabulary.py +5。PB との合計 +81・+10。削除 0)も外す(SGR.t_declared_numstat)


# ---------------------------------------------------------------- 7. 行頭の名前
def reserved_problems(rels=GATE_RELS + (ROWS_REL,), base=ROOT):
    out = []
    for rel in rels:
        with open(os.path.join(base, rel), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        for n, line in enumerate(lines, 1):
            if any(re.match(r"%s\w*\s*=" % re.escape(p), line) for p in RESERVED_PREFIXES):
                out.append(u"%s:%d が既存の門の数える名前を行頭に置いている" % (rel, n))
    return out


# ---------------------------------------------------------------- 5. 配線
def wiring_problems(script=None):
    u"""この script が J の便の script(NS)の同じ instance を使っているか + NS の配線の検査。問題の列。"""
    ps = script or PS
    out = list(ps.wiring_problems())
    missing = object()
    for label in ("N", "S", "SC", "RUN", "IJ", "TUNE", "RM", "GEN"):
        if getattr(ps, label, missing) is not getattr(ps.NS, label, missing) or getattr(ps, label, missing) is missing:
            out.append(u"%s がこの script と J の便の script で同じ instance でない" % label)
    if ps.NS is not ps.JT.NS:
        out.append(u"NS がこの script と J の便の script で同じ instance でない")
    if getattr(ps.NS, "yen_scan_on", missing) is not ps.yen_scan_on:
        out.append(u"切り替えの with が NS のものでない")
    if ps.FLAG != getattr(ps.NS, "FLAG", missing):
        out.append(u"切り替えの名前が NS と違う")
    if ps.R.__name__ != "adapters.xbrl.recipes":
        out.append(u"engine の手がかりを読む module が recipes でない")
    return out


# ---------------------------------------------------------------- 6. site の標本
TEXT_C = u"前期の売上高は9億7,000万円でした。"
REFS_C = [{"key": "jppfs:NetSales@CurrentYearDuration", "value": 1234560000.0, "unit": u"円", "label": u"売上高"},
          {"key": "jppfs:NetSales@Prior1YearDuration", "value": 970000000.0, "unit": u"円", "label": u"売上高"}]


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_seal_tables_paths_and_key_phrases_are_complete(self):
        self.assertEqual([], seal_problems(self.seal))

    def test_a_2_a_changed_key_phrase_turns_the_seal_check_red(self):
        for ph in SEAL_PHRASES:
            self.assertIn(ph, self.seal)
            mutated = self.seal.replace(ph, ph[:-1] + u"？")                       # 同じ字が 2 か所に在る要点も全部壊す
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], seal_problems(mutated), ph)

    def test_a_3_a_broken_prediction_table_or_missing_section_turns_it_red(self):
        lines = self.seal.split("\n")
        ps10 = [i for i, ln in enumerate(lines) if ln.startswith("| PS-10 |")]
        self.assertEqual(1, len(ps10))
        self.assertNotEqual([], seal_problems("\n".join(lines[:ps10[0]] + lines[ps10[0] + 1:])))                       # 10 行が 9 行
        p5 = [i for i, ln in enumerate(lines) if ln.startswith("| PS-5 |")][0]
        cells = lines[p5].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:p5] + [" | ".join(cells[:2]) + " |"] + lines[p5 + 1:])))   # 外れ方の欄が無い
        self.assertNotEqual([], seal_problems("\n".join(lines[:p5] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[p5 + 1:])))   # 予測の欄が空
        k4 = [i for i, ln in enumerate(lines) if ln.startswith("- K-4:")]
        self.assertEqual(1, len(k4))
        self.assertNotEqual([], seal_problems("\n".join(lines[:k4[0]] + lines[k4[0] + 1:])))
        self.assertNotEqual([], seal_problems(self.seal.replace("measure/xbrl_pswap_2026-11-06.py", "measure/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("inject_2026-11-06.json", "inject_x.json")))
        self.assertNotEqual([], seal_problems(self.seal.replace("XBRL_PERIOD_SWAP_RESULT_2026-11-06.md", "x.md")))
        self.assertNotEqual([], seal_problems(self.seal.replace("tests/measure/test_xbrl_jtypes_rows.py", "tests/measure/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("## §4", "## 四", 1)))

    def test_a_4_the_seed_cap_type_words_and_periods_are_read_from_the_seal(self):
        self.assertEqual([PS.SEED_T9], seal_seed_forms(self.seal))
        self.assertEqual(10, seal_cap(self.seal))
        self.assertEqual("T9_PRIOR_TO_CURRENT", seal_type(self.seal))
        self.assertEqual(tuple(PS.PRIOR_WORDS), seal_prior_words(self.seal))
        self.assertEqual((u"CurrentYear", u"Prior1Year", u"他", u"なし"), seal_periods(self.seal))
        self.assertEqual([], seal_seed_forms(self.seal.replace(u"random.Random(\"%s|%s|T9_PRIOR_TO_CURRENT\" % (seed, 本の名前))", u"x", 1)))
        self.assertEqual(11, seal_cap(self.seal.replace(u"cap 型 1 本 10", u"cap 型 1 本 11", 1)))
        self.assertIsNone(seal_cap(self.seal.replace(u"cap 型 1 本 10", u"cap 10", 1)))


class ScriptMatchesSealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_b_1_the_script_agrees_with_the_seal(self):
        self.assertEqual([], script_problems(self.seal))

    def _fake(self, **ov):
        d = dict(SEED_T9=PS.SEED_T9, RUN=PS.RUN, T9=PS.T9, INJECT_PROFILES=PS.INJECT_PROFILES, SEAL_REL=PS.SEAL_REL, SEAL_COMMIT=PS.SEAL_COMMIT, FLAG=PS.FLAG,
                 SHAPES=PS.SHAPES, BASE_WORD=PS.BASE_WORD, PRIOR_WORDS=PS.PRIOR_WORDS, PERIODS=PS.PERIODS)
        d.update(ov)
        return types.SimpleNamespace(**d)

    def test_b_2_a_changed_script_constant_turns_it_red(self):
        self.assertEqual([], script_problems(self.seal, self._fake()))
        for ov in (dict(SEED_T9=u"%s|%s|T9_PRIOR_TO_CURRENTx"), dict(SEED_T9=u"%s|%s|T6_PRIOR"), dict(RUN=types.SimpleNamespace(INJECT_CAP=11)), dict(T9="T9_PRIOR"),
                   dict(INJECT_PROFILES=("P28E", "P29E")), dict(SEAL_COMMIT="0000000"), dict(FLAG="compound_yen_2026_11_05"), dict(SHAPES=(u"既存", u"万だけ")),
                   dict(BASE_WORD=u"無改変の文で P29E が GROUNDED の claim"), dict(PRIOR_WORDS=PS.PRIOR_WORDS[:-1]), dict(PRIOR_WORDS=PS.PRIOR_WORDS[:-1] + (u"前々期",)),
                   dict(PERIODS=(u"CurrentYear", u"Prior1Year", u"他")), dict(PERIODS=(u"Prior1Year", u"CurrentYear", u"他", u"なし")), dict(PERIODS=(u"CurrentYear", u"Prior1Year", u"その他", u"なし"))):
            self.assertNotEqual([], script_problems(self.seal, self._fake(**ov)), ov)
        self.assertNotEqual([], script_problems(self.seal.replace(u"cap 型 1 本 10", u"cap 型 1 本 11", 1), self._fake()))
        self.assertNotEqual([], script_problems(self.seal.replace(u"前年同期・前年度)", u"前年同期)", 1), self._fake()))
        self.assertNotEqual([], script_problems(self.seal.replace(u"%s|%s|T9_PRIOR_TO_CURRENT", u"%s|%s|T9_x", 1), self._fake()))

    def test_b_3_the_site_function_really_builds_its_random_stream_from_the_seal_seed(self):
        key, seed = u"bk", u"sd"
        with PS.yen_scan_on():
            got = seeds_used(lambda: PS.t9_all_sites(TEXT_C, REFS_C, seed, key))
        self.assertEqual([PS.SEED_T9 % (seed, key)], got)
        self.assertEqual(u"sd|bk|T9_PRIOR_TO_CURRENT", got[0])


class NotTouchedAndFrozenTest(unittest.TestCase):
    def test_c_1_inject_lib_and_engine_are_untouched_since_the_seal(self):
        self.assertEqual([], real_untouched_problems())

    def test_c_2_the_untouched_check_sees_a_changed_line(self):
        for rel in ("measure/inject.py", "measure/lib/numbers.py", "measure/lib/scales.py", "measure/lib/sites.py", "adapters/xbrl/extract.py", "core/py/audit_core/verify.py"):
            self.assertNotEqual([], untouched_problems(["1\t0\t%s%s" % (PREFIX, rel)]), rel)
        self.assertNotEqual([], untouched_problems(["0\t2\t%sadapters/xbrl/recipes.py" % PREFIX]))
        self.assertEqual([], untouched_problems([]))

    def test_d_1_previous_scripts_records_and_gates_are_byte_identical_to_the_seal_commit(self):
        self.assertEqual([], SGR.frozen_problems(rels=READ_ONLY_RELS, root=REPO, base=ROOT, seal_rel=SEAL_REL))

    def test_d_1b_the_j_script_record_and_gates_are_in_the_read_only_list(self):
        for rel in ("measure/xbrl_jtypes_2026-11-05.py", "fixtures/xbrl/jtypes/inject_2026-11-05.json", "tests/measure/test_xbrl_jtypes_seal.py", "tests/measure/test_xbrl_jtypes_result.py",
                    "measure/inject.py", "measure/lib/sites.py", "measure/xbrl_nscan_2026-11-05.py"):
            self.assertIn(rel, READ_ONLY_RELS)
        self.assertEqual(len(READ_ONLY_RELS), len(set(READ_ONLY_RELS)))

    def test_d_2_the_frozen_check_sees_a_changed_file_and_a_missing_one(self):
        self.assertNotEqual([], SGR.frozen_problems(rels=READ_ONLY_RELS + (SCRIPT_RELS[0],), root=REPO, base=ROOT, seal_rel=SEAL_REL))      # 封の commit に無い file
        self.assertNotEqual([], SGR.frozen_problems(rels=("measure/xbrl_nscan_2026-11-05.py", "measure/nonexistent_file.py"), root=REPO, base=ROOT, seal_rel=SEAL_REL))

    def test_d_3_the_frozen_check_goes_red_when_a_tracked_file_changes_after_the_seal(self):
        r = PR.Repo()
        r.put("measure/prev.py")
        r.put(SEAL_REL)
        r.commit("measure/prev.py", SEAL_REL)
        base = os.path.join(r.d, "audit-core")
        self.assertEqual([], SGR.frozen_problems(rels=("measure/prev.py",), root=r.d, base=base, seal_rel=SEAL_REL))
        with open(os.path.join(base, "measure/prev.py"), "a", encoding="utf-8") as fh:
            fh.write("x = 1\n")
        self.assertEqual([u"封の commit の blob と byte が違う: measure/prev.py"], SGR.frozen_problems(rels=("measure/prev.py",), root=r.d, base=base, seal_rel=SEAL_REL))

    def test_e_1_gate_files_do_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems(rels=tuple(r for r in GATE_RELS + (ROWS_REL,) if os.path.exists(os.path.join(ROOT, r)))))

    def test_e_2_the_reserved_name_check_sees_a_planted_name(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rels=("g.py",), base=d))
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_NOTES = 1\n")
            self.assertEqual([], reserved_problems(rels=("g.py",), base=d))

    def test_f_1_scripts_and_gates_carry_no_docid(self):
        for rel in SCRIPT_RELS + GATE_RELS + (ROWS_REL,):
            if os.path.exists(os.path.join(ROOT, rel)):
                self.assertIsNone(DOCID_RE.search(read(rel)), rel)

    def test_f_2_scripts_name_the_seal(self):
        for rel in SCRIPT_RELS:
            self.assertIn("XBRL_PERIOD_SWAP_SEAL_2026-11-06.md", read(rel), rel)


class WiringTest(unittest.TestCase):
    def test_w_1_the_script_uses_the_same_instances_as_the_j_script(self):
        self.assertEqual([], wiring_problems())
        self.assertIs(PS.RUN.N, N)
        self.assertIs(PS.IJ.N, N)
        self.assertIs(PS.TUNE.N, N)
        self.assertIs(PS.S.N, N)
        self.assertIs(PS.JT.NS, NS)
        self.assertIs(PS.JT.RM, RM)

    def test_w_2_another_instance_turns_the_wiring_check_red(self):
        for name in ("N", "S", "SC", "RUN", "IJ", "TUNE", "RM", "GEN", "NS"):
            fake = types.SimpleNamespace(**dict((k, getattr(PS, k)) for k in dir(PS) if not k.startswith("__")))
            setattr(fake, name, types.SimpleNamespace())
            self.assertNotEqual([], wiring_problems(fake), name)
        fake = types.SimpleNamespace(**dict((k, getattr(PS, k)) for k in dir(PS) if not k.startswith("__")))
        fake.yen_scan_on = lambda: None
        self.assertNotEqual([], wiring_problems(fake))
        fake = types.SimpleNamespace(**dict((k, getattr(PS, k)) for k in dir(PS) if not k.startswith("__")))
        fake.R = types.SimpleNamespace(__name__="adapters.xbrl.other")
        self.assertNotEqual([], wiring_problems(fake))
        self.assertEqual([], wiring_problems())

    def test_w_3_the_h_wiring_check_still_sees_a_swapped_n_or_key_check(self):
        old = NS.RUN.N
        NS.RUN.N = types.SimpleNamespace(__file__=N.__file__)
        try:
            self.assertNotEqual([], wiring_problems())
        finally:
            NS.RUN.N = old
        old = PS.GEN.key_leaks
        PS.GEN.key_leaks = NS.NF.ORIG_KEY_LEAKS
        try:
            self.assertNotEqual([], wiring_problems())
        finally:
            PS.GEN.key_leaks = old
        self.assertEqual([], wiring_problems())

    def test_w_4_the_switch_is_on_only_inside_the_with_and_goes_back_even_on_an_exception(self):
        self.assertFalse(getattr(N, FLAG))
        with PS.yen_scan_on():
            self.assertTrue(getattr(N, FLAG))
        self.assertFalse(getattr(N, FLAG))
        try:
            with PS.yen_scan_on():
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertFalse(getattr(N, FLAG))
        setattr(N, FLAG, True)                                           # すでに真だったら真のまま戻す(入れ子)
        try:
            with PS.yen_scan_on():
                pass
            self.assertTrue(getattr(N, FLAG))
        finally:
            setattr(N, FLAG, False)

    def test_w_5_the_key_check_for_this_seal_path_is_on_only_inside_its_with(self):
        long_path = PS.SEAL_REL
        self.assertEqual([], PS.key_leaks_ps(long_path))
        self.assertTrue(PS.key_leaks_ps(u"sk-" + u"a" * 30))
        old = PS.GEN.key_leaks
        with PS.key_check_ps():
            self.assertIs(PS.GEN.key_leaks, PS.key_leaks_ps)
        self.assertIs(PS.GEN.key_leaks, old)
        try:
            with PS.key_check_ps():
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertIs(PS.GEN.key_leaks, old)
        self.assertEqual([], wiring_problems())


class SiteTest(unittest.TestCase):
    u"""封 §1 の 1・2: T9 の site は条件を全部満たす (token, ref) だけ。複合も同じ経路。並べ替えは token の start の順 + 封の字の乱数。"""

    def sites(self, text=TEXT_C, refs=REFS_C):
        with PS.yen_scan_on():
            return PS.t9_stages_and_sites(text, refs)

    def test_g_1_a_prior_year_number_gets_the_current_value_written_in_the_original_form(self):
        stages, sites = self.sites()
        self.assertEqual(1, len(sites))
        s = sites[0]
        self.assertEqual((u"12億3,456", 123456.0, "T9_PRIOR_TO_CURRENT", u"複合"), (s["rendered"], s["new_value"], s["type"], PS.shape_of_token(s["token"])))
        self.assertEqual(u"9億7,000", s["token"].text)
        self.assertEqual(u"jppfs:NetSales@CurrentYearDuration", s["current"]["key"])
        self.assertEqual({"参照先が Prior1Year": 1, "同じ要素の CurrentYear が 1 件": 1, "単位が同じ・両方正・値が違う": 1, "site": 1}, dict(stages))
        inj = PS.build_t9(s, "x-T9-01")
        self.assertEqual((u"12億3,456", [s["token"].start, s["token"].end], 123456.0), (inj["replacement"], inj["span"], inj["new_value"]))
        tampered, placements = IJ.apply_edits(TEXT_C, [inj])
        self.assertEqual(u"前期の売上高は12億3,456万円でした。", tampered)                 # 単位の字は触らない
        self.assertEqual(TEXT_C, IJ.revert(tampered, [inj], placements, TEXT_C))

    def test_g_2_all_three_shapes_are_sites(self):
        text = u"前期の売上高は9億7,000万円、前期の利益は1,000万円、前期の費用は300百万円でした。"
        refs = REFS_C + [{"key": "jppfs:Profit@CurrentYearDuration", "value": 12340000.0, "unit": u"円", "label": u"利益"},
                         {"key": "jppfs:Profit@Prior1YearDuration", "value": 10000000.0, "unit": u"円", "label": u"利益"},
                         {"key": "jppfs:Cost@CurrentYearDuration", "value": 450000000.0, "unit": u"円", "label": u"費用"},
                         {"key": "jppfs:Cost@Prior1YearDuration", "value": 300000000.0, "unit": u"円", "label": u"費用"}]
        _st, sites = self.sites(text, refs)
        self.assertEqual({u"複合": 1, u"万だけ": 1, u"既存": 1}, dict(PS.shape_counter(sites)))
        self.assertEqual(sorted([u"12億3,456", u"1,234", u"450"]), sorted(s["rendered"] for s in sites))

    def test_g_3_each_condition_of_the_seal_removes_the_site(self):
        base = self.sites()[1]
        self.assertEqual(1, len(base))

        def refs_with(**ov):
            cur = dict(REFS_C[0])
            pri = dict(REFS_C[1])
            for k, v in ov.items():
                (cur if k.startswith("c_") else pri)[k[2:]] = v
            return [cur, pri]
        cases = {
            "value equal": refs_with(c_value=970000000.0),
            "cur not positive": refs_with(c_value=-1234560000.0),
            "cur zero": refs_with(c_value=0.0),                                         # 描いた字 0 は読み直しで一致する。両方正の条件だけが除く
            "ref not positive": refs_with(p_value=0.0),
            "unit differs": refs_with(c_unit=u"千円"),
            "cannot render back": refs_with(c_value=1234560100.0),                    # 万円の位で書けない当期の値(許容 1e-9 倍の外)
        }
        for name, refs in cases.items():
            self.assertEqual([], self.sites(refs=refs)[1], name)
        self.assertEqual([], self.sites(refs=[dict(REFS_C[0], key="jppfs:NetSales@Prior1YearDuration"), dict(REFS_C[1], key="jppfs:NetSales@Prior2YearDuration")])[1], "ref is not Prior1Year")
        self.assertEqual([], self.sites(refs=[REFS_C[0], dict(REFS_C[0], key="jppfs:NetSales@CurrentYearDuration"), REFS_C[1]])[1], "two current facts")
        self.assertEqual([], self.sites(refs=[REFS_C[1]])[1], "no current fact")
        # 当期の値の字が元の字と同じになる(rendered == token.text)ことは、値が違う (IJ.TOL より上) なら起きない。字の同一を直接確かめる
        stages, sites = self.sites()
        self.assertNotEqual(sites[0]["rendered"], sites[0]["token"].text)
        # 当期の文脈は Prior1Year を CurrentYear に替えた key(Prior1YearInstant → CurrentYearInstant など、接尾辞は保つ)
        refs_i = [{"key": "jppfs:Assets@CurrentYearInstant", "value": 1234560000.0, "unit": u"円", "label": u"資産"},
                  {"key": "jppfs:Assets@Prior1YearInstant", "value": 970000000.0, "unit": u"円", "label": u"資産"}]
        self.assertEqual(1, len(self.sites(refs=refs_i)[1]))
        refs_x = [dict(refs_i[0], key="jppfs:Assets@CurrentYearDuration"), refs_i[1]]                      # 接尾辞が違う
        self.assertEqual([], self.sites(refs=refs_x)[1])
        # 当期の値が前期の値と 0.5 円しか違わず、前期の数の字の形(万円の位)で描くと元の字と同じになる(rendered == token.text)なら site にしない(読み直しの許容の内)
        self.assertEqual([], self.sites(refs=[dict(REFS_C[0], value=970000000.5), REFS_C[1]])[1])
        # 描いた字を読み直した値が当期の値と 1 円違っても、許容(値の 1e-9 倍)の内なら site になる
        self.assertEqual(1, len(self.sites(refs=[dict(REFS_C[0], value=1234560001.0), REFS_C[1]])[1]))

    def test_g_3b_a_current_year_reference_is_not_a_site(self):
        text = u"売上高は12億3,456万円でした。"                                                         # 参照先が CurrentYear(T6 の側)
        self.assertEqual([], self.sites(text=text)[1])
        self.assertEqual(0, self.sites(text=text)[0]["参照先が Prior1Year"])

    def test_g_4_the_site_choice_does_not_use_the_engine_cue(self):
        calls = []
        real = PS.R._prior_cue
        PS.R._prior_cue = lambda *a, **k: calls.append(a) or True
        try:
            with PS.yen_scan_on():
                with_cue = PS.t9_all_sites(TEXT_C, REFS_C, u"sd", u"bk")
                PS.R._prior_cue = lambda *a, **k: calls.append(a) or False
                without_cue = PS.t9_all_sites(TEXT_C, REFS_C, u"sd", u"bk")
                text2 = u"売上高は9億7,000万円でした。"                                                    # 前期の手がかりが無い文でも site になる
                nocue = PS.t9_stages_and_sites(text2, REFS_C)
        finally:
            PS.R._prior_cue = real
        self.assertEqual([], calls)                                                                      # site の関数は手がかりを呼ばない
        self.assertEqual(with_cue[1][0]["rendered"], without_cue[1][0]["rendered"])
        self.assertEqual(1, len(nocue[1]))
        self.assertIs(PS.R._prior_cue, real)

    def test_g_5_sites_are_one_per_token_ordered_by_start_then_shuffled_by_the_seal_seed(self):
        text = u"".join(u"前期の科目%sは%s千円、" % (chr(0x41 + i), format(1000 + 7 * i, ",")) for i in range(12)) + u"でした。"
        refs = []
        for i in range(12):
            refs.append({"key": "jppfs:Item%d@Prior1YearDuration" % i, "value": float((1000 + 7 * i) * 1000), "unit": u"円", "label": u"科目%s" % chr(0x41 + i)})
            refs.append({"key": "jppfs:Item%d@CurrentYearDuration" % i, "value": float((2000 + 11 * i) * 1000), "unit": u"円", "label": u"科目%s" % chr(0x41 + i)})
        with PS.yen_scan_on():
            plain = PS.t9_sites(text, refs)
            allsites = PS.t9_all_sites(text, refs, u"sd", u"bk")[1]
            again = PS.t9_all_sites(text, refs, u"sd", u"bk")[1]
            other = PS.t9_all_sites(text, refs, u"sd", u"other")[1]
        self.assertEqual(12, len(plain))
        spans = [(s["token"].start, s["token"].end) for s in allsites]
        self.assertEqual(len(spans), len(set(spans)))                                             # 同じ token が 2 回 site にならない
        self.assertEqual(sorted(spans), sorted((s["token"].start, s["token"].end) for s in plain))
        expect = sorted(plain, key=lambda s: s["token"].start)
        random.Random(PS.SEED_T9 % (u"sd", u"bk")).shuffle(expect)                                 # token の start の順に並べてから封の字の乱数で並べ替える
        self.assertEqual([s["rendered"] for s in expect], [s["rendered"] for s in allsites])
        self.assertEqual([s["rendered"] for s in allsites], [s["rendered"] for s in again])        # 決定的
        self.assertNotEqual(spans, sorted(spans))                                                  # 並べ替えは実際に順序を変える
        self.assertNotEqual([s["rendered"] for s in allsites], [s["rendered"] for s in other])     # 本の名前で種が変わる

    def test_g_6_read_back_needs_one_token_and_the_unit_factor(self):
        with PS.yen_scan_on():
            self.assertEqual(97000.0 * 10000, PS.read_back(u"9億7,000", u"万円"))
            self.assertEqual(800.0 * 1e8, PS.read_back(u"800", u"億円"))
            self.assertEqual(12.0, PS.read_back(u"12", None))                                    # 単位の無い数
            self.assertIsNone(PS.read_back(u"x", u"万円"))
            self.assertIsNone(PS.read_back(u"12、34", u"万円"))                                    # token が 2 つ


class OrderTest(unittest.TestCase):
    def test_o_1_the_real_history_has_the_seal_before_the_script_and_the_gates(self):
        u"""script・門のどれかが未 commit なら赤(足した commit が無い)。"""
        self.assertEqual([], PR.order_problems(REPO, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [], SCRIPT_RELS + GATE_RELS + (ROWS_REL,)))


OTHERS = ["measure/a.py", "tests/g.py"]
SEALF = "docs/seal.md"


def order_of(r, seal_short):
    return PR.order_problems(r.d, PREFIX, SEALF, seal_short, [], OTHERS)


class OrderMutationTest(unittest.TestCase):
    def _repo(self, before_seal=(), after_seal_only=(), after=OTHERS):
        r = PR.Repo()
        for f in before_seal:
            r.put(f)
            r.commit(f)
        r.put(SEALF)
        s = r.commit(SEALF)
        for f in after_seal_only:
            r.put(f)
            r.commit(f)
        for f in after:
            r.put(f)
        if after:
            r.commit(*after)
        return r, s[:7]

    def test_p_1_a_correct_order_is_green(self):
        r, s = self._repo()
        self.assertEqual([], order_of(r, s))

    def test_p_2_a_script_before_the_seal_is_red(self):
        r, s = self._repo(before_seal=[OTHERS[0]], after=OTHERS[1:])
        self.assertIn("BEFORE_SEAL:" + OTHERS[0], order_of(r, s))

    def test_p_3_an_uncommitted_script_is_red_not_skipped(self):
        r, s = self._repo(after=OTHERS[:1])
        self.assertEqual(["UNCOMMITTED:" + OTHERS[1]], order_of(r, s))

    def test_p_4_a_wrong_seal_hash_is_red(self):
        r, _s = self._repo()
        self.assertIn("SEAL_NOT_THE_SEALED", order_of(r, "0000000"))


if __name__ == "__main__":
    unittest.main()
