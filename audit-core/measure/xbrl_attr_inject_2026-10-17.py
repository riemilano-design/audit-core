# -*- coding: utf-8 -*-
"""封 `docs/XBRL_ATTR_INJECT_SEAL_2026-10-17.md` の実測。

**単位・期間・次元を 1 つだけ変えた fact を注入して、Core が誤って通すかを測る。**
併せて**注入しない実材料での露出**(同じ値を別の期間・次元・単位に持つ兄弟 fact)を数える。

**engine は 1 行も変えない。規則を増やさない。0 USD・席は呼ばない。**
**注入は instance の fact 一覧に足すだけで、repo にも書類にも残さない。**

    python3 measure/xbrl_attr_inject_2026-10-17.py
"""
import collections
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
OUT = os.path.join(FX, "attr_inject_2026-10-17.json")
SEAL = "docs/XBRL_ATTR_INJECT_SEAL_2026-10-17.md"

from adapters.xbrl import instance as I                     # noqa: E402
from adapters.xbrl import prose as PR                        # noqa: E402
from adapters.xbrl import edinet as ED                       # noqa: E402

_vp = importlib.util.spec_from_file_location(
    "verify_external_v1_for_attr",
    os.path.join(HERE, "xbrl_verify_external_v1_2026-10-17.py"))
VE = importlib.util.module_from_spec(_vp)
_vp.loader.exec_module(VE)
_sp = importlib.util.spec_from_file_location(
    "inv_for_attr", os.path.join(HERE, "xbrl_verify_inventory_2026-10-17.py"))
INV = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(INV)
A1, MB, IJ = INV.A1, INV.MB, INV.IJ

PASS = "GROUNDED"
#: 注入した枠の名。**実在の枠と衝突しない字**にする。
TEST_MEMBER = "_AttrInjectTestMember"


#: 期間の接頭辞(**字で留める**)。`period_free` が**実在しない枠**を選ぶために使う。
PERIOD_PREFIXES = ("CurrentYear", "Prior1Year", "Prior2Year", "Prior3Year",
                   "Prior4Year")


def _period_of(ctx):
    for a in PERIOD_PREFIXES:
        if ctx.startswith(a):
            return a
    return None


def period_candidates(ctx):
    """**期間だけ違う枠の名**を、実在しうる順に全部返す(字の置き換えだけ)。"""
    cur = _period_of(ctx)
    if cur is None:
        return []
    rest = ctx[len(cur):]
    return [a + rest for a in PERIOD_PREFIXES if a != cur]


def period_existing(facts, name, ctx):
    """**実在する**「期間だけ違う枠」の最初の 1 つ(無ければ None)。"""
    have = {f["context"] for f in facts if f["name"] == name}
    for c in period_candidates(ctx):
        if c in have:
            return c
    return None


def period_free(facts, name, ctx):
    """**実在しない**「期間だけ違う枠」の最初の 1 つ(無ければ None)。

    **注入は必ず実在しない枠に作る** ― 実在する枠を指すと、
    止まったのが「期間を見たから」ではなく「値が違ったから」になり、
    **1 つの欄に 2 つの別物が混ざる**(第 1 便で実際に混ざった)。
    """
    have = {f["context"] for f in facts if f["name"] == name}
    for c in period_candidates(ctx):
        if c not in have:
            return c
    return None


