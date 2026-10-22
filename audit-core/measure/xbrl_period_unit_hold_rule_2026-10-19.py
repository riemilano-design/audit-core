# -*- coding: utf-8 -*-
u"""期間・単位の保留規則 P・U と、(d) → P → U の合成。

封 `docs/XBRL_PERIOD_UNIT_HOLD_SEAL_2026-10-19.md`(commit `f78c775`。実装より先)。

**engine を 1 行も変えない。**(d) の `dim_of`・`apply_hold` は import して使う(書き直さない)。
状態名は (d) と同じ食い違い(封の語 `UNVERIFIABLE` → Core の既存の名 `UNPROVABLE`)。
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, mod):
    sp = importlib.util.spec_from_file_location(mod, os.path.join(HERE, name))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


D = _load("xbrl_dim_hold_rule_2026-10-17.py", "dim_hold_rule_for_pu")
dim_of = D.dim_of
GROUNDED = D.GROUNDED
HELD_STATE = D.HELD_STATE
REASON_P = "ambiguous_period:%d"
REASON_U = "unit_class_mismatch:%s/%s"

#: 封 §1-2 の 3(主張の単位の種類)。**字で留める。**
CLAIM_CLASS = {u"百万円": "JPY", u"千円": "JPY", u"億円": "JPY", u"兆円": "JPY",
               u"円": "JPY", u"%": "pure", u"％": "pure"}


def claim_class(unit):
    u"""主張の単位の種類。表に無い単位と `None` は **None(判定しない)**。"""
    return CLAIM_CLASS.get(unit)


def fact_class(unit):
    u"""fact の単位の種類。`JPY`・`pure` はそのまま、**それ以外は字のまま**、`None` は None。"""
    if unit is None or unit == "":
        return None
    return unit


def period_siblings(facts, f, tol):
    u"""封 §1-1 の条件 3〜5: 要素同一・**次元の部分が同じで枠が違う**・同単位・tol 内。"""
    out = []
    for g in facts:
        if g is f:
            continue
        if g["name"] != f["name"]:
            continue                                   # 要素が違う
        if g["context"] == f["context"]:
            continue                                   # 同じ枠
        if dim_of(g["context"]) != dim_of(f["context"]):
            continue                                   # 次元が違う → (d) の仕事
        if (g.get("unit") or "") != (f.get("unit") or ""):
            continue                                   # 単位が違う
        if g.get("value") is None or f.get("value") is None:
            continue
        if abs(g["value"] - f["value"]) > tol:
            continue
        out.append(g)
    return out


def _hold(out, reason):
    new = dict(out)
    new["state"] = HELD_STATE
    new["held"] = True
    new["reason"] = reason
    assert new["pointers"] == out["pointers"], u"参照先を変えてはならない"
    return new


def apply_period_hold(out, f, facts, tol):
    u"""規則 P。``(新しい応答, 兄弟)``。**GROUNDED 以外は変えない。**"""
    if out.get("state") != GROUNDED or f is None:
        return out, []
    sibs = period_siblings(facts, f, tol)
    if not sibs:
        return out, []
    new = _hold(out, REASON_P % len(sibs))
    new["hold_period_siblings"] = len(sibs)
    return new, sibs


def unit_mismatch(claim_unit, f):
    u"""規則 U の条件 3〜5。``(発火するか, claim_class, fact_class)``。"""
    cc = claim_class(claim_unit)
    fc = fact_class((f or {}).get("unit"))
    if cc is None or fc is None:
        return False, cc, fc
    return cc != fc, cc, fc


def apply_unit_hold(out, f, claim_unit):
    u"""規則 U。``(新しい応答, 発火したか)``。**GROUNDED 以外は変えない。**"""
    if out.get("state") != GROUNDED or f is None:
        return out, False
    fire, cc, fc = unit_mismatch(claim_unit, f)
    if not fire:
        return out, False
    new = _hold(out, REASON_U % (cc, fc))
    new["hold_unit_classes"] = (cc, fc)
    return new, True


def apply_all(out, f, facts, tol, claim_unit):
    u"""合成(封 §1-3): (d) → P → U を**それぞれ v1 の応答に独立に当て**、
    どれかが発火したら `UNPROVABLE`。理由は発火した順に `;` で連結。

    返すのは ``(最終の応答, {"d": bool, "P": bool, "U": bool})``。
    """
    if out.get("state") != GROUNDED or f is None:
        return out, {"d": False, "P": False, "U": False}
    nd, sd = D.apply_hold(out, f, facts, tol)
    np_, sp_ = apply_period_hold(out, f, facts, tol)
    nu, fu = apply_unit_hold(out, f, claim_unit)
    fired = {"d": bool(sd), "P": bool(sp_), "U": bool(fu)}
    if not any(fired.values()):
        return out, fired
    reasons = [n["reason"] for n, k in ((nd, "d"), (np_, "P"), (nu, "U")) if fired[k]]
    new = _hold(out, ";".join(reasons))
    new["hold_rules"] = tuple(k for k in ("d", "P", "U") if fired[k])
    return new, fired
