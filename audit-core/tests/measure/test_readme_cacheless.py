# -*- coding: utf-8 -*-
u"""門: cache の無い clone で README.en.md の手順が字どおりに動くか(封 docs/README_CACHELESS_SEAL_2026-11-02.md)。

縛る物:
- 記録 fixtures/readme_cacheless_2026-11-02.json の形(封・HEAD・script の sha256・key_leaks)。
- 予測 R-1〜R-7 の当たり / 外れを、記録の生の欄と封 §1 の幅から**ここで求め直し**、記録の「予測の判定」と結果の文書 §1 の表に一致させる。
- 結果の文書の数(表の実測の欄・散文の 3 桁以上の数)が記録に在ること(無い数は【門なし】を付ける)。
- 封が結果の後で変わっていないこと(封の commit と木が同じ)。README.en.md の 3 節が封の commit から変わっていないこと(変わってよいのは試験 file の本数の行だけ)。
- script が標準ライブラリだけで engine を import しないこと。
- 順序: 封の commit が script・記録・文書・この門より先(git)。
- 変異(in-memory)で赤くなること。
"""
from __future__ import print_function

import ast
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"

SEAL_REL = "docs/README_CACHELESS_SEAL_2026-11-02.md"
DOC_REL = "docs/README_CACHELESS_RESULT_2026-11-02.md"
REC_REL = "fixtures/readme_cacheless_2026-11-02.json"
SCRIPT_REL = "measure/readme_cacheless_2026-11-02.py"
GATE_REL = "tests/measure/test_readme_cacheless.py"
README_REL = "README.en.md"
SEAL_COMMIT_SHORT = "443a078"

SEAL, DOC, REC, SCRIPT, README = (os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL, README_REL))

IDS = tuple(u"R-%d" % i for i in range(1, 8))
K1, K2, K3, K4, K5, K6, K7 = (u"1 儀式(ラベル無し)", u"2 ラベルの名簿", u"3 verify_document", u"4 report_customer(ラベル dir 無し)",
                              u"5 install", u"6 壁時計の合計(秒)", u"7 README の字")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
NOT_GATED = u"【門なし】"
ALLOWED_IMPORTS = {"argparse", "ast", "hashlib", "io", "json", "os", "platform", "re", "shutil", "subprocess", "sys", "tempfile", "time",
                   "__future__"}
FORBIDDEN = (u"accurate", u"world's first", u"guarantee", u"正確", u"世界初", u"保証")


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.returncode, r.stdout.decode("utf-8", "replace").strip()


# ---------------------------------------------------------------- 封 §1 の幅(字から読む)

def seal_rows(seal):
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(R-\d+)\*\* \| (.*)$", l)
        if m:
            body = m.group(2).rstrip()
            if body.endswith(u"|"):
                body = body[:-1].rstrip()
            cells = [c.strip() for c in body.split(u" | ")]
            out[m.group(1)] = tuple(cells)
    return out


def num(s):
    return int(s.replace(u",", u""))


def seal_bounds(seal):
    u"""ref_judge が使う幅を封の字から取る(封を書き換えたら ref と食い違って赤)。"""
    rows = seal_rows(seal)
    b = {}
    m = re.search(r"\*\*([\d,]+) 以上 ([\d,]+) 未満\*\*", rows[u"R-2"][0])
    b[u"bytes"] = (num(m.group(1)), num(m.group(2)))
    b[u"labels_required"] = num(re.search(r"\*\*(\d+) 本\*\*", rows[u"R-2"][0]).group(1))
    b[u"roster"] = num(re.search(r"名簿 `taxonomy_labels_sha256.txt` は \*\*(\d+) 本\*\*", rows[u"R-2"][0]).group(1))
    b[u"claims_text"] = num(re.search(r"`document.claims` は \*\*(\d+)\*\*", rows[u"R-3"][0]).group(1))
    b[u"claims_notext_min"] = num(re.search(r"\*\*(\d+) 以上\*\*", rows[u"R-3"][0]).group(1))
    b[u"element_rows_min"] = num(re.search(r"\*\*(\d+) 行以上\*\*", rows[u"R-4"][0]).group(1))
    b[u"seconds_max"] = num(re.search(r"\*\*(\d+) 秒以下\*\*", rows[u"R-6"][0]).group(1))
    b[u"readme_phrases"] = num(re.search(r"\*\*(\d+) つとも\*\*", rows[u"R-7"][0]).group(1))
    return b


