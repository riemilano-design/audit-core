# -*- coding: utf-8 -*-
import copy
import unittest

from adapters.kokkai import verify_meeting as VM
from tests.adapters.kokkai import _material as M


def _run(claims):
    return VM.verify_meeting(copy.deepcopy(M.MEETING), M.summary(claims))


class EndToEndTest(unittest.TestCase):
    def test_all_four_points_right_is_grounded(self):
        out = _run([M.claim("K-1", quote="暫定予算は三百億円", number={"text": "三百億円", "value": 3e10, "unit": "円"})])
        self.assertEqual(out["claims"][0]["state"], "GROUNDED")
        self.assertEqual(out["claims"][0]["checks"], {"speaker": "GROUNDED", "quote": "GROUNDED", "number": "GROUNDED"})
        self.assertEqual(out["document"]["states"], {"GROUNDED": 1})
        self.assertEqual(out["document"]["check_states"], {"GROUNDED": 3})

    def test_wrong_order_is_pointer_not_found_on_every_check(self):
        out = _run([M.claim("K-1", order=42, quote="暫定予算は三百億円")])
        self.assertEqual(out["claims"][0]["state"], "POINTER_NOT_FOUND")
        self.assertEqual(out["claims"][0]["checks"], {"speaker": "POINTER_NOT_FOUND", "quote": "POINTER_NOT_FOUND"})
        self.assertEqual(out["checks"][0]["reason"], "unresolved:kokkai:%s#42" % M.ISSUE)

    def test_wrong_speaker_is_value_mismatch(self):
        out = _run([M.claim("K-1", speaker="佐藤花子")])
        self.assertEqual(out["claims"][0]["state"], "VALUE_MISMATCH")

    def test_other_existing_order_with_quote_is_caught_by_the_quote(self):
        # 発言者が同じ別の発言(1 → 3)に差し替えると、発言者は一致するが引用で止まる
        out = _run([M.claim("K-1", order=3, quote="暫定予算は三百億円")])
        self.assertEqual(out["claims"][0]["checks"], {"speaker": "GROUNDED", "quote": "VALUE_MISMATCH"})
        self.assertEqual(out["claims"][0]["state"], "VALUE_MISMATCH")

    def test_other_existing_order_without_quote_or_number_passes(self):
        # 計画 §8 の T1 の外れ方そのもの: 発言者だけの claim は別の発言に差し替えても捕まらない
        out = _run([M.claim("K-1", order=3)])
        self.assertEqual(out["claims"][0]["state"], "GROUNDED")

    def test_missing_order_is_unverifiable(self):
        c = M.claim("K-1"); del c["speech_order"]
        out = _run([c])
        self.assertEqual(out["claims"][0]["state"], "UNVERIFIABLE")
        self.assertEqual(out["checks"][0]["reason"], "no_pointer_given")

    def test_fold_order_is_pnf_over_vm_over_unv(self):
        self.assertEqual(VM.fold_claim_state(["GROUNDED", "VALUE_MISMATCH", "POINTER_NOT_FOUND"]), "POINTER_NOT_FOUND")
        self.assertEqual(VM.fold_claim_state(["UNVERIFIABLE", "VALUE_MISMATCH"]), "VALUE_MISMATCH")
        self.assertEqual(VM.fold_claim_state(["GROUNDED", "UNVERIFIABLE"]), "UNVERIFIABLE")
        self.assertEqual(VM.fold_claim_state(["GROUNDED", "GROUNDED"]), "GROUNDED")
        with self.assertRaises(ValueError):
            VM.fold_claim_state([])

    def test_rule_text_is_pinned_literally(self):
        self.assertEqual(VM.CLAIM_STATE_RULE, (
            "claim の検査(発言者・引用・数)の state のうち、1 つでも POINTER_NOT_FOUND なら POINTER_NOT_FOUND。"
            "無ければ、1 つでも VALUE_MISMATCH なら VALUE_MISMATCH。"
            "無ければ、1 つでも UNVERIFIABLE なら UNVERIFIABLE。"
            "全部 GROUNDED なら GROUNDED。検査が 0 件の claim は無い(発言者の検査は必ず作る)。"))
        out = _run([M.claim("K-1")])
        self.assertEqual(out["document"]["rule"], VM.CLAIM_STATE_RULE)

    def test_issue_id_mismatch_raises(self):
        s = M.summary([M.claim("K-1")]); s["issueID"] = "OTHER"
        with self.assertRaises(ValueError):
            VM.verify_meeting(copy.deepcopy(M.MEETING), s)

    def test_output_is_deterministic_bytes(self):
        a = VM.dumps(_run([M.claim("K-1", quote="三回目")]))
        b = VM.dumps(_run([M.claim("K-1", quote="三回目")]))
        self.assertEqual(a, b)

    def test_claims_keep_summary_order_and_every_claim_appears_once(self):
        out = _run([M.claim("K-2", order=2, speaker="佐藤花子"), M.claim("K-1")])
        self.assertEqual([c["id"] for c in out["claims"]], ["K-2", "K-1"])
