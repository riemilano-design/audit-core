# -*- coding: utf-8 -*-
"""評価用の測定 script(measure/xbrl_p27_eval_2026-10-27.py)の試験(封 docs/XBRL_P27_SEAL_2026-10-27.md §7・§6・§3-2・§4・§9-4 前半)。
**作り物だけで経路を通す。** 本物の評価用の文・DB の応答・prompts は開かない(使い捨ての folder に偽の文・偽の記録・偽の ZIP を置く)。
通信しない・鍵を使わない・本物の cache に書かない。git の呼び出しは同じ形の関数に差し替える(各条件が単独で止めることを見る)。

偽の docID は実在の書類番号の接頭辞を使わず、部品から組む(引きの門 test_xbrl_fresh_seal test_23 が追跡 file の docID を数える)。
**「X を開かない」を試す試験は、先に置き場を使い捨ての folder に向け、open を数え、さらに読めない権限にして、開けば別の例外が出る形で見る。**"""
import ast
import builtins
import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.environ.get("P27_EVAL_SCRIPT", os.path.join(ROOT, "measure", "xbrl_p27_eval_2026-10-27.py"))
REAL_BASE = os.path.expanduser("~/.cache/audit-core")
REAL_DIRS = [os.path.join(REAL_BASE, "edinet"), os.path.join(REAL_BASE, "edinet-fresh-2026-10-21"), os.path.join(REAL_BASE, "edinetdb-p27")]

spec = importlib.util.spec_from_file_location("p27_eval", SCRIPT)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

FAKE_KEY = "".join(["Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7", "cF0xR"])
SENTINEL = u"印字印"                                  # 文の中の字(span に入る。repo の記録にも標準出力にも出てはならない)
SENTINEL_DB = u"秘密の会社名テスト"
SENTINEL_REASON = u"理由の自由文テスト一"

DOC_PREFIX = "ZZ0"
TUNE = [DOC_PREFIX + "TUN01", DOC_PREFIX + "TUN02"]
EVAL = [DOC_PREFIX + "EVA01", DOC_PREFIX + "EVA02", DOC_PREFIX + "EVA03"]
STYLE = {TUNE[0]: "A", TUNE[1]: "B", EVAL[0]: "A", EVAL[1]: "B", EVAL[2]: "C"}

H = lambda c: (c * 40)[:40]            # noqa: E731
GIT = {"HEAD": H("a"), "W": H("1"), "T": H("2"), "S2": H("3"), "E": H("4")}
FAKE_VOCAB = types.SimpleNamespace(PROFILES={"P22": 1, "P26": 1, "P27": 1, "P27E": 1}, DEFAULT_PROFILE="P26")


def _listing(folder):
    return sorted(os.listdir(folder)) if os.path.isdir(folder) else None


_BEFORE = {}


def setUpModule():
    for d in REAL_DIRS:
        _BEFORE[d] = _listing(d)


def tearDownModule():
    for d in REAL_DIRS:
        assert _listing(d) == _BEFORE[d], "本物の cache が試験で変わった: %s" % d


def sha(b):
    return M.sha256_hex(b)


def fact(name, ctx, value, unit="JPY"):
    return {"name": name, "context": ctx, "unit": unit, "decimals": "-6", "value": value}


SMALL_FACTS = [fact("jppfs_cor:NetSales", "CurrentYearDuration", 5000000000.0),
               fact("jppfs_cor:NetSales", "Prior1YearDuration", 2000000000.0),
               fact("jppfs_cor:OperatingIncome", "CurrentYearDuration", 430000000.0),
               fact("jppfs_cor:TotalAssets", "CurrentYearInstant", 1200000000.0)]
# 一致が 5 つ(50・20・4.3・1,200百万・来期の 50)。999 億円は遠い fact だけ。52 億円は 50 億円の fact に 4% の差(P27E が名指す)。来期の 50 億円は P27 が止める。
# 読む行 = 52 億円(P27E で VALUE_MISMATCH かつ P26 で VALUE_MISMATCH でない)と 来期の 50 億円(P26 で GROUNDED かつ P27 で GROUNDED でない)
SMALL_TEXT = (u"決算\n\n・" + SENTINEL + u"は50億円で、前期の20億円から増えた。\n・営業利益は4.3億円、経常利益は999億円だった。\n・総資産は1,200百万円だった。\n"
              u"・来期の予想は50億円。\n・営業収益は52億円だった。")
PLAIN_TEXT = (u"決算\n\n・" + SENTINEL + u"は50億円で、前期の20億円から増えた。\n・営業利益は4.3億円。\n・総資産は1,200百万円だった。")      # 注入用(来期・遠い数なし)

BIG_N = 60
BIG_FACTS = [fact("jppfs_cor:Item%02d" % i, "CurrentYearDuration", float(i * 1000) * 1e6) for i in range(1, BIG_N + 1)]
BIG_TEXT = u"大きい文\n" + u"\n".join(u"・項目%d は%s百万円だった。" % (i, "{:,}".format(i * 1000)) for i in range(1, BIG_N + 1))


class FakeGit(object):
    """``run(*args) -> (rc, stdout)``。呼び出しの形を分類する(知らない形は AssertionError)。``over`` で 1 つの応答だけ替える。"""

    def __init__(self, **over):
        self.calls = []
        self.over = over

    def kind(self, a):
        if a[0] == "ls-files":
            return "seal_tracked"
        if a[0] == "rev-parse":
            return "head"
        if a[0] == "diff":
            if a == ("diff", "--quiet", "HEAD", "--", M.SEAL):
                return "seal_diff"
            if a[:2] == ("diff", "--quiet") and a[3] == "HEAD" and a[4] == "--" and a[5:] == ("audit-core/adapters", "audit-core/core"):
                return "engine_diff"
        if a[0] == "log":
            if a[1] == "--diff-filter=A" and a[2] == "--format=%H" and a[3] == "--":
                if a[4] == M.W_PATH:
                    return "W"
                if a[4] in M.T_PATHS:
                    return "T%d" % (M.T_PATHS.index(a[4]) + 1)
                if a[4] == M.SEAL:
                    return "S2"
            if a[1] == "--format=%H" and a[2] == '-SPROFILES["P27E"]' and a[3:] == ("--", "audit-core/adapters/xbrl/vocabulary.py"):
                return "E"
        if a[0] == "merge-base" and a[1] == "--is-ancestor":
            if a[2] == GIT["W"]:
                return "anc_W_S2"
            if a[2] == GIT["S2"]:
                return "anc_S2_E"
            if a[2] == GIT["E"]:
                return "anc_E_HEAD"
        raise AssertionError("知らない git の呼び出し: %r" % (a,))

    def __call__(self, *a):
        self.calls.append(a)
        k = self.kind(a)
        if k in self.over:
            return self.over[k]
        one = {"head": GIT["HEAD"], "W": GIT["W"], "T1": GIT["T"], "T2": GIT["T"], "T3": GIT["T"], "S2": GIT["S2"], "E": GIT["E"]}
        return (0, one.get(k, ""))


@contextlib.contextmanager
def open_spy():
    """io.open と builtins.open で開いた path の一覧。"""
    opened = []
    real_io, real_b = io.open, builtins.open

    def s_io(file, *a, **kw):
        opened.append(str(file))
        return real_io(file, *a, **kw)

    def s_b(file, *a, **kw):
        opened.append(str(file))
        return real_b(file, *a, **kw)
    with mock.patch("io.open", s_io), mock.patch("builtins.open", s_b):
        yield opened