def inject(facts, base, branch):
    """**値を変えず属性 1 つだけ変えた fact を 1 件足す。**(新しい一覧を返す)

    返すのは ``(新しい facts, 注入した key, 作れなかった理由)``。
    **判定を 1 か所に置く**(枝ごとに字を散らさない)。
    """
    name, ctx, val, unit = (base["name"], base["context"], base["value"],
                            base["unit"])
    if branch == u"対照":
        return facts, "%s@%s" % (name, ctx), None
    if branch == u"単位":
        new = dict(base, context=ctx + "_UnitTest", unit="USD")
    elif branch == u"期間(注入)":
        p = period_free(facts, name, ctx)
        if p is None:
            return facts, None, u"実在しない期間の枠を作れない(%s)" % ctx
        new = dict(base, context=p)
    elif branch == u"期間(実在の枠を指す)":
        p = period_existing(facts, name, ctx)
        if p is None:
            return facts, None, u"期間だけ違う実在の枠が無い"
        # **足さない。**実在の fact をそのまま指す(値は書類のまま)
        return facts, "%s@%s" % (name, p), None
    elif branch == u"次元":
        new = dict(base, context=ctx + TEST_MEMBER)
    else:
        raise ValueError(branch)
    if any(f["name"] == new["name"] and f["context"] == new["context"]
           for f in facts):
        return facts, None, u"注入したい枠が既に在る(%s)" % new["context"]
    return facts + [new], "%s@%s" % (new["name"], new["context"]), None


def exposure(facts, base, tol):
    """**注入しない実材料での露出。**同じ値を別の期間・次元・単位に持つ兄弟 fact。"""
    name, ctx, val, unit = (base["name"], base["context"], base["value"],
                            base["unit"])
    out = {u"別の期間": [], u"別の次元": [], u"別の単位": []}
    for f in facts:
        if f["name"] != name or f["context"] == ctx:
            continue
        if f["value"] is None or abs(f["value"] - val) > tol:
            continue
        same_dim = (I._nonconsolidated_only(f["context"], {}) is None)  # 使わない
        key = "%s@%s" % (f["name"], f["context"])
        if (f["unit"] or "") != (unit or ""):
            out[u"別の単位"].append(key)
        elif _dim_of(f["context"]) != _dim_of(ctx):
            out[u"別の次元"].append(key)
        else:
            out[u"別の期間"].append(key)
    return out


def _dim_of(ctx):
    """枠の次元の部分(最初の `_` から後ろ)。**期間と次元を分ける 1 か所。**"""
    return ctx.split("_", 1)[1] if "_" in ctx else ""


