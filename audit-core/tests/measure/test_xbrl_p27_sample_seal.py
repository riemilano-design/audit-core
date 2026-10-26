# -*- coding: utf-8 -*-
"""封の門: docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md(P27 段 1)― §10-1。

封が「機械で 1 通りに決まる」と書いたものを、手元の記録と script の定数から毎回数え直す。
  - 候補の並び(§1-1): fetched_2026-10-21.json の位置 1〜30 = 使う書類、31〜40 = 予備の候補
  - ZIP の sha256 と記録の一致・EDINET コード・3 コードの除外が 0 件(§1-2・§1-3)― **ZIP が手元に無い環境では skip(理由の行が出る)**
  - 型の割り当て・分け方の関数を小さい入力で(§1-6・§1-7)
  - 書き手(§3-3)と読み手(§5-6)の指示文が、封の文書のコード塊と 1 字も違わない
  - 封の字で決めた定数(3 コード・URL・置き場・回数の上限・下見 2 回)が script と同じ
この門は通信しない・鍵に触れない・本物の cache を読むだけ(ZIP を数える)。"""
import importlib.util
import io
import json
import os
import re
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL = os.path.join(ROOT, "docs", "XBRL_P27_SAMPLE_SEAL_2026-10-27.md")
FETCHED = os.path.join(ROOT, "fixtures", "xbrl", "fresh", "fetched_2026-10-21.json")
FETCH_SCRIPT = os.environ.get("P27_DBFETCH_SCRIPT", os.path.join(ROOT, "measure", "xbrl_p27_dbfetch_2026-10-27.py"))
PROMPTS_SCRIPT = os.environ.get("P27_PROMPTS_SCRIPT", os.path.join(ROOT, "measure", "xbrl_p27_prompts_2026-10-27.py"))
ZIP_DIR = os.path.expanduser("~/.cache/audit-core/edinet-fresh-2026-10-21")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


F = _load("p27_seal_dbfetch", FETCH_SCRIPT)
P = _load("p27_seal_prompts", PROMPTS_SCRIPT)

with io.open(SEAL, encoding="utf-8") as _fh:
    SEAL_TEXT = _fh.read()


def seal_code_block(after_pattern):
    """封の文書で、after_pattern の行の直後のコード塊(``` と ``` の間。前後の改行を除く)。ちょうど 1 つ。"""
    found = re.findall(after_pattern + r"\n\n```\n(.*?)\n```\n", SEAL_TEXT, re.S)
    assert len(found) == 1, (after_pattern, len(found))
    return found[0]


def seal_type_sentences():
    return dict(re.findall(r"^   - ([ABC]): `([^`]*)`$", SEAL_TEXT, re.M))


