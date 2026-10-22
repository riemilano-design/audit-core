# -*- coding: utf-8 -*-
u"""封(docs/PACKAGING_SEAL_2026-10-20.md)の予測 G-1〜G-6 を門にする。

**0 USD。通信しない。** venv を作る試験(G-1〜G-3)は重い(pip install / pip wheel)ので、
環境変数 ``AUDIT_CORE_PACKAGING=1`` のときだけ走る(既定の `pytest` を遅くしない)。
G-4(pyproject の構造)・G-5(覆いの検査)・G-6(README の数・禁止語)は常に走る。

venv はこの試験自身が作る一時ディレクトリに作り、使い終わったら消す
(リポジトリの木には何も残さない)。``pip`` には必ず ``--no-build-isolation``
と ``--no-index`` を渡す(PyPI には触れない。setuptools・wheel はこの機械の
``--system-site-packages`` から継承する)。
"""
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
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PYPROJECT = os.path.join(ROOT, "pyproject.toml")
SETUP_CFG = os.path.join(ROOT, "setup.cfg")
SETUP_PY = os.path.join(ROOT, "setup.py")
README = os.path.join(ROOT, "README.en.md")
FROZEN_SRC = os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py")
SUITE_COV_SRC = os.path.join(ROOT, "measure", "suite_coverage_2026-10-16.py")
SUITE_COV_OUT = os.path.join(ROOT, "fixtures", "suite_coverage_2026-10-16.json")
PACKAGING_REC = os.path.join(ROOT, "fixtures", "packaging_2026-10-20.json")
MUTATIONS = os.path.join(ROOT, "tests", "adapters", "xbrl", "mutations.json")
CORE_DIR = os.path.join(ROOT, "core", "py", "audit_core")

RUN_HEAVY = os.environ.get("AUDIT_CORE_PACKAGING") == "1"
HEAVY_SKIP_REASON = (u"AUDIT_CORE_PACKAGING=1 のときだけ走る"
                     u"(venv の作成・pip install・pip wheel ― 0 USD だが重い)")

FORBIDDEN_WORDS = ("accurate", "world's first", "only", "unique", "guarantee")


def readme_bullets(t):
    u"""README.en.md の `- ` bullet を 1 項目ごとに切り出す(折り返し(ソフトラップ)
    を飛び越えて、1 bullet をひと続きの字として扱う)。独立監査 REVISE
    (2026-10-20、2 回目)で「数とその領域の字の組」を縛るために使う。
    """
    blocks = re.split(r"\n(?=- )", t)
    return [b for b in blocks if b.startswith("- ")]


def readme_paragraphs(t):
    u"""空行で区切った段落。"""
    return t.split("\n\n")


