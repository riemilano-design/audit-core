# -*- coding: utf-8 -*-
"""封 docs/XBRL_NUMBER_READER_ENGINE_SEAL_2026-11-04.md(数の読み取り N ― 万・億の数のコンマを 1 つの数に読む。P29 = P28 + N・P29E = P28E + N。既定にしない)の測定の門。封 §5-4。

**この門が縛るもの**(結果の門 ``test_xbrl_numfix_result.py`` は記録・文書・採用の判定を縛る)

1. 封 §1-1 の正規表現の字が engine の ``extract._MAN_COMMA_RE_2026_11_04.pattern`` と一致する(封の字を ``_X_2026_11_04`` ごと展開して比べる。字で二重に持たない)。
2. 旗の名前・旗の位置(``numbers_2026_10_21`` の直後・``written_precision_2026_10_27`` の前)・P29 = P28 + 旗・P29E = P28E + 旗・旗が真の profile は P29 と P29E だけ・
   ``DEFAULT_PROFILE == "P27"``・旗の既定が偽・``recipes._numbers_of`` が旗で N の読みに変わる。
3. 封 §3 の予測の表が C-1〜C-13 の 13 行で、どの行も予測と外れ方の欄を持つ。§4 の K-1〜K-5 と追記 1 が在る。§5 の script 3 本と記録 4 つの path が封に在る。
4. engine の変更は封の commit から engine の commit までで §2-1 の 3 file だけ・削除 0。
5. 前の便の script・記録(この便が importlib で読むだけのもの)は封の commit の blob と byte が同じ。
6. 順序: 封 48e7078 ⊏ engine を触った commit ⊏ script 3 本・門 2 本(記録・結果の文書の順序は結果の門が見る)。engine の commit の hash を字で持たず、履歴から探す。未 commit は赤(skip にしない)。
7. 新しい門が、既存の門が行頭の名前を数える変数名を行頭に置いていない。
8. 門の変異: 封の字・profile の定義・表の行・numstat・順序を 1 つずつ壊した標本で上の検査が赤になる。

この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import dataclasses
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

SEAL_REL = "docs/XBRL_NUMBER_READER_ENGINE_SEAL_2026-11-04.md"
SEAL_COMMIT_SHORT = "48e7078"
FLAG = "numbers_man_comma_2026_11_04"
ENGINE_FILES = ("adapters/xbrl/extract.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/recipes.py")
SCRIPT_RELS = ("measure/xbrl_numfix_2026-11-04.py", "measure/xbrl_numfix_regress97_2026-11-04.py", "measure/xbrl_numfix_shapes_2026-11-04.py")
GATE_RELS = ("tests/measure/test_xbrl_numfix_seal.py", "tests/measure/test_xbrl_numfix_result.py")
RECORD_RELS = ("fixtures/xbrl/numfix/ai200_2026-11-04.json", "fixtures/xbrl/numfix/inject_2026-11-04.json",
               "fixtures/xbrl/numfix/regress97_2026-11-04.json", "fixtures/xbrl/numfix/shapes_2026-11-04.json")
#: この便が読むだけの前の便の script・記録(封の commit の blob と byte が同じでなければならない)
READ_ONLY_RELS = ("measure/xbrl_aiforms_gen_2026-11-03.py", "measure/xbrl_aiforms_run_2026-11-03.py", "measure/xbrl_p27_tune_2026-10-27.py",
                  "measure/xbrl_p28_regress97_2026-11-02.py", "measure/xbrl_p27_regress97_2026-10-27.py", "measure/xbrl_p28_ai_prose_2026-11-02.py",
                  "fixtures/xbrl/aiforms/gen_2026-11-03.json", "fixtures/xbrl/aiforms/f5_gen_2026-11-03.json",
                  "fixtures/xbrl/aiforms/claims_2026-11-03.json", "fixtures/xbrl/aiforms/f5_claims_2026-11-03.json",
                  "fixtures/xbrl/aiforms/inject_2026-11-03.json", "fixtures/xbrl/aiforms/f5_inject_2026-11-03.json",
                  "fixtures/xbrl/p28e/regress97_2026-11-03.json", "measure/SEED.json")
#: 既存の門が行頭の名前を数える変数名(新しい門はこれらを行頭に置かない。封 §2-3)
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS", "LATER_FINGERPRINT",
                     "FINGERPRINT_", "LATER_TARGET", "LATER_FROZEN", "FROZEN_BUNDLE_AT_SEAL", "TARGET_AT_SEAL", "ENGINE_AT_SEAL", "ENGINE_AT_MEASURE", "ENGINE_DECLARED")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
PRED_IDS = tuple("C-%d" % i for i in range(1, 14))
K_IDS = tuple("K-%d" % i for i in range(1, 6))


def load_module(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_numfix_seal")       # 順序の部品(order_problems・Repo・added_commits・git_in)。門としては走らせない


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def read_bytes(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return fh.read()


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=REPO, capture_output=True)


# ---------------------------------------------------------------- 1. 封 §1-1 の正規表現
def seal_regex(seal):
    u"""封 §1-1 のコード片を実行して (X, 正規表現の字) を得る。``re.compile`` は字をそのまま返す偽物に替える(字面の展開だけを使う)。"""
    sec = seal[seal.index("### §1-1"):seal.index("### §1-2")]
    m = re.search(r"```\n(.*?)\n```", sec, re.S)
    assert m, u"封 §1-1 にコード片が無い"
    ns = {"re": types.SimpleNamespace(compile=lambda s: s)}
    from adapters.xbrl import extract as E
    ns["_SIGN_2026_10_21"] = E._SIGN_2026_10_21
    exec(compile(m.group(1), "seal §1-1", "exec"), ns)
    return ns["_X_2026_11_04"], ns["_MAN_COMMA_RE_2026_11_04"]


def regex_problems(seal):
    from adapters.xbrl import extract as E
    out = []
    try:
        x, pat = seal_regex(seal)
    except Exception as e:                                   # noqa: BLE001  壊れた封は読めない = 赤
        return [u"封 §1-1 のコード片が読めない(%s)" % type(e).__name__]
    if x != E._X_2026_11_04:
        out.append(u"_X_2026_11_04 が封の字と違う")
    if pat != E._MAN_COMMA_RE_2026_11_04.pattern:
        out.append(u"_MAN_COMMA_RE_2026_11_04 の字が封を展開した字と違う")
    sign = re.search(r"`_SIGN_2026_10_21` = `([^`]*)`", seal)
    if not sign or sign.group(1) != E._SIGN_2026_10_21:
        out.append(u"封が頭に付けるとした _SIGN_2026_10_21 の字が engine の字と違う")
    return out


# ---------------------------------------------------------------- 2. 旗・profile
def profile_problems(V=None, fields=None, numbers_of=None):
    u"""旗・profile の定義。V = vocabulary(試験が壊した写しを渡す)、fields = Profile の欄の名前の列、numbers_of = recipes._numbers_of。"""
    from adapters.xbrl import recipes as R
    from adapters.xbrl import vocabulary as VOC
    V = V or VOC
    numbers_of = numbers_of or R._numbers_of
    out = []
    names = list(fields) if fields is not None else [f.name for f in dataclasses.fields(V.Profile)]
    if FLAG not in names:
        return [u"Profile に旗 %s が無い" % FLAG]
    i = names.index(FLAG)
    # 2026-11-04: RB(封 docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md §0-2 の 3)が旗 rounding_mixed_2026_11_04 をこの旗の直後に足した: この旗 → RB の旗 → written_precision_2026_10_27(RB の旗が在るときだけ)
    after = names[i + 2] if names[i + 1:i + 2] == ["rounding_mixed_2026_11_04"] else names[i + 1]
    if names[i - 1] != "numbers_2026_10_21" or after != "written_precision_2026_10_27":
        out.append(u"旗の位置が numbers_2026_10_21 の直後・written_precision_2026_10_27 の前でない")
    if dataclasses.fields(V.Profile)[names.index(FLAG)].default is not False:
        out.append(u"旗の既定が偽でない")
    if V.DEFAULT_PROFILE != "P27":
        out.append(u"DEFAULT_PROFILE が P27 でない")
    for new, base in (("P29", "P28"), ("P29E", "P28E")):
        p, b = V.PROFILES.get(new), V.PROFILES.get(base)
        if p is None or b is None:
            out.append(u"%s か %s が PROFILES に無い" % (new, base))
            continue
        if p != dataclasses.replace(b, name=new, **{FLAG: True}):
            out.append(u"%s が %s + 旗 でない" % (new, base))
        if getattr(b, FLAG) is not False:
            out.append(u"%s の旗が偽でない(既存の profile を変えた)" % base)
    on = sorted(k for k, p in V.PROFILES.items() if getattr(p, FLAG, False))
    # 2026-11-04: RB の旗が Profile に在るときは P30E(= P29E + RB)も N の旗を引き継いで真
    if on != ["P29", "P29E"] + (["P30E"] if "rounding_mixed_2026_11_04" in names else []):
        out.append(u"旗が真の profile が P29・P29E だけでない: %s" % on)
    s = u"売上高は1,234万円でした。"
    got_off = [(a, b) for (a, b, _v, _u, _p) in numbers_of(V.PROFILES["P28"], s)]
    got_on = [(a, b, v) for (a, b, v, _u, _p) in numbers_of(V.PROFILES["P29"], s)]
    if got_off != [] or got_on != [(s.index(u"1"), s.index(u"円") + 1, 12340000.0)]:
        out.append(u"recipes._numbers_of が旗で N の読みに替わらない(旗が偽: %r・真: %r)" % (got_off, got_on))
    return out


# ---------------------------------------------------------------- 3. 封の表
def table_ids(seal, start, end, pat):
    sec = seal[seal.index(start):seal.index(end)]
    return [m.group(1) for m in (re.match(pat, line) for line in sec.splitlines()) if m]


def seal_problems(seal):
    out = []
    ids = table_ids(seal, "## §3", "## §4", r"^\| (C-\d+) \| (.*) \|$")
    if ids != list(PRED_IDS):
        out.append(u"封 §3 の表が C-1〜C-13 の 13 行でない: %s" % ids)
    sec = seal[seal.index("## §3"):seal.index("## §4")]
    for line in sec.splitlines():
        m = re.match(r"^\| (C-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            if len(cells) < 3 or any(not c.strip() for c in cells[:3]):
                out.append(u"封 §3 の %s の欄(欄・予測・外れ方)が埋まっていない" % m.group(1))
    sec4 = seal[seal.index("## §4"):seal.index("## §5")]
    got_k = re.findall(r"^- \*\*(K-\d)", sec4, re.M)
    if got_k != list(K_IDS):
        out.append(u"封 §4 の K-1〜K-5 が揃っていない: %s" % got_k)
    if not re.search(r"^## 追記 1", seal, re.M):
        out.append(u"封に追記 1 が無い")
    for rel in SCRIPT_RELS + RECORD_RELS:
        if rel not in seal:
            out.append(u"封に path が無い: %s" % rel)
    sec21 = seal[seal.index("### §2-1"):seal.index("### §2-2")]
    for rel in ENGINE_FILES:
        if u"`%s`" % rel not in sec21:
            out.append(u"封 §2-1 に engine の file が無い: %s" % rel)
    return out


# ---------------------------------------------------------------- 4. engine の変更
def numstat_problems(lines):
    u"""``git diff --numstat <封> <engine の commit> -- adapters core`` の行 → 問題の列。"""
    out = []
    paths = []
    for ln in lines:
        ins, dele, path = ln.split("\t")
        paths.append(path)
        if dele != "0":
            out.append(u"削除が 0 でない: %s" % path)
    if sorted(paths) != sorted(PREFIX + p for p in ENGINE_FILES):
        out.append(u"engine の変更が §2-1 の 3 file だけでない: %s" % sorted(paths))
    return out


def engine_commit(root, prefix, seal_rel, impl_files):
    u"""封の commit と engine の commit(封の後に各 file を最初に触った commit のうち、子孫にあたる最後のもの)。履歴から探す(hash を字で持たない)。"""
    s = PR.added_commits(root, prefix + seal_rel)
    if len(s) != 1:
        return None, None
    firsts = []
    for rel in impl_files:
        lst = [c for c in PR.git_in(root, "log", "--format=%H", s[0] + "..HEAD", "--", prefix + rel)[1].split() if c]
        if not lst:
            return s[0], None
        firsts.append(lst[-1])
    e = firsts[0]
    for c in firsts[1:]:
        if PR.is_anc(root, e, c):
            e = c
    return s[0], e


def real_numstat_problems(root=REPO):
    seal, e = engine_commit(root, PREFIX, SEAL_REL, ENGINE_FILES)
    if seal is None or e is None:
        return [u"封か engine の commit が履歴に無い"]
    lines = [x for x in PR.git_in(root, "diff", "--numstat", seal, e, "--", PREFIX + "adapters", PREFIX + "core")[1].splitlines() if x]
    return numstat_problems(lines)


# ---------------------------------------------------------------- 5. 前の便の file は byte 不変
def frozen_problems(rels=READ_ONLY_RELS, root=REPO, base=ROOT, seal_rel=SEAL_REL):
    u"""root = git の木、base = 作業木の audit-core の folder。封の commit の blob と作業木の byte を比べる。"""
    seal = PR.added_commits(root, PREFIX + seal_rel)
    if len(seal) != 1:
        return [u"封の commit が 1 つに決まらない"]
    out = []
    for rel in rels:
        blob = subprocess.run(["git", "show", "%s:%s%s" % (seal[0], PREFIX, rel)], cwd=root, capture_output=True)
        if blob.returncode != 0:
            out.append(u"封の commit に無い: %s" % rel)
            continue
        with open(os.path.join(base, rel), "rb") as fh:
            if blob.stdout != fh.read():
                out.append(u"封の commit の blob と byte が違う: %s" % rel)
    return out


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


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_regex_equals_the_seal(self):
        self.assertEqual([], regex_problems(self.seal))

    def test_a_2_the_seal_tables_and_paths_are_complete(self):
        self.assertEqual([], seal_problems(self.seal))

    def test_a_3_a_changed_seal_character_turns_the_regex_check_red(self):
        start = self.seal.index("### §1-1")
        for old, new in ((u"兆)?", u"兆?"), (u"|\\d+)", u"|\\d*)"), (u"億)?", u"億)"), (u"))?円", u")?円"), (u"万)?", u"万)"), (u"{1,3}", u"{1,4}")):
            i = self.seal.index(old, start)
            mutated = self.seal[:i] + new + self.seal[i + len(old):]
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], regex_problems(mutated), old)

    def test_a_4_a_broken_code_block_is_red_not_an_exception(self):
        mutated = self.seal.replace(u"_X_2026_11_04 = r", u"_X_2026_11_04 = undefined_name; _Y = r", 1)
        self.assertNotEqual([], regex_problems(mutated))
        self.assertNotEqual([], regex_problems(self.seal.replace(u"```\n_X_2026_11_04", u"``\n_X_2026_11_04", 1)))


    def test_a_5_a_broken_prediction_table_or_missing_section_turns_it_red(self):
        lines = self.seal.split("\n")
        c13 = [i for i, ln in enumerate(lines) if ln.startswith("| C-13 |")]
        self.assertEqual(1, len(c13))
        self.assertNotEqual([], seal_problems("\n".join(lines[:c13[0]] + lines[c13[0] + 1:])))                       # 13 行が 12 行
        c5 = [i for i, ln in enumerate(lines) if ln.startswith("| C-5 |")][0]
        cells = lines[c5].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:c5] + [" | ".join(cells[:2]) + " |"] + lines[c5 + 1:])))   # 外れ方の欄が無い
        self.assertNotEqual([], seal_problems("\n".join(lines[:c5] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[c5 + 1:])))   # 予測の欄が空
        k5 = [i for i, ln in enumerate(lines) if ln.startswith("- **K-5")]
        self.assertEqual(1, len(k5))
        self.assertNotEqual([], seal_problems("\n".join(lines[:k5[0]] + lines[k5[0] + 1:])))
        self.assertNotEqual([], seal_problems(self.seal.replace("## 追記 1", "## 追記 一", 1)))
        self.assertNotEqual([], seal_problems(self.seal.replace("measure/xbrl_numfix_shapes_2026-11-04.py", "measure/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("`adapters/xbrl/recipes.py` | `_numbers_of`", "`adapters/xbrl/x.py` | `_numbers_of`", 1)))


class ProfileTest(unittest.TestCase):
    def test_b_1_flag_and_profiles(self):
        self.assertEqual([], profile_problems())

    def test_b_2_a_broken_profile_turns_it_red(self):
        from adapters.xbrl import recipes as R
        from adapters.xbrl import vocabulary as VOC

        def fake(**profiles):
            v = types.SimpleNamespace(Profile=VOC.Profile, DEFAULT_PROFILE=VOC.DEFAULT_PROFILE, PROFILES=dict(VOC.PROFILES))
            v.PROFILES.update(profiles)
            return v
        self.assertEqual([], profile_problems(fake()))
        # P29 から別の旗を 1 つ外す・P29E の名前を変える・P29 の旗を偽にする・旗が真の profile を 1 つ増やす
        self.assertNotEqual([], profile_problems(fake(P29=dataclasses.replace(VOC.P29, numbers_2026_10_21=False))))
        self.assertNotEqual([], profile_problems(fake(P29E=dataclasses.replace(VOC.P29E, name="P29X"))))
        self.assertNotEqual([], profile_problems(fake(P29=dataclasses.replace(VOC.P29, **{FLAG: False}))))
        self.assertNotEqual([], profile_problems(fake(P28=dataclasses.replace(VOC.P28, **{FLAG: True}))))
        self.assertNotEqual([], profile_problems(fake(P27=dataclasses.replace(VOC.P27, **{FLAG: True}))))
        v = fake()
        v.DEFAULT_PROFILE = "P29E"
        self.assertNotEqual([], profile_problems(v))
        # 旗の位置が違う・旗の欄が無い
        names = [f.name for f in dataclasses.fields(VOC.Profile)]
        moved = [n for n in names if n != FLAG]
        moved.insert(moved.index("written_precision_2026_10_27") + 1, FLAG)
        self.assertNotEqual([], profile_problems(fields=moved))
        self.assertNotEqual([], profile_problems(fields=[n for n in names if n != FLAG]))
        # recipes._numbers_of が旗を見ない
        self.assertNotEqual([], profile_problems(numbers_of=lambda p, s: R._numbers_of(VOC.P28, s)))


class EngineAndFrozenTest(unittest.TestCase):
    def test_c_1_engine_changes_are_the_three_files_and_no_deletions(self):
        self.assertEqual([], real_numstat_problems())

    def test_c_2_numstat_mutations_turn_it_red(self):
        good = ["35\t0\t%sadapters/xbrl/extract.py" % PREFIX, "7\t0\t%sadapters/xbrl/vocabulary.py" % PREFIX, "2\t0\t%sadapters/xbrl/recipes.py" % PREFIX]
        self.assertEqual([], numstat_problems(good))
        self.assertNotEqual([], numstat_problems(good[:2]))
        self.assertNotEqual([], numstat_problems(good + ["1\t0\t%sadapters/xbrl/prose.py" % PREFIX]))
        self.assertNotEqual([], numstat_problems(good + ["1\t0\t%score/py/audit_core/x.py" % PREFIX]))
        self.assertNotEqual([], numstat_problems(["35\t1\t%sadapters/xbrl/extract.py" % PREFIX] + good[1:]))

    def test_d_1_previous_scripts_and_records_are_byte_identical_to_the_seal_commit(self):
        self.assertEqual([], frozen_problems())

    def test_d_2_the_frozen_check_sees_a_changed_file_and_a_missing_one(self):
        self.assertNotEqual([], frozen_problems(rels=READ_ONLY_RELS + ("measure/xbrl_numfix_2026-11-04.py",)))     # 封の commit に無い file
        self.assertNotEqual([], frozen_problems(rels=("tests/measure/test_xbrl_numfix_seal.py",)))

    def test_d_3_the_frozen_check_goes_red_when_a_tracked_file_changes_after_the_seal(self):
        r = PR.Repo()
        r.put("measure/prev.py")
        r.put(SEAL_REL)
        r.commit("measure/prev.py", SEAL_REL)
        base = os.path.join(r.d, "audit-core")
        self.assertEqual([], frozen_problems(rels=("measure/prev.py",), root=r.d, base=base))
        with open(os.path.join(base, "measure/prev.py"), "a", encoding="utf-8") as fh:
            fh.write("x = 1\n")
        self.assertEqual([u"封の commit の blob と byte が違う: measure/prev.py"], frozen_problems(rels=("measure/prev.py",), root=r.d, base=base))
        r.put("measure/later.py")
        r.commit("measure/later.py")
        self.assertEqual(["封の commit に無い: measure/later.py"], frozen_problems(rels=("measure/later.py",), root=r.d, base=base))

    def test_e_1_gate_files_do_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems(rels=tuple(r for r in GATE_RELS if os.path.exists(os.path.join(ROOT, r)))))

    def test_e_2_the_reserved_name_check_sees_a_planted_name(self):
        with tempfile.TemporaryDirectory() as d:
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
            t = read(rel)
            self.assertIn("XBRL_NUMBER_READER_ENGINE_SEAL_2026-11-04.md", t, rel)


class OrderTest(unittest.TestCase):
    def test_o_1_the_real_history_has_the_seal_before_the_engine_before_the_scripts(self):
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
        seal, e = engine_commit(r.d, PREFIX, SEALF, IMPLS)
        self.assertTrue(seal.startswith(s))
        self.assertTrue(e and e != seal)
        self.assertEqual(e, PR.git_in(r.d, "rev-parse", "HEAD~1")[1])


if __name__ == "__main__":
    unittest.main()
