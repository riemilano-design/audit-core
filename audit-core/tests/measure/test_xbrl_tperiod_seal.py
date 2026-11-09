# -*- coding: utf-8 -*-
"""封 docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md(規則 T ― 表の見出しの「前期」の列の数を前期の手がかりがある数として扱う。P33E = P32E + 旗。既定にしない)の測定の門。封 §3・§4・§5。

**この門が縛るもの**(結果の門 ``test_xbrl_tperiod_result.py`` は記録・文書・採用の判定・行の欄を縛る)

1. 封の字: §3 の予測の表が T-1〜T-10 の 10 行でどの行も予測と外れ方の欄を持つ・§4 の K-1〜K-5・§5 の path(script・記録 3 つ・門 2 本・結果の文書)・規則の要点(旗の後ろだけ・P33E のみ・
   同じ扱い・「比・増減・率・差」・前期 1 列/当期 1 列以下・セルの数・cap なし・原文では届かない)。封の字を 1 字変えると赤。
2. 封の字と script の定数が同じ: 封の path と commit(封 eb281f1)・profile の対(P32E → P33E)・T の幅(封の字から読んだ値を literal に留めた値と照らす)・engine の 2 file・記録の path・
   結果の文書の path・前の便の記録(PB の regress97・inject)の path・97 書類の profile(PB の 10 + P33E)。
3. 触らない file は **engine の commit の blob と byte が同じ**: PB の script・記録 3 つ・門 2 本、前の便(RB・T9・T9 の第 2 便・T5Y・J・H・N)の script・記録・門と ``measure/inject.py``・``measure/lib``。
   engine(``core/``・``adapters/``)は engine の commit から 0 行。engine の commit の hash を字で持たず、履歴から探す。後の便が足す宣言された遷移の部品は PB の便の形(``SGP`` の関数)を呼ぶ。
4. 順序: 封 eb281f1 ⊏ engine を触った commit ⊏ script・門 2 本(記録・結果の文書の順序は結果の門が見る)。未 commit は赤(skip にしない)。
5. 配線: この script が PB の script・RB の便の script・T9 の第 2 便の script の同じ instance を使う。PB の module の差し替え(OLD・NEW・PROFILES・記録の path・封)と XR(RB の regress97 script)の
   差し替えが使う側の実体に届く。前の便の関数を**そのまま呼ぶ**(この script は同名の関数を定義しない)。(a) の対(P30E・P33E)の差し替えは with を出ると戻る。
   script が読み込む前の便の script が ``sys.modules`` の名前を上書きしても、読み込みの前に居た名前は元の object へ戻る(2 通りの順で赤くならない)。
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
    (さもないと pytest の引数で RB の結果の門を先に並べたとき、RB の門が持つ object と ``sys.modules`` の object が別になって赤くなる。7109c97 の直しと同じ形)。
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


SGP = load_module("tests/measure/test_xbrl_pbind_seal.py", "pbind_seal_gate_for_tperiod_seal")      # PB の封の門の部品(触らない file の比べ・順序・行頭の名前)。門としては走らせない
SGR = SGP.SGR
PR = SGP.PR
TPR = load_module("measure/xbrl_tperiod_2026-11-09.py", "tperiod_script_for_seal_gate")
PB, RM, RR, PI, PS, XR = TPR.PB, TPR.RM, TPR.RR, TPR.PI, TPR.PS, TPR.XR

SEAL_REL = TPR.SEAL_REL
SEAL_COMMIT_SHORT = "eb281f1"                     # 封の最初の commit(literal に留める。script の定数と違えば script_problems が赤)
DOC_REL = TPR.DOC_REL
SCRIPT_RELS = ("measure/xbrl_tperiod_2026-11-09.py",)
GATE_RELS = ("tests/measure/test_xbrl_tperiod_seal.py", "tests/measure/test_xbrl_tperiod_result.py")
RECORD_RELS = ("fixtures/xbrl/tperiod/moves_200_2026-11-09.json", "fixtures/xbrl/tperiod/regress97_2026-11-09.json", "fixtures/xbrl/tperiod/inject_2026-11-09.json")
ENGINE_FILES = ("adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py")
#: 封 §2-3 が宣言した engine の遷移(literal に留める。後の便の宣言された遷移の部品 ``SGR.t_declared_*`` の値と同じでなければ赤)
ENGINE_NUMSTAT_PIN = {"adapters/xbrl/recipes.py": (57, 0), "adapters/xbrl/vocabulary.py": (5, 0)}
ENGINE_SHA16_PIN = {"adapters/xbrl/recipes.py": "346adb0d586e3af2", "adapters/xbrl/vocabulary.py": "369891933a5876c4"}
ENGINE_FP_PIN = "5221d3c9a7bdb5c9833dee52490b0064255bdb54fb3210f1b19c1d19f28f9116"
#: engine の commit から 0 行でなければならない path(engine・lib・仕掛け)
NOT_TOUCHED_RELS = ("adapters", "core", "measure/lib", "measure/inject.py")
#: この便が読むだけの前の便の script・記録・門(engine の commit の blob と byte が同じでなければならない)。PB の便の門の部品(READ_ONLY_RELS)に PB の script・記録・門を足す
READ_ONLY_RELS = SGP.READ_ONLY_RELS + (
    "measure/xbrl_pbind_2026-11-06.py",
    "fixtures/xbrl/pbind/moves_200_2026-11-06.json", "fixtures/xbrl/pbind/regress97_2026-11-06.json", "fixtures/xbrl/pbind/inject_2026-11-06.json",
    "tests/measure/test_xbrl_pbind_seal.py", "tests/measure/test_xbrl_pbind_result.py")
RESERVED_PREFIXES = SGR.RESERVED_PREFIXES
DOCID_RE = SGR.DOCID_RE
PRED_IDS = tuple("T-%d" % i for i in range(1, 11))
K_IDS = tuple("K-%d" % i for i in range(1, 6))
#: 前の便の関数(この script は同名の関数を定義せず、前の便の module の関数を呼ぶ)。(module の別名, 関数名)
REUSED_FUNCS = (("PB", "judge_book_pb"), ("PB", "doc_moves_pb"), ("PB", "moves_block"), ("PB", "inject_job_pb"), ("PB", "write_record"), ("PB", "engine_numstat"), ("PB", "engine_message"),
                ("PB", "moves_inputs"), ("PB", "period5"), ("PB", "install"), ("XR", "doc_job"), ("XR", "doc_rows"), ("XR", "engine_commits"), ("XR", "engine_link"),
                ("RM", "load_jobs"), ("PI", "load_books"))
#: 封の字の要点(封に無ければ赤)
SEAL_PHRASES = (
    u"規則は **profile の旗の後ろだけ**で、既定 P27・P27E〜P32E は 1 行も変わらない",
    u"新しい profile は E 系だけ **P33E = P32E + 旗**",
    u"表の前期の列の数は、`_prior_cue` と `_prior_cue_window_2026_11_06` が真を返す数と**同じ扱い**",
    u"列の見出しに「比・増減・率・差」の字があれば期の列にしない",
    u"見出しが使えるのは「前期」がちょうど 1 列・「当期」が 1 列以下のときだけ",
    u"セルの数が見出しと違う行は入れない",
    u"判定は記録から門が機械で求め、司令塔は覆さない。",
    u"1 つでも外れたら「採用しない(人間に返す)」",
    u"分母 0 は外れ",
    u"対応は文の番号と替えたセルの数の位置",
    u"site は全部採る(cap なし)",
    u"**原文では規則 T は届かない**",
    u"行頭が `|` の文 / 動いた行 / GROUNDED を失う行",
)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. 封の字
def seal_record_rels(seal):
    u"""封 §5 の ``fixtures/xbrl/tperiod/<名前>_2026-11-09.json`` の path の列(出る順)。無ければ空。"""
    try:
        sec5 = seal[seal.index("## §5"):seal.index("## §6")]
    except ValueError:
        return []
    return re.findall(r"`(fixtures/xbrl/tperiod/[a-z0-9_]+_2026-11-09\.json)`", sec5)


def seal_engine_files(seal):
    u"""封 §2-1 の表の engine の file(``adapters/xbrl/*.py``)。出る順。"""
    sec21 = seal[seal.index("### §2-1"):seal.index("### §2-2")]
    return [m.group(1) for m in (re.match(r"^\| `(adapters/xbrl/[a-z_]+\.py)` \|", ln) for ln in sec21.splitlines()) if m]


def seal_problems(seal):
    out = []
    try:
        ids = SGR.table_ids(seal, "## §3", "## §4", r"^\| (T-\d+) \| (.*) \|$")
        sec = seal[seal.index("## §3"):seal.index("## §4")]
        sec4 = seal[seal.index("## §4"):seal.index("## §5")]
        sec5 = seal[seal.index("## §5"):seal.index("## §6")]
    except ValueError:
        return [u"封の節(§2-1・§3・§4・§5・§6)が揃っていない"]
    if ids != list(PRED_IDS):
        out.append(u"封 §3 の表が T-1〜T-10 の 10 行でない: %s" % ids)
    for line in sec.splitlines():
        m = re.match(r"^\| (T-\d+) \| (.*) \|$", line)
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
        out.append(u"封 §5 の記録の path が script・門の持つ 3 つと違う: %s" % seal_record_rels(seal))
    if seal_engine_files(seal) != list(ENGINE_FILES):
        out.append(u"封 §2-1 の engine の file が recipes・vocabulary の 2 つでない: %s" % seal_engine_files(seal))
    for ph in SEAL_PHRASES:
        if ph not in seal:
            out.append(u"封に規則の要点の字が無い: %s" % ph)
    return out


# ---------------------------------------------------------------- 2. 封の字と script の定数
def script_problems(seal, tp=None):
    u"""封の字と script の定数が同じか。tp = script の module(試験が壊した写しを渡す)。"""
    tp = tp or TPR
    out = []
    if tp.SEAL_REL != SEAL_REL or tp.SEAL_COMMIT != SEAL_COMMIT_SHORT:
        out.append(u"封の path・commit が違う")
    if tuple(tp.PROFILES) != ("P32E", "P33E") or (tp.OLD, tp.NEW) != ("P32E", "P33E"):
        out.append(u"profile の対が (P32E, P33E) でない")
    if tp.INJECT_A_PROFILES != ("P30E", "P33E") or tp.BASE_OLD != "P30E":
        out.append(u"(a) の profile の対が (P30E, P33E) でない")
    if tuple(tp.ENGINE_FILES) != tuple(seal_engine_files(seal)):
        out.append(u"engine の file が封 §2-1 の 2 file でない")
    if list(tp.REC_REL.values()) != seal_record_rels(seal) or tuple(tp.REC_REL) != ("moves", "regress97", "inject"):
        out.append(u"記録の path が封 §5 と違う")
    if tp.DOC_REL != DOC_REL or tp.SCRIPT_REL != SCRIPT_RELS[0]:
        out.append(u"結果の文書・script の path が封 §5 と違う")
    if tp.PB_REGRESS97_REL != "fixtures/xbrl/pbind/regress97_2026-11-06.json" or tp.PB_INJECT_REL != "fixtures/xbrl/pbind/inject_2026-11-06.json":
        out.append(u"比べ先の記録(PB の regress97・inject)の path が封の字(T-2)と違う")
    if tuple(tp.BASE_PROFILES) != ("P22", "P26", "P27", "P27E", "P28", "P28E", "P29", "P29E", "P30E", "P32E") or tuple(tp.NOW_PROFILES) != tuple(tp.BASE_PROFILES) + ("P33E",):
        out.append(u"97 書類の profile が P22〜P32E の 10 + P33E でない(T-2 は旗が偽の 10 profile)")
    if tuple(tp.PAIRS) != ((u"P33E 対 P32E", "P32E", "P33E"),) or tuple(tp.KEYED) != ("P32E", "P33E"):
        out.append(u"XR に差し替える対が P33E 対 P32E でない")
    if tuple(tp.PERIODS5) != ("CurrentYear", "Prior1Year", "Prior2Year", u"他", u"なし"):
        out.append(u"期の語が 5 つでない")
    if tuple(tp.PREV_SCRIPT_RELS[:1]) != ("measure/xbrl_pbind_2026-11-06.py",):
        out.append(u"前の便の script の先頭が PB の script でない")
    if (tp.TP, tp.TC) != (u"TP", u"TC"):
        out.append(u"注入の型の名前が TP・TC でない")
    return out


# ---------------------------------------------------------------- 3. 触らない file(engine の commit の blob と byte が同じ)
def seal_and_engine(root=REPO, seal_rel=SEAL_REL):
    return SGR.engine_commit(root, PREFIX, seal_rel, ENGINE_FILES)


def frozen_since_engine_problems(rels=READ_ONLY_RELS, root=REPO, base=ROOT, seal_rel=SEAL_REL, impl_files=ENGINE_FILES):
    u"""PB の便の部品をそのまま使う(封と engine の commit だけをこの便のものにする)。root = git の木、base = 作業木の audit-core の folder。"""
    return SGP.frozen_since_engine_problems(rels=rels, root=root, base=base, seal_rel=seal_rel, impl_files=impl_files)


def untouched_since_engine_problems(rels=NOT_TOUCHED_RELS, root=REPO, seal_rel=SEAL_REL, impl_files=ENGINE_FILES):
    return SGP.untouched_since_engine_problems(rels=rels, root=root, seal_rel=seal_rel, impl_files=impl_files)


reserved_problems = SGR.reserved_problems


def engine_numstat_at_history(root=REPO, seal_rel=SEAL_REL, impl_files=ENGINE_FILES):
    u"""封の commit から engine の commit までの ``adapters``・``core`` の numstat {file: (挿入, 削除)}。履歴から作る。"""
    s, e = SGR.engine_commit(root, PREFIX, seal_rel, impl_files)
    if s is None or e is None:
        return None
    lines = [x for x in PR.git_in(root, "diff", "--numstat", s, e, "--", PREFIX + "adapters", PREFIX + "core")[1].splitlines() if x]
    return dict((x.split("\t")[2][len(PREFIX):], (int(x.split("\t")[0]), int(x.split("\t")[1]))) for x in lines)


def engine_sha16_at_history(root=REPO, seal_rel=SEAL_REL, impl_files=ENGINE_FILES):
    u"""engine の commit の blob の sha16(sha256 の先頭 16 字)。{file: sha16}。"""
    import hashlib
    s, e = SGR.engine_commit(root, PREFIX, seal_rel, impl_files)
    if s is None or e is None:
        return None
    out = {}
    for rel in impl_files:
        blob = subprocess.run(["git", "show", "%s:%s%s" % (e, PREFIX, rel)], cwd=root, capture_output=True)
        out[rel] = hashlib.sha256(blob.stdout).hexdigest()[:16] if blob.returncode == 0 else None
    return out


def engine_fingerprint_adapter_at_history(root=REPO, seal_rel=SEAL_REL, impl_files=ENGINE_FILES):
    u"""engine の commit の木の ``adapters/xbrl`` の .py から作った束ねた指紋(``verify_document._py_digest``)。"""
    s, e = SGR.engine_commit(root, PREFIX, seal_rel, impl_files)
    if s is None or e is None:
        return None
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
        arc = subprocess.run(["git", "archive", e, PREFIX + "adapters/xbrl"], cwd=root, stdout=subprocess.PIPE, check=True)
        subprocess.run(["tar", "-x", "-C", d], input=arc.stdout, check=True)
        digest, _n = TPR.VD._py_digest(os.path.join(d, PREFIX, "adapters", "xbrl"))
    return digest


def engine_declaration_problems(numstat=None, sha16=None, fp=None, numstat_pin=ENGINE_NUMSTAT_PIN, sha16_pin=ENGINE_SHA16_PIN, fp_pin=ENGINE_FP_PIN):
    u"""engine の commit の numstat・blob の sha16・束ねた指紋が封 §2-3 の宣言(literal)と同じか。引数に履歴から作った値を渡す(試験は壊した値を渡す)。"""
    out = []
    if numstat != numstat_pin:
        out.append(u"封の commit から engine の commit までの numstat が宣言と違う: %r" % (numstat,))
    if sha16 != sha16_pin:
        out.append(u"engine の commit の blob の sha16 が宣言と違う: %r" % (sha16,))
    if fp != fp_pin:
        out.append(u"engine の commit の木の束ねた指紋が宣言と違う: %r" % (fp,))
    return out


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


def wiring_problems(tp=None):
    u"""この script が前の便の script の同じ instance を使っているか + PB・XR の差し替えが届いているか。問題の列。"""
    tp = tp or TPR
    out = list(tp.wiring_problems())
    missing = object()
    checks = (("RM", tp.PB, "RM"), ("RR", tp.PB, "RR"), ("PI", tp.PB, "PI"), ("PS", tp.PB, "PS"), ("XR", tp.PB, "XR"), ("NF", tp.RM, "NF"), ("GEN", tp.RM, "GEN"), ("RUN", tp.RM, "RUN"),
              ("TUNE", tp.RM, "TUNE"), ("R97", tp.RR, "R97"), ("D", tp.RR, "D"))
    for mine, holder, theirs in checks:
        if getattr(tp, mine, missing) is not getattr(holder, theirs, missing) or getattr(tp, mine, missing) is missing:
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
        e10 = [i for i, ln in enumerate(lines) if ln.startswith("| T-10 |")]
        self.assertEqual(1, len(e10))
        self.assertNotEqual([], seal_problems("\n".join(lines[:e10[0]] + lines[e10[0] + 1:])))                       # 10 行が 9 行
        e5 = [i for i, ln in enumerate(lines) if ln.startswith("| T-5 |")][0]
        cells = lines[e5].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:e5] + [" | ".join(cells[:2]) + " |"] + lines[e5 + 1:])))   # 外れ方の欄が無い
        self.assertNotEqual([], seal_problems("\n".join(lines[:e5] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[e5 + 1:])))   # 予測の欄が空
        k5 = [i for i, ln in enumerate(lines) if ln.startswith("- K-5:")]
        self.assertEqual(1, len(k5))
        self.assertNotEqual([], seal_problems("\n".join(lines[:k5[0]] + lines[k5[0] + 1:])))
        self.assertNotEqual([], seal_problems(self.seal.replace("measure/xbrl_tperiod_2026-11-09.py", "measure/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("`fixtures/xbrl/tperiod/inject_2026-11-09.json`", "`fixtures/xbrl/tperiod/x.json`")))
        self.assertNotEqual([], seal_problems(self.seal.replace("fixtures/xbrl/tperiod/", "fixtures/xbrl/x/")))
        self.assertNotEqual([], seal_problems(self.seal.replace("XBRL_TABLE_PERIOD_ENGINE_RESULT_2026-11-09.md", "x.md")))
        self.assertNotEqual([], seal_problems(self.seal.replace("tests/measure/test_xbrl_tperiod_result.py", "tests/measure/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("| `adapters/xbrl/vocabulary.py` |", "| `adapters/xbrl/comparators.py` |", 1)))
        self.assertNotEqual([], seal_problems(self.seal.replace("## §4", "## 四", 1)))

    def test_a_4_the_record_paths_and_engine_files_are_read_from_the_seal(self):
        self.assertEqual(list(RECORD_RELS), seal_record_rels(self.seal))
        self.assertEqual(list(ENGINE_FILES), seal_engine_files(self.seal))
        self.assertEqual([], seal_record_rels(self.seal.replace("## §5", "## 五", 1)))


class ScriptMatchesSealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_b_1_the_script_agrees_with_the_seal(self):
        self.assertEqual([], script_problems(self.seal))

    def _fake(self, **ov):
        d = dict((k, getattr(TPR, k)) for k in ("SEAL_REL", "SEAL_COMMIT", "PROFILES", "OLD", "NEW", "INJECT_A_PROFILES", "BASE_OLD", "ENGINE_FILES", "REC_REL", "DOC_REL", "SCRIPT_REL",
                                               "PB_REGRESS97_REL", "PB_INJECT_REL", "BASE_PROFILES", "NOW_PROFILES", "PAIRS", "KEYED", "PERIODS5", "PREV_SCRIPT_RELS", "TP", "TC"))
        d.update(ov)
        return types.SimpleNamespace(**d)

    def test_b_2_a_changed_script_constant_turns_it_red(self):
        self.assertEqual([], script_problems(self.seal, self._fake()))
        recs = TPR.REC_REL
        for ov in (dict(SEAL_COMMIT="0000000"), dict(SEAL_REL="docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md"), dict(PROFILES=("P30E", "P32E")), dict(NEW="P32E"), dict(OLD="P30E"),
                   dict(INJECT_A_PROFILES=("P32E", "P33E")), dict(BASE_OLD="P32E"), dict(ENGINE_FILES=TPR.ENGINE_FILES + ("adapters/xbrl/comparators.py",)), dict(ENGINE_FILES=TPR.ENGINE_FILES[:1]),
                   dict(REC_REL=dict(list(recs.items())[:2])), dict(REC_REL=type(recs)([("moves", "fixtures/xbrl/tperiod/x.json")] + list(recs.items())[1:])),
                   dict(DOC_REL="docs/x.md"), dict(SCRIPT_REL="measure/x.py"), dict(PB_REGRESS97_REL="fixtures/xbrl/rmix/regress97_2026-11-04.json"),
                   dict(PB_INJECT_REL="fixtures/xbrl/pswap/inject_idmap_2026-11-06.json"), dict(BASE_PROFILES=TPR.BASE_PROFILES[:-1]), dict(NOW_PROFILES=TPR.NOW_PROFILES[:-1]),
                   dict(PERIODS5=("CurrentYear", "Prior1Year", u"他", u"なし")), dict(PAIRS=((u"P32E 対 P30E", "P30E", "P32E"),)), dict(KEYED=("P30E", "P32E")),
                   dict(PREV_SCRIPT_RELS=TPR.PREV_SCRIPT_RELS[1:]), dict(TP=u"T")):
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

    def test_d_1b_the_pb_script_records_and_gates_are_in_the_read_only_list_and_exist(self):
        for rel in ("measure/xbrl_pbind_2026-11-06.py", "fixtures/xbrl/pbind/moves_200_2026-11-06.json", "fixtures/xbrl/pbind/regress97_2026-11-06.json", "fixtures/xbrl/pbind/inject_2026-11-06.json",
                    "tests/measure/test_xbrl_pbind_seal.py", "tests/measure/test_xbrl_pbind_result.py", "measure/xbrl_rmix_2026-11-04.py", "measure/xbrl_pswap_idmap_2026-11-06.py",
                    "measure/inject.py", "measure/lib/numbers.py", "measure/lib/sites.py"):
            self.assertIn(rel, READ_ONLY_RELS)
        self.assertEqual(len(READ_ONLY_RELS), len(set(READ_ONLY_RELS)))
        for rel in READ_ONLY_RELS:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_d_2_the_frozen_check_sees_a_changed_file_a_missing_one_and_a_file_without_the_engine_commit(self):
        self.assertNotEqual([], frozen_since_engine_problems(rels=READ_ONLY_RELS + (SCRIPT_RELS[0],)))              # engine の commit に無い file(script は engine の後)
        self.assertNotEqual([], frozen_since_engine_problems(rels=("measure/xbrl_pbind_2026-11-06.py", "measure/nonexistent_file.py")))
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
        u"""PB の便の門のように、engine の commit が触った file(T の宣言された遷移)は engine の commit の blob を基準にする。封の commit の blob とは違ってよい。"""
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        r.commit("measure/gate.py", SEAL_REL)
        r.put("measure/gate.py")
        r.put("adapters/xbrl/recipes.py")
        r.put("adapters/xbrl/vocabulary.py")
        r.commit("measure/gate.py", *ENGINE_FILES)
        self.assertEqual([], frozen_since_engine_problems(rels=("measure/gate.py",), root=r.d, base=os.path.join(r.d, "audit-core")))

    def test_d_5_the_gates_that_the_t_engine_commit_touched_are_frozen_at_that_commit(self):
        u"""T の engine の commit が宣言された遷移を足した PB の門(2 本)は、engine の commit の blob と byte が同じ(現物が engine の commit の後に変わっていない)。"""
        s, e = seal_and_engine()
        for rel in ("tests/measure/test_xbrl_pbind_seal.py", "tests/measure/test_xbrl_pbind_result.py"):
            blob = subprocess.run(["git", "show", "%s:%s%s" % (e, PREFIX, rel)], cwd=REPO, capture_output=True)
            self.assertEqual(0, blob.returncode, rel)
            with open(os.path.join(ROOT, rel), "rb") as fh:
                self.assertEqual(blob.stdout, fh.read(), rel)

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
            self.assertIn("XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md", read(rel), rel)


class EngineDeclarationTest(unittest.TestCase):
    u"""封 §2-3 が宣言した engine の遷移(recipes.py +57 / −0・vocabulary.py +5 / −0・sha16 2 値・束ねた指紋)を literal で留める。
    後の便が足す宣言された遷移の部品(``SGR.t_declared_numstat``・``t_declared_fingerprint``)の値も同じ literal でなければ赤。"""

    def test_n_1_the_engine_commit_matches_the_declared_numstat_sha16_and_fingerprint(self):
        self.assertEqual([], engine_declaration_problems(engine_numstat_at_history(), engine_sha16_at_history(), engine_fingerprint_adapter_at_history()))

    def test_n_2_the_working_tree_engine_files_still_have_the_declared_sha16(self):
        for rel in ENGINE_FILES:
            self.assertEqual(ENGINE_SHA16_PIN[rel], SGR.pb_sha16(rel), rel)

    def test_n_3_a_changed_literal_or_a_changed_value_turns_the_declaration_check_red(self):
        n, h, f = engine_numstat_at_history(), engine_sha16_at_history(), engine_fingerprint_adapter_at_history()
        bad_n = dict(n)
        bad_n["adapters/xbrl/recipes.py"] = (58, 0)
        self.assertNotEqual([], engine_declaration_problems(bad_n, h, f))
        bad_n = dict(n)
        bad_n["adapters/xbrl/vocabulary.py"] = (5, 1)
        self.assertNotEqual([], engine_declaration_problems(bad_n, h, f))
        bad_n = dict(n)
        bad_n["adapters/xbrl/comparators.py"] = (1, 0)                                       # 宣言に無い file
        self.assertNotEqual([], engine_declaration_problems(bad_n, h, f))
        self.assertNotEqual([], engine_declaration_problems(None, h, f))
        for rel in ENGINE_FILES:
            bad_h = dict(h)
            bad_h[rel] = h[rel][:-1] + (u"0" if h[rel][-1] != u"0" else u"1")                 # sha16 を 1 字変える
            self.assertNotEqual([], engine_declaration_problems(n, bad_h, f), rel)
            pin = dict(ENGINE_SHA16_PIN)
            pin[rel] = pin[rel][:-1] + (u"0" if pin[rel][-1] != u"0" else u"1")                # literal の方を 1 字変える
            self.assertNotEqual([], engine_declaration_problems(n, h, f, sha16_pin=pin), rel)
        self.assertNotEqual([], engine_declaration_problems(n, h, f[:-1] + (u"0" if f[-1] != u"0" else u"1")))
        self.assertNotEqual([], engine_declaration_problems(n, h, f, fp_pin=ENGINE_FP_PIN[:-1] + (u"0" if ENGINE_FP_PIN[-1] != u"0" else u"1")))
        self.assertNotEqual([], engine_declaration_problems(n, h, None))

    def test_n_4_the_declared_transition_parts_of_the_earlier_gate_carry_the_same_values(self):
        self.assertEqual(dict((k, tuple(int(x) for x in v)) for k, v in SGR.T_NUMSTAT.items()), ENGINE_NUMSTAT_PIN)
        self.assertEqual(SGR.T_SHA16, ENGINE_SHA16_PIN)
        self.assertEqual(SGR.T_FP, ENGINE_FP_PIN)
        self.assertEqual(SGR.T_SEAL_REL, SEAL_REL)
        self.assertTrue(SGR.t_seal_in_history())
        self.assertTrue(SGR.t_declared_fingerprint(ENGINE_FP_PIN))
        self.assertFalse(SGR.t_declared_fingerprint(ENGINE_FP_PIN[:-1] + u"0"))


class WiringTest(unittest.TestCase):
    def test_w_1_the_script_uses_the_same_instances_as_the_previous_scripts(self):
        self.assertEqual([], wiring_problems())
        self.assertIs(TPR.XR, TPR.PB.XR)
        self.assertIs(TPR.XR, TPR.RR.XR)
        self.assertIs(TPR.PS, TPR.PI.PS)
        self.assertIs(TPR.RM, TPR.PB.RM)
        self.assertIs(TPR.NF, TPR.RM.NF)
        self.assertIs(TPR.R97, TPR.XR.R97)

    def test_w_2_another_instance_or_a_missed_swap_turns_the_wiring_check_red(self):
        for name in ("RM", "RR", "PI", "PS", "XR", "NF", "GEN", "RUN", "TUNE", "R97", "D"):
            fake = types.SimpleNamespace(**dict((k, getattr(TPR, k)) for k in dir(TPR) if not k.startswith("__")))
            setattr(fake, name, types.SimpleNamespace())
            self.assertNotEqual([], wiring_problems(fake), name)
        self.assertEqual([], wiring_problems())

    def test_w_3_the_pb_swap_and_the_xr_swap_reach_the_users_and_a_missed_swap_is_reported(self):
        for name, v in TPR.PB_SWAP:
            self.assertEqual(v, getattr(PB, name), name)
        for name, v in TPR.XR_SWAP:
            self.assertEqual(v, getattr(XR, name), name)
        for name, bad in (("OLD", "P30E"), ("NEW", "P32E"), ("PROFILES", ("P30E", "P32E")), ("SEAL_REL", "docs/x.md"), ("SEAL_COMMIT", "0000000")):
            old = getattr(PB, name)
            setattr(PB, name, bad)
            try:
                self.assertTrue(any(u"PB.%s" % name in x for x in TPR.wiring_problems()), name)
            finally:
                setattr(PB, name, old)
        for name in ("PAIRS", "ENGINE_FILES", "KEYED"):
            old = getattr(XR, name)
            setattr(XR, name, tuple(old) + (("x",) if name != "PAIRS" else (("x", "P27", "P28"),)))
            try:
                self.assertTrue(any(u"XR.%s" % name in x for x in TPR.wiring_problems()), name)
            finally:
                setattr(XR, name, old)
        self.assertEqual([], TPR.wiring_problems())

    def test_w_4_the_users_read_the_swapped_names_in_their_own_globals(self):
        self.assertIs(XR.engine_commits.__globals__["ENGINE_FILES"], XR.ENGINE_FILES)
        self.assertEqual(tuple(TPR.ENGINE_FILES), tuple(XR.engine_commits.__globals__["ENGINE_FILES"]))
        self.assertEqual("eb281f1", XR.engine_commits.__globals__["SEAL_COMMIT"])
        self.assertEqual(SEAL_REL, XR.engine_commits.__globals__["SEAL_REL"])
        self.assertEqual(tuple(TPR.NOW_PROFILES), tuple(XR.doc_rows.__globals__["NOW_PROFILES"]))
        self.assertEqual(tuple(TPR.BASE_PROFILES), tuple(XR.doc_rows.__globals__["BASE_PROFILES"]))
        self.assertEqual(tuple(TPR.KEYED), tuple(XR.doc_job.__globals__["KEYED"]))
        self.assertEqual("P32E", PB.judge_book_pb.__globals__["OLD"])
        self.assertEqual("P33E", PB.judge_book_pb.__globals__["NEW"])
        self.assertEqual(("P32E", "P33E"), tuple(PB.moves_block.__globals__["PROFILES"]))
        self.assertEqual(("P32E", "P33E"), (PB.doc_moves_pb.__globals__["OLD"], PB.doc_moves_pb.__globals__["NEW"]))

    def test_w_5_the_a_pair_swap_reaches_the_inject_function_and_goes_back(self):
        self.assertEqual(("P32E", "P33E"), tuple(PB.PROFILES))
        with TPR.swap_pb(OLD=TPR.BASE_OLD, NEW=TPR.NEW, PROFILES=TPR.INJECT_A_PROFILES):
            self.assertEqual(("P30E", "P33E"), tuple(PB.inject_text_pb.__globals__["PROFILES"]))
            self.assertEqual(("P33E", "P30E"), tuple(PB.base_pair().value))
        self.assertEqual(("P32E", "P33E"), tuple(PB.inject_text_pb.__globals__["PROFILES"]))
        self.assertEqual(("P32E", "P33E"), (PB.OLD, PB.NEW))
        try:
            with TPR.swap_pb(OLD="P30E", NEW="P33E", PROFILES=("P30E", "P33E")):
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertEqual(("P32E", "P33E"), (PB.OLD, PB.NEW))
        self.assertEqual(("P32E", "P33E"), tuple(PB.PROFILES))

    def test_w_6_the_script_defines_none_of_the_previous_functions_and_uses_them(self):
        src = read(SCRIPT_RELS[0])
        self.assertEqual([], own_function_problems(src))
        self.assertEqual([], calls_problems(src))
        for m, f in REUSED_FUNCS:
            self.assertTrue(callable(getattr(getattr(TPR, m), f)), (m, f))
            self.assertFalse(hasattr(TPR, f), f)                                   # この script の名前空間に同名の関数を持たない
            self.assertNotEqual([], own_function_problems(src + u"\n\ndef %s(*a):\n    return None\n" % f), f)
            self.assertNotEqual([], own_function_problems(src + u"\n%s = None\n" % f), f)
            self.assertNotEqual([], calls_problems(src.replace(u"%s.%s" % (m, f), u"X.%s" % f)), (m, f))

    def test_w_7_the_script_loads_the_pb_script_with_importlib_and_does_not_edit_it(self):
        src = read(SCRIPT_RELS[0])
        self.assertIn(u'load_module("xbrl_pbind_2026-11-06.py"', src)
        self.assertEqual(1, src.count(u"load_module(\"xbrl_"))

    def test_w_8_the_loader_puts_back_the_names_that_were_there_before_and_keeps_its_own(self):
        u"""script の ``load_module``(PB の script を読み込む関数)は、読み込みの前に居た ``sys.modules`` の名前を元の object に戻し、読み込んだ module 自身の名前は残す。
        門の load_module と同じ形(7109c97)。戻す行を外した版は、先に居た名前を上書きして残す(= 2 通りの順で赤になる欠陥)。"""
        before = dict(sys.modules)
        probe = "tperiod_script_loader_probe"
        try:
            mod = TPR.load_module("xbrl_pbind_2026-11-06.py", probe)
            self.assertIsNot(mod.XR, PB.XR)                                                                  # 前提: 読み直しは別の object を作る(上書きの機会がある)
            self.assertEqual([], sorted(k for k, v in before.items() if sys.modules.get(k) is not v))
            self.assertIs(sys.modules.get(probe), mod)
        finally:
            sys.modules.pop(probe, None)

    def test_w_9_a_loader_without_the_restore_lines_overwrites_the_names(self):
        u"""戻す行(``finally`` の中)を外した版の loader を同じ file の字から作って走らせると、先に居た名前が上書きされる(= w_8 が赤になる)。"""
        src = read(SCRIPT_RELS[0])
        i = src.index(u"def load_module(")
        j = src.index(u"\n\n\n", i)
        fn = src[i:j]
        self.assertIn(u"finally:", fn)
        k = fn.index(u"    finally:")
        broken = fn[:k].rstrip() + u"\n    except ZeroDivisionError:\n        pass\n    return mod\n"
        self.assertNotIn(u"sys.modules[k] = v", broken)
        ns = {"importlib": importlib, "os": os, "sys": sys, "HERE": os.path.join(ROOT, "measure")}
        exec(compile(u"import importlib.util\n" + broken, "<broken_loader>", "exec"), ns)
        before = dict(sys.modules)
        probe = "tperiod_script_broken_loader_probe"
        try:
            ns["load_module"]("xbrl_pbind_2026-11-06.py", probe)
            changed = sorted(k for k, v in before.items() if sys.modules.get(k) is not v)
            self.assertNotEqual([], changed)                                                                  # 上書きされた名前が在る(門 w_8 が赤になる形)
        finally:
            for k, v in before.items():
                sys.modules[k] = v
            for k in list(sys.modules):
                if k not in before:
                    sys.modules.pop(k, None)


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
