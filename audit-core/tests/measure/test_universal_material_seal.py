# -*- coding: utf-8 -*-
u"""封 docs/UNIVERSAL_MATERIAL_SEAL_2026-11-23.md(UM0 ― 開示に限らない共通構造(材料の型 第 0 版)で、資料の指定から資料の生成までの 7 段を 1 本につなぐ)の封の門。

**この門が作る素材は、開発の 3 社(i = 101・102・103)だけ。** 本番だけの 12 社(i = 1〜12)の素材・正解の束は作らない・読まない
(``params`` で作りから決まる数を数えるだけ。素材を作る関数は ``dev_world`` を通し、開発の 3 社以外なら例外で止まる)。
置き場も道具も通信も鍵も使わない。席(subagent)は呼ばない。openpyxl は素材を書く所だけ(検査は標準の library だけで読む)。

**この門が縛るもの**

1. 封の字: 封の file の sha256・封の commit の blob と同じ・engine は封の commit から 0 行・見出しの表と表の外の言い方・規則 K0〜K9・変異 M1〜M11・D1〜D5・予測の表が、script の定数と同じ。
2. 定義表 A・B が script の定数と同じ・表の外の言い方・数字が定義表の字に無い。
3. 検査は作る側を import せず(AST)・標準の library だけ・``python3 -I`` の別 process で動き、**どんな入力でも rc 0 で結果の JSON**。
4. 開発の 3 社の正解の束: 表の外の行だけ K3 だけで止め、ほかは通し、無いを受ける。素材の file を検査が読み直した cell の値が、作る側の値と同じ。
5. 規則 K0〜K9 を 1 つずつ外した検査(関数の差し替え。戻しは try/finally)で、対応する材料の変異が通る(赤になる)。資料の検査 C1〜C4 も同じ。黙る組(別の規則も止める組)は ``SILENT_BY_DESIGN`` に置き、黙ることを別の試験で縛る。
6. 退化の入力(材料 0 個・全部 ``無い``・同じ id 2 回・位置が負や 0・数値の字の形・倍率 0・sheet の名・CSV の行が短い・壊れた JSON・孤立 surrogate・巨大な数・鍵の型違い)。
7. 置き場・計算・B の計画・B の資料・資料の検査・資料の変異 D1〜D5。
8. 記録(無い時は無いと assert し、在る時は形・禁止の字・数の導き直し)・封 → script → 定義表 → 指示書 → 門の commit の順。
"""
import ast
import collections
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
od = collections.OrderedDict


def load_module(rel, name):
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


SEAL_REL = "docs/UNIVERSAL_MATERIAL_SEAL_2026-11-23.md"
SEAL_COMMIT_SHORT = "4ef1368c"
SEAL_SHA256 = "cff6ee52b5fdb7e05018f6ffa7b8c3de2ce20f8ac0034139040815856d942e26"
GEN_REL = "measure/universal_source_gen_2026-11-23.py"
CHECK_REL = "measure/universal_check_2026-11-23.py"
DEF_RELS = ("fixtures/universal/um0/definition_A.json", "fixtures/universal/um0/definition_B.json")
INSTRUCTION_REL = "docs/UNIVERSAL_MATERIAL_INSTRUCTION_2026-11-23.md"
GATE_REL = "tests/measure/test_universal_material_seal.py"
RECORD_REL = "fixtures/universal/um0/record.json"
ORDER_FILES = (GEN_REL, CHECK_REL) + DEF_RELS + (INSTRUCTION_REL, GATE_REL)
GEN = load_module(GEN_REL, "um0_gen_for_seal_gate")
CHK = load_module(CHECK_REL, "um0_check_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_um0_seal_gate")      # 順序の部品。門としては走らせない
DEV = (101, 102, 103)


def J(text):
    return text.encode("utf-8")


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def read_bytes(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return fh.read()


def wjson(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False))


def wbytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


# ======================================================================== 開発の 3 社の世界(本番の 12 社は作らない)
_WORLD = {}
_TMPS = []


class World(object):
    pass


def dev_world(i):
    if i not in DEV:
        raise AssertionError(u"本番の会社(%r)の素材は作らない" % (i,))
    if i in _WORLD:
        return _WORLD[i]
    w = World()
    w.i = i
    w.co = GEN.build(i)
    w.tmp = tempfile.mkdtemp(prefix="um0_gate_%d_" % i)
    _TMPS.append(w.tmp)
    GEN.write_files(w.co, os.path.join(w.tmp, "A"), u"A")
    w.src_dir = os.path.join(w.tmp, "A")
    w.src = CHK.Source(w.src_dir)
    w.defA, w.defB = GEN.defn_of(CHK, u"A"), GEN.defn_of(CHK, u"B")
    w.spA, w.spB = GEN.spec_of(CHK, w.co, u"A"), GEN.spec_of(CHK, w.co, u"B")
    w.gold = GEN.gold_bundle(w.co)
    _WORLD[i] = w
    return w


def tearDownModule():
    for t in _TMPS:
        shutil.rmtree(t, ignore_errors=True)


def check(w, bundle, **kw):
    return CHK.check_bundle(w.spA, w.defA, bundle, w.src, **kw)


def verdicts(res):
    return dict((r[u"id"], (r[u"判定"], tuple(r[u"規則"]))) for r in res[u"材料"])


@contextlib.contextmanager
def removed(rule):
    u"""検査の規則 1 つを、何もしない関数に差し替える(戻しは finally)。"""
    noop = {u"K0": lambda ctx, b, w_: [], u"K7": lambda ctx, res, items: (set(), 0, 0), u"K9": lambda ctx, d: False}
    saved = CHK.RULE_FUNCS[rule]
    try:
        CHK.RULE_FUNCS[rule] = noop.get(rule, lambda ctx, m, d, info: False)
        yield
    finally:
        CHK.RULE_FUNCS[rule] = saved


@contextlib.contextmanager
def doc_removed(rule):
    saved = CHK.DOC_RULES[rule]
    try:
        CHK.DOC_RULES[rule] = lambda c: []
        yield
    finally:
        CHK.DOC_RULES[rule] = saved


# ======================================================================== 1. 封の字(手で書いた写し。script の表から作っていない)
EXPECT_TABLE = od([
    ("a01", ([u"売上高", u"売上高合計"], [u"営業収益"])), ("a02", ([u"売上高", u"売上高合計"], [u"営業収益"])), ("a03", ([u"売上総利益"], [u"粗利益"])),
    ("a04", ([u"営業利益"], [u"営業損益"])), ("a05", ([u"営業利益"], [u"営業損益"])), ("a06", ([u"経常利益"], [u"経常損益"])), ("a07", ([u"当期純利益"], [u"税引後利益"])),
    ("a08", ([u"減価償却費"], [u"償却費"])), ("a09", ([u"現金及び預金", u"現金預金"], [u"現預金"])), ("a10", ([u"流動資産合計"], [u"流動資産計"])),
    ("a11", ([u"資産合計", u"資産の部合計"], [u"総資産"])), ("a12", ([u"短期借入金"], [u"短期借入"])), ("a13", ([u"長期借入金"], [u"長期借入"])),
    ("a14", ([u"負債合計", u"負債の部合計"], [u"負債計"])), ("a15", ([u"純資産合計", u"純資産の部合計"], [u"資本合計"])), ("a16", ([u"純資産合計", u"純資産の部合計"], [u"資本合計"])),
    ("a29", ([u"期末残高", u"残高"], [u"借入残高"])), ("a30", ([u"期末従業員数", u"従業員数"], [u"社員数"])), ("b01", ([u"人件費", u"人件費合計"], [u"人件費計"])),
])
for _k in range(17, 29):
    EXPECT_TABLE["a%d" % _k] = ([u"売上高", u"月次売上高"], [u"売上金額"])
SEAL_RULE_LINES = (u"K0 形", u"K1 値", u"K2 見出しの申告", u"K3 意味", u"K4 期", u"K5 単位", u"K6 和の行", u"K7 関係", u"K8 範囲", u"K9 無い")
SEAL_MUT_PHRASES = (u"M1 数値に 1 を足す", u"M2 数値を 1000 倍にする", u"M3 表示の倍率を別の値にする", u"M4 位置を同じ行の", u"M5 位置を 1 つ下の数の行へ移し、数値と行の見出しもその cell に合わせる",
                    u"M6 期間をもう一方の期に書き換える", u"M7 位置を 1 つ下の数の行へ移し数値もその cell に合わせるが、行の見出しの申告は元のまま", u"M8 `在る` を `無い` にする",
                    u"M9 `無い` の行を `在る` にし", u"M10 2 つの材料", u"M11 `素材の和` の `行の並び` から最後の 1 行を外し", u"D1 数字 1 つを別の数字に", u"D2 単位の字を別の単位に",
                    u"D3 値の違う隣の札と札を入れ替える", u"D4 札を消す", u"D5 `無い`・`確認待ち` を `100円` に")
SEAL_PREDICTION_IDS = (u"UM0-A1", u"UM0-A2", u"UM0-A3", u"UM0-B1", u"UM0-B2", u"UM0-B3", u"UM0-B4", u"UM0-B5", u"UM0-B6", u"UM0-C1", u"UM0-C2", u"UM0-C3", u"UM0-C4", u"UM0-E1")


def seal_text():
    return read(SEAL_REL)


