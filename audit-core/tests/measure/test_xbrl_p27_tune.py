# -*- coding: utf-8 -*-
"""調整用の測定 script(measure/xbrl_p27_tune_2026-10-27.py)の試験(封 docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md §4-2・§5・§6・§10-4 前半)。
通信しない・鍵を使わない(偽の鍵)・本物の cache に書かない。engine と ZIP の中身は作り物(StubBackend)に替える。

**「X に書かない」「X を開かない」を試す試験は、先に置き場を使い捨ての folder に向ける**(置き場を本物に戻す変異でも本物の cache には届かない)。
偽の docID は実在の書類番号の接頭辞を使わず、部品から組む(引きの門 test_xbrl_fresh_seal test_23 が追跡 file の docID を数える)。"""
import ast
import contextlib
import importlib.util
import io
import json
import os
import random
import shutil
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.environ.get("P27_TUNE_SCRIPT", os.path.join(ROOT, "measure", "xbrl_p27_tune_2026-10-27.py"))
REAL_BASE = os.path.expanduser("~/.cache/audit-core")
REAL_DIRS = [os.path.join(REAL_BASE, "edinet"), os.path.join(REAL_BASE, "edinet-fresh-2026-10-21"),
             os.path.join(REAL_BASE, "edinetdb-p27")]

spec = importlib.util.spec_from_file_location("p27_tune", SCRIPT)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

# 偽の鍵(固定の字面を file に置かない。tests/core/test_boundary.py の型にも当たらない)
FAKE_KEY = "".join(["Ab3dE6gH9jK2mN5pQ8sT1vW4yZ7", "cF0xR"])        # 32 字
LONG_NAME = "NetCashProvidedByUsedInOperatingActivities"         # 要素の名前(32 字以上の英字)
SENTINEL_COMPANY = u"秘密の会社名テスト"                            # 文と DB の応答の中の字(記録の中に入ってはならない)
SENTINEL_REASON = u"理由の自由文テスト一"
SENTINEL_SHAPE = u"道五の形を書いた十字以上の字"

DOC_PREFIX = "ZZ0"
TUNE = [DOC_PREFIX + "TUN01", DOC_PREFIX + "TUN02", DOC_PREFIX + "TUN03"]
EVAL = [DOC_PREFIX + "EVA01", DOC_PREFIX + "EVA02"]
STYLE = {TUNE[0]: "A", TUNE[1]: "B", TUNE[2]: "C", EVAL[0]: "A", EVAL[1]: "B"}


def _listing(folder):
    return sorted(os.listdir(folder)) if os.path.isdir(folder) else None


_BEFORE = {}


def setUpModule():
    for d in REAL_DIRS:
        _BEFORE[d] = _listing(d)


def tearDownModule():
    for d in REAL_DIRS:         # 本物の cache の件数と名前が試験の前と同じ(この試験は本物の cache に 1 file も足さない)
        assert _listing(d) == _BEFORE[d], "本物の cache が試験で変わった: %s" % d


def sha(b):
    return M.sha256_hex(b)


def fact(name, ctx, value, unit="JPY"):
    return {"name": name, "context": ctx, "unit": unit, "decimals": "-6", "value": value}


SMALL_FACTS = [fact("jppfs_cor:NetSales", "CurrentYearDuration", 5000000000.0),
               fact("jppfs_cor:NetSales", "Prior1YearDuration", 2000000000.0),
               fact("jppfs_cor:OperatingIncome", "CurrentYearDuration", 430000000.0),
               fact("jppfs_cor:TotalAssets", "CurrentYearInstant", 1200000000.0)]
# 4 つが合い(P22・P26 とも GROUNDED)、999 億円は合う fact が無い(P22: 名指して VALUE_MISMATCH / P26: no_same_value で止める)
SMALL_TEXT = (SENTINEL_COMPANY + u" 決算\n\n・売上高は50億円で、前期の20億円から増えた。\n・営業利益は4.3億円、経常利益は999億円だった。\n"
              u"・総資産は1,200百万円だった。")

BIG_N = 60
BIG_FACTS = [fact("jppfs_cor:Item%02d" % i, "CurrentYearDuration", float(i * 1000) * 1e6) for i in range(1, BIG_N + 1)]
BIG_TEXT = u"大きい文\n" + u"\n".join(u"・項目%d は%s百万円だった。" % (i, "{:,}".format(i * 1000)) for i in range(1, BIG_N + 1))


