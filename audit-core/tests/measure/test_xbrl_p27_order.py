# -*- coding: utf-8 -*-
"""封 docs/XBRL_P27_SEAL_2026-10-27.md §6(と段 1 の封 §4-4・§4-5)・§9-4 後半 ― P27 段 2 の**順序の門**。

順序は file の有無でなく、git の commit の順で示す。W・T・S2・E・R のそれぞれを git から求め(字で留めない)、祖先関係と、記録の中の commit と、凍結が保たれたことと、封を後から直していないことを見る。

- **commit の求め方**: 各 path について ``git log --diff-filter=A --format=%H -- <path>`` の行が**ちょうど 1 つ**(0 か 2 以上なら赤。消して足し直した履歴を許さない)。
  W = 評価用の文の凍結(reports の記録)・T = 調整用の診断の 3 つの記録(同じ commit)・S2 = 段 2 の封・R = 評価用の 3 つの記録(同じ commit)。
  E = ``git log --format=%H -S'PROFILES["P27E"]' -- adapters/xbrl/vocabulary.py`` の最も古い commit(P27E を足した engine の commit)。
- **祖先関係**: W ⊑ T ⊑ S2、S2 ⊏ E(S2 ≠ E)、E ⊑ R、R ⊑ HEAD。S2 の commit が engine(adapters・core)を 1 行も触っていない。
- **記録の中の commit**: R の 3 つの記録(R の blob)の「W の commit」「S2 の commit」「E の commit」が求めた値と同じで、「HEAD の commit」(測った時)が E の子孫。
- **凍結が保たれた**: W の記録は W から HEAD まで変わっていない。**封を後から直していない**: R より後に S2 の file を変えた commit は、どれも削除の行が 0(日付つきの追記だけ)。
- **門の変異**(この file の中で確かめる): 使い捨ての git repo(TMPDIR の下)に (1) S2 を W より前に足す、(2) R を E より前に足す、(3) S2 を R の後に書き換える(行を消す)、
  (4) W の記録を S2 の後に書き換える、(5) S2 を 2 回足す、を作り、判定の関数が赤になる(それぞれ特定の符号で)。順序が正しい repo では緑。

**この門は R が commit される前は赤になる**(R の記録がまだ追跡されていない: 「R が無い」)。R の中で初めて緑になる(前例 axis3 の test_9 と同じ扱い)。
この file は docID の字を持たない。評価用の文・DB の応答・束・理由は開かない(読むのは git の履歴と repo の記録だけ)。
"""
import collections
import json
import os
import re
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
E_PICKAXE = 'PROFILES["P27E"]'


class Cfg(object):
    """path の一覧(git の path。repo の root から)。本物は ``audit-core/`` の下、使い捨ての repo は prefix なし。"""

    def __init__(self, prefix):
        fx = prefix + "fixtures/xbrl/p27/"
        self.w = fx + "reports_2026-10-27.json"
        self.t = [fx + "tune_2026-10-27.json", fx + "tune_inject_2026-10-27.json", fx + "tune_readings_2026-10-27.json"]
        self.s2 = prefix + "docs/XBRL_P27_SEAL_2026-10-27.md"
        self.r = [fx + "eval_2026-10-27.json", fx + "eval_inject_2026-10-27.json", fx + "eval_readings_2026-10-27.json"]
        self.vocab = prefix + "adapters/xbrl/vocabulary.py"
        self.engine = [prefix + "adapters", prefix + "core"]


REAL = Cfg("audit-core/")
PLAIN = Cfg("")