class World(object):
    """偽の repo の根・ZIP・文(reports_dir)・DB の応答(db_dir)・既存の cache。"""

    def __init__(self, tmp, texts=None, facts=None):
        self.tmp = tmp
        self.root = os.path.join(tmp, "root")
        self.zip_dir = os.path.join(tmp, "zips")
        self.cache_root = os.path.join(tmp, "p27cache")
        self.reports_dir = os.path.join(tmp, "rep_x")
        self.db_dir = os.path.join(tmp, "db_x")
        self.existing = os.path.join(tmp, "existing")
        self.outside = os.path.join(tmp, "outside", "eval")
        self.out = os.path.join(tmp, "out", "rec.json")
        self.texts = dict((d, SMALL_TEXT) for d in TUNE + EVAL)
        self.texts.update(texts or {})
        self.facts = dict((d, SMALL_FACTS) for d in TUNE + EVAL)
        self.facts.update(facts or {})
        for d in (self.zip_dir, self.existing, self.reports_dir, self.db_dir, self.cache_root,
                  os.path.join(self.root, "fixtures", "xbrl", "p27"), os.path.join(self.root, "fixtures", "xbrl", "fresh")):
            os.makedirs(d)
        for i in range(3):
            open(os.path.join(self.existing, "X%d.zip" % i), "wb").write(b"x")
        companies, zip_rows, calls = [], [], []
        self.report_bytes, self.zip_bytes, self.db_bytes = {}, {}, {}
        for d in TUNE + EVAL:
            rb = self.texts[d].encode("utf-8")
            zb = json.dumps({"facts": self.facts[d]}).encode("utf-8")
            self.report_bytes[d], self.zip_bytes[d] = rb, zb
            open(os.path.join(self.reports_dir, d + ".txt"), "wb").write(rb)
            open(os.path.join(self.zip_dir, d + ".zip"), "wb").write(zb)
            os.makedirs(os.path.join(self.db_dir, d))
            for kind in ("financials", "companies", "ratios"):
                b = (json.dumps({"kind": kind, "name": SENTINEL_DB, "doc": d}, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
                self.db_bytes[(d, kind)] = b
                open(os.path.join(self.db_dir, d, kind + ".json"), "wb").write(b)
                calls.append({"docID": d, "種類": kind, "sha256": sha(b)})
            companies.append({"docID": d, "区分": "調整用" if d in TUNE else "評価用", "型": STYLE[d], "文の sha256": sha(rb)})
            zip_rows.append({"docID": d, "sha256": sha(zb)})
        self.write_json("fixtures/xbrl/p27/reports_2026-10-27.json", {"会社": companies})
        self.write_json("fixtures/xbrl/p27/dbfetch_2026-10-27.json", {"呼び出し": calls})
        self.write_json("fixtures/xbrl/fresh/fetched_2026-10-21.json", {"取得した書類": zip_rows})
        self.log = []
        self.git = FakeGit()
        self.judge_path = None

    def write_json(self, rel, obj):
        io.open(os.path.join(self.root, rel), "w", encoding="utf-8").write(json.dumps(obj, ensure_ascii=False))

    def common(self, **kw):
        a = dict(root=self.root, out=self.out, outside_dir=self.outside, zip_dir=self.zip_dir, cache_root=self.cache_root, existing_dir=self.existing,
                 reports_dir=self.reports_dir, db_dir=self.db_dir, git_run=self.git, vocab=FAKE_VOCAB, backend=M.StubBackend4(), say=self.log.append)
        a.update(kw)
        return a

    def judge(self, **kw):
        return M.run_judge(**self.common(**kw))

    def inject(self, **kw):
        a = self.common(seed_fn=lambda path: ("test-seed", {"sealed_in_commit": "x", "seed_file_sha256": "y"}), work_root=os.path.join(self.tmp, "work"))
        a.update(kw)
        return M.run_inject(**a)

    def seat_file(self, name, labels):
        p = os.path.join(self.tmp, name + ".json")
        io.open(p, "w", encoding="utf-8").write(json.dumps({"席": name, "札": labels}, ensure_ascii=False))
        return p

    def reconcile(self, a, b, **kw):
        args = self.common(seat_a=a, seat_b=b, judge_record=self.judge_path, backend=None)
        args.update(kw)
        return M.run_reconcile(**args)

    def record(self, path=None):
        return json.load(io.open(path or self.out, encoding="utf-8"))

    def record_text(self):
        return io.open(self.out, encoding="utf-8").read()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p27eval_", dir=os.environ.get("TMPDIR"))
        self.addCleanup(self._cleanup)
        self.w = World(self.tmp)

    def _cleanup(self):
        for dp, dns, _fs in os.walk(self.tmp):                    # 権限を戻してから消す
            for dn in dns:
                try:
                    os.chmod(os.path.join(dp, dn), 0o755)
                except OSError:
                    pass
        shutil.rmtree(self.tmp, True)

    def nothing_written(self, w=None):
        w = w or self.w
        self.assertFalse(os.path.exists(w.out), "記録が書かれた")
        self.assertFalse(os.path.exists(w.outside), "外の置き場に何か書かれた")


def label(key, side, det=None, shape=None, why=u"理由"):
    return {"行": key, "側": side, "細目": det, "道5の形": shape, "理由": why}


# ======================================================================================================
class TestPreflight(Base):
    def cases(self):
        w_two = GIT["W"] + "\n" + H("9")
        return [("seal_not_tracked", dict(seal_tracked=(1, ""))), ("seal_differs_from_HEAD", dict(seal_diff=(1, ""))),
                ("seal_diff_other_rc", dict(seal_diff=(129, ""))), ("head_unreadable", dict(head=(128, ""))),
                ("W_zero_commits", dict(W=(0, ""))), ("W_two_commits", dict(W=(0, w_two))), ("W_bad_rc", dict(W=(1, GIT["W"]))),
                ("T_zero_commits", dict(T1=(0, ""))), ("T_commits_differ", dict(T2=(0, H("7")))), ("T_two_commits", dict(T3=(0, GIT["T"] + "\n" + H("8")))),
                ("S2_zero_commits", dict(S2=(0, ""))), ("S2_two_commits", dict(S2=(0, GIT["S2"] + "\n" + H("9")))),
                ("E_not_found", dict(E=(0, ""))), ("E_bad_rc", dict(E=(1, GIT["E"]))),
                ("W_not_ancestor_of_S2", dict(anc_W_S2=(1, ""))), ("S2_not_ancestor_of_E", dict(anc_S2_E=(1, ""))),
                ("S2_equals_E", dict(E=(0, GIT["S2"]))), ("E_not_ancestor_of_HEAD", dict(anc_E_HEAD=(1, ""))),
                ("engine_moved_since_E", dict(engine_diff=(1, ""))), ("engine_diff_other_rc", dict(engine_diff=(129, "")))]

    def run_all_subcommands(self, git, vocab=FAKE_VOCAB, quiet=True):
        seats = (os.path.join(self.tmp, "no_a.json"), os.path.join(self.tmp, "no_b.json"))
        for fn in (lambda: self.w.judge(git_run=git, vocab=vocab), lambda: self.w.inject(git_run=git, vocab=vocab),
                   lambda: self.w.reconcile(seats[0], seats[1], git_run=git, vocab=vocab)):
            yield fn

    def lock_materials(self):
        for d in (self.w.reports_dir, self.w.db_dir):
            os.chmod(d, 0)

    def test_01_every_failing_condition_stops_alone_and_opens_no_evaluation_file(self):
        self.lock_materials()
        for name, over in self.cases():
            for i, fn in enumerate(self.run_all_subcommands(FakeGit(**over))):
                with open_spy() as opened:
                    with self.assertRaises(M.Stop, msg="%s / subcommand %d" % (name, i)):
                        fn()
                bad = [p for p in opened if self.w.reports_dir in p or self.w.db_dir in p or p.endswith(".zip") or self.w.zip_dir in p]
                self.assertEqual(bad, [], "%s: 評価用の file を開いた" % name)
                self.nothing_written()

    def test_02_failing_vocabulary_checks_stop_alone(self):
        self.lock_materials()
        good = dict(PROFILES={"P22": 1, "P26": 1, "P27": 1, "P27E": 1}, DEFAULT_PROFILE="P26")
        bad = [("P22 missing", dict(good, PROFILES={"P26": 1, "P27": 1, "P27E": 1})), ("P26 missing", dict(good, PROFILES={"P22": 1, "P27": 1, "P27E": 1})),
               ("P27 missing", dict(good, PROFILES={"P22": 1, "P26": 1, "P27E": 1})), ("P27E missing", dict(good, PROFILES={"P22": 1, "P26": 1, "P27": 1})),
               ("default P27", dict(good, DEFAULT_PROFILE="P27")), ("default P22", dict(good, DEFAULT_PROFILE="P22")), ("default absent", dict(PROFILES=good["PROFILES"]))]
        for name, kw in bad:
            for i, fn in enumerate(self.run_all_subcommands(FakeGit(), vocab=types.SimpleNamespace(**kw))):
                with open_spy() as opened:
                    with self.assertRaises(M.Stop, msg="%s / %d" % (name, i)):
                        fn()
                self.assertEqual([p for p in opened if self.w.reports_dir in p or self.w.db_dir in p or self.w.zip_dir in p], [], name)
                self.nothing_written()

    def test_03_all_conditions_good_passes_and_the_commits_are_the_ones_git_answered(self):
        g = M.preflight(FakeGit(), FAKE_VOCAB)
        self.assertEqual(g, GIT)

    def test_04_the_exact_git_calls_a_before_b(self):
        git = FakeGit()
        M.preflight(git, FAKE_VOCAB)
        want = [("ls-files", "--error-unmatch", "--", "audit-core/docs/XBRL_P27_SEAL_2026-10-27.md"),
                ("diff", "--quiet", "HEAD", "--", "audit-core/docs/XBRL_P27_SEAL_2026-10-27.md"),
                ("rev-parse", "HEAD"),
                ("log", "--diff-filter=A", "--format=%H", "--", "audit-core/fixtures/xbrl/p27/reports_2026-10-27.json")]
        self.assertEqual(git.calls[:4], want)
        rest = git.calls[4:]
        self.assertEqual([c for c in rest if c[0] == "log"][:3],
                         [("log", "--diff-filter=A", "--format=%H", "--", "audit-core/fixtures/xbrl/p27/" + n)
                          for n in ("tune_2026-10-27.json", "tune_inject_2026-10-27.json", "tune_readings_2026-10-27.json")])
        self.assertIn(("log", "--diff-filter=A", "--format=%H", "--", "audit-core/docs/XBRL_P27_SEAL_2026-10-27.md"), rest)
        self.assertIn(("log", "--format=%H", '-SPROFILES["P27E"]', "--", "audit-core/adapters/xbrl/vocabulary.py"), rest)
        self.assertIn(("merge-base", "--is-ancestor", GIT["W"], GIT["S2"]), rest)
        self.assertIn(("merge-base", "--is-ancestor", GIT["S2"], GIT["E"]), rest)
        self.assertIn(("merge-base", "--is-ancestor", GIT["E"], GIT["HEAD"]), rest)
        self.assertIn(("diff", "--quiet", GIT["E"], "HEAD", "--", "audit-core/adapters", "audit-core/core"), rest)
        # (a) の 2 つが (b) の前
        self.assertEqual([c[0] for c in git.calls[:3]], ["ls-files", "diff", "rev-parse"])

    def test_05_E_is_the_oldest_commit_that_added_P27E(self):
        newer, older = H("6"), GIT["E"]
        g = M.preflight(FakeGit(E=(0, newer + "\n" + older)), FAKE_VOCAB)
        self.assertEqual(g["E"], older)
        self.assertEqual(M.preflight(FakeGit(E=(0, older)), FAKE_VOCAB)["E"], older)

    def test_06_a_failing_check_after_a_passing_one_is_still_reached(self):
        # (a) が通っても (b) の 1 つが違えば止まる(各 check は前の check の結果で飛ばされない)
        with self.assertRaises(M.Stop):
            M.preflight(FakeGit(anc_E_HEAD=(1, "")), FAKE_VOCAB)
        with self.assertRaises(M.Stop):
            M.preflight(FakeGit(engine_diff=(1, "")), FAKE_VOCAB)

    def test_07_the_real_git_runner_answers_rc_and_stdout(self):
        repo = os.path.join(self.tmp, "g")
        os.makedirs(repo)
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
        for args in (["init", "-q"], ["config", "commit.gpgsign", "false"]):
            subprocess.run(["git", "-C", repo] + args, check=True, env=env, capture_output=True)
        open(os.path.join(repo, "f.txt"), "w").write("a\n")
        subprocess.run(["git", "-C", repo, "add", "f.txt"], check=True, env=env, capture_output=True)
        subprocess.run(["git", "-C", repo, "commit", "-q", "-m", "m"], check=True, env=env, capture_output=True)
        run = M.git_runner(repo)
        rc, head = run("rev-parse", "HEAD")
        self.assertEqual(rc, 0)
        self.assertRegex(head, r"^[0-9a-f]{40}$")
        self.assertEqual(run("ls-files", "--error-unmatch", "--", "f.txt")[0], 0)
        self.assertNotEqual(run("ls-files", "--error-unmatch", "--", "none.txt")[0], 0)
        self.assertEqual(run("diff", "--quiet", "HEAD", "--", "f.txt")[0], 0)
        open(os.path.join(repo, "f.txt"), "w").write("b\n")
        self.assertEqual(run("diff", "--quiet", "HEAD", "--", "f.txt")[0], 1)
        rc, log = run("log", "--diff-filter=A", "--format=%H", "--", "f.txt")
        self.assertEqual((rc, log), (0, head))

    def test_08_preflight_runs_before_the_sha_check_and_before_any_material_is_read(self):
        # 文の sha256 も壊した上で git も壊す -> 止める理由は git(文を開かないので sha の違いに届かない)
        open(os.path.join(self.w.reports_dir, EVAL[0] + ".txt"), "ab").write(b" ")
        with open_spy() as opened:
            with self.assertRaises(M.Stop) as cm:
                self.w.judge(git_run=FakeGit(seal_diff=(1, "")))
        self.assertIn("封", str(cm.exception))
        self.assertEqual([p for p in opened if self.w.reports_dir in p], [])


class TestScope(Base):
    def test_10_tuning_and_unlisted_docs_stop_before_any_file_is_opened(self):
        for docs, why in (([TUNE[0]], "tuning"), ([EVAL[0], TUNE[1]], "tuning after eval"), ([TUNE[0], EVAL[0]], "tuning first"),
                          ([DOC_PREFIX + "NONE01"], "unlisted"), ([EVAL[0], DOC_PREFIX + "NONE01"], "unlisted after eval")):
            for fn in (lambda **k: self.w.judge(**k), lambda **k: self.w.inject(**k)):
                with open_spy() as opened:
                    with self.assertRaises(M.Stop, msg=why) as cm:
                        fn(docs=docs)
                self.assertIn("調整用の docID" if "tuning" in why else "区分が評価用でない", str(cm.exception), why)       # 理由ごとの止め(調整用 / 区分の外)
                bad = [p for p in opened if self.w.reports_dir in p or self.w.db_dir in p or self.w.zip_dir in p or p.endswith(".zip")]
                self.assertEqual(bad, [], why)
                self.assertEqual(self.w.git.calls, [], why)                        # git にも届かない(docs の止めが先)
                self.nothing_written()

    def test_11_the_eval_ids_come_from_the_W_record_and_default_docs_are_all_of_them_in_order(self):
        ctx = M.EvalCtx(self.w.root, self.w.zip_dir, self.w.cache_root, self.w.existing, self.w.outside, None, None, self.w.reports_dir, self.w.db_dir)
        self.assertEqual(ctx.docs, EVAL)
        self.assertEqual(sorted(ctx.eval_ids), sorted(EVAL))
        self.assertEqual(ctx.tuning, TUNE)
        self.assertEqual(ctx.eval_list, EVAL)
        rec = self.w.judge()
        self.assertEqual(rec["対象の docID"], EVAL)
        self.assertTrue(rec["対象は評価用の全部"])
        self.assertEqual(rec["評価用の件数"], 3)

    def test_12_a_subset_of_the_eval_docs_is_allowed_but_not_flagged_as_all(self):
        rec = self.w.judge(docs=[EVAL[1]])
        self.assertEqual(rec["対象の docID"], [EVAL[1]])
        self.assertFalse(rec["対象は評価用の全部"])

    def test_13_every_loader_refuses_a_tuning_doc_without_opening(self):
        ctx = M.EvalCtx(self.w.root, self.w.zip_dir, self.w.cache_root, self.w.existing, self.w.outside, None, None, self.w.reports_dir, self.w.db_dir)
        for name in ("read_report", "read_zip", "read_db", "zip_path", "guard"):
            with open_spy() as opened:
                with self.assertRaises(M.Stop) as cm:
                    getattr(ctx, name)(TUNE[1])
            self.assertIn("調整用の docID", str(cm.exception), name)
            self.assertEqual(opened, [], name)
        for name in ("read_report", "read_zip", "read_db", "zip_path", "guard"):
            with open_spy() as opened:
                with self.assertRaises(M.Stop) as cm:
                    getattr(ctx, name)(DOC_PREFIX + "NONE01")
            self.assertIn("区分が評価用でない", str(cm.exception), name)
            self.assertEqual(opened, [], name)

    def test_14_the_eval_context_reads_from_the_given_reports_and_db_folders(self):
        ctx = M.EvalCtx(self.w.root, self.w.zip_dir, self.w.cache_root, self.w.existing, self.w.outside, None, None, self.w.reports_dir, self.w.db_dir)
        text, b = ctx.read_report(EVAL[0])
        self.assertEqual(b, self.w.report_bytes[EVAL[0]])
        self.assertEqual(ctx.read_db(EVAL[0])["ratios"], self.w.db_bytes[(EVAL[0], "ratios")])
        self.assertEqual(ctx.read_zip(EVAL[0]), self.w.zip_bytes[EVAL[0]])
        # 既定の置き場: reports は <cache-root>/reports・DB は <cache-root>/<docID>/
        ctx2 = M.EvalCtx(self.w.root, self.w.zip_dir, self.w.cache_root, self.w.existing, self.w.outside, None, None)
        self.assertEqual(ctx2.reports_dir, os.path.join(self.w.cache_root, "reports"))
        self.assertEqual(ctx2.db_dir, self.w.cache_root)

    def test_15_outside_folder_may_not_be_stage1_places_protected_folders_or_the_repo(self):
        for bad in (os.path.join(self.w.cache_root, "tune"), os.path.join(self.w.cache_root, "tune_p27", "x"), os.path.join(self.w.zip_dir, "eval"),
                    os.path.join(self.w.existing, "eval"), os.path.join(self.w.root, "eval")):
            with self.assertRaises(M.Stop, msg=bad):
                self.w.judge(outside_dir=bad)
            self.assertFalse(os.path.exists(self.w.out))
        self.assertEqual(_listing(self.w.existing), ["X0.zip", "X1.zip", "X2.zip"])
        with self.assertRaises(M.Stop):
            self.w.inject(work_root=os.path.join(self.w.existing, "work"))

    def test_16_default_outside_folder_is_eval_under_the_cache_root(self):
        self.assertEqual(M.OUTSIDE_NAME, "eval")
        rec = self.w.judge(outside_dir=None)
        self.assertTrue(os.path.exists(os.path.join(self.w.cache_root, "eval", "judge_full.json")))
        self.assertFalse(os.path.exists(os.path.join(self.w.cache_root, "tune")))
        self.assertTrue(rec["repo の外に置いたもの"]["folder"].endswith("eval"))

    def test_17_a_company_with_an_unknown_kubun_in_the_W_record_stops(self):
        p = os.path.join(self.w.root, "fixtures/xbrl/p27/reports_2026-10-27.json")
        d = json.load(io.open(p, encoding="utf-8"))
        d["会社"][0]["区分"] = "予備"
        io.open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
        with self.assertRaises(M.Stop):
            self.w.judge()
        self.nothing_written()

    def test_18_Stop_is_the_stage1_Stop(self):
        self.assertIs(M.Stop, M.T.Stop)


class CountingBackend(M.StubBackend4):
    def __init__(self):
        self.verify_calls = 0

    def verify(self, zb, profile, text):
        self.verify_calls += 1
        return M.StubBackend4.verify(self, zb, profile, text)


class TestShaCheck(Base):
    def tamper(self, path, fn):
        orig = open(path, "rb").read()
        open(path, "wb").write(fn(orig))
        return orig

    def test_20_a_report_that_differs_from_the_W_record_stops_before_any_work_and_writes_nothing(self):
        for d in EVAL:                                     # 先頭でも最後でも(10 本の全部を照らす)
            path = os.path.join(self.w.reports_dir, d + ".txt")
            orig = self.tamper(path, lambda b: b + b" ")
            for fn in (lambda be: self.w.judge(backend=be), lambda be: self.w.inject(backend=be)):
                be = CountingBackend()
                with self.assertRaises(M.Stop) as cm:
                    fn(be)
                self.assertIn("W の記録", str(cm.exception))
                self.assertIn(d, str(cm.exception))
                self.assertEqual(be.verify_calls, 0, d)               # engine に 1 本も通していない
                self.nothing_written()
            open(path, "wb").write(orig)
        self.w.judge()                                       # 戻せば通る
        self.assertTrue(os.path.exists(self.w.out))

    def test_21_zip_and_db_sha_mismatch_stop_before_any_work_and_write_nothing(self):
        be = CountingBackend()
        zp = os.path.join(self.w.zip_dir, EVAL[2] + ".zip")
        orig = self.tamper(zp, lambda b: b + b" ")
        for fn in (lambda: self.w.judge(backend=be), lambda: self.w.inject(backend=be)):
            with self.assertRaises(M.Stop) as cm:
                fn()
            self.assertIn("ZIP", str(cm.exception))
            self.assertEqual(be.verify_calls, 0)
            self.nothing_written()
        open(zp, "wb").write(orig)
        for kind in ("financials", "companies", "ratios"):
            dp = os.path.join(self.w.db_dir, EVAL[2], kind + ".json")
            orig = self.tamper(dp, lambda b: b + b" ")
            with self.assertRaises(M.Stop) as cm:
                self.w.judge(backend=be)
            self.assertIn("DB の応答", str(cm.exception))
            self.assertEqual(be.verify_calls, 0)
            self.nothing_written()
            open(dp, "wb").write(orig)

    def test_22_a_stop_message_has_no_text_or_db_chars(self):
        path = os.path.join(self.w.reports_dir, EVAL[0] + ".txt")
        self.tamper(path, lambda b: b + b" ")
        with self.assertRaises(M.Stop) as cm:
            self.w.judge()
        self.assertNotIn(SENTINEL, str(cm.exception))
        self.assertNotIn(SENTINEL_DB, str(cm.exception))

    def test_23_a_backend_that_writes_into_the_zip_folder_stops_without_a_record(self):
        zip_dir = self.w.zip_dir

        class Writer(M.StubBackend4):
            def verify(self, zb, profile, text):
                open(os.path.join(zip_dir, "stray.zip"), "wb").write(b"x")
                return M.StubBackend4.verify(self, zb, profile, text)
        for fn in (lambda: self.w.judge(backend=Writer()), lambda: self.w.inject(backend=Writer())):
            with self.assertRaises(M.Stop) as cm:
                fn()
            self.assertIn("変わった", str(cm.exception))
            self.assertFalse(os.path.exists(self.w.out))
            os.remove(os.path.join(zip_dir, "stray.zip"))

    def test_24_header_cache_before_after_and_nothing_added_to_protected_folders(self):
        before = (_listing(self.w.existing), _listing(self.w.zip_dir))
        rec = self.w.judge()
        self.assertEqual((_listing(self.w.existing), _listing(self.w.zip_dir)), before)
        c = rec["cache の前後"]
        self.assertTrue(c["変化なし"])
        self.assertEqual(c["前"], c["後"])
        self.assertEqual(c["前"]["既存の cache"]["件数"], 3)
        self.assertEqual(c["前"]["ZIP の folder"]["件数"], 5)
        self.assertEqual(c["前"]["既存の cache"]["名前の一覧の sha256"], sha("\n".join(["X0.zip", "X1.zip", "X2.zip"]).encode("utf-8")))


class TestJudge(Base):
    def stub_outs(self, doc):
        be = M.StubBackend4()
        zb, text = self.w.zip_bytes[doc], self.w.texts[doc]
        return dict((p, be.verify(zb, p, text)) for p in M.PROFILES)

    def test_30_four_profiles_in_this_order_and_the_stage1_list_follows(self):
        self.assertEqual(M.PROFILES, ("P22", "P26", "P27", "P27E"))
        rec = self.w.judge()
        self.assertEqual(M.T.PROFILES, ("P22", "P26", "P27", "P27E"))
        for row in rec["claim"]:
            self.assertEqual(list(row), ["docID", "id", "P22", "P26", "P27", "P27E"])
        for c in rec["会社"]:
            self.assertEqual(list(c["claim の数"]), ["P22", "P26", "P27", "P27E"])
            self.assertEqual(list(c["state の数"]), ["P22", "P26", "P27", "P27E"])

    def test_31_record_fields_of_P22_and_P26_are_the_stage1_claim_record(self):
        rec = self.w.judge()
        self.assertIs(M.claim_record, M.T.claim_record)
        self.assertEqual(M.T.RECORD_CLAIM_FIELDS, ("kind", "form", "unit", "state", "reason", "pointers"))
        for doc in EVAL:
            outs = self.stub_outs(doc)
            rows = [r for r in rec["claim"] if r["docID"] == doc]
            for p in M.PROFILES:
                want = [M.T.claim_record(c) for c in outs[p]["claims"]]
                self.assertEqual([r[p] for r in rows], want, (doc, p))
                for r in rows:
                    self.assertEqual(sorted(r[p]), sorted(M.T.RECORD_CLAIM_FIELDS))
        self.assertEqual([r["id"] for r in rec["claim"] if r["docID"] == EVAL[0]], ["N%03d" % i for i in range(1, 8)])

    def test_32_the_stub_world_states(self):
        rec = self.w.judge()
        s = rec["集計"]["state の数"]
        self.assertEqual(s["P22"], {"GROUNDED": 15, "VALUE_MISMATCH": 6, "UNVERIFIABLE": 0, "POINTER_NOT_FOUND": 0})
        self.assertEqual(s["P26"], {"GROUNDED": 15, "VALUE_MISMATCH": 0, "UNVERIFIABLE": 0, "POINTER_NOT_FOUND": 6})
        self.assertEqual(s["P27"], {"GROUNDED": 12, "VALUE_MISMATCH": 0, "UNVERIFIABLE": 3, "POINTER_NOT_FOUND": 6})
        self.assertEqual(s["P27E"], {"GROUNDED": 12, "VALUE_MISMATCH": 3, "UNVERIFIABLE": 3, "POINTER_NOT_FOUND": 3})

    def test_33_claims_are_paired_by_id_per_profile_and_differences_are_recorded(self):
        class Skew(M.StubBackend4):
            def verify(self, zb, profile, text):
                out = M.StubBackend4.verify(self, zb, profile, text)
                if profile == "P27":
                    out["claims"] = out["claims"][1:]            # 先頭の id が P27 に無い
                    out["claims"][0]["span"] = u"別の窓"
                if profile == "P27E":
                    out["claims"][2]["unit"] = u"千円"
                return out
        rec = self.w.judge(backend=Skew())
        c0 = rec["会社"][0]
        self.assertEqual(c0["片方の profile にしか無い id"], {"P26": [], "P27": ["N001"], "P27E": []})
        self.assertEqual(c0["値・span・単位が profile 間で違う id"], {"P26": [], "P27": ["N002"], "P27E": ["N003"]})
        row = [r for r in rec["claim"] if r["docID"] == EVAL[0] and r["id"] == "N001"][0]
        self.assertIsNone(row["P27"])
        self.assertIsNotNone(row["P22"])

        # P22 に無く、あとの profile にだけ在る id も対にして記録する(P22 の id の並びの後ろ)
        class Extra(M.StubBackend4):
            def verify(self, zb, profile, text):
                out = M.StubBackend4.verify(self, zb, profile, text)
                if profile == "P27E":
                    out["claims"].append(dict(out["claims"][0], id="N900"))
                return out
        self.w.out = os.path.join(self.tmp, "o3", "extra.json")
        rec = self.w.judge(backend=Extra(), outside_dir=os.path.join(self.tmp, "outside_extra"))
        rows = [r for r in rec["claim"] if r["docID"] == EVAL[0]]
        self.assertEqual([r["id"] for r in rows], ["N%03d" % i for i in range(1, 8)] + ["N900"])
        self.assertEqual([p for p in M.PROFILES if rows[-1][p] is not None], ["P27E"])
        self.assertEqual(rec["会社"][0]["片方の profile にしか無い id"], {"P26": [], "P27": [], "P27E": ["N900"]})
        self.assertEqual(rec["会社"][0]["claim の数"]["P27E"], 8)

    def test_34_the_pairing_agrees_with_stage1_pair_claims_for_P22_and_P26(self):
        class Skew(M.StubBackend4):
            def verify(self, zb, profile, text):
                out = M.StubBackend4.verify(self, zb, profile, text)
                if profile == "P26":
                    out["claims"] = out["claims"][1:]
                    out["claims"][0]["span"] = u"別の窓"
                return out
        be = Skew()
        zb, text = self.w.zip_bytes[EVAL[0]], self.w.texts[EVAL[0]]
        outs = dict((p, be.verify(zb, p, text)) for p in M.PROFILES)
        ids4, _per, only4, differ4 = M.pair_claims(outs)
        old = M.T.PROFILES
        M.T.PROFILES = ("P22", "P26")
        try:
            ids2, _a, _b, only2, differ2 = M.T.pair_claims(outs)
        finally:
            M.T.PROFILES = old
        self.assertEqual(ids4, ids2)
        self.assertEqual(only4["P26"], only2)
        self.assertEqual(differ4["P26"], differ2)

    def test_35_duplicate_ids_in_one_profile_stop(self):
        class Dup(M.StubBackend4):
            def verify(self, zb, profile, text):
                out = M.StubBackend4.verify(self, zb, profile, text)
                if profile == "P27":
                    out["claims"][1]["id"] = out["claims"][0]["id"]
                return out
        with self.assertRaises(M.Stop):
            self.w.judge(backend=Dup())
        self.nothing_written()

    def test_36_read_row_conditions_truth_table(self):
        def c(state):
            return None if state is None else {"state": state}

        def f(p26, p27, p27e, p22="GROUNDED"):
            return M.read_row_conditions({"P22": c(p22), "P26": c(p26), "P27": c(p27), "P27E": c(p27e)})
        K3, K4 = M.COND_K3, M.COND_K4
        self.assertEqual(f("PNF" if False else "POINTER_NOT_FOUND", "POINTER_NOT_FOUND", "VALUE_MISMATCH"), [K3])         # P27E だけ VALUE_MISMATCH
        self.assertEqual(f("GROUNDED", "UNVERIFIABLE", "UNVERIFIABLE"), [K4])                                          # P26 GROUNDED -> P27 GROUNDED でない
        self.assertEqual(f("GROUNDED", "GROUNDED", "VALUE_MISMATCH"), [K3])                                            # (B は GROUNDED を動かさないので実際は起きない形も条件は数える)
        self.assertEqual(f("GROUNDED", "POINTER_NOT_FOUND", "VALUE_MISMATCH"), [K3, K4])                               # 両方
        self.assertEqual(f("VALUE_MISMATCH", "VALUE_MISMATCH", "VALUE_MISMATCH"), [])                                  # P26 も VALUE_MISMATCH なら読まない
        self.assertEqual(f("VALUE_MISMATCH", "POINTER_NOT_FOUND", "POINTER_NOT_FOUND"), [])
        self.assertEqual(f("GROUNDED", "GROUNDED", "GROUNDED"), [])
        self.assertEqual(f("POINTER_NOT_FOUND", "POINTER_NOT_FOUND", "POINTER_NOT_FOUND"), [])
        self.assertEqual(f("UNVERIFIABLE", "UNVERIFIABLE", "UNVERIFIABLE"), [])
        self.assertEqual(f("GROUNDED", "GROUNDED", "UNVERIFIABLE"), [])                                                # P27E だけの変化は読まない(P27 で GROUNDED)
        self.assertEqual(f("POINTER_NOT_FOUND", "VALUE_MISMATCH", "POINTER_NOT_FOUND"), [])                            # P27 だけ VALUE_MISMATCH は対象外
        self.assertEqual(f("VALUE_MISMATCH", "GROUNDED", "GROUNDED", p22="VALUE_MISMATCH"), [])                        # P22 の state は条件に使わない
        # claim が無い profile
        self.assertEqual(f(None, None, "VALUE_MISMATCH"), [K3])
        self.assertEqual(f("GROUNDED", None, "GROUNDED"), [K4])
        self.assertEqual(f(None, None, None), [])
        self.assertEqual(M.read_row_conditions({}), [])

    def test_37_read_rows_in_a_run_and_dossier_files_only_for_them(self):
        rec = self.w.judge()
        rows = rec["読む行"]
        self.assertEqual(len(rows), 6)
        by = dict(((c["docID"], c["id"]), c) for c in rec["claim"])
        for doc in EVAL:
            got = [r for r in rows if r["docID"] == doc]
            self.assertEqual([r["条件"] for r in got], [[M.COND_K4], [M.COND_K3]])      # 来期の 50 億円(N006)・52 億円(N007)の順
            self.assertEqual([r["id"] for r in got], ["N006", "N007"])
        for r in rows:
            c = by[(r["docID"], r["id"])]
            self.assertEqual(r["行"], "%s:%s" % (r["docID"], r["id"]))
            if M.COND_K3 in r["条件"]:
                self.assertEqual((c["P26"]["state"], c["P27E"]["state"]), ("POINTER_NOT_FOUND", "VALUE_MISMATCH"))
            if M.COND_K4 in r["条件"]:
                self.assertEqual((c["P26"]["state"], c["P27"]["state"]), ("GROUNDED", "UNVERIFIABLE"))
        picked = set((r["docID"], r["id"]) for r in rows)
        for k, c in by.items():
            if k not in picked:
                self.assertEqual(M.read_row_conditions(c), [], k)
        names = sorted(os.listdir(os.path.join(self.w.outside, "dossier")))
        self.assertEqual(names, sorted(["%s__%s.txt" % (r["docID"], r["id"]) for r in rows] + ["index.json", "reader_prompt.txt"]))
        self.assertEqual(rec["集計"]["読む行"], {"数": 6, "条件ごと(重なる)": {M.COND_K3: 3, M.COND_K4: 3}})

    def test_38_dossier_has_p27_and_p27e_blocks_from_the_script_constants_after_p26(self):
        rec = self.w.judge()
        d = os.path.join(self.w.outside, "dossier")
        r = [x for x in rec["読む行"] if M.COND_K3 in x["条件"]][0]
        body = io.open(os.path.join(d, "%s__%s.txt" % (r["docID"], r["id"])), encoding="utf-8").read()
        full = json.load(io.open(os.path.join(self.w.outside, "judge_full.json"), encoding="utf-8"))["docs"][r["docID"]]["claims"]
        for p in M.PROFILES:
            claim = [c for c in full[p] if c["id"] == r["id"]][0]
            block = M.DOSSIER_P27_BLOCK.format(profile=p, body=M.T.dumps(claim).rstrip("\n")) if p in ("P27", "P27E") else \
                "## 2 claim の全部の欄(%s)\n%s\n\n" % (p, M.T.dumps(claim).rstrip("\n"))
            self.assertIn(block, body, p)
        order = [body.index("## 2 claim の全部の欄(%s)" % p) for p in M.PROFILES]
        self.assertEqual(order, sorted(order))
        self.assertLess(body.index("## 2 claim の全部の欄(P27E)"), body.index(M.DOSSIER_MARK3))
        self.assertLess(body.index(M.DOSSIER_MARK3), body.index(M.DOSSIER_MARK4))
        self.assertIn('"state": "VALUE_MISMATCH"', body.split("## 2 claim の全部の欄(P27E)")[1])
        self.assertEqual(M.DOSSIER_P27_BLOCK, "## 2 claim の全部の欄({profile})\n{body}\n\n")
        self.assertEqual(M.DOSSIER_P27_PROFILES, ("P27", "P27E"))
        info = rec["束の P27・P27E の欄を足す形(script の定数)"]
        self.assertEqual(info["DOSSIER_P27_BLOCK"], M.DOSSIER_P27_BLOCK)

    def test_39_taking_the_p27_blocks_out_gives_the_stage1_dossier_byte_for_byte(self):
        outs = self.stub_outs(EVAL[0])
        claims = dict((p, [c for c in outs[p]["claims"] if c["id"] == "N007"][0]) for p in M.PROFILES)
        facts = M.StubBackend4().facts(self.w.zip_bytes[EVAL[0]])
        db = dict((k, self.w.db_bytes[(EVAL[0], k)]) for k in ("financials", "companies", "ratios"))
        para, note = M.T.paragraph_of(self.w.texts[EVAL[0]], claims["P22"]["span"])
        base = M.T.render_dossier(EVAL[0], "A", "N007", para, note, claims["P22"], claims["P26"], facts, db)
        got = M.render_dossier4(EVAL[0], "A", "N007", para, note, claims, facts, db)
        stripped = got
        for p in M.DOSSIER_P27_PROFILES:
            stripped = stripped.replace(M.DOSSIER_P27_BLOCK.format(profile=p, body=M.T.dumps(claims[p]).rstrip("\n")), "")
        self.assertEqual(stripped, base)
        self.assertIsNot(M.render_dossier, None)
        self.assertIs(M.render_dossier, M.T.render_dossier)
        # P27E の pointers が P22・P26 の pointers に無ければ、節 3b にその fact を足す。同じなら足さない
        self.assertNotIn(M.DOSSIER_P27_FACTS_HEAD, got)
        other = dict(claims, P27E=dict(claims["P27E"], pointers=["xbrl:jppfs_cor:TotalAssets@CurrentYearInstant"]))
        got2 = M.render_dossier4(EVAL[0], "A", "N007", para, note, other, facts, db)
        self.assertIn(M.DOSSIER_P27_FACTS_HEAD, got2)
        tail = got2.split(M.DOSSIER_P27_FACTS_HEAD)[1].split(M.DOSSIER_MARK4)[0]
        self.assertIn("要素 jppfs_cor:TotalAssets", tail)
        self.assertIn("◀ 名指し", tail)
        self.assertLess(got2.index(M.DOSSIER_MARK3), got2.index(M.DOSSIER_P27_FACTS_HEAD))
        self.assertLess(got2.index(M.DOSSIER_P27_FACTS_HEAD), got2.index(M.DOSSIER_MARK4))
        # claim が無い profile
        none = dict(claims, P27=None)
        got3 = M.render_dossier4(EVAL[0], "A", "N007", para, note, none, facts, db)
        self.assertIn("## 2 claim の全部の欄(P27)\n" + M.DOSSIER_NO_CLAIM + "\n\n", got3)
        self.assertEqual(M.DOSSIER_NO_CLAIM, M.T.render_dossier(EVAL[0], "A", "N007", para, note, None, None, facts, db).split("## 2 claim の全部の欄(P22)\n")[1].split("\n")[0])

    def test_40_reader_prompt_index_and_hashes(self):
        rec = self.w.judge()
        d = os.path.join(self.w.outside, "dossier")
        self.assertEqual(open(os.path.join(d, "reader_prompt.txt"), "rb").read(), M.PR.READER_PROMPT.encode("utf-8"))
        self.assertIs(M.PR, M.T.PR)
        info = rec["repo の外に置いたもの"]["dossier"]
        self.assertEqual(info["読み手の指示文 reader_prompt.txt の sha256"], sha(M.PR.READER_PROMPT.encode("utf-8")))
        self.assertTrue(info["読み手の指示文は封 §5-6 の字(prompts の READER_PROMPT)と同じ"])
        self.assertEqual(info["index.json の sha256"], sha(open(os.path.join(d, "index.json"), "rb").read()))
        self.assertEqual(info["件数"], 6)
        for row in json.load(io.open(os.path.join(d, "index.json"), encoding="utf-8"))["rows"]:
            self.assertEqual(info["各 file の sha256"][row["行"]], row["sha256"])
            self.assertEqual(row["sha256"], sha(open(os.path.join(d, row["file"]), "rb").read()))
        full = open(os.path.join(self.w.outside, "judge_full.json"), "rb").read()
        self.assertEqual(rec["repo の外に置いたもの"]["全部の欄(span・subject・value・recomputed を含む)"]["sha256"], sha(full))
        self.assertIn(SENTINEL, full.decode("utf-8"))                      # 外には全部の欄(span)がある
        for kind in ("companies", "financials", "ratios"):
            body = io.open(os.path.join(d, "%s__N007.txt" % EVAL[0]), encoding="utf-8").read()
            self.assertIn(self.w.db_bytes[(EVAL[0], kind)].decode("utf-8"), body)

    def test_41_rule_counts_per_company_and_the_V6_numbers(self):
        rec = self.w.judge()
        for c in rec["会社"]:
            rc = c["規則ごと(build_raw_claims の provenance)"]
            self.assertEqual(sorted(rc), ["P27", "P27E"])
            for p in rc:
                self.assertEqual(sorted(rc[p]), sorted(M.RULE_KEYS))
            self.assertEqual(rc["P27"]["C3 future_period"], 1)
            self.assertEqual(rc["P27E"]["B relative_within_rho"], 1)
            self.assertEqual(rc["P27"]["B relative_within_rho"], 0)
        v6 = rec["集計"]["規則ごとに当たった claim(V-6。build_raw_claims の provenance)"]
        self.assertEqual(v6, {"C2 で止めた claim(P27)": 0, "C3 で target_or_plan にした claim(P27)": 3,
                              "C1 で other_concept になった行(P27)": 0, "B で名指した行(P27E の無改変)": 3})

    def test_42_real_backend_counts_provenance_with_the_same_input_as_verify_document(self):
        seen = {}

        def fake_modified(zb, text):
            seen["modified_args"] = (zb, text)
            return b"MODIFIED", "el", "member"

        def fake_rules(zb, profiles):
            seen["rules_args"] = (zb, tuple(profiles))
            return {"P27": {}, "P27E": {}}
        be = M.RealBackend4()
        with mock.patch.object(M.R97.VD.PR, "build_modified_zip", fake_modified), mock.patch.object(M.R97, "rule_counts", fake_rules):
            be.rule_counts(b"ZIP", u"文")
        self.assertEqual(seen["modified_args"], (b"ZIP", u"文"))
        self.assertEqual(seen["rules_args"], (b"MODIFIED", ("P22", "P26", "P27", "P27E")))
        self.assertIs(M.rule_counts, M.R97.rule_counts)
        self.assertTrue(issubclass(M.RealBackend4, M.T.RealBackend))
        # verify_document が同じ差し込みをしていること(rule_counts が同じ入力を数える前提)
        src = io.open(os.path.join(ROOT, "adapters", "xbrl", "verify_document.py"), encoding="utf-8").read()
        self.assertIn("PR.build_modified_zip(zip_bytes, text)", src)

    def test_43_summary_numbers_from_crafted_rows(self):
        def row(p22, p26, p27, p27e, i):
            f = lambda s: None if s is None else {"state": s}                      # noqa: E731
            return {"docID": "d", "id": "N%03d" % i, "P22": f(p22), "P26": f(p26), "P27": f(p27), "P27E": f(p27e)}
        G, V_, U, P = "GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"
        rows = [row(G, G, G, G, 1), row(G, G, U, U, 2), row(V_, P, P, V_, 3), row(V_, V_, V_, V_, 4), row(V_, P, G, G, 5), row(G, P, P, P, 6), row(G, None, G, G, 7)]
        rc = {"P27": dict((k, 0) for k in M.RULE_KEYS), "P27E": dict((k, 0) for k in M.RULE_KEYS)}
        per_doc = [{"規則ごと(build_raw_claims の provenance)": dict(rc, P27=dict(rc["P27"], **{M.RULE_KEYS[0]: 4, M.RULE_KEYS[1]: 2, M.RULE_KEYS[3]: 1}),
                                                          P27E=dict(rc["P27E"], **{M.RULE_KEYS[4]: 3}))}]
        read = [{"条件": [M.COND_K3]}, {"条件": [M.COND_K3, M.COND_K4]}]
        s = M.judge_summary(rows, per_doc, read)
        self.assertEqual(s["claim"], {"P22": 7, "P26": 6, "P27": 7, "P27E": 7})
        self.assertEqual(s["state の数"]["P22"], {G: 4, V_: 3, U: 0, P: 0})
        self.assertEqual(s["state の数"]["P26"], {G: 2, V_: 1, U: 0, P: 3})
        self.assertEqual(s["state の数"]["P27"], {G: 3, V_: 1, U: 1, P: 2})
        self.assertEqual(s["state の数"]["P27E"], {G: 3, V_: 2, U: 1, P: 1})
        self.assertEqual(s["VALUE_MISMATCH の率"]["P26"], {"件": 1, "分母": 6, "率": 16.7})
        self.assertEqual(s["P27E の VALUE_MISMATCH の行 − P27 の VALUE_MISMATCH の行"], 1)
        self.assertEqual(s["P26 → P27 で GROUNDED を離れた行"], 1)             # 行 2
        self.assertEqual(s["P26 → P27 で新しい GROUNDED"], 2)                  # 行 5・7(P26 に claim が無い)
        self.assertEqual(s["P26 → P27 で VALUE_MISMATCH に入る行"], 0)
        self.assertEqual(s["P27 → P27E で state が動いた行"], 1)               # 行 3(POINTER_NOT_FOUND → VALUE_MISMATCH)だけ。行 2 は UNVERIFIABLE のまま
        self.assertTrue(s["P27 と P27E で GROUNDED の行が同じ"] is True)
        moved = rows + [row(G, G, G, U, 8)]
        self.assertTrue(M.judge_summary(moved, per_doc, read)["P27 と P27E で GROUNDED の行が同じ"] is False)
        self.assertEqual(s["P27E で VALUE_MISMATCH かつ P26 で VALUE_MISMATCH でない行"], 1)
        self.assertEqual(s["規則ごとに当たった claim(V-6。build_raw_claims の provenance)"],
                         {"C2 で止めた claim(P27)": 4, "C3 で target_or_plan にした claim(P27)": 2, "C1 で other_concept になった行(P27)": 1, "B で名指した行(P27E の無改変)": 3})
        self.assertEqual(s["読む行"], {"数": 2, "条件ごと(重なる)": {M.COND_K3: 2, M.COND_K4: 1}})

    def test_44_header_has_the_four_commits_fingerprint_cache_and_outside_sha(self):
        rec = self.w.judge()
        for key, g in (("HEAD の commit", "HEAD"), ("W の commit", "W"), ("T の commit", "T"), ("S2 の commit", "S2"), ("E の commit", "E")):
            self.assertEqual(rec[key], GIT[g], key)
        self.assertEqual(rec["engine の指紋"], {"stub": True})
        self.assertEqual(rec["seal"], "audit-core/docs/XBRL_P27_SEAL_2026-10-27.md")
        self.assertTrue(rec["dry_run"] is False)
        self.assertEqual(rec["backend"], "stub")
        self.assertEqual(rec["使った文の sha256"], dict((d, sha(self.w.report_bytes[d])) for d in EVAL))
        self.assertEqual(rec["この script の sha256"], sha(open(SCRIPT, "rb").read()))
        self.assertEqual(rec["段 1 の測定の script(読むだけ・1 字も変えない)の sha256"], sha(open(os.path.join(os.path.dirname(SCRIPT), "xbrl_p27_tune_2026-10-27.py"), "rb").read()))
        self.assertEqual(rec["97 書類の測定の script(rule_counts を読むだけ・1 字も変えない)の sha256"],
                         sha(open(os.path.join(os.path.dirname(SCRIPT), "xbrl_p27_regress97_2026-10-27.py"), "rb").read()))
        self.assertEqual(rec["走る前の確かめ"]["profile の一覧"], ["P22", "P26", "P27", "P27E"])
        self.assertEqual(rec["走る前の確かめ"]["既定の profile"], "P26")

    def test_45_existing_outputs_are_never_overwritten(self):
        self.w.judge()
        before = self.w.record_text()
        with self.assertRaises(M.Stop):
            self.w.judge(outside_dir=os.path.join(self.tmp, "outside2"))
        self.assertEqual(self.w.record_text(), before)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "outside2")))
        # 外の置き場に file が在れば、記録を書かずに止める
        out2 = os.path.join(self.tmp, "o2", "rec.json")
        with self.assertRaises(M.Stop):
            self.w.judge(out=out2)
        self.assertFalse(os.path.exists(out2))

    def test_46_dry_run_needs_an_explicit_out(self):
        with self.assertRaises(M.Stop):
            self.w.judge(dry_run=True, out=None)
        self.nothing_written()
        rec = self.w.judge(dry_run=True)
        self.assertTrue(rec["dry_run"])


