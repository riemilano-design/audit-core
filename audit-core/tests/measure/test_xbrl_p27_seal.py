# -*- coding: utf-8 -*-
"""封 docs/XBRL_P27_SEAL_2026-10-27.md(P27 段 2 ― 外部の数の文のための engine の直し)の門。封 §9-2。

**この門が縛るもの**

1. 封の字に、評価用の docID(W の記録 ``fixtures/xbrl/p27/reports_2026-10-27.json`` の ``区分`` が評価用の会社)が 0 件。docID の形の字(``S100`` + 4 字)も 0 件。
   claim の id の形(``N`` + 3 桁・``T`` + 3 桁)が 0 件。= 封を書いた席は評価用を開いていない、の字面の側の証拠(git で証明できるのは順序だけ。封 §8)。
2. 封 §1 の定数(ρ・窓・単位の一覧・正規表現 3 つ)・旗 5 つの名前と P27・P27E の作り方が、engine の字と同じ。封の字から読み、engine から読んだ値と比べる。
3. 封 §2-3 の留めの一覧: 封の字の数(sha16 ごとの file 数・和集合 26 file・型 5 つの file 数・``tests/adapters/xbrl`` の 13 file)を、**実物の ``git grep``**(封の時点
   の commit ``29e6d0a``)から数え直した値と照らす。26 file の全部が、いま P27 の封の遷移を宣言している(封の path を字で持つ)。
4. engine の変更は挿入だけ: 封の commit から、5 file の削除の行が 0・``core/``・comparators・verify_document・run・report は 0 行・``DEFAULT_PROFILE = "P26"`` の行はそのまま。
   5 file の sha16 は、封の時点の値か、宣言された遷移(P27 の段 2 の後)の値。
5. 新しい門(この file・``test_xbrl_p27_engine_result.py``・``tests/adapters/xbrl/test_recipes_p27.py``)が、既存の門が行頭の名前を数える変数名(封 §2-3)を行頭に置いていない。
6. 門の変異: 評価用の docID を封の写しに足す・claim の id を足す・定数を変える・単位を 1 つ消す・数を変える・留めの宣言を外す・削除の行を足す、で上の検査が赤になる。

評価用の AI の文・評価用の DB の応答は開かない(W の記録の ``区分`` と docID の欄を読むだけ)。この file は評価用の docID の字を持たない
(引きの門 test_xbrl_fresh_seal が追跡 file の docID を数える)。
"""
import ast
import dataclasses
import hashlib
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

SEAL_REL = "docs/XBRL_P27_SEAL_2026-10-27.md"
SEAL = os.path.join(ROOT, SEAL_REL)
W_REL = "fixtures/xbrl/p27/reports_2026-10-27.json"
BASELINE_COMMIT = "29e6d0a"       # 封 §2-3 の ``git grep -l -F <sha16> 29e6d0a -- tests`` の commit
ENGINE5 = ("vocabulary.py", "recipes.py", "extract.py", "registry_setup.py", "report_customer.py")
UNCHANGED_ENGINE = ("comparators.py", "verify_document.py", "run.py", "report.py")
#: 封の時点の sha16 の字(§2-3)。封の字から読んだ値と同じであることを test_3 が見る(字で留めない)。
#: 宣言された遷移(P27 の段 2 の後)の sha16。実装の便が測った値。封が履歴に在り、値がこれのときだけ受け入れる。
P27_AFTER16 = {"vocabulary.py": "85896a67913ce1e7", "recipes.py": "52d645e713c53c1c", "extract.py": "3cf55966f12919f0",
               "registry_setup.py": "d6f25750bcd73c0a", "report_customer.py": "6679138d350ec382"}
