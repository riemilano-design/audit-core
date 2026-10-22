# -*- coding: utf-8 -*-
u"""期間の対(PP, period pair)― 率の主張(参照先 1 本)を前期の兄弟で検算する規則。

封 `docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md`(commit `790a5c5`。実装より先)。
**段 1(engine 不変)。**比較の算術は 1 つも新しく書かない ―
`adapters.xbrl.holds.dim_of`・`adapters.xbrl.verify_external.contract_for`・
`adapters.xbrl.resolve.make_resolver`・`audit_core.verify` をそのまま import して使うだけ。

規則(封 §0):

1. **前期の兄弟** = 同じ `name`、同じ `dim_of(context)`、期間の札(`context` の
   最初の `_` より前)が `CurrentYear` → `Prior1Year` に置き換わった枠の fact。
   `f` の期間の札が `CurrentYear` で始まらなければ `prior_siblings` は `None`
   を返す(「当てない」。当期でない fact には当てない)。
2. 兄弟が**ちょうど 1 本**なら、参照先を `(f, 兄弟)` の 2 本に機械で補い、
   既存の比較器 `pct_change(cur,prior)`(許容 `PCT_TOLERANCE_DEFAULT`。
   `adapters/xbrl/recipes.py`。新しい閾値は作らない)で検算する。
   **0 本・2 本以上なら `UNPROVABLE`、理由 `prior_sibling:<本数>`。**
3. **符号**: 主張の数の字面の直後(8 字以内)に **増・伸・上回** があれば `+1`、
   **減・下回・落ち** があれば `-1`、どちらも無ければ `None`(符号不明)。
   符号が在れば符号つきで比較、無ければ絶対値で比較する(応答の `sign_checked`
   に符号が在ったかを残す。新しい比較器は作らない ― 絶対値の比較は
   `claim.value` に絶対値を渡すだけで、`pct_change` 自身は変えない)。
4. PP が補った兄弟は応答の `derived_pointers` に**別欄で**書く
   (席が名指した参照先そのものは変えない)。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

import audit_core as core                     # noqa: E402

from adapters.xbrl import holds as H           # noqa: E402
from adapters.xbrl import resolve as RV        # noqa: E402
from adapters.xbrl import verify_external as VE  # noqa: E402

#: `dim_of` は engine(`adapters/xbrl/holds.py`)の実物をそのまま使う(書き直さない)。
dim_of = H.dim_of

#: 符号の字(封 §0 の 3)。**字で留める。**
SIGN_UP = (u"増", u"伸", u"上回")
SIGN_DOWN = (u"減", u"下回", u"落ち")
#: 数の字面の直後、何字まで見るか(封 §0 の 3)。
SIGN_WINDOW = 8

UNPROVABLE = VE.UNPROVABLE


def period_tag(ctx):
    u"""枠の期間の札(`context` の最初の `_` より前)。"""
    return ctx.split("_", 1)[0]


def prior_siblings(facts, f):
    u"""前期の兄弟の一覧。

    同じ `name`・同じ `dim_of(context)` で、期間の札が `CurrentYear` → `Prior1Year`
    に置き換わった枠の fact を**全部**返す(どれを選ぶかは `apply_pp` が本数で決める)。

    `f` の期間の札が `CurrentYear` で始まらなければ **`None`**
    (「当てない」。封 §0 の当たらない例の 2 つ目: 期間の札が `Prior1YearDuration`
    の fact を名指した主張には PP を当てない)。
    """
    tag = period_tag(f["context"])
    if not tag.startswith("CurrentYear"):
        return None
    prior_tag = "Prior1Year" + tag[len("CurrentYear"):]
    dim = dim_of(f["context"])
    out = []
    for g in facts:
        if g is f or g["name"] != f["name"]:
            continue
        if dim_of(g["context"]) != dim:
            continue                                   # 次元が違う兄弟は数えない
        if period_tag(g["context"]) != prior_tag:
            continue
        out.append(g)
    return out


def sign_from_text(excerpt, number_text):
    u"""数の字面の直後 `SIGN_WINDOW` 字以内の符号の字。

    `number_text` が `excerpt` に複数回出るなら、**最初に出た位置**を採る
    (どれを採るかを機械で決める。封は「書く」としか言っていないので、
    最初の出現を正とする選び方をここに 1 通りだけ書く)。
    見つからなければ `None`(符号不明)。
    """
    i = excerpt.find(number_text)
    if i < 0:
        return None
    window = excerpt[i + len(number_text): i + len(number_text) + SIGN_WINDOW]
    if any(w in window for w in SIGN_UP):
        return 1
    if any(w in window for w in SIGN_DOWN):
        return -1
    return None


def apply_pp(spec, f, facts, registry):
    u"""PP を 1 件の主張に当てる。

    ``spec`` は ``{"kind": "ratio_change", "value", "unit", "pointers": [当期 1 本],
    "sign": +1/-1/None}``。``f`` は ``spec["pointers"][0]`` が解けた fact
    (呼び出し側が解く。ここでは参照先の文字列を読まない)。

    返すのは ``{"state", "reason", "recomputed", "derived_pointers", "sign_checked"}``。
    **``spec["pointers"]`` そのものは変えない**(補った兄弟は ``derived_pointers`` に別欄)。
    """
    sign = spec.get("sign")
    sign_checked = sign in (1, -1)

    def held(reason, derived):
        return {"state": UNPROVABLE, "reason": reason, "recomputed": None,
                "derived_pointers": derived, "sign_checked": sign_checked}

    if f is None:
        return held("no_fact", [])
    sibs = prior_siblings(facts, f)
    if sibs is None:
        # 当期でない fact には当てない(封 §0 の当たらない例の 2 つ目)。
        return held("not_current_year", [])
    if len(sibs) != 1:
        return held("prior_sibling:%d" % len(sibs), [])
    g = sibs[0]
    cur_loc = "%s@%s" % (f["name"], f["context"])
    prior_loc = "%s@%s" % (g["name"], g["context"])

    value = spec["value"]
    claim_value = float(sign * value) if sign_checked else float(abs(value))
    contract, why = VE.contract_for("ratio_change", spec.get("unit"), 2)
    if contract is None:
        return held(why, [prior_loc])

    claim = core.Claim(id=spec.get("id", "PP1"), form=core.Form("direct_value"),
                       subject=spec.get("subject"), value=claim_value,
                       unit=spec.get("unit"), modifiers=core.Modifiers(),
                       provenance={"source": "pp"})
    recipe = core.Recipe(claim=claim,
                         pointers=(core.Pointer("xbrl", cur_loc), core.Pointer("xbrl", prior_loc)),
                         contract=contract)
    resolver = RV.make_resolver(facts)
    res = core.verify(recipe, resolver, registry)
    return {"state": res.state.name, "reason": res.reason, "recomputed": res.recomputed,
            "derived_pointers": [prior_loc], "sign_checked": sign_checked}
