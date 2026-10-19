# -*- coding: utf-8 -*-
"""外から渡された主張と参照先を、登録済みの規則で照合し、保留規則で止める入口(製品の経路)。

封 `docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md`(commit `ae528a4`。実装より先)。
中身は contract v1 の入口 ``measure/xbrl_verify_external_v1_2026-10-17.py``
(封 `docs/XBRL_CONTRACT_V1_SEAL_2026-10-17.md`)の**写し**に、保留規則 ``holds.apply_holds``
((d)・P・U)を足しただけである。**比較の算術は 1 つも新しく書かない**
(``audit_core`` に登録済みの comparator と :data:`vocabulary.UNIT_SCALE` をそのまま使う)。

役割: **特定は呼び出し側(LLM など)、実証はここ。**この入口は「正しい」を返さない。
``GROUNDED`` は「存在と値の検査を通過し、保留規則が 1 つも発火しなかった」という意味で、
:data:`holds.UNCHECKED` の属性は**見ていない**。応答の ``checks`` / ``unchecked`` に毎回入れる。

**PP(期間の対、2026-10-19 段 2)**: 封 `docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md`
(commit `790a5c5` + 追記 1 `78a04f5`)。率の主張(単位 ``％``/``%``・参照先 1 本)で、
その参照先が解けた fact の期間の札が ``CurrentYear*`` のとき、``holds.pp_pick`` で
前期の兄弟を 1 本に絞り、既存の ``contract_for("ratio_change", unit, 2)`` と
``core.verify`` で検算する。**符号は ``spec["sign"]``(``+1``/``-1``/``None``。文を読んで
決めるのは呼び出し側)で受け取る。**既定で有効(``period_pair=True``)。``period_pair=False``
を渡すと PP 以前の経路(contract v1 がそのまま参照先 2 本を要求する)に戻る
(③ `docs/XBRL_HOLDS_PRODUCT_PATH_RESULT_2026-10-19.md` の記録の再現用)。

使い方(library)::

    from adapters.xbrl import instance as I, verify_external as VE
    inst = I.load_instance(zip_bytes)
    out = VE.verify_external(
        {"kind": "single_value", "value": 771000.0, "unit": u"千円",
         "pointers": ["jppfs_cor:CurrentAssets@CurrentYearInstant"]},
        inst["facts"], inst["contexts"])
    out["state"]        # GROUNDED / VALUE_MISMATCH / POINTER_NOT_FOUND / UNPROVABLE
    out["held"]         # 保留なら True。out["hold_rules"] に ("d","P","U") の部分列
    out["checks"], out["unchecked"]
    out["derived_pointers"]   # PP が補った前期の兄弟(席の pointers は変えない)
    out["direction_checked"]  # PP で符号が +1/-1 として渡されたか

使い方(CLI)::

    python3 -m adapters.xbrl.verify_external --doc S100YXMA --claims claims.json --out out.json
    python3 -m adapters.xbrl.verify_external --zip <書類.zip> --claims claims.json --out out.json

``claims.json`` は ``{"claims": [{"id", "kind", "value", "unit", "pointers"[, "tolerance", "sign"]}, ...]}``。
``kind`` は ``single_value`` / ``difference`` / ``ratio_change``(規則の表 :data:`RULES`)。
``sign`` は任意(``1``/``-1``/``None``。PP の符号。渡さなければ符号不明として絶対値で比較)。
通信しない。EDINET に触らない(ZIP は手元の file だけ)。
"""

import argparse
import hashlib
import io
import json
import os
import sys

import audit_core as core

from . import holds as H
from . import instance as I
from . import recipes as R
from . import registry_setup as RS
from . import resolve as RV
from . import vocabulary as V

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

