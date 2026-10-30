# -*- coding: utf-8 -*-
u"""門: `docs/FACTS_FOR_BUYERS_2026-10-20.md`(測った事実 1 冊)の数を記録に縛る。

**この file は測定をしない。**1 冊の表の各行に付いた `〔…〕` の印(記録の path・key・数)を、
記録をいま開いて照合する(`measure/facts_check_2026-10-20.py` と同じ関数)。API は呼ばない。

守るのは 10 つ。
  1. 全部の印が記録と一致する(CLI の `--check` も 0 で終わる。行の絞り込み・一覧も働く)
  2. 章が §0 から §7 まで順に在り、§0 は 10 行以内
  3. §1 の先頭の 3 行が、表計算の接続(12 / 24)・誤り検出(検証層が消した 4)・XBRL の R-S2(11.6%)
  4. §1〜§4 の全部の行が、印・記録 path・再現コマンド(自分の ID)・門の file・記録を作る script を持つ
  5. 数の欄の字が、印から作った字(`ラベル 数`)と一致する(印を直さずに数だけ書き換えると赤)。
     表の注・領域の欄・表の外の字に、印の無い率・比・3 桁以上の数が無い
  6. 禁句(精度・LLM より正確・世界で 1 社・金額・契約・税・USD)が無い
  7. §5 の字が、引いた文書に実在する。§4-2 の封に結果文書が無い
  8. §6 の木の数が `git ls-tree` の別実装(grep)と一致する。試験 file・収集本数は覆いの記録に縛る
  9. 行数・印の本数が字で留めてある(行や印を黙って消すと赤)
 10. 判定に歯が在る(壊した字・壊した記録を食わせて赤になる)
"""
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "measure", "facts_check_2026-10-20.py")
DOC = os.path.join(ROOT, "docs", "FACTS_FOR_BUYERS_2026-10-20.md")
SUITE = os.path.join(ROOT, "fixtures", "suite_coverage_2026-10-16.json")
REV = "c740e61"

# 行の本数・印の本数。**黙って減らすと赤くなる**ように字で留める(増やすときは直す)
EXPECT_ROWS = {"L": 41, "D": 29, "H": 11, "HD": 4, "P": 25, "Q": 8, "N": 13, "A": 11}
EXPECT_CLAIMS = 553   # 印の本数(表の行の印、§5 の本数の印 1、§6 の印 11)

FORBIDDEN = [u"精度", u"LLM より正確", u"世界で 1 社", u"金額", u"契約", u"税", u"USD"]
ALLOWED_PATH_PREFIX = (u"fixtures/", u"tests/adapters/xbrl/mutations.json", u"core/py/audit_core/")


def _load_mod():
    spec = importlib.util.spec_from_file_location("facts_check_t", SRC)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def text(p=DOC):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sections(doc):
    u"""`## §N …` で区切った {N: 本文の行のリスト}。§0 の前は -1。"""
    out = {-1: []}
    cur = -1
    for line in doc.splitlines():
        m = re.match(r"^## §(\d) ", line)
        if m:
            cur = int(m.group(1))
            out[cur] = []
            continue
        out[cur].append(line)
    return out


def table_cells(line):
    return [c.strip() for c in line.strip().strip(u"|").split(u"|")]


def table_rows(lines):
    rows = []
    for ln in lines:
        if ln.startswith(u"|") and not re.match(r"^\|[-| ]+\|$", ln):
            c = table_cells(ln)
            if re.match(r"^[A-Z]+-\d+$", c[0]):
                rows.append((ln, c))
    return rows


def number_flags(s):
    u"""字の中の、印の無い数の疑い(率・比・3 桁以上・小数)を返す。code span・印・日付・識別子は除く。"""
    s = re.sub(r"`[^`]*`", u" ", s)
    s = re.sub(u"〔[^〕]*〕", u" ", s)
    s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
    flags = []
    for m in re.finditer(r"\d+\s*/\s*\d+", s):
        flags.append(m.group(0))
    for m in re.finditer(r"(?<![A-Za-z0-9_\-.])(\d[\d,]*(?:\.\d+)?)(\s*%)?(?![A-Za-z0-9_])", s):
        raw = m.group(1)
        digits = raw.replace(u",", u"")
        if m.group(2) or u"." in digits or len(digits.split(u".")[0]) >= 3:
            flags.append(m.group(0))
    return flags


