# -*- coding: utf-8 -*-
"""取得 script(measure/xbrl_fresh_fetch_2026-10-21.py)の試験(封 docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md §1-3・§1-4)。
通信しない・鍵を使わない(偽の鍵)・本物の cache に書かない(読むだけ)。通信の関数 fetcher と待ちの関数 sleep を差し替える。"""
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.environ.get("FRESH_FETCH_SCRIPT", os.path.join(ROOT, "measure", "xbrl_fresh_fetch_2026-10-21.py"))
REAL_CACHE = os.path.expanduser("~/.cache/audit-core/edinet")
REAL_DRAW = os.path.join(ROOT, "fixtures", "xbrl", "fresh", "draw_2026-10-21.json")

spec = importlib.util.spec_from_file_location("fresh_fetch", SCRIPT)
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)

# 偽の鍵(固定の字面を file に置かない)
FAKE_KEY = "".join(["Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7", "cF0xR"])      # 32 字
FAKE_HEX_KEY = "".join(["0123456789", "abcdef0123456789", "abcdef"])   # 32 桁の 16 進


def make_zip(n=1):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("x%d.txt" % n, "dummy")
    return b.getvalue()


class Env(object):
    def __init__(self):
        self.tmp = tempfile.mkdtemp(prefix="freshfetch_", dir=os.environ.get("TMPDIR"))
        self.cache = os.path.join(self.tmp, "fresh")            # 新しい folder(取得した ZIP の置き場所)
        os.makedirs(self.cache)
        self.existing = os.path.join(self.tmp, "existing")      # 既存の cache の代わり(取得は 1 file も書かない)
        os.makedirs(self.existing)
        self.docs = ["S1000%03d" % i for i in range(40)]
        self.draw = os.path.join(self.tmp, "draw.json")
        json.dump({F.DRAW_KEY: self.docs}, io.open(self.draw, "w", encoding="utf-8"))
        self.out = os.path.join(self.tmp, "out", "fetched.json")
        self.calls = []
        self.sleeps = []
        self.log = []

    def cp(self, d):
        return os.path.join(self.cache, d + ".zip")

    def ecp(self, d):
        return os.path.join(self.existing, d + ".zip")

    def fetcher(self, behaviour=None):
        def f(d):
            self.calls.append(d)
            b = (behaviour or (lambda d, k: make_zip()))(d, self.calls.count(d))
            if isinstance(b, BaseException):
                raise b
            with open(self.cp(d), "wb") as fh:
                fh.write(b)
        return f

    def run(self, env=None, fetcher=None, counter=None, **kw):
        return F.run(root=ROOT, draw=self.draw, out=self.out,
                     env={F.KEY_NAME: FAKE_KEY} if env is None else env,
                     fetcher=fetcher or self.fetcher(), counter=counter or (lambda b: (5, "P22")),
                     sleep=self.sleeps.append, fetch_dir=self.cache, fresh_path_of=self.cp,
                     existing_path_of=self.ecp, say=self.log.append, **kw)

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class T(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.cleanup)

    def read(self):
        return json.load(io.open(self.e.out, encoding="utf-8"))

    # --- 止まる所 ---
    def test_01_no_key_stops_before_any_fetch(self):
        for env in ({}, {F.KEY_NAME: ""}):
            with self.assertRaises(SystemExit):
                self.e.run(env=env)
        self.assertEqual(self.e.calls, [])
        self.assertFalse(os.path.exists(self.e.out))
        self.assertEqual(os.listdir(self.e.cache), [])

    def test_02_cached_docid_stops_before_any_fetch(self):
        with open(self.e.ecp(self.e.docs[17]), "wb") as fh:    # 既存の cache に、40 件の途中の 1 件
            fh.write(make_zip())
        with self.assertRaises(SystemExit) as cm:
            self.e.run()
        self.assertIn(self.e.docs[17], str(cm.exception))
        self.assertEqual(self.e.calls, [])                       # 1 件も取得していない
        self.assertFalse(os.path.exists(self.e.out))

    def test_03_existing_record_is_not_overwritten(self):
        os.makedirs(os.path.dirname(self.e.out))
        open(self.e.out, "w").write("{}")
        with self.assertRaises(SystemExit):
            self.e.run()
        self.assertEqual(self.e.calls, [])

    def test_04_draw_not_40_stops(self):
        json.dump({F.DRAW_KEY: self.e.docs[:39]}, io.open(self.e.draw, "w"))
        with self.assertRaises(SystemExit):
            self.e.run()
        self.assertEqual(self.e.calls, [])

    # --- ZIP でない応答 ---
    def test_05_non_zip_is_failure_cache_removed_body_not_recorded(self):
        body = b'{"statusCode":401,"message":"Access denied marker-%s"}' % FAKE_KEY.encode()

        def beh(d, k):
            return body if d == self.e.docs[3] else make_zip()
        rec = self.e.run(fetcher=self.e.fetcher(beh))
        r = rec["取得した書類"][3]
        self.assertEqual(r["取得"], "失敗")
        self.assertEqual(r["応答の長さ"], len(body))
        self.assertFalse(os.path.exists(self.e.cp(self.e.docs[3])))     # cache を消した
        self.assertNotIn("sha256", r)
        self.assertEqual(r["試行回数"], 1)                                # 再試行しない
        self.assertNotIn(FAKE_KEY, io.open(self.e.out, encoding="utf-8").read())
        self.assertNotIn("Access denied", io.open(self.e.out, encoding="utf-8").read())
        self.assertFalse(r["使う"])
        self.assertEqual(rec["取得に失敗"], 1)
        self.assertEqual(rec["使う件数"], 30)                             # 39 件のうち先頭 30 件

    def test_06_three_consecutive_non_zip_stops_and_writes_no_record(self):
        rec_calls = []

        def beh(d, k):
            rec_calls.append(d)
            return b'{"statusCode":401}'
        with self.assertRaises(SystemExit):
            self.e.run(fetcher=self.e.fetcher(beh))
        self.assertEqual(len(rec_calls), 3)
        self.assertFalse(os.path.exists(self.e.out))
        self.assertEqual(os.listdir(self.e.cache), [])

    def test_07_non_consecutive_non_zip_does_not_stop(self):
        bad = {self.e.docs[1], self.e.docs[3], self.e.docs[5]}
        rec = self.e.run(fetcher=self.e.fetcher(lambda d, k: b"{}" if d in bad else make_zip()))
        self.assertEqual(rec["取得に失敗"], 3)

    # --- 通信の失敗 ---
    def test_08_transient_error_retried_then_ok(self):
        def beh(d, k):
            if d == self.e.docs[0] and k < 3:
                return OSError("boom " + FAKE_KEY)       # 文に鍵が入っても記録しない
            return make_zip()
        rec = self.e.run(fetcher=self.e.fetcher(beh))
        r = rec["取得した書類"][0]
        self.assertEqual((r["取得"], r["試行回数"]), ("成功", 3))
        self.assertEqual(self.e.sleeps[:2], list(F.BACKOFF_SEC))
        self.assertNotIn(FAKE_KEY, io.open(self.e.out, encoding="utf-8").read())

    def test_09_gives_up_after_max_attempts_records_type_only(self):
        def beh(d, k):
            return OSError("url has Subscription-Key=" + FAKE_KEY) if d == self.e.docs[2] else make_zip()
        rec = self.e.run(fetcher=self.e.fetcher(beh))
        r = rec["取得した書類"][2]
        self.assertEqual((r["取得"], r["失敗の型"], r["試行回数"]), ("失敗", "OSError", F.MAX_ATTEMPTS))
        t = io.open(self.e.out, encoding="utf-8").read()
        self.assertNotIn(FAKE_KEY, t)
        self.assertNotIn("Subscription-Key", t)
        self.assertEqual(self.e.calls.count(self.e.docs[2]), F.MAX_ATTEMPTS)

    def test_10_http_4xx_not_retried_5xx_retried(self):
        class H(Exception):
            def __init__(self, code):
                self.code = code
        def beh(d, k):
            if d == self.e.docs[0]:
                return H(404)
            if d == self.e.docs[1]:
                return H(503)
            return make_zip()
        rec = self.e.run(fetcher=self.e.fetcher(beh))
        a, b = rec["取得した書類"][0], rec["取得した書類"][1]
        self.assertEqual((a["失敗の型"], a["試行回数"]), ("H 404", 1))
        self.assertEqual((b["失敗の型"], b["試行回数"]), ("H 503", F.MAX_ATTEMPTS))

    def test_11_interval_between_documents(self):
        self.e.run(interval=2.5)
        self.assertEqual(self.e.sleeps, [2.5] * 39)

    # --- 使う 30 件 ---
    def test_12_first_30_with_claims_in_drawn_order(self):
        claims = {d: (0 if i in (0, 4, 9) else 7) for i, d in enumerate(self.e.docs)}
        order = {}

        def fetcher(d):
            order[len(order)] = d
            self.e.fetcher()(d)
        # counter は blob から docID を引けないので、取得順に対応づけた系列を返す
        seq = iter([claims[d] for d in self.e.docs])
        rec = self.e.run(fetcher=fetcher, counter=lambda b: (next(seq), "P22"))
        used = rec["使う書類"]
        self.assertEqual(len(used), 30)
        self.assertEqual(used, [d for i, d in enumerate(self.e.docs) if i not in (0, 4, 9)][:30])
        self.assertEqual([r["使う順"] for r in rec["取得した書類"] if r["使う"]], list(range(1, 31)))
        self.assertEqual(list(order.values()), self.e.docs)            # 引いた順
        self.assertEqual(rec["足りない件数"], 0)
        self.assertEqual(rec["claim を数えた抽出"]["profile"], "P22")

    def test_13_shortfall_is_recorded_not_redrawn(self):
        seq = iter([0 if i % 2 else 3 for i in range(40)])       # 20 件だけ claim 1 以上
        rec = self.e.run(counter=lambda b: (next(seq), "P22"))
        self.assertEqual((rec["使う件数"], rec["足りない件数"]), (20, 10))
        self.assertEqual(len(self.e.calls), 40)                  # 41 件目は引かない

    def test_14_extraction_failure_is_not_used_and_message_not_recorded(self):
        def counter(b):
            raise ValueError("secret " + FAKE_KEY)
        rec = self.e.run(counter=counter)
        self.assertEqual(rec["使う件数"], 0)
        self.assertEqual(rec["取得した書類"][0]["抽出の失敗"], "ValueError")
        self.assertNotIn(FAKE_KEY, io.open(self.e.out, encoding="utf-8").read())

    def test_15_record_fields(self):
        rec = self.e.run()
        r = rec["取得した書類"][0]
        for k in ("docID", "位置(引いた順)", "取得", "bytes", "sha256", "置いた file", "試行回数", "claims", "使う"):
            self.assertIn(k, r)
        self.assertEqual(len(r["sha256"]), 64)
        self.assertEqual(rec["置いた場所"]["folder"], F.display_path(os.path.abspath(self.e.cache)))
        self.assertTrue(r["置いた file"].endswith("/%s.zip" % self.e.docs[0]))
        self.assertEqual(rec["合計バイト"], sum(x["bytes"] for x in rec["取得した書類"]))
        self.assertFalse(os.path.exists(self.e.out + ".partial"))   # 完走したら進みの file は消える

    # --- 鍵の検査 ---
    def test_16_key_leak_check_catches_fake_keys(self):
        self.assertTrue(F.key_leaks('{"a": "%s"}' % FAKE_KEY))
        self.assertTrue(F.key_leaks('{"a": "%s"}' % FAKE_HEX_KEY))            # 32 桁 16 進も赤
        self.assertTrue(F.key_leaks("?Subscription-Key=abc"))
        self.assertTrue(F.key_leaks("EDINET_API_KEY=abcdefgh1"))
        self.assertTrue(F.key_leaks("short-but-exact", key_value="short-but-exact"))
        self.assertEqual(F.key_leaks('{"sha256": "%s"}' % ("ab" * 32)), [])    # sha256 の 64 桁は通す
        self.assertEqual(F.key_leaks("通常の文 S100YXFQ 12345"), [])

    def test_17_leak_in_record_blocks_write(self):
        # 書類の行に鍵らしい字が混ざる状況(例: docID に紛れる)を counter の profile 名で作る
        # 環境の鍵とは別の字(環境の鍵そのものの検査が先に当たって、32 字以上の英数字の検査の配線が隠れないように)
        other = "".join(["Qw3rTy6uIo9pAs2dFg5hJk8lZx1cVb", "4n"])      # 32 字
        self.assertNotEqual(other, FAKE_KEY)
        with self.assertRaises(SystemExit):
            self.e.run(counter=lambda b: (5, other))
        self.assertFalse(os.path.exists(self.e.out))

    def test_18_key_value_itself_in_record_blocks_write(self):
        with self.assertRaises(SystemExit):
            self.e.run(env={F.KEY_NAME: "P22"}, counter=lambda b: (5, "P22"))     # 短い鍵の値が記録に出る
        self.assertFalse(os.path.exists(self.e.out))

    def test_19_post_write_check_removes_file(self):
        calls = []
        real = F.key_leaks

        def fake(text, key_value=None):
            calls.append(1)
            return [] if len(calls) == 1 else ["after"]
        F.key_leaks = fake
        try:
            with self.assertRaises(SystemExit):
                self.e.run()
        finally:
            F.key_leaks = real
        self.assertFalse(os.path.exists(self.e.out))      # 書いた後の検査が赤なら消す

    def test_20_script_and_log_never_print_key(self):
        self.e.run()
        self.assertFalse([l for l in self.e.log if FAKE_KEY in str(l)])
        with io.open(SCRIPT, encoding="utf-8") as fh:
            src = fh.read()
        # 封の門 test_30 と同じ検査
        self.assertIsNone(re.search(r"\b[0-9a-f]{32}\b", src))
        self.assertIsNone(re.search(r"EDINET_API_KEY\s*=\s*['\"]?\w{8,}", src))
        self.assertNotIn("print(", src.replace("say(", ""))      # print を直接呼ばない

    # --- 中断からの続き ---
    def test_21_resume_after_interrupt_reuses_verified_files_only(self):
        n = []

        def beh(d, k):
            n.append(d)
            if len(n) == 6:
                return KeyboardInterrupt()
            return make_zip(len(n))
        with self.assertRaises(KeyboardInterrupt):
            self.e.run(fetcher=self.e.fetcher(beh))
        self.assertTrue(os.path.exists(self.e.out + ".partial"))
        self.assertFalse(os.path.exists(self.e.out))
        self.e.calls[:] = []
        rec = self.e.run()
        self.assertEqual(len(self.e.calls), 35)               # 取れた 5 件は取り直さない
        self.assertTrue(all(r.get("前回の続き") for r in rec["取得した書類"][:5]))
        # cache の中身が partial の sha256 と違えば止まる(別物に差し替わっている)
        shutil.rmtree(self.e.cache); os.makedirs(self.e.cache)
        os.remove(self.e.out)
        json.dump({"取得した書類": [{"docID": self.e.docs[0], "取得": "成功", "sha256": "0" * 64}]},
                  io.open(self.e.out + ".partial", "w"))
        open(self.e.cp(self.e.docs[0]), "wb").write(make_zip(99))
        with self.assertRaises(SystemExit):
            self.e.run()

    # --- 本物の draw と本物の書類(読むだけ) ---
    def test_22_real_draw_loads_and_none_is_cached(self):
        docs = F.load_draw(REAL_DRAW)
        self.assertEqual(len(docs), 40)
        cached = [d for d in docs if os.path.exists(os.path.join(REAL_CACHE, d + ".zip"))]
        # 取得の後も在ってはならない: 取得した書類は新しい folder にだけ置く(既存の cache は既存の門が数える)
        self.assertEqual(cached, [], "封の 40 件が既存の cache に在る")

    def test_23_default_counter_on_a_real_cached_document(self):
        sys.path.insert(0, ROOT)
        zs = sorted(f for f in os.listdir(REAL_CACHE) if f.endswith(".zip"))
        if not zs:
            self.skipTest("cache が無い")
        with open(os.path.join(REAL_CACHE, zs[0]), "rb") as fh:
            b = fh.read()
        n, profile = F.default_counter(b)
        self.assertIsInstance(n, int)
        from adapters.xbrl import vocabulary as V
        self.assertEqual(profile, V.DEFAULT_PROFILE)

    def test_24_cli_stops_without_key(self):
        import subprocess
        env = {k: v for k, v in os.environ.items() if k != F.KEY_NAME}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        out = os.path.join(self.e.tmp, "cli_out.json")
        p = subprocess.run([sys.executable, "-B", SCRIPT, "--root", ROOT, "--out", out],
                           env=env, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn(F.KEY_NAME, p.stderr)
        self.assertFalse(os.path.exists(out))


    def test_25_default_counter_passes_no_profile_so_the_default_extraction_is_counted(self):
        """封 §1-3「既定の抽出」= 取得時点の DEFAULT_PROFILE。P26 など旗つきの profile を script が自分で選ばない。
        verify_document を差し替え、引数に profile が渡らないことを見る(script は関数の中で import するので差し替えが届く)。"""
        sys.path.insert(0, ROOT)
        from adapters.xbrl import verify_document as VD
        seen = []

        def fake(*args, **kwargs):
            seen.append((args, kwargs))
            return {"document": {"claims": 7}, "profile": "marker"}
        real = VD.verify_document
        VD.verify_document = fake
        try:
            self.assertEqual(F.default_counter(b"zip-bytes"), (7, "marker"))
        finally:
            VD.verify_document = real
        self.assertEqual(seen, [((b"zip-bytes",), {})])
        # script が profile の名前の字(P20〜P26 など)を持たない(構造で見る: 文字列定数)
        import ast
        with io.open(SCRIPT, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        self.assertEqual([v for v in names if re.search(r"\bP[0-9]{2}\b", v)], [])


    # --- 置き場所(既存の cache には書かない) ---
    def test_26_unmatched_file_in_the_new_folder_stops(self):
        with open(self.e.cp(self.e.docs[5]), "wb") as fh:      # 新しい folder に在るが partial に記録が無い
            fh.write(make_zip())
        with self.assertRaises(SystemExit) as cm:
            self.e.run()
        self.assertIn(self.e.docs[5], str(cm.exception))
        self.assertEqual(self.e.calls, [])
        self.assertFalse(os.path.exists(self.e.out))

    def test_27_default_run_writes_nothing_to_the_existing_cache_under_a_swapped_home(self):
        """差し替えた HOME で、既定の置き場所と既定の fetcher(`adapters.xbrl.edinet.fetch`。urlopen だけ差し替える。通信しない)を通す。
        既存の cache(HOME/.cache/audit-core/edinet)には 1 file も書かれず、40 件は新しい folder にだけ置かれる。"""
        import subprocess
        home = os.path.join(self.e.tmp, "home")
        os.makedirs(home)
        out = os.path.join(self.e.tmp, "child_out.json")
        driver = (
            "import importlib.util, sys, urllib.request\n"
            "script, root, draw, out, key = sys.argv[1:6]\n"
            "spec = importlib.util.spec_from_file_location('ff', script)\n"
            "F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)\n"
            "class R(object):\n"
            "    def read(self): return %r\n"
            "urllib.request.urlopen = lambda url, timeout=None: R()\n"
            "import os; os.environ[F.KEY_NAME] = key      # edinet.fetch は鍵を環境変数から取る(偽の字)\n"
            "F.run(root=root, draw=draw, out=out, env={F.KEY_NAME: key}, counter=lambda b: (3, 'P22'),\n"
            "      sleep=lambda s: None, interval=0, say=lambda s: None)\n" % (make_zip(),))
        env = {k: v for k, v in os.environ.items() if k not in (F.KEY_NAME, "HOME")}
        env["HOME"] = home
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        p = subprocess.run([sys.executable, "-B", "-c", driver, SCRIPT, ROOT, self.e.draw, out, FAKE_KEY],
                           env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr[-500:])
        existing = os.path.join(home, ".cache", "audit-core", "edinet")
        fresh = os.path.join(home, ".cache", "audit-core", F.FRESH_DIR_NAME)
        written = sorted(os.path.relpath(os.path.join(d, f), home) for d, _, fs in os.walk(home) for f in fs)
        self.assertEqual(len(written), 40)
        self.assertTrue(all(w.startswith(os.path.join(".cache", "audit-core", F.FRESH_DIR_NAME) + os.sep) for w in written), written)
        self.assertEqual(sorted(os.listdir(fresh)), sorted(d + ".zip" for d in self.e.docs))
        self.assertFalse(os.path.exists(existing) and os.listdir(existing))      # 既存の cache は空のまま(folder も作らない)
        rec = json.load(io.open(out, encoding="utf-8"))
        self.assertEqual(rec["置いた場所"]["folder"], "~/.cache/audit-core/" + F.FRESH_DIR_NAME)
        self.assertEqual(rec["取得に成功"], 40)

    def test_28_default_fetch_dir_is_the_sealed_name_and_is_not_the_existing_cache(self):
        saved = os.environ.get("HOME")
        os.environ["HOME"] = "/nonexistent-home-for-test"
        try:
            self.assertEqual(F.default_fetch_dir(), "/nonexistent-home-for-test/.cache/audit-core/edinet-fresh-2026-10-21")
        finally:
            if saved is None:
                del os.environ["HOME"]
            else:
                os.environ["HOME"] = saved


    # --- 監査の REVISE で足した 4 本(黙った変異 M2a・M6b・M3b・M1f に対応) ---
    def test_29_default_fetcher_restores_cache_dir_on_success_and_on_exception(self):
        """default_fetcher は ED.CACHE_DIR を呼んでいる間だけ新しい folder に向け、成功でも例外でも元の値に戻す(finally)。
        urlopen と鍵の取り出しを差し替える(通信しない・環境の鍵は読まない)。"""
        from unittest import mock
        import urllib.request
        sys.path.insert(0, ROOT)
        from adapters.xbrl import edinet as ED
        sentinel = os.path.join(self.e.tmp, "sentinel_cache_dir")      # 元の値の目印(作らない・書かれない)
        target = os.path.join(self.e.tmp, "target")

        class R(object):
            def read(self_inner):
                return make_zip()

        def boom(url, timeout=None):
            raise OSError("boom")
        with mock.patch.object(ED, "_api_key", lambda: FAKE_KEY), mock.patch.object(ED, "CACHE_DIR", sentinel):
            with mock.patch.object(urllib.request, "urlopen", lambda url, timeout=None: R()):
                path = F.default_fetcher("S1000000", target)
            self.assertEqual(ED.CACHE_DIR, sentinel)                          # 成功: 戻った
            self.assertEqual(path, os.path.join(target, "S1000000.zip"))       # 書いたのは新しい folder
            self.assertTrue(os.path.exists(path))
            self.assertFalse(os.path.exists(sentinel))                         # 元の folder には書いていない
            with mock.patch.object(urllib.request, "urlopen", boom):
                with self.assertRaises(OSError):
                    F.default_fetcher("S1000001", target)
            self.assertEqual(ED.CACHE_DIR, sentinel)                          # 例外: 戻った

    def test_30_default_wiring_stops_when_a_drawn_docid_is_in_the_existing_cache(self):
        """差し替えた HOME の既存の cache(HOME/.cache/audit-core/edinet)に draw の docID を 1 つ置き、run を既定の配線
        (existing_path_of を渡さない)で走らせる。何も取得せずに止まる(urlopen の呼び出し 0)。"""
        import subprocess
        home = os.path.join(self.e.tmp, "home30")
        existing = os.path.join(home, ".cache", "audit-core", "edinet")
        os.makedirs(existing)
        with open(os.path.join(existing, self.e.docs[7] + ".zip"), "wb") as fh:
            fh.write(make_zip())
        out = os.path.join(self.e.tmp, "child30_out.json")
        driver = (
            "import importlib.util, sys, urllib.request, os\n"
            "script, root, draw, out, key = sys.argv[1:6]\n"
            "spec = importlib.util.spec_from_file_location('ff', script)\n"
            "F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)\n"
            "calls = []\n"
            "class R(object):\n"
            "    def read(self): return %r\n"
            "def urlopen(url, timeout=None):\n"
            "    calls.append(1); return R()\n"
            "urllib.request.urlopen = urlopen\n"
            "os.environ[F.KEY_NAME] = key\n"
            "try:\n"
            "    F.run(root=root, draw=draw, out=out, env={F.KEY_NAME: key}, counter=lambda b: (3, 'P22'),\n"
            "          sleep=lambda s: None, interval=0, say=lambda s: None)\n"
            "    print('RAN calls=%%d' %% len(calls))\n"
            "except F.Stop as e:\n"
            "    print('STOP calls=%%d %%s' %% (len(calls), e))\n" % (make_zip(),))
        env = {k: v for k, v in os.environ.items() if k not in (F.KEY_NAME, "HOME")}
        env["HOME"] = home
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        p = subprocess.run([sys.executable, "-B", "-c", driver, SCRIPT, ROOT, self.e.draw, out, FAKE_KEY],
                           env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr[-500:])
        self.assertTrue(p.stdout.startswith("STOP calls=0 "), p.stdout[:200])
        self.assertIn(self.e.docs[7], p.stdout)
        self.assertFalse(os.path.exists(out))
        self.assertFalse(os.path.exists(os.path.join(home, ".cache", "audit-core", F.FRESH_DIR_NAME)))

    def test_31_default_wiring_counts_with_the_default_profile(self):
        """fetcher と counter を省いた既定の配線で run を通し(urlopen だけ差し替え。実の ZIP を返す)、記録の profile が
        vocabulary.DEFAULT_PROFILE になる。counter を別のものに替えると赤になる。"""
        from unittest import mock
        import urllib.request
        zs = sorted((os.path.getsize(os.path.join(REAL_CACHE, f)), f) for f in os.listdir(REAL_CACHE) if f.endswith(".zip")) \
            if os.path.isdir(REAL_CACHE) else []
        if not zs:
            self.skipTest("cache が無い")
        with open(os.path.join(REAL_CACHE, zs[0][1]), "rb") as fh:
            real = fh.read()
        sys.path.insert(0, ROOT)
        from adapters.xbrl import edinet as ED
        from adapters.xbrl import vocabulary as V

        class R(object):
            def read(self_inner):
                return real
        # ED.CACHE_DIR を使い捨ての folder に向けておく: 置き場所を既存の cache に戻す変異でも、実の cache には書かれない
        sandbox = os.path.join(self.e.tmp, "sandbox_existing_cache")
        with mock.patch.object(ED, "_api_key", lambda: FAKE_KEY), mock.patch.object(ED, "CACHE_DIR", sandbox), \
                mock.patch.object(urllib.request, "urlopen", lambda url, timeout=None: R()):
            rec = F.run(root=ROOT, draw=self.e.draw, out=self.e.out, env={F.KEY_NAME: FAKE_KEY}, sleep=self.e.sleeps.append,
                        interval=0, fetch_dir=self.e.cache, existing_path_of=self.e.ecp, say=self.e.log.append)
        self.assertEqual(rec["取得に成功"], 40)
        self.assertEqual(rec["claim を数えた抽出"]["profile"], V.DEFAULT_PROFILE)
        self.assertTrue(all(isinstance(r["claims"], int) for r in rec["取得した書類"]))
        self.assertEqual(sorted(os.listdir(self.e.cache)), sorted(d + ".zip" for d in self.e.docs))
        self.assertFalse(os.path.exists(sandbox))             # 既存の cache の代わりの folder には何も書かれていない

    def test_32_partial_never_holds_the_key_even_when_exception_messages_do(self):
        """例外の文に偽の鍵が入る流れ(test_08 の再試行と test_21 の中断)の後も、残った .partial に鍵の字が無い。"""
        n = []

        def beh(d, k):
            n.append(d)
            if d == self.e.docs[0]:
                return OSError("boom " + FAKE_KEY)                 # 3 回失敗して失敗の行になる
            if len(n) > 8:
                return KeyboardInterrupt(FAKE_KEY)                 # 途中で中断(.partial が残る)
            return make_zip(len(n))
        with self.assertRaises(KeyboardInterrupt):
            self.e.run(fetcher=self.e.fetcher(beh))
        partial = self.e.out + ".partial"
        self.assertTrue(os.path.exists(partial))
        t = io.open(partial, encoding="utf-8").read()
        rows = json.loads(t)["取得した書類"]
        self.assertEqual(rows[0]["取得"], "失敗")                    # 例外の流れを通った(型だけが記録されている)
        self.assertEqual(rows[0]["失敗の型"], "OSError")
        self.assertNotIn(FAKE_KEY, t)
        self.assertEqual(F.key_leaks(t, FAKE_KEY), [])


if __name__ == "__main__":
    unittest.main()
