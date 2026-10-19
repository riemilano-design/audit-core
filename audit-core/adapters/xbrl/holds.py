# -*- coding: utf-8 -*-
"""保留規則 (d)・P・U ― **外から渡された参照先が、値の照合だけでは確定しないときに止める。**

封 `docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md`(commit `ae528a4`。実装より先)。
規則は **1 つも新しく作らない**。`measure/` で封じて測った 3 つの写しである:

- (d) 同額の次元兄弟 ``measure/xbrl_dim_hold_rule_2026-10-17.py``
      (封 `docs/XBRL_DIM_HOLD_SEAL_2026-10-17.md`、結果 `docs/XBRL_DIM_HOLD_RESULT_2026-10-17.md`)
- P 同額の期間兄弟 / U 単位の種類 ``measure/xbrl_period_unit_hold_rule_2026-10-19.py``
      (封 `docs/XBRL_PERIOD_UNIT_HOLD_SEAL_2026-10-19.md`、結果 `docs/XBRL_PERIOD_UNIT_HOLD_RESULT_2026-10-19.md`)

**この file は ``audit_core`` を import しない**(データの層。``tests/adapters/xbrl/test_boundary.py``)。
**規則は減らす方向にしか動かない**: ``GROUNDED`` だけを ``UNPROVABLE`` に下げ、他の状態と参照先は
1 文字も変えない。**別の fact を正解として選び直さない**(兄弟は件数と軸としてだけ理由に出る)。

**保留は誤りの指摘ではない。**「現在の値照合だけでは参照先を確定できない」という意味である。
精度(危険な通過)はこの規則で変わらない ― 測定では 0 → 0 だった。

足した情報は **軸** だけ((e) の準備): (d) が発火したとき、``f`` と兄弟の枠で違う軸を
``hold_axes`` に出す。**どの軸の違いなら不一致かは決めない**(別の封)。
"""

GROUNDED = "GROUNDED"
#: 封の語は ``UNVERIFIABLE``。Core の既存の状態名 ``UNPROVABLE`` を使い、新しい名を作らない。
HELD_STATE = "UNPROVABLE"
REASON_D = "ambiguous_dimension:%d"
REASON_P = "ambiguous_period:%d"
REASON_U = "unit_class_mismatch:%s/%s"

#: 主張の単位の種類(封 P・U §1-2 の 3)。**字で留める。**
#: `円` は contract v1 が規則の対象から外しているので、ここに在っても発火の機会は無い。
CLAIM_CLASS = {u"百万円": "JPY", u"千円": "JPY", u"億円": "JPY", u"兆円": "JPY",
               u"円": "JPY", u"%": "pure", u"％": "pure"}

#: 応答に毎回入れる。**保留規則が見るもの / 見ないもの**を呼び出し側に隠さない。
CHECKS = (u"存在", u"値", u"同額の次元兄弟", u"同額の期間兄弟", u"単位の種類")
UNCHECKED = (u"重複", u"単位の倍率", u"期間(同額の兄弟が無いとき)",
             u"次元(同額の兄弟が無いとき)", u"要素の取り違え")


def dim_of(ctx):
    """枠の次元の部分(最初の ``_`` から後ろ)。**期間と次元を分ける 1 か所。**"""
    return ctx.split("_", 1)[1] if "_" in ctx else ""


def _same_value(g, f, tol):
    if g.get("value") is None or f.get("value") is None:
        return False
    return abs(g["value"] - f["value"]) <= tol


def _candidates(facts, f):
    """要素が同じで枠が違う fact(兄弟の母集団)。"""
    for g in facts:
        if g is f or g["name"] != f["name"] or g["context"] == f["context"]:
            continue
        yield g


