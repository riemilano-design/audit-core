# -*- coding: utf-8 -*-
u"""門: README.en.md の入口の字を 2 か所直した便(封 docs/README_FIX_SEAL_2026-11-02.md)。

縛る物:
- 封 §0-1・§0-2 に固定した字が README.en.md に**そのまま**在ること(封の字は封の file から読む。写しを門に持たない)。
- その字の中の事実(例外の名・OS・setuptools・Python の版・rc)が 11-02 の記録 fixtures/readme_cacheless_2026-11-02.json の欄と合うこと。
- 封の commit の README と木の README の差分が、2 節と試験 file の本数の行に限ること。儀式の節(## 10-minute reproduction)は同じこと。
- 禁止語 0・英語だけ(test_packaging の G-6 と同じ字)。
- 封の §0〜§3 が封の commit から変わっていないこと(追記は §4 以降)。
- 順序: 封の commit がこの門より先。
- 変異で赤くなること。
"""
from __future__ import print_function

import difflib
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

SEAL_REL = "docs/README_FIX_SEAL_2026-11-02.md"
README_REL = "README.en.md"
REC_REL = "fixtures/readme_cacheless_2026-11-02.json"
GATE_REL = "tests/measure/test_readme_fix.py"
SEAL_COMMIT_SHORT = "6cde4b3"
SEAL, README, REC = (os.path.join(ROOT, r) for r in (SEAL_REL, README_REL, REC_REL))

RITUAL_HEAD = u"## 10-minute reproduction"
FIX_HEADS = (u"## Check your own filing's text", u"## Install")
FORBIDDEN_WORDS = ("accurate", "world's first", "only", "unique", "guarantee")
ADDENDUM_HEAD = u"## §4"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def quotes(seal):
    u"""封の `> ` 引用の段落(改行で区切る)を順に返す。0-1: [旧 1 文, 新 3 文]、0-2: [旧段落, 新段落]。"""
    out, cur = [], []
    for l in seal.splitlines():
        if l.startswith(u"> "):
            cur.append(l[2:].rstrip())
        elif cur:
            out.append(u" ".join(cur))
            cur = []
    if cur:
        out.append(u" ".join(cur))
    return out


def flat(t):
    return re.sub(r"\s+", u" ", t).strip()


def section(text, head):
    i = text.index(head)
    j = text.find(u"\n## ", i + 1)
    return text[i:] if j < 0 else text[i:j]


def heads_of_diff(old, new):
    u"""差分の行(+/−)が属する節の見出しの集合(旧・新それぞれの文脈で引く)。"""
    def owner(lines, idx):
        for k in range(idx, -1, -1):
            if lines[k].startswith(u"## "):
                return lines[k]
        return u"(先頭)"
    sm = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    heads, changed = set(), []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        for i in range(i1, i2):
            heads.add(owner(old, i)); changed.append(u"-" + old[i])
        for j in range(j1, j2):
            heads.add(owner(new, j)); changed.append(u"+" + new[j])
    return heads, changed