def main():
    if os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(測り直さない)" % OUT)
    v1 = json.load(io.open(os.path.join(FX, "contract_v1_2026-10-17.json"),
                           encoding="utf-8"))
    passed = [x for x in v1["rows"] if x[u"**B′ の最終判定**"] == u"検査通過"]
    by_doc = collections.defaultdict(list)
    for x in passed:
        by_doc[x[u"doc"]].append(x)
    seed, _m = IJ.verify_seed_sealed(MB.SEED_FILE)
    rows = []
    for doc in sorted(by_doc):
        zb = io.open(ED.cache_path(doc), "rb").read()
        old, A1.TMP = A1.TMP, MB.TMP
        try:
            text, refs = A1.material(doc)
        finally:
            A1.TMP = old
        chosen, _c = MB.pick_injections(text, refs, seed, doc)
        tampered, pl = IJ.apply_edits(text, chosen)
        mrows = {r["id"]: r for r in MB.build_rows(tampered, chosen, pl)[0]}
        zb2, _e, _mm = PR.build_modified_zip(zb, tampered)
        facts = I.load_instance(zb2)["facts"]
        keys = {A1.norm_pointer("xbrl:%s@%s" % (f["name"], f["context"])): f
                for f in facts}
        for x in by_doc[doc]:
            r = mrows[x[u"id"]]
            base = keys.get(x[u"席の参照先"])
            spec = {"kind": "single_value", "value": r[u"値"],
                    "unit": r[u"単位"]}
            if base is None:
                rows.append({u"doc": doc, u"id": x[u"id"],
                             u"**無効**": u"席の参照先が instance に無い"})
                continue
            tol = abs(VE.V.UNIT_SCALE.get(r[u"単位"], 1)) or 1
            rec = {u"doc": doc, u"id": x[u"id"], u"値": r[u"値"],
                   u"単位": r[u"単位"], u"参照先": x[u"席の参照先"],
                   u"fact の値": base["value"], u"fact の単位": base["unit"],
                   u"枝": {}}
            for branch in (u"対照", u"単位", u"期間(注入)",
                           u"期間(実在の枠を指す)", u"次元"):
                fs, key, why = inject(facts, base, branch)
                if key is None:
                    rec[u"枝"][branch] = {u"作れなかった": why}
                    continue
                out = VE.verify_external(dict(spec, pointers=[key]), fs)
                rec[u"枝"][branch] = {
                    u"注入した key": key, u"state": out["state"],
                    u"**誤って通した**": (branch != u"対照"
                                  and out["state"] == PASS)}
            rec[u"露出(注入なし)"] = {k: {u"件数": len(v), u"例": v[:3]}
                               for k, v in exposure(facts, base, tol).items()}
            rows.append(rec)

    valid = [x for x in rows if not x.get(u"**無効**")
             and x[u"枝"][u"対照"].get(u"state") == PASS]
    invalid = [x for x in rows if x not in valid]
    t = collections.Counter()
    for x in valid:
        for branch in (u"単位", u"期間(注入)", u"期間(実在の枠を指す)", u"次元"):
            b = x[u"枝"][branch]
            if u"作れなかった" in b:
                t[(branch, u"作れなかった")] += 1
            else:
                t[(branch, u"試せた")] += 1
                t[(branch, u"**誤って通した**")] += bool(b[u"**誤って通した**"])
                t[(branch, u"止めた(" + b[u"state"] + ")")] += (
                    0 if b[u"**誤って通した**"] else 1)
        for k in (u"別の期間", u"別の次元", u"別の単位"):
            if x[u"露出(注入なし)"][k][u"件数"]:
                t[(u"露出", k)] += 1

    def rate(num, den):
        return {u"分子": num, u"分母": den,
                u"率": (round(100.0 * num / den, 1) if den else None)}

    n = len(valid)
    pred = [
        {u"記号": "Q-1", u"予測": u"対照 = 24/24 が GROUNDED",
         u"実測": u"%d/%d" % (n, len(rows)), u"当たり": n == 24 == len(rows)},
        {u"記号": "Q-2", u"予測": u"単位注入 → 24/24 が誤って通過",
         u"実測": u"%d/%d" % (t[(u"単位", u"**誤って通した**")],
                           t[(u"単位", u"試せた")]),
         u"当たり": (t[(u"単位", u"**誤って通した**")] == n
                 == t[(u"単位", u"試せた")])},
        {u"記号": "Q-3", u"予測": u"期間注入 → 24/24 が誤って通過",
         u"実測": u"%d/%d" % (t[(u"期間(注入)", u"**誤って通した**")],
                           t[(u"期間(注入)", u"試せた")]),
         u"当たり": (t[(u"期間(注入)", u"**誤って通した**")] == n
                 == t[(u"期間(注入)", u"試せた")])},
        {u"記号": "Q-4", u"予測": u"次元注入 → 24/24 が誤って通過",
         u"実測": u"%d/%d" % (t[(u"次元", u"**誤って通した**")],
                           t[(u"次元", u"試せた")]),
         u"当たり": (t[(u"次元", u"**誤って通した**")] == n
                 == t[(u"次元", u"試せた")])},
        {u"記号": "Q-5", u"予測": u"別の期間に同じ値 = 1 行以上",
         u"実測": t[(u"露出", u"別の期間")],
         u"当たり": t[(u"露出", u"別の期間")] >= 1},
        {u"記号": "Q-6", u"予測": u"別の次元に同じ値 = 1 行以上",
         u"実測": t[(u"露出", u"別の次元")],
         u"当たり": t[(u"露出", u"別の次元")] >= 1},
        {u"記号": "Q-7", u"予測": u"別の単位に同じ値 = 0 行",
         u"実測": t[(u"露出", u"別の単位")],
         u"当たり": t[(u"露出", u"別の単位")] == 0},
        {u"記号": "Q-8",
         u"予測": u"注入で POINTER_NOT_FOUND / 実証不能 = 0 行",
         u"実測": sum(v for (b, k), v in t.items()
                    if b in (u"単位", u"期間(注入)", u"次元")
                    and (u"POINTER_NOT_FOUND" in k or u"UNPROVABLE" in k)),
         u"当たり": not any(
             (u"POINTER_NOT_FOUND" in k or u"UNPROVABLE" in k)
             for (b, k) in t if b in (u"単位", u"期間(注入)", u"次元")),
         u"注": u"**VALUE_MISMATCH は数えない**(予測は見つからない・規則が無いの 2 つについて。"
               u"第 1 便の器は VALUE_MISMATCH も数えていた)"},
    ]
    hit = sum(1 for p in pred if p[u"当たり"])
    rec = {
        "seal": SEAL,
        "step": u"**属性注入の実測。engine 不変・規則不変・0 USD・席は呼ばない**",
        u"基準": u"contract v1 が検査通過させた行(`**B′ の最終判定**` = 検査通過)",
        u"行": {u"基準": len(rows), u"**対照が通った(有効)**": n,
              u"無効": [{k: x[k] for k in x if k in (u"doc", u"id", u"**無効**")}
                      for x in invalid]},
        u"**第 1 部 注入**": {
            branch: {u"試せた": t[(branch, u"試せた")],
                     u"作れなかった": t[(branch, u"作れなかった")],
                     u"**誤って通した**": rate(t[(branch, u"**誤って通した**")],
                                      t[(branch, u"試せた")])}
            for branch in (u"単位", u"期間(注入)", u"期間(実在の枠を指す)",
                           u"次元")},
        u"**第 2 部 露出(注入なし)**": {
            k: rate(t[(u"露出", k)], n)
            for k in (u"別の期間", u"別の次元", u"別の単位")},
        u"**予測との照合**": {u"欄ごと": pred, u"当たり": hit,
                      u"外れ": len(pred) - hit},
        u"rows": rows,
        u"limits": [
            u"**人工の注入は穴の存在を示すが、実務で何件起きるかではない**(封 §4)",
            u"**誤通過の件数は注入を作った私の手で決まる。**危険度は第 2 部で語る",
            u"**24 行は contract v1 が通した行である。**通らなかった行の穴は測っていない",
            u"**0 件でも「放置してよい」とは書かない**(封 §5)",
            u"**engine を直していない。規則も増やしていない。**",
            u"**注入は instance の fact 一覧に足しただけで、repo にも書類にも残さない。**",
        ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(u"=== 属性注入(単位・期間・次元)。0 USD・engine 不変 ===")
    print(u"基準 %d 行 / **対照が通った(有効)%d 行**" % (len(rows), n))
    for branch in (u"単位", u"期間(注入)", u"期間(実在の枠を指す)", u"次元"):
        v = rec[u"**第 1 部 注入**"][branch]
        print(u"  %s: 試せた %d(作れなかった %d)→ **誤って通した %s**"
              % (branch, v[u"試せた"], v[u"作れなかった"],
                 u"%s%%(%s/%s)" % (v[u"**誤って通した**"][u"率"],
                                   v[u"**誤って通した**"][u"分子"],
                                   v[u"**誤って通した**"][u"分母"])))
    print(u"--- 第 2 部 露出(注入なし。同じ値を持つ兄弟 fact が在る行)---")
    for k in (u"別の期間", u"別の次元", u"別の単位"):
        v = rec[u"**第 2 部 露出(注入なし)**"][k]
        print(u"  %-6s %s%%(%s/%s)" % (k, v[u"率"], v[u"分子"], v[u"分母"]))
    print(u"--- 予測との照合 ---")
    for p in pred:
        print(u"  %-4s %-36s 実測 %-12s %s"
              % (p[u"記号"], p[u"予測"], p[u"実測"],
                 u"**当たり**" if p[u"当たり"] else u"**外れ**"))
    print(u"  当たり %d / 外れ %d" % (hit, len(pred) - hit))
    print(u"->", OUT)


if __name__ == "__main__":
    main()
