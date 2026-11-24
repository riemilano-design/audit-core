# -*- coding: utf-8 -*-
u"""封 docs/UNIVERSAL_PROCESS_SEAL_2026-11-24.md(UM3 ― 便 UM2 と同じ素材を、型も検査も持たない AI の席に資料まで作らせ、作る過程を並べる)の封の門。

**この門が作る素材は、この file の中で tmp に組む架空の 2 社(101・102)だけ。** 本番の 1〜4 は作らない・読まない。席(subagent)は呼ばない。API・鍵・通信は使わない。
便 UM0・UM1・UM2 の file・engine は封の commit から 0 行(``git diff``)・作業の木でも変わっていない(``git status``)。

**縛るもの**

1. 封と頼みの紙の字(sha256)・封と頼みの紙は同じ commit・engine と便 UM0・UM2 の file が 0 行・順序(封 → script → 門。未 commit の間は「未 commit」と分かる形で通す)。
2. script は ``python3 -I``・標準 library だけ・どんな入力でも落ちない(rc が整数で traceback を出さない)・scratchpad の path を字で持たない。
3. 予測 16 本の境(表の字と BOUNDS が同じ・境の 1 つ下と 1 つ上で当たり外れが変わる)。
4. 行ごとの結果の名 8 つ・計算の 3 行・関係・B との掛け合わせ(社・回・期・id の鍵)・揺れ・自信・資料の数の字が、手で決めた数と同じ(作り物の 2 社 × 2 回 × 2 期)。
5. 過程の数(席と記録の対応・汚れ・書き直し・script・2 期目の持ち越し)が、手で作った会話の記録の数と同じ。「過程が数えられない」・「答えなし」。
6. ``--hand`` が folder を作り、正解・作り方・便 UM2 の頼み.md を出す先に置かない。
7. 記録が持ってはいけない字(file の名・日付・額の形・科目の字)・記録の形・本番の 4 社がそろわない時は書かない。

**封が決めていなかった読み**は script の docstring に書いた(結果の文書に書く)。
"""
import ast
import collections
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
from fractions import Fraction

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


SEAL_REL = "docs/UNIVERSAL_PROCESS_SEAL_2026-11-24.md"
BRIEF_REL = "docs/UNIVERSAL_PROCESS_BRIEF_2026-11-24.md"
SEAL_COMMIT_SHORT = "6c4457fe"
SEAL_SHA256 = "40ec5672357e952411736be137551c43c7f7da0075cd1eca8532899eb2160ca4"
BRIEF_SHA256 = "76aaa2077cf7d3b726b8f05617e23ee6024b0d6b8926685192dbac188347ded8"
TALLY_REL = "measure/universal_process_tally_2026-11-24.py"
GATE_REL = "tests/measure/test_universal_process_seal.py"
RECORD_REL = "fixtures/universal/um3/record.json"
ORDER_FILES = (TALLY_REL, GATE_REL)
#: 便 UM0・UM2 の file(封の commit に在ったもの。0 行でなければならない)
PRIOR_FILES = (
    "docs/UNIVERSAL_MATERIAL_INSTRUCTION_2026-11-23.md", "docs/UNIVERSAL_MATERIAL_RESULT_2026-11-23.md", "docs/UNIVERSAL_MATERIAL_SEAL_2026-11-23.md",
    "docs/UNIVERSAL_MATERIAL_THIRD_PARTY_SOURCE_PRESEAL_2026-11-23.md", "docs/UNIVERSAL_MATERIAL_THIRD_PARTY_SOURCE_SEAL_2026-11-23.md",
    "docs/UNIVERSAL_THROUGH_INSTRUCTION_2026-11-23.md", "docs/UNIVERSAL_THROUGH_RESULT_2026-11-24.md", "docs/UNIVERSAL_THROUGH_SEAL_2026-11-23.md",
    "docs/UNIVERSAL_THROUGH_SOURCE_BRIEF_2026-11-23.md",
    "fixtures/universal/um0/definition_A.json", "fixtures/universal/um0/definition_B.json", "fixtures/universal/um0/record.json", "fixtures/universal/um2/record.json",
    "measure/universal_check_2026-11-23.py", "measure/universal_source_gen_2026-11-23.py", "measure/universal_through_check_2026-11-23.py",
    "measure/universal_through_tally_2026-11-23.py",
    "tests/measure/test_universal_material_result.py", "tests/measure/test_universal_material_seal.py", "tests/measure/test_universal_through_result.py",
    "tests/measure/test_universal_through_seal.py",
)
TAL = load_module(TALLY_REL, "um3_tally_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_um3_seal_gate")      # 順序の部品。門としては走らせない


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def read_bytes(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return fh.read()


def git(*args):
    return subprocess.run(["git", "-C", REPO] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode("utf-8")


def wtext(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def wjson(path, obj):
    wtext(path, json.dumps(obj, ensure_ascii=False))


def wbytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def run_cli(args, cwd=None):
    r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, TALLY_REL)] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


# ======================================================================== 1. 封の字・順序
class SealTextTest(unittest.TestCase):
    def test_a_1_the_seal_and_the_brief_are_the_sealed_bytes(self):
        self.assertEqual(SEAL_SHA256, hashlib.sha256(read_bytes(SEAL_REL)).hexdigest())
        self.assertEqual(BRIEF_SHA256, hashlib.sha256(read_bytes(BRIEF_REL)).hexdigest())

    def test_a_2_the_seal_and_the_brief_are_one_commit_and_unchanged(self):
        for rel in (SEAL_REL, BRIEF_REL):
            hs = [x for x in git("log", "--format=%H", "--", PREFIX + rel).split() if x]
            self.assertEqual(1, len(hs), (rel, hs))
            self.assertTrue(hs[0].startswith(SEAL_COMMIT_SHORT), (rel, hs))
            blob = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (hs[0], PREFIX + rel)], stdout=subprocess.PIPE).stdout
            self.assertEqual(blob, read_bytes(rel))

    def test_a_3_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual("", git("diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core").strip())
        self.assertEqual("", git("status", "--porcelain", "--", PREFIX + "adapters", PREFIX + "core").strip())

    def test_a_4_the_prior_wave_files_are_zero_lines_from_the_seal_commit(self):
        for rel in PRIOR_FILES:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)
            self.assertEqual("", git("diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + rel).strip(), rel)
            self.assertEqual("", git("status", "--porcelain", "--", PREFIX + rel).strip(), rel)

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        body = read("tests/adapters/xbrl/test_boundary.py")
        for word in (u"universal", u"um0", u"um2", u"um3"):
            self.assertNotIn(word, body)

    def test_a_6_the_prediction_rows_of_the_seal_hold_the_sealed_words(self):
        seal = read(SEAL_REL)
        rows = dict((m.group(1), m.group(0)) for m in re.finditer(u"^\\| (UM3-[A-Z][0-9]) \\|.*$", seal, re.M))
        self.assertEqual(sorted(TAL.BOUNDS), sorted(rows))
        self.assertEqual(16, len(rows))
        words = {
            u"UM3-A1": (u"240 のうち 216 以上", u"215 以下"), u"UM3-A2": (u"90% 以上", u"85% 以上"), u"UM3-A3": (u"480 のうち 1 以上", u"0"),
            u"UM3-A4": (u"240 のうち 216 以上", u"215 以下"), u"UM3-A5": (u"80% 以上", u"80% 未満"), u"UM3-A6": (u"1 以上", u"0"),
            u"UM3-A7": (u"4 社のうち 2 以上", u"1 以下"), u"UM3-A8": (u"半分以上", u"半分未満"), u"UM3-A9": (u"95% 以上", u"95% 未満"),
            u"UM3-L1": (u"6 以上", u"5 以下"), u"UM3-L2": (u"6 以上", u"5 以下"), u"UM3-L3": (u"3 以下", u"4 以上"), u"UM3-L4": (u"より小さい", u"同じか大きい"),
            u"UM3-L5": (u"16 のうち 4 以上", u"3 以下"), u"UM3-L6": (u"16 のうち 0", u"1 以上"), u"UM3-D1": (u"16 本のうち 8 以上", u"7 以下"),
        }
        for k, ws in words.items():
            for w in ws:
                self.assertIn(w, rows[k], (k, w))

    def test_a_7_the_bounds_in_the_script_are_the_sealed_numbers(self):
        want = od([
            (u"UM3-A1", {u"同じ+無いで同じ": 216, u"行の数": 240}), (u"UM3-A2", {u"在るの百分率": 90, u"同じの百分率": 85}),
            (u"UM3-A3", {u"違う+無いのに在る": 1, u"行の数": 480}), (u"UM3-A4", {u"同じ+無いで同じ": 216, u"行の数": 240}),
            (u"UM3-A5", {u"同じの百分率": 80}), (u"UM3-A6", {u"無いのに在る": 1}), (u"UM3-A7", {u"数値が違う行が在る社": 2, u"会社の数": 4}),
            (u"UM3-A8", {u"高の割合の分子": 1, u"高の割合の分母": 2}), (u"UM3-A9", {u"成り立つ百分率": 95}),
            (u"UM3-L1", {u"席": 6, u"席の数": 8}), (u"UM3-L2", {u"席": 6, u"席の数": 8}), (u"UM3-L3", {u"席": 3, u"席の数": 8}),
            (u"UM3-L4", {u"中央値の 2 倍の差": 1}), (u"UM3-L5", {u"席": 4, u"席の数": 16}), (u"UM3-L6", {u"席": 0, u"席の数": 16}), (u"UM3-D1", {u"資料": 8, u"席の数": 16}),
        ])
        self.assertEqual(json.dumps(want, ensure_ascii=False), json.dumps(TAL.BOUNDS, ensure_ascii=False))


def order_problems_allowing_not_yet(root, seal_short, files):
    got = PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], files)
    return [x for x in got if not x.startswith(u"UNCOMMITTED:")]


def make_repo(files_by_commit, root):
    subprocess.run(["git", "init", "-q", root], check=True)
    for msg, files in files_by_commit:
        for rel, body in files.items():
            wbytes(os.path.join(root, rel), body.encode("utf-8"))
        subprocess.run(["git", "-C", root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg], check=True)