def seal_commit_readme():
    rc, out = git("show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, README_REL))
    return out if rc == 0 else None


class FixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = jtext(SEAL)
        cls.readme = jtext(README)
        cls.rec = jload(REC)
        cls.q = quotes(cls.seal)

    def test_a_1_seal_quotes_are_four_and_the_new_text_is_in_the_readme_verbatim(self):
        self.assertEqual(len(self.q), 4, self.q)
        old1, new1, old2, new2 = self.q
        r = flat(self.readme)
        self.assertNotIn(flat(old1), r, u"直す前の 1 文がまだ在る")
        self.assertIn(flat(new1), r, u"0-1 の新しい字が README に無い")
        self.assertIn(flat(new2), r, u"0-2 の新しい段落が README に無い")
        self.assertIn(u"both worked on that machine.", r)
        self.assertNotIn(u"both work.", r)
        # 0-1 は節「Check your own filing's text」に、0-2 は節「Install」に在る
        self.assertIn(flat(new1), flat(section(self.readme, FIX_HEADS[0])))
        self.assertIn(flat(new2), flat(section(self.readme, FIX_HEADS[1])))

    def test_a_2_facts_in_the_new_text_match_the_record(self):
        rec = self.rec
        env = rec[u"環境"]
        r3 = rec[u"3 verify_document"]
        r5 = rec[u"5 install"]
        new1, new2 = self.q[1], self.q[3]
        # 0-1: FileNotFoundError・何も書かない・rc=1
        self.assertTrue(r3[u"text あり"][u"例外の行"].startswith(u"FileNotFoundError"))
        self.assertTrue(r3[u"text なし"][u"例外の行"].startswith(u"FileNotFoundError"))
        self.assertIn(u"`FileNotFoundError`", new1)
        self.assertEqual((r3[u"text あり"][u"rc"], r3[u"text なし"][u"rc"]), (1, 1))
        self.assertFalse(r3[u"text あり"][u"out.json が在る"] or r3[u"text なし"][u"out.json が在る"])
        self.assertIn(u"before writing anything", new1)
        self.assertFalse(rec[u"4 report_customer(ラベル dir 無し)"][u"report.md が在る"], u"R-4 で報告が書かれていたら『未測』は嘘")
        self.assertIn(u"was not measured in that run", new1)
        # 0-2: OS・setuptools・python・例外・rc
        self.assertTrue(env[u"OS"].startswith(u"Ubuntu 24.04"), env[u"OS"])
        self.assertIn(u"Ubuntu 24.04", new2)
        self.assertEqual(env[u"setuptools"], u"68.1.2"); self.assertIn(u"68.1.2", new2)
        self.assertEqual(env[u"python"], u"3.13.18"); self.assertIn(u"3.13.18", new2)
        self.assertIn(u"dist-packages", env[u"setuptools の置き場"])
        ne, ed = r5[u"非 editable"], r5[u"editable"]
        self.assertEqual(ne[u"install rc"], 1)
        self.assertTrue(ne[u"install の例外の行"].startswith(u"AttributeError: install_layout"))
        self.assertIn(u"`AttributeError: install_layout`", new2)
        self.assertEqual((ed[u"install rc"], ed[u"combined import rc"]), (0, 0))
        self.assertIn(u"editable install plus the combined import both worked", new2)

    def test_b_1_diff_since_seal_is_confined_to_the_two_sections_and_the_count_line(self):
        old = seal_commit_readme()
        if old is None:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        heads, changed = heads_of_diff(old.splitlines(), self.readme.splitlines())
        allowed = set(FIX_HEADS) | {u"## Test suite"}
        self.assertTrue(all(any(h.startswith(a) for a in allowed) for h in heads), (heads, changed[:6]))
        for l in changed:
            if l[1:].strip() and not any(l[1:].startswith(a[3:]) for a in allowed):
                self.assertTrue(u"test files" in l or l[0] in u"+-", l)
        stray = [l for l in changed if l[1:].startswith(u"- **") or re.search(r"\d+/\d+", l)]
        self.assertEqual([l for l in stray if u"test files" not in l], [], u"数の bullet が変わった")
        self.assertEqual(section(old, RITUAL_HEAD), section(self.readme, RITUAL_HEAD), u"儀式の節が変わった")

    def test_b_2_line_count_delta_is_the_measured_plus_six(self):
        u"""封 F-4 は +2〜+4 と見立てたが、実測は **+6**(足した段落が折り返しで 5 行 + 空行 1)。**外れ**(封 §4 の追記)。
        門は実測の値を縛る(見立てに合わせて折り返しを変えない)。"""
        old = seal_commit_readme()
        if old is None:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        d = self.readme.count(u"\n") - old.count(u"\n")
        self.assertEqual(d, 6, d)

    def test_c_1_english_only_and_no_forbidden_words(self):
        self.assertNotRegex(self.readme, r"[぀-ヿ一-鿿]")
        low = self.readme.lower()
        for w in FORBIDDEN_WORDS:
            self.assertNotIn(w, low, w)

    def test_d_1_seal_body_unchanged_since_its_commit(self):
        rc, committed = git("show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL))
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)

        def body(t):
            return (t[:t.index(ADDENDUM_HEAD)] if ADDENDUM_HEAD in t else t).rstrip()
        self.assertEqual(body(committed), body(self.seal), u"**封の §0〜§3 が後で変わっている**(追記は §4 以降に)")

    def test_e_1_order_seal_before_gate(self):
        rc, out = git("log", "--diff-filter=A", "--format=%H", "--", PREFIX + SEAL_REL)
        s = [l for l in out.split() if l]
        if rc != 0 or not s:
            self.skipTest(u"封の commit が履歴に無い")
        self.assertEqual(len(s), 1); self.assertTrue(s[0].startswith(SEAL_COMMIT_SHORT))
        rc, out = git("log", "--diff-filter=A", "--format=%H", "--", PREFIX + GATE_REL)
        g = [l for l in out.split() if l]
        self.assertTrue(g, u"この門を足した commit が無い(未 commit)")
        self.assertNotEqual(g[-1], s[0])
        self.assertEqual(git("merge-base", "--is-ancestor", s[0], g[-1])[0], 0, u"門が封の後でない")


class MutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = jtext(SEAL)
        cls.readme = jtext(README)
        cls.q = quotes(cls.seal)

    def test_m_1_dropping_a_word_from_the_new_text_is_caught(self):
        bad = self.readme.replace(u"before writing anything", u"before writing")
        self.assertNotEqual(bad, self.readme)
        self.assertNotIn(flat(self.q[1]), flat(bad))

    def test_m_2_restoring_the_old_sentence_is_caught(self):
        bad = self.readme.replace(flat(self.q[1]), self.q[0])
        self.assertIn(flat(self.q[0]), flat(bad))

    def test_m_3_a_forbidden_word_is_caught(self):
        bad = self.readme + u"\nThis is the only engine.\n"
        self.assertTrue(any(w in bad.lower() for w in FORBIDDEN_WORDS))

    def test_m_4_a_change_in_the_ritual_section_is_caught(self):
        old = seal_commit_readme()
        if old is None:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        bad = self.readme.replace(u"Run time 22.8 seconds", u"Run time 22.9 seconds")
        self.assertNotEqual(bad, self.readme)
        heads, _ = heads_of_diff(old.splitlines(), bad.splitlines())
        self.assertTrue(any(h.startswith(RITUAL_HEAD) for h in heads))
        self.assertNotEqual(section(old, RITUAL_HEAD), section(bad, RITUAL_HEAD))

    def test_m_5_a_changed_version_number_is_caught(self):
        bad = self.q[3].replace(u"68.1.2", u"68.1.3")
        self.assertNotIn(u"68.1.2", bad)


if __name__ == "__main__":
    unittest.main()