def make_run(repo_dir):
    def run(*args):
        r = subprocess.run(["git", "-C", repo_dir] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r.returncode, r.stdout.decode("utf-8", "replace").strip()
    return run


def added_commits(run, path):
    rc, out = run("log", "--diff-filter=A", "--format=%H", "--", path)
    return [l for l in out.splitlines() if l.strip()] if rc == 0 else []


def is_anc(run, a, b):
    return a is not None and b is not None and run("merge-base", "--is-ancestor", a, b)[0] == 0


def find_commits(run, cfg):
    """(commit の辞書 W・T・S2・E・R(求まらなければ None), 問題の列 [(符号, 文)])。"""
    problems, out = [], {}
    for label, paths in (("W", [cfg.w]), ("T", cfg.t), ("S2", [cfg.s2]), ("R", cfg.r)):
        found, ok = set(), True
        for p in paths:
            lst = added_commits(run, p)
            if len(lst) != 1 or not HEX40.match(lst[0]):
                problems.append((label + "_ONCE", u"%s: %s を足した commit がちょうど 1 つに決まらない(%d 行)" % (label, os.path.basename(p), len(lst))))
                ok = False
            else:
                found.add(lst[0])
        if ok and len(found) != 1:
            problems.append((label + "_SAME", u"%s の記録が同じ commit に足されていない" % label))
            ok = False
        out[label] = sorted(found)[0] if ok else None
    rc, txt = run("log", "--format=%H", "-S" + E_PICKAXE, "--", cfg.vocab)
    lines = [l for l in txt.splitlines() if l.strip()]
    if rc != 0 or not lines or not HEX40.match(lines[-1]):
        problems.append(("E_NONE", u"P27E を足した engine の commit(E)が求まらない"))
        out["E"] = None
    else:
        out["E"] = lines[-1]
    return out, problems


def record_blobs(run, commit, paths):
    out = []
    for p in paths:
        rc, txt = run("show", "%s:%s" % (commit, p))
        if rc != 0:
            return None
        out.append(json.loads(txt))
    return out


def order_problems(run, cfg, head="HEAD"):
    """順序の門の判定。問題の列 [(符号, 文)](空なら通す)。"""
    c, problems = find_commits(run, cfg)
    W, T, S2, E, R = c["W"], c["T"], c["S2"], c["E"], c["R"]

    def need(code, ok, msg):
        if not ok:
            problems.append((code, msg))
    if W and T and not is_anc(run, W, T):
        problems.append(("W<=T", u"W が T の祖先でない"))
    if T and S2 and not is_anc(run, T, S2):
        problems.append(("T<=S2", u"T が S2 の祖先でない"))
    if S2 and E and not (S2 != E and is_anc(run, S2, E)):
        problems.append(("S2<E", u"S2 が E の真の祖先でない"))
    if E and R and not is_anc(run, E, R):
        problems.append(("E<=R", u"E が R の祖先でない"))
    if R and not is_anc(run, R, head):
        problems.append(("R<=HEAD", u"R が HEAD の祖先でない"))
    if S2:
        rc, parent = run("rev-parse", S2 + "^")
        base = parent if rc == 0 else EMPTY_TREE
        if run("diff", "--quiet", base, S2, "--", *cfg.engine)[0] != 0:
            problems.append(("S2_ENGINE", u"S2 の commit が engine(adapters・core)を触っている"))
    if R:
        recs = record_blobs(run, R, cfg.r)
        if recs is None:
            problems.append(("REC_READ", u"R の記録が R の blob から読めない"))
        else:
            for i, rec in enumerate(recs):
                for key, want in ((u"W の commit", W), (u"S2 の commit", S2), (u"E の commit", E)):
                    if want is None or rec.get(key) != want:
                        problems.append(("REC_COMMITS", u"R の記録 %d の「%s」が求めた commit と違う" % (i, key)))
                hd = rec.get(u"HEAD の commit")
                if not (isinstance(hd, str) and HEX40.match(hd) and is_anc(run, E, hd)):
                    problems.append(("REC_HEAD", u"R の記録 %d の「HEAD の commit」が E の子孫でない" % i))
    if W:
        if run("diff", "--quiet", W, head, "--", cfg.w)[0] != 0:
            problems.append(("W_FROZEN", u"W の記録が W の後に変わっている"))
    if R and S2:
        rc, txt = run("log", "--format=%H", "%s..%s" % (R, head), "--", cfg.s2)
        for h in [l for l in txt.splitlines() if l.strip()]:
            rc2, rc_parent = run("rev-parse", h + "^")
            base = rc_parent if rc2 == 0 else EMPTY_TREE
            rc3, num = run("diff", "--numstat", base, h, "--", cfg.s2)
            for line in num.splitlines():
                parts = line.split("\t")
                if len(parts) >= 2 and parts[1] != "0":
                    problems.append(("S2_REWRITE", u"R より後の commit %s が S2 の file の行を消している" % h[:7]))
    return problems


def codes(problems):
    return sorted(set(c for c, _m in problems))


# ======================================================================================================
# 使い捨ての git repo(変異用)
class Tmp(object):
    def __init__(self, base):
        self.dir = tempfile.mkdtemp(prefix="p27order_", dir=base)
        self.run = make_run(self.dir)
        self._g("init", "-q")
        self.h = {}

    def _g(self, *args):
        r = subprocess.run(["git", "-C", self.dir, "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"] + list(args),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert r.returncode == 0, (args, r.stderr[:300])
        return r.stdout.decode("utf-8").strip()

    def write(self, rel, text):
        p = os.path.join(self.dir, rel)
        d = os.path.dirname(p)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)

    def commit(self, msg, *paths):
        self._g("add", "--", *paths)
        self._g("commit", "-q", "-m", msg)
        return self._g("rev-parse", "HEAD")

    def head(self):
        return self._g("rev-parse", "HEAD")


def build(base, steps):
    """steps は 'W' 'T' 'S2' 'E' 'R' と変異の手('S2_REWRITE' 'S2_APPEND' 'W_REWRITE' 'S2_TWICE' 'S2E' 'S2_ENGINE')の並び。commit の順に作る。"""
    t = Tmp(base)
    cfg = PLAIN
    for step in steps:
        if step == "W":
            t.write(cfg.w, json.dumps({"会社": [1]}))
            t.h["W"] = t.commit("W", cfg.w)
        elif step == "T":
            for p in cfg.t:
                t.write(p, json.dumps({"k": p}))
            t.h["T"] = t.commit("T", *cfg.t)
        elif step == "S2":
            t.write(cfg.s2, u"# 封\n\n行 1\n行 2\n行 3\n")
            t.h["S2"] = t.commit("S2", cfg.s2)
        elif step == "E":
            t.write(cfg.vocab, u"PROFILES = {}\nPROFILES[\"P27E\"] = 1\n")
            t.write("core/x.py", u"x = 1\n")
            t.h["E"] = t.commit("E", cfg.vocab, "core/x.py")
        elif step == "R":
            hd = t.head()
            for p in cfg.r:
                t.write(p, json.dumps({u"W の commit": t.h.get("W", "0" * 40), u"S2 の commit": t.h.get("S2", "0" * 40),
                                      u"E の commit": t.h.get("E", "0" * 40), u"HEAD の commit": hd}))
            t.h["R"] = t.commit("R", *cfg.r)
        elif step == "S2_REWRITE":                      # R の後に S2 の file の行を消す
            t.write(cfg.s2, u"# 封\n\n行 1\n行 3\n")
            t.commit("S2 を書き換える", cfg.s2)
        elif step == "S2_APPEND":                       # 日付つきの追記(削除 0)は許される
            with open(os.path.join(t.dir, cfg.s2), "a", encoding="utf-8") as f:
                f.write(u"\n## 追記\n行 4\n")
            t.commit("S2 に追記", cfg.s2)
        elif step == "W_REWRITE":
            t.write(cfg.w, json.dumps({"会社": [2]}))
            t.commit("W の記録を書き換える", cfg.w)
        elif step == "S2_TWICE":                        # 消して足し直す
            t._g("rm", "-q", "--", cfg.s2)
            t._g("commit", "-q", "-m", "S2 を消す")
            t.write(cfg.s2, u"# 封\n\n行 1\n行 2\n行 3\n")
            t.commit("S2 を足し直す", cfg.s2)
        elif step == "S2E":                             # S2 と E が同じ commit(S2 が E の真の祖先でない)
            t.write(cfg.s2, u"# 封\n\n行 1\n行 2\n行 3\n")
            t.write(cfg.vocab, u"PROFILES = {}\nPROFILES[\"P27E\"] = 1\n")
            t.h["S2"] = t.h["E"] = t.commit("S2 と E", cfg.s2, cfg.vocab)
        elif step == "S2_ENGINE":                       # S2 の commit が engine を触る(別の手として S2 の代わりに使う)
            t.write(cfg.s2, u"# 封\n\n行 1\n行 2\n行 3\n")
            t.write("core/y.py", u"y = 1\n")
            t.h["S2"] = t.commit("S2 と engine", cfg.s2, "core/y.py")
        else:
            raise AssertionError(step)
    return t


# ======================================================================================================
class TestRealRepoOrder(unittest.TestCase):
    """本物の履歴。R の記録が commit される前は、R を求める試験が赤になる(R の中で初めて緑)。"""

    @classmethod
    def setUpClass(cls):
        cls.grun = staticmethod(make_run(REPO))
        cls.found, cls.found_problems = find_commits(cls.grun, REAL)

    def test_10_W_T_S2_E_are_each_determined_by_git(self):
        bad = [p for p in self.found_problems if p[0] in ("W_ONCE", "T_ONCE", "T_SAME", "S2_ONCE", "E_NONE")]
        self.assertEqual(bad, [])
        for k in ("W", "T", "S2", "E"):
            self.assertRegex(self.found[k], HEX40.pattern, k)
        self.assertEqual(len(set(self.found[k] for k in ("W", "T", "S2", "E"))), 4)

    def test_11_the_ancestry_W_T_S2_E_holds(self):
        f = self.found
        self.assertTrue(is_anc(self.grun, f["W"], f["T"]))
        self.assertTrue(is_anc(self.grun, f["T"], f["S2"]))
        self.assertTrue(f["S2"] != f["E"] and is_anc(self.grun, f["S2"], f["E"]))

    def test_12_S2_touched_no_engine(self):
        rc, parent = self.grun("rev-parse", self.found["S2"] + "^")
        self.assertEqual(rc, 0)
        self.assertEqual(self.grun("diff", "--quiet", parent, self.found["S2"], "--", *REAL.engine)[0], 0)

    def test_13_the_W_record_is_frozen(self):
        self.assertEqual(self.grun("diff", "--quiet", self.found["W"], "HEAD", "--", REAL.w)[0], 0)

    def test_14_R_is_determined_by_git_and_is_after_E_and_before_HEAD(self):
        """R が無ければ(R の記録が未追跡なら)ここが赤。R の中で初めて緑になる。"""
        bad = [p for p in self.found_problems if p[0] in ("R_ONCE", "R_SAME")]
        self.assertEqual(bad, [], u"R が無い(評価用の 3 つの記録が未追跡)か、同じ commit に足されていない")
        f = self.found
        self.assertTrue(is_anc(self.grun, f["E"], f["R"]))
        self.assertTrue(is_anc(self.grun, f["R"], "HEAD"))

    def test_15_the_records_inside_R_carry_the_commits_found(self):
        self.assertIsNotNone(self.found["R"], u"R が無い")
        self.assertEqual([p for p in order_problems(self.grun, REAL) if p[0] in ("REC_READ", "REC_COMMITS", "REC_HEAD")], [])

    def test_16_the_seal_was_not_rewritten_after_R(self):
        self.assertIsNotNone(self.found["R"], u"R が無い")
        self.assertEqual([p for p in order_problems(self.grun, REAL) if p[0] == "S2_REWRITE"], [])

    def test_17_the_whole_order_gate_has_no_problem(self):
        self.assertEqual(order_problems(self.grun, REAL), [])


class TestOrderGateMutations(unittest.TestCase):
    """門の変異(封 §6)。使い捨ての git repo で、順序が正しければ緑・5 つの違反はそれぞれ特定の符号で赤。"""

    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="p27order_root_")

    def _problems(self, steps):
        t = build(self.base, steps)
        return order_problems(t.run, PLAIN), t

    def test_20_a_correct_order_is_green(self):
        p, t = self._problems(["W", "T", "S2", "E", "R"])
        self.assertEqual(p, [])
        p, t = self._problems(["W", "T", "S2", "E", "R", "S2_APPEND"])          # 日付つきの追記(削除 0)は許される
        self.assertEqual(p, [])

    def test_21_missing_R_is_red(self):
        p, t = self._problems(["W", "T", "S2", "E"])
        self.assertIn("R_ONCE", codes(p))

    def test_22_mutation_1_S2_added_before_W_is_red(self):
        p, t = self._problems(["S2", "W", "T", "E", "R"])
        self.assertIn("T<=S2", codes(p))

    def test_23_mutation_2_R_added_before_E_is_red(self):
        p, t = self._problems(["W", "T", "S2", "R", "E"])
        self.assertIn("E<=R", codes(p))

    def test_24_mutation_3_S2_rewritten_after_R_is_red(self):
        p, t = self._problems(["W", "T", "S2", "E", "R", "S2_REWRITE"])
        self.assertIn("S2_REWRITE", codes(p))

    def test_25_mutation_4_W_record_rewritten_after_S2_is_red(self):
        p, t = self._problems(["W", "T", "S2", "W_REWRITE", "E", "R"])
        self.assertIn("W_FROZEN", codes(p))

    def test_26_mutation_5_S2_added_twice_is_red(self):
        p, t = self._problems(["W", "T", "S2", "S2_TWICE", "E", "R"])
        self.assertIn("S2_ONCE", codes(p))

    def test_27_S2_touching_the_engine_is_red(self):
        p, t = self._problems(["W", "T", "S2_ENGINE", "E", "R"])
        self.assertIn("S2_ENGINE", codes(p))

    def test_28_records_with_a_wrong_commit_are_red(self):
        t = build(self.base, ["W", "T", "S2", "E"])
        for rel in PLAIN.r:                                   # R の記録に別の S2 の commit を書く
            t.write(rel, json.dumps({u"W の commit": t.h["W"], u"S2 の commit": t.h["E"], u"E の commit": t.h["E"], u"HEAD の commit": t.head()}))
        t.commit("R", *PLAIN.r)
        self.assertIn("REC_COMMITS", codes(order_problems(t.run, PLAIN)))

    def test_29_a_measurement_HEAD_that_is_not_a_descendant_of_E_is_red(self):
        t = build(self.base, ["W", "T", "S2", "E"])
        for rel in PLAIN.r:
            t.write(rel, json.dumps({u"W の commit": t.h["W"], u"S2 の commit": t.h["S2"], u"E の commit": t.h["E"], u"HEAD の commit": t.h["S2"]}))
        t.commit("R", *PLAIN.r)
        self.assertIn("REC_HEAD", codes(order_problems(t.run, PLAIN)))

    def test_30_the_three_records_added_in_different_commits_are_red(self):
        t = build(self.base, ["W", "T", "S2", "E"])
        hd = t.head()
        for i, rel in enumerate(PLAIN.r):
            t.write(rel, json.dumps({u"W の commit": t.h["W"], u"S2 の commit": t.h["S2"], u"E の commit": t.h["E"], u"HEAD の commit": hd}))
            t.commit("R%d" % i, rel)
        self.assertIn("R_SAME", codes(order_problems(t.run, PLAIN)))

    def test_32_S2_and_E_in_the_same_commit_are_red(self):
        p, t = self._problems(["W", "T", "S2E", "R"])
        self.assertIn("S2<E", codes(p))

    def test_33_R_that_is_not_an_ancestor_of_the_head_is_red(self):
        t = build(self.base, ["W", "T", "S2", "E", "R"])
        self.assertEqual(order_problems(t.run, PLAIN), [])
        self.assertIn("R<=HEAD", codes(order_problems(t.run, PLAIN, head=t.h["E"])))

    def test_31_E_is_the_oldest_commit_that_added_the_string(self):
        t = build(self.base, ["W", "T", "S2", "E"])
        t.write(PLAIN.vocab, u"PROFILES = {}\n")                       # 消す
        t.commit("消す", PLAIN.vocab)
        t.write(PLAIN.vocab, u"PROFILES = {}\nPROFILES[\"P27E\"] = 2\n")       # 足し直す
        t.commit("足し直す", PLAIN.vocab)
        c, _p = find_commits(t.run, PLAIN)
        self.assertEqual(c["E"], t.h["E"])


if __name__ == "__main__":
    unittest.main()
