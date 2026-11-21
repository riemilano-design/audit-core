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
EXPECT_ROWS = {"L": 86, "D": 63, "H": 11, "HD": 4, "P": 71, "Q": 7, "N": 13, "A": 11}
EXPECT_CLAIMS = 3628   # 2026-11-21(2): L-86(11)・D-63(16)・P-71(8)で +35(XG1 = 便 XG0 で候補が 2 つ以上だった行を、数を持てる要素・計算書の種類・業種の科目の一覧で絞ると、要素が 1 つに決まる行はどれだけ増えるか。予測 XG1-1〜XG1-7 の判定の根拠・来歴・材料の sha256)。2026-11-21: L-85(10)・D-62(13)・P-70(8)で +31(XG0 = 有価証券報告書の計算書の行で、行の字と標準タクソノミのラベルの表だけで要素が 1 つに決まる行はどれだけか。予測 XG0-1〜XG0-6 の判定の根拠・来歴・材料の並びの sha256)。

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
        self.assertEqual(n, 7)   # 2026-11-01: Q-03(AI_PROSE)は記録に判定の欄が在るので P-29 へ。ID は空けたまま


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
                                         u"5f3ae0a", u"fb6f268",
                                         # 2026-11-01: 候補の欄の系列(封・承認の追記・結果)
                                         u"0df5222", u"db68a2c", u"cb8612f",
                                         u"9d847c0", u"3001a10",
                                         u"68c0a3b", u"31808fa", u"250b916",
                                         # 2026-11-01(2): P-29(AI が書いた文の最小実験。封・門③の置き換え・記録・凍結の観測)
                                         u"4621b73", u"9140e6b", u"ab7d132", u"c11427c",
                                         # 2026-11-02: P-30(cache の無い clone で README の手順。封)
                                         u"443a078",
                                         # 2026-11-02(2): L-45(README の入口の字の直し。封)
                                         u"6cde4b3",
                                         # 2026-11-02(3): P-31(導出の検証の診断(前半)。封)
                                         u"67efc7a",
                                         # 2026-11-02(4): P-32(導出の検証の診断(後半)。封)
                                         u"42b51d3",
                                         # 2026-11-02(5): P-33(主語の制約つきの導出。封)
                                         u"ab09aa6",
                                         # 2026-11-02(6): P-34(近傍の深さ 2 と型 2 つ。封)
                                         u"cb3ba0d",
                                         # 2026-11-02(7): P-35(偽の数に導出一致を出す率。封)
                                         u"79dba8b",
                                         # 2026-11-02(8): P-36(engine が止めた真の文 53 の中身。封)
                                         u"ab2ad5b",
                                         # 2026-11-02(9): P-37(「その他」の行の主語の結びつき。封)
                                         u"8d4cf3b",
                                         # 2026-11-02(10): P-38(文の期の印と engine の context。封)
                                         u"5a3b2a0",
                                         # 2026-11-02(11): P-39(AI の文を P27E と P27 で再判定。封)
                                         u"35f624c",
                                         # 2026-11-02(12): P-40(出所のずれの名指し。封)
                                         u"3a099e7",
                                         # 2026-11-03: P-41(「その他」の主語の結び直し O = P28。封)
                                         u"c6cbfae",
                                         # 2026-11-03(2): P-42(外部の数の文の profile に O を重ねる P28E。封)
                                         u"7bfad77",
                                         # 2026-11-04: P-43(数の読み取り N = P29・P29E。封)
                                         u"48e7078",
                                         # 2026-11-04(2): P-44(丸め方の根拠が混ざる桁 RB = P30E。封)
                                         u"de23edc",
                                         # 2026-11-05: P-45(注入の仕掛けの数の読み H = 切り替え yen_scan_2026_11_05。封)
                                         u"89afc79",
                                         # 2026-11-05(2): P-46(AI の文への注入の型を広げる J = T2_UNIT・T6_PRIOR・T7_ROUND。封)
                                         u"edad5cd",
                                         # 2026-11-06: P-47(前期の fact に結ばれた数に当期の値を入れる注入 T9 = 期の取り違えの率。封)
                                         u"3a6aefa",
                                         # 2026-11-06(2): P-48(T9 の第 2 便 = 注入後の claim を基準の claim の id で引く対応付け。封)
                                         u"ec00fa1",
                                         # 2026-11-06(3): P-49(期の手がかりを縛る engine 規則 PB = P32E。封)
                                         u"b7824e6",
                                         # 2026-11-09: P-50(注入の仕掛けの T5 を円族の数に作る T5Y。封)
                                         u"79d05cd",
                                         # 2026-11-10: P-51(人が書いた決算短信の概況で engine を測る TS。封と結果の commit)
                                         u"5bba61e", u"7ca4eb0",
                                         # 2026-11-10(2): P-52(AI の文の形を増やす FX。封と結果の commit)
                                         u"ad65426", u"f925b7b",
                                         # 2026-11-10(3): P-53(表の前期の列の数を前期の手がかりとして扱う engine 規則 T = P33E。封と結果の commit)
                                         u"eb281f1", u"c951e03",
                                         # 2026-11-10(4): P-54(engine の非機能の実測 NF = verify_document 1 回の時間とメモリ。封と結果の commit)
                                         u"abe8f4d", u"97f8a48",
                                         # 2026-11-14: P-55(短信の概況の文を同じ短信の添付の財務諸表で確かめる TSS = P33E。封と結果の commit)
                                         u"e56d678", u"1007755",
                                         # 2026-11-14(2): P-56(TSS の第 2 便 = 中間の短信の期の名前を measure/ の側で写す・近い行を読む。封の commit)
                                         u"a1fd09b",
                                         # 2026-11-15: P-57(TSS の便 1b = 短信の概況の文に誤りを 1 件ずつ入れ、同じ短信の財務諸表に当てて止めるか。封の commit)
                                         u"bcc244a",
                                         # 2026-11-15(2): P-58(KAM の便 = 監査報告書の KAM の文を同じ有報の fact で確かめる。封の commit)
                                         u"497a466",
                                         # 2026-11-16: P-59(YS の便 = 有報の 3 つの節の文を同じ有報の fact で確かめる。封の commit)
                                         u"e7754d7",
                                         # 2026-11-17: P-60(AT の便 = 便をまたいだ集計。封の commit)
                                         u"52f3a22",
                                         # 2026-11-17(2): P-61(PS の便 = 止めた行に同じ短信のサマリーの予想の fact という当てる先が在るか。最初の封の commit)
                                         u"a080ce5",
                                         # 2026-11-17(3): P-62(NR の便 = engine の inline XBRL の読み取りの欠陥が過去の便の判定に効いた量。封の commit)
                                         u"720a473",
                                         # 2026-11-17(4): P-63(NRE の便 = engine の inline XBRL の読み取りの直しの測定。封の commit)
                                         u"36ca78f",
                                         # 2026-11-18: P-64(RT の便 = TSS の系列を直した engine で取り直して前の記録と並べる。封の commit)
                                         u"b4c08fc",
                                         # 2026-11-18(2): P-65(SE の便 = サマリーを engine に渡したときに動く行と、engine の語彙が予想の枠の fact に届くか。封の commit)
                                         u"fabd87b",
                                         # 2026-11-19: P-66(SC の便 = 文は一部分を言うのに全体の fact に結んだ行を文の字で止める後付けの規則。封の commit)
                                         u"5b77133",
                                         # 2026-11-19(2): P-67(PA の便 = 実績の数でないのに実績の fact に結んだ行を文の字で止める後付けの規則。封の commit)
                                         u"e69b733",
                                         # 2026-11-20: P-68(LX の便 = 文の字だけを読んだ LLM の席の答えで結んだ行を止める後付けの規則。封の commit)
                                         u"198961e",
                                         # 2026-11-21: P-69(CT0 の便 = 治験の公開データで、いまの engine の数の読み取りが英語の論文の要旨の数をどれだけ拾うか。封の commit)
                                         u"9e41971",
                                         # 2026-11-21(2): P-70(XG0 の便 = 有価証券報告書の計算書の行で、行の字と標準のラベルの表だけで要素が 1 つに決まる行はどれだけか。封の commit)
                                         u"3374e50",
                                         # 2026-11-21(3): P-71(XG1 の便 = 便 XG0 で候補が 2 つ以上だった行を、数を持てる要素・計算書の種類・業種の科目の一覧で絞ると、要素が 1 つに決まる行はどれだけ増えるか。封の commit)
                                         u"1bda199"]))
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
