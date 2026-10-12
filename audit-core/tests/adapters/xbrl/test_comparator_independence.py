# -*- coding: utf-8 -*-
"""比較器(値の照合)を強制したときに、pointer の選択が動くかを測る恒久の門。

**人間の裁定 2026-10-12 §3** による。測るのは 1 つの不変条件である:

> **どの fact に束縛するかは、Claim の値が一致するかどうかに依存してはならない。**

測り方は、`vocabulary.match_value` を

* 「常に不一致」(`None` を返す)
* 「常に一致」(真を返す)

の 2 通りに差し替え、`build_raw_claims` が返す数の Claim の **`form` と `pointer`** が
変わる件数と、変わった id の一覧の sha256 を、**字で書いた期待値**と突き合わせる。

**いまの実装(`recipes.py` の `hits[0]`)はこの不変条件を満たしていない。**
だからこの門は「0 件であること」ではなく **「測った件数が字で固定した数と一致すること」** を要求する。
両方向に失敗を検出する:

* 値への依存が増えれば件数が増えて赤くなる。
* 値への依存が減れば件数が減って赤くなる ― **直したときは期待値を同じコミットで更新する**
  (封 `audit-core/docs/CANDIDATE_DEFINITION_SEAL_2026-10-12.md` §4-G は、設計 Y で
  **0 / 0 になる**と予測している)。

**この門が測るのは 2 書類・2 profile・数の Claim 151 件だけである。**
「すべての入力・すべての経路で成立する」ことは測っていない(台帳 L-011 の限定と同じ)。
AI が書いた文章での同じ測定(`S100Z4Q1` の 304 件で 68 / 98)は
`audit-core/fixtures/xbrl/value_independence_2026-10-12.py` が行い、
材料が追跡されていない ZIP なのでこの門には入れていない。
"""

import hashlib
import json
import unittest

from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

from . import _material as M


# 2026-10-12 の実測。**人が決めた数ではなく測った数**だが、字で書くことで
# 「この経路の振る舞いが変わったか」を機械が検出できるようにする
# ([[pin-human-decided-numbers-literally]] と同じ理由で、定数から作らない)。
EXPECTED = {
    ("1B", "never"): (23, "942ba9de084ed4fb9a2dce2eca306148eeeafad7b058767879681ff5a79dfb2c"),
    ("1B", "always"): (37, "04847ee14478605406685dcd59e216bae4466f28c154704fa9508129423a7d95"),
    ("5F", "never"): (8, "6d1a2a39aa5537fc1c255d43b98bc49d0c30fb42992081529b6bbc7cae72b86e"),
    ("5F", "always"): (34, "91cae9bc09d3c498ae2b8c5f35e8b9143a78951a1469bfc4e8374042e89f35f7"),
}
EXPECTED_CLAIM_COUNT = {"1B": 60, "5F": 91}


def _snapshot(zb, profile):
    """数の Claim の (form, pointer) だけを取る。値・状態・理由は見ない。"""

    num_claims, _text_claims = R.build_raw_claims(zb, profile)
    return {c["id"]: (c.get("form"), json.dumps(c.get("pointer"), ensure_ascii=False))
            for c in num_claims}


def _forced(zb, profile, mode):
    original = V.match_value
    try:
        if mode == "never":
            V.match_value = lambda fact_value, target, unit: None
        elif mode == "always":
            V.match_value = lambda fact_value, target, unit: "forced"
        else:
            raise AssertionError("mode")
        return _snapshot(zb, profile)
    finally:
        V.match_value = original


class ComparatorIndependenceTest(unittest.TestCase):
    """比較器を強制したときに動く pointer の件数を字で留める。"""

    def _run_one(self, tag, doc, profile):
        zb = M.load_zip_bytes(doc["docID"], doc["sha256"])
        base = _snapshot(zb, profile)
        self.assertEqual(len(base), EXPECTED_CLAIM_COUNT[tag],
                         "%s: 数の Claim の件数が変わった(母集団が動いた)" % (tag,))
        # 差し替えから戻ったことを確かめる(戻し忘れると後続の試験を黙らせる)
        self.assertEqual(_snapshot(zb, profile), base, "%s: 差し替えが戻っていない" % (tag,))

        for mode in ("never", "always"):
            other = _forced(zb, profile, mode)
            moved = sorted(i for i in base if base[i] != other.get(i))
            sha = hashlib.sha256(("\n".join(moved) + "\n").encode("utf-8")).hexdigest()
            want_n, want_sha = EXPECTED[(tag, mode)]
            self.assertEqual(
                (len(moved), sha), (want_n, want_sha),
                "%s/%s: 比較器を強制したときに pointer が動いた件数が %d 件(期待 %d 件)。"
                "動いた id = %s\n"
                "値への依存が変わったなら、封の予測と実測を記録した上で EXPECTED を"
                "同じコミットで更新すること。" % (tag, mode, len(moved), want_n, ",".join(moved)))
            self.assertEqual(_snapshot(zb, profile), base,
                             "%s/%s: 差し替えが戻っていない" % (tag, mode))

    def test_1B_comparator_forcing(self):
        self._run_one("1B", M.DOC_1, V.P1)

    def test_5F_comparator_forcing(self):
        self._run_one("5F", M.DOC_5, V.P5F)

    def test_the_gate_is_not_vacuous(self):
        """門が空でないこと: 差し替えが実際に Claim を動かしている。

        4 つの期待値がすべて 0 なら、この門は何も測っていないのと同じになる
        (将来 0 / 0 になったときは、**その 0 を作る経路の試験を別に足す**)。
        """
        self.assertTrue(any(n for n, _sha in EXPECTED.values()),
                        "期待値が全部 0 なら、差し替えが届いていないのか直ったのかを"
                        "区別できない。直ったのなら 0 を保証する別の試験を足すこと。")
