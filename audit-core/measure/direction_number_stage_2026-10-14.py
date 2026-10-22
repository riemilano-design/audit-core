# -*- coding: utf-8 -*-
"""方向の主張に「数が付かなかった理由」を、どの処理段のものかに分ける(2026-10-14)。

人間の指示(2026-10-14): 「先に見るのは、切り出しが数を付けなかった理由」。
知りたいのは次の 3 つの区別で、**原因も修正箇所も違う**:
  (1) 文から数値を抽出する段階で、照合対象として拾われなかったのか
  (2) 拾われていたのに、主張と数値の対応付けで外れたのか
  (3) 数値自体は拾われていて、別セグメントへの接続を許してしまったのか
「既存の dump と記録で区別できる範囲だけ確認する。区別できなければ未確定のまま残す」。

**合否の判定ではない。新しい標本は引いていない。**使うのは
最終評価用 8 書類の**既に取得済みの ZIP**(2026-10-14 に 1 度だけ取得したもの)と、
commit 済みの確定ラベル・dump・key・facts だけ。通信しない。

====================================================================
分かったこと(先に書く)
====================================================================
(1) ではない。engine は**同じ文・同じ主語の金額の主張を別に作っている**
(例 `S100Z38F` の `N040` = 売上高 9,648 百万円)。拾われている。
(2) でもない。その金額の主張は方向の主張と**同じ fact に結ばれている**(pointer が共通)。
(3) に近いが、正確には**「数値の主張は VALUE_MISMATCH で止まっていたのに、
同じ枠に結んだ方向の主張だけが GROUNDED になった」**。engine は矛盾を**自分の中に持っていた**。

そこで測るのは「方向の主張が使っている fact そのものを使った金額の主張が、
同じ文の中で VALUE_MISMATCH だったか」である。これを兄弟(sibling)と呼ぶ。

====================================================================
落ちた兄弟の分け方(**19 件すべてを読んだ後に書いた。開示**)
====================================================================
上から最初に当たったものを採る。``stated`` は文に書かれた金額を円に直した値、
許容は**書かれた数の末尾の 0 の桁の 2 倍**(「2億57百万円」は百万円の桁で書かれているので
円の桁で比べてはいけない。これを間違えて自分で 4 件を取りこぼした)。

  A ``diff``   stated が、方向の主張が結んだ 2 件の fact の**差**に当たる。
               → **engine 自身のバグ**。「〜に比べ X の増加」の X は水準ではなく差なのに、
                 engine は水準と比べて VALUE_MISMATCH にしている。**止めすぎ側の誤り。**
  B ``frame``  stated が、**結んだ fact と同じ要素の別の枠**(member/期間)の値に当たる。
               → **接続(枠の選び方)の誤り**。文の数は別の枠のものだと engine 自身が示している。
  C ``subject`` stated が、**別の要素**の値に当たる。
               → **数を文中の別の主語に付けた**(「〈A〉については…〈B〉の…により X 円」の
                 X は A のものだが B に付けた)。num 主張側の語の掛かり先の誤り。
  D ``none``   当たる fact が無い。

====================================================================
段
====================================================================
  ``extract``   取得済み ZIP から主張を作り直し、兄弟の記録を fixture に書く(ZIP が要る)。
  ``classify``  fixture と commit 済みの facts だけで分類して数を出す(ZIP は要らない)。
  ``check``     ``classify`` の出力が記録と一致することを確かめる。
"""
import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import grounds_eval as GE  # noqa: E402

BASE = os.environ.get("FINAL8_BASE") or os.path.join(ROOT, "fixtures", "xbrl", "final8")
SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")
PROFILE = "P16"
SIB = os.path.join(BASE, "direction_siblings_2026-10-14.json")
OUT = os.path.join(BASE, "direction_number_stage_2026-10-14.json")
MONEY = {"百万円": 10 ** 6, "千円": 10 ** 3, "円": 1, "億円": 10 ** 8}
KINDS = {"A": "A 文の数は『差』(engine は水準と比べた)",
         "B": "B 同じ要素の別の枠に当たる(接続 = 枠の選び方)",
         "C": "C 別の要素に当たる(数を別の主語に付けた)",
         "D": "D 当たる fact が無い"}


