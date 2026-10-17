# -*- coding: utf-8 -*-
u"""(d) 同額の次元兄弟が在れば保留にする規則。

封 `docs/XBRL_DIM_HOLD_SEAL_2026-10-17.md`(commit `407dbcd`。実装より先)。
人間の承認:**封じた (d) の限定実装と測定まで。**

**engine を 1 行も変えない。**`adapters/`・`core/` は触らず、
contract v1 の入口(`xbrl_verify_external_v1_2026-10-17.py`)の**応答を後から見る**層として
`measure/` に置く(置き場所の理由は入口 file の冒頭と同じ ―
`tests/adapters/xbrl/test_boundary.py` の一覧を自分の都合で書き換えない)。

**封の字との食い違いを 2 つ記録する(封は直さない)**

1. **状態の名。**封 §4 は `UNVERIFIABLE` と書いたが、**Core の状態名は `UNPROVABLE`**
   である(`audit_core` の `State`)。**新しい状態名を作らない**ので `UNPROVABLE` を返し、
   `held=True` と理由で区別できるようにする。
2. **`tol`。**封 §2 の 5 は「比較器が使ったものと同じ値」と書いた。金額の比較器
   (`equals_within`)が梯子に渡す幅は `claim_scale`(= `UNIT_SCALE[単位]`)なので、
   **その数をそのまま使う。**(露出を数えた `attr_inject` と同じ数である。)
   **比較器が主張の値に対して許す帯**(`_match_value` が `g` も受けるか)は別の数え方で、
   **測定では別の欄として記録する** ― 1 つの欄に 2 つの機構を混ぜない。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

GROUNDED = "GROUNDED"
#: 封 §4 の `UNVERIFIABLE`。**Core の既存の状態名を使う**(上の食い違い 1)。
HELD_STATE = "UNPROVABLE"
REASON = "ambiguous_dimension:%d"


def dim_of(ctx):
    u"""枠の次元の部分(最初の `_` から後ろ)。**期間と次元を分ける 1 か所。**

    `measure/xbrl_attr_inject_2026-10-17.py` の `_dim_of` と同じ定義
    (封 §2 の 4 がこの関数を名指している)。
    """
    return ctx.split("_", 1)[1] if "_" in ctx else ""


def siblings(facts, f, tol):
    u"""封 §2 の条件 3〜5 を満たす fact を返す。

    3. 要素が同一(`name` が同じ)
    4. **枠の次元の部分が違う**(期間だけ違う枠は :func:`dim_of` が同じなので入らない)
    5. 単位が同じで、値の差が `tol` 以内

    **次元の有無は見ない**(封 §2 の最後 ― 曖昧さは対称)。
    """
    out = []
    for g in facts:
        if g is f:
            continue
        if g["name"] != f["name"]:
            continue                                   # 要素が違う → 対象外
        if g["context"] == f["context"]:
            continue                                   # 同じ枠(同じ fact)
        if dim_of(g["context"]) == dim_of(f["context"]):
            continue                                   # 期間だけ違う → 対象外
        if (g.get("unit") or "") != (f.get("unit") or ""):
            continue                                   # 単位が違う → 対象外
        if g.get("value") is None or f.get("value") is None:
            continue
        if abs(g["value"] - f["value"]) > tol:
            continue                                   # 同額でない
        out.append(g)
    return out


def apply_hold(out, f, facts, tol):
    u"""contract v1 の応答に (d) を当てる。``(新しい応答, 兄弟の一覧)`` を返す。

    **`GROUNDED` 以外は 1 文字も変えない**(封 §4)。
    **参照先は増やさない・選び直さない**(封 §3-2)。
    """
    if out.get("state") != GROUNDED or f is None:
        return out, []
    sibs = siblings(facts, f, tol)
    if not sibs:
        return out, []
    new = dict(out)
    new["state"] = HELD_STATE
    new["held"] = True
    new["reason"] = REASON % len(sibs)
    new["hold_siblings"] = len(sibs)
    # **参照先を触っていないことを、その場で確かめる**(封 §3-2・予測 D-13)
    assert new["pointers"] == out["pointers"], u"参照先を変えてはならない"
    return new, sibs