#: 規則の表(contract v1 封 §2)。``(規則の名, 必要な参照先の本数, comparator)``。
#: **v1 はこの 3 つだけ。増やすなら別の封。**
RULES = {
    "single_value": (u"単一の値(金額)", 1, "equals_within"),
    "difference": (u"差分", 2, "diff(a-b) equals_within"),
    "ratio_change": (u"変化率", 2, "pct_change(cur,prior)"),
}

#: 率の単位(``ratio_change`` だけが受ける)。
RATIO_UNITS = (u"%", u"％")

#: 率の許容。**新しい数を作らない** ― Core が字で留めている既定値を借りる。
DEFAULT_PCT_TOLERANCE = R.PCT_TOLERANCE_DEFAULT

UNPROVABLE = "UNPROVABLE"

#: **`円`(生の円)は v1 の対象から外す**(contract v1 の入口と同じ理由: 既存コードは `円` に
#: 書類ごとの丸め精度を使い、`UNIT_SCALE["円"] = 1` を許容幅にすると食い違う)。
EXCLUDED_MONEY_UNITS = (u"円",)

#: 出力の欄(**並びを字で固定する**。byte の安定のため)
RESULT_FIELDS = ("id", "kind", "value", "unit", "pointers", "state", "rule", "reason",
                 "held", "hold_rules", "hold_axes", "recomputed", "comparator",
                 "checks", "unchecked", "derived_pointers", "direction_checked")


def _money_scale(unit):
    if unit is None or unit in EXCLUDED_MONEY_UNITS:
        return None
    return V.UNIT_SCALE.get(unit)


def contract_for(kind, unit, n_pointers, tolerance=None):
    """主張の種類・単位・参照先の本数から contract を作る。作れなければ ``(None, 理由)``。"""
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
        return core.Contract(comparator=comparator, params={"tolerance": tol}), None
    scale = _money_scale(unit)
    if scale is None:
        return None, u"規則 %s は金額の単位を要る(渡されたのは %r)" % (name, unit)
    return core.Contract(comparator=comparator,
                         params={"unit_scale": float(scale), "claim_scale": float(scale)}), None


def tol_of(unit):
    """保留規則が使う同額の幅 = 比較器が梯子に渡す幅(``UNIT_SCALE[単位]``)。新しい閾値を作らない。"""
    return abs(V.UNIT_SCALE.get(unit, 1)) or 1


def _claim(spec, claim_id):
    return core.Claim(id=claim_id, form=core.Form("direct_value"),
                      subject=spec.get("subject"),
                      value=float(spec["value"]), unit=spec.get("unit"),
                      modifiers=core.Modifiers(),
                      provenance={"source": "external"})


def _fact_of(pointers, facts):
    """参照先 1 本が解けた fact(無ければ None)。

    **resolver と同じ選び方**(``resolve.make_resolver``: 同じ (名, 枠) が複数在れば instance の
    並びで先頭)。重複の件数と値の揺れは resolver の ``meta`` が持つ。兄弟の判定は枠が同じ fact を
    除くので、重複のどれを選んでも同じ答えになる。
    """
    if len(pointers) != 1:
        return None
    name, _, ctx = pointers[0].partition("@")
    for f in facts:
        if f["name"] == name and f["context"] == ctx:
            return f
    return None