class TestInject(Base):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p27eval_", dir=os.environ.get("TMPDIR"))
        self.addCleanup(self._cleanup)
        self.w = World(os.path.join(self.tmp, "w"), texts=dict((d, PLAIN_TEXT) for d in TUNE + EVAL))
        self.big = World(os.path.join(self.tmp, "big"), texts=dict((d, BIG_TEXT) for d in TUNE + EVAL), facts=dict((d, BIG_FACTS) for d in TUNE + EVAL))

    def test_50_the_stage1_functions_are_used_as_they_are(self):
        T = M.T
        self.assertIs(M.select_t1_value, T.IJ.select)
        self.assertIs(M.t8_candidates, T.t8_candidates)
        self.assertIs(M.base_status, T.base_status)
        self.assertIs(M.claim_for_p27, T.claim_for_p27)
        self.assertIs(M.classify, T.classify)
        self.assertIs(M.inject_doc, T.inject_doc)
        for name in ("t8_candidates", "base_status", "claim_for_p27", "classify", "inject_doc", "find_base_claim", "named_original", "pick_r", "inject_summary"):
            self.assertTrue(getattr(T, name).__code__.co_filename.endswith("xbrl_p27_tune_2026-10-27.py"), name)
        tree = ast.parse(io.open(SCRIPT, encoding="utf-8").read())
        defined = set(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
        self.assertFalse(defined & {"t8_candidates", "base_status", "claim_for_p27", "classify", "find_base_claim", "named_original", "pick_r", "inject_doc",
                                    "inject_summary", "select", "claim_record", "render_dossier", "combine", "load_seat", "validate_label", "write_record"}, defined)

    def test_51_each_row_has_all_four_profiles_and_the_base_is_grounded_in_p22_and_p26(self):
        rec = self.w.inject()
        j = self.w.judge(out=os.path.join(self.tmp, "o", "judge.json"), outside_dir=os.path.join(self.tmp, "outside_j"))
        by = dict(((c["docID"], c["id"]), c) for c in j["claim"])
        self.assertTrue(rec["行"])
        for r in rec["行"]:
            self.assertEqual(sorted(k for k in r if k in M.PROFILES), ["P22", "P26", "P27", "P27E"])
            b = by[(r["docID"], r["基準の claim"])]
            self.assertEqual((b["P22"]["state"], b["P26"]["state"]), ("GROUNDED", "GROUNDED"))
        # 土台が 1 つでも GROUNDED でない claim(ここでは偽の文に無い)を作って、土台から外れることを見る
        text = PLAIN_TEXT + u"\n・営業収益は999億円だった。"
        w2 = World(os.path.join(self.tmp, "b2"), texts=dict((d, text) for d in TUNE + EVAL))
        rec2 = w2.inject(docs=[EVAL[0]])
        self.assertEqual(rec2["書類別の数え"][EVAL[0]]["T8_REL"]["どちらも GROUNDED でない"], 1)
        self.assertEqual(rec2["書類別の数え"][EVAL[0]]["T8_REL"]["両方 GROUNDED"], 4)
        self.assertEqual(rec2["書類別の数え"][EVAL[0]]["T8_REL"]["採った"], 4)

    def test_52_the_stub_world_outcomes_per_profile(self):
        rec = self.w.inject()
        t8 = [r for r in rec["行"] if r["型"] == "T8_REL"]
        self.assertEqual(len(t8), 12)                                # 3 書類 × 4 つの土台(50・20・4.3・1,200百万。どれも P22 と P26 の両方で GROUNDED)
        for r in t8:
            self.assertIn(r["r"], M.T.T8_R_VALUES)
            self.assertEqual(r["P22"]["結果"], M.T.LABEL_NAMED_ORIGINAL)
            self.assertEqual(r["P26"]["結果"], M.T.LABEL_PNF)
            self.assertEqual(r["P27"]["結果"], M.T.LABEL_PNF)
            self.assertEqual(r["P27E"]["結果"], M.T.LABEL_NAMED_ORIGINAL)
            self.assertEqual(r["P26"]["reason"], "no_same_value")

    def test_53_rates_use_the_rows_mapped_in_all_four_profiles_as_the_denominator(self):
        class Drop(M.StubBackend4):
            """P27E だけ、注入した文では claim を返さない(= 対応が付かない)。"""
            def verify(self, zb, profile, text):
                out = M.StubBackend4.verify(self, zb, profile, text)
                if profile == "P27E" and text != PLAIN_TEXT:
                    out["claims"] = []
                return out
        rec = self.w.inject(backend=Drop())
        per = rec["集計(各 profile で対応が付く行が分母)"]["T8_REL"]
        all4 = rec["集計(4 profile の全部で対応が付く行が分母。V-1〜V-3)"]["T8_REL"]
        self.assertGreater(per["P22"]["全体"]["対応が付く"], 0)
        self.assertEqual(per["P27E"]["全体"]["対応が付く"], 0)
        self.assertEqual(all4["P22"]["全体"]["対応が付く"], 0)           # 4 profile の全部で対応が付く行だけが分母
        self.assertEqual(rec["4 profile の全部で対応が付く行"], {"T1_VALUE": 0, "T8_REL": 0})
        ok = self.w.inject(out=os.path.join(self.tmp, "o", "ok.json"), outside_dir=os.path.join(self.tmp, "outside_ok"))
        n = sum(1 for r in ok["行"] if r["型"] == "T8_REL")
        self.assertEqual(ok["集計(4 profile の全部で対応が付く行が分母。V-1〜V-3)"]["T8_REL"]["P27E"]["全体"]["対応が付く"], n)
        self.assertEqual(ok["4 profile の全部で対応が付く行"]["T8_REL"], n)
        self.assertEqual(ok["集計(4 profile の全部で対応が付く行が分母。V-1〜V-3)"]["T8_REL"][M.T.LABEL_PASS if False else "P22"]["全体"][M.T.LABEL_NAMED_ORIGINAL],
                         {"件": n, "分母": n, "率": 100.0})

    def test_54_cap_is_40_per_type_per_doc(self):
        self.assertEqual(M.INJECT_CAP, 40)
        self.assertEqual(M.T.INJECT_CAP, 40)
        rec = self.big.inject(docs=[EVAL[0]])
        rows = rec["行"]
        self.assertEqual(sum(1 for r in rows if r["型"] == "T1_VALUE"), 40)
        self.assertEqual(sum(1 for r in rows if r["型"] == "T8_REL"), 40)
        c = rec["書類別の数え"][EVAL[0]]
        self.assertGreaterEqual(c["T8_REL"]["作れる site"], 41)
        self.assertEqual(c["T8_REL"]["採った"], 40)
        self.assertEqual(c["T1_VALUE"]["採った"], 40)
        small = self.big.inject(docs=[EVAL[0]], cap=7, out=os.path.join(self.tmp, "o", "cap7.json"), outside_dir=os.path.join(self.tmp, "outside_c7"))
        self.assertEqual(sum(1 for r in small["行"] if r["型"] == "T8_REL"), 7)
        self.assertEqual(sum(1 for r in small["行"] if r["型"] == "T1_VALUE"), 7)

    def test_55_round_trip_is_in_the_record_and_a_broken_revert_stops_without_a_record(self):
        rec = self.big.inject(docs=[EVAL[0]], cap=3)
        rt = rec["round-trip"]
        self.assertTrue(rt["注入した字を元に戻すと無改変の文と byte 一致"] is True)
        self.assertEqual(rt["確かめた注入の数"], 6)
        self.assertEqual(rt["確かめた注入の数"], sum(rec["書類別の数え"][EVAL[0]][t]["採った"] for t in M.INJECT_TYPES))
        real_revert = M.T.IJ.revert
        for broken in ("T8_REL", "T1_VALUE"):
            out = os.path.join(self.tmp, "o", "rt_%s.json" % broken)

            def revert(tampered, chosen, placements, original, broken=broken):
                if chosen[0]["type"] == broken:
                    return original + u"。"
                return real_revert(tampered, chosen, placements, original)
            with mock.patch.object(M.T.IJ, "revert", revert):
                with self.assertRaises(M.Stop) as cm:
                    self.big.inject(docs=[EVAL[0]], cap=2, out=out, outside_dir=os.path.join(self.tmp, "outside_rt_" + broken))
            self.assertIn("round-trip", str(cm.exception))
            self.assertFalse(os.path.exists(out))
            self.assertFalse(os.path.exists(os.path.join(self.tmp, "outside_rt_" + broken)))

    def test_56_t1_sites_are_what_inject_select_returns_for_the_seed(self):
        be = M.StubBackend4()
        refs = be.refs(os.path.join(self.big.zip_dir, EVAL[0] + ".zip"), EVAL[0], None)
        want, _c, _a, _w = M.T.IJ.select(BIG_TEXT, refs, "xbrl", "test-seed", EVAL[0], 40, types=["T1_VALUE"])
        self.big.inject(docs=[EVAL[0]])
        full = json.load(io.open(os.path.join(self.big.outside, "inject_full.json"), encoding="utf-8"))["seed 以外の注入の字"]
        got = [x for x in full if "-T1-" in x["id"]]
        self.assertEqual([x["id"] for x in got], [w["id"] for w in want])
        self.assertEqual([x["後の字"] for x in got], [w["replacement"] for w in want])

    def test_57_the_seed_comes_from_verify_seed_sealed_on_the_measure_seed_file(self):
        called = []

        def fake(path):
            called.append(path)
            raise M.T.IJ.SealError("not sealed")
        with mock.patch.object(M.T.IJ, "verify_seed_sealed", fake):
            with self.assertRaises(M.T.IJ.SealError):
                M.run_inject(**self.w.common(work_root=os.path.join(self.tmp, "w")))
        self.assertEqual([os.path.basename(p) for p in called], ["SEED.json"])
        self.assertEqual(os.path.dirname(called[0]), os.path.dirname(SCRIPT))
        self.assertFalse(os.path.exists(self.w.out))
        rec = self.w.inject(seed_fn=lambda path: ("seed-q", {"sealed_in_commit": "c" * 40, "seed_file_sha256": "d" * 64}))
        self.assertEqual(rec["種"], {"file": "measure/SEED.json", "sealed_in_commit": "c" * 40, "seed_file_sha256": "d" * 64})
        a = self.big.inject(docs=[EVAL[0]], seed_fn=lambda p: ("seed-1", {}))
        b = self.big.inject(docs=[EVAL[0]], seed_fn=lambda p: ("seed-2", {}), out=os.path.join(self.tmp, "o", "s2.json"), outside_dir=os.path.join(self.tmp, "outside_s2"))
        self.assertNotEqual([(r["型"], r["基準の claim"], r.get("r")) for r in a["行"]], [(r["型"], r["基準の claim"], r.get("r")) for r in b["行"]])   # 種が変われば別の site・別の r

    def test_58_record_has_no_injected_chars_and_the_outside_file_has_them(self):
        rec = self.w.inject()
        txt = self.w.record_text()
        full_path = os.path.join(self.w.outside, "inject_full.json")
        full = json.load(io.open(full_path, encoding="utf-8"))["seed 以外の注入の字"]
        self.assertTrue(full)
        self.assertEqual(rec["repo の外に置いたもの"]["注入の字・新しい値"]["sha256"], sha(open(full_path, "rb").read()))
        self.assertEqual(sorted(set(k for k in M.T.walk_keys(rec) if k in M.T.FORBIDDEN_RECORD_KEYS)), [])
        for k in ('"元の字"', '"後の字"', '"新しい値"', '"replacement"', '"new_value"'):
            self.assertNotIn(k, txt)
        self.assertNotIn(SENTINEL, txt)
        self.assertNotIn(SENTINEL_DB, txt)
        for row in rec["行"]:
            self.assertEqual(sorted(k for k in row if k not in ("r", "r を決めた回")), sorted(["P22", "P26", "P27", "P27E", "docID", "id", "基準の claim", "型", "文体"]))

    def test_59_multi_process_matches_single_process(self):
        a = self.w.inject(docs=EVAL[:2])
        b = self.w.inject(docs=EVAL[:2], procs=2, out=os.path.join(self.tmp, "o", "p2.json"), outside_dir=os.path.join(self.tmp, "outside_p2"))
        self.assertEqual(a["行"], b["行"])
        self.assertEqual(a["書類別の数え"], b["書類別の数え"])
        self.assertEqual(M.T.PROFILES, M.PROFILES)

    def test_59b_default_work_folder_is_under_TMPDIR(self):
        seen = []

        class Spy(M.StubBackend4):
            def refs(self, zip_path, doc, work):
                seen.append(work)
                return M.StubBackend4.refs(self, zip_path, doc, work)
        tmpdir = os.path.join(self.tmp, "tmpdir")
        os.makedirs(tmpdir)
        with mock.patch.dict(os.environ, {"TMPDIR": tmpdir}):
            self.w.inject(backend=Spy(), work_root=None)
        self.assertTrue(seen)
        for s in seen:
            self.assertTrue(os.path.realpath(s).startswith(os.path.realpath(tmpdir) + os.sep), s)


class TestReconcile(Base):
    def setUp(self):
        Base.setUp(self)
        self.jrec = self.w.judge()
        self.judge_path = self.w.out
        self.w.judge_path = self.judge_path
        self.w.out = os.path.join(self.tmp, "out", "readings.json")
        self.keys = [r["行"] for r in self.jrec["読む行"]]
        self.conds = dict((r["行"], r["条件"]) for r in self.jrec["読む行"])
        self.assertEqual(len(self.keys), 6)

    def seats(self, a_labels, b_labels):
        return self.w.seat_file("a", a_labels), self.w.seat_file("b", b_labels)

    def test_60_the_stage1_reconcile_pieces_are_used(self):
        self.assertIs(M.combine, M.T.combine)
        self.assertIs(M.load_seat, M.T.load_seat)
        self.assertIs(M.validate_label, M.T.validate_label)
        self.assertEqual(M.combine(("道具", "道1"), ("道具", "道5")), ("道具", "分からない"))

    def test_61_reconcile_run_writes_labels_only_and_free_text_outside_with_per_condition_counts(self):
        a_l, b_l = [], []
        for k in self.keys:
            if M.COND_K3 in self.conds[k]:
                a_l.append(label(k, "道具", "道1", why=SENTINEL_REASON))
                b_l.append(label(k, "道具", "道1"))
            else:
                a_l.append(label(k, "文", "文2"))
                b_l.append(label(k, "道具", "道3"))
        a, b = self.seats(a_l, b_l)
        rec = self.w.reconcile(a, b)
        rows = dict((r["行"], r) for r in rec["行"])
        for k in self.keys:
            self.assertEqual(rows[k]["条件"], self.conds[k])
            if M.COND_K3 in self.conds[k]:
                self.assertEqual(rows[k]["合わせた"], {"側": "道具", "細目": "道1"})
            else:
                self.assertEqual(rows[k]["合わせた"], {"側": "分からない", "細目": None})
        s = rec["集計"]
        self.assertEqual(s["読む行"], 6)
        self.assertEqual(s["2 席の側が一致した行"], {"件": 3, "分母": 6, "率": 50.0})
        self.assertEqual(s["合わせた側の内訳"], {"文": 0, "道具": 3, "分からない": 3})
        self.assertEqual(s["合わせた側が道具の行"], 3)
        by = s["条件ごと(重なる)"]
        self.assertEqual(by[M.COND_K3]["合わせた側が道具の行"], 3)
        self.assertEqual(by[M.COND_K4]["合わせた側が道具の行"], 0)
        self.assertEqual(by[M.COND_K4]["合わせた側の内訳"], {"文": 0, "道具": 0, "分からない": 3})
        self.assertEqual(by[M.COND_K3]["行"] + by[M.COND_K4]["行"], 6)
        txt = self.w.record_text()
        self.assertNotIn(SENTINEL_REASON, txt)
        free = io.open(os.path.join(self.w.outside, "readings_free_text.json"), encoding="utf-8").read()
        self.assertIn(SENTINEL_REASON, free)
        self.assertEqual(rec["repo の外に置いたもの"]["道5 の形と各席の理由の文"]["sha256"], sha(open(os.path.join(self.w.outside, "readings_free_text.json"), "rb").read()))
        self.assertEqual(rec["入力"]["席1 の札の file の sha256"], sha(open(a, "rb").read()))
        self.assertEqual(rec["入力"]["判定の記録の sha256"], sha(open(self.judge_path, "rb").read()))
        self.assertEqual(sorted(set(k for k in M.T.walk_keys(rec) if k in M.T.FORBIDDEN_RECORD_KEYS)), [])
        self.assertEqual(rec["HEAD の commit"], GIT["HEAD"])
        self.assertEqual(rec["E の commit"], GIT["E"])

    def test_62_rows_and_labels_must_be_one_to_one_and_words_are_checked(self):
        full = [label(k, "文", "文1") for k in self.keys]
        a = self.w.seat_file("a", full)
        for labels in (full[:5], full + [label(DOC_PREFIX + "NONE01:N001", "文", "文1")], full + [full[0]]):
            b = self.w.seat_file("b", labels)
            with self.assertRaises(M.Stop):
                self.w.reconcile(a, b)
            self.assertFalse(os.path.exists(self.w.out))
            self.assertFalse(os.path.exists(os.path.join(self.w.outside, "readings_free_text.json")))
        with self.assertRaises(M.Stop):
            self.w.reconcile(a, self.w.seat_file("b", [label(self.keys[0], "文", "文9")] + full[1:]))
        self.assertFalse(os.path.exists(self.w.out))

    def test_63_summary_counts_the_tool_side_per_condition_from_crafted_rows(self):
        def row(side_a, side_b, side, det, conds):
            return {"行": "x", "条件": conds, "席1": {"側": side_a}, "席2": {"側": side_b}, "合わせた": {"側": side, "細目": det}}
        rows = [row("道具", "道具", "道具", "道1", [M.COND_K3]), row("道具", "道具", "道具", "道5", [M.COND_K3, M.COND_K4]),
                row("文", "道具", "分からない", None, [M.COND_K4]), row("文", "文", "文", "文2", [M.COND_K4])]
        s = M.readings_summary(rows)
        self.assertEqual(s["合わせた側が道具の行"], 2)
        self.assertEqual(s["条件ごと(重なる)"][M.COND_K3], {"行": 2, "合わせた側の内訳": {"文": 0, "道具": 2, "分からない": 0}, "合わせた側が道具の行": 2})
        self.assertEqual(s["条件ごと(重なる)"][M.COND_K4], {"行": 3, "合わせた側の内訳": {"文": 1, "道具": 1, "分からない": 1}, "合わせた側が道具の行": 1})
        self.assertEqual(s["合わせた札が文2の行"], 1)
        self.assertEqual(s["合わせた細目が付いた道具の行"]["道1〜道4"], {"件": 1, "分母": 2, "率": 50.0})


class TestRecords(Base):
    """記録 3 つが段 1 の write_record の検査を通り、禁止欄が無く、頭の欄が揃う。偽の抜粋を足した写しで赤。"""

    def make_all(self):
        j = self.w.judge()
        self.w.judge_path = self.w.out
        jp = self.w.out
        self.w.out = os.path.join(self.tmp, "out", "inj.json")
        i = self.w.inject(docs=EVAL)
        ip = self.w.out
        a = self.w.seat_file("a", [label(k, "道具", "道1", why=SENTINEL_REASON) for k in [r["行"] for r in j["読む行"]]])
        b = self.w.seat_file("b", [label(k, "道具", "道1", why=SENTINEL_REASON) for k in [r["行"] for r in j["読む行"]]])
        self.w.out = os.path.join(self.tmp, "out", "rd.json")
        r = self.w.reconcile(a, b)
        return (j, jp), (i, ip), (r, self.w.out)

    def problems(self, rec, extra_texts=()):
        """記録が repo に置ける形か(段 1 の検査 + 文・DB の字が混ざっていないこと)。問題の一覧。"""
        out = []
        out += ["禁止欄:" + k for k in sorted(set(k for k in M.T.walk_keys(rec) if k in M.T.FORBIDDEN_RECORD_KEYS))]
        out += M.T.record_key_leaks(rec)
        txt = json.dumps(rec, ensure_ascii=False)
        out += ["文の字:" + s for s in (SENTINEL, SENTINEL_DB, SENTINEL_REASON) + tuple(extra_texts) if s in txt]
        return out

    def test_70_the_three_records_pass_the_write_record_checks_and_have_the_head_fields(self):
        triples = self.make_all()
        for rec, path in triples:
            self.assertEqual(self.problems(rec), [], path)
            self.assertEqual(self.problems(json.load(io.open(path, encoding="utf-8"))), [], path)
            for key, g in (("HEAD の commit", "HEAD"), ("W の commit", "W"), ("S2 の commit", "S2"), ("E の commit", "E"), ("T の commit", "T")):
                self.assertEqual(rec[key], GIT[g])
            self.assertIn("engine の指紋", rec)
            self.assertTrue(rec["cache の前後"]["変化なし"])
            self.assertEqual(rec["cache の前後"]["前"]["既存の cache"]["件数"], 3)
            self.assertEqual(rec["cache の前後"]["前"]["ZIP の folder"]["件数"], 5)
            outside = rec["repo の外に置いたもの"]
            self.assertTrue(outside["folder"])
            self.assertEqual(rec["対象の docID"], EVAL)
        (j, _), (i, _), (r, _) = triples
        self.assertEqual(j["repo の外に置いたもの"]["全部の欄(span・subject・value・recomputed を含む)"]["sha256"],
                         sha(open(os.path.join(self.w.outside, "judge_full.json"), "rb").read()))
        self.assertEqual(i["repo の外に置いたもの"]["注入の字・新しい値"]["sha256"], sha(open(os.path.join(self.w.outside, "inject_full.json"), "rb").read()))
        self.assertEqual(r["repo の外に置いたもの"]["道5 の形と各席の理由の文"]["sha256"],
                         sha(open(os.path.join(self.w.outside, "readings_free_text.json"), "rb").read()))

    def test_71_a_copy_with_a_fake_excerpt_is_red(self):
        triples = self.make_all()
        for rec, _path in triples:
            for doctored in (dict(rec, 抜粋=u"…%s は50億円…" % SENTINEL), dict(rec, span=u"窓"), dict(rec, 余り=FAKE_KEY),
                             dict(rec, 理由=SENTINEL_REASON)):
                self.assertNotEqual(self.problems(doctored), [])
            with self.assertRaises(M.Stop):
                M.write_record(os.path.join(self.tmp, "x1.json"), dict(rec, span=u"窓"))
            with self.assertRaises(M.Stop):
                M.write_record(os.path.join(self.tmp, "x2.json"), dict(rec, 余り=FAKE_KEY))
            with self.assertRaises(M.Stop):
                M.write_record(os.path.join(self.tmp, "x3.json"), dict(rec, nested=[{"subject": u"科目"}]))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "x1.json")))

    def test_72_commit_keys_are_exempt_only_when_they_are_forty_hex_digits(self):
        out = os.path.join(self.tmp, "k", "c.json")
        ok = {"HEAD の commit": H("a"), "W の commit": H("b"), "T の commit": H("c"), "S2 の commit": H("d"), "E の commit": H("e")}
        M.write_record(out, ok)
        self.assertTrue(os.path.exists(out))
        for key in ok:
            with self.assertRaises(M.Stop, msg=key):
                M.write_record(os.path.join(self.tmp, "k", key + ".json"), dict(ok, **{key: "0123456789abcdef" * 3}))
        with self.assertRaises(M.Stop):
            M.write_record(os.path.join(self.tmp, "k", "memo.json"), {"memo": H("a")})
        with self.assertRaises(M.Stop):
            M.write_record(os.path.join(self.tmp, "k", "key.json"), {"HEAD の commit": H("a")}, key_value=H("a"))

    def test_73_a_record_written_by_a_run_is_scanned_again_after_writing(self):
        real = M.T.write_text

        def corrupt(path, text):
            if path != self.w.out:
                return real(path, text)
            obj = json.loads(text)
            obj["混入"] = FAKE_KEY
            real(path, json.dumps(obj))
        with mock.patch.object(M.T, "write_text", corrupt):
            with self.assertRaises(M.Stop):
                self.w.judge()
        self.assertFalse(os.path.exists(self.w.out))