class World(object):
    """偽の repo の根・ZIP・文・DB の応答・既存の cache。"""

    def __init__(self, tmp, texts=None, facts=None):
        self.tmp = tmp
        self.root = os.path.join(tmp, "root")
        self.zip_dir = os.path.join(tmp, "zips")
        self.cache_root = os.path.join(tmp, "p27cache")
        self.existing = os.path.join(tmp, "existing")
        self.outside = os.path.join(tmp, "outside")
        self.out = os.path.join(tmp, "out", "rec.json")
        self.texts = dict((d, SMALL_TEXT) for d in TUNE + EVAL)
        self.texts.update(texts or {})
        self.facts = dict((d, SMALL_FACTS) for d in TUNE + EVAL)
        self.facts.update(facts or {})
        for d in (self.zip_dir, self.existing, os.path.join(self.cache_root, "reports"),
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
            open(os.path.join(self.cache_root, "reports", d + ".txt"), "wb").write(rb)
            open(os.path.join(self.zip_dir, d + ".zip"), "wb").write(zb)
            os.makedirs(os.path.join(self.cache_root, d))
            for kind in ("financials", "companies", "ratios"):
                b = (json.dumps({"kind": kind, "name": SENTINEL_COMPANY, "doc": d}, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
                self.db_bytes[(d, kind)] = b
                open(os.path.join(self.cache_root, d, kind + ".json"), "wb").write(b)
                calls.append({"docID": d, "種類": kind, "sha256": sha(b)})
            companies.append({"docID": d, "区分": "調整用" if d in TUNE else "評価用", "型": STYLE[d], "文の sha256": sha(rb)})
            zip_rows.append({"docID": d, "sha256": sha(zb)})
        self.write_json("fixtures/xbrl/p27/reports_2026-10-27.json", {"会社": companies})
        self.write_json("fixtures/xbrl/p27/dbfetch_2026-10-27.json", {"呼び出し": calls})
        self.write_json("fixtures/xbrl/fresh/fetched_2026-10-21.json", {"取得した書類": zip_rows})
        self.log = []

    def write_json(self, rel, obj):
        io.open(os.path.join(self.root, rel), "w", encoding="utf-8").write(json.dumps(obj, ensure_ascii=False))

    def common(self, **kw):
        a = dict(root=self.root, out=self.out, outside_dir=self.outside, zip_dir=self.zip_dir, cache_root=self.cache_root,
                 existing_dir=self.existing, git_dir=ROOT, backend=M.StubBackend(), say=self.log.append)
        a.update(kw)
        return a

    def judge(self, **kw):
        return M.run_judge(**self.common(**kw))

    def inject(self, **kw):
        a = self.common(seed_fn=lambda path: ("test-seed", {"sealed_in_commit": "x", "seed_file_sha256": "y"}), work_root=os.path.join(self.tmp, "work"))
        a.update(kw)
        return M.run_inject(**a)

    def record(self):
        return json.load(io.open(self.out, encoding="utf-8"))

    def record_text(self):
        return io.open(self.out, encoding="utf-8").read()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p27tune_", dir=os.environ.get("TMPDIR"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.w = World(self.tmp)


@contextlib.contextmanager
def open_spy():
    """io.open で開いた path の一覧(script は file を io.open でだけ開く)。"""
    opened = []
    real = io.open

    def spy(file, *a, **kw):
        opened.append(str(file))
        return real(file, *a, **kw)
    with mock.patch("io.open", spy):
        yield opened


class TestEvalStop(Base):
    def test_01_eval_docid_stops_before_any_material_is_opened(self):
        for fn in (lambda **k: self.w.judge(**k), lambda **k: self.w.inject(**k)):
            with open_spy() as opened:
                with self.assertRaises(M.Stop) as cm:
                    fn(docs=[EVAL[0]])
            self.assertIn("評価用", str(cm.exception))
            bad = [p for p in opened if EVAL[0] in p or os.sep + "reports" + os.sep in p or p.endswith(".zip")
                   or os.path.join(self.w.cache_root, TUNE[0]) in p]
            self.assertEqual(bad, [], bad)
            self.assertFalse(os.path.exists(self.w.out))
            self.assertFalse(os.path.exists(self.w.outside))

    def test_02_a_tuning_doc_listed_before_an_eval_doc_is_not_opened_either(self):
        with open_spy() as opened:
            with self.assertRaises(M.Stop):
                self.w.judge(docs=[TUNE[0], EVAL[1]])
        self.assertEqual([p for p in opened if os.sep + "reports" + os.sep in p or p.endswith(".zip")], [])

    def test_03_a_doc_that_is_not_tuning_stops_too(self):
        with open_spy() as opened:
            with self.assertRaises(M.Stop):
                self.w.judge(docs=["ZZ0NONE01"])
        self.assertEqual([p for p in opened if os.sep + "reports" + os.sep in p], [])

    def test_04_every_loader_refuses_an_eval_doc_without_opening(self):
        ctx = M.Ctx(self.w.root, self.w.zip_dir, self.w.cache_root, self.w.existing, self.w.outside, None, None)
        self.assertEqual(ctx.docs, TUNE)
        for name in ("read_report", "read_zip", "read_db", "zip_path"):
            with open_spy() as opened:
                with self.assertRaises(M.Stop):
                    getattr(ctx, name)(EVAL[1])
            self.assertEqual(opened, [], name)

    def test_05_ctx_eval_list_comes_from_the_W_record(self):
        ctx = M.Ctx(self.w.root, self.w.zip_dir, self.w.cache_root, self.w.existing, self.w.outside, None, None)
        self.assertEqual(sorted(ctx.eval_ids), sorted(EVAL))
        self.assertEqual(ctx.tuning, TUNE)

    def test_06_default_docs_are_only_the_tuning_docs(self):
        with open_spy() as opened:
            self.w.judge()
        self.assertFalse([p for p in opened if any(e in p for e in EVAL)], "評価用の docID の path を開いた")
        self.assertEqual(self.w.record()["対象の docID"], TUNE)


class TestJudge(Base):
    def test_10_record_has_no_span_subject_value_recomputed_and_no_text_or_db_chars(self):
        self.w.judge()
        txt = self.w.record_text()
        rec = json.loads(txt)
        self.assertEqual(sorted(set(k for k in M.walk_keys(rec) if k in M.FORBIDDEN_RECORD_KEYS)), [])
        for forbidden in ('"span"', '"subject"', '"value"', '"recomputed"'):
            self.assertNotIn(forbidden, txt)
        self.assertNotIn(SENTINEL_COMPANY, txt)                       # 文と DB の応答の字
        self.assertNotIn(u"売上高", txt)
        for row in rec["claim"]:
            self.assertEqual(sorted(row), ["P22", "P26", "docID", "id"])
            for p in ("P22", "P26"):
                self.assertEqual(sorted(row[p]), sorted(M.RECORD_CLAIM_FIELDS))
        # 全部の欄は repo の外に在り、sha256 が記録と同じ
        full = open(os.path.join(self.w.outside, "judge_full.json"), "rb").read()
        self.assertEqual(rec["repo の外に置いたもの"]["全部の欄(span・subject・value・recomputed を含む)"]["sha256"], sha(full))
        self.assertIn('"subject"', full.decode("utf-8"))                       # 外の file には全部の欄(span・subject・value・recomputed)がある
        self.assertIn(u"億円", full.decode("utf-8"))
        self.assertIn('"recomputed"', full.decode("utf-8"))

    def test_11_forbidden_keys_and_claim_record_fields(self):
        c = {"id": "N001", "kind": "num", "form": "direct_value", "subject": u"科目", "value": 5.0, "unit": u"円", "word": None,
             "span": u"文の字", "state": "GROUNDED", "pointers": ["xbrl:a:b@c"], "reason": None, "recomputed": 5.0}
        r = M.claim_record(c)
        self.assertEqual(sorted(r), sorted(M.RECORD_CLAIM_FIELDS))
        self.assertEqual(r["state"], "GROUNDED")
        for k in M.FORBIDDEN_RECORD_KEYS:
            with self.assertRaises(M.Stop):
                M.assert_record_clean({"a": [{"b": {k: 1}}]})

    def test_12_reason_and_pointers_must_be_code_shaped(self):
        base = {"kind": "num", "form": "f", "unit": u"円", "state": "VALUE_MISMATCH", "pointers": [], "reason": None}
        for reason in ("no_same_value", "no_element(unit not in XBRL)", "ambiguous(elements)"):
            self.assertEqual(M.claim_record(dict(base, reason=reason))["reason"], reason)
        for reason in (u"売上高が5,000と違う", "value 5000000", u"no_element(5000)"):
            with self.assertRaises(M.Stop):
                M.claim_record(dict(base, reason=reason))
        for p in ("xbrl:jppfs_cor:NetSales@CurrentYearDuration", "formula:a/b*100", "builtin:flow_sign(cur)==direction"):
            self.assertEqual(M.claim_record(dict(base, pointers=[p]))["pointers"], [p])
        with self.assertRaises(M.Stop):
            M.claim_record(dict(base, pointers=[u"売上高 5,000"]))
        with self.assertRaises(M.Stop):
            M.claim_record(dict(base, state="OTHER"))

    def test_13_read_row_conditions(self):
        def c(state, reason=None):
            return {"state": state, "reason": reason}
        f = M.read_row_conditions
        self.assertEqual(f(c("VALUE_MISMATCH"), c("GROUNDED")), ["P22_VALUE_MISMATCH"])
        self.assertEqual(f(c("GROUNDED"), c("VALUE_MISMATCH")), ["P26_VALUE_MISMATCH"])
        self.assertEqual(f(c("VALUE_MISMATCH"), c("VALUE_MISMATCH")), ["P26_VALUE_MISMATCH", "P22_VALUE_MISMATCH"])
        self.assertEqual(f(c("GROUNDED"), c("POINTER_NOT_FOUND", "no_same_value")), ["P26_POINTER_NOT_FOUND_no_same_value"])
        self.assertEqual(f(c("VALUE_MISMATCH"), c("POINTER_NOT_FOUND", "no_same_value")),
                         ["P22_VALUE_MISMATCH", "P26_POINTER_NOT_FOUND_no_same_value"])
        # 読まない: no_same_value 以外の理由・UNVERIFIABLE の no_same_value・P22 側の no_same_value
        self.assertEqual(f(c("GROUNDED"), c("POINTER_NOT_FOUND", "no_element")), [])
        self.assertEqual(f(c("GROUNDED"), c("POINTER_NOT_FOUND", "no_same_value_x")), [])
        self.assertEqual(f(c("GROUNDED"), c("UNVERIFIABLE", "no_same_value")), [])
        self.assertEqual(f(c("POINTER_NOT_FOUND", "no_same_value"), c("GROUNDED")), [])
        self.assertEqual(f(c("GROUNDED"), c("GROUNDED")), [])
        self.assertEqual(f(None, None), [])
        self.assertEqual(f(None, c("VALUE_MISMATCH")), ["P26_VALUE_MISMATCH"])

    def test_14_read_rows_in_a_run(self):
        rec = self.w.judge()
        rows = rec["読む行"]
        # 偽の文は 999 億円の 1 行だけが、P22: VALUE_MISMATCH・P26: POINTER_NOT_FOUND(no_same_value) になる(調整用 3 社)
        self.assertEqual(len(rows), 3)
        for r in rows:
            self.assertEqual(r["条件"], ["P22_VALUE_MISMATCH", "P26_POINTER_NOT_FOUND_no_same_value"])
        by = dict(((c["docID"], c["id"]), c) for c in rec["claim"])
        for r in rows:
            self.assertEqual(by[(r["docID"], r["id"])]["P22"]["state"], "VALUE_MISMATCH")
            self.assertEqual(by[(r["docID"], r["id"])]["P26"]["reason"], "no_same_value")
        picked = set((r["docID"], r["id"]) for r in rows)
        others = [k for k in by if k not in picked]
        self.assertTrue(all(by[k]["P22"]["state"] == "GROUNDED" and by[k]["P26"]["state"] == "GROUNDED" for k in others))
        self.assertEqual(rec["集計"]["読む行"]["数"], 3)
        self.assertEqual(rec["集計"]["claim"], {"P22": 15, "P26": 15})

    def test_15_summary_counts_and_style_medians(self):
        rec = self.w.judge()
        self.assertEqual(rec["集計"]["state の数"]["P22"]["VALUE_MISMATCH"], 3)
        self.assertEqual(rec["集計"]["state の数"]["P26"]["POINTER_NOT_FOUND"], 3)
        self.assertEqual(rec["集計"]["VALUE_MISMATCH の率"]["P22"], {"件": 3, "分母": 15, "率": 20.0})
        self.assertEqual(rec["集計"]["VALUE_MISMATCH の率"]["P26"]["件"], 0)
        med = rec["集計"]["文あたりの claim の数(P26)の型ごと"]
        self.assertEqual((med["A"]["中央値"], med["B"]["中央値"], med["C"]["中央値"]), (5, 5, 5))
        # 文体の型は W の記録から
        self.assertEqual([c["型"] for c in rec["会社"]], ["A", "B", "C"])

    def test_16_claims_are_paired_by_id_and_differences_are_recorded(self):
        class Skew(M.StubBackend):
            def verify(self, zb, profile, text):
                out = M.StubBackend.verify(self, zb, profile, text)
                if profile == "P26":
                    out["claims"] = out["claims"][1:]          # 先頭の id が P26 に無い
                    out["claims"][0]["span"] = u"別の窓"
                return out
        rec = self.w.judge(backend=Skew())
        c0 = rec["会社"][0]
        self.assertEqual(c0["片方の profile にしか無い id"], ["N001"])
        self.assertEqual(c0["値・span・単位が profile 間で違う id"], ["N002"])
        row = [r for r in rec["claim"] if r["docID"] == TUNE[0] and r["id"] == "N001"][0]
        self.assertIsNone(row["P26"])

    def test_17_dossier_has_paragraph_both_profiles_facts_and_db(self):
        rec = self.w.judge()
        d = os.path.join(self.w.outside, "dossier")
        r = rec["読む行"][0]
        body = io.open(os.path.join(d, "%s__%s.txt" % (r["docID"], r["id"])), encoding="utf-8").read()
        self.assertIn(u"経常利益は999億円だった", body)                         # 文の段落
        self.assertNotIn(u"総資産は1,200百万円", body)                          # 箇条書きは、かかる行だけ
        self.assertIn("(P22)", body)
        self.assertIn("(P26)", body)
        self.assertIn('"state": "VALUE_MISMATCH"', body)
        self.assertIn('"reason": "no_same_value"', body)
        self.assertIn('"subject"', body)                                       # claim の全部の欄
        self.assertIn("jppfs_cor:NetSales", body)                              # pointers の fact
        self.assertIn("context=Prior1YearDuration", body)                      # 同じ要素の別の context の fact
        self.assertIn("◀ 名指し", body)
        for kind in ("companies", "financials", "ratios"):
            self.assertIn(self.w.db_bytes[(r["docID"], kind)].decode("utf-8"), body)
        # 読み手の指示文は封の字のまま。repo の記録には文の段落も DB の字も無い
        self.assertEqual(open(os.path.join(d, "reader_prompt.txt"), "rb").read(), M.PR.READER_PROMPT.encode("utf-8"))
        info = rec["repo の外に置いたもの"]["dossier"]
        self.assertEqual(info["読み手の指示文 reader_prompt.txt の sha256"], sha(M.PR.READER_PROMPT.encode("utf-8")))
        self.assertTrue(info["読み手の指示文は封 §5-6 の字(prompts の READER_PROMPT)と同じ"])
        self.assertEqual(info["index.json の sha256"], sha(open(os.path.join(d, "index.json"), "rb").read()))
        self.assertEqual(info["件数"], len(rec["読む行"]))
        for row in json.load(io.open(os.path.join(d, "index.json"), encoding="utf-8"))["rows"]:
            self.assertEqual(info["各 file の sha256"][row["行"]], row["sha256"])
            self.assertEqual(row["sha256"], sha(open(os.path.join(d, row["file"]), "rb").read()))
        self.assertNotIn(u"経常利益は999億円", self.w.record_text())

    def test_18_paragraph_of(self):
        text = u"題\n\n見出し\n本文一。本文二。\n\n・箇条一は11円。\n・箇条二は22円。\n・箇条三は33円。"
        p, note = M.paragraph_of(text, u"本文一。")
        self.assertEqual((p, note), (u"見出し\n本文一。本文二。", ""))
        p, _ = M.paragraph_of(text, u"箇条二は22円")
        self.assertEqual(p, u"・箇条二は22円。")
        p, _ = M.paragraph_of(text, u"一は11円。\n・箇条二")
        self.assertEqual(p, u"・箇条一は11円。\n・箇条二は22円。")
        p, note = M.paragraph_of(text, u"どこにも無い")
        self.assertEqual(p, text)
        self.assertTrue(note)
        p, note = M.paragraph_of(text, None)
        self.assertEqual(p, text)

    def test_19_dossier_lists_facts_once_and_marks_named(self):
        facts = [fact("a:X", "C1", 1.0), fact("a:X", "C1", 1.0), fact("a:X", "C2", 2.0), fact("a:Y", "C1", 9.0)]
        lines = M.fact_lines(facts, ["xbrl:a:X@C2", "builtin:z(1)"])
        self.assertEqual(sum(1 for ln in lines if "context=C1" in ln), 1)
        self.assertEqual([ln for ln in lines if "名指し" in ln][0].split()[0], "context=C2")
        self.assertFalse([ln for ln in lines if "a:Y" in ln or "value=9.0" in ln])
        self.assertIn("builtin:z(1)", " ".join(lines))


class TestHeaderAndCache(Base):
    def test_20_header_has_head_w_seal_sha_and_cache(self):
        rec = self.w.judge()
        self.assertEqual(rec["seal"], "audit-core/docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md")
        self.assertRegex(rec["HEAD の commit"], r"^[0-9a-f]{40}$")
        self.assertTrue(rec["W の commit"].startswith("c48f464"))
        self.assertTrue(rec["W は HEAD の祖先"])
        self.assertEqual(rec["使った文の sha256"], dict((d, sha(self.w.report_bytes[d])) for d in TUNE))
        self.assertEqual(rec["この script の sha256"], sha(open(SCRIPT, "rb").read()))
        self.assertTrue(rec["cache の前後"]["変化なし"])
        self.assertEqual(rec["cache の前後"]["前"]["既存の cache"]["件数"], 3)
        self.assertEqual(rec["cache の前後"]["前"]["ZIP の folder"]["件数"], 5)
        self.assertEqual(rec["cache の前後"]["前"]["既存の cache"]["名前の一覧の sha256"], sha("\n".join(["X0.zip", "X1.zip", "X2.zip"]).encode("utf-8")))
        self.assertTrue(rec["dry_run"] is False)

    def test_21_nothing_is_added_to_the_two_protected_folders(self):
        before = (_listing(self.w.existing), _listing(self.w.zip_dir))
        self.w.judge()
        self.w.out = os.path.join(self.tmp, "out", "inj.json")
        self.w.inject()
        self.assertEqual((_listing(self.w.existing), _listing(self.w.zip_dir)), before)

    def test_22_a_backend_that_writes_into_the_zip_folder_stops_the_run_without_a_record(self):
        zip_dir = self.w.zip_dir

        class Writer(M.StubBackend):
            def verify(self, zb, profile, text):
                open(os.path.join(zip_dir, "stray.zip"), "wb").write(b"x")
                return M.StubBackend.verify(self, zb, profile, text)
        for fn in (lambda: self.w.judge(backend=Writer()), lambda: self.w.inject(backend=Writer())):
            with self.assertRaises(M.Stop) as cm:
                fn()
            self.assertIn("変わった", str(cm.exception))
            self.assertFalse(os.path.exists(self.w.out))
            os.remove(os.path.join(zip_dir, "stray.zip"))

    def test_23_outside_and_work_folders_may_not_be_inside_the_protected_folders_or_the_repo(self):
        for bad in (os.path.join(self.w.zip_dir, "tune"), os.path.join(self.w.existing, "tune"), os.path.join(self.w.root, "tune")):
            with self.assertRaises(M.Stop):
                self.w.judge(outside_dir=bad)
        with self.assertRaises(M.Stop):
            self.w.inject(work_root=os.path.join(self.w.existing, "work"))
        with self.assertRaises(M.Stop):
            self.w.inject(work_root=os.path.join(self.w.zip_dir, "work"))
        self.assertEqual(_listing(self.w.existing), ["X0.zip", "X1.zip", "X2.zip"])

    def test_24_default_work_folder_is_under_TMPDIR(self):
        seen = []

        class Spy(M.StubBackend):
            def refs(self, zip_path, doc, work):
                seen.append(work)
                return M.StubBackend.refs(self, zip_path, doc, work)
        tmpdir = os.path.join(self.tmp, "tmpdir")
        os.makedirs(tmpdir)
        with mock.patch.dict(os.environ, {"TMPDIR": tmpdir}):
            self.w.inject(backend=Spy(), work_root=None)
        self.assertTrue(seen)
        for s in seen:
            self.assertTrue(os.path.realpath(s).startswith(os.path.realpath(tmpdir) + os.sep), s)

    def test_25_sha_mismatch_of_a_report_zip_or_db_response_stops(self):
        for rel, name in ((os.path.join(self.w.cache_root, "reports", TUNE[0] + ".txt"), "文"), (os.path.join(self.w.zip_dir, TUNE[0] + ".zip"), "ZIP")):
            orig = open(rel, "rb").read()
            open(rel, "wb").write(orig + b" ")
            with self.assertRaises(M.Stop) as cm:
                self.w.judge()
            self.assertIn("sha256", str(cm.exception))
            open(rel, "wb").write(orig)
        p = os.path.join(self.w.cache_root, TUNE[0], "ratios.json")
        orig = open(p, "rb").read()
        open(p, "wb").write(orig + b" ")
        with self.assertRaises(M.Stop) as cm:
            self.w.judge()                   # 読む行が在る会社では DB の応答も確かめる
        self.assertIn("DB の応答", str(cm.exception))
        open(p, "wb").write(orig)
        self.w.judge()                       # 元に戻せば通る
        self.assertTrue(os.path.exists(self.w.out))

    def test_26_existing_output_is_not_overwritten(self):
        self.w.judge()
        before = self.w.record_text()
        with self.assertRaises(M.Stop):
            self.w.judge(outside_dir=os.path.join(self.tmp, "outside2"))
        self.assertEqual(self.w.record_text(), before)

    def test_27_the_script_reads_no_secret_and_does_not_touch_the_network(self):
        tree = ast.parse(io.open(SCRIPT, encoding="utf-8").read())
        imported = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                imported |= set(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                imported.add((n.module or "").split(".")[0])
        self.assertFalse(imported & {"urllib", "socket", "http", "requests", "ssl", "anthropic", "openai"}, imported)
        env_reads = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute) and n.attr == "environ":
                env_reads.append(n)
        # 環境変数は TMPDIR だけを読む(鍵の変数を読まない)
        src = io.open(SCRIPT, encoding="utf-8").read()
        self.assertEqual(src.count("os.environ"), 1)
        self.assertIn('os.environ.get("TMPDIR")', src)


class TestKeyCheck(Base):
    def test_30_key_like_strings_are_refused_before_writing(self):
        out = os.path.join(self.tmp, "k", "rec.json")
        with mock.patch.object(M, "write_text", wraps=M.write_text) as wt:         # 書く前に止まる(一度も書かない)
            for obj in ({"step": FAKE_KEY}, {"a": [{"reason": "x" * 5, "note": "A" * 40}]}, {"k": "EDINETDB_API_KEY=abcdefgh1234"}):
                with self.assertRaises(M.Stop):
                    M.write_record(out, obj)
                self.assertFalse(os.path.exists(out))
            with self.assertRaises(M.Stop):
                M.write_record(out, {"何か": "foo " + FAKE_KEY + " bar"}, key_value=FAKE_KEY)
            self.assertFalse(os.path.exists(out))
            self.assertEqual(wt.call_count, 0)

    def test_31_sha256_hex_and_element_names_in_pointers_and_git_commits_pass(self):
        out = os.path.join(self.tmp, "k", "ok.json")
        obj = {"sha": "a" * 64, "claim": [{"pointers": ["xbrl:jppfs_cor:%s@CurrentYearDuration" % LONG_NAME]}],
               "HEAD の commit": "0123456789abcdef0123456789abcdef01234567", "x": {"sealed_in_commit": "f" * 40}}
        M.write_record(out, obj)
        self.assertTrue(os.path.exists(out))

    def test_32_pointers_still_get_the_hex32_and_env_key_checks(self):
        out = os.path.join(self.tmp, "k", "p.json")
        with self.assertRaises(M.Stop):
            M.write_record(out, {"c": [{"pointers": ["xbrl:a:" + "0123456789abcdef" * 2]}]})
        with self.assertRaises(M.Stop):
            M.write_record(out, {"c": [{"pointers": ["xbrl:a:" + FAKE_KEY]}]}, key_value=FAKE_KEY)
        self.assertFalse(os.path.exists(out))

    def test_33_a_commit_looking_string_in_another_field_is_not_exempt(self):
        out = os.path.join(self.tmp, "k", "c.json")
        with self.assertRaises(M.Stop):
            M.write_record(out, {"memo": "0123456789abcdef0123456789abcdef01234567"})
        with self.assertRaises(M.Stop):
            M.write_record(out, {"HEAD の commit": "0123456789abcdef" * 3})               # commit の欄でも 40 桁の 16 進でなければ当てる
        with self.assertRaises(M.Stop):
            M.write_record(out, {"HEAD の commit": "0123456789abcdef0123456789abcdef01234567"}, key_value="0123456789abcdef0123456789abcdef01234567")

    def test_34_the_record_is_scanned_again_after_writing(self):
        out = os.path.join(self.tmp, "k", "after.json")
        real = M.write_text

        def corrupt(path, text):
            obj = json.loads(text)
            obj["混入"] = FAKE_KEY
            real(path, json.dumps(obj))
        with mock.patch.object(M, "write_text", corrupt):
            with self.assertRaises(M.Stop):
                M.write_record(out, {"a": 1})
        self.assertFalse(os.path.exists(out))               # 書いた後に見つかれば消して止める

    def test_35_real_records_of_a_run_are_scanned(self):
        rec = self.w.judge()
        self.assertEqual(M.record_key_leaks(rec), [])
        self.assertEqual(M.record_key_leaks(dict(rec, 余り=FAKE_KEY)), ["32 字以上の英数字の連なり(長さ 32)"])


class TestReconcile(Base):
    def label(self, key, side, det=None, shape=None, why=u"理由"):
        return {"行": key, "側": side, "細目": det, "道5の形": shape, "理由": why}

    def seat_file(self, name, labels):
        p = os.path.join(self.tmp, name + ".json")
        io.open(p, "w", encoding="utf-8").write(json.dumps({"席": name, "札": labels}, ensure_ascii=False))
        return p

    def setup_judge(self):
        self.jrec = self.w.judge()
        self.jpath = self.w.out
        self.w.out = os.path.join(self.tmp, "out", "readings.json")
        self.keys = [r["行"] for r in self.jrec["読む行"]]
        self.assertEqual(len(self.keys), 3)

    def run_rec(self, a, b, **kw):
        args = self.w.common(seat_a=a, seat_b=b, judge_record=self.jpath, backend=None)
        args.update(kw)
        return M.run_reconcile(**args)

    def test_40_combine_rule(self):
        c = M.combine
        self.assertEqual(c(("文", "文1"), ("文", "文1")), ("文", "文1"))
        self.assertEqual(c(("道具", "道2"), ("道具", "道2")), ("道具", "道2"))
        self.assertEqual(c(("文", "文1"), ("道具", "道1")), ("分からない", None))           # 側が割れる
        self.assertEqual(c(("道具", "道1"), ("分からない", None)), ("分からない", None))
        self.assertEqual(c(("文", "文2"), ("文", "文3")), ("文", "分からない"))              # 側が同じで細目が割れる
        self.assertEqual(c(("道具", "道1"), ("道具", "道5")), ("道具", "分からない"))
        self.assertEqual(c(("分からない", None), ("分からない", None)), ("分からない", None))

    def test_41_validate_label_words(self):
        v = M.validate_label
        self.assertEqual(v(self.label("k", "文", "文4"))[:2], ("文", "文4"))
        self.assertEqual(v(self.label("k", "分からない"))[:2], ("分からない", None))
        shape = u"あ" * 10
        self.assertEqual(v(self.label("k", "道具", "道5", shape))[2], shape)
        self.assertEqual(v(self.label("k", "道具", "道5", u"あ" * 40))[2], u"あ" * 40)
        bad = [self.label("k", "不明"), self.label("k", "文", "文5"), self.label("k", "文", "道1"), self.label("k", "道具", "文1"),
               self.label("k", "道具", "道6"), self.label("k", "道具", None), self.label("k", "文", None),
               self.label("k", "分からない", "文1"), self.label("k", "道具", "道5", None), self.label("k", "道具", "道5", u"あ" * 9),
               self.label("k", "道具", "道5", u"あ" * 41), self.label("k", "道具", "道1", u"あ" * 12), self.label("k", "文", "文1", why=""),
               self.label("k", "文", "文1", why=None), self.label("k", "文 ", "文1"), self.label("k", None)]
        for lab in bad:
            with self.assertRaises(M.Stop, msg=lab):
                v(lab)

    def test_42_reconcile_run_writes_labels_only_and_free_text_outside(self):
        self.setup_judge()
        k0, k1, k2 = self.keys
        a = self.seat_file("a", [self.label(k0, "道具", "道1", why=SENTINEL_REASON), self.label(k1, "文", "文2"),
                                  self.label(k2, "道具", "道5", SENTINEL_SHAPE, SENTINEL_REASON)])
        b = self.seat_file("b", [self.label(k0, "道具", "道1"), self.label(k1, "道具", "道3"),
                                  self.label(k2, "道具", "道5", SENTINEL_SHAPE + u"二", SENTINEL_REASON + u"二")])
        rec = self.run_rec(a, b)
        rows = dict((r["行"], r) for r in rec["行"])
        self.assertEqual(rows[k0]["合わせた"], {"側": "道具", "細目": "道1"})
        self.assertEqual(rows[k1]["合わせた"], {"側": "分からない", "細目": None})
        self.assertEqual(rows[k2]["合わせた"], {"側": "道具", "細目": "道5"})                  # 細目が同じ(道5)なら自由文が違っても同じ
        self.assertEqual(rows[k1]["席1"], {"側": "文", "細目": "文2"})
        self.assertEqual(rows[k1]["席2"], {"側": "道具", "細目": "道3"})
        txt = self.w.record_text()
        for s in (SENTINEL_REASON, SENTINEL_SHAPE):
            self.assertNotIn(s, txt)
        free_path = os.path.join(self.w.outside, "readings_free_text.json")
        free = io.open(free_path, encoding="utf-8").read()
        self.assertIn(SENTINEL_SHAPE, free)
        self.assertIn(SENTINEL_REASON, free)
        self.assertEqual(rec["repo の外に置いたもの"]["道5 の形と各席の理由の文"]["sha256"], sha(open(free_path, "rb").read()))
        self.assertEqual(rec["入力"]["席1 の札の file の sha256"], sha(open(a, "rb").read()))
        self.assertEqual(rec["入力"]["判定の記録の sha256"], sha(open(self.jpath, "rb").read()))
        s = rec["集計"]
        self.assertEqual(s["2 席の側が一致した行"], {"件": 2, "分母": 3, "率": 66.7})
        self.assertEqual(s["合わせた側の内訳"], {"文": 0, "道具": 2, "分からない": 1})
        self.assertEqual(s["P26 で VALUE_MISMATCH の行"]["行"], 0)                           # 偽の判定では P26 は VALUE_MISMATCH を出さない
        self.assertEqual(s["合わせた細目が付いた道具の行"]["道1〜道4"], {"件": 1, "分母": 2, "率": 50.0})
        self.assertEqual(s["合わせた札が文2の行"], 0)
        self.assertEqual(sorted(set(k for k in M.walk_keys(rec) if k in M.FORBIDDEN_RECORD_KEYS)), [])

    def test_43_rows_and_labels_must_be_one_to_one(self):
        self.setup_judge()
        k0, k1, k2 = self.keys
        full = [self.label(k0, "文", "文1"), self.label(k1, "文", "文1"), self.label(k2, "文", "文1")]
        a = self.seat_file("a", full)
        for labels in (full[:2], full + [self.label("ZZ0NONE01:N001", "文", "文1")], full + [full[0]]):
            b = self.seat_file("b", labels)
            with self.assertRaises(M.Stop):
                self.run_rec(a, b)
            self.assertFalse(os.path.exists(self.w.out))
        with self.assertRaises(M.Stop):
            self.run_rec(a, self.seat_file("b", [self.label(k0, "文", "文9")] + full[1:]))      # 札の語が違えば止める
        self.assertFalse(os.path.exists(self.w.out))

    def test_44_p26_value_mismatch_rows_are_counted_from_the_judge_record(self):
        rows = [{"行": "a:1", "席1": {"側": "道具"}, "席2": {"側": "道具"}, "合わせた": {"側": "道具", "細目": "道1"}},
                {"行": "a:2", "席1": {"側": "道具"}, "席2": {"側": "文"}, "合わせた": {"側": "分からない", "細目": None}},
                {"行": "a:3", "席1": {"側": "文"}, "席2": {"側": "文"}, "合わせた": {"側": "文", "細目": "文2"}}]
        jr = {"a:1": {"P26": "VALUE_MISMATCH"}, "a:2": {"P26": "VALUE_MISMATCH"}, "a:3": {"P26": "GROUNDED"}}
        s = M.readings_summary(rows, jr)
        self.assertEqual(s["P26 で VALUE_MISMATCH の行"]["行"], 2)
        self.assertEqual(s["P26 で VALUE_MISMATCH の行"]["道具の率"], {"件": 1, "分母": 2, "率": 50.0})
        self.assertEqual(s["P26 で VALUE_MISMATCH の行"]["分からないの率"], {"件": 1, "分母": 2, "率": 50.0})
        self.assertEqual(s["合わせた札が文2の行"], 1)


class FakeRng(object):
    def __init__(self, script):
        self.script = list(script)
        self.used = 0

    def choice(self, seq):
        assert tuple(seq) == M.T8_R_VALUES
        self.used += 1
        return self.script.pop(0)


def token(text):
    toks = [t for t in M.N.scan(text) if t.unit is not None]
    assert len(toks) == 1, toks
    return toks[0]


def vindex_of(values_yen):
    return M.S._value_index([{"key": "k%d" % i, "value": v, "unit": u"円"} for i, v in enumerate(values_yen)])


class TestT8Rel(unittest.TestCase):
    def test_50_the_r_values_and_try_count_are_the_sealed_ones(self):
        self.assertEqual(M.T8_R_VALUES, (-0.10, -0.03, 0.03, 0.10))
        self.assertEqual(M.T8_TRIES, 4)
        self.assertEqual(M.INJECT_CAP, 40)
        self.assertEqual(M.MONEY_FAMILY, (u"円", u"千円", u"百万円", u"億円", u"兆円"))
        self.assertEqual(M.INJECT_TYPES, ("T1_VALUE", "T8_REL"))

    def test_51_r_comes_from_random_of_seed_doc_claim_id(self):
        tok = token(u"売上高は1,000百万円だった。")
        v = vindex_of([])
        seen = set()
        for i in range(120):
            cid = "N%03d" % i
            exp = random.Random("seed-x:ZZ0DOC01:%s" % cid).choice((-0.10, -0.03, 0.03, 0.10))
            r, new, tries = M.pick_r("seed-x", "ZZ0DOC01", cid, tok, v)
            self.assertEqual((r, tries), (exp, 1), cid)
            seen.add(r)
        self.assertEqual(seen, set((-0.10, -0.03, 0.03, 0.10)))          # 4 値の全部が出る
        a = [M.pick_r("seed-x", "ZZ0DOC01", "N%03d" % i, tok, v)[0] for i in range(40)]
        b = [M.pick_r("seed-y", "ZZ0DOC01", "N%03d" % i, tok, v)[0] for i in range(40)]
        c = [M.pick_r("seed-x", "ZZ0DOC02", "N%03d" % i, tok, v)[0] for i in range(40)]
        self.assertNotEqual(a, b)                                          # 種が変われば別
        self.assertNotEqual(a, c)                                          # docID が変われば別

    def test_52_new_value_is_rounded_to_the_written_digits(self):
        v = vindex_of([])
        cases = [(u"1,234.5百万円", 0.03, 1271.5), (u"1,000百万円", 0.03, 1030.0), (u"12.34億円", 0.10, 13.57),
                 (u"12.34億円", -0.10, 11.11), (u"500千円", -0.03, 485.0), (u"3.0兆円", 0.10, 3.3)]
        for text, r, want in cases:
            tok = token(u"売上は" + text + u"だった。")
            got_r, new, tries = M.pick_r("s", "d", "N001", tok, v, FakeRng([r]))
            self.assertEqual((got_r, tries), (r, 1))
            self.assertAlmostEqual(new, want, places=9, msg=text)
        tok = token(u"売上は1,234.5百万円だった。")
        _r, new, _t = M.pick_r("s", "d", "N001", tok, v, FakeRng([0.03]))
        self.assertEqual(M.N.render_value(new, tok), u"1,271.5")                 # 同じ書き方(区切りと小数の桁)

    def test_53_same_value_or_a_value_in_refs_goes_to_the_next_draw_up_to_four_times(self):
        v = vindex_of([])
        tok = token(u"売上は10億円だった。")                                       # 10 × 1.03 = 10.3 → 10(元と同じ)
        rng = FakeRng([0.03, 0.03, 0.03, -0.10])
        self.assertEqual(M.pick_r("s", "d", "N001", tok, v, rng), (-0.10, 9.0, 4))
        self.assertEqual(rng.used, 4)
        rng = FakeRng([0.03, 0.03, 0.03, 0.03])
        self.assertIsNone(M.pick_r("s", "d", "N001", tok, v, rng))                  # 4 回とも駄目なら None
        self.assertEqual(rng.used, 4)
        rng = FakeRng([0.03, -0.10, 0.10, 0.10])
        self.assertEqual(M.pick_r("s", "d", "N001", tok, v, rng), (-0.10, 9.0, 2))
        # refs のどれかの値と同じ(書かれた単位に直して比べる): 11億円(= 1.1e9 円)が refs に在れば +10% は使えない
        v = vindex_of([1.1e9])
        rng = FakeRng([0.10, -0.10])
        self.assertEqual(M.pick_r("s", "d", "N001", tok, v, rng), (-0.10, 9.0, 2))
        # 別の単位の同じ数字は同じ値でない
        v = vindex_of([11.0])
        self.assertEqual(M.pick_r("s", "d", "N001", tok, v, FakeRng([0.10])), (0.10, 11.0, 1))

    def test_54_a_token_without_an_r_is_not_a_site_and_is_counted(self):
        facts = [fact("jppfs_cor:Item01", "CurrentYearDuration", 1e9), fact("jppfs_cor:Item02", "CurrentYearDuration", 2e9)]
        text = u"・一は10億円だった。\n・二は20億円だった。"
        be = M.StubBackend()
        zb = json.dumps({"facts": facts}).encode("utf-8")
        claims = {"P22": be.verify(zb, "P22", text)["claims"], "P26": be.verify(zb, "P26", text)["claims"]}
        by_id = dict((p, dict((c["id"], c) for c in claims[p])) for p in claims)
        refs = [{"key": f["name"] + "@" + f["context"], "value": f["value"], "unit": u"円"} for f in facts]
        script = {"10": [0.03] * 4, "20": [0.10]}      # 10億円: 4 回とも同じ値 / 20億円: +10% = 22 が決まる
        sites, counts = M.t8_candidates(text, refs, claims, by_id, "s", "d", 40, rng_for_r=lambda tok: FakeRng(script[tok.text]))
        self.assertEqual(counts["円族の token"], 2)
        self.assertEqual(counts["r が決まらず site にしない"], 1)
        self.assertEqual(counts["作れる site"], 1)
        self.assertEqual(len(sites), 1)
        inj, t, bc = sites[0]
        self.assertEqual((inj["type"], inj["replacement"], inj["detail"]["relative"]), ("T8_REL", "22", 0.10))
        self.assertEqual(text[inj["span"][0]:inj["span"][1]], "20")

    def test_55_only_yen_family_tokens_are_sites(self):
        facts = [fact("jppfs_cor:A", "C", 1e9), fact("jppfs_cor:B", "C", 500.0, "pure")]
        text = u"・一は10億円だった。\n・従業員は500人だった。\n・比率は500回だった。"
        be = M.StubBackend()
        zb = json.dumps({"facts": facts}).encode("utf-8")
        claims = dict((p, be.verify(zb, p, text)["claims"]) for p in ("P22", "P26"))
        by_id = dict((p, dict((c["id"], c) for c in claims[p])) for p in claims)
        sites, counts = M.t8_candidates(text, [], claims, by_id, "s", "d", 40)
        self.assertEqual(counts["円族の token"], 1)
        self.assertEqual([text[i["span"][0]:i["span"][1]] for i, _t, _b in sites], ["10"])

    def test_56_base_must_be_grounded_in_both_profiles(self):
        # P22 だけ GROUNDED の行は土台にしない(片方だけ GROUNDED の数は別に数える)
        def claim(i, state, value=1e9):
            return {"id": i, "value": value, "span": u"一は10億円", "unit": u"円", "state": state}
        text = u"一は10億円だった。"
        tok = token(text)
        for s22, s26, want in (("GROUNDED", "GROUNDED", "両方 GROUNDED"), ("GROUNDED", "POINTER_NOT_FOUND", "P22 のみ GROUNDED"),
                               ("VALUE_MISMATCH", "GROUNDED", "P26 のみ GROUNDED"), ("VALUE_MISMATCH", "POINTER_NOT_FOUND", "どちらも GROUNDED でない")):
            base = {"P22": [claim("N001", s22)], "P26": [claim("N001", s26)]}
            by = dict((p, dict((c["id"], c) for c in base[p])) for p in base)
            status, bc = M.base_status(base, by, tok, text)
            self.assertEqual(status, want)
            self.assertEqual(bc is not None, want == "両方 GROUNDED")
        base = {"P22": [claim("N001", "GROUNDED")], "P26": []}
        self.assertEqual(M.base_status(base, {"P22": {"N001": base["P22"][0]}, "P26": {}}, tok, text)[0], "profile 間で claim が合わない")
        base = {"P22": [claim("N001", "GROUNDED", value=7.0)], "P26": [claim("N001", "GROUNDED", value=7.0)]}
        by = dict((p, dict((c["id"], c) for c in base[p])) for p in base)
        self.assertEqual(M.base_status(base, by, tok, text)[0], "基準に対応が付かない")

    def test_57_claim_matching_scales_money_to_yen_like_the_precedent(self):
        # 円族の token(10億円)の claim は円に直した値(1e9)で持たれる。前例の _find_base_claim は同じ単位の値で比べたが、ここは円に直して比べる
        claims = [{"id": "N001", "value": 1e9, "span": u"一は10億円だった", "unit": u"円", "state": "GROUNDED"},
                  {"id": "N002", "value": 10.0, "span": u"二は10回", "unit": u"回", "state": "GROUNDED"}]
        self.assertEqual(M.find_base_claim(claims, 10.0, u"10", u"億円")["id"], "N001")
        self.assertEqual(M.find_base_claim(claims, 10.0, u"10", u"回")["id"], "N002")
        self.assertIsNone(M.find_base_claim(claims, 10.0, u"10", u"千円"))
        inj = {"new_value": 11.0, "replacement": u"11"}
        cl = [{"value": 1.1e9, "span": u"一は11億円", "unit": u"円"}]
        self.assertEqual(M.claim_for_p27(cl, inj, u"億円"), cl[0])
        self.assertIsNone(M.claim_for_p27(cl + [dict(cl[0])], inj, u"億円"))            # 2 件は対応が付かない
        self.assertIsNone(M.claim_for_p27([], inj, u"億円"))
        # 字の手がかりで 2 件を 1 件にしぼる / 手がかりが無ければ値だけ
        two = [dict(cl[0]), {"value": 1.1e9, "span": u"二は別の窓", "unit": u"円"}]
        self.assertEqual(M.claim_for_p27(two, inj, u"億円"), two[0])
        self.assertEqual(M.claim_for_p27([{"value": 1.1e9, "span": u"窓", "unit": u"円"}], inj, u"億円")["span"], u"窓")


class TestInject(Base):
    def setUp(self):
        Base.setUp(self)
        self.big = World(self.tmp + "_big", texts=dict((d, BIG_TEXT) for d in TUNE + EVAL), facts=dict((d, BIG_FACTS) for d in TUNE + EVAL)) \
            if not os.path.exists(self.tmp + "_big") else None
        self.addCleanup(shutil.rmtree, self.tmp + "_big", True)

    def test_60_cap_is_40_per_type_per_doc(self):
        rec = self.big.inject(docs=[TUNE[0]])
        rows = rec["行"]
        self.assertEqual(sum(1 for r in rows if r["型"] == "T1_VALUE"), 40)
        self.assertEqual(sum(1 for r in rows if r["型"] == "T8_REL"), 40)
        c = rec["書類別の数え"][TUNE[0]]
        self.assertGreaterEqual(c["T8_REL"]["作れる site"], 41)             # 作れる site は 40 より多く、採るのは 40
        self.assertEqual(c["T8_REL"]["採った"], 40)
        self.assertEqual(c["T1_VALUE"]["採った"], 40)
        self.assertGreater(c["T1_VALUE"]["作れる site"], 40)
        self.assertEqual(rec["T8_REL の site"]["注入の行"], 40)
        small = self.big.inject(docs=[TUNE[0]], cap=7, out=os.path.join(self.tmp, "o", "cap7.json"))
        self.assertEqual(sum(1 for r in small["行"] if r["型"] == "T8_REL"), 7)
        self.assertEqual(sum(1 for r in small["行"] if r["型"] == "T1_VALUE"), 7)

    def test_61_round_trip_failure_stops(self):
        self.big.inject(docs=[TUNE[0]], cap=2)                       # 通る
        with mock.patch.object(M.IJ, "revert", lambda tampered, chosen, placements, original: original + u"。"):
            with self.assertRaises(M.Stop) as cm:
                self.big.inject(docs=[TUNE[0]], cap=2, out=os.path.join(self.tmp, "o", "rt.json"))
        self.assertIn("round-trip", str(cm.exception))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "o", "rt.json")))

    def test_62_each_injection_changes_one_number_and_reverts(self):
        text = BIG_TEXT
        be = M.StubBackend()
        zb = json.dumps({"facts": BIG_FACTS}).encode("utf-8")
        claims = dict((p, be.verify(zb, p, text)["claims"]) for p in ("P22", "P26"))
        by_id = dict((p, dict((c["id"], c) for c in claims[p])) for p in claims)
        refs = be.refs(os.path.join(self.big.zip_dir, TUNE[0] + ".zip"), TUNE[0], None)
        sites, _c = M.t8_candidates(text, refs, claims, by_id, "s", "d", 40)
        self.assertEqual(len(sites), 40)
        ids = set()
        for inj, tok, bc in sites:
            tam, pl = M.IJ.apply_edits(text, [inj])
            self.assertNotEqual(tam, text)
            self.assertEqual(M.IJ.revert(tam, [inj], pl, text), text)
            self.assertEqual(len(tam) - len(text), len(inj["replacement"]) - (inj["span"][1] - inj["span"][0]))
            ids.add(inj["id"])
        self.assertEqual(len(ids), 40)
        # cap で採る 40 件は、token を Random("<seed>|<docID>|T8_REL") で並べ替えた先頭(本文の順の先頭 40 件ではない)
        order = [t for t in M.N.scan(text) if t.unit in M.MONEY_FAMILY and M.N.is_quantity(text, t)]
        random.Random("s|d|T8_REL").shuffle(order)
        self.assertEqual([tuple(i["span"]) for i, _t, _b in sites], [(t.start, t.end) for t in order[:40]])
        self.assertNotEqual([tuple(i["span"]) for i, _t, _b in sites], sorted(tuple(i["span"]) for i, _t, _b in sites))
        # 同じ種・同じ書類なら同じ site と r(再現する)
        again, _ = M.t8_candidates(text, refs, claims, by_id, "s", "d", 40)
        self.assertEqual([(i["id"], i["replacement"], i["span"]) for i, _t, _b in sites], [(i["id"], i["replacement"], i["span"]) for i, _t, _b in again])

    def test_62b_t1_is_inject_select_as_it_is_and_the_seed_decides_the_sites(self):
        be = M.StubBackend()
        refs = be.refs(os.path.join(self.big.zip_dir, TUNE[0] + ".zip"), TUNE[0], None)
        want, _cat, _a, _w = M.IJ.select(BIG_TEXT, refs, "xbrl", "test-seed", TUNE[0], 40, types=["T1_VALUE"])
        rec = self.big.inject(docs=[TUNE[0]])
        full = json.load(io.open(os.path.join(self.big.outside, "inject_full.json"), encoding="utf-8"))["seed 以外の注入の字"]
        got = [x for x in full if "-T1-" in x["id"]]
        self.assertEqual([x["id"] for x in got], [w["id"] for w in want])
        self.assertEqual([x["後の字"] for x in got], [w["replacement"] for w in want])
        self.assertEqual([x["新しい値"] for x in got], [w["new_value"] for w in want])
        # 別の種なら T1 も T8 も別の site になる
        other = self.big.inject(docs=[TUNE[0]], out=os.path.join(self.tmp, "o", "seed2.json"), outside_dir=os.path.join(self.tmp, "outside_s2"),
                                seed_fn=lambda path: ("other-seed", {}))
        full2 = json.load(io.open(os.path.join(self.tmp, "outside_s2", "inject_full.json"), encoding="utf-8"))["seed 以外の注入の字"]
        self.assertNotEqual([x["id"] + x["後の字"] for x in full if "-T1-" in x["id"]], [x["id"] + x["後の字"] for x in full2 if "-T1-" in x["id"]])
        self.assertNotEqual([x["id"] + x["後の字"] for x in full if "-T8-" in x["id"]], [x["id"] + x["後の字"] for x in full2 if "-T8-" in x["id"]])
        self.assertEqual(other["種"]["sealed_in_commit"], None)

    def test_63_named_the_original_value_rule(self):
        base = {"state": "GROUNDED", "pointers": ["xbrl:a:X@C", "xbrl:a:Y@C"], "recomputed": 5.0}
        vm = {"state": "VALUE_MISMATCH", "pointers": ["xbrl:a:X@C"], "recomputed": 5.0}
        self.assertTrue(M.named_original(vm, base))
        self.assertTrue(M.named_original(dict(vm, pointers=["xbrl:a:X@C", "zzz"]), base))                 # 先頭だけを見る
        self.assertFalse(M.named_original(dict(vm, pointers=["xbrl:a:Y@C"]), base))                       # 先頭が違う(別の fact)
        self.assertFalse(M.named_original(dict(vm, pointers=["xbrl:a:X@D"]), base))                       # 同じ要素の別の context
        self.assertFalse(M.named_original(dict(vm, recomputed=5.5), base))                                # 先頭は同じで値が違う
        self.assertFalse(M.named_original(dict(vm, recomputed=None), base))
        self.assertFalse(M.named_original(dict(vm, pointers=[]), dict(base, pointers=[])))               # 名指しが空どうしは名指しでない
        self.assertFalse(M.named_original(dict(vm, pointers=[]), base))
        for s in ("GROUNDED", "POINTER_NOT_FOUND", "UNVERIFIABLE"):
            self.assertFalse(M.named_original(dict(vm, state=s), base))                                   # VALUE_MISMATCH でなければ違う

    def test_64_classify_labels(self):
        base = {"state": "GROUNDED", "pointers": ["xbrl:a:X@C"], "recomputed": 5.0}

        def cl(state, **kw):
            return M.classify(dict({"state": state, "pointers": ["xbrl:a:X@C"], "recomputed": 5.0, "reason": None}, **kw), base)
        self.assertEqual(cl("GROUNDED")["結果"], M.LABEL_PASS)
        self.assertEqual(cl("VALUE_MISMATCH")["結果"], M.LABEL_NAMED_ORIGINAL)
        self.assertEqual(cl("VALUE_MISMATCH", recomputed=6.0)["結果"], M.LABEL_NAMED_OTHER)
        self.assertEqual(cl("POINTER_NOT_FOUND", reason="no_same_value")["結果"], M.LABEL_PNF)
        self.assertEqual(cl("POINTER_NOT_FOUND", reason="no_same_value")["reason"], "no_same_value")
        self.assertEqual(cl("UNVERIFIABLE", reason="no_subject")["結果"], M.LABEL_UNV)
        self.assertEqual(M.classify(None, base), {"対応": False, "結果": M.LABEL_UNMAPPED, "state": None, "reason": None})
        with self.assertRaises(M.Stop):
            cl("SOMETHING")
        with self.assertRaises(M.Stop):
            cl("POINTER_NOT_FOUND", reason=u"売上高が5,000と違う")

    def test_65_tally_by_type_profile_style_with_the_mapped_rows_as_the_denominator(self):
        def row(t, style, p22, p26):
            return {"型": t, "文体": style, "P22": p22, "P26": p26}

        def res(label, state=None, reason=None):
            return {"対応": label != M.LABEL_UNMAPPED, "結果": label, "state": state, "reason": reason}
        un = res(M.LABEL_UNMAPPED)
        rows = [row("T8_REL", "A", res(M.LABEL_NAMED_ORIGINAL, "VALUE_MISMATCH"), res(M.LABEL_PNF, "POINTER_NOT_FOUND", "no_same_value")),
                row("T8_REL", "A", res(M.LABEL_NAMED_ORIGINAL, "VALUE_MISMATCH"), res(M.LABEL_PASS, "GROUNDED")),
                row("T8_REL", "B", res(M.LABEL_NAMED_OTHER, "VALUE_MISMATCH"), res(M.LABEL_UNV, "UNVERIFIABLE", "no_subject")),
                row("T8_REL", "B", un, un),
                row("T1_VALUE", "C", res(M.LABEL_NAMED_ORIGINAL, "VALUE_MISMATCH"), res(M.LABEL_NAMED_ORIGINAL, "VALUE_MISMATCH"))]
        s = M.inject_summary(rows)
        a = s["T8_REL"]["P22"]["全体"]
        self.assertEqual((a["注入の行"], a["対応が付く"], a["対応が付かない"]), (4, 3, 1))
        self.assertEqual(a[M.LABEL_NAMED_ORIGINAL], {"件": 2, "分母": 3, "率": 66.7})
        self.assertEqual(a[M.LABEL_NAMED_OTHER], {"件": 1, "分母": 3, "率": 33.3})
        b = s["T8_REL"]["P26"]["全体"]
        self.assertEqual(b[M.LABEL_PASS], {"件": 1, "分母": 3, "率": 33.3})
        self.assertEqual(b["POINTER_NOT_FOUND の reason の内訳"], {"no_same_value": 1})
        self.assertEqual(b["UNVERIFIABLE の reason の内訳"], {"no_subject": 1})
        self.assertEqual(s["T8_REL"]["P22"]["A"][M.LABEL_NAMED_ORIGINAL], {"件": 2, "分母": 2, "率": 100.0})        # 文体の型ごと
        self.assertEqual(s["T8_REL"]["P22"]["B"]["対応が付く"], 1)
        self.assertEqual(s["T8_REL"]["P22"]["C"]["注入の行"], 0)
        self.assertEqual(s["T1_VALUE"]["P26"]["C"][M.LABEL_NAMED_ORIGINAL], {"件": 1, "分母": 1, "率": 100.0})
        self.assertEqual(s["T8_REL"]["両方の profile で対応が付く"], 3)

    def test_66_record_has_no_chars_of_the_injected_numbers_and_the_outside_file_has_them(self):
        rec = self.w.inject()
        txt = self.w.record_text()
        full_path = os.path.join(self.w.outside, "inject_full.json")
        full = json.load(io.open(full_path, encoding="utf-8"))["seed 以外の注入の字"]
        self.assertTrue(full)
        self.assertEqual(rec["repo の外に置いたもの"]["注入の字・新しい値"]["sha256"], sha(open(full_path, "rb").read()))
        self.assertEqual(sorted(set(k for k in M.walk_keys(rec) if k in M.FORBIDDEN_RECORD_KEYS)), [])
        for k in ('"元の字"', '"後の字"', '"新しい値"', '"replacement"', '"new_value"'):
            self.assertNotIn(k, txt)
        self.assertNotIn(SENTINEL_COMPANY, txt)
        for row in rec["行"]:
            self.assertEqual(sorted(k for k in row if k not in ("r", "r を決めた回")), sorted(["P22", "P26", "docID", "id", "基準の claim", "型", "文体"]))
            self.assertEqual(sorted(row["P22"]), ["reason", "state", "対応", "結果"])
        self.assertEqual(rec["種"], {"file": "measure/SEED.json", "sealed_in_commit": "x", "seed_file_sha256": "y"})
        self.assertEqual(rec["集計"]["T8_REL"]["P22"]["全体"]["注入の行"], rec["T8_REL の site"]["注入の行"])

    def test_67_stub_world_outcomes_p22_names_the_original_p26_stops(self):
        rec = self.w.inject()
        t8 = [r for r in rec["行"] if r["型"] == "T8_REL"]
        self.assertTrue(t8)
        for r in t8:
            self.assertIn(r["r"], M.T8_R_VALUES)
            self.assertEqual(r["P22"]["結果"], M.LABEL_NAMED_ORIGINAL)
            self.assertEqual(r["P26"]["結果"], M.LABEL_PNF)
            self.assertEqual(r["P26"]["reason"], "no_same_value")
        # 999 億円(合う fact が無い)は土台が GROUNDED でないので、どの型でも注入の行にならない
        self.assertEqual(rec["書類別の数え"][TUNE[0]]["T8_REL"]["どちらも GROUNDED でない"], 1)
        self.assertEqual(rec["書類別の数え"][TUNE[0]]["T8_REL"]["円族の token"], 5)
        self.assertEqual(rec["書類別の数え"][TUNE[0]]["T8_REL"]["採った"], 4)
        by_style = rec["集計"]["T8_REL"]["P22"]
        self.assertEqual(by_style["A"]["注入の行"] + by_style["B"]["注入の行"] + by_style["C"]["注入の行"], by_style["全体"]["注入の行"])

    def test_68_seed_is_checked_by_inject_verify_seed_sealed(self):
        called = []

        def fake(path):
            called.append(path)
            raise M.IJ.SealError("not sealed")
        with mock.patch.object(M.IJ, "verify_seed_sealed", fake):
            with self.assertRaises(M.IJ.SealError):
                M.run_inject(**self.w.common(work_root=os.path.join(self.tmp, "w")))
        self.assertEqual([os.path.basename(p) for p in called], ["SEED.json"])
        self.assertEqual(os.path.dirname(called[0]), os.path.dirname(SCRIPT))
        self.assertFalse(os.path.exists(self.w.out))

    def test_69_multi_process_matches_single_process(self):
        a = self.w.inject(docs=TUNE[:2])
        b = self.w.inject(docs=TUNE[:2], procs=2, out=os.path.join(self.tmp, "o", "p2.json"), outside_dir=os.path.join(self.tmp, "outside_p2"))
        self.assertEqual(a["行"], b["行"])
        self.assertEqual(a["書類別の数え"], b["書類別の数え"])


