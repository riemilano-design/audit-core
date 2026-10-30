"""最終評価用 8 書類の封(docs/FINAL_EVAL_8_SEAL_2026-10-14.md)を見張る。

開封の記録 fixtures/xbrl/final8/opened_*.json が無い間は、8 書類の ZIP が
キャッシュに 1 件も無いことを赤くなる門にする(記憶や手の確認ではなく試験で)。
開封の記録が在る場合は、その記録が同じ 8 件を挙げていることを見る。
"""
import glob
import json
import os
import tempfile
import unittest

from adapters.xbrl import edinet

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # tests/adapters/xbrl → audit-core
SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")
SEAL = os.path.join(ROOT, "docs", "FINAL_EVAL_8_SEAL_2026-10-14.md")
OPENED_GLOB = os.path.join(ROOT, "fixtures", "xbrl", "final8", "opened_*.json")


def sealed_doc_ids():
    with open(SPLIT, encoding="utf-8") as f:
        return list(json.load(f)["final_eval_sealed"])


def cached_before_opening(doc_ids, cache_dir, opened):
    """開封前なのにキャッシュに在る docID の一覧(空なら封は生きている)。

    opened が真なら開封済みなので何も返さない。cache_dir は本番の
    edinet.CACHE_DIR と同じ並び(<docID>.zip)を仮定する。
    """
    if opened:
        return []
    return [d for d in doc_ids if os.path.exists(os.path.join(cache_dir, d + ".zip"))]


class SealIsAliveTest(unittest.TestCase):
    def test_the_split_names_eight_documents(self):
        ids = sealed_doc_ids()
        self.assertEqual(8, len(ids))
        self.assertEqual(8, len(set(ids)))

    def test_the_seal_document_lists_every_sealed_id(self):
        with open(SEAL, encoding="utf-8") as f:
            text = f.read()
        for doc in sealed_doc_ids():
            self.assertIn("`%s`" % doc, text, doc)

    def test_no_sealed_zip_is_cached_until_the_opening_is_recorded(self):
        opened = sorted(glob.glob(OPENED_GLOB))
        ids = sealed_doc_ids()
        bad = cached_before_opening(ids, edinet.CACHE_DIR, bool(opened))
        self.assertEqual([], bad,
                         "封の 8 書類がキャッシュに在る(開封の記録が無いのに): %s" % bad)
        if opened:
            self.assertEqual(1, len(opened), opened)
            with open(opened[0], encoding="utf-8") as f:
                rec = json.load(f)
            self.assertEqual(sorted(ids), sorted(rec["docs"]))


class GateSelfCheckTest(unittest.TestCase):
    """門そのものが退化していないか(偽物のキャッシュで赤くなるか)。本物の
    キャッシュには触らない。"""

    def test_a_cached_zip_is_reported_before_opening(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "S100XXXX.zip"), "wb").close()
            self.assertEqual(["S100XXXX"],
                             cached_before_opening(["S100XXXX", "S100YYYY"], d, opened=False))

    def test_nothing_is_reported_after_opening(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "S100XXXX.zip"), "wb").close()
            self.assertEqual([], cached_before_opening(["S100XXXX"], d, opened=True))

    def test_the_cache_layout_assumed_here_is_the_production_one(self):
        # 本番の cache_path が <CACHE_DIR>/<docID>.zip でなくなったら、この門は
        # 存在しない道を見て緑のまま黙る。その退化をここで赤にする。
        self.assertEqual(os.path.join(edinet.CACHE_DIR, "S100XXXX.zip"),
                         edinet.cache_path("S100XXXX"))