class TestOutput(Base):
    def test_80_stdout_and_say_carry_no_sentinel_chars_in_any_subcommand(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.w = self.w
            j = self.w.judge(say=print)
            self.w.judge_path = self.w.out
            self.w.out = os.path.join(self.tmp, "out", "inj.json")
            self.w.inject(say=print)
            a = self.w.seat_file("a", [label(r["行"], "道具", "道1", why=SENTINEL_REASON) for r in j["読む行"]])
            b = self.w.seat_file("b", [label(r["行"], "道具", "道1", why=SENTINEL_REASON) for r in j["読む行"]])
            self.w.out = os.path.join(self.tmp, "out", "rd.json")
            self.w.reconcile(a, b, say=print)
        printed = buf.getvalue() + "\n".join(self.w.log)
        self.assertTrue(buf.getvalue())
        for s in (SENTINEL, SENTINEL_DB, SENTINEL_REASON, u"億円", u"営業", u"売上"):
            self.assertNotIn(s, printed, s)
        # 件数・path は出る
        self.assertIn("読む行 6", buf.getvalue())

    def test_81_cli_dry_run_runs_the_whole_path_and_stdout_is_clean(self):
        base = ["--root", self.w.root, "--git-dir", ROOT, "--zip-dir", self.w.zip_dir, "--cache-root", self.w.cache_root,
                "--reports-dir", self.w.reports_dir, "--db-dir", self.w.db_dir,
                "--existing-cache-dir", self.w.existing, "--outside-dir", self.w.outside, "--dry-run"]
        buf = io.StringIO()
        with mock.patch.object(M, "preflight", lambda run, vocab=None: dict(GIT)):
            with contextlib.redirect_stdout(buf):
                M.main(["judge", "--out", self.w.out] + base)
                rec = self.w.record()
                self.assertTrue(rec["dry_run"])
                self.assertEqual(rec["backend"], "stub")
                with mock.patch.object(M.T.IJ, "verify_seed_sealed", lambda path: ("test-seed", {"sealed_in_commit": "x", "seed_file_sha256": "y"})):
                    M.main(["inject", "--out", os.path.join(self.tmp, "o", "inj.json"), "--work-dir", os.path.join(self.tmp, "wk")] + base)
                keys = [r["行"] for r in rec["読む行"]]
                a = self.w.seat_file("a", [label(k, "文", "文1") for k in keys])
                b = self.w.seat_file("b", [label(k, "文", "文1") for k in keys])
                M.main(["reconcile", "--out", os.path.join(self.tmp, "o", "rd.json"), "--seat-a", a, "--seat-b", b, "--judge-record", self.w.out] + base)
        for s in (SENTINEL, SENTINEL_DB, u"億円"):
            self.assertNotIn(s, buf.getvalue())
        self.assertTrue(json.load(io.open(os.path.join(self.tmp, "o", "inj.json"), encoding="utf-8"))["行"])
        self.assertEqual(len(json.load(io.open(os.path.join(self.tmp, "o", "rd.json"), encoding="utf-8"))["行"]), 6)

    def test_82_cli_without_explicit_folders_stops_instead_of_touching_the_home(self):
        with self.assertRaises(M.Stop):
            M.main(["judge", "--root", self.w.root, "--dry-run", "--out", self.w.out])
        self.nothing_written()

    def test_83_cli_tuning_doc_on_the_command_line_stops(self):
        with open_spy() as opened:
            with self.assertRaises(M.Stop):
                M.main(["judge", "--root", self.w.root, "--git-dir", ROOT, "--zip-dir", self.w.zip_dir, "--cache-root", self.w.cache_root,
                        "--reports-dir", self.w.reports_dir, "--db-dir", self.w.db_dir,
                        "--existing-cache-dir", self.w.existing, "--outside-dir", self.w.outside, "--dry-run", "--out", self.w.out, "--docs", TUNE[0]])
        self.assertEqual([p for p in opened if self.w.reports_dir in p or self.w.db_dir in p or self.w.zip_dir in p], [])
        self.nothing_written()


class TestScriptSource(unittest.TestCase):
    def test_90_the_script_reads_no_secret_and_does_not_touch_the_network(self):
        tree = ast.parse(io.open(SCRIPT, encoding="utf-8").read())
        imported = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                imported |= set(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                imported.add((n.module or "").split(".")[0])
        self.assertFalse(imported & {"urllib", "socket", "http", "requests", "ssl", "anthropic", "openai"}, imported)
        src = io.open(SCRIPT, encoding="utf-8").read()
        self.assertEqual(src.count("os.environ"), 1)
        self.assertIn('os.environ.get("TMPDIR")', src)

    def test_91_the_docstring_states_the_conditions(self):
        doc = M.__doc__
        for s in ("評価用の文を開く条件", "開かずに止める条件", "repo に入れない欄", "span", "subject", "value", "recomputed"):
            self.assertIn(s, doc)

    def test_92_constants_match_the_seal(self):
        self.assertEqual(M.PROFILES, ("P22", "P26", "P27", "P27E"))
        self.assertEqual(M.JUDGE_REL, os.path.join("fixtures", "xbrl", "p27", "eval_2026-10-27.json"))
        self.assertEqual(M.INJECT_REL, os.path.join("fixtures", "xbrl", "p27", "eval_inject_2026-10-27.json"))
        self.assertEqual(M.READINGS_REL, os.path.join("fixtures", "xbrl", "p27", "eval_readings_2026-10-27.json"))
        self.assertEqual(M.E_PICKAXE, 'PROFILES["P27E"]')
        self.assertEqual(M.SEAL, "audit-core/docs/XBRL_P27_SEAL_2026-10-27.md")
        self.assertEqual(M.INJECT_TYPES, ("T1_VALUE", "T8_REL"))
        self.assertEqual(M.COND_K3, "P27E_VALUE_MISMATCH_and_P26_not_VALUE_MISMATCH")
        self.assertEqual(M.COND_K4, "P26_GROUNDED_and_P27_not_GROUNDED")
        self.assertEqual(M.RULE_KEYS, tuple(["C2 per_unit_counter", "C3 future_period", "C1 の窓に入った claim", "C1 の窓に入って other_concept になった claim", "B relative_within_rho"]))

    def test_93_stage1_and_regress97_and_rerun_scripts_are_not_the_eval_script(self):
        # 段 1・97 書類・E の再現の script は、この script が読むだけ(中身は別の門が縛る)。この script のその sha256 は記録の頭に入る
        for name in ("xbrl_p27_tune_2026-10-27.py", "xbrl_p27_regress97_2026-10-27.py"):
            self.assertTrue(os.path.exists(os.path.join(os.path.dirname(SCRIPT), name)))


if __name__ == "__main__":
    unittest.main()