class TestCli(Base):
    def test_70_dry_run_cli_runs_the_whole_path(self):
        base = ["--root", self.w.root, "--git-dir", ROOT, "--zip-dir", self.w.zip_dir, "--cache-root", self.w.cache_root,
                "--existing-cache-dir", self.w.existing, "--outside-dir", self.w.outside, "--dry-run"]
        with contextlib.redirect_stdout(io.StringIO()):
            M.main(["judge", "--out", self.w.out] + base)
            rec = self.w.record()
            self.assertTrue(rec["dry_run"])
            self.assertEqual(rec["backend"], "stub")
            seed_patch = mock.patch.object(M.IJ, "verify_seed_sealed", lambda path: ("test-seed", {"sealed_in_commit": "x", "seed_file_sha256": "y"}))
            with seed_patch:
                M.main(["inject", "--out", os.path.join(self.tmp, "o", "inj.json"), "--work-dir", os.path.join(self.tmp, "wk")] + base)
        self.assertTrue(json.load(io.open(os.path.join(self.tmp, "o", "inj.json"), encoding="utf-8"))["行"])

    def test_71_dry_run_without_explicit_folders_stops_instead_of_touching_the_home(self):
        with self.assertRaises(M.Stop):
            M.main(["judge", "--root", self.w.root, "--dry-run", "--out", self.w.out])
        self.assertFalse(os.path.exists(self.w.out))

    def test_72_eval_doc_on_the_command_line_stops(self):
        with open_spy() as opened:
            with self.assertRaises(M.Stop):
                M.main(["judge", "--root", self.w.root, "--git-dir", ROOT, "--zip-dir", self.w.zip_dir, "--cache-root", self.w.cache_root,
                        "--existing-cache-dir", self.w.existing, "--outside-dir", self.w.outside, "--dry-run", "--out", self.w.out,
                        "--docs", EVAL[0]])
        self.assertEqual([p for p in opened if EVAL[0] in p or os.sep + "reports" + os.sep in p], [])


if __name__ == "__main__":
    unittest.main()
