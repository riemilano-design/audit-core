# -*- coding: utf-8 -*-
"""外から渡された主張と参照先を、登録済みの規則で照合する入口(contract v1)。

封 `docs/XBRL_CONTRACT_V1_SEAL_2026-10-17.md`(2026-10-17 の人間の決定)。

**置き場所について(封の字との食い違いを記録する)**

封 §1 はこの file を `adapters/xbrl/verify_external.py` と書いた。しかし
**既存の境界試験**(`tests/adapters/xbrl/test_boundary.py` の
`test_only_recipes_and_run_import_core_among_adapter_files`)は、
**adapters/xbrl の中で `audit_core` を import してよい file を 6 つに限っている。**
新しい入口はその一覧に無いので、置けば**既存の構造の約束を破る。**

**一覧を書き換えて通すことはしない**(試験を自分の都合で緩めるのと同じ)。
**封の字も直さない**(測った後の封は編集しない)。
だから**この実験のあいだは `measure/` に置く。**
**製品のどこに置くか(境界の一覧を変えるか)は構造の決定であり、人間が決める。**
役割を替える設計 ― **特定は呼び出し側(LLM)、実証はここ** ― の最小の入口である。

**比較の算術は 1 つも新しく書かない。**`audit_core` に登録済みの comparator
(``equals_within`` / ``diff(a-b) equals_within`` / ``pct_change(cur,prior)``)と
:data:`adapters.xbrl.vocabulary.UNIT_SCALE` をそのまま使う。
この file が足すのは **「外から来た主張と参照先から Recipe を組む」ことだけ**で、
``recipes``・``verify_document``・``resolve``・``comparators`` は 1 行も変えていない。

**この入口は「正しい」を返さない。**``GROUNDED`` は
**「現行 Core の検査を通過した」**という意味で、:data:`UNCHECKED` の 4 つは**見ていない**
(封 §2 の 1。根拠は ``docs/XBRL_VERIFY_INVENTORY_2026-10-17.md``)。
応答の ``unchecked`` に毎回その 4 つを入れて返すので、呼び出し側は
**未検査属性を隠せない。**

使い方::

    from adapters.xbrl import instance as I
    # 置き場所は measure/(上の「置き場所について」を読むこと)

    facts = I.load_instance(zip_bytes)["facts"]
    out = VE.verify_external(
        {"kind": "single_value", "value": 771000.0, "unit": u"千円",
         "pointers": ["jppfs_cor:CurrentAssets@CurrentYearInstant"]},
        facts)
    out["state"]      # GROUNDED / VALUE_MISMATCH / POINTER_NOT_FOUND / UNPROVABLE
    out["rule"]       # 使った規則の名(規則が無ければ None)
    out["unchecked"]  # ("単位", "期間", "次元(連結区分)", "重複")
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

import audit_core as core                                    # noqa: E402

from adapters.xbrl import recipes as R                        # noqa: E402
from adapters.xbrl import registry_setup as RS                # noqa: E402
from adapters.xbrl import resolve as RV                       # noqa: E402
from adapters.xbrl import vocabulary as V                     # noqa: E402

#: **この入口が見ていない属性。**応答に毎回入れる(封 §2 の 1)。
UNCHECKED = (u"単位", u"期間", u"次元(連結区分)", u"重複")

#: 規則の表(封 §2)。``(規則の名, 必要な参照先の本数, comparator)``。
#: **v1 はこの 3 つだけ。増やすなら別の封。**
RULES = {
    "single_value": (u"単一の値(金額)", 1, "equals_within"),
    "difference": (u"差分", 2, "diff(a-b) equals_within"),
    "ratio_change": (u"変化率", 2, "pct_change(cur,prior)"),
}

#: 率の単位(``ratio_change`` だけが受ける)。
RATIO_UNITS = (u"%", u"％")

#: 率の許容。**新しい数を作らない** ― Core が字で留めている既定値を借りる
#: (``recipes.PCT_TOLERANCE_DEFAULT``)。呼び出し側が ``tolerance`` を渡せば
#: それを使う(**許容は判断なので、呼び出し側が書けるようにしておく**)。
DEFAULT_PCT_TOLERANCE = R.PCT_TOLERANCE_DEFAULT

UNPROVABLE = "UNPROVABLE"


#: **`円`(生の円)は v1 の対象から外す。**
#:
#: 既存の `recipes._direct_value_claim` は `円` だけ
#: ``scale = prec``(fact の `decimals` から来る書類ごとの丸め精度)を使い、
#: ``UNIT_SCALE["円"] = 1`` は使わない。`UNIT_SCALE` の 1 をそのまま許容幅にすると、
#: **既存コードが同じ単位に与えている許容と食い違う**(独立監査の指摘、2026-10-17)。
#: 許容を合わせるには precision を渡す経路が要り、それは
#: 「比較の算術は新しく書かない」という封 §1 を超える。**だから規則を与えない。**
#: 封 §2 の表は `円` を対象に含むと書いているが、**封の字は直さず、ここで外す。**
EXCLUDED_MONEY_UNITS = (u"円",)


def _money_scale(unit):
    """金額の単位から ``unit_scale`` を引く。**無ければ None**(規則が無い)。

    `円` は :data:`EXCLUDED_MONEY_UNITS` により **None**(規則が無い)。
    """
    if unit is None or unit in EXCLUDED_MONEY_UNITS:
        return None
    return V.UNIT_SCALE.get(unit)


def contract_for(kind, unit, n_pointers, tolerance=None):
    """主張の種類・単位・参照先の本数から contract を作る。

    **作れない組み合わせでは ``(None, 理由)`` を返す。**その行は ``実証不能`` になる
    (封 §2 の落とし口)。判定を 1 か所に置くため、呼び出し側はここだけを見る。
    """
    rule = RULES.get(kind)
    if rule is None:
        return None, u"規則が無い(未知の種類: %r)" % (kind,)
    name, want, comparator = rule
    if n_pointers != want:
        return None, (u"規則 %s は参照先 %d 本を要る(渡されたのは %d 本)"
                      % (name, want, n_pointers))
    if kind == "ratio_change":
        if unit not in RATIO_UNITS:
            return None, u"規則 %s は率の単位を要る(渡されたのは %r)" % (name, unit)
        tol = DEFAULT_PCT_TOLERANCE if tolerance is None else float(tolerance)
        return core.Contract(comparator=comparator,
                             params={"tolerance": tol}), None
    scale = _money_scale(unit)
    if scale is None:
        return None, u"規則 %s は金額の単位を要る(渡されたのは %r)" % (name, unit)
    return core.Contract(comparator=comparator,
                         params={"unit_scale": float(scale),
                                 "claim_scale": float(scale)}), None


def _claim(spec, claim_id):
    return core.Claim(id=claim_id, form=core.Form("direct_value"),
                      subject=spec.get("subject"),
                      value=float(spec["value"]), unit=spec.get("unit"),
                      modifiers=core.Modifiers(),
                      provenance={"source": "external"})


def verify_external(spec, facts, registry=None, claim_id="EXT1"):
    """1 件の外部要求を検証して応答の辞書を返す(**file は書かない**)。

    ``spec`` は ``{"kind", "value", "unit", "pointers"}``。
    ``facts`` は :func:`adapters.xbrl.instance.load_instance` の ``facts``。

    **規則が無ければ ``UNPROVABLE`` を返し、検証しない。**
    ``GROUNDED`` は「現行 Core の検査を通過した」だけで、``unchecked`` の 4 つは見ていない。
    """
    pointers = tuple(spec.get("pointers") or ())
    base = {"unchecked": UNCHECKED, "pointers": pointers,
            "kind": spec.get("kind")}
    contract, why = contract_for(spec.get("kind"), spec.get("unit"),
                                 len(pointers), spec.get("tolerance"))
    if contract is None:
        out = dict(base)
        out.update({"state": UNPROVABLE, "rule": None, "reason": why,
                    "recomputed": None, "comparator": None})
        return out
    rule_name = RULES[spec["kind"]][0]
    recipe = core.Recipe(
        claim=_claim(spec, claim_id),
        pointers=tuple(core.Pointer("xbrl", p) for p in pointers),
        contract=contract)
    resolver = RV.make_resolver(facts)
    registry = registry or RS.register_all(core.Registry.default())
    res = core.verify(recipe, resolver, registry)
    out = dict(base)
    out.update({"state": res.state.name, "rule": rule_name,
                "reason": res.reason, "recomputed": res.recomputed,
                "comparator": contract.comparator,
                "comparison": (res.provenance or {}).get("comparison")})
    return out
