# -*- coding: utf-8 -*-
u"""封 docs/UNIVERSAL_FILL_VERIFY_SEAL_2026-11-24.md(UM4 ― 先に普通の AI の席に全部の数を埋めさせ、後から別の席に根拠を調べさせる作り方を、新しい素材で測る)の封の門。

**この門が作る素材は、この file の中で tmp に組む架空の 1 社(201)だけ。** 開発の素材(番号 102)も本番の 5〜8 も repo に写さない・読まない。席(subagent)は呼ばない。API・鍵・通信は使わない。
便 UM0〜UM3 の file・engine は封の commit から 0 行(``git diff``)・作業の木でも変わっていない(``git status``)。

**縛るもの**

1. 封と 2 つの頼みの紙の字(sha256)・3 つが同じ commit・engine と便 UM0〜UM3 の file が 0 行・順序(封 → script → 門。記録は順序の対象外で、無い時も在る時も落ちない)。
2. script は ``python3 -I``・標準 library だけ(便 UM2 の検査を file の path から読み込む所の importlib だけ許す)・どんな入力でも落ちない・scratchpad の path を字で持たない。
3. 予測 21 本の境(表の字と BOUNDS が同じ・境の 1 つ下と 1 つ上で当たり外れが変わる)。
4. 素材の形の検査(封 §1-1)の規則ごとの OK/NG と、出力に項目の名・値・file の名を出さないこと。
5. 壊した表の作り方(封 §1-4)の 5 種類(罠の値・桁・隣・無いのに在る・在るのに無い)を、手で決めた行・数・作れなかった数・外した数で。
6. 確かめの状態(封 §1-3)の 8 状態を、条件ごと(2 道の file が同じ・別の道の計算が違う・出どころが無い・計算が違う・形が読めない など)に、作り物の素材の cell から計算し直して。
7. 席の folder(``--hand``)に正解・作り方・確かめる席に渡さない file が入らないこと・確かめる表は id・状態・数値だけ。
8. 行ごとの照合・並べる表・過程の数・記録が持ってはいけない字・本番の 4 社(5〜8)がそろわない時は記録を書かないこと。

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


SEAL_REL = "docs/UNIVERSAL_FILL_VERIFY_SEAL_2026-11-24.md"
SOURCE_BRIEF_REL = "docs/UNIVERSAL_FILL_VERIFY_SOURCE_BRIEF_2026-11-24.md"
CHECK_BRIEF_REL = "docs/UNIVERSAL_FILL_VERIFY_CHECK_BRIEF_2026-11-24.md"
SEAL_COMMIT_SHORT = "ce005f98"
SEAL_SHA256 = "cf43aeecb13988ce3bc5d0c2f2bed27d904d0b5cd3bff8135c2bfc9ceaad5336"
SOURCE_BRIEF_SHA256 = "c9f32a7ba1619b4f473ee2b945834731011e167d80a1e582604f80aca3006a14"
CHECK_BRIEF_SHA256 = "aad4fa7a8b06268ae7ced8aa716db3aa8d4c8749cfbba24fecafc1c4958ee95e"
SCRIPT_REL = "measure/universal_fill_verify_2026-11-24.py"
GATE_REL = "tests/measure/test_universal_fill_verify_seal.py"
RECORD_REL = "fixtures/universal/um4/record.json"
ORDER_FILES = (SCRIPT_REL, GATE_REL)
#: 便 UM0〜UM3 の file(封の commit に在ったもの。0 行でなければならない)
PRIOR_FILES = (
    "docs/UNIVERSAL_MATERIAL_INSTRUCTION_2026-11-23.md", "docs/UNIVERSAL_MATERIAL_RESULT_2026-11-23.md", "docs/UNIVERSAL_MATERIAL_SEAL_2026-11-23.md",
    "docs/UNIVERSAL_MATERIAL_THIRD_PARTY_SOURCE_PRESEAL_2026-11-23.md", "docs/UNIVERSAL_MATERIAL_THIRD_PARTY_SOURCE_SEAL_2026-11-23.md",
    "docs/UNIVERSAL_THROUGH_INSTRUCTION_2026-11-23.md", "docs/UNIVERSAL_THROUGH_RESULT_2026-11-24.md", "docs/UNIVERSAL_THROUGH_SEAL_2026-11-23.md",
    "docs/UNIVERSAL_THROUGH_SOURCE_BRIEF_2026-11-23.md",
    "docs/UNIVERSAL_PROCESS_BRIEF_2026-11-24.md", "docs/UNIVERSAL_PROCESS_RESULT_2026-11-24.md", "docs/UNIVERSAL_PROCESS_SEAL_2026-11-24.md",
    "fixtures/universal/um0/definition_A.json", "fixtures/universal/um0/definition_B.json", "fixtures/universal/um0/record.json",
    "fixtures/universal/um2/record.json", "fixtures/universal/um3/record.json",
    "measure/universal_check_2026-11-23.py", "measure/universal_source_gen_2026-11-23.py", "measure/universal_through_check_2026-11-23.py",
    "measure/universal_through_tally_2026-11-23.py", "measure/universal_process_tally_2026-11-24.py",
    "tests/measure/test_universal_material_result.py", "tests/measure/test_universal_material_seal.py", "tests/measure/test_universal_through_result.py",
    "tests/measure/test_universal_through_seal.py", "tests/measure/test_universal_process_result.py", "tests/measure/test_universal_process_seal.py",
)
FV = load_module(SCRIPT_REL, "um4_fill_verify_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_um4_seal_gate")      # 順序の部品。門としては走らせない


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
    r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, SCRIPT_REL)] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


# ======================================================================== 1. 封の字・順序
class SealTextTest(unittest.TestCase):
    def test_a_1_the_seal_and_the_two_briefs_are_the_sealed_bytes(self):
        self.assertEqual(SEAL_SHA256, hashlib.sha256(read_bytes(SEAL_REL)).hexdigest())
        self.assertEqual(SOURCE_BRIEF_SHA256, hashlib.sha256(read_bytes(SOURCE_BRIEF_REL)).hexdigest())
        self.assertEqual(CHECK_BRIEF_SHA256, hashlib.sha256(read_bytes(CHECK_BRIEF_REL)).hexdigest())

    def test_a_2_the_seal_and_the_briefs_are_one_commit_and_unchanged(self):
        for rel in (SEAL_REL, SOURCE_BRIEF_REL, CHECK_BRIEF_REL):
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
        for word in (u"universal", u"um0", u"um2", u"um3", u"um4"):
            self.assertNotIn(word, body)

    def test_a_6_the_prediction_rows_of_the_seal_hold_the_sealed_words(self):
        seal = read(SEAL_REL)
        rows = dict((m.group(1), m.group(0)) for m in re.finditer(u"^\\| (UM4-[A-Z][0-9]) \\|.*$", seal, re.M))
        self.assertEqual(sorted(FV.BOUNDS), sorted(rows))
        self.assertEqual(21, len(rows))
        words = {
            u"UM4-M1": (u"3 以上", u"2 以下"), u"UM4-F1": (u"95% 以上", u"95% 未満"), u"UM4-F2": (u"2 以上", u"1 以下"),
            u"UM4-F3": (u"2 以上", u"1 以下"), u"UM4-F4": (u"半分以上", u"半分未満"), u"UM4-F5": (u"半分以上", u"半分未満"),
            u"UM4-V1": (u"1 以上", u"0"), u"UM4-V2": (u"85% 以上", u"85% 未満"), u"UM4-V3": (u"4 以上", u"3 以下"),
            u"UM4-V4": (u"1 以上", u"0"), u"UM4-V5": (u"は 0", u"1 以上"), u"UM4-V6": (u"は 0", u"1 以上"),
            u"UM4-V7": (u"3 以上", u"2 以下"), u"UM4-V8": (u"80% 以上", u"80% 未満"), u"UM4-V9": (u"10 以下", u"11 以上"),
            u"UM4-T1": (u"84 以下", u"85 以上"), u"UM4-T2": (u"は 0", u"1 以上"), u"UM4-G1": (u"15 行以上", u"14 以下"),
            u"UM4-G2": (u"多い", u"同じか少ない"), u"UM4-P1": (u"4 社とも多い", u"1 社でも同じか少ない"), u"UM4-P2": (u"1 以上", u"0"),
        }
        for k, ws in words.items():
            for w in ws:
                self.assertIn(w, rows[k], (k, w))

    def test_a_7_the_bounds_in_the_script_are_the_sealed_numbers(self):
        want = od([
            (u"UM4-M1", {u"直しなしで通る社": 3, u"会社の数": 4}), (u"UM4-F1", {u"同じの百分率": 95, u"普通の行": 168}),
            (u"UM4-F2", {u"罠を取った行": 2, u"罠の行": 32}), (u"UM4-F3", {u"無いのに在る": 2, u"無いの行": 24}),
            (u"UM4-F4", {u"高で数を出した行の分子": 1, u"分母": 2, u"決めの行": 16}),
            (u"UM4-F5", {u"回βも同じ答えの分子": 1, u"分母": 2, u"判定する分母の下限": 3}),
            (u"UM4-V1", {u"通した誤り": 1}), (u"UM4-V2", {u"通す百分率": 85}), (u"UM4-V3", {u"要確認": 4, u"決めの行": 8}),
            (u"UM4-V4", {u"通す": 1, u"行": 8}), (u"UM4-V5", {u"通す": 0, u"行": 8}), (u"UM4-V6", {u"通す": 0, u"行": 4}),
            (u"UM4-V7", {u"無いに異議": 3, u"行": 4}), (u"UM4-V8", {u"直せたの百分率": 80}), (u"UM4-V9", {u"状態が違う行": 10, u"行": 96}),
            (u"UM4-T1", {u"通す行": 84, u"行": 120, u"百分率": 70}), (u"UM4-T2", {u"通した誤り": 0}), (u"UM4-G1", {u"取得の差": 15}),
            (u"UM4-G2", {u"差": 1}), (u"UM4-P1", {u"社": 4}), (u"UM4-P2", {u"席": 1, u"席の数": 20}),
        ])
        self.assertEqual(json.dumps(want, ensure_ascii=False), json.dumps(FV.BOUNDS, ensure_ascii=False))

    def test_a_8_the_seal_fixes_the_eight_states_and_the_five_mutations_the_script_names(self):
        seal = read(SEAL_REL)
        for s in FV.STATUS_NAMES:
            self.assertIn(s, seal, s)
        self.assertEqual(8, len(FV.STATUS_NAMES))
        for k in FV.MUT_KINDS:
            self.assertIn(k, seal, k)
        self.assertEqual(5, len(FV.MUT_KINDS))
        self.assertEqual((FV.S_2, FV.S_OK, FV.S_NONE_OK), FV.PASS_STATUSES)
        self.assertEqual((5, 6, 7, 8), FV.PROD)
        self.assertEqual((102,), FV.DEV)


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
        other = PREFIX + SCRIPT_REL
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("pre", {other: "x"}), ("seal-x", {seal: "s"}), ("later", {PREFIX + "b": "y"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            got = PR.order_problems(tmp, PREFIX, SEAL_REL, short, [], [SCRIPT_REL, "b", "missing.py"])
            self.assertIn(u"BEFORE_SEAL:" + SCRIPT_REL, got)
            self.assertIn(u"UNCOMMITTED:missing.py", got)
            allowed = order_problems_allowing_not_yet(tmp, short, [SCRIPT_REL, "b", "missing.py"])
            self.assertIn(u"BEFORE_SEAL:" + SCRIPT_REL, allowed)
            self.assertNotIn(u"UNCOMMITTED:missing.py", allowed)
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("seal-x", {seal: "s"}), ("later", {other: "y"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            self.assertEqual([], list(PR.order_problems(tmp, PREFIX, SEAL_REL, short, [], [SCRIPT_REL])))


# ======================================================================== 2. script の作り
STDLIB_OK = set(["__future__", "collections", "csv", "datetime", "hashlib", "importlib", "io", "json", "os", "re", "shutil", "sys", "unicodedata", "fractions"])


class ScriptShapeTest(unittest.TestCase):
    def test_b_1_only_the_standard_library_is_imported_and_importlib_only_loads_the_um2_check(self):
        tree = ast.parse(read(SCRIPT_REL))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names |= set(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add((node.module or "").split(".")[0])
        self.assertTrue(names <= STDLIB_OK, names - STDLIB_OK)
        body = read(SCRIPT_REL)
        self.assertEqual(1, body.count("spec_from_file_location("))
        self.assertIn(u"measure/universal_through_check_2026-11-23.py", body)
        for w in (u"exec(", u"eval(", u"__import__(", u"subprocess", u"urllib", u"socket"):
            self.assertNotIn(w, body, w)

    def test_b_2_it_runs_isolated_and_writes_no_traceback_for_bad_commands(self):
        for args in ([], ["--nope"], ["--hand"], ["--tally"], ["--tally", "--record"], ["--process"], ["--digest"], ["--hand", "--tally"], ["--material"],
                     ["--mutate"], ["--status"], ["--through"], ["--status", "--which", "x"]):
            rc, _o, err = run_cli(args)
            self.assertIn(rc, (1, 2, 0), args)
            self.assertNotIn("Traceback", err, args)
        self.assertEqual(2, run_cli([])[0])

    def test_b_3_the_script_does_not_hold_a_scratchpad_path_or_the_harness_words(self):
        body = read(SCRIPT_REL)
        for w in ("scratchpad", "/private/tmp", "claude-501", "apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(",
                  "verify_document(", "verify_external(", "tampered", u"注入"):
            self.assertNotIn(w, body, w)

    def test_b_4_the_gate_has_no_skip_and_makes_no_production_material(self):
        body = read(GATE_REL)
        self.assertNotIn(u"skip" + u"Test", body)
        self.assertNotIn(u"@unittest." + u"skip", body)
        self.assertNotIn(u"pytest.mark." + u"skip", body)
        self.assertEqual((5, 6, 7, 8), FV.PROD)

    def test_b_5_the_fixture_folder_holds_only_the_record(self):
        d = os.path.join(ROOT, "fixtures", "universal", "um4")
        if os.path.exists(d):
            self.assertEqual([u"record.json"], sorted(os.listdir(d)))

    def test_b_6_the_script_writes_no_production_record_unless_asked_with_record(self):
        real = os.path.join(ROOT, RECORD_REL)
        before = (os.path.exists(real), read_bytes(RECORD_REL) if os.path.exists(real) else None)
        with tempfile.TemporaryDirectory() as tmp:
            run_cli(["--tally", "--co", tmp, "--root", tmp, "--companies", "201"])
        self.assertEqual(before, (os.path.exists(real), read_bytes(RECORD_REL) if os.path.exists(real) else None))


# ======================================================================== 3. 作り物の 1 社(201)
GOLD_NAMES = od([
    (u"a01", u"売上高_当期"), (u"a02", u"売上高_前期"), (u"a03", u"売上総利益_当期"), (u"a04", u"営業利益_当期"), (u"a05", u"営業利益_前期"),
    (u"a06", u"経常利益_当期"), (u"a07", u"当期純利益_当期"), (u"a08", u"減価償却費_当期"), (u"a09", u"現金及び預金_当期末"),
    (u"a10", u"流動資産合計_当期末"), (u"a11", u"資産合計_当期末"), (u"a12", u"短期借入金_当期末"), (u"a13", u"長期借入金_当期末"),
    (u"a14", u"負債合計_当期末"), (u"a15", u"純資産合計_当期末"), (u"a16", u"純資産合計_前期末"),
    (u"a29", u"借入の残高の合計_当期末"), (u"a30", u"期末の従業員数_当期末"),
])
A_IDS = [u"a%02d" % k for k in range(1, 31)]
MONTHS = [u"a%d" % (16 + k) for k in range(1, 13)]
GOLD = od([
    (u"a01", 100000), (u"a02", None), (u"a03", 30000), (u"a04", 20000), (u"a05", None), (u"a06", 18000), (u"a07", 12000), (u"a08", 5000),
    (u"a09", 7000), (u"a10", 15000), (u"a11", 40000), (u"a12", 3000), (u"a13", 8000), (u"a14", 25000), (u"a15", 15000), (u"a16", 9000),
    (u"a29", 11000), (u"a30", None),
])
MONTH_GOLD = [8000 + 100 * k for k in range(12)]
PERIOD = {u"当期の始まり": u"2025-03-01", u"当期の終わり": u"2026-02-28"}
T_CSV = u"科目,金額\n売上,\"110,000\"\n営業,25000\n純利,13000\n預金,\"6,500\"\n"
M_CSV = u"科目,金額,列3\nx2,30000,5000\nx3,20000,10000\nx4,18000,0\nx5,40000,0\nx6,8,0\nx7,13000,0\nx8,3000,0\n"
N_CSV = u"科目,金額\nx2,30000\n"
J_CSV = u"日付,科目,借方,貸方\n2025-04-01,売上,4000,0\n2025-04-02,売上,5000,0\n2025-04-03,仕入,100,0\n"
TRAPS = {u"無い": [u"売上高_前期", u"営業利益_前期", u"期末の従業員数_当期末"],
         u"罠": [{u"項目": u"売上高_当期", u"罠の値": 110000, u"file": u"t.csv", u"行": 2, u"列": 2, u"説明": u"x"},
                 {u"項目": u"営業利益_当期", u"罠の値": 25000, u"file": u"t.csv", u"行": 3, u"列": 2, u"説明": u"x"},
                 {u"項目": u"当期純利益_当期", u"罠の値": 13000, u"file": u"t.csv", u"行": 4, u"列": 2, u"説明": u"x"},
                 {u"項目": u"現金及び預金_当期末", u"罠の値": 6500, u"file": u"t.csv", u"行": 5, u"列": 2, u"説明": u"x"}],
         u"決め": [{u"項目": u"短期借入金_当期末", u"読み": [{u"値": 3000, u"説明": u"x"}, {u"値": 7000, u"説明": u"y"}]},
                 {u"項目": u"借入の残高の合計_当期末", u"読み": [{u"値": 11000, u"説明": u"x"}, {u"値": 13000, u"説明": u"y"}]}]}


def gold_json(gold=None, months=None):
    gold = dict(GOLD) if gold is None else gold
    body = dict((GOLD_NAMES[i], gold[i]) for i in GOLD_NAMES)
    body[u"月次の売上高_当期"] = list(MONTH_GOLD) if months is None else months
    body[u"人件費_当期"] = 123
    return {u"期1": body}


def make_company(co, i=201, gold=None, traps=None, period=None, files=None):
    d = os.path.join(co, str(i))
    wjson(os.path.join(d, u"正解", u"正解.json"), gold_json(gold))
    wjson(os.path.join(d, u"正解", u"罠.json"), TRAPS if traps is None else traps)
    wjson(os.path.join(d, u"正解", u"期.json"), PERIOD if period is None else period)
    files = {u"t.csv": T_CSV, u"m.csv": M_CSV, u"n.csv": N_CSV, u"j.csv": J_CSV} if files is None else files
    for n, body in files.items():
        wtext(os.path.join(d, u"期1", n), body)
    wtext(os.path.join(d, u"作り方", u"作る.py"), u"x = 1\n")
    return d


def rows_json(path, rows):
    wjson(path, {u"行": rows})


def vrow(i, state, num=None, conf=u"中"):
    return {u"id": i, u"状態": state, u"数値": num, u"出どころ": u"x", u"自信": conf}


def alpha_rows():
    u"""回 α の値の表(手で決めた結果。下の ALPHA_NAMES と同じ)。"""
    rows = [vrow(u"a01", u"在る", u"110000"), vrow(u"a02", u"在る", u"500"), vrow(u"a03", u"在る", u"30000"), vrow(u"a04", u"在る", u"20000"),
            vrow(u"a05", u"無い"), vrow(u"a06", u"在る", u"18001"), vrow(u"a07", u"在る", u"13000"), vrow(u"a08", u"分からない"),
            vrow(u"a10", u"在る", u"abc"), vrow(u"a11", u"在る", u"40000"), vrow(u"a12", u"在る", u"3000", u"高"), vrow(u"a13", u"在る", u"8000"),
            vrow(u"a14", u"無い"), vrow(u"a15", u"在る", u"15000"), vrow(u"a16", u"在る", u"9000"), vrow(u"a29", u"在る", u"13000", u"高"),
            vrow(u"a30", u"在る", u"7")]
    for k, m in enumerate(MONTHS):
        rows.append(vrow(m, u"在る", u"1" if k == 0 else str(MONTH_GOLD[k])))
    return rows


def beta_rows():
    rows = alpha_rows()
    out = []
    for r in rows:
        r = dict(r)
        if r[u"id"] == u"a01":
            r[u"数値"] = u"100000"
        if r[u"id"] == u"a17":
            r[u"数値"] = u"2"
        if r[u"id"] == u"a30":
            r[u"状態"], r[u"数値"] = u"無い", None
        out.append(r)
    return out


ALPHA_NAMES = {
    u"a01": u"違う", u"a02": u"無いのに在る", u"a03": u"同じ", u"a04": u"同じ", u"a05": u"無いで同じ", u"a06": u"違う", u"a07": u"違う", u"a08": u"分からない",
    u"a09": u"答えなし", u"a10": u"形が読めない", u"a11": u"同じ", u"a12": u"決め:1つ目", u"a13": u"同じ", u"a14": u"無いで違う", u"a15": u"同じ", u"a16": u"同じ",
    u"a29": u"決め:2つ目", u"a30": u"無いのに在る", u"a17": u"違う",
}
for _m in MONTHS[1:]:
    ALPHA_NAMES[_m] = u"同じ"
KIND_OF = dict((i, u"普通") for i in A_IDS)
KIND_OF.update({u"a02": u"無い", u"a05": u"無い", u"a30": u"無い", u"a01": u"罠", u"a04": u"罠", u"a07": u"罠", u"a09": u"罠", u"a12": u"決め", u"a29": u"決め"})


def src_cell(f, r, c, mult=1):
    return {u"種類": u"素材", u"file": f, u"位置": {u"行": r, u"列": c}, u"行の見出し": u"x", u"列の見出し": u"y", u"表示の倍率": mult}


def src_sum(f, col, rows, mult=1):
    return {u"種類": u"素材の和", u"file": f, u"列": col, u"行の並び": rows, u"列の見出し": u"y", u"表示の倍率": mult}


def src_rows(f, mult=1):
    return {u"種類": u"表の行の和", u"file": f, u"頭の行": 1, u"額": {u"列": u"借方", u"符号": u"そのまま"},
            u"条件": [{u"列": u"科目", u"比べ方": u"等しい", u"値": u"売上"}], u"表示の倍率": mult}


def crow(i, view, **kw):
    r = {u"id": i, u"見立て": view, u"出どころ": None, u"別の道": None, u"正しいと見る数値": None, u"正しいと見る数値の出どころ": None, u"注": u"x"}
    r.update(kw)
    return r


def orig_check_rows():
    u"""確かめる席(原の表)の根拠の表。回 α の表の各行に手で決めた見立てを付ける。"""
    rows = [
        crow(u"a01", u"合わない", **{u"正しいと見る数値": u"100000"}),
        crow(u"a02", u"見つからない"),
        crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2), 別の道=src_cell(u"n.csv", 2, 2)),
        crow(u"a04", u"合う", 出どころ=src_cell(u"m.csv", 3, 2), 別の道=src_cell(u"m.csv", 3, 2)),
        crow(u"a05", u"無いで合う"),
        crow(u"a06", u"合う", 出どころ=src_cell(u"m.csv", 4, 2)),
        crow(u"a07", u"合う", 出どころ=src_cell(u"t.csv", 4, 2)),
        crow(u"a08", u"在るはず", **{u"正しいと見る数値": u"5000"}),
        crow(u"a10", u"合う", 出どころ=src_cell(u"m.csv", 2, 2)),
        crow(u"a11", u"決めが要る"),
        crow(u"a12", u"合う", 出どころ=src_cell(u"m.csv", 8, 2)),
        crow(u"a13", u"合う", 出どころ=src_cell(u"m.csv", 6, 2, 1000)),
        crow(u"a14", u"在るはず", **{u"正しいと見る数値": u"24999"}),
        crow(u"a15", u"合う", 出どころ=src_sum(u"m.csv", 3, [2, 3])),
        crow(u"a16", u"合う", 出どころ=src_rows(u"j.csv")),
        crow(u"a29", u"決めが要る"),
        crow(u"a30", u"合わない"),
        crow(u"a17", u"合う", 出どころ=src_cell(u"m.csv", 2, 2)),
    ]
    for m in MONTHS[1:]:
        rows.append(crow(m, u"見つからない"))
    return rows


def broken_check_rows():
    u"""確かめる席(壊した表)の根拠の表。壊した 6 行は手で決め、ほかの行は原と同じ。a18 だけ違う見立て。"""
    by = dict((r[u"id"], r) for r in orig_check_rows())
    by[u"a04"] = crow(u"a04", u"合わない", **{u"正しいと見る数値": u"20000"})
    by[u"a09"] = crow(u"a09", u"合う", 出どころ=src_cell(u"t.csv", 5, 2))
    by[u"a03"] = crow(u"a03", u"合わない", **{u"正しいと見る数値": u"30000"})
    by[u"a06"] = crow(u"a06", u"合う", 出どころ=src_cell(u"m.csv", 5, 2))
    by[u"a11"] = crow(u"a11", u"在るはず", **{u"正しいと見る数値": u"40000"})
    by[u"a05"] = crow(u"a05", u"合わない")
    by[u"a18"] = crow(u"a18", u"決めが要る")
    return [by[k] for k in sorted(by)]


ORIG_STATUS = {
    FV.S_2: [u"a03"], FV.S_OK: [u"a04", u"a07", u"a12", u"a13", u"a15", u"a16"],
    FV.S_NOBASIS: [u"a02", u"a06", u"a10", u"a17"] + MONTHS[1:], FV.S_MISMATCH: [u"a01", u"a30"], FV.S_REVIEW: [u"a11", u"a29"],
    FV.S_NONE_OK: [u"a05"], FV.S_NONE_OBJ: [u"a08", u"a14"], FV.S_NA: [u"a09"],
}


def type_bundle():
    items = []
    for i in A_IDS:
        if i == u"a03":
            items.append({u"id": i, u"状態": u"在る", u"数値": u"30000", u"単位": u"円", u"期間": {u"始まり": u"2025-03-01", u"終わり": u"2026-02-28"}, u"範囲": u"全社",
                          u"出どころ": src_cell(u"m.csv", 2, 2)})
        else:
            items.append({u"id": i, u"状態": u"無い", u"無い理由": u"素材が無い"})
    return {u"型の版": u"u2", u"材料": items}


DOC_TEXT = u"# 資料\n売上は[材料:a01]です。\n\n次の段落。数は[材料:a03]。終わり\n"


class TB(object):
    u"""tmp に組んだ 1 社の世界。``--hand`` を CLI で通して席の folder を作り、席の出力は手で書く。"""

    def __init__(self, tmp, gold=None):
        self.tmp = tmp
        self.co = os.path.join(tmp, u"co")
        self.root = os.path.join(tmp, u"root")
        self.tdir = os.path.join(tmp, u"tr")
        make_company(self.co, gold=gold)
        self.a = os.path.join(self.root, u"201", u"fill", u"a")

    def cli(self, *args):
        return run_cli(list(args))

    def hand(self, kind, rnd=None):
        args = ["--hand", "--co", self.co, "--root", self.root, "--company", "201", "--kind", kind]
        if rnd:
            args += ["--round", rnd]
        return run_cli(args)

    def seat(self, kind):
        return FV.seat_dir(self.root, 201, kind)

    def build(self, with_type=True, alpha=None, bundle=None, skip_alpha=False):
        for k, r in ((u"fill", u"a"), (u"fill", u"b")):
            assert self.hand(k, r)[0] == 0
        if not skip_alpha:
            rows_json(os.path.join(self.seat(u"fill-a"), u"値の表.json"), alpha_rows() if alpha is None else alpha)
        wtext(os.path.join(self.seat(u"fill-a"), u"資料.md"), DOC_TEXT)
        rows_json(os.path.join(self.seat(u"fill-b"), u"値の表.json"), beta_rows())
        if not skip_alpha:
            assert self.hand(u"check-orig")[0] == 0
            assert self.hand(u"check-broken")[0] == 0
            rows_json(os.path.join(self.seat(u"check-orig"), u"根拠の表.json"), orig_check_rows())
            rows_json(os.path.join(self.seat(u"check-broken"), u"根拠の表.json"), broken_check_rows())
        if with_type:
            assert self.hand(u"type")[0] == 0
            wjson(os.path.join(self.seat(u"type"), u"材料_期1_A.json"), type_bundle() if bundle is None else bundle)
        return self


def counts_of(rec):
    return rec[u"数"]


# ======================================================================== 4. 素材の形の検査(封 §1-1)
def mat_rules_with(mod):
    u"""作り物の 1 社に ``mod(co_dir)`` で 1 か所だけ壊しを入れて、規則の名 → OK/NG を返す。"""
    with tempfile.TemporaryDirectory() as tmp:
        d = make_company(os.path.join(tmp, u"co"))
        mod(d)
        return FV.material_report(d)[u"規則"]


def set_traps(d, fn):
    p = os.path.join(d, u"正解", u"罠.json")
    obj = json.loads(read_text(p))
    fn(obj)
    wjson(p, obj)


def set_gold(d, fn):
    p = os.path.join(d, u"正解", u"正解.json")
    obj = json.loads(read_text(p))
    fn(obj[u"期1"])
    wjson(p, obj)


def read_text(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


class MaterialTest(unittest.TestCase):
    def test_m_1_the_good_company_passes_every_rule_and_the_report_names_only_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_company(os.path.join(tmp, u"co"))
            rep = FV.material_report(d)
            self.assertEqual(u"OK", rep[u"全部"])
            self.assertEqual(sorted(FV.MATERIAL_RULES), sorted(rep[u"規則"]))
            self.assertEqual(11, len(rep[u"規則"]))
            self.assertTrue(all(v == u"OK" for v in rep[u"規則"].values()))
            rc, out, err = run_cli(["--material", d])
            self.assertEqual(0, rc, err)
            for leak in list(GOLD_NAMES.values()) + [u"t.csv", u"m.csv", u"110000", u"110,000", u"30000", u"2025", u"罠.json", u"正解.json", u"期1"]:
                self.assertNotIn(leak, out, leak)
            self.assertEqual(rep, json.loads(out))

    def test_m_2_each_rule_turns_ng_for_its_own_break_and_only_for_it(self):
        def trap_count(o):
            del o[u"罠"][3]

        def none_count(o):
            del o[u"無い"][2]

        def decide_count(o):
            o[u"決め"].append(o[u"決め"][0])

        def same_item(o):
            o[u"罠"][1][u"項目"] = o[u"罠"][0][u"項目"]

        def out_of_18(o):
            o[u"無い"][0] = u"人件費_当期"

        def null_elsewhere(o):
            pass

        def trap_equals_gold(o):
            o[u"罠"][0][u"罠の値"] = 100000

        def cell_differs(o):
            o[u"罠"][1][u"罠の値"] = 25001

        def decide_same(o):
            o[u"決め"][0][u"読み"][1][u"値"] = 3000

        cases = [
            (u"罠が 4 つ", lambda d: set_traps(d, trap_count), [u"罠が 4 つ", u"9 項目が別", u"9 項目が 18 個の中", u"罠の値が正解と違う整数", u"罠の値が書かれた升に在る"]),
            (u"無いが 3 つ", lambda d: set_traps(d, none_count), [u"無いが 3 つ", u"9 項目が別", u"9 項目が 18 個の中", u"無いの項目だけ正解が null"]),
            (u"決めが 2 つ", lambda d: set_traps(d, decide_count), [u"決めが 2 つ", u"9 項目が別", u"9 項目が 18 個の中", u"決めの 2 つの値が違う"]),
            (u"9 項目が別", lambda d: set_traps(d, same_item), [u"9 項目が別"]),
            (u"9 項目が 18 個の中", lambda d: set_traps(d, out_of_18), [u"9 項目が 18 個の中", u"無いの項目だけ正解が null"]),
            (u"無いの項目だけ正解が null", lambda d: set_gold(d, lambda g: g.__setitem__(u"売上総利益_当期", None)), [u"無いの項目だけ正解が null"]),
            (u"罠の値が正解と違う整数", lambda d: set_traps(d, trap_equals_gold), [u"罠の値が正解と違う整数", u"罠の値が書かれた升に在る"]),
            (u"罠の値が書かれた升に在る", lambda d: set_traps(d, cell_differs), [u"罠の値が書かれた升に在る"]),
            (u"決めの 2 つの値が違う", lambda d: set_traps(d, decide_same), [u"決めの 2 つの値が違う"]),
            (u"期の始まりと終わりが在る", lambda d: wjson(os.path.join(d, u"正解", u"期.json"), {u"当期の始まり": u"2025-03-01"}), [u"期の始まりと終わりが在る"]),
            (u"素材の file が在る", lambda d: shutil.rmtree(os.path.join(d, u"期1")), [u"素材の file が在る", u"罠の値が書かれた升に在る"]),
        ]
        self.assertEqual(sorted(FV.MATERIAL_RULES), sorted(c[0] for c in cases))
        for rule, mod, expect_ng in cases:
            got = mat_rules_with(mod)
            ng = sorted(k for k, v in got.items() if v == u"NG")
            self.assertIn(rule, ng, rule)
            self.assertEqual(sorted(expect_ng), ng, rule)

    def test_m_3_the_trap_cell_is_read_with_commas_and_two_encodings_and_a_wrong_place_is_ng(self):
        def cp932(d):
            wbytes(os.path.join(d, u"期1", u"t.csv"), T_CSV.encode("cp932"))

        def bom(d):
            wbytes(os.path.join(d, u"期1", u"t.csv"), T_CSV.encode("utf-8-sig"))

        def row_out(d):
            set_traps(d, lambda o: o[u"罠"][0].__setitem__(u"行", 99))

        def col_zero(d):
            set_traps(d, lambda o: o[u"罠"][0].__setitem__(u"列", 0))

        def dotdot(d):
            set_traps(d, lambda o: o[u"罠"][0].__setitem__(u"file", u"../t.csv"))

        def no_file(d):
            set_traps(d, lambda o: o[u"罠"][0].__setitem__(u"file", u"zz.csv"))

        def text_cell(d):
            set_traps(d, lambda o: o[u"罠"][0].__setitem__(u"列", 1))

        def bool_row(d):
            set_traps(d, lambda o: o[u"罠"][0].__setitem__(u"行", True))

        key = u"罠の値が書かれた升に在る"
        self.assertEqual(u"OK", mat_rules_with(cp932)[key])
        self.assertEqual(u"OK", mat_rules_with(bom)[key])
        for bad in (row_out, col_zero, dotdot, no_file, text_cell, bool_row):
            self.assertEqual(u"NG", mat_rules_with(bad)[key], bad.__name__)

    def test_m_4_a_broken_or_missing_file_makes_rules_ng_and_never_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            for kind in ("missing", "broken", "list", "deep"):
                d = make_company(os.path.join(tmp, kind))
                p = os.path.join(d, u"正解", u"罠.json")
                if kind == "missing":
                    os.remove(p)
                elif kind == "broken":
                    wtext(p, u"{not json")
                elif kind == "list":
                    wtext(p, u"[1]")
                else:
                    wtext(p, u"[" * 5000 + u"]" * 5000)
                rep = FV.material_report(d)
                self.assertEqual(u"NG", rep[u"全部"], kind)
            rep = FV.material_report(os.path.join(tmp, u"none"))
            self.assertEqual(u"NG", rep[u"全部"])
            self.assertTrue(all(v == u"NG" for v in rep[u"規則"].values()))

    def test_m_5_the_cell_reader_takes_only_a_signed_integer_text(self):
        self.assertEqual(110000, FV.cell_int(u"110,000"))
        self.assertEqual(-5, FV.cell_int(u" -5 "))
        for bad in (u"1.5", u"", u"abc", u"△5", u"(5)", u"1e3", None, 5, u"5円"):
            self.assertIsNone(FV.cell_int(bad), bad)


# ======================================================================== 5. 席の folder(--hand)
def tree(folder):
    out = []
    for d, ds, fs in os.walk(folder):
        for n in ds + fs:
            out.append(os.path.relpath(os.path.join(d, n), folder).replace(os.sep, u"/"))
    return sorted(out)


class HandTest(unittest.TestCase):
    def test_f_1_fill_check_and_type_folders_hold_exactly_what_the_seal_gives(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp).build()
            outs = set([u"値の表.json", u"資料.md", u"根拠の表.json", u"材料_期1_A.json"])
            top = lambda k: sorted(set(os.listdir(w.seat(k))) - outs)
            self.assertEqual([u"definition_A.json", u"指定.json", u"素材", u"頼み.md"], top(u"fill-a"))
            self.assertEqual(top(u"fill-a"), top(u"fill-b"))
            for k in (u"check-orig", u"check-broken"):
                self.assertEqual(sorted([u"definition_A.json", u"指定.json", u"素材", u"頼み.md", u"出どころの書き方.md", u"確かめる表.json"]), top(k))
            self.assertEqual(sorted([u"definition_A.json", u"指定.json", u"期1", u"指示書.md"]), top(u"type"))
            self.assertEqual(read_bytes(u"docs/UNIVERSAL_PROCESS_BRIEF_2026-11-24.md"), open(os.path.join(w.seat(u"fill-a"), u"頼み.md"), "rb").read())
            self.assertEqual(read_bytes(CHECK_BRIEF_REL), open(os.path.join(w.seat(u"check-orig"), u"頼み.md"), "rb").read())
            for k in (u"check-orig", u"check-broken", u"type"):
                name = u"指示書.md" if k == u"type" else u"出どころの書き方.md"
                self.assertEqual(read_bytes(u"docs/UNIVERSAL_THROUGH_INSTRUCTION_2026-11-23.md"), open(os.path.join(w.seat(k), name), "rb").read(), k)
            self.assertEqual(read_bytes(u"fixtures/universal/um0/definition_A.json"), open(os.path.join(w.seat(u"fill-a"), u"definition_A.json"), "rb").read())
            spec = json.loads(read_text(os.path.join(w.seat(u"fill-a"), u"指定.json")))
            self.assertEqual({u"成果物": u"A", u"当期の始まり": u"2025-03-01", u"当期の終わり": u"2026-02-28"}, spec)

    def test_f_2_no_gold_no_how_to_and_no_answer_land_in_any_seat_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp).build()
            for k in FV.SEAT_KINDS:
                names = tree(w.seat(k))
                for n in names:
                    for bad in (u"正解", u"作り方", u"罠.json", u"期.json", u"壊し方", u"段3"):
                        self.assertNotIn(bad, n, (k, n))
            for k in (u"fill-a", u"fill-b"):
                self.assertEqual([u"m.csv", u"j.csv", u"n.csv", u"t.csv"], [x for x in [u"m.csv", u"j.csv", u"n.csv", u"t.csv"] if os.path.exists(os.path.join(w.seat(k), u"素材", x))])
            self.assertTrue(os.path.exists(os.path.join(w.seat(u"type"), u"期1", u"t.csv")))
            self.assertFalse(os.path.exists(os.path.join(w.seat(u"type"), u"素材")))

    def test_f_3_the_check_table_has_only_id_state_and_value_and_none_of_the_fillers_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp).build()
            for k in (u"check-orig", u"check-broken"):
                obj = json.loads(read_text(os.path.join(w.seat(k), u"確かめる表.json")))
                self.assertEqual([u"行"], list(obj))
                for r in obj[u"行"]:
                    self.assertEqual([u"id", u"状態", u"数値"], list(r))
                body = read_text(os.path.join(w.seat(k), u"確かめる表.json"))
                for leak in (u"出どころ", u"自信", u"作業の記録", u"資料"):
                    self.assertNotIn(leak, body)
            orig = json.loads(read_text(os.path.join(w.seat(u"check-orig"), u"確かめる表.json")))[u"行"]
            self.assertEqual(sorted(r[u"id"] for r in alpha_rows()), sorted(r[u"id"] for r in orig))
            self.assertEqual(dict((r[u"id"], (r[u"状態"], r[u"数値"])) for r in alpha_rows()), dict((r[u"id"], (r[u"状態"], r[u"数値"])) for r in orig))

    def test_f_4_the_broken_table_differs_from_the_original_in_exactly_the_six_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp).build()
            load = lambda k: dict((r[u"id"], (r[u"状態"], r[u"数値"])) for r in json.loads(read_text(os.path.join(w.seat(k), u"確かめる表.json")))[u"行"])
            o, b = load(u"check-orig"), load(u"check-broken")
            diff = sorted(i for i in set(o) | set(b) if o.get(i) != b.get(i))
            self.assertEqual([u"a03", u"a04", u"a05", u"a06", u"a09", u"a11"], diff)
            self.assertEqual((u"在る", u"25000"), b[u"a04"])
            self.assertEqual((u"無い", None), b[u"a11"])

    def test_f_5_an_existing_destination_is_left_alone_and_a_missing_source_makes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp)
            self.assertEqual(0, w.hand(u"fill", u"a")[0])
            marker = os.path.join(w.seat(u"fill-a"), u"mark")
            wtext(marker, u"m")
            rc, _o, err = w.hand(u"fill", u"a")
            self.assertEqual(3, rc)
            self.assertTrue(os.path.exists(marker))
            self.assertNotIn("Traceback", err)
            shutil.rmtree(os.path.join(w.co, u"201", u"期1"))
            rc, _o, _e = w.hand(u"type")
            self.assertEqual(4, rc)
            self.assertFalse(os.path.exists(w.seat(u"type")))

    def test_f_6_a_forbidden_name_in_the_material_stops_before_anything_is_made(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp)
            wtext(os.path.join(w.co, u"201", u"期1", u"正解メモ.txt"), u"x")
            self.assertEqual(0, w.hand(u"fill", u"a")[0])
            shutil.rmtree(w.seat(u"fill-a"))
            wtext(os.path.join(w.co, u"201", u"期1", u"作り方", u"x.txt"), u"x")
            rc, _o, _e = w.hand(u"fill", u"a")
            self.assertEqual(5, rc)
            self.assertFalse(os.path.exists(w.seat(u"fill-a")))
            wtext(os.path.join(w.co, u"201", u"期1", u"頼み.md"), u"x")
            shutil.rmtree(os.path.join(w.co, u"201", u"期1", u"作り方"))
            self.assertEqual(5, w.hand(u"fill", u"a")[0])

    def test_f_7_a_spec_that_cannot_be_read_makes_nothing_and_a_missing_or_empty_alpha_table_stops_the_check_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp)
            wjson(os.path.join(w.co, u"201", u"正解", u"期.json"), {u"当期の始まり": u"2025-13-01", u"当期の終わり": u"2026-02-28"})
            self.assertEqual(4, w.hand(u"fill", u"a")[0])
            wjson(os.path.join(w.co, u"201", u"正解", u"期.json"), PERIOD)
            self.assertEqual(0, w.hand(u"fill", u"a")[0])
            alpha = os.path.join(w.seat(u"fill-a"), u"値の表.json")
            for kind in (u"check-orig", u"check-broken"):
                for state in (u"無し", u"読めない", u"行が 0", u"行が並びでない"):
                    if os.path.exists(alpha):
                        os.remove(alpha)
                    if state == u"読めない":
                        wtext(alpha, u"{broken")
                    elif state == u"行が 0":
                        rows_json(alpha, [])
                    elif state == u"行が並びでない":
                        wjson(alpha, {u"行": u"x"})
                    rc, out, err = w.hand(kind)
                    self.assertEqual(7, rc, (kind, state))
                    self.assertFalse(os.path.exists(w.seat(kind)), (kind, state))
                    self.assertNotIn("Traceback", err)
            rows_json(alpha, alpha_rows())
            self.assertEqual(0, w.hand(u"check-orig")[0])
            self.assertEqual(len(alpha_rows()), len(json.loads(read_text(os.path.join(w.seat(u"check-orig"), u"確かめる表.json")))[u"行"]))

    def test_f_8_odd_arguments_are_refused_without_a_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            for args in (["--hand", "--co", tmp, "--root", tmp, "--company", "x", "--kind", "type"], ["--hand", "--co", tmp, "--root", tmp, "--company", "1", "--kind", "zzz"],
                         ["--hand", "--co", tmp, "--root", tmp, "--company", "1", "--kind", "fill", "--round", "c"]):
                rc, _o, err = run_cli(args)
                self.assertEqual(2, rc, args)
                self.assertNotIn("Traceback", err)


# ======================================================================== 6. 壊した表(封 §1-4)
def gold_map(**over):
    g = dict(GOLD)
    for k, m in enumerate(MONTHS):
        g[m] = MONTH_GOLD[k]
    g.update(over)
    return g


def forms_of(obj=None):
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, u"罠.json")
        wjson(p, TRAPS if obj is None else obj)
        return FV.read_forms(p)


def table_dict(rows):
    return dict((r[u"id"], r) for r in rows)


def simple(c):
    return [(x[u"id"], x[u"種類"], x[u"状態"], x[u"数値"], x[u"外した"]) for x in c]


class MutateTest(unittest.TestCase):
    def test_u_1_the_world_gives_the_six_hand_decided_rows(self):
        changes, not_made = FV.make_broken(table_dict(alpha_rows()), gold_map(), forms_of())
        self.assertEqual([(u"a04", u"罠の値", u"在る", 25000, False), (u"a09", u"罠の値", u"在る", 6500, False), (u"a03", u"桁", u"在る", 31000, False),
                          (u"a06", u"隣", u"在る", 40000, False), (u"a05", u"無いのに在る", u"在る", 11000, False), (u"a11", u"在るのに無い", u"無い", None, False)],
                         simple(changes))
        self.assertEqual(dict((k, 0) for k in FV.MUT_KINDS), not_made)

    def test_u_2_trap_rows_skip_those_the_seat_already_got_wrong_by_the_trap_and_stop_at_two(self):
        def ids(rows):
            ch, nm = FV.make_broken(rows, gold_map(), forms_of())
            return [x[u"id"] for x in ch if x[u"種類"] == u"罠の値"], nm[u"罠の値"]
        rows = table_dict(alpha_rows())                                      # a01・a07 は回 α がもう罠の値
        self.assertEqual(([u"a04", u"a09"], 0), ids(rows))
        rows[u"a04"] = vrow(u"a04", u"在る", u"25000")
        self.assertEqual(([u"a09"], 1), ids(rows))
        rows[u"a09"] = vrow(u"a09", u"在る", u"6500")
        self.assertEqual(([], 2), ids(rows))
        rows[u"a07"] = vrow(u"a07", u"在る", u"12999")
        self.assertEqual(([u"a07"], 1), ids(rows))
        rows[u"a01"] = vrow(u"a01", u"無い")                                 # 在る でない行も「罠の値でない」
        self.assertEqual(([u"a01", u"a07"], 0), ids(rows))
        rows[u"a04"] = vrow(u"a04", u"在る", u"1")
        rows[u"a09"] = vrow(u"a09", u"在る", u"2")
        self.assertEqual(([u"a01", u"a04"], 0), ids(rows))                   # 2 つで止まる
        ch = FV.make_broken(rows, gold_map(), forms_of())[0]
        self.assertEqual([(u"a01", u"在る", 110000), (u"a04", u"在る", 25000)], [(x[u"id"], x[u"状態"], x[u"数値"]) for x in ch if x[u"種類"] == u"罠の値"])

    def test_u_3_the_digit_row_changes_the_second_digit_from_the_top_and_wraps_nine_to_zero(self):
        def first_digit_row(num, others=None):
            rows = table_dict(alpha_rows())
            for i in (u"a03", u"a06", u"a11", u"a13", u"a15", u"a16"):
                rows[i] = vrow(i, u"在る", u"5")
            rows[u"a03"] = vrow(u"a03", u"在る", num)
            for k, m in enumerate(MONTHS):
                rows[m] = vrow(m, u"在る", u"7")
            ch, nm = FV.make_broken(rows, gold_map(), forms_of())
            return [x for x in ch if x[u"種類"] == u"桁"], nm
        for num, want in ((u"1234", 1334), (u"1934567", 1034567), (u"90000", 91000), (u"-4500", -4600), (u"-9100", -9200), (u"1000", 1100)):
            got, _ = first_digit_row(num)
            self.assertEqual([want], [x[u"数値"] for x in got], num)
        got, nm = first_digit_row(u"999")
        self.assertEqual([], got)                       # 絶対の値が 1000 未満の行は選ばれない
        self.assertEqual(1, nm[u"桁"])
        self.assertEqual(1, nm[u"隣"])                   # 桁が無いので隣も作れない
        self.assertEqual(1, nm[u"在るのに無い"])

    def test_u_4_the_neighbour_row_borrows_the_next_next_value_and_skips_the_same_number(self):
        rows = table_dict(alpha_rows())
        for i, v in ((u"a03", u"3000"), (u"a06", u"500"), (u"a11", u"500"), (u"a13", u"700"), (u"a15", u"700")):
            rows[i] = vrow(i, u"在る", v)
        ch, nm = FV.make_broken(rows, gold_map(), forms_of())
        nb = [x for x in ch if x[u"種類"] == u"隣"]
        self.assertEqual([(u"a06", 700)], [(x[u"id"], x[u"数値"]) for x in nb])        # 500 と同じ a11 は飛ばして a13
        self.assertEqual([u"a11"], [x[u"id"] for x in ch if x[u"種類"] == u"在るのに無い"])      # 借りた行(a06)の次の普通の行
        for i in (u"a13", u"a15", u"a16", u"a17"):
            rows[i] = vrow(i, u"在る", u"500")
        for m in MONTHS:
            rows[m] = vrow(m, u"在る", u"500")
        ch, nm = FV.make_broken(rows, gold_map(), forms_of())
        self.assertEqual([], [x for x in ch if x[u"種類"] in (u"隣", u"在るのに無い")])
        self.assertEqual((1, 1), (nm[u"隣"], nm[u"在るのに無い"]))
        self.assertEqual(0, nm[u"桁"])

    def test_u_5_the_has_none_row_takes_a01_cut_down_by_ten_toward_zero(self):
        for a01, want in ((u"110000", 11000), (u"119", 11), (u"-119", -11), (u"9", 0)):
            rows = table_dict(alpha_rows())
            rows[u"a01"] = vrow(u"a01", u"在る", a01)
            got = [x for x in FV.make_broken(rows, gold_map(), forms_of())[0] if x[u"種類"] == u"無いのに在る"]
            self.assertEqual([want], [x[u"数値"] for x in got], a01)
        rows = table_dict(alpha_rows())
        rows[u"a01"] = vrow(u"a01", u"無い")
        ch, nm = FV.make_broken(rows, gold_map(), forms_of())
        self.assertEqual(1, nm[u"無いのに在る"])
        self.assertEqual([], [x for x in ch if x[u"種類"] == u"無いのに在る"])
        rows = table_dict(alpha_rows())
        rows[u"a05"] = vrow(u"a05", u"在る", u"4")
        ch, nm = FV.make_broken(rows, gold_map(), forms_of())
        self.assertEqual([], [x for x in ch if x[u"種類"] == u"無いのに在る"])          # a30 も 在る なので作れない
        self.assertEqual(1, nm[u"無いのに在る"])
        rows[u"a30"] = vrow(u"a30", u"無い")
        ids = [x[u"id"] for x in FV.make_broken(rows, gold_map(), forms_of())[0] if x[u"種類"] == u"無いのに在る"]
        self.assertEqual([u"a30"], ids)
        rows = table_dict(alpha_rows())
        del rows[u"a05"]                                                              # 行が無い無いの行も候補
        ids = [x[u"id"] for x in FV.make_broken(rows, gold_map(), forms_of())[0] if x[u"種類"] == u"無いのに在る"]
        self.assertEqual([u"a05"], ids)

    def test_u_6_a_row_that_becomes_the_gold_is_dropped_from_the_broken_rows_and_counted(self):
        rows = table_dict(alpha_rows())
        rows[u"a03"] = vrow(u"a03", u"在る", u"12000")
        ch, nm = FV.make_broken(rows, gold_map(a03=13000), forms_of())
        d = [x for x in ch if x[u"種類"] == u"桁"][0]
        self.assertEqual((13000, True), (d[u"数値"], d[u"外した"]))
        rep = FV.mutate_report(ch, nm)
        self.assertEqual(1, rep[u"外した数"])
        self.assertEqual(5, rep[u"壊した行の数"])
        self.assertEqual(0, rep[u"作れなかった数"])
        self.assertEqual({u"作った": 1, u"作れなかった": 0, u"外した": 1}, dict(rep[u"桁"]))

    def test_u_7_without_forms_nothing_is_made_and_everything_is_counted_as_not_made(self):
        ch, nm = FV.make_broken(table_dict(alpha_rows()), gold_map(), None)
        self.assertEqual([], ch)
        self.assertEqual({u"罠の値": 2, u"桁": 1, u"隣": 1, u"無いのに在る": 1, u"在るのに無い": 1}, nm)
        self.assertEqual(6, FV.mutate_report(ch, nm)[u"作れなかった数"])

    def test_u_8_the_command_prints_only_counts_and_writes_the_change_table_outside_the_seat(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp).build()
            out = os.path.join(tmp, u"壊し方.json")
            rc, text, err = run_cli(["--mutate", "--co", w.co, "--root", w.root, "--company", "201", "--changes-out", out])
            self.assertEqual(0, rc, err)
            rep = json.loads(text)
            self.assertEqual(0, rep[u"作れなかった数"])
            self.assertEqual(6, rep[u"壊した行の数"])
            for leak in (u"a04", u"a03", u"25000", u"売上"):
                self.assertNotIn(leak, text)
            saved = json.loads(read_text(out))[u"変えた行"]
            self.assertEqual(6, len(saved))
            self.assertFalse(os.path.exists(os.path.join(w.root, u"201", u"壊し方_表.json")))
            rc, _t, _e = run_cli(["--mutate", "--co", w.co, "--root", w.root, "--company", "201"])
            self.assertEqual(0, rc)
            self.assertTrue(os.path.exists(os.path.join(w.root, u"201", u"壊し方_表.json")))
            for k in FV.SEAT_KINDS:
                self.assertNotIn(u"壊し方", u" ".join(tree(w.seat(k))))

    def test_u_9_a_missing_alpha_table_makes_no_broken_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp)
            w.hand(u"fill", u"a")
            rc, text, _e = run_cli(["--mutate", "--co", w.co, "--root", w.root, "--company", "201", "--changes-out", os.path.join(tmp, u"x.json")])
            self.assertEqual(0, rc)
            self.assertEqual(6, json.loads(text)[u"作れなかった数"])


# ======================================================================== 7. 確かめの状態(封 §1-3)
class StatusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        d = make_company(os.path.join(cls.tmp, u"co"))
        cls.chk = FV.load_check_module()
        cls.src = cls.chk.Source(os.path.join(d, u"期1"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def j(self, trow, orow):
        return FV.judge_status(trow, orow, self.chk, self.src)

    def present(self, num=u"30000"):
        return {u"id": u"a03", u"状態": u"在る", u"数値": num}

    def test_s_1_two_roads_need_the_same_number_and_two_different_files(self):
        t = self.present()
        self.assertEqual(FV.S_2, self.j(t, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2), 別の道=src_cell(u"n.csv", 2, 2))))
        self.assertEqual(FV.S_OK, self.j(t, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2), 別の道=src_cell(u"m.csv", 2, 2))))       # 2 つの file が同じ
        self.assertEqual(FV.S_OK, self.j(t, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2), 別の道=src_cell(u"n.csv", 1, 2))))          # 別の道の計算が違う(字の cell)
        self.assertEqual(FV.S_OK, self.j(t, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2), 別の道=src_cell(u"m.csv", 3, 2))))          # 別の道の計算が違う(別の数)
        self.assertEqual(FV.S_OK, self.j(t, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2))))                                        # 別の道が無い
        self.assertEqual(FV.S_OK, self.j(t, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2), 別の道=u"n.csv")))                        # 別の道が読めない
        self.assertEqual(FV.S_OK, self.j(t, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2), 別の道={u"file": u"n.csv"})))
        self.assertEqual(FV.S_2, self.j(t, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2), 別の道=src_rows_30000())))
        # 別 file でも別の数なら 2 道にならない(別の道の側の計算が違う)・出どころ側が違い別の道だけ合う時は根拠なし
        self.assertEqual(FV.S_OK, self.j(t, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2), 別の道=src_cell(u"j.csv", 2, 3))))
        self.assertEqual(FV.S_OK, self.j(t, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2), 別の道=src_cell(u"m.csv", 4, 2))))
        self.assertEqual(FV.S_OK, self.j(t, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2), 別の道=src_cell(u"n.csv", 2, 2, 1000))))
        self.assertEqual(FV.S_NOBASIS, self.j(t, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 3, 2), 別の道=src_cell(u"n.csv", 2, 2))))

    def test_s_2_a_pass_without_a_computable_equal_source_is_no_basis(self):
        t = self.present()
        base = crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2))
        self.assertEqual(FV.S_OK, self.j(t, base))
        cases = {
            u"出どころ無し": crow(u"a03", u"合う"),
            u"出どころが字": crow(u"a03", u"合う", 出どころ=u"m.csv"),
            u"種類が違う": crow(u"a03", u"合う", 出どころ=dict(src_cell(u"m.csv", 2, 2), **{u"種類": u"推測"})),
            u"倍率が字": crow(u"a03", u"合う", 出どころ=dict(src_cell(u"m.csv", 2, 2), **{u"表示の倍率": u"1"})),
            u"倍率が真偽": crow(u"a03", u"合う", 出どころ=dict(src_cell(u"m.csv", 2, 2), **{u"表示の倍率": True})),
            u"倍率が無い": crow(u"a03", u"合う", 出どころ={k: v for k, v in src_cell(u"m.csv", 2, 2).items() if k != u"表示の倍率"}),
            u"倍率が小数": crow(u"a03", u"合う", 出どころ=dict(src_cell(u"m.csv", 2, 2), **{u"表示の倍率": 1.0})),
            u"計算が違う": crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 3, 2)),
            u"倍率が違う": crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2, 1000)),
            u"file が無い": crow(u"a03", u"合う", 出どころ=src_cell(u"zz.csv", 2, 2)),
            u"file が folder の外": crow(u"a03", u"合う", 出どころ=src_cell(u"../m.csv", 2, 2)),
            u"位置が外": crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 99, 2)),
            u"位置が字": crow(u"a03", u"合う", 出どころ=dict(src_cell(u"m.csv", 2, 2), **{u"位置": u"B2"})),
            u"cell が字": crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 1, 1)),
            u"和の行が無い": crow(u"a03", u"合う", 出どころ=src_sum(u"m.csv", 2, [])),
            u"行の和が 0 行": crow(u"a03", u"合う", 出どころ=dict(src_rows(u"j.csv"), **{u"条件": [{u"列": u"科目", u"比べ方": u"等しい", u"値": u"無"}]})),
        }
        for name, row in cases.items():
            self.assertEqual(FV.S_NOBASIS, self.j(t, row), name)
        for bad in (u"abc", None, u"3.0", u"", u"３００００"):
            self.assertEqual(FV.S_NOBASIS, self.j(self.present(bad), base), repr(bad))
        self.assertEqual(FV.S_OK, self.j(self.present(30000), base))                                                                       # JSON の整数も 10 進の字として読む

    def test_s_3_the_three_source_kinds_and_the_display_multiplier_are_recomputed(self):
        self.assertEqual(FV.S_OK, self.j({u"id": u"a15", u"状態": u"在る", u"数値": u"15000"}, crow(u"a15", u"合う", 出どころ=src_sum(u"m.csv", 3, [2, 3]))))
        self.assertEqual(FV.S_OK, self.j({u"id": u"a16", u"状態": u"在る", u"数値": u"9000"}, crow(u"a16", u"合う", 出どころ=src_rows(u"j.csv"))))
        self.assertEqual(FV.S_OK, self.j({u"id": u"a13", u"状態": u"在る", u"数値": u"8000"}, crow(u"a13", u"合う", 出どころ=src_cell(u"m.csv", 6, 2, 1000))))
        self.assertEqual(FV.S_NOBASIS, self.j({u"id": u"a13", u"状態": u"在る", u"数値": u"8000"}, crow(u"a13", u"合う", 出どころ=src_cell(u"m.csv", 6, 2, 1))))
        self.assertEqual(FV.S_NOBASIS, self.j({u"id": u"a15", u"状態": u"在る", u"数値": u"15001"}, crow(u"a15", u"合う", 出どころ=src_sum(u"m.csv", 3, [2, 3]))))
        self.assertEqual(FV.S_NOBASIS, self.j({u"id": u"a16", u"状態": u"在る", u"数値": u"9000"}, crow(u"a16", u"合う", 出どころ=src_rows(u"j.csv", 10))))
        # 見出しの規則は当てない(行の見出しが違っても cell の数が合えば確認済み)
        self.assertEqual(FV.S_OK, self.j(self.present(), crow(u"a03", u"合う", 出どころ=dict(src_cell(u"m.csv", 2, 2), **{u"行の見出し": u"全く違う", u"列の見出し": u"全く違う"}))))

    def test_s_8_a_zero_or_negative_integer_multiplier_is_accepted_as_it_is(self):
        self.assertEqual(FV.S_OK, self.j({u"id": u"a03", u"状態": u"在る", u"数値": u"0"}, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2, 0))))
        self.assertEqual(FV.S_OK, self.j({u"id": u"a03", u"状態": u"在る", u"数値": u"-30000"}, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2, -1))))
        self.assertEqual(FV.S_NOBASIS, self.j({u"id": u"a03", u"状態": u"在る", u"数値": u"30000"}, crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2, -1))))

    def test_s_4_the_other_views_map_to_their_state(self):
        t = self.present()
        self.assertEqual(FV.S_NOBASIS, self.j(t, crow(u"a03", u"見つからない")))
        self.assertEqual(FV.S_MISMATCH, self.j(t, crow(u"a03", u"合わない")))
        self.assertEqual(FV.S_REVIEW, self.j(t, crow(u"a03", u"決めが要る")))
        for st in (u"無い", u"分からない"):
            n = {u"id": u"a03", u"状態": st, u"数値": None}
            self.assertEqual(FV.S_NONE_OK, self.j(n, crow(u"a03", u"無いで合う")), st)
            self.assertEqual(FV.S_NONE_OBJ, self.j(n, crow(u"a03", u"在るはず")), st)
            self.assertEqual(FV.S_REVIEW, self.j(n, crow(u"a03", u"決めが要る")), st)

    def test_s_5_no_answer_for_a_missing_row_a_view_outside_its_group_or_a_broken_form(self):
        t = self.present()
        n = {u"id": u"a03", u"状態": u"無い", u"数値": None}
        good = crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2))
        for name, args in (
            (u"表の行が無い", (None, good)), (u"根拠の行が無い", (t, None)), (u"表の状態が読めない", ({u"id": u"a03", u"状態": u"？"}, good)), (u"表の行が字", (u"x", good)),
            (u"見立てが無い", (t, {u"id": u"a03"})), (u"見立てが字でない", (t, {u"id": u"a03", u"見立て": 5})), (u"見立てが別の字", (t, crow(u"a03", u"たぶん合う"))),
            (u"在るの行に無いの見立て", (t, crow(u"a03", u"無いで合う"))), (u"在るの行に在るはず", (t, crow(u"a03", u"在るはず"))),
            (u"無いの行に合う", (n, good)), (u"無いの行に合わない", (n, crow(u"a03", u"合わない"))), (u"無いの行に見つからない", (n, crow(u"a03", u"見つからない"))),
            (u"根拠の行が並び", (t, [good])),
        ):
            self.assertEqual(FV.S_NA, self.j(*args), name)

    def test_s_6_the_fix_is_judged_by_the_number_the_checker_wrote_against_the_gold(self):
        mis = crow(u"a03", u"合わない", **{u"正しいと見る数値": u"30000"})
        self.assertEqual(u"直せた", FV.fix_name(FV.S_MISMATCH, mis, 30000))
        self.assertEqual(u"直せた", FV.fix_name(FV.S_NONE_OBJ, mis, 30000))
        self.assertEqual(u"直しが違う", FV.fix_name(FV.S_MISMATCH, mis, 30001))
        self.assertEqual(u"直しが違う", FV.fix_name(FV.S_MISMATCH, mis, None))       # 正解が null ならどんな数でも違う
        for v in (None, u"abc", u"3.5", u"", True):
            self.assertEqual(u"直しなし", FV.fix_name(FV.S_MISMATCH, crow(u"a03", u"合わない", **{u"正しいと見る数値": v}), 30000), repr(v))
        self.assertEqual(u"直しなし", FV.fix_name(FV.S_MISMATCH, {u"id": u"a03"}, 30000))
        for st in (FV.S_2, FV.S_OK, FV.S_NOBASIS, FV.S_REVIEW, FV.S_NONE_OK, FV.S_NA):
            self.assertIsNone(FV.fix_name(st, mis, 30000), st)

    def test_s_7_a_missing_or_broken_check_table_is_no_answer_for_every_row_and_duplicates_read_the_first(self):
        gold = gold_map()
        given = table_dict(alpha_rows())
        for ostate in (u"無し", u"読めない"):
            got = FV.status_rows(self.chk, self.src, given, ostate, {}, gold)
            self.assertEqual(30, len(got))
            self.assertTrue(all(v == (FV.S_NA, None) for v in got.values()), ostate)
        gold2 = dict(gold)
        gold2[u"a09"] = FV.UNREADABLE
        got = FV.status_rows(self.chk, self.src, given, u"読めた", {}, gold2)
        self.assertEqual(29, len(got))
        self.assertNotIn(u"a09", got)
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, u"根拠の表.json")
            rows_json(p, [crow(u"a03", u"決めが要る"), crow(u"a03", u"合う", 出どころ=src_cell(u"m.csv", 2, 2))])
            st, rows, dup = FV.read_table(p)
            self.assertEqual((u"読めた", 1), (st, dup))
            self.assertEqual(FV.S_REVIEW, FV.status_rows(self.chk, self.src, given, st, rows, gold)[u"a03"][0])


def src_rows_30000():
    u"""30000 になる別の file の出どころ(表の行の和)。"""
    return {u"種類": u"表の行の和", u"file": u"n.csv", u"頭の行": 1, u"額": {u"列": u"金額", u"符号": u"そのまま"},
            u"条件": [{u"列": u"科目", u"比べ方": u"等しい", u"値": u"x2"}], u"表示の倍率": 1}


# ======================================================================== 8. 型の席の束(--through)
class ThroughTest(unittest.TestCase):
    def test_r_1_the_um2_check_is_run_on_the_bundle_and_rows_are_judged_one_by_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp).build()
            chk = FV.load_check_module()
            rep, res = FV.through_report(chk, w.root, 201)
            self.assertEqual(u"受理", rep[u"束"])
            self.assertEqual(1, rep[u"判定"][u"止める"])
            self.assertEqual(29, rep[u"判定"][u"無いを受ける"])
            self.assertEqual(0, rep[u"判定"][u"通す"] + rep[u"判定"][u"断り"] + rep[u"判定"][u"判定なし"])
            self.assertTrue(rep[u"止めた規則"])
            self.assertTrue(set(rep[u"止めた規則"]) <= set(FV.RULE_NAMES))
            self.assertEqual(30, sum(rep[u"判定"].values()))

    def test_r_2_a_refused_bundle_is_refused_for_every_row_a_missing_file_is_not_judged_and_a_broken_one_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp).build()
            chk = FV.load_check_module()
            p = os.path.join(w.seat(u"type"), u"材料_期1_A.json")
            b = type_bundle()
            b[u"材料"] = b[u"材料"][:-1]
            wjson(p, b)
            rep, _ = FV.through_report(chk, w.root, 201)
            self.assertEqual((u"断り", 30), (rep[u"束"], rep[u"判定"][u"断り"]))
            self.assertEqual([u"K0"], rep[u"束の規則"])
            wtext(p, u"{broken")
            rep, _ = FV.through_report(chk, w.root, 201)
            self.assertEqual((u"断り", 30), (rep[u"束"], rep[u"判定"][u"断り"]))
            os.remove(p)
            rep, _ = FV.through_report(chk, w.root, 201)
            self.assertEqual((u"無し", 30), (rep[u"束"], rep[u"判定"][u"判定なし"]))

    def test_r_3_an_unmarked_rows_sum_is_not_counted_as_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp).build()
            chk = FV.load_check_module()
            self.assertEqual(u"通す(取り方は未確認)", FV.JUDGES[1])
            self.assertEqual((u"通す", u"無いを受ける"), FV.JUDGE_PASS)
            state, judged, ans, _res = FV.type_data(chk, w.seat(u"type"), gold_map(), forms_of())
            self.assertEqual(u"受理", state)
            self.assertEqual((u"止める", u"無いを受ける"), (FV.type_row_judge(state, judged, u"a03")[0], FV.type_row_judge(state, judged, u"a05")[0]))
            self.assertEqual(u"判定なし", FV.type_row_judge(state, judged, u"zz")[0])
            self.assertEqual(u"同じ", ans[u"a03"][0])
            self.assertEqual(u"無いで同じ", ans[u"a05"][0])
            self.assertEqual(u"決め:無い", ans[u"a12"][0])

    def test_r_4_the_command_prints_counts_and_writes_the_full_result_outside_the_seat(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp).build()
            rc, text, err = run_cli(["--through", "--root", w.root, "--company", "201"])
            self.assertEqual(0, rc, err)
            rep = json.loads(text)
            self.assertEqual(u"受理", rep[u"束"])
            self.assertNotIn(u"a03", text)
            self.assertTrue(os.path.exists(os.path.join(w.root, u"201", u"判定_型.json")))
            self.assertNotIn(u"判定_型.json", tree(w.seat(u"type")))


# ======================================================================== 9. 行ごとの照合・並べる表(手で決めた数。作り物の 1 社)
def want(test, c, **pairs):
    for k, v in pairs.items():
        test.assertEqual(v, c.get(k.replace(u"__", u":"), 0), k)


def kv(**pairs):
    return dict((k.replace(u"__", u":"), v) for k, v in pairs.items())


class WorldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.w = TB(cls.tmp).build()
        cls.rec = FV.tally([201], cls.w.co, cls.w.root, None)
        cls.c = cls.rec[u"数"]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)


class FillTest(WorldTest):
    def test_c_1_the_fill_names_are_counted_by_kind_for_each_round(self):
        c = self.c
        exp = {
            u"埋め:回a:普通:行の数": 21, u"埋め:回a:普通:同じ": 16, u"埋め:回a:普通:違う": 2, u"埋め:回a:普通:分からない": 1, u"埋め:回a:普通:形が読めない": 1, u"埋め:回a:普通:無いで違う": 1,
            u"埋め:回a:無い:行の数": 3, u"埋め:回a:無い:無いのに在る": 2, u"埋め:回a:無い:無いで同じ": 1,
            u"埋め:回a:罠:行の数": 4, u"埋め:回a:罠:違う": 2, u"埋め:回a:罠:同じ": 1, u"埋め:回a:罠:答えなし": 1, u"埋め:回a:罠を取った": 2,
            u"埋め:回a:決め:行の数": 2, u"埋め:回a:決め:決め:1つ目": 1, u"埋め:回a:決め:決め:2つ目": 1, u"埋め:回a:決め:自信高で数を出した": 2,
            u"埋め:回b:普通:行の数": 21, u"埋め:回b:普通:同じ": 16, u"埋め:回b:普通:違う": 2, u"埋め:回b:普通:分からない": 1, u"埋め:回b:普通:形が読めない": 1, u"埋め:回b:普通:無いで違う": 1,
            u"埋め:回b:無い:行の数": 3, u"埋め:回b:無い:無いのに在る": 1, u"埋め:回b:無い:無いで同じ": 2,
            u"埋め:回b:罠:行の数": 4, u"埋め:回b:罠:違う": 1, u"埋め:回b:罠:同じ": 2, u"埋め:回b:罠:答えなし": 1, u"埋め:回b:罠を取った": 1,
            u"埋め:回b:決め:行の数": 2, u"埋め:回b:決め:決め:1つ目": 1, u"埋め:回b:決め:決め:2つ目": 1, u"埋め:回b:決め:自信高で数を出した": 2,
            u"行の種類:普通": 21, u"行の種類:無い": 3, u"行の種類:罠": 4, u"行の種類:決め": 2,
            u"埋め:回a:表:読めた": 1, u"埋め:回b:表:読めた": 1,
        }
        for k, v in exp.items():
            self.assertEqual(v, c.get(k, 0), k)
        # どの回も 30 行(正解が読めない行は 0)。名の和は行の数と同じ
        for r in u"ab":
            for kind in FV.KINDS:
                names = FV.ALL_NAMES
                self.assertEqual(c[u"埋め:回%s:%s:行の数" % (r, kind)], sum(c.get(u"埋め:回%s:%s:%s" % (r, kind, n), 0) for n in names), (r, kind))
        self.assertEqual(0, c[u"正解が読めない行"])

    def test_c_2_the_two_rounds_are_compared_row_by_row(self):
        c = self.c
        self.assertEqual({u"埋め:揺れ:行の数": 30, u"埋め:揺れ:結果の名が同じ": 28, u"埋め:揺れ:在るどうし": 24, u"埋め:揺れ:在るどうしで数が同じ": 22,
                          u"埋め:揺れ:回αが違った行": 7, u"埋め:揺れ:回αが違った行のうち回βも同じ答え": 4},
                         dict((k, c[k]) for k in c if k.startswith(u"埋め:揺れ:")))

    def test_c_3_the_hand_decided_names_match_the_table_in_this_file(self):
        gold = FV.read_gold1(os.path.join(self.w.co, u"201", u"正解", u"正解.json"))
        forms = FV.read_forms(os.path.join(self.w.co, u"201", u"正解", u"罠.json"))
        st, rows, _d = FV.read_table(os.path.join(self.w.seat(u"fill-a"), u"値の表.json"))
        got = FV.fill_answers(gold, forms, st, rows)
        self.assertEqual(ALPHA_NAMES, dict((i, v[0]) for i, v in got.items()))
        self.assertEqual(KIND_OF, dict((i, v[4]) for i, v in got.items()))
        self.assertEqual([u"a01", u"a07"], [i for i, v in got.items() if v[2]])
        self.assertEqual([u"a12", u"a29"], [i for i, v in got.items() if v[4] == u"決め"])


class VerifyTest(WorldTest):
    def test_v_1_the_original_table_crosses_the_fill_names_with_the_eight_states(self):
        c = self.c
        for s, ids in ORIG_STATUS.items():
            self.assertEqual(len(ids), c[u"原:状態:" + s], s)
        cross = dict((k, v) for k, v in c.items() if k.startswith(u"原:") and u"×" in k and v)
        self.assertEqual({
            u"原:同じ×確認済み(2 道)": 1, u"原:同じ×確認済み": 4, u"原:同じ×要確認": 1, u"原:同じ×根拠なし": 11, u"原:無いで同じ×無いを確かめた": 1,
            u"原:違う×不一致": 1, u"原:違う×根拠なし": 2, u"原:違う×確認済み": 1, u"原:無いのに在る×根拠なし": 1, u"原:無いのに在る×不一致": 1,
            u"原:無いで違う×無いに異議": 1, u"原:分からない×無いに異議": 1, u"原:形が読めない×根拠なし": 1, u"原:答えなし×答えなし": 1,
            u"原:決め:1つ目×確認済み": 1, u"原:決め:2つ目×要確認": 1}, cross)
        self.assertEqual(30, c[u"原:行の数"])
        self.assertEqual(30, sum(cross.values()))
        self.assertEqual(8, c[u"原:通した"])

    def test_v_2_the_five_numbers_of_the_comparison_follow_the_decided_definitions(self):
        c = self.c
        self.assertEqual({u"取得": 6, u"止めすぎ": 12, u"通した誤り": 1, u"決めを通した": 1, u"通さなかった誤り": 6},
                         dict((k, c[u"並べる:埋め+確かめ:" + k]) for k in FV.METRICS))
        self.assertEqual({u"取得": 18, u"止めすぎ": 0, u"通した誤り": 7, u"決めを通した": 2, u"通さなかった誤り": 0},
                         dict((k, c[u"並べる:埋めのみ:" + k]) for k in FV.METRICS))
        self.assertEqual({u"取得": 3, u"止めすぎ": 1, u"通した誤り": 24, u"決めを通した": 2, u"通さなかった誤り": 0},
                         dict((k, c[u"並べる:型+検査:" + k]) for k in FV.METRICS))
        self.assertEqual((18, 7, 2), (c[u"原:同じの行"], c[u"原:誤りの行"], c[u"原:決めの行"]))
        self.assertEqual((1, 1), (c[u"原:決め:状態:確認済み"], c[u"原:決め:状態:要確認"]))

    def test_v_3_the_broken_table_counts_each_kind_with_its_states_and_its_fixes(self):
        c = self.c
        exp = {
            u"罠の値": {u"作った": 2, u"行の数": 2, u"通した": 1, u"通さなかった": 1, u"直せた": 1, u"状態:不一致": 1, u"状態:確認済み": 1},
            u"桁": {u"作った": 1, u"行の数": 1, u"通さなかった": 1, u"直せた": 1, u"状態:不一致": 1},
            u"隣": {u"作った": 1, u"行の数": 1, u"通した": 1, u"状態:確認済み": 1},
            u"無いのに在る": {u"作った": 1, u"行の数": 1, u"通さなかった": 1, u"直しなし": 1, u"状態:不一致": 1},
            u"在るのに無い": {u"作った": 1, u"行の数": 1, u"通さなかった": 1, u"直せた": 1, u"状態:無いに異議": 1},
        }
        for k in FV.MUT_KINDS:
            got = dict((x[len(u"壊:%s:" % k):], v) for x, v in c.items() if x.startswith(u"壊:%s:" % k) and v and not x.startswith(u"壊:作れなかった"))
            self.assertEqual(exp[k], got, k)
        self.assertEqual((0, 24, 1), (c[u"壊:作れなかった数"], c[u"壊:壊していない行"], c[u"壊:壊していない行で状態が違う"]))

    def test_v_4_the_status_command_matches_the_tally_and_writes_the_stage3_document_outside_the_seat(self):
        w = self.w
        for which, total_ok in ((u"orig", 8),):
            out = os.path.join(self.tmp, u"rows_%s.json" % which)
            doc = os.path.join(self.tmp, u"段3_%s.md" % which)
            rc, text, err = run_cli(["--status", "--co", w.co, "--root", w.root, "--company", "201", "--which", which, "--rows-out", out, "--doc-out", doc])
            self.assertEqual(0, rc, err)
            rep = json.loads(text)
            self.assertEqual(dict((s, len(ids)) for s, ids in ORIG_STATUS.items()), dict(rep[u"状態"]))
            self.assertEqual({u"直せた": 2, u"直しが違う": 1, u"直しなし": 1}, dict(rep[u"直し"]))
            rows = json.loads(read_text(out))
            self.assertEqual(30, len(rows))
            self.assertEqual(sum(1 for r in rows.values() if r[u"状態"] in FV.PASS_STATUSES), total_ok)
            body = read_text(doc)
            self.assertTrue(body.startswith(DOC_TEXT.rstrip(u"\n") + u"\n\n## 確かめの状態\n"))
            self.assertIn(u"## 確かめの状態", body)
            self.assertEqual(30, len(re.findall(u"^\\| a[0-9]{2} \\|", body, re.M)))
            self.assertIn(u"| a07 | ", body)
            self.assertTrue(body.rstrip().endswith(u"|"))
        self.assertFalse(os.path.exists(os.path.join(w.root, u"201", u"段3_orig.md")))
        rc, _t, _e = run_cli(["--status", "--co", w.co, "--root", w.root, "--company", "201", "--which", "broken"])
        self.assertEqual(0, rc)
        self.assertTrue(os.path.exists(os.path.join(w.root, u"201", u"段3_broken.md")))
        for k in FV.SEAT_KINDS:
            self.assertNotIn(u"段3", u" ".join(tree(w.seat(k))))

    def test_v_8_the_broken_status_reads_the_broken_seats_table_and_not_the_original_one(self):
        w = self.w
        rc, text, err = run_cli(["--status", "--co", w.co, "--root", w.root, "--company", "201", "--which", "broken", "--rows-out", os.path.join(self.tmp, u"rb.json")])
        self.assertEqual(0, rc, err)
        rep = json.loads(text)
        self.assertEqual({FV.S_2: 0, FV.S_OK: 7, FV.S_NOBASIS: 13, FV.S_MISMATCH: 5, FV.S_REVIEW: 2, FV.S_NONE_OK: 0, FV.S_NONE_OBJ: 3, FV.S_NA: 0}, dict(rep[u"状態"]))
        self.assertEqual({u"直せた": 5, u"直しが違う": 1, u"直しなし": 2}, dict(rep[u"直し"]))
        rows = json.loads(read_text(os.path.join(self.tmp, u"rb.json")))
        self.assertEqual((FV.S_MISMATCH, u"直せた"), (rows[u"a04"][u"状態"], rows[u"a04"][u"直し"]))
        self.assertEqual(FV.S_OK, rows[u"a09"][u"状態"])
        rc, text, _e = run_cli(["--status", "--co", w.co, "--root", w.root, "--company", "201", "--which", "orig"])
        self.assertEqual(1, json.loads(text)[u"状態"][FV.S_2])

    def test_v_5_the_stage3_document_does_not_change_a_sentence_of_the_alpha_document(self):
        w = self.w
        original = read_text(os.path.join(w.seat(u"fill-a"), u"資料.md"))
        doc = os.path.join(w.root, u"201", u"段3_orig.md")
        run_cli(["--status", "--co", w.co, "--root", w.root, "--company", "201", "--which", "orig"])
        self.assertTrue(read_text(doc).startswith(original.rstrip(u"\n") + u"\n\n## 確かめの状態\n\n| id | 項目 | 状態 |\n| --- | --- | --- |\n"))
        self.assertEqual(original, read_text(os.path.join(w.seat(u"fill-a"), u"資料.md")))

    def test_v_6_the_type_seat_rows_follow_the_decided_judgements(self):
        c = self.c
        self.assertEqual({u"型:束:受理": 1, u"型:行の数": 30, u"型:判定:止める": 1, u"型:判定:無いを受ける": 29, u"型:通した": 29,
                          u"型:同じ×止める": 1, u"型:無いで同じ×無いを受ける": 3, u"型:無いで違う×無いを受ける": 24, u"型:決め:無い×無いを受ける": 2},
                         dict((k, v) for k, v in c.items() if k.startswith(u"型:") and v and not k.startswith(u"型:止める:")))
        self.assertGreaterEqual(sum(v for k, v in c.items() if k.startswith(u"型:止める:")), 1)

    def test_v_7_the_world_predictions_follow_the_hand_decided_counts(self):
        p = self.rec[u"予測"]
        self.assertEqual(sorted(FV.BOUNDS), sorted(p))
        self.assertEqual(
            {u"UM4-M1": False, u"UM4-F1": False, u"UM4-F2": True, u"UM4-F3": True, u"UM4-F4": True, u"UM4-F5": True, u"UM4-V1": True, u"UM4-V2": False,
             u"UM4-V3": False, u"UM4-V4": True, u"UM4-V5": False, u"UM4-V6": True, u"UM4-V7": False, u"UM4-V8": False, u"UM4-V9": True, u"UM4-T1": False,
             u"UM4-T2": False, u"UM4-G1": False, u"UM4-G2": False, u"UM4-P1": None, u"UM4-P2": None},
            dict((k, v[u"当たり"]) for k, v in p.items()))
        self.assertEqual(FV.judge(self.rec), p)


# ======================================================================== 10. 過程の数
def write_transcript(tdir, name, folder, calls, first_text=None, ts0=0):
    lines = [{u"type": u"user", u"message": {u"role": u"user", u"content": first_text if first_text is not None else u"folder: %s\nお願いします" % folder},
              u"timestamp": u"2026-11-24T10:00:00Z"}]
    for k, (nm, inp) in enumerate(calls):
        lines.append({u"type": u"assistant", u"message": {u"role": u"assistant", u"content": [{u"type": u"text", u"text": u"考える"}, {u"type": u"tool_use", u"id": u"t%d" % k, u"name": nm, u"input": inp}]},
                      u"timestamp": u"2026-11-24T10:00:%02dZ" % (ts0 + 2 * k + 1)})
        lines.append({u"type": u"user", u"message": {u"role": u"user", u"content": [{u"type": u"tool_result", u"tool_use_id": u"t%d" % k, u"content": u"ok"}]},
                      u"timestamp": u"2026-11-24T10:00:%02dZ" % (ts0 + 2 * k + 2)})
    wtext(os.path.join(tdir, name + u".jsonl"), u"\n".join(json.dumps(x, ensure_ascii=False) for x in lines))


def seat_calls(root, kinds, cid=201):
    a = FV.seat_dir(root, cid, u"fill-a")
    o = FV.seat_dir(root, cid, u"check-orig")
    t = FV.seat_dir(root, cid, u"type")
    return {
        u"fill-a": (a, [(u"Bash", {u"command": u"cat %s/素材/t.csv" % a}), (u"Write", {u"file_path": a + u"/値の表.json", u"content": u"{}"}), (u"Bash", {u"command": u"ls /Users/someone/other"})]),
        u"check-orig": (o, [(u"Read", {u"file_path": o + u"/素材/m.csv"}), (u"Read", {u"file_path": o + u"/素材/j.csv"}), (u"Write", {u"file_path": o + u"/根拠の表.json", u"content": u"{}"}), (u"Write", {u"file_path": o + u"/根拠の表.json", u"content": u"{}"})]),
        u"type": (t, [(u"Read", {u"file_path": t + u"/期1/t.csv"})]),
    }


class ProcessTest(WorldTest):
    def test_d_1_each_seat_kind_has_the_hand_counted_numbers_and_the_pairing_is_by_folder(self):
        tdir = os.path.join(self.tmp, u"tr1")
        for k, (folder, calls) in seat_calls(self.w.root, None).items():
            write_transcript(tdir, k, folder, calls)
        index = FV.Transcripts(tdir)
        a = FV.process_seat(index, self.w.seat(u"fill-a"), u"fill-a")
        self.assertEqual(u"数えた", a[u"状態"])
        self.assertEqual((3, 1, 1, 2, 1, 1), (a[u"道具の呼び出し"], a[u"出力を書いた回数"], a[u"最初に出力を書くまでの呼び出し"] == 2, a[u"汚れた呼び出し"] + 1, a[u"汚れの席"], a[u"素材の file のうち path が出た数"]))
        self.assertEqual({u"Bash": 2, u"Write": 1}, a[u"道具の名ごと"])
        self.assertEqual((0, 0), (a[u"書き直した"], a[u"python を走らせた数"]))
        o = FV.process_seat(index, self.w.seat(u"check-orig"), u"check-orig")
        self.assertEqual((4, 2, 1, 0, 0, 2), (o[u"道具の呼び出し"], o[u"出力を書いた回数"], o[u"書き直した"], o[u"汚れた呼び出し"], o[u"汚れの席"], o[u"素材の file のうち path が出た数"]))
        t = FV.process_seat(index, self.w.seat(u"type"), u"type")
        self.assertEqual((1, 0, None, 0), (t[u"道具の呼び出し"], t[u"出力を書いた回数"], t[u"最初に出力を書くまでの呼び出し"], t[u"汚れた呼び出し"]))
        for kind in (u"fill-b", u"check-broken"):
            r = FV.process_seat(index, self.w.seat(kind), kind)
            self.assertEqual((u"過程が数えられない", u"記録が 0 本"), (r[u"状態"], r[u"理由"]))

    def test_d_2_the_output_names_differ_by_kind_so_a_check_seat_writing_the_fill_table_is_not_a_write(self):
        tdir = os.path.join(self.tmp, u"tr2")
        o = self.w.seat(u"check-orig")
        write_transcript(tdir, u"o", o, [(u"Write", {u"file_path": o + u"/値の表.json", u"content": u"{}"})])
        got = FV.process_seat(FV.Transcripts(tdir), o, u"check-orig")
        self.assertEqual(0, got[u"出力を書いた回数"])
        write_transcript(tdir, u"o2", o + u"x", [(u"Write", {u"file_path": o + u"x/根拠の表.json", u"content": u"{}"})])
        self.assertEqual(u"数えた", FV.process_seat(FV.Transcripts(tdir), o, u"check-orig")[u"状態"])

    def test_d_3_two_transcripts_for_one_folder_or_none_cannot_be_counted_and_a_record_without_a_tool_call_neither(self):
        tdir = os.path.join(self.tmp, u"tr3")
        a = self.w.seat(u"fill-a")
        write_transcript(tdir, u"one", a, [(u"Read", {u"file_path": a + u"/素材/t.csv"})])
        write_transcript(tdir, u"two", a, [(u"Read", {u"file_path": a + u"/素材/t.csv"})])
        r = FV.process_seat(FV.Transcripts(tdir), a, u"fill-a")
        self.assertEqual((u"過程が数えられない", u"記録が 2 本以上", 2), (r[u"状態"], r[u"理由"], r[u"本数"]))
        tdir2 = os.path.join(self.tmp, u"tr3b")
        write_transcript(tdir2, u"nocall", a, [])
        r = FV.process_seat(FV.Transcripts(tdir2), a, u"fill-a")
        self.assertEqual((u"過程が数えられない", u"tool_use が無い"), (r[u"状態"], r[u"理由"]))
        self.assertEqual(u"記録の folder が無い", FV.process_seat(None, a, u"fill-a")[u"理由"])
        # 席の folder が別の席の folder の頭の字になっていても対にならない(fill/a と fill/ab)
        tdir3 = os.path.join(self.tmp, u"tr3c")
        write_transcript(tdir3, u"ab", a + u"b", [(u"Read", {u"file_path": a + u"b/x"})])
        self.assertEqual(u"記録が 0 本", FV.process_seat(FV.Transcripts(tdir3), a, u"fill-a")[u"理由"])

    def test_d_4_a_path_outside_the_seat_folder_is_dirty_and_the_inside_and_the_final_report_are_not(self):
        a = self.w.seat(u"fill-a")
        v = FV.folder_variants(a)
        self.assertTrue(FV.is_dirty(u"cat /Users/x/y", v))
        self.assertTrue(FV.is_dirty(u"cat ../x", v))
        self.assertTrue(FV.is_dirty(u"cat ~/x", v))
        self.assertTrue(FV.is_dirty(u"echo $HOME", v))
        self.assertFalse(FV.is_dirty(u"cat %s/素材/t.csv" % a, v))
        self.assertFalse(FV.is_dirty(u"/usr/bin/python3 %s/x.py" % a, v))
        tdir = os.path.join(self.tmp, u"tr4")
        write_transcript(tdir, u"a", a, [(u"SubagentHandback", {u"message": u"/Users/x に書いた"}), (u"Bash", {u"command": u"cat /tmp/zz"})])
        got = FV.process_seat(FV.Transcripts(tdir), a, u"fill-a")
        self.assertEqual((2, 1), (got[u"道具の呼び出し"], got[u"汚れた呼び出し"]))

    def test_d_5_the_command_counts_every_seat_of_the_root_and_never_prints_a_folders_content(self):
        tdir = os.path.join(self.tmp, u"tr5")
        for k, (folder, calls) in seat_calls(self.w.root, None).items():
            write_transcript(tdir, k, folder, calls)
        rc, text, err = run_cli(["--process", "--transcripts", tdir, "--root", self.w.root, "--companies", "201"])
        self.assertEqual(0, rc, err)
        res = json.loads(text)
        self.assertEqual(5, len(res))
        self.assertEqual(3, sum(1 for v in res.values() if v[u"状態"] == u"数えた"))

    def test_d_6_per_company_calls_are_added_by_method_only_when_every_seat_was_counted(self):
        tdir = os.path.join(self.tmp, u"tr6")
        for k, (folder, calls) in seat_calls(self.w.root, None).items():
            write_transcript(tdir, k, folder, calls)
        rec = FV.tally([201], self.w.co, self.w.root, tdir)
        c = rec[u"数"]
        self.assertEqual((1, 7, 1, 1), (c[u"P1:埋め+確かめ:数えた"], c[u"P1:埋め+確かめ:道具の呼び出し"], c[u"P1:型:数えた"], c[u"P1:型:道具の呼び出し"]))
        self.assertEqual((7, 1), (c[u"過程:作り方:埋め+確かめ:道具の呼び出し"], c[u"過程:作り方:型:道具の呼び出し"]))
        self.assertEqual((5, 3, 2), (c[u"過程:席の数"], c[u"過程:数えた席"], c[u"過程:数えられない席"]))
        self.assertEqual((1, 1), (c[u"過程:汚れの席"], c[u"過程:汚れた呼び出し"]))
        self.assertEqual((7, 1), (c[u"過程:埋めa:道具の呼び出しの数"] + c[u"過程:確かめ原:道具の呼び出しの数"], c[u"過程:型:道具の呼び出しの数"]))
        self.assertEqual(1, c[u"過程:書き直した"])
        self.assertEqual(dict((FV.SEAT_LABEL[k], 1) for k in FV.SEAT_KINDS), dict((FV.SEAT_LABEL[k], c[u"過程:%s:席の数" % FV.SEAT_LABEL[k]]) for k in FV.SEAT_KINDS))
        self.assertEqual({u"埋めb": 1, u"確かめ壊": 1}, dict((FV.SEAT_LABEL[k], c[u"過程:%s:数えられない席" % FV.SEAT_LABEL[k]]) for k in (u"fill-b", u"check-broken")))
        self.assertEqual(0, sum(c[u"過程:%s:数えられない席" % FV.SEAT_LABEL[k]] for k in (u"fill-a", u"check-orig", u"type")))
        self.assertEqual((1, 7, 1), (c[u"過程:埋めa:汚れの席"], c[u"過程:埋めa:道具の呼び出しの数"] + c[u"過程:確かめ原:道具の呼び出しの数"], c[u"過程:型:道具の呼び出しの数"]))
        self.assertEqual(10, c[u"読んだ file の数"])
        self.assertTrue(rec[u"予測"][u"UM4-P2"][u"当たり"])
        self.assertTrue(rec[u"予測"][u"UM4-P1"][u"当たり"])        # 1 社だけで 7 > 1(会社の数 1 の分母。封の 4 社ではない)
        seats = rec[u"席ごと"]
        self.assertEqual(sorted(u"201:" + FV.SEAT_LABEL[k] for k in FV.SEAT_KINDS), sorted(seats))
        self.assertEqual(3, sum(v[u"数えた"] for v in seats.values()))

    def test_d_7_the_digest_writes_one_file_per_counted_seat_and_a_rows_file_with_the_gold_outside_the_repo(self):
        tdir = os.path.join(self.tmp, u"tr7")
        for k, (folder, calls) in seat_calls(self.w.root, None).items():
            write_transcript(tdir, k, folder, calls)
        out = os.path.join(self.tmp, u"dg")
        rc, text, err = run_cli(["--digest", "--co", self.w.co, "--root", self.w.root, "--transcripts", tdir, "--out-dir", out, "--companies", "201"])
        self.assertEqual(0, rc, err)
        self.assertEqual({u"書いた数": 4, u"書かなかった数": 2}, json.loads(text))
        names = sorted(os.listdir(out))
        self.assertEqual([u"201_型.md", u"201_埋めa.md", u"201_確かめ原.md", u"行の読み_201.md"], names)
        rows = read_text(os.path.join(out, u"行の読み_201.md"))
        self.assertEqual(30, len(re.findall(u"^\\| a[0-9]{2} \\|", rows, re.M)))
        self.assertIn(u"| a07 | 罠 | 違う | 13000 | 12000 | 確認済み |", rows)
        self.assertIn(u"(壊した: 桁)", rows)
        seat_md = read_text(os.path.join(out, u"201_埋めa.md"))
        self.assertIn(u"## 道具の呼び出しの順", seat_md)


# ======================================================================== 11. 予測 21 本の境
def rec_of(n_co=4, per_company=None, **kw):
    c = dict((k.replace(u"__", u":").replace(u"_P_", u"+"), v) for k, v in kw.items())
    return {u"会社の数": n_co, u"数": c, u"会社ごと": per_company or {}}


def flips(test, pid, low, high, key=u"当たり"):
    test.assertIs(False, FV.judge(low)[pid][key], (pid, u"低い側"))
    test.assertIs(True, FV.judge(high)[pid][key], (pid, u"高い側"))


class JudgeTest(unittest.TestCase):
    def test_j_1_the_judge_names_the_twentyone_and_reads_only_the_counts(self):
        out = FV.judge(rec_of())
        self.assertEqual(sorted(FV.BOUNDS), sorted(out))
        self.assertEqual(21, len(out))
        self.assertTrue(all(v[u"当たり"] is None for k, v in out.items() if k not in (u"UM4-M1", u"UM4-P2")))
        self.assertIsNone(FV.judge({})[u"UM4-F1"][u"当たり"])

    def test_j_2_m1_and_the_four_fill_predictions_flip_at_their_sealed_numbers(self):
        flips(self, u"UM4-M1", rec_of(素材__直しなしで通った社=2), rec_of(素材__直しなしで通った社=3))
        flips(self, u"UM4-F1", rec_of(埋め__回a__普通__同じ=159, 埋め__回a__普通__行の数=168), rec_of(埋め__回a__普通__同じ=160, 埋め__回a__普通__行の数=168))
        self.assertIs(True, FV.judge(rec_of(埋め__回a__普通__同じ=80, 埋め__回b__普通__同じ=80, 埋め__回a__普通__行の数=84, 埋め__回b__普通__行の数=84))[u"UM4-F1"][u"当たり"])
        flips(self, u"UM4-F2", rec_of(埋め__回a__罠を取った=1, 埋め__回a__罠__行の数=16), rec_of(埋め__回a__罠を取った=1, 埋め__回b__罠を取った=1, 埋め__回a__罠__行の数=16))
        flips(self, u"UM4-F3", rec_of(埋め__回a__無い__無いのに在る=1, 埋め__回a__無い__行の数=12), rec_of(埋め__回a__無い__無いのに在る=2, 埋め__回a__無い__行の数=12))
        flips(self, u"UM4-F4", rec_of(埋め__回a__決め__自信高で数を出した=7, 埋め__回a__決め__行の数=16), rec_of(埋め__回a__決め__自信高で数を出した=8, 埋め__回a__決め__行の数=16))
        lo = rec_of(埋め__揺れ__回αが違った行=4, 埋め__揺れ__回αが違った行のうち回βも同じ答え=1)
        hi = rec_of(埋め__揺れ__回αが違った行=4, 埋め__揺れ__回αが違った行のうち回βも同じ答え=2)
        flips(self, u"UM4-F5", lo, hi)
        self.assertIsNone(FV.judge(rec_of(埋め__揺れ__回αが違った行=2, 埋め__揺れ__回αが違った行のうち回βも同じ答え=2))[u"UM4-F5"][u"当たり"])      # 分母が 3 未満は判定しない
        self.assertIs(True, FV.judge(rec_of(埋め__揺れ__回αが違った行=3, 埋め__揺れ__回αが違った行のうち回βも同じ答え=2))[u"UM4-F5"][u"当たり"])

    def test_j_3_the_original_table_predictions_flip_at_their_sealed_numbers(self):
        flips(self, u"UM4-V1", rec_of(並べる__埋め_P_確かめ__通した誤り=0, 原__誤りの行=5), rec_of(並べる__埋め_P_確かめ__通した誤り=1, 原__誤りの行=5))
        flips(self, u"UM4-V2", rec_of(並べる__埋め_P_確かめ__取得=84, 原__同じの行=100), rec_of(並べる__埋め_P_確かめ__取得=85, 原__同じの行=100))
        flips(self, u"UM4-V3", rec_of(原__決め__状態__要確認=3, 原__決めの行=8), rec_of(原__決め__状態__要確認=4, 原__決めの行=8))
        self.assertIsNone(FV.judge(rec_of(並べる__埋め_P_確かめ__通した誤り=0, 原__誤りの行=0))[u"UM4-V1"][u"当たり"])

    def test_j_4_the_broken_table_predictions_flip_at_their_sealed_numbers(self):
        flips(self, u"UM4-V4", rec_of(壊__罠の値__行の数=8, 壊__罠の値__通した=0), rec_of(壊__罠の値__行の数=8, 壊__罠の値__通した=1))
        v5 = lambda a, b: rec_of(壊__桁__行の数=4, 壊__隣__行の数=4, 壊__桁__通した=a, 壊__隣__通した=b)
        self.assertIs(True, FV.judge(v5(0, 0))[u"UM4-V5"][u"当たり"])
        self.assertIs(False, FV.judge(v5(1, 0))[u"UM4-V5"][u"当たり"])
        self.assertIs(False, FV.judge(v5(0, 1))[u"UM4-V5"][u"当たり"])
        self.assertIs(True, FV.judge(rec_of(壊__無いのに在る__行の数=4, 壊__無いのに在る__通した=0))[u"UM4-V6"][u"当たり"])
        self.assertIs(False, FV.judge(rec_of(壊__無いのに在る__行の数=4, 壊__無いのに在る__通した=1))[u"UM4-V6"][u"当たり"])
        flips(self, u"UM4-V7", rec_of(壊__在るのに無い__行の数=4, 壊__在るのに無い__状態__無いに異議=2), rec_of(壊__在るのに無い__行の数=4, 壊__在るのに無い__状態__無いに異議=3))
        self.assertIs(False, FV.judge(rec_of(壊__在るのに無い__行の数=2, 壊__在るのに無い__状態__無いに異議=2))[u"UM4-V7"][u"当たり"])        # 数の境は数のまま動かさない
        lo = rec_of(壊__罠の値__状態__不一致=6, 壊__罠の値__直せた=4, 壊__桁__状態__無いに異議=4, 壊__桁__直せた=3)
        hi = rec_of(壊__罠の値__状態__不一致=6, 壊__罠の値__直せた=4, 壊__桁__状態__無いに異議=4, 壊__桁__直せた=4)
        flips(self, u"UM4-V8", lo, hi)
        self.assertIs(False, FV.judge(rec_of(壊__壊していない行=96, 壊__壊していない行で状態が違う=11))[u"UM4-V9"][u"当たり"])
        self.assertIs(True, FV.judge(rec_of(壊__壊していない行=96, 壊__壊していない行で状態が違う=10))[u"UM4-V9"][u"当たり"])
        for pid in (u"UM4-V4", u"UM4-V5", u"UM4-V6", u"UM4-V7", u"UM4-V8", u"UM4-V9"):
            self.assertIsNone(FV.judge(rec_of())[pid][u"当たり"], pid)             # 対象の行が 1 つも無ければ判定しない

    def test_j_5_the_type_seat_and_comparison_predictions_flip_at_their_sealed_numbers(self):
        self.assertIs(True, FV.judge(rec_of(型__行の数=120, 型__通した=84))[u"UM4-T1"][u"当たり"])
        self.assertIs(False, FV.judge(rec_of(型__行の数=120, 型__通した=85))[u"UM4-T1"][u"当たり"])
        self.assertIs(True, FV.judge(rec_of(型__行の数=100, 型__通した=70))[u"UM4-T1"][u"当たり"])             # 割合の境は分母が減っても割合
        self.assertIs(False, FV.judge(rec_of(型__行の数=100, 型__通した=71))[u"UM4-T1"][u"当たり"])
        self.assertIs(True, FV.judge(rec_of(型__行の数=120, 並べる__型_P_検査__通した誤り=0))[u"UM4-T2"][u"当たり"])
        self.assertIs(False, FV.judge(rec_of(型__行の数=120, 並べる__型_P_検査__通した誤り=1))[u"UM4-T2"][u"当たり"])
        base = dict(型__行の数=120, 原__行の数=120, 並べる__型_P_検査__取得=50)
        self.assertIs(False, FV.judge(rec_of(**dict(base, 並べる__埋め_P_確かめ__取得=64)))[u"UM4-G1"][u"当たり"])
        self.assertIs(True, FV.judge(rec_of(**dict(base, 並べる__埋め_P_確かめ__取得=65)))[u"UM4-G1"][u"当たり"])
        self.assertIsNone(FV.judge(rec_of(並べる__埋め_P_確かめ__取得=65))[u"UM4-G1"][u"当たり"])
        eq = dict(base, 並べる__埋め_P_確かめ__通した誤り=3, 並べる__埋め_P_確かめ__決めを通した=1, 並べる__型_P_検査__通した誤り=2, 並べる__型_P_検査__決めを通した=2)
        self.assertIs(False, FV.judge(rec_of(**eq))[u"UM4-G2"][u"当たり"])
        self.assertIs(True, FV.judge(rec_of(**dict(eq, 並べる__埋め_P_確かめ__通した誤り=4)))[u"UM4-G2"][u"当たり"])
        self.assertIs(False, FV.judge(rec_of(**dict(eq, 並べる__埋め_P_確かめ__通した誤り=2)))[u"UM4-G2"][u"当たり"])

    def test_j_6_p1_needs_every_company_counted_and_one_company_not_above_decides_it_false(self):
        def pcs(fill_check, typ):
            return dict((str(5 + k), {u"P1:埋め+確かめ:数えた": 1, u"P1:型:数えた": 1, u"P1:埋め+確かめ:道具の呼び出し": fc, u"P1:型:道具の呼び出し": ty})
                        for k, (fc, ty) in enumerate(zip(fill_check, typ)))
        self.assertIs(True, FV.judge(rec_of(per_company=pcs([5, 6, 7, 8], [4, 5, 6, 7])))[u"UM4-P1"][u"当たり"])
        self.assertIs(False, FV.judge(rec_of(per_company=pcs([5, 6, 7, 8], [4, 5, 6, 8])))[u"UM4-P1"][u"当たり"])        # 同じは外れ
        self.assertIs(False, FV.judge(rec_of(per_company=pcs([5, 6, 7, 8], [4, 5, 6, 9])))[u"UM4-P1"][u"当たり"])
        three = pcs([5, 6, 7], [4, 5, 6])
        self.assertIsNone(FV.judge(rec_of(per_company=three))[u"UM4-P1"][u"当たり"])                                 # 1 社が数えられない
        three[u"8"] = {u"P1:埋め+確かめ:数えられない": 1, u"P1:型:数えた": 1, u"P1:型:道具の呼び出し": 1}
        self.assertIsNone(FV.judge(rec_of(per_company=three))[u"UM4-P1"][u"当たり"])
        three[u"5"][u"P1:型:道具の呼び出し"] = 5
        self.assertIs(False, FV.judge(rec_of(per_company=three))[u"UM4-P1"][u"当たり"])                              # 数えた社の中に同じが在れば他が数えられなくても外れ

    def test_j_7_p2_is_one_or_more_dirty_seats_and_is_not_judged_when_a_seat_could_not_be_counted(self):
        self.assertIs(True, FV.judge(rec_of(過程__席の数=20, 過程__汚れの席=1))[u"UM4-P2"][u"当たり"])
        self.assertIs(False, FV.judge(rec_of(過程__席の数=20, 過程__汚れの席=0, 過程__数えられない席=0))[u"UM4-P2"][u"当たり"])
        self.assertIsNone(FV.judge(rec_of(過程__席の数=20, 過程__汚れの席=0, 過程__数えられない席=1))[u"UM4-P2"][u"当たり"])
        self.assertIs(True, FV.judge(rec_of(過程__席の数=20, 過程__汚れの席=1, 過程__数えられない席=3))[u"UM4-P2"][u"当たり"])

    def test_j_8_the_judge_is_pure_and_returns_the_same_for_the_same_counts(self):
        rec = rec_of(素材__直しなしで通った社=3, 型__行の数=120, 型__通した=84)
        a = json.dumps(FV.judge(rec), ensure_ascii=False)
        self.assertEqual(a, json.dumps(FV.judge(copy.deepcopy(rec)), ensure_ascii=False))
        self.assertEqual({u"会社の数": 4, u"数": rec[u"数"], u"会社ごと": {}}, rec)


# ======================================================================== 12. 落ちない・記録
FORBIDDEN_WORDS = (u".csv", u".json", u".md", u".py", u".xlsx", u"仕訳帳", u"売上高", u"純資産", u"現金", u"借入金", u"営業利益", u"経常利益", u"減価償却", u"勘定",
                   u"円", u"/private", u"/Users", u"scratchpad", u"罠.json", u"正解.json")


SEAT_FIELDS = set([u"数えた", u"道具の呼び出し", u"席の発言の回", u"秒", u"素材の file の数", u"素材の file のうち path が出た数", u"素材の file のうち 2 回以上の数",
                   u"最大の file に触れた", u"最初に出力を書くまでの呼び出し", u"出力を書いた回数", u"書き直した", u"資料を書いた回数", u"script を書いた数",
                   u"python を走らせた数", u"道具が誤りを返した数", u"汚れた呼び出し", u"汚れの席"])


def record_problems(rec, companies=(5, 6, 7, 8)):
    out = []
    keys = [u"会社の数", u"外した社の数", u"数", u"会社ごと", u"席ごと", u"読んだ file の sha256 の束ね", u"限界", u"欄の説明", u"予測"]
    if not isinstance(rec, dict) or sorted(rec) != sorted(keys):
        return [u"記録の頂の鍵"]
    sha = rec[u"読んだ file の sha256 の束ね"]
    if not isinstance(sha, str) or not re.match(r"^[0-9a-f]{64}\Z", sha):
        out.append(u"sha256 の形")
    body = json.dumps(dict((k, v) for k, v in rec.items() if k != u"読んだ file の sha256 の束ね"), ensure_ascii=False)
    for w in FORBIDDEN_WORDS:
        if w in body:
            out.append(u"記録に禁止の字: " + w)
    if re.search(u"[0-9]{4}-[0-9]{2}-[0-9]{2}", body):
        out.append(u"日付の形")
    if re.search(u"[0-9]{6,}", body):
        out.append(u"長い数(額の形)")
    if not (isinstance(rec[u"外した社の数"], int) and not isinstance(rec[u"外した社の数"], bool)) or rec[u"外した社の数"] < 0 or rec[u"外した社の数"] + rec[u"会社の数"] != len(companies):
        out.append(u"外した社の数 + 数えた社の数 が社の数と違う")
    if rec[u"会社の数"] != len(rec[u"会社ごと"]):
        out.append(u"会社の数と会社ごとの数が違う")
    allowed = set(FV.FIXED_COUNTS) | set(u"素材:規則 NG:" + r for r in FV.MATERIAL_RULES)
    stray = [k for k in rec[u"数"] if k not in allowed]
    if stray:
        out.append(u"数の鍵が決まった集合の外: %d" % len(stray))
    for row in rec[u"会社ごと"].values():
        if [k for k in row if k not in allowed]:
            out.append(u"会社ごとの鍵が決まった集合の外")
    for k, row in rec[u"席ごと"].items():
        if not re.match(u"^[0-9]+:(%s)\\Z" % u"|".join(FV.SEAT_LABEL.values()), k):
            out.append(u"席ごとの鍵の形")
        if [f for f in row if f not in SEAT_FIELDS and not f.endswith(u"が無い")]:
            out.append(u"席ごとの欄の名")
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in rec[u"数"].values()):
        out.append(u"数が整数でない")
    for k in FV.FIXED_COUNTS:
        if k not in rec[u"数"]:
            out.append(u"数の欄が無い: " + k)
    if not set(rec[u"会社ごと"]) <= set(str(i) for i in companies):
        out.append(u"会社ごとの会社")
    for row in list(rec[u"席ごと"].values()) + list(rec[u"会社ごと"].values()):
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in row.values()):
            out.append(u"席ごと・会社ごとが整数でない")
    if sorted(rec[u"予測"]) != sorted(FV.BOUNDS):
        out.append(u"予測の数")
    for v in rec[u"予測"].values():
        if v[u"当たり"] not in (True, False, None):
            out.append(u"当たりの値")
    if not rec[u"限界"] or not all(isinstance(x, str) and x for x in rec[u"限界"]):
        out.append(u"限界の欄")
    return out


class RecordTest(WorldTest):
    def test_h_1_the_record_state_is_stated_and_checked(self):
        path = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(path):
            self.assertFalse(os.path.exists(path), u"記録はまだ無い(本番は未実行。記録の無い状態で緑)")
            return
        self.assertEqual([], record_problems(json.loads(read(RECORD_REL))))

    def test_h_2_the_record_the_script_builds_has_the_shape_the_predictions_and_no_forbidden_word(self):
        rec = json.loads(json.dumps(self.rec, ensure_ascii=False))
        self.assertEqual([], record_problems(rec, companies=(201,)))
        self.assertNotEqual([], record_problems(rec))              # 本番の 4 社でない記録は本番の形として赤
        self.assertEqual(21, len(rec[u"予測"]))
        self.assertEqual(FV.judge(rec), rec[u"予測"])

    def test_h_3_the_record_check_turns_red_for_a_forbidden_word_a_value_a_wrong_count_and_a_missing_key(self):
        good = json.loads(json.dumps(self.rec, ensure_ascii=False))
        for word in (u"仕訳帳.csv", u"値の表.json", u"資料.md", u"売上高", u"2024-04-01", u"1234567", u"勘定甲03", u"3,000円", u"正解.json"):
            bad = copy.deepcopy(good)
            bad[u"数"][u"x:" + word] = 1
            self.assertNotEqual([], record_problems(bad, companies=(201,)), word)
        bad = copy.deepcopy(good)
        bad[u"数"][u"原:行の数"] = u"30"
        self.assertNotEqual([], record_problems(bad, companies=(201,)))
        bad = copy.deepcopy(good)
        del bad[u"数"][u"壊:壊していない行"]
        self.assertNotEqual([], record_problems(bad, companies=(201,)))
        bad = copy.deepcopy(good)
        bad[u"読んだ file の sha256 の束ね"] = u"abc"
        self.assertNotEqual([], record_problems(bad, companies=(201,)))
        bad = copy.deepcopy(good)
        bad[u"予測"][u"UM4-G1"][u"当たり"] = u"はい"
        self.assertNotEqual([], record_problems(bad, companies=(201,)))
        for key in (u"x:無い項目の字", u"原:決め:状態:a07", u"埋め:回a:普通:行の数:a03", u"素材:規則 NG:売上高_当期"):
            bad = copy.deepcopy(good)
            bad[u"数"][key] = 1
            self.assertNotEqual([], record_problems(bad, companies=(201,)), key)
        bad = copy.deepcopy(good)
        bad[u"会社ごと"][u"201"][u"x:素材の字"] = 1
        self.assertNotEqual([], record_problems(bad, companies=(201,)))
        bad = copy.deepcopy(good)
        bad[u"席ごと"][u"201:売上高"] = {u"数えた": 1}
        self.assertNotEqual([], record_problems(bad, companies=(201,)))
        bad = copy.deepcopy(good)
        bad[u"席ごと"][u"201:型"][u"x"] = 1
        self.assertNotEqual([], record_problems(bad, companies=(201,)))
        bad = copy.deepcopy(good)
        bad[u"外した社の数"] = 1
        self.assertNotEqual([], record_problems(bad, companies=(201,)))                     # 外した + 数えた が社の数と合わない
        bad[u"外した社の数"] = u"0"
        self.assertNotEqual([], record_problems(bad, companies=(201,)))
        self.assertNotEqual([], record_problems({}))
        self.assertNotEqual([], record_problems(None))

    def test_h_4_the_record_holds_no_per_row_form_no_item_name_and_no_file_name(self):
        body = json.dumps(self.rec, ensure_ascii=False)
        for leak in list(GOLD_NAMES.values()) + [u"t.csv", u"m.csv", u"j.csv", u"110000", u"a01", u"a17", u"罠.json"]:
            self.assertNotIn(leak, body, leak)
        for row in self.rec[u"席ごと"].values():
            self.assertTrue(all(isinstance(v, int) for v in row.values()))

    def test_h_5_the_record_command_writes_nothing_unless_every_company_not_excluded_is_there(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, u"記録.json")
            co, root = os.path.join(tmp, u"co"), os.path.join(tmp, u"root")

            def mk(co_ids, root_ids):
                for base, ids in ((co, co_ids), (root, root_ids)):
                    shutil.rmtree(base, ignore_errors=True)
                    os.makedirs(base)
                    for i in ids:
                        os.makedirs(os.path.join(base, str(i)))

            def run(*extra):
                rc, _o, err = run_cli(["--tally", "--record", "--co", co, "--root", root, "--out", out] + list(extra))
                self.assertNotIn("Traceback", err)
                return rc
            cases = [
                ((), (), []), ((5, 6, 7), (5, 6, 7), []), ((201,), (201,), []),
                ((5, 6, 7, 8), (5, 6, 7), []),                         # root だけ欠ける
                ((5, 6, 7), (5, 6, 7, 8), []),                         # co だけ欠ける
                ((5, 6, 7), (5, 6, 7), [u"7"]),                        # 外した社の分では足りない
                ((5, 6), (5, 6), [u"7", u"8", u"9"]),                  # 外す社は 5〜8 の中
                ((5, 6, 7, 8), (5, 6, 7, 8), [u"5", u"6", u"7", u"8"]),  # 数える社が 0
            ]
            for co_ids, root_ids, ex in cases:
                mk(co_ids, root_ids)
                self.assertEqual(2, run(*(["--exclude"] + ex if ex else [])), (co_ids, root_ids, ex))
                self.assertFalse(os.path.exists(out), (co_ids, root_ids, ex))

    def test_h_6_the_record_command_writes_the_record_for_four_or_for_the_not_excluded_companies(self):
        for ids, ex, want_counted, want_out in (((5, 6, 7, 8), [], 4, 0), ((5, 6, 7), [u"8"], 3, 1), ((5, 8), [u"6", u"7"], 2, 2), ((5, 6, 7, 8), [u"5"], 3, 1)):
            with tempfile.TemporaryDirectory() as tmp:
                for i in ids:
                    for base in (u"co", u"root"):
                        os.makedirs(os.path.join(tmp, base, str(i)))
                if ex == [u"5"]:
                    shutil.rmtree(os.path.join(tmp, u"co", u"5"))
                    shutil.rmtree(os.path.join(tmp, u"root", u"5"))
                out = os.path.join(tmp, u"記録.json")
                rc, _o, err = run_cli(["--tally", "--record", "--co", os.path.join(tmp, u"co"), "--root", os.path.join(tmp, u"root"), "--out", out] + (["--exclude"] + ex if ex else []))
                self.assertEqual(0, rc, err)
                rec = json.loads(read_text(out))
            self.assertEqual((want_counted, want_out), (rec[u"会社の数"], rec[u"外した社の数"]))
            self.assertEqual(4, rec[u"会社の数"] + rec[u"外した社の数"])
            self.assertEqual([], record_problems(rec))
            self.assertEqual(want_counted, rec[u"数"][u"正解が読めない社"])
            self.assertEqual(want_counted, rec[u"数"][u"素材:社の数"])
            self.assertEqual(sorted(str(i) for i in ids if str(i) not in ex), sorted(rec[u"会社ごと"]))
            self.assertNotIn(u"外した社の番号", json.dumps(rec, ensure_ascii=False))

    def test_h_7_the_record_command_without_out_writes_to_the_fixed_place_under_its_own_root(self):
        real = os.path.join(ROOT, RECORD_REL)
        before = (os.path.exists(real), read_bytes(RECORD_REL) if os.path.exists(real) else None)
        with tempfile.TemporaryDirectory() as tmp:
            for i in (5, 6, 7, 8):
                for base in (u"co", u"root"):
                    os.makedirs(os.path.join(tmp, base, str(i)))
            fake = os.path.join(tmp, u"fake", u"audit-core")
            os.makedirs(os.path.join(fake, u"measure"))
            copy_to = os.path.join(fake, SCRIPT_REL)
            shutil.copyfile(os.path.join(ROOT, SCRIPT_REL), copy_to)
            r = subprocess.run([sys.executable, "-I", copy_to, "--tally", "--record", "--co", os.path.join(tmp, u"co"), "--root", os.path.join(tmp, u"root")],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(0, r.returncode, r.stderr.decode("utf-8", "replace"))
            self.assertEqual(b"", r.stdout)
            placed = os.path.join(fake, RECORD_REL)
            self.assertTrue(os.path.exists(placed))
            self.assertEqual(4, json.loads(read_text(placed))[u"会社の数"])
        self.assertEqual(before, (os.path.exists(real), read_bytes(RECORD_REL) if os.path.exists(real) else None))

    def test_h_8_the_first_failed_companies_given_on_the_command_line_are_the_only_ones_not_counted_as_first_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in (5, 6):
                make_company(os.path.join(tmp, u"co"), i)
            rec = FV.tally([5, 6], os.path.join(tmp, u"co"), os.path.join(tmp, u"root"), None, first_ng=[6])
            c = rec[u"数"]
            self.assertEqual((2, 2, 1, 1), (c[u"素材:社の数"], c[u"素材:形の検査に通った社"], c[u"素材:直しなしで通った社"], c[u"素材:最初に落ちた社"]))
            self.assertIs(False, rec[u"予測"][u"UM4-M1"][u"当たり"])
            shutil.rmtree(os.path.join(tmp, u"co", u"5", u"期1"))
            rec = FV.tally([5, 6], os.path.join(tmp, u"co"), os.path.join(tmp, u"root"), None, first_ng=[])
            c = rec[u"数"]
            self.assertEqual((1, 1, 1), (c[u"素材:形の検査に通った社"], c[u"素材:形の検査に通らなかった社"], c[u"素材:直しなしで通った社"]))
            self.assertGreaterEqual(c[u"素材:規則 NG:素材の file が在る"], 1)

    def test_h_9_the_command_reads_first_ng_numbers_after_the_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_company(os.path.join(tmp, u"co"), 5)
            out = os.path.join(tmp, u"r.json")
            rc, _o, err = run_cli(["--tally", "--co", os.path.join(tmp, u"co"), "--root", os.path.join(tmp, u"root"), "--companies", "5", "--material-first-ng", "5", "--out", out])
            self.assertEqual(0, rc, err)
            c = json.loads(read_text(out))[u"数"]
            self.assertEqual((1, 0, 1), (c[u"素材:最初に落ちた社"], c[u"素材:直しなしで通った社"], c[u"素材:形の検査に通った社"]))


class CrashTest(unittest.TestCase):
    def test_g_1_tally_on_nothing_counts_everything_as_no_answer_and_does_not_fall(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = FV.tally([201], os.path.join(tmp, u"co"), os.path.join(tmp, u"root"), None)
            c = rec[u"数"]
            self.assertEqual(1, c[u"正解が読めない社"])
            self.assertEqual(0, c[u"原:行の数"])
            self.assertEqual(sorted(FV.BOUNDS), sorted(rec[u"予測"]))
            self.assertIs(False, rec[u"予測"][u"UM4-M1"][u"当たり"])

    def test_g_2_broken_seat_outputs_do_not_crash_the_tally_and_become_no_answer_or_unreadable(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp).build()
            for k in (u"fill-a", u"fill-b"):
                wtext(os.path.join(w.seat(k), u"値の表.json"), u"{broken")
            for k in (u"check-orig", u"check-broken"):
                wtext(os.path.join(w.seat(k), u"根拠の表.json"), u"[" * 5000 + u"]" * 5000)
            wjson(os.path.join(w.seat(u"type"), u"材料_期1_A.json"), {u"材料": u"x"})
            rec = FV.tally([201], w.co, w.root, None)
            c = rec[u"数"]
            self.assertEqual(60, c[u"埋め:回a:普通:形が読めない"] + c[u"埋め:回b:普通:形が読めない"] + c[u"埋め:回a:無い:形が読めない"] + c[u"埋め:回b:無い:形が読めない"]
                             + c[u"埋め:回a:罠:形が読めない"] + c[u"埋め:回b:罠:形が読めない"] + c[u"埋め:回a:決め:決め:形が読めない"] + c[u"埋め:回b:決め:決め:形が読めない"])
            self.assertEqual(30, c[u"原:答えなし×答えなし"] + sum(v for k, v in c.items() if k.startswith(u"原:") and k.endswith(u"×答えなし") and k != u"原:答えなし×答えなし"))
            self.assertEqual(2, c[u"確かめ:orig:表:読めない"] + c[u"確かめ:broken:表:読めない"])
            self.assertEqual(1, c[u"型:束:断り"])

    def test_g_3_main_never_raises_for_odd_arguments(self):
        for args in ([], ["--tally"], ["--tally", "--co"], ["--process", "--transcripts"], ["--digest", "--root", "x"], ["--companies", "x", "--tally"],
                     ["--tally", "--co", "/nonexistent", "--root", "/nonexistent", "--companies", "a"], ["--material", "/nonexistent"], ["--through", "--root", "/n", "--company", "z"],
                     ["--status", "--co", "/n", "--root", "/n", "--company", "1", "--which", "orig"], ["--mutate", "--co", "/n", "--root", "/n", "--company", "1", "--changes-out", "/nonexistent/x/y.json"]):
            r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, SCRIPT_REL)] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertIn(r.returncode, (0, 1, 2, 4), args)
            self.assertNotIn(b"Traceback", r.stderr, args)

    def test_g_4_main_turns_any_exception_into_a_message_and_rc_one(self):
        orig = FV._main
        try:
            FV._main = lambda argv: 1 // 0
            buf = io.StringIO()
            old = sys.stderr
            sys.stderr = buf
            try:
                self.assertEqual(1, FV.main(["--tally"]))
            finally:
                sys.stderr = old
            self.assertIn(u"ZeroDivisionError", buf.getvalue())
            self.assertNotIn(u"Traceback", buf.getvalue())
        finally:
            FV._main = orig

    def test_g_5_odd_shapes_in_the_gold_the_forms_and_the_rows_do_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_company(os.path.join(tmp, u"co"))
            wjson(os.path.join(d, u"正解", u"正解.json"), {u"期1": {u"売上高_当期": 1.5, u"月次の売上高_当期": u"x"}})
            wjson(os.path.join(d, u"正解", u"罠.json"), {u"罠": [1, None, {u"項目": [], u"罠の値": u"x"}], u"決め": [{u"項目": u"短期借入金_当期末", u"読み": [1]}], u"無い": [5]})
            rec = FV.tally([201], os.path.join(tmp, u"co"), os.path.join(tmp, u"root"), None)
            self.assertGreater(rec[u"数"][u"正解が読めない行"], 0)
            self.assertNotEqual(u"OK", FV.material_report(d)[u"全部"])
        self.assertEqual((None, None, False), FV.answer_name(u"普通", FV.UNREADABLE, u"読めた", {}, None, None))
        self.assertEqual(u"形が読めない", FV.classify(5, u"読めた", {u"状態": u"在る", u"数値": 1.5}))
        self.assertEqual(u"形が読めない", FV.classify(5, u"読めた", {u"状態": u"在る", u"数値": True}))
        self.assertEqual(u"同じ", FV.classify(5, u"読めた", {u"状態": u"在る", u"数値": 5}))
        self.assertEqual(u"形が読めない", FV.classify(5, u"読めた", {u"状態": u"？"}))
        self.assertEqual(u"形が読めない", FV.classify(5, u"読めた", {u"状態": u"在る", u"数値": u"9" * 5000}))


# ======================================================================== 13. 変異で見つかった穴を縛る(作り物の標本)
def rows_sum_item(i=u"a01", value=u"9000"):
    return {u"id": i, u"状態": u"在る", u"数値": value, u"単位": u"円", u"期間": {u"始まり": u"2025-03-01", u"終わり": u"2026-02-28"}, u"範囲": u"全社",
            u"出どころ": {u"種類": u"表の行の和", u"file": u"j.csv", u"頭の行": 1, u"額": {u"列": u"借方", u"符号": u"そのまま"},
                      u"条件": [{u"列": u"科目", u"比べ方": u"等しい", u"値": u"売上"}, {u"列": u"日付", u"比べ方": u"以上", u"値": u"2025-03-01"},
                              {u"列": u"日付", u"比べ方": u"以下", u"値": u"2026-02-28"}], u"表示の倍率": 1}}


def bundle_with(item):
    b = type_bundle()
    b[u"材料"] = [item if x[u"id"] == item[u"id"] else x for x in b[u"材料"]]
    return b


class HoleTest(unittest.TestCase):
    def test_x_1_material_rules_see_a_missing_gold_key_a_column_past_the_row_and_a_path_that_climbs_out(self):
        def drop_key(d):
            set_gold(d, lambda g: g.pop(u"売上総利益_当期"))

        def col_out(d):
            set_traps(d, lambda o: o[u"罠"][0].__setitem__(u"列", 99))

        def climb(d):
            wtext(os.path.join(d, u"t.csv"), T_CSV)                      # 期1/ の外(社の folder の直下)に同じ file
            set_traps(d, lambda o: o[u"罠"][0].__setitem__(u"file", u"../t.csv"))
        self.assertEqual(u"NG", mat_rules_with(drop_key)[u"無いの項目だけ正解が null"])
        ng = lambda got: sorted(k for k, v in got.items() if v == u"NG")
        self.assertEqual([u"罠の値が書かれた升に在る"], ng(mat_rules_with(col_out)))            # 後ろの規則まで巻き添えで NG にならない
        self.assertEqual([u"罠の値が書かれた升に在る"], ng(mat_rules_with(climb)))

    def test_x_2_a_table_row_with_a_broken_state_is_no_answer_even_when_the_view_fits_the_other_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_company(os.path.join(tmp, u"co"))
            chk = FV.load_check_module()
            src = chk.Source(os.path.join(d, u"期1"))
            self.assertEqual(FV.S_NA, FV.judge_status({u"id": u"a03", u"状態": u"？", u"数値": None}, crow(u"a03", u"無いで合う"), chk, src))
            self.assertEqual(FV.S_NA, FV.judge_status({u"id": u"a03", u"状態": u"？", u"数値": None}, crow(u"a03", u"決めが要る"), chk, src))

    def test_x_3_the_answer_names_for_trap_and_decide_rows_follow_the_values(self):
        an = FV.answer_name
        row = lambda st, n=None: {u"状態": st, u"数値": n}
        self.assertEqual((u"違う", 110000, True), an(u"罠", 100000, u"読めた", row(u"在る", u"110000"), 110000, None))
        self.assertEqual((u"違う", 90000, False), an(u"罠", 100000, u"読めた", row(u"在る", u"90000"), 110000, None))       # 罠の値でない違う数は罠を取っていない
        self.assertEqual((u"同じ", 100000, False), an(u"罠", 100000, u"読めた", row(u"在る", u"100000"), 110000, None))
        self.assertEqual((u"違う", 110000, False), an(u"普通", 100000, u"読めた", row(u"在る", u"110000"), None, None))        # 罠の行でなければ数えない
        d = lambda r, t=u"読めた": an(u"決め", 3000, t, r, None, (3000, 7000))
        self.assertEqual((u"決め:1つ目", 3000, False), d(row(u"在る", u"3000")))
        self.assertEqual((u"決め:2つ目", 7000, False), d(row(u"在る", u"7000")))
        self.assertEqual((u"決め:どちらでもない", 5, False), d(row(u"在る", u"5")))
        self.assertEqual((u"決め:分からない", None, False), d(row(u"分からない")))
        self.assertEqual((u"決め:無い", None, False), d(row(u"無い")))
        self.assertEqual((u"決め:答えなし", None, False), d(None))
        self.assertEqual((u"決め:答えなし", None, False), d(None, u"無し"))
        self.assertEqual((u"決め:形が読めない", None, False), d(None, u"読めない"))
        self.assertEqual((u"決め:形が読めない", None, False), d(row(u"在る", u"abc")))
        self.assertEqual((u"決め:形が読めない", None, False), d(row(u"？")))
        self.assertEqual((u"決め:1つ目", 3000, False), an(u"決め", 3000, u"読めた", row(u"在る", u"3000"), None, None))              # 読みが読めない時は正解を 1 つ目とみなす
        self.assertEqual((u"決め:どちらでもない", 7000, False), an(u"決め", 3000, u"読めた", row(u"在る", u"7000"), None, None))

    def test_x_4_the_kind_of_a_row_puts_decide_before_trap_before_none_and_a_decide_is_never_a_same_or_a_wrong(self):
        forms = {u"無い": [u"a02"], u"罠": {u"a01": 5, u"a12": 6}, u"決め": {u"a12": (1, 2)}}
        gold = gold_map()
        kinds = FV.row_kinds(gold, forms)
        self.assertEqual((u"罠", u"決め", u"無い", u"普通"), (kinds[u"a01"], kinds[u"a12"], kinds[u"a02"], kinds[u"a03"]))
        self.assertEqual(u"無い", FV.row_kinds(gold, None)[u"a05"])
        self.assertEqual({u"止めすぎ": 1}, dict(FV.metric_counts([(u"同じ", u"普通", False)])))
        self.assertEqual({u"決めを通した": 1}, dict(FV.metric_counts([(u"同じ", u"決め", True), (u"無いで同じ", u"決め", False)])))             # 決めの行は 取得・止めすぎ に入れない
        self.assertEqual({u"決めを通した": 1}, dict(FV.metric_counts([(u"決め:1つ目", u"決め", True), (u"決め:2つ目", u"決め", False)])))
        self.assertEqual({u"通した誤り": 1, u"通さなかった誤り": 2}, dict(FV.metric_counts([(u"違う", u"罠", True), (u"無いのに在る", u"無い", False), (u"無いで違う", u"普通", False)])))

    def test_x_5_a_decide_row_counts_as_a_confident_number_only_when_the_confidence_is_high(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = [dict(r, 自信=u"中") if r[u"id"] == u"a12" else r for r in alpha_rows()]
            w = TB(tmp).build(alpha=rows)
            c = FV.tally([201], w.co, w.root, None)[u"数"]
            self.assertEqual((1, 2), (c[u"埋め:回a:決め:自信高で数を出した"], c[u"埋め:回b:決め:自信高で数を出した"]))

    def test_x_6_a_broken_row_that_equals_the_gold_is_counted_as_made_and_dropped_not_as_a_broken_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            g = dict(GOLD)
            g[u"a03"] = 31000                                      # 桁の変え方(30000 → 31000)が正解と同じになる
            w = TB(tmp, gold=g).build()
            c = FV.tally([201], w.co, w.root, None)[u"数"]
            self.assertEqual((1, 1, 0, 0), (c[u"壊:桁:作った"], c[u"壊:桁:外した"], c[u"壊:桁:行の数"], c[u"壊:桁:通さなかった"] + c[u"壊:桁:通した"]))
            self.assertEqual(24, c[u"壊:壊していない行"])
            self.assertEqual(0, c[u"壊:作れなかった数"])

    def test_x_7_without_the_alpha_table_no_broken_row_is_made_in_the_tally_either(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp).build(skip_alpha=True)
            c = FV.tally([201], w.co, w.root, None)[u"数"]
            self.assertEqual(6, c[u"壊:作れなかった数"])
            self.assertEqual(0, sum(c[u"壊:%s:作った" % k] for k in FV.MUT_KINDS))
            self.assertEqual(1, c[u"埋め:回a:表:無し"])
            self.assertEqual((0, 0), (c[u"確かめ:orig:表:読めた"], c[u"確かめ:broken:表:読めた"]))

    def test_x_8_the_type_seat_takes_a_trap_value_and_an_unmarked_rows_sum_as_decided(self):
        with tempfile.TemporaryDirectory() as tmp:
            trap_item = {u"id": u"a07", u"状態": u"在る", u"数値": u"13000", u"単位": u"円", u"期間": {u"始まり": u"2025-03-01", u"終わり": u"2026-02-28"}, u"範囲": u"全社",
                         u"出どころ": src_cell(u"t.csv", 4, 2)}
            w = TB(tmp).build(bundle=bundle_with(trap_item))
            c = FV.tally([201], w.co, w.root, None)[u"数"]
            self.assertEqual(1, sum(v for k, v in c.items() if k.startswith(u"型:罠を取った×")))
            self.assertEqual(1, c[u"型:違う×止める"])
        with tempfile.TemporaryDirectory() as tmp:
            w = TB(tmp).build(bundle=bundle_with(rows_sum_item()))
            c = FV.tally([201], w.co, w.root, None)[u"数"]
            self.assertEqual({u"止める": 1, u"通す(取り方は未確認)": 1, u"無いを受ける": 28, u"通す": 0}, dict((j, c[u"型:判定:" + j]) for j in (u"止める", u"通す(取り方は未確認)", u"無いを受ける", u"通す")))
            self.assertEqual(28, c[u"型:通した"])
            self.assertEqual(1, c[u"型:違う×通す(取り方は未確認)"])
            self.assertEqual((23, 1), (c[u"並べる:型+検査:通した誤り"], c[u"並べる:型+検査:通さなかった誤り"]))

    def test_x_10_the_two_rounds_are_added_and_the_base_is_only_the_kind_the_seal_names(self):
        self.assertIs(True, FV.judge(rec_of(埋め__回a__無い__無いのに在る=1, 埋め__回b__無い__無いのに在る=1, 埋め__回a__無い__行の数=12, 埋め__回b__無い__行の数=12))[u"UM4-F3"][u"当たり"])
        self.assertIs(False, FV.judge(rec_of(埋め__回a__無い__無いのに在る=1, 埋め__回b__無い__無いのに在る=0, 埋め__回a__無い__行の数=12, 埋め__回b__無い__行の数=12))[u"UM4-F3"][u"当たり"])
        self.assertIs(True, FV.judge(rec_of(埋め__回a__罠を取った=0, 埋め__回b__罠を取った=2, 埋め__回a__罠__行の数=16, 埋め__回b__罠__行の数=16))[u"UM4-F2"][u"当たり"])
        base = dict(埋め__回a__普通__同じ=160, 埋め__回a__普通__行の数=168, 埋め__回a__罠__行の数=16, 埋め__回a__無い__行の数=12, 埋め__回a__決め__行の数=8)
        self.assertIs(True, FV.judge(rec_of(**base))[u"UM4-F1"][u"当たり"])                  # 罠・無い・決めの行は分母に入れない
        self.assertEqual({u"同じ": 160, u"普通の行": 168}, dict((k, v) for k, v in FV.judge(rec_of(**base))[u"UM4-F1"].items() if k != u"当たり"))

    def test_x_9_the_percent_boundaries_flip_exactly_at_equal(self):
        self.assertIs(True, FV.judge(rec_of(埋め__回a__普通__同じ=19, 埋め__回a__普通__行の数=20))[u"UM4-F1"][u"当たり"])
        self.assertIs(False, FV.judge(rec_of(埋め__回a__普通__同じ=18, 埋め__回a__普通__行の数=20))[u"UM4-F1"][u"当たり"])
        self.assertIs(True, FV.judge(rec_of(並べる__埋め_P_確かめ__取得=17, 原__同じの行=20))[u"UM4-V2"][u"当たり"])
        self.assertIs(False, FV.judge(rec_of(並べる__埋め_P_確かめ__取得=16, 原__同じの行=20))[u"UM4-V2"][u"当たり"])
        self.assertIs(True, FV.judge(rec_of(壊__罠の値__状態__不一致=5, 壊__罠の値__直せた=4))[u"UM4-V8"][u"当たり"])
        self.assertIs(False, FV.judge(rec_of(壊__罠の値__状態__不一致=5, 壊__罠の値__直せた=3))[u"UM4-V8"][u"当たり"])
        self.assertIs(True, FV.judge(rec_of(埋め__回a__決め__自信高で数を出した=8, 埋め__回a__決め__行の数=16))[u"UM4-F4"][u"当たり"])
        self.assertIs(True, FV.judge(rec_of(埋め__揺れ__回αが違った行=4, 埋め__揺れ__回αが違った行のうち回βも同じ答え=2))[u"UM4-F5"][u"当たり"])


class FixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.w = TB(cls.tmp).build()
        cls.tdir = os.path.join(cls.tmp, u"tr")
        for cid in (201, 202):
            if cid == 202:
                shutil.copytree(os.path.join(cls.w.co, u"201"), os.path.join(cls.w.co, u"202"))
                shutil.copytree(os.path.join(cls.w.root, u"201"), os.path.join(cls.w.root, u"202"))
            for k, (folder, calls) in seat_calls(cls.w.root, None, cid).items():
                write_transcript(cls.tdir, u"%s_%s" % (cid, k), folder, calls)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_y_1_two_companies_are_tallied_processed_and_digested_company_by_company(self):
        w = self.w
        out = os.path.join(self.tmp, u"r2.json")
        rc, _o, err = run_cli(["--tally", "--co", w.co, "--root", w.root, "--transcripts", self.tdir, "--companies", "201", "202", "--out", out])
        self.assertEqual(0, rc, err)
        rec = json.loads(read_text(out))
        c = rec[u"数"]
        self.assertEqual((2, 0), (rec[u"会社の数"], rec[u"外した社の数"]))
        self.assertEqual((2, 42, 6, 20), (c[u"素材:社の数"], c[u"埋め:回a:普通:行の数"], c[u"過程:数えた席"], c[u"読んだ file の数"]))
        self.assertEqual([u"201", u"202"], sorted(rec[u"会社ごと"]))
        self.assertEqual(10, len(rec[u"席ごと"]))
        for cid in (u"201", u"202"):
            self.assertEqual(21, rec[u"会社ごと"][cid][u"埋め:回a:普通:行の数"])
            self.assertEqual(1, rec[u"会社ごと"][cid][u"P1:型:数えた"])
        self.assertEqual([], record_problems(rec, companies=(201, 202)))
        rc, text, err = run_cli(["--process", "--transcripts", self.tdir, "--root", w.root, "--companies", "201", "202"])
        self.assertEqual(0, rc, err)
        res = json.loads(text)
        self.assertEqual(10, len(res))
        self.assertEqual(6, sum(1 for v in res.values() if v[u"状態"] == u"数えた"))
        self.assertEqual(2, sum(1 for k, v in res.items() if v[u"状態"] == u"数えた" and k.endswith(u"/202/type")) + sum(1 for k, v in res.items() if v[u"状態"] == u"数えた" and k.endswith(u"/201/type")))
        dg = os.path.join(self.tmp, u"dg2")
        rc, text, err = run_cli(["--digest", "--co", w.co, "--root", w.root, "--transcripts", self.tdir, "--out-dir", dg, "--companies", "201", "202"])
        self.assertEqual(0, rc, err)
        self.assertEqual({u"書いた数": 8, u"書かなかった数": 4}, json.loads(text))
        self.assertEqual(sorted([u"201_型.md", u"201_埋めa.md", u"201_確かめ原.md", u"202_型.md", u"202_埋めa.md", u"202_確かめ原.md", u"行の読み_201.md", u"行の読み_202.md"]), sorted(os.listdir(dg)))
        self.assertIn(u"社 202", read_text(os.path.join(dg, u"行の読み_202.md")))

    def test_y_2_an_excluded_company_is_in_no_denominator_and_only_its_count_is_kept(self):
        w = self.w
        out = os.path.join(self.tmp, u"r3.json")
        rc, _o, err = run_cli(["--tally", "--co", w.co, "--root", w.root, "--transcripts", self.tdir, "--companies", "201", "202", "--exclude", "202", "--out", out])
        self.assertEqual(0, rc, err)
        rec = json.loads(read_text(out))
        c = rec[u"数"]
        self.assertEqual((1, 1), (rec[u"会社の数"], rec[u"外した社の数"]))
        self.assertEqual((1, 21, 3, 10, 5), (c[u"素材:社の数"], c[u"埋め:回a:普通:行の数"], c[u"過程:数えた席"], c[u"読んだ file の数"], c[u"過程:席の数"]))
        self.assertEqual([u"201"], sorted(rec[u"会社ごと"]))
        self.assertEqual(5, len(rec[u"席ごと"]))
        self.assertNotIn(u"202", json.dumps(rec, ensure_ascii=False))
        self.assertEqual([], record_problems(rec, companies=(201, 202)))
        self.assertNotEqual([], record_problems(rec, companies=(201,)))         # 外した 1 + 数えた 1 は社の数 1 と合わない
        rec2 = FV.tally([201], w.co, w.root, self.tdir, excluded=1)
        self.assertEqual(1, rec2[u"外した社の数"])
        self.assertEqual(0, FV.tally([201], w.co, w.root, self.tdir)[u"外した社の数"])

    def test_y_3_the_material_check_hides_the_folder_and_names_the_rule_that_a_wrong_count_or_a_symlink_breaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_company(os.path.join(tmp, u"秘密の社"))
            rc, out, _e = run_cli(["--material", d])
            self.assertEqual(0, rc)
            for leak in (d, u"秘密の社", os.path.basename(tmp), u"/"):
                self.assertNotIn(leak, out, leak)
            rc, out, _e = run_cli(["--material", os.path.join(tmp, u"無い社")])
            self.assertEqual(0, rc)
            self.assertNotIn(u"無い社", out)
        ng = lambda got: sorted(k for k, v in got.items() if v == u"NG")

        def traps5(d):
            set_traps(d, lambda o: o[u"罠"].append(dict(o[u"罠"][0], 項目=u"流動資産合計_当期末")))

        def nones4(d):
            set_traps(d, lambda o: o[u"無い"].append(u"純資産合計_前期末"))

        def decide1(d):
            set_traps(d, lambda o: o[u"決め"].pop())

        def none_nonnull(d):
            set_gold(d, lambda g: g.__setitem__(u"売上高_前期", 5))

        def link(d):
            real = os.path.join(os.path.dirname(d), u"real.csv")
            wtext(real, T_CSV)
            os.remove(os.path.join(d, u"期1", u"t.csv"))
            os.symlink(real, os.path.join(d, u"期1", u"t.csv"))
        self.assertEqual(sorted([u"罠が 4 つ", u"9 項目が別", u"9 項目が 18 個の中", u"罠の値が正解と違う整数", u"罠の値が書かれた升に在る"]), ng(mat_rules_with(traps5)))
        self.assertEqual(sorted([u"無いが 3 つ", u"9 項目が別", u"9 項目が 18 個の中", u"無いの項目だけ正解が null"]), ng(mat_rules_with(nones4)))
        self.assertEqual(sorted([u"決めが 2 つ", u"9 項目が別", u"9 項目が 18 個の中", u"決めの 2 つの値が違う"]), ng(mat_rules_with(decide1)))
        self.assertEqual([u"無いの項目だけ正解が null"], ng(mat_rules_with(none_nonnull)))
        self.assertEqual([u"罠の値が書かれた升に在る"], ng(mat_rules_with(link)))

    def test_y_4_the_has_none_row_is_the_first_none_row_whose_alpha_state_is_not_present_even_if_the_number_is_not_an_integer(self):
        rows = table_dict(alpha_rows())
        rows[u"a05"] = vrow(u"a05", u"在る", u"abc")                      # 在る と書いたが整数の字でない行は選ばない
        ch, nm = FV.make_broken(rows, gold_map(), forms_of())
        self.assertEqual([], [x for x in ch if x[u"種類"] == u"無いのに在る"])
        self.assertEqual(1, nm[u"無いのに在る"])
        rows[u"a30"] = vrow(u"a30", u"分からない")
        self.assertEqual([u"a30"], [x[u"id"] for x in FV.make_broken(rows, gold_map(), forms_of())[0] if x[u"種類"] == u"無いのに在る"])
        rows = table_dict(alpha_rows())
        rows[u"a05"] = vrow(u"a05", u"分からない")
        self.assertEqual([u"a05"], [x[u"id"] for x in FV.make_broken(rows, gold_map(), forms_of())[0] if x[u"種類"] == u"無いのに在る"])


if __name__ == "__main__":
    unittest.main()