def norm_ws(s):
    u"""ソフトラップ(折り返しの改行+字下げの空白)を単一の空白に畳む。
    markdown は折り返しを 1 つの続いた文として描画するので、複数語の句を
    探すときは畳んだ上で比べる。
    """
    return " ".join(s.split())


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def load_json(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def load_module(src, name):
    sp = importlib.util.spec_from_file_location(name, src)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def clean_egg_info():
    u"""`pip install -e .`・`pip install .`・`pip wheel .` を ``cwd=ROOT`` で
    呼ぶと、setuptools が ``audit_core.egg-info/`` を**ソース木の中**に書く
    (venv の外。インストール先がどこであっても起きる副作用)。試験が
    リポジトリの木に何も残さないよう、毎回その場で消す(封の触ってよい
    file には入っていない ― 生成物であって成果物ではない)。
    """
    for name in os.listdir(ROOT):
        if name.endswith(".egg-info"):
            shutil.rmtree(os.path.join(ROOT, name), ignore_errors=True)


# ---------------------------------------------------------------------------
# G-4: pyproject.toml を置いても pytest の収集が変わらない(構造で保証する)。
# ---------------------------------------------------------------------------

class PyprojectStructureTest(unittest.TestCase):
    u"""G-4 の理由(封: 「pytest の設定を書かないので rootdir も変わらない」)を
    構造で固定する。**これが崩れたら G-4 の前提が崩れている。**
    """

    def test_g4_pyproject_has_only_build_system(self):
        t = text(PYPROJECT)
        tables = re.findall(r"(?m)^\[([^\]]+)\]", t)
        self.assertEqual(tables, ["build-system"],
                         u"pyproject.toml に [build-system] 以外の表が在る"
                         u"(pytest の設定を書くと rootdir が変わりうる)")
        self.assertIn('requires = ["setuptools", "wheel"]', t)
        self.assertIn('build-backend = "setuptools.build_meta"', t)

    def test_g4_setup_cfg_does_not_configure_pytest(self):
        t = text(SETUP_CFG)
        self.assertNotIn("[tool:pytest]", t)
        self.assertNotIn("[pytest]", t)

    def test_g4_setup_py_is_a_two_line_shim(self):
        t = text(SETUP_PY)
        self.assertIn("from setuptools import setup", t)
        self.assertIn("setup()", t)
        # PEP 621 の [project] 表は使えない(setuptools 58 < 61)ので
        # setup.cfg に metadata が無ければ無効
        self.assertNotIn("name=", t)
        self.assertNotIn("packages=", t)

    def test_g4_live_collection_count_is_at_least_the_pinned_before_count(self):
        u"""**生きている門。**pyproject を置く前の収集本数(3363。この封の
        実装直前に repo-root から測った一度限りの実測で、
        ``fixtures/packaging_2026-10-20.json`` の G-4 に残す)を下回らないこと。

        pyproject を置いた直後(試験 file を 1 本も足す前)に測り直しても
        3363 のままだったことは実装記録に書く。ここでは、後から試験 file を
        足した分だけ本数が**増える方向**にしか動かないことを縛る
        (pyproject 自体が収集を**減らす**方向に壊れたら、ここが赤くなる)。
        """
        r = run([sys.executable, "-B", "-m", "pytest", "--collect-only", "-q",
                "-p", "no:cacheprovider"], cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:])
        m = re.search(r"(\d+) tests? collected", r.stdout)
        self.assertIsNotNone(m, r.stdout[-500:])
        self.assertGreaterEqual(int(m.group(1)), 3363)


# ---------------------------------------------------------------------------
# G-1・G-2: venv に editable install → import・console script --help。
# ---------------------------------------------------------------------------