# ---------------------------------------------------------------- 判定の求め直し

def ref_judge(rec, b):
    r1, r2, r3, r4, r5, r7 = rec[K1], rec[K2], rec[K3], rec[K4], rec[K5], rec[K7]
    j = collections.OrderedDict()
    j[u"R-1"] = r1[u"rc"] == 2 and r1[u"案内に TAXONOMY_LABELS_README.md"] and r1[u"案内に EDINET_TAXONOMY_DIR"] and r1[u"out dir の file 数"] == 0
    j[u"R-2"] = (r2[u"儀式が要求する本数"] == b[u"labels_required"] and r2[u"README.en.md の字"][u"本数の語"] == "two"
                 and r2[u"名簿の本数"] == b[u"roster"] and r2[u"sha256 が 3 か所で同じ本数"] == b[u"labels_required"]
                 and b[u"bytes"][0] <= r2[u"要求 2 本のバイト数の合計"] < b[u"bytes"][1])
    a, c = r3[u"text あり"], r3[u"text なし"]
    j[u"R-3"] = a[u"rc"] == 0 and a.get(u"claims") == b[u"claims_text"] and c[u"rc"] == 0 and (c.get(u"claims") or 0) >= b[u"claims_notext_min"]
    j[u"R-4"] = (r4[u"rc"] == 0 and r4[u"report.md が在る"] and r4[u"report.provenance.json が在る"]
                 and r4.get(u"要素名の形が出る行の数", 0) >= b[u"element_rows_min"])
    ne, ed = r5[u"非 editable"], r5[u"editable"]
    j[u"R-5"] = (ne[u"install rc"] == 0 and ne[u"combined import rc"] == 0 and all(h[u"rc"] == 0 for h in ne[u"--help"].values())
                 and ed[u"install rc"] == 0 and ed[u"combined import rc"] == 0)
    j[u"R-6"] = rec[K6] <= b[u"seconds_max"]
    j[u"R-7"] = r7[u"一致した数"] == b[u"readme_phrases"]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in j.items())
    out[u"当たり"] = sum(1 for v in j.values() if v)
    out[u"外れ"] = sum(1 for v in j.values() if not v)
    return out


def ref_readme_match_count(r7):
    return sum(1 for k, v in r7.items() if isinstance(v, dict) and v[u"一致"])


# ---------------------------------------------------------------- 結果の文書

def doc_rows(doc):
    out = collections.OrderedDict()
    for l in doc.splitlines():
        m = re.match(r"^\| \*\*(R-\d+)\*\* \| (.*)\|\s*$", l)
        if m:
            cells = [c.strip() for c in m.group(2).split(u" | ")]
            out[m.group(1)] = tuple(cells)
    return out