def precision(value):
    """書かれた数の末尾の 0 の桁。許容はこの 2 倍にする。"""
    n = int(round(abs(value)))
    if n == 0:
        return 1
    p = 1
    while n % (p * 10) == 0 and p < 10 ** 9:
        p *= 10
    return p


def xbrl_pointers(claim):
    p = claim.get("pointer")
    if p is None:
        return []
    xs = [p] if isinstance(p, str) else p
    return sorted(x for x in xs if x.startswith("xbrl:"))


def docs_list():
    return json.load(io.open(SPLIT, encoding="utf-8"))["final_eval_sealed"]


def facts_of(doc):
    return json.load(io.open(os.path.join(BASE, "seat", "facts_%s.json" % doc), encoding="utf-8"))


def classify_sibling(row, facts):
    """落ちた兄弟 1 件を A/B/C/D に分ける(docstring の順で最初に当たったもの)。"""
    stated = row["stated"]
    tol = 2 * precision(stated)
    if row["direction_delta"] is not None and abs(stated - row["direction_delta"]) <= tol:
        return "A"
    hits = [f for f in facts if f["値"] is not None and abs(abs(f["値"]) - stated) <= tol]
    bound = set(row["direction_elements"])
    if any(f["要素"].split(":")[-1] in bound for f in hits):
        return "B"
    if hits:
        return "C"
    return "D"