class CandidateOrder(unittest.TestCase):
    """§1-1 候補の並び(手元の記録)。"""

    def rows(self):
        with io.open(FETCHED, encoding="utf-8") as fh:
            rec = json.load(fh)
        return rec, sorted(rec["取得した書類"], key=lambda r: r["位置(引いた順)"])

    def test_01_positions_1_to_40_and_the_30_used_are_the_primary(self):
        rec, rows = self.rows()
        self.assertEqual([r["位置(引いた順)"] for r in rows], list(range(1, 41)))
        self.assertEqual([r["docID"] for r in rows[:30]], rec["使う書類"])
        self.assertEqual(len(rec["使う書類"]), 30)
        self.assertEqual([r["使う順"] for r in rows[:30]], list(range(1, 31)))     # 使う順と位置は一致
        self.assertTrue(all(r["使う"] is True for r in rows[:30]))

    def test_02_reserve_candidates_are_positions_31_to_40_fetched_with_claims_and_not_used(self):
        _, rows = self.rows()
        reserve = rows[30:]
        self.assertEqual(len(reserve), 10)
        for r in reserve:
            self.assertEqual(r["取得"], "成功")
            self.assertGreaterEqual(r["claims"], 1)
            self.assertIs(r["使う"], False)
        # 『取得済み・claim 1 以上・使うが false』は 40 件のうちこの 10 件だけ
        self.assertEqual(len([r for r in rows if r["取得"] == "成功" and r["claims"] >= 1 and not r["使う"]]), 10)

    def test_03_load_candidates_returns_the_same_30_and_10(self):
        primary, reserve = F.load_candidates(FETCHED)
        _, rows = self.rows()
        self.assertEqual([c["docID"] for c in primary], [r["docID"] for r in rows[:30]])
        self.assertEqual([c["docID"] for c in reserve], [r["docID"] for r in rows[30:]])
        self.assertEqual([c["位置"] for c in primary + reserve], list(range(1, 41)))
        self.assertEqual(set(c["区分"] for c in primary), {"主"})
        self.assertEqual(set(c["区分"] for c in reserve), {"予備の候補"})
        self.assertEqual([c["sha256"] for c in primary + reserve], [r["sha256"] for r in rows])

    def test_04_load_candidates_is_ordered_by_position_not_by_file_order(self):
        import tempfile
        _, rows = self.rows()
        rec = json.load(io.open(FETCHED, encoding="utf-8"))
        rec["取得した書類"] = list(reversed(rec["取得した書類"]))
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as tmp:
            p = os.path.join(tmp, "f.json")
            json.dump(rec, io.open(p, "w", encoding="utf-8"))
            primary, reserve = F.load_candidates(p)
        self.assertEqual([c["docID"] for c in primary + reserve], [r["docID"] for r in rows])

    def test_05_a_record_that_does_not_match_the_seal_stops(self):
        import tempfile
        base = json.load(io.open(FETCHED, encoding="utf-8"))
        cases = []
        r = json.loads(json.dumps(base)); r["取得した書類"][5]["位置(引いた順)"] = 99; cases.append(r)       # 位置が連番でない
        r = json.loads(json.dumps(base)); r["使う書類"] = list(reversed(r["使う書類"])); cases.append(r)      # 使う書類と位置 1〜30 が違う
        r = json.loads(json.dumps(base)); r["取得した書類"][35]["使う"] = True; cases.append(r)              # 予備の候補が使うになっている
        r = json.loads(json.dumps(base)); r["取得した書類"][35]["claims"] = 0; cases.append(r)               # claim が 0
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as tmp:
            for i, rec in enumerate(cases):
                p = os.path.join(tmp, "f%d.json" % i)
                json.dump(rec, io.open(p, "w", encoding="utf-8"))
                with self.assertRaises(SystemExit):
                    F.load_candidates(p)

    def test_06_the_seal_names_the_same_file_and_positions(self):
        self.assertIn("fixtures/xbrl/fresh/fetched_2026-10-21.json", SEAL_TEXT)
        self.assertEqual(os.path.join("fixtures", "xbrl", "fresh", "fetched_2026-10-21.json"), os.path.relpath(FETCHED, ROOT))
        self.assertIn("位置 1〜30", SEAL_TEXT)
        self.assertIn("位置 31〜40", SEAL_TEXT)
        self.assertEqual((F.N_PRIMARY, F.N_RESERVE), (30, 10))


