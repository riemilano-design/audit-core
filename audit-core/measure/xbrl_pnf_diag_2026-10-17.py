# -*- coding: utf-8 -*-
"""**診断: `POINTER_NOT_FOUND` の 10 行で Core がどの key を試したか。**

人間の指示(2026-10-17)の 1 番。**Core の関数・正規化・探索挙動は変えない。**
読むだけ・数えるだけ。**費用 0 USD・席は呼ばない・通信しない。**

## 既存の記録では足りない(先に確かめたこと)

`fixtures/xbrl/cd8/material_2026-10-17.json` が持つのは **結果の参照先**
(`verify_document` の `claims[].pointers`)で、**試した key は入っていない**。
`POINTER_NOT_FOUND` のとき結果の参照先は空なので、記録からは「何を試したか」が出ない。
だから**診断用の記録だけを足す**(engine には触らない)。

## 配線は Core と同じであることを門で示す

`verify_document` と**同じ呼び出し・同じ順**で recipe を作り、
`core.verify_all` の結果(state と pointers)が
`verify_document` の出力と**全主張で一致すること**を要求する。
一致しなければ止める ― **私の配線が Core と違うなら、観測は Core の観測ではない。**

    python3 measure/xbrl_pnf_diag_2026-10-17.py
"""
import collections
import hashlib
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
MAT = os.path.join(FX, "material_2026-10-17.json")
OUT = os.path.join(FX, "pnf_diag_2026-10-17.json")

import audit_core as core                                    # noqa: E402
from adapters.xbrl import instance as I                      # noqa: E402
from adapters.xbrl import prose as PR                         # noqa: E402
from adapters.xbrl import recipes as R                        # noqa: E402
from adapters.xbrl import registry_setup as RS                # noqa: E402
from adapters.xbrl import resolve as RV                       # noqa: E402
from adapters.xbrl import verify_document as VD               # noqa: E402
from adapters.xbrl import edinet as ED                        # noqa: E402
from adapters.xbrl import vocabulary as V                     # noqa: E402


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


MB = _mod("cd_material_for_diag", "xbrl_cd_material_2026-10-17.py")
A1 = MB.A1
IJ = MB.IJ
PROFILE = MB.PROFILE


def member_of(ctx):
    """**Core 自身の helper を使う**(次元メンバーの読み方を自分で書かない)。

    **生の context を渡すこと。**`norm_pointer` を通した小文字の context を渡すと
    `None` が返る(一度それで誤った記録を作った。記憶
    `normalize-both-sides-of-a-comparison`)。
    """
    return R._member_of_ctx(ctx)


def norm(name, ctx):
    """**instance 側の鍵を、正解と同じ関数で正規化する。**

    正解は `A1.norm_pointer` を通った小文字の `element@context` である。
    instance の fact 名は `jppfs_cor:OperatingRevenue2` のように大文字を含む。
    **片側だけで照合すると「正解の要素名が instance に無い」と誤って出る。**
    """
    return A1.norm_pointer("xbrl:%s@%s" % (name, ctx))


def ctx_of(locator):
    return locator.split("@", 1)[1] if "@" in locator else ""


def name_of(locator):
    return locator.split("@", 1)[0].split(":")[-1]


def vocab_of(zb2, inst, profile):
    """**Core が使った語彙(語 -> 要素)をそのまま読む。**手書き行 + ラベル由来行。

    `build_recipes` と同じ関数(`_label_subjects`)を呼ぶだけで、**作り方は変えない。**
    """
    rows = list(profile.subjects)
    added = []
    if getattr(profile, "label_vocabulary", False):
        hand_rows, added, _ov = R._label_subjects(zb2, inst, profile)
        rows = list(hand_rows) + list(added)
    return rows, len(added)


