# -*- coding: utf-8 -*-
"""封 docs/XBRL_T5_YEN_SEAL_2026-11-06.md(T5Y ― 注入の仕掛けの T5 を円族の数に作れるようにする切り替え ``t5_yen_2026_11_06``)の測定の門。封 §0-2・§1・§2-1・§5。

**この門が縛るもの**(結果の門 ``test_xbrl_t5y_result.py`` は記録・文書・採用の判定・行の欄・偽で不変を縛る)

1. 封の字: §3 の予測の表が Y-1〜Y-10 の 10 行でどの行も予測と外れ方の欄を持つ・§4 の K-1〜K-4・§2-1 と §5 の path・規則の要点の字。封の字を 1 字変えると赤。
2. 封の字と script の定数が同じ: 型 T5_COINCIDENT・乱数の種の字・cap・土台・profile・切り替えの名前 2 つ・形・封の path と commit・T9 の第 2 便の path・Y-10 の変異の名前。
3. 触らない file は封の commit から 0 行(``measure/lib/numbers.py``・``scales.py``・``core/``・``adapters/``。後の PB の engine の宣言された遷移だけは除く)。
   仕掛け(``measure/lib/sites.py``・``measure/inject.py``)は封の commit から**挿入だけ**(削除 0 行)。前の便(T9 の第 2 便を含む)の script・記録・門・文書は封の commit の blob と byte が同じ
   (仕掛けの 2 file は T5Y の宣言された遷移だけ許す。``SGR.t5y_declared_file_change``)。
4. 順序: 封 79d05cd ⊏ 仕掛けの 2 file の変更・script・試験・門 2 本(記録・結果の文書の順序は結果の門が見る)。未 commit は赤(skip にしない)。
5. 配線: この script が T9 の第 2 便の script の同じ instance(NS・N・S・RUN・IJ・TUNE・SC・RM・GEN・JT・NF)を使う。切り替え 2 つは with の中だけ真。IJ が引く S がこの script の S。
   T9 の第 2 便の対応付けの関数・T9 の行の欄の関数を**そのまま使う**(この script が同じ名前の関数を定義していない・呼び出しは PI / PS の関数)。
6. 新しい門が、既存の門が行頭の名前を数える変数名を行頭に置いていない。script・門に docID の字が無い。
7. 門の変異: 封の字・script の定数・numstat・順序・配線を 1 つずつ壊した標本で上の検査が赤になる。

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


PIG = load_module("tests/measure/test_xbrl_pswap_idmap_seal.py", "pswap_idmap_seal_gate_for_t5y_seal")     # T9 の第 2 便の封の門の部品(READ_ONLY_RELS・封の字を読む関数)。門としては走らせない
PSG = PIG.PSG
SGR = PIG.SGR
PR = PIG.PR
TY = load_module("measure/xbrl_t5y_2026-11-06.py", "t5y_script_for_seal_gate")
PI = TY.PI
PS = TY.PS
NS = TY.NS
N, S, SC, RUN, IJ, TUNE, RM = TY.N, TY.S, TY.SC, TY.RUN, TY.IJ, TY.TUNE, TY.RM

SEAL_REL = TY.SEAL_REL
SEAL_COMMIT_SHORT = "79d05cd"                     # 封の commit(literal に留める。script の定数と違えば script_problems が赤)
FLAG = TY.FLAG
FLAG2 = TY.FLAG2
SCRIPT_RELS = ("measure/xbrl_t5y_2026-11-06.py",)
GATE_RELS = ("tests/measure/test_xbrl_t5y_seal.py", "tests/measure/test_xbrl_t5y_result.py")
TEST_RELS = ("measure/tests/test_t5_yen.py",)
RECORD_RELS = tuple(TY.REC_REL.values())
DOC_REL = TY.DOC_REL
#: 仕掛け(封の commit から挿入だけ)
DEVICE_RELS = ("measure/lib/sites.py", "measure/inject.py")
#: 触らない file(封の commit から 0 行)
NOT_TOUCHED_RELS = ("measure/lib/numbers.py", "measure/lib/scales.py", "adapters", "core")
#: この便が読むだけの前の便の script・記録・門(封の commit の blob と byte が同じでなければならない)。T9 の第 2 便の分から仕掛けの 2 file を除き、T9 の第 2 便の script・記録・門・文書を足す
READ_ONLY_RELS = tuple(r for r in PIG.READ_ONLY_RELS if r not in DEVICE_RELS) + (
    "measure/xbrl_pswap_idmap_2026-11-06.py", "fixtures/xbrl/pswap/inject_idmap_2026-11-06.json",
    "tests/measure/test_xbrl_pswap_idmap_seal.py", "tests/measure/test_xbrl_pswap_idmap_result.py",
    "docs/XBRL_PERIOD_SWAP_IDMAP_SEAL_2026-11-06.md", "docs/XBRL_PERIOD_SWAP_IDMAP_RESULT_2026-11-06.md")
RESERVED_PREFIXES = SGR.RESERVED_PREFIXES
DOCID_RE = SGR.DOCID_RE
PRED_IDS = tuple("Y-%d" % i for i in range(1, 11))
K_IDS = tuple("K-%d" % i for i in range(1, 5))
#: Y-10 の変異の名前(literal に留める。script の定数・封の字と違えば赤)
MUTATION_NAMES_PIN = (u"切り替えを外す", u"篩を書かれた値に戻す", u"描きを倍率で割らない", u"読み直しを外す", u"相手の単位の優先を外す")
#: 呼び出しを縛る関数(この script は同じ名前の関数を定義せず、PI / PS の関数を呼ぶ)
PI_FUNCS = ("id_map",)
PS_FUNCS = ("pointer_period", "reached_of", "shape_of_token")
#: 封の字の要点(封に無ければ赤)
SEAL_PHRASES = (
    u"切り替え `t5_yen_2026_11_06 = False`",
    u"偽なら `t5_sites`・`build_t5` は 1 byte も振る舞いを変えない(K-1)",
    u"篩と「値が違う」を円で比べ",
    u"`N.scan(描いた字 + 単位)` で読み直すと token 1 つで",
    u"円の値が相手の値と書かれた桁の半分以内",
    u"読み直した値が元の値から桁の半分より離れる",
    u"`cand = other[\"value\"] / (SC.scale_of(t.unit) or 1)` を描き",
    u"`new_value` は描いた字を読み直した値(token の単位)",
    u"`detail` に `coincident_ref_key`・`replacement_value`(円)を持つ",
    u"相手の単位の優先(`pool`)と乱数は現行のまま",
    u"測定は土台 P30E・比較 P29E(J と同じ。P32E は別の便)",
    u"注入後の claim は**基準の claim の id で引く**(T9 の第 2 便の 3 条件)",
    u"cap 型 1 本 10",
    u"random.Random(\"%s|%s|T5_COINCIDENT\" % (seed, 本の名前))",
    u"土台 P30E GROUNDED を先頭から cap",
    u"`IJ.apply_edits`・`IJ.revert`",
    u"差し替えは `[token.start, token.end]`(単位の字は触らない)",
    u"`NS.yen_scan_on()` と `t5_yen_on()`(新しい context manager。切り替えを with の中だけ真)",
)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. 封の字
def seal_problems(seal):
    out = []
    try:
        ids = PSG.table_ids(seal, "## §3", "## §4", r"^\| (Y-\d+) \| (.*) \|$")
        sec = seal[seal.index("## §3"):seal.index("## §4")]
        sec4 = seal[seal.index("## §4"):seal.index("## §5")]
        sec5 = seal[seal.index("## §5"):seal.index("## §6")]
        sec21 = seal[seal.index("### §2-1"):seal.index("### §2-2")]
    except ValueError:
        return [u"封の節(§2-1・§2-2・§3・§4・§5・§6)が揃っていない"]
    if ids != list(PRED_IDS):
        out.append(u"封 §3 の表が Y-1〜Y-10 の 10 行でない: %s" % ids)
    for line in sec.splitlines():
        m = re.match(r"^\| (Y-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            if len(cells) < 3 or any(not c.strip() for c in cells[:3]):
                out.append(u"封 §3 の %s の欄(欄・予測・外れ方)が埋まっていない" % m.group(1))
    got_k = re.findall(r"^- (K-\d):", sec4, re.M)
    if got_k != list(K_IDS):
        out.append(u"封 §4 の K-1〜K-4 が揃っていない: %s" % got_k)
    for rel in SCRIPT_RELS + GATE_RELS[:1]:
        if rel not in sec5:
            out.append(u"封 §5 に path が無い: %s" % rel)
    if GATE_RELS[1] not in sec5 and u"test_xbrl_t5y_result.py" not in sec5:
        out.append(u"封 §5 に結果の門の path が無い")
    for rel in RECORD_RELS + (DOC_REL,) + SCRIPT_RELS + GATE_RELS + TEST_RELS + DEVICE_RELS:
        if rel not in sec21:
            out.append(u"封 §2-1 に path が無い: %s" % rel)
    for ph in SEAL_PHRASES:
        if ph not in seal:
            out.append(u"封に規則の要点の字が無い: %s" % ph)
    return out


def seal_seed_forms(seal):
    return PSG.seal_seed_forms(seal)


def seal_cap(seal):
    return PSG.seal_cap(seal)


def seal_type_from_seed(seal):
    forms = seal_seed_forms(seal)
    m = re.search(r"\|(T\d_[A-Z_]+)$", forms[0]) if forms else None
    return m.group(1) if m else None


def seal_mutation_names(seal):
    try:
        sec = seal[seal.index("## §3"):seal.index("## §4")]
    except ValueError:
        return None
    m = re.search(r"^\| Y-10 \|.*?変異\(([^)]*)\)で赤", sec, re.M)
    return tuple(x.strip() for x in m.group(1).split(u"・")) if m else None


# ---------------------------------------------------------------- 2. 封の字と script の定数
def script_problems(seal, ty=None):
    u"""封の字と script の定数が同じか。ty = script の module(試験が壊した写しを渡す)。"""
    ty = ty or TY
    out = []
    if seal_seed_forms(seal) != ["%s|%s|T5_COINCIDENT"] or ty.SEED_T5 != "%s|%s|T5_COINCIDENT":
        out.append(u"乱数の種の字が封の字と違う")
    if seal_cap(seal) != ty.RUN.INJECT_CAP:
        out.append(u"cap が封の字と違う")
    if ty.T5 != "T5_COINCIDENT" or seal_type_from_seed(seal) != ty.T5:
        out.append(u"型が封の字(T5_COINCIDENT)と違う")
    if tuple(ty.INJECT_PROFILES) != ("P29E", "P30E"):
        out.append(u"profile が (P29E, P30E) でない")
    if ty.SEAL_REL != SEAL_REL or ty.SEAL_COMMIT != SEAL_COMMIT_SHORT:
        out.append(u"封の path・commit が違う")
    if ty.FLAG != "yen_scan_2026_11_05" or ty.FLAG2 != "t5_yen_2026_11_06":
        out.append(u"切り替えの名前が違う")
    if tuple(ty.SHAPES) != (u"既存", u"万だけ", u"複合"):
        out.append(u"形が 既存 / 万だけ / 複合 でない")
    if ty.BASE_WORD != u"無改変の文で P30E が GROUNDED の claim":
        out.append(u"土台の字が P30E が GROUNDED の claim でない")
    if ty.PI_SCRIPT_REL != "measure/xbrl_pswap_idmap_2026-11-06.py" or ty.PI_RECORD_REL != "fixtures/xbrl/pswap/inject_idmap_2026-11-06.json":
        out.append(u"T9 の第 2 便の script・記録の path が封の字と違う")
    if tuple(ty.DEVICE_RELS) != DEVICE_RELS:
        out.append(u"仕掛けの 2 file の path が違う")
    if ty.TEST_T5_REL != TEST_RELS[0] or ty.TEST_INJECT_REL != "measure/tests/test_inject.py":
        out.append(u"Y-10 の試験の path が違う")
    if tuple(ty.MUTATIONS) != MUTATION_NAMES_PIN or seal_mutation_names(seal) != MUTATION_NAMES_PIN:
        out.append(u"Y-10 の変異の名前が封の字・留めた名前と違う")
    if tuple(ty.PARTNER_PERIODS) != (u"CurrentYear", u"Prior1Year", u"他"):
        out.append(u"相手の fact の期の語が 3 つでない")
    return out


# ---------------------------------------------------------------- 3. 触らない file・仕掛けは挿入だけ
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
    return untouched_problems([x for x in PR.git_in(root, "diff", "--numstat", sh, "--", *paths)[1].splitlines() if x and not SGR.pb_declared_numstat(x, root) and not SGR.t_declared_numstat(x, root)])      # 2026-11-09(T): 封 docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md §2-3 が宣言した遷移(recipes.py +57・vocabulary.py +5。削除 0)も外す(SGR.t_declared_numstat)


def insert_only_problems(lines):
    u"""``git diff --numstat`` の行(仕掛けの 2 file)が、どちらも 1 行ずつ在り、足した行が 1 以上で削除が 0 行か。"""
    out = []
    seen = {}
    for ln in lines:
        parts = ln.split("\t")
        if len(parts) != 3 or not parts[2].startswith(PREFIX):
            out.append(u"numstat の行の形が違う: %s" % ln)
            continue
        seen.setdefault(parts[2][len(PREFIX):], []).append(parts)
    for rel in DEVICE_RELS:
        rows = seen.get(rel, [])
        if len(rows) != 1:
            out.append(u"%s が封の commit から変わっていない・numstat が 1 行でない" % rel)
            continue
        add, dele = rows[0][0], rows[0][1]
        if not add.isdigit() or int(add) < 1:
            out.append(u"%s の挿入が 1 行以上でない" % rel)
        if dele != "0":
            out.append(u"%s に削除 %s 行がある(挿入だけのはず)" % (rel, dele))
    for rel in seen:
        if rel not in DEVICE_RELS:
            out.append(u"仕掛けでない file が numstat に在る: %s" % rel)
    return out


def real_device_problems(root=REPO):
    sh = seal_commit(root)
    if sh is None:
        return [u"封の commit が履歴に 1 つに決まらない"]
    paths = [PREFIX + p for p in DEVICE_RELS]
    return insert_only_problems([x for x in PR.git_in(root, "diff", "--numstat", sh, "--", *paths)[1].splitlines() if x])


reserved_problems = PSG.reserved_problems


# ---------------------------------------------------------------- 5. 配線
def wiring_problems(script=None):
    u"""この script が T9 の第 2 便の script(PI)の同じ instance を使っているか + NS の配線の検査 + 関数を自分で定義していないか。問題の列。"""
    ty = script or TY
    out = list(ty.wiring_problems())
    missing = object()
    for label in ("N", "S", "SC", "RUN", "IJ", "TUNE", "RM", "GEN", "NS", "JT", "NF", "PS"):
        if getattr(ty, label, missing) is not getattr(ty.PI, label, missing) or getattr(ty, label, missing) is missing:
            out.append(u"%s がこの script と T9 の第 2 便の script で同じ instance でない" % label)
    if getattr(ty.NS, "yen_scan_on", missing) is not ty.yen_scan_on:
        out.append(u"H の切り替えの with が NS のものでない")
    if getattr(ty.S, "t5_yen_on", missing) is not ty.t5_yen_on:
        out.append(u"T5 の切り替えの with が S のものでない")
    if ty.FLAG != getattr(ty.NS, "FLAG", missing) or not hasattr(ty.S, ty.FLAG2):
        out.append(u"切り替えの名前が NS・S と違う")
    if getattr(ty.IJ, "S", missing) is not ty.S:
        out.append(u"IJ が引く S がこの script の S と違う")
    return out


def defined_names(src):
    names = set()
    for n in ast.parse(src).body:
        if isinstance(n, ast.FunctionDef):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return names


def own_function_problems(src):
    u"""T9 の第 2 便・T9 の関数と同じ名前を、script 自身が定義・代入していないか(差し替えていない)。"""
    got = defined_names(src)
    return [u"関数 %s をこの script が自分で定義している" % f for f in PI_FUNCS + PS_FUNCS if f in got]


def calls_problems(src):
    u"""script の本文が ``PI.<関数>(``・``PS.<関数>(`` を呼んでいるか。"""
    return [u"この script が PI.%s を呼んでいない" % f for f in PI_FUNCS if u"PI.%s(" % f not in src] + [u"この script が PS.%s を呼んでいない" % f for f in PS_FUNCS if u"PS.%s(" % f not in src]


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
            mutated = self.seal.replace(ph, ph[:-1] + u"？")
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], seal_problems(mutated), ph)

    def test_a_3_a_broken_prediction_table_or_missing_section_turns_it_red(self):
        lines = self.seal.split("\n")
        y10 = [i for i, ln in enumerate(lines) if ln.startswith("| Y-10 |")]
        self.assertEqual(1, len(y10))
        self.assertNotEqual([], seal_problems("\n".join(lines[:y10[0]] + lines[y10[0] + 1:])))
        y5 = [i for i, ln in enumerate(lines) if ln.startswith("| Y-5 |")][0]
        cells = lines[y5].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:y5] + [" | ".join(cells[:2]) + " |"] + lines[y5 + 1:])))
        self.assertNotEqual([], seal_problems("\n".join(lines[:y5] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[y5 + 1:])))
        k4 = [i for i, ln in enumerate(lines) if ln.startswith("- K-4:")]
        self.assertEqual(1, len(k4))
        self.assertNotEqual([], seal_problems("\n".join(lines[:k4[0]] + lines[k4[0] + 1:])))
        self.assertNotEqual([], seal_problems(self.seal.replace("measure/xbrl_t5y_2026-11-06.py", "measure/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("inject_2026-11-06.json", "inject_x.json")))
        self.assertNotEqual([], seal_problems(self.seal.replace("XBRL_T5_YEN_RESULT_2026-11-06.md", "x.md")))
        self.assertNotEqual([], seal_problems(self.seal.replace("measure/tests/test_t5_yen.py", "measure/tests/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("## §4", "## 四", 1)))

    def test_a_4_the_seed_cap_type_and_mutation_names_are_read_from_the_seal(self):
        self.assertEqual(["%s|%s|T5_COINCIDENT"], seal_seed_forms(self.seal))
        self.assertEqual(10, seal_cap(self.seal))
        self.assertEqual("T5_COINCIDENT", seal_type_from_seed(self.seal))
        self.assertEqual(MUTATION_NAMES_PIN, seal_mutation_names(self.seal))
        self.assertIsNone(seal_mutation_names(self.seal.replace(u"で赤", u"で緑")))
        self.assertEqual(MUTATION_NAMES_PIN[:4], seal_mutation_names(self.seal.replace(u"・相手の単位の優先を外す)", u")")))


class ScriptMatchesSealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_b_1_the_script_agrees_with_the_seal(self):
        self.assertEqual([], script_problems(self.seal))

    def _fake(self, **ov):
        d = dict(SEED_T5=TY.SEED_T5, RUN=TY.RUN, T5=TY.T5, INJECT_PROFILES=TY.INJECT_PROFILES, SEAL_REL=TY.SEAL_REL, SEAL_COMMIT=TY.SEAL_COMMIT, FLAG=TY.FLAG, FLAG2=TY.FLAG2,
                 SHAPES=TY.SHAPES, BASE_WORD=TY.BASE_WORD, PI_SCRIPT_REL=TY.PI_SCRIPT_REL, PI_RECORD_REL=TY.PI_RECORD_REL, DEVICE_RELS=TY.DEVICE_RELS,
                 TEST_T5_REL=TY.TEST_T5_REL, TEST_INJECT_REL=TY.TEST_INJECT_REL, MUTATIONS=TY.MUTATIONS, PARTNER_PERIODS=TY.PARTNER_PERIODS)
        d.update(ov)
        return types.SimpleNamespace(**d)

    def test_b_2_a_changed_script_constant_turns_it_red(self):
        self.assertEqual([], script_problems(self.seal, self._fake()))
        muts = dict((k, v) for k, v in list(TY.MUTATIONS.items())[:4])
        for ov in (dict(SEED_T5="%s|%s|T9_PRIOR_TO_CURRENT"), dict(RUN=types.SimpleNamespace(INJECT_CAP=11)), dict(T5="T5_x"), dict(INJECT_PROFILES=("P28E", "P29E")),
                   dict(SEAL_COMMIT="0000000"), dict(SEAL_REL="docs/XBRL_PERIOD_SWAP_IDMAP_SEAL_2026-11-06.md"), dict(FLAG="compound_yen_2026_11_05"), dict(FLAG2="t5_yen_x"),
                   dict(SHAPES=(u"既存", u"万だけ")), dict(BASE_WORD=u"無改変の文で P29E が GROUNDED の claim"), dict(PI_SCRIPT_REL="measure/x.py"), dict(PI_RECORD_REL="fixtures/x.json"),
                   dict(DEVICE_RELS=TY.DEVICE_RELS[:1]), dict(TEST_T5_REL="measure/tests/x.py"), dict(TEST_INJECT_REL="measure/tests/x.py"), dict(MUTATIONS=muts),
                   dict(PARTNER_PERIODS=(u"CurrentYear", u"Prior1Year"))):
            self.assertNotEqual([], script_problems(self.seal, self._fake(**ov)), ov)
        self.assertNotEqual([], script_problems(self.seal.replace("cap 型 1 本 10", "cap 型 1 本 11", 1), self._fake()))
        self.assertNotEqual([], script_problems(self.seal.replace("%s|%s|T5_COINCIDENT", "%s|%s|T5_x", 1), self._fake()))
        self.assertNotEqual([], script_problems(self.seal.replace(u"・相手の単位の優先を外す)", u")"), self._fake()))


class NotTouchedAndFrozenTest(unittest.TestCase):
    def test_c_1_numbers_scales_and_engine_are_untouched_since_the_seal(self):
        self.assertEqual([], real_untouched_problems())

    def test_c_2_the_untouched_check_sees_a_changed_line(self):
        for rel in ("measure/lib/numbers.py", "measure/lib/scales.py", "adapters/xbrl/extract.py", "core/py/audit_core/verify.py"):
            self.assertNotEqual([], untouched_problems(["1\t0\t%s%s" % (PREFIX, rel)]), rel)
        self.assertNotEqual([], untouched_problems(["0\t2\t%sadapters/xbrl/recipes.py" % PREFIX]))
        self.assertEqual([], untouched_problems([]))

    def test_c_3_the_device_files_changed_by_insertion_only_since_the_seal(self):
        self.assertEqual([], real_device_problems())

    def test_c_4_the_insert_only_check_sees_a_deletion_a_missing_file_and_a_foreign_file(self):
        good = ["81\t0\t%smeasure/lib/sites.py" % PREFIX, "30\t0\t%smeasure/inject.py" % PREFIX]
        self.assertEqual([], insert_only_problems(good))
        self.assertNotEqual([], insert_only_problems(["81\t1\t%smeasure/lib/sites.py" % PREFIX, good[1]]))               # 1 行削除
        self.assertNotEqual([], insert_only_problems([good[0], "30\t2\t%smeasure/inject.py" % PREFIX]))
        self.assertNotEqual([], insert_only_problems(good[:1]))                                                           # inject.py が変わっていない
        self.assertNotEqual([], insert_only_problems(good[1:]))
        self.assertNotEqual([], insert_only_problems(good + ["3\t0\t%smeasure/lib/numbers.py" % PREFIX]))                # 仕掛けでない file
        self.assertNotEqual([], insert_only_problems([good[0], "0\t0\t%smeasure/inject.py" % PREFIX]))                    # 挿入 0
        self.assertNotEqual([], insert_only_problems([good[0], "-\t-\t%smeasure/inject.py" % PREFIX]))
        self.assertNotEqual([], insert_only_problems(good + [good[0]]))                                                   # 同じ file が 2 行

    def test_d_1_previous_scripts_records_and_gates_are_byte_identical_to_the_seal_commit(self):
        self.assertEqual([], SGR.frozen_problems(rels=READ_ONLY_RELS, root=REPO, base=ROOT, seal_rel=SEAL_REL))

    def test_d_1b_the_t9_idmap_script_record_gates_and_the_previous_ones_are_in_the_read_only_list(self):
        for rel in ("measure/xbrl_pswap_idmap_2026-11-06.py", "fixtures/xbrl/pswap/inject_idmap_2026-11-06.json", "tests/measure/test_xbrl_pswap_idmap_seal.py",
                    "tests/measure/test_xbrl_pswap_idmap_result.py", "measure/xbrl_pswap_2026-11-06.py", "fixtures/xbrl/pswap/inject_2026-11-06.json",
                    "measure/xbrl_jtypes_2026-11-05.py", "fixtures/xbrl/jtypes/inject_2026-11-05.json", "measure/xbrl_nscan_2026-11-05.py", "measure/xbrl_p27_tune_2026-10-27.py",
                    "measure/lib/numbers.py", "measure/lib/scales.py"):
            self.assertIn(rel, READ_ONLY_RELS)
        for rel in DEVICE_RELS:                                                        # 仕掛けの 2 file はこの便が変える = 読むだけの一覧に入れない
            self.assertNotIn(rel, READ_ONLY_RELS)
        self.assertEqual(len(READ_ONLY_RELS), len(set(READ_ONLY_RELS)))

    def test_d_2_the_frozen_check_sees_a_changed_file_and_a_missing_one(self):
        self.assertNotEqual([], SGR.frozen_problems(rels=READ_ONLY_RELS + (SCRIPT_RELS[0],), root=REPO, base=ROOT, seal_rel=SEAL_REL))      # 封の commit に無い file
        self.assertNotEqual([], SGR.frozen_problems(rels=("measure/xbrl_pswap_idmap_2026-11-06.py", "measure/nonexistent_file.py"), root=REPO, base=ROOT, seal_rel=SEAL_REL))

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

    def test_f_1_scripts_tests_and_gates_carry_no_docid(self):
        for rel in SCRIPT_RELS + GATE_RELS + TEST_RELS:
            if os.path.exists(os.path.join(ROOT, rel)):
                self.assertIsNone(DOCID_RE.search(read(rel)), rel)

    def test_f_2_scripts_name_the_seal(self):
        for rel in SCRIPT_RELS:
            self.assertIn("XBRL_T5_YEN_SEAL_2026-11-06.md", read(rel), rel)


class WiringTest(unittest.TestCase):
    def test_w_1_the_script_uses_the_same_instances_as_the_t9_idmap_script(self):
        self.assertEqual([], wiring_problems())
        self.assertIs(TY.RUN.N, N)
        self.assertIs(TY.IJ.N, N)
        self.assertIs(TY.IJ.S, S)
        self.assertIs(TY.TUNE.N, N)
        self.assertIs(TY.S.N, N)
        self.assertIs(TY.PI.PS, PS)
        self.assertIs(TY.PI.NS, NS)

    def test_w_2_another_instance_turns_the_wiring_check_red(self):
        for name in ("N", "S", "SC", "RUN", "IJ", "TUNE", "RM", "GEN", "NS", "JT", "NF", "PS"):
            fake = types.SimpleNamespace(**dict((k, getattr(TY, k)) for k in dir(TY) if not k.startswith("__")))
            setattr(fake, name, types.SimpleNamespace())
            self.assertNotEqual([], wiring_problems(fake), name)
        for name in ("yen_scan_on", "t5_yen_on"):
            fake = types.SimpleNamespace(**dict((k, getattr(TY, k)) for k in dir(TY) if not k.startswith("__")))
            setattr(fake, name, lambda: None)
            self.assertNotEqual([], wiring_problems(fake), name)
        fake = types.SimpleNamespace(**dict((k, getattr(TY, k)) for k in dir(TY) if not k.startswith("__")))
        fake.IJ = types.SimpleNamespace(S=types.SimpleNamespace())                    # IJ が引く S が違う
        self.assertNotEqual([], wiring_problems(fake))
        self.assertEqual([], wiring_problems())

    def test_w_3_the_h_wiring_check_still_sees_a_swapped_n_or_key_check(self):
        old = NS.RUN.N
        NS.RUN.N = types.SimpleNamespace(__file__=N.__file__)
        try:
            self.assertNotEqual([], wiring_problems())
        finally:
            NS.RUN.N = old
        old = TY.GEN.key_leaks
        TY.GEN.key_leaks = NS.NF.ORIG_KEY_LEAKS
        try:
            self.assertNotEqual([], wiring_problems())
        finally:
            TY.GEN.key_leaks = old
        self.assertEqual([], wiring_problems())

    def test_w_4_both_switches_are_on_only_inside_their_with_and_go_back_even_on_an_exception(self):
        self.assertFalse(getattr(N, FLAG))
        self.assertFalse(getattr(S, FLAG2))
        with TY.yen_scan_on():
            with TY.t5_yen_on():
                self.assertTrue(getattr(N, FLAG))
                self.assertTrue(getattr(S, FLAG2))
                with TY.t5_yen_off():
                    self.assertFalse(getattr(S, FLAG2))
                    self.assertTrue(getattr(N, FLAG))
                self.assertTrue(getattr(S, FLAG2))
        self.assertFalse(getattr(N, FLAG))
        self.assertFalse(getattr(S, FLAG2))
        for mk in (TY.yen_scan_on, TY.t5_yen_on):
            try:
                with mk():
                    raise RuntimeError("x")
            except RuntimeError:
                pass
            self.assertFalse(getattr(N, FLAG))
            self.assertFalse(getattr(S, FLAG2))

    def test_w_5_the_key_check_for_this_seal_path_is_on_only_inside_its_with(self):
        self.assertEqual([], TY.key_leaks_ty(TY.SEAL_REL))
        self.assertTrue(TY.key_leaks_ty(u"sk-" + u"a" * 30))
        old = TY.GEN.key_leaks
        with TY.key_check_ty():
            self.assertIs(TY.GEN.key_leaks, TY.key_leaks_ty)
        self.assertIs(TY.GEN.key_leaks, old)
        try:
            with TY.key_check_ty():
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertIs(TY.GEN.key_leaks, old)
        self.assertEqual([], wiring_problems())

    def test_w_6_the_script_defines_none_of_the_reused_functions_and_calls_them_from_their_owners(self):
        src = read(SCRIPT_RELS[0])
        self.assertEqual([], own_function_problems(src))
        self.assertEqual([], calls_problems(src))
        for f in PI_FUNCS:
            self.assertTrue(callable(getattr(TY.PI, f)), f)
            self.assertFalse(hasattr(TY, f), f)
        for f in PS_FUNCS:
            self.assertTrue(callable(getattr(TY.PS, f)), f)
            self.assertFalse(hasattr(TY, f), f)
        for f in PI_FUNCS + PS_FUNCS:
            self.assertNotEqual([], own_function_problems(src + u"\n\ndef %s(*a):\n    return None\n" % f), f)
            self.assertNotEqual([], own_function_problems(src + u"\n%s = None\n" % f), f)
            owner = u"PI" if f in PI_FUNCS else u"PS"
            self.assertNotEqual([], calls_problems(src.replace(u"%s.%s(" % (owner, f), u"X.%s(" % f)), f)

    def test_w_7_the_inject_wiring_check_sees_a_missing_install(self):
        old = (RUN.PROFILES, RUN.base_status4)
        try:
            RM.install_inject()
            self.assertEqual([], TY.inject_wiring_problems())
            RUN.PROFILES = ("P22", "P26")
            self.assertNotEqual([], TY.inject_wiring_problems())
            RM.install_inject()
            RUN.base_status4 = lambda *a, **k: None
            self.assertNotEqual([], TY.inject_wiring_problems())
        finally:
            RUN.PROFILES, RUN.base_status4 = old


class OrderTest(unittest.TestCase):
    def test_o_1_the_real_history_has_the_seal_before_the_device_the_script_the_tests_and_the_gates(self):
        u"""仕掛けの 2 file・script・試験・門のどれかが未 commit なら赤(足した commit が無い)。"""
        self.assertEqual([], PR.order_problems(REPO, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, list(DEVICE_RELS), list(SCRIPT_RELS + TEST_RELS + GATE_RELS)))


OTHERS = ["measure/a.py", "tests/g.py"]
SEALF = "docs/seal.md"


def order_of(r, seal_short):
    return PR.order_problems(r.d, PREFIX, SEALF, seal_short, ["measure/lib/dev.py"], OTHERS)


class OrderMutationTest(unittest.TestCase):
    def _repo(self, dev_before=False, dev_after=True, after=OTHERS):
        r = PR.Repo()
        r.put("measure/lib/dev.py")
        r.commit("measure/lib/dev.py")
        if dev_before:
            pass
        r.put(SEALF)
        s = r.commit(SEALF)
        if dev_after:
            with open(os.path.join(r.d, PREFIX, "measure/lib/dev.py"), "a", encoding="utf-8") as fh:
                fh.write("x = 1\n")
            r.commit("measure/lib/dev.py")
        for f in after:
            r.put(f)
        if after:
            r.commit(*after)
        return r, s[:7]

    def test_p_1_a_correct_order_is_green(self):
        r, s = self._repo()
        self.assertEqual([], order_of(r, s))

    def test_p_2_a_device_file_not_changed_after_the_seal_is_red(self):
        r, s = self._repo(dev_after=False)
        self.assertIn("IMPL_UNCOMMITTED:measure/lib/dev.py", order_of(r, s))

    def test_p_3_an_uncommitted_script_is_red_not_skipped(self):
        r, s = self._repo(after=OTHERS[:1])
        self.assertEqual(["UNCOMMITTED:" + OTHERS[1]], order_of(r, s))

    def test_p_4_a_wrong_seal_hash_is_red(self):
        r, _s = self._repo()
        self.assertIn("SEAL_NOT_THE_SEALED", order_of(r, "0000000"))


if __name__ == "__main__":
    unittest.main()