class ZipRecount(unittest.TestCase):
    """§1-2・§1-3 ZIP の sha256 と EDINET コードの数え直し。**ZIP が手元に無いときは skip(行が出る)。**"""

    def test_07_zip_sha256_matches_the_record_and_the_three_codes_are_not_among_the_40(self):
        with io.open(FETCHED, encoding="utf-8") as fh:
            rows = sorted(json.load(fh)["取得した書類"], key=lambda r: r["位置(引いた順)"])
        missing, codes = [], []
        for r in rows:
            path = os.path.join(ZIP_DIR, r["docID"] + ".zip")
            if not os.path.exists(path):
                missing.append(r["docID"])
                continue
            with open(path, "rb") as fh:
                zb = fh.read()
            self.assertEqual(F.sha256_hex(zb), r["sha256"], r["docID"])
            self.assertEqual(len(zb), r["bytes"], r["docID"])
            with zipfile.ZipFile(io.BytesIO(zb)) as z:
                names = [n for n in z.namelist() if n.startswith("XBRL/PublicDoc/") and n.endswith(".xbrl")]
            self.assertEqual(len(names), 1, r["docID"])                      # 1 ZIP に 1 つ
            codes.append(F.edinet_code_from_zip(zb))
        if missing:
            self.skipTest("ZIP が手元に無い(%d / 40 件・%s)。sha256・EDINET コード・3 コードの除外 0 件の数え直しは、在った %d 件だけ"
                          % (len(missing), ZIP_DIR, len(codes)))
        self.assertEqual(len(codes), 40)
        self.assertEqual(len(set(codes)), 40)                               # 会社の重複なし(重複があれば script が止まる)
        for c in codes:
            self.assertRegex(c, r"^E[0-9]{5}$")
        # 除かれるのは 0 件(封 §1-3): 主の候補は 30 件、予備の候補は 10 件のまま
        self.assertEqual([c for c in codes if c in F.EXCLUDED_CODES], [])

    def test_08_the_three_codes_are_the_ones_in_the_seal(self):
        for code, name in (("E02144", "トヨタ自動車"), ("E01777", "ソニーグループ"), ("E02367", "任天堂")):
            self.assertIn(code, F.EXCLUDED_CODES)
            self.assertIn("`%s`(%s)" % (code, name), SEAL_TEXT)
        self.assertEqual(len(F.EXCLUDED_CODES), 3)

    def test_09_code_is_read_from_the_xbrl_file_name_inside_publicdoc(self):
        def z(names):
            b = io.BytesIO()
            with zipfile.ZipFile(b, "w") as zz:
                for n in names:
                    zz.writestr(n, "x")
            return b.getvalue()
        good = "XBRL/PublicDoc/jpcrp030000-asr-001_E34960-000_2026-05-31_01_2026-08-19.xbrl"
        self.assertEqual(F.edinet_code_from_zip(z([good, "XBRL/AuditDoc/jpaud-aar-cn-001_E99999-000_x.xbrl"])), "E34960")   # AuditDoc は数えない
        with self.assertRaises(SystemExit):
            F.edinet_code_from_zip(z([good, good.replace("E34960", "E34961")]))         # 2 つ
        with self.assertRaises(SystemExit):
            F.edinet_code_from_zip(z(["XBRL/PublicDoc/x.xbrl"]))                         # コードが読めない


class Partition(unittest.TestCase):
    """§1-6・§1-7 分け方と型の割り当て(小さい入力)。"""

    def ids(self, n):
        return ["d%02d" % i for i in range(n)]

    def test_10_thirty_gives_u20_reserve10_split_10_10(self):
        k = self.ids(30)
        p = F.partition(k)
        self.assertEqual(p["U"], k[:20])
        self.assertEqual(p["予備"], k[20:])
        self.assertEqual(p["調整用"], k[:10])
        self.assertEqual(p["評価用"], k[10:20])
        self.assertFalse(p["停止"])

    def test_11_types_are_abc_by_position_in_U_and_counts_match_the_seal(self):
        k = self.ids(30)
        p = F.partition(k)
        self.assertEqual([p["型"][d] for d in p["U"][:6]], ["A", "B", "C", "A", "B", "C"])
        tune = [p["型"][d] for d in p["調整用"]]
        ev = [p["型"][d] for d in p["評価用"]]
        self.assertEqual((tune.count("A"), tune.count("B"), tune.count("C")), (4, 3, 3))      # 調整用は A 4・B 3・C 3
        self.assertEqual((ev.count("A"), ev.count("B"), ev.count("C")), (3, 4, 3))            # 評価用(i = 10〜19)は A 3・B 4・C 3
        self.assertEqual(set(p["型"]), set(p["U"]))                                            # 型は U の会社だけ
        self.assertEqual(F.assign_styles(["x", "y", "z", "w"]), {"x": "A", "y": "B", "z": "C", "w": "A"})
        self.assertEqual(F.STYLES, ("A", "B", "C"))

    def test_12_fewer_than_20_uses_all_of_K_and_the_evaluation_side_gets_the_odd_one(self):
        for n, tune, ev in ((19, 9, 10), (13, 6, 7), (12, 6, 6), (15, 7, 8)):
            k = self.ids(n)
            p = F.partition(k)
            self.assertEqual(p["U"], k, n)
            self.assertEqual(p["予備"], [], n)
            self.assertEqual((len(p["調整用"]), len(p["評価用"])), (tune, ev), n)
            self.assertEqual(p["調整用"] + p["評価用"], p["U"], n)                            # 先頭 ⌊|U|/2⌋ が調整用・残りが評価用
            self.assertFalse(p["停止"], n)

    def test_13_under_12_stops_and_exactly_12_does_not(self):
        self.assertTrue(F.partition(self.ids(11))["停止"])
        self.assertTrue(F.partition(self.ids(0))["停止"])
        self.assertFalse(F.partition(self.ids(12))["停止"])
        self.assertFalse(F.partition(self.ids(20))["停止"])
        self.assertFalse(F.partition(self.ids(25))["停止"])

    def test_14_more_than_20_leaves_the_rest_as_reserve_in_order(self):
        k = self.ids(27)
        p = F.partition(k)
        self.assertEqual(p["予備"], k[20:])
        self.assertEqual(len(p["U"]), 20)
        self.assertEqual(p["U"] + p["予備"], k)

    def test_15_the_seal_states_the_same_rules_in_words(self):
        for s in ("U = K の先頭 20 件", "調整用 = U の先頭 ⌊|U| / 2⌋ 件", "|U| < 12 なら止める", '("A", "B", "C")[i % 3]',
                  "A 4・B 3・C 3", "A 3・B 4・C 3"):
            self.assertIn(s, SEAL_TEXT)
        self.assertEqual((F.U_SIZE, F.U_MIN), (20, 12))


