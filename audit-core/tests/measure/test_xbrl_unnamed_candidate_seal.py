# -*- coding: utf-8 -*-
"""封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md(P27 が「証拠が無く名指さない」で止めた行に、名指さなかった fact を出力の候補の欄として添える)の門。封 §7 の 2。

**この門が縛るもの**

1. 封の字に、docID(評価用の会社は W の記録 ``fixtures/xbrl/p27/reports_2026-10-27.json`` の ``区分`` で読む。docID の形 ``S100`` + 4 字も)と claim の id の形(``N`` + 3 桁・``T`` + 3 桁)が 0 件。
   禁止語・code fence も 0(封の席は評価用を開いていない、の字面の側の証拠。git で証明できるのは順序だけ)。
2. 封 §2-3 の数(sha16 ごとの file 数 27・33・11・9、和集合 37 file の全部が ``tests/measure``、留めの型ごとの file 数、診断の門の型 12 / 6、``LATER_ENGINE_COMMITS`` 1)を、
   **実物の ``git grep``**(封の時点の commit ``020ffc0``)から数え直した値と照らす。
3. 封 §1-2 の欄の名前(``candidate``)・旗の名前(``unnamed_candidate_2026_10_29``)・``basis`` の字(``no_same_value``)・``P27C`` の作り方・「欄は 13 欄目で末尾」が、実装の後の engine の字と同じ。
   封の字から読み、engine から読んだ値と比べる(字で二重に持たない)。
4. 封の commit(``0df5222``)と承認の追記の commit(``db68a2c``)は文書だけ: ``adapters/``・``core/`` を 1 行も触っていない。封の file は封の commit が 1 回だけ足した。
5. 新しい門(この file)が、既存の門が行頭の名前を数える変数名(封 §2-3 の言い分け)を行頭に置いていない。
6. 門の変異: docID・claim id・禁止語を封の写しに足す・数を変える・欄や旗の名前を変える・engine を触った標本の numstat、で上の検査が赤になる。

評価用の AI の文・評価用の DB の応答は開かない(W の記録の ``区分`` と docID の欄を読むだけ)。この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import dataclasses
import json
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

SEAL_REL = "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md"
W_REL = "fixtures/xbrl/p27/reports_2026-10-27.json"
GREP_COMMIT = "020ffc0"          # 封 §2-3 の ``git grep -l -F <sha16> 020ffc0 -- tests`` の commit(封の時点の HEAD)
SEAL_COMMIT_PREFIX = "0df5222"   # 封を足した commit
APPROVAL_COMMIT_PREFIX = "db68a2c"   # 人間の承認の追記の commit(文書だけ)
FORBIDDEN_WORDS = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社", u"貴社の DB の誤り", u"取り戻す")
#: 既存の門が行頭の名前を数える変数名(封 §2-3 の言い分け)。新しい門はこれらを行頭に置かない。
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS", "LATER_FINGERPRINT",
                     "FINGERPRINT_", "LATER_TARGET", "LATER_FROZEN", "FROZEN_BUNDLE_AT_SEAL", "TARGET_AT_SEAL", "ENGINE_AT_SEAL", "ENGINE_AT_MEASURE", "ENGINE_DECLARED")


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=REPO, capture_output=True, text=True)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def evaluation_docids(w):
    return sorted(c["docID"] for c in w["会社"] if c["区分"] == u"評価用")


# ---------------------------------------------------------------- 1. 封の字
def check_no_names(text, eval_ids):
    for d in eval_ids:
        assert d not in text, u"**封の字に評価用の docID がある**"
    assert not re.search(r"S100[0-9A-Z]{4}", text), u"封の字に docID の形がある"
    assert not re.search(r"\b[NT]\d{3}\b", text), u"封の字に claim の id の形がある"
    for w in FORBIDDEN_WORDS:
        assert w not in text, u"封の字に禁止語がある: " + w
    assert "```" not in text, u"封の字に code fence がある"


# ---------------------------------------------------------------- 2. 留めの一覧の数え直し
def section_2_3(text):
    return text[text.index("### §2-3"):text.index("## §3")]


def parse_counts(text):
    u"""§2-3 の字: sha16 ごとの file 数・束ねた指紋の file 数・和集合の数・型ごとの file 数。"""
    sec = section_2_3(text)
    head = re.search(r"`verify_document\.py` `([0-9a-f]{16})` \*\*(\d+) file\*\*・`vocabulary\.py` `([0-9a-f]{16})` \*\*(\d+)\*\*・"
                     r"`report_customer\.py` `([0-9a-f]{16})` \*\*(\d+)\*\*・束ねた指紋 `([0-9a-f]{16})` \*\*(\d+)\*\*", sec)
    per = {"verify_document.py": (head.group(1), int(head.group(2))), "vocabulary.py": (head.group(3), int(head.group(4))),
           "report_customer.py": (head.group(5), int(head.group(6)))}
    fp = (head.group(7), int(head.group(8)))
    union = re.search(r"和集合は \*\*(\d+) file、全部 `tests/measure`\*\*", sec)
    names = re.findall(r"`(test_[a-z0-9_]+\.py)`", sec[sec.index("和集合は"):sec.index("留めの型")])
    rows = {}
    for m in re.finditer(r"(?m)^\| (`\w+`[^|]*?) \| (\d+)(?: / (\d+))? \| ", sec):
        rows[re.match(r"`(\w+)`", m.group(1)).group(1)] = (int(m.group(2)), int(m.group(3)) if m.group(3) else None)
    other = re.search(r"`ENGINE_AT_MEASURE` / `ENGINE_DECLARED`", sec)
    assert other
    return {"per": per, "fp": fp, "union_n": int(union.group(1)), "union": sorted(names), "rows": rows}


def grep_files(sha16):
    out = git("grep", "-l", "-F", sha16, GREP_COMMIT, "--", "audit-core/tests").stdout.split()
    return sorted(l.split(":", 1)[1].replace("audit-core/", "", 1) for l in out if ":" in l)


def blob_at(rel):
    return git("show", "%s:audit-core/%s" % (GREP_COMMIT, rel)).stdout


def recount(claims):
    union = set()
    for name, (sha, n) in sorted(claims["per"].items()):
        files = grep_files(sha)
        assert len(files) == n, u"%s の sha16 を持つ file の数が封の字と違う: %d != %d" % (name, len(files), n)
        union |= set(files)
    fp_files = grep_files(claims["fp"][0])
    assert len(fp_files) == claims["fp"][1], u"束ねた指紋を持つ file の数が封の字と違う"
    union |= set(fp_files)
    assert len(union) == claims["union_n"], u"和集合の数が封の字と違う: %d" % len(union)
    assert all(f.startswith("tests/measure/") for f in union), u"和集合に tests/measure の外の file がある"
    assert sorted(os.path.basename(f) for f in union) == claims["union"], u"和集合の file 名が封の字と違う"
    # 型ごとの file 数(行頭の変数名で数える。封の言い方)
    want = claims["rows"]
    counts = {}
    for t in ("ENGINE_LATER", "FROZEN_LATER", "ENGINE_TRANSITIONS", "UNTOUCHED", "PIN_DEF", "ENGINE_AT_MEASURE", "ENGINE_DECLARED", "LATER_ENGINE_COMMITS"):
        counts[t] = len([f for f in sorted(union) if re.search(r"(?m)^%s" % t, blob_at(f))])
    assert counts["ENGINE_LATER"] == want["ENGINE_LATER"][0], u"ENGINE_LATER 系の file の数が封の字と違う: %d" % counts["ENGINE_LATER"]
    assert counts["FROZEN_LATER"] == want["FROZEN_LATER"][0], u"FROZEN_LATER の file の数が封の字と違う: %d" % counts["FROZEN_LATER"]
    assert counts["ENGINE_TRANSITIONS"] == want["ENGINE_TRANSITIONS"][0], u"ENGINE_TRANSITIONS の file の数が封の字と違う: %d" % counts["ENGINE_TRANSITIONS"]
    assert counts["UNTOUCHED"] == want["UNTOUCHED"][0], u"UNTOUCHED の file の数が封の字と違う: %d" % counts["UNTOUCHED"]
    assert counts["PIN_DEF"] == want["PIN_DEF"][0], u"PIN_DEF の file の数が封の字と違う: %d" % counts["PIN_DEF"]
    assert (counts["ENGINE_AT_MEASURE"], counts["ENGINE_DECLARED"]) == want["ENGINE_AT_MEASURE"], u"診断の門の型の file の数が封の字と違う"
    assert counts["LATER_ENGINE_COMMITS"] == want["LATER_ENGINE_COMMITS"][0], u"LATER_ENGINE_COMMITS の file の数が封の字と違う"
    return sorted(union)


# ---------------------------------------------------------------- 3. 封の字と engine の字
def parse_names(text):
    u"""§1-2 の字から、欄の名前・旗の名前・basis の字・profile の名前を読む。"""
    sec = text[text.index("### §1-2"):text.index("### §1-3")]
    field = re.search(r"\*\*欄の名前\*\*: `(\w+)`。`CLAIM_FIELDS` の\*\*末尾\*\*に足す\((\d+) 欄目", sec)
    flag = re.search(r"旗 `(\w+): bool = False`", sec)
    basis = re.search(r'"basis": "(\w+)"', sec)
    keys = re.search(r"鍵の並びは pointer・value・basis の順", sec)
    prof = re.search(r'`P27C = dataclasses\.replace\(P27, name="(\w+)", (\w+)=True\)`', sec)
    assert field and flag and basis and keys and prof, u"封の字から欄・旗・basis・P27C が読めない"
    return {"field": field.group(1), "nth": int(field.group(2)), "flag": flag.group(1), "basis": basis.group(1), "profile": prof.group(1), "profile_flag": prof.group(2)}


def check_names(n):
    from adapters.xbrl import recipes as R
    from adapters.xbrl import verify_document as VD
    from adapters.xbrl import vocabulary as V
    assert VD.CLAIM_FIELDS[-1] == n["field"], u"欄の名前が封の字と違う"
    assert len(VD.CLAIM_FIELDS) == n["nth"], u"欄の数(封の字の「%d 欄目」)が違う" % n["nth"]
    fields = dict((f.name, f) for f in dataclasses.fields(V.Profile))
    assert n["flag"] in fields and fields[n["flag"]].default is False, u"旗が無いか、既定が偽でない"
    assert [f.name for f in dataclasses.fields(V.Profile)][-1] == n["flag"], u"旗が Profile の末尾でない(P27 の旗 5 つの後ろ)"
    assert R.NO_SAME_VALUE == n["basis"], u"basis の字が engine の no_same_value と違う"
    assert n["profile"] in V.PROFILES and V.PROFILES[n["profile"]] is V.P27C
    assert V.P27C == dataclasses.replace(V.P27, name=n["profile"], **{n["profile_flag"]: True}), u"P27C の作り方が封の字と違う"
    assert n["profile_flag"] == n["flag"]
    assert [p for p, prof in V.PROFILES.items() if getattr(prof, n["flag"])] == [n["profile"]], u"旗が真の profile が P27C だけでない"
    assert V.DEFAULT_PROFILE == "P27" and not getattr(V.P27, n["flag"]) and not getattr(V.P27E, n["flag"]), u"既定の P27・P27E は旗が偽のまま"


# ---------------------------------------------------------------- 4. 封の commit は文書だけ
def commit_of(prefix):
    r = git("rev-parse", prefix + "^{commit}")
    return r.stdout.strip() if r.returncode == 0 else None


def engine_numstat(a, b):
    return git("diff", "--numstat", a, b, "--", "audit-core/adapters", "audit-core/core").stdout.strip()


class SealTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(SEAL_REL)
        cls.w = json.loads(read(W_REL))

    def test_1_the_seal_names_no_docid_no_claim_id_no_forbidden_word(self):
        eval_ids = evaluation_docids(self.w)
        self.assertEqual(10, len(eval_ids))
        check_no_names(self.text, eval_ids)

    def test_2_the_pin_list_is_recounted_from_the_real_git_grep(self):
        claims = parse_counts(self.text)
        self.assertEqual({"verify_document.py": ("c3791080ab5aef2f", 27), "vocabulary.py": ("514ebb8104451c07", 33), "report_customer.py": ("6679138d350ec382", 11)}, claims["per"])
        self.assertEqual(("92326a0f4dcefd21", 9), claims["fp"])
        self.assertEqual(37, claims["union_n"])
        self.assertEqual(37, len(claims["union"]))
        self.assertEqual({"ENGINE_LATER": (16, None), "FROZEN_LATER": (1, None), "ENGINE_TRANSITIONS": (3, None), "UNTOUCHED": (6, None), "PIN_DEF": (1, None),
                          "ENGINE_AT_MEASURE": (12, 6), "LATER_ENGINE_COMMITS": (1, None)}, claims["rows"])
        union = recount(claims)
        self.assertEqual(37, len(union))

    def test_3_the_names_in_the_seal_equal_the_engine(self):
        n = parse_names(self.text)
        self.assertEqual({"field": "candidate", "nth": 13, "flag": "unnamed_candidate_2026_10_29", "basis": "no_same_value", "profile": "P27C",
                          "profile_flag": "unnamed_candidate_2026_10_29"}, n)
        check_names(n)

    def test_4_the_seal_and_the_approval_commits_touch_no_engine_file(self):
        seal = commit_of(SEAL_COMMIT_PREFIX)
        appr = commit_of(APPROVAL_COMMIT_PREFIX)
        self.assertIsNotNone(seal, u"封の commit が履歴に無い")
        self.assertIsNotNone(appr, u"承認の追記の commit が履歴に無い")
        self.assertEqual("", engine_numstat(seal + "^", seal), u"封の commit は文書だけ(engine を 1 行も触らない)")
        self.assertEqual("", engine_numstat(seal, appr), u"承認の追記の commit は文書だけ(engine を 1 行も触らない)")
        added = [s for s in git("log", "--diff-filter=A", "--format=%H", "--", "audit-core/" + SEAL_REL).stdout.split() if s]
        self.assertEqual([seal], added, u"封の file を足した commit がちょうど 1 つ(封の commit)")

    def test_5_the_new_gate_does_not_define_the_reserved_names_at_the_line_start(self):
        for line in read("tests/measure/test_xbrl_unnamed_candidate_seal.py").splitlines():
            m = re.match(r"^([A-Za-z_][A-Za-z_0-9]*)\s*[=:]", line)
            if m:
                for pre in RESERVED_PREFIXES:
                    self.assertFalse(m.group(1).startswith(pre), m.group(1))
        self.assertTrue(any(read("tests/measure/test_xbrl_unnamed_candidate_seal.py").count(p) for p in RESERVED_PREFIXES))


class GateMutationTest(unittest.TestCase):
    u"""門自身が、壊した標本で赤くなる(毎回走る)。"""

    @classmethod
    def setUpClass(cls):
        cls.text = read(SEAL_REL)
        cls.w = json.loads(read(W_REL))

    def _red(self, f, *a):
        with self.assertRaises(AssertionError):
            f(*a)

    def test_m1_a_docid_a_claim_id_or_a_forbidden_word_in_the_seal_is_red(self):
        eval_ids = evaluation_docids(self.w)
        check_no_names(self.text, eval_ids)
        for add in (eval_ids[0], u"S100ABCD", u"N012", u"T123", u"取り戻す", u"証明した", u"```"):
            self._red(check_no_names, self.text + u"\n" + add, eval_ids)

    def test_m2_changing_a_count_in_the_seal_text_is_red(self):
        claims = parse_counts(self.text)
        recount(claims)
        bad = dict(claims, per=dict(claims["per"], **{"vocabulary.py": (claims["per"]["vocabulary.py"][0], 32)}))
        self._red(recount, bad)
        self._red(recount, dict(claims, union_n=36))
        self._red(recount, dict(claims, fp=(claims["fp"][0], 8)))
        self._red(recount, dict(claims, rows=dict(claims["rows"], PIN_DEF=(2, None))))
        self._red(recount, dict(claims, rows=dict(claims["rows"], ENGINE_AT_MEASURE=(12, 5))))
        self._red(recount, dict(claims, union=claims["union"][:-1] + ["test_xbrl_x.py"]))

    def test_m3_changing_a_name_in_the_seal_text_is_red(self):
        n = parse_names(self.text)
        check_names(n)
        for key, new in (("field", "candidates"), ("nth", 12), ("flag", "unnamed_candidate_2026_10_30"), ("basis", "named"), ("profile", "P27X")):
            self._red(check_names, dict(n, **{key: new}))

    def test_m4_a_seal_text_with_another_name_does_not_parse_to_the_engine(self):
        for old, new in (("**欄の名前**: `candidate`", "**欄の名前**: `candidates`"), ("unnamed_candidate_2026_10_29: bool = False", "unnamed_candidate_2026_10_30: bool = False"),
                         ('"basis": "no_same_value"', '"basis": "named"')):
            self.assertIn(old, self.text)
            self._red(lambda t: check_names(parse_names(t)), self.text.replace(old, new, 1))

    def test_m5_an_engine_touching_commit_is_seen_by_the_numstat_check(self):
        # 封の commit の 1 つ後ろ(実装を含む commit)と封の commit の差は、engine を触る標本として numstat が空でない。
        # 実装の前の木ではこの比べ先が無いので、engine を触った commit を履歴から探す: 020ffc0 の 1 つ前の engine の commit。
        r = git("log", "--format=%H", "-n", "1", "--", "audit-core/adapters/xbrl/vocabulary.py")
        engine_commit = r.stdout.strip()
        self.assertTrue(engine_commit)
        self.assertNotEqual("", engine_numstat(engine_commit + "^", engine_commit))


if __name__ == "__main__":
    unittest.main()