def expected_substrings(rec):
    u"""表の実測の欄に在るべき字(記録から作る)。"""
    r1, r2, r3, r5, r7 = rec[K1], rec[K2], rec[K3], rec[K5], rec[K7]
    ne, ed = r5[u"非 editable"], r5[u"editable"]
    helps = sorted(set(h[u"rc"] for h in ne[u"--help"].values()))
    return {
        u"R-1": [u"rc=%d" % r1[u"rc"], u"file %d" % r1[u"out dir の file 数"]],
        u"R-2": [u"要求 %d 本" % r2[u"儀式が要求する本数"], u"「%s」" % r2[u"README.en.md の字"][u"本数の語"], u"名簿 %d 本" % r2[u"名簿の本数"],
                 u"同じ本数 %d" % r2[u"sha256 が 3 か所で同じ本数"], u"{:,} バイト".format(r2[u"要求 2 本のバイト数の合計"])],
        u"R-3": [u"あり rc=%d" % r3[u"text あり"][u"rc"], u"無し rc=%d" % r3[u"text なし"][u"rc"]],
        u"R-4": [u"rc=%d" % rec[K4][u"rc"]],
        u"R-5": [u"install **rc=%d**" % ne[u"install rc"], u"import rc=%d" % ne[u"combined import rc"]]
                + [u"rc=%d" % h for h in helps] + [u"install rc=%d" % ed[u"install rc"], u"import **rc=%d**" % ed[u"combined import rc"]],
        u"R-6": [u"%s 秒" % rec[K6]],
        u"R-7": [u"一致 %d" % r7[u"一致した数"]],
    }


def table_problems(doc, rec, judged):
    p = []
    rows = doc_rows(doc)
    if tuple(rows.keys()) != IDS:
        return [u"表の行が R-1〜R-7 でない: %s" % list(rows.keys())]
    exp = expected_substrings(rec)
    for i in IDS:
        cells = rows[i]
        if len(cells) != 3:
            p.append(u"%s の欄が 3 でない" % i)
            continue
        if cells[2] != u"**%s**" % judged[i]:
            p.append(u"%s の判定が %s でない" % (i, judged[i]))
        for s in exp[i]:
            if s not in cells[1]:
                p.append(u"%s の実測の欄に %s が無い" % (i, s))
    head = doc.splitlines()[0]
    if u"当たり %d / 外れ %d" % (judged[u"当たり"], judged[u"外れ"]) not in head:
        p.append(u"見出しの当たり / 外れの数")
    misses = [i for i in IDS if judged[i] == u"外れ"]
    if u"(%s)" % u"・".join(misses) not in head:
        p.append(u"見出しの外れの ID")
    return p


def prose_problems(doc, rec_text):
    u"""表・見出し以外の行で、3 桁以上の数は記録の字に在るか、行に【門なし】が在ること。禁止語。"""
    p = []
    for ln in doc.splitlines():
        if ln.startswith(u"|") or ln.startswith(u"#") or not ln.strip():
            continue
        s = re.sub(r"`[^`]*`", u" ", ln)
        s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
        s = re.sub(r"R-\d+|§\d+(-\d+)*", u" ", s)
        for n in re.findall(r"\d[\d,.]*\d|\d", s):
            flat = n.replace(u",", u"")
            if len(re.sub(r"\D", u"", flat)) >= 3 and NOT_GATED not in ln and n not in rec_text and flat not in rec_text:
                p.append(u"%s … %s" % (n, ln[:50]))
    for w in FORBIDDEN:
        if w in doc:
            p.append(u"禁止語 %s" % w)
    return p


# ---------------------------------------------------------------- script の純度

def script_problems(src):
    p = []
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS:
                    p.append(u"import %s" % a.name)
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                p.append(u"from %s import" % node.module)
    for bad in ("adapters", "audit_core", "urllib", "http", "socket", "zipfile"):
        if re.search(r"^\s*(import|from)\s+%s\b" % bad, src, re.M):
            p.append(u"%s を import" % bad)
    return p


# ---------------------------------------------------------------- git

def added_commits(path):
    rc, out = git("log", "--diff-filter=A", "--format=%H", "--", path)
    return [l for l in out.splitlines() if l.strip()] if rc == 0 else []


def is_anc(a, b):
    return a is not None and b is not None and git("merge-base", "--is-ancestor", a, b)[0] == 0