def classify_candidate_zero(gold, subject, vocab, names):
    """**候補 0 の内訳。**語彙と subject から、どこで落ちたかを 1 か所で決める。

    **引くのは `subject`(Core が文から決めた主語)である。**
    `word` は向きの語の欄で、数の主張では `None` になる ―
    一度 `word` で引いて「語が取れていない」と誤った記録を作った。
    """
    g = name_of(gold)
    in_vocab = any(g == A1.norm_pointer("xbrl:%s@x" % e).split("@")[0]
                   for _w, elems in vocab for e in elems)
    if subject is None:
        return (u"subject が文から取れていない", in_vocab, None)
    hit = R._elements_for_word(vocab, subject)
    if hit is None:
        return (u"その subject が語彙に無い", in_vocab, None)
    norm_hit = [A1.norm_pointer("xbrl:%s@x" % e).split("@")[0] for e in hit]
    if g in norm_hit:
        return (u"語彙は正解の要素を持っていた(落ちたのは後段)", in_vocab, list(hit))
    return (u"subject に当たった要素に正解が無い", in_vocab, list(hit))


def classify(tried, gold, names, keys):
    """**分類を 1 か所に置く。**記録が裏づけない原因は返さない。

    `tried` は **正規化済みの key**、`gold` も正規化済み、
    `names`・`keys` も同じ関数を通した集合であること。
    """
    if not tried:
        return u"候補 0(試した key が 1 本も無い)"
    g_name = name_of(gold)
    same_name = [t for t in tried if name_of(t) == g_name]
    if same_name:
        return u"要素名は同じで context が違う"
    absent = [t for t in tried if name_of(t) not in names]
    if absent:
        return u"試した要素名が instance に無い"
    if all(t not in keys for t in tried):
        return u"要素名は在るが、その context に fact が無い"
    return u"その他"


