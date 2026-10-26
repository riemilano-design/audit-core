# -*- coding: utf-8 -*-
"""取得 script(measure/xbrl_p27_dbfetch_2026-10-27.py)の試験(封 docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md §1・§2)。
通信しない・鍵を使わない(偽の鍵)・本物の cache に書かない。transport(通信の関数)・replacer・sleep・now を差し替える。

**「X に書かない」を試す試験は、先に書き先を使い捨ての folder に向ける**(置き場所を本物に戻す変異でも、本物の cache には届かない)。
既定の置き場所を通す試験は、HOME を使い捨てにした子 process で走らせる。最後に本物の cache の件数が走る前と同じことを確かめる。"""
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
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.environ.get("P27_DBFETCH_SCRIPT", os.path.join(ROOT, "measure", "xbrl_p27_dbfetch_2026-10-27.py"))
REAL_FETCHED = os.path.join(ROOT, "fixtures", "xbrl", "fresh", "fetched_2026-10-21.json")
REAL_BASE = os.path.expanduser("~/.cache/audit-core")
REAL_DIRS = [os.path.join(REAL_BASE, "edinet"), os.path.join(REAL_BASE, "edinet-fresh-2026-10-21"),
             os.path.join(REAL_BASE, "edinetdb-p27")]

spec = importlib.util.spec_from_file_location("p27_dbfetch", SCRIPT)
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)

# 偽の鍵(固定の字面を file に置かない。tests/core/test_boundary.py の型にも当たらない)
FAKE_KEY = "".join(["Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7", "cF0xR"])      # 32 字
OTHER_32 = "".join(["Qw3rTy6uIo9pAs2dFg5hJk8lZx1cVb", "4n"])        # 鍵とは別の 32 字
SENTINEL_NAME = u"秘密の会社名テスト"                                  # 応答の値(記録に入ってはならない)
SENTINEL_NUMBER = 987654321


def _listing(folder):
    if not os.path.isdir(folder):
        return None
    return sorted(os.listdir(folder))


_BEFORE = {}


def setUpModule():
    for d in REAL_DIRS:
        _BEFORE[d] = _listing(d)


def tearDownModule():
    # 本物の cache の件数と名前が、試験の前と同じ(この試験は本物の cache に 1 file も足さない)
    for d in REAL_DIRS:
        assert _listing(d) == _BEFORE[d], "本物の cache が試験で変わった: %s" % d


def make_zip(code, n):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("XBRL/PublicDoc/jpcrp030000-asr-001_%s-000_2026-05-31_01_2026-08-19.xbrl" % code, "dummy %d" % n)
    return b.getvalue()


