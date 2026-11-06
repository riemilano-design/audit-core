# -*- coding: utf-8 -*-
"""封 docs/XBRL_PERIOD_SWAP_IDMAP_SEAL_2026-11-06.md(T9 の第 2 便 ― 注入後の claim を基準の claim の id で引く対応付け)の測定の門。封 §1・§2-1・§5。

**この門が縛るもの**(結果の門 ``test_xbrl_pswap_idmap_result.py`` は記録・文書・採用の判定・行の欄・対応付けを縛る)

1. 封の字: §1 の対応の 3 つの条件((ア)(イ)(ウ))・旧の対応付け・T9 の script を importlib で読み込むこと・§3 の予測の表が Q-1〜Q-10 の 10 行でどの行も予測と外れ方の欄を持つ・§4 の K-1〜K-4・§5 の path。封の字を 1 字変えると赤。
2. 封の字と script の定数が同じ: 対応の 3 条件の名前・封の path と commit・T9 の封の乱数の種の字(この script が T9 の定数をそのまま使う)・cap・型・profile・土台・形・前の便の path。
3. 触らない file は封の commit から 0 行: ``measure/inject.py``・``measure/lib``・``core/``・``adapters/``。前の便(J・H・RB・N・**T9**)の script・記録・門は封の commit の blob と byte が同じ。
4. 順序: 封 ec00fa1 ⊏ script・門 2 本(記録・結果の文書の順序は結果の門が見る)。未 commit は赤(skip にしない)。
5. 配線: この script が T9 の script の同じ instance(NS・N・RUN・IJ・TUNE・S・SC・RM・GEN)を使う。切り替えは with の中だけ真。
   T9 の site の関数・行の欄の関数を**そのまま使う**(この script が同じ名前の関数を定義していない・T9 の関数を差し替えるとこの script の行が変わる = 届いている)。
6. 新しい門が、既存の門が行頭の名前を数える変数名を行頭に置いていない。script・門に docID の字が無い。
7. 門の変異: 封の字・script の定数・numstat・順序・配線・T9 の関数の差し替えを 1 つずつ壊した標本で上の検査が赤になる。

この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import ast
import importlib.util
import os
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


PSG = load_module("tests/measure/test_xbrl_pswap_seal.py", "pswap_seal_gate_for_idmap_seal")     # T9 の封の門の部品(READ_ONLY_RELS・封の字を読む関数)。門としては走らせない
JSG = PSG.JSG
SGR = PSG.SGR
PR = PSG.PR
PI = load_module("measure/xbrl_pswap_idmap_2026-11-06.py", "pswap_idmap_script_for_seal_gate")
PS = PI.PS
NS = PI.NS
N, S, SC, RUN, IJ, TUNE, RM = PI.N, PI.S, PI.SC, PI.RUN, PI.IJ, PI.TUNE, PI.RM

SEAL_REL = PI.SEAL_REL
SEAL_COMMIT_SHORT = "ec00fa1"                     # 封の commit(literal に留める。script の定数と違えば script_problems が赤)
T9_SEAL_REL = PS.SEAL_REL
FLAG = PI.FLAG
SCRIPT_RELS = ("measure/xbrl_pswap_idmap_2026-11-06.py",)
GATE_RELS = ("tests/measure/test_xbrl_pswap_idmap_seal.py", "tests/measure/test_xbrl_pswap_idmap_result.py")
RECORD_RELS = tuple(PI.REC_REL.values())
DOC_REL = PI.DOC_REL
#: 触らない file(封の commit から 0 行)
NOT_TOUCHED_RELS = ("measure/inject.py", "measure/lib", "adapters", "core")
#: この便が読むだけの前の便の script・記録・門(封の commit の blob と byte が同じでなければならない)。T9 の便の分 + T9 の script・記録・門・文書
READ_ONLY_RELS = PSG.READ_ONLY_RELS + (
    "measure/xbrl_pswap_2026-11-06.py", "fixtures/xbrl/pswap/inject_2026-11-06.json",
    "tests/measure/test_xbrl_pswap_seal.py", "tests/measure/test_xbrl_pswap_result.py", "tests/measure/test_xbrl_jtypes_rows.py",
    "docs/XBRL_PERIOD_SWAP_SEAL_2026-11-06.md", "docs/XBRL_PERIOD_SWAP_RESULT_2026-11-06.md")
RESERVED_PREFIXES = SGR.RESERVED_PREFIXES
DOCID_RE = SGR.DOCID_RE
PRED_IDS = tuple("Q-%d" % i for i in range(1, 11))
K_IDS = tuple("K-%d" % i for i in range(1, 5))
#: 対応の 3 つの条件の名前(literal に留める。script の定数と違えば script_problems が赤)
CONDS_PIN = (u"ア id の claim が在る", u"イ 値が注入した値", u"ウ span に差し替えの字")
#: T9 の site・行の欄の関数(この script は同じ名前の関数を定義せず、T9 の module の関数を呼ぶ)
T9_FUNCS = ("t9_all_sites", "build_t9", "engine_cue", "has_prior_word", "pointer_period", "reached_of", "shape_of_token")
#: 封の字の要点(封に無ければ赤)
SEAL_PHRASES = (
    u"注入後の文の claim のうち `id == 基準の claim の id` の claim を c とし",
    u"(ア) c が在る",
    u"(イ) `c[\"value\"]` が在り円に直した値が注入した値と `TUNE.same_number` で一致",
    u"(ウ) `c[\"span\"]` に差し替えの字 rendered が在る",
    u"の 3 つを全部満たすときだけ対応が付く(P29E・P30E それぞれ)",
    u"`TUNE.claim_for_p27` の結果(付いた / 付かない。付いたら id が同じか)も持つ",
    u"判定には使わない",
    u"`TUNE.claim_for_p27` そのものは変えない",
    u"土台 = 無改変で P30E が GROUNDED の claim、比較 = P29E",
    u"T9 の `xbrl_pswap_2026-11-06.py` を importlib で読み込み",
    u"T9 の記録 `fixtures/xbrl/pswap/inject_2026-11-06.json` を読んで照らす",
    u"engine の手がかりは T9 と同じく `recipes._prior_cue(text, token.start, token.end)` を読むだけ",
    u"T9 の封 §1 の 1〜3・5・6 のまま",
)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. 封の字
def seal_problems(seal):
    out = []
    try:
        ids = PSG.table_ids(seal, "## §3", "## §4", r"^\| (Q-\d+) \| (.*) \|$")
        sec = seal[seal.index("## §3"):seal.index("## §4")]
        sec4 = seal[seal.index("## §4"):seal.index("## §5")]
        sec5 = seal[seal.index("## §5"):seal.index("## §6")]
        sec21 = seal[seal.index("### §2-1"):seal.index("### §2-2")]
    except ValueError:
        return [u"封の節(§2-1・§2-2・§3・§4・§5・§6)が揃っていない"]
    if ids != list(PRED_IDS):
        out.append(u"封 §3 の表が Q-1〜Q-10 の 10 行でない: %s" % ids)
    for line in sec.splitlines():
        m = re.match(r"^\| (Q-\d+) \| (.*) \|$", line)
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
    for rel in RECORD_RELS + (DOC_REL,) + SCRIPT_RELS + GATE_RELS:
        if rel not in sec21:
            out.append(u"封 §2-1 に path が無い: %s" % rel)
    for ph in SEAL_PHRASES:
        if ph not in seal:
            out.append(u"封に規則の要点の字が無い: %s" % ph)
    return out


def seal_conds(seal):
    u"""封の字から対応の 3 つの条件の記号(ア・イ・ウ。出る順)を読む。"""
    sec = seal[seal.index("## §1"):seal.index("## §2")]
    return tuple(re.findall(r"\((ア|イ|ウ)\) ", sec.split(u"\n")[2]))


# ---------------------------------------------------------------- 2. 封の字と script の定数
def script_problems(seal, t9_seal, pi=None):
    u"""封の字と script の定数が同じか。pi = script の module(試験が壊した写しを渡す)。"""
    pi = pi or PI
    out = []
    if tuple(c[0] for c in pi.CONDS) != seal_conds(seal) or tuple(pi.CONDS) != CONDS_PIN:
        out.append(u"対応の 3 つの条件が封の字((ア)(イ)(ウ))と違う")
    if PSG.seal_seed_forms(t9_seal) != [PS.SEED_T9] or PSG.seal_cap(t9_seal) != pi.RUN.INJECT_CAP:
        out.append(u"T9 の封の乱数の種の字・cap と違う")
    if pi.T9 != "T9_PRIOR_TO_CURRENT" or PSG.seal_type(t9_seal) != pi.T9:
        out.append(u"型が T9 の封の字(T9_PRIOR_TO_CURRENT)と違う")
    if tuple(pi.INJECT_PROFILES) != ("P29E", "P30E"):
        out.append(u"profile が (P29E, P30E) でない")
    if pi.SEAL_REL != SEAL_REL or pi.SEAL_COMMIT != SEAL_COMMIT_SHORT or pi.FLAG != "yen_scan_2026_11_05":
        out.append(u"封の path・commit・切り替えの名前が違う")
    if tuple(pi.SHAPES) != (u"既存", u"万だけ", u"複合"):
        out.append(u"形が 既存 / 万だけ / 複合 でない")
    if pi.BASE_WORD != u"無改変の文で P30E が GROUNDED の claim":
        out.append(u"土台の字が P30E が GROUNDED の claim でない")
    if pi.PS_SCRIPT_REL != "measure/xbrl_pswap_2026-11-06.py" or pi.PS_RECORD_REL != "fixtures/xbrl/pswap/inject_2026-11-06.json":
        out.append(u"T9 の script・記録の path が封の字と違う")
    if tuple(pi.PERIODS) != tuple(PSG.seal_periods(t9_seal) or ()):
        out.append(u"pointer の期の語が T9 の封の字と違う")
    if tuple(pi.UNTOUCHED_FOR_Q1) != ("measure/inject.py", "measure/lib/sites.py", "measure/xbrl_pswap_2026-11-06.py"):
        out.append(u"Q-1 の 0 行の file が封の字(inject.py・sites.py・T9 の script)でない")
    return out


# ---------------------------------------------------------------- 3. 触らない file
def seal_commit(root=REPO):
    s = PR.added_commits(root, PREFIX + SEAL_REL)
    return s[0] if len(s) == 1 else None


untouched_problems = PSG.untouched_problems


def real_untouched_problems(root=REPO):
    sh = seal_commit(root)
    if sh is None:
        return [u"封の commit が履歴に 1 つに決まらない"]
    paths = [PREFIX + p for p in NOT_TOUCHED_RELS]
    # 2026-11-06(PB): 封 docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md §2-3 が宣言した遷移(recipes.py +24・vocabulary.py +5。削除 0)だけは触らない file から外す(SGR.pb_declared_numstat。他の行・他の値は赤のまま)
    # 2026-11-06(T5Y): 封 docs/XBRL_T5_YEN_SEAL_2026-11-06.md §2-1 が宣言した遷移(仕掛けの 2 file に挿入だけ: inject.py +30・sites.py +81。削除 0)も外す(SGR.t5y_declared_numstat。他の行・他の値は赤のまま)
    return untouched_problems([x for x in PR.git_in(root, "diff", "--numstat", sh, "--", *paths)[1].splitlines() if x and not SGR.pb_declared_numstat(x, root) and not SGR.t5y_declared_numstat(x, root)])


reserved_problems = PSG.reserved_problems


# ---------------------------------------------------------------- 5. 配線
def wiring_problems(script=None):
    u"""この script が T9 の script(PS)の同じ instance を使っているか + NS の配線の検査 + T9 の関数を自分で定義していないか。問題の列。"""
    pi = script or PI
    out = list(pi.wiring_problems())
    missing = object()
    for label in ("N", "S", "SC", "RUN", "IJ", "TUNE", "RM", "GEN", "NS", "JT", "NF"):
        if getattr(pi, label, missing) is not getattr(pi.PS, label, missing) or getattr(pi, label, missing) is missing:
            out.append(u"%s がこの script と T9 の script で同じ instance でない" % label)
    if getattr(pi.NS, "yen_scan_on", missing) is not pi.yen_scan_on:
        out.append(u"切り替えの with が NS のものでない")
    if pi.FLAG != getattr(pi.NS, "FLAG", missing):
        out.append(u"切り替えの名前が NS と違う")
    return out


def defined_names(src):
    u"""script の本文に def された関数と代入された名前(トップ階層)。"""
    names = set()
    for n in ast.parse(src).body:
        if isinstance(n, ast.FunctionDef):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return names


def own_t9_function_problems(src):
    u"""T9 の site・行の欄の関数と同じ名前を、script 自身が定義・代入していないか(差し替えていない)。"""
    got = defined_names(src)
    return [u"T9 の関数 %s をこの script が自分で定義している" % f for f in T9_FUNCS if f in got]


def calls_t9_function_problems(src):
    u"""script の本文が ``PS.<関数>`` を呼んでいるか(T9 の関数を使っている)。"""
    return [u"この script が PS.%s を呼んでいない" % f for f in T9_FUNCS if u"PS.%s(" % f not in src]


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
        q10 = [i for i, ln in enumerate(lines) if ln.startswith("| Q-10 |")]
        self.assertEqual(1, len(q10))
        self.assertNotEqual([], seal_problems("\n".join(lines[:q10[0]] + lines[q10[0] + 1:])))                       # 10 行が 9 行
        q5 = [i for i, ln in enumerate(lines) if ln.startswith("| Q-5 |")][0]
        cells = lines[q5].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:q5] + [" | ".join(cells[:2]) + " |"] + lines[q5 + 1:])))   # 外れ方の欄が無い
        self.assertNotEqual([], seal_problems("\n".join(lines[:q5] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[q5 + 1:])))   # 予測の欄が空
        k4 = [i for i, ln in enumerate(lines) if ln.startswith("- K-4:")]
        self.assertEqual(1, len(k4))
        self.assertNotEqual([], seal_problems("\n".join(lines[:k4[0]] + lines[k4[0] + 1:])))
        self.assertNotEqual([], seal_problems(self.seal.replace("measure/xbrl_pswap_idmap_2026-11-06.py", "measure/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("inject_idmap_2026-11-06.json", "inject_x.json")))
        self.assertNotEqual([], seal_problems(self.seal.replace("XBRL_PERIOD_SWAP_IDMAP_RESULT_2026-11-06.md", "x.md")))
        self.assertNotEqual([], seal_problems(self.seal.replace("tests/measure/test_xbrl_pswap_idmap_result.py", "tests/measure/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("## §4", "## 四", 1)))

    def test_a_4_the_three_conditions_are_read_from_the_seal_in_order(self):
        self.assertEqual((u"ア", u"イ", u"ウ"), seal_conds(self.seal))
        self.assertEqual((u"ア", u"イ"), seal_conds(self.seal.replace(u"、(ウ) `c[\"span\"]` に差し替えの字 rendered が在る", u"", 1)))      # 1 つ欠けると読める数が減る
        self.assertNotEqual((u"ア", u"イ", u"ウ"), seal_conds(self.seal.replace(u"(イ) `c[", u"(ロ) `c[", 1)))


class ScriptMatchesSealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)
        cls.t9_seal = read(T9_SEAL_REL)

    def test_b_1_the_script_agrees_with_the_seals(self):
        self.assertEqual([], script_problems(self.seal, self.t9_seal))
        self.assertEqual(CONDS_PIN, tuple(PI.CONDS))

    def _fake(self, **ov):
        d = dict(CONDS=PI.CONDS, RUN=PI.RUN, T9=PI.T9, INJECT_PROFILES=PI.INJECT_PROFILES, SEAL_REL=PI.SEAL_REL, SEAL_COMMIT=PI.SEAL_COMMIT, FLAG=PI.FLAG,
                 SHAPES=PI.SHAPES, BASE_WORD=PI.BASE_WORD, PS_SCRIPT_REL=PI.PS_SCRIPT_REL, PS_RECORD_REL=PI.PS_RECORD_REL, PERIODS=PI.PERIODS, UNTOUCHED_FOR_Q1=PI.UNTOUCHED_FOR_Q1)
        d.update(ov)
        return types.SimpleNamespace(**d)

    def test_b_2_a_changed_script_constant_turns_it_red(self):
        self.assertEqual([], script_problems(self.seal, self.t9_seal, self._fake()))
        for ov in (dict(CONDS=PI.CONDS[:2]), dict(CONDS=(PI.CONDS[1], PI.CONDS[0], PI.CONDS[2])), dict(CONDS=PI.CONDS[:2] + (u"ウ span に差し替えの字が在る",)),
                   dict(RUN=types.SimpleNamespace(INJECT_CAP=11)), dict(T9="T9_PRIOR"), dict(INJECT_PROFILES=("P28E", "P29E")), dict(SEAL_COMMIT="0000000"),
                   dict(SEAL_REL="docs/XBRL_PERIOD_SWAP_SEAL_2026-11-06.md"), dict(FLAG="compound_yen_2026_11_05"), dict(SHAPES=(u"既存", u"万だけ")),
                   dict(BASE_WORD=u"無改変の文で P29E が GROUNDED の claim"), dict(PS_SCRIPT_REL="measure/x.py"), dict(PS_RECORD_REL="fixtures/x.json"),
                   dict(PERIODS=(u"CurrentYear", u"Prior1Year", u"他")), dict(UNTOUCHED_FOR_Q1=PI.UNTOUCHED_FOR_Q1[:2])):
            self.assertNotEqual([], script_problems(self.seal, self.t9_seal, self._fake(**ov)), ov)
        self.assertNotEqual([], script_problems(self.seal.replace(u"(イ) `c[", u"(ロ) `c[", 1), self.t9_seal, self._fake()))
        self.assertNotEqual([], script_problems(self.seal, self.t9_seal.replace(u"cap 型 1 本 10", u"cap 型 1 本 11", 1), self._fake()))
        self.assertNotEqual([], script_problems(self.seal, self.t9_seal.replace(u"%s|%s|T9_PRIOR_TO_CURRENT", u"%s|%s|T9_x", 1), self._fake()))


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

    def test_d_1b_the_t9_script_record_gates_and_the_previous_ones_are_in_the_read_only_list(self):
        for rel in ("measure/xbrl_pswap_2026-11-06.py", "fixtures/xbrl/pswap/inject_2026-11-06.json", "tests/measure/test_xbrl_pswap_seal.py", "tests/measure/test_xbrl_pswap_result.py",
                    "measure/xbrl_jtypes_2026-11-05.py", "fixtures/xbrl/jtypes/inject_2026-11-05.json", "tests/measure/test_xbrl_jtypes_seal.py", "tests/measure/test_xbrl_jtypes_result.py",
                    "measure/inject.py", "measure/lib/sites.py", "measure/xbrl_nscan_2026-11-05.py", "measure/xbrl_p27_tune_2026-10-27.py"):
            self.assertIn(rel, READ_ONLY_RELS)
        self.assertEqual(len(READ_ONLY_RELS), len(set(READ_ONLY_RELS)))

    def test_d_2_the_frozen_check_sees_a_changed_file_and_a_missing_one(self):
        self.assertNotEqual([], SGR.frozen_problems(rels=READ_ONLY_RELS + (SCRIPT_RELS[0],), root=REPO, base=ROOT, seal_rel=SEAL_REL))      # 封の commit に無い file
        self.assertNotEqual([], SGR.frozen_problems(rels=("measure/xbrl_pswap_2026-11-06.py", "measure/nonexistent_file.py"), root=REPO, base=ROOT, seal_rel=SEAL_REL))

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
        self.assertEqual([], reserved_problems(rels=tuple(r for r in GATE_RELS if os.path.exists(os.path.join(ROOT, r))), base=ROOT))

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
            self.assertIn("XBRL_PERIOD_SWAP_IDMAP_SEAL_2026-11-06.md", read(rel), rel)


class WiringTest(unittest.TestCase):
    def test_w_1_the_script_uses_the_same_instances_as_the_t9_script(self):
        self.assertEqual([], wiring_problems())
        self.assertIs(PI.RUN.N, N)
        self.assertIs(PI.IJ.N, N)
        self.assertIs(PI.TUNE.N, N)
        self.assertIs(PI.S.N, N)
        self.assertIs(PI.PS.NS, NS)
        self.assertIs(PI.PS.RM, RM)
        self.assertIs(PI.PS.JT, PI.JT)

    def test_w_2_another_instance_turns_the_wiring_check_red(self):
        for name in ("N", "S", "SC", "RUN", "IJ", "TUNE", "RM", "GEN", "NS", "JT", "NF"):
            fake = types.SimpleNamespace(**dict((k, getattr(PI, k)) for k in dir(PI) if not k.startswith("__")))
            setattr(fake, name, types.SimpleNamespace())
            self.assertNotEqual([], wiring_problems(fake), name)
        fake = types.SimpleNamespace(**dict((k, getattr(PI, k)) for k in dir(PI) if not k.startswith("__")))
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
        old = PI.GEN.key_leaks
        PI.GEN.key_leaks = NS.NF.ORIG_KEY_LEAKS
        try:
            self.assertNotEqual([], wiring_problems())
        finally:
            PI.GEN.key_leaks = old
        self.assertEqual([], wiring_problems())

    def test_w_4_the_switch_is_on_only_inside_the_with_and_goes_back_even_on_an_exception(self):
        self.assertFalse(getattr(N, FLAG))
        with PI.yen_scan_on():
            self.assertTrue(getattr(N, FLAG))
        self.assertFalse(getattr(N, FLAG))
        try:
            with PI.yen_scan_on():
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertFalse(getattr(N, FLAG))

    def test_w_5_the_key_check_for_this_seal_path_is_on_only_inside_its_with(self):
        self.assertEqual([], PI.key_leaks_pi(PI.SEAL_REL))
        self.assertTrue(PI.key_leaks_pi(u"sk-" + u"a" * 30))
        old = PI.GEN.key_leaks
        with PI.key_check_pi():
            self.assertIs(PI.GEN.key_leaks, PI.key_leaks_pi)
        self.assertIs(PI.GEN.key_leaks, old)
        try:
            with PI.key_check_pi():
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertIs(PI.GEN.key_leaks, old)
        self.assertEqual([], wiring_problems())

    def test_w_6_the_script_defines_none_of_the_t9_site_and_row_functions_and_calls_them_from_t9(self):
        src = read(SCRIPT_RELS[0])
        self.assertEqual([], own_t9_function_problems(src))
        self.assertEqual([], calls_t9_function_problems(src))
        for f in T9_FUNCS:
            self.assertTrue(callable(getattr(PI.PS, f)), f)
            self.assertFalse(hasattr(PI, f), f)                                   # PI の名前空間に同名の関数を持たない
        # 壊した写し: 同名の関数を定義する・PS.<関数> の呼び出しをやめる、で赤
        for f in T9_FUNCS:
            self.assertNotEqual([], own_t9_function_problems(src + u"\n\ndef %s(*a):\n    return None\n" % f), f)
            self.assertNotEqual([], own_t9_function_problems(src + u"\n%s = None\n" % f), f)
            self.assertNotEqual([], calls_t9_function_problems(src.replace(u"PS.%s(" % f, u"X.%s(" % f)), f)


    def test_w_8_the_inject_wiring_check_sees_a_missing_install(self):
        u"""``inject_wiring_problems`` は RM の差し替え(RUN.PROFILES・base_status4)が届いているかを見る。差し替えが無ければ赤。"""
        old = (RUN.PROFILES, RUN.base_status4)
        try:
            RM.install_inject()
            self.assertEqual([], PI.inject_wiring_problems())
            RUN.PROFILES = ("P22", "P26")
            self.assertNotEqual([], PI.inject_wiring_problems())
            RM.install_inject()
            RUN.base_status4 = lambda *a, **k: None
            self.assertNotEqual([], PI.inject_wiring_problems())
        finally:
            RUN.PROFILES, RUN.base_status4 = old


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