class SealedConstants(unittest.TestCase):
    """封の字で決めた定数が script と同じ。"""

    def test_16_urls_paths_and_query_are_the_sealed_ones(self):
        for kind, tail in (("financials", "/financials?years=3&include_nulls=true&include_null_reasons=true"),
                           ("companies", ""), ("ratios", "/ratios")):
            sealed = "https://edinetdb.jp/v1/companies/{EDINETコード}" + tail
            self.assertIn("`GET %s`" % sealed, SEAL_TEXT, kind)
            self.assertEqual(F.BASE_URL + F.ENDPOINT_PATHS[kind] % "{EDINETコード}", sealed)

    def test_17_limit_retries_and_the_two_preview_calls(self):
        self.assertIn("1 日(JST)95 回", SEAL_TEXT)
        self.assertEqual(F.DAILY_LIMIT, 95)
        self.assertIn("2 回の呼び出し", SEAL_TEXT)
        self.assertIn("1 日 95 回の上限に数える", SEAL_TEXT)
        self.assertEqual(F.PRIOR_USES, {"2026-10-27": 2})
        self.assertIn("60 秒待って 2 回まで再試行", SEAL_TEXT)
        self.assertEqual((F.MAX_RETRIES, F.RETRY_WAIT_SEC), (2, 60.0))

    def test_18_places_names_and_the_header(self):
        self.assertIn("~/.cache/audit-core/edinetdb-p27/<docID>/{financials,companies,ratios}.json", SEAL_TEXT)
        self.assertEqual(F.P27_CACHE_DIR_NAME, "edinetdb-p27")
        self.assertIn("fixtures/xbrl/p27/dbfetch_2026-10-27.json", SEAL_TEXT)
        self.assertEqual(F.OUT_REL, os.path.join("fixtures", "xbrl", "p27", "dbfetch_2026-10-27.json"))
        self.assertIn("ヘッダ `X-API-Key`", SEAL_TEXT)
        self.assertIn("`EDINETDB_API_KEY`", SEAL_TEXT)
        self.assertEqual(F.KEY_NAME, "EDINETDB_API_KEY")
        self.assertEqual((F.FRESH_ZIP_DIR_NAME, F.EXISTING_CACHE_DIR_NAME), ("edinet-fresh-2026-10-21", "edinet"))
        self.assertIn("固定の 1 文「%s」" % F.PROBE_SENTENCE, SEAL_TEXT)