def fin_body(doc, years=None, wrap="data", extra=None):
    years = years if years is not None else [(2024, "S0000024"), (2025, "S0000025"), (2026, doc)]
    rows = [{"fiscal_year": y, "doc_id": d, "revenue": SENTINEL_NUMBER, "name": SENTINEL_NAME} for y, d in years]
    if extra is not None:
        rows = extra
    # 応答の字を整えていない形(インデントと末尾の改行つき)。保存が byte のままでなく整形や strip をすると、試験が赤になる
    return (json.dumps({wrap: rows} if wrap else rows, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


class World(object):
    """40 件の偽の候補(ZIP・記録・応答)。"""

    def __init__(self, tmp):
        self.tmp = tmp
        self.docs = ["S1000%03d" % i for i in range(1, 41)]
        self.codes = dict((d, "E%05d" % (10000 + i)) for i, d in enumerate(self.docs))
        self.zip_dir = os.path.join(tmp, "zips")
        self.existing = os.path.join(tmp, "existing")
        self.cache_root = os.path.join(tmp, "p27cache")
        os.makedirs(self.zip_dir)
        os.makedirs(self.existing)
        for i in range(3):
            open(os.path.join(self.existing, "X%d.zip" % i), "wb").write(b"x")
        rows = []
        for i, d in enumerate(self.docs):
            zb = make_zip(self.codes[d], i)
            open(os.path.join(self.zip_dir, d + ".zip"), "wb").write(zb)
            r = {"docID": d, "位置(引いた順)": i + 1, "取得": "成功", "bytes": len(zb), "sha256": F.sha256_hex(zb),
                 "claims": 5, "使う": i < 30}
            if i < 30:
                r["使う順"] = i + 1
            rows.append(r)
        self.fetched = os.path.join(tmp, "fetched.json")
        json.dump({"取得した書類": rows, "使う書類": self.docs[:30]}, io.open(self.fetched, "w", encoding="utf-8"))
        self.out = os.path.join(tmp, "out", "dbfetch.json")
        self.calls = []                  # path の列
        self.sleeps = []
        self.log = []
        self.behaviour = {}              # (doc, kind) -> 値(status, body) か 例外 か 列(1 回ごと)か 関数
        self.clock = [0]                 # now の進み(秒)
        self.start = F.datetime.datetime(2026, 10, 27, 3, 0, 0, tzinfo=F.datetime.timezone.utc)   # JST 2026-10-27 12:00

    def doc_of_path(self, path):
        code = re.match(r"/companies/(E[0-9]{5})", path).group(1)
        return [d for d in self.docs if self.codes[d] == code][0]

    def kind_of_path(self, path):
        m = re.match(r"/companies/E[0-9]{5}/(financials|ratios)", path)
        return m.group(1) if m else "companies"

    def transport(self, path, key):
        self.calls.append(path)
        d, kind = self.doc_of_path(path), self.kind_of_path(path)
        b = self.behaviour.get((d, kind))
        if isinstance(b, list):
            n = [p for p in self.calls if self.doc_of_path(p) == d and self.kind_of_path(p) == kind]
            b = b[min(len(n), len(b)) - 1]
        if callable(b):
            b = b()
        if isinstance(b, BaseException):
            raise b
        if b is not None:
            return b
        if kind == "financials":
            return 200, fin_body(d)
        return 200, (json.dumps({"kind": kind, "name": SENTINEL_NAME, "v": SENTINEL_NUMBER}, ensure_ascii=False, indent=1) + "\n\n").encode("utf-8")

    def now(self):
        return self.start + F.datetime.timedelta(seconds=self.clock[0])

    def run(self, **kw):
        args = dict(root=ROOT, fetched=self.fetched, out=self.out, env={F.KEY_NAME: FAKE_KEY},
                    transport=self.transport, replacer=lambda zb, text: (zb, "e", "m"), sleep=self.sleeps.append,
                    now=self.now, zip_dir=self.zip_dir, cache_root=self.cache_root,
                    existing_cache_dir=self.existing, interval=0, say=self.log.append)
        args.update(kw)
        return F.run(**args)


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p27fetch_", dir=os.environ.get("TMPDIR"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.w = World(self.tmp)

    def text(self):
        return io.open(self.w.out, encoding="utf-8").read()

    def paths(self, kind=None):
        return [p for p in self.w.calls if kind is None or self.w.kind_of_path(p) == kind]

    # --- 止まる所 ---
    def test_01_no_key_stops_before_any_call(self):
        for env in ({}, {F.KEY_NAME: ""}):
            with self.assertRaises(SystemExit):
                self.w.run(env=env)
        self.assertEqual(self.w.calls, [])
        self.assertFalse(os.path.exists(self.w.out))
        self.assertFalse(os.path.exists(self.w.cache_root))

    def test_02_existing_record_is_not_overwritten(self):
        os.makedirs(os.path.dirname(self.w.out))
        open(self.w.out, "w").write("{}")
        with self.assertRaises(SystemExit):
            self.w.run()
        self.assertEqual(self.w.calls, [])

    # --- 通った道 ---
    def test_03_all_pass_splits_20_with_10_10_and_types(self):
        rec = self.w.run()
        self.assertEqual(rec["|K|"], 30)
        self.assertEqual(rec["U"], self.w.docs[:20])
        self.assertEqual(rec["予備"], self.w.docs[20:30])
        self.assertEqual(rec["調整用"], self.w.docs[:10])
        self.assertEqual(rec["評価用"], self.w.docs[10:20])
        self.assertEqual([rec["型の割り当て"][d] for d in rec["U"]], ["A", "B", "C"] * 6 + ["A", "B"])
        self.assertFalse(rec["予備の候補を照らしたか"])            # |K| >= 20 なので位置 31〜40 は照らさない
        self.assertEqual(len(self.paths("financials")), 30)
        # /companies と /ratios は U の 20 社だけ(予備 10 社は取らない)
        self.assertEqual(sorted(self.w.doc_of_path(p) for p in self.paths("companies")), sorted(self.w.docs[:20]))
        self.assertEqual(sorted(self.w.doc_of_path(p) for p in self.paths("ratios")), sorted(self.w.docs[:20]))
        self.assertEqual(len(self.w.calls), 30 + 40)
        self.assertIsNone(rec["止め"])
        self.assertEqual(rec["材料が欠けた U の会社"], [])
        self.assertEqual(rec["回数"]["この script の試行の合計"], 70)
        self.assertEqual(self.w.sleeps, [])

    def test_04_call_order_and_urls(self):
        self.w.run()
        first = self.w.calls[0]
        self.assertEqual(first, "/companies/%s/financials?years=3&include_nulls=true&include_null_reasons=true" % self.w.codes[self.w.docs[0]])
        # 先に 30 件の /financials(位置の順)、そのあと U の会社ごとに companies → ratios
        self.assertEqual([self.w.doc_of_path(p) for p in self.w.calls[:30]], self.w.docs[:30])
        self.assertTrue(all(self.w.kind_of_path(p) == "financials" for p in self.w.calls[:30]))
        rest = self.w.calls[30:]
        self.assertEqual([(self.w.doc_of_path(p), self.w.kind_of_path(p)) for p in rest],
                         [(d, k) for d in self.w.docs[:20] for k in ("companies", "ratios")])
        self.assertEqual(rest[0], "/companies/%s" % self.w.codes[self.w.docs[0]])
        self.assertEqual(rest[1], "/companies/%s/ratios" % self.w.codes[self.w.docs[0]])

    # --- §1-4 の照らしの理由 ---
    def test_05_each_exclusion_reason(self):
        w = self.w
        d = w.docs
        w.behaviour[(d[1], "financials")] = (404, b"")                                  # 応答なし
        w.behaviour[(d[2], "financials")] = (200, fin_body(d[2], extra=[]))             # 行なし
        w.behaviour[(d[3], "financials")] = (200, fin_body(d[3], years=[(2025, "S0000025"), (2026, d[3]), (2026, d[3])]))   # 当期が 1 行でない
        w.behaviour[(d[4], "financials")] = (200, fin_body(d[4], years=[(2025, "S0000025"), (2026, "S9999999")]))           # doc_id が違う
        w.behaviour[(d[5], "financials")] = (200, fin_body(d[5], years=[(2025, d[5]), (2026, "S9999999")]))                 # 前の期が一致しても当期でなければ除く
        w.behaviour[(d[6], "financials")] = (200, fin_body(d[6], years=[(2026, d[6]), (2025, "S0000025")]))                 # 並びの順は関係ない(残る)
        bad_zip = open(os.path.join(w.zip_dir, d[7] + ".zip"), "rb").read()

        def replacer(zb, text):
            if zb == bad_zip:
                raise ValueError("x")
            return zb, "e", "m"
        rec = w.run(replacer=replacer)
        by = dict((j["docID"], j) for j in rec["照らし"])
        self.assertEqual((by[d[1]]["判定"], by[d[1]]["理由"]), ("除く", "応答なし"))
        self.assertEqual((by[d[2]]["判定"], by[d[2]]["理由"]), ("除く", "行なし"))
        self.assertEqual((by[d[3]]["判定"], by[d[3]]["理由"]), ("除く", "当期が 1 行でない"))
        self.assertEqual((by[d[4]]["判定"], by[d[4]]["理由"]), ("除く", "当期の doc_id が違う"))
        self.assertEqual(by[d[4]]["DB の当期の doc_id"], "S9999999")
        self.assertEqual((by[d[5]]["判定"], by[d[5]]["理由"]), ("除く", "当期の doc_id が違う"))
        self.assertEqual(by[d[6]]["判定"], "残る")
        self.assertEqual((by[d[7]]["判定"], by[d[7]]["理由"]), ("除く", "差し替えの節なし"))
        self.assertEqual(by[d[7]]["差し替えの例外の型"], "ValueError")
        self.assertNotIn("DB の当期の doc_id", by[d[1]])
        # K は残った会社だけを位置の順に。除かれた会社は /companies・/ratios を取らない
        removed = {d[1], d[2], d[3], d[4], d[5], d[7]}
        self.assertEqual(rec["K"], [x for x in d[:30] if x not in removed])
        self.assertEqual(rec["|K|"], 24)
        self.assertFalse(rec["予備の候補を照らしたか"])                      # K = 24 >= 20 なので位置 31〜40 は照らさない
        self.assertEqual(rec["除いた理由の内訳"], {"応答なし": 1, "行なし": 1, "当期が 1 行でない": 1,
                                             "当期の doc_id が違う": 2, "差し替えの節なし": 1})

    def test_06_reserve_candidates_are_examined_only_when_K_is_under_20(self):
        w = self.w
        # 主の候補 30 件のうち 12 件を除く(K = 18)→ 予備の候補 10 件を照らして足す(K = 28 → U は先頭 20)
        for i in range(12):
            w.behaviour[(w.docs[i], "financials")] = (404, b"")
        rec = w.run()
        self.assertTrue(rec["予備の候補を照らしたか"])
        self.assertEqual(len(self.paths("financials")), 40)
        self.assertEqual(rec["|K|"], 28)
        self.assertEqual(rec["K"], w.docs[12:40])
        self.assertEqual(rec["U"], w.docs[12:32])
        self.assertEqual(rec["予備"], w.docs[32:40])
        self.assertEqual(len(w.calls), 40 + 40)

    def test_07_reserve_not_examined_when_K_is_exactly_20(self):
        w = self.w
        for i in range(10):
            w.behaviour[(w.docs[i], "financials")] = (404, b"")
        rec = w.run()
        self.assertFalse(rec["予備の候補を照らしたか"])
        self.assertEqual(rec["|K|"], 20)
        self.assertEqual(len(self.paths("financials")), 30)
        self.assertEqual(len([j for j in rec["照らし"] if str(j["判定"]).startswith("照らさなかった")]), 10)

    def test_08_under_12_stops_with_record_and_no_material_calls(self):
        w = self.w
        for i in list(range(20)) + list(range(30, 39)):      # 主 30 件のうち 20 件・予備の候補 10 件のうち 9 件を除く
            w.behaviour[(w.docs[i], "financials")] = (404, b"")
        rec = w.run()
        self.assertEqual(rec["|K|"], 11)
        self.assertEqual(rec["U"], w.docs[20:30] + [w.docs[39]])
        self.assertTrue(rec["止め"])
        self.assertEqual(self.paths("companies"), [])
        self.assertEqual(self.paths("ratios"), [])
        self.assertEqual(rec["U の材料"], [])
        self.assertEqual(rec["除いた理由の内訳"], {"応答なし": 29})        # 残った数と除いた理由の内訳を記録する
        self.assertTrue(os.path.exists(self.w.out))             # 止めでも記録は書く
        self.assertEqual(len(w.calls), 40)

    def test_09_exactly_12_does_not_stop(self):
        w = self.w
        for i in range(12, 40):
            w.behaviour[(w.docs[i], "financials")] = (404, b"")
        rec = w.run()
        self.assertEqual(len(rec["U"]), 12)
        self.assertIsNone(rec["止め"])
        self.assertEqual((len(rec["調整用"]), len(rec["評価用"])), (6, 6))
        self.assertEqual(len(self.paths("companies")), 12)

    def test_10_three_excluded_codes_are_dropped_without_calls(self):
        w = self.w
        for i, c in enumerate(F.EXCLUDED_CODES):       # 位置 2・5・9 の会社の ZIP を、除く 3 コードの ZIP に差し替える(sha256 も記録に合わせる)
            d = w.docs[[1, 4, 8][i]]
            w.codes[d] = c
            zb = make_zip(c, 99 + i)
            open(os.path.join(w.zip_dir, d + ".zip"), "wb").write(zb)
        rows = json.load(io.open(w.fetched, encoding="utf-8"))
        for r in rows["取得した書類"]:
            r["sha256"] = F.sha256_hex(open(os.path.join(w.zip_dir, r["docID"] + ".zip"), "rb").read())
        json.dump(rows, io.open(w.fetched, "w", encoding="utf-8"))
        rec = w.run()
        self.assertEqual(rec["除いた 3 コード"]["除かれた件数"], 3)
        by = dict((j["docID"], j) for j in rec["照らし"])
        for i in (1, 4, 8):
            self.assertEqual(by[w.docs[i]]["理由"], "3 本の会社")
            self.assertNotIn(w.docs[i], rec["K"])
        self.assertEqual(len(self.paths("financials")), 27)        # 除く 3 社は /financials も呼ばない
        self.assertEqual(rec["|K|"], 27)

    def test_11_missing_field_stops_at_the_first_company(self):
        for rows in ([{"fiscal_year": 2026}], [{"doc_id": "S1000001"}],
                     [{"fiscal_year": 2025, "doc_id": "S1"}, {"doc_id": "S1000001"}]):
            tmp = tempfile.mkdtemp(prefix="p27fetch_", dir=os.environ.get("TMPDIR"))
            self.addCleanup(shutil.rmtree, tmp, True)
            w = World(tmp)
            w.behaviour[(w.docs[0], "financials")] = (200, fin_body(w.docs[0], extra=rows))
            with self.assertRaises(SystemExit) as cm:
                w.run()
            self.assertEqual(len(w.calls), 1)                      # 1 社目で止まる(進まない)
            self.assertFalse(os.path.exists(w.out))
            self.assertIn("欄", str(cm.exception))
            self.assertNotIn(SENTINEL_NAME, str(cm.exception))      # 応答の値は出さない

    def test_12_missing_field_in_a_later_company_also_stops_there(self):
        w = self.w
        w.behaviour[(w.docs[4], "financials")] = (200, fin_body(w.docs[4], extra=[{"fiscal_year": 2026}]))
        with self.assertRaises(SystemExit):
            w.run()
        self.assertEqual(len(w.calls), 5)
        self.assertFalse(os.path.exists(w.out))

    def test_13_unknown_response_shape_stops(self):
        for body in (b"[]", b'{"a": 1}', b'{"x": [], "y": []}', b"not json", b'{"x": [{"fiscal_year": 2026, "doc_id": "S1"}], "y": [{"k": 1}]}',
                     b'[1, 2]'):
            tmp = tempfile.mkdtemp(prefix="p27fetch_", dir=os.environ.get("TMPDIR"))
            self.addCleanup(shutil.rmtree, tmp, True)
            w = World(tmp)
            w.behaviour[(w.docs[0], "financials")] = (200, body)
            if body == b"[]":                 # 空の列は 行なし(止まらない)
                rec = w.run()
                self.assertEqual(rec["照らし"][0]["理由"], "行なし")
            else:
                with self.assertRaises(SystemExit):
                    w.run()
                self.assertFalse(os.path.exists(w.out))

    def test_14_shapes_that_are_accepted_without_guessing_names(self):
        rows = [{"fiscal_year": 2026, "doc_id": "S1000001", "n": 1}]
        self.assertEqual(F.extract_rows(rows), rows)
        self.assertEqual(F.extract_rows({"data": rows}), rows)
        self.assertEqual(F.extract_rows({"whatever": rows, "meta": {"a": 1}}), rows)
        self.assertEqual(F.extract_rows({"meta": {"a": 1}, "warnings": [], "z": rows}), rows)
        self.assertEqual(F.extract_rows({"data": {"items": rows}}), rows)
        self.assertEqual(F.extract_rows({"data": []}), [])
        with self.assertRaises(SystemExit):
            F.extract_rows({"a": rows, "b": rows})                  # 2 つあれば決まらない
        # fiscal_year は文字列でも読む。最大は数として比べる
        self.assertEqual(F.judge_financials([{"fiscal_year": "2026", "doc_id": "S1000001"}], "S1000001")[0], "残る")
        with self.assertRaises(F.FieldMissing):
            F.judge_financials([{"fiscal_year": None, "doc_id": "S1000001"}], "S1000001")
        # 最大の fiscal_year を取る(1 行目が最大でなくても・文字列の並びでなく数で)
        v = F.judge_financials([{"fiscal_year": 2025, "doc_id": "S1000001"}, {"fiscal_year": 2027, "doc_id": "S1000002"},
                                {"fiscal_year": 2026, "doc_id": "S1000003"}], "S1000002")
        self.assertEqual(v[0], "残る")
        # DB の doc_id が EDINET の公の識別子の形でないときは、記録に字を出さない
        v = F.judge_financials([{"fiscal_year": 2026, "doc_id": SENTINEL_NAME}], "S1000001")
        self.assertEqual(v, ("除く", "当期の doc_id が違う", None))
        self.assertEqual(F.judge_financials([{"fiscal_year": 2026, "doc_id": None}], "S1000001")[1], "当期の doc_id が違う")

    def test_15_duplicate_edinet_code_stops(self):
        w = self.w
        w.codes[w.docs[3]] = w.codes[w.docs[0]]
        zb = make_zip(w.codes[w.docs[0]], 77)
        open(os.path.join(w.zip_dir, w.docs[3] + ".zip"), "wb").write(zb)
        rows = json.load(io.open(w.fetched, encoding="utf-8"))
        rows["取得した書類"][3]["sha256"] = F.sha256_hex(zb)
        json.dump(rows, io.open(w.fetched, "w", encoding="utf-8"))
        with self.assertRaises(SystemExit):
            w.run()
        self.assertFalse(os.path.exists(w.out))

    # --- ZIP の確かめ ---
    def test_16_zip_sha_mismatch_stops_before_the_call(self):
        w = self.w
        open(os.path.join(w.zip_dir, w.docs[2] + ".zip"), "wb").write(make_zip(w.codes[w.docs[2]], 123))
        with self.assertRaises(SystemExit) as cm:
            w.run()
        self.assertIn(w.docs[2], str(cm.exception))
        self.assertEqual(len(w.calls), 2)                  # 位置 1・2 の分は進んでいた。位置 3 の ZIP が違うので、その会社は呼ばない
        self.assertFalse(os.path.exists(w.out))

    def test_17_zip_with_two_xbrl_or_no_code_stops(self):
        w = self.w
        for members in (["XBRL/PublicDoc/a_E10001-000_x.xbrl", "XBRL/PublicDoc/b_E10002-000_x.xbrl"], ["XBRL/PublicDoc/noname.xbrl"], []):
            b = io.BytesIO()
            with zipfile.ZipFile(b, "w") as z:
                for m in members:
                    z.writestr(m, "x")
            with self.assertRaises(SystemExit):
                F.edinet_code_from_zip(b.getvalue())
        self.assertEqual(F.edinet_code_from_zip(make_zip("E12345", 0)), "E12345")

    def test_18_candidate_record_must_match_the_seal_shape(self):
        w = self.w
        rows = json.load(io.open(w.fetched, encoding="utf-8"))
        rows["取得した書類"][35]["使う"] = True                 # 予備の候補が『使う』になっている
        json.dump(rows, io.open(w.fetched, "w", encoding="utf-8"))
        with self.assertRaises(SystemExit):
            w.run()
        self.assertEqual(w.calls, [])

    # --- 回数・再試行 ---
    def test_19_retries_5xx_429_and_network_but_not_4xx(self):
        w = self.w
        w.behaviour[(w.docs[0], "financials")] = [(503, b"x"), (429, b"x"), None]
        w.behaviour[(w.docs[1], "financials")] = (404, b"x")
        w.behaviour[(w.docs[2], "financials")] = [OSError("boom " + FAKE_KEY), OSError("boom"), OSError("boom")]
        w.behaviour[(w.docs[3], "financials")] = (500, b"x")
        rec = w.run()
        rows = dict((r["docID"], r) for r in rec["呼び出し"] if r["種類"] == "financials")
        self.assertEqual((rows[w.docs[0]]["status"], rows[w.docs[0]]["再試行の回数"]), (200, 2))
        self.assertEqual((rows[w.docs[1]]["status"], rows[w.docs[1]]["再試行の回数"]), (404, 0))
        self.assertEqual((rows[w.docs[2]]["status"], rows[w.docs[2]]["再試行の回数"], rows[w.docs[2]]["失敗の型"]), (None, 2, "OSError"))
        self.assertEqual((rows[w.docs[3]]["status"], rows[w.docs[3]]["再試行の回数"]), (500, 2))
        self.assertEqual(w.sleeps, [F.RETRY_WAIT_SEC] * 2 + [F.RETRY_WAIT_SEC] * 2 + [F.RETRY_WAIT_SEC] * 2)
        by = dict((j["docID"], j) for j in rec["照らし"])
        for d in (w.docs[1], w.docs[2], w.docs[3]):
            self.assertEqual((by[d]["判定"], by[d]["理由"]), ("除く", "応答なし"))
        # 3 回とも失敗した会社は引き直さない(3 回ちょうど)
        self.assertEqual(len([p for p in w.calls if w.doc_of_path(p) == w.docs[2]]), 3)
        self.assertEqual(rec["回数"]["応答なしの数"], 3)
        self.assertNotIn(FAKE_KEY, self.text())
        # 試行の合計 = 呼び出しの試行の総和(再試行を含む)
        self.assertEqual(rec["回数"]["この script の試行の合計"], len(w.calls))
        self.assertEqual(F.MAX_RETRIES, 2)
        self.assertEqual(F.RETRY_WAIT_SEC, 60.0)

    def test_20_the_two_preview_calls_count_as_already_used_today(self):
        self.assertEqual(F.DAILY_LIMIT, 95)
        self.assertEqual(F.PRIOR_USES, {"2026-10-27": 2})
        w = self.w
        # 2026-10-27(JST)に走る。70 回 + 下見の 2 回 = 72 回。上限 71 なら途中で止まる・72 なら通る
        with self.assertRaises(F.LimitStop):
            w.run(limit=71)
        self.assertEqual(len(w.calls), 69)                   # 69 回目の試行で 69 + 2 = 71。70 回目は上限
        tmp = tempfile.mkdtemp(prefix="p27fetch_", dir=os.environ.get("TMPDIR"))
        self.addCleanup(shutil.rmtree, tmp, True)
        w2 = World(tmp)
        rec = w2.run(limit=72)
        self.assertEqual(rec["回数"]["最大の 1 日(下見の分を含む)"], 72)
        self.assertEqual(rec["回数"]["既に使った数として数えた分(封 §11-0 の下見)"], {"2026-10-27": 2})

    def test_21_prior_uses_apply_only_to_their_own_jst_day(self):
        w = self.w
        w.start = F.datetime.datetime(2026, 10, 27, 15, 30, 0, tzinfo=F.datetime.timezone.utc)   # JST 10-28 00:30
        rec = w.run(limit=70)                                  # 下見の 2 回は 10-27 の分。10-28 には数えない
        self.assertEqual(list(rec["回数"]["試行の日別(JST)"]), ["2026-10-28"])
        self.assertEqual(rec["回数"]["最大の 1 日(下見の分を含む)"], 70)

    def test_22_limit_stops_records_where_and_the_next_day_continues_in_the_same_order(self):
        w = self.w
        with self.assertRaises(F.LimitStop):
            w.run(limit=40)                                    # 38 回(40 - 下見の 2)で止まる
        self.assertEqual(len(w.calls), 38)
        self.assertFalse(os.path.exists(w.out))
        partial = json.load(io.open(w.out + ".partial", encoding="utf-8"))
        self.assertEqual(len(partial["停止の履歴"]), 1)
        stop = partial["停止の履歴"][0]
        self.assertEqual((stop["docID"], stop["種類"]), (w.docs[4], "companies"))      # 30 + 8 回の次(U の 5 社目の /companies)
        self.assertIn("上限", stop["理由"])
        first_day_calls = list(w.calls)
        # 翌日(JST)に同じ順で続ける。済んだ応答は呼び直さない
        w.start = w.start + F.datetime.timedelta(days=1)
        w.calls[:] = []
        rec = w.run(limit=95)
        self.assertEqual(len(first_day_calls) + len(w.calls), 70)
        self.assertEqual(len(set(first_day_calls) & set(w.calls)), 0)
        self.assertEqual(rec["回数"]["試行の日別(JST)"], {"2026-10-27": 38, "2026-10-28": 32})
        self.assertEqual(len(rec["上限で止まった履歴"]), 1)
        self.assertFalse(os.path.exists(w.out + ".partial"))
        self.assertEqual(rec["U"], w.docs[:20])

    def test_23_a_401_or_403_stops_at_the_first_one_and_leaves_the_row_unfinished(self):
        # 鍵の誤りは 1 回目で止める。その行は完了にしない(応答なしに回さない・済みの応答に入れない)。送った 1 回は試行として残る
        for pos, kind, status, n_calls in ((2, "financials", 401, 3), (4, "financials", 403, 5), (4, "companies", 403, 30 + 8 + 1)):
            tmp = tempfile.mkdtemp(prefix="p27fetch_", dir=os.environ.get("TMPDIR"))
            self.addCleanup(shutil.rmtree, tmp, True)
            w = World(tmp)
            w.behaviour[(w.docs[pos], kind)] = (status, b'{"error":"x"}')
            with self.assertRaises(SystemExit) as cm:
                w.run()
            self.assertNotIsInstance(cm.exception, F.LimitStop)
            self.assertEqual(len(w.calls), n_calls)              # 1 回目で止まる(続けて 3 回を待たない・再試行しない)
            self.assertEqual((w.doc_of_path(w.calls[-1]), w.kind_of_path(w.calls[-1])), (w.docs[pos], kind))
            self.assertEqual(w.sleeps, [])
            self.assertFalse(os.path.exists(w.out))
            self.assertFalse(os.path.exists(os.path.join(w.cache_root, w.docs[pos], kind + ".json")))
            rows = json.load(io.open(w.out + ".partial", encoding="utf-8"))["呼び出し"]
            self.assertEqual(len(rows), n_calls)
            self.assertTrue(all(r["完了"] for r in rows[:-1]))
            last = rows[-1]
            self.assertEqual((last["docID"], last["種類"], last["完了"]), (w.docs[pos], kind, False))
            self.assertNotIn("status", last)                       # 行の status は付けない(応答なしの確定に回らない)
            self.assertEqual([a["status"] for a in last["試行"]], [status])

    # --- 中断からの続き ---
    def test_24_resume_reuses_recorded_responses_only(self):
        w = self.w
        n = []

        def beh():
            n.append(1)
            return KeyboardInterrupt() if len(n) == 1 else None      # 1 回目だけ中断(7 社目の /financials)
        w.behaviour[(w.docs[6], "financials")] = beh
        with self.assertRaises(KeyboardInterrupt):
            w.run()
        self.assertTrue(os.path.exists(w.out + ".partial"))
        w.calls[:] = []
        rec = w.run()
        self.assertEqual(len(w.calls), 70 - 6)                    # 取れた 6 件は呼び直さない
        self.assertEqual(rec["U"], w.docs[:20])

    def test_25_stray_or_tampered_response_files_stop(self):
        w = self.w
        stray = os.path.join(w.cache_root, w.docs[0])
        os.makedirs(stray)
        open(os.path.join(stray, "financials.json"), "wb").write(b"{}")
        with self.assertRaises(SystemExit):
            w.run()
        self.assertEqual(w.calls, [])
        shutil.rmtree(w.cache_root)
        with self.assertRaises(F.LimitStop):
            w.run(limit=10)
        # 記録と違う中身。形は正しい別の応答(extract_rows が通り、別の理由では止まらない)。sha256 の再確認だけが止める
        tampered = fin_body(w.docs[0], years=[(2026, "S9999999")])
        self.assertNotEqual(tampered, fin_body(w.docs[0]))
        open(os.path.join(w.cache_root, w.docs[0], "financials.json"), "wb").write(tampered)
        w.calls[:] = []
        with self.assertRaises(SystemExit):
            w.run()
        self.assertEqual(w.calls, [])

    # --- 鍵 ---
    def test_26_key_in_a_response_is_not_saved(self):
        w = self.w
        w.behaviour[(w.docs[2], "financials")] = (200, fin_body(w.docs[2]) + FAKE_KEY.encode("utf-8"))
        with self.assertRaises(SystemExit) as cm:
            w.run()
        self.assertFalse(os.path.exists(os.path.join(w.cache_root, w.docs[2], "financials.json")))
        self.assertNotIn(FAKE_KEY, str(cm.exception))
        self.assertFalse(os.path.exists(w.out))
        partial = io.open(w.out + ".partial", encoding="utf-8").read()
        self.assertNotIn(FAKE_KEY, partial)

    def test_27_key_leak_check_catches_fake_keys_and_lets_sha256_through(self):
        self.assertTrue(F.key_leaks('{"a": "%s"}' % FAKE_KEY))
        self.assertTrue(F.key_leaks('{"a": "%s"}' % "0123456789abcdef0123456789abcdef"))      # 32 桁 16 進も赤
        self.assertTrue(F.key_leaks("short-but-exact", key_value="short-but-exact"))
        self.assertTrue(F.key_leaks(F.KEY_NAME + "=" + "abcdefgh1"))
        self.assertEqual(F.key_leaks('{"sha256": "%s"}' % ("ab" * 32)), [])
        self.assertEqual(F.key_leaks("通常の文 S1000001 12345 /companies/E34960/financials?years=3"), [])
        self.assertTrue(F.bytes_leak_key(b"xx" + FAKE_KEY.encode() + b"yy", FAKE_KEY))
        self.assertFalse(F.bytes_leak_key(b"xx", FAKE_KEY))
        self.assertFalse(F.bytes_leak_key(b"xx", None))

    def test_28_leak_in_record_blocks_write(self):
        w = self.w
        # 環境の鍵とは別の 32 字(環境の鍵そのものの検査が先に当たって、32 字の検査の配線が隠れないように)
        self.assertNotEqual(OTHER_32, FAKE_KEY)
        exc_type = type(OTHER_32, (Exception,), {})
        with self.assertRaises(SystemExit):
            w.run(replacer=lambda zb, text: (_ for _ in ()).throw(exc_type("x")))
        self.assertFalse(os.path.exists(w.out))

    def test_29_key_value_itself_in_record_blocks_write(self):
        w = self.w
        with self.assertRaises(SystemExit):
            w.run(env={F.KEY_NAME: "E10000"})                     # 短い鍵の値が記録に出る(EDINET コードと同じ字)
        self.assertFalse(os.path.exists(w.out))

    def test_30_post_write_check_removes_file(self):
        calls = []
        real = F.key_leaks

        def fake(text, key_value=None):
            calls.append(1)
            return [] if len(calls) == 1 else ["after"]
        F.key_leaks = fake
        try:
            with self.assertRaises(SystemExit):
                self.w.run()
        finally:
            F.key_leaks = real
        self.assertFalse(os.path.exists(self.w.out))

    def test_31_exception_text_and_log_never_print_the_key(self):
        w = self.w
        w.behaviour[(w.docs[0], "financials")] = [OSError("url has " + FAKE_KEY)] * 3
        w.run()
        self.assertFalse([l for l in w.log if FAKE_KEY in str(l)])
        for p in (w.out, ):
            self.assertNotIn(FAKE_KEY, io.open(p, encoding="utf-8").read())
        with io.open(SCRIPT, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIsNone(re.search(r"\b[0-9a-f]{32}\b", src))
        self.assertIsNone(re.search(r"EDINET_API_KEY\s*[:=]\s*\S{8,}", src))        # tests/core/test_boundary.py と同じ型
        self.assertIsNone(re.search(KEYISH_IN_SOURCE, src))
        self.assertNotIn("print(", src.replace("say(", ""))
        self.assertNotIn("subprocess", src)                                          # キーチェーン(security)を呼ばない
        self.assertNotIn("os.system", src)

    # --- 置き場(既存の cache には書かない) ---
    def test_32_cache_root_inside_an_existing_cache_stops_without_a_call(self):
        w = self.w
        for inside in (os.path.join(w.existing, "edinetdb-p27"), os.path.join(w.zip_dir, "x"), w.existing, w.zip_dir):
            with self.assertRaises(SystemExit):
                w.run(cache_root=inside)
        self.assertEqual(w.calls, [])
        self.assertEqual(_listing(w.existing), ["X0.zip", "X1.zip", "X2.zip"])
        self.assertEqual(len(_listing(w.zip_dir)), 40)

    def test_33_responses_go_only_to_the_cache_root_byte_for_byte(self):
        w = self.w
        rec = w.run()
        self.assertEqual(sorted(os.listdir(w.cache_root)), sorted(w.docs[:30]))
        for d in w.docs[:30]:
            self.assertIn("financials.json", os.listdir(os.path.join(w.cache_root, d)))
        for d in w.docs[:20]:
            self.assertEqual(sorted(os.listdir(os.path.join(w.cache_root, d))), ["companies.json", "financials.json", "ratios.json"])
        for d in w.docs[20:30]:
            self.assertEqual(os.listdir(os.path.join(w.cache_root, d)), ["financials.json"])
        got = open(os.path.join(w.cache_root, w.docs[0], "financials.json"), "rb").read()
        self.assertEqual(got, fin_body(w.docs[0]))                          # 受け取った byte のまま
        self.assertTrue(got.endswith(b"\n") and b"\n " in got)               # 整えていない形が試験の入力になっている
        got2 = open(os.path.join(w.cache_root, w.docs[0], "ratios.json"), "rb").read()
        self.assertTrue(got2.endswith(b"\n\n"))
        self.assertEqual(F.sha256_hex(got2), [r for r in rec["呼び出し"] if r["docID"] == w.docs[0] and r["種類"] == "ratios"][0]["sha256"])
        row = [r for r in rec["呼び出し"] if r["docID"] == w.docs[0] and r["種類"] == "financials"][0]
        self.assertEqual((row["bytes"], row["sha256"]), (len(got), F.sha256_hex(got)))
        # 既存の cache と ZIP の folder は 1 file も変わらない
        self.assertEqual(_listing(w.existing), ["X0.zip", "X1.zip", "X2.zip"])
        self.assertEqual(len(_listing(w.zip_dir)), 40)
        self.assertTrue(rec["cache の前後"]["変化なし"])
        self.assertEqual(rec["cache の前後"]["前"], rec["cache の前後"]["後"])
        self.assertEqual(rec["cache の前後"]["前"]["既存の cache"]["件数"], 3)
        self.assertEqual(rec["cache の前後"]["前"]["ZIP の folder"]["件数"], 40)

    def test_34_a_change_in_the_existing_cache_during_the_run_stops_without_a_record(self):
        w = self.w
        real = w.transport

        def tr(path, key):
            open(os.path.join(w.existing, "intruder.zip"), "wb").write(b"x")    # 走っている間に既存の cache に file が増えた
            return real(path, key)
        with self.assertRaises(SystemExit):
            w.run(transport=tr)
        self.assertFalse(os.path.exists(w.out))

    def test_35_default_wiring_under_a_swapped_home_touches_only_the_p27_folder(self):
        """HOME を使い捨てにした子 process で、置き場所を省いた既定の配線を通す(urlopen だけ差し替える。通信しない)。
        既存の cache(HOME/.cache/audit-core/edinet)には 1 file も足されず、応答は edinetdb-p27 にだけ置かれる。"""
        home = os.path.join(self.tmp, "home")
        base = os.path.join(home, ".cache", "audit-core")
        os.makedirs(os.path.join(base, "edinet"))
        os.makedirs(os.path.join(base, "edinet-fresh-2026-10-21"))
        for d in self.w.docs:
            shutil.copy(os.path.join(self.w.zip_dir, d + ".zip"), os.path.join(base, "edinet-fresh-2026-10-21", d + ".zip"))
        open(os.path.join(base, "edinet", "keep.zip"), "wb").write(b"x")
        out = os.path.join(self.tmp, "child_out.json")
        codes = json.dumps(dict((c, d) for d, c in self.w.codes.items()))
        driver = (
            "import importlib.util, sys, io, json, re, urllib.request\n"
            "script, root, fetched, out, key, codes = sys.argv[1:7]\n"
            "codes = json.loads(codes)\n"
            "spec = importlib.util.spec_from_file_location('p27', script)\n"
            "F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)\n"
            "seen = []\n"
            "class R(object):\n"
            "    def __init__(self, b): self.b = b\n"
            "    def read(self): return self.b\n"
            "    def getcode(self): return 200\n"
            "    def __enter__(self): return self\n"
            "    def __exit__(self, *a): return False\n"
            "def urlopen(req, timeout=None):\n"
            "    seen.append((req.full_url, req.get_header('X-api-key')))\n"
            "    m = re.match(r'https://edinetdb.jp/v1/companies/(E[0-9]{5})(?:/(financials|ratios))?', req.full_url)\n"
            "    d = codes[m.group(1)]\n"
            "    if m.group(2) == 'financials':\n"
            "        return R(json.dumps({'data': [{'fiscal_year': 2026, 'doc_id': d}]}).encode())\n"
            "    return R(b'{}')\n"
            "urllib.request.urlopen = urlopen\n"
            "rec = F.run(root=root, fetched=fetched, out=out, env={F.KEY_NAME: key}, replacer=lambda z, t: (z, 'e', 'm'),\n"
            "            sleep=lambda s: None, interval=0, say=lambda s: None)\n"
            "print('RAN %d keyok=%s' % (len(seen), all(k == key for _, k in seen)))\n")
        env = dict((k, v) for k, v in os.environ.items() if k not in (F.KEY_NAME, "HOME"))
        env["HOME"] = home
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        p = subprocess.run([sys.executable, "-B", "-c", driver, SCRIPT, ROOT, self.w.fetched, out, FAKE_KEY, codes],
                           env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        self.assertEqual(p.stdout.strip(), "RAN 70 keyok=True")
        self.assertEqual(os.listdir(os.path.join(base, "edinet")), ["keep.zip"])
        self.assertEqual(len(os.listdir(os.path.join(base, "edinet-fresh-2026-10-21"))), 40)
        self.assertEqual(sorted(os.listdir(os.path.join(base, "edinetdb-p27"))), sorted(self.w.docs[:30]))
        written = sorted(os.path.relpath(os.path.join(d, f), home) for d, _, fs in os.walk(home) for f in fs)
        outside = [x for x in written if not (x.startswith(os.path.join(".cache", "audit-core", "edinetdb-p27") + os.sep)
                                              or x.startswith(os.path.join(".cache", "audit-core", "edinet-fresh-2026-10-21") + os.sep)
                                              or x == os.path.join(".cache", "audit-core", "edinet", "keep.zip"))]
        self.assertEqual(outside, [])

    def test_36_default_folder_names(self):
        saved = os.environ.get("HOME")
        os.environ["HOME"] = "/nonexistent-home-for-test"
        try:
            self.assertEqual(F.default_cache_root(), "/nonexistent-home-for-test/.cache/audit-core/edinetdb-p27")
            self.assertEqual(F.default_zip_dir(), "/nonexistent-home-for-test/.cache/audit-core/edinet-fresh-2026-10-21")
            self.assertEqual(F.default_existing_cache_dir(), "/nonexistent-home-for-test/.cache/audit-core/edinet")
        finally:
            if saved is None:
                del os.environ["HOME"]
            else:
                os.environ["HOME"] = saved

    # --- 記録の形(応答の値が入らない) ---
    def test_37_record_has_no_response_values_and_the_sealed_fields(self):
        rec = self.w.run()
        t = self.text()
        self.assertNotIn(SENTINEL_NAME, t)
        self.assertNotIn(str(SENTINEL_NUMBER), t)
        self.assertEqual(json.loads(t)["K"], rec["K"])
        for k in ("照らし", "K", "U", "調整用", "評価用", "予備", "型の割り当て", "呼び出し", "回数", "cache の前後", "除いた 3 コード",
                  "除いた理由の内訳", "上限で止まった履歴", "止め", "U の材料"):
            self.assertIn(k, rec)
        r = rec["呼び出し"][0]
        for k in ("順", "docID", "EDINET コード", "種類", "path", "status", "再試行の回数", "bytes", "sha256", "時刻(UTC)", "試行"):
            self.assertIn(k, r)
        self.assertEqual([x["順"] for x in rec["呼び出し"]], list(range(1, 71)))
        self.assertNotIn("完了", r)
        j = rec["照らし"][0]
        for k in ("docID", "位置", "区分", "EDINET コード", "ZIP の sha256 が記録と一致", "判定", "差し替え"):
            self.assertIn(k, j)
        self.assertEqual(len(r["sha256"]), 64)
        self.assertNotIn("X-API-Key", t)
        self.assertEqual(rec["鍵"]["環境変数の名前"], F.KEY_NAME)
        self.assertFalse(os.path.exists(self.w.out + ".partial"))
        self.assertEqual([m["docID"] for m in rec["U の材料"]], rec["U"])

    def test_38_missing_material_in_U_is_recorded_not_dropped(self):
        w = self.w
        w.behaviour[(w.docs[3], "ratios")] = (404, b"")
        w.behaviour[(w.docs[5], "companies")] = (200, b"not json")
        rec = w.run()
        self.assertEqual(rec["U"], w.docs[:20])                      # U は変えない
        self.assertEqual(rec["材料が欠けた U の会社"], [w.docs[3], w.docs[5]])

    # --- 通信の中身 ---
    def test_39_default_transport_sends_the_key_only_in_the_header_and_returns_http_errors_as_status(self):
        import urllib.error
        seen = []

        class R(object):
            def read(self_inner):
                return b"[]"

            def getcode(self_inner):
                return 200

            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *a):
                return False

        def ok(req, timeout=None):
            seen.append(req)
            return R()

        def err(req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 429, "x", {}, io.BytesIO(b"slow down"))
        with mock.patch("urllib.request.urlopen", ok):
            self.assertEqual(F.default_transport("/companies/E34960", FAKE_KEY), (200, b"[]"))
        req = seen[0]
        self.assertEqual(req.full_url, "https://edinetdb.jp/v1/companies/E34960")
        self.assertNotIn(FAKE_KEY, req.full_url)
        self.assertEqual(req.get_header("X-api-key"), FAKE_KEY)
        with mock.patch("urllib.request.urlopen", err):
            self.assertEqual(F.default_transport("/companies/E34960", FAKE_KEY), (429, b"slow down"))

    # --- dry-run ---
    def test_40_dry_run_needs_its_own_paths_and_no_key(self):
        with self.assertRaises(SystemExit):
            F.main(["--dry-run"])
        with self.assertRaises(SystemExit):
            F.run(root=ROOT, env={}, dry_run=True, fetched=self.w.fetched, out=self.w.out, zip_dir=self.w.zip_dir,
                  cache_root=self.w.cache_root, existing_cache_dir=self.w.existing)       # transport が無い
        fake = os.path.join(self.tmp, "fake")
        for d in self.w.docs[:12]:
            c = self.w.codes[d]
            os.makedirs(os.path.join(fake, c))
            open(os.path.join(fake, c, "financials.json"), "wb").write(fin_body(d))
            open(os.path.join(fake, c, "companies.json"), "wb").write(b"{}")
            open(os.path.join(fake, c, "ratios.json"), "wb").write(b"{}")
        rec = F.run(root=ROOT, env={}, dry_run=True, transport=F.fake_transport(fake), replacer=lambda zb, t: (zb, "e", "m"),
                    fetched=self.w.fetched, out=self.w.out, zip_dir=self.w.zip_dir, cache_root=self.w.cache_root,
                    existing_cache_dir=self.w.existing, interval=0, say=self.w.log.append, sleep=self.w.sleeps.append)
        self.assertTrue(rec["dry_run"])
        self.assertEqual(rec["|K|"], 12)                                  # 12 件に偽の応答がある。ほかは 404 で 応答なし
        self.assertEqual(rec["U"], self.w.docs[:12])

    def test_41_dry_run_cli_on_the_real_candidates_when_the_real_zips_exist(self):
        real_zips = F.default_zip_dir()
        if not (os.path.isdir(real_zips) and os.path.exists(REAL_FETCHED)):
            self.skipTest("本物の ZIP が手元に無い(%s)。dry-run の CLI の通しは走らせていない" % real_zips)
        primary, reserve = F.load_candidates(REAL_FETCHED)
        fake = os.path.join(self.tmp, "fake_real")
        for c in primary + reserve:
            with open(os.path.join(real_zips, c["docID"] + ".zip"), "rb") as fh:
                code = F.edinet_code_from_zip(fh.read())
            os.makedirs(os.path.join(fake, code))
            open(os.path.join(fake, code, "financials.json"), "wb").write(fin_body(c["docID"]))
            open(os.path.join(fake, code, "companies.json"), "wb").write(b"{}")
            open(os.path.join(fake, code, "ratios.json"), "wb").write(b"{}")
        out = os.path.join(self.tmp, "dry_out.json")
        env = dict((k, v) for k, v in os.environ.items() if k != F.KEY_NAME)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        p = subprocess.run([sys.executable, "-B", SCRIPT, "--root", ROOT, "--dry-run", "--fake-dir", fake, "--out", out,
                            "--cache-root", os.path.join(self.tmp, "dry_cache")],
                           env=env, capture_output=True, text=True, timeout=300)
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        rec = json.load(io.open(out, encoding="utf-8"))
        self.assertTrue(rec["dry_run"])
        self.assertEqual(rec["|K|"], 30)                                  # 本物の ZIP の経営分析の節で差し替えが通る(30 件とも)
        self.assertEqual(rec["U"], [c["docID"] for c in primary[:20]])
        self.assertEqual(rec["除いた 3 コード"]["除かれた件数"], 0)
        self.assertEqual(rec["回数"]["この script の試行の合計"], 30 + 40)

    def test_42_the_five_sealed_constants(self):
        self.assertEqual((F.N_PRIMARY, F.N_RESERVE, F.U_SIZE, F.U_MIN), (30, 10, 20, 12))
        self.assertEqual(F.EXCLUDED_CODES, ("E02144", "E01777", "E02367"))
        self.assertEqual(F.KEY_NAME, "EDINETDB_API_KEY")

    def test_43_default_replacer_goes_through_the_verify_document_path_with_the_fixed_sentence(self):
        """封 §1-5: `verify_document --text` と同じ経路(`prose.build_modified_zip`)を、固定の 1 文で通す。
        経路を通さずに『通った』と数えると、経営分析の節が無い会社を除けない。"""
        sys.path.insert(0, ROOT)
        from adapters.xbrl import prose as PR
        seen = []

        def fake(zb, text):
            seen.append((zb, text))
            return b"modified", "elem", "member"
        with mock.patch.object(PR, "build_modified_zip", fake):
            self.assertEqual(F.check_replace(b"zip-bytes", F.default_replacer), (True, None))
        self.assertEqual(seen, [(b"zip-bytes", u"当期の業績を記載する。")])
        # 節の無い ZIP(本物の経路)は例外で、除かれる
        ok, etype = F.check_replace(make_zip("E12345", 0), F.default_replacer)
        self.assertFalse(ok)
        self.assertTrue(etype)
        # 本物の ZIP(手元に在れば)は通る
        real = os.path.join(F.default_zip_dir(), "%s.zip" % json.load(io.open(REAL_FETCHED, encoding="utf-8"))["使う書類"][0])
        if os.path.exists(real):
            self.assertEqual(F.check_replace(open(real, "rb").read(), F.default_replacer), (True, None))

    # --- 鍵の誤りで止めたあとの続き・記録の集計 ---
    def test_44_after_a_401_the_same_row_is_called_again_and_is_never_a_no_response(self):
        base = World(tempfile.mkdtemp(prefix="p27fetch_", dir=os.environ.get("TMPDIR")))
        self.addCleanup(shutil.rmtree, base.tmp, True)
        want = base.run()                                        # 401 の無い走り
        w = self.w
        w.behaviour[(w.docs[0], "financials")] = (401, b'{"error":"x"}')      # 位置 1 の /financials が 401
        with self.assertRaises(SystemExit):
            w.run()
        self.assertEqual(len(w.calls), 1)
        partial = json.load(io.open(w.out + ".partial", encoding="utf-8"))
        self.assertEqual([(r["docID"], r["完了"]) for r in partial["呼び出し"]], [(w.docs[0], False)])
        # 鍵を直したことにして、同じ out・partial で続ける
        w.behaviour.clear()
        w.calls[:] = []
        rec = w.run(env={F.KEY_NAME: OTHER_32})
        self.assertEqual(rec["除いた理由の内訳"], {})                      # 応答なし 0 件
        self.assertEqual(rec["回数"]["応答なしの数"], 0)
        self.assertEqual((rec["|K|"], rec["K"]), (want["|K|"], want["K"]))
        self.assertEqual(rec["U"][:3], w.docs[:3])                        # U の先頭は位置 1 の会社
        self.assertEqual(rec["U"], want["U"])
        self.assertEqual(rec["調整用"], want["調整用"])
        self.assertEqual(w.doc_of_path(w.calls[0]), w.docs[0])             # 位置 1 から呼び直した
        self.assertEqual(len(w.calls), 70)
        self.assertEqual(rec["回数"]["呼び出し(応答の最終の行)の数"], 70)
        self.assertEqual(rec["回数"]["この script の試行の合計"], 71)       # 401 の 1 回は試行として残る(上限の数)
        by = dict((j["docID"], j) for j in rec["照らし"])
        self.assertEqual(by[w.docs[0]]["判定"], "残る")
        self.assertEqual(by[w.docs[0]]["financials の応答"]["status"], 200)

    def test_45_record_counts_only_completed_rows_while_the_daily_limit_counts_every_sent_call(self):
        w = self.w
        w.behaviour[(w.docs[0], "financials")] = [(503, b"x"), (200, fin_body(w.docs[0]))]
        with self.assertRaises(F.LimitStop):
            w.run(limit=3)                                        # 下見 2 + 試行 1 で上限。再試行の途中で止まる
        self.assertEqual(len(w.calls), 1)
        partial = json.load(io.open(w.out + ".partial", encoding="utf-8"))
        self.assertEqual([(r["docID"], r["完了"], len(r["試行"])) for r in partial["呼び出し"]], [(w.docs[0], False, 1)])
        w.start = w.start + F.datetime.timedelta(days=1)             # 翌日(JST)に続ける
        rec = w.run()
        self.assertEqual(len(w.calls), 71)                           # 送った呼び出しは 1 + 70
        self.assertEqual(rec["回数"]["呼び出し(応答の最終の行)の数"], 70)
        self.assertEqual(rec["回数"]["応答なしの数"], 0)
        self.assertEqual(rec["除いた理由の内訳"], {})
        # 1 日の上限の数えは変わらない(未完の行の試行も数える)
        self.assertEqual(rec["回数"]["この script の試行の合計"], 71)
        self.assertEqual(rec["回数"]["試行の日別(JST)"], {"2026-10-27": 1, "2026-10-28": 70})
        self.assertEqual(rec["回数"]["最大の 1 日(下見の分を含む)"], 70)


KEYISH_IN_SOURCE = r"[A-Za-z0-9]{32,}"

if __name__ == "__main__":
    unittest.main()