def stage_extract():
    from adapters.xbrl import recipes as R, vocabulary as V, edinet
    docs = docs_list()
    labels = GE.load_labels(os.path.join(BASE, "labels_final8_2026-10-14.json"))
    dump = {}
    for d in docs:
        dump.update(json.load(io.open(os.path.join(BASE, "commander_only", "dump_%s_%s.json" % (PROFILE, d)),
                                      encoding="utf-8")))
    rows, census = [], []
    for d in docs:
        zb = io.open(edinet.cache_path(d), "rb").read()
        num, txt = R.build_raw_claims(zb, V.PROFILES[PROFILE])
        km = {r["行の鍵"]: r["claim_id"] for r in json.load(
            io.open(os.path.join(BASE, "commander_only", "key_%s.json" % d), encoding="utf-8"))["rows_map"]}
        by_id = {c["id"]: c for c in txt}
        vals = {(f["要素"].split(":")[-1], f["context"]): f["値"] for f in facts_of(d)}
        for x in num:
            if x.get("unit") not in MONEY:
                continue
            ps = xbrl_pointers(x)
            census.append({"docID": d, "id": x["id"], "result": x.get("result"),
                           "stated": x["value"] * MONEY[x["unit"]],
                           "pointers": ps})
        for r in GE.score(dump, labels):
            if r["state"] != "GROUNDED" or not r["direction"] or not r["id"].startswith(d + ":"):
                continue
            c = by_id.get(km[r["id"].split(":", 1)[1]])
            if c is None:
                continue
            mine = xbrl_pointers(c)
            xs = [vals.get((p.split("@")[0].split(":")[-1], p.split("@", 1)[1])) for p in mine]
            delta = abs(xs[0] - xs[1]) if len(xs) == 2 and all(v is not None for v in xs) else None
            sibs = []
            for x in num:
                if (x.get("unit") in MONEY and x["sentence"] == c["sentence"]
                        and set(xbrl_pointers(x)) & set(mine)):
                    sibs.append({"id": x["id"], "unit": x["unit"], "result": x.get("result"),
                                 "subject": x.get("subject"),
                                 "stated": x["value"] * MONEY[x["unit"]],
                                 "recomputed": x.get("recomputed")})
            rows.append({"id": r["id"], "docID": d, "claim_id": c["id"],
                         "e2": not r["strict"], "subject": c.get("subject"),
                         "member": c.get("member"), "word": c.get("word"),
                         "direction_pointers": mine,
                         "direction_elements": sorted({p.split("@")[0].split(":")[-1] for p in mine}),
                         "direction_delta": delta, "money_siblings": sibs})
    rows.sort(key=lambda r: r["id"])
    out = {"purpose": "方向の形で GROUNDED になった 52 行の、同じ文・同じ fact の金額の主張(兄弟)",
           "profile": PROFILE, "how": "取得済み ZIP から build_raw_claims を回し直した。通信しない",
           "rows": rows, "money_claim_census": census}
    with io.open(SIB, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("方向かつ GROUNDED %d 行 / 金額の num 主張 %d 件 -> %s" % (len(rows), len(census), SIB))


def stage_classify():
    sib = json.load(io.open(SIB, encoding="utf-8"))
    facts = {d: facts_of(d) for d in docs_list()}
    have = collections.Counter()
    kinds = collections.Counter()
    per_row = []
    for r in sib["rows"]:
        bad = [s for s in r["money_siblings"] if s["result"] == "VALUE_MISMATCH"]
        t = "E2" if r["e2"] else "E1'"
        if not r["money_siblings"]:
            have[(t, "同じ文・同じ fact の金額の主張が無い")] += 1
        elif bad:
            have[(t, "在る → VALUE_MISMATCH(engine 自身が落としていた)")] += 1
        else:
            have[(t, "在る → 落ちていない")] += 1
        ks = []
        for s in bad:
            row = dict(r, stated=s["stated"])
            k = classify_sibling(row, facts[r["docID"]])
            kinds[(t, KINDS[k])] += 1
            ks.append(k)
        per_row.append({"id": r["id"], "kind": t, "siblings": len(r["money_siblings"]),
                        "bad": len(bad), "classes": ks})

    # 欠陥 A の大きさ(8 書類の金額の num 主張すべて)
    vals = {}
    for d, fs in facts.items():
        for f in fs:
            vals[(d, f["要素"].split(":")[-1], f["context"])] = f["値"]
    census = collections.Counter()
    for c in sib["money_claim_census"]:
        census[("全体", str(c["result"]))] += 1
        if c["result"] != "VALUE_MISMATCH":
            continue
        if len(c["pointers"]) != 1:
            census[("VALUE_MISMATCH の中身", "pointer が 1 件でない")] += 1
            continue
        elem = c["pointers"][0].split("@")[0].split(":")[-1]
        ctx = c["pointers"][0].split("@", 1)[1]
        other = (ctx.replace("CurrentYear", "Prior1Year") if "CurrentYear" in ctx
                 else ctx.replace("Prior1Year", "CurrentYear"))
        a, b = vals.get((c["docID"], elem, ctx)), vals.get((c["docID"], elem, other))
        if a is None or b is None:
            census[("VALUE_MISMATCH の中身", "対になる期間の fact が無い")] += 1
        elif abs(c["stated"] - abs(a - b)) <= 2 * precision(c["stated"]):
            census[("VALUE_MISMATCH の中身", "文の数は『差』だった(欠陥 A)")] += 1
        else:
            census[("VALUE_MISMATCH の中身", "差でもない")] += 1

    def table(title, c):
        print("\n[%s]" % title)
        for k, n in sorted(c.items(), key=lambda kv: (kv[0][0], -kv[1], kv[0][1])):
            print("  %-4s %-44s %3d" % (k[0], k[1], n))
        print("  %-49s %3d" % ("合計", sum(c.values())))

    table("方向かつ GROUNDED 52 行 × 同じ文の金額の主張", have)
    table("落ちた兄弟の分け方", kinds)
    table("欠陥 A の大きさ(8 書類の金額の num 主張)", census)
    out = {"purpose": "方向の主張に数が付かなかった理由を処理段に分ける(合否の判定ではない)",
           "profile": PROFILE,
           "sibling_presence": {" | ".join(k): v for k, v in sorted(have.items())},
           "bad_sibling_kinds": {" | ".join(k): v for k, v in sorted(kinds.items())},
           "money_claim_census": {" | ".join(k): v for k, v in sorted(census.items())},
           "rows": per_row}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("\n->", OUT)
    return out


def stage_check():
    out = stage_classify()
    rec = json.load(io.open(OUT, encoding="utf-8"))
    assert rec == json.loads(json.dumps(out, ensure_ascii=False)), "fixture が再現しない"
    print("再現 OK")


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "classify"
    {"extract": stage_extract, "classify": stage_classify, "check": stage_check}[stage]()


if __name__ == "__main__":
    main()