class PromptsAreTheSealedText(unittest.TestCase):
    """§3-3 と §5-6 の指示文が、封の文書のコード塊と 1 字も違わない。"""

    def test_19_writer_template_is_the_sealed_block_to_the_character(self):
        block = seal_code_block(r"3\. \*\*指示文\(この字のとおり。[^\n]*")
        self.assertEqual(P.WRITER_TEMPLATE, block)
        self.assertEqual(len(P.WRITER_TEMPLATE), len(block))

    def test_20_reader_prompt_is_the_sealed_block_to_the_character(self):
        block = seal_code_block(r"6\. \*\*読み手の指示文\(この字のとおり\)\*\*:")
        self.assertEqual(P.READER_PROMPT, block)

    def test_21_type_sentences_are_the_sealed_three(self):
        sealed = seal_type_sentences()
        self.assertEqual(sorted(sealed), ["A", "B", "C"])
        self.assertEqual(P.TYPE_SENTENCES, sealed)

    def test_22_template_has_exactly_the_four_sealed_placeholders_once_each(self):
        for ph in P.PLACEHOLDERS:
            self.assertEqual(P.WRITER_TEMPLATE.count(ph), 1, ph)
        self.assertEqual(P.PLACEHOLDERS, ("{型の文}", "{companies の JSON}", "{financials の JSON}", "{ratios の JSON}"))
        # {…} の字はこの 4 つだけ
        self.assertEqual(sorted(re.findall(r"\{[^}]*\}", P.WRITER_TEMPLATE)), sorted(P.PLACEHOLDERS))
        self.assertEqual(re.findall(r"\{[^}]*\}", P.READER_PROMPT), [])

    def test_23_render_fills_only_the_placeholders_in_one_pass(self):
        out = P.render_writer_prompt("B", "<C>", "<F>", "<R>")
        self.assertIn("5. 形は次の型で書いてください: " + P.TYPE_SENTENCES["B"] + "\n", out)
        self.assertIn("会社の情報(companies):\n<C>\n\n財務の数(financials):\n<F>\n\n財務の比率(ratios):\n<R>", out)
        self.assertNotIn("{", out)
        # 埋め込んだ JSON の中に置き換えの字があっても、再び置き換えない
        tricky = P.render_writer_prompt("A", '{"a": "{型の文}"}', "{ratios の JSON}", "{companies の JSON}")
        self.assertEqual(tricky.count("{型の文}"), 1)
        self.assertEqual(tricky.count("{ratios の JSON}"), 1)
        self.assertEqual(tricky.count("{companies の JSON}"), 1)
        expected = (P.WRITER_TEMPLATE.replace("{型の文}", P.TYPE_SENTENCES["A"]).replace("{companies の JSON}", "c")
                    .replace("{financials の JSON}", "f").replace("{ratios の JSON}", "r"))
        self.assertEqual(P.render_writer_prompt("A", "c", "f", "r"), expected)

    def test_24_writer_prompt_leaves_out_what_the_seal_forbids_it_to_say(self):
        # §3-4: Audit Core・検証・照合・「後で原本と比べる」こと・P26 の規則・§0-2 の 4 つの型・前の 3 本の文。数の書き方を指図しない
        for w in ("Audit Core", "検証", "照合", "原本", "XBRL", "有価証券", "P26", "P22", "括弧", "前期比", "要因", "減益", "ソニー", "トヨタ", "任天堂"):
            self.assertNotIn(w, P.WRITER_TEMPLATE, w)
        for t in P.TYPE_SENTENCES.values():
            for w in ("括弧", "前期比", "要因", "Audit Core", "検証"):
                self.assertNotIn(w, t, w)

    def test_25_the_seal_blocks_are_found_exactly_once(self):
        # 抜き出しの規則が、封の文書にコード塊をちょうど 2 つ(書き手・読み手)と見ている
        self.assertEqual(SEAL_TEXT.count("\n```\n"), 4)


if __name__ == "__main__":
    unittest.main()
