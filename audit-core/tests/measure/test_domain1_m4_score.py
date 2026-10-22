"""段 4 の採点器を**本物のラベルを見る前に**固定する(封 §5)。

材料は手で作った合成の答え。守るのは 4 つ。
  1. 2 席が食い違った行は**判定不能として分母に残る**(分母を小さくしない)
  2. 値が合っていても根拠が違えば**誤接続**として数える
  3. ラベルが「根拠なし」なのに接続したら **G-3**
  4. 母数が 20 未満なら**判定不能**(合格とも不合格とも書かない)
"""
import importlib.util
import io
import json
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "measure", "sheet_m4_score_2026-10-15.py")

spec = importlib.util.spec_from_file_location("m4s", SCRIPT)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def claim(cid, value=100):
    return {"id": cid, "value": value, "sentence": "文 %s" % cid, "scorable": True,
            "undecidable": False}


def bind(cid, state="GROUNDED", scope="一般会計", level="款", name="議会費",
         column="支出済額"):
    return {"claim_id": cid, "state": state, "route": "R-1" if state == "GROUNDED" else None,
            "pointer": "sheet:x!D10",
            "evidence": {"scope": scope, "level": level, "name": name, "column": column}}


def ans(cid, **kw):
    d = {"id": cid}
    d.update(kw)
    return d


LABEL = dict(会計="一般会計", 階層="款", 科目名="議会費", 列="支出済額")


class UnitTest(unittest.TestCase):
    def test_agreement_makes_a_confirmed_label(self):
        k, same = S.confirmed(ans("R1", **LABEL), ans("R1", **LABEL))
        self.assertTrue(same)
        self.assertEqual(k[0], "label")

    def test_disagreement_becomes_undecidable_and_stays_in_the_denominator(self):
        other = dict(LABEL, 科目名="総務費")
        k, same = S.confirmed(ans("R1", **LABEL), ans("R1", **other))
        self.assertFalse(same)
        self.assertEqual(k, ("verdict", S.norm("判定不能")))

    def test_a_non_grounded_bind_has_no_engine_key(self):
        self.assertIsNone(S.engine_key(bind("R1", state="VALUE_MISMATCH")))

    def test_an_account_level_bind_has_an_empty_subject_name(self):
        k = S.engine_key(bind("R1", level="会計", name="一般会計", column="歳出決算額"))
        self.assertEqual(k[1][2], "")


class EndToEndTest(unittest.TestCase):
    def _run(self, claims, binds, a1, a2):
        d = tempfile.mkdtemp(prefix="m4score-")
        S.BINDS = os.path.join(d, "b.json")
        S.SEAT1 = os.path.join(d, "s1.json")
        S.SEAT2 = os.path.join(d, "s2.json")
        S.OUT = os.path.join(d, "out.json")
        json.dump({"claims": claims, "binds": binds},
                  io.open(S.BINDS, "w", encoding="utf-8"), ensure_ascii=False)
        json.dump({"answers": a1}, io.open(S.SEAT1, "w", encoding="utf-8"), ensure_ascii=False)
        json.dump({"answers": a2}, io.open(S.SEAT2, "w", encoding="utf-8"), ensure_ascii=False)
        S.main()
        return json.load(io.open(S.OUT, encoding="utf-8"))

    def test_a_wrong_ground_with_a_right_value_is_counted_as_a_false_link(self):
        r = self._run([claim("R1")], [bind("R1", name="総務費")],
                      [ans("R1", **LABEL)], [ans("R1", **LABEL)])
        self.assertEqual(r["lines"]["G-2 誤接続"]["count"], 1)
        self.assertEqual(r["rows"][0]["wrong_fields"], ["科目名"])

    def test_grounding_a_claim_the_labels_call_unfounded_is_g3(self):
        r = self._run([claim("R1")], [bind("R1")],
                      [ans("R1", verdict="根拠なし")], [ans("R1", verdict="根拠なし")])
        self.assertEqual(r["lines"]["G-3 根拠なしの接続"]["count"], 1)
        self.assertEqual(r["lines"]["G-2 誤接続"]["count"], 0)

    def test_holding_back_on_an_unfounded_claim_counts_in_g4(self):
        r = self._run([claim("R1")], [bind("R1", state="POINTER_NOT_FOUND")],
                      [ans("R1", verdict="根拠なし")], [ans("R1", verdict="根拠なし")])
        self.assertEqual(r["lines"]["G-4 保留の適切さ"]["num"], 1)
        self.assertEqual(r["lines"]["G-4 保留の適切さ"]["den"], 1)

    def test_a_small_denominator_is_undecidable_not_a_pass(self):
        r = self._run([claim("R1")], [bind("R1")], [ans("R1", **LABEL)], [ans("R1", **LABEL)])
        self.assertEqual(r["lines"]["G-1 接続の正確さ"]["num"], 1)
        self.assertEqual(r["overall"], "判定不能(母数不足)")

    def test_disagreeing_seats_lower_the_accuracy_instead_of_shrinking_it(self):
        claims = [claim("R%d" % i) for i in range(1, 21)]
        binds = [bind("R%d" % i) for i in range(1, 21)]
        a1 = [ans("R%d" % i, **LABEL) for i in range(1, 21)]
        a2 = [ans("R%d" % i, **(LABEL if i > 5 else dict(LABEL, 科目名="総務費")))
              for i in range(1, 21)]
        r = self._run(claims, binds, a1, a2)
        self.assertEqual(r["lines"]["G-5 母数"]["count"], 20)      # 分母は縮まない
        self.assertEqual(r["lines"]["G-1 接続の正確さ"]["num"], 15)
        self.assertEqual(r["lines"]["G-4 保留の適切さ"]["den"], 5)  # 食い違いは保留の分母へ
        self.assertEqual(r["lines"]["G-2 誤接続"]["count"], 5)      # 保留すべき行に接続した


if __name__ == "__main__":
    unittest.main()