#: 2026-10-28(既定を P26 -> P27 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md §1-1・§4 (j) が宣言した遷移。vocabulary.py は DEFAULT_PROFILE の 1 行と注記(+5 行・-1 行)、
#: verify_document.py は docstring の 1 行(+1 行・-1 行)だけが動いた。上の P27_AFTER16(P27 の段 2 の後の値)は測った時点の値として残す。受け入れるのは、その封が履歴に在り、
#: 値が下の値のときだけ(他の file は遷移を持たない)。
DEFAULT_P27_SEAL_REL = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"
DEFAULT_P27_AFTER16 = {"vocabulary.py": "514ebb8104451c07", "verify_document.py": "c3791080ab5aef2f"}
DEFAULT_P27_DELETIONS = {"adapters/xbrl/vocabulary.py": 1, "adapters/xbrl/verify_document.py": 1}
#: 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。vocabulary.py に旗 1 つ・P27C・PROFILES の登録(+5 行)、
#: verify_document.py に Claim の欄 candidate(+11 行・-1 行)、report_customer.py に candidate_ja と「要確認」の理由の欄の描き直し 1 行(+22 行・-1 行)。上の DEFAULT_P27_AFTER16
#: (既定を P27 に切り替える 段 2 の後の値)は測った時点の値として残す。受け入れるのは、その封が履歴に在り、3 file の sha16 が下の値のときだけ(封の commit 43fe0e3 からの削除は累計: 1・2・1)。
CAND_SEAL_REL = "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md"
CAND_AFTER16 = {"vocabulary.py": "7fbcfbf0e472f366", "verify_document.py": "6c76c8ade6c7b1c8", "report_customer.py": "bdbaa00a419219fe"}
CAND_DELETIONS = {"adapters/xbrl/vocabulary.py": 1, "adapters/xbrl/verify_document.py": 2, "adapters/xbrl/report_customer.py": 1}
#: 既存の門が行頭の名前を数える変数名(封 §2-3 の言い分け)。新しい門はこれらを行頭に置かない。
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS", "LATER_FINGERPRINT",
                     "FINGERPRINT_", "LATER_TARGET", "LATER_FROZEN", "FROZEN_BUNDLE_AT_SEAL", "TARGET_AT_SEAL", "ENGINE_AT_SEAL")