@unittest.skipUnless(RUN_HEAVY, HEAVY_SKIP_REASON)
class EditableInstallTest(unittest.TestCase):
    u"""G-1・G-2。**この機械の setuptools 58.0.4 は PEP 660 が無く、
    `setup.py develop` の egg-link は repo の根だけを sys.path に足す。**
    package_dir で `core/py/audit_core` に写した `audit_core` は、
    `adapters` を先に import していない限り、その sys.path 追加だけでは
    解決できない(`adapters/__init__.py` 自身が `core/py` を
    `sys.path` に足す既存の仕組みを持つが、それは `audit_core` を先に書いた
    `import audit_core, adapters.xbrl.verify_external` の時点ではまだ効いていない)。
    **この試験は外れ方をそのまま再現し、固定する。**
    """

    @classmethod
    def setUpClass(cls):
        cls.venv = tempfile.mkdtemp(prefix="audit_core_pkg_editable_")
        r = run([sys.executable, "-m", "venv", "--system-site-packages", cls.venv])
        if r.returncode != 0:
            raise RuntimeError(r.stdout + r.stderr)
        cls.py = os.path.join(cls.venv, "bin", "python3")

    @classmethod
    def tearDownClass(cls):
        u"""editable install の間、`audit_core.egg-info/`(easy-install.pth・
        egg-link が指す本体)は venv の中からも使われている
        (`test_g2_console_scripts_help` が entry_points.txt を読む)。
        **クラスの全試験が終わってから**まとめて消す(試験ごとに消すと
        次の試験が `PackageNotFoundError` になる)。
        """
        shutil.rmtree(cls.venv, ignore_errors=True)
        clean_egg_info()

    def test_g1_editable_install_succeeds(self):
        r = run([self.py, "-m", "pip", "install", "-e", ".",
                "--no-build-isolation", "--no-index"], cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])

    def test_g1_combined_import_from_outside_cwd_fails_on_this_toolchain(self):
        u"""**外れをそのまま再現する。**rc=0 ではなく、
        `ModuleNotFoundError: audit_core` を期待する(封は書き換えない)。
        """
        r = run([self.py, "-m", "pip", "install", "-e", ".",
                "--no-build-isolation", "--no-index"], cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:])
        outside = tempfile.mkdtemp(prefix="audit_core_pkg_outside_")
        try:
            r2 = run([self.py, "-c",
                     "import audit_core, adapters.xbrl.verify_external"],
                    cwd=outside)
            self.assertNotEqual(r2.returncode, 0,
                                u"**editable で combined import が通った"
                                u"(機械の setuptools が変わった可能性。"
                                u"封 G-1 を測り直すこと)**")
            self.assertIn("ModuleNotFoundError", r2.stderr)
            self.assertIn("audit_core", r2.stderr)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_g2_console_scripts_help(self):
        for name in ("audit-core-verify-document", "audit-core-verify-external"):
            exe = os.path.join(self.venv, "bin", name)
            r = run([exe, "--help"])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("usage:", r.stdout)


@unittest.skipUnless(RUN_HEAVY, HEAVY_SKIP_REASON)
class NonEditableInstallTest(unittest.TestCase):
    u"""封 G-1 の注意に従い、**判定の対象ではない**追加の実測
    (非 editable。`pip install . --no-build-isolation`)を別に置く。
    """

    def tearDown(self):
        clean_egg_info()

    def test_g1_non_editable_install_and_import_succeed(self):
        venv = tempfile.mkdtemp(prefix="audit_core_pkg_noneditable_")
        try:
            r = run([sys.executable, "-m", "venv", "--system-site-packages", venv])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            py = os.path.join(venv, "bin", "python3")
            r1 = run([py, "-m", "pip", "install", ".",
                     "--no-build-isolation", "--no-index"], cwd=ROOT)
            self.assertEqual(r1.returncode, 0, r1.stdout[-2000:])
            outside = tempfile.mkdtemp(prefix="audit_core_pkg_outside_ne_")
            try:
                r2 = run([py, "-c",
                         "import audit_core, adapters.xbrl.verify_external"],
                        cwd=outside)
                self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
            finally:
                shutil.rmtree(outside, ignore_errors=True)
        finally:
            shutil.rmtree(venv, ignore_errors=True)


@unittest.skipUnless(RUN_HEAVY, HEAVY_SKIP_REASON)
class WheelTest(unittest.TestCase):
    u"""G-3。``pip wheel`` で 1 本の wheel ができ、中の ``.py`` が保護面の
    36 本(``fixtures/frozen_bundle_sha.py`` の ``FROZEN_COUNT``)に一致すること。
    ``.py`` 以外は metadata(``*.dist-info/*``)だけであること。
    """

    def tearDown(self):
        clean_egg_info()

    def test_g3_wheel_py_count_matches_frozen_bundle(self):
        out = tempfile.mkdtemp(prefix="audit_core_pkg_wheel_")
        try:
            r = run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps",
                    "--no-build-isolation", "--no-index", "-w", out], cwd=ROOT)
            self.assertEqual(r.returncode, 0, r.stdout[-2000:])
            whls = [f for f in os.listdir(out) if f.endswith(".whl")]
            self.assertEqual(len(whls), 1, whls)
            path = os.path.join(out, whls[0])
            with zipfile.ZipFile(path) as z:
                names = z.namelist()
            py = [n for n in names if n.endswith(".py")]
            other = [n for n in names if not n.endswith(".py")]
            frozen = load_module(FROZEN_SRC, "frozen_bundle_sha_pkg_t")
            self.assertEqual(len(py), frozen.FROZEN_COUNT, sorted(py))
            for n in other:
                self.assertIn(".dist-info/", n, u"metadata 以外の非 .py file: %s" % n)
        finally:
            shutil.rmtree(out, ignore_errors=True)