def main():
    if os.path.exists(OUT):
        raise SystemExit(u"既に在る: %s(測り直さない)" % OUT)
    mat = json.load(io.open(MAT, encoding="utf-8"))
    seed, _meta = IJ.verify_seed_sealed(MB.SEED_FILE)
    target = {}
    for p in mat[u"書類ごと"]:
        ids = [rid for rid, pre in p[u"席の前に出せる分"].items()
               if pre["Core"][u"参照先"] is None
               and (pre[u"正解"] or {}).get(u"種類") == u"参照先が在る"]
        if ids:
            target[p["docID"]] = (sorted(ids), p)
    rows, per_doc = [], {}
    for doc, (ids, prec) in sorted(target.items()):
        zb = io.open(ED.cache_path(doc), "rb").read()
        old_tmp, A1.TMP = A1.TMP, MB.TMP
        try:
            text, refs = A1.material(doc)
        finally:
            A1.TMP = old_tmp
        chosen, _counts = MB.pick_injections(text, refs, seed, doc)
        tampered, placements = IJ.apply_edits(text, chosen)
        mrows, _ = MB.build_rows(tampered, chosen, placements)
        task = MB.seat_text(mrows, tampered, refs)
        sha = hashlib.sha256(task.encode("utf-8")).hexdigest()
        if sha != prec[u"材料"]["sha256"]:
            raise SystemExit(u"**材料が封の記録と違う: %s。止める**" % doc)

        # **verify_document と同じ呼び出し・同じ順**
        zb2, element, member = PR.build_modified_zip(zb, tampered)
        inst = I.load_instance(zb2)
        resolver = RV.make_resolver(inst["facts"])
        registry = RS.register_all(core.Registry.default())
        recipe_list = R.build_recipes(zb2, V.PROFILES[PROFILE])
        results = core.verify_all(recipe_list, resolver, registry)
        by_id = {r.claim_id: r for r in results}
        rec_by_id = {rp.claim.id: rp for rp in recipe_list}

        ref = VD.verify_document(zb, PROFILE, tampered)
        mismatch = []
        for c in ref["claims"]:
            got = by_id.get(c["id"])
            if got is None:
                mismatch.append((c["id"], "missing"))
                continue
            ptrs = [(p if isinstance(p, str) else p.scheme + ":" + p.locator)
                    for p in got.pointers]
            if got.state.name != c["state"] or ptrs != c["pointers"]:
                mismatch.append((c["id"], got.state.name, c["state"]))
        if mismatch:
            raise SystemExit(u"**配線が verify_document と違う: %s。止める**"
                             % mismatch[:3])

        ctx_by_name = collections.defaultdict(list)
        for f in inst["facts"]:
            ctx_by_name[norm(f["name"], "").split("@")[0]].append(f["context"])
        names = {norm(f["name"], "").split("@")[0] for f in inst["facts"]}
        keys = {norm(f["name"], f["context"]) for f in inst["facts"]}
        raw_ctx = {norm(f["name"], f["context"]): f["context"]
                   for f in inst["facts"]}
        vocab, n_added = vocab_of(zb2, inst, V.PROFILES[PROFILE])
        claims = ref["claims"]
        per_doc[doc] = {u"主張の数": len(claims),
                        u"**配線が verify_document と一致**": True,
                        u"材料の sha256 が封の記録と一致": True,
                        u"instance の fact 数": len(inst["facts"]),
                        u"次元つきの context を持つ fact": sum(
                            1 for f in inst["facts"] if member_of(f["context"])),
                        u"text 差し替え": {"element": element, "member": member},
                        u"語彙の行": len(vocab),
                        u"うちラベル由来": n_added}
        for rid in ids:
            r = next(x for x in mrows if x["id"] == rid)
            claim = None
            for c in claims:
                if c.get("value") is None:
                    continue
                if (abs(c["value"] - r[u"値"]) <= A1.TOL
                        and r[u"数の字面"] in (c.get("span") or "")):
                    claim = c
                    break
            gold = prec[u"席の前に出せる分"][rid][u"正解"][u"正解"]
            tried_raw, tried = [], []
            if claim is not None:
                rp = rec_by_id.get(claim["id"])
                for p in (rp.pointers if rp else ()):
                    tried_raw.append(p.locator)
                    n, _, c = p.locator.partition("@")
                    tried.append(norm(n, c))
            got = by_id.get(claim["id"]) if claim is not None else None
            _cz = (classify_candidate_zero(gold, (claim or {}).get("subject"),
                                           vocab, names)
                   if not tried else (None, None, None))
            rows.append({
                u"doc": doc, u"id": rid, u"値": r[u"値"],
                u"数の字面": r[u"数の字面"],
                u"Core の主張 id": (claim or {}).get("id"),
                u"Core の state": (claim or {}).get("state"),
                u"Core の reason": (claim or {}).get("reason"),
                u"**試した key**(生)": tried_raw,
                u"**試した key**": tried,
                u"試した key の内訳": [
                    {u"key": t, u"生": raw, u"要素名": name_of(t),
                     u"次元(生の context から)": member_of(
                         raw.partition("@")[2]),
                     u"要素名が instance に在る": name_of(t) in names,
                     u"この context に fact が在る": t in keys}
                    for t, raw in zip(tried, tried_raw)],
                u"正解の key": gold,
                u"正解の context(生)": raw_ctx.get(gold),
                u"正解の次元(生の context から)": member_of(
                    raw_ctx.get(gold) or ""),
                u"正解の (要素名, context) が instance に在る": gold in keys,
                u"正解の要素名が instance に在る": name_of(gold) in names,
                u"Core が見た語": (claim or {}).get("word"),
                u"Core が決めた subject": (claim or {}).get("subject"),
                u"**候補 0 の内訳**": (
                    {u"どこで落ちたか": _cz[0],
                     u"正解の要素が語彙に在る": _cz[1],
                     u"その語に当たった要素": _cz[2]} if not tried else None),
                u"**正解の要素名が在る context**": sorted(
                    {(c, member_of(c) or u"次元なし")
                     for c in ctx_by_name.get(name_of(gold), [])}),
                u"**正解の要素名に次元なしの context が在るか**": any(
                    not member_of(c) for c in ctx_by_name.get(name_of(gold), [])),
                u"**分類**": classify(tried, gold, names, keys),
                u"結果の参照先": [(p if isinstance(p, str)
                              else p.scheme + ":" + p.locator)
                             for p in (got.pointers if got else ())]})

    kinds = collections.Counter(r[u"**分類**"] for r in rows)
    dim = collections.Counter(
        (bool(r[u"正解の次元(生の context から)"]),
         bool(any(x[u"次元(生の context から)"]
                  for x in r[u"試した key の内訳"]))) for r in rows)
    rec = {"step": u"**診断のみ。engine は触っていない。0 USD・席は呼ばない**",
           u"人間の指示": u"2026-10-17 の 1 番(POINTER_NOT_FOUND の試行 key を記録する)",
           u"profile": PROFILE,
           u"**既存の記録で足りなかった理由**": (
               u"material の記録は `verify_document` の **結果の** 参照先しか持たない。"
               u"`POINTER_NOT_FOUND` では結果が空なので、**試した key は記録に無い**"),
           u"書類ごと": per_doc,
           u"**観測**": {u"行": len(rows),
                     u"候補 0 の内訳ごと": dict(collections.Counter(
                         (r[u"**候補 0 の内訳**"] or {}).get(u"どこで落ちたか")
                         for r in rows)),
                     u"正解の要素が語彙に在った行": sum(
                         1 for r in rows
                         if (r[u"**候補 0 の内訳**"] or {}).get(
                             u"正解の要素が語彙に在る")),
                     u"分類ごと": dict(kinds),
                     u"(正解に次元, 試した key に次元)": {
                         u"%s/%s" % k: v for k, v in dim.items()}},
           u"rows": rows,
           u"limits": [
               u"**10 行の観測である。**ここから Core 全体の振る舞いを断定しない",
               u"**正規化は両側に同じ関数(`A1.norm_pointer`)を掛けた。**"
               u"一度これを片側だけに掛けて「正解の要素名が instance に無い」と"
               u"誤った記録を作った(この記録は掛け直した後の 1 本)",
               u"**原因の分類は、試した key と instance の fact だけから付けた。**"
               u"なぜその key を選んだか(member の解決・語彙・ラベル)は見ていない",
               u"**直していない。**この記録は改善の提案ではなく観測である",
               u"**2 書類に偏っている**(残る 6 書類では起きていない)。"
               u"書類差と注入箇所の差は分けていない",
           ]}
    json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(u"=== POINTER_NOT_FOUND 10 行の診断(0 USD・engine は触らない)===")
    for d, v in sorted(per_doc.items()):
        print(u"%s 主張 %d / fact %d(次元つき %d)/ 配線一致 %s"
              % (d, v[u"主張の数"], v[u"instance の fact 数"],
                 v[u"次元つきの context を持つ fact"],
                 v[u"**配線が verify_document と一致**"]))
    for r in rows:
        print(u"%s %s 値 %s" % (r[u"doc"], r[u"id"], r[u"値"]))
        print(u"   試した key: %s" % (r[u"**試した key**"] or u"**無し**"))
        print(u"   正解      : %s" % r[u"正解の key"])
        print(u"   正解は instance に在るか: (名前,context) %s / 名前 %s / 次元 %s"
              % (r[u"正解の (要素名, context) が instance に在る"],
                 r[u"正解の要素名が instance に在る"],
                 r[u"正解の次元(生の context から)"]))
        if r[u"**候補 0 の内訳**"]:
            z = r[u"**候補 0 の内訳**"]
            print(u"   subject %r(向きの語 %r)-> %s"
                  u"(正解の要素が語彙に在る: %s / その subject に当たった要素 %s)"
                  % (r[u"Core が決めた subject"], r[u"Core が見た語"],
                     z[u"どこで落ちたか"], z[u"正解の要素が語彙に在る"],
                     z[u"その語に当たった要素"]))
        print(u"   分類      : %s / state %s / reason %s"
              % (r[u"**分類**"], r[u"Core の state"], r[u"Core の reason"]))
    print(u"--- 正解の要素名に次元なしの context が在るか ---")
    for r in rows:
        print(u"  %s %s %-44s 次元なしの context: %s / context 数 %d"
              % (r[u"doc"], r[u"id"], name_of(r[u"正解の key"]),
                 r[u"**正解の要素名に次元なしの context が在るか**"],
                 len(r[u"**正解の要素名が在る context**"])))
    print(u"--- 分類ごと ---")
    for k, v in sorted(kinds.items()):
        print(u"  %-34s %d" % (k, v))
    print(u"->", OUT)


if __name__ == "__main__":
    main()