NEW_GATE_FILES = ("tests/measure/test_xbrl_p27_seal.py", "tests/measure/test_xbrl_p27_engine_result.py", "tests/adapters/xbrl/test_recipes_p27.py")
PIN_TYPES = ("ENGINE_LATER", "FROZEN_LATER", "ENGINE_TRANSITIONS", "UNTOUCHED", "PIN_DEF")


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=REPO, capture_output=True, text=True)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha16_of(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def seal_commit():
    u"""封の commit(``--diff-filter=A`` の行がちょうど 1 つ)。0 か 2 以上なら None。"""
    got = [s for s in git("log", "--diff-filter=A", "--format=%H", "--", "audit-core/" + SEAL_REL).stdout.split() if s]
    return got[0] if len(got) == 1 else None


def cand_declared():
    u"""候補の欄を足す遷移(封 CAND_SEAL_REL §2-3)が宣言されているか。封が履歴に在り、作業木の 3 file の sha16 が宣言の値のときだけ True。"""
    added = git("log", "--diff-filter=A", "--format=%H", "--", "audit-core/" + CAND_SEAL_REL).stdout.split()
    if not added:
        return False
    return dict((n, sha16_of("adapters/xbrl/" + n)) for n in CAND_AFTER16) == CAND_AFTER16


def default_p27_declared():
    u"""既定を P27 に切り替える 段 2 の遷移が宣言されているか。封が履歴に在り、作業木の 2 file の sha16 が宣言の値のときだけ True。
    2026-10-30: 候補の欄を足す遷移(cand_declared)の後も既定は P27 のままなので、その宣言の後も True(vocabulary.py・verify_document.py は後の値になる)。"""
    if cand_declared():
        return True
    added = git("log", "--diff-filter=A", "--format=%H", "--", "audit-core/" + DEFAULT_P27_SEAL_REL).stdout.split()
    if not added:
        return False
    got = dict((n, sha16_of("adapters/xbrl/" + n)) for n in DEFAULT_P27_AFTER16)
    return got == DEFAULT_P27_AFTER16        # 宣言の値でなければ False(下流の門が封の時点の値か P27 の段 2 の後の値かを見て、どちらでもなければ赤にする)


def evaluation_docids(w):
    return sorted(c["docID"] for c in w["会社"] if c["区分"] == u"評価用")


# ---------------------------------------------------------------- 1. 封の字
def check_no_evaluation_names(text, eval_ids):
    for d in eval_ids:
        assert d not in text, u"**封の字に評価用の docID がある**"
    assert not re.search(r"S100[0-9A-Z]{4}", text), u"封の字に docID の形がある"
    assert not re.search(r"\b[NT]\d{3}\b", text), u"封の字に claim の id の形がある"


# ---------------------------------------------------------------- 2. 定数
def parse_constants(text):
    u"""封 §1 の字から、定数・正規表現・単位の一覧・旗・profile の作り方を読む。"""
    out = {}
    out["rho"] = float(re.search(r"`LAST_BRANCH_REL_RHO = ([0-9.]+)`", text).group(1))
    out["window"] = int(re.search(r"`PER_SHARE_WINDOW = (\d+)`", text).group(1))
    out["per_share_re"] = re.search(r'PER_SHARE_RE = re\.compile\(r"([^"]+)"\)', text).group(1)
    out["a_re"] = re.search(r"正規表現 `(\(\\d\[\\d,\]\*\)[^`]*)`", text).group(1)
    out["c3_re"] = re.search(r"最後の\*\*「`(\(\\d\{4\}\)[^`]*)`」", text).group(1)
    m = re.search(r"`unit` が `(\(\"人\"[^)]*\))` のどれか", text)
    out["units"] = ast.literal_eval(m.group(1))
    m = re.search(r'`s\[b:b \+ 3\]` が `"当たり"` か `"あたり"`', text)
    assert m
    out["after"] = ("当たり", "あたり")
    out["flags"] = re.findall(r"`(\w+_2026_10_27)`", re.search(r"`vocabulary\.Profile` に旗 5 つ[^\n]*", text).group(0))
    m = re.search(r'`P27 = dataclasses\.replace\(P26, name="P27", ([^`]*)\)`', text)
    out["p27"] = dict(re.findall(r"(\w+)=(True)", m.group(1)))
    m = re.search(r'`P27E = dataclasses\.replace\(P27, name="P27E", ([^`]*)\)`', text)
    out["p27e"] = dict(re.findall(r"(\w+)=(True)", m.group(1)))
    out["default"] = re.search(r'`DEFAULT_PROFILE = "(P\d+)"`', text).group(1)
    return out


def check_constants(c):
    from adapters.xbrl import extract as E
    from adapters.xbrl import recipes as R
    from adapters.xbrl import vocabulary as V
    assert c["rho"] == R.LAST_BRANCH_REL_RHO, u"ρ が封の字と違う"
    assert c["window"] == R.PER_SHARE_WINDOW, u"窓が封の字と違う"
    assert c["per_share_re"] == R.PER_SHARE_RE.pattern, u"1 株当たりの正規表現が封の字と違う"
    assert c["a_re"] == E._LAST_DIGITS_RE_2026_10_27.pattern, u"A の正規表現が封の字と違う"
    assert c["c3_re"] == R._FUTURE_PERIOD_RE.pattern, u"C3 の正規表現が封の字と違う"
    assert tuple(c["units"]) == tuple(R.PER_UNIT_COUNTER_UNITS), u"C2 の単位の一覧が封の字と違う"
    assert tuple(c["after"]) == tuple(R.PER_UNIT_COUNTER_AFTER), u"C2 の後ろの字が封の字と違う"
    fields = [f.name for f in dataclasses.fields(V.Profile)]
    assert c["flags"] == [n for n in fields if n.endswith("_2026_10_27")], u"旗 5 つの名前か順が封の字と違う"
    assert len(c["flags"]) == 5
    for n in c["flags"]:
        assert dataclasses.fields(V.Profile)[fields.index(n)].default is False, u"旗の既定が偽でない: " + n
    want27 = dict((k, True) for k in c["p27"])
    got27 = dict((n, getattr(V.P27, n)) for n in fields if n != "name" and getattr(V.P27, n) != getattr(V.P26, n))
    assert got27 == want27, u"P27 の作り方が封の字と違う"
    want27e = dict((k, True) for k in c["p27e"])
    got27e = dict((n, getattr(V.P27E, n)) for n in fields if n != "name" and getattr(V.P27E, n) != getattr(V.P27, n))
    assert got27e == want27e, u"P27E の作り方が封の字と違う"
    assert V.PROFILES["P27"] is V.P27 and V.PROFILES["P27E"] is V.P27E
    assert c["default"] == "P26", u"封の字の既定が P26 でない"
    # 2026-10-28: 既定を P26 -> P27 に切り替える 段 2 の遷移が宣言されている間は P27(封の字は封の commit 時点の既定 P26 のまま)
    assert V.DEFAULT_PROFILE == (u"P27" if default_p27_declared() else u"P26"), u"既定が P26 でも、宣言された遷移の P27 でもない"
    assert V.P27.name == "P27" and V.P27E.name == "P27E"


# ---------------------------------------------------------------- 3. 留めの一覧
def parse_pin_claims(text):
    u"""§2-3 の字: sha16 ごとの file 数・束ねた指紋の file 数・和集合の file 名・型 5 つの file 数・tests/adapters/xbrl の file 数と名前。"""
    sec = text[text.index("### §2-3"):text.index("## §3")]
    per = dict((a, (b, int(n))) for a, b, n in re.findall(r"`(\w+\.py)` `([0-9a-f]{16})`\((\d+)(?: file)?\)", sec))
    fp = re.search(r"`adapter_xbrl_py_sha256` `([0-9a-f]{16})…`\((\d+)\)", sec)
    union = re.search(r"和集合は `tests/measure` の (\d+) file:\n\n(.*?)\n\n", sec, re.S)
    names = re.findall(r"`(test_[a-z0-9_]+\.py)`", union.group(2))
    m = re.search(r"留めの型は 5 つ: (.*?)。", sec)
    types = dict((k, int(n)) for k, n in re.findall(r"`(\w+)`(?: 系)?\((\d+)", m.group(1)))
    adapters = re.search(r"`P26` の字を持つのは (\d+) file", sec)
    return {"per": per, "fp": (fp.group(1), int(fp.group(2))), "union_n": int(union.group(1)), "union": sorted(names), "types": types,
            "adapters_n": int(adapters.group(1))}


def git_grep_files(commit, needle, pathspec, fixed=True):
    args = ["grep", "-l"] + (["-F"] if fixed else ["-E"]) + [needle, commit, "--", pathspec]
    return sorted(l.split(":", 1)[1].replace("audit-core/", "", 1) for l in git(*args).stdout.split() if ":" in l)


def check_pin_recount(claims, text_of_blob=None):
    union = set()
    for name, (sha, n) in sorted(claims["per"].items()):
        files = git_grep_files(BASELINE_COMMIT, sha, "audit-core/tests")
        assert len(files) == n, u"%s の sha16 を持つ file の数が封の字と違う: %d != %d" % (name, len(files), n)
        union |= set(f for f in files if f.startswith("tests/measure/"))
        blob = git("show", "%s:audit-core/adapters/xbrl/%s" % (BASELINE_COMMIT, name)).stdout.encode("utf-8")
        assert hashlib.sha256(blob).hexdigest()[:16] == sha, u"封の sha16 が封の時点の file の sha16 と違う: " + name
    fp_sha, fp_n = claims["fp"]
    fp_files = git_grep_files(BASELINE_COMMIT, fp_sha, "audit-core/tests")
    assert len(fp_files) == fp_n, u"束ねた指紋を持つ file の数が封の字と違う"
    union |= set(f for f in fp_files if f.startswith("tests/measure/"))
    assert len(union) == claims["union_n"], u"和集合の数が封の字と違う: %d" % len(union)
    assert sorted(os.path.basename(f) for f in union) == claims["union"], u"和集合の file 名が封の字と違う"
    # 型 5 つ(封の言い方: その名前の字が file に在る file の数。コメントの中を含む)
    for t in PIN_TYPES:
        n = 0
        for f in sorted(union):
            blob = git("show", "%s:audit-core/%s" % (BASELINE_COMMIT, f)).stdout
            if re.search(r"\b%s\b" % t, blob):
                n += 1
        assert n == claims["types"][t], u"留めの型 %s の file の数が封の字と違う: %d != %d" % (t, n, claims["types"][t])
    assert len(git_grep_files(BASELINE_COMMIT, "P26", "audit-core/tests/adapters/xbrl")) == claims["adapters_n"], u"P26 の字を持つ tests/adapters/xbrl の file の数が封の字と違う"
    return sorted(union)


def check_declared_in_all(union, read_fn, seal_name="XBRL_P27_SEAL_2026-10-27"):
    for f in union:
        assert seal_name in read_fn(f), u"**留めの一覧の file が P27 の封の遷移を宣言していない: %s**" % f


# ---------------------------------------------------------------- 4. engine は挿入だけ
def parse_numstat(text):
    rows = {}
    for line in text.splitlines():
        a, d, p = line.split("\t")
        rows[p] = (int(a) if a.isdigit() else None, int(d) if d.isdigit() else None)
    return rows


def check_insertion_only(numstat_text, allowed_deletions=None):
    u"""allowed_deletions: 2026-10-28 の遷移({path: 削除の行数の上限})。None なら従来どおり削除は 0。"""
    rows = parse_numstat(numstat_text)
    allowed = allowed_deletions or {}
    for p, (a, d) in sorted(rows.items()):
        rel = p.replace("audit-core/", "", 1)
        assert d <= allowed.get(rel, 0), u"**既存の行が書き換えられている(削除の行が 0 でない): %s**" % p
        if rel.startswith("core/") or rel.startswith("adapters/xbrl/"):
            if rel.startswith("adapters/xbrl/"):
                name = os.path.basename(rel)
                assert name in ENGINE5 or rel in allowed, u"**封の範囲の外の engine の file が動いている: %s**" % p
            else:
                raise AssertionError(u"**core/ が動いている: %s**" % p)
        elif rel.startswith("adapters/"):
            raise AssertionError(u"**adapters/ の封の範囲の外が動いている: %s**" % p)


class SealTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(SEAL_REL)
        cls.w = json.loads(read(W_REL))

    def test_1_the_seal_names_no_evaluation_company_and_no_claim_id(self):
        eval_ids = evaluation_docids(self.w)
        self.assertEqual(10, len(eval_ids))
        check_no_evaluation_names(self.text, eval_ids)

    def test_2_the_constants_in_the_seal_equal_the_engine(self):
        c = parse_constants(self.text)
        self.assertEqual(0.15, c["rho"])
        self.assertEqual(20, c["window"])
        self.assertEqual(9, len(c["units"]))
        check_constants(c)

    def test_3_the_pin_list_is_recounted_from_the_real_git_grep(self):
        claims = parse_pin_claims(self.text)
        self.assertEqual(set(ENGINE5), set(claims["per"]))
        self.assertEqual({"vocabulary.py": 25, "recipes.py": 22, "extract.py": 8, "registry_setup.py": 14, "report_customer.py": 9},
                         dict((k, v[1]) for k, v in claims["per"].items()))
        self.assertEqual(6, claims["fp"][1])
        self.assertEqual(26, claims["union_n"])
        self.assertEqual({"ENGINE_LATER": 20, "FROZEN_LATER": 13, "ENGINE_TRANSITIONS": 4, "UNTOUCHED": 7, "PIN_DEF": 2}, claims["types"])
        self.assertEqual(13, claims["adapters_n"])
        union = check_pin_recount(claims)
        self.assertEqual(26, len(union))

    def test_4_all_26_files_declare_the_p27_transition(self):
        union = check_pin_recount(parse_pin_claims(self.text))
        check_declared_in_all(union, read)

    def test_5_the_new_sha16_values_are_in_the_files_that_pin_them(self):
        u"""26 file のうち、engine の file の sha16 を字で持つ file は、宣言された遷移の値(いまの engine の sha16)を字で持つ。持っていない file は、その file が留めていない engine の file。"""
        claims = parse_pin_claims(self.text)
        union = check_pin_recount(claims)
        for name in ENGINE5:
            holders = [f for f in union if claims["per"][name][0] in read(f)]
            self.assertTrue(holders, name)                                                  # 封の時点の値を字で持つ file(測った時点の値は残す)
            self.assertTrue(any(P27_AFTER16[name] in read(f) for f in union), name)         # いまの値(宣言された遷移の値)を字で持つ file が少なくとも 1 つ
            want = DEFAULT_P27_AFTER16[name] if (name == "vocabulary.py" and default_p27_declared()) else P27_AFTER16[name]
            if cand_declared() and name in CAND_AFTER16:
                want = CAND_AFTER16[name]          # 2026-10-30: 候補の欄を足す遷移の後の値(上の値は測った時点の値として残す)
            self.assertEqual(sha16_of("adapters/xbrl/" + name), want, name)


class EngineDiffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s2 = seal_commit()

    def test_6_the_seal_commit_is_one_and_the_default_is_untouched(self):
        self.assertIsNotNone(self.s2, u"封の commit が履歴に 1 つだけ在る")
        v = read("adapters/xbrl/vocabulary.py")
        # 2026-10-28: 既定を P26 -> P27 に切り替える 段 2 の遷移が宣言されている間は P27(封の commit 時点は P26)
        self.assertEqual(1, len(re.findall(r'(?m)^DEFAULT_PROFILE = "%s"$' % (u"P27" if default_p27_declared() else u"P26"), v)))
        self.assertEqual(1, len(re.findall(r'(?m)^PROFILES\["P27E"\] = P27E$', v)))

    def test_7_only_insertions_in_the_five_files(self):
        out = git("diff", "--numstat", self.s2, "--", "audit-core/adapters", "audit-core/core").stdout
        rows = parse_numstat(out)
        self.assertTrue(rows)
        declared = default_p27_declared()
        cand = cand_declared()
        check_insertion_only(out, CAND_DELETIONS if cand else (DEFAULT_P27_DELETIONS if declared else None))
        for name in ENGINE5:
            self.assertIn("audit-core/adapters/xbrl/" + name, rows, name)
        # 封 §2-1 の挿入の行数の見込み(vocabulary 10〜20・extract 10〜20・recipes 90〜140・registry 1〜4・report 1〜4)のうち、見込みの内に収まらない file は無い(recipes は上限が 140 の見込み)
        # 2026-10-28: 既定を P26 -> P27 に切り替える 段 2 の遷移(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md §1-1)が宣言されていれば、削除は vocabulary.py の 1 行(DEFAULT_PROFILE)と
        # verify_document.py の 1 行(docstring)だけで、vocabulary.py の挿入は注記の分(≤ 8)だけ増える。宣言が無ければ従来どおり削除 0・挿入 10〜20。
        # 2026-10-30(候補の欄を足す。封 CAND_SEAL_REL §2-3): vocabulary.py の挿入はさらに +5(旗 1 つ・P27C・PROFILES の登録)、report_customer.py は +22(candidate_ja と理由の欄の描き直し)、
        # 削除は累計 vocabulary.py 1・verify_document.py 2・report_customer.py 1(CLAIM_FIELDS の 1 行・理由の欄の 1 行が加わる)。
        extra = (13 if cand else 8) if declared else 0
        self.assertEqual(sum(CAND_DELETIONS.values()) if cand else (sum(DEFAULT_P27_DELETIONS.values()) if declared else 0), sum(d for _a, d in rows.values()))
        self.assertGreaterEqual(rows["audit-core/adapters/xbrl/vocabulary.py"][0], 10)
        self.assertLessEqual(rows["audit-core/adapters/xbrl/vocabulary.py"][0], 20 + extra)
        self.assertGreaterEqual(rows["audit-core/adapters/xbrl/extract.py"][0], 10)
        self.assertLessEqual(rows["audit-core/adapters/xbrl/extract.py"][0], 20)
        self.assertGreaterEqual(rows["audit-core/adapters/xbrl/recipes.py"][0], 90)
        self.assertLessEqual(rows["audit-core/adapters/xbrl/recipes.py"][0], 140)
        self.assertGreaterEqual(rows["audit-core/adapters/xbrl/registry_setup.py"][0], 1)
        self.assertLessEqual(rows["audit-core/adapters/xbrl/registry_setup.py"][0], 4)
        self.assertGreaterEqual(rows["audit-core/adapters/xbrl/report_customer.py"][0], 1)
        self.assertLessEqual(rows["audit-core/adapters/xbrl/report_customer.py"][0], 4 + 22 if cand else 4)

    def test_8_the_untouched_engine_files_and_core_are_byte_equal_to_the_seal_commit(self):
        for name in UNCHANGED_ENGINE:
            got = git("diff", self.s2, "--numstat", "--", "audit-core/adapters/xbrl/" + name).stdout.strip()
            if name == "verify_document.py" and cand_declared():
                # 2026-10-30: docstring の 1 行(+1 行・-1 行)に続けて、Claim の欄 candidate(+11 行・-1 行)。累計 12・2。他の 3 file は 0 行のまま
                self.assertEqual("12\t2\taudit-core/adapters/xbrl/verify_document.py", got, name)
                continue
            if name == "verify_document.py" and default_p27_declared():
                # 2026-10-28: docstring の 1 行(+1 行・-1 行)だけ。他の 3 file は 0 行のまま
                self.assertEqual("1\t1\taudit-core/adapters/xbrl/verify_document.py", got, name)
                continue
            self.assertEqual("", got, name)
        self.assertEqual("", git("diff", self.s2, "--numstat", "--", "audit-core/core").stdout.strip())
        self.assertEqual("", git("status", "--porcelain", "--", "audit-core/core").stdout.strip())

    def test_9_the_five_sha16_are_the_seal_time_values_or_the_declared_transition(self):
        for name in ENGINE5:
            at_seal = hashlib.sha256(git("show", "%s:audit-core/adapters/xbrl/%s" % (self.s2, name)).stdout.encode("utf-8")).hexdigest()[:16]
            got = sha16_of("adapters/xbrl/" + name)
            if got != at_seal:
                want = P27_AFTER16[name]
                if default_p27_declared() and name == "vocabulary.py":
                    want = DEFAULT_P27_AFTER16[name]          # 2026-10-28: 既定を P27 に切り替える 段 2 の遷移の値(P27_AFTER16 は P27 の段 2 の後の値で、測った時点の値として残す)
                if cand_declared() and name in CAND_AFTER16:
                    want = CAND_AFTER16[name]                 # 2026-10-30: 候補の欄を足す遷移の後の値
                self.assertEqual(want, got, u"**%s が封の時点の値でも、宣言された遷移の値でもない**" % name)

    def test_10_the_s2_commit_did_not_touch_the_engine(self):
        out = git("diff", "--stat", self.s2 + "^", self.s2, "--", "audit-core/adapters", "audit-core/core").stdout.strip()
        self.assertEqual("", out, u"封の commit は文書だけ(engine を 1 行も触らない)")


class NamesTest(unittest.TestCase):
    def test_11_new_gates_do_not_define_the_reserved_names_at_the_line_start(self):
        for rel in NEW_GATE_FILES:
            for line in read(rel).splitlines():
                m = re.match(r"^([A-Za-z_][A-Za-z_0-9]*)\s*[=:]", line)
                if m:
                    for pre in RESERVED_PREFIXES:
                        self.assertFalse(m.group(1).startswith(pre) or m.group(1) == pre, (rel, m.group(1)))
        # 門が自分の定義を見ている字: 予約の名前そのものは上の RESERVED_PREFIXES の中の字にだけ在る(行頭には無い)
        self.assertTrue(any(read("tests/measure/test_xbrl_p27_seal.py").count(p) for p in RESERVED_PREFIXES))


class GateMutationTest(unittest.TestCase):
    u"""門自身が、壊した標本で赤くなる(毎回走る。評価用の docID の字は W の記録から読む)。"""

    @classmethod
    def setUpClass(cls):
        cls.text = read(SEAL_REL)
        cls.w = json.loads(read(W_REL))

    def _red(self, f, *a):
        with self.assertRaises(AssertionError):
            f(*a)

    def test_m1_an_evaluation_docid_or_a_claim_id_in_the_seal_is_red(self):
        eval_ids = evaluation_docids(self.w)
        check_no_evaluation_names(self.text, eval_ids)
        self._red(check_no_evaluation_names, self.text + "\n" + eval_ids[0], eval_ids)
        self._red(check_no_evaluation_names, self.text + "\nN012", eval_ids)
        self._red(check_no_evaluation_names, self.text + "\nT123", eval_ids)
        self._red(check_no_evaluation_names, self.text + "\nS100ABCD", eval_ids)

    def test_m2_changing_a_constant_in_the_seal_text_is_red(self):
        check_constants(parse_constants(self.text))
        for old, new in (("`LAST_BRANCH_REL_RHO = 0.15`", "`LAST_BRANCH_REL_RHO = 0.20`"), ("`PER_SHARE_WINDOW = 20`", "`PER_SHARE_WINDOW = 21`"),
                         ('PER_SHARE_RE = re.compile(r"株当たり|EPS|BPS")', 'PER_SHARE_RE = re.compile(r"株当たり|EPS")'),
                         ('"店舗", "社", "件")` のどれか', '"店舗", "社")` のどれか'),
                         ('P27 = dataclasses.replace(P26, name="P27", written_precision_2026_10_27=True,', 'P27 = dataclasses.replace(P26, name="P27",')):
            self.assertEqual(1, self.text.count(old), old)
            self._red(lambda t: check_constants(parse_constants(t)), self.text.replace(old, new))

    def test_m3_changing_a_count_in_the_seal_text_is_red(self):
        claims = parse_pin_claims(self.text)
        check_pin_recount(claims)
        bad = dict(claims)
        bad["per"] = dict(claims["per"])
        bad["per"]["vocabulary.py"] = (claims["per"]["vocabulary.py"][0], 24)
        self._red(check_pin_recount, bad)
        bad = dict(claims, union_n=25)
        self._red(check_pin_recount, bad)
        bad = dict(claims, types=dict(claims["types"], PIN_DEF=3))
        self._red(check_pin_recount, bad)
        bad = dict(claims, adapters_n=12)
        self._red(check_pin_recount, bad)
        bad = dict(claims, fp=(claims["fp"][0], 5))
        self._red(check_pin_recount, bad)

    def test_m4_a_file_that_does_not_declare_the_transition_is_red(self):
        union = check_pin_recount(parse_pin_claims(self.text))
        check_declared_in_all(union, read)
        self._red(check_declared_in_all, union, lambda f: read(f).replace("XBRL_P27_SEAL_2026-10-27", "XBRL_P27_SEAL_x") if f == union[3] else read(f))

    def test_m5_a_deleted_line_or_an_outside_file_is_red(self):
        s2 = seal_commit()
        out = git("diff", "--numstat", s2, "--", "audit-core/adapters", "audit-core/core").stdout
        allowed = CAND_DELETIONS if cand_declared() else (DEFAULT_P27_DELETIONS if default_p27_declared() else None)
        check_insertion_only(out, allowed)
        self._red(check_insertion_only, out + "1\t1\taudit-core/adapters/xbrl/recipes.py\n", allowed)
        self._red(check_insertion_only, out + "3\t0\taudit-core/adapters/xbrl/comparators.py\n", allowed)
        self._red(check_insertion_only, out + "3\t0\taudit-core/core/py/audit_core/x.py\n", allowed)
        self._red(check_insertion_only, out + "3\t0\taudit-core/adapters/shogi/x.py\n", allowed)


if __name__ == "__main__":
    unittest.main()