# ---------------------------------------------------------------------------
# G-5: 覆いの検査(試験 file +2・漏れは既存の 1 本のまま)。
# ---------------------------------------------------------------------------

class SuiteCoverageTest(unittest.TestCase):
    def test_g5_the_two_new_test_files_are_on_disk_and_counted(self):
        m = load_module(SUITE_COV_SRC, "suite_cov_pkg_t")
        files = set(m.test_files())
        self.assertIn("tests/measure/test_packaging.py", files)
        self.assertIn("tests/measure/test_packaging_result.py", files)

    def test_g5_the_written_record_reflects_plus_two_and_the_one_known_gap(self):
        """**packaging 記録(測った時点の before/after)に縛る。**

        生きた覆いの記録(`fixtures/suite_coverage_2026-10-16.json`)には
        縛らない ― その記録は後続の封(QWED 段 B など)で本数が進むため、
        この封(G-5)が固定すべきは「2026-10-20 に測った +2・漏れ 1 本」という
        **その時点の差分**であり、いまの生きた本数ではない
        (司令塔の決定 2026-10-20。memory
        「字で留めた本数は足した人が直さないと黙って古くなる」の型を避ける)。
        """
        g5 = load_json(PACKAGING_REC)["G-5"]
        self.assertEqual(g5["test_files_on_disk_before"], 176)
        self.assertEqual(g5["test_files_on_disk_after"], 178)
        self.assertEqual(g5["tests_measure_before"], 118)
        self.assertEqual(g5["tests_measure_after"], 120)
        self.assertEqual(g5["uncovered_files_after"], [])
        self.assertEqual(g5["missed_discover_before"],
                         ["measure/tests/test_inject.py"])
        self.assertEqual(g5["missed_discover_after"],
                         ["measure/tests/test_inject.py"])
        self.assertTrue(g5["hit"])


# ---------------------------------------------------------------------------
# G-6: README.en.md の数と禁止語。
# ---------------------------------------------------------------------------