def order_problems():
    p = []
    s = added_commits(PREFIX + SEAL_REL)
    if len(s) != 1 or not HEX40.match(s[0]):
        return [u"封を足した commit がちょうど 1 つに決まらない(%d)" % len(s)]
    S = s[0]
    if not S.startswith(SEAL_COMMIT_SHORT):
        p.append(u"封の commit が %s でない" % SEAL_COMMIT_SHORT)
    if not is_anc(S, "HEAD"):
        p.append(u"封の commit が HEAD の祖先でない")
    for rel in (SCRIPT_REL, REC_REL, DOC_REL, GATE_REL):
        a = added_commits(PREFIX + rel)
        if not a:
            p.append(u"%s を足した commit が無い(未 commit)" % rel)
            continue
        A = a[-1]
        if A == S or not is_anc(S, A):
            p.append(u"%s が封の後でない" % rel)
    return p


def readme_diff_lines():
    u"""封の commit の README と木の README の違う行(空なら同じ)。"""
    rc, old = git("show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, README_REL))
    if rc != 0:
        return None
    new = jtext(README).rstrip("\n").splitlines()
    old = old.splitlines()
    import difflib
    return [l for l in difflib.unified_diff(old, new, lineterm=u"", n=0) if (l.startswith(u"+") or l.startswith(u"-")) and not l.startswith((u"+++", u"---"))]


def load_script():
    spec = importlib.util.spec_from_file_location("readme_cacheless_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ================================================================ tests

class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.rec_text = json.dumps(cls.rec, ensure_ascii=False)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)
        cls.bounds = seal_bounds(cls.seal)

    def test_a_1_keys_and_constants(self):
        for k in (u"注意", u"封", u"HEAD の commit", u"この script の sha256", u"環境", u"固定した 1 文", K1, K2, K3, K4, K5, K6, K7,
                  u"予測の判定", u"木に出た生成物(消した)", u"key_leaks"):
            self.assertIn(k, self.rec)
        self.assertEqual(self.rec[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        self.assertTrue(self.rec[u"HEAD の commit"].startswith(SEAL_COMMIT_SHORT), u"記録の HEAD が封の commit でない(封 → 実測の順)")
        self.assertEqual(self.rec[u"key_leaks"], [])
        for n in self.rec[u"木に出た生成物(消した)"]:
            self.assertTrue(n == "build" or n.endswith(".egg-info"), n)
            self.assertFalse(os.path.exists(os.path.join(ROOT, n)), u"%s が木に残っている" % n)
        with io.open(SCRIPT, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), self.rec[u"この script の sha256"])
        self.assertFalse(self.rec[u"環境"][u"cache dir が在る"], u"cache が在る機械の記録(封の条件の外)")
        self.assertIsNone(self.rec[u"環境"][u"EDINET_TAXONOMY_DIR"])
        self.assertEqual(self.rec_text.count("scratchpad"), 0, u"--work の絶対パスが記録に残っている")

    def test_b_1_judgement_recomputed(self):
        self.assertEqual(dict(ref_judge(self.rec, self.bounds)), self.rec[u"予測の判定"])
        self.assertEqual(ref_readme_match_count(self.rec[K7]), self.rec[K7][u"一致した数"])
        self.assertEqual(self.rec[u"予測の判定"][u"当たり"] + self.rec[u"予測の判定"][u"外れ"], 7)

    def test_c_1_doc_table_matches_record(self):
        self.assertEqual(table_problems(self.doc, self.rec, self.rec[u"予測の判定"]), [])

    def test_c_2_doc_prose_numbers_are_in_the_record_or_marked(self):
        self.assertEqual(prose_problems(self.doc, self.rec_text), [])

    def test_c_3_doc_names_no_docid(self):
        for p in (SEAL, DOC, REC, SCRIPT, __file__):
            self.assertEqual(DOCID_RE.findall(jtext(p)), [], p)

    def test_d_1_seal_has_seven_rows_each_with_a_way_to_fail(self):
        rows = seal_rows(self.seal)
        self.assertEqual(tuple(rows.keys()), IDS)
        for i, cells in rows.items():
            self.assertEqual(len(cells), 2, i)
            self.assertTrue(cells[1].strip(), u"%s に外れ方が無い" % i)

    def test_d_2_seal_unchanged_since_its_commit(self):
        rc, committed = git("show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL))
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(committed.rstrip(u"\n"), self.seal.rstrip(u"\n"), u"**封が結果の後で変わっている**")

    def test_e_1_readme_three_sections_unchanged_since_seal(self):
        d = readme_diff_lines()
        if d is None:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        stray = [l for l in d if u"test files" not in l]
        self.assertEqual(stray, [], u"README.en.md が封の後で変わった(許すのは試験 file の本数の行だけ)")

    def test_f_1_script_is_stdlib_only_and_matches_record(self):
        self.assertEqual(script_problems(jtext(SCRIPT)), [])
        mod = load_script()
        self.assertEqual(mod.SEAL_COMMIT, SEAL_COMMIT_SHORT)
        self.assertEqual(mod.SENTENCE, self.rec[u"固定した 1 文"])
        self.assertEqual(mod.judge(self.rec), self.rec[u"予測の判定"])
        # ラベルの名簿(読むだけ)は何度走らせても同じ
        self.assertEqual(mod.item_2_labels(), self.rec[K2])

    def test_g_1_seal_bounds_are_the_sealed_ones(self):
        self.assertEqual(self.bounds, {u"bytes": (8000000, 9000000), u"labels_required": 2, u"roster": 3, u"claims_text": 1,
                                       u"claims_notext_min": 200, u"element_rows_min": 1, u"seconds_max": 600, u"readme_phrases": 4})

    def test_i_1_order(self):
        u"""封の commit < script・記録・文書・門(新 4 file が未 commit の間は赤)。"""
        rc, _ = git("cat-file", "-e", SEAL_COMMIT_SHORT + "^{commit}")
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(order_problems(), [])


class MutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.rec_text = json.dumps(cls.rec, ensure_ascii=False)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)
        cls.bounds = seal_bounds(cls.seal)

    def test_m_1_flipping_a_recorded_judgement_is_caught(self):
        rec = json.loads(self.rec_text)
        rec[u"予測の判定"][u"R-3"] = u"当たり"
        self.assertNotEqual(dict(ref_judge(rec, self.bounds)), rec[u"予測の判定"])

    def test_m_2_changing_a_raw_field_is_caught(self):
        rec = json.loads(self.rec_text)
        rec[K1][u"rc"] = 0
        self.assertNotEqual(dict(ref_judge(rec, self.bounds)), rec[u"予測の判定"])

    def test_m_3_swapping_a_doc_verdict_is_caught(self):
        bad = self.doc.replace(u"| **外れ** |", u"| **当たり** |", 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec, self.rec[u"予測の判定"]), [])

    def test_m_4_changing_a_doc_number_is_caught(self):
        s = u"{:,} バイト".format(self.rec[K2][u"要求 2 本のバイト数の合計"])
        bad = self.doc.replace(s, u"8,362,743 バイト")
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec, self.rec[u"予測の判定"]), [])

    def test_m_5_unbound_three_digit_number_in_prose_is_caught(self):
        bad = self.doc + u"\n記録に無い数 987654 を書いた行。\n"
        self.assertNotEqual(prose_problems(bad, self.rec_text), [])

    def test_m_6_engine_import_in_script_is_caught(self):
        src = jtext(SCRIPT) + u"\nimport adapters.xbrl.instance\n"
        self.assertNotEqual(script_problems(src), [])

    def test_m_7_changing_a_seal_bound_changes_the_reference(self):
        bad = self.seal.replace(u"**600 秒以下**", u"**5 秒以下**")
        self.assertNotEqual(bad, self.seal)
        self.assertNotEqual(dict(ref_judge(self.rec, seal_bounds(bad))), self.rec[u"予測の判定"])

    def test_m_8_dropping_a_seal_row_is_caught(self):
        bad = u"\n".join(l for l in self.seal.splitlines() if not l.startswith(u"| **R-7**"))
        self.assertNotEqual(tuple(seal_rows(bad).keys()), IDS)


if __name__ == "__main__":
    unittest.main()
