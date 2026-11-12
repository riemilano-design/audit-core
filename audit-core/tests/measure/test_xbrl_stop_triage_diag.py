# -*- coding: utf-8 -*-
u"""止まった数字の「見る順」の診断(docs/XBRL_STOP_TRIAGE_DIAG_2026-11-12.md)を記録に縛る門。

  a  記録は入力の記録から数え直した字と byte で同じ(入口 measure/xbrl_stop_triage_2026-11-12.py を import して数える。engine は呼ばない)
  b  文書の表の塊は記録から機械で作った字と byte で同じ / 塊と囲みの外の地の文に 2 桁以上の数が無い(日付と ` ` の中は除く)
  c  予測の囲みの字の sha256 が、数える前に出した値と同じ
  d  別の記録(fx_tally_2026-11-09.json)の数と合う(自分の数え方の欠陥を疑う側の照合)
  e  組の決め方の当たる例・当たらない例 / 節の表は報告(adapters/xbrl/report_customer.py)と同じ / 報告は engine の証拠の欄を読んでいない(文書 §4 の 2)/
     予測の 3 条件の境目 / 行を読む profile と「=」の解き方(作り物の記録で)
  f  記録と文書に書類の番号・会社の名の欄が無い
"""
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

SCRIPT_REL = "measure/xbrl_stop_triage_2026-11-12.py"
REC_REL = "fixtures/xbrl/aiforms/stop_triage_2026-11-12.json"
DOC_REL = "docs/XBRL_STOP_TRIAGE_DIAG_2026-11-12.md"
TALLY_REL = "fixtures/xbrl/aiforms/fx_tally_2026-11-09.json"
PREDICTION_SHA256 = "f22b997d68cf3598a7f91f6510ccc63992de01f5514cb5a5cf46ff74ce13300f"
BEGIN, END = u"<!-- ST:BEGIN -->\n", u"<!-- ST:END -->\n"


def load_module(rel, name):
    u"""importlib で読み込む。読み込みの前に居た ``sys.modules`` の名前は、読み込みの後に元の object へ戻す。"""
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for k, v in before.items():
            if k != name and sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


ST = load_module(SCRIPT_REL, "xbrl_stop_triage_2026_11_12_for_gate")


def _read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


class StopTriageDiagTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec_text = _read(REC_REL)
        cls.rec = json.loads(cls.rec_text)
        cls.doc = _read(DOC_REL)
        cls.built = ST.build()

    # --- a
    def test_a1_record_is_what_the_script_counts_from_the_inputs(self):
        self.assertEqual(ST.dumps(self.built), self.rec_text)

    def test_a2_inputs_are_pinned_by_sha256(self):
        self.assertEqual(len(self.rec[u"入力"]), 6)
        for name, sha in self.rec[u"入力"].items():
            with io.open(os.path.join(ROOT, "fixtures", "xbrl", "aiforms", name), "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), sha, name)

    def test_a3_every_labelled_row_falls_in_exactly_one_tier(self):
        for sid, d in self.rec[u"組"].items():
            for where, s in [(u"全体", d[u"全体"])] + list(d[u"形ごと"].items()) + list(d[u"書き手ごと"].items()):
                self.assertEqual(sum(sum(v.values()) for v in s[u"組"].values()), s[u"札のある行"], (sid, where))
                self.assertEqual(sum(v[u"偽"] for v in s[u"組"].values()), s[u"偽"], (sid, where))
                self.assertEqual(list(s[u"組"].keys()), list(ST.TIERS))
            self.assertEqual(sum(s[u"札のある行"] for s in d[u"形ごと"].values()), d[u"全体"][u"札のある行"], sid)
            self.assertEqual(sum(s[u"札のある行"] for s in d[u"書き手ごと"].values()), d[u"全体"][u"札のある行"], sid)
            self.assertEqual(sum(sum(v.values()) for v in d[u"報告の節ごと"].values()), d[u"全体"][u"札のある行"], sid)

    # --- b
    def _block(self):
        self.assertEqual(self.doc.count(BEGIN), 1)
        self.assertEqual(self.doc.count(END), 1)
        return self.doc.split(BEGIN, 1)[1].split(END, 1)[0]

    def test_b1_doc_block_is_rendered_from_the_record(self):
        self.assertEqual(self._block(), ST.render(self.rec))

    def test_b2_prose_outside_the_block_holds_no_number_of_two_or_more_digits(self):
        prose = self.doc.replace(self._block(), u"")
        prose = re.sub(u"```.*?```", u"", prose, flags=re.S)
        prose = re.sub(u"`[^`]*`", u"", prose)
        prose = re.sub(u"2026-\\d\\d-\\d\\d", u"", prose)
        prose = prose.replace(u"sha256", u"")
        self.assertEqual(re.findall(u"[0-9０-９][0-9０-９,.]*[0-9０-９]", prose), [])
        self.assertEqual(re.findall(u"[一二三四五六七八九十百千]{2,}", prose), [])

    # --- c
    def test_c1_prediction_fence_is_the_text_written_before_counting(self):
        fences = re.findall(u"```\n(.*?)```\n", self.doc, flags=re.S)
        self.assertEqual(len(fences), 1)
        self.assertEqual(hashlib.sha256(fences[0].encode("utf-8")).hexdigest(), PREDICTION_SHA256)
        self.assertIn(PREDICTION_SHA256, self.doc)

    def test_c2_prediction_results_are_judged_from_the_record(self):
        P = self.rec[u"予測の当たり"]
        self.assertEqual(list(P.keys()), ["P1", "P2", "P3", "P4", "P5", "P6", "P7"])
        fx = self.rec[u"組"]["FX"]
        for f, s in fx[u"形ごと"].items():
            red = s[u"組"][u"赤"]
            rk, rf = sum(red.values()), red[u"偽"]
            self.assertEqual(P["P1"][f], rf * s[u"札のある行"] >= 3 * s[u"偽"] * rk, f)
            self.assertEqual(P["P2"][f], rf * 100 >= 70 * s[u"偽"], f)
        self.assertEqual(list(P["P1"].keys()), ["F6", "F7", "F8", "F9"])
        self.assertEqual(list(P["P4"].keys()), ["W1", "W2"])
        for c in self.rec[u"FX の会社ごと"]:
            self.assertEqual(str(c[u"番号"]) in P["P7"], c[u"偽"] >= 5, c)

    # --- d
    def test_d1_fx_counts_agree_with_the_earlier_tally_record(self):
        t = json.loads(_read(TALLY_REL))[u"集計"]
        lab = t[u"2 札"][u"札の分布"][u"全体"]
        eng = t[u"3 engine の判定(無改変)"]["P33E"][u"全体"]
        fx = self.rec[u"組"]["FX"]
        s = fx[u"全体"]
        self.assertEqual(s[u"札のある行"], lab[u"数の claim"])
        self.assertEqual(s[u"札の無い行"], 0)
        self.assertEqual(s[u"偽"], lab[u"偽"][u"件"])
        self.assertEqual(sum(v[u"真"] for v in s[u"組"].values()), lab[u"真"][u"件"])
        self.assertEqual(sum(s[u"組"][u"緑"].values()), eng["4 state"]["GROUNDED"])
        self.assertEqual(s[u"組"][u"緑"][u"偽"], eng[u"札 偽の行で通した数"])
        self.assertEqual(s[u"組"][u"緑"][u"真"], eng[u"札 真の行の GROUNDED 率"][u"件"])
        sec = fx[u"報告の節ごと"]
        self.assertEqual(sum(sec[u"違う"].values()), eng["4 state"]["VALUE_MISMATCH"])
        self.assertEqual(sec[u"違う"][u"真"], eng[u"札 真で止めた行の reason/state の内訳"]["(reason なし)/VALUE_MISMATCH"])
        self.assertEqual(sum(s[u"組"][u"赤"].values()) + sum(s[u"組"][u"黄"].values()) + sum(s[u"組"][u"灰"].values()),
                         eng["4 state"]["VALUE_MISMATCH"] + eng["4 state"]["UNVERIFIABLE"] + eng["4 state"]["POINTER_NOT_FOUND"])
        # 黄は「違う」の節の一部
        self.assertLess(sum(s[u"組"][u"黄"].values()), sum(sec[u"違う"].values()))
        self.assertGreater(sum(s[u"組"][u"黄"].values()), 0)
        why = fx[u"要確認の理由ごと"]
        inner = eng[u"札 真で止めた行の reason/state の内訳"]
        for k, v in why.items():
            st, rs = k.split(" / ", 1)
            self.assertEqual(v[u"真"], inner[rs + "/" + st], k)

    # --- e
    def test_e1_tier_rule_examples(self):
        T = ST.tier_of
        self.assertEqual(T("GROUNDED", "", None), u"緑")
        self.assertEqual(T("VALUE_MISMATCH", "", None), u"赤")
        self.assertEqual(T("VALUE_MISMATCH", "", "relative_within_rho"), u"赤")
        self.assertEqual(T("VALUE_MISMATCH", "", "scale_10^1"), u"赤")
        self.assertEqual(T("VALUE_MISMATCH", "", "same_element:Prior1YearDuration"), u"黄")
        self.assertEqual(T("VALUE_MISMATCH", "", "same_element:Prior1YearInstant_NonConsolidatedMember"), u"黄")
        self.assertEqual(T("VALUE_MISMATCH", "", "same_element:CurrentYearDuration"), u"赤")
        self.assertEqual(T("POINTER_NOT_FOUND", "no_element", None), u"赤")
        self.assertEqual(T("POINTER_NOT_FOUND", "no_same_value", None), u"赤")
        self.assertEqual(T("POINTER_NOT_FOUND", "no_element(ratio without fact)", None), u"灰")
        self.assertEqual(T("POINTER_NOT_FOUND", "no_element(unit not in XBRL)", None), u"灰")
        self.assertEqual(T("POINTER_NOT_FOUND", "other_concept", "same_element:Prior1YearDuration"), u"灰")
        self.assertEqual(T("UNVERIFIABLE", "no_element", None), u"灰")
        self.assertEqual(T("UNVERIFIABLE", "no_subject", None), u"灰")

    def test_e2_section_table_is_the_customer_report_s(self):
        from adapters.xbrl import report_customer as RC
        self.assertEqual(tuple(ST.OUT_OF_SCOPE_REASONS), tuple(RC.OUT_OF_SCOPE_REASONS))
        self.assertEqual(tuple(ST.NOT_JUDGED_REASONS), tuple(RC.NOT_JUDGED_REASONS))
        self.assertEqual(ST.SECTIONS, (RC.SECTION_MISMATCH, RC.SECTION_CHECK, RC.SECTION_OUT, RC.SECTION_NOT_JUDGED, RC.SECTION_MATCH))
        seen = set()
        for sid, cn, ln, prof in ST.SETS:
            for r in ST.rows_of(cn, ln, prof):
                seen.add((r[6], r[7]))
        self.assertGreater(len(seen), 10)
        for state, reason in sorted(seen):
            self.assertEqual(ST.section_of(state, reason), RC.section_of({"state": state, "reason": reason}), (state, reason))

    def test_e3_customer_report_does_not_read_the_evidence_field(self):
        self.assertNotIn("last_branch_evidence", _read("adapters/xbrl/report_customer.py"))
        self.assertIn(u"は `last_branch_evidence` を読まない", self.doc)

    def test_e4_script_reads_records_only(self):
        src = _read(SCRIPT_REL)
        for word in ("import adapters", "from adapters", "import core", "from core", "recipes", "subprocess", "urllib", "anthropic", "API_KEY"):
            self.assertNotIn(word, src, word)

    def test_e5_three_conditions_at_the_boundaries(self):
        def s(n, f, red, grey):
            z = lambda k, x: {u"真": k - x, u"偽": x, u"判定不能": 0}
            rest = n - red[0] - grey[0]
            return {u"札のある行": n, u"偽": f, u"組": {u"赤": z(*red), u"黄": z(0, 0), u"灰": z(*grey), u"緑": z(rest, f - red[1] - grey[1])}}
        names = (u"赤の偽率が全体の 3 倍以上", u"赤が偽の 70% 以上", u"灰の偽率が全体以下")
        got = lambda *a: tuple(ST.three(s(*a))[k] for k in names)
        # 全体の偽率 10%(1000 行・偽 100)。赤 200 行に偽 70 = 35%(3.5 倍)・取り分 70%。灰 100 行に偽 10 = 10%
        self.assertEqual(got(1000, 100, (200, 70), (100, 10)), (True, True, True))
        self.assertEqual(got(1000, 100, (200, 69), (100, 10)), (True, False, True))
        self.assertEqual(got(1000, 100, (200, 70), (100, 11)), (True, True, False))
        # 赤 200 行に偽 60 = 30%(ちょうど 3 倍)は当たり、59 は外れ
        self.assertEqual(got(1000, 100, (200, 60), (100, 10)), (True, False, True))
        self.assertEqual(got(1000, 100, (200, 59), (100, 10)), (False, False, True))
        self.assertEqual(list(ST.three(s(1000, 100, (200, 70), (100, 10))).keys()), list(names))

    def test_e6_rows_are_read_at_the_named_profile(self):
        self.assertEqual(ST.SETS, (
            ("FX", "fx_claims_2026-11-09.json", "fx_labels_2026-11-09.json", "P33E"),
            ("F14", "claims_2026-11-03.json", "labels_2026-11-03.json", "P28E"),
            ("F5", "f5_claims_2026-11-03.json", "f5_labels_2026-11-03.json", "P28E")))
        G = ["GROUNDED", None, [], None, None, None, None]
        V = ["VALUE_MISMATCH", None, [], None, None, None, "same_element:Prior1YearDuration"]
        N = ["POINTER_NOT_FOUND", "no_same_value", [], None, None, None, None]
        claims = {u"欄": {"claim": ["id", "kind"]}, "profile": ["A", "B", "C"], u"本": [{
            "name": "x", "docID": "d", "form": "F0", "writer": "W0", u"行": [
                ["r1", "k", G, V, N],        # A 緑 → B 黄 → C 赤
                ["r2", "k", G, "=", "="],    # ずっと緑
                ["r3", "k", G, V, "="],      # C は B と同じ = 黄
                ["r4", "k", G, None, None],  # B・C に claim が無い
                ["r5", "k", None, None, N],  # C だけ
                ["r6", "k", G, None, "="],   # C は B と同じ = 無い
            ]}]}
        labels = {u"本": [{"name": "x", u"札": [["r1", u"偽"], ["r2", u"真"], ["r3", u"真"], ["r4", u"真"], ["r6", u"真"]]}]}
        real = ST._load
        ST._load = lambda name: claims if name == "c" else labels
        try:
            at = lambda prof: [(r[3], r[5]) for r in ST.rows_of("c", "l", prof)]
            self.assertEqual(at("C"), [(u"赤", u"偽"), (u"緑", u"真"), (u"黄", u"真"), (u"赤", None)])
            self.assertEqual(at("B"), [(u"黄", u"偽"), (u"緑", u"真"), (u"黄", u"真")])
            self.assertEqual(at("A"), [(u"緑", u"偽"), (u"緑", u"真"), (u"緑", u"真"), (u"緑", u"真"), (u"緑", u"真")])
        finally:
            ST._load = real

    # --- f
    def test_f1_no_filing_id_or_company_field(self):
        for text in (self.rec_text, self.doc):
            self.assertEqual(re.findall(u"S100[0-9A-Z]{4}", text), [])
            for word in (u"docID", u"会社名", u"提出者", u"証券コード"):
                self.assertNotIn(word, text, word)
        nums = [c[u"番号"] for c in self.rec[u"FX の会社ごと"]]
        self.assertEqual(nums, list(range(1, len(nums) + 1)))

    def test_f2_limits_are_in_the_record_and_the_doc(self):
        self.assertEqual(len(self.rec[u"限界"]), 5)
        for word in (u"人は付けていない", u"封は無い", u"見る順", u"赤だけ見れば足りる」とは言えない", u"客の実物の文では測っていない", u"Claude の 2 つの model だけ"):
            self.assertIn(word, self.doc, word)


if __name__ == "__main__":
    unittest.main()