class ReadmeTest(unittest.TestCase):
    def setUp(self):
        self.t = text(README)

    def test_g6_is_english(self):
        # ひらがな・カタカナ・漢字が無いこと(雑な判定だが「英語 1 枚」を縛る)
        self.assertNotRegex(self.t, r"[぀-ヿ一-鿿]")

    def test_g6_forbidden_words_absent(self):
        low = self.t.lower()
        for w in FORBIDDEN_WORDS:
            self.assertNotIn(w, low, u"禁止語が在る: %s" % w)

    def test_g6_losses_are_stated_first(self):
        u"""**負けの数を先頭に置く。**LLM 24/24・Core 12/24 が、他の数より前。"""
        idx_loss = self.t.index("12/24")
        idx_llm = self.t.index("24/24")
        self.assertLess(idx_llm, idx_loss + 200)
        for other in ("18/18", "192/192", "0/50", "8/8", "1/49"):
            self.assertGreater(self.t.index(other), idx_loss, other)

    def test_g6_sheet_connection_numbers_match_the_record(self):
        rec = load_json(os.path.join(ROOT, "fixtures", "sheet",
                                     "poc_ab_score_2026-10-17.json"))
        arms = rec["arms"]
        llm = arms[u"A1 一般 LLM(sonnet)"][u"正解集合"]
        core = arms[u"B Audit Core"][u"正解集合"]
        llm_total = sum(llm.values())
        core_total = sum(core.values())
        self.assertIn("%d/%d" % (llm[u"正しい接続"], llm_total), self.t)
        self.assertIn("%d/%d" % (core[u"正しい接続"], core_total), self.t)
        self.assertEqual(core[u"誤接続"], 0)
        self.assertIn(str(core[u"保留"]), self.t)

    def test_g6_attribute_injection_numbers_match_the_record(self):
        rec = load_json(os.path.join(ROOT, "fixtures", "xbrl", "cd8",
                                     "attr_inject_2026-10-17.json"))
        p1 = rec[u"**第 1 部 注入**"]
        for k in (u"単位", u"期間(注入)", u"次元"):
            c = p1[k][u"**誤って通した**"]
            self.assertIn("%d/%d" % (c[u"分子"], c[u"分母"]), self.t)

    def test_g6_holds_product_path_numbers_match_the_record(self):
        rec = load_json(os.path.join(ROOT, "fixtures", "xbrl", "cd8",
                                     "holds_product_path_2026-10-19.json"))
        f6 = rec[u"**実測**"]["F-6"]
        for k in (u"期間(注入)", u"単位", u"次元"):
            c = f6[k]
            self.assertIn("%d/%d" % (c[u"作れた"], c[u"**保留**"]), self.t)
        f4 = rec[u"**実測**"]["F-4"]
        self.assertIn("%d/%d" % (f4[u"**一致**"], f4[u"行"]), self.t)

    def test_g6_correct_reference_hold_rate_matches_the_record(self):
        rec = load_json(os.path.join(ROOT, "fixtures", "xbrl", "cd8",
                                     "period_unit_hold_2026-10-19.json"))
        p2 = rec[u"**第 2 部 露出の帯(状態は変えない)**"]
        c = p2[u"D4 正解(T5)の参照先 50 件/P"]
        self.assertIn("%d/%d" % (c[u"分子"], c[u"分母"]), self.t)

    def test_g6_error_detection_numbers_match_the_record(self):
        rec = load_json(os.path.join(ROOT, "fixtures", "sheet",
                                     "errdet_cprime_2026-10-19.json"))
        seat1 = rec[u"方式ごとの内訳"]["seat1"]
        a = seat1["A"][u"検出"]
        cprime = seat1[u"C′"][u"検出"]
        old_missed = rec[u"旧 C(2026-10-17)との突き合わせ"]["seat1"][u"旧 C の見落とし"]
        total = len(a)
        self.assertIn("%d/%d" % (len(a), total), self.t)
        self.assertIn("%d/%d" % (total - len(old_missed), total), self.t)
        self.assertIn("%d/%d" % (len(cprime), total), self.t)
        overwrite = rec[u"**判定(封 §3 の K-1〜K-4)**"]["seat1"]["K-2 上書き 0"][u"件数"]
        self.assertEqual(overwrite, 0)

    def test_g6_kokkai_false_pass_matches_the_record(self):
        rec = load_json(os.path.join(ROOT, "fixtures", "kokkai",
                                     "false_pass_round12_2026-10-15.json"))
        self.assertIn("%d/%d" % (rec["passed"], rec["n"]), self.t)

    def test_g6_test_suite_numbers_match_the_record(self):
        rec = load_json(SUITE_COV_OUT)
        self.assertIn(str(rec["test_files_on_disk"]), self.t)
        # 2026-10-20: 収集本数は試験を 1 本足すたびに変わるので README には書かない(記録にだけ在る)
        self.assertNotIn("collected test cases", self.t)

    def test_g6_mutation_count_matches_the_record(self):
        rows = load_json(MUTATIONS)
        self.assertIn(str(len(rows)), self.t)

    def test_g6_core_line_count_matches_the_record(self):
        total = 0
        for fn in sorted(os.listdir(CORE_DIR)):
            if fn.endswith(".py"):
                with io.open(os.path.join(CORE_DIR, fn), encoding="utf-8") as fh:
                    total += sum(1 for _ in fh)
        self.assertIn(str(total), self.t)

    def test_g6_license_is_proprietary(self):
        self.assertIn("Proprietary", self.t)
        self.assertIn("Yushi Yamanaka", self.t)

    def test_g6_states_it_is_an_excerpt_of_the_japanese_primary_source(self):
        self.assertIn("excerpt", self.t.lower())