def _verify_period_pair(spec, facts, contexts, registry, base, claim_id):
    """PP(期間の対)。``verify_external`` から、率の主張(参照先 1 本)に限って呼ばれる。

    封 `docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md` §0。``holds.pp_pick`` が前期の
    兄弟をちょうど 1 本に絞れたときだけ検算に進む(``contract_for`` と ``core.verify``
    は既存のものをそのまま使う。新しい比較器は作らない)。絞れないときは
    ``UNPROVABLE``(理由は ``holds.pp_pick`` のもの)。**常に応答の辞書を返す**
    (呼び出し側はここで確定。古い経路への fallback は無い)。
    """
    f = _fact_of(spec.get("pointers") or (), facts)
    decision = H.pp_pick(facts, f, spec.get("sign"))
    rule_name = RULES["ratio_change"][0]
    out = dict(base)
    out["direction_checked"] = decision["direction_checked"]
    if not decision["ok"]:
        out.update({"state": UNPROVABLE, "rule": rule_name, "reason": decision["reason"],
                    "recomputed": None, "comparator": None})
        return out
    prior = decision["prior"]
    prior_loc = "%s@%s" % (prior["name"], prior["context"])
    value = float(spec["value"])
    claim_value = float(spec["sign"]) * value if decision["direction_checked"] else abs(value)
    contract, why = contract_for("ratio_change", spec.get("unit"), 2, spec.get("tolerance"))
    if contract is None:
        out.update({"state": UNPROVABLE, "rule": rule_name, "reason": why,
                    "recomputed": None, "comparator": None, "derived_pointers": [prior_loc]})
        return out
    cur_loc = "%s@%s" % (f["name"], f["context"])
    claim = core.Claim(id=claim_id, form=core.Form("direct_value"), subject=spec.get("subject"),
                       value=claim_value, unit=spec.get("unit"), modifiers=core.Modifiers(),
                       provenance={"source": "external"})
    recipe = core.Recipe(claim=claim,
                         pointers=(core.Pointer("xbrl", cur_loc), core.Pointer("xbrl", prior_loc)),
                         contract=contract)
    resolver = RV.make_resolver(facts)
    res = core.verify(recipe, resolver, registry)
    out.update({"state": res.state.name, "rule": rule_name, "reason": res.reason,
                "recomputed": res.recomputed, "comparator": contract.comparator,
                "derived_pointers": [prior_loc],
                "comparison": (res.provenance or {}).get("comparison")})
    # 封 §3(H-10、測定 measure/xbrl_period_pair_2026-10-19.py と同じ呼び方): (d)・P・U は
    # 当期の fact f に対して **f 自身の単位**で当てる(claim_unit は spec["unit"](％)ではない。
    # 主張は率だが f は金額の fact なので、spec["unit"] を渡すと単位の種類が必ず不一致になる)。
    out, _fired = H.apply_holds(out, f, facts, tol_of(f["unit"]), f["unit"], contexts)
    if not decision["direction_checked"]:
        # 符号不明(絶対値で比較した): unchecked に「方向」を足す。
        # CHECKS/UNCHECKED の定数そのものは変えない(封 §5 の 1 通りの実装)。
        out["unchecked"] = H.UNCHECKED + (u"方向",)
    return out


def verify_external(spec, facts, contexts=None, registry=None, claim_id="EXT1", period_pair=True):
    """1 件の外部要求を検証して応答の辞書を返す(**file は書かない**)。

    ``spec`` は ``{"kind", "value", "unit", "pointers"[, "tolerance", "sign"]}``。
    ``facts`` / ``contexts`` は :func:`instance.load_instance` の返り値のもの。
    規則が無ければ ``UNPROVABLE``(検証しない)。``GROUNDED`` には保留規則を当てる。

    ``period_pair``(既定 ``True``): 率の主張(単位 ``％``/``%``・参照先 1 本)を
    PP(期間の対、封 `docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md`)で検算する。
    ``False`` を渡すと PP 以前の経路(contract v1 がそのまま参照先 2 本を要求する)
    に戻る(③ の記録の再現用)。
    """
    pointers = tuple(spec.get("pointers") or ())
    base = {"pointers": pointers, "kind": spec.get("kind"), "held": False,
            "hold_rules": (), "hold_axes": [], "checks": H.CHECKS, "unchecked": H.UNCHECKED,
            "derived_pointers": [], "direction_checked": False}
    if (period_pair and spec.get("kind") == "ratio_change" and len(pointers) == 1
            and spec.get("unit") in RATIO_UNITS):
        registry = registry or RS.register_all(core.Registry.default())
        return _verify_period_pair(spec, facts, contexts, registry, base, claim_id)
    contract, why = contract_for(spec.get("kind"), spec.get("unit"), len(pointers),
                                 spec.get("tolerance"))
    if contract is None:
        out = dict(base)
        out.update({"state": UNPROVABLE, "rule": None, "reason": why,
                    "recomputed": None, "comparator": None})
        return out
    rule_name = RULES[spec["kind"]][0]
    recipe = core.Recipe(claim=_claim(spec, claim_id),
                         pointers=tuple(core.Pointer("xbrl", p) for p in pointers),
                         contract=contract)
    resolver = RV.make_resolver(facts)
    registry = registry or RS.register_all(core.Registry.default())
    res = core.verify(recipe, resolver, registry)
    out = dict(base)
    out.update({"state": res.state.name, "rule": rule_name, "reason": res.reason,
                "recomputed": res.recomputed, "comparator": contract.comparator,
                "comparison": (res.provenance or {}).get("comparison")})
    f = _fact_of(pointers, facts)
    out, _fired = H.apply_holds(out, f, facts, tol_of(spec.get("unit")), spec.get("unit"),
                                contexts)
    return out