class OrderTest(unittest.TestCase):
    def test_p_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        self.assertEqual([], order_problems_allowing_not_yet(REPO, SEAL_COMMIT_SHORT, list(ORDER_FILES)))

    def test_p_2_the_order_check_lists_the_script_and_the_gate_and_not_the_record(self):
        self.assertEqual(2, len(ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)
        for rel in ORDER_FILES:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_p_3_the_order_part_turns_red_when_a_file_comes_before_the_seal(self):
        seal = PREFIX + SEAL_REL
        other = PREFIX + TALLY_REL
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("pre", {other: "x"}), ("seal-x", {seal: "s"}), ("later", {PREFIX + "b": "y"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            got = PR.order_problems(tmp, PREFIX, SEAL_REL, short, [], [TALLY_REL, "b", "missing.py"])
            self.assertIn(u"BEFORE_SEAL:" + TALLY_REL, got)
            self.assertIn(u"UNCOMMITTED:missing.py", got)
            allowed = order_problems_allowing_not_yet(tmp, short, [TALLY_REL, "b", "missing.py"])
            self.assertIn(u"BEFORE_SEAL:" + TALLY_REL, allowed)
            self.assertNotIn(u"UNCOMMITTED:missing.py", allowed)
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("seal-x", {seal: "s"}), ("later", {other: "y"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            self.assertEqual([], list(PR.order_problems(tmp, PREFIX, SEAL_REL, short, [], [TALLY_REL])))


# ======================================================================== 2. script の作り
STDLIB_OK = set(["__future__", "collections", "datetime", "hashlib", "io", "json", "os", "re", "shutil", "sys", "unicodedata", "fractions"])


class ScriptShapeTest(unittest.TestCase):
    def test_b_1_only_the_standard_library_is_imported(self):
        tree = ast.parse(read(TALLY_REL))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names |= set(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add((node.module or "").split(".")[0])
        self.assertTrue(names <= STDLIB_OK, names - STDLIB_OK)
        self.assertNotIn("importlib", names)

    def test_b_2_it_runs_isolated_and_writes_no_traceback_for_bad_commands(self):
        for args in ([], ["--nope"], ["--hand"], ["--tally"], ["--tally", "--record"], ["--process"], ["--digest"], ["--hand", "--tally"]):
            rc, _o, err = run_cli(args)
            self.assertIn(rc, (1, 2, 0), args)
            self.assertNotIn("Traceback", err, args)
        self.assertEqual(2, run_cli([])[0])

    def test_b_3_the_script_does_not_hold_a_scratchpad_path_or_the_harness_words(self):
        body = read(TALLY_REL)
        for w in ("scratchpad", "/private/tmp", "claude-501", "apply_edits(", "inject_with_profile(", "run_doc(", "IJ.select(", "verify_document(", "verify_external(", "tampered", u"注入"):
            self.assertNotIn(w, body, w)

    def test_b_4_the_gate_has_no_skip_and_makes_no_production_material(self):
        body = read(GATE_REL)
        self.assertNotIn(u"skip" + u"Test", body)
        self.assertNotIn(u"@unittest." + u"skip", body)
        self.assertNotIn(u"pytest.mark." + u"skip", body)
        self.assertEqual((1, 2, 3, 4), TAL.PROD)

    def test_b_5_the_fixture_folder_holds_only_the_record(self):
        d = os.path.join(ROOT, "fixtures", "universal", "um3")
        if os.path.exists(d):
            self.assertEqual([u"record.json"], sorted(os.listdir(d)))


# ======================================================================== 3. 作り物の 2 社
GOLD_NAMES = od([
    (u"a01", u"売上高_当期"), (u"a02", u"売上高_前期"), (u"a03", u"売上総利益_当期"), (u"a04", u"営業利益_当期"), (u"a05", u"営業利益_前期"),
    (u"a06", u"経常利益_当期"), (u"a07", u"当期純利益_当期"), (u"a08", u"減価償却費_当期"), (u"a09", u"現金及び預金_当期末"),
    (u"a10", u"流動資産合計_当期末"), (u"a11", u"資産合計_当期末"), (u"a12", u"短期借入金_当期末"), (u"a13", u"長期借入金_当期末"),
    (u"a14", u"負債合計_当期末"), (u"a15", u"純資産合計_当期末"), (u"a16", u"純資産合計_前期末"),
    (u"a29", u"借入の残高の合計_当期末"), (u"a30", u"期末の従業員数_当期末"),
])
A_IDS = [u"a%02d" % k for k in range(1, 31)]
NAMES8 = (u"同じ", u"違う", u"無いのに在る", u"無いで同じ", u"無いで違う", u"分からない", u"答えなし", u"形が読めない")


def make_gold(seed, nulls=()):
    months = [1000000 * seed + 100003 * k for k in range(1, 13)]
    v = {u"a01": sum(months)}
    for k, m in enumerate(months):
        v[u"a%d" % (17 + k)] = m
    for n in (2, 3, 4, 5, 6, 7, 8, 9, 10, 16):
        v[u"a%02d" % n] = 100000 * seed + 7919 * n + n * n
    v[u"a12"] = 3000000 + seed * 101
    v[u"a13"] = 5000000 + seed * 103
    v[u"a29"] = v[u"a12"] + v[u"a13"]
    v[u"a14"] = 2 * v[u"a12"] + 11 * seed
    v[u"a15"] = 9000000 + seed * 37
    v[u"a11"] = v[u"a14"] + v[u"a15"]
    v[u"a30"] = 40 + seed
    for n in nulls:
        v[n] = None
    return v


def gold_file(g1, g2):
    out = {}
    for per, g in ((u"期1", g1), (u"期2", g2)):
        body = dict((GOLD_NAMES[i], g[i]) for i in GOLD_NAMES)
        body[u"月次の売上高_当期"] = [g[u"a%d" % (17 + k)] for k in range(12)]
        out[per] = body
    return out


# 席の行の種類 → 値の表の行(結果の名の判定は門の側で別に持つ。script の classify を使わない)
KIND_NAME = {u"same": u"同じ", u"jsonint": u"同じ", u"diff": u"違う", u"diff1": u"違う", u"unread": u"形が読めない", u"ghost5": u"無いのに在る", u"ghost9": u"無いのに在る",
             u"unknown": u"分からない", u"absent": u"答えなし"}


def kind_name(kind, gold_value):
    if kind == u"none":
        return u"無いで同じ" if gold_value is None else u"無いで違う"
    return KIND_NAME[kind]


def table_rows(gold, spec, conf=None):
    rows = []
    for ident in A_IDS:
        kind = spec.get(ident, u"same")
        g = gold[ident]
        row = od([(u"id", ident), (u"自信", (conf or {}).get(ident, u"高")), (u"出どころ", u"ある file のどこか")])
        if kind == u"absent":
            continue
        if kind == u"same":
            row.update([(u"状態", u"在る"), (u"数値", str(g))])
        elif kind == u"jsonint":
            row.update([(u"状態", u"在る"), (u"数値", g)])
        elif kind == u"diff":
            row.update([(u"状態", u"在る"), (u"数値", str(g + 13))])
        elif kind == u"diff1":
            row.update([(u"状態", u"在る"), (u"数値", str(g + 1))])
        elif kind == u"unread":
            row.update([(u"状態", u"在る"), (u"数値", u"1,234")])
        elif kind == u"none":
            row.update([(u"状態", u"無い"), (u"数値", None)])
        elif kind == u"ghost5":
            row.update([(u"状態", u"在る"), (u"数値", u"5")])
        elif kind == u"ghost9":
            row.update([(u"状態", u"在る"), (u"数値", u"9")])
        elif kind == u"unknown":
            row.update([(u"状態", u"分からない"), (u"数値", None)])
        rows.append(row)
    return rows


def calc_rows(gold, bad33=False):
    a31 = gold[u"a12"] + gold[u"a13"]
    r32 = Fraction(gold[u"a15"], gold[u"a11"])
    a32 = Fraction(round(r32 * 10000), 10000)
    r33 = Fraction(a31) / (gold[u"a04"] + gold[u"a08"])
    a33 = Fraction(round(r33 * 100), 100) + (1 if bad33 else 0)
    return [od([(u"id", u"a31"), (u"状態", u"在る"), (u"数値", str(a31)), (u"自信", u"高"), (u"出どころ", u"x")]),
            od([(u"id", u"a32"), (u"状態", u"在る"), (u"数値", u"%.4f" % float(a32)), (u"自信", u"高"), (u"出どころ", u"x")]),
            od([(u"id", u"a33"), (u"状態", u"在る"), (u"数値", u"%.2f" % float(a33)), (u"自信", u"高"), (u"出どころ", u"x")])]


# 社 101・102 の正解
NULLS = {(101, 1): (u"a05", u"a06", u"a07"), (101, 2): (u"a05", u"a08"), (102, 1): (), (102, 2): ()}
SEED = {(101, 1): 7, (101, 2): 8, (102, 1): 9, (102, 2): 10}
GOLD = dict((k, make_gold(SEED[k], NULLS[k])) for k in SEED)

# 席の行の指定(書かない id は same)
SPEC = {
    (101, u"a", 1): {u"a02": u"diff", u"a03": u"jsonint", u"a04": u"unread", u"a05": u"none", u"a06": u"ghost5", u"a07": u"none", u"a08": u"none", u"a09": u"unknown",
                     u"a10": u"absent", u"a14": u"diff1"},
    (101, u"b", 1): {u"a03": u"diff", u"a05": u"none", u"a06": u"ghost5", u"a07": u"ghost9", u"a08": u"none", u"a09": u"unknown", u"a10": u"absent", u"a14": u"diff1"},
    (102, u"a", 1): {u"a02": u"diff"},
    (102, u"b", 1): {u"a02": u"diff", u"a30": u"absent"},
    (101, u"a", 2): {u"a05": u"ghost5", u"a08": u"none", u"a20": u"diff", u"a30": u"absent"},
    (101, u"b", 2): {u"a05": u"none", u"a08": u"none", u"a21": u"diff"},
}
CONF = {(101, u"a", 1): {u"a02": u"低", u"a06": u"中", u"a09": u"低", u"a04": u"不明"}}
BAD_DOC = {(101, u"a", 1): 2, (101, u"b", 1): 0, (102, u"a", 1): 1, (102, u"b", 1): 0, (101, u"a", 2): 1, (101, u"b", 2): 3, (102, u"a", 2): 0}
UNMATCHED_TOKENS = (u"31415926", u"27182818", u"16180339")


def doc_text(gold, bad_n):
    toks = u" ".join(UNMATCHED_TOKENS[:bad_n])
    return (u"# 説明資料\n令和の資料です。2025年3月 2024-03-31 の期。7 店。\n売上は {a01:,}円、資産は {a11} です。\n{bad}\n".format(a01=gold[u"a01"], a11=gold[u"a11"], bad=toks))


def materials(folder, sub=u"素材"):
    wtext(os.path.join(folder, sub, u"仕訳帳.csv"), u"日付,科目,借方,貸方\n" + u"2024-04-05,売上高,0,100\n" * 20)
    wtext(os.path.join(folder, sub, u"月次.csv"), u"月,売上高\n1,100\n2,200\n")
    wtext(os.path.join(folder, sub, u"在庫.csv"), u"品,数\nあ,1\n")


# ---- 会話の記録の作り方(便 UM2 の席の記録と同じ形: 1 行 1 つ・message.content・timestamp)
class TB(object):
    def __init__(self, path, first_text, with_ts=True):
        self.path, self.n, self.with_ts, self.k = path, 0, with_ts, 0
        self.lines = []
        self.add({u"type": u"user", u"message": {u"role": u"user", u"content": first_text}})

    def add(self, o):
        if self.with_ts:
            o[u"timestamp"] = u"2026-11-24T10:%02d:%02d.000Z" % divmod(self.n * 10, 60)
        self.n += 1
        self.lines.append(json.dumps(o, ensure_ascii=False))

    def call(self, name, inp, error=False, dup=False, dupres=False):
        self.k += 1
        tid = u"toolu_%d" % self.k
        blk = {u"type": u"tool_use", u"id": tid, u"name": name, u"input": inp}
        self.add({u"type": u"assistant", u"message": {u"role": u"assistant", u"content": [blk]}})
        if dup:
            self.add({u"type": u"assistant", u"message": {u"role": u"assistant", u"content": [blk]}})
        res = {u"type": u"tool_result", u"tool_use_id": tid, u"content": u"x"}
        if error:
            res[u"is_error"] = True
        self.add({u"type": u"user", u"message": {u"role": u"user", u"content": [res]}})
        if dupres:
            self.add({u"type": u"user", u"message": {u"role": u"user", u"content": [res]}})

    def text(self, t):
        self.add({u"type": u"assistant", u"message": {u"role": u"assistant", u"content": [{u"type": u"text", u"text": t}]}})

    def save(self):
        wtext(self.path, u"\n".join(self.lines) + u"\n")


def build_world(tmp):
    u"""作り物の世界。→ dict(co, seat, root, tdir, hand2)。"""
    co, seat, root, tdir, hand2 = [os.path.join(tmp, x) for x in (u"co", u"seat", u"root", u"trans", u"hand2")]
    for i in (101, 102):
        wjson(os.path.join(co, str(i), u"正解", u"正解.json"), gold_file(GOLD[(i, 1)], GOLD[(i, 2)]))
        wjson(os.path.join(seat, str(i), u"指定_期1_A.json"), {u"成果物": u"A", u"当期の始まり": u"2024-04-01", u"当期の終わり": u"2025-03-31"})
        wjson(os.path.join(seat, str(i), u"指定_期2_A.json"), {u"成果物": u"A", u"当期の始まり": u"2025-04-01", u"当期の終わり": u"2026-03-31"})
        for p in (1, 2):
            materials(os.path.join(co, str(i)), u"期%d" % p)
    # 便 UM2 の B の出力(101 だけ。102 は無い)
    mats = []
    for ident in A_IDS:
        if ident in (u"a02", u"a03", u"a09", u"a14"):
            mats.append({u"id": ident, u"状態": u"在る", u"判定": u"止める", u"規則": [u"K4"]})
        elif ident == u"a04":
            mats.append({u"id": ident, u"状態": u"在る", u"判定": u"止める", u"規則": [u"K1", u"K4"]})
        elif ident in (u"a05", u"a06", u"a07"):
            mats.append({u"id": ident, u"状態": u"無い", u"判定": u"無いを受ける", u"規則": []})
        elif ident == u"a08":
            mats.append({u"id": ident, u"状態": u"在る", u"判定": u"通す(取り方は未確認)", u"規則": []})
        elif ident == u"a10":
            continue
        else:
            mats.append({u"id": ident, u"状態": u"在る", u"判定": u"通す", u"規則": []})
    wjson(os.path.join(seat, u"101", u"出力", u"判定_期1_A.json"), {u"束": {u"状態": u"受理", u"規則": [], u"理由": []}, u"材料": mats})
    store = {}
    for ident in A_IDS:
        store[ident] = {u"状態": u"確認待ち" if ident in (u"a05", u"a20", u"a30") else (u"無い" if ident == u"a08" else (u"保留" if ident == u"a21" else u"在る"))}
    wjson(os.path.join(seat, u"101", u"出力", u"置き場_期2_A.json"), {u"版": u"u2-store", u"行": store})
    # 席の folder(値の表・資料)
    for (i, r, p), spec in SPEC.items():
        f = os.path.join(root, str(i), r, u"期%d" % p)
        rows = table_rows(GOLD[(i, p)], spec, CONF.get((i, r, p)))
        if (i, r, p) == (101, u"a", 1):
            rows += calc_rows(GOLD[(i, p)], bad33=True)
        wjson(os.path.join(f, u"値の表.json"), {u"行": rows})
        materials(f)
        wtext(os.path.join(f, u"資料.md"), doc_text(GOLD[(i, p)], BAD_DOC[(i, r, p)]))
    # 102 の 2 期目: a は壊れた json・b は folder が無い(資料も無い)。資料だけ a に在る
    fa = os.path.join(root, u"102", u"a", u"期2")
    wtext(os.path.join(fa, u"値の表.json"), u"{")
    wtext(os.path.join(fa, u"資料.md"), doc_text(GOLD[(102, 2)], 0))
    materials(fa)
    # 101 の 2 期目の席の folder に前の期の成果
    f2 = os.path.join(root, u"101", u"a", u"期2")
    wtext(os.path.join(f2, u"前の期の成果", u"道具", u"x.py"), u"print(1)\n")
    materials(f2, u"前の期の素材")
    # 会話の記録
    f1 = os.path.join(root, u"101", u"a", u"期1")
    t1 = TB(os.path.join(tdir, u"t1.output"), u"役: 資料を作る席。folder `%s` 1 期目の章。" % f1)
    t1.call(u"Read", {u"file_path": f1 + u"/頼み.md"})
    t1.text(u"見ます")
    t1.text(u"  ")
    t1.call(u"Bash", {u"command": u'ls "%s/素材"' % f1}, dup=True)
    t1.call(u"Bash", {u"command": u'head -3 "%s/素材/月次.csv"' % f1})
    t1.call(u"Bash", {u"command": u'wc -l "%s/素材/仕訳帳.csv"' % f1})
    t1.call(u"Write", {u"file_path": f1 + u"/道具/a.py", u"content": u"import json\nopen('値の表.json','w').write('{}')\n"})
    t1.call(u"Bash", {u"command": u'cd "%s" && python3 道具/a.py' % f1})
    t1.call(u"Bash", {u"command": u'python3 -c "print(1)"'}, error=True)
    t1.call(u"Write", {u"file_path": f1 + u"/値の表.json", u"content": u"{}"})
    t1.call(u"Write", {u"file_path": f1 + u"/資料.md", u"content": u"x"})
    t1.call(u"Read", {u"file_path": f1 + u"/素材/仕訳帳.csv"})
    t1.save()
    t2 = TB(os.path.join(tdir, u"t2.output"), u"folder `%s` 2 期目の章。" % f2)
    t2.call(u"Read", {u"file_path": f2 + u"/頼み.md"})
    t2.call(u"Bash", {u"command": u'ls "%s/前の期の成果"' % f2})
    t2.call(u"Read", {u"file_path": f2 + u"/前の期の成果/値の表.json"})
    t2.call(u"Bash", {u"command": u'cd "%s" && python3 前の期の成果/道具/x.py' % f2})
    t2.call(u"Bash", {u"command": u'head "%s/前の期の素材/月次.csv"' % f2})
    t2.call(u"Bash", {u"command": u'head "%s/素材/月次.csv"' % f2})
    t2.call(u"Bash", {u"command": u"cat /etc/hosts"})
    t2.call(u"Bash", {u"command": u"cat ../x"})
    t2.call(u"Write", {u"file_path": f2 + u"/値の表.json", u"content": u"{}"})
    t2.call(u"Write", {u"file_path": f2 + u"/資料.md", u"content": u"x"})
    t2.save()
    # 101 回 b 期 2 は同じ folder の記録が 2 本
    f4 = os.path.join(root, u"101", u"b", u"期2")
    materials(f4)
    for name in (u"t3.output", u"t4.output"):
        t = TB(os.path.join(tdir, name), u"folder `%s`" % f4)
        t.call(u"Read", {u"file_path": f4 + u"/頼み.md"})
        t.save()
    # 回 b 期 1 の記録は、最初の user の文には別の folder・2 つ目の user の文に自分の folder(対応しない)
    f3 = os.path.join(root, u"101", u"b", u"期1")
    t5 = TB(os.path.join(tdir, u"t5.output"), u"folder `%s`" % os.path.join(root, u"999", u"a", u"期1"))
    t5.add({u"type": u"user", u"message": {u"role": u"user", u"content": u"あとで folder `%s`" % f3}})
    t5.call(u"Read", {u"file_path": f3 + u"/頼み.md"})
    t5.save()
    # B の席(便 UM2 の 1 期目の B の席)101: 時刻なし
    fb = os.path.join(hand2, u"101", u"A")
    materials(fb, u"期1")
    tb = TB(os.path.join(tdir, u"tb.output"), u"folder `%s` 役: 材料を書く席" % fb, with_ts=False)
    tb.call(u"Bash", {u"command": u'head "%s/期1/月次.csv"' % fb})
    tb.call(u"Bash", {u"command": u'cat "%s/期1/仕訳帳.csv"' % fb})
    tb.call(u"Write", {u"file_path": fb + u"/作る.py", u"content": u"print(2)\n"})
    tb.call(u"Bash", {u"command": u'python3 "%s/作る.py"' % fb})
    tb.save()
    return dict(co=co, seat=seat, root=root, tdir=tdir, hand2=hand2)


class World(unittest.TestCase):
    u"""作り物の世界を 1 つだけ作る(読むだけ)。"""
    tmp = None

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.w = build_world(cls.tmp)
        cls.rec2 = cls.tally((101, 102), (u"a", u"b"))
        cls.rec1 = cls.tally((101, 102), (u"a",))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def tally(cls, companies, rounds):
        w = cls.w
        return TAL.tally(companies, w["co"], w["seat"], w["root"], w["tdir"], w["hand2"], rounds)

    def n(self, key, rec=None):
        return (rec or self.rec2)[u"数"][key]


# ======================================================================== 4. 行ごとの結果・計算・関係・掛け合わせ・揺れ・自信・資料
class RowResultTest(World):
    def test_c_1_the_id_to_gold_key_table_is_the_one_written_independently(self):
        self.assertEqual(list(GOLD_NAMES.items()), [(i, k) for i, k in TAL.GOLD_KEYS])
        d = json.loads(read("fixtures/universal/um0/definition_A.json"))
        names = dict((r[u"id"], r[u"名"]) for r in d[u"行"])
        for ident in [u"a%02d" % k for k in range(1, 11)] + [u"a12", u"a13", u"a14", u"a30"]:
            self.assertEqual(GOLD_NAMES[ident], names[ident].replace(u"(", u"_").replace(u")", u""), ident)

    def test_c_2_company_101_round_a_period_1_has_the_hand_decided_counts(self):
        # 同じ 21・違う 2・形が読めない 1・無いで同じ 2・無いのに在る 1・無いで違う 1・分からない 1・答えなし 1(足して 30)
        want = {u"同じ": 21, u"違う": 2, u"形が読めない": 1, u"無いで同じ": 2, u"無いのに在る": 1, u"無いで違う": 1, u"分からない": 1, u"答えなし": 1}
        self.assertEqual(30, sum(want.values()))
        rec = self.tally((101,), (u"a",))
        for name in NAMES8:
            self.assertEqual(want[name], rec[u"数"][u"期1:結果:" + name], name)
        self.assertEqual(30, rec[u"数"][u"期1:行の数"])

    def test_c_3_all_eight_result_names_are_reached_and_the_totals_follow_the_specs(self):
        for p in (1, 2):
            want = collections.Counter()
            for (i, r, pp), spec in SPEC.items():
                if pp == p:
                    for ident in A_IDS:
                        want[kind_name(spec.get(ident, u"same"), GOLD[(i, p)][ident])] += 1
            if p == 2:
                want[u"形が読めない"] += 30          # 102 a の壊れた値の表
                want[u"答えなし"] += 30              # 102 b の folder 無し
            for name in NAMES8:
                self.assertEqual(want[name], self.n(u"期%d:結果:%s" % (p, name)), (p, name))
            self.assertEqual(120, self.n(u"期%d:行の数" % p))
            self.assertEqual(120, sum(self.n(u"期%d:結果:%s" % (p, nm)) for nm in NAMES8))
        for name in NAMES8:
            self.assertGreaterEqual(self.n(u"期1:結果:" + name) + self.n(u"期2:結果:" + name), 1, name)
        # 手で決めた合計(p1: 同じ 100・違う 6・形 1・無いで同じ 3・無いのに在る 3・無いで違う 2・分からない 2・答えなし 3 / p2: 同じ 53・違う 2・無いのに在る 1・無いで同じ 3・形 30・答えなし 31)
        hand1 = {u"同じ": 100, u"違う": 6, u"形が読めない": 1, u"無いで同じ": 3, u"無いのに在る": 3, u"無いで違う": 2, u"分からない": 2, u"答えなし": 3}
        hand2 = {u"同じ": 53, u"違う": 2, u"形が読めない": 30, u"無いで同じ": 3, u"無いのに在る": 1, u"無いで違う": 0, u"分からない": 0, u"答えなし": 31}
        for name in NAMES8:
            self.assertEqual(hand1[name], self.n(u"期1:結果:" + name), name)
            self.assertEqual(hand2[name], self.n(u"期2:結果:" + name), name)

    def test_c_4_a_missing_file_is_no_answer_a_broken_one_is_unreadable_and_a_missing_row_is_no_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual((u"無し", {}, 0), TAL.read_table(os.path.join(tmp, u"x.json")))
            wtext(os.path.join(tmp, u"b.json"), u"{")
            self.assertEqual(u"読めない", TAL.read_table(os.path.join(tmp, u"b.json"))[0])
            wjson(os.path.join(tmp, u"c.json"), {u"行": {u"a01": 1}})
            self.assertEqual(u"読めない", TAL.read_table(os.path.join(tmp, u"c.json"))[0])
            wjson(os.path.join(tmp, u"d.json"), {u"行": [{u"id": u"a01", u"状態": u"在る", u"数値": u"1"}, {u"id": u"a01", u"状態": u"在る", u"数値": u"2"}, 5]})
            st, rows, dup = TAL.read_table(os.path.join(tmp, u"d.json"))
            self.assertEqual((u"読めた", 1, u"1"), (st, dup, rows[u"a01"][u"数値"]))
        c = TAL.classify
        row = lambda **k: dict(k)
        self.assertEqual(u"答えなし", c(5, u"無し", None))
        self.assertEqual(u"形が読めない", c(5, u"読めない", None))
        self.assertEqual(u"答えなし", c(5, u"読めた", None))
        self.assertIsNone(c(TAL.UNREADABLE, u"読めた", row(状態=u"在る", 数値=u"5")))

    def test_c_5_the_number_reading_is_a_signed_integer_text_only(self):
        c = TAL.classify
        ok = lambda v: c(5, u"読めた", {u"状態": u"在る", u"数値": v})
        self.assertEqual(u"同じ", ok(u" 5 "))
        self.assertEqual(u"同じ", ok(u"+5"))
        self.assertEqual(u"違う", ok(u"-5"))
        self.assertEqual(u"同じ", ok(5))
        for bad in (u"5.0", u"5,000", u"５", u"1e3", u"", u"五", u"5円", 5.0, True, None, [5], u"- 5", u"1_000", u"5\u0663", u"\u0663", u"5 6"):
            self.assertEqual(u"形が読めない", ok(bad), repr(bad))
        self.assertEqual(u"形が読めない", ok(u"9" * 5000))
        self.assertEqual(u"形が読めない", c(5, u"読めた", {u"状態": u"たぶん", u"数値": u"5"}))
        self.assertEqual(u"形が読めない", c(5, u"読めた", {u"数値": u"5"}))
        self.assertEqual(u"無いのに在る", c(None, u"読めた", {u"状態": u"在る", u"数値": u"0"}))
        self.assertEqual(u"形が読めない", c(None, u"読めた", {u"状態": u"在る", u"数値": None}))
        self.assertEqual(u"無いで同じ", c(None, u"読めた", {u"状態": u"無い"}))
        self.assertEqual(u"無いで違う", c(0, u"読めた", {u"状態": u"無い"}))
        self.assertEqual(u"分からない", c(None, u"読めた", {u"状態": u"分からない", u"数値": u"7"}))

    def test_c_6_an_unreadable_gold_item_is_not_a_result_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = build_world(tmp)
            g = json.loads(read_text(os.path.join(w["co"], u"101", u"正解", u"正解.json")))
            del g[u"期1"][u"売上高_当期"]
            g[u"期1"][u"営業利益_当期"] = u"x"
            wjson(os.path.join(w["co"], u"101", u"正解", u"正解.json"), g)
            rec = TAL.tally((101,), w["co"], w["seat"], w["root"], w["tdir"], w["hand2"], (u"a",))
        self.assertEqual(2, rec[u"数"][u"正解が読めない行"])
        self.assertEqual(28, rec[u"数"][u"期1:行の数"])

    def test_c_7_the_three_calculation_rows_follow_the_definition_table(self):
        n = self.n
        self.assertEqual((2, 1, 9, 0), (n(u"期1:計算:同じ"), n(u"期1:計算:違う"), n(u"期1:計算:答えなし"), n(u"期1:計算:分母から外した")))
        self.assertEqual((0, 0, 7, 3, 2), (n(u"期2:計算:同じ"), n(u"期2:計算:違う"), n(u"期2:計算:答えなし"), n(u"期2:計算:形が読めない"), n(u"期2:計算:分母から外した")))
        defs = TAL.load_calc_defs(os.path.join(ROOT, TAL.DEFS_REL))
        self.assertEqual([(u"a31", u"和", [u"a12", u"a13"], 0), (u"a32", u"比", [u"a15", u"a11"], 4), (u"a33", u"比の分母和", [u"a31", u"a04", u"a08"], 2)], defs)
        exp = TAL.expected_calc(defs, GOLD[(101, 2)])
        self.assertIsNone(exp[u"a33"][0])
        exp1 = TAL.expected_calc(defs, GOLD[(101, 1)])
        self.assertEqual(Fraction(GOLD[(101, 1)][u"a12"] + GOLD[(101, 1)][u"a13"]), exp1[u"a31"][0])
        self.assertEqual(u"違う", TAL.calc_result(Fraction(5, 100), 2, u"読めた", {u"状態": u"在る", u"数値": u"0.06"}))
        self.assertEqual(u"同じ", TAL.calc_result(Fraction(5, 100), 2, u"読めた", {u"状態": u"在る", u"数値": u"0.0500"}))
        self.assertEqual(u"同じ", TAL.calc_result(Fraction(6, 100), 2, u"読めた", {u"状態": u"在る", u"数値": u"0.055"}))      # 0.5 は 0 から遠い側
        self.assertEqual(u"形が読めない", TAL.calc_result(Fraction(5, 100), 2, u"読めた", {u"状態": u"在る", u"数値": u"5%"}))
        self.assertEqual(u"無い", TAL.calc_result(Fraction(5, 100), 2, u"読めた", {u"状態": u"無い"}))

    def test_c_17_a_zero_denominator_takes_the_row_out_of_the_base_and_does_not_fall(self):
        defs = TAL.load_calc_defs(os.path.join(ROOT, TAL.DEFS_REL))
        g = dict(GOLD[(101, 1)])
        g.update({u"a04": 0, u"a08": 0})
        self.assertIsNone(TAL.expected_calc(defs, g)[u"a33"][0])
        g = dict(GOLD[(101, 1)])
        g[u"a11"] = 0
        self.assertIsNone(TAL.expected_calc(defs, g)[u"a32"][0])
        g = dict(GOLD[(101, 1)])
        g.update({u"a04": 5, u"a08": -5})
        self.assertIsNone(TAL.expected_calc(defs, g)[u"a33"][0])

    def test_c_18_a_calculation_rows_value_in_the_document_is_a_matched_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = build_world(tmp)
            f = os.path.join(w["root"], u"101", u"a", u"期1")
            before = TAL.tally((101,), w["co"], w["seat"], w["root"], w["tdir"], w["hand2"], (u"a",))[u"数"]
            rows = json.loads(read_text(os.path.join(f, u"値の表.json")))[u"行"]
            dec = [r[u"数値"] for r in rows if r[u"id"] in (u"a32", u"a33")]
            self.assertEqual(2, len(dec))
            self.assertTrue(all(u"." in x for x in dec))
            with io.open(os.path.join(f, u"資料.md"), "a", encoding="utf-8") as fh:
                fh.write(u"\n計算 %s と %s です\n" % (dec[0], dec[1]))
            after = TAL.tally((101,), w["co"], w["seat"], w["root"], w["tdir"], w["hand2"], (u"a",))[u"数"]
        self.assertEqual(2, after[u"資料:数の字の数"] - before[u"資料:数の字の数"])
        self.assertEqual(0, after[u"資料:当たらない数の字の数"] - before[u"資料:当たらない数の字の数"])

    def test_c_8_relations_hold_in_the_seats_own_table(self):
        n = self.n
        # 2 期目は 101 の a で a20(月次の一か月)・b で a21 が正解と違うので R1 が成り立たない(見られる 2 本のうち 0)
        self.assertEqual((18, 14, 6), (n(u"関係:見られる本数"), n(u"関係:成り立つ本数"), n(u"関係:見られない本数")))
        self.assertEqual((6, 4, 6, 4, 6, 6), (n(u"関係:R1:見られる本数"), n(u"関係:R1:成り立つ本数"), n(u"関係:R2:見られる本数"), n(u"関係:R2:成り立つ本数"), n(u"関係:R3:見られる本数"), n(u"関係:R3:成り立つ本数")))
        rows = dict((r[u"id"], r) for r in table_rows(GOLD[(101, 1)], {}))
        self.assertEqual((3, 3, 0), TAL.relation_counts(rows, u"読めた")[:3])
        rows[u"a20"] = {u"id": u"a20", u"状態": u"無い"}
        self.assertEqual((2, 2, 1), TAL.relation_counts(rows, u"読めた")[:3])
        rows[u"a20"] = {u"id": u"a20", u"状態": u"無い", u"数値": str(GOLD[(101, 1)][u"a20"])}          # 無いと書いた行の数値は使わない
        self.assertEqual((2, 2, 1), TAL.relation_counts(rows, u"読めた")[:3])
        rows[u"a20"] = {u"id": u"a20", u"状態": u"在る", u"数値": str(GOLD[(101, 1)][u"a20"])}
        self.assertEqual((3, 3, 0), TAL.relation_counts(rows, u"読めた")[:3])
        self.assertEqual((0, 0, 3), TAL.relation_counts(rows, u"無し")[:3])

    def test_c_9_the_cross_with_b_uses_company_round_period_and_id(self):
        n = self.n
        stop = {u"違う": 4, u"同じ": 3, u"形が読めない": 1, u"分からない": 2}
        for name in NAMES8:
            self.assertEqual(stop.get(name, 0), n(u"掛け合わせ1:止める×" + name), name)
        self.assertEqual((4, 2, 2), (n(u"掛け合わせ1:止める:K4×違う"), n(u"掛け合わせ1:止める:K4×同じ"), n(u"掛け合わせ1:止める:K4×分からない")))
        self.assertEqual((1, 1), (n(u"掛け合わせ1:止める:K1+K4×形が読めない"), n(u"掛け合わせ1:止める:K1+K4×同じ")))
        # B なし: 101 の a10(両回 答えなし)と 102 の 2 回ぶん(a は 同じ 29・違う 1 / b は 同じ 28・違う 1・答えなし 1)
        self.assertEqual((29 + 28, 1 + 1, 2 + 1), (n(u"掛け合わせ1:B なし×同じ"), n(u"掛け合わせ1:B なし×違う"), n(u"掛け合わせ1:B なし×答えなし")))
        self.assertEqual((3, 3), (n(u"掛け合わせ1:無いを受ける×無いで同じ"), n(u"掛け合わせ1:無いを受ける×無いのに在る")))
        self.assertEqual(2, n(u"掛け合わせ1:通す(取り方は未確認)×無いで違う"))
        total1 = sum(v for k, v in self.rec2[u"数"].items() if k.startswith(u"掛け合わせ1:") and not k.startswith(u"掛け合わせ1:止める:"))
        self.assertEqual(120, total1)
        # 2 期目: 置き場の状態
        self.assertEqual({u"無いのに在る": 1, u"違う": 1, u"答えなし": 1, u"無いで同じ": 1, u"同じ": 2}, dict((nm, n(u"掛け合わせ2:確認待ち×" + nm)) for nm in NAMES8 if n(u"掛け合わせ2:確認待ち×" + nm)))
        self.assertEqual(2, n(u"掛け合わせ2:無い×無いで同じ"))
        self.assertEqual((1, 1), (n(u"掛け合わせ2:保留×同じ"), n(u"掛け合わせ2:保留×違う")))
        self.assertEqual(60, sum(n(u"掛け合わせ2:B なし×" + nm) for nm in NAMES8))          # 102 の 2 回ぶん
        self.assertEqual(50, sum(n(u"掛け合わせ2:在る×" + nm) for nm in NAMES8))             # 101 の (30 - 確認待ち 3 - 無い 1 - 保留 1) × 2 回

    def test_c_10_the_gold_comparison_of_the_cross_follows_each_company_not_the_other(self):
        rec = self.tally((101,), (u"a",))
        self.assertEqual(0, sum(v for k, v in rec[u"数"].items() if k.startswith(u"掛け合わせ1:B なし×") and not k.endswith(u"答えなし")))
        rec = self.tally((102,), (u"a",))
        self.assertEqual(30, sum(v for k, v in rec[u"数"].items() if k.startswith(u"掛け合わせ1:B なし×")))
        self.assertEqual(0, sum(v for k, v in rec[u"数"].items() if k.startswith(u"掛け合わせ1:止める×")))

    def test_c_11_fluctuation_counts_pairs_of_the_two_rounds(self):
        n = self.n
        self.assertEqual((60, 55, 53, 51, 2, 1), tuple(n(u"揺れ:期1:" + k) for k in (u"行の数", u"結果の名が同じ", u"在るどうし", u"在るどうしで数値が同じ", u"在るどうしで数値が違う", u"数値が違う行が在る社")))
        self.assertEqual((60, 26, 27, 25, 2, 1), tuple(n(u"揺れ:期2:" + k) for k in (u"行の数", u"結果の名が同じ", u"在るどうし", u"在るどうしで数値が同じ", u"在るどうしで数値が違う", u"数値が違う行が在る社")))
        self.assertEqual(0, self.n(u"揺れ:期1:行の数", self.rec1))             # 回が 1 つなら揺れは数えない

    def test_c_12_confidence_is_crossed_with_the_result_name(self):
        n1 = lambda k: self.rec1[u"数"][k]
        self.assertEqual((1, 1, 1, 1), (n1(u"自信:低×違う"), n1(u"自信:低×分からない"), n1(u"自信:中×無いのに在る"), n1(u"自信:読めない×形が読めない")))
        self.assertEqual(3, n1(u"自信:高×違う"))                 # 101 a 期 1 の a14・102 a 期 1 の a02・101 a 期 2 の a20
        self.assertEqual(1, n1(u"自信:高×無いのに在る"))         # 101 a 期 2 の a05
        self.assertEqual(2, n1(u"自信:なし×答えなし"))           # 101 a の a10(期 1)・a30(期 2)
        self.assertEqual(30, n1(u"自信:なし×形が読めない"))      # 102 a 期 2 の壊れた値の表(行が無いので自信は「なし」)
        self.assertEqual(120, sum(v for k, v in self.rec1[u"数"].items() if k.startswith(u"自信:")))

    def test_c_13_the_documents_numbers_are_counted_as_decided(self):
        n = self.n
        self.assertEqual((7, 1, 1), (n(u"資料:本数"), n(u"資料:なし"), n(u"期2:資料:なし")))
        self.assertEqual((9, 5), (n(u"資料:当たらない数の字の数"), n(u"資料:当たらない数の字が 1 つ以上の資料")))
        self.assertEqual(21, n(u"資料:数の字の数"))
        self.assertEqual(1, n(u"資料:値の表が読めない資料"))

    def test_c_14_numbers_of_the_document_match_the_four_forms_and_skip_dates(self):
        vals = [Fraction(1234567), Fraction(4521, 10000), Fraction(50)]
        text = u"1,234,567円 / 1,235千円 / 1.2百万円 / 0.4521→45.21% / 50 / 2025年3月31日 / 2025-03-31 / 2025/3/31 / 99999 / 7 / 12.5 / 令和6年"
        self.assertEqual([u"1234567", u"1235", u"1.2", u"0.4521", u"45.21", u"50", u"99999", u"12.5"], TAL.doc_numbers(text))
        self.assertEqual((8, 2), TAL.unmatched_numbers(text, vals))
        self.assertEqual((0, 0), TAL.unmatched_numbers(u"", vals))
        self.assertEqual((1, 1), TAL.unmatched_numbers(u"1234567", []))
        self.assertEqual((1, 1), TAL.unmatched_numbers(u"9" * 60, vals))
        self.assertEqual((1, 0), TAL.unmatched_numbers(u"△1,234,567", vals))
        self.assertEqual((1, 0), TAL.unmatched_numbers(u"1,234,567", [Fraction(-1234567)]))          # 負の値は絶対値で当てる
        self.assertEqual((1, 0), TAL.unmatched_numbers(u"△1,234,567", [Fraction(-1234567)]))
        self.assertEqual((1, 0), TAL.unmatched_numbers(u"１２３４５６７", [Fraction(1234567)]))      # 全角の数字は NFKC にそろえて数える

    def test_c_16_each_result_name_turned_into_its_neighbour_changes_the_counts_the_gate_decided(self):
        real = TAL.classify
        base = self.tally((101,), (u"a",))[u"数"]
        for k, name in enumerate(NAMES8):
            neighbour = NAMES8[(k + 1) % len(NAMES8)]

            def turned(gold_v, tstate, row, name=name, neighbour=neighbour):
                got = real(gold_v, tstate, row)
                return neighbour if got == name else got
            TAL.classify = turned
            try:
                got = self.tally((101,), (u"a",))[u"数"]
            finally:
                TAL.classify = real
            self.assertNotEqual([got[u"期1:結果:" + n] for n in NAMES8], [base[u"期1:結果:" + n] for n in NAMES8], name)
            self.assertNotEqual(got[u"期1:結果:" + name], base[u"期1:結果:" + name], name)
        self.assertIs(real, TAL.classify)

    def test_c_15_the_record_carries_the_sha_of_what_was_read(self):
        rec = self.rec2
        self.assertTrue(re.match(r"^[0-9a-f]{64}\Z", rec[u"読んだ便 UM2 の出力の sha256 の束ね"]))
        self.assertEqual(4, rec[u"数"][u"読んだ便 UM2 の出力の file の数"])           # 正解 2 つ + 101 の判定と置き場
        a = TAL.read_um2_digest(self.w["co"], self.w["seat"], (101, 102))
        self.assertEqual(4, a[1])
        wjson(os.path.join(self.w["seat"], u"101", u"出力", u"置き場_期2_A.json"), {u"版": u"u2-store", u"行": {}})
        try:
            b = TAL.read_um2_digest(self.w["co"], self.w["seat"], (101, 102))
        finally:
            store = {}
            for ident in A_IDS:
                store[ident] = {u"状態": u"確認待ち" if ident in (u"a05", u"a20", u"a30") else (u"無い" if ident == u"a08" else (u"保留" if ident == u"a21" else u"在る"))}
            wjson(os.path.join(self.w["seat"], u"101", u"出力", u"置き場_期2_A.json"), {u"版": u"u2-store", u"行": store})
        self.assertNotEqual(a[0], b[0])
        self.assertEqual(a[0], TAL.read_um2_digest(self.w["co"], self.w["seat"], (101, 102))[0])


def read_text(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


# ======================================================================== 5. 過程の数
class ProcessTest(World):
    def seat(self, i, r, p):
        return TAL.process_seat(TAL.Transcripts(self.w["tdir"]), os.path.join(self.w["root"], str(i), r, u"期%d" % p))

    def test_d_1_the_first_period_seat_has_the_hand_counted_numbers(self):
        s = self.seat(101, u"a", 1)
        want = od([
            (u"状態", u"数えた"), (u"道具の呼び出し", 10), (u"道具の名ごと", {u"Bash": 5, u"Read": 2, u"Write": 3}), (u"席の発言の回", 1), (u"秒", 220),
            (u"素材の file の数", 3), (u"素材の file のうち path が出た数", 2), (u"素材の file のうち 2 回以上の数", 1), (u"最大の file に触れた", 1),
            (u"最初に値の表を書くまでの呼び出し", 6), (u"値の表を書いた回数", 2), (u"書き直した", 1), (u"資料を書いた回数", 1), (u"script を書いた数", 2),
            (u"python を走らせた数", 2), (u"道具が誤りを返した数", 1), (u"前の期の成果の path が出た呼び出し", 0), (u"前の期の成果の道具を走らせた", 0),
            (u"前の期の素材の path が出た呼び出し", 0), (u"汚れた呼び出し", 0), (u"汚れの席", 0)])
        self.assertEqual(dict(want), dict(s))

    def test_d_2_the_second_period_seat_counts_the_carried_work_and_the_outside_paths(self):
        s = self.seat(101, u"a", 2)
        self.assertEqual(u"数えた", s[u"状態"])
        self.assertEqual((10, {u"Bash": 6, u"Read": 2, u"Write": 2}, 190), (s[u"道具の呼び出し"], s[u"道具の名ごと"], s[u"秒"]))
        self.assertEqual((3, 1, 1), (s[u"前の期の成果の path が出た呼び出し"], s[u"前の期の成果の道具を走らせた"], s[u"前の期の素材の path が出た呼び出し"]))
        self.assertEqual((1, 0, 0, 1), (s[u"素材の file のうち path が出た数"], s[u"素材の file のうち 2 回以上の数"], s[u"最大の file に触れた"], s[u"python を走らせた数"]))
        self.assertEqual((2, 1), (s[u"汚れた呼び出し"], s[u"汚れの席"]))
        self.assertEqual((9, 1, 1, 0), (s[u"最初に値の表を書くまでの呼び出し"], s[u"値の表を書いた回数"], s[u"資料を書いた回数"], s[u"書き直した"]))

    def test_d_3_the_seat_to_transcript_pairing_is_exactly_one_by_the_first_user_text(self):
        self.assertEqual(u"記録が 0 本", self.seat(102, u"a", 1)[u"理由"])
        two = self.seat(101, u"b", 2)
        self.assertEqual((u"過程が数えられない", u"記録が 2 本以上", 2), (two[u"状態"], two[u"理由"], two[u"本数"]))
        later = self.seat(101, u"b", 1)          # 2 つ目の user の文にだけ folder が在る記録は対応しない
        self.assertEqual((u"過程が数えられない", u"記録が 0 本"), (later[u"状態"], later[u"理由"]))
        idx = TAL.Transcripts(self.w["tdir"])
        self.assertEqual(1, len(idx.match(os.path.join(self.w["root"], u"101", u"a", u"期1"))))
        self.assertEqual(2, len(idx.match(os.path.join(self.w["root"], u"101", u"b", u"期2"))))
        # path の続きが違う folder(期 1 に対して 期 10)には対応しない・/private の有無は同じ folder
        f = os.path.join(self.w["root"], u"101", u"a", u"期1")
        self.assertEqual([], idx.match(f + u"0"))
        alt = f[len(u"/private"):] if f.startswith(u"/private/") else u"/private" + f
        self.assertEqual(1, len(idx.match(alt)))
        self.assertEqual(u"記録の folder が無い", TAL.process_seat(None, f)[u"理由"])

    def test_d_4_a_record_without_tool_use_cannot_be_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, u"期1")
            os.makedirs(f)
            t = TB(os.path.join(tmp, u"t", u"x.output"), u"folder `%s`" % f)
            t.text(u"こんにちは")
            t.save()
            s = TAL.process_seat(TAL.Transcripts(os.path.join(tmp, u"t")), f)
        self.assertEqual((u"過程が数えられない", u"tool_use が無い"), (s[u"状態"], s[u"理由"]))

    def test_d_5_no_timestamp_means_no_seconds(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, u"期1")
            os.makedirs(f)
            t = TB(os.path.join(tmp, u"t", u"x.output"), u"folder `%s`" % f, with_ts=False)
            t.call(u"Bash", {u"command": u"ls"})
            t.save()
            s = TAL.process_seat(TAL.Transcripts(os.path.join(tmp, u"t")), f)
        self.assertEqual((u"数えた", None), (s[u"状態"], s[u"秒"]))

    def test_d_6_outside_and_relative_paths_are_counted_inside_and_system_binaries_are_not(self):
        f = u"/private/tmp/zz/seat"
        v = TAL.folder_variants(f)
        for raw, want in ((u"cat /private/tmp/zz/seat/素材/a.csv", False), (u"cat /tmp/zz/seat/素材/a.csv", False), (u"cat /private/tmp/zz/other/a.csv", True),
                          (u"cat /private/tmp/zz/seat2/a.csv", True), (u"/usr/bin/python3 /private/tmp/zz/seat/x.py", False), (u"cat /Users/x/y", True),
                          (u"cat ../a", True), (u"cat ~/a", True), (u"echo $HOME", True), (u"ls", False), (u"cd /private/tmp/zz/seat; ls", False),
                          (u"cat /etc/passwd", True), (u"cat /var/folders/ab", True), (u"python3 -c 'print(1)'", False)):
            self.assertEqual(want, TAL.is_dirty(raw, v), raw)

    def test_d_7_writes_are_seen_by_tool_by_redirect_by_script_body_and_by_a_written_script(self):
        w = TAL.writes_name
        for raw in (u"cat x > 値の表.json", u"python3 - <<E\njson.dump(o, open('値の表.json','w'))\nE", u"tee 値の表.json", u"cp a.json 値の表.json", u"open(os.path.join(d,'値の表.json'),'w')"):
            self.assertTrue(w(raw, u"値の表.json"), raw)
        for raw in (u"cat 値の表.json", u"python3 -c \"import json;json.load(open('値の表.json'))\"", u"ls", u"echo 値の表.json > x.txt"):
            self.assertFalse(w(raw, u"値の表.json"), raw)

    def test_d_8_broken_transcripts_do_not_crash_the_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, u"期1")
            os.makedirs(f)
            t = TB(os.path.join(tmp, u"t", u"x.output"), u"folder `%s`" % f)
            t.call(u"Bash", {u"command": u"ls"})
            t.lines.insert(1, u"{not json")
            t.lines.insert(1, u"[1,2]")
            t.lines.insert(1, u"")
            t.lines.insert(1, json.dumps({u"type": u"assistant", u"message": {u"content": u"文"}}))
            t.lines.insert(1, json.dumps({u"type": u"assistant", u"message": {u"content": [{u"type": u"tool_use", u"id": 5, u"name": None, u"input": [1, {u"a": u"b"}]}, 3]}}))
            t.lines.append(u"x" * 3000000)
            t.save()
            wbytes(os.path.join(tmp, u"t", u"y.output"), b"\xff\xfe\x00bad\n")
            wbytes(os.path.join(tmp, u"t", u"z.output"), b"")
            s = TAL.process_seat(TAL.Transcripts(os.path.join(tmp, u"t")), f)
            self.assertEqual(u"数えた", s[u"状態"])
            self.assertEqual(2, s[u"道具の呼び出し"])
            self.assertEqual(u"記録が 0 本", TAL.process_seat(TAL.Transcripts(os.path.join(tmp, u"nothing")), f)[u"理由"])

    def test_d_12_the_median_is_doubled_and_integer(self):
        self.assertEqual(14, TAL.median2([7]))
        self.assertEqual(4, TAL.median2([3, 1, 2]))
        self.assertEqual(5, TAL.median2([4, 1, 2, 3]))
        self.assertEqual(18, TAL.median2([9, 100, 8]))
        self.assertIsNone(TAL.median2([]))

    def count_of(self, build, folder_name=u"期1", extra_dirs=()):
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, folder_name)
            materials(f)
            for d in extra_dirs:
                os.makedirs(os.path.join(f, d))
            t = TB(os.path.join(tmp, u"t", u"x.output"), u"folder `%s`" % f)
            build(t, f)
            t.save()
            return TAL.process_seat(TAL.Transcripts(os.path.join(tmp, u"t")), f)

    def test_d_16_one_outside_call_is_enough_to_make_a_seat_dirty(self):
        def one(t, f):
            t.call(u"Bash", {u"command": u'ls "%s"' % f})
            t.call(u"Read", {u"file_path": u"/Users/someone/memory.md"})
        got = self.count_of(one)
        self.assertEqual((1, 1), (got[u"汚れた呼び出し"], got[u"汚れの席"]))

        def none(t, f):
            t.call(u"Bash", {u"command": u'ls "%s"' % f})
        got = self.count_of(none)
        self.assertEqual((0, 0), (got[u"汚れた呼び出し"], got[u"汚れの席"]))

    # ---- 直し(記録の監査 REVISE): 席の発言の回の合成メッセージ・SubagentHandback の汚れ
    def test_d_60_a_synthetic_limit_message_is_not_a_seat_utterance(self):
        def build(t, f):
            t.text(u"席の本当の発言")
            t.call(u"Bash", {u"command": u'ls "%s"' % f})
            t.add({u"type": u"assistant", u"isApiErrorMessage": True,
                   u"message": {u"role": u"assistant", u"model": u"claude-x", u"content": [{u"type": u"text", u"text": u"You have hit your limit"}]}})
            t.add({u"type": u"assistant", u"message": {u"role": u"assistant", u"model": u"<synthetic>", u"content": [{u"type": u"text", u"text": u"No response requested."}]}})
            t.add({u"type": u"assistant", u"isApiErrorMessage": False,
                   u"message": {u"role": u"assistant", u"model": u"claude-x", u"content": [{u"type": u"text", u"text": u"もう 1 つの本当の発言"}]}})
        self.assertEqual(2, self.count_of(build)[u"席の発言の回"])

    def test_d_61_the_final_report_tool_input_is_not_a_path_but_the_same_text_in_bash_is_dirty(self):
        outside = (u"報告 ../前の期の成果/x と /Users/someone/memory.md と ~/x と $HOME", u"/tmp/other/x.csv を読んだ")
        for text in outside:
            def hand(t, f, text=text):
                t.call(u"Bash", {u"command": u'ls "%s"' % f})
                t.call(u"SubagentHandback", {u"message": text})
            got = self.count_of(hand)
            self.assertEqual((2, {u"Bash": 1, u"SubagentHandback": 1}, 0, 0), (got[u"道具の呼び出し"], got[u"道具の名ごと"], got[u"汚れた呼び出し"], got[u"汚れの席"]), text)

            def bash(t, f, text=text):
                t.call(u"Bash", {u"command": u'ls "%s"' % f})
                t.call(u"Bash", {u"command": u"echo " + text})
            got = self.count_of(bash)
            self.assertEqual((1, 1), (got[u"汚れた呼び出し"], got[u"汚れの席"]), text)

    # ---- 直し 1(監査 REVISE): 汚れの根の読み方・走らせた形・黙った変異
    ROOT_NAMES = (u"private", u"Users", u"tmp", u"var", u"etc", u"home", u"opt", u"usr", u"Library", u"Applications", u"Volumes")

    def test_d_17_a_root_name_inside_a_relative_path_is_not_an_outside_path_and_each_root_is_outside_at_the_head(self):
        f = u"/private/tmp/zz/seat"
        v = TAL.folder_variants(f)
        for raw in (u"python3 道具/tmp_x.py", u"cat 道具/var_x.py", u"head 素材/home.csv", u"cat %s/道具/tmp_x.py" % f, u"cat %s/素材/home.csv" % f,
                    u"cat 素材/tmp/x", u"cat a_b/var/x", u"ls ./tmp/a", u"ls ./etc/a", u"ls a-/etc/b", u"ls a./opt/b", u"ls 道具//tmp/x", u"cat 資料/home/x.md"):
            self.assertFalse(TAL.is_dirty(raw, v), raw)
        for name in self.ROOT_NAMES:
            for raw in (u"cat /%s/zz/a" % name, u'cat "/%s/zz/a"' % name, u"cat '/%s/zz/a'" % name, u"x=/%s/zz/a" % name, u"cat (/%s/zz/a)" % name,
                        u"cat a:/%s/zz/a" % name, u"cat a,/%s/zz/a" % name, u"cat a;/%s/zz/a" % name, u"/%s/zz/a" % name):
                self.assertTrue(TAL.is_dirty(raw, v), raw)
        for raw in (u"cat /tmp/other/x.csv", u"cat /home/someone/x.csv", u"ls /tmp", u"cat ../x", u"cat ~/x", u"echo $HOME"):
            self.assertTrue(TAL.is_dirty(raw, v), raw)

        def inside(t, f):
            t.call(u"Bash", {u"command": u"python3 道具/tmp_x.py"})
            t.call(u"Bash", {u"command": u"cat 道具/var_x.py"})
            t.call(u"Bash", {u"command": u"head 素材/home.csv"})
            t.call(u"Read", {u"file_path": f + u"/道具/tmp_x.py"})
            t.call(u"Read", {u"file_path": f + u"/素材/home.csv"})
        got = self.count_of(inside)
        self.assertEqual((5, 0, 0), (got[u"道具の呼び出し"], got[u"汚れた呼び出し"], got[u"汚れの席"]))

        def outside(t, f):
            t.call(u"Bash", {u"command": u"python3 道具/tmp_x.py"})
            t.call(u"Bash", {u"command": u"cat /tmp/other/x.csv"})
            t.call(u"Read", {u"file_path": u"/home/someone/x.csv"})
        got = self.count_of(outside)
        self.assertEqual((2, 1), (got[u"汚れた呼び出し"], got[u"汚れの席"]))

    def test_d_18_a_duplicated_tool_result_id_is_one_result_and_a_duplicated_tool_use_id_is_one_call(self):
        def build(t, f):
            t.call(u"Bash", {u"command": u"ls"}, error=True, dupres=True)
            t.call(u"Bash", {u"command": u"pwd"}, error=True, dup=True, dupres=True)
            t.call(u"Bash", {u"command": u"pwd"}, error=True)
        got = self.count_of(build)
        self.assertEqual((3, 3), (got[u"道具の呼び出し"], got[u"道具が誤りを返した数"]))

    def test_d_19_the_value_table_and_the_document_are_written_by_each_of_the_four_write_tools(self):
        def build(t, f):
            t.call(u"Write", {u"file_path": f + u"/値の表.json", u"content": u"{}"})
            t.call(u"Edit", {u"file_path": f + u"/値の表.json", u"old_string": u"{}", u"new_string": u"{ }"})
            t.call(u"MultiEdit", {u"file_path": f + u"/値の表.json", u"edits": [{u"old_string": u"{ }", u"new_string": u"{}"}]})
            t.call(u"NotebookEdit", {u"notebook_path": f + u"/値の表.json", u"new_source": u"x"})
            t.call(u"Edit", {u"file_path": f + u"/資料.md", u"old_string": u"a", u"new_string": u"b"})
            t.call(u"MultiEdit", {u"file_path": f + u"/資料.md", u"edits": [{u"old_string": u"b", u"new_string": u"c"}]})
            t.call(u"NotebookEdit", {u"notebook_path": f + u"/資料.md", u"new_source": u"x"})
            t.call(u"Read", {u"file_path": f + u"/値の表.json"})
        got = self.count_of(build)
        self.assertEqual((4, 1, 1, 3), (got[u"値の表を書いた回数"], got[u"書き直した"], got[u"最初に値の表を書くまでの呼び出し"], got[u"資料を書いた回数"]))

    def test_d_20_a_carried_tool_counts_as_run_only_in_a_run_form_of_a_bash_call(self):
        tool = u"前の期の成果/道具/x.py"
        for cmd in (u"python3 %s", u"python3 -u %s", u"python %s", u'python3 "%s"', u"sh %s", u"bash %s", u"zsh %s", u"bash -x %s", u"%s", u"./%s", u'"%s"',
                    u"cd /tmp/q && python3 %s", u"echo a; %s", u"echo a | %s", u"(%s)", u"/usr/bin/python3 %s", u"/bin/sh %s", u"/bin/bash %s", u"echo a && (%s)"):
            def build(t, f, cmd=cmd):
                t.call(u"Bash", {u"command": cmd % (f + u"/" + tool)})
            self.assertEqual(1, self.count_of(build, extra_dirs=(u"前の期の成果/道具",))[u"前の期の成果の道具を走らせた"], cmd)

            def build_rel(t, f, cmd=cmd):
                t.call(u"Bash", {u"command": cmd % tool})
            self.assertEqual(1, self.count_of(build_rel, extra_dirs=(u"前の期の成果/道具",))[u"前の期の成果の道具を走らせた"], cmd + u" (相対)")
        for cmd in (u"cat %s", u"cat ./%s", u"ls %s", u"head -3 %s", u"cat %s.sh", u"cat 前の期の成果/道具/run.sh", u"ls 前の期の成果/道具/a.sh 前の期の成果/道具/b.py",
                    u"cat 前の期の成果/道具/x.py | wc -l", u"wc -l ./前の期の成果/道具/x.py", u"diff %s ./前の期の成果/道具/y.py", u"python3 -c 'print(1)'  # %s", u"echo %s", u"echo mypython3 %s", u"echo run.sh %s", u"echo a-sh %s", u"echo (%s)"):
            def build(t, f, cmd=cmd):
                t.call(u"Bash", {u"command": cmd.replace(u"%s", tool) if u"%s" in cmd else cmd})
            self.assertEqual(0, self.count_of(build, extra_dirs=(u"前の期の成果/道具",))[u"前の期の成果の道具を走らせた"], cmd)

        def not_bash(t, f):
            t.call(u"Write", {u"file_path": f + u"/作業の記録.md", u"content": u"python3 %s/%s を使う\nbash %s/%s" % (f, tool, f, tool)})
            t.call(u"Edit", {u"file_path": f + u"/作業の記録.md", u"old_string": u"a", u"new_string": u"sh %s" % tool})
        got = self.count_of(not_bash, extra_dirs=(u"前の期の成果/道具",))
        self.assertEqual((0, 0), (got[u"前の期の成果の道具を走らせた"], got[u"python を走らせた数"]))

    def test_d_21_a_text_that_names_python_is_a_python_run_only_in_a_bash_call(self):
        def build(t, f):
            t.call(u"Write", {u"file_path": f + u"/メモ.md", u"content": u"python3 道具/a.py を走らせる"})
            t.call(u"Bash", {u"command": u"python3 道具/a.py"})
        self.assertEqual(1, self.count_of(build)[u"python を走らせた数"])

    def test_d_23_a_root_right_after_a_redirect_or_file_scheme_is_outside_and_a_tool_directory_is_not(self):
        v = TAL.folder_variants(u"/private/tmp/zz/seat")
        for raw in (u"echo a >/tmp/x", u"echo a 2>/tmp/x", u"cat</etc/passwd", u"cat <</tmp/x", u"open file:///Users/x", u"curl file:///tmp/a"):
            self.assertTrue(TAL.is_dirty(raw, v), raw)
        for raw in (u"/usr/local/bin/python3 道具/a.py", u"/usr/bin/env python3 道具/a.py", u"/usr/bin/python3 道具/a.py"):
            self.assertFalse(TAL.is_dirty(raw, v), raw)
        for raw in (u"cat ///etc/x", u"cat a//tmp/x", u"cat 道具/tmp/x", u"cat afile:///x"):
            self.assertFalse(TAL.is_dirty(raw, v), raw)

    def test_d_24_a_carried_tool_run_needs_a_command_position_and_covers_cd_source_and_value_flags(self):
        tool = u"前の期の成果/道具"

        def ran(cmd):
            def build(t, f):
                t.call(u"Bash", {u"command": cmd.replace(u"TOOL", tool)})
            return self.count_of(build, extra_dirs=(tool,))[u"前の期の成果の道具を走らせた"]
        for cmd in (u"python3 -W ignore TOOL/a.py", u"python3 -X utf8 TOOL/a.py", u"python3 -u -W ignore -X utf8 TOOL/a.py", u"bash -o pipefail TOOL/a.sh",
                    u"cd TOOL && python3 x.py", u"cd /tmp/q/TOOL && python3 x.py", u'cd "TOOL/" && sh x.sh', u"cd TOOL; bash x.sh", u"cd TOOL && ./x", u"cd TOOL\npython3 x.py",
                    u"(cd TOOL && python3 x.py)", u"cd /elsewhere; cd TOOL && python3 x.py",
                    u"source TOOL/env.sh", u". TOOL/env.sh", u"cd /q && . TOOL/env.sh",
                    u"env PYTHONPATH=x python3 TOOL/a.py", u"PYTHONPATH=x python3 TOOL/a.py", u"A=1 B=2 TOOL/a.py", u"/usr/bin/env python3 TOOL/a.py",
                    u"python3 TOOL/a.py 2>&1 | tail -3"):
            self.assertEqual(1, ran(cmd.replace(u"\\n", u"\n")), cmd)
        for cmd in (u"echo python3 TOOL/a.py", u"grep sh TOOL/a.py", u"echo bash TOOL/a.sh", u"grep python3 TOOL/a.py", u"cat TOOL/a.py",
                    u"cd TOOL && cat x.py", u"cd TOOL && ls", u"cd TOOL/sub && python3 x.py", u"cd /elsewhere && python3 x.py", u"cd TOOL; cd /elsewhere; python3 x.py",
                    u"cd TOOL-x && python3 x.py", u"source other.sh TOOL/a.sh", u"echo source TOOL/a.sh", u"echo . TOOL/a.sh", u"cd TOOL && python3 -c 'print(1)'",
                    u"python3 -c 'import runpy; runpy.run_path(\"TOOL/a.py\")'", u"python3 -m pdb TOOL/a.py", u"python3 -m pdb x && cat TOOL/a.py",
                    u"echo a \\\nTOOL/a.py", u"echo a >& TOOL/a.py", u"cd /q/旧TOOL && python3 x.py", u"cat TOOL/a.py; ./x.sh", u"cd /elsewhere && cat TOOL/a.py && ./x", u"cd TOOL && python3 -m pdb x.py",
                    u"python3-config TOOL/a.py", u"python3x TOOL/a.py"):
            self.assertEqual(0, ran(cmd), cmd)

    def test_d_25_a_carried_tool_at_the_head_of_a_later_line_of_one_bash_call_is_run(self):
        tool = u"前の期の成果/道具"

        def build(t, f):
            t.call(u"Bash", {u"command": u"echo start\n%s/a.py\necho end" % tool})
        self.assertEqual(1, self.count_of(build, extra_dirs=(tool,))[u"前の期の成果の道具を走らせた"])

        def build2(t, f):
            t.call(u"Bash", {u"command": u"echo start\npython3 %s/a.py" % tool})
        self.assertEqual(1, self.count_of(build2, extra_dirs=(tool,))[u"前の期の成果の道具を走らせた"])

        def build3(t, f):
            t.call(u"Bash", {u"command": u"echo start\ncat %s/a.py" % tool})
        self.assertEqual(0, self.count_of(build3, extra_dirs=(tool,))[u"前の期の成果の道具を走らせた"])

    def test_d_26_the_record_states_its_limits_and_that_the_run_seats_are_a_lower_bound(self):
        self.assertTrue(all(isinstance(x, str) and x for x in TAL.LIMITS))
        self.assertTrue(any(u"少なく数える側" in x for x in TAL.LIMITS))
        notes = dict(TAL.FIELD_NOTES)
        for p in (1, 2):
            self.assertIn(u"下限", notes[u"過程:期%d:前の期の成果の道具を走らせた席" % p])
        joined = u"\n".join(TAL.LIMITS)
        for w in (u"前の期の成果の道具の script を cp や sed", u"数値が JSON の数", u"listdir・glob", u"走らせ直して書いた回", u"月・日の字の間に空白",
                  u"正解に null が 1 つも無い時", u"ハーネスが folder の外に保存した道具の出力の file", u"汚れを多く数える側"):
            self.assertIn(w, joined)
        self.assertNotIn(u"実際の席の数は記録の数以上)", joined.replace(u"記録の数以上とは言えない", u""))
        for w in (u"cp や sed", u"JSON の数", u"listdir・glob", u"走らせ直して", u"空白が在る形", u"構造上 0", u"ハーネスが folder の外に保存した", u"isApiErrorMessage", u"SubagentHandback"):
            self.assertIn(w, TAL.__doc__)
        doc = TAL.__doc__
        for w in (u"/root", u"/System", u"cd ..", u"${HOME}", u"$PWD/..", u"//tmp", u"/./tmp", u"runpy", u"-m pdb", u"走らせた席は下限"):
            self.assertIn(w, doc)

    def test_d_22_the_process_totals_keep_the_second_period_out_of_the_first(self):
        base = od([(u"状態", u"数えた"), (u"最大の file に触れた", 0), (u"script を書いた数", 0), (u"前の期の成果の道具を走らせた", 0), (u"道具の呼び出し", 0), (u"書き直した", 0),
                   (u"汚れの席", 0), (u"汚れた呼び出し", 0), (u"道具が誤りを返した数", 0), (u"python を走らせた数", 0), (u"前の期の成果の path が出た呼び出し", 0),
                   (u"前の期の素材の path が出た呼び出し", 0), (u"道具の名ごと", {}), (u"秒", 5)])
        on = copy.deepcopy(base)
        on.update([(u"最大の file に触れた", 1), (u"script を書いた数", 3), (u"前の期の成果の道具を走らせた", 1), (u"道具の呼び出し", 7)])
        keys = (u"最大の file に触れた席", u"script を書いた席", u"前の期の成果の道具を走らせた席", u"道具の呼び出しの数")
        for hot, cold in ((2, 1), (1, 2)):
            c = collections.Counter()
            TAL.process_totals(c, {(101, u"a", hot): on, (101, u"a", cold): base}, {}, {})
            for k, want in zip(keys, (1, 1, 1, 7)):
                self.assertEqual(want, c[u"過程:期%d:%s" % (hot, k)], (hot, k))
                self.assertEqual(0, c[u"過程:期%d:%s" % (cold, k)], (cold, k))

    def test_d_13_only_an_error_flag_that_is_true_counts_as_an_error(self):
        def build(t, f):
            t.call(u"Bash", {u"command": u"ls"}, error=True)
            t.call(u"Bash", {u"command": u"ls"})
            t.lines.append(json.dumps({u"type": u"user", u"message": {u"role": u"user", u"content": [{u"type": u"tool_result", u"tool_use_id": u"x1", u"is_error": False, u"content": u"ok"}]}}))
            t.lines.append(json.dumps({u"type": u"user", u"message": {u"role": u"user", u"content": [{u"type": u"tool_result", u"tool_use_id": u"x2", u"is_error": u"yes", u"content": u"ok"}]}}))
        self.assertEqual(1, self.count_of(build)[u"道具が誤りを返した数"])

    def test_d_14_a_carried_tool_counts_as_run_only_when_a_run_command_names_it(self):
        def build(t, f):
            t.call(u"Read", {u"file_path": f + u"/前の期の成果/道具/x.py"})
            t.call(u"Bash", {u"command": u'cat "%s/前の期の成果/道具/x.py"' % f})
            t.call(u"Bash", {u"command": u'ls "%s/前の期の成果/道具"' % f})
        got = self.count_of(build, extra_dirs=(u"前の期の成果/道具",))
        self.assertEqual((3, 0, 0), (got[u"前の期の成果の path が出た呼び出し"], got[u"前の期の成果の道具を走らせた"], got[u"python を走らせた数"]))

        def build2(t, f):
            t.call(u"Bash", {u"command": u'python3 "%s/前の期の成果/道具/x.py"' % f})
        self.assertEqual(1, self.count_of(build2, extra_dirs=(u"前の期の成果/道具",))[u"前の期の成果の道具を走らせた"])

        def build3(t, f):
            t.call(u"Bash", {u"command": u'bash "%s/前の期の成果/道具/x.sh"' % f})
        self.assertEqual(1, self.count_of(build3, extra_dirs=(u"前の期の成果/道具",))[u"前の期の成果の道具を走らせた"])

    def test_d_15_the_first_user_text_skips_meta_messages_and_the_path_must_end_there(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, u"期1")
            other = os.path.join(tmp, u"期10")
            t = TB(os.path.join(tmp, u"t", u"meta.output"), u"x")
            t.lines[0] = json.dumps({u"type": u"user", u"isMeta": True, u"message": {u"role": u"user", u"content": u"folder `%s`" % other}})
            t.add({u"type": u"user", u"message": {u"role": u"user", u"content": u"folder `%s`" % f}})
            t.call(u"Bash", {u"command": u"ls"})
            t.save()
            t2 = TB(os.path.join(tmp, u"t", u"ten.output"), u"folder `%s` です" % other)
            t2.call(u"Bash", {u"command": u"ls"})
            t2.save()
            idx = TAL.Transcripts(os.path.join(tmp, u"t"))
            self.assertEqual([os.path.join(tmp, u"t", u"meta.output")], idx.match(f))
            self.assertEqual([os.path.join(tmp, u"t", u"ten.output")], idx.match(other))

    def test_d_9_the_totals_of_the_process_in_the_tally(self):
        n = self.n
        want = {
            u"過程:期1:席の数": 4, u"過程:期1:数えられない席": 3, u"過程:期2:席の数": 4, u"過程:期2:数えられない席": 3, u"過程:数えた席": 2, u"過程:数えられない席": 6,
            u"過程:期1:最大の file に触れた席": 1, u"過程:期2:最大の file に触れた席": 0, u"過程:期1:script を書いた席": 1, u"過程:期2:script を書いた席": 0,
            u"過程:期1:前の期の成果の道具を走らせた席": 0, u"過程:期2:前の期の成果の道具を走らせた席": 1, u"過程:期1:道具の呼び出しの数": 10, u"過程:期2:道具の呼び出しの数": 10,
            u"過程:期1:道具の呼び出しの中央値の 2 倍": 20, u"過程:期2:道具の呼び出しの中央値の 2 倍": 20, u"過程:値の表を 2 回以上書いた席": 1, u"過程:汚れの席": 1,
            u"過程:汚れた呼び出し": 2, u"過程:道具が誤りを返した数": 1, u"過程:python を走らせた数": 3, u"過程:script を書いた数": 2, u"過程:秒の合計": 410, u"過程:秒が無い席": 0,
            u"過程:道具:Read": 4, u"過程:道具:Bash": 11, u"過程:道具:Write": 5, u"過程:前の期の成果の path が出た呼び出し": 3, u"過程:前の期の素材の path が出た呼び出し": 1,
            u"B の席:席の数": 2, u"B の席:数えた席": 1, u"B の席:数えられない席": 1, u"B の席:記録が無い席": 1, u"B の席:最大の file に触れた席": 1, u"B の席:script を書いた席": 1,
            u"B の席:道具の呼び出しの数": 4, u"B の席:汚れの席": 0, u"B の席:python を走らせた数": 1, u"B の席:道具が誤りを返した数": 0, u"B の席:秒が無い席": 1, u"B の席:秒の合計": 0,
        }
        for k, v in want.items():
            self.assertEqual(v, n(k), k)

    def test_d_10_the_results_without_the_dirty_seats_are_listed_next_to_the_whole(self):
        n = self.n
        # 汚れた席は 101 a 期 2。外した後の期 2 の行の数は 120 から 30 引く(その席は 30 行)。期 1 は外れない
        self.assertEqual(120, n(u"汚れの席を外した:期1:行の数"))
        self.assertEqual(90, n(u"汚れの席を外した:期2:行の数"))
        self.assertEqual(120, n(u"期2:行の数"))
        self.assertEqual(53 - 26, n(u"汚れの席を外した:期2:結果:同じ"))
        self.assertEqual(1 - 1, n(u"汚れの席を外した:期2:結果:無いのに在る"))

    def test_d_11_seats_are_listed_by_company_round_and_period_with_numbers_only(self):
        s = self.rec2[u"席ごと"]
        self.assertEqual(8, len(s))
        self.assertEqual(sorted([u"%d:%s:%d" % (i, r, p) for i in (101, 102) for r in (u"a", u"b") for p in (1, 2)]), sorted(s))
        self.assertEqual((1, 10, 21, 2), (s[u"101:a:1"][u"数えた"], s[u"101:a:1"][u"道具の呼び出し"], s[u"101:a:1"][u"結果:同じ"], s[u"101:a:1"][u"結果:違う"]))
        self.assertEqual((0, 30), (s[u"102:b:2"][u"数えた"], s[u"102:b:2"][u"結果:答えなし"]))
        self.assertEqual(1, s[u"101:a:2"][u"汚れの席"])
        self.assertEqual(1, self.rec2[u"B の席ごと"][u"101"][u"秒が無い"])


# ======================================================================== 6. 予測の判定(境の 1 つ下と 1 つ上)
def rec_of(**kw):
    c = collections.Counter()
    for k, v in kw.items():
        c[k.replace(u"__", u":").replace(u"_x_", u"×")] = v
    return {u"数": dict(c), u"会社の数": 4, u"回": [u"a", u"b"]}


def put(c, **kv):
    c.update(kv)
    return c


class JudgeTest(unittest.TestCase):
    def j(self, counts, pid, companies=4, rounds=(u"a", u"b")):
        rec = {u"数": counts, u"会社の数": companies, u"回": list(rounds)}
        return TAL.judge(rec)[pid][u"当たり"]

    def test_e_1_a1_and_a4_flip_at_216_of_240(self):
        for pid, p in ((u"UM3-A1", 1), (u"UM3-A4", 2)):
            base = {u"期%d:行の数" % p: 240}
            self.assertTrue(self.j(put(dict(base), **{u"期%d:結果:同じ" % p: 200, u"期%d:結果:無いで同じ" % p: 16}), pid))
            self.assertFalse(self.j(put(dict(base), **{u"期%d:結果:同じ" % p: 200, u"期%d:結果:無いで同じ" % p: 15}), pid))
            self.assertTrue(self.j(put(dict(base), **{u"期%d:結果:同じ" % p: 217}), pid))
            self.assertIsNone(self.j({u"期%d:行の数" % p: 239, u"期%d:結果:同じ" % p: 239}, pid))

    def test_e_2_a2_flips_at_90_percent_present_and_85_percent_same(self):
        def c(stopped, present, same):
            d = {u"掛け合わせ1:止める×同じ": same, u"掛け合わせ1:止める×違う": present - same, u"掛け合わせ1:止める×分からない": stopped - present}
            return d
        self.assertTrue(self.j(c(100, 90, 77), u"UM3-A2"))
        self.assertFalse(self.j(c(100, 89, 89), u"UM3-A2"))
        self.assertFalse(self.j(c(100, 100, 84), u"UM3-A2"))
        self.assertTrue(self.j(c(100, 100, 85), u"UM3-A2"))
        self.assertFalse(self.j(c(100, 90, 76), u"UM3-A2"))
        self.assertIsNone(self.j({}, u"UM3-A2"))
        self.assertFalse(self.j({u"掛け合わせ1:止める×分からない": 10}, u"UM3-A2"))

    def test_e_2b_a2_counts_a_stopped_row_the_seat_filled_though_the_gold_has_none_as_present(self):
        d = {u"掛け合わせ1:止める×同じ": 8, u"掛け合わせ1:止める×無いのに在る": 1, u"掛け合わせ1:止める×無いで同じ": 1}
        out = TAL.judge({u"数": d, u"会社の数": 4, u"回": [u"a", u"b"]})[u"UM3-A2"]
        self.assertEqual((10, 9, 8, True), (out[u"止めた行"], out[u"在る"], out[u"同じ"], out[u"当たり"]))

    def test_e_3_a3_and_a6_need_at_least_one(self):
        rows = {u"期1:行の数": 240, u"期2:行の数": 240}
        self.assertTrue(self.j(put(dict(rows), **{u"期2:結果:違う": 1}), u"UM3-A3"))
        self.assertTrue(self.j(put(dict(rows), **{u"期1:結果:無いのに在る": 1}), u"UM3-A3"))
        self.assertFalse(self.j(dict(rows), u"UM3-A3"))
        self.assertIsNone(self.j({u"期1:行の数": 240, u"期2:行の数": 239, u"期2:結果:違う": 3}, u"UM3-A3"))
        self.assertTrue(self.j(put(dict(rows), **{u"期2:結果:無いのに在る": 1}), u"UM3-A6"))
        self.assertFalse(self.j(put(dict(rows), **{u"期2:結果:違う": 5}), u"UM3-A6"))

    def test_e_4_a5_flips_at_80_percent(self):
        self.assertTrue(self.j({u"掛け合わせ2:確認待ち×同じ": 80, u"掛け合わせ2:確認待ち×違う": 20}, u"UM3-A5"))
        self.assertFalse(self.j({u"掛け合わせ2:確認待ち×同じ": 79, u"掛け合わせ2:確認待ち×違う": 21}, u"UM3-A5"))
        self.assertTrue(self.j({u"掛け合わせ2:確認待ち×同じ": 8, u"掛け合わせ2:確認待ち×違う": 2}, u"UM3-A5"))
        self.assertFalse(self.j({u"掛け合わせ2:確認待ち×同じ": 7, u"掛け合わせ2:確認待ち×違う": 3}, u"UM3-A5"))
        self.assertIsNone(self.j({}, u"UM3-A5"))

    def test_e_5_a7_flips_at_two_companies_of_four(self):
        self.assertTrue(self.j({u"揺れ:期1:数値が違う行が在る社": 2}, u"UM3-A7"))
        self.assertFalse(self.j({u"揺れ:期1:数値が違う行が在る社": 1}, u"UM3-A7"))
        self.assertIsNone(self.j({u"揺れ:期1:数値が違う行が在る社": 2}, u"UM3-A7", companies=3))
        self.assertIsNone(self.j({u"揺れ:期1:数値が違う行が在る社": 2}, u"UM3-A7", rounds=(u"a",)))
        self.assertFalse(self.j({u"揺れ:期2:数値が違う行が在る社": 4}, u"UM3-A7"))

    def test_e_6_a8_is_half_or_more_and_is_not_judged_without_wrong_rows(self):
        self.assertTrue(self.j({u"期1:結果:違う": 3, u"期2:結果:無いのに在る": 1, u"自信:高×違う": 2}, u"UM3-A8"))
        self.assertFalse(self.j({u"期1:結果:違う": 3, u"自信:高×違う": 1}, u"UM3-A8"))           # 1/3 は半分未満
        self.assertTrue(self.j({u"期1:結果:違う": 2, u"自信:高×違う": 1}, u"UM3-A8"))            # ちょうど半分
        self.assertFalse(self.j({u"期1:結果:違う": 3, u"期2:結果:無いのに在る": 1, u"自信:高×違う": 1}, u"UM3-A8"))
        self.assertTrue(self.j({u"期1:結果:違う": 3, u"期2:結果:無いのに在る": 1, u"自信:高×違う": 1, u"自信:高×無いのに在る": 1}, u"UM3-A8"))
        self.assertIsNone(self.j({u"自信:高×違う": 1}, u"UM3-A8"))

    def test_e_7_a9_flips_at_95_percent(self):
        self.assertTrue(self.j({u"関係:見られる本数": 100, u"関係:成り立つ本数": 95}, u"UM3-A9"))
        self.assertFalse(self.j({u"関係:見られる本数": 100, u"関係:成り立つ本数": 94}, u"UM3-A9"))
        self.assertTrue(self.j({u"関係:見られる本数": 20, u"関係:成り立つ本数": 19}, u"UM3-A9"))
        self.assertFalse(self.j({u"関係:見られる本数": 20, u"関係:成り立つ本数": 18}, u"UM3-A9"))
        self.assertIsNone(self.j({u"関係:見られる本数": 0, u"関係:成り立つ本数": 0}, u"UM3-A9"))

    def seats(self, **kw):
        base = {u"過程:期1:席の数": 8, u"過程:期2:席の数": 8}
        base.update(kw)
        return base

    def test_e_8_l1_and_l2_flip_at_six_of_eight_and_wait_when_a_seat_cannot_be_counted(self):
        for pid, key in ((u"UM3-L1", u"過程:期1:最大の file に触れた席"), (u"UM3-L2", u"過程:期1:script を書いた席")):
            self.assertTrue(self.j(self.seats(**{key: 6}), pid))
            self.assertFalse(self.j(self.seats(**{key: 5}), pid))
            self.assertIsNone(self.j(self.seats(**{key: 5, u"過程:期1:数えられない席": 1}), pid))
            self.assertTrue(self.j(self.seats(**{key: 6, u"過程:期1:数えられない席": 2}), pid))
            self.assertIsNone(self.j({key: 8, u"過程:期1:席の数": 7}, pid))

    def test_e_9_l3_flips_at_three_and_four(self):
        key = u"過程:期2:前の期の成果の道具を走らせた席"
        self.assertTrue(self.j(self.seats(**{key: 3}), u"UM3-L3"))
        self.assertFalse(self.j(self.seats(**{key: 4}), u"UM3-L3"))
        self.assertIsNone(self.j(self.seats(**{key: 3, u"過程:期2:数えられない席": 1}), u"UM3-L3"))
        self.assertFalse(self.j(self.seats(**{key: 4, u"過程:期2:数えられない席": 1}), u"UM3-L3"))

    def test_e_10_l4_needs_the_second_period_median_to_be_smaller(self):
        k1, k2 = u"過程:期1:道具の呼び出しの中央値の 2 倍", u"過程:期2:道具の呼び出しの中央値の 2 倍"
        self.assertTrue(self.j(self.seats(**{k1: 21, k2: 20}), u"UM3-L4"))
        self.assertFalse(self.j(self.seats(**{k1: 20, k2: 20}), u"UM3-L4"))
        self.assertFalse(self.j(self.seats(**{k1: 20, k2: 21}), u"UM3-L4"))
        self.assertIsNone(self.j(self.seats(**{k1: 30, k2: 20, u"過程:期2:数えられない席": 1}), u"UM3-L4"))
        self.assertIsNone(self.j(self.seats(**{k1: 30}), u"UM3-L4"))

    def test_e_11_l5_l6_and_d1_flip_at_their_sealed_numbers(self):
        self.assertTrue(self.j(self.seats(**{u"過程:値の表を 2 回以上書いた席": 4}), u"UM3-L5"))
        self.assertFalse(self.j(self.seats(**{u"過程:値の表を 2 回以上書いた席": 3}), u"UM3-L5"))
        self.assertIsNone(self.j(self.seats(**{u"過程:値の表を 2 回以上書いた席": 3, u"過程:期1:数えられない席": 1}), u"UM3-L5"))
        self.assertTrue(self.j(self.seats(), u"UM3-L6"))
        self.assertFalse(self.j(self.seats(**{u"過程:汚れの席": 1}), u"UM3-L6"))
        self.assertFalse(self.j(self.seats(**{u"過程:汚れの席": 1, u"過程:期2:数えられない席": 3}), u"UM3-L6"))
        self.assertIsNone(self.j(self.seats(**{u"過程:期2:数えられない席": 1}), u"UM3-L6"))
        self.assertTrue(self.j(self.seats(**{u"資料:当たらない数の字が 1 つ以上の資料": 8, u"資料:本数": 10}), u"UM3-D1"))
        self.assertFalse(self.j(self.seats(**{u"資料:当たらない数の字が 1 つ以上の資料": 7, u"資料:本数": 16}), u"UM3-D1"))
        self.assertIsNone(self.j(self.seats(**{u"資料:当たらない数の字が 1 つ以上の資料": 7, u"資料:本数": 15}), u"UM3-D1"))

    def test_e_12_the_judge_names_the_sixteen_and_reads_only_the_counts(self):
        out = TAL.judge({u"数": {}, u"会社の数": 4, u"回": [u"a", u"b"]})
        self.assertEqual(sorted(TAL.BOUNDS), sorted(out))
        self.assertEqual(16, len(out))
        self.assertEqual(16, len(TAL.judge({})))
        self.assertEqual(16, len(TAL.judge({u"数": {u"期1:行の数": u"x"}})))


# ======================================================================== 7. --hand
def make_hand_world(tmp):
    co, seat, root = [os.path.join(tmp, x) for x in (u"co", u"seat", u"root")]
    for i in (101, 102):
        for p in (1, 2):
            materials(os.path.join(co, str(i)), u"期%d" % p)
            wtext(os.path.join(co, str(i), u"期%d" % p, u"期印.txt"), u"期%d の素材" % p)
            wjson(os.path.join(seat, str(i), u"指定_期%d_A.json" % p), {u"成果物": u"A", u"期": p})
        wjson(os.path.join(co, str(i), u"正解", u"正解.json"), {u"期1": {}})
        wtext(os.path.join(co, str(i), u"作り方", u"作る.py"), u"x\n")
    brief = os.path.join(tmp, u"brief.md")
    wtext(brief, u"# 頼みの紙\n")
    return dict(co=co, seat=seat, root=root, brief=brief, definition=os.path.join(ROOT, TAL.DEFS_REL))


def hand_args(w, i, r, p):
    return ["--hand", "--co", w["co"], "--seat", w["seat"], "--definition", w["definition"], "--brief", w["brief"], "--root", w["root"],
            "--company", str(i), "--round", r, "--period", str(p)]


def tree(folder):
    out = []
    for d, ds, fs in os.walk(folder):
        for n in ds + fs:
            out.append(os.path.relpath(os.path.join(d, n), folder))
    return sorted(out)


class HandTest(unittest.TestCase):
    def test_f_1_period_one_folder_has_the_brief_the_spec_the_definition_and_the_material_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = make_hand_world(tmp)
            rc, out, _e = run_cli(hand_args(w, 101, u"a", 1))
            self.assertEqual(0, rc, out)
            dest = os.path.join(w["root"], u"101", u"a", u"期1")
            self.assertEqual(sorted([u"definition_A.json", u"指定.json", u"素材", u"素材/仕訳帳.csv", u"素材/在庫.csv", u"素材/月次.csv", u"素材/期印.txt", u"頼み.md"]), tree(dest))
            self.assertEqual(u"期1 の素材", read_text(os.path.join(dest, u"素材", u"期印.txt")))
            self.assertEqual(read_bytes_abs(w["definition"]), read_bytes_abs(os.path.join(dest, u"definition_A.json")))
            self.assertEqual(read_bytes_abs(w["brief"]), read_bytes_abs(os.path.join(dest, u"頼み.md")))
            self.assertEqual(json.loads(read_text(os.path.join(dest, u"指定.json"))), {u"成果物": u"A", u"期": 1})
            self.assertEqual(read_bytes_abs(os.path.join(w["co"], u"101", u"期1", u"月次.csv")), read_bytes_abs(os.path.join(dest, u"素材", u"月次.csv")))
            self.assertEqual(0, json.loads(out)[u"禁止の名の問題"])

    def test_f_2_period_two_copies_the_same_rounds_period_one_outputs_and_counts_the_missing_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = make_hand_world(tmp)
            self.assertEqual(0, run_cli(hand_args(w, 101, u"a", 1))[0])
            self.assertEqual(0, run_cli(hand_args(w, 101, u"b", 1))[0])
            a1 = os.path.join(w["root"], u"101", u"a", u"期1")
            b1 = os.path.join(w["root"], u"101", u"b", u"期1")
            for f, tag in ((a1, u"A"), (b1, u"B")):
                wtext(os.path.join(f, u"資料.md"), tag + u"資料")
                wtext(os.path.join(f, u"値の表.json"), u'{"行": []}' + tag)
                wtext(os.path.join(f, u"道具", u"x.py"), tag + u"print(1)")
            wtext(os.path.join(a1, u"作業の記録.md"), u"Aの記録")          # b には記録が無い
            rc, out, _e = run_cli(hand_args(w, 101, u"a", 2))
            self.assertEqual(0, rc, out)
            self.assertEqual((4, 0), (json.loads(out)[u"前の期の成果を写した数"], json.loads(out)[u"前の期の成果が無かった数"]))
            rc, out, _e = run_cli(hand_args(w, 101, u"b", 2))
            self.assertEqual(0, rc, out)
            self.assertEqual((3, 1), (json.loads(out)[u"前の期の成果を写した数"], json.loads(out)[u"前の期の成果が無かった数"]))
            da = os.path.join(w["root"], u"101", u"a", u"期2")
            db = os.path.join(w["root"], u"101", u"b", u"期2")
            self.assertEqual(u"A資料", read_text(os.path.join(da, u"前の期の成果", u"資料.md")))
            self.assertEqual(u"B資料", read_text(os.path.join(db, u"前の期の成果", u"資料.md")))             # 同じ回の成果
            self.assertEqual(u"Bprint(1)", read_text(os.path.join(db, u"前の期の成果", u"道具", u"x.py")))
            self.assertFalse(os.path.exists(os.path.join(db, u"前の期の成果", u"作業の記録.md")))
            self.assertTrue(os.path.exists(os.path.join(da, u"前の期の素材", u"仕訳帳.csv")))
            self.assertEqual(u"期1 の素材", read_text(os.path.join(da, u"前の期の素材", u"期印.txt")))
            self.assertEqual(u"期2 の素材", read_text(os.path.join(da, u"素材", u"期印.txt")))
            self.assertEqual(u"期2 の素材", read_text(os.path.join(db, u"素材", u"期印.txt")))
            self.assertEqual(sorted([u"definition_A.json", u"指定.json", u"素材", u"前の期の素材", u"前の期の成果", u"頼み.md"]), sorted(n for n in tree(da) if os.sep not in n))
            self.assertEqual(json.loads(read_text(os.path.join(da, u"指定.json"))), {u"成果物": u"A", u"期": 2})

    def test_f_3_no_gold_no_how_to_and_no_other_brief_land_in_the_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = make_hand_world(tmp)
            self.assertEqual(0, run_cli(hand_args(w, 102, u"a", 1))[0])
            self.assertEqual(0, run_cli(hand_args(w, 102, u"a", 2))[0])
            for p in (1, 2):
                for rel in tree(os.path.join(w["root"], u"102", u"a", u"期%d" % p)):
                    for bad in (u"正解", u"作り方"):
                        self.assertNotIn(bad, rel)
                    self.assertTrue(not rel.endswith(u"頼み.md") or rel == u"頼み.md", rel)
            self.assertEqual([], TAL.hand_problems(os.path.join(w["root"], u"102", u"a", u"期1"), w["brief"]))
            d = os.path.join(w["root"], u"102", u"a", u"期1")
            os.makedirs(os.path.join(d, u"素材", u"正解"))
            wtext(os.path.join(d, u"素材", u"頼み.md"), u"便 UM2 の頼み")
            wtext(os.path.join(d, u"頼み.md"), u"違う紙")
            got = TAL.hand_problems(d, w["brief"])
            self.assertEqual(3, len(got), got)
            self.assertEqual([u"頼みの紙が読めない"], TAL.hand_problems(d, os.path.join(tmp, u"無い")))

    def test_f_4_a_forbidden_name_in_the_source_stops_before_anything_is_made(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = make_hand_world(tmp)
            os.makedirs(os.path.join(w["co"], u"101", u"期1", u"正解"))
            rc, _o, _e = run_cli(hand_args(w, 101, u"a", 1))
            self.assertEqual(5, rc)
            self.assertFalse(os.path.exists(os.path.join(w["root"], u"101", u"a", u"期1")))

    def test_f_5_prior_outputs_that_hold_a_forbidden_name_end_with_a_nonzero_rc(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = make_hand_world(tmp)
            self.assertEqual(0, run_cli(hand_args(w, 101, u"a", 1))[0])
            a1 = os.path.join(w["root"], u"101", u"a", u"期1")
            wtext(os.path.join(a1, u"道具", u"作り方", u"y.py"), u"x")
            rc, out, _e = run_cli(hand_args(w, 101, u"a", 2))
            self.assertEqual(6, rc)
            self.assertEqual(1, json.loads(out)[u"禁止の名の問題"])

    def test_f_6_an_existing_destination_is_left_alone_and_a_missing_source_makes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = make_hand_world(tmp)
            dest = os.path.join(w["root"], u"101", u"a", u"期1")
            wtext(os.path.join(dest, u"keep.txt"), u"keep")
            before = tree(dest)
            self.assertEqual(3, run_cli(hand_args(w, 101, u"a", 1))[0])
            self.assertEqual(before, tree(dest))
            self.assertEqual(u"keep", read_text(os.path.join(dest, u"keep.txt")))
            self.assertEqual(4, run_cli(hand_args(w, 102, u"a", 2))[0])            # 期 1 の folder が無い
            self.assertFalse(os.path.exists(os.path.join(w["root"], u"102", u"a", u"期2")))
            self.assertEqual(4, run_cli(hand_args(w, 999, u"a", 1))[0])
            for bad in (["--round", "c"], ["--period", "3"], ["--period", "x"], ["--company", "y"]):
                args = hand_args(w, 101, u"b", 1)
                k = args.index(bad[0])
                args[k + 1] = bad[1]
                self.assertEqual(2, run_cli(args)[0], bad)
            self.assertEqual(2, run_cli(["--hand"])[0])


def read_bytes_abs(path):
    with open(path, "rb") as fh:
        return fh.read()


# ======================================================================== 8. 落ちない・記録
class CrashTest(unittest.TestCase):
    def test_g_1_tally_on_nothing_counts_everything_as_no_answer_and_does_not_fall(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = TAL.tally((101,), os.path.join(tmp, u"x"), os.path.join(tmp, u"y"), os.path.join(tmp, u"z"), os.path.join(tmp, u"t"), os.path.join(tmp, u"h"))
        self.assertEqual(1, rec[u"数"][u"正解が読めない社"])
        self.assertEqual(0, rec[u"数"][u"期1:行の数"])
        rc, out, err = run_cli(["--tally", "--co", "/nonexistent/a", "--seat", "/nonexistent/b", "--root", "/nonexistent/c", "--transcripts", "/nonexistent/d", "--companies", "101"])
        self.assertEqual(0, rc, err)
        json.loads(out)

    def test_g_2_a_broken_gold_a_deep_json_and_a_huge_value_do_not_crash_the_tally(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = build_world(tmp)
            wtext(os.path.join(w["co"], u"101", u"正解", u"正解.json"), u"[" * 100000)
            wtext(os.path.join(w["co"], u"102", u"正解", u"正解.json"), json.dumps(gold_file(GOLD[(102, 1)], GOLD[(102, 2)])))
            wtext(os.path.join(w["root"], u"102", u"a", u"期1", u"値の表.json"), u"[" * 100000)
            wjson(os.path.join(w["root"], u"102", u"b", u"期1", u"値の表.json"), {u"行": [{u"id": u"a01", u"状態": u"在る", u"数値": u"9" * 100000, u"自信": u"高"}, None, {u"id": 5}]})
            wtext(os.path.join(w["root"], u"102", u"a", u"期2", u"資料.md"), u"9" * 200000 + u"\n" + u"1.5 " * 1000)
            rec = TAL.tally((101, 102), w["co"], w["seat"], w["root"], w["tdir"], w["hand2"], (u"a", u"b"))
        self.assertEqual(1, rec[u"数"][u"正解が読めない社"])
        self.assertEqual((31, 29, 60), (rec[u"数"][u"期1:結果:形が読めない"], rec[u"数"][u"期1:結果:答えなし"], rec[u"数"][u"期1:行の数"]))      # 102 a は全行・102 b は a01 だけ(9 が 10 万個)

    def test_g_3_main_never_raises_for_odd_arguments(self):
        for args in (["--tally", "--companies", "x"], ["--process"], ["--process", "--folder"], ["--digest", "--root"], ["--tally", "--co"], ["--hand", "--process"],
                     ["--process", "--transcripts", "/nonexistent", "--folder", "/nonexistent/f"], ["--tally", "--co", "/", "--seat", "/", "--root", "/", "--companies", "-1"]):
            rc = TAL.main(args)
            self.assertIsInstance(rc, int, args)

    def test_g_6_main_turns_any_exception_into_a_message_and_rc_one(self):
        import contextlib
        from unittest import mock
        for exc in (ValueError(u"x"), OSError(u"y"), ZeroDivisionError(), RecursionError(), UnicodeDecodeError("utf-8", b"\xff", 0, 1, u"z"), TypeError(u"t")):
            err = io.StringIO()
            with mock.patch.object(TAL, "_main", side_effect=exc), contextlib.redirect_stderr(err):
                rc = TAL.main(["--tally"])
            self.assertEqual(1, rc, repr(exc))
            self.assertIn(type(exc).__name__, err.getvalue())

    def test_g_7_the_default_rounds_are_both_rounds_for_tally_process_and_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = build_world(tmp)
            rc, out, err = run_cli(["--tally", "--co", w["co"], "--seat", w["seat"], "--root", w["root"], "--transcripts", w["tdir"], "--um2-hand", w["hand2"], "--companies", "101", "102"])
            self.assertEqual(0, rc, err)
            got = json.loads(out)
            self.assertEqual([u"a", u"b"], got[u"回"])
            self.assertEqual(60, got[u"数"][u"揺れ:期1:行の数"])
            rc, out, err = run_cli(["--process", "--transcripts", w["tdir"], "--root", w["root"], "--companies", "101"])
            self.assertEqual(0, rc, err)
            self.assertEqual(4, len(json.loads(out)))
            out_dir = os.path.join(tmp, u"抜き書き")
            rc, out, err = run_cli(["--digest", "--root", w["root"], "--transcripts", w["tdir"], "--um2-hand", w["hand2"], "--companies", "101", "--out-dir", out_dir])
            self.assertEqual(0, rc, err)
            self.assertIn(u"101_a_期1.md", os.listdir(out_dir))
            self.assertNotIn(u"101_b_期1.md", os.listdir(out_dir))        # 回 b 期 1 は記録が対応しない(数えられない席は書かない)
            self.assertIn(u"101_a_期2.md", os.listdir(out_dir))

    def test_g_4_process_command_prints_the_counts_for_the_given_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = build_world(tmp)
            rc, out, err = run_cli(["--process", "--transcripts", w["tdir"], "--folder", os.path.join(w["root"], u"101", u"a", u"期1"), os.path.join(w["root"], u"102", u"a", u"期1")])
            self.assertEqual(0, rc, err)
            got = json.loads(out)
            self.assertEqual([u"数えた", u"過程が数えられない"], [v[u"状態"] for v in got.values()])
            rc, out, err = run_cli(["--process", "--transcripts", w["tdir"], "--root", w["root"], "--companies", "101", "--rounds", "a"])
            self.assertEqual(0, rc, err)
            self.assertEqual(2, len(json.loads(out)))

    def test_g_5_digest_writes_one_file_per_counted_seat_outside_the_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = build_world(tmp)
            out_dir = os.path.join(tmp, u"抜き書き")
            rc, out, err = run_cli(["--digest", "--root", w["root"], "--transcripts", w["tdir"], "--um2-hand", w["hand2"], "--companies", "101", "--rounds", "a", "--out-dir", out_dir])
            self.assertEqual(0, rc, err)
            self.assertEqual(sorted([u"101_a_期1.md", u"101_a_期2.md", u"B_101.md"]), sorted(os.listdir(out_dir)))
            body = read_text(os.path.join(out_dir, u"101_a_期1.md"))
            self.assertEqual(10, len(re.findall(r"^[0-9]+\. ", body, re.M)))
            self.assertIn(u"見ます", body)
            self.assertIn(u"## 作業の記録", body)
            self.assertIn(u"a02 | 在る | 自信 低", body)
            self.assertFalse(os.path.abspath(out_dir).startswith(REPO))


FORBIDDEN_WORDS = (u".csv", u".json", u".md", u".py", u".xlsx", u"仕訳帳", u"売上高", u"純資産", u"現金", u"借入金", u"営業利益", u"経常利益", u"減価償却", u"勘定", u"円", u"/private", u"/Users", u"scratchpad")


def record_problems(rec, companies=(1, 2, 3, 4)):
    out = []
    keys = [u"会社の数", u"回", u"数", u"会社ごと", u"席ごと", u"B の席ごと", u"読んだ便 UM2 の出力の sha256 の束ね", u"限界", u"欄の説明", u"予測"]
    if not isinstance(rec, dict) or sorted(rec) != sorted(keys):
        return [u"記録の頂の鍵"]
    sha = rec[u"読んだ便 UM2 の出力の sha256 の束ね"]
    if not isinstance(sha, str) or not re.match(r"^[0-9a-f]{64}\Z", sha):
        out.append(u"sha256 の形")
    body = json.dumps(dict((k, v) for k, v in rec.items() if k != u"読んだ便 UM2 の出力の sha256 の束ね"), ensure_ascii=False)
    for w in FORBIDDEN_WORDS:
        if w in body:
            out.append(u"記録に禁止の字: " + w)
    if re.search(u"[0-9]{4}-[0-9]{2}-[0-9]{2}", body):
        out.append(u"日付の形")
    if re.search(u"[0-9]{6,}", body):
        out.append(u"長い数(額の形)")
    if rec[u"会社の数"] != len(companies):
        out.append(u"会社の数")
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in rec[u"数"].values()):
        out.append(u"数が整数でない")
    for k in TAL.FIXED_COUNTS:
        if k not in rec[u"数"]:
            out.append(u"数の欄が無い: " + k)
    if not set(rec[u"会社ごと"]) <= set(str(i) for i in companies):
        out.append(u"会社ごとの会社")
    for row in list(rec[u"席ごと"].values()) + list(rec[u"B の席ごと"].values()):
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in row.values()):
            out.append(u"席ごとが整数でない")
    if sorted(rec[u"予測"]) != sorted(TAL.BOUNDS):
        out.append(u"予測の数")
    for v in rec[u"予測"].values():
        if v[u"当たり"] not in (True, False, None):
            out.append(u"当たりの値")
    if not rec[u"限界"] or not all(isinstance(x, str) and x for x in rec[u"限界"]):
        out.append(u"限界の欄")
    if not any(u"下限" in v for v in rec[u"欄の説明"].values()):
        out.append(u"欄の説明に下限が無い")
    return out


class RecordTest(World):
    def test_h_1_the_record_state_is_stated_and_checked(self):
        path = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(path):
            self.assertFalse(os.path.exists(path), u"記録はまだ無い(本番は未実行。記録の無い状態で緑)")
            return
        self.assertEqual([], record_problems(json.loads(read(RECORD_REL))))

    def test_h_2_the_record_the_script_builds_has_the_shape_and_no_forbidden_word(self):
        rec = json.loads(json.dumps(self.rec2, ensure_ascii=False))
        self.assertEqual([], record_problems(rec, companies=(101, 102)))
        self.assertNotEqual([], record_problems(rec))              # 本番の 4 社でない記録は本番の形として赤

    def test_h_3_the_record_check_turns_red_for_a_forbidden_word_a_value_a_wrong_count_and_a_missing_key(self):
        good = json.loads(json.dumps(self.rec2, ensure_ascii=False))
        for word in (u"仕訳帳.csv", u"値の表.json", u"資料.md", u"売上高", u"2024-04-01", u"1234567", u"勘定甲03", u"3,000円"):
            bad = copy.deepcopy(good)
            bad[u"数"][u"x:" + word] = 1
            self.assertNotEqual([], record_problems(bad, companies=(101, 102)), word)
        bad = copy.deepcopy(good)
        bad[u"数"][u"期1:行の数"] = u"120"
        self.assertNotEqual([], record_problems(bad, companies=(101, 102)))
        bad = copy.deepcopy(good)
        del bad[u"数"][u"期1:行の数"]
        self.assertNotEqual([], record_problems(bad, companies=(101, 102)))
        bad = copy.deepcopy(good)
        bad[u"読んだ便 UM2 の出力の sha256 の束ね"] = u"abc"
        self.assertNotEqual([], record_problems(bad, companies=(101, 102)))
        bad = copy.deepcopy(good)
        bad[u"予測"][u"UM3-A1"][u"当たり"] = u"はい"
        self.assertNotEqual([], record_problems(bad, companies=(101, 102)))
        self.assertNotEqual([], record_problems({}))
        self.assertNotEqual([], record_problems(None))

    def test_h_4_the_record_command_writes_nothing_without_the_four_production_companies(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = build_world(tmp)
            out = os.path.join(tmp, u"記録.json")
            rc, _o, err = run_cli(["--tally", "--record", "--co", w["co"], "--seat", w["seat"], "--root", w["root"], "--transcripts", w["tdir"], "--out", out])
            self.assertEqual(2, rc)
            self.assertFalse(os.path.exists(out))
            self.assertNotIn("Traceback", err)

    def test_h_5_the_record_command_writes_the_record_when_the_four_companies_are_there(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = build_world(tmp)
            for i in (1, 2, 3, 4):
                for base in (w["co"], w["seat"], w["root"]):
                    os.makedirs(os.path.join(base, str(i)), exist_ok=True)
            out = os.path.join(tmp, u"記録.json")
            rc, _o, err = run_cli(["--tally", "--record", "--co", w["co"], "--seat", w["seat"], "--root", w["root"], "--transcripts", w["tdir"], "--out", out])
            self.assertEqual(0, rc, err)
            rec = json.loads(read_text(out))
        self.assertEqual(4, rec[u"会社の数"])
        self.assertEqual([u"a", u"b"], rec[u"回"])
        self.assertEqual([], record_problems(rec))

    def test_h_7_the_record_command_without_out_writes_to_the_fixed_place_under_its_own_root(self):
        real = os.path.join(ROOT, RECORD_REL)
        before = (os.path.exists(real), read_bytes(RECORD_REL) if os.path.exists(real) else None)
        with tempfile.TemporaryDirectory() as tmp:
            w = build_world(tmp)
            for i in (1, 2, 3, 4):
                for base in (w["co"], w["seat"], w["root"]):
                    os.makedirs(os.path.join(base, str(i)), exist_ok=True)
            fake = os.path.join(tmp, u"fake", u"audit-core")
            os.makedirs(os.path.join(fake, u"measure"))
            copy_to = os.path.join(fake, TALLY_REL)
            shutil.copyfile(os.path.join(ROOT, TALLY_REL), copy_to)
            r = subprocess.run([sys.executable, "-I", copy_to, "--tally", "--record", "--co", w["co"], "--seat", w["seat"], "--root", w["root"], "--transcripts", w["tdir"]],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(0, r.returncode, r.stderr.decode("utf-8", "replace"))
            self.assertEqual(b"", r.stdout)
            placed = os.path.join(fake, RECORD_REL)
            self.assertTrue(os.path.exists(placed))
            self.assertEqual(4, json.loads(read_text(placed))[u"会社の数"])
        after = (os.path.exists(real), read_bytes(RECORD_REL) if os.path.exists(real) else None)
        self.assertEqual(before, after)

    def test_h_6_the_prediction_in_the_record_follows_the_counts_in_the_record(self):
        rec = self.rec2
        self.assertEqual(TAL.judge(rec), rec[u"予測"])
        self.assertIsNone(rec[u"予測"][u"UM3-A1"][u"当たり"])             # 分母が封と違う(2 社 × 2 回)