def git(*args):
    return subprocess.run(["git", "-C", REPO] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode("utf-8")


class SealTextTest(unittest.TestCase):
    def test_a_1_the_seal_file_is_the_sealed_bytes(self):
        self.assertEqual(SEAL_SHA256, hashlib.sha256(read_bytes(SEAL_REL)).hexdigest())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        hs = [x for x in git("log", "--format=%H", "--", PREFIX + SEAL_REL).split() if x]
        self.assertEqual(1, len(hs), hs)
        self.assertTrue(hs[0].startswith(SEAL_COMMIT_SHORT), hs)
        blob = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (hs[0], PREFIX + SEAL_REL)], stdout=subprocess.PIPE).stdout
        self.assertEqual(blob, read_bytes(SEAL_REL))

    def test_a_3_engine_is_zero_lines_from_the_seal_commit(self):
        out = git("diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core")
        self.assertEqual("", out.strip())

    def test_a_4_the_boundary_import_list_is_not_widened(self):
        body = read("tests/adapters/xbrl/test_boundary.py")
        for word in (u"universal", u"um0"):
            self.assertNotIn(word, body)

    def test_a_5_the_seal_holds_the_tables_rules_mutations_and_predictions_the_gate_copies(self):
        seal = seal_text()
        pairs = set((tuple(t), tuple(o)) for t, o in EXPECT_TABLE.values())
        for t, o in pairs:
            self.assertIn(u"[%s] / 外 [%s]" % (u", ".join(t), u", ".join(o)), seal)
        for s in SEAL_RULE_LINES + SEAL_MUT_PHRASES + SEAL_PREDICTION_IDS:
            self.assertIn(s, seal, s)
        self.assertIn(u"[a03, a06, a07, a09, a10, a12, a13, a14]", seal)

    def test_a_6_the_script_tables_equal_the_hand_copy(self):
        got = od((r[0], (r[4], r[5])) for r in GEN.ROWS_A + [GEN.ROW_B1])
        self.assertEqual(dict(EXPECT_TABLE), dict(got))
        self.assertEqual([u"a03", u"a06", u"a07", u"a09", u"a10", u"a12", u"a13", u"a14"], GEN.T5_LIST)
        self.assertEqual(tuple(u"M%d" % k for k in range(1, 12)), GEN.MUT_CODES)
        self.assertEqual(tuple(u"D%d" % k for k in range(1, 6)), GEN.DOC_CODES)
        self.assertEqual(tuple(u"K%d" % k for k in range(10)), CHK.RULES)
        self.assertEqual((101, 102, 103), GEN.DEV)
        self.assertEqual(tuple(range(1, 13)), GEN.PROD)
        self.assertEqual(20261123000, GEN.SEED_BASE)

    def test_a_7_the_production_numbers_follow_from_the_make(self):
        u"""作りから決まる数(本番の素材は作らない。``params`` だけ): 360 行・無い 7(a30 が 4・a08 が 3)・表に無い言い方 24・残り 329・形と単位と当期の終わりの割り振り。"""
        ends = {1: u"2026-03-31", 2: u"2025-12-31", 0: u"2025-09-30"}
        absent = collections.Counter()
        t5 = 0
        for i in GEN.PROD:
            p = GEN.params(i)
            self.assertEqual(ends[i % 3], GEN.iso(p["ce"]))
            self.assertEqual({1: "L1", 2: "L2", 0: "L3"}[i % 3], p["form"])
            self.assertEqual((1, 1000, 1000000)[(i // 3) % 3], p["mult"])
            self.assertEqual(i % 2 == 1, p["jp"])
            self.assertEqual(i % 4 in (0, 1), p["cur_left"])
            self.assertEqual(2, len(p["t5"]))
            self.assertEqual(sorted(set([GEN.T5_LIST[i % 8], GEN.T5_LIST[(i + 3) % 8]])), p["t5"])
            t5 += len(p["t5"])
            if not p["has_staff"]:
                absent["a30"] += 1
            if not p["has_dep"]:
                absent["a08"] += 1
        self.assertEqual({"a30": 4, "a08": 3}, dict(absent))
        self.assertEqual(24, t5)
        self.assertEqual(360 - 7 - 24, 329)
        self.assertEqual(30, len(GEN.ROWS_A))
        # 当期の始まり・前期
        p = GEN.params(1)
        self.assertEqual((u"2025-04-01", u"2026-03-31", u"2024-04-01", u"2025-03-31"), tuple(GEN.iso(p[k]) for k in ("cs", "ce", "ps", "pe")))
        self.assertTrue(GEN.params(5)["neg_net"] and GEN.params(10)["neg_net"])
        self.assertEqual([5, 10], [i for i in GEN.PROD if GEN.params(i)["neg_net"]])
        # 封 1-2 の i ごとの決めを、封の字から別に書いた表(字で持つ)と比べる(式を共有しない)。
        # 列: i -> (当期の終わり, 形, 単位の倍率, 「当期」言い方か, 当期が左か, 人員あり, 減価償却あり, 負の書き方, 表に無い言い方の 2 つ)
        sealed = {
            1: (u"2026-03-31", "L1", 1, True, True, True, True, "-", ["a06", "a10"]),
            2: (u"2025-12-31", "L2", 1, False, False, True, True, u"△", ["a07", "a12"]),
            3: (u"2025-09-30", "L3", 1000, True, False, False, True, "()", ["a09", "a13"]),
            4: (u"2026-03-31", "L1", 1000, False, True, True, False, "-", ["a10", "a14"]),
            5: (u"2025-12-31", "L2", 1000, True, True, True, True, u"△", ["a03", "a12"]),
            6: (u"2025-09-30", "L3", 1000000, False, False, False, True, "()", ["a06", "a13"]),
            7: (u"2026-03-31", "L1", 1000000, True, False, True, True, "-", ["a07", "a14"]),
            8: (u"2025-12-31", "L2", 1000000, False, True, True, False, u"△", ["a03", "a09"]),
            9: (u"2025-09-30", "L3", 1, True, True, False, True, "()", ["a06", "a10"]),
            10: (u"2026-03-31", "L1", 1, False, False, True, True, "-", ["a07", "a12"]),
            11: (u"2025-12-31", "L2", 1, True, False, True, True, u"△", ["a09", "a13"]),
            12: (u"2025-09-30", "L3", 1000, False, True, False, False, "()", ["a10", "a14"]),
        }
        self.assertEqual(list(range(1, 13)), sorted(sealed))
        for i in GEN.PROD:
            p = GEN.params(i)
            got = (GEN.iso(p["ce"]), p["form"], p["mult"], p["jp"], p["cur_left"], p["has_staff"], p["has_dep"], p["neg"], p["t5"])
            self.assertEqual(sealed[i], got, "i=%d" % i)


# ======================================================================== 2. 定義表
class DefinitionTest(unittest.TestCase):
    def test_b_1_the_definition_files_equal_the_script(self):
        for rel, product in zip(DEF_RELS, (u"A", u"B")):
            self.assertEqual(json.loads(json.dumps(GEN.def_json(product), ensure_ascii=False)), json.loads(read(rel)), rel)

    def test_b_2_no_outside_words_and_no_digits_in_the_definition_text(self):
        for rel in DEF_RELS:
            body = read(rel)
            strings = set()
            for row in json.loads(body)[u"行"]:
                strings.update(row.get(u"見出し", []))
                strings.add(row[u"名"])
                strings.add(re.sub(u"\\(.*\\)$", u"", row[u"名"]))
            for ident, (_t, outs) in EXPECT_TABLE.items():
                for w in outs:
                    self.assertNotIn(w, strings, (rel, ident, w))
            for row in json.loads(body)[u"行"]:
                self.assertIsNone(re.search(u"[0-9０-９]", row[u"名"]), row[u"名"])
            self.assertNotIn(u"表の外", body)

    def test_b_3_shape_of_the_definition(self):
        a, b = [json.loads(read(r)) for r in DEF_RELS]
        self.assertEqual({u"成果物", u"題", u"行", u"関係"}, set(a))
        self.assertEqual(33, len(a[u"行"]))
        self.assertEqual(30, len([r for r in a[u"行"] if r[u"取り方"] in (u"素材", u"素材の和")]))
        self.assertEqual([u"a31", u"a32", u"a33"], [r[u"id"] for r in a[u"行"] if r[u"取り方"] == u"計算"])
        self.assertEqual([u"b02", u"b03", u"b04"], [r[u"id"] for r in b[u"行"] if r[u"取り方"] == u"計算"])
        self.assertEqual(17, len([r for r in b[u"行"] if r[u"取り方"] != u"計算"]))
        self.assertEqual([u"R1", u"R2", u"R3"], [r[u"id"] for r in a[u"関係"]])
        self.assertEqual([u"R1"], [r[u"id"] for r in b[u"関係"]])
        for d in (a, b):
            for r in d[u"行"]:
                self.assertIn(r[u"単位"], (u"円", u"人", u"純数", u"年"))
                self.assertEqual(u"全社", r[u"範囲"])
        sums = [r for r in a[u"行"] if r[u"取り方"] == u"素材の和"]
        self.assertEqual([u"a29"], [r[u"id"] for r in sums])
        for r in a[u"行"]:
            if r[u"取り方"] != u"計算":
                self.assertEqual(u"無し" if r[u"id"] in (u"a29", u"a30") else u"要る", r[u"期の読み"])
        a33 = [r for r in a[u"行"] if r[u"id"] == u"a33"][0]
        self.assertEqual((u"比の分母和", [u"a31", u"a04", u"a08"], 2), (a33[u"式"], a33[u"入力"], a33[u"桁"]))


# ======================================================================== 3. 検査の独立
class IndependenceTest(unittest.TestCase):
    STD = set(["calendar", "csv", "datetime", "decimal", "io", "json", "os", "re", "sys", "unicodedata", "zipfile", "__future__", "fractions", "xml"])

    def test_c_1_the_check_imports_only_the_standard_library_and_not_the_make_side(self):
        tree = ast.parse(read(CHECK_REL))
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                mods.add((n.module or "").split(".")[0])
        self.assertEqual(set(), mods - self.STD, mods - self.STD)
        body = read(CHECK_REL)
        code_only = re.sub(r'(?s)u?"""(.*?)"""', "", body, count=1)           # 先頭の説明文を除く
        self.assertNotIn(u"universal_source_gen", code_only)
        names = set(n.id for n in ast.walk(tree) if isinstance(n, ast.Name)) | set(n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute))
        self.assertNotIn(u"importlib", names)
        self.assertNotIn(u"subprocess", names)

    def test_c_1b_the_make_side_uses_only_the_standard_library_and_openpyxl(self):
        tree = ast.parse(read(GEN_REL))
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                mods.add((n.module or "").split(".")[0])
        self.assertEqual(set(), mods - self.STD - set(["openpyxl", "importlib", "random", "tempfile", "collections", "copy"]), mods)
        self.assertIn("openpyxl", mods)

    def test_c_2_the_make_side_does_not_define_the_outside_words_in_the_check(self):
        body = read(CHECK_REL)
        for _i, (_t, outs) in EXPECT_TABLE.items():
            for w in outs:
                self.assertNotIn(w, body)

    def test_c_3_the_check_runs_under_dash_I_and_returns_json_with_rc_0_for_any_command(self):
        script = os.path.join(ROOT, CHECK_REL)
        env = {"PATH": os.environ.get("PATH", ""), "LANG": ""}
        cases = [[], ["nonsense"], ["material"], ["material", "--spec"], ["material", "--spec", "/no", "--def", "/no", "--bundle", "/no", "--src", "/no"],
                 ["plan", "--def", "/no", "--store", "/no"], ["document", "--def", "/no"], ["render"], ["store"], ["--out"], ["material", "--out", "/no/such/dir/x.json"]]
        for argv in cases:
            rc = subprocess.run([sys.executable, "-I", script] + argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            self.assertEqual(0, rc.returncode, (argv, rc.stderr[-300:]))
            self.assertEqual(b"", rc.stderr, argv)
            if rc.stdout:
                json.loads(rc.stdout.decode("utf-8"))
            self.assertNotIn(u"内部の例外".encode("utf-8"), rc.stdout, argv)

    def test_c_4_the_check_runs_in_an_isolated_process_on_a_dev_company_and_matches_in_process(self):
        w = dev_world(101)
        d = os.path.join(w.tmp, "cli")
        wjson(os.path.join(d, "gold.json"), w.gold)
        wbytes(os.path.join(d, "def.json"), read_bytes(DEF_RELS[0]))
        rc = subprocess.run([sys.executable, "-I", os.path.join(ROOT, CHECK_REL), "material", "--spec", os.path.join(w.src_dir, u"指定.json"), "--def", os.path.join(d, "def.json"),
                             "--bundle", os.path.join(d, "gold.json"), "--src", w.src_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={"PATH": os.environ.get("PATH", ""), "LANG": ""})
        self.assertEqual(0, rc.returncode)
        got = json.loads(rc.stdout.decode("utf-8"))
        self.assertEqual(json.loads(json.dumps(check(w, w.gold), ensure_ascii=False)), got)

    def test_c_5_the_check_does_not_read_outside_the_source_folder(self):
        w = dev_world(101)
        m = copy.deepcopy(w.gold)
        for item in m[u"材料"]:
            if item[u"id"] == u"a01":
                item[u"出どころ"][u"file"] = u"../A/決算.xlsx"
            if item[u"id"] == u"a02":
                item[u"出どころ"][u"file"] = os.path.join(w.src_dir, u"決算.xlsx")
        v = verdicts(check(w, m))
        self.assertEqual(u"止める", v[u"a01"][0])
        self.assertTrue({u"K1", u"K2", u"K3"} <= set(v[u"a01"][1]), v[u"a01"])
        self.assertIn(u"K1", v[u"a02"][1])


# ======================================================================== 4. 素材の読み書き・正解の束
def flat_cells(grid):
    return dict(grid.cells)


class MakeAndReadTest(unittest.TestCase):
    def test_d_1_the_make_is_deterministic_in_cell_values(self):
        for i in DEV:
            a, b = GEN.build(i), GEN.build(i)
            self.assertEqual(a.files, b.files)
            self.assertEqual(GEN.gold_bundle(a), GEN.gold_bundle(b))
        self.assertNotEqual(GEN.build(101).files, GEN.build(102).files)

    def test_d_2_the_check_reads_back_every_cell_the_make_wrote(self):
        for i in DEV:
            w = dev_world(i)
            for name, body in w.co.files.items():
                got = w.src.file(name)
                self.assertIsNotNone(got, name)
                if name.endswith(".xlsx"):
                    self.assertEqual(set(body), set(got[1]))
                    for sn, cells in body.items():
                        self.assertEqual(dict((k, v) for k, v in cells.items()), flat_cells(got[1][sn]), (i, name, sn))
                else:
                    want = dict(((r, c), v) for r, row in enumerate(body, 1) for c, v in enumerate(row, 1) if v != u"")
                    self.assertEqual(want, flat_cells(got[1]), (i, name))
            self.assertEqual(sorted(set(w.co.files) | {u"指定.json"}), sorted(w.src.names()))

    def test_d_3_the_relations_hold_in_the_make(self):
        for i in DEV:
            co = GEN.build(i)
            v = dict((m[u"id"], int(m[u"数値"])) for m in GEN.gold_bundle(co)[u"材料"] if m[u"状態"] == u"在る")
            self.assertEqual(v[u"a01"], sum(v[u"a%d" % k] for k in range(17, 29)))
            self.assertEqual(v[u"a11"], v[u"a14"] + v[u"a15"])
            self.assertEqual(v[u"a29"], v[u"a12"] + v[u"a13"])
            self.assertTrue(all(x > 0 for k, x in v.items() if k in (u"a01", u"a11", u"a29")))

    def test_d_4_the_dev_forms_cover_the_three_shapes_units_and_notations(self):
        co = [GEN.build(i) for i in DEV]
        self.assertEqual(set(["L1", "L2", "L3"]), set(c.p["form"] for c in co))
        self.assertEqual(set(["L1", "L2", "L3"]), set(c.p["form"] for c in co))
        self.assertEqual(set([1, 1000]), set(c.p["mult"] for c in co))        # 開発の 3 社に百万円の社は無い(本番に在る。小さい手作りの素材で見る)
        sheets = set(sn for c in co for sn in c.files[u"決算.xlsx"])
        self.assertEqual(set([u"試算表", u"部門別", u"損益", u"貸借", u"PL", u"BS"]), sheets)

    def test_d_5_the_gold_traps_are_in_the_material(self):
        u"""罠の形が素材に在る: 合計の行・当期予算の列・小計の行・前年同月の列・飾りの付いた見出し・負の書き方・単位の cell。"""
        seen_total_row = seen_budget = seen_deco = seen_neg = seen_unit = seen_prev_month = False
        for i in DEV:
            co = GEN.build(i)
            x = co.files[u"決算.xlsx"]
            for sn, cells in x.items():
                for (r, c), v in cells.items():
                    if v == u"当期予算":
                        seen_budget = True
                    if isinstance(v, str) and re.match(u"^(Ⅰ |[0-9]\\. |　)", v):
                        seen_deco = True
                    if isinstance(v, str) and re.match(u"^(-[0-9]|△[0-9]|\\([0-9])", v):
                        seen_neg = True
                    if isinstance(v, str) and v.startswith(u"(単位:"):
                        seen_unit = True
                    if v == u"合計":
                        seen_total_row = True
            seen_prev_month = seen_prev_month or co.files[u"月次売上.csv"][0][2] == u"前年同月"
            seen_total_row = seen_total_row or any(r[0] == u"合計" for r in co.files[u"借入金一覧.csv"])
            for lab in (u"売上原価", u"販売費及び一般管理費合計", u"営業外収益", u"固定資産合計"):
                self.assertTrue(any(isinstance(v, str) and lab in v for cells in x.values() for v in cells.values()), lab)
        self.assertTrue(all([seen_total_row, seen_budget, seen_deco, seen_neg, seen_unit, seen_prev_month]))
        # 封 1-2 の負の書き方(字で): text_num を直接 3 通りで呼ぶ
        self.assertEqual((u"-1,234", u"△1,234", u"(1,234)"), tuple(GEN.text_num(-1234, n) for n in (u"-", u"△", u"(")))
        self.assertEqual(u"1,234", GEN.text_num(1234, u"△"))
        # 作る側が cell に書く字が params の neg のとおり: neg だけ 3 通りに差し替えて build を呼び、負の cell の書き方を見る
        orig_params = GEN.params
        neg_re = re.compile(u"^(-[0-9]|△[0-9]|\\([0-9])")
        try:
            for i in DEV:
                for neg in (u"-", u"△", u"("):
                    def swapped(j, _o=orig_params, _n=neg):
                        q = dict(_o(j))
                        q["neg"] = _n
                        q["neg_net"] = True
                        return q
                    GEN.params = swapped
                    co = GEN.build(i)
                    self.assertEqual(neg, co.p["neg"])
                    found = [v for cells in co.files[u"決算.xlsx"].values() for v in cells.values() if isinstance(v, str) and neg_re.match(v)]
                    self.assertTrue(found, (i, neg))
                    self.assertTrue(all(v[0] == neg for v in found), (i, neg, found))
                    # R2 の注入: a11 の cell を負の字にして注入し、渡した書き方で書かれる(L2 は字の cell)
                    if co.p["form"] == u"L2":
                        a = co.mats["a11"]
                        co.files[u"決算.xlsx"][a["sheet"]][(a["row"], a["col"])] = GEN.text_num(-500, neg)
                        a["value"] = -500
                        co2, _b, _k = GEN.source_mutant(co, u"R2")
                        self.assertEqual(GEN.text_num(-499, neg), co2.files[u"決算.xlsx"][a["sheet"]][(a["row"], a["col"])])
                        self.assertEqual(neg, co2.files[u"決算.xlsx"][a["sheet"]][(a["row"], a["col"])][0])
        finally:
            GEN.params = orig_params
        self.assertIs(orig_params, GEN.params)
        # 開発の 3 社の素材そのものでも、負の cell が在る社では params の書き方と一致する(在る社は 0 にならない)
        with_neg = 0
        for i in DEV:
            co = GEN.build(i)
            found = [v for cells in co.files[u"決算.xlsx"].values() for v in cells.values() if isinstance(v, str) and neg_re.match(v)]
            if found:
                with_neg += 1
                self.assertTrue(all(v[0] == (u"(" if co.p["neg"] == u"()" else co.p["neg"]) for v in found), (i, found))
        self.assertTrue(with_neg >= 1)


class GoldStageATest(unittest.TestCase):
    def test_e_1_the_gold_is_stopped_only_on_the_outside_rows_by_k3_and_accepted_otherwise(self):
        for i in DEV:
            w = dev_world(i)
            res = check(w, w.gold)
            self.assertEqual(u"受理", res[u"束"][u"状態"])
            v = verdicts(res)
            t5 = set(w.co.p["t5"])
            absent = set(GEN.absent_ids(w.co))
            self.assertEqual(30, len(v))
            for ident, (verdict, rules) in v.items():
                if ident in t5:
                    self.assertEqual((u"止める", (u"K3",)), (verdict, rules), (i, ident))
                elif ident in absent:
                    self.assertEqual((u"無いを受ける", ()), (verdict, rules), (i, ident))
                else:
                    self.assertEqual((u"通す", ()), (verdict, rules), (i, ident))
            seen = sum(1 for k in (u"R1", u"R2", u"R3") if GEN.relation_seen(w.co, k))
            self.assertEqual({u"見た": seen, u"見なかった": 3 - seen}, res[u"K7"])

    def test_e_2_dev_counts(self):
        res = GEN.tally_a(DEV, CHK)
        self.assertEqual({u"通す": 83, u"止める": 6, u"無いを受ける": 1, u"束ごとの断り": 0}, res[u"合計"])
        for i in DEV:
            self.assertEqual({u"K3": 2}, res[u"会社ごと"][i][u"止めた規則"])

    def test_e_3_the_form_only_check_passes_everything(self):
        for i in DEV:
            w = dev_world(i)
            res = check(w, w.gold, form_only=True)
            self.assertTrue(set(r[u"判定"] for r in res[u"材料"]) <= set([u"通す", u"無いを受ける"]))
            self.assertEqual(len(GEN.absent_ids(w.co)), sum(1 for r in res[u"材料"] if r[u"判定"] == u"無いを受ける"))

    def test_e_4_a_dev_company_with_each_material_listed_once_in_the_gold(self):
        for i in DEV:
            w = dev_world(i)
            ids = [m[u"id"] for m in w.gold[u"材料"]]
            self.assertEqual(sorted(ids), ids)
            self.assertEqual(30, len(set(ids)))
            self.assertEqual(sorted(CHK.material_ids(w.defA)), ids)


# ======================================================================== 5. 規則ごとの手の値(小さい手作りの素材)
def mini(tmp, unit_cells=(u"(単位:千円)",), extra=None, csv_rows=None):
    u"""手で書いた小さい素材: xlsx(sheet S)と CSV。"""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = u"S"
    for k, u in enumerate(unit_cells):
        ws.cell(row=1 + k, column=1, value=u)
    ws.cell(row=4, column=1, value=u"科目")
    ws.cell(row=4, column=2, value=u"当期")
    ws.cell(row=4, column=3, value=u"前期")
    ws.cell(row=5, column=1, value=u"売上高")
    ws.cell(row=5, column=2, value=1234)
    ws.cell(row=5, column=3, value=u"△2,345")
    ws.cell(row=6, column=1, value=u"営業利益")
    ws.cell(row=6, column=2, value=u"(77)")
    ws.cell(row=6, column=3, value=88)
    for (r, c), v in (extra or {}).items():
        ws.cell(row=r, column=c, value=v)
    os.makedirs(tmp, exist_ok=True)
    wb.save(os.path.join(tmp, u"x.xlsx"))
    rows = csv_rows or [[u"月", u"売上高", u"前年同月"], [u"4月", u"1,000", u"900"], [u"5月", u"2,000", u"1,900"], [u"合計", u"3,000", u"2,800"], [u"短い"]]
    import csv
    with io.open(os.path.join(tmp, u"y.csv"), "w", encoding="utf-8", newline=u"") as fh:
        csv.writer(fh).writerows(rows)


MINI_DEF = {u"成果物": u"A", u"題": u"小", u"関係": [], u"行": [
    {u"id": u"s01", u"名": u"売上高", u"単位": u"円", u"期": u"当期", u"範囲": u"全社", u"取り方": u"素材", u"見出し": [u"売上高"], u"期の読み": u"要る"},
    {u"id": u"s02", u"名": u"売上高前", u"単位": u"円", u"期": u"前期", u"範囲": u"全社", u"取り方": u"素材", u"見出し": [u"売上高"], u"期の読み": u"要る"},
    {u"id": u"s03", u"名": u"営業利益", u"単位": u"円", u"期": u"当期", u"範囲": u"全社", u"取り方": u"素材", u"見出し": [u"営業利益"], u"期の読み": u"無し"},
    {u"id": u"s04", u"名": u"月の和", u"単位": u"円", u"期": u"当期末", u"範囲": u"全社", u"取り方": u"素材の和", u"見出し": [u"売上高"], u"期の読み": u"無し"},
    {u"id": u"s05", u"名": u"四月", u"単位": u"円", u"期": u"当期の月:1", u"範囲": u"全社", u"取り方": u"素材", u"見出し": [u"売上高"], u"期の読み": u"要る"},
]}
MINI_SPEC = {u"成果物": u"A", u"当期の始まり": u"2025-04-01", u"当期の終わり": u"2026-03-31"}


def mat(ident, value, unit=u"円", per=None, src=None, scope=u"全社"):
    return od([(u"id", ident), (u"状態", u"在る"), (u"数値", value), (u"単位", unit),
               (u"期間", per or od([(u"始まり", u"2025-04-01"), (u"終わり", u"2026-03-31")])), (u"範囲", scope), (u"出どころ", src)])


def xsrc(cell, rowh, colh, mult=1000):
    return od([(u"種類", u"素材"), (u"file", u"x.xlsx"), (u"位置", od([(u"sheet", u"S"), (u"セル", cell)])), (u"行の見出し", rowh), (u"列の見出し", colh), (u"表示の倍率", mult)])


def csrc(r, c, rowh, colh, mult=1):
    return od([(u"種類", u"素材"), (u"file", u"y.csv"), (u"位置", od([(u"行", r), (u"列", c)])), (u"行の見出し", rowh), (u"列の見出し", colh), (u"表示の倍率", mult)])


def mini_bundle(items):
    return od([(u"型の版", u"u0"), (u"材料", items)])


PRIOR = od([(u"始まり", u"2024-04-01"), (u"終わり", u"2025-03-31")])
ENDPT = od([(u"時点", u"2026-03-31")])


def mini_good():
    return [mat(u"s01", u"1234000", src=xsrc(u"B5", u"売上高", u"当期")), mat(u"s02", u"-2345000", per=PRIOR, src=xsrc(u"C5", u"売上高", u"前期")),
            mat(u"s03", u"-77000", src=xsrc(u"B6", u"営業利益", u"当期")),
            mat(u"s04", u"3000", per=ENDPT, src=od([(u"種類", u"素材の和"), (u"file", u"y.csv"), (u"列", 2), (u"行の並び", [2, 3]), (u"列の見出し", u"売上高"), (u"表示の倍率", 1)])),
            mat(u"s05", u"1000", per=od([(u"始まり", u"2025-04-01"), (u"終わり", u"2025-04-30")]), src=csrc(2, 2, u"4月", u"売上高"))]


class MiniRuleTest(unittest.TestCase):
    def run_mini(self, items, **kw):
        with tempfile.TemporaryDirectory() as tmp:
            mini(tmp, **kw)
            wjson(os.path.join(tmp, "spec.json"), MINI_SPEC)
            wjson(os.path.join(tmp, "def.json"), MINI_DEF)
            wjson(os.path.join(tmp, "b.json"), mini_bundle(items) if isinstance(items, list) else items)
            return CHK.check_files(os.path.join(tmp, "spec.json"), os.path.join(tmp, "def.json"), os.path.join(tmp, "b.json"), tmp)

    def rules_of(self, items, ident, **kw):
        res = self.run_mini(items, **kw)
        self.assertEqual(u"受理", res[u"束"][u"状態"], res[u"束"])
        return dict((r[u"id"], tuple(r[u"規則"])) for r in res[u"材料"])[ident]

    def change(self, ident, fn):
        items = mini_good()
        for m in items:
            if m[u"id"] == ident:
                fn(m)
        return items

    def test_f_0_the_good_mini_bundle_passes_with_hand_numbers(self):
        res = self.run_mini(mini_good())
        self.assertEqual([(u"通す", ())] * 5, [(r[u"判定"], tuple(r[u"規則"])) for r in res[u"材料"]])
        self.assertEqual({u"見た": 0, u"見なかった": 0}, res[u"K7"])

    def test_f_1_k1_value_times_multiplier(self):
        self.assertEqual((u"K1",), self.rules_of(self.change(u"s01", lambda m: m.__setitem__(u"数値", u"1234001")), u"s01"))
        self.assertEqual((u"K1",), self.rules_of(self.change(u"s04", lambda m: m.__setitem__(u"数値", u"2999")), u"s04"))
        self.assertEqual((u"K1",), self.rules_of(self.change(u"s01", lambda m: m[u"出どころ"].__setitem__(u"位置", od([(u"sheet", u"S"), (u"セル", u"B99")]))), u"s01")[:1] + (u"K1",)[1:])

    def test_f_2_k2_declared_headings(self):
        self.assertIn(u"K2", self.rules_of(self.change(u"s01", lambda m: m[u"出どころ"].__setitem__(u"列の見出し", u"前期")), u"s01"))
        self.assertEqual((u"K2",), self.rules_of(self.change(u"s03", lambda m: m[u"出どころ"].__setitem__(u"行の見出し", u"売上高")), u"s03")[:1])
        # 正規化の後に同じなら通る
        self.assertEqual((), self.rules_of(self.change(u"s01", lambda m: m[u"出どころ"].__setitem__(u"行の見出し", u"Ⅰ 売 上高")), u"s01"))

    def test_f_3_k3_exactly_one_side_in_the_table(self):
        both = self.change(u"s01", lambda m: m[u"出どころ"].__setitem__(u"位置", od([(u"sheet", u"S"), (u"セル", u"B5")])))
        extra = {(4, 2): u"売上高"}
        self.assertIn(u"K3", self.rules_of(both, u"s01", extra=extra))
        neither = self.rules_of(self.change(u"s01", lambda m: None), u"s01", extra={(5, 1): u"売上金額"})
        self.assertIn(u"K3", neither)
        self.assertNotIn(u"K4", neither)       # 表に当たらなかった行は K4 の見出しの側を見ない

    def test_f_4_k4_period(self):
        self.assertEqual((u"K4",), self.rules_of(self.change(u"s01", lambda m: m.__setitem__(u"期間", PRIOR)), u"s01"))
        self.assertEqual((u"K4",), self.rules_of(self.change(u"s03", lambda m: m.__setitem__(u"期間", PRIOR)), u"s03"))
        def to_current_col(m):
            m[u"出どころ"].update(od([(u"位置", od([(u"sheet", u"S"), (u"セル", u"B5")])), (u"列の見出し", u"当期")]))
            m[u"数値"] = u"1234000"
        self.assertEqual((u"K4",), self.rules_of(self.change(u"s02", to_current_col), u"s02"))
        # 無しの行(s03)の列の見出しは見ない・要る行(s01)の「当期」は読める
        self.assertEqual((), self.rules_of(mini_good(), u"s03"))
        # 読めない見出し(当期予算)
        self.assertIn(u"K4", self.rules_of(mini_good(), u"s01", extra={(4, 2): u"当期予算"}))
        # 月の見出し: 5 月は 2 か月目
        def to_may(m):
            m[u"出どころ"].update(od([(u"位置", od([(u"行", 3), (u"列", 2)])), (u"行の見出し", u"5月")]))
            m[u"数値"] = u"2000"
        self.assertEqual((u"K4",), self.rules_of(self.change(u"s05", to_may), u"s05"))

    def test_f_5_k5_unit(self):
        self.assertIn(u"K5", self.rules_of(self.change(u"s01", lambda m: m.__setitem__(u"単位", u"人")), u"s01"))
        self.assertIn(u"K5", self.rules_of(self.change(u"s01", lambda m: m[u"出どころ"].__setitem__(u"表示の倍率", 1)), u"s01"))
        self.assertEqual((), self.rules_of(mini_good(), u"s01", unit_cells=(u"(単位:千円)",)))
        self.assertIn(u"K5", self.rules_of(mini_good(), u"s01", unit_cells=(u"(単位:千円)", u"単位:百万円")))     # 2 個以上は読めない
        self.assertIn(u"K5", self.rules_of(mini_good(), u"s01", unit_cells=()))      # 0 個は円
        self.assertEqual((), self.rules_of(mini_good(), u"s01", unit_cells=(u"単位:千円",)))
        self.assertEqual((), self.rules_of(mini_good(), u"s01", unit_cells=(u"(単位:千円)",)))
        self.assertEqual((), self.rules_of(mini_good(), u"s01", unit_cells=(u"（単位：千円）",)))
        mm = mini_good()
        mm[0][u"数値"], mm[0][u"出どころ"][u"表示の倍率"] = u"1234000000", 1000000
        self.assertEqual((), self.rules_of(mm, u"s01", unit_cells=(u"(単位:百万円)",)))
        self.assertIn(u"K5", self.rules_of(mm, u"s01", unit_cells=(u"(単位:千円)",)))

    def test_f_6_k6_sum_rows(self):
        self.assertEqual((u"K6",), self.rules_of(self.change(u"s04", lambda m: (m[u"出どころ"].__setitem__(u"行の並び", [2, 3, 4]), m.__setitem__(u"数値", u"6000"))), u"s04"))
        self.assertEqual((u"K6",), self.rules_of(self.change(u"s04", lambda m: (m[u"出どころ"].__setitem__(u"行の並び", [2]), m.__setitem__(u"数値", u"1000"))), u"s04"))
        self.assertEqual((), self.rules_of(mini_good(), u"s04"))
        # 「計」の行も合計と同じに除く(合計・計のどちらも明細ではない)
        rows = [[u"月", u"売上高", u"前年同月"], [u"4月", u"1,000", u"900"], [u"5月", u"2,000", u"1,900"], [u"計", u"3,000", u"2,800"], [u"　合 計 ", u"3,000", u"2,800"], [u"小計", u"3,000", u"2,800"]]
        self.assertEqual((u"K6",), self.rules_of(mini_good(), u"s04", csv_rows=rows))          # 「小計」は明細として数える(封は 合計・計 だけ)
        rows[5] = [u"その他", u"0", u"0"]
        self.assertEqual((), self.rules_of(self.change(u"s04", lambda m: (m[u"出どころ"].__setitem__(u"行の並び", [2, 3, 6]), m.__setitem__(u"数値", u"3000"))), u"s04", csv_rows=rows))

    def test_f_7_k7_relations(self):
        d = copy.deepcopy(MINI_DEF)
        d[u"関係"] = [{u"id": u"Rx", u"左": [u"s05"], u"右": [u"s04"]}]
        items = mini_good()
        with tempfile.TemporaryDirectory() as tmp:
            mini(tmp)
            wjson(os.path.join(tmp, "spec.json"), MINI_SPEC)
            wjson(os.path.join(tmp, "def.json"), d)
            wjson(os.path.join(tmp, "b.json"), mini_bundle(items))
            res = CHK.check_files(os.path.join(tmp, "spec.json"), os.path.join(tmp, "def.json"), os.path.join(tmp, "b.json"), tmp)
        v = dict((r[u"id"], tuple(r[u"規則"])) for r in res[u"材料"])
        self.assertEqual((u"K7",), v[u"s04"])
        self.assertEqual((u"K7",), v[u"s05"])
        self.assertEqual((), v[u"s01"])
        self.assertEqual({u"見た": 1, u"見なかった": 0}, res[u"K7"])

    def test_f_8_k8_scope_and_k9_none(self):
        self.assertEqual((u"K8",), self.rules_of(self.change(u"s01", lambda m: m.__setitem__(u"範囲", u"部門")), u"s01"))
        none = od([(u"id", u"s03"), (u"状態", u"無い"), (u"無い理由", u"素材が無い")])
        items = mini_good()
        items[2] = none
        self.assertEqual((u"K9",), self.rules_of(items, u"s03"))           # 営業利益の字が在る
        items2 = mini_good()
        items2[2] = none
        # 字が無ければ受ける
        with tempfile.TemporaryDirectory() as tmp:
            mini(tmp, extra={(6, 1): u"営業損益"})
            wjson(os.path.join(tmp, "spec.json"), MINI_SPEC)
            wjson(os.path.join(tmp, "def.json"), MINI_DEF)
            wjson(os.path.join(tmp, "b.json"), mini_bundle(items2))
            res = CHK.check_files(os.path.join(tmp, "spec.json"), os.path.join(tmp, "def.json"), os.path.join(tmp, "b.json"), tmp)
        self.assertEqual(u"無いを受ける", [x for x in res[u"材料"] if x[u"id"] == u"s03"][0][u"判定"])

    def test_f_9_number_reading_and_heading_reading(self):
        n = CHK.cell_number
        from fractions import Fraction as F
        for v, want in ((u"1,234", F(1234)), (u" 12 ", F(12)), (u"-5", F(-5)), (u"△5", F(-5)), (u"▲5", F(-5)), (u"(5)", F(-5)), (7, F(7)), (u"0", F(0)), (1.5, F(3, 2)), (u"　5　", F(5))):
            self.assertEqual(want, n(v), v)
        for v in (u"1e3", u"１", u"+1", u"1.5", u"", None, True, u"(5", u"5)", u"-", u"--5", u"1 2", u"約5", float("nan"), float("inf"), [], {}):
            self.assertIsNone(n(v), v)
        self.assertEqual(u"売上高", CHK.norm(u"Ⅰ 売上高"))
        self.assertEqual(u"売上高", CHK.norm(u"1. 売上高"))
        self.assertEqual(u"売上高", CHK.norm(u"　売上高　"))
        self.assertEqual(u"売上高", CHK.norm(u"Ⅲ.売上高"))
        self.assertEqual(u"123", CHK.norm(u"123"))            # 取った後に残らなければ取らない
        self.assertEqual(u"月", CHK.norm(u"4月"))             # 封の字どおり(頭の数字を取る)
        self.assertEqual(u"", CHK.norm(None))

    def test_f_10_period_reading(self):
        class S(object):
            pass
        sp = S()
        sp.cs, sp.ce = CHK.parse_date(u"2025-04-01"), CHK.parse_date(u"2026-03-31")
        sp.ps, sp.pe = CHK.parse_date(u"2024-04-01"), CHK.parse_date(u"2025-03-31")
        d = CHK.parse_date
        rd = lambda h, k: CHK.read_period(h, k, sp)
        self.assertEqual((u"期間", sp.cs, sp.ce), rd(u"当期", u"期間"))
        self.assertEqual((u"時点", sp.ce), rd(u"当期", u"時点"))
        self.assertEqual((u"時点", sp.pe), rd(u"前期", u"時点"))
        self.assertEqual((u"期間", sp.cs, sp.ce), rd(u"2026年3月期", u"期間"))
        self.assertEqual((u"時点", d(u"2026-03-31")), rd(u"2026年3月期", u"時点"))
        self.assertEqual((u"時点", d(u"2026-03-31")), rd(u"2026年3月末", u"時点"))
        self.assertEqual((u"期間", d(u"2025-05-01"), d(u"2025-05-31")), rd(u"5月", u"期間"))
        self.assertEqual((u"期間", d(u"2026-02-01"), d(u"2026-02-28")), rd(u"2026/02", u"期間"))
        self.assertEqual((u"期間", d(u"2026-01-01"), d(u"2026-01-31")), rd(u"2026年1月", u"期間"))
        self.assertEqual((u"期間", sp.cs, sp.ce), rd(u"1. 当期", u"期間"))
        self.assertEqual((u"期間", d(u"2025-04-01"), d(u"2025-04-30")), rd(u"　4 月", u"期間"))
        for bad in (u"当期予算", u"前年同月", u"", u"13月", u"2026年13月期", u"2026/13", None, 5):
            self.assertIsNone(rd(bad, u"期間"), bad)


# ======================================================================== 6. 変異と規則を 1 つずつ外した検査
#: 予測(実行より先に書いた): 規則 R を外した検査で「通してしまう」(通した数が増える)材料の変異の符号。
REMOVE_RED = od([
    (u"K0", [u"X0"]), (u"K1", [u"M1", u"M2"]), (u"K2", [u"XH"]), (u"K3", [u"M5", u"M10"]), (u"K4", [u"M4", u"M6"]),
    (u"K5", [u"XU", u"XM"]), (u"K6", [u"M11"]), (u"K7", [u"S"]), (u"K8", [u"XG"]), (u"K9", [u"M8"])])
#: 予測: 規則 R を外しても通らない(別の規則も止める)組。黙ること自体を別の試験で縛る(退化値の穴の記録)。
SILENT_BY_DESIGN = od([
    (u"K1", [u"M3"]),         # 倍率の書き換えは K5 も止める
    (u"K2", [u"M7"]),         # K3 か K4 も止める
    (u"K3", [u"M7"]),         # K2 も止める
    (u"K5", [u"M3"]),         # K1 も止める
    (u"K9", [u"M9"]),         # K1・K2・K3 も止める
])
ALL_MUT_FOR_SWEEP = (u"M1", u"M2", u"M3", u"M4", u"M5", u"M6", u"M7", u"M8", u"M9", u"M10", u"M11", u"X0", u"XH", u"XU", u"XM", u"XG")


def mutant_passes(codes):
    u"""開発の 3 社で、符号ごとの「通した」数(いま入っている規則の関数で)。"""
    out = collections.Counter()
    made = collections.Counter()
    for i in DEV:
        w = dev_world(i)
        for code in codes:
            if code in GEN.MUT_CODES:
                plan = [p for p in GEN.mutant_plan(w.co, w.gold) if p[0] == code]
                mk = lambda p: GEN.make_mutant(w.co, w.gold, p[0], p[1], p[2])
            else:
                plan = [(code, m[u"id"], None) for m in w.gold[u"材料"]]
                mk = lambda p: GEN.make_extra(w.co, w.gold, p[0], p[1])
            for p in plan:
                b = mk(p)
                if b is None:
                    continue
                made[code] += 1
                res = check(w, b)
                if GEN.judge_mutant(res, [p[1]] + ([p[2]] if p[2] else [])) == u"通した":
                    out[code] += 1
    return out, made


class MutationSweepTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_passes, cls.made = mutant_passes(ALL_MUT_FOR_SWEEP)

    def test_g_1_with_all_rules_only_the_unseen_none_claims_slip_through(self):
        u"""M8 を表に無い言い方の行に掛けると、素材に表の字が無いので K9 が見つけられず「無いを受ける」(封の A2 の予測が外れる所)。ほかは 1 つも通さない。"""
        want = collections.Counter()
        for i in DEV:
            want[u"M8"] += len(GEN.build(i).p["t5"])
        self.assertEqual(want, self.base_passes)

    def test_g_2_the_made_counts_are_positive_for_every_code_except_where_the_shape_is_missing(self):
        for code in ALL_MUT_FOR_SWEEP:
            self.assertGreater(self.made[code], 0, code)

    def test_g_3_removing_each_rule_lets_its_mutation_through(self):
        for rule, codes in REMOVE_RED.items():
            if codes == [u"S"]:
                continue
            with removed(rule):
                passes, _made = mutant_passes(codes)
            for code in codes:
                self.assertGreater(passes[code], self.base_passes[code], (rule, code))

    def test_g_4_silent_pairs_stay_silent_and_are_the_only_silent_pairs(self):
        for rule, codes in SILENT_BY_DESIGN.items():
            with removed(rule):
                passes, _m = mutant_passes(codes)
            for code in codes:
                self.assertEqual(self.base_passes[code], passes[code], (rule, code))

    def test_g_5_removing_a_rule_never_lowers_the_pass_count(self):
        for rule in (u"K1", u"K2", u"K3", u"K4", u"K5", u"K6", u"K8", u"K9"):
            with removed(rule):
                passes, _m = mutant_passes((u"M1", u"M6", u"M8", u"M10"))
            for code in (u"M1", u"M6", u"M8", u"M10"):
                self.assertGreaterEqual(passes[code], self.base_passes[code], (rule, code))

    def test_g_6_the_removal_is_restored_after_the_with_block(self):
        before = dict(CHK.RULE_FUNCS)
        with removed(u"K3"):
            self.assertNotEqual(before[u"K3"], CHK.RULE_FUNCS[u"K3"])
        self.assertEqual(before, CHK.RULE_FUNCS)
        try:
            with removed(u"K9"):
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertEqual(before, CHK.RULE_FUNCS)

    def test_g_7_the_form_only_check_passes_every_mutation_that_keeps_the_shape(self):
        for i in DEV:
            w = dev_world(i)
            for code, ident, ident2 in GEN.mutant_plan(w.co, w.gold):
                b = GEN.make_mutant(w.co, w.gold, code, ident, ident2)
                if b is None:
                    continue
                res = check(w, b, form_only=True)
                self.assertEqual(u"受理", res[u"束"][u"状態"], (i, code, ident))
                self.assertTrue(all(r[u"判定"] != u"止める" for r in res[u"材料"]), (i, code, ident))

    def test_g_8_every_mutant_differs_from_the_gold(self):
        for i in DEV:
            w = dev_world(i)
            for code, ident, ident2 in GEN.mutant_plan(w.co, w.gold):
                b = GEN.make_mutant(w.co, w.gold, code, ident, ident2)
                if b is not None:
                    self.assertNotEqual(w.gold, b, (i, code, ident))

    def test_g_9_the_mutants_change_only_the_aimed_place(self):
        w = dev_world(101)
        g = dict((m[u"id"], m) for m in w.gold[u"材料"])
        def only(b, ident, keys):
            nb = dict((m[u"id"], m) for m in b[u"材料"])
            self.assertEqual([ident], [k for k in nb if nb[k] != g[k]])
            for k in set(nb[ident]) | set(g[ident]):
                if k not in keys:
                    self.assertEqual(g[ident].get(k), nb[ident].get(k), (ident, k))
        only(GEN.make_mutant(w.co, w.gold, u"M1", u"a01"), u"a01", (u"数値",))
        only(GEN.make_mutant(w.co, w.gold, u"M3", u"a01"), u"a01", (u"出どころ",))
        only(GEN.make_mutant(w.co, w.gold, u"M6", u"a01"), u"a01", (u"期間",))
        only(GEN.make_mutant(w.co, w.gold, u"M8", u"a01"), u"a01", (u"状態", u"数値", u"単位", u"期間", u"範囲", u"出どころ", u"無い理由"))
        m3 = GEN.make_mutant(w.co, w.gold, u"M3", u"a01")
        self.assertEqual(g[u"a01"][u"数値"], [m for m in m3[u"材料"] if m[u"id"] == u"a01"][0][u"数値"])
        m11 = GEN.make_mutant(w.co, w.gold, u"M11", u"a29")
        a29 = [m for m in m11[u"材料"] if m[u"id"] == u"a29"][0]
        self.assertEqual(g[u"a29"][u"出どころ"][u"行の並び"][:-1], a29[u"出どころ"][u"行の並び"])
        self.assertEqual(int(g[u"a29"][u"数値"]) - GEN.build(101).loans[-1][2], int(a29[u"数値"]))
        m10 = GEN.make_mutant(w.co, w.gold, u"M10", u"a01", u"a02")
        nb = dict((m[u"id"], m) for m in m10[u"材料"])
        self.assertEqual(g[u"a02"][u"出どころ"], nb[u"a01"][u"出どころ"])
        self.assertEqual(g[u"a02"][u"数値"], nb[u"a01"][u"数値"])
        self.assertEqual(g[u"a01"][u"期間"], nb[u"a01"][u"期間"])


class SourceMutationTest(unittest.TestCase):
    u"""K7: 素材のほうを書き換えて材料も合わせる(K1〜K6 を通る)。関係を見る時だけ止める。"""

    def run_kind(self, w, kind):
        co2, bundle, _k = GEN.source_mutant(w.co, kind)
        d = os.path.join(w.tmp, "S_" + kind)
        shutil.rmtree(d, ignore_errors=True)
        GEN.write_files(co2, d, u"A")
        return CHK.check_bundle(w.spA, w.defA, bundle, CHK.Source(d))

    def test_h_1_the_relation_stops_every_material_on_it_exactly_when_it_is_seen(self):
        ids = {u"R1": [u"a%d" % k for k in range(17, 29)] + [u"a01"], u"R2": [u"a11", u"a14", u"a15"], u"R3": [u"a29", u"a12", u"a13"]}
        for i in DEV:
            w = dev_world(i)
            for kind in (u"R1", u"R2", u"R3"):
                res = self.run_kind(w, kind)
                v = verdicts(res)
                seen = GEN.relation_seen(w.co, kind)
                for ident in ids[kind]:
                    if ident in w.co.p["t5"]:
                        self.assertEqual(u"止める", v[ident][0])
                    elif seen:
                        self.assertEqual((u"止める", (u"K7",)), v[ident], (i, kind, ident))
                    else:
                        self.assertEqual((u"通す", ()), v[ident], (i, kind, ident))

    def test_h_2_without_k7_the_source_mutation_passes_where_it_was_seen(self):
        total = 0
        for i in DEV:
            w = dev_world(i)
            for kind in (u"R1", u"R2", u"R3"):
                with removed(u"K7"):
                    v = verdicts(self.run_kind(w, kind))
                if GEN.relation_seen(w.co, kind):
                    total += 1
                    for ident, (verdict, rules) in v.items():
                        self.assertNotIn(u"K7", rules)
        self.assertGreater(total, 0)

    def test_h_3_each_relation_is_seen_in_some_dev_company_and_unseen_in_another(self):
        for kind in (u"R1", u"R2", u"R3"):
            flags = [GEN.relation_seen(dev_world(i).co, kind) for i in DEV]
            self.assertIn(True, flags, kind)
        self.assertIn(False, [GEN.relation_seen(dev_world(i).co, u"R3") for i in DEV])
        self.assertIn(False, [GEN.relation_seen(dev_world(i).co, u"R2") for i in DEV])


# ======================================================================== 7. 退化の入力
class DegenerateTest(unittest.TestCase):
    def w(self):
        return dev_world(101)

    def refused(self, bundle, reason_part=None):
        w = self.w()
        res = check(w, bundle)
        self.assertEqual(u"断り", res[u"束"][u"状態"], str(bundle)[:200])
        self.assertEqual([u"K0"], res[u"束"][u"規則"])
        self.assertEqual([], res[u"材料"])
        if reason_part:
            self.assertTrue(any(reason_part in r for r in res[u"束"][u"理由"]), res[u"束"][u"理由"])
        return res

    def edit(self, ident, fn):
        b = copy.deepcopy(self.w().gold)
        for m in b[u"材料"]:
            if m[u"id"] == ident:
                fn(m)
        return b

    def test_i_1_zero_materials_and_all_none(self):
        self.refused(od([(u"型の版", u"u0"), (u"材料", [])]), u"頼んだ行")
        w = self.w()
        allnone = od([(u"型の版", u"u0"), (u"材料", [od([(u"id", m[u"id"]), (u"状態", u"無い"), (u"無い理由", u"素材が無い")]) for m in w.gold[u"材料"]])])
        res = check(w, allnone)
        self.assertEqual(u"受理", res[u"束"][u"状態"])
        got = collections.Counter(r[u"判定"] for r in res[u"材料"])
        self.assertEqual(30, sum(got.values()))
        self.assertEqual(set(u"a%02d" % k for k in range(1, 31)) - set(GEN.absent_ids(w.co)) - set(w.co.p["t5"]), set(r[u"id"] for r in res[u"材料"] if r[u"判定"] == u"止める"))
        for r in res[u"材料"]:
            if r[u"判定"] == u"止める":
                self.assertEqual([u"K9"], r[u"規則"])

    def test_i_2_duplicate_ids_and_missing_ids_and_extra_ids(self):
        w = self.w()
        b = copy.deepcopy(w.gold)
        b[u"材料"].append(copy.deepcopy(b[u"材料"][0]))
        self.refused(b, u"重複")
        b = copy.deepcopy(w.gold)
        b[u"材料"].pop()
        self.refused(b, u"頼んだ行")
        b = copy.deepcopy(w.gold)
        b[u"材料"][0][u"id"] = u"zz9"
        self.refused(b, u"頼んだ行")

    def test_i_3_positions_negative_zero_and_wrong_types(self):
        for pos in (od([(u"行", -1), (u"列", 2)]), od([(u"行", 0), (u"列", 2)]), od([(u"行", 2), (u"列", 0)]), od([(u"行", True), (u"列", 2)]), od([(u"行", 2.0), (u"列", 2)]),
                    od([(u"行", u"2"), (u"列", 2)]), od([(u"行", 2)]), od([(u"sheet", u"S")]), [], None, u"B5"):
            self.refused(self.edit(u"a17", lambda m, pos=pos: m[u"出どころ"].__setitem__(u"位置", pos)), u"位置")
        for cell in (u"B0", u"b5", u"B", u"5", u"B-1", u"AAAA1", u"B05", u"", None, 5):
            self.refused(self.edit(u"a01", lambda m, cell=cell: m[u"出どころ"][u"位置"].__setitem__(u"セル", cell)), u"位置")
        self.refused(self.edit(u"a29", lambda m: m[u"出どころ"].__setitem__(u"行の並び", [3, 2])), u"行の並び")
        self.refused(self.edit(u"a29", lambda m: m[u"出どころ"].__setitem__(u"行の並び", [])), u"行の並び")
        self.refused(self.edit(u"a29", lambda m: m[u"出どころ"].__setitem__(u"行の並び", [2, 2])), u"行の並び")
        self.refused(self.edit(u"a29", lambda m: m[u"出どころ"].__setitem__(u"列", 0)), u"列")

    def test_i_4_value_strings_that_are_not_plain_integers(self):
        for v in (u"1e3", u"01", u"+1", u"１", u"1,000", u"1.0", u"", u"-", u"--1", u" 1", u"1 ", u"1\n", u"-0 ", u"０", 5, None, 1.5, True, [1]):
            self.refused(self.edit(u"a01", lambda m, v=v: m.__setitem__(u"数値", v)), u"数値")
        w = self.w()
        for v in (u"0", u"-1", u"123"):
            res = check(w, self.edit(u"a01", lambda m, v=v: m.__setitem__(u"数値", v)))
            self.assertEqual(u"受理", res[u"束"][u"状態"])

    def test_i_5_multiplier_zero_and_other_values(self):
        for mult in (0, -1, 10, 999, 1000.0, u"1", True, None, [1000]):
            self.refused(self.edit(u"a01", lambda m, mult=mult: m[u"出どころ"].__setitem__(u"表示の倍率", mult)), u"表示の倍率")

    def test_i_6_sheet_names_files_and_cells_outside(self):
        w = self.w()
        b = self.edit(u"a01", lambda m: m[u"出どころ"][u"位置"].__setitem__(u"sheet", u"無い sheet"))
        v = verdicts(check(w, b))
        self.assertEqual(u"止める", v[u"a01"][0])
        self.assertTrue({u"K1", u"K2", u"K3"} <= set(v[u"a01"][1]))
        for cell in (u"ZZZ99999", u"B100000", u"XFD1048576"):
            b = self.edit(u"a01", lambda m, cell=cell: m[u"出どころ"][u"位置"].__setitem__(u"セル", cell))
            self.assertIn(u"K1", verdicts(check(w, b))[u"a01"][1])
        b = self.edit(u"a17", lambda m: m[u"出どころ"].__setitem__(u"位置", od([(u"行", 10 ** 9), (u"列", 10 ** 9)])))
        self.assertIn(u"K1", verdicts(check(w, b))[u"a17"][1])
        for name in (u"無い.csv", u"", u"../x", u"/etc/passwd", u"決算.xlsx/", u".", u"人員.csv\x00"):
            b = self.edit(u"a17", lambda m, name=name: m[u"出どころ"].__setitem__(u"file", name))
            self.assertIn(u"K1", verdicts(check(w, b))[u"a17"][1], name)
        b = self.edit(u"a17", lambda m: m[u"出どころ"].__setitem__(u"file", u"決算.xlsx"))              # 種類が CSV の位置で xlsx
        self.assertIn(u"K1", verdicts(check(w, b))[u"a17"][1])

    def test_i_7_a_short_csv_row_and_missing_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            wbytes(os.path.join(tmp, u"月次売上.csv"), u"月,売上高,前年同月\n4月\n5月,\n,,\n".encode("utf-8"))
            w = self.w()
            src = CHK.Source(tmp)
            b = self.edit(u"a17", lambda m: None)
            res = CHK.check_bundle(w.spA, w.defA, b, src)
            self.assertEqual(u"受理", res[u"束"][u"状態"])
            self.assertIn(u"K1", verdicts(res)[u"a17"][1])
            g = src.file(u"月次売上.csv")[1]
            self.assertIsNone(g.get(2, 2))

    def test_i_8_broken_files_through_the_file_api(self):
        w = self.w()
        specp = os.path.join(w.src_dir, u"指定.json")
        defp = os.path.join(w.tmp, "defA.json")
        wbytes(defp, read_bytes(DEF_RELS[0]))
        with tempfile.TemporaryDirectory() as tmp:
            good = os.path.join(tmp, "g.json")
            wjson(good, w.gold)
            cases = {
                "missing": os.path.join(tmp, "none.json"), "empty": b"", "notjson": b"{{", "list": b"[]", "null": b"null", "str": b'"x"', "num": b"1",
                "deep": b"[" * 100000, "deepobj": b'{"a":' * 50000, "nan": J(u'{"型の版":NaN}'), "bom": b"\xef\xbb\xbf{}", "latin1": b'{"x":"\xe9"}',
                "surrogate": u'{"型の版":"u0","材料":[{"id":"\\ud800","状態":"無い","無い理由":"素材が無い"}]}'.encode("utf-8"),
                "keys": J(u'{"型の版":"u0","材料":[],"extra":1}'), "version": J(u'{"型の版":"u1","材料":[]}'), "mat_not_list": J(u'{"型の版":"u0","材料":{"a":1}}'),
                "item_str": J(u'{"型の版":"u0","材料":["x"]}'), "id_int": J(u'{"型の版":"u0","材料":[{"id":1,"状態":"無い","無い理由":"素材が無い"}]}'),
                "state": J(u'{"型の版":"u0","材料":[{"id":"a01","状態":"保留"}]}'), "none_reason": J(u'{"型の版":"u0","材料":[{"id":"a01","状態":"無い","無い理由":"x"}]}'),
                "none_extra": J(u'{"型の版":"u0","材料":[{"id":"a01","状態":"無い","無い理由":"素材が無い","数値":"1"}]}'),
            }
            for name, body in cases.items():
                p = body if isinstance(body, str) else os.path.join(tmp, name + ".json")
                if not isinstance(body, str):
                    wbytes(p, body)
                res = CHK.check_files(specp, defp, p, w.src_dir)
                self.assertIn(res[u"束"][u"状態"], (u"断り",), name)
                self.assertEqual([u"K0"], res[u"束"][u"規則"], name)
            for bad_spec in (b"", b"{", b"[]", J(u'{"成果物":"A"}'), J(u'{"成果物":"C","当期の始まり":"2025-04-01","当期の終わり":"2026-03-31"}'),
                             J(u'{"成果物":"A","当期の始まり":"2025-02-30","当期の終わり":"2026-03-31"}'), J(u'{"成果物":"A","当期の始まり":"2026-04-01","当期の終わり":"2025-03-31"}'),
                             J(u'{"成果物":"A","当期の始まり":"0001-01-01","当期の終わり":"2026-03-31"}'),
                             J(u'{"成果物":"A","当期の始まり":"2025-04-01","当期の終わり":"2026-03-31","x":1}'), J(u'{"成果物":"A","当期の始まり":20250401,"当期の終わり":"2026-03-31"}')):
                p = os.path.join(tmp, "spec_bad.json")
                wbytes(p, bad_spec)
                res = CHK.check_files(p, defp, good, w.src_dir)
                self.assertEqual(u"断り", res[u"束"][u"状態"], bad_spec)
                self.assertEqual([u"入力"], res[u"束"][u"規則"], bad_spec)
            p = os.path.join(tmp, "spec_edge.json")
            wbytes(p, J(u'{"成果物":"A","当期の始まり":"9999-12-31","当期の終わり":"9999-12-31"}'))
            res = CHK.check_files(p, defp, good, w.src_dir)              # 在る日なので指定は読める。月の日付が作れない行は K4 で止まるだけで落ちない
            self.assertEqual(u"受理", res[u"束"][u"状態"])
            self.assertTrue(all(u"K4" in r[u"規則"] for r in res[u"材料"] if r[u"状態"] == u"在る"))
            for bad_def in (b"", b"[]", J(u'{"行":1}'), J(u'{"行":[1]}'), J(u'{"行":[{"id":1}]}'), J(u'{"行":[{"id":"a"},{"id":"a"}]}')):
                p = os.path.join(tmp, "def_bad.json")
                wbytes(p, bad_def)
                res = CHK.check_files(specp, p, good, w.src_dir)
                self.assertEqual([u"入力"], res[u"束"][u"規則"], bad_def)
            res = CHK.check_files(specp, defp, good, os.path.join(tmp, "no_such_dir"))
            self.assertEqual(u"受理", res[u"束"][u"状態"])
            self.assertTrue(all(r[u"判定"] in (u"止める", u"無いを受ける") for r in res[u"材料"]))

    def test_i_9_huge_numbers_and_surrogates_inside_a_material(self):
        w = self.w()
        huge = u"9" * 30000
        b = self.edit(u"a01", lambda m: m.__setitem__(u"数値", huge))
        self.assertIn(u"K1", verdicts(check(w, b))[u"a01"][1])
        b = self.edit(u"a01", lambda m: m.__setitem__(u"数値", u"-" + huge))
        self.assertIn(u"K1", verdicts(check(w, b))[u"a01"][1])
        b = self.edit(u"a01", lambda m: m[u"出どころ"].__setitem__(u"行の見出し", u"\ud800売上高\udfff"))
        self.assertIn(u"K2", verdicts(check(w, b))[u"a01"][1])
        b = self.edit(u"a01", lambda m: m[u"出どころ"].__setitem__(u"file", u"\ud800"))
        self.assertIn(u"K1", verdicts(check(w, b))[u"a01"][1])
        # 巨大な数が計算の入力に入っても落ちない
        defn = w.defA
        rows = {u"a12": {u"状態": u"在る", u"値": huge * 3}, u"a13": {u"状態": u"在る", u"値": u"5"}}
        row = [r for r in defn.rows if r[u"id"] == u"a31"][0]
        self.assertEqual(u"在る", CHK.compute_row(row, rows)[u"状態"])
        row = [r for r in defn.rows if r[u"id"] == u"a32"][0]
        rows = {u"a15": {u"状態": u"在る", u"値": huge * 40}, u"a11": {u"状態": u"在る", u"値": u"3"}}
        self.assertIn(CHK.compute_row(row, rows)[u"状態"], (u"在る", u"無い"))

    def test_i_10_key_types_in_materials(self):
        for k in (u"状態", u"数値", u"単位", u"期間", u"範囲", u"出どころ"):
            self.refused(self.edit(u"a01", lambda m, k=k: m.pop(k)), None)
            self.refused(self.edit(u"a01", lambda m, k=k: m.__setitem__(k, 5)), None)
        for per in (od([(u"時点", u"2025-13-01")]), od([(u"始まり", u"2025-01-01")]), od([(u"始まり", u"2025-01-01"), (u"終わり", u"2025-12-31"), (u"時点", u"2025-12-31")]), u"2025", [], None, od([(u"時点", u"２０２５-12-31")])):
            self.refused(self.edit(u"a01", lambda m, per=per: m.__setitem__(u"期間", per)), u"期間")
        self.refused(self.edit(u"a01", lambda m: m[u"出どころ"].__setitem__(u"種類", u"素材の和")), u"出どころ")
        self.refused(self.edit(u"a01", lambda m: m[u"出どころ"].__setitem__(u"extra", 1)), u"出どころ")
        self.refused(self.edit(u"a01", lambda m: m.__setitem__(u"extra", 1)), u"在るの鍵")

    def test_i_11_the_kind_of_source_must_match_the_definition(self):
        w = self.w()
        b = self.edit(u"a29", lambda m: m.__setitem__(u"出どころ", copy.deepcopy([x for x in w.gold[u"材料"] if x[u"id"] == u"a30"][0][u"出どころ"])))
        v = verdicts(check(w, b))
        self.assertIn(u"K3", v[u"a29"][1])

    def test_i_12_cli_never_leaks_an_exception_for_broken_inputs(self):
        w = self.w()
        script = os.path.join(ROOT, CHECK_REL)
        env = {"PATH": os.environ.get("PATH", ""), "LANG": ""}
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "b.json")
            wbytes(bad, u'{"型の版":"u0","材料":[{"id":"\\ud800","状態":"無い","無い理由":"素材が無い"}]}'.encode("utf-8"))
            wbytes(os.path.join(tmp, "deep.json"), b"[" * 200000)
            for p in (bad, os.path.join(tmp, "deep.json"), os.path.join(tmp, "nonexistent.json")):
                rc = subprocess.run([sys.executable, "-I", script, "material", "--spec", os.path.join(w.src_dir, u"指定.json"), "--def", os.path.join(ROOT, DEF_RELS[0]), "--bundle", p, "--src", w.src_dir],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
                self.assertEqual(0, rc.returncode)
                self.assertEqual(b"", rc.stderr)
                out = json.loads(rc.stdout.decode("utf-8"))
                self.assertEqual(u"断り", out[u"束"][u"状態"])
                self.assertNotIn(u"内部の例外", out)


# ======================================================================== 8. 置き場・計算・B の計画・資料
def run_flow(w, bundleA=None, bseat=None):
    u"""A の置き場 → B の計画 → b01(正解か席の答え)→ B の置き場。戻りは (resA, storeA, plan, resB, storeB)。"""
    bundleA = bundleA or w.gold
    resA = check(w, bundleA)
    storeA = CHK.build_store(w.defA, resA, bundleA, u"A")
    plan = CHK.make_plan(w.defB, storeA)
    b = bseat or GEN.gold_bundle(w.co, [u"b01"])
    resB = CHK.check_bundle(w.spB, w.defB, b, w.src, ids=plan[u"新しく要る"])
    storeB = CHK.build_store(w.defB, resB, b, u"B", prior=storeA, ids=plan[u"新しく要る"])
    return resA, storeA, plan, resB, storeB


class StoreTest(unittest.TestCase):
    def test_j_1_store_rows_states_and_the_computed_rows(self):
        for i in DEV:
            w = dev_world(i)
            _ra, st, plan, _rb, _sb = run_flow(w)
            rows = st[u"行"]
            t5 = set(w.co.p["t5"])
            absent = set(GEN.absent_ids(w.co))
            for ident in CHK.material_ids(w.defA):
                s = rows[ident][u"状態"]
                if ident in t5:
                    self.assertEqual(u"確認待ち", s)
                    self.assertEqual([u"K3"], rows[ident][u"規則"])
                elif ident in absent:
                    self.assertEqual(u"無い", s)
                else:
                    self.assertEqual(u"在る", s)
                    self.assertEqual([m for m in w.gold[u"材料"] if m[u"id"] == ident][0][u"数値"], rows[ident][u"値"])
            self.assertEqual(u"A", rows[u"a01"][u"入った成果物"])
            # 計算: 独立に Fraction で
            from fractions import Fraction as F
            val = lambda k: F(int(rows[k][u"値"])) if rows[k][u"状態"] == u"在る" else None
            if rows[u"a12"][u"状態"] == u"在る" and rows[u"a13"][u"状態"] == u"在る":
                self.assertEqual(str(val(u"a12") + val(u"a13")), rows[u"a31"][u"値"])
            else:
                self.assertEqual(u"保留", rows[u"a31"][u"状態"])
            if rows[u"a15"][u"状態"] == u"在る" and rows[u"a11"][u"状態"] == u"在る":
                x = val(u"a15") / val(u"a11")
                want = (x * 10000 + F(1, 2)).__floor__() if x >= 0 else -((-x * 10000 + F(1, 2)).__floor__())
                self.assertEqual(F(want, 10000), F(rows[u"a32"][u"値"]))

    def test_j_2_plan_has_three_boxes_and_never_asks_again_for_a_waiting_row(self):
        for i in DEV:
            w = dev_world(i)
            _ra, st, plan, _rb, _sb = run_flow(w)
            self.assertEqual(16, len(plan[u"置き場に在る"]))
            self.assertEqual([u"b01"], plan[u"新しく要る"])
            self.assertEqual([u"b02", u"b03", u"b04"], plan[u"計算で作る"])
            self.assertEqual(sorted(plan[u"置き場に在る"]), plan[u"置き場に在る"])
        # 止まった行(確認待ち)は新しく要るに入らない: a04 を T5 並みに止めた束
        w = dev_world(101)
        b = copy.deepcopy(w.gold)
        for m in b[u"材料"]:
            if m[u"id"] == u"a04":
                m[u"数値"] = str(int(m[u"数値"]) + 1)
        _ra, st, plan, _rb, _sb = run_flow(w, bundleA=b)
        self.assertEqual(u"確認待ち", st[u"行"][u"a04"][u"状態"])
        self.assertIn(u"a04", plan[u"置き場に在る"])
        self.assertNotIn(u"a04", plan[u"新しく要る"])

    def test_j_3_rows_reused_in_b_keep_their_source_and_b_marks_are_added(self):
        w = dev_world(101)
        _ra, st, plan, _rb, sb = run_flow(w)
        rows = sb[u"行"]
        self.assertEqual(u"A", rows[u"a01"][u"入った成果物"])
        self.assertEqual([u"A", u"B"], rows[u"a01"][u"使われた成果物"])
        self.assertEqual(u"B", rows[u"b01"][u"入った成果物"])
        self.assertEqual([u"B"], rows[u"b01"][u"使われた成果物"])
        self.assertEqual(st[u"行"][u"a01"][u"出どころ"], rows[u"a01"][u"出どころ"])
        self.assertEqual([u"A"], st[u"行"][u"a09"][u"使われた成果物"])

    def test_j_4_computed_rows_state_rules(self):
        row = {u"id": u"x", u"式": u"和", u"入力": [u"p", u"q"], u"桁": 0, u"単位": u"円", u"範囲": u"全社"}
        ok = lambda v: {u"状態": u"在る", u"値": v}
        for rows, want in (({u"p": ok(u"1"), u"q": ok(u"2")}, (u"在る", u"3")),
                           ({u"p": {u"状態": u"無い"}, u"q": ok(u"2")}, (u"無い", None)),
                           ({u"p": {u"状態": u"確認待ち"}, u"q": ok(u"2")}, (u"保留", None)),
                           ({u"p": {u"状態": u"保留"}, u"q": ok(u"2")}, (u"保留", None)),
                           ({u"p": {u"状態": u"無い"}, u"q": {u"状態": u"確認待ち"}}, (u"無い", None)),
                           ({u"p": ok(u"1")}, (u"保留", None))):
            got = CHK.compute_row(row, rows)
            self.assertEqual(want[0], got[u"状態"], rows)
            if want[1] is not None:
                self.assertEqual(want[1], got[u"値"])
        self.assertEqual(u"入力の材料が無い", CHK.compute_row(row, {u"p": {u"状態": u"無い"}, u"q": ok(u"2")})[u"理由"])

    def test_j_5_computed_rounding_zero_and_formulas_by_hand(self):
        ok = lambda v: {u"状態": u"在る", u"値": v}
        def calc(f, ins, rows, places):
            return CHK.compute_row({u"id": u"x", u"式": f, u"入力": ins, u"桁": places, u"単位": u"純数", u"範囲": u"全社"}, rows)
        self.assertEqual(u"3", calc(u"比", [u"p", u"q"], {u"p": ok(u"5"), u"q": ok(u"2")}, 0)[u"値"])             # 2.5 → 3
        self.assertEqual(u"-3", calc(u"比", [u"p", u"q"], {u"p": ok(u"-5"), u"q": ok(u"2")}, 0)[u"値"])          # -2.5 → -3(0 から遠い側)
        self.assertEqual(u"0.1235", calc(u"比", [u"p", u"q"], {u"p": ok(u"12345"), u"q": ok(u"100000")}, 4)[u"値"])
        self.assertEqual(u"0", calc(u"比", [u"p", u"q"], {u"p": ok(u"-1"), u"q": ok(u"100000")}, 2)[u"値"].replace(u"0.00", u"0"))
        self.assertEqual(u"計算できない", calc(u"比", [u"p", u"q"], {u"p": ok(u"1"), u"q": ok(u"0")}, 2)[u"理由"])
        self.assertEqual(u"3.5", calc(u"比の分母和", [u"a", u"b", u"c"], {u"a": ok(u"7"), u"b": ok(u"1"), u"c": ok(u"1")}, 1)[u"値"])
        self.assertEqual(u"計算できない", calc(u"比の分母和", [u"a", u"b", u"c"], {u"a": ok(u"7"), u"b": ok(u"1"), u"c": ok(u"-1")}, 1)[u"理由"])      # 分母 0
        self.assertEqual(u"計算できない", calc(u"比の分母和", [u"a", u"b", u"c"], {u"a": ok(u"7"), u"b": ok(u"-3"), u"c": ok(u"1")}, 1)[u"理由"])      # 分母が負
        self.assertEqual(u"0.2500", calc(u"増減率", [u"a", u"b"], {u"a": ok(u"125"), u"b": ok(u"100")}, 4)[u"値"])
        self.assertEqual(u"-0.5000", calc(u"増減率", [u"a", u"b"], {u"a": ok(u"50"), u"b": ok(u"100")}, 4)[u"値"])
        self.assertEqual(u"計算できない", calc(u"増減率", [u"a", u"b"], {u"a": ok(u"50"), u"b": ok(u"0")}, 4)[u"理由"])
        self.assertEqual(u"計算できない", calc(u"未知の式", [u"a", u"b"], {u"a": ok(u"50"), u"b": ok(u"1")}, 4)[u"理由"])
        self.assertEqual(u"計算できない", CHK.compute_row({u"id": u"x", u"式": u"和", u"入力": u"ab"}, {})[u"理由"])


class DocumentTest(unittest.TestCase):
    def docs(self, w):
        _ra, stA, plan, _rb, stB = run_flow(w)
        return stA, stB, CHK.render_doc(w.defA, stA), CHK.render_doc(w.defB, stB)

    def test_k_1_the_rendered_documents_pass_the_document_check(self):
        for i in DEV:
            w = dev_world(i)
            stA, stB, docA, docB = self.docs(w)
            for d, st, text in ((w.defA, stA, docA), (w.defB, stB, docB)):
                res = CHK.check_document(d, st, text)
                self.assertEqual({u"通った": True, u"赤": [], u"札の数": len(d.rows), u"結ばれていない数": 0, u"語の食い違い": 0}, res)

    def test_k_2_the_tag_format_follows_the_seal_examples(self):
        w = dev_world(101)
        stA, stB, docA, docB = self.docs(w)
        self.assertRegex(docA, u"月次売上高\\(当期の一か月目\\): [0-9,]+百万円\\[材料:a17\\]")
        self.assertRegex(docA, u"期末の従業員数\\(当期末\\): [0-9,]+人\\[材料:a30\\]")
        self.assertRegex(docA, u"自己資本比率: -?[0-9]+\\.[0-9]%\\[材料:a32\\]")
        self.assertIn(u"確認待ち[材料:a03]", docA)                    # 101 は a03 が表の外
        self.assertIn(u"確認待ち[材料:a31]", docA)                    # a12 が確認待ちなので計算は保留
        w2 = dev_world(102)
        stA2, _sb2, docA2, _d2 = self.docs(w2)
        self.assertIn(u"無い[材料:a30]", docA2)
        self.assertRegex(docB, u"一人当たり売上: [0-9,]+円\\[材料:b04\\]")

    def test_k_3_numbers_are_the_store_values_divided_and_rounded_by_hand(self):
        w = dev_world(103)
        stA, _sb, docA, _d = self.docs(w)
        for ident, div in ((u"a01", 1000000), (u"a04", 1000000), (u"a17", 1000000)):
            v = int(stA[u"行"][ident][u"値"])
            n = (v + div // 2) // div if v >= 0 else -((-v + div // 2) // div)
            self.assertIn(u"%s百万円[材料:%s]" % (u"{:,}".format(n), ident), docA)

    def test_k_4_document_mutations_and_the_document_rules_one_by_one(self):
        total = collections.Counter()
        made = collections.Counter()
        mapping = {u"D1": u"C2", u"D2": u"C2", u"D3": u"C2", u"D5": u"C3"}
        for i in DEV:
            w = dev_world(i)
            stA, stB, docA, docB = self.docs(w)
            for d, st, text in ((w.defA, stA, docA), (w.defB, stB, docB)):
                units = dict((r[u"id"], r[u"単位"]) for r in d.rows)
                for code, k, new in GEN.doc_mutants(text, units):
                    if new is None:
                        continue
                    self.assertNotEqual(text, new)
                    made[code] += 1
                    if CHK.check_document(d, st, new)[u"通った"]:
                        total[code] += 1
        for code in GEN.DOC_CODES:
            self.assertGreater(made[code], 0, code)
        self.assertEqual({}, dict(total))

    def test_k_5_each_document_rule_removed_lets_its_mutation_through(self):
        w = dev_world(102)
        stA, stB, docA, docB = self.docs(w)
        def passes(rule_to_remove, codes, extra_texts=()):
            n = collections.Counter()
            with doc_removed(rule_to_remove):
                for code, k, new in GEN.doc_mutants(docA, dict((r[u"id"], r[u"単位"]) for r in w.defA.rows)):
                    if new is not None and code in codes and CHK.check_document(w.defA, stA, new)[u"通った"]:
                        n[code] += 1
                for name, text in extra_texts:
                    if CHK.check_document(w.defA, stA, text)[u"通った"]:
                        n[name] += 1
            return n
        extra = [(u"E1", docA + u"\n売上は約3割増えた。\n"), (u"E2", docA + u"\n- 余分: 1百万円[材料:z99]\n")]
        self.assertEqual(0, passes(u"C2", (), extra)[u"E1"])
        self.assertGreater(passes(u"C2", (u"D1", u"D2", u"D3"))[u"D1"], 0)
        self.assertGreater(passes(u"C2", (u"D1", u"D2", u"D3"))[u"D2"], 0)
        self.assertGreater(passes(u"C2", (u"D1", u"D2", u"D3"))[u"D3"], 0)
        self.assertGreater(passes(u"C3", (u"D5",))[u"D5"], 0)
        self.assertGreater(passes(u"C4", (), extra)[u"E1"], 0)
        self.assertGreater(passes(u"C1", (u"D4",), extra)[u"D4"], 0)
        self.assertGreater(passes(u"C1", (), extra)[u"E2"], 0)
        # 自分の規則を外さなければ通さない
        self.assertEqual({}, dict((k, v) for k, v in passes(u"C3", (u"D1", u"D2", u"D3", u"D4"), extra).items()))

    def test_k_6_hand_made_red_cases(self):
        w = dev_world(102)
        stA, _sb, docA, _d = self.docs(w)
        cases = {
            u"在るでない行に数": docA.replace(u"無い[材料:a30]", u"45人[材料:a30]"),
            u"在る行に語": docA.replace(u"[材料:a01]", u"[材料:a01]").replace(re.search(u"[0-9,]+百万円\\[材料:a01\\]", docA).group(0), u"無い[材料:a01]"),
            u"単位の字": re.sub(u"([0-9,]+)百万円\\[材料:a01\\]", u"\\1人[材料:a01]", docA),
            u"小数の桁": re.sub(u"(-?[0-9]+)\\.([0-9])%\\[材料:a32\\]", u"\\1.\\g<2>0%[材料:a32]", docA),
            u"札が無い行": docA.replace(u"[材料:a16]", u""),
            u"結ばれていない数": docA + u"\n来期は3割増を見込む。\n",
            u"定義表に無い札": docA + u"\n- x: 1百万円[材料:z9]\n",
            u"札の前に数も語も無い": docA + u"\n- x: 売上[材料:a01]\n",
        }
        for kind, text in cases.items():
            res = CHK.check_document(w.defA, stA, text)
            self.assertFalse(res[u"通った"], kind)
            self.assertIn(kind, [r[u"種類"] for r in res[u"赤"]], (kind, res[u"赤"]))
        self.assertTrue(CHK.check_document(w.defA, stA, docA).get(u"通った"))

    def test_k_7_free_number_rule_skips_dates_and_heading_numbers_only(self):
        w = dev_world(102)
        stA, _sb, docA, _d = self.docs(w)
        ok = docA + u"\n2026年3月期の状況。2026年3月31日現在。2026-03-31。2026/03。3月。\n"
        self.assertTrue(CHK.check_document(w.defA, stA, ok)[u"通った"])
        ok2 = u"# 1 概況\n\n## 2 数値\n\n1. 売上\n" + docA.split(u"\n", 1)[1]
        self.assertTrue(CHK.check_document(w.defA, stA, ok2)[u"通った"])
        res = CHK.check_document(w.defA, stA, docA + u"\n約 3 割と 12.5 と 1,234。\n")
        self.assertEqual(3, res[u"結ばれていない数"])
        res = CHK.check_document(w.defA, stA, docA + u"\n１２３\n")
        self.assertEqual(1, res[u"結ばれていない数"])

    def test_k_8_word_mismatch_is_counted_not_red(self):
        w = dev_world(102)
        stA, _sb, docA, _d = self.docs(w)
        res = CHK.check_document(w.defA, stA, docA.replace(u"無い[材料:a30]", u"確認待ち[材料:a30]"))
        self.assertTrue(res[u"通った"])
        self.assertEqual(1, res[u"語の食い違い"])

    def test_k_9_degenerate_documents_do_not_raise(self):
        w = dev_world(101)
        _ra, st, plan, _rb, sb = run_flow(w)
        for text in (u"", u"\n", u"[材料:", u"[材料:]", u"無い[材料:a01]" * 3, u"\ud800", u"９９９百万円[材料:a01]", u"1百万円[材料:a01" * 100, None, 5, b"x"):
            res = CHK.check_document(w.defA, st, text)
            self.assertFalse(res[u"通った"])
        for store in (None, {}, {u"行": None}, {u"行": {u"a01": None}}, {u"行": {u"a01": {u"状態": u"在る"}}}, {u"行": {u"a01": {u"状態": u"在る", u"値": u"x"}}}, []):
            res = CHK.check_document(w.defA, store, u"1百万円[材料:a01]\n")
            self.assertFalse(res[u"通った"])
        self.assertEqual(u"確認待ち", CHK.render_doc(w.defA, {u"行": {}}).split(u"\n")[4].split(u": ")[1].split(u"[")[0])


class RenderCommandTest(unittest.TestCase):
    def test_l_1_the_commands_chain_through_files_in_isolated_processes(self):
        w = dev_world(102)
        script = os.path.join(ROOT, CHECK_REL)
        env = {"PATH": os.environ.get("PATH", ""), "LANG": ""}
        d = os.path.join(w.tmp, "chain")
        os.makedirs(d, exist_ok=True)
        wjson(os.path.join(d, "gold.json"), w.gold)
        wjson(os.path.join(d, "goldB.json"), GEN.gold_bundle(w.co, [u"b01"]))
        defA, defB = [os.path.join(ROOT, r) for r in DEF_RELS]
        specA, specB = os.path.join(w.src_dir, u"指定.json"), os.path.join(d, u"指定B.json")
        wjson(specB, GEN.spec_json(w.co, u"B"))
        def run(*a):
            rc = subprocess.run([sys.executable, "-I", script] + list(a), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            self.assertEqual(0, rc.returncode, a)
            self.assertEqual(b"", rc.stderr)
            return rc
        run("material", "--spec", specA, "--def", defA, "--bundle", os.path.join(d, "gold.json"), "--src", w.src_dir, "--out", os.path.join(d, "resA.json"))
        run("store", "--def", defA, "--result", os.path.join(d, "resA.json"), "--bundle", os.path.join(d, "gold.json"), "--product", "A", "--out", os.path.join(d, "storeA.json"))
        run("plan", "--def", defB, "--store", os.path.join(d, "storeA.json"), "--out", os.path.join(d, "plan.json"))
        plan = json.load(io.open(os.path.join(d, "plan.json"), encoding="utf-8"))
        self.assertEqual([u"b01"], plan[u"新しく要る"])
        run("material", "--spec", specB, "--def", defB, "--bundle", os.path.join(d, "goldB.json"), "--src", w.src_dir, "--ids", u",".join(plan[u"新しく要る"]), "--out", os.path.join(d, "resB.json"))
        resB = json.load(io.open(os.path.join(d, "resB.json"), encoding="utf-8"))
        self.assertEqual([(u"b01", u"通す")], [(r[u"id"], r[u"判定"]) for r in resB[u"材料"]])
        run("store", "--def", defB, "--result", os.path.join(d, "resB.json"), "--bundle", os.path.join(d, "goldB.json"), "--product", "B", "--prior", os.path.join(d, "storeA.json"),
            "--ids", u",".join(plan[u"新しく要る"]), "--out", os.path.join(d, "storeB.json"))
        run("render", "--def", defB, "--store", os.path.join(d, "storeB.json"), "--out", os.path.join(d, "docB.md"))
        run("document", "--def", defB, "--store", os.path.join(d, "storeB.json"), "--doc", os.path.join(d, "docB.md"), "--out", os.path.join(d, "docB.json"))
        out = json.load(io.open(os.path.join(d, "docB.json"), encoding="utf-8"))
        self.assertTrue(out[u"通った"], out)
        stB = json.load(io.open(os.path.join(d, "storeB.json"), encoding="utf-8"))
        self.assertEqual(u"在る", stB[u"行"][u"b01"][u"状態"])
        # 同じ道を中でやった結果と同じ
        _ra, _sa, _p, _rb, sb = run_flow(w)
        self.assertEqual(json.loads(json.dumps(sb, ensure_ascii=False)), stB)


# ======================================================================== 9. 指示書
class InstructionTest(unittest.TestCase):
    def test_m_1_the_instruction_has_two_chapters_and_the_example_is_the_real_dev_line(self):
        body = read(INSTRUCTION_REL)
        self.assertIn(u"## 章 1 材料を書く席", body)
        self.assertIn(u"## 章 2 資料を書く席", body)
        lines = [ln for ln in body.splitlines() if ln.startswith(u"{\"id\": \"a01\"")]
        self.assertEqual(1, len(lines))
        self.assertEqual(json.loads(json.dumps(GEN.gold_material(GEN.build(101), u"a01"), ensure_ascii=False)), json.loads(lines[0]))
        self.assertEqual(1, len(re.findall(u"^\\{\"id\"", body, re.M)))            # 実物の 1 行は 1 つだけ

    def test_m_2_the_instruction_has_no_rule_names_trap_kinds_predictions_or_outside_words(self):
        body = read(INSTRUCTION_REL)
        for pat in (u"(?<![A-Za-z0-9])K[0-9](?![0-9])", u"(?<![A-Za-z0-9])C[1-4](?![0-9])", u"(?<![A-Za-z0-9])M[0-9]+(?![0-9])", u"(?<![A-Za-z0-9])D[1-5](?![0-9])", u"(?<![A-Za-z0-9])T[0-9]+(?![0-9])"):
            self.assertIsNone(re.search(pat, body), pat)
        for word in (u"罠", u"予測", u"表の外", u"UM0", u"外れ", u"封", u"検査の規則", u"正解", u"司令塔", u"作り物"):
            self.assertNotIn(word, body, word)
        for _i, (_t, outs) in EXPECT_TABLE.items():
            for w in outs:
                self.assertNotIn(w, body, w)

    def test_m_3_the_instruction_names_every_key_of_the_type_and_the_escape_for_unmatched_headings(self):
        body = read(INSTRUCTION_REL)
        for key in (u"型の版", u"材料", u"id", u"状態", u"数値", u"単位", u"期間", u"範囲", u"出どころ", u"無い理由", u"素材が無い", u"種類", u"file", u"位置", u"行の見出し", u"列の見出し", u"表示の倍率",
                    u"行の並び", u"時点", u"始まり", u"終わり", u"sheet", u"セル", u"素材の和", u"当期の月:k", u"[材料:<id>]", u"確認待ち"):
            self.assertIn(key, body, key)
        self.assertIn(u"意味が合うと判断した行は、その素材の位置と見出しをそのまま書く", body)
        self.assertIn(u"黙って別の行の数で埋めない", body)
        self.assertIn(u"渡された folder の外は読まない", body)
        self.assertIn(u"置き場に無い数を書かない", body)
        self.assertIn(u"札の無い数字", body)

    def test_m_4_the_example_in_the_instruction_passes_the_check_as_written(self):
        w = dev_world(101)
        body = read(INSTRUCTION_REL)
        line = [ln for ln in body.splitlines() if ln.startswith(u"{\"id\": \"a01\"")][0]
        m = json.loads(line, object_pairs_hook=od)
        b = copy.deepcopy(w.gold)
        b[u"材料"] = [m if x[u"id"] == u"a01" else x for x in b[u"材料"]]
        self.assertEqual(u"通す", verdicts(check(w, b))[u"a01"][0])


# ======================================================================== 10. 段 B・C の集計(席の代わりに作った出力で)
class TallyTest(unittest.TestCase):
    def seat_dir(self, tmp, perfect=True):
        for i in DEV:
            w = dev_world(i)
            d = os.path.join(tmp, str(i))
            wjson(os.path.join(d, u"材料_A.json"), w.gold)
            wjson(os.path.join(d, u"材料_B.json"), GEN.gold_bundle(w.co, [u"b01"]))
            _ra, stA, plan, _rb, _sb = run_flow(w)
            wbytes(os.path.join(d, u"資料_A.md"), CHK.render_doc(w.defA, stA).encode("utf-8"))

    def test_n_1_the_stage_b_and_c_tally_with_a_perfect_seat(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.seat_dir(tmp)
            res = GEN.tally_bc(DEV, tmp, CHK)
        c = res[u"数"]
        self.assertEqual(3, c[u"A の資料を通した"])
        self.assertEqual(3, c[u"B の資料を通した"])
        self.assertEqual(3, c[u"b01 の席の答えが正解どおり"])
        self.assertEqual(0, c.get(u"束が K0 で断られた社", 0))
        self.assertEqual(3 * 16, c[u"B の計画:置き場に在る"])
        self.assertEqual(3, c[u"B の計画:新しく要る"])
        self.assertEqual(9, c[u"B の計画:計算で作る"])
        boxes = res[u"4 つの枠"]
        self.assertEqual({u"正解どおり×通した": 83 + 1, u"正解どおり×止めた": 6, u"正解と違う×通した": 0, u"正解と違う×止めた": 0}, dict(boxes))
        self.assertEqual(c[u"表に無い言い方の行"], c[u"表に無い言い方の行で席が正解どおり"])
        self.assertEqual(6, c[u"表に無い言い方の行"])
        self.assertEqual(1, c[u"無いの行"])
        self.assertEqual(1, c[u"無いの行で席が無いと書いた"])
        self.assertEqual(0, c[u"通したが数値が違う"])
        self.assertEqual(0, c[u"位置は違うが通り数値は同じ"])
        self.assertEqual(0, sum(v for k, v in c.items() if k.startswith(u"資料の変異:") and k.endswith(u":通した")))
        self.assertEqual(0, sum(v for k, v in c.items() if k.startswith(u"資料の変異:") and k.endswith(u":通した:B")))
        for code in GEN.DOC_CODES:
            self.assertGreater(c[u"資料の変異:%s:作れた" % code], 0)

    def test_n_2_a_wrong_seat_is_counted_as_wrong(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.seat_dir(tmp)
            w = dev_world(101)
            b = copy.deepcopy(w.gold)
            for m in b[u"材料"]:
                if m[u"id"] == u"a30":
                    m[u"数値"] = str(int(m[u"数値"]) + 1)
                if m[u"id"] == u"a17":      # 位置が違い、数値も別の月の値に合わせた
                    m[u"出どころ"][u"位置"] = od([(u"行", 3), (u"列", 2)])
                    m[u"数値"] = [x for x in w.gold[u"材料"] if x[u"id"] == u"a18"][0][u"数値"]
            wjson(os.path.join(tmp, u"101", u"材料_A.json"), b)
            wbytes(os.path.join(tmp, u"102", u"材料_A.json"), J(u"{"))             # 束が壊れた社
            os.remove(os.path.join(tmp, u"103", u"資料_A.md"))
            res = GEN.tally_bc(DEV, tmp, CHK)
        c = res[u"数"]
        self.assertEqual(1, c[u"束が K0 で断られた社"])
        self.assertEqual(0, c[u"席の出力なし"])
        self.assertEqual(2 + 30, res[u"4 つの枠"][u"正解と違う×止めた"])
        self.assertEqual(0, res[u"4 つの枠"][u"正解と違う×通した"])
        self.assertEqual(0, c[u"A の資料を通した"])          # 101 は置き場が違い、102 は束が断られ、103 は資料が無い
        self.assertEqual(1, c[u"A の資料なし"])
        self.assertEqual(0, c[u"通したが数値が違う"])

    def test_n_3_a_missing_seat_directory_counts_and_does_not_raise(self):
        res = GEN.tally_bc(DEV, os.path.join(tempfile.gettempdir(), "um0_no_such_dir_x"), CHK)
        self.assertEqual(3, res[u"数"][u"席の出力なし"])

    def test_n_4_the_stage_a_tally_has_the_documented_shape_and_no_forbidden_words(self):
        res = GEN.tally_a(DEV, CHK)
        body = json.dumps(res, ensure_ascii=False)
        for _i, (t, outs) in EXPECT_TABLE.items():
            for w in t + outs:
                self.assertNotIn(w, body, w)
        for name in (u"決算.xlsx", u"月次売上.csv", u"借入金一覧.csv", u"人員.csv", u"定義", u"指定.json"):
            self.assertNotIn(name, body)
        self.assertEqual(set(u"M%d" % k for k in range(1, 12)) | set(GEN.X_CODES), set(res[u"変異"]))
        for code, row in res[u"変異"].items():
            for k in row:
                self.assertRegex(k, u"^(作れた|作れなかった|断った|止めた|通した|形だけの検査が通した|規則:K[0-9](\\+K[0-9])*)$")

    def test_n_5_stage_a_rows_by_code_for_the_dev_companies(self):
        res = GEN.tally_a(DEV, CHK)[u"変異"]
        for code in GEN.MUT_CODES:
            row = res[code]
            self.assertEqual(row[u"作れた"], row.get(u"断った", 0) + row.get(u"止めた", 0) + row.get(u"通した", 0), code)
            if code != u"M8":
                self.assertEqual(0, row.get(u"通した", 0), code)
        self.assertEqual(6, res[u"M8"][u"通した"])
        for code in GEN.MUT_CODES:
            self.assertEqual(res[code][u"作れた"], res[code].get(u"形だけの検査が通した", 0), code)       # UM0-A3 の形
        self.assertEqual(89, res[u"M1"][u"作れた"])
        self.assertEqual(1, res[u"M9"][u"作れた"])
        self.assertEqual(3, res[u"M11"][u"作れた"])
        self.assertEqual(res[u"X0"][u"作れた"], res[u"X0"][u"断った"])


# ======================================================================== 11. 記録・順序・門自身
FORBIDDEN_IN_RECORD = [w for _i, (t, o) in EXPECT_TABLE.items() for w in (t + o)] + [u"決算.xlsx", u"月次売上.csv", u"借入金一覧.csv", u"人員.csv", u"北辰銀行", u"東和信金", u"東日本事業部"]


def record_problems(rec, companies=None):
    companies = GEN.PROD if companies is None else companies
    out = []
    body = json.dumps(rec, ensure_ascii=False)
    for w in FORBIDDEN_IN_RECORD:
        if w in body:
            out.append(u"記録に禁止の字: " + w)
    if not isinstance(rec, dict) or set(rec) != {u"段 A", u"段 B・C"}:
        out.append(u"記録の頂の鍵")
        return out
    a = rec[u"段 A"]
    if set(a) != {u"会社ごと", u"合計", u"変異"}:
        out.append(u"段 A の鍵")
    else:
        if set(a[u"会社ごと"]) != set(str(i) for i in companies):
            out.append(u"段 A の会社が 1〜12 でない")
        else:
            tot = collections.Counter()
            for i, row in a[u"会社ごと"].items():
                for k in (u"通す", u"止める", u"無いを受ける", u"束ごとの断り"):
                    tot[k] += row[k]
            if dict(tot) != a[u"合計"]:
                out.append(u"段 A の合計が会社ごとの足しと違う")
    if re.search(u"[0-9]{6,}", body):
        out.append(u"記録に長い数(値)がある")
    return out


class RecordTest(unittest.TestCase):
    def test_o_1_the_record_state_is_stated_and_checked(self):
        path = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(path):
            self.assertFalse(os.path.exists(path), u"記録はまだ無い(本番は未実行。記録の無い状態で緑)")
            return
        rec = json.loads(read(RECORD_REL))
        self.assertEqual([], record_problems(rec))

    def test_o_2_the_record_check_turns_red_for_a_forbidden_word_a_value_and_a_wrong_total(self):
        good = {u"段 A": {u"会社ごと": dict((str(i), {u"通す": 1, u"止める": 0, u"無いを受ける": 0, u"束ごとの断り": 0}) for i in GEN.PROD),
                          u"合計": {u"通す": 12, u"止める": 0, u"無いを受ける": 0, u"束ごとの断り": 0}, u"変異": {}}, u"段 B・C": {}}
        self.assertEqual([], record_problems(good))
        bad = copy.deepcopy(good)
        bad[u"段 B・C"][u"x"] = u"売上高"
        self.assertNotEqual([], record_problems(bad))
        bad = copy.deepcopy(good)
        bad[u"段 B・C"][u"x"] = 12345678
        self.assertNotEqual([], record_problems(bad))
        bad = copy.deepcopy(good)
        bad[u"段 A"][u"合計"][u"通す"] = 11
        self.assertNotEqual([], record_problems(bad))
        bad = copy.deepcopy(good)
        del bad[u"段 A"][u"会社ごと"]["12"]
        self.assertNotEqual([], record_problems(bad))
        self.assertNotEqual([], record_problems({}))

    def test_o_2b_the_record_the_script_builds_has_the_shape_and_no_forbidden_word_on_the_dev_companies(self):
        with tempfile.TemporaryDirectory() as tmp:
            TallyTest().seat_dir(tmp)
            rec = json.loads(json.dumps(GEN.build_record(DEV, tmp, CHK), ensure_ascii=False))
        self.assertEqual([], record_problems(rec, DEV))
        self.assertEqual(set(["段 A", "段 B・C"]), set(rec))
        self.assertEqual(set(["会社ごと", "合計", "変異"]), set(rec[u"段 A"]))
        self.assertEqual(set(["会社ごと", "数", "4 つの枠"]), set(rec[u"段 B・C"]))
        self.assertNotEqual([], record_problems(rec))                # 12 社そろっていない記録は本番の形として赤

    def test_o_3_the_record_command_is_never_run_here_and_writes_nothing_without_the_seat_directory(self):
        self.assertFalse(os.path.exists(os.path.join(ROOT, RECORD_REL)) and not os.path.isfile(os.path.join(ROOT, RECORD_REL)))


def make_repo(files_by_commit, root):
    u"""作り物の git repo(順序の部品の試し用)。``files_by_commit`` は [(題, {rel: 字})]。"""
    subprocess.run(["git", "init", "-q", root], check=True)
    for k, (msg, files) in enumerate(files_by_commit):
        for rel, body in files.items():
            wbytes(os.path.join(root, rel), body.encode("utf-8"))
        subprocess.run(["git", "-C", root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg], check=True)


def order_problems_allowing_not_yet(root, seal_short, files):
    u"""未 commit の file(まだ無い)は許す。commit されている file は、封の commit より後・HEAD の中であること。封の履歴の問題はそのまま返す。"""
    got = PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], files)
    return [x for x in got if not x.startswith(u"UNCOMMITTED:")]


class OrderTest(unittest.TestCase):
    def test_p_1_the_real_history_has_the_seal_before_the_scripts_definitions_instruction_and_the_gate(self):
        u"""どれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。記録は別。"""
        self.assertEqual([], order_problems_allowing_not_yet(REPO, SEAL_COMMIT_SHORT, list(ORDER_FILES)))

    def test_p_2_the_order_check_lists_every_file_and_not_the_record(self):
        self.assertEqual(6, len(ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)
        for rel in ORDER_FILES:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_p_3_the_order_part_turns_red_when_a_file_comes_before_the_seal_or_is_missing(self):
        seal = PREFIX + SEAL_REL
        other = PREFIX + GEN_REL
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("pre", {other: "x"}), ("seal-x", {seal: "s"}), ("later", {PREFIX + "b": "y"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            got = PR.order_problems(tmp, PREFIX, SEAL_REL, short, [], [GEN_REL, "b", "missing.py"])
            self.assertIn(u"BEFORE_SEAL:" + GEN_REL, got)
            self.assertIn(u"UNCOMMITTED:missing.py", got)
            self.assertNotIn(u"BEFORE_SEAL:b", got)
            allowed = order_problems_allowing_not_yet(tmp, short, [GEN_REL, "b", "missing.py"])
            self.assertIn(u"BEFORE_SEAL:" + GEN_REL, allowed)
            self.assertNotIn(u"UNCOMMITTED:missing.py", allowed)
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("seal-x", {seal: "s"}), ("later", {other: "y"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            self.assertEqual([], list(PR.order_problems(tmp, PREFIX, SEAL_REL, short, [], [GEN_REL])))


class HygieneTest(unittest.TestCase):
    def test_q_1_the_new_files_do_not_contain_the_harness_words(self):
        words = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(", "tampered", u"注入")
        for rel in (GEN_REL, CHECK_REL):
            body = read(rel)
            for w in words:
                self.assertNotIn(w, body, (rel, w))

    def test_q_2_the_gate_makes_no_material_for_the_production_companies(self):
        tree = ast.parse(read(GATE_REL))
        names = set(n.id for n in ast.walk(tree) if isinstance(n, ast.Name))
        attrs = set(n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute))
        self.assertNotIn(u"PROD", names)
        # 素材・正解を作る関数は ``dev_world``(開発の 3 社以外は例外)か、``DEV`` / 開発の会社の ``co`` だけで呼ぶ
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("build", "write_files") and isinstance(node.func.value, ast.Name) and node.func.value.id == "GEN":
                for arg in node.args[:1]:
                    if isinstance(arg, ast.Constant):
                        self.assertIn(arg.value, DEV, ast.dump(arg))
                    else:
                        self.assertIn(type(arg).__name__, ("Name", "Attribute"), ast.dump(arg))
        with self.assertRaises(AssertionError):
            dev_world(1)
        with self.assertRaises(AssertionError):
            dev_world(12)

    def test_q_3_the_gate_has_the_expected_class_names_and_no_skip(self):
        body = read(GATE_REL)
        self.assertNotIn(u"skip" + u"Test", body)
        self.assertNotIn(u"@unittest." + u"skip", body)
        self.assertNotIn(u"pytest.mark." + u"skip", body)

    def test_q_4_no_file_outside_the_declared_folders_is_written_by_the_scripts(self):
        self.assertTrue(os.path.isdir(os.path.join(ROOT, "fixtures", "universal", "um0")))
        self.assertEqual([u"definition_A.json", u"definition_B.json"] + ([u"record.json"] if os.path.exists(os.path.join(ROOT, RECORD_REL)) else []),
                         sorted(os.listdir(os.path.join(ROOT, "fixtures", "universal", "um0")), key=lambda x: (x == u"record.json", x)))


if __name__ == "__main__":
    unittest.main()