def verify_claims(claims, inst, registry=None, period_pair=True):
    """複数の主張を同じ instance で検証する。返すのは ``RESULT_FIELDS`` の並びの行の一覧。"""
    registry = registry or RS.register_all(core.Registry.default())
    rows = []
    for i, c in enumerate(claims):
        cid = c.get("id") or ("EXT%d" % (i + 1))
        out = verify_external(c, inst["facts"], inst.get("contexts"), registry, cid,
                              period_pair=period_pair)
        row = dict(out)
        row.update({"id": cid, "value": c.get("value"), "unit": c.get("unit"),
                    "pointers": list(out["pointers"]), "hold_rules": list(out["hold_rules"]),
                    "checks": list(out["checks"]), "unchecked": list(out["unchecked"]),
                    "derived_pointers": list(out["derived_pointers"])})
        rows.append({k: row.get(k) for k in RESULT_FIELDS})
    return rows


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def dumps(out):
    """**byte を 1 通りに決める。**(同じ入力 -> 同じ byte)"""
    return json.dumps(out, ensure_ascii=False, indent=1, sort_keys=False) + "\n"


def load_zip(path=None, doc=None):
    if (path is None) == (doc is None):
        raise ValueError("--zip か --doc のどちらか 1 つを渡す")
    if path is None:
        path = os.path.join(CACHE_DIR, "%s.zip" % doc)
    with open(path, "rb") as fh:
        return fh.read()


def run(zip_bytes, claims, period_pair=True):
    inst = I.load_instance(zip_bytes)
    rows = verify_claims(claims, inst, period_pair=period_pair)
    states = {}
    for r in rows:
        states[r["state"]] = states.get(r["state"], 0) + 1
    return {
        "tool": "adapters.xbrl.verify_external",
        "input": {"zip_sha256": sha256_bytes(zip_bytes), "zip_bytes": len(zip_bytes),
                  "instance_source": inst["source"], "facts": len(inst["facts"]),
                  "contexts": len(inst["contexts"]), "claims": len(claims)},
        "states": {k: states[k] for k in sorted(states)},
        "held": sum(1 for r in rows if r["held"]),
        "checks": list(H.CHECKS), "unchecked": list(H.UNCHECKED),
        "results": rows,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--zip", default=None, help=u"書類の ZIP の道")
    ap.add_argument("--doc", default=None, help=u"EDINET docID(手元のキャッシュから読む)")
    ap.add_argument("--claims", required=True, help=u'{"claims": [...]} の JSON file')
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    zb = load_zip(a.zip, a.doc)
    with io.open(a.claims, encoding="utf-8") as fh:
        claims = json.load(fh)["claims"]
    out = run(zb, claims)
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(dumps(out))
    print("written: %s  claims=%d  %s  held=%d"
          % (a.out, out["input"]["claims"], out["states"], out["held"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