def dimension_siblings(facts, f, tol):
    """(d): 次元の部分が違い、同単位・同額。**次元の有無は見ない**(曖昧さは対称)。"""
    out = []
    for g in _candidates(facts, f):
        if dim_of(g["context"]) == dim_of(f["context"]):
            continue                                   # 期間だけ違う → P の仕事
        if (g.get("unit") or "") != (f.get("unit") or ""):
            continue
        if not _same_value(g, f, tol):
            continue
        out.append(g)
    return out


def period_siblings(facts, f, tol):
    """P: 次元の部分が同じで枠が違う(= 期間だけ違う)、同単位・同額。"""
    out = []
    for g in _candidates(facts, f):
        if dim_of(g["context"]) != dim_of(f["context"]):
            continue                                   # 次元が違う → (d) の仕事
        if (g.get("unit") or "") != (f.get("unit") or ""):
            continue
        if not _same_value(g, f, tol):
            continue
        out.append(g)
    return out


def claim_class(unit):
    """主張の単位の種類。表に無い単位と ``None`` は **None(判定しない)**。"""
    return CLAIM_CLASS.get(unit)


def fact_class(unit):
    """fact の単位の種類。``JPY``・``pure`` はそのまま、**それ以外は字のまま**、空は None。"""
    if unit is None or unit == "":
        return None
    return unit


def unit_mismatch(claim_unit, f):
    """U の条件 3〜5。``(発火するか, claim_class, fact_class)``。"""
    cc = claim_class(claim_unit)
    fc = fact_class((f or {}).get("unit"))
    if cc is None or fc is None:
        return False, cc, fc
    return cc != fc, cc, fc


def axes_of(contexts, ctx):
    """枠の軸の組 ``{(軸, 枠の名)}``。``contexts`` が無い・枠が無い・``axes`` が無ければ空。"""
    c = (contexts or {}).get(ctx) or {}
    return set(tuple(a) for a in (c.get("axes") or ()))


def differing_axes(contexts, f, siblings):
    """``f`` と兄弟の枠で**どちらか一方にだけ在る**軸(QName)の一覧(昇順)。"""
    mine = {a for a, _m in axes_of(contexts, f["context"])}
    out = set()
    for g in siblings:
        theirs = {a for a, _m in axes_of(contexts, g["context"])}
        out |= mine ^ theirs
        # 同じ軸で枠の名だけ違う場合も「その軸が違う」
        for a, m in axes_of(contexts, f["context"]):
            for a2, m2 in axes_of(contexts, g["context"]):
                if a == a2 and m != m2:
                    out.add(a)
    return sorted(out)


def apply_holds(out, f, facts, tol, claim_unit, contexts=None):
    """(d) → P → U を**それぞれ独立に** ``out`` に当て、どれかが発火したら ``UNPROVABLE``。

    返すのは ``(新しい応答, {"d": bool, "P": bool, "U": bool})``。
    **``GROUNDED`` 以外は ``out`` をそのまま返す。参照先は変えない。``out`` も ``facts`` も書き換えない。**
    """
    fired = {"d": False, "P": False, "U": False}
    if out.get("state") != GROUNDED or f is None:
        return out, fired
    sd = dimension_siblings(facts, f, tol)
    sp = period_siblings(facts, f, tol)
    fu, cc, fc = unit_mismatch(claim_unit, f)
    fired = {"d": bool(sd), "P": bool(sp), "U": bool(fu)}
    if not any(fired.values()):
        return out, fired
    reasons = []
    if fired["d"]:
        reasons.append(REASON_D % len(sd))
    if fired["P"]:
        reasons.append(REASON_P % len(sp))
    if fired["U"]:
        reasons.append(REASON_U % (cc, fc))
    new = dict(out)
    new["state"] = HELD_STATE
    new["held"] = True
    new["reason"] = ";".join(reasons)
    new["hold_rules"] = tuple(k for k in ("d", "P", "U") if fired[k])
    new["hold_axes"] = differing_axes(contexts, f, sd) if fired["d"] else []
    assert new["pointers"] == out["pointers"], u"参照先を変えてはならない"
    return new, fired