def forbidden_hits(doc):
    return [w for w in FORBIDDEN if w in doc]


class CheckAgainstRecordsTest(unittest.TestCase):
    u"""1. 全部の印が記録と一致する。"""

    @classmethod
    def setUpClass(cls):
        cls.fc = _load_mod()
        cls.doc = text()

    def test_1_every_claim_matches_its_record(self):
        buf = io.StringIO()
        ok, ng, skip = self.fc.run_check(doc_text=self.doc, out=buf)
        self.assertEqual(ng, 0, buf.getvalue())
        self.assertEqual(ok + skip, EXPECT_CLAIMS)
        if skip:
            # git の印だけが SKIP になる(commit %s がこの clone に無い)。ほかの印は全部 OK を確かめた
            self.skipTest(u"git の印 %d 本を照合できない(commit %s が無い clone)。履歴を持つ clone で走らせること"
                          % (skip, REV))

    def test_2_cli_check_exits_zero_and_says_ok(self):
        r = subprocess.run([sys.executable, SRC, "--check"], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = r.stdout.decode("utf-8")
        self.assertEqual(r.returncode, 0, out + r.stderr.decode("utf-8"))
        self.assertIn(u"NG 0", out)
        self.assertNotIn(u"\nNG ", out)

    def test_3_cli_row_filter_and_list(self):
        r = subprocess.run([sys.executable, SRC, "--check", "--row", "L-01"], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = r.stdout.decode("utf-8")
        self.assertEqual(r.returncode, 0, out)
        self.assertIn(u"OK    L-01", out)
        self.assertNotIn(u"L-02", out)
        r = subprocess.run([sys.executable, SRC, "--check", "--row", "L-99"], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(r.returncode, 1)
        r = subprocess.run([sys.executable, SRC, "--list"], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ids = r.stdout.decode("utf-8").split()
        self.assertEqual(ids[0], u"L-01")
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn(u"A-11", ids)

    def test_4_claim_paths_are_in_allowed_places(self):
        for lineno, rid, kind, body, _bare in self.fc.claims(self.doc):
            if kind == u"git":
                continue
            left, _ = self.fc.split_eq(body)
            paths = []
            if kind == u"wc":
                paths = left.split(u" ")
            else:
                for term in re.split(u" ＋ | ÷ | :: ", left):
                    if u"#" in term:
                        paths.append(term.split(u"#", 1)[0].strip())
            self.assertTrue(paths, (lineno, body))
            for p in paths:
                self.assertTrue(p.startswith(ALLOWED_PATH_PREFIX), (lineno, p))
                self.assertTrue(os.path.isfile(os.path.join(ROOT, p)), (lineno, p))


class StructureTest(unittest.TestCase):
    u"""2〜4・9. 章・先頭の 3 行・行の部品・本数の留め。"""

    @classmethod
    def setUpClass(cls):
        cls.fc = _load_mod()
        cls.doc = text()
        cls.sec = sections(cls.doc)

    def test_5_sections_are_in_order_and_complete(self):
        heads = re.findall(r"(?m)^## §(\d) ", self.doc)
        self.assertEqual(heads, [str(i) for i in range(8)])
        self.assertIn(u"## §0 この文書の読み方", self.doc)
        self.assertIn(u"## §1 負けた数(先頭)", self.doc)
        self.assertIn(u"## §5 記録が無い数(門なし)", self.doc)

    def test_6_section0_is_at_most_ten_lines(self):
        body = [l for l in self.sec[0] if l.strip() and l.strip() != u"---"]
        self.assertLessEqual(len(body), 10)
        joined = u"\n".join(body)
        self.assertIn(u"計算 対 出所", joined)
        self.assertIn(u"何でないか", joined)

    def test_7_section1_starts_with_the_three_losses(self):
        rows = table_rows(self.sec[1])
        self.assertEqual([r[1][0] for r in rows[:3]], [u"L-01", u"L-02", u"L-03"])
        r1, r2, r3 = [ln for ln, _ in rows[:3]]
        # L-01: Core 12 / 24(保留 12)
        self.assertIn(u"poc_ab_score_2026-10-17.json#arms > B Audit Core > 正解集合 > 正しい接続 = 12〕", r1)
        self.assertIn(u"B Audit Core > 正解集合 > 保留 = 12〕", r1)
        self.assertIn(u"12 / 24 = 50.0%", r1)
        # L-02: LLM + Core(旧い検証層)の検出 4、席そのままは 8
        self.assertIn(u"errdet_score_2026-10-17.json#A / C の内訳 > C seat1 > 検出 = 4〕", r2)
        self.assertIn(u"A / C の内訳 > A seat1 > 検出 = 8〕", r2)
        self.assertIn(u"席の見つけた誤りを消した", r2)
        # L-03: R-S2 11.6%(線 10% を外した)
        self.assertIn(u"38 / 329 = 11.6%", r3)
        self.assertIn(u"RS2_E2_over_G_max = 0.1〕", r3)
        self.assertIn(u"Q1 > RS2 > pass = false〕", r3)

    def test_8_row_counts_are_pinned(self):
        got = {
            "L": len(table_rows(self.sec[1])),
            "D": len(table_rows(self.sec[2])),
            "H": len([1 for ln, c in table_rows(self.sec[3]) if c[0].startswith(u"H-") and u"〔" in ln]),
            "HD": len([1 for ln, c in table_rows(self.sec[3]) if c[0].startswith(u"H-") and u"〔" not in ln]),
            "P": len([1 for ln, c in table_rows(self.sec[4]) if c[0].startswith(u"P-")]),
            "Q": len([1 for ln, c in table_rows(self.sec[4]) if c[0].startswith(u"Q-")]),
            "N": len(table_rows(self.sec[5])),
            "A": len(table_rows(self.sec[6])),
        }
        self.assertEqual(got, EXPECT_ROWS)
        ids = [c[0] for sec in range(1, 7) for _, c in table_rows(self.sec[sec])]
        self.assertEqual(len(ids), len(set(ids)), u"行の ID が重なっている")

    def test_9_every_measured_row_has_claim_path_command_gate_and_script(self):
        n_checked = 0
        for sec in (1, 2, 3, 4, 6):
            for ln, c in table_rows(self.sec[sec]):
                rid = c[0]
                if rid.startswith(u"H-") and u"〔" not in ln:
                    continue
                if rid.startswith(u"Q-"):
                    continue
                n_checked += 1
                self.assertIn(u"〔", ln, rid)
                self.assertRegex(ln, u"fixtures/[^ 〕#]+\\.json#|tests/adapters/xbrl/mutations\\.json#|〔git |〔wc ", rid)
                self.assertIn(u"`python3 measure/facts_check_2026-10-20.py --check --row %s`" % rid, ln, rid)
                if sec != 6:
                    gates = re.findall(r"`(tests/measure/test_[a-z0-9_]+\.py)`", ln)
                    self.assertTrue(gates, u"%s: 門の file が無い" % rid)
                    for g in gates:
                        self.assertTrue(os.path.isfile(os.path.join(ROOT, g)), (rid, g))
                scripts = re.findall(r"記録を作る: ((?:`measure/[A-Za-z0-9_\-.]+\.py` ?)+)", ln)
                for grp in scripts:
                    for s in re.findall(r"`(measure/[^`]+)`", grp):
                        self.assertTrue(os.path.isfile(os.path.join(ROOT, s)), (rid, s))
                # 3-1 の穴は根拠の結果文書を持つ
                if sec == 3:
                    docs = re.findall(r"`(docs/[A-Za-z0-9_\-.]+\.md)`", ln)
                    self.assertTrue(docs, rid)
                    for d in docs:
                        self.assertTrue(os.path.isfile(os.path.join(ROOT, d)), (rid, d))
        self.assertGreaterEqual(n_checked, 30 + 20 + 7 + 18 + 11)

    def test_10_claim_total_is_pinned_from_below(self):
        n = len(self.fc.claims(self.doc))
        self.assertEqual(n, EXPECT_CLAIMS)
        kinds = set(k for _, _, k, _, _ in self.fc.claims(self.doc))
        self.assertEqual(kinds, set([u"rec", u"rate", u"sum", u"cnt", u"git", u"wc"]))


class NumberCellMatchesClaimsTest(unittest.TestCase):
    u"""5. 数の欄の字 = 印から作った字。印の無い数が表の外・注に無い。"""

    @classmethod
    def setUpClass(cls):
        cls.fc = _load_mod()
        cls.doc = text()
        cls.sec = sections(cls.doc)

    def shown(self, kind, body):
        left, exp = self.fc.split_eq(body)
        if kind == u"rate":
            a_ref, b_ref = left.split(self.fc.DIV, 1)
            a = self.fc.sum_terms(a_ref)
            b = self.fc.sum_terms(b_ref)
            return u"%s / %s = %s" % (a, b, exp)
        return exp

    def _items_cell(self, sec, cells):
        u"""数の欄(§1・§2・§4: 3 番目。§3-1: 3 番目で `。数: ` の後ろ)から品目の並びと注を返す。"""
        cell = cells[2]
        if sec == 3 and u"。数: " in cell:
            head, rest = cell.split(u"。数: ", 1)
            return rest, head
        return cell, u""

    def test_11_number_cell_equals_label_plus_shown_in_claim_order(self):
        n = 0
        for sec in (1, 2, 3, 4):
            for ln, c in table_rows(self.sec[sec]):
                toks = self.fc.TOKEN_RE.findall(ln)
                if not toks:
                    continue
                cell, _head = self._items_cell(sec, c)
                items_part = cell.split(u"。", 1)[0]
                segs = items_part.split(u"; ")
                self.assertEqual(len(segs), len(toks), u"%s: 数の欄の品目 %d と印 %d" % (c[0], len(segs), len(toks)))
                for seg, (kind, body) in zip(segs, toks):
                    sh = self.shown(kind, body)
                    self.assertTrue(seg.endswith(u" " + sh), u"%s: 「%s」は「%s」で終わらない" % (c[0], seg, sh))
                    n += 1
        self.assertGreaterEqual(n, EXPECT_CLAIMS - 12)

    def test_12_no_unbound_rates_ratios_or_big_numbers_in_row_prose(self):
        for sec in (1, 2, 3, 4):
            for ln, c in table_rows(self.sec[sec]):
                prose = [c[1]]
                cell, head = self._items_cell(sec, c)
                if u"。" in cell:
                    prose.append(cell.split(u"。", 1)[1])
                if head:
                    prose.append(head)
                for p in prose:
                    self.assertEqual(number_flags(p), [], u"%s: 印の無い数 %r in %r" % (c[0], number_flags(p), p))

    def test_13_no_unbound_numbers_outside_tables(self):
        in_fence = False
        for sec_no, lines in sorted(self.sec.items()):
            for ln in lines:
                if ln.startswith(u"```"):
                    in_fence = not in_fence
                    continue
                if in_fence or ln.startswith(u"|") or not ln.strip():
                    continue
                self.assertEqual(number_flags(ln), [], u"§%s の表の外に印の無い数 %r: %s" % (sec_no, number_flags(ln), ln))

    def test_14_each_claim_literal_is_printed_in_its_row(self):
        for lineno, rid, kind, body, bare in self.fc.claims(self.doc):
            if rid is None:
                continue
            self.assertIn(self.shown(kind, body), bare, (rid, body))

    def test_15_forbidden_words_are_absent(self):
        self.assertEqual(forbidden_hits(self.doc), [])

    def test_16_qwed_is_only_calc_versus_origin(self):
        self.assertIn(u"計算 対 出所", self.doc)
        for bad in (u"QWED より", u"QWED に勝", u"QWED に負け", u"QWED の方が"):
            self.assertNotIn(bad, self.doc)


class QuotesAndSealsTest(unittest.TestCase):
    u"""7. §5 の字が文書に在る。§4-2 の封に結果文書が無い。"""

    @classmethod
    def setUpClass(cls):
        cls.fc = _load_mod()
        cls.doc = text()
        cls.sec = sections(cls.doc)

    def test_17_section5_quotes_exist_in_the_cited_docs(self):
        n = 0
        for ln, c in table_rows(self.sec[5]):
            self.assertIn(u"記録なし(数は文書の字)", ln, c[0])
            self.assertNotIn(u"〔", ln, c[0])
            m = re.search(r"`(docs/[A-Za-z0-9_\-.]+\.md)`", c[1])
            self.assertTrue(m, c[0])
            p = os.path.join(ROOT, m.group(1))
            self.assertTrue(os.path.isfile(p), c[0])
            body = text(p)
            self.assertIn(c[2], body, u"%s: 引いた字が %s に無い" % (c[0], m.group(1)))
            n += 1
        self.assertEqual(n, 13)

    def test_18_section3_doc_only_quotes_exist_in_the_ledger(self):
        ledger = text(os.path.join(ROOT, "docs", "XBRL_OPEN_ISSUES_2026-10-15.md"))
        n = 0
        for ln, c in table_rows(self.sec[3]):
            if not c[0].startswith(u"H-") or u"〔" in ln:
                continue
            self.assertIn(u"記録なし(数は文書の字)", ln, c[0])
            self.assertIn(c[3], ledger, c[0])
            n += 1
        self.assertEqual(n, 4)

    def test_19_unresulted_seals_exist_and_have_no_result_doc(self):
        import glob
        n = 0
        for ln, c in table_rows(self.sec[4]):
            if not c[0].startswith(u"Q-"):
                continue
            seal = re.search(r"`(docs/[A-Za-z0-9_\-.]+\.md)`", c[1]).group(1)
            self.assertTrue(os.path.isfile(os.path.join(ROOT, seal)), seal)
            stem = re.search(r"`docs/([A-Z0-9_]+)\*RESULT\*`", c[2]).group(1)
            self.assertTrue(os.path.basename(seal).startswith(stem + u"_"), (seal, stem))
            self.assertIn(u"_SEAL_", os.path.basename(seal))
            self.assertEqual(glob.glob(os.path.join(ROOT, "docs", stem + u"*RESULT*")), [], stem)
            n += 1
        self.assertEqual(n, 8)


class AssetNumbersTest(unittest.TestCase):
    u"""8. 資産の数。"""

    @classmethod
    def setUpClass(cls):
        cls.fc = _load_mod()
        cls.doc = text()

    def _has_rev(self):
        r = subprocess.run(["git", "cat-file", "-e", REV + "^{commit}"], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r.returncode == 0

    def test_20_fenced_shell_commands_agree_with_the_claims(self):
        m = re.search(r"(?s)```sh\n(.*?)```", self.doc)
        self.assertTrue(m)
        lines = [l for l in m.group(1).splitlines() if l.strip()]
        pairs = list(zip(lines[0::2], lines[1::2]))
        self.assertEqual([p[0] for p in pairs], [u"# A-01", u"# A-02", u"# A-03", u"# A-04", u"# A-05", u"# A-11"])
        want = {}
        for lineno, rid, kind, body, _ in self.fc.claims(self.doc):
            if rid and rid.startswith(u"A-"):
                want[rid] = self.fc.split_eq(body)[1]
        if not self._has_rev():
            self.skipTest(u"commit %s が無い clone" % REV)
        for (hdr, cmd) in pairs:
            rid = hdr[2:].strip()
            r = subprocess.run(["sh", "-c", cmd], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(r.returncode, 0, (cmd, r.stderr))
            self.assertEqual(r.stdout.decode("utf-8").strip(), want[rid], (rid, cmd))

    def test_21_suite_numbers_are_bound_to_the_coverage_record(self):
        with io.open(SUITE, encoding="utf-8") as fh:
            rec = json.load(fh)
        want = {
            u"A-06": rec["test_files_on_disk"],
            u"A-07": rec["by_directory"]["tests/measure"],
            u"A-08": rec["commands"]["pytest"]["tests"],
            u"A-09": rec["commands"]["discover"]["tests"],
        }
        got = {}
        for lineno, rid, kind, body, _ in self.fc.claims(self.doc):
            if rid in want:
                got[rid] = int(self.fc.split_eq(body)[1])
        self.assertEqual(got, want)

    def test_22_record_is_the_live_disk_count(self):
        with io.open(SUITE, encoding="utf-8") as fh:
            rec = json.load(fh)
        n = 0
        for base, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__", ".pytest_cache")]
            n += len([f for f in files if f.startswith("test_") and f.endswith(".py")])
        self.assertEqual(rec["test_files_on_disk"], n)


class NoApiNoNetworkTest(unittest.TestCase):
    u"""0 回の API・通信なし・環境変数を読まない(道具は記録を読むだけ)。"""

    def test_33_the_check_script_touches_no_env_no_network_no_llm(self):
        src = text(SRC)
        for bad in (u"os.environ", u"getenv", u"urllib", u"requests", u"socket", u"http.client",
                    u"anthropic", u"openai", u"subprocess.Popen("):
            self.assertNotIn(bad, src, bad)
        # 外へ出す subprocess は git だけ
        calls = re.findall(r"subprocess\.run\(\[([^\]]*)\]", src)
        self.assertTrue(calls)
        for c in calls:
            self.assertTrue(c.strip().startswith(u'"git"'), c)

    def test_34_commit_hashes_named_in_the_doc_exist(self):
        doc = text()
        hashes = sorted(set(re.findall(r"`([0-9a-f]{7})`", doc)))
        self.assertEqual(hashes, sorted([u"8f18b53", u"4e7f490", u"9994f64", u"bcf2bad",
                                         u"5eb80a2", u"26ee30f", u"a516288", u"c740e61",
                                         u"e37ae3b", u"c0d7cc0", u"43fe0e3", u"aeae608",
                                         u"87f83fd", u"6a34db5",
                                         u"365b468", u"f8cc00b", u"071abb4", u"cd25727",
                                         u"6bea94b", u"ed615b5",
                                         u"5f3ae0a", u"fb6f268"]))
        r = subprocess.run(["git", "cat-file", "-e", REV + "^{commit}"], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode != 0:
            self.skipTest(u"commit %s が無い clone" % REV)
        for h in hashes:
            r = subprocess.run(["git", "cat-file", "-e", h + "^{commit}"], cwd=ROOT,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(r.returncode, 0, h)


class ResultDocCountingTest(unittest.TestCase):
    u"""§4 の注: 結果文書の「当たり N」は、記録の true の本数に null の本数のうち一部を足した数。"""

    def test_23_result_docs_count_the_null_items_as_hits(self):
        def load(rel):
            with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                return json.load(fh)

        cases = [
            ("fixtures/xbrl/gen_c/c0_2026-10-20.json", u"**予測 G-1〜G-14**",
             "docs/XBRL_GENERALITY_RESULT_2026-10-20.md", u"**当たり 8 / 外れ 6。**"),
            ("fixtures/xbrl/gen_c/c0_p20_2026-10-20.json", u"**予測 R-1〜R-11**",
             "docs/XBRL_GENERALITY_P20_RESULT_2026-10-20.md", u"**当たり 5 / 外れ 6。**"),
            ("fixtures/xbrl/gen_c/c1_2026-10-20.json", u"**予測 K-1〜K-12**",
             "docs/XBRL_GENERALITY_C1_RESULT_2026-10-20.md", u"**当たり 10 / 外れ 2。**"),
            ("fixtures/xbrl/gen_c/alpha_2026-10-20.json", u"**予測 S-1〜S-9**",
             "docs/XBRL_GENERALITY_ALPHA_RESULT_2026-10-20.md", u"**当たり 5 / 外れ 4。**"),
        ]
        for rec_path, key, doc_path, quote in cases:
            items = load(rec_path)[key]
            t = len([x for x in items if x["当たり"] is True])
            f = len([x for x in items if x["当たり"] is False])
            nl = len([x for x in items if x["当たり"] is None])
            m = re.search(r"当たり (\d+) / 外れ (\d+)", quote)
            doc_hit, doc_miss = int(m.group(1)), int(m.group(2))
            self.assertIn(quote, text(os.path.join(ROOT, doc_path)))
            self.assertEqual(doc_miss, f, rec_path)
            self.assertEqual(doc_hit, t + nl, rec_path)  # null は全部、結果文書で当たりと判定された
        items = load("fixtures/xbrl/naming_fix/p21_2026-10-20.json")[u"**予測 N-1〜N-12**"]
        t = len([x for x in items if x["当たり"] is True])
        f = len([x for x in items if x["当たり"] is False])
        nl = len([x for x in items if x["当たり"] is None])
        self.assertIn(u"**当たり 10 / 外れ 0 / 判定しない 2。**",
                      text(os.path.join(ROOT, "docs", "XBRL_NAMING_FIX_RESULT_2026-10-20.md")))
        self.assertEqual((t, f, nl), (8, 0, 4))  # 10 = 8 + 2、判定しない 2 = null のうち 2


class TeethTest(unittest.TestCase):
    u"""10. 判定に歯が在る: 壊した字・壊した記録を食わせて赤になる。"""

    @classmethod
    def setUpClass(cls):
        cls.fc = _load_mod()
        cls.doc = text()

    def _run(self, doc):
        buf = io.StringIO()
        ok, ng, skip = self.fc.run_check(doc_text=doc, out=buf)
        return ok, ng, buf.getvalue()

    def test_24_a_changed_literal_is_red(self):
        bad = self.doc.replace(u"#arms > B Audit Core > 正解集合 > 保留 = 12〕", u"#arms > B Audit Core > 正解集合 > 保留 = 13〕", 1)
        self.assertNotEqual(bad, self.doc)
        ok, ng, out = self._run(bad)
        self.assertEqual(ng, 1, out)

    def test_25_a_changed_rate_is_red(self):
        bad = self.doc.replace(u"#A_P16 > G = 11.6%〕", u"#A_P16 > G = 11.5%〕", 1)
        self.assertNotEqual(bad, self.doc)
        self.assertEqual(self._run(bad)[1], 1)

    def test_26_a_wrong_key_is_red(self):
        bad = self.doc.replace(u"#arms > B Audit Core > 正解集合 > 保留 = 12〕", u"#arms > B Audit Core > 正解集合 > 保留し = 12〕", 1)
        ok, ng, out = self._run(bad)
        self.assertEqual(ng, 1, out)
        self.assertIn(u"key が無い", out)

    def test_27_a_poisoned_record_is_red(self):
        fc = self.fc
        rel = "fixtures/xbrl/final8/commander_only/score_report_2026-10-14.json"
        fc.load_json(rel)
        saved = fc._CACHE[rel]
        try:
            fc._CACHE[rel] = json.loads(json.dumps(saved))
            fc._CACHE[rel]["A_P16"]["E2_strict"] = 37
            ok, ng, out = self._run(self.doc)
            self.assertGreaterEqual(ng, 1, out)
            self.assertIn(u"L-03", out)
        finally:
            fc._CACHE[rel] = saved
        self.assertEqual(self._run(self.doc)[1], 0)

    def test_28_a_list_length_claim_is_red_when_the_list_changes(self):
        fc = self.fc
        rel = "fixtures/sheet/errdet_score_2026-10-17.json"
        fc.load_json(rel)
        saved = fc._CACHE[rel]
        try:
            clone = json.loads(json.dumps(saved))
            clone[u"A / C の内訳"][u"C seat1"][u"検出"].append(u"R999")
            fc._CACHE[rel] = clone
            ok, ng, out = self._run(self.doc)
            self.assertGreaterEqual(ng, 1, out)
        finally:
            fc._CACHE[rel] = saved

    def test_29_rounding_is_half_up_not_half_even_or_down(self):
        fc = self.fc
        # 1 / 16 = 6.25 -> 6.3(切り捨て・偶数丸めなら 6.2)
        self.assertEqual(str(fc.pct(fc.Decimal(1), fc.Decimal(16))), u"6.3")
        # 0 の分母は赤
        with self.assertRaises(fc.Ng):
            fc.pct(fc.Decimal(1), fc.Decimal(0))

    def test_30_the_doc_row_with_a_decimal_threshold_is_compared_as_a_number(self):
        fc = self.fc
        self.assertTrue(fc.literal_equal(0.1, u"0.1"))
        self.assertFalse(fc.literal_equal(0.1, u"0.11"))
        self.assertTrue(fc.literal_equal(True, u"true"))
        self.assertFalse(fc.literal_equal(False, u"true"))
        self.assertTrue(fc.literal_equal(None, u"null"))
        self.assertFalse(fc.literal_equal(0, u"null"))

    def test_31_number_audit_catches_unbound_figures(self):
        self.assertEqual(number_flags(u"席は 3 つ。P21 の 2026-10-20 は `192` 〔rec x#y = 192〕"), [])
        self.assertTrue(number_flags(u"当たりは 12 / 24 だった"))
        self.assertTrue(number_flags(u"率は 11.6% だった"))
        self.assertTrue(number_flags(u"本数は 192 本"))
        self.assertTrue(number_flags(u"本数は 1,203 本"))

    def test_32_forbidden_words_check_would_fire(self):
        for w in FORBIDDEN:
            self.assertIn(w, forbidden_hits(self.doc + u"\n" + w))


if __name__ == "__main__":
    unittest.main()
