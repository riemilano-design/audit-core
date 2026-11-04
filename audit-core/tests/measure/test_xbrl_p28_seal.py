# -*- coding: utf-8 -*-
"""封 docs/XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02.md(「その他」の主語の結び直し O を engine に入れる。P28 = P27 + O。既定にしない)の門。封 §7 の 1。

**この門が縛るもの**

1. 封 §1-1 の定数 3 つ(``OTHER_SUBJECT_TRAIL_2026_11_02``・``OTHER_SUBJECT_RE_2026_11_02``・``OTHER_SUBJECT_HOPS_2026_11_02``)の字が、engine の字と
   ``measure/xbrl_other_rule_2026-11-02.py``(measure 側の規則の字)の字と同じ。封の字から読み、engine から読んだ値と比べる(字で二重に持たない)。
2. P28 の作り方(``dataclasses.replace(P27, name="P28", other_subject_2026_11_02=True)``)・旗が真の profile が P28 だけ・旗の位置(P27 の旗 5 つの後ろ・
   ``unnamed_candidate_2026_10_29`` の前 = Profile の末尾の手前)・``DEFAULT_PROFILE == "P27"``・旗の既定が偽。
3. 封 §2-3 の留めの一覧(sha16 ごとの file 数 36・33・30・21・19・17・16・15、adapter の指紋 11 file、束ねた sha 4 file)を、実物の ``git grep``
   (封が数えた commit ``c4b8221``)から数え直した値と照らす。
4. 封の commit(``c6cbfae``)は文書だけ: ``adapters/``・``core/`` を 1 行も触っていない。封の file は封の commit が 1 回だけ足した。
5. 新しい門(この file と結果の門)が、既存の門が行頭の名前を数える変数名を行頭に置いていない。
6. 門の変異: 封の写しの定数を変える・数を変える・旗の位置を変える・engine を触った標本の numstat、で上の検査が赤になる。

この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import ast
import dataclasses
import importlib.util
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

SEAL_REL = "docs/XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02.md"
MEASURE_RULE_REL = "measure/xbrl_other_rule_2026-11-02.py"
GREP_COMMIT = "c4b8221"          # 封 §2-3 の ``git grep -l -F <sha16> c4b8221 -- tests`` の commit
SEAL_COMMIT_PREFIX = "c6cbfae"   # 封を足した commit
P28E_SEAL_COMMIT_PREFIX = "7bfad77"   # 2026-11-03 追記: P28E の封(docs/XBRL_P28E_SEAL_2026-11-03.md)を足した commit。旗が真の profile の遷移(下の check_profile)
N_SEAL_COMMIT_PREFIX = "48e7078"   # 2026-11-04 追記: 数の読み取り N の封(docs/XBRL_NUMBER_READER_ENGINE_SEAL_2026-11-04.md)を足した commit。旗が真の profile の遷移(下の check_profile)
RB_SEAL_COMMIT_PREFIX = "de23edc"   # 2026-11-04 追記: 丸め方の根拠が混ざる桁は両方の帯で照らす RB の封(docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md)を足した commit。旗が真の profile の遷移(下の check_profile)
#: 既存の門が行頭の名前を数える変数名(封 §2-3 の言い分け)。新しい門はこれらを行頭に置かない。
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS", "LATER_FINGERPRINT",
                     "FINGERPRINT_", "LATER_TARGET", "LATER_FROZEN", "FROZEN_BUNDLE_AT_SEAL", "TARGET_AT_SEAL", "ENGINE_AT_SEAL", "ENGINE_AT_MEASURE", "ENGINE_DECLARED")
NEW_GATE_FILES = ("tests/measure/test_xbrl_p28_seal.py", "tests/measure/test_xbrl_p28_result.py", "tests/adapters/xbrl/test_recipes_p28.py")


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=REPO, capture_output=True, text=True)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. 封 §1-1 の定数
def parse_constants(text):
    u"""封 §1-1 の字から定数 3 つを読む(Python の字面を ``ast.literal_eval`` で値にする)。"""
    sec = text[text.index("### §1-1"):text.index("### §1-2")]
    trail = re.search(r'`OTHER_SUBJECT_TRAIL_2026_11_02 = u":" \+ u":" \+ (u"[^"]*")`', sec)
    rx = re.search(r'`OTHER_SUBJECT_RE_2026_11_02 = re\.compile\((u"[^`]*")\)`', sec)
    hops = re.search(r"`OTHER_SUBJECT_HOPS_2026_11_02 = (\d+)`", sec)
    assert trail and rx and hops, u"封の字から定数 3 つが読めない"
    return {"trail": ":" + ":" + ast.literal_eval(trail.group(1)), "pattern": ast.literal_eval(rx.group(1)), "hops": int(hops.group(1))}


def measure_constants():
    spec = importlib.util.spec_from_file_location("p28_measure_other_rule", os.path.join(ROOT, MEASURE_RULE_REL))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    hops = re.search(r"hops >= (\d+)", read(MEASURE_RULE_REL))
    assert hops, u"measure の字から hops の上限が読めない"
    return {"trail": mod.TRAIL, "pattern": mod.OTHER_RE.pattern, "hops": int(hops.group(1))}


def engine_constants():
    from adapters.xbrl import recipes as R
    return {"trail": R.OTHER_SUBJECT_TRAIL_2026_11_02, "pattern": R.OTHER_SUBJECT_RE_2026_11_02.pattern, "hops": R.OTHER_SUBJECT_HOPS_2026_11_02}


def check_constants(seal, eng, meas):
    assert seal == eng, u"封の定数が engine の字と違う: %r != %r" % (seal, eng)
    assert seal == meas, u"封の定数が measure の字と違う: %r != %r" % (seal, meas)
    # コロン・括弧はどれも ASCII(封の字)。pattern の字の集合の中のコロン 2 つと括弧 4 つ・trail のコロン 2 つ
    assert seal["trail"][:2] == "::" and all(ord(c) < 128 for c in seal["trail"][:2]), u"trail のコロンが ASCII でない"
    inner = re.search(r"\[\^(.*?)\]", seal["pattern"]).group(1)
    assert [ord(c) for c in inner if c in ":()\uff1a\uff08\uff09"] == [58, 58, 40, 41, 40, 41], u"字の集合のコロン 2 つと括弧 4 つが全部 ASCII でない"
    assert seal["trail"].endswith(" 　"), u"trail の末尾が半角空白 + 全角空白 U+3000 でない"


# ---------------------------------------------------------------- 2. P28 の作り方
def check_profile():
    from adapters.xbrl import vocabulary as V
    flag = "other_subject_2026_11_02"
    fields = [f.name for f in dataclasses.fields(V.Profile)]
    by = dict((f.name, f) for f in dataclasses.fields(V.Profile))
    assert flag in by and by[flag].default is False, u"旗が無いか、既定が偽でない"
    assert V.P28 == dataclasses.replace(V.P27, name="P28", **{flag: True}), u"P28 の作り方が封の字と違う"
    assert V.PROFILES["P28"] is V.P28
    # 2026-11-03 の遷移: 封 7bfad77(docs/XBRL_P28E_SEAL_2026-11-03.md)が履歴に在るとき、旗が真の profile は P28 と P28E(= P27E + O)の 2 つ。履歴に無ければ P28 だけ(封 c6cbfae §1-3 の字)。
    with_p28e = commit_of(P28E_SEAL_COMMIT_PREFIX) is not None
    # 2026-11-04 の遷移: 数の読み取り N の封 48e7078(docs/XBRL_NUMBER_READER_ENGINE_SEAL_2026-11-04.md)が履歴に在るとき、P29(= P28 + N)と P29E(= P28E + N)も O の旗を引き継いで真(新しい旗は N の 1 つだけ)。
    with_n = commit_of(N_SEAL_COMMIT_PREFIX) is not None
    # 2026-11-04 の遷移: RB の封 de23edc(docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md)が履歴に在るとき、P30E(= P29E + RB)も O の旗を引き継いで真(新しい旗は RB の 1 つだけ)。
    with_rb = commit_of(RB_SEAL_COMMIT_PREFIX) is not None
    assert [n for n, p in V.PROFILES.items() if getattr(p, flag)] == (["P28", "P28E"] + (["P29", "P29E"] + (["P30E"] if with_rb else []) if with_n else []) if with_p28e else ["P28"]), u"旗が真の profile が封の字(P28 だけ。P28E の封が履歴に在れば P28 と P28E。N の封が履歴に在れば P29 と P29E も。RB の封が履歴に在れば P30E も)と違う"
    if with_p28e:
        assert V.P28E == dataclasses.replace(V.P27E, name="P28E", **{flag: True}), u"P28E の作り方が封 7bfad77 の字と違う"
        assert V.PROFILES["P28E"] is V.P28E
    p27_flags = [n for n in fields if n.endswith("_2026_10_27")]
    assert len(p27_flags) == 5
    assert fields.index(flag) == fields.index(p27_flags[-1]) + 1, u"旗が P27 の旗 5 つの直後でない"
    assert fields.index(flag) + 1 == fields.index("unnamed_candidate_2026_10_29"), u"旗が unnamed_candidate_2026_10_29 の前でない"
    assert fields[-1] == "unnamed_candidate_2026_10_29", u"unnamed_candidate_2026_10_29 が Profile の末尾でない(P27C の封の門が縛る)"
    assert V.DEFAULT_PROFILE == "P27", u"既定が P27 でない"
    for n in ("P27", "P27E", "P27C"):
        assert not getattr(V.PROFILES[n], flag), n


# ---------------------------------------------------------------- 3. 留めの一覧の数え直し
def parse_pin_counts(text):
    sec = text[text.index("### §2-3"):text.index("## §3")]
    per = dict((a, (b, int(n))) for a, b, n in re.findall(r"`(\w+\.py)` `([0-9a-f]{16})`\((\d+)(?:。[^)]*)?\)", sec))
    fp = re.search(r"adapter の指紋 `([0-9a-f]{16})…` (\d+) file", sec)
    bundle = re.search(r"束ねた sha `([0-9a-f]{16})…`\((\d+) 本\)を字で持つ (\d+) file\(([^)]*)\)", sec)
    assert per and fp and bundle, u"封の字から留めの一覧が読めない"
    names = re.findall(r"`(test_[a-z0-9_]+\.py)`", bundle.group(4))
    return {"per": per, "fp": (fp.group(1), int(fp.group(2))), "bundle": (bundle.group(1), int(bundle.group(2)), int(bundle.group(3)), sorted(names))}


def grep_files(sha):
    out = git("grep", "-l", "-F", sha, GREP_COMMIT, "--", "audit-core/tests").stdout.split()
    return sorted(l.split(":", 1)[1].replace("audit-core/", "", 1) for l in out if ":" in l)


def recount(claims):
    for name, (sha, n) in sorted(claims["per"].items()):
        files = grep_files(sha)
        assert len(files) == n, u"%s の sha16 を持つ file の数が封の字と違う: %d != %d" % (name, len(files), n)
        assert all(f.startswith("tests/measure/") for f in files), u"%s の sha16 を持つ file に tests/measure の外がある" % name
    sha, n = claims["fp"]
    assert len(grep_files(sha)) == n, u"adapter の指紋を持つ file の数が封の字と違う"
    sha, files_n, held_n, names = claims["bundle"]
    files = grep_files(sha)
    assert files_n == 37
    assert len(files) == held_n, u"束ねた sha を字で持つ file の数が封の字と違う"
    assert sorted(os.path.basename(f) for f in files) == names, u"束ねた sha を字で持つ file の名前が封の字と違う"
    return True


# ---------------------------------------------------------------- 4. 封の commit は文書だけ
def commit_of(prefix):
    r = git("rev-parse", prefix + "^{commit}")
    return r.stdout.strip() if r.returncode == 0 else None


def engine_numstat(a, b):
    return git("diff", "--numstat", a, b, "--", "audit-core/adapters", "audit-core/core").stdout.strip()


# ---------------------------------------------------------------- 5. 行頭の名前
def reserved_heads(text):
    bad = []
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z_0-9]*)\s*[=:]", line)
        if m and any(m.group(1).startswith(p) for p in RESERVED_PREFIXES):
            bad.append(m.group(1))
    return bad


class SealTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(SEAL_REL)

    def test_1_the_constants_in_the_seal_equal_the_engine_and_the_measure_script(self):
        seal = parse_constants(self.text)
        self.assertEqual({"trail": ":" + ":" + "、はがをでに " + "　", "pattern": "その他(の[^、。::()()\\s]{0,8})?$", "hops": 5}, seal)
        check_constants(seal, engine_constants(), measure_constants())

    def test_2_p28_is_p27_plus_the_flag_and_only_p28_has_it(self):
        check_profile()

    def test_3_the_pin_list_is_recounted_from_the_real_git_grep(self):
        claims = parse_pin_counts(self.text)
        self.assertEqual({"vocabulary.py": ("7fbcfbf0e472f366", 36), "recipes.py": ("52d645e713c53c1c", 33), "verify_document.py": ("6c76c8ade6c7b1c8", 30),
                          "comparators.py": ("d8706338325e725b", 21), "extract.py": ("3cf55966f12919f0", 19), "resolve.py": ("a41043763c1d4073", 17),
                          "registry_setup.py": ("d6f25750bcd73c0a", 16), "report_customer.py": ("bdbaa00a419219fe", 15)}, claims["per"])
        self.assertEqual(("dc7e35fbfb0f56ca", 11), claims["fp"])
        self.assertEqual(("864b1f96292f1615", 37, 4, ["test_xbrl_customer_report_fix_seal.py", "test_xbrl_customer_report_seal.py", "test_xbrl_default_p26_seal.py",
                                                      "test_xbrl_p26_seal.py"]), claims["bundle"])
        self.assertTrue(recount(claims))

    def test_4_the_seal_commit_touches_no_engine_file_and_added_the_seal_once(self):
        seal = commit_of(SEAL_COMMIT_PREFIX)
        self.assertIsNotNone(seal, u"封の commit が履歴に無い")
        self.assertEqual("", engine_numstat(seal + "^", seal), u"封の commit は文書だけ(engine を 1 行も触らない)")
        added = [s for s in git("log", "--diff-filter=A", "--format=%H", "--", "audit-core/" + SEAL_REL).stdout.split() if s]
        self.assertEqual([seal], added, u"封の file を足した commit がちょうど 1 つ(封の commit)")

    def test_5_the_new_gates_do_not_define_the_reserved_names_at_the_line_start(self):
        for rel in NEW_GATE_FILES:
            path = os.path.join(REPO, "audit-core", rel)
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    self.assertEqual([], reserved_heads(fh.read()), rel)
        self.assertIn("RESERVED_PREFIXES", read("tests/measure/test_xbrl_p28_seal.py"))


class GateMutationTest(unittest.TestCase):
    u"""門自身が、壊した標本で赤くなる(毎回走る)。"""

    @classmethod
    def setUpClass(cls):
        cls.text = read(SEAL_REL)

    def _red(self, f, *a):
        with self.assertRaises(AssertionError):
            f(*a)

    def test_m1_a_changed_constant_in_the_seal_text_is_red(self):
        eng, meas = engine_constants(), measure_constants()
        check_constants(parse_constants(self.text), eng, meas)
        for old, new in (("{0,8})?$", "{0,9})?$"), ("、はがをでに ", "はがをでに "), ("OTHER_SUBJECT_HOPS_2026_11_02 = 5", "OTHER_SUBJECT_HOPS_2026_11_02 = 4")):
            self.assertIn(old, self.text)
            self._red(lambda t: check_constants(parse_constants(t), eng, meas), self.text.replace(old, new, 1))

    def test_m2_a_changed_engine_or_measure_constant_is_red(self):
        seal = parse_constants(self.text)
        eng, meas = engine_constants(), measure_constants()
        self._red(check_constants, seal, dict(eng, hops=4), meas)
        self._red(check_constants, seal, dict(eng, pattern=eng["pattern"].replace("{0,8}", "{0,9}")), meas)
        self._red(check_constants, seal, eng, dict(meas, trail=meas["trail"][:2] + meas["trail"][3:]))

    def test_m3_a_changed_count_in_the_seal_text_is_red(self):
        claims = parse_pin_counts(self.text)
        recount(claims)
        self._red(recount, dict(claims, per=dict(claims["per"], **{"recipes.py": (claims["per"]["recipes.py"][0], 32)})))
        self._red(recount, dict(claims, fp=(claims["fp"][0], 10)))
        self._red(recount, dict(claims, bundle=claims["bundle"][:2] + (3,) + claims["bundle"][3:]))
        self._red(recount, dict(claims, bundle=claims["bundle"][:3] + (claims["bundle"][3][:-1] + ["test_xbrl_x.py"],)))

    def test_m4_a_flag_in_the_wrong_place_or_a_wrong_profile_is_red(self):
        from adapters.xbrl import vocabulary as V
        fields = [f.name for f in dataclasses.fields(V.Profile)]
        flag = "other_subject_2026_11_02"
        # 旗が末尾にある並びなら、unnamed_candidate_2026_10_29 の直前という検査は赤になる(並びの検査は fields.index の式)。
        moved = [n for n in fields if n != flag] + [flag]
        self.assertNotEqual(moved.index(flag) + 1, moved.index("unnamed_candidate_2026_10_29"))
        self.assertNotEqual(V.P28, dataclasses.replace(V.P27, name="P28"))
        self.assertNotEqual(V.P28, dataclasses.replace(V.P27, name="P28", other_subject_2026_11_02=True, written_precision_2026_10_27=False))

    def test_m5_an_engine_touching_commit_is_seen_by_the_numstat_check(self):
        r = git("log", "--format=%H", "-n", "1", "--", "audit-core/adapters/xbrl/vocabulary.py")
        engine_commit = r.stdout.strip()
        self.assertTrue(engine_commit)
        self.assertNotEqual("", engine_numstat(engine_commit + "^", engine_commit))

    def test_m6_a_reserved_head_is_seen(self):
        self.assertEqual([], reserved_heads("P28_PIN = 1\n"))
        self.assertEqual(["ENGINE_LATER_X"], reserved_heads("ENGINE_LATER_X = {}\n"))
        self.assertEqual(["UNTOUCHED"], reserved_heads("UNTOUCHED: dict = {}\n"))


if __name__ == "__main__":
    unittest.main()
