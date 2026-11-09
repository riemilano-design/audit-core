# -*- coding: utf-8 -*-
"""封 docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md(PB ― 前期の手がかりがある数を当期の fact に落とさない。P32E = P30E + 旗。既定にしない)の測定の門。封 §5・追記 1。

**この門が縛るもの**(結果の門 ``test_xbrl_pbind_result.py`` は記録・文書・採用の判定・行の欄を縛る)

1. 封の字: §3 の予測の表が E-1〜E-10 の 10 行でどの行も予測と外れ方の欄を持つ・§4 の K-1〜K-5・§5 の path(script・記録 3 つ(中括弧の形)・門 2 本・結果の文書)・
   規則の要点((窓だけ・前期の fact を名指して VALUE_MISMATCH・Prior2Year 以前は残す・増減の語があっても同じ)と追記 1。封の字を 1 字変えると赤。
2. 封の字と script の定数が同じ: 封の path と commit(封 b7824e6・追記 56317fb)・profile の対(P30E → P32E)・E の幅(封の字から読んだ値を literal に留めた値と照らす)・
   engine の 2 file・記録の path・結果の文書の path・前の便の記録(RB の regress97・T9 の第 2 便)の path。
3. 触らない file は **engine の commit の blob と byte が同じ**: 前の便(RB・T9 の第 2 便・T9・N・J・H)の script・記録・門と ``measure/inject.py``・``measure/lib``。
   engine(``core/``・``adapters/``)は engine の commit から 0 行。engine の commit の hash を字で持たず、履歴から探す。
4. 順序: 封 b7824e6 ⊏ engine を触った commit ⊏ script・門 2 本(記録・結果の文書の順序は結果の門が見る)。未 commit は赤(skip にしない)。
5. 配線: この script が RB の便の script・T9 の第 2 便の script の同じ instance を使う。XR(RB の regress97 script の持つ N の便の script)の差し替えが届いている。
   前の便の関数(``RM.load_jobs``・``RM.id_map``・``RM.label_of``・``PI.id_map``・``PS.t9_all_sites``・``PS.build_t9``・``PS.engine_cue``・``PS.has_prior_word``・
   ``PS.pointer_period``・``PS.shape_of_token``・``XR.doc_job``・``XR.doc_rows``・``XR.engine_commits``・``XR.engine_link``)を**そのまま呼ぶ**(この script は同名の関数を定義しない)。
6. 新しい門が、既存の門が行頭の名前を数える変数名を行頭に置いていない。script・門に docID の字が無い。
7. 門の変異: 封の字・script の定数・順序・触らない file・配線を 1 つずつ壊した標本で上の検査が赤になる。

この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import ast
import importlib.util
import os
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
    u"""importlib で読み込む。読み込んだ file が中で読む前の便の script は、決まった名前で ``sys.modules`` に登録し直して**先に居た module を上書きする**
    (RB の ``numfix_regress97_for_rmix`` など。``--procs 2`` の pickle は名前で引く)。読み込みの前に居た名前は、読み込みの後に元の object へ戻す
    (さもないと pytest の引数で RB の結果の門を PB の門より先に並べたとき、RB の門が持つ object と ``sys.modules`` の object が別になって赤くなる)。
    読み込んだ module 自身の名前 ``name`` は残す。"""
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


SGR = load_module("tests/measure/test_xbrl_rmix_seal.py", "rmix_seal_gate_for_pbind_seal")           # engine の commit を履歴から探す関数・順序の部品。門としては走らせない
PR = SGR.PR
PB = load_module("measure/xbrl_pbind_2026-11-06.py", "pbind_script_for_seal_gate")
RM, RR, PI, PS, XR = PB.RM, PB.RR, PB.PI, PB.PS, PB.XR

SEAL_REL = PB.SEAL_REL
SEAL_COMMIT_SHORT = "b7824e6"                     # 封の最初の commit(literal に留める。script の定数と違えば script_problems が赤)
ADDENDUM_COMMIT_SHORT = "56317fb"                 # 追記 1 の commit
DOC_REL = PB.DOC_REL
SCRIPT_RELS = ("measure/xbrl_pbind_2026-11-06.py",)
GATE_RELS = ("tests/measure/test_xbrl_pbind_seal.py", "tests/measure/test_xbrl_pbind_result.py")
RECORD_RELS = ("fixtures/xbrl/pbind/moves_200_2026-11-06.json", "fixtures/xbrl/pbind/regress97_2026-11-06.json", "fixtures/xbrl/pbind/inject_2026-11-06.json")
ENGINE_FILES = ("adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py")
#: engine の commit から 0 行でなければならない path(engine・lib・仕掛け)
NOT_TOUCHED_RELS = ("adapters", "core", "measure/lib", "measure/inject.py")
#: この便が読むだけの前の便の script・記録・門(engine の commit の blob と byte が同じでなければならない)。RB の便の門の部品(READ_ONLY_RELS)に、RB・T9 の第 2 便・T9 の分を足す
READ_ONLY_RELS = SGR.READ_ONLY_RELS + (
    "measure/xbrl_rmix_2026-11-04.py", "measure/xbrl_rmix_regress97_2026-11-04.py",
    "fixtures/xbrl/rmix/ai200_2026-11-04.json", "fixtures/xbrl/rmix/inject_2026-11-04.json", "fixtures/xbrl/rmix/regress97_2026-11-04.json",
    "tests/measure/test_xbrl_rmix_seal.py", "tests/measure/test_xbrl_rmix_result.py",
    "measure/xbrl_pswap_idmap_2026-11-06.py", "fixtures/xbrl/pswap/inject_idmap_2026-11-06.json",
    "tests/measure/test_xbrl_pswap_idmap_seal.py", "tests/measure/test_xbrl_pswap_idmap_result.py",
    "measure/xbrl_pswap_2026-11-06.py", "fixtures/xbrl/pswap/inject_2026-11-06.json",
    "tests/measure/test_xbrl_pswap_seal.py", "tests/measure/test_xbrl_pswap_result.py",
    "measure/xbrl_jtypes_2026-11-05.py", "measure/xbrl_nscan_2026-11-05.py",
    "measure/inject.py", "measure/lib/numbers.py", "measure/lib/scales.py", "measure/lib/sites.py")
RESERVED_PREFIXES = SGR.RESERVED_PREFIXES
DOCID_RE = SGR.DOCID_RE
PRED_IDS = tuple("E-%d" % i for i in range(1, 11))
K_IDS = tuple("K-%d" % i for i in range(1, 6))
#: 前の便の関数(この script は同名の関数を定義せず、前の便の module の関数を呼ぶ)。(module の別名, 関数名)
REUSED_FUNCS = (("RM", "load_jobs"), ("RM", "id_map"), ("RM", "label_of"), ("PI", "id_map"), ("PS", "t9_all_sites"), ("PS", "build_t9"), ("PS", "engine_cue"), ("PS", "has_prior_word"),
                ("PS", "pointer_period"), ("PS", "shape_of_token"), ("XR", "doc_job"), ("XR", "doc_rows"), ("XR", "engine_commits"), ("XR", "engine_link"))
#: 封の字の要点(封に無ければ赤)
SEAL_PHRASES = (
    u"**profile の旗の後ろだけ**で、既定 P27・P27E〜P30E は 1 行も変わらない",
    u"新しい profile は E 系だけ **P32E = P30E + 旗**",
    u"手がかりは**数の直前 12 字の窓だけ**",
    u"縛った後の state は **前期の fact を名指して VALUE_MISMATCH**",
    u"hits に context が `Prior1Year` で始まる fact が無い",
    u"`hits` から context が `CurrentYear` で始まる fact を外す(Prior2Year 以前は残す)",
    u"`Prior1Year` の fact があれば先頭を名指して `VALUE_MISMATCH`",
    u"増減の語(is_diff)があっても同じ",
    u"判定は記録から門が機械で求め、司令塔は覆さない。",
    u"1 つでも外れたら「採用しない(人間に返す)」",
    u"## 追記 1(2026-11-06",
    u"**前期の fact が無い要素**",
    u"**Prior2Year**",
    u"`xbrl_rmix_2026-11-04.py` の作り",
)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. 封の字
def seal_record_rels(seal):
    u"""封 §5 の中括弧の形 ``fixtures/xbrl/pbind/{a,b,c}_2026-11-06.json`` を展開した path の列。無ければ空。"""
    m = re.search(r"`(fixtures/xbrl/pbind)/\{([^}]*)\}(_2026-11-06\.json)`", seal)
    return [u"%s/%s%s" % (m.group(1), n.strip(), m.group(3)) for n in m.group(2).split(u",")] if m else []


def seal_engine_files(seal):
    u"""封 §2-1 の表の engine の file(``adapters/xbrl/*.py``)。出る順。"""
    sec21 = seal[seal.index("### §2-1"):seal.index("### §2-2")]
    return [m.group(1) for m in (re.match(r"^\| `(adapters/xbrl/[a-z_]+\.py)` \|", ln) for ln in sec21.splitlines()) if m]


def seal_problems(seal):
    out = []
    try:
        ids = SGR.table_ids(seal, "## §3", "## §4", r"^\| (E-\d+) \| (.*) \|$")
        sec = seal[seal.index("## §3"):seal.index("## §4")]
        sec4 = seal[seal.index("## §4"):seal.index("## §5")]
        sec5 = seal[seal.index("## §5"):seal.index("## §6")]
    except ValueError:
        return [u"封の節(§2-1・§3・§4・§5・§6)が揃っていない"]
    if ids != list(PRED_IDS):
        out.append(u"封 §3 の表が E-1〜E-10 の 10 行でない: %s" % ids)
    for line in sec.splitlines():
        m = re.match(r"^\| (E-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            if len(cells) < 3 or any(not c.strip() for c in cells[:3]):
                out.append(u"封 §3 の %s の欄(欄・予測・外れ方)が埋まっていない" % m.group(1))
    got_k = re.findall(r"^- (K-\d):", sec4, re.M)
    if got_k != list(K_IDS):
        out.append(u"封 §4 の K-1〜K-5 が揃っていない: %s" % got_k)
    for rel in SCRIPT_RELS + GATE_RELS + (DOC_REL,):
        if rel not in sec5:
            out.append(u"封 §5 に path が無い: %s" % rel)
    if seal_record_rels(seal) != list(RECORD_RELS):
        out.append(u"封 §5 の記録の path(中括弧の形)が script・門の持つ 3 つと違う: %s" % seal_record_rels(seal))
    if seal_engine_files(seal) != list(ENGINE_FILES):
        out.append(u"封 §2-1 の engine の file が recipes・vocabulary の 2 つでない: %s" % seal_engine_files(seal))
    for ph in SEAL_PHRASES:
        if ph not in seal:
            out.append(u"封に規則の要点の字が無い: %s" % ph)
    return out


# ---------------------------------------------------------------- 2. 封の字と script の定数
def script_problems(seal, pb=None):
    u"""封の字と script の定数が同じか。pb = script の module(試験が壊した写しを渡す)。"""
    pb = pb or PB
    out = []
    if pb.SEAL_REL != SEAL_REL or pb.SEAL_COMMIT != SEAL_COMMIT_SHORT or pb.ADDENDUM_COMMIT != ADDENDUM_COMMIT_SHORT:
        out.append(u"封の path・commit(最初の commit と追記 1 の commit)が違う")
    if tuple(pb.PROFILES) != ("P30E", "P32E") or (pb.OLD, pb.NEW) != ("P30E", "P32E"):
        out.append(u"profile の対が (P30E, P32E) でない")
    if tuple(pb.ENGINE_FILES) != tuple(seal_engine_files(seal)):
        out.append(u"engine の file が封 §2-1 の 2 file でない")
    if list(pb.REC_REL.values()) != seal_record_rels(seal) or tuple(pb.REC_REL) != ("moves", "regress97", "inject"):
        out.append(u"記録の path が封 §5 と違う")
    if pb.DOC_REL != DOC_REL or pb.SCRIPT_REL != SCRIPT_RELS[0]:
        out.append(u"結果の文書・script の path が封 §5 と違う")
    if pb.RB_RECORD_REL != "fixtures/xbrl/rmix/regress97_2026-11-04.json" or pb.T9_RECORD_REL != "fixtures/xbrl/pswap/inject_idmap_2026-11-06.json":
        out.append(u"比べ先の記録(RB の regress97・T9 の第 2 便)の path が封の字(E-2)と違う")
    if tuple(pb.BASE_PROFILES) != tuple(pb.RR.NOW_PROFILES) or tuple(pb.NOW_PROFILES) != tuple(pb.BASE_PROFILES) + ("P32E",):
        out.append(u"97 書類の profile が RB の便の記録の 9 つ + P32E でない(E-2 は P22〜P30E)")
    if tuple(pb.PERIODS5) != ("CurrentYear", "Prior1Year", "Prior2Year", u"他", u"なし"):
        out.append(u"期の語が 5 つ(Prior2Year を分ける。追記 1 の 4)でない")
    if tuple(pb.PAIRS) != ((u"P32E 対 P30E", "P30E", "P32E"),) or tuple(pb.KEYED) != ("P30E", "P32E"):
        out.append(u"XR に差し替える対が P32E 対 P30E でない")
    return out


# ---------------------------------------------------------------- 3. 触らない file(engine の commit の blob と byte が同じ)
def seal_and_engine(root=REPO, seal_rel=SEAL_REL):
    return SGR.engine_commit(root, PREFIX, seal_rel, ENGINE_FILES)


def frozen_since_engine_problems(rels=READ_ONLY_RELS, root=REPO, base=ROOT, seal_rel=SEAL_REL, impl_files=ENGINE_FILES):
    u"""root = git の木、base = 作業木の audit-core の folder。engine の commit(履歴から探す)の blob と作業木の byte を比べる。"""
    s, e = SGR.engine_commit(root, PREFIX, seal_rel, impl_files)
    if s is None or e is None:
        return [u"封か engine の commit が履歴に 1 つに決まらない"]
    out = []
    for rel in rels:
        blob = subprocess.run(["git", "show", "%s:%s%s" % (e, PREFIX, rel)], cwd=root, capture_output=True)
        if blob.returncode != 0:
            out.append(u"engine の commit に無い: %s" % rel)
            continue
        path = os.path.join(base, rel)
        if not os.path.exists(path):
            out.append(u"作業木に無い: %s" % rel)
            continue
        with open(path, "rb") as fh:
            if blob.stdout != fh.read():
                if SGR.t5y_declared_file_change(root, e, rel, base):      # 2026-11-06(T5Y): 仕掛けの 2 file と、T5Y の便の commit だけが触った前の便の門は宣言された遷移
                    continue
                if SGR.t_declared_file_change(root, e, rel, base):      # 2026-11-09(T): T の engine の commit が触った(T5Y の便の commit も触ってよい)前の便の門は宣言された遷移
                    continue
                out.append(u"engine の commit の blob と byte が違う: %s" % rel)
    return out


def untouched_since_engine_problems(rels=NOT_TOUCHED_RELS, root=REPO, seal_rel=SEAL_REL, impl_files=ENGINE_FILES):
    u"""engine の commit から作業木まで(未 commit を含む)で 0 行でなければならない path の変更。問題の列。"""
    s, e = SGR.engine_commit(root, PREFIX, seal_rel, impl_files)
    if s is None or e is None:
        return [u"封か engine の commit が履歴に 1 つに決まらない"]
    code, text = PR.git_in(root, "diff", "--numstat", e, "--", *[PREFIX + p for p in rels])
    if code != 0:
        return [u"git diff が失敗"]
    # 2026-11-06(T5Y): 仕掛けの 2 file(measure/inject.py・measure/lib/sites.py)に挿入だけを足した宣言された遷移(行数・sha16・封が履歴に在る、の全部が宣言と同じ行)だけを許す
    # 2026-11-09(T): 封 docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md §2-3 が宣言した遷移(recipes.py +57・vocabulary.py +5。削除 0。行数・sha16・封が履歴に在る、の全部が宣言と同じ行)も許す(SGR.t_declared_numstat)
    return [u"engine の commit から変わった: %s" % ln for ln in text.splitlines() if ln and not SGR.t5y_declared_numstat(ln, root=root) and not SGR.t_declared_numstat(ln, root=root)]


reserved_problems = SGR.reserved_problems


# ---------------------------------------------------------------- 5. 配線
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


def own_function_problems(src):
    u"""前の便の関数と同じ名前を、script 自身が定義・代入していないか(差し替えていない)。"""
    got = defined_names(src)
    return [u"前の便の関数 %s をこの script が自分で定義している" % f for _m, f in REUSED_FUNCS if f in got]


def calls_problems(src):
    u"""script の本文が ``<module>.<関数>`` を呼んでいる(または引いている)か。"""
    return [u"この script が %s.%s を使っていない" % (m, f) for m, f in REUSED_FUNCS if u"%s.%s" % (m, f) not in src]


def wiring_problems(pb=None):
    u"""この script が前の便の script の同じ instance を使っているか + XR の差し替えが届いているか。問題の列。"""
    pb = pb or PB
    out = list(pb.wiring_problems())
    missing = object()
    checks = (("NF", pb.RM, "NF"), ("GEN", pb.RM, "GEN"), ("RUN", pb.RM, "RUN"), ("TUNE", pb.RM, "TUNE"), ("XR", pb.RR, "XR"), ("R97", pb.RR, "R97"), ("D", pb.RR, "D"), ("PS", pb.PI, "PS"))
    for mine, holder, theirs in checks:
        if getattr(pb, mine, missing) is not getattr(holder, theirs, missing) or getattr(pb, mine, missing) is missing:
            out.append(u"%s がこの script と前の便の script で同じ instance でない" % mine)
    return out


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
        e10 = [i for i, ln in enumerate(lines) if ln.startswith("| E-10 |")]
        self.assertEqual(1, len(e10))
        self.assertNotEqual([], seal_problems("\n".join(lines[:e10[0]] + lines[e10[0] + 1:])))                       # 10 行が 9 行
        e5 = [i for i, ln in enumerate(lines) if ln.startswith("| E-5 |")][0]
        cells = lines[e5].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:e5] + [" | ".join(cells[:2]) + " |"] + lines[e5 + 1:])))   # 外れ方の欄が無い
        self.assertNotEqual([], seal_problems("\n".join(lines[:e5] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[e5 + 1:])))   # 予測の欄が空
        k5 = [i for i, ln in enumerate(lines) if ln.startswith("- K-5:")]
        self.assertEqual(1, len(k5))
        self.assertNotEqual([], seal_problems("\n".join(lines[:k5[0]] + lines[k5[0] + 1:])))
        self.assertNotEqual([], seal_problems(self.seal.replace("measure/xbrl_pbind_2026-11-06.py", "measure/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("{moves_200,regress97,inject}", "{moves_200,regress97}")))
        self.assertNotEqual([], seal_problems(self.seal.replace("fixtures/xbrl/pbind/{", "fixtures/xbrl/x/{")))
        self.assertNotEqual([], seal_problems(self.seal.replace("XBRL_PRIOR_CUE_BIND_ENGINE_RESULT_2026-11-06.md", "x.md")))
        self.assertNotEqual([], seal_problems(self.seal.replace("tests/measure/test_xbrl_pbind_result.py", "tests/measure/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("| `adapters/xbrl/vocabulary.py` |", "| `adapters/xbrl/comparators.py` |", 1)))
        self.assertNotEqual([], seal_problems(self.seal.replace("## §4", "## 四", 1)))

    def test_a_4_the_record_paths_and_engine_files_are_read_from_the_seal(self):
        self.assertEqual(list(RECORD_RELS), seal_record_rels(self.seal))
        self.assertEqual(list(ENGINE_FILES), seal_engine_files(self.seal))
        self.assertEqual([], seal_record_rels(self.seal.replace("{moves_200", "[moves_200")))


class ScriptMatchesSealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_b_1_the_script_agrees_with_the_seal(self):
        self.assertEqual([], script_problems(self.seal))

    def _fake(self, **ov):
        d = dict((k, getattr(PB, k)) for k in ("SEAL_REL", "SEAL_COMMIT", "ADDENDUM_COMMIT", "PROFILES", "OLD", "NEW", "ENGINE_FILES", "REC_REL", "DOC_REL", "SCRIPT_REL", "RB_RECORD_REL",
                                               "T9_RECORD_REL", "BASE_PROFILES", "NOW_PROFILES", "PERIODS5", "PAIRS", "KEYED"))
        d["RR"] = PB.RR
        d.update(ov)
        return types.SimpleNamespace(**d)

    def test_b_2_a_changed_script_constant_turns_it_red(self):
        self.assertEqual([], script_problems(self.seal, self._fake()))
        recs = PB.REC_REL
        for ov in (dict(SEAL_COMMIT="0000000"), dict(ADDENDUM_COMMIT="0000000"), dict(SEAL_REL="docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md"), dict(PROFILES=("P29E", "P30E")),
                   dict(NEW="P31E"), dict(OLD="P29E"), dict(ENGINE_FILES=PB.ENGINE_FILES + ("adapters/xbrl/comparators.py",)), dict(ENGINE_FILES=PB.ENGINE_FILES[:1]),
                   dict(REC_REL=dict(list(recs.items())[:2])), dict(REC_REL=type(recs)([("moves", "fixtures/xbrl/pbind/x.json")] + list(recs.items())[1:])),
                   dict(DOC_REL="docs/x.md"), dict(SCRIPT_REL="measure/x.py"), dict(RB_RECORD_REL="fixtures/xbrl/numfix/regress97_2026-11-04.json"),
                   dict(T9_RECORD_REL="fixtures/xbrl/pswap/inject_2026-11-06.json"), dict(BASE_PROFILES=PB.BASE_PROFILES[:-1]), dict(NOW_PROFILES=PB.NOW_PROFILES[:-1]),
                   dict(PERIODS5=("CurrentYear", "Prior1Year", u"他", u"なし")), dict(PAIRS=((u"P30E 対 P29E", "P29E", "P30E"),)), dict(KEYED=("P29E", "P30E"))):
            self.assertNotEqual([], script_problems(self.seal, self._fake(**ov)), sorted(ov))
        self.assertNotEqual([], script_problems(self.seal.replace("| `adapters/xbrl/vocabulary.py` |", "| `adapters/xbrl/comparators.py` |", 1), self._fake()))


class NotTouchedAndFrozenTest(unittest.TestCase):
    def test_c_1_engine_lib_and_inject_are_untouched_since_the_engine_commit(self):
        self.assertEqual([], untouched_since_engine_problems())

    def test_c_1b_the_engine_commit_is_found_from_history_and_is_after_the_seal(self):
        s, e = seal_and_engine()
        self.assertTrue(s and s.startswith(SEAL_COMMIT_SHORT))
        self.assertTrue(e and e != s)
        self.assertTrue(PR.is_anc(REPO, s, e))

    def _repo(self, extra_change=None):
        r = PR.Repo()
        r.put("measure/lib/x.py")
        r.put("measure/prev.py")
        r.put(SEAL_REL)
        r.commit("measure/lib/x.py", "measure/prev.py", SEAL_REL)
        r.put("adapters/xbrl/recipes.py")
        r.put("adapters/xbrl/vocabulary.py")
        r.commit(*ENGINE_FILES)
        if extra_change:
            r.put(extra_change)
        return r

    def test_c_2_the_untouched_check_sees_a_changed_line_even_uncommitted(self):
        r = self._repo()
        self.assertEqual([], untouched_since_engine_problems(rels=("adapters", "measure/lib"), root=r.d))
        for rel in ("measure/lib/x.py", "adapters/xbrl/recipes.py"):
            r2 = self._repo(extra_change=rel)                                           # 未 commit の変更
            self.assertNotEqual([], untouched_since_engine_problems(rels=("adapters", "measure/lib"), root=r2.d), rel)
        r3 = self._repo()
        r3.put("measure/lib/x.py")
        r3.commit("measure/lib/x.py")                                                   # engine の commit の後に commit された変更
        self.assertNotEqual([], untouched_since_engine_problems(rels=("adapters", "measure/lib"), root=r3.d))
        r4 = PR.Repo()                                                                  # engine の commit が無い
        r4.put(SEAL_REL)
        r4.commit(SEAL_REL)
        self.assertNotEqual([], untouched_since_engine_problems(rels=("adapters",), root=r4.d))

    def test_d_1_previous_scripts_records_and_gates_are_byte_identical_to_the_engine_commit(self):
        self.assertEqual([], frozen_since_engine_problems())

    def test_d_1b_the_previous_scripts_records_gates_lib_and_inject_are_in_the_read_only_list(self):
        for rel in ("measure/xbrl_rmix_2026-11-04.py", "measure/xbrl_rmix_regress97_2026-11-04.py", "fixtures/xbrl/rmix/regress97_2026-11-04.json", "fixtures/xbrl/rmix/ai200_2026-11-04.json",
                    "tests/measure/test_xbrl_rmix_seal.py", "tests/measure/test_xbrl_rmix_result.py", "measure/xbrl_pswap_idmap_2026-11-06.py", "fixtures/xbrl/pswap/inject_idmap_2026-11-06.json",
                    "tests/measure/test_xbrl_pswap_idmap_seal.py", "tests/measure/test_xbrl_pswap_idmap_result.py", "measure/xbrl_pswap_2026-11-06.py", "measure/xbrl_numfix_2026-11-04.py",
                    "measure/xbrl_numfix_regress97_2026-11-04.py", "measure/inject.py", "measure/lib/numbers.py", "measure/lib/sites.py", "measure/xbrl_p27_tune_2026-10-27.py"):
            self.assertIn(rel, READ_ONLY_RELS)
        self.assertEqual(len(READ_ONLY_RELS), len(set(READ_ONLY_RELS)))
        for rel in READ_ONLY_RELS:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_d_2_the_frozen_check_sees_a_changed_file_a_missing_one_and_a_file_without_the_engine_commit(self):
        self.assertNotEqual([], frozen_since_engine_problems(rels=READ_ONLY_RELS + (SCRIPT_RELS[0],)))              # engine の commit に無い file(script は engine の後)
        self.assertNotEqual([], frozen_since_engine_problems(rels=("measure/xbrl_pswap_2026-11-06.py", "measure/nonexistent_file.py")))
        r = PR.Repo()                                                                                                   # 封も engine の commit も無い repo
        r.put("measure/prev.py")
        r.commit("measure/prev.py")
        self.assertNotEqual([], frozen_since_engine_problems(rels=("measure/prev.py",), root=r.d, base=os.path.join(r.d, "audit-core")))

    def test_d_3_the_frozen_check_goes_red_when_a_tracked_file_changes_after_the_engine_commit(self):
        r = PR.Repo()
        r.put("measure/prev.py")
        r.put(SEAL_REL)
        r.commit("measure/prev.py", SEAL_REL)
        r.put("measure/other.py")
        r.put("adapters/xbrl/recipes.py")
        r.put("adapters/xbrl/vocabulary.py")
        r.commit("measure/other.py", *ENGINE_FILES)
        base = os.path.join(r.d, "audit-core")
        self.assertEqual([], frozen_since_engine_problems(rels=("measure/prev.py", "measure/other.py"), root=r.d, base=base))
        with open(os.path.join(base, "measure/prev.py"), "a", encoding="utf-8") as fh:
            fh.write("x = 1\n")
        self.assertEqual([u"engine の commit の blob と byte が違う: measure/prev.py"], frozen_since_engine_problems(rels=("measure/prev.py", "measure/other.py"), root=r.d, base=base))
        r.put("measure/later.py")
        r.commit("measure/later.py")
        self.assertEqual([u"engine の commit に無い: measure/later.py"], frozen_since_engine_problems(rels=("measure/later.py",), root=r.d, base=base))

    def test_d_4_a_file_changed_between_the_seal_and_the_engine_commit_is_still_frozen_from_the_engine_commit(self):
        u"""RB の便の門のように、engine の commit が触った file(PB の宣言された遷移)は engine の commit の blob を基準にする。封の commit の blob とは違ってよい。"""
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        r.commit("measure/gate.py", SEAL_REL)
        r.put("measure/gate.py")
        r.put("adapters/xbrl/recipes.py")
        r.put("adapters/xbrl/vocabulary.py")
        r.commit("measure/gate.py", *ENGINE_FILES)
        self.assertEqual([], frozen_since_engine_problems(rels=("measure/gate.py",), root=r.d, base=os.path.join(r.d, "audit-core")))

    # ------------------------------------------------ 2026-11-06(T5Y): 仕掛けの 2 file と T5Y の便の門への宣言された遷移(部品は rmix の門の t5y_*)
    def _t5y_repo(self, extra_commit=False, dirty=False, touch_device=True, t5y_seal=True, gate_in_engine=False):
        u"""封 → engine の commit → (T5Y の封)→ T5Y の便の commit(仕掛けの 2 file と前の便の門を触る)→ ..."""
        r = PR.Repo()
        r.put("measure/gate.py")
        for rel in SGR.T5Y_FILES:
            r.put(rel)
        r.put(SEAL_REL)
        r.commit("measure/gate.py", SEAL_REL, *SGR.T5Y_FILES)
        r.put("adapters/xbrl/recipes.py")
        r.put("adapters/xbrl/vocabulary.py")
        if gate_in_engine:
            r.put("measure/gate.py")                                                                                   # PB の engine の commit も触った門(封の後)
        r.commit(*(ENGINE_FILES + (("measure/gate.py",) if gate_in_engine else ())))
        if t5y_seal:
            r.put(SGR.T5Y_SEAL_REL)
            r.commit(SGR.T5Y_SEAL_REL)
        r.put("measure/gate.py")
        files = ["measure/gate.py"] + (list(SGR.T5Y_FILES) if touch_device else [])
        for rel in files:
            r.put(rel)
        r.commit(*files)
        if extra_commit:
            r.put("measure/gate.py")
            r.commit("measure/gate.py")
        if dirty:
            r.put("measure/gate.py")
        return r

    def test_t5y_1_the_declared_transition_of_the_device_is_accepted_and_it_really_differs_from_the_engine_commit(self):
        s, e = seal_and_engine()
        for rel in SGR.T5Y_FILES:
            blob = subprocess.run(["git", "show", "%s:%s%s" % (e, PREFIX, rel)], cwd=REPO, capture_output=True).stdout
            with open(os.path.join(ROOT, rel), "rb") as fh:
                self.assertNotEqual(blob, fh.read(), rel)                                                          # 遷移は実際に起きている(空の門にしない)
        self.assertEqual([], frozen_since_engine_problems(rels=SGR.T5Y_FILES))
        self.assertEqual([], untouched_since_engine_problems(rels=("measure/lib", "measure/inject.py")))

    def test_t5y_2_a_gate_changed_only_by_the_t5y_commit_is_accepted(self):
        r = self._t5y_repo()
        base = os.path.join(r.d, "audit-core")
        self.assertEqual([], frozen_since_engine_problems(rels=("measure/gate.py",), root=r.d, base=base))

    def test_t5y_2b_a_gate_changed_by_the_engine_commit_and_then_by_the_t5y_commit_is_compared_from_the_engine_commit(self):
        r = self._t5y_repo(gate_in_engine=True)
        self.assertEqual([], frozen_since_engine_problems(rels=("measure/gate.py",), root=r.d, base=os.path.join(r.d, "audit-core")))
        r2 = self._t5y_repo(gate_in_engine=True, extra_commit=True)
        self.assertNotEqual([], frozen_since_engine_problems(rels=("measure/gate.py",), root=r2.d, base=os.path.join(r2.d, "audit-core")))

    def test_t5y_3_a_gate_changed_again_or_uncommitted_or_without_the_device_is_red(self):
        for kw in ({"extra_commit": True}, {"dirty": True}, {"touch_device": False}, {"t5y_seal": False}):
            r = self._t5y_repo(**kw)
            base = os.path.join(r.d, "audit-core")
            self.assertEqual([u"engine の commit の blob と byte が違う: measure/gate.py"], frozen_since_engine_problems(rels=("measure/gate.py",), root=r.d, base=base), kw)

    def test_t5y_4_the_untouched_check_does_not_accept_other_changes_of_lib_and_inject(self):
        r = self._t5y_repo()
        base = os.path.join(r.d, "audit-core")
        self.assertNotEqual([], untouched_since_engine_problems(rels=("measure/lib", "measure/inject.py"), root=r.d))        # 宣言の行数・sha16 と違う変更(この repo の file は宣言の値でない)
        self.assertNotEqual([], untouched_since_engine_problems(rels=("adapters",), root=self._t5y_adapter_change().d))
        self.assertNotEqual([], untouched_since_engine_problems(rels=("measure/lib",), root=self._t5y_repo(t5y_seal=False).d))

    def _t5y_adapter_change(self):
        r = self._t5y_repo()
        r.put("adapters/xbrl/recipes.py")                                                                                # engine は T5Y の宣言に入らない
        return r

    def test_t5y_5_the_declared_numstat_of_the_device_is_not_accepted_for_the_engine_files(self):
        for rel in ("adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py", "core/py/audit_core/verify.py", "measure/lib/numbers.py", "measure/lib/scales.py"):
            self.assertFalse(SGR.t5y_declared_numstat("81\t0\t%s%s" % (PREFIX, rel)), rel)
            self.assertFalse(SGR.t5y_declared_numstat("30\t0\t%s%s" % (PREFIX, rel)), rel)

    def test_t5y_6_the_declared_numstat_is_accepted_only_when_the_t5y_seal_is_in_the_history_of_the_tree_checked(self):
        u"""宣言の行数(81 / 0)と同じ変更でも、調べる木の履歴に T5Y の封が無ければ赤(``root`` を渡して履歴を見る)。sha16 は現物(この木)の file で見る。"""
        def repo(with_seal):
            r = PR.Repo()
            r.put("measure/lib/sites.py")
            r.put(SEAL_REL)
            r.commit("measure/lib/sites.py", SEAL_REL)
            r.put("adapters/xbrl/recipes.py")
            r.put("adapters/xbrl/vocabulary.py")
            r.commit(*ENGINE_FILES)
            if with_seal:
                r.put(SGR.T5Y_SEAL_REL)
                r.commit(SGR.T5Y_SEAL_REL)
            with open(os.path.join(r.d, PREFIX, "measure/lib/sites.py"), "a", encoding="utf-8") as fh:
                fh.write(u"y = 1\n" * 81)                                                 # 挿入 81・削除 0
            return r
        self.assertNotEqual([], untouched_since_engine_problems(rels=("measure/lib",), root=repo(False).d))
        self.assertEqual([], untouched_since_engine_problems(rels=("measure/lib",), root=repo(True).d))

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
            self.assertIn("XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md", read(rel), rel)


class WiringTest(unittest.TestCase):
    def test_w_1_the_script_uses_the_same_instances_as_the_previous_scripts(self):
        self.assertEqual([], wiring_problems())
        self.assertIs(PB.XR, PB.RR.XR)
        self.assertIs(PB.PS, PB.PI.PS)
        self.assertIs(PB.NF, PB.RM.NF)
        self.assertIs(PB.R97, PB.XR.R97)

    def test_w_2_another_instance_or_a_missed_swap_turns_the_wiring_check_red(self):
        for name in ("NF", "GEN", "RUN", "TUNE", "XR", "R97", "D", "PS"):
            fake = types.SimpleNamespace(**dict((k, getattr(PB, k)) for k in dir(PB) if not k.startswith("__")))
            setattr(fake, name, types.SimpleNamespace())
            self.assertNotEqual([], wiring_problems(fake), name)
        self.assertEqual([], wiring_problems())

    def test_w_3_the_xr_swap_reaches_the_users_and_a_missed_swap_is_reported(self):
        for name, v in PB.XR_SWAP:
            self.assertEqual(v, getattr(XR, name), name)
        old = XR.PAIRS
        XR.PAIRS = (("P30E 対 P29E", "P29E", "P30E"),)
        try:
            self.assertTrue(any(u"XR.PAIRS" in x for x in PB.wiring_problems()))
        finally:
            XR.PAIRS = old
        old = XR.ENGINE_FILES
        XR.ENGINE_FILES = old + ("adapters/xbrl/comparators.py",)
        try:
            self.assertTrue(any(u"XR.ENGINE_FILES" in x for x in PB.wiring_problems()))
        finally:
            XR.ENGINE_FILES = old
        self.assertEqual([], PB.wiring_problems())

    def test_w_4_the_xr_module_is_the_one_the_regress_script_loaded_and_its_users_read_the_swapped_names(self):
        self.assertIs(XR.engine_commits.__globals__["ENGINE_FILES"], XR.ENGINE_FILES)
        self.assertEqual(tuple(PB.ENGINE_FILES), tuple(XR.engine_commits.__globals__["ENGINE_FILES"]))
        self.assertEqual("b7824e6", XR.engine_commits.__globals__["SEAL_COMMIT"])
        self.assertEqual(tuple(PB.NOW_PROFILES), tuple(XR.doc_rows.__globals__["NOW_PROFILES"]))
        self.assertEqual(tuple(PB.BASE_PROFILES), tuple(XR.doc_rows.__globals__["BASE_PROFILES"]))
        self.assertEqual(tuple(PB.KEYED), tuple(XR.doc_job.__globals__["KEYED"]))

    def test_w_5_the_base_pair_swap_reaches_the_base_status_function_and_goes_back(self):
        self.assertEqual(("P29E", "P30E"), tuple(PI.RM.INJECT_PROFILES))
        with PB.base_pair():
            self.assertEqual(("P32E", "P30E"), tuple(PI.RM.base_status_rb.__globals__["INJECT_PROFILES"]))
        self.assertEqual(("P29E", "P30E"), tuple(PI.RM.base_status_rb.__globals__["INJECT_PROFILES"]))
        try:
            with PB.base_pair():
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertEqual(("P29E", "P30E"), tuple(PI.RM.INJECT_PROFILES))

    def test_w_6_the_script_defines_none_of_the_previous_functions_and_uses_them(self):
        src = read(SCRIPT_RELS[0])
        self.assertEqual([], own_function_problems(src))
        self.assertEqual([], calls_problems(src))
        for m, f in REUSED_FUNCS:
            self.assertTrue(callable(getattr(getattr(PB, m), f)), (m, f))
            self.assertFalse(hasattr(PB, f), f)                                   # PB の名前空間に同名の関数を持たない
            self.assertNotEqual([], own_function_problems(src + u"\n\ndef %s(*a):\n    return None\n" % f), f)
            self.assertNotEqual([], own_function_problems(src + u"\n%s = None\n" % f), f)
            self.assertNotEqual([], calls_problems(src.replace(u"%s.%s" % (m, f), u"X.%s" % f)), (m, f))

    def test_w_7_the_script_loads_the_previous_scripts_with_importlib_and_does_not_edit_them(self):
        src = read(SCRIPT_RELS[0])
        for name in ("xbrl_rmix_2026-11-04.py", "xbrl_rmix_regress97_2026-11-04.py", "xbrl_pswap_idmap_2026-11-06.py"):
            self.assertIn(u'load_module("%s"' % name, src)
        self.assertEqual(3, src.count(u"load_module(\"xbrl_"))


class OrderTest(unittest.TestCase):
    def test_o_1_the_real_history_has_the_seal_before_the_engine_before_the_scripts_and_gates(self):
        u"""script・門のどれかが未 commit なら赤(足した commit が無い)。engine の commit の hash は履歴から探す。"""
        self.assertEqual([], PR.order_problems(REPO, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, ENGINE_FILES, SCRIPT_RELS + GATE_RELS))


OTHERS = ["measure/a.py", "tests/g.py"]
IMPLS = list(ENGINE_FILES)
SEALF = "docs/seal.md"


def order_of(r, seal_short):
    return PR.order_problems(r.d, PREFIX, SEALF, seal_short, IMPLS, OTHERS)


class OrderMutationTest(unittest.TestCase):
    def _repo(self, before_impl=(), after_seal_before_impl=(), after_impl=OTHERS, seal_touches=None):
        r = PR.Repo()
        for f in before_impl:
            r.put(f)
            r.commit(f)
        if seal_touches:
            r.put(seal_touches)
        r.put(SEALF)
        s = r.commit(SEALF, *([seal_touches] if seal_touches else []))
        for f in after_seal_before_impl:
            r.put(f)
            r.commit(f)
        for f in IMPLS:
            r.put(f)
        r.commit(*IMPLS)
        for f in after_impl:
            r.put(f)
        if after_impl:
            r.commit(*after_impl)
        return r, s[:7]

    def test_p_1_a_correct_order_is_green(self):
        r, s = self._repo()
        self.assertEqual([], order_of(r, s))

    def test_p_2_a_script_before_the_engine_or_before_the_seal_is_red(self):
        r, s = self._repo(after_seal_before_impl=[OTHERS[0]], after_impl=OTHERS[1:])
        self.assertIn("BEFORE_IMPL:" + OTHERS[0], order_of(r, s))
        r2, s2 = self._repo(before_impl=[OTHERS[0]], after_impl=OTHERS[1:])
        self.assertIn("BEFORE_SEAL:" + OTHERS[0], order_of(r2, s2))

    def test_p_3_an_uncommitted_script_and_an_uncommitted_engine_are_red_not_skipped(self):
        r, s = self._repo(after_impl=OTHERS[:1])
        self.assertEqual(["UNCOMMITTED:" + OTHERS[1]], order_of(r, s))
        r2 = PR.Repo()
        r2.put(SEALF)
        s2 = r2.commit(SEALF)
        r2.put(IMPLS[0])
        r2.commit(IMPLS[0])
        self.assertTrue(any(p.startswith("IMPL_UNCOMMITTED:") for p in order_of(r2, s2[:7])))

    def test_p_4_a_wrong_seal_hash_or_a_seal_that_touches_the_engine_is_red(self):
        r, s = self._repo()
        self.assertIn("SEAL_NOT_THE_SEALED", order_of(r, "0000000"))
        r2, s2 = self._repo(before_impl=[IMPLS[0]], seal_touches=IMPLS[0])
        self.assertIn("SEAL_TOUCHES_ENGINE", order_of(r2, s2))

    def test_p_5_the_engine_commit_is_found_from_history_without_a_hash(self):
        r, s = self._repo()
        seal, e = SGR.engine_commit(r.d, PREFIX, SEALF, IMPLS)
        self.assertTrue(seal.startswith(s))
        self.assertTrue(e and e != seal)
        self.assertEqual(e, PR.git_in(r.d, "rev-parse", "HEAD~1")[1])


if __name__ == "__main__":
    unittest.main()