class ReadmeDomainPairTest(unittest.TestCase):
    u"""独立監査 REVISE(2026-10-20、2 回目)。**数だけでなく、その数がどの
    領域(書類の種類)の実測かという字も**、同じ場所(bullet・段落)に在ること
    を縛る。領域名を書き間違える(表計算と議事録を取り違える)・分母の出どころ
    (書類 1 つ・主張 24 件)を落とす・時系列(engine の新設より前の実測)を
    落とす、の 3 種を直す前の REVISE で見つかった(封は書き換えない。この
    門を足した)。
    """

    def setUp(self):
        self.t = text(README)

    def test_g6_errdet_bullet_is_spreadsheet_not_parliament(self):
        u"""errdet_cprime の 8/8・4/8 は表計算(R001〜R035)の実測。
        議事録(national-parliament-minutes)ではない。
        """
        bullets = [b for b in readme_bullets(self.t) if "8/8" in b and "4/8" in b]
        self.assertTrue(bullets, u"8/8 と 4/8 を含む bullet が見つからない")
        for b in bullets:
            nb = norm_ws(b)
            self.assertIn("spreadsheet", nb, nb)
            self.assertNotIn("parliament", nb, nb)

    def test_g6_false_pass_bullet_names_the_parliament_domain_as_separate(self):
        u"""1/49(false_pass_round12)は議事録の別の材料。「同じ領域」と書かない。"""
        bullets = [b for b in readme_bullets(self.t) if "1/49" in b]
        self.assertTrue(bullets, u"1/49 を含む bullet が見つからない")
        for b in bullets:
            nb = norm_ws(b)
            self.assertIn("national-parliament-minutes", nb, nb)
            self.assertIn("separate dataset", nb, nb)

    def test_g6_sheet_connection_paragraph_names_24_claim_single_spreadsheet(self):
        u"""poc_ab_score の 24 は正解集合の主張(claim)の数。書類は 1 つ。"""
        paras = [p for p in readme_paragraphs(self.t) if "24/24" in p and "12/24" in p]
        self.assertTrue(paras, u"24/24 と 12/24 を含む段落が見つからない")
        for p in paras:
            np_ = norm_ws(p)
            self.assertIn("24-claim", np_, np_)
            self.assertIn("single spreadsheet", np_, np_)

    def test_g6_first_18_18_bullet_states_the_timeline_before_holds_existed(self):
        u"""attr_inject(2026-10-17)は holds.py 新設(2026-10-19、commit 295e636)
        より前の実測。production hold rule を「迂回した」とは書かない。
        """
        bullets = [b for b in readme_bullets(self.t) if "18/18" in b]
        self.assertTrue(bullets, u"18/18 を含む bullet が見つからない")
        self.assertIn("before the production hold rules", norm_ws(bullets[0]))

    def test_g6_4_of_8_bullet_names_the_overwrite_not_rule_based(self):
        u"""独立監査 REVISE(2026-10-20、3 回目)。旧 C は LLM の席 + 旧検証層
        (`docs/DOMAIN1_ERRDET_CPRIME_RESULT_2026-10-19.md` §3「旧 C はこの 4 件を
        『確認済み』で上書きしていた」)で、rule-based ではない。
        """
        bullets = [b for b in readme_bullets(self.t) if "4/8" in b]
        self.assertTrue(bullets, u"4/8 を含む bullet が見つからない")
        for b in bullets:
            nb = norm_ws(b)
            self.assertIn("overwrote", nb, nb)
            self.assertNotIn("rule-based", nb, nb)


if __name__ == "__main__":
    unittest.main()
