# -*- coding: utf-8 -*-
"""封 docs/XBRL_INJECT_TYPES_SEAL_2026-11-05.md(J ― AI の文 200 本に注入の型を広げる: T2_UNIT・T6_PRIOR・T7_ROUND)の測定の門。封 §1・§5。

**この門が縛るもの**(結果の門 ``test_xbrl_jtypes_result.py`` は記録・文書・採用の判定を縛る)

1. 封の字: §1 の乱数の種の字 3 つ(T6_PRIOR・T7_ROUND・T7_ROUND|複合)・cap(型ごと 1 本 10)・土台(``RM.base_status_rb``)・profile(P29E・P30E)・型 3 つ・T5 は注入しない・
   §3 の予測の表が J-1〜J-10 の 10 行でどの行も予測と外れ方の欄を持つ・§4 の K-1〜K-4・§5 の path。封の字を 1 字変えると赤。
2. 封の字と script の定数が同じ: 種の字(script の定数 = 封の字。T6・T7 を呼ぶと実際にその字で乱数が作られる)・cap・型・profile・封の commit・path。
3. 触らない file は封の commit から 0 行: ``measure/inject.py``・``measure/lib``(numbers・scales・sites)・``core/``・``adapters/``。
   前の便(H・RB・N)の script・記録・門と、この便が読むだけの file は封の commit の blob と byte が同じ。
4. 順序: 封 edad5cd ⊏ script・門 2 本(記録・結果の文書の順序は結果の門が見る)。未 commit は赤(skip にしない)。
5. 配線: この script が NS(H の便の script)の同じ instance を使う(N・RUN・IJ・TUNE・S・SC)。切り替えは with の中だけ真(出るとき・例外のときも元に戻す)。
   複合を除く差し替えは with の中だけで、出たら元の関数に戻る。
6. 複合の写し: T6 は描いた字 + 単位を ``N.scan`` して値に戻して前期の値と一致を見る・T7 は like の単位で値 ± 1 を描く(符号は専用の乱数)。仕掛けの経路と母集団が混ざらない(同じ token が 2 回 site にならない)。
7. 新しい門が、既存の門が行頭の名前を数える変数名を行頭に置いていない。script・門に docID の字が無い。
8. 門の変異: 封の字・script の定数・numstat・順序・配線・複合の写しを 1 つずつ壊した標本で上の検査が赤になる。

この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import importlib.util
import os
import random
import re
import subprocess
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


SGR = load_module("tests/measure/test_xbrl_rmix_seal.py", "rmix_seal_gate_for_jtypes_seal")       # 前の便の封の門の部品(frozen_problems・RESERVED_PREFIXES)。門としては走らせない
PR = SGR.PR                                                                                      # order_problems・Repo・added_commits・git_in
JT = load_module("measure/xbrl_jtypes_2026-11-05.py", "jtypes_script_for_seal_gate")
NS = JT.NS
N, S, SC, RUN, IJ, TUNE, RM = JT.N, JT.S, JT.SC, JT.RUN, JT.IJ, JT.TUNE, JT.RM

SEAL_REL = JT.SEAL_REL
SEAL_COMMIT_SHORT = JT.SEAL_COMMIT
FLAG = JT.FLAG
SCRIPT_RELS = ("measure/xbrl_jtypes_2026-11-05.py",)
GATE_RELS = ("tests/measure/test_xbrl_jtypes_seal.py", "tests/measure/test_xbrl_jtypes_result.py")
RECORD_RELS = tuple(JT.REC_REL.values())
DOC_REL = JT.DOC_REL
#: 触らない file(封の commit から 0 行)
NOT_TOUCHED_RELS = ("measure/inject.py", "measure/lib", "adapters", "core")
#: この便が読むだけの前の便の script・記録・門(封の commit の blob と byte が同じでなければならない)
READ_ONLY_RELS = (
    "measure/inject.py", "measure/lib/numbers.py", "measure/lib/scales.py", "measure/lib/sites.py", "measure/tests/test_inject.py", "measure/tests/test_yen_scan.py",
    "measure/xbrl_nscan_2026-11-05.py", "fixtures/xbrl/nscan/offcheck_2026-11-05.json", "fixtures/xbrl/nscan/inject_2026-11-05.json",
    "tests/measure/test_xbrl_nscan_seal.py", "tests/measure/test_xbrl_nscan_result.py", "docs/XBRL_INJECT_SCAN_FIX_SEAL_2026-11-05.md",
    "measure/xbrl_rmix_2026-11-04.py", "measure/xbrl_rmix_regress97_2026-11-04.py",
    "fixtures/xbrl/rmix/ai200_2026-11-04.json", "fixtures/xbrl/rmix/inject_2026-11-04.json", "fixtures/xbrl/rmix/regress97_2026-11-04.json",
    "tests/measure/test_xbrl_rmix_seal.py", "tests/measure/test_xbrl_rmix_result.py",
    "measure/xbrl_numfix_2026-11-04.py", "measure/xbrl_numfix_regress97_2026-11-04.py", "measure/xbrl_numfix_shapes_2026-11-04.py",
    "fixtures/xbrl/numfix/ai200_2026-11-04.json", "fixtures/xbrl/numfix/inject_2026-11-04.json",
    "fixtures/xbrl/numfix/regress97_2026-11-04.json", "fixtures/xbrl/numfix/shapes_2026-11-04.json",
    "tests/measure/test_xbrl_numfix_result.py",
    "measure/xbrl_aiforms_gen_2026-11-03.py", "measure/xbrl_aiforms_run_2026-11-03.py", "measure/xbrl_p27_tune_2026-10-27.py",
    "fixtures/xbrl/aiforms/gen_2026-11-03.json", "fixtures/xbrl/aiforms/f5_gen_2026-11-03.json",
    "fixtures/xbrl/aiforms/claims_2026-11-03.json", "fixtures/xbrl/aiforms/f5_claims_2026-11-03.json",
    "fixtures/xbrl/aiforms/labels_2026-11-03.json", "fixtures/xbrl/aiforms/f5_labels_2026-11-03.json", "measure/SEED.json")
#: 既存の門が行頭の名前を数える変数名(新しい門はこれらを行頭に置かない。前の便の封の門と同じ一覧)
RESERVED_PREFIXES = SGR.RESERVED_PREFIXES
DOCID_RE = SGR.DOCID_RE
PRED_IDS = tuple("J-%d" % i for i in range(1, 11))
K_IDS = tuple("K-%d" % i for i in range(1, 5))
#: 封の字の要点(封に無ければ赤)
SEAL_PHRASES = (
    u"`S.t2_sites` は with の中だけ「`groups` が 2 つ以上の token を除く」版に差し替える",
    u"`TUNE.claim_for_p27(claims, inj, 差し替え後の単位)`",
    u"`inj[\"detail\"][\"unit_after\"]`",
    u"random.Random(\"%s|%s|T6_PRIOR\" % (seed, 本の名前))",
    u"random.Random(\"%s|%s|T7_ROUND\" % (seed, 本の名前))",
    u"random.Random(\"%s|%s|T7_ROUND|複合\" % (seed, 本の名前))",
    u"[+1, −1] を並べ替えて先に選び",
    u"`N.scan(描いた字 + 単位)`",
    u"cap は型ごと 1 本 10",
    u"土台 = 無改変の文で **P30E** が GROUNDED の claim(`RM.base_status_rb`)",
    u"比較 = P29E",
    u"**T5 は注入しない**",
    u"切り替え `yen_scan_2026_11_05`",
    u"`measure/inject.py`・`measure/lib/sites.py`・`measure/lib/numbers.py`・`measure/lib/scales.py`・`core/`・`adapters/`・前の便の script と記録は 0 行",
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
        ids = table_ids(seal, "## §3", "## §4", r"^\| (J-\d+) \| (.*) \|$")
        sec = seal[seal.index("## §3"):seal.index("## §4")]
        sec4 = seal[seal.index("## §4"):seal.index("## §5")]
        sec5 = seal[seal.index("## §5"):seal.index("## §6")]
    except ValueError:
        return [u"封の節(§3・§4・§5・§6)が揃っていない"]
    if ids != list(PRED_IDS):
        out.append(u"封 §3 の表が J-1〜J-10 の 10 行でない: %s" % ids)
    for line in sec.splitlines():
        m = re.match(r"^\| (J-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            if len(cells) < 3 or any(not c.strip() for c in cells[:3]):
                out.append(u"封 §3 の %s の欄(欄・予測・外れ方)が埋まっていない" % m.group(1))
    got_k = re.findall(r"^- (K-\d):", sec4, re.M)
    if got_k != list(K_IDS):
        out.append(u"封 §4 の K-1〜K-4 が揃っていない: %s" % got_k)
    for rel in SCRIPT_RELS + GATE_RELS + RECORD_RELS:
        if rel not in sec5:
            out.append(u"封 §5 に path が無い: %s" % rel)
    if DOC_REL not in seal[seal.index("### §2-1"):seal.index("### §2-2")]:
        out.append(u"封 §2-1 に結果の文書の path が無い: %s" % DOC_REL)
    for ph in SEAL_PHRASES:
        if ph not in seal:
            out.append(u"封に規則の要点の字が無い: %s" % ph)
    return out


def seal_seed_forms(seal):
    u"""封の字から乱数の種の字(``random.Random("...")`` の中。出る順)を読む。"""
    return re.findall(r"random\.Random\(\"([^\"]+)\" % \(seed, 本の名前\)\)", seal)


def seal_cap(seal):
    m = re.search(r"cap は型ごと 1 本 (\d+)", seal)
    return int(m.group(1)) if m else None


def seal_types(seal):
    return re.findall(r"\*\*(T\d_[A-Z]+)\*\*", seal[seal.index("## §1"):seal.index("## §2")])


# ---------------------------------------------------------------- 2. 封の字と script の定数
def script_problems(seal, jt=None):
    u"""封の字と script の定数が同じか。jt = script の module(試験が壊した写しを渡す)。"""
    jt = jt or JT
    out = []
    forms = seal_seed_forms(seal)
    want = [jt.SEED_T6, jt.SEED_T7, jt.SEED_T7_COMPOUND]
    if forms != want:
        out.append(u"乱数の種の字が封の字と違う: 封 %r / script %r" % (forms, want))
    if seal_cap(seal) != jt.RUN.INJECT_CAP:
        out.append(u"cap が封の字(型ごと 1 本 10)と違う")
    if list(jt.J_TYPES) != ["T2_UNIT", "T6_PRIOR", "T7_ROUND"] or seal_types(seal)[:3] != list(jt.J_TYPES):
        out.append(u"型が封の字(T2_UNIT・T6_PRIOR・T7_ROUND)と違う")
    if tuple(jt.INJECT_PROFILES) != ("P29E", "P30E"):
        out.append(u"profile が (P29E, P30E) でない")
    if jt.SEAL_REL != SEAL_REL or jt.SEAL_COMMIT != SEAL_COMMIT_SHORT or jt.FLAG != "yen_scan_2026_11_05":
        out.append(u"封の path・commit・切り替えの名前が違う")
    if tuple(jt.SHAPES) != (u"既存", u"万だけ", u"複合"):
        out.append(u"形が 既存 / 万だけ / 複合 でない")
    if jt.BASE_WORD != u"無改変の文で P30E が GROUNDED の claim":
        out.append(u"土台の字が P30E が GROUNDED の claim でない")
    return out


REAL_RANDOM = random.Random


class RecordingRandom(REAL_RANDOM):
    u"""``random.Random`` の種の字を記録する(段 2 の乱数が封の字で作られるかを見る)。"""
    seen = []

    def __init__(self, x=None):
        RecordingRandom.seen.append(x)
        REAL_RANDOM.__init__(self, x)


def seeds_used(fn):
    u"""``fn()`` の間 ``JT.random.Random`` を記録版に替えて、作られた乱数の種の字の列を返す(戻す)。"""
    real = JT.random.Random
    RecordingRandom.seen = []
    JT.random.Random = RecordingRandom
    try:
        fn()
    finally:
        JT.random.Random = real
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
    return untouched_problems([x for x in PR.git_in(root, "diff", "--numstat", sh, "--", *paths)[1].splitlines() if x])


# ---------------------------------------------------------------- 7. 行頭の名前
def reserved_problems(rels=GATE_RELS, base=ROOT):
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
    u"""この script が NS の同じ instance を使っているか + NS の配線の検査。問題の列。"""
    jt = script or JT
    out = list(jt.wiring_problems())
    for label, a, b in (("N", jt.N, jt.NS.N), ("S", jt.S, jt.NS.S), ("SC", jt.SC, jt.NS.SC), ("RUN", jt.RUN, jt.NS.RUN), ("IJ", jt.IJ, jt.NS.IJ),
                        ("TUNE", jt.TUNE, jt.NS.TUNE), ("RM", jt.RM, jt.NS.RM), ("GEN", jt.GEN, jt.NS.GEN)):
        if a is not b:
            out.append(u"%s がこの script と NS で同じ instance でない" % label)
    if jt.yen_scan_on is not jt.NS.yen_scan_on:
        out.append(u"切り替えの with が NS のものでない")
    if jt.FLAG != jt.NS.FLAG:
        out.append(u"切り替えの名前が NS と違う")
    return out


# ---------------------------------------------------------------- 6. 複合の写しの標本
TEXT_C = u"売上高は12億3,456万円でした。"
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
        j10 = [i for i, ln in enumerate(lines) if ln.startswith("| J-10 |")]
        self.assertEqual(1, len(j10))
        self.assertNotEqual([], seal_problems("\n".join(lines[:j10[0]] + lines[j10[0] + 1:])))                       # 10 行が 9 行
        j5 = [i for i, ln in enumerate(lines) if ln.startswith("| J-5 |")][0]
        cells = lines[j5].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:j5] + [" | ".join(cells[:2]) + " |"] + lines[j5 + 1:])))   # 外れ方の欄が無い
        self.assertNotEqual([], seal_problems("\n".join(lines[:j5] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[j5 + 1:])))   # 予測の欄が空
        k4 = [i for i, ln in enumerate(lines) if ln.startswith("- K-4:")]
        self.assertEqual(1, len(k4))
        self.assertNotEqual([], seal_problems("\n".join(lines[:k4[0]] + lines[k4[0] + 1:])))
        self.assertNotEqual([], seal_problems(self.seal.replace("measure/xbrl_jtypes_2026-11-05.py", "measure/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("inject_2026-11-05.json", "inject_x.json")))
        self.assertNotEqual([], seal_problems(self.seal.replace("fixtures/xbrl/jtypes/", "fixtures/xbrl/x/")))
        self.assertNotEqual([], seal_problems(self.seal.replace("XBRL_INJECT_TYPES_RESULT_2026-11-05.md", "x.md")))
        self.assertNotEqual([], seal_problems(self.seal.replace("## §4", "## 四", 1)))

    def test_a_4_the_seeds_cap_and_types_are_read_from_the_seal(self):
        self.assertEqual([JT.SEED_T6, JT.SEED_T7, JT.SEED_T7_COMPOUND], seal_seed_forms(self.seal))
        self.assertEqual(10, seal_cap(self.seal))
        self.assertEqual(["T2_UNIT", "T6_PRIOR", "T7_ROUND"], seal_types(self.seal)[:3])
        self.assertEqual(2, len(seal_seed_forms(self.seal.replace(u"random.Random(\"%s|%s|T7_ROUND|複合\" % (seed, 本の名前))", u"x", 1))))
        self.assertEqual(11, seal_cap(self.seal.replace(u"cap は型ごと 1 本 10", u"cap は型ごと 1 本 11", 1)))
        self.assertIsNone(seal_cap(self.seal.replace(u"cap は型ごと 1 本 10", u"cap は 10", 1)))


class ScriptMatchesSealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_b_1_the_script_agrees_with_the_seal(self):
        self.assertEqual([], script_problems(self.seal))

    def _fake(self, **ov):
        d = dict(SEED_T6=JT.SEED_T6, SEED_T7=JT.SEED_T7, SEED_T7_COMPOUND=JT.SEED_T7_COMPOUND, RUN=JT.RUN, J_TYPES=JT.J_TYPES, INJECT_PROFILES=JT.INJECT_PROFILES, SEAL_REL=JT.SEAL_REL,
                 SEAL_COMMIT=JT.SEAL_COMMIT, FLAG=JT.FLAG, SHAPES=JT.SHAPES, BASE_WORD=JT.BASE_WORD)
        d.update(ov)
        return types.SimpleNamespace(**d)

    def test_b_2_a_changed_script_constant_turns_it_red(self):
        self.assertEqual([], script_problems(self.seal, self._fake()))
        for ov in (dict(SEED_T6=u"%s|%s|T6_PRIORx"), dict(SEED_T7=u"%s|%s|T7_ROUND "), dict(SEED_T7_COMPOUND=u"%s|%s|T7_ROUND|compound"),
                   dict(RUN=types.SimpleNamespace(INJECT_CAP=11)), dict(J_TYPES=("T2_UNIT", "T6_PRIOR")), dict(J_TYPES=("T2_UNIT", "T6_PRIOR", "T7_ROUNDX")),
                   dict(INJECT_PROFILES=("P28E", "P29E")), dict(SEAL_COMMIT="0000000"), dict(FLAG="compound_yen_2026_11_05"), dict(SHAPES=(u"既存", u"万だけ")),
                   dict(BASE_WORD=u"無改変の文で P29E が GROUNDED の claim")):
            self.assertNotEqual([], script_problems(self.seal, self._fake(**ov)), ov)
        self.assertNotEqual([], script_problems(self.seal.replace(u"cap は型ごと 1 本 10", u"cap は型ごと 1 本 11", 1), self._fake()))
        self.assertNotEqual([], script_problems(self.seal.replace(u"%s|%s|T7_ROUND|複合", u"%s|%s|T7_ROUND|x", 1), self._fake()))

    def test_b_3_the_site_functions_really_build_their_random_streams_from_the_seal_seeds(self):
        key, seed = u"bk", u"sd"
        with JT.yen_scan_on():
            got6 = seeds_used(lambda: JT.t6_all_sites(TEXT_C, REFS_C, seed, key))
            got7 = seeds_used(lambda: JT.t7_all_sites(TEXT_C, REFS_C, seed, key))
        self.assertEqual([JT.SEED_T6 % (seed, key)], got6)
        self.assertEqual([JT.SEED_T7 % (seed, key), JT.SEED_T7_COMPOUND % (seed, key)], got7)
        self.assertNotEqual(got7[0], got7[1])                                                  # 仕掛けの乱数と複合の写しの乱数は別


class NotTouchedAndFrozenTest(unittest.TestCase):
    def test_c_1_inject_lib_and_engine_are_untouched_since_the_seal(self):
        self.assertEqual([], real_untouched_problems())

    def test_c_2_the_untouched_check_sees_a_changed_line(self):
        for rel in ("measure/inject.py", "measure/lib/numbers.py", "measure/lib/scales.py", "measure/lib/sites.py", "adapters/xbrl/extract.py", "core/py/audit_core/verify.py"):
            self.assertNotEqual([], untouched_problems(["1\t0\t%s%s" % (PREFIX, rel)]), rel)
        self.assertNotEqual([], untouched_problems(["0\t2\t%sadapters/xbrl/extract.py" % PREFIX]))
        self.assertEqual([], untouched_problems([]))

    def test_d_1_previous_scripts_records_and_gates_are_byte_identical_to_the_seal_commit(self):
        self.assertEqual([], SGR.frozen_problems(rels=READ_ONLY_RELS, root=REPO, base=ROOT, seal_rel=SEAL_REL))

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
        self.assertEqual([], reserved_problems(rels=tuple(r for r in GATE_RELS if os.path.exists(os.path.join(ROOT, r)))))

    def test_e_2_the_reserved_name_check_sees_a_planted_name(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rels=("g.py",), base=d))
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_NOTES = 1\n")
            self.assertEqual([], reserved_problems(rels=("g.py",), base=d))

    def test_f_1_scripts_and_gates_carry_no_docid(self):
        for rel in SCRIPT_RELS + GATE_RELS:
            if os.path.exists(os.path.join(ROOT, rel)):
                self.assertIsNone(DOCID_RE.search(read(rel)), rel)

    def test_f_2_scripts_name_the_seal(self):
        for rel in SCRIPT_RELS:
            self.assertIn("XBRL_INJECT_TYPES_SEAL_2026-11-05.md", read(rel), rel)


class WiringTest(unittest.TestCase):
    def test_w_1_the_script_uses_the_same_instances_as_the_h_script(self):
        self.assertEqual([], wiring_problems())
        self.assertIs(JT.RUN.N, N)
        self.assertIs(JT.IJ.N, N)
        self.assertIs(JT.TUNE.N, N)
        self.assertIs(JT.S.N, N)
        self.assertIs(JT.NS.RM, RM)

    def test_w_2_another_instance_turns_the_wiring_check_red(self):
        for name in ("N", "S", "SC", "RUN", "IJ", "TUNE", "RM"):
            fake = types.SimpleNamespace(**dict((k, getattr(JT, k)) for k in dir(JT) if not k.startswith("__")))
            setattr(fake, name, types.SimpleNamespace())
            self.assertNotEqual([], wiring_problems(fake), name)
        fake = types.SimpleNamespace(**dict((k, getattr(JT, k)) for k in dir(JT) if not k.startswith("__")))
        fake.yen_scan_on = lambda: None
        self.assertNotEqual([], wiring_problems(fake))
        self.assertEqual([], wiring_problems())

    def test_w_3_the_h_wiring_check_still_sees_a_swapped_n_or_key_check(self):
        old = NS.RUN.N
        NS.RUN.N = types.SimpleNamespace(__file__=N.__file__)
        try:
            self.assertNotEqual([], wiring_problems())
        finally:
            NS.RUN.N = old
        old = JT.GEN.key_leaks
        JT.GEN.key_leaks = NS.NF.ORIG_KEY_LEAKS
        try:
            self.assertNotEqual([], wiring_problems())
        finally:
            JT.GEN.key_leaks = old
        self.assertEqual([], wiring_problems())

    def test_w_4_the_switch_is_on_only_inside_the_with_and_goes_back_even_on_an_exception(self):
        self.assertFalse(getattr(N, FLAG))
        with JT.yen_scan_on():
            self.assertTrue(getattr(N, FLAG))
            with JT.yen_scan_off():
                self.assertFalse(getattr(N, FLAG))
            self.assertTrue(getattr(N, FLAG))
        self.assertFalse(getattr(N, FLAG))
        for cm in (JT.yen_scan_on, JT.yen_scan_off):
            try:
                with cm():
                    raise RuntimeError("x")
            except RuntimeError:
                pass
            self.assertFalse(getattr(N, FLAG))
        setattr(N, FLAG, True)                                           # すでに真だったら真のまま戻す(入れ子)
        try:
            with JT.yen_scan_on():
                pass
            self.assertTrue(getattr(N, FLAG))
            with JT.yen_scan_off():
                pass
            self.assertTrue(getattr(N, FLAG))
        finally:
            setattr(N, FLAG, False)

    def test_w_5_the_without_compound_swap_keeps_only_non_compound_tokens_and_is_put_back(self):
        text = u"売上高は12億3,456万円、利益は10億円、費用は1,234万円、粗利は5,000千円でした。"
        refs = [{"key": "k1@CurrentYearDuration", "value": 1234560000.0, "unit": u"円", "label": u"売上高"}, {"key": "k2@CurrentYearDuration", "value": 12340000.0, "unit": u"円", "label": u"費用"},
                {"key": "k3@CurrentYearDuration", "value": 1000000000.0, "unit": u"円", "label": u"利益"}, {"key": "k4@CurrentYearDuration", "value": 5000000.0, "unit": u"円", "label": u"粗利"}]
        with JT.yen_scan_on():
            for name, tok_of in (("t2_sites", lambda x: x["token"]), ("identified_sites", lambda x: x[0]), ("data_bearing_sites", lambda x: x[0])):
                orig = getattr(S, name)
                full = set(tok_of(x).text for x in orig(text, refs))
                self.assertIn(u"12億3,456", full, name)
                with JT.without_compound(name) as o:
                    self.assertIs(o, orig)
                    self.assertIsNot(getattr(S, name), orig)
                    got = set(tok_of(x).text for x in getattr(S, name)(text, refs))
                self.assertEqual(full - {u"12億3,456"}, got, name)
                self.assertIn(u"1,234", got, name)                          # 万だけ は残る
                self.assertIs(getattr(S, name), orig)
                try:
                    with JT.without_compound(name):
                        raise RuntimeError("x")
                except RuntimeError:
                    pass
                self.assertIs(getattr(S, name), orig)

    def test_w_6_the_key_check_for_this_seal_path_is_on_only_inside_its_with(self):
        long_path = JT.SEAL_REL
        self.assertTrue(NS.NF.ORIG_KEY_LEAKS(long_path, None, True))                 # 封の path は 32 字を超える英数字の連なりで素の検査に当たる
        self.assertEqual([], JT.key_leaks_j(long_path))
        self.assertTrue(JT.key_leaks_j(u"sk-" + u"a" * 30))
        old = JT.GEN.key_leaks
        with JT.key_check_j():
            self.assertIs(JT.GEN.key_leaks, JT.key_leaks_j)
        self.assertIs(JT.GEN.key_leaks, old)
        self.assertEqual([], wiring_problems())


class CompoundCopyTest(unittest.TestCase):
    u"""封 §0-1 の 3・§1 の 2・3: 複合 token の T6・T7 は script の写しで作る。仕掛けの経路と母集団が混ざらない。"""

    def test_g_1_the_t6_copy_draws_the_prior_value_back_through_the_scan(self):
        with JT.yen_scan_on():
            tok = [t for t in N.scan(TEXT_C) if t.groups is not None and len(t.groups) >= 2][0]
            self.assertEqual(u"12億3,456", tok.text)
            self.assertEqual([], IJ.t6_sites(TEXT_C, REFS_C))                       # 仕掛けの経路は複合で site を作れない(描いた字を float に戻せない)
            sites = JT.t6_compound_sites(TEXT_C, REFS_C)
            self.assertEqual(1, len(sites))
            s = sites[0]
            self.assertEqual((u"9億7,000", 97000.0, "T6_PRIOR"), (s["rendered"], s["new_value"], s["type"]))
            self.assertEqual(970000000.0, JT.rendered_back(s["rendered"], tok.unit))
            inj = IJ.build_t6(s, REFS_C, None)
            self.assertEqual((u"9億7,000", [tok.start, tok.end]), (inj["replacement"], inj["span"]))
            tampered, _pl = IJ.apply_edits(TEXT_C, [dict(inj, id="x")])
            self.assertEqual(u"売上高は9億7,000万円でした。", tampered)

    def test_g_2_the_t6_copy_refuses_a_prior_it_cannot_write_back(self):
        refs = [REFS_C[0], dict(REFS_C[1], value=970000001.0)]                       # 万円の位で書けない前期の値
        with JT.yen_scan_on():
            self.assertEqual([], JT.t6_compound_sites(TEXT_C, refs))
            refs2 = [REFS_C[0], dict(REFS_C[1], unit=u"千円")]                       # 単位が違う
            self.assertEqual([], JT.t6_compound_sites(TEXT_C, refs2))
            refs3 = [REFS_C[0], dict(REFS_C[1], value=REFS_C[0]["value"])]           # 値が同じ
            self.assertEqual([], JT.t6_compound_sites(TEXT_C, refs3))
            refs4 = [REFS_C[0], dict(REFS_C[1], key="jppfs:NetSales@Prior2YearDuration")]    # 前期の枠が無い
            self.assertEqual([], JT.t6_compound_sites(TEXT_C, refs4))

    def test_g_2b_the_copy_refuses_a_token_whose_own_fact_is_not_a_current_year_fact(self):
        refs = [{"key": "jppfs:NetSales@Prior1YearDuration", "value": 1234560000.0, "unit": u"円", "label": u"売上高"},
                {"key": "jppfs:NetSales@Prior1Yearuration", "value": 970000000.0, "unit": u"円", "label": u"売上高"}]       # 前期の fact を当期の枠とみなして『前期の前期』を引かない
        with JT.yen_scan_on():
            self.assertEqual([], JT.t6_compound_sites(TEXT_C, refs))
            self.assertEqual(1, len(JT.t6_compound_sites(TEXT_C, REFS_C)))

    def test_g_2c_a_compound_token_that_the_h_route_can_also_write_becomes_a_site_only_once(self):
        u"""先頭の位が落ちる形(1億500万円 → 前期 9700万円)は仕掛けの経路でも site になる。複合を除く差し替えが効いていれば写しだけの 1 件。"""
        text = u"売上高は1億500万円でした。"
        refs = [{"key": "jppfs:NetSales@CurrentYearDuration", "value": 105000000.0, "unit": u"円", "label": u"売上高"},
                {"key": "jppfs:NetSales@Prior1YearDuration", "value": 97000000.0, "unit": u"円", "label": u"売上高"}]
        with JT.yen_scan_on():
            self.assertEqual(1, len(IJ.t6_sites(text, refs)))                       # 仕掛けの経路は複合でも先頭の位が落ちる形だけ site にする
            sites = JT.t6_all_sites(text, refs, u"sd", u"bk")
            self.assertEqual(1, len(sites))
            self.assertEqual((u"9700", 9700.0), (sites[0]["rendered"], sites[0]["new_value"]))
            self.assertLess(NS.groups_in(sites[0]["rendered"]), len(sites[0]["token"].groups))
            self.assertEqual(1, len(JT.t6_compound_sites(text, refs)))              # 写しが作った 1 件(仕掛けの経路の 1 件は複合を除く差し替えで落ちた)

    def test_g_3_rendered_back_needs_one_token_that_covers_the_whole_string(self):
        with JT.yen_scan_on():
            self.assertEqual(97000.0 * 10000, JT.rendered_back(u"9億7,000", u"万円"))
            self.assertIsNone(JT.rendered_back(u"9億7,000", u"千円"))               # 単位が合わない
            self.assertIsNone(JT.rendered_back(u"x", u"万円"))
            self.assertIsNone(JT.rendered_back(u"x9億7,000", u"万円"))             # 描いた字の前に余分な字が付くと全体を覆わない
            self.assertEqual(800.0 * 1e8, JT.rendered_back(u"800", u"億円"))

    def test_g_4_the_t7_copy_moves_the_smallest_group_by_one_and_picks_the_sign_first(self):
        with JT.yen_scan_on():
            signs = set()
            for i in range(40):
                rng = random.Random("probe%d" % i)
                sites = JT.t7_compound_sites(TEXT_C, REFS_C, rng)
                self.assertEqual(1, len(sites))
                s = sites[0]
                self.assertIn((s["delta"], s["rendered"]), ((1, u"12億3,457"), (-1, u"12億3,455")))
                self.assertEqual(123456.0 + s["delta"], s["new_value"])
                signs.add(s["delta"])
            self.assertEqual({1, -1}, signs)                                       # 符号は乱数で決まる
            rng = random.Random("probe3")
            first = list([1, -1])
            random.Random("probe3").shuffle(first)
            self.assertEqual(first[0], JT.t7_compound_sites(TEXT_C, REFS_C, rng)[0]["delta"])      # 先に選んだ側
            # 先に選んだ側が refs の値と一致するときは逆側
            for i in range(40):
                order = [1, -1]
                random.Random("q%d" % i).shuffle(order)
                if order[0] == 1:
                    refs = REFS_C + [{"key": "x@CurrentYearDuration", "value": 1234570000.0, "unit": u"円", "label": u"他"}]
                    s = JT.t7_compound_sites(TEXT_C, refs, random.Random("q%d" % i))
                    self.assertEqual([-1], [x["delta"] for x in s])
                    break
            else:
                self.fail("+1 を先に選ぶ乱数が見つからない")

    def test_g_5_the_t7_copy_refuses_a_value_whose_group_count_would_drop_or_that_becomes_zero(self):
        text = u"売上高は1億0万円でした。"        # 値は 10000(億 1 + 万 0)。-1 は 9999 = 先頭の位が落ちる
        refs = [{"key": "k@CurrentYearDuration", "value": 100000000.0, "unit": u"円", "label": u"売上高"}]
        with JT.yen_scan_on():
            toks = [t for t in N.scan(text) if t.groups is not None]
            if toks and len(toks[0].groups) >= 2:
                for i in range(20):
                    for s in JT.t7_compound_sites(text, refs, random.Random("z%d" % i)):
                        self.assertEqual(1, s["delta"])                           # -1 は桁の数が減るので作らない
                        self.assertEqual(NS.groups_in(s["rendered"]), len(toks[0].groups))

    def test_g_6_the_two_populations_do_not_overlap_in_the_site_lists(self):
        text = u"売上高は12億3,456万円でした。粗利益は1,234万円でした。"
        refs = REFS_C + [{"key": "jppfs:GrossProfit@CurrentYearDuration", "value": 12340000.0, "unit": u"円", "label": u"粗利益"},
                         {"key": "jppfs:GrossProfit@Prior1YearDuration", "value": 11000000.0, "unit": u"円", "label": u"粗利益"}]
        with JT.yen_scan_on():
            for fn in (JT.t6_all_sites, JT.t7_all_sites):
                sites = fn(text, refs, u"sd", u"bk")
                spans = [(s["token"].start, s["token"].end) for s in sites]
                self.assertEqual(len(spans), len(set(spans)), fn.__name__)         # 同じ token が 2 回 site にならない
                shapes = sorted(JT.shape_of_token(s["token"]) for s in sites)
                self.assertEqual([u"万だけ", u"複合"], shapes, fn.__name__)         # 仕掛けの経路は 万だけ、写しは 複合
            pick = lambda sites: [(s["token"].start, s["rendered"]) for s in sites]
            self.assertEqual(pick(JT.t6_all_sites(text, refs, u"sd", u"bk")), pick(JT.t6_all_sites(text, refs, u"sd", u"bk")))      # 決定的
            self.assertEqual(pick(JT.t7_all_sites(text, refs, u"sd", u"bk")), pick(JT.t7_all_sites(text, refs, u"sd", u"bk")))


class OrderTest(unittest.TestCase):
    def test_o_1_the_real_history_has_the_seal_before_the_script_and_the_gates(self):
        u"""script・門のどれかが未 commit なら赤(足した commit が無い)。"""
        self.assertEqual([], PR.order_problems(REPO, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [], SCRIPT_RELS + GATE_RELS))


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
